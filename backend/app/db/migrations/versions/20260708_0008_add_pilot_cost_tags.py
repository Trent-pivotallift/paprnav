"""add pilot cost allocation tags

Revision ID: 20260708_0008
Revises: 20260620_0007
Create Date: 2026-07-08
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20260708_0008"
down_revision: Union[str, None] = "20260620_0007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("organizations", sa.Column("customer_account_tag", sa.String(length=128), nullable=True))
    op.create_index(op.f("ix_organizations_customer_account_tag"), "organizations", ["customer_account_tag"], unique=True)

    op.add_column("aircraft", sa.Column("cost_allocation_tag", sa.String(length=128), nullable=True))
    op.create_index(op.f("ix_aircraft_cost_allocation_tag"), "aircraft", ["cost_allocation_tag"], unique=True)

    op.add_column("uploads", sa.Column("pilot_consent_accepted", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("uploads", sa.Column("initial_ocr_billable_to_tag", sa.String(length=128), nullable=True))
    op.add_column("uploads", sa.Column("cost_allocation_tags", sa.JSON(), nullable=True))
    op.create_index(op.f("ix_uploads_initial_ocr_billable_to_tag"), "uploads", ["initial_ocr_billable_to_tag"])

    op.add_column("ocr_runs", sa.Column("billing_status", sa.String(length=64), nullable=False, server_default="not_billable"))
    op.add_column("ocr_runs", sa.Column("billable_account_tag", sa.String(length=128), nullable=True))
    op.add_column("ocr_runs", sa.Column("billable_aircraft_tag", sa.String(length=128), nullable=True))
    op.add_column("ocr_runs", sa.Column("billable_page_count", sa.Integer(), nullable=True))
    op.add_column("ocr_runs", sa.Column("cost_allocation_tags", sa.JSON(), nullable=True))
    op.create_index(op.f("ix_ocr_runs_billable_account_tag"), "ocr_runs", ["billable_account_tag"])
    op.create_index(op.f("ix_ocr_runs_billable_aircraft_tag"), "ocr_runs", ["billable_aircraft_tag"])


def downgrade() -> None:
    op.drop_index(op.f("ix_ocr_runs_billable_aircraft_tag"), table_name="ocr_runs")
    op.drop_index(op.f("ix_ocr_runs_billable_account_tag"), table_name="ocr_runs")
    op.drop_column("ocr_runs", "cost_allocation_tags")
    op.drop_column("ocr_runs", "billable_page_count")
    op.drop_column("ocr_runs", "billable_aircraft_tag")
    op.drop_column("ocr_runs", "billable_account_tag")
    op.drop_column("ocr_runs", "billing_status")

    op.drop_index(op.f("ix_uploads_initial_ocr_billable_to_tag"), table_name="uploads")
    op.drop_column("uploads", "cost_allocation_tags")
    op.drop_column("uploads", "initial_ocr_billable_to_tag")
    op.drop_column("uploads", "pilot_consent_accepted")

    op.drop_index(op.f("ix_aircraft_cost_allocation_tag"), table_name="aircraft")
    op.drop_column("aircraft", "cost_allocation_tag")

    op.drop_index(op.f("ix_organizations_customer_account_tag"), table_name="organizations")
    op.drop_column("organizations", "customer_account_tag")
