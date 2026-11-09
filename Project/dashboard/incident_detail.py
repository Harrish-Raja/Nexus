"""Everything established about one incident, and the assessment form."""

import streamlit as st

from config import config
from dashboard.api_client import call_service
from dashboard.incident_queue import badge, procedure_title


def _reporting_clock(detail):
    deadlines = detail["deadlines"]
    earliest = deadlines.get("earliest_milestone") or {}
    if not deadlines["milestones"]:
        st.info(config.NO_PROCEDURE_APPLIES_MESSAGE)
    for line in deadlines["milestones"]:
        with st.container(border=True):
            left, middle, right, far = st.columns([3, 3, 3, 1])
            marks = ""
            if (line["procedure_code"], line["milestone"]) == (earliest.get("procedure_code"),
                                                               earliest.get("milestone")):
                marks += " " + badge("Earliest", config.DEADLINE_EARLIEST_COLOUR)
            if line["overdue"]:
                marks += " " + badge("Overdue", config.DEADLINE_OVERDUE_COLOUR)
            left.markdown(f"**{procedure_title(line['procedure_code'])}** - {line['milestone']}"
                          f"  \n{line['authority']}{marks}")
            left.caption("Read from " + ", ".join(line["source_documents"]))
            middle.markdown(f"Within **{line['hours']} hours** of {line['clock_start_phrase']}")
            if line["clock_started"]:
                middle.caption(f"started {line['started_at']}")
                right.markdown(f"**{line['due_at_hub_time']}** hub time  \n{line['due_at']}")
                colour = config.DEADLINE_OVERDUE_COLOUR if line["overdue"] else "gray"
                far.markdown(f":{colour}[{line['hours_remaining']:.2f} h]")
            else:
                right.markdown(line["status"])
    with st.expander("Why each procedure applies"):
        for code, reason in detail["applicability"]["grounds"].items():
            st.markdown(f"**{procedure_title(code)}** - {reason}")
        if detail["applicability"]["significant_only_with_campaign"]:
            st.warning(config.CAMPAIGN_SIGNIFICANCE_MESSAGE)
        duties = detail["duties"]
        excused = ", ".join(duties["exempt_protection_states"]) or "none read"
        st.markdown(f"Customers must be told: **{'yes' if duties['customer_notice_required'] else 'no'}**"
                    f" (protection that would excuse it: {excused})")
    st.caption(f"Stored in UTC, shown in the hub's own time ({detail['deadlines']['hub_time_zone']}).")


def _incident_facts(profile):
    left, right = st.columns(2)
    with left.container(border=True):
        st.markdown("**Timeline**, as the hub recorded it")
        st.markdown(f"First alert - {profile.get('first_alert_at')}  \n"
                    f"Triage started - {profile.get('triage_started_at')}  \n"
                    f"Confirmed - {profile.get('confirmed_at') or 'awaiting confirmation'}")
    with right.container(border=True):
        st.markdown("**Systems**")
        st.markdown(f"{profile.get('affected_system_class')}, hosted in "
                    f"{profile.get('hosting_region')}  \nSystems affected - "
                    f"{profile.get('systems_affected_count')} · Internet facing - "
                    f"{profile.get('internet_facing_flag')}  \nSupplier involved - "
                    f"{profile.get('third_party_supplier_involved_flag')} · Backups - "
                    f"{profile.get('backups_available_flag')}")
    with left.container(border=True):
        st.markdown("**People and data**")
        st.markdown(f"EU data subjects - {profile.get('eu_data_subjects_count')} · Indian data "
                    f"subjects - {profile.get('india_data_subjects_count')}  \nRecords - "
                    f"{profile.get('records_affected_count')} · Customers - "
                    f"{profile.get('customers_affected_count')}  \nProtection - "
                    f"{profile.get('data_protection_state')} · MFA - "
                    f"{profile.get('mfa_enforced_flag')} · Exfiltration confirmed - "
                    f"{profile.get('exfiltration_confirmed_flag')}")
    with right.container(border=True):
        st.markdown("**Impact**")
        st.markdown(f"Outage - {profile.get('service_outage_minutes')} minutes · Direct loss - "
                    f"EUR {profile.get('direct_financial_loss_eur')}  \nAttacker still active - "
                    f"{profile.get('attacker_still_active_flag')}  \nCampaign - "
                    f"{profile.get(config.CAMPAIGN_COLUMN)}")


def _harm_and_attack(detail):
    harm, attack = detail["harm"], detail["attack"]
    left, right = st.columns(2)
    with left.container(border=True):
        st.caption("Chance the people involved are at high risk")
        st.markdown(f"## {harm['harm_probability']:.2f}")
        st.markdown(badge(harm["harm_band"] + " band",
                          config.HARM_BAND_BADGE_COLOURS[harm["harm_band"]]))
        words = lambda columns: ", ".join(config.DATA_CATEGORY_LABELS[c] for c in columns) or "none"
        st.markdown(f"Data involved - {words(harm['data_categories'])}  \nHigh-impact data - "
                    f"{words(harm['high_impact_categories'])}  \nSensitive data - "
                    f"{words(harm['sensitive_categories'])}")
    with right.container(border=True):
        st.caption("Attack named by the notes")
        st.markdown(f"## {attack['attack_type']}")
        st.markdown(f"Named by {attack['agreement']:.0%} of {attack['notes_read']} notes")
    for text, label in zip(detail["note_texts"], attack["note_attack_types"]):
        st.chat_message("assistant", avatar="📝").markdown(f"*{label}*  \n{text}")


def _effort(effort):
    columns = st.columns(4)
    columns[0].metric("Estimated by the model", f"{effort['base_hours']:.2f} h")
    columns[1].metric("Effort needed", f"{effort['effort_needed_hours']:.2f} h")
    columns[2].metric("Hours available", "-" if effort["hours_available"] is None
                      else f"{effort['hours_available']:.2f} h",
                      help=f"Hours to the earliest deadline less {config.FILING_RESERVE_HOURS} h "
                           "kept for writing and filing.")
    fits = effort["can_file_complete_in_time"]
    columns[3].metric("Complete report in time", "-" if fits is None else ("yes" if fits else "no"))
    if effort.get("deadline_message"):
        st.warning(effort["deadline_message"])
    st.caption(f"Containment is planned from {effort['containment_starts']} in the hub's time, a "
               f"{effort['weekday_started']}"
               f"{', out of hours' if effort['out_of_hours_start'] == config.BOOLEAN_YES else ''}"
               f". Assumed rather than known: {', '.join(effort['planning_assumptions'])}."
               + (f" The sensitive-data multiplier of {config.SENSITIVE_DATA_EFFORT_MULTIPLIER} "
                  "was applied." if effort["multiplier_applied"] else ""))


def _assess(reference):
    request_text = st.text_area("What do you want looked at?", key=f"ask_{reference}")
    st.caption("Five agents run, one language model call each, and the run stops for the Data "
               "Protection Officer. Nothing is filed and no customer is told until a person decides.")
    if st.button("Start the assessment", type="primary", icon=":material/play_arrow:"):
        if len(request_text.strip()) < config.ANALYST_REQUEST_MINIMUM_CHARACTERS:
            st.error(f"Write at least {config.ANALYST_REQUEST_MINIMUM_CHARACTERS} characters.")
            return
        with st.spinner("Five agents are working through the incident. Nothing will be filed."):
            record = call_service("POST", "/assessments", None,
                                  {"incident_reference": reference,
                                   "analyst_request": request_text.strip()})
        st.success(f"Assessment {record['assessment_id']} is waiting on the Decision queue. The "
                   f"agents recommend {record['recommended_disposition']}. Nothing has been filed "
                   "and no customer has been told.")
        with st.expander("What the agents wrote", expanded=True):
            st.markdown(record["assessment_text"])


def render_incident_detail_page():
    rows = call_service("GET", "/queue", {"harm_band": config.HARM_BAND_ALL}, None)
    references = [row["incident_reference"] for row in rows]
    remembered = st.session_state.get("selected_incident")
    index = references.index(remembered) if remembered in references else 0
    reference = st.selectbox("Incident", references, index=index,
                             help="The same tools the agents use produce every figure on this "
                                  "page, so what you read here is what the assessment is given.")
    if not reference:
        return
    st.session_state["selected_incident"] = reference
    detail = call_service("GET", f"/queue/{reference}", None, None)
    profile = detail["profile"]
    st.title(reference)
    st.markdown(" ".join([
        badge(f"{detail['harm']['harm_band']} harm - {detail['harm']['harm_probability']:.2f}",
              config.HARM_BAND_BADGE_COLOURS[detail["harm"]["harm_band"]]),
        badge(f"{profile.get('soc_hub')} hub", "gray"),
        badge(str(profile.get("confirmation_status")), "blue"),
        badge(str(profile.get(config.CAMPAIGN_COLUMN)), "violet"),
        badge(f"Containment: {profile.get('containment_status')}", "gray")]))
    st.caption(f"{profile.get('affected_system_class')} hosted in {profile.get('hosting_region')}"
               f" · {profile.get('attack_vector')} · detected by {profile.get('detection_source')}"
               f" · severity {profile.get('initial_severity')}")
    tabs = st.tabs(["Reporting clock", "Incident", "Harm and attack", "Effort", "Assess"])
    with tabs[0]:
        _reporting_clock(detail)
    with tabs[1]:
        _incident_facts(profile)
    with tabs[2]:
        _harm_and_attack(detail)
    with tabs[3]:
        _effort(detail["effort"])
    with tabs[4]:
        _assess(reference)
