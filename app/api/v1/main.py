"""Точка входа в приложение"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from starlette.responses import Response

from app.api.middleware import RequestLoggingMiddleware
from app.api.v1.api import router
from app.core.config import settings
from app.core.logging import get_logger, setup_logging
from app.core.metrics import render_metrics

setup_logging(
    log_level=settings.log_level,
    service_name=settings.service_name,
)

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
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
async def health() -> dict[str, str]:
    """
    Проверка доступности сервиса

    Returns:
        dict[str, str]: Статус сервиса в формате {"status": "ok"}
    """
    logger.info("Health check called")
    return {"status": "ok"}


@app.get(
    path="/metrics",
    tags=["observability"],
    summary="Prometheus metrics",
)
async def metrics() -> Response:
    """
    Отдаёт Prometheus-метрики приложения.

    Returns:
        Response: Текст в формате exposition format для Prometheus
    """
    return render_metrics()
