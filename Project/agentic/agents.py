"""The language model client, the reply parser and the seven agent prompts.

Every agent is handed facts that the models, the documents and the rules have already
established, and is asked only for prose in a fixed layout of labelled fields.
"""

import json
import os
import re
import time

from dotenv import load_dotenv
from google import genai
from google.genai import errors as genai_errors
from google.genai import types

from config import config

load_dotenv()

_GENERATION_CONFIG = types.GenerateContentConfig(
    max_output_tokens=config.GEMINI_MAX_OUTPUT_TOKENS,
    temperature=config.GEMINI_TEMPERATURE,
    automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
)

_NO_RECALCULATION = ("Every figure below was established by Merrowfield's models, documents and "
                     "rules. Do not recalculate, round differently or change any figure, band, "
                     "deadline or time; quote them as given.")

_TRANSIENT_STATUS = {429, 500, 502, 503, 504}


def _facts(value):
    return json.dumps(value, indent=2, default=str, ensure_ascii=False)


def call_language_model(prompt_text, agent_name):
    """One language model call, returning the reply and what the call cost."""
    api_key = os.environ.get(config.GEMINI_API_KEY_VARIABLE, "").strip().strip('"')
    model_name = os.environ.get(config.GEMINI_MODEL_VARIABLE, "").strip().strip('"')
    if not api_key or not model_name:
        raise ValueError(f"The language model is not configured: set both "
                         f"{config.GEMINI_API_KEY_VARIABLE} and {config.GEMINI_MODEL_VARIABLE} "
                         f"in .env (agent {agent_name}).")
    response = None
    started = time.perf_counter()
    with genai.Client(api_key=api_key) as client:
        for attempt in range(3):
            started = time.perf_counter()
            try:
                response = client.models.generate_content(model=model_name, contents=prompt_text,
                                                          config=_GENERATION_CONFIG)
                break
            except genai_errors.APIError as error:
                if getattr(error, "code", None) in _TRANSIENT_STATUS and attempt < 2:
                    time.sleep(2 * (attempt + 1))
                    continue
                raise
    latency = max(1, int(round((time.perf_counter() - started) * 1000)))
    text = ""
    try:
        text = (response.text or "") if response is not None else ""
    except (ValueError, AttributeError):
        text = ""
    text = text.strip()
    if not text:
        raise ValueError(f"The language model {model_name} returned an empty reply to agent "
                         f"{agent_name}.")
    return {"response_text": text,
            "call_record": {"agent_name": agent_name, "model_name": model_name,
                            "prompt_characters": len(prompt_text),
                            "response_characters": len(text),
                            "latency_milliseconds": latency}}


def parse_labelled_response(response_text, field_labels, agent_name):
    """Read a reply laid out as labelled fields back into one entry per label."""
    decoration = config.RESPONSE_DECORATION_CHARACTERS
    ordered = sorted(field_labels, key=len, reverse=True)
    patterns = [(label, re.compile(r"^" + re.escape(label) + r"[\s*_`~#]*:(.*)$", re.IGNORECASE))
                for label in ordered]
    captured = {}
    current = None
    for line in str(response_text).splitlines():
        candidate = line.lstrip(decoration)
        started = None
        for label, pattern in patterns:
            if label in captured:
                continue
            match = pattern.match(candidate)
            if match:
                started = (label, match.group(1))
                break
        if started:
            current = started[0]
            captured[current] = [started[1]]
        elif current is not None:
            captured[current].append(line)
    result, missing = {}, []
    for label in field_labels:
        value = "\n".join(captured.get(label, [])).strip().strip(decoration).strip()
        if not value:
            missing.append(label)
        result[label] = value
    if missing:
        raise ValueError(f"Agent {agent_name} did not answer {', '.join(missing)}.")
    return result


def _layout(labels):
    return ("Reply in exactly this layout, each label at the start of its own line, followed by "
            "a colon and your text, and nothing else:\n"
            + "\n".join(f"{label}: ..." for label in labels))


def _labels_words(categories):
    return [config.DATA_CATEGORY_LABELS.get(column, column) for column in categories]


def _incident_summary(profile):
    keys = ["incident_reference", "soc_hub", "detection_source", "initial_severity",
            "first_alert_at", "confirmed_at", "confirmation_status", "containment_status",
            "affected_system_class", "hosting_region", "systems_affected_count",
            "internet_facing_flag", "attack_vector", "personal_data_involved_flag",
            "eu_data_subjects_count", "india_data_subjects_count", "customers_affected_count",
            "records_affected_count", "data_protection_state", "mfa_enforced_flag",
            "exfiltration_confirmed_flag", "attacker_still_active_flag",
            "service_outage_minutes", "direct_financial_loss_eur", config.CAMPAIGN_COLUMN,
            "third_party_supplier_involved_flag", "backups_available_flag"]
    return {key: profile.get(key) for key in keys if key in profile}


def plan_assessment(incident_profile, analyst_request):
    labels = ["PRIORITY", "CHECKS", "RATIONALE"]
    prompt = (f"You are the incident intake planner at {config.ORGANISATION_NAME}'s security "
              "operations desk. Decide what has to be established about this incident before "
              "anyone can decide whom to notify. You plan; you settle nothing. Do not state any "
              "deadline, harm band or reporting duty as though it were established - later "
              "agents receive those from Merrowfield's tools.\n\n"
              f"The analyst asked: {analyst_request}\n\n"
              f"The incident's own facts:\n{_facts(_incident_summary(incident_profile))}\n\n"
              "PRIORITY is one line naming what matters most. CHECKS is a short numbered list of "
              "what must be established. RATIONALE is two or three sentences.\n\n"
              + _layout(labels))
    reply = call_language_model(prompt, config.AGENT_NAME_PLANNER)
    plan = parse_labelled_response(reply["response_text"], labels, config.AGENT_NAME_PLANNER)
    return {"assessment_plan": plan, "call_record": reply["call_record"]}


def assess_harm(harm_facts, incident_profile, assessment_plan):
    labels = ["DRIVERS", "PROTECTION", "HARM SUMMARY"]
    facts = {
        "harm_probability": harm_facts["harm_probability"],
        "harm_band": harm_facts["harm_band"],
        "data_categories_involved": _labels_words(harm_facts["data_categories"]),
        "high_impact_categories": _labels_words(harm_facts["high_impact_categories"]),
        "sensitive_categories": _labels_words(harm_facts["sensitive_categories"]),
        "data_protection_state": incident_profile.get("data_protection_state"),
        "exfiltration_confirmed": incident_profile.get("exfiltration_confirmed_flag"),
        "personal_data_involved": incident_profile.get("personal_data_involved_flag"),
        "records_affected": incident_profile.get("records_affected_count"),
        "customers_affected": incident_profile.get("customers_affected_count"),
    }
    prompt = (f"You are the harm analyst for {config.ORGANISATION_NAME}'s Data Protection "
              "Officer. Explain what is driving the harm score, in terms the officer can act on.\n"
              f"{_NO_RECALCULATION} Do not recalculate the probability or the band. Where the "
              "data protection state and the band point in different directions, say so.\n\n"
              f"Established harm facts:\n{_facts(facts)}\n\n"
              f"The planner's plan:\n{_facts(assessment_plan)}\n\n"
              + _layout(labels))
    reply = call_language_model(prompt, config.AGENT_NAME_HARM)
    parsed = parse_labelled_response(reply["response_text"], labels, config.AGENT_NAME_HARM)
    return {"harm_assessment": parsed, "call_record": reply["call_record"]}


def identify_attack(attack_facts, campaign_incidents, incident_profile, harm_assessment):
    labels = ["ATTACK TYPE", "CONFIDENCE", "EVIDENCE"]
    facts = {
        "notes_read": attack_facts["notes_read"],
        "type_each_note_was_called": attack_facts["note_attack_types"],
        "type_most_notes_name": attack_facts["attack_type"],
        "agreement": attack_facts["agreement"],
        "other_types_named": attack_facts["other_attack_types"],
        "attack_vector": incident_profile.get("attack_vector"),
        "affected_system_class": incident_profile.get("affected_system_class"),
        "incidents_in_campaign": len(campaign_incidents),
    }
    prompt = (f"You are the attack analyst at {config.ORGANISATION_NAME}. A classifier read every "
              "analyst note on this incident; say how much weight the attack type the notes name "
              f"deserves. {_NO_RECALCULATION}\nAn agreement below about one half means the notes "
              "do not settle the type: say so plainly rather than presenting it as settled.\n"
              f"ATTACK TYPE must be one of {config.VALID_ATTACK_TYPES}, or the words "
              "'none established'.\n\n"
              f"Established facts:\n{_facts(facts)}\n\n"
              f"What the harm analyst wrote:\n{_facts(harm_assessment)}\n\n"
              + _layout(labels))
    reply = call_language_model(prompt, config.AGENT_NAME_ATTACK)
    parsed = parse_labelled_response(reply["response_text"], labels, config.AGENT_NAME_ATTACK)
    return {"attack_analysis": parsed, "call_record": reply["call_record"]}


def _deadline_lines(deadlines):
    lines = []
    for line in deadlines.get("milestones", []):
        lines.append({key: line.get(key) for key in [
            "procedure_code", "authority", "milestone", "hours", "clock_start_phrase",
            "clock_started", "started_at", "due_at", "due_at_hub_time", "hours_remaining",
            "overdue", "status"]})
    return lines


def _reporting_summary(reporting_facts):
    applicability = reporting_facts.get("applicability", {})
    duties = reporting_facts.get("duties", {})
    deadlines = reporting_facts.get("deadlines", {})
    earliest = deadlines.get("earliest_milestone")
    return {
        "applicable_procedures": [
            {"code": code, "title": config.PROCEDURE_TITLE_BY_CODE.get(code),
             "authority": config.PROCEDURE_AUTHORITY_BY_CODE.get(code),
             "grounds": applicability.get("grounds", {}).get(code)}
            for code in applicability.get("applicable_procedures", [])],
        "customers_across_campaign": applicability.get("customers_across_campaign"),
        "significant_only_with_campaign": applicability.get("significant_only_with_campaign"),
        "milestones": _deadline_lines(deadlines),
        "earliest_milestone": None if not earliest else {
            key: earliest.get(key) for key in ["procedure_code", "milestone", "due_at",
                                               "due_at_hub_time", "hours_remaining", "overdue"]},
        "milestones_counted_from_a_filing": deadlines.get("filed_milestones", []),
        "hub_time_zone": deadlines.get("hub_time_zone"),
        "customer_notice_required": duties.get("customer_notice_required"),
        "protection_states_that_excuse_a_customer_notice": duties.get("exempt_protection_states"),
        "hours_measured_from_snapshot": config.SNAPSHOT_AT_UTC,
    }


def advise_on_reporting_duties(reporting_facts, harm_facts, incident_profile):
    labels = ["AUTHORITIES", "DEADLINES", "CUSTOMER NOTICE"]
    summary = _reporting_summary(reporting_facts)
    campaign_note = ""
    if summary["significant_only_with_campaign"]:
        campaign_note = f"\nNote: {config.CAMPAIGN_SIGNIFICANCE_MESSAGE}.\n"
    passages = "\n\n".join(f"[{passage['document_name']}] {passage['chunk_text']}"
                           for passage in reporting_facts.get("duties", {}).get("passages", []))
    if not summary["applicable_procedures"]:
        campaign_note += f"\n{config.NO_PROCEDURE_APPLIES_MESSAGE}.\n"
    prompt = (f"You are the reporting duty advisor at {config.ORGANISATION_NAME}. State what the "
              "company must do and by when, for every authority that must be told.\n"
              f"{_NO_RECALCULATION} Use only what the passages below say. Never change an hour or "
              "a time, and never apply one procedure's deadline to another.\n"
              f"{campaign_note}\n"
              f"Established reporting facts:\n{_facts(summary)}\n\n"
              f"Harm band: {harm_facts['harm_band']} (probability {harm_facts['harm_probability']}); "
              f"data protection state: {incident_profile.get('data_protection_state')}.\n\n"
              f"Passages from the procedures that apply:\n{passages or '(none)'}\n\n"
              + _layout(labels))
    reply = call_language_model(prompt, config.AGENT_NAME_REPORTING)
    parsed = parse_labelled_response(reply["response_text"], labels, config.AGENT_NAME_REPORTING)
    return {"reporting_advice": parsed, "call_record": reply["call_record"]}


def read_disposition(text, agent_name):
    """The one disposition named in a reply, or a ValueError when none is recognised."""
    cleaned = " ".join(re.sub(r"[^A-Za-z]+", " ", str(text)).upper().split())
    for option in sorted(config.DECISION_OPTIONS, key=len, reverse=True):
        if cleaned == option:
            return option
    for option in sorted(config.DECISION_OPTIONS, key=len, reverse=True):
        if re.search(r"\b" + re.escape(option) + r"\b", cleaned):
            return option
    raise ValueError(f"Agent {agent_name} recommended {text!r}, which is not one of "
                     f"{config.DECISION_OPTIONS}.")


def write_incident_assessment(incident_profile, analyst_request, harm_facts, effort_facts,
                              reporting_facts, harm_assessment, attack_analysis, reporting_advice):
    labels = ["ASSESSMENT", "RECOMMENDED DISPOSITION"]
    effort = {key: effort_facts.get(key) for key in [
        "base_hours", "multiplier_applied", "effort_needed_hours", "containment_starts",
        "out_of_hours_start", "hours_remaining", "hours_available", "can_file_complete_in_time",
        "deadline_message", "planning_assumptions"]}
    prompt = (f"You are the incident writer at {config.ORGANISATION_NAME}. Write the assessment the "
              "Data Protection Officer reads, answering what the analyst actually asked, and "
              "recommend one disposition. You recommend; you do not decide. Nothing is filed "
              f"and no customer is told on your reply.\n{_NO_RECALCULATION}\n\n"
              f"The analyst asked: {analyst_request}\n\n"
              f"Incident facts:\n{_facts(_incident_summary(incident_profile))}\n\n"
              f"Harm facts: probability {harm_facts['harm_probability']}, band "
              f"{harm_facts['harm_band']}, categories {_labels_words(harm_facts['data_categories'])}"
              f"\n\nEffort against the earliest deadline:\n{_facts(effort)}\n\n"
              f"Reporting facts:\n{_facts(_reporting_summary(reporting_facts))}\n\n"
              f"Harm analyst:\n{_facts(harm_assessment)}\n\nAttack analyst:\n"
              f"{_facts(attack_analysis)}\n\nReporting duty advisor:\n{_facts(reporting_advice)}\n\n"
              "ASSESSMENT is one or two paragraphs. RECOMMENDED DISPOSITION is exactly one of: "
              + "; ".join(config.DECISION_OPTIONS) + " - written exactly as shown.\n\n"
              + _layout(labels))
    reply = call_language_model(prompt, config.AGENT_NAME_WRITER)
    parsed = parse_labelled_response(reply["response_text"], labels, config.AGENT_NAME_WRITER)
    parsed["RECOMMENDED DISPOSITION"] = read_disposition(parsed["RECOMMENDED DISPOSITION"],
                                                         config.AGENT_NAME_WRITER)
    return {"incident_assessment": parsed, "call_record": reply["call_record"]}


def draft_customer_notice(incident_profile, harm_facts, attack_type, customer_steps):
    labels = ["SUBJECT", "NOTICE"]
    involved = _labels_words(harm_facts["data_categories"])
    not_involved = [label for column, label in config.DATA_CATEGORY_LABELS.items()
                    if column not in harm_facts["data_categories"]]
    facts = {
        "incident_reference_to_quote": incident_profile.get("incident_reference"),
        "what_happened": attack_type,
        "data_involved": involved,
        "data_not_involved": not_involved,
        "confirmed_taken": incident_profile.get("exfiltration_confirmed_flag"),
        "containment": incident_profile.get("containment_status"),
    }
    steps = "\n\n".join(passage["chunk_text"] for passage in customer_steps)
    prompt = (f"You write customer notices for {config.ORGANISATION_NAME}. Write the notice the "
              "affected customers receive, in plain language with short sentences: what "
              "happened, what data was and was not involved, whether anything is confirmed to "
              "have been taken, where containment stands, and the steps customers should take.\n"
              "The notice must never carry: any internal system name, server or host name, any "
              "ticketing identifier other than the incident reference given, any ticket queue or "
              "shift code, any staff or analyst identifier, any campaign reference or linked "
              "incident, any identifier taken from an analyst's note, any guess about who was "
              "behind it, any promise the investigation has not established, or anything from a "
              "regulator filing. Point customers to the help centre in the app or on the "
              "website; do not invent a contact address or phone number.\n\n"
              f"Facts:\n{_facts(facts)}\n\n"
              f"What the playbook tells affected customers to do:\n{steps or '(none)'}\n\n"
              + _layout(labels))
    reply = call_language_model(prompt, config.AGENT_NAME_CUSTOMER_NOTICE)
    parsed = parse_labelled_response(reply["response_text"], labels,
                                     config.AGENT_NAME_CUSTOMER_NOTICE)
    return {"customer_notice": parsed, "call_record": reply["call_record"]}


def draft_regulator_filing(incident_profile, harm_facts, attack_type, reporting_facts,
                           incident_assessment, dpo_decision, customer_notice, filing_submitted_at):
    labels = ["SUMMARY", "SECTIONS", "CUSTOMERS"]
    summary = _reporting_summary(reporting_facts)
    if customer_notice:
        told = (f"Customers were told: a customer notice was written and sent at "
                f"{filing_submitted_at}, before this filing.")
    else:
        told = ("Customers were not told: the decision taken did not call for a customer notice, "
                f"and the reason recorded is: {dpo_decision.get('decision_reason')}")
    prompt = (f"You draft regulator filings for {config.ORGANISATION_NAME}. Write the filing the "
              "authorities receive.\n" + _NO_RECALCULATION + "\nState every authority owed a "
              "report, when each clock started and from what, when each falls due, and how many "
              f"hours were left at the moment of filing ({filing_submitted_at}). State the "
              "decision, who took it, their role and their reason in their own words.\n\n"
              f"Incident facts:\n{_facts(_incident_summary(incident_profile))}\n\n"
              f"Attack type: {attack_type}. Harm band: {harm_facts['harm_band']} (probability "
              f"{harm_facts['harm_probability']}); data involved: "
              f"{_labels_words(harm_facts['data_categories'])}.\n\n"
              f"Reporting facts:\n{_facts(summary)}\n\n"
              f"The assessment:\n{incident_assessment.get('ASSESSMENT', '')}\n\n"
              f"The decision:\n{_facts(dpo_decision)}\n\n"
              f"Customers: {told}\n\n"
              "SUMMARY is a short paragraph. SECTIONS covers each authority and milestone. "
              "CUSTOMERS says whether customers were told, when, and why.\n\n"
              + _layout(labels))
    reply = call_language_model(prompt, config.AGENT_NAME_REGULATOR_FILING)
    parsed = parse_labelled_response(reply["response_text"], labels,
                                     config.AGENT_NAME_REGULATOR_FILING)
    return {"regulator_filing": parsed, "call_record": reply["call_record"]}
