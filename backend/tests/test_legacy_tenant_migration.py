"""旧多租户 schema 自动迁移测试."""

from io import BytesIO
from unittest.mock import MagicMock

import pytest
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from config.constants import DOC_VISIBILITY_PRIVATE, ROLE_SUPER_ADMIN
from config.settings import get_settings
from file_mgr.file_service import FileService, list_files_for_user
from storage.legacy_tenant_migration import migrate_legacy_tenant_schema
from storage.mysql_db import get_db_session
from storage.repositories.file_repository import FileRepository
from storage.repositories.user_repository import UserRepository
import storage.mysql_db as mysql_db


def _create_legacy_tables(engine) -> None:
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                CREATE TABLE users (
                    id VARCHAR(64) PRIMARY KEY,
                    tenant_id VARCHAR(64) NOT NULL,
                    username VARCHAR(64) NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    role VARCHAR(32) NOT NULL DEFAULT 'employee',
                    real_name VARCHAR(64),
                    phone VARCHAR(32),
                    email VARCHAR(128),
                    department_id VARCHAR(64),
                    status VARCHAR(32) NOT NULL DEFAULT 'active',
                    created_at DATETIME,
                    updated_at DATETIME
                )
                """
            )
        )
        conn.execute(
            text(
                "CREATE UNIQUE INDEX uq_users_tenant_username ON users (tenant_id, username)"
            )
        )
        conn.execute(text("CREATE INDEX ix_users_tenant_id ON users (tenant_id)"))

        conn.execute(
            text(
                """
                CREATE TABLE files (
                    id VARCHAR(64) PRIMARY KEY,
                    tenant_id VARCHAR(64) NOT NULL,
                    user_id VARCHAR(64) NOT NULL,
                    filename VARCHAR(512) NOT NULL,
                    storage_path VARCHAR(1024) NOT NULL,
                    folder_id VARCHAR(64),
                    visibility VARCHAR(32) NOT NULL DEFAULT 'private',
                    department_id VARCHAR(64),
                    chunk_count INTEGER NOT NULL DEFAULT 0,
                    status VARCHAR(32) NOT NULL DEFAULT 'indexed',
                    message VARCHAR(512),
                    uploaded_at DATETIME
                )
                """
            )
        )
        conn.execute(
            text(
                "CREATE UNIQUE INDEX uq_files_tenant_filename ON files (tenant_id, filename)"
            )
        )
        conn.execute(text("CREATE INDEX ix_files_tenant_id ON files (tenant_id)"))


@pytest.fixture
def legacy_sqlite_db(monkeypatch):
    get_settings.cache_clear()
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    mysql_db._engine = engine
    mysql_db._SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    _create_legacy_tables(engine)
    yield engine
    get_settings.cache_clear()


def test_migrate_legacy_tenant_schema_drops_tenant_id(legacy_sqlite_db):
    migrate_legacy_tenant_schema(legacy_sqlite_db)

    inspector = inspect(legacy_sqlite_db)
    user_cols = {col["name"] for col in inspector.get_columns("users")}
    file_cols = {col["name"] for col in inspector.get_columns("files")}

    assert "tenant_id" not in user_cols
    assert "tenant_id" not in file_cols
    assert "uq_users_username" in {idx["name"] for idx in inspector.get_indexes("users")}
    assert "uq_files_user_filename" in {idx["name"] for idx in inspector.get_indexes("files")}

    with get_db_session() as session:
        user_repo = UserRepository(session)
        user = user_repo.create(
            id="user-1",
            username="alice",
            password_hash="hash",
            role=ROLE_SUPER_ADMIN,
        )
        file_repo = FileRepository(session)
        file_repo.create(
            id="file-1",
            user_id=user.id,
            filename="notes.txt",
            storage_path="/tmp/user-1/file-1/notes.txt",
            visibility=DOC_VISIBILITY_PRIVATE,
        )


def test_migrate_rejects_duplicate_usernames(legacy_sqlite_db):
    with legacy_sqlite_db.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO users (id, tenant_id, username, password_hash) "
                "VALUES ('u1', 't1', 'dup', 'h1'), ('u2', 't2', 'dup', 'h2')"
            )
        )

    with pytest.raises(RuntimeError, match="重复 username"):
        migrate_legacy_tenant_schema(legacy_sqlite_db)


def test_upload_after_legacy_migration(legacy_sqlite_db):
    migrate_legacy_tenant_schema(legacy_sqlite_db)

    with get_db_session() as session:
        UserRepository(session).create(
            id="user-1",
            username="uploader",
            password_hash="hash",
            role=ROLE_SUPER_ADMIN,
        )

    storage = MagicMock()
    storage.save.return_value = "/tmp/uploads/user-1/notes.txt"
    processor = MagicMock()
    processor.process.return_value = {
        "chunk_count": 3,
        "status": "indexed",
        "message": "ok",
    }
    vector_cls = MagicMock()

    service = FileService(storage=storage, processor=processor, vector_store_cls=vector_cls)
    result = service.upload(
        file=BytesIO(b"hello"),
        filename="notes.txt",
        user_id="user-1",
        visibility=DOC_VISIBILITY_PRIVATE,
    )

    assert result["filename"] == "notes.txt"
    assert list_files_for_user("user-1")["total"] == 1
