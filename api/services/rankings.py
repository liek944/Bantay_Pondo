"""Rankings and leaderboard service."""

from decimal import Decimal

from api.schemas.rankings import RankingItem, RankingsResponse
from db.session import get_async_db_connection

ALLOWED_METRICS = {
    "mismatch_score": "m.mismatch_score",
    "total_spend_php": "m.total_spend_php",
    "hazard_exposure_pct": "m.hazard_exposure_pct",
    "spend_per_capita": "m.spend_per_capita",
    "population_at_risk": "m.population_at_risk",
}

LEVEL_TABLES = {
    "municipality": "municipalities",
    "barangay": "barangays",
    "province": "provinces",
    "region": "regions",
}


async def get_rankings(
    metric: str = "mismatch_score",
    level: str = "municipality",
    limit: int = 20,
    year: int | None = None,
    order: str = "asc",
    data_version: str = "v1.0.0",
) -> RankingsResponse:
    """Retrieve ranked localities by metric and administrative level."""
    metric_col = ALLOWED_METRICS.get(metric.lower(), "m.mismatch_score")
    tbl_name = LEVEL_TABLES.get(level.lower(), "municipalities")
    order_direction = "DESC" if order.lower() == "desc" else "ASC"
    limit_clamped = max(1, min(limit, 100))

    async with get_async_db_connection() as conn:
        async with conn.cursor() as cur:
            # Resolve target year if not provided
            if year is None:
                await cur.execute("SELECT MAX(year) FROM locality_metrics")
                yr_row = await cur.fetchone()
                target_year = yr_row[0] if (yr_row and yr_row[0]) else 2021
            else:
                target_year = year

            query = f"""
                SELECT
                    m.psgc_code,
                    t.name,
                    '{level}' AS level,
                    {metric_col} AS metric_val,
                    m.mismatch_score,
                    m.national_percentile,
                    m.total_spend_php,
                    m.hazard_exposure_pct
                FROM locality_metrics m
                JOIN {tbl_name} t ON m.psgc_code = t.psgc_code
                WHERE m.year = %s
                ORDER BY {metric_col} {order_direction} NULLS LAST, t.name ASC
                LIMIT %s
            """

            await cur.execute(query, (target_year, limit_clamped))
            rows = await cur.fetchall()

    items: list[RankingItem] = []
    for idx, r in enumerate(rows, start=1):
        items.append(
            RankingItem(
                rank=idx,
                psgc_code=r[0],
                name=r[1],
                level=r[2],
                metric_value=Decimal(str(r[3])),
                mismatch_score=Decimal(str(r[4])),
                national_percentile=Decimal(str(r[5])),
                total_spend_php=Decimal(str(r[6])),
                hazard_exposure_pct=Decimal(str(r[7])),
            )
        )

    return RankingsResponse(
        metric=metric,
        level=level,
        year=target_year,
        order=order_direction.lower(),
        total=len(items),
        items=items,
        data_version=data_version,
    )
