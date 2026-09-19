"""
fixer.ai — Remaining Useful Life (RUL) Heuristic & Service Window Estimation
Spec: 01_ARCHITECTURE.md §4, 05_BUILD_PLAN_6_DAYS.md Day 4

Implements trend-based prognostic extrapolation:
- Fits a linear/exponential rate of degradation dy/dt across time series sensor readings.
- Extrapolates to OEM / AS9100 critical failure thresholds.
- Clearly flags all outputs as trend-based heuristic (not an over-claimed ML model).
- Generates actionable maintenance service windows ("Within 24h", "2-3 days", "> 30 days nominal").
"""
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple, Any
import math
import numpy as np

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.database.models import SensorReading
from backend.health.scoring import DEFAULT_BASELINES


# ─────────────────────────────────────────────────────────────────────────────
# Critical Thresholds per Machine & Sensor (OEM / Industry Limits)
# ─────────────────────────────────────────────────────────────────────────────
CRITICAL_THRESHOLDS: Dict[str, Dict[str, Dict[str, Any]]] = {
    "M-01": {
        "torque": {"threshold": 120.0, "unit": "Nm", "direction": "high", "nominal": 45.0},
        "vibration": {"threshold": 2.8, "unit": "mm/s2", "direction": "high", "nominal": 0.82},
    },
    "M-02": {
        "vibration": {"threshold": 3.8, "unit": "mm/s2", "direction": "high", "nominal": 1.1},
        "temperature": {"threshold": 85.0, "unit": "degC", "direction": "high", "nominal": 42.0},
    },
    "M-03": {
        "current": {"threshold": 23.5, "unit": "A", "direction": "high", "nominal": 14.5},
        "vibration": {"threshold": 6.0, "unit": "mm/s2", "direction": "high", "nominal": 2.1},
        "temperature": {"threshold": 85.0, "unit": "degC", "direction": "high", "nominal": 55.0},
    },
    "M-04": {
        "calibration_dev": {"threshold": 0.30, "unit": "Nm_offset", "direction": "high", "nominal": 0.02},
    },
}


@dataclass
class RULReport:
    """Prognostic Remaining Useful Life estimation result."""
    machine_id: str
    rul_hours: Optional[float]              # Estimated hours until failure threshold
    rul_days: Optional[float]               # Estimated days until failure threshold
    service_window: str                     # Human-readable window: e.g. "Within 24 hours"
    critical_sensor: Optional[str]          # Degrading sensor driving the estimate
    current_value: Optional[float]
    threshold_value: Optional[float]
    unit: str
    trend_rate_per_hour: float              # Rate of change per hour
    r_squared: float                        # Goodness of fit (0.0 - 1.0)
    is_degrading: bool                      # True if positive degradation trend detected
    predicted_failure_iso: Optional[str]    # Estimated timestamp of threshold breach
    heuristic_disclosure: str = "Linear trend extrapolation against OEM limit (heuristic — not trained ML)"
    is_heuristic: bool = True

    def to_dict(self) -> dict:
        return {
            "machine_id": self.machine_id,
            "rul_hours": round(self.rul_hours, 1) if self.rul_hours is not None else None,
            "rul_days": round(self.rul_days, 1) if self.rul_days is not None else None,
            "service_window": self.service_window,
            "critical_sensor": self.critical_sensor,
            "current_value": round(self.current_value, 3) if self.current_value is not None else None,
            "threshold_value": round(self.threshold_value, 3) if self.threshold_value is not None else None,
            "unit": self.unit,
            "trend_rate_per_hour": round(self.trend_rate_per_hour, 4),
            "r_squared": round(self.r_squared, 3),
            "is_degrading": self.is_degrading,
            "predicted_failure_iso": self.predicted_failure_iso,
            "heuristic_disclosure": self.heuristic_disclosure,
            "is_heuristic": self.is_heuristic,
        }


def _fit_linear_trend(timestamps: List[float], values: List[float]) -> Tuple[float, float, float]:
    """
    Fits y = slope * t + intercept using Ordinary Least Squares.
    Returns: (slope, intercept, r_squared)
    """
    n = len(values)
    if n < 3:
        return 0.0, float(values[-1]) if values else 0.0, 0.0

    t_arr = np.array(timestamps, dtype=float)
    y_arr = np.array(values, dtype=float)

    # Filter out non-finite numbers
    valid_mask = np.isfinite(t_arr) & np.isfinite(y_arr)
    if np.sum(valid_mask) < 3:
        return 0.0, float(values[-1]) if values else 0.0, 0.0

    t_arr = t_arr[valid_mask]
    y_arr = y_arr[valid_mask]

    # Normalize t so origin is 0 to avoid numerical precision loss
    t0 = t_arr[0]
    t_rel = t_arr - t0

    with np.errstate(all="ignore"):
        # Fit line
        try:
            slope, intercept = np.polyfit(t_rel, y_arr, 1)
        except Exception:
            return 0.0, float(np.mean(y_arr)), 0.0

        # Calculate R^2
        y_pred = slope * t_rel + intercept
        ss_tot = np.sum((y_arr - np.mean(y_arr)) ** 2)
        ss_res = np.sum((y_arr - y_pred) ** 2)
        r2 = 1.0 - (ss_res / ss_tot) if (np.isfinite(ss_tot) and ss_tot > 1e-9) else 0.0
        if not np.isfinite(r2):
            r2 = 0.0
        r2 = max(0.0, min(1.0, float(r2)))

    return float(slope), float(intercept), r2


def _classify_service_window(rul_hours: Optional[float], is_degrading: bool) -> str:
    """Classifies estimated RUL hours into an operational service window."""
    if not is_degrading or rul_hours is None or rul_hours > 720.0:
        return "> 30 days (nominal)"
    if rul_hours <= 12.0:
        return "Immediate (< 12 hours)"
    if rul_hours <= 24.0:
        return "Within 24 hours"
    if rul_hours <= 72.0:
        return "2–3 days"
    if rul_hours <= 168.0:
        return "Within 7 days"
    return "2–4 weeks"


def estimate_rul_from_readings(
    machine_id: str,
    readings_history: List[Dict[str, Any]],
    current_snapshot: Optional[Dict[str, float]] = None,
) -> RULReport:
    """
    Estimate RUL given a series of historical readings [{timestamp, sensor_type, value}].
    If sensor readings demonstrate an upward degradation slope towards critical OEM thresholds,
    extrapolates hours remaining to breach.
    """
    machine_thresholds = CRITICAL_THRESHOLDS.get(machine_id, {})
    if not machine_thresholds:
        return RULReport(
            machine_id=machine_id,
            rul_hours=None,
            rul_days=None,
            service_window="> 30 days (nominal)",
            critical_sensor=None,
            current_value=None,
            threshold_value=None,
            unit="",
            trend_rate_per_hour=0.0,
            r_squared=0.0,
            is_degrading=False,
            predicted_failure_iso=None,
        )

    # Group readings by sensor type
    sensor_series: Dict[str, List[Tuple[float, float]]] = {}
    for r in readings_history:
        stype = r.get("sensor_type")
        val = r.get("value")
        ts = r.get("timestamp")
        if stype in machine_thresholds and val is not None and ts is not None:
            # Parse timestamp to epoch seconds
            try:
                if isinstance(ts, str):
                    dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                    epoch = dt.timestamp()
                elif isinstance(ts, (int, float)):
                    epoch = float(ts)
                else:
                    continue
                if stype not in sensor_series:
                    sensor_series[stype] = []
                sensor_series[stype].append((epoch, float(val)))
            except Exception:
                continue

    # Evaluate degradation for each monitored sensor
    worst_rul_hours = float("inf")
    critical_candidate = None
    best_candidate_meta: Dict[str, Any] = {}

    for stype, points in sensor_series.items():
        if len(points) < 4:
            continue
        # Sort by timestamp
        points.sort(key=lambda p: p[0])
        epochs = [p[0] for p in points]
        vals = [p[1] for p in points]

        thresh_info = machine_thresholds[stype]
        crit_val = float(thresh_info["threshold"])
        unit = thresh_info["unit"]
        curr_val = current_snapshot.get(stype, vals[-1]) if current_snapshot else vals[-1]

        slope_sec, intercept, r2 = _fit_linear_trend(epochs, vals)
        slope_hr = slope_sec * 3600.0  # rate of change per hour

        # Check if sensor is trending towards critical limit
        if slope_hr > 0.0001:
            remaining_delta = crit_val - curr_val
            if remaining_delta > 0:
                hours_left = remaining_delta / slope_hr
                if hours_left < worst_rul_hours:
                    worst_rul_hours = hours_left
                    critical_candidate = stype
                    best_candidate_meta = {
                        "current_value": curr_val,
                        "threshold_value": crit_val,
                        "unit": unit,
                        "trend_rate_per_hour": slope_hr,
                        "r_squared": r2,
                    }

    # If an active degrading sensor was found
    if critical_candidate and worst_rul_hours < float("inf"):
        now_dt = datetime.now(timezone.utc)
        pred_dt = now_dt + timedelta(hours=worst_rul_hours)
        is_deg = worst_rul_hours < 720.0
        service_window = _classify_service_window(worst_rul_hours, is_deg)

        return RULReport(
            machine_id=machine_id,
            rul_hours=worst_rul_hours,
            rul_days=worst_rul_hours / 24.0,
            service_window=service_window,
            critical_sensor=critical_candidate,
            current_value=best_candidate_meta.get("current_value"),
            threshold_value=best_candidate_meta.get("threshold_value"),
            unit=best_candidate_meta.get("unit", ""),
            trend_rate_per_hour=best_candidate_meta.get("trend_rate_per_hour", 0.0),
            r_squared=best_candidate_meta.get("r_squared", 0.0),
            is_degrading=is_deg,
            predicted_failure_iso=pred_dt.isoformat(),
        )

    # If no degradation slope detected or machine is healthy:
    # Use current snapshot to check proximity to limits
    primary_sensor = list(machine_thresholds.keys())[0]
    thresh_info = machine_thresholds[primary_sensor]
    curr_val = current_snapshot.get(primary_sensor, thresh_info.get("nominal", 0.0)) if current_snapshot else thresh_info.get("nominal", 0.0)

    return RULReport(
        machine_id=machine_id,
        rul_hours=None,
        rul_days=None,
        service_window="> 30 days (nominal)",
        critical_sensor=primary_sensor,
        current_value=float(curr_val),
        threshold_value=float(thresh_info["threshold"]),
        unit=thresh_info["unit"],
        trend_rate_per_hour=0.0,
        r_squared=0.0,
        is_degrading=False,
        predicted_failure_iso=None,
    )


async def estimate_rul_from_db(
    machine_id: str,
    db: AsyncSession,
    lookback_seconds: int = 1800,
    current_snapshot: Optional[Dict[str, float]] = None,
) -> RULReport:
    """
    Fetch recent sensor readings from database and compute RUL report.
    """
    # Fetch last 300 readings for this machine
    stmt = (
        select(SensorReading)
        .where(SensorReading.machine_id == machine_id)
        .order_by(SensorReading.timestamp.desc())
        .limit(300)
    )
    res = await db.execute(stmt)
    records = res.scalars().all()

    readings_history = [
        {
            "sensor_type": r.sensor_type,
            "value": r.value,
            "timestamp": r.timestamp,
        }
        for r in reversed(records)
    ]

    return estimate_rul_from_readings(
        machine_id=machine_id,
        readings_history=readings_history,
        current_snapshot=current_snapshot,
    )
