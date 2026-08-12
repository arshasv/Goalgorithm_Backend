"""add first_team_to_score column to actual_results

Revision ID: e7f8a9b0c1d2
Revises: 6e40fd0a1a21
Create Date: 2026-06-25 05:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "e7f8a9b0c1d2"
down_revision: Union[str, None] = "6e40fd0a1a21"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "actual_results",
        sa.Column("first_team_to_score", sa.String(50), server_default="none", nullable=False),
    )


def downgrade() -> None:
    op.drop_column("actual_results", "first_team_to_score")
