"""
fixer.ai — Per-machine simulation configs
One dataclass per machine, matching the 4-machine fleet in:
  02_MOCK_MACHINERY_AND_SENSOR_SIMULATION.md

Each config defines:
- Which sensors exist and their units
- OU parameters (theta, sigma, baseline) per sensor
- Duty-cycle parameters where applicable
- Whether this sensor uses vibration_step, temperature_step, ou_step, or calibration_drift_step
"""
from dataclasses import dataclass, field
from typing import Callable, Any


@dataclass
class SensorConfig:
    """Config for a single sensor signal on a machine."""
    sensor_type: str
    unit: str
    baseline: float
    theta: float        # OU mean-reversion strength
    sigma: float        # OU noise magnitude
    # Which generator function to call: 'vibration' | 'temperature' | 'ou' | 'calibration'
    generator: str = "ou"
    # Extra kwargs passed to the generator function
    extra: dict = field(default_factory=dict)
    # Whether this sensor uses a duty-cycle target (overrides baseline dynamically)
    duty_cycle: str = None  # 'robot_torque' | 'cnc_temp' | 'conveyor_current' | None


@dataclass
class MachineSimConfig:
    """Full simulation config for one machine."""
    machine_id: str
    model: str
    sensors: list[SensorConfig]


# ─────────────────────────────────────────────────────────────────────────────
# M-01 — FANUC ARC Mate 100iD (6-axis robotic welding arm)
# Sensors: torque, vibration, cycle_count
# ─────────────────────────────────────────────────────────────────────────────
M01_CONFIG = MachineSimConfig(
    machine_id="M-01",
    model="fanuc_arc_mate_100id",
    sensors=[
        SensorConfig(
            sensor_type="torque",
            unit="Nm",
            baseline=45.0,      # Mean torque during weld cycle
            theta=0.8,          # Fairly tight mean-reversion (torque tracks duty cycle closely)
            sigma=2.5,          # Low independent noise — torque tightly correlated to duty cycle
            generator="ou",
            duty_cycle="robot_torque",  # Baseline overridden by trapezoid duty cycle
            extra={
                "cycle_period": 30.0,
                "peak_torque": 110.0,
                "idle_torque": 15.0,
                "ramp_fraction": 0.15,
            },
        ),
        SensorConfig(
            sensor_type="vibration",
            unit="mm/s2",
            baseline=0.82,
            theta=1.2,
            sigma=0.12,
            generator="vibration",
            extra={
                "spike_probability": 0.025,       # ~2.5% per tick
                "spike_magnitude_multiplier": 5.0,
            },
        ),
        # cycle_count: binary flag (1 = welding, 0 = idle) — derived from duty cycle, not OU
        SensorConfig(
            sensor_type="cycle_count",
            unit="cycles",
            baseline=0.0,
            theta=0.0,
            sigma=0.0,
            generator="duty_cycle_flag",  # Special — computed from robot_torque duty cycle phase
            duty_cycle="robot_torque",
        ),
    ],
)

# ─────────────────────────────────────────────────────────────────────────────
# M-02 — Haas VF-2 CNC Precision Mill
# Sensors: vibration, temperature (spindle), rpm
# ─────────────────────────────────────────────────────────────────────────────
M02_CONFIG = MachineSimConfig(
    machine_id="M-02",
    model="haas_vf2",
    sensors=[
        SensorConfig(
            sensor_type="vibration",
            unit="mm/s2",
            baseline=1.1,
            theta=0.9,
            sigma=0.18,
            generator="vibration",
            extra={
                "spike_probability": 0.015,
                "spike_magnitude_multiplier": 4.5,
            },
        ),
        SensorConfig(
            sensor_type="temperature",
            unit="degC",
            baseline=42.0,
            theta=0.0,   # Not used for temperature — uses thermal_tau instead
            sigma=0.0,
            generator="temperature",
            duty_cycle="cnc_temp",
            extra={
                "thermal_tau": 60.0,     # 60-second thermal time constant — slow
                "small_noise_sigma": 0.15,
                "cutting_period": 120.0,
                "pause_fraction": 0.15,
                "hot_temp": 78.0,
                "ambient_temp": 22.0,
            },
        ),
        SensorConfig(
            sensor_type="rpm",
            unit="rpm",
            baseline=8000.0,
            theta=2.0,          # RPM follows commanded speed closely
            sigma=80.0,
            generator="ou",
            duty_cycle="cnc_temp",   # RPM also drops during tool-change pause (0 during pause)
            extra={
                "cutting_period": 120.0,
                "pause_fraction": 0.15,
                "idle_rpm": 0.0,
                "cutting_rpm": 8000.0,
            },
        ),
    ],
)

# ─────────────────────────────────────────────────────────────────────────────
# M-03 — Conveyor/Press Motor
# Sensors: vibration, temperature, current
# ─────────────────────────────────────────────────────────────────────────────
M03_CONFIG = MachineSimConfig(
    machine_id="M-03",
    model="generic_conveyor",
    sensors=[
        SensorConfig(
            sensor_type="vibration",
            unit="mm/s2",
            baseline=2.1,
            theta=0.7,
            sigma=0.30,
            generator="vibration",
            extra={
                "spike_probability": 0.03,        # Slightly more frequent spikes than M-01/M-02
                "spike_magnitude_multiplier": 4.0,
            },
        ),
        SensorConfig(
            sensor_type="temperature",
            unit="degC",
            baseline=55.0,
            theta=0.0,
            sigma=0.0,
            generator="temperature",
            extra={
                "thermal_tau": 90.0,      # Slower thermal response — larger motor mass
                "small_noise_sigma": 0.2,
                "cutting_period": 60.0,   # Not used for motor — steady state target
                "pause_fraction": 0.0,
                "hot_temp": 62.0,
                "ambient_temp": 22.0,
            },
        ),
        SensorConfig(
            sensor_type="current",
            unit="A",
            baseline=14.5,
            theta=1.5,
            sigma=0.8,
            generator="ou",
            duty_cycle="conveyor_current",    # Periodic load spikes
            extra={
                "spike_period": 8.0,
                "spike_width": 0.5,
                "spike_magnitude": 6.0,
            },
        ),
    ],
)

# ─────────────────────────────────────────────────────────────────────────────
# M-04 — Torque Calibration Station
# Sensors: calibration_dev only (near-flat, slow monotonic drift)
# ─────────────────────────────────────────────────────────────────────────────
M04_CONFIG = MachineSimConfig(
    machine_id="M-04",
    model="calibration_station",
    sensors=[
        SensorConfig(
            sensor_type="calibration_dev",
            unit="Nm_offset",
            baseline=0.02,
            theta=0.0,   # No mean-reversion — pure drift
            sigma=0.0,   # No OU noise — calibration deviation has deterministic drift + tiny noise
            generator="calibration",
            extra={
                "drift_rate_per_tick": 0.0003,    # Very slow: ~0.018 Nm_offset per minute at 1 tick/sec
                "recal_threshold": 0.30,
            },
        ),
    ],
)

# Lookup by machine_id
ALL_MACHINE_CONFIGS: dict[str, MachineSimConfig] = {
    "M-01": M01_CONFIG,
    "M-02": M02_CONFIG,
    "M-03": M03_CONFIG,
    "M-04": M04_CONFIG,
}
