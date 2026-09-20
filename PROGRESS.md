# Bantay Pondo — Implementation Progress

Project tracking across the 9 sequential delivery milestones specified in [SPEC.md](SPEC.md).

---

## Milestone Status Overview

| # | Milestone | Status | Branch | Tests |
|---|---|---|---|---|
| 1 | Repo scaffold, Docker Compose, Postgres+PostGIS up, Alembic initialized | **COMPLETED** | `milestone/01-repo-scaffold` | 6 passing |
| 2 | Schema migrations and spatial indexes | Pending | `milestone/02-schema-migrations` | — |
| 3 | Ingestion for PSGC boundaries and NOAH hazards only, with row-count assertions | Pending | — | — |
| 4 | Ingestion for DPWH projects, including the spatial join and review queue | Pending | — | — |
| 5 | Scoring job with tests | Pending | — | — |
| 6 | API endpoints, no tiles yet | Pending | — | — |
| 7 | Vector tiles | Pending | — | — |
| 8 | Contractor dedupe, procurement join, flags | Pending | — | — |
| 9 | CI, deployment compose, nginx, observability | Pending | — | — |

---

## Milestone 1 Details: Repo Scaffold, Docker Compose, Postgres+PostGIS, Alembic Initialized

- **Status**: Complete
- **Branch**: `milestone/01-repo-scaffold`
- **Completed On**: 2026-09-20

### Deliverables:
1. **Repository Structure**: Created canonical SPEC directory layout:
   - `/pipeline`: Data ingestion, normalization, and scoring jobs.
   - `/api`: FastAPI asynchronous service.
   - `/db`: Database session management, Alembic environment, migration versions.
   - `/infra`: Docker compose specification and multi-stage Dockerfiles.
   - `/tests`: Pytest test suite and test fixtures.
2. **Docker Compose & Infrastructure**:
   - `infra/docker-compose.yml` & root `docker-compose.yml`: Configured with `postgis/postgis:16-3.4-alpine` (PostgreSQL 16, PostGIS 3.4.3) and `redis:7-alpine`.
   - `infra/Dockerfile.api`: Multi-stage build with non-root user (`appuser`, UID 10001).
   - `infra/Dockerfile.pipeline`: Multi-stage build with non-root user (`appuser`, UID 10001).
3. **Python Environment & Tooling**:
   - `pyproject.toml`: Defined dependencies matching SPEC stack (httpx, polars, geopandas, psycopg3, fastapi, redis, alembic, sqlalchemy, geoalchemy2, pydantic-settings, pytest, ruff, mypy).
   - `.gitignore` and `.env.example` / `.env` for local environment configuration.
4. **Alembic Initialization**:
   - `alembic.ini` and `db/migrations/env.py` configured with dynamic database URL loading and filtering of PostGIS system/tiger tables.
   - Initialized migration environment in `db/migrations/versions`.
5. **Database Session & Settings**:
   - `api/config.py`: Strongly typed configuration using Pydantic Settings.
   - `db/session.py`: Psycopg and SQLAlchemy connection and session factories supporting async and sync access.
6. **Automated Verification Suite**:
   - `tests/test_milestone_01.py`: 6 tests asserting repository layout, PostgreSQL 16 connection, PostGIS 3.4 spatial operations, Redis connectivity, Alembic initialization, and Dockerfiles.

### Definition of Done Checklist:
- [x] `ruff check` passes on `/pipeline`, `/api`, `/db`, and `/tests` (0 errors).
- [x] `mypy --strict` passes on `/pipeline` and `/api` (0 errors).
- [x] `pytest` passes (6/6 tests passing in 0.66s).
- [x] Row-count assertions hold on baseline database.
- [x] `PROGRESS.md` updated.
- [x] Committed on branch `milestone/01-repo-scaffold` with descriptive message.
