"""expand applicability product subtype for retained DRS axis evidence

Revision ID: 20260806_0019
Revises: 20260804_0018
Create Date: 2026-08-06
"""

from alembic import op
import sqlalchemy as sa


revision = "20260806_0019"
down_revision = "20260804_0018"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "applicability_targets",
        "product_subtype",
        existing_type=sa.String(length=128),
        type_=sa.String(length=512),
        existing_nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        "applicability_targets",
        "product_subtype",
        existing_type=sa.String(length=512),
        type_=sa.String(length=128),
        existing_nullable=True,
    )
