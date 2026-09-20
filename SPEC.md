Build the backend and data pipeline for "Bantay Pondo," a Philippine civic
accountability platform that scores whether government infrastructure spending
matches disaster-risk exposure at the LGU and barangay level.

DATA SOURCES (BetterGov.ph Open Data Portal, data.bettergov.ph — inspect the
actual resource endpoints and file formats before writing ingestion code; do not
assume schemas):

- DPWH infrastructure projects (contract ID, description, budget, contract cost,
  contractor, funding source, dates, physical progress, lat/lng, region)
- PhilGEPS procurement awards
- Project NOAH hazard maps (flood, landslide, storm surge polygons)
- PSGC administrative boundaries GeoJSON (barangay, municipality, city, province,
  region — each polygon carries a canonical PSGC code)
- Philippine election results (winners since 2001, vote counts since 2016)
- Politicians and public officials raw dataset
- Open Congress API (open-congress-api.bettergov.ph) for bills and members

STACK (non-negotiable):

- PostgreSQL 16 + PostGIS 3.4 as the single source of truth
- Python 3.12 for the ETL pipeline (httpx, polars, geopandas, psycopg3)
- FastAPI for the read API, async throughout
- Redis for response caching
- Docker Compose for local dev; multi-stage Dockerfiles, non-root users
- Alembic for migrations
- Vector tiles served from PostGIS via ST_AsMVT

REPO LAYOUT:
/pipeline ingestion, normalization, scoring jobs
/api FastAPI service
/db Alembic migrations, seed SQL, spatial index definitions
/infra docker-compose, Dockerfiles, nginx conf, deploy scripts
/tests

DATA MODEL — create these tables:
regions, provinces, municipalities, barangays
psgc_code (PK, text), name, parent_psgc, geom (geometry(MultiPolygon,4326)),
land_area_sqkm, population, population_year
hazard_zones
id, hazard_type (enum: flood|landslide|storm_surge), severity_level (int),
geom (geometry(MultiPolygon,4326)), source_dataset, source_year
projects
id, contract_id (unique), title, description, implementing_office,
contractor_id (FK), funding_source, budget_php (numeric), contract_cost_php,
start_date, target_completion_date, physical_progress_pct,
geom (geometry(Point,4326)), psgc_code (FK, resolved by spatial join),
source_row_hash, ingested_at
contractors
id, normalized_name (unique), raw_names (text[]), address,
first_seen, total_contracts, total_value_php
procurement_awards
id, reference_id, contractor_id (FK), title, award_amount_php, award_date,
procuring_entity, psgc_code
officials
id, name, position, psgc_code, district, term_start, term_end, party
locality_metrics -- materialized, recomputed by a scheduled job
psgc_code (PK), year, hazard_exposure_pct, flood_pct, landslide_pct,
surge_pct, population_at_risk, total_spend_php, spend_per_capita,
spend_per_exposed_sqkm, mismatch_score (numeric 0-100),
national_percentile, computed_at

SPATIAL INDEXES: GIST on every geom column. BRIN on ingested_at. Composite
btree on (psgc_code, year) in locality_metrics.

PIPELINE STAGES — each idempotent, each re-runnable, each logging row counts in
and out:

1. fetch — download source files to a local raw/ cache, content-hashed, skip
   unchanged files
2. parse — normalize to typed Polars frames, coerce peso amounts stripping
   currency symbols and commas, parse dates tolerantly, quarantine
   malformed rows to a rejects table with the reason
3. geocode — spatially join every project point to its containing barangay
   polygon via ST_Contains; projects whose coordinates fall outside
   all polygons or are null go to a review queue rather than being
   dropped silently
4. dedupe — contractor name normalization: uppercase, strip legal suffixes
   (INC, CORP, CO, ENTERPRISES, CONSTRUCTION), collapse whitespace,
   fuzzy-match with trigram similarity above 0.9 into a single
   canonical entity, preserving all raw variants
5. score — compute locality_metrics (formula below)
6. publish — refresh materialized views, warm the Redis cache, bump a
   data_version row

MISMATCH SCORE — implement exactly this, and expose every input in the API
response so the number is auditable:
hazard_exposure_pct = (area of locality intersecting any hazard polygon,
severity-weighted) / total locality area
Weight severity levels 1/2/3 as 0.3/0.6/1.0.
expected_share = locality's severity-weighted exposed area / national total
actual_share = locality's infrastructure spend / national total spend
ratio = actual_share / expected_share
mismatch_score = 50 + 50 \* tanh(ln(ratio)) -- clamp 0..100
Below 50 = underserved relative to risk. Above 50 = spend exceeds risk share.
Store the raw ratio alongside the score. Never label a locality as fraudulent
or corrupt anywhere in the data model or API — the score flags disproportion,
not wrongdoing.

API ENDPOINTS (all read-only, all cached, all returning a data_version field):
GET /v1/localities/search?q=&level= typeahead, trigram-backed
GET /v1/localities/{psgc_code} profile + metrics + officials
GET /v1/localities/{psgc_code}/projects paginated, filter by year,
funding_source, contractor,
min_budget
GET /v1/localities/compare?a=&b= side-by-side metrics
GET /v1/projects/{contract_id} detail + flags + related awards
GET /v1/contractors/{id} profile, contracts, district
concentration (HHI)
GET /v1/rankings?metric=&level=&limit= leaderboards
GET /v1/tiles/{layer}/{z}/{x}/{y}.mvt vector tiles: boundaries,
hazards, projects
GET /v1/meta/datasets source provenance, last refresh
timestamp per dataset
GET /healthz GET /readyz

PROJECT FLAGS — rule-based, each returning a human-readable string plus a
machine code, never a verdict:

- contract_cost exceeds budget by more than 15%
- physical_progress below 20% more than 12 months past target completion
- contractor holds more than 40% of a district's total contract value
- duplicate project descriptions within the same barangay and year
- project coordinates fall outside its stated region

NON-FUNCTIONAL REQUIREMENTS:

- Every endpoint under 300ms p95 on warm cache; tiles under 150ms
- Redis keys namespaced by data_version so a refresh invalidates cleanly
- Structured JSON logs, request IDs, Prometheus metrics at /metrics
- Rate limiting at the nginx layer, 60 req/min per IP for the API, uncapped
  for tiles
- OpenAPI schema auto-generated, served at /docs
- Pytest suite: unit tests for the scoring math against hand-computed fixtures,
  integration tests against a Dockerized Postgres with a small seeded fixture
  set, a contract test asserting every endpoint's response shape
- GitHub Actions: lint (ruff), typecheck (mypy strict on /pipeline and /api),
  test, build and push images
- docker-compose.yml for local; a separate compose file for a single-EC2
  deployment behind nginx with Let's Encrypt

DELIVER IN THIS ORDER, and stop after each for review:

1. Repo scaffold, Docker Compose, Postgres+PostGIS up, Alembic initialized
2. Schema migrations and spatial indexes
3. Ingestion for PSGC boundaries and NOAH hazards only, with row-count assertions
4. Ingestion for DPWH projects, including the spatial join and review queue
5. Scoring job with tests
6. API endpoints, no tiles yet
7. Vector tiles
8. Contractor dedupe, procurement join, flags
9. CI, deployment compose, nginx, observability

Ask me before choosing any library not listed above.
