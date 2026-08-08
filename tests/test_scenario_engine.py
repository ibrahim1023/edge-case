from pathlib import Path

from edgecase.models import CandidateScenario, Priority, ProjectFingerprint, RepoAnalysis, Scope
from edgecase.services.scenario_engine import ScenarioEngine


def test_generate_candidates_for_api_service():
    analysis = RepoAnalysis(
        repo_path=Path("/tmp/fake"),
        project_type="api-service",
        frameworks=["fastapi"],
        behaviors=["api"],
        dependencies=["fastapi"],
        test_files=[],
    )
    fingerprint = ProjectFingerprint(
        project_type="api-service",
        frameworks=["fastapi"],
        testing_framework="pytest",
        dependencies=["fastapi"],
        behaviors=["api"],
        domain="api",
        architecture="fastapi-routes",
    )

    engine = ScenarioEngine()
    candidates = engine.generate_candidates(analysis, fingerprint, scope=Scope.WHOLE_PROJECT)

    assert len(candidates) > 0
    categories = {c.category for c in candidates}
    assert "invalid_input" in categories


def test_scope_filters_candidates():
    analysis = RepoAnalysis(
        repo_path=Path("/tmp/fake"),
        project_type="api-service",
        frameworks=["fastapi", "sqlalchemy"],
        behaviors=["api", "database"],
        dependencies=["fastapi", "sqlalchemy"],
        test_files=[],
    )
    fingerprint = ProjectFingerprint(
        project_type="api-service",
        frameworks=["fastapi", "sqlalchemy"],
        testing_framework="pytest",
        dependencies=["fastapi", "sqlalchemy"],
        behaviors=["api", "database"],
        domain="api",
        architecture="fastapi-routes + sqlalchemy-orm",
    )

    engine = ScenarioEngine()
    whole = engine.generate_candidates(analysis, fingerprint, scope=Scope.WHOLE_PROJECT)
    db = engine.generate_candidates(analysis, fingerprint, scope=Scope.DATABASE)

    assert len(whole) >= len(db)
    db_categories = {c.category for c in db}
    assert "database" in db_categories
    assert any("roll back" in c.scenario for c in db)


def test_validate_and_rank_scores_signals():
    analysis = RepoAnalysis(repo_path=Path("/tmp/fake"), project_type="api-service")
    fingerprint = ProjectFingerprint(
        project_type="api-service",
        maturity="mature",
        is_monorepo=True,
    )
    high = CandidateScenario(
        category="idempotency",
        area="Payments",
        scenario="Duplicate calls should be idempotent",
        priority=Priority.CRITICAL,
        why_it_matters="Avoid double charges",
        bug_regression_evidence=["double charge"],
        official_evidence=["Stripe docs"],
    )
    low = CandidateScenario(
        category="invalid_input",
        area="API",
        scenario="Invalid input should fail",
        priority=Priority.MEDIUM,
        why_it_matters="Input validation matters",
    )
    engine = ScenarioEngine()
    ranked = engine.validate_and_rank("https://github.com/o/r", analysis, fingerprint, [low, high])

    assert ranked[0].category == "idempotency"
    assert ranked[0].priority_score > ranked[1].priority_score
