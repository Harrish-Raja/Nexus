"""Answers one question from the documents the chat may read, in exactly one model call."""

import re

from agentic.agents import call_language_model, parse_labelled_response
from config import config
from knowledge.vector_index import search_documents

_REFERENCE = re.compile(config.INCIDENT_REFERENCE_PATTERN)
_LABELS = ["QUESTION TYPE", "INCIDENT REFERENCE", "ANSWER"]


def _read_type(text):
    cleaned = " ".join(re.sub(r"[^A-Za-z]+", " ", str(text)).upper().split())
    for option in sorted(config.CHAT_TYPE_OPTIONS, key=len, reverse=True):
        if cleaned == option or cleaned.startswith(option + " "):
            return option
    raise ValueError(f"Agent {config.AGENT_NAME_RESPONSE_ASSISTANT} classified the question as "
                     f"{text!r}, which is not one of {config.CHAT_TYPE_OPTIONS}.")


def answer_from_documents(collection, question_text, conversation):
    """Search twice, ask the model once, and give the answer only if it is grounded."""
    exclusion = {"$nin": list(config.CHAT_EXCLUDED_DOCUMENTS)}
    results = search_documents(collection, [question_text, conversation["search_text"]],
                               config.RETRIEVAL_RESULT_COUNT, exclusion)
    nearest = {}
    for passages in results:
        for passage in passages:
            held = nearest.get(passage["chunk_id"])
            if held is None or passage["distance"] < held["distance"]:
                nearest[passage["chunk_id"]] = passage
    passages = sorted(nearest.values(), key=lambda passage: passage["distance"])
    closest = passages[0]["distance"] if passages else 1.0

    numbered = "\n\n".join(f"[{position}] ({passage['document_name']}) {passage['chunk_text']}"
                           for position, passage in enumerate(passages, start=1))
    prompt = (f"You are {config.ORGANISATION_NAME}'s response assistant. Answer the question only "
              "from the passages below, which come from Merrowfield's own procedures, policies, "
              "standards and playbooks. Never use general knowledge. Never state a deadline the "
              "passages do not state, and never apply one procedure's deadline to another.\n"
              f"Classify the question as exactly one of: {'; '.join(config.CHAT_TYPE_OPTIONS)}.\n"
              f"- {config.CHAT_TYPE_INCIDENT_STATUS}: the question asks about one named incident "
              "(a reference like INC-BLR-0041927). Do not answer it; write 'See the record.' "
              "as the ANSWER.\n"
              f"- {config.CHAT_TYPE_OUT_OF_SCOPE}: the passages do not answer the question.\n"
              "INCIDENT REFERENCE is the incident reference named in the question, or NONE.\n\n"
              f"The conversation so far:\n{conversation['history_text']}\n\n"
              f"Passages:\n{numbered or '(none)'}\n\n"
              f"Question: {question_text}\n\n"
              "Reply in exactly this layout, each label at the start of its own line:\n"
              "QUESTION TYPE: ...\nINCIDENT REFERENCE: ...\nANSWER: ...")
    reply = call_language_model(prompt, config.AGENT_NAME_RESPONSE_ASSISTANT)
    fields = parse_labelled_response(reply["response_text"], _LABELS,
                                     config.AGENT_NAME_RESPONSE_ASSISTANT)
    question_type = _read_type(fields["QUESTION TYPE"])

    named = _REFERENCE.search(fields["INCIDENT REFERENCE"]) or _REFERENCE.search(question_text)
    reference = named.group(0) if named else None
    if _REFERENCE.search(question_text):
        question_type = config.CHAT_TYPE_INCIDENT_STATUS

    base = {"incident_reference": None, "closest_distance": float(closest),
            "call_record": reply["call_record"]}
    if question_type == config.CHAT_TYPE_INCIDENT_STATUS:
        return dict(base, question_type=question_type, incident_reference=reference,
                    answer="", source_documents=[], was_refused=False)
    if (question_type in config.CHAT_ANSWERED_TYPES
            and closest <= config.CHAT_MAX_RELEVANCE_DISTANCE):
        sources = []
        for passage in passages:
            if passage["document_name"] not in sources:
                sources.append(passage["document_name"])
        return dict(base, question_type=question_type, answer=fields["ANSWER"],
                    source_documents=sources, was_refused=False)
    return dict(base, question_type=config.CHAT_TYPE_OUT_OF_SCOPE,
                answer=config.CHAT_REFUSAL_MESSAGE, source_documents=[], was_refused=True)
