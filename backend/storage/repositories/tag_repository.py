"""标签字典数据访问."""

from datetime import timezone
from typing import Any, Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from storage.models.tag import Tag
from storage.models.tag_category import TagCategory


class TagRepository:
    """标签分类与标签 CRUD。"""

    def __init__(self, session: Session):
        self.session = session

    def list_categories(self) -> list[TagCategory]:
        stmt = select(TagCategory).order_by(TagCategory.sort_order, TagCategory.created_at)
        return list(self.session.scalars(stmt).all())

    def get_category(self, category_id: str) -> Optional[TagCategory]:
        return self.session.get(TagCategory, category_id)

    def create_category(self, **fields: Any) -> TagCategory:
        record = TagCategory(**fields)
        self.session.add(record)
        self.session.flush()
        return record

    def update_category(self, instance: TagCategory, **fields: Any) -> TagCategory:
        for key, value in fields.items():
            setattr(instance, key, value)
        self.session.flush()
        return instance

    def delete_category(self, instance: TagCategory) -> None:
        self.session.delete(instance)

    def list_tags_by_category(self, category_id: str) -> list[Tag]:
        stmt = select(Tag).where(Tag.category_id == category_id).order_by(Tag.created_at)
        return list(self.session.scalars(stmt).all())

    def list_all_tags(self) -> list[Tag]:
        stmt = select(Tag).order_by(Tag.category_id, Tag.created_at)
        return list(self.session.scalars(stmt).all())

    def get_tag(self, tag_id: str) -> Optional[Tag]:
        return self.session.get(Tag, tag_id)

    def create_tag(self, **fields: Any) -> Tag:
        record = Tag(**fields)
        self.session.add(record)
        self.session.flush()
        return record

    def update_tag(self, instance: Tag, **fields: Any) -> Tag:
        for key, value in fields.items():
            setattr(instance, key, value)
        self.session.flush()
        return instance

    def delete_tag(self, instance: Tag) -> None:
        self.session.delete(instance)

    def count_tags_by_category(self, category_id: str) -> int:
        stmt = select(func.count()).select_from(Tag).where(Tag.category_id == category_id)
        return int(self.session.scalar(stmt) or 0)

    @staticmethod
    def category_to_dict(category: TagCategory, tags: list[Tag] | None = None) -> dict[str, Any]:
        created_at = category.created_at
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)
        tag_items = [TagRepository.tag_to_dict(tag) for tag in (tags or [])]
        return {
            "id": category.id,
            "name": category.name,
            "sort_order": category.sort_order,
            "tag_count": len(tag_items),
            "tags": tag_items,
            "created_at": created_at.isoformat(),
        }

    @staticmethod
    def tag_to_dict(tag: Tag, category_name: str | None = None) -> dict[str, Any]:
        created_at = tag.created_at
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)
        data = {
            "id": tag.id,
            "category_id": tag.category_id,
            "name": tag.name,
            "keywords": tag.keywords,
            "created_at": created_at.isoformat(),
        }
        if category_name is not None:
            data["category_name"] = category_name
        return data
