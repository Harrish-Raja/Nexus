"""The assessments waiting at the gate, and the Data Protection Officer's decision form."""

import pandas as pd
import streamlit as st

from config import config
from dashboard.api_client import call_service
from dashboard.incident_queue import badge


def _cost_note():
    parts = []
    for decision in config.DECISION_OPTIONS:
        extra = config.LLM_CALLS_BY_DECISION[decision] - config.LLM_CALLS_BEFORE_DECISION
        parts.append(f"{decision} costs {extra} more model call{'s' if extra != 1 else ''}")
    return "; ".join(parts) + ". The reason is kept and open to inspection."


def render_decision_queue_page():
    st.title("Decision queue")
    pending = call_service("GET", "/incidents",
                           {"status_value": [config.INCIDENT_STATUS_PENDING]}, None)
    if not pending:
        st.info("No assessment is waiting for a decision.")
        return
    table = pd.DataFrame([{"Assessment": record["assessment_id"],
                           "Incident": record["incident_reference"], "Hub": record["soc_hub"],
                           "Band": record["harm_band"],
                           "Recommended": record["recommended_disposition"],
                           "Earliest deadline, UTC": record["earliest_deadline_at"] or "No clock",
                           "Hours left": record["hours_remaining"],
                           "Opened, UTC": record["created_at"]} for record in pending])
    selection = st.dataframe(table, hide_index=True, width="stretch", on_select="rerun",
                             selection_mode="single-row", key="decision_table")
    chosen = selection.selection.rows if selection and selection.selection else []
    record = pending[chosen[0]] if chosen else pending[0]

    left, right = st.columns([3, 2])
    with left:
        st.subheader(f"{record['incident_reference']} · {record['assessment_id']}")
        st.markdown(" ".join([
            badge(f"{record['harm_band']} harm - {record['harm_probability']:.2f}",
                  config.HARM_BAND_BADGE_COLOURS[record["harm_band"]]),
            badge(record["attack_type"], "gray"),
            badge("Recommended: " + record["recommended_disposition"],
                  config.DECISION_BADGE_COLOURS[record["recommended_disposition"]])]))
        st.markdown(record["assessment_text"])
        with st.container(border=True):
            st.markdown(f"Procedures - **{record['applicable_procedures'] or 'none'}**")
            if record["earliest_procedure"]:
                st.markdown(f"Earliest deadline - **{record['earliest_procedure']}, due "
                            f"{record['earliest_deadline_at']}, {record['hours_remaining']:.2f} "
                            "hours from the queue snapshot**")
            fits = record["can_file_complete_in_time"]
            st.markdown(f"Effort needed - **{record['effort_needed_hours']:.2f} hours**, complete "
                        f"report in time - **{'-' if fits is None else ('yes' if fits else 'no')}**")
            st.markdown("Customers must be told under Procedure 01 - "
                        f"**{'yes' if record['customer_notice_required'] else 'no'}**")
        with st.expander("What the analyst asked, and what the planner decided to check"):
            st.markdown(f"**The analyst asked**  \n{record['analyst_request']}")
            st.markdown(f"**The plan**  \n{record['assessment_plan_text']}")
    with right.container(border=True):
        st.markdown("**Your decision**")
        with st.form(f"decide_{record['assessment_id']}"):
            decision = st.radio("Disposition", config.DECISION_OPTIONS,
                                label_visibility="collapsed")
            reason = st.text_area("Your reason, in your own words")
            st.caption(_cost_note())
            submitted = st.form_submit_button("Record the decision", type="primary",
                                              width="stretch")
        if submitted:
            if len(reason.strip()) < config.DECISION_REASON_MINIMUM_CHARACTERS:
                st.error(f"Give a reason of at least {config.DECISION_REASON_MINIMUM_CHARACTERS} "
                         "characters.")
                return
            with st.spinner("Recording the decision and drafting what it calls for."):
                final = call_service("POST", f"/incidents/{record['assessment_id']}"
                                     f"{config.DECISION_PATH_ENDING}", None,
                                     {"decision": decision, "decision_reason": reason.strip()})
            st.success(f"{final['decision']} recorded. The incident now stands at "
                       f"{final['status']}.")
            if final["customer_notice_text"]:
                with st.expander("Customer notice"):
                    st.markdown(final["customer_notice_text"])
            if final["regulator_filing_text"]:
                with st.expander("Regulator filing"):
                    st.markdown(final["regulator_filing_text"])
            if final["final_report_due_at"]:
                st.info(f"Final report due {final['final_report_due_at']}.")
