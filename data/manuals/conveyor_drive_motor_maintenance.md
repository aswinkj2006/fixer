# Industrial Conveyor Drive Assembly Maintenance Manual
Drive Configuration: 7.5 kW TEFC 3-Phase Induction Motor + Worm Gear Speed Reducer + V-Belt Final Stage
Application: Press Line Conveyance System (Station 7)

## Section 1: Electric Motor Specifications & Operating Limits
- Rated Power: 7.5 kW (10 HP), 400V 50Hz, 14.5 Amps full load current (FLC).
- Synchronous Speed: 1,500 RPM (4-pole), Nominal Operating Speed: 1,440 RPM.
- Bearing Type: Drive-End: 6208-2RS C3 Deep Groove Ball Bearing; Non-Drive-End: 6207-2RS C3.
- Normal Operating Temperature: 50 degC to 68 degC at motor stator housing.
- Thermal Overload Threshold: 85 degC warning, 95 degC trip.

## Section 2: Failure Mode FC-CNV-001: Drive Motor Bearing Thermal Runaway
- Symptom: Continuous monotonic rise in motor bearing housing temperature from 55 degC up to 90 degC+, accompanied by high-frequency acoustic emission (> 5 kHz) and progressive increase in phase current draw (+15% above 14.5A baseline).
- Cause: Lubricant starvation, grease oxidation, or severe ball raceway micro-welding due to thermal breakdown of polyurea thickener.
- Vibration Signature: Overall ISO 10816-3 vibration exceeds Class II 'Unrestricted Long-Term Operation' limit (4.5 mm/s RMS).
- Corrective Repair Procedure:
  1. Lock Out / Tag Out (LOTO) main motor disconnect switch at MCC panel.
  2. Remove belt guard and slacken tensioner bracket bolts. Slip drive belts off sheaves.
  3. Uncouple motor from worm reducer adapter flange.
  4. Pull motor end-bell using mechanical three-jaw puller. Extract damaged 6208-2RS bearing.
  5. Inspect motor rotor shaft bearing journal for fretting corrosion (tolerance: 40.002 mm to 40.011 mm).
  6. Induction heat replacement SKF 6208-2RSH/C3 bearing to 110 degC and install flush against shaft shoulder.
  7. Re-grease with 12 grams of Mobil Polyrex EM synthetic polyurea grease.
  8. Reassemble, check air gap uniformity (0.35 mm +/- 0.05 mm), and re-torque end-bell through-bolts to 28 Nm.

## Section 3: V-Belt Transmission & Tensioning (FC-CNV-002)
- Drive Belts: Matched set of three (3) Gates Super HC 3VX450 Cogged V-Belts.
- Symptom of Failure Mode FC-CNV-002:
  - Slippage between motor sheave and reducer input pulley under peak press discharge load.
  - Audible belt squeal during conveyor start sequence.
  - Belt surface glazing, rubber debris inside belt housing, sheave groove polishing.
  - Conveyor linear velocity dropping from 0.45 m/s to 0.38 m/s while motor runs at full RPM.
- Root Cause: Belt tension decay below minimum resonant frequency due to structural relaxation and looseness in the jackbolt tensioning cradle.
- Corrective Action:
  1. Inspect sheave grooves with V-belt groove profile gauge. Replace sheave if groove sidewall wear exceeds 0.8 mm.
  2. Replace all three belts simultaneously as a factory-matched set (never replace a single belt in a multi-groove set).
  3. Adjust motor slide base using adjustment screws until acoustic belt tension meter reads 62 Hz to 68 Hz at center span with 25 N span deflection.
  4. Verify laser sheave alignment: Angular misalignment must be < 0.2 degrees, parallel offset < 0.5 mm.
  5. Tighten motor foundation anchor bolts to 85 Nm and re-check tension after 24 hours of operation.
