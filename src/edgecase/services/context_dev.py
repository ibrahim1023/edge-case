from edgecase.config import settings
from edgecase.models import ContextResearch, ProjectFingerprint


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
        self.use_mocks = settings.use_mocks or not self.api_key

    def get_official_testing_guidance(self, fingerprint: ProjectFingerprint) -> list[dict]:
        if self.use_mocks:
            return _mock_guidance(fingerprint.frameworks)
        # TODO: call real Context.dev endpoint
        return _mock_guidance(fingerprint.frameworks)

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

    def research(self, fingerprint: ProjectFingerprint) -> ContextResearch:
        return ContextResearch(
            official_guidance=self.get_official_testing_guidance(fingerprint),
            similar_projects=self.find_similar_projects(fingerprint),
            test_patterns=self.extract_test_patterns(fingerprint),
            bugs_regressions=self.find_bugs_and_regressions(fingerprint),
        )
