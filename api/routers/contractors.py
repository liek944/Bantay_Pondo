"""Contractor endpoints router."""

from fastapi import APIRouter, HTTPException, Response, status

from api.cache import build_cache_key, get_cached, set_cached
from api.schemas.contractors import ContractorProfileResponse
from api.services.contractors import get_contractor_profile
from api.services.data_version import get_current_data_version

router = APIRouter(prefix="/v1/contractors", tags=["Contractors"])


@router.get("/{contractor_id}", response_model=ContractorProfileResponse)
async def get_contractor(
    contractor_id: int,
    response: Response,
) -> ContractorProfileResponse:
    """Retrieve contractor profile, awarded contracts, and district concentration (HHI)."""
    data_version = await get_current_data_version()
    cache_key = build_cache_key(data_version, "contractor_profile", contractor_id=contractor_id)

    cached = await get_cached(cache_key)
    if cached is not None:
        response.headers["X-Cache"] = "HIT"
        response.headers["X-Data-Version"] = data_version
        return ContractorProfileResponse.model_validate(cached)

    res = await get_contractor_profile(contractor_id, data_version)
    if not res:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Contractor with ID '{contractor_id}' not found",
        )

    await set_cached(cache_key, res.model_dump(mode="json"))
    response.headers["X-Cache"] = "MISS"
    response.headers["X-Data-Version"] = data_version
    return res
