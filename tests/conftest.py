"""Pytest configuration and fixtures for Bantay Pondo."""

from collections.abc import AsyncGenerator, Generator
from typing import Any

import httpx
import psycopg
import pytest
import redis

from api.config import Settings, get_settings
from api.main import app
from db.session import get_raw_conninfo


@pytest.fixture(scope="session")
def settings() -> Settings:
    """Provide session-wide application settings."""
    return get_settings()


@pytest.fixture(scope="function")
def db_conn() -> Generator[psycopg.Connection[Any], None, None]:
    """Provide a direct psycopg database connection for testing."""
    with psycopg.connect(get_raw_conninfo()) as conn:
        yield conn


@pytest.fixture(scope="function")
def redis_client(settings: Settings) -> Generator[redis.Redis, None, None]:
    """Provide a connected Redis client for testing."""
    client: redis.Redis = redis.from_url(settings.redis_url, decode_responses=True)
    yield client
    client.close()


@pytest.fixture(scope="function")
async def async_client() -> AsyncGenerator[httpx.AsyncClient, None]:
    """Provide an asynchronous HTTP test client bound to the FastAPI app."""
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client

