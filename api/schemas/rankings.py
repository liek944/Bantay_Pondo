"""Rankings and leaderboards schemas."""

from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class RankingItem(BaseModel):
    """Individual ranked locality item."""

    model_config = ConfigDict(from_attributes=True)

    rank: int
    psgc_code: str
    name: str
    level: str
    metric_value: Decimal | float
    mismatch_score: Decimal
    national_percentile: Decimal
    total_spend_php: Decimal
    hazard_exposure_pct: Decimal


class RankingsResponse(BaseModel):
    """Leaderboard ranking response."""

    metric: str
    level: str
    year: int
    order: str
    total: int
    items: list[RankingItem]
    data_version: str
