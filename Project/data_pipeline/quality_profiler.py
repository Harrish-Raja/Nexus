"""Measures how dirty each raw extract was, and writes the evidence out."""

import json
import os
import re

import pandas as pd

from config import config
from data_pipeline import common_cleaning as cleaning

_NULL_TOKENS = {str(token).strip().lower() for token in config.NULL_TOKEN_LIST}


def _missing_mask(frame):
    """Cells that are empty or hold one of the ways 'missing' is written."""
    def column_mask(series):
        return series.isna() | series.astype(str).str.strip().str.lower().isin(_NULL_TOKENS)
    return frame.apply(column_mask)


def profile_dataset(raw_frame, clean_frame, target_column, range_limits):
    """The general account of one dataset: what arrived, what survived, what was wrong."""
    missing = _missing_mask(raw_frame)
    missing_by_column = {column: int(count) for column, count in missing.sum().items()
                         if int(count) > 0}

    out_of_range = {}
    for column_name, (lowest, highest) in range_limits.items():
        if column_name not in raw_frame.columns:
            continue
        values = pd.to_numeric(raw_frame[column_name].astype(str).str.strip()
                               .str.replace(config.DIGIT_GROUPING_SEPARATOR, "", regex=False),
                               errors="coerce")
        count = int(((values < lowest) | (values > highest)).sum())
        if count > 0:
            out_of_range[column_name] = count

    rows_received = int(len(raw_frame))
    rows_kept = int(len(clean_frame))
    return {
        "rows_received": rows_received,
        "rows_kept": rows_kept,
        "rows_removed": rows_received - rows_kept,
        "duplicate_rows": int(raw_frame.duplicated().sum()),
        "rows_with_no_answer": int(missing[target_column].sum())
        if target_column in missing.columns else 0,
        "columns": int(clean_frame.shape[1]),
        "missing_cells_by_column": missing_by_column,
        "out_of_range_by_column": out_of_range,
        "missing_cells_after_cleaning": int(clean_frame.isna().sum().sum()),
    }


def _timestamp_notations(raw_frame, timestamp_columns):
    counts = {"iso_utc": 0, "numeric_offset": 0, "named_zone": 0, "epoch_seconds": 0,
              "unreadable": 0}
    epoch = re.compile(config.EPOCH_SECONDS_PATTERN)
    zone = re.compile(config.ZONE_ABBREVIATION_PATTERN)
    offset = re.compile(config.UTC_OFFSET_SUFFIX_PATTERN)
    for column_name in timestamp_columns:
        if column_name not in raw_frame.columns:
            continue
        values = raw_frame[column_name].dropna().astype(str).str.strip()
        values = values[~values.str.lower().isin(_NULL_TOKENS)]
        parsed = cleaning.parse_mixed_format_timestamps(values.to_frame(), [column_name])
        for text, instant in zip(values, parsed[column_name]):
            if pd.isna(instant):
                counts["unreadable"] += 1
            elif epoch.match(text):
                counts["epoch_seconds"] += 1
            elif text.endswith(config.ISO_UTC_SUFFIX):
                counts["iso_utc"] += 1
            elif offset.search(text):
                counts["numeric_offset"] += 1
            elif zone.search(text):
                counts["named_zone"] += 1
            else:
                counts["unreadable"] += 1
    return counts


def _not_plain_numbers(raw_frame, columns):
    result = {}
    for column_name in columns:
        if column_name not in raw_frame.columns:
            continue
        values = raw_frame[column_name].dropna().astype(str).str.strip()
        values = values[~values.str.lower().isin(_NULL_TOKENS)]
        result[column_name] = int(pd.to_numeric(values, errors="coerce").isna().sum())
    return result


def _interval_account(frame):
    working = cleaning.replace_missing_tokens(
        cleaning.strip_text_whitespace(frame[[config.FIRST_ALERT_COLUMN, config.AWARENESS_COLUMN,
                                              config.INCIDENT_INTERVAL_COLUMN]]),
        config.NULL_TOKEN_LIST)
    times = cleaning.parse_mixed_format_timestamps(
        working, [config.FIRST_ALERT_COLUMN, config.AWARENESS_COLUMN])
    first = times[config.FIRST_ALERT_COLUMN]
    aware = times[config.AWARENESS_COLUMN]
    recorded = pd.to_numeric(working[config.INCIDENT_INTERVAL_COLUMN], errors="coerce")
    both = first.notna() & aware.notna() & recorded.notna()
    minutes = (aware - first).dt.total_seconds() // 60
    return {
        "checked": int(both.sum()),
        "disagreeing": int((both & (minutes != recorded)).sum()),
        "confirmed_before_first_alert": int((both & (aware < first)).sum()),
    }


def _unrecognised(clean_frame, column_name, valid_values):
    if column_name not in clean_frame.columns:
        return 0
    allowed = set(valid_values) | {config.UNKNOWN_CATEGORY_VALUE}
    return int((~clean_frame[column_name].astype(str).isin(allowed)).sum())


def profile_incident_details(raw_frame, clean_frame):
    """The defects peculiar to the incident extracts."""
    return {
        "timestamp_notations": _timestamp_notations(raw_frame, config.INCIDENT_TIMESTAMP_COLUMNS),
        "counts_not_written_as_numbers": _not_plain_numbers(raw_frame,
                                                            config.INCIDENT_COUNT_COLUMNS),
        "values_written_with_units": _not_plain_numbers(
            raw_frame, config.INCIDENT_DURATION_MINUTES_COLUMNS + config.INCIDENT_MONEY_COLUMNS),
        "confirmation_interval_as_received": _interval_account(raw_frame),
        "confirmation_interval_after_cleaning": _interval_account(clean_frame.astype(str)),
        "unrecognised_hubs": _unrecognised(clean_frame, "soc_hub", config.VALID_HUBS),
        "unrecognised_system_classes": _unrecognised(clean_frame, "affected_system_class",
                                                     config.VALID_SYSTEM_CLASSES),
        "unrecognised_hosting_regions": _unrecognised(clean_frame, "hosting_region",
                                                      config.VALID_HOSTING_REGIONS),
        "unrecognised_protection_states": _unrecognised(clean_frame, "data_protection_state",
                                                        config.VALID_PROTECTION_STATES),
        "positive_share": round(float(pd.to_numeric(
            clean_frame[config.INCIDENT_TARGET_COLUMN]).mean()), 4) if len(clean_frame) else 0.0,
    }


def profile_effort_details(raw_frame, clean_frame):
    """The defects peculiar to the effort extracts."""
    flag = clean_frame[config.FORENSIC_IMAGE_FLAG_COLUMN]
    counts = pd.to_numeric(clean_frame[config.FORENSIC_IMAGE_COUNT_COLUMN], errors="coerce")
    return {
        "values_written_with_units": _not_plain_numbers(raw_frame,
                                                        config.EFFORT_DURATION_HOURS_COLUMNS),
        "forensic_images_without_requirement": int(((flag == config.BOOLEAN_NO)
                                                    & (counts > 0)).sum()),
        "unrecognised_analyst_grades": _unrecognised(clean_frame, "analyst_grade",
                                                     config.VALID_ANALYST_GRADES),
        "unrecognised_attack_types": _unrecognised(clean_frame, "attack_type",
                                                   config.VALID_ATTACK_TYPES),
        "median_hours": round(float(pd.to_numeric(
            clean_frame[config.EFFORT_TARGET_COLUMN]).median()), 4),
    }


def profile_note_details(raw_frame, clean_frame):
    """The defects peculiar to free text."""
    raw_text = raw_frame[config.NOTE_TEXT_COLUMN].fillna("").astype(str)
    shares = clean_frame[config.NOTE_TARGET_COLUMN].value_counts(normalize=True)
    return {
        "timestamp_notations": _timestamp_notations(raw_frame, config.NOTE_TIMESTAMP_COLUMNS),
        "notes_with_markup": int(raw_text.str.contains(config.MARKUP_PATTERN).sum()),
        "unrecognised_attack_types": _unrecognised(clean_frame, config.NOTE_TARGET_COLUMN,
                                                   config.VALID_ATTACK_TYPES),
        "shortest_note_words": int(clean_frame[config.NOTE_TEXT_COLUMN].astype(str)
                                   .str.split().str.len().min()) if len(clean_frame) else 0,
        "attack_type_shares": {str(name): round(float(share), 4)
                               for name, share in shares.sort_index().items()},
    }


def write_quality_report(profiles, file_path):
    """Write every profile as readable JSON."""
    folder = os.path.dirname(file_path)
    if folder:
        os.makedirs(folder, exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as report_file:
        json.dump(profiles, report_file, indent=2, sort_keys=False, default=str)
        report_file.write("\n")
    return file_path
