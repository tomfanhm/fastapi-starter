from __future__ import annotations

import enum

from sqlalchemy import Enum, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class UserRole(str, enum.Enum):
    """User role enumeration."""

    USER = "user"
    ADMIN = "admin"


class User(Base):
    """User database model."""

    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(320), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    first_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    last_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role"),
        default=UserRole.USER,
        server_default=UserRole.USER.value,
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(default=True, server_default="true", nullable=False)
