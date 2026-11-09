"""Cuts the documents into sections at their numbered headings, then into passages."""

import os
import re

from config import config

_HEADING = re.compile(config.SECTION_HEADING_PATTERN)
_HEADER = re.compile(config.DOCUMENT_HEADER_PATTERN)
_WHITESPACE = re.compile(config.WHITESPACE_RUN_PATTERN)
_SENTENCE_BOUNDARY = re.compile(config.SENTENCE_BOUNDARY_PATTERN)


def _section_starts(text):
    """Positions of numbered headings whose numbers run 1, 2, 3 ... in sequence."""
    starts = []
    expected = 1
    for match in _HEADING.finditer(text):
        if int(match.group(1)) == expected:
            starts.append(match.start(1))
            expected += 1
    return starts


def split_documents_into_sections(document_entries):
    """Divide each document at its own numbered section headings."""
    sections = []
    for entry in document_entries:
        text = _HEADER.sub(" ", entry["document_text"])
        text = _WHITESPACE.sub(" ", text).strip()
        starts = _section_starts(text)
        if not starts:
            boundaries = [0, len(text)]
        else:
            boundaries = [0] + starts[1:] + [len(text)]
        for position in range(len(boundaries) - 1):
            section_text = text[boundaries[position]:boundaries[position + 1]].strip()
            if section_text:
                sections.append({"document_name": entry["document_name"],
                                 "section_text": section_text})
    return sections


def _sentences(text):
    return [piece.strip() for piece in _SENTENCE_BOUNDARY.split(text) if piece.strip()]


def _overlap_tail(sentences, chunk_overlap):
    """The trailing sentences of a passage that make up about chunk_overlap characters."""
    tail = []
    length = 0
    for sentence in reversed(sentences[1:]):
        if tail and length + len(sentence) + 1 > chunk_overlap:
            break
        tail.insert(0, sentence)
        length += len(sentence) + 1
        if length >= chunk_overlap:
            break
    return tail


def build_chunk_records(section_entries, chunk_size, chunk_overlap):
    """Cut each section into passages of whole sentences that overlap their neighbours."""
    records = []
    section_number_by_document = {}
    for entry in section_entries:
        document_name = entry["document_name"]
        section_number = section_number_by_document.get(document_name, 0) + 1
        section_number_by_document[document_name] = section_number
        stem = os.path.splitext(document_name)[0]

        sentences = _sentences(entry["section_text"])
        passages = []
        current = []
        current_length = 0
        fresh = 0
        for sentence in sentences:
            if current and fresh > 0 and current_length + 1 + len(sentence) > chunk_size:
                passages.append(" ".join(current))
                current = _overlap_tail(current, chunk_overlap)
                current_length = len(" ".join(current))
                fresh = 0
            current.append(sentence)
            current_length = len(" ".join(current))
            fresh += 1
        if current and (fresh > 0 or not passages):
            passages.append(" ".join(current))

        for chunk_number, passage in enumerate(passages, start=1):
            records.append({
                "chunk_id": f"{stem}-s{section_number:03d}-c{chunk_number:03d}",
                "chunk_text": passage,
                "document_name": document_name,
            })
    return records
