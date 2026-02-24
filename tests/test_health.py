"""Smoke-тест для проверки доступности сервиса"""
from fastapi.testclient import TestClient

from app.main import app


def test_health() -> None:
    """Health-check эндпоинта"""
    client = TestClient(app=app)
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}
