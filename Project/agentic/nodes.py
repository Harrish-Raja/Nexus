"""The ten steps of the workflow. Each node does one thing and returns only the keys it wrote."""

import re
import uuid

from langgraph.types import interrupt

from agentic import agents
from config import config
from data_pipeline.dataset_loader import load_processed_dataset
from knowledge.vector_index import open_vector_index
from modeling.model_registry import load_feature_schema, load_model
from persistence import repository
from persistence.database import SessionFactory
from tools.deadline_tools import (compare_effort_with_deadline, compute_final_report_due,
                                  compute_procedure_deadlines, select_applicable_procedures)
from tools.incident_data_tools import (fetch_campaign_incidents, fetch_incident_notes,
                                       fetch_incident_profile)
from tools.prediction_tools import (build_attack_facts, build_harm_facts,
                                    estimate_containment_effort)
from tools.retrieval_tools import read_customer_steps, read_reporting_duties

harm_model = load_model(config.HARM_MODEL_FILE)
effort_model = load_model(config.EFFORT_MODEL_FILE)
attack_model = load_model(config.ATTACK_MODEL_FILE)
harm_feature_names = load_feature_schema(config.HARM_SCHEMA_FILE)
effort_feature_names = load_feature_schema(config.EFFORT_SCHEMA_FILE)
open_incidents = load_processed_dataset(config.OPEN_INCIDENTS_FILE)
open_incident_notes = load_processed_dataset(config.OPEN_INCIDENT_NOTES_FILE)
knowledge_collection = open_vector_index(config.VECTOR_STORE_DIRECTORY,
                                         config.VECTOR_COLLECTION_NAME)

_IDENTIFIER_IN_NOTE = re.compile(r"\b[A-Za-z]+(?:-[A-Za-z0-9]+)+\b")


def establish_incident_facts(incident_reference):
    """Everything the tools establish about one incident before any agent is asked."""
    profile = fetch_incident_profile(open_incidents, incident_reference)
    notes = fetch_incident_notes(open_incident_notes, incident_reference)
    campaign = fetch_campaign_incidents(open_incidents, profile)
    rows = open_incidents[open_incidents["incident_reference"].astype(str).str.strip()
                          == str(incident_reference).strip()].head(1)
    harm = build_harm_facts(harm_model, harm_feature_names, rows)[0]
    attack = build_attack_facts(attack_model, notes)
    return profile, notes, campaign, harm, attack


def establish_reporting_facts(profile, harm, campaign):
    applicability = select_applicable_procedures(profile, harm["harm_band"], campaign)
    duties = read_reporting_duties(knowledge_collection, applicability["applicable_procedures"],
                                   profile, harm["harm_band"])
    deadlines = compute_procedure_deadlines(profile, duties["procedure_readings"])
    return {"applicability": applicability, "duties": duties, "deadlines": deadlines}


def establish_effort(profile, harm, attack_type, deadlines):
    effort = estimate_containment_effort(effort_model, effort_feature_names, profile, harm,
                                         attack_type)
    effort.update(compare_effort_with_deadline(effort, deadlines))
    return effort


def _record_call(run_id, call_record):
    with SessionFactory() as session:
        repository.insert_llm_call(session, run_id, call_record)


def _as_text(fields):
    return "\n\n".join(f"{label}: {value}" for label, value in fields.items())


def _internal_identifiers(profile):
    reference = str(profile.get("incident_reference"))
    tokens = {str(profile.get(column)) for column in ["incident_id", "assigned_analyst_id",
                                                     "ticket_queue_code", "analyst_shift_code"]
              if profile.get(column)}
    campaign = profile.get(config.CAMPAIGN_COLUMN)
    if campaign and campaign != config.NO_CAMPAIGN_VALUE:
        tokens.add(str(campaign))
        linked = open_incidents[open_incidents[config.CAMPAIGN_COLUMN] == campaign]
        tokens |= set(linked["incident_reference"].astype(str))
    notes = open_incident_notes[open_incident_notes["incident_reference"] == reference]
    tokens |= set(notes["analyst_id"].astype(str))
    for text in notes[config.NOTE_TEXT_COLUMN].astype(str):
        tokens |= {token for token in _IDENTIFIER_IN_NOTE.findall(text)
                   if any(character.isdigit() for character in token)}
    tokens.discard(reference)
    return sorted((token for token in tokens if token and token != "None"), key=len, reverse=True)


def _scrub(text, identifiers):
    for token in identifiers:
        text = text.replace(token, "")
    return re.sub(r"[ \t]{2,}", " ", text)


def load_incident_context_node(state):
    profile, _, campaign, harm, attack = establish_incident_facts(state["incident_reference"])
    run_id = "RUN-" + uuid.uuid4().hex[:12].upper()
    assessment_id = "ASM-" + uuid.uuid4().hex[:12].upper()
    with SessionFactory() as session:
        repository.insert_agent_run(session, {
            "run_id": run_id, "thread_id": state["thread_id"],
            "incident_reference": profile["incident_reference"],
            "analyst_id": state["analyst_id"], "analyst_request": state["analyst_request"],
            "status": config.AGENT_RUN_STATUS_RUNNING, "llm_call_count": 0})
    return {"run_id": run_id, "assessment_id": assessment_id, "incident_profile": profile,
            "campaign_incidents": campaign, "harm_facts": harm, "attack_facts": attack}


def plan_assessment_node(state):
    reply = agents.plan_assessment(state["incident_profile"], state["analyst_request"])
    _record_call(state["run_id"], reply["call_record"])
    return {"assessment_plan": reply["assessment_plan"], "llm_call_log": [reply["call_record"]]}


def assess_harm_node(state):
    reply = agents.assess_harm(state["harm_facts"], state["incident_profile"],
                               state["assessment_plan"])
    _record_call(state["run_id"], reply["call_record"])
    return {"harm_assessment": reply["harm_assessment"], "llm_call_log": [reply["call_record"]]}


def identify_attack_node(state):
    reply = agents.identify_attack(state["attack_facts"], state["campaign_incidents"],
                                   state["incident_profile"], state["harm_assessment"])
    _record_call(state["run_id"], reply["call_record"])
    return {"attack_analysis": reply["attack_analysis"], "llm_call_log": [reply["call_record"]]}


def check_reporting_duties_node(state):
    reporting_facts = establish_reporting_facts(state["incident_profile"], state["harm_facts"],
                                                state["campaign_incidents"])
    reply = agents.advise_on_reporting_duties(reporting_facts, state["harm_facts"],
                                              state["incident_profile"])
    _record_call(state["run_id"], reply["call_record"])
    return {"reporting_facts": reporting_facts, "reporting_advice": reply["reporting_advice"],
            "llm_call_log": [reply["call_record"]]}


def compose_incident_assessment_node(state):
    profile = state["incident_profile"]
    harm = state["harm_facts"]
    attack = state["attack_facts"]
    reporting = state["reporting_facts"]
    effort = establish_effort(profile, harm, attack["attack_type"], reporting["deadlines"])
    reply = agents.write_incident_assessment(profile, state["analyst_request"], harm, effort,
                                             reporting, state["harm_assessment"],
                                             state["attack_analysis"], state["reporting_advice"])
    _record_call(state["run_id"], reply["call_record"])
    written = reply["incident_assessment"]
    earliest = reporting["deadlines"].get("earliest_milestone")
    with SessionFactory() as session:
        repository.insert_security_incident(session, {
            "assessment_id": state["assessment_id"], "run_id": state["run_id"],
            "incident_reference": profile["incident_reference"],
            "incident_id": str(profile.get("incident_id")), "soc_hub": str(profile.get("soc_hub")),
            "analyst_request": state["analyst_request"],
            "harm_probability": harm["harm_probability"], "harm_band": harm["harm_band"],
            "attack_type": attack["attack_type"], "attack_agreement": attack["agreement"],
            "applicable_procedures": ", ".join(
                reporting["applicability"]["applicable_procedures"]),
            "earliest_procedure": earliest["procedure_code"] if earliest else None,
            "earliest_deadline_at": earliest["due_at"] if earliest else None,
            "hours_remaining": effort["hours_remaining"],
            "effort_needed_hours": effort["effort_needed_hours"],
            "can_file_complete_in_time": effort["can_file_complete_in_time"],
            "customer_notice_required": reporting["duties"]["customer_notice_required"],
            "assessment_plan_text": _as_text(state["assessment_plan"]),
            "assessment_text": written["ASSESSMENT"],
            "recommended_disposition": written["RECOMMENDED DISPOSITION"],
            "status": config.INCIDENT_STATUS_PENDING,
        })
    assessment = dict(written)
    assessment["effort"] = effort
    return {"incident_assessment": assessment, "llm_call_log": [reply["call_record"]]}


def request_dpo_decision_node(state):
    with SessionFactory() as session:
        repository.update_agent_run(session, state["run_id"],
                                    config.AGENT_RUN_STATUS_AWAITING_DECISION,
                                    len(state.get("llm_call_log") or []))
    decision = interrupt({"assessment_id": state["assessment_id"]})
    return {"dpo_decision": dict(decision), "customer_notice": {}, "regulator_filing": {},
            "filing_submitted_at": None}


def route_after_decision(state):
    return state["dpo_decision"]["decision"]


def draft_customer_notice_node(state):
    attack_type = state["attack_facts"]["attack_type"]
    steps = read_customer_steps(knowledge_collection, attack_type)
    reply = agents.draft_customer_notice(state["incident_profile"], state["harm_facts"],
                                         attack_type, steps)
    _record_call(state["run_id"], reply["call_record"])
    identifiers = _internal_identifiers(state["incident_profile"])
    notice = {label: _scrub(value, identifiers)
              for label, value in reply["customer_notice"].items()}
    return {"customer_notice": notice, "llm_call_log": [reply["call_record"]]}


def draft_regulator_filing_node(state):
    filing_submitted_at = config.SNAPSHOT_AT_UTC
    reply = agents.draft_regulator_filing(
        state["incident_profile"], state["harm_facts"], state["attack_facts"]["attack_type"],
        state["reporting_facts"], state["incident_assessment"], state["dpo_decision"],
        state.get("customer_notice") or {}, filing_submitted_at)
    _record_call(state["run_id"], reply["call_record"])
    return {"regulator_filing": reply["regulator_filing"],
            "filing_submitted_at": filing_submitted_at, "llm_call_log": [reply["call_record"]]}


def record_incident_outcome_node(state):
    decision = state["dpo_decision"]
    notice = state.get("customer_notice") or {}
    filing = state.get("regulator_filing") or {}
    filed_at = state.get("filing_submitted_at")
    final_report_due = (compute_final_report_due(state["reporting_facts"]["deadlines"], filed_at)
                        if filed_at else None)
    with SessionFactory() as session:
        repository.insert_dpo_decision(session, {
            "assessment_id": state["assessment_id"], "run_id": state["run_id"],
            "decision": decision["decision"], "decided_by": decision["decided_by"],
            "decided_by_role": decision["decided_by_role"],
            "decision_reason": decision["decision_reason"]})
        repository.record_incident_outcome(session, state["assessment_id"], {
            "status": config.INCIDENT_STATUS_BY_DECISION[decision["decision"]],
            "customer_notice_text": _as_text(notice) if notice else None,
            "regulator_filing_text": _as_text(filing) if filing else None,
            "filing_submitted_at": filed_at,
            "final_report_due_at": final_report_due,
        })
        repository.update_agent_run(session, state["run_id"], config.AGENT_RUN_STATUS_COMPLETE,
                                    len(state.get("llm_call_log") or []))
    return {}
