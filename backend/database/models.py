"""
fixer.ai — SQLAlchemy ORM models
All 6 tables from the data model in IMPLEMENTATION_PLAN.md §3.
Uses SQLAlchemy 2.0 declarative style with async support.
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, Float, Integer, Text, ForeignKey,
    DateTime, Index, JSON
)
from sqlalchemy.orm import DeclarativeBase, relationship


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _uuid() -> str:
    return str(uuid.uuid4())


class Base(DeclarativeBase):
    pass


# ─────────────────────────────────────────────────────────────────────────────
# machines
# ─────────────────────────────────────────────────────────────────────────────
class Machine(Base):
    __tablename__ = "machines"

    machine_id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    model = Column(String, nullable=False)
    # 'robot_arm' | 'cnc_mill' | 'conveyor' | 'calibration_station'
    machine_type = Column(String, nullable=False)
    install_date = Column(String, nullable=False)  # ISO 8601 date
    location = Column(String)
    # JSON: {"vibration": {"mean": 0.8, "std": 0.1, "min": 0.0, "max": 3.0}, ...}
    baseline_ranges = Column(Text, nullable=False, default="{}")

    # Relationships
    sensor_readings = relationship("SensorReading", back_populates="machine")
    tickets = relationship("Ticket", back_populates="machine")


# ─────────────────────────────────────────────────────────────────────────────
# sensor_readings (high-volume time series)
# ─────────────────────────────────────────────────────────────────────────────
class SensorReading(Base):
    __tablename__ = "sensor_readings"
    __table_args__ = (
        Index("idx_sensor_machine_time", "machine_id", "timestamp"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    machine_id = Column(String, ForeignKey("machines.machine_id"), nullable=False)
    timestamp = Column(String, nullable=False)  # ISO 8601 datetime
    # 'torque' | 'vibration' | 'temperature' | 'rpm' | 'current' | 'calibration_dev'
    sensor_type = Column(String, nullable=False)
    value = Column(Float, nullable=False)
    # 'Nm' | 'mm/s2' | 'degC' | 'rpm' | 'A' | 'Nm_offset'
    unit = Column(String, nullable=False)

    machine = relationship("Machine", back_populates="sensor_readings")


# ─────────────────────────────────────────────────────────────────────────────
# technicians
# ─────────────────────────────────────────────────────────────────────────────
class Technician(Base):
    __tablename__ = "technicians"

    technician_id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    # 'mechanical' | 'electrical' | 'calibration'
    specialty = Column(String, nullable=False)
    slack_user_id = Column(String)  # e.g. 'U12345ABC' for @mention

    tickets = relationship("Ticket", back_populates="assigned_technician")


# ─────────────────────────────────────────────────────────────────────────────
# failure_codes — Problem → Cause → Remedy taxonomy
# (ISO 14224 / real CMMS data-governance pattern)
# ─────────────────────────────────────────────────────────────────────────────
class FailureCode(Base):
    __tablename__ = "failure_codes"

    code = Column(String, primary_key=True)  # e.g. 'FC-ROB-001'
    machine_type = Column(String)  # NULL = fleet-wide
    problem = Column(Text, nullable=False)
    cause = Column(Text, nullable=False)
    remedy = Column(Text, nullable=False)

    tickets = relationship("Ticket", back_populates="failure_code_ref")


# ─────────────────────────────────────────────────────────────────────────────
# tickets
# ─────────────────────────────────────────────────────────────────────────────
class Ticket(Base):
    __tablename__ = "tickets"
    __table_args__ = (
        Index("idx_ticket_machine", "machine_id", "status"),
    )

    ticket_id = Column(String, primary_key=True, default=_uuid)
    machine_id = Column(String, ForeignKey("machines.machine_id"), nullable=False)
    opened_at = Column(String, nullable=False)
    closed_at = Column(String)
    symptom_text = Column(Text)
    image_ref = Column(String)       # local file path
    audio_transcript = Column(Text)
    # JSON: {"ranked_diagnoses": [...], "confidence": 0.0–1.0, "severity": "..."}
    diagnosis = Column(Text)
    confidence = Column(Float)
    # 'low' | 'medium' | 'high' | 'critical'
    severity = Column(String)
    # 'open' | 'escalated' | 'resolved'
    status = Column(String, nullable=False, default="open")
    assigned_technician_id = Column(String, ForeignKey("technicians.technician_id"))
    slack_thread_ts = Column(String)
    failure_code = Column(String, ForeignKey("failure_codes.code"))
    resolution_summary = Column(Text)

    machine = relationship("Machine", back_populates="tickets")
    assigned_technician = relationship("Technician", back_populates="tickets")
    failure_code_ref = relationship("FailureCode", back_populates="tickets")
    messages = relationship("TicketMessage", back_populates="ticket")


# ─────────────────────────────────────────────────────────────────────────────
# ticket_messages — mirrored from Slack + local bot/technician conversation
# Gets embedded into Tier 2 RAG on ticket resolution
# ─────────────────────────────────────────────────────────────────────────────
class TicketMessage(Base):
    __tablename__ = "ticket_messages"
    __table_args__ = (
        Index("idx_msg_ticket", "ticket_id", "timestamp"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticket_id = Column(String, ForeignKey("tickets.ticket_id"), nullable=False)
    machine_id = Column(String, nullable=False)  # denormalized for fast per-machine queries
    # 'bot' | 'technician' | 'system'
    sender = Column(String, nullable=False)
    sender_name = Column(String)
    text = Column(Text, nullable=False)
    timestamp = Column(String, nullable=False)
    slack_ts = Column(String)  # null if local-only message

    ticket = relationship("Ticket", back_populates="messages")
