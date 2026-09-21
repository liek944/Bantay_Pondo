"""Metadata and datasets provenance router."""

from fastapi import APIRouter, Response

from api.cache import build_cache_key, get_cached, set_cached
from api.schemas.meta import DatasetsMetaResponse
from api.services.data_version import get_current_data_version
from api.services.meta import get_datasets_meta

router = APIRouter(prefix="/v1/meta", tags=["Metadata"])


@router.get("/datasets", response_model=DatasetsMetaResponse)
async def list_datasets_metadata(response: Response) -> DatasetsMetaResponse:
    """Retrieve platform dataset provenance, source URLs, and last refresh timestamps."""
    data_version = await get_current_data_version()
    cache_key = build_cache_key(data_version, "meta_datasets")

    cached = await get_cached(cache_key)
    if cached is not None:
        response.headers["X-Cache"] = "HIT"
        response.headers["X-Data-Version"] = data_version
        return DatasetsMetaResponse.model_validate(cached)

    res = await get_datasets_meta(data_version)

    await set_cached(cache_key, res.model_dump(mode="json"))
    response.headers["X-Cache"] = "MISS"
    response.headers["X-Data-Version"] = data_version
    return res
