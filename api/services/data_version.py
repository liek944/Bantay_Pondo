"""Service for retrieving current data version."""

from api.config import get_settings
from db.session import get_async_db_connection

_cached_data_version: str | None = None


async def get_current_data_version() -> str:
    """Retrieve the current data version tag from the database or fall back to config."""
    global _cached_data_version
    if _cached_data_version is not None:
        return _cached_data_version

    settings = get_settings()
    try:
        async with get_async_db_connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "SELECT version_tag FROM data_versions "
                    "WHERE is_current = true ORDER BY published_at DESC LIMIT 1"
                )
                row = await cur.fetchone()
                if row and row[0]:
                    _cached_data_version = str(row[0])
                    return _cached_data_version
    except Exception:
        pass

    _cached_data_version = settings.data_version
    return _cached_data_version


def reset_version_cache() -> None:
    """Clear in-memory version cache."""
    global _cached_data_version
    _cached_data_version = None
