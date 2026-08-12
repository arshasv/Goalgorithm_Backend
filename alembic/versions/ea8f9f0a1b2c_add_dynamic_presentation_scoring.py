"""add dynamic presentation scoring

Revision ID: ea8f9f0a1b2c
Revises: fd7f730d5d46
Create Date: 2026-06-19 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'ea8f9f0a1b2c'
down_revision: Union[str, Sequence[str], None] = 'fd7f730d5d46'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Update scoring_configs table
    op.add_column('scoring_configs', sa.Column('presentation_criteria', sa.JSON(), nullable=True))
    op.add_column('scoring_configs', sa.Column('presentation_judge_count', sa.Integer(), nullable=False, server_default='2'))

    # 2. Update presentation_evaluations table
    op.add_column('presentation_evaluations', sa.Column('judge_count', sa.Integer(), nullable=True))
    op.add_column('presentation_evaluations', sa.Column('judge_scores', sa.JSON(), nullable=True))
    op.add_column('presentation_evaluations', sa.Column('presentation_criteria_config', sa.JSON(), nullable=True))
    op.add_column('presentation_evaluations', sa.Column('max_marks', sa.Integer(), nullable=True))
    
    # Alter raw_total type to Float/Float(53)
    op.alter_column('presentation_evaluations', 'raw_total',
                    existing_type=sa.Integer(),
                    type_=sa.Float(),
                    existing_nullable=True)


def downgrade() -> None:
    op.alter_column('presentation_evaluations', 'raw_total',
                    existing_type=sa.Float(),
                    type_=sa.Integer(),
                    existing_nullable=True)
    op.drop_column('presentation_evaluations', 'max_marks')
    op.drop_column('presentation_evaluations', 'presentation_criteria_config')
    op.drop_column('presentation_evaluations', 'judge_scores')
    op.drop_column('presentation_evaluations', 'judge_count')
    op.drop_column('scoring_configs', 'presentation_judge_count')
    op.drop_column('scoring_configs', 'presentation_criteria')
