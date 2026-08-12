"""Add is_active column to users table

Revision ID: f4e5d6a7b8c9
Revises: d2e3f4a5b6c7
Create Date: 2026-06-25 04:35:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f4e5d6a7b8c9"
down_revision: Union[str, None] = "d2e3f4a5b6c7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    from sqlalchemy.engine.reflection import Inspector
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    columns = [c['name'] for c in inspector.get_columns('users')]
    if 'is_active' not in columns:
        op.add_column(
            "users",
            sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        )


def downgrade() -> None:
    op.drop_column("users", "is_active")
