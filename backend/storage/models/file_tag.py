"""文档-标签关联表模型."""

from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from storage.mysql_db import Base

TAG_SOURCE_AUTO = "auto"
TAG_SOURCE_MANUAL = "manual"


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class FileTag(Base):
    """文档与标签的多对多关联."""

    __tablename__ = "file_tags"

    file_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("files.id", ondelete="CASCADE"), primary_key=True
    )
    tag_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True
    )
    source: Mapped[str] = mapped_column(String(16), nullable=False, default=TAG_SOURCE_AUTO)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
