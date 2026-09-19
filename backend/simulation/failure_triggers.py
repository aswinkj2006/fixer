"""
fixer.ai — Hidden failure trigger presets (3 modes, gradual escalation)

Spec: 02_MOCK_MACHINERY_AND_SENSOR_SIMULATION.md §Three hidden failure trigger modes

CRITICAL design rule from spec:
  Do NOT make these instant spike triggers.
  Each mode modifies the simulation parameters to cause GRADUAL escalation
  that develops over the demo window (simulation clock runs faster than real time,
  so "weeks" of drift compress into minutes).

Admin route: POST /admin/trigger?machine=M01&mode=1
This swaps the affected machine's generator parameters to the failure preset.
Everything else keeps running on the normal OU/duty-cycle model.

Implementation: each trigger returns a callable that, given (current_params, t_since_trigger),
returns modified params. The simulator applies these modifications on each tick.
"""
import numpy as np
from typing import Any


# ─────────────────────────────────────────────────────────────────────────────
# Trigger state — mutable dict held by the simulator
# ─────────────────────────────────────────────────────────────────────────────

class FailureTriggerState:
    """
    Holds the active failure trigger state for one machine.
    The simulator calls apply() on each tick to get modified sensor parameters.
    """

    def __init__(self, machine_id: str, mode: int):
        self.machine_id = machine_id
        self.mode = mode
        self.t_since_trigger: float = 0.0   # simulation ticks since trigger activated
        self.active: bool = True

    def tick(self, dt_sim: float = 1.0):
        """Advance the trigger time counter by one simulation tick."""
        if self.active:
            self.t_since_trigger += dt_sim

    def deactivate(self):
        self.active = False


# ─────────────────────────────────────────────────────────────────────────────
# MODE 1 — M-01 Robotic Arm: Grease Leak (Rising Torque)
# Torque baseline climbs exponentially: baseline += A * (exp(k*t) - 1)
# Mimics increasing friction from grease-leak-driven lubrication loss
# ─────────────────────────────────────────────────────────────────────────────

class Mode1TorqueDrift:
    """
    M-01 failure trigger.
    Exponential torque baseline escalation.
    Parameters tuned so full escalation (idle_torque doubles) takes ~10 demo minutes
    at SIM_CLOCK_MULTIPLIER=600 (= ~100 real-hours of wear in 10 minutes).
    """
    A = 2.0          # Amplitude: additional Nm at t_ref
    k = 0.0005       # Growth rate constant (per simulation tick)
    # At t=1000 ticks: baseline += 2 * (e^0.5 - 1) ≈ 1.3 Nm (subtle start)
    # At t=5000 ticks: baseline += 2 * (e^2.5 - 1) ≈ 22 Nm (clearly escalated)

    @classmethod
    def modified_baseline(cls, original_baseline: float, t: float) -> float:
        """Return the escalated torque baseline at time t since trigger."""
        drift = cls.A * (np.exp(cls.k * t) - 1.0)
        return original_baseline + drift

    @classmethod
    def health_impact(cls, t: float) -> float:
        """Returns 0..1 health degradation factor (0 = healthy, 1 = critical)."""
        return min(1.0, (np.exp(cls.k * t) - 1.0) / 20.0)


# ─────────────────────────────────────────────────────────────────────────────
# MODE 2 — M-02 CNC Mill: Spindle Bearing Wear
# Vibration sigma increases over time + slow upward baseline shift
# Mimics bearing-wear-induced vibration growth (kurtosis increases too)
# ─────────────────────────────────────────────────────────────────────────────

class Mode2BearingWear:
    """
    M-02 failure trigger.
    Vibration sigma grows linearly + baseline shifts upward exponentially.
    At high sigma values, the kurtosis of the vibration signal naturally increases
    (heavy-tail behavior amplified — consistent with bearing defect frequency harmonics).
    """
    sigma_growth_rate = 0.0001   # sigma units per tick
    baseline_A = 0.5             # Max baseline shift (mm/s2)
    baseline_k = 0.0003          # Exponential rate for baseline drift

    @classmethod
    def modified_sigma(cls, original_sigma: float, t: float) -> float:
        return original_sigma + cls.sigma_growth_rate * t

    @classmethod
    def modified_baseline(cls, original_baseline: float, t: float) -> float:
        return original_baseline + cls.baseline_A * (np.exp(cls.baseline_k * t) - 1.0)

    @classmethod
    def health_impact(cls, t: float) -> float:
        sigma_increase = cls.sigma_growth_rate * t
        return min(1.0, sigma_increase / 0.8)  # Fully critical when sigma has grown by 0.8


# ─────────────────────────────────────────────────────────────────────────────
# MODE 3 — M-03 Conveyor Motor: Developing Motor Fault
# Current baseline steps upward + vibration spike frequency increases
# Mimics developing motor fault (bearing spalling → increased friction → current rise)
# ─────────────────────────────────────────────────────────────────────────────

class Mode3MotorFault:
    """
    M-03 failure trigger.
    Current baseline steps upward as a piecewise function of time (not smooth — real motor
    faults often progress in bursts, not a smooth curve). Vibration spike probability
    also increases monotonically.
    """
    # Current baseline step function: gradual plateaus (more realistic than smooth curve)
    current_steps = [
        (0, 0.0),        # t=0: no change
        (500, 1.5),      # t=500: +1.5A (subtle — just above noise)
        (1500, 4.0),     # t=1500: +4.0A (clearly elevated)
        (3000, 8.5),     # t=3000: +8.5A (serious — near overload)
    ]
    max_spike_prob = 0.12           # Max vibration spike probability (vs 0.03 normal)
    spike_prob_growth = 0.00003     # Per tick

    @classmethod
    def current_delta(cls, t: float) -> float:
        """Returns the additional current draw above normal baseline at time t."""
        delta = 0.0
        for threshold, value in cls.current_steps:
            if t >= threshold:
                delta = value
        return delta

    @classmethod
    def vibration_spike_probability(cls, original_prob: float, t: float) -> float:
        additional = min(cls.max_spike_prob, cls.spike_prob_growth * t)
        return original_prob + additional

    @classmethod
    def health_impact(cls, t: float) -> float:
        return min(1.0, cls.current_delta(t) / 8.5)


# ─────────────────────────────────────────────────────────────────────────────
# Registry — used by simulator and admin route
# ─────────────────────────────────────────────────────────────────────────────

TRIGGER_CLASSES = {
    ("M-01", 1): Mode1TorqueDrift,
    ("M-02", 2): Mode2BearingWear,
    ("M-03", 3): Mode3MotorFault,
}

# Active triggers (machine_id → FailureTriggerState), managed by simulator
active_triggers: dict[str, FailureTriggerState] = {}


def activate_trigger(machine_id: str, mode: int) -> bool:
    """
    Activate a failure trigger for a machine.
    Returns True if successful, False if machine/mode combination not valid.
    """
    key = (machine_id, mode)
    if key not in TRIGGER_CLASSES:
        return False
    active_triggers[machine_id] = FailureTriggerState(machine_id, mode)
    return True


def deactivate_trigger(machine_id: str) -> bool:
    """Deactivate the active trigger for a machine (return to normal simulation)."""
    if machine_id in active_triggers:
        active_triggers[machine_id].deactivate()
        del active_triggers[machine_id]
        return True
    return False


def get_trigger_state(machine_id: str) -> FailureTriggerState | None:
    return active_triggers.get(machine_id)


def get_all_trigger_states() -> dict[str, dict]:
    """Returns serializable state for all active triggers."""
    return {
        mid: {
            "machine_id": ts.machine_id,
            "mode": ts.mode,
            "t_since_trigger": ts.t_since_trigger,
            "active": ts.active,
        }
        for mid, ts in active_triggers.items()
    }
