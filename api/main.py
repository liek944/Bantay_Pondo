"""Main FastAPI application entrypoint for Bantay Pondo."""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse

from api.cache import close_redis_client, get_redis_client
from api.config import get_settings
from api.middleware.logging import StructuredLoggingMiddleware
from api.middleware.metrics import MetricsMiddleware, render_prometheus_metrics
from api.middleware.request_id import RequestIDMiddleware
from api.routers import contractors, health, localities, meta, projects, rankings
from api.services.data_version import get_current_data_version

logger = logging.getLogger("api")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage application startup and shutdown lifecycles."""
    settings = get_settings()
    logging.basicConfig(
        level=settings.log_level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    logger.info("Initializing Bantay Pondo API...")

    # Pre-warm Redis connection
    try:
        client = get_redis_client()
        await client.ping()
        logger.info("Redis cache connection established successfully.")
    except Exception as exc:
        logger.warning("Redis initial ping failed: %s (will retry on demand)", exc)

    yield

    logger.info("Shutting down Bantay Pondo API...")
    await close_redis_client()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application instance."""
    settings = get_settings()

    app = FastAPI(
        title="Bantay Pondo API",
        description=(
            "Philippine civic accountability platform scoring whether government "
            "infrastructure spending matches disaster-risk exposure at the LGU and barangay level."
        ),
        version=settings.data_version,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # Middleware stack (registered in reverse order of execution)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(MetricsMiddleware)
    app.add_middleware(StructuredLoggingMiddleware)
    app.add_middleware(RequestIDMiddleware)

    # Routers
    app.include_router(health.router)
    app.include_router(localities.router)
    app.include_router(projects.router)
    app.include_router(contractors.router)
    app.include_router(rankings.router)
    app.include_router(meta.router)

    # Prometheus metrics endpoint
    @app.get("/metrics", response_class=PlainTextResponse, tags=["Observability"])
    async def metrics() -> PlainTextResponse:
        """Prometheus metrics endpoint in plain text exposition format."""
        return PlainTextResponse(
            render_prometheus_metrics(),
            media_type="text/plain; version=0.0.4",
        )

    # Global exception handlers
    @app.exception_handler(status.HTTP_404_NOT_FOUND)
    async def not_found_handler(request: Request, exc: Exception) -> JSONResponse:
        data_ver = await get_current_data_version()
        detail = getattr(exc, "detail", "Resource not found")
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"detail": detail, "data_version": data_ver},
            headers={"X-Data-Version": data_ver},
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.error("Unhandled exception processing %s: %s", request.url.path, exc, exc_info=True)
        data_ver = await get_current_data_version()
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Internal server error", "data_version": data_ver},
            headers={"X-Data-Version": data_ver},
        )

    return app


app = create_app()
