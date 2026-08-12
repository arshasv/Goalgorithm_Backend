"""fix_scoring_config_probability_columns

Revision ID: b2c3d4e5f6g7
Revises: a1b2c3d4e5f6
Create Date: 2026-06-23 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b2c3d4e5f6g7'
down_revision: Union[str, Sequence[str], None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add missing probability fields
    op.add_column('scoring_configs', sa.Column('probability_high_threshold', sa.Float(), server_default='15.0', nullable=False))
    op.add_column('scoring_configs', sa.Column('probability_high_points', sa.Integer(), server_default='5', nullable=False))
    op.add_column('scoring_configs', sa.Column('probability_medium_threshold', sa.Float(), server_default='30.0', nullable=False))
    op.add_column('scoring_configs', sa.Column('probability_medium_points', sa.Integer(), server_default='2', nullable=False))


def downgrade() -> None:
    op.drop_column('scoring_configs', 'probability_high_threshold')
    op.drop_column('scoring_configs', 'probability_high_points')
    op.drop_column('scoring_configs', 'probability_medium_threshold')
    op.drop_column('scoring_configs', 'probability_medium_points')
