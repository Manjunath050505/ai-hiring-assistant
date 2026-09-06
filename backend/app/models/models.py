import enum
import uuid
from datetime import datetime, timezone
from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.session import Base

def now(): return datetime.now(timezone.utc)

class InterviewStatus(str, enum.Enum):
    CREATED="CREATED"; PUBLISHED="PUBLISHED"; CANDIDATE_STARTED="CANDIDATE_STARTED"; CALL_REQUESTED="CALL_REQUESTED"; INITIATED="INITIATED"; RINGING="RINGING"; IN_PROGRESS="IN_PROGRESS"; COMPLETED="COMPLETED"; NOT_CONNECTED="NOT_CONNECTED"; FAILED="FAILED"; CANCELLED="CANCELLED"

class Job(Base):
    __tablename__="jobs"
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    company_name: Mapped[str] = mapped_column(String(200), default="Demo Company")
    description: Mapped[str] = mapped_column(Text)
    skills: Mapped[str] = mapped_column(Text, default="")
    experience_level: Mapped[str] = mapped_column(String(100), default="Fresher")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, onupdate=now)
    interviews = relationship("Interview", back_populates="job")

class Interview(Base):
    __tablename__="interviews"
    id: Mapped[int] = mapped_column(primary_key=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("jobs.id"))
    public_token: Mapped[str] = mapped_column(String(80), unique=True, index=True, default=lambda: uuid.uuid4().hex + uuid.uuid4().hex)
    hunar_agent_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    hunar_call_id: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    request_id: Mapped[str] = mapped_column(String(100), unique=True, index=True, default=lambda: str(uuid.uuid4()))
    status: Mapped[InterviewStatus] = mapped_column(Enum(InterviewStatus), default=InterviewStatus.CREATED, index=True)
    language: Mapped[str] = mapped_column(String(30), default="ENGLISH")
    voice_persona: Mapped[str] = mapped_column(String(30), default="NEHA")
    interview_prompt: Mapped[str] = mapped_column(Text)
    criteria: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    recording_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    result_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    overall_score: Mapped[float | None] = mapped_column(nullable=True)
    recommendation: Mapped[str | None] = mapped_column(String(30), nullable=True)
    job = relationship("Job", back_populates="interviews")
    candidates = relationship("InterviewCandidate", back_populates="interview")

class Candidate(Base):
    __tablename__="candidates"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    phone_number: Mapped[str] = mapped_column(String(30), index=True)
    email: Mapped[str | None] = mapped_column(String(320), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    interviews = relationship("InterviewCandidate", back_populates="candidate")

class InterviewCandidate(Base):
    __tablename__="interview_candidates"
    id: Mapped[int] = mapped_column(primary_key=True)
    interview_id: Mapped[int] = mapped_column(ForeignKey("interviews.id"), index=True)
    candidate_id: Mapped[int] = mapped_column(ForeignKey("candidates.id"), index=True)
    consent: Mapped[bool] = mapped_column(Boolean, default=False)
    status: Mapped[str] = mapped_column(String(40), default="ACTIVE")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    __table_args__=(UniqueConstraint("interview_id", "candidate_id", name="uq_interview_candidate"),)
    interview = relationship("Interview", back_populates="candidates")
    candidate = relationship("Candidate", back_populates="interviews")

class WebhookEvent(Base):
    __tablename__="webhook_events"
    id: Mapped[int] = mapped_column(primary_key=True)
    event_type: Mapped[str] = mapped_column(String(100), index=True)
    call_id: Mapped[str | None] = mapped_column(String(100), index=True, nullable=True)
    request_id: Mapped[str | None] = mapped_column(String(100), index=True, nullable=True)
    payload: Mapped[dict] = mapped_column(JSON)
    processed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
