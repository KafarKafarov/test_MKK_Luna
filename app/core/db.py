"""Модуль инициализации подключения к БД и создания SQLAlchemy-сессий"""
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import settings

engine = create_async_engine(
    url=settings.database_url,
    pool_pre_ping=True,
)
SessionLocal = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
      DI, предоставляющий async-сессию на время запроса

      Yields:
          Session: Активная SQLAlchemy-сессия
    """
    async with SessionLocal() as session:
        yield session
