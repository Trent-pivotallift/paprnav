"""add OCR review audit metadata

Revision ID: 20260722_0010
Revises: 20260710_0009
Create Date: 2026-07-22
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20260722_0010"
down_revision: Union[str, None] = "20260710_0009"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column("logbook_entries", "entry_date", existing_type=sa.Date(), nullable=True)
    op.add_column("logbook_entry_evidence", sa.Column("review_metadata", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.execute("UPDATE logbook_entries SET entry_date = CURRENT_DATE WHERE entry_date IS NULL")
    op.drop_column("logbook_entry_evidence", "review_metadata")
    op.alter_column("logbook_entries", "entry_date", existing_type=sa.Date(), nullable=False)
