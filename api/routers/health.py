"""Health and readiness probe routers."""

from fastapi import APIRouter, Response, status

from api.cache import get_redis_client
from api.schemas.health import HealthResponse, ReadyResponse
from api.services.data_version import get_current_data_version
from db.session import get_async_db_connection

router = APIRouter(tags=["Health"])


@router.get("/healthz", response_model=HealthResponse)
async def healthz() -> HealthResponse:
    """Liveness probe: verifies that the FastAPI process is running."""
    return HealthResponse(status="ok")


@router.get("/readyz", response_model=ReadyResponse)
async def readyz(response: Response) -> ReadyResponse:
    """Readiness probe: verifies that PostgreSQL and Redis connections are live."""
    db_status = "healthy"
    redis_status = "healthy"
    is_ready = True

    try:
        async with get_async_db_connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute("SELECT 1")
    except Exception:
        db_status = "unhealthy"
        is_ready = False

    try:
        client = get_redis_client()
        pong = await client.ping()
        if not pong:
            redis_status = "unhealthy"
            is_ready = False
    except Exception:
        redis_status = "unhealthy"
        is_ready = False

    data_version = await get_current_data_version()

    if not is_ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return ReadyResponse(
        status="ready" if is_ready else "unhealthy",
        database=db_status,
        redis=redis_status,
        data_version=data_version,
    )
