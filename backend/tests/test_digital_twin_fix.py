"""
Tests for 3D Digital Twin Fault Injection and 1-Click Physical Repair API.
Verifies that:
1. Fault injection activates the machine failure trigger.
2. Fix endpoint resets simulator to nominal baseline and deactivates trigger.
3. Open tickets are resolved upon physical repair.
"""
import pytest
from httpx import AsyncClient, ASGITransport
from backend.main import app, AsyncSessionLocal
from backend.simulation.simulator import init_simulators, get_current_readings
from backend.simulation.failure_triggers import get_trigger_state, activate_trigger, deactivate_trigger
from backend.database.models import Ticket, Machine
from datetime import datetime, timezone
import uuid


@pytest.mark.asyncio
async def test_fault_injection_and_repair_loop():
    init_simulators()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. Trigger fault on M-01
        res_fault = await client.post("/api/machines/M-01/fault", json={"mode": 1})
        assert res_fault.status_code == 200
        data_fault = res_fault.json()
        assert data_fault["status"] == "fault_active"
        assert data_fault["machine_id"] == "M-01"
        assert get_trigger_state("M-01") is not None

        # 2. Create an open ticket for M-01 in DB
        test_tid = str(uuid.uuid4())
        async with AsyncSessionLocal() as db:
            ticket = Ticket(
                ticket_id=test_tid,
                machine_id="M-01",
                opened_at=datetime.now(timezone.utc).isoformat(),
                status="open",
                severity="critical",
                symptom_text="Reducer joint 2 overheating and severe torque spike",
            )
            db.add(ticket)
            await db.commit()

        # 3. Call 1-click repair endpoint
        res_fix = await client.post("/api/machines/M-01/fix", json={"technician_notes": "Replaced seal & flushed lubricant"})
        assert res_fix.status_code == 200
        data_fix = res_fix.json()
        assert data_fix["status"] == "repaired"
        assert data_fix["machine_id"] == "M-01"
        assert test_tid in data_fix["resolved_tickets"]

        # Trigger should now be deactivated
        assert get_trigger_state("M-01") is None

        # 4. Check DB ticket status
        async with AsyncSessionLocal() as db:
            updated_ticket = await db.get(Ticket, test_tid)
            assert updated_ticket.status == "resolved"
            assert "Mobilux EP2" in updated_ticket.resolution_summary or "repaired" in updated_ticket.resolution_summary

        # Clean up
        deactivate_trigger("M-01")
