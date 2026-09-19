"""
fixer.ai — Continual Learning Hook
Embeds newly resolved tickets and technician conversations into the machine's isolated Tier 2 collection.
Enables the machine to "remember" previous repairs and learn over time.
"""
import json
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select

from backend.config import DATABASE_URL
from backend.database.models import Ticket, TicketMessage, FailureCode
from backend.rag.chroma_client import get_tier2_collection, get_chroma_client


async def embed_resolved_ticket(
    ticket_id: str,
    client: Optional[object] = None,
    session: Optional[AsyncSession] = None,
) -> bool:
    """
    On ticket resolution (e.g. technician clicks 'Mark Resolved' in Slack or web UI):
    Pulls ticket + messages, formats resolution card, and embeds directly into
    that machine's isolated Tier 2 vector collection.
    """
    should_close_session = False
    if session is None:
        engine = create_async_engine(DATABASE_URL)
        session_factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        db_session = session_factory()
        should_close_session = True
    else:
        db_session = session

    try:
        # Fetch ticket
        res = await db_session.execute(
            select(Ticket, FailureCode)
            .outerjoin(FailureCode, Ticket.failure_code == FailureCode.code)
            .where(Ticket.ticket_id == ticket_id)
        )
        row = res.first()
        if not row:
            print(f"Warning: Ticket {ticket_id} not found for RAG embedding.")
            return False

        ticket, fc = row

        # Fetch messages
        msg_res = await db_session.execute(
            select(TicketMessage)
            .where(TicketMessage.ticket_id == ticket_id)
            .order_by(TicketMessage.timestamp)
        )
        messages = msg_res.scalars().all()

        conv_text = "\n".join([
            f"[{m.sender_name or m.sender}]: {m.text}" for m in messages
        ])

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

        chroma = client or get_chroma_client()
        collection = get_tier2_collection(ticket.machine_id, client=chroma)
        doc_id = f"tier2_{ticket.machine_id.replace('-', '_')}_{ticket.ticket_id}"

        collection.upsert(
            ids=[doc_id],
            documents=[document],
            metadatas=[meta],
        )
        print(f"[OK] Embedded resolved ticket {ticket.ticket_id[:8]} into tier2__{ticket.machine_id.replace('-', '_')}")
        return True

    except Exception as e:
        print(f"Error embedding ticket {ticket_id} into RAG: {e}")
        return False
    finally:
        if should_close_session:
            await db_session.close()


async def verify_machine_memory(
    machine_id: str,
    query_text: str,
    n_results: int = 3,
    client: Optional[object] = None,
) -> dict:
    """
    Diagnostic & verification helper:
    Queries a machine's isolated Tier 2 brain to confirm newly learned tickets
    are immediately retrievable.
    """
    chroma = client or get_chroma_client()
    try:
        col = get_tier2_collection(machine_id, client=chroma)
        res = col.query(
            query_texts=[query_text],
            n_results=n_results,
            include=["documents", "metadatas", "distances"],
        )
        if not res or not res.get("documents") or not res["documents"][0]:
            return {"found": False, "count": 0, "results": []}

        items = []
        for i in range(len(res["documents"][0])):
            doc = res["documents"][0][i]
            meta = res["metadatas"][0][i] if res.get("metadatas") else {}
            dist = res["distances"][0][i] if res.get("distances") else 1.0
            items.append({
                "ticket_id": meta.get("ticket_id"),
                "failure_code": meta.get("failure_code"),
                "distance": round(float(dist), 4),
                "similarity": round(max(0.0, 1.0 - float(dist)), 4) if float(dist) <= 2.0 else 0.0,
                "document_preview": doc[:250] + "..." if len(doc) > 250 else doc,
            })

        return {
            "found": True,
            "machine_id": machine_id,
            "query": query_text,
            "count": len(items),
            "results": items,
        }
    except Exception as e:
        print(f"[continual_learning] verify error for {machine_id}: {e}")
        return {"found": False, "error": str(e), "results": []}

