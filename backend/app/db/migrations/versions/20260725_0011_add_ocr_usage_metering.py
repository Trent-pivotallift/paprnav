"""add provider-neutral OCR usage metering

Revision ID: 20260725_0011
Revises: 20260722_0010
Create Date: 2026-07-25
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260725_0011"
down_revision: Union[str, None] = "20260722_0010"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "ocr_runs",
        sa.Column("processing_seconds", sa.Float(), nullable=True),
    )
    op.add_column(
        "ocr_runs",
        sa.Column("pricing_unit", sa.String(length=64), nullable=True),
    )
    op.add_column(
        "ocr_runs",
        sa.Column("pricing_rate_usd", sa.Float(), nullable=True),
    )
    op.add_column(
        "ocr_runs",
        sa.Column("estimated_cost_usd", sa.Float(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("ocr_runs", "estimated_cost_usd")
    op.drop_column("ocr_runs", "pricing_rate_usd")
    op.drop_column("ocr_runs", "pricing_unit")
    op.drop_column("ocr_runs", "processing_seconds")
