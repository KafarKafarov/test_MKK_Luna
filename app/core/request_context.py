"""Хранение request_id для текущего HTTP-запроса"""

from contextvars import ContextVar, Token


request_id_context: ContextVar[str | None] = ContextVar(
    "request_id",
    default=None,
)


def get_request_id() -> str | None:
    """Возвращает request_id текущего запроса"""
    return request_id_context.get()


def set_request_id(request_id: str) -> Token:
    """Сохраняет request_id в контексте текущего запроса"""
    return request_id_context.set(request_id)


def reset_request_id(token: Token) -> None:
    """Сбрасывает request_id из контекста"""
    request_id_context.reset(token)