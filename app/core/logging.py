"""Настройка структурированного логирования приложения"""

import json
import logging
from datetime import UTC, datetime
from logging.config import dictConfig
from typing import Any

from app.core.request_context import get_request_id


class RequestContextFilter(logging.Filter):
    """Подставляет request_id из контекста в каждый log"""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = get_request_id()
        return True


class JsonFormatter(logging.Formatter):
    """Форматтер, который превращает log в JSON"""

    def __init__(self, service_name: str) -> None:
        super().__init__()
        self.service_name = service_name

    def format(self, record: logging.LogRecord) -> str:
        log_data: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "service": self.service_name,
            "logger": record.name,
            "message": record.getMessage(),
        }

        if record.exc_info:
            log_data["exception"] = self.formatException(
                ei=record.exc_info,
            )

        if hasattr(record, "request_id") and record.request_id is not None:
            log_data["request_id"] = record.request_id

        if hasattr(record, "method") and record.method is not None:
            log_data["method"] = record.method

        if hasattr(record, "path") and record.path is not None:
            log_data["path"] = record.path

        if hasattr(record, "status_code") and record.status_code is not None:
            log_data["status_code"] = record.status_code

        if hasattr(record, "duration_ms") and record.duration_ms is not None:
            log_data["duration_ms"] = record.duration_ms

        return json.dumps(
            obj=log_data,
            ensure_ascii=False,
        )


def setup_logging(
        log_level: str = "INFO",
        service_name: str = "orgs-api",
) -> None:
    """Глобальная настройка логирования приложения"""
    dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "filters": {
                "request_context": {
                    "()": "app.core.logging.RequestContextFilter",
                }
            },
            "formatters": {
                "json": {
                    "()": "app.core.logging.JsonFormatter",
                    "service_name": service_name,
                }
            },
            "handlers": {
                "default": {
                    "class": "logging.StreamHandler",
                    "formatter": "json",
                    "filters": ["request_context"],
                    "stream": "ext://sys.stdout",
                }
            },
            "root": {
                "level": log_level,
                "handlers": ["default"],
            },
            "loggers": {
                "uvicorn": {
                    "level": log_level,
                    "handlers": ["default"],
                    "propagate": False,
                },
                "uvicorn.error": {
                    "level": log_level,
                    "handlers": ["default"],
                    "propagate": False,
                },
                "uvicorn.access": {
                    "level": log_level,
                    "handlers": ["default"],
                    "propagate": False,
                },
            },
        }
    )


def get_logger(name: str) -> logging.Logger:
    """Возвращает logger для модуля"""
    return logging.getLogger(name)
