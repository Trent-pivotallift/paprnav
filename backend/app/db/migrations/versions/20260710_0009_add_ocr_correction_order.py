"""add OCR correction ordering

Revision ID: 20260710_0009
Revises: 20260708_0008
Create Date: 2026-07-10
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20260710_0009"
down_revision: Union[str, None] = "20260708_0008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "ocr_corrections",
        sa.Column("correction_order", sa.Integer(), nullable=True),
    )
    op.execute(
        """
        UPDATE ocr_corrections
        SET correction_order = ordered.row_number
        FROM (
            SELECT
                id,
                ROW_NUMBER() OVER (
                    PARTITION BY ocr_text_span_id
                    ORDER BY created_at, id
                ) AS row_number
            FROM ocr_corrections
        ) AS ordered
        WHERE ocr_corrections.id = ordered.id
        """
    )
    op.alter_column(
        "ocr_corrections",
        "correction_order",
        existing_type=sa.Integer(),
        nullable=False,
    )
    op.create_index(
        "ix_ocr_corrections_span_order",
        "ocr_corrections",
        ["ocr_text_span_id", "correction_order"],
    )
    op.create_unique_constraint(
        "uq_ocr_corrections_span_order",
        "ocr_corrections",
        ["ocr_text_span_id", "correction_order"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_ocr_corrections_span_order", "ocr_corrections", type_="unique")
    op.drop_index("ix_ocr_corrections_span_order", table_name="ocr_corrections")
    op.drop_column("ocr_corrections", "correction_order")
