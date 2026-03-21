from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.exceptions.handlers import ForbiddenException
from app.models.user import User, UserRole
from app.schemas.user import UserResponse, UserUpdate
from app.services.user_service import get_user_by_id, update_user

router = APIRouter(prefix="/users", tags=["users"])


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user profile",
)
async def get_me(
    current_user: User = Depends(get_current_user),
) -> User:
    """Return the currently authenticated user's profile."""
    return current_user


@router.patch(
    "/me",
    response_model=UserResponse,
    summary="Update current user profile",
)
async def update_me(
    data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Partially update the current user's profile."""
    return await update_user(db, current_user, data)


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="Get user by ID (admin only)",
)
async def get_user(
    user_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Fetch a user by ID. Requires admin role."""
    if current_user.role != UserRole.ADMIN:
        raise ForbiddenException(detail="Admin access required")
    return await get_user_by_id(db, user_id)
