"""会话 API 测试."""

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
        "user_id": "test-user-1",
        "role": "employee",
    }
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_create_and_list_sessions(client):
    create_resp = client.post("/api/sessions", json={"title": "测试会话"})
    assert create_resp.status_code == 200
    body = create_resp.json()
    assert body["code"] == 10000
    session_id = body["result"]["id"]

    list_resp = client.get("/api/sessions")
    assert list_resp.status_code == 200
    sessions = list_resp.json()["result"]["sessions"]
    assert any(s["id"] == session_id for s in sessions)


def test_import_sessions(client):
    payload = {
        "sessions": [
            {
                "title": "旧会话",
                "messages": [
                    {"role": "user", "content": "你好"},
                    {"role": "assistant", "content": "您好"},
                ],
            }
        ]
    }
    resp = client.post("/api/sessions/import", json=payload)
    assert resp.status_code == 200
    session_id = resp.json()["result"]["sessions"][0]["id"]

    history_resp = client.get(f"/api/sessions/{session_id}/history")
    assert history_resp.status_code == 200
    history = history_resp.json()["result"]["history"]
    assert len(history) == 2
