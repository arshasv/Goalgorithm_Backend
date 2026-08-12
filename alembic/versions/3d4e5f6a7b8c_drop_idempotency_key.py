"""drop idempotency_key from predictions

Revision ID: 3d4e5f6a7b8c
Revises: 9a9c4b5d6e7f
Create Date: 2026-06-16 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "3d4e5f6a7b8c"
down_revision: Union[str, None] = "9a9c4b5d6e7f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_column("predictions", "idempotency_key")


def downgrade() -> None:
    op.add_column(
        "predictions",
        sa.Column("idempotency_key", sa.String(length=255), nullable=True),
    )
