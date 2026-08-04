"""会话创建、命名、归档、删除."""

import uuid
from typing import Any, Optional

from config.response_codes import NOT_FOUND
from core.exceptions import AppError, ValidationError
from storage.mysql_db import get_db_session
from storage.repositories.message_repository import MessageRepository
from storage.repositories.session_repository import SessionRepository


class SessionService:
    """管理聊天会话。"""

    def create(
        self,
        user_id: str,
        title: Optional[str] = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """创建新聊天会话。"""
        session_title = (title or "新对话").strip() or "新对话"
        session_id = str(uuid.uuid4())
        with get_db_session() as session:
            repo = SessionRepository(session)
            record = repo.create(
                id=session_id,
                user_id=user_id,
                title=session_title,
            )
            return SessionRepository.to_dict(record)

    def rename(self, session_id: str, title: str, user_id: str) -> dict[str, Any]:
        """重命名会话。"""
        new_title = title.strip()
        if not new_title:
            raise ValidationError("会话标题不能为空")
        with get_db_session() as session:
            repo = SessionRepository(session)
            record = repo.get_by_id_for_user(session_id, user_id)
            if record is None:
                raise AppError("会话不存在", code=NOT_FOUND, status_code=404)
            repo.update(record, title=new_title)
            return SessionRepository.to_dict(record)

    def archive(self, session_id: str, user_id: str) -> dict[str, Any]:
        """归档会话。"""
        with get_db_session() as session:
            repo = SessionRepository(session)
            record = repo.get_by_id_for_user(session_id, user_id)
            if record is None:
                raise AppError("会话不存在", code=NOT_FOUND, status_code=404)
            repo.update(record, is_archived=True)
            return SessionRepository.to_dict(record)

    def delete(self, session_id: str, user_id: str) -> bool:
        """删除会话及其消息。"""
        with get_db_session() as session:
            repo = SessionRepository(session)
            msg_repo = MessageRepository(session)
            record = repo.get_by_id_for_user(session_id, user_id)
            if record is None:
                raise AppError("会话不存在", code=NOT_FOUND, status_code=404)
            msg_repo.delete_by_session(session_id)
            repo.delete(record)
        try:
            from audit.op_log_service import OpLogService
            OpLogService().log(
                user_id=user_id,
                action="session.delete",
                resource_type="session",
                resource_id=session_id,
            )
        except Exception:
            pass
        return True

    def list_sessions(
        self, user_id: str, include_archived: bool = False
    ) -> list[dict[str, Any]]:
        """获取用户会话列表。"""
        with get_db_session() as session:
            repo = SessionRepository(session)
            records = repo.list_by_user(user_id, include_archived=include_archived)
            return [SessionRepository.to_dict(r) for r in records]

    def import_sessions(
        self, user_id: str, sessions: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """批量导入会话及消息（localStorage 迁移）。"""
        from chat.history_service import HistoryService

        history = HistoryService()
        imported: list[dict[str, Any]] = []
        for item in sessions:
            title = (item.get("title") or "新对话").strip() or "新对话"
            created = self.create(user_id, title=title)
            session_id = created["id"]
            for msg in item.get("messages") or []:
                role = msg.get("role")
                content = msg.get("content", "")
                if role and content:
                    history.save_message(session_id, role, content, user_id=user_id)
            imported.append(created)
        return imported

    def get_session(self, session_id: str, user_id: str) -> dict[str, Any]:
        """获取单个会话（校验归属）。"""
        with get_db_session() as session:
            repo = SessionRepository(session)
            record = repo.get_by_id_for_user(session_id, user_id)
            if record is None:
                raise AppError("会话不存在", code=NOT_FOUND, status_code=404)
            return SessionRepository.to_dict(record)
