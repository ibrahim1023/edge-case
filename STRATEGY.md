# EdgeCase Build Strategy

## Overall Approach

Build a mock-first, pluggable system. Every external client starts with a deterministic mock. Once the core flow works, swap in real API keys one at a time. This keeps the hackathon demo reliable and makes the codebase easy to iterate on after the event.

## 1. Mock-First Strategy

All external services have a `*Client` class that defaults to mock output when `USE_MOCKS=true` or the API key is missing:

- `ContextDevClient` returns curated patterns, guidance, and bug examples based on the `ProjectFingerprint`.
- `DevinClient` returns plausible validation results and a generated pytest stub.

This lets the backend run end-to-end without real credentials. To switch to real, set the key and `USE_MOCKS=false`.

## 2. Repository Analysis Strategy

1. **Clone** the repo to a temp dir with `GitPython`.
2. **Parse** dependency files (`pyproject.toml`, `requirements.txt`, `setup.py`, `Pipfile`) for framework and integration keywords.
3. **Count** existing test functions with `ast`.
4. **Build** a `RepoAnalysis` and `ProjectFingerprint` for downstream research.

The analyzer is intentionally lightweight. It uses keyword matching rather than heavy static analysis so it runs quickly on any public repo.

## 3. Scenario Generation Strategy

1. Map the `project_type` and `behaviors` to a set of candidate categories (e.g., `idempotency`, `transaction_rollback`, `invalid_input`).
2. Use `ContextResearch` to fill in `why_it_matters`, `suggested_test_cases`, and evidence fields.
3. Validate each candidate with `DevinClient` to filter false positives.
4. Sort by `devin_priority` and return the top 5.

This keeps the focus on *scenarios*, not one-off test functions.

## 4. Devin Integration Strategy

For the real Devin integration, each action is one prompt:

- **Investigate**: summarize architecture and current test gaps.
- **Validate**: decide whether a candidate scenario is relevant and assign a priority.
- **Implement**: write pytest tests and run them.

The mock client currently writes a stub test file and runs `pytest` locally. When the real API is available, the same prompts can be sent to Devin and the response parsed into the same result objects.

## 5. ElevenLabs Strategy

Use ElevenLabs **Conversational AI** with a set of tool-calling functions:

- `set_repository(owner, repo)`
- `confirm_repository()`
- `set_preferences(scope, depth, implement)`
- `start_analysis()`
- `get_findings()`
- `explain_scenario(index)`
- `implement_scenario(index)`

Each tool maps to a backend endpoint. The backend sends back short JSON summaries that ElevenLabs reads aloud. For now the system has a text UI, but the webhook endpoint is already stubbed.

## 6. 2.5-Hour Demo Strategy

If this is built during a short hackathon, prioritize a happy-path vertical slice:

1. FastAPI skeleton and session store.
2. Repo clone + fingerprint.
3. Mock `Context.dev` + `Devin`.
4. Top-5 scenario generation.
5. Text UI to trigger and display the flow.

After the slice works, add real voice and real APIs as stretch goals.

## 7. Testing Strategy

- Unit tests for `repo_analyzer.py` and `scenario_engine.py` with known repos.
- `TestClient` tests for the FastAPI routes.
- Integration test that clones a real small repo end-to-end.
- Run `pytest` in the cloned repo after Devin implementation.

## 8. Next Steps

1. Add real `Context.dev` endpoint URLs and response parsing.
2. Add real `Devin` API job creation and polling.
3. Wire the ElevenLabs widget and tool calls.
4. Improve scenario relevance and priority scoring.
5. Persist sessions to a real store.
