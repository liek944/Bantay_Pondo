"""Metadata and provenance service for ingested datasets."""

import json
from pathlib import Path
from typing import Any

from api.schemas.meta import DatasetMetaItem, DatasetsMetaResponse
from db.session import get_async_db_connection

DATA_DIR = Path("data/raw")
MANIFEST_PATH = DATA_DIR / "manifest.json"


async def get_datasets_meta(data_version: str) -> DatasetsMetaResponse:
    """Retrieve metadata, row counts, and source provenance for all platform datasets."""
    manifest: dict[str, Any] = {}
    if MANIFEST_PATH.exists():
        try:
            with open(MANIFEST_PATH, encoding="utf-8") as f:
                manifest = json.load(f)
        except Exception:
            manifest = {}

    counts: dict[str, int] = {}
    async with get_async_db_connection() as conn:
        async with conn.cursor() as cur:
            for tbl in ("projects", "hazard_zones", "barangays", "procurement_awards"):
                await cur.execute(f"SELECT COUNT(*) FROM {tbl}")
                r = await cur.fetchone()
                counts[tbl] = int(r[0]) if r else 0

    dpwh_manifest = manifest.get("dpwh_transparency_data.parquet", {})

    datasets = [
        DatasetMetaItem(
            dataset_name="DPWH Infrastructure Projects",
            source_url="https://huggingface.co/datasets/bettergovph/dpwh-transparency-data",
            description=(
                "DPWH transparency dataset tracking civil works projects, budgets, "
                "contract costs, physical progress, and geolocations."
            ),
            record_count=counts.get("projects", 0),
            last_refresh=dpwh_manifest.get("downloaded_at"),
            sha256=dpwh_manifest.get("sha256"),
        ),
        DatasetMetaItem(
            dataset_name="Project NOAH Hazard Maps",
            source_url="https://noah.up.edu.ph",
            description=(
                "Flood, landslide, and storm surge hazard exposure maps classified "
                "across severity levels 1, 2, and 3."
            ),
            record_count=counts.get("hazard_zones", 0),
            last_refresh="2026-09-20T11:00:00Z",
            sha256=manifest.get("noah_hazards.zip", {}).get("sha256"),
        ),
        DatasetMetaItem(
            dataset_name="PSGC Administrative Boundaries",
            source_url="https://psa.gov.ph/classification/psgc",
            description=(
                "Philippine Standard Geographic Code (PSGC) administrative tiers: "
                "regions, provinces, municipalities/cities, and barangays."
            ),
            record_count=counts.get("barangays", 0),
            last_refresh="2026-09-20T10:00:00Z",
            sha256=manifest.get("psgc_boundaries.geojson", {}).get("sha256"),
        ),
        DatasetMetaItem(
            dataset_name="PhilGEPS Procurement Awards",
            source_url="https://notices.philgeps.gov.ph",
            description=(
                "Philippine Government Electronic Procurement System (PhilGEPS) "
                "procurement notices and award registries."
            ),
            record_count=counts.get("procurement_awards", 0),
            last_refresh=None,
            sha256=None,
        ),
    ]

    return DatasetsMetaResponse(
        datasets=datasets,
        data_version=data_version,
    )
