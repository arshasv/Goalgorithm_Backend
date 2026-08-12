"""add_password_reset_otps_table

Revision ID: fd7f730d5d46
Revises: 6a7b8c9d0e1f
Create Date: 2026-06-18 06:12:01.774269

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = 'fd7f730d5d46'
down_revision: Union[str, Sequence[str], None] = '6a7b8c9d0e1f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'password_reset_otps',
        sa.Column('id', sa.Uuid(as_uuid=True), primary_key=True, default=None),
        sa.Column('user_id', sa.Uuid(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('otp_hash', sa.String(255), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('used', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table('password_reset_otps')
