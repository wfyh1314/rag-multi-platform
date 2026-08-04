"""数据库异常映射与全局 handler 测试."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError, OperationalError, SQLAlchemyError

from config.response_codes import BAD_REQUEST, DATABASE_ERROR
from core.db_errors import map_db_exception
from main import sqlalchemy_error_handler


def _mysql_operational_error(errno: int, message: str) -> OperationalError:
    return OperationalError("SELECT 1", {}, Exception(errno, message))


def test_map_schema_mismatch_error():
    exc = _mysql_operational_error(1364, "Field 'tenant_id' doesn't have a default value")
    status, code, message = map_db_exception(exc)
    assert status == 503
    assert code == DATABASE_ERROR
    assert "迁移" in message


def test_map_connection_error():
    exc = _mysql_operational_error(2003, "Can't connect to MySQL server")
    status, code, message = map_db_exception(exc)
    assert status == 503
    assert code == DATABASE_ERROR
    assert "连接失败" in message


def test_map_duplicate_integrity_error():
    exc = IntegrityError("INSERT", {}, Exception(1062, "Duplicate entry 'x' for key 'uq_users_username'"))
    status, code, message = map_db_exception(exc)
    assert status == 409
    assert code == BAD_REQUEST
    assert "已存在" in message


@pytest.mark.asyncio
async def test_sqlalchemy_handler_returns_business_code():
    from unittest.mock import MagicMock

    request = MagicMock()
    request.method = "POST"
    request.url.path = "/api/upload"
    request.state.uuid = "test-uuid"
    exc = _mysql_operational_error(1364, "Field 'tenant_id' doesn't have a default value")

    response = await sqlalchemy_error_handler(request, exc)
    assert response.status_code == 503
    body = response.body.decode()
    assert str(DATABASE_ERROR) in body
    assert "迁移" in body


def test_api_returns_db_business_code_on_sqlalchemy_error():
    probe_app = FastAPI()

    @probe_app.get("/probe-db-error")
    def probe_db_error():
        raise _mysql_operational_error(1054, "Unknown column 'tenant_id' in 'field list'")

    probe_app.add_exception_handler(SQLAlchemyError, sqlalchemy_error_handler)

    client = TestClient(probe_app, raise_server_exceptions=False)
    response = client.get("/probe-db-error")
    assert response.status_code == 503
    data = response.json()
    assert data["code"] == DATABASE_ERROR
    assert "迁移" in data["message"]
