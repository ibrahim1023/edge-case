from uuid import UUID

from fastapi import APIRouter, HTTPException

from edgecase.state import store

router = APIRouter(prefix="/session", tags=["status"])


@router.get("/{id}/status", summary="Check analysis progress")
def status(id: UUID) -> dict:
    session = store.get(id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return {
        "status": session.analysis_status,
        "error": session.analysis_error,
        "findings_count": len(session.validated_scenarios),
        "repository": session.repository,
    }
