"""Contractor Pydantic models with district concentration metrics."""

import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from api.schemas.projects import ProjectSummary


class ContractorSummary(BaseModel):
    """Core contractor entity profile."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    normalized_name: str
    raw_names: list[str]
    address: str | None = None
    first_seen: datetime.date | None = None
    total_contracts: int
    total_value_php: Decimal


class DistrictConcentrationItem(BaseModel):
    """Market share of contractor within a specific implementing district or office."""

    district: str
    contract_count: int
    total_value_php: Decimal
    share_pct: float


class DistrictConcentration(BaseModel):
    """Herfindahl-Hirschman Index (HHI) concentration metrics."""

    hhi: float
    normalized_hhi: float
    interpretation: str
    market_shares: list[DistrictConcentrationItem]


class ContractorProfileResponse(BaseModel):
    """Complete profile response for a contractor."""

    profile: ContractorSummary
    contracts: list[ProjectSummary]
    district_concentration: DistrictConcentration
    data_version: str
