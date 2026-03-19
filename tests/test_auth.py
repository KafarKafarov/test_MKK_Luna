"""Тесты авторизации API"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_unauthorized(client: AsyncClient) -> None:
    """Проверяет, что запрос без заголовка X-API-Key запрещён"""
    resp = await client.get(
        url="/organizations/search",
        params={"q": "a"},
    )
    assert resp.status_code == 401

@pytest.mark.asyncio
async def test_wrong_key(client: AsyncClient) -> None:
    """Проверяет, что неверный API key приводит к 401 ошибки"""
    resp = await client.get(
        url="/organizations/search",
        params={"q": "a"},
        headers={"X-API-Key": "wrong"},
    )
    assert resp.status_code == 401
