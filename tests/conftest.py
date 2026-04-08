from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import Settings, get_settings
from app.core.database import Base, get_db, init_engine
from app.core.security import create_access_token, hash_password
from app.main import create_app
from app.models.user import User, UserRole

TEST_DATABASE_URL = "sqlite+aiosqlite://"


@pytest.fixture(scope="session")
def test_settings() -> Settings:
    """Override settings for testing."""
    return Settings(
        database_url=TEST_DATABASE_URL,
        jwt_secret_key="test-secret-key-that-is-long-enough-for-hs256",
        debug=True,
        environment="test",
    )


@pytest.fixture
async def db_engine() -> AsyncGenerator[AsyncEngine, None]:
    """Create an in-memory test database engine and tables."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
async def db_session(db_engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
    """Yield a test database session."""
    session_factory = async_sessionmaker(bind=db_engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session


@pytest.fixture
async def async_client(db_session: AsyncSession, test_settings: Settings) -> AsyncGenerator[AsyncClient, None]:
    """Create an async test client with overridden dependencies."""
    init_engine(test_settings)
    app = create_app()

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        try:
            yield db_session
            await db_session.commit()
        except Exception:
            await db_session.rollback()
            raise

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_settings] = lambda: test_settings

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()


@pytest.fixture
async def test_user(db_session: AsyncSession) -> User:
    """Create a test user in the database."""
    user = User(
        id=uuid.uuid4(),
        email="test@example.com",
        password_hash=hash_password("testpassword123"),
        first_name="Test",
        last_name="User",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def admin_user(db_session: AsyncSession) -> User:
    """Create an admin user in the database."""
    user = User(
        id=uuid.uuid4(),
        email="admin@example.com",
        password_hash=hash_password("adminpassword123"),
        first_name="Admin",
        last_name="User",
        role=UserRole.ADMIN,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def inactive_user(db_session: AsyncSession) -> User:
    """Create a deactivated user in the database."""
    user = User(
        id=uuid.uuid4(),
        email="inactive@example.com",
        password_hash=hash_password("inactivepass123"),
        first_name="Inactive",
        last_name="User",
        is_active=False,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
def auth_headers(test_user: User, test_settings: Settings) -> dict[str, str]:
    """Generate auth headers with a valid JWT for the test user."""
    token = create_access_token(subject=str(test_user.id), settings=test_settings)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_headers(admin_user: User, test_settings: Settings) -> dict[str, str]:
    """Generate auth headers with a valid JWT for the admin user."""
    token = create_access_token(subject=str(admin_user.id), settings=test_settings)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def inactive_headers(inactive_user: User, test_settings: Settings) -> dict[str, str]:
    """Generate auth headers with a valid JWT for the inactive user."""
    token = create_access_token(subject=str(inactive_user.id), settings=test_settings)
    return {"Authorization": f"Bearer {token}"}
