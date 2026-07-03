"""用户管理：注册、登录、密码、个人信息."""

from typing import Any, Optional


class UserService:
    """管理租户内用户账户。"""

    def register(
        self,
        username: str,
        password: str,
        tenant_id: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """注册新用户。"""
        raise NotImplementedError

    def login(self, username: str, password: str, tenant_id: str) -> dict[str, Any]:
        """认证用户并返回令牌。"""
        raise NotImplementedError

    def get_profile(self, user_id: str) -> Optional[dict[str, Any]]:
        """获取用户资料。"""
        raise NotImplementedError

    def update_profile(self, user_id: str, **kwargs: Any) -> dict[str, Any]:
        """更新用户资料。"""
        raise NotImplementedError

    def change_password(self, user_id: str, old_password: str, new_password: str) -> bool:
        """修改用户密码。"""
        raise NotImplementedError
