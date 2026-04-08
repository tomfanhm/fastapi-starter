from __future__ import annotations

from httpx import AsyncClient


async def test_health_returns_ok(async_client: AsyncClient) -> None:
    """GET /health should return 200 with status ok."""
    response = await async_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["database_connected"] is True
