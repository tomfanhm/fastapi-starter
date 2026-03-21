from __future__ import annotations

from pydantic import BaseModel


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = "ok"


class PaginationParams(BaseModel):
    """Generic pagination parameters."""

    skip: int = 0
    limit: int = 20


class PaginatedResponse(BaseModel):
    """Generic paginated response wrapper."""

    total: int
    skip: int
    limit: int
    items: list[dict[str, object]]
