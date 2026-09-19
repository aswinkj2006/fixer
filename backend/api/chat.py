"""
fixer.ai — Chat/Resolver API
POST /chat/{machine_id}

Accepts: multipart/form-data with optional image + audio + text symptom.
Returns: full diagnosis card with ticket_id, repair steps, decision, and RAG context used.

All LLM calls inside the pipeline are marked # LLM-STUB — flip LLM_STUB_MODE=false
and ensure Ollama is running to enable real inference on capable hardware.
"""
from typing import Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException

from backend.config import LLM_STUB_MODE

router = APIRouter()


@router.post("/chat/{machine_id}")
async def run_resolver(
    machine_id: str,
    symptom_text: str = Form(default=""),
    image: Optional[UploadFile] = File(default=None),
    image_file: Optional[UploadFile] = File(default=None),
    audio: Optional[UploadFile] = File(default=None),
    audio_file: Optional[UploadFile] = File(default=None),
):
    """
    Multimodal resolver agent entry point.

    In LLM_STUB_MODE=true:
      - Transcription and vision return deterministic per-machine stubs.
      - Fusion reasoning returns RAG-enriched stub diagnosis (real Chroma retrieval runs).
      - Decision node logic is REAL (evaluates severity/confidence for escalation).

    In LLM_STUB_MODE=false:
      - Full local Ollama pipeline runs (whisper.cpp, Gemma 3 4B, Phi-4-mini).
    """
    from backend.main import AsyncSessionLocal
    from backend.resolver.pipeline import run_pipeline

    # Validate machine ID
    valid_machines = {"M-01", "M-02", "M-03", "M-04"}
    if machine_id not in valid_machines:
        raise HTTPException(
            status_code=404,
            detail=f"Machine '{machine_id}' not found. Valid: {sorted(valid_machines)}"
        )

    # Read uploaded file bytes
    effective_audio = audio or audio_file
    audio_bytes = None
    audio_filename = "input.wav"
    if effective_audio and effective_audio.filename:
        audio_bytes = await effective_audio.read()
        audio_filename = effective_audio.filename

    effective_image = image or image_file
    image_bytes = None
    image_filename = "image.jpg"
    if effective_image and effective_image.filename:
        image_bytes = await effective_image.read()
        image_filename = effective_image.filename

    async with AsyncSessionLocal() as db:
        result = await run_pipeline(
            machine_id=machine_id,
            db=db,
            symptom_text=symptom_text,
            audio_bytes=audio_bytes,
            audio_filename=audio_filename,
            image_bytes=image_bytes,
            image_filename=image_filename,
        )

    return result
