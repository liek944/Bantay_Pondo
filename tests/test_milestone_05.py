"""Verification tests for Milestone 5: Scoring job and mismatch score calculation."""

from decimal import Decimal
from typing import Any

import psycopg

from pipeline.stages.score import (
    MAX_RATIO_SENTINEL,
    SEVERITY_WEIGHTS,
    _setup_hazard_exposure_cache,
    compute_and_store_locality_metrics,
    compute_exposure_pct,
    compute_mismatch_score,
)


def test_severity_weights_match_specification() -> None:
    """SPEC requirement: Weight severity levels 1/2/3 as 0.3/0.6/1.0."""
    assert SEVERITY_WEIGHTS[1] == Decimal("0.3")
    assert SEVERITY_WEIGHTS[2] == Decimal("0.6")
    assert SEVERITY_WEIGHTS[3] == Decimal("1.0")


def test_mismatch_score_balanced_allocation() -> None:
    """SPEC requirement: ratio = 1.0 yields mismatch_score = 50.0 (balanced)."""
    raw_ratio, score = compute_mismatch_score(
        actual_share=Decimal("0.05"),
        expected_share=Decimal("0.05"),
    )
    assert raw_ratio == Decimal("1.0000")
    assert score == Decimal("50.0000")


def test_mismatch_score_hand_computed_ratios() -> None:
    """SPEC requirement: mismatch_score = 50 + 50 * tanh(ln(ratio)) with exact math.

    Identities from tanh(ln(r)) = (r^2 - 1) / (r^2 + 1):
    - r = 2.0 -> (4 - 1)/(4 + 1) = 3/5 = 0.6 -> score = 50 + 50*(0.6) = 80.0
    - r = 0.5 -> (0.25 - 1)/(0.25 + 1) = -0.75/1.25 = -0.6 -> score = 50 - 30 = 20.0
    - r = 3.0 -> (9 - 1)/(9 + 1) = 8/10 = 0.8 -> score = 50 + 50*(0.8) = 90.0
    - r = 1/3 -> -0.8 -> score = 50 + 50*(-0.8) = 10.0
    """
    # Ratio = 2.0 (spend double risk share)
    r2, s2 = compute_mismatch_score(Decimal("0.04"), Decimal("0.02"))
    assert r2 == Decimal("2.0000")
    assert s2 == Decimal("80.0000")

    # Ratio = 0.5 (spend half risk share)
    r05, s05 = compute_mismatch_score(Decimal("0.01"), Decimal("0.02"))
    assert r05 == Decimal("0.5000")
    assert s05 == Decimal("20.0000")

    # Ratio = 3.0
    r3, s3 = compute_mismatch_score(Decimal("0.06"), Decimal("0.02"))
    assert r3 == Decimal("3.0000")
    assert s3 == Decimal("90.0000")

    # Ratio = 1/3 (approx 0.3333)
    r_third, s_third = compute_mismatch_score(Decimal("1.0"), Decimal("3.0"))
    assert r_third == Decimal("0.3333")
    assert s_third == Decimal("10.0000")


def test_mismatch_score_underserved_and_overserved_orders_of_magnitude() -> None:
    """SPEC requirement: Below 50 = underserved, Above 50 = spend exceeds risk share."""
    # 10x overserved (ratio = 10) -> tanh(ln(10)) = 99/101 ~ 0.9801 -> score ~ 99.0099
    r_over, s_over = compute_mismatch_score(Decimal("0.10"), Decimal("0.01"))
    assert r_over == Decimal("10.0000")
    assert s_over == Decimal("99.0099")
    assert s_over > Decimal("50.0")

    # 10x underserved (ratio = 0.1) -> tanh(ln(0.1)) = -99/101 ~ -0.9801 -> score ~ 0.9901
    r_under, s_under = compute_mismatch_score(Decimal("0.01"), Decimal("0.10"))
    assert r_under == Decimal("0.1000")
    assert s_under == Decimal("0.9901")
    assert s_under < Decimal("50.0")


def test_mismatch_score_boundary_conditions() -> None:
    """SPEC & robustness: Handle zero spend, zero risk, and both zero safely."""
    # Zero spend, positive risk: maximally underserved
    r_zero_spend, s_zero_spend = compute_mismatch_score(
        actual_share=Decimal("0.00"),
        expected_share=Decimal("0.05"),
    )
    assert r_zero_spend == Decimal("0.0000")
    assert s_zero_spend == Decimal("0.0000")

    # Positive spend, zero risk: spend exceeds risk share, finite ratio sentinel
    r_zero_risk, s_zero_risk = compute_mismatch_score(
        actual_share=Decimal("0.05"),
        expected_share=Decimal("0.00"),
    )
    assert r_zero_risk == MAX_RATIO_SENTINEL
    assert s_zero_risk == Decimal("100.0000")

    # Both zero: balanced
    r_both_zero, s_both_zero = compute_mismatch_score(
        actual_share=Decimal("0.00"),
        expected_share=Decimal("0.00"),
    )
    assert r_both_zero == Decimal("1.0000")
    assert s_both_zero == Decimal("50.0000")


def test_compute_exposure_pct_clamping() -> None:
    """Verify exposure percentage calculation, zero handling, and clamping to 100%."""
    assert compute_exposure_pct(Decimal("0"), Decimal("100")) == Decimal("0.0000")
    assert compute_exposure_pct(Decimal("25.5"), Decimal("100")) == Decimal("25.5000")
    assert compute_exposure_pct(Decimal("120"), Decimal("100")) == Decimal("100.0000")
    assert compute_exposure_pct(Decimal("50"), Decimal("0")) == Decimal("0.0000")


def test_spatial_hazard_exposure_caching(db_conn: psycopg.Connection[Any]) -> None:
    """Assert PostGIS spatial intersection populates exposure cache with valid areas."""
    _setup_hazard_exposure_cache(db_conn)

    with db_conn.cursor() as cur:
        cur.execute(
            """
            SELECT count(*), sum(total_weighted_exposed_sqkm)
            FROM temp_barangay_exposure
            WHERE total_weighted_exposed_sqkm > 0;
            """
        )
        row = cur.fetchone()
        assert row is not None
        assert row[0] > 0, "Expected at least one exposed barangay in fixture dataset"
        assert float(row[1]) > 0.0, "Expected positive exposed square kilometers"

        cur.execute(
            """
            SELECT count(*), sum(total_weighted_exposed_sqkm)
            FROM temp_muni_exposure
            WHERE total_weighted_exposed_sqkm > 0;
            """
        )
        muni_row = cur.fetchone()
        assert muni_row is not None
        assert muni_row[0] > 0, "Expected at least one exposed municipality"
        assert float(muni_row[1]) > 0.0


def test_end_to_end_scoring_job_execution(db_conn: psycopg.Connection[Any]) -> None:
    """Verify complete scoring job execution for year 2021 and column integrity."""
    result = compute_and_store_locality_metrics(
        db_conn,
        years=[2021],
        levels=["municipalities", "barangays"],
    )

    assert result["years_processed"] == [2021]
    assert result["rows_inserted"] > 0
    assert result["total_localities_scored"] > 0
    assert result["total_spend_php"] > Decimal("0")
    assert result["total_weighted_exposed_sqkm"] > Decimal("0")

    with db_conn.cursor() as cur:
        # Check that rows were inserted into locality_metrics
        cur.execute(
            """
            SELECT
                psgc_code,
                year,
                hazard_exposure_pct,
                flood_pct,
                landslide_pct,
                surge_pct,
                population_at_risk,
                total_spend_php,
                spend_per_capita,
                spend_per_exposed_sqkm,
                raw_ratio,
                mismatch_score,
                national_percentile,
                computed_at
            FROM locality_metrics
            WHERE year = 2021
            ORDER BY total_spend_php DESC
            LIMIT 5;
            """
        )
        rows = cur.fetchall()
        assert len(rows) > 0, "locality_metrics should contain scored rows for year 2021"

        for r in rows:
            assert r[1] == 2021
            # Scores and percentiles must be strictly bounded between 0 and 100
            assert Decimal("0.0") <= r[2] <= Decimal("100.0"), f"Invalid hazard: {r[2]}"
            assert Decimal("0.0") <= r[3] <= Decimal("100.0"), f"Invalid flood_pct: {r[3]}"
            assert Decimal("0.0") <= r[4] <= Decimal("100.0"), f"Invalid landslide_pct: {r[4]}"
            assert Decimal("0.0") <= r[5] <= Decimal("100.0"), f"Invalid surge_pct: {r[5]}"
            assert Decimal("0.0") <= r[11] <= Decimal("100.0"), f"Invalid mismatch: {r[11]}"
            assert Decimal("0.0") <= r[12] <= Decimal("100.0"), f"Invalid percentile: {r[12]}"
            assert r[13] is not None, "computed_at timestamp must be populated"


def test_scoring_job_idempotency(db_conn: psycopg.Connection[Any]) -> None:
    """SPEC requirement: Scoring stage is idempotent and re-runnable without duplicates."""
    # First execution
    res1 = compute_and_store_locality_metrics(db_conn, years=[2022], levels=["municipalities"])
    assert res1["rows_inserted"] > 0

    with db_conn.cursor() as cur:
        cur.execute("SELECT count(*) FROM locality_metrics WHERE year = 2022;")
        count1 = cur.fetchone()[0]

    # Second execution
    res2 = compute_and_store_locality_metrics(db_conn, years=[2022], levels=["municipalities"])
    assert res2["rows_inserted"] == res1["rows_inserted"]

    with db_conn.cursor() as cur:
        cur.execute("SELECT count(*) FROM locality_metrics WHERE year = 2022;")
        count2 = cur.fetchone()[0]

    assert count1 == count2, f"Idempotent re-run created duplicate rows: {count1} != {count2}"


def test_baseline_fixture_counts_preserved(db_conn: psycopg.Connection[Any]) -> None:
    """Assert exact baseline boundary and hazard row counts are preserved."""
    with db_conn.cursor() as cur:
        for table, expected_count in [
            ("regions", 17),
            ("provinces", 82),
            ("municipalities", 1620),
            ("barangays", 41803),
            ("hazard_zones", 9),
        ]:
            cur.execute(f"SELECT count(*) FROM {table};")
            actual_count = cur.fetchone()[0]
            assert actual_count == expected_count, (
                f"Row count assertion failed for {table}: "
                f"expected {expected_count}, got {actual_count}"
            )
