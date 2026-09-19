"""
fixer.ai — RAG Ingestion Pipeline
Handles chunking and embedding for:
- Tier 1: Shared equipment manuals per machine model
- Tier 2: Isolated ticket resolution history per machine instance
"""
import asyncio
import json
import re
from pathlib import Path
from typing import Optional

try:
    import pymupdf  # PyMuPDF
except ImportError:
    pymupdf = None

from backend.config import MANUALS_DIR
from backend.rag.chroma_client import (
    get_tier1_collection,
    get_tier2_collection,
    get_chroma_client,
)

# Mapping of manual files to machine model slugs
MANUAL_MODEL_MAP = {
    "fanuc_arcmate100id_maintenance.md": "fanuc_arcmate100id",
    "fanuc_hrp1_mechanical_unit_manual.pdf": "fanuc_arcmate100id",
    "fanuc_lr_mate_200id_manual.pdf": "fanuc_arcmate100id",
    "fanuc_am120ic_migatronic.pdf": "fanuc_arcmate100id",
    "haas_vf2_maintenance.md": "haas_vf2",
    "conveyor_drive_motor_maintenance.md": "generic_conveyor",
    "torque_calibration_station_iso6789.md": "calibration_station",
}

# Keywords to filter high-value maintenance/troubleshooting pages from large PDFs
HIGH_VALUE_KEYWORDS = [
    "alarm", "error", "troubleshoot", "maintenance", "grease", "lubricat",
    "torque", "harmonic", "bearing", "servo", "motor", "brake", "replace",
    "inspection", "srvo", "vibration", "specification", "calibration"
]


def chunk_text(text: str, chunk_size: int = 700, overlap: int = 100) -> list[str]:
    """
    Splits text into overlapping chunks, attempting to break on paragraphs or sentences.
    """
    cleaned = text.strip()
    if not cleaned:
        return []
    
    if len(cleaned) <= chunk_size:
        return [cleaned]

    chunks = []
    start = 0
    while start < len(cleaned):
        end = start + chunk_size
        if end >= len(cleaned):
            chunks.append(cleaned[start:].strip())
            break
        
        # Try to break on double newline (paragraph)
        break_pos = cleaned.rfind("\n\n", start, end)
        if break_pos == -1 or break_pos < start + (chunk_size // 2):
            # Try single newline
            break_pos = cleaned.rfind("\n", start, end)
        if break_pos == -1 or break_pos < start + (chunk_size // 2):
            # Try period
            break_pos = cleaned.rfind(". ", start, end)
            if break_pos != -1:
                break_pos += 1  # include period

        if break_pos == -1 or break_pos <= start:
            break_pos = end

        chunk = cleaned[start:break_pos].strip()
        if chunk:
            chunks.append(chunk)
        start = max(start + 1, break_pos - overlap)

    return chunks


def extract_pdf_chunks(pdf_path: Path, max_pages: int = 40) -> list[tuple[str, dict]]:
    """
    Extracts text chunks from PDF, prioritizing pages with maintenance/alarm keywords.
    Returns list of (chunk_text, metadata_dict).
    """
    if pymupdf is None:
        return []

    doc_chunks = []
    try:
        doc = pymupdf.open(str(pdf_path))
        extracted_pages = 0

        for page_idx in range(len(doc)):
            if extracted_pages >= max_pages:
                break

            page = doc[page_idx]
            page_text = page.get_text("text").strip()
            if len(page_text) < 80:
                continue

            # Prioritize pages with maintenance/troubleshooting content
            text_lower = page_text.lower()
            is_high_value = any(kw in text_lower for kw in HIGH_VALUE_KEYWORDS)
            
            # If doc is small (<30 pages), take all; if large, only take high-value pages
            if len(doc) > 30 and not is_high_value:
                continue

            extracted_pages += 1
            chunks = chunk_text(page_text, chunk_size=700, overlap=100)
            for c_idx, c in enumerate(chunks):
                meta = {
                    "source": pdf_path.name,
                    "page": page_idx + 1,
                    "chunk_index": c_idx,
                    "is_troubleshooting": is_high_value,
                }
                doc_chunks.append((c, meta))

        doc.close()
    except Exception as e:
        print(f"  Warning: PDF extraction failed for {pdf_path.name}: {e}")

    return doc_chunks


def extract_markdown_chunks(md_path: Path) -> list[tuple[str, dict]]:
    """
    Extracts section-aware chunks from markdown manuals.
    """
    content = md_path.read_text(encoding="utf-8")
    sections = re.split(r'\n(?=#{1,3}\s)', content)
    
    results = []
    for s_idx, sec in enumerate(sections):
        sec = sec.strip()
        if not sec:
            continue
        
        # Extract title from header line
        lines = sec.split("\n", 1)
        header = lines[0].replace("#", "").strip() if lines else "General"
        
        chunks = chunk_text(sec, chunk_size=750, overlap=100)
        for c_idx, c in enumerate(chunks):
            meta = {
                "source": md_path.name,
                "section": header,
                "section_index": s_idx,
                "chunk_index": c_idx,
            }
            results.append((c, meta))

    return results


def ingest_all_tier1_manuals() -> dict[str, int]:
    """
    Ingests all manuals from data/manuals/ into their respective Tier 1 collections.
    Returns counts per model slug.
    """
    counts: dict[str, int] = {}
    client = get_chroma_client()

    print("\n[Tier 1 Ingestion] Processing equipment manuals...")
    for filename, model_slug in MANUAL_MODEL_MAP.items():
        file_path = MANUALS_DIR / filename
        if not file_path.exists():
            continue

        print(f"  Ingesting {filename} -> tier1__{model_slug}...")
        collection = get_tier1_collection(model_slug, client=client)

        if file_path.suffix.lower() == ".pdf":
            chunks_with_meta = extract_pdf_chunks(file_path)
        else:
            chunks_with_meta = extract_markdown_chunks(file_path)

        if not chunks_with_meta:
            continue

        # Prepare batch for Chroma
        ids = []
        documents = []
        metadatas = []

        file_stem = file_path.stem.replace("-", "_").replace(".", "_")
        for i, (text, meta) in enumerate(chunks_with_meta):
            chunk_id = f"tier1_{model_slug}_{file_stem}_{i}"
            meta["model_slug"] = model_slug
            meta["tier"] = "1"
            ids.append(chunk_id)
            documents.append(text)
            # Chroma metadata values must be str, int, float, or bool
            metadatas.append({k: (str(v) if not isinstance(v, (int, float, bool)) else v) for k, v in meta.items()})

        # Upsert in batches of 50
        batch_size = 50
        for b_start in range(0, len(ids), batch_size):
            b_end = b_start + batch_size
            collection.upsert(
                ids=ids[b_start:b_end],
                documents=documents[b_start:b_end],
                metadatas=metadatas[b_start:b_end],
            )

        counts[model_slug] = counts.get(model_slug, 0) + len(ids)
        print(f"    ✓ Stored {len(ids)} chunks from {filename}")

    return counts


async def ingest_tier2_historical_tickets() -> dict[str, int]:
    """
    Ingests all resolved tickets from SQLite database into isolated Tier 2 collections:
    tier2__M_01, tier2__M_02, tier2__M_03, tier2__M_04.
    """
    from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy import select
    from backend.config import DATABASE_URL
    from backend.database.models import Ticket, TicketMessage

    engine = create_async_engine(DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    counts: dict[str, int] = {}
    client = get_chroma_client()

    print("\n[Tier 2 Ingestion] Ingesting resolved historical tickets into isolated collections...")
    async with async_session() as session:
        from backend.database.models import FailureCode
        result = await session.execute(
            select(Ticket, FailureCode)
            .outerjoin(FailureCode, Ticket.failure_code == FailureCode.code)
            .where(Ticket.status == "resolved")
        )
        rows = result.all()

        for ticket, fc in rows:
            # Fetch message thread for this ticket
            msg_res = await session.execute(
                select(TicketMessage)
                .where(TicketMessage.ticket_id == ticket.ticket_id)
                .order_by(TicketMessage.timestamp)
            )
            messages = msg_res.scalars().all()

            conv_text = "\n".join([
                f"[{m.sender_name or m.sender}]: {m.text}" for m in messages
            ])

            # Extract details from diagnosis JSON if present
            diag_details = ""
            parts_needed = ""
            if ticket.diagnosis:
                try:
                    d_obj = json.loads(ticket.diagnosis)
                    if "ranked_diagnoses" in d_obj and d_obj["ranked_diagnoses"]:
                        diag_details = d_obj["ranked_diagnoses"][0].get("diagnosis", "")
                    if "parts_likely_needed" in d_obj:
                        parts_needed = ", ".join(d_obj["parts_likely_needed"])
                except Exception:
                    diag_details = str(ticket.diagnosis)

            problem_desc = fc.problem if fc else (ticket.symptom_text or "")
            cause_desc = fc.cause if fc else "N/A"
            remedy_desc = fc.remedy if fc else (ticket.resolution_summary or "")

            # Structured representation for semantic retrieval
            document = f"""Ticket ID: {ticket.ticket_id}
Machine: {ticket.machine_id}
Failure Code: {ticket.failure_code or 'N/A'}
Problem: {problem_desc}
Symptom: {ticket.symptom_text or ''}
Root Cause: {cause_desc}
Remedy / Corrective Action: {remedy_desc}
AI Diagnosis: {diag_details}
Parts Used: {parts_needed or 'Standard shop consumables'}
Resolution Summary: {ticket.resolution_summary or 'Resolved successfully'}

Conversation History:
{conv_text}
""".strip()

            meta = {
                "tier": "2",
                "machine_id": ticket.machine_id,
                "ticket_id": ticket.ticket_id,
                "failure_code": str(ticket.failure_code or ""),
                "technician_id": str(ticket.assigned_technician_id or ""),
                "status": str(ticket.status),
                "severity": str(ticket.severity or ""),
                "confidence": float(ticket.confidence or 0.0),
            }

            collection = get_tier2_collection(ticket.machine_id, client=client)
            doc_id = f"tier2_{ticket.machine_id.replace('-', '_')}_{ticket.ticket_id}"

            collection.upsert(
                ids=[doc_id],
                documents=[document],
                metadatas=[meta],
            )
            counts[ticket.machine_id] = counts.get(ticket.machine_id, 0) + 1
            print(f"  ✓ Ingested ticket {ticket.ticket_id[:8]} -> tier2__{ticket.machine_id.replace('-', '_')} ({ticket.failure_code})")

    await engine.dispose()
    return counts


def run_full_ingestion() -> dict:
    """Executes both Tier 1 and Tier 2 ingestion pipelines synchronously."""
    t1_counts = ingest_all_tier1_manuals()
    t2_counts = asyncio.run(ingest_tier2_historical_tickets())
    return {"tier1": t1_counts, "tier2": t2_counts}
