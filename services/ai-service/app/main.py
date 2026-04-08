from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

from app.config import get_settings
from app.db.postgres_client import PostgresClient
from app.db.redis_client import RedisClient
from app.db.chroma_client import ChromaClient
from app.schemas import HealthResponse

from app.middleware.error_handler import register_error_handlers
from app.routers import (
    agent_router,
    scheme_router,
    mandi_router,
    loan_router,
    dispute_router,
    dpr_router,
    stt_router,
    tts_router,
    ocr_router,
    predict_router,
)

logger = structlog.get_logger(__name__)

# ── Shared clients (populated during lifespan) ──────────────────────────────
postgres: PostgresClient | None = None
redis: RedisClient | None = None
chroma: ChromaClient | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown lifecycle hook."""
    global postgres, redis, chroma
    settings = get_settings()

    logger.info("ai_service.starting", env=settings.app_env)

    # --- Startup ---
    # PostgreSQL
    try:
        postgres = PostgresClient(dsn=settings.db_url)
        await postgres.connect()
    except Exception as exc:
        logger.error("postgres.startup_failed", error=str(exc))
        postgres = None

    # Redis
    try:
        redis = RedisClient(host=settings.redis_host, port=settings.redis_port)
        await redis.connect()
    except Exception as exc:
        logger.error("redis.startup_failed", error=str(exc))
        redis = None

    # ChromaDB
    try:
        chroma = ChromaClient(host=settings.chroma_host)
        chroma.connect()
    except Exception as exc:
        logger.error("chroma.startup_failed", error=str(exc))
        chroma = None

    logger.info("ai_service.started")

    yield  # ── Application runs ──

    # --- Shutdown ---
    logger.info("ai_service.shutting_down")
    if postgres:
        await postgres.disconnect()
    if redis:
        await redis.disconnect()
    logger.info("ai_service.stopped")


# ── FastAPI application ─────────────────────────────────────────────────────

app = FastAPI(
    title="KisanMitra AI Service",
    version="1.0.0",
    lifespan=lifespan,
)

# ── CORS (allow API-gateway origin) ─────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Error handlers ──────────────────────────────────────────────────────────

register_error_handlers(app)

# ── Prometheus metrics ───────────────────────────────────────────────────────

Instrumentator().instrument(app).expose(app)

# ── Routers ──────────────────────────────────────────────────────────────────

API_PREFIX = "/ai/v1"

app.include_router(agent_router.router,   prefix=API_PREFIX, tags=["Agent"])
app.include_router(scheme_router.router,  prefix=API_PREFIX, tags=["Schemes"])
app.include_router(mandi_router.router,   prefix=API_PREFIX, tags=["Mandi Prices"])
app.include_router(loan_router.router,    prefix=API_PREFIX, tags=["Loans"])
app.include_router(dispute_router.router, prefix=API_PREFIX, tags=["Disputes"])
app.include_router(dpr_router.router,     prefix=API_PREFIX, tags=["DPR"])
app.include_router(stt_router.router,     prefix=API_PREFIX, tags=["Speech-to-Text"])
app.include_router(tts_router.router,     prefix=API_PREFIX, tags=["Text-to-Speech"])
app.include_router(ocr_router.router,     prefix=API_PREFIX, tags=["OCR"])
app.include_router(predict_router.router, prefix=API_PREFIX, tags=["Predictions"])


# ── Health check ─────────────────────────────────────────────────────────────

@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Return the health status of the service and its dependencies."""
    checks: dict[str, str] = {}

    # Postgres
    try:
        if postgres:
            await postgres.fetch_one("SELECT 1")
            checks["postgres"] = "healthy"
        else:
            checks["postgres"] = "not_connected"
    except Exception as exc:
        checks["postgres"] = f"unhealthy: {exc}"

    # Redis
    try:
        if redis:
            await redis.set("health_ping", "pong", ttl=5)
            checks["redis"] = "healthy"
        else:
            checks["redis"] = "not_connected"
    except Exception as exc:
        checks["redis"] = f"unhealthy: {exc}"

    # ChromaDB
    try:
        if chroma:
            chroma.get_or_create_collection("health_check")
            checks["chroma"] = "healthy"
        else:
            checks["chroma"] = "not_connected"
    except Exception as exc:
        checks["chroma"] = f"unhealthy: {exc}"

    overall = "healthy" if all(v == "healthy" for v in checks.values()) else "degraded"
    return HealthResponse(status=overall, checks=checks)
