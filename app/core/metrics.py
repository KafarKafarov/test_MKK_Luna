"""Prometheus-метрики для HTTP-трафика приложения."""

from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
)
from starlette.responses import Response
from starlette.types import Scope

HTTP_REQUESTS_TOTAL = Counter(
    name="orgs_api_http_requests_total",
    documentation="Total HTTP requests handled by the API.",
    labelnames=("method", "route", "status_code"),
)

HTTP_REQUEST_DURATION_SECONDS = Histogram(
    name="orgs_api_http_request_duration_seconds",
    documentation="HTTP request latency in seconds.",
    labelnames=("method", "route"),
    buckets=(
        0.005,
        0.01,
        0.025,
        0.05,
        0.1,
        0.25,
        0.5,
        1.0,
        2.5,
        5.0,
        10.0,
    ),
)

HTTP_REQUESTS_IN_PROGRESS = Gauge(
    name="orgs_api_http_requests_in_progress",
    documentation="Number of HTTP requests currently being processed.",
)


def resolve_route_template(scope: Scope) -> str:
    """Возвращает шаблон маршрута, чтобы не плодить label cardinality."""
    route = scope.get("route")
    route_path = getattr(route, "path", None)
    if isinstance(route_path, str):
        return route_path
    return "unmatched"


def observe_http_request(
    method: str,
    route: str,
    status_code: int,
    duration_seconds: float,
) -> None:
    """Записывает итоговую метрику по завершённому HTTP-запросу."""
    status_code_label = str(status_code)
    HTTP_REQUESTS_TOTAL.labels(
        method=method,
        route=route,
        status_code=status_code_label,
    ).inc()
    HTTP_REQUEST_DURATION_SECONDS.labels(
        method=method,
        route=route,
    ).observe(amount=duration_seconds)


def render_metrics() -> Response:
    """Формирует Prometheus-compatible ответ для /metrics."""
    return Response(
        content=generate_latest(),
        headers={"Content-Type": CONTENT_TYPE_LATEST},
    )
