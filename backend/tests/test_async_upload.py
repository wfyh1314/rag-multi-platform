"""Celery 异步上传（eager 模式）测试."""

from io import BytesIO
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from config.settings import get_settings
from file_mgr.file_service import FileService
import storage.mysql_db as mysql_db
from storage.models.file import File
from storage.mysql_db import create_tables, get_db_session
from tasks.celery_app import celery_app


@pytest.fixture
def sqlite_async_db(monkeypatch):
    get_settings.cache_clear()
    monkeypatch.setenv("ASYNC_UPLOAD_THRESHOLD_MB", "0")
    celery_app.conf.task_always_eager = True
    celery_app.conf.task_eager_propagates = True

    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    mysql_db._engine = engine
    mysql_db._SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    create_tables()
    yield
    celery_app.conf.task_always_eager = False
    celery_app.conf.task_eager_propagates = False
    get_settings.cache_clear()


class MockFileStorage:
    def save(self, file, filename: str, subdir: str = "") -> str:
        return f"/tmp/uploads/{subdir}/{filename}"

    def delete_dir(self, subdir: str) -> bool:
        return True


class MockVectorStore:
    def __init__(self, settings=None):
        pass

    def delete_by_file_id(self, file_id: str) -> None:
        return None


def test_async_upload_indexes_via_celery_eager(sqlite_async_db):
    storage = MockFileStorage()
    processor = MagicMock()
    processor.process.return_value = {
        "chunk_count": 3,
        "status": "indexed",
        "message": "ok",
    }
    service = FileService(
        storage=storage,
        processor=processor,
        vector_store_cls=MockVectorStore,
    )

    with patch("tasks.parse_file_task.DocumentProcessor") as mock_processor_cls, patch(
        "tasks.parse_file_task.TagService"
    ) as mock_tag_cls:
        mock_processor_cls.return_value.process.return_value = {
            "chunk_count": 3,
            "status": "indexed",
            "message": "ok",
        }
        mock_tag_cls.return_value.auto_tag_file.return_value = []
        result = service.upload(
            BytesIO(b"hello async world"),
            "async-test.txt",
            user_id="user-async-1",
        )

    assert result["status"] == "pending"
    assert result["file_id"]

    with get_db_session() as session:
        record = session.scalar(select(File).where(File.id == result["file_id"]))
        assert record is not None
        assert record.status == "indexed"
        assert record.chunk_count == 3
