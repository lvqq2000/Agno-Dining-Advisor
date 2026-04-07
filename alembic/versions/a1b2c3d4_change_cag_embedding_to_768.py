"""change cag embedding to 768

Revision ID: a1b2c3d4e5f6
Revises: d9f1b8c7a6e5
Create Date: 2026-04-07 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = 'd9f1b8c7a6e5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Alter cag_reference_data.embedding to vector(768)."""
    # The USING cast is a no-op for pgvector when reducing/increasing dims if stored properly,
    # but we include an explicit ALTER TYPE command.
    op.execute("ALTER TABLE cag_reference_data ALTER COLUMN embedding TYPE vector(768);")


def downgrade() -> None:
    """Revert embedding to 1536 (previous accidental value)."""
    op.execute("ALTER TABLE cag_reference_data ALTER COLUMN embedding TYPE vector(1536);")
