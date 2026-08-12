"""Add unique constraint to match_number

Revision ID: cb30b92ad5f2
Revises: 6e40fd0a1a21
Create Date: 2026-06-25 03:37:33.983993

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'cb30b92ad5f2'
down_revision: Union[str, Sequence[str], None] = '6e40fd0a1a21'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_unique_constraint('uq_matches_match_number', 'matches', ['match_number'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint('uq_matches_match_number', 'matches', type_='unique')
