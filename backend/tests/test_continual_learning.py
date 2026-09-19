"""
fixer.ai — Tests: Continual Learning Loop
Spec: 01_ARCHITECTURE.md §3, 05_BUILD_PLAN_6_DAYS.md Day 4

Verifies:
- Resolving a ticket triggers embedding into that machine's Tier 2 Chroma collection
- Newly resolved ticket is immediately retrievable via semantic memory search
- Tier 2 isolation is preserved (ticket embedded in M-01 never leaks to M-02)
- HTTP POST /api/tickets/{ticket_id}/resolve marks resolved and updates Tier 2 memory
"""
import uuid
import pytest
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from backend.config import DATABASE_URL
from backend.database.models import Ticket, TicketMessage, FailureCode
from backend.rag.continual_learning import embed_resolved_ticket, verify_machine_memory
from backend.main import app


@pytest.mark.asyncio
async def test_continual_learning_embed_and_retrieve():
    """Verify newly resolved ticket is embedded into Tier 2 and immediately retrievable."""
    engine = create_async_engine(DATABASE_URL)
    session_factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    unique_uuid = str(uuid.uuid4())
    ticket_id = f"CL-TEST-{unique_uuid[:8]}"
    distinctive_symptom = f"Unusual harmonic resonance at 420Hz in harmonic drive reducer {unique_uuid[:6]}"
    distinctive_remedy = f"Flushed reducer casing and replaced specialized damping flange seal {unique_uuid[:6]}"

    async with session_factory() as session:
        # Create test ticket on M-01
        t = Ticket(
            ticket_id=ticket_id,
            machine_id="M-01",
            opened_at=datetime.now(timezone.utc).isoformat(),
            closed_at=datetime.now(timezone.utc).isoformat(),
            status="resolved",
            severity="medium",
            symptom_text=distinctive_symptom,
            resolution_summary=distinctive_remedy,
            failure_code="FC-ROB-001",
            confidence=0.89,
        )
        session.add(t)

        # Add technician message
        msg = TicketMessage(
            ticket_id=ticket_id,
            machine_id="M-01",
            sender="technician",
            sender_name="Arjun Rao",
            text=f"Torque stabilized after applying {distinctive_remedy}.",
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        session.add(msg)
        await session.commit()

        # Execute continual learning hook
        success = await embed_resolved_ticket(ticket_id, session=session)
        assert success is True, "embed_resolved_ticket should return True"

    # Verify M-01's brain retrievable immediately
    mem_m01 = await verify_machine_memory("M-01", distinctive_symptom)
    assert mem_m01["found"] is True
    assert mem_m01["count"] > 0
    top_result = mem_m01["results"][0]
    assert top_result["ticket_id"] == ticket_id

    try:
        # Verify Tier 2 isolation: M-02 must NOT return this ticket
        mem_m02 = await verify_machine_memory("M-02", distinctive_symptom)
        if mem_m02.get("results"):
            returned_ids = [r["ticket_id"] for r in mem_m02["results"]]
            assert ticket_id not in returned_ids, "M-01 ticket must never leak into M-02 Tier 2 brain"
    finally:
        try:
            from backend.rag.chroma_client import get_tier2_collection
            col = get_tier2_collection("M-01")
            col.delete(ids=[f"tier2_M_01_{ticket_id}"])
        except Exception:
            pass
        await engine.dispose()


def test_api_resolve_ticket_endpoint():
    """Verify POST /api/tickets/{ticket_id}/resolve API endpoint."""
    client = TestClient(app)

    # First get an existing ticket
    res = client.get("/api/machines/M-01/tickets")
    assert res.status_code == 200
    tickets = res.json()
    assert len(tickets) > 0

    target_ticket_id = tickets[0]["ticket_id"]

    # Call resolve endpoint
    payload = {
        "resolution_summary": "Replaced damaged O-ring and replenished lubricant to nominal fill level.",
        "technician_notes": "Completed test weld cycle with 0 deviation. Ready for production.",
        "technician_id": "T-01",
    }
    resolve_res = client.post(f"/api/tickets/{target_ticket_id}/resolve", json=payload)
    assert resolve_res.status_code == 200
    data = resolve_res.json()
    assert data["success"] is True
    assert data["status"] == "resolved"
    assert data["ticket_id"] == target_ticket_id
    assert "continual_learning_embedded" in data
    assert data["continual_learning_embedded"] is True
