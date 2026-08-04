"""Add department_id to users and files.

Revision ID: 002_department
Revises: 001_baseline
Create Date: 2026-07-10

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "002_department"
down_revision: Union[str, None] = "001_baseline"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = set(inspector.get_table_names())

    if "users" in existing_tables:
        user_cols = {col["name"] for col in inspector.get_columns("users")}
        if "department_id" not in user_cols:
            op.add_column("users", sa.Column("department_id", sa.String(length=64), nullable=True))
            op.create_index("ix_users_department_id", "users", ["department_id"], unique=False)

    if "files" in existing_tables:
        file_cols = {col["name"] for col in inspector.get_columns("files")}
        if "department_id" not in file_cols:
            op.add_column("files", sa.Column("department_id", sa.String(length=64), nullable=True))
            op.create_index("ix_files_department_id", "files", ["department_id"], unique=False)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = set(inspector.get_table_names())

    if "files" in existing_tables:
        file_cols = {col["name"] for col in inspector.get_columns("files")}
        if "department_id" in file_cols:
            op.drop_index("ix_files_department_id", table_name="files")
            op.drop_column("files", "department_id")

    if "users" in existing_tables:
        user_cols = {col["name"] for col in inspector.get_columns("users")}
        if "department_id" in user_cols:
            op.drop_index("ix_users_department_id", table_name="users")
            op.drop_column("users", "department_id")
