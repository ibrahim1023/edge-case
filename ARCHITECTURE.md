# EdgeCase Architecture

## High-Level Components

```text
User (voice or web UI)
    |
    v
ElevenLabs Conversational AI  <--- text fallback via /static/index.html
    |
    v
FastAPI Backend (edgecase.main:app)
    |
    +---> GitHub (clone)              GitPython
    +---> Devin (analysis / tests)    DevinClient
    +---> Context.dev (research)      ContextDevClient
    +---> Session Store               in-memory dict
```

## Backend Layers

### 1. API Layer (`src/edgecase/api/`)

Each module is a `fastapi.APIRouter`:

| Module | Purpose |
|--------|---------|
| `session.py` | Create and retrieve sessions |
| `repository.py` | Accept `owner/repo`, normalize, confirm |
| `preferences.py` | Set scope, depth, implementation mode |
| `analyze.py` | Clone repo, analyze, generate findings |
| `findings.py` | Return the top validated scenarios |
| `implement.py` | Run Devin test implementation for a scenario |
| `webhooks.py` | Entry point for ElevenLabs tool calls |

### 2. Services Layer (`src/edgecase/services/`)

Business logic and external integrations:

| Module | Responsibility |
|--------|--------------|
| `github.py` | Clone public repos, list Python and test files |
| `repo_analyzer.py` | Parse dependency files, count tests, detect frameworks |
| `fingerprint.py` | Build a `ProjectFingerprint` from `RepoAnalysis` |
| `context_dev.py` | Research: guidance, similar projects, patterns, bugs |
| `devin_client.py` | Validate scenarios and implement pytest tests |
| `scenario_engine.py` | Generate and rank missing test scenarios |

### 3. State Layer (`src/edgecase/state.py`)

A simple in-memory `SessionStore` keyed by `UUID`. Sessions are created and mutated by the API routes. For a production deployment, replace this with Redis / SQLite / Postgres.

### 4. Models Layer (`src/edgecase/models.py`)

All Pydantic v2 models used across the system: `Session`, `RepoAnalysis`, `ProjectFingerprint`, `CandidateScenario`, `ValidatedScenario`, `ImplementationResult`.

## Data Flow

```text
1. POST /session
2. POST /session/{id}/repository       set + normalize owner/repo
3. POST /session/{id}/confirm          mark repo as confirmed
4. POST /session/{id}/preferences      scope, depth, implement flag
5. POST /session/{id}/analyze
      ├─ clone GitHub repo
      ├─ analyze_repo()                build RepoAnalysis
      ├─ build_fingerprint()           build ProjectFingerprint
      ├─ ContextDevClient.research()   get guidance / patterns / bugs
      ├─ generate_candidates()         build CandidateScenarios
      └─ validate_and_rank()           Devin validates, return top 5
6. GET /session/{id}/findings          return ValidatedScenario list
7. POST /session/{id}/scenarios/{id}/implement
      ├─ DevinClient.implement_scenario()
      └─ run pytest and capture result
```

## Configuration

`src/edgecase/config.py` uses `pydantic-settings` and reads from `.env`:

- `ELEVENLABS_API_KEY`; `ELEVENLABS_AGENT_ID` for the Conversational AI widget
- `CONTEXT_DEV_API_KEY`
- `DEVIN_TOKEN`
- `GITHUB_TOKEN` (optional; classic or fine-grained with public repo `read`)
- `USE_MOCKS=true` (default)
- `REPO_CLONE_DIR`

## Integration Abstractions

Each external integration is wrapped as a `*Client` class with a mock mode. When the API key is missing or `USE_MOCKS=true`, the client returns deterministic, realistic placeholder data. This lets the rest of the backend run without real credentials while keeping the real code paths clear.

## UI

`src/edgecase/static/index.html` is a minimal text UI. It calls the FastAPI endpoints directly and displays the workflow. ElevenLabs voice can be added later by configuring the Conversational AI agent to call the backend `webhooks` endpoint.
