"""bind AD materialization to signed extraction and repair AMOC provenance

Revision ID: 20260823_0024
Revises: 20260822_0023
Create Date: 2026-08-23
"""

from alembic import op
import sqlalchemy as sa


revision = "20260823_0024"
down_revision = "20260822_0023"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "ad_target_applicability",
        sa.Column("source_extraction_id", sa.String(length=36), nullable=True),
    )
    op.create_foreign_key(
        "fk_ad_target_applicability_source_extraction",
        "ad_target_applicability",
        "ad_extractions",
        ["source_extraction_id"],
        ["id"],
    )
    op.create_index(
        op.f("ix_ad_target_applicability_source_extraction_id"),
        "ad_target_applicability",
        ["source_extraction_id"],
    )
    op.execute("""
        UPDATE ad_target_applicability
        SET status = 'superseded'
        WHERE applicability_basis = 'extraction'
          AND status = 'current'
          AND source_extraction_id IS NULL
    """)
    op.drop_index(
        "uq_ad_target_applicability_identity_v2",
        table_name="ad_target_applicability",
    )
    op.execute("""
        CREATE UNIQUE INDEX uq_ad_target_applicability_identity_v3
        ON ad_target_applicability (
            directive_id,
            target_id,
            COALESCE(source_publication_id, ''),
            applicability_basis,
            COALESCE(applicability_group_key, ''),
            COALESCE(source_extraction_id, '')
        )
    """)

    op.create_table(
        "ad_extraction_review_decisions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("review_id", sa.String(length=36), nullable=False),
        sa.Column("extraction_id", sa.String(length=36), nullable=False),
        sa.Column("decision", sa.String(length=64), nullable=False),
        sa.Column("output_hash", sa.String(length=64), nullable=False),
        sa.Column("decision_output", sa.JSON(), nullable=True),
        sa.Column("actor_user_id", sa.String(length=36), nullable=True),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["review_id"], ["ad_extraction_reviews.id"]),
        sa.ForeignKeyConstraint(["extraction_id"], ["ad_extractions.id"]),
        sa.ForeignKeyConstraint(["actor_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in (
        "review_id", "extraction_id", "decision", "output_hash",
        "actor_user_id", "event_type",
    ):
        op.create_index(
            op.f(f"ix_ad_extraction_review_decisions_{column}"),
            "ad_extraction_review_decisions",
            [column],
        )

    op.create_table(
        "ad_match_due_state_links",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("match_result_id", sa.String(length=36), nullable=False),
        sa.Column("due_state_id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["match_result_id"], ["ad_match_results.id"]),
        sa.ForeignKeyConstraint(["due_state_id"], ["aircraft_ad_due_states.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("match_result_id", "due_state_id", name="uq_ad_match_due_state_link"),
    )
    op.create_index(
        op.f("ix_ad_match_due_state_links_match_result_id"),
        "ad_match_due_state_links",
        ["match_result_id"],
    )
    op.create_index(
        op.f("ix_ad_match_due_state_links_due_state_id"),
        "ad_match_due_state_links",
        ["due_state_id"],
    )

    # Revision 0023 previously added an empty AMOC envelope without recording
    # which rows it touched. Conservatively reopen every pre-origin v3 row.
    op.execute("""
        INSERT INTO ad_extraction_review_decisions (
            id, review_id, extraction_id, decision, output_hash,
            decision_output, actor_user_id, decided_at, notes, event_type,
            metadata_json
        )
        SELECT
            'ard_' || md5(random()::text || clock_timestamp()::text || review.id),
            review.id,
            extraction.id,
            COALESCE(review.decision, review.status, 'migration_repair'),
            encode(sha256(convert_to(COALESCE(review.decision_output::jsonb, 'null'::jsonb)::text, 'UTF8')), 'hex'),
            review.decision_output,
            review.reviewer_user_id,
            COALESCE(review.reviewed_at, now()),
            review.notes,
            'migration_repair_snapshot',
            json_build_object(
                'reason', 'ambiguous_amoc_envelope_from_0023',
                'extractionOutputHash', encode(sha256(convert_to(extraction.output::jsonb::text, 'UTF8')), 'hex'),
                'extractionOutput', extraction.output,
                'proposedOutputHash', encode(sha256(convert_to(review.proposed_output::jsonb::text, 'UTF8')), 'hex'),
                'proposedOutput', review.proposed_output,
                'decisionOutputHash', encode(sha256(convert_to(COALESCE(review.decision_output::jsonb, 'null'::jsonb)::text, 'UTF8')), 'hex'),
                'repairedAt', now(),
                'repairActor', 'alembic:20260823_0024'
            )
        FROM ad_extraction_reviews AS review
        JOIN ad_extractions AS extraction ON extraction.id = review.extraction_id
        WHERE extraction.schema_version = 'ad_extraction_v3'
          AND NOT (COALESCE(extraction.raw_response::jsonb, '{}'::jsonb)
                  ? 'amocEnvelopeOrigin')
    """)
    op.execute("""
        UPDATE ad_extraction_reviews AS review
        SET proposed_output = CASE
                WHEN review.proposed_output::jsonb -> 'amocProvisions' = '[]'::jsonb
                THEN (review.proposed_output::jsonb - 'amocProvisions')::json
                ELSE review.proposed_output
            END,
            decision_output = NULL,
            decision = NULL,
            reviewer_user_id = NULL,
            reviewed_at = NULL,
            status = 'pending',
            notes = CASE
                WHEN COALESCE(review.notes, '') = ''
                THEN 'Reopened by migration 0024: AMOC envelope provenance is ambiguous.'
                ELSE review.notes || E'\nReopened by migration 0024: AMOC envelope provenance is ambiguous.'
            END
        FROM ad_extractions AS extraction
        WHERE extraction.id = review.extraction_id
          AND extraction.schema_version = 'ad_extraction_v3'
          AND NOT (COALESCE(extraction.raw_response::jsonb, '{}'::jsonb)
                  ? 'amocEnvelopeOrigin')
    """)
    op.execute("""
        UPDATE ad_extractions
        SET output = CASE
                WHEN output::jsonb -> 'amocProvisions' = '[]'::jsonb
                THEN (output::jsonb - 'amocProvisions')::json
                ELSE output
            END,
            status = 'needs_review',
            raw_response = (
                COALESCE(raw_response::jsonb, '{}'::jsonb)
                || jsonb_build_object(
                    'amocEnvelopeOrigin', 'migration_repair_pending',
                    'amocEnvelopeRepair', jsonb_build_object(
                        'reason', 'ambiguous_amoc_envelope_from_0023',
                        'repairedAt', now()
                    )
                )
            )::json
        WHERE schema_version = 'ad_extraction_v3'
          AND NOT (COALESCE(raw_response::jsonb, '{}'::jsonb)
                  ? 'amocEnvelopeOrigin')
    """)
    op.execute("""
        UPDATE airworthiness_directives AS directive
        SET review_status = 'pending',
            extraction_status = 'needs_review',
            approved_at = NULL
        WHERE EXISTS (
            SELECT 1 FROM ad_extractions AS extraction
            WHERE extraction.directive_id = directive.id
              AND extraction.schema_version = 'ad_extraction_v3'
              AND extraction.raw_response::jsonb ->> 'amocEnvelopeOrigin'
                    = 'migration_repair_pending'
        )
    """)


def downgrade() -> None:
    dependent = op.get_bind().execute(sa.text("""
        SELECT 1
        WHERE EXISTS (SELECT 1 FROM ad_extraction_review_decisions LIMIT 1)
           OR EXISTS (SELECT 1 FROM ad_match_due_state_links LIMIT 1)
           OR EXISTS (
                SELECT 1 FROM ad_target_applicability
                WHERE source_extraction_id IS NOT NULL
                LIMIT 1
           )
           OR EXISTS (
                SELECT 1 FROM ad_extractions
                WHERE schema_version = 'ad_extraction_v3'
                LIMIT 1
           )
    """)).first()
    if dependent is not None:
        raise RuntimeError(
            "Revision 0024 contains signed AD provenance and is irreversible; "
            "restore a verified pre-0024 backup with the matching application version"
        )

    op.drop_index(
        op.f("ix_ad_match_due_state_links_due_state_id"),
        table_name="ad_match_due_state_links",
    )
    op.drop_index(
        op.f("ix_ad_match_due_state_links_match_result_id"),
        table_name="ad_match_due_state_links",
    )
    op.drop_table("ad_match_due_state_links")
    for column in reversed((
        "review_id", "extraction_id", "decision", "output_hash",
        "actor_user_id", "event_type",
    )):
        op.drop_index(
            op.f(f"ix_ad_extraction_review_decisions_{column}"),
            table_name="ad_extraction_review_decisions",
        )
    op.drop_table("ad_extraction_review_decisions")
    op.drop_index(
        "uq_ad_target_applicability_identity_v3",
        table_name="ad_target_applicability",
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
    op.drop_index(
        op.f("ix_ad_target_applicability_source_extraction_id"),
        table_name="ad_target_applicability",
    )
    op.drop_constraint(
        "fk_ad_target_applicability_source_extraction",
        "ad_target_applicability",
        type_="foreignkey",
    )
    op.drop_column("ad_target_applicability", "source_extraction_id")
