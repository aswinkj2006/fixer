"""
fixer.ai — Health Assessment & Prognostic Scoring
Spec: 01_ARCHITECTURE.md §4, 05_BUILD_PLAN_6_DAYS.md Day 4

Calculates an industrial health score (0–100) per machine:
- Evaluates sensor signals against that machine's historical baseline (mean + variance).
- Uses industrial weakest-link prognostic modeling (ISO 10816 & multi-sensor condition index):
  a machine with a severe vibration anomaly is critical even if temperature is nominal.
- Smoothly degrades as sensor metrics deviate from operational envelopes.
- Status categorization:
    * >= 85.0: "healthy" (Nominal operation)
    * 60.0 - 84.9: "warning" (Developing anomaly / inspection recommended)
    * < 60.0: "critical" (Immediate maintenance / potential failure)
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
import json
import math

from backend.simulation.machines import ALL_MACHINE_CONFIGS


# ─────────────────────────────────────────────────────────────────────────────
# Default baseline fallback values per machine if DB baseline_ranges is empty
# ─────────────────────────────────────────────────────────────────────────────
DEFAULT_BASELINES: Dict[str, Dict[str, Dict[str, Any]]] = {
    "M-01": {
        "torque": {"mean": 45.0, "std": 3.2, "min": 15.0, "max": 115.0, "unit": "Nm", "critical_high": 125.0},
        "vibration": {"mean": 0.82, "std": 0.12, "min": 0.0, "max": 2.2, "unit": "mm/s2", "critical_high": 2.8},
        "cycle_count": {"mean": 0.0, "std": 0.0, "min": 0.0, "max": 1.0, "unit": "cycles"},
    },
    "M-02": {
        "vibration": {"mean": 1.1, "std": 0.18, "min": 0.0, "max": 2.5, "unit": "mm/s2", "critical_high": 3.8},
        "temperature": {"mean": 42.0, "std": 5.0, "min": 20.0, "max": 80.0, "unit": "degC", "critical_high": 85.0},
        "rpm": {"mean": 8000.0, "std": 200.0, "min": 0.0, "max": 8500.0, "unit": "rpm", "critical_low": 7200.0},
    },
    "M-03": {
        "vibration": {"mean": 2.1, "std": 0.30, "min": 0.0, "max": 4.5, "unit": "mm/s2", "critical_high": 6.0},
        "temperature": {"mean": 55.0, "std": 4.0, "min": 20.0, "max": 75.0, "unit": "degC", "critical_high": 85.0},
        "current": {"mean": 14.5, "std": 1.2, "min": 0.0, "max": 21.5, "unit": "A", "critical_high": 23.5},
    },
    "M-04": {
        "calibration_dev": {"mean": 0.02, "std": 0.005, "min": -0.15, "max": 0.15, "unit": "Nm_offset", "critical_high": 0.30},
    },
}


@dataclass
class SensorHealthDetail:
    """Detailed prognostic health breakdown for an individual sensor."""
    sensor_type: str
    current_value: float
    baseline_mean: float
    unit: str
    z_score: float
    sensor_health_score: float   # 0.0 to 100.0
    status: str                  # "healthy" | "warning" | "critical"
    message: str


@dataclass
class MachineHealthReport:
    """Consolidated health report for a machine."""
    machine_id: str
    health_score: float          # 0.0 to 100.0
    status: str                  # "healthy" | "warning" | "critical"
    primary_driver: Optional[str] # Sensor with most severe degradation
    sensor_details: Dict[str, SensorHealthDetail]
    timestamp: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "machine_id": self.machine_id,
            "health_score": round(self.health_score, 1),
            "status": self.status,
            "primary_driver": self.primary_driver,
            "sensor_details": {
                st: {
                    "sensor_type": det.sensor_type,
                    "current_value": round(det.current_value, 3),
                    "baseline_mean": round(det.baseline_mean, 3),
                    "unit": det.unit,
                    "z_score": round(det.z_score, 2),
                    "sensor_health_score": round(det.sensor_health_score, 1),
                    "status": det.status,
                    "message": det.message,
                }
                for st, det in self.sensor_details.items()
            },
            "timestamp": self.timestamp,
        }


def _evaluate_sensor_score(
    sensor_type: str,
    value: float,
    baseline_spec: dict,
    machine_id: str,
) -> SensorHealthDetail:
    """
    Computes an individual sensor's health score (0-100) and z-score deviation.
    Accounts for operational duty cycles and directional physics.
    """
    mean = float(baseline_spec.get("mean", 0.0))
    std = float(baseline_spec.get("std", 1.0))
    if std <= 0.0:
        std = 1.0
    unit = str(baseline_spec.get("unit", ""))
    max_normal = float(baseline_spec.get("max", mean + 3 * std))
    crit_high = float(baseline_spec.get("critical_high", max_normal * 1.25))

    # Binary flags or event counters have no health degradation
    if sensor_type in ("cycle_count", "status_flag"):
        return SensorHealthDetail(
            sensor_type=sensor_type,
            current_value=value,
            baseline_mean=mean,
            unit=unit,
            z_score=0.0,
            sensor_health_score=100.0,
            status="healthy",
            message="Nominal cycle tracking",
        )

    # ── Specialized evaluation by sensor physics ──
    z_score = (value - mean) / std
    sensor_score = 100.0
    status = "healthy"
    message = "Normal operation"

    if sensor_type == "vibration":
        # Accelerometer vibration: high vibration is always detrimental
        # Baseline normal ~0.8-2.1.
        if value <= mean:
            z_score = max(0.0, (value - mean) / std)
            sensor_score = 100.0
        else:
            z_score = (value - mean) / std
            if z_score <= 2.0:
                # Normal operational noise
                sensor_score = 100.0 - (z_score * 2.5)  # 95 - 100
            elif z_score <= 4.0:
                # Developing roughness / bearing defect signature
                sensor_score = 95.0 - ((z_score - 2.0) * 15.0)  # 65 - 95
                status = "warning"
                message = f"Vibration elevated ({value:.2f} {unit}, +{z_score:.1f}σ)"
            else:
                # Severe vibration / imminent spallation
                excess = z_score - 4.0
                sensor_score = max(10.0, 65.0 - (excess * 12.0))
                status = "critical"
                message = f"Critical vibration excursion ({value:.2f} {unit}, +{z_score:.1f}σ)"

    elif sensor_type == "temperature":
        # Thermal signals have lag and high thermal mass
        # Only excessive heat above max_normal indicates cooling failure or bearing friction
        if value <= max_normal:
            sensor_score = 100.0
            z_score = max(0.0, (value - mean) / std)
        else:
            delta = value - max_normal
            over_span = max(1.0, crit_high - max_normal)
            ratio = min(1.5, delta / over_span)
            sensor_score = max(15.0, 95.0 - (ratio * 70.0))
            z_score = (value - mean) / std
            if sensor_score < 60.0:
                status = "critical"
                message = f"High thermal threshold exceeded ({value:.1f} {unit})"
            else:
                status = "warning"
                message = f"Temperature running hot ({value:.1f} {unit})"

    elif sensor_type == "current":
        # Motor current draw (M-03 conveyor)
        # Normal baseline is 14.5A, duty spikes up to ~20.5A. Overload is > 22A
        if value <= max_normal:
            sensor_score = 100.0
            z_score = max(0.0, (value - mean) / std)
        else:
            overload = value - max_normal
            z_score = (value - mean) / std
            if overload < 2.0:
                sensor_score = 85.0 - (overload * 12.0)
                status = "warning"
                message = f"Motor current elevated ({value:.1f} {unit})"
            else:
                sensor_score = max(10.0, 60.0 - (overload * 8.0))
                status = "critical"
                message = f"Motor near overload draw ({value:.1f} {unit})"

    elif sensor_type == "torque":
        # Robotic arm torque (M-01)
        # Duty cycle moves between 15 and 110 Nm. Mode 1 drifts baseline upward.
        if value <= max_normal:
            sensor_score = 100.0
            z_score = max(0.0, (value - mean) / std)
        else:
            excess = value - max_normal
            z_score = (value - mean) / std
            if excess < 10.0:
                sensor_score = 88.0 - (excess * 2.5)
                status = "warning"
                message = f"Axis torque exceeding envelope ({value:.1f} {unit})"
            else:
                sensor_score = max(12.0, 63.0 - (excess * 3.0))
                status = "critical"
                message = f"Excessive axis friction / torque surge ({value:.1f} {unit})"

    elif sensor_type == "calibration_dev":
        # Metrology offset (M-04): AS9100 calibration drift
        abs_dev = abs(value)
        recal_threshold = crit_high or 0.30
        ratio = abs_dev / recal_threshold
        z_score = abs_dev / std if std > 0 else 0.0
        if ratio <= 0.4:
            sensor_score = 100.0 - (ratio * 10.0)
        elif ratio <= 0.8:
            sensor_score = 90.0 - ((ratio - 0.4) * 50.0)
            status = "warning"
            message = f"Calibration drift approaching recalibration limit ({abs_dev:.3f} {unit})"
        else:
            sensor_score = max(5.0, 70.0 - ((ratio - 0.8) * 150.0))
            status = "critical"
            message = f"AS9100 calibration tolerance breached ({abs_dev:.3f} {unit})"

    elif sensor_type == "rpm":
        # Spindle RPM (M-02): During pauses, RPM drops to 0 (nominal pause)
        # Only unexpected speed loss during cutting is degraded
        crit_low = float(baseline_spec.get("critical_low", 7000.0))
        if value < 100.0:
            # Idle/tool-change pause — completely normal
            sensor_score = 100.0
            z_score = 0.0
        elif value >= crit_low:
            sensor_score = 100.0
            z_score = 0.0
        else:
            # Speed droop under load
            drop = crit_low - value
            sensor_score = max(20.0, 85.0 - (drop / 50.0))
            status = "warning" if sensor_score >= 60.0 else "critical"
            z_score = (mean - value) / std
            message = f"Spindle RPM droop under load ({value:.0f} {unit})"

    else:
        # General sensor fallback
        abs_z = abs(z_score)
        if abs_z <= 2.0:
            sensor_score = 100.0 - (abs_z * 3.0)
        elif abs_z <= 4.0:
            sensor_score = 94.0 - ((abs_z - 2.0) * 15.0)
            status = "warning"
            message = f"{sensor_type} deviation ({value:.2f} {unit})"
        else:
            sensor_score = max(10.0, 64.0 - ((abs_z - 4.0) * 12.0))
            status = "critical"
            message = f"Critical {sensor_type} anomaly ({value:.2f} {unit})"

    sensor_score = max(0.0, min(100.0, sensor_score))
    if sensor_score >= 85.0:
        status = "healthy"
    elif sensor_score >= 60.0:
        status = "warning"
    else:
        status = "critical"

    return SensorHealthDetail(
        sensor_type=sensor_type,
        current_value=value,
        baseline_mean=mean,
        unit=unit,
        z_score=z_score,
        sensor_health_score=sensor_score,
        status=status,
        message=message,
    )


def compute_health_score(
    machine_id: str,
    current_readings: Dict[str, float],
    baseline_ranges: Optional[Dict[str, dict]] = None,
    timestamp: Optional[str] = None,
) -> MachineHealthReport:
    """
    Compute full prognostic health assessment for a machine.

    Args:
        machine_id: Machine identifier (M-01 .. M-04)
        current_readings: Mapping of sensor_type to latest numerical value
        baseline_ranges: Optional customized baseline dict from DB.
                         Falls back to DEFAULT_BASELINES for that machine.
        timestamp: Optional reading timestamp ISO string.

    Returns:
        MachineHealthReport with 0-100 score, status, and breakdown.
    """
    baselines = baseline_ranges or DEFAULT_BASELINES.get(machine_id, {})
    if not baselines and machine_id in DEFAULT_BASELINES:
        baselines = DEFAULT_BASELINES[machine_id]

    details: Dict[str, SensorHealthDetail] = {}
    scores: List[float] = []

    for sensor_type, value in current_readings.items():
        spec = baselines.get(sensor_type)
        if not spec:
            # Fallback spec from machine config if available
            cfg = ALL_MACHINE_CONFIGS.get(machine_id)
            if cfg:
                matching = next((s for s in cfg.sensors if s.sensor_type == sensor_type), None)
                if matching:
                    spec = {
                        "mean": matching.baseline,
                        "std": matching.sigma if matching.sigma > 0 else 1.0,
                        "unit": matching.unit,
                    }
        if not spec:
            spec = {"mean": float(value), "std": 1.0, "unit": ""}

        detail = _evaluate_sensor_score(sensor_type, float(value), spec, machine_id)
        details[sensor_type] = detail
        if detail.sensor_type not in ("cycle_count", "status_flag"):
            scores.append(detail.sensor_health_score)

    if not scores:
        overall_score = 100.0
        primary_driver = None
        status = "healthy"
    else:
        # Weakest-link condition monitoring aggregation:
        # Machine health is dominated by the most degraded sensor,
        # with secondary degradation penalty for multiple faults.
        scores.sort()
        worst_score = scores[0]
        secondary_penalties = sum((100.0 - s) * 0.08 for s in scores[1:])
        overall_score = max(0.0, min(100.0, worst_score - secondary_penalties))

        # Find primary driver
        worst_sensor = min(
            (det for det in details.values() if det.sensor_type not in ("cycle_count", "status_flag")),
            key=lambda d: d.sensor_health_score,
            default=None,
        )
        primary_driver = worst_sensor.sensor_type if worst_sensor and worst_sensor.sensor_health_score < 90.0 else None

        if overall_score >= 85.0:
            status = "healthy"
        elif overall_score >= 60.0:
            status = "warning"
        else:
            status = "critical"

    return MachineHealthReport(
        machine_id=machine_id,
        health_score=overall_score,
        status=status,
        primary_driver=primary_driver,
        sensor_details=details,
        timestamp=timestamp,
    )
