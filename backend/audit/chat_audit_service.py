"""问答审计日志：用户提问、回答、引用文档."""

from typing import Any, Optional


class ChatAuditService:
    """问答交互审计。"""

    def log_chat(
        self,
        tenant_id: str,
        user_id: str,
        session_id: str,
        query: str,
        answer: str,
        sources: Optional[list[dict[str, Any]]] = None,
    ) -> dict[str, Any]:
        """记录问答审计条目。"""
        raise NotImplementedError

    def query(
        self,
        tenant_id: str,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> dict[str, Any]:
        """查询问答审计日志。"""
        raise NotImplementedError
