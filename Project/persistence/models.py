"""The six tables everything the system is later asked to account for is held in."""

import datetime

from sqlalchemy import Boolean, DateTime, Float, Integer, String, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """The declarative base every table inherits from."""


class UserAccount(Base):
    __tablename__ = "user_accounts"

    username: Mapped[str] = mapped_column(String(64), primary_key=True)
    display_name: Mapped[str] = mapped_column(String(128), nullable=False)
    role: Mapped[str] = mapped_column(String(64), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(256), nullable=False)
    password_salt: Mapped[str] = mapped_column(String(128), nullable=False)
    session_token: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=False,
                                                 server_default=func.now())


class AgentRun(Base):
    __tablename__ = "agent_runs"

    run_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    thread_id: Mapped[str] = mapped_column(String(128), nullable=False)
    incident_reference: Mapped[str] = mapped_column(String(32), nullable=False)
    analyst_id: Mapped[str] = mapped_column(String(64), nullable=False)
    analyst_request: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    llm_call_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0,
                                                server_default="0")
    started_at: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=False,
                                                 server_default=func.now())
    finished_at: Mapped[datetime.datetime | None] = mapped_column(DateTime, nullable=True)


class SecurityIncident(Base):
    __tablename__ = "security_incidents"

    assessment_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    run_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    incident_reference: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    incident_id: Mapped[str] = mapped_column(String(32), nullable=False)
    soc_hub: Mapped[str] = mapped_column(String(32), nullable=False)
    analyst_request: Mapped[str] = mapped_column(Text, nullable=False)
    harm_probability: Mapped[float] = mapped_column(Float, nullable=False)
    harm_band: Mapped[str] = mapped_column(String(16), nullable=False)
    attack_type: Mapped[str] = mapped_column(String(64), nullable=False)
    attack_agreement: Mapped[float] = mapped_column(Float, nullable=False)
    applicable_procedures: Mapped[str] = mapped_column(Text, nullable=False)
    earliest_procedure: Mapped[str | None] = mapped_column(String(32), nullable=True)
    earliest_deadline_at: Mapped[str | None] = mapped_column(String(32), nullable=True)
    hours_remaining: Mapped[float | None] = mapped_column(Float, nullable=True)
    effort_needed_hours: Mapped[float] = mapped_column(Float, nullable=False)
    can_file_complete_in_time: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    customer_notice_required: Mapped[bool] = mapped_column(Boolean, nullable=False)
    assessment_plan_text: Mapped[str] = mapped_column(Text, nullable=False)
    assessment_text: Mapped[str] = mapped_column(Text, nullable=False)
    recommended_disposition: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    customer_notice_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    regulator_filing_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    filing_submitted_at: Mapped[str | None] = mapped_column(String(32), nullable=True)
    final_report_due_at: Mapped[str | None] = mapped_column(String(32), nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=False,
                                                 server_default=func.now())


class DpoDecision(Base):
    __tablename__ = "dpo_decisions"

    decision_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    assessment_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    run_id: Mapped[str] = mapped_column(String(64), nullable=False)
    decision: Mapped[str] = mapped_column(String(64), nullable=False)
    decided_by: Mapped[str] = mapped_column(String(128), nullable=False)
    decided_by_role: Mapped[str] = mapped_column(String(64), nullable=False)
    decision_reason: Mapped[str] = mapped_column(Text, nullable=False)
    decided_at: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=False,
                                                 server_default=func.now())


class LlmCall(Base):
    __tablename__ = "llm_calls"

    call_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    agent_name: Mapped[str] = mapped_column(String(64), nullable=False)
    model_name: Mapped[str] = mapped_column(String(128), nullable=False)
    prompt_characters: Mapped[int] = mapped_column(Integer, nullable=False)
    response_characters: Mapped[int] = mapped_column(Integer, nullable=False)
    latency_milliseconds: Mapped[int] = mapped_column(Integer, nullable=False)
    called_at: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=False,
                                                server_default=func.now())


class ChatTurn(Base):
    __tablename__ = "chat_turns"

    turn_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    user_role: Mapped[str] = mapped_column(String(64), nullable=False)
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    question_type: Mapped[str] = mapped_column(String(32), nullable=False)
    incident_reference: Mapped[str | None] = mapped_column(String(32), nullable=True)
    answer_text: Mapped[str] = mapped_column(Text, nullable=False)
    source_documents: Mapped[str] = mapped_column(Text, nullable=False)
    closest_distance: Mapped[float] = mapped_column(Float, nullable=False)
    was_refused: Mapped[bool] = mapped_column(Boolean, nullable=False)
    asked_at: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=False,
                                               server_default=func.now())
