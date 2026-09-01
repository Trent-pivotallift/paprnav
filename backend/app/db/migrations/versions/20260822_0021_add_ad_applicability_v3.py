"""add source-faithful AD applicability v3 persistence

Revision ID: 20260822_0021
Revises: 20260809_0020
Create Date: 2026-08-22
"""

from alembic import op
import sqlalchemy as sa


revision = "20260822_0021"
down_revision = "20260809_0020"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_constraint(
        "uq_ad_target_applicability",
        "ad_target_applicability",
        type_="unique",
    )
    op.add_column(
        "ad_target_applicability",
        sa.Column("applicability_group_key", sa.String(length=128), nullable=True),
    )
    op.add_column(
        "ad_target_applicability",
        sa.Column("source_identity", sa.JSON(), nullable=True),
    )
    op.add_column(
        "ad_target_applicability",
        sa.Column("equipment_conditions", sa.JSON(), nullable=True),
    )
    op.add_column(
        "ad_target_applicability",
        sa.Column("source_payload", sa.JSON(), nullable=True),
    )
    op.create_index(
        op.f("ix_ad_target_applicability_applicability_group_key"),
        "ad_target_applicability",
        ["applicability_group_key"],
    )
    op.create_unique_constraint(
        "uq_ad_target_applicability",
        "ad_target_applicability",
        [
            "directive_id",
            "target_id",
            "source_publication_id",
            "applicability_basis",
            "applicability_group_key",
        ],
    )


def downgrade() -> None:
    v3_row = op.get_bind().execute(sa.text("""
        SELECT 1 FROM ad_extractions
        WHERE schema_version = 'ad_extraction_v3'
        LIMIT 1
    """)).first()
    if v3_row is not None:
        raise RuntimeError(
            "Revision 0021 contains v3 regulatory data and is irreversible; "
            "restore a verified pre-0021 backup with the matching application version"
        )
    op.drop_constraint(
        "uq_ad_target_applicability",
        "ad_target_applicability",
        type_="unique",
    )
    op.drop_index(
        op.f("ix_ad_target_applicability_applicability_group_key"),
        table_name="ad_target_applicability",
    )
    op.drop_column("ad_target_applicability", "source_payload")
    op.drop_column("ad_target_applicability", "equipment_conditions")
    op.drop_column("ad_target_applicability", "source_identity")
    op.drop_column("ad_target_applicability", "applicability_group_key")
    op.create_unique_constraint(
        "uq_ad_target_applicability",
        "ad_target_applicability",
        ["directive_id", "target_id", "source_publication_id", "applicability_basis"],
    )
