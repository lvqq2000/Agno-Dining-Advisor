"""add traces table

Revision ID: d9f1b8c7a6e5
Revises: 97395532e89d
Create Date: 2026-04-07 09:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd9f1b8c7a6e5'
down_revision: Union[str, Sequence[str], None] = '97395532e89d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema: create traces table."""
    op.create_table(
        'traces',
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('session_id', sa.String(length=64), nullable=False),
        sa.Column('step_name', sa.String(length=128), nullable=False),
        sa.Column('input', sa.Text(), nullable=True),
        sa.Column('output', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=32), nullable=False),
        sa.Column('prompt_version', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    op.create_index('ix_traces_session_id', 'traces', ['session_id'])


def downgrade() -> None:
    """Downgrade schema: drop traces table."""
    op.drop_index('ix_traces_session_id', table_name='traces')
    op.drop_table('traces')
