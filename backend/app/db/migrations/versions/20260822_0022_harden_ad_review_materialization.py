"""harden AD review materialization and AMOC persistence

Revision ID: 20260822_0022
Revises: 20260822_0021
Create Date: 2026-08-22
"""

from alembic import op
import sqlalchemy as sa


revision = "20260822_0022"
down_revision = "20260822_0021"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "ad_compliance_triggers",
        sa.Column(
            "trigger_kind",
            sa.String(length=32),
            nullable=False,
            server_default="recurring",
        ),
    )

    op.create_table(
        "ad_amoc_provisions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("directive_id", sa.String(length=36), nullable=False),
        sa.Column("source_extraction_id", sa.String(length=36), nullable=False),
        sa.Column("provision_hash", sa.String(length=64), nullable=False),
        sa.Column("provision_key", sa.String(length=128), nullable=False),
        sa.Column("authority_text", sa.Text(), nullable=False),
        sa.Column("approving_authority", sa.String(length=512), nullable=True),
        sa.Column("submission_instructions", sa.Text(), nullable=True),
        sa.Column("conditions", sa.JSON(), nullable=False),
        sa.Column("citations", sa.JSON(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("source_payload", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["directive_id"], ["airworthiness_directives.id"]),
        sa.ForeignKeyConstraint(["source_extraction_id"], ["ad_extractions.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("provision_hash"),
    )
    for column in (
        "directive_id", "source_extraction_id", "provision_hash",
        "provision_key", "approving_authority", "status",
    ):
        op.create_index(
            op.f(f"ix_ad_amoc_provisions_{column}"),
            "ad_amoc_provisions",
            [column],
        )

    duplicate = op.get_bind().execute(sa.text("""
        SELECT 1
        FROM ad_target_applicability
        GROUP BY directive_id,
                 target_id,
                 COALESCE(source_publication_id, ''),
                 applicability_basis,
                 COALESCE(applicability_group_key, '')
        HAVING COUNT(*) > 1
        LIMIT 1
    """)).first()
    if duplicate is not None:
        raise RuntimeError(
            "Cannot install NULL-safe AD applicability identity index while duplicate rows exist"
        )
    op.drop_constraint(
        "uq_ad_target_applicability",
        "ad_target_applicability",
        type_="unique",
    )
    op.execute("""
        CREATE UNIQUE INDEX uq_ad_target_applicability_identity_v2
        ON ad_target_applicability (
            directive_id,
            target_id,
            COALESCE(source_publication_id, ''),
            applicability_basis,
            COALESCE(applicability_group_key, '')
        )
    """)


def downgrade() -> None:
    v3_row = op.get_bind().execute(sa.text("""
        SELECT 1 FROM ad_extractions
        WHERE schema_version = 'ad_extraction_v3'
        LIMIT 1
    """)).first()
    if v3_row is not None:
        raise RuntimeError(
            "Revision 0022 contains v3 regulatory data and is irreversible; "
            "restore a verified pre-0022 backup with the matching application version"
        )
    op.drop_index(
        "uq_ad_target_applicability_identity_v2",
        table_name="ad_target_applicability",
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
    for column in reversed((
        "directive_id", "source_extraction_id", "provision_hash",
        "provision_key", "approving_authority", "status",
    )):
        op.drop_index(
            op.f(f"ix_ad_amoc_provisions_{column}"),
            table_name="ad_amoc_provisions",
        )
    op.drop_table("ad_amoc_provisions")
    op.drop_column("ad_compliance_triggers", "trigger_kind")
