from __future__ import annotations

import json
from typing import Any

import redis.asyncio as aioredis
import structlog

logger = structlog.get_logger(__name__)


class RedisClient:
    """Async Redis client for caching and session management."""

    def __init__(self, host: str = "localhost", port: int = 6379) -> None:
        self._host = host
        self._port = port
        self._client: aioredis.Redis | None = None

    async def connect(self) -> None:
        """Open the Redis connection."""
        logger.info("redis.connecting", host=self._host, port=self._port)
        self._client = aioredis.Redis(
            host=self._host, port=self._port, decode_responses=True
        )
        await self._client.ping()
        logger.info("redis.connected")

    async def disconnect(self) -> None:
        """Close the Redis connection."""
        if self._client:
            await self._client.close()
            self._client = None
            logger.info("redis.disconnected")

    async def get(self, key: str) -> str | None:
        """Get a string value."""
        return await self._client.get(key)

    async def set(self, key: str, value: str, ttl: int | None = None) -> None:
        """Set a string value with optional TTL in seconds."""
        if ttl:
            await self._client.setex(key, ttl, value)
        else:
            await self._client.set(key, value)

    async def get_json(self, key: str) -> Any | None:
        """Get and deserialise a JSON value."""
        raw = await self._client.get(key)
        if raw is None:
            return None
        return json.loads(raw)

    async def set_json(
        self, key: str, value: Any, ttl: int | None = None
    ) -> None:
        """Serialise a value to JSON and store it."""
        raw = json.dumps(value, ensure_ascii=False)
        if ttl:
            await self._client.setex(key, ttl, raw)
        else:
            await self._client.set(key, raw)
