"""add logical page regions and stage results

Revision ID: 20260726_0014
Revises: 20260725_0013
Create Date: 2026-07-26
"""

from alembic import op
import sqlalchemy as sa


revision = "20260726_0014"
down_revision = "20260725_0013"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("ingestion_pages", sa.Column("stage_results", sa.JSON(), nullable=True))
    op.create_table(
        "logical_page_regions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("ingestion_page_id", sa.String(length=36), nullable=False),
        sa.Column("region_key", sa.String(length=64), nullable=False),
        sa.Column("region_type", sa.String(length=64), nullable=False),
        sa.Column("bbox_left", sa.Float(), nullable=False),
        sa.Column("bbox_top", sa.Float(), nullable=False),
        sa.Column("bbox_width", sa.Float(), nullable=False),
        sa.Column("bbox_height", sa.Float(), nullable=False),
        sa.Column("bbox_units", sa.String(length=32), nullable=False),
        sa.Column("reading_order", sa.Integer(), nullable=False),
        sa.Column("classification", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["ingestion_page_id"], ["ingestion_pages.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("ingestion_page_id", "region_key", name="uq_logical_page_region_key"),
    )
    op.create_index(
        op.f("ix_logical_page_regions_ingestion_page_id"),
        "logical_page_regions",
        ["ingestion_page_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_logical_page_regions_ingestion_page_id"), table_name="logical_page_regions")
    op.drop_table("logical_page_regions")
    op.drop_column("ingestion_pages", "stage_results")
