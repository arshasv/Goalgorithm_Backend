"""add_presentation_rounds

Revision ID: a1b2c3d4e5f6
Revises: 585ddbe45cfc
Create Date: 2026-06-23 05:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = '585ddbe45cfc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add presentation_rounds table and round_id / weighted_score columns."""
    # Create presentation_rounds table
    op.create_table('presentation_rounds',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    # Add round_id and weighted_score to presentation_evaluations
    op.add_column('presentation_evaluations',
        sa.Column('round_id', sa.Uuid(), nullable=True)
    )
    op.add_column('presentation_evaluations',
        sa.Column('weighted_score', sa.Float(), nullable=True)
    )
    op.create_foreign_key(
        'fk_pres_eval_round_id', 'presentation_evaluations',
        'presentation_rounds', ['round_id'], ['id'], ondelete='CASCADE'
    )

    # Drop old unique constraint on team_id alone, add composite unique
    op.drop_index('ix_presentation_evaluations_team_id', table_name='presentation_evaluations')
    op.create_index(
        'ix_presentation_evaluations_team_round',
        'presentation_evaluations', ['team_id', 'round_id'], unique=True
    )

    # Add round_id to presentation_scores
    op.add_column('presentation_scores',
        sa.Column('round_id', sa.Uuid(), nullable=True)
    )
    op.create_foreign_key(
        'fk_pres_score_round_id', 'presentation_scores',
        'presentation_rounds', ['round_id'], ['id'], ondelete='CASCADE'
    )


def downgrade() -> None:
    """Remove presentation_rounds support."""
    op.drop_constraint('fk_pres_score_round_id', 'presentation_scores', type_='foreignkey')
    op.drop_column('presentation_scores', 'round_id')

    op.drop_index('ix_presentation_evaluations_team_round', table_name='presentation_evaluations')
    op.create_index(
        'ix_presentation_evaluations_team_id',
        'presentation_evaluations', ['team_id'], unique=True
    )

    op.drop_constraint('fk_pres_eval_round_id', 'presentation_evaluations', type_='foreignkey')
    op.drop_column('presentation_evaluations', 'weighted_score')
    op.drop_column('presentation_evaluations', 'round_id')

    op.drop_table('presentation_rounds')
