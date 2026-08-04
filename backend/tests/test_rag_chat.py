"""问答链路测试."""

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
        "user_id": "dev-user",
        "role": "super_admin",
    }
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_health_check(client):
    """健康检查接口应返回 ok。"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_list_models(client):
    """模型列表接口应返回已配置的 LLM 模型。"""
    response = client.get("/api/models")
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 10000
    assert "models" in data["result"]
    assert len(data["result"]["models"]) >= 1


def test_clear_history(client):
    """清空历史接口应成功。"""
    create_resp = client.post("/api/sessions", json={"title": "测试"})
    session_id = create_resp.json()["result"]["id"]
    response = client.post("/api/history/clear", json={"session_id": session_id})
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 10000
    assert "清空" in data["message"]
