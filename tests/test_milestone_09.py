"""Verification tests for Milestone 9: CI, deployment compose, nginx, and observability."""

import os
import re
from pathlib import Path
from typing import Any

import httpx
import psycopg
import pytest
import yaml

# ---------------------------------------------------------------------------
# CI & Infrastructure Configuration Tests
# ---------------------------------------------------------------------------


def test_github_actions_ci_workflow_structure() -> None:
    """Validate .github/workflows/ci.yml syntax, triggers, jobs, and steps per SPEC."""
    ci_path = Path(".github/workflows/ci.yml")
    assert ci_path.exists(), ".github/workflows/ci.yml must exist"

    with ci_path.open() as f:
        ci_yaml = yaml.safe_load(f)

    # Workflow triggers
    assert "push" in ci_yaml.get("on", ci_yaml.get(True, {}))
    assert "pull_request" in ci_yaml.get("on", ci_yaml.get(True, {}))

    # Jobs definition
    jobs = ci_yaml["jobs"]
    assert "lint-and-typecheck" in jobs, "CI must contain lint-and-typecheck job"
    assert "test" in jobs, "CI must contain test job"
    assert "build-images" in jobs, "CI must contain build-images job"

    # Step commands in lint job
    lint_job = jobs["lint-and-typecheck"]
    lint_commands = [
        step.get("run", "") for step in lint_job.get("steps", []) if "run" in step
    ]
    lint_str = " ".join(lint_commands)
    assert "ruff check" in lint_str, "CI must run ruff check"
    assert "mypy --strict" in lint_str, "CI must run mypy --strict on pipeline and api"

    # Test job services: PostGIS 16 & Redis 7
    test_job = jobs["test"]
    services = test_job.get("services", {})
    assert "postgres" in services, "test job must have postgres service container"
    assert "redis" in services, "test job must have redis service container"
    assert "postgis" in services["postgres"]["image"], "postgres service must use postgis image"
    assert "16" in services["postgres"]["image"], "postgres service must use PostGIS 16"
    assert "redis:7" in services["redis"]["image"], "redis service must use Redis 7"

    # Test commands
    test_commands = [
        step.get("run", "") for step in test_job.get("steps", []) if "run" in step
    ]
    test_str = " ".join(test_commands)
    assert "pytest" in test_str, "CI test job must execute pytest"
    assert "alembic upgrade head" in test_str, "CI test job must run database migrations"

    # Image build job dependencies
    build_job = jobs["build-images"]
    assert "lint-and-typecheck" in build_job.get("needs", [])
    assert "test" in build_job.get("needs", [])


def test_nginx_configuration_and_rate_limits() -> None:
    """Validate Nginx configuration: 60 req/min API rate limit, uncapped tiles, and SSL."""
    nginx_path = Path("infra/nginx/nginx.conf")
    assert nginx_path.exists(), "infra/nginx/nginx.conf must exist"

    content = nginx_path.read_text()

    # Rate limiting zone: 60 req/min for API per SPEC
    assert "limit_req_zone $binary_remote_addr zone=api_limit:10m rate=60r/m;" in content, (
        "Nginx must configure 60 req/min rate limit zone"
    )
    assert "limit_req_status 429;" in content, "Nginx must return HTTP 429 on rate limit exceeded"

    # Vector tiles endpoint: UNCAPPED per SPEC
    # Extract location /v1/tiles/ block
    tiles_match = re.search(r"location\s+/v1/tiles/\s*\{([^}]+)\}", content)
    assert tiles_match is not None, "Nginx must define location /v1/tiles/"
    tiles_block = tiles_match.group(1)
    assert "limit_req" not in tiles_block, (
        "SPEC requirement: vector tiles must be UNCAPPED (no limit_req directive)"
    )

    # API endpoints: RATE LIMITED
    api_match = re.search(r"location\s+/v1/\s*\{([^}]+)\}", content)
    assert api_match is not None, "Nginx must define location /v1/"
    api_block = api_match.group(1)
    assert "limit_req zone=api_limit" in api_block, "API location must enforce api_limit"

    # Let's Encrypt ACME challenge location and SSL configuration
    assert "location /.well-known/acme-challenge/" in content
    assert "ssl_certificate /etc/letsencrypt/live/bantaypondo.ph/fullchain.pem;" in content
    assert "ssl_certificate_key /etc/letsencrypt/live/bantaypondo.ph/privkey.pem;" in content
    assert "TLSv1.2 TLSv1.3" in content

    # Structured JSON log format
    assert "log_format json_combined" in content
    assert "$request_id" in content

    # Request ID and proxy header propagation
    assert "proxy_set_header X-Request-ID $request_id;" in content


def test_production_docker_compose_and_dockerfiles() -> None:
    """Validate production Docker Compose specification and non-root Dockerfiles."""
    compose_path = Path("infra/docker-compose.prod.yml")
    assert compose_path.exists(), "infra/docker-compose.prod.yml must exist"

    with compose_path.open() as f:
        compose_yaml = yaml.safe_load(f)

    services = compose_yaml["services"]
    expected_services = ["db", "redis", "api", "nginx", "certbot", "prometheus"]
    for svc in expected_services:
        assert svc in services, f"Production compose must define service: {svc}"

    # Database uses PostGIS 16 and has healthcheck
    assert "postgis/postgis:16" in services["db"]["image"]
    assert "healthcheck" in services["db"]

    # Redis has healthcheck and appendonly
    assert "redis:7" in services["redis"]["image"]
    assert "healthcheck" in services["redis"]
    assert "--appendonly yes" in services["redis"].get("command", "")

    # API depends on DB and Redis health
    assert services["api"]["depends_on"]["db"]["condition"] == "service_healthy"
    assert services["api"]["depends_on"]["redis"]["condition"] == "service_healthy"
    assert "healthcheck" in services["api"]

    # Nginx exposes ports 80 and 443
    nginx_ports = services["nginx"].get("ports", [])
    assert "80:80" in nginx_ports
    assert "443:443" in nginx_ports

    # Root docker-compose.prod.yml exists and includes infra
    root_prod = Path("docker-compose.prod.yml")
    assert root_prod.exists()

    # Non-root user in Dockerfiles
    dockerfile_api = Path("infra/Dockerfile.api").read_text()
    assert "USER appuser" in dockerfile_api
    assert "10001" in dockerfile_api

    dockerfile_pipeline = Path("infra/Dockerfile.pipeline").read_text()
    assert "USER appuser" in dockerfile_pipeline
    assert "10001" in dockerfile_pipeline


def test_prometheus_scrape_configuration() -> None:
    """Validate Prometheus scraping configuration for Bantay Pondo API."""
    prom_path = Path("infra/prometheus/prometheus.yml")
    assert prom_path.exists(), "infra/prometheus/prometheus.yml must exist"

    with prom_path.open() as f:
        prom_yaml = yaml.safe_load(f)

    scrape_configs = prom_yaml.get("scrape_configs", [])
    assert len(scrape_configs) >= 1
    api_job = next(
        (job for job in scrape_configs if job.get("job_name") == "bantay_pondo_api"), None
    )
    assert api_job is not None, "Prometheus must have job bantay_pondo_api"
    assert api_job.get("metrics_path") == "/metrics"
    targets = api_job.get("static_configs", [{}])[0].get("targets", [])
    assert "api:8000" in targets


def test_deployment_scripts_and_env_templates() -> None:
    """Validate Let's Encrypt bootstrap and single-EC2 deploy scripts."""
    init_ssl = Path("infra/scripts/init-letsencrypt.sh")
    deploy_sh = Path("infra/scripts/deploy.sh")
    env_example = Path(".env.prod.example")

    assert init_ssl.exists()
    assert os.access(init_ssl, os.X_OK), "init-letsencrypt.sh must be executable"

    assert deploy_sh.exists()
    assert os.access(deploy_sh, os.X_OK), "deploy.sh must be executable"

    assert env_example.exists()
    content = env_example.read_text()
    assert "POSTGRES_PASSWORD" in content
    assert "REDIS_PASSWORD" in content
    assert "DATA_VERSION" in content


# ---------------------------------------------------------------------------
# Observability Tests: JSON Logs, Request ID, Prometheus Metrics
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_observability_request_id_and_headers(
    async_client: httpx.AsyncClient,
) -> None:
    """Assert X-Request-ID propagation and auto-generation on requests."""
    # Custom incoming Request ID
    custom_id = "bp-custom-trace-12345"
    resp = await async_client.get("/healthz", headers={"X-Request-ID": custom_id})
    assert resp.status_code == 200
    assert resp.headers.get("X-Request-ID") == custom_id

    # Auto-generated Request ID when not provided
    resp_auto = await async_client.get("/healthz")
    assert resp_auto.status_code == 200
    generated_id = resp_auto.headers.get("X-Request-ID")
    assert generated_id is not None
    assert len(generated_id) >= 10


@pytest.mark.asyncio
async def test_observability_prometheus_metrics_exposition(
    async_client: httpx.AsyncClient,
) -> None:
    """Assert /metrics endpoint returns standard Prometheus text format with request counts."""
    # Make a few calls to register metrics
    await async_client.get("/healthz")
    await async_client.get("/readyz")

    resp = await async_client.get("/metrics")
    assert resp.status_code == 200
    assert "text/plain" in resp.headers["content-type"]

    body = resp.text
    assert "# HELP http_requests_total" in body
    assert "# TYPE http_requests_total counter" in body
    assert "http_requests_total{" in body
    assert "# HELP http_request_duration_seconds" in body
    assert "# TYPE http_request_duration_seconds gauge" in body
    assert "http_request_duration_seconds{" in body


# ---------------------------------------------------------------------------
# API Contract Tests: Asserting Every Endpoint's Response Shape
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_contract_health_and_ready_endpoints(
    async_client: httpx.AsyncClient,
) -> None:
    """Assert /healthz and /readyz contract shapes and status indicators."""
    # Healthz
    h_resp = await async_client.get("/healthz")
    assert h_resp.status_code == 200
    assert "X-Request-ID" in h_resp.headers
    h_data = h_resp.json()
    assert h_data == {"status": "ok"}

    # Readyz
    r_resp = await async_client.get("/readyz")
    assert r_resp.status_code == 200
    assert "X-Request-ID" in r_resp.headers
    r_data = r_resp.json()
    assert r_data["status"] == "ready"
    assert r_data["database"] == "healthy"
    assert r_data["redis"] == "healthy"
    assert "data_version" in r_data


@pytest.mark.asyncio
async def test_contract_openapi_and_docs(
    async_client: httpx.AsyncClient,
) -> None:
    """Assert OpenAPI schema auto-generation contains all endpoints defined in SPEC."""
    resp = await async_client.get("/openapi.json")
    assert resp.status_code == 200
    openapi = resp.json()

    assert openapi["openapi"].startswith("3.")
    paths = openapi["paths"]

    expected_paths = [
        "/healthz",
        "/readyz",
        "/metrics",
        "/v1/localities/search",
        "/v1/localities/{psgc_code}",
        "/v1/localities/{psgc_code}/projects",
        "/v1/localities/compare",
        "/v1/projects/{contract_id}",
        "/v1/contractors/{contractor_id}",
        "/v1/rankings",
        "/v1/tiles/{layer}/{z}/{x}/{y}.mvt",
        "/v1/meta/datasets",
    ]
    for path in expected_paths:
        assert path in paths, f"OpenAPI schema must declare route: {path}"


@pytest.mark.asyncio
async def test_contract_localities_search(
    async_client: httpx.AsyncClient,
) -> None:
    """Assert GET /v1/localities/search response shape."""
    resp = await async_client.get("/v1/localities/search?q=Tuguegarao&level=municipality")
    assert resp.status_code == 200
    assert "X-Data-Version" in resp.headers
    assert "X-Request-ID" in resp.headers
    data = resp.json()

    assert "data_version" in data
    assert data["query"] == "Tuguegarao"
    assert data["total"] >= 1
    assert "items" in data
    assert isinstance(data["items"], list)

    first = data["items"][0]
    expected_fields = ["psgc_code", "name", "level", "parent_psgc", "similarity"]
    for field in expected_fields:
        assert field in first, f"Search result item missing field: {field}"


@pytest.mark.asyncio
async def test_contract_localities_profile(
    async_client: httpx.AsyncClient,
) -> None:
    """Assert GET /v1/localities/{psgc_code} response shape."""
    # Tuguegarao City (0201529000)
    resp = await async_client.get("/v1/localities/0201529000")
    assert resp.status_code == 200
    assert "X-Data-Version" in resp.headers
    assert "X-Request-ID" in resp.headers
    data = resp.json()

    assert "data_version" in data
    assert "profile" in data
    profile = data["profile"]
    expected_profile_fields = [
        "psgc_code",
        "name",
        "level",
        "parent_psgc",
        "land_area_sqkm",
        "population",
    ]
    for field in expected_profile_fields:
        assert field in profile, f"Locality profile missing field: {field}"
    assert "metrics" in data
    assert isinstance(data["metrics"], list)
    assert "officials" in data
    assert isinstance(data["officials"], list)


@pytest.mark.asyncio
async def test_contract_localities_projects_paginated(
    async_client: httpx.AsyncClient,
) -> None:
    """Assert GET /v1/localities/{psgc_code}/projects response shape."""
    # Maraiging barangay (1600205010)
    resp = await async_client.get("/v1/localities/1600205010/projects?page=1&page_size=10")
    assert resp.status_code == 200
    assert "X-Data-Version" in resp.headers
    assert "X-Request-ID" in resp.headers
    data = resp.json()

    assert "data_version" in data
    assert data["page"] == 1
    assert data["page_size"] == 10
    assert data["total"] >= 1
    assert "items" in data
    assert isinstance(data["items"], list)
    assert len(data["items"]) >= 1


@pytest.mark.asyncio
async def test_contract_localities_compare(
    async_client: httpx.AsyncClient,
) -> None:
    """Assert GET /v1/localities/compare response shape."""
    # Tuguegarao City (0201509000) vs Adams (0102801000)
    resp = await async_client.get("/v1/localities/compare?a=0201509000&b=0102801000")
    assert resp.status_code == 200
    assert "X-Data-Version" in resp.headers
    assert "X-Request-ID" in resp.headers
    data = resp.json()

    assert "data_version" in data
    assert "locality_a" in data
    assert "locality_b" in data
    assert "deltas" in data


@pytest.mark.asyncio
async def test_contract_projects_detail_with_flags(
    async_client: httpx.AsyncClient,
) -> None:
    """Assert GET /v1/projects/{contract_id} response shape."""
    resp = await async_client.get("/v1/projects/21NA0052")
    assert resp.status_code == 200
    assert "X-Data-Version" in resp.headers
    assert "X-Request-ID" in resp.headers
    data = resp.json()

    assert "data_version" in data
    assert data["contract_id"] == "21NA0052"
    assert "flags" in data
    assert isinstance(data["flags"], list)
    assert "related_awards" in data
    assert isinstance(data["related_awards"], list)


@pytest.mark.asyncio
async def test_contract_contractor_profile_and_hhi(
    async_client: httpx.AsyncClient,
) -> None:
    """Assert GET /v1/contractors/{id} response shape."""
    resp = await async_client.get("/v1/contractors/1")
    assert resp.status_code == 200
    assert "X-Data-Version" in resp.headers
    assert "X-Request-ID" in resp.headers
    data = resp.json()

    assert "data_version" in data
    assert "profile" in data
    assert "normalized_name" in data["profile"]
    assert "contracts" in data
    assert "district_concentration" in data
    assert "hhi" in data["district_concentration"]


@pytest.mark.asyncio
async def test_contract_rankings_leaderboard(
    async_client: httpx.AsyncClient,
) -> None:
    """Assert GET /v1/rankings response shape."""
    resp = await async_client.get(
        "/v1/rankings?metric=mismatch_score&level=municipality&limit=10&order=asc"
    )
    assert resp.status_code == 200
    assert "X-Data-Version" in resp.headers
    assert "X-Request-ID" in resp.headers
    data = resp.json()

    assert "data_version" in data
    assert data["metric"] == "mismatch_score"
    assert data["level"] == "municipality"
    assert "items" in data
    assert isinstance(data["items"], list)
    if data["items"]:
        first = data["items"][0]
        assert "rank" in first
        assert "mismatch_score" in first
        assert "national_percentile" in first


@pytest.mark.asyncio
async def test_contract_vector_tiles(
    async_client: httpx.AsyncClient,
) -> None:
    """Assert GET /v1/tiles/{layer}/{z}/{x}/{y}.mvt vector tile response shape."""
    layers = ["projects", "hazards", "boundaries"]
    for layer in layers:
        resp = await async_client.get(f"/v1/tiles/{layer}/5/28/14.mvt")
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "application/vnd.mapbox-vector-tile"
        assert "X-Data-Version" in resp.headers
        assert "X-Request-ID" in resp.headers
        assert isinstance(resp.content, bytes)


@pytest.mark.asyncio
async def test_contract_meta_datasets(
    async_client: httpx.AsyncClient,
) -> None:
    """Assert GET /v1/meta/datasets response shape."""
    resp = await async_client.get("/v1/meta/datasets")
    assert resp.status_code == 200
    assert "X-Data-Version" in resp.headers
    assert "X-Request-ID" in resp.headers
    data = resp.json()

    assert "data_version" in data
    assert "datasets" in data
    assert isinstance(data["datasets"], list)
    assert len(data["datasets"]) >= 1

    first = data["datasets"][0]
    for field in ["dataset_name", "source_url", "description", "record_count", "sha256"]:
        assert field in first, f"Dataset metadata missing field: {field}"


# ---------------------------------------------------------------------------
# Fixture Dataset Conservation Invariant Test
# ---------------------------------------------------------------------------


def test_fixture_row_counts_preservation(db_conn: psycopg.Connection[Any]) -> None:
    """Assert preservation of exact fixture row counts for boundaries and hazards."""
    with db_conn.cursor() as cur:
        cur.execute("SELECT count(*) FROM regions;")
        r_row = cur.fetchone()
        assert r_row is not None and r_row[0] == 17

        cur.execute("SELECT count(*) FROM provinces;")
        p_row = cur.fetchone()
        assert p_row is not None and p_row[0] == 82

        cur.execute("SELECT count(*) FROM municipalities;")
        m_row = cur.fetchone()
        assert m_row is not None and m_row[0] == 1620

        cur.execute("SELECT count(*) FROM barangays;")
        b_row = cur.fetchone()
        assert b_row is not None and b_row[0] == 41803

        cur.execute("SELECT count(*) FROM hazard_zones;")
        h_row = cur.fetchone()
        assert h_row is not None and h_row[0] == 9
