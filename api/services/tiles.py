"""PostGIS Mapbox Vector Tile (MVT) generation service."""

import logging
from typing import Any

from db.session import get_async_db_connection

logger = logging.getLogger(__name__)

SUPPORTED_LAYERS = frozenset(
    [
        "boundaries",
        "hazards",
        "projects",
        # Sub-layer aliases for direct boundary querying
        "regions",
        "provinces",
        "municipalities",
        "barangays",
    ]
)

BOUNDARY_LEVEL_TABLES = {
    "region": ("regions", "region"),
    "regions": ("regions", "region"),
    "province": ("provinces", "province"),
    "provinces": ("provinces", "province"),
    "municipality": ("municipalities", "municipality"),
    "municipalities": ("municipalities", "municipality"),
    "barangay": ("barangays", "barangay"),
    "barangays": ("barangays", "barangay"),
}


def validate_tile_coordinates(z: int, x: int, y: int) -> None:
    """Validate Slippy Map zoom and tile coordinates.

    Raises ValueError if coordinates are outside valid bounds.
    """
    if z < 0 or z > 22:
        raise ValueError(f"Zoom level {z} is out of bounds (0-22)")
    max_coord = 1 << z
    if x < 0 or x >= max_coord:
        raise ValueError(f"Tile x coordinate {x} is out of bounds for zoom {z} (0-{max_coord - 1})")
    if y < 0 or y >= max_coord:
        raise ValueError(f"Tile y coordinate {y} is out of bounds for zoom {z} (0-{max_coord - 1})")


def resolve_boundary_target(z: int, level: str | None) -> tuple[str, str]:
    """Resolve administrative table name and level string for boundary tiles.

    Returns tuple of (table_name, level_string).
    """
    if level is not None:
        normalized_level = level.strip().lower()
        if normalized_level in BOUNDARY_LEVEL_TABLES:
            return BOUNDARY_LEVEL_TABLES[normalized_level]
        valid = "region, province, municipality, barangay"
        raise ValueError(f"Invalid boundary level '{level}'. Must be one of: {valid}")

    # Automatic Level-of-Detail (LOD) selection based on zoom
    if z <= 6:
        return "regions", "region"
    elif z <= 9:
        return "provinces", "province"
    elif z <= 12:
        return "municipalities", "municipality"
    else:
        return "barangays", "barangay"


async def generate_vector_tile(
    layer: str,
    z: int,
    x: int,
    y: int,
    level: str | None = None,
) -> bytes:
    """Generate Mapbox Vector Tile (MVT) bytes using PostGIS ST_AsMVT.

    Args:
        layer: Target layer name (boundaries, hazards, projects, or boundary alias).
        z: Slippy Map zoom level (0-22).
        x: Tile column coordinate.
        y: Tile row coordinate.
        level: Optional administrative level override for boundary tiles.

    Returns:
        MVT binary bytes (protocol buffer format). Empty bytes if no features intersect.
    """
    validate_tile_coordinates(z, x, y)
    normalized_layer = layer.strip().lower()

    if normalized_layer not in SUPPORTED_LAYERS:
        layers_str = ", ".join(sorted(SUPPORTED_LAYERS))
        raise ValueError(f"Unsupported tile layer '{layer}'. Supported layers: {layers_str}")

    # Resolve actual layer query
    if normalized_layer in ("boundaries", "regions", "provinces", "municipalities", "barangays"):
        override_level = level if normalized_layer == "boundaries" else normalized_layer
        table_name, level_str = resolve_boundary_target(z, override_level)
        return await _generate_boundaries_tile(
            table_name=table_name,
            level_str=level_str,
            mvt_layer_name=normalized_layer,
            z=z,
            x=x,
            y=y,
        )
    elif normalized_layer == "hazards":
        return await _generate_hazards_tile(z=z, x=x, y=y)
    elif normalized_layer == "projects":
        return await _generate_projects_tile(z=z, x=x, y=y)
    else:
        raise ValueError(f"Unknown layer '{layer}'")


async def _generate_boundaries_tile(
    table_name: str,
    level_str: str,
    mvt_layer_name: str,
    z: int,
    x: int,
    y: int,
) -> bytes:
    """Generate boundaries vector tile from administrative boundary tables."""
    # Sanitize table name against known table identifiers
    allowed_tables = {"regions", "provinces", "municipalities", "barangays"}
    if table_name not in allowed_tables:
        raise ValueError(f"Unsafe table name: {table_name}")

    query = f"""
        WITH bounds AS (
            SELECT ST_TileEnvelope(%s, %s, %s) AS geom_3857,
                   ST_Transform(ST_TileEnvelope(%s, %s, %s), 4326) AS geom_4326
        ),
        mvtgeom AS (
            SELECT
                psgc_code,
                name,
                parent_psgc,
                %s AS level,
                population,
                land_area_sqkm,
                ST_AsMVTGeom(ST_Transform(geom, 3857), bounds.geom_3857, 4096, 64, true) AS geom
            FROM {table_name}, bounds
            WHERE geom && bounds.geom_4326
        )
        SELECT ST_AsMVT(mvtgeom, %s, 4096, 'geom') FROM mvtgeom;
    """
    params: list[Any] = [z, x, y, z, x, y, level_str, mvt_layer_name]

    async with get_async_db_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(query, params)
            row = await cur.fetchone()
            if row and row[0]:
                return bytes(row[0])
    return b""


async def _generate_hazards_tile(z: int, x: int, y: int) -> bytes:
    """Generate disaster hazard exposure vector tile from hazard_zones table."""
    # Adaptive simplification tolerance in degrees (coarser at lower zoom levels)
    # 360 degrees / (2^z * 2048 pixels)
    tolerance = 360.0 / (float(1 << z) * 2048.0)

    query = """
        WITH bounds AS (
            SELECT ST_TileEnvelope(%s, %s, %s) AS geom_3857,
                   ST_Transform(ST_TileEnvelope(%s, %s, %s), 4326) AS geom_4326
        ),
        clipped AS (
            SELECT
                h.id,
                h.hazard_type::text AS hazard_type,
                h.severity_level,
                h.source_dataset,
                h.source_year,
                ST_ClipByBox2D(h.geom, bounds.geom_4326) AS clipped_geom,
                bounds.geom_3857
            FROM hazard_zones h, bounds
            WHERE h.geom && bounds.geom_4326
        ),
        mvtgeom AS (
            SELECT
                id,
                hazard_type,
                severity_level,
                source_dataset,
                source_year,
                ST_AsMVTGeom(
                    ST_Transform(ST_Simplify(clipped_geom, %s), 3857),
                    geom_3857,
                    4096,
                    64,
                    true
                ) AS geom
            FROM clipped
            WHERE NOT ST_IsEmpty(clipped_geom)
        )
        SELECT ST_AsMVT(mvtgeom, 'hazards', 4096, 'geom') FROM mvtgeom;
    """
    params: list[Any] = [z, x, y, z, x, y, tolerance]

    async with get_async_db_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(query, params)
            row = await cur.fetchone()
            if row and row[0]:
                return bytes(row[0])
    return b""


async def _generate_projects_tile(z: int, x: int, y: int) -> bytes:
    """Generate infrastructure projects vector tile from projects table."""
    query = """
        WITH bounds AS (
            SELECT ST_TileEnvelope(%s, %s, %s) AS geom_3857,
                   ST_Transform(ST_TileEnvelope(%s, %s, %s), 4326) AS geom_4326
        ),
        mvtgeom AS (
            SELECT
                p.id,
                p.contract_id,
                p.title,
                p.implementing_office,
                p.funding_source,
                p.budget_php::float8 AS budget_php,
                p.contract_cost_php::float8 AS contract_cost_php,
                p.physical_progress_pct::float8 AS physical_progress_pct,
                p.psgc_code,
                ST_AsMVTGeom(ST_Transform(p.geom, 3857), bounds.geom_3857, 4096, 64, true) AS geom
            FROM projects p, bounds
            WHERE p.geom IS NOT NULL
              AND p.geom && bounds.geom_4326
        )
        SELECT ST_AsMVT(mvtgeom, 'projects', 4096, 'geom') FROM mvtgeom;
    """
    params: list[Any] = [z, x, y, z, x, y]

    async with get_async_db_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(query, params)
            row = await cur.fetchone()
            if row and row[0]:
                return bytes(row[0])
    return b""
