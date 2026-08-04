"""API 限流中间件（Redis 滑动窗口，不可用时跳过）."""

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from config.constants import API_RATE_LIMIT_PER_MINUTE
from config.response_codes import TOO_MANY_REQUESTS
from core.logger import get_logger
from core.request_context import get_request_uuid
from core.response import fail

logger = get_logger(__name__)

SKIP_PREFIXES = ("/health", "/docs", "/openapi.json", "/redoc", "/static")


class RateLimitMiddleware(BaseHTTPMiddleware):
    """按 IP 限流 API 请求（每分钟 API_RATE_LIMIT_PER_MINUTE 次）。"""

    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        if any(path.startswith(prefix) for prefix in SKIP_PREFIXES):
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        key = f"rate:{client_ip}"

        try:
            from storage.redis_client import RedisCache

            count = RedisCache().incr_rate_limit(key, window_seconds=60)
            if count > API_RATE_LIMIT_PER_MINUTE:
                request_uuid = getattr(request.state, "uuid", "") or get_request_uuid()
                return JSONResponse(
                    status_code=429,
                    content=fail(
                        code=TOO_MANY_REQUESTS,
                        message="请求过于频繁，请稍后再试",
                        request_uuid=request_uuid,
                    ),
                )
        except Exception as exc:
            logger.debug("Rate limit skipped (Redis unavailable): %s", exc)

        return await call_next(request)
