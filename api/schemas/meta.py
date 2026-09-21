"""Metadata schemas for dataset provenance and refresh tracking."""

from pydantic import BaseModel, ConfigDict


class DatasetMetaItem(BaseModel):
    """Metadata and provenance record for an ingested dataset."""

    model_config = ConfigDict(from_attributes=True)

    dataset_name: str
    source_url: str
    description: str
    record_count: int
    last_refresh: str | None = None
    sha256: str | None = None


class DatasetsMetaResponse(BaseModel):
    """Meta datasets response container."""

    datasets: list[DatasetMetaItem]
    data_version: str
