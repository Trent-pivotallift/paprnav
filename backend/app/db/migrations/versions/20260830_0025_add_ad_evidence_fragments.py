"""add immutable retained-page evidence fragments

Revision ID: 20260830_0025
Revises: 20260823_0024
Create Date: 2026-08-30
"""

from alembic import op
import sqlalchemy as sa


revision = "20260830_0025"
down_revision = "20260823_0024"
branch_labels = None
depends_on = None


IMMUTABLE_TABLES = (
    "ad_source_page_renditions",
    "ad_source_page_text_versions",
    "ad_evidence_fragments",
    "ad_evidence_fragment_lifecycle_events",
)


def upgrade() -> None:
    op.create_unique_constraint(
        "uq_ad_source_document_id_content_hash",
        "ad_source_documents",
        ["id", "content_hash"],
    )
    op.create_unique_constraint(
        "uq_ad_publication_directive_document",
        "ad_publications",
        ["directive_id", "source_document_id"],
    )
    op.create_table(
        "ad_source_page_renditions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("source_document_id", sa.String(length=36), nullable=False),
        sa.Column("source_content_hash", sa.String(length=64), nullable=False),
        sa.Column("page_number", sa.Integer(), nullable=False),
        sa.Column("renderer_name", sa.String(length=128), nullable=False),
        sa.Column("renderer_version", sa.String(length=128), nullable=False),
        sa.Column("renderer_configuration_hash", sa.String(length=64), nullable=False),
        sa.Column("media_type", sa.String(length=255), nullable=False),
        sa.Column("width_px", sa.Integer(), nullable=False),
        sa.Column("height_px", sa.Integer(), nullable=False),
        sa.Column("storage_backend", sa.String(length=64), nullable=False),
        sa.Column("storage_key", sa.String(length=1024), nullable=False),
        sa.Column("rendition_hash", sa.String(length=64), nullable=False),
        sa.Column("storage_bytes", sa.BigInteger(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("page_number >= 1", name="ck_ad_source_page_rendition_page_number"),
        sa.CheckConstraint("storage_bytes > 0", name="ck_ad_source_page_rendition_storage_bytes"),
        sa.CheckConstraint("width_px > 0 AND height_px > 0", name="ck_ad_source_page_rendition_dimensions"),
        sa.CheckConstraint("length(source_content_hash) = 64", name="ck_ad_source_page_rendition_source_hash"),
        sa.CheckConstraint("length(renderer_configuration_hash) = 64", name="ck_ad_source_page_rendition_config_hash"),
        sa.CheckConstraint("length(rendition_hash) = 64", name="ck_ad_source_page_rendition_hash"),
        sa.ForeignKeyConstraint(
            ["source_document_id", "source_content_hash"],
            ["ad_source_documents.id", "ad_source_documents.content_hash"],
            name="fk_ad_source_page_rendition_document_hash",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "id", "source_document_id", "source_content_hash", "page_number",
            name="uq_ad_source_page_rendition_chain",
        ),
        sa.UniqueConstraint(
            "source_document_id",
            "source_content_hash",
            "page_number",
            "renderer_configuration_hash",
            name="uq_ad_source_page_rendition_identity",
        ),
    )
    for column in (
        "source_document_id", "source_content_hash", "renderer_configuration_hash", "rendition_hash",
    ):
        op.create_index(op.f(f"ix_ad_source_page_renditions_{column}"), "ad_source_page_renditions", [column])

    op.create_table(
        "ad_source_page_text_versions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("rendition_id", sa.String(length=36), nullable=False),
        sa.Column("source_document_id", sa.String(length=36), nullable=False),
        sa.Column("source_content_hash", sa.String(length=64), nullable=False),
        sa.Column("page_number", sa.Integer(), nullable=False),
        sa.Column("extractor_name", sa.String(length=128), nullable=False),
        sa.Column("extractor_version", sa.String(length=128), nullable=False),
        sa.Column("extractor_configuration_hash", sa.String(length=64), nullable=False),
        sa.Column("page_text", sa.Text(), nullable=False),
        sa.Column("text_hash", sa.String(length=64), nullable=False),
        sa.Column("coordinate_map_storage_key", sa.String(length=1024), nullable=True),
        sa.Column("coordinate_map_hash", sa.String(length=64), nullable=True),
        sa.Column("extraction_quality", sa.Float(), nullable=True),
        sa.Column("text_classification", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("length(extractor_configuration_hash) = 64", name="ck_ad_source_page_text_config_hash"),
        sa.CheckConstraint("length(text_hash) = 64", name="ck_ad_source_page_text_hash"),
        sa.ForeignKeyConstraint(
            ["rendition_id", "source_document_id", "source_content_hash", "page_number"],
            [
                "ad_source_page_renditions.id", "ad_source_page_renditions.source_document_id",
                "ad_source_page_renditions.source_content_hash", "ad_source_page_renditions.page_number",
            ],
            name="fk_ad_source_page_text_rendition_chain",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "id", "rendition_id", "source_document_id", "source_content_hash", "page_number",
            name="uq_ad_source_page_text_chain",
        ),
        sa.UniqueConstraint(
            "rendition_id", "extractor_configuration_hash", "text_hash",
            name="uq_ad_source_page_text_version_identity",
        ),
    )
    for column in (
        "rendition_id", "source_document_id", "source_content_hash",
        "extractor_configuration_hash", "text_hash",
    ):
        op.create_index(op.f(f"ix_ad_source_page_text_versions_{column}"), "ad_source_page_text_versions", [column])

    op.create_table(
        "ad_evidence_fragments",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("directive_id", sa.String(length=36), nullable=False),
        sa.Column("source_document_id", sa.String(length=36), nullable=False),
        sa.Column("source_content_hash", sa.String(length=64), nullable=False),
        sa.Column("rendition_id", sa.String(length=36), nullable=False),
        sa.Column("page_text_version_id", sa.String(length=36), nullable=False),
        sa.Column("page_start", sa.Integer(), nullable=False),
        sa.Column("page_end", sa.Integer(), nullable=False),
        sa.Column("paragraph_locator", sa.String(length=255), nullable=True),
        sa.Column("table_locator", sa.String(length=255), nullable=True),
        sa.Column("row_locator", sa.String(length=255), nullable=True),
        sa.Column("note_locator", sa.String(length=255), nullable=True),
        sa.Column("character_start", sa.Integer(), nullable=False),
        sa.Column("character_end", sa.Integer(), nullable=False),
        sa.Column("region_map_hash", sa.String(length=64), nullable=True),
        sa.Column("exact_text", sa.Text(), nullable=False),
        sa.Column("fragment_hash", sa.String(length=64), nullable=False),
        sa.Column("parser_name", sa.String(length=128), nullable=False),
        sa.Column("parser_version", sa.String(length=128), nullable=False),
        sa.Column("created_by_user_id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("page_start >= 1", name="ck_ad_evidence_fragment_page_start"),
        sa.CheckConstraint("page_end = page_start", name="ck_ad_evidence_fragment_single_page"),
        sa.CheckConstraint("character_start >= 0", name="ck_ad_evidence_fragment_character_start"),
        sa.CheckConstraint("character_end > character_start", name="ck_ad_evidence_fragment_character_end"),
        sa.CheckConstraint("length(source_content_hash) = 64", name="ck_ad_evidence_fragment_source_hash"),
        sa.CheckConstraint("length(fragment_hash) = 64", name="ck_ad_evidence_fragment_hash"),
        sa.CheckConstraint("length(exact_text) > 0", name="ck_ad_evidence_fragment_exact_text"),
        sa.ForeignKeyConstraint(
            ["directive_id", "source_document_id"],
            ["ad_publications.directive_id", "ad_publications.source_document_id"],
            name="fk_ad_evidence_fragment_publication",
        ),
        sa.ForeignKeyConstraint(["directive_id"], ["airworthiness_directives.id"]),
        sa.ForeignKeyConstraint(
            ["source_document_id", "source_content_hash"],
            ["ad_source_documents.id", "ad_source_documents.content_hash"],
            name="fk_ad_evidence_fragment_document_hash",
        ),
        sa.ForeignKeyConstraint(
            [
                "page_text_version_id", "rendition_id", "source_document_id",
                "source_content_hash", "page_start",
            ],
            [
                "ad_source_page_text_versions.id", "ad_source_page_text_versions.rendition_id",
                "ad_source_page_text_versions.source_document_id",
                "ad_source_page_text_versions.source_content_hash",
                "ad_source_page_text_versions.page_number",
            ],
            name="fk_ad_evidence_fragment_text_chain",
        ),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("fragment_hash", name="uq_ad_evidence_fragment_hash"),
        sa.UniqueConstraint(
            "page_text_version_id", "character_start", "character_end",
            "paragraph_locator", "table_locator", "row_locator", "note_locator",
            name="uq_ad_evidence_fragment_selection",
        ),
    )
    for column in (
        "directive_id", "source_document_id", "source_content_hash", "rendition_id",
        "page_text_version_id", "fragment_hash", "created_by_user_id",
    ):
        op.create_index(op.f(f"ix_ad_evidence_fragments_{column}"), "ad_evidence_fragments", [column])

    op.create_table(
        "ad_evidence_fragment_lifecycle_events",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("fragment_id", sa.String(length=36), nullable=False),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("actor_user_id", sa.String(length=36), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("sequence_number", sa.Integer(), nullable=False),
        sa.Column("predecessor_event_hash", sa.String(length=64), nullable=True),
        sa.Column("event_hash", sa.String(length=64), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint(
            "event_type IN ('admitted', 'superseded', 'quarantined')",
            name="ck_ad_evidence_fragment_lifecycle_event_type",
        ),
        sa.CheckConstraint("length(event_hash) = 64", name="ck_ad_evidence_fragment_event_hash"),
        sa.CheckConstraint(
            "predecessor_event_hash IS NULL OR length(predecessor_event_hash) = 64",
            name="ck_ad_evidence_fragment_predecessor_hash",
        ),
        sa.CheckConstraint("sequence_number >= 0", name="ck_ad_evidence_fragment_event_sequence"),
        sa.CheckConstraint(
            "(event_type = 'admitted' AND sequence_number = 0 AND predecessor_event_hash IS NULL) "
            "OR (event_type <> 'admitted' AND sequence_number > 0 AND predecessor_event_hash IS NOT NULL)",
            name="ck_ad_evidence_fragment_event_root",
        ),
        sa.ForeignKeyConstraint(["fragment_id"], ["ad_evidence_fragments.id"]),
        sa.ForeignKeyConstraint(
            ["fragment_id", "predecessor_event_hash"],
            ["ad_evidence_fragment_lifecycle_events.fragment_id", "ad_evidence_fragment_lifecycle_events.event_hash"],
            name="fk_ad_evidence_fragment_event_predecessor",
        ),
        sa.ForeignKeyConstraint(["actor_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("event_hash", name="uq_ad_evidence_fragment_lifecycle_event_hash"),
        sa.UniqueConstraint(
            "fragment_id", "event_hash", name="uq_ad_evidence_fragment_event_chain_identity"
        ),
        sa.UniqueConstraint(
            "fragment_id", "sequence_number", name="uq_ad_evidence_fragment_event_sequence"
        ),
    )
    for column in ("fragment_id", "event_type", "actor_user_id", "event_hash"):
        op.create_index(
            op.f(f"ix_ad_evidence_fragment_lifecycle_events_{column}"),
            "ad_evidence_fragment_lifecycle_events",
            [column],
        )
    op.create_index(
        "uq_ad_evidence_fragment_admission_root",
        "ad_evidence_fragment_lifecycle_events",
        ["fragment_id"],
        unique=True,
        postgresql_where=sa.text("event_type = 'admitted'"),
    )

    op.execute("""
        CREATE OR REPLACE FUNCTION paprnav_hash_parts(VARIADIC parts text[])
        RETURNS text AS $$
        DECLARE
            part text;
            material text := '';
        BEGIN
            FOREACH part IN ARRAY parts LOOP
                IF part IS NULL THEN
                    material := material || '-1:';
                ELSE
                    material := material || octet_length(convert_to(part, 'UTF8'))::text || ':' || part;
                END IF;
            END LOOP;
            RETURN encode(sha256(convert_to(material, 'UTF8')), 'hex');
        END;
        $$ LANGUAGE plpgsql IMMUTABLE STRICT
    """)
    op.execute("""
        CREATE OR REPLACE FUNCTION paprnav_validate_ad_page_text()
        RETURNS trigger AS $$
        BEGIN
            IF NEW.text_hash <> encode(sha256(convert_to(NEW.page_text, 'UTF8')), 'hex') THEN
                RAISE EXCEPTION 'AD page text hash mismatch';
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql
    """)
    op.execute("""
        CREATE TRIGGER trg_ad_source_page_text_versions_validate
        BEFORE INSERT ON ad_source_page_text_versions
        FOR EACH ROW EXECUTE FUNCTION paprnav_validate_ad_page_text()
    """)
    op.execute("""
        CREATE OR REPLACE FUNCTION paprnav_validate_ad_evidence_fragment()
        RETURNS trigger AS $$
        DECLARE
            authoritative_text text;
            authoritative_parser_name text;
            authoritative_parser_version text;
            expected_text text;
            expected_hash text;
        BEGIN
            SELECT page_text, extractor_name, extractor_version
            INTO authoritative_text, authoritative_parser_name, authoritative_parser_version
            FROM ad_source_page_text_versions
            WHERE id = NEW.page_text_version_id
              AND rendition_id = NEW.rendition_id
              AND source_document_id = NEW.source_document_id
              AND source_content_hash = NEW.source_content_hash
              AND page_number = NEW.page_start;
            IF authoritative_text IS NULL THEN
                RAISE EXCEPTION 'AD evidence fragment source chain mismatch';
            END IF;
            IF NEW.character_end > char_length(authoritative_text) THEN
                RAISE EXCEPTION 'AD evidence fragment selector exceeds page text';
            END IF;
            IF NEW.parser_name IS DISTINCT FROM authoritative_parser_name
               OR NEW.parser_version IS DISTINCT FROM authoritative_parser_version THEN
                RAISE EXCEPTION 'AD evidence fragment parser provenance mismatch';
            END IF;
            expected_text := substring(
                authoritative_text FROM NEW.character_start + 1
                FOR NEW.character_end - NEW.character_start
            );
            IF NEW.exact_text IS DISTINCT FROM expected_text THEN
                RAISE EXCEPTION 'AD evidence fragment exact text mismatch';
            END IF;
            expected_hash := paprnav_hash_parts(
                NEW.directive_id, NEW.source_document_id, NEW.source_content_hash,
                NEW.rendition_id, NEW.page_text_version_id,
                NEW.page_start::text, NEW.page_end::text,
                NEW.character_start::text, NEW.character_end::text,
                NEW.paragraph_locator, NEW.table_locator, NEW.row_locator, NEW.note_locator,
                NEW.region_map_hash, NEW.exact_text,
                NEW.parser_name, NEW.parser_version
            );
            IF NEW.fragment_hash <> expected_hash THEN
                RAISE EXCEPTION 'AD evidence fragment hash mismatch';
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql
    """)
    op.execute("""
        CREATE TRIGGER trg_ad_evidence_fragments_validate
        BEFORE INSERT ON ad_evidence_fragments
        FOR EACH ROW EXECUTE FUNCTION paprnav_validate_ad_evidence_fragment()
    """)
    op.execute("""
        CREATE OR REPLACE FUNCTION paprnav_validate_ad_evidence_event()
        RETURNS trigger AS $$
        DECLARE
            source_fragment_hash text;
            predecessor_sequence integer;
            expected_hash text;
        BEGIN
            SELECT fragment_hash INTO source_fragment_hash
            FROM ad_evidence_fragments WHERE id = NEW.fragment_id;
            IF source_fragment_hash IS NULL THEN
                RAISE EXCEPTION 'AD evidence lifecycle fragment is missing';
            END IF;
            IF NEW.event_type <> 'admitted' THEN
                SELECT sequence_number INTO predecessor_sequence
                FROM ad_evidence_fragment_lifecycle_events
                WHERE fragment_id = NEW.fragment_id
                  AND event_hash = NEW.predecessor_event_hash;
                IF predecessor_sequence IS NULL OR predecessor_sequence <> NEW.sequence_number - 1 THEN
                    RAISE EXCEPTION 'AD evidence lifecycle predecessor mismatch';
                END IF;
            END IF;
            expected_hash := paprnav_hash_parts(
                NEW.fragment_id, source_fragment_hash, NEW.event_type,
                NEW.actor_user_id, NEW.reason, NEW.sequence_number::text,
                NEW.predecessor_event_hash
            );
            IF NEW.event_hash <> expected_hash THEN
                RAISE EXCEPTION 'AD evidence lifecycle event hash mismatch';
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql
    """)
    op.execute("""
        CREATE TRIGGER trg_ad_evidence_fragment_lifecycle_events_validate
        BEFORE INSERT ON ad_evidence_fragment_lifecycle_events
        FOR EACH ROW EXECUTE FUNCTION paprnav_validate_ad_evidence_event()
    """)
    op.execute("""
        CREATE OR REPLACE FUNCTION paprnav_require_ad_evidence_admission()
        RETURNS trigger AS $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM ad_evidence_fragment_lifecycle_events
                WHERE fragment_id = NEW.id
                  AND event_type = 'admitted'
                  AND sequence_number = 0
                  AND predecessor_event_hash IS NULL
            ) THEN
                RAISE EXCEPTION 'AD evidence fragment lacks a valid admission root';
            END IF;
            RETURN NULL;
        END;
        $$ LANGUAGE plpgsql
    """)
    op.execute("""
        CREATE CONSTRAINT TRIGGER trg_ad_evidence_fragment_requires_admission
        AFTER INSERT ON ad_evidence_fragments
        DEFERRABLE INITIALLY DEFERRED
        FOR EACH ROW EXECUTE FUNCTION paprnav_require_ad_evidence_admission()
    """)

    # PostgreSQL is the production authority. These triggers prevent any ORM,
    # script, or future endpoint from silently rewriting admitted evidence.
    op.execute("""
        CREATE OR REPLACE FUNCTION paprnav_reject_immutable_ad_evidence_mutation()
        RETURNS trigger AS $$
        BEGIN
            RAISE EXCEPTION 'immutable AD evidence rows cannot be updated or deleted';
        END;
        $$ LANGUAGE plpgsql
    """)
    for table_name in IMMUTABLE_TABLES:
        op.execute(f"""
            CREATE TRIGGER trg_{table_name}_immutable
            BEFORE UPDATE OR DELETE ON {table_name}
            FOR EACH ROW EXECUTE FUNCTION paprnav_reject_immutable_ad_evidence_mutation()
        """)


def downgrade() -> None:
    # ACCESS EXCLUSIVE is retained through the migration transaction. It
    # prevents an admission from committing between the emptiness check and
    # the destructive DROP statements.
    op.execute(
        "LOCK TABLE ad_evidence_fragment_lifecycle_events, ad_evidence_fragments, "
        "ad_source_page_text_versions, ad_source_page_renditions IN ACCESS EXCLUSIVE MODE"
    )
    dependent = op.get_bind().execute(sa.text("""
        SELECT 1
        WHERE EXISTS (SELECT 1 FROM ad_source_page_renditions LIMIT 1)
           OR EXISTS (SELECT 1 FROM ad_source_page_text_versions LIMIT 1)
           OR EXISTS (SELECT 1 FROM ad_evidence_fragments LIMIT 1)
           OR EXISTS (SELECT 1 FROM ad_evidence_fragment_lifecycle_events LIMIT 1)
    """)).first()
    if dependent is not None:
        raise RuntimeError(
            "Revision 0025 contains immutable AD evidence; restore a verified "
            "pre-0025 backup instead of deleting retained regulatory evidence"
        )

    op.execute(
        "DROP TRIGGER IF EXISTS trg_ad_evidence_fragment_requires_admission "
        "ON ad_evidence_fragments"
    )
    op.execute(
        "DROP TRIGGER IF EXISTS trg_ad_evidence_fragment_lifecycle_events_validate "
        "ON ad_evidence_fragment_lifecycle_events"
    )
    op.execute("DROP TRIGGER IF EXISTS trg_ad_evidence_fragments_validate ON ad_evidence_fragments")
    op.execute(
        "DROP TRIGGER IF EXISTS trg_ad_source_page_text_versions_validate "
        "ON ad_source_page_text_versions"
    )
    for table_name in reversed(IMMUTABLE_TABLES):
        op.execute(f"DROP TRIGGER IF EXISTS trg_{table_name}_immutable ON {table_name}")
    op.execute("DROP FUNCTION IF EXISTS paprnav_reject_immutable_ad_evidence_mutation()")
    op.execute("DROP FUNCTION IF EXISTS paprnav_require_ad_evidence_admission()")
    op.execute("DROP FUNCTION IF EXISTS paprnav_validate_ad_evidence_event()")
    op.execute("DROP FUNCTION IF EXISTS paprnav_validate_ad_evidence_fragment()")
    op.execute("DROP FUNCTION IF EXISTS paprnav_validate_ad_page_text()")
    op.execute("DROP FUNCTION IF EXISTS paprnav_hash_parts(VARIADIC text[])")

    op.drop_index(
        "uq_ad_evidence_fragment_admission_root",
        table_name="ad_evidence_fragment_lifecycle_events",
    )
    for column in reversed(("fragment_id", "event_type", "actor_user_id", "event_hash")):
        op.drop_index(
            op.f(f"ix_ad_evidence_fragment_lifecycle_events_{column}"),
            table_name="ad_evidence_fragment_lifecycle_events",
        )
    op.drop_table("ad_evidence_fragment_lifecycle_events")
    for column in reversed((
        "directive_id", "source_document_id", "source_content_hash", "rendition_id",
        "page_text_version_id", "fragment_hash", "created_by_user_id",
    )):
        op.drop_index(op.f(f"ix_ad_evidence_fragments_{column}"), table_name="ad_evidence_fragments")
    op.drop_table("ad_evidence_fragments")
    for column in reversed((
        "rendition_id", "source_document_id", "source_content_hash",
        "extractor_configuration_hash", "text_hash",
    )):
        op.drop_index(op.f(f"ix_ad_source_page_text_versions_{column}"), table_name="ad_source_page_text_versions")
    op.drop_table("ad_source_page_text_versions")
    for column in reversed((
        "source_document_id", "source_content_hash", "renderer_configuration_hash", "rendition_hash",
    )):
        op.drop_index(op.f(f"ix_ad_source_page_renditions_{column}"), table_name="ad_source_page_renditions")
    op.drop_table("ad_source_page_renditions")
    op.drop_constraint(
        "uq_ad_publication_directive_document", "ad_publications", type_="unique"
    )
    op.drop_constraint(
        "uq_ad_source_document_id_content_hash", "ad_source_documents", type_="unique"
    )
