"""The repairs more than one dataset needs.

Every function takes a table and returns a repaired copy, leaving the table it was
given untouched. No function reads or writes a file, and none removes a column.
"""

import datetime
import re

import numpy as np
import pandas as pd

from config import config


def _is_text_column(series):
    return series.dtype == object or pd.api.types.is_string_dtype(series.dtype)


def _is_missing(value):
    if value is None:
        return True
    try:
        return bool(pd.isna(value))
    except (TypeError, ValueError):
        return False


def _as_object(series):
    """The column as plain Python objects, with every gap held as NaN."""
    values = series.astype(object)
    return values.where(~series.isna(), np.nan)


def strip_text_whitespace(dataframe):
    """Remove leading and trailing whitespace from every text column."""
    result = dataframe.copy()
    for column_name in result.columns:
        if _is_text_column(result[column_name]):
            result[column_name] = _as_object(result[column_name]).map(
                lambda value: value.strip() if isinstance(value, str) else value)
    return result


def replace_missing_tokens(dataframe, null_tokens):
    """Empty every cell whose whole value is one of the ways 'missing' is written."""
    tokens = {str(token).strip().lower() for token in null_tokens}
    result = dataframe.copy()
    for column_name in result.columns:
        if _is_text_column(result[column_name]):
            result[column_name] = _as_object(result[column_name]).map(
                lambda value: np.nan if isinstance(value, str)
                and value.strip().lower() in tokens else value)
    return result


def remove_duplicate_records(dataframe):
    """Keep the first of every set of rows identical in every column."""
    return dataframe.drop_duplicates(keep="first").reset_index(drop=True)


def normalize_category_column(dataframe, column_name, value_mapping):
    """Fold the spellings of one business value onto that value, ignoring case and padding."""
    lookup = {str(key).strip().lower(): value for key, value in value_mapping.items()}
    result = dataframe.copy()

    def fold(value):
        if isinstance(value, str):
            return lookup.get(value.strip().lower(), value)
        return value

    result[column_name] = _as_object(result[column_name]).map(fold)
    return result


def restrict_to_known_values(dataframe, column_name, valid_values):
    """Empty every value the business vocabulary does not hold."""
    allowed = set(valid_values)
    result = dataframe.copy()
    result[column_name] = _as_object(result[column_name]).map(
        lambda value: value if isinstance(value, str) and value in allowed else np.nan)
    return result


def normalize_boolean_columns(dataframe, boolean_columns):
    """Turn every way of writing yes and no into the two business values."""
    true_tokens = {token.lower() for token in config.BOOLEAN_TRUE_TOKENS}
    false_tokens = {token.lower() for token in config.BOOLEAN_FALSE_TOKENS}

    def fold(value):
        if _is_missing(value):
            return np.nan
        text = str(value).strip().lower()
        if isinstance(value, float) and float(value).is_integer():
            text = str(int(value))
        if text in true_tokens:
            return config.BOOLEAN_YES
        if text in false_tokens:
            return config.BOOLEAN_NO
        return np.nan

    result = dataframe.copy()
    for column_name in boolean_columns:
        result[column_name] = _as_object(result[column_name]).map(fold)
    return result


_EPOCH = re.compile(config.EPOCH_SECONDS_PATTERN)
_ZONE = re.compile(config.ZONE_ABBREVIATION_PATTERN)
_OFFSET = re.compile(config.UTC_OFFSET_SUFFIX_PATTERN)


def _parse_one_timestamp(value):
    if _is_missing(value):
        return pd.NaT
    if isinstance(value, (pd.Timestamp, datetime.datetime)):
        stamp = pd.Timestamp(value)
        return stamp.tz_localize("UTC") if stamp.tzinfo is None else stamp.tz_convert("UTC")
    text = str(value).strip()
    if not text:
        return pd.NaT
    if _EPOCH.match(text):
        return pd.Timestamp(int(text), unit="s", tz="UTC")
    if text.endswith(config.ISO_UTC_SUFFIX):
        text = text[: -len(config.ISO_UTC_SUFFIX)] + "+00:00"
    zone_match = _ZONE.search(text)
    if zone_match and not _OFFSET.search(text):
        offset = config.TIMEZONE_ABBREVIATION_OFFSETS.get(zone_match.group(1))
        if offset is None:
            return pd.NaT
        text = text[: zone_match.start()] + " " + offset
    for timestamp_format in config.TIMESTAMP_FORMAT_LIST:
        try:
            parsed = datetime.datetime.strptime(text, timestamp_format)
        except ValueError:
            continue
        return pd.Timestamp(parsed).tz_convert("UTC")
    return pd.NaT


def parse_mixed_format_timestamps(dataframe, timestamp_columns):
    """Read each timestamp column, whatever notation and zone it was written in, into UTC."""
    result = dataframe.copy()
    for column_name in timestamp_columns:
        parsed = [_parse_one_timestamp(value) for value in result[column_name]]
        result[column_name] = pd.to_datetime(pd.Series(parsed, index=result.index,
                                                       dtype=object), utc=True)
    return result


def format_timestamps_as_text(dataframe, timestamp_columns):
    """Write instants back as UTC text in the one output notation."""
    result = dataframe.copy()
    for column_name in timestamp_columns:
        instants = pd.to_datetime(result[column_name], utc=True)
        result[column_name] = _as_object(instants.dt.strftime(config.OUTPUT_TIMESTAMP_FORMAT))
    return result


def _parse_one_date(value):
    if _is_missing(value):
        return pd.NaT
    text = str(value).strip()
    for date_format in config.DATE_FORMAT_LIST:
        try:
            return pd.Timestamp(datetime.datetime.strptime(text, date_format))
        except ValueError:
            continue
    return pd.NaT


def parse_mixed_format_dates(dataframe, date_columns):
    """Read each date column, whichever of the date notations it was written in."""
    result = dataframe.copy()
    for column_name in date_columns:
        parsed = [_parse_one_date(value) for value in result[column_name]]
        result[column_name] = pd.to_datetime(pd.Series(parsed, index=result.index, dtype=object))
    return result


def format_dates_as_text(dataframe, date_columns):
    """Write dates back as text in the one output notation."""
    result = dataframe.copy()
    for column_name in date_columns:
        dates = pd.to_datetime(result[column_name])
        result[column_name] = _as_object(dates.dt.strftime(config.OUTPUT_DATE_FORMAT))
    return result


def _plain_number(text):
    """A number written with digit grouping, or nothing if it is not one."""
    cleaned = text.replace(config.DIGIT_GROUPING_SEPARATOR, "").strip()
    try:
        return float(cleaned)
    except ValueError:
        return np.nan


_SUFFIX_PATTERN = re.compile(
    r"^([\d" + re.escape(config.DIGIT_GROUPING_SEPARATOR) + r".]+)\s*("
    + "|".join(re.escape(suffix) for suffix in sorted(config.COUNT_SUFFIX_MULTIPLIERS,
                                                      key=len, reverse=True))
    + r")$", re.IGNORECASE)
_SUFFIX_MULTIPLIERS = {suffix.lower(): multiplier
                       for suffix, multiplier in config.COUNT_SUFFIX_MULTIPLIERS.items()}


def _read_count(value):
    if _is_missing(value):
        return np.nan
    if isinstance(value, (int, float, np.integer, np.floating)):
        return float(value)
    text = str(value).strip()
    suffixed = _SUFFIX_PATTERN.match(text)
    if suffixed:
        number = _plain_number(suffixed.group(1))
        if pd.isna(number):
            return np.nan
        return float(round(number * _SUFFIX_MULTIPLIERS[suffixed.group(2).lower()]))
    return _plain_number(text)


def convert_written_counts(dataframe, count_columns):
    """Turn counts written with digit groups or a lakh/thousand suffix into numbers."""
    result = dataframe.copy()
    for column_name in count_columns:
        result[column_name] = pd.to_numeric(result[column_name].map(_read_count),
                                            errors="coerce")
    return result


def _read_money(value):
    if _is_missing(value):
        return np.nan
    if isinstance(value, (int, float, np.integer, np.floating)):
        return float(value)
    text = str(value).strip()
    for marker in sorted(config.CURRENCY_MARKERS, key=len, reverse=True):
        if text.upper().startswith(marker.upper()):
            text = text[len(marker):]
        if text.upper().endswith(marker.upper()):
            text = text[: len(text) - len(marker)]
        text = text.strip()
    return _plain_number(text)


def convert_money_amounts(dataframe, money_columns):
    """Turn amounts written with a currency marker into numbers of euros."""
    result = dataframe.copy()
    for column_name in money_columns:
        result[column_name] = pd.to_numeric(result[column_name].map(_read_money),
                                            errors="coerce")
    return result


_HOURS_AND_MINUTES = re.compile(config.HOURS_AND_MINUTES_PATTERN, re.IGNORECASE)
_MINUTES_ONLY = re.compile(config.MINUTES_UNIT_PATTERN, re.IGNORECASE)
_HOURS_ONLY = re.compile(config.HOURS_UNIT_PATTERN, re.IGNORECASE)


def _read_duration(value, bare_unit_minutes):
    """A duration in minutes; a bare number is taken in the column's own unit."""
    if _is_missing(value):
        return np.nan
    if isinstance(value, (int, float, np.integer, np.floating)):
        return float(value) * bare_unit_minutes
    text = str(value).strip()
    both = _HOURS_AND_MINUTES.match(text)
    if both:
        return float(both.group(1)) * 60 + float(both.group(2))
    minutes = _MINUTES_ONLY.match(text)
    if minutes:
        return float(minutes.group(1))
    hours = _HOURS_ONLY.match(text)
    if hours:
        return float(hours.group(1)) * 60
    try:
        return float(text) * bare_unit_minutes
    except ValueError:
        return np.nan


def convert_durations_to_minutes(dataframe, duration_columns):
    """Turn durations written with units into minutes."""
    result = dataframe.copy()
    for column_name in duration_columns:
        result[column_name] = pd.to_numeric(
            result[column_name].map(lambda value: _read_duration(value, 1.0)), errors="coerce")
    return result


def convert_durations_to_hours(dataframe, duration_columns):
    """Turn durations written with units into hours; a bare number is already hours."""
    result = dataframe.copy()
    for column_name in duration_columns:
        def to_hours(value):
            if _is_missing(value):
                return np.nan
            if isinstance(value, (int, float, np.integer, np.floating)):
                return float(value)
            text = str(value).strip()
            try:
                return float(text)
            except ValueError:
                minutes = _read_duration(text, 60.0)
                return minutes / 60.0 if not pd.isna(minutes) else np.nan

        result[column_name] = pd.to_numeric(result[column_name].map(to_hours), errors="coerce")
    return result


def convert_text_to_numeric(dataframe, numeric_columns):
    """Turn the remaining measured columns into numbers; anything else becomes empty."""
    result = dataframe.copy()
    for column_name in numeric_columns:
        result[column_name] = pd.to_numeric(result[column_name], errors="coerce")
    return result


def remove_out_of_range_measurements(dataframe, range_limits):
    """Empty readings below or above the limits for their column."""
    result = dataframe.copy()
    for column_name, (lowest, highest) in range_limits.items():
        if column_name not in result.columns:
            continue
        values = pd.to_numeric(result[column_name], errors="coerce")
        outside = (values < lowest) | (values > highest)
        result[column_name] = values.where(~outside, np.nan)
    return result


def remove_rows_missing_target(dataframe, target_column):
    """Drop every row whose answer is empty."""
    return dataframe[dataframe[target_column].notna()].reset_index(drop=True)


def resolve_missing_measurements(dataframe, numeric_columns):
    """Fill gaps in measured columns with the median of the column's own readings."""
    result = dataframe.copy()
    for column_name in numeric_columns:
        values = pd.to_numeric(result[column_name], errors="coerce")
        if values.isna().any():
            median = values.median()
            values = values.fillna(0.0 if pd.isna(median) else median)
        result[column_name] = values
    return result


def resolve_missing_categories(dataframe, category_columns):
    """Fill gaps in category columns with the value that says nothing was recorded."""
    result = dataframe.copy()
    for column_name in category_columns:
        values = _as_object(result[column_name])
        result[column_name] = values.where(values.notna(), config.UNKNOWN_CATEGORY_VALUE)
    return result
