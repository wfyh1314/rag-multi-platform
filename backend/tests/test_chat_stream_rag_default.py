"""chat/stream 默认走 RAG 测试."""

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


async def _fake_rag_stream(*args, **kwargs):
    yield 'data: {"content": "rag answer"}\n\n'
    yield 'data: {"done": true}\n\n'


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


def _mock_stream_rag_answer(*args, **kwargs):
    return _fake_rag_stream()


def test_chat_stream_without_collection_uses_rag(client):
    with patch("api.chat_api.stream_rag_answer", side_effect=_mock_stream_rag_answer) as mock_rag:
        response = client.post(
            "/api/chat/stream",
            json={"query": "hello", "history": []},
        )

    assert response.status_code == 200
    mock_rag.assert_called_once()
    assert mock_rag.call_args.kwargs.get("file_id") is None
