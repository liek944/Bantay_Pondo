"""Ingestion stage for Project NOAH disaster hazard datasets."""

import json
import logging
import os
import tempfile
import zipfile
from pathlib import Path
from typing import Any

import geopandas as gpd
import psycopg
from shapely.geometry import MultiPolygon, Polygon
from shapely.wkb import dumps as wkb_dumps

logger = logging.getLogger(__name__)


def normalize_to_multipolygon(geom: Any) -> MultiPolygon | None:
    """Normalize Polygon or MultiPolygon to 2D MultiPolygon."""
    try:
        if geom is None or geom.is_empty:
            return None
        if not geom.is_valid:
            geom = geom.buffer(0)
        if isinstance(geom, Polygon):
            return MultiPolygon([geom])
        if isinstance(geom, MultiPolygon):
            return geom
        if hasattr(geom, "geoms"):
            polys = [g for g in geom.geoms if isinstance(g, Polygon)]
            if polys:
                return MultiPolygon(polys)
        return None
    except Exception as exc:
        logger.debug("Hazard geometry normalization error: %s", exc)
        return None


def record_reject(
    conn: psycopg.Connection[Any],
    source_dataset: str,
    raw_row: dict[str, Any],
    failure_reason: str,
) -> None:
    """Record an unparseable or invalid hazard row into the rejects quarantine table."""
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO rejects (source_dataset, raw_row, failure_reason, created_at)
            VALUES (%s, %s, %s, NOW());
            """,
            (source_dataset, json.dumps(raw_row, default=str), failure_reason),
        )
    conn.commit()


def ingest_noah_hazards(
    conn: psycopg.Connection[Any],
    filepath: Path,
    hazard_type: str,
    severity_level: int = 2,
    source_dataset: str = "Project NOAH",
    source_year: int = 2024,
    batch_size: int = 1000,
) -> int:
    """Extract, parse, and ingest Project NOAH hazard polygons into hazard_zones.

    Accepts a .zip shapefile archive or a direct .shp / .geojson file.
    """
    valid_hazard_types = {"flood", "landslide", "storm_surge"}
    if hazard_type not in valid_hazard_types:
        raise ValueError(
            f"Invalid hazard_type '{hazard_type}'. Must be one of {valid_hazard_types}"
        )

    logger.info(
        "Ingesting Project NOAH %s hazards (severity %d) from %s ...",
        hazard_type,
        severity_level,
        filepath.name,
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        target_file: Path
        if filepath.suffix.lower() == ".zip":
            with zipfile.ZipFile(filepath, "r") as z:
                z.extractall(tmpdir)
            shp_files = [
                Path(tmpdir) / f
                for f in os.listdir(tmpdir)
                if f.lower().endswith(".shp") or f.lower().endswith(".geojson")
            ]
            if not shp_files:
                raise FileNotFoundError(f"No .shp or .geojson file found inside {filepath.name}")
            target_file = shp_files[0]
        else:
            target_file = filepath

        gdf = gpd.read_file(target_file)

    total_in = len(gdf)
    logger.info("Found %d features in %s", total_in, target_file.name)

    # Reproject if needed
    if gdf.crs is not None and gdf.crs.to_epsg() != 4326:
        gdf = gdf.to_crs(epsg=4326)

    valid_records: list[tuple[str, int, bytes, str, int]] = []
    reject_count = 0

    for idx, row in gdf.iterrows():
        geom = row.get("geometry")
        multi_geom = normalize_to_multipolygon(geom)
        if multi_geom is None or multi_geom.is_empty:
            row_dict = {k: v for k, v in row.items() if k != "geometry"}
            row_dict["row_idx"] = idx
            record_reject(conn, source_dataset, row_dict, "Invalid or empty hazard geometry")
            reject_count += 1
            continue

        wkb_bytes: bytes = wkb_dumps(multi_geom)
        valid_records.append(
            (hazard_type, severity_level, wkb_bytes, source_dataset, source_year)
        )

    logger.info(
        "Prepared %d valid hazard records (%d rejected). Inserting into PostGIS ...",
        len(valid_records),
        reject_count,
    )

    # Idempotency: delete matching existing records from same source_dataset and hazard_type
    with conn.cursor() as cur:
        cur.execute(
            """
            DELETE FROM hazard_zones
            WHERE source_dataset = %s AND hazard_type = %s::hazard_type_enum;
            """,
            (source_dataset, hazard_type),
        )

        insert_query = """
            INSERT INTO hazard_zones (
                hazard_type, severity_level, geom, source_dataset, source_year
            )
            VALUES (%s::hazard_type_enum, %s, ST_SetSRID(ST_GeomFromWKB(%s::bytea), 4326), %s, %s);
        """
        for i in range(0, len(valid_records), batch_size):
            batch = valid_records[i : i + batch_size]
            cur.executemany(insert_query, batch)

    conn.commit()

    with conn.cursor() as cur:
        cur.execute("SELECT count(*) FROM hazard_zones;")
        db_row = cur.fetchone()
        total_out = int(db_row[0]) if db_row else 0

    logger.info(
        "Ingested hazard %s: %d in, %d processed, %d total in database.",
        hazard_type,
        total_in,
        len(valid_records),
        total_out,
    )
    return total_out
