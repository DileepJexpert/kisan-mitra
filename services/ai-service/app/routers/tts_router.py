"""
Text-to-Speech Router
Converts text to audio using Bhashini TTS (free Hindi).
"""

import base64

from fastapi import APIRouter, HTTPException
import structlog

from app.schemas import TTSRequest, TTSResponse
from app.models.tts_provider import get_tts_provider

logger = structlog.get_logger(__name__)

router = APIRouter()

# Maximum text length to prevent abuse
MAX_TEXT_LENGTH = 5000


@router.post("/tts/speak", response_model=TTSResponse)
async def text_to_speech(request: TTSRequest):
    """Convert text to speech using Bhashini TTS."""
    if not request.text or not request.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")

    if len(request.text) > MAX_TEXT_LENGTH:
        raise HTTPException(
            status_code=400,
            detail=f"Text too long (max {MAX_TEXT_LENGTH} characters)",
        )

    # Map voice names to gender
    voice = request.voice.lower()
    gender = "female"
    if "male" in voice and "female" not in voice:
        gender = "male"

    tts = get_tts_provider()

    try:
        audio_bytes = await tts.speak(
            text=request.text.strip(),
            language=request.language,
            voice=gender,
        )
    except Exception as e:
        logger.error("tts.speak_failed", error=str(e))
        raise HTTPException(status_code=503, detail="Text-to-speech service unavailable")

    if audio_bytes is None:
        raise HTTPException(
            status_code=503,
            detail="TTS provider returned no audio. Check Bhashini API key configuration.",
        )

    audio_b64 = base64.b64encode(audio_bytes).decode()

    # Estimate duration (rough: ~150 words/minute for Hindi)
    word_count = len(request.text.split())
    estimated_duration = word_count / 2.5  # ~150 wpm → ~2.5 words/sec

    return TTSResponse(
        audio_base64=audio_b64,
        duration_seconds=round(estimated_duration, 1),
    )
