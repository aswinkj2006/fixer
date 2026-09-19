"""
fixer.ai — Resolver Pipeline Tests
Tests:
1. Speech stub returns per-machine realistic transcripts.
2. Vision stub returns structured defect dicts with required keys.
3. Fusion returns valid diagnosis structure with real RAG context.
4. Decision node correctly triggers escalate vs self_resolve.
5. Full pipeline end-to-end: creates a ticket in DB with correct fields.
6. Pipeline handles missing audio + image gracefully.
7. Decision escalates on critical severity.
8. Decision self-resolves on low severity + high confidence.
"""
import pytest
import asyncio
import json
import uuid
from datetime import datetime, timezone

# Force stub mode for tests
import os
os.environ["LLM_STUB_MODE"] = "true"

from backend.resolver.speech import transcribe_audio, _stub_transcribe
from backend.resolver.vision import analyze_image, _stub_analyze
from backend.resolver.fusion import fuse_and_reason, _build_rag_query
from backend.resolver.decision import decide_action
from backend.resolver.pipeline import run_pipeline, _infer_failure_code, _format_bot_message
from backend.database.models import Technician


# ─────────────────────────────────────────────────────────────────────────────
# FIXTURES
# ─────────────────────────────────────────────────────────────────────────────

class MockSession:
    """Mock AsyncSession for decision node tests."""
    def __init__(self, tech=None):
        self._tech = tech or Technician(
            technician_id="T-01",
            name="Arjun Sharma",
            specialty="mechanical",
            slack_user_id="U0C2LRFUGSX",
        )

    async def execute(self, query):
        return self

    def scalar_one_or_none(self):
        return self._tech


# ─────────────────────────────────────────────────────────────────────────────
# SPEECH TESTS
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_speech_stub_returns_per_machine_transcript():
    for machine_id in ["M-01", "M-02", "M-03", "M-04"]:
        result = await transcribe_audio(b"fake_audio_bytes", "test.wav", machine_id)
        assert isinstance(result, str)
        assert len(result) > 20, f"Transcript for {machine_id} too short"

    m01 = await transcribe_audio(b"x", "test.wav", "M-01")
    m03 = await transcribe_audio(b"x", "test.wav", "M-03")
    assert m01 != m03, "Different machines should get different transcripts"


@pytest.mark.asyncio
async def test_speech_stub_no_audio_returns_symptom_text():
    # When no audio_bytes, pipeline uses symptom_text directly — test stub function
    result = _stub_transcribe("M-02")
    assert "spindle" in result.lower() or "whine" in result.lower()


# ─────────────────────────────────────────────────────────────────────────────
# VISION TESTS
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_vision_stub_returns_required_keys():
    required_keys = {"component", "observed_defect", "severity_estimate", "maintenance_indicators", "stub_mode"}
    for machine_id in ["M-01", "M-02", "M-03", "M-04"]:
        result = await analyze_image(b"fake_image_bytes", "test.jpg", machine_id)
        missing = required_keys - set(result.keys())
        assert not missing, f"Missing keys for {machine_id}: {missing}"
        assert result["stub_mode"] is True
        assert result["severity_estimate"] in {"none", "minor", "moderate", "severe"}


@pytest.mark.asyncio
async def test_vision_no_image_returns_none_severity():
    result = await analyze_image(b"", "test.jpg", "M-01")
    assert result["severity_estimate"] == "none"
    assert "No image" in result["observed_defect"]


@pytest.mark.asyncio
async def test_vision_stub_distinct_per_machine():
    m01 = await analyze_image(b"x", "x.jpg", "M-01")
    m03 = await analyze_image(b"x", "x.jpg", "M-03")
    # Different machines should report different components
    assert m01["component"] != m03["component"]
    # M-03 should be more severe (motor bearing thermal runaway)
    assert m03["severity_estimate"] == "severe"
    assert m01["severity_estimate"] == "moderate"


# ─────────────────────────────────────────────────────────────────────────────
# FUSION TESTS
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_fusion_returns_valid_diagnosis_structure():
    required_top_keys = {"ranked_diagnoses", "repair_steps", "severity", "confidence", "parts_likely_needed", "specialist_required"}
    for machine_id in ["M-01", "M-02", "M-03", "M-04"]:
        result = await fuse_and_reason(
            machine_id=machine_id,
            transcript="grinding noise near the main bearing, running hot",
            vision_summary={"observed_defect": "metallic residue on flange", "component": "bearing housing", "severity_estimate": "moderate", "maintenance_indicators": "grease leak"},
            sensor_snapshot={"vibration": 4.2, "temperature": 78.5},
        )
        missing = required_top_keys - set(result.keys())
        assert not missing, f"Missing keys for {machine_id}: {missing}"
        assert isinstance(result["ranked_diagnoses"], list)
        assert len(result["ranked_diagnoses"]) >= 1
        assert 0.0 <= result["confidence"] <= 1.0
        assert result["severity"] in {"low", "medium", "high", "critical"}
        assert isinstance(result["repair_steps"], list)
        assert len(result["repair_steps"]) >= 2


@pytest.mark.asyncio
async def test_fusion_includes_rag_context_metadata():
    result = await fuse_and_reason(
        machine_id="M-01",
        transcript="bearing noise",
        vision_summary={"observed_defect": "no image", "severity_estimate": "none", "component": "", "maintenance_indicators": ""},
        sensor_snapshot={},
    )
    assert "rag_context_used" in result
    rag = result["rag_context_used"]
    assert "manual_chunks_retrieved" in rag
    assert "past_tickets_retrieved" in rag
    # Since we have real Chroma data, should have > 0 manual chunks
    assert rag["manual_chunks_retrieved"] > 0


@pytest.mark.asyncio
async def test_fusion_m04_returns_calibration_specialist():
    result = await fuse_and_reason(
        machine_id="M-04",
        transcript="calibration drift off spec",
        vision_summary={"observed_defect": "connector corrosion", "severity_estimate": "minor", "component": "transducer", "maintenance_indicators": ""},
        sensor_snapshot={"calibration_dev": 0.18},
    )
    assert result["specialist_required"] == "calibration"


def test_rag_query_builder_combines_sources():
    query = _build_rag_query(
        "grinding noise near J2 joint",
        {"observed_defect": "metallic grease contamination", "component": "J2 reducer"},
    )
    assert "grinding" in query
    assert "metallic" in query or "J2" in query


# ─────────────────────────────────────────────────────────────────────────────
# DECISION NODE TESTS
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_decision_escalates_on_critical():
    diagnosis = {
        "severity": "critical",
        "confidence": 0.85,
        "specialist_required": "mechanical",
        "ranked_diagnoses": [{"diagnosis": "bearing collapse"}],
    }
    db = MockSession()
    result = await decide_action(diagnosis, "M-03", db)
    assert result["action"] == "escalate"
    assert result["slack_alert"] is True
    assert result["assigned_technician"] is not None


@pytest.mark.asyncio
async def test_decision_escalates_on_high():
    diagnosis = {"severity": "high", "confidence": 0.80, "specialist_required": "mechanical", "ranked_diagnoses": [{}]}
    db = MockSession()
    result = await decide_action(diagnosis, "M-01", db)
    assert result["action"] == "escalate"


@pytest.mark.asyncio
async def test_decision_self_resolves_on_low_medium():
    for severity in ["low", "medium"]:
        diagnosis = {"severity": severity, "confidence": 0.85, "specialist_required": "general", "ranked_diagnoses": [{}]}
        db = MockSession()
        result = await decide_action(diagnosis, "M-01", db)
        assert result["action"] == "self_resolve"
        assert result["slack_alert"] is False


@pytest.mark.asyncio
async def test_decision_escalates_on_low_confidence():
    # Even low severity escalates if confidence < 50%
    diagnosis = {"severity": "low", "confidence": 0.35, "specialist_required": "general", "ranked_diagnoses": [{}]}
    db = MockSession()
    result = await decide_action(diagnosis, "M-01", db)
    assert result["action"] == "escalate"


@pytest.mark.asyncio
async def test_decision_returns_technician():
    diagnosis = {"severity": "high", "confidence": 0.82, "specialist_required": "mechanical", "ranked_diagnoses": [{}]}
    db = MockSession()
    result = await decide_action(diagnosis, "M-01", db)
    tech = result["assigned_technician"]
    assert tech is not None
    assert "name" in tech
    assert "slack_user_id" in tech


# ─────────────────────────────────────────────────────────────────────────────
# PIPELINE END-TO-END TESTS
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_pipeline_creates_ticket_in_db():
    """Full pipeline run verifies a real ticket is written to SQLite."""
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy import select
    from backend.config import DATABASE_URL
    from backend.database.models import Ticket, TicketMessage

    engine = create_async_engine(DATABASE_URL)
    session_factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as db:
        result = await run_pipeline(
            machine_id="M-01",
            db=db,
            symptom_text="Grinding noise near J2 joint, running hotter than normal.",
            audio_bytes=None,
            image_bytes=None,
        )

    assert "ticket_id" in result
    assert result["machine_id"] == "M-01"
    assert "diagnosis" in result
    assert "decision" in result

    # Verify the ticket was actually written to DB
    async with session_factory() as db:
        ticket_res = await db.execute(
            select(Ticket).where(Ticket.ticket_id == result["ticket_id"])
        )
        ticket = ticket_res.scalar_one_or_none()
        assert ticket is not None, "Ticket not found in DB after pipeline run"
        assert ticket.machine_id == "M-01"
        assert ticket.severity in {"low", "medium", "high", "critical"}
        assert ticket.status in {"open", "escalated"}

        # Verify initial bot message was written
        msg_res = await db.execute(
            select(TicketMessage).where(TicketMessage.ticket_id == result["ticket_id"])
        )
        messages = msg_res.scalars().all()
        assert len(messages) >= 1
        assert messages[0].sender == "bot"

    await engine.dispose()


@pytest.mark.asyncio
async def test_pipeline_with_image_and_audio():
    """Pipeline handles binary image + audio bytes without crashing."""
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker
    from backend.config import DATABASE_URL

    engine = create_async_engine(DATABASE_URL)
    session_factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as db:
        result = await run_pipeline(
            machine_id="M-03",
            db=db,
            symptom_text="Motor very hot",
            audio_bytes=b"\x00\xFF\x00" * 100,  # fake audio bytes
            audio_filename="voice.wav",
            image_bytes=b"\xFF\xD8\xFF" * 100,   # fake JPEG header bytes
            image_filename="bearing.jpg",
        )

    assert result["machine_id"] == "M-03"
    assert isinstance(result["transcript"], str) and len(result["transcript"]) > 0
    assert isinstance(result["vision_summary"], dict)
    diag = result["diagnosis"]
    assert diag["severity"] in {"low", "medium", "high", "critical"}

    await engine.dispose()


def test_failure_code_inference():
    """Verify failure code mapping for key terms."""
    m01_diag = {"ranked_diagnoses": [{"diagnosis": "harmonic drive torque escalation"}]}
    assert _infer_failure_code("M-01", m01_diag) == "FC-ROB-001"

    m02_diag = {"ranked_diagnoses": [{"diagnosis": "spindle bearing vibration high"}]}
    assert _infer_failure_code("M-02", m02_diag) == "FC-CNC-001"

    m03_diag = {"ranked_diagnoses": [{"diagnosis": "drive motor bearing thermal runaway"}]}
    assert _infer_failure_code("M-03", m03_diag) == "FC-CNV-001"

    m04_diag = {"ranked_diagnoses": [{"diagnosis": "calibration transducer drift"}]}
    assert _infer_failure_code("M-04", m04_diag) == "FC-CAL-001"


def test_format_bot_message_structure():
    """Verify the bot message contains required fields."""
    diagnosis = {
        "ranked_diagnoses": [{"diagnosis": "Bearing failure", "confidence": 0.85, "evidence": "Heat + vibration"}],
        "repair_steps": ["Step 1", "Step 2", "Step 3"],
        "severity": "high",
        "confidence": 0.85,
        "parts_likely_needed": ["Bearing SKF 6208"],
        "manual_reference": "Test Manual §2.1",
        "rag_context_used": {"manual_chunks_retrieved": 4, "past_tickets_retrieved": 2},
    }
    decision = {
        "action": "escalate",
        "assigned_technician": {"name": "Arjun Sharma", "slack_user_id": "U123"},
    }
    msg = _format_bot_message(diagnosis, decision)
    assert "Bearing failure" in msg
    assert "HIGH" in msg
    assert "Arjun Sharma" in msg
    assert "Step 1" in msg
    assert "4 manual excerpts" in msg
