from uuid import UUID

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from edgecase.models import Session
from edgecase.state import store

router = APIRouter(prefix="/session", tags=["repository"])


class RepositoryInput(BaseModel):
    repository: str


@router.post("/{id}/repository", response_model=Session, summary="Set repository in owner/repo format")
def set_repository(id: UUID, body: RepositoryInput) -> Session:
    session = store.get(id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    value = body.repository.strip().lower().replace(" slash ", "/").replace(" ", "")
    if "/" not in value:
        raise HTTPException(status_code=422, detail="Repository must be in owner/repo format")

    owner, repo = value.split("/", 1)
    session.repository = value
    session.repository_url = f"https://github.com/{owner}/{repo}"
    store.save(session)
    return session


@router.post("/{id}/confirm", response_model=Session)
def confirm_repository(id: UUID) -> Session:
    session = store.get(id)
    if not session or not session.repository:
        raise HTTPException(status_code=400, detail="No repository set")
    session.repository_confirmed = True
    store.save(session)
    return session
