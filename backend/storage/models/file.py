"""文件表模型."""

from datetime import datetime, timezone

from sqlalchemy import DateTime, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from config.constants import DOC_VISIBILITY_PRIVATE
from storage.mysql_db import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class File(Base):
    """上传文件元数据."""

    __tablename__ = "files"
    __table_args__ = (UniqueConstraint("user_id", "filename", name="uq_files_user_filename"),)

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    filename: Mapped[str] = mapped_column(String(512), nullable=False)
    storage_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    folder_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    visibility: Mapped[str] = mapped_column(String(32), nullable=False, default=DOC_VISIBILITY_PRIVATE)
    department_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    chunk_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="indexed")
    message: Mapped[str | None] = mapped_column(String(512), nullable=True)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
