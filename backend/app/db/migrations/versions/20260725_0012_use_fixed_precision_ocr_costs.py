"""use fixed precision OCR costs

Revision ID: 20260725_0012
Revises: 20260725_0011
Create Date: 2026-07-25
"""

from alembic import op
import sqlalchemy as sa


revision = "20260725_0012"
down_revision = "20260725_0011"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "ocr_runs",
        "pricing_rate_usd",
        existing_type=sa.Float(),
        type_=sa.Numeric(18, 8),
        existing_nullable=True,
        postgresql_using="pricing_rate_usd::numeric(18, 8)",
    )
    op.alter_column(
        "ocr_runs",
        "estimated_cost_usd",
        existing_type=sa.Float(),
        type_=sa.Numeric(18, 8),
        existing_nullable=True,
        postgresql_using="estimated_cost_usd::numeric(18, 8)",
    )


def downgrade() -> None:
    op.alter_column(
        "ocr_runs",
        "estimated_cost_usd",
        existing_type=sa.Numeric(18, 8),
        type_=sa.Float(),
        existing_nullable=True,
        postgresql_using="estimated_cost_usd::double precision",
    )
    op.alter_column(
        "ocr_runs",
        "pricing_rate_usd",
        existing_type=sa.Numeric(18, 8),
        type_=sa.Float(),
        existing_nullable=True,
        postgresql_using="pricing_rate_usd::double precision",
    )
