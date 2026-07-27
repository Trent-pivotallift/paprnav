"""add reusable AD coverage and cost attribution

Revision ID: 20260726_0016
Revises: 20260726_0015
Create Date: 2026-07-26
"""

from alembic import op
import sqlalchemy as sa


revision = "20260726_0016"
down_revision = "20260726_0015"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("ad_source_snapshots", sa.Column("storage_bytes", sa.BigInteger(), nullable=True))

    op.create_table(
        "ad_coverage_sets",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("target_id", sa.String(length=36), nullable=False),
        sa.Column("current_source_snapshot_id", sa.String(length=36), nullable=True),
        sa.Column("status", sa.String(length=64), nullable=False),
        sa.Column("coverage_version", sa.String(length=128), nullable=False),
        sa.Column("first_triggered_by_aircraft_id", sa.String(length=36), nullable=True),
        sa.Column("first_triggered_by_organization_id", sa.String(length=36), nullable=True),
        sa.Column("directive_count", sa.Integer(), nullable=False),
        sa.Column("source_document_count", sa.Integer(), nullable=False),
        sa.Column("derived_storage_bytes", sa.BigInteger(), nullable=False),
        sa.Column("last_built_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["current_source_snapshot_id"], ["ad_source_snapshots.id"]),
        sa.ForeignKeyConstraint(["first_triggered_by_aircraft_id"], ["aircraft.id"]),
        sa.ForeignKeyConstraint(["first_triggered_by_organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["target_id"], ["applicability_targets.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("target_id"),
    )
    for column in [
        "target_id",
        "current_source_snapshot_id",
        "status",
        "first_triggered_by_aircraft_id",
        "first_triggered_by_organization_id",
    ]:
        op.create_index(op.f(f"ix_ad_coverage_sets_{column}"), "ad_coverage_sets", [column])

    op.create_table(
        "ad_coverage_subscriptions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("coverage_set_id", sa.String(length=36), nullable=False),
        sa.Column("aircraft_id", sa.String(length=36), nullable=False),
        sa.Column("organization_id", sa.String(length=36), nullable=False),
        sa.Column("status", sa.String(length=64), nullable=False),
        sa.Column("triggered_creation", sa.Boolean(), nullable=False),
        sa.Column("linked_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("last_resolved_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["aircraft_id"], ["aircraft.id"]),
        sa.ForeignKeyConstraint(["coverage_set_id"], ["ad_coverage_sets.id"]),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("coverage_set_id", "aircraft_id", name="uq_ad_coverage_subscription"),
    )
    for column in ["coverage_set_id", "aircraft_id", "organization_id", "status"]:
        op.create_index(
            op.f(f"ix_ad_coverage_subscriptions_{column}"),
            "ad_coverage_subscriptions",
            [column],
        )

    op.create_table(
        "ad_cost_ledger_entries",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("idempotency_key", sa.String(length=255), nullable=True),
        sa.Column("scope_type", sa.String(length=64), nullable=False),
        sa.Column("cost_category", sa.String(length=64), nullable=False),
        sa.Column("source_snapshot_id", sa.String(length=36), nullable=True),
        sa.Column("coverage_set_id", sa.String(length=36), nullable=True),
        sa.Column("aircraft_id", sa.String(length=36), nullable=True),
        sa.Column("organization_id", sa.String(length=36), nullable=True),
        sa.Column("usage_quantity", sa.Numeric(18, 6), nullable=False),
        sa.Column("usage_unit", sa.String(length=64), nullable=False),
        sa.Column("actual_cost_usd", sa.Numeric(18, 8), nullable=False),
        sa.Column("allocated_cost_usd", sa.Numeric(18, 8), nullable=False),
        sa.Column("attribution_status", sa.String(length=64), nullable=False),
        sa.Column("allocation_policy_version", sa.String(length=64), nullable=True),
        sa.Column("incurred_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["aircraft_id"], ["aircraft.id"]),
        sa.ForeignKeyConstraint(["coverage_set_id"], ["ad_coverage_sets.id"]),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["source_snapshot_id"], ["ad_source_snapshots.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in [
        "idempotency_key",
        "scope_type",
        "cost_category",
        "source_snapshot_id",
        "coverage_set_id",
        "aircraft_id",
        "organization_id",
        "attribution_status",
    ]:
        op.create_index(
            op.f(f"ix_ad_cost_ledger_entries_{column}"),
            "ad_cost_ledger_entries",
            [column],
            unique=column == "idempotency_key",
        )


def downgrade() -> None:
    for column in [
        "idempotency_key",
        "scope_type",
        "cost_category",
        "source_snapshot_id",
        "coverage_set_id",
        "aircraft_id",
        "organization_id",
        "attribution_status",
    ]:
        op.drop_index(op.f(f"ix_ad_cost_ledger_entries_{column}"), table_name="ad_cost_ledger_entries")
    op.drop_table("ad_cost_ledger_entries")

    for column in ["coverage_set_id", "aircraft_id", "organization_id", "status"]:
        op.drop_index(
            op.f(f"ix_ad_coverage_subscriptions_{column}"),
            table_name="ad_coverage_subscriptions",
        )
    op.drop_table("ad_coverage_subscriptions")

    for column in [
        "target_id",
        "current_source_snapshot_id",
        "status",
        "first_triggered_by_aircraft_id",
        "first_triggered_by_organization_id",
    ]:
        op.drop_index(op.f(f"ix_ad_coverage_sets_{column}"), table_name="ad_coverage_sets")
    op.drop_table("ad_coverage_sets")
    op.drop_column("ad_source_snapshots", "storage_bytes")
