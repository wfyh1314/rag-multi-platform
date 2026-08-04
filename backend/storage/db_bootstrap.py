"""数据库初始化与默认种子数据."""

import logging
import uuid

from sqlalchemy import inspect, text

from config.constants import DOC_VISIBILITY_PRIVATE, ROLE_SUPER_ADMIN
from config.settings import Settings, get_settings
from core.security import hash_password
from storage.mysql_db import create_tables, get_db_session, get_engine, init_db
from storage.repositories.user_repository import UserRepository

logger = logging.getLogger(__name__)

DEFAULT_ADMIN_USERNAME = "admin"
DEFAULT_ADMIN_PASSWORD = "admin@123"

_FILES_COLUMN_ALTERATIONS: list[tuple[str, str]] = [
    ("folder_id", "ALTER TABLE files ADD COLUMN folder_id VARCHAR(64) NULL"),
    (
        "visibility",
        f"ALTER TABLE files ADD COLUMN visibility VARCHAR(32) NOT NULL DEFAULT '{DOC_VISIBILITY_PRIVATE}'",
    ),
    ("department_id", "ALTER TABLE files ADD COLUMN department_id VARCHAR(64) NULL"),
    ("chunk_count", "ALTER TABLE files ADD COLUMN chunk_count INT NOT NULL DEFAULT 0"),
    ("status", "ALTER TABLE files ADD COLUMN status VARCHAR(32) NOT NULL DEFAULT 'indexed'"),
    ("message", "ALTER TABLE files ADD COLUMN message VARCHAR(512) NULL"),
]

_USERS_COLUMN_ALTERATIONS: list[tuple[str, str]] = [
    ("department_id", "ALTER TABLE users ADD COLUMN department_id VARCHAR(64) NULL"),
]


def ensure_schema() -> None:
    """补齐旧库缺失字段（create_all 不会 ALTER 已有表）。"""
    engine = get_engine()
    inspector = inspect(engine)
    table_alterations = [
        ("files", _FILES_COLUMN_ALTERATIONS),
        ("users", _USERS_COLUMN_ALTERATIONS),
    ]

    pending: list[tuple[str, str, str]] = []
    for table_name, alterations in table_alterations:
        if table_name not in inspector.get_table_names():
            continue
        existing = {column["name"] for column in inspector.get_columns(table_name)}
        for name, sql in alterations:
            if name not in existing:
                pending.append((table_name, name, sql))

    if not pending:
        return

    with engine.begin() as conn:
        for table_name, name, sql in pending:
            conn.execute(text(sql))
            logger.info("Added missing column %s.%s", table_name, name)


def seed_default_data(settings: Settings | None = None) -> None:
    """创建表并写入默认 admin 账号。"""
    cfg = settings or get_settings()
    init_db(cfg)
    create_tables()
    ensure_schema()

    with get_db_session() as session:
        user_repo = UserRepository(session)

        if user_repo.get_by_username(DEFAULT_ADMIN_USERNAME) is None:
            user_repo.create(
                id=str(uuid.uuid4()),
                username=DEFAULT_ADMIN_USERNAME,
                password_hash=hash_password(DEFAULT_ADMIN_PASSWORD),
                role=ROLE_SUPER_ADMIN,
                real_name="管理员",
                department_id="default",
            )
            logger.info("Seeded default admin user: %s", DEFAULT_ADMIN_USERNAME)
