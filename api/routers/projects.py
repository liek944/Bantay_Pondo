"""Project endpoints router."""

from fastapi import APIRouter, HTTPException, Response, status

from api.cache import build_cache_key, get_cached, set_cached
from api.schemas.projects import ProjectDetailResponse
from api.services.data_version import get_current_data_version
from api.services.projects import get_project_detail

router = APIRouter(prefix="/v1/projects", tags=["Projects"])


@router.get("/{contract_id}", response_model=ProjectDetailResponse)
async def get_project(
    contract_id: str,
    response: Response,
) -> ProjectDetailResponse:
    """Retrieve detailed project information, rule-based risk flags, and related awards."""
    data_version = await get_current_data_version()
    cache_key = build_cache_key(data_version, "project_detail", contract_id=contract_id)

    cached = await get_cached(cache_key)
    if cached is not None:
        response.headers["X-Cache"] = "HIT"
        response.headers["X-Data-Version"] = data_version
        return ProjectDetailResponse.model_validate(cached)

    res = await get_project_detail(contract_id, data_version)
    if not res:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with contract ID '{contract_id}' not found",
        )

    await set_cached(cache_key, res.model_dump(mode="json"))
    response.headers["X-Cache"] = "MISS"
    response.headers["X-Data-Version"] = data_version
    return res
