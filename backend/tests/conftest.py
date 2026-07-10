"""测试全局配置."""

from unittest.mock import patch

import pytest

from config.settings import get_settings

# 避免测试启动时连接真实 MySQL
patch("storage.db_bootstrap.seed_default_data", lambda settings=None: None).start()


@pytest.fixture(autouse=True)
def auth_skip_enabled(monkeypatch):
    """默认开启 AUTH_SKIP，保持现有 API 测试无需 token。"""
    get_settings.cache_clear()
    monkeypatch.setenv("AUTH_SKIP", "true")
    yield
    get_settings.cache_clear()
