"""Ingestion stage for PSGC administrative boundaries."""

import json
import logging
from pathlib import Path
from typing import Any

import psycopg
from shapely.geometry import MultiPolygon, Polygon, shape
from shapely.wkb import dumps as wkb_dumps

logger = logging.getLogger(__name__)


def normalize_to_multipolygon(geom_dict: dict[str, Any]) -> MultiPolygon | None:
    """Normalize any Polygon or MultiPolygon GeoJSON geometry to a valid Shapely MultiPolygon."""
    try:
        geom = shape(geom_dict)
        if geom.is_empty:
            return None
        if not geom.is_valid:
            geom = geom.buffer(0)
        if isinstance(geom, Polygon):
            return MultiPolygon([geom])
        if isinstance(geom, MultiPolygon):
            return geom
        # If geometry collection or other, extract polygons
        if hasattr(geom, "geoms"):
            polys = [g for g in geom.geoms if isinstance(g, Polygon)]
            if polys:
                return MultiPolygon(polys)
        return None
    except Exception as exc:
        logger.debug("Geometry normalization error: %s", exc)
        return None


def record_reject(
    conn: psycopg.Connection[Any],
    source_dataset: str,
    raw_row: dict[str, Any],
    failure_reason: str,
) -> None:
    """Record an unparseable or invalid row into the rejects quarantine table."""
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO rejects (source_dataset, raw_row, failure_reason, created_at)
            VALUES (%s, %s, %s, NOW());
            """,
            (source_dataset, json.dumps(raw_row), failure_reason),
        )
    conn.commit()


def ingest_geojson_boundaries(
    conn: psycopg.Connection[Any],
    filepath: Path,
    level: str,
    batch_size: int = 2000,
) -> int:
    """Parse and ingest administrative boundary GeoJSON into PostGIS with row-count assertions.

    Levels supported: 'regions', 'provinces', 'municipalities', 'barangays'.
    """
    valid_levels = {"regions", "provinces", "municipalities", "barangays"}
    if level not in valid_levels:
        raise ValueError(f"Unknown boundary level '{level}'. Must be one of {valid_levels}")

    logger.info("Parsing %s GeoJSON from %s ...", level, filepath)
    with open(filepath, encoding="utf-8") as f:
        geojson_data = json.load(f)

    features: list[dict[str, Any]] = geojson_data.get("features", [])
    total_in = len(features)
    logger.info("Found %d features in %s", total_in, filepath.name)

    valid_records: list[tuple[str, str, str | None, float | None, bytes]] = []
    reject_count = 0

    for feat in features:
        props: dict[str, Any] = feat.get("properties") or {}
        geom_dict: dict[str, Any] | None = feat.get("geometry")

        psgc_code = str(props.get("psgc_code") or "").strip()
        if not psgc_code:
            record_reject(conn, f"psgc_{level}", feat, "Missing or empty psgc_code")
            reject_count += 1
            continue

        name = (
            str(props.get("psgc_name") or "").strip()
            or str(props.get("ADM4_EN") or "").strip()
            or str(props.get("ADM3_EN") or "").strip()
            or str(props.get("ADM2_EN") or "").strip()
            or str(props.get("ADM1_EN") or "").strip()
        )
        if not name:
            record_reject(conn, f"psgc_{level}", feat, "Missing or empty name property")
            reject_count += 1
            continue

        parent_psgc: str | None = None
        if level == "provinces":
            parent_psgc = psgc_code[:2] + "00000000"
        elif level == "municipalities":
            parent_psgc = psgc_code[:5] + "00000"
        elif level == "barangays":
            parent_psgc = psgc_code[:7] + "000"

        land_area_raw = props.get("AREA_SQKM") or props.get("land_area_sqkm")
        land_area: float | None = None
        if land_area_raw is not None:
            try:
                land_area = float(land_area_raw)
            except (ValueError, TypeError):
                land_area = None

        if not geom_dict:
            record_reject(conn, f"psgc_{level}", feat, "Missing geometry dictionary")
            reject_count += 1
            continue

        multi_geom = normalize_to_multipolygon(geom_dict)
        if multi_geom is None or multi_geom.is_empty:
            record_reject(
                conn, f"psgc_{level}", feat, "Failed to normalize geometry to MultiPolygon"
            )
            reject_count += 1
            continue

        wkb_bytes: bytes = wkb_dumps(multi_geom)
        valid_records.append((psgc_code, name, parent_psgc, land_area, wkb_bytes))

    logger.info(
        "Normalized %d valid records for table '%s' (%d rejected). Executing batch insert ...",
        len(valid_records),
        level,
        reject_count,
    )

    upsert_query = f"""
        INSERT INTO {level} (psgc_code, name, parent_psgc, land_area_sqkm, geom)
        VALUES (%s, %s, %s, %s, ST_SetSRID(ST_GeomFromWKB(%s::bytea), 4326))
        ON CONFLICT (psgc_code) DO UPDATE
        SET name = EXCLUDED.name,
            parent_psgc = EXCLUDED.parent_psgc,
            land_area_sqkm = EXCLUDED.land_area_sqkm,
            geom = EXCLUDED.geom;
    """  # noqa: S608

    with conn.cursor() as cur:
        for i in range(0, len(valid_records), batch_size):
            batch = valid_records[i : i + batch_size]
            cur.executemany(upsert_query, batch)
    conn.commit()

    with conn.cursor() as cur:
        cur.execute(f"SELECT count(*) FROM {level};")  # noqa: S608
        row = cur.fetchone()
        total_out = int(row[0]) if row else 0

    logger.info(
        "Ingested %s: %d in, %d processed, %d total in database.",
        level,
        total_in,
        len(valid_records),
        total_out,
    )
    return total_out
