"""add component applicability tables

Revision ID: 20260620_0007
Revises: 20260619_0006
Create Date: 2026-06-20
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20260620_0007"
down_revision: Union[str, None] = "20260619_0006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column("airworthiness_directives", "discovery_record_id", existing_type=sa.String(length=36), nullable=True)

    op.create_table(
        "installed_components",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("aircraft_id", sa.String(length=36), nullable=False),
        sa.Column("role", sa.String(length=64), nullable=False),
        sa.Column("component_type", sa.String(length=64), nullable=False),
        sa.Column("make", sa.String(length=128), nullable=True),
        sa.Column("model", sa.String(length=128), nullable=True),
        sa.Column("serial_number", sa.String(length=128), nullable=True),
        sa.Column("installed_at", sa.Date(), nullable=True),
        sa.Column("removed_at", sa.Date(), nullable=True),
        sa.Column("source", sa.String(length=64), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["aircraft_id"], ["aircraft.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "aircraft_id",
            "role",
            "make",
            "model",
            "serial_number",
            "installed_at",
            name="uq_installed_component_identity",
        ),
    )
    for column in ["aircraft_id", "role", "component_type", "make", "model", "serial_number", "removed_at"]:
        op.create_index(op.f(f"ix_installed_components_{column}"), "installed_components", [column])

    op.create_table(
        "ad_source_snapshots",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("source_system", sa.String(length=64), nullable=False),
        sa.Column("source_type", sa.String(length=64), nullable=False),
        sa.Column("source_url", sa.String(length=1024), nullable=True),
        sa.Column("storage_backend", sa.String(length=64), nullable=True),
        sa.Column("storage_key", sa.String(length=1024), nullable=True),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column("filename", sa.String(length=512), nullable=True),
        sa.Column("captured_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(length=64), nullable=False),
        sa.Column("parser_name", sa.String(length=128), nullable=True),
        sa.Column("parser_version", sa.String(length=64), nullable=True),
        sa.Column("row_count", sa.Integer(), nullable=True),
        sa.Column("table_inventory", sa.JSON(), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in ["source_system", "source_type", "content_hash", "status"]:
        op.create_index(op.f(f"ix_ad_source_snapshots_{column}"), "ad_source_snapshots", [column])

    op.create_table(
        "applicability_targets",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("product_type", sa.String(length=64), nullable=False),
        sa.Column("product_subtype", sa.String(length=128), nullable=True),
        sa.Column("make", sa.String(length=255), nullable=True),
        sa.Column("model", sa.String(length=255), nullable=True),
        sa.Column("normalized_key", sa.String(length=512), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("product_type", "product_subtype", "make", "model", name="uq_applicability_target_identity"),
    )
    for column in ["product_type", "product_subtype", "make", "model"]:
        op.create_index(op.f(f"ix_applicability_targets_{column}"), "applicability_targets", [column])
    op.create_index(op.f("ix_applicability_targets_normalized_key"), "applicability_targets", ["normalized_key"], unique=True)

    op.create_table(
        "ad_publications",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("directive_id", sa.String(length=36), nullable=False),
        sa.Column("source_snapshot_id", sa.String(length=36), nullable=True),
        sa.Column("source_system", sa.String(length=64), nullable=False),
        sa.Column("source_type", sa.String(length=64), nullable=False),
        sa.Column("source_identifier", sa.String(length=255), nullable=False),
        sa.Column("title", sa.Text(), nullable=True),
        sa.Column("publication_date", sa.Date(), nullable=True),
        sa.Column("effective_date", sa.Date(), nullable=True),
        sa.Column("html_url", sa.String(length=1024), nullable=True),
        sa.Column("pdf_url", sa.String(length=1024), nullable=True),
        sa.Column("status", sa.String(length=64), nullable=True),
        sa.Column("content_hash", sa.String(length=64), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["directive_id"], ["airworthiness_directives.id"]),
        sa.ForeignKeyConstraint(["source_snapshot_id"], ["ad_source_snapshots.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "directive_id",
            "source_system",
            "source_type",
            "source_identifier",
            name="uq_ad_publication_identity",
        ),
    )
    for column in [
        "directive_id",
        "source_snapshot_id",
        "source_system",
        "source_type",
        "source_identifier",
        "publication_date",
        "status",
        "content_hash",
    ]:
        op.create_index(op.f(f"ix_ad_publications_{column}"), "ad_publications", [column])

    op.create_table(
        "ad_target_applicability",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("directive_id", sa.String(length=36), nullable=False),
        sa.Column("target_id", sa.String(length=36), nullable=False),
        sa.Column("source_publication_id", sa.String(length=36), nullable=True),
        sa.Column("applicability_basis", sa.String(length=64), nullable=False),
        sa.Column("serial_range", sa.JSON(), nullable=True),
        sa.Column("conditions", sa.JSON(), nullable=True),
        sa.Column("compliance_actions", sa.JSON(), nullable=True),
        sa.Column("compliance_intervals", sa.JSON(), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("citations", sa.JSON(), nullable=True),
        sa.Column("status", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["directive_id"], ["airworthiness_directives.id"]),
        sa.ForeignKeyConstraint(["source_publication_id"], ["ad_publications.id"]),
        sa.ForeignKeyConstraint(["target_id"], ["applicability_targets.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "directive_id",
            "target_id",
            "source_publication_id",
            "applicability_basis",
            name="uq_ad_target_applicability",
        ),
    )
    for column in ["directive_id", "target_id", "source_publication_id", "status"]:
        op.create_index(op.f(f"ix_ad_target_applicability_{column}"), "ad_target_applicability", [column])

    op.create_table(
        "ad_reconciliation_issues",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("issue_type", sa.String(length=128), nullable=False),
        sa.Column("severity", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=64), nullable=False),
        sa.Column("directive_id", sa.String(length=36), nullable=True),
        sa.Column("publication_id", sa.String(length=36), nullable=True),
        sa.Column("target_id", sa.String(length=36), nullable=True),
        sa.Column("aircraft_id", sa.String(length=36), nullable=True),
        sa.Column("source_snapshot_id", sa.String(length=36), nullable=True),
        sa.Column("payload", sa.JSON(), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["aircraft_id"], ["aircraft.id"]),
        sa.ForeignKeyConstraint(["directive_id"], ["airworthiness_directives.id"]),
        sa.ForeignKeyConstraint(["publication_id"], ["ad_publications.id"]),
        sa.ForeignKeyConstraint(["source_snapshot_id"], ["ad_source_snapshots.id"]),
        sa.ForeignKeyConstraint(["target_id"], ["applicability_targets.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in ["issue_type", "severity", "status", "directive_id", "publication_id", "target_id", "aircraft_id", "source_snapshot_id"]:
        op.create_index(op.f(f"ix_ad_reconciliation_issues_{column}"), "ad_reconciliation_issues", [column])

    op.add_column("ad_match_results", sa.Column("installed_component_id", sa.String(length=36), nullable=True))
    op.add_column("ad_match_results", sa.Column("target_applicability_id", sa.String(length=36), nullable=True))
    op.add_column("ad_match_results", sa.Column("applicability_snapshot", sa.JSON(), nullable=True))
    op.create_foreign_key("fk_ad_match_results_installed_component_id", "ad_match_results", "installed_components", ["installed_component_id"], ["id"])
    op.create_foreign_key("fk_ad_match_results_target_applicability_id", "ad_match_results", "ad_target_applicability", ["target_applicability_id"], ["id"])
    op.create_index(op.f("ix_ad_match_results_installed_component_id"), "ad_match_results", ["installed_component_id"])
    op.create_index(op.f("ix_ad_match_results_target_applicability_id"), "ad_match_results", ["target_applicability_id"])


def downgrade() -> None:
    op.drop_index(op.f("ix_ad_match_results_target_applicability_id"), table_name="ad_match_results")
    op.drop_index(op.f("ix_ad_match_results_installed_component_id"), table_name="ad_match_results")
    op.drop_constraint("fk_ad_match_results_target_applicability_id", "ad_match_results", type_="foreignkey")
    op.drop_constraint("fk_ad_match_results_installed_component_id", "ad_match_results", type_="foreignkey")
    op.drop_column("ad_match_results", "applicability_snapshot")
    op.drop_column("ad_match_results", "target_applicability_id")
    op.drop_column("ad_match_results", "installed_component_id")

    for column in ["issue_type", "severity", "status", "directive_id", "publication_id", "target_id", "aircraft_id", "source_snapshot_id"]:
        op.drop_index(op.f(f"ix_ad_reconciliation_issues_{column}"), table_name="ad_reconciliation_issues")
    op.drop_table("ad_reconciliation_issues")

    for column in ["directive_id", "target_id", "source_publication_id", "status"]:
        op.drop_index(op.f(f"ix_ad_target_applicability_{column}"), table_name="ad_target_applicability")
    op.drop_table("ad_target_applicability")

    for column in [
        "directive_id",
        "source_snapshot_id",
        "source_system",
        "source_type",
        "source_identifier",
        "publication_date",
        "status",
        "content_hash",
    ]:
        op.drop_index(op.f(f"ix_ad_publications_{column}"), table_name="ad_publications")
    op.drop_table("ad_publications")

    op.drop_index(op.f("ix_applicability_targets_normalized_key"), table_name="applicability_targets")
    for column in ["product_type", "product_subtype", "make", "model"]:
        op.drop_index(op.f(f"ix_applicability_targets_{column}"), table_name="applicability_targets")
    op.drop_table("applicability_targets")

    for column in ["source_system", "source_type", "content_hash", "status"]:
        op.drop_index(op.f(f"ix_ad_source_snapshots_{column}"), table_name="ad_source_snapshots")
    op.drop_table("ad_source_snapshots")

    for column in ["aircraft_id", "role", "component_type", "make", "model", "serial_number", "removed_at"]:
        op.drop_index(op.f(f"ix_installed_components_{column}"), table_name="installed_components")
    op.drop_table("installed_components")

    op.alter_column("airworthiness_directives", "discovery_record_id", existing_type=sa.String(length=36), nullable=False)
