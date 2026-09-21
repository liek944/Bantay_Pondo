"""Vector tiles router serving PostGIS MVT tiles."""

import logging

from fastapi import APIRouter, HTTPException, Query, Response, status

from api.cache import build_cache_key, get_cached_bytes, set_cached_bytes
from api.services.data_version import get_current_data_version
from api.services.tiles import SUPPORTED_LAYERS, generate_vector_tile, validate_tile_coordinates

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/tiles", tags=["Tiles"])

MVT_MEDIA_TYPE = "application/vnd.mapbox-vector-tile"


@router.get(
    "/{layer}/{z}/{x}/{y}.mvt",
    response_class=Response,
    summary="Get Mapbox Vector Tile",
    description="Serves dynamic vector tiles from PostGIS via ST_AsMVT with Redis caching.",
    responses={
        200: {
            "content": {MVT_MEDIA_TYPE: {}},
            "description": "Binary Mapbox Vector Tile (MVT) protobuf.",
        },
        400: {"description": "Invalid zoom or tile coordinates."},
        404: {"description": "Unsupported tile layer."},
    },
)
async def get_tile(
    layer: str,
    z: int,
    x: int,
    y: int,
    level: str | None = Query(
        None,
        description="Optional boundary level override: region, province, municipality, barangay",
    ),
) -> Response:
    """Retrieve or generate Mapbox Vector Tile (MVT) for the requested layer and coordinates."""
    # Validate coordinates
    try:
        validate_tile_coordinates(z, x, y)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    # Validate layer
    normalized_layer = layer.strip().lower()
    if normalized_layer not in SUPPORTED_LAYERS:
        layers_str = ", ".join(sorted(SUPPORTED_LAYERS))
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Unsupported tile layer '{layer}'. Supported layers: {layers_str}",
        )

    data_version = await get_current_data_version()
    cache_route = f"tiles:{normalized_layer}:{z}:{x}:{y}"
    cache_key = build_cache_key(data_version, cache_route, level=level)

    # Check Redis cache
    cached_tile = await get_cached_bytes(cache_key)
    if cached_tile is not None:
        return Response(
            content=cached_tile,
            media_type=MVT_MEDIA_TYPE,
            headers={
                "X-Cache": "HIT",
                "X-Data-Version": data_version,
                "Content-Type": MVT_MEDIA_TYPE,
            },
        )

    # Generate tile via PostGIS
    try:
        tile_bytes = await generate_vector_tile(
            layer=normalized_layer,
            z=z,
            x=x,
            y=y,
            level=level,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except Exception as exc:
        logger.error("Error generating vector tile %s/%d/%d/%d: %s", layer, z, x, y, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate vector tile",
        ) from exc

    # Cache binary tile payload
    await set_cached_bytes(cache_key, tile_bytes)

    return Response(
        content=tile_bytes,
        media_type=MVT_MEDIA_TYPE,
        headers={
            "X-Cache": "MISS",
            "X-Data-Version": data_version,
            "Content-Type": MVT_MEDIA_TYPE,
        },
    )
