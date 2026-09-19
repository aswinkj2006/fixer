"""
fixer.ai — Tests: ISO 14224 Fleet Reliability & Downtime Analytics
Tests:
- Parsing ISO timestamps for downtime calculation
- Machine MTBF, MTTR, Availability % calculation
- Downtime cost avoided calculation ($18,500/hr benchmark)
- Fleet-wide aggregation across all assets
- FastAPI endpoints for fleet and machine reliability
"""
import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock

from backend.health.reliability import (
    _parse_iso,
    compute_machine_reliability,
    compute_fleet_reliability,
    AVERAGE_DOWNTIME_COST_PER_HOUR,
    AVERAGE_LOOKUP_TIME_SAVED_HOURS,
)


def test_parse_iso_timestamps():
    """Verify ISO string parser handles UTC, offsets, and invalid dates gracefully."""
    dt1 = _parse_iso("2026-09-18T10:00:00Z")
    assert dt1 is not None
    assert dt1.hour == 10

    dt2 = _parse_iso("2026-09-18T12:30:00+00:00")
    assert dt2 is not None
    assert dt2.minute == 30

    assert _parse_iso(None) is None
    assert _parse_iso("invalid-timestamp") is None


@pytest.mark.asyncio
async def test_compute_machine_reliability_nominal():
    """A machine with no downtime tickets should exhibit 100% availability and nominal MTBF."""
    mock_db = AsyncMock()
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = []
    mock_res = MagicMock()
    mock_res.scalars.return_value = mock_scalars
    mock_db.execute.return_value = mock_res

    res = await compute_machine_reliability("M-01", db=mock_db, window_days=30)
    assert res["machine_id"] == "M-01"
    assert res["failure_count"] == 0
    assert res["resolved_count"] == 0
    assert res["total_downtime_hours"] == 0.0
    assert res["availability_pct"] == 100.0
    assert res["cost_avoided_usd"] == 0.0
    assert res["mtbf_hours"] == 30 * 24.0


@pytest.mark.asyncio
async def test_compute_machine_reliability_with_failures():
    """Test MTBF, MTTR, availability %, and downtime cost avoidance with resolved tickets."""
    now = datetime.now(timezone.utc)
    t1_open = (now - timedelta(days=5, hours=4)).isoformat()
    t1_close = (now - timedelta(days=5)).isoformat()  # 4 hours downtime, resolved

    t2_open = (now - timedelta(days=2, hours=2)).isoformat()
    t2_close = (now - timedelta(days=2)).isoformat()  # 2 hours downtime, resolved

    # Mock Ticket objects
    t1 = MagicMock()
    t1.ticket_id = "TICK-M01-001"
    t1.machine_id = "M-01"
    t1.opened_at = t1_open
    t1.closed_at = t1_close
    t1.status = "resolved"
    t1.severity = "high"
    t1.failure_code = "HYD-LEAK-01"
    t1.symptom_text = "Hydraulic pressure loss at primary joint"

    t2 = MagicMock()
    t2.ticket_id = "TICK-M01-002"
    t2.machine_id = "M-01"
    t2.opened_at = t2_open
    t2.closed_at = t2_close
    t2.status = "resolved"
    t2.severity = "medium"
    t2.failure_code = "TEMP-WARN-02"
    t2.symptom_text = "Servo overheat warning"

    mock_db = AsyncMock()
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = [t1, t2]
    mock_res = MagicMock()
    mock_res.scalars.return_value = mock_scalars
    mock_db.execute.return_value = mock_res

    res = await compute_machine_reliability("M-01", db=mock_db, window_days=10)
    # Total window = 240 hrs. Downtime = 4 + 2 = 6 hrs.
    # Operating hours = 234 hrs.
    # MTTR = 6 / 2 = 3.0 hrs
    # MTBF = 234 / 2 = 117.0 hrs
    # Availability = (234 / 240) * 100 = 97.5%
    # Cost avoided = 2 tickets * 0.75 hrs * $18,500 = $27,750
    assert res["failure_count"] == 2
    assert res["resolved_count"] == 2
    assert res["total_downtime_hours"] == 6.0
    assert res["mttr_hours"] == 3.0
    assert res["mtbf_hours"] == 117.0
    assert res["availability_pct"] == 97.5
    assert res["cost_avoided_usd"] == 27750.0
    assert len(res["recent_downtime_events"]) == 2


@pytest.mark.asyncio
async def test_compute_fleet_reliability_aggregation():
    """Verify fleet reliability correctly sums and averages across multiple machines."""
    mock_db = AsyncMock()
    # First query gets machine IDs
    mock_m_scalars = MagicMock()
    mock_m_scalars.all.return_value = ["M-01", "M-02"]
    mock_m_res = MagicMock()
    mock_m_res.scalars.return_value = mock_m_scalars

    # Second queries get tickets for each machine
    mock_t_scalars = MagicMock()
    mock_t_scalars.all.return_value = []
    mock_t_res = MagicMock()
    mock_t_res.scalars.return_value = mock_t_scalars

    mock_db.execute.side_effect = [mock_m_res, mock_t_res, mock_t_res]

    fleet = await compute_fleet_reliability(db=mock_db, window_days=30)
    assert fleet["total_machines"] == 2
    assert fleet["window_days"] == 30
    assert fleet["fleet_availability_pct"] == 100.0
    assert fleet["fleet_failures_count"] == 0
    assert "M-01" in fleet["machine_breakdown"]
    assert "M-02" in fleet["machine_breakdown"]


@pytest.mark.asyncio
async def test_reliability_endpoints_live_db():
    """Test GET /fleet/reliability and GET /machines/M-01/reliability against local database."""
    from httpx import AsyncClient, ASGITransport
    from backend.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Fleet endpoint
        res_fleet = await ac.get("/api/fleet/reliability")
        assert res_fleet.status_code == 200
        data_fleet = res_fleet.json()
        assert "fleet_availability_pct" in data_fleet
        assert "fleet_mtbf_hours" in data_fleet
        assert "fleet_mttr_hours" in data_fleet
        assert "total_cost_avoided_usd" in data_fleet
        assert "machine_breakdown" in data_fleet

        # Machine endpoint
        res_m = await ac.get("/api/machines/M-01/reliability")
        assert res_m.status_code == 200
        data_m = res_m.json()
        assert data_m["machine_id"] == "M-01"
        assert "availability_pct" in data_m
        assert "mtbf_hours" in data_m
        assert "recent_downtime_events" in data_m
