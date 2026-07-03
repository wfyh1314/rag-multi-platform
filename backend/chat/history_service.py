"""历史对话持久化查询、溯源文档记录."""

from typing import Any, Optional


class HistoryService:
    """管理聊天历史与引用文档。"""

    def save_message(
        self,
        session_id: str,
        role: str,
        content: str,
        sources: Optional[list[dict[str, Any]]] = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """保存聊天消息，可选附带引用文档。"""
        raise NotImplementedError

    def get_history(self, session_id: str, limit: int = 50) -> list[dict[str, Any]]:
        """获取会话聊天历史。"""
        raise NotImplementedError

    def clear(self, session_id: str) -> bool:
        """清空会话历史（占位，默认返回成功）。"""
        return True

    def get_sources(self, message_id: str) -> list[dict[str, Any]]:
        """获取消息关联的引用文档。"""
        raise NotImplementedError
