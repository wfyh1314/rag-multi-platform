"""聊天消息数据访问."""

from datetime import timezone
from typing import Any, Optional

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from storage.models.chat_message import ChatMessage


class MessageRepository:
    """聊天消息 CRUD。"""

    def __init__(self, session: Session):
        self.session = session

    def create(self, **fields: Any) -> ChatMessage:
        record = ChatMessage(**fields)
        self.session.add(record)
        self.session.flush()
        return record

    def get_by_id(self, message_id: str) -> Optional[ChatMessage]:
        return self.session.get(ChatMessage, message_id)

    def list_by_session(self, session_id: str, limit: int = 50) -> list[ChatMessage]:
        stmt = (
            select(ChatMessage)
            .where(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.created_at.asc())
            .limit(limit)
        )
        return list(self.session.scalars(stmt).all())

    def delete_by_session(self, session_id: str) -> int:
        stmt = delete(ChatMessage).where(ChatMessage.session_id == session_id)
        result = self.session.execute(stmt)
        return result.rowcount or 0

    @staticmethod
    def to_dict(record: ChatMessage) -> dict[str, Any]:
        created_at = record.created_at
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)
        return {
            "id": record.id,
            "session_id": record.session_id,
            "role": record.role,
            "content": record.content,
            "sources": record.sources or [],
            "created_at": created_at.isoformat(),
        }
