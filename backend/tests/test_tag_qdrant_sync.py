"""标签同步 Qdrant payload 测试."""

import uuid
from unittest.mock import patch

from config.constants import DOC_VISIBILITY_PRIVATE
from storage.mysql_db import get_db_session
from storage.repositories.file_repository import FileRepository
from storage.repositories.file_tag_repository import FileTagRepository
from storage.repositories.tag_repository import TagRepository
from tag.tag_service import TagService
from tests.test_file_delete import sqlite_file_db


def _seed_tagged_file(user_id: str = "user-1") -> tuple[str, list[str]]:
    file_id = str(uuid.uuid4())
    category_id = str(uuid.uuid4())
    tag_ids = [str(uuid.uuid4()), str(uuid.uuid4())]
    with get_db_session() as session:
        FileRepository(session).create(
            id=file_id,
            user_id=user_id,
            filename="sync-doc.txt",
            storage_path=f"/tmp/{file_id}.txt",
            visibility=DOC_VISIBILITY_PRIVATE,
            chunk_count=1,
            status="indexed",
        )
        tag_repo = TagRepository(session)
        tag_repo.create_category(id=category_id, name="分类", sort_order=0)
        for tag_id in tag_ids:
            tag_repo.create_tag(
                id=tag_id,
                category_id=category_id,
                name=f"标签-{tag_id[:4]}",
                keywords="关键词",
            )
        FileTagRepository(session).add_tags(file_id, tag_ids, "manual")
    return file_id, sorted(tag_ids)


def test_sync_tags_to_qdrant_updates_payload(sqlite_file_db):
    file_id, expected_tag_ids = _seed_tagged_file()

    with patch("storage.vector_store.VectorStore.set_payload_by_filter") as mock_set:
        TagService().sync_tags_to_qdrant(file_id)

    mock_set.assert_called_once_with(
        {"file_id": file_id},
        {"tag_ids": expected_tag_ids},
    )


def test_set_manual_file_tags_triggers_qdrant_sync(sqlite_file_db):
    file_id, _ = _seed_tagged_file()
    new_tag_id = str(uuid.uuid4())
    category_id = str(uuid.uuid4())

    with get_db_session() as session:
        tag_repo = TagRepository(session)
        tag_repo.create_category(id=category_id, name="新分类", sort_order=1)
        tag_repo.create_tag(
            id=new_tag_id,
            category_id=category_id,
            name="手动标签",
            keywords="手动",
        )

    user = {"user_id": "user-1", "department_id": None}
    with patch.object(TagService, "sync_tags_to_qdrant") as mock_sync:
        TagService().set_manual_file_tags(user, file_id, [new_tag_id])

    mock_sync.assert_called_once_with(file_id)
