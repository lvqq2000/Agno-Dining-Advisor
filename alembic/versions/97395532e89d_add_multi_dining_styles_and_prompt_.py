"""add multi dining styles and prompt template type/version uniqueness

Revision ID: 97395532e89d
Revises: f28c68565e0b
Create Date: 2026-04-07 08:37:54.474865

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '97395532e89d'
down_revision: Union[str, Sequence[str], None] = 'f28c68565e0b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
