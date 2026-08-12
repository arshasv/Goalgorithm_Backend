"""Add group_code column to team_members table

Revision ID: b1c2d3e4f5g6
Revises: f4e5d6a7b8c9
Create Date: 2026-06-25 05:35:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b1c2d3e4f5g6"
down_revision: Union[str, None] = "f4e5d6a7b8c9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    from sqlalchemy.engine.reflection import Inspector
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    columns = [c['name'] for c in inspector.get_columns('team_members')]
    if 'group_code' not in columns:
        op.add_column(
            "team_members",
            sa.Column("group_code", sa.String(10), nullable=True),
        )


def downgrade() -> None:
    op.drop_column("team_members", "group_code")
