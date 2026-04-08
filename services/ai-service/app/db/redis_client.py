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
        raw = json.dumps(value, ensure_ascii=False, default=str)
        if ttl:
            await self._client.setex(key, ttl, raw)
        else:
            await self._client.set(key, raw)

    async def increment(self, key: str, ttl: int | None = None) -> int:
        """Increment a counter. Returns new value."""
        val = await self._client.incr(key)
        if ttl and val == 1:
            await self._client.expire(key, ttl)
        return val

    # ── Conversation Memory ─────────────────────────────────────────────────

    async def save_message(self, user_id: str, role: str, content: str,
                           agent_name: str | None = None) -> None:
        """Append a message to the user's conversation history."""
        import time
        key = f"conv:{user_id}"
        entry = json.dumps({
            "role": role,
            "content": content,
            "agent_name": agent_name,
            "timestamp": time.time(),
        }, ensure_ascii=False, default=str)
        await self._client.rpush(key, entry)
        await self._client.ltrim(key, -20, -1)  # Keep last 20 messages
        await self._client.expire(key, 86400)  # 24-hour TTL

    async def get_conversation_history(self, user_id: str,
                                        last_n: int = 10) -> list[dict]:
        """Get the last N messages from conversation history."""
        key = f"conv:{user_id}"
        entries = await self._client.lrange(key, -last_n, -1)
        return [json.loads(e) for e in entries] if entries else []

    async def save_user_context(self, user_id: str, context: dict) -> None:
        """Store agent-discovered context for follow-up queries."""
        await self.set_json(f"ctx:{user_id}", context, ttl=3600)

    async def get_user_context(self, user_id: str) -> dict | None:
        """Retrieve stored conversation context."""
        return await self.get_json(f"ctx:{user_id}")
