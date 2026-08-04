"""文件数据访问."""

from datetime import timezone
from typing import Any, Optional

from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session

from config.constants import DOC_VISIBILITY_DEPARTMENT, DOC_VISIBILITY_PUBLIC
from storage.models.file import File


class FileRepository:
    """文件 CRUD。"""

    def __init__(self, session: Session):
        self.session = session

    def create(self, **fields: Any) -> File:
        record = File(**fields)
        self.session.add(record)
        self.session.flush()
        return record

    def get_by_id(self, file_id: str) -> Optional[File]:
        return self.session.get(File, file_id)

    def get_by_user_filename(self, user_id: str, filename: str) -> Optional[File]:
        stmt = select(File).where(File.user_id == user_id, File.filename == filename)
        return self.session.scalars(stmt).first()

    def list_accessible(
        self,
        user_id: str,
        keyword: str | None = None,
        folder_id: str | None = None,
        department_id: str | None = None,
    ) -> list[File]:
        access_conditions = [
            File.visibility == DOC_VISIBILITY_PUBLIC,
            File.user_id == user_id,
        ]
        if department_id:
            access_conditions.append(
                and_(
                    File.visibility == DOC_VISIBILITY_DEPARTMENT,
                    File.department_id == department_id,
                )
            )
        stmt = select(File).where(or_(*access_conditions))
        if keyword:
            kw = keyword.strip()
            if kw:
                stmt = stmt.where(File.filename.ilike(f"%{kw}%"))
        if folder_id is not None:
            if folder_id == "":
                stmt = stmt.where(File.folder_id.is_(None))
            else:
                stmt = stmt.where(File.folder_id == folder_id)
        stmt = stmt.order_by(File.uploaded_at.desc())
        return list(self.session.scalars(stmt).all())

    def delete(self, instance: File) -> None:
        self.session.delete(instance)

    @staticmethod
    def to_dict(record: File) -> dict[str, Any]:
        uploaded_at = record.uploaded_at
        if uploaded_at.tzinfo is None:
            uploaded_at = uploaded_at.replace(tzinfo=timezone.utc)
        return {
            "file_id": record.id,
            "filename": record.filename,
            "user_id": record.user_id,
            "owner_id": record.user_id,
            "folder_id": record.folder_id,
            "visibility": record.visibility,
            "department_id": record.department_id,
            "chunk_count": record.chunk_count,
            "status": record.status,
            "message": record.message,
            "uploaded_at": uploaded_at.isoformat(),
        }
