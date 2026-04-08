from __future__ import annotations

from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = "ok"
    database_connected: bool = True


class PaginationParams(BaseModel):
    """Generic pagination parameters."""

    skip: int = 0
    limit: int = 20


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response wrapper."""

    total: int
    skip: int
    limit: int
    items: list[T]
