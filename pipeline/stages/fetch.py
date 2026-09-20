"""Data fetching stage with content hashing and idempotency."""

import datetime
import hashlib
import json
import logging
from pathlib import Path
from typing import Any

import httpx

logger = logging.getLogger(__name__)


def compute_sha256(filepath: Path) -> str:
    """Compute SHA256 checksum of a file in binary mode."""
    sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            sha256.update(chunk)
    return sha256.hexdigest()


def fetch_file(
    url: str,
    target_dir: Path,
    filename: str | None = None,
    force_download: bool = False,
    timeout: float = 120.0,
) -> dict[str, Any]:
    """Download a source file into target_dir with SHA256 content verification.

    Skips download if file already exists with same size and hash registered in manifest.
    """
    target_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = target_dir / "manifest.json"

    manifest: dict[str, Any] = {}
    if manifest_path.exists():
        try:
            with open(manifest_path, encoding="utf-8") as f:
                manifest = json.load(f)
        except Exception as exc:
            logger.warning("Could not read existing manifest, initializing empty: %s", exc)
            manifest = {}

    if not filename:
        filename = url.rstrip("/").split("/")[-1].split("?")[0]
        if not filename:
            filename = "downloaded_resource"

    target_path = target_dir / filename

    # Check if cached and unchanged
    if not force_download and target_path.exists() and filename in manifest:
        existing_hash = compute_sha256(target_path)
        if existing_hash == manifest[filename].get("sha256"):
            logger.info(
                "File %s is unchanged (SHA256: %s). Skipping download.",
                filename,
                existing_hash,
            )
            return {
                "filename": filename,
                "path": str(target_path),
                "sha256": existing_hash,
                "size_bytes": target_path.stat().st_size,
                "cached": True,
            }

    logger.info("Downloading %s from %s ...", filename, url)
    headers = {"User-Agent": "BantayPondo-Pipeline/1.0"}
    temp_target = target_dir / f"{filename}.part"

    with httpx.Client(timeout=timeout, follow_redirects=True) as client:
        with client.stream("GET", url, headers=headers) as response:
            response.raise_for_status()
            with open(temp_target, "wb") as f:
                for chunk in response.iter_bytes(chunk_size=65536):
                    f.write(chunk)

    temp_target.rename(target_path)
    file_hash = compute_sha256(target_path)
    file_size = target_path.stat().st_size

    manifest[filename] = {
        "url": url,
        "sha256": file_hash,
        "size_bytes": file_size,
        "downloaded_at": datetime.datetime.now(datetime.UTC).isoformat(),
    }

    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    logger.info("Saved %s (SHA256: %s, %d bytes)", filename, file_hash, file_size)

    return {
        "filename": filename,
        "path": str(target_path),
        "sha256": file_hash,
        "size_bytes": file_size,
        "cached": False,
    }
