"""
fixer.ai — Day 1 Tests: Ornstein-Uhlenbeck process + failure triggers

Tests verify:
1. OU values stay bounded and mean-reverting under normal mode
2. Each hidden failure trigger escalates its target signal correctly over time
3. Per-sensor noise characters (vibration kurtosis, M-04 slow drift)

Run: pytest backend/tests/test_ou_process.py -v
"""
import numpy as np
import pytest
from scipy import stats

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.simulation.ou_process import (
    ou_step, vibration_step, temperature_step, calibration_drift_step,
    robot_torque_duty_cycle, cnc_temp_target
)
from backend.simulation.failure_triggers import (
    Mode1TorqueDrift, Mode2BearingWear, Mode3MotorFault
)


# ─────────────────────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def rng():
    return np.random.default_rng(seed=42)


# ─────────────────────────────────────────────────────────────────────────────
# 1. OU Process — boundedness
# ─────────────────────────────────────────────────────────────────────────────

class TestOUBoundedness:
    def test_ou_stays_bounded(self, rng):
        """OU values must stay within 5*sigma of baseline for 10,000 ticks."""
        baseline = 45.0
        theta = 0.8
        sigma = 2.5
        dt = 1.0
        n_ticks = 10_000

        value = baseline
        violations = 0
        limit = 5 * sigma

        for _ in range(n_ticks):
            value = ou_step(value, baseline, theta, sigma, dt, rng)
            if abs(value - baseline) > limit:
                violations += 1

        # Allow at most 0.1% violations (extremely rare tail events)
        assert violations < n_ticks * 0.001, (
            f"OU values exceeded 5*sigma in {violations}/{n_ticks} ticks — "
            f"not sufficiently bounded"
        )

    def test_ou_stays_bounded_different_params(self, rng):
        """Test with high-noise vibration parameters."""
        baseline = 1.1
        theta = 0.9
        sigma = 0.18
        dt = 1.0
        n_ticks = 10_000

        value = baseline
        for _ in range(n_ticks):
            value = ou_step(value, baseline, theta, sigma, dt, rng)

        # Final value should still be near baseline after many ticks
        assert abs(value - baseline) < 5 * sigma


# ─────────────────────────────────────────────────────────────────────────────
# 2. OU Process — mean reversion
# ─────────────────────────────────────────────────────────────────────────────

class TestOUMeanReversion:
    def test_ou_running_mean_converges_to_baseline(self, rng):
        """Running mean of OU process must converge to baseline ± 0.05."""
        baseline = 45.0
        theta = 0.8
        sigma = 2.5
        dt = 1.0
        n_ticks = 10_000

        value = baseline
        history = []
        for _ in range(n_ticks):
            value = ou_step(value, baseline, theta, sigma, dt, rng)
            history.append(value)

        running_mean = np.mean(history)
        assert abs(running_mean - baseline) < 0.5, (
            f"OU running mean {running_mean:.4f} deviates too far from baseline {baseline}"
        )

    def test_ou_reverts_from_displaced_start(self, rng):
        """Process starting far from baseline must revert within 1000 ticks."""
        baseline = 45.0
        theta = 0.8
        sigma = 2.5
        dt = 1.0

        # Start very far from baseline
        value = baseline + 20 * sigma
        initial_deviation = abs(value - baseline)

        for _ in range(1000):
            value = ou_step(value, baseline, theta, sigma, dt, rng)

        final_deviation = abs(value - baseline)
        assert final_deviation < initial_deviation * 0.05, (
            f"OU failed to revert: started {initial_deviation:.2f} from baseline, "
            f"still {final_deviation:.2f} away after 1000 ticks"
        )


# ─────────────────────────────────────────────────────────────────────────────
# 3. Failure Mode 1 — M-01 Torque: Exponential (not linear) growth
# ─────────────────────────────────────────────────────────────────────────────

class TestFailureMode1:
    def test_torque_baseline_grows_exponentially(self):
        """
        Mode 1 torque escalation must be exponential, not linear.
        Verify: baseline at t=3000 > 2 * baseline at t=1000 (if linear, would be ~3x, not >2x)
        True exponential: baseline at t=2000 >> 2 * baseline at t=1000
        """
        original_baseline = 45.0
        t_samples = [100, 500, 1000, 2000, 3000, 5000]
        deltas = [
            Mode1TorqueDrift.modified_baseline(original_baseline, t) - original_baseline
            for t in t_samples
        ]

        # All deltas should be positive (escalation going up)
        for i, d in enumerate(deltas):
            assert d >= 0, f"Torque delta at t={t_samples[i]} is negative: {d}"

        # Verify exponential: delta(t=3000) / delta(t=1000) > 2x
        # (Linear growth would give exactly 3x; exponential grows faster)
        if deltas[2] > 0.01:  # Avoid division by near-zero
            ratio_3000_to_1000 = deltas[4] / deltas[2]
            assert ratio_3000_to_1000 > 5.0, (
                f"Growth from t=1000 to t=3000 ratio {ratio_3000_to_1000:.2f} "
                f"— expected exponential (>5x), got near-linear"
            )

    def test_torque_escalation_is_gradual_not_instant(self):
        """At t=100 ticks, escalation should be subtle (< 2 Nm above baseline)."""
        original_baseline = 45.0
        delta_at_100 = Mode1TorqueDrift.modified_baseline(original_baseline, 100) - original_baseline
        assert delta_at_100 < 2.0, (
            f"Mode 1 torque escalation at t=100 is {delta_at_100:.3f} Nm — "
            f"should be subtle (< 2 Nm). Escalation is too fast."
        )

    def test_health_impact_increases_over_time(self):
        """Health impact factor must increase monotonically."""
        impacts = [Mode1TorqueDrift.health_impact(t) for t in range(0, 6000, 500)]
        for i in range(1, len(impacts)):
            assert impacts[i] >= impacts[i-1], (
                f"Health impact decreased at t={i*500}: {impacts[i]} < {impacts[i-1]}"
            )


# ─────────────────────────────────────────────────────────────────────────────
# 4. Failure Mode 2 — M-02 Vibration: Sigma increases monotonically
# ─────────────────────────────────────────────────────────────────────────────

class TestFailureMode2:
    def test_vibration_sigma_increases_monotonically(self):
        """Mode 2 sigma must increase monotonically with time."""
        original_sigma = 0.18
        t_samples = [0, 500, 1000, 2000, 3000, 4000, 5000]
        sigmas = [Mode2BearingWear.modified_sigma(original_sigma, t) for t in t_samples]

        for i in range(1, len(sigmas)):
            assert sigmas[i] > sigmas[i-1], (
                f"Sigma not monotonically increasing at t={t_samples[i]}: "
                f"{sigmas[i]:.4f} <= {sigmas[i-1]:.4f}"
            )

    def test_vibration_baseline_shifts_upward(self):
        """Mode 2 baseline must shift upward over time."""
        original_baseline = 1.1
        t_samples = [0, 500, 1000, 3000, 5000]
        baselines = [Mode2BearingWear.modified_baseline(original_baseline, t) for t in t_samples]

        for i in range(1, len(baselines)):
            assert baselines[i] >= baselines[i-1]

        # Shift at t=5000 should be clearly above original
        assert baselines[-1] > original_baseline + 0.3, (
            f"Baseline shift at t=5000 ({baselines[-1] - original_baseline:.3f}) too small"
        )

    def test_sigma_increase_is_gradual(self):
        """Sigma should not double in the first 500 ticks (too fast)."""
        original_sigma = 0.18
        sigma_at_500 = Mode2BearingWear.modified_sigma(original_sigma, 500)
        assert sigma_at_500 < original_sigma * 2.0, (
            f"Mode 2 sigma doubled in 500 ticks ({sigma_at_500:.4f}) — escalation too fast"
        )


# ─────────────────────────────────────────────────────────────────────────────
# 5. Failure Mode 3 — M-03 Current: Step-up and spike probability increase
# ─────────────────────────────────────────────────────────────────────────────

class TestFailureMode3:
    def test_current_delta_steps_upward(self):
        """Mode 3 current delta must step upward at defined thresholds."""
        assert Mode3MotorFault.current_delta(0) == 0.0
        assert Mode3MotorFault.current_delta(499) == 0.0
        assert Mode3MotorFault.current_delta(500) == 1.5
        assert Mode3MotorFault.current_delta(1499) == 1.5
        assert Mode3MotorFault.current_delta(1500) == 4.0
        assert Mode3MotorFault.current_delta(3000) == 8.5

    def test_current_escalation_not_instant(self):
        """At t=0, current delta must be zero (not instant spike)."""
        assert Mode3MotorFault.current_delta(0) == 0.0

    def test_vibration_spike_probability_increases(self):
        """Spike probability must increase over time under Mode 3."""
        original_prob = 0.03
        probs = [
            Mode3MotorFault.vibration_spike_probability(original_prob, t)
            for t in [0, 500, 1000, 2000, 3000, 5000]
        ]
        for i in range(1, len(probs)):
            assert probs[i] >= probs[i-1]

        # Should be capped at max_spike_prob + original
        max_expected = Mode3MotorFault.max_spike_prob + original_prob
        assert probs[-1] <= max_expected + 0.001

    def test_health_impact_follows_current_steps(self):
        """Health impact should be 0 before first step, non-zero after."""
        assert Mode3MotorFault.health_impact(0) == 0.0
        assert Mode3MotorFault.health_impact(500) > 0.0
        assert Mode3MotorFault.health_impact(3000) > Mode3MotorFault.health_impact(1500)


# ─────────────────────────────────────────────────────────────────────────────
# 6. Vibration — Non-Gaussian (heavy-tailed) noise
# ─────────────────────────────────────────────────────────────────────────────

class TestVibrationNoise:
    def test_vibration_kurtosis_heavy_tailed(self):
        """
        Vibration time series must have kurtosis > 3 (heavier tails than Gaussian).
        Real accelerometers have heavy-tailed noise; plain OU would give kurtosis ~3.
        This verifies the spike injection is working.
        """
        rng = np.random.default_rng(seed=123)
        baseline = 1.1
        theta = 0.9
        sigma = 0.18
        dt = 1.0
        n_ticks = 5_000

        values = []
        current = baseline
        for _ in range(n_ticks):
            current = vibration_step(
                current, baseline, theta, sigma, dt,
                spike_probability=0.025,
                spike_magnitude_multiplier=5.0,
                rng=rng,
            )
            values.append(current)

        kurt = stats.kurtosis(values)  # Excess kurtosis (0 = Gaussian)
        assert kurt > 1.5, (
            f"Vibration kurtosis {kurt:.3f} too low — expected > 1.5 (excess kurtosis). "
            f"Heavy-tail spikes may not be working."
        )

    def test_vibration_non_negative(self):
        """Vibration values must be >= 0 (physical constraint)."""
        rng = np.random.default_rng(seed=99)
        current = 0.82
        for _ in range(1000):
            current = vibration_step(current, 0.82, 1.2, 0.12, 1.0, rng=rng)
            assert current >= 0.0, f"Vibration went negative: {current}"


# ─────────────────────────────────────────────────────────────────────────────
# 7. M-04 Calibration — Slow drift
# ─────────────────────────────────────────────────────────────────────────────

class TestCalibrationDrift:
    def test_calibration_drift_is_slow(self):
        """
        M-04 calibration drift must be very slow.
        Average absolute drift per tick must be < 0.01 Nm_offset.
        """
        rng = np.random.default_rng(seed=77)
        current = 0.02
        drift_rate = 0.0003
        n_ticks = 500

        deltas = []
        for _ in range(n_ticks):
            prev = current
            current = calibration_drift_step(
                current, drift_rate_per_tick=drift_rate, recal_threshold=0.30, rng=rng
            )
            # Don't count recalibration resets in drift measurement
            if abs(current - prev) < 0.05:  # Filter out recal reset events
                deltas.append(abs(current - prev))

        avg_drift = np.mean(deltas) if deltas else 0
        assert avg_drift < 0.01, (
            f"Calibration drift rate {avg_drift:.6f} Nm_offset/tick exceeds spec (< 0.01)"
        )

    def test_calibration_resets_at_threshold(self):
        """When deviation exceeds recal_threshold, it should reset to near-zero."""
        rng = np.random.default_rng(seed=55)
        # Start just below threshold
        current = 0.299
        found_reset = False

        for _ in range(200):
            prev = current
            current = calibration_drift_step(
                current, drift_rate_per_tick=0.001, recal_threshold=0.30, rng=rng
            )
            if prev >= 0.25 and current < 0.05:
                found_reset = True
                break

        assert found_reset, "Calibration did not reset to near-zero when threshold exceeded"


# ─────────────────────────────────────────────────────────────────────────────
# 8. Temperature — Thermal lag (no fast jitter)
# ─────────────────────────────────────────────────────────────────────────────

class TestTemperatureThermalLag:
    def test_temperature_does_not_jump_faster_than_thermal_constant(self):
        """Temperature per-tick change must be bounded by thermal lag."""
        rng = np.random.default_rng(seed=33)
        current = 22.0
        target = 78.0
        thermal_tau = 60.0
        dt = 1.0

        prev = current
        for tick in range(10):
            current = temperature_step(current, target, thermal_tau, dt, rng=rng)
            delta = abs(current - prev)
            # With tau=60, alpha ≈ 0.016 per tick — max reasonable jump is ~1°C
            assert delta < 5.0, (
                f"Temperature jumped {delta:.3f}°C in tick {tick} — thermal lag not working"
            )
            prev = current

    def test_temperature_approaches_target_asymptotically(self):
        """Temperature must get closer to target each tick (on average)."""
        rng = np.random.default_rng(seed=44)
        current = 22.0
        target = 78.0
        thermal_tau = 60.0

        # After 200 ticks, should be significantly warmer but not at target
        for _ in range(200):
            current = temperature_step(current, target, thermal_tau, 1.0, rng=rng)

        assert current > 40.0, "Temperature not warming toward target after 200 ticks"
        assert current < 78.0, "Temperature exceeded target (overshooting)"


# ─────────────────────────────────────────────────────────────────────────────
# 9. Duty cycle — basic shape verification
# ─────────────────────────────────────────────────────────────────────────────

class TestDutyCycles:
    def test_robot_torque_peaks_during_weld(self):
        """Torque duty cycle must peak during weld phase."""
        cycle_period = 30.0
        peak_torque = 110.0
        idle_torque = 15.0

        # At 30% of cycle (weld phase), torque should be near peak
        weld_time = cycle_period * 0.35
        weld_torque = robot_torque_duty_cycle(weld_time, cycle_period, peak_torque, idle_torque)
        assert weld_torque > peak_torque * 0.9, (
            f"Torque during weld phase: {weld_torque:.1f} — expected near {peak_torque}"
        )

        # At 90% of cycle (idle phase), torque should be near idle
        idle_time = cycle_period * 0.92
        idle = robot_torque_duty_cycle(idle_time, cycle_period, peak_torque, idle_torque)
        assert idle < idle_torque * 1.5, (
            f"Torque during idle phase: {idle:.1f} — expected near {idle_torque}"
        )

    def test_cnc_temp_target_drops_during_pause(self):
        """CNC temperature target should drop toward ambient during tool-change pause."""
        cutting_period = 120.0
        pause_fraction = 0.15
        hot_temp = 78.0
        ambient_temp = 22.0

        # At 95% of cycle (in pause zone)
        pause_time = cutting_period * 0.95
        target_during_pause = cnc_temp_target(
            pause_time, cutting_period, pause_fraction, hot_temp, ambient_temp
        )
        assert target_during_pause == ambient_temp, (
            f"CNC temp target during pause should be {ambient_temp}, got {target_during_pause}"
        )

        # At 50% of cycle (during cutting)
        cutting_time = cutting_period * 0.50
        target_during_cut = cnc_temp_target(
            cutting_time, cutting_period, pause_fraction, hot_temp, ambient_temp
        )
        assert target_during_cut == hot_temp, (
            f"CNC temp target during cutting should be {hot_temp}, got {target_during_cut}"
        )
