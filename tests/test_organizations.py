"""HTTP-тесты эндпоинтов, связанных с организациями"""
from fastapi.testclient import TestClient


def test_search_empty_res(client: TestClient) -> None:
    """
        Поиск по названию возвращает пустой список,
        если совпадений нет
    """
    resp = client.get(
        url="/organizations/search",
        params={"q": "abc"},
        headers={"X-API-Key": "supersecret"},
    )
    assert resp.status_code == 200
    assert resp.json() == []


def test_get_organization(client: TestClient) -> None:
    """
        Запрос организации по несуществующему id должен вернуть 404
    """
    resp = client.get(
        url="/organizations/999",
        headers={"X-API-Key": "supersecret"},
    )
    assert resp.status_code == 404
