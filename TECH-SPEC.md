# EdgeCase — Technical Specification

> Living document. Update `README.md` and this file after any major architecture or integration change.

---

## 01 — Problem

**Who:** Python teams shipping public libraries, APIs, CLI tools, and web services.

**Pain:** Existing tests often cover the happy path but miss the scenarios that cause real outages — duplicate webhooks, expired auth tokens, transaction rollbacks, provider timeouts, and invalid inputs. Code-coverage dashboards look green, yet the most important edge cases are untested.

**Why voice:** The user may be in an IDE, in a meeting, or reviewing a repo on a phone. Saying *“analyze ibrahim1023/ci-rootcause, whole project, highest value, implement approved”* is faster and more natural than filling forms. ElevenLabs turns the workflow into a hands-free conversation.

---

## 02 — Architecture

```text
User (voice or web UI)
    |
    v
ElevenLabs Conversational AI  <-- text fallback via /static/index.html
    |
    v
FastAPI Backend (edgecase.main:app)
    |
    +---> GitHub (clone)              GitPython
    +---> Devin (analysis / tests)    DevinClient
    +---> Context.dev (research)      ContextDevClient
    +---> Session Store               SQLite + in-memory cache
```

**Data flow:**

1. `POST /session` — create a session.
2. `POST /session/{id}/repository` — normalize and confirm `owner/repo`.
3. `POST /session/{id}/preferences` — set `scope`, `depth`, `allow_devin_implementation`.
4. `POST /session/{id}/analyze` — clone, build `RepoAnalysis` + `ProjectFingerprint`, fetch `ContextResearch`, generate and validate the top 5 `CandidateScenario` objects.
5. `GET /session/{id}/findings` — return `ValidatedScenario` list.
6. `POST /session/{id}/scenarios/{scenario_id}/implement` — write and run pytest tests via `DevinClient`.

**Key design choice:** every external client (`ContextDevClient`, `DevinClient`) runs in mock mode by default. This keeps the full flow working without real credentials.

---

## 03 — Tool Rationale

| Tool | Why it is used |
|------|----------------|
| **ElevenLabs** | Voice-first interaction. Its Conversational AI platform supports tool calling, so the agent can confirm the repo, set preferences, and trigger backend endpoints via natural speech. |
| **Context.dev** | Provides official testing guidance, similar projects, common test patterns, and real bugs/regressions. This evidence is what turns generic advice into a concrete, defensible list of missing scenarios. |
| **Devin** | Acts as the execution layer: it can investigate a repo, validate whether a scenario is actually relevant, and write/rerun pytest tests for an approved scenario. |

**Why not a single LLM?** Each tool has a distinct, high-quality dataset. Context.dev grounds the *what* in real patterns, Devin handles the *how*, and ElevenLabs delivers the *interface*.

---

## 04 — Feasibility (6-hour scope)

The project is scoped to be demoable in a single day by cutting scope aggressively:

- **Public repos only:** no auth, no private clone, no multi-repo support.
- **Lightweight analysis:** keyword matching + `ast` imports, not expensive static analysis.
- **Top 5 scenarios, one implementation:** the engine returns the five most important gaps and can implement exactly one per session.
- **Text UI first, voice second:** the FastAPI text UI proves the flow; the ElevenLabs widget is a pluggable add-on.
- **Single-writer SQLite:** session persistence is a local database, not a distributed store.

**Out of scope:** full coverage reports, security audits, automatic merges, multi-language support, and persistent production-grade backends.

---

## 05 — Extensibility (v2)

A production-ready v2 would layer on the existing FastAPI backend:

1. **Persistent, shared sessions** (Redis/Postgres) with TTL and re-engagement.
2. **Full ElevenLabs voice wiring** — Conversational AI widget, tool-call mapping, transcript display, voice approval.
3. **Module-level scope** — drill into a specific package or service instead of the whole repo.
4. **Feedback loop** — use the result of `pytest` runs to re-rank future scenarios.
5. **Security and performance scenarios** — rate limits, auth bypass, and load/timeout tests.
6. **Multi-language support** — extend the analyzer to JavaScript/TypeScript and Go repos.
7. **CI gate** — run generated tests in a sandbox and post the diff as a PR suggestion.
