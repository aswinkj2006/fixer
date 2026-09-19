# Torque Tool Calibration Station Operating & Verification Procedure (ISO 6789-2:2017)
Station ID: QA-TC-04 / M-04
System Type: Dual-Range Reaction Torque Transducer System (Range: 5 Nm – 500 Nm)
Controller: Precision Digital Metrology Amplifier System

## Section 1: Standard Operating Norms & ISO 6789 Requirements
- International Standard: ISO 6789-2:2017 (Assembly tools for screws and nuts — Hand torque tools — Part 2: Requirements for calibration and determination of measurement uncertainty).
- Environmental Operating Range: Temperature 20 degC +/- 2 degC; Relative Humidity 40% to 65%.
- Maximum Permissible Measurement Uncertainty: <= 1.0% of measured torque value across 20% to 100% of transducer nominal range.
- Tare Zero Baseline: +/- 0.02 Nm offset maximum under no-load condition.

## Section 2: Failure Mode FC-CAL-001: Transducer Zero Drift
- Symptom:
  - Slow, steady monotonic drift of tare baseline offset from nominal 0.02 Nm up past 0.15 Nm and reaching > 0.35 Nm over 48 hours.
  - Tool verification readings consistently failing 6-sigma tolerance gates on automated production line.
- Root Cause:
  1. Thermal hysteresis or resistive strain gauge foil delamination on internal Wheatstone bridge beam.
  2. Moisture ingress through transducer hermetic seal causing insulation leakage across bridge corners.
  3. Pre-load mechanical strain on reaction torque reaction arm due to loose mounting flange bolts.
- Diagnostic & Recalibration Procedure:
  1. Check ambient room temperature: Verify QA Metrology room temperature sensor is calibrated (20.0 degC +/- 1.0 degC).
  2. Unload the calibration socket completely and execute amplifier zero balance routine.
  3. Perform 5-point calibration test cycle using deadweight calibration beam and Class M1 certified standard weights:
     - Point 1: 20% of scale (100 Nm)
     - Point 2: 40% of scale (200 Nm)
     - Point 3: 60% of scale (300 Nm)
     - Point 4: 80% of scale (400 Nm)
     - Point 5: 100% of scale (500 Nm)
  4. Record 5 ascending and 5 descending cycles per ISO 6789-2 clause 6.3.
  5. Calculate relative measurement error:
     w_e = [(X_obs - X_ref) / X_ref] * 100%
  6. If relative measurement error exceeds 1.0% or tare offset remains > 0.05 Nm:
     - Inspect transducer cable connector for bent pins or contamination (clean with anhydrous isopropyl alcohol).
     - Replace reaction torque transducer (Model: HBM T20WN / 500 Nm, Part No. QA-TR-500).
     - Enter new factory calibration matrix coefficients (Sensitivity S = 2.0015 mV/V, Zero Balance Z = -0.003 mV/V) into amplifier metrology firmware.
