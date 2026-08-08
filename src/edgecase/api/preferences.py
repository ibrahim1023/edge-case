from uuid import UUID

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from edgecase.models import Depth, Scope, Session
from edgecase.state import store

router = APIRouter(prefix="/session", tags=["preferences"])


class PreferencesInput(BaseModel):
    scope: Scope = Scope.WHOLE_PROJECT
    depth: Depth = Depth.HIGH_VALUE
    allow_devin_implementation: bool = True


@router.post("/{id}/preferences", response_model=Session)
def set_preferences(id: UUID, body: PreferencesInput) -> Session:
    session = store.get(id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    session.scope = body.scope
    session.depth = body.depth
    session.allow_devin_implementation = body.allow_devin_implementation
    store.save(session)
    return session
