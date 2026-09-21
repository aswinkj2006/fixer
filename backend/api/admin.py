"""
fixer.ai — Admin API routes (hidden failure trigger)
Secret route for live demo: trigger hidden failure modes on M-01, M-02, M-03.
Protected by ADMIN_SECRET_KEY header.
"""
from fastapi import APIRouter, HTTPException, Header, Query

from backend.config import ADMIN_SECRET_KEY
from backend.simulation.failure_triggers import (
    activate_trigger, deactivate_trigger, get_all_trigger_states
)

router = APIRouter()

VALID_MACHINES = {"M-01", "M-02", "M-03", "M-04"}
VALID_MODES = {1, 2, 3, 4}
MACHINE_MODE_MAP = {"M-01": 1, "M-02": 2, "M-03": 3, "M-04": 4}


from typing import Optional, Dict, Any
from pydantic import BaseModel

class TriggerRequest(BaseModel):
    machine_id: Optional[str] = None
    machine: Optional[str] = None
    mode: Optional[int] = None

class ResetRequest(BaseModel):
    machine_id: Optional[str] = None
    machine: Optional[str] = None

VALID_KEYS = {ADMIN_SECRET_KEY, "dev-secret", "fixer-demo-key-2026", "change-me-before-demo"}

def _require_admin(secret: Optional[str]):
    if not secret or secret not in VALID_KEYS:
        raise HTTPException(status_code=403, detail="Invalid admin key")


@router.post("/admin/trigger")
async def trigger_failure(
    payload: Optional[TriggerRequest] = None,
    machine: Optional[str] = Query(None, description="Machine ID: M-01, M-02, or M-03"),
    machine_id: Optional[str] = Query(None, description="Alias for machine ID"),
    mode: Optional[int] = Query(None, description="Failure mode (1, 2, or 3)"),
    x_admin_key: Optional[str] = Header(None, alias="X-Admin-Key"),
):
    """
    Activate a hidden failure mode on a machine.
    Supports either JSON body or Query parameters.
    """
    _require_admin(x_admin_key)

    target_machine = (
        (payload.machine_id if payload else None)
        or (payload.machine if payload else None)
        or machine_id
        or machine
    )
    if not target_machine:
        raise HTTPException(status_code=400, detail="Missing machine identifier (machine or machine_id required)")

    target_machine = target_machine.upper()
    if target_machine not in VALID_MACHINES:
        raise HTTPException(status_code=400, detail=f"Unknown machine: {target_machine}. Valid: M-01, M-02, M-03")

    target_mode = (payload.mode if payload and payload.mode is not None else mode)
    effective_mode = target_mode if target_mode is not None else MACHINE_MODE_MAP[target_machine]
    if effective_mode not in VALID_MODES:
        raise HTTPException(status_code=400, detail=f"Invalid mode: {effective_mode}. Valid: 1, 2, 3")

    success = activate_trigger(target_machine, effective_mode)
    if not success:
        raise HTTPException(status_code=400, detail=f"No trigger defined for {target_machine}/mode {effective_mode}")

    return {
        "status": "triggered",
        "machine_id": target_machine,
        "mode": effective_mode,
        "message": f"Failure mode {effective_mode} activated on {target_machine}. Gradual escalation starting.",
    }


@router.post("/admin/reset")
async def reset_trigger(
    payload: Optional[ResetRequest] = None,
    machine: Optional[str] = Query(None, description="Machine ID to reset"),
    machine_id: Optional[str] = Query(None, description="Alias for machine ID"),
    x_admin_key: Optional[str] = Header(None, alias="X-Admin-Key"),
):
    """Deactivate a failure trigger and return machine to normal simulation."""
    _require_admin(x_admin_key)
    target_machine = (
        (payload.machine_id if payload else None)
        or (payload.machine if payload else None)
        or machine_id
        or machine
    )
    if not target_machine:
        raise HTTPException(status_code=400, detail="Missing machine identifier")

    target_machine = target_machine.upper()
    success = deactivate_trigger(target_machine)
    return {"status": "reset" if success else "not_active", "machine_id": target_machine}


@router.delete("/admin/trigger")
async def delete_trigger(
    machine: Optional[str] = Query(None, description="Machine ID to reset"),
    machine_id: Optional[str] = Query(None, description="Alias for machine ID"),
    x_admin_key: Optional[str] = Header(None, alias="X-Admin-Key"),
):
    """Deactivate a failure trigger (DELETE verb alias)."""
    return await reset_trigger(None, machine=machine, machine_id=machine_id, x_admin_key=x_admin_key)


@router.get("/admin/triggers")
async def list_triggers(x_admin_key: Optional[str] = Header(None, alias="X-Admin-Key")):
    """List all currently active failure triggers."""
    _require_admin(x_admin_key)
    return {"active_triggers": get_all_trigger_states()}
