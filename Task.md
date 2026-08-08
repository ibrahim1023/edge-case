# EdgeCase Implementation Tasks

Legend: `[x]` = implemented, `[ ]` = not yet implemented.

---

## Phase 0 — Project Setup

- [x] Create `pyproject.toml` with FastAPI, Pydantic, Uvicorn, httpx, GitPython, pytest
- [x] Create `.env.example` for all API keys and config
- [x] Add `README.md` with setup and run instructions
- [x] Create `AGENTS.md` with project conventions
- [ ] Set up virtual environment in repo (optional)
- [x] Add `ruff` / `mypy` to `pyproject.toml` optional dependencies
- [x] Add CI workflow for linting and tests

---

## Phase 1 — Session State & Models

- [x] Define `Session`, `RepoAnalysis`, `ProjectFingerprint`, `CandidateScenario`, `ValidatedScenario`, `ImplementationResult` Pydantic models
- [x] Define `Scope`, `Depth`, `Priority` enums
- [x] Implement in-memory `SessionStore`
- [x] Create `config.py` with `pydantic-settings`
- [x] Persist sessions to disk or SQLite
- [x] Add session expiry / cleanup

---

## Phase 2 — Repository Ingestion & Analysis

- [x] Implement `github.py` to clone public repos with `GitPython`
- [x] Implement `repo_analyzer.py` to detect frameworks from dependency files
- [x] Scan `pyproject.toml`, `requirements.txt`, `setup.py`, `Pipfile`, `pytest.ini`
- [x] List source and test files
- [x] Count existing `def test_` functions
- [x] Build `RepoAnalysis` from cloned repo
- [x] Improve behavior detection with AST import analysis
- [x] Improve false positives (e.g. `token` in `pypa/packaging` flagged as auth)
- [x] Detect databases and external services more accurately

---

## Phase 3 — Project Fingerprint

- [x] Implement `fingerprint.py` to infer `project_type`
- [x] Map frameworks to architecture (`fastapi-routes`, `sqlalchemy-orm`, etc.)
- [x] Map behaviors to domain (`payments`, `webhooks`, etc.)
- [x] Add version / maturity signals to fingerprint
- [x] Normalize project type logic for monorepos

---

## Phase 4 — Context.dev Research

- [x] Create `context_dev.py` client abstraction
- [x] Add mock responses for guidance, similar projects, patterns, bugs
- [x] Integrate real Context.dev endpoint
- [x] Cache research per session
- [x] Fallback to mock with clear logging when API is unavailable

---

## Phase 5 — Scenario Engine

- [x] Generate candidate scenarios from project fingerprint
- [x] Map repo categories to scenario templates
- [x] Enrich scenarios with research evidence
- [x] Select and rank top 5 scenarios
- [x] Devin validation of relevance and priority
- [x] Use real Context.dev evidence for `why_it_matters`
- [ ] Improve priority scoring with more signals
- [x] Make scenario categories aware of user `scope` preference

---

## Phase 6 — Devin Client & Test Implementation

- [x] Create `devin_client.py` abstraction
- [x] Implement mock repository investigation
- [x] Implement mock scenario validation
- [x] Implement mock test implementation with stub file + pytest run
- [x] Integrate real Devin API for investigation
- [x] Integrate real Devin API for validation
- [x] Integrate real Devin API for test implementation
- [x] Parse Devin output into `ImplementationResult`
- [x] Improve generated tests to be scenario-specific

---

## Phase 7 — FastAPI Backend

- [x] Implement `POST /session`
- [x] Implement `POST /session/{id}/repository` with `owner/repo` normalization
- [x] Implement `POST /session/{id}/confirm`
- [x] Implement `POST /session/{id}/preferences` (scope, depth, implementation)
- [x] Implement `POST /session/{id}/analyze`
- [x] Implement `GET /session/{id}/findings`
- [x] Implement `POST /session/{id}/scenarios/{scenario_id}/implement`
- [x] Implement `POST /webhooks/elevenlabs` stub
- [x] Add async `BackgroundTasks` for long analysis
- [x] Add `GET /session/{id}/status` for polling analysis progress
- [x] Add `POST /session/{id}/explain` for spoken scenario summaries
- [x] Add OpenAPI descriptions and response models

---

## Phase 8 — Voice & UI

- [x] Create minimal `static/index.html` text UI
- [x] Serve static files from FastAPI
- [ ] Wire ElevenLabs Conversational AI widget
- [ ] Map ElevenLabs tool calls to backend endpoints
- [ ] Add transcript display for voice
- [ ] Implement voice confirmation of `owner/repo`
- [ ] Implement voice follow-up questions
- [ ] Implement voice explanation of findings
- [ ] Implement voice approval of scenario and Devin implementation

---

## Phase 9 — Testing & Verification

- [x] Add `tests/test_api.py` for session lifecycle
- [x] Run `pytest` successfully
- [x] Validate end-to-end flow against `pypa/packaging`
- [x] Add tests for `repo_analyzer.py`
- [x] Add tests for `scenario_engine.py`
- [ ] Add tests for `devin_client.py` and `context_dev.py`
- [ ] Add integration test for full analyze → findings → implement flow
- [ ] Add linting and type checking

---

## Phase 10 — Real API Integration & Polish

- [x] Obtain and configure real ElevenLabs, Context.dev, Devin API keys
- [x] Validate real Context.dev endpoints
- [x] Validate real Devin endpoints
- [x] Add proper error handling for external API failures
- [x] Add retries and timeouts for `httpx` clients
- [ ] Improve `README.md` and `AGENTS.md` with real API setup
- [ ] Record a demo video or screenshot
