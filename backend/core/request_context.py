"""请求上下文：追踪 UUID."""

import uuid
from contextvars import ContextVar

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

_request_uuid: ContextVar[str] = ContextVar("request_uuid", default="")


def get_request_uuid() -> str:
    """获取当前请求 UUID。"""
    return _request_uuid.get()


def set_request_uuid(value: str) -> None:
    """设置当前请求 UUID。"""
    _request_uuid.set(value)


class RequestUuidMiddleware(BaseHTTPMiddleware):
    """为每个请求生成并注入 UUID。"""

    async def dispatch(self, request: Request, call_next):
        request_uuid = str(uuid.uuid4())
        request.state.uuid = request_uuid
        token = _request_uuid.set(request_uuid)
        try:
            return await call_next(request)
        finally:
            _request_uuid.reset(token)
