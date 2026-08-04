"""审计日志数据访问."""

from datetime import timezone
from typing import Any, Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from storage.models.chat_audit_log import ChatAuditLog
from storage.models.operation_log import OperationLog


class AuditRepository:
    """操作与问答审计 CRUD。"""

    def __init__(self, session: Session):
        self.session = session

    def create_operation_log(self, **fields: Any) -> OperationLog:
        record = OperationLog(**fields)
        self.session.add(record)
        self.session.flush()
        return record

    def create_chat_audit_log(self, **fields: Any) -> ChatAuditLog:
        record = ChatAuditLog(**fields)
        self.session.add(record)
        self.session.flush()
        return record

    def query_operation_logs(
        self,
        action: str | None = None,
        user_id: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[OperationLog], int]:
        stmt = select(OperationLog)
        count_stmt = select(func.count()).select_from(OperationLog)
        if action:
            stmt = stmt.where(OperationLog.action == action)
            count_stmt = count_stmt.where(OperationLog.action == action)
        if user_id:
            stmt = stmt.where(OperationLog.user_id == user_id)
            count_stmt = count_stmt.where(OperationLog.user_id == user_id)
        total = self.session.scalar(count_stmt) or 0
        offset = (page - 1) * page_size
        stmt = stmt.order_by(OperationLog.created_at.desc()).offset(offset).limit(page_size)
        return list(self.session.scalars(stmt).all()), total

    def query_chat_audit_logs(
        self,
        user_id: str | None = None,
        session_id: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[ChatAuditLog], int]:
        stmt = select(ChatAuditLog)
        count_stmt = select(func.count()).select_from(ChatAuditLog)
        if user_id:
            stmt = stmt.where(ChatAuditLog.user_id == user_id)
            count_stmt = count_stmt.where(ChatAuditLog.user_id == user_id)
        if session_id:
            stmt = stmt.where(ChatAuditLog.session_id == session_id)
            count_stmt = count_stmt.where(ChatAuditLog.session_id == session_id)
        total = self.session.scalar(count_stmt) or 0
        offset = (page - 1) * page_size
        stmt = stmt.order_by(ChatAuditLog.created_at.desc()).offset(offset).limit(page_size)
        return list(self.session.scalars(stmt).all()), total

    @staticmethod
    def operation_log_to_dict(record: OperationLog) -> dict[str, Any]:
        created_at = record.created_at
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)
        return {
            "id": record.id,
            "user_id": record.user_id,
            "action": record.action,
            "resource_type": record.resource_type,
            "resource_id": record.resource_id,
            "detail": record.detail,
            "created_at": created_at.isoformat(),
        }

    @staticmethod
    def chat_audit_log_to_dict(record: ChatAuditLog) -> dict[str, Any]:
        created_at = record.created_at
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)
        return {
            "id": record.id,
            "user_id": record.user_id,
            "session_id": record.session_id,
            "query": record.query,
            "answer": record.answer,
            "sources": record.sources or [],
            "created_at": created_at.isoformat(),
        }
