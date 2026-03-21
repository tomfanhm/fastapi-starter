from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, hash_password, verify_password
from app.exceptions.handlers import UnauthorizedException
from app.models.user import User
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
    user: User | None = await get_user_by_email(db, email)
    if user is None or not verify_password(password, user.password_hash):
        raise UnauthorizedException(detail="Invalid email or password")
    token = create_access_token(subject=str(user.id))
    return TokenResponse(access_token=token)
