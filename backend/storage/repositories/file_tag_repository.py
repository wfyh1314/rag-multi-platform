"""文档标签关联数据访问."""

from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from storage.models.file_tag import TAG_SOURCE_AUTO, TAG_SOURCE_MANUAL, FileTag
from storage.models.tag import Tag
from storage.models.tag_category import TagCategory


class FileTagRepository:
    """文档-标签关联 CRUD。"""

    def __init__(self, session: Session):
        self.session = session

    def list_by_file_id(self, file_id: str) -> list[FileTag]:
        stmt = select(FileTag).where(FileTag.file_id == file_id)
        return list(self.session.scalars(stmt).all())

    def list_tag_details_by_file_id(self, file_id: str) -> list[dict[str, Any]]:
        return self.list_tag_details_by_file_ids([file_id]).get(file_id, [])

    def list_tag_details_by_file_ids(
        self, file_ids: list[str]
    ) -> dict[str, list[dict[str, Any]]]:
        if not file_ids:
            return {}
        stmt = (
            select(FileTag, Tag, TagCategory)
            .join(Tag, FileTag.tag_id == Tag.id)
            .join(TagCategory, Tag.category_id == TagCategory.id)
            .where(FileTag.file_id.in_(file_ids))
            .order_by(FileTag.file_id, TagCategory.sort_order, Tag.name)
        )
        rows = self.session.execute(stmt).all()
        result: dict[str, list[dict[str, Any]]] = {file_id: [] for file_id in file_ids}
        for file_tag, tag, category in rows:
            result.setdefault(file_tag.file_id, []).append(
                {
                    "tag_id": tag.id,
                    "tag_name": tag.name,
                    "category_id": category.id,
                    "category_name": category.name,
                    "keywords": tag.keywords,
                    "source": file_tag.source,
                    "label": f"{category.name}: {tag.name}",
                }
            )
        return result

    def list_file_ids_by_tag_ids(self, tag_ids: list[str]) -> set[str]:
        if not tag_ids:
            return set()
        stmt = select(FileTag.file_id).where(FileTag.tag_id.in_(tag_ids)).distinct()
        return set(self.session.scalars(stmt).all())

    def delete_by_file_id(self, file_id: str) -> None:
        stmt = delete(FileTag).where(FileTag.file_id == file_id)
        self.session.execute(stmt)

    def delete_auto_by_file_id(self, file_id: str) -> None:
        stmt = delete(FileTag).where(
            FileTag.file_id == file_id,
            FileTag.source == TAG_SOURCE_AUTO,
        )
        self.session.execute(stmt)

    def delete_manual_by_file_id(self, file_id: str) -> None:
        stmt = delete(FileTag).where(
            FileTag.file_id == file_id,
            FileTag.source == TAG_SOURCE_MANUAL,
        )
        self.session.execute(stmt)

    def add_tags(self, file_id: str, tag_ids: list[str], source: str) -> None:
        existing = {item.tag_id for item in self.list_by_file_id(file_id)}
        for tag_id in tag_ids:
            if tag_id in existing:
                continue
            self.session.add(FileTag(file_id=file_id, tag_id=tag_id, source=source))
            existing.add(tag_id)
        self.session.flush()

    def replace_manual_tags(self, file_id: str, tag_ids: list[str]) -> None:
        self.delete_manual_by_file_id(file_id)
        self.add_tags(file_id, tag_ids, TAG_SOURCE_MANUAL)

    def get_tag_ids_by_file_id(self, file_id: str) -> set[str]:
        return {item.tag_id for item in self.list_by_file_id(file_id)}
