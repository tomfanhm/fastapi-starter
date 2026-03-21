from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from datetime import datetime

from sqlalchemy import DateTime, Uuid, func
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from app.core.config import get_settings

settings = get_settings()

_engine_kwargs: dict[str, object] = {
    "echo": settings.debug,
}
if settings.database_url.startswith("postgresql"):
    _engine_kwargs["pool_size"] = settings.database_pool_size
    _engine_kwargs["max_overflow"] = settings.database_max_overflow

async_engine = create_async_engine(settings.database_url, **_engine_kwargs)

async_session_factory = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """Declarative base with common columns."""

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Yield an async database session."""
    async with async_session_factory() as session:
        try:
            yield session
        finally:
            await session.close()
