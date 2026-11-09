# BreachWatch AI — Incident Triage and Breach Reporting

BreachWatch AI helps a security operations desk triage open incidents and meet its breach-reporting deadlines. It:

- cleans five raw incident extracts
- trains three models: harm probability, containment effort and attack type
- indexes the company's procedure PDFs for search
- works out every running reporting clock
- runs a five-agent assessment that stops for the Data Protection Officer (DPO) before anything is filed
- serves all of this through a REST API and a Streamlit dashboard

The project must pass all 50 tests in `tests.py`. **Nobody edits `tests.py` or `config/config.py`.**

---

## 1. Team and feature branches

| Member | Role | Feature branch | Owns |
|---|---|---|---|
| **Harrish** | Team lead: reviews and merges every PR | `feature/agentic-api` | LangGraph agents, workflow graph, REST API |
| **Swarna** | Data engineer | `feature/data-pipeline` | Data cleaning, feature building, quality report, incident data tool, two dashboard pages |
| **Yash** | ML engineer | `feature/ml-models` | Harm, effort and attack models, prediction and deadline tools |
| **Ajay** | Knowledge and chat engineer | `feature/knowledge-base` | PDF extraction, vector index, procedure reading, retrieval tool, response chat |
| **Shubash** | Backend and UI engineer | `feature/persistence-access-ui` | Database, sign-in and permissions, dashboard client and pages |

### Files per member (complete list)

**Swarna — `feature/data-pipeline` (11 files)**
- `data_pipeline/dataset_loader.py`
- `data_pipeline/common_cleaning.py`
- `data_pipeline/feature_builder.py`
- `data_pipeline/incident_cleaning.py`
- `data_pipeline/effort_cleaning.py`
- `data_pipeline/incident_note_cleaning.py`
- `data_pipeline/quality_profiler.py`
- `run_data_pipeline.py`
- `tools/incident_data_tools.py`
- `dashboard/incident_queue.py`
- `dashboard/incident_detail.py`

**Yash — `feature/ml-models` (8 files)**
- `modeling/model_evaluation.py`
- `modeling/model_registry.py`
- `modeling/harm_model.py`
- `modeling/effort_model.py`
- `modeling/attack_model.py`
- `run_model_training.py`
- `tools/prediction_tools.py`
- `tools/deadline_tools.py`

**Ajay — `feature/knowledge-base` (9 files)**
- `knowledge/pdf_extraction.py`
- `knowledge/chunk_splitting.py`
- `knowledge/vector_index.py`
- `knowledge/procedure_reading.py`
- `run_knowledge_indexing.py`
- `tools/retrieval_tools.py`
- `chat/conversation_memory.py`
- `chat/incident_status_answer.py`
- `chat/response_assistant.py`

**Shubash — `feature/persistence-access-ui` (12 files)**
- `persistence/database.py`
- `persistence/models.py`
- `persistence/repository.py`
- `run_database_setup.py`
- `access/password_security.py`
- `access/permissions.py`
- `dashboard/api_client.py`
- `dashboard/audit_trail.py`
- `dashboard/decision_queue.py`
- `dashboard/response_chat.py`
- `run_dashboard.py`

**Harrish — `feature/agentic-api` (7 files, plus reviewing and merging)**
- `agentic/state.py`
- `agentic/agents.py`
- `agentic/nodes.py`
- `agentic/graph.py`
- `api/schemas.py`
- `api/routes.py`
- `run_api_service.py`

---

## 2. Git workflow

```
main      ← final release only (end of Day 5)
 └── develop      ← every feature PR merges here, every day
      ├── feature/agentic-api            (Harrish)
      ├── feature/data-pipeline          (Swarna)
      ├── feature/ml-models              (Yash)
      ├── feature/knowledge-base         (Ajay)
      └── feature/persistence-access-ui  (Shubash)
```

**One-time setup (each member):**
```bash
git checkout develop
git pull origin develop
git checkout -b feature/<your-branch>
git push -u origin feature/<your-branch>
```

**Every day:**
1. **Morning:** bring in what was merged last night.
   ```bash
   git checkout feature/<your-branch>
   git pull origin develop
   ```
2. **During the day:** build only that day's files (see Section 3), commit, then push.
   ```bash
   git add <today's files>
   git commit -m "Day N: <what was built>"
   git push origin feature/<your-branch>
   ```
3. **By 5 PM:** open a pull request from `feature/<your-branch>` to `develop`, titled `Day N - <name> - <files>`.
4. **By 7 PM:** Harrish reviews and merges every PR into `develop` in the **merge order** given for that day, because later modules import earlier ones. After merging, Harrish runs the day's checks on `develop`.

**PR rules:**
- No edits to `tests.py` or `config/config.py`. Harrish rejects any PR that touches them.
- Never commit `.env`, which holds the Gemini API key.
- Never commit generated folders: `processed/`, `output/`, `database/` and `__pycache__/`. Each stage regenerates them.
- Every PR description lists which tests now pass on the branch.

---

## 3. Five-day plan

### Day 1 — Foundations (modules with no internal dependencies)

| Member | Files to push |
|---|---|
| Swarna | `data_pipeline/dataset_loader.py`, `data_pipeline/common_cleaning.py`, `data_pipeline/feature_builder.py`, `data_pipeline/incident_cleaning.py` |
| Yash | `modeling/model_evaluation.py`, `modeling/model_registry.py` |
| Ajay | `knowledge/pdf_extraction.py`, `knowledge/chunk_splitting.py` |
| Shubash | `persistence/database.py`, `persistence/models.py` |
| Harrish | `agentic/state.py`, `api/schemas.py` |

**Merge order:** any order, since nothing here imports another member's file.
**Check on `develop`:** every file imports without errors.

### Day 2 — Data pipeline complete, models and index written

| Member | Files to push |
|---|---|
| Swarna | `data_pipeline/effort_cleaning.py`, `data_pipeline/incident_note_cleaning.py`, `data_pipeline/quality_profiler.py`, `run_data_pipeline.py` |
| Yash | `modeling/harm_model.py`, `modeling/effort_model.py`, `modeling/attack_model.py` (these use Swarna's `feature_builder.py` from Day 1) |
| Ajay | `knowledge/vector_index.py`, `knowledge/procedure_reading.py` |
| Shubash | `persistence/repository.py`, `run_database_setup.py` |
| Harrish | `agentic/agents.py` (Gemini client, `parse_labelled_response`, the seven prompts) |

**Merge order:** Swarna, then Yash, Ajay, Shubash and Harrish.
**Check on `develop`:**
```bash
python run_database_setup.py
python run_data_pipeline.py
python -m pytest tests.py -v -k "cleaning or cleans or spelling or text_become_numbers or quality_report"
```
**Expected:** the 6 data-cleaning tests pass. The cleaned row counts must be 29715, 8308, 28611, 5913 and 32405.

### Day 3 — Models trained, documents indexed, tools started

| Member | Files to push |
|---|---|
| Swarna | `tools/incident_data_tools.py` |
| Yash | `run_model_training.py`, `tools/prediction_tools.py` |
| Ajay | `run_knowledge_indexing.py`, `tools/retrieval_tools.py` |
| Shubash | `access/password_security.py`, `access/permissions.py`, `dashboard/api_client.py` |
| Harrish | Integration day: run every stage end to end on `develop`, fix import or path problems across branches, and review the model metrics |

**Merge order:** Swarna, then Yash, Ajay and Shubash.
**Check on `develop`:**
```bash
python run_data_pipeline.py
python run_model_training.py
python run_knowledge_indexing.py
python -m pytest tests.py -v
```
**Expected:**
- **Feature-engineering tests pass:** feature schemas, schema order, scoring rows with gaps, fitted columns.
- **Model tests pass:** harm AUC, effort R², attack macro F1, "score rises with …" and note cleaning.
- **Knowledge-base tests pass:** document text, passages, index, narrowed search and customer steps.

### Day 4 — Deadlines, agent workflow, chat memory, first dashboard pages

| Member | Files to push |
|---|---|
| Swarna | `dashboard/incident_queue.py` |
| Yash | `tools/deadline_tools.py` (uses `incident_data_tools` and `prediction_tools` from Day 3) |
| Ajay | `chat/conversation_memory.py`, `chat/incident_status_answer.py` |
| Shubash | `dashboard/audit_trail.py` (imports `badge` from Swarna's `incident_queue.py`) |
| Harrish | `agentic/nodes.py`, `agentic/graph.py` (the ten nodes, SQLite checkpointing, and the pause for the DPO) |

**Merge order:** Swarna, then Yash, Ajay, Shubash and Harrish. Harrish merges last because `nodes.py` imports all four tools.
**Check on `develop`:** the deadline, campaign, effort-against-deadline and containment-planning tests pass. So do the agent-workflow tests: ten nodes, one call per agent, the stop before filing, resume, and the customer notice. The agent tests need a valid `GEMINI_API_KEY` in `.env`.

### Day 5 — API, remaining dashboard pages, final run of all 50 tests

| Member | Files to push |
|---|---|
| Swarna | `dashboard/incident_detail.py` |
| Yash | Fix any failing model or deadline tests; re-check the metrics in `output/model_metrics.json` |
| Ajay | `chat/response_assistant.py` (uses Harrish's `agentic/agents.py` and his own `vector_index.py`) |
| Shubash | `dashboard/decision_queue.py`, `dashboard/response_chat.py`, `run_dashboard.py` |
| Harrish | `api/routes.py`, `run_api_service.py` |

**Merge order:** Ajay, then Swarna, Shubash and Harrish. Harrish merges last because `routes.py` imports chat, access, persistence and tools. Yash's fixes merge whenever they are ready.
**Final check on `develop`, from a clean clone:**
```bash
pip install -r requirements.txt
python run_database_setup.py
python run_data_pipeline.py
python run_model_training.py
python run_knowledge_indexing.py
python -m pytest tests.py -v          # expected: 50 passed
python run_api_service.py             # terminal 1
python -m streamlit run run_dashboard.py   # terminal 2
```
Once all 50 tests pass and every dashboard page loads, Harrish opens the release PR from `develop` to `main` and merges it.

---

## 4. Summary: who pushes what, each day

| Day | Harrish | Swarna | Yash | Ajay | Shubash |
|---|---|---|---|---|---|
| 1 | state, schemas | dataset_loader, common_cleaning, feature_builder, incident_cleaning | model_evaluation, model_registry | pdf_extraction, chunk_splitting | database, models |
| 2 | agents | effort_cleaning, incident_note_cleaning, quality_profiler, run_data_pipeline | harm_model, effort_model, attack_model | vector_index, procedure_reading | repository, run_database_setup |
| 3 | integration and review | incident_data_tools | run_model_training, prediction_tools | run_knowledge_indexing, retrieval_tools | password_security, permissions, api_client |
| 4 | nodes, graph | incident_queue | deadline_tools | conversation_memory, incident_status_answer | audit_trail |
| 5 | routes, run_api_service, release | incident_detail | fixes and metric checks | response_assistant | decision_queue, response_chat, run_dashboard |

## 5. Test milestones

| End of day | Tests expected to pass on `develop` |
|---|---|
| Day 1 | None yet; every module imports cleanly |
| Day 2 | The 6 data-cleaning tests, including the quality report |
| Day 3 | + feature-engineering, model and knowledge-base tests |
| Day 4 | + deadline, campaign, effort and agent-workflow tests |
| Day 5 | All 50: + sign-in, role access, queue order and response chat |
