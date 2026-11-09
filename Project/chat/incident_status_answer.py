"""Answers a question about one named incident from the record, as the asker's role allows.

No language model is called here: every word comes from the record or from config.
"""

from config import config
from persistence.models import SecurityIncident
from persistence.repository import fetch_incident_records


def _refusal():
    return {"answer": config.CHAT_INCIDENT_REFUSAL_MESSAGE, "source_documents": [],
            "was_refused": True}


def _in_queue(open_incidents, incident_reference):
    if not incident_reference:
        return False
    references = set(open_incidents["incident_reference"].astype(str).str.strip())
    return str(incident_reference).strip() in references


def _staff_answer(record):
    lines = [f"{record['incident_reference']} - latest assessment {record['assessment_id']}, "
             f"status {record['status']}.",
             f"Harm probability {record['harm_probability']} ({record['harm_band']} band). "
             f"Attack type {record['attack_type']}, named by "
             f"{round(float(record['attack_agreement']) * 100)}% of the notes.",
             f"Procedures that apply: {record['applicable_procedures'] or 'none'}."]
    if record["earliest_procedure"]:
        lines.append(f"Earliest deadline: {record['earliest_procedure']}, due "
                     f"{record['earliest_deadline_at']}, {record['hours_remaining']} hours from "
                     f"the snapshot.")
    else:
        lines.append("No reporting clock is running.")
    fits = record["can_file_complete_in_time"]
    lines.append(f"Effort needed {record['effort_needed_hours']} hours; "
                 + ("it fits before the deadline." if fits is True
                    else "it does not fit before the deadline." if fits is False
                    else "there is no running deadline to fit it into."))
    lines.append("Customers must be told." if record["customer_notice_required"]
                 else "Customers need not be told.")
    lines.append(f"Recommended: {record['recommended_disposition']}.")
    if record.get("decision"):
        lines.append(f"Decided: {record['decision']} by {record['decided_by']} "
                     f"({record['decided_by_role']}): {record['decision_reason']}")
    if record.get("filing_submitted_at"):
        lines.append(f"Filed at {record['filing_submitted_at']}"
                     + (f"; final report due {record['final_report_due_at']}."
                        if record.get("final_report_due_at") else "."))
    return " ".join(lines)


def answer_incident_status(session, open_incidents, role_name, incident_reference):
    """Staff are answered from the record; anyone else only from a published notice."""
    records = []
    if incident_reference:
        records = fetch_incident_records(
            session, SecurityIncident.incident_reference == str(incident_reference).strip())

    if role_name not in config.CHAT_INCIDENT_STATUS_ROLES:
        disclosed = [record for record in records
                     if record["status"] in config.CHAT_DISCLOSED_INCIDENT_STATUSES
                     and record.get("customer_notice_text")]
        if not disclosed or not _in_queue(open_incidents, incident_reference):
            return _refusal()
        record = disclosed[0]
        sent_at = record.get("filing_submitted_at") or str(record.get("decided_at"))
        return {"answer": config.CHAT_PUBLISHED_NOTICE_TEMPLATE
                % (record["incident_reference"], sent_at, record["customer_notice_text"]),
                "source_documents": [config.CHAT_PUBLISHED_NOTICE_SOURCE_TEMPLATE
                                     % record["incident_reference"]],
                "was_refused": False}

    if not _in_queue(open_incidents, incident_reference):
        return {"answer": config.CHAT_UNKNOWN_INCIDENT_MESSAGE, "source_documents": [],
                "was_refused": False}
    if not records:
        return {"answer": config.CHAT_NOT_ASSESSED_TEMPLATE % str(incident_reference).strip(),
                "source_documents": [], "was_refused": False}
    record = records[0]
    return {"answer": _staff_answer(record),
            "source_documents": [f"Assessment {record['assessment_id']}"],
            "was_refused": False}
