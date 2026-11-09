"""Turns what the models produce into the facts the business acts on."""

from collections import Counter

import pandas as pd

from config import config


def harm_band_for(probability):
    if probability >= config.HARM_BAND_HIGH_THRESHOLD:
        return config.HARM_BAND_HIGH
    if probability >= config.HARM_BAND_MEDIUM_THRESHOLD:
        return config.HARM_BAND_MEDIUM
    return config.HARM_BAND_LOW


def _flagged(row, columns):
    return [column for column in columns
            if column in row and str(row[column]) == config.BOOLEAN_YES]


def build_harm_facts(harm_model, harm_feature_names, incidents):
    """Score each incident, band the score, and name the kinds of data involved."""
    frame = pd.DataFrame(incidents).reset_index(drop=True)
    features = frame.reindex(columns=list(harm_feature_names))
    probabilities = harm_model.predict_proba(features)[:, 1]
    facts = []
    for position, probability in enumerate(probabilities):
        row = frame.iloc[position]
        facts.append({
            "harm_probability": round(float(probability), 4),
            "harm_band": harm_band_for(float(probability)),
            "data_categories": _flagged(row, config.DATA_CATEGORY_FLAG_COLUMNS),
            "high_impact_categories": _flagged(row, config.HIGH_IMPACT_DATA_FLAG_COLUMNS),
            "sensitive_categories": _flagged(row, config.SENSITIVE_DATA_FLAG_COLUMNS),
        })
    return facts


def build_attack_facts(attack_model, note_texts):
    """What every note is called, the type most notes name, and how far they agree."""
    texts = [str(text) for text in note_texts]
    predicted = [str(label) for label in attack_model.predict(texts)] if texts else []
    counts = Counter(predicted)
    if counts:
        first_seen = {label: predicted.index(label) for label in counts}
        attack_type = max(counts, key=lambda label: (counts[label], -first_seen[label]))
        agreement = round(counts[attack_type] / len(predicted), 4)
    else:
        attack_type, agreement = None, 0.0
    order = {label: position for position, label in enumerate(config.VALID_ATTACK_TYPES)}
    others = sorted((label for label in counts if label != attack_type),
                    key=lambda label: (order.get(label, len(order)), label))
    return {"attack_type": attack_type, "agreement": agreement, "notes_read": len(predicted),
            "note_attack_types": predicted, "other_attack_types": others}


def _planned_start(hub):
    zone = config.HUB_TIME_ZONE_BY_HUB.get(hub, "UTC")
    return pd.Timestamp(config.SNAPSHOT_AT_UTC).tz_convert(zone)


def estimate_containment_effort(effort_model, effort_feature_names, incident_profile, harm_facts,
                                attack_type):
    """Estimate containment hours for a containment starting at the snapshot, in hub time."""
    start = _planned_start(incident_profile.get("soc_hub"))
    weekday = config.VALID_WEEKDAYS[start.weekday()]
    out_of_hours = (start.hour < config.WORKING_HOURS_START_HOUR
                    or start.hour >= config.WORKING_HOURS_END_HOUR
                    or weekday in config.WEEKEND_DAYS)

    known = {
        "attack_type": attack_type,
        "harm_band": harm_facts["harm_band"],
        "data_categories_affected_count": len(harm_facts["data_categories"]),
        "regions_affected_count": config.REGIONS_AFFECTED_BY_HOSTING_REGION.get(
            incident_profile.get("hosting_region"), 1),
        "weekday_started": weekday,
        "out_of_hours_start_flag": config.BOOLEAN_YES if out_of_hours else config.BOOLEAN_NO,
    }
    row = {}
    for column_name in effort_feature_names:
        if column_name in known:
            row[column_name] = known[column_name]
        elif column_name in config.CONTAINMENT_PLANNING_ASSUMPTIONS:
            row[column_name] = config.CONTAINMENT_PLANNING_ASSUMPTIONS[column_name]
        elif column_name in config.EFFORT_MODEL_BASELINES:
            row[column_name] = config.EFFORT_MODEL_BASELINES[column_name]
        else:
            row[column_name] = incident_profile.get(column_name)
    estimate = float(effort_model.predict(pd.DataFrame([row], columns=list(effort_feature_names)))[0])
    estimate = max(estimate, 0.01)

    multiplier_applied = len(harm_facts["sensitive_categories"]) > 0
    needed = estimate * config.SENSITIVE_DATA_EFFORT_MULTIPLIER if multiplier_applied else estimate
    return {
        "base_hours": max(round(estimate, 2), 0.01),
        "multiplier_applied": multiplier_applied,
        "effort_needed_hours": max(round(needed, 2), 0.01),
        "containment_starts": start.strftime(config.DISPLAY_TIMESTAMP_FORMAT),
        "weekday_started": weekday,
        "out_of_hours_start": config.BOOLEAN_YES if out_of_hours else config.BOOLEAN_NO,
        "planning_assumptions": [name for name in config.CONTAINMENT_PLANNING_ASSUMPTIONS
                                 if name in effort_feature_names],
    }
