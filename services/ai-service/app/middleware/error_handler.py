"""
Global error handling for the AI service.
Custom exceptions and FastAPI exception handlers.
"""

import time
import traceback

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import structlog

logger = structlog.get_logger(__name__)


# ── Custom Exceptions ───────────────────────────────────────────────────────

class AgentError(Exception):
    """Error during agent execution."""
    def __init__(self, message: str, agent: str = "unknown"):
        self.agent = agent
        super().__init__(message)


class LLMError(Exception):
    """Error communicating with LLM provider."""
    def __init__(self, message: str, provider: str = "unknown"):
        self.provider = provider
        super().__init__(message)


class ToolError(Exception):
    """Error executing an agent tool."""
    def __init__(self, message: str, tool: str = "unknown"):
        self.tool = tool
        super().__init__(message)


class OCRError(Exception):
    """Error during OCR processing."""
    pass


class PredictionError(Exception):
    """Error during price prediction."""
    pass


# ── Exception Handlers ──────────────────────────────────────────────────────

def register_error_handlers(app: FastAPI):
    """Register all exception handlers with the FastAPI app."""

    @app.exception_handler(AgentError)
    async def agent_error_handler(request: Request, exc: AgentError):
        logger.error("agent.error", agent=exc.agent, error=str(exc),
                      path=request.url.path)
        return JSONResponse(
            status_code=500,
            content={
                "error": "agent_error",
                "message": str(exc),
                "agent": exc.agent,
                "timestamp": time.time(),
            },
        )

    @app.exception_handler(LLMError)
    async def llm_error_handler(request: Request, exc: LLMError):
        logger.error("llm.error", provider=exc.provider, error=str(exc))
        return JSONResponse(
            status_code=503,
            content={
                "error": "llm_unavailable",
                "message": "AI model temporarily unavailable. Please try again.",
                "timestamp": time.time(),
            },
        )

    @app.exception_handler(OCRError)
    async def ocr_error_handler(request: Request, exc: OCRError):
        logger.error("ocr.error", error=str(exc))
        return JSONResponse(
            status_code=422,
            content={
                "error": "ocr_error",
                "message": "Could not process document. Please send a clearer photo.",
                "timestamp": time.time(),
            },
        )

    @app.exception_handler(PredictionError)
    async def prediction_error_handler(request: Request, exc: PredictionError):
        logger.error("prediction.error", error=str(exc))
        return JSONResponse(
            status_code=500,
            content={
                "error": "prediction_error",
                "message": "Price prediction temporarily unavailable.",
                "timestamp": time.time(),
            },
        )

    @app.exception_handler(Exception)
    async def general_error_handler(request: Request, exc: Exception):
        logger.error("unhandled.error", error=str(exc),
                      path=request.url.path,
                      traceback=traceback.format_exc()[:500])
        return JSONResponse(
            status_code=500,
            content={
                "error": "internal_error",
                "message": "An unexpected error occurred. Please try again.",
                "timestamp": time.time(),
            },
        )
