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
| 5 | Scoring job with tests | **COMPLETED** | `milestone/05-scoring-job` | 41 passing |
| 6 | API endpoints, no tiles yet | **COMPLETED** | `milestone/06-api-endpoints` | 58 passing |
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

---

## Milestone 5 Details: Scoring Job with Tests

- **Status**: Complete
- **Branch**: `milestone/05-scoring-job`
- **Completed On**: 2026-09-20

### Deliverables:
1. **Mathematical Scoring Engine (`pipeline/stages/score.py`)**:
   - Implemented exact SPEC mismatch scoring formula:
     - Hazard exposure percentage: severity-weighted exposed area / total locality area.
     - Severity level weights: level 1 = 0.3, level 2 = 0.6, level 3 = 1.0.
     - `expected_share`: locality's severity-weighted exposed area / national total exposed area.
     - `actual_share`: locality's infrastructure spend / national total spend.
     - `raw_ratio = actual_share / expected_share`.
     - `mismatch_score = clamp(50 + 50 * tanh(ln(ratio)), 0..100)`.
   - Handled all boundary conditions safely:
     - Balanced spend & risk ($r = 1.0 \implies \text{score} = 50.0$).
     - Underserved ($r < 1.0 \implies \text{score} < 50.0$, zero spend $\implies \text{score} = 0.0$).
     - Overserved ($r > 1.0 \implies \text{score} > 50.0$, zero risk $\implies \text{score} = 100.0$).
     - Finite ratio sentinel (`Decimal("999999.0000")`) to ensure valid JSON serialization across Pydantic models and APIs.
     - No labeling of localities as fraudulent or corrupt — score measures disproportion, not wrongdoing.
2. **PostGIS High-Performance Spatial Exposure Engine**:
   - Pre-filtered candidate localities using spatial bounding box envelopes (`&&`).
   - Polygon subdivision (`ST_Subdivide(geom, 256)`) with GIST indexing on temporary tables to compute exact spherical polygon intersection areas (`ST_Area(ST_Intersection(...)::geography, false) / 1e6`).
   - Grouped exposures across hazard types (`flood`, `landslide`, `storm_surge`) and rolled up from barangays to municipalities.
3. **Locality Metrics Materialization**:
   - Aggregated DPWH project spend per year and locality (`EXTRACT(YEAR FROM start_date)`).
   - Computed `hazard_exposure_pct`, `flood_pct`, `landslide_pct`, `surge_pct`.
   - Computed `population_at_risk`, `spend_per_capita`, and `spend_per_exposed_sqkm`.
   - Computed `national_percentile` via SQL window function `PERCENT_RANK() OVER (PARTITION BY year ORDER BY mismatch_score ASC) * 100`.
   - Idempotent upsert via `ON CONFLICT (psgc_code, year) DO UPDATE`.
4. **Pipeline CLI Runner Integration (`pipeline/main.py`)**:
   - Subcommand `score [--year YYYY] [--level municipalities|barangays|all]`.
   - Integrated into `pipeline/main.py all`.
   - Executed on live dataset slice: 1,894 metrics upserted across 1,894 localities for year 2021.
5. **Automated Verification Suite (`tests/test_milestone_05.py`)**:
   - 10 new automated tests (41 total across repo):
     - Severity weights verification ($0.3, 0.6, 1.0$).
     - Pure math unit tests for balanced allocation ($\text{score} = 50.0$).
     - Pure math tests against hand-computed identities ($\text{ratio } 2.0 \implies 80.0, 0.5 \implies 20.0, 3.0 \implies 90.0, 1/3 \implies 10.0$).
     - Orders of magnitude verification ($\text{ratio } 10.0 \implies 99.0099, 0.1 \implies 0.9901$).
     - Boundary condition handling (zero spend, zero risk, both zero).
     - Exposure percentage clamping ($0 \le \text{pct} \le 100$).
     - Spatial hazard exposure caching asserting non-zero exposure in Batanes and Cagayan.
     - End-to-end scoring job execution and column validity in `locality_metrics`.
     - Idempotency test asserting zero duplicate rows on re-runs.
     - Baseline fixture row-count preservation.
6. **Fixture Dataset Row-Count Assertions**:
   - Preserved exact baseline boundary and hazard row counts: 17 regions, 82 provinces, 1,620 municipalities, 41,803 barangays, and 9 hazard zones.

### Definition of Done Checklist:
- [x] `ruff check` passes on `/pipeline`, `/api`, `/db`, and `/tests` (0 errors).
- [x] `mypy --strict` passes on `/pipeline` and `/api` (0 errors).
- [x] `pytest` passes (41/41 tests passing).
- [x] Row-count assertions hold on the fixture dataset (17 regions, 82 provinces, 1,620 municipalities, 41,803 barangays, 9 hazard zones).
- [x] `PROGRESS.md` updated.
- [x] Committed on branch `milestone/05-scoring-job` with descriptive message.

---

## Milestone 6 Details: API Endpoints, No Tiles Yet

- **Status**: Complete
- **Branch**: `milestone/06-api-endpoints`
- **Completed On**: 2026-09-21

### Deliverables:
1. **Core API Configuration & Redis Caching Layer (`api/config.py`, `api/cache.py`)**:
   - Configuration for cache TTL (300s), default pagination (20), and max limit (100).
   - Async Redis caching engine with namespaced keys: `bantay:{data_version}:{route}:{sorted_params}`.
   - Robust error handling: transparently falls back to direct PostgreSQL query execution if Redis times out or is temporarily unavailable.
   - Response header injection: `X-Cache: HIT` / `X-Cache: MISS` and `X-Data-Version: ...`.
2. **Observability, Tracing & Middlewares (`api/middleware/`)**:
   - `RequestIDMiddleware`: extracts incoming `X-Request-ID` or generates UUID4, persisting it through response headers.
   - `StructuredLoggingMiddleware`: structured JSON access logging with duration in milliseconds, status codes, and client IP.
   - `MetricsMiddleware` & `/metrics`: Prometheus metrics collector exposing request totals by method/endpoint/status and request durations in standard Prometheus exposition format.
3. **Pydantic Schemas (`api/schemas/`)**:
   - `common.py`: BaseResponse guaranteeing `data_version`, generic `PaginatedResponse[T]`, and `ErrorResponse`.
   - `localities.py`: Locality search results with similarity scores, profile response, metrics history, officials summary, and side-by-side comparison deltas.
   - `projects.py`: Project summary, detailed view with geocoded barangay/municipality/province/region hierarchy, procurement awards, and rule-based risk flags.
   - `contractors.py`: Contractor summary, contracts list, and Herfindahl-Hirschman Index (HHI) concentration metrics with market shares per implementing office.
   - `rankings.py`: Leaderboards ranked by `mismatch_score`, `total_spend_php`, `hazard_exposure_pct`, `spend_per_capita`, `population_at_risk`.
   - `meta.py`: Source provenance, last refresh timestamps, record counts, and checksums for all platform datasets.
   - `health.py`: Liveness and readiness probe responses.
4. **Database Services & Business Logic (`api/services/`)**:
   - `data_version.py`: Active dataset version lookup with database fallback to configuration.
   - `localities.py`: Trigram-backed similarity typeahead search, hierarchical profile lookup, paginated project filtering, and comparison deltas.
   - `projects.py`: Project detail with rule-based flag evaluations (`COST_OVERRUN_15PCT`, `DELAYED_LOW_PROGRESS`, `DISTRICT_CONTRACTOR_CONCENTRATION_40PCT`, `DUPLICATE_DESCRIPTION_BARANGAY_YEAR`, `COORDINATES_OUTSIDE_REGION`).
   - `contractors.py`: Profile resolution and HHI market concentration calculation ($HHI = \sum s_i^2 \times 10,000$).
   - `rankings.py`: Leaderboard ranking aggregations by metric and administrative level.
   - `meta.py`: Dataset provenance and row-count tracking from manifest and database.
5. **FastAPI Application & Routers (`api/main.py`, `api/routers/`)**:
   - Lifespan management for Redis and database connection pools.
   - Registered routers: `/healthz`, `/readyz`, `/v1/localities`, `/v1/projects`, `/v1/contractors`, `/v1/rankings`, `/v1/meta/datasets`.
   - OpenAPI documentation served at `/docs`, `/redoc`, and `/openapi.json`.
6. **Automated Verification Suite (`tests/test_milestone_06.py`)**:
   - 17 new automated tests (58 total across repository):
     - Health and readiness endpoints (`/healthz`, `/readyz`).
     - Prometheus metrics text format (`/metrics`).
     - OpenAPI schema completeness.
     - Trigram locality typeahead search.
     - Locality profile, metrics history, and officials.
     - Locality projects pagination and budget filtering.
     - Side-by-side locality comparison.
     - Project detail and rule-based flags.
     - Pure logic flag evaluation.
     - Contractor profile and HHI concentration calculation.
     - Rankings leaderboards.
     - Platform datasets provenance.
     - Redis caching HIT / MISS verification.
     - Request ID tracing middleware.
     - Baseline fixture row-count preservation.
7. **Fixture Dataset Row-Count Assertions**:
   - Preserved exact baseline boundary and hazard row counts: 17 regions, 82 provinces, 1,620 municipalities, 41,803 barangays, and 9 hazard zones.

### Definition of Done Checklist:
- [x] `ruff check` passes on `/pipeline`, `/api`, `/db`, and `/tests` (0 errors).
- [x] `mypy --strict` passes on `/pipeline` and `/api` (0 errors).
- [x] `pytest` passes (58/58 tests passing in 2m 42s).
- [x] Row-count assertions hold on the fixture dataset (17 regions, 82 provinces, 1,620 municipalities, 41,803 barangays, 9 hazard zones).
- [x] `PROGRESS.md` updated.
- [x] Committed on branch `milestone/06-api-endpoints` with descriptive message.


