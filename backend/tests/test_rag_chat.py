"""问答链路测试."""

import pytest
from fastapi.testclient import TestClient

from main import app


@pytest.fixture
def client():
    return TestClient(app)


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
    assert "models" in data
    assert len(data["models"]) >= 1


def test_clear_history(client):
    """清空历史接口应成功。"""
    response = client.post("/api/history/clear", json={"session_id": "test-session"})
    assert response.status_code == 200
    assert "清空" in response.json()["message"]
