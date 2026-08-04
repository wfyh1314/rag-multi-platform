"""多级树形文件夹 CRUD."""

import uuid
from typing import Any, Optional

from config.response_codes import NOT_FOUND
from core.exceptions import AppError, ValidationError
from storage.mysql_db import get_db_session
from storage.repositories.folder_repository import FolderRepository


class FolderService:
    """管理多级树形文件夹。"""

    def create(
        self,
        name: str,
        parent_id: Optional[str] = None,
        user_id: Optional[str] = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """创建文件夹。"""
        folder_name = name.strip()
        if not folder_name:
            raise ValidationError("文件夹名称不能为空")
        if not user_id:
            raise ValidationError("缺少 user_id")
        with get_db_session() as session:
            repo = FolderRepository(session)
            if parent_id:
                parent = repo.get_by_id_for_user(parent_id, user_id)
                if parent is None:
                    raise AppError("父文件夹不存在", code=NOT_FOUND, status_code=404)
            record = repo.create(
                id=str(uuid.uuid4()),
                user_id=user_id,
                name=folder_name,
                parent_id=parent_id,
            )
            return FolderRepository.to_dict(record)

    def list_tree(
        self,
        parent_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        """获取文件夹树。"""
        if not user_id:
            return []
        with get_db_session() as session:
            repo = FolderRepository(session)
            all_folders = repo.list_by_user(user_id)
            folder_dicts = [FolderRepository.to_dict(folder) for folder in all_folders]

        by_parent: dict[str | None, list[dict[str, Any]]] = {}
        for item in folder_dicts:
            item["children"] = []
            by_parent.setdefault(item["parent_id"], []).append(item)

        def attach_children(node: dict[str, Any]) -> dict[str, Any]:
            children = by_parent.get(node["id"], [])
            node["children"] = [attach_children(c) for c in children]
            return node

        roots = by_parent.get(parent_id, by_parent.get(None, []))
        return [attach_children(r) for r in roots]

    def rename(self, folder_id: str, name: str, user_id: str) -> dict[str, Any]:
        """重命名文件夹。"""
        new_name = name.strip()
        if not new_name:
            raise ValidationError("文件夹名称不能为空")
        with get_db_session() as session:
            repo = FolderRepository(session)
            record = repo.get_by_id_for_user(folder_id, user_id)
            if record is None:
                raise AppError("文件夹不存在", code=NOT_FOUND, status_code=404)
            repo.update(record, name=new_name)
            return FolderRepository.to_dict(record)

    def move(
        self,
        folder_id: str,
        new_parent_id: Optional[str],
        user_id: str,
    ) -> dict[str, Any]:
        """将文件夹移动到新父级。"""
        if folder_id == new_parent_id:
            raise ValidationError("不能将文件夹移动到自身")
        with get_db_session() as session:
            repo = FolderRepository(session)
            record = repo.get_by_id_for_user(folder_id, user_id)
            if record is None:
                raise AppError("文件夹不存在", code=NOT_FOUND, status_code=404)
            if new_parent_id:
                parent = repo.get_by_id_for_user(new_parent_id, user_id)
                if parent is None:
                    raise AppError("目标父文件夹不存在", code=NOT_FOUND, status_code=404)
            repo.update(record, parent_id=new_parent_id)
            return FolderRepository.to_dict(record)

    def delete(self, folder_id: str, user_id: str) -> bool:
        """删除空文件夹。"""
        with get_db_session() as session:
            repo = FolderRepository(session)
            record = repo.get_by_id_for_user(folder_id, user_id)
            if record is None:
                raise AppError("文件夹不存在", code=NOT_FOUND, status_code=404)
            if repo.count_children(folder_id) > 0:
                raise ValidationError("文件夹非空，请先删除子文件夹")
            if repo.count_files(folder_id) > 0:
                raise ValidationError("文件夹内仍有文件，请先移出或删除文件")
            repo.delete(record)
            return True
