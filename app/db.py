"""Модуль инициализации подключения к БД и создания SQLAlchemy-сессий"""
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import settings

engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db() -> Generator[Session, None, None]:
    """
      DI, предоставляющий SQLAlchemy-сессию на время запроса

      Yields:
          Session: Активная SQLAlchemy-сессия
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
