"""Ingestion stage for DPWH infrastructure projects with PostGIS spatial join and review queue."""

import datetime
import hashlib
import json
import logging
import math
from pathlib import Path
from typing import Any, TypedDict

import polars as pl
import psycopg

from pipeline.stages.ingest_psgc import record_reject

logger = logging.getLogger(__name__)


class ProjectIngestionResult(TypedDict):
    """Statistics recorded during DPWH project ingestion."""

    total_in: int
    geocoded: int
    review_queue: int
    rejects: int
    upserted: int


def _parse_date(value: Any) -> datetime.date | None:
    """Safely parse date values from Date or String types."""
    if value is None:
        return None
    if isinstance(value, datetime.date):
        return value
    if isinstance(value, datetime.datetime):
        return value.date()
    if isinstance(value, str):
        cleaned = value.strip()
        if not cleaned:
            return None
        for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%Y/%m/%d"):
            try:
                return datetime.datetime.strptime(cleaned, fmt).date()
            except ValueError:
                continue
    return None


def parse_and_normalize_project(
    row: dict[str, Any],
) -> tuple[dict[str, Any] | None, str | None]:
    """Validate and normalize a raw DPWH project row into typed attributes.

    Returns:
        (normalized_dict, None) on success.
        (None, failure_reason) if row is malformed and must be quarantined to rejects.
    """
    contract_id_raw = row.get("contractId")
    if contract_id_raw is None or not str(contract_id_raw).strip():
        return None, "Missing or empty contractId"

    contract_id = str(contract_id_raw).strip()

    description_raw = row.get("description")
    description = str(description_raw).strip() if description_raw is not None else None
    title = description if description else contract_id

    location_raw = row.get("location")
    implementing_office: str | None = None
    if isinstance(location_raw, dict):
        office = location_raw.get("province") or location_raw.get("region")
        if office:
            implementing_office = str(office).strip()

    funding_source_raw = row.get("sourceOfFunds")
    funding_source = (
        str(funding_source_raw).strip() if funding_source_raw is not None else None
    )

    budget_raw = row.get("budget")
    budget_php: float | None = None
    if budget_raw is not None:
        try:
            b_val = float(budget_raw)
            if not math.isnan(b_val):
                budget_php = b_val
        except (ValueError, TypeError):
            budget_php = None

    # DPWH transparency dataset currently tracks paid amounts via amountPaid
    # Contract cost is nullable and reserved for actual award/completion cost
    contract_cost_php: float | None = None

    start_date = _parse_date(row.get("startDate"))
    target_completion_date = _parse_date(row.get("completionDate"))

    progress_raw = row.get("progress")
    physical_progress_pct: float | None = None
    if progress_raw is not None:
        try:
            p_val = float(progress_raw)
            if not math.isnan(p_val):
                physical_progress_pct = p_val
        except (ValueError, TypeError):
            physical_progress_pct = None

    # Validate coordinate float values
    lat_raw = row.get("latitude")
    lon_raw = row.get("longitude")
    lat: float | None = None
    lon: float | None = None
    invalid_coord_reason: str | None = None

    if lat_raw is not None and lon_raw is not None:
        try:
            lat_f = float(lat_raw)
            lon_f = float(lon_raw)
            if math.isnan(lat_f) or math.isnan(lon_f):
                lat = None
                lon = None
                invalid_coord_reason = "Missing coordinates (null lat/lon)"
            elif not (-90.0 <= lat_f <= 90.0 and -180.0 <= lon_f <= 180.0):
                lat = lat_f
                lon = lon_f
                invalid_coord_reason = (
                    f"Coordinates out of range: lat={lat_f}, lon={lon_f}"
                )
            else:
                lat = lat_f
                lon = lon_f
        except (ValueError, TypeError):
            lat = None
            lon = None
            invalid_coord_reason = "Invalid coordinate format"
    else:
        invalid_coord_reason = "Missing coordinates (null lat/lon)"

    source_row_hash = hashlib.sha256(
        json.dumps(row, sort_keys=True, default=str).encode("utf-8")
    ).hexdigest()

    normalized: dict[str, Any] = {
        "contract_id": contract_id,
        "title": title,
        "description": description,
        "implementing_office": implementing_office,
        "funding_source": funding_source,
        "budget_php": budget_php,
        "contract_cost_php": contract_cost_php,
        "start_date": start_date,
        "target_completion_date": target_completion_date,
        "physical_progress_pct": physical_progress_pct,
        "latitude": lat,
        "longitude": lon,
        "invalid_coord_reason": invalid_coord_reason,
        "source_row_hash": source_row_hash,
        "raw_payload": row,
    }
    return normalized, None


def ingest_dpwh_projects(
    conn: psycopg.Connection[Any],
    filepath: Path,
    limit: int | None = None,
    batch_size: int = 5000,
) -> ProjectIngestionResult:
    """Ingest DPWH projects from parquet with PostGIS spatial join to barangays.

    - Geocoded projects are inserted into `projects` with valid `geom` and `psgc_code`.
    - Un-geocoded projects (null coords or outside boundaries) are inserted into `projects`
      (with `psgc_code = NULL`) AND recorded into `project_reviews`.
    - Malformed rows are quarantined to `rejects` table.
    - Idempotent: safe to re-run on existing datasets.
    """
    logger.info("Reading DPWH project dataset from %s ...", filepath)
    df = pl.read_parquet(filepath)
    if limit is not None and limit > 0:
        logger.info("Limiting ingestion to first %d rows", limit)
        df = df.head(limit)

    total_in = len(df)
    logger.info("Total input records to process: %d", total_in)

    geocoded_count = 0
    review_queue_count = 0
    rejects_count = 0
    upserted_count = 0

    rows = df.iter_rows(named=True)

    # Process in batches for high throughput and memory stability
    batch: list[dict[str, Any]] = []
    for row in rows:
        batch.append(row)
        if len(batch) >= batch_size:
            res = _process_project_batch(conn, batch)
            geocoded_count += res["geocoded"]
            review_queue_count += res["review_queue"]
            rejects_count += res["rejects"]
            upserted_count += res["upserted"]
            batch.clear()

    if batch:
        res = _process_project_batch(conn, batch)
        geocoded_count += res["geocoded"]
        review_queue_count += res["review_queue"]
        rejects_count += res["rejects"]
        upserted_count += res["upserted"]
        batch.clear()

    logger.info(
        "DPWH Ingestion Complete: Total in: %d | Geocoded: %d | "
        "Review Queue: %d | Rejects: %d | Upserted in projects: %d",
        total_in,
        geocoded_count,
        review_queue_count,
        rejects_count,
        upserted_count,
    )

    assert total_in == (geocoded_count + review_queue_count + rejects_count), (
        f"Row accounting mismatch: total_in ({total_in}) != "
        f"geocoded ({geocoded_count}) + review ({review_queue_count}) + rejects ({rejects_count})"
    )

    return {
        "total_in": total_in,
        "geocoded": geocoded_count,
        "review_queue": review_queue_count,
        "rejects": rejects_count,
        "upserted": upserted_count,
    }


def _process_project_batch(
    conn: psycopg.Connection[Any],
    batch: list[dict[str, Any]],
) -> dict[str, int]:
    """Process a single batch of DPWH project records."""
    valid_records: list[dict[str, Any]] = []
    has_coords_records: list[dict[str, Any]] = []
    no_coords_records: list[dict[str, Any]] = []
    review_entries: list[dict[str, Any]] = []
    reject_count = 0

    for raw_row in batch:
        norm, err = parse_and_normalize_project(raw_row)
        if err is not None or norm is None:
            record_reject(conn, "dpwh_projects", raw_row, err or "Malformed project row")
            reject_count += 1
            continue

        valid_records.append(norm)
        if norm["invalid_coord_reason"] is None:
            has_coords_records.append(norm)
        else:
            no_coords_records.append(norm)
            review_entries.append(
                {
                    "contract_id": norm["contract_id"],
                    "reason": norm["invalid_coord_reason"],
                    "latitude": norm["latitude"],
                    "longitude": norm["longitude"],
                    "raw_payload": norm["raw_payload"],
                }
            )

    geocoded_count = 0

    # Perform set-based PostGIS spatial join for rows with coordinates
    if has_coords_records:
        with conn.cursor() as cur:
            cur.execute(
                """
                CREATE TEMP TABLE tmp_dpwh_pts (
                    contract_id text PRIMARY KEY,
                    lon float8,
                    lat float8
                ) ON COMMIT DROP;
                """
            )
            with cur.copy(
                "COPY tmp_dpwh_pts (contract_id, lon, lat) FROM STDIN"
            ) as copy:
                for rec in has_coords_records:
                    copy.write_row((rec["contract_id"], rec["longitude"], rec["latitude"]))

            cur.execute(
                """
                ALTER TABLE tmp_dpwh_pts ADD COLUMN geom geometry(Point, 4326);
                UPDATE tmp_dpwh_pts SET geom = ST_SetSRID(ST_Point(lon, lat), 4326);
                CREATE INDEX ON tmp_dpwh_pts USING gist(geom);
                ANALYZE tmp_dpwh_pts;
                """
            )

            # Spatial join against barangays: match containing polygon
            cur.execute(
                """
                SELECT
                    p.contract_id,
                    b.psgc_code
                FROM tmp_dpwh_pts p
                LEFT JOIN LATERAL (
                    SELECT psgc_code
                    FROM barangays b
                    WHERE ST_Contains(b.geom, p.geom)
                    LIMIT 1
                ) b ON true;
                """
            )
            matched_map: dict[str, str | None] = {
                row[0]: row[1] for row in cur.fetchall()
            }

        for rec in has_coords_records:
            matched_psgc = matched_map.get(rec["contract_id"])
            rec["geom"] = (
                f"SRID=4326;POINT({rec['longitude']} {rec['latitude']})"
            )
            if matched_psgc is not None:
                rec["psgc_code"] = matched_psgc
                geocoded_count += 1
            else:
                rec["psgc_code"] = None
                review_entries.append(
                    {
                        "contract_id": rec["contract_id"],
                        "reason": "Coordinates outside all barangay boundaries",
                        "latitude": rec["latitude"],
                        "longitude": rec["longitude"],
                        "raw_payload": rec["raw_payload"],
                    }
                )

    for rec in no_coords_records:
        rec["geom"] = None
        rec["psgc_code"] = None

    # Upsert all valid records into projects table
    if valid_records:
        with conn.cursor() as cur:
            cur.executemany(
                """
                INSERT INTO projects (
                    contract_id, title, description, implementing_office,
                    funding_source, budget_php, contract_cost_php, start_date,
                    target_completion_date, physical_progress_pct, geom, psgc_code,
                    source_row_hash, ingested_at
                ) VALUES (
                    %(contract_id)s, %(title)s, %(description)s,
                    %(implementing_office)s, %(funding_source)s, %(budget_php)s,
                    %(contract_cost_php)s, %(start_date)s, %(target_completion_date)s,
                    %(physical_progress_pct)s, %(geom)s, %(psgc_code)s,
                    %(source_row_hash)s, NOW()
                )
                ON CONFLICT (contract_id) DO UPDATE SET
                    title = EXCLUDED.title,
                    description = EXCLUDED.description,
                    implementing_office = EXCLUDED.implementing_office,
                    funding_source = EXCLUDED.funding_source,
                    budget_php = EXCLUDED.budget_php,
                    contract_cost_php = EXCLUDED.contract_cost_php,
                    start_date = EXCLUDED.start_date,
                    target_completion_date = EXCLUDED.target_completion_date,
                    physical_progress_pct = EXCLUDED.physical_progress_pct,
                    geom = EXCLUDED.geom,
                    psgc_code = EXCLUDED.psgc_code,
                    source_row_hash = EXCLUDED.source_row_hash,
                    ingested_at = NOW();
                """,
                valid_records,
            )

    # Sync review queue: clean previous entries for this batch and insert updated review reasons
    if review_entries:
        review_cids = [r["contract_id"] for r in review_entries]
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM project_reviews WHERE contract_id = ANY(%s);",
                (review_cids,),
            )
            cur.executemany(
                """
                INSERT INTO project_reviews (
                    contract_id, reason, latitude, longitude, raw_payload, created_at
                ) VALUES (
                    %(contract_id)s, %(reason)s, %(latitude)s, %(longitude)s,
                    %(raw_payload)s::jsonb, NOW()
                );
                """,
                [
                    {
                        "contract_id": r["contract_id"],
                        "reason": r["reason"],
                        "latitude": r["latitude"],
                        "longitude": r["longitude"],
                        "raw_payload": json.dumps(r["raw_payload"], default=str),
                    }
                    for r in review_entries
                ],
            )

    conn.commit()

    review_count = len(review_entries)
    upserted_count = len(valid_records)

    return {
        "geocoded": geocoded_count,
        "review_queue": review_count,
        "rejects": reject_count,
        "upserted": upserted_count,
    }
