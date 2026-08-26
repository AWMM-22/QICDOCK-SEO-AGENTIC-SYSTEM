"""Optional Redis cache.

Uses REDIS_URL when reachable; silently degrades to no-op otherwise so the
system never fails because of cache unavailability (plan section 29.8).
"""
import json
import logging
from typing import Callable, Awaitable, Optional

from app.core.config.settings import settings

logger = logging.getLogger(__name__)

_client = None
_available: Optional[bool] = None


async def _get_client():
    global _client, _available
    if _available is False or not settings.REDIS_URL:
        return None
    if _client is None:
        try:
            import redis.asyncio as aioredis

            _client = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
            await _client.ping()
            _available = True
            logger.info("Redis cache connected")
        except Exception as e:
            logger.warning("Redis unavailable - caching disabled: %s", e)
            _client = None
            _available = False
    return _client


def _key(namespace: str, raw: str) -> str:
    return f"qicdock:{namespace}:{raw}"


async def cached(namespace: str, key: str, ttl_seconds: int,
                 factory: Callable[[], Awaitable[object]]) -> object:
    """Return cached value for key, else compute via factory() and store."""
    client = await _get_client()
    cache_key = _key(namespace, key)
    if client is None:
        return await factory()
    try:
        hit = await client.get(cache_key)
        if hit is not None:
            return json.loads(hit)
    except Exception as e:
        logger.warning("Cache read failed: %s", e)

    value = await factory()

    try:
        await client.set(cache_key, json.dumps(value, default=str), ex=ttl_seconds)
    except Exception as e:
        logger.warning("Cache write failed: %s", e)
    return value
