"""add review attestation and current AD match marker

Revision ID: 20260730_0017
Revises: 20260726_0016
Create Date: 2026-07-30
"""

from alembic import op
import sqlalchemy as sa


revision = "20260730_0017"
down_revision = "20260726_0016"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "logbook_entries",
        sa.Column("reviewed_by_user_id", sa.String(length=36), nullable=True),
    )
    op.add_column(
        "logbook_entries",
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_logbook_entries_reviewed_by_user_id_users",
        "logbook_entries",
        "users",
        ["reviewed_by_user_id"],
        ["id"],
    )
    op.create_index(
        op.f("ix_logbook_entries_reviewed_by_user_id"),
        "logbook_entries",
        ["reviewed_by_user_id"],
    )

    op.add_column(
        "ad_match_results",
        sa.Column(
            "is_current",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),
    )
    op.create_index(
        op.f("ix_ad_match_results_is_current"),
        "ad_match_results",
        ["is_current"],
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_ad_match_results_is_current"),
        table_name="ad_match_results",
    )
    op.drop_column("ad_match_results", "is_current")

    op.drop_index(
        op.f("ix_logbook_entries_reviewed_by_user_id"),
        table_name="logbook_entries",
    )
    op.drop_constraint(
        "fk_logbook_entries_reviewed_by_user_id_users",
        "logbook_entries",
        type_="foreignkey",
    )
    op.drop_column("logbook_entries", "reviewed_at")
    op.drop_column("logbook_entries", "reviewed_by_user_id")
