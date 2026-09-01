"""reserve the v3 AMOC envelope repair boundary

Revision ID: 20260822_0023
Revises: 20260822_0022
Create Date: 2026-08-22
"""

from alembic import op


revision = "20260822_0023"
down_revision = "20260822_0022"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Never add semantic fields to extraction or signed-review JSON in a data
    # migration. Revision 0024 repairs databases that previously ran the older
    # 0023 implementation by conservatively reopening the ambiguous cohort.
    pass


def downgrade() -> None:
    # Data-only compatibility backfill is intentionally retained on downgrade;
    # removing a key could destroy subsequently reviewed AMOC content.
    pass
