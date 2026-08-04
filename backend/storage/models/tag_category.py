"""标签分类表模型."""

from datetime import datetime, timezone

from sqlalchemy import DateTime, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from storage.mysql_db import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class TagCategory(Base):
    """标签字典分类."""

    __tablename__ = "tag_categories"
    __table_args__ = (UniqueConstraint("name", name="uq_tag_categories_name"),)

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
