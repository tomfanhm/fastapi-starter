from __future__ import annotations

from httpx import AsyncClient

from app.models.user import User


async def test_get_me_without_token(async_client: AsyncClient) -> None:
    """GET /api/v1/users/me without auth should return 401."""
    response = await async_client.get("/api/v1/users/me")
    assert response.status_code == 401


async def test_get_me_with_token(
    async_client: AsyncClient,
    test_user: User,
    auth_headers: dict[str, str],
) -> None:
    """GET /api/v1/users/me with valid token should return user data."""
    response = await async_client.get("/api/v1/users/me", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == test_user.email
    assert data["first_name"] == "Test"
    assert data["last_name"] == "User"


async def test_update_me(
    async_client: AsyncClient,
    test_user: User,
    auth_headers: dict[str, str],
) -> None:
    """PATCH /api/v1/users/me should update user fields."""
    response = await async_client.patch(
        "/api/v1/users/me",
        headers=auth_headers,
        json={"first_name": "Updated"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["first_name"] == "Updated"
    assert data["last_name"] == "User"  # unchanged
