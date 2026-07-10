"""用户数据访问."""

from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from storage.models.user import User


class UserRepository:
    """用户 CRUD。"""

    def __init__(self, session: Session):
        self.session = session

    def get_by_username(self, tenant_id: str, username: str) -> Optional[User]:
        stmt = select(User).where(User.tenant_id == tenant_id, User.username == username)
        return self.session.scalars(stmt).first()

    def get_by_id(self, user_id: str) -> Optional[User]:
        return self.session.get(User, user_id)

    def create(self, **fields) -> User:
        user = User(**fields)
        self.session.add(user)
        self.session.flush()
        return user
