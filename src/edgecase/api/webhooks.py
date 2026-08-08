from fastapi import APIRouter, Request

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post("/elevenlabs")
async def elevenlabs_webhook(request: Request) -> dict:
    payload = await request.json()
    # TODO: map tool calls to backend endpoints when using ElevenLabs Conversational AI
    return {"received": True, "payload": payload}
