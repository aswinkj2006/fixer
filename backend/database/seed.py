"""
fixer.ai — Database seed script
Seeds: 4 machines, 4 technicians, 8 failure codes, 10 synthetic resolved tickets.

Run once:
    python -m backend.database.seed

Seeds are idempotent — safe to run multiple times (upsert by primary key).
"""
import asyncio
import json
import os
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Allow running as a module from project root
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.dialects.sqlite import insert as sqlite_insert

from backend.config import DATABASE_URL
from backend.database.models import Base, Machine, Technician, FailureCode, Ticket, TicketMessage


def _now_str() -> str:
    return datetime.now(timezone.utc).isoformat()


def _days_ago(n: int) -> str:
    return (datetime.now(timezone.utc) - timedelta(days=n)).isoformat()


# ─────────────────────────────────────────────────────────────────────────────
# MACHINES (4 machines, matching 02_MOCK_MACHINERY_AND_SENSOR_SIMULATION.md)
# ─────────────────────────────────────────────────────────────────────────────
MACHINES = [
    {
        "machine_id": "M-01",
        "name": "FANUC ARC Mate 100iD — Welding Cell A",
        "model": "fanuc_arc_mate_100id",
        "machine_type": "robot_arm",
        "install_date": "2022-03-15",
        "location": "Bay 3 — Robotic Welding Cell",
        "baseline_ranges": json.dumps({
            "torque": {"mean": 45.0, "std": 3.2, "min": 20.0, "max": 120.0, "unit": "Nm"},
            "vibration": {"mean": 0.82, "std": 0.12, "min": 0.0, "max": 5.0, "unit": "mm/s2"},
            "cycle_count": {"mean": 0.0, "std": 0.0, "min": 0.0, "max": 1.0, "unit": "cycles"},
        }),
    },
    {
        "machine_id": "M-02",
        "name": "Haas VF-2 CNC Mill — Line 2",
        "model": "haas_vf2",
        "machine_type": "cnc_mill",
        "install_date": "2021-07-22",
        "location": "Bay 1 — Precision Machining",
        "baseline_ranges": json.dumps({
            "vibration": {"mean": 1.1, "std": 0.18, "min": 0.0, "max": 8.0, "unit": "mm/s2"},
            "temperature": {"mean": 42.0, "std": 5.0, "min": 20.0, "max": 85.0, "unit": "degC"},
            "rpm": {"mean": 8000.0, "std": 200.0, "min": 0.0, "max": 12000.0, "unit": "rpm"},
        }),
    },
    {
        "machine_id": "M-03",
        "name": "Conveyor Drive Motor — Press Station 7",
        "model": "generic_conveyor",
        "machine_type": "conveyor",
        "install_date": "2020-11-08",
        "location": "Bay 5 — Press & Conveyance",
        "baseline_ranges": json.dumps({
            "vibration": {"mean": 2.1, "std": 0.30, "min": 0.0, "max": 12.0, "unit": "mm/s2"},
            "temperature": {"mean": 55.0, "std": 4.0, "min": 20.0, "max": 90.0, "unit": "degC"},
            "current": {"mean": 14.5, "std": 1.2, "min": 0.0, "max": 30.0, "unit": "A"},
        }),
    },
    {
        "machine_id": "M-04",
        "name": "Torque Calibration Station — QA Bay",
        "model": "calibration_station",
        "machine_type": "calibration_station",
        "install_date": "2023-01-10",
        "location": "QA Bay — Metrology",
        "baseline_ranges": json.dumps({
            # Calibration deviation: near-flat, very slow monotonic drift
            "calibration_dev": {"mean": 0.02, "std": 0.005, "min": -0.5, "max": 0.5, "unit": "Nm_offset"},
        }),
    },
]

# ─────────────────────────────────────────────────────────────────────────────
# TECHNICIANS (Indian names per spec)
# ─────────────────────────────────────────────────────────────────────────────
_DEMO_SLACK_USER_ID = os.getenv("SLACK_TECHNICIAN_ID", "U0C2LRFUGSX")
TECHNICIANS = [
    {
        "technician_id": "T-01",
        "name": "Arjun Sharma",
        "specialty": "mechanical",
        "slack_user_id": _DEMO_SLACK_USER_ID,
    },
    {
        "technician_id": "T-02",
        "name": "Priya Nair",
        "specialty": "electrical",
        "slack_user_id": _DEMO_SLACK_USER_ID,
    },
    {
        "technician_id": "T-03",
        "name": "Kavitha Reddy",
        "specialty": "calibration",
        "slack_user_id": _DEMO_SLACK_USER_ID,
    },
    {
        "technician_id": "T-04",
        "name": "Rohan Mehta",
        "specialty": "mechanical",
        "slack_user_id": _DEMO_SLACK_USER_ID,
    },
]

# ─────────────────────────────────────────────────────────────────────────────
# FAILURE CODES (Problem → Cause → Remedy taxonomy, ISO 14224 pattern)
# ─────────────────────────────────────────────────────────────────────────────
FAILURE_CODES = [
    # Robot arm (M-01)
    {
        "code": "FC-ROB-001",
        "machine_type": "robot_arm",
        "problem": "Elevated joint torque on axis J3",
        "cause": "Reducer grease leak causing increased friction — insufficient lubrication at gear contact surfaces",
        "remedy": "Inspect and replace J3 reducer grease (FANUC spec: Vigo Grease RE0). Re-grease to specified quantity. Verify torque returns to baseline. Schedule preventive re-lubrication at next PM interval.",
    },
    {
        "code": "FC-ROB-002",
        "machine_type": "robot_arm",
        "problem": "Abnormal vibration signature on weld cycle",
        "cause": "Worn servo motor bearing or loose TCP (Tool Centre Point) fixture causing resonance",
        "remedy": "Inspect TCP fixture bolts and retighten to spec. Check servo motor bearing play. If bearing wear confirmed, replace servo motor. Re-run TCP calibration after any fixture work.",
    },
    # CNC mill (M-02)
    {
        "code": "FC-CNC-001",
        "machine_type": "cnc_mill",
        "problem": "Spindle bearing wear — increasing vibration, reduced precision",
        "cause": "Spindle bearing fatigue from cumulative cutting hours, coolant contamination, or inadequate lubrication",
        "remedy": "Replace spindle bearings. Before replacement: confirm vibration spectrum shows defect frequency signature (BPFO/BPFI harmonics). After replacement: run spindle run-in cycle per Haas procedure, re-qualify workpiece dimensions.",
    },
    {
        "code": "FC-CNC-002",
        "machine_type": "cnc_mill",
        "problem": "Dimensional tolerance drift on finished parts",
        "cause": "Thermal expansion during prolonged cutting without warm-up cycle, or spindle runout exceeding 0.005mm",
        "remedy": "Run Haas warm-up macro before production. Check and correct spindle runout with test indicator. If runout persists after tightening tool holder, inspect spindle taper for fretting.",
    },
    # Conveyor (M-03)
    {
        "code": "FC-CNV-001",
        "machine_type": "conveyor",
        "problem": "Rising motor current draw with vibration increase",
        "cause": "Developing bearing fault in drive motor — early-stage spalling increasing mechanical resistance",
        "remedy": "Obtain vibration spectrum (kurtosis > 4 = bearing fault confirmed). Schedule planned bearing replacement within 2 weeks. Temporary: reduce conveyor load by 20% and increase greasing frequency. Do not defer beyond confirmed spike pattern.",
    },
    {
        "code": "FC-CNV-002",
        "machine_type": "conveyor",
        "problem": "Intermittent belt slip under load",
        "cause": "Worn drive belt or insufficient belt tension",
        "remedy": "Measure belt tension with tension meter. Adjust to spec or replace belt. Check drive pulley for wear groove — if depth > 2mm, replace pulley.",
    },
    # Calibration station (M-04)
    {
        "code": "FC-CAL-001",
        "machine_type": "calibration_station",
        "problem": "Calibration deviation drift approaching AS9100 alert threshold",
        "cause": "Reference spring relaxation or load cell drift between scheduled calibration intervals",
        "remedy": "Perform immediate re-calibration using NIST-traceable reference weights per ISO 6789 procedure. Document calibration certificate. If drift rate > 0.05 Nm/month, schedule inspection of reference load cell for fatigue or contamination.",
    },
    {
        "code": "FC-CAL-002",
        "machine_type": "calibration_station",
        "problem": "Out-of-spec torque wrench reading confirmed on audit check",
        "cause": "Calibration interval exceeded or physical shock to instrument",
        "remedy": "Remove instrument from service immediately. Log CAPA (Corrective and Preventive Action) in QMS. Re-calibrate or replace. Review all parts torqued with this instrument since last valid calibration — flag for re-inspection per AS9100 nonconformance procedure.",
    },
]

# ─────────────────────────────────────────────────────────────────────────────
# SYNTHETIC RESOLVED TICKETS (10 total — 2–3 per machine)
# These seed the dashboard, recurring-fault detection, and Tier 2 RAG from Day 1.
# ─────────────────────────────────────────────────────────────────────────────

def _make_ticket_and_messages(
    machine_id: str,
    failure_code: str,
    symptom: str,
    diagnosis_json: dict,
    repair_summary: str,
    technician_id: str,
    days_ago_opened: int,
    days_ago_closed: int,
    messages: list[dict],
) -> tuple[dict, list[dict]]:
    tid = str(uuid.uuid4())
    ticket = {
        "ticket_id": tid,
        "machine_id": machine_id,
        "opened_at": _days_ago(days_ago_opened),
        "closed_at": _days_ago(days_ago_closed),
        "symptom_text": symptom,
        "image_ref": None,
        "audio_transcript": symptom,
        "diagnosis": json.dumps(diagnosis_json),
        "confidence": diagnosis_json.get("confidence", 0.85),
        "severity": diagnosis_json.get("severity", "medium"),
        "status": "resolved",
        "assigned_technician_id": technician_id,
        "slack_thread_ts": None,
        "failure_code": failure_code,
        "resolution_summary": repair_summary,
    }
    msgs = []
    for m in messages:
        msgs.append({
            "ticket_id": tid,
            "machine_id": machine_id,
            "sender": m["sender"],
            "sender_name": m.get("sender_name", ""),
            "text": m["text"],
            "timestamp": _days_ago(days_ago_opened - m.get("hours_offset", 0) / 24),
            "slack_ts": None,
        })
    return ticket, msgs


SYNTHETIC_TICKETS_RAW = [
    # M-01 — ticket 1: grease leak detected early
    _make_ticket_and_messages(
        machine_id="M-01",
        failure_code="FC-ROB-001",
        symptom="J3 axis torque readings trending upward over the past 3 days. No audible noise yet but torque is 15% above baseline.",
        diagnosis_json={
            "ranked_diagnoses": [
                {"diagnosis": "J3 reducer grease leak / insufficient lubrication", "confidence": 0.88, "evidence": "Torque trending +15% over 72h, no vibration spike yet — consistent with friction increase from lubrication degradation."}
            ],
            "severity": "medium",
            "confidence": 0.88,
            "repair_steps": [
                "Isolate M-01 and lock-out/tag-out per safety procedure.",
                "Inspect J3 reducer housing for grease leakage (visual + white-rag wipe).",
                "If leak confirmed: clean sealing surface, replace O-ring seal, re-grease with FANUC-specified Vigo Grease RE0.",
                "Restore power and run 5-cycle test. Verify torque returns within 5% of baseline.",
            ],
            "parts_likely_needed": ["J3 reducer O-ring kit", "Vigo Grease RE0 (250g)"],
            "specialist_required": "mechanical",
        },
        repair_summary="J3 reducer O-ring replaced, re-greased. Torque returned to baseline within 2 cycles.",
        technician_id="T-01",
        days_ago_opened=21,
        days_ago_closed=20,
        messages=[
            {"sender": "bot", "sender_name": "fixer.ai", "text": "Diagnosis: J3 reducer grease leak suspected (88% confidence). Torque trending +15% over 72h. Recommended action: inspect J3 reducer housing for grease leak. Severity: MEDIUM.", "hours_offset": 0},
            {"sender": "technician", "sender_name": "Arjun Sharma", "text": "Confirmed grease leak on J3 reducer — can see grease residue on the housing lower seal. Going to replace the O-ring and re-grease.", "hours_offset": 2},
            {"sender": "bot", "sender_name": "fixer.ai", "text": "Confirmed. FANUC spec for J3 re-greasing: Vigo Grease RE0, 250g quantity. Replace O-ring seal (part: A98L-0040-0174). Torque test after: expect return to 44–47 Nm range.", "hours_offset": 2},
            {"sender": "technician", "sender_name": "Arjun Sharma", "text": "Done. Replaced O-ring, re-greased. Running test cycles now. Torque reading: 45.2 Nm. Back to normal.", "hours_offset": 5},
            {"sender": "system", "sender_name": "fixer.ai", "text": "Ticket resolved. Resolution embedded into M-01 memory.", "hours_offset": 5},
        ],
    ),
    # M-01 — ticket 2: vibration anomaly during weld
    _make_ticket_and_messages(
        machine_id="M-01",
        failure_code="FC-ROB-002",
        symptom="Unusual vibration felt during weld arc — welder reports robot arm feels 'shaky' at extension. No quality reject yet.",
        diagnosis_json={
            "ranked_diagnoses": [
                {"diagnosis": "Loose TCP fixture causing resonance at weld extension", "confidence": 0.79, "evidence": "Vibration elevated at end-of-arm during weld position, not at idle — pattern consistent with mechanical looseness at tooling, not bearing."}
            ],
            "severity": "medium",
            "confidence": 0.79,
            "repair_steps": [
                "Check and retighten all TCP fixture bolts to specified torque (FANUC spec: 15 Nm for M8 bolts).",
                "Re-run TCP calibration using the robot teach pendant.",
                "Run 10 weld cycles in the problem position and monitor vibration sensor.",
                "If vibration persists after TCP fix, inspect J5/J6 servo motor bearing for play.",
            ],
            "parts_likely_needed": ["TCP calibration tool"],
            "specialist_required": "mechanical",
        },
        repair_summary="TCP fixture had 2 loose M8 bolts — retightened. Vibration resolved after TCP recalibration.",
        technician_id="T-04",
        days_ago_opened=14,
        days_ago_closed=14,
        messages=[
            {"sender": "bot", "sender_name": "fixer.ai", "text": "Diagnosis: TCP fixture looseness suspected (79% confidence). Vibration elevated at weld extension position only — consistent with tooling resonance, not bearing failure. Severity: MEDIUM.", "hours_offset": 0},
            {"sender": "technician", "sender_name": "Rohan Mehta", "text": "Checked TCP bolts — two M8 bolts were finger-tight. Retightened to 15 Nm. Running TCP calibration now.", "hours_offset": 1},
            {"sender": "technician", "sender_name": "Rohan Mehta", "text": "TCP cal done. Ran 10 test welds — vibration normal. Weld bead quality check passed.", "hours_offset": 3},
        ],
    ),
    # M-01 — ticket 3: similar grease issue, recurrence
    _make_ticket_and_messages(
        machine_id="M-01",
        failure_code="FC-ROB-001",
        symptom="J3 torque creeping up again — similar pattern to 3 weeks ago. 12% above baseline.",
        diagnosis_json={
            "ranked_diagnoses": [
                {"diagnosis": "J3 reducer grease leak recurrence — O-ring seal may not have been seated correctly on last repair, or grease quantity was insufficient", "confidence": 0.91, "evidence": "Same torque drift pattern as ticket 3 weeks ago. Recurrence within short interval suggests root cause not fully addressed."}
            ],
            "severity": "medium",
            "confidence": 0.91,
            "repair_steps": [
                "Inspect J3 reducer O-ring seat — check for nicks or improper seating from previous repair.",
                "Replace O-ring regardless; ensure mating surface is clean and burr-free before seating.",
                "Re-grease to correct quantity (do not over-fill — excess grease causes seal failure).",
                "After repair, increase grease check interval from 3-monthly to 6-weekly for J3.",
            ],
            "parts_likely_needed": ["J3 reducer O-ring kit", "Vigo Grease RE0 (250g)"],
            "specialist_required": "mechanical",
        },
        repair_summary="O-ring from previous repair had micro-nick causing slow weep. New O-ring seated correctly. Increased J3 check interval to 6-weekly.",
        technician_id="T-01",
        days_ago_opened=7,
        days_ago_closed=6,
        messages=[
            {"sender": "bot", "sender_name": "fixer.ai", "text": "⚠️ Recurring pattern detected: J3 reducer grease leak — this is the 2nd occurrence on M-01 in 21 days. Previous fix: O-ring replaced 21 days ago (Ticket resolved by Arjun Sharma). Confidence: 91%. Recommend inspecting O-ring seat quality. Severity: MEDIUM.", "hours_offset": 0},
            {"sender": "technician", "sender_name": "Arjun Sharma", "text": "Found the issue — O-ring from last time had a small nick on the inner lip. Must have been a defect. Replacing with new one and checking the seating surface first.", "hours_offset": 2},
            {"sender": "bot", "sender_name": "fixer.ai", "text": "Recommendation: after this repair, increase J3 grease check from 3-monthly to 6-weekly and log as a 'watch item' in the PM schedule.", "hours_offset": 2},
            {"sender": "technician", "sender_name": "Arjun Sharma", "text": "Done. New O-ring properly seated. Torque back to 44.8 Nm. Flagged for 6-weekly checks.", "hours_offset": 4},
        ],
    ),
    # M-02 — ticket 1: spindle bearing early wear
    _make_ticket_and_messages(
        machine_id="M-02",
        failure_code="FC-CNC-001",
        symptom="Surface finish degrading on aluminum parts. Spindle vibration sensor reading 20% above historical baseline during cuts.",
        diagnosis_json={
            "ranked_diagnoses": [
                {"diagnosis": "Spindle bearing early-stage wear — elevated vibration during cutting", "confidence": 0.84, "evidence": "Vibration 20% above baseline, correlated with cutting load. Surface finish degradation consistent with spindle runout increase from bearing wear."}
            ],
            "severity": "medium",
            "confidence": 0.84,
            "repair_steps": [
                "Measure spindle runout with a dial indicator (acceptance: < 0.005mm TIR).",
                "If runout > 0.010mm: schedule spindle bearing replacement at next available maintenance window.",
                "Immediate mitigation: reduce spindle speed by 15% and feed rate by 10% to preserve finish quality.",
                "Run Haas spindle warm-up macro for 20 minutes before production to stabilize thermal expansion.",
            ],
            "parts_likely_needed": ["Haas VF-2 spindle bearing set", "Dial indicator (0.001mm resolution)"],
            "specialist_required": "mechanical",
        },
        repair_summary="Runout measured at 0.013mm (over spec). Spindle bearings replaced. Post-repair runout: 0.003mm. Surface finish back to spec.",
        technician_id="T-01",
        days_ago_opened=30,
        days_ago_closed=28,
        messages=[
            {"sender": "bot", "sender_name": "fixer.ai", "text": "Diagnosis: spindle bearing early wear (84% confidence). Vibration 20% above M-02 historical baseline during cuts. Recommend spindle runout measurement immediately. Severity: MEDIUM.", "hours_offset": 0},
            {"sender": "technician", "sender_name": "Arjun Sharma", "text": "Runout measured: 0.013mm — outside Haas spec of 0.005mm. Scheduling spindle bearing replacement. Reducing speed/feed in the meantime.", "hours_offset": 3},
            {"sender": "technician", "sender_name": "Arjun Sharma", "text": "Bearing replacement complete. Post-repair runout: 0.003mm. Test parts measure within tolerance. Sign-off done.", "hours_offset": 51},
        ],
    ),
    # M-02 — ticket 2: thermal drift
    _make_ticket_and_messages(
        machine_id="M-02",
        failure_code="FC-CNC-002",
        symptom="First batch of the shift showing +0.04mm dimensional error on Z-depth. Error disappears after machine runs for 30 minutes.",
        diagnosis_json={
            "ranked_diagnoses": [
                {"diagnosis": "Thermal drift on cold startup — spindle and column thermal expansion not stabilised", "confidence": 0.93, "evidence": "Error present on first batch, disappears after 30 min warm-up. Pattern is textbook cold-start thermal drift — not a wear issue."}
            ],
            "severity": "low",
            "confidence": 0.93,
            "repair_steps": [
                "Run Haas spindle warm-up macro (Macro O9999 or equivalent) for minimum 20 minutes before production.",
                "During warm-up, run a dry-run of the program in air to allow column thermal stabilisation.",
                "After warm-up, measure Z reference with a gauge block — adjust G54 Z offset if needed.",
                "This is a process/procedure issue, not a hardware failure — no parts required.",
            ],
            "parts_likely_needed": [],
            "specialist_required": "none",
        },
        repair_summary="Warm-up macro added to start-of-shift procedure. Z drift eliminated. Operator briefed.",
        technician_id="T-02",
        days_ago_opened=18,
        days_ago_closed=18,
        messages=[
            {"sender": "bot", "sender_name": "fixer.ai", "text": "Self-resolve path (low severity, 93% confidence): thermal drift on cold startup. No hardware fault. Action: implement spindle warm-up macro before first production batch.", "hours_offset": 0},
            {"sender": "technician", "sender_name": "Priya Nair", "text": "Confirmed — we weren't running the warm-up macro consistently. Added it to the shift-start checklist. Test measurement after 20-min warm-up: Z error = 0.001mm. Fixed.", "hours_offset": 1},
        ],
    ),
    # M-03 — ticket 1: current rise + bearing warning
    _make_ticket_and_messages(
        machine_id="M-03",
        failure_code="FC-CNV-001",
        symptom="Motor current draw 18% above normal and vibration increasing over the past week. Motor running hotter than usual.",
        diagnosis_json={
            "ranked_diagnoses": [
                {"diagnosis": "Developing drive motor bearing fault — early-stage spalling increasing friction and current draw", "confidence": 0.86, "evidence": "Current +18%, vibration trending upward, temperature elevated — triad pattern consistent with bearing spalling progression."}
            ],
            "severity": "high",
            "confidence": 0.86,
            "repair_steps": [
                "Obtain vibration spectrum (kurtosis measurement): if kurtosis > 4, bearing fault confirmed.",
                "Schedule planned bearing replacement within 1 week — do not defer beyond current trend.",
                "Immediate: reduce conveyor load by 20% to slow degradation rate.",
                "Increase manual grease inspection to twice-weekly until replacement.",
                "After bearing replacement, re-measure current and vibration to confirm return to baseline.",
            ],
            "parts_likely_needed": ["Drive motor bearing set (6205-2RS or equivalent)", "Grease gun with EP2 grease"],
            "specialist_required": "mechanical",
        },
        repair_summary="Bearing replacement confirmed spalling on outer race. Post-replacement: current -16%, vibration at baseline, temperature normal.",
        technician_id="T-04",
        days_ago_opened=25,
        days_ago_closed=23,
        messages=[
            {"sender": "bot", "sender_name": "fixer.ai", "text": "🔴 HIGH severity escalation: M-03 drive motor bearing fault suspected (86% confidence). Current +18%, vibration trending up, temperature elevated. Assigning to Rohan Mehta (mechanical). Recommended action: kurtosis measurement + planned bearing replacement within 1 week.", "hours_offset": 0},
            {"sender": "technician", "sender_name": "Rohan Mehta", "text": "Kurtosis reading: 5.8 — confirmed bearing fault. Ordering bearings now. Reducing conveyor load as instructed.", "hours_offset": 4},
            {"sender": "technician", "sender_name": "Rohan Mehta", "text": "Bearings replaced. Found significant spalling on outer race — would have been a hard failure within 2 weeks at that rate. Post-repair readings: current 14.3A (baseline), vibration 2.0 mm/s2, temp 54°C. All good.", "hours_offset": 52},
        ],
    ),
    # M-03 — ticket 2: belt slip
    _make_ticket_and_messages(
        machine_id="M-03",
        failure_code="FC-CNV-002",
        symptom="Intermittent belt slip detected — encoder count not matching expected throughput at peak load.",
        diagnosis_json={
            "ranked_diagnoses": [
                {"diagnosis": "Drive belt tension insufficient — worn belt or stretched from load cycles", "confidence": 0.80, "evidence": "Slip occurs only at peak load, not at idle — tension-related, not drive unit electrical fault."}
            ],
            "severity": "medium",
            "confidence": 0.80,
            "repair_steps": [
                "Measure belt tension with tension meter — compare to spec (typically 250–280 Hz frequency method).",
                "If tension below spec: adjust tensioner. If belt shows cracking or glazing: replace belt.",
                "Check drive pulley for wear grooves — if depth > 2mm, replace pulley.",
                "Run at full load and verify encoder count matches expected throughput.",
            ],
            "parts_likely_needed": ["Conveyor drive belt (spec per M-03 nameplate)", "Tension meter"],
            "specialist_required": "mechanical",
        },
        repair_summary="Belt tension was 30% below spec. Adjusted tensioner. Belt surface showed minor glazing — belt replaced. Full load test passed.",
        technician_id="T-01",
        days_ago_opened=10,
        days_ago_closed=10,
        messages=[
            {"sender": "bot", "sender_name": "fixer.ai", "text": "Diagnosis: belt tension insufficient (80% confidence). Slip only under peak load — tension-related, not electrical. Severity: MEDIUM.", "hours_offset": 0},
            {"sender": "technician", "sender_name": "Arjun Sharma", "text": "Belt tension measured at 180 Hz — spec is 265 Hz. Adjusted tensioner and inspected belt surface: glazing visible. Replacing belt.", "hours_offset": 2},
            {"sender": "technician", "sender_name": "Arjun Sharma", "text": "New belt fitted, tension set to 270 Hz. Full load test: encoder count matching expected throughput within 0.1%. Fixed.", "hours_offset": 3},
        ],
    ),
    # M-04 — ticket 1: calibration drift warning
    _make_ticket_and_messages(
        machine_id="M-04",
        failure_code="FC-CAL-001",
        symptom="Calibration deviation drifting — system flagged 0.18 Nm_offset, approaching the 0.25 Nm_offset AS9100 alert threshold.",
        diagnosis_json={
            "ranked_diagnoses": [
                {"diagnosis": "Reference load cell drift — monotonic creep between calibration intervals", "confidence": 0.90, "evidence": "Drift is slow and monotonic — consistent with load cell creep or reference spring relaxation, not impact damage."}
            ],
            "severity": "medium",
            "confidence": 0.90,
            "repair_steps": [
                "Perform immediate re-calibration using NIST-traceable reference weights per ISO 6789:2017 procedure.",
                "Document new calibration certificate with date and operator name.",
                "After recal, check drift rate: if drift > 0.05 Nm per month, schedule load cell inspection.",
                "Log in QMS as a 'trend watch' — if this is the 2nd drift event within 6 months, initiate CAPA.",
            ],
            "parts_likely_needed": ["NIST-traceable reference weight set"],
            "specialist_required": "calibration",
        },
        repair_summary="Recalibrated using NIST reference weights. Post-cal deviation: 0.002 Nm_offset. Certificate issued. Drift rate flagged for monitoring.",
        technician_id="T-03",
        days_ago_opened=35,
        days_ago_closed=35,
        messages=[
            {"sender": "bot", "sender_name": "fixer.ai", "text": "⚠️ Calibration alert: M-04 deviation at 0.18 Nm_offset — approaching AS9100 alert threshold of 0.25 Nm_offset. Assigning to Kavitha Reddy (calibration). Action required before next audit check.", "hours_offset": 0},
            {"sender": "technician", "sender_name": "Kavitha Reddy", "text": "Recalibration complete using NIST reference set. Post-cal reading: 0.002 Nm_offset. Certificate issued (Cal-M04-2026-09-12). Within spec. Will monitor drift rate monthly.", "hours_offset": 2},
        ],
    ),
    # M-04 — ticket 2: near-recurrence drift
    _make_ticket_and_messages(
        machine_id="M-04",
        failure_code="FC-CAL-001",
        symptom="Calibration deviation at 0.22 Nm_offset — this is the second drift event within 2 months. Getting close to the audit threshold again.",
        diagnosis_json={
            "ranked_diagnoses": [
                {"diagnosis": "Accelerated reference load cell creep — 2nd drift event in 2 months suggests load cell fatigue or contamination", "confidence": 0.87, "evidence": "Previous drift took 4 months to reach 0.18 Nm — this event reached 0.22 Nm in 2 months. Accelerated rate confirms the load cell itself needs inspection."}
            ],
            "severity": "high",
            "confidence": 0.87,
            "repair_steps": [
                "Perform immediate recalibration to clear current deviation.",
                "Initiate CAPA in QMS — 2nd drift event within 60 days requires formal investigation.",
                "Schedule load cell inspection and cleaning — check for contamination at force-application point.",
                "Consider shortening calibration interval from 6-monthly to 3-monthly until load cell is confirmed stable.",
                "If drift rate does not improve after cleaning: replace reference load cell.",
            ],
            "parts_likely_needed": ["NIST-traceable reference weight set", "Load cell inspection tools"],
            "specialist_required": "calibration",
        },
        repair_summary="Recalibrated. Load cell inspection found contamination on the seating surface — cleaned. CAPA initiated. Interval changed to 3-monthly.",
        technician_id="T-03",
        days_ago_opened=5,
        days_ago_closed=5,
        messages=[
            {"sender": "bot", "sender_name": "fixer.ai", "text": "🔴 HIGH severity: M-04 calibration drift 0.22 Nm_offset — second event in 60 days (previous: 0.18 Nm 35 days ago). Accelerated drift rate indicates load cell issue, not normal creep. CAPA required. Assigning to Kavitha Reddy.", "hours_offset": 0},
            {"sender": "technician", "sender_name": "Kavitha Reddy", "text": "Recalibrated immediately. Inspecting load cell — found contamination on seating surface (coolant mist ingress from nearby M-02). Cleaned. Post-cal: 0.001 Nm_offset.", "hours_offset": 3},
            {"sender": "technician", "sender_name": "Kavitha Reddy", "text": "CAPA initiated: CAP-2026-0918. Changed cal interval to 3-monthly. Added contamination shield to load cell seating area. Will monitor next 3 cal events.", "hours_offset": 5},
        ],
    ),
]


# ─────────────────────────────────────────────────────────────────────────────
# DB SETUP + SEED
# ─────────────────────────────────────────────────────────────────────────────
async def create_tables(engine):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def seed_db():
    engine = create_async_engine(DATABASE_URL, echo=False)
    await create_tables(engine)

    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # ── Machines ──────────────────────────────────────────────────────────
        for m in MACHINES:
            existing = await session.get(Machine, m["machine_id"])
            if not existing:
                session.add(Machine(**m))
                print(f"  ✓ Machine {m['machine_id']}: {m['name']}")

        # ── Technicians ───────────────────────────────────────────────────────
        for t in TECHNICIANS:
            existing = await session.get(Technician, t["technician_id"])
            if not existing:
                session.add(Technician(**t))
                print(f"  ✓ Technician {t['technician_id']}: {t['name']} ({t['specialty']})")
            else:
                # Update mutable fields (Slack ID may have changed since first seed)
                existing.slack_user_id = t["slack_user_id"]
                existing.name = t["name"]
                existing.specialty = t["specialty"]

        # ── Failure codes ─────────────────────────────────────────────────────
        for fc in FAILURE_CODES:
            existing = await session.get(FailureCode, fc["code"])
            if not existing:
                session.add(FailureCode(**fc))
                print(f"  ✓ Failure code {fc['code']}: {fc['problem'][:50]}...")

        await session.commit()

        # ── Tickets + Messages ────────────────────────────────────────────────
        for ticket_data, messages_data in SYNTHETIC_TICKETS_RAW:
            existing = await session.get(Ticket, ticket_data["ticket_id"])
            if not existing:
                session.add(Ticket(**ticket_data))
                await session.flush()  # Ensure ticket_id is committed before messages
                for msg_data in messages_data:
                    session.add(TicketMessage(**msg_data))
                print(f"  ✓ Ticket {ticket_data['ticket_id'][:8]}... [{ticket_data['machine_id']}] {ticket_data['failure_code']}")

        await session.commit()

    await engine.dispose()
    print("\n✅ Seed complete. Database ready.")


if __name__ == "__main__":
    # Fix Windows console encoding for Unicode output
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    print("fixer.ai — seeding database...")
    asyncio.run(seed_db())
