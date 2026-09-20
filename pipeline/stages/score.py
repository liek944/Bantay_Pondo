"""Bantay Pondo scoring job: computes mismatch scores and risk metrics per locality.

Implements the exact mathematical specification from SPEC.md:
- Hazard exposure area: severity-weighted intersection of locality boundary
  and Project NOAH polygons.
  Severity weights: level 1 = 0.3, level 2 = 0.6, level 3 = 1.0.
- expected_share = locality's severity-weighted exposed area / national total
- actual_share = locality's infrastructure spend / national total spend
- ratio = actual_share / expected_share
- mismatch_score = clamp(50 + 50 * tanh(ln(ratio)), 0..100)
- Store raw ratio alongside score without labeling localities as fraudulent or corrupt.
"""

import datetime
import logging
import math
from decimal import Decimal
from typing import Any, TypedDict

import psycopg

logger = logging.getLogger(__name__)

SEVERITY_WEIGHTS: dict[int, Decimal] = {
    1: Decimal("0.3"),
    2: Decimal("0.6"),
    3: Decimal("1.0"),
}

MAX_RATIO_SENTINEL: Decimal = Decimal("999999.0000")


class ScoringJobResult(TypedDict):
    """Summary metrics returned by scoring job execution."""

    years_processed: list[int]
    levels_processed: list[str]
    total_localities_scored: int
    total_spend_php: Decimal
    total_weighted_exposed_sqkm: Decimal
    rows_inserted: int


def compute_mismatch_score(
    actual_share: Decimal,
    expected_share: Decimal,
) -> tuple[Decimal, Decimal]:
    """Pure mathematical computation of raw ratio and mismatch score.

    Formula:
        ratio = actual_share / expected_share
        mismatch_score = clamp(50 + 50 * tanh(ln(ratio)), 0, 100)

    Edge cases handled:
        - actual_share == 0 and expected_share == 0: ratio = 1.0, score = 50.0 (balanced)
        - actual_share == 0 and expected_share > 0: ratio = 0.0, score = 0.0 (underserved)
        - actual_share > 0 and expected_share == 0: ratio = 999999.0, score = 100.0 (spend > risk)

    Returns:
        (raw_ratio, mismatch_score) rounded to 4 decimal places.
    """
    act = float(actual_share)
    exp = float(expected_share)

    if act <= 0.0 and exp <= 0.0:
        return Decimal("1.0000"), Decimal("50.0000")
    if act <= 0.0 and exp > 0.0:
        return Decimal("0.0000"), Decimal("0.0000")
    if act > 0.0 and exp <= 0.0:
        return MAX_RATIO_SENTINEL, Decimal("100.0000")

    ratio_f = act / exp
    ln_ratio = math.log(ratio_f)
    tanh_val = math.tanh(ln_ratio)
    score_f = 50.0 + 50.0 * tanh_val
    clamped_score = max(0.0, min(100.0, score_f))

    raw_ratio = Decimal(str(round(ratio_f, 4)))
    mismatch_score = Decimal(str(round(clamped_score, 4)))
    return raw_ratio, mismatch_score


def compute_exposure_pct(
    exposed_sqkm: Decimal,
    total_area_sqkm: Decimal,
) -> Decimal:
    """Compute percentage of locality exposed to hazard, clamped to 0..100."""
    if total_area_sqkm <= Decimal(0):
        return Decimal("0.0000")
    pct = (exposed_sqkm / total_area_sqkm) * Decimal(100)
    clamped = max(Decimal(0), min(Decimal(100), pct))
    return Decimal(str(round(clamped, 4)))


def _setup_hazard_exposure_cache(conn: psycopg.Connection[Any]) -> None:
    """Compute and cache severity-weighted hazard exposures in temporary tables."""
    logger.info("Setting up hazard exposure spatial calculations...")
    with conn.cursor() as cur:
        # Pre-filter candidate barangays matching hazard zone envelopes
        cur.execute(
            """
            CREATE TEMP TABLE IF NOT EXISTS candidate_barangays AS
            SELECT b.psgc_code, b.geom, b.land_area_sqkm, b.parent_psgc
            FROM barangays b
            WHERE EXISTS (
                SELECT 1 FROM hazard_zones hz WHERE b.geom && hz.geom
            );
            CREATE INDEX IF NOT EXISTS idx_cand_b_geom ON candidate_barangays USING gist(geom);
            """
        )

        # Subdivide large hazard zone polygons for high-performance spatial intersection
        cur.execute(
            """
            CREATE TEMP TABLE IF NOT EXISTS temp_hazard_subdivided AS
            SELECT
                id,
                hazard_type,
                severity_level,
                CASE severity_level
                    WHEN 1 THEN 0.3
                    WHEN 2 THEN 0.6
                    WHEN 3 THEN 1.0
                    ELSE 1.0
                END AS weight,
                ST_Subdivide(geom, 256) AS geom
            FROM hazard_zones;
            CREATE INDEX IF NOT EXISTS idx_temp_hz_geom ON temp_hazard_subdivided USING gist(geom);
            """
        )

        # Compute barangay-level severity-weighted hazard intersections
        cur.execute(
            """
            CREATE TEMP TABLE IF NOT EXISTS temp_barangay_exposure (
                psgc_code VARCHAR(10) PRIMARY KEY,
                total_weighted_exposed_sqkm NUMERIC NOT NULL,
                flood_weighted_sqkm NUMERIC NOT NULL,
                landslide_weighted_sqkm NUMERIC NOT NULL,
                surge_weighted_sqkm NUMERIC NOT NULL
            );
            """
        )

        cur.execute("SELECT count(*) FROM temp_barangay_exposure;")
        count_row = cur.fetchone()
        existing_exposure_count = count_row[0] if count_row else 0

        if existing_exposure_count == 0:
            logger.info("Computing PostGIS spatial intersections with hazard zones...")
            cur.execute(
                """
                INSERT INTO temp_barangay_exposure (
                    psgc_code,
                    total_weighted_exposed_sqkm,
                    flood_weighted_sqkm,
                    landslide_weighted_sqkm,
                    surge_weighted_sqkm
                )
                SELECT
                    b.psgc_code,
                    SUM(
                        ST_Area(ST_Intersection(b.geom, hz.geom)::geography, false)
                        / 1e6 * hz.weight
                    ) AS total_weighted_exposed_sqkm,
                    SUM(
                        CASE WHEN hz.hazard_type = 'flood'
                        THEN ST_Area(ST_Intersection(b.geom, hz.geom)::geography, false)
                        / 1e6 * hz.weight ELSE 0 END
                    ) AS flood_weighted_sqkm,
                    SUM(
                        CASE WHEN hz.hazard_type = 'landslide'
                        THEN ST_Area(ST_Intersection(b.geom, hz.geom)::geography, false)
                        / 1e6 * hz.weight ELSE 0 END
                    ) AS landslide_weighted_sqkm,
                    SUM(
                        CASE WHEN hz.hazard_type = 'storm_surge'
                        THEN ST_Area(ST_Intersection(b.geom, hz.geom)::geography, false)
                        / 1e6 * hz.weight ELSE 0 END
                    ) AS surge_weighted_sqkm
                FROM temp_hazard_subdivided hz
                JOIN candidate_barangays b ON ST_Intersects(b.geom, hz.geom)
                GROUP BY b.psgc_code;
                """
            )
            logger.info("Computed and cached barangay hazard exposures.")

        # Roll up barangay hazard exposure to parent municipalities
        cur.execute(
            """
            CREATE TEMP TABLE IF NOT EXISTS temp_muni_exposure AS
            SELECT
                b.parent_psgc AS psgc_code,
                SUM(be.total_weighted_exposed_sqkm) AS total_weighted_exposed_sqkm,
                SUM(be.flood_weighted_sqkm) AS flood_weighted_sqkm,
                SUM(be.landslide_weighted_sqkm) AS landslide_weighted_sqkm,
                SUM(be.surge_weighted_sqkm) AS surge_weighted_sqkm
            FROM temp_barangay_exposure be
            JOIN barangays b ON be.psgc_code = b.psgc_code
            WHERE b.parent_psgc IS NOT NULL
            GROUP BY b.parent_psgc;
            CREATE UNIQUE INDEX IF NOT EXISTS idx_temp_muni_psgc
                ON temp_muni_exposure (psgc_code);
            """
        )
    conn.commit()


def compute_and_store_locality_metrics(
    conn: psycopg.Connection[Any],
    years: list[int] | None = None,
    levels: list[str] | None = None,
) -> ScoringJobResult:
    """Compute and upsert mismatch scores and risk metrics for all localities.

    Args:
        conn: Psycopg active database connection.
        years: Specific project years to compute. If None, computes for all years in projects.
        levels: Boundary tiers to score (default: ['municipalities', 'barangays']).

    Returns:
        ScoringJobResult containing execution summary statistics.
    """
    if levels is None:
        levels = ["municipalities", "barangays"]

    with conn.cursor() as cur:
        if years is None:
            cur.execute(
                """
                SELECT DISTINCT EXTRACT(YEAR FROM start_date)::int AS yr
                FROM projects
                WHERE start_date IS NOT NULL
                ORDER BY yr;
                """
            )
            years = [int(r[0]) for r in cur.fetchall() if r[0] is not None]
            if not years:
                years = [datetime.date.today().year]

    logger.info("Running scoring job for years %s and levels %s", years, levels)

    # Initialize spatial exposure tables
    _setup_hazard_exposure_cache(conn)

    total_inserted = 0
    total_national_spend = Decimal("0")
    total_national_exposure = Decimal("0")
    distinct_localities_scored: set[str] = set()

    for year in years:
        logger.info("Processing scoring for year %d...", year)

        for lvl in levels:
            if lvl == "municipalities":
                inserted, spend, exposure = _score_municipalities_for_year(conn, year)
            elif lvl == "barangays":
                inserted, spend, exposure = _score_barangays_for_year(conn, year)
            else:
                logger.warning("Unknown level '%s' skipped.", lvl)
                continue

            total_inserted += inserted
            total_national_spend += spend
            total_national_exposure += exposure
            logger.info(
                "Year %d Level %s: Upserted %d metrics (Spend: PHP %s, Exposed: %s sq km)",
                year,
                lvl,
                inserted,
                spend,
                exposure,
            )

    with conn.cursor() as cur:
        cur.execute("SELECT count(DISTINCT psgc_code) FROM locality_metrics;")
        cnt_row = cur.fetchone()
        localities_count = int(cnt_row[0]) if cnt_row else len(distinct_localities_scored)

    return {
        "years_processed": years,
        "levels_processed": levels,
        "total_localities_scored": localities_count,
        "total_spend_php": total_national_spend,
        "total_weighted_exposed_sqkm": total_national_exposure,
        "rows_inserted": total_inserted,
    }


def _score_municipalities_for_year(
    conn: psycopg.Connection[Any],
    year: int,
) -> tuple[int, Decimal, Decimal]:
    """Score all municipalities for a specific year and upsert into locality_metrics."""
    with conn.cursor() as cur:
        # 1. Aggregate municipal spend from projects joined to barangays
        cur.execute(
            """
            CREATE TEMP TABLE temp_muni_spend_yr ON COMMIT DROP AS
            SELECT
                b.parent_psgc AS psgc_code,
                SUM(COALESCE(p.contract_cost_php, p.budget_php, 0)) AS total_spend_php
            FROM projects p
            JOIN barangays b ON p.psgc_code = b.psgc_code
            WHERE b.parent_psgc IS NOT NULL
              AND EXTRACT(YEAR FROM p.start_date) = %s
            GROUP BY b.parent_psgc;
            """,
            (year,),
        )

        # 2. Compute national totals for municipalities in this year
        cur.execute(
            """
            SELECT
                COALESCE(SUM(ms.total_spend_php), 0),
                COALESCE(SUM(me.total_weighted_exposed_sqkm), 0)
            FROM municipalities m
            LEFT JOIN temp_muni_spend_yr ms ON m.psgc_code = ms.psgc_code
            LEFT JOIN temp_muni_exposure me ON m.psgc_code = me.psgc_code;
            """
        )
        tot_row = cur.fetchone()
        national_spend = Decimal(str(tot_row[0])) if tot_row else Decimal("0")
        national_exposure = Decimal(str(tot_row[1])) if tot_row else Decimal("0")

        # 3. Insert / upsert locality_metrics with window function for percentile ranking
        cur.execute(
            """
            WITH ranked_localities AS (
                SELECT
                    m.psgc_code,
                    %s::int AS year,
                    CASE
                        WHEN m.land_area_sqkm > 0
                        THEN LEAST(
                            100.0,
                            (COALESCE(me.total_weighted_exposed_sqkm, 0)
                            / m.land_area_sqkm) * 100.0
                        )
                        ELSE 0.0
                    END AS hazard_exposure_pct,
                    CASE
                        WHEN m.land_area_sqkm > 0
                        THEN LEAST(
                            100.0,
                            (COALESCE(me.flood_weighted_sqkm, 0)
                            / m.land_area_sqkm) * 100.0
                        )
                        ELSE 0.0
                    END AS flood_pct,
                    CASE
                        WHEN m.land_area_sqkm > 0
                        THEN LEAST(
                            100.0,
                            (COALESCE(me.landslide_weighted_sqkm, 0)
                            / m.land_area_sqkm) * 100.0
                        )
                        ELSE 0.0
                    END AS landslide_pct,
                    CASE
                        WHEN m.land_area_sqkm > 0
                        THEN LEAST(
                            100.0,
                            (COALESCE(me.surge_weighted_sqkm, 0)
                            / m.land_area_sqkm) * 100.0
                        )
                        ELSE 0.0
                    END AS surge_pct,
                    CASE
                        WHEN m.population > 0 AND m.land_area_sqkm > 0
                        THEN ROUND(
                            m.population * LEAST(
                                1.0,
                                COALESCE(me.total_weighted_exposed_sqkm, 0) / m.land_area_sqkm
                            )
                        )
                        ELSE 0
                    END AS population_at_risk,
                    COALESCE(ms.total_spend_php, 0) AS total_spend_php,
                    CASE
                        WHEN m.population > 0
                        THEN COALESCE(ms.total_spend_php, 0) / m.population
                        ELSE 0.0
                    END AS spend_per_capita,
                    CASE
                        WHEN COALESCE(me.total_weighted_exposed_sqkm, 0) > 0
                        THEN COALESCE(ms.total_spend_php, 0) / me.total_weighted_exposed_sqkm
                        ELSE 0.0
                    END AS spend_per_exposed_sqkm,
                    CASE
                        WHEN %s > 0 AND %s > 0
                             AND COALESCE(me.total_weighted_exposed_sqkm, 0) > 0
                             AND COALESCE(ms.total_spend_php, 0) > 0
                        THEN (COALESCE(ms.total_spend_php, 0) / %s)
                             / (me.total_weighted_exposed_sqkm / %s)
                        WHEN COALESCE(me.total_weighted_exposed_sqkm, 0) > 0
                             AND COALESCE(ms.total_spend_php, 0) <= 0
                        THEN 0.0
                        WHEN COALESCE(me.total_weighted_exposed_sqkm, 0) <= 0
                             AND COALESCE(ms.total_spend_php, 0) > 0
                        THEN 999999.0
                        ELSE 1.0
                    END AS raw_ratio,
                    CASE
                        WHEN %s > 0 AND %s > 0
                             AND COALESCE(me.total_weighted_exposed_sqkm, 0) > 0
                             AND COALESCE(ms.total_spend_php, 0) > 0
                        THEN LEAST(
                            100.0,
                            GREATEST(
                                0.0,
                                50.0 + 50.0 * TANH(
                                    LN(
                                        (COALESCE(ms.total_spend_php, 0) / %s)
                                        / (me.total_weighted_exposed_sqkm / %s)
                                    )
                                )
                            )
                        )
                        WHEN COALESCE(me.total_weighted_exposed_sqkm, 0) > 0
                             AND COALESCE(ms.total_spend_php, 0) <= 0
                        THEN 0.0
                        WHEN COALESCE(me.total_weighted_exposed_sqkm, 0) <= 0
                             AND COALESCE(ms.total_spend_php, 0) > 0
                        THEN 100.0
                        ELSE 50.0
                    END AS mismatch_score
                FROM municipalities m
                LEFT JOIN temp_muni_spend_yr ms ON m.psgc_code = ms.psgc_code
                LEFT JOIN temp_muni_exposure me ON m.psgc_code = me.psgc_code
            ),
            scored_localities AS (
                SELECT
                    *,
                    PERCENT_RANK() OVER (
                        ORDER BY mismatch_score ASC
                    ) * 100.0 AS national_percentile
                FROM ranked_localities
            )
            INSERT INTO locality_metrics (
                psgc_code, year, hazard_exposure_pct, flood_pct, landslide_pct, surge_pct,
                population_at_risk, total_spend_php, spend_per_capita, spend_per_exposed_sqkm,
                raw_ratio, mismatch_score, national_percentile, computed_at
            )
            SELECT
                psgc_code, year, hazard_exposure_pct, flood_pct, landslide_pct, surge_pct,
                population_at_risk, total_spend_php, spend_per_capita, spend_per_exposed_sqkm,
                raw_ratio, mismatch_score, national_percentile, NOW()
            FROM scored_localities
            ON CONFLICT (psgc_code, year) DO UPDATE SET
                hazard_exposure_pct = EXCLUDED.hazard_exposure_pct,
                flood_pct = EXCLUDED.flood_pct,
                landslide_pct = EXCLUDED.landslide_pct,
                surge_pct = EXCLUDED.surge_pct,
                population_at_risk = EXCLUDED.population_at_risk,
                total_spend_php = EXCLUDED.total_spend_php,
                spend_per_capita = EXCLUDED.spend_per_capita,
                spend_per_exposed_sqkm = EXCLUDED.spend_per_exposed_sqkm,
                raw_ratio = EXCLUDED.raw_ratio,
                mismatch_score = EXCLUDED.mismatch_score,
                national_percentile = EXCLUDED.national_percentile,
                computed_at = NOW();
            """,
            (
                year,
                national_spend,
                national_exposure,
                national_spend,
                national_exposure,
                national_spend,
                national_exposure,
                national_spend,
                national_exposure,
            ),
        )
        row_count = cur.rowcount
    conn.commit()
    return row_count, national_spend, national_exposure


def _score_barangays_for_year(
    conn: psycopg.Connection[Any],
    year: int,
) -> tuple[int, Decimal, Decimal]:
    """Score all active/relevant barangays for a specific year and upsert into locality_metrics."""
    with conn.cursor() as cur:
        # 1. Aggregate barangay spend from projects
        cur.execute(
            """
            CREATE TEMP TABLE temp_brgy_spend_yr ON COMMIT DROP AS
            SELECT
                psgc_code,
                SUM(COALESCE(contract_cost_php, budget_php, 0)) AS total_spend_php
            FROM projects
            WHERE psgc_code IS NOT NULL
              AND EXTRACT(YEAR FROM start_date) = %s
            GROUP BY psgc_code;
            """,
            (year,),
        )

        # 2. National totals for barangays in this year
        cur.execute(
            """
            SELECT
                COALESCE(SUM(bs.total_spend_php), 0),
                COALESCE(SUM(be.total_weighted_exposed_sqkm), 0)
            FROM barangays b
            LEFT JOIN temp_brgy_spend_yr bs ON b.psgc_code = bs.psgc_code
            LEFT JOIN temp_barangay_exposure be ON b.psgc_code = be.psgc_code;
            """
        )
        tot_row = cur.fetchone()
        national_spend = Decimal(str(tot_row[0])) if tot_row else Decimal("0")
        national_exposure = Decimal(str(tot_row[1])) if tot_row else Decimal("0")

        # 3. Upsert barangays (scoring all barangays with activity, spend, or risk)
        cur.execute(
            """
            WITH ranked_barangays AS (
                SELECT
                    b.psgc_code,
                    %s::int AS year,
                    CASE
                        WHEN b.land_area_sqkm > 0
                        THEN LEAST(
                            100.0,
                            (COALESCE(be.total_weighted_exposed_sqkm, 0)
                            / b.land_area_sqkm) * 100.0
                        )
                        ELSE 0.0
                    END AS hazard_exposure_pct,
                    CASE
                        WHEN b.land_area_sqkm > 0
                        THEN LEAST(
                            100.0,
                            (COALESCE(be.flood_weighted_sqkm, 0)
                            / b.land_area_sqkm) * 100.0
                        )
                        ELSE 0.0
                    END AS flood_pct,
                    CASE
                        WHEN b.land_area_sqkm > 0
                        THEN LEAST(
                            100.0,
                            (COALESCE(be.landslide_weighted_sqkm, 0)
                            / b.land_area_sqkm) * 100.0
                        )
                        ELSE 0.0
                    END AS landslide_pct,
                    CASE
                        WHEN b.land_area_sqkm > 0
                        THEN LEAST(
                            100.0,
                            (COALESCE(be.surge_weighted_sqkm, 0)
                            / b.land_area_sqkm) * 100.0
                        )
                        ELSE 0.0
                    END AS surge_pct,
                    CASE
                        WHEN b.population > 0 AND b.land_area_sqkm > 0
                        THEN ROUND(
                            b.population * LEAST(
                                1.0,
                                COALESCE(be.total_weighted_exposed_sqkm, 0) / b.land_area_sqkm
                            )
                        )
                        ELSE 0
                    END AS population_at_risk,
                    COALESCE(bs.total_spend_php, 0) AS total_spend_php,
                    CASE
                        WHEN b.population > 0
                        THEN COALESCE(bs.total_spend_php, 0) / b.population
                        ELSE 0.0
                    END AS spend_per_capita,
                    CASE
                        WHEN COALESCE(be.total_weighted_exposed_sqkm, 0) > 0
                        THEN COALESCE(bs.total_spend_php, 0) / be.total_weighted_exposed_sqkm
                        ELSE 0.0
                    END AS spend_per_exposed_sqkm,
                    CASE
                        WHEN %s > 0 AND %s > 0
                             AND COALESCE(be.total_weighted_exposed_sqkm, 0) > 0
                             AND COALESCE(bs.total_spend_php, 0) > 0
                        THEN (COALESCE(bs.total_spend_php, 0) / %s)
                             / (be.total_weighted_exposed_sqkm / %s)
                        WHEN COALESCE(be.total_weighted_exposed_sqkm, 0) > 0
                             AND COALESCE(bs.total_spend_php, 0) <= 0
                        THEN 0.0
                        WHEN COALESCE(be.total_weighted_exposed_sqkm, 0) <= 0
                             AND COALESCE(bs.total_spend_php, 0) > 0
                        THEN 999999.0
                        ELSE 1.0
                    END AS raw_ratio,
                    CASE
                        WHEN %s > 0 AND %s > 0
                             AND COALESCE(be.total_weighted_exposed_sqkm, 0) > 0
                             AND COALESCE(bs.total_spend_php, 0) > 0
                        THEN LEAST(
                            100.0,
                            GREATEST(
                                0.0,
                                50.0 + 50.0 * TANH(
                                    LN(
                                        (COALESCE(bs.total_spend_php, 0) / %s)
                                        / (be.total_weighted_exposed_sqkm / %s)
                                    )
                                )
                            )
                        )
                        WHEN COALESCE(be.total_weighted_exposed_sqkm, 0) > 0
                             AND COALESCE(bs.total_spend_php, 0) <= 0
                        THEN 0.0
                        WHEN COALESCE(be.total_weighted_exposed_sqkm, 0) <= 0
                             AND COALESCE(bs.total_spend_php, 0) > 0
                        THEN 100.0
                        ELSE 50.0
                    END AS mismatch_score
                FROM barangays b
                LEFT JOIN temp_brgy_spend_yr bs ON b.psgc_code = bs.psgc_code
                LEFT JOIN temp_barangay_exposure be ON b.psgc_code = be.psgc_code
                WHERE bs.total_spend_php > 0 OR be.total_weighted_exposed_sqkm > 0
            ),
            scored_barangays AS (
                SELECT
                    *,
                    PERCENT_RANK() OVER (
                        ORDER BY mismatch_score ASC
                    ) * 100.0 AS national_percentile
                FROM ranked_barangays
            )
            INSERT INTO locality_metrics (
                psgc_code, year, hazard_exposure_pct, flood_pct, landslide_pct, surge_pct,
                population_at_risk, total_spend_php, spend_per_capita, spend_per_exposed_sqkm,
                raw_ratio, mismatch_score, national_percentile, computed_at
            )
            SELECT
                psgc_code, year, hazard_exposure_pct, flood_pct, landslide_pct, surge_pct,
                population_at_risk, total_spend_php, spend_per_capita, spend_per_exposed_sqkm,
                raw_ratio, mismatch_score, national_percentile, NOW()
            FROM scored_barangays
            ON CONFLICT (psgc_code, year) DO UPDATE SET
                hazard_exposure_pct = EXCLUDED.hazard_exposure_pct,
                flood_pct = EXCLUDED.flood_pct,
                landslide_pct = EXCLUDED.landslide_pct,
                surge_pct = EXCLUDED.surge_pct,
                population_at_risk = EXCLUDED.population_at_risk,
                total_spend_php = EXCLUDED.total_spend_php,
                spend_per_capita = EXCLUDED.spend_per_capita,
                spend_per_exposed_sqkm = EXCLUDED.spend_per_exposed_sqkm,
                raw_ratio = EXCLUDED.raw_ratio,
                mismatch_score = EXCLUDED.mismatch_score,
                national_percentile = EXCLUDED.national_percentile,
                computed_at = NOW();
            """,
            (
                year,
                national_spend,
                national_exposure,
                national_spend,
                national_exposure,
                national_spend,
                national_exposure,
                national_spend,
                national_exposure,
            ),
        )
        row_count = cur.rowcount
    conn.commit()
    return row_count, national_spend, national_exposure
