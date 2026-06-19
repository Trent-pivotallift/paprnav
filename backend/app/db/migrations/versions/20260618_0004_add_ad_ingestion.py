"""add ad ingestion tables

Revision ID: 20260618_0004
Revises: 20260618_0003
Create Date: 2026-06-18
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20260618_0004"
down_revision: Union[str, None] = "20260618_0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "ad_discovery_records",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("federal_register_document_number", sa.String(length=64), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("document_type", sa.String(length=64), nullable=True),
        sa.Column("abstract", sa.Text(), nullable=True),
        sa.Column("publication_date", sa.Date(), nullable=True),
        sa.Column("effective_date", sa.Date(), nullable=True),
        sa.Column("html_url", sa.String(length=1024), nullable=True),
        sa.Column("pdf_url", sa.String(length=1024), nullable=True),
        sa.Column("public_inspection_pdf_url", sa.String(length=1024), nullable=True),
        sa.Column("agency_names", sa.JSON(), nullable=True),
        sa.Column("excerpts", sa.Text(), nullable=True),
        sa.Column("api_snapshot", sa.JSON(), nullable=False),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column("classification", sa.String(length=64), nullable=False),
        sa.Column("classification_confidence", sa.Float(), nullable=False),
        sa.Column("classification_reason", sa.Text(), nullable=False),
        sa.Column("classifier_name", sa.String(length=128), nullable=False),
        sa.Column("classifier_version", sa.String(length=128), nullable=False),
        sa.Column("classified_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_ad_discovery_records_classification"),
        "ad_discovery_records",
        ["classification"],
    )
    op.create_index(op.f("ix_ad_discovery_records_content_hash"), "ad_discovery_records", ["content_hash"])
    op.create_index(
        op.f("ix_ad_discovery_records_federal_register_document_number"),
        "ad_discovery_records",
        ["federal_register_document_number"],
        unique=True,
    )
    op.create_index(op.f("ix_ad_discovery_records_publication_date"), "ad_discovery_records", ["publication_date"])

    op.create_table(
        "airworthiness_directives",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("discovery_record_id", sa.String(length=36), nullable=False),
        sa.Column("ad_number", sa.String(length=64), nullable=True),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=64), nullable=False),
        sa.Column("source_content_hash", sa.String(length=64), nullable=False),
        sa.Column("extraction_status", sa.String(length=64), nullable=False),
        sa.Column("review_status", sa.String(length=64), nullable=False),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["discovery_record_id"], ["ad_discovery_records.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("discovery_record_id"),
    )
    op.create_index(op.f("ix_airworthiness_directives_ad_number"), "airworthiness_directives", ["ad_number"])
    op.create_index(
        op.f("ix_airworthiness_directives_discovery_record_id"),
        "airworthiness_directives",
        ["discovery_record_id"],
    )
    op.create_index(
        op.f("ix_airworthiness_directives_extraction_status"),
        "airworthiness_directives",
        ["extraction_status"],
    )
    op.create_index(op.f("ix_airworthiness_directives_review_status"), "airworthiness_directives", ["review_status"])
    op.create_index(
        op.f("ix_airworthiness_directives_source_content_hash"),
        "airworthiness_directives",
        ["source_content_hash"],
    )
    op.create_index(op.f("ix_airworthiness_directives_status"), "airworthiness_directives", ["status"])

    op.create_table(
        "ad_extractions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("directive_id", sa.String(length=36), nullable=False),
        sa.Column("provider_name", sa.String(length=128), nullable=False),
        sa.Column("provider_version", sa.String(length=128), nullable=False),
        sa.Column("schema_version", sa.String(length=64), nullable=False),
        sa.Column("input_content_hash", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=64), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("output", sa.JSON(), nullable=False),
        sa.Column("citations", sa.JSON(), nullable=True),
        sa.Column("raw_response", sa.JSON(), nullable=True),
        sa.Column("extracted_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["directive_id"], ["airworthiness_directives.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "directive_id",
            "input_content_hash",
            "provider_name",
            "provider_version",
            "schema_version",
            name="uq_ad_extraction_idempotency",
        ),
    )
    op.create_index(op.f("ix_ad_extractions_directive_id"), "ad_extractions", ["directive_id"])
    op.create_index(op.f("ix_ad_extractions_input_content_hash"), "ad_extractions", ["input_content_hash"])
    op.create_index(op.f("ix_ad_extractions_status"), "ad_extractions", ["status"])

    op.create_table(
        "ad_supersessions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("superseding_ad_id", sa.String(length=36), nullable=False),
        sa.Column("superseded_ad_id", sa.String(length=36), nullable=False),
        sa.Column("relationship_type", sa.String(length=64), nullable=False),
        sa.Column("evidence_text", sa.Text(), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["superseded_ad_id"], ["airworthiness_directives.id"]),
        sa.ForeignKeyConstraint(["superseding_ad_id"], ["airworthiness_directives.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "superseding_ad_id",
            "superseded_ad_id",
            "relationship_type",
            name="uq_ad_supersession_edge",
        ),
    )
    op.create_index(op.f("ix_ad_supersessions_superseded_ad_id"), "ad_supersessions", ["superseded_ad_id"])
    op.create_index(op.f("ix_ad_supersessions_superseding_ad_id"), "ad_supersessions", ["superseding_ad_id"])

    op.create_table(
        "ad_extraction_reviews",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("extraction_id", sa.String(length=36), nullable=False),
        sa.Column("status", sa.String(length=64), nullable=False),
        sa.Column("proposed_output", sa.JSON(), nullable=False),
        sa.Column("decision_output", sa.JSON(), nullable=True),
        sa.Column("decision", sa.String(length=64), nullable=True),
        sa.Column("reviewer_user_id", sa.String(length=36), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["extraction_id"], ["ad_extractions.id"]),
        sa.ForeignKeyConstraint(["reviewer_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("extraction_id"),
    )
    op.create_index(op.f("ix_ad_extraction_reviews_extraction_id"), "ad_extraction_reviews", ["extraction_id"])
    op.create_index(op.f("ix_ad_extraction_reviews_reviewer_user_id"), "ad_extraction_reviews", ["reviewer_user_id"])
    op.create_index(op.f("ix_ad_extraction_reviews_status"), "ad_extraction_reviews", ["status"])


def downgrade() -> None:
    op.drop_index(op.f("ix_ad_extraction_reviews_status"), table_name="ad_extraction_reviews")
    op.drop_index(op.f("ix_ad_extraction_reviews_reviewer_user_id"), table_name="ad_extraction_reviews")
    op.drop_index(op.f("ix_ad_extraction_reviews_extraction_id"), table_name="ad_extraction_reviews")
    op.drop_table("ad_extraction_reviews")

    op.drop_index(op.f("ix_ad_supersessions_superseding_ad_id"), table_name="ad_supersessions")
    op.drop_index(op.f("ix_ad_supersessions_superseded_ad_id"), table_name="ad_supersessions")
    op.drop_table("ad_supersessions")

    op.drop_index(op.f("ix_ad_extractions_status"), table_name="ad_extractions")
    op.drop_index(op.f("ix_ad_extractions_input_content_hash"), table_name="ad_extractions")
    op.drop_index(op.f("ix_ad_extractions_directive_id"), table_name="ad_extractions")
    op.drop_table("ad_extractions")

    op.drop_index(op.f("ix_airworthiness_directives_status"), table_name="airworthiness_directives")
    op.drop_index(op.f("ix_airworthiness_directives_source_content_hash"), table_name="airworthiness_directives")
    op.drop_index(op.f("ix_airworthiness_directives_review_status"), table_name="airworthiness_directives")
    op.drop_index(op.f("ix_airworthiness_directives_extraction_status"), table_name="airworthiness_directives")
    op.drop_index(op.f("ix_airworthiness_directives_discovery_record_id"), table_name="airworthiness_directives")
    op.drop_index(op.f("ix_airworthiness_directives_ad_number"), table_name="airworthiness_directives")
    op.drop_table("airworthiness_directives")

    op.drop_index(op.f("ix_ad_discovery_records_publication_date"), table_name="ad_discovery_records")
    op.drop_index(op.f("ix_ad_discovery_records_federal_register_document_number"), table_name="ad_discovery_records")
    op.drop_index(op.f("ix_ad_discovery_records_content_hash"), table_name="ad_discovery_records")
    op.drop_index(op.f("ix_ad_discovery_records_classification"), table_name="ad_discovery_records")
    op.drop_table("ad_discovery_records")
