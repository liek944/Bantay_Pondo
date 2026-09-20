"""Verification tests for Milestone 2: Schema migrations and spatial indexes."""

from pathlib import Path
from typing import Any

import psycopg
from alembic.config import Config
from alembic.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine

from api.config import Settings


def test_alembic_current_revision_is_head(settings: Settings) -> None:
    """SPEC requirement: Alembic migrations managed and database at head."""
    root = Path(__file__).resolve().parent.parent
    ini_path = root / "alembic.ini"
    config = Config(str(ini_path))
    script = ScriptDirectory.from_config(config)
    head_rev = script.get_current_head()
    assert head_rev is not None, "No head revision found in Alembic scripts"

    engine = create_engine(settings.database_url)
    with engine.connect() as connection:
        context = MigrationContext.configure(connection)
        current_rev = context.get_current_revision()
        assert current_rev == head_rev, (
            f"Database revision '{current_rev}' does not match Alembic head '{head_rev}'"
        )


def test_required_tables_exist(db_conn: psycopg.Connection[Any]) -> None:
    """SPEC requirement: All required core and pipeline tables exist in database."""
    expected_tables = {
        "regions",
        "provinces",
        "municipalities",
        "barangays",
        "hazard_zones",
        "contractors",
        "projects",
        "procurement_awards",
        "officials",
        "locality_metrics",
        "project_reviews",
        "rejects",
        "data_versions",
    }
    with db_conn.cursor() as cur:
        cur.execute(
            """
            SELECT tablename
            FROM pg_tables
            WHERE schemaname = 'public';
            """
        )
        existing_tables = {row[0] for row in cur.fetchall()}
        missing = expected_tables - existing_tables
        assert not missing, f"Missing required tables in public schema: {missing}"


def test_spatial_geometry_columns_and_srid(db_conn: psycopg.Connection[Any]) -> None:
    """SPEC requirement: Geometry columns have correct type and SRID 4326."""
    expected_geoms = {
        "regions": ("geom", "MULTIPOLYGON", 4326),
        "provinces": ("geom", "MULTIPOLYGON", 4326),
        "municipalities": ("geom", "MULTIPOLYGON", 4326),
        "barangays": ("geom", "MULTIPOLYGON", 4326),
        "hazard_zones": ("geom", "MULTIPOLYGON", 4326),
        "projects": ("geom", "POINT", 4326),
    }
    with db_conn.cursor() as cur:
        for table, (col, geom_type, srid) in expected_geoms.items():
            cur.execute(
                """
                SELECT f_geometry_column, type, srid
                FROM geometry_columns
                WHERE f_table_schema = 'public'
                  AND f_table_name = %s
                  AND f_geometry_column = %s;
                """,
                (table, col),
            )
            row = cur.fetchone()
            assert row is not None, f"Geometry metadata missing for {table}.{col}"
            actual_type = str(row[1]).upper()
            actual_srid = int(row[2])
            assert actual_type == geom_type, (
                f"Expected geometry type {geom_type} for {table}.{col}, got {actual_type}"
            )
            assert actual_srid == srid, (
                f"Expected SRID {srid} for {table}.{col}, got {actual_srid}"
            )


def test_spatial_indexes_gist_exist(db_conn: psycopg.Connection[Any]) -> None:
    """SPEC requirement: GIST spatial index on every geom column."""
    spatial_tables = [
        "regions",
        "provinces",
        "municipalities",
        "barangays",
        "hazard_zones",
        "projects",
    ]
    with db_conn.cursor() as cur:
        for table in spatial_tables:
            cur.execute(
                """
                SELECT indexname, indexdef
                FROM pg_indexes
                WHERE schemaname = 'public'
                  AND tablename = %s
                  AND indexdef ILIKE '%%USING gist%%geom%%';
                """,
                (table,),
            )
            rows = cur.fetchall()
            assert len(rows) > 0, f"Missing GIST spatial index on {table}.geom"


def test_brin_index_on_projects_ingested_at(db_conn: psycopg.Connection[Any]) -> None:
    """SPEC requirement: BRIN index on ingested_at in projects table."""
    with db_conn.cursor() as cur:
        cur.execute(
            """
            SELECT indexname, indexdef
            FROM pg_indexes
            WHERE schemaname = 'public'
              AND tablename = 'projects'
              AND indexdef ILIKE '%%USING brin%%ingested_at%%';
            """
        )
        rows = cur.fetchall()
        assert len(rows) > 0, "Missing BRIN index on projects.ingested_at"


def test_composite_btree_on_locality_metrics(db_conn: psycopg.Connection[Any]) -> None:
    """SPEC requirement: Composite btree on (psgc_code, year) in locality_metrics."""
    with db_conn.cursor() as cur:
        cur.execute(
            """
            SELECT indexname, indexdef
            FROM pg_indexes
            WHERE schemaname = 'public'
              AND tablename = 'locality_metrics'
              AND indexdef ILIKE '%%(psgc_code, year)%%';
            """
        )
        rows = cur.fetchall()
        assert len(rows) > 0, "Missing composite btree index on locality_metrics(psgc_code, year)"


def test_trigram_index_on_contractors(db_conn: psycopg.Connection[Any]) -> None:
    """SPEC requirement: Contractor fuzzy-matching trigram index."""
    with db_conn.cursor() as cur:
        cur.execute(
            """
            SELECT indexname, indexdef
            FROM pg_indexes
            WHERE schemaname = 'public'
              AND tablename = 'contractors'
              AND indexdef ILIKE '%%gin_trgm_ops%%';
            """
        )
        rows = cur.fetchall()
        assert len(rows) > 0, (
            "Missing GIN trigram index on contractors.normalized_name"
        )


def test_foreign_key_constraints(db_conn: psycopg.Connection[Any]) -> None:
    """SPEC requirement: Foreign keys on projects, procurement awards, and provinces."""
    expected_fks = {
        ("projects", "contractor_id", "contractors", "id"),
        ("procurement_awards", "contractor_id", "contractors", "id"),
        ("provinces", "parent_psgc", "regions", "psgc_code"),
    }
    with db_conn.cursor() as cur:
        cur.execute(
            """
            SELECT
                tc.table_name,
                kcu.column_name,
                ccu.table_name AS foreign_table_name,
                ccu.column_name AS foreign_column_name
            FROM information_schema.table_constraints AS tc
            JOIN information_schema.key_column_usage AS kcu
              ON tc.constraint_name = kcu.constraint_name
              AND tc.table_schema = kcu.table_schema
            JOIN information_schema.constraint_column_usage AS ccu
              ON ccu.constraint_name = tc.constraint_name
              AND ccu.table_schema = tc.table_schema
            WHERE tc.constraint_type = 'FOREIGN KEY'
              AND tc.table_schema = 'public';
            """
        )
        actual_fks = set(cur.fetchall())
        for expected in expected_fks:
            assert expected in actual_fks, f"Missing foreign key constraint: {expected}"


def test_fixture_row_count_assertions(db_conn: psycopg.Connection[Any]) -> None:
    """Definition of Done: Row-count assertions hold on fixture dataset."""
    expected_counts = {
        "regions": 17,
        "provinces": 82,
        "municipalities": 1620,
        "barangays": 41803,
        "hazard_zones": 9,
    }
    with db_conn.cursor() as cur:
        for table, expected_count in expected_counts.items():
            cur.execute(f"SELECT count(*) FROM {table};")  # noqa: S608
            row = cur.fetchone()
            assert row is not None
            actual_count = row[0]
            assert actual_count == expected_count, (
                f"Row count mismatch for {table}: expected {expected_count}, got {actual_count}"
            )


def test_postgis_spatial_query_operations(db_conn: psycopg.Connection[Any]) -> None:
    """Verify PostGIS spatial queries operate efficiently on indexed tables."""
    with db_conn.cursor() as cur:
        # Test spatial intersection between barangay and point
        cur.execute(
            """
            SELECT b.psgc_code, b.name
            FROM barangays b
            WHERE ST_Intersects(
                b.geom,
                ST_SetSRID(ST_MakePoint(120.9842, 14.5995), 4326)
            )
            LIMIT 1;
            """
        )
        row = cur.fetchone()
        assert row is not None, "Spatial intersection query returned no results for Manila point"
        assert len(row[0]) > 0
        assert len(row[1]) > 0

        # Verify ST_Area on regions table
        cur.execute("SELECT name, ST_Area(geom) FROM regions LIMIT 1;")
        area_row = cur.fetchone()
        assert area_row is not None
        assert area_row[1] > 0.0
