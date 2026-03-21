from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions.handlers import ConflictException, NotFoundException
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate


async def get_user_by_id(db: AsyncSession, user_id: uuid.UUID) -> User:
    """Fetch a user by ID or raise NotFoundException."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise NotFoundException(detail=f"User {user_id} not found")
    return user


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    """Fetch a user by email, returning None if not found."""
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def create_user(db: AsyncSession, data: UserCreate, hashed_password: str) -> User:
    """Create a new user. Raises ConflictException if email exists."""
    existing = await get_user_by_email(db, data.email)
    if existing is not None:
        raise ConflictException(detail="A user with this email already exists")
    user = User(
        email=data.email,
        password_hash=hashed_password,
        first_name=data.first_name,
        last_name=data.last_name,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def update_user(db: AsyncSession, user: User, data: UserUpdate) -> User:
    """Partially update a user's fields."""
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)
    await db.commit()
    await db.refresh(user)
    return user
