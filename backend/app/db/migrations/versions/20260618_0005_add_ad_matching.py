"""add ad matching tables

Revision ID: 20260618_0005
Revises: 20260618_0004
Create Date: 2026-06-18
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20260618_0005"
down_revision: Union[str, None] = "20260618_0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "ad_match_results",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("aircraft_id", sa.String(length=36), nullable=False),
        sa.Column("directive_id", sa.String(length=36), nullable=False),
        sa.Column("extraction_id", sa.String(length=36), nullable=False),
        sa.Column("status", sa.String(length=64), nullable=False),
        sa.Column("match_type", sa.String(length=64), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("rationale", sa.Text(), nullable=False),
        sa.Column("unresolved_reasons", sa.JSON(), nullable=True),
        sa.Column("algorithm_name", sa.String(length=128), nullable=False),
        sa.Column("algorithm_version", sa.String(length=128), nullable=False),
        sa.Column("input_hash", sa.String(length=64), nullable=False),
        sa.Column("computed_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["aircraft_id"], ["aircraft.id"]),
        sa.ForeignKeyConstraint(["directive_id"], ["airworthiness_directives.id"]),
        sa.ForeignKeyConstraint(["extraction_id"], ["ad_extractions.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "aircraft_id",
            "directive_id",
            "algorithm_name",
            "algorithm_version",
            "input_hash",
            name="uq_ad_match_result_replay",
        ),
    )
    op.create_index(op.f("ix_ad_match_results_aircraft_id"), "ad_match_results", ["aircraft_id"])
    op.create_index(op.f("ix_ad_match_results_algorithm_name"), "ad_match_results", ["algorithm_name"])
    op.create_index(op.f("ix_ad_match_results_directive_id"), "ad_match_results", ["directive_id"])
    op.create_index(op.f("ix_ad_match_results_extraction_id"), "ad_match_results", ["extraction_id"])
    op.create_index(op.f("ix_ad_match_results_input_hash"), "ad_match_results", ["input_hash"])
    op.create_index(op.f("ix_ad_match_results_match_type"), "ad_match_results", ["match_type"])
    op.create_index(op.f("ix_ad_match_results_status"), "ad_match_results", ["status"])

    op.create_table(
        "ad_match_evidence",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("match_result_id", sa.String(length=36), nullable=False),
        sa.Column("logbook_entry_id", sa.String(length=36), nullable=False),
        sa.Column("evidence_type", sa.String(length=64), nullable=False),
        sa.Column("field_name", sa.String(length=128), nullable=True),
        sa.Column("matched_text", sa.Text(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("rationale", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["logbook_entry_id"], ["logbook_entries.id"]),
        sa.ForeignKeyConstraint(["match_result_id"], ["ad_match_results.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_ad_match_evidence_logbook_entry_id"), "ad_match_evidence", ["logbook_entry_id"])
    op.create_index(op.f("ix_ad_match_evidence_match_result_id"), "ad_match_evidence", ["match_result_id"])

    op.create_table(
        "ad_match_adjudications",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("match_result_id", sa.String(length=36), nullable=False),
        sa.Column("status", sa.String(length=64), nullable=False),
        sa.Column("decision", sa.String(length=64), nullable=True),
        sa.Column("reviewer_user_id", sa.String(length=36), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["match_result_id"], ["ad_match_results.id"]),
        sa.ForeignKeyConstraint(["reviewer_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("match_result_id"),
    )
    op.create_index(op.f("ix_ad_match_adjudications_match_result_id"), "ad_match_adjudications", ["match_result_id"])
    op.create_index(op.f("ix_ad_match_adjudications_reviewer_user_id"), "ad_match_adjudications", ["reviewer_user_id"])
    op.create_index(op.f("ix_ad_match_adjudications_status"), "ad_match_adjudications", ["status"])


def downgrade() -> None:
    op.drop_index(op.f("ix_ad_match_adjudications_status"), table_name="ad_match_adjudications")
    op.drop_index(op.f("ix_ad_match_adjudications_reviewer_user_id"), table_name="ad_match_adjudications")
    op.drop_index(op.f("ix_ad_match_adjudications_match_result_id"), table_name="ad_match_adjudications")
    op.drop_table("ad_match_adjudications")

    op.drop_index(op.f("ix_ad_match_evidence_match_result_id"), table_name="ad_match_evidence")
    op.drop_index(op.f("ix_ad_match_evidence_logbook_entry_id"), table_name="ad_match_evidence")
    op.drop_table("ad_match_evidence")

    op.drop_index(op.f("ix_ad_match_results_status"), table_name="ad_match_results")
    op.drop_index(op.f("ix_ad_match_results_match_type"), table_name="ad_match_results")
    op.drop_index(op.f("ix_ad_match_results_input_hash"), table_name="ad_match_results")
    op.drop_index(op.f("ix_ad_match_results_extraction_id"), table_name="ad_match_results")
    op.drop_index(op.f("ix_ad_match_results_directive_id"), table_name="ad_match_results")
    op.drop_index(op.f("ix_ad_match_results_algorithm_name"), table_name="ad_match_results")
    op.drop_index(op.f("ix_ad_match_results_aircraft_id"), table_name="ad_match_results")
    op.drop_table("ad_match_results")
