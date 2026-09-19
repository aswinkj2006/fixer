"""
fixer.ai — Tests: Remaining Useful Life (RUL) Heuristic
Tests:
- Stable machines produce nominal RUL (> 30 days) and is_degrading=False
- Upward trend extrapolates time to threshold accurately (linear OLS fitting)
- Service window classifications (Immediate, 24h, 2-3d, nominal)
- Heuristic transparency label disclosure
- Report dictionary serialization
"""
import pytest
from datetime import datetime, timezone, timedelta
from backend.health.rul import (
    estimate_rul_from_readings,
    _fit_linear_trend,
    _classify_service_window,
    CRITICAL_THRESHOLDS,
)


def test_fit_linear_trend_accuracy():
    """Verify OLS linear regression accurately calculates slope and R^2."""
    t0 = 1000.0
    # y = 2.0 * t + 5.0
    timestamps = [t0 + i for i in range(10)]
    values = [2.0 * i + 5.0 for i in range(10)]

    slope, intercept, r2 = _fit_linear_trend(timestamps, values)
    assert abs(slope - 2.0) < 1e-4
    assert abs(r2 - 1.0) < 1e-4


def test_stable_machine_nominal_rul():
    """A healthy machine with flat readings should yield nominal RUL (> 30 days)."""
    now = datetime.now(timezone.utc)
    readings = []
    # 20 readings with constant nominal vibration
    for i in range(20):
        ts = (now - timedelta(minutes=20 - i)).isoformat()
        readings.append({
            "sensor_type": "vibration",
            "value": 1.10 + (0.01 if i % 2 == 0 else -0.01),
            "timestamp": ts,
        })

    report = estimate_rul_from_readings("M-02", readings, current_snapshot={"vibration": 1.10})
    assert report.is_degrading is False
    assert report.rul_hours is None
    assert report.service_window == "> 30 days (nominal)"
    assert report.is_heuristic is True
    assert "heuristic" in report.heuristic_disclosure.lower()


def test_degrading_vibration_extrapolation():
    """
    Simulate bearing wear on M-02:
    Vibration climbing from 2.0 to 2.9 mm/s2 over 9 hours (rate: 0.1 mm/s2 per hour).
    Critical threshold is 3.8 mm/s2.
    Current = 2.9. Remaining delta = 0.9.
    Expected RUL = 0.9 / 0.1 = ~9.0 hours.
    Service window should be 'Immediate (< 12 hours)'.
    """
    base_time = datetime(2026, 3, 1, 10, 0, 0, tzinfo=timezone.utc)
    readings = []
    for h in range(10):
        ts = (base_time + timedelta(hours=h)).isoformat()
        val = 2.0 + (0.1 * h)  # 2.0, 2.1, ..., 2.9
        readings.append({
            "sensor_type": "vibration",
            "value": val,
            "timestamp": ts,
        })

    report = estimate_rul_from_readings("M-02", readings, current_snapshot={"vibration": 2.9})
    assert report.is_degrading is True
    assert report.critical_sensor == "vibration"
    assert report.rul_hours is not None
    assert abs(report.rul_hours - 9.0) < 1.0
    assert report.service_window == "Immediate (< 12 hours)"
    assert report.r_squared > 0.95
    assert report.predicted_failure_iso is not None


def test_service_window_classification():
    """Verify classification thresholds into operational maintenance windows."""
    assert _classify_service_window(6.0, True) == "Immediate (< 12 hours)"
    assert _classify_service_window(18.0, True) == "Within 24 hours"
    assert _classify_service_window(48.0, True) == "2–3 days"
    assert _classify_service_window(120.0, True) == "Within 7 days"
    assert _classify_service_window(400.0, True) == "2–4 weeks"
    assert _classify_service_window(800.0, True) == "> 30 days (nominal)"
    assert _classify_service_window(None, False) == "> 30 days (nominal)"


def test_rul_report_serialization():
    """Ensure RULReport cleanly serializes to dictionary for JSON APIs."""
    report = estimate_rul_from_readings("M-01", [], current_snapshot={"torque": 45.0})
    d = report.to_dict()
    assert d["machine_id"] == "M-01"
    assert d["service_window"] == "> 30 days (nominal)"
    assert d["is_heuristic"] is True
    assert "heuristic_disclosure" in d
