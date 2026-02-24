"""HTTP-тесты геопоиска"""
from fastapi.testclient import TestClient


def test_geo_validation(client: TestClient) -> None:
    """Радиус должен быть строго положительным"""
    resp = client.get(
        url="/geo/radius",
        params={"lat": 0, "lon": 0, "r_m": -1},
        headers={"X-API-Key": "supersecret"},
    )
    assert resp.status_code == 422


def test_geo_empty(client: TestClient) -> None:
    """
        Геопоиск по прямоугольнику,
        возвращает пустые списки если зданий в bbox нет
    """
    resp = client.get(
        url="/geo/rectangle",
        params={
            "lat1": 0,
            "lon1": 0,
            "lat2": 1,
            "lon2": 1,
        },
        headers={"X-API-Key": "supersecret"},
    )
    assert resp.status_code == 200
    assert resp.json() == {"organizations": [], "buildings": []}
