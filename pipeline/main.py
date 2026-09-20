"""Bantay Pondo Data Pipeline CLI runner."""

import argparse
import logging
import sys
from pathlib import Path
from typing import TypedDict

from db.session import get_db_connection
from pipeline.stages.fetch import fetch_file
from pipeline.stages.ingest_dpwh import ProjectIngestionResult, ingest_dpwh_projects
from pipeline.stages.ingest_noah import ingest_noah_hazards
from pipeline.stages.ingest_psgc import ingest_geojson_boundaries

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("pipeline")

RAW_DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"

PSGC_URLS: dict[str, str] = {
    "regions": "https://github.com/bendlikeabamboo/barangay-boundaries-repository/releases/download/v2026.4.13.0/regions.geojson",
    "provinces": "https://github.com/bendlikeabamboo/barangay-boundaries-repository/releases/download/v2026.4.13.0/provinces.geojson",
    "municipalities": "https://github.com/bendlikeabamboo/barangay-boundaries-repository/releases/download/v2026.4.13.0/municipalities.geojson",
    "barangays": "https://github.com/bendlikeabamboo/barangay-boundaries-repository/releases/download/v2026.4.13.0/barangays.geojson",
}


class HazardDatasetConfig(TypedDict):
    """Configuration specification for a Project NOAH hazard source dataset."""

    url: str
    filename: str
    hazard_type: str
    severity_level: int
    source_dataset: str
    source_year: int


NOAH_DATASETS: list[HazardDatasetConfig] = [
    {
        "url": "https://huggingface.co/datasets/bettergovph/project-noah-hazard-maps/resolve/main/Flood/100yr/Batanes.zip",
        "filename": "flood_100yr_batanes.zip",
        "hazard_type": "flood",
        "severity_level": 3,
        "source_dataset": "Project NOAH Flood 100yr",
        "source_year": 2024,
    },
    {
        "url": "https://huggingface.co/datasets/bettergovph/project-noah-hazard-maps/resolve/main/Landslide/LandslideHazards/Batanes.zip",
        "filename": "landslide_batanes.zip",
        "hazard_type": "landslide",
        "severity_level": 2,
        "source_dataset": "Project NOAH Landslide Hazards",
        "source_year": 2024,
    },
    {
        "url": "https://huggingface.co/datasets/bettergovph/project-noah-hazard-maps/resolve/main/Storm%20Surge/StormSurgeAdvisory1/Cagayan.zip",
        "filename": "storm_surge_advisory1_cagayan.zip",
        "hazard_type": "storm_surge",
        "severity_level": 1,
        "source_dataset": "Project NOAH Storm Surge Advisory 1",
        "source_year": 2024,
    },
]


DPWH_PROJECTS_URL = (
    "https://huggingface.co/datasets/bettergovph/dpwh-transparency-data/resolve/main/dpwh_transparency_data.parquet"
)


def run_ingest_boundaries(levels: list[str] | None = None) -> dict[str, int]:
    """Fetch and ingest PSGC administrative boundaries with row-count assertions."""
    if not levels:
        levels = ["regions", "provinces", "municipalities", "barangays"]

    counts: dict[str, int] = {}
    with get_db_connection() as conn:
        for lvl in levels:
            if lvl in PSGC_URLS:
                logger.info("--- Stage: Fetch & Ingest %s ---", lvl)
                res = fetch_file(PSGC_URLS[lvl], RAW_DATA_DIR, filename=f"{lvl}.geojson")
                count = ingest_geojson_boundaries(conn, Path(res["path"]), lvl)
                counts[lvl] = count
                logger.info("Stage %s SUCCESS with %d rows asserted.", lvl, count)
    return counts


def run_ingest_hazards(
    datasets: list[HazardDatasetConfig] | None = None,
) -> dict[str, int]:
    """Fetch and ingest Project NOAH hazard datasets with row-count assertions."""
    if not datasets:
        datasets = NOAH_DATASETS

    counts: dict[str, int] = {}
    with get_db_connection() as conn:
        for item in datasets:
            logger.info(
                "--- Stage: Fetch & Ingest Hazard %s (%s) ---",
                item["filename"],
                item["hazard_type"],
            )
            res = fetch_file(item["url"], RAW_DATA_DIR, filename=item["filename"])
            count = ingest_noah_hazards(
                conn=conn,
                filepath=Path(res["path"]),
                hazard_type=item["hazard_type"],
                severity_level=item["severity_level"],
                source_dataset=item["source_dataset"],
                source_year=item["source_year"],
            )
            counts[item["hazard_type"]] = count
            logger.info(
                "Stage hazard %s SUCCESS with %d rows asserted.",
                item["hazard_type"],
                count,
            )
    return counts


def run_ingest_projects(limit: int | None = None) -> ProjectIngestionResult:
    """Fetch and ingest DPWH infrastructure projects with PostGIS spatial join and review queue."""
    logger.info("--- Stage: Fetch & Ingest DPWH Infrastructure Projects ---")
    res = fetch_file(
        DPWH_PROJECTS_URL,
        RAW_DATA_DIR,
        filename="dpwh_transparency_data.parquet",
    )
    with get_db_connection() as conn:
        stats = ingest_dpwh_projects(
            conn=conn,
            filepath=Path(res["path"]),
            limit=limit,
        )
    logger.info(
        "Stage DPWH projects SUCCESS: %d in, %d geocoded, %d in review queue, %d rejects",
        stats["total_in"],
        stats["geocoded"],
        stats["review_queue"],
        stats["rejects"],
    )
    return stats


def main() -> None:
    """CLI runner entrypoint."""
    parser = argparse.ArgumentParser(description="Bantay Pondo Data Pipeline CLI")
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser(
        "ingest-boundaries", help="Fetch and ingest PSGC administrative boundaries"
    )
    subparsers.add_parser(
        "ingest-hazards", help="Fetch and ingest Project NOAH hazard polygons"
    )
    projects_parser = subparsers.add_parser(
        "ingest-projects",
        help="Fetch and ingest DPWH infrastructure projects with spatial join",
    )
    projects_parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit number of project rows to ingest",
    )

    all_parser = subparsers.add_parser("all", help="Execute complete ingestion pipeline")
    all_parser.add_argument(
        "--limit-projects",
        type=int,
        default=None,
        help="Limit number of project rows to ingest during all",
    )

    args = parser.parse_args()

    if args.command == "ingest-boundaries":
        run_ingest_boundaries()
    elif args.command == "ingest-hazards":
        run_ingest_hazards()
    elif args.command == "ingest-projects":
        run_ingest_projects(limit=args.limit)
    elif args.command == "all":
        run_ingest_boundaries()
        run_ingest_hazards()
        run_ingest_projects(limit=args.limit_projects)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
