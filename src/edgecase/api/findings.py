from uuid import UUID

from fastapi import APIRouter, HTTPException

from edgecase.models import Session, ValidatedScenario
from edgecase.state import store

router = APIRouter(prefix="/session", tags=["findings"])


@router.get("/{id}/findings", response_model=list[ValidatedScenario])
def findings(id: UUID) -> list[ValidatedScenario]:
    session = store.get(id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session.validated_scenarios
