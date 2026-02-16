from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.db import get_db
from app.main import app


@pytest.fixture(scope="session")
def engine() -> Generator[Engine, None, None]:
    eng = create_engine(
        "postgresql+psycopg://orgs:1234@localhost:5432/orgs",
        pool_pre_ping=True,
    )
    yield eng


@pytest.fixture()
def db_session(engine: Engine) -> Generator[Session, None, None]:
    testing_session_local = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
    )
    s = testing_session_local()
    try:
        yield s
        s.rollback()
    finally:
        s.close()


@pytest.fixture(autouse=True)
def cleanup_db(engine: Engine) -> None:
    with engine.begin() as conn:
        conn.execute(
            text(
                "TRUNCATE "
                "organization_activities, "
                "organization_phones, "
                "organizations, "
                "activities, "
                "buildings "
                "RESTART IDENTITY CASCADE"
            )
        )


@pytest.fixture(autouse=True)
def override_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    from app import config

    if hasattr(config, "get_settings"):
        class _TestSettings:
            database_url = "postgresql+psycopg://orgs:1234@localhost:5432/orgs"
            api_key = "supersecret"
        monkeypatch.setattr(config, "get_settings", lambda: _TestSettings())
    else:
        monkeypatch.setattr(config.settings, "api_key", "supersecret", raising=False)


@pytest.fixture()
def client(db_session: Session) -> Generator[TestClient, None, None]:
    def override_get_db() -> Generator[Session, None, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
