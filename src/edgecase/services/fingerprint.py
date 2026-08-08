from edgecase.models import ProjectFingerprint, RepoAnalysis


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
    )
