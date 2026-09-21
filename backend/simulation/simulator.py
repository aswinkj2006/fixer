"""
fixer.ai — Main simulation loop

Generates sensor readings for all 4 machines on each tick, applies:
1. Normal OU / duty-cycle / noise model (per machines.py)
2. Active failure trigger modifications (per failure_triggers.py)
3. Writes readings to SQLite DB
4. Broadcasts readings via WebSocket to all connected frontend clients

SIM_CLOCK_MULTIPLIER: how many real seconds per simulated second.
  Default 600 = 1 real second = 10 simulated minutes.
  This makes "weeks" of drift visible in a few demo minutes.
"""
import asyncio
import json
import time
from datetime import datetime, timezone

import numpy as np

from backend.config import SIM_CLOCK_MULTIPLIER, SIM_TICK_INTERVAL
from backend.simulation.machines import ALL_MACHINE_CONFIGS, SensorConfig
from backend.simulation.ou_process import (
    ou_step, vibration_step, temperature_step, calibration_drift_step,
    robot_torque_duty_cycle, cnc_temp_target, conveyor_current_load_spike
)
from backend.simulation.failure_triggers import (
    active_triggers, get_trigger_state,
    Mode1TorqueDrift, Mode2BearingWear, Mode3MotorFault, Mode4CalibrationDrift, TRIGGER_CLASSES
)


class MachineSimulator:
    """
    Stateful simulator for a single machine.
    Maintains current sensor values across ticks.
    """

    def __init__(self, config, rng_seed: int = None):
        self.config = config
        self.machine_id = config.machine_id
        self.rng = np.random.default_rng(rng_seed)
        self.sim_time: float = 0.0  # Simulation time in seconds

        # Initialize current values at baseline
        self.current_values: dict[str, float] = {
            sc.sensor_type: sc.baseline for sc in config.sensors
        }

    def reset_to_baseline(self):
        """Instantly reset all current sensor values to nominal baseline upon repair."""
        for sc in self.config.sensors:
            self.current_values[sc.sensor_type] = sc.baseline

    def tick(self, dt_real: float = 1.0) -> dict[str, float]:
        """
        Advance simulation by one real-time tick.
        dt_real: real-time seconds elapsed
        Returns dict of {sensor_type: value} for this tick.
        """
        dt_sim = dt_real * SIM_CLOCK_MULTIPLIER
        self.sim_time += dt_sim

        trigger_state = get_trigger_state(self.machine_id)
        if trigger_state:
            trigger_state.tick(dt_sim)

        readings = {}
        for sc in self.config.sensors:
            readings[sc.sensor_type] = self._step_sensor(sc, dt_sim, trigger_state)
            self.current_values[sc.sensor_type] = readings[sc.sensor_type]

        return readings

    def _step_sensor(
        self,
        sc: SensorConfig,
        dt_sim: float,
        trigger_state
    ) -> float:
        """Generate next value for one sensor."""
        current = self.current_values[sc.sensor_type]
        t = trigger_state.t_since_trigger if trigger_state else 0.0
        trigger_class = TRIGGER_CLASSES.get((self.machine_id, trigger_state.mode)) if trigger_state else None

        # ── Compute effective baseline (may be modified by duty cycle or trigger) ──
        baseline = sc.baseline
        sigma = sc.sigma
        theta = sc.theta

        # Apply duty-cycle baseline modification
        if sc.duty_cycle == "robot_torque":
            extras = sc.extra
            if sc.sensor_type == "cycle_count":
                # Derive cycle flag from torque duty cycle phase
                phase = (self.sim_time % extras.get("cycle_period", 30.0)) / extras.get("cycle_period", 30.0)
                return 1.0 if 0.15 < phase < 0.65 else 0.0
            baseline = robot_torque_duty_cycle(
                self.sim_time,
                cycle_period=extras.get("cycle_period", 30.0),
                peak_torque=extras.get("peak_torque", 110.0),
                idle_torque=extras.get("idle_torque", 15.0),
                ramp_fraction=extras.get("ramp_fraction", 0.15),
            )

        elif sc.duty_cycle == "cnc_temp" and sc.sensor_type == "rpm":
            extras = sc.extra
            period = extras.get("cutting_period", 120.0)
            pause_frac = extras.get("pause_fraction", 0.15)
            phase = (self.sim_time % period) / period
            baseline = extras.get("idle_rpm", 0.0) if phase > (1.0 - pause_frac) else extras.get("cutting_rpm", 8000.0)

        # ── Apply failure trigger parameter modifications ──
        if trigger_class is not None:
            if trigger_class is Mode1TorqueDrift and sc.sensor_type == "torque":
                baseline = Mode1TorqueDrift.modified_baseline(sc.baseline, t)
            elif trigger_class is Mode2BearingWear and sc.sensor_type == "vibration":
                baseline = Mode2BearingWear.modified_baseline(sc.baseline, t)
                sigma = Mode2BearingWear.modified_sigma(sc.sigma, t)
            elif trigger_class is Mode3MotorFault and sc.sensor_type == "current":
                baseline = sc.baseline + Mode3MotorFault.current_delta(t)
            elif trigger_class is Mode4CalibrationDrift and sc.sensor_type == "calibration_dev":
                baseline = Mode4CalibrationDrift.modified_baseline(sc.baseline, t)
            # Mode 3 vibration spike probability modification is handled below

        # ── Generate value using appropriate generator ──
        if sc.generator == "vibration":
            extras = sc.extra.copy()
            if trigger_class is Mode3MotorFault and sc.sensor_type == "vibration":
                extras["spike_probability"] = Mode3MotorFault.vibration_spike_probability(
                    extras.get("spike_probability", 0.03), t
                )
            return vibration_step(
                current, baseline, theta, sigma, dt_sim,
                spike_probability=extras.get("spike_probability", 0.02),
                spike_magnitude_multiplier=extras.get("spike_magnitude_multiplier", 5.0),
                rng=self.rng,
            )

        elif sc.generator == "temperature":
            extras = sc.extra
            target = cnc_temp_target(
                self.sim_time,
                cutting_period=extras.get("cutting_period", 120.0),
                pause_fraction=extras.get("pause_fraction", 0.15),
                hot_temp=extras.get("hot_temp", 78.0),
                ambient_temp=extras.get("ambient_temp", 22.0),
            ) if sc.duty_cycle == "cnc_temp" else extras.get("hot_temp", 55.0)
            # Temperature failure trigger: baseline drifts to higher hot_temp (not implemented as trigger — M-02 trigger is vibration)
            return temperature_step(
                current, target,
                thermal_tau=extras.get("thermal_tau", 60.0),
                dt=dt_sim,
                small_noise_sigma=extras.get("small_noise_sigma", 0.05),
                rng=self.rng,
            )

        elif sc.generator == "calibration":
            extras = sc.extra
            return calibration_drift_step(
                current,
                drift_rate_per_tick=extras.get("drift_rate_per_tick", 0.0003),
                recal_threshold=extras.get("recal_threshold", 0.30),
                rng=self.rng,
            )

        elif sc.generator == "duty_cycle_flag":
            # Already handled above in duty_cycle branch
            return current

        else:
            # Standard OU
            return ou_step(current, baseline, theta, sigma, dt_sim, rng=self.rng)


# ─────────────────────────────────────────────────────────────────────────────
# Global simulator instances — one per machine
# ─────────────────────────────────────────────────────────────────────────────
_simulators: dict[str, MachineSimulator] = {}
_ws_broadcast_callback = None   # Set by WebSocket router on startup


def init_simulators():
    """Initialize simulator instances for all 4 machines."""
    for machine_id, config in ALL_MACHINE_CONFIGS.items():
        _simulators[machine_id] = MachineSimulator(config, rng_seed=hash(machine_id) % 2**31)


def set_ws_broadcast_callback(callback):
    """Register the WebSocket broadcast function (called by api/websocket.py)."""
    global _ws_broadcast_callback
    _ws_broadcast_callback = callback


async def run_simulation_loop(db_session_factory):
    """
    Main async simulation loop.
    - Ticks all simulators at SIM_TICK_INTERVAL intervals
    - Writes sensor readings to DB
    - Broadcasts readings via WebSocket
    """
    from backend.database.models import SensorReading
    init_simulators()

    while True:
        tick_start = time.monotonic()
        timestamp = datetime.now(timezone.utc).isoformat()

        async with db_session_factory() as session:
            for machine_id, sim in _simulators.items():
                readings = sim.tick(dt_real=SIM_TICK_INTERVAL)

                for sensor_type, value in readings.items():
                    # Get unit from config
                    cfg = ALL_MACHINE_CONFIGS[machine_id]
                    sensor_cfg = next(s for s in cfg.sensors if s.sensor_type == sensor_type)

                    db_reading = SensorReading(
                        machine_id=machine_id,
                        timestamp=timestamp,
                        sensor_type=sensor_type,
                        value=round(float(value), 4),
                        unit=sensor_cfg.unit,
                    )
                    session.add(db_reading)

                # Broadcast to WebSocket clients for this machine
                if _ws_broadcast_callback:
                    payload = {
                        "machine_id": machine_id,
                        "timestamp": timestamp,
                        "readings": {k: round(float(v), 4) for k, v in readings.items()},
                    }
                    await _ws_broadcast_callback(machine_id, json.dumps(payload))

            await session.commit()

        # Maintain tick interval
        elapsed = time.monotonic() - tick_start
        sleep_time = max(0.0, SIM_TICK_INTERVAL - elapsed)
        await asyncio.sleep(sleep_time)


def get_current_readings(machine_id: str) -> dict[str, float]:
    """Get the latest in-memory sensor values for a machine (for API snapshot)."""
    sim = _simulators.get(machine_id)
    if sim is None:
        return {}
    return {k: round(float(v), 4) for k, v in sim.current_values.items()}


def reset_machine_simulator(machine_id: str) -> dict[str, float]:
    """Deactivate trigger and reset sensor simulator to baseline for machine_id."""
    from backend.simulation.failure_triggers import deactivate_trigger
    deactivate_trigger(machine_id)
    sim = _simulators.get(machine_id)
    if sim:
        sim.reset_to_baseline()
        return {k: round(float(v), 4) for k, v in sim.current_values.items()}
    return {}

