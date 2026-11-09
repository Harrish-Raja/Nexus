"""What has been decided, the record behind each decision, and every chat question."""

import pandas as pd
import streamlit as st

from config import config
from dashboard.api_client import call_service
from dashboard.incident_queue import badge

_DECIDED = [status for status in config.INCIDENT_STATUS_OPTIONS
            if status != config.INCIDENT_STATUS_PENDING]


def _decided_incidents():
    decided = call_service("GET", "/incidents", {"status_value": _DECIDED}, None)
    columns = st.columns(1 + len(config.DECISION_OPTIONS))
    columns[0].metric("Decided", len(decided))
    for column, decision in zip(columns[1:], config.DECISION_OPTIONS):
        column.metric(decision.capitalize(),
                      sum(1 for record in decided if record["decision"] == decision))
    if not decided:
        st.info("Nothing has been decided yet.")
        return
    table = pd.DataFrame([{"Incident": record["incident_reference"], "Hub": record["soc_hub"],
                           "Band": record["harm_band"],
                           "Recommended": record["recommended_disposition"],
                           "Decided": record["decision"], "By": record["decided_by"],
                           "Filed, UTC": record["filing_submitted_at"] or "None",
                           "Final report due, UTC": record["final_report_due_at"] or "None",
                           "Status": record["status"]} for record in decided])
    selection = st.dataframe(table, hide_index=True, width="stretch", on_select="rerun",
                             selection_mode="single-row", key="audit_table")
    st.caption("Select a row to open its record: the decision, both documents and every "
               "language model call the run made.")
    chosen = selection.selection.rows if selection and selection.selection else []
    if not chosen:
        return
    record = decided[chosen[0]]
    st.subheader(f"{record['incident_reference']} · {record['assessment_id']}")
    st.markdown(badge(record["decision"], config.DECISION_BADGE_COLOURS[record["decision"]])
                + f" by {record['decided_by']} ({record['decided_by_role']}) at "
                  f"{record['decided_at']}")
    st.markdown(f"**Reason** - {record['decision_reason']}")
    if record["decision"] != record["recommended_disposition"]:
        st.warning(f"The officer decided {record['decision']} where the agents recommended "
                   f"{record['recommended_disposition']}. That is the decision the Incident "
                   "Response Plan reserves to a person.")
    if record["customer_notice_text"]:
        with st.expander("Customer notice"):
            st.markdown(record["customer_notice_text"])
    if record["regulator_filing_text"]:
        with st.expander("Regulator filing"):
            st.markdown(record["regulator_filing_text"])
    budget = call_service("GET", f"/incidents/{record['assessment_id']}/calls", None, None)
    verdict = ("as expected" if budget["call_count"] == budget["expected_call_count"]
               else "NOT as expected")
    st.markdown(f"**Model calls** - {budget['call_count']} made, {budget['expected_call_count']} "
                f"expected for this path ({verdict}); {budget['total_latency_milliseconds']} ms "
                "in all.")
    st.dataframe(pd.DataFrame(budget["calls"]), hide_index=True, width="stretch")


def _chat_log():
    turns = call_service("GET", "/audit/chat-turns",
                         {"turn_limit": config.CHAT_AUDIT_RECENT_ROWS}, None)
    refused = sum(1 for turn in turns if turn["was_refused"])
    st.caption(f"The {len(turns)} most recent questions, newest first. {refused} were refused.")
    st.dataframe(pd.DataFrame([{"Asked, UTC": turn["asked_at"],
                                "Who": f"{turn['username']} ({turn['user_role']})",
                                "Kind": turn["question_type"],
                                "Incident": turn["incident_reference"] or "None",
                                "Refused": turn["was_refused"], "Question": turn["question_text"],
                                "Answer": turn["answer_text"], "From": turn["source_documents"]}
                               for turn in turns]), hide_index=True, width="stretch")


def render_audit_trail_page():
    st.title("Audit trail")
    decided_tab, chat_tab = st.tabs(["Decided incidents", "Response assistant log"])
    with decided_tab:
        _decided_incidents()
    with chat_tab:
        _chat_log()
