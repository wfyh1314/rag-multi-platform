"""文件元数据 MySQL 持久化测试."""

from io import BytesIO
from unittest.mock import MagicMock

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from config.constants import DOC_VISIBILITY_PRIVATE, DOC_VISIBILITY_PUBLIC
from config.settings import get_settings
from file_mgr.file_service import (
    FileService,
    get_file_record,
    list_collections_for_user,
    list_files_for_user,
)
import storage.mysql_db as mysql_db
from storage.models.file import File
from storage.mysql_db import create_tables, get_db_session
from storage.repositories.file_repository import FileRepository


@pytest.fixture
def sqlite_file_db(monkeypatch):
    get_settings.cache_clear()
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    mysql_db._engine = engine
    mysql_db._SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    create_tables()
    yield
    get_settings.cache_clear()


class MockVectorStore:
    deleted_file_ids: list[str] = []

    def __init__(self, settings=None):
        pass

    def delete_by_file_id(self, file_id: str) -> None:
        MockVectorStore.deleted_file_ids.append(file_id)


class MockFileStorage:
    def __init__(self):
        self.saved_paths: list[str] = []

    def save(self, file, filename: str, subdir: str = "") -> str:
        path = f"/tmp/uploads/{subdir}/{filename}"
        self.saved_paths.append(path)
        return path

    def delete_dir(self, subdir: str) -> bool:
        return True


def _mock_processor_result(*args, **kwargs):
    return {
        "chunk_count": 5,
        "status": "indexed",
        "message": "ok",
    }


def test_upload_persists_to_db(sqlite_file_db):
    storage = MockFileStorage()
    processor = MagicMock()
    processor.process.side_effect = _mock_processor_result
    service = FileService(
        storage=storage,
        processor=processor,
        vector_store_cls=MockVectorStore,
    )

    result = service.upload(
        file=BytesIO(b"hello world"),
        filename="notes.txt",
        user_id="user-1",
        visibility=DOC_VISIBILITY_PRIVATE,
    )

    assert result["filename"] == "notes.txt"
    assert result["chunk_count"] == 5
    assert result["visibility"] == DOC_VISIBILITY_PRIVATE

    listed = list_files_for_user("user-1")
    assert listed["total"] == 1
    assert listed["files"][0]["file_id"] == result["file_id"]

    collections = list_collections_for_user("user-1")
    assert collections["collections"][0]["file_id"] == result["file_id"]


def test_get_file_record(sqlite_file_db):
    with get_db_session() as session:
        repo = FileRepository(session)
        repo.create(
            id="file-123",
            user_id="user-1",
            filename="report.pdf",
            storage_path="/tmp/user-1/file-123/report.pdf",
            visibility=DOC_VISIBILITY_PUBLIC,
            chunk_count=2,
            status="indexed",
        )

    record = get_file_record("file-123")
    assert record["filename"] == "report.pdf"
    assert record["visibility"] == DOC_VISIBILITY_PUBLIC


def test_same_filename_reupload_replaces_old_record(sqlite_file_db):
    MockVectorStore.deleted_file_ids.clear()
    storage = MockFileStorage()
    processor = MagicMock()
    processor.process.side_effect = _mock_processor_result
    service = FileService(
        storage=storage,
        processor=processor,
        vector_store_cls=MockVectorStore,
    )

    first = service.upload(
        file=BytesIO(b"version1"),
        filename="dup.txt",
        user_id="user-1",
        visibility=DOC_VISIBILITY_PRIVATE,
    )
    second = service.upload(
        file=BytesIO(b"version2"),
        filename="dup.txt",
        user_id="user-1",
        visibility=DOC_VISIBILITY_PRIVATE,
    )

    assert first["file_id"] != second["file_id"]
    assert MockVectorStore.deleted_file_ids == [first["file_id"]]

    listed = list_files_for_user("user-1")
    assert listed["total"] == 1
    assert listed["files"][0]["file_id"] == second["file_id"]

    with get_db_session() as session:
        rows = list(session.scalars(select(File).where(File.user_id == "user-1")).all())
        assert len(rows) == 1
        assert rows[0].id == second["file_id"]
