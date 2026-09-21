"""Project Pydantic models for listings, details, flags, and procurement awards."""

import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict


class ProjectSummary(BaseModel):
    """Compact summary of a project for locality listings."""

    model_config = ConfigDict(from_attributes=True)

    contract_id: str
    title: str
    implementing_office: str | None = None
    funding_source: str | None = None
    budget_php: Decimal | None = None
    contract_cost_php: Decimal | None = None
    start_date: datetime.date | None = None
    target_completion_date: datetime.date | None = None
    physical_progress_pct: Decimal | None = None
    psgc_code: str | None = None
    contractor_id: int | None = None
    contractor_name: str | None = None


class ProjectFlag(BaseModel):
    """Rule-based anomaly or risk flag (informative, never a fraud verdict)."""

    code: str
    message: str
    severity: str
    details: dict[str, Any] = {}


class ProcurementAwardSummary(BaseModel):
    """Procurement award associated with project or contractor."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    reference_id: str | None = None
    title: str
    award_amount_php: Decimal | None = None
    award_date: datetime.date | None = None
    procuring_entity: str | None = None


class ProjectDetailResponse(BaseModel):
    """Full detail view for a specific DPWH project."""

    model_config = ConfigDict(from_attributes=True)

    contract_id: str
    title: str
    description: str | None = None
    implementing_office: str | None = None
    funding_source: str | None = None
    budget_php: Decimal | None = None
    contract_cost_php: Decimal | None = None
    start_date: datetime.date | None = None
    target_completion_date: datetime.date | None = None
    physical_progress_pct: Decimal | None = None
    latitude: float | None = None
    longitude: float | None = None
    psgc_code: str | None = None
    barangay_name: str | None = None
    municipality_name: str | None = None
    province_name: str | None = None
    region_name: str | None = None
    contractor_id: int | None = None
    contractor_name: str | None = None
    flags: list[ProjectFlag]
    related_awards: list[ProcurementAwardSummary]
    ingested_at: datetime.datetime
    data_version: str
