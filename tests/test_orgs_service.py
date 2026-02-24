"""Тесты сервисного слоя и минимальные проверки HTTP-контракта"""
from unittest.mock import Mock

import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.services import OrgsService

def test_get_organization() -> None:
    """
        OrgsService.get_organization обязан выбрасывать HTTPException(404),
        если репозиторий не нашёл организацию

        Mock: orgs_repo.get_org_by_id
    """
    fake_repo = Mock()
    fake_repo.get_org_by_id.return_value = None

    svc = OrgsService(orgs=fake_repo, buildings=Mock())

    with pytest.raises(HTTPException) as exc:
        svc.get_organization(Mock(spec=Session), 1)

    assert exc.value.status_code == 404

def test_activity_not_found() -> None:
    """
        OrgsService.organizations_by_activity должен выбрасывать HTTPException,
        если activity не существует

        Mock: orgs_repo.activity_exists
    """
    fake_repo = Mock()
    fake_repo.activity_exists.return_value = False

    svc = OrgsService(orgs=fake_repo, buildings=Mock())

    with pytest.raises(HTTPException):
        svc.organizations_by_activity(Mock(spec=Session), 1)

def test_search_validation(client: TestClient) -> None:
    """
        Тест валидации параметра q в /organizations/search
    """
    resp = client.get(
        url="/organizations/search",
        params={"q": ""},
        headers={"X-API-Key": "supersecret"},
    )
    assert resp.status_code == 422
