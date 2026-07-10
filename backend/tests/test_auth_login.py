"""登录与用户信息测试."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from config.constants import ROLE_SUPER_ADMIN
from config.settings import get_settings
from core.exceptions import AuthenticationError
from core.security import hash_password
from main import app
import storage.mysql_db as mysql_db
from storage.mysql_db import create_tables, get_db_session
from storage.repositories.tenant_repository import TenantRepository
from storage.repositories.user_repository import UserRepository
from tenant.user_service import UserService


@pytest.fixture
def sqlite_auth_db(monkeypatch):
    """使用 SQLite 内存库并关闭 AUTH_SKIP。"""
    get_settings.cache_clear()
    monkeypatch.setenv("AUTH_SKIP", "false")
    monkeypatch.setenv("JWT_SECRET_KEY", "test-secret-key-for-auth")
    monkeypatch.setenv("DEFAULT_TENANT_ID", "default")

    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    mysql_db._engine = engine
    mysql_db._SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    create_tables()

    with get_db_session() as session:
        tenant_repo = TenantRepository(session)
        user_repo = UserRepository(session)
        tenant_repo.create(id="default", name="默认租户", status="active")
        user_repo.create(
            id="user-admin-001",
            username="admin",
            password_hash=hash_password("admin@123"),
            tenant_id="default",
            role=ROLE_SUPER_ADMIN,
            real_name="系统管理员",
            phone="13800000000",
            email="admin@example.com",
            status="active",
        )

    yield
    mysql_db._engine = None
    mysql_db._SessionLocal = None
    get_settings.cache_clear()


def test_login_success(sqlite_auth_db):
    service = UserService()
    profile = service.login("admin", "admin@123", "default")
    assert profile["username"] == "admin"
    assert profile["real_name"] == "系统管理员"
    assert profile["phone"] == "13800000000"
    assert profile["email"] == "admin@example.com"
    assert profile["role"] == ROLE_SUPER_ADMIN


def test_login_wrong_password(sqlite_auth_db):
    service = UserService()
    with pytest.raises(AuthenticationError):
        service.login("admin", "wrong-password", "default")


def test_login_unknown_user(sqlite_auth_db):
    service = UserService()
    with pytest.raises(AuthenticationError):
        service.login("nobody", "admin@123", "default")


def test_login_wrong_tenant(sqlite_auth_db):
    service = UserService()
    with pytest.raises(AuthenticationError):
        service.login("admin", "admin@123", "other-tenant")


def test_login_api_returns_token_and_user(sqlite_auth_db):
    client = TestClient(app)
    response = client.post(
        "/api/auth/login",
        json={"username": "admin", "password": "admin@123", "tenant_id": "default"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 10000
    assert data["uuid"]
    result = data["result"]
    assert result["token_type"] == "bearer"
    assert result["access_token"]
    assert result["user"]["username"] == "admin"
    assert result["user"]["real_name"] == "系统管理员"


def test_users_me_with_token(sqlite_auth_db):
    client = TestClient(app)
    login_resp = client.post(
        "/api/auth/login",
        json={"username": "admin", "password": "admin@123", "tenant_id": "default"},
    )
    token = login_resp.json()["result"]["access_token"]

    me_resp = client.get("/api/users/me", headers={"Authorization": f"Bearer {token}"})
    assert me_resp.status_code == 200
    data = me_resp.json()
    assert data["code"] == 10000
    user = data["result"]
    assert user["username"] == "admin"
    assert user["email"] == "admin@example.com"


def test_users_me_without_token_returns_401(sqlite_auth_db):
    client = TestClient(app)
    response = client.get("/api/users/me")
    assert response.status_code == 401
    data = response.json()
    assert data["code"] == 10401
    assert data["uuid"]
