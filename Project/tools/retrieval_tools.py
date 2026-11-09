"""The document lookups the workflow needs."""

from config import config
from knowledge.procedure_reading import read_customer_notice_exemption, read_procedure_deadlines
from knowledge.vector_index import search_documents


def _add_passages(collected, seen, passages):
    for passage in passages:
        if passage["chunk_id"] not in seen:
            seen.add(passage["chunk_id"])
            collected.append(passage)


def read_reporting_duties(collection, applicable_procedures, incident_profile, harm_band):
    """Read every applicable procedure from its own document, and settle the customer notice."""
    readings, passages, seen = {}, [], set()
    for code in applicable_procedures:
        readings[code] = read_procedure_deadlines(collection, code)
        _add_passages(passages, seen, readings[code]["passages"])

    exempt_states = []
    notice_code = config.PROCEDURE_EU_PERSONAL_DATA_BREACH
    if notice_code in applicable_procedures:
        exemption = read_customer_notice_exemption(collection, notice_code)
        exempt_states = list(exemption["exempt_protection_states"])
        _add_passages(passages, seen, exemption["passages"])

    protection = incident_profile.get("data_protection_state")
    customer_notice_required = bool(notice_code in applicable_procedures
                                    and harm_band in config.CUSTOMER_NOTICE_HARM_BANDS
                                    and protection not in exempt_states)
    return {"procedure_readings": readings, "exempt_protection_states": exempt_states,
            "customer_notice_required": customer_notice_required, "passages": passages}


def read_customer_steps(collection, attack_type):
    """What this attack type's own playbook tells affected customers to do."""
    playbook = config.PLAYBOOK_DOCUMENT_BY_ATTACK_TYPE[attack_type]
    results = search_documents(collection, [config.CUSTOMER_STEPS_QUESTION_TEMPLATE % attack_type],
                               config.PLAYBOOK_RESULT_COUNT, {"$eq": playbook})
    return [passage for passage in results[0] if passage["document_name"] == playbook]
