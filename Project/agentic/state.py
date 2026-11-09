"""What the workflow carries from one node to the next."""

import operator
from typing import Annotated, Optional, TypedDict


class IncidentAssessmentState(TypedDict):
    incident_reference: str
    analyst_request: str
    analyst_id: str
    thread_id: str
    run_id: str
    assessment_id: str
    incident_profile: dict
    campaign_incidents: list
    harm_facts: dict
    attack_facts: dict
    reporting_facts: dict
    assessment_plan: dict
    harm_assessment: dict
    attack_analysis: dict
    reporting_advice: dict
    incident_assessment: dict
    dpo_decision: dict
    customer_notice: dict
    regulator_filing: dict
    filing_submitted_at: Optional[str]
    llm_call_log: Annotated[list, operator.add]
