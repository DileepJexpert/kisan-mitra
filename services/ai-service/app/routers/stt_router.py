"""
Speech-to-Text Router
Handles audio transcription via Whisper (local) with Bhashini fallback.
Supports OGG (WhatsApp), WAV, MP3 formats.
"""

import base64
import io
import subprocess
import tempfile

from fastapi import APIRouter, HTTPException
import structlog

from app.schemas import STTRequest, STTResponse
from app.models.stt_provider import get_stt_router

logger = structlog.get_logger(__name__)

router = APIRouter()


def _convert_ogg_to_wav(audio_bytes: bytes) -> bytes:
    """Convert OGG/OPUS (WhatsApp format) to WAV using ffmpeg."""
    try:
        with tempfile.NamedTemporaryFile(suffix=".ogg", delete=True) as ogg_tmp, \
             tempfile.NamedTemporaryFile(suffix=".wav", delete=True) as wav_tmp:
            ogg_tmp.write(audio_bytes)
            ogg_tmp.flush()

            subprocess.run(
                ["ffmpeg", "-y", "-i", ogg_tmp.name,
                 "-ar", "16000", "-ac", "1", "-f", "wav", wav_tmp.name],
                capture_output=True, timeout=15, check=True,
            )

            wav_tmp.seek(0)
            return wav_tmp.read()
    except FileNotFoundError:
        logger.warning("stt.ffmpeg_not_found", msg="Trying raw audio")
        return audio_bytes
    except subprocess.CalledProcessError as e:
        logger.warning("stt.ffmpeg_failed", error=e.stderr.decode()[:200])
        return audio_bytes


def _detect_audio_format(audio_bytes: bytes) -> str:
    """Detect audio format from magic bytes."""
    if audio_bytes[:4] == b"OggS":
        return "ogg"
    if audio_bytes[:4] == b"RIFF":
        return "wav"
    if audio_bytes[:3] == b"ID3" or audio_bytes[:2] == b"\xff\xfb":
        return "mp3"
    if audio_bytes[:4] == b"fLaC":
        return "flac"
    return "unknown"


@router.post("/stt/transcribe", response_model=STTResponse)
async def transcribe_audio(request: STTRequest):
    """Transcribe audio to text using Whisper or Bhashini."""
    try:
        audio_bytes = base64.b64decode(request.audio_base64)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid base64 audio data")

    if len(audio_bytes) < 100:
        raise HTTPException(status_code=400, detail="Audio data too small")

    if len(audio_bytes) > 25 * 1024 * 1024:  # 25MB limit
        raise HTTPException(status_code=400, detail="Audio too large (max 25MB)")

    # Convert OGG/OPUS to WAV if needed (WhatsApp sends OGG)
    fmt = _detect_audio_format(audio_bytes)
    if fmt in ("ogg", "mp3", "unknown"):
        audio_bytes = _convert_ogg_to_wav(audio_bytes)

    stt = get_stt_router()
    try:
        result = await stt.transcribe(audio_bytes, language=request.language)
    except Exception as e:
        logger.error("stt.transcribe_failed", error=str(e))
        raise HTTPException(status_code=503, detail="Speech transcription service unavailable")

    if not result.get("text"):
        return STTResponse(
            text="",
            language_detected=result.get("language_detected"),
            confidence=0.0,
        )

    return STTResponse(
        text=result["text"],
        language_detected=result.get("language_detected"),
        confidence=result.get("confidence"),
    )


@router.post("/stt/transcribe-url")
async def transcribe_from_url(audio_url: str, language: str = "hi"):
    """Download audio from URL (Gupshup media) and transcribe."""
    import httpx

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(audio_url)
            resp.raise_for_status()
            audio_bytes = resp.content
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to download audio: {str(e)}")

    fmt = _detect_audio_format(audio_bytes)
    if fmt in ("ogg", "mp3", "unknown"):
        audio_bytes = _convert_ogg_to_wav(audio_bytes)

    stt = get_stt_router()
    result = await stt.transcribe(audio_bytes, language=language)

    return STTResponse(
        text=result.get("text", ""),
        language_detected=result.get("language_detected"),
        confidence=result.get("confidence"),
    )
