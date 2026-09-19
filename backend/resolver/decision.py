"""
fixer.ai — Decision Node
Takes the fusion diagnosis and decides the action:
  - LOW severity + HIGH confidence → guided self-resolve (show steps to on-site technician)
  - HIGH severity OR low confidence OR specialist required → escalate via Slack work order

Also selects the right technician based on specialty match.
"""
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.database.models import Technician


# Severity escalation thresholds (per spec §5 decision node)
ESCALATE_SEVERITIES = {"high", "critical"}
CONFIDENCE_ESCALATION_THRESHOLD = 0.50   # below this → escalate even if low severity


async def decide_action(
    diagnosis: dict,
    machine_id: str,
    db: AsyncSession,
) -> dict:
    """
    Evaluate the diagnosis and determine the response action.

    Returns:
        {
            "action": "self_resolve" | "escalate",
            "reason": str,
            "assigned_technician": dict | None,
            "slack_alert": bool,
        }
    """
    severity = diagnosis.get("severity", "medium").lower()
    confidence = float(diagnosis.get("confidence", 0.5))
    specialist = diagnosis.get("specialist_required", "general").lower()

    should_escalate = (
        severity in ESCALATE_SEVERITIES
        or confidence < CONFIDENCE_ESCALATION_THRESHOLD
    )

    technician = await _select_technician(specialist, db)

    if should_escalate:
        reason = _escalation_reason(severity, confidence)
        return {
            "action": "escalate",
            "reason": reason,
            "assigned_technician": _serialize_tech(technician),
            "slack_alert": True,
        }
    else:
        return {
            "action": "self_resolve",
            "reason": (
                f"Severity '{severity}' with {int(confidence * 100)}% confidence — "
                "guided self-resolve steps provided. Escalate if issue persists."
            ),
            "assigned_technician": _serialize_tech(technician),
            "slack_alert": False,
        }


def _escalation_reason(severity: str, confidence: float) -> str:
    if severity == "critical":
        return f"CRITICAL severity — immediate production stop required. Paging specialist on-call."
    if severity == "high":
        return f"HIGH severity fault detected ({int(confidence * 100)}% confidence). Specialist work order generated."
    if confidence < CONFIDENCE_ESCALATION_THRESHOLD:
        return f"Low diagnostic confidence ({int(confidence * 100)}%) — escalating for specialist inspection."
    return "Escalation triggered by decision policy."


async def _select_technician(specialty: str, db: AsyncSession) -> Optional[Technician]:
    """
    Select the best available technician matching the required specialty.
    Falls back to any technician if no specialty match.
    """
    # Try exact specialty match
    result = await db.execute(
        select(Technician).where(Technician.specialty == specialty).limit(1)
    )
    tech = result.scalar_one_or_none()
    if tech:
        return tech

    # Fallback: return first available technician
    result = await db.execute(select(Technician).limit(1))
    return result.scalar_one_or_none()


def _serialize_tech(tech: Optional[Technician]) -> Optional[dict]:
    if tech is None:
        return None
    return {
        "technician_id": tech.technician_id,
        "name": tech.name,
        "specialty": tech.specialty,
        "slack_user_id": tech.slack_user_id,
    }
