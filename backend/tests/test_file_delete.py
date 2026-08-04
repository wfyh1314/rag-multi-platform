"""FileService 删除功能测试."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from config.constants import DOC_VISIBILITY_PRIVATE
from config.response_codes import NOT_FOUND
from config.settings import get_settings
from core.exceptions import AppError, PermissionDeniedError
from file_mgr.file_service import FileService, get_file_record
import storage.mysql_db as mysql_db
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
    deleted_dirs: list[str] = []

    def delete_dir(self, subdir: str) -> bool:
        MockFileStorage.deleted_dirs.append(subdir)
        return True


def _register(user_id: str, file_id: str, filename: str = "test.txt") -> None:
    with get_db_session() as session:
        repo = FileRepository(session)
        repo.create(
            id=file_id,
            user_id=user_id,
            filename=filename,
            storage_path=f"/tmp/{user_id}/{file_id}/{filename}",
            visibility=DOC_VISIBILITY_PRIVATE,
            chunk_count=3,
            status="indexed",
            message="ok",
        )


def test_delete_removes_registry_and_calls_storage(sqlite_file_db):
    MockVectorStore.deleted_file_ids.clear()
    MockFileStorage.deleted_dirs.clear()
    _register("user-1", "file-abc")

    service = FileService(
        storage=MockFileStorage(),
        vector_store_cls=MockVectorStore,
    )
    assert service.delete("file-abc", {"user_id": "user-1"}) is True

    assert get_file_record("file-abc") is None
    assert MockVectorStore.deleted_file_ids == ["file-abc"]
    assert MockFileStorage.deleted_dirs == ["user-1/file-abc"]


def test_delete_not_found_raises(sqlite_file_db):
    service = FileService(storage=MockFileStorage(), vector_store_cls=MockVectorStore)
    with pytest.raises(AppError) as exc_info:
        service.delete("missing-id", {"user_id": "user-1"})
    assert exc_info.value.status_code == 404
    assert exc_info.value.code == NOT_FOUND


def test_delete_other_user_raises(sqlite_file_db):
    _register("user-1", "file-abc")
    service = FileService(storage=MockFileStorage(), vector_store_cls=MockVectorStore)
    with pytest.raises(PermissionDeniedError):
        service.delete("file-abc", {"user_id": "user-2"})
