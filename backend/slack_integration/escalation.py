"""
fixer.ai — Slack Escalation with Block Kit
Spec: 04_SLACK_INTEGRATION.md, 01_ARCHITECTURE.md §5, 05_BUILD_PLAN_6_DAYS.md Day 5

Formats structured work order cards using Slack Block Kit:
- Diagnosis, confidence score, and severity indicator
- Targeted technician @mention (<@USER_ID>) based on specialty
- Repair steps checklist & required parts
- Interactive action buttons: "Mark Resolved", "Acknowledge", "Open Machine Detail"
- Opens a dedicated incident thread (thread_ts)
- Mirrors initial escalation card to ticket_messages table
"""
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
import json

from backend.config import SLACK_BOT_TOKEN, SLACK_ESCALATION_CHANNEL, FRONTEND_ORIGIN
from backend.database.models import Ticket, TicketMessage


def build_escalation_blocks(
    ticket_id: str,
    machine_id: str,
    diagnosis: dict,
    decision: dict,
    web_url: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Constructs a rich Slack Block Kit layout for an escalated work order.
    """
    top_diag = diagnosis.get("ranked_diagnoses", [{}])[0] if diagnosis.get("ranked_diagnoses") else {}
    fault_name = top_diag.get("diagnosis") or diagnosis.get("diagnosis", "Unspecified Equipment Fault")
    evidence = top_diag.get("evidence", "Abnormal sensor telemetry drift detected.")
    confidence = float(diagnosis.get("confidence", 0.75))
    severity = str(diagnosis.get("severity", "high")).upper()

    tech = decision.get("assigned_technician") or {}
    tech_mention = f"<@{tech['slack_user_id']}>" if tech.get("slack_user_id") else (tech.get("name") or "On-call Technician")
    specialty = tech.get("specialty", "General Maintenance").title()

    severity_emoji = {
        "LOW": "🟡",
        "MEDIUM": "🟠",
        "HIGH": "🔴",
        "CRITICAL": "🚨",
    }.get(severity, "⚠️")

    # Repair steps
    repair_steps = diagnosis.get("repair_steps") or [
        "Inspect component for physical wear or contamination.",
        "Verify telemetry against manufacturer operational baseline.",
        "Perform scheduled maintenance overhaul per service manual.",
    ]
    formatted_steps = "\n".join(f"• *Step {i+1}:* {step}" for i, step in enumerate(repair_steps[:4]))

    # Parts
    parts = diagnosis.get("parts_likely_needed") or ["Standard OEM maintenance kit"]
    formatted_parts = ", ".join(parts)

    detail_url = web_url or f"{FRONTEND_ORIGIN}/machine/{machine_id}"

    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"{severity_emoji} fixer.ai Work Order — {machine_id}",
                "emoji": True,
            },
        },
        {
            "type": "section",
            "fields": [
                {
                    "type": "mrkdwn",
                    "text": f"*Severity:*\n`{severity}`",
                },
                {
                    "type": "mrkdwn",
                    "text": f"*Confidence:*\n`{int(confidence * 100)}%`",
                },
                {
                    "type": "mrkdwn",
                    "text": f"*Assigned Specialist:*\n{tech_mention} ({specialty})",
                },
                {
                    "type": "mrkdwn",
                    "text": f"*Ticket ID:*\n`{ticket_id[:8]}`",
                },
            ],
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Primary Diagnosis:*\n*{fault_name}*\n_{evidence}_",
            },
        },
        {"type": "divider"},
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Guided Action Steps:*\n{formatted_steps}",
            },
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Parts Likely Needed:*\n`{formatted_parts}`",
            },
        },
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": f"📍 *Machine:* `{machine_id}` | ⚡ *Source:* Multimodal Resolver Agent (Offline Tier 1/2 RAG)",
                },
            ],
        },
        {
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "✅ Mark Resolved",
                        "emoji": True,
                    },
                    "style": "primary",
                    "action_id": "mark_resolved",
                    "value": ticket_id,
                },
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "👀 Acknowledge",
                        "emoji": True,
                    },
                    "action_id": "acknowledge_ticket",
                    "value": ticket_id,
                },
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "📊 Open Machine Dashboard",
                        "emoji": True,
                    },
                    "url": detail_url,
                    "action_id": "open_machine_url",
                },
            ],
        },
    ]

    return blocks


async def post_escalation_alert(
    ticket: Ticket,
    diagnosis: dict,
    decision: dict,
    db_session = None,
) -> Optional[str]:
    """
    Post a rich Block Kit escalation card to the Slack escalation channel.
    Opens a thread, captures thread_ts, and mirrors initial alert to ticket_messages.
    """
    if not SLACK_BOT_TOKEN:
        print("[slack] No SLACK_BOT_TOKEN configured — skipping Slack escalation.")
        return None

    try:
        from slack_sdk import WebClient
        from slack_sdk.errors import SlackApiError

        client = WebClient(token=SLACK_BOT_TOKEN)
        blocks = build_escalation_blocks(
            ticket_id=ticket.ticket_id,
            machine_id=ticket.machine_id,
            diagnosis=diagnosis,
            decision=decision,
        )

        top_diag = diagnosis.get("ranked_diagnoses", [{}])[0] if diagnosis.get("ranked_diagnoses") else {}
        fallback_text = f"fixer.ai Work Order for {ticket.machine_id}: {top_diag.get('diagnosis', 'Fault alert')}"

        resp = client.chat_postMessage(
            channel=SLACK_ESCALATION_CHANNEL,
            text=fallback_text,
            blocks=blocks,
            mrkdwn=True,
        )

        thread_ts = str(resp["ts"])
        print(f"[slack] Escalation card posted to {SLACK_ESCALATION_CHANNEL}. thread_ts={thread_ts}")

        # Mirror initial message to local DB if session available
        if db_session:
            try:
                ticket.slack_thread_ts = thread_ts
                msg = TicketMessage(
                    ticket_id=ticket.ticket_id,
                    machine_id=ticket.machine_id,
                    sender="bot",
                    sender_name="fixer.ai Slack Bot",
                    text=f"[Slack Escalation Opened in {SLACK_ESCALATION_CHANNEL}]\n{fallback_text}",
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    slack_ts=thread_ts,
                )
                db_session.add(msg)
                await db_session.commit()
            except Exception as e:
                print(f"[slack] DB mirror warning: {e}")

        return thread_ts

    except Exception as e:
        print(f"[slack] Escalation card post failed: {e}")
        return None
