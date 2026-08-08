from fastapi import APIRouter

from edgecase.config import settings

router = APIRouter(prefix="/config", tags=["config"])


@router.get("")
def get_config() -> dict:
    return {
        "elevenlabs_agent_id": settings.elevenlabs_agent_id,
        "use_mocks": settings.use_mocks,
        "has_context_dev_key": bool(settings.context_dev_api_key),
        "has_devin_token": bool(settings.devin_token),
        "has_github_token": bool(settings.github_token),
    }
