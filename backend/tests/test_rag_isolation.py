"""
fixer.ai — RAG Scoping and Isolation Tests
Tests:
1. Tier 1 shared manuals scoped by machine model (no cross-contamination across models).
2. Tier 2 strictly isolated per machine instance (M-01 history NEVER leaks into M-02).
3. Synthetic same-model multi-instance isolation test.
4. Specific alarm/symptom retrieval precision across all 4 machine types.
5. Dynamic continual learning insertion: new resolution is retrievable by its own machine only.
"""
import pytest
import asyncio
import uuid
from datetime import datetime, timezone

from backend.rag.chroma_client import (
    get_tier1_collection,
    get_tier2_collection,
    get_chroma_client,
)
from backend.rag.retrieval import (
    retrieve_tier1,
    retrieve_tier2,
    retrieve_fused_context,
)
from backend.rag.continual_learning import embed_resolved_ticket
from backend.database.models import Ticket, TicketMessage, FailureCode
from backend.config import DATABASE_URL
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker


@pytest.mark.asyncio
async def test_tier1_model_scoping():
    """Verify Tier 1 collections return content only for the queried model."""
    # FANUC query
    fanuc_results = retrieve_tier1("fanuc_arcmate100id", "harmonic drive joint J2 over-torque", n=4)
    assert len(fanuc_results) > 0, "Should retrieve chunks from FANUC manuals"
    for item in fanuc_results:
        assert item["metadata"].get("model_slug") == "fanuc_arcmate100id"
        assert item["metadata"].get("tier") == "1"

    # Haas CNC query
    haas_results = retrieve_tier1("haas_vf2", "spindle bearing vibration high", n=3)
    assert len(haas_results) > 0, "Should retrieve chunks from Haas manual"
    for item in haas_results:
        assert item["metadata"].get("model_slug") == "haas_vf2"
        # Confirm no FANUC text in Haas collection
        assert "arcmate" not in item["text"].lower()


@pytest.mark.asyncio
async def test_tier2_machine_isolation():
    """
    CRITICAL ISOLATION TEST:
    A query against M-01's Tier 2 collection must NEVER return M-02, M-03, or M-04 tickets.
    """
    # Query M-01
    m01_results = retrieve_tier2("M-01", "bearing vibration over-torque failure", n=5)
    assert len(m01_results) > 0, "M-01 should have resolved ticket history"
    for item in m01_results:
        assert item["metadata"]["machine_id"] == "M-01", (
            f"Isolation violation! Returned machine_id={item['metadata']['machine_id']} for M-01 query"
        )
        assert item["metadata"]["tier"] == "2"

    # Query M-02
    m02_results = retrieve_tier2("M-02", "spindle vibration bearing failure", n=5)
    assert len(m02_results) > 0, "M-02 should have resolved ticket history"
    for item in m02_results:
        assert item["metadata"]["machine_id"] == "M-02", (
            f"Isolation violation! Returned machine_id={item['metadata']['machine_id']} for M-02 query"
        )

    # Query M-03
    m03_results = retrieve_tier2("M-03", "conveyor motor thermal runaway belt slip", n=5)
    assert len(m03_results) > 0, "M-03 should have resolved ticket history"
    for item in m03_results:
        assert item["metadata"]["machine_id"] == "M-03"

    # Query M-04
    m04_results = retrieve_tier2("M-04", "transducer zero drift calibration offset", n=5)
    assert len(m04_results) > 0, "M-04 should have resolved ticket history"
    for item in m04_results:
        assert item["metadata"]["machine_id"] == "M-04"

    # Cross-check ticket IDs: No overlap between M-01 and M-02 ticket sets
    m01_ticket_ids = {item["ticket_id"] for item in m01_results}
    m02_ticket_ids = {item["ticket_id"] for item in m02_results}
    assert m01_ticket_ids.isdisjoint(m02_ticket_ids), (
        f"Cross-contamination detected! Overlapping tickets: {m01_ticket_ids & m02_ticket_ids}"
    )


@pytest.mark.asyncio
async def test_same_model_distinct_instance_isolation():
    """
    Two distinct machine instances of the EXACT same model family:
    Tests that instance A's memory is never accessible to instance B.
    """
    client = get_chroma_client()
    col_a = get_tier2_collection("TEST-UNIT-A", client=client)
    col_b = get_tier2_collection("TEST-UNIT-B", client=client)

    unique_fault_signature = "FAULT-SIGNATURE-GAMMA-98214-CRACKED-SEAL"
    col_a.upsert(
        ids=["ticket_a_001"],
        documents=[f"Unit A had catastrophic failure: {unique_fault_signature}. Replaced o-ring."],
        metadatas=[{"tier": "2", "machine_id": "TEST-UNIT-A", "ticket_id": "ticket_a_001"}],
    )

    col_b.upsert(
        ids=["ticket_b_001"],
        documents=["Unit B normal scheduled maintenance: routine oil change. No seal issue."],
        metadatas=[{"tier": "2", "machine_id": "TEST-UNIT-B", "ticket_id": "ticket_b_001"}],
    )

    # Query B for Unit A's unique fault
    results_b = retrieve_tier2("TEST-UNIT-B", unique_fault_signature, n=2, client=client)
    # Unit B must NOT return Unit A's ticket
    for r in results_b:
        assert r["id"] != "ticket_a_001"
        assert r["metadata"]["machine_id"] == "TEST-UNIT-B"

    # Query A for Unit A's unique fault
    results_a = retrieve_tier2("TEST-UNIT-A", unique_fault_signature, n=1, client=client)
    assert len(results_a) == 1
    assert results_a[0]["id"] == "ticket_a_001"
    assert results_a[0]["metadata"]["machine_id"] == "TEST-UNIT-A"


@pytest.mark.asyncio
async def test_retrieval_relevance_for_failure_modes():
    """
    Verify high relevance for specific failure modes across equipment types:
    - FANUC SRVO-062 pulse coder battery
    - Haas Way Lube filter / Alarm 121
    - Conveyor V-belt tension frequency
    - Metrology ISO 6789 deadweight calibration
    """
    # 1. FANUC alarm
    fanuc_hits = retrieve_tier1("fanuc_arcmate100id", "SRVO-062 pulse coder battery BZAL", n=2)
    assert any("battery" in h["text"].lower() or "srvo" in h["text"].lower() for h in fanuc_hits)

    # 2. Haas way lube
    haas_hits = retrieve_tier1("haas_vf2", "Alarm 121 low lube pressure filter", n=2)
    assert any("lube" in h["text"].lower() or "filter" in h["text"].lower() for h in haas_hits)

    # 3. Conveyor belt tension
    conveyor_hits = retrieve_tier1("generic_conveyor", "V-belt tension acoustic meter 3VX450", n=2)
    assert any("belt" in h["text"].lower() or "tension" in h["text"].lower() for h in conveyor_hits)

    # 4. Calibration station
    cal_hits = retrieve_tier1("calibration_station", "ISO 6789 deadweight calibration 5-point", n=2)
    assert any("6789" in h["text"] or "transducer" in h["text"].lower() for h in cal_hits)


@pytest.mark.asyncio
async def test_continual_learning_dynamic_insertion():
    """
    Verify that resolving a ticket inserts it into that machine's Tier 2 collection
    and makes it immediately retrievable for that machine, but not for others.
    """
    engine = create_async_engine(DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    test_ticket_id = f"test-ticket-{uuid.uuid4().hex[:8]}"
    test_phrase = f"Unusual harmonic resonance at 312 Hz after flange bolt swap {uuid.uuid4().hex[:6]}"

    async with async_session() as session:
        # Create a new resolved ticket for M-01
        new_ticket = Ticket(
            ticket_id=test_ticket_id,
            machine_id="M-01",
            opened_at=datetime.now(timezone.utc).isoformat(),
            closed_at=datetime.now(timezone.utc).isoformat(),
            symptom_text=test_phrase,
            status="resolved",
            severity="high",
            confidence=0.88,
            assigned_technician_id="T-01",
            failure_code="FC-ROB-001",
            resolution_summary="Torqued J2 mounting bolts to 125 Nm. Vibration subsided.",
        )
        msg = TicketMessage(
            ticket_id=test_ticket_id,
            machine_id="M-01",
            sender="technician",
            sender_name="Arjun Sharma",
            text="Completed repair and verified zero harmonic buzz.",
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        session.add(new_ticket)
        session.add(msg)
        await session.commit()

        # Call continual learning hook
        success = await embed_resolved_ticket(test_ticket_id, session=session)
        assert success is True, "embed_resolved_ticket should succeed"

    try:
        # Query M-01: Should find the newly embedded resolution
        m01_hits = retrieve_tier2("M-01", test_phrase, n=10)
        found_in_m01 = any(h["ticket_id"] == test_ticket_id for h in m01_hits)
        assert found_in_m01, f"Newly resolved ticket {test_ticket_id} should be retrievable by M-01"

        # Query M-02: Must NEVER find this ticket
        m02_hits = retrieve_tier2("M-02", test_phrase, n=10)
        found_in_m02 = any(h["ticket_id"] == test_ticket_id for h in m02_hits)
        assert not found_in_m02, f"Isolation leak! Ticket {test_ticket_id} was retrieved by M-02"
    finally:
        try:
            col = get_tier2_collection("M-01")
            col.delete(ids=[f"tier2_M_01_{test_ticket_id}"])
        except Exception:
            pass
        await engine.dispose()


@pytest.mark.asyncio
async def test_fused_context_structure():
    """Verify retrieve_fused_context returns a well-formed bundle for the resolver agent."""
    bundle = retrieve_fused_context(
        machine_id="M-01",
        model_slug="fanuc_arcmate100id",
        query="J2 joint over-torque motor alarm",
        n_manuals=3,
        n_tickets=2,
    )
    assert bundle["machine_id"] == "M-01"
    assert bundle["model_slug"] == "fanuc_arcmate100id"
    assert bundle["has_manual_context"] is True
    assert bundle["has_ticket_context"] is True
    assert len(bundle["manual_excerpts"]) <= 3
    assert len(bundle["past_tickets"]) <= 2
