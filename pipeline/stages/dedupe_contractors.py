"""Contractor deduplication stage with suffix stripping, trigram matching, and project links."""

import logging
import re
from pathlib import Path
from typing import Any, TypedDict

import polars as pl
import psycopg

logger = logging.getLogger(__name__)


class ContractorDedupeResult(TypedDict):
    """Statistics recorded during contractor deduplication and project linking."""

    total_raw: int
    canonical_entities: int
    projects_linked: int


def py_trigrams(s: str) -> set[str]:
    """Extract character trigrams with pg_trgm padding (2 spaces prefix, 1 space suffix)."""
    padded = f"  {s} "
    if len(padded) < 3:
        return set()
    return {padded[i : i + 3] for i in range(len(padded) - 2)}


def compute_trigram_similarity(s1: str, s2: str) -> float:
    """Compute trigram Jaccard similarity between two strings, matching pg_trgm similarity()."""
    if s1 == s2:
        return 1.0
    t1 = py_trigrams(s1)
    t2 = py_trigrams(s2)
    if not t1 and not t2:
        return 1.0
    if not t1 or not t2:
        return 0.0
    intersection = len(t1 & t2)
    union = len(t1 | t2)
    return intersection / union


def normalize_contractor_name(raw: str | None) -> str:
    """Normalize a raw contractor name according to SPEC requirements:

    1. Uppercase.
    2. Strip parenthetical registration/revocation codes: (12345), ([REVOKED] 12345).
    3. Strip former names in parentheses: (FORMERLY: ...).
    4. Handle joint ventures / consortia separated by ' / '.
    5. Strip legal suffixes: INC, CORP, CO, ENTERPRISES, CONSTRUCTION and common variants.
    6. Collapse all whitespace.
    """
    if not raw:
        return ""

    s = raw.upper().strip()
    if not s:
        return ""

    # Strip parenthetical registration / revocation numbers like (12345), ([REVOKED] 12345)
    s = re.sub(r"\s*\(\s*(?:\[?[A-Z]+\]?\s*)?\d+\s*\)", "", s)
    # Strip former name parentheticals like (FORMERLY: ...), (FORMERLY ...)
    s = re.sub(r"\s*\(\s*FORMERLY(?::|\b)[^)]*\)?", "", s)

    # Process joint venture components separately
    parts = s.split(" / ")
    norm_parts: list[str] = []

    # Legal suffixes to strip from word boundaries at the tail of each entity name
    suffix_pattern = (
        r"\b(?:"
        r"INCORPORATED|INC\.?|"
        r"CORPORATION|CORP\.?|"
        r"COMPANY|CO\.?|"
        r"ENTERPRISES|ENTERPRISE|"
        r"CONSTRUCTION"
        r")\b"
    )

    for part in parts:
        p = part.strip()
        prev = None
        while prev != p:
            prev = p
            # Strip trailing punctuation, commas, dots, ampersands, slashes, hyphens
            p = re.sub(r"[\s,\./&+-]+$", "", p)
            # Strip legal suffix if located at the end of the string
            p = re.sub(r"[\s,\./&+-]+" + suffix_pattern + r"[\s,\./&+-]*$", "", p)

        # Collapse intra-word whitespace
        p = re.sub(r"\s+", " ", p).strip()
        if p:
            norm_parts.append(p)

    if not norm_parts:
        return re.sub(r"\s+", " ", s).strip()

    return " / ".join(norm_parts)


def dedupe_and_upsert_contractors(
    conn: psycopg.Connection[Any],
    raw_contractor_names: list[str],
) -> dict[str, int]:
    """Cluster raw contractor names into canonical entities using pg_trgm similarity > 0.9.

    Preserves all raw variants in `contractors.raw_names`.
    Returns a dictionary mapping each raw contractor string to its canonical contractor ID.
    """
    raw_to_id: dict[str, int] = {}
    cleaned_raw = [r.strip() for r in raw_contractor_names if r and r.strip()]
    if not cleaned_raw:
        return raw_to_id

    # Group raw variants by their normalized representation
    norm_to_raws: dict[str, set[str]] = {}
    for raw in cleaned_raw:
        norm = normalize_contractor_name(raw)
        if not norm:
            continue
        norm_to_raws.setdefault(norm, set()).add(raw)

    logger.info(
        "Clustering %d raw contractor names across %d distinct normalized forms...",
        len(cleaned_raw),
        len(norm_to_raws),
    )

    with conn.cursor() as cur:
        # Set pg_trgm threshold to 0.9 as specified in SPEC
        cur.execute("SELECT set_limit(0.9);")

        for norm_name, raw_set in norm_to_raws.items():
            # Check for existing canonical contractor matching exact norm or trigram sim > 0.9
            cur.execute(
                """
                SELECT id, normalized_name, raw_names
                FROM contractors
                WHERE normalized_name = %(norm)s
                   OR (normalized_name %% %(norm)s AND similarity(normalized_name, %(norm)s) > 0.9)
                ORDER BY
                    (normalized_name = %(norm)s) DESC,
                    similarity(normalized_name, %(norm)s) DESC
                LIMIT 1;
                """,
                {"norm": norm_name},
            )
            matched = cur.fetchone()

            if matched:
                contractor_id = int(matched[0])
                existing_raws = set(matched[2]) if matched[2] else set()
                merged_raws = sorted(existing_raws | raw_set)
                if len(merged_raws) > len(existing_raws):
                    cur.execute(
                        """
                        UPDATE contractors
                        SET raw_names = %(merged)s
                        WHERE id = %(id)s;
                        """,
                        {"merged": merged_raws, "id": contractor_id},
                    )
            else:
                cur.execute(
                    """
                    INSERT INTO contractors (
                        normalized_name, raw_names, address, total_contracts, total_value_php
                    ) VALUES (
                        %(norm)s, %(raws)s, NULL, 0, 0
                    ) RETURNING id;
                    """,
                    {"norm": norm_name, "raws": sorted(raw_set)},
                )
                row = cur.fetchone()
                assert row is not None
                contractor_id = int(row[0])

            # Map all raw variants and the normalized string to this canonical ID
            for raw in raw_set:
                raw_to_id[raw] = contractor_id
            raw_to_id[norm_name] = contractor_id

    conn.commit()
    return raw_to_id


def link_projects_to_contractors(
    conn: psycopg.Connection[Any],
    contract_contractor_pairs: list[tuple[str, str]],
    raw_to_id: dict[str, int],
    batch_size: int = 5000,
) -> int:
    """Link projects to their canonical contractor_id in batches."""
    linked_count = 0
    updates: list[tuple[int, str]] = []

    for contract_id, raw_contractor in contract_contractor_pairs:
        if not raw_contractor:
            continue
        c_id = raw_to_id.get(raw_contractor.strip()) or raw_to_id.get(
            normalize_contractor_name(raw_contractor)
        )
        if c_id is not None:
            updates.append((c_id, contract_id))

    if not updates:
        return 0

    logger.info("Updating %d projects with canonical contractor IDs...", len(updates))

    with conn.cursor() as cur:
        for i in range(0, len(updates), batch_size):
            chunk = updates[i : i + batch_size]
            cur.executemany(
                """
                UPDATE projects
                SET contractor_id = %s
                WHERE contract_id = %s;
                """,
                chunk,
            )
            linked_count += len(chunk)

    conn.commit()
    return linked_count


def update_contractor_aggregated_metrics(conn: psycopg.Connection[Any]) -> None:
    """Recalculate total_contracts, total_value_php, and first_seen on contractors."""
    logger.info("Recalculating contractor aggregate statistics from linked projects...")
    with conn.cursor() as cur:
        cur.execute(
            """
            UPDATE contractors c
            SET
                total_contracts = sub.cnt,
                total_value_php = sub.total_val,
                first_seen = sub.min_date
            FROM (
                SELECT
                    contractor_id,
                    COUNT(*) AS cnt,
                    COALESCE(SUM(COALESCE(contract_cost_php, budget_php)), 0) AS total_val,
                    MIN(start_date) AS min_date
                FROM projects
                WHERE contractor_id IS NOT NULL
                GROUP BY contractor_id
            ) sub
            WHERE c.id = sub.contractor_id;
            """
        )
    conn.commit()


def dedupe_contractors(
    conn: psycopg.Connection[Any],
    filepath: Path | None = None,
    limit: int | None = None,
) -> ContractorDedupeResult:
    """Execute complete contractor deduplication workflow:

    1. Extract contractor names from DPWH parquet dataset or projects database.
    2. Deduplicate and cluster into canonical entities with pg_trgm similarity > 0.9.
    3. Update projects table with contractor_id foreign keys.
    4. Materialize aggregate contractor metrics (total contracts, total value, first seen).
    """
    if filepath is None:
        filepath = Path("data/raw/dpwh_transparency_data.parquet")

    logger.info("Reading contractor information from %s ...", filepath)
    df = pl.read_parquet(filepath, columns=["contractId", "contractor"])
    if limit is not None and limit > 0:
        logger.info("Limiting contractor dedupe to first %d records", limit)
        df = df.head(limit)

    contract_contractor_pairs: list[tuple[str, str]] = []
    unique_raw_names: set[str] = set()

    for row in df.iter_rows(named=True):
        cid = str(row["contractId"]).strip()
        raw_c = row.get("contractor")
        if raw_c is not None:
            raw_c_str = str(raw_c).strip()
            if raw_c_str:
                contract_contractor_pairs.append((cid, raw_c_str))
                unique_raw_names.add(raw_c_str)

    logger.info(
        "Extracted %d project pairs with %d unique contractor names.",
        len(contract_contractor_pairs),
        len(unique_raw_names),
    )

    raw_to_id = dedupe_and_upsert_contractors(conn, list(unique_raw_names))
    linked_count = link_projects_to_contractors(
        conn, contract_contractor_pairs, raw_to_id
    )
    update_contractor_aggregated_metrics(conn)

    with conn.cursor() as cur:
        cur.execute("SELECT count(*) FROM contractors;")
        count_row = cur.fetchone()
        assert count_row is not None
        total_canonical = int(count_row[0])

    logger.info(
        "Contractor deduplication complete: %d raw -> %d canonical. Linked %d projects.",
        len(unique_raw_names),
        total_canonical,
        linked_count,
    )

    return {
        "total_raw": len(unique_raw_names),
        "canonical_entities": total_canonical,
        "projects_linked": linked_count,
    }
