"""add name_normalized, drop college_name

Revision ID: 7cc606d61ec5
Revises: 48d44333ee2f
Create Date: 2026-06-11 06:15:27.357009

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '7cc606d61ec5'
down_revision: Union[str, Sequence[str], None] = '48d44333ee2f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('teams', sa.Column('name_normalized', sa.String(255), nullable=True))
    op.execute(
        "UPDATE teams SET name_normalized = LOWER(REGEXP_REPLACE(TRIM(name), '[\\s_\\-]+', '', 'g'))"
    )
    op.alter_column('teams', 'name_normalized', nullable=False)
    op.create_unique_constraint('uq_teams_name_normalized', 'teams', ['name_normalized'])
    op.drop_column('teams', 'college_name')
    op.add_column('teams', sa.Column('is_csv_managed', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('team_members', sa.Column('employee_id', sa.String(length=255), nullable=True))
    op.execute(
        "UPDATE team_members SET employee_id = 'EMP_' || SUBSTRING(id::text, 1, 8)"
    )
    op.alter_column('team_members', 'employee_id', nullable=False)


def downgrade() -> None:
    op.drop_column('team_members', 'employee_id')
    op.drop_column('teams', 'is_csv_managed')
    op.add_column('teams', sa.Column('college_name', sa.String(255), nullable=True))
    op.drop_constraint('uq_teams_name_normalized', 'teams', type_='unique')
    op.drop_column('teams', 'name_normalized')
