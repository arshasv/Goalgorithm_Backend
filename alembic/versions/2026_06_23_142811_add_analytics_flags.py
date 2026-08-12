"""Add granular analytics visibility flags

Revision ID: 2026_06_23_142811
Revises: d57820ca7344
Create Date: 2026-06-23 14:28:11.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2026_06_23_142811'
down_revision = 'd57820ca7344'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add new boolean columns
    op.add_column('leaderboard_visibility', sa.Column('analytics_visibility_enabled', sa.Boolean(), server_default='0', nullable=False))
    op.add_column('leaderboard_visibility', sa.Column('show_model_analytics', sa.Boolean(), server_default='1', nullable=False))
    op.add_column('leaderboard_visibility', sa.Column('show_prediction_analytics', sa.Boolean(), server_default='1', nullable=False))
    op.add_column('leaderboard_visibility', sa.Column('show_technical_analytics', sa.Boolean(), server_default='1', nullable=False))
    op.add_column('leaderboard_visibility', sa.Column('show_presentation_analytics', sa.Boolean(), server_default='1', nullable=False))
    op.add_column('leaderboard_visibility', sa.Column('show_overall_comparison', sa.Boolean(), server_default='1', nullable=False))


def downgrade() -> None:
    op.drop_column('leaderboard_visibility', 'show_overall_comparison')
    op.drop_column('leaderboard_visibility', 'show_presentation_analytics')
    op.drop_column('leaderboard_visibility', 'show_technical_analytics')
    op.drop_column('leaderboard_visibility', 'show_prediction_analytics')
    op.drop_column('leaderboard_visibility', 'show_model_analytics')
    op.drop_column('leaderboard_visibility', 'analytics_visibility_enabled')
