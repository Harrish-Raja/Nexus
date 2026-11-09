"""Which procedures apply, what each clock says, which deadline governs, and whether the work fits.

Every hour in this module comes from a reading of a procedure's own document.
"""

import pandas as pd

from config import config
from tools.incident_data_tools import fetch_campaign_incidents
from tools.prediction_tools import build_harm_facts


def _number(value):
    try:
        number = float(value)
    except (TypeError, ValueError):
        return 0.0
    return 0.0 if pd.isna(number) else number


def _instant(value):
    if value is None:
        return None
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    try:
        return pd.to_datetime(value, utc=True)
    except (TypeError, ValueError):
        return None


def _snapshot():
    return pd.to_datetime(config.SNAPSHOT_AT_UTC, utc=True)


def select_applicable_procedures(incident_profile, harm_band, campaign_incidents):
    """Decide which reporting procedures apply, and say on which grounds."""
    grounds = {}

    eu_subjects = _number(incident_profile.get(config.EU_DATA_SUBJECTS_COLUMN))
    personal = str(incident_profile.get("personal_data_involved_flag")) == config.BOOLEAN_YES
    if personal and eu_subjects > 0 and harm_band in config.EU_PROCEDURE_HARM_BANDS:
        grounds[config.PROCEDURE_EU_PERSONAL_DATA_BREACH] = (
            f"personal data of {int(eu_subjects)} EU data subjects involved at a {harm_band} "
            "harm band")

    own_customers = _number(incident_profile.get("customers_affected_count"))
    campaign = list(campaign_incidents) if campaign_incidents else [
        {"customers_affected_count": own_customers}]
    across = sum(_number(entry.get("customers_affected_count")) for entry in campaign)
    outage = _number(incident_profile.get("service_outage_minutes"))
    loss = _number(incident_profile.get("direct_financial_loss_eur"))
    outage_met = outage > config.SIGNIFICANT_OUTAGE_MINUTES
    customers_met = across > config.SIGNIFICANT_CUSTOMERS_ACROSS_CAMPAIGN
    loss_met = loss > config.SIGNIFICANT_DIRECT_LOSS_EUR
    reasons = []
    if outage_met:
        reasons.append(f"a service outage of {int(outage)} minutes, more than "
                       f"{config.SIGNIFICANT_OUTAGE_MINUTES}")
    if customers_met:
        reasons.append(f"{int(across)} customers affected across the campaign, more than "
                       f"{config.SIGNIFICANT_CUSTOMERS_ACROSS_CAMPAIGN}")
    if loss_met:
        reasons.append(f"a direct loss of EUR {int(loss)}, more than "
                       f"EUR {config.SIGNIFICANT_DIRECT_LOSS_EUR}")
    if reasons:
        grounds[config.PROCEDURE_SIGNIFICANT_INCIDENT] = "; ".join(reasons)

    india_subjects = _number(incident_profile.get(config.INDIA_DATA_SUBJECTS_COLUMN))
    region = incident_profile.get("hosting_region")
    india_reasons = []
    if region in config.INDIA_HOSTING_REGIONS:
        india_reasons.append(f"systems hosted in {region}")
    if india_subjects > 0:
        india_reasons.append(f"{int(india_subjects)} Indian data subjects")
    if india_reasons:
        grounds[config.PROCEDURE_INDIA_CYBER_INCIDENT] = "; ".join(india_reasons)

    significant_only_with_campaign = bool(
        customers_met and own_customers <= config.SIGNIFICANT_CUSTOMERS_ACROSS_CAMPAIGN
        and not outage_met and not loss_met)
    applicable = [code for code in config.PROCEDURE_OPTIONS if code in grounds]
    return {"applicable_procedures": applicable,
            "grounds": {code: grounds[code] for code in applicable},
            "customers_across_campaign": int(across) if float(across).is_integer() else across,
            "significant_only_with_campaign": significant_only_with_campaign}


def _hub_zone(incident_profile):
    return config.HUB_TIME_ZONE_BY_HUB.get(incident_profile.get("soc_hub"), "UTC")


def compute_procedure_deadlines(incident_profile, procedure_readings):
    """Start every clock from the moment its own procedure names, and find the earliest."""
    zone = _hub_zone(incident_profile)
    snapshot = _snapshot()
    ordered_codes = ([code for code in config.PROCEDURE_OPTIONS if code in procedure_readings]
                     + [code for code in procedure_readings if code not in config.PROCEDURE_OPTIONS])
    milestones, filed_milestones = [], []
    for code in ordered_codes:
        reading = procedure_readings[code]
        authority = config.PROCEDURE_AUTHORITY_BY_CODE.get(code)
        for milestone in reading.get("milestones", []):
            started = _instant(incident_profile.get(milestone["clock_start_column"]))
            line = {
                "procedure_code": code,
                "authority": authority,
                "milestone": milestone["milestone"],
                "hours": milestone["hours"],
                "clock_start_phrase": milestone["clock_start_phrase"],
                "clock_start_column": milestone["clock_start_column"],
                "clock_started": started is not None,
                "source_documents": list(reading.get("source_documents", [])),
                "started_at": None, "due_at": None, "due_at_hub_time": None,
                "hours_remaining": None, "overdue": False,
                "status": config.CLOCK_NOT_STARTED_MESSAGE,
            }
            if started is not None:
                due = started + pd.Timedelta(hours=float(milestone["hours"]))
                left = (due - snapshot).total_seconds() / 3600
                overdue = due <= snapshot
                line.update({
                    "started_at": started.strftime(config.OUTPUT_TIMESTAMP_FORMAT),
                    "due_at": due.strftime(config.OUTPUT_TIMESTAMP_FORMAT),
                    "due_at_hub_time": due.tz_convert(zone).strftime(
                        config.DISPLAY_TIMESTAMP_FORMAT),
                    "hours_remaining": round(left, 2),
                    "overdue": bool(overdue),
                    "status": config.DEADLINE_OVERDUE_MESSAGE if overdue else "Running",
                })
            milestones.append(line)
        for filed in reading.get("filed_milestones", []):
            filed_milestones.append({"procedure_code": code, "authority": authority,
                                     "milestone": filed["milestone"], "months": filed["months"],
                                     "after_milestone": filed["after_milestone"]})
    running = [line for line in milestones if line["clock_started"]]
    earliest = min(running, key=lambda line: line["hours_remaining"]) if running else None
    return {"milestones": milestones, "earliest_milestone": earliest,
            "filed_milestones": filed_milestones, "hub_time_zone": zone}


def compare_effort_with_deadline(effort_facts, deadline_facts):
    """Whether the effort fits in the hours the earliest deadline leaves, less the reserve."""
    earliest = deadline_facts.get("earliest_milestone")
    if not earliest:
        message = (config.CLOCK_NOT_STARTED_MESSAGE if deadline_facts.get("milestones")
                   else config.NO_PROCEDURE_APPLIES_MESSAGE)
        return {"hours_remaining": None, "hours_available": None,
                "can_file_complete_in_time": None, "deadline_message": message}
    remaining = float(earliest["hours_remaining"])
    available = round(remaining - config.FILING_RESERVE_HOURS, 2)
    fits = bool(float(effort_facts["effort_needed_hours"]) <= available)
    if earliest.get("overdue"):
        message = config.DEADLINE_OVERDUE_MESSAGE
        fits = False
    elif not fits:
        message = config.DEADLINE_BREACH_MESSAGE
    else:
        message = None
    return {"hours_remaining": remaining, "hours_available": available,
            "can_file_complete_in_time": fits, "deadline_message": message}


def compute_final_report_due(deadline_facts, filing_submitted_at):
    """The earliest report counted in calendar months from the moment of filing, if any."""
    filed = deadline_facts.get("filed_milestones") or []
    filed_at = _instant(filing_submitted_at)
    if not filed or filed_at is None:
        return None
    due = min(filed_at + pd.DateOffset(months=int(entry["months"])) for entry in filed)
    return due.strftime(config.OUTPUT_TIMESTAMP_FORMAT)


def rank_incident_queue(open_incidents, harm_model, harm_feature_names, procedure_readings):
    """The whole queue, nearest running deadline first, then by harm where nothing runs."""
    harm_facts = build_harm_facts(harm_model, harm_feature_names, open_incidents)
    rows = []
    for position, (_, record) in enumerate(open_incidents.iterrows()):
        profile = {key: (None if not isinstance(value, (list, dict)) and pd.isna(value) else value)
                   for key, value in record.items()}
        facts = harm_facts[position]
        campaign = fetch_campaign_incidents(open_incidents, profile)
        applicability = select_applicable_procedures(profile, facts["harm_band"], campaign)
        readings = {code: procedure_readings[code]
                    for code in applicability["applicable_procedures"]
                    if code in procedure_readings}
        deadlines = compute_procedure_deadlines(profile, readings)
        rows.append({
            "incident_reference": str(profile["incident_reference"]),
            "soc_hub": str(profile.get("soc_hub")),
            "harm_probability": facts["harm_probability"],
            "harm_band": facts["harm_band"],
            "applicable_procedures": applicability["applicable_procedures"],
            "significant_only_with_campaign": applicability["significant_only_with_campaign"],
            "awareness_established": _instant(profile.get(config.AWARENESS_COLUMN)) is not None,
            "earliest_milestone": deadlines["earliest_milestone"],
        })
    running = sorted((row for row in rows if row["earliest_milestone"] is not None),
                     key=lambda row: row["earliest_milestone"]["hours_remaining"])
    waiting = sorted((row for row in rows if row["earliest_milestone"] is None),
                     key=lambda row: -row["harm_probability"])
    return running + waiting
