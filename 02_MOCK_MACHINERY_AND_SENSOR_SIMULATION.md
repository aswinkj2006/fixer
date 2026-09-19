# FixIQ — Mock Machinery & Sensor Simulation

## The mock fleet (4 machines)

| ID | Machine | Type | Realistic fault mode | Spoofed signals |
|----|---------|------|----------------------|------------------|
| M-01 | 6-axis robotic welding arm | Robotics | Reducer grease leak → rising axis torque | torque (Nm), vibration, cycle count |
| M-02 | CNC precision mill | Precision engineering | Spindle bearing wear → tolerance drift | vibration, spindle temp, RPM |
| M-03 | Conveyor/press motor | Automotive | Bearing wear, general vibration + heat | vibration, motor temp, current draw |
| M-04 | Torque calibration station | Automotive/compliance | Calibration drift (AS9100 audit hotspot) | calibration deviation, last-cal date |

M-01 should be modeled after a real machine: the **FANUC ARC Mate 100iD / 120iD**, a real 6-axis arc-welding robot with publicly available manuals — see `06_RESEARCH_AND_SOURCES.md` for the exact manual links to ingest into the RAG store for this machine's Tier 1 collection.

## Why realism matters here specifically

Random per-tick noise looks fake almost immediately to anyone who has seen real sensor data. What makes simulated data feel real is **correlated, mean-reverting fluctuation** plus a **duty-cycle pattern** — not independent random numbers each tick.

## Normal operation: Ornstein-Uhlenbeck (mean-reverting) process

Use this instead of plain Gaussian noise for every sensor's baseline fluctuation:

```
next_value = current_value + theta * (baseline - current_value) * dt + sigma * random_normal() * sqrt(dt)
```

- `theta` = how strongly the value reverts to baseline (higher = tighter/steadier signal)
- `sigma` = noise magnitude — should differ per sensor type (vibration needs higher sigma than temperature; temperature has thermal lag and shouldn't jitter fast)

## Duty-cycle layer (on top of the OU baseline)

- **Robotic arm torque (M-01)**: rises during a weld cycle, drops to near-zero at idle. Model as a repeating trapezoid/square wave with OU noise added on top.
- **CNC spindle temp (M-02)**: climbs during cutting (exponential approach to a "hot" setpoint), cools during tool-change pauses (exponential decay toward ambient).
- **Conveyor motor current (M-03)**: fairly flat baseline with periodic load spikes when parts pass a sensor point.
- **Calibration deviation (M-04)**: near-flat, moves very little day-to-day, with periodic resets when "recalibrated" — this near-stillness is itself realistic and should not be given the same noise treatment as the other three.

## Per-sensor noise character (this is what sells realism to someone testing it closely)

- **Vibration**: OU baseline + occasional short non-Gaussian spikes (real accelerometers have heavy-tailed noise, not clean Gaussian).
- **Temperature**: heavily smoothed (low-pass filter / exponential moving average) — real thermal sensors don't jitter fast tick-to-tick.
- **Torque / current**: tightly correlated to the duty cycle, low independent noise.
- **Calibration deviation**: slow monotonic drift only, essentially flat between recalibration events.

## Three hidden failure trigger modes

Do not make these instant spike triggers — an immediate jump to a red-alert state the moment a hidden button is pressed will look scripted to a judge. Instead, make each one a **gradual escalation** that develops over the demo window (run the simulation clock faster than real time so "weeks" of drift compress into minutes):

- **Mode 1 (M-01, robotic arm)**: torque baseline climbs exponentially — `baseline += A * (exp(k*t) - 1)` — mimicking a grease-leak-driven friction increase.
- **Mode 2 (M-02, CNC mill)**: vibration variance (sigma) increases over time, plus a slow upward baseline shift — mimicking bearing wear.
- **Mode 3 (M-03, conveyor)**: current draw baseline steps upward and vibration spikes become more frequent — mimicking a developing motor fault.

Implement as a hidden config flag or secret admin route (e.g. `/admin/trigger?machine=M01&mode=1`) that swaps that machine's generator parameters to the failure preset. Everything else keeps running on the normal OU/duty-cycle model — the fact that most of what a judge sees during the demo is convincingly boring/normal is what makes the triggered failure moments credible.

## Physical/degradation grounding (optional, for extra credibility)

If time allows, ground the failure-mode escalation curves in real degradation literature rather than an arbitrary exponential constant — reliability engineering commonly uses Weibull hazard functions and feature-drift metrics like kurtosis growth to describe bearing degradation. See `06_RESEARCH_AND_SOURCES.md` for the relevant papers. This is a nice-to-have for technical credibility with judges who probe the math, not a hard requirement for the demo to work.
