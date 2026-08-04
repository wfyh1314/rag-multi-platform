"""旧多租户库结构迁移：移除 tenant_id 并修正唯一约束."""

from __future__ import annotations

import logging

from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine

logger = logging.getLogger(__name__)

_FILES_TENANT_INDEXES = ("uq_files_tenant_filename", "ix_files_tenant_id")
_USERS_TENANT_INDEXES = ("uq_users_tenant_username", "ix_users_tenant_id")
_FILES_USER_UNIQUE = "uq_files_user_filename"
_USERS_USERNAME_UNIQUE = "uq_users_username"


def _table_has_column(inspector, table_name: str, column_name: str) -> bool:
    if table_name not in inspector.get_table_names():
        return False
    return column_name in {col["name"] for col in inspector.get_columns(table_name)}


def _index_names(inspector, table_name: str) -> set[str]:
    names: set[str] = set()
    for idx in inspector.get_indexes(table_name):
        if idx.get("name"):
            names.add(idx["name"])
    for uc in inspector.get_unique_constraints(table_name):
        if uc.get("name"):
            names.add(uc["name"])
    return names


def _drop_index(conn, dialect: str, table_name: str, index_name: str) -> None:
    if dialect == "sqlite":
        conn.execute(text(f"DROP INDEX IF EXISTS {index_name}"))
    else:
        conn.execute(text(f"ALTER TABLE {table_name} DROP INDEX {index_name}"))


def _add_files_user_unique(conn, dialect: str) -> None:
    if dialect == "sqlite":
        conn.execute(
            text(
                f"CREATE UNIQUE INDEX IF NOT EXISTS {_FILES_USER_UNIQUE} "
                "ON files (user_id, filename)"
            )
        )
    else:
        conn.execute(
            text(
                f"ALTER TABLE files ADD CONSTRAINT {_FILES_USER_UNIQUE} "
                "UNIQUE (user_id, filename)"
            )
        )


def _add_users_username_unique(conn, dialect: str) -> None:
    if dialect == "sqlite":
        conn.execute(
            text(
                f"CREATE UNIQUE INDEX IF NOT EXISTS {_USERS_USERNAME_UNIQUE} "
                "ON users (username)"
            )
        )
    else:
        conn.execute(
            text(
                f"ALTER TABLE users ADD CONSTRAINT {_USERS_USERNAME_UNIQUE} "
                "UNIQUE (username)"
            )
        )


def _migrate_files_tenant_schema(conn, inspector, dialect: str) -> None:
    if not _table_has_column(inspector, "files", "tenant_id"):
        return

    dup_rows = conn.execute(
        text(
            "SELECT user_id, filename, COUNT(*) AS cnt FROM files "
            "GROUP BY user_id, filename HAVING COUNT(*) > 1"
        )
    ).fetchall()
    if dup_rows:
        samples = ", ".join(f"{row[0]}/{row[1]}" for row in dup_rows[:5])
        raise RuntimeError(
            "files 表存在重复 (user_id, filename)，无法迁移去租户结构。"
            f" 请先清理重复记录: {samples}"
        )

    indexes = _index_names(inspector, "files")
    for index_name in _FILES_TENANT_INDEXES:
        if index_name in indexes:
            _drop_index(conn, dialect, "files", index_name)
            logger.info("Dropped index files.%s", index_name)

    if dialect == "sqlite":
        conn.execute(text("ALTER TABLE files DROP COLUMN tenant_id"))
    else:
        conn.execute(text("ALTER TABLE files DROP COLUMN tenant_id"))
    logger.info("Dropped column files.tenant_id")

    inspector = inspect(conn)
    if _FILES_USER_UNIQUE not in _index_names(inspector, "files"):
        _add_files_user_unique(conn, dialect)
        logger.info("Added unique constraint %s on files", _FILES_USER_UNIQUE)


def _migrate_users_tenant_schema(conn, inspector, dialect: str) -> None:
    if not _table_has_column(inspector, "users", "tenant_id"):
        return

    dup_rows = conn.execute(
        text(
            "SELECT username, COUNT(*) AS cnt FROM users "
            "GROUP BY username HAVING COUNT(*) > 1"
        )
    ).fetchall()
    if dup_rows:
        samples = ", ".join(row[0] for row in dup_rows[:5])
        raise RuntimeError(
            "users 表存在重复 username，无法迁移去租户结构。"
            f" 请先清理重复记录: {samples}"
        )

    indexes = _index_names(inspector, "users")
    for index_name in _USERS_TENANT_INDEXES:
        if index_name in indexes:
            _drop_index(conn, dialect, "users", index_name)
            logger.info("Dropped index users.%s", index_name)

    if dialect == "sqlite":
        conn.execute(text("ALTER TABLE users DROP COLUMN tenant_id"))
    else:
        conn.execute(text("ALTER TABLE users DROP COLUMN tenant_id"))
    logger.info("Dropped column users.tenant_id")

    inspector = inspect(conn)
    if _USERS_USERNAME_UNIQUE not in _index_names(inspector, "users"):
        _add_users_username_unique(conn, dialect)
        logger.info("Added unique constraint %s on users", _USERS_USERNAME_UNIQUE)


def migrate_legacy_tenant_schema(engine: Engine | None = None) -> None:
    """将旧多租户 files/users 表迁移为去租户结构。"""
    from storage.mysql_db import get_engine

    db_engine = engine or get_engine()
    dialect = db_engine.dialect.name
    inspector = inspect(db_engine)

    has_files_tenant = _table_has_column(inspector, "files", "tenant_id")
    has_users_tenant = _table_has_column(inspector, "users", "tenant_id")
    if not has_files_tenant and not has_users_tenant:
        return

    with db_engine.begin() as conn:
        if has_users_tenant:
            _migrate_users_tenant_schema(conn, inspector, dialect)
            inspector = inspect(conn)
        if has_files_tenant:
            _migrate_files_tenant_schema(conn, inspector, dialect)
