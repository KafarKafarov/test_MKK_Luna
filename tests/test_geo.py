"""HTTP-тесты геопоиска"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_geo_validation(
        client: AsyncClient,
        auth_headers: dict,
) -> None:
    """Радиус должен быть строго положительным"""
    resp = await client.get(
        url="/geo/radius",
        params={"lat": 0, "lon": 0, "r_m": -1},
        headers=auth_headers,
    )
    assert resp.status_code == 422

@pytest.mark.asyncio
async def test_geo_empty(
        client: AsyncClient,
        auth_headers: dict,
) -> None:
    """
        Геопоиск по прямоугольнику,
        возвращает пустые списки если зданий в bbox нет
    """
    resp = await client.get(
        url="/geo/rectangle",
        params={
            "lat1": 0,
            "lon1": 0,
            "lat2": 1,
            "lon2": 1,
        },
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json() == {"organizations": [], "buildings": []}
