"""Add model execution tracking

Revision ID: c1d2e3f4g5h6
Revises: 6bde330bd760
Create Date: 2026-06-25 15:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c1d2e3f4g5h6'
down_revision = '6bde330bd760'
branch_labels = None
depends_on = None


def upgrade() -> None:
    from sqlalchemy.engine.reflection import Inspector
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    tables = inspector.get_table_names()

    if 'model_uploads' not in tables:
        op.create_table(
            'model_uploads',
            sa.Column('id', sa.Uuid(), nullable=False),
            sa.Column('team_id', sa.Uuid(), nullable=False),
            sa.Column('match_id', sa.Uuid(), nullable=False),
            sa.Column('original_filename', sa.String(length=255), nullable=False),
            sa.Column('stored_file_path', sa.String(length=1024), nullable=False),
            sa.Column('status', sa.String(length=50), nullable=False),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(['match_id'], ['matches.id'], ),
            sa.ForeignKeyConstraint(['team_id'], ['teams.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_model_uploads_id'), 'model_uploads', ['id'], unique=False)
        
    if 'model_executions' not in tables:
        op.create_table(
            'model_executions',
            sa.Column('id', sa.Uuid(), nullable=False),
            sa.Column('model_upload_id', sa.Uuid(), nullable=False),
            sa.Column('status', sa.String(length=50), nullable=False),
            sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('error_message', sa.String(), nullable=True),
            sa.Column('prediction_id', sa.Uuid(), nullable=True),
            sa.ForeignKeyConstraint(['model_upload_id'], ['model_uploads.id'], ),
            sa.ForeignKeyConstraint(['prediction_id'], ['predictions.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_model_executions_id'), 'model_executions', ['id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_model_executions_id'), table_name='model_executions')
    op.drop_table('model_executions')
    op.drop_index(op.f('ix_model_uploads_id'), table_name='model_uploads')
    op.drop_table('model_uploads')
