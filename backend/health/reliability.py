"""
fixer.ai — Fleet Reliability & Downtime Analytics (ISO 14224)
Calculates:
  - MTBF (Mean Time Between Failures) in operating hours
  - MTTR (Mean Time To Repair) in hours
  - Actual vs Predicted Downtime Log
  - Overall Plant Availability & Unplanned Downtime Cost Savings
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from backend.database.models import Ticket, Machine, FailureCode

# Automotive / CNC typical unplanned downtime cost per hour ($USD)
AVERAGE_DOWNTIME_COST_PER_HOUR = 18500.0
# Average technician diagnostic lookup time saved by fixer.ai RAG per ticket (hours)
AVERAGE_LOOKUP_TIME_SAVED_HOURS = 0.75


def _parse_iso(dt_str: Optional[str]) -> Optional[datetime]:
    if not dt_str:
        return None
    try:
        # Handle ISO strings with Z or +00:00
        clean_str = dt_str.replace("Z", "+00:00")
        return datetime.fromisoformat(clean_str)
    except Exception:
        return None


async def compute_machine_reliability(machine_id: str, db: AsyncSession, window_days: int = 90) -> Dict[str, Any]:
    """
    Computes ISO 14224 reliability metrics for a single machine over a rolling window.
    """
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=window_days)
    total_window_hours = window_days * 24.0

    # Fetch tickets in window
    result = await db.execute(
        select(Ticket)
        .where(Ticket.machine_id == machine_id)
        .order_by(Ticket.opened_at.desc())
    )
    tickets = result.scalars().all()

    downtime_events = []
    total_downtime_hours = 0.0
    resolved_count = 0

    for t in tickets:
        opened = _parse_iso(t.opened_at)
        closed = _parse_iso(t.closed_at) if t.closed_at else None

        if opened and opened < cutoff and (not closed or closed < cutoff):
            continue

        if closed and opened:
            duration_hrs = max(0.2, (closed - opened).total_seconds() / 3600.0)
            status_label = "Resolved"
        elif opened:
            duration_hrs = max(0.1, (now - opened).total_seconds() / 3600.0)
            status_label = "In Progress"
        else:
            duration_hrs = 1.0
            status_label = "Resolved"

        total_downtime_hours += duration_hrs
        if t.status == "resolved":
            resolved_count += 1

        downtime_events.append({
            "ticket_id": t.ticket_id,
            "machine_id": t.machine_id,
            "opened_at": t.opened_at,
            "closed_at": t.closed_at,
            "duration_hours": round(duration_hrs, 2),
            "status": status_label,
            "severity": t.severity or "medium",
            "failure_code": t.failure_code or "UNSPECIFIED",
            "symptom": t.symptom_text[:60] if t.symptom_text else "General fault",
        })

    failure_count = len(downtime_events)
    operating_hours = max(0.0, total_window_hours - total_downtime_hours)
    
    mttr_hours = total_downtime_hours / max(1, resolved_count) if resolved_count > 0 else 0.0
    mtbf_hours = operating_hours / max(1, failure_count) if failure_count > 0 else total_window_hours
    availability_pct = (operating_hours / total_window_hours) * 100.0

    cost_avoided = resolved_count * AVERAGE_LOOKUP_TIME_SAVED_HOURS * AVERAGE_DOWNTIME_COST_PER_HOUR

    return {
        "machine_id": machine_id,
        "window_days": window_days,
        "total_window_hours": total_window_hours,
        "operating_hours": round(operating_hours, 1),
        "total_downtime_hours": round(total_downtime_hours, 1),
        "failure_count": failure_count,
        "resolved_count": resolved_count,
        "mtbf_hours": round(mtbf_hours, 1),
        "mttr_hours": round(mttr_hours, 1),
        "availability_pct": round(availability_pct, 1),
        "cost_avoided_usd": round(cost_avoided, 0),
        "recent_downtime_events": downtime_events[:10],
    }


async def compute_fleet_reliability(db: AsyncSession, window_days: int = 90) -> Dict[str, Any]:
    """
    Aggregates plant-wide reliability metrics across all 4 production assets.
    """
    res = await db.execute(select(Machine.machine_id))
    machine_ids = res.scalars().all()

    fleet_events = []
    total_operating = 0.0
    total_downtime = 0.0
    total_failures = 0
    total_resolved = 0
    total_cost_avoided = 0.0

    machine_scorecards = {}
    for mid in machine_ids:
        report = await compute_machine_reliability(mid, db=db, window_days=window_days)
        machine_scorecards[mid] = report
        total_operating += report["operating_hours"]
        total_downtime += report["total_downtime_hours"]
        total_failures += report["failure_count"]
        total_resolved += report["resolved_count"]
        total_cost_avoided += report["cost_avoided_usd"]
        fleet_events.extend(report["recent_downtime_events"])

    total_window_hours = len(machine_ids) * window_days * 24.0
    fleet_availability = (total_operating / max(1.0, total_window_hours)) * 100.0
    fleet_mttr = total_downtime / max(1, total_resolved) if total_resolved > 0 else 0.0
    fleet_mtbf = total_operating / max(1, total_failures) if total_failures > 0 else total_window_hours

    # Sort recent events descending by opened_at
    fleet_events.sort(key=lambda e: e["opened_at"] or "", reverse=True)

    return {
        "window_days": window_days,
        "total_machines": len(machine_ids),
        "fleet_operating_hours": round(total_operating, 1),
        "fleet_downtime_hours": round(total_downtime, 1),
        "fleet_failures_count": total_failures,
        "fleet_resolved_count": total_resolved,
        "fleet_mtbf_hours": round(fleet_mtbf, 1),
        "fleet_mttr_hours": round(fleet_mttr, 1),
        "fleet_availability_pct": round(fleet_availability, 1),
        "total_cost_avoided_usd": round(total_cost_avoided, 0),
        "recent_fleet_events": fleet_events[:15],
        "machine_breakdown": machine_scorecards,
    }
