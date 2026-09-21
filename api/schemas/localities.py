"""Locality Pydantic models for search, profile, and comparison."""

import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class LocalitySearchResult(BaseModel):
    """Locality item for typeahead search results."""

    model_config = ConfigDict(from_attributes=True)

    psgc_code: str
    name: str
    level: str
    parent_psgc: str | None = None
    land_area_sqkm: float | None = None
    population: int | None = None
    similarity: float | None = None


class LocalitySearchResponse(BaseModel):
    """Typeahead search response container."""

    query: str
    level: str | None = None
    total: int
    items: list[LocalitySearchResult]
    data_version: str


class LocalityMetricDetail(BaseModel):
    """Materialized risk and mismatch score metrics for a locality and year."""

    model_config = ConfigDict(from_attributes=True)

    year: int
    hazard_exposure_pct: Decimal
    flood_pct: Decimal
    landslide_pct: Decimal
    surge_pct: Decimal
    population_at_risk: int
    total_spend_php: Decimal
    spend_per_capita: Decimal
    spend_per_exposed_sqkm: Decimal
    raw_ratio: Decimal
    mismatch_score: Decimal
    national_percentile: Decimal
    computed_at: datetime.datetime


class OfficialSummary(BaseModel):
    """Summary of elected or public official."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    position: str
    district: str | None = None
    term_start: datetime.date | None = None
    term_end: datetime.date | None = None
    party: str | None = None


class LocalityProfile(BaseModel):
    """Administrative profile of a locality."""

    model_config = ConfigDict(from_attributes=True)

    psgc_code: str
    name: str
    level: str
    parent_psgc: str | None = None
    parent_name: str | None = None
    land_area_sqkm: float | None = None
    population: int | None = None
    population_year: int | None = None


class LocalityProfileResponse(BaseModel):
    """Locality detail response combining profile, metrics history, and officials."""

    profile: LocalityProfile
    metrics: list[LocalityMetricDetail]
    officials: list[OfficialSummary]
    data_version: str


class LocalityComparisonItem(BaseModel):
    """Locality comparison entity container."""

    profile: LocalityProfile
    metric: LocalityMetricDetail | None = None


class LocalityMetricDelta(BaseModel):
    """Deltas between two localities."""

    mismatch_score_delta: Decimal | None = None
    total_spend_php_delta: Decimal | None = None
    hazard_exposure_pct_delta: Decimal | None = None
    spend_per_capita_delta: Decimal | None = None


class LocalityComparisonResponse(BaseModel):
    """Side-by-side comparison response between two localities."""

    year: int
    locality_a: LocalityComparisonItem
    locality_b: LocalityComparisonItem
    deltas: LocalityMetricDelta
    data_version: str
