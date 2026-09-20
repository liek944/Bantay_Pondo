"""Verification tests for Milestone 3: Ingestion for PSGC boundaries and NOAH hazards."""

import hashlib
import json
import tempfile
from pathlib import Path
from typing import Any

import psycopg

from db.session import get_raw_conninfo
from pipeline.stages.fetch import compute_sha256, fetch_file
from pipeline.stages.ingest_noah import normalize_to_multipolygon as noah_normalize
from pipeline.stages.ingest_psgc import (
    ingest_geojson_boundaries,
    normalize_to_multipolygon,
    record_reject,
)


def test_compute_sha256_and_fetch_manifest(tmp_path: Path) -> None:
    """Verify SHA256 checksum calculation and caching manifest behavior."""
    test_file = tmp_path / "sample.txt"
    test_file.write_bytes(b"Bantay Pondo Test Data Payload")

    expected_hash = hashlib.sha256(b"Bantay Pondo Test Data Payload").hexdigest()
    actual_hash = compute_sha256(test_file)
    assert actual_hash == expected_hash, f"Hash mismatch: {actual_hash} != {expected_hash}"

    # Test manifest caching logic
    manifest_dir = tmp_path / "raw_cache"
    manifest_dir.mkdir(parents=True, exist_ok=True)
    cached_file = manifest_dir / "data.txt"
    cached_file.write_bytes(b"Cached Content")
    cached_hash = hashlib.sha256(b"Cached Content").hexdigest()

    manifest_file = manifest_dir / "manifest.json"
    manifest_data = {
        "data.txt": {
            "url": "https://example.com/data.txt",
            "sha256": cached_hash,
            "size_bytes": cached_file.stat().st_size,
        }
    }
    manifest_file.write_text(json.dumps(manifest_data), encoding="utf-8")

    # When fetching an unchanged file that already exists in manifest
    result = fetch_file(
        url="https://example.com/data.txt",
        target_dir=manifest_dir,
        filename="data.txt",
        force_download=False,
    )
    assert result["cached"] is True
    assert result["sha256"] == cached_hash


def test_geometry_normalization_utilities() -> None:
    """Verify geometry normalization handles valid polygons and rejects corrupt geometries."""
    # Simple polygon
    polygon_geojson: dict[str, Any] = {
        "type": "Polygon",
        "coordinates": [
            [
                [120.0, 14.0],
                [121.0, 14.0],
                [121.0, 15.0],
                [120.0, 15.0],
                [120.0, 14.0],
            ]
        ],
    }
    normalized = normalize_to_multipolygon(polygon_geojson)
    assert normalized is not None
    assert normalized.geom_type == "MultiPolygon"
    assert normalized.is_valid

    # Corrupt geometry dictionary
    corrupt_geom: dict[str, Any] = {"type": "Polygon", "coordinates": []}
    assert normalize_to_multipolygon(corrupt_geom) is None
    assert noah_normalize(None) is None


def test_psgc_boundary_row_counts(db_conn: psycopg.Connection[Any]) -> None:
    """SPEC requirement: Row-count assertions hold on PSGC administrative boundaries."""
    expected_counts = {
        "regions": 17,
        "provinces": 82,
        "municipalities": 1620,
        "barangays": 41803,
    }
    with db_conn.cursor() as cur:
        for table, expected_count in expected_counts.items():
            cur.execute(f"SELECT count(*) FROM {table};")  # noqa: S608
            row = cur.fetchone()
            assert row is not None
            actual_count = int(row[0])
            assert actual_count == expected_count, (
                f"Row count mismatch for {table}: expected {expected_count}, got {actual_count}"
            )


def test_tuguegarao_city_present_and_valid(db_conn: psycopg.Connection[Any]) -> None:
    """Assert Tuguegarao City (Cagayan) is ingested with valid geometry and positive land area."""
    with db_conn.cursor() as cur:
        cur.execute(
            """
            SELECT psgc_code, name, land_area_sqkm, ST_IsValid(geom)
            FROM municipalities
            WHERE name ILIKE '%Tuguegarao%';
            """
        )
        row = cur.fetchone()
        assert row is not None, "Tuguegarao City not found in municipalities table"
        assert "Tuguegarao" in str(row[1])
        assert row[2] is not None and float(row[2]) > 0.0, "Land area must be positive"
        assert row[3] is True, "Tuguegarao geometry must be valid PostGIS MultiPolygon"


def test_noah_hazard_zones_counts_and_types(db_conn: psycopg.Connection[Any]) -> None:
    """SPEC requirement: Project NOAH hazard zones ingested across flood, landslide, storm surge."""
    with db_conn.cursor() as cur:
        cur.execute("SELECT count(*) FROM hazard_zones;")
        total_row = cur.fetchone()
        assert total_row is not None
        assert int(total_row[0]) == 9, f"Expected 9 hazard zones, got {total_row[0]}"

        cur.execute("SELECT DISTINCT hazard_type::text, severity_level FROM hazard_zones;")
        rows = cur.fetchall()
        hazard_types = {row[0] for row in rows}
        severity_levels = {int(row[1]) for row in rows}

        assert hazard_types == {"flood", "landslide", "storm_surge"}
        assert severity_levels == {1, 2, 3}


def test_quarantine_rejects_on_malformed_input(db_conn: psycopg.Connection[Any]) -> None:
    """AGENTS.md rule: Never drop rows silently. Failed parses go to rejects table."""
    test_reason = "Test malformed geometry rejection"
    test_payload: dict[str, Any] = {"test_id": 99999, "bad_field": "corrupted"}

    record_reject(db_conn, "test_harness", test_payload, test_reason)

    with db_conn.cursor() as cur:
        cur.execute(
            """
            SELECT source_dataset, raw_row, failure_reason, created_at
            FROM rejects
            WHERE source_dataset = 'test_harness' AND failure_reason = %s;
            """,
            (test_reason,),
        )
        row = cur.fetchone()
        assert row is not None, "Failed parse was not quarantined to rejects table"
        assert row[0] == "test_harness"
        assert row[2] == test_reason
        assert row[3] is not None


def test_idempotent_ingestion_preserves_counts() -> None:
    """SPEC requirement: Ingestion stages are idempotent and re-runnable."""
    sample_geojson = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {
                    "psgc_code": "0100000000",
                    "psgc_name": "Region I (Ilocos Region)",
                    "AREA_SQKM": 12307.35,
                },
                "geometry": {
                    "type": "MultiPolygon",
                    "coordinates": [
                        [
                            [
                                [120.0, 16.0],
                                [120.5, 16.0],
                                [120.5, 16.5],
                                [120.0, 16.5],
                                [120.0, 16.0],
                            ]
                        ]
                    ],
                },
            }
        ],
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".geojson", delete=False) as f:
        json.dump(sample_geojson, f)
        temp_path = Path(f.name)

    try:
        with psycopg.connect(get_raw_conninfo()) as conn:
            # Running ingestion on single region upserts cleanly without duplicating
            count_first = ingest_geojson_boundaries(conn, temp_path, "regions")
            count_second = ingest_geojson_boundaries(conn, temp_path, "regions")
            assert count_first == 17
            assert count_second == 17
    finally:
        temp_path.unlink(missing_ok=True)
