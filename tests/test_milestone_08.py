"""Verification tests for Milestone 8: Contractor dedupe, procurement join, and risk flags."""

import datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import httpx
import polars as pl
import psycopg
import pytest

from api.services.projects import evaluate_project_flags
from pipeline.stages.dedupe_contractors import (
    compute_trigram_similarity,
    dedupe_and_upsert_contractors,
    link_projects_to_contractors,
    normalize_contractor_name,
    update_contractor_aggregated_metrics,
)
from pipeline.stages.ingest_procurement import (
    ingest_philgeps_awards,
    load_psgc_province_map,
    match_psgc_code,
    parse_and_normalize_award,
)


def test_contractor_name_normalization() -> None:
    """Verify contractor name normalization per SPEC: uppercase, suffixes, parentheticals."""
    # Strip legal suffixes: INC, CORP, CO, ENTERPRISES, CONSTRUCTION
    assert normalize_contractor_name("Alpha Construction Inc.") == "ALPHA"
    assert normalize_contractor_name("Beta Builders Corp.") == "BETA BUILDERS"
    assert normalize_contractor_name("Gamma Trading Company") == "GAMMA TRADING"
    assert normalize_contractor_name("Delta Enterprises") == "DELTA"
    assert normalize_contractor_name("Epsilon Construction") == "EPSILON"

    # Strip registration codes in parentheses
    assert normalize_contractor_name("PIV CONSTRUCTION (16102)") == "PIV"
    assert (
        normalize_contractor_name("ST. MATTHEW GEN. CONTRACTOR & DEV CORP. ([REVOKED] 40908)")
        == "ST. MATTHEW GEN. CONTRACTOR & DEV"
    )

    # Strip former name parentheticals
    assert (
        normalize_contractor_name(
            "AQUALINE CONSTRUCTION CORPORATION (FORMERLY: AQUALINE CONST) (11555)"
        )
        == "AQUALINE"
    )

    # Joint venture splitting and trimming
    jv_raw = "TRYST BUILDERS ENTERPRISES (31164) / F.B. BANTALES ENGINEERING CONSTRUCTION (31045)"
    assert normalize_contractor_name(jv_raw) == "TRYST BUILDERS / F.B. BANTALES ENGINEERING"

    # Whitespace and empty strings
    assert normalize_contractor_name("   ") == ""
    assert normalize_contractor_name(None) == ""
    assert normalize_contractor_name("  MEGA   BUILDERS   INC.  ") == "MEGA BUILDERS"


def test_trigram_similarity_math_parity_with_pg_trgm(
    db_conn: psycopg.Connection[Any],
) -> None:
    """Assert Python trigram similarity matches PostgreSQL pg_trgm similarity() exactly."""
    test_pairs = [
        ("ALPHA BUILDERS", "ALPHA BUILDER"),
        ("MEGA CORP", "MEGGA CORP"),
        ("RAMONA", "RAMONA"),
        ("BANTAY PONDO", "BANTAY PNDO"),
        ("NORTHERN BUILDERS", "NORTHERN TRADING"),
    ]

    with db_conn.cursor() as cur:
        for s1, s2 in test_pairs:
            cur.execute("SELECT similarity(%s, %s);", (s1, s2))
            row = cur.fetchone()
            assert row is not None
            pg_val = float(row[0])
            py_val = compute_trigram_similarity(s1, s2)
            assert abs(pg_val - py_val) < 0.0001, (
                f"Mismatch for ({s1!r}, {s2!r}): PG={pg_val}, PY={py_val}"
            )


def test_contractor_dedupe_clustering(db_conn: psycopg.Connection[Any]) -> None:
    """Verify fuzzy matching with similarity > 0.9 merges entities and preserves raw aliases."""
    raw_variants = [
        "HORIZON PACIFIC BUILDERS CORP. (12345)",
        "HORIZON PACIFIC BUILDERS INC.",
        "HORIZON PACIFIC BUILDERS (FORMERLY: HORIZON) (12345)",
        "COMPLETELY DIFFERENT BUILDERS INC.",
    ]

    raw_to_id = dedupe_and_upsert_contractors(db_conn, raw_variants)

    # All three horizon variants should resolve to the same canonical ID
    id1 = raw_to_id["HORIZON PACIFIC BUILDERS CORP. (12345)"]
    id2 = raw_to_id["HORIZON PACIFIC BUILDERS INC."]
    id3 = raw_to_id["HORIZON PACIFIC BUILDERS (FORMERLY: HORIZON) (12345)"]
    id_diff = raw_to_id["COMPLETELY DIFFERENT BUILDERS INC."]

    assert id1 == id2 == id3
    assert id1 != id_diff

    with db_conn.cursor() as cur:
        cur.execute("SELECT normalized_name, raw_names FROM contractors WHERE id = %s;", (id1,))
        row = cur.fetchone()
        assert row is not None
        assert row[0] == "HORIZON PACIFIC BUILDERS"
        raw_list = list(row[1])
        # Assert raw variants are preserved
        assert "HORIZON PACIFIC BUILDERS CORP. (12345)" in raw_list
        assert "HORIZON PACIFIC BUILDERS INC." in raw_list


def test_contractor_project_linking_and_metrics(db_conn: psycopg.Connection[Any]) -> None:
    """Verify linking projects updates projects.contractor_id and materializes metrics."""
    with db_conn.cursor() as cur:
        # Create test contractor
        cur.execute(
            """
            INSERT INTO contractors (
                normalized_name, raw_names, address, total_contracts, total_value_php
            )
            VALUES ('METRO INFRA', ARRAY['Metro Infra Corp'], 'Quezon City', 0, 0)
            ON CONFLICT (normalized_name) DO UPDATE SET total_contracts = 0
            RETURNING id;
            """
        )
        c_row = cur.fetchone()
        assert c_row is not None
        c_id = int(c_row[0])

        # Create two test projects
        cur.execute(
            """
            INSERT INTO projects (
                contract_id, title, implementing_office, budget_php, contract_cost_php,
                start_date, target_completion_date, physical_progress_pct
            ) VALUES
            (
                'TEST_PRJ_LINK_01', 'School A', 'Manila DEO', 5000000.0, 5200000.0,
                '2021-01-10', '2021-12-10', 100.0
            ),
            (
                'TEST_PRJ_LINK_02', 'Road B', 'Manila DEO', 3000000.0, NULL,
                '2022-03-15', '2022-09-15', 80.0
            )
            ON CONFLICT (contract_id) DO UPDATE SET budget_php = EXCLUDED.budget_php;
            """
        )
    db_conn.commit()

    raw_to_id = {"Metro Infra Corp": c_id}
    pairs = [("TEST_PRJ_LINK_01", "Metro Infra Corp"), ("TEST_PRJ_LINK_02", "Metro Infra Corp")]

    linked = link_projects_to_contractors(db_conn, pairs, raw_to_id)
    assert linked == 2

    # Update aggregated metrics
    update_contractor_aggregated_metrics(db_conn)

    with db_conn.cursor() as cur:
        # Verify projects.contractor_id
        cur.execute(
            "SELECT contractor_id FROM projects WHERE contract_id = 'TEST_PRJ_LINK_01';"
        )
        row = cur.fetchone()
        assert row is not None
        assert row[0] == c_id

        # Verify contractor metrics
        cur.execute(
            "SELECT total_contracts, total_value_php, first_seen FROM contractors WHERE id = %s;",
            (c_id,),
        )
        stats = cur.fetchone()
        assert stats is not None
        assert stats[0] >= 2
        # Total value: 5,200,000 (cost) + 3,000,000 (budget fallback) = 8,200,000
        assert Decimal(str(stats[1])) >= Decimal("8200000.00")
        assert stats[2] == datetime.date(2021, 1, 10)


def test_philgeps_awards_normalization_and_rejects(
    db_conn: psycopg.Connection[Any],
) -> None:
    """Verify PhilGEPS row normalization and quarantine of malformed rows into rejects."""
    valid_row: dict[str, Any] = {
        "reference_id": "PHIL-2024-001",
        "contract_no": "CN-2024-01",
        "award_title": "Concreting of Farm-to-Market Road",
        "notice_title": "ITB Farm Road",
        "awardee_name": "ACME BUILDERS CORP.",
        "organization_name": "DPWH AGUSAN DEL NORTE",
        "area_of_delivery": "Agusan Del Norte",
        "contract_amount": 14500000.50,
        "award_date": "2024-05-20",
    }

    norm, err = parse_and_normalize_award(valid_row)
    assert err is None
    assert norm is not None
    assert norm["reference_id"] == "PHIL-2024-001"
    assert norm["title"] == "Concreting of Farm-to-Market Road"
    assert norm["award_amount_php"] == Decimal("14500000.50")
    assert norm["award_date"] == datetime.date(2024, 5, 20)
    assert norm["procuring_entity"] == "DPWH AGUSAN DEL NORTE"
    assert norm["awardee_name"] == "ACME BUILDERS CORP."

    # Test malformed row: missing title
    malformed_row: dict[str, Any] = {
        "reference_id": "BAD-001",
        "award_title": "",
        "notice_title": None,
        "contract_amount": 1000.0,
    }
    bad_norm, bad_err = parse_and_normalize_award(malformed_row)
    assert bad_norm is None
    assert bad_err is not None
    assert "Missing" in bad_err


def test_philgeps_awards_ingestion_and_reconciliation(
    db_conn: psycopg.Connection[Any],
    tmp_path: Path,
) -> None:
    """Verify PhilGEPS ingestion creates awards, links contractors, and reconciles DPWH cost."""
    # Ensure a matching project exists with contract_cost_php NULL
    with db_conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO projects (
                contract_id, title, budget_php, contract_cost_php, start_date
            ) VALUES (
                '24GF00199', 'Road Rehabilitation Project', 10000000.00, NULL, '2024-01-01'
            )
            ON CONFLICT (contract_id) DO UPDATE SET contract_cost_php = NULL;
            """
        )
    db_conn.commit()

    # Create temporary parquet fixture with 3 awards (2 valid, 1 malformed)
    test_awards = pl.DataFrame(
        {
            "reference_id": ["REF-001", "24GF00199", "BAD-ROW"],
            "contract_no": ["CN-001", "24GF00199", None],
            "award_title": ["Supply of Materials", "Construction Work for 24GF00199", ""],
            "notice_title": ["Notice 1", "Notice 2", None],
            "awardee_name": ["VANGUARD SUPPLIES", "ZENITH BUILDERS", "NONE"],
            "organization_name": ["LGU Tuguegarao", "DPWH REGION II", "LGU"],
            "area_of_delivery": ["Cagayan", "Cagayan", "Nowhere"],
            "contract_amount": [500000.0, 9850000.0, None],
            "award_date": ["2024-03-01", "2024-04-15", None],
        }
    )
    fixture_path = tmp_path / "test_philgeps.parquet"
    test_awards.write_parquet(fixture_path)

    stats = ingest_philgeps_awards(db_conn, fixture_path)

    assert stats["total_in"] == 3
    assert stats["inserted"] == 2
    assert stats["rejects"] == 1
    assert stats["projects_updated"] >= 1

    # Verify DPWH project contract_cost_php was reconciled
    with db_conn.cursor() as cur:
        cur.execute(
            "SELECT contract_cost_php FROM projects WHERE contract_id = '24GF00199';"
        )
        cost_row = cur.fetchone()
        assert cost_row is not None
        assert Decimal(str(cost_row[0])) == Decimal("9850000.00")

        # Verify contractor was created and linked
        cur.execute(
            """
            SELECT pa.reference_id, pa.contractor_id, c.normalized_name
            FROM procurement_awards pa
            JOIN contractors c ON pa.contractor_id = c.id
            WHERE pa.reference_id = '24GF00199';
            """
        )
        joined_row = cur.fetchone()
        assert joined_row is not None
        assert joined_row[2] == "ZENITH BUILDERS"


def test_load_psgc_province_map_and_matching(db_conn: psycopg.Connection[Any]) -> None:
    """Verify PSGC province and region name matching."""
    prov_map = load_psgc_province_map(db_conn)
    assert len(prov_map) > 0

    # Test matching known province
    cagayan_code = match_psgc_code("Cagayan", prov_map)
    assert cagayan_code is not None

    batanes_code = match_psgc_code("Batanes", prov_map)
    assert batanes_code is not None

    # Unmatched / null handling
    assert match_psgc_code(None, prov_map) is None
    assert match_psgc_code("Unknown Planet", prov_map) is None


@pytest.mark.asyncio
async def test_flag_cost_overrun_15pct() -> None:
    """Verify rule: contract_cost exceeds budget by more than 15%."""
    # 20% overrun -> flag triggered
    proj_overrun: dict[str, Any] = {
        "contract_id": "FLAG_OVERRUN_TEST",
        "budget_php": Decimal("1000000.00"),
        "contract_cost_php": Decimal("1200000.00"),
    }
    flags = await evaluate_project_flags(proj_overrun)
    assert any(f.code == "COST_OVERRUN_15PCT" for f in flags)

    # 10% overrun -> no flag
    proj_normal: dict[str, Any] = {
        "contract_id": "FLAG_NORMAL_TEST",
        "budget_php": Decimal("1000000.00"),
        "contract_cost_php": Decimal("1100000.00"),
    }
    flags_normal = await evaluate_project_flags(proj_normal)
    assert not any(f.code == "COST_OVERRUN_15PCT" for f in flags_normal)


@pytest.mark.asyncio
async def test_flag_delayed_low_progress() -> None:
    """Verify rule: physical_progress below 20% more than 12 months past target completion."""
    overdue_date = datetime.date.today() - datetime.timedelta(days=400)
    recent_date = datetime.date.today() - datetime.timedelta(days=100)

    # Overdue > 12 months and progress 15% -> flag triggered
    proj_delayed: dict[str, Any] = {
        "contract_id": "FLAG_DELAYED_TEST",
        "target_completion_date": overdue_date,
        "physical_progress_pct": Decimal("15.0"),
    }
    flags = await evaluate_project_flags(proj_delayed)
    assert any(f.code == "DELAYED_LOW_PROGRESS" for f in flags)

    # Overdue > 12 months but progress 50% -> no flag
    proj_progressing: dict[str, Any] = {
        "contract_id": "FLAG_PROG_TEST",
        "target_completion_date": overdue_date,
        "physical_progress_pct": Decimal("50.0"),
    }
    assert not any(
        f.code == "DELAYED_LOW_PROGRESS"
        for f in await evaluate_project_flags(proj_progressing)
    )

    # Overdue only 100 days -> no flag
    proj_recent: dict[str, Any] = {
        "contract_id": "FLAG_RECENT_TEST",
        "target_completion_date": recent_date,
        "physical_progress_pct": Decimal("5.0"),
    }
    assert not any(
        f.code == "DELAYED_LOW_PROGRESS" for f in await evaluate_project_flags(proj_recent)
    )


@pytest.mark.asyncio
async def test_flag_district_contractor_concentration_40pct(
    db_conn: psycopg.Connection[Any],
) -> None:
    """Verify rule: contractor holds more than 40% of a district's total contract value."""
    with db_conn.cursor() as cur:
        # Create unique contractor
        cur.execute(
            """
            INSERT INTO contractors (normalized_name, raw_names, total_contracts, total_value_php)
            VALUES ('DOMINANT CONTRACTOR', ARRAY['Dominant Contractor'], 1, 8000000.00)
            ON CONFLICT (normalized_name) DO UPDATE SET total_value_php = 8000000.00
            RETURNING id;
            """
        )
        dom_row = cur.fetchone()
        assert dom_row is not None
        c_dom = int(dom_row[0])

        # Create district projects where dominant contractor holds 8M out of 10M (80%)
        cur.execute(
            """
            INSERT INTO projects (
                contract_id, title, implementing_office, contractor_id, budget_php
            ) VALUES
            ('DOM_PRJ_01', 'Dominant Highway', 'Test District DEO', %s, 8000000.00),
            ('OTHER_PRJ_01', 'Small Culvert', 'Test District DEO', NULL, 2000000.00)
            ON CONFLICT (contract_id) DO UPDATE SET budget_php = EXCLUDED.budget_php;
            """,
            (c_dom,),
        )
    db_conn.commit()

    proj_check: dict[str, Any] = {
        "contract_id": "DOM_PRJ_01",
        "contractor_id": c_dom,
        "implementing_office": "Test District DEO",
    }
    flags = await evaluate_project_flags(proj_check)
    assert any(f.code == "DISTRICT_CONTRACTOR_CONCENTRATION_40PCT" for f in flags)
    flag_item = next(
        f for f in flags if f.code == "DISTRICT_CONTRACTOR_CONCENTRATION_40PCT"
    )
    assert flag_item.details["share_pct"] == 80.0


@pytest.mark.asyncio
async def test_flag_duplicate_description_barangay_year(
    db_conn: psycopg.Connection[Any],
) -> None:
    """Verify rule: duplicate project descriptions within the same barangay and year."""
    with db_conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO projects (
                contract_id, title, description, psgc_code, start_date
            ) VALUES
            ('DUP_PRJ_01', 'FMR Phase 1', 'FARM TO MARKET ROAD', '0201509001', '2021-03-01'),
            ('DUP_PRJ_02', 'FMR Phase 2', 'FARM TO MARKET ROAD', '0201509001', '2021-06-01')
            ON CONFLICT (contract_id) DO UPDATE SET description = EXCLUDED.description;
            """
        )
    db_conn.commit()

    proj_check: dict[str, Any] = {
        "contract_id": "DUP_PRJ_01",
        "description": "farm to market road",
        "psgc_code": "0201509001",
        "start_date": datetime.date(2021, 3, 1),
    }
    flags = await evaluate_project_flags(proj_check)
    assert any(f.code == "DUPLICATE_DESCRIPTION_BARANGAY_YEAR" for f in flags)


@pytest.mark.asyncio
async def test_flag_coordinates_outside_stated_region(
    db_conn: psycopg.Connection[Any],
) -> None:
    """Verify rule: project coordinates fall outside its stated region."""
    # Project with coordinates in Caraga (Region XIII, e.g. 125.57, 9.36)
    # Stated region is Region I (Ilocos, PSGC 0100000000)
    with db_conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO projects (
                contract_id, title, implementing_office, geom, psgc_code
            ) VALUES (
                'SPATIAL_MISMATCH_PRJ', 'Bridge in Caraga', 'Ilocos Norte 1st DEO',
                ST_SetSRID(ST_Point(125.5748, 9.3674), 4326), '1600205010'
            )
            ON CONFLICT (contract_id) DO UPDATE SET geom = EXCLUDED.geom;
            """
        )
    db_conn.commit()

    proj_check: dict[str, Any] = {
        "contract_id": "SPATIAL_MISMATCH_PRJ",
        "implementing_office": "Ilocos Norte 1st DEO",
        "has_geom": True,
        "latitude": 9.3674,
        "longitude": 125.5748,
    }
    flags = await evaluate_project_flags(proj_check)
    assert any(f.code == "COORDINATES_OUTSIDE_REGION" for f in flags)


@pytest.mark.asyncio
async def test_api_project_detail_with_flags_and_related_awards(
    async_client: httpx.AsyncClient,
    db_conn: psycopg.Connection[Any],
) -> None:
    """Verify GET /v1/projects/{contract_id} returns evaluated flags and related awards."""
    # Ensure project and related award exist
    with db_conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO contractors (normalized_name, raw_names)
            VALUES ('SUMMIT BUILDERS', ARRAY['Summit Builders Inc'])
            ON CONFLICT (normalized_name) DO UPDATE SET raw_names = EXCLUDED.raw_names
            RETURNING id;
            """
        )
        summit_row = cur.fetchone()
        assert summit_row is not None
        c_id = int(summit_row[0])

        cur.execute(
            """
            INSERT INTO projects (
                contract_id, title, budget_php, contract_cost_php,
                contractor_id, psgc_code, start_date
            ) VALUES (
                'API_FLAG_PRJ', 'Summit Multi-Purpose Building', 1000000.00, 1300000.00,
                %s, '0201509001', '2022-01-01'
            )
            ON CONFLICT (contract_id) DO UPDATE SET contract_cost_php = 1300000.00;
            """,
            (c_id,),
        )

        cur.execute(
            """
            INSERT INTO procurement_awards (
                reference_id, contractor_id, title, award_amount_php, award_date, procuring_entity
            ) VALUES (
                'AWARD-SUMMIT-01', %s, 'Supply of Steel for API_FLAG_PRJ',
                300000.0, '2022-02-01', 'DPWH'
            );
            """,
            (c_id,),
        )
    db_conn.commit()

    resp = await async_client.get("/v1/projects/API_FLAG_PRJ")
    assert resp.status_code == 200
    data = resp.json()

    assert data["contract_id"] == "API_FLAG_PRJ"
    assert "flags" in data
    assert any(f["code"] == "COST_OVERRUN_15PCT" for f in data["flags"])
    assert "related_awards" in data
    assert len(data["related_awards"]) >= 1
    assert data["related_awards"][0]["reference_id"] == "AWARD-SUMMIT-01"


@pytest.mark.asyncio
async def test_api_contractor_profile_real_contracts_and_hhi(
    async_client: httpx.AsyncClient,
    db_conn: psycopg.Connection[Any],
) -> None:
    """Verify GET /v1/contractors/{id} returns real linked contracts and calculated HHI."""
    with db_conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO contractors (normalized_name, raw_names, address)
            VALUES ('VORTEX CONSTRUCTION', ARRAY['Vortex Construction Corp'], 'Davao City')
            ON CONFLICT (normalized_name) DO UPDATE SET address = 'Davao City'
            RETURNING id;
            """
        )
        vortex_row = cur.fetchone()
        assert vortex_row is not None
        c_id = int(vortex_row[0])

        cur.execute(
            """
            INSERT INTO projects (
                contract_id, title, implementing_office, budget_php, contractor_id
            ) VALUES
            ('VORTEX_01', 'Bridge 1', 'Davao City DEO', 6000000.00, %s),
            ('VORTEX_02', 'Road 2', 'Davao del Sur DEO', 4000000.00, %s)
            ON CONFLICT (contract_id) DO UPDATE SET budget_php = EXCLUDED.budget_php;
            """,
            (c_id, c_id),
        )
    db_conn.commit()

    resp = await async_client.get(f"/v1/contractors/{c_id}")
    assert resp.status_code == 200
    data = resp.json()

    assert data["profile"]["normalized_name"] == "VORTEX CONSTRUCTION"
    assert len(data["contracts"]) >= 2
    assert "district_concentration" in data
    hhi = data["district_concentration"]["hhi"]
    assert hhi > 0
    assert "interpretation" in data["district_concentration"]


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
