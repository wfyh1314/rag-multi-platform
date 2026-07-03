"""文档权限校验：私有/部门/公开文档访问拦截."""

from typing import Any, Optional

from config.constants import DOC_VISIBILITY_DEPARTMENT, DOC_VISIBILITY_PRIVATE, DOC_VISIBILITY_PUBLIC
from core.exceptions import PermissionDeniedError


class DocPermissionService:
    """文档级访问控制。"""

    def can_access(
        self,
        user: dict[str, Any],
        document: dict[str, Any],
    ) -> bool:
        """检查用户是否有权访问文档。"""
        visibility = document.get("visibility", DOC_VISIBILITY_PRIVATE)
        user_id = user.get("user_id")
        tenant_id = user.get("tenant_id")

        if document.get("tenant_id") != tenant_id:
            return False
        if visibility == DOC_VISIBILITY_PUBLIC:
            return True
        if visibility == DOC_VISIBILITY_PRIVATE:
            return document.get("owner_id") == user_id
        if visibility == DOC_VISIBILITY_DEPARTMENT:
            return document.get("department_id") == user.get("department_id")
        return False

    def require_access(self, user: dict[str, Any], document: dict[str, Any]) -> None:
        """用户无权访问时抛出异常。"""
        if not self.can_access(user, document):
            raise PermissionDeniedError("无权访问该文档")

    def filter_accessible(
        self,
        user: dict[str, Any],
        documents: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """过滤出用户可访问的文档列表。"""
        return [d for d in documents if self.can_access(user, d)]
