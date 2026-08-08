from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, HTTPException

from edgecase.config import settings
from edgecase.models import Session
from edgecase.services.fingerprint import build_fingerprint
from edgecase.services.github import clone_repo, list_source_files, list_test_files
from edgecase.services.repo_analyzer import analyze_repo
from edgecase.services.scenario_engine import ScenarioEngine
from edgecase.state import store

router = APIRouter(prefix="/session", tags=["analyze"])
engine = ScenarioEngine()


def _run_analysis(
    session_id: UUID,
    owner: str,
    repo: str,
    repository_url: str,
) -> None:
    session = store.get(session_id)
    if not session:
        return

    mode = "mock" if settings.use_mocks else "real"

    def set_detail(detail: str) -> None:
        session.status_detail = detail
        store.save(session)

    try:
        set_detail("Cloning repository")
        repo_path = clone_repo(owner, repo)

        set_detail("Listing source and test files")
        source_files = list_source_files(repo_path)
        test_files = list_test_files(repo_path)

        set_detail("Analyzing repository structure")
        analysis = analyze_repo(repo_path, source_files, test_files)

        set_detail("Building project fingerprint")
        fingerprint = build_fingerprint(analysis)

        set_detail(f"Calling Context.dev ({mode})")
        research = engine.context.research(fingerprint, session.repository_url or "")

        set_detail("Generating candidate scenarios")
        candidates = engine.generate_candidates(analysis, fingerprint, session.scope, research, session.repository_url or "")

        set_detail(f"Calling Devin ({mode})")
        validated = engine.validate_and_rank(repository_url, analysis, fingerprint, candidates)

        session.repo_analysis = analysis
        session.project_fingerprint = fingerprint
        session.context_research = research
        session.candidate_scenarios = candidates
        session.validated_scenarios = validated
        session.analysis_status = "completed"
        session.status_detail = "Completed"
    except Exception as exc:
        session.analysis_error = str(exc)
        session.analysis_status = "failed"
        session.status_detail = "Failed"
    store.save(session)


@router.post("/{id}/analyze", response_model=Session, summary="Start async repo analysis and scenario discovery")
def analyze(id: UUID, background_tasks: BackgroundTasks) -> Session:
    session = store.get(id)
    if not session or not session.repository_confirmed:
        raise HTTPException(status_code=400, detail="Repository not confirmed")

    owner, repo = session.repository.split("/", 1)
    session.analysis_status = "running"
    store.save(session)
    background_tasks.add_task(_run_analysis, session.id, owner, repo, session.repository_url or "")
    return session
