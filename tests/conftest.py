from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import Settings, get_settings
from app.core.database import Base, get_db
from app.core.security import create_access_token, hash_password
from app.main import create_app
from app.models.user import User

# Use a separate test database — SQLite async for simplicity in tests
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"


@pytest.fixture(scope="session")
def test_settings() -> Settings:
    """Override settings for testing."""
    return Settings(
        database_url=TEST_DATABASE_URL,
        jwt_secret_key="test-secret-key",
        debug=True,
        environment="test",
    )


@pytest.fixture
async def db_engine() -> AsyncGenerator[AsyncEngine, None]:
    """Create a test database engine and tables."""
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
    app = create_app()

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

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
async def auth_headers(test_user: User) -> dict[str, str]:
    """Generate auth headers with a valid JWT for the test user."""
    token = create_access_token(
        subject=str(test_user.id),
        settings=Settings(
            database_url=TEST_DATABASE_URL,
            jwt_secret_key="test-secret-key",
        ),
    )
    return {"Authorization": f"Bearer {token}"}
