"""The shape of every request the service accepts and every reply it returns."""

import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field

from config import config

HarmBandFilter = Literal[tuple(config.HARM_BAND_OPTIONS + [config.HARM_BAND_ALL])]
IncidentStatusValue = Literal[tuple(config.INCIDENT_STATUS_OPTIONS)]
DecisionValue = Literal[tuple(config.DECISION_OPTIONS)]


class SignInRequest(BaseModel):
    username: str
    password: str


class SignedInUserResponse(BaseModel):
    username: str
    display_name: str
    role: str
    session_token: str
    pages: list[str]
    areas: list[str]


class SignedOutResponse(BaseModel):
    username: str
    signed_out: bool


class QueueRow(BaseModel):
    incident_reference: str
    soc_hub: str
    harm_probability: float
    harm_band: str
    applicable_procedures: list[str]
    significant_only_with_campaign: bool
    awareness_established: bool
    earliest_milestone: Optional[dict]


class IncidentDetailResponse(BaseModel):
    profile: dict
    note_texts: list[str]
    campaign_incidents: list[dict]
    harm: dict
    attack: dict
    applicability: dict
    duties: dict
    deadlines: dict
    effort: dict


class AssessmentRequest(BaseModel):
    incident_reference: str
    analyst_request: str = Field(min_length=config.ANALYST_REQUEST_MINIMUM_CHARACTERS)


class DecisionRequest(BaseModel):
    decision: DecisionValue
    decision_reason: str = Field(min_length=config.DECISION_REASON_MINIMUM_CHARACTERS)


class SecurityIncidentResponse(BaseModel):
    assessment_id: str
    run_id: str
    incident_reference: str
    incident_id: str
    soc_hub: str
    analyst_request: str
    harm_probability: float
    harm_band: str
    attack_type: str
    attack_agreement: float
    applicable_procedures: str
    earliest_procedure: Optional[str]
    earliest_deadline_at: Optional[str]
    hours_remaining: Optional[float]
    effort_needed_hours: float
    can_file_complete_in_time: Optional[bool]
    customer_notice_required: bool
    assessment_plan_text: str
    assessment_text: str
    recommended_disposition: str
    status: str
    customer_notice_text: Optional[str]
    regulator_filing_text: Optional[str]
    filing_submitted_at: Optional[str]
    final_report_due_at: Optional[str]
    created_at: datetime.datetime
    llm_call_count: int
    decision: Optional[str]
    decided_by: Optional[str]
    decided_by_role: Optional[str]
    decision_reason: Optional[str]
    decided_at: Optional[datetime.datetime]


class CallBudgetResponse(BaseModel):
    assessment_id: str
    run_id: str
    call_count: int
    expected_call_count: int
    total_latency_milliseconds: int
    calls: list[dict]


class ChatRequest(BaseModel):
    question: str = Field(min_length=config.CHAT_QUESTION_MINIMUM_CHARACTERS)


class ChatResponse(BaseModel):
    question_type: str
    incident_reference: Optional[str]
    answer: str
    source_documents: list[str]
    was_refused: bool


class ChatTurnResponse(BaseModel):
    turn_id: int
    username: str
    user_role: str
    question_text: str
    question_type: str
    incident_reference: Optional[str]
    answer_text: str
    source_documents: str
    closest_distance: float
    was_refused: bool
    asked_at: datetime.datetime
