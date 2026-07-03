"""FileService 删除功能测试."""

import pytest

from core.exceptions import AppError
from file_mgr import file_service as file_service_module
from file_mgr.file_service import FileService, get_file_record


@pytest.fixture(autouse=True)
def clear_registry():
    file_service_module._upload_registry.clear()
    yield
    file_service_module._upload_registry.clear()


class MockVectorStore:
    deleted_file_ids: list[str] = []

    def __init__(self, tenant_id: str, settings=None):
        self.tenant_id = tenant_id

    def delete_by_file_id(self, file_id: str) -> None:
        MockVectorStore.deleted_file_ids.append(file_id)


class MockFileStorage:
    deleted_dirs: list[str] = []

    def delete_dir(self, subdir: str) -> bool:
        MockFileStorage.deleted_dirs.append(subdir)
        return True


def _register(tenant_id: str, file_id: str, filename: str = "test.txt") -> None:
    file_service_module._upload_registry.setdefault(tenant_id, []).append({
        "file_id": file_id,
        "filename": filename,
        "tenant_id": tenant_id,
        "status": "indexed",
        "chunk_count": 3,
    })


def test_delete_removes_registry_and_calls_storage():
    MockVectorStore.deleted_file_ids.clear()
    MockFileStorage.deleted_dirs.clear()
    _register("tenant-1", "file-abc")

    service = FileService(
        storage=MockFileStorage(),
        vector_store_cls=MockVectorStore,
    )
    assert service.delete("file-abc", "tenant-1") is True

    assert get_file_record("tenant-1", "file-abc") is None
    assert MockVectorStore.deleted_file_ids == ["file-abc"]
    assert MockFileStorage.deleted_dirs == ["tenant-1/file-abc"]


def test_delete_not_found_raises():
    service = FileService(storage=MockFileStorage(), vector_store_cls=MockVectorStore)
    with pytest.raises(AppError) as exc_info:
        service.delete("missing-id", "tenant-1")
    assert exc_info.value.status_code == 404
    assert exc_info.value.code == "FILE_NOT_FOUND"
