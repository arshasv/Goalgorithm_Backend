"""Add external API fields to matches table

Revision ID: 6a7b8c9d0e1f
Revises: 5b6c7d8e9f0a
Create Date: 2026-06-18 12:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "6a7b8c9d0e1f"
down_revision: Union[str, None] = "5b6c7d8e9f0a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "matches",
        sa.Column("external_api_id", sa.String(255), nullable=True),
    )
    op.add_column(
        "matches",
        sa.Column("competition_name", sa.String(255), nullable=True),
    )
    op.add_column(
        "matches",
        sa.Column("external_sync_status", sa.String(20), nullable=True),
    )
    op.create_index(
        "ix_matches_external_api_id",
        "matches",
        ["external_api_id"],
        unique=True,
        postgresql_where=sa.text("external_api_id IS NOT NULL"),
        sqlite_where=sa.text("external_api_id IS NOT NULL"),
    )


def downgrade() -> None:
    op.drop_index("ix_matches_external_api_id")
    op.drop_column("matches", "external_sync_status")
    op.drop_column("matches", "competition_name")
    op.drop_column("matches", "external_api_id")
