"""Verification tests for Milestone 6: API endpoints (no tiles yet)."""

from decimal import Decimal
from typing import Any

import httpx
import psycopg
import pytest

from api.services.projects import evaluate_project_flags


@pytest.mark.asyncio
async def test_healthz_endpoint(async_client: httpx.AsyncClient) -> None:
    """SPEC requirement: GET /healthz liveness probe."""
    resp = await async_client.get("/healthz")
    assert resp.status_code == 200
    data = resp.json()
    assert data == {"status": "ok"}


@pytest.mark.asyncio
async def test_readyz_endpoint(async_client: httpx.AsyncClient) -> None:
    """SPEC requirement: GET /readyz readiness probe with DB and Redis health."""
    resp = await async_client.get("/readyz")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ready"
    assert data["database"] == "healthy"
    assert data["redis"] == "healthy"
    assert "data_version" in data


@pytest.mark.asyncio
async def test_metrics_prometheus_endpoint(async_client: httpx.AsyncClient) -> None:
    """SPEC requirement: Prometheus metrics at /metrics."""
    # First issue a request to populate metrics
    await async_client.get("/healthz")
    resp = await async_client.get("/metrics")
    assert resp.status_code == 200
    assert "text/plain" in resp.headers["content-type"]
    text = resp.text
    assert "http_requests_total" in text
    assert "http_request_duration_seconds" in text


@pytest.mark.asyncio
async def test_openapi_schema_and_docs(async_client: httpx.AsyncClient) -> None:
    """SPEC requirement: OpenAPI schema auto-generated, served at /docs."""
    docs_resp = await async_client.get("/docs")
    assert docs_resp.status_code == 200

    openapi_resp = await async_client.get("/openapi.json")
    assert openapi_resp.status_code == 200
    schema = openapi_resp.json()
    assert schema["info"]["title"] == "Bantay Pondo API"
    paths = schema["paths"]
    assert "/v1/localities/search" in paths
    assert "/v1/localities/{psgc_code}" in paths
    assert "/v1/localities/{psgc_code}/projects" in paths
    assert "/v1/localities/compare" in paths
    assert "/v1/projects/{contract_id}" in paths
    assert "/v1/contractors/{contractor_id}" in paths
    assert "/v1/rankings" in paths
    assert "/v1/meta/datasets" in paths


@pytest.mark.asyncio
async def test_locality_search_typeahead(async_client: httpx.AsyncClient) -> None:
    """SPEC requirement: GET /v1/localities/search?q=&level= typeahead, trigram-backed."""
    resp = await async_client.get("/v1/localities/search?q=Tuguegarao&level=municipality")
    assert resp.status_code == 200
    data = resp.json()
    assert data["query"] == "Tuguegarao"
    assert data["total"] >= 1
    assert "data_version" in data

    match = next((item for item in data["items"] if "Tuguegarao" in item["name"]), None)
    assert match is not None
    assert match["psgc_code"] == "0201529000"
    assert match["level"] == "municipality"
    assert match["similarity"] is not None and match["similarity"] > 0


@pytest.mark.asyncio
async def test_locality_profile_endpoint(async_client: httpx.AsyncClient) -> None:
    """SPEC requirement: GET /v1/localities/{psgc_code} profile + metrics + officials."""
    # Tuguegarao City
    resp = await async_client.get("/v1/localities/0201529000")
    assert resp.status_code == 200
    data = resp.json()
    assert "data_version" in data

    profile = data["profile"]
    assert profile["psgc_code"] == "0201529000"
    assert "Tuguegarao" in profile["name"]
    assert profile["level"] == "municipality"

    metrics = data["metrics"]
    assert isinstance(metrics, list)
    if metrics:
        m = metrics[0]
        assert "mismatch_score" in m
        assert "raw_ratio" in m
        assert "hazard_exposure_pct" in m
        assert "total_spend_php" in m

    officials = data["officials"]
    assert isinstance(officials, list)


@pytest.mark.asyncio
async def test_locality_profile_not_found(async_client: httpx.AsyncClient) -> None:
    """Non-existent locality returns 404 with data_version."""
    resp = await async_client.get("/v1/localities/9999999999")
    assert resp.status_code == 404
    data = resp.json()
    assert "not found" in data["detail"].lower()
    assert "data_version" in data


@pytest.mark.asyncio
async def test_locality_projects_paginated_and_filtered(
    async_client: httpx.AsyncClient,
) -> None:
    """SPEC requirement: GET /v1/localities/{psgc_code}/projects paginated and filterable."""
    # Maraiging barangay (1600205010) has known project 21NA0052
    resp = await async_client.get("/v1/localities/1600205010/projects?page=1&page_size=10")
    assert resp.status_code == 200
    data = resp.json()
    assert "data_version" in data
    assert data["page"] == 1
    assert data["page_size"] == 10
    assert data["total"] >= 1
    assert len(data["items"]) >= 1

    contract_ids = [item["contract_id"] for item in data["items"]]
    assert "21NA0052" in contract_ids
    assert data["items"][0]["psgc_code"] == "1600205010"
    assert "budget_php" in data["items"][0]

    # Test filtering by min_budget
    resp_filtered = await async_client.get(
        "/v1/localities/1600205010/projects?min_budget=50000000"
    )
    assert resp_filtered.status_code == 200
    data_filtered = resp_filtered.json()
    assert data_filtered["total"] == 0


@pytest.mark.asyncio
async def test_locality_compare_endpoint(async_client: httpx.AsyncClient) -> None:
    """SPEC requirement: GET /v1/localities/compare?a=&b= side-by-side metrics."""
    # Tuguegarao City (0201509000) vs Adams (0102801000)
    resp = await async_client.get("/v1/localities/compare?a=0201509000&b=0102801000")
    assert resp.status_code == 200
    data = resp.json()
    assert "data_version" in data
    assert data["locality_a"]["profile"]["psgc_code"] == "0201509000"
    assert data["locality_b"]["profile"]["psgc_code"] == "0102801000"
    assert "deltas" in data


@pytest.mark.asyncio
async def test_project_detail_and_flags_endpoint(
    async_client: httpx.AsyncClient,
) -> None:
    """SPEC requirement: GET /v1/projects/{contract_id} detail + flags + related awards."""
    resp = await async_client.get("/v1/projects/21NA0052")
    assert resp.status_code == 200
    data = resp.json()
    assert "data_version" in data
    assert data["contract_id"] == "21NA0052"
    assert data["psgc_code"] == "1600205010"
    assert "flags" in data
    assert isinstance(data["flags"], list)
    assert "related_awards" in data
    assert isinstance(data["related_awards"], list)

    # 404 on unknown contract
    resp_404 = await async_client.get("/v1/projects/NONEXISTENT_9999")
    assert resp_404.status_code == 404
    assert "data_version" in resp_404.json()


@pytest.mark.asyncio
async def test_project_flags_evaluation_pure_logic() -> None:
    """Verify rule-based project flag evaluation logic."""
    # Test Cost overrun > 15%
    overrun_proj: dict[str, Any] = {
        "contract_id": "FLAG_TEST_01",
        "budget_php": Decimal("1000000.00"),
        "contract_cost_php": Decimal("1200000.00"),  # 20% overrun
        "physical_progress_pct": Decimal("50.0"),
    }
    flags = await evaluate_project_flags(overrun_proj)
    flag_codes = [f.code for f in flags]
    assert "COST_OVERRUN_15PCT" in flag_codes
    cost_flag = next(f for f in flags if f.code == "COST_OVERRUN_15PCT")
    assert "exceeds" in cost_flag.message
    assert cost_flag.severity == "warning"


@pytest.mark.asyncio
async def test_contractor_profile_and_hhi(
    db_conn: psycopg.Connection[Any],
    async_client: httpx.AsyncClient,
) -> None:
    """SPEC requirement: GET /v1/contractors/{id} profile, contracts, district HHI."""
    # Insert a temporary contractor for testing HHI calculation
    with db_conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO contractors (
                normalized_name, raw_names, address, total_contracts, total_value_php
            )
            VALUES (
                'ALPHA BUILDERS CORP',
                ARRAY['Alpha Builders Corp', 'Alpha Builders Inc'],
                'Manila',
                2,
                10000000.00
            )
            ON CONFLICT (normalized_name) DO UPDATE SET total_contracts = 2
            RETURNING id
            """
        )
        row = cur.fetchone()
        assert row is not None
        contractor_id = int(row[0])
    db_conn.commit()

    resp = await async_client.get(f"/v1/contractors/{contractor_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["profile"]["normalized_name"] == "ALPHA BUILDERS CORP"
    assert "district_concentration" in data
    hhi_data = data["district_concentration"]
    assert "hhi" in hhi_data
    assert "normalized_hhi" in hhi_data
    assert "interpretation" in hhi_data
    assert "data_version" in data


@pytest.mark.asyncio
async def test_rankings_leaderboard_endpoint(async_client: httpx.AsyncClient) -> None:
    """SPEC requirement: GET /v1/rankings?metric=&level=&limit= leaderboards."""
    resp = await async_client.get(
        "/v1/rankings?metric=mismatch_score&level=municipality&limit=10&order=asc"
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["metric"] == "mismatch_score"
    assert data["level"] == "municipality"
    assert data["total"] <= 10
    assert "data_version" in data
    assert len(data["items"]) > 0

    first = data["items"][0]
    assert first["rank"] == 1
    assert "mismatch_score" in first
    assert "national_percentile" in first


@pytest.mark.asyncio
async def test_meta_datasets_endpoint(async_client: httpx.AsyncClient) -> None:
    """SPEC requirement: GET /v1/meta/datasets source provenance and last refresh."""
    resp = await async_client.get("/v1/meta/datasets")
    assert resp.status_code == 200
    data = resp.json()
    assert "data_version" in data
    datasets = data["datasets"]
    assert len(datasets) >= 4

    names = [d["dataset_name"] for d in datasets]
    assert "DPWH Infrastructure Projects" in names
    assert "Project NOAH Hazard Maps" in names
    assert "PSGC Administrative Boundaries" in names
    assert "PhilGEPS Procurement Awards" in names

    dpwh = next(d for d in datasets if "DPWH" in d["dataset_name"])
    assert dpwh["record_count"] >= 1000
    assert "huggingface.co" in dpwh["source_url"]


@pytest.mark.asyncio
async def test_caching_hit_and_miss(async_client: httpx.AsyncClient) -> None:
    """SPEC requirement: Response caching in Redis with X-Cache headers."""
    # First request: Cache MISS
    resp1 = await async_client.get("/v1/meta/datasets")
    assert resp1.status_code == 200
    assert resp1.headers.get("X-Cache") in ("MISS", "HIT")
    data_ver = resp1.headers.get("X-Data-Version")
    assert data_ver is not None

    # Second request: Cache HIT
    resp2 = await async_client.get("/v1/meta/datasets")
    assert resp2.status_code == 200
    assert resp2.headers.get("X-Cache") == "HIT"
    assert resp2.headers.get("X-Data-Version") == data_ver
    assert resp1.json() == resp2.json()


@pytest.mark.asyncio
async def test_request_id_tracing_middleware(async_client: httpx.AsyncClient) -> None:
    """SPEC requirement: Structured JSON logs and request IDs."""
    custom_id = "test-req-trace-12345"
    resp = await async_client.get("/healthz", headers={"X-Request-ID": custom_id})
    assert resp.status_code == 200
    assert resp.headers.get("X-Request-ID") == custom_id

    # Auto-generated request ID when not supplied
    resp_auto = await async_client.get("/healthz")
    assert resp_auto.status_code == 200
    assert resp_auto.headers.get("X-Request-ID") is not None


def test_baseline_fixture_counts_preserved(db_conn: psycopg.Connection[Any]) -> None:
    """Definition of Done: Row-count assertions hold on fixture dataset."""
    expected_counts = {
        "regions": 17,
        "provinces": 82,
        "municipalities": 1620,
        "barangays": 41803,
        "hazard_zones": 9,
    }
    with db_conn.cursor() as cur:
        for table, expected in expected_counts.items():
            cur.execute(f"SELECT COUNT(*) FROM {table}")
            row = cur.fetchone()
            assert row is not None
            assert (
                row[0] == expected
            ), f"Table '{table}' row count changed: expected {expected}, found {row[0]}"
