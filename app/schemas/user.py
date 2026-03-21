from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr

from app.models.user import UserRole


class UserCreate(BaseModel):
    """Schema for creating a user."""

    email: EmailStr
    password: str
    first_name: str | None = None
    last_name: str | None = None


class UserUpdate(BaseModel):
    """Schema for partially updating a user."""

    first_name: str | None = None
    last_name: str | None = None
    email: EmailStr | None = None


class UserResponse(BaseModel):
    """Public user response schema."""

    id: uuid.UUID
    email: str
    first_name: str | None
    last_name: str | None
    role: UserRole
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
