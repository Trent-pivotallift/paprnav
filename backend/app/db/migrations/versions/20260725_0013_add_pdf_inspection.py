"""add provider-neutral PDF inspection metadata

Revision ID: 20260725_0013
Revises: 20260725_0012
Create Date: 2026-07-25
"""

from alembic import op
import sqlalchemy as sa


revision = "20260725_0013"
down_revision = "20260725_0012"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("ingestion_jobs", sa.Column("document_inspection", sa.JSON(), nullable=True))
    op.add_column("ingestion_pages", sa.Column("inspection_status", sa.String(length=64), nullable=True))
    op.add_column("ingestion_pages", sa.Column("source_page_fingerprint", sa.String(length=64), nullable=True))
    op.add_column("ingestion_pages", sa.Column("canonical_image_sha256", sa.String(length=64), nullable=True))
    op.add_column("ingestion_pages", sa.Column("render_profile", sa.String(length=64), nullable=True))
    op.add_column("ingestion_pages", sa.Column("render_metadata", sa.JSON(), nullable=True))
    op.add_column("ingestion_pages", sa.Column("page_classification", sa.JSON(), nullable=True))
    op.add_column("ingestion_pages", sa.Column("native_text_evaluation", sa.JSON(), nullable=True))
    op.add_column("ingestion_pages", sa.Column("extraction_plan", sa.JSON(), nullable=True))
    op.create_index(
        op.f("ix_ingestion_pages_source_page_fingerprint"),
        "ingestion_pages",
        ["source_page_fingerprint"],
        unique=False,
    )
    op.create_index(
        op.f("ix_ingestion_pages_canonical_image_sha256"),
        "ingestion_pages",
        ["canonical_image_sha256"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_ingestion_pages_canonical_image_sha256"), table_name="ingestion_pages")
    op.drop_index(op.f("ix_ingestion_pages_source_page_fingerprint"), table_name="ingestion_pages")
    op.drop_column("ingestion_pages", "extraction_plan")
    op.drop_column("ingestion_pages", "native_text_evaluation")
    op.drop_column("ingestion_pages", "page_classification")
    op.drop_column("ingestion_pages", "render_metadata")
    op.drop_column("ingestion_pages", "render_profile")
    op.drop_column("ingestion_pages", "canonical_image_sha256")
    op.drop_column("ingestion_pages", "source_page_fingerprint")
    op.drop_column("ingestion_pages", "inspection_status")
    op.drop_column("ingestion_jobs", "document_inspection")
