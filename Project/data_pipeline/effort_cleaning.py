"""The whole cleaning run for the two containment effort extracts."""

import pandas as pd

from config import config
from data_pipeline import common_cleaning as cleaning
from data_pipeline.dataset_loader import load_raw_dataset, save_processed_dataset


def _own_mapping(valid_values):
    return {value.lower(): value for value in valid_values}


EFFORT_CATEGORY_VOCABULARY = {
    "soc_hub": (config.HUB_MAPPING, config.VALID_HUBS),
    "attack_type": (config.ATTACK_TYPE_MAPPING, config.VALID_ATTACK_TYPES),
    "harm_band": (config.HARM_BAND_MAPPING, config.HARM_BAND_OPTIONS),
    "initial_severity": (_own_mapping(config.VALID_SEVERITIES), config.VALID_SEVERITIES),
    "analyst_grade": (config.ANALYST_GRADE_MAPPING, config.VALID_ANALYST_GRADES),
    "weekday_started": (_own_mapping(config.VALID_WEEKDAYS), config.VALID_WEEKDAYS),
    "ticket_queue_code": (_own_mapping(config.VALID_TICKET_QUEUES), config.VALID_TICKET_QUEUES),
}


def _repair_forensic_counts(dataframe):
    """No image was required, so none was counted: the flag is the decision."""
    result = dataframe.copy()
    not_required = result[config.FORENSIC_IMAGE_FLAG_COLUMN] == config.BOOLEAN_NO
    counts = pd.to_numeric(result[config.FORENSIC_IMAGE_COUNT_COLUMN], errors="coerce")
    result[config.FORENSIC_IMAGE_COUNT_COLUMN] = counts.where(~(not_required & (counts > 0)), 0.0)
    return result


def _fill_missing_dates(dataframe):
    result = dataframe.copy()
    for column_name in config.EFFORT_DATE_COLUMNS:
        column = result[column_name]
        if column.isna().any() and column.notna().any():
            result[column_name] = column.fillna(column.mode().iloc[0])
    return result


def clean_effort_dataset(input_file_path, output_file_path):
    """Turn one raw effort extract into the cleaned table the effort model learns from."""
    frame = load_raw_dataset(input_file_path, config.NULL_TOKEN_LIST)
    frame = cleaning.strip_text_whitespace(frame)
    frame = cleaning.replace_missing_tokens(frame, config.NULL_TOKEN_LIST)

    for column_name, (mapping, valid_values) in EFFORT_CATEGORY_VOCABULARY.items():
        frame = cleaning.normalize_category_column(frame, column_name, mapping)
        frame = cleaning.restrict_to_known_values(frame, column_name, valid_values)
    frame = cleaning.normalize_boolean_columns(frame, config.EFFORT_BOOLEAN_COLUMNS)

    frame = cleaning.parse_mixed_format_dates(frame, config.EFFORT_DATE_COLUMNS)
    frame = cleaning.convert_durations_to_hours(frame, config.EFFORT_DURATION_HOURS_COLUMNS)
    frame = cleaning.convert_text_to_numeric(frame, config.EFFORT_NUMERIC_COLUMNS)
    frame = _repair_forensic_counts(frame)
    frame = cleaning.remove_out_of_range_measurements(frame, config.EFFORT_RANGE_LIMITS)

    frame = cleaning.remove_rows_missing_target(frame, config.EFFORT_TARGET_COLUMN)
    frame = cleaning.remove_duplicate_records(frame)

    frame = cleaning.resolve_missing_measurements(frame, config.EFFORT_NUMERIC_COLUMNS)
    frame = _fill_missing_dates(frame)
    frame = cleaning.resolve_missing_categories(frame, config.EFFORT_CATEGORY_COLUMNS)
    frame = cleaning.resolve_missing_categories(frame, config.EFFORT_BOOLEAN_COLUMNS)
    remaining_text = [name for name in frame.columns
                      if name not in config.EFFORT_NUMERIC_COLUMNS
                      and name not in config.EFFORT_DATE_COLUMNS]
    frame = cleaning.resolve_missing_categories(frame, remaining_text)

    frame = cleaning.format_dates_as_text(frame, config.EFFORT_DATE_COLUMNS)
    frame = frame.reset_index(drop=True)

    save_processed_dataset(frame, output_file_path)
    return frame
