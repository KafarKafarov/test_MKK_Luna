"""HTTP-тест эндпоинтов, связанных с видами деятельности"""
from fastapi.testclient import TestClient


def test_activity_not_found(client: TestClient) -> None:
    """Для несуществующего activity_id API вернет 404"""
    resp = client.get(
        url="/activities/999/organizations",
        headers={"X-API-Key": "supersecret"},
    )
    assert resp.status_code == 404
