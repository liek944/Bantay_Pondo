# Bantay Pondo — Implementation Progress

Project tracking across the 9 sequential delivery milestones specified in [SPEC.md](SPEC.md).

---

## Milestone Status Overview

| # | Milestone | Status | Branch | Tests |
|---|---|---|---|---|
| 1 | Repo scaffold, Docker Compose, Postgres+PostGIS up, Alembic initialized | **COMPLETED** | `milestone/01-repo-scaffold` | 6 passing |
| 2 | Schema migrations and spatial indexes | **COMPLETED** | `milestone/02-schema-migrations` | 16 passing |
| 3 | Ingestion for PSGC boundaries and NOAH hazards only, with row-count assertions | **COMPLETED** | `milestone/03-psgc-noah-ingestion` | 23 passing |
| 4 | Ingestion for DPWH projects, including the spatial join and review queue | **COMPLETED** | `milestone/04-dpwh-ingestion` | 31 passing |
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

---

## Milestone 2 Details: Schema Migrations and Spatial Indexes

- **Status**: Complete
- **Branch**: `milestone/02-schema-migrations`
- **Completed On**: 2026-09-20

### Deliverables:
1. **SQLAlchemy 2.0 Declarative Models (`db/models.py`)**:
   - Administrative boundaries with PostGIS MultiPolygon SRID 4326: `regions`, `provinces`, `municipalities`, `barangays`.
   - Disaster hazard exposure polygons: `hazard_zones` with `hazard_type_enum` (`flood`, `landslide`, `storm_surge`).
   - Core domain models: `projects` (with Point geometry SRID 4326), `contractors` (with string array aliases and trigram index), `procurement_awards`, `officials`.
   - Scoring & metrics model: `locality_metrics` with composite primary key `(psgc_code, year)`.
   - Ingestion and data versioning models: `project_reviews` (review queue), `rejects` (quarantine table), `data_versions` (cache & refresh tracking).
2. **Alembic Migration (`db/migrations/versions/0001_initial_schema.py`)**:
   - Registered extensions: `postgis`, `pg_trgm`, `btree_gist`.
   - Safe, idempotent schema setup and rollback (`upgrade()` / `downgrade()`).
   - Bound metadata to `db/migrations/env.py` (`target_metadata = Base.metadata`).
   - Database verified and stamped at revision `0001_initial_schema (head)`.
3. **Spatial and Performance Indexes**:
   - GIST spatial indexes on every geometry column: `regions.geom`, `provinces.geom`, `municipalities.geom`, `barangays.geom`, `hazard_zones.geom`, `projects.geom`.
   - BRIN index on `projects.ingested_at`.
   - Composite B-Tree index on `locality_metrics(psgc_code, year)`.
   - GIN trigram index on `contractors.normalized_name` (`gin_trgm_ops`).
4. **Automated Verification Suite (`tests/test_milestone_02.py`)**:
   - 10 new automated tests (16 total) validating Alembic head revision, table existence, geometry types and SRID 4326, GIST/BRIN/B-tree/GIN trigram indexes, foreign key constraints, live spatial queries, and fixture row-count preservation.
5. **Fixture Dataset Verification**:
   - Preserved exact fixture row counts: 17 regions, 82 provinces, 1,620 municipalities, 41,803 barangays, and 9 hazard zones.

### Definition of Done Checklist:
- [x] `ruff check` passes on `/pipeline`, `/api`, `/db`, and `/tests` (0 errors).
- [x] `mypy --strict` passes on `/pipeline`, `/api`, `/db`, and `/tests` (0 errors).
- [x] `pytest` passes (16/16 tests passing in 1.90s).
- [x] Row-count assertions hold on the fixture dataset (17 regions, 82 provinces, 1,620 municipalities, 41,803 barangays, 9 hazard zones).
- [x] `PROGRESS.md` updated.
- [x] Committed on branch `milestone/02-schema-migrations` with descriptive message.

---

## Milestone 3 Details: Ingestion for PSGC Boundaries and NOAH Hazards Only

- **Status**: Complete
- **Branch**: `milestone/03-psgc-noah-ingestion`
- **Completed On**: 2026-09-20

### Deliverables:
1. **Pipeline Fetch Stage (`pipeline/stages/fetch.py`)**:
   - Implemented `compute_sha256` and `fetch_file` with content-addressed caching, atomic writing (`.part`), and manifest tracking (`data/raw/manifest.json`).
   - Network download skipping when local file SHA256 matches manifest.
2. **PSGC Boundaries Ingestion Stage (`pipeline/stages/ingest_psgc.py`)**:
   - Real schema discovery for 4 boundary tiers (`regions`, `provinces`, `municipalities`, `barangays`).
   - Geometry normalization to 2D PostGIS `MultiPolygon(4326)` via Shapely and WKB.
   - Spheroidal land area parsing and parent PSGC hierarchy resolution.
   - Idempotent upsert via `ON CONFLICT (psgc_code) DO UPDATE`.
   - Rejects quarantine table logging (`rejects`) on malformed/invalid geometries without silent drops.
3. **Project NOAH Hazards Ingestion Stage (`pipeline/stages/ingest_noah.py`)**:
   - Direct `.zip` shapefile extraction and parsing with GeoPandas.
   - PostGIS `MultiPolygon(4326)` normalization and CRS reprojection if needed.
   - Classification across `hazard_type_enum` (`flood`, `landslide`, `storm_surge`) and severity levels 1, 2, 3.
   - Idempotent ingestion per dataset source and hazard type.
4. **Pipeline CLI Entrypoint (`pipeline/main.py`)**:
   - CLI subcommands `ingest-boundaries`, `ingest-hazards`, and `all`.
   - Strictly typed with `TypedDict` and type annotations passing `mypy --strict`.
5. **Automated Verification Suite (`tests/test_milestone_03.py`)**:
   - 7 new automated tests (23 total) verifying fetch SHA256 manifest caching, geometry normalization, boundary row-count assertions (17 regions, 82 provinces, 1,620 municipalities, 41,803 barangays), Tuguegarao City presence and geometry validity, NOAH hazard zone counts and types, quarantine rejects logging, and idempotency.
6. **Fixture Dataset Row-Count Assertions**:
   - Preserved exact fixture row counts: 17 regions, 82 provinces, 1,620 municipalities, 41,803 barangays, and 9 hazard zones.

### Definition of Done Checklist:
- [x] `ruff check` passes on `/pipeline`, `/api`, and `/tests` (0 errors).
- [x] `mypy --strict` passes on `/pipeline` and `/api` (0 errors).
- [x] `pytest` passes (23/23 tests passing in 4.57s).
- [x] Row-count assertions hold on the fixture dataset (17 regions, 82 provinces, 1,620 municipalities, 41,803 barangays, 9 hazard zones).
- [x] `PROGRESS.md` updated.
- [x] Committed on branch `milestone/03-psgc-noah-ingestion` with descriptive message.

---

## Milestone 4 Details: Ingestion for DPWH Projects, Spatial Join, and Review Queue

- **Status**: Complete
- **Branch**: `milestone/04-dpwh-ingestion`
- **Completed On**: 2026-09-20

### Deliverables:
1. **Real Schema Discovery & Profiling**:
   - Profiled `bettergovph/dpwh-transparency-data` (`dpwh_transparency_data.parquet`, 24.3 MB, 248,220 rows).
   - Confirmed 248,220 unique `contractId`s (100% unique primary identifiers).
   - Identified 214,747 (86.5%) projects with valid Philippine coordinates and 33,473 (13.5%) projects with missing coordinates.
   - PostGIS `ST_Contains` point benchmark resolved 10,000 points in 5.1s via PostGIS GIST spatial indexing.
2. **DPWH Projects Ingestion Stage (`pipeline/stages/ingest_dpwh.py`)**:
   - Normalized fields: `contract_id`, `title`, `description`, `implementing_office`, `funding_source`, `budget_php`, `contract_cost_php`, `start_date`, `target_completion_date`, `physical_progress_pct`, `latitude`, `longitude`.
   - Computed SHA256 `source_row_hash` per row for change tracking and auditability.
   - High-performance set-based PostGIS spatial join using temporary staging table with GIST index.
   - Routing without silent drops:
     - Projects matching a containing barangay polygon have `geom` and `psgc_code` populated.
     - Projects with null or out-of-range coordinates are stored in `projects` with `psgc_code = NULL` and recorded in `project_reviews` (`Missing coordinates (null lat/lon)`).
     - Projects whose coordinates fall outside all barangay polygons (offshore/marine works) are stored in `projects` with `geom = Point` and `psgc_code = NULL` and recorded in `project_reviews` (`Coordinates outside all barangay boundaries`).
     - Malformed rows (e.g. empty `contractId`) are quarantined into `rejects` table.
   - Idempotent upsert via `ON CONFLICT (contract_id) DO UPDATE`.
   - Conservation accounting invariant: `total_in == geocoded + review_queue + rejects`.
3. **Pipeline CLI Integration (`pipeline/main.py`)**:
   - Registered `run_ingest_projects(limit=None)` and CLI subcommands `ingest-projects [--limit N]` and `--limit-projects` in `all`.
   - Successfully executed on live dataset slice (1,000 projects): 821 geocoded, 179 in review queue, 0 rejects, 1,000 upserted in projects.
4. **Automated Verification Suite (`tests/test_milestone_04.py`)**:
   - 8 new automated tests (31 total) verifying normalization, date parsing, row hash generation, invalid row rejection, spatial join to known barangay (Maraiging, PSGC `1600205010`), missing coordinate routing to review queue, offshore coordinate routing to review queue, malformed row quarantine in rejects, idempotency, and batch accounting balance conservation.
5. **Fixture Dataset Row-Count Assertions**:
   - Preserved exact baseline boundary and hazard row counts: 17 regions, 82 provinces, 1,620 municipalities, 41,803 barangays, and 9 hazard zones.

### Definition of Done Checklist:
- [x] `ruff check` passes on `/pipeline`, `/api`, `/db`, and `/tests` (0 errors).
- [x] `mypy --strict` passes on `/pipeline`, `/api`, and `/tests` (0 errors).
- [x] `pytest` passes (31/31 tests passing in 4.17s).
- [x] Row-count assertions hold on the fixture dataset (17 regions, 82 provinces, 1,620 municipalities, 41,803 barangays, 9 hazard zones).
- [x] `PROGRESS.md` updated.
- [x] Committed on branch `milestone/04-dpwh-ingestion` with descriptive message.

