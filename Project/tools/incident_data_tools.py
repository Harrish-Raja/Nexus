"""Serves single records out of the live queue, from tables the caller already opened."""

import numpy as np
import pandas as pd

from config import config


def plain_value(value):
    """A cell as a plain Python value, with every gap as None."""
    if value is None:
        return None
    if isinstance(value, (list, dict, tuple)):
        return value
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    if isinstance(value, np.bool_):
        return bool(value)
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, np.floating):
        return float(value)
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    return value


def plain_record(row):
    return {str(key): plain_value(value) for key, value in dict(row).items()}


def _matching(frame, incident_reference):
    reference = str(incident_reference).strip()
    return frame[frame["incident_reference"].astype(str).str.strip() == reference]


def fetch_incident_profile(open_incidents, incident_reference):
    """One incident's own facts, column by column."""
    rows = _matching(open_incidents, incident_reference)
    if rows.empty:
        raise ValueError(config.INCIDENT_NOT_IN_QUEUE_MESSAGE % incident_reference)
    return plain_record(rows.iloc[0])


def fetch_incident_notes(open_incident_notes, incident_reference):
    """Every note on one incident, oldest first by note_sequence."""
    rows = _matching(open_incident_notes, incident_reference)
    if rows.empty:
        raise ValueError(config.INCIDENT_WITHOUT_NOTES_MESSAGE % incident_reference)
    ordered = rows.sort_values("note_sequence", kind="stable")
    return [str(text) for text in ordered[config.NOTE_TEXT_COLUMN]]


def fetch_campaign_incidents(open_incidents, incident_profile):
    """Every incident of the same campaign, itself included; an unlinked incident alone."""
    campaign = incident_profile.get(config.CAMPAIGN_COLUMN)
    if campaign is None or str(campaign).strip() in ("", config.NO_CAMPAIGN_VALUE):
        rows = _matching(open_incidents, incident_profile["incident_reference"])
        if rows.empty:
            return [{column: plain_value(incident_profile.get(column))
                     for column in config.CAMPAIGN_INCIDENT_COLUMNS}]
    else:
        rows = open_incidents[open_incidents[config.CAMPAIGN_COLUMN].astype(str).str.strip()
                              == str(campaign).strip()]
    return [{column: plain_value(row[column]) for column in config.CAMPAIGN_INCIDENT_COLUMNS}
            for _, row in rows.iterrows()]
