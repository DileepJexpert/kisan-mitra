from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.schemas import ChatRequest, ChatResponse

router = APIRouter()


@router.post("/agent/chat", response_model=ChatResponse)
async def agent_chat(request: ChatRequest):
    """Main conversational agent endpoint."""
    return JSONResponse(
        status_code=501,
        content={"detail": "Agent chat endpoint not yet implemented"},
    )
