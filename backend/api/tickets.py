"""fixer.ai — Tickets API (stub for Day 1 — expanded on Day 3/4)"""
from fastapi import APIRouter, HTTPException
from sqlalchemy import select
from backend.database.models import Ticket, TicketMessage

router = APIRouter()


@router.get("/tickets/{ticket_id}")
async def get_ticket(ticket_id: str):
    from backend.main import AsyncSessionLocal
    async with AsyncSessionLocal() as db:
        ticket = await db.get(Ticket, ticket_id)
        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket not found")

        result = await db.execute(
            select(TicketMessage)
            .where(TicketMessage.ticket_id == ticket_id)
            .order_by(TicketMessage.timestamp)
        )
        messages = result.scalars().all()

        return {
            "ticket": {
                "ticket_id": ticket.ticket_id,
                "machine_id": ticket.machine_id,
                "opened_at": ticket.opened_at,
                "closed_at": ticket.closed_at,
                "status": ticket.status,
                "severity": ticket.severity,
                "symptom_text": ticket.symptom_text,
                "diagnosis": ticket.diagnosis,
                "confidence": ticket.confidence,
                "failure_code": ticket.failure_code,
                "assigned_technician_id": ticket.assigned_technician_id,
                "resolution_summary": ticket.resolution_summary,
            },
            "messages": [
                {
                    "id": m.id,
                    "sender": m.sender,
                    "sender_name": m.sender_name,
                    "text": m.text,
                    "timestamp": m.timestamp,
                }
                for m in messages
            ],
        }


@router.get("/machines/{machine_id}/tickets")
async def get_machine_tickets(machine_id: str, status: str = None, limit: int = 50):
    from backend.main import AsyncSessionLocal
    async with AsyncSessionLocal() as db:
        query = select(Ticket).where(Ticket.machine_id == machine_id)
        if status:
            query = query.where(Ticket.status == status)
        query = query.order_by(Ticket.opened_at.desc()).limit(limit)
        result = await db.execute(query)
        tickets = result.scalars().all()

        return [
            {
                "ticket_id": t.ticket_id,
                "opened_at": t.opened_at,
                "closed_at": t.closed_at,
                "status": t.status,
                "severity": t.severity,
                "symptom_text": t.symptom_text,
                "failure_code": t.failure_code,
                "confidence": t.confidence,
                "assigned_technician_id": t.assigned_technician_id,
            }
            for t in tickets
        ]


from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone
from backend.rag.continual_learning import embed_resolved_ticket


class ResolveTicketRequest(BaseModel):
    resolution_summary: str
    remedy: Optional[str] = None
    technician_notes: Optional[str] = None
    technician_id: Optional[str] = None


@router.post("/tickets/{ticket_id}/resolve")
async def resolve_ticket(ticket_id: str, payload: ResolveTicketRequest):
    """
    Mark a ticket resolved (from UI or Slack 'Mark Resolved' button).
    Updates DB status, logs resolution notes, and triggers the continual learning loop
    to embed the resolution into that machine's Tier 2 collection.
    """
    from backend.main import AsyncSessionLocal
    async with AsyncSessionLocal() as db:
        ticket = await db.get(Ticket, ticket_id)
        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket not found")

        now_iso = datetime.now(timezone.utc).isoformat()
        ticket.status = "resolved"
        ticket.closed_at = now_iso
        ticket.resolution_summary = payload.resolution_summary

        if payload.technician_id:
            ticket.assigned_technician_id = payload.technician_id

        # Log technician closing message if provided
        if payload.technician_notes:
            msg = TicketMessage(
                ticket_id=ticket.ticket_id,
                machine_id=ticket.machine_id,
                sender="technician",
                sender_name=payload.technician_id or "Technician",
                text=payload.technician_notes,
                timestamp=now_iso,
            )
            db.add(msg)

        await db.commit()
        await db.refresh(ticket)

        # Trigger continual learning embedding into that machine's Tier 2 brain
        cl_success = await embed_resolved_ticket(ticket_id=ticket.ticket_id, session=db)

        return {
            "success": True,
            "ticket_id": ticket.ticket_id,
            "machine_id": ticket.machine_id,
            "status": ticket.status,
            "closed_at": ticket.closed_at,
            "resolution_summary": ticket.resolution_summary,
            "continual_learning_embedded": cl_success,
        }

