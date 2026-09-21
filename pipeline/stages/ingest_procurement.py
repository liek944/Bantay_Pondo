"""Ingestion stage for PhilGEPS procurement awards with contractor linking and PSGC mapping."""

import datetime
import logging
import math
import re
from decimal import Decimal
from pathlib import Path
from typing import Any, TypedDict

import polars as pl
import psycopg

from pipeline.stages.dedupe_contractors import normalize_contractor_name
from pipeline.stages.ingest_psgc import record_reject

logger = logging.getLogger(__name__)


class ProcurementIngestionResult(TypedDict):
    """Statistics recorded during PhilGEPS procurement awards ingestion."""

    total_in: int
    inserted: int
    contractors_linked: int
    projects_updated: int
    rejects: int


def _parse_date(value: Any) -> datetime.date | None:
    """Safely parse award date into datetime.date."""
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


def parse_and_normalize_award(
    row: dict[str, Any],
) -> tuple[dict[str, Any] | None, str | None]:
    """Validate and normalize a raw PhilGEPS procurement award row.

    Returns:
        (normalized_dict, None) on success.
        (None, failure_reason) if row is malformed and must be quarantined.
    """
    raw_title = row.get("award_title") or row.get("notice_title")
    if not raw_title or not str(raw_title).strip():
        return None, "Missing award_title and notice_title"

    title = str(raw_title).strip()

    ref_raw = row.get("reference_id") or row.get("contract_no")
    reference_id = str(ref_raw).strip() if ref_raw is not None else None

    amount_raw = row.get("contract_amount")
    award_amount_php: Decimal | None = None
    if amount_raw is not None:
        try:
            val = float(amount_raw)
            if not math.isnan(val):
                award_amount_php = Decimal(str(round(val, 2)))
        except (ValueError, TypeError):
            award_amount_php = None

    award_date = _parse_date(row.get("award_date"))

    org_raw = row.get("organization_name")
    procuring_entity = str(org_raw).strip() if org_raw is not None else None

    awardee_raw = row.get("awardee_name")
    awardee_name = str(awardee_raw).strip() if awardee_raw is not None else None

    area_raw = row.get("area_of_delivery")
    area_of_delivery = str(area_raw).strip() if area_raw is not None else None

    return {
        "reference_id": reference_id,
        "title": title,
        "award_amount_php": award_amount_php,
        "award_date": award_date,
        "procuring_entity": procuring_entity,
        "awardee_name": awardee_name,
        "area_of_delivery": area_of_delivery,
        "raw_payload": row,
    }, None


def load_psgc_province_map(conn: psycopg.Connection[Any]) -> dict[str, str]:
    """Load normalized province and region names mapped to their canonical PSGC codes."""
    prov_map: dict[str, str] = {}
    with conn.cursor() as cur:
        cur.execute("SELECT psgc_code, name FROM provinces;")
        for code, name in cur.fetchall():
            norm_name = re.sub(r"[^A-Z0-9]", "", name.upper())
            prov_map[norm_name] = code

        cur.execute("SELECT psgc_code, name FROM regions;")
        for code, name in cur.fetchall():
            norm_name = re.sub(r"[^A-Z0-9]", "", name.upper())
            prov_map[norm_name] = code
            # Also register short forms like 'REGIONXIII', 'REGIONIVA', 'NCR'
            short = re.sub(r"\(.*?\)", "", name).strip().upper()
            short_norm = re.sub(r"[^A-Z0-9]", "", short)
            if short_norm:
                prov_map[short_norm] = code

    return prov_map


def match_psgc_code(area_of_delivery: str | None, prov_map: dict[str, str]) -> str | None:
    """Resolve PSGC code from area of delivery string."""
    if not area_of_delivery:
        return None
    cleaned = re.sub(r"[^A-Z0-9]", "", area_of_delivery.upper())
    if cleaned in prov_map:
        return prov_map[cleaned]

    # Substring search if exact match not found
    for name_key, code in prov_map.items():
        if name_key in cleaned or cleaned in name_key:
            return code
    return None


def resolve_or_create_contractor(
    conn: psycopg.Connection[Any],
    awardee_name: str | None,
    contractor_cache: dict[str, int],
) -> int | None:
    """Resolve existing contractor by normalized name or insert new contractor entity."""
    if not awardee_name:
        return None

    cleaned_raw = awardee_name.strip()
    if cleaned_raw in contractor_cache:
        return contractor_cache[cleaned_raw]

    norm = normalize_contractor_name(cleaned_raw)
    if not norm:
        return None

    if norm in contractor_cache:
        return contractor_cache[norm]

    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT id, raw_names
            FROM contractors
            WHERE normalized_name = %(norm)s
               OR (normalized_name %% %(norm)s AND similarity(normalized_name, %(norm)s) > 0.9)
            ORDER BY
                (normalized_name = %(norm)s) DESC,
                similarity(normalized_name, %(norm)s) DESC
            LIMIT 1;
            """,
            {"norm": norm},
        )
        row = cur.fetchone()
        if row:
            cid = int(row[0])
            raw_list = list(row[1]) if row[1] else []
            if cleaned_raw not in raw_list:
                raw_list.append(cleaned_raw)
                cur.execute(
                    "UPDATE contractors SET raw_names = %s WHERE id = %s;",
                    (raw_list, cid),
                )
        else:
            cur.execute(
                """
                INSERT INTO contractors (
                    normalized_name, raw_names, address, total_contracts, total_value_php
                ) VALUES (
                    %s, %s, NULL, 0, 0
                ) RETURNING id;
                """,
                (norm, [cleaned_raw]),
            )
            inserted_row = cur.fetchone()
            assert inserted_row is not None
            cid = int(inserted_row[0])

    contractor_cache[cleaned_raw] = cid
    contractor_cache[norm] = cid
    return cid


def ingest_philgeps_awards(
    conn: psycopg.Connection[Any],
    filepath: Path,
    limit: int | None = None,
    batch_size: int = 5000,
) -> ProcurementIngestionResult:
    """Ingest PhilGEPS procurement awards from parquet into database with contractor linking.

    - Resolves contractor_id via normalization and pg_trgm matching against contractors table.
    - Resolves psgc_code from area_of_delivery matching provinces/regions.
    - Quarantines malformed rows into rejects table without silent drops.
    - Reconciles DPWH contract_cost_php when matching contract ID is detected.
    - Idempotent: safe to re-run on existing datasets.
    """
    logger.info("Reading PhilGEPS procurement dataset from %s ...", filepath)
    df = pl.read_parquet(filepath)
    if limit is not None and limit > 0:
        logger.info("Limiting PhilGEPS awards ingestion to first %d rows", limit)
        df = df.head(limit)

    total_in = len(df)
    logger.info("Total PhilGEPS award records to process: %d", total_in)

    prov_map = load_psgc_province_map(conn)
    contractor_cache: dict[str, int] = {}

    inserted_count = 0
    rejects_count = 0
    contractors_linked_count = 0
    projects_updated_count = 0

    valid_batch: list[dict[str, Any]] = []

    for raw_row in df.iter_rows(named=True):
        norm, err = parse_and_normalize_award(raw_row)
        if err is not None or norm is None:
            record_reject(conn, "philgeps_awards", raw_row, err or "Malformed award row")
            rejects_count += 1
            continue

        cid = resolve_or_create_contractor(conn, norm["awardee_name"], contractor_cache)
        if cid is not None:
            contractors_linked_count += 1
        norm["contractor_id"] = cid
        norm["psgc_code"] = match_psgc_code(norm["area_of_delivery"], prov_map)

        valid_batch.append(norm)
        if len(valid_batch) >= batch_size:
            cnt, updated_projs = _flush_award_batch(conn, valid_batch)
            inserted_count += cnt
            projects_updated_count += updated_projs
            valid_batch.clear()

    if valid_batch:
        cnt, updated_projs = _flush_award_batch(conn, valid_batch)
        inserted_count += cnt
        projects_updated_count += updated_projs
        valid_batch.clear()

    conn.commit()

    logger.info(
        "PhilGEPS Ingestion Complete: Total in: %d | Inserted: %d | "
        "Linked Contractors: %d | Updated Projects: %d | Rejects: %d",
        total_in,
        inserted_count,
        contractors_linked_count,
        projects_updated_count,
        rejects_count,
    )

    assert total_in == (inserted_count + rejects_count), (
        f"Row accounting mismatch: total_in ({total_in}) != "
        f"inserted ({inserted_count}) + rejects ({rejects_count})"
    )

    return {
        "total_in": total_in,
        "inserted": inserted_count,
        "contractors_linked": contractors_linked_count,
        "projects_updated": projects_updated_count,
        "rejects": rejects_count,
    }


def _flush_award_batch(
    conn: psycopg.Connection[Any],
    batch: list[dict[str, Any]],
) -> tuple[int, int]:
    """Insert a batch of normalized procurement awards and reconcile matching DPWH projects."""
    if not batch:
        return 0, 0

    inserted = 0
    updated_projs = 0

    with conn.cursor() as cur:
        cur.executemany(
            """
            INSERT INTO procurement_awards (
                reference_id, contractor_id, title, award_amount_php,
                award_date, procuring_entity, psgc_code
            ) VALUES (
                %(reference_id)s, %(contractor_id)s, %(title)s, %(award_amount_php)s,
                %(award_date)s, %(procuring_entity)s, %(psgc_code)s
            );
            """,
            batch,
        )
        inserted = len(batch)

        # Check for matching DPWH contract IDs in reference_id or title
        dpwh_matches: list[tuple[Decimal, str]] = []
        for item in batch:
            amount = item["award_amount_php"]
            if amount is None or amount <= 0:
                continue

            ref_id = item["reference_id"]
            title = item["title"]
            candidate_id: str | None = None

            # Detect DPWH contractId patterns e.g. 21NA0052, 24JE0007, 25GF00009
            m = re.search(r"\b\d{2}[A-Z]{1,3}\d{4,5}\b", f"{ref_id or ''} {title}")
            if m:
                candidate_id = m.group(0)

            if candidate_id:
                dpwh_matches.append((amount, candidate_id))

        if dpwh_matches:
            cur.executemany(
                """
                UPDATE projects
                SET contract_cost_php = %s
                WHERE contract_id = %s
                  AND contract_cost_php IS NULL;
                """,
                dpwh_matches,
            )
            updated_projs = len(dpwh_matches)

    return inserted, updated_projs
