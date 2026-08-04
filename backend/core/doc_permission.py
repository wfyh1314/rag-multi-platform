"""文档权限校验：私有/公共文档访问拦截."""

from typing import Any

from config.constants import (
    DOC_VISIBILITY_DEPARTMENT,
    DOC_VISIBILITY_PRIVATE,
    DOC_VISIBILITY_PUBLIC,
)
from core.exceptions import PermissionDeniedError


class DocPermissionService:
    """文档级访问控制。"""

    def can_access(self, user: dict[str, Any], document: dict[str, Any]) -> bool:
        """检查用户是否有权访问文档。"""
        visibility = document.get("visibility", DOC_VISIBILITY_PRIVATE)
        user_id = user.get("user_id")
        owner_id = document.get("owner_id") or document.get("user_id")

        if visibility == DOC_VISIBILITY_PUBLIC:
            return True
        if visibility == DOC_VISIBILITY_PRIVATE:
            return owner_id == user_id
        if visibility == DOC_VISIBILITY_DEPARTMENT:
            if owner_id == user_id:
                return True
            user_dept = user.get("department_id")
            doc_dept = document.get("department_id")
            return bool(user_dept and doc_dept and user_dept == doc_dept)
        return False

    def can_delete(self, user: dict[str, Any], document: dict[str, Any]) -> bool:
        """仅上传者可删除。"""
        user_id = user.get("user_id")
        return document.get("owner_id") == user_id or document.get("user_id") == user_id

    def require_access(self, user: dict[str, Any], document: dict[str, Any]) -> None:
        """用户无权访问时抛出异常。"""
        if not self.can_access(user, document):
            raise PermissionDeniedError("无权访问该文档")

    def require_delete(self, user: dict[str, Any], document: dict[str, Any]) -> None:
        """用户无权删除时抛出异常。"""
        if not self.can_delete(user, document):
            raise PermissionDeniedError("无权删除该文档")

    def filter_accessible(
        self,
        user: dict[str, Any],
        documents: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """过滤出用户可访问的文档列表。"""
        return [d for d in documents if self.can_access(user, d)]
