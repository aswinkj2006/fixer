"""
fixer.ai — Tests: Prognostic Health Scoring & Condition Monitoring
Tests:
- Healthy fleet baselines produce >= 85.0 health scores
- Simulated failure modes (torque, vibration, current, calibration) degrade health appropriately
- Directional physics & operational envelope handling (no false alarms on normal duty cycles)
- Weakest-link aggregation property (ISO 10816 principle)
- Sensor breakdown reports and primary driver attribution
"""
import pytest
from backend.health.scoring import compute_health_score, DEFAULT_BASELINES


def test_healthy_m01_baseline():
    """M-01 operating with nominal torque and vibration should score >= 90 (healthy)."""
    readings = {
        "torque": 45.0,
        "vibration": 0.82,
        "cycle_count": 1.0,
    }
    report = compute_health_score("M-01", readings)
    assert report.health_score >= 90.0
    assert report.status == "healthy"
    assert report.primary_driver is None
    assert "torque" in report.sensor_details
    assert "vibration" in report.sensor_details


def test_m01_torque_failure_mode():
    """M-01 grease leak causing elevated torque (> 120 Nm) should trigger warning/critical."""
    # Escalated torque well beyond normal weld envelope
    readings = {
        "torque": 135.0,
        "vibration": 0.85,
        "cycle_count": 1.0,
    }
    report = compute_health_score("M-01", readings)
    assert report.health_score < 65.0
    assert report.status in ("warning", "critical")
    assert report.primary_driver == "torque"
    assert report.sensor_details["torque"].status == "critical"
    assert "Excessive" in report.sensor_details["torque"].message


def test_m02_bearing_wear_vibration_spike():
    """M-02 spindle bearing wear causing high vibration should drop health score."""
    readings = {
        "vibration": 4.2,  # Normal is 1.1 mm/s2
        "temperature": 45.0,
        "rpm": 8000.0,
    }
    report = compute_health_score("M-02", readings)
    assert report.health_score < 60.0
    assert report.status == "critical"
    assert report.primary_driver == "vibration"
    assert report.sensor_details["vibration"].status == "critical"


def test_m02_duty_cycle_rpm_pause():
    """M-02 RPM dropping to 0 during tool-change pause is normal and should NOT penalize health."""
    readings = {
        "vibration": 1.1,
        "temperature": 45.0,
        "rpm": 0.0,  # Idle tool change pause
    }
    report = compute_health_score("M-02", readings)
    assert report.health_score >= 90.0
    assert report.status == "healthy"
    assert report.sensor_details["rpm"].sensor_health_score == 100.0


def test_m03_motor_current_overload():
    """M-03 motor current surge (> 24A) should flag motor overload fault."""
    readings = {
        "current": 25.5,  # Normal is 14.5A, max normal is 21.5A
        "vibration": 2.2,
        "temperature": 56.0,
    }
    report = compute_health_score("M-03", readings)
    assert report.health_score < 60.0
    assert report.status == "critical"
    assert report.primary_driver == "current"
    assert "overload" in report.sensor_details["current"].message.lower()


def test_m04_calibration_drift():
    """M-04 calibration deviation exceeding AS9100 threshold should drop health score."""
    # Recal threshold is 0.30 Nm_offset
    readings_minor = {"calibration_dev": 0.03}
    report_minor = compute_health_score("M-04", readings_minor)
    assert report_minor.health_score >= 95.0

    readings_breach = {"calibration_dev": 0.32}
    report_breach = compute_health_score("M-04", readings_breach)
    assert report_breach.health_score < 50.0
    assert report_breach.status == "critical"
    assert "AS9100" in report_breach.sensor_details["calibration_dev"].message


def test_weakest_link_aggregation():
    """A single critical sensor must pull the machine into degraded state even if others are perfect."""
    readings = {
        "vibration": 5.5,    # Disastrous vibration
        "temperature": 55.0,  # Perfectly nominal
        "current": 14.5,      # Perfectly nominal
    }
    report = compute_health_score("M-03", readings)
    assert report.health_score < 55.0
    assert report.status == "critical"
    assert report.primary_driver == "vibration"


def test_report_serialization():
    """Report should serialize cleanly to dictionary for JSON API responses."""
    readings = {"torque": 45.0, "vibration": 0.82}
    report = compute_health_score("M-01", readings)
    d = report.to_dict()
    assert isinstance(d["health_score"], float)
    assert d["status"] == "healthy"
    assert "sensor_details" in d
    assert "torque" in d["sensor_details"]
