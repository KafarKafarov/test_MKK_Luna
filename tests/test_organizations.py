"""HTTP-тесты эндпоинтов, связанных с организациями"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_search_empty_res(
        client: AsyncClient,
        auth_headers: dict,
) -> None:
    """
        Поиск по названию возвращает пустой список,
        если совпадений нет
    """
    resp = await client.get(
        url="/organizations/search",
        params={"q": "abc"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json() == []

@pytest.mark.asyncio
async def test_get_organization(
        client: AsyncClient,
        auth_headers: dict,
) -> None:
    """
        Запрос организации по несуществующему id должен вернуть 404
    """
    resp = await client.get(
        url="/organizations/999",
        headers=auth_headers,
    )
    assert resp.status_code == 404
