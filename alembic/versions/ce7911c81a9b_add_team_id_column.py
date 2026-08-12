"""add team_id column to teams table

Revision ID: ce7911c81a9b
Revises: bb19542bf4e4
Create Date: 2026-06-12 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'ce7911c81a9b'
down_revision: Union[str, Sequence[str], None] = 'bb19542bf4e4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('teams', sa.Column('team_id', sa.String(1), nullable=True))
    op.execute(
        """
        UPDATE teams 
        SET team_id = CASE 
            WHEN name ILIKE '%Alpha%' THEN 'A'
            WHEN name ILIKE '%Beta%' THEN 'B'
            WHEN name ILIKE '%Gamma%' THEN 'C'
            WHEN name ILIKE '%Delta%' THEN 'D'
            WHEN name ILIKE '%Epsilon%' THEN 'E'
            ELSE SUBSTRING(name, 1, 1) 
        END
        WHERE name IS NOT NULL
        """
    )
    op.alter_column('teams', 'team_id', nullable=False)
    op.create_unique_constraint('uq_teams_team_id', 'teams', ['team_id'])


def downgrade() -> None:
    op.drop_constraint('uq_teams_team_id', 'teams', type_='unique')
    op.drop_column('teams', 'team_id')
