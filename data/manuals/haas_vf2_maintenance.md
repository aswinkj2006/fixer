# Haas VF-2 CNC Mill Maintenance & Troubleshooting Manual (96-0115 Rev AN)
Series: Haas Classic / Next Generation Control (NGC)
Spindle: 30-Horsepower Inline Direct-Drive / 8,100 RPM / 10,000 RPM 40-Taper

## Chapter 1: Spindle System & Vibration Analysis
### 1.1 Spindle Baseline Specifications
- Maximum Speed: 8,100 RPM (Standard) / 10,000 RPM (High-Speed Option).
- Baseline RMS Vibration: 0.8 mm/s2 to 1.4 mm/s2 across full speed range (20 Hz - 5,000 Hz).
- Spindle Taper Runout: < 0.0002 inches (0.005 mm) TIR at spindle nose.
- Drawbar Pull Force: 1,800 to 2,200 lbs (8.0 to 9.8 kN) at 40-Taper retention knob.

### 1.2 Failure Mode FC-CNC-001: Spindle Bearing Vibration High
- Symptom: Continuous escalation of vibration velocity RMS beyond 4.5 mm/s2 at 8,000 RPM. Distinct high-frequency harmonic peak at Ball Pass Frequency Outer Race (BPFO = 328 Hz).
- Cause: Front angular contact hybrid ceramic bearing pair race spalling or cage fatigue, accelerated by heavy side-load face milling and contaminated chiller fluid.
- Alarm: Alarm 9100.016 — Spindle Vibration Limit Exceeded.
- Corrective Maintenance Procedure:
  1. Perform spindle sweep test using 0.0001" dial indicator on 300 mm test arbor.
  2. Measure axial and radial play: If radial deflection exceeds 0.012 mm under 50 N side load, replace spindle cartridge assembly.
  3. Replacement Part: Haas Spindle Cartridge 40T 10K (Part No. 93-30-10020B).
  4. Post-replacement Run-In Procedure (Mandatory 4-hour cycle):
     - Step 1: 500 RPM for 30 minutes. Check bearing temp (< 35 degC).
     - Step 2: 2,000 RPM for 45 minutes.
     - Step 3: 5,000 RPM for 45 minutes.
     - Step 4: 8,000 RPM for 60 minutes. Verify RMS vibration < 1.2 mm/s2.

## Chapter 2: Lubrication System (Minimum Quantity Lubrication & Way Lube)
### 2.1 Lubrication Distribution & Pressure Sensors
- Way Lube System: Bijur Delimon electric pump delivering Mobil Vactra No. 2 Way Oil to linear guide trucks and ballscrew nuts.
- Pressure Specification: Cycle pressure must reach 35 to 45 PSI (2.4 to 3.1 bar) within 45 seconds of pump activation.
- Failure Mode FC-CNC-002: Way Lube Pressure Low.
  - Symptom: Sensor indicates lube pressure failing to reach 25 PSI during 30-minute auto-lube interval. Controller warning: Alarm 121 — Low Lube Pressure.
  - Root Cause:
    1. Filter screen at reservoir bottom fouled with dried paraffin and particulate sludge.
    2. Pressure switch diaphragm rupture or electrical contact oxidation.
    3. Leak in 4mm polyurethane distribution line to Y-axis saddle truck.
  - Corrective Procedure:
    1. Disconnect lube reservoir (Part No. 93-2172). Drain contaminated Vactra No. 2 oil.
    2. Clean reservoir body and suction tube with mineral spirits.
    3. Replace 40-micron suction filter screen (Part No. 58-3012).
    4. Prime system manually using manual stroke lever on pump until oil emerges without air bubbles from all 6 linear guide metering valves.
    5. Clear Alarm 121 on NGC pendant: Press [DIAGNOSTIC] -> [MAINTENANCE] -> Reset Lube Timer.
