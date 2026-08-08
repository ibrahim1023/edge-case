import logging
from urllib.parse import urlencode

import httpx

from edgecase.config import settings
from edgecase.models import ContextResearch, ProjectFingerprint

logger = logging.getLogger(__name__)


def _mock_guidance(frameworks: list[str]) -> list[dict]:
    results = []
    for fw in frameworks:
        results.append({
            "source": f"{fw} docs",
            "title": f"Testing {fw}",
            "summary": f"Use fixtures and integration tests for {fw}.",
        })
    return results


def _mock_similar(fingerprint: ProjectFingerprint) -> list[dict]:
    return [{
        "source": "GitHub",
        "title": f"mature-{fingerprint.domain}-python",
        "summary": f"A popular {fingerprint.domain} project using {fingerprint.architecture}.",
    }]


def _mock_patterns(fingerprint: ProjectFingerprint) -> list[dict]:
    patterns = []
    if "webhook" in fingerprint.behaviors:
        patterns.append({"pattern": "duplicate webhook delivery", "frequency": 0.8})
        patterns.append({"pattern": "invalid webhook payload", "frequency": 0.6})
    if "database" in fingerprint.behaviors:
        patterns.append({"pattern": "transaction rollback", "frequency": 0.7})
        patterns.append({"pattern": "connection failure", "frequency": 0.5})
    if "payment" in fingerprint.behaviors:
        patterns.append({"pattern": "provider timeout", "frequency": 0.7})
        patterns.append({"pattern": "idempotency", "frequency": 0.9})
    if "authentication" in fingerprint.behaviors:
        patterns.append({"pattern": "expired token", "frequency": 0.7})
    if not patterns:
        patterns.append({"pattern": "invalid input", "frequency": 0.8})
        patterns.append({"pattern": "boundary conditions", "frequency": 0.6})
    return patterns


def _mock_bugs(fingerprint: ProjectFingerprint) -> list[dict]:
    if "webhook" in fingerprint.behaviors:
        return [{"bug": "Duplicate webhook caused double fulfillment", "fix": "Added idempotency"}]
    if "payment" in fingerprint.behaviors:
        return [{"bug": "Provider timeout left payment unrecorded", "fix": "Add retry and rollback"}]
    return [{"bug": "Missing validation caused runtime errors", "fix": "Add input checks"}]


class ContextDevClient:
    def __init__(self):
        self.api_key = settings.context_dev_api_key
        self.base_url = settings.context_dev_base_url.rstrip("/")
        self.use_mocks = settings.use_mocks or not self.api_key
        self.client = httpx.Client(
            headers={"Authorization": f"Bearer {self.api_key}"},
            timeout=30,
            follow_redirects=True,
        )
        self._research_cache: dict[str, ContextResearch] = {}

    def _request(self, method: str, path: str, **kwargs) -> httpx.Response:
        url = f"{self.base_url}{path}"
        last_exc = None
        for attempt in range(3):
            try:
                response = self.client.request(method, url, **kwargs)
                if response.status_code in (429, 500, 502, 503, 504):
                    logger.warning(f"Context.dev {response.status_code} on {url}; retry {attempt + 1}/3")
                    last_exc = httpx.HTTPStatusError("transient error", request=response.request, response=response)
                    continue
                response.raise_for_status()
                return response
            except httpx.HTTPError as exc:
                logger.warning(f"Context.dev request failed: {exc}; retry {attempt + 1}/3")
                last_exc = exc
        raise last_exc or httpx.HTTPError(f"Context.dev request to {url} failed")

    def _scrape(self, target_url: str) -> str:
        """Scrape a web page and return its main-content markdown."""
        params = urlencode({
            "url": target_url,
            "useMainContentOnly": "true",
            "tags": "edgecase",
        })
        try:
            response = self._request("GET", f"/web/scrape/markdown?{params}")
            data = response.json()
            return data.get("markdown") or data.get("content") or ""
        except httpx.HTTPError as exc:
            logger.warning(f"Context.dev scrape failed for {target_url}: {exc}")
            return ""

    def get_official_testing_guidance(self, fingerprint: ProjectFingerprint, repo_url: str = "") -> list[dict]:
        if self.use_mocks:
            return _mock_guidance(fingerprint.frameworks)

        results = []
        if repo_url:
            markdown = self._scrape(repo_url)
            if markdown:
                results.append({
                    "source": repo_url,
                    "title": "Repository overview",
                    "summary": markdown[:2000],
                })

        for fw in fingerprint.frameworks:
            # Lightweight fallback for framework docs if known; otherwise continues to mock
            results.append({
                "source": f"{fw} docs",
                "title": f"Testing {fw}",
                "summary": f"Use fixtures and integration tests for {fw}.",
            })

        return results

    def find_similar_projects(self, fingerprint: ProjectFingerprint) -> list[dict]:
        if self.use_mocks:
            return _mock_similar(fingerprint)
        return _mock_similar(fingerprint)

    def extract_test_patterns(self, fingerprint: ProjectFingerprint) -> list[dict]:
        if self.use_mocks:
            return _mock_patterns(fingerprint)
        return _mock_patterns(fingerprint)

    def find_bugs_and_regressions(self, fingerprint: ProjectFingerprint) -> list[dict]:
        if self.use_mocks:
            return _mock_bugs(fingerprint)
        return _mock_bugs(fingerprint)

    def _research_key(self, fingerprint: ProjectFingerprint, repo_url: str) -> str:
        if repo_url:
            return repo_url
        return f"{fingerprint.domain}:{','.join(fingerprint.frameworks)}:{','.join(fingerprint.behaviors)}"

    def research(self, fingerprint: ProjectFingerprint, repo_url: str = "") -> ContextResearch:
        key = self._research_key(fingerprint, repo_url)
        if key in self._research_cache:
            return self._research_cache[key]
        research = ContextResearch(
            official_guidance=self.get_official_testing_guidance(fingerprint, repo_url),
            similar_projects=self.find_similar_projects(fingerprint),
            test_patterns=self.extract_test_patterns(fingerprint),
            bugs_regressions=self.find_bugs_and_regressions(fingerprint),
        )
        self._research_cache[key] = research
        return research
