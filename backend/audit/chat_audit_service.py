"""问答审计日志：用户提问、回答、引用文档."""

import uuid
from typing import Any, Optional

from storage.mysql_db import get_db_session
from storage.repositories.audit_repository import AuditRepository


class ChatAuditService:
    """问答交互审计。"""

    def log_chat(
        self,
        user_id: str,
        session_id: str,
        query: str,
        answer: str,
        sources: Optional[list[dict[str, Any]]] = None,
    ) -> dict[str, Any]:
        """记录问答审计条目。"""
        with get_db_session() as session:
            repo = AuditRepository(session)
            record = repo.create_chat_audit_log(
                id=str(uuid.uuid4()),
                user_id=user_id,
                session_id=session_id,
                query=query,
                answer=answer,
                sources=sources,
            )
            return AuditRepository.chat_audit_log_to_dict(record)

    def query(
        self,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> dict[str, Any]:
        """查询问答审计日志。"""
        with get_db_session() as session:
            repo = AuditRepository(session)
            records, total = repo.query_chat_audit_logs(
                user_id=user_id,
                session_id=session_id,
                page=page,
                page_size=page_size,
            )
            items = [AuditRepository.chat_audit_log_to_dict(r) for r in records]
            return {
                "total": total,
                "page": page,
                "page_size": page_size,
                "items": items,
            }
