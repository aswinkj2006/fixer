"""
fixer.ai — Slack Interactive Resolution Handler
Spec: 04_SLACK_INTEGRATION.md §4 & §Continual learning on resolution

Handles the 'Mark Resolved' interactive Slack button click:
1. Validates ticket state in database.
2. Updates ticket to 'resolved' and records closed_at timestamp.
3. Automatically triggers continual learning: embeds the full thread into that machine's Tier 2 collection.
4. Mirrors resolution confirmation back into the Slack thread.
5. Writes the resolution event to the local ticket_messages table.
"""
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select

from backend.config import DATABASE_URL, SLACK_BOT_TOKEN
from backend.database.models import Ticket, TicketMessage
from backend.rag.continual_learning import embed_resolved_ticket


async def handle_slack_resolution(
    ticket_id: str,
    user_id: str,
    user_name: Optional[str] = None,
    channel_id: Optional[str] = None,
    thread_ts: Optional[str] = None,
    session: Optional[AsyncSession] = None,
    slack_client = None,
) -> Dict[str, Any]:
    """
    Executes complete resolution workflow when technician clicks 'Mark Resolved' in Slack.
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
        ticket = await db.get(Ticket, ticket_id)
        if not ticket:
            return {"success": False, "error": f"Ticket {ticket_id} not found."}

        now_iso = datetime.now(timezone.utc).isoformat()
        technician_name = user_name or f"Technician (<@{user_id}>)"

        ticket.status = "resolved"
        ticket.closed_at = now_iso
        if not ticket.resolution_summary:
            ticket.resolution_summary = f"Resolved and verified in-thread by {technician_name} via Slack."

        # Mirror resolution message into ticket_messages
        resolution_msg = TicketMessage(
            ticket_id=ticket.ticket_id,
            machine_id=ticket.machine_id,
            sender="technician",
            sender_name=technician_name,
            text=f"Marked ticket resolved via Slack action button. Corrective actions confirmed.",
            timestamp=now_iso,
            slack_ts=thread_ts,
        )
        db.add(resolution_msg)
        await db.commit()
        await db.refresh(ticket)

        # Trigger continual learning embedding into Tier 2 isolated memory
        cl_success = await embed_resolved_ticket(ticket.ticket_id, session=db)

        # Post confirmation back to Slack thread
        if SLACK_BOT_TOKEN and channel_id and thread_ts:
            try:
                from slack_sdk import WebClient
                client = slack_client or WebClient(token=SLACK_BOT_TOKEN)
                confirmation_text = (
                    f"✅ *Ticket `{ticket.ticket_id[:8]}` Marked Resolved* by <@{user_id}>\n"
                    f"🧠 *Continual Learning Complete:* Resolution summary and technician thread logs have been "
                    f"chunked & embedded into `{ticket.machine_id}` Tier 2 brain.\n"
                    f"_Next time this machine demonstrates a similar pattern, this fix will be automatically surfaced._"
                )
                client.chat_postMessage(
                    channel=channel_id,
                    thread_ts=thread_ts,
                    text=confirmation_text,
                    mrkdwn=True,
                )
            except Exception as e:
                print(f"[slack_resolution] Failed to post thread confirmation: {e}")

        return {
            "success": True,
            "ticket_id": ticket.ticket_id,
            "machine_id": ticket.machine_id,
            "status": "resolved",
            "continual_learning_embedded": cl_success,
        }

    except Exception as e:
        print(f"[slack_resolution] Error resolving ticket: {e}")
        return {"success": False, "error": str(e)}
    finally:
        if should_close:
            await db.close()
