"""用户管理：注册、登录、密码、个人信息."""

import uuid
from typing import Any, Optional

from config.constants import ROLE_EMPLOYEE
from core.exceptions import AuthenticationError, ValidationError
from core.security import hash_password, verify_password
from storage.models.user import User
from storage.mysql_db import get_db_session
from storage.repositories.user_repository import UserRepository


class UserService:
    """管理用户账户。"""

    @staticmethod
    def _to_profile(user: User) -> dict[str, Any]:
        return {
            "id": user.id,
            "username": user.username,
            "role": user.role,
            "real_name": user.real_name,
            "phone": user.phone,
            "email": user.email,
            "department_id": user.department_id,
        }

    def register(self, username: str, password: str, **kwargs: Any) -> dict[str, Any]:
        """注册新用户。"""
        username = username.strip()
        if not username:
            raise ValidationError("用户名不能为空")
        with get_db_session() as session:
            repo = UserRepository(session)
            if repo.get_by_username(username) is not None:
                raise ValidationError("用户名已存在")
            user = repo.create(
                id=str(uuid.uuid4()),
                username=username,
                password_hash=hash_password(password),
                role=kwargs.get("role", ROLE_EMPLOYEE),
                real_name=kwargs.get("real_name"),
                phone=kwargs.get("phone"),
                email=kwargs.get("email"),
                department_id=kwargs.get("department_id"),
            )
            return self._to_profile(user)

    def login(self, username: str, password: str) -> dict[str, Any]:
        """认证用户并返回用户资料（不含密码）。"""
        with get_db_session() as session:
            repo = UserRepository(session)
            user = repo.get_by_username(username)
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
        allowed = {"real_name", "phone", "email", "department_id"}
        updates = {k: v for k, v in kwargs.items() if k in allowed and v is not None}
        with get_db_session() as session:
            repo = UserRepository(session)
            user = repo.get_by_id(user_id)
            if user is None:
                raise ValidationError("用户不存在")
            for key, value in updates.items():
                setattr(user, key, value)
            session.flush()
            return self._to_profile(user)

    def change_password(self, user_id: str, old_password: str, new_password: str) -> bool:
        """修改用户密码。"""
        with get_db_session() as session:
            repo = UserRepository(session)
            user = repo.get_by_id(user_id)
            if user is None:
                raise ValidationError("用户不存在")
            if not verify_password(old_password, user.password_hash):
                raise AuthenticationError("原密码错误")
            user.password_hash = hash_password(new_password)
            session.flush()
            return True
