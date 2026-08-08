from uuid import UUID

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from edgecase.state import store

router = APIRouter(prefix="/session", tags=["explain"])


class ExplainInput(BaseModel):
    scenario_index: int = 0


@router.post("/{id}/explain")
def explain(id: UUID, body: ExplainInput) -> dict:
    session = store.get(id)
    if not session or not session.validated_scenarios:
        raise HTTPException(status_code=400, detail="No findings available")
    try:
        scenario = session.validated_scenarios[body.scenario_index]
    except IndexError:
        raise HTTPException(status_code=404, detail="Scenario index out of range")

    text = (
        f"{scenario.scenario}. "
        f"This is a {scenario.devin_priority.lower()} priority missing test "
        f"in the {scenario.area} area. {scenario.why_it_matters} "
        f"Suggested cases: {'; '.join(scenario.suggested_test_cases)}."
    )
    return {"explanation": text, "scenario_id": str(scenario.id)}
