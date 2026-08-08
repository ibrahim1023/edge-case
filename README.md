# EdgeCase

Voice-first AI agent that discovers the most important missing pytest scenarios in public Python GitHub repositories.

## What It Does

- Clones a public Python repo and builds a project fingerprint.
- Researches testing patterns from similar projects (Context.dev).
- Generates, validates, and ranks the top 5 missing test scenarios.
- Optionally implements pytest tests for an approved scenario (Devin).

## Quickstart

```bash
cd /Users/ibrahim/Documents/Work/EdgeCase
python -m venv .venv && source .venv/bin/activate
pip install -e .
cp .env.example .env          # optional: add real API keys
python -m uvicorn edgecase.main:app --reload
```

Open `http://localhost:8000/` for the text UI or `/docs` for the OpenAPI spec.

## API Flow

1. `POST /session`
2. `POST /session/{id}/repository` — `{"repository": "owner/repo"}`
3. `POST /session/{id}/confirm`
4. `POST /session/{id}/preferences` — scope, depth, implementation
5. `POST /session/{id}/analyze` — clone, analyze, generate top 5 scenarios
6. `GET /session/{id}/findings`
7. `POST /session/{id}/scenarios/{scenario_id}/implement`

## Project Docs

| File | Purpose |
|------|---------|
| `AGENTS.md` | Coding conventions and must-read checklist for agents |
| `ARCHITECTURE.md` | System components and data flow |
| `STRATEGY.md` | Implementation strategy and mock-first approach |
| `Task.md` | Phased task tracker with checkboxes |
| `Product Spec.md` | Original product requirements |

## Configuration

Key env vars in `.env`:

- `ELEVENLABS_API_KEY` — voice API; `ELEVENLABS_AGENT_ID` only for the Conversational AI widget
- `CONTEXT_DEV_API_KEY`
- `DEVIN_TOKEN` — Devin API token (often labeled "API key" in the Devin UI)
- `GITHUB_TOKEN` — optional; classic or fine-grained token with public repo `read` access
- `USE_MOCKS=true` — default; uses mocks when real keys are absent

## Testing

```bash
python -m pytest tests -q
```

## Status

FastAPI backend, repo analyzer, scenario engine, mock clients, text UI, and tests are implemented. Real Context.dev, Devin, and ElevenLabs integrations are stubbed and ready for API keys.
