"""HTTP-тест эндпоинтов, связанных с видами деятельности"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_activity_not_found(
        client: AsyncClient,
        auth_headers: dict[str, str],
) -> None:
    """Для несуществующего activity_id API вернет 404"""
    resp = await client.get(
        url="/activities/999/organizations",
        headers=auth_headers,
    )
    assert resp.status_code == 404
