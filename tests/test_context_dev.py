from edgecase.models import ProjectFingerprint
from edgecase.services.context_dev import ContextDevClient


def test_research_caches_by_repo_url():
    client = ContextDevClient()
    client.use_mocks = True
    fingerprint = ProjectFingerprint(
        project_type="api-service",
        frameworks=["fastapi"],
        behaviors=["api"],
        domain="api",
    )
    first = client.research(fingerprint, repo_url="https://github.com/owner/repo")
    second = client.research(fingerprint, repo_url="https://github.com/owner/repo")
    assert first is second


def test_research_caches_by_fingerprint():
    client = ContextDevClient()
    client.use_mocks = True
    fingerprint = ProjectFingerprint(
        project_type="api-service",
        frameworks=["fastapi"],
        behaviors=["api"],
        domain="api",
    )
    first = client.research(fingerprint)
    second = client.research(fingerprint)
    assert first is second


def test_research_different_repo_returns_different():
    client = ContextDevClient()
    client.use_mocks = True
    fingerprint = ProjectFingerprint(
        project_type="api-service",
        frameworks=["fastapi"],
        behaviors=["api"],
        domain="api",
    )
    first = client.research(fingerprint, repo_url="https://github.com/a/repo")
    second = client.research(fingerprint, repo_url="https://github.com/b/repo")
    assert first is not second
