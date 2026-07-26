"""add provider-neutral candidate validation

Revision ID: 20260726_0015
Revises: 20260726_0014
Create Date: 2026-07-26
"""

from alembic import op
import sqlalchemy as sa


revision = "20260726_0015"
down_revision = "20260726_0014"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("logbook_entries", sa.Column("validation_status", sa.String(length=64), nullable=True))
    op.add_column("logbook_entries", sa.Column("validation_results", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("logbook_entries", "validation_results")
    op.drop_column("logbook_entries", "validation_status")
