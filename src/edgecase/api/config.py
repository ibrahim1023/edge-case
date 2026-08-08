from fastapi import APIRouter

from edgecase.config import settings

router = APIRouter(prefix="/config", tags=["config"])


@router.get("")
def get_config() -> dict:
    return {
        "elevenlabs_agent_id": settings.elevenlabs_agent_id,
        "use_mocks": settings.use_mocks,
    }
