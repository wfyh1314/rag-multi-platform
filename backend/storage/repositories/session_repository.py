"""会话数据访问."""

from datetime import timezone
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from storage.models.chat_session import ChatSession


class SessionRepository:
    """聊天会话 CRUD。"""

    def __init__(self, session: Session):
        self.session = session

    def create(self, **fields: Any) -> ChatSession:
        record = ChatSession(**fields)
        self.session.add(record)
        self.session.flush()
        return record

    def get_by_id(self, session_id: str) -> Optional[ChatSession]:
        return self.session.get(ChatSession, session_id)

    def get_by_id_for_user(self, session_id: str, user_id: str) -> Optional[ChatSession]:
        stmt = select(ChatSession).where(
            ChatSession.id == session_id,
            ChatSession.user_id == user_id,
        )
        return self.session.scalars(stmt).first()

    def list_by_user(self, user_id: str, include_archived: bool = False) -> list[ChatSession]:
        stmt = select(ChatSession).where(ChatSession.user_id == user_id)
        if not include_archived:
            stmt = stmt.where(ChatSession.is_archived.is_(False))
        stmt = stmt.order_by(ChatSession.updated_at.desc())
        return list(self.session.scalars(stmt).all())

    def update(self, instance: ChatSession, **fields: Any) -> ChatSession:
        for key, value in fields.items():
            setattr(instance, key, value)
        self.session.flush()
        return instance

    def delete(self, instance: ChatSession) -> None:
        self.session.delete(instance)

    @staticmethod
    def to_dict(record: ChatSession) -> dict[str, Any]:
        created_at = record.created_at
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)
        updated_at = record.updated_at
        if updated_at.tzinfo is None:
            updated_at = updated_at.replace(tzinfo=timezone.utc)
        return {
            "id": record.id,
            "title": record.title,
            "is_archived": record.is_archived,
            "created_at": created_at.isoformat(),
            "updated_at": updated_at.isoformat(),
        }
