"""Database session and connection management."""

from collections.abc import AsyncGenerator, Generator
from contextlib import asynccontextmanager, contextmanager
from typing import Any

import psycopg
from psycopg import AsyncConnection, Connection
from sqlalchemy import Engine, create_engine
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import Session, sessionmaker

from api.config import get_settings


def get_raw_conninfo() -> str:
    """Return PostgreSQL conninfo string for native psycopg connections."""
    s = get_settings()
    return (
        f"host={s.postgres_host} port={s.postgres_port} "
        f"dbname={s.postgres_db} user={s.postgres_user} "
        f"password={s.postgres_password}"
    )


def get_sync_engine() -> Engine:
    """Create a synchronous SQLAlchemy engine for migrations and sync tasks."""
    settings = get_settings()
    return create_engine(settings.database_url, echo=False)


def get_async_engine() -> AsyncEngine:
    """Create an asynchronous SQLAlchemy engine for FastAPI services."""
    settings = get_settings()
    return create_async_engine(settings.database_url_async, echo=False)


def get_sync_sessionmaker() -> sessionmaker[Session]:
    """Create a synchronous sessionmaker factory."""
    return sessionmaker(bind=get_sync_engine(), autoflush=False, autocommit=False)


def get_async_sessionmaker() -> async_sessionmaker[AsyncSession]:
    """Create an asynchronous sessionmaker factory."""
    return async_sessionmaker(bind=get_async_engine(), autoflush=False, expire_on_commit=False)


@contextmanager
def get_db_connection() -> Generator[Connection[Any], None, None]:
    """Provide a direct synchronous psycopg connection context."""
    with psycopg.connect(get_raw_conninfo()) as conn:
        yield conn


@asynccontextmanager
async def get_async_db_connection() -> AsyncGenerator[AsyncConnection[Any], None]:
    """Provide a direct asynchronous psycopg connection context."""
    async with await psycopg.AsyncConnection.connect(get_raw_conninfo()) as conn:
        yield conn
