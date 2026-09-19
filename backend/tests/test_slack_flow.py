"""
fixer.ai — Tests: Slack Integration Flow & Continual Learning Handlers
Tests:
- Block Kit alert card construction (fields, actions, buttons, markdown)
- Targeted technician @mention by specialty
- Interactive resolution handler (ticket status update, DB message log, continual learning trigger)
- In-thread message handler (two-way mirroring to ticket_messages table)
"""
import uuid
import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select

from backend.config import DATABASE_URL
from backend.database.models import Ticket, TicketMessage, Technician
from backend.slack_integration.escalation import build_escalation_blocks
from backend.slack_integration.resolution_handler import handle_slack_resolution
from backend.slack_integration.message_handler import handle_in_thread_message


def test_build_escalation_blocks():
    """Verify Block Kit work order card contains all required industrial sections."""
    ticket_id = "TEST-TKT-12345"
    machine_id = "M-01"
    diagnosis = {
        "ranked_diagnoses": [
            {
                "diagnosis": "J2 Harmonic Drive Grease Leak",
                "evidence": "Observed dark grease droplet buildup around housing",
            }
        ],
        "confidence": 0.92,
        "severity": "high",
        "repair_steps": [
            "Lockout/tagout robot power supply",
            "Remove inspection cover and check seal integrity",
            "Replace Viton oil seal",
        ],
        "parts_likely_needed": ["Seal Kit A06B-0120-V20", "Kyodo Yushi Molywhite Grease"],
    }
    decision = {
        "assigned_technician": {
            "name": "Arjun Rao",
            "slack_user_id": "U0C2LRFUGSX",
            "specialty": "mechanical",
        }
    }

    blocks = build_escalation_blocks(ticket_id, machine_id, diagnosis, decision)
    assert isinstance(blocks, list)
    assert len(blocks) >= 6

    # 1. Header block
    header = blocks[0]
    assert header["type"] == "header"
    assert "M-01" in header["text"]["text"]

    # 2. Section fields
    fields_section = blocks[1]
    assert fields_section["type"] == "section"
    field_texts = [f["text"] for f in fields_section["fields"]]
    assert any("HIGH" in t for t in field_texts)
    assert any("92%" in t for t in field_texts)
    assert any("<@U0C2LRFUGSX>" in t for t in field_texts)

    # 3. Actions block with buttons
    actions = next(b for b in blocks if b["type"] == "actions")
    action_ids = [btn["action_id"] for btn in actions["elements"]]
    assert "mark_resolved" in action_ids
    assert "acknowledge_ticket" in action_ids

    mark_resolved_btn = next(btn for btn in actions["elements"] if btn["action_id"] == "mark_resolved")
    assert mark_resolved_btn["value"] == ticket_id
    assert mark_resolved_btn["style"] == "primary"


@pytest.mark.asyncio
async def test_handle_slack_resolution_workflow():
    """Verify Slack resolution button marks ticket resolved and triggers continual learning."""
    engine = create_async_engine(DATABASE_URL)
    session_factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    ticket_id = f"SLACK-RES-{str(uuid.uuid4())[:8]}"
    dummy_thread_ts = "1726000000.123456"

    async with session_factory() as session:
        # Create ticket
        t = Ticket(
            ticket_id=ticket_id,
            machine_id="M-01",
            opened_at=datetime.now(timezone.utc).isoformat(),
            status="escalated",
            severity="high",
            symptom_text="Torque climbing on J2 axis with grease leakage",
            slack_thread_ts=dummy_thread_ts,
            failure_code="FC-ROB-001",
        )
        session.add(t)
        await session.commit()

        # Mock Slack client
        mock_slack = MagicMock()
        mock_slack.chat_postMessage.return_value = {"ok": True}

        # Execute resolution handler
        res = await handle_slack_resolution(
            ticket_id=ticket_id,
            user_id="U0C2LRFUGSX",
            user_name="Arjun Rao",
            channel_id="C01234567",
            thread_ts=dummy_thread_ts,
            session=session,
            slack_client=mock_slack,
        )

        assert res["success"] is True
        assert res["status"] == "resolved"
        assert res["continual_learning_embedded"] is True

        # Verify ticket in DB
        updated = await session.get(Ticket, ticket_id)
        assert updated.status == "resolved"
        assert updated.closed_at is not None

        # Verify resolution message logged in ticket_messages
        msg_res = await session.execute(
            select(TicketMessage).where(TicketMessage.ticket_id == ticket_id)
        )
        messages = msg_res.scalars().all()
        assert len(messages) >= 1
        assert any("Marked ticket resolved" in m.text for m in messages)

    await engine.dispose()


@pytest.mark.asyncio
async def test_handle_in_thread_message_sync():
    """Verify technician in-thread messages are mirrored to DB and trigger agent reply."""
    engine = create_async_engine(DATABASE_URL)
    session_factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    ticket_id = f"SLACK-MSG-{str(uuid.uuid4())[:8]}"
    dummy_thread_ts = f"1726111111.{str(uuid.uuid4())[:6]}"

    async with session_factory() as session:
        # Create ticket
        t = Ticket(
            ticket_id=ticket_id,
            machine_id="M-02",
            opened_at=datetime.now(timezone.utc).isoformat(),
            status="escalated",
            severity="high",
            symptom_text="Spindle vibration anomaly",
            slack_thread_ts=dummy_thread_ts,
            failure_code="FC-CNC-001",
        )
        session.add(t)
        await session.commit()

        mock_slack = MagicMock()
        mock_slack.chat_postMessage.return_value = {"ts": "1726111112.000100"}

        # Simulate technician sending message in thread
        res = await handle_in_thread_message(
            thread_ts=dummy_thread_ts,
            text="Inspected the spindle bearing. Should I flush with clean oil or replace immediately?",
            user_id="U0C2LRFUGSX",
            user_name="Priya Sharma",
            channel_id="C01234567",
            message_ts="1726111111.999999",
            session=session,
            slack_client=mock_slack,
        )

        assert res["handled"] is True
        assert "bot_reply" in res
        assert "fixer.ai" in res["bot_reply"]

        # Check DB messages: should contain technician message + bot response
        msgs = (
            await session.execute(
                select(TicketMessage).where(TicketMessage.ticket_id == ticket_id)
            )
        ).scalars().all()
        assert len(msgs) >= 2
        senders = [m.sender for m in msgs]
        assert "technician" in senders
        assert "bot" in senders

    await engine.dispose()
