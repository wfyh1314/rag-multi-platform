"""文件可见性权限测试."""

import pytest

from config.constants import DOC_VISIBILITY_PRIVATE, DOC_VISIBILITY_PUBLIC
from core.doc_permission import DocPermissionService
from core.exceptions import PermissionDeniedError
from file_mgr.file_service import list_files_for_user, list_collections_for_user
from storage.mysql_db import create_tables, get_db_session
from storage.repositories.file_repository import FileRepository
from tests.test_file_delete import sqlite_file_db


def test_doc_permission_private_document():
    perm = DocPermissionService()
    owner = {"user_id": "u1"}
    other = {"user_id": "u2"}
    doc = {"user_id": "u1", "owner_id": "u1", "visibility": DOC_VISIBILITY_PRIVATE}

    assert perm.can_access(owner, doc) is True
    assert perm.can_access(other, doc) is False


def test_doc_permission_public_document():
    perm = DocPermissionService()
    owner = {"user_id": "u1"}
    other = {"user_id": "u2"}
    doc = {"user_id": "u1", "owner_id": "u1", "visibility": DOC_VISIBILITY_PUBLIC}

    assert perm.can_access(owner, doc) is True
    assert perm.can_access(other, doc) is True


def test_doc_permission_delete_only_owner():
    perm = DocPermissionService()
    owner = {"user_id": "u1"}
    other = {"user_id": "u2"}
    doc = {"user_id": "u1", "owner_id": "u1", "visibility": DOC_VISIBILITY_PUBLIC}

    assert perm.can_delete(owner, doc) is True
    assert perm.can_delete(other, doc) is False


def test_list_files_respects_visibility(sqlite_file_db):
    with get_db_session() as session:
        repo = FileRepository(session)
        repo.create(
            id="private-file",
            user_id="user-a",
            filename="a.txt",
            storage_path="/tmp/a.txt",
            visibility=DOC_VISIBILITY_PRIVATE,
            chunk_count=1,
            status="indexed",
        )
        repo.create(
            id="public-file",
            user_id="user-b",
            filename="b.txt",
            storage_path="/tmp/b.txt",
            visibility=DOC_VISIBILITY_PUBLIC,
            chunk_count=1,
            status="indexed",
        )

    user_a_files = list_files_for_user("user-a")["files"]
    user_b_files = list_files_for_user("user-b")["files"]

    assert {item["file_id"] for item in user_a_files} == {"private-file", "public-file"}
    assert {item["file_id"] for item in user_b_files} == {"public-file"}


def test_list_collections_returns_objects(sqlite_file_db):
    with get_db_session() as session:
        repo = FileRepository(session)
        repo.create(
            id="file-1",
            user_id="user-a",
            filename="notes.txt",
            storage_path="/tmp/notes.txt",
            visibility=DOC_VISIBILITY_PRIVATE,
            chunk_count=1,
            status="indexed",
        )

    data = list_collections_for_user("user-a")
    assert data["collections"] == [
        {
            "file_id": "file-1",
            "filename": "notes.txt",
            "visibility": DOC_VISIBILITY_PRIVATE,
        }
    ]


def test_require_access_raises_for_private(sqlite_file_db):
    perm = DocPermissionService()
    doc = {"user_id": "user-a", "owner_id": "user-a", "visibility": DOC_VISIBILITY_PRIVATE}
    with pytest.raises(PermissionDeniedError):
        perm.require_access({"user_id": "user-b"}, doc)
