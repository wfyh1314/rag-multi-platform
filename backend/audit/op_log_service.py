"""操作审计日志：上传、删除、登录等."""

import uuid
from typing import Any, Optional

from storage.mysql_db import get_db_session
from storage.repositories.audit_repository import AuditRepository


class OpLogService:
    """操作审计服务。"""

    def log(
        self,
        user_id: str,
        action: str,
        resource_type: str,
        resource_id: Optional[str] = None,
        detail: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """写入操作审计日志。"""
        with get_db_session() as session:
            repo = AuditRepository(session)
            record = repo.create_operation_log(
                id=str(uuid.uuid4()),
                user_id=user_id,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                detail=detail,
            )
            return AuditRepository.operation_log_to_dict(record)

    def query(
        self,
        action: Optional[str] = None,
        user_id: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> dict[str, Any]:
        """分页查询操作审计日志。"""
        with get_db_session() as session:
            repo = AuditRepository(session)
            records, total = repo.query_operation_logs(
                action=action,
                user_id=user_id,
                page=page,
                page_size=page_size,
            )
            items = [AuditRepository.operation_log_to_dict(r) for r in records]
            return {
                "total": total,
                "page": page,
                "page_size": page_size,
                "items": items,
            }
