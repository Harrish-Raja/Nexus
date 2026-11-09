"""The whole cleaning run for the two security incident extracts."""

import numpy as np
import pandas as pd

from config import config
from data_pipeline import common_cleaning as cleaning
from data_pipeline.dataset_loader import load_raw_dataset, save_processed_dataset


def _own_mapping(valid_values):
    return {value.lower(): value for value in valid_values}


INCIDENT_CATEGORY_VOCABULARY = {
    "soc_hub": (config.HUB_MAPPING, config.VALID_HUBS),
    "detection_source": (config.DETECTION_SOURCE_MAPPING, config.VALID_DETECTION_SOURCES),
    "initial_severity": (_own_mapping(config.VALID_SEVERITIES), config.VALID_SEVERITIES),
    "affected_system_class": (config.SYSTEM_CLASS_MAPPING, config.VALID_SYSTEM_CLASSES),
    "hosting_region": (config.HOSTING_REGION_MAPPING, config.VALID_HOSTING_REGIONS),
    "attack_vector": (config.ATTACK_VECTOR_MAPPING, config.VALID_ATTACK_VECTORS),
    "data_protection_state": (config.PROTECTION_STATE_MAPPING, config.VALID_PROTECTION_STATES),
    "ticket_queue_code": (_own_mapping(config.VALID_TICKET_QUEUES), config.VALID_TICKET_QUEUES),
    "weekday_detected": (_own_mapping(config.VALID_WEEKDAYS), config.VALID_WEEKDAYS),
    "analyst_shift_code": (_own_mapping(config.VALID_SHIFT_CODES), config.VALID_SHIFT_CODES),
}


def _put_timeline_in_order(dataframe):
    """Swap the first alert and the confirmation where the confirmation comes first."""
    result = dataframe.copy()
    first = result[config.FIRST_ALERT_COLUMN]
    aware = result[config.AWARENESS_COLUMN]
    backwards = (aware < first).fillna(False).astype(bool)
    result.loc[backwards, config.FIRST_ALERT_COLUMN] = aware[backwards]
    result.loc[backwards, config.AWARENESS_COLUMN] = first[backwards]
    return result


def _recompute_interval(dataframe):
    """Whole minutes from first alert to confirmation, wherever both are known."""
    result = dataframe.copy()
    first = result[config.FIRST_ALERT_COLUMN]
    aware = result[config.AWARENESS_COLUMN]
    both = first.notna() & aware.notna()
    minutes = ((aware - first).dt.total_seconds() // 60)
    recorded = pd.to_numeric(result[config.INCIDENT_INTERVAL_COLUMN], errors="coerce")
    result[config.INCIDENT_INTERVAL_COLUMN] = recorded.where(~both, minutes)
    return result


def _fill_missing_timeline(dataframe):
    """Fill an unknown moment from the other one and the interval, so no cell is empty."""
    result = dataframe.copy()
    interval = pd.to_timedelta(result[config.INCIDENT_INTERVAL_COLUMN], unit="m")
    first = result[config.FIRST_ALERT_COLUMN]
    aware = result[config.AWARENESS_COLUMN]
    result[config.FIRST_ALERT_COLUMN] = first.where(first.notna(), aware - interval)
    result[config.AWARENESS_COLUMN] = aware.where(aware.notna(),
                                                  result[config.FIRST_ALERT_COLUMN] + interval)
    for column_name in config.INCIDENT_TIMESTAMP_COLUMNS:
        column = result[column_name]
        if column.isna().any():
            result[column_name] = column.where(column.notna(), result[config.FIRST_ALERT_COLUMN])
    return result


def clean_incident_dataset(input_file_path, output_file_path):
    """Turn one raw incident extract into the cleaned table the harm model learns from."""
    frame = load_raw_dataset(input_file_path, config.NULL_TOKEN_LIST)
    frame = cleaning.strip_text_whitespace(frame)
    frame = cleaning.replace_missing_tokens(frame, config.NULL_TOKEN_LIST)

    for column_name, (mapping, valid_values) in INCIDENT_CATEGORY_VOCABULARY.items():
        frame = cleaning.normalize_category_column(frame, column_name, mapping)
        frame = cleaning.restrict_to_known_values(frame, column_name, valid_values)
    frame = cleaning.normalize_boolean_columns(
        frame, config.INCIDENT_BOOLEAN_COLUMNS + [config.INCIDENT_TARGET_COLUMN])

    frame = cleaning.parse_mixed_format_timestamps(frame, config.INCIDENT_TIMESTAMP_COLUMNS)
    frame = _put_timeline_in_order(frame)

    frame = cleaning.convert_written_counts(frame, config.INCIDENT_COUNT_COLUMNS)
    frame = cleaning.convert_money_amounts(frame, config.INCIDENT_MONEY_COLUMNS)
    frame = cleaning.convert_durations_to_minutes(frame, config.INCIDENT_DURATION_MINUTES_COLUMNS)
    frame = cleaning.convert_text_to_numeric(frame, config.INCIDENT_NUMERIC_COLUMNS)
    frame = cleaning.remove_out_of_range_measurements(frame, config.INCIDENT_RANGE_LIMITS)
    frame = _recompute_interval(frame)

    frame = cleaning.remove_rows_missing_target(frame, config.INCIDENT_TARGET_COLUMN)
    frame = cleaning.remove_duplicate_records(frame)

    frame = cleaning.resolve_missing_measurements(frame, config.INCIDENT_NUMERIC_COLUMNS)
    frame = _fill_missing_timeline(frame)
    frame = cleaning.resolve_missing_categories(frame, config.INCIDENT_CATEGORY_COLUMNS)
    frame = cleaning.resolve_missing_categories(frame, config.INCIDENT_BOOLEAN_COLUMNS)
    remaining_text = [name for name in frame.columns
                      if name not in config.INCIDENT_NUMERIC_COLUMNS
                      and name not in config.INCIDENT_TIMESTAMP_COLUMNS
                      and name != config.INCIDENT_TARGET_COLUMN]
    frame = cleaning.resolve_missing_categories(frame, remaining_text)

    frame[config.INCIDENT_TARGET_COLUMN] = np.where(
        frame[config.INCIDENT_TARGET_COLUMN] == config.BOOLEAN_YES, 1, 0).astype(int)
    frame = cleaning.format_timestamps_as_text(frame, config.INCIDENT_TIMESTAMP_COLUMNS)
    frame = frame.reset_index(drop=True)

    save_processed_dataset(frame, output_file_path)
    return frame
