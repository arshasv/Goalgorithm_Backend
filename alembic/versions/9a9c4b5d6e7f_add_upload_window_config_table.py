"""add upload_window_config table

Revision ID: 9a9c4b5d6e7f
Revises: 2a9b3c5d7e8f
Create Date: 2026-06-12 09:33:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '9a9c4b5d6e7f'
down_revision = '2a9b3c5d7e8f'
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table('upload_window_config',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('is_enabled', sa.Boolean(), nullable=False),
    sa.Column('start_time', sa.DateTime(timezone=True), nullable=True),
    sa.Column('end_time', sa.DateTime(timezone=True), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )

def downgrade() -> None:
    op.drop_table('upload_window_config')
