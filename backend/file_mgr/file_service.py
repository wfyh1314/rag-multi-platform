"""文件上传、批量上传、预览、移动、删除、状态更新."""

import uuid
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path
from typing import Any, BinaryIO, Optional

from config.constants import ALLOWED_EXTENSIONS, DOC_VISIBILITY_PRIVATE, DOC_VISIBILITY_PUBLIC, MAX_UPLOAD_SIZE_MB
from config.response_codes import NOT_FOUND
from core.doc_permission import DocPermissionService
from core.exceptions import AppError, FileParseError, ValidationError
from core.logger import get_logger
from core.utils import get_file_extension
from document.loaders import load_document
from document.pipeline import DocumentProcessor
from file_mgr.file_storage import FileStorage
from storage.mysql_db import get_db_session
from storage.repositories.file_repository import FileRepository
from storage.vector_store import VectorStore

logger = get_logger()
_doc_permission = DocPermissionService()


def _normalize_visibility(visibility: str | None) -> str:
    value = (visibility or DOC_VISIBILITY_PRIVATE).strip().lower()
    if value not in {DOC_VISIBILITY_PRIVATE, DOC_VISIBILITY_PUBLIC}:
        raise ValidationError(f"不支持的可见性: {visibility}")
    return value


def list_files_for_user(
    user_id: str,
    keyword: str | None = None,
    folder_id: str | None = None,
) -> dict[str, Any]:
    """返回当前用户可访问的文件列表。"""
    with get_db_session() as session:
        repo = FileRepository(session)
        items = [
            FileRepository.to_dict(record)
            for record in repo.list_accessible(user_id, keyword, folder_id=folder_id)
        ]
    return {"files": items, "total": len(items)}


def list_collections_for_user(user_id: str) -> dict[str, list]:
    """返回当前用户可选知识库列表。"""
    with get_db_session() as session:
        repo = FileRepository(session)
        collections = [
            {
                "file_id": record.id,
                "filename": record.filename,
                "visibility": record.visibility,
            }
            for record in repo.list_accessible(user_id)
        ]
    return {"collections": collections, "pending": []}


def get_file_record(file_id: str) -> dict[str, Any] | None:
    """按 file_id 查找上传记录。"""
    with get_db_session() as session:
        repo = FileRepository(session)
        record = repo.get_by_id(file_id)
        if record is None:
            return None
        return FileRepository.to_dict(record)


def get_accessible_file_record(user: dict[str, Any], file_id: str) -> dict[str, Any]:
    """获取用户有权访问的文件记录。"""
    record = get_file_record(file_id)
    if record is None:
        raise AppError(f"文件不存在: {file_id}", code=NOT_FOUND, status_code=404)
    _doc_permission.require_access(user, record)
    return record


class FileService:
    """管理文件上传与生命周期。"""

    def __init__(
        self,
        storage: Optional[FileStorage] = None,
        processor: Optional[DocumentProcessor] = None,
        vector_store_cls: type[VectorStore] = VectorStore,
    ):
        self.storage = storage or FileStorage()
        self.processor = processor or DocumentProcessor()
        self._vector_store_cls = vector_store_cls
        self._tag_service = None
        from config.settings import get_settings
        self.settings = get_settings()

    @property
    def tag_service(self):
        if self._tag_service is None:
            from tag.tag_service import TagService

            self._tag_service = TagService()
        return self._tag_service

    def upload(
        self,
        file: BinaryIO,
        filename: str,
        user_id: str,
        visibility: str = DOC_VISIBILITY_PRIVATE,
        folder_id: Optional[str] = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """上传文件，同步执行解析、清洗、分块、向量化与入库。"""
        ext = get_file_extension(filename)
        if ext not in ALLOWED_EXTENSIONS:
            raise ValidationError(f"不支持的文件格式: {ext}")

        visibility = _normalize_visibility(visibility)
        content = file.read()
        max_bytes = MAX_UPLOAD_SIZE_MB * 1024 * 1024
        if len(content) > max_bytes:
            raise ValidationError(f"文件大小超过限制 ({MAX_UPLOAD_SIZE_MB}MB)")

        safe_name = Path(filename).name
        async_threshold = self.settings.async_upload_threshold_mb * 1024 * 1024
        use_async = len(content) > async_threshold

        with get_db_session() as session:
            repo = FileRepository(session)
            existing = repo.get_by_user_filename(user_id, safe_name)
            if existing is not None:
                self._delete_existing(existing)
                repo.delete(existing)

        file_id = str(uuid.uuid4())
        subdir = f"{user_id}/{file_id}"
        saved_path = self.storage.save(BytesIO(content), safe_name, subdir=subdir)

        if use_async:
            uploaded_at = datetime.now(timezone.utc)
            with get_db_session() as session:
                repo = FileRepository(session)
                record = repo.create(
                    id=file_id,
                    user_id=user_id,
                    filename=safe_name,
                    storage_path=saved_path,
                    folder_id=folder_id,
                    visibility=visibility,
                    chunk_count=0,
                    status="pending",
                    message="等待异步解析",
                    uploaded_at=uploaded_at,
                )
                result_dict = FileRepository.to_dict(record)
            from tasks.parse_file_task import parse_file_task
            parse_file_task.delay(file_id, saved_path, user_id, visibility)
            try:
                from audit.op_log_service import OpLogService
                OpLogService().log(
                    user_id=user_id,
                    action="file.upload",
                    resource_type="file",
                    resource_id=file_id,
                    detail={"filename": safe_name, "async": True},
                )
            except Exception:
                pass
            return result_dict

        try:
            result = self.processor.process(
                file_path=saved_path,
                file_id=file_id,
                user_id=user_id,
                visibility=visibility,
            )
        except FileParseError:
            self.storage.delete_dir(subdir)
            raise
        except Exception as exc:
            self.storage.delete_dir(subdir)
            raise FileParseError(f"文档处理失败: {exc}", filename=safe_name) from exc

        uploaded_at = datetime.now(timezone.utc)
        with get_db_session() as session:
            repo = FileRepository(session)
            record = repo.create(
                id=file_id,
                user_id=user_id,
                filename=safe_name,
                storage_path=saved_path,
                folder_id=folder_id,
                visibility=visibility,
                chunk_count=result["chunk_count"],
                status=result["status"],
                message=result["message"],
                uploaded_at=uploaded_at,
            )
            try:
                self.tag_service.auto_tag_file(file_id, saved_path)
            except Exception as exc:
                logger.warning("上传后自动打标失败 file_id=%s: %s", file_id, exc)
            result_dict = FileRepository.to_dict(record)
        try:
            from audit.op_log_service import OpLogService
            OpLogService().log(
                user_id=user_id,
                action="file.upload",
                resource_type="file",
                resource_id=file_id,
                detail={"filename": safe_name},
            )
        except Exception:
            pass
        return result_dict

    def batch_upload(
        self,
        files: list[tuple[BinaryIO, str]],
        user_id: str,
        visibility: str = DOC_VISIBILITY_PRIVATE,
        folder_id: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        """批量上传文件。"""
        results = []
        for file_obj, name in files:
            results.append(self.upload(file_obj, name, user_id, visibility, folder_id))
        return results

    def preview(self, file_id: str, user: dict[str, Any]) -> dict[str, Any]:
        """获取文件预览内容。"""
        record = get_accessible_file_record(user, file_id)
        storage_path = record.get("storage_path")
        if not storage_path:
            raise AppError("文件路径不存在", code=NOT_FOUND, status_code=404)
        try:
            chunks = load_document(storage_path)
            preview_text = "\n\n".join(c.content for c in chunks[:5] if c.content)
            if len(preview_text) > 8000:
                preview_text = preview_text[:8000] + "\n...(预览截断)"
            return {
                "file_id": file_id,
                "filename": record["filename"],
                "preview": preview_text or "(无文本内容)",
                "chunk_count": len(chunks),
            }
        except Exception as exc:
            raise FileParseError(f"预览失败: {exc}", filename=record["filename"]) from exc

    def move(self, file_id: str, folder_id: str, user: dict[str, Any]) -> dict[str, Any]:
        """将文件移动到其他文件夹。"""
        with get_db_session() as session:
            repo = FileRepository(session)
            record = repo.get_by_id(file_id)
            if record is None:
                raise AppError(f"文件不存在: {file_id}", code=NOT_FOUND, status_code=404)
            record_dict = FileRepository.to_dict(record)
            _doc_permission.require_access(user, record_dict)
            if folder_id:
                from storage.repositories.folder_repository import FolderRepository
                folder_repo = FolderRepository(session)
                folder = folder_repo.get_by_id_for_user(folder_id, user.get("user_id", user.get("id", "")))
                if folder is None:
                    raise AppError("目标文件夹不存在", code=NOT_FOUND, status_code=404)
            record.folder_id = folder_id or None
            session.flush()
            return FileRepository.to_dict(record)

    def delete(self, file_id: str, user: dict[str, Any]) -> bool:
        """删除文件：向量索引、本地磁盘、数据库记录。"""
        user_id = user.get("user_id", user.get("id", ""))
        with get_db_session() as session:
            repo = FileRepository(session)
            record = repo.get_by_id(file_id)
            if record is None:
                raise AppError(
                    f"文件不存在: {file_id}",
                    code=NOT_FOUND,
                    status_code=404,
                )
            record_dict = FileRepository.to_dict(record)
            _doc_permission.require_delete(user, record_dict)
            self._delete_existing(record)
            repo.delete(record)
        try:
            from audit.op_log_service import OpLogService
            OpLogService().log(
                user_id=user_id,
                action="file.delete",
                resource_type="file",
                resource_id=file_id,
                detail={"filename": record_dict.get("filename")},
            )
        except Exception:
            pass
        return True

    def _delete_existing(self, record) -> None:
        """删除向量与磁盘文件。"""
        file_id = record.id
        user_id = record.user_id
        try:
            self.tag_service.delete_file_tags(file_id)
        except Exception as exc:
            logger.warning("删除文档标签失败 file_id=%s: %s", file_id, exc)
        try:
            self._vector_store_cls().delete_by_file_id(file_id)
        except Exception as exc:
            logger.warning("删除 Qdrant 向量失败 file_id=%s: %s", file_id, exc)

        self.storage.delete_dir(f"{user_id}/{file_id}")

    def update_status(self, file_id: str, status: str, user: dict[str, Any]) -> dict[str, Any]:
        """更新文件解析/索引状态。"""
        with get_db_session() as session:
            repo = FileRepository(session)
            record = repo.get_by_id(file_id)
            if record is None:
                raise AppError(f"文件不存在: {file_id}", code=NOT_FOUND, status_code=404)
            record_dict = FileRepository.to_dict(record)
            _doc_permission.require_access(user, record_dict)
            record.status = status
            session.flush()
            return FileRepository.to_dict(record)
