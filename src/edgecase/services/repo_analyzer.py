import ast
import tomllib
from pathlib import Path

from edgecase.models import RepoAnalysis

DEPENDENCY_FILES = [
    "pyproject.toml",
    "requirements.txt",
    "setup.py",
    "setup.cfg",
    "Pipfile",
]

FRAMEWORK_IMPORTS = {
    "fastapi": ["fastapi"],
    "flask": ["flask"],
    "django": ["django"],
    "sqlalchemy": ["sqlalchemy"],
    "pydantic": ["pydantic"],
    "celery": ["celery"],
    "redis": ["redis"],
    "stripe": ["stripe"],
    "pytest": ["pytest"],
    "httpx": ["httpx"],
    "requests": ["requests"],
    "click": ["click"],
    "typer": ["typer"],
    "boto3": ["boto3"],
    "jwt": ["jwt", "jose"],
    "oauth": ["oauthlib", "authlib"],
}

FRAMEWORK_KEYWORDS = {
    "fastapi": ["fastapi"],
    "flask": ["flask"],
    "django": ["django"],
    "sqlalchemy": ["sqlalchemy"],
    "pydantic": ["pydantic"],
    "celery": ["celery"],
    "redis": ["redis"],
    "stripe": ["stripe"],
    "pytest": ["pytest"],
    "httpx": ["httpx"],
    "requests": ["requests"],
    "click": ["click"],
    "typer": ["typer"],
    "boto3": ["boto3"],
}

INTEGRATION_KEYWORDS = [
    "stripe", "redis", "celery", "postgres", "sqlite", "mysql",
    "aws", "s3", "github", "slack", "twilio",
]

BEHAVIOR_KEYWORDS = {
    "payment-processing": ["payment", "stripe", "charge", "refund"],
    "webhook-processing": ["webhook", "hook"],
    "authentication": ["auth", "login", "jwt", "oauth"],
    "background-jobs": ["celery", "worker", "background", "queue", "job"],
    "database": ["sqlalchemy", "database", "postgres", "sqlite", "mysql"],
    "api": ["fastapi", "flask", "django", "api", "endpoint"],
    "cli": ["click", "typer", "argparse", "command"],
}

BEHAVIOR_FROM_FRAMEWORK = {
    "fastapi": "api",
    "flask": "api",
    "django": "api",
    "sqlalchemy": "database",
    "pydantic": "api",
    "celery": "background-jobs",
    "redis": "background-jobs",
    "stripe": "payment-processing",
    "click": "cli",
    "typer": "cli",
    "jwt": "authentication",
    "oauth": "authentication",
}


def _read_dependency_text(repo_path: Path) -> str:
    chunks = []
    for name in DEPENDENCY_FILES:
        file_path = repo_path / name
        if file_path.exists():
            chunks.append(file_path.read_text(encoding="utf-8", errors="ignore"))
    return "\n".join(chunks).lower()


def _parse_pyproject_deps(repo_path: Path) -> list[str]:
    pyproject = repo_path / "pyproject.toml"
    if not pyproject.exists():
        return []
    try:
        with pyproject.open("rb") as f:
            data = tomllib.load(f)
    except Exception:
        return []
    deps = []
    project = data.get("project") or {}
    deps.extend(project.get("dependencies", []))
    deps.extend(data.get("tool", {}).get("poetry", {}).get("dependencies", {}).keys())
    optional = project.get("optional-dependencies") or {}
    for group in optional.values():
        deps.extend(group)
    return deps


def _extract_imports(source_files: list[Path]) -> set[str]:
    imports = set()
    for path in source_files[:100]:
        try:
            tree = ast.parse(path.read_text(encoding="utf-8", errors="ignore"))
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name.split(".")[0].lower())
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module.split(".")[0].lower())
    return imports


def _detect_frameworks(deps: list[str], imports: set[str]) -> list[str]:
    found = []
    text = " ".join(deps).lower()
    for fw, keywords in FRAMEWORK_KEYWORDS.items():
        if any(kw in text for kw in keywords):
            found.append(fw)
    for fw, modules in FRAMEWORK_IMPORTS.items():
        if any(m in imports for m in modules) and fw not in found:
            found.append(fw)
    return found


def _detect_integrations(dependency_text: str, imports: set[str]) -> list[str]:
    found = set()
    text = dependency_text
    for kw in INTEGRATION_KEYWORDS:
        if kw in text or kw in imports:
            found.add(kw)
    return sorted(found)


def _detect_behaviors(frameworks: list[str], imports: set[str]) -> list[str]:
    found = set()
    for fw in frameworks:
        behavior = BEHAVIOR_FROM_FRAMEWORK.get(fw)
        if behavior:
            found.add(behavior)
    for behavior, keywords in BEHAVIOR_KEYWORDS.items():
        if any(kw in imports or kw in " ".join(frameworks) for kw in keywords):
            found.add(behavior)
    return sorted(found)


def _project_type(repo_path: Path, frameworks: list[str], source_files: list[Path]) -> str:
    if any(f in frameworks for f in ["fastapi", "flask", "django"]):
        return "api-service"
    if any(f in frameworks for f in ["click", "typer"]):
        return "cli-tool"
    if ((repo_path / "setup.py").exists() or (repo_path / "pyproject.toml").exists()) and not any(
        f in frameworks for f in ["fastapi", "flask", "django", "click", "typer"]
    ):
        return "library"
    return "unknown"


def _count_tests(test_files: list[Path]) -> tuple[int, str]:
    total = 0
    for tf in test_files:
        try:
            tree = ast.parse(tf.read_text(encoding="utf-8", errors="ignore"))
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
                total += 1
    return total, f"{len(test_files)} test files, {total} test functions"


def analyze_repo(repo_path: Path, source_files: list[Path], test_files: list[Path]) -> RepoAnalysis:
    deps = _parse_pyproject_deps(repo_path) or _read_dependency_text(repo_path).splitlines()
    imports = _extract_imports(source_files)
    frameworks = _detect_frameworks(deps, imports)
    dep_text = _read_dependency_text(repo_path)
    integrations = _detect_integrations(dep_text, imports)
    behaviors = _detect_behaviors(frameworks, imports)

    entry_points = [
        str(p.relative_to(repo_path)) for p in source_files
        if p.name in ("app.py", "main.py", "__main__.py", "cli.py")
    ]

    test_count, summary = _count_tests(test_files)

    return RepoAnalysis(
        repo_path=repo_path,
        project_type=_project_type(repo_path, frameworks, source_files),
        frameworks=frameworks,
        testing_framework="pytest" if test_files else None,
        dependencies=[d for d in deps if d.strip()],
        integrations=integrations,
        behaviors=behaviors,
        test_files=[str(p.relative_to(repo_path)) for p in test_files],
        entry_points=entry_points,
        existing_tests_summary=summary,
        source_file_count=len(source_files),
        test_function_count=test_count,
    )
