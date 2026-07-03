"""租户 CRUD、容量限额、数据隔离校验."""

from typing import Any, Optional


class TenantService:
    """管理租户生命周期与配额。"""

    def create(self, name: str, **kwargs: Any) -> dict[str, Any]:
        """创建新租户。"""
        raise NotImplementedError

    def get(self, tenant_id: str) -> Optional[dict[str, Any]]:
        """按 ID 获取租户。"""
        raise NotImplementedError

    def update(self, tenant_id: str, **kwargs: Any) -> dict[str, Any]:
        """更新租户信息。"""
        raise NotImplementedError

    def delete(self, tenant_id: str) -> bool:
        """删除租户。"""
        raise NotImplementedError

    def check_quota(self, tenant_id: str, resource: str) -> bool:
        """检查租户指定资源是否在配额内。"""
        raise NotImplementedError

    def validate_isolation(self, tenant_id: str, resource_tenant_id: str) -> None:
        """校验租户数据隔离，不匹配时抛出异常。"""
        if tenant_id != resource_tenant_id:
            from core.exceptions import PermissionDeniedError
            raise PermissionDeniedError("跨租户访问被拒绝")
