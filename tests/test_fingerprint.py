from pathlib import Path
from uuid import uuid4

from edgecase.models import RepoAnalysis
from edgecase.services.fingerprint import build_fingerprint


def test_fingerprint_mature():
    analysis = RepoAnalysis(
        repo_path=Path(f"/tmp/{uuid4()}"),
        project_type="api-service",
        frameworks=["fastapi"],
        source_file_count=10,
        test_function_count=50,
    )
    fingerprint = build_fingerprint(analysis)
    assert fingerprint.maturity == "mature"
    assert fingerprint.architecture == "fastapi-routes"


def test_fingerprint_early():
    analysis = RepoAnalysis(
        repo_path=Path(f"/tmp/{uuid4()}"),
        project_type="library",
        frameworks=[],
        source_file_count=20,
        test_function_count=3,
    )
    fingerprint = build_fingerprint(analysis)
    assert fingerprint.maturity == "early"


def test_fingerprint_monorepo(tmp_path: Path):
    (tmp_path / "pyproject.toml").write_text("[project]\n")
    (tmp_path / "packages").mkdir()
    (tmp_path / "packages" / "pyproject.toml").write_text("[project]\n")
    analysis = RepoAnalysis(
        repo_path=tmp_path,
        project_type="library",
        source_file_count=10,
        test_function_count=0,
    )
    fingerprint = build_fingerprint(analysis)
    assert fingerprint.is_monorepo is True


def test_fingerprint_not_monorepo(tmp_path: Path):
    (tmp_path / "pyproject.toml").write_text("[project]\n")
    analysis = RepoAnalysis(
        repo_path=tmp_path,
        project_type="library",
        source_file_count=10,
        test_function_count=0,
    )
    fingerprint = build_fingerprint(analysis)
    assert fingerprint.is_monorepo is False
