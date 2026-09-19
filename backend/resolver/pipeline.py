"""
fixer.ai — Resolver Pipeline
Orchestrates the full multimodal fault diagnosis pipeline:

  1. Speech → Transcript (whisper.cpp stub)
  2. Vision → Structured defect description (Gemma 3 4B stub)
  3. RAG retrieval → Tier 1 manual excerpts + Tier 2 this-machine history
  4. Fusion → Reasoning model call with compact context (Phi-4-mini stub)
  5. Decision → Escalate / Self-resolve + technician routing
  6. DB write → Ticket + initial bot message
  7. Slack (if escalate) → Work order posted to #fixer-ai-escalations

All LLM steps marked # LLM-STUB — each becomes a real Ollama call when
switching to capable hardware (just flip LLM_STUB_MODE=false).
"""
import json
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import LLM_STUB_MODE
from backend.database.models import Ticket, TicketMessage
from backend.simulation.simulator import get_current_readings
from backend.resolver.speech import transcribe_audio
from backend.resolver.vision import analyze_image
from backend.resolver.fusion import fuse_and_reason
from backend.resolver.decision import decide_action


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


async def run_pipeline(
    machine_id: str,
    db: AsyncSession,
    symptom_text: str = "",
    audio_bytes: Optional[bytes] = None,
    audio_filename: str = "input.wav",
    image_bytes: Optional[bytes] = None,
    image_filename: str = "image.jpg",
) -> dict:
    """
    Full resolver pipeline. Returns complete result dict.

    Args:
        machine_id:     Target machine (M-01, M-02, M-03, M-04).
        db:             Active async DB session.
        symptom_text:   Free-text symptom from technician.
        audio_bytes:    Raw audio upload bytes (optional).
        audio_filename: Original audio filename.
        image_bytes:    Raw image upload bytes (optional).
        image_filename: Original image filename.

    Returns:
        {
            "ticket_id": str,
            "machine_id": str,
            "transcript": str,
            "vision_summary": dict,
            "diagnosis": dict,
            "decision": dict,
            "stub_mode": bool,
        }
    """
    # ── Step 1: Speech-to-text ────────────────────────────────────────────────
    if audio_bytes:
        transcript = await transcribe_audio(audio_bytes, audio_filename, machine_id)
    else:
        transcript = symptom_text or ""

    # ── Step 2: Vision analysis ───────────────────────────────────────────────
    vision_summary = await analyze_image(
        image_bytes or b"",
        image_filename,
        machine_id,
    )

    # ── Step 3 + 4: RAG retrieval + Fusion reasoning ──────────────────────────
    sensor_snapshot = get_current_readings(machine_id)
    diagnosis = await fuse_and_reason(
        machine_id=machine_id,
        transcript=transcript,
        vision_summary=vision_summary,
        sensor_snapshot=sensor_snapshot,
    )

    # ── Step 5: Decision node ─────────────────────────────────────────────────
    decision = await decide_action(diagnosis, machine_id, db)

    # ── Step 6: Write ticket to DB ────────────────────────────────────────────
    ticket_id = str(uuid.uuid4())
    image_ref = f"uploads/{machine_id}_{ticket_id[:8]}_{image_filename}" if image_bytes else None

    # Resolve failure_code from top diagnosis (match against known codes)
    failure_code = _infer_failure_code(machine_id, diagnosis)
    assigned_tech_id = None
    if decision.get("assigned_technician"):
        assigned_tech_id = decision["assigned_technician"]["technician_id"]

    ticket = Ticket(
        ticket_id=ticket_id,
        machine_id=machine_id,
        opened_at=_now(),
        symptom_text=symptom_text or transcript[:500] if transcript else "",
        image_ref=image_ref,
        audio_transcript=transcript,
        diagnosis=json.dumps(diagnosis),
        confidence=diagnosis.get("confidence", 0.5),
        severity=diagnosis.get("severity", "medium"),
        status="escalated" if decision["action"] == "escalate" else "open",
        assigned_technician_id=assigned_tech_id,
        failure_code=failure_code,
    )
    db.add(ticket)

    # Bot initial message
    db.add(TicketMessage(
        ticket_id=ticket_id,
        machine_id=machine_id,
        sender="bot",
        sender_name="fixer.ai",
        text=_format_bot_message(diagnosis, decision),
        timestamp=_now(),
    ))

    await db.commit()
    await db.refresh(ticket)

    # ── Step 7: Slack escalation (if required) ────────────────────────────────
    slack_thread_ts = None
    if decision["action"] == "escalate":
        try:
            slack_thread_ts = await _fire_slack_escalation(ticket, diagnosis, decision)
            if slack_thread_ts:
                ticket.slack_thread_ts = slack_thread_ts
                await db.commit()
        except Exception as e:
            print(f"[pipeline] Slack escalation failed (non-fatal): {e}")

    return {
        "ticket_id": ticket_id,
        "machine_id": machine_id,
        "transcript": transcript,
        "vision_summary": vision_summary,
        "sensor_snapshot": sensor_snapshot,
        "diagnosis": diagnosis,
        "decision": decision,
        "slack_thread_ts": slack_thread_ts,
        "stub_mode": LLM_STUB_MODE,
    }


def _infer_failure_code(machine_id: str, diagnosis: dict) -> Optional[str]:
    """
    Map the top diagnosis to a known failure code from seed data.
    Simple keyword matching — good enough for demo.
    """
    text = diagnosis.get("ranked_diagnoses", [{}])[0].get("diagnosis", "").lower()
    code_hints = {
        "M-01": [("torque", "FC-ROB-001"), ("servo", "FC-ROB-002"), ("harmonic", "FC-ROB-001")],
        "M-02": [("bearing", "FC-CNC-001"), ("vibration", "FC-CNC-001"), ("lube", "FC-CNC-002"), ("way", "FC-CNC-002")],
        "M-03": [("bearing", "FC-CNV-001"), ("thermal", "FC-CNV-001"), ("belt", "FC-CNV-002"), ("slip", "FC-CNV-002")],
        "M-04": [("drift", "FC-CAL-001"), ("calibration", "FC-CAL-001"), ("transducer", "FC-CAL-001")],
    }
    for keyword, code in code_hints.get(machine_id, []):
        if keyword in text:
            return code
    return None


def _format_bot_message(diagnosis: dict, decision: dict) -> str:
    """Format the initial bot message for the ticket thread."""
    top = diagnosis.get("ranked_diagnoses", [{}])[0]
    diag_text = top.get("diagnosis", "Fault detected")
    confidence = int(diagnosis.get("confidence", 0.5) * 100)
    severity = diagnosis.get("severity", "medium").upper()
    action = decision.get("action", "self_resolve")
    tech = decision.get("assigned_technician")
    tech_name = tech["name"] if tech else "unassigned"

    steps = diagnosis.get("repair_steps", [])
    steps_str = "\n".join(f"  {i+1}. {s}" for i, s in enumerate(steps[:4]))

    parts = diagnosis.get("parts_likely_needed", [])
    parts_str = ", ".join(parts) if parts else "Standard shop consumables"

    manual_ref = diagnosis.get("manual_reference", "")

    if action == "escalate":
        action_str = f"⚠️ ESCALATED → Assigned to {tech_name}. Slack work order sent."
    else:
        action_str = f"ℹ️ SELF-RESOLVE → Steps provided below. Escalate if unresolved after 2 hours."

    msg = (
        f"**Diagnosis**: {diag_text}\n"
        f"**Confidence**: {confidence}% | **Severity**: {severity}\n"
        f"**Evidence**: {top.get('evidence', '')}\n\n"
        f"**Action**: {action_str}\n\n"
        f"**Repair Steps**:\n{steps_str}\n\n"
        f"**Parts Likely Needed**: {parts_str}\n"
    )
    if manual_ref:
        msg += f"**Manual Reference**: {manual_ref}\n"

    rag = diagnosis.get("rag_context_used", {})
    if rag:
        msg += (
            f"\n*Context: {rag.get('manual_chunks_retrieved', 0)} manual excerpts + "
            f"{rag.get('past_tickets_retrieved', 0)} past tickets retrieved from this machine's memory.*"
        )
    return msg


async def _fire_slack_escalation(
    ticket: Ticket,
    diagnosis: dict,
    decision: dict,
) -> Optional[str]:
    """
    Post a structured Block Kit work order to Slack.
    Wired to a stub here; full implementation in slack_integration/escalation.py (Day 5).
    Returns thread timestamp on success, None on failure.
    """
    try:
        from backend.slack_integration.escalation import post_escalation_alert
        thread_ts = await post_escalation_alert(ticket=ticket, diagnosis=diagnosis, decision=decision)
        return thread_ts
    except ImportError:
        # Slack integration not yet fully built (Day 5)
        print("[pipeline] Slack escalation module not available — stub.")
        return None
    except Exception as e:
        raise e
