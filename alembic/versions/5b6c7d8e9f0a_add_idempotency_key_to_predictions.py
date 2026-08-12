"""add idempotency_key column back to predictions

Revision ID: 5b6c7d8e9f0a
Revises: 4a5b6c7d8e9f
Create Date: 2026-06-16 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "5b6c7d8e9f0a"
down_revision: Union[str, None] = "4a5b6c7d8e9f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("predictions", sa.Column("idempotency_key", sa.String(255), nullable=True))
    op.create_index("ix_predictions_idempotency_key", "predictions", ["idempotency_key"])


def downgrade() -> None:
    op.drop_index("ix_predictions_idempotency_key", table_name="predictions")
    op.drop_column("predictions", "idempotency_key")
