"""测试全局配置."""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from config.settings import get_settings
from core.security import get_current_user
from main import app
import storage.mysql_db as mysql_db
from storage.mysql_db import create_tables

# 避免测试启动时连接真实 MySQL
patch("storage.db_bootstrap.seed_default_data", lambda settings=None: None).start()


@pytest.fixture(autouse=True)
def auth_skip_enabled(monkeypatch):
    """默认开启 AUTH_SKIP，保持现有 API 测试无需 token。"""
    get_settings.cache_clear()
    monkeypatch.setenv("AUTH_SKIP", "true")
    yield
    get_settings.cache_clear()


@pytest.fixture
def client(monkeypatch):
    get_settings.cache_clear()
    monkeypatch.setenv("AUTH_SKIP", "true")

    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    mysql_db._engine = engine
    mysql_db._SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    create_tables()

    app.dependency_overrides[get_current_user] = lambda: {
        "user_id": "test-user-1",
        "role": "employee",
        "department_id": "dept-a",
    }
    yield TestClient(app)
    app.dependency_overrides.clear()
