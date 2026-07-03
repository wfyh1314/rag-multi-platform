"""RBAC 角色权限：超级管理员/企业管理员/普通员工."""

from typing import Any

from config.constants import ROLE_EMPLOYEE, ROLE_SUPER_ADMIN, ROLE_TENANT_ADMIN
from core.exceptions import PermissionDeniedError


# 角色 -> 权限映射
ROLE_PERMISSIONS: dict[str, frozenset[str]] = {
    ROLE_SUPER_ADMIN: frozenset({"*"}),
    ROLE_TENANT_ADMIN: frozenset({
        "tenant:manage", "user:manage", "file:manage", "chat:use", "audit:view",
    }),
    ROLE_EMPLOYEE: frozenset({"file:read", "file:upload", "chat:use"}),
}


class RBACService:
    """基于角色的访问控制服务。"""

    def has_permission(self, role: str, permission: str) -> bool:
        """检查角色是否拥有指定权限。"""
        perms = ROLE_PERMISSIONS.get(role, frozenset())
        return "*" in perms or permission in perms

    def require_permission(self, role: str, permission: str) -> None:
        """角色缺少权限时抛出异常。"""
        if not self.has_permission(role, permission):
            raise PermissionDeniedError(f"缺少权限: {permission}")

    def assign_role(self, user_id: str, role: str) -> dict[str, Any]:
        """为用户分配角色。"""
        raise NotImplementedError

    def list_roles(self, tenant_id: str) -> list[dict[str, Any]]:
        """获取租户角色列表。"""
        raise NotImplementedError
