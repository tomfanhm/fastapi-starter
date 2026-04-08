from __future__ import annotations

import uuid as uuid_mod
from datetime import UTC, datetime, timedelta
from typing import Any

import bcrypt
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.database import get_db
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

# Pre-computed dummy hash for constant-time comparison when user doesn't exist
_DUMMY_HASH = bcrypt.hashpw(b"dummy", bcrypt.gensalt())


def create_access_token(
    subject: str,
    expires_delta: timedelta | None = None,
    settings: Settings | None = None,
) -> str:
    """Create a JWT access token."""
    if settings is None:
        settings = get_settings()
    if expires_delta is None:
        expires_delta = timedelta(minutes=settings.jwt_access_token_expire_minutes)
    expire = datetime.now(UTC) + expires_delta
    to_encode: dict[str, Any] = {"sub": subject, "exp": expire}
    return jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)  # type: ignore[return-value]


def verify_token(token: str, settings: Settings | None = None) -> dict[str, Any]:
    """Verify and decode a JWT token. Raises HTTPException on failure."""
    if settings is None:
        settings = get_settings()
    credentials_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload: dict[str, Any] = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        if payload.get("sub") is None:
            raise credentials_exc
        return payload
    except jwt.PyJWTError as exc:
        raise credentials_exc from exc


def hash_password(plain: str) -> str:
    """Hash a plaintext password using bcrypt."""
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    """Verify a plaintext password against a bcrypt hash."""
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def verify_password_or_dummy(plain: str, hashed: str | None) -> bool:
    """Constant-time password check. Uses dummy hash when user doesn't exist to prevent timing oracle."""
    if hashed is None:
        bcrypt.checkpw(plain.encode(), _DUMMY_HASH)
        return False
    return bcrypt.checkpw(plain.encode(), hashed.encode())


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> User:
    """Dependency that extracts and validates the current user from the JWT token."""
    payload = verify_token(token, settings)
    user_id = payload.get("sub")
    result = await db.execute(select(User).where(User.id == uuid_mod.UUID(user_id)))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account disabled",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user
