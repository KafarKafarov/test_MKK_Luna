"""Тесты авторизации API"""
from fastapi.testclient import TestClient


def test_unauthorized(client: TestClient) -> None:
    """Проверяет, что запрос без заголовка X-API-Key запрещён"""
    resp = client.get(url="/organizations/search", params={"q": "a"})
    assert resp.status_code == 401


def test_wrong_key(client: TestClient) -> None:
    """Проверяет, что неверный API key приводит к 401 ошибки"""
    resp = client.get(
        url="/organizations/search",
        params={"q": "a"},
        headers={"X-API-Key": "wrong"},
    )
    assert resp.status_code == 401
