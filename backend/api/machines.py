"""
fixer.ai — Machines API
GET /machines — fleet overview with health scores, RUL, OEE, active triggers
GET /machines/{machine_id} — machine detail with sensor snapshot, health, RUL
GET /machines/{machine_id}/health — dedicated prognostic health report
GET /machines/{machine_id}/rul — dedicated RUL heuristic report
GET /machines/{machine_id}/recurring-faults — Tier 2 recurring fault clusters
GET /fleet/recurring-faults — fleet-wide recurring fault leaderboard
"""
import json
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from backend.database.models import Machine, Ticket, SensorReading
from backend.simulation.simulator import get_current_readings
from backend.simulation.failure_triggers import get_all_trigger_states
from backend.health.scoring import compute_health_score, DEFAULT_BASELINES
from backend.health.rul import estimate_rul_from_db, estimate_rul_from_readings
from backend.health.reliability import compute_machine_reliability, compute_fleet_reliability
from backend.rag.recurring_faults import detect_recurring_faults, get_fleet_recurring_leaderboard

router = APIRouter()


@router.get("/machines")
async def list_machines():
    """Fleet overview — returns all 4 machines with current readings, health score, RUL, and open tickets."""
    from backend.main import AsyncSessionLocal
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Machine))
        machines = result.scalars().all()

        output = []
        for m in machines:
            readings = get_current_readings(m.machine_id)
            baseline_ranges = json.loads(m.baseline_ranges) if m.baseline_ranges else DEFAULT_BASELINES.get(m.machine_id, {})

            # Health scoring
            health_report = compute_health_score(m.machine_id, readings, baseline_ranges=baseline_ranges)

            # RUL heuristic estimation
            rul_report = await estimate_rul_from_db(m.machine_id, db=db, current_snapshot=readings)

            # Count open tickets
            open_count = await db.scalar(
                select(func.count()).select_from(Ticket).where(
                    Ticket.machine_id == m.machine_id,
                    Ticket.status.in_(["open", "escalated"])
                )
            )
            trigger_states = get_all_trigger_states()
            trigger_active = m.machine_id in trigger_states

            # Synthetic OEE (Overall Equipment Effectiveness) calculated from health & availability
            # OEE = Availability x Performance x Quality
            # Base OEE 0.88 - 0.94 for healthy machines, degrading gracefully with health score
            health_factor = health_report.health_score / 100.0
            oee_pct = round(max(40.0, min(96.5, 94.0 * health_factor)), 1)

            output.append({
                "machine_id": m.machine_id,
                "name": m.name,
                "model": m.model,
                "machine_type": m.machine_type,
                "location": m.location,
                "install_date": m.install_date,
                "current_readings": readings,
                "health_score": round(health_report.health_score, 1),
                "health_status": health_report.status,
                "primary_driver": health_report.primary_driver,
                "rul_hours": rul_report.rul_hours,
                "predicted_service_window": rul_report.service_window,
                "oee_pct": oee_pct,
                "open_tickets": open_count or 0,
                "trigger_active": trigger_active,
            })
        return output


@router.get("/machines/{machine_id}")
async def get_machine(machine_id: str):
    """Machine detail: metadata, current readings, full health score, RUL, and recent tickets."""
    from backend.main import AsyncSessionLocal
    async with AsyncSessionLocal() as db:
        machine = await db.get(Machine, machine_id)
        if not machine:
            raise HTTPException(status_code=404, detail=f"Machine {machine_id} not found")

        readings = get_current_readings(machine_id)
        baseline_ranges = json.loads(machine.baseline_ranges) if machine.baseline_ranges else DEFAULT_BASELINES.get(machine_id, {})

        # Health & RUL calculations
        health_report = compute_health_score(machine_id, readings, baseline_ranges=baseline_ranges)
        rul_report = await estimate_rul_from_db(machine_id, db=db, current_snapshot=readings)

        # Recent tickets
        result = await db.execute(
            select(Ticket)
            .where(Ticket.machine_id == machine_id)
            .order_by(Ticket.opened_at.desc())
            .limit(20)
        )
        tickets = result.scalars().all()

        trigger_states = get_all_trigger_states()
        trigger_active = machine_id in trigger_states

        return {
            "machine_id": machine.machine_id,
            "name": machine.name,
            "model": machine.model,
            "machine_type": machine.machine_type,
            "location": machine.location,
            "install_date": machine.install_date,
            "baseline_ranges": baseline_ranges,
            "current_readings": readings,
            "trigger_active": trigger_active,
            "health": health_report.to_dict(),
            "rul": rul_report.to_dict(),
            "recent_tickets": [
                {
                    "ticket_id": t.ticket_id,
                    "opened_at": t.opened_at,
                    "closed_at": t.closed_at,
                    "status": t.status,
                    "severity": t.severity,
                    "symptom_text": t.symptom_text,
                    "failure_code": t.failure_code,
                    "confidence": t.confidence,
                }
                for t in tickets
            ],
        }


@router.get("/machines/{machine_id}/health")
async def get_machine_health(machine_id: str):
    """Prognostic health assessment report for a single machine."""
    from backend.main import AsyncSessionLocal
    async with AsyncSessionLocal() as db:
        machine = await db.get(Machine, machine_id)
        if not machine:
            raise HTTPException(status_code=404, detail=f"Machine {machine_id} not found")

        readings = get_current_readings(machine_id)
        baseline_ranges = json.loads(machine.baseline_ranges) if machine.baseline_ranges else DEFAULT_BASELINES.get(machine_id, {})
        report = compute_health_score(machine_id, readings, baseline_ranges=baseline_ranges)
        return report.to_dict()


@router.get("/machines/{machine_id}/rul")
async def get_machine_rul(machine_id: str):
    """Remaining Useful Life trend-based extrapolation heuristic for a single machine."""
    from backend.main import AsyncSessionLocal
    async with AsyncSessionLocal() as db:
        machine = await db.get(Machine, machine_id)
        if not machine:
            raise HTTPException(status_code=404, detail=f"Machine {machine_id} not found")

        readings = get_current_readings(machine_id)
        report = await estimate_rul_from_db(machine_id, db=db, current_snapshot=readings)
        return report.to_dict()


@router.get("/machines/{machine_id}/recurring-faults")
async def get_machine_recurring_faults(machine_id: str, threshold: float = Query(0.80, ge=0.5, le=1.0)):
    """Clusters of recurring fault patterns detected from this machine's Tier 2 memory."""
    from backend.main import AsyncSessionLocal
    async with AsyncSessionLocal() as db:
        machine = await db.get(Machine, machine_id)
        if not machine:
            raise HTTPException(status_code=404, detail=f"Machine {machine_id} not found")

        clusters = detect_recurring_faults(machine_id, similarity_threshold=threshold)
        return {
            "machine_id": machine_id,
            "cluster_count": len(clusters),
            "clusters": [c.to_dict() for c in clusters],
        }


@router.get("/fleet/recurring-faults")
async def get_fleet_recurring_faults():
    """Fleet-wide recurring fault leaderboard for executive dashboard."""
    leaderboard = get_fleet_recurring_leaderboard()
    return {
        "count": len(leaderboard),
        "leaderboard": leaderboard,
    }


@router.get("/machines/{machine_id}/report")
async def get_machine_report(machine_id: str):
    """
    Generate a formal ISO 14224 / AS9100 Plant Maintenance Diagnostic & Shift Handover Report.
    Returns both structured JSON metrics and formatted printable text.
    """
    from datetime import datetime, timezone
    from backend.main import AsyncSessionLocal
    async with AsyncSessionLocal() as db:
        machine = await db.get(Machine, machine_id)
        if not machine:
            raise HTTPException(status_code=404, detail=f"Machine {machine_id} not found")

        readings = get_current_readings(machine_id)
        baseline_ranges = json.loads(machine.baseline_ranges) if machine.baseline_ranges else DEFAULT_BASELINES.get(machine_id, {})
        health_report = compute_health_score(machine_id, readings, baseline_ranges=baseline_ranges)
        rul_report = await estimate_rul_from_db(machine_id, db=db, current_snapshot=readings)
        clusters = detect_recurring_faults(machine_id)

        result = await db.execute(
            select(Ticket)
            .where(Ticket.machine_id == machine_id)
            .order_by(Ticket.opened_at.desc())
            .limit(5)
        )
        recent_tickets = result.scalars().all()

        now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

        # Build formatted report
        lines = [
            "=" * 80,
            "FIXER.AI — INDUSTRIAL EQUIPMENT DIAGNOSTIC & SHIFT HANDOVER REPORT",
            "=" * 80,
            f"Asset ID        : {machine.machine_id}",
            f"Asset Name      : {machine.name}",
            f"Model / Class   : {machine.model} ({machine.machine_type})",
            f"Shop Location   : {machine.location}",
            f"Installed Date  : {machine.install_date}",
            f"Report Timestamp: {now_str}",
            "-" * 80,
            "1. CONDITION MONITORING & HEALTH STATUS (ISO 10816)",
            f"   Current Health Score : {round(health_report.health_score, 1)}% [{health_report.status.upper()}]",
            f"   Primary Fault Driver : {health_report.primary_driver or 'None (All signals within nominal envelope)'}",
            "   Active Sensor Breakdown:",
        ]

        for s_key, s_detail in health_report.sensor_details.items():
            lines.append(
                f"     • {s_key:<16}: {s_detail.current_value:>7.2f} {s_detail.unit:<5} "
                f"(Baseline: {s_detail.baseline_mean:>7.2f}, Z: {s_detail.z_score:>+5.2f}, Health: {s_detail.sensor_health_score:>5.1f}%)"
            )

        lines.extend([
            "-" * 80,
            "2. PROGNOSTIC REMAINING USEFUL LIFE (RUL)",
            f"   Predicted Window     : {rul_report.service_window}",
            f"   Hours Remaining      : {f'{rul_report.rul_hours:.1f} hrs' if rul_report.rul_hours else 'Nominal (> 720 hrs)'}",
            f"   Critical Driver      : {rul_report.critical_sensor or 'None'}",
            f"   Methodology Notice   : {rul_report.heuristic_disclosure}",
            "-" * 80,
            "3. TIER 2 ISOLATED VECTOR MEMORY & RECURRING FAULT CLUSTERS",
            f"   Detected Patterns    : {len(clusters)} recurring historical failure modes",
        ])

        if clusters:
            for idx, c in enumerate(clusters, 1):
                lines.append(f"   [{idx}] {c.pattern_name} ({c.occurrence_count} occurrences, Severity: {c.severity.upper()})")
                lines.append(f"       Diagnostic Insight   : {c.summary_insight}")
                lines.append(f"       Longest-Lasting Fix  : {c.longest_lasting_fix}")
        else:
            lines.append("   (No recurring failure clusters exceeding threshold in Tier 2 memory)")

        lines.extend([
            "-" * 80,
            "4. RECENT CMMS WORK ORDER LOG (ISO 14224)",
        ])

        if recent_tickets:
            for t in recent_tickets:
                lines.append(
                    f"   • Ticket #{t.ticket_id[:8]} | {t.opened_at[:10]} | Status: {t.status.upper():<9} | "
                    f"Severity: {t.severity.upper():<8} | {t.symptom_text[:50]}..."
                )
        else:
            lines.append("   (No maintenance tickets logged for this unit)")

        lines.extend([
            "=" * 80,
            "OPERATOR SIGN-OFF:",
            "Lead Technician: ________________________   Date: ______________",
            "=" * 80,
        ])

        formatted_text = "\n".join(lines)

        return {
            "machine_id": machine.machine_id,
            "timestamp": now_str,
            "health_score": round(health_report.health_score, 1),
            "status": health_report.status,
            "rul_window": rul_report.service_window,
            "cluster_count": len(clusters),
            "formatted_report": formatted_text,
        }


@router.get("/fleet/reliability")
async def get_fleet_reliability_metrics(window_days: int = 90):
    """
    Fleet-wide ISO 14224 reliability metrics (MTBF, MTTR, availability %, cost savings).
    """
    from backend.main import AsyncSessionLocal
    async with AsyncSessionLocal() as db:
        return await compute_fleet_reliability(db=db, window_days=window_days)


@router.get("/machines/{machine_id}/reliability")
async def get_machine_reliability_metrics(machine_id: str, window_days: int = 90):
    """
    Asset-specific ISO 14224 reliability and downtime history.
    """
    from backend.main import AsyncSessionLocal
    async with AsyncSessionLocal() as db:
        machine = await db.get(Machine, machine_id)
        if not machine:
            raise HTTPException(status_code=404, detail=f"Machine {machine_id} not found")
        return await compute_machine_reliability(machine_id=machine_id, db=db, window_days=window_days)


from pydantic import BaseModel

class FaultInjectionRequest(BaseModel):
    mode: Optional[int] = None

class MachineFixRequest(BaseModel):
    technician_notes: Optional[str] = None
    technician_id: Optional[str] = "Tech-Lead-01"


@router.post("/machines/{machine_id}/fault")
async def inject_machine_fault(machine_id: str, payload: Optional[FaultInjectionRequest] = None):
    """
    Induce a realistic physical trouble state on the machine (for 3D Digital Twin simulation).
    """
    from backend.simulation.failure_triggers import activate_trigger
    mid = machine_id.upper()
    mode_map = {"M-01": 1, "M-02": 2, "M-03": 3, "M-04": 4}
    mode = (payload.mode if payload and payload.mode is not None else mode_map.get(mid, 1))

    success = activate_trigger(mid, mode)
    if not success:
        raise HTTPException(status_code=400, detail=f"Failed to activate fault for {mid}")

    fault_descriptions = {
        "M-01": "Joint 2 Reducer grease seal degradation with rising axis friction and torque.",
        "M-02": "Spindle bearing inner race spalling causing vibration rise and thermal buildup.",
        "M-03": "Conveyor motor stator overload and friction binding causing elevated current draw.",
        "M-04": "AS9100 metrology reaction torque transducer calibration drift beyond tolerance.",
    }

    return {
        "status": "fault_active",
        "machine_id": mid,
        "mode": mode,
        "description": fault_descriptions.get(mid, "Failure mode activated."),
    }


@router.post("/machines/{machine_id}/fix")
async def fix_machine(machine_id: str, payload: Optional[MachineFixRequest] = None):
    """
    Execute 1-click physical repair on machine:
    1. Deactivates failure trigger and resets simulator to healthy baseline.
    2. Auto-resolves any open tickets for this machine and embeds them into Tier 2 vector memory.
    3. Broadcasts normalized telemetry immediately via WebSocket.
    4. Returns updated healthy snapshot.
    """
    from datetime import datetime, timezone
    from backend.simulation.simulator import reset_machine_simulator
    from backend.rag.continual_learning import embed_resolved_ticket
    from backend.database.models import Ticket, TicketMessage
    from backend.main import AsyncSessionLocal

    mid = machine_id.upper()
    normal_readings = reset_machine_simulator(mid)

    remedy_descriptions = {
        "M-01": "Purged degraded grease cavity, flushed with Mobilux EP2 synthetic lubricant, and torqued seal flange to 85 Nm.",
        "M-02": "Replaced spindle ceramic hybrid bearing set, replenished micro-fog lubrication, and verified radial runout (<1.2 µm).",
        "M-03": "Cleared conveyor mechanical bind, realigned shaft flex-coupler, and verified 3-phase stator current balance.",
        "M-04": "Completed AS9100 optical laser zero recalibration routine and re-indexed reaction torque transducer.",
    }

    remedy = remedy_descriptions.get(mid, "Equipment physical maintenance and calibration successfully completed.")
    notes = (payload.technician_notes if payload and payload.technician_notes else remedy)
    tech_id = (payload.technician_id if payload and payload.technician_id else "Lead-Technician")

    tickets_resolved = []
    async with AsyncSessionLocal() as db:
        # Find any open or escalated tickets for this machine
        result = await db.execute(
            select(Ticket).where(
                Ticket.machine_id == mid,
                Ticket.status.in_(["open", "escalated"])
            )
        )
        open_tickets = result.scalars().all()

        now_iso = datetime.now(timezone.utc).isoformat()
        for t in open_tickets:
            t.status = "resolved"
            t.closed_at = now_iso
            t.resolution_summary = remedy
            t.assigned_technician_id = tech_id

            msg = TicketMessage(
                ticket_id=t.ticket_id,
                machine_id=mid,
                sender="technician",
                sender_name=tech_id,
                text=f"Physical repair executed via 3D Digital Twin Workbench: {remedy}",
                timestamp=now_iso,
            )
            db.add(msg)
            tickets_resolved.append(t.ticket_id)

        await db.commit()

        # Embed resolved tickets into Tier 2 continual learning memory
        for tid in tickets_resolved:
            try:
                await embed_resolved_ticket(ticket_id=tid, session=db)
            except Exception:
                pass

    return {
        "status": "repaired",
        "machine_id": mid,
        "message": f"Machine {mid} physically repaired and restored to nominal operating state.",
        "remedy": remedy,
        "resolved_tickets": tickets_resolved,
        "current_readings": normal_readings,
    }


