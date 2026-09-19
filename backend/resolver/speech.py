"""
fixer.ai — Speech-to-Text Module
Transcribes audio to text for the resolver agent pipeline.

In LLM_STUB_MODE: returns a realistic stub transcript.
In production: uses whisper.cpp (local, offline, CPU-fast).
"""
import os
from pathlib import Path
from typing import Optional

from backend.config import LLM_STUB_MODE


async def transcribe_audio(
    audio_bytes: bytes,
    filename: str = "input.wav",
    machine_id: Optional[str] = None,
) -> str:
    """
    Transcribes audio content to text.

    Args:
        audio_bytes:  Raw audio bytes from multipart upload.
        filename:     Original filename (used to infer format).
        machine_id:   Passed to stub for contextual mock output.

    Returns:
        Transcribed string. Empty string on failure.
    """
    if LLM_STUB_MODE:
        return _stub_transcribe(machine_id)

    # Production path: whisper.cpp or faster-whisper
    # To enable: pip install faster-whisper and set LLM_STUB_MODE=false
    try:
        return await _whisper_transcribe(audio_bytes, filename)
    except Exception as e:
        print(f"[speech] Transcription failed: {e}. Falling back to empty string.")
        return ""


def _stub_transcribe(machine_id: Optional[str]) -> str:
    """
    # LLM-STUB: Deterministic mock transcription per machine type.
    Replace with real whisper.cpp/faster-whisper call on capable hardware.
    """
    stubs = {
        "M-01": (
            "There's a grinding noise coming from the J2 joint area. "
            "I can feel some extra resistance when I manually move the arm. "
            "It started getting louder over the last two shifts. The arm is also running hotter than usual near that joint."
        ),
        "M-02": (
            "The spindle is making a high-pitched whine, especially at higher RPMs. "
            "Surface finish has gotten worse — you can see chatter marks on the last few parts. "
            "It's worse when the spindle is cold, gets a bit better after 20 minutes warm-up."
        ),
        "M-03": (
            "The motor casing feels really hot to the touch — much hotter than normal. "
            "We're also seeing the conveyor belt slip slightly when the press loads up at the end of the cycle. "
            "Current draw has been higher on the panel meter."
        ),
        "M-04": (
            "The calibration readings have been drifting. "
            "We calibrated it last month but it's already showing a 0.15 Nm offset. "
            "That's close to our AS9100 alert threshold so I need this looked at urgently."
        ),
    }
    return stubs.get(machine_id or "", stubs["M-01"])


async def _whisper_transcribe(audio_bytes: bytes, filename: str) -> str:
    """
    # LLM-STUB → Production: Transcribe using faster-whisper locally.
    Requires: pip install faster-whisper
    Model: tiny.en or base.en for CPU, medium.en for GPU.
    """
    import tempfile
    try:
        from faster_whisper import WhisperModel
        model = WhisperModel("base.en", device="cpu", compute_type="int8")
        with tempfile.NamedTemporaryFile(suffix=Path(filename).suffix or ".wav", delete=False) as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name
        segments, _ = model.transcribe(tmp_path, beam_size=5)
        os.unlink(tmp_path)
        return " ".join(seg.text.strip() for seg in segments)
    except ImportError:
        raise RuntimeError("faster-whisper not installed. Install it on capable hardware.")
