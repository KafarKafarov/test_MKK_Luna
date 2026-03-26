"""Точка входа в приложение"""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.middleware import RequestLoggingMiddleware
from app.api.v1.api import router
from app.core.config import settings
from app.core.logging import get_logger, setup_logging

setup_logging(
    log_level=settings.log_level,
    service_name=settings.service_name,
)

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    """Логирует запуск и остановку приложения"""
    logger.info("Application started")
    yield
    logger.info("Application stopped")


app = FastAPI(
    title="Organizations API",
    description="API для организаций/зданий/деятельностей. Авторизация: X-API-Key.",
    lifespan=lifespan,
)

app.add_middleware(
    middleware_class=RequestLoggingMiddleware,
)
app.include_router(router=router)


@app.get(
    path="/health",
    tags=["health"],
    summary="Health check",
)
def health() -> dict[str, str]:
    """
    Проверка доступности сервиса

    Returns:
        dict[str, str]: Статус сервиса в формате {"status": "ok"}
    """
    logger.info("Health check called")
    return {"status": "ok"}
