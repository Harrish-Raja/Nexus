"""The open queue, in the order the desk should work it."""

import pandas as pd
import streamlit as st

from config import config
from dashboard.api_client import call_service


def badge(text, colour):
    return f":{colour}-badge[{text}]"


def procedure_title(code):
    return f"{code} - {config.PROCEDURE_TITLE_BY_CODE.get(code, code)}"


def render_incident_queue_page():
    st.title("Incident queue")
    st.caption(f"The live queue as extracted at {config.SNAPSHOT_AT_UTC}. Every clock runs from "
               "its own start and every hour left is measured from that moment, so the earliest "
               "running deadline is always at the top.")
    band = st.segmented_control("Harm band", [config.HARM_BAND_ALL] + config.HARM_BAND_OPTIONS,
                                default=config.HARM_BAND_ALL, key="queue_band")
    rows = call_service("GET", "/queue", {"harm_band": band or config.HARM_BAND_ALL}, None)

    running = [row for row in rows if row["earliest_milestone"]]
    overdue = [row for row in running if row["earliest_milestone"]["overdue"]]
    upcoming = [row["earliest_milestone"]["hours_remaining"] for row in running
                if not row["earliest_milestone"]["overdue"]]
    before_confirmation = [row for row in running if not row["awareness_established"]]
    columns = st.columns(5)
    columns[0].metric("Open incidents", len(rows))
    columns[1].metric("Deadline already passed", len(overdue))
    columns[2].metric("Next deadline", f"{min(upcoming):.1f} h" if upcoming else "-")
    columns[3].metric("Running before confirmation", len(before_confirmation))
    columns[4].metric("Significant through a campaign",
                      sum(1 for row in rows if row["significant_only_with_campaign"]))

    table = pd.DataFrame([{
        "Incident": row["incident_reference"],
        "Hub": row["soc_hub"],
        "Band": row["harm_band"],
        "Harm probability": row["harm_probability"],
        "Hours left": (row["earliest_milestone"]["hours_remaining"]
                       if row["earliest_milestone"] else None),
        "Earliest duty": (f"{row['earliest_milestone']['procedure_code']} - "
                          f"{row['earliest_milestone']['milestone']} to "
                          f"{row['earliest_milestone']['authority']}"
                          if row["earliest_milestone"] else "No clock running"),
        "Due, hub time": (row["earliest_milestone"]["due_at_hub_time"]
                          if row["earliest_milestone"] else ""),
        "Procedures": ", ".join(row["applicable_procedures"]) or "None",
        "Overdue": bool(row["earliest_milestone"] and row["earliest_milestone"]["overdue"]),
        "Awaiting confirmation": not row["awareness_established"],
    } for row in rows])
    if table.empty:
        st.info("No incident in this band.")
        return
    selection = st.dataframe(
        table, hide_index=True, width="stretch", on_select="rerun",
        selection_mode="single-row", key="queue_table",
        column_config={"Harm probability": st.column_config.ProgressColumn(
            min_value=0.0, max_value=1.0, format="%.2f"),
            "Hours left": st.column_config.NumberColumn(format="%.2f h")})
    st.caption(f"{len(table)} incidents shown. Select a row to take it to the incident detail "
               "page. Incidents with no running clock come last, highest harm first.")
    chosen = selection.selection.rows if selection and selection.selection else []
    if chosen:
        st.session_state["selected_incident"] = table.iloc[chosen[0]]["Incident"]
        st.success(f"{st.session_state['selected_incident']} will open on the Incident detail page.")
