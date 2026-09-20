"""Verification tests for Milestone 4: DPWH projects ingestion, spatial join, and review queue."""

import datetime
import tempfile
from pathlib import Path
from typing import Any

import polars as pl
import psycopg

from pipeline.stages.ingest_dpwh import (
    ingest_dpwh_projects,
    parse_and_normalize_project,
)


def test_parse_and_normalize_project_valid() -> None:
    """Verify DPWH raw project normalization, date parsing, and source row hashing."""
    raw_row: dict[str, Any] = {
        "contractId": "21NA0052",
        "description": "CONCRETING OF BRGY. MARAIGING FMR, JABONGA, AGUSAN DEL NORTE",
        "category": "Roads",
        "componentCategories": "Roads",
        "status": "Completed",
        "budget": 11939997.93,
        "amountPaid": 0,
        "progress": 100.0,
        "location": {
            "province": "Agusan del Norte DEO",
            "region": "Region XIII",
        },
        "contractor": "C'ZARLES CONSTRUCTION & SUPPLY",
        "startDate": "2021-07-05",
        "completionDate": "2022-02-27",
        "infraYear": "2021",
        "programName": "Outside Infra",
        "sourceOfFunds": "Outside Infra - GAA 2021 DA FMR",
        "latitude": 9.3674914,
        "longitude": 125.5748542,
        "reportCount": 0,
        "hasSatelliteImage": True,
    }

    norm, err = parse_and_normalize_project(raw_row)
    assert err is None
    assert norm is not None
    assert norm["contract_id"] == "21NA0052"
    assert norm["title"] == raw_row["description"]
    assert norm["implementing_office"] == "Agusan del Norte DEO"
    assert norm["funding_source"] == "Outside Infra - GAA 2021 DA FMR"
    assert norm["budget_php"] == 11939997.93
    assert norm["start_date"] == datetime.date(2021, 7, 5)
    assert norm["target_completion_date"] == datetime.date(2022, 2, 27)
    assert norm["physical_progress_pct"] == 100.0
    assert norm["latitude"] == 9.3674914
    assert norm["longitude"] == 125.5748542
    assert norm["invalid_coord_reason"] is None
    assert len(norm["source_row_hash"]) == 64


def test_parse_and_normalize_project_invalid() -> None:
    """Verify malformed project rows (missing contractId) return rejection reason."""
    bad_row_empty_id: dict[str, Any] = {
        "contractId": "   ",
        "description": "Ghost project",
    }
    norm, err = parse_and_normalize_project(bad_row_empty_id)
    assert norm is None
    assert err is not None
    assert "Missing or empty contractId" in err

    bad_row_none_id: dict[str, Any] = {
        "contractId": None,
        "description": "Ghost project 2",
    }
    norm, err = parse_and_normalize_project(bad_row_none_id)
    assert norm is None
    assert err is not None


def test_spatial_join_resolves_known_barangay(db_conn: psycopg.Connection[Any]) -> None:
    """Assert coordinate in Jabonga resolves to Barangay Maraiging (PSGC 1600205010)."""
    fixture_rows = [
        {
            "contractId": "TEST_GEOCODE_001",
            "description": "MARAIGING FMR ROAD CONCRETING",
            "location": {"province": "Agusan del Norte DEO", "region": "Region XIII"},
            "sourceOfFunds": "GAA 2021",
            "budget": 5000000.0,
            "progress": 100.0,
            "startDate": "2021-01-01",
            "completionDate": "2021-12-31",
            "latitude": 9.3674914,
            "longitude": 125.5748542,
        }
    ]

    with tempfile.NamedTemporaryFile(suffix=".parquet") as tmp:
        df = pl.DataFrame(fixture_rows)
        df.write_parquet(tmp.name)

        stats = ingest_dpwh_projects(db_conn, Path(tmp.name))
        assert stats["total_in"] == 1
        assert stats["geocoded"] == 1
        assert stats["review_queue"] == 0
        assert stats["rejects"] == 0

    with db_conn.cursor() as cur:
        cur.execute(
            """
            SELECT contract_id, psgc_code, ST_AsText(geom)
            FROM projects
            WHERE contract_id = 'TEST_GEOCODE_001';
            """
        )
        row = cur.fetchone()
        assert row is not None
        assert row[0] == "TEST_GEOCODE_001"
        assert row[1] == "1600205010", f"Expected barangay 1600205010, got {row[1]}"
        assert "POINT(125.5748542 9.3674914)" in str(row[2])


def test_missing_coordinates_routed_to_review_queue(
    db_conn: psycopg.Connection[Any],
) -> None:
    """SPEC requirement: Projects with null coordinates go to review queue without silent drops."""
    fixture_rows = [
        {
            "contractId": "TEST_NULL_COORD_002",
            "description": "UNMAPPED INFRASTRUCTURE PROJECT",
            "location": {"province": "Central Office", "region": "NCR"},
            "sourceOfFunds": "GAA 2023",
            "budget": 25000000.0,
            "progress": 50.0,
            "startDate": "2023-01-01",
            "completionDate": "2023-12-31",
            "latitude": None,
            "longitude": None,
        }
    ]

    with tempfile.NamedTemporaryFile(suffix=".parquet") as tmp:
        df = pl.DataFrame(fixture_rows)
        df.write_parquet(tmp.name)

        stats = ingest_dpwh_projects(db_conn, Path(tmp.name))
        assert stats["total_in"] == 1
        assert stats["geocoded"] == 0
        assert stats["review_queue"] == 1
        assert stats["rejects"] == 0

    with db_conn.cursor() as cur:
        # Project must still exist in projects table with psgc_code NULL
        cur.execute(
            """
            SELECT contract_id, psgc_code, geom
            FROM projects
            WHERE contract_id = 'TEST_NULL_COORD_002';
            """
        )
        p_row = cur.fetchone()
        assert p_row is not None
        assert p_row[1] is None
        assert p_row[2] is None

        # Project must be queued in project_reviews
        cur.execute(
            """
            SELECT contract_id, reason, latitude, longitude
            FROM project_reviews
            WHERE contract_id = 'TEST_NULL_COORD_002';
            """
        )
        r_row = cur.fetchone()
        assert r_row is not None
        assert r_row[0] == "TEST_NULL_COORD_002"
        assert "Missing coordinates" in r_row[1]
        assert r_row[2] is None
        assert r_row[3] is None


def test_coordinates_outside_all_boundaries_routed_to_review_queue(
    db_conn: psycopg.Connection[Any],
) -> None:
    """SPEC requirement: Coordinates falling outside all barangay polygons go to review queue."""
    fixture_rows = [
        {
            "contractId": "TEST_OFFSHORE_003",
            "description": "OFFSHORE DEEP OCEAN BUOY OR RIG",
            "location": {"province": "Regional Office", "region": "Region VIII"},
            "sourceOfFunds": "GAA 2024",
            "budget": 80000000.0,
            "progress": 10.0,
            "startDate": "2024-01-01",
            "completionDate": "2024-12-31",
            # Point located far out in the Philippine Sea
            "latitude": 10.0,
            "longitude": 135.0,
        }
    ]

    with tempfile.NamedTemporaryFile(suffix=".parquet") as tmp:
        df = pl.DataFrame(fixture_rows)
        df.write_parquet(tmp.name)

        stats = ingest_dpwh_projects(db_conn, Path(tmp.name))
        assert stats["total_in"] == 1
        assert stats["geocoded"] == 0
        assert stats["review_queue"] == 1
        assert stats["rejects"] == 0

    with db_conn.cursor() as cur:
        # Project must still exist in projects table with psgc_code NULL and geom intact
        cur.execute(
            """
            SELECT contract_id, psgc_code, ST_AsText(geom)
            FROM projects
            WHERE contract_id = 'TEST_OFFSHORE_003';
            """
        )
        p_row = cur.fetchone()
        assert p_row is not None
        assert p_row[1] is None
        assert "POINT(135 10)" in str(p_row[2])

        # Project must be queued in project_reviews with boundary reason
        cur.execute(
            """
            SELECT contract_id, reason, latitude, longitude
            FROM project_reviews
            WHERE contract_id = 'TEST_OFFSHORE_003';
            """
        )
        r_row = cur.fetchone()
        assert r_row is not None
        assert r_row[0] == "TEST_OFFSHORE_003"
        assert "outside all barangay boundaries" in r_row[1]
        assert float(r_row[2]) == 10.0
        assert float(r_row[3]) == 135.0


def test_malformed_project_quarantined_to_rejects(
    db_conn: psycopg.Connection[Any],
) -> None:
    """AGENTS.md hard rule: Never drop rows silently. Failed parses go to rejects table."""
    fixture_rows = [
        {
            "contractId": "",  # Malformed: empty contract ID
            "description": "Ghost infrastructure project",
            "budget": 100000.0,
        }
    ]

    with tempfile.NamedTemporaryFile(suffix=".parquet") as tmp:
        df = pl.DataFrame(fixture_rows)
        df.write_parquet(tmp.name)

        stats = ingest_dpwh_projects(db_conn, Path(tmp.name))
        assert stats["total_in"] == 1
        assert stats["geocoded"] == 0
        assert stats["review_queue"] == 0
        assert stats["rejects"] == 1

    with db_conn.cursor() as cur:
        cur.execute(
            """
            SELECT source_dataset, failure_reason, created_at
            FROM rejects
            WHERE source_dataset = 'dpwh_projects'
            ORDER BY id DESC
            LIMIT 1;
            """
        )
        row = cur.fetchone()
        assert row is not None
        assert row[0] == "dpwh_projects"
        assert "Missing or empty contractId" in row[1]


def test_idempotent_project_upsert_preserves_count(
    db_conn: psycopg.Connection[Any],
) -> None:
    """SPEC requirement: Ingestion stages are idempotent and re-runnable."""
    fixture_rows = [
        {
            "contractId": "TEST_IDEMPOTENT_004",
            "description": "IDEMPOTENCY TEST PROJECT",
            "location": {"province": "Agusan del Norte DEO"},
            "sourceOfFunds": "GAA 2022",
            "budget": 12000000.0,
            "progress": 30.0,
            "startDate": "2022-01-01",
            "completionDate": "2022-12-31",
            "latitude": 9.3674914,
            "longitude": 125.5748542,
        }
    ]

    with tempfile.NamedTemporaryFile(suffix=".parquet") as tmp:
        df = pl.DataFrame(fixture_rows)
        df.write_parquet(tmp.name)

        # First run
        stats_1 = ingest_dpwh_projects(db_conn, Path(tmp.name))
        assert stats_1["upserted"] == 1

        # Second run with modified progress to verify update
        fixture_rows[0]["progress"] = 75.0
        df_updated = pl.DataFrame(fixture_rows)
        df_updated.write_parquet(tmp.name)

        stats_2 = ingest_dpwh_projects(db_conn, Path(tmp.name))
        assert stats_2["upserted"] == 1

    with db_conn.cursor() as cur:
        cur.execute(
            """
            SELECT count(*), physical_progress_pct
            FROM projects
            WHERE contract_id = 'TEST_IDEMPOTENT_004'
            GROUP BY physical_progress_pct;
            """
        )
        rows = cur.fetchall()
        assert len(rows) == 1
        assert rows[0][0] == 1
        assert float(rows[0][1]) == 75.0


def test_batch_accounting_balance_holds(db_conn: psycopg.Connection[Any]) -> None:
    """Assert total_in == geocoded + review_queue + rejects across a mixed batch."""
    fixture_rows = [
        # 1: Valid coordinate matching barangay
        {
            "contractId": "BATCH_01",
            "description": "Valid point",
            "latitude": 9.3674914,
            "longitude": 125.5748542,
        },
        # 2: Missing coordinate
        {
            "contractId": "BATCH_02",
            "description": "Missing coords",
            "latitude": None,
            "longitude": None,
        },
        # 3: Coordinate outside all polygons
        {
            "contractId": "BATCH_03",
            "description": "Offshore point",
            "latitude": 10.0,
            "longitude": 135.0,
        },
        # 4: Corrupt / empty ID
        {
            "contractId": "",
            "description": "Malformed row",
            "latitude": 9.0,
            "longitude": 125.0,
        },
    ]

    with tempfile.NamedTemporaryFile(suffix=".parquet") as tmp:
        df = pl.DataFrame(fixture_rows)
        df.write_parquet(tmp.name)

        stats = ingest_dpwh_projects(db_conn, Path(tmp.name))

        assert stats["total_in"] == 4
        assert stats["geocoded"] == 1
        assert stats["review_queue"] == 2
        assert stats["rejects"] == 1
        assert stats["total_in"] == (
            stats["geocoded"] + stats["review_queue"] + stats["rejects"]
        )
