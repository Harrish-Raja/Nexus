"""Every read and write against the six tables, returning plain records."""

from sqlalchemy import func, select, update

from persistence.models import AgentRun, ChatTurn, DpoDecision, LlmCall, SecurityIncident, UserAccount

from config import config


def _record(instance):
    return {column.name: getattr(instance, column.name) for column in instance.__table__.columns}


def insert_user_account(session, account_record):
    session.add(UserAccount(**account_record))
    session.commit()
    return account_record["username"]


def fetch_user_account(session, condition):
    account = session.execute(select(UserAccount).where(condition)).scalars().first()
    return _record(account) if account is not None else None


def update_session_token(session, username, session_token):
    session.execute(update(UserAccount).where(UserAccount.username == username)
                    .values(session_token=session_token))
    session.commit()
    return username


def insert_agent_run(session, run_record):
    session.add(AgentRun(**run_record))
    session.commit()
    return run_record["run_id"]


def update_agent_run(session, run_id, status_value, llm_call_count):
    values = {"status": status_value, "llm_call_count": int(llm_call_count)}
    if status_value == config.AGENT_RUN_STATUS_COMPLETE:
        values["finished_at"] = func.now()
    session.execute(update(AgentRun).where(AgentRun.run_id == run_id).values(**values))
    session.commit()
    return run_id


def insert_llm_call(session, run_id, call_record):
    fields = {key: call_record[key] for key in ["agent_name", "model_name", "prompt_characters",
                                                "response_characters", "latency_milliseconds"]}
    call = LlmCall(run_id=run_id, **fields)
    session.add(call)
    session.commit()
    return call.call_id


def fetch_llm_calls(session, run_id):
    calls = session.execute(select(LlmCall).where(LlmCall.run_id == run_id)
                            .order_by(LlmCall.call_id)).scalars().all()
    return [_record(call) for call in calls]


def insert_security_incident(session, incident_record):
    session.add(SecurityIncident(**incident_record))
    session.commit()
    return incident_record["assessment_id"]


def record_incident_outcome(session, assessment_id, outcome_record):
    session.execute(update(SecurityIncident)
                    .where(SecurityIncident.assessment_id == assessment_id)
                    .values(**outcome_record))
    session.commit()
    return assessment_id


def fetch_incident_records(session, condition):
    statement = (select(SecurityIncident, AgentRun.thread_id, AgentRun.llm_call_count,
                        DpoDecision.decision, DpoDecision.decided_by, DpoDecision.decided_by_role,
                        DpoDecision.decision_reason, DpoDecision.decided_at)
                 .outerjoin(AgentRun, AgentRun.run_id == SecurityIncident.run_id)
                 .outerjoin(DpoDecision, DpoDecision.assessment_id == SecurityIncident.assessment_id)
                 .where(condition)
                 .order_by(SecurityIncident.created_at.desc(), SecurityIncident.assessment_id.desc()))
    records = []
    for row in session.execute(statement).all():
        record = _record(row[0])
        record.update({"thread_id": row[1], "llm_call_count": row[2] or 0, "decision": row[3],
                       "decided_by": row[4], "decided_by_role": row[5],
                       "decision_reason": row[6], "decided_at": row[7]})
        records.append(record)
    return records


def insert_dpo_decision(session, decision_record):
    decision = DpoDecision(**decision_record)
    session.add(decision)
    session.commit()
    return decision.decision_id


def insert_chat_turn(session, turn_record):
    turn = ChatTurn(**turn_record)
    session.add(turn)
    session.commit()
    return turn.turn_id


def fetch_chat_turns(session, condition, turn_limit):
    turns = session.execute(select(ChatTurn).where(condition)
                            .order_by(ChatTurn.turn_id.desc()).limit(int(turn_limit))
                            ).scalars().all()
    return [_record(turn) for turn in turns]
