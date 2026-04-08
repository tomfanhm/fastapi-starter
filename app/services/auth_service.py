from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, hash_password, verify_password_or_dummy
from app.exceptions.handlers import UnauthorizedException
from app.schemas.auth import RegisterRequest, TokenResponse
from app.schemas.user import UserCreate
from app.services.user_service import create_user, get_user_by_email


async def register_user(db: AsyncSession, data: RegisterRequest) -> TokenResponse:
    """Register a new user and return a token."""
    hashed = hash_password(data.password)
    user_data = UserCreate(
        email=data.email,
        password=data.password,
        first_name=data.first_name,
        last_name=data.last_name,
    )
    user = await create_user(db, user_data, hashed)
    token = create_access_token(subject=str(user.id))
    return TokenResponse(access_token=token)


async def authenticate_user(db: AsyncSession, email: str, password: str) -> TokenResponse:
    """Authenticate a user by email/password and return a token."""
    user = await get_user_by_email(db, email)
    hashed = user.password_hash if user is not None else None
    if not verify_password_or_dummy(password, hashed):
        raise UnauthorizedException(detail="Invalid email or password")
    # user is guaranteed non-None here since verify_password_or_dummy returns False for None hash
    assert user is not None
    token = create_access_token(subject=str(user.id))
    return TokenResponse(access_token=token)
