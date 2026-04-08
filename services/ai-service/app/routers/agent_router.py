from fastapi import APIRouter

from app.schemas import ChatRequest, ChatResponse
from app.agents.supervisor import process_message

router = APIRouter()


@router.post("/agent/chat", response_model=ChatResponse)
async def agent_chat(request: ChatRequest):
    """Main conversational agent endpoint."""
    result = await process_message(
        user_id=request.user_id,
        message=request.message,
        language=request.language,
        channel=request.channel,
        audio_base64=request.audio_base64,
    )
    return ChatResponse(
        reply_text=result.get("reply_text", ""),
        reply_audio_base64=result.get("reply_audio_base64"),
        agents_used=result.get("agents_used", []),
        actions_taken=result.get("actions_taken", []),
        follow_up_actions=result.get("follow_up_actions", []),
    )
