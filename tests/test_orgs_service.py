"""Тесты сервисного слоя и минимальные проверки HTTP-контракта"""
from unittest.mock import Mock

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.services import OrgsService


def test_get_organization(mock_db: Session) -> None:
    """
        OrgsService.get_organization обязан выбрасывать HTTPException(404),
        если репозиторий не нашёл организацию

        Args: mock_db

        Mock: orgs_repo.get_org_by_id
    """
    fake_repo = Mock()
    fake_repo.get_org_by_id.return_value = None

    svc = OrgsService(orgs=fake_repo, buildings=Mock())

    with pytest.raises(expected_exception=HTTPException) as exc:
        svc.get_organization(db=mock_db, org_id=1)

    assert exc.value.status_code == 404

def test_activity_not_found(mock_db: Session) -> None:
    """
        OrgsService.organizations_by_activity должен выбрасывать HTTPException,
        если activity не существует

        Args: mock_db

        Mock: orgs_repo.activity_exists
    """
    fake_repo = Mock()
    fake_repo.activity_exists.return_value = False

    svc = OrgsService(orgs=fake_repo, buildings=Mock())

    with pytest.raises(expected_exception=HTTPException):
        svc.organizations_by_activity(db=mock_db, activity_id=1)

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
