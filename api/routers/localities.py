"""Locality endpoints router."""

from fastapi import APIRouter, HTTPException, Query, Response, status

from api.cache import build_cache_key, get_cached, set_cached
from api.schemas.common import PaginatedResponse
from api.schemas.localities import (
    LocalityComparisonResponse,
    LocalityProfileResponse,
    LocalitySearchResponse,
)
from api.schemas.projects import ProjectSummary
from api.services.data_version import get_current_data_version
from api.services.localities import (
    compare_localities,
    get_locality_profile_response,
    get_locality_projects,
    search_localities,
)

router = APIRouter(prefix="/v1/localities", tags=["Localities"])


@router.get("/search", response_model=LocalitySearchResponse)
async def search(
    response: Response,
    q: str = Query(..., min_length=1, description="Search query for typeahead locality search"),
    level: str | None = Query(
        None, description="Optional administrative tier (region, province, municipality, barangay)"
    ),
    limit: int = Query(20, ge=1, le=100, description="Max results to return"),
) -> LocalitySearchResponse:
    """Typeahead search across PSGC administrative boundaries with trigram similarity."""
    data_version = await get_current_data_version()
    cache_key = build_cache_key(data_version, "localities_search", q=q, level=level, limit=limit)

    cached = await get_cached(cache_key)
    if cached is not None:
        response.headers["X-Cache"] = "HIT"
        response.headers["X-Data-Version"] = data_version
        return LocalitySearchResponse.model_validate(cached)

    results = await search_localities(q=q, level=level, limit=limit)
    res = LocalitySearchResponse(
        query=q,
        level=level,
        total=len(results),
        items=results,
        data_version=data_version,
    )
    await set_cached(cache_key, res.model_dump(mode="json"))
    response.headers["X-Cache"] = "MISS"
    response.headers["X-Data-Version"] = data_version
    return res


@router.get("/compare", response_model=LocalityComparisonResponse)
async def compare(
    response: Response,
    a: str = Query(..., description="PSGC code of locality A"),
    b: str = Query(..., description="PSGC code of locality B"),
    year: int | None = Query(None, description="Year for metric comparison (defaults to latest)"),
) -> LocalityComparisonResponse:
    """Side-by-side comparison of two localities' risk exposure and spending mismatch metrics."""
    data_version = await get_current_data_version()
    cache_key = build_cache_key(data_version, "localities_compare", a=a, b=b, year=year)

    cached = await get_cached(cache_key)
    if cached is not None:
        response.headers["X-Cache"] = "HIT"
        response.headers["X-Data-Version"] = data_version
        return LocalityComparisonResponse.model_validate(cached)

    res = await compare_localities(psgc_a=a, psgc_b=b, year=year, data_version=data_version)
    if not res:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"One or both localities not found: '{a}', '{b}'",
        )

    await set_cached(cache_key, res.model_dump(mode="json"))
    response.headers["X-Cache"] = "MISS"
    response.headers["X-Data-Version"] = data_version
    return res


@router.get("/{psgc_code}", response_model=LocalityProfileResponse)
async def get_locality(
    psgc_code: str,
    response: Response,
) -> LocalityProfileResponse:
    """Retrieve locality profile, metrics history, and officials by PSGC code."""
    data_version = await get_current_data_version()
    cache_key = build_cache_key(data_version, "locality_profile", psgc_code=psgc_code)

    cached = await get_cached(cache_key)
    if cached is not None:
        response.headers["X-Cache"] = "HIT"
        response.headers["X-Data-Version"] = data_version
        return LocalityProfileResponse.model_validate(cached)

    res = await get_locality_profile_response(psgc_code, data_version)
    if not res:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Locality with PSGC code '{psgc_code}' not found",
        )

    await set_cached(cache_key, res.model_dump(mode="json"))
    response.headers["X-Cache"] = "MISS"
    response.headers["X-Data-Version"] = data_version
    return res


@router.get("/{psgc_code}/projects", response_model=PaginatedResponse[ProjectSummary])
async def get_projects(
    psgc_code: str,
    response: Response,
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(20, ge=1, le=100, description="Page size"),
    year: int | None = Query(None, description="Filter by start year"),
    funding_source: str | None = Query(None, description="Filter by funding source substring"),
    contractor: str | None = Query(None, description="Filter by contractor name or ID"),
    min_budget: float | None = Query(None, ge=0, description="Minimum project budget in PHP"),
) -> PaginatedResponse[ProjectSummary]:
    """Retrieve paginated infrastructure projects geocoded to a locality."""
    data_version = await get_current_data_version()
    cache_key = build_cache_key(
        data_version,
        "locality_projects",
        psgc_code=psgc_code,
        page=page,
        page_size=page_size,
        year=year,
        funding_source=funding_source,
        contractor=contractor,
        min_budget=min_budget,
    )

    cached = await get_cached(cache_key)
    if cached is not None:
        response.headers["X-Cache"] = "HIT"
        response.headers["X-Data-Version"] = data_version
        return PaginatedResponse[ProjectSummary].model_validate(cached)

    items, total = await get_locality_projects(
        psgc_code=psgc_code,
        page=page,
        page_size=page_size,
        year=year,
        funding_source=funding_source,
        contractor=contractor,
        min_budget=min_budget,
    )
    total_pages = (total + page_size - 1) // page_size if total > 0 else 0

    res = PaginatedResponse[ProjectSummary](
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        data_version=data_version,
    )

    await set_cached(cache_key, res.model_dump(mode="json"))
    response.headers["X-Cache"] = "MISS"
    response.headers["X-Data-Version"] = data_version
    return res
