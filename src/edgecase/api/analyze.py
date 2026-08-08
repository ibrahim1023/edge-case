from uuid import UUID

from fastapi import APIRouter, HTTPException

from edgecase.models import Session
from edgecase.services.fingerprint import build_fingerprint
from edgecase.services.github import clone_repo, list_source_files, list_test_files
from edgecase.services.repo_analyzer import analyze_repo
from edgecase.services.scenario_engine import ScenarioEngine
from edgecase.state import store

router = APIRouter(prefix="/session", tags=["analyze"])
engine = ScenarioEngine()


@router.post("/{id}/analyze", response_model=Session)
def analyze(id: UUID) -> Session:
    session = store.get(id)
    if not session or not session.repository_confirmed:
        raise HTTPException(status_code=400, detail="Repository not confirmed")

    owner, repo = session.repository.split("/", 1)
    try:
        repo_path = clone_repo(owner, repo)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Could not clone repo: {exc}") from exc

    source_files = list_source_files(repo_path)
    test_files = list_test_files(repo_path)
    analysis = analyze_repo(repo_path, source_files, test_files)
    fingerprint = build_fingerprint(analysis)
    research = engine.context.research(fingerprint)
    candidates = engine.generate_candidates(analysis, fingerprint, session.scope, research)
    validated = engine.validate_and_rank(session.repository_url or "", analysis, candidates)

    session.repo_analysis = analysis
    session.project_fingerprint = fingerprint
    session.context_research = research
    session.candidate_scenarios = candidates
    session.validated_scenarios = validated
    store.save(session)
    return session
