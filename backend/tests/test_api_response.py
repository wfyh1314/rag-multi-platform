"""统一 API 响应格式测试."""

import pytest
from fastapi.testclient import TestClient

from config.response_codes import SUCCESS, UNAUTHORIZED
from config.settings import get_settings
from core.response import fail, success
from main import app


def test_success_response_structure():
    body = success(result={"key": "value"}, message="操作成功", description="desc")
    assert body["code"] == SUCCESS
    assert body["message"] == "操作成功"
    assert body["description"] == "desc"
    assert body["result"] == {"key": "value"}


def test_fail_response_structure():
    body = fail(code=UNAUTHORIZED, message="未授权", description="认证失败")
    assert body["code"] == UNAUTHORIZED
    assert body["message"] == "未授权"
    assert body["result"] is None


def test_api_response_includes_uuid():
    client = TestClient(app)
    response = client.get("/api/models")
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == SUCCESS
    assert data["uuid"]
    assert "models" in data["result"]


@pytest.fixture
def auth_required(monkeypatch):
    get_settings.cache_clear()
    monkeypatch.setenv("AUTH_SKIP", "false")
    yield
    get_settings.cache_clear()
    monkeypatch.setenv("AUTH_SKIP", "true")


def test_unauthorized_includes_uuid(auth_required):
    client = TestClient(app)
    response = client.get("/api/users/me")
    assert response.status_code == 401
    data = response.json()
    assert data["code"] == UNAUTHORIZED
    assert data["uuid"]
