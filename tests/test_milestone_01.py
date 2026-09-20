"""Verification tests for Milestone 1: Repo scaffold, Docker Compose, Postgres+PostGIS, Alembic."""

from pathlib import Path
from typing import Any

import psycopg
import redis
from alembic.config import Config
from alembic.script import ScriptDirectory

from api.config import Settings


def test_spec_repo_layout() -> None:
    """SPEC requirement: repo layout contains /pipeline, /api, /db, /infra, /tests."""
    root = Path(__file__).resolve().parent.parent
    expected_dirs = ["pipeline", "api", "db", "infra", "tests"]
    for dir_name in expected_dirs:
        dir_path = root / dir_name
        assert dir_path.is_dir(), f"Expected directory '{dir_name}' does not exist at {dir_path}"


def test_postgres_version_and_connection(db_conn: psycopg.Connection[Any]) -> None:
    """SPEC requirement: PostgreSQL 16 as the single source of truth."""
    with db_conn.cursor() as cur:
        cur.execute("SHOW server_version;")
        row = cur.fetchone()
        assert row is not None, "Failed to retrieve PostgreSQL server version"
        version_str = str(row[0])
        assert version_str.startswith("16"), f"Expected PostgreSQL 16.x, got '{version_str}'"


def test_postgis_extension_and_spatial_functionality(db_conn: psycopg.Connection[Any]) -> None:
    """SPEC requirement: PostGIS 3.4 with valid spatial operations."""
    with db_conn.cursor() as cur:
        cur.execute("SELECT PostGIS_Version();")
        row = cur.fetchone()
        assert row is not None, "Failed to retrieve PostGIS version"
        postgis_ver = str(row[0])
        assert postgis_ver.startswith("3.4"), f"Expected PostGIS 3.4.x, got '{postgis_ver}'"

        # Verify spatial geometry creation and SRID 4326 compliance
        cur.execute("SELECT ST_AsText(ST_SetSRID(ST_MakePoint(120.9842, 14.5995), 4326));")
        pt_row = cur.fetchone()
        assert pt_row is not None
        assert pt_row[0] == "POINT(120.9842 14.5995)"


def test_redis_connectivity(redis_client: redis.Redis) -> None:
    """SPEC requirement: Redis for response caching."""
    pong = redis_client.ping()
    assert pong is True, f"Expected PING response True, got {pong}"

    test_key = "bantay:test:milestone_01"
    redis_client.set(test_key, "ok", ex=10)
    val = redis_client.get(test_key)
    assert val == "ok"
    redis_client.delete(test_key)


def test_alembic_initialization(settings: Settings) -> None:
    """SPEC requirement: Alembic initialized and configured."""
    root = Path(__file__).resolve().parent.parent
    ini_path = root / "alembic.ini"
    assert ini_path.is_file(), f"Missing alembic.ini at {ini_path}"

    config = Config(str(ini_path))
    script = ScriptDirectory.from_config(config)
    assert Path(script.dir).resolve() == (root / "db" / "migrations").resolve(), (
        f"Alembic script dir mismatch: {script.dir}"
    )

    # Verify versions directory exists
    versions_dir = root / "db" / "migrations" / "versions"
    assert versions_dir.is_dir(), f"Missing migrations versions dir at {versions_dir}"


def test_docker_compose_and_dockerfiles() -> None:
    """SPEC requirement: Docker Compose for local dev, multi-stage Dockerfiles, non-root users."""
    root = Path(__file__).resolve().parent.parent
    compose_path = root / "infra" / "docker-compose.yml"
    assert compose_path.is_file(), f"Missing {compose_path}"

    compose_content = compose_path.read_text()
    assert "postgis/postgis:16-3.4-alpine" in compose_content
    assert "redis:7-alpine" in compose_content

    api_dockerfile = root / "infra" / "Dockerfile.api"
    assert api_dockerfile.is_file(), f"Missing {api_dockerfile}"
    api_content = api_dockerfile.read_text()
    assert "FROM python:3.12-slim AS builder" in api_content
    assert "USER appuser" in api_content

    pipeline_dockerfile = root / "infra" / "Dockerfile.pipeline"
    assert pipeline_dockerfile.is_file(), f"Missing {pipeline_dockerfile}"
    pipeline_content = pipeline_dockerfile.read_text()
    assert "FROM python:3.12-slim AS builder" in pipeline_content
    assert "USER appuser" in pipeline_content
