from pydantic import BaseModel, ConfigDict


class BaseResponse(BaseModel):
    """Base response model guaranteeing data_version presence."""

    model_config = ConfigDict(from_attributes=True)

    data_version: str


class PaginatedResponse[T](BaseModel):
    """Generic paginated response structure."""

    model_config = ConfigDict(from_attributes=True)

    items: list[T]
    total: int
    page: int
    page_size: int
    total_pages: int
    data_version: str


class ErrorResponse(BaseModel):
    """Standard error response model."""

    detail: str
    data_version: str
