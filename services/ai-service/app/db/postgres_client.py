from __future__ import annotations

import asyncpg
import structlog

logger = structlog.get_logger(__name__)


class PostgresClient:
    """Async PostgreSQL client backed by an asyncpg connection pool."""

    def __init__(self, dsn: str) -> None:
        self._dsn = dsn
        self._pool: asyncpg.Pool | None = None

    async def connect(self) -> None:
        """Create the connection pool."""
        logger.info("postgres.connecting", dsn=self._dsn.split("@")[-1])
        self._pool = await asyncpg.create_pool(dsn=self._dsn, min_size=2, max_size=10)
        logger.info("postgres.connected")

    async def disconnect(self) -> None:
        """Close the connection pool."""
        if self._pool:
            await self._pool.close()
            self._pool = None
            logger.info("postgres.disconnected")

    async def execute(self, query: str, *args) -> str:
        """Execute a query and return the status string."""
        async with self._pool.acquire() as conn:
            return await conn.execute(query, *args)

    async def fetch_one(self, query: str, *args) -> asyncpg.Record | None:
        """Fetch a single row."""
        async with self._pool.acquire() as conn:
            return await conn.fetchrow(query, *args)

    async def fetch_all(self, query: str, *args) -> list[asyncpg.Record]:
        """Fetch all matching rows."""
        async with self._pool.acquire() as conn:
            return await conn.fetch(query, *args)
