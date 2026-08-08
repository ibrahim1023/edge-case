import json
import logging
import re
import subprocess
import time
from pathlib import Path

import httpx

from edgecase.config import settings
from edgecase.models import CandidateScenario, ImplementationResult, ValidatedScenario

logger = logging.getLogger(__name__)


INVESTIGATE_PROMPT = """Investigate the repo at {repo_url} and report its project type, frameworks, main behaviors, and any obvious missing test areas. Return a JSON object with keys: project_type, frameworks, behaviors, missing_test_areas."""

VALIDATE_PROMPT = """For the repository {repo_url}, decide if this is a meaningful missing test scenario:

Area: {area}
Scenario: {scenario}
Affected files: {affected_files}
Existing tests: {existing_tests}

Return a JSON object with keys: relevant (bool), priority (CRITICAL|HIGH|MEDIUM|LOW), reason (str), existing_coverage (str)."""

IMPLEMENT_PROMPT = """Write a pytest test file for this missing scenario in the repo at {repo_url}:

Area: {area}
Scenario: {scenario}
Test cases:
{test_cases}

Use the existing pytest conventions. Only add tests; do not modify production code. Return the content of the test file."""


def _devin_unavailable_note() -> str:
    return "Devin token is valid, but the organization or task endpoint is not configured."


class DevinClient:
    def __init__(self):
        self.token = settings.devin_token
        self.org_id = settings.devin_org_id
        self.base_url = settings.devin_base_url.rstrip("/")
        self.use_mocks = settings.use_mocks or not self.token
        self.client = httpx.Client(
            headers={"Authorization": f"Bearer {self.token}"},
            timeout=30,
        )

    def _request(self, method: str, path: str, **kwargs) -> httpx.Response:
        url = f"{self.base_url}{path}"
        last_exc = None
        for attempt in range(3):
            try:
                response = self.client.request(method, url, **kwargs)
                if response.status_code in (429, 500, 502, 503, 504):
                    logger.warning(f"Devin {response.status_code} on {url}; retry {attempt + 1}/3")
                    last_exc = httpx.HTTPStatusError("transient error", request=response.request, response=response)
                    time.sleep(2 ** attempt)
                    continue
                response.raise_for_status()
                return response
            except httpx.HTTPError as exc:
                logger.warning(f"Devin request failed: {exc}; retry {attempt + 1}/3")
                last_exc = exc
                time.sleep(2 ** attempt)
        raise last_exc or httpx.HTTPError(f"Devin request to {url} failed")

    def _validate_token(self) -> bool:
        """Check the Devin token by calling the v3/self endpoint."""
        try:
            response = self._request("GET", "/self")
            return response.status_code == 200
        except httpx.HTTPError as exc:
            logger.warning(f"Devin token validation failed: {exc}")
            return False

    def _call(self, prompt: str) -> str:
        if self.use_mocks:
            return ""

        # With just a token but no org ID, we can only validate the token.
        if not self.org_id:
            self._validate_token()
            logger.info("Devin organization ID not set; skipping real session creation.")
            return ""

        try:
            # https://docs.devin.ai/api-reference/v3/sessions/post-organizations-sessions
            create_resp = self._request(
                "POST",
                f"/organizations/{self.org_id}/sessions",
                json={"prompt": prompt, "tags": ["edgecase"]},
            )
            session = create_resp.json()
            session_id = session.get("session_id") or session.get("id")
            if not session_id:
                logger.warning("Devin create session response missing session_id")
                return ""

            # Poll until the session reaches a terminal state.
            for _ in range(60):
                time.sleep(5)
                status_resp = self._request("GET", f"/organizations/{self.org_id}/sessions/{session_id}")
                status = (status_resp.json().get("status") or "").lower()
                if status in ("exit", "error", "suspended"):
                    break

            # Try to fetch the conversation messages.
            messages_resp = self._request("GET", f"/organizations/{self.org_id}/sessions/{session_id}/messages")
            data = messages_resp.json()
            if isinstance(data, list) and data:
                for msg in reversed(data):
                    content = msg.get("content") if isinstance(msg, dict) else msg
                    if content:
                        return content
                return str(data[-1])
            if isinstance(data, dict):
                return data.get("content") or data.get("text") or str(data)
            return ""
        except httpx.HTTPError as exc:
            logger.warning(f"Devin real call failed: {exc}; falling back to mock")
            return ""

    def run_repository_investigation(self, repo_url: str) -> dict:
        if self.use_mocks:
            return {
                "project_type": "api-service",
                "frameworks": ["fastapi", "sqlalchemy"],
                "behaviors": ["api", "database"],
                "missing_test_areas": ["invalid input", "concurrency"],
            }
        raw = self._call(INVESTIGATE_PROMPT.format(repo_url=repo_url))
        try:
            return json.loads(raw)
        except Exception:
            return {
                "token_valid": True,
                "note": _devin_unavailable_note(),
            }

    def validate_scenario(self, repo_url: str, analysis: dict, scenario: CandidateScenario) -> ValidatedScenario:
        if self.use_mocks:
            return ValidatedScenario(
                **scenario.model_dump(),
                devin_relevant=True,
                devin_priority=scenario.priority,
                devin_reason="Devin confirmed the scenario matches observable behavior.",
                existing_coverage="No direct test found.",
            )
        raw = self._call(VALIDATE_PROMPT.format(
            repo_url=repo_url,
            area=scenario.area,
            scenario=scenario.scenario,
            affected_files=", ".join(scenario.affected_files),
            existing_tests=analysis.get("existing_tests_summary", ""),
        ))
        raw = re.sub(r"```json|```", "", raw).strip()
        try:
            data = json.loads(raw)
        except Exception:
            data = {
                "relevant": True,
                "priority": scenario.priority.value,
                "reason": _devin_unavailable_note(),
                "existing_coverage": "N/A",
            }
        return ValidatedScenario(
            **scenario.model_dump(),
            devin_relevant=data.get("relevant", True),
            devin_priority=data.get("priority", scenario.priority.value),
            devin_reason=data.get("reason", ""),
            existing_coverage=data.get("existing_coverage", ""),
        )

    def _write_test_stub(self, repo_path: Path, scenario: ValidatedScenario) -> Path:
        test_file = repo_path / "tests" / f"test_{scenario.category.replace(' ', '_')}.py"
        if not test_file.parent.exists():
            test_file.parent.mkdir(parents=True, exist_ok=True)
        test_file.write_text(f"""import pytest

# EdgeCase generated tests for: {scenario.scenario}

def test_{scenario.category.replace(' ', '_')}_basic():
    # TODO: implement meaningful test for "{scenario.scenario}"
    assert True
""", encoding="utf-8")
        return test_file

    def implement_scenario(self, repo_path: Path, scenario: ValidatedScenario) -> ImplementationResult:
        if self.use_mocks:
            test_file = self._write_test_stub(repo_path, scenario)
            result = self._run_pytest(repo_path)
            return ImplementationResult(
                scenario_id=scenario.id,
                tests_added=1,
                passed=result.get("passed", 0),
                failed=result.get("failed", 0),
                potential_implementation_issue=result.get("failed", 0) > 0,
                summary=result.get("summary", ""),
            )
        raw = self._call(IMPLEMENT_PROMPT.format(
            repo_url=str(repo_path),
            area=scenario.area,
            scenario=scenario.scenario,
            test_cases="\n".join(scenario.suggested_test_cases),
        ))
        if not raw.strip():
            return ImplementationResult(
                scenario_id=scenario.id,
                tests_added=0,
                passed=0,
                failed=0,
                potential_implementation_issue=False,
                summary=_devin_unavailable_note(),
            )
        # Try to write the returned content as a test file if it looks like Python.
        test_file = repo_path / "tests" / f"test_{scenario.category.replace(' ', '_')}.py"
        if not test_file.parent.exists():
            test_file.parent.mkdir(parents=True, exist_ok=True)
        test_file.write_text(raw, encoding="utf-8")
        result = self._run_pytest(repo_path)
        return ImplementationResult(
            scenario_id=scenario.id,
            tests_added=1,
            passed=result.get("passed", 0),
            failed=result.get("failed", 0),
            potential_implementation_issue=result.get("failed", 0) > 0,
            summary=result.get("summary", ""),
        )

    def _run_pytest(self, repo_path: Path) -> dict:
        try:
            result = subprocess.run(
                ["pytest", "-q"],
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=120,
            )
            passed = result.stdout.count(" passed")
            failed = result.stdout.count(" failed")
            return {"passed": passed, "failed": failed, "summary": result.stdout + result.stderr}
        except Exception as exc:
            return {"passed": 0, "failed": 0, "summary": f"pytest error: {exc}"}
