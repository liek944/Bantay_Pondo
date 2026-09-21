"""Rankings and leaderboards endpoints router."""

from fastapi import APIRouter, Query, Response

from api.cache import build_cache_key, get_cached, set_cached
from api.schemas.rankings import RankingsResponse
from api.services.data_version import get_current_data_version
from api.services.rankings import get_rankings

router = APIRouter(prefix="/v1/rankings", tags=["Rankings"])


@router.get("", response_model=RankingsResponse)
async def list_rankings(
    response: Response,
    metric: str = Query(
        "mismatch_score",
        description=(
            "Ranking metric: mismatch_score, total_spend_php, "
            "hazard_exposure_pct, spend_per_capita, population_at_risk"
        ),
    ),
    level: str = Query(
        "municipality",
        description="Administrative tier: municipality, barangay, province, region",
    ),
    limit: int = Query(20, ge=1, le=100, description="Number of localities to return"),
    year: int | None = Query(None, description="Year (defaults to latest available year)"),
    order: str = Query("asc", description="Sort order: 'asc' (most underserved) or 'desc'"),
) -> RankingsResponse:
    """Retrieve locality leaderboards sorted by risk mismatch or spending metrics."""
    data_version = await get_current_data_version()
    cache_key = build_cache_key(
        data_version,
        "rankings",
        metric=metric,
        level=level,
        limit=limit,
        year=year,
        order=order,
    )

    cached = await get_cached(cache_key)
    if cached is not None:
        response.headers["X-Cache"] = "HIT"
        response.headers["X-Data-Version"] = data_version
        return RankingsResponse.model_validate(cached)

    res = await get_rankings(
        metric=metric,
        level=level,
        limit=limit,
        year=year,
        order=order,
        data_version=data_version,
    )

    await set_cached(cache_key, res.model_dump(mode="json"))
    response.headers["X-Cache"] = "MISS"
    response.headers["X-Data-Version"] = data_version
    return res
