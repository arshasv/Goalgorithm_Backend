"""add scoring_configs table and config_id to scores

Revision ID: 1e8b23c4f5a6
Revises: ce7911c81a9b
Create Date: 2026-06-12 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '1e8b23c4f5a6'
down_revision: Union[str, Sequence[str], None] = 'ce7911c81a9b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('scoring_configs',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('now()')),
        sa.Column('winner_points_correct', sa.Integer(), nullable=False, server_default='5'),
        sa.Column('winner_points_incorrect', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('scoreline_points_exact', sa.Integer(), nullable=False, server_default='10'),
        sa.Column('scoreline_points_margin', sa.Integer(), nullable=False, server_default='5'),
        sa.Column('scoreline_points_incorrect', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('probability_threshold', sa.Float(), nullable=False, server_default='15.0'),
        sa.Column('probability_points_pass', sa.Integer(), nullable=False, server_default='5'),
        sa.Column('probability_points_fail', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('player_points_exact', sa.Integer(), nullable=False, server_default='5'),
        sa.Column('player_points_close', sa.Integer(), nullable=False, server_default='2'),
        sa.Column('player_points_wrong', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('player_avg_threshold_exact', sa.Float(), nullable=False, server_default='4.0'),
        sa.Column('player_avg_threshold_close', sa.Float(), nullable=False, server_default='2.0'),
        sa.Column('max_base_score', sa.Integer(), nullable=False, server_default='25'),
        sa.Column('technical_max_per_category', sa.Integer(), nullable=False, server_default='5'),
        sa.Column('technical_max_total', sa.Integer(), nullable=False, server_default='20'),
        sa.Column('presentation_ai_explanation_max', sa.Integer(), nullable=False, server_default='20'),
        sa.Column('presentation_qa_score_max', sa.Integer(), nullable=False, server_default='15'),
        sa.Column('presentation_delivery_score_max', sa.Integer(), nullable=False, server_default='15'),
        sa.Column('presentation_denominator', sa.Integer(), nullable=False, server_default='150'),
        sa.Column('presentation_max_marks', sa.Integer(), nullable=False, server_default='20'),
        sa.Column('multiplier_a', sa.Integer(), nullable=False, server_default='3'),
        sa.Column('multiplier_b', sa.Integer(), nullable=False, server_default='2'),
        sa.Column('multiplier_c', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('phase1_max_marks', sa.Integer(), nullable=False, server_default='60'),
        sa.PrimaryKeyConstraint('id'),
    )

    op.add_column('scores', sa.Column('config_id', sa.String(255), nullable=True))

    op.execute(
        "INSERT INTO scoring_configs (id, name, is_active, version) VALUES "
        "('00000000-0000-0000-0000-000000000001', 'Default 2026', true, 1)"
    )


def downgrade() -> None:
    op.drop_column('scores', 'config_id')
    op.drop_table('scoring_configs')
