from fastapi.testclient import TestClient

from app.main import app


def test_search_smoke() -> None:
    client = TestClient(app)
    r = client.get("/organizations/search", params={"q": "Еда"})
    assert r.status_code == 200
