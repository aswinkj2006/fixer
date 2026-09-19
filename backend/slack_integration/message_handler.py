"""
fixer.ai — Slack In-Thread Message Handler & Live Mirroring
Spec: 04_SLACK_INTEGRATION.md §3 & §5

Handles technician replies inside an incident Slack thread:
1. Matches incoming thread_ts to open/escalated ticket in local DB.
2. Mirrors technician message into ticket_messages in real time.
3. Invokes the resolver agent with that machine's fused Tier 1 + Tier 2 context.
4. Posts agent diagnosis/guidance back into the Slack thread.
5. Mirrors agent response into ticket_messages for local web UI display.
"""
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select

from backend.config import DATABASE_URL, SLACK_BOT_TOKEN
from backend.database.models import Ticket, TicketMessage
from backend.resolver.fusion import fuse_and_reason
from backend.simulation.simulator import get_current_readings


async def handle_in_thread_message(
    thread_ts: str,
    text: str,
    user_id: str,
    user_name: Optional[str] = None,
    channel_id: Optional[str] = None,
    message_ts: Optional[str] = None,
    session: Optional[AsyncSession] = None,
    slack_client = None,
) -> Dict[str, Any]:
    """
    Processes an in-thread message from a technician on an escalated incident.
    """
    should_close = False
    if session is None:
        engine = create_async_engine(DATABASE_URL)
        session_factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        db = session_factory()
        should_close = True
    else:
        db = session

    try:
        # Find matching ticket by thread_ts
        res = await db.execute(
            select(Ticket).where(Ticket.slack_thread_ts == thread_ts)
        )
        ticket = res.scalars().first()
        if not ticket:
            return {"handled": False, "reason": f"No ticket matches thread_ts {thread_ts}"}

        now_iso = datetime.now(timezone.utc).isoformat()
        technician_name = user_name or f"Technician (<@{user_id}>)"

        # 1. Mirror technician reply to ticket_messages
        tech_msg = TicketMessage(
            ticket_id=ticket.ticket_id,
            machine_id=ticket.machine_id,
            sender="technician",
            sender_name=technician_name,
            text=text,
            timestamp=now_iso,
            slack_ts=message_ts or thread_ts,
        )
        db.add(tech_msg)
        await db.commit()

        # 2. Invoke conversational reasoning with current sensor snapshot + RAG
        sensor_snapshot = get_current_readings(ticket.machine_id)
        reasoning_res = await fuse_and_reason(
            machine_id=ticket.machine_id,
            transcript=text,
            vision_summary=None,
            sensor_snapshot=sensor_snapshot,
        )

        top_diag = reasoning_res.get("ranked_diagnoses", [{}])[0] if reasoning_res.get("ranked_diagnoses") else {}
        diag_title = top_diag.get("diagnosis", "Telemetry evaluated")
        repair_steps = reasoning_res.get("repair_steps", [])
        steps_text = "\n".join(f"• {s}" for s in repair_steps[:3]) if repair_steps else "Proceed with standard inspection."

        bot_reply_text = (
            f"🤖 *fixer.ai Advisory Update for {ticket.machine_id}*\n"
            f"*Assessment:* {diag_title}\n"
            f"*Recommended Next Action:*\n{steps_text}\n"
            f"_Live sensor snapshot: {json_compact(sensor_snapshot)}_"
        )

        # 3. Post reply back to thread
        bot_slack_ts = None
        if SLACK_BOT_TOKEN and channel_id:
            try:
                from slack_sdk import WebClient
                client = slack_client or WebClient(token=SLACK_BOT_TOKEN)
                resp = client.chat_postMessage(
                    channel=channel_id,
                    thread_ts=thread_ts,
                    text=bot_reply_text,
                    mrkdwn=True,
                )
                bot_slack_ts = str(resp["ts"])
            except Exception as e:
                print(f"[slack_message] Error posting reply: {e}")

        # 4. Mirror bot reply to ticket_messages
        bot_msg = TicketMessage(
            ticket_id=ticket.ticket_id,
            machine_id=ticket.machine_id,
            sender="bot",
            sender_name="fixer.ai",
            text=bot_reply_text,
            timestamp=datetime.now(timezone.utc).isoformat(),
            slack_ts=bot_slack_ts,
        )
        db.add(bot_msg)
        await db.commit()

        return {
            "handled": True,
            "ticket_id": ticket.ticket_id,
            "machine_id": ticket.machine_id,
            "bot_reply": bot_reply_text,
        }

    except Exception as e:
        print(f"[slack_message] Error in thread handler: {e}")
        return {"handled": False, "error": str(e)}
    finally:
        if should_close:
            await db.close()


def json_compact(d: dict) -> str:
    """Compact string representation for telemetry snapshot."""
    if not d:
        return "Nominal"
    return ", ".join(f"{k}: {v}" for k, v in list(d.items())[:3])
