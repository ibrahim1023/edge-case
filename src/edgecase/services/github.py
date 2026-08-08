import shutil
from pathlib import Path

import git

from edgecase.config import settings


CLONE_ROOT = settings.repo_clone_dir


def clone_repo(owner: str, repo: str) -> Path:
    CLONE_ROOT.mkdir(parents=True, exist_ok=True)
    target = CLONE_ROOT / f"{owner}__{repo}"
    if target.exists():
        shutil.rmtree(target)
    url = f"https://github.com/{owner}/{repo}.git"
    git.Repo.clone_from(url, target, depth=1)
    return target


def _is_python_file(path: Path) -> bool:
    return path.suffix == ".py" and not any(p.startswith(".") for p in path.parts)


def list_python_files(path: Path) -> list[Path]:
    return [p for p in path.rglob("*.py") if _is_python_file(p)]


def list_test_files(path: Path) -> list[Path]:
    return [
        p for p in list_python_files(path)
        if p.name.startswith("test_") or p.name.endswith("_test.py") or "tests" in p.parts
    ]


def list_source_files(path: Path) -> list[Path]:
    tests = set(list_test_files(path))
    return [p for p in list_python_files(path) if p not in tests]


def read_file(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")
