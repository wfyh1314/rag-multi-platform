"""Baseline for databases created via create_all().

Revision ID: 001_baseline
Revises:
Create Date: 2026-07-10

"""

from typing import Sequence, Union

# revision identifiers, used by Alembic.
revision: str = "001_baseline"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Existing deployments already have tables from create_all()."""
    pass


def downgrade() -> None:
    pass
