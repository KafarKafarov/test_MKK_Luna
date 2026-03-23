"""Тесты сервисного слоя и минимальные проверки HTTP-контракта"""
from unittest.mock import AsyncMock, Mock

import pytest
from fastapi import HTTPException
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.services import OrgsService


@pytest.mark.asyncio
async def test_get_organization(
        mock_db: AsyncSession,
) -> None:
    """
        OrgsService.get_organization обязан выбрасывать HTTPException(404),
        если репозиторий не нашёл организацию

        Args: mock_db

        Mock: orgs_repo.get_org_by_id
    """
    fake_repo = Mock()
    fake_repo.get_org_by_id = AsyncMock(
        return_value=None,
    )

    svc = OrgsService(
        orgs=fake_repo,
        buildings=Mock(),
    )

    with pytest.raises(
            expected_exception=HTTPException,
    ) as exc:
        await svc.get_organization(
            db=mock_db,
            org_id=1,
        )

    assert exc.value.status_code == 404
    fake_repo.get_org_by_id.assert_awaited_once_with(
        db=mock_db,
        org_id=1,
    )

@pytest.mark.asyncio
async def test_activity_not_found(
        mock_db: AsyncSession,
) -> None:
    """
        OrgsService.organizations_by_activity должен выбрасывать HTTPException,
        если activity не существует

        Args: mock_db

        Mock: orgs_repo.activity_exists
    """
    fake_repo = Mock()
    fake_repo.activity_exists = AsyncMock(
        return_value=False,
    )
    fake_repo.activity_descendants_ids = AsyncMock()

    svc = OrgsService(
        orgs=fake_repo,
        buildings=Mock(),
    )

    with pytest.raises(
            expected_exception=HTTPException,
    ):
        await svc.organizations_by_activity(
            db=mock_db,
            activity_id=1,
        )

    fake_repo.activity_descendants_ids.assert_not_called()

@pytest.mark.asyncio
async def test_search_validation(
        client: AsyncClient,
        auth_headers: dict[str, str],
) -> None:
    """
        Тест валидации параметра q в /organizations/search
    """
    resp = await client.get(
        url="/organizations/search",
        params={"q": ""},
        headers=auth_headers,
    )
    assert resp.status_code == 422
