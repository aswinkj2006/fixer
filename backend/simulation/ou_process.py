"""
fixer.ai — Ornstein-Uhlenbeck process + duty cycles + per-sensor noise

Implements the sensor simulation math specified in:
  02_MOCK_MACHINERY_AND_SENSOR_SIMULATION.md

Key design decisions:
- OU process for mean-reverting baseline fluctuation (NOT plain Gaussian noise)
- Duty-cycle layer on top (trapezoid for robot torque, exponential for CNC temp, etc.)
- Non-Gaussian heavy-tail spikes for vibration (real accelerometers have heavy-tailed noise)
- Temperature uses exponential moving average (thermal lag — cannot jitter fast)
- Calibration deviation uses slow monotonic drift only

All functions are stateless (take current_value as input) for easy testing and replay.
"""
import numpy as np
from typing import Optional


# ─────────────────────────────────────────────────────────────────────────────
# Core OU update — one tick
# ─────────────────────────────────────────────────────────────────────────────

def ou_step(
    current_value: float,
    baseline: float,
    theta: float,
    sigma: float,
    dt: float = 1.0,
    rng: Optional[np.random.Generator] = None,
) -> float:
    """
    Exact analytical step of the Ornstein-Uhlenbeck process:
        X_{t+dt} = baseline + (X_t - baseline) * exp(-theta * dt) + sigma_eff * W
    Unconditionally stable for any dt, eliminating numerical Euler divergence.
    """
    if rng is None:
        rng = np.random.default_rng()

    # Guard against invalid incoming current_value
    if not np.isfinite(current_value) or abs(current_value) > 1e8:
        current_value = baseline

    if theta > 1e-6:
        decay = float(np.exp(-min(theta * dt, 50.0)))
        denom = 2.0 * theta
        var = (1.0 - np.exp(-min(2.0 * theta * dt, 50.0))) / denom
        sigma_eff = float(sigma * np.sqrt(max(var, 0.0)))
    else:
        decay = 1.0
        sigma_eff = float(sigma * np.sqrt(dt))

    noise = float(rng.standard_normal())
    result = baseline + (current_value - baseline) * decay + sigma_eff * noise
    if not np.isfinite(result):
        result = baseline
    return float(result)


# ─────────────────────────────────────────────────────────────────────────────
# Non-Gaussian vibration spike (heavy-tailed noise)
# Real accelerometers: occasional short spikes >> 3*sigma (kurtosis > 3)
# ─────────────────────────────────────────────────────────────────────────────

def vibration_step(
    current_value: float,
    baseline: float,
    theta: float,
    sigma: float,
    dt: float,
    spike_probability: float = 0.02,
    spike_magnitude_multiplier: float = 5.0,
    rng: Optional[np.random.Generator] = None,
) -> float:
    """
    OU baseline + occasional non-Gaussian spikes.
    spike_probability: probability per tick of a heavy-tail spike (default 2%)
    spike_magnitude_multiplier: how many sigma the spike rises above baseline
    """
    if rng is None:
        rng = np.random.default_rng()
    # OU base
    value = ou_step(current_value, baseline, theta, sigma, dt, rng)
    # Heavy-tail spike
    if rng.random() < spike_probability:
        spike = rng.exponential(sigma * spike_magnitude_multiplier)
        value += spike
    return max(0.0, value)  # vibration cannot be negative


# ─────────────────────────────────────────────────────────────────────────────
# Temperature step — thermal lag via exponential moving average
# Real thermal sensors cannot jitter fast tick-to-tick
# ─────────────────────────────────────────────────────────────────────────────

def temperature_step(
    current_value: float,
    target_temperature: float,
    thermal_tau: float,
    dt: float,
    small_noise_sigma: float = 0.05,
    rng: Optional[np.random.Generator] = None,
) -> float:
    """
    Exponential approach to target_temperature (simulates thermal mass).
    thermal_tau: time constant (higher = slower approach — more thermal lag)
    """
    if rng is None:
        rng = np.random.default_rng()
    # Exponential decay toward target
    alpha = 1.0 - np.exp(-dt / thermal_tau)
    new_value = current_value + alpha * (target_temperature - current_value)
    # Very small Gaussian noise (sensors have small electronic noise)
    new_value += rng.normal(0, small_noise_sigma)
    return new_value


# ─────────────────────────────────────────────────────────────────────────────
# Duty-cycle helpers
# ─────────────────────────────────────────────────────────────────────────────

def robot_torque_duty_cycle(
    sim_time: float,
    cycle_period: float = 30.0,
    peak_torque: float = 110.0,
    idle_torque: float = 15.0,
    ramp_fraction: float = 0.15,
) -> float:
    """
    M-01 torque: trapezoid wave (ramp up → hold peak → ramp down → idle).
    sim_time: current simulation time in seconds
    cycle_period: seconds per weld cycle
    Returns the deterministic torque setpoint for this moment in the duty cycle.
    """
    phase = (sim_time % cycle_period) / cycle_period
    # ramp_fraction of cycle is ramp-up, 0.5 is peak, ramp_fraction is ramp-down, rest is idle
    ramp = ramp_fraction
    if phase < ramp:
        # Ramp up
        return idle_torque + (peak_torque - idle_torque) * (phase / ramp)
    elif phase < (0.5 + ramp):
        # Peak (weld arc active)
        return peak_torque
    elif phase < (0.5 + 2 * ramp):
        # Ramp down
        return peak_torque - (peak_torque - idle_torque) * ((phase - 0.5 - ramp) / ramp)
    else:
        # Idle
        return idle_torque


def cnc_temp_target(
    sim_time: float,
    cutting_period: float = 120.0,
    pause_fraction: float = 0.15,
    hot_temp: float = 78.0,
    ambient_temp: float = 22.0,
) -> float:
    """
    M-02 spindle temperature target: climbs during cutting, cools during tool-change pause.
    Returns the current target temperature for the exponential approach function.
    """
    phase = (sim_time % cutting_period) / cutting_period
    if phase > (1.0 - pause_fraction):
        # Tool-change pause — cool toward ambient
        return ambient_temp
    else:
        # Cutting — target hot setpoint
        return hot_temp


def conveyor_current_load_spike(
    sim_time: float,
    base_current: float,
    spike_period: float = 8.0,
    spike_width: float = 0.5,
    spike_magnitude: float = 6.0,
    rng: Optional[np.random.Generator] = None,
) -> float:
    """
    M-03 current: flat baseline with periodic load spikes when parts pass a sensor point.
    Returns the current additive spike value (0 normally, spike_magnitude at peak).
    """
    if rng is None:
        rng = np.random.default_rng()
    phase_in_period = sim_time % spike_period
    if phase_in_period < spike_width:
        # Add spike with small random variation
        return spike_magnitude * (0.8 + 0.4 * rng.random())
    return 0.0


def calibration_drift_step(
    current_value: float,
    drift_rate_per_tick: float = 0.0003,
    recal_threshold: float = 0.30,
    rng: Optional[np.random.Generator] = None,
) -> float:
    """
    M-04 calibration deviation: very slow monotonic drift + reset when 'recalibrated'.
    No OU noise — calibration deviation is deterministic creep, not random fluctuation.
    drift_rate_per_tick: Nm_offset per tick (very slow)
    recal_threshold: automatically resets to near-zero when this is exceeded
    """
    if rng is None:
        rng = np.random.default_rng()
    new_value = current_value + drift_rate_per_tick + rng.normal(0, 0.0005)
    # Simulate periodic recalibration (reset when threshold crossed in normal operation)
    if new_value >= recal_threshold:
        new_value = rng.normal(0.002, 0.001)  # Post-recal near-zero
    return new_value
