"""Locality query services."""

from decimal import Decimal
from typing import Any

from api.schemas.localities import (
    LocalityComparisonItem,
    LocalityComparisonResponse,
    LocalityMetricDelta,
    LocalityMetricDetail,
    LocalityProfile,
    LocalityProfileResponse,
    LocalitySearchResult,
    OfficialSummary,
)
from api.schemas.projects import ProjectSummary
from db.session import get_async_db_connection

ADMIN_LEVELS = ("region", "province", "municipality", "barangay")
TABLE_MAP = {
    "region": "regions",
    "province": "provinces",
    "municipality": "municipalities",
    "barangay": "barangays",
}


async def search_localities(
    q: str,
    level: str | None = None,
    limit: int = 20,
) -> list[LocalitySearchResult]:
    """Perform typeahead search for localities using trigram similarity and substring match."""
    cleaned_q = q.strip()
    if not cleaned_q:
        return []

    target_levels = [level.lower()] if level and level.lower() in TABLE_MAP else list(ADMIN_LEVELS)

    queries: list[str] = []
    params: list[Any] = []

    for lvl in target_levels:
        tbl = TABLE_MAP[lvl]
        queries.append(
            f"""
            SELECT
                psgc_code,
                name,
                '{lvl}' AS level,
                parent_psgc,
                land_area_sqkm,
                population,
                similarity(name, %s) AS similarity
            FROM {tbl}
            WHERE name ILIKE %s OR similarity(name, %s) > 0.15
            """
        )
        like_pattern = f"%{cleaned_q}%"
        params.extend([cleaned_q, like_pattern, cleaned_q])

    union_sql = " UNION ALL ".join(queries)
    full_sql = f"""
        WITH matched AS (
            {union_sql}
        )
        SELECT psgc_code, name, level, parent_psgc, land_area_sqkm, population, similarity
        FROM matched
        ORDER BY similarity DESC, population DESC NULLS LAST, name ASC
        LIMIT %s
    """
    params.append(limit)

    results: list[LocalitySearchResult] = []
    async with get_async_db_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(full_sql, params)
            rows = await cur.fetchall()
            for r in rows:
                results.append(
                    LocalitySearchResult(
                        psgc_code=r[0],
                        name=r[1],
                        level=r[2],
                        parent_psgc=r[3],
                        land_area_sqkm=float(r[4]) if r[4] is not None else None,
                        population=int(r[5]) if r[5] is not None else None,
                        similarity=round(float(r[6]), 3) if r[6] is not None else None,
                    )
                )
    return results


async def get_locality_entity(psgc_code: str) -> tuple[LocalityProfile, str] | None:
    """Find administrative boundary info and tier for a given psgc_code."""
    async with get_async_db_connection() as conn:
        async with conn.cursor() as cur:
            for lvl in ("municipality", "barangay", "province", "region"):
                tbl = TABLE_MAP[lvl]
                query = f"""
                    SELECT t.psgc_code, t.name, '{lvl}' AS level, t.parent_psgc,
                           t.land_area_sqkm, t.population, t.population_year,
                           p.name AS parent_name
                    FROM {tbl} t
                    LEFT JOIN {tbl} p ON t.parent_psgc = p.psgc_code
                    WHERE t.psgc_code = %s
                    LIMIT 1
                """
                await cur.execute(query, (psgc_code,))
                row = await cur.fetchone()
                if row:
                    profile = LocalityProfile(
                        psgc_code=row[0],
                        name=row[1],
                        level=row[2],
                        parent_psgc=row[3],
                        land_area_sqkm=float(row[4]) if row[4] is not None else None,
                        population=int(row[5]) if row[5] is not None else None,
                        population_year=int(row[6]) if row[6] is not None else None,
                        parent_name=row[7],
                    )
                    return profile, lvl
    return None


async def get_locality_metrics_history(psgc_code: str) -> list[LocalityMetricDetail]:
    """Retrieve full time-series metrics history for a locality."""
    sql = """
        SELECT
            year, hazard_exposure_pct, flood_pct, landslide_pct, surge_pct,
            population_at_risk, total_spend_php, spend_per_capita,
            spend_per_exposed_sqkm, raw_ratio, mismatch_score,
            national_percentile, computed_at
        FROM locality_metrics
        WHERE psgc_code = %s
        ORDER BY year DESC
    """
    metrics: list[LocalityMetricDetail] = []
    async with get_async_db_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(sql, (psgc_code,))
            rows = await cur.fetchall()
            for r in rows:
                metrics.append(
                    LocalityMetricDetail(
                        year=r[0],
                        hazard_exposure_pct=Decimal(str(r[1])),
                        flood_pct=Decimal(str(r[2])),
                        landslide_pct=Decimal(str(r[3])),
                        surge_pct=Decimal(str(r[4])),
                        population_at_risk=int(r[5]),
                        total_spend_php=Decimal(str(r[6])),
                        spend_per_capita=Decimal(str(r[7])),
                        spend_per_exposed_sqkm=Decimal(str(r[8])),
                        raw_ratio=Decimal(str(r[9])),
                        mismatch_score=Decimal(str(r[10])),
                        national_percentile=Decimal(str(r[11])),
                        computed_at=r[12],
                    )
                )
    return metrics


async def get_locality_officials(psgc_code: str) -> list[OfficialSummary]:
    """Retrieve officials associated with a locality."""
    sql = """
        SELECT id, name, position, district, term_start, term_end, party
        FROM officials
        WHERE psgc_code = %s
        ORDER BY name ASC
    """
    officials: list[OfficialSummary] = []
    async with get_async_db_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(sql, (psgc_code,))
            rows = await cur.fetchall()
            for r in rows:
                officials.append(
                    OfficialSummary(
                        id=r[0],
                        name=r[1],
                        position=r[2],
                        district=r[3],
                        term_start=r[4],
                        term_end=r[5],
                        party=r[6],
                    )
                )
    return officials


async def get_locality_profile_response(
    psgc_code: str,
    data_version: str,
) -> LocalityProfileResponse | None:
    """Retrieve locality profile, metrics history, and officials."""
    entity = await get_locality_entity(psgc_code)
    if not entity:
        return None
    profile, _ = entity

    metrics = await get_locality_metrics_history(psgc_code)
    officials = await get_locality_officials(psgc_code)

    return LocalityProfileResponse(
        profile=profile,
        metrics=metrics,
        officials=officials,
        data_version=data_version,
    )


async def get_locality_projects(
    psgc_code: str,
    page: int = 1,
    page_size: int = 20,
    year: int | None = None,
    funding_source: str | None = None,
    contractor: str | None = None,
    min_budget: float | None = None,
) -> tuple[list[ProjectSummary], int]:
    """Retrieve paginated projects belonging to a locality with optional filters."""
    where_clauses: list[str] = [
        """(
            p.psgc_code = %s
            OR p.psgc_code IN (SELECT psgc_code FROM barangays WHERE parent_psgc = %s)
            OR p.psgc_code IN (
                SELECT b.psgc_code FROM barangays b
                JOIN municipalities m ON b.parent_psgc = m.psgc_code
                WHERE m.parent_psgc = %s
            )
        )"""
    ]
    params: list[Any] = [psgc_code, psgc_code, psgc_code]

    if year is not None:
        where_clauses.append("EXTRACT(YEAR FROM p.start_date) = %s")
        params.append(year)

    if funding_source:
        where_clauses.append("p.funding_source ILIKE %s")
        params.append(f"%{funding_source.strip()}%")

    if contractor:
        where_clauses.append(
            "(c.normalized_name ILIKE %s OR CAST(c.id AS TEXT) = %s)"
        )
        params.extend([f"%{contractor.strip()}%", contractor.strip()])

    if min_budget is not None:
        where_clauses.append("p.budget_php >= %s")
        params.append(min_budget)

    where_sql = " AND ".join(where_clauses)

    count_sql = f"""
        SELECT COUNT(*)
        FROM projects p
        LEFT JOIN contractors c ON p.contractor_id = c.id
        WHERE {where_sql}
    """

    offset = (page - 1) * page_size
    select_sql = f"""
        SELECT
            p.contract_id,
            p.title,
            p.implementing_office,
            p.funding_source,
            p.budget_php,
            p.contract_cost_php,
            p.start_date,
            p.target_completion_date,
            p.physical_progress_pct,
            p.psgc_code,
            p.contractor_id,
            c.normalized_name AS contractor_name
        FROM projects p
        LEFT JOIN contractors c ON p.contractor_id = c.id
        WHERE {where_sql}
        ORDER BY p.budget_php DESC NULLS LAST, p.start_date DESC NULLS LAST
        LIMIT %s OFFSET %s
    """
    select_params = list(params) + [page_size, offset]

    items: list[ProjectSummary] = []
    total = 0

    async with get_async_db_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(count_sql, params)
            count_row = await cur.fetchone()
            total = int(count_row[0]) if count_row else 0

            await cur.execute(select_sql, select_params)
            rows = await cur.fetchall()
            for r in rows:
                items.append(
                    ProjectSummary(
                        contract_id=r[0],
                        title=r[1],
                        implementing_office=r[2],
                        funding_source=r[3],
                        budget_php=Decimal(str(r[4])) if r[4] is not None else None,
                        contract_cost_php=Decimal(str(r[5])) if r[5] is not None else None,
                        start_date=r[6],
                        target_completion_date=r[7],
                        physical_progress_pct=Decimal(str(r[8])) if r[8] is not None else None,
                        psgc_code=r[9],
                        contractor_id=r[10],
                        contractor_name=r[11],
                    )
                )

    return items, total


async def compare_localities(
    psgc_a: str,
    psgc_b: str,
    year: int | None = None,
    data_version: str = "v1.0.0",
) -> LocalityComparisonResponse | None:
    """Compare two localities side-by-side."""
    entity_a = await get_locality_entity(psgc_a)
    entity_b = await get_locality_entity(psgc_b)
    if not entity_a or not entity_b:
        return None

    profile_a, _ = entity_a
    profile_b, _ = entity_b

    metrics_a = await get_locality_metrics_history(psgc_a)
    metrics_b = await get_locality_metrics_history(psgc_b)

    # Pick requested year or latest common / latest available year
    target_year: int
    if year is not None:
        target_year = year
    elif metrics_a:
        target_year = metrics_a[0].year
    elif metrics_b:
        target_year = metrics_b[0].year
    else:
        target_year = 2021

    metric_a = next((m for m in metrics_a if m.year == target_year), None)
    metric_b = next((m for m in metrics_b if m.year == target_year), None)

    # Deltas (A - B)
    score_delta = (
        (metric_a.mismatch_score - metric_b.mismatch_score)
        if metric_a and metric_b
        else None
    )
    spend_delta = (
        (metric_a.total_spend_php - metric_b.total_spend_php)
        if metric_a and metric_b
        else None
    )
    hazard_delta = (
        (metric_a.hazard_exposure_pct - metric_b.hazard_exposure_pct)
        if metric_a and metric_b
        else None
    )
    spend_capita_delta = (
        (metric_a.spend_per_capita - metric_b.spend_per_capita)
        if metric_a and metric_b
        else None
    )

    deltas = LocalityMetricDelta(
        mismatch_score_delta=score_delta,
        total_spend_php_delta=spend_delta,
        hazard_exposure_pct_delta=hazard_delta,
        spend_per_capita_delta=spend_capita_delta,
    )

    return LocalityComparisonResponse(
        year=target_year,
        locality_a=LocalityComparisonItem(profile=profile_a, metric=metric_a),
        locality_b=LocalityComparisonItem(profile=profile_b, metric=metric_b),
        deltas=deltas,
        data_version=data_version,
    )
