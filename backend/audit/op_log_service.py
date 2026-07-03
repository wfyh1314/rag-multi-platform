"""操作日志：上传/删除/权限变更/文件移动."""

from typing import Any, Optional


class OpLogService:
    """操作审计日志记录。"""

    def log(
        self,
        tenant_id: str,
        user_id: str,
        action: str,
        resource_type: str,
        resource_id: str,
        detail: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """记录一条操作日志。"""
        raise NotImplementedError

    def query(
        self,
        tenant_id: str,
        action: Optional[str] = None,
        user_id: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> dict[str, Any]:
        """按条件查询操作日志。"""
        raise NotImplementedError
