from uuid import UUID

from fastapi import APIRouter, HTTPException

from edgecase.models import Session
from edgecase.state import store

router = APIRouter(prefix="/session", tags=["session"])


@router.post("", response_model=Session)
def create_session() -> Session:
    return store.create()


@router.get("/{id}", response_model=Session)
def get_session(id: UUID) -> Session:
    session = store.get(id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")  # noqa: F821
    return session
