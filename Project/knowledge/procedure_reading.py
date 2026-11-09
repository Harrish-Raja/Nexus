"""Reads a procedure's own rules out of that procedure's own document.

No hour, month, clock start or exemption is supplied by the code: each is read from the
sentences the store returns for the procedure's own document.
"""

import re

from config import config
from knowledge.vector_index import search_documents

_WHITESPACE = re.compile(config.WHITESPACE_RUN_PATTERN)
_MILESTONE = re.compile(config.MILESTONE_STATEMENT_PATTERN)
_FILED_MILESTONE = re.compile(config.FILED_MILESTONE_STATEMENT_PATTERN)
_EXEMPTION = re.compile(config.EXEMPTION_STATEMENT_PATTERN)


def _passages_for(collection, procedure_code, question_template):
    document_name = config.PROCEDURE_DOCUMENT_BY_CODE[procedure_code]
    results = search_documents(collection, [question_template % procedure_code],
                               config.PROCEDURE_RESULT_COUNT, {"$eq": document_name})
    passages = [passage for passage in results[0] if passage["document_name"] == document_name]
    return document_name, passages


def _source_documents(passages):
    return sorted({passage["document_name"] for passage in passages})


def _plain_text(passage):
    return _WHITESPACE.sub(" ", passage["chunk_text"])


def read_procedure_deadlines(collection, procedure_code):
    """Every milestone one procedure states, with its hours and the moment it runs from."""
    document_name, passages = _passages_for(collection, procedure_code,
                                            config.DEADLINE_QUESTION_TEMPLATE)
    milestones, filed_milestones = [], []
    seen, seen_filed = set(), set()
    for passage in passages:
        text = _plain_text(passage)
        for name, hours, phrase in _MILESTONE.findall(text):
            key = (name, int(hours), phrase)
            if key in seen or phrase not in config.CLOCK_START_COLUMN_BY_PHRASE:
                continue
            seen.add(key)
            milestones.append({"milestone": name, "hours": int(hours),
                               "clock_start_phrase": phrase,
                               "clock_start_column": config.CLOCK_START_COLUMN_BY_PHRASE[phrase]})
        for name, months_word, after in _FILED_MILESTONE.findall(text):
            key = (name, months_word, after)
            if key in seen_filed or months_word not in config.MONTHS_BY_WORD:
                continue
            seen_filed.add(key)
            filed_milestones.append({"milestone": name,
                                     "months": int(config.MONTHS_BY_WORD[months_word]),
                                     "after_milestone": after})
    if not milestones:
        raise ValueError(config.PROCEDURE_UNREAD_MESSAGE % (document_name, "its deadlines"))
    return {"milestones": milestones, "filed_milestones": filed_milestones,
            "source_documents": _source_documents(passages), "passages": passages}


def read_customer_notice_exemption(collection, procedure_code):
    """The protection states that excuse telling customers, as the procedure names them."""
    document_name, passages = _passages_for(collection, procedure_code,
                                            config.EXEMPTION_QUESTION_TEMPLATE)
    states = []
    for passage in passages:
        for state in _EXEMPTION.findall(_plain_text(passage)):
            if state not in states:
                states.append(state)
    if not states:
        raise ValueError(config.PROCEDURE_UNREAD_MESSAGE
                         % (document_name, "which protection excuses a customer notice"))
    return {"exempt_protection_states": sorted(states),
            "source_documents": _source_documents(passages), "passages": passages}
