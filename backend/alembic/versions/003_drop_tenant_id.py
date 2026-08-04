"""Drop legacy tenant_id from users and files.

Revision ID: 003_drop_tenant_id
Revises: 002_department
Create Date: 2026-07-10

"""

from typing import Sequence, Union

from alembic import op

from storage.legacy_tenant_migration import migrate_legacy_tenant_schema

revision: str = "003_drop_tenant_id"
down_revision: Union[str, None] = "002_department"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    migrate_legacy_tenant_schema(op.get_bind().engine)


def downgrade() -> None:
    # 去租户迁移不可逆；回滚需手工恢复 tenant_id 列与旧索引。
    pass
