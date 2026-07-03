"""Redis：JWT 登录缓存、会话缓存、接口限流."""

from typing import Any, Optional

import redis

from config.settings import Settings, get_settings

_redis_client: Optional[redis.Redis] = None


def get_redis_client(settings: Optional[Settings] = None) -> redis.Redis:
    """返回 Redis 单例客户端。"""
    global _redis_client
    if _redis_client is None:
        cfg = settings or get_settings()
        _redis_client = redis.Redis(
            host=cfg.redis_host,
            port=cfg.redis_port,
            password=cfg.redis_password or None,
            db=cfg.redis_db,
            decode_responses=True,
        )
    return _redis_client


class RedisCache:
    """Redis 缓存辅助类，用于 JWT、会话与限流。"""

    def __init__(self, client: Optional[redis.Redis] = None):
        self.client = client or get_redis_client()

    def set(self, key: str, value: str, ttl_seconds: Optional[int] = None) -> None:
        """设置缓存值，可选 TTL。"""
        if ttl_seconds:
            self.client.setex(key, ttl_seconds, value)
        else:
            self.client.set(key, value)

    def get(self, key: str) -> Optional[str]:
        """获取缓存值。"""
        return self.client.get(key)

    def delete(self, key: str) -> None:
        """删除缓存键。"""
        self.client.delete(key)

    def incr_rate_limit(self, key: str, window_seconds: int = 60) -> int:
        """递增限流计数器。"""
        pipe = self.client.pipeline()
        pipe.incr(key)
        pipe.expire(key, window_seconds)
        results = pipe.execute()
        return int(results[0])
