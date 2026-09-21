"""Health and readiness schemas."""

from pydantic import BaseModel


class HealthResponse(BaseModel):
    """Liveness probe response model."""

    status: str = "ok"


class ReadyResponse(BaseModel):
    """Readiness probe response model."""

    status: str = "ready"
    database: str
    redis: str
    data_version: str
