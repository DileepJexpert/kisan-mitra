from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.schemas import TTSRequest, TTSResponse

router = APIRouter()


@router.post("/tts/speak", response_model=TTSResponse)
async def text_to_speech(request: TTSRequest):
    """Convert text to speech using Sarvam AI or Bhashini."""
    return JSONResponse(
        status_code=501,
        content={"detail": "Text-to-speech endpoint not yet implemented"},
    )
