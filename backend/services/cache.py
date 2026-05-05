"""Redis-backed cache helper.

All third-party API calls use ``cached(...)`` to avoid hammering paid endpoints.
Keys are namespaced by project where possible to avoid leakage.
"""

from __future__ import annotations

import hashlib
import logging
from typing import Any, Awaitable, Callable, Optional

import orjson
import redis.asyncio as aioredis

from config import settings

log = logging.getLogger(__name__)

_redis: Optional[aioredis.Redis] = None


async def get_redis() -> aioredis.Redis:
    global _redis
    if _redis is None:
        _redis = aioredis.from_url(settings.redis_url, encoding="utf-8", decode_responses=False)
    return _redis


def make_key(*parts: Any) -> str:
    """Stable cache key from arbitrary parts."""
    raw = "|".join(str(p) for p in parts)
    if len(raw) > 200:
        raw = hashlib.sha256(raw.encode()).hexdigest()
    return f"seolab:{raw}"


async def cached(
    key: str,
    ttl: int,
    fetcher: Callable[[], Awaitable[Any]],
    force_refresh: bool = False,
) -> Any:
    """Get-or-set helper. Stores JSON-serialised values."""
    r = await get_redis()
    if not force_refresh:
        try:
            blob = await r.get(key)
            if blob is not None:
                return orjson.loads(blob)
        except Exception as e:  # pragma: no cover - cache must never break the flow
            log.warning("cache get failed for %s: %s", key, e)

    value = await fetcher()
    try:
        await r.set(key, orjson.dumps(value), ex=ttl)
    except Exception as e:  # pragma: no cover
        log.warning("cache set failed for %s: %s", key, e)
    return value


async def invalidate(pattern: str) -> int:
    r = await get_redis()
    deleted = 0
    async for key in r.scan_iter(match=pattern, count=500):
        await r.delete(key)
        deleted += 1
    return deleted
