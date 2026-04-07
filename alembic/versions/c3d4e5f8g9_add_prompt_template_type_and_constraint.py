"""add template_type enum column and unique constraint (template_type, version)

Revision ID: c3d4e5f8g9
Revises: a1b2c3d4e5f6
Create Date: 2026-04-07 12:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c3d4e5f8g9'
down_revision: Union[str, Sequence[str], None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add template_type enum and a composite unique constraint (template_type, version).

    Steps:
    - create enum type template_type_enum
    - drop any existing unique constraint that only covers 'version'
    - add template_type column (non-null) with a safe server default
    - create new unique constraint on (template_type, version)
    """
    # Create enum type
    op.execute(
        "CREATE TYPE template_type_enum AS ENUM ('recommendation_with_cag','random_recommendation');"
    )

    # Drop any unique constraint that only covers the 'version' column (name is unknown)
    op.execute(
        """
        DO $$
        DECLARE
          conname TEXT;
        BEGIN
          SELECT c.conname INTO conname
          FROM pg_constraint c
          JOIN pg_class t ON c.conrelid = t.oid
          WHERE t.relname = 'prompt_templates'
            AND c.contype = 'u'
            AND array_length(c.conkey,1) = 1
            AND (SELECT attname FROM pg_attribute WHERE attrelid = t.oid AND attnum = c.conkey[1]) = 'version'
          LIMIT 1;
          IF conname IS NOT NULL THEN
            EXECUTE format('ALTER TABLE prompt_templates DROP CONSTRAINT %I', conname);
          END IF;
        END$$;
        """
    )

    # Add the new column with server default to avoid NOT NULL issues for existing rows
    op.add_column(
        'prompt_templates',
        sa.Column('template_type', sa.Enum('recommendation_with_cag','random_recommendation', name='template_type_enum'), nullable=False, server_default='recommendation_with_cag'),
    )

    # Create composite unique constraint for template_type + version
    op.create_unique_constraint('uq_template_version', 'prompt_templates', ['template_type', 'version'])

    # Remove server default (optional / cleanup)
    op.alter_column('prompt_templates', 'template_type', server_default=None)


def downgrade() -> None:
    # Drop the composite unique constraint and column, then drop the enum type
    op.drop_constraint('uq_template_version', 'prompt_templates', type_='unique')
    op.drop_column('prompt_templates', 'template_type')
    op.execute('DROP TYPE IF EXISTS template_type_enum;')
