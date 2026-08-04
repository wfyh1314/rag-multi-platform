"""部门可见性权限测试."""

import pytest

from config.constants import DOC_VISIBILITY_DEPARTMENT, DOC_VISIBILITY_PRIVATE, DOC_VISIBILITY_PUBLIC
from core.doc_permission import DocPermissionService
from core.exceptions import PermissionDeniedError, ValidationError
from file_mgr.file_service import list_files_for_user
from storage.mysql_db import get_db_session
from storage.repositories.file_repository import FileRepository
from storage.repositories.user_repository import UserRepository
from tests.test_file_delete import sqlite_file_db


def test_doc_permission_department_same_dept():
    perm = DocPermissionService()
    owner = {"user_id": "u1", "department_id": "dept-a"}
    colleague = {"user_id": "u2", "department_id": "dept-a"}
    outsider = {"user_id": "u3", "department_id": "dept-b"}
    doc = {
        "user_id": "u1",
        "owner_id": "u1",
        "visibility": DOC_VISIBILITY_DEPARTMENT,
        "department_id": "dept-a",
    }

    assert perm.can_access(owner, doc) is True
    assert perm.can_access(colleague, doc) is True
    assert perm.can_access(outsider, doc) is False


def test_list_files_includes_department_docs(sqlite_file_db):
    with get_db_session() as session:
        user_repo = UserRepository(session)
        user_repo.create(
            id="user-a",
            username="user_a",
            password_hash="hash",
            department_id="dept-a",
        )
        user_repo.create(
            id="user-b",
            username="user_b",
            password_hash="hash",
            department_id="dept-a",
        )
        user_repo.create(
            id="user-c",
            username="user_c",
            password_hash="hash",
            department_id="dept-b",
        )
        file_repo = FileRepository(session)
        file_repo.create(
            id="dept-file",
            user_id="user-a",
            filename="dept.txt",
            storage_path="/tmp/dept.txt",
            visibility=DOC_VISIBILITY_DEPARTMENT,
            department_id="dept-a",
            chunk_count=1,
            status="indexed",
        )
        file_repo.create(
            id="private-file",
            user_id="user-a",
            filename="private.txt",
            storage_path="/tmp/private.txt",
            visibility=DOC_VISIBILITY_PRIVATE,
            chunk_count=1,
            status="indexed",
        )
        file_repo.create(
            id="public-file",
            user_id="user-c",
            filename="public.txt",
            storage_path="/tmp/public.txt",
            visibility=DOC_VISIBILITY_PUBLIC,
            chunk_count=1,
            status="indexed",
        )

    user_b_files = {item["file_id"] for item in list_files_for_user("user-b")["files"]}
    user_c_files = {item["file_id"] for item in list_files_for_user("user-c")["files"]}

    assert user_b_files == {"dept-file", "public-file"}
    assert user_c_files == {"public-file"}


def test_upload_department_without_user_department_raises(sqlite_file_db):
    from io import BytesIO

    from file_mgr.file_service import FileService

    with get_db_session() as session:
        UserRepository(session).create(
            id="user-no-dept",
            username="no_dept",
            password_hash="hash",
        )

    service = FileService()
    with pytest.raises(ValidationError, match="未设置部门"):
        service.upload(
            file=BytesIO(b"hello"),
            filename="test.txt",
            user_id="user-no-dept",
            visibility=DOC_VISIBILITY_DEPARTMENT,
        )


def test_require_access_raises_for_other_department():
    perm = DocPermissionService()
    doc = {
        "user_id": "user-a",
        "owner_id": "user-a",
        "visibility": DOC_VISIBILITY_DEPARTMENT,
        "department_id": "dept-a",
    }
    with pytest.raises(PermissionDeniedError):
        perm.require_access({"user_id": "user-b", "department_id": "dept-b"}, doc)
