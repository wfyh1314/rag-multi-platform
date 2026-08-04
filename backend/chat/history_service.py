"""历史对话持久化查询、溯源文档记录."""

import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from config.response_codes import NOT_FOUND
from core.exceptions import AppError
from storage.mysql_db import get_db_session
from storage.repositories.message_repository import MessageRepository
from storage.repositories.session_repository import SessionRepository


class HistoryService:
    """管理聊天历史与引用文档。"""

    def save_message(
        self,
        session_id: str,
        role: str,
        content: str,
        sources: Optional[list[dict[str, Any]]] = None,
        user_id: Optional[str] = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """保存聊天消息，可选附带引用文档。"""
        message_id = kwargs.get("message_id") or str(uuid.uuid4())
        with get_db_session() as session:
            if user_id:
                sess_repo = SessionRepository(session)
                record = sess_repo.get_by_id_for_user(session_id, user_id)
                if record is None:
                    raise AppError("会话不存在", code=NOT_FOUND, status_code=404)
            msg_repo = MessageRepository(session)
            msg = msg_repo.create(
                id=message_id,
                session_id=session_id,
                role=role,
                content=content,
                sources=sources,
            )
            if user_id:
                sess_repo.update(record, updated_at=datetime.now(timezone.utc))
            return MessageRepository.to_dict(msg)

    def get_history(
        self,
        session_id: str,
        limit: int = 50,
        user_id: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        """获取会话聊天历史。"""
        with get_db_session() as session:
            if user_id:
                sess_repo = SessionRepository(session)
                record = sess_repo.get_by_id_for_user(session_id, user_id)
                if record is None:
                    raise AppError("会话不存在", code=NOT_FOUND, status_code=404)
            msg_repo = MessageRepository(session)
            records = msg_repo.list_by_session(session_id, limit=limit)
            return [MessageRepository.to_dict(r) for r in records]

    def clear(self, session_id: str, user_id: Optional[str] = None) -> bool:
        """清空会话历史。"""
        with get_db_session() as session:
            if user_id:
                sess_repo = SessionRepository(session)
                record = sess_repo.get_by_id_for_user(session_id, user_id)
                if record is None:
                    raise AppError("会话不存在", code=NOT_FOUND, status_code=404)
            msg_repo = MessageRepository(session)
            msg_repo.delete_by_session(session_id)
            return True

    def get_sources(self, message_id: str) -> list[dict[str, Any]]:
        """获取消息关联的引用文档。"""
        with get_db_session() as session:
            msg_repo = MessageRepository(session)
            record = msg_repo.get_by_id(message_id)
            if record is None:
                raise AppError("消息不存在", code=NOT_FOUND, status_code=404)
            return record.sources or []
