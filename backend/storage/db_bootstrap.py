"""数据库初始化与默认种子数据."""

import logging
import uuid

from config.constants import ROLE_SUPER_ADMIN
from config.settings import Settings, get_settings
from core.security import hash_password
from storage.mysql_db import create_tables, get_db_session, init_db
from storage.repositories.tenant_repository import TenantRepository
from storage.repositories.user_repository import UserRepository

logger = logging.getLogger(__name__)

DEFAULT_ADMIN_USERNAME = "admin"
DEFAULT_ADMIN_PASSWORD = "admin@123"


def seed_default_data(settings: Settings | None = None) -> None:
    """创建表并写入默认租户与 admin 账号。"""
    cfg = settings or get_settings()
    init_db(cfg)
    create_tables()

    tenant_id = cfg.default_tenant_id
    with get_db_session() as session:
        tenant_repo = TenantRepository(session)
        user_repo = UserRepository(session)

        if tenant_repo.get_by_id(tenant_id) is None:
            tenant_repo.create(id=tenant_id, name="默认租户", status="active")
            logger.info("Seeded default tenant: %s", tenant_id)

        if user_repo.get_by_username(tenant_id, DEFAULT_ADMIN_USERNAME) is None:
            user_repo.create(
                id=str(uuid.uuid4()),
                username=DEFAULT_ADMIN_USERNAME,
                password_hash=hash_password(DEFAULT_ADMIN_PASSWORD),
                tenant_id=tenant_id,
                role=ROLE_SUPER_ADMIN,
                real_name="系统管理员",
                phone="13800000000",
                email="admin@example.com",
                status="active",
            )
            logger.info("Seeded default admin user for tenant: %s", tenant_id)
