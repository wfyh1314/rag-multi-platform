"""文件夹数据访问."""

from datetime import timezone
from typing import Any, Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from storage.models.file import File
from storage.models.folder import Folder


class FolderRepository:
    """文件夹 CRUD。"""

    def __init__(self, session: Session):
        self.session = session

    def create(self, **fields: Any) -> Folder:
        record = Folder(**fields)
        self.session.add(record)
        self.session.flush()
        return record

    def get_by_id(self, folder_id: str) -> Optional[Folder]:
        return self.session.get(Folder, folder_id)

    def get_by_id_for_user(self, folder_id: str, user_id: str) -> Optional[Folder]:
        stmt = select(Folder).where(Folder.id == folder_id, Folder.user_id == user_id)
        return self.session.scalars(stmt).first()

    def list_by_user(self, user_id: str) -> list[Folder]:
        stmt = select(Folder).where(Folder.user_id == user_id).order_by(Folder.created_at.asc())
        return list(self.session.scalars(stmt).all())

    def list_children(self, user_id: str, parent_id: str | None) -> list[Folder]:
        stmt = select(Folder).where(Folder.user_id == user_id, Folder.parent_id == parent_id)
        return list(self.session.scalars(stmt).all())

    def count_children(self, folder_id: str) -> int:
        stmt = select(func.count()).select_from(Folder).where(Folder.parent_id == folder_id)
        return self.session.scalar(stmt) or 0

    def count_files(self, folder_id: str) -> int:
        stmt = select(func.count()).select_from(File).where(File.folder_id == folder_id)
        return self.session.scalar(stmt) or 0

    def update(self, instance: Folder, **fields: Any) -> Folder:
        for key, value in fields.items():
            setattr(instance, key, value)
        self.session.flush()
        return instance

    def delete(self, instance: Folder) -> None:
        self.session.delete(instance)

    @staticmethod
    def to_dict(record: Folder) -> dict[str, Any]:
        created_at = record.created_at
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)
        return {
            "id": record.id,
            "name": record.name,
            "parent_id": record.parent_id,
            "created_at": created_at.isoformat(),
        }
