from pathlib import Path

from edgecase.models import ProjectFingerprint, RepoAnalysis

_MANIFEST_FILES = ("pyproject.toml", "setup.py", "setup.cfg")


def _architecture(analysis: RepoAnalysis) -> str:
    parts = []
    if "fastapi" in analysis.frameworks:
        parts.append("fastapi-routes")
    if "flask" in analysis.frameworks:
        parts.append("flask-blueprints")
    if "django" in analysis.frameworks:
        parts.append("django-apps")
    if "sqlalchemy" in analysis.frameworks:
        parts.append("sqlalchemy-orm")
    if "celery" in analysis.frameworks:
        parts.append("celery-workers")
    if not parts:
        return "plain-modules"
    return " + ".join(parts)


def _domain(analysis: RepoAnalysis) -> str:
    if "payment-processing" in analysis.behaviors:
        return "payments"
    if "webhook-processing" in analysis.behaviors:
        return "webhooks"
    if "authentication" in analysis.behaviors:
        return "authentication"
    if "database" in analysis.behaviors:
        return "data-management"
    if "cli" in analysis.behaviors:
        return "cli-tool"
    return "general-python"


def _maturity(analysis: RepoAnalysis) -> str:
    if analysis.test_function_count == 0:
        return "no-tests"
    density = analysis.test_function_count / max(analysis.source_file_count, 1)
    if analysis.test_function_count >= 50 or density >= 0.2:
        return "mature"
    if analysis.test_function_count >= 10:
        return "mid"
    return "early"


def _is_monorepo(repo_path: Path) -> bool:
    if not repo_path.exists() or not repo_path.is_dir():
        return False
    roots = set()
    if any((repo_path / m).exists() for m in _MANIFEST_FILES):
        roots.add(".")
    for sub in repo_path.iterdir():
        if sub.is_dir() and any((sub / m).exists() for m in _MANIFEST_FILES):
            roots.add(sub.name)
    return len(roots) > 1


def build_fingerprint(analysis: RepoAnalysis) -> ProjectFingerprint:
    return ProjectFingerprint(
        project_type=analysis.project_type,
        frameworks=analysis.frameworks,
        testing_framework=analysis.testing_framework,
        dependencies=analysis.dependencies,
        integrations=analysis.integrations,
        behaviors=analysis.behaviors,
        domain=_domain(analysis),
        architecture=_architecture(analysis),
        maturity=_maturity(analysis),
        is_monorepo=_is_monorepo(analysis.repo_path),
    )
