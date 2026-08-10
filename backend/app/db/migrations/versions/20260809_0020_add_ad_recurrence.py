"""add normalized AD recurrence and aircraft due-state tables

Revision ID: 20260809_0020
Revises: 20260806_0019
Create Date: 2026-08-09
"""

from alembic import op
import sqlalchemy as sa


revision = "20260809_0020"
down_revision = "20260806_0019"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "ad_compliance_requirements",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("directive_id", sa.String(length=36), nullable=False),
        sa.Column("target_applicability_id", sa.String(length=36), nullable=False),
        sa.Column("source_extraction_id", sa.String(length=36), nullable=False),
        sa.Column("requirement_hash", sa.String(length=64), nullable=False),
        sa.Column("requirement_type", sa.String(length=64), nullable=False),
        sa.Column("combination_logic", sa.String(length=32), nullable=False),
        sa.Column("action_text", sa.Text(), nullable=False),
        sa.Column("terminating_action_text", sa.Text(), nullable=True),
        sa.Column("effective_date", sa.Date(), nullable=True),
        sa.Column("review_status", sa.String(length=64), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("citations", sa.JSON(), nullable=True),
        sa.Column("source_payload", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["directive_id"], ["airworthiness_directives.id"]),
        sa.ForeignKeyConstraint(["target_applicability_id"], ["ad_target_applicability.id"]),
        sa.ForeignKeyConstraint(["source_extraction_id"], ["ad_extractions.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("requirement_hash"),
    )
    for column in ["directive_id", "target_applicability_id", "source_extraction_id", "requirement_hash", "requirement_type", "review_status", "status"]:
        op.create_index(op.f(f"ix_ad_compliance_requirements_{column}"), "ad_compliance_requirements", [column])

    op.create_table(
        "ad_compliance_triggers",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("requirement_id", sa.String(length=36), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("metric", sa.String(length=64), nullable=False),
        sa.Column("interval_value", sa.Numeric(14, 3), nullable=False),
        sa.Column("interval_unit", sa.String(length=32), nullable=False),
        sa.Column("anchor_kind", sa.String(length=64), nullable=False),
        sa.Column("source_text", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["requirement_id"], ["ad_compliance_requirements.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("requirement_id", "sequence", name="uq_ad_compliance_trigger_sequence"),
    )
    op.create_index(op.f("ix_ad_compliance_triggers_requirement_id"), "ad_compliance_triggers", ["requirement_id"])
    op.create_index(op.f("ix_ad_compliance_triggers_metric"), "ad_compliance_triggers", ["metric"])

    op.create_table(
        "ad_compliance_events",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("evidence_key", sa.String(length=64), nullable=False),
        sa.Column("requirement_id", sa.String(length=36), nullable=False),
        sa.Column("aircraft_id", sa.String(length=36), nullable=False),
        sa.Column("installed_component_id", sa.String(length=36), nullable=True),
        sa.Column("logbook_entry_id", sa.String(length=36), nullable=False),
        sa.Column("occurred_on", sa.Date(), nullable=False),
        sa.Column("action_text", sa.Text(), nullable=False),
        sa.Column("tach_hours", sa.Numeric(14, 3), nullable=True),
        sa.Column("hobbs_hours", sa.Numeric(14, 3), nullable=True),
        sa.Column("total_time_hours", sa.Numeric(14, 3), nullable=True),
        sa.Column("cycle_count", sa.Integer(), nullable=True),
        sa.Column("is_terminating_action", sa.Boolean(), nullable=False),
        sa.Column("verification_status", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["requirement_id"], ["ad_compliance_requirements.id"]),
        sa.ForeignKeyConstraint(["aircraft_id"], ["aircraft.id"]),
        sa.ForeignKeyConstraint(["installed_component_id"], ["installed_components.id"]),
        sa.ForeignKeyConstraint(["logbook_entry_id"], ["logbook_entries.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("evidence_key"),
    )
    for column in ["evidence_key", "requirement_id", "aircraft_id", "installed_component_id", "logbook_entry_id", "occurred_on", "verification_status"]:
        op.create_index(op.f(f"ix_ad_compliance_events_{column}"), "ad_compliance_events", [column])

    op.create_table(
        "aircraft_time_states",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("state_hash", sa.String(length=64), nullable=False),
        sa.Column("aircraft_id", sa.String(length=36), nullable=False),
        sa.Column("installed_component_id", sa.String(length=36), nullable=True),
        sa.Column("source_logbook_entry_id", sa.String(length=36), nullable=True),
        sa.Column("observed_on", sa.Date(), nullable=False),
        sa.Column("tach_hours", sa.Numeric(14, 3), nullable=True),
        sa.Column("hobbs_hours", sa.Numeric(14, 3), nullable=True),
        sa.Column("total_time_hours", sa.Numeric(14, 3), nullable=True),
        sa.Column("cycle_count", sa.Integer(), nullable=True),
        sa.Column("verification_status", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["aircraft_id"], ["aircraft.id"]),
        sa.ForeignKeyConstraint(["installed_component_id"], ["installed_components.id"]),
        sa.ForeignKeyConstraint(["source_logbook_entry_id"], ["logbook_entries.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("state_hash"),
    )
    for column in ["state_hash", "aircraft_id", "installed_component_id", "source_logbook_entry_id", "observed_on", "verification_status"]:
        op.create_index(op.f(f"ix_aircraft_time_states_{column}"), "aircraft_time_states", [column])

    op.create_table(
        "aircraft_ad_due_states",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("aircraft_id", sa.String(length=36), nullable=False),
        sa.Column("requirement_id", sa.String(length=36), nullable=False),
        sa.Column("installed_component_id", sa.String(length=36), nullable=True),
        sa.Column("last_compliance_event_id", sa.String(length=36), nullable=True),
        sa.Column("status", sa.String(length=64), nullable=False),
        sa.Column("due_date", sa.Date(), nullable=True),
        sa.Column("due_metric", sa.String(length=64), nullable=True),
        sa.Column("due_value", sa.Numeric(14, 3), nullable=True),
        sa.Column("trigger_states", sa.JSON(), nullable=True),
        sa.Column("unresolved_reasons", sa.JSON(), nullable=True),
        sa.Column("algorithm_version", sa.String(length=64), nullable=False),
        sa.Column("input_hash", sa.String(length=64), nullable=False),
        sa.Column("is_current", sa.Boolean(), nullable=False),
        sa.Column("computed_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["aircraft_id"], ["aircraft.id"]),
        sa.ForeignKeyConstraint(["requirement_id"], ["ad_compliance_requirements.id"]),
        sa.ForeignKeyConstraint(["installed_component_id"], ["installed_components.id"]),
        sa.ForeignKeyConstraint(["last_compliance_event_id"], ["ad_compliance_events.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "aircraft_id",
            "requirement_id",
            "installed_component_id",
            "algorithm_version",
            "input_hash",
            name="uq_aircraft_ad_due_state_replay",
        ),
    )
    for column in ["aircraft_id", "requirement_id", "installed_component_id", "last_compliance_event_id", "status", "due_date", "input_hash", "is_current"]:
        op.create_index(op.f(f"ix_aircraft_ad_due_states_{column}"), "aircraft_ad_due_states", [column])
    op.add_column("ad_match_results", sa.Column("due_state_id", sa.String(length=36), nullable=True))
    op.create_foreign_key(
        "fk_ad_match_results_due_state_id",
        "ad_match_results",
        "aircraft_ad_due_states",
        ["due_state_id"],
        ["id"],
    )
    op.create_index(op.f("ix_ad_match_results_due_state_id"), "ad_match_results", ["due_state_id"])


def downgrade() -> None:
    op.drop_index(op.f("ix_ad_match_results_due_state_id"), table_name="ad_match_results")
    op.drop_constraint("fk_ad_match_results_due_state_id", "ad_match_results", type_="foreignkey")
    op.drop_column("ad_match_results", "due_state_id")
    op.drop_table("aircraft_ad_due_states")
    op.drop_table("aircraft_time_states")
    op.drop_table("ad_compliance_events")
    op.drop_table("ad_compliance_triggers")
    op.drop_table("ad_compliance_requirements")
