"""会话创建、命名、归档、删除."""

from typing import Any, Optional


class SessionService:
    """管理聊天会话。"""

    def create(
        self,
        tenant_id: str,
        user_id: str,
        title: Optional[str] = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """创建新聊天会话。"""
        raise NotImplementedError

    def rename(self, session_id: str, title: str, tenant_id: str) -> dict[str, Any]:
        """重命名会话。"""
        raise NotImplementedError

    def archive(self, session_id: str, tenant_id: str) -> dict[str, Any]:
        """归档会话。"""
        raise NotImplementedError

    def delete(self, session_id: str, tenant_id: str) -> bool:
        """删除会话。"""
        raise NotImplementedError

    def list_sessions(self, tenant_id: str, user_id: str) -> list[dict[str, Any]]:
        """获取用户会话列表。"""
        raise NotImplementedError
