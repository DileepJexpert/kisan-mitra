from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.schemas import STTRequest, STTResponse

router = APIRouter()


@router.post("/stt/transcribe", response_model=STTResponse)
async def transcribe_audio(request: STTRequest):
    """Transcribe audio to text using Whisper or Bhashini."""
    return JSONResponse(
        status_code=501,
        content={"detail": "Speech-to-text endpoint not yet implemented"},
    )
