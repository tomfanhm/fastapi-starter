from __future__ import annotations

from httpx import AsyncClient

from app.models.user import User


async def test_register_new_user(async_client: AsyncClient) -> None:
    """POST /api/v1/auth/register should create user and return token."""
    response = await async_client.post(
        "/api/v1/auth/register",
        json={
            "email": "newuser@example.com",
            "password": "strongpass123",
            "first_name": "New",
            "last_name": "User",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


async def test_register_duplicate_email(async_client: AsyncClient, test_user: User) -> None:
    """POST /api/v1/auth/register with existing email should return 409."""
    response = await async_client.post(
        "/api/v1/auth/register",
        json={
            "email": test_user.email,
            "password": "somepassword123",
        },
    )
    assert response.status_code == 409
    assert response.json()["error"] == "CONFLICT"


async def test_login_valid_credentials(async_client: AsyncClient, test_user: User) -> None:
    """POST /api/v1/auth/login with valid credentials should return token."""
    response = await async_client.post(
        "/api/v1/auth/login",
        data={"username": test_user.email, "password": "testpassword123"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


async def test_login_wrong_password(async_client: AsyncClient, test_user: User) -> None:
    """POST /api/v1/auth/login with wrong password should return 401."""
    response = await async_client.post(
        "/api/v1/auth/login",
        data={"username": test_user.email, "password": "wrongpassword"},
    )
    assert response.status_code == 401


async def test_login_nonexistent_email(async_client: AsyncClient) -> None:
    """POST /api/v1/auth/login with unknown email should return 401."""
    response = await async_client.post(
        "/api/v1/auth/login",
        data={"username": "nobody@example.com", "password": "whatever1"},
    )
    assert response.status_code == 401


async def test_register_short_password(async_client: AsyncClient) -> None:
    """POST /api/v1/auth/register with short password should return 422."""
    response = await async_client.post(
        "/api/v1/auth/register",
        json={"email": "short@example.com", "password": "abc"},
    )
    assert response.status_code == 422
