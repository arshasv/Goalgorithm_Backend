"""add goal_scorers to predictions

Revision ID: bb19542bf4e4
Revises: 7cc606d61ec5
Create Date: 2026-06-12 04:36:03.702104

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'bb19542bf4e4'
down_revision: Union[str, Sequence[str], None] = '7cc606d61ec5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('predictions', sa.Column('goal_scorers', sa.JSON(), nullable=True))
    op.add_column('actual_results', sa.Column('goal_scorers', sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column('predictions', 'goal_scorers')
    op.drop_column('actual_results', 'goal_scorers')
