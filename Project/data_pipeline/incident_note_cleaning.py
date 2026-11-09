"""The whole cleaning run for the analyst notes."""

import re

import numpy as np
import pandas as pd

from config import config
from data_pipeline import common_cleaning as cleaning
from data_pipeline.dataset_loader import load_raw_dataset, save_processed_dataset

_MARKUP = re.compile(config.MARKUP_PATTERN)
_WHITESPACE = re.compile(config.WHITESPACE_RUN_PATTERN)

# What each escaped artefact stands for once it is written as a plain character.
_ARTEFACT_MEANING = {"&nbsp;": " ", "&amp;": "&", "&lt;": "<", "&gt;": ">", "&quot;": '"',
                     "&#39;": "'", "\xa0": " "}


def _own_mapping(valid_values):
    return {value.lower(): value for value in valid_values}


NOTE_CATEGORY_VOCABULARY = {
    config.NOTE_TARGET_COLUMN: (config.ATTACK_TYPE_MAPPING, config.VALID_ATTACK_TYPES),
    "soc_hub": (config.HUB_MAPPING, config.VALID_HUBS),
    "analyst_grade": (config.ANALYST_GRADE_MAPPING, config.VALID_ANALYST_GRADES),
    "affected_system_class": (config.SYSTEM_CLASS_MAPPING, config.VALID_SYSTEM_CLASSES),
    "note_source": (_own_mapping(config.VALID_NOTE_SOURCES), config.VALID_NOTE_SOURCES),
    "initial_severity": (_own_mapping(config.VALID_SEVERITIES), config.VALID_SEVERITIES),
}


def repair_note_text(text):
    """Strip markup and escaped characters, quiet a shouted note and tidy its whitespace."""
    if not isinstance(text, str):
        return text
    repaired = text
    for _ in range(3):
        before = repaired
        for artefact in config.ENCODING_ARTIFACT_LIST:
            repaired = repaired.replace(artefact, _ARTEFACT_MEANING.get(artefact, " "))
        if repaired == before:
            break
    repaired = _MARKUP.sub(" ", repaired)
    repaired = _WHITESPACE.sub(" ", repaired).strip()
    letters = [character for character in repaired if character.isalpha()]
    if letters and all(character.isupper() for character in letters):
        repaired = repaired.lower()
    return repaired


def clean_incident_note_dataset(input_file_path, output_file_path):
    """Turn the raw notes into the cleaned table the attack model learns from."""
    frame = load_raw_dataset(input_file_path, config.NULL_TOKEN_LIST)
    frame = cleaning.strip_text_whitespace(frame)
    frame = cleaning.replace_missing_tokens(frame, config.NULL_TOKEN_LIST)

    frame[config.NOTE_TEXT_COLUMN] = frame[config.NOTE_TEXT_COLUMN].astype(object).map(
        repair_note_text)
    frame[config.NOTE_TEXT_COLUMN] = frame[config.NOTE_TEXT_COLUMN].map(
        lambda value: value if isinstance(value, str) and value else np.nan)
    frame[config.NOTE_LENGTH_COLUMN] = frame[config.NOTE_TEXT_COLUMN].map(
        lambda value: len(value) if isinstance(value, str) else np.nan)

    for column_name, (mapping, valid_values) in NOTE_CATEGORY_VOCABULARY.items():
        frame = cleaning.normalize_category_column(frame, column_name, mapping)
        frame = cleaning.restrict_to_known_values(frame, column_name, valid_values)

    word_counts = frame[config.NOTE_TEXT_COLUMN].map(
        lambda value: len(value.split()) if isinstance(value, str) else 0)
    frame = frame[word_counts >= config.MINIMUM_NOTE_WORDS].reset_index(drop=True)
    frame = cleaning.remove_rows_missing_target(frame, config.NOTE_TARGET_COLUMN)
    frame = cleaning.remove_duplicate_records(frame)

    frame = cleaning.parse_mixed_format_timestamps(frame, config.NOTE_TIMESTAMP_COLUMNS)
    for column_name in config.NOTE_TIMESTAMP_COLUMNS:
        column = frame[column_name]
        if column.isna().any() and column.notna().any():
            frame[column_name] = column.fillna(column.median())
    frame = cleaning.format_timestamps_as_text(frame, config.NOTE_TIMESTAMP_COLUMNS)

    frame = cleaning.convert_text_to_numeric(frame, config.NOTE_NUMERIC_COLUMNS)
    frame = cleaning.remove_out_of_range_measurements(frame, config.NOTE_RANGE_LIMITS)
    frame = cleaning.resolve_missing_measurements(frame, config.NOTE_NUMERIC_COLUMNS)
    frame[config.NOTE_LENGTH_COLUMN] = frame[config.NOTE_TEXT_COLUMN].str.len().astype(int)
    frame["note_sequence"] = pd.to_numeric(frame["note_sequence"]).round().astype(int)

    frame = cleaning.resolve_missing_categories(frame, config.NOTE_CATEGORY_COLUMNS)
    remaining_text = [name for name in frame.columns
                      if name not in config.NOTE_NUMERIC_COLUMNS
                      and name not in config.NOTE_TIMESTAMP_COLUMNS]
    frame = cleaning.resolve_missing_categories(frame, remaining_text)
    frame = frame.reset_index(drop=True)

    save_processed_dataset(frame, output_file_path)
    return frame
