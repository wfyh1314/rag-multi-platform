"""文件上传、批量上传、预览、移动、删除、状态更新."""

import uuid
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path
from typing import Any, BinaryIO, Optional

from config.constants import ALLOWED_EXTENSIONS, MAX_UPLOAD_SIZE_MB
from core.exceptions import FileParseError, ValidationError
from core.utils import get_file_extension
from document.pipeline import DocumentProcessor
from file_mgr.file_storage import FileStorage

# 按租户记录已上传文件（内存注册表，供前端知识库下拉使用）
_upload_registry: dict[str, list[dict[str, Any]]] = {}


def list_files_for_tenant(tenant_id: str, keyword: str | None = None) -> dict[str, Any]:
    """返回租户文件列表，支持文件名模糊搜索。"""
    items = list(_upload_registry.get(tenant_id, []))
    if keyword:
        kw = keyword.strip().lower()
        if kw:
            items = [item for item in items if kw in item.get("filename", "").lower()]
    items.sort(key=lambda x: x.get("uploaded_at", ""), reverse=True)
    return {"files": items, "total": len(items)}


def list_collections_for_tenant(tenant_id: str) -> dict[str, list]:
    """返回租户已索引文件列表，供 /api/collections 使用。"""
    items = _upload_registry.get(tenant_id, [])
    return {
        "collections": [item["filename"] for item in items],
        "pending": [],
    }


def get_file_id_by_filename(tenant_id: str, filename: str) -> str | None:
    """根据文件名解析 file_id，供 RAG 检索过滤使用。"""
    for item in _upload_registry.get(tenant_id, []):
        if item.get("filename") == filename:
            return item.get("file_id")
    return None


def _register_upload(tenant_id: str, record: dict[str, Any]) -> None:
    """登记上传成功的文件，同名文件以最新记录为准。"""
    items = _upload_registry.setdefault(tenant_id, [])
    items[:] = [item for item in items if item.get("filename") != record["filename"]]
    items.append(record)


class FileService:
    """管理文件上传与生命周期。"""

    def __init__(
        self,
        storage: Optional[FileStorage] = None,
        processor: Optional[DocumentProcessor] = None,
    ):
        self.storage = storage or FileStorage()
        self.processor = processor or DocumentProcessor()

    def upload(
        self,
        file: BinaryIO,
        filename: str,
        tenant_id: str,
        user_id: str,
        folder_id: Optional[str] = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """上传文件，同步执行解析、清洗、分块、向量化与入库。"""
        ext = get_file_extension(filename)
        if ext not in ALLOWED_EXTENSIONS:
            raise ValidationError(f"不支持的文件格式: {ext}")

        content = file.read()
        max_bytes = MAX_UPLOAD_SIZE_MB * 1024 * 1024
        if len(content) > max_bytes:
            raise ValidationError(f"文件大小超过限制 ({MAX_UPLOAD_SIZE_MB}MB)")

        file_id = str(uuid.uuid4())
        safe_name = Path(filename).name
        subdir = f"{tenant_id}/{file_id}"
        saved_path = self.storage.save(BytesIO(content), safe_name, subdir=subdir)

        try:
            result = self.processor.process(
                file_path=saved_path,
                tenant_id=tenant_id,
                file_id=file_id,
                user_id=user_id,
            )
        except FileParseError:
            raise
        except Exception as exc:
            raise FileParseError(f"文档处理失败: {exc}", filename=safe_name) from exc

        upload_record = {
            "file_id": file_id,
            "filename": safe_name,
            "tenant_id": tenant_id,
            "user_id": user_id,
            "folder_id": folder_id,
            "chunk_count": result["chunk_count"],
            "status": result["status"],
            "message": result["message"],
            "uploaded_at": datetime.now(timezone.utc).isoformat(),
        }
        _register_upload(tenant_id, upload_record)
        return upload_record

    def batch_upload(
        self,
        files: list[tuple[BinaryIO, str]],
        tenant_id: str,
        user_id: str,
        folder_id: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        """批量上传文件。"""
        results = []
        for file_obj, name in files:
            results.append(self.upload(file_obj, name, tenant_id, user_id, folder_id))
        return results

    def preview(self, file_id: str, tenant_id: str) -> dict[str, Any]:
        """获取文件预览内容。"""
        raise NotImplementedError

    def move(self, file_id: str, folder_id: str, tenant_id: str) -> dict[str, Any]:
        """将文件移动到其他文件夹。"""
        raise NotImplementedError

    def delete(self, file_id: str, tenant_id: str) -> bool:
        """删除文件。"""
        raise NotImplementedError

    def update_status(self, file_id: str, status: str, tenant_id: str) -> dict[str, Any]:
        """更新文件解析/索引状态。"""
        raise NotImplementedError
