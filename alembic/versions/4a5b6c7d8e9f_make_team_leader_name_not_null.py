"""make team_leader_name NOT NULL

Revision ID: 4a5b6c7d8e9f
Revises: 3d4e5f6a7b8c
Create Date: 2026-06-16 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "4a5b6c7d8e9f"
down_revision: Union[str, None] = "3d4e5f6a7b8c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("UPDATE teams SET team_leader_name = '' WHERE team_leader_name IS NULL")
    op.alter_column('teams', 'team_leader_name', nullable=False)


def downgrade() -> None:
    op.alter_column('teams', 'team_leader_name', nullable=True)
