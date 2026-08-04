"""标签 API 集成测试."""

import uuid
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from config.constants import DOC_VISIBILITY_PRIVATE
from config.settings import get_settings
from core.security import get_current_user
from main import app
import storage.mysql_db as mysql_db
from storage.mysql_db import create_tables, get_db_session
from storage.repositories.file_repository import FileRepository
from storage.repositories.file_tag_repository import FileTagRepository
from storage.repositories.tag_repository import TagRepository


@pytest.fixture
def client(monkeypatch):
    get_settings.cache_clear()
    monkeypatch.setenv("AUTH_SKIP", "true")

    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    mysql_db._engine = engine
    mysql_db._SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    create_tables()

    app.dependency_overrides[get_current_user] = lambda: {
        "user_id": "test-user-1",
        "role": "employee",
    }
    yield TestClient(app)
    app.dependency_overrides.clear()


def _seed_file_with_tag(user_id: str = "test-user-1") -> tuple[str, str, str]:
    file_id = str(uuid.uuid4())
    category_id = str(uuid.uuid4())
    tag_id = str(uuid.uuid4())
    with get_db_session() as session:
        file_repo = FileRepository(session)
        file_repo.create(
            id=file_id,
            user_id=user_id,
            filename="tagged-doc.txt",
            storage_path=f"/tmp/{file_id}.txt",
            visibility=DOC_VISIBILITY_PRIVATE,
            chunk_count=1,
            status="indexed",
            uploaded_at=datetime.now(timezone.utc),
        )
        tag_repo = TagRepository(session)
        tag_repo.create_category(id=category_id, name="分类A", sort_order=0)
        tag_repo.create_tag(
            id=tag_id,
            category_id=category_id,
            name="标签1",
            keywords="关键词",
        )
        FileTagRepository(session).add_tags(file_id, [tag_id], "manual")
    return file_id, category_id, tag_id


def test_tag_category_crud(client):
    create_resp = client.post("/api/tag-categories", json={"name": "业务分类"})
    assert create_resp.status_code == 200
    category_id = create_resp.json()["result"]["id"]

    tag_resp = client.post(
        f"/api/tag-categories/{category_id}/tags",
        json={"name": "合同", "keywords": "合同,协议"},
    )
    assert tag_resp.status_code == 200
    tag_id = tag_resp.json()["result"]["id"]

    list_resp = client.get("/api/tag-categories")
    assert list_resp.status_code == 200
    categories = list_resp.json()["result"]["categories"]
    assert any(c["id"] == category_id for c in categories)

    update_resp = client.put(f"/api/tags/{tag_id}", json={"name": "合同类", "keywords": "合同"})
    assert update_resp.status_code == 200
    assert update_resp.json()["result"]["name"] == "合同类"


def test_list_files_with_tags_batch(client):
    file_id, _, tag_id = _seed_file_with_tag()

    resp = client.get("/api/files/with-tags")
    assert resp.status_code == 200
    files = resp.json()["result"]["files"]
    matched = next(item for item in files if item["file_id"] == file_id)
    assert len(matched["tags"]) == 1
    assert matched["tags"][0]["tag_id"] == tag_id


def test_file_tag_repository_batch_lookup():
    get_settings.cache_clear()
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    mysql_db._engine = engine
    mysql_db._SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    create_tables()

    file_a = str(uuid.uuid4())
    file_b = str(uuid.uuid4())
    category_id = str(uuid.uuid4())
    tag_id = str(uuid.uuid4())

    with get_db_session() as session:
        tag_repo = TagRepository(session)
        tag_repo.create_category(id=category_id, name="批量", sort_order=0)
        tag_repo.create_tag(id=tag_id, category_id=category_id, name="T1", keywords="")
        ft_repo = FileTagRepository(session)
        ft_repo.add_tags(file_a, [tag_id], "manual")

        batch = ft_repo.list_tag_details_by_file_ids([file_a, file_b])
        assert len(batch[file_a]) == 1
        assert batch[file_b] == []
        assert ft_repo.list_file_ids_by_tag_ids([tag_id]) == {file_a}

    get_settings.cache_clear()
