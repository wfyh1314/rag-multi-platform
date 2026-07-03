"""多级树形文件夹 CRUD、归属租户隔离."""

from typing import Any, Optional


class FolderService:
    """管理租户级多级树形文件夹。"""

    def create(
        self,
        tenant_id: str,
        name: str,
        parent_id: Optional[str] = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """创建文件夹。"""
        raise NotImplementedError

    def list_tree(self, tenant_id: str, parent_id: Optional[str] = None) -> list[dict[str, Any]]:
        """获取文件夹树。"""
        raise NotImplementedError

    def rename(self, folder_id: str, name: str, tenant_id: str) -> dict[str, Any]:
        """重命名文件夹。"""
        raise NotImplementedError

    def move(self, folder_id: str, new_parent_id: Optional[str], tenant_id: str) -> dict[str, Any]:
        """将文件夹移动到新父级。"""
        raise NotImplementedError

    def delete(self, folder_id: str, tenant_id: str) -> bool:
        """删除文件夹及其内容。"""
        raise NotImplementedError
