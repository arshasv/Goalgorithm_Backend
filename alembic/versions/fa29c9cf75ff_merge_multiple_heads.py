"""merge multiple heads

Revision ID: fa29c9cf75ff
Revises: a1b2c3d4e5f7, b1c2d3e4f5g6, e7f8a9b0c1d2
Create Date: 2026-06-25 14:12:06.502806

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'fa29c9cf75ff'
down_revision: Union[str, Sequence[str], None] = ('a1b2c3d4e5f7', 'b1c2d3e4f5g6', 'e7f8a9b0c1d2')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
