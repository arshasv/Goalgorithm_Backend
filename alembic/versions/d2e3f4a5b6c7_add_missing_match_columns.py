"""Add missing columns to matches table (round, external_api_id, etc.)

Revision ID: d2e3f4a5b6c7
Revises: cb30b92ad5f2
Create Date: 2026-06-25 04:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d2e3f4a5b6c7"
down_revision: Union[str, None] = "cb30b92ad5f2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    from sqlalchemy.engine.reflection import Inspector
    
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    
    def safe_add_column(table, column):
        columns = [c['name'] for c in inspector.get_columns(table)]
        if column.name not in columns:
            op.add_column(table, column)

    safe_add_column("matches", sa.Column("round", sa.String(100), nullable=True))
    safe_add_column("matches", sa.Column("external_api_id", sa.String(255), nullable=True))
    safe_add_column("matches", sa.Column("competition_name", sa.String(255), nullable=True))
    safe_add_column("matches", sa.Column("external_sync_status", sa.String(20), nullable=True))

    safe_add_column("actual_results", sa.Column("result_source", sa.String(50), server_default="MANUAL", nullable=False))
    safe_add_column("actual_results", sa.Column("last_synced_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("matches", "external_sync_status")
    op.drop_column("matches", "competition_name")
    op.drop_column("matches", "external_api_id")
    op.drop_column("matches", "round")

    op.drop_column("actual_results", "last_synced_at")
    op.drop_column("actual_results", "result_source")
