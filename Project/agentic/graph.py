"""The order the nodes run in, the gate, the branch and the checkpoint."""

import os
import sqlite3

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, START, StateGraph

from agentic import nodes
from agentic.state import IncidentAssessmentState
from config import config


def build_workflow(checkpoint_path):
    """Assemble the ten nodes into a workflow that pauses at the gate and survives a restart."""
    graph = StateGraph(IncidentAssessmentState)
    graph.add_node("load_incident_context", nodes.load_incident_context_node)
    graph.add_node("plan_assessment", nodes.plan_assessment_node)
    graph.add_node("assess_harm", nodes.assess_harm_node)
    graph.add_node("identify_attack", nodes.identify_attack_node)
    graph.add_node("check_reporting_duties", nodes.check_reporting_duties_node)
    graph.add_node("compose_incident_assessment", nodes.compose_incident_assessment_node)
    graph.add_node("request_dpo_decision", nodes.request_dpo_decision_node)
    graph.add_node("draft_customer_notice", nodes.draft_customer_notice_node)
    graph.add_node("draft_regulator_filing", nodes.draft_regulator_filing_node)
    graph.add_node("record_incident_outcome", nodes.record_incident_outcome_node)

    graph.add_edge(START, "load_incident_context")
    graph.add_edge("load_incident_context", "plan_assessment")
    graph.add_edge("plan_assessment", "assess_harm")
    graph.add_edge("assess_harm", "identify_attack")
    graph.add_edge("identify_attack", "check_reporting_duties")
    graph.add_edge("check_reporting_duties", "compose_incident_assessment")
    graph.add_edge("compose_incident_assessment", "request_dpo_decision")
    graph.add_conditional_edges("request_dpo_decision", nodes.route_after_decision, {
        config.DECISION_RECORD_ONLY: "record_incident_outcome",
        config.DECISION_NOTIFY_REGULATOR: "draft_regulator_filing",
        config.DECISION_NOTIFY_REGULATOR_AND_CUSTOMERS: "draft_customer_notice",
    })
    graph.add_edge("draft_customer_notice", "draft_regulator_filing")
    graph.add_edge("draft_regulator_filing", "record_incident_outcome")
    graph.add_edge("record_incident_outcome", END)

    folder = os.path.dirname(checkpoint_path)
    if folder:
        os.makedirs(folder, exist_ok=True)
    checkpointer = SqliteSaver(sqlite3.connect(checkpoint_path, check_same_thread=False))
    return graph.compile(checkpointer=checkpointer)
