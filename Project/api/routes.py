"""The REST service: the queue, the incident lookups, the workflow, the decision, the chat
and the audit trail, behind a sign-in guard and an access guard."""

import hmac
import secrets
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, FastAPI, Header, HTTPException, Query, Request
from langgraph.types import Command
from sqlalchemy import true

from access.password_security import hash_password
from access.permissions import check_request_permission
from agentic import nodes
from agentic.graph import build_workflow
from api.schemas import (AssessmentRequest, CallBudgetResponse, ChatRequest, ChatResponse,
                         ChatTurnResponse, DecisionRequest, HarmBandFilter,
                         IncidentDetailResponse, IncidentStatusValue, QueueRow,
                         SecurityIncidentResponse, SignedInUserResponse, SignedOutResponse,
                         SignInRequest)
from chat.conversation_memory import recall_conversation
from chat.incident_status_answer import answer_incident_status
from chat.response_assistant import answer_from_documents
from config import config
from knowledge.procedure_reading import read_procedure_deadlines
from persistence import repository
from persistence.database import SessionFactory
from persistence.models import ChatTurn, SecurityIncident, UserAccount
from tools.deadline_tools import rank_incident_queue
from tools.incident_data_tools import fetch_incident_profile

assessment_workflow = build_workflow(config.CHECKPOINT_DATABASE_FILE)
procedure_readings = {code: read_procedure_deadlines(nodes.knowledge_collection, code)
                      for code in config.PROCEDURE_OPTIONS}
ranked_queue = rank_incident_queue(nodes.open_incidents, nodes.harm_model,
                                   nodes.harm_feature_names, procedure_readings)

_DUMMY_SALT = secrets.token_hex(config.PASSWORD_SALT_BYTES)


def _account_for_token(x_session_token):
    if not x_session_token:
        return None
    with SessionFactory() as session:
        return repository.fetch_user_account(session,
                                             UserAccount.session_token == x_session_token)


def authorize_request(request: Request,
                      x_session_token: Annotated[str | None,
                                                 Header(alias=config.SESSION_TOKEN_HEADER)] = None):
    """Who is asking, and whether their role reaches the area of this request."""
    account = _account_for_token(x_session_token)
    if account is None:
        raise HTTPException(status_code=401, detail=config.SIGN_IN_REQUIRED_MESSAGE)
    permission = check_request_permission(account["role"], request.url.path, request.method)
    if not permission["allowed"]:
        raise HTTPException(status_code=403, detail=config.AREA_REFUSED_MESSAGE
                            % (account["role"], permission["area"]))
    return {"username": account["username"], "display_name": account["display_name"],
            "role": account["role"]}


SignedInUser = Annotated[dict, Depends(authorize_request)]

public_router = APIRouter()
guarded_router = APIRouter(dependencies=[Depends(authorize_request)])


@public_router.post("/auth/signin", response_model=SignedInUserResponse)
def sign_in_user(sign_in_request: SignInRequest):
    with SessionFactory() as session:
        account = repository.fetch_user_account(
            session, UserAccount.username == sign_in_request.username)
        salt = account["password_salt"] if account else _DUMMY_SALT
        offered = hash_password(sign_in_request.password, salt)
        stored = account["password_hash"] if account else hash_password(secrets.token_hex(8), salt)
        if account is None or not hmac.compare_digest(offered, stored):
            raise HTTPException(status_code=401, detail=config.SIGN_IN_FAILED_MESSAGE)
        token = secrets.token_urlsafe(config.SESSION_TOKEN_BYTES)
        repository.update_session_token(session, account["username"], token)
    return {"username": account["username"], "display_name": account["display_name"],
            "role": account["role"], "session_token": token,
            "pages": list(config.ROLE_PAGE_ACCESS.get(account["role"], [])),
            "areas": list(config.ROLE_AREA_ACCESS.get(account["role"], []))}


@public_router.post("/auth/signout", response_model=SignedOutResponse)
def sign_out_user(x_session_token: Annotated[str | None,
                                             Header(alias=config.SESSION_TOKEN_HEADER)] = None):
    account = _account_for_token(x_session_token)
    if account is None:
        raise HTTPException(status_code=401, detail=config.SIGN_IN_REQUIRED_MESSAGE)
    with SessionFactory() as session:
        repository.update_session_token(session, account["username"], None)
    return {"username": account["username"], "signed_out": True}


@guarded_router.get("/queue", response_model=list[QueueRow])
def list_incident_queue(harm_band: Annotated[HarmBandFilter, Query()]):
    if harm_band == config.HARM_BAND_ALL:
        return ranked_queue
    return [row for row in ranked_queue if row["harm_band"] == harm_band]


def build_incident_detail(incident_reference):
    profile, notes, campaign, harm, attack = nodes.establish_incident_facts(incident_reference)
    reporting = nodes.establish_reporting_facts(profile, harm, campaign)
    effort = nodes.establish_effort(profile, harm, attack["attack_type"], reporting["deadlines"])
    return {"profile": profile, "note_texts": notes, "campaign_incidents": campaign,
            "harm": harm, "attack": attack, "applicability": reporting["applicability"],
            "duties": reporting["duties"], "deadlines": reporting["deadlines"], "effort": effort}


@guarded_router.get("/queue/{incident_reference}", response_model=IncidentDetailResponse)
def get_incident_detail(incident_reference: str):
    try:
        fetch_incident_profile(nodes.open_incidents, incident_reference)
    except ValueError:
        raise HTTPException(status_code=404,
                            detail=config.INCIDENT_NOT_IN_QUEUE_MESSAGE % incident_reference)
    return build_incident_detail(incident_reference)


def _one_record(assessment_id):
    with SessionFactory() as session:
        records = repository.fetch_incident_records(
            session, SecurityIncident.assessment_id == assessment_id)
    return records[0] if records else None


@guarded_router.post("/assessments", response_model=SecurityIncidentResponse, status_code=201)
def start_incident_assessment(assessment_request: AssessmentRequest,
                              signed_in_user: SignedInUser):
    reference = assessment_request.incident_reference.strip()
    try:
        fetch_incident_profile(nodes.open_incidents, reference)
    except ValueError:
        raise HTTPException(status_code=404,
                            detail=config.INCIDENT_NOT_IN_QUEUE_MESSAGE % reference)
    thread_id = f"{reference}-{uuid.uuid4().hex[:12]}"
    run_config = {"configurable": {"thread_id": thread_id}}
    try:
        assessment_workflow.invoke({
            "incident_reference": reference,
            "analyst_request": assessment_request.analyst_request,
            "analyst_id": signed_in_user["username"],
            "thread_id": thread_id,
            "llm_call_log": [],
        }, run_config)
        state = assessment_workflow.get_state(run_config)
    except Exception as error:  # a model failure, refusal or unreachable service
        raise HTTPException(status_code=502, detail=f"The assessment could not be completed: "
                                                    f"{type(error).__name__}: {error}")
    assessment_id = state.values.get("assessment_id")
    record = _one_record(assessment_id) if assessment_id else None
    if record is None or "request_dpo_decision" not in tuple(state.next):
        raise HTTPException(status_code=502,
                            detail="The assessment did not reach the Data Protection Officer.")
    return record


@guarded_router.get("/incidents", response_model=list[SecurityIncidentResponse])
def list_incidents(status_value: Annotated[list[IncidentStatusValue], Query()]):
    with SessionFactory() as session:
        return repository.fetch_incident_records(session,
                                                 SecurityIncident.status.in_(list(status_value)))


@guarded_router.post("/incidents/{assessment_id}/decision",
                     response_model=SecurityIncidentResponse)
def submit_dpo_decision(assessment_id: str, decision_request: DecisionRequest,
                        signed_in_user: SignedInUser):
    record = _one_record(assessment_id)
    if record is None:
        raise HTTPException(status_code=404, detail=config.ASSESSMENT_NOT_FOUND_MESSAGE)
    if record["status"] != config.INCIDENT_STATUS_PENDING or record["decision"]:
        raise HTTPException(status_code=409, detail=config.ALREADY_DECIDED_MESSAGE)
    decision = {"decision": decision_request.decision,
                "decided_by": signed_in_user["display_name"],
                "decided_by_role": signed_in_user["role"],
                "decision_reason": decision_request.decision_reason}
    run_config = {"configurable": {"thread_id": record["thread_id"]}}
    try:
        assessment_workflow.invoke(Command(resume=decision), run_config)
    except Exception as error:
        raise HTTPException(status_code=502, detail=f"The decision could not be carried out: "
                                                    f"{type(error).__name__}: {error}")
    return _one_record(assessment_id)


@guarded_router.get("/incidents/{assessment_id}/calls", response_model=CallBudgetResponse)
def get_call_budget(assessment_id: str):
    record = _one_record(assessment_id)
    if record is None:
        raise HTTPException(status_code=404, detail=config.ASSESSMENT_NOT_FOUND_MESSAGE)
    with SessionFactory() as session:
        calls = repository.fetch_llm_calls(session, record["run_id"])
    expected = (config.LLM_CALLS_BY_DECISION[record["decision"]] if record["decision"]
                else config.LLM_CALLS_BEFORE_DECISION)
    return {"assessment_id": assessment_id, "run_id": record["run_id"], "call_count": len(calls),
            "expected_call_count": expected,
            "total_latency_milliseconds": sum(call["latency_milliseconds"] for call in calls),
            "calls": calls}


@guarded_router.post("/chat/ask", response_model=ChatResponse)
def ask_response_assistant(chat_request: ChatRequest, signed_in_user: SignedInUser):
    question = chat_request.question.strip()
    with SessionFactory() as session:
        conversation = recall_conversation(session, signed_in_user["username"], question)
        try:
            result = answer_from_documents(nodes.knowledge_collection, question, conversation)
        except Exception as error:
            raise HTTPException(status_code=502, detail=f"The assistant could not answer: "
                                                        f"{type(error).__name__}: {error}")
        repository.insert_llm_call(session, "CHAT-" + signed_in_user["username"],
                                   result["call_record"])
        if result["question_type"] == config.CHAT_TYPE_INCIDENT_STATUS:
            status = answer_incident_status(session, nodes.open_incidents,
                                            signed_in_user["role"], result["incident_reference"])
            result.update(status)
        repository.insert_chat_turn(session, {
            "username": signed_in_user["username"], "user_role": signed_in_user["role"],
            "question_text": question, "question_type": result["question_type"],
            "incident_reference": result["incident_reference"],
            "answer_text": result["answer"],
            "source_documents": ", ".join(result["source_documents"]),
            "closest_distance": float(result["closest_distance"]),
            "was_refused": bool(result["was_refused"])})
    return {"question_type": result["question_type"],
            "incident_reference": result["incident_reference"], "answer": result["answer"],
            "source_documents": result["source_documents"],
            "was_refused": bool(result["was_refused"])}


@guarded_router.get("/chat/turns", response_model=list[ChatTurnResponse])
def list_own_chat_turns(signed_in_user: SignedInUser,
                        turn_limit: Annotated[int, Query(ge=1, le=config.CHAT_AUDIT_MAX_ROWS)]):
    with SessionFactory() as session:
        return repository.fetch_chat_turns(session,
                                           ChatTurn.username == signed_in_user["username"],
                                           turn_limit)


@guarded_router.get("/audit/chat-turns", response_model=list[ChatTurnResponse])
def list_recent_chat_turns(turn_limit: Annotated[int, Query(ge=1,
                                                            le=config.CHAT_AUDIT_MAX_ROWS)]):
    with SessionFactory() as session:
        return repository.fetch_chat_turns(session, true(), turn_limit)


service_application = FastAPI(title=config.API_TITLE)
service_application.include_router(public_router)
service_application.include_router(guarded_router)
