"""convert prompt_templates.template_type enum -> varchar

Revision ID: d4e5f6_change_prompt_template_enum_to_varchar
Revises: c3d4e5f8g9
Create Date: 2026-04-07 12:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd4e5f6'
down_revision: Union[str, Sequence[str], None] = 'c3d4e5f8g9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Convert enum column to plain varchar (store enum labels as text)
    op.execute("ALTER TABLE prompt_templates ALTER COLUMN template_type TYPE VARCHAR USING template_type::text;")
    # Drop the enum type if present
    op.execute("DROP TYPE IF EXISTS template_type_enum;")


def downgrade() -> None:
    # Recreate enum type and convert back to enum (best-effort)
    op.execute("CREATE TYPE template_type_enum AS ENUM ('recommendation_with_cag','random_recommendation');")
    op.execute("ALTER TABLE prompt_templates ALTER COLUMN template_type TYPE template_type_enum USING template_type::text::template_type_enum;")
