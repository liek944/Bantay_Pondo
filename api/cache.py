"""Redis caching layer for Bantay Pondo API."""

import json
import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

from redis import asyncio as aioredis
from redis.exceptions import RedisError

from api.config import get_settings

logger = logging.getLogger(__name__)

_redis_client: aioredis.Redis | None = None
_redis_binary_client: aioredis.Redis | None = None


def get_redis_client() -> aioredis.Redis:
    """Return async Redis client instance, refreshing if event loop changed."""
    global _redis_client
    try:
        import asyncio

        current_loop = asyncio.get_running_loop()
        if _redis_client is not None:
            pool = getattr(_redis_client, "connection_pool", None)
            pool_loop = getattr(pool, "_loop", None)
            if pool_loop is not None and (pool_loop.is_closed() or pool_loop is not current_loop):
                _redis_client = None
    except RuntimeError:
        pass

    if _redis_client is None:
        settings = get_settings()
        _redis_client = aioredis.from_url(
            settings.redis_url,
            decode_responses=True,
            socket_timeout=2.0,
            socket_connect_timeout=2.0,
        )
    return _redis_client


def get_redis_binary_client() -> aioredis.Redis:
    """Return async Redis binary client instance (decode_responses=False) for raw bytes."""
    global _redis_binary_client
    try:
        import asyncio

        current_loop = asyncio.get_running_loop()
        if _redis_binary_client is not None:
            pool = getattr(_redis_binary_client, "connection_pool", None)
            pool_loop = getattr(pool, "_loop", None)
            if pool_loop is not None and (pool_loop.is_closed() or pool_loop is not current_loop):
                _redis_binary_client = None
    except RuntimeError:
        pass

    if _redis_binary_client is None:
        settings = get_settings()
        _redis_binary_client = aioredis.from_url(
            settings.redis_url,
            decode_responses=False,
            socket_timeout=2.0,
            socket_connect_timeout=2.0,
        )
    return _redis_binary_client


async def close_redis_client() -> None:
    """Close shared Redis client connection pools."""
    global _redis_client, _redis_binary_client
    if _redis_client is not None:
        try:
            await _redis_client.aclose()
        except Exception as exc:
            logger.warning("Error closing Redis client: %s", exc)
        finally:
            _redis_client = None

    if _redis_binary_client is not None:
        try:
            await _redis_binary_client.aclose()
        except Exception as exc:
            logger.warning("Error closing Redis binary client: %s", exc)
        finally:
            _redis_binary_client = None


def build_cache_key(data_version: str, route: str, **kwargs: Any) -> str:
    """Build namespaced cache key: bantay:{data_version}:{route}:{sorted_params}."""
    sorted_parts: list[str] = []
    for k in sorted(kwargs.keys()):
        v = kwargs[k]
        if v is not None:
            sorted_parts.append(f"{k}={v}")
    param_str = "&".join(sorted_parts) if sorted_parts else "default"
    return f"bantay:{data_version}:{route}:{param_str}"


async def get_cached(key: str) -> dict[str, Any] | list[Any] | None:
    """Retrieve and deserialize JSON payload from Redis cache.

    Returns None if cache miss or if Redis is unavailable.
    """
    try:
        client = get_redis_client()
        raw = await client.get(key)
        if raw is not None:
            return json.loads(raw)  # type: ignore[no-any-return]
    except (RedisError, ConnectionError, TimeoutError, json.JSONDecodeError) as exc:
        logger.warning("Redis cache read failed for key '%s': %s", key, exc)
    except Exception as exc:
        logger.error("Unexpected error during cache read for key '%s': %s", key, exc)
    return None


async def set_cached(key: str, value: Any, ttl: int | None = None) -> bool:
    """Serialize and store payload into Redis cache with TTL."""
    try:
        settings = get_settings()
        expire = ttl if ttl is not None else settings.cache_ttl_seconds
        client = get_redis_client()
        serialized = json.dumps(value, default=str)
        await client.set(key, serialized, ex=expire)
        return True
    except (RedisError, ConnectionError, TimeoutError, TypeError) as exc:
        logger.warning("Redis cache write failed for key '%s': %s", key, exc)
        return False
    except Exception as exc:
        logger.error("Unexpected error during cache write for key '%s': %s", key, exc)
        return False


async def get_cached_bytes(key: str) -> bytes | None:
    """Retrieve raw binary payload (e.g. MVT tile) from Redis cache.

    Returns None if cache miss or if Redis is unavailable.
    """
    try:
        client = get_redis_binary_client()
        raw = await client.get(key)
        if raw is not None and isinstance(raw, (bytes, bytearray)):
            return bytes(raw)
    except (RedisError, ConnectionError, TimeoutError) as exc:
        logger.warning("Redis binary cache read failed for key '%s': %s", key, exc)
    except Exception as exc:
        logger.error("Unexpected error during binary cache read for key '%s': %s", key, exc)
    return None


async def set_cached_bytes(key: str, value: bytes, ttl: int | None = None) -> bool:
    """Store raw binary payload (e.g. MVT tile) into Redis cache with TTL."""
    try:
        settings = get_settings()
        expire = ttl if ttl is not None else settings.cache_ttl_seconds
        client = get_redis_binary_client()
        await client.set(key, value, ex=expire)
        return True
    except (RedisError, ConnectionError, TimeoutError) as exc:
        logger.warning("Redis binary cache write failed for key '%s': %s", key, exc)
        return False
    except Exception as exc:
        logger.error("Unexpected error during binary cache write for key '%s': %s", key, exc)
        return False


async def invalidate_version(data_version: str) -> int:
    """Delete all keys for a given data_version."""
    try:
        client = get_redis_client()
        pattern = f"bantay:{data_version}:*"
        keys = await client.keys(pattern)
        if keys:
            deleted: int = await client.delete(*keys)
            logger.info("Invalidated %d cache keys for version %s", deleted, data_version)
            return deleted
        return 0
    except Exception as exc:
        logger.warning("Failed to invalidate cache for version %s: %s", data_version, exc)
        return 0


@asynccontextmanager
async def lifespan_redis() -> AsyncGenerator[None, None]:
    """Context manager for managing Redis client lifecycle."""
    get_redis_client()
    get_redis_binary_client()
    try:
        yield
    finally:
        await close_redis_client()
