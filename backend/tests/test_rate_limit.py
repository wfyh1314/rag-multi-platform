"""API 限流中间件测试."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from core.rate_limit import RateLimitMiddleware


def test_rate_limit_blocks_when_exceeded():
    middleware = RateLimitMiddleware(app=MagicMock())
    request = MagicMock()
    request.url.path = "/api/files"
    request.client.host = "127.0.0.1"
    request.state.uuid = "test-uuid"

    call_next = AsyncMock(return_value="ok")

    async def run():
        with patch("storage.redis_client.RedisCache") as mock_cache_cls:
            mock_cache_cls.return_value.incr_rate_limit.return_value = 999
            return await middleware.dispatch(request, call_next)

    response = asyncio.run(run())
    assert response.status_code == 429
    call_next.assert_not_called()


def test_rate_limit_skips_when_redis_unavailable():
    middleware = RateLimitMiddleware(app=MagicMock())
    request = MagicMock()
    request.url.path = "/api/files"
    request.client.host = "127.0.0.1"

    call_next = AsyncMock(return_value="passed")

    async def run():
        with patch("storage.redis_client.RedisCache", side_effect=ConnectionError("no redis")):
            return await middleware.dispatch(request, call_next)

    response = asyncio.run(run())
    assert response == "passed"
    call_next.assert_called_once()
