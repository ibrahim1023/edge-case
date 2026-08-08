from edgecase.services.github import list_source_files, list_test_files
from edgecase.services.repo_analyzer import analyze_repo


def test_repo_analyzer_detects_fastapi(tmp_path):
    (tmp_path / "pyproject.toml").write_text("[project]\ndependencies = [\"fastapi\"]\n")
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("from fastapi import FastAPI\napp = FastAPI()\n")

    source = list_source_files(tmp_path)
    tests = list_test_files(tmp_path)
    result = analyze_repo(tmp_path, source, tests)

    assert "fastapi" in result.frameworks
    assert "api" in result.behaviors
    assert result.project_type == "api-service"


def test_repo_analyzer_no_false_auth(tmp_path):
    (tmp_path / "pyproject.toml").write_text("[project]\ndependencies = [\"pytest\"]\n")
    (tmp_path / "packaging").mkdir()
    (tmp_path / "packaging" / "token.py").write_text("def token():\n    return 'abc'\n")

    source = list_source_files(tmp_path)
    tests = list_test_files(tmp_path)
    result = analyze_repo(tmp_path, source, tests)

    assert "authentication" not in result.behaviors
    assert result.project_type == "library"
