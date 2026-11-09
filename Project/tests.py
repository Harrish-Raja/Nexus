import pytest


@pytest.fixture(scope="session")
def processed_frames():
    import pandas as pd

    from config import config

    loaded = {"problem": None}
    try:
        for path in [config.CLEAN_INCIDENTS_TRAIN_FILE, config.CLEAN_INCIDENTS_EVAL_FILE,
                     config.CLEAN_EFFORT_TRAIN_FILE, config.CLEAN_EFFORT_EVAL_FILE,
                     config.CLEAN_INCIDENT_NOTES_FILE]:
            loaded[path] = pd.read_csv(path, low_memory=False)
    except (Exception, SystemExit) as error:
        loaded["problem"] = (
            "The cleaned extracts could not be read ("
            + type(error).__name__
            + ": "
            + str(error)[:300]
            + "). Every check on cleaning, features and models reads the files the data "
            "pipeline writes, so the pipeline has to have run and written all of them."
        )
    return loaded


@pytest.fixture(scope="session")
def raw_frames():
    import pandas as pd

    from config import config

    loaded = {"problem": None}
    try:
        for path in [config.RAW_INCIDENTS_TRAIN_FILE, config.RAW_INCIDENTS_EVAL_FILE,
                     config.RAW_EFFORT_TRAIN_FILE, config.RAW_EFFORT_EVAL_FILE,
                     config.RAW_INCIDENT_NOTES_FILE]:
            loaded[path] = pd.read_csv(path, dtype=str)
    except (Exception, SystemExit) as error:
        loaded["problem"] = (
            "The raw extracts supplied with the project could not be read ("
            + type(error).__name__
            + ": "
            + str(error)[:300]
            + "). The data folder has to stay as it was supplied."
        )
    return loaded


@pytest.fixture(scope="session")
def saved_models():
    from config import config

    loaded = {"problem": None}
    try:
        from modeling.model_registry import load_feature_schema, load_model

        loaded.update({
            "harm": load_model(config.HARM_MODEL_FILE),
            "effort": load_model(config.EFFORT_MODEL_FILE),
            "attack": load_model(config.ATTACK_MODEL_FILE),
            "harm_schema": list(load_feature_schema(config.HARM_SCHEMA_FILE)),
            "effort_schema": list(load_feature_schema(config.EFFORT_SCHEMA_FILE)),
        })
    except (Exception, SystemExit) as error:
        loaded["problem"] = (
            "The saved models and their feature schemas could not be loaded ("
            + type(error).__name__
            + ": "
            + str(error)[:300]
            + "). Model training saves them, and every check on the models scores what "
            "training saved."
        )
    return loaded


@pytest.fixture(scope="session")
def open_queue():
    from config import config

    loaded = {"problem": None}
    try:
        from data_pipeline.dataset_loader import load_processed_dataset

        loaded.update({
            "incidents": load_processed_dataset(config.OPEN_INCIDENTS_FILE),
            "notes": load_processed_dataset(config.OPEN_INCIDENT_NOTES_FILE),
        })
    except (Exception, SystemExit) as error:
        loaded["problem"] = (
            "The live queue could not be loaded ("
            + type(error).__name__
            + ": "
            + str(error)[:300]
            + "). The tools, the queue and the workflow all start from the open incidents "
            "and their notes."
        )
    return loaded


@pytest.fixture(scope="session")
def knowledge_collection():
    from config import config

    opened = {"problem": None}
    try:
        from knowledge.vector_index import open_vector_index

        opened["collection"] = open_vector_index(config.VECTOR_STORE_DIRECTORY,
                                                 config.VECTOR_COLLECTION_NAME)
    except (Exception, SystemExit) as error:
        opened["problem"] = (
            "The vector store could not be opened ("
            + type(error).__name__
            + ": "
            + str(error)[:300]
            + "). Knowledge indexing builds it, and every check on retrieval and on the "
            "procedures searches it."
        )
    return opened


@pytest.fixture(scope="session")
def planted_collection(tmp_path_factory):
    from config import config

    phrase_by_column = {column: phrase
                        for phrase, column in config.CLOCK_START_COLUMN_BY_PHRASE.items()}
    alert = phrase_by_column[config.FIRST_ALERT_COLUMN]
    aware = phrase_by_column[config.AWARENESS_COLUMN]
    word_by_months = {months: word for word, months in config.MONTHS_BY_WORD.items()}
    eu = config.PROCEDURE_EU_PERSONAL_DATA_BREACH
    significant = config.PROCEDURE_SIGNIFICANT_INCIDENT
    india = config.PROCEDURE_INDIA_CYBER_INCIDENT
    planted = {
        "problem": None,
        "milestones": {eu: [("checkpoint amber", 19, alert)],
                       significant: [("checkpoint blue", 7, aware),
                                     ("checkpoint cyan", 41, alert)],
                       india: [("checkpoint dune", 3, aware)]},
        "filed": {eu: [("closing amber", 3, "checkpoint amber")], significant: [], india: []},
        "exempt": {eu: [config.VALID_PROTECTION_STATES[3], config.VALID_PROTECTION_STATES[4]],
                   significant: [config.VALID_PROTECTION_STATES[0]], india: []},
    }
    records = []
    for code in config.PROCEDURE_OPTIONS:
        sentences = ["The " + name + " is due within " + str(hours) + " hours of " + phrase + "."
                     for name, hours, phrase in planted["milestones"][code]]
        sentences += ["The " + name + " is due " + word_by_months[months] + " months after the "
                      + after + " is filed." for name, months, after in planted["filed"][code]]
        sentences += [" ".join("Customers need not be told where the data protection state is "
                               + state + "." for state in planted["exempt"][code])]
        sentences += ["The desk keeps a record of every report it files.",
                      "Each report names the hub that raised it."]
        passages = [sentence for sentence in sentences if sentence.strip()][:3]
        for position, passage in enumerate(passages):
            records.append({"chunk_id": "planted-" + code + "-" + str(position),
                            "chunk_text": passage,
                            "document_name": config.PROCEDURE_DOCUMENT_BY_CODE[code]})
    try:
        from knowledge.vector_index import build_vector_index, open_vector_index

        store = str(tmp_path_factory.mktemp("planted") / "store")
        build_vector_index(records, store, "planted_passages")
        planted["collection"] = open_vector_index(store, "planted_passages")
    except (Exception, SystemExit) as error:
        planted["problem"] = (
            "A small store of invented procedure passages could not be built and opened with "
            "build_vector_index and open_vector_index ("
            + type(error).__name__
            + ": "
            + str(error)[:300]
            + ")."
        )
    return planted


@pytest.fixture
def invented_readings():
    from config import config

    phrase_by_column = {column: phrase
                        for phrase, column in config.CLOCK_START_COLUMN_BY_PHRASE.items()}
    from_alert = {"clock_start_phrase": phrase_by_column[config.FIRST_ALERT_COLUMN],
                  "clock_start_column": config.FIRST_ALERT_COLUMN}
    from_awareness = {"clock_start_phrase": phrase_by_column[config.AWARENESS_COLUMN],
                      "clock_start_column": config.AWARENESS_COLUMN}
    return {
        config.PROCEDURE_EU_PERSONAL_DATA_BREACH: {
            "milestones": [dict(from_alert, milestone="checkpoint amber", hours=30)],
            "filed_milestones": [{"milestone": "closing amber", "months": 2,
                                  "after_milestone": "checkpoint amber"}],
            "source_documents": [
                config.PROCEDURE_DOCUMENT_BY_CODE[config.PROCEDURE_EU_PERSONAL_DATA_BREACH]],
            "passages": [],
        },
        config.PROCEDURE_SIGNIFICANT_INCIDENT: {
            "milestones": [dict(from_awareness, milestone="checkpoint blue", hours=12),
                           dict(from_alert, milestone="checkpoint cyan", hours=50)],
            "filed_milestones": [],
            "source_documents": [
                config.PROCEDURE_DOCUMENT_BY_CODE[config.PROCEDURE_SIGNIFICANT_INCIDENT]],
            "passages": [],
        },
        config.PROCEDURE_INDIA_CYBER_INCIDENT: {
            "milestones": [dict(from_awareness, milestone="checkpoint dune", hours=4)],
            "filed_milestones": [],
            "source_documents": [
                config.PROCEDURE_DOCUMENT_BY_CODE[config.PROCEDURE_INDIA_CYBER_INCIDENT]],
            "passages": [],
        },
    }


@pytest.fixture(scope="session")
def service_client():
    service = {"problem": None}
    try:
        from fastapi.testclient import TestClient

        from api.routes import service_application

        client = TestClient(service_application, raise_server_exceptions=False)
        client.__enter__()
        service["client"] = client
    except (Exception, SystemExit) as error:
        service["problem"] = (
            "The REST service could not be started ("
            + type(error).__name__
            + ": "
            + str(error)[:300]
            + "). Every check on sign-in, access, the queue, the workflow and the chat goes "
            "through it."
        )
    yield service
    if "client" in service:
        try:
            service["client"].__exit__(None, None, None)
        except (Exception, SystemExit):
            pass


@pytest.fixture(scope="session")
def staff(service_client):
    from config import config

    signed_in = {"problem": service_client["problem"]}
    if signed_in["problem"] is not None:
        return signed_in
    try:
        for account in config.SEED_USER_ACCOUNTS:
            if account["role"] in signed_in:
                continue
            reply = service_client["client"].post(
                "/auth/signin",
                json={"username": account["username"], "password": account["password"]})
            assert reply.status_code == 200, (
                "Signing in as "
                + account["username"]
                + " with the password the configuration seeds returned "
                + str(reply.status_code)
                + ", so no check that needs a signed-in "
                + account["role"]
                + " can run."
            )
            signed_in[account["role"]] = {
                "username": account["username"],
                "display_name": reply.json()["display_name"],
                "headers": {config.SESSION_TOKEN_HEADER: reply.json()["session_token"]},
            }
    except (Exception, SystemExit) as error:
        signed_in["problem"] = (
            "The seeded staff could not be signed in ("
            + type(error).__name__
            + ": "
            + str(error)[:400]
            + "). Run the database setup so the seeded accounts exist."
        )
    return signed_in


@pytest.fixture(scope="session")
def saved_run(service_client, staff, open_queue):
    from config import config

    run = {"problem": service_client["problem"] or staff["problem"] or open_queue["problem"],
           "decision_problem": None}
    if run["problem"] is not None:
        return run
    client = service_client["client"]
    analyst = staff[config.ROLE_ANALYST]
    officer = staff[config.ROLE_DPO]
    run["analyst_request"] = "What must we report, to whom and by when, and must customers be told?"
    run["decision"] = config.DECISION_NOTIFY_REGULATOR_AND_CUSTOMERS
    run["decision_reason"] = ("The data taken puts the people it belongs to at high risk, so the "
                              "authorities and the customers are both told.")
    run["officer_name"] = officer["display_name"]
    for name in ["detail", "calls_at_gate", "pending_at_gate", "final_calls"]:
        run[name] = {"status": None, "body": "never requested"}
    run["run_record"] = {"problem": "never read"}
    try:
        queue = client.get("/queue", params={"harm_band": config.HARM_BAND_ALL},
                           headers=analyst["headers"])
        assert queue.status_code == 200, (
            "The incident queue returned "
            + str(queue.status_code)
            + " to a signed-in analyst, so no incident could be chosen to assess."
        )
        campaigns = dict(zip(open_queue["incidents"]["incident_reference"],
                             open_queue["incidents"][config.CAMPAIGN_COLUMN]))
        ranked = sorted(
            (bool(row["earliest_milestone"]["overdue"]), -len(row["applicable_procedures"]),
             campaigns.get(row["incident_reference"]) == config.NO_CAMPAIGN_VALUE, position,
             row["incident_reference"])
            for position, row in enumerate(queue.json())
            if config.PROCEDURE_SIGNIFICANT_INCIDENT in row["applicable_procedures"]
            and row["earliest_milestone"] is not None)
        assert len(ranked) > 0, (
            "No incident in the queue has "
            + config.PROCEDURE_SIGNIFICANT_INCIDENT
            + " applying to it and a running clock. The live queue holds many, so the queue "
            "is not working out which procedures apply or which clocks are running."
        )
        run["reference"] = ranked[0][-1]
        try:
            reply = client.get("/queue/" + run["reference"], headers=analyst["headers"])
            run["detail"] = {"status": reply.status_code, "body": reply.json()}
        except (Exception, SystemExit) as error:
            run["detail"]["body"] = type(error).__name__ + ": " + str(error)[:300]

        opened = client.post(
            "/assessments",
            json={"incident_reference": run["reference"],
                  "analyst_request": run["analyst_request"]},
            headers=analyst["headers"])
        assert opened.status_code == 201, (
            "Opening an assessment on "
            + run["reference"]
            + " returned "
            + str(opened.status_code)
            + " with "
            + opened.text[:300]
            + ", so the workflow never reached the Data Protection Officer."
        )
        run["at_gate"] = opened.json()
        assessment_id = run["at_gate"]["assessment_id"]
    except (Exception, SystemExit) as error:
        run["problem"] = (
            "The one assessment run that the agent, workflow and record checks read could "
            "not be opened ("
            + type(error).__name__
            + ": "
            + str(error)[:600]
            + ")."
        )
        return run

    try:
        reply = client.get("/incidents/" + assessment_id + "/calls", headers=analyst["headers"])
        run["calls_at_gate"] = {"status": reply.status_code, "body": reply.json()}
    except (Exception, SystemExit) as error:
        run["calls_at_gate"]["body"] = type(error).__name__ + ": " + str(error)[:300]
    try:
        reply = client.get("/incidents", params={"status_value": [config.INCIDENT_STATUS_PENDING]},
                           headers=analyst["headers"])
        run["pending_at_gate"] = {"status": reply.status_code, "body": reply.json()}
    except (Exception, SystemExit) as error:
        run["pending_at_gate"]["body"] = type(error).__name__ + ": " + str(error)[:300]
    try:
        from persistence.database import SessionFactory
        from persistence.models import AgentRun

        with SessionFactory() as session:
            run["run_record"] = {"problem": None,
                                 "status_at_gate": session.get(AgentRun,
                                                               run["at_gate"]["run_id"]).status}
    except (Exception, SystemExit) as error:
        run["run_record"] = {"problem": ("The agent run of the paused assessment could not be "
                                         "read from the database (" + type(error).__name__
                                         + ": " + str(error)[:300] + ").")}

    try:
        decided = client.post(
            "/incidents/" + assessment_id + config.DECISION_PATH_ENDING,
            json={"decision": run["decision"], "decision_reason": run["decision_reason"]},
            headers=officer["headers"])
        assert decided.status_code == 200, (
            "Recording the decision on "
            + assessment_id
            + " returned "
            + str(decided.status_code)
            + " with "
            + decided.text[:300]
            + ", so the paused run was never resumed."
        )
        run["final"] = decided.json()
    except (Exception, SystemExit) as error:
        run["decision_problem"] = (
            "The Data Protection Officer's decision on the one assessment run could not be "
            "recorded ("
            + type(error).__name__
            + ": "
            + str(error)[:600]
            + ")."
        )
        return run

    try:
        reply = client.get("/incidents/" + assessment_id + "/calls", headers=analyst["headers"])
        run["final_calls"] = {"status": reply.status_code, "body": reply.json()}
    except (Exception, SystemExit) as error:
        run["final_calls"]["body"] = type(error).__name__ + ": " + str(error)[:300]
    if run["run_record"]["problem"] is None:
        try:
            with SessionFactory() as session:
                finished_run = session.get(AgentRun, run["at_gate"]["run_id"])
                run["run_record"].update({"status_final": finished_run.status,
                                          "thread_id": finished_run.thread_id})
        except (Exception, SystemExit) as error:
            run["run_record"]["problem"] = (
                "The agent run of the finished assessment could not be read from the database ("
                + type(error).__name__ + ": " + str(error)[:300] + ").")
    return run


@pytest.fixture(scope="session")
def chat_replies(service_client, staff, saved_run):
    from config import config

    replies = {"problem": service_client["problem"] or staff["problem"],
               "procedure_question": ("Who decides whether a regulator and the customers must "
                                      "be told about an incident?"),
               "procedure": {"status": None, "body": "never asked"},
               "turns": {"status": None, "body": "never read"},
               "status": {"status": None, "body": "never asked"},
               "status_problem": saved_run["problem"] or saved_run["decision_problem"]}
    if replies["problem"] is not None:
        return replies
    client = service_client["client"]
    analyst = staff[config.ROLE_ANALYST]
    replies["analyst"] = analyst["username"]
    try:
        reply = client.post("/chat/ask", json={"question": replies["procedure_question"]},
                            headers=analyst["headers"])
        replies["procedure"] = {"status": reply.status_code, "body": reply.json()}
    except (Exception, SystemExit) as error:
        replies["procedure"]["body"] = type(error).__name__ + ": " + str(error)[:300]
    try:
        reply = client.get("/chat/turns", params={"turn_limit": 5}, headers=analyst["headers"])
        replies["turns"] = {"status": reply.status_code, "body": reply.json()}
    except (Exception, SystemExit) as error:
        replies["turns"]["body"] = type(error).__name__ + ": " + str(error)[:300]
    if replies["status_problem"] is None:
        try:
            reply = client.post(
                "/chat/ask",
                json={"question": "What is the status of incident " + saved_run["reference"] + "?"},
                headers=staff[config.ROLE_COMMUNICATIONS]["headers"])
            replies["status"] = {"status": reply.status_code, "body": reply.json()}
        except (Exception, SystemExit) as error:
            replies["status"]["body"] = type(error).__name__ + ": " + str(error)[:300]
    return replies


def test_cleaning_keeps_one_complete_row_for_every_record(raw_frames, processed_frames,
                                                          tmp_path):
    import pandas as pd

    from config import config
    from data_pipeline.effort_cleaning import clean_effort_dataset

    assert raw_frames["problem"] is None, raw_frames["problem"]
    assert processed_frames["problem"] is None, processed_frames["problem"]
    rebuilt_path = str(tmp_path / "effort_eval_cleaned_again.csv")
    clean_effort_dataset(config.RAW_EFFORT_EVAL_FILE, rebuilt_path)
    rebuilt = pd.read_csv(rebuilt_path, low_memory=False)
    saved = processed_frames[config.CLEAN_EFFORT_EVAL_FILE]
    assert rebuilt.shape == saved.shape and rebuilt.equals(saved), (
        "Cleaning "
        + config.RAW_EFFORT_EVAL_FILE
        + " again gives "
        + str(rebuilt.shape)
        + " rows and columns where "
        + config.CLEAN_EFFORT_EVAL_FILE
        + " holds "
        + str(saved.shape)
        + ", or the same shape with different values. Every check reads the cleaned files, "
        "so they have to be what the cleaning code produces now: run the data pipeline "
        "again after changing it."
    )
    datasets = [
        (config.RAW_INCIDENTS_TRAIN_FILE, config.CLEAN_INCIDENTS_TRAIN_FILE,
         config.INCIDENT_IDENTIFIER_COLUMNS[0], config.INCIDENT_TARGET_COLUMN),
        (config.RAW_INCIDENTS_EVAL_FILE, config.CLEAN_INCIDENTS_EVAL_FILE,
         config.INCIDENT_IDENTIFIER_COLUMNS[0], config.INCIDENT_TARGET_COLUMN),
        (config.RAW_EFFORT_TRAIN_FILE, config.CLEAN_EFFORT_TRAIN_FILE,
         config.EFFORT_IDENTIFIER_COLUMNS[0], config.EFFORT_TARGET_COLUMN),
        (config.RAW_EFFORT_EVAL_FILE, config.CLEAN_EFFORT_EVAL_FILE,
         config.EFFORT_IDENTIFIER_COLUMNS[0], config.EFFORT_TARGET_COLUMN),
        (config.RAW_INCIDENT_NOTES_FILE, config.CLEAN_INCIDENT_NOTES_FILE,
         "note_id", config.NOTE_TARGET_COLUMN),
    ]
    null_tokens = {token.strip().lower() for token in config.NULL_TOKEN_LIST}
    for raw_path, clean_path, identifier, target in datasets:
        raw_frame = raw_frames[raw_path]
        clean_frame = processed_frames[clean_path]

        given = raw_frame[target].fillna("").str.strip()
        unanswered = given.eq("") | given.str.lower().isin(null_tokens)
        never_answered = (set(raw_frame.loc[unanswered, identifier].fillna("").str.strip())
                          - set(raw_frame.loc[~unanswered, identifier].fillna("").str.strip()))
        kept_unanswered = sorted(never_answered & set(clean_frame[identifier].astype(str)))
        assert len(never_answered) > 0 and len(kept_unanswered) == 0, (
            clean_path
            + " keeps "
            + str(len(kept_unanswered))
            + " records whose answer "
            + raw_path
            + " never gives, for example "
            + str(kept_unanswered[:3])
            + ". A record with no answer is removed, never given an invented one: a model "
            "fitted on invented answers learns the invention."
        )
        assert len(clean_frame) < len(raw_frame), (
            clean_path
            + " keeps "
            + str(len(clean_frame))
            + " rows of the "
            + str(len(raw_frame))
            + " in "
            + raw_path
            + ". The extract carries repeated rows and rows with no answer, so nothing "
            "has been removed that should have been."
        )
        repeated = int(clean_frame[identifier].duplicated().sum())
        assert repeated == 0, (
            clean_path
            + " still holds "
            + str(repeated)
            + " rows whose "
            + identifier
            + " appears on another row. A record counted twice is weighted twice by "
            "every model fitted on it."
        )
        empty = int(clean_frame.isna().sum().sum())
        assert empty == 0, (
            clean_path
            + " still holds "
            + str(empty)
            + " empty cells. A model cannot be fitted on holes, and an estimator that "
            "drops them quietly is fitted on less than it was given."
        )
        assert clean_frame[target].nunique() > 1, (
            "The answer column "
            + target
            + " in "
            + clean_path
            + " holds a single value, so there is nothing for a model to learn."
        )

    for clean_path in [config.CLEAN_INCIDENTS_TRAIN_FILE, config.CLEAN_INCIDENTS_EVAL_FILE]:
        answers = sorted(processed_frames[clean_path][config.INCIDENT_TARGET_COLUMN].unique())
        assert answers == [0, 1], (
            config.INCIDENT_TARGET_COLUMN
            + " in "
            + clean_path
            + " holds "
            + str(answers[:6])
            + " where a classifier needs 1 for an incident that put people at high risk "
            "and 0 for one that did not."
        )


def test_one_instant_written_every_way_cleans_to_the_same_utc_time(processed_frames):
    import datetime

    import pandas as pd

    from config import config
    from data_pipeline.common_cleaning import (format_timestamps_as_text,
                                               parse_mixed_format_timestamps)

    assert processed_frames["problem"] is None, processed_frames["problem"]
    iso_format, numeric_zone_format, named_zone_format = config.TIMESTAMP_FORMAT_LIST
    instant = pd.Timestamp(config.SNAPSHOT_AT_UTC) - pd.Timedelta(hours=37, minutes=25)
    written = [str(int(instant.timestamp())),
               instant.strftime(iso_format.replace("%z", "")) + config.ISO_UTC_SUFFIX]
    for abbreviation, offset_text in config.TIMEZONE_ABBREVIATION_OFFSETS.items():
        sign = -1 if offset_text.startswith("-") else 1
        hours, minutes = offset_text[1:].split(":")
        zone = datetime.timezone(sign * datetime.timedelta(hours=int(hours),
                                                           minutes=int(minutes)))
        local = instant.tz_convert(zone)
        written.append(local.strftime(numeric_zone_format.replace("%z", "")) + offset_text)
        written.append(local.strftime(named_zone_format.replace("%z", "")) + abbreviation)

    frame = pd.DataFrame({config.FIRST_ALERT_COLUMN: written + [None]})
    parsed = parse_mixed_format_timestamps(frame, [config.FIRST_ALERT_COLUMN])
    cleaned = format_timestamps_as_text(parsed, [config.FIRST_ALERT_COLUMN])
    stored = list(cleaned[config.FIRST_ALERT_COLUMN])
    expected = instant.strftime(config.OUTPUT_TIMESTAMP_FORMAT)

    wrong = [(given, produced) for given, produced in zip(written, stored[:-1])
             if produced != expected]
    assert len(wrong) == 0, (
        "The same moment, "
        + expected
        + ", written "
        + str(len(written))
        + " ways, cleaned to something else "
        + str(len(wrong))
        + " times, for example "
        + str(wrong[:3])
        + ". Epoch seconds, an offset and a zone abbreviation are three notations for one "
        "instant, and a deadline counted from the wrong instant is wrong by the offset."
    )
    assert pd.isna(stored[-1]) or str(stored[-1]).strip() == "", (
        "An empty timestamp came back as "
        + repr(stored[-1])
        + ". A moment nobody recorded stays empty; inventing one starts a reporting "
        "clock that never started."
    )

    for path, columns in [(config.CLEAN_INCIDENTS_TRAIN_FILE, config.INCIDENT_TIMESTAMP_COLUMNS),
                          (config.CLEAN_INCIDENT_NOTES_FILE, config.NOTE_TIMESTAMP_COLUMNS)]:
        for column_name in columns:
            values = processed_frames[path][column_name].astype(str)
            unreadable = int(pd.to_datetime(values, format=config.OUTPUT_TIMESTAMP_FORMAT,
                                            errors="coerce").isna().sum())
            assert unreadable == 0, (
                column_name
                + " in "
                + path
                + " has "
                + str(unreadable)
                + " values not written as "
                + config.OUTPUT_TIMESTAMP_FORMAT
                + ", so the processed file still mixes notations."
            )


def test_counts_amounts_and_durations_written_as_text_become_numbers():
    import pandas as pd

    from data_pipeline.common_cleaning import (convert_durations_to_hours,
                                               convert_durations_to_minutes,
                                               convert_money_amounts, convert_written_counts)

    count_cases = [("1,20,637", 120637), ("118,500", 118500), ("42", 42),
                   ("1.185 lakh", 118500), ("8.7k", 8700), (None, None)]
    money_cases = [("€105,114", 105114.0), ("EUR 178495", 178495.0), ("3400", 3400.0),
                   (None, None)]
    minute_cases = [("28h 01m", 1681.0), ("5 h", 300.0), ("276 min", 276.0), ("45", 45.0),
                    (None, None)]
    hour_cases = [("3h 15m", 3.25), ("7.5 h", 7.5), ("225 min", 3.75), ("3.25", 3.25),
                  (None, None)]

    for converter, column_name, cases in [
            (convert_written_counts, "customers_affected_count", count_cases),
            (convert_money_amounts, "direct_financial_loss_eur", money_cases),
            (convert_durations_to_minutes, "service_outage_minutes", minute_cases),
            (convert_durations_to_hours, "containment_hours", hour_cases)]:
        frame = pd.DataFrame({column_name: [written for written, _ in cases]})
        produced = list(converter(frame, [column_name])[column_name])
        for (written, wanted), value in zip(cases, produced):
            if wanted is None:
                assert pd.isna(value), (
                    converter.__name__
                    + " turned an empty "
                    + column_name
                    + " into "
                    + repr(value)
                    + ". A figure nobody recorded is not nought."
                )
            else:
                assert value == pytest.approx(wanted), (
                    converter.__name__
                    + " read "
                    + repr(written)
                    + " as "
                    + repr(value)
                    + " where it means "
                    + str(wanted)
                    + ". The hubs write the same quantity with digit groups, a lakh or a "
                    "thousand suffix, a currency marker or a unit, and every one of them "
                    "is a number a threshold is compared against."
                )


def test_every_spelling_is_folded_onto_a_value_the_company_uses(processed_frames):
    import pandas as pd

    from config import config
    from data_pipeline.common_cleaning import (normalize_boolean_columns,
                                               normalize_category_column,
                                               replace_missing_tokens, restrict_to_known_values)

    assert processed_frames["problem"] is None, processed_frames["problem"]
    for column_name, mapping, recognised in [
            ("soc_hub", config.HUB_MAPPING, config.VALID_HUBS),
            ("hosting_region", config.HOSTING_REGION_MAPPING, config.VALID_HOSTING_REGIONS),
            ("data_protection_state", config.PROTECTION_STATE_MAPPING,
             config.VALID_PROTECTION_STATES),
            ("attack_type", config.ATTACK_TYPE_MAPPING, config.VALID_ATTACK_TYPES),
            ("analyst_grade", config.ANALYST_GRADE_MAPPING, config.VALID_ANALYST_GRADES)]:
        spellings = ([key.upper() for key in mapping] + [key.title() for key in mapping]
                     + ["Somewhere Nobody Recognises"])
        frame = pd.DataFrame({column_name: spellings})
        folded = restrict_to_known_values(
            normalize_category_column(frame, column_name, mapping), column_name, recognised)
        produced = list(folded[column_name])
        expected = [mapping[key] for key in mapping] * 2
        wrong = [(spelling, value) for spelling, value, wanted
                 in zip(spellings, produced, expected) if value != wanted]
        assert len(wrong) == 0, (
            column_name
            + " folded "
            + str(len(wrong))
            + " spellings the configuration maps onto something else, for example "
            + str(wrong[:3])
            + ". Case is not meaning: BLR, Bangalore and bengaluru are one hub."
        )
        assert pd.isna(produced[-1]), (
            column_name
            + " kept "
            + repr(produced[-1])
            + ", a value the company does not use, instead of emptying it for imputation."
        )

    tokens = config.BOOLEAN_TRUE_TOKENS + config.BOOLEAN_FALSE_TOKENS
    flags = normalize_boolean_columns(
        pd.DataFrame({"mfa_enforced_flag": [token.upper() for token in tokens] + [None]}),
        ["mfa_enforced_flag"])["mfa_enforced_flag"]
    expected_flags = ([config.BOOLEAN_YES] * len(config.BOOLEAN_TRUE_TOKENS)
                      + [config.BOOLEAN_NO] * len(config.BOOLEAN_FALSE_TOKENS))
    assert list(flags[:-1]) == expected_flags and pd.isna(flags.iloc[-1]), (
        "Yes and no, written "
        + str([token.upper() for token in tokens])
        + ", came back as "
        + str(list(flags))
        + ". Every way of saying yes becomes "
        + config.BOOLEAN_YES
        + ", every way of saying no becomes "
        + config.BOOLEAN_NO
        + ", and an empty flag stays empty."
    )

    blanks = replace_missing_tokens(
        pd.DataFrame({"detection_source": config.NULL_TOKEN_LIST + ["User report"]}),
        config.NULL_TOKEN_LIST)["detection_source"]
    assert blanks.iloc[:-1].isna().all() and blanks.iloc[-1] == "User report", (
        "Of the "
        + str(len(config.NULL_TOKEN_LIST))
        + " ways the configuration lists of writing nothing, these survived as values: "
        + str([value for value in blanks.iloc[:-1] if not pd.isna(value)])
        + ". A placeholder kept as a category becomes a category the models learn."
    )

    for path, checks in [
            (config.CLEAN_INCIDENTS_TRAIN_FILE,
             [("soc_hub", config.VALID_HUBS), ("hosting_region", config.VALID_HOSTING_REGIONS),
              ("data_protection_state", config.VALID_PROTECTION_STATES),
              ("affected_system_class", config.VALID_SYSTEM_CLASSES),
              ("attack_vector", config.VALID_ATTACK_VECTORS)]),
            (config.CLEAN_EFFORT_TRAIN_FILE,
             [("attack_type", config.VALID_ATTACK_TYPES),
              ("analyst_grade", config.VALID_ANALYST_GRADES),
              ("harm_band", config.HARM_BAND_OPTIONS)]),
            (config.CLEAN_INCIDENT_NOTES_FILE,
             [(config.NOTE_TARGET_COLUMN, config.VALID_ATTACK_TYPES),
              ("note_source", config.VALID_NOTE_SOURCES)])]:
        for column_name, recognised in checks:
            strays = sorted(set(processed_frames[path][column_name].astype(str))
                            - set(recognised) - {config.UNKNOWN_CATEGORY_VALUE})
            assert len(strays) == 0, (
                column_name
                + " in "
                + path
                + " still holds "
                + str(strays[:6])
                + ", which the configuration does not list."
            )
    for path, columns in [(config.CLEAN_INCIDENTS_TRAIN_FILE, config.INCIDENT_BOOLEAN_COLUMNS),
                          (config.CLEAN_EFFORT_TRAIN_FILE, config.EFFORT_BOOLEAN_COLUMNS)]:
        for column_name in columns:
            strays = sorted(set(processed_frames[path][column_name].astype(str))
                            - {config.BOOLEAN_YES, config.BOOLEAN_NO,
                               config.UNKNOWN_CATEGORY_VALUE})
            assert len(strays) == 0, (
                column_name
                + " in "
                + path
                + " still holds "
                + str(strays)
                + " besides yes, no and unknown."
            )


def test_cleaning_repairs_facts_that_contradict_each_other(raw_frames, processed_frames,
                                                           tmp_path):
    import pandas as pd

    from config import config
    from data_pipeline.common_cleaning import (parse_mixed_format_timestamps,
                                               replace_missing_tokens, strip_text_whitespace)
    from data_pipeline.incident_cleaning import clean_incident_dataset

    assert raw_frames["problem"] is None, raw_frames["problem"]
    assert processed_frames["problem"] is None, processed_frames["problem"]
    raw_incidents = raw_frames[config.RAW_INCIDENTS_EVAL_FILE]
    identifier = config.INCIDENT_IDENTIFIER_COLUMNS[0]
    both_times = [config.FIRST_ALERT_COLUMN, config.AWARENESS_COLUMN]
    raw_times = parse_mixed_format_timestamps(
        replace_missing_tokens(strip_text_whitespace(raw_incidents[both_times]),
                               config.NULL_TOKEN_LIST), both_times)
    backwards_rows = raw_incidents[(raw_times[config.AWARENESS_COLUMN]
                                    < raw_times[config.FIRST_ALERT_COLUMN]).values]
    assert len(backwards_rows) > 0, (
        "Read through the cleaning module, no raw incident was confirmed before its first "
        "alert. The extract carries such rows, so the timestamps are not being read."
    )
    sample_path = str(tmp_path / "incidents_raw_sample.csv")
    cleaned_path = str(tmp_path / "incidents_cleaned_sample.csv")
    pd.concat([raw_incidents.head(1000), backwards_rows]).drop_duplicates().to_csv(
        sample_path, index=False)
    clean_incident_dataset(sample_path, cleaned_path)
    cleaned_sample = pd.read_csv(cleaned_path, low_memory=False)
    null_tokens = {token.strip().lower() for token in config.NULL_TOKEN_LIST}
    given = backwards_rows[config.INCIDENT_TARGET_COLUMN].fillna("").str.strip()
    answered = set(backwards_rows.loc[~(given.eq("") | given.str.lower().isin(null_tokens)),
                                      identifier].str.strip())
    dropped = sorted(answered - set(cleaned_sample[identifier].astype(str)))
    assert len(dropped) == 0, (
        str(len(dropped))
        + " incidents received with their two times the wrong way round were dropped by "
        "cleaning, for example "
        + str(dropped[:3])
        + ". Their times are swapped back and the incidents kept."
    )

    for path, frame in ([("the sample just cleaned", cleaned_sample)]
                        + [(path, processed_frames[path])
                           for path in [config.CLEAN_INCIDENTS_TRAIN_FILE,
                                        config.CLEAN_INCIDENTS_EVAL_FILE]]):
        first = pd.to_datetime(frame[config.FIRST_ALERT_COLUMN], utc=True)
        confirmed = pd.to_datetime(frame[config.AWARENESS_COLUMN], utc=True)
        backwards = int((confirmed < first).sum())
        assert backwards == 0, (
            path
            + " still has "
            + str(backwards)
            + " incidents confirmed before their first alert. Confirmation follows the "
            "alert, so a row the other way round has its two times swapped, and left "
            "that way a clock counted from confirmation starts before one counted from the "
            "first alert."
        )
        minutes = ((confirmed - first).dt.total_seconds() // 60).astype(int)
        disagreeing = int((minutes != frame[config.INCIDENT_INTERVAL_COLUMN]
                           .astype(float).astype(int)).sum())
        assert disagreeing == 0, (
            config.INCIDENT_INTERVAL_COLUMN
            + " in "
            + path
            + " disagrees with its own two timestamps on "
            + str(disagreeing)
            + " rows. The interval is the whole minutes from the first alert to the "
            "confirmation, worked out again from the two cleaned timestamps on every row."
        )

    raw_effort = raw_frames[config.RAW_EFFORT_TRAIN_FILE]
    said_no = raw_effort[config.FORENSIC_IMAGE_FLAG_COLUMN].str.strip().str.lower().isin(
        config.BOOLEAN_FALSE_TOKENS)
    imaged = pd.to_numeric(raw_effort[config.FORENSIC_IMAGE_COUNT_COLUMN], errors="coerce") > 0
    assert int((said_no & imaged).sum()) > 0, (
        "No raw containment record takes forensic images while saying none were required, "
        "so there is nothing here for the repair to have done."
    )
    for path in [config.CLEAN_EFFORT_TRAIN_FILE, config.CLEAN_EFFORT_EVAL_FILE]:
        frame = processed_frames[path]
        contradicted = int(((frame[config.FORENSIC_IMAGE_FLAG_COLUMN] == config.BOOLEAN_NO)
                            & (frame[config.FORENSIC_IMAGE_COUNT_COLUMN] > 0)).sum())
        assert contradicted == 0, (
            path
            + " still has "
            + str(contradicted)
            + " records that took forensic images when none were required. The flag is "
            "the decision and the count follows it, so those counts are nought."
        )

    for path, range_limits in [(config.CLEAN_INCIDENTS_TRAIN_FILE, config.INCIDENT_RANGE_LIMITS),
                               (config.CLEAN_EFFORT_TRAIN_FILE, config.EFFORT_RANGE_LIMITS),
                               (config.CLEAN_INCIDENT_NOTES_FILE, config.NOTE_RANGE_LIMITS)]:
        for column_name, (lowest, highest) in range_limits.items():
            values = pd.to_numeric(processed_frames[path][column_name], errors="coerce")
            outside = int(((values < lowest) | (values > highest)).sum())
            assert outside == 0, (
                column_name
                + " in "
                + path
                + " still has "
                + str(outside)
                + " values outside "
                + str(lowest)
                + " to "
                + str(highest)
                + ". A reading nothing real could produce is emptied before anything is "
                "imputed, or the imputation is worked out from it."
            )


def test_saved_feature_schemas_leave_out_the_answer_and_every_identifier(processed_frames,
                                                                         saved_models):
    from config import config

    assert processed_frames["problem"] is None, processed_frames["problem"]
    assert saved_models["problem"] is None, saved_models["problem"]
    for schema_name, schema, clean_path, identifiers, target in [
            ("harm", saved_models["harm_schema"], config.CLEAN_INCIDENTS_TRAIN_FILE,
             config.INCIDENT_IDENTIFIER_COLUMNS, config.INCIDENT_TARGET_COLUMN),
            ("effort", saved_models["effort_schema"], config.CLEAN_EFFORT_TRAIN_FILE,
             config.EFFORT_IDENTIFIER_COLUMNS, config.EFFORT_TARGET_COLUMN)]:
        assert len(schema) > 0, (
            "The saved " + schema_name + " feature schema is empty, so nothing records "
            "which columns the model was fitted on."
        )
        assert target not in schema, (
            "The saved "
            + schema_name
            + " schema lists "
            + target
            + ", the answer the model predicts. A model shown its own answer scores almost "
            "perfectly and has learned nothing."
        )
        leaked = [name for name in identifiers if name in schema]
        assert len(leaked) == 0, (
            "The saved "
            + schema_name
            + " schema lists "
            + str(leaked)
            + ". An identifier or a timestamp says which record a row is, not what it "
            "means, and a model fitted on it memorises rows."
        )
        assert len(schema) == len(set(schema)), (
            "The saved "
            + schema_name
            + " schema names a column twice: "
            + str(schema)
            + ". A row built to that schema no longer lines up with what the model was fitted on."
        )
        unknown = [name for name in schema if name not in processed_frames[clean_path].columns]
        assert len(unknown) == 0, (
            "The saved "
            + schema_name
            + " schema lists "
            + str(unknown)
            + ", which "
            + clean_path
            + " does not have, so no cleaned row can be scored."
        )


def test_model_inputs_are_built_in_the_saved_schema_order(processed_frames, saved_models):
    from config import config
    from data_pipeline.feature_builder import build_model_inputs

    assert processed_frames["problem"] is None, processed_frames["problem"]
    assert saved_models["problem"] is None, saved_models["problem"]
    for schema_name, clean_path, identifiers, target in [
            ("harm", config.CLEAN_INCIDENTS_EVAL_FILE, config.INCIDENT_IDENTIFIER_COLUMNS,
             config.INCIDENT_TARGET_COLUMN),
            ("effort", config.CLEAN_EFFORT_EVAL_FILE, config.EFFORT_IDENTIFIER_COLUMNS,
             config.EFFORT_TARGET_COLUMN)]:
        frame = processed_frames[clean_path]
        features, answers = build_model_inputs(frame.copy(), identifiers, target)
        built = list(features.columns)
        saved = list(saved_models[schema_name + "_schema"])
        assert built == saved, (
            "The "
            + schema_name
            + " features built from "
            + clean_path
            + " are "
            + str(built[:5])
            + " ... ("
            + str(len(built))
            + " columns) but the schema saved beside the model is "
            + str(saved[:5])
            + " ... ("
            + str(len(saved))
            + " columns). Same names in a different order score silently and wrongly."
        )
        assert len(features) == len(frame) and len(answers) == len(frame), (
            "Building the "
            + schema_name
            + " inputs turned "
            + str(len(frame))
            + " rows into "
            + str(len(features))
            + " feature rows and "
            + str(len(answers))
            + " answers. Choosing columns must not drop or add rows."
        )
        assert list(answers) == list(frame[target]), (
            "The "
            + schema_name
            + " answers returned are not the "
            + target
            + " column of the rows given, in the same order."
        )


def test_saved_models_score_rows_with_gaps_and_values_never_seen(processed_frames,
                                                                 saved_models):
    import numpy as np

    from config import config

    assert processed_frames["problem"] is None, processed_frames["problem"]
    assert saved_models["problem"] is None, saved_models["problem"]
    for model_name, clean_path in [("harm", config.CLEAN_INCIDENTS_EVAL_FILE),
                                   ("effort", config.CLEAN_EFFORT_EVAL_FILE)]:
        schema = saved_models[model_name + "_schema"]
        rows = processed_frames[clean_path][schema].head(60).copy()
        numeric = [name for name in schema if rows[name].dtype.kind in "if"]
        text = [name for name in schema if name not in numeric]
        assert len(numeric) > 0 and len(text) > 0, (
            "The "
            + model_name
            + " schema holds "
            + str(len(numeric))
            + " numeric and "
            + str(len(text))
            + " text columns, so gaps in both kinds cannot be tried."
        )
        rows.loc[rows.index[:20], numeric[0]] = np.nan
        rows.loc[rows.index[20:40], text[0]] = np.nan
        rows.loc[rows.index[40:], text[-1]] = "A value no training row ever held"

        model = saved_models[model_name]
        refusal = ""
        try:
            scores = (model.predict_proba(rows)[:, 1] if model_name == "harm"
                      else model.predict(rows))
        except ValueError as error:
            scores, refusal = [], str(error)
        assert refusal == "", (
            "The saved "
            + model_name
            + " model refused rows with a gap or a value it never saw: "
            + refusal[:200]
            + ". A live incident arrives with gaps and new spellings, so the pipeline saved "
            "with the model has to fill every gap and ignore what it does not know."
        )
        assert len(scores) == len(rows), (
            "The saved "
            + model_name
            + " model returned "
            + str(len(scores))
            + " scores for "
            + str(len(rows))
            + " rows. Every row given has to get a score, or the scores are matched to the "
            "wrong incidents."
        )
        assert np.isfinite(np.asarray(scores, dtype=float)).all(), (
            "The saved "
            + model_name
            + " model returned an empty or infinite score for a row with a gap or a value "
            "it never saw. A live incident arrives with gaps, and the pipeline saved "
            "with the model has to fill them and ignore what it does not know."
        )


def test_each_saved_model_was_fitted_on_the_columns_its_schema_names(saved_models):
    assert saved_models["problem"] is None, saved_models["problem"]
    for model_name in ["harm", "effort"]:
        model = saved_models[model_name]
        schema = [str(name) for name in saved_models[model_name + "_schema"]]
        fitted_on = getattr(model, "feature_names_in_", None)
        if fitted_on is None:
            assert getattr(model, "n_features_in_", None) == len(schema), (
                "The saved "
                + model_name
                + " model records neither the names nor the number of the columns it was "
                "fitted on, or the number is not the "
                + str(len(schema))
                + " its saved schema lists, so nothing shows that the schema describes it."
            )
        else:
            fitted_names = [str(name) for name in fitted_on]
            assert fitted_names == schema, (
                "The saved "
                + model_name
                + " model was fitted on "
                + str(fitted_names[:5])
                + " ... ("
                + str(len(fitted_names))
                + " columns) but the schema saved beside it lists "
                + str(schema[:5])
                + " ... ("
                + str(len(schema))
                + " columns). Live incidents are built to the schema, so a model fitted on "
                "other columns, or on the same ones in another order, scores them wrongly or "
                "not at all."
            )
    classes = getattr(saved_models["harm"], "classes_", None)
    assert classes is not None and list(classes) == [0, 1], (
        "The saved harm model's classes are "
        + str(None if classes is None else list(classes))
        + ". Every tool reads the second column of its probabilities as the chance that an "
        "incident puts people at high risk, which holds only when the classes are 0 and 1 "
        "in that order."
    )


def test_the_quality_report_accounts_for_every_row_it_received(raw_frames, processed_frames):
    import json
    import os

    from config import config
    from data_pipeline.quality_profiler import profile_dataset

    assert raw_frames["problem"] is None, raw_frames["problem"]
    assert processed_frames["problem"] is None, processed_frames["problem"]
    assert os.path.isfile(config.DATA_QUALITY_REPORT_FILE), (
        "There is no quality report at "
        + config.DATA_QUALITY_REPORT_FILE
        + ". The data pipeline writes one beside the cleaned files to say what cleaning did."
    )
    with open(config.DATA_QUALITY_REPORT_FILE) as report_file:
        report = json.load(report_file)

    for raw_path, clean_path, target, range_limits in [
            (config.RAW_INCIDENTS_TRAIN_FILE, config.CLEAN_INCIDENTS_TRAIN_FILE,
             config.INCIDENT_TARGET_COLUMN, config.INCIDENT_RANGE_LIMITS),
            (config.RAW_INCIDENTS_EVAL_FILE, config.CLEAN_INCIDENTS_EVAL_FILE,
             config.INCIDENT_TARGET_COLUMN, config.INCIDENT_RANGE_LIMITS),
            (config.RAW_EFFORT_TRAIN_FILE, config.CLEAN_EFFORT_TRAIN_FILE,
             config.EFFORT_TARGET_COLUMN, config.EFFORT_RANGE_LIMITS),
            (config.RAW_EFFORT_EVAL_FILE, config.CLEAN_EFFORT_EVAL_FILE,
             config.EFFORT_TARGET_COLUMN, config.EFFORT_RANGE_LIMITS),
            (config.RAW_INCIDENT_NOTES_FILE, config.CLEAN_INCIDENT_NOTES_FILE,
             config.NOTE_TARGET_COLUMN, config.NOTE_RANGE_LIMITS)]:
        name = os.path.splitext(os.path.basename(raw_path))[0]
        assert name in report, (
            "The quality report has no entry for "
            + name
            + ", so nothing says what cleaning did to "
            + raw_path
            + "."
        )
        entry = report[name]
        raw_frame = raw_frames[raw_path]
        clean_frame = processed_frames[clean_path]
        profiled = profile_dataset(raw_frame, clean_frame, target, range_limits)
        fields = {"rows_received", "rows_kept", "rows_removed", "duplicate_rows", "columns",
                  "missing_cells_after_cleaning", "out_of_range_by_column"}
        missing = sorted((fields - set(entry)) | (fields - set(profiled)))
        assert len(missing) == 0, (
            "The quality report entry for "
            + name
            + ", or the profile worked out for it, has no "
            + str(missing)
            + ", so what cleaning did to that extract cannot be read."
        )
        for field_name, measured in [("rows_received", len(raw_frame)),
                                     ("rows_kept", len(clean_frame)),
                                     ("rows_removed", len(raw_frame) - len(clean_frame)),
                                     ("duplicate_rows", int(raw_frame.duplicated().sum())),
                                     ("columns", clean_frame.shape[1]),
                                     ("missing_cells_after_cleaning",
                                      int(clean_frame.isna().sum().sum()))]:
            assert entry[field_name] == measured, (
                "The quality report says "
                + field_name
                + " is "
                + str(entry[field_name])
                + " for "
                + name
                + ", but the files say "
                + str(measured)
                + ". A report that does not match the data it describes cannot be used to "
                "defend what the pipeline did."
            )
            assert profiled[field_name] == measured, (
                "Profiling "
                + name
                + " now gives "
                + field_name
                + " as "
                + str(profiled[field_name])
                + " where the files say "
                + str(measured)
                + ", so the profiler does not count what it is given."
            )
        unexpected = sorted(set(entry["out_of_range_by_column"]) - set(range_limits))
        assert len(unexpected) == 0, (
            "The quality report counts out-of-range values in "
            + str(unexpected)
            + " for "
            + name
            + ", which have no range in the configuration."
        )
        assert sum(entry["out_of_range_by_column"].values()) > 0, (
            "The quality report finds no value outside its range in "
            + name
            + ". Every extract carries some, so the ranges are not being checked."
        )


def test_harm_model_ranks_held_out_incidents_above_the_configured_minimum(processed_frames,
                                                                          saved_models):
    import copy

    import numpy as np
    from sklearn.metrics import roc_auc_score

    from config import config
    from data_pipeline.feature_builder import build_model_inputs
    from modeling.model_evaluation import evaluate_classifier

    assert processed_frames["problem"] is None, processed_frames["problem"]
    assert saved_models["problem"] is None, saved_models["problem"]
    train_features, train_answers = build_model_inputs(
        processed_frames[config.CLEAN_INCIDENTS_TRAIN_FILE].head(6000),
        config.INCIDENT_IDENTIFIER_COLUMNS, config.INCIDENT_TARGET_COLUMN)
    eval_features, eval_answers = build_model_inputs(
        processed_frames[config.CLEAN_INCIDENTS_EVAL_FILE].copy(),
        config.INCIDENT_IDENTIFIER_COLUMNS, config.INCIDENT_TARGET_COLUMN)
    model = saved_models["harm"]
    scores = evaluate_classifier(copy.deepcopy(model), train_features, train_answers,
                                 eval_features, eval_answers)
    missing = sorted({"roc_auc", "train_roc_auc", "generalisation_gap"} - set(scores))
    assert len(missing) == 0, (
        "evaluate_classifier returned no "
        + str(missing)
        + ", so the harm model's scores cannot be read."
    )

    assert scores["roc_auc"] >= config.MINIMUM_HARM_ROC_AUC, (
        "The harm model scored "
        + str(scores["roc_auc"])
        + " ROC AUC on the held-out incidents, below the "
        + str(config.MINIMUM_HARM_ROC_AUC)
        + " the configuration sets. The bar sits well below what a sound model reaches."
    )
    probabilities = model.predict_proba(eval_features)[:, 1]
    measured = roc_auc_score(eval_answers, probabilities)
    assert abs(scores["roc_auc"] - measured) < 0.006, (
        "The evaluation reports a ROC AUC of "
        + str(scores["roc_auc"])
        + " for the held-out incidents, but the model's own probabilities give "
        + str(round(measured, 4))
        + ". The score has to be measured on the held-out rows, from probabilities."
    )
    trained_on = roc_auc_score(train_answers, model.predict_proba(train_features)[:, 1])
    assert abs(scores["train_roc_auc"] - trained_on) < 0.006, (
        "The evaluation reports a training ROC AUC of "
        + str(scores["train_roc_auc"])
        + ", but the model's own probabilities on the training rows it was given give "
        + str(round(trained_on, 4))
        + ". The training score is measured on the training rows, or the gap cannot show "
        "how much the model memorised."
    )
    assert abs(scores["generalisation_gap"]
               - (scores["train_roc_auc"] - scores["roc_auc"])) < 0.011, (
        "The reported gap "
        + str(scores["generalisation_gap"])
        + " is not the training score "
        + str(scores["train_roc_auc"])
        + " less the held-out score "
        + str(scores["roc_auc"])
        + "."
    )
    answers = np.asarray(eval_answers)
    high_risk = float(probabilities[answers == 1].mean())
    the_rest = float(probabilities[answers == 0].mean())
    assert high_risk > the_rest, (
        "Incidents that put people at high risk average "
        + str(round(high_risk, 4))
        + " and the rest "
        + str(round(the_rest, 4))
        + ". The model scores the wrong way round."
    )


def test_effort_model_explains_held_out_hours_better_than_their_average(processed_frames,
                                                                        saved_models):
    import copy

    import numpy as np
    from sklearn.metrics import r2_score

    from config import config
    from data_pipeline.feature_builder import build_model_inputs
    from modeling.model_evaluation import evaluate_regressor

    assert processed_frames["problem"] is None, processed_frames["problem"]
    assert saved_models["problem"] is None, saved_models["problem"]
    train_features, train_answers = build_model_inputs(
        processed_frames[config.CLEAN_EFFORT_TRAIN_FILE].head(6000),
        config.EFFORT_IDENTIFIER_COLUMNS, config.EFFORT_TARGET_COLUMN)
    eval_features, eval_answers = build_model_inputs(
        processed_frames[config.CLEAN_EFFORT_EVAL_FILE].copy(),
        config.EFFORT_IDENTIFIER_COLUMNS, config.EFFORT_TARGET_COLUMN)
    model = saved_models["effort"]
    scores = evaluate_regressor(copy.deepcopy(model), train_features, train_answers,
                                eval_features, eval_answers)
    missing = sorted({"r2", "train_r2", "mean_absolute_error", "baseline_mean_absolute_error",
                      "lowest_prediction"} - set(scores))
    assert len(missing) == 0, (
        "evaluate_regressor returned no "
        + str(missing)
        + ", so the effort model's scores cannot be read."
    )

    assert scores["r2"] >= config.MINIMUM_EFFORT_R2, (
        "The effort model scored "
        + str(scores["r2"])
        + " R squared on the held-out records, below the "
        + str(config.MINIMUM_EFFORT_R2)
        + " the configuration sets."
    )
    predictions = np.asarray(model.predict(eval_features), dtype=float)
    measured = r2_score(eval_answers, predictions)
    assert abs(scores["r2"] - measured) < 0.006, (
        "The evaluation reports R squared "
        + str(scores["r2"])
        + ", but the model's own predictions on the held-out records give "
        + str(round(measured, 4))
        + "."
    )
    trained_on = r2_score(train_answers, np.asarray(model.predict(train_features), dtype=float))
    assert abs(scores["train_r2"] - trained_on) < 0.006, (
        "The evaluation reports a training R squared of "
        + str(scores["train_r2"])
        + ", but the model's own predictions on the training rows it was given give "
        + str(round(trained_on, 4))
        + "."
    )
    baseline = float(np.mean(np.abs(np.asarray(eval_answers, dtype=float)
                                    - float(np.mean(np.asarray(train_answers, dtype=float))))))
    assert abs(scores["baseline_mean_absolute_error"] - baseline) < 0.051, (
        "The evaluation reports a baseline error of "
        + str(scores["baseline_mean_absolute_error"])
        + " hours, but always answering the average of the training hours it was given "
        "misses the held-out records by "
        + str(round(baseline, 2))
        + " hours on average."
    )
    assert scores["mean_absolute_error"] < scores["baseline_mean_absolute_error"], (
        "The model misses by "
        + str(scores["mean_absolute_error"])
        + " hours on average, no better than the "
        + str(scores["baseline_mean_absolute_error"])
        + " hours missed by always answering the training average."
    )
    assert abs(scores["lowest_prediction"] - float(predictions.min())) < 0.051, (
        "The evaluation reports a lowest estimate of "
        + str(scores["lowest_prediction"])
        + " hours, but the model's lowest estimate on the held-out records is "
        + str(round(float(predictions.min()), 2))
        + "."
    )


def test_harm_score_rises_with_the_facts_a_dpo_weighs(processed_frames, saved_models):
    from config import config

    assert processed_frames["problem"] is None, processed_frames["problem"]
    assert saved_models["problem"] is None, saved_models["problem"]
    schema = saved_models["harm_schema"]
    eval_frame = processed_frames[config.CLEAN_INCIDENTS_EVAL_FILE]
    with_personal_data = eval_frame[eval_frame["personal_data_involved_flag"]
                                    == config.BOOLEAN_YES][schema].head(1500)
    assert len(with_personal_data) > 100, (
        "Only "
        + str(len(with_personal_data))
        + " held-out incidents involve personal data, too few to compare."
    )
    model = saved_models["harm"]
    for column_name, riskier, safer in [
            ("government_id_flag", config.BOOLEAN_YES, config.BOOLEAN_NO),
            ("exfiltration_confirmed_flag", config.BOOLEAN_YES, config.BOOLEAN_NO),
            ("data_protection_state", "Plaintext", "Encrypted")]:
        worse = with_personal_data.copy()
        worse[column_name] = riskier
        better = with_personal_data.copy()
        better[column_name] = safer
        worse_average = float(model.predict_proba(worse)[:, 1].mean())
        better_average = float(model.predict_proba(better)[:, 1].mean())
        assert worse_average > better_average, (
            "With "
            + column_name
            + " set to "
            + riskier
            + " the same incidents average "
            + str(round(worse_average, 4))
            + ", and with it set to "
            + safer
            + " they average "
            + str(round(better_average, 4))
            + ". A Data Protection Officer weighs that fact the other way, so the model "
            "has not learned what makes a breach high risk."
        )


def test_effort_estimate_rises_with_the_scope_of_the_work(processed_frames, saved_models):
    from config import config

    assert processed_frames["problem"] is None, processed_frames["problem"]
    assert saved_models["problem"] is None, saved_models["problem"]
    schema = saved_models["effort_schema"]
    records = processed_frames[config.CLEAN_EFFORT_EVAL_FILE][schema].head(2000)
    model = saved_models["effort"]
    estimates = model.predict(records)
    as_recorded = float(estimates.mean())
    assert float(estimates.std()) > 0.5, (
        "The effort model estimates about the same hours for every record, with a spread of "
        + str(round(float(estimates.std()), 3))
        + ". An estimate that ignores the record cannot say whether a filing fits."
    )

    wider = records.copy()
    wider["systems_affected_count"] = records["systems_affected_count"] * 4
    more_logs = records.copy()
    more_logs["log_sources_to_review"] = records["log_sources_to_review"] + 10
    imaged = records.copy()
    imaged[config.FORENSIC_IMAGE_FLAG_COLUMN] = config.BOOLEAN_YES
    imaged[config.FORENSIC_IMAGE_COUNT_COLUMN] = 6
    not_imaged = records.copy()
    not_imaged[config.FORENSIC_IMAGE_FLAG_COLUMN] = config.BOOLEAN_NO
    not_imaged[config.FORENSIC_IMAGE_COUNT_COLUMN] = 0
    active = records.copy()
    active["attacker_still_active_flag"] = config.BOOLEAN_YES
    gone = records.copy()
    gone["attacker_still_active_flag"] = config.BOOLEAN_NO

    for change, larger, smaller in [
            ("four times the systems affected", wider, None),
            ("ten more log sources to review", more_logs, None),
            ("six forensic images taken", imaged, not_imaged),
            ("an attacker still active", active, gone)]:
        larger_average = float(model.predict(larger).mean())
        smaller_average = (as_recorded if smaller is None
                           else float(model.predict(smaller).mean()))
        assert larger_average > smaller_average, (
            "With "
            + change
            + " the same records average "
            + str(round(larger_average, 2))
            + " estimated hours against "
            + str(round(smaller_average, 2))
            + " without. More work cannot take less time, so the model has not learned "
            "what drives containment effort."
        )


def test_harm_facts_band_each_score_by_the_configured_thresholds(open_queue, saved_models):
    import pandas as pd

    from config import config
    from tools.prediction_tools import build_harm_facts

    assert open_queue["problem"] is None, open_queue["problem"]
    assert saved_models["problem"] is None, saved_models["problem"]
    incidents = open_queue["incidents"]
    facts = build_harm_facts(saved_models["harm"], saved_models["harm_schema"],
                             incidents.copy())
    assert len(facts) == len(incidents), (
        "Harm facts were built for "
        + str(len(facts))
        + " of the "
        + str(len(incidents))
        + " incidents given, so the facts no longer line up with the incidents they "
        "describe."
    )
    missing = sorted({"harm_probability", "harm_band", "data_categories",
                      "high_impact_categories", "sensitive_categories"} - set(facts[0]))
    assert len(missing) == 0, (
        "The harm facts carry no "
        + str(missing)
        + ", so the agents and the queue cannot read them."
    )
    refusal = ""
    try:
        probabilities = saved_models["harm"].predict_proba(
            incidents[saved_models["harm_schema"]])[:, 1]
    except ValueError as error:
        probabilities, refusal = [], str(error)
    assert refusal == "", (
        "The saved harm model refused the live incidents as they stand: "
        + refusal[:200]
        + ". Live incidents arrive with gaps, and the pipeline saved with the model fills them."
    )
    bands_seen = set()
    for position, (fact, probability) in enumerate(zip(facts, probabilities)):
        row = incidents.iloc[position]
        reference = str(row["incident_reference"])
        assert abs(fact["harm_probability"] - float(probability)) < 0.006, (
            reference
            + " was given a harm probability of "
            + str(fact["harm_probability"])
            + " where the saved model scores it "
            + str(round(float(probability), 4))
            + "."
        )
        expected_bands = {config.HARM_BAND_HIGH if value >= config.HARM_BAND_HIGH_THRESHOLD
                          else config.HARM_BAND_MEDIUM
                          if value >= config.HARM_BAND_MEDIUM_THRESHOLD
                          else config.HARM_BAND_LOW
                          for value in [float(probability), fact["harm_probability"]]}
        assert fact["harm_band"] in expected_bands, (
            reference
            + " scored "
            + str(fact["harm_probability"])
            + " and was banded "
            + str(fact["harm_band"])
            + " where the thresholds "
            + str(config.HARM_BAND_MEDIUM_THRESHOLD)
            + " and "
            + str(config.HARM_BAND_HIGH_THRESHOLD)
            + " put it in "
            + " or ".join(sorted(expected_bands))
            + ". A score sitting on a threshold belongs to the band above it."
        )
        flagged = {column for column in config.DATA_CATEGORY_FLAG_COLUMNS
                   if row[column] == config.BOOLEAN_YES}
        for key, allowed in [("data_categories", config.DATA_CATEGORY_FLAG_COLUMNS),
                             ("high_impact_categories", config.HIGH_IMPACT_DATA_FLAG_COLUMNS),
                             ("sensitive_categories", config.SENSITIVE_DATA_FLAG_COLUMNS)]:
            expected = flagged & set(allowed)
            assert set(fact[key]) == expected, (
                reference
                + " lists "
                + key
                + " as "
                + str(sorted(fact[key]))
                + " where its flags give "
                + str(sorted(expected))
                + ". The categories are read from the incident's own flags, and the sensitive "
                "ones decide the effort multiplier."
            )
        bands_seen.add(fact["harm_band"])
    assert bands_seen == set(config.HARM_BAND_OPTIONS), (
        "Across the live queue only "
        + str(sorted(bands_seen))
        + " occur. The queue holds incidents of every band, so the scores are not "
        "separating them."
    )
    assert pd.Series(probabilities).std() > 0.05, (
        "Every live incident scores about the same, so the queue cannot be ordered by harm."
    )


def test_attack_classifier_clears_the_configured_macro_f1(processed_frames, saved_models):
    import copy

    from sklearn.metrics import f1_score
    from sklearn.model_selection import train_test_split

    from config import config
    from modeling.model_evaluation import evaluate_text_classifier

    assert processed_frames["problem"] is None, processed_frames["problem"]
    assert saved_models["problem"] is None, saved_models["problem"]
    notes = processed_frames[config.CLEAN_INCIDENT_NOTES_FILE]
    train_text, eval_text, train_answers, eval_answers = train_test_split(
        notes[config.NOTE_TEXT_COLUMN], notes[config.NOTE_TARGET_COLUMN],
        test_size=config.VALIDATION_SPLIT_RATIO, stratify=notes[config.NOTE_TARGET_COLUMN],
        random_state=config.RANDOM_SEED)
    model = saved_models["attack"]
    scores = evaluate_text_classifier(copy.deepcopy(model), train_text.head(6000),
                                      train_answers.head(6000), eval_text, eval_answers)
    missing = sorted({"macro_f1", "train_macro_f1", "generalisation_gap", "per_class_f1"}
                     - set(scores))
    assert len(missing) == 0, (
        "evaluate_text_classifier returned no "
        + str(missing)
        + ", so the attack classifier's scores cannot be read."
    )

    assert scores["macro_f1"] >= config.MINIMUM_ATTACK_MACRO_F1, (
        "The attack classifier scored "
        + str(scores["macro_f1"])
        + " macro F1 on the held-out notes, below the "
        + str(config.MINIMUM_ATTACK_MACRO_F1)
        + " the configuration sets. Macro F1 weighs the rarest attack type as much as the "
        "commonest, which is the point: the rare types are the ones a busy desk misreads."
    )
    measured = f1_score(eval_answers, model.predict(eval_text), average="macro")
    assert abs(scores["macro_f1"] - measured) < 0.006, (
        "The evaluation reports macro F1 "
        + str(scores["macro_f1"])
        + ", but the classifier's own predictions on the held-out notes give "
        + str(round(measured, 4))
        + "."
    )
    trained_on = f1_score(train_answers.head(6000), model.predict(train_text.head(6000)),
                          average="macro")
    assert (abs(scores["train_macro_f1"] - trained_on) < 0.006
            and abs(scores["generalisation_gap"]
                    - (scores["train_macro_f1"] - scores["macro_f1"])) < 0.011), (
        "The evaluation reports a training macro F1 of "
        + str(scores["train_macro_f1"])
        + " and a gap of "
        + str(scores["generalisation_gap"])
        + ", but the classifier's own predictions on the training notes it was given give "
        + str(round(trained_on, 4))
        + ". The training score is measured on the training notes and the gap is that less "
        "the held-out score."
    )
    assert set(scores["per_class_f1"]) == set(config.VALID_ATTACK_TYPES), (
        "The per-type scores cover "
        + str(sorted(scores["per_class_f1"]))
        + " where the desk codes to "
        + str(config.VALID_ATTACK_TYPES)
        + ". A type left out is a type whose score nobody sees."
    )


def test_attack_predictions_stay_inside_the_vocabulary_and_cover_every_type(processed_frames,
                                                                            saved_models):
    from sklearn.model_selection import train_test_split

    from config import config

    assert processed_frames["problem"] is None, processed_frames["problem"]
    assert saved_models["problem"] is None, saved_models["problem"]
    notes = processed_frames[config.CLEAN_INCIDENT_NOTES_FILE]
    _, eval_text, _, eval_answers = train_test_split(
        notes[config.NOTE_TEXT_COLUMN], notes[config.NOTE_TARGET_COLUMN],
        test_size=config.VALIDATION_SPLIT_RATIO, stratify=notes[config.NOTE_TARGET_COLUMN],
        random_state=config.RANDOM_SEED)
    predicted = [str(label) for label in saved_models["attack"].predict(eval_text)]

    strays = sorted(set(predicted) - set(config.VALID_ATTACK_TYPES))
    assert len(strays) == 0, (
        "The attack classifier predicted "
        + str(strays)
        + ", which the configuration does not list. Every type downstream is looked up "
        "by name, playbooks included."
    )
    never = sorted(set(config.VALID_ATTACK_TYPES) - set(predicted))
    assert len(never) == 0, (
        "Across "
        + str(len(predicted))
        + " held-out notes the classifier never once predicted "
        + str(never)
        + ", so those incidents are always given someone else's playbook."
    )
    for attack_type in config.VALID_ATTACK_TYPES:
        given = [label for label, truth in zip(predicted, eval_answers) if truth == attack_type]
        commonest = max(set(given), key=given.count)
        assert commonest == attack_type, (
            "Notes about "
            + attack_type
            + " are most often read as "
            + commonest
            + ". A classifier that confuses a type with another more often than it names "
            "it has not learned that type."
        )


def test_note_cleaning_leaves_plain_words_the_classifier_can_read(raw_frames, processed_frames,
                                                                  tmp_path):
    import pandas as pd

    from config import config
    from data_pipeline.incident_note_cleaning import clean_incident_note_dataset

    assert raw_frames["problem"] is None, raw_frames["problem"]
    assert processed_frames["problem"] is None, processed_frames["problem"]
    raw_notes = raw_frames[config.RAW_INCIDENT_NOTES_FILE]
    raw_text = raw_notes[config.NOTE_TEXT_COLUMN].fillna("")
    carrying = raw_text.str.contains(config.MARKUP_PATTERN)
    for artefact in config.ENCODING_ARTIFACT_LIST:
        carrying = carrying | raw_text.str.contains(artefact, regex=False)
    assert int(carrying.sum()) > 0, (
        "No raw note carries markup or an encoding artefact, so there is nothing for this "
        "check to look for."
    )
    sample_path = str(tmp_path / "notes_raw_sample.csv")
    cleaned_path = str(tmp_path / "notes_cleaned_sample.csv")
    marked = raw_notes[carrying].head(120)
    pd.concat([marked, raw_notes.head(200)]).drop_duplicates().to_csv(sample_path, index=False)
    clean_incident_note_dataset(sample_path, cleaned_path)
    cleaned_sample = pd.read_csv(cleaned_path, low_memory=False)
    kept = set(marked["note_id"].str.strip()) & set(cleaned_sample["note_id"].astype(str))
    assert len(kept) >= 0.8 * marked["note_id"].nunique(), (
        "Of "
        + str(marked["note_id"].nunique())
        + " notes that carried markup or an encoding artefact, cleaning kept "
        + str(len(kept))
        + ". The markup and the artefacts are taken out of the text and the note is kept."
    )

    for source, notes in [("the sample just cleaned", cleaned_sample),
                          (config.CLEAN_INCIDENT_NOTES_FILE,
                           processed_frames[config.CLEAN_INCIDENT_NOTES_FILE])]:
        texts = notes[config.NOTE_TEXT_COLUMN].astype(str)
        with_markup = int(texts.str.contains(config.MARKUP_PATTERN).sum())
        assert with_markup == 0, (
            str(with_markup)
            + " notes in "
            + source
            + " still carry markup such as "
            + str(texts[texts.str.contains(config.MARKUP_PATTERN)].head(1).tolist())
            + ". A tag is a word to the vectoriser and it names no attack."
        )
        for artefact in config.ENCODING_ARTIFACT_LIST:
            carrying_now = int(texts.str.contains(artefact, regex=False).sum())
            assert carrying_now == 0, (
                str(carrying_now)
                + " notes in "
                + source
                + " still contain the encoding artefact "
                + repr(artefact)
                + ", which the vectoriser reads as a word that means nothing."
            )
        untidy = int((texts != texts.str.strip()).sum()
                     + texts.str.contains(r"\s{2,}|[\t\n\r]").sum())
        assert untidy == 0, (
            str(untidy)
            + " notes in "
            + source
            + " still carry runs of whitespace or leading and trailing spaces."
        )
        word_counts = texts.str.split().str.len()
        assert int(word_counts.min()) >= config.MINIMUM_NOTE_WORDS, (
            "A note in "
            + source
            + " runs to only "
            + str(int(word_counts.min()))
            + " words where the configuration keeps notes of at least "
            + str(config.MINIMUM_NOTE_WORDS)
            + ". A fragment that short names no attack and teaches the classifier noise."
        )
        lengths = notes[config.NOTE_LENGTH_COLUMN].astype(int)
        wrong_length = int((lengths != texts.str.len()).sum())
        assert wrong_length == 0, (
            config.NOTE_LENGTH_COLUMN
            + " disagrees with the cleaned text on "
            + str(wrong_length)
            + " notes in "
            + source
            + ". Length is measured after cleaning, not carried over from the raw text."
        )


def test_attack_facts_report_the_type_most_notes_name(open_queue, saved_models):
    from tools.incident_data_tools import fetch_incident_notes
    from tools.prediction_tools import build_attack_facts

    assert open_queue["problem"] is None, open_queue["problem"]
    assert saved_models["problem"] is None, saved_models["problem"]
    notes = open_queue["notes"]
    counts = notes.groupby("incident_reference").size()
    references = list(counts[counts >= 2].index[:40])
    assert len(references) >= 20, (
        "Fewer than twenty live incidents have two notes or more, so vote counting "
        "cannot be tried."
    )
    model = saved_models["attack"]
    disagreement_seen = False
    for reference in references:
        texts = fetch_incident_notes(notes, reference)
        facts = build_attack_facts(model, texts)
        missing = sorted({"attack_type", "notes_read", "note_attack_types", "agreement",
                          "other_attack_types"} - set(facts))
        assert len(missing) == 0, (
            "The attack facts for "
            + reference
            + " carry no "
            + str(missing)
            + ", so the attack analyst cannot read them."
        )
        predicted = [str(label) for label in model.predict(texts)]
        votes = predicted.count(facts["attack_type"])

        assert facts["notes_read"] == len(texts), (
            reference
            + " has "
            + str(len(texts))
            + " notes but the facts say "
            + str(facts["notes_read"])
            + " were read, so the agreement is worked out over the wrong number of notes."
        )
        assert list(facts["note_attack_types"]) == predicted, (
            reference
            + " lists the notes as "
            + str(facts["note_attack_types"])
            + " where the classifier reads them as "
            + str(predicted)
            + ". The facts handed to the attack analyst have to be the classifier's own "
            "reading, note by note."
        )
        assert votes == max(predicted.count(label) for label in predicted), (
            reference
            + " was put down as "
            + str(facts["attack_type"])
            + ", which "
            + str(votes)
            + " of its notes name, while another type is named by more."
        )
        assert abs(facts["agreement"] - votes / len(texts)) < 0.006, (
            reference
            + " reports agreement "
            + str(facts["agreement"])
            + " where "
            + str(votes)
            + " of "
            + str(len(texts))
            + " notes agree. Agreement tells the analyst how settled the type is."
        )
        assert sorted(facts["other_attack_types"]) == sorted(
                set(predicted) - {facts["attack_type"]}), (
            reference
            + " lists "
            + str(facts["other_attack_types"])
            + " as the other types named, where its notes name "
            + str(sorted(set(predicted) - {facts["attack_type"]}))
            + "."
        )
        disagreement_seen = disagreement_seen or len(set(predicted)) > 1
    assert disagreement_seen, (
        "Not one of these incidents has notes that disagree, so the agreement figure was "
        "never tested below one."
    )


def test_notes_are_read_for_one_incident_in_the_order_they_were_written(open_queue):
    from config import config
    from tools.incident_data_tools import fetch_incident_notes, fetch_incident_profile

    assert open_queue["problem"] is None, open_queue["problem"]
    notes = open_queue["notes"]
    incidents = open_queue["incidents"]
    counts = notes.groupby("incident_reference").size()
    for reference in list(counts.sort_values(ascending=False).index[:15]):
        texts = fetch_incident_notes(notes.sample(frac=1.0, random_state=config.RANDOM_SEED),
                                     reference)
        own = notes[notes["incident_reference"] == reference].sort_values("note_sequence")
        assert len(texts) == len(own), (
            "Reading the notes of "
            + reference
            + " returned "
            + str(len(texts))
            + " of its "
            + str(len(own))
            + ". Every note of the incident is read, whatever its length."
        )
        assert list(texts) == list(own[config.NOTE_TEXT_COLUMN]), (
            "The notes of "
            + reference
            + " came back as "
            + str([text[:30] for text in texts])
            + " where, in the order they were written, they are "
            + str([text[:30] for text in own[config.NOTE_TEXT_COLUMN]])
            + ". The notes were handed over shuffled, and a later note corrects an earlier "
            "one, so they are put back in the order they were written."
        )

    reference = str(incidents["incident_reference"].iloc[0])
    profile = fetch_incident_profile(incidents, reference)
    assert profile["incident_reference"] == reference and set(incidents.columns) <= set(profile), (
        "The profile fetched for "
        + reference
        + " is not that incident's row with every column the queue holds."
    )
    unknown = "INC-" + config.HUB_CODE_BY_HUB[config.VALID_HUBS[0]] + "-9999999"
    for reader in [fetch_incident_profile, fetch_incident_notes]:
        refused = False
        try:
            reader(incidents if reader is fetch_incident_profile else notes, unknown)
        except ValueError:
            refused = True
        assert refused, (
            reader.__name__
            + " did not raise a ValueError for "
            + unknown
            + ", which is not in the queue. An assessment opened on an incident that does "
            "not exist has to stop before it spends a language model call, and the "
            "service turns that ValueError into its refusal."
        )


def test_every_document_gives_up_its_text():
    import os

    from config import config
    from knowledge.pdf_extraction import extract_text_from_directory

    in_folder = sorted(name for name in os.listdir(config.DOCS_DIRECTORY)
                       if name.lower().endswith(".pdf"))
    documents = extract_text_from_directory(config.DOCS_DIRECTORY)
    assert len(documents) > 0 and {"document_name", "document_text"} <= set(documents[0]), (
        "Reading the document folder returned "
        + str(len(documents))
        + " entries"
        + ("" if len(documents) == 0 else ", the first keyed " + str(sorted(documents[0])))
        + ", where every entry names its document and carries its text."
    )
    names = sorted(document["document_name"] for document in documents)
    assert names == in_folder, (
        "Reading the document folder returned "
        + str(names)
        + " where the folder holds "
        + str(in_folder)
        + ". A document never read is a question answered from general knowledge instead."
    )
    for document in documents:
        assert len(document["document_text"].split()) > 200, (
            document["document_name"]
            + " gave up only "
            + str(len(document["document_text"].split()))
            + " words. A PDF that will not give up its text is indexed as an empty passage."
        )
    total_words = sum(len(document["document_text"].split()) for document in documents)
    assert total_words >= 8500, (
        "The "
        + str(len(in_folder))
        + " documents gave up "
        + str(total_words)
        + " words between them, where every page read in full gives well over 8,500. A "
        "reader that stops early loses the later sections, and a question about them is "
        "answered from nothing."
    )
    for required in (list(config.PROCEDURE_DOCUMENT_BY_CODE.values())
                     + list(config.PLAYBOOK_DOCUMENT_BY_ATTACK_TYPE.values())):
        assert required in names, (
            required
            + " was not read, and the configuration sends questions to it by name."
        )


def test_documents_are_cut_into_passages_of_about_the_configured_size_without_page_headers():
    import re

    from config import config
    from knowledge.chunk_splitting import build_chunk_records, split_documents_into_sections
    from knowledge.pdf_extraction import extract_text_from_directory

    documents = extract_text_from_directory(config.DOCS_DIRECTORY)
    sections = split_documents_into_sections(documents)
    chunks = build_chunk_records(sections, config.CHUNK_SIZE_CHARACTERS,
                                 config.CHUNK_OVERLAP_CHARACTERS)
    assert len(chunks) > 0 and {"chunk_id", "chunk_text", "document_name"} <= set(chunks[0]), (
        "Cutting the documents returned "
        + str(len(chunks))
        + " passages"
        + ("" if len(chunks) == 0 else ", the first keyed " + str(sorted(chunks[0])))
        + ", where every passage carries its identifier, its text and its document."
    )
    assert len(sections) > len(documents), (
        str(len(documents))
        + " documents split into "
        + str(len(sections))
        + " sections. Each document is written in numbered sections, and a section is "
        "the unit a question is usually about."
    )
    with_header = [chunk["chunk_id"] for chunk in chunks
                   if re.search(config.DOCUMENT_HEADER_PATTERN, chunk["chunk_text"])]
    assert len(with_header) == 0, (
        "These passages still carry the running page header: "
        + str(with_header[:5])
        + ". The header repeats on every document, so it matches every question equally "
        "and pushes the passages that answer it out of the results."
    )
    lengths = [len(chunk["chunk_text"]) for chunk in chunks]
    average = sum(lengths) / len(lengths)
    assert config.CHUNK_SIZE_CHARACTERS / 5 <= average <= config.CHUNK_SIZE_CHARACTERS, (
        "Passages average "
        + str(int(average))
        + " characters where the configuration asks for passages of up to "
        + str(config.CHUNK_SIZE_CHARACTERS)
        + ". Passages far longer return a whole document for every question; far "
        "shorter lose the sentence that gave them their meaning."
    )
    assert max(lengths) <= 2 * config.CHUNK_SIZE_CHARACTERS, (
        "The longest passage runs to "
        + str(max(lengths))
        + " characters, far beyond the "
        + str(config.CHUNK_SIZE_CHARACTERS)
        + " the configuration asks for."
    )
    ids = [chunk["chunk_id"] for chunk in chunks]
    assert len(ids) == len(set(ids)), (
        "Passage identifiers repeat, so storing them would overwrite one passage with "
        "another."
    )
    words_by_document = {document["document_name"]: set(document["document_text"].split())
                         for document in documents}
    for chunk in chunks:
        words = chunk["chunk_text"].split()
        foreign = [word for word in words if word not in words_by_document.get(
            chunk["document_name"], set())]
        assert len(words) > 0 and len(foreign) <= len(words) // 10, (
            "Passage "
            + str(chunk["chunk_id"])
            + " says it comes from "
            + str(chunk["document_name"])
            + " but "
            + str(len(foreign))
            + " of its "
            + str(len(words))
            + " words are not in that document, for example "
            + str(foreign[:5])
            + ". A passage has to cite the document it was cut from."
        )

    lines = ["Line " + first + second + " of the overlap check names gateway " + first + second
             + "." for first in "abcdefgh" for second in "abcdefgh"][:60]
    synthetic = [{"document_name": "Overlap-Check.pdf",
                  "document_text": "1. Overlap check\n" + " ".join(lines)}]
    pieces = [str(chunk["chunk_text"]) for chunk in build_chunk_records(
        split_documents_into_sections(synthetic), config.CHUNK_SIZE_CHARACTERS,
        config.CHUNK_OVERLAP_CHARACTERS)]
    assert len(pieces) >= 3, (
        "One numbered section of "
        + str(len(" ".join(lines)))
        + " characters was cut into "
        + str(len(pieces))
        + " passages, where passages of up to "
        + str(config.CHUNK_SIZE_CHARACTERS)
        + " characters need at least three."
    )
    unshared = [position for position in range(1, len(pieces))
                if pieces[position].strip()[:20] not in pieces[position - 1]]
    assert len(unshared) == 0, (
        "Passages "
        + str(unshared)
        + " of one long section open with text the passage before them does not carry. "
        "Neighbouring passages of a section overlap by about "
        + str(config.CHUNK_OVERLAP_CHARACTERS)
        + " characters, so a sentence cut at a boundary is still whole in one of them."
    )


def test_the_index_holds_every_passage_once_with_the_document_it_came_from(
        knowledge_collection):
    from config import config
    from knowledge.chunk_splitting import build_chunk_records, split_documents_into_sections
    from knowledge.pdf_extraction import extract_text_from_directory

    assert knowledge_collection["problem"] is None, knowledge_collection["problem"]
    collection = knowledge_collection["collection"]
    documents = extract_text_from_directory(config.DOCS_DIRECTORY)
    chunks = build_chunk_records(split_documents_into_sections(documents),
                                 config.CHUNK_SIZE_CHARACTERS, config.CHUNK_OVERLAP_CHARACTERS)
    stored = collection.get(include=["metadatas"])
    assert collection.count() == len(chunks) == len(stored["ids"]), (
        "The vector store holds "
        + str(collection.count())
        + " passages where cutting the documents gives "
        + str(len(chunks))
        + ". More means the index was added to twice and repeats itself in every result; "
        "fewer means passages no search can reach."
    )
    assert len(set(stored["ids"])) == len(stored["ids"]), (
        "Stored passage identifiers repeat, so one passage has overwritten another and its "
        "text can no longer be found."
    )
    names = {document["document_name"] for document in documents}
    cited = [metadata.get("document_name") for metadata in stored["metadatas"]]
    unnamed = [value for value in cited if value not in names]
    assert len(unnamed) == 0, (
        str(len(unnamed))
        + " stored passages name no document from the folder, for example "
        + str(unnamed[:3])
        + ". The name is what lets an answer cite its source and a search be narrowed "
        "to one procedure."
    )
    assert set(cited) == names, (
        "No stored passage comes from "
        + str(sorted(names - set(cited)))
        + ", so nothing in those documents can ever be found."
    )
    by_document = {}
    for chunk in chunks:
        by_document[chunk["document_name"]] = by_document.get(chunk["document_name"], 0) + 1
    stored_by_document = {name: cited.count(name) for name in names}
    assert stored_by_document == by_document, (
        "Passages stored per document "
        + str(stored_by_document)
        + " differ from passages cut per document "
        + str(by_document)
        + ". A document with passages missing answers less than it says."
    )


def test_a_search_narrowed_to_one_document_reads_only_that_document(knowledge_collection):
    from config import config
    from knowledge.vector_index import search_documents

    assert knowledge_collection["problem"] is None, knowledge_collection["problem"]
    collection = knowledge_collection["collection"]
    questions = ["Which reports are due, and within how many hours?",
                 "Who must be told, and what must the report contain?"]
    for document_name in config.PROCEDURE_DOCUMENT_BY_CODE.values():
        results = search_documents(collection, questions, config.PROCEDURE_RESULT_COUNT,
                                   {"$eq": document_name})
        assert len(results) == len(questions), (
            "Searching with "
            + str(len(questions))
            + " questions returned "
            + str(len(results))
            + " result lists, one per question."
        )
        for question, passages in zip(questions, results):
            assert all({"chunk_id", "chunk_text", "document_name", "distance"} <= set(passage)
                       for passage in passages), (
                "A passage returned by the search carries only "
                + str(sorted(passages[0]) if passages else [])
                + ", where each names its identifier, its text, its document and its distance."
            )
            assert len(passages) == config.PROCEDURE_RESULT_COUNT, (
                "Asking "
                + repr(question)
                + " of "
                + document_name
                + " returned "
                + str(len(passages))
                + " passages where "
                + str(config.PROCEDURE_RESULT_COUNT)
                + " were asked for."
            )
            strays = sorted({passage["document_name"] for passage in passages} - {document_name})
            assert len(strays) == 0, (
                "A search narrowed to "
                + document_name
                + " returned passages from "
                + str(strays)
                + ". The three procedures share most of their sentences, and a passage "
                "from the wrong one states the wrong deadline."
            )
            distances = [passage["distance"] for passage in passages]
            assert distances == sorted(distances), (
                "Passages came back in the order "
                + str(distances)
                + ", not closest first. The first passage is the one an answer is grounded on."
            )
            assert all(passage["chunk_text"].strip() and passage["chunk_id"]
                       for passage in passages), (
                "A passage came back without its text or its identifier."
            )

    excluded = config.CHAT_EXCLUDED_DOCUMENTS
    wide = search_documents(collection, ["What happened in earlier incidents?"],
                            config.RETRIEVAL_RESULT_COUNT, {"$nin": excluded})[0]
    assert len(wide) == config.RETRIEVAL_RESULT_COUNT and not any(
            passage["document_name"] in excluded for passage in wide), (
        "A search told to leave out "
        + str(excluded)
        + " returned "
        + str([passage["document_name"] for passage in wide])
        + ". The casebook describes real past incidents and must never reach an answer."
    )


def test_customer_steps_come_from_the_playbook_for_that_attack(knowledge_collection):
    from config import config
    from knowledge.vector_index import search_documents
    from tools.retrieval_tools import read_customer_steps

    assert knowledge_collection["problem"] is None, knowledge_collection["problem"]
    collection = knowledge_collection["collection"]
    for attack_type, playbook in config.PLAYBOOK_DOCUMENT_BY_ATTACK_TYPE.items():
        steps = read_customer_steps(collection, attack_type)
        assert 0 < len(steps) <= config.PLAYBOOK_RESULT_COUNT, (
            "The customer steps for "
            + attack_type
            + " came back as "
            + str(len(steps))
            + " passages where up to "
            + str(config.PLAYBOOK_RESULT_COUNT)
            + " are wanted."
        )
        strays = sorted({step["document_name"] for step in steps} - {playbook})
        assert len(strays) == 0, (
            "The customer steps for "
            + attack_type
            + " were read from "
            + str(strays)
            + " as well as "
            + playbook
            + ". Customers of a ransomware incident told to watch for phishing emails are "
            "told the wrong thing."
        )
        closest = search_documents(collection,
                                   [config.CUSTOMER_STEPS_QUESTION_TEMPLATE % attack_type],
                                   config.PLAYBOOK_RESULT_COUNT, {"$eq": playbook})[0]
        assert (sorted(str(step["chunk_id"]) for step in steps)
                == sorted(str(passage["chunk_id"]) for passage in closest)), (
            "The customer steps for "
            + attack_type
            + " are the passages "
            + str(sorted(str(step["chunk_id"]) for step in steps))
            + ", where the passages of "
            + playbook
            + " closest to the configured question about what affected customers should do "
            "are "
            + str(sorted(str(passage["chunk_id"]) for passage in closest))
            + ". The steps are the playbook's answer to that question, not any passage of it."
        )


def test_each_procedure_is_read_from_its_own_document(knowledge_collection, planted_collection):
    from config import config
    from knowledge.procedure_reading import read_procedure_deadlines

    assert knowledge_collection["problem"] is None, knowledge_collection["problem"]
    assert planted_collection["problem"] is None, planted_collection["problem"]
    readings = {}
    for procedure_code in config.PROCEDURE_OPTIONS:
        own_document = config.PROCEDURE_DOCUMENT_BY_CODE[procedure_code]
        reading = read_procedure_deadlines(knowledge_collection["collection"], procedure_code)
        missing = sorted({"milestones", "filed_milestones", "source_documents", "passages"}
                         - set(reading))
        assert len(missing) == 0, (
            procedure_code
            + " was read back with no "
            + str(missing)
            + ", so its deadlines cannot be worked out."
        )
        readings[procedure_code] = reading
        assert sorted(reading["source_documents"]) == [own_document], (
            procedure_code
            + " was read from "
            + str(reading["source_documents"])
            + " instead of "
            + own_document
            + " alone. The three procedures are written almost word for word alike, so a "
            "search across all of them reads one procedure's deadline into another."
        )
        passage_text = " ".join(passage["chunk_text"] for passage in reading["passages"])
        assert len(reading["milestones"]) > 0, (
            "No deadline was read from "
            + own_document
            + ". A procedure read with no deadline starts no clock, and the incident looks as "
            "if nothing is due."
        )
        for milestone in reading["milestones"]:
            missing = sorted({"milestone", "hours", "clock_start_phrase", "clock_start_column"}
                             - set(milestone))
            assert len(missing) == 0, (
                "A deadline read from "
                + own_document
                + " has no "
                + str(missing)
                + "."
            )
            assert milestone["clock_start_phrase"] in config.CLOCK_START_COLUMN_BY_PHRASE, (
                procedure_code
                + " starts "
                + repr(milestone["milestone"])
                + " from "
                + repr(milestone["clock_start_phrase"])
                + ", which is not a start the configuration recognises."
            )
            assert (milestone["clock_start_column"]
                    == config.CLOCK_START_COLUMN_BY_PHRASE[milestone["clock_start_phrase"]]), (
                procedure_code
                + " counts "
                + repr(milestone["milestone"])
                + " from the column "
                + str(milestone["clock_start_column"])
                + " although its document says it runs from "
                + milestone["clock_start_phrase"]
                + "."
            )
            assert (float(milestone["hours"]) > 0 and float(milestone["hours"]).is_integer()
                    and str(int(float(milestone["hours"]))) in passage_text), (
                procedure_code
                + " gives "
                + repr(milestone["milestone"])
                + " "
                + str(milestone["hours"])
                + " hours, a figure the passages read from "
                + own_document
                + " do not state."
            )
            assert str(milestone["milestone"]).lower() in passage_text.lower(), (
                procedure_code
                + " names a report "
                + repr(milestone["milestone"])
                + " that the passages read from "
                + own_document
                + " do not name."
            )
        own_milestones = {milestone["milestone"] for milestone in reading["milestones"]}
        for filed in reading["filed_milestones"]:
            assert (filed["after_milestone"] in own_milestones
                    and float(filed["months"]) > 0 and float(filed["months"]).is_integer()), (
                procedure_code
                + " sets "
                + repr(filed["milestone"])
                + " to follow "
                + repr(filed["after_milestone"])
                + " by "
                + str(filed["months"])
                + " months, which does not match a report of its own procedure."
            )

    statements = {code: sorted((milestone["milestone"], milestone["hours"],
                                milestone["clock_start_column"])
                               for milestone in reading["milestones"])
                  for code, reading in readings.items()}
    assert len({str(value) for value in statements.values()}) == len(statements), (
        "Two procedures read back identical deadlines: "
        + str(statements)
        + ". Each document sets its own, so identical readings mean one document was read "
        "for another."
    )
    assert any(reading["filed_milestones"] for reading in readings.values()), (
        "No procedure sets a report that runs from a filing, so the final report can "
        "never be dated."
    )

    for procedure_code, stated in planted_collection["milestones"].items():
        planted = read_procedure_deadlines(planted_collection["collection"], procedure_code)
        read_back = sorted((str(milestone["milestone"]).lower(), int(float(milestone["hours"])),
                            str(milestone["clock_start_column"]))
                           for milestone in planted["milestones"])
        expected = sorted((name, hours, config.CLOCK_START_COLUMN_BY_PHRASE[phrase])
                          for name, hours, phrase in stated)
        assert read_back == expected, (
            "From a store in which "
            + config.PROCEDURE_DOCUMENT_BY_CODE[procedure_code]
            + " states "
            + str(expected)
            + ", reading "
            + procedure_code
            + " returned "
            + str(read_back)
            + ". Every deadline is read from the passages retrieved from the procedure's own "
            "document, never supplied and never taken from another procedure."
        )
        filed_back = sorted((str(filed["milestone"]).lower(), int(float(filed["months"])),
                             str(filed["after_milestone"]).lower())
                            for filed in planted["filed_milestones"])
        assert filed_back == sorted(planted_collection["filed"][procedure_code]), (
            "From a store in which "
            + config.PROCEDURE_DOCUMENT_BY_CODE[procedure_code]
            + " sets the reports that follow a filing as "
            + str(sorted(planted_collection["filed"][procedure_code]))
            + ", reading "
            + procedure_code
            + " returned "
            + str(filed_back)
            + "."
        )


def test_procedure_01_decides_when_customers_need_not_be_told(
        knowledge_collection, planted_collection, open_queue):
    from config import config
    from knowledge.procedure_reading import read_customer_notice_exemption
    from tools.incident_data_tools import fetch_incident_profile
    from tools.retrieval_tools import read_reporting_duties

    assert knowledge_collection["problem"] is None, knowledge_collection["problem"]
    assert planted_collection["problem"] is None, planted_collection["problem"]
    assert open_queue["problem"] is None, open_queue["problem"]
    collection = knowledge_collection["collection"]
    exemption = read_customer_notice_exemption(collection,
                                               config.PROCEDURE_EU_PERSONAL_DATA_BREACH)
    missing = sorted({"exempt_protection_states", "source_documents", "passages"}
                     - set(exemption))
    assert len(missing) == 0, (
        "The exemption was read back with no "
        + str(missing)
        + ", so whether customers must be told cannot be decided."
    )
    eu_document = config.PROCEDURE_DOCUMENT_BY_CODE[config.PROCEDURE_EU_PERSONAL_DATA_BREACH]
    exempt = sorted(exemption["exempt_protection_states"])
    passage_text = " ".join(passage["chunk_text"] for passage in exemption["passages"])
    assert sorted(exemption["source_documents"]) == [eu_document], (
        "The exemption was read from "
        + str(exemption["source_documents"])
        + " instead of "
        + eu_document
        + ". Only Procedure 01 says when customers need not be told."
    )
    assert len(exempt) > 0 and set(exempt) <= set(config.VALID_PROTECTION_STATES), (
        "The exemption names "
        + str(exempt)
        + ", which is not a non-empty set of protection states the company records."
    )
    assert all(state in passage_text for state in exempt), (
        "The exemption names "
        + str(exempt)
        + ", which the passages read from "
        + eu_document
        + " do not state."
    )
    planted_states = planted_collection["exempt"]
    planted = read_customer_notice_exemption(planted_collection["collection"],
                                             config.PROCEDURE_EU_PERSONAL_DATA_BREACH)
    assert (sorted(planted["exempt_protection_states"])
            == sorted(planted_states[config.PROCEDURE_EU_PERSONAL_DATA_BREACH])), (
        "From a store in which "
        + eu_document
        + " names "
        + str(sorted(planted_states[config.PROCEDURE_EU_PERSONAL_DATA_BREACH]))
        + " as excusing a customer notice, and "
        + config.PROCEDURE_DOCUMENT_BY_CODE[config.PROCEDURE_SIGNIFICANT_INCIDENT]
        + " names "
        + str(planted_states[config.PROCEDURE_SIGNIFICANT_INCIDENT])
        + ", the exemption was read as "
        + str(sorted(planted["exempt_protection_states"]))
        + ". It is read from Procedure 01's own passages, never supplied."
    )

    incidents = open_queue["incidents"]
    profile = dict(fetch_incident_profile(incidents, str(incidents["incident_reference"].iloc[0])))
    profile.update({"personal_data_involved_flag": config.BOOLEAN_YES,
                    config.EU_DATA_SUBJECTS_COLUMN: 5000})
    exposed = [state for state in config.VALID_PROTECTION_STATES if state not in exempt][0]
    notice_band = config.CUSTOMER_NOTICE_HARM_BANDS[0]
    quieter_band = [band for band in config.HARM_BAND_OPTIONS
                    if band not in config.CUSTOMER_NOTICE_HARM_BANDS][0]
    eu_only = [config.PROCEDURE_EU_PERSONAL_DATA_BREACH]
    for protection, band, applicable, must_tell in [
            (exposed, notice_band, eu_only, True),
            (exempt[0], notice_band, eu_only, False),
            (exposed, quieter_band, eu_only, False),
            (exposed, notice_band, [config.PROCEDURE_INDIA_CYBER_INCIDENT], False)]:
        case = dict(profile, data_protection_state=protection)
        duties = read_reporting_duties(collection, applicable, case, band)
        missing = sorted({"customer_notice_required", "exempt_protection_states"} - set(duties))
        assert len(missing) == 0, (
            "Reading the reporting duties returned no "
            + str(missing)
            + ", so whether customers must be told cannot be read."
        )
        assert bool(duties["customer_notice_required"]) == must_tell, (
            "With "
            + str(applicable)
            + " applying, a "
            + band
            + " band and data "
            + protection
            + ", customers were "
            + ("" if duties["customer_notice_required"] else "not ")
            + "to be told. Procedure 01 requires telling them only when it applies, the "
            "risk is high, and the protection in place is not one it names as excusing it."
        )
        if config.PROCEDURE_EU_PERSONAL_DATA_BREACH not in applicable:
            assert len(duties["exempt_protection_states"]) == 0, (
                "An incident Procedure 01 does not cover was given its exemption "
                + str(duties["exempt_protection_states"])
                + "."
            )


def test_the_procedures_that_apply_follow_from_the_facts_of_the_incident(open_queue):
    from config import config
    from tools.deadline_tools import select_applicable_procedures
    from tools.incident_data_tools import fetch_incident_profile

    assert open_queue["problem"] is None, open_queue["problem"]
    incidents = open_queue["incidents"]
    base = dict(fetch_incident_profile(incidents, str(incidents["incident_reference"].iloc[0])))
    base.update({"personal_data_involved_flag": config.BOOLEAN_NO,
                 config.EU_DATA_SUBJECTS_COLUMN: 0, config.INDIA_DATA_SUBJECTS_COLUMN: 0,
                 "hosting_region": [region for region in config.VALID_HOSTING_REGIONS
                                    if region not in config.INDIA_HOSTING_REGIONS][0],
                 "service_outage_minutes": 0, "direct_financial_loss_eur": 0,
                 "customers_affected_count": 0, config.CAMPAIGN_COLUMN: config.NO_CAMPAIGN_VALUE})
    band_in = config.EU_PROCEDURE_HARM_BANDS[0]
    eu = config.PROCEDURE_EU_PERSONAL_DATA_BREACH
    significant = config.PROCEDURE_SIGNIFICANT_INCIDENT
    india = config.PROCEDURE_INDIA_CYBER_INCIDENT
    personal = {"personal_data_involved_flag": config.BOOLEAN_YES,
                config.EU_DATA_SUBJECTS_COLUMN: 1}

    cases = [("nothing that triggers a procedure", {}, band_in, set()),
             ("EU data subjects but no personal data", {config.EU_DATA_SUBJECTS_COLUMN: 1},
              band_in, set()),
             ("Indian data subjects", {config.INDIA_DATA_SUBJECTS_COLUMN: 1}, band_in, {india})]
    cases += [("EU personal data at the " + band + " band", personal, band,
               {eu} if band in config.EU_PROCEDURE_HARM_BANDS else set())
              for band in config.HARM_BAND_OPTIONS]
    cases += [("systems hosted in " + region, {"hosting_region": region}, band_in,
               {india} if region in config.INDIA_HOSTING_REGIONS else set())
              for region in config.VALID_HOSTING_REGIONS]
    for column_name, threshold in [("service_outage_minutes", config.SIGNIFICANT_OUTAGE_MINUTES),
                                   ("direct_financial_loss_eur",
                                    config.SIGNIFICANT_DIRECT_LOSS_EUR),
                                   ("customers_affected_count",
                                    config.SIGNIFICANT_CUSTOMERS_ACROSS_CAMPAIGN)]:
        cases += [(column_name + " one over its threshold", {column_name: threshold + 1},
                   band_in, {significant}),
                  (column_name + " exactly at its threshold", {column_name: threshold},
                   band_in, set())]

    for description, changes, band, expected in cases:
        profile = dict(base, **changes)
        campaign = [{column: profile[column] for column in config.CAMPAIGN_INCIDENT_COLUMNS}]
        found = select_applicable_procedures(profile, band, campaign)
        missing = sorted({"applicable_procedures", "grounds"} - set(found))
        assert len(missing) == 0, (
            "Working out which procedures apply returned no "
            + str(missing)
            + "."
        )
        assert set(found["applicable_procedures"]) == expected, (
            "An incident with "
            + description
            + " came out as "
            + str(found["applicable_procedures"])
            + " where the rules give "
            + str(sorted(expected))
            + "."
        )
        grounded = {code for code, reason in dict(found["grounds"]).items()
                    if str(reason).strip()}
        assert grounded == expected, (
            "An incident with "
            + description
            + " gives grounds for "
            + str(sorted(grounded))
            + ". Every procedure that applies says why, and no other does."
        )


def test_customers_are_counted_across_the_campaign_and_only_within_it(open_queue):
    from config import config
    from tools.deadline_tools import select_applicable_procedures
    from tools.incident_data_tools import fetch_campaign_incidents, fetch_incident_profile

    assert open_queue["problem"] is None, open_queue["problem"]
    incidents = open_queue["incidents"]
    linked_rows = incidents[incidents[config.CAMPAIGN_COLUMN] != config.NO_CAMPAIGN_VALUE]
    alone_rows = incidents[incidents[config.CAMPAIGN_COLUMN] == config.NO_CAMPAIGN_VALUE]
    linked = dict(fetch_incident_profile(incidents, str(linked_rows["incident_reference"].iloc[0])))
    alone = dict(fetch_incident_profile(incidents, str(alone_rows["incident_reference"].iloc[0])))

    campaign = fetch_campaign_incidents(incidents, linked)
    same_campaign = incidents[incidents[config.CAMPAIGN_COLUMN] == linked[config.CAMPAIGN_COLUMN]]
    assert (sorted(entry["incident_reference"] for entry in campaign)
            == sorted(same_campaign["incident_reference"])), (
        "The campaign of "
        + linked["incident_reference"]
        + " came back as "
        + str(sorted(entry["incident_reference"] for entry in campaign))
        + " where the queue links "
        + str(sorted(same_campaign["incident_reference"]))
        + "."
    )
    solo = fetch_campaign_incidents(incidents, alone)
    assert [entry["incident_reference"] for entry in solo] == [alone["incident_reference"]], (
        "An incident outside any campaign came back with "
        + str([entry["incident_reference"] for entry in solo])
        + " as its campaign. It is judged alone."
    )

    threshold = config.SIGNIFICANT_CUSTOMERS_ACROSS_CAMPAIGN
    quiet = {"service_outage_minutes": 0, "direct_financial_loss_eur": 0}
    own = dict(linked, customers_affected_count=threshold // 2 + 1, **quiet)
    partner = {column: own[column] for column in config.CAMPAIGN_INCIDENT_COLUMNS}
    partner.update({"incident_reference": "INC-" + config.HUB_CODE_BY_HUB[own["soc_hub"]]
                    + "-9999998", "customers_affected_count": threshold // 2 + 1})
    together = [{column: own[column] for column in config.CAMPAIGN_INCIDENT_COLUMNS}, partner]
    band = config.HARM_BAND_LOW
    counted = select_applicable_procedures(own, band, together)
    missing = sorted({"applicable_procedures", "customers_across_campaign",
                      "significant_only_with_campaign"} - set(counted))
    assert len(missing) == 0, (
        "Working out which procedures apply returned no "
        + str(missing)
        + ", so the campaign's customers cannot be read."
    )
    assert config.PROCEDURE_SIGNIFICANT_INCIDENT in counted["applicable_procedures"], (
        "An incident with "
        + str(own["customers_affected_count"])
        + " customers in a campaign of "
        + str(sum(entry["customers_affected_count"] for entry in together))
        + " is not significant. Procedure 02 counts customers across the campaign."
    )
    assert counted["customers_across_campaign"] == sum(
            entry["customers_affected_count"] for entry in together), (
        "Customers across the campaign were counted as "
        + str(counted["customers_across_campaign"])
        + ". Procedure 02 adds up the customers of every incident in the campaign."
    )
    assert bool(counted["significant_only_with_campaign"]), (
        "An incident significant only because of its campaign is not marked as such, so "
        "the analyst cannot see why it is being reported."
    )

    judged_alone = dict(own, **{config.CAMPAIGN_COLUMN: config.NO_CAMPAIGN_VALUE})
    by_itself = select_applicable_procedures(
        judged_alone, band, [{column: judged_alone[column]
                              for column in config.CAMPAIGN_INCIDENT_COLUMNS}])
    assert config.PROCEDURE_SIGNIFICANT_INCIDENT not in by_itself["applicable_procedures"], (
        "The same incident outside any campaign, with "
        + str(judged_alone["customers_affected_count"])
        + " customers, is still significant."
    )
    big_alone = dict(own, customers_affected_count=threshold + 1)
    big = select_applicable_procedures(
        big_alone, band, [{column: big_alone[column]
                           for column in config.CAMPAIGN_INCIDENT_COLUMNS}, partner])
    assert not bool(big["significant_only_with_campaign"]), (
        "An incident over the threshold on its own customers is marked as significant only "
        "with its campaign."
    )


def test_only_the_procedures_that_apply_are_read_and_cited(knowledge_collection, open_queue):
    from config import config
    from tools.incident_data_tools import fetch_incident_profile
    from tools.retrieval_tools import read_reporting_duties

    assert knowledge_collection["problem"] is None, knowledge_collection["problem"]
    assert open_queue["problem"] is None, open_queue["problem"]
    incidents = open_queue["incidents"]
    profile = fetch_incident_profile(incidents, str(incidents["incident_reference"].iloc[0]))
    eu = config.PROCEDURE_EU_PERSONAL_DATA_BREACH
    significant = config.PROCEDURE_SIGNIFICANT_INCIDENT
    india = config.PROCEDURE_INDIA_CYBER_INCIDENT
    for applicable in [[], [india], [eu, significant], [eu, significant, india]]:
        duties = read_reporting_duties(knowledge_collection["collection"], applicable, profile,
                                       config.HARM_BAND_HIGH)
        missing = sorted({"procedure_readings", "passages", "customer_notice_required"}
                         - set(duties))
        assert len(missing) == 0, (
            "Reading the reporting duties returned no "
            + str(missing)
            + "."
        )
        assert set(duties["procedure_readings"]) == set(applicable), (
            "With "
            + str(applicable)
            + " applying, procedures "
            + str(sorted(duties["procedure_readings"]))
            + " were read. A procedure that does not apply sets no deadline."
        )
        allowed = {config.PROCEDURE_DOCUMENT_BY_CODE[code] for code in applicable}
        cited = {passage["document_name"] for passage in duties["passages"]}
        assert cited == allowed, (
            "With "
            + str(applicable)
            + " applying, the passages handed to the advisor come from "
            + str(sorted(cited))
            + " where they should come from "
            + str(sorted(allowed))
            + ". A passage from a procedure that does not apply invites the model to state "
            "its deadline."
        )
        if not applicable:
            assert not bool(duties["customer_notice_required"]), (
                "An incident no procedure covers was still found to need a customer notice."
            )


def test_each_clock_runs_from_its_own_start(open_queue, invented_readings):
    import pandas as pd

    from config import config
    from tools.deadline_tools import compute_procedure_deadlines
    from tools.incident_data_tools import fetch_incident_profile

    assert open_queue["problem"] is None, open_queue["problem"]
    incidents = open_queue["incidents"]
    confirmed_rows = incidents[incidents[config.AWARENESS_COLUMN].notna()]
    profile = dict(fetch_incident_profile(incidents,
                                          str(confirmed_rows["incident_reference"].iloc[0])))
    start_of = {(code, milestone["milestone"]): milestone["clock_start_column"]
                for code, reading in invented_readings.items()
                for milestone in reading["milestones"]}
    first_facts = compute_procedure_deadlines(profile, invented_readings)
    missing = sorted({"milestones", "earliest_milestone"} - set(first_facts))
    missing += sorted({"procedure_code", "milestone", "due_at", "clock_started",
                       "hours_remaining"} - set(first_facts["milestones"][0])
                      if "milestones" in first_facts and first_facts["milestones"] else [])
    assert len(missing) == 0, (
        "The deadlines worked out carry no "
        + str(missing)
        + ", so no clock can be read from them."
    )
    baseline = {(line["procedure_code"], line["milestone"]): line["due_at"]
                for line in first_facts["milestones"]}
    assert set(baseline) == set(start_of), (
        "The deadlines computed are "
        + str(sorted(baseline))
        + " where the readings given set "
        + str(sorted(start_of))
        + ". Every milestone of every procedure given gets a line of its own."
    )
    for moved_column, shift_hours in [(config.FIRST_ALERT_COLUMN, 2),
                                      (config.AWARENESS_COLUMN, 3)]:
        earlier = dict(profile)
        shifted = pd.Timestamp(profile[moved_column]) - pd.Timedelta(hours=shift_hours)
        earlier[moved_column] = (shifted.isoformat() if isinstance(profile[moved_column], str)
                                 else shifted)
        moved = {(line["procedure_code"], line["milestone"]): line["due_at"]
                 for line in compute_procedure_deadlines(earlier, invented_readings)["milestones"]}
        for key, column_name in start_of.items():
            gap = (pd.to_datetime(baseline[key], utc=True)
                   - pd.to_datetime(moved[key], utc=True)).total_seconds() / 3600
            expected_gap = shift_hours if column_name == moved_column else 0
            assert abs(gap - expected_gap) < 0.001, (
                "Moving "
                + moved_column
                + " "
                + str(shift_hours)
                + " hours earlier moved "
                + str(key)
                + " by "
                + str(round(gap, 2))
                + " hours. That deadline runs from "
                + column_name
                + ", so it moves "
                + ("with it" if expected_gap else "not at all")
                + ". Counting every clock from one start makes at least one deadline wrong."
            )

    unconfirmed_rows = incidents[incidents[config.AWARENESS_COLUMN].isna()]
    assert len(unconfirmed_rows) > 0, (
        "The live queue holds no incident awaiting confirmation, so the clock that has not "
        "started cannot be tried."
    )
    waiting = fetch_incident_profile(incidents, str(unconfirmed_rows["incident_reference"].iloc[0]))
    facts = compute_procedure_deadlines(waiting, invented_readings)
    for line in facts["milestones"]:
        runs_from_alert = (start_of[(line["procedure_code"], line["milestone"])]
                           == config.FIRST_ALERT_COLUMN)
        assert bool(line["clock_started"]) == runs_from_alert, (
            str((line["procedure_code"], line["milestone"]))
            + " is "
            + ("running" if line["clock_started"] else "not running")
            + " for an incident not yet confirmed. A clock from the first alert is already "
            "running; a clock from awareness has not started."
        )
        if runs_from_alert:
            assert not pd.isna(line["due_at"]) and not pd.isna(line["hours_remaining"]), (
                "The deadline that runs from the first alert has no due time although its "
                "clock is running."
            )
        else:
            assert pd.isna(line["due_at"]) and pd.isna(line["hours_remaining"]), (
                str((line["procedure_code"], line["milestone"]))
                + " was given a due time for an incident nobody has confirmed. A deadline "
                "counted from a moment that has not happened is invented."
            )
    earliest = facts["earliest_milestone"]
    assert (earliest is not None
            and start_of[(earliest["procedure_code"], earliest["milestone"])]
            == config.FIRST_ALERT_COLUMN), (
        "The earliest deadline of an unconfirmed incident was "
        + str(facts["earliest_milestone"])
        + ". Only the clock from the first alert is running, so it is the earliest."
    )


def test_the_earliest_deadline_is_the_minimum_over_every_running_clock(
        open_queue, invented_readings):
    import pandas as pd

    from config import config
    from tools.deadline_tools import compute_procedure_deadlines, select_applicable_procedures
    from tools.incident_data_tools import fetch_incident_profile

    assert open_queue["problem"] is None, open_queue["problem"]
    incidents = open_queue["incidents"]
    for reference in list(incidents["incident_reference"][:60]):
        profile = fetch_incident_profile(incidents, reference)
        facts = compute_procedure_deadlines(profile, invented_readings)
        running = [line for line in facts["milestones"] if line["clock_started"]]
        earliest = facts["earliest_milestone"]
        assert len(running) > 0, (
            reference
            + " has no running clock, although the readings given include deadlines counted "
            "from the first alert, which every incident has."
        )
        lowest = min(line["hours_remaining"] for line in running)
        assert earliest is not None and abs(earliest["hours_remaining"] - lowest) < 0.001, (
            reference
            + " was given an earliest deadline "
            + str(None if earliest is None else earliest["hours_remaining"])
            + " hours away when its running clocks leave as little as "
            + str(lowest)
            + ". The deadline that matters is the minimum over every applicable procedure."
        )

    eu_only = None
    for reference in incidents["incident_reference"]:
        profile = dict(fetch_incident_profile(incidents, reference))
        if pd.isna(profile[config.AWARENESS_COLUMN]):
            continue
        found = select_applicable_procedures(
            profile, config.HARM_BAND_HIGH,
            [{column: profile[column] for column in config.CAMPAIGN_INCIDENT_COLUMNS}])
        if set(found["applicable_procedures"]) == {config.PROCEDURE_EU_PERSONAL_DATA_BREACH}:
            eu_only = profile
            break
    assert eu_only is not None, (
        "No confirmed live incident comes out under Procedure 01 alone, so adding Indian "
        "users to one cannot be tried."
    )

    eu_reading = {config.PROCEDURE_EU_PERSONAL_DATA_BREACH:
                  invented_readings[config.PROCEDURE_EU_PERSONAL_DATA_BREACH]}
    before = compute_procedure_deadlines(eu_only, eu_reading)["earliest_milestone"]
    with_india = dict(eu_only, **{config.INDIA_DATA_SUBJECTS_COLUMN: 1500})
    after_codes = select_applicable_procedures(
        with_india, config.HARM_BAND_HIGH,
        [{column: with_india[column] for column in config.CAMPAIGN_INCIDENT_COLUMNS}]
    )["applicable_procedures"]
    after = compute_procedure_deadlines(
        with_india, {code: invented_readings[code] for code in after_codes})["earliest_milestone"]
    assert config.PROCEDURE_INDIA_CYBER_INCIDENT in after_codes, (
        "Adding Indian users to "
        + eu_only["incident_reference"]
        + " did not bring in "
        + config.PROCEDURE_INDIA_CYBER_INCIDENT
        + ". Indian data subjects bring the India procedure in on their own."
    )
    assert after["hours_remaining"] < before["hours_remaining"], (
        "Adding Indian users to "
        + eu_only["incident_reference"]
        + " left the earliest deadline "
        + str(after["hours_remaining"])
        + " hours away, where it was "
        + str(before["hours_remaining"])
        + ". The procedure whose deadline falls soonest comes first."
    )


def test_hours_left_are_counted_from_the_snapshot_not_the_wall_clock(open_queue,
                                                                     invented_readings):
    import pandas as pd

    from config import config
    from tools.deadline_tools import compute_procedure_deadlines
    from tools.incident_data_tools import fetch_incident_profile

    assert open_queue["problem"] is None, open_queue["problem"]
    incidents = open_queue["incidents"]
    snapshot = pd.to_datetime(config.SNAPSHOT_AT_UTC, utc=True)
    confirmed_rows = incidents[incidents[config.AWARENESS_COLUMN].notna()]
    hours_by_key = {(code, milestone["milestone"]): (milestone["hours"],
                                                     milestone["clock_start_column"])
                    for code, reading in invented_readings.items()
                    for milestone in reading["milestones"]}
    overdue_seen = running_seen = False
    for reference in list(confirmed_rows["incident_reference"][:25]):
        profile = fetch_incident_profile(incidents, reference)
        first = compute_procedure_deadlines(profile, invented_readings)
        missing = sorted({"started_at", "due_at", "hours_remaining", "overdue",
                          "due_at_hub_time"} - set(first["milestones"][0]))
        assert len(missing) == 0, (
            "A deadline worked out for "
            + reference
            + " carries no "
            + str(missing)
            + "."
        )
        second = compute_procedure_deadlines(profile, invented_readings)
        assert first == second, (
            "Working out the deadlines of "
            + reference
            + " twice gave two different answers. The same incident at the same snapshot has "
            "one set of deadlines."
        )
        zone = config.HUB_TIME_ZONE_BY_HUB[profile["soc_hub"]]
        for line in first["milestones"]:
            hours, start_column = hours_by_key[(line["procedure_code"], line["milestone"])]
            started = pd.to_datetime(profile[start_column], utc=True)
            due = pd.to_datetime(line["due_at"], utc=True)
            assert pd.to_datetime(line["started_at"], utc=True) == started, (
                str((reference, line["milestone"]))
                + " started at "
                + str(line["started_at"])
                + " where "
                + start_column
                + " is "
                + str(started)
                + ". Each deadline runs from its own moment, read in UTC."
            )
            assert (due - started).total_seconds() / 3600 == hours, (
                str((reference, line["milestone"]))
                + " falls due "
                + str((due - started).total_seconds() / 3600)
                + " hours after its start where the procedure allows "
                + str(hours)
                + "."
            )
            left = (due - snapshot).total_seconds() / 3600
            assert abs(line["hours_remaining"] - left) < 0.051, (
                str((reference, line["milestone"]))
                + " has "
                + str(line["hours_remaining"])
                + " hours left, but from the snapshot "
                + config.SNAPSHOT_AT_UTC
                + " to "
                + str(line["due_at"])
                + " is "
                + str(round(left, 2))
                + ". Hours are counted from the snapshot, never from the clock on the wall, "
                "or the queue changes every time it is opened."
            )
            assert bool(line["overdue"]) == (left <= 0), (
                str((reference, line["milestone"]))
                + " is marked "
                + ("overdue" if line["overdue"] else "not overdue")
                + " although it falls due "
                + str(round(left, 2))
                + " hours after the snapshot. A deadline at or before the snapshot is overdue."
            )
            shown = line["due_at_hub_time"]
            local = (pd.to_datetime(shown, format=config.DISPLAY_TIMESTAMP_FORMAT,
                                    errors="coerce") if isinstance(shown, str) else pd.NaT)
            if pd.isna(local):
                local = pd.to_datetime(shown, errors="coerce")
                if not pd.isna(local) and local.tzinfo is not None:
                    local = local.tz_convert(zone).tz_localize(None)
            assert not pd.isna(local) and local == due.tz_convert(zone).tz_localize(None), (
                str((reference, line["milestone"]))
                + " is shown as due "
                + str(line["due_at_hub_time"])
                + " hub time, but "
                + str(line["due_at"])
                + " is "
                + due.tz_convert(zone).strftime(config.DISPLAY_TIMESTAMP_FORMAT)
                + " in "
                + zone
                + "."
            )
            overdue_seen = overdue_seen or bool(line["overdue"])
            running_seen = running_seen or not bool(line["overdue"])
    assert overdue_seen and running_seen, (
        "The incidents tried gave no deadline on one side of the snapshot or the other, so "
        "overdue and running deadlines were not both tried."
    )


def test_effort_is_weighed_against_the_earliest_deadline_less_the_filing_reserve(
        open_queue, invented_readings):
    import pandas as pd

    from config import config
    from tools.deadline_tools import compare_effort_with_deadline, compute_procedure_deadlines
    from tools.incident_data_tools import fetch_incident_profile

    assert open_queue["problem"] is None, open_queue["problem"]
    incidents = open_queue["incidents"]
    eu_reading = {config.PROCEDURE_EU_PERSONAL_DATA_BREACH:
                  invented_readings[config.PROCEDURE_EU_PERSONAL_DATA_BREACH]}
    snapshot = pd.to_datetime(config.SNAPSHOT_AT_UTC, utc=True)
    allowed = eu_reading[config.PROCEDURE_EU_PERSONAL_DATA_BREACH]["milestones"][0]
    deadlines = None
    for reference in incidents["incident_reference"]:
        profile = fetch_incident_profile(incidents, reference)
        if pd.isna(profile[allowed["clock_start_column"]]):
            continue
        true_left = (pd.to_datetime(profile[allowed["clock_start_column"]], utc=True)
                     + pd.Timedelta(hours=allowed["hours"]) - snapshot).total_seconds() / 3600
        if true_left > config.FILING_RESERVE_HOURS + 1 and float(true_left * 2).is_integer():
            deadlines = compute_procedure_deadlines(profile, eu_reading)
            break
    assert deadlines is not None and deadlines["earliest_milestone"] is not None, (
        "No live incident has a running deadline a whole or half hour more than an hour beyond "
        "the filing reserve under the readings given, so the comparison cannot be tried."
    )
    remaining = deadlines["earliest_milestone"]["hours_remaining"]
    effort = {"base_hours": 1.0, "multiplier_applied": False, "effort_needed_hours": 1.0,
              "containment_starts": "", "weekday_started": config.VALID_WEEKDAYS[0],
              "out_of_hours_start": config.BOOLEAN_NO, "planning_assumptions": []}

    fits = compare_effort_with_deadline(effort, deadlines)
    missing = sorted({"hours_remaining", "hours_available", "can_file_complete_in_time",
                      "deadline_message"} - set(fits))
    assert len(missing) == 0, (
        "Comparing the effort with the deadline returned no "
        + str(missing)
        + "."
    )
    assert abs(fits["hours_remaining"] - remaining) < 0.051, (
        "The comparison reports "
        + str(fits["hours_remaining"])
        + " hours remaining where the earliest deadline leaves "
        + str(remaining)
        + "."
    )
    available = fits["hours_available"]
    assert abs(available - (remaining - config.FILING_RESERVE_HOURS)) < 0.051, (
        "With "
        + str(remaining)
        + " hours to the earliest deadline, "
        + str(available)
        + " hours were counted as available. The filing itself takes "
        + str(config.FILING_RESERVE_HOURS)
        + " hours, which are not available for containment."
    )
    assert bool(fits["can_file_complete_in_time"]) is True, (
        "One hour of effort was judged not to fit into "
        + str(available)
        + " hours available."
    )
    exact = compare_effort_with_deadline(
        dict(effort, base_hours=available, effort_needed_hours=available), deadlines)
    assert bool(exact["can_file_complete_in_time"]) is True, (
        "Effort of exactly the hours available was judged not to fit. Fitting exactly is "
        "fitting: the comparison is effort at most the hours available."
    )
    over = compare_effort_with_deadline(dict(effort, effort_needed_hours=available + 0.25),
                                        deadlines)
    assert bool(over["can_file_complete_in_time"]) is False and over["deadline_message"], (
        "Effort a quarter of an hour beyond the hours available was judged to fit, or the "
        "shortfall carries no message. The desk has to be told to file an initial report."
    )
    no_clock = compute_procedure_deadlines(fetch_incident_profile(
        incidents, str(incidents["incident_reference"].iloc[0])), {})
    nothing = compare_effort_with_deadline(effort, no_clock)
    assert (pd.isna(nothing["hours_remaining"]) and pd.isna(nothing["hours_available"])
            and pd.isna(nothing["can_file_complete_in_time"])), (
        "With no deadline at all the comparison still gave "
        + str(nothing)
        + ". Without a running clock there is nothing to fit the effort into."
    )


def test_containment_is_planned_from_the_snapshot_in_the_hubs_own_time(open_queue,
                                                                       saved_models):
    import pandas as pd

    from config import config
    from tools.incident_data_tools import fetch_incident_profile
    from tools.prediction_tools import build_harm_facts, estimate_containment_effort

    assert open_queue["problem"] is None, open_queue["problem"]
    assert saved_models["problem"] is None, saved_models["problem"]
    incidents = open_queue["incidents"]
    snapshot = pd.to_datetime(config.SNAPSHOT_AT_UTC, utc=True)
    estimates = set()
    for hub in config.VALID_HUBS:
        reference = str(incidents[incidents["soc_hub"] == hub]["incident_reference"].iloc[0])
        profile = dict(fetch_incident_profile(incidents, reference))
        for sensitive in [False, True]:
            case = dict(profile, personal_data_involved_flag=config.BOOLEAN_YES)
            for column_name in config.SENSITIVE_DATA_FLAG_COLUMNS:
                case[column_name] = config.BOOLEAN_NO
            if sensitive:
                case[config.SENSITIVE_DATA_FLAG_COLUMNS[0]] = config.BOOLEAN_YES
            harm = build_harm_facts(saved_models["harm"], saved_models["harm_schema"],
                                    pd.DataFrame([case]))[0]
            plan = estimate_containment_effort(saved_models["effort"],
                                               saved_models["effort_schema"], case, harm,
                                               config.VALID_ATTACK_TYPES[0])
            missing = sorted({"base_hours", "multiplier_applied", "effort_needed_hours",
                              "containment_starts", "weekday_started", "out_of_hours_start",
                              "planning_assumptions"} - set(plan))
            assert len(missing) == 0, (
                "The containment plan for "
                + reference
                + " carries no "
                + str(missing)
                + "."
            )
            assert bool(plan["multiplier_applied"]) == sensitive, (
                reference
                + " with "
                + ("" if sensitive else "no ")
                + "sensitive data was "
                + ("" if plan["multiplier_applied"] else "not ")
                + "given the sensitive-data multiplier."
            )
            expected = (plan["base_hours"] * config.SENSITIVE_DATA_EFFORT_MULTIPLIER
                        if sensitive else plan["base_hours"])
            assert plan["base_hours"] > 0 and (
                    abs(plan["effort_needed_hours"] - expected) <= 0.02 * expected + 0.01), (
                reference
                + " needs "
                + str(plan["effort_needed_hours"])
                + " hours on a model estimate of "
                + str(plan["base_hours"])
                + ". The multiplier of "
                + str(config.SENSITIVE_DATA_EFFORT_MULTIPLIER)
                + " applies once, and only when sensitive data is involved."
            )
            zone = config.HUB_TIME_ZONE_BY_HUB[hub]
            local = snapshot.tz_convert(zone).tz_localize(None)
            shown = plan["containment_starts"]
            planned = (pd.to_datetime(shown, format=config.DISPLAY_TIMESTAMP_FORMAT,
                                      errors="coerce") if isinstance(shown, str) else pd.NaT)
            if pd.isna(planned):
                planned = pd.to_datetime(shown, errors="coerce")
                if not pd.isna(planned) and planned.tzinfo is not None:
                    planned = planned.tz_convert(zone).tz_localize(None)
            assert not pd.isna(planned) and planned == local, (
                reference
                + " plans containment from "
                + str(plan["containment_starts"])
                + " where the snapshot, in "
                + hub
                + "'s own time, is "
                + local.strftime(config.DISPLAY_TIMESTAMP_FORMAT)
                + ". Shift hours and weekends are local, so the start is too."
            )
            out_of_hours = (planned.hour < config.WORKING_HOURS_START_HOUR
                            or planned.hour >= config.WORKING_HOURS_END_HOUR
                            or config.VALID_WEEKDAYS[planned.weekday()] in config.WEEKEND_DAYS)
            assert (plan["weekday_started"] == config.VALID_WEEKDAYS[planned.weekday()]
                    and plan["out_of_hours_start"] == (config.BOOLEAN_YES if out_of_hours
                                                       else config.BOOLEAN_NO)), (
                reference
                + " starts on "
                + str(plan["weekday_started"])
                + " and is marked "
                + str(plan["out_of_hours_start"])
                + " for out of hours, which does not agree with its own start time "
                + str(plan["containment_starts"])
                + "."
            )
            assert sorted(plan["planning_assumptions"]) == sorted(
                    config.CONTAINMENT_PLANNING_ASSUMPTIONS), (
                reference
                + " lists its planning assumptions as "
                + str(plan["planning_assumptions"])
                + ". An estimate made before containment starts has to say which facts it "
                "had to assume."
            )
            estimates.add(round(plan["base_hours"], 2))
    assert len(estimates) >= 2, (
        "The "
        + str(len(config.VALID_HUBS))
        + " incidents tried, one from each hub, were all estimated at "
        + str(sorted(estimates))
        + " hours, so the estimate does not depend on the incident."
    )


def test_each_assessing_agent_was_called_once_and_in_order(saved_run):
    from config import config

    assert saved_run["problem"] is None, saved_run["problem"]
    assert saved_run["decision_problem"] is None, saved_run["decision_problem"]
    for name in ["calls_at_gate", "final_calls"]:
        listed = saved_run[name]
        assert listed["status"] == 200 and isinstance(listed["body"], dict) and {
                "calls", "call_count", "expected_call_count"} <= set(listed["body"]), (
            "Reading the run's model calls "
            + ("at the pause" if name == "calls_at_gate" else "once it finished")
            + " returned "
            + str(listed["status"])
            + " with "
            + str(listed["body"])[:300]
            + ", where the audit area lists every call with its count and the count expected."
        )
    at_gate = saved_run["calls_at_gate"]["body"]
    assessing = [config.AGENT_NAME_PLANNER, config.AGENT_NAME_HARM, config.AGENT_NAME_ATTACK,
                 config.AGENT_NAME_REPORTING, config.AGENT_NAME_WRITER]
    called = [call["agent_name"] for call in at_gate["calls"]]
    assert at_gate["call_count"] == len(at_gate["calls"]) == config.LLM_CALLS_BEFORE_DECISION, (
        "Reaching the Data Protection Officer took "
        + str(at_gate["call_count"])
        + " language model calls where the workflow allows "
        + str(config.LLM_CALLS_BEFORE_DECISION)
        + ", one per assessing agent. More means an agent ran twice; fewer, that one never ran."
    )
    assert called == assessing, (
        "The agents ran in the order "
        + str(called)
        + ". Each one reads what the one before it concluded: the attack is judged against "
        "the harm, the duties against both, and the write-up against all three."
    )
    assert at_gate["expected_call_count"] == config.LLM_CALLS_BEFORE_DECISION, (
        "Before any decision the service expected "
        + str(at_gate["expected_call_count"])
        + " calls. Until a decision is taken only the assessing agents' calls are expected."
    )

    final = saved_run["final_calls"]["body"]
    drafting = [call["agent_name"] for call in final["calls"]][len(assessing):]
    assert final["call_count"] == config.LLM_CALLS_BY_DECISION[saved_run["decision"]], (
        "A decision of "
        + saved_run["decision"]
        + " ended with "
        + str(final["call_count"])
        + " calls where the workflow allows "
        + str(config.LLM_CALLS_BY_DECISION[saved_run["decision"]])
        + "."
    )
    assert drafting == [config.AGENT_NAME_CUSTOMER_NOTICE, config.AGENT_NAME_REGULATOR_FILING], (
        "After the decision the agents called were "
        + str(drafting)
        + ". Telling customers and the authorities means the notice is written first and "
        "the filing second, so the filing can say that customers were told."
    )
    assert final["expected_call_count"] == final["call_count"], (
        "The service expected "
        + str(final["expected_call_count"])
        + " calls for a "
        + saved_run["decision"]
        + " and the run made "
        + str(final["call_count"])
        + ". The expected figure follows the decision taken."
    )


def test_every_model_call_is_recorded_with_what_it_cost(saved_run):
    from config import config

    assert saved_run["problem"] is None, saved_run["problem"]
    assert saved_run["decision_problem"] is None, saved_run["decision_problem"]
    listed = saved_run["final_calls"]
    assert listed["status"] == 200 and isinstance(listed["body"], dict) and {
            "calls", "total_latency_milliseconds"} <= set(listed["body"]), (
        "Reading the finished run's model calls returned "
        + str(listed["status"])
        + " with "
        + str(listed["body"])[:300]
        + ", where the audit area lists every call and their total latency."
    )
    final = saved_run["final_calls"]["body"]
    agents = {config.AGENT_NAME_PLANNER, config.AGENT_NAME_HARM, config.AGENT_NAME_ATTACK,
              config.AGENT_NAME_REPORTING, config.AGENT_NAME_WRITER,
              config.AGENT_NAME_CUSTOMER_NOTICE, config.AGENT_NAME_REGULATOR_FILING}
    assert len(final["calls"]) > 0, (
        "No language model call was recorded against the run at all, so nothing can say "
        "what the assessment cost or which model made it."
    )
    for call in final["calls"]:
        assert call["agent_name"] in agents, (
            "A call was recorded against "
            + str(call["agent_name"])
            + ", which is not one of the seven agents."
        )
        assert str(call["model_name"]).strip(), (
            "The call from "
            + call["agent_name"]
            + " does not say which model answered it, so an audit asking what assessed the "
            "incident has nothing to read."
        )
        assert call["prompt_characters"] > 0 and call["response_characters"] > 0, (
            "The call from "
            + call["agent_name"]
            + " records a prompt of "
            + str(call["prompt_characters"])
            + " and a reply of "
            + str(call["response_characters"])
            + " characters. A call that was made sent something and got something back."
        )
        assert call["latency_milliseconds"] > 0, (
            "The call from "
            + call["agent_name"]
            + " took "
            + str(call["latency_milliseconds"])
            + " milliseconds by its own record."
        )
    assert final["total_latency_milliseconds"] == sum(
            call["latency_milliseconds"] for call in final["calls"]), (
        "The run's total latency "
        + str(final["total_latency_milliseconds"])
        + " is not the sum of its calls."
    )
    assert saved_run["final"]["llm_call_count"] == len(final["calls"]), (
        "The run records "
        + str(saved_run["final"]["llm_call_count"])
        + " calls against the "
        + str(len(final["calls"]))
        + " logged for it. The run's own count is what the audit trail reads."
    )


def test_the_assessment_reaches_the_dpo_as_a_recommendation_they_can_act_on(saved_run):
    from config import config

    assert saved_run["problem"] is None, saved_run["problem"]
    at_gate = saved_run["at_gate"]
    assert at_gate["recommended_disposition"] in config.DECISION_OPTIONS, (
        "The write-up recommended "
        + repr(at_gate["recommended_disposition"])
        + " where the Data Protection Officer chooses between "
        + str(config.DECISION_OPTIONS)
        + ". A recommendation in other words cannot be matched against the decision taken."
    )
    assert at_gate["analyst_request"] == saved_run["analyst_request"], (
        "The record holds the analyst's question as "
        + repr(at_gate["analyst_request"])
        + " where the analyst asked "
        + repr(saved_run["analyst_request"])
        + ". The plan is only readable against what was actually asked."
    )
    plan = str(at_gate["assessment_plan_text"]).strip()
    assessment = str(at_gate["assessment_text"]).strip()
    assert len(plan) > 60, (
        "The assessment plan stored runs to "
        + str(len(plan))
        + " characters, so the planner's reply never reached the record."
    )
    assert len(assessment) > 150, (
        "The assessment stored for the Data Protection Officer runs to "
        + str(len(assessment))
        + " characters, which is not something anyone could decide from."
    )
    assert plan != assessment and assessment not in plan, (
        "The assessment stored is the plan over again, so the writer's reply was thrown "
        "away."
    )
    assert at_gate["attack_type"] in config.VALID_ATTACK_TYPES, (
        "The record names the attack as "
        + repr(at_gate["attack_type"])
        + ", which the desk does not code to."
    )


def test_a_reply_decorated_the_way_models_write_is_read_back_whole():
    from agentic.agents import parse_labelled_response
    from config import config

    labels = ["HEADLINE", "NEXT STEPS", "REASONING"]
    headline = "Start with the gateway that raised the first alert"
    first_step = "Read the gateway log for the hour before the alert."
    second_step = "List every account that signed in from outside the office."
    reasoning_start = "The gateway log rolls over at midnight."
    reasoning_end = "The account list is kept for one day only."
    reply = ("Sure - here is what you asked for.\n"
             "\n"
             "**HEADLINE:** " + headline + "\n"
             "## NEXT STEPS:\n"
             "1. " + first_step + "\n"
             "2. " + second_step + "\n"
             "\n"
             "- REASONING: " + reasoning_start + "\n"
             + reasoning_end)
    refusal = ""
    try:
        parsed = parse_labelled_response(reply, labels, "decoration_check")
    except ValueError as error:
        parsed, refusal = {}, str(error)
    assert refusal == "", (
        "A reply holding all three fields was refused: "
        + refusal
        + ". A model wraps its labels in markdown, headings and bullets, and a reader that "
        "cannot see past them stops every assessment at the first agent."
    )
    assert sorted(parsed) == sorted(labels), (
        "Reading the reply returned the fields "
        + str(sorted(parsed))
        + " where "
        + str(sorted(labels))
        + " were asked for."
    )
    for label in labels:
        value = str(parsed[label])
        assert value.strip() and value == value.strip(config.RESPONSE_DECORATION_CHARACTERS), (
            label
            + " was read back as "
            + repr(value)
            + ". The decoration a model puts around a label belongs to neither the label nor "
            "its value, and an empty value is no value."
        )
    assert headline in parsed["HEADLINE"] and "HEADLINE" not in parsed["HEADLINE"], (
        "HEADLINE was read back as "
        + repr(parsed["HEADLINE"])
        + " where the reply gives it as "
        + repr(headline)
        + "."
    )
    steps = parsed["NEXT STEPS"]
    assert (first_step in steps and second_step in steps and headline not in steps
            and reasoning_start not in steps), (
        "NEXT STEPS was read back as "
        + repr(steps)
        + ". A value that runs over several lines keeps every line until the next label, "
        "and nothing from any other field."
    )
    assert reasoning_start in parsed["REASONING"] and reasoning_end in parsed["REASONING"], (
        "REASONING was read back as "
        + repr(parsed["REASONING"])
        + ". A label behind a bullet is still a label, and its value runs on to the next "
        "line."
    )

    for incomplete in ["HEADLINE: One thing\nNEXT STEPS: Two things",
                       "HEADLINE: One thing\nNEXT STEPS:\nREASONING: Three things"]:
        refused = False
        try:
            parse_labelled_response(incomplete, labels, "decoration_check")
        except ValueError:
            refused = True
        assert refused, (
            "A reply missing a field, or leaving one empty, was accepted: "
            + repr(incomplete)
            + ". The next agent reads every field, so a reply without one has to be refused "
            "with a ValueError rather than passed on."
        )


def test_the_customer_notice_names_nothing_internal(saved_run, open_queue):
    import re

    from config import config

    assert saved_run["problem"] is None, saved_run["problem"]
    assert saved_run["decision_problem"] is None, saved_run["decision_problem"]
    assert open_queue["problem"] is None, open_queue["problem"]
    final = saved_run["final"]
    notice = str(final["customer_notice_text"] or "")
    filing = str(final["regulator_filing_text"] or "")
    assert len(notice.strip()) > 150, (
        "The customer notice stored runs to "
        + str(len(notice.strip()))
        + " characters, so the notice agent's reply never reached the record."
    )
    assert notice.strip() != filing.strip() and filing.strip() not in notice, (
        "The customer notice stored carries the regulator filing, which is confidential and "
        "never goes to customers."
    )

    reference = saved_run["reference"]
    incidents = open_queue["incidents"]
    notes = open_queue["notes"]
    row = incidents[incidents["incident_reference"] == reference].iloc[0]
    internal = {str(row[column]) for column in ["incident_id", "assigned_analyst_id",
                                                "ticket_queue_code", "analyst_shift_code"]}
    if row[config.CAMPAIGN_COLUMN] != config.NO_CAMPAIGN_VALUE:
        internal.add(str(row[config.CAMPAIGN_COLUMN]))
        internal |= set(incidents.loc[incidents[config.CAMPAIGN_COLUMN]
                                      == row[config.CAMPAIGN_COLUMN],
                                      "incident_reference"].astype(str))
    own_notes = notes[notes["incident_reference"] == reference]
    internal |= {str(value) for value in own_notes["analyst_id"]}
    for text in own_notes[config.NOTE_TEXT_COLUMN]:
        internal |= {token for token in re.findall(r"\b[A-Za-z]+(?:-[A-Za-z0-9]+)+\b", str(text))
                     if any(character.isdigit() for character in token)}
    internal.discard(reference)
    leaked = sorted(token for token in internal if token and token in notice)
    assert len(leaked) == 0, (
        "The customer notice names "
        + str(leaked)
        + ". A notice is public the moment it is sent, and it must never carry an internal "
        "identifier, a host name, an analyst, a campaign or another incident linked to it."
    )


def test_the_workflow_has_ten_reachable_nodes_and_sends_each_decision_down_its_own_path(tmp_path):
    from agentic.graph import build_workflow
    from agentic.state import IncidentAssessmentState
    from config import config

    compiled = build_workflow(str(tmp_path / "workflow_check.db"))
    node_names = sorted(str(name) for name in compiled.builder.nodes)
    expected_nodes = sorted(["load_incident_context", "plan_assessment", "assess_harm",
                             "identify_attack", "check_reporting_duties",
                             "compose_incident_assessment", "request_dpo_decision",
                             "draft_customer_notice", "draft_regulator_filing",
                             "record_incident_outcome"])
    assert node_names == expected_nodes, (
        "The workflow declares the nodes "
        + str(node_names)
        + " where the design has "
        + str(expected_nodes)
        + "."
    )

    branches = compiled.builder.branches.get("request_dpo_decision", {})
    assert len(branches) == 1, (
        "The decision node has "
        + str(len(branches))
        + " conditional branches where it has one, choosing the path from the decision."
    )
    branch = list(branches.values())[0]
    destinations = {}
    for decision in config.DECISION_OPTIONS:
        state = {key: None for key in IncidentAssessmentState.__annotations__}
        state["dpo_decision"] = {"decision": decision, "decided_by": "Check",
                                 "decided_by_role": config.ROLE_DPO,
                                 "decision_reason": "Routing is being checked."}
        routed = branch.path.invoke(state)
        if isinstance(routed, (list, tuple)) and len(routed) == 1:
            routed = routed[0]
        destinations[decision] = branch.ends[routed] if branch.ends else routed
    expected_paths = {config.DECISION_RECORD_ONLY: "record_incident_outcome",
                      config.DECISION_NOTIFY_REGULATOR: "draft_regulator_filing",
                      config.DECISION_NOTIFY_REGULATOR_AND_CUSTOMERS: "draft_customer_notice"}
    assert destinations == expected_paths, (
        "The decisions route to "
        + str(destinations)
        + ". Recording only writes nothing further, notifying the regulator writes the "
        "filing alone, and telling customers as well writes the notice and then the filing."
    )

    edges = {(str(source), str(target)) for source, target in compiled.builder.edges}
    edges |= {("request_dpo_decision", str(target)) for target in destinations.values()}
    reached = {"__start__"}
    grew = True
    while grew:
        grew = False
        for source, target in edges:
            if source in reached and target not in reached:
                reached.add(target)
                grew = True
    unreachable = sorted(set(node_names) - reached)
    assert len(unreachable) == 0, (
        "These nodes cannot be reached from the start: "
        + str(unreachable)
        + ". A node with no way in never runs, whatever it contains."
    )
    for source, target, reason in [
            ("draft_customer_notice", "draft_regulator_filing",
             "the filing records whether customers were told, so it is written after the notice"),
            ("draft_regulator_filing", "record_incident_outcome",
             "what was filed has to reach the record"),
            ("record_incident_outcome", "__end__", "the run ends once the outcome is recorded")]:
        assert (source, target) in edges, (
            "Nothing leads from " + source + " to " + target + ": " + reason + "."
        )


def test_the_run_stopped_for_the_dpo_before_anything_was_filed(saved_run):
    from config import config

    assert saved_run["problem"] is None, saved_run["problem"]
    at_gate = saved_run["at_gate"]
    assert at_gate["status"] == config.INCIDENT_STATUS_PENDING, (
        "When the five assessing agents finished, the incident stood at "
        + str(at_gate["status"])
        + " where it waits at "
        + config.INCIDENT_STATUS_PENDING
        + ". The Incident Response Plan gives the decision to the Data Protection Officer, "
        "so nothing is filed or sent until one decides."
    )
    pending = saved_run["pending_at_gate"]
    assert pending["status"] == 200 and isinstance(pending["body"], list), (
        "Listing the incidents pending a decision returned "
        + str(pending["status"])
        + " with "
        + str(pending["body"])[:300]
        + ", so the Data Protection Officer's queue cannot be read."
    )
    assert at_gate["assessment_id"] in [str(row.get("assessment_id")) for row in pending["body"]], (
        "The assessment waiting for a decision is missing from the list of incidents "
        "pending a decision, so the Data Protection Officer's queue would not show it."
    )
    nothing_yet = {field_name: at_gate[field_name] for field_name in [
        "decision", "decided_by", "customer_notice_text", "regulator_filing_text",
        "filing_submitted_at", "final_report_due_at"] if at_gate[field_name] is not None}
    assert len(nothing_yet) == 0, (
        "Before anyone decided, the record already holds "
        + str(nothing_yet)
        + ". Nothing may be decided, written to customers or filed while the run waits."
    )
    assert at_gate["llm_call_count"] == config.LLM_CALLS_BEFORE_DECISION, (
        "The run records "
        + str(at_gate["llm_call_count"])
        + " calls at the pause where the five assessing agents make "
        + str(config.LLM_CALLS_BEFORE_DECISION)
        + "."
    )
    assert saved_run["run_record"]["problem"] is None, saved_run["run_record"]["problem"]
    status_at_gate = saved_run["run_record"]["status_at_gate"]
    assert status_at_gate == config.AGENT_RUN_STATUS_AWAITING_DECISION, (
        "While it waited the run was recorded as "
        + str(status_at_gate)
        + " where it should read "
        + config.AGENT_RUN_STATUS_AWAITING_DECISION
        + ". A paused run that still reads as running tells nobody it is waiting for them."
    )


def test_resuming_finished_the_run_from_its_checkpoint_without_repeating_an_agent(saved_run):
    from agentic.graph import build_workflow
    from config import config

    assert saved_run["problem"] is None, saved_run["problem"]
    assert saved_run["decision_problem"] is None, saved_run["decision_problem"]
    assert saved_run["run_record"]["problem"] is None, saved_run["run_record"]["problem"]
    listed = {name: saved_run[name] for name in ["calls_at_gate", "final_calls"]}
    assert all(entry["status"] == 200 and isinstance(entry["body"], dict)
               and "calls" in entry["body"] for entry in listed.values()), (
        "Reading the run's model calls returned "
        + str({name: (entry["status"], str(entry["body"])[:150])
               for name, entry in listed.items()})
        + ", so what ran before and after the pause cannot be compared."
    )
    before = [call["agent_name"] for call in listed["calls_at_gate"]["body"]["calls"]]
    after = [call["agent_name"] for call in listed["final_calls"]["body"]["calls"]]
    assert len(after) == len(set(after)), (
        "The finished run called "
        + str(after)
        + ". An agent that appears twice ran again on resume, so the paused state was not "
        "restored and the assessment was paid for twice."
    )
    assert after[:len(before)] == before and len(after) == (
            len(before) + config.LLM_CALLS_BY_DECISION[saved_run["decision"]]
            - config.LLM_CALLS_BEFORE_DECISION), (
        "Resuming turned "
        + str(before)
        + " into "
        + str(after)
        + ". Resuming continues from the pause with the drafting agents the decision needs."
    )
    assert saved_run["run_record"]["status_final"] == config.AGENT_RUN_STATUS_COMPLETE, (
        "The run finished at "
        + str(saved_run["run_record"]["status_final"])
        + " rather than "
        + config.AGENT_RUN_STATUS_COMPLETE
        + ". A finished run that still reads as waiting stays in somebody's queue."
    )
    reopened = build_workflow(config.CHECKPOINT_DATABASE_FILE).get_state(
        {"configurable": {"thread_id": saved_run["run_record"]["thread_id"]}})
    assert reopened.values.get("assessment_id") == saved_run["at_gate"]["assessment_id"], (
        "A workflow built afresh on "
        + config.CHECKPOINT_DATABASE_FILE
        + " does not find the run's state under its thread, so a paused run would not "
        "survive the service being restarted overnight."
    )
    assert len(reopened.next) == 0 and (
            reopened.values["dpo_decision"]["decision"] == saved_run["decision"]), (
        "The checkpoint of the finished run still waits at "
        + str(reopened.next)
        + " or holds a different decision, so the run on disk is not the one that finished."
    )


def test_the_decision_filed_both_documents_and_set_the_final_report_date(saved_run,
                                                                         service_client,
                                                                         staff):
    import pandas as pd

    from config import config
    from tools.deadline_tools import compute_final_report_due

    assert saved_run["problem"] is None, saved_run["problem"]
    assert saved_run["decision_problem"] is None, saved_run["decision_problem"]
    assert staff["problem"] is None, staff["problem"]
    assert saved_run["detail"]["status"] == 200, (
        "The detail panel of "
        + saved_run["reference"]
        + " returned "
        + str(saved_run["detail"]["status"])
        + " with "
        + str(saved_run["detail"]["body"])[:300]
        + ", so the deadlines the decision was taken on cannot be read."
    )
    final = saved_run["final"]
    assert final["status"] == config.INCIDENT_STATUS_BY_DECISION[saved_run["decision"]], (
        "After a decision of "
        + saved_run["decision"]
        + " the incident stands at "
        + str(final["status"])
        + " where the configuration maps it to "
        + config.INCIDENT_STATUS_BY_DECISION[saved_run["decision"]]
        + "."
    )
    assert (final["decision"] == saved_run["decision"]
            and final["decided_by"] == saved_run["officer_name"]
            and final["decided_by_role"] == config.ROLE_DPO
            and final["decision_reason"] == saved_run["decision_reason"]
            and final["decided_at"] is not None), (
        "The decision is recorded as "
        + str({key: final[key] for key in ["decision", "decided_by", "decided_by_role",
                                           "decision_reason", "decided_at"]})
        + ". It has to name the decision, the person, their role, their reason as written, "
        "and when."
    )
    assert final["customer_notice_text"] and final["regulator_filing_text"], (
        "Telling the regulator and the customers stored "
        + ("a notice" if final["customer_notice_text"] else "no notice")
        + " and "
        + ("a filing" if final["regulator_filing_text"] else "no filing")
        + "."
    )
    assert (pd.to_datetime(final["filing_submitted_at"], utc=True)
            == pd.to_datetime(config.SNAPSHOT_AT_UTC, utc=True)), (
        "The filing is recorded as submitted at "
        + str(final["filing_submitted_at"])
        + ". The desk works at the snapshot "
        + config.SNAPSHOT_AT_UTC
        + ", and the final report is dated from the moment of filing."
    )
    deadlines = saved_run["detail"]["body"]["deadlines"]
    expected_due = compute_final_report_due(deadlines, final["filing_submitted_at"])
    assert expected_due is not None and final["final_report_due_at"] is not None and (
            pd.to_datetime(final["final_report_due_at"], utc=True)
            == pd.to_datetime(expected_due, utc=True)), (
        "The final report is recorded as due "
        + str(final["final_report_due_at"])
        + " where the procedures read for this incident put it at "
        + str(expected_due)
        + "."
    )
    months = min(filed["months"] for filed in deadlines["filed_milestones"])
    days = (pd.to_datetime(final["final_report_due_at"], utc=True)
            - pd.to_datetime(final["filing_submitted_at"], utc=True)).days
    assert 28 * months <= days <= 31 * months, (
        "The final report falls due "
        + str(days)
        + " days after the filing where the procedure allows "
        + str(months)
        + " calendar month(s)."
    )
    without_filed = dict(deadlines, filed_milestones=[])
    assert compute_final_report_due(without_filed, final["filing_submitted_at"]) is None, (
        "An incident whose procedures set no report after filing was still given a final "
        "report date."
    )
    again = service_client["client"].post(
        "/incidents/" + saved_run["at_gate"]["assessment_id"] + config.DECISION_PATH_ENDING,
        json={"decision": config.DECISION_RECORD_ONLY,
              "decision_reason": "A second decision on the same assessment."},
        headers=staff[config.ROLE_DPO]["headers"])
    assert again.status_code == 409, (
        "Deciding an assessment that was already decided returned "
        + str(again.status_code)
        + " where it is refused with 409. A second decision would file again or overwrite "
        "the first."
    )


def test_the_stored_assessment_agrees_with_the_tools_that_produced_it(saved_run):
    import pandas as pd

    from config import config

    assert saved_run["problem"] is None, saved_run["problem"]
    assert saved_run["detail"]["status"] == 200, (
        "The detail panel of "
        + saved_run["reference"]
        + " returned "
        + str(saved_run["detail"]["status"])
        + " with "
        + str(saved_run["detail"]["body"])[:300]
        + ", so the facts the tools work out cannot be compared with the record."
    )
    stored = saved_run["at_gate"]
    detail = saved_run["detail"]["body"]
    earliest = detail["deadlines"]["earliest_milestone"]
    comparisons = [
        ("harm_probability", detail["harm"]["harm_probability"]),
        ("harm_band", detail["harm"]["harm_band"]),
        ("attack_type", detail["attack"]["attack_type"]),
        ("attack_agreement", detail["attack"]["agreement"]),
        ("earliest_procedure", earliest["procedure_code"]),
        ("earliest_deadline_at", earliest["due_at"]),
        ("hours_remaining", detail["effort"]["hours_remaining"]),
        ("effort_needed_hours", detail["effort"]["effort_needed_hours"]),
        ("can_file_complete_in_time", detail["effort"]["can_file_complete_in_time"]),
        ("customer_notice_required", detail["duties"]["customer_notice_required"]),
    ]
    for field_name, worked_out in comparisons:
        if field_name == "earliest_deadline_at":
            agrees = (stored[field_name] is not None
                      and pd.to_datetime(stored[field_name], utc=True)
                      == pd.to_datetime(worked_out, utc=True))
        elif isinstance(worked_out, float) and stored[field_name] is not None:
            agrees = abs(float(stored[field_name]) - worked_out) < (
                0.051 if "hours" in field_name else 0.0051)
        else:
            agrees = stored[field_name] == worked_out
        assert agrees, (
            "The stored "
            + field_name
            + " is "
            + str(stored[field_name])
            + " where the tools, run again on the same incident, give "
            + str(worked_out)
            + ". The record has to hold the figures the decision was taken on."
        )
    stored_codes = sorted(code for code in config.PROCEDURE_OPTIONS
                          if code in str(stored["applicable_procedures"]))
    assert stored_codes == sorted(detail["applicability"]["applicable_procedures"]), (
        "The record lists "
        + str(stored_codes)
        + " as the procedures that apply, where the rules give "
        + str(sorted(detail["applicability"]["applicable_procedures"]))
        + "."
    )
    margin = (stored["hours_remaining"] - config.FILING_RESERVE_HOURS
              - stored["effort_needed_hours"])
    assert abs(margin) < 0.06 or bool(stored["can_file_complete_in_time"]) == (margin >= 0), (
        "The record says the filing "
        + ("can" if stored["can_file_complete_in_time"] else "cannot")
        + " be completed in time with "
        + str(stored["effort_needed_hours"])
        + " hours needed and "
        + str(stored["hours_remaining"])
        + " left before the "
        + str(config.FILING_RESERVE_HOURS)
        + "-hour reserve. The two do not agree."
    )


def test_signing_in_and_out_decides_who_the_service_will_serve(service_client):
    from access.password_security import hash_password
    from config import config
    from persistence.database import SessionFactory
    from persistence.models import UserAccount
    from persistence.repository import fetch_user_account

    assert service_client["problem"] is None, service_client["problem"]
    client = service_client["client"]
    analysts = [account for account in config.SEED_USER_ACCOUNTS
                if account["role"] == config.ROLE_ANALYST]
    account = analysts[-1]
    signed_in = client.post("/auth/signin", json={"username": account["username"],
                                                  "password": account["password"]})
    body = signed_in.json() if signed_in.status_code == 200 else {}
    assert ({"session_token", "role", "pages", "areas"} <= set(body)
            and str(body["session_token"]).strip()), (
        "Signing in as "
        + account["username"]
        + " with the seeded password returned "
        + str(signed_in.status_code)
        + " with "
        + signed_in.text[:200]
        + ", where a sign-in returns a session token with the role, pages and areas it opens."
    )
    assert (body["role"] == account["role"]
            and sorted(body["pages"]) == sorted(config.ROLE_PAGE_ACCESS[account["role"]])
            and sorted(body["areas"]) == sorted(config.ROLE_AREA_ACCESS[account["role"]])), (
        "Signing in as a "
        + account["role"]
        + " returned the role "
        + str(body["role"])
        + ", the pages "
        + str(body["pages"])
        + " and the areas "
        + str(body["areas"])
        + ", which are not what the configuration grants that role."
    )

    wrong = client.post("/auth/signin", json={"username": account["username"],
                                              "password": "wrong-" + account["password"]})
    stranger = client.post("/auth/signin", json={"username": "no-such-person",
                                                 "password": account["password"]})
    assert wrong.status_code == 401 and stranger.status_code == 401, (
        "A wrong password returned "
        + str(wrong.status_code)
        + " and an unknown username "
        + str(stranger.status_code)
        + ". Both are refused."
    )
    assert wrong.json() == stranger.json(), (
        "A wrong password is refused with "
        + repr(wrong.json())
        + " and an unknown username with "
        + repr(stranger.json())
        + ". Two different refusals tell a stranger which usernames exist."
    )

    token_headers = {config.SESSION_TOKEN_HEADER: body["session_token"]}
    parameters = {"harm_band": config.HARM_BAND_ALL}
    accepted = client.get("/queue", params=parameters, headers=token_headers)
    assert accepted.status_code == 200, (
        "The token just issued to "
        + account["username"]
        + " was not accepted by the queue. A fresh session token opens the areas its role "
        "is granted."
    )
    for headers in [None, {config.SESSION_TOKEN_HEADER: "not-a-token-anyone-was-given"}]:
        refused = client.get("/queue", params=parameters, headers=headers)
        assert refused.status_code == 401, (
            "The queue answered "
            + str(refused.status_code)
            + " to a request "
            + ("with no token" if headers is None else "with an invented token")
            + ". Only a signed-in user may read it."
        )
    signed_out = client.post("/auth/signout", headers=token_headers)
    after = client.get("/queue", params=parameters, headers=token_headers)
    assert signed_out.status_code == 200 and after.status_code == 401, (
        "After signing out, the old token got "
        + str(after.status_code)
        + " from the queue. Signing out ends the session."
    )

    with SessionFactory() as session:
        stored = fetch_user_account(session, UserAccount.username == account["username"])
        other = fetch_user_account(session, UserAccount.username == analysts[0]["username"])
    assert (stored["password_hash"] != account["password"]
            and stored["password_hash"] == hash_password(account["password"],
                                                         stored["password_salt"])), (
        "The password stored for "
        + account["username"]
        + " is not the salted hash of the password. A password kept as written is read by "
        "anyone who can open the database."
    )
    assert (stored["password_salt"] != other["password_salt"]
            and stored["password_hash"] != other["password_hash"]), (
        account["username"]
        + " and "
        + analysts[0]["username"]
        + " share a password and are stored with the same salt or the same hash, so one "
        "cracked hash opens both accounts."
    )


def test_every_role_reaches_exactly_the_areas_it_is_granted(service_client):
    from access.permissions import check_request_permission
    from config import config

    assert service_client["problem"] is None, service_client["problem"]
    client = service_client["client"]
    headers = {}
    for role_name in config.ROLE_AREA_ACCESS:
        account = [entry for entry in config.SEED_USER_ACCOUNTS if entry["role"] == role_name][1]
        reply = client.post("/auth/signin", json={"username": account["username"],
                                                  "password": account["password"]})
        assert reply.status_code == 200, (
            "Signing in as "
            + account["username"]
            + " returned "
            + str(reply.status_code)
            + ", so what a "
            + account["role"]
            + " may reach cannot be probed."
        )
        headers[account["role"]] = {config.SESSION_TOKEN_HEADER: reply.json()["session_token"]}
    assert set(headers) == set(config.ROLE_AREA_ACCESS), (
        "Only " + str(sorted(headers)) + " could be signed in, so not every role was probed."
    )

    probes = [
        (config.AREA_INTAKE, "GET", "/queue", {"harm_band": config.HARM_BAND_ALL}, None),
        (config.AREA_ASSESSMENT, "POST", "/assessments", None,
         {"incident_reference": "INC-" + config.HUB_CODE_BY_HUB[config.VALID_HUBS[0]]
          + "-9999999", "analyst_request": "Assess this one."}),
        (config.AREA_AUDIT, "GET", "/incidents",
         {"status_value": [config.INCIDENT_STATUS_PENDING]}, None),
        (config.AREA_AUDIT, "GET", "/audit/chat-turns", {"turn_limit": 1}, None),
        (config.AREA_DECISION, "POST",
         "/incidents/ASM-DOES-NOT-EXIST" + config.DECISION_PATH_ENDING, None,
         {"decision": config.DECISION_RECORD_ONLY,
          "decision_reason": "Nothing further is needed here."}),
        (config.AREA_CHAT, "GET", "/chat/turns", {"turn_limit": 1}, None),
    ]
    for role_name, role_headers in headers.items():
        for area_name, method, path, parameters, payload in probes:
            reply = client.request(method, path, params=parameters, json=payload,
                                   headers=role_headers)
            granted = area_name in config.ROLE_AREA_ACCESS[role_name]
            assert (reply.status_code == 403) != granted and reply.status_code != 401, (
                "A "
                + role_name
                + " calling "
                + method
                + " "
                + path
                + " got "
                + str(reply.status_code)
                + ". The "
                + area_name
                + " area is "
                + ("granted" if granted else "not granted")
                + " to that role, and the guard runs before the endpoint: a role without the "
                "area is refused with 403 whether or not the thing asked for exists."
            )
            permission = check_request_permission(role_name, path, method)
            assert permission["area"] == area_name and bool(permission["allowed"]) == granted, (
                "The permission check put "
                + method
                + " "
                + path
                + " in "
                + str(permission["area"])
                + " and "
                + ("allowed" if permission["allowed"] else "refused")
                + " it for a "
                + role_name
                + "."
            )


def test_the_queue_puts_the_nearest_running_deadline_first(service_client, staff, open_queue):
    from config import config

    assert staff["problem"] is None, staff["problem"]
    assert open_queue["problem"] is None, open_queue["problem"]
    client = service_client["client"]
    headers = staff[config.ROLE_ANALYST]["headers"]
    reply = client.get("/queue", params={"harm_band": config.HARM_BAND_ALL}, headers=headers)
    assert reply.status_code == 200 and isinstance(reply.json(), list), (
        "The queue returned "
        + str(reply.status_code)
        + " with "
        + reply.text[:200]
        + " to a signed-in analyst."
    )
    everything = reply.json()
    missing = sorted({"incident_reference", "earliest_milestone", "harm_probability",
                      "harm_band"} - set(everything[0] if everything else {}))
    assert len(missing) == 0, (
        "A queue row carries no "
        + str(missing)
        + ", so the queue cannot be ordered or filtered."
    )
    assert (sorted(row["incident_reference"] for row in everything)
            == sorted(open_queue["incidents"]["incident_reference"])), (
        "The queue holds "
        + str(len(everything))
        + " incidents where the live extract holds "
        + str(len(open_queue["incidents"]))
        + ". Every open incident is in the queue exactly once."
    )
    running = [row for row in everything if row["earliest_milestone"] is not None]
    waiting = [row for row in everything if row["earliest_milestone"] is None]
    assert everything == running + waiting, (
        "An incident with no running clock is listed ahead of one whose clock is running. "
        "A running deadline always outranks one that has not started."
    )
    hours = [row["earliest_milestone"]["hours_remaining"] for row in running]
    assert hours == sorted(hours), (
        "The running part of the queue is not ordered by the hours left to its earliest "
        "deadline: "
        + str(hours[:8])
        + ". The desk works the queue from the top."
    )
    harm = [row["harm_probability"] for row in waiting]
    assert harm == sorted(harm, reverse=True), (
        "Incidents with no running clock are not ordered by harm, highest first: "
        + str(harm[:8])
        + "."
    )
    assert len(running) > 0 and len(waiting) > 0, (
        "The queue holds only running or only waiting incidents, so its order cannot be "
        "tried on both."
    )

    for band in config.HARM_BAND_OPTIONS:
        banded = client.get("/queue", params={"harm_band": band}, headers=headers).json()
        assert banded == [row for row in everything if row["harm_band"] == band], (
            "Filtering the queue to "
            + band
            + " did not return exactly the "
            + band
            + " incidents of the full queue, in the same order."
        )

    missing = client.get(
        "/queue/INC-" + config.HUB_CODE_BY_HUB[config.VALID_HUBS[0]] + "-9999999",
        headers=headers)
    assert missing.status_code == 404, (
        "The detail of an incident that is not in the queue returned "
        + str(missing.status_code)
        + " rather than 404."
    )
    first = running[0]
    detail = client.get("/queue/" + first["incident_reference"], headers=headers).json()
    panel = detail["deadlines"]["earliest_milestone"] or {}
    shown = first["earliest_milestone"]
    assert all(panel.get(key) == shown[key] for key in shown), (
        "The detail of "
        + first["incident_reference"]
        + " gives its earliest deadline as "
        + str(detail["deadlines"]["earliest_milestone"])
        + " where the queue shows "
        + str(first["earliest_milestone"])
        + ". The panel and the queue work from the same facts."
    )


def test_a_procedure_question_is_answered_from_the_documents_and_remembered(chat_replies):
    import os

    from chat.conversation_memory import recall_conversation
    from config import config
    from persistence.database import SessionFactory

    assert chat_replies["problem"] is None, chat_replies["problem"]
    for name, meaning in [("procedure", "Asking the response assistant who decides on "
                                        "notification"),
                          ("turns", "Reading back the analyst's own chat turns")]:
        assert chat_replies[name]["status"] == 200, (
            meaning
            + " returned "
            + str(chat_replies[name]["status"])
            + " with "
            + str(chat_replies[name]["body"])[:300]
            + "."
        )
    reply = chat_replies["procedure"]["body"]
    missing = sorted({"question_type", "answer", "source_documents", "was_refused"}
                     - set(reply))
    assert len(missing) == 0, (
        "The assistant's reply carries no "
        + str(missing)
        + ", so what it answered and where from cannot be read."
    )
    assert reply["was_refused"] is False and reply["question_type"] in config.CHAT_ANSWERED_TYPES, (
        "Asking who decides on notification was answered as "
        + str(reply["question_type"])
        + (" and refused" if reply["was_refused"] else "")
        + ". The Incident Response Plan answers it, so a refusal means the search never "
        "reached it."
    )
    folder = {name for name in os.listdir(config.DOCS_DIRECTORY) if name.lower().endswith(".pdf")}
    cited = reply["source_documents"]
    assert len(cited) > 0 and set(cited) <= folder, (
        "The answer cites "
        + str(cited)
        + ". An answer that cannot name the documents it came from is an answer from "
        "general knowledge."
    )
    assert not set(cited) & set(config.CHAT_EXCLUDED_DOCUMENTS), (
        "The answer cites "
        + str(sorted(set(cited) & set(config.CHAT_EXCLUDED_DOCUMENTS)))
        + ", which the assistant must not read: it describes real past incidents."
    )
    assert len(reply["answer"].strip()) > 40 and reply["answer"] != config.CHAT_REFUSAL_MESSAGE, (
        "The answer given was "
        + repr(reply["answer"][:120])
        + ", which answers nothing."
    )

    turns = chat_replies["turns"]["body"]
    asked = [turn for turn in turns
             if turn["question_text"] == chat_replies["procedure_question"]]
    assert len(asked) > 0, (
        "The analyst's latest turns read back as "
        + str([turn["question_text"] for turn in turns])
        + ", which do not include the question just answered, so the audit trail and the "
        "chat page lose it."
    )
    latest = asked[0]
    assert latest["question_type"] == reply["question_type"] and latest["was_refused"] is False, (
        "The analyst's stored turn is "
        + str({key: latest[key] for key in ["question_text", "question_type", "was_refused"]})
        + ", which is not how the question was just answered."
    )
    assert latest["closest_distance"] <= config.CHAT_MAX_RELEVANCE_DISTANCE, (
        "An answered question is stored with its closest passage "
        + str(latest["closest_distance"])
        + " away, beyond the "
        + str(config.CHAT_MAX_RELEVANCE_DISTANCE)
        + " within which an answer counts as grounded."
    )
    assert all(name in latest["source_documents"] for name in cited), (
        "The stored turn cites "
        + repr(latest["source_documents"])
        + " where the answer cited "
        + str(cited)
        + ". The audit trail has to show where each answer came from."
    )

    follow_up = "And who must be told first?"
    with SessionFactory() as session:
        remembered = recall_conversation(session, chat_replies["analyst"], follow_up)
    assert chat_replies["procedure_question"] in remembered["history_text"], (
        "The conversation recalled for the analyst's next question does not include the "
        "question just asked, so a follow-up such as "
        + repr(follow_up)
        + " would be read with no idea what it follows."
    )
    assert (follow_up in remembered["search_text"]
            and chat_replies["procedure_question"] in remembered["search_text"]), (
        "The text searched for the follow-up is "
        + repr(remembered["search_text"][:200])
        + ". It has to carry the new question and the ones before it."
    )


def test_incident_status_is_refused_alike_until_the_customers_are_told(
        chat_replies, saved_run, open_queue):
    from chat.incident_status_answer import answer_incident_status
    from config import config
    from persistence.database import SessionFactory
    from persistence.models import SecurityIncident
    from persistence.repository import fetch_incident_records

    assert saved_run["problem"] is None, saved_run["problem"]
    assert saved_run["decision_problem"] is None, saved_run["decision_problem"]
    assert chat_replies["problem"] is None, chat_replies["problem"]
    assert open_queue["problem"] is None, open_queue["problem"]
    assert chat_replies["status"]["status"] == 200, (
        "A customer communications agent asking about "
        + saved_run["reference"]
        + " got "
        + str(chat_replies["status"]["status"])
        + " with "
        + str(chat_replies["status"]["body"])[:300]
        + "."
    )
    incidents = open_queue["incidents"]
    unknown = "INC-" + config.HUB_CODE_BY_HUB[config.VALID_HUBS[0]] + "-9999999"
    with SessionFactory() as session:
        untouched = next(reference for reference in incidents["incident_reference"]
                         if not fetch_incident_records(
                             session, SecurityIncident.incident_reference == reference))
        refused_unassessed = answer_incident_status(session, incidents,
                                                    config.ROLE_COMMUNICATIONS, untouched)
        refused_unknown = answer_incident_status(session, incidents,
                                                 config.ROLE_COMMUNICATIONS, unknown)
        staff_view = answer_incident_status(session, incidents, config.ROLE_ANALYST,
                                            saved_run["reference"])
        staff_unknown = answer_incident_status(session, incidents, config.ROLE_ANALYST, unknown)

    assert bool(refused_unassessed["was_refused"]) and not refused_unassessed["source_documents"], (
        "A customer communications agent asking about "
        + untouched
        + ", which nobody has told customers about, was answered: "
        + repr(refused_unassessed["answer"][:120])
        + "."
    )
    assert ([refused_unassessed["answer"], sorted(refused_unassessed["source_documents"]),
             bool(refused_unassessed["was_refused"])]
            == [refused_unknown["answer"], sorted(refused_unknown["source_documents"]),
                bool(refused_unknown["was_refused"])]), (
        "The refusal for an incident customers have not been told about reads "
        + repr(refused_unassessed)
        + " and for an incident that does not exist "
        + repr(refused_unknown)
        + ". A refusal that changes shape when there is nothing to refuse tells the asker "
        "which incidents are real."
    )
    assert (untouched not in refused_unassessed["answer"]
            and unknown not in refused_unknown["answer"]), (
        "The refusal repeats the reference back, which confirms it is one the desk knows."
    )

    disclosed = chat_replies["status"]["body"]
    notice = str(saved_run["final"]["customer_notice_text"] or "").strip()
    assert (disclosed["was_refused"] is False and len(notice) > 0
            and " ".join(notice.split()) in " ".join(str(disclosed["answer"]).split())), (
        "Once customers had been told about "
        + saved_run["reference"]
        + ", the agent asking about it got "
        + repr(disclosed["answer"][:160])
        + ". What was published to customers may be repeated to them word for word."
    )
    assert len(disclosed["source_documents"]) > 0, (
        "The answer from the published notice cites nothing, so the agent cannot say where "
        "it came from."
    )

    assert (not bool(staff_view["was_refused"])
            and saved_run["at_gate"]["assessment_id"] in staff_view["answer"]
            and saved_run["final"]["status"] in staff_view["answer"]), (
        "An analyst asking about "
        + saved_run["reference"]
        + " was told "
        + repr(staff_view["answer"][:200])
        + ", which does not name its latest assessment and where it stands."
    )
    assert (not bool(staff_unknown["was_refused"])
            and staff_unknown["answer"] != refused_unknown["answer"]), (
        "An analyst asking about an incident that is not in the queue was refused as if "
        "they were outside the desk. Staff are told the incident is not in the queue."
    )
