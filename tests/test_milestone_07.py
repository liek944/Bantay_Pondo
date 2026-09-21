"""Verification tests for Milestone 7: Vector Tiles (PostGIS ST_AsMVT & Redis caching)."""

import time
from typing import Any

import httpx
import psycopg
import pytest
import redis

MVT_MEDIA_TYPE = "application/vnd.mapbox-vector-tile"


@pytest.mark.asyncio
async def test_openapi_tile_route_registered(async_client: httpx.AsyncClient) -> None:
    """SPEC requirement: OpenAPI schema includes vector tile endpoint."""
    resp = await async_client.get("/openapi.json")
    assert resp.status_code == 200
    schema = resp.json()
    paths = schema["paths"]
    assert "/v1/tiles/{layer}/{z}/{x}/{y}.mvt" in paths


@pytest.mark.asyncio
async def test_invalid_tile_layer_404(async_client: httpx.AsyncClient) -> None:
    """SPEC requirement: Return 404 for unknown tile layer."""
    resp = await async_client.get("/v1/tiles/unknown_layer/10/856/470.mvt")
    assert resp.status_code == 404
    data = resp.json()
    assert "Unsupported tile layer" in data["detail"]
    assert "data_version" in data


@pytest.mark.asyncio
async def test_invalid_tile_coordinates_400(async_client: httpx.AsyncClient) -> None:
    """Validate tile coordinates bounds checking (400 Bad Request)."""
    # Negative zoom
    resp1 = await async_client.get("/v1/tiles/projects/-1/0/0.mvt")
    assert resp1.status_code == 400
    assert "Zoom level -1 is out of bounds" in resp1.json()["detail"]

    # Excessive zoom
    resp2 = await async_client.get("/v1/tiles/projects/25/0/0.mvt")
    assert resp2.status_code == 400
    assert "Zoom level 25 is out of bounds" in resp2.json()["detail"]

    # X coordinate out of bounds (at z=2, valid x is 0..3)
    resp3 = await async_client.get("/v1/tiles/projects/2/4/0.mvt")
    assert resp3.status_code == 400
    assert "Tile x coordinate 4 is out of bounds" in resp3.json()["detail"]

    # Y coordinate out of bounds
    resp4 = await async_client.get("/v1/tiles/projects/2/0/5.mvt")
    assert resp4.status_code == 400
    assert "Tile y coordinate 5 is out of bounds" in resp4.json()["detail"]


@pytest.mark.asyncio
async def test_projects_tile_generation_and_caching(
    async_client: httpx.AsyncClient,
    redis_client: redis.Redis,
) -> None:
    """SPEC requirement: GET /v1/tiles/projects/{z}/{x}/{y}.mvt with caching."""
    # Manila area tile at z=10: x=856, y=470
    url = "/v1/tiles/projects/10/856/470.mvt"

    # Invalidate any preexisting cache key for this tile
    for key in redis_client.scan_iter("bantay:*:tiles:projects:10:856:470:*"):
        redis_client.delete(key)

    # First request: Cache MISS
    resp1 = await async_client.get(url)
    assert resp1.status_code == 200
    assert MVT_MEDIA_TYPE in resp1.headers["content-type"]
    assert resp1.headers["x-cache"] == "MISS"
    assert "x-data-version" in resp1.headers
    content1 = resp1.content
    assert len(content1) > 0

    # Second request: Cache HIT with identical payload
    resp2 = await async_client.get(url)
    assert resp2.status_code == 200
    assert MVT_MEDIA_TYPE in resp2.headers["content-type"]
    assert resp2.headers["x-cache"] == "HIT"
    assert resp2.headers["x-data-version"] == resp1.headers["x-data-version"]
    assert resp2.content == content1


@pytest.mark.asyncio
async def test_hazards_tile_generation(async_client: httpx.AsyncClient) -> None:
    """SPEC requirement: GET /v1/tiles/hazards/{z}/{x}/{y}.mvt."""
    # Northern Luzon / Batanes at z=6: x=53, y=28
    url = "/v1/tiles/hazards/6/53/28.mvt"
    resp = await async_client.get(url)
    assert resp.status_code == 200
    assert MVT_MEDIA_TYPE in resp.headers["content-type"]
    assert "x-data-version" in resp.headers
    assert len(resp.content) > 0


@pytest.mark.asyncio
async def test_boundaries_tile_hierarchy(async_client: httpx.AsyncClient) -> None:
    """SPEC requirement: GET /v1/tiles/boundaries/{z}/{x}/{y}.mvt across zoom levels."""
    # Regions at low zoom (z=5)
    resp_reg = await async_client.get("/v1/tiles/boundaries/5/26/14.mvt")
    assert resp_reg.status_code == 200
    assert MVT_MEDIA_TYPE in resp_reg.headers["content-type"]
    assert len(resp_reg.content) > 0

    # Municipalities at zoom 10
    resp_mun = await async_client.get("/v1/tiles/boundaries/10/856/470.mvt")
    assert resp_mun.status_code == 200
    assert MVT_MEDIA_TYPE in resp_mun.headers["content-type"]
    assert len(resp_mun.content) > 0

    # Barangays at zoom 13
    resp_bgy = await async_client.get("/v1/tiles/boundaries/13/6849/3760.mvt")
    assert resp_bgy.status_code == 200
    assert MVT_MEDIA_TYPE in resp_bgy.headers["content-type"]
    assert len(resp_bgy.content) > 0


@pytest.mark.asyncio
async def test_boundaries_tile_level_override(async_client: httpx.AsyncClient) -> None:
    """Boundaries tile with explicit ?level= query parameter."""
    resp = await async_client.get("/v1/tiles/boundaries/10/856/470.mvt?level=provinces")
    assert resp.status_code == 200
    assert MVT_MEDIA_TYPE in resp.headers["content-type"]
    assert len(resp.content) > 0

    # Invalid level parameter returns 400
    resp_invalid = await async_client.get("/v1/tiles/boundaries/10/856/470.mvt?level=galaxy")
    assert resp_invalid.status_code == 400


@pytest.mark.asyncio
async def test_boundary_alias_layers(async_client: httpx.AsyncClient) -> None:
    """Direct boundary tier sub-layer queries."""
    for sublayer in ("regions", "provinces", "municipalities"):
        resp = await async_client.get(f"/v1/tiles/{sublayer}/10/856/470.mvt")
        assert resp.status_code == 200
        assert MVT_MEDIA_TYPE in resp.headers["content-type"]


@pytest.mark.asyncio
async def test_empty_tile_returns_200(async_client: httpx.AsyncClient) -> None:
    """Querying an area outside the Philippines returns empty tile with 200 OK."""
    # Point in the middle of the Pacific where no features exist
    resp = await async_client.get("/v1/tiles/projects/10/0/0.mvt")
    assert resp.status_code == 200
    assert MVT_MEDIA_TYPE in resp.headers["content-type"]
    assert len(resp.content) == 0


@pytest.mark.asyncio
async def test_warm_tile_latency_under_150ms(async_client: httpx.AsyncClient) -> None:
    """SPEC Non-functional requirement: Tiles under 150ms on warm cache."""
    url = "/v1/tiles/projects/10/856/470.mvt"

    # Pre-warm
    warmup = await async_client.get(url)
    assert warmup.status_code == 200

    # Measure 5 requests
    durations: list[float] = []
    for _ in range(5):
        t0 = time.perf_counter()
        resp = await async_client.get(url)
        t1 = time.perf_counter()
        assert resp.status_code == 200
        assert resp.headers["x-cache"] == "HIT"
        durations.append((t1 - t0) * 1000.0)

    avg_ms = sum(durations) / len(durations)
    max_ms = max(durations)
    # Assert maximum warm latency is well under 150ms
    assert max_ms < 150.0, f"Max warm tile latency {max_ms:.2f}ms exceeded 150ms SLA"
    assert avg_ms < 50.0, f"Average warm tile latency {avg_ms:.2f}ms exceeded 50ms"


def test_fixture_row_counts_preserved(db_conn: psycopg.Connection[Any]) -> None:
    """Hard rule: Baseline fixture row counts must be preserved."""
    expected = {
        "regions": 17,
        "provinces": 82,
        "municipalities": 1620,
        "barangays": 41803,
        "hazard_zones": 9,
    }
    with db_conn.cursor() as cur:
        for table, expected_count in expected.items():
            cur.execute(f"SELECT count(*) FROM {table}")  # noqa: S608
            actual_count = cur.fetchone()[0]
            assert actual_count == expected_count, (
                f"Row count mismatch for {table}: expected {expected_count}, got {actual_count}"
            )
