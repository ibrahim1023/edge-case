# EdgeCase — Agent Guide

This file captures the project conventions and practical details needed to work in this codebase.

## Before You Start Coding

If you are a coding agent, read these documents in this order **before** making any changes:

1. `README.md` — high-level overview and quickstart
2. `ARCHITECTURE.md` — system components and data flow
3. `STRATEGY.md` — implementation strategy and mock-first approach
4. `Task.md` — current task status and implementation phases
5. `Product Spec.md` — original product requirements
6. `AGENTS.md` — this file, for conventions

When asked to add or change a feature, always cross-reference `Task.md` for the phase and `ARCHITECTURE.md` for the intended design. Do not introduce new frameworks or restructure existing modules without checking these docs first.

## Project Overview

A voice-first (currently text/API) agent that clones a public Python GitHub repo, analyzes its architecture, generates the most important missing pytest scenarios, and can optionally generate pytest tests for one approved scenario.

## Tech Stack

- Python 3.12+
- FastAPI + Pydantic v2
- Uvicorn
- `httpx` for HTTP clients
- `GitPython` for cloning repos
- `pytest` for tests
- `pydantic-settings` for config

## Repository Layout

```text
EdgeCase/
├── src/edgecase/
│   ├── main.py              # FastAPI app
│   ├── config.py            # Environment / settings
│   ├── models.py            # Pydantic models
│   ├── state.py             # In-memory session store
│   ├── api/                 # FastAPI route modules
│   ├── services/            # Business logic
│   │   ├── github.py        # Clone / list repo files
│   │   ├── repo_analyzer.py # Detect frameworks, deps, tests
│   │   ├── fingerprint.py   # Build ProjectFingerprint
│   │   ├── context_dev.py   # Context.dev client (mock/real)
│   │   ├── devin_client.py  # Devin client (mock/real)
│   │   └── scenario_engine.py # Generate / rank scenarios
│   └── static/              # Web UI
└── tests/
```

## Environment Variables

Copy `.env.example` to `.env` and fill in:

- `ELEVENLABS_API_KEY` — for voice API calls
- `ELEVENLABS_AGENT_ID` — only needed for the Conversational AI widget
- `CONTEXT_DEV_API_KEY` — real Context.dev API
- `DEVIN_TOKEN` — real Devin API token (often labeled "API key" in the Devin UI)
- `GITHUB_TOKEN` — optional; classic or fine-grained token with public repo `read` access
- `USE_MOCKS` — `true` (default) uses mocked clients if keys are missing
- `REPO_CLONE_DIR` — where to clone repos; defaults to `/tmp/edgecase_repos`

## Common Commands

Install in editable mode:

```bash
pip install -e "/Users/ibrahim/Documents/Work/EdgeCase"
```

Run the server:

```bash
python -m uvicorn edgecase.main:app --reload
```

Run the test suite:

```bash
python -m pytest tests -q
```

## Design Conventions

- All request/response models live in `models.py`.
- All routes use dedicated `APIRouter` modules under `src/edgecase/api/`.
- All external integrations are wrapped as `*Client` classes under `src/edgecase/services/`.
- Mock clients are the default; flip `USE_MOCKS` to `false` and set keys to use real services.
- The in-memory `SessionStore` is the source of truth for now; replace with a persistent store only if needed.
- Keep the UI minimal; it is served as static HTML from `src/edgecase/static/index.html`.

## Adding a New Service

1. Create a module in `src/edgecase/services/`.
2. Add a client class that can run in mock mode or call a real API.
3. Import it in the relevant `api/` route and wire an endpoint.
4. Add a `TestClient` test in `tests/` if it has a route.

## Known Constraints

- Public Python GitHub repos only.
- Private repos are not supported.
- ElevenLabs voice is not yet fully integrated; the API endpoints and a text UI exist.
- Devin and Context.dev clients fall back to mocks unless keys are supplied.
