from __future__ import annotations

from pydantic import BaseModel, EmailStr


class RegisterRequest(BaseModel):
    """Registration request payload."""

    email: EmailStr
    password: str
    first_name: str | None = None
    last_name: str | None = None


class LoginRequest(BaseModel):
    """Login request payload (for JSON-based login)."""

    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """JWT token response."""

    access_token: str
    token_type: str = "bearer"
