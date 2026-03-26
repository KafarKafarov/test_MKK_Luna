"""Middleware для request_id и логирования HTTP-запросов"""

import time
import uuid

from starlette.types import (
    ASGIApp,
    Message,
    Receive,
    Scope,
    Send,
)

from app.core.logging import get_logger
from app.core.request_context import (
    reset_request_id,
    set_request_id,
)

logger = get_logger(__name__)


class RequestLoggingMiddleware:
    """Middleware для request_id и логирования HTTP-запросов"""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(
            self,
            scope: Scope,
            receive: Receive,
            send: Send,
    ) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request_id = uuid.uuid4().hex
        token = set_request_id(request_id=request_id)

        method = scope.get("method", "")
        path = scope.get("path", "")

        start_time = time.perf_counter()
        status_code = 500

        async def send_wrapper(message: Message) -> None:
            nonlocal status_code

            if message["type"] == "http.response.start":
                status_code = message["status"]

                headers = list(message.get("headers", []))
                headers.append((b"x-request-id", request_id.encode()))
                message["headers"] = headers

            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        except Exception:
            duration_ms = round(
                (time.perf_counter() - start_time) * 1000,
                2,
            )
            logger.exception(
                msg="Request failed",
                extra={
                    "method": method,
                    "path": path,
                    "status_code": status_code,
                    "duration_ms": duration_ms,
                },
            )
            raise
        else:
            duration_ms = round(
                (time.perf_counter() - start_time) * 1000,
                2,
            )
            logger.info(
                msg="Request completed",
                extra={
                    "method": method,
                    "path": path,
                    "status_code": status_code,
                    "duration_ms": duration_ms,
                },
            )
        finally:
            reset_request_id(token=token)
