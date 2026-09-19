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
