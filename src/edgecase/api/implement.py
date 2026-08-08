from uuid import UUID

from fastapi import APIRouter, HTTPException

from edgecase.models import ImplementationResult
from edgecase.services.scenario_engine import ScenarioEngine
from edgecase.state import store

router = APIRouter(prefix="/session", tags=["implement"])
engine = ScenarioEngine()


@router.post("/{id}/scenarios/{scenario_id}/implement", response_model=ImplementationResult, summary="Implement and run tests for a scenario")
def implement(id: UUID, scenario_id: UUID) -> ImplementationResult:
    session = store.get(id)
    if not session or not session.repo_analysis:
        raise HTTPException(status_code=400, detail="No analysis available")

    scenario = next((s for s in session.validated_scenarios if s.id == scenario_id), None)
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")

    result = engine.devin.implement_scenario(session.repo_analysis.repo_path, scenario)
    session.selected_scenario = scenario
    session.implementation_result = result
    store.save(session)
    return result
