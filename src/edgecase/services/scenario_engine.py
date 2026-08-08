from edgecase.models import (
    CandidateScenario,
    ContextResearch,
    Priority,
    ProjectFingerprint,
    RepoAnalysis,
    Scope,
    ValidatedScenario,
)
from edgecase.services.context_dev import ContextDevClient
from edgecase.services.devin_client import DevinClient


CATEGORY_MAP = {
    "api-service": ["invalid_input", "external_service_failure", "concurrent_requests", "boundary_conditions"],
    "cli-tool": ["invalid_input", "boundary_conditions"],
    "library": ["invalid_input", "boundary_conditions", "concurrent_requests"],
    "unknown": ["invalid_input", "boundary_conditions"],
}

SCENARIO_TEMPLATES = {
    "idempotency": {
        "category": "idempotency",
        "scenario": "Repeated {integration} calls should not cause duplicate side effects",
        "priority": Priority.CRITICAL,
        "test_cases": [
            "Same request sent twice sequentially",
            "Same request sent concurrently",
        ],
    },
    "duplicate_webhook": {
        "category": "idempotency",
        "scenario": "Duplicate {integration} webhook delivery should be handled safely",
        "priority": Priority.CRITICAL,
        "test_cases": [
            "Same webhook sent twice sequentially",
            "Same webhook sent concurrently",
        ],
    },
    "transaction_rollback": {
        "category": "database",
        "scenario": "Database transaction should roll back on external service failure",
        "priority": Priority.HIGH,
        "test_cases": [
            "Commit fails after external call",
            "Partial write is not persisted",
        ],
    },
    "provider_timeout": {
        "category": "external_service_failure",
        "scenario": "{integration} timeout should be handled gracefully",
        "priority": Priority.HIGH,
        "test_cases": [
            "Simulate slow response",
            "Simulate no response",
        ],
    },
    "expired_token": {
        "category": "authentication",
        "scenario": "Expired authentication token should be rejected",
        "priority": Priority.HIGH,
        "test_cases": [
            "Use token 1 second after expiry",
            "Refresh before expiry",
        ],
    },
    "invalid_input": {
        "category": "invalid_input",
        "scenario": "Invalid input should return a clear error",
        "priority": Priority.MEDIUM,
        "test_cases": [
            "Empty payload",
            "Missing required fields",
        ],
    },
    "concurrent_requests": {
        "category": "concurrency",
        "scenario": "Concurrent {integration} requests should not corrupt state",
        "priority": Priority.MEDIUM,
        "test_cases": [
            "Two simultaneous updates",
            "Two simultaneous reads",
        ],
    },
    "boundary_conditions": {
        "category": "boundary_conditions",
        "scenario": "Boundary values should be handled correctly",
        "priority": Priority.MEDIUM,
        "test_cases": [
            "Minimum allowed value",
            "Maximum allowed value",
        ],
    },
}


class ScenarioEngine:
    def __init__(self):
        self.context = ContextDevClient()
        self.devin = DevinClient()

    def _categories_for(self, fingerprint: ProjectFingerprint, scope: Scope) -> list[str]:
        base = CATEGORY_MAP.get(fingerprint.project_type or "unknown", []).copy()
        if "payment" in fingerprint.behaviors and "idempotency" not in base:
            base.append("idempotency")
        if "webhook" in fingerprint.behaviors and "duplicate_webhook" not in base:
            base.append("duplicate_webhook")
        if "database" in fingerprint.behaviors and "transaction_rollback" not in base:
            base.append("transaction_rollback")
        if any(i in fingerprint.integrations for i in ["stripe", "redis", "celery"]):
            base.append("provider_timeout")
        if "authentication" in fingerprint.behaviors:
            base.append("expired_token")

        scope_allowed = {
            Scope.WHOLE_PROJECT: set(base),
            Scope.MODULE: set(base),
            Scope.API: {"invalid_input", "external_service_failure", "concurrent_requests", "boundary_conditions", "idempotency", "duplicate_webhook", "provider_timeout"},
            Scope.DATABASE: {"transaction_rollback", "concurrent_requests", "boundary_conditions", "invalid_input"},
            Scope.AUTH: {"expired_token", "invalid_input", "boundary_conditions"},
            Scope.BACKGROUND_JOBS: {"provider_timeout", "concurrent_requests", "invalid_input", "boundary_conditions"},
        }
        allowed = scope_allowed.get(scope, set(base))
        return [c for c in base if c in allowed]

    def _template_for(self, category: str, fingerprint: ProjectFingerprint) -> dict:
        if category in ("idempotency", "duplicate_webhook") and "payment" in fingerprint.behaviors:
            return SCENARIO_TEMPLATES["duplicate_webhook"]
        if category == "idempotency" and "payment" not in fingerprint.behaviors:
            return SCENARIO_TEMPLATES["idempotency"]
        if category == "duplicate_webhook" and "payment" not in fingerprint.behaviors:
            return SCENARIO_TEMPLATES["duplicate_webhook"]
        return SCENARIO_TEMPLATES.get(category, SCENARIO_TEMPLATES["invalid_input"])

    def _build_candidate(
        self,
        category: str,
        fingerprint: ProjectFingerprint,
        analysis: RepoAnalysis,
        research: ContextResearch,
    ) -> CandidateScenario:
        template = self._template_for(category, fingerprint)
        integration = fingerprint.integrations[0] if fingerprint.integrations else "provider"
        area = fingerprint.behaviors[0].replace("-", " ").title() if fingerprint.behaviors else "Core logic"
        scenario_text = template["scenario"].format(integration=integration)

        official = [g["summary"] for g in research.official_guidance if any(f in g.get("source", "") for f in fingerprint.frameworks)]
        similar = [p["pattern"] for p in research.test_patterns]
        bugs = [b["bug"] for b in research.bugs_regressions]

        affected_files = [
            f for f in analysis.test_files[:5]
        ] or [
            f for f in analysis.entry_points
        ] or [
            str(analysis.repo_path / "src")
        ]

        why_parts = []
        if official:
            why_parts.append(f"{official[0]}")
        if similar:
            why_parts.append(f"Common pattern in similar projects: {similar[0]}.")
        if bugs:
            why_parts.append(f"Documented regression: {bugs[0]}.")
        why_it_matters = " ".join(why_parts) or f"{scenario_text} is a common source of bugs in {fingerprint.domain} projects."

        return CandidateScenario(
            category=template["category"],
            area=area,
            scenario=scenario_text,
            priority=template["priority"],
            why_it_matters=why_it_matters,
            repo_evidence=[f"Repo uses {integration}", f"Frameworks: {', '.join(fingerprint.frameworks)}"],
            official_evidence=official[:2] or [f"{f} testing best practices" for f in fingerprint.frameworks[:2]],
            similar_project_evidence=similar[:3],
            bug_regression_evidence=bugs,
            suggested_test_cases=template["test_cases"],
            affected_files=affected_files,
        )

    def generate_candidates(
        self,
        analysis: RepoAnalysis,
        fingerprint: ProjectFingerprint,
        scope: Scope = Scope.WHOLE_PROJECT,
        research: ContextResearch | None = None,
        repo_url: str = "",
    ) -> list[CandidateScenario]:
        research = research or self.context.research(fingerprint, repo_url)
        categories = self._categories_for(fingerprint, scope)
        candidates = [self._build_candidate(c, fingerprint, analysis, research) for c in categories]
        return candidates

    def validate_and_rank(
        self,
        repo_url: str,
        analysis: RepoAnalysis,
        candidates: list[CandidateScenario],
    ) -> list[ValidatedScenario]:
        validated = []
        for c in candidates:
            v = self.devin.validate_scenario(repo_url, analysis.model_dump(), c)
            if v.devin_relevant:
                validated.append(v)
        order = {Priority.CRITICAL: 0, Priority.HIGH: 1, Priority.MEDIUM: 2, Priority.LOW: 3}
        validated.sort(key=lambda x: (order.get(x.devin_priority, 9), x.scenario))
        return validated[:5]
