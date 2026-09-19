# FANUC ARC Mate 100iD Maintenance Manual (B-83925EN/01)
Applicable Models: ARC Mate 100iD, ARC Mate 100iD/8L, ARC Mate 120iD
Controller: R-30iB Plus / R-30iB Mate Plus

## Chapter 1: Safety & Periodic Inspection Schedule
### 1.1 Periodic Inspection Intervals
- Daily: Check for abnormal vibration, unusual noise, and axis joint backlash. Inspect cable harness for pinching or sheath wear.
- Every 3 Months (500 operating hours): Measure brake slip torque for axes J1 through J6. Check connector tightness on servo amplifiers.
- Annually (2,000 operating hours): Replace battery for pulse coder backup (4x Size D Alkaline batteries). Inspect grease discharge ports for discoloration or metal shavings.
- Every 3 Years (10,000 operating hours): Complete grease replacement for all 6 reducer units using Molywhite RE No.00 grease.

## Chapter 2: Axis J2 Drive Mechanism & Harmonic Drive Maintenance
### 2.1 J2 Harmonic Reducer Specification & Symptoms of Wear
- Reduction ratio: 1/160.
- Lubricant: Kyodo Yushi Molywhite RE No.00 (Part No. A98L-0040-0174#16).
- Normal baseline operating torque: 18.0 Nm to 24.5 Nm during standard weaving motion.
- Failure Mode FC-ROB-001: Joint J2 Motor Over-Torque.
  - Initial Symptoms: Gradual exponential growth in peak motor current, torque baseline elevation >30 Nm, subtle harmonic hum at 120 Hz, slight repeatability degradation (+/- 0.08 mm).
  - Cause: Harmonic drive gear mesh degradation, tooth micro-pitting from grease starvation or thermal breakdown of extreme pressure additives.
  - Remedial Action:
    1. Lock arm in calibration fixture using transportation bracket.
    2. Drain old lubricant from J2 drain port. Check for silver metallic paste.
    3. Flush housing with clean spindle oil, then purge with fresh Molywhite RE No.00 grease (quantity: 380 cc).
    4. If torque deviation persists above 32 Nm after re-greasing, replace the J2 harmonic gear set (Part No. A97L-0218-0421) and recalibrate axis mastering.

## Chapter 3: Servo Amplifier & Electrical Faults (R-30iB Plus)
### 3.1 Servo Alarm SRVO-023: Stop Error Excess (High Load)
- Alarm Condition: The position error during axis motor motion exceeded the threshold set in $PARAM_GROUP[1].$STPERRLIM.
- Cause: Mechanical binding in axis reducer, defective dynamic brake, or failure of servo amplifier IGBT gate drive circuit.
- Troubleshooting Steps:
  1. Release brake manually using the brake release box and check joint movement smoothness.
  2. Measure phase-to-phase resistance of motor windings: Axis J2 motor should measure 0.42 ohms +/- 5% across U-V, V-W, W-U.
  3. Megger test: Check insulation resistance between motor power leads and chassis ground (must exceed 10 Mohm at 500V DC).

### 3.2 Servo Alarm SRVO-062: SVAL2 BZAL Alarm (Pulse Coder Disconnection)
- Cause: Absolute pulse coder backup battery voltage dropped below 2.8V DC or pulse coder cable shielding severed.
- Action: Replace battery with controller energized. If alarm occurred with power OFF, perform zero-point axis mastering (Quick Mastering or Single Axis Mastering per Section 4.2).

### 3.3 Servo Alarm SRVO-050: CLALM Alarm (Collision / Over-Torque Detection)
- Cause: Disturbance torque detected by the software disturbance observer exceeded tolerance.
- Failure Mode FC-ROB-002: Axis J3 Servo Amplifier Alarm.
  - Component: Servo Amplifier Module (Part No. A06B-6240-H105).
  - Diagnosis: Elevated heat sink temperature >85 degC, intermediate DC bus voltage fluctuating outside 280V–340V DC range, switching transistor saturation voltage drift.
  - Remedial Action:
    1. Turn off main circuit breaker and wait 10 minutes for discharge LED on servo amplifier to extinguish.
    2. Inspect cabinet cooling fan A90L-0001-0538; clean heat sink fins with compressed air.
    3. Replace damaged 6-axis servo amplifier module A06B-6240-H105.
    4. Power up and verify bus voltage stabilises at 310V DC.

## Chapter 4: Axis Mastering & Zero-Point Calibration
### 4.1 Calibration Alignment Marks
Each joint (J1 to J6) has scribed mechanical zero alignment marks (vernier marks). When all axes are aligned to zero marks, the robot position corresponds to (0, 0, 0, 0, -90, 0) degrees in J2/J3 relative coordinates.
### 4.2 Single Axis Mastering Procedure
1. Navigate to: [MENU] -> [0 NEXT] -> [6 SYSTEM] -> [Master/Cal].
2. If Master/Cal does not appear, set $MASTER_ENB = 1 in System Variables.
3. Select [4 Single Axis Master] and press ENTER.
4. Position the target axis at its alignment witness mark.
5. Set SEL column to 1 for the target axis, then press [F5 EXEC].
6. Press [FCTN] -> [1 ABORT ALL], then return to Master/Cal and select [6 CALIBRATE], press [F4 YES].
