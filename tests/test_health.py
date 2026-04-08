"""Smoke-тест для проверки доступности сервиса"""

import pytest
from httpx import ASGITransport, AsyncClient

from app.api.v1.main import app


@pytest.mark.asyncio
async def test_health() -> None:
    """Health-check эндпоинта"""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        resp = await client.get(url="/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}
