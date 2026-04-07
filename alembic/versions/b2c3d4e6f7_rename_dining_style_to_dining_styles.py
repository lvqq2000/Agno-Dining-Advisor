"""rename dining_style -> dining_styles (varchar[])

Revision ID: b2c3d4e6f7
Revises: a1b2c3d4e5f6
Create Date: 2026-04-07 12:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b2c3d4e6f7'
down_revision: Union[str, Sequence[str], None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Convert cag_reference_data.dining_style (string) -> dining_styles (varchar[]).

    Steps:
    1. add nullable dining_styles array column
    2. backfill from dining_style
    3. set dining_styles NOT NULL
    4. drop dining_style
    """
    op.add_column(
        'cag_reference_data',
        sa.Column('dining_styles', sa.ARRAY(sa.String()), nullable=True),
    )

    # Wrap existing single-value dining_style into an array for each row
    op.execute(
        "UPDATE cag_reference_data SET dining_styles = ARRAY[dining_style]::varchar[] WHERE dining_style IS NOT NULL"
    )

    # Make dining_styles non-nullable
    op.alter_column('cag_reference_data', 'dining_styles', nullable=False)

    # Drop old column
    op.drop_column('cag_reference_data', 'dining_style')


def downgrade() -> None:
    """Revert dining_styles -> dining_style (single string).

    This will keep only the first element if multiple were present.
    """
    op.add_column(
        'cag_reference_data',
        sa.Column('dining_style', sa.String(), nullable=True),
    )

    op.execute(
        "UPDATE cag_reference_data SET dining_style = (CASE WHEN array_length(dining_styles,1) >= 1 THEN dining_styles[1] ELSE NULL END)"
    )

    op.alter_column('cag_reference_data', 'dining_style', nullable=False)
    op.drop_column('cag_reference_data', 'dining_styles')
