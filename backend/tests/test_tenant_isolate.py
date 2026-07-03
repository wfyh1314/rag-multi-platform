"""租户隔离越权测试."""

import pytest

from core.exceptions import PermissionDeniedError
from tenant.doc_permission import DocPermissionService
from tenant.tenant_service import TenantService


def test_tenant_isolation_rejects_cross_tenant_access():
    """跨租户资源访问应抛出 PermissionDeniedError。"""
    service = TenantService()
    with pytest.raises(PermissionDeniedError):
        service.validate_isolation("tenant-a", "tenant-b")


def test_doc_permission_private_document():
    """文档所有者可访问私有文档，其他用户不可。"""
    perm = DocPermissionService()
    owner = {"user_id": "u1", "tenant_id": "t1"}
    other = {"user_id": "u2", "tenant_id": "t1"}
    doc = {"tenant_id": "t1", "owner_id": "u1", "visibility": "private"}

    assert perm.can_access(owner, doc) is True
    assert perm.can_access(other, doc) is False
