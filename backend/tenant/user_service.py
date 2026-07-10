"""用户管理：注册、登录、密码、个人信息."""

from typing import Any, Optional

from core.exceptions import AuthenticationError
from core.security import verify_password
from storage.models.user import User
from storage.mysql_db import get_db_session
from storage.repositories.user_repository import UserRepository


class UserService:
    """管理租户内用户账户。"""

    @staticmethod
    def _to_profile(user: User) -> dict[str, Any]:
        return {
            "id": user.id,
            "username": user.username,
            "tenant_id": user.tenant_id,
            "role": user.role,
            "real_name": user.real_name,
            "phone": user.phone,
            "email": user.email,
        }

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
        """认证用户并返回用户资料（不含密码）。"""
        with get_db_session() as session:
            repo = UserRepository(session)
            user = repo.get_by_username(tenant_id, username)
            if user is None:
                raise AuthenticationError("用户名或密码错误")
            if user.status != "active":
                raise AuthenticationError("账户已被禁用")
            if not verify_password(password, user.password_hash):
                raise AuthenticationError("用户名或密码错误")
            return self._to_profile(user)

    def get_profile(self, user_id: str) -> Optional[dict[str, Any]]:
        """获取用户资料。"""
        with get_db_session() as session:
            repo = UserRepository(session)
            user = repo.get_by_id(user_id)
            if user is None:
                return None
            return self._to_profile(user)

    def update_profile(self, user_id: str, **kwargs: Any) -> dict[str, Any]:
        """更新用户资料。"""
        raise NotImplementedError

    def change_password(self, user_id: str, old_password: str, new_password: str) -> bool:
        """修改用户密码。"""
        raise NotImplementedError
