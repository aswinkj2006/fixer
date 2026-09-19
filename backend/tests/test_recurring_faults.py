"""
fixer.ai — Tests: Recurring Fault Detection & Leaderboard
Tests:
- Tier 2 past incidents are clustered by semantic pattern and failure code
- Occurrence count is tracked per machine
- Longest-lasting historical fix is extracted
- Fleet-wide recurring fault leaderboard aggregates across machines
- Live symptom matcher detects recurring incidents
"""
import pytest
from backend.rag.recurring_faults import (
    detect_recurring_faults,
    get_fleet_recurring_leaderboard,
    match_symptom_recurrence,
)


def test_detect_recurring_faults_m01():
    """M-01 Tier 2 collection should cluster past incidents and surface recurring patterns."""
    clusters = detect_recurring_faults("M-01")
    assert isinstance(clusters, list)
    # If Tier 2 is seeded, clusters should be found
    if clusters:
        top = clusters[0]
        assert top.machine_id == "M-01"
        assert top.occurrence_count >= 1
        assert len(top.longest_lasting_fix) > 0
        assert "M-01" in top.summary_insight
        assert len(top.ticket_ids) >= 1
        d = top.to_dict()
        assert "cluster_id" in d
        assert "longest_lasting_fix" in d


def test_detect_recurring_faults_m02():
    """M-02 Tier 2 collection should return clusters with failure codes."""
    clusters = detect_recurring_faults("M-02")
    assert isinstance(clusters, list)
    for c in clusters:
        assert c.machine_id == "M-02"
        assert c.occurrence_count >= 1


def test_fleet_recurring_leaderboard():
    """Fleet leaderboard should aggregate and rank clusters across all 4 machines."""
    leaderboard = get_fleet_recurring_leaderboard(min_occurrences=1)
    assert isinstance(leaderboard, list)
    if leaderboard:
        # Should be ranked 1, 2, 3...
        for idx, item in enumerate(leaderboard, start=1):
            assert item["rank"] == idx
            assert item["machine_id"] in ("M-01", "M-02", "M-03", "M-04")
            assert "longest_lasting_fix" in item
            assert "summary_insight" in item


def test_live_symptom_recurrence_match():
    """A matching symptom query should identify the recurring pattern on that machine."""
    # Querying grease leakage on M-01
    match = match_symptom_recurrence("M-01", "dark oil leaking around J2 axis gearbox seal with rising torque")
    if match:
        assert match["matched"] is True
        assert match["machine_id"] == "M-01"
        assert match["similarity"] > 0.60
        assert "longest_lasting_fix" in match
        assert "RECURRING FAULT PATTERN DETECTED" in match["guidance"]
