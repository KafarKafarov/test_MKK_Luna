"""Конфигурация pytest для интеграционных тестов API"""
from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock

import pytest
import pytest_asyncio
from dotenv import load_dotenv
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

load_dotenv()

from app.api.v1.main import app
from app.core.db import get_db
from app.models.models import Base


@pytest_asyncio.fixture(scope="function")
async def engine() -> AsyncGenerator[AsyncEngine, None]:
    """
        Тестовое БД

        Scope: session
        - создаётся один раз на всю тестовую сессию

        Yields:
            Engine: SQLAlchemy engine для тестовой базы
    """
    eng = create_async_engine(
        url="postgresql+asyncpg://orgs:1234@localhost:5432/orgs",
        pool_pre_ping=True,
        poolclass=NullPool,
    )

    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield eng

    await eng.dispose()

@pytest_asyncio.fixture(scope="function")
async def db_session(
        engine: AsyncEngine,
) -> AsyncGenerator[AsyncSession, None]:
    """
        Создаёт изолированную SQLAlchemy-сессию для каждого теста

        Scope: function
        - новая сессия для каждого теста
    """
    async_session = async_sessionmaker(
            bind=engine,
            expire_on_commit=False,
        )

    async with async_session() as session:
        yield session


@pytest.fixture(autouse=True)
def override_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """Переопределяет API key для тестовой среды"""
    from app.core import config

    monkeypatch.setattr(
        target=config.settings,
        name="api_key",
        value="supersecret",
        raising=False,
    )


@pytest_asyncio.fixture()
async def client(
        db_session: AsyncSession,
) -> AsyncGenerator[AsyncClient, None]:
    """Создаёт AsyncClient с переопределённой зависимостью get_db"""
    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        """
            Переопределенная зависимость get_db

            Yields:
                Session: Тестовая SQLAlchemy-сессия
        """
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
    ) as c:
        yield c
    app.dependency_overrides.clear()

@pytest.fixture()
def mock_db() -> AsyncSession:
    return AsyncMock(spec=AsyncSession)

@pytest.fixture
def auth_headers():
    return {"X-API-Key": "supersecret"}
