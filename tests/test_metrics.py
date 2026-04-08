"""Smoke-тесты observability-эндпоинта."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.api.v1.main import app


@pytest.mark.asyncio
async def test_metrics_is_public() -> None:
    """Prometheus должен забирать метрики без API key."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        resp = await client.get(url="/metrics")
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_metrics_contains_app_counters() -> None:
    """После запроса к API в /metrics должны появиться пользовательские метрики."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        health_response = await client.get(url="/health")
        metrics_response = await client.get(url="/metrics")

    assert health_response.status_code == 200
    assert metrics_response.status_code == 200
    assert "orgs_api_http_requests_total" in metrics_response.text
    assert 'route="/health"' in metrics_response.text
