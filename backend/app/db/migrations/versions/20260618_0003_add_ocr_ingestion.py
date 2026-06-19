"""add ocr ingestion tables

Revision ID: 20260618_0003
Revises: 20260617_0002
Create Date: 2026-06-18
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20260618_0003"
down_revision: Union[str, None] = "20260617_0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "ingestion_jobs",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("upload_id", sa.String(length=36), nullable=False),
        sa.Column("aircraft_id", sa.String(length=36), nullable=False),
        sa.Column("created_by_user_id", sa.String(length=36), nullable=False),
        sa.Column("status", sa.String(length=64), nullable=False),
        sa.Column("page_extraction_status", sa.String(length=64), nullable=False),
        sa.Column("ocr_status", sa.String(length=64), nullable=False),
        sa.Column("verification_status", sa.String(length=64), nullable=False),
        sa.Column("entry_extraction_status", sa.String(length=64), nullable=False),
        sa.Column("logbook_section_key", sa.String(length=64), nullable=True),
        sa.Column("error_code", sa.String(length=128), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["aircraft_id"], ["aircraft.id"]),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["upload_id"], ["uploads.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_ingestion_jobs_aircraft_id"), "ingestion_jobs", ["aircraft_id"])
    op.create_index(op.f("ix_ingestion_jobs_created_by_user_id"), "ingestion_jobs", ["created_by_user_id"])
    op.create_index(op.f("ix_ingestion_jobs_upload_id"), "ingestion_jobs", ["upload_id"])

    op.create_table(
        "ingestion_pages",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("ingestion_job_id", sa.String(length=36), nullable=False),
        sa.Column("upload_id", sa.String(length=36), nullable=False),
        sa.Column("source_page_number", sa.Integer(), nullable=False),
        sa.Column("current_page_order", sa.Integer(), nullable=False),
        sa.Column("page_label", sa.String(length=128), nullable=True),
        sa.Column("image_storage_backend", sa.String(length=64), nullable=True),
        sa.Column("image_storage_key", sa.String(length=1024), nullable=True),
        sa.Column("width_px", sa.Integer(), nullable=True),
        sa.Column("height_px", sa.Integer(), nullable=True),
        sa.Column("rotation_degrees", sa.Float(), nullable=True),
        sa.Column("extraction_confidence", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["ingestion_job_id"], ["ingestion_jobs.id"]),
        sa.ForeignKeyConstraint(["upload_id"], ["uploads.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("ingestion_job_id", "source_page_number", name="uq_ingestion_page_source"),
    )
    op.create_index(op.f("ix_ingestion_pages_ingestion_job_id"), "ingestion_pages", ["ingestion_job_id"])
    op.create_index(op.f("ix_ingestion_pages_upload_id"), "ingestion_pages", ["upload_id"])

    op.create_table(
        "ocr_runs",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("ingestion_job_id", sa.String(length=36), nullable=False),
        sa.Column("provider_name", sa.String(length=128), nullable=False),
        sa.Column("provider_version", sa.String(length=128), nullable=False),
        sa.Column("configuration_hash", sa.String(length=128), nullable=False),
        sa.Column("status", sa.String(length=64), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["ingestion_job_id"], ["ingestion_jobs.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_ocr_runs_ingestion_job_id"), "ocr_runs", ["ingestion_job_id"])

    op.create_table(
        "page_verifications",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("ingestion_job_id", sa.String(length=36), nullable=False),
        sa.Column("verified_by_user_id", sa.String(length=36), nullable=False),
        sa.Column("is_order_confirmed", sa.Boolean(), nullable=False),
        sa.Column("is_complete", sa.Boolean(), nullable=False),
        sa.Column("missing_or_uncertain_notes", sa.Text(), nullable=True),
        sa.Column("page_order_snapshot", sa.JSON(), nullable=True),
        sa.Column("verified_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["ingestion_job_id"], ["ingestion_jobs.id"]),
        sa.ForeignKeyConstraint(["verified_by_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_page_verifications_ingestion_job_id"), "page_verifications", ["ingestion_job_id"])
    op.create_index(op.f("ix_page_verifications_verified_by_user_id"), "page_verifications", ["verified_by_user_id"])

    op.create_table(
        "ocr_text_spans",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("ocr_run_id", sa.String(length=36), nullable=False),
        sa.Column("ingestion_page_id", sa.String(length=36), nullable=False),
        sa.Column("provider_block_id", sa.String(length=255), nullable=True),
        sa.Column("span_type", sa.String(length=64), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("confidence_scale", sa.String(length=32), nullable=False),
        sa.Column("bbox_left", sa.Float(), nullable=True),
        sa.Column("bbox_top", sa.Float(), nullable=True),
        sa.Column("bbox_width", sa.Float(), nullable=True),
        sa.Column("bbox_height", sa.Float(), nullable=True),
        sa.Column("bbox_units", sa.String(length=32), nullable=False),
        sa.Column("polygon", sa.JSON(), nullable=True),
        sa.Column("rotation_degrees", sa.Float(), nullable=True),
        sa.Column("reading_order", sa.Integer(), nullable=False),
        sa.Column("relationships", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["ingestion_page_id"], ["ingestion_pages.id"]),
        sa.ForeignKeyConstraint(["ocr_run_id"], ["ocr_runs.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_ocr_text_spans_ingestion_page_id"), "ocr_text_spans", ["ingestion_page_id"])
    op.create_index(op.f("ix_ocr_text_spans_ocr_run_id"), "ocr_text_spans", ["ocr_run_id"])

    op.create_table(
        "ocr_corrections",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("ingestion_job_id", sa.String(length=36), nullable=False),
        sa.Column("ingestion_page_id", sa.String(length=36), nullable=False),
        sa.Column("ocr_text_span_id", sa.String(length=36), nullable=False),
        sa.Column("corrected_by_user_id", sa.String(length=36), nullable=False),
        sa.Column("original_text", sa.Text(), nullable=False),
        sa.Column("corrected_text", sa.Text(), nullable=False),
        sa.Column("original_confidence", sa.Float(), nullable=True),
        sa.Column("correction_reason", sa.String(length=64), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["corrected_by_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["ingestion_job_id"], ["ingestion_jobs.id"]),
        sa.ForeignKeyConstraint(["ingestion_page_id"], ["ingestion_pages.id"]),
        sa.ForeignKeyConstraint(["ocr_text_span_id"], ["ocr_text_spans.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_ocr_corrections_corrected_by_user_id"), "ocr_corrections", ["corrected_by_user_id"])
    op.create_index(op.f("ix_ocr_corrections_ingestion_job_id"), "ocr_corrections", ["ingestion_job_id"])
    op.create_index(op.f("ix_ocr_corrections_ingestion_page_id"), "ocr_corrections", ["ingestion_page_id"])
    op.create_index(op.f("ix_ocr_corrections_ocr_text_span_id"), "ocr_corrections", ["ocr_text_span_id"])

    op.create_table(
        "logbook_entry_evidence",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("logbook_entry_id", sa.String(length=36), nullable=False),
        sa.Column("upload_id", sa.String(length=36), nullable=False),
        sa.Column("ingestion_job_id", sa.String(length=36), nullable=False),
        sa.Column("ingestion_page_id", sa.String(length=36), nullable=True),
        sa.Column("ocr_text_span_id", sa.String(length=36), nullable=True),
        sa.Column("ocr_correction_id", sa.String(length=36), nullable=True),
        sa.Column("evidence_type", sa.String(length=64), nullable=False),
        sa.Column("field_name", sa.String(length=128), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("extraction_provider_name", sa.String(length=128), nullable=True),
        sa.Column("extraction_provider_version", sa.String(length=128), nullable=True),
        sa.Column("extraction_schema_version", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["ingestion_job_id"], ["ingestion_jobs.id"]),
        sa.ForeignKeyConstraint(["ingestion_page_id"], ["ingestion_pages.id"]),
        sa.ForeignKeyConstraint(["logbook_entry_id"], ["logbook_entries.id"]),
        sa.ForeignKeyConstraint(["ocr_correction_id"], ["ocr_corrections.id"]),
        sa.ForeignKeyConstraint(["ocr_text_span_id"], ["ocr_text_spans.id"]),
        sa.ForeignKeyConstraint(["upload_id"], ["uploads.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_logbook_entry_evidence_ingestion_job_id"), "logbook_entry_evidence", ["ingestion_job_id"])
    op.create_index(op.f("ix_logbook_entry_evidence_ingestion_page_id"), "logbook_entry_evidence", ["ingestion_page_id"])
    op.create_index(op.f("ix_logbook_entry_evidence_logbook_entry_id"), "logbook_entry_evidence", ["logbook_entry_id"])
    op.create_index(op.f("ix_logbook_entry_evidence_ocr_correction_id"), "logbook_entry_evidence", ["ocr_correction_id"])
    op.create_index(op.f("ix_logbook_entry_evidence_ocr_text_span_id"), "logbook_entry_evidence", ["ocr_text_span_id"])
    op.create_index(op.f("ix_logbook_entry_evidence_upload_id"), "logbook_entry_evidence", ["upload_id"])


def downgrade() -> None:
    op.drop_index(op.f("ix_logbook_entry_evidence_upload_id"), table_name="logbook_entry_evidence")
    op.drop_index(op.f("ix_logbook_entry_evidence_ocr_text_span_id"), table_name="logbook_entry_evidence")
    op.drop_index(op.f("ix_logbook_entry_evidence_ocr_correction_id"), table_name="logbook_entry_evidence")
    op.drop_index(op.f("ix_logbook_entry_evidence_logbook_entry_id"), table_name="logbook_entry_evidence")
    op.drop_index(op.f("ix_logbook_entry_evidence_ingestion_page_id"), table_name="logbook_entry_evidence")
    op.drop_index(op.f("ix_logbook_entry_evidence_ingestion_job_id"), table_name="logbook_entry_evidence")
    op.drop_table("logbook_entry_evidence")

    op.drop_index(op.f("ix_ocr_corrections_ocr_text_span_id"), table_name="ocr_corrections")
    op.drop_index(op.f("ix_ocr_corrections_ingestion_page_id"), table_name="ocr_corrections")
    op.drop_index(op.f("ix_ocr_corrections_ingestion_job_id"), table_name="ocr_corrections")
    op.drop_index(op.f("ix_ocr_corrections_corrected_by_user_id"), table_name="ocr_corrections")
    op.drop_table("ocr_corrections")

    op.drop_index(op.f("ix_ocr_text_spans_ocr_run_id"), table_name="ocr_text_spans")
    op.drop_index(op.f("ix_ocr_text_spans_ingestion_page_id"), table_name="ocr_text_spans")
    op.drop_table("ocr_text_spans")

    op.drop_index(op.f("ix_page_verifications_verified_by_user_id"), table_name="page_verifications")
    op.drop_index(op.f("ix_page_verifications_ingestion_job_id"), table_name="page_verifications")
    op.drop_table("page_verifications")

    op.drop_index(op.f("ix_ocr_runs_ingestion_job_id"), table_name="ocr_runs")
    op.drop_table("ocr_runs")

    op.drop_index(op.f("ix_ingestion_pages_upload_id"), table_name="ingestion_pages")
    op.drop_index(op.f("ix_ingestion_pages_ingestion_job_id"), table_name="ingestion_pages")
    op.drop_table("ingestion_pages")

    op.drop_index(op.f("ix_ingestion_jobs_upload_id"), table_name="ingestion_jobs")
    op.drop_index(op.f("ix_ingestion_jobs_created_by_user_id"), table_name="ingestion_jobs")
    op.drop_index(op.f("ix_ingestion_jobs_aircraft_id"), table_name="ingestion_jobs")
    op.drop_table("ingestion_jobs")
