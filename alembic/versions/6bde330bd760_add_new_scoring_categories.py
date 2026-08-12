"""add_new_scoring_categories

Revision ID: 6bde330bd760
Revises: fa29c9cf75ff
Create Date: 2026-06-25 14:12:27.989426

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6bde330bd760'
down_revision: Union[str, Sequence[str], None] = 'fa29c9cf75ff'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    from sqlalchemy.engine.reflection import Inspector
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    score_cols = [c['name'] for c in inspector.get_columns('scores')]
    config_cols = [c['name'] for c in inspector.get_columns('scoring_configs')]

    if 'total_goals_points' not in score_cols:
        op.add_column('scores', sa.Column('total_goals_points', sa.Float(), nullable=True))
    if 'btts_points' not in score_cols:
        op.add_column('scores', sa.Column('btts_points', sa.Float(), nullable=True))
    if 'first_team_to_score_points' not in score_cols:
        op.add_column('scores', sa.Column('first_team_to_score_points', sa.Float(), nullable=True))
    if 'clean_sheet_points' not in score_cols:
        op.add_column('scores', sa.Column('clean_sheet_points', sa.Float(), nullable=True))

    if 'total_goals_points_exact' not in config_cols:
        op.add_column('scoring_configs', sa.Column('total_goals_points_exact', sa.Integer(), server_default='5', nullable=False))
    if 'total_goals_points_wrong' not in config_cols:
        op.add_column('scoring_configs', sa.Column('total_goals_points_wrong', sa.Integer(), server_default='0', nullable=False))
    if 'btts_points_correct' not in config_cols:
        op.add_column('scoring_configs', sa.Column('btts_points_correct', sa.Integer(), server_default='5', nullable=False))
    if 'btts_points_incorrect' not in config_cols:
        op.add_column('scoring_configs', sa.Column('btts_points_incorrect', sa.Integer(), server_default='0', nullable=False))
    if 'first_team_to_score_points_correct' not in config_cols:
        op.add_column('scoring_configs', sa.Column('first_team_to_score_points_correct', sa.Integer(), server_default='5', nullable=False))
    if 'first_team_to_score_points_incorrect' not in config_cols:
        op.add_column('scoring_configs', sa.Column('first_team_to_score_points_incorrect', sa.Integer(), server_default='0', nullable=False))
    if 'clean_sheet_points_correct' not in config_cols:
        op.add_column('scoring_configs', sa.Column('clean_sheet_points_correct', sa.Integer(), server_default='5', nullable=False))
    if 'clean_sheet_points_incorrect' not in config_cols:
        op.add_column('scoring_configs', sa.Column('clean_sheet_points_incorrect', sa.Integer(), server_default='0', nullable=False))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('scores', 'total_goals_points')
    op.drop_column('scores', 'btts_points')
    op.drop_column('scores', 'first_team_to_score_points')
    op.drop_column('scores', 'clean_sheet_points')

    op.drop_column('scoring_configs', 'total_goals_points_exact')
    op.drop_column('scoring_configs', 'total_goals_points_wrong')
    op.drop_column('scoring_configs', 'btts_points_correct')
    op.drop_column('scoring_configs', 'btts_points_incorrect')
    op.drop_column('scoring_configs', 'first_team_to_score_points_correct')
    op.drop_column('scoring_configs', 'first_team_to_score_points_incorrect')
    op.drop_column('scoring_configs', 'clean_sheet_points_correct')
    op.drop_column('scoring_configs', 'clean_sheet_points_incorrect')
