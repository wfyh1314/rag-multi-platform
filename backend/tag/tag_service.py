"""标签业务服务."""

import uuid
from typing import Any

from config.response_codes import NOT_FOUND
from core.doc_permission import DocPermissionService
from core.exceptions import AppError, ValidationError
from core.logger import get_logger
from document.loaders import load_document
from storage.mysql_db import get_db_session
from storage.models.file_tag import TAG_SOURCE_AUTO, TAG_SOURCE_MANUAL
from storage.repositories.file_repository import FileRepository
from storage.repositories.file_tag_repository import FileTagRepository
from storage.repositories.tag_repository import TagRepository
from tag.tag_matcher import match_tag_ids

logger = get_logger()
_doc_permission = DocPermissionService()


def _load_file_content(file_path: str) -> str:
    chunks = load_document(file_path)
    return "\n".join(chunk.content for chunk in chunks if chunk.content)


class TagService:
    """标签字典与文档打标。"""

    def list_categories_tree(self) -> dict[str, Any]:
        with get_db_session() as session:
            tag_repo = TagRepository(session)
            categories = []
            for category in tag_repo.list_categories():
                tags = tag_repo.list_tags_by_category(category.id)
                categories.append(tag_repo.category_to_dict(category, tags))
            return {"categories": categories, "total": len(categories)}

    def create_category(self, name: str) -> dict[str, Any]:
        value = name.strip()
        if not value:
            raise ValidationError("分类名称不能为空")

        with get_db_session() as session:
            tag_repo = TagRepository(session)
            existing = [item for item in tag_repo.list_categories() if item.name == value]
            if existing:
                raise ValidationError(f"分类已存在: {value}")

            sort_order = len(tag_repo.list_categories())
            category = tag_repo.create_category(
                id=str(uuid.uuid4()),
                name=value,
                sort_order=sort_order,
            )
            return tag_repo.category_to_dict(category, [])

    def update_category(self, category_id: str, name: str) -> dict[str, Any]:
        value = name.strip()
        if not value:
            raise ValidationError("分类名称不能为空")

        with get_db_session() as session:
            tag_repo = TagRepository(session)
            category = tag_repo.get_category(category_id)
            if category is None:
                raise AppError(f"分类不存在: {category_id}", code=NOT_FOUND, status_code=404)

            duplicate = [
                item
                for item in tag_repo.list_categories()
                if item.name == value and item.id != category_id
            ]
            if duplicate:
                raise ValidationError(f"分类已存在: {value}")

            tag_repo.update_category(category, name=value)
            tags = tag_repo.list_tags_by_category(category_id)
            return tag_repo.category_to_dict(category, tags)

    def delete_category(self, category_id: str) -> None:
        with get_db_session() as session:
            tag_repo = TagRepository(session)
            category = tag_repo.get_category(category_id)
            if category is None:
                raise AppError(f"分类不存在: {category_id}", code=NOT_FOUND, status_code=404)
            tag_repo.delete_category(category)

    def create_tag(self, category_id: str, name: str, keywords: str) -> dict[str, Any]:
        tag_name = name.strip()
        if not tag_name:
            raise ValidationError("标签名称不能为空")

        with get_db_session() as session:
            tag_repo = TagRepository(session)
            category = tag_repo.get_category(category_id)
            if category is None:
                raise AppError(f"分类不存在: {category_id}", code=NOT_FOUND, status_code=404)

            tag = tag_repo.create_tag(
                id=str(uuid.uuid4()),
                category_id=category_id,
                name=tag_name,
                keywords=(keywords or "").strip(),
            )
            return tag_repo.tag_to_dict(tag, category.name)

    def update_tag(self, tag_id: str, name: str, keywords: str) -> dict[str, Any]:
        tag_name = name.strip()
        if not tag_name:
            raise ValidationError("标签名称不能为空")

        with get_db_session() as session:
            tag_repo = TagRepository(session)
            tag = tag_repo.get_tag(tag_id)
            if tag is None:
                raise AppError(f"标签不存在: {tag_id}", code=NOT_FOUND, status_code=404)

            category = tag_repo.get_category(tag.category_id)
            tag_repo.update_tag(tag, name=tag_name, keywords=(keywords or "").strip())
            return tag_repo.tag_to_dict(tag, category.name if category else None)

    def delete_tag(self, tag_id: str) -> None:
        with get_db_session() as session:
            tag_repo = TagRepository(session)
            tag = tag_repo.get_tag(tag_id)
            if tag is None:
                raise AppError(f"标签不存在: {tag_id}", code=NOT_FOUND, status_code=404)
            tag_repo.delete_tag(tag)

    def list_files_with_tags(
        self,
        user_id: str,
        keyword: str | None = None,
        folder_id: str | None = None,
    ) -> dict[str, Any]:
        from file_mgr.file_service import list_files_for_user

        files_result = list_files_for_user(user_id, keyword, folder_id=folder_id)
        file_ids = [item["file_id"] for item in files_result["files"]]

        tags_by_file: dict[str, list[dict[str, Any]]] = {file_id: [] for file_id in file_ids}
        if file_ids:
            with get_db_session() as session:
                file_tag_repo = FileTagRepository(session)
                tags_by_file = file_tag_repo.list_tag_details_by_file_ids(file_ids)

        files = []
        for item in files_result["files"]:
            files.append({**item, "tags": tags_by_file.get(item["file_id"], [])})

        return {"files": files, "total": len(files)}

    def get_file_tags(self, user: dict[str, Any], file_id: str) -> dict[str, Any]:
        from file_mgr.file_service import get_accessible_file_record

        record = get_accessible_file_record(user, file_id)
        with get_db_session() as session:
            file_tag_repo = FileTagRepository(session)
            tags = file_tag_repo.list_tag_details_by_file_id(file_id)
        return {"file_id": file_id, "filename": record["filename"], "tags": tags}

    def set_manual_file_tags(
        self, user: dict[str, Any], file_id: str, tag_ids: list[str]
    ) -> dict[str, Any]:
        from file_mgr.file_service import get_accessible_file_record

        get_accessible_file_record(user, file_id)

        with get_db_session() as session:
            tag_repo = TagRepository(session)
            file_tag_repo = FileTagRepository(session)

            valid_ids: list[str] = []
            for tag_id in tag_ids:
                if tag_repo.get_tag(tag_id) is None:
                    raise ValidationError(f"标签不存在: {tag_id}")
                valid_ids.append(tag_id)

            file_tag_repo.replace_manual_tags(file_id, valid_ids)
            tags = file_tag_repo.list_tag_details_by_file_id(file_id)

        self.sync_tags_to_qdrant(file_id)
        return {"file_id": file_id, "tags": tags}

    def auto_tag_file(self, file_id: str, file_path: str) -> list[str]:
        try:
            content = _load_file_content(file_path)
        except Exception as exc:
            logger.warning("自动打标读取文档失败 file_id=%s: %s", file_id, exc)
            return []

        with get_db_session() as session:
            tag_repo = TagRepository(session)
            file_tag_repo = FileTagRepository(session)
            all_tags = tag_repo.list_all_tags()
            matched_ids = match_tag_ids(content, all_tags)

            existing = file_tag_repo.get_tag_ids_by_file_id(file_id)
            manual_ids = {
                item.tag_id
                for item in file_tag_repo.list_by_file_id(file_id)
                if item.source == TAG_SOURCE_MANUAL
            }

            file_tag_repo.delete_auto_by_file_id(file_id)
            auto_ids = [tag_id for tag_id in matched_ids if tag_id not in manual_ids]
            file_tag_repo.add_tags(file_id, auto_ids, TAG_SOURCE_AUTO)

            final_ids = sorted(existing | set(auto_ids) | manual_ids)

        self.sync_tags_to_qdrant(file_id)
        return final_ids

    def sync_tags_to_qdrant(self, file_id: str) -> None:
        """将 MySQL 中的标签同步到 Qdrant chunk payload。"""
        with get_db_session() as session:
            tag_ids = sorted(FileTagRepository(session).get_tag_ids_by_file_id(file_id))
        try:
            from storage.vector_store import VectorStore
            VectorStore().set_payload_by_filter(
                {"file_id": file_id},
                {"tag_ids": tag_ids},
            )
        except Exception as exc:
            logger.warning("同步标签到 Qdrant 失败 file_id=%s: %s", file_id, exc)

    def rerun_auto_tags(
        self, user: dict[str, Any], file_ids: list[str] | None = None
    ) -> dict[str, Any]:
        from file_mgr.file_service import get_accessible_file_record, list_files_for_user

        user_id = user.get("user_id", "")
        if file_ids:
            targets = []
            for file_id in file_ids:
                record = get_accessible_file_record(user, file_id)
                targets.append(record)
        else:
            targets = list_files_for_user(user_id)["files"]

        success_count = 0
        failed: list[dict[str, str]] = []

        for item in targets:
            file_id = item["file_id"]
            with get_db_session() as session:
                repo = FileRepository(session)
                record = repo.get_by_id(file_id)
                if record is None:
                    failed.append({"file_id": file_id, "reason": "文件不存在"})
                    continue
                storage_path = record.storage_path

            try:
                self.auto_tag_file(file_id, storage_path)
                self.sync_tags_to_qdrant(file_id)
                success_count += 1
            except Exception as exc:
                logger.warning("批量重跑标签失败 file_id=%s: %s", file_id, exc)
                failed.append({"file_id": file_id, "reason": str(exc)})

        return {
            "total": len(targets),
            "success_count": success_count,
            "failed": failed,
        }

    def delete_file_tags(self, file_id: str) -> None:
        with get_db_session() as session:
            FileTagRepository(session).delete_by_file_id(file_id)
