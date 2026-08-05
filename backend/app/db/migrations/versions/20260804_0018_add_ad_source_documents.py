"""add provider-neutral AD source documents

Revision ID: 20260804_0018
Revises: 20260730_0017
Create Date: 2026-08-04
"""

from alembic import op
import sqlalchemy as sa


revision = "20260804_0018"
down_revision = "20260730_0017"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "ad_source_documents",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("source_snapshot_id", sa.String(length=36), nullable=True),
        sa.Column("source_system", sa.String(length=64), nullable=False),
        sa.Column("source_type", sa.String(length=64), nullable=False),
        sa.Column("source_identifier", sa.String(length=255), nullable=False),
        sa.Column("parent_source_identifier", sa.String(length=255), nullable=True),
        sa.Column("source_url", sa.String(length=1024), nullable=True),
        sa.Column("storage_backend", sa.String(length=64), nullable=False),
        sa.Column("storage_key", sa.String(length=1024), nullable=False),
        sa.Column("media_type", sa.String(length=255), nullable=True),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column("storage_bytes", sa.BigInteger(), nullable=False),
        sa.Column("captured_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("publication_date", sa.Date(), nullable=True),
        sa.Column("status", sa.String(length=64), nullable=False),
        sa.Column("parser_name", sa.String(length=128), nullable=True),
        sa.Column("parser_version", sa.String(length=64), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["source_snapshot_id"], ["ad_source_snapshots.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "source_system",
            "source_type",
            "source_identifier",
            "content_hash",
            name="uq_ad_source_document_version",
        ),
    )
    for column in (
        "source_snapshot_id",
        "source_system",
        "source_type",
        "source_identifier",
        "parent_source_identifier",
        "content_hash",
        "publication_date",
        "status",
    ):
        op.create_index(
            op.f(f"ix_ad_source_documents_{column}"),
            "ad_source_documents",
            [column],
        )

    op.add_column(
        "ad_publications",
        sa.Column("source_document_id", sa.String(length=36), nullable=True),
    )
    op.create_foreign_key(
        "fk_ad_publications_source_document_id_ad_source_documents",
        "ad_publications",
        "ad_source_documents",
        ["source_document_id"],
        ["id"],
    )
    op.create_index(
        op.f("ix_ad_publications_source_document_id"),
        "ad_publications",
        ["source_document_id"],
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_ad_publications_source_document_id"),
        table_name="ad_publications",
    )
    op.drop_constraint(
        "fk_ad_publications_source_document_id_ad_source_documents",
        "ad_publications",
        type_="foreignkey",
    )
    op.drop_column("ad_publications", "source_document_id")
    op.drop_table("ad_source_documents")
