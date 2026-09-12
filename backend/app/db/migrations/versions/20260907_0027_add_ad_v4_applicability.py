"""add validator-2 compatibility and candidate-only V4 applicability projection

Revision ID: 20260907_0027
Revises: 20260901_0026
Create Date: 2026-09-07
"""

from alembic import op
import sqlalchemy as sa


revision = "20260907_0027"
down_revision = "20260901_0026"
branch_labels = None
depends_on = None

V1_VALIDATOR = "paprnav-ad-v4-validator-1"
V1_C14N = "paprnav-ad-v4-c14n-1"
V2_VALIDATOR = "paprnav-ad-v4-validator-2"
V2_C14N = "paprnav-ad-v4-c14n-2"

CHILD_TABLES = (
    "ad_v4_candidate_evidence_bindings",
    "ad_v4_candidate_submissions",
    "ad_v4_candidate_submission_relationships",
    "ad_v4_candidate_proposal_events",
)

APP_TABLES = (
    "ad_v4_feature_gates",
    "ad_v4_candidate_app_projections",
    "ad_v4_candidate_app_materialization_requests",
    "ad_v4_candidate_app_semantic_nodes",
    "ad_v4_candidate_app_data",
    "ad_v4_candidate_app_evidence_links",
    "ad_v4_candidate_app_identity_mappings",
    "ad_v4_candidate_app_value_assertions",
    "ad_v4_candidate_app_product_scopes",
    "ad_v4_candidate_app_designation_scopes",
    "ad_v4_candidate_app_designation_values",
    "ad_v4_candidate_app_designation_ranges",
    "ad_v4_candidate_app_conditions",
    "ad_v4_candidate_app_designation_groups",
    "ad_v4_candidate_app_designation_group_members",
    "ad_v4_candidate_app_rules",
    "ad_v4_candidate_app_expressions",
    "ad_v4_candidate_app_expression_edges",
    "ad_v4_candidate_app_rule_exclusions",
    "ad_v4_candidate_app_search_hints",
    "ad_v4_candidate_app_search_hint_groups",
    "ad_v4_candidate_app_search_hint_members",
    "ad_v4_candidate_corrections",
    "ad_v4_candidate_correction_refs",
    "ad_v4_candidate_correction_semantic_bindings",
    "ad_v4_candidate_correction_evidence_links",
    "ad_v4_candidate_app_change_dependencies",
    "ad_v4_candidate_app_projection_events",
)


def _id(name: str, *, primary: bool = False) -> sa.Column:
    return sa.Column(name, sa.String(36), primary_key=primary, nullable=False)


def upgrade() -> None:
    for table in CHILD_TABLES:
        op.add_column(table, sa.Column("validator_version", sa.String(64), nullable=True))
        op.add_column(table, sa.Column("canonicalization_version", sa.String(64), nullable=True))
        op.execute(f"ALTER TABLE {table} DISABLE TRIGGER trg_{table}_immutable")
        if table == "ad_v4_candidate_submission_relationships":
            op.execute(f"""UPDATE {table} c SET validator_version=p.validator_version,
                       canonicalization_version=p.canonicalization_version
                  FROM ad_v4_candidate_submissions s, ad_v4_candidate_proposals p
                 WHERE s.id=c.submission_id AND p.id=s.proposal_id""")
        else:
            op.execute(f"""UPDATE {table} c SET validator_version=p.validator_version,
                       canonicalization_version=p.canonicalization_version
                  FROM ad_v4_candidate_proposals p WHERE p.id=c.proposal_id""")
        op.execute(f"ALTER TABLE {table} ENABLE TRIGGER trg_{table}_immutable")
        op.alter_column(table, "validator_version", nullable=False)
        op.alter_column(table, "canonicalization_version", nullable=False)
        op.create_check_constraint(
            f"ck_{table}_version_pair", table,
            "(validator_version='paprnav-ad-v4-validator-1' AND canonicalization_version='paprnav-ad-v4-c14n-1') OR "
            "(validator_version='paprnav-ad-v4-validator-2' AND canonicalization_version='paprnav-ad-v4-c14n-2')",
        )

    op.drop_constraint("uq_ad_v4_proposal_content", "ad_v4_candidate_proposals", type_="unique")
    op.create_unique_constraint(
        "uq_ad_v4_proposal_content_v2", "ad_v4_candidate_proposals",
        ["directive_id", "validator_version", "canonicalization_version", "canonical_hash"],
    )
    op.create_unique_constraint(
        "uq_ad_v4_binding_parent_identity", "ad_v4_candidate_evidence_bindings",
        ["proposal_id", "id", "evidence_key"],
    )

    op.create_table(
        "ad_v4_feature_gates",
        sa.Column("gate_key", sa.String(64), primary_key=True),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("changed_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("changed_by", sa.String(128), nullable=False, server_default="migration"),
        sa.CheckConstraint("gate_key IN ('validator2_write_enabled','materializer3a_enabled')", name="ck_ad_v4_feature_gate_key"),
    )
    op.execute("INSERT INTO ad_v4_feature_gates(gate_key,enabled) VALUES ('validator2_write_enabled',false),('materializer3a_enabled',false)")

    op.create_table(
        "ad_v4_candidate_app_projections",
        _id("id", primary=True), sa.Column("identity_hash", sa.String(64), nullable=False, unique=True),
        _id("proposal_id"), _id("directive_id"), sa.Column("schema_version", sa.String(64), nullable=False),
        sa.Column("validator_version", sa.String(64), nullable=False), sa.Column("canonicalization_version", sa.String(64), nullable=False),
        sa.Column("proposal_canonical_hash", sa.String(64), nullable=False), sa.Column("evidence_binding_hash", sa.String(64), nullable=False),
        sa.Column("materializer_version", sa.String(64), nullable=False), sa.Column("applicability_subtree_bytes", sa.LargeBinary(), nullable=False),
        sa.Column("applicability_subtree_hash", sa.String(64), nullable=False), sa.Column("projection_canonical_bytes", sa.LargeBinary(), nullable=False),
        sa.Column("projection_hash", sa.String(64), nullable=False), sa.Column("gate", sa.String(32), nullable=False),
        sa.Column("semantic_node_count", sa.Integer(), nullable=False), sa.Column("datum_count", sa.Integer(), nullable=False),
        sa.Column("evidence_link_count", sa.Integer(), nullable=False), sa.Column("identity_mapping_count", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["proposal_id"], ["ad_v4_candidate_proposals.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["directive_id"], ["airworthiness_directives.id"], ondelete="RESTRICT"),
        sa.CheckConstraint("gate='candidate_only'", name="ck_ad_v4_app_projection_gate"),
        sa.CheckConstraint(f"validator_version='{V2_VALIDATOR}' AND canonicalization_version='{V2_C14N}'", name="ck_ad_v4_app_projection_v2"),
        sa.UniqueConstraint("id", "proposal_id", name="uq_ad_v4_app_projection_parent_identity"),
        sa.UniqueConstraint("proposal_id", "materializer_version", name="uq_ad_v4_app_projection_parent"),
    )
    op.create_index("ix_ad_v4_app_projection_proposal", "ad_v4_candidate_app_projections", ["proposal_id", "materializer_version"])

    op.create_table(
        "ad_v4_candidate_app_materialization_requests",
        _id("id", primary=True), _id("projection_id"), _id("proposal_id"), _id("directive_id"),
        _id("actor_user_id"), _id("authorizing_membership_id"), _id("organization_id"),
        sa.Column("actor_role", sa.String(64), nullable=False), sa.Column("actor_status", sa.String(32), nullable=False),
        sa.Column("auth_policy_name", sa.String(96), nullable=False), sa.Column("auth_policy_version", sa.String(64), nullable=False),
        sa.Column("auth_claims_hash", sa.String(64), nullable=False), sa.Column("endpoint_action", sa.String(96), nullable=False),
        sa.Column("idempotency_key", sa.String(255), nullable=False), sa.Column("request_canonical_bytes", sa.LargeBinary(), nullable=False),
        sa.Column("request_hash", sa.String(64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["projection_id"], ["ad_v4_candidate_app_projections.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["projection_id", "proposal_id"], ["ad_v4_candidate_app_projections.id", "ad_v4_candidate_app_projections.proposal_id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["proposal_id"], ["ad_v4_candidate_proposals.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["directive_id"], ["airworthiness_directives.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["actor_user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["authorizing_membership_id"], ["organization_memberships.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="RESTRICT"),
        sa.CheckConstraint("actor_role='platform_admin' AND actor_status='active'", name="ck_ad_v4_app_request_auth"),
        sa.UniqueConstraint("actor_user_id", "authorizing_membership_id", "endpoint_action", "auth_policy_version", "idempotency_key", name="uq_ad_v4_app_request_idempotency"),
    )

    op.create_table(
        "ad_v4_candidate_app_semantic_nodes",
        _id("id", primary=True), sa.Column("identity_hash", sa.String(64), nullable=False, unique=True),
        _id("projection_id"), _id("proposal_id"), sa.Column("parent_node_id", sa.String(36), nullable=True),
        sa.Column("node_type", sa.String(64), nullable=False), sa.Column("node_key", sa.Text(), nullable=False),
        sa.Column("source_pointer", sa.Text(), nullable=False), sa.Column("canonical_node_hash", sa.String(64), nullable=False),
        sa.Column("canonical_ordinal", sa.Integer(), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["projection_id"], ["ad_v4_candidate_app_projections.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["proposal_id"], ["ad_v4_candidate_proposals.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["projection_id", "proposal_id"], ["ad_v4_candidate_app_projections.id", "ad_v4_candidate_app_projections.proposal_id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["parent_node_id"], ["ad_v4_candidate_app_semantic_nodes.id"], ondelete="RESTRICT"),
        sa.CheckConstraint("canonical_ordinal>=0", name="ck_ad_v4_app_node_ordinal"),
        sa.CheckConstraint("node_type IN ('product_scope','designation_scope','value_assertion','identity_mapping','designation_value','designation_range','designation_group','designation_group_member','condition','expression','applicability_rule','search_hint','search_hint_group','search_hint_model','change_dependency')", name="ck_ad_v4_app_node_type"),
        sa.UniqueConstraint("id", "projection_id", "proposal_id", name="uq_ad_v4_app_node_parent_identity"),
        sa.UniqueConstraint("projection_id", "node_type", "node_key", name="uq_ad_v4_app_node_key"),
    )
    op.create_index("ix_ad_v4_app_node_reconstruct", "ad_v4_candidate_app_semantic_nodes", ["projection_id", "node_type", "node_key"])

    op.create_table(
        "ad_v4_candidate_app_data",
        _id("id", primary=True), _id("projection_id"), _id("proposal_id"),
        sa.Column("semantic_node_id", sa.String(36), nullable=True), sa.Column("json_pointer", sa.Text(), nullable=False),
        sa.Column("parent_pointer", sa.Text(), nullable=True), sa.Column("property_name", sa.String(255), nullable=True),
        sa.Column("array_ordinal", sa.Integer(), nullable=True), sa.Column("value_kind", sa.String(16), nullable=False),
        sa.Column("string_value", sa.Text(), nullable=True), sa.Column("boolean_value", sa.Boolean(), nullable=True),
        sa.Column("value_hash", sa.String(64), nullable=False),
        sa.ForeignKeyConstraint(["projection_id"], ["ad_v4_candidate_app_projections.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["proposal_id"], ["ad_v4_candidate_proposals.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["semantic_node_id"], ["ad_v4_candidate_app_semantic_nodes.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["projection_id", "proposal_id"], ["ad_v4_candidate_app_projections.id", "ad_v4_candidate_app_projections.proposal_id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["semantic_node_id", "projection_id", "proposal_id"], ["ad_v4_candidate_app_semantic_nodes.id", "ad_v4_candidate_app_semantic_nodes.projection_id", "ad_v4_candidate_app_semantic_nodes.proposal_id"], ondelete="RESTRICT"),
        sa.CheckConstraint("value_kind IN ('object','array','string','boolean')", name="ck_ad_v4_app_datum_kind"),
        sa.UniqueConstraint("projection_id", "json_pointer", name="uq_ad_v4_app_datum_pointer"),
    )
    op.create_index("ix_ad_v4_app_data_reconstruct", "ad_v4_candidate_app_data", ["projection_id"])

    op.create_table(
        "ad_v4_candidate_app_evidence_links",
        _id("id", primary=True), _id("projection_id"), _id("proposal_id"), _id("semantic_node_id"), _id("candidate_binding_id"),
        sa.Column("evidence_key", sa.String(128), nullable=False), sa.Column("purpose", sa.String(64), nullable=False),
        sa.Column("canonical_ordinal", sa.Integer(), nullable=False), sa.Column("link_hash", sa.String(64), nullable=False),
        sa.ForeignKeyConstraint(["projection_id"], ["ad_v4_candidate_app_projections.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["projection_id", "proposal_id"], ["ad_v4_candidate_app_projections.id", "ad_v4_candidate_app_projections.proposal_id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["proposal_id", "candidate_binding_id", "evidence_key"], ["ad_v4_candidate_evidence_bindings.proposal_id", "ad_v4_candidate_evidence_bindings.id", "ad_v4_candidate_evidence_bindings.evidence_key"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["semantic_node_id"], ["ad_v4_candidate_app_semantic_nodes.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["semantic_node_id", "projection_id", "proposal_id"], ["ad_v4_candidate_app_semantic_nodes.id", "ad_v4_candidate_app_semantic_nodes.projection_id", "ad_v4_candidate_app_semantic_nodes.proposal_id"], ondelete="RESTRICT"),
        sa.UniqueConstraint("semantic_node_id", "purpose", "evidence_key", name="uq_ad_v4_app_evidence_link"),
    )
    op.create_index("ix_ad_v4_app_evidence_reconstruct", "ad_v4_candidate_app_evidence_links", ["semantic_node_id", "purpose", "canonical_ordinal"])

    op.create_table(
        "ad_v4_candidate_app_identity_mappings",
        _id("id", primary=True), _id("semantic_node_id"), _id("projection_id"), _id("proposal_id"), _id("source_occurrence_node_id"), _id("evidence_parent_node_id"),
        sa.Column("identity_kind", sa.String(32), nullable=False), sa.Column("source_value", sa.Text(), nullable=False),
        sa.Column("normalization_origin", sa.String(64), nullable=False), sa.Column("normalized_state", sa.String(32), nullable=False),
        sa.Column("normalized_value", sa.Text(), nullable=True), sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("temporal_scope", sa.String(64), nullable=True), sa.Column("normalization_namespace", sa.String(64), nullable=True),
        sa.Column("normalization_version", sa.String(64), nullable=True), sa.Column("review_state", sa.String(32), nullable=False),
        sa.Column("identity_hash", sa.String(64), nullable=False, unique=True),
        sa.ForeignKeyConstraint(["projection_id"], ["ad_v4_candidate_app_projections.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["proposal_id"], ["ad_v4_candidate_proposals.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["source_occurrence_node_id"], ["ad_v4_candidate_app_semantic_nodes.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["evidence_parent_node_id"], ["ad_v4_candidate_app_semantic_nodes.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["semantic_node_id"], ["ad_v4_candidate_app_semantic_nodes.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["projection_id", "proposal_id"], ["ad_v4_candidate_app_projections.id", "ad_v4_candidate_app_projections.proposal_id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["source_occurrence_node_id", "projection_id", "proposal_id"], ["ad_v4_candidate_app_semantic_nodes.id", "ad_v4_candidate_app_semantic_nodes.projection_id", "ad_v4_candidate_app_semantic_nodes.proposal_id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["evidence_parent_node_id", "projection_id", "proposal_id"], ["ad_v4_candidate_app_semantic_nodes.id", "ad_v4_candidate_app_semantic_nodes.projection_id", "ad_v4_candidate_app_semantic_nodes.proposal_id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["semantic_node_id", "projection_id", "proposal_id"], ["ad_v4_candidate_app_semantic_nodes.id", "ad_v4_candidate_app_semantic_nodes.projection_id", "ad_v4_candidate_app_semantic_nodes.proposal_id"], ondelete="RESTRICT"),
        sa.CheckConstraint("identity_kind IN ('manufacturer','model','series','model_or_series')", name="ck_ad_v4_app_identity_kind"),
        sa.CheckConstraint("normalization_origin IN ('candidate_payload','source_only','no_normalized_identity')", name="ck_ad_v4_app_identity_origin"),
        sa.CheckConstraint("normalized_state IN ('known','unknown','not_applicable')", name="ck_ad_v4_app_identity_state"),
        sa.CheckConstraint("(normalization_origin='candidate_payload' AND ((normalized_state='known' AND normalized_value IS NOT NULL AND reason IS NULL AND temporal_scope IS NULL AND normalization_namespace IS NOT NULL AND normalization_version IS NOT NULL) OR (normalized_state='unknown' AND normalized_value IS NULL AND reason IN ('not_observed','unavailable','not_obtained','not_extracted','not_yet_reviewed','not_yet_verified','conflicting_evidence','source_ambiguous','unsupported_expression') AND temporal_scope IS NOT NULL AND normalization_namespace IS NULL AND normalization_version IS NULL) OR (normalized_state='not_applicable' AND normalized_value IS NULL AND reason IS NOT NULL AND char_length(reason) BETWEEN 1 AND 512 AND temporal_scope IS NOT NULL AND normalization_namespace IS NULL AND normalization_version IS NULL))) OR (normalization_origin IN ('source_only','no_normalized_identity') AND normalized_state='unknown' AND normalized_value IS NULL AND reason IN ('not_extracted','not_yet_reviewed') AND temporal_scope IN ('source_observation','directive_version') AND normalization_namespace IS NULL AND normalization_version IS NULL)", name="ck_ad_v4_app_identity_union"),
        sa.CheckConstraint("review_state='unreviewed_candidate'", name="ck_ad_v4_app_identity_review"),
        sa.UniqueConstraint("semantic_node_id", name="uq_ad_v4_app_identity_semantic_node"),
        sa.UniqueConstraint("projection_id", "identity_kind", "source_occurrence_node_id", name="uq_ad_v4_app_identity_occurrence"),
    )

    _create_source_and_scope_tables()
    _create_condition_tables()
    _create_rule_tables()
    _create_search_hint_tables()

    _create_correction_tables()
    _create_dependency_and_event_tables()
    _replace_v4_validation_functions()
    _install_projection_validation()
    _install_projection_audit_validation()
    _install_projection_completeness()
    _install_immutability()


def _typed_owner_fks() -> tuple[sa.ForeignKeyConstraint, ...]:
    return (
        sa.ForeignKeyConstraint(["projection_id"], ["ad_v4_candidate_app_projections.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["proposal_id"], ["ad_v4_candidate_proposals.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["projection_id", "proposal_id"], ["ad_v4_candidate_app_projections.id", "ad_v4_candidate_app_projections.proposal_id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["semantic_node_id", "projection_id", "proposal_id"], ["ad_v4_candidate_app_semantic_nodes.id", "ad_v4_candidate_app_semantic_nodes.projection_id", "ad_v4_candidate_app_semantic_nodes.proposal_id"], ondelete="RESTRICT"),
    )


def _create_source_and_scope_tables() -> None:
    op.create_table(
        "ad_v4_candidate_app_value_assertions",
        _id("semantic_node_id", primary=True), _id("projection_id"), _id("proposal_id"), _id("parent_semantic_node_id"),
        sa.Column("field_code", sa.String(64), nullable=False), sa.Column("state", sa.String(32), nullable=False),
        sa.Column("value_type", sa.String(16), nullable=False), sa.Column("text_value", sa.Text(), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True), sa.Column("temporal_scope", sa.String(64), nullable=True),
        *_typed_owner_fks(),
        sa.ForeignKeyConstraint(["parent_semantic_node_id", "projection_id", "proposal_id"], ["ad_v4_candidate_app_semantic_nodes.id", "ad_v4_candidate_app_semantic_nodes.projection_id", "ad_v4_candidate_app_semantic_nodes.proposal_id"], ondelete="RESTRICT"),
        sa.CheckConstraint("state IN ('known','unknown','not_applicable')", name="ck_ad_v4_app_value_state"),
        sa.CheckConstraint("value_type='text'", name="ck_ad_v4_app_value_type"),
        sa.CheckConstraint("field_code IN ('manufacturer','model_or_series','part_number','serial_number','stc_number','attribute_value','source_display_text')", name="ck_ad_v4_app_value_field"),
        sa.CheckConstraint("(state='known' AND text_value IS NOT NULL AND char_length(text_value) BETWEEN 1 AND 512 AND reason IS NULL AND temporal_scope IS NULL) OR (state='unknown' AND text_value IS NULL AND reason IN ('not_observed','unavailable','not_obtained','not_extracted','not_yet_reviewed','not_yet_verified','conflicting_evidence','source_ambiguous','unsupported_expression') AND temporal_scope IS NOT NULL) OR (state='not_applicable' AND text_value IS NULL AND reason IS NOT NULL AND char_length(reason) BETWEEN 1 AND 512 AND temporal_scope IS NOT NULL)", name="ck_ad_v4_app_value_union"),
        sa.CheckConstraint("temporal_scope IS NULL OR temporal_scope IN ('directive_version','publication_version','at_applicability_evaluation','at_compliance_evaluation','source_observation')", name="ck_ad_v4_app_value_temporal"),
        sa.UniqueConstraint("parent_semantic_node_id", "field_code", name="uq_ad_v4_app_value_parent_field"),
    )
    op.create_table(
        "ad_v4_candidate_app_product_scopes",
        _id("semantic_node_id", primary=True), _id("projection_id"), _id("proposal_id"),
        sa.Column("scope_key", sa.String(128), nullable=False), sa.Column("product_role", sa.String(32), nullable=False),
        sa.Column("manufacturer_presence", sa.String(32), nullable=False), sa.Column("manufacturer_source_value", sa.Text(), nullable=True),
        sa.Column("manufacturer_identity_mapping_node_id", sa.String(36), nullable=True),
        sa.Column("model_presence", sa.String(32), nullable=False), sa.Column("serial_presence", sa.String(32), nullable=False),
        sa.Column("part_number_presence", sa.String(32), nullable=False),
        *_typed_owner_fks(),
        sa.ForeignKeyConstraint(["manufacturer_identity_mapping_node_id", "projection_id", "proposal_id"], ["ad_v4_candidate_app_semantic_nodes.id", "ad_v4_candidate_app_semantic_nodes.projection_id", "ad_v4_candidate_app_semantic_nodes.proposal_id"], ondelete="RESTRICT"),
        sa.CheckConstraint("product_role IN ('airframe','engine','propeller','appliance','installed_part','modification')", name="ck_ad_v4_app_product_role"),
        sa.CheckConstraint("manufacturer_presence IN ('property_absent','present')", name="ck_ad_v4_app_product_manufacturer_presence"),
        sa.CheckConstraint("(manufacturer_presence='present' AND manufacturer_source_value IS NOT NULL AND manufacturer_identity_mapping_node_id IS NOT NULL) OR (manufacturer_presence='property_absent' AND manufacturer_source_value IS NULL AND manufacturer_identity_mapping_node_id IS NULL)", name="ck_ad_v4_app_product_manufacturer_union"),
        sa.CheckConstraint("model_presence IN ('property_absent','present') AND serial_presence IN ('property_absent','present') AND part_number_presence IN ('property_absent','present')", name="ck_ad_v4_app_product_designation_presence"),
        sa.UniqueConstraint("projection_id", "scope_key", name="uq_ad_v4_app_product_scope_key"),
    )
    op.create_table(
        "ad_v4_candidate_app_designation_scopes",
        _id("semantic_node_id", primary=True), _id("projection_id"), _id("proposal_id"), _id("product_scope_node_id"),
        sa.Column("field_kind", sa.String(32), nullable=False), sa.Column("scope_kind", sa.String(32), nullable=False),
        sa.Column("series_expression", sa.Text(), nullable=True), sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("temporal_scope", sa.String(64), nullable=True), sa.Column("evaluation_state", sa.String(32), nullable=False),
        sa.Column("evaluator_contract", sa.String(64), nullable=False),
        *_typed_owner_fks(),
        sa.ForeignKeyConstraint(["product_scope_node_id", "projection_id", "proposal_id"], ["ad_v4_candidate_app_semantic_nodes.id", "ad_v4_candidate_app_semantic_nodes.projection_id", "ad_v4_candidate_app_semantic_nodes.proposal_id"], ondelete="RESTRICT"),
        sa.CheckConstraint("field_kind IN ('model','serial','part_number')", name="ck_ad_v4_app_designation_field"),
        sa.CheckConstraint("scope_kind IN ('all','listed','series_expression','ranges','unknown','not_applicable')", name="ck_ad_v4_app_designation_kind"),
        sa.CheckConstraint("(scope_kind='series_expression' AND series_expression IS NOT NULL AND reason IS NULL AND temporal_scope IS NULL AND evaluation_state='unknown' AND evaluator_contract='unsupported_expression') OR (scope_kind IN ('unknown','not_applicable') AND series_expression IS NULL AND reason IS NOT NULL AND temporal_scope IS NOT NULL AND evaluation_state='unevaluated' AND evaluator_contract='none') OR (scope_kind IN ('all','listed','ranges') AND series_expression IS NULL AND reason IS NULL AND temporal_scope IS NULL AND evaluation_state='unevaluated' AND evaluator_contract='none')", name="ck_ad_v4_app_designation_union"),
        sa.UniqueConstraint("product_scope_node_id", "field_kind", name="uq_ad_v4_app_designation_scope_field"),
    )
    op.create_table(
        "ad_v4_candidate_app_designation_values",
        _id("semantic_node_id", primary=True), _id("projection_id"), _id("proposal_id"), _id("designation_scope_id"),
        sa.Column("source_value", sa.Text(), nullable=False), sa.Column("canonical_ordinal", sa.Integer(), nullable=False),
        sa.Column("identity_mapping_node_id", sa.String(36), nullable=True),
        *_typed_owner_fks(),
        sa.ForeignKeyConstraint(["designation_scope_id", "projection_id", "proposal_id"], ["ad_v4_candidate_app_semantic_nodes.id", "ad_v4_candidate_app_semantic_nodes.projection_id", "ad_v4_candidate_app_semantic_nodes.proposal_id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["identity_mapping_node_id", "projection_id", "proposal_id"], ["ad_v4_candidate_app_semantic_nodes.id", "ad_v4_candidate_app_semantic_nodes.projection_id", "ad_v4_candidate_app_semantic_nodes.proposal_id"], ondelete="RESTRICT"),
        sa.CheckConstraint("canonical_ordinal>=0", name="ck_ad_v4_app_designation_value_ordinal"),
        sa.UniqueConstraint("designation_scope_id", "source_value", name="uq_ad_v4_app_designation_value_source"),
        sa.UniqueConstraint("designation_scope_id", "canonical_ordinal", name="uq_ad_v4_app_designation_value_ordinal"),
    )
    op.create_table(
        "ad_v4_candidate_app_designation_ranges",
        _id("semantic_node_id", primary=True), _id("projection_id"), _id("proposal_id"), _id("designation_scope_id"),
        sa.Column("lower_value", sa.Text(), nullable=False), sa.Column("upper_value", sa.Text(), nullable=False),
        sa.Column("lower_inclusive", sa.Boolean(), nullable=False), sa.Column("upper_inclusive", sa.Boolean(), nullable=False),
        sa.Column("polarity", sa.String(16), nullable=False), sa.Column("canonical_ordinal", sa.Integer(), nullable=False),
        sa.Column("comparator_version", sa.String(64), nullable=False),
        *_typed_owner_fks(),
        sa.ForeignKeyConstraint(["designation_scope_id", "projection_id", "proposal_id"], ["ad_v4_candidate_app_semantic_nodes.id", "ad_v4_candidate_app_semantic_nodes.projection_id", "ad_v4_candidate_app_semantic_nodes.proposal_id"], ondelete="RESTRICT"),
        sa.CheckConstraint("canonical_ordinal>=0", name="ck_ad_v4_app_designation_range_ordinal"),
        sa.CheckConstraint("polarity IN ('included','excluded')", name="ck_ad_v4_app_designation_range_polarity"),
        sa.CheckConstraint("comparator_version='lexical_source_only_v1'", name="ck_ad_v4_app_designation_range_comparator"),
        sa.UniqueConstraint("designation_scope_id", "lower_value", "upper_value", "lower_inclusive", "upper_inclusive", "polarity", name="uq_ad_v4_app_designation_range_identity"),
        sa.UniqueConstraint("designation_scope_id", "canonical_ordinal", name="uq_ad_v4_app_designation_range_ordinal"),
    )


def _create_condition_tables() -> None:
    op.create_table(
        "ad_v4_candidate_app_conditions",
        _id("semantic_node_id", primary=True), _id("projection_id"), _id("proposal_id"),
        sa.Column("condition_key", sa.String(128), nullable=False),
        sa.Column("condition_type", sa.String(64), nullable=False),
        sa.Column("operator", sa.String(64), nullable=False),
        sa.Column("temporal_basis", sa.String(64), nullable=False),
        sa.Column("comparator_presence", sa.String(32), nullable=False),
        sa.Column("comparator_version", sa.Text(), nullable=True),
        sa.Column("subject_product_role_presence", sa.String(32), nullable=False),
        sa.Column("subject_product_role", sa.String(32), nullable=True),
        sa.Column("subject_attribute_key_presence", sa.String(32), nullable=False),
        sa.Column("subject_attribute_key", sa.String(128), nullable=True),
        sa.Column("designation_group_presence", sa.String(32), nullable=False),
        sa.Column("designation_group_node_id", sa.String(36), nullable=True),
        sa.Column("evaluation_state", sa.String(32), nullable=False),
        sa.Column("evaluator_contract", sa.String(64), nullable=False),
        *_typed_owner_fks(),
        sa.ForeignKeyConstraint(["designation_group_node_id", "projection_id", "proposal_id"], ["ad_v4_candidate_app_semantic_nodes.id", "ad_v4_candidate_app_semantic_nodes.projection_id", "ad_v4_candidate_app_semantic_nodes.proposal_id"], ondelete="RESTRICT"),
        sa.CheckConstraint("condition_type IN ('identity','identifier_range','installed_equipment','modification_or_stc','configuration_attribute','temporal_overlap','source_inclusion','source_exclusion','reviewed_manual_predicate')", name="ck_ad_v4_app_condition_type"),
        sa.CheckConstraint("operator IN ('identity_equals','identity_in','identifier_in_range','is_installed','is_not_installed','equals','overlaps','includes','excludes','requires_review')", name="ck_ad_v4_app_condition_operator"),
        sa.CheckConstraint("comparator_presence IN ('property_absent','present') AND subject_product_role_presence IN ('property_absent','present') AND subject_attribute_key_presence IN ('property_absent','present') AND designation_group_presence IN ('property_absent','present')", name="ck_ad_v4_app_condition_presence"),
        sa.CheckConstraint("(comparator_presence='present')=(comparator_version IS NOT NULL)", name="ck_ad_v4_app_condition_comparator"),
        sa.CheckConstraint("(subject_product_role_presence='present')=(subject_product_role IS NOT NULL)", name="ck_ad_v4_app_condition_role_presence"),
        sa.CheckConstraint("subject_product_role IS NULL OR subject_product_role IN ('airframe','engine','propeller','appliance','installed_part','modification')", name="ck_ad_v4_app_condition_role"),
        sa.CheckConstraint("(subject_attribute_key_presence='present')=(subject_attribute_key IS NOT NULL)", name="ck_ad_v4_app_condition_attribute"),
        sa.CheckConstraint("(designation_group_presence='present')=(designation_group_node_id IS NOT NULL)", name="ck_ad_v4_app_condition_group"),
        sa.CheckConstraint("evaluation_state='unevaluated' AND evaluator_contract='none'", name="ck_ad_v4_app_condition_evaluation"),
        sa.UniqueConstraint("projection_id", "condition_key", name="uq_ad_v4_app_condition_key"),
    )
    op.create_table(
        "ad_v4_candidate_app_designation_groups",
        _id("semantic_node_id", primary=True), _id("projection_id"), _id("proposal_id"),
        _id("condition_node_id"), sa.Column("group_key", sa.String(128), nullable=False),
        sa.Column("association", sa.String(32), nullable=False), _id("source_display_assertion_node_id"),
        sa.Column("reason", sa.Text(), nullable=True), sa.Column("temporal_scope", sa.String(64), nullable=True),
        sa.Column("canonical_ordinal", sa.Integer(), nullable=False),
        *_typed_owner_fks(),
        sa.ForeignKeyConstraint(["condition_node_id", "projection_id", "proposal_id"], ["ad_v4_candidate_app_semantic_nodes.id", "ad_v4_candidate_app_semantic_nodes.projection_id", "ad_v4_candidate_app_semantic_nodes.proposal_id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["source_display_assertion_node_id", "projection_id", "proposal_id"], ["ad_v4_candidate_app_semantic_nodes.id", "ad_v4_candidate_app_semantic_nodes.projection_id", "ad_v4_candidate_app_semantic_nodes.proposal_id"], ondelete="RESTRICT"),
        sa.CheckConstraint("association IN ('all_members','any_member','source_group','unknown')", name="ck_ad_v4_app_group_association"),
        sa.CheckConstraint("(association='unknown' AND reason IN ('not_observed','unavailable','not_obtained','not_extracted','not_yet_reviewed','not_yet_verified','conflicting_evidence','source_ambiguous','unsupported_expression') AND temporal_scope IS NOT NULL) OR (association<>'unknown' AND reason IS NULL AND temporal_scope IS NULL)", name="ck_ad_v4_app_group_unknown"),
        sa.CheckConstraint("canonical_ordinal>=0", name="ck_ad_v4_app_group_ordinal"),
        sa.UniqueConstraint("condition_node_id", "group_key", name="uq_ad_v4_app_group_key"),
        sa.UniqueConstraint("condition_node_id", "canonical_ordinal", name="uq_ad_v4_app_group_ordinal"),
    )
    op.create_table(
        "ad_v4_candidate_app_designation_group_members",
        _id("semantic_node_id", primary=True), _id("projection_id"), _id("proposal_id"),
        _id("group_node_id"), sa.Column("member_key", sa.String(128), nullable=False),
        sa.Column("designation_kind", sa.String(32), nullable=False),
        sa.Column("source_designation", sa.Text(), nullable=True),
        sa.Column("expression_text", sa.Text(), nullable=True),
        _id("manufacturer_assertion_node_id"), sa.Column("manufacturer_state", sa.String(32), nullable=False),
        sa.Column("manufacturer_value", sa.Text(), nullable=True), sa.Column("manufacturer_reason", sa.Text(), nullable=True),
        sa.Column("manufacturer_temporal_scope", sa.String(64), nullable=True),
        sa.Column("evaluation_state", sa.String(32), nullable=True), sa.Column("evaluation_reason", sa.String(64), nullable=True),
        sa.Column("canonical_ordinal", sa.Integer(), nullable=False), _id("designation_identity_mapping_node_id"),
        *_typed_owner_fks(),
        sa.ForeignKeyConstraint(["group_node_id", "projection_id", "proposal_id"], ["ad_v4_candidate_app_semantic_nodes.id", "ad_v4_candidate_app_semantic_nodes.projection_id", "ad_v4_candidate_app_semantic_nodes.proposal_id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["manufacturer_assertion_node_id", "projection_id", "proposal_id"], ["ad_v4_candidate_app_semantic_nodes.id", "ad_v4_candidate_app_semantic_nodes.projection_id", "ad_v4_candidate_app_semantic_nodes.proposal_id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["designation_identity_mapping_node_id", "projection_id", "proposal_id"], ["ad_v4_candidate_app_semantic_nodes.id", "ad_v4_candidate_app_semantic_nodes.projection_id", "ad_v4_candidate_app_semantic_nodes.proposal_id"], ondelete="RESTRICT"),
        sa.CheckConstraint("designation_kind IN ('model','series_expression')", name="ck_ad_v4_app_group_member_kind"),
        sa.CheckConstraint("(designation_kind='model' AND source_designation IS NOT NULL AND expression_text IS NULL AND evaluation_state IS NULL AND evaluation_reason IS NULL) OR (designation_kind='series_expression' AND source_designation IS NULL AND expression_text IS NOT NULL AND evaluation_state='unevaluated' AND evaluation_reason='unsupported_expression')", name="ck_ad_v4_app_group_member_union"),
        sa.CheckConstraint("manufacturer_state IN ('known','unknown','not_applicable')", name="ck_ad_v4_app_group_member_manufacturer_state"),
        sa.CheckConstraint("(manufacturer_state='known' AND manufacturer_value IS NOT NULL AND manufacturer_reason IS NULL AND manufacturer_temporal_scope IS NULL) OR (manufacturer_state='unknown' AND manufacturer_value IS NULL AND manufacturer_reason IN ('not_observed','unavailable','not_obtained','not_extracted','not_yet_reviewed','not_yet_verified','conflicting_evidence','source_ambiguous','unsupported_expression') AND manufacturer_temporal_scope IS NOT NULL) OR (manufacturer_state='not_applicable' AND manufacturer_value IS NULL AND manufacturer_reason IS NOT NULL AND char_length(manufacturer_reason) BETWEEN 1 AND 512 AND manufacturer_temporal_scope IS NOT NULL)", name="ck_ad_v4_app_group_member_manufacturer_union"),
        sa.CheckConstraint("canonical_ordinal>=0", name="ck_ad_v4_app_group_member_ordinal"),
        sa.UniqueConstraint("group_node_id", "member_key", name="uq_ad_v4_app_group_member_key"),
        sa.UniqueConstraint("group_node_id", "canonical_ordinal", name="uq_ad_v4_app_group_member_ordinal"),
    )
    op.create_index("ix_ad_v4_app_group_member_parent", "ad_v4_candidate_app_designation_group_members", ["group_node_id", "canonical_ordinal"])


def _create_rule_tables() -> None:
    op.create_table(
        "ad_v4_candidate_app_rules",
        _id("semantic_node_id", primary=True), _id("projection_id"), _id("proposal_id"),
        sa.Column("rule_key", sa.String(128), nullable=False), _id("scope_expression_node_id"),
        sa.Column("condition_presence", sa.String(32), nullable=False),
        sa.Column("condition_expression_node_id", sa.String(36), nullable=True),
        sa.Column("evaluator_contract", sa.String(64), nullable=False),
        *_typed_owner_fks(),
        sa.ForeignKeyConstraint(["scope_expression_node_id", "projection_id", "proposal_id"], ["ad_v4_candidate_app_semantic_nodes.id", "ad_v4_candidate_app_semantic_nodes.projection_id", "ad_v4_candidate_app_semantic_nodes.proposal_id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["condition_expression_node_id", "projection_id", "proposal_id"], ["ad_v4_candidate_app_semantic_nodes.id", "ad_v4_candidate_app_semantic_nodes.projection_id", "ad_v4_candidate_app_semantic_nodes.proposal_id"], ondelete="RESTRICT"),
        sa.CheckConstraint("condition_presence IN ('property_absent','present')", name="ck_ad_v4_app_rule_condition_presence"),
        sa.CheckConstraint("(condition_presence='present')=(condition_expression_node_id IS NOT NULL)", name="ck_ad_v4_app_rule_condition_union"),
        sa.CheckConstraint("evaluator_contract='none'", name="ck_ad_v4_app_rule_evaluator"),
        sa.UniqueConstraint("projection_id", "rule_key", name="uq_ad_v4_app_rule_key"),
    )
    op.create_table(
        "ad_v4_candidate_app_expressions",
        _id("semantic_node_id", primary=True), _id("projection_id"), _id("proposal_id"),
        _id("owning_rule_node_id"), sa.Column("expression_context", sa.String(16), nullable=False),
        sa.Column("expression_path", sa.Text(), nullable=False),
        sa.Column("expression_node_type", sa.String(32), nullable=False),
        sa.Column("result_domain", sa.String(32), nullable=False),
        sa.Column("evaluator_contract", sa.String(64), nullable=False),
        sa.Column("scope_node_id", sa.String(36), nullable=True),
        sa.Column("condition_node_id", sa.String(36), nullable=True),
        sa.Column("referenced_rule_node_id", sa.String(36), nullable=True),
        *_typed_owner_fks(),
        sa.ForeignKeyConstraint(["owning_rule_node_id", "projection_id", "proposal_id"], ["ad_v4_candidate_app_semantic_nodes.id", "ad_v4_candidate_app_semantic_nodes.projection_id", "ad_v4_candidate_app_semantic_nodes.proposal_id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["scope_node_id", "projection_id", "proposal_id"], ["ad_v4_candidate_app_semantic_nodes.id", "ad_v4_candidate_app_semantic_nodes.projection_id", "ad_v4_candidate_app_semantic_nodes.proposal_id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["condition_node_id", "projection_id", "proposal_id"], ["ad_v4_candidate_app_semantic_nodes.id", "ad_v4_candidate_app_semantic_nodes.projection_id", "ad_v4_candidate_app_semantic_nodes.proposal_id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["referenced_rule_node_id", "projection_id", "proposal_id"], ["ad_v4_candidate_app_semantic_nodes.id", "ad_v4_candidate_app_semantic_nodes.projection_id", "ad_v4_candidate_app_semantic_nodes.proposal_id"], ondelete="RESTRICT"),
        sa.CheckConstraint("expression_context IN ('scope','condition')", name="ck_ad_v4_app_expression_context"),
        sa.CheckConstraint("expression_node_type IN ('scope_ref','predicate_ref','rule_ref','not','all','any')", name="ck_ad_v4_app_expression_type"),
        sa.CheckConstraint("result_domain='true_false_unknown' AND evaluator_contract='none'", name="ck_ad_v4_app_expression_evaluator"),
        sa.CheckConstraint("(expression_node_type='scope_ref' AND scope_node_id IS NOT NULL AND condition_node_id IS NULL AND referenced_rule_node_id IS NULL) OR (expression_node_type='predicate_ref' AND scope_node_id IS NULL AND condition_node_id IS NOT NULL AND referenced_rule_node_id IS NULL) OR (expression_node_type='rule_ref' AND scope_node_id IS NULL AND condition_node_id IS NULL AND referenced_rule_node_id IS NOT NULL) OR (expression_node_type IN ('not','all','any') AND scope_node_id IS NULL AND condition_node_id IS NULL AND referenced_rule_node_id IS NULL)", name="ck_ad_v4_app_expression_reference_union"),
        sa.UniqueConstraint("owning_rule_node_id", "expression_context", "expression_path", name="uq_ad_v4_app_expression_path"),
    )
    op.create_table(
        "ad_v4_candidate_app_expression_edges",
        _id("projection_id"), _id("proposal_id"), _id("owning_rule_node_id"),
        sa.Column("expression_context", sa.String(16), nullable=False),
        _id("parent_expression_id", primary=True), _id("child_expression_id"),
        sa.Column("sequence", sa.Integer(), primary_key=True, nullable=False),
        sa.ForeignKeyConstraint(["projection_id", "proposal_id"], ["ad_v4_candidate_app_projections.id", "ad_v4_candidate_app_projections.proposal_id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["owning_rule_node_id", "projection_id", "proposal_id"], ["ad_v4_candidate_app_semantic_nodes.id", "ad_v4_candidate_app_semantic_nodes.projection_id", "ad_v4_candidate_app_semantic_nodes.proposal_id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["parent_expression_id", "projection_id", "proposal_id"], ["ad_v4_candidate_app_semantic_nodes.id", "ad_v4_candidate_app_semantic_nodes.projection_id", "ad_v4_candidate_app_semantic_nodes.proposal_id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["child_expression_id", "projection_id", "proposal_id"], ["ad_v4_candidate_app_semantic_nodes.id", "ad_v4_candidate_app_semantic_nodes.projection_id", "ad_v4_candidate_app_semantic_nodes.proposal_id"], ondelete="RESTRICT"),
        sa.CheckConstraint("expression_context IN ('scope','condition')", name="ck_ad_v4_app_expression_edge_context"),
        sa.CheckConstraint("sequence>=0", name="ck_ad_v4_app_expression_edge_sequence"),
        sa.UniqueConstraint("parent_expression_id", "child_expression_id", name="uq_ad_v4_app_expression_edge_pair"),
        sa.UniqueConstraint("child_expression_id", name="uq_ad_v4_app_expression_child"),
    )
    op.create_index("ix_ad_v4_app_expression_edge_owner", "ad_v4_candidate_app_expression_edges", ["owning_rule_node_id", "expression_context", "parent_expression_id", "sequence"])
    op.create_table(
        "ad_v4_candidate_app_rule_exclusions",
        _id("projection_id"), _id("proposal_id"),
        _id("rule_node_id", primary=True), _id("excluded_rule_node_id"),
        sa.Column("canonical_ordinal", sa.Integer(), primary_key=True, nullable=False),
        sa.ForeignKeyConstraint(["projection_id", "proposal_id"], ["ad_v4_candidate_app_projections.id", "ad_v4_candidate_app_projections.proposal_id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["rule_node_id", "projection_id", "proposal_id"], ["ad_v4_candidate_app_semantic_nodes.id", "ad_v4_candidate_app_semantic_nodes.projection_id", "ad_v4_candidate_app_semantic_nodes.proposal_id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["excluded_rule_node_id", "projection_id", "proposal_id"], ["ad_v4_candidate_app_semantic_nodes.id", "ad_v4_candidate_app_semantic_nodes.projection_id", "ad_v4_candidate_app_semantic_nodes.proposal_id"], ondelete="RESTRICT"),
        sa.CheckConstraint("canonical_ordinal>=0", name="ck_ad_v4_app_rule_exclusion_ordinal"),
        sa.UniqueConstraint("rule_node_id", "excluded_rule_node_id", name="uq_ad_v4_app_rule_exclusion_pair"),
    )


def _create_search_hint_tables() -> None:
    op.create_table(
        "ad_v4_candidate_app_search_hints",
        _id("semantic_node_id", primary=True), _id("projection_id"), _id("proposal_id"),
        sa.Column("hint_key", sa.String(128), nullable=False),
        sa.Column("product_role", sa.String(32), nullable=False),
        _id("source_display_assertion_node_id"),
        sa.Column("controlling", sa.Boolean(), nullable=False),
        sa.Column("exhaustive", sa.Boolean(), nullable=False),
        *_typed_owner_fks(),
        sa.ForeignKeyConstraint(["source_display_assertion_node_id", "projection_id", "proposal_id"], ["ad_v4_candidate_app_semantic_nodes.id", "ad_v4_candidate_app_semantic_nodes.projection_id", "ad_v4_candidate_app_semantic_nodes.proposal_id"], ondelete="RESTRICT"),
        sa.CheckConstraint("product_role IN ('airframe','engine','propeller','appliance','installed_part','modification')", name="ck_ad_v4_app_search_hint_role"),
        sa.CheckConstraint("controlling=false AND exhaustive=false", name="ck_ad_v4_app_search_hint_noncontrolling"),
        sa.UniqueConstraint("projection_id", "hint_key", name="uq_ad_v4_app_search_hint_key"),
    )
    op.create_table(
        "ad_v4_candidate_app_search_hint_groups",
        _id("semantic_node_id", primary=True), _id("projection_id"), _id("proposal_id"),
        _id("hint_node_id"), sa.Column("group_key", sa.String(128), nullable=False),
        _id("manufacturer_assertion_node_id"),
        sa.Column("manufacturer_state", sa.String(32), nullable=False),
        sa.Column("manufacturer_value", sa.Text(), nullable=True),
        sa.Column("manufacturer_reason", sa.Text(), nullable=True),
        sa.Column("manufacturer_temporal_scope", sa.String(64), nullable=True),
        sa.Column("association", sa.String(32), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("temporal_scope", sa.String(64), nullable=True),
        sa.Column("canonical_ordinal", sa.Integer(), nullable=False),
        *_typed_owner_fks(),
        sa.ForeignKeyConstraint(["hint_node_id", "projection_id", "proposal_id"], ["ad_v4_candidate_app_semantic_nodes.id", "ad_v4_candidate_app_semantic_nodes.projection_id", "ad_v4_candidate_app_semantic_nodes.proposal_id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["manufacturer_assertion_node_id", "projection_id", "proposal_id"], ["ad_v4_candidate_app_semantic_nodes.id", "ad_v4_candidate_app_semantic_nodes.projection_id", "ad_v4_candidate_app_semantic_nodes.proposal_id"], ondelete="RESTRICT"),
        sa.CheckConstraint("association IN ('paired','source_group','unknown')", name="ck_ad_v4_app_search_hint_group_association"),
        sa.CheckConstraint("(association='unknown' AND reason IN ('not_observed','unavailable','not_obtained','not_extracted','not_yet_reviewed','not_yet_verified','conflicting_evidence','source_ambiguous','unsupported_expression') AND temporal_scope IS NOT NULL) OR (association<>'unknown' AND reason IS NULL AND temporal_scope IS NULL)", name="ck_ad_v4_app_search_hint_group_unknown"),
        sa.CheckConstraint("temporal_scope IS NULL OR temporal_scope IN ('directive_version','publication_version','at_applicability_evaluation','at_compliance_evaluation','source_observation')", name="ck_ad_v4_app_search_hint_group_temporal"),
        sa.CheckConstraint("manufacturer_state IN ('known','unknown','not_applicable')", name="ck_ad_v4_app_search_hint_group_manufacturer_state"),
        sa.CheckConstraint("(manufacturer_state='known' AND manufacturer_value IS NOT NULL AND manufacturer_reason IS NULL AND manufacturer_temporal_scope IS NULL) OR (manufacturer_state='unknown' AND manufacturer_value IS NULL AND manufacturer_reason IN ('not_observed','unavailable','not_obtained','not_extracted','not_yet_reviewed','not_yet_verified','conflicting_evidence','source_ambiguous','unsupported_expression') AND manufacturer_temporal_scope IS NOT NULL) OR (manufacturer_state='not_applicable' AND manufacturer_value IS NULL AND manufacturer_reason IS NOT NULL AND char_length(manufacturer_reason) BETWEEN 1 AND 512 AND manufacturer_temporal_scope IS NOT NULL)", name="ck_ad_v4_app_search_hint_group_manufacturer_union"),
        sa.CheckConstraint("manufacturer_temporal_scope IS NULL OR manufacturer_temporal_scope IN ('directive_version','publication_version','at_applicability_evaluation','at_compliance_evaluation','source_observation')", name="ck_ad_v4_app_search_hint_group_manufacturer_temporal"),
        sa.CheckConstraint("canonical_ordinal>=0", name="ck_ad_v4_app_search_hint_group_ordinal"),
        sa.UniqueConstraint("hint_node_id", "group_key", name="uq_ad_v4_app_search_hint_group_key"),
        sa.UniqueConstraint("hint_node_id", "canonical_ordinal", name="uq_ad_v4_app_search_hint_group_ordinal"),
    )
    op.create_index("ix_ad_v4_app_search_hint_group_parent", "ad_v4_candidate_app_search_hint_groups", ["hint_node_id", "canonical_ordinal"])
    op.create_table(
        "ad_v4_candidate_app_search_hint_members",
        _id("semantic_node_id", primary=True), _id("projection_id"), _id("proposal_id"),
        _id("group_node_id"), sa.Column("member_key", sa.String(128), nullable=False),
        sa.Column("designation_kind", sa.String(32), nullable=False),
        sa.Column("source_designation", sa.Text(), nullable=True),
        sa.Column("expression_text", sa.Text(), nullable=True),
        _id("manufacturer_assertion_node_id"),
        sa.Column("manufacturer_state", sa.String(32), nullable=False),
        sa.Column("manufacturer_value", sa.Text(), nullable=True),
        sa.Column("manufacturer_reason", sa.Text(), nullable=True),
        sa.Column("manufacturer_temporal_scope", sa.String(64), nullable=True),
        sa.Column("evaluation_state", sa.String(32), nullable=True),
        sa.Column("evaluation_reason", sa.String(64), nullable=True),
        sa.Column("canonical_ordinal", sa.Integer(), nullable=False),
        _id("designation_identity_mapping_node_id"),
        *_typed_owner_fks(),
        sa.ForeignKeyConstraint(["group_node_id", "projection_id", "proposal_id"], ["ad_v4_candidate_app_semantic_nodes.id", "ad_v4_candidate_app_semantic_nodes.projection_id", "ad_v4_candidate_app_semantic_nodes.proposal_id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["manufacturer_assertion_node_id", "projection_id", "proposal_id"], ["ad_v4_candidate_app_semantic_nodes.id", "ad_v4_candidate_app_semantic_nodes.projection_id", "ad_v4_candidate_app_semantic_nodes.proposal_id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["designation_identity_mapping_node_id", "projection_id", "proposal_id"], ["ad_v4_candidate_app_semantic_nodes.id", "ad_v4_candidate_app_semantic_nodes.projection_id", "ad_v4_candidate_app_semantic_nodes.proposal_id"], ondelete="RESTRICT"),
        sa.CheckConstraint("designation_kind IN ('model','series_expression')", name="ck_ad_v4_app_search_hint_member_kind"),
        sa.CheckConstraint("(designation_kind='model' AND source_designation IS NOT NULL AND expression_text IS NULL AND evaluation_state IS NULL AND evaluation_reason IS NULL) OR (designation_kind='series_expression' AND source_designation IS NULL AND expression_text IS NOT NULL AND evaluation_state='unevaluated' AND evaluation_reason='unsupported_expression')", name="ck_ad_v4_app_search_hint_member_union"),
        sa.CheckConstraint("(source_designation IS NULL OR char_length(source_designation) BETWEEN 1 AND 512) AND (expression_text IS NULL OR char_length(expression_text) BETWEEN 1 AND 512)", name="ck_ad_v4_app_search_hint_member_text_length"),
        sa.CheckConstraint("manufacturer_state IN ('known','unknown','not_applicable')", name="ck_ad_v4_app_search_hint_member_manufacturer_state"),
        sa.CheckConstraint("(manufacturer_state='known' AND manufacturer_value IS NOT NULL AND manufacturer_reason IS NULL AND manufacturer_temporal_scope IS NULL) OR (manufacturer_state='unknown' AND manufacturer_value IS NULL AND manufacturer_reason IN ('not_observed','unavailable','not_obtained','not_extracted','not_yet_reviewed','not_yet_verified','conflicting_evidence','source_ambiguous','unsupported_expression') AND manufacturer_temporal_scope IS NOT NULL) OR (manufacturer_state='not_applicable' AND manufacturer_value IS NULL AND manufacturer_reason IS NOT NULL AND char_length(manufacturer_reason) BETWEEN 1 AND 512 AND manufacturer_temporal_scope IS NOT NULL)", name="ck_ad_v4_app_search_hint_member_manufacturer_union"),
        sa.CheckConstraint("manufacturer_temporal_scope IS NULL OR manufacturer_temporal_scope IN ('directive_version','publication_version','at_applicability_evaluation','at_compliance_evaluation','source_observation')", name="ck_ad_v4_app_search_hint_member_manufacturer_temporal"),
        sa.CheckConstraint("canonical_ordinal>=0", name="ck_ad_v4_app_search_hint_member_ordinal"),
        sa.UniqueConstraint("group_node_id", "member_key", name="uq_ad_v4_app_search_hint_member_key"),
        sa.UniqueConstraint("group_node_id", "canonical_ordinal", name="uq_ad_v4_app_search_hint_member_ordinal"),
    )
    op.create_index("ix_ad_v4_app_search_hint_member_parent", "ad_v4_candidate_app_search_hint_members", ["group_node_id", "canonical_ordinal"])


def _create_correction_tables() -> None:
    op.create_table(
        "ad_v4_candidate_corrections", _id("id", primary=True), sa.Column("identity_hash", sa.String(64), nullable=False, unique=True),
        _id("proposal_id"), sa.Column("correction_key", sa.String(128), nullable=False), sa.Column("correction_type", sa.String(64), nullable=False),
        sa.Column("original_document_ref_key", sa.String(128), nullable=False), sa.Column("correcting_document_ref_key", sa.String(128), nullable=False),
        sa.Column("original_document_identity_hash", sa.String(64), nullable=False), sa.Column("correcting_document_identity_hash", sa.String(64), nullable=False),
        sa.Column("canonical_hash", sa.String(64), nullable=False), sa.Column("canonical_ordinal", sa.Integer(), nullable=False),
        sa.Column("foundation_version", sa.String(64), nullable=False), sa.Column("generation", sa.Integer(), nullable=False),
        sa.Column("expected_ref_count", sa.Integer(), nullable=False), sa.Column("expected_evidence_count", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["proposal_id"], ["ad_v4_candidate_proposals.id"], ondelete="RESTRICT"),
        sa.CheckConstraint("canonical_ordinal>=0", name="ck_ad_v4_correction_ordinal_nonnegative"),
        sa.UniqueConstraint("id", "proposal_id", name="uq_ad_v4_correction_parent_identity"),
        sa.UniqueConstraint("proposal_id", "correction_key", name="uq_ad_v4_correction_key"),
        sa.UniqueConstraint("proposal_id", "canonical_ordinal", name="uq_ad_v4_correction_ordinal"),
    )
    op.create_table(
        "ad_v4_candidate_correction_refs", _id("id", primary=True), _id("correction_id"), _id("proposal_id"),
        sa.Column("canonical_ordinal", sa.Integer(), nullable=False), sa.Column("namespace", sa.String(64), nullable=False),
        sa.Column("semantic_key", sa.String(128), nullable=False), sa.Column("owner_slice", sa.String(32), nullable=False),
        sa.Column("reference_hash", sa.String(64), nullable=False),
        sa.ForeignKeyConstraint(["correction_id"], ["ad_v4_candidate_corrections.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["correction_id", "proposal_id"], ["ad_v4_candidate_corrections.id", "ad_v4_candidate_corrections.proposal_id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["proposal_id"], ["ad_v4_candidate_proposals.id"], ondelete="RESTRICT"),
        sa.CheckConstraint("canonical_ordinal>=0", name="ck_ad_v4_correction_ref_ordinal_nonnegative"),
        sa.UniqueConstraint("id", "proposal_id", name="uq_ad_v4_correction_ref_parent_identity"),
        sa.UniqueConstraint("correction_id", "namespace", "semantic_key", name="uq_ad_v4_correction_ref_key"),
        sa.UniqueConstraint("correction_id", "canonical_ordinal", name="uq_ad_v4_correction_ref_ordinal"),
    )
    op.create_table(
        "ad_v4_candidate_correction_semantic_bindings", _id("id", primary=True), _id("correction_ref_id"), _id("proposal_id"), _id("projection_id"), _id("semantic_node_id"),
        sa.Column("binding_slice", sa.String(32), nullable=False), sa.Column("generation", sa.Integer(), nullable=False), sa.Column("binding_hash", sa.String(64), nullable=False, unique=True),
        sa.ForeignKeyConstraint(["correction_ref_id"], ["ad_v4_candidate_correction_refs.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["correction_ref_id", "proposal_id"], ["ad_v4_candidate_correction_refs.id", "ad_v4_candidate_correction_refs.proposal_id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["proposal_id"], ["ad_v4_candidate_proposals.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["projection_id"], ["ad_v4_candidate_app_projections.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["semantic_node_id"], ["ad_v4_candidate_app_semantic_nodes.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["projection_id", "proposal_id"], ["ad_v4_candidate_app_projections.id", "ad_v4_candidate_app_projections.proposal_id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["semantic_node_id", "projection_id", "proposal_id"], ["ad_v4_candidate_app_semantic_nodes.id", "ad_v4_candidate_app_semantic_nodes.projection_id", "ad_v4_candidate_app_semantic_nodes.proposal_id"], ondelete="RESTRICT"),
        sa.UniqueConstraint("correction_ref_id", name="uq_ad_v4_correction_semantic_ref"),
    )
    op.create_table(
        "ad_v4_candidate_correction_evidence_links", _id("id", primary=True), _id("correction_id"), _id("proposal_id"), _id("candidate_binding_id"),
        sa.Column("evidence_key", sa.String(128), nullable=False), sa.Column("canonical_ordinal", sa.Integer(), nullable=False), sa.Column("link_hash", sa.String(64), nullable=False),
        sa.ForeignKeyConstraint(["correction_id"], ["ad_v4_candidate_corrections.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["correction_id", "proposal_id"], ["ad_v4_candidate_corrections.id", "ad_v4_candidate_corrections.proposal_id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["proposal_id", "candidate_binding_id", "evidence_key"], ["ad_v4_candidate_evidence_bindings.proposal_id", "ad_v4_candidate_evidence_bindings.id", "ad_v4_candidate_evidence_bindings.evidence_key"], ondelete="RESTRICT"),
        sa.CheckConstraint("canonical_ordinal>=0", name="ck_ad_v4_correction_evidence_ordinal_nonnegative"),
        sa.UniqueConstraint("correction_id", "evidence_key", name="uq_ad_v4_correction_evidence"),
        sa.UniqueConstraint("correction_id", "canonical_ordinal", name="uq_ad_v4_correction_evidence_ordinal"),
    )


def _create_dependency_and_event_tables() -> None:
    op.create_table(
        "ad_v4_candidate_app_change_dependencies", _id("id", primary=True), _id("projection_id"), _id("proposal_id"), _id("semantic_node_id"),
        sa.Column("dependency_key", sa.String(255), nullable=False), sa.Column("dependency_kind", sa.String(64), nullable=False),
        sa.Column("predecessor_ad_number", sa.String(64), nullable=False), sa.Column("successor_ad_number", sa.String(64), nullable=False),
        sa.Column("resolution_state", sa.String(32), nullable=False), sa.Column("unresolved_reason", sa.String(64), nullable=True),
        sa.Column("target_projection_id", sa.String(36), nullable=True), sa.Column("source_dependency_id", sa.String(36), nullable=True),
        sa.Column("dependency_hash", sa.String(64), nullable=False, unique=True),
        sa.ForeignKeyConstraint(["projection_id"], ["ad_v4_candidate_app_projections.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["proposal_id"], ["ad_v4_candidate_proposals.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["projection_id", "proposal_id"], ["ad_v4_candidate_app_projections.id", "ad_v4_candidate_app_projections.proposal_id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["semantic_node_id"], ["ad_v4_candidate_app_semantic_nodes.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["semantic_node_id", "projection_id", "proposal_id"], ["ad_v4_candidate_app_semantic_nodes.id", "ad_v4_candidate_app_semantic_nodes.projection_id", "ad_v4_candidate_app_semantic_nodes.proposal_id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["target_projection_id"], ["ad_v4_candidate_app_projections.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["source_dependency_id"], ["ad_v4_candidate_app_change_dependencies.id"], ondelete="RESTRICT"),
        sa.CheckConstraint("dependency_kind IN ('outgoing_supersedes','outgoing_partially_supersedes','incoming_supersession_signal')", name="ck_ad_v4_app_dependency_kind"),
        sa.UniqueConstraint("id", "projection_id", name="uq_ad_v4_app_dependency_parent_identity"),
        sa.UniqueConstraint("projection_id", "dependency_key", name="uq_ad_v4_app_dependency"),
    )
    op.create_table(
        "ad_v4_candidate_app_projection_events", _id("id", primary=True), _id("projection_id"), _id("proposal_id"),
        sa.Column("sequence_number", sa.Integer(), nullable=False), sa.Column("event_type", sa.String(64), nullable=False),
        sa.Column("reason_code", sa.String(64), nullable=False), sa.Column("causing_request_id", sa.String(36), nullable=True),
        sa.Column("causing_relationship_id", sa.String(36), nullable=True), sa.Column("causing_lifecycle_event_id", sa.String(36), nullable=True),
        sa.Column("causing_dependency_id", sa.String(36), nullable=True), sa.Column("predecessor_event_hash", sa.String(64), nullable=True),
        sa.Column("canonical_bytes", sa.LargeBinary(), nullable=False), sa.Column("event_hash", sa.String(64), nullable=False),
        sa.Column("actor_kind", sa.String(32), nullable=False), sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["projection_id"], ["ad_v4_candidate_app_projections.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["proposal_id"], ["ad_v4_candidate_proposals.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["projection_id", "proposal_id"], ["ad_v4_candidate_app_projections.id", "ad_v4_candidate_app_projections.proposal_id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["causing_request_id"], ["ad_v4_candidate_app_materialization_requests.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["causing_relationship_id"], ["ad_v4_candidate_submission_relationships.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["causing_lifecycle_event_id"], ["ad_evidence_fragment_lifecycle_events.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["causing_dependency_id"], ["ad_v4_candidate_app_change_dependencies.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["causing_dependency_id", "projection_id"], ["ad_v4_candidate_app_change_dependencies.id", "ad_v4_candidate_app_change_dependencies.projection_id"], ondelete="RESTRICT", name="fk_ad_v4_app_event_same_projection_dependency"),
        sa.UniqueConstraint("projection_id", "sequence_number", name="uq_ad_v4_app_event_sequence"),
        sa.UniqueConstraint("projection_id", "event_hash", name="uq_ad_v4_app_event_hash"),
    )
    op.create_index("ix_ad_v4_app_event_fold", "ad_v4_candidate_app_projection_events", ["projection_id", "sequence_number"])
    op.create_index("uq_ad_v4_app_event_dependency_cause", "ad_v4_candidate_app_projection_events", ["projection_id", "event_type", "causing_dependency_id"], unique=True, postgresql_where=sa.text("causing_dependency_id IS NOT NULL"))
    op.create_index("uq_ad_v4_app_event_relationship_cause", "ad_v4_candidate_app_projection_events", ["projection_id", "event_type", "causing_relationship_id"], unique=True, postgresql_where=sa.text("causing_relationship_id IS NOT NULL"))
    op.create_index("uq_ad_v4_app_event_lifecycle_cause", "ad_v4_candidate_app_projection_events", ["projection_id", "event_type", "causing_lifecycle_event_id"], unique=True, postgresql_where=sa.text("causing_lifecycle_event_id IS NOT NULL"))


def _replace_v4_validation_functions() -> None:
    op.execute("""
    CREATE OR REPLACE FUNCTION paprnav_v4_capabilities() RETURNS jsonb AS $$
      SELECT jsonb_build_object(
        'revision','20260907_0027',
        'validatorPairs',jsonb_build_array(
          jsonb_build_array('paprnav-ad-v4-validator-1','paprnav-ad-v4-c14n-1'),
          jsonb_build_array('paprnav-ad-v4-validator-2','paprnav-ad-v4-c14n-2')),
        'materializers',jsonb_build_array('paprnav-ad-v4-app-materializer-2'),
        'validator2_write_enabled',(SELECT enabled FROM ad_v4_feature_gates WHERE gate_key='validator2_write_enabled'),
        'materializer3a_enabled',(SELECT enabled FROM ad_v4_feature_gates WHERE gate_key='materializer3a_enabled'));
    $$ LANGUAGE sql STABLE
    """)
    op.execute("""
    CREATE OR REPLACE FUNCTION paprnav_set_v4_feature_gate(p_key text,p_enabled boolean,p_actor text) RETURNS void AS $$
    BEGIN
      IF p_key NOT IN ('validator2_write_enabled','materializer3a_enabled') OR length(trim(p_actor))=0 THEN
        RAISE EXCEPTION 'invalid V4 feature gate change';
      END IF;
      UPDATE ad_v4_feature_gates SET enabled=p_enabled,changed_at=now(),changed_by=p_actor WHERE gate_key=p_key;
      IF NOT FOUND THEN RAISE EXCEPTION 'unknown V4 feature gate'; END IF;
    END; $$ LANGUAGE plpgsql
    """)
    op.execute("""
    CREATE OR REPLACE FUNCTION paprnav_v4_validate_proposal() RETURNS trigger AS $$
    DECLARE domain text;
    BEGIN
      IF (NEW.validator_version,NEW.canonicalization_version) NOT IN (
        ('paprnav-ad-v4-validator-1','paprnav-ad-v4-c14n-1'),
        ('paprnav-ad-v4-validator-2','paprnav-ad-v4-c14n-2')) THEN
        RAISE EXCEPTION 'V4 unsupported validator/canonicalization pair';
      END IF;
      domain := CASE WHEN NEW.validator_version='paprnav-ad-v4-validator-2'
        THEN 'paprnav:ad_extraction_v4:proposal:paprnav-ad-v4-c14n-2'
        ELSE 'paprnav:ad_extraction_v4:proposal:paprnav-ad-v4-c14n-1' END;
      IF convert_from(NEW.canonical_bytes,'UTF8')::jsonb IS DISTINCT FROM NEW.parsed_json::jsonb
         OR NEW.canonical_hash<>encode(sha256(convert_to(domain,'UTF8')||decode('00','hex')||NEW.canonical_bytes),'hex')
         OR NEW.schema_version<>'ad_extraction_v4' OR NEW.gate<>'candidate_only'
         OR NEW.parsed_json::jsonb->>'schemaVersion'<>NEW.schema_version
         OR NEW.parsed_json::jsonb->'directiveIdentity'->>'directiveId'<>NEW.directive_id THEN
        RAISE EXCEPTION 'V4 proposal envelope/relational identity mismatch';
      END IF;
      RETURN NEW;
    END; $$ LANGUAGE plpgsql
    """)
    op.execute("""
    CREATE OR REPLACE FUNCTION paprnav_v4_validate_relationship() RETURNS trigger AS $$
    DECLARE s ad_v4_candidate_submissions%ROWTYPE; p ad_v4_candidate_proposals%ROWTYPE; pred ad_v4_candidate_proposals%ROWTYPE; payload jsonb; domain text; version text;
    BEGIN
      SELECT * INTO s FROM ad_v4_candidate_submissions WHERE id=NEW.submission_id;
      SELECT * INTO p FROM ad_v4_candidate_proposals WHERE id=s.proposal_id;
      SELECT * INTO pred FROM ad_v4_candidate_proposals WHERE id=NEW.predecessor_proposal_id;
      domain:=CASE WHEN NEW.validator_version='paprnav-ad-v4-validator-2' THEN 'paprnav:ad_extraction_v4:submission-relationship:2' ELSE 'paprnav:ad_extraction_v4:submission-relationship:1' END;
      version:=CASE WHEN NEW.validator_version='paprnav-ad-v4-validator-2' THEN 'ad-v4-submission-relationship-v2' ELSE 'ad-v4-submission-relationship-v1' END;
      payload:=convert_from(NEW.canonical_bytes,'UTF8')::jsonb;
      IF s.id IS NULL OR p.id IS NULL OR pred.id IS NULL OR p.directive_id<>pred.directive_id OR p.id=pred.id
         OR NEW.validator_version<>s.validator_version OR NEW.canonicalization_version<>s.canonicalization_version
         OR NEW.relationship_hash<>encode(sha256(convert_to(domain,'UTF8')||decode('00','hex')||NEW.canonical_bytes),'hex')
         OR payload->>'version'<>version OR payload->>'submissionId'<>NEW.submission_id
         OR payload->>'relationshipKey'<>NEW.relationship_key OR payload->>'relationType'<>NEW.relation_type
         OR payload->>'predecessorProposalId'<>NEW.predecessor_proposal_id THEN
        RAISE EXCEPTION 'V4 relationship envelope mismatch';
      END IF;
      IF NEW.validator_version='paprnav-ad-v4-validator-2' AND (payload->>'validatorVersion'<>NEW.validator_version OR payload->>'canonicalizationVersion'<>NEW.canonicalization_version) THEN
        RAISE EXCEPTION 'V4 relationship v2 version mismatch';
      END IF;
      RETURN NEW;
    END; $$ LANGUAGE plpgsql
    """)
    op.execute("""
    CREATE OR REPLACE FUNCTION paprnav_v4_validate_event() RETURNS trigger AS $$
    DECLARE p ad_v4_candidate_proposals%ROWTYPE; s ad_v4_candidate_submissions%ROWTYPE; payload jsonb; domain text; version text;
    BEGIN
      SELECT * INTO p FROM ad_v4_candidate_proposals WHERE id=NEW.proposal_id;
      SELECT * INTO s FROM ad_v4_candidate_submissions WHERE id=NEW.created_by_submission_id;
      domain:=CASE WHEN NEW.validator_version='paprnav-ad-v4-validator-2' THEN 'paprnav:ad_extraction_v4:candidate-event:2' ELSE 'paprnav:ad_extraction_v4:candidate-event:1' END;
      version:=CASE WHEN NEW.validator_version='paprnav-ad-v4-validator-2' THEN 'ad-v4-candidate-created-v2' ELSE 'ad-v4-candidate-created-v1' END;
      payload:=convert_from(NEW.canonical_bytes,'UTF8')::jsonb;
      IF p.id IS NULL OR s.id IS NULL OR s.proposal_id<>p.id OR NEW.directive_id<>p.directive_id
         OR NEW.validator_version<>p.validator_version OR NEW.canonicalization_version<>p.canonicalization_version
         OR NEW.validator_version<>s.validator_version OR NEW.canonicalization_version<>s.canonicalization_version
         OR NEW.proposal_canonical_hash<>p.canonical_hash OR NEW.evidence_binding_hash<>p.evidence_binding_hash
         OR NEW.event_hash<>encode(sha256(convert_to(domain,'UTF8')||decode('00','hex')||NEW.canonical_bytes),'hex')
         OR payload->>'version'<>version OR payload->>'proposalId'<>NEW.proposal_id OR payload->>'createdBySubmissionId'<>NEW.created_by_submission_id THEN
        RAISE EXCEPTION 'V4 event envelope mismatch';
      END IF;
      IF NEW.validator_version='paprnav-ad-v4-validator-2' AND (payload->>'validatorVersion'<>NEW.validator_version OR payload->>'canonicalizationVersion'<>NEW.canonicalization_version) THEN
        RAISE EXCEPTION 'V4 event v2 version mismatch';
      END IF;
      RETURN NEW;
    END; $$ LANGUAGE plpgsql
    """)
    op.execute("""
    CREATE OR REPLACE FUNCTION paprnav_v4_validate_binding() RETURNS trigger AS $$
    DECLARE p ad_v4_candidate_proposals%ROWTYPE; f ad_evidence_fragments%ROWTYPE; e ad_evidence_fragment_lifecycle_events%ROWTYPE; n integer; declared jsonb;
    BEGIN
      SELECT * INTO p FROM ad_v4_candidate_proposals WHERE id=NEW.proposal_id;
      SELECT * INTO f FROM ad_evidence_fragments WHERE id=NEW.fragment_id FOR UPDATE;
      SELECT count(*) INTO n FROM ad_evidence_fragment_lifecycle_events WHERE fragment_id=NEW.fragment_id;
      SELECT * INTO e FROM ad_evidence_fragment_lifecycle_events WHERE id=NEW.admitted_event_id AND fragment_id=NEW.fragment_id;
      declared:=p.parsed_json::jsonb->'evidenceBindings'->NEW.evidence_key;
      IF p.id IS NULL OR NEW.validator_version<>p.validator_version OR NEW.canonicalization_version<>p.canonicalization_version
         OR f.id IS NULL OR f.directive_id<>NEW.directive_id OR f.fragment_hash<>NEW.fragment_hash
         OR n<>1 OR e.event_type<>'admitted' OR e.sequence_number<>0 OR e.predecessor_event_hash IS NOT NULL OR e.event_hash<>NEW.admitted_event_hash
         OR p.directive_id<>NEW.directive_id OR declared IS NULL OR declared->>'fragmentId'<>NEW.fragment_id OR declared->>'fragmentHash'<>NEW.fragment_hash THEN
        RAISE EXCEPTION 'V4 evidence binding mismatch';
      END IF;
      RETURN NEW;
    END; $$ LANGUAGE plpgsql
    """)
    op.execute("""
    CREATE OR REPLACE FUNCTION paprnav_v4_require_binding_parent_complete() RETURNS trigger AS $$
    DECLARE p ad_v4_candidate_proposals%ROWTYPE; expected jsonb; payload jsonb; version text;
    BEGIN
      SELECT * INTO p FROM ad_v4_candidate_proposals WHERE id=NEW.proposal_id;
      SELECT coalesce(jsonb_agg(jsonb_build_object('evidenceKey',b.evidence_key,'fragmentId',b.fragment_id,'fragmentHash',b.fragment_hash,'admittedEventId',b.admitted_event_id,'admittedEventHash',b.admitted_event_hash) ORDER BY b.evidence_key),'[]'::jsonb)
        INTO expected FROM ad_v4_candidate_evidence_bindings b WHERE b.proposal_id=NEW.proposal_id;
      payload:=convert_from(p.evidence_binding_bytes,'UTF8')::jsonb;
      version:=CASE WHEN p.validator_version='paprnav-ad-v4-validator-2' THEN 'ad-v4-evidence-bindings-v2' ELSE 'ad-v4-evidence-bindings-v1' END;
      IF p.id IS NULL OR payload->>'version'<>version OR payload->'bindings'<>expected
         OR (SELECT count(*) FROM ad_v4_candidate_evidence_bindings WHERE proposal_id=p.id)<>p.binding_count
         OR (p.validator_version='paprnav-ad-v4-validator-2' AND (payload->>'validatorVersion'<>p.validator_version OR payload->>'canonicalizationVersion'<>p.canonicalization_version)) THEN
        RAISE EXCEPTION 'V4 proposal binding set is incomplete';
      END IF;
      RETURN NULL;
    END; $$ LANGUAGE plpgsql
    """)
    op.execute("""
    CREATE OR REPLACE FUNCTION paprnav_v4_validate_submission() RETURNS trigger AS $$
    DECLARE p ad_v4_candidate_proposals%ROWTYPE; m organization_memberships%ROWTYPE; u users%ROWTYPE; payload jsonb; domain text; version text;
    BEGIN
      SELECT * INTO p FROM ad_v4_candidate_proposals WHERE id=NEW.proposal_id;
      SELECT * INTO m FROM organization_memberships WHERE id=NEW.authorizing_membership_id FOR UPDATE;
      SELECT * INTO u FROM users WHERE id=NEW.actor_user_id FOR UPDATE;
      domain:=CASE WHEN NEW.validator_version='paprnav-ad-v4-validator-2' THEN 'paprnav:ad_extraction_v4:submission:2' ELSE 'paprnav:ad_extraction_v4:submission:1' END;
      version:=CASE WHEN NEW.validator_version='paprnav-ad-v4-validator-2' THEN 'ad-v4-submission-v2' ELSE 'ad-v4-submission-v1' END;
      payload:=convert_from(NEW.request_canonical_bytes,'UTF8')::jsonb;
      IF p.id IS NULL OR NEW.validator_version<>p.validator_version OR NEW.canonicalization_version<>p.canonicalization_version
         OR m.id IS NULL OR u.id IS NULL OR u.status<>'active' OR m.user_id<>NEW.actor_user_id OR m.organization_id<>NEW.organization_id
         OR m.role<>'platform_admin' OR m.status<>'active' OR NEW.actor_role<>m.role OR NEW.actor_status<>m.status
         OR p.directive_id<>NEW.directive_id OR payload->>'version'<>version OR payload->>'proposalCanonicalHash'<>p.canonical_hash
         OR NEW.request_hash<>encode(sha256(convert_to(domain,'UTF8')||decode('00','hex')||NEW.request_canonical_bytes),'hex') THEN
        RAISE EXCEPTION 'V4 submission authorization/envelope mismatch';
      END IF;
      IF NEW.validator_version='paprnav-ad-v4-validator-2' AND (payload->>'validatorVersion'<>NEW.validator_version OR payload->>'canonicalizationVersion'<>NEW.canonicalization_version) THEN
        RAISE EXCEPTION 'V4 submission v2 version envelope mismatch';
      END IF;
      RETURN NEW;
    END; $$ LANGUAGE plpgsql
    """)
    op.execute("""
    CREATE OR REPLACE FUNCTION paprnav_v4_require_complete_proposal() RETURNS trigger AS $$
    DECLARE expected jsonb; payload jsonb; version text;
    BEGIN
      SELECT coalesce(jsonb_agg(jsonb_build_object('evidenceKey',b.evidence_key,'fragmentId',b.fragment_id,'fragmentHash',b.fragment_hash,'admittedEventId',b.admitted_event_id,'admittedEventHash',b.admitted_event_hash) ORDER BY b.evidence_key),'[]'::jsonb)
        INTO expected FROM ad_v4_candidate_evidence_bindings b WHERE b.proposal_id=NEW.id;
      payload:=convert_from(NEW.evidence_binding_bytes,'UTF8')::jsonb;
      version:=CASE WHEN NEW.validator_version='paprnav-ad-v4-validator-2' THEN 'ad-v4-evidence-bindings-v2' ELSE 'ad-v4-evidence-bindings-v1' END;
      IF (SELECT count(*) FROM ad_v4_candidate_evidence_bindings WHERE proposal_id=NEW.id)<>NEW.binding_count
         OR (SELECT count(*) FROM ad_v4_candidate_proposal_events WHERE proposal_id=NEW.id AND event_type='candidate_created')<>1
         OR payload->>'version'<>version OR payload->'bindings'<>expected
         OR (NEW.validator_version='paprnav-ad-v4-validator-2' AND (payload->>'validatorVersion'<>NEW.validator_version OR payload->>'canonicalizationVersion'<>NEW.canonicalization_version)) THEN
        RAISE EXCEPTION 'V4 proposal is incomplete';
      END IF;
      RETURN NULL;
    END; $$ LANGUAGE plpgsql
    """)


def _install_immutability() -> None:
    for table in APP_TABLES:
        if table == "ad_v4_feature_gates":
            continue
        op.execute(f"CREATE TRIGGER trg_{table}_immutable BEFORE UPDATE OR DELETE ON {table} FOR EACH ROW EXECUTE FUNCTION paprnav_v4_reject_mutation()")


def _install_projection_validation() -> None:
    op.execute(r"""
    CREATE FUNCTION paprnav_v4_lock_app_ad_numbers(p_proposal_id text) RETURNS void AS $$
    DECLARE ad_number text;
    BEGIN
      FOR ad_number IN
        SELECT DISTINCT value FROM (
          SELECT p.parsed_json::jsonb->'directiveIdentity'->'adNumber'->>'value' AS value
            FROM ad_v4_candidate_proposals p WHERE p.id=p_proposal_id
          UNION ALL
          SELECT relation->>'predecessorAdNumber'
            FROM ad_v4_candidate_proposals p,
                 jsonb_array_elements(p.parsed_json::jsonb->'supersessionRelations') relation
           WHERE p.id=p_proposal_id
          UNION ALL
          SELECT relation->>'successorAdNumber'
            FROM ad_v4_candidate_proposals p,
                 jsonb_array_elements(p.parsed_json::jsonb->'supersessionRelations') relation
           WHERE p.id=p_proposal_id
        ) numbers WHERE value IS NOT NULL ORDER BY value
      LOOP
        PERFORM pg_advisory_xact_lock(
          (('x'||substr(encode(sha256(
            convert_to('applicability-ad-resolution:'||ad_number,'UTF8')
          ),'hex'),1,16))::bit(64))::bigint
        );
      END LOOP;
    END; $$ LANGUAGE plpgsql
    """)
    op.execute("""
    CREATE FUNCTION paprnav_v4_validate_app_projection() RETURNS trigger AS $$
    DECLARE p ad_v4_candidate_proposals%ROWTYPE; subtree jsonb; envelope jsonb;
    BEGIN
      PERFORM paprnav_v4_lock_app_ad_numbers(NEW.proposal_id);
      SELECT * INTO p FROM ad_v4_candidate_proposals WHERE id=NEW.proposal_id FOR SHARE;
      subtree:=convert_from(NEW.applicability_subtree_bytes,'UTF8')::jsonb;
      envelope:=convert_from(NEW.projection_canonical_bytes,'UTF8')::jsonb;
      IF p.id IS NULL OR p.directive_id<>NEW.directive_id
         OR p.validator_version<>NEW.validator_version OR p.canonicalization_version<>NEW.canonicalization_version
         OR p.canonical_hash<>NEW.proposal_canonical_hash OR p.evidence_binding_hash<>NEW.evidence_binding_hash
         OR NEW.validator_version<>'paprnav-ad-v4-validator-2' OR NEW.canonicalization_version<>'paprnav-ad-v4-c14n-2'
         OR NEW.materializer_version<>'paprnav-ad-v4-app-materializer-2' OR NEW.gate<>'candidate_only'
         OR subtree IS DISTINCT FROM jsonb_build_object(
              'productScopes',p.parsed_json::jsonb->'productScopes',
              'conditionDefinitions',p.parsed_json::jsonb->'conditionDefinitions',
              'applicabilityRules',p.parsed_json::jsonb->'applicabilityRules',
              'applicabilitySearchHints',p.parsed_json::jsonb->'applicabilitySearchHints')
         OR NEW.applicability_subtree_hash<>encode(sha256(
              convert_to('paprnav:ad_extraction_v4:applicability-subtree:paprnav-ad-v4-c14n-2','UTF8')||decode('00','hex')||NEW.applicability_subtree_bytes),'hex')
         OR NEW.projection_hash<>encode(sha256(
              convert_to('paprnav:ad_extraction_v4:applicability-projection:2','UTF8')||decode('00','hex')||NEW.projection_canonical_bytes),'hex')
         OR envelope->>'version'<>'ad-v4-applicability-projection-v2'
         OR envelope->>'proposalId'<>NEW.proposal_id
         OR envelope->>'proposalCanonicalHash'<>NEW.proposal_canonical_hash
         OR envelope->>'evidenceBindingHash'<>NEW.evidence_binding_hash
         OR envelope->>'validatorVersion'<>NEW.validator_version
         OR envelope->>'canonicalizationVersion'<>NEW.canonicalization_version
         OR envelope->>'materializerVersion'<>NEW.materializer_version
         OR envelope->>'applicabilitySubtreeHash'<>NEW.applicability_subtree_hash THEN
        RAISE EXCEPTION 'V4 applicability projection envelope mismatch';
      END IF;
      RETURN NEW;
    END; $$ LANGUAGE plpgsql
    """)
    op.execute("CREATE TRIGGER trg_ad_v4_candidate_app_projections_validate BEFORE INSERT ON ad_v4_candidate_app_projections FOR EACH ROW EXECUTE FUNCTION paprnav_v4_validate_app_projection()")


def _install_projection_audit_validation() -> None:
    op.execute("""
    CREATE FUNCTION paprnav_v4_validate_app_request() RETURNS trigger AS $$
    DECLARE p ad_v4_candidate_app_projections%ROWTYPE; m organization_memberships%ROWTYPE; u users%ROWTYPE; payload jsonb;
    BEGIN
      SELECT * INTO p FROM ad_v4_candidate_app_projections WHERE id=NEW.projection_id;
      SELECT * INTO m FROM organization_memberships WHERE id=NEW.authorizing_membership_id FOR SHARE;
      SELECT * INTO u FROM users WHERE id=NEW.actor_user_id FOR SHARE;
      payload:=convert_from(NEW.request_canonical_bytes,'UTF8')::jsonb;
      IF p.id IS NULL OR p.proposal_id<>NEW.proposal_id OR p.directive_id<>NEW.directive_id
         OR m.id IS NULL OR u.id IS NULL OR u.status<>'active'
         OR m.user_id<>NEW.actor_user_id OR m.organization_id<>NEW.organization_id
         OR m.role<>'platform_admin' OR m.status<>'active'
         OR NEW.actor_role<>m.role OR NEW.actor_status<>m.status
         OR NEW.endpoint_action<>'materialize_ad_v4_applicability'
         OR payload->>'action'<>NEW.endpoint_action OR payload->>'directiveId'<>NEW.directive_id
         OR payload->>'proposalId'<>NEW.proposal_id
         OR payload->>'validatorVersion'<>p.validator_version
         OR payload->>'canonicalizationVersion'<>p.canonicalization_version
         OR payload->>'materializerVersion'<>p.materializer_version
         OR NEW.request_hash<>encode(sha256(
              convert_to('paprnav:ad_extraction_v4:applicability-row:2','UTF8')||decode('00','hex')||NEW.request_canonical_bytes),'hex') THEN
        RAISE EXCEPTION 'V4 applicability request authorization/envelope mismatch';
      END IF;
      RETURN NEW;
    END; $$ LANGUAGE plpgsql
    """)
    op.execute("CREATE TRIGGER trg_ad_v4_candidate_app_materialization_requests_validate BEFORE INSERT ON ad_v4_candidate_app_materialization_requests FOR EACH ROW EXECUTE FUNCTION paprnav_v4_validate_app_request()")
    op.execute("""
    CREATE FUNCTION paprnav_v4_validate_app_event() RETURNS trigger AS $$
    DECLARE p ad_v4_candidate_app_projections%ROWTYPE; previous ad_v4_candidate_app_projection_events%ROWTYPE; payload jsonb;
    BEGIN
      SELECT * INTO p FROM ad_v4_candidate_app_projections WHERE id=NEW.projection_id;
      payload:=convert_from(NEW.canonical_bytes,'UTF8')::jsonb;
      IF NEW.sequence_number>0 THEN
        SELECT * INTO previous FROM ad_v4_candidate_app_projection_events
         WHERE projection_id=NEW.projection_id AND sequence_number=NEW.sequence_number-1 FOR SHARE;
      END IF;
      IF p.id IS NULL OR p.proposal_id<>NEW.proposal_id
         OR payload->>'version'<>'ad-v4-applicability-event-v2'
         OR payload->>'eventType'<>NEW.event_type OR payload->>'projectionId'<>NEW.projection_id
         OR payload->>'proposalId'<>NEW.proposal_id OR (payload->>'sequence')::integer<>NEW.sequence_number
         OR NEW.event_hash<>encode(sha256(
              convert_to('paprnav:ad_extraction_v4:applicability-projection-event:2','UTF8')||decode('00','hex')||NEW.canonical_bytes),'hex')
         OR (NEW.sequence_number=0 AND (NEW.event_type<>'materialized' OR NEW.predecessor_event_hash IS NOT NULL
              OR NEW.causing_request_id IS NULL OR payload->>'requestId'<>NEW.causing_request_id
              OR num_nonnulls(NEW.causing_relationship_id,NEW.causing_lifecycle_event_id,NEW.causing_dependency_id)<>0))
         OR (NEW.sequence_number>0 AND (previous.id IS NULL OR previous.event_hash<>NEW.predecessor_event_hash OR payload->>'predecessorEventHash'<>NEW.predecessor_event_hash))
         OR (NEW.event_type='stale_marked' AND num_nonnulls(
              NEW.causing_relationship_id,NEW.causing_lifecycle_event_id,NEW.causing_dependency_id)<>1)
         OR (NEW.event_type='stale_marked' AND (NEW.causing_request_id IS NOT NULL OR NEW.actor_kind<>'system_repair'
              OR payload->'reasons' IS NULL OR jsonb_typeof(payload->'reasons')<>'array'
              OR NEW.reason_code<>CASE WHEN jsonb_array_length(payload->'reasons')=1
                   THEN payload->'reasons'->>0 ELSE 'multiple' END
              OR payload->'cause'->>'id'<>coalesce(NEW.causing_relationship_id,NEW.causing_dependency_id,NEW.causing_lifecycle_event_id)
              OR payload->'cause'->>'kind'<>CASE
                   WHEN NEW.causing_relationship_id IS NOT NULL THEN 'candidate_relationship'
                   WHEN NEW.causing_dependency_id IS NOT NULL THEN 'supersession_dependency'
                   ELSE 'evidence_lifecycle' END))
         OR (NEW.causing_dependency_id IS NOT NULL AND NOT EXISTS (
              SELECT 1 FROM ad_v4_candidate_app_change_dependencies d
               WHERE d.id=NEW.causing_dependency_id AND d.projection_id=NEW.projection_id
                 AND d.dependency_kind='incoming_supersession_signal'
                 AND d.resolution_state='resolved_candidate'))
         OR (NEW.event_type NOT IN ('materialized','stale_marked')) THEN
        RAISE EXCEPTION 'V4 applicability event chain/envelope mismatch';
      END IF;
      RETURN NEW;
    END; $$ LANGUAGE plpgsql
    """)
    op.execute("CREATE TRIGGER trg_ad_v4_candidate_app_projection_events_validate BEFORE INSERT ON ad_v4_candidate_app_projection_events FOR EACH ROW EXECUTE FUNCTION paprnav_v4_validate_app_event()")


def _install_projection_completeness() -> None:
    op.execute(r"""
    CREATE FUNCTION paprnav_v4_json_nodes(
      p_value jsonb, p_pointer text DEFAULT '', p_parent text DEFAULT NULL,
      p_property text DEFAULT NULL, p_ordinal integer DEFAULT NULL
    ) RETURNS TABLE(
      json_pointer text, parent_pointer text, property_name text,
      array_ordinal integer, value_kind text, string_value text,
      boolean_value boolean
    ) AS $$
    DECLARE child_key text; child_value jsonb; child_ordinal integer;
    BEGIN
      RETURN QUERY SELECT p_pointer,p_parent,p_property,p_ordinal,
        CASE jsonb_typeof(p_value)
          WHEN 'object' THEN 'object' WHEN 'array' THEN 'array'
          WHEN 'boolean' THEN 'boolean' ELSE 'string' END,
        CASE WHEN jsonb_typeof(p_value)='string' THEN p_value #>> '{}' ELSE NULL END,
        CASE WHEN jsonb_typeof(p_value)='boolean' THEN (p_value #>> '{}')::boolean ELSE NULL END;
      IF jsonb_typeof(p_value)='object' THEN
        FOR child_key,child_value IN SELECT key,value FROM jsonb_each(p_value) LOOP
          RETURN QUERY SELECT * FROM paprnav_v4_json_nodes(
            child_value,p_pointer||'/'||child_key,p_pointer,child_key,NULL);
        END LOOP;
      ELSIF jsonb_typeof(p_value)='array' THEN
        FOR child_value,child_ordinal IN
          SELECT value,(ordinality-1)::integer FROM jsonb_array_elements(p_value) WITH ORDINALITY
        LOOP
          RETURN QUERY SELECT * FROM paprnav_v4_json_nodes(
            child_value,p_pointer||'/'||child_ordinal::text,p_pointer,NULL,child_ordinal);
        END LOOP;
      END IF;
    END; $$ LANGUAGE plpgsql IMMUTABLE
    """)
    op.execute(r"""
    CREATE FUNCTION paprnav_v4_jcs(p_value jsonb) RETURNS text AS $$
    DECLARE result text;
    BEGIN
      CASE jsonb_typeof(p_value)
        WHEN 'object' THEN
          SELECT '{'||coalesce(string_agg(to_jsonb(key)::text||':'||paprnav_v4_jcs(value),',' ORDER BY key),'')||'}'
            INTO result FROM jsonb_each(p_value);
        WHEN 'array' THEN
          SELECT '['||coalesce(string_agg(paprnav_v4_jcs(value),',' ORDER BY ordinality),'')||']'
            INTO result FROM jsonb_array_elements(p_value) WITH ORDINALITY;
        ELSE result:=p_value::text;
      END CASE;
      RETURN result;
    END; $$ LANGUAGE plpgsql IMMUTABLE STRICT
    """)
    op.execute(r"""
    CREATE FUNCTION paprnav_v4_pointer_value(p_root jsonb,p_pointer text) RETURNS jsonb AS $$
    DECLARE result jsonb:=p_root; token text;
    BEGIN
      IF p_pointer='' THEN RETURN result; END IF;
      FOREACH token IN ARRAY string_to_array(trim(leading '/' FROM p_pointer),'/') LOOP
        IF jsonb_typeof(result)='array' THEN result:=result->token::integer;
        ELSE result:=result->token;
        END IF;
        IF result IS NULL THEN RETURN NULL; END IF;
      END LOOP;
      RETURN result;
    END; $$ LANGUAGE plpgsql IMMUTABLE STRICT
    """)
    op.execute(r"""
    CREATE FUNCTION paprnav_v4_app_evidence_json(p_projection_id text,p_node_id text)
    RETURNS jsonb AS $$
      SELECT coalesce(jsonb_agg(to_jsonb(evidence_key) ORDER BY canonical_ordinal),'[]'::jsonb)
        FROM ad_v4_candidate_app_evidence_links
       WHERE projection_id=p_projection_id AND semantic_node_id=p_node_id
    $$ LANGUAGE sql STABLE
    """)
    op.execute(r"""
    CREATE FUNCTION paprnav_v4_app_assertion_json(p_projection_id text,p_node_id text)
    RETURNS jsonb AS $$
    DECLARE a ad_v4_candidate_app_value_assertions%ROWTYPE;
    BEGIN
      SELECT * INTO STRICT a FROM ad_v4_candidate_app_value_assertions
       WHERE projection_id=p_projection_id AND semantic_node_id=p_node_id;
      IF a.state='known' THEN
        RETURN jsonb_build_object('state',a.state,'value',a.text_value,
          'evidenceKeys',paprnav_v4_app_evidence_json(p_projection_id,p_node_id));
      END IF;
      RETURN jsonb_build_object('state',a.state,'reason',a.reason,
        'temporalScope',jsonb_build_object('kind',a.temporal_scope),
        'evidenceKeys',paprnav_v4_app_evidence_json(p_projection_id,p_node_id));
    END; $$ LANGUAGE plpgsql STABLE STRICT
    """)
    op.execute(r"""
    CREATE FUNCTION paprnav_v4_app_normalized_json(
      p_projection_id text,p_mapping_node_id text,p_assertion_node_id text
    ) RETURNS jsonb AS $$
    DECLARE m ad_v4_candidate_app_identity_mappings%ROWTYPE;
    BEGIN
      SELECT * INTO STRICT m FROM ad_v4_candidate_app_identity_mappings
       WHERE projection_id=p_projection_id AND semantic_node_id=p_mapping_node_id;
      IF m.normalized_state='known' THEN
        RETURN jsonb_build_object('state',m.normalized_state,'value',m.normalized_value,
          'evidenceKeys',paprnav_v4_app_evidence_json(p_projection_id,p_assertion_node_id));
      END IF;
      RETURN jsonb_build_object('state',m.normalized_state,'reason',m.reason,
        'temporalScope',jsonb_build_object('kind',m.temporal_scope),
        'evidenceKeys',paprnav_v4_app_evidence_json(p_projection_id,p_assertion_node_id));
    END; $$ LANGUAGE plpgsql STABLE STRICT
    """)
    op.execute(r"""
    CREATE FUNCTION paprnav_v4_app_designation_json(p_projection_id text,p_scope_node_id text)
    RETURNS jsonb AS $$
    DECLARE s ad_v4_candidate_app_designation_scopes%ROWTYPE; result jsonb;
    BEGIN
      SELECT * INTO STRICT s FROM ad_v4_candidate_app_designation_scopes
       WHERE projection_id=p_projection_id AND semantic_node_id=p_scope_node_id;
      result:=jsonb_build_object('kind',s.scope_kind,
        'evidenceKeys',paprnav_v4_app_evidence_json(p_projection_id,p_scope_node_id));
      IF s.scope_kind='listed' THEN
        result:=result||jsonb_build_object('sourceDesignations',(
          SELECT coalesce(jsonb_agg(to_jsonb(source_value) ORDER BY canonical_ordinal),'[]'::jsonb)
            FROM ad_v4_candidate_app_designation_values
           WHERE projection_id=p_projection_id AND designation_scope_id=p_scope_node_id));
      ELSIF s.scope_kind='series_expression' THEN
        result:=result||jsonb_build_object('expression',s.series_expression);
      ELSIF s.scope_kind='ranges' THEN
        result:=result||jsonb_build_object('ranges',(
          SELECT coalesce(jsonb_agg(jsonb_build_object(
            'lower',lower_value,'upper',upper_value,
            'lowerInclusive',lower_inclusive,'upperInclusive',upper_inclusive,
            'polarity',polarity) ORDER BY canonical_ordinal),'[]'::jsonb)
            FROM ad_v4_candidate_app_designation_ranges
           WHERE projection_id=p_projection_id AND designation_scope_id=p_scope_node_id));
      ELSIF s.scope_kind IN ('unknown','not_applicable') THEN
        result:=result||jsonb_build_object('reason',s.reason,
          'temporalScope',jsonb_build_object('kind',s.temporal_scope));
      END IF;
      RETURN result;
    END; $$ LANGUAGE plpgsql STABLE STRICT
    """)
    op.execute(r"""
    CREATE FUNCTION paprnav_v4_app_expression_json(p_projection_id text,p_expression_node_id text)
    RETURNS jsonb AS $$
    DECLARE e ad_v4_candidate_app_expressions%ROWTYPE; result jsonb;
    BEGIN
      SELECT * INTO STRICT e FROM ad_v4_candidate_app_expressions
       WHERE projection_id=p_projection_id AND semantic_node_id=p_expression_node_id;
      result:=jsonb_build_object('nodeType',e.expression_node_type);
      IF e.expression_node_type='scope_ref' THEN
        RETURN result||jsonb_build_object('scopeKey',(
          SELECT node_key FROM ad_v4_candidate_app_semantic_nodes WHERE id=e.scope_node_id));
      ELSIF e.expression_node_type='predicate_ref' THEN
        RETURN result||jsonb_build_object('conditionKey',(
          SELECT node_key FROM ad_v4_candidate_app_semantic_nodes WHERE id=e.condition_node_id));
      ELSIF e.expression_node_type='rule_ref' THEN
        RETURN result||jsonb_build_object('ruleKey',(
          SELECT node_key FROM ad_v4_candidate_app_semantic_nodes WHERE id=e.referenced_rule_node_id));
      ELSIF e.expression_node_type='not' THEN
        RETURN result||jsonb_build_object('operand',(
          SELECT paprnav_v4_app_expression_json(p_projection_id,child_expression_id)
            FROM ad_v4_candidate_app_expression_edges
           WHERE projection_id=p_projection_id AND parent_expression_id=p_expression_node_id
           ORDER BY sequence LIMIT 1));
      END IF;
      RETURN result||jsonb_build_object('operands',(
        SELECT coalesce(jsonb_agg(
          paprnav_v4_app_expression_json(p_projection_id,child_expression_id)
          ORDER BY sequence),'[]'::jsonb)
          FROM ad_v4_candidate_app_expression_edges
         WHERE projection_id=p_projection_id AND parent_expression_id=p_expression_node_id));
    END; $$ LANGUAGE plpgsql STABLE STRICT
    """)
    op.execute(r"""
    CREATE FUNCTION paprnav_v4_app_condition_group_json(p_projection_id text,p_group_node_id text)
    RETURNS jsonb AS $$
    DECLARE g ad_v4_candidate_app_designation_groups%ROWTYPE; result jsonb;
    BEGIN
      SELECT * INTO STRICT g FROM ad_v4_candidate_app_designation_groups
       WHERE projection_id=p_projection_id AND semantic_node_id=p_group_node_id;
      result:=jsonb_build_object(
        'groupKey',g.group_key,
        'sourceDisplayText',paprnav_v4_app_assertion_json(p_projection_id,g.source_display_assertion_node_id),
        'association',g.association,
        'members',(SELECT coalesce(jsonb_agg(
          jsonb_build_object(
            'memberKey',m.member_key,'designationKind',m.designation_kind,
            'manufacturer',paprnav_v4_app_assertion_json(p_projection_id,m.manufacturer_assertion_node_id),
            'evidenceKeys',paprnav_v4_app_evidence_json(p_projection_id,m.semantic_node_id))
          ||CASE WHEN m.designation_kind='model'
             THEN jsonb_build_object('sourceDesignation',m.source_designation)
             ELSE jsonb_build_object('expressionText',m.expression_text,
                    'evaluationState','unknown','reason',m.evaluation_reason) END
          ORDER BY m.canonical_ordinal),'[]'::jsonb)
          FROM ad_v4_candidate_app_designation_group_members m
         WHERE m.projection_id=p_projection_id AND m.group_node_id=p_group_node_id),
        'evidenceKeys',paprnav_v4_app_evidence_json(p_projection_id,p_group_node_id));
      IF g.association='unknown' THEN
        result:=result||jsonb_build_object('reason',g.reason,
          'temporalScope',jsonb_build_object('kind',g.temporal_scope));
      END IF;
      RETURN result;
    END; $$ LANGUAGE plpgsql STABLE STRICT
    """)
    op.execute(r"""
    CREATE FUNCTION paprnav_v4_app_search_group_json(p_projection_id text,p_group_node_id text)
    RETURNS jsonb AS $$
    DECLARE g ad_v4_candidate_app_search_hint_groups%ROWTYPE; result jsonb;
    BEGIN
      SELECT * INTO STRICT g FROM ad_v4_candidate_app_search_hint_groups
       WHERE projection_id=p_projection_id AND semantic_node_id=p_group_node_id;
      result:=jsonb_build_object(
        'groupKey',g.group_key,
        'manufacturer',paprnav_v4_app_assertion_json(p_projection_id,g.manufacturer_assertion_node_id),
        'association',g.association,
        'members',(SELECT coalesce(jsonb_agg(
          jsonb_build_object(
            'memberKey',m.member_key,'designationKind',m.designation_kind,
            'manufacturer',paprnav_v4_app_assertion_json(p_projection_id,m.manufacturer_assertion_node_id),
            'evidenceKeys',paprnav_v4_app_evidence_json(p_projection_id,m.semantic_node_id))
          ||CASE WHEN m.designation_kind='model'
             THEN jsonb_build_object('sourceDesignation',m.source_designation)
             ELSE jsonb_build_object('expressionText',m.expression_text,
                    'evaluationState','unknown','reason',m.evaluation_reason) END
          ORDER BY m.canonical_ordinal),'[]'::jsonb)
          FROM ad_v4_candidate_app_search_hint_members m
         WHERE m.projection_id=p_projection_id AND m.group_node_id=p_group_node_id),
        'evidenceKeys',paprnav_v4_app_evidence_json(p_projection_id,p_group_node_id));
      IF g.association='unknown' THEN
        result:=result||jsonb_build_object('reason',g.reason,
          'temporalScope',jsonb_build_object('kind',g.temporal_scope));
      END IF;
      RETURN result;
    END; $$ LANGUAGE plpgsql STABLE STRICT
    """)
    op.execute(r"""
    CREATE FUNCTION paprnav_v4_candidate_app_typed_subtree(p_projection_id text)
    RETURNS jsonb AS $$
    DECLARE product_values jsonb; condition_values jsonb; rule_values jsonb; hint_values jsonb;
    BEGIN
      SELECT coalesce(jsonb_agg(
        jsonb_build_object('scopeKey',p.scope_key,'productRole',p.product_role,
          'evidenceKeys',paprnav_v4_app_evidence_json(p_projection_id,p.semantic_node_id))
        ||CASE WHEN p.manufacturer_presence='present' THEN jsonb_build_object(
            'manufacturer',jsonb_build_object('sourceValue',p.manufacturer_source_value,
              'normalizedIdentity',paprnav_v4_app_normalized_json(
                p_projection_id,p.manufacturer_identity_mapping_node_id,a.semantic_node_id)))
          ELSE '{}'::jsonb END
        ||CASE WHEN p.model_presence='present' THEN jsonb_build_object('modelScope',
            paprnav_v4_app_designation_json(p_projection_id,model_scope.semantic_node_id)) ELSE '{}'::jsonb END
        ||CASE WHEN p.serial_presence='present' THEN jsonb_build_object('serialScope',
            paprnav_v4_app_designation_json(p_projection_id,serial_scope.semantic_node_id)) ELSE '{}'::jsonb END
        ||CASE WHEN p.part_number_presence='present' THEN jsonb_build_object('partNumberScope',
            paprnav_v4_app_designation_json(p_projection_id,part_scope.semantic_node_id)) ELSE '{}'::jsonb END
        ORDER BY n.canonical_ordinal),'[]'::jsonb) INTO product_values
        FROM ad_v4_candidate_app_product_scopes p
        JOIN ad_v4_candidate_app_semantic_nodes n ON n.id=p.semantic_node_id
        LEFT JOIN ad_v4_candidate_app_value_assertions a
          ON a.parent_semantic_node_id=p.semantic_node_id AND a.field_code='manufacturer'
        LEFT JOIN ad_v4_candidate_app_designation_scopes model_scope
          ON model_scope.product_scope_node_id=p.semantic_node_id AND model_scope.field_kind='model'
        LEFT JOIN ad_v4_candidate_app_designation_scopes serial_scope
          ON serial_scope.product_scope_node_id=p.semantic_node_id AND serial_scope.field_kind='serial'
        LEFT JOIN ad_v4_candidate_app_designation_scopes part_scope
          ON part_scope.product_scope_node_id=p.semantic_node_id AND part_scope.field_kind='part_number'
       WHERE p.projection_id=p_projection_id;

      SELECT coalesce(jsonb_agg(
        jsonb_build_object(
          'conditionKey',c.condition_key,'conditionType',c.condition_type,
          'operator',c.operator,
          'subject',
            (CASE WHEN c.subject_product_role_presence='present'
               THEN jsonb_build_object('productRole',c.subject_product_role) ELSE '{}'::jsonb END)
            ||(CASE WHEN c.subject_attribute_key_presence='present'
               THEN jsonb_build_object('attributeKey',c.subject_attribute_key) ELSE '{}'::jsonb END)
            ||coalesce((SELECT jsonb_object_agg(
                 CASE a.field_code
                   WHEN 'manufacturer' THEN 'manufacturer'
                   WHEN 'model_or_series' THEN 'modelOrSeries'
                   WHEN 'part_number' THEN 'partNumber'
                   WHEN 'serial_number' THEN 'serialNumber'
                   WHEN 'stc_number' THEN 'stcNumber'
                   ELSE 'attributeValue' END,
                 paprnav_v4_app_assertion_json(p_projection_id,a.semantic_node_id))
               FROM ad_v4_candidate_app_value_assertions a
              WHERE a.projection_id=p_projection_id AND a.parent_semantic_node_id=c.semantic_node_id
                AND a.field_code IN ('manufacturer','model_or_series','part_number','serial_number','stc_number','attribute_value')),'{}'::jsonb)
            ||CASE WHEN c.designation_group_presence='present'
               THEN jsonb_build_object('designationGroup',
                 paprnav_v4_app_condition_group_json(p_projection_id,c.designation_group_node_id))
               ELSE '{}'::jsonb END,
          'temporalBasis',jsonb_build_object('kind',c.temporal_basis),
          'evidenceKeys',paprnav_v4_app_evidence_json(p_projection_id,c.semantic_node_id))
        ||CASE WHEN c.comparator_presence='present'
          THEN jsonb_build_object('comparatorVersion',c.comparator_version) ELSE '{}'::jsonb END
        ORDER BY n.canonical_ordinal),'[]'::jsonb) INTO condition_values
        FROM ad_v4_candidate_app_conditions c
        JOIN ad_v4_candidate_app_semantic_nodes n ON n.id=c.semantic_node_id
       WHERE c.projection_id=p_projection_id;

      SELECT coalesce(jsonb_agg(
        jsonb_build_object(
          'ruleKey',r.rule_key,
          'scopeExpression',paprnav_v4_app_expression_json(p_projection_id,r.scope_expression_node_id),
          'exclusionRuleKeys',(SELECT coalesce(jsonb_agg(to_jsonb(excluded.node_key)
            ORDER BY x.canonical_ordinal),'[]'::jsonb)
            FROM ad_v4_candidate_app_rule_exclusions x
            JOIN ad_v4_candidate_app_semantic_nodes excluded ON excluded.id=x.excluded_rule_node_id
           WHERE x.projection_id=p_projection_id AND x.rule_node_id=r.semantic_node_id),
          'evidenceKeys',paprnav_v4_app_evidence_json(p_projection_id,r.semantic_node_id))
        ||CASE WHEN r.condition_presence='present'
          THEN jsonb_build_object('conditionExpression',
            paprnav_v4_app_expression_json(p_projection_id,r.condition_expression_node_id))
          ELSE '{}'::jsonb END
        ORDER BY n.canonical_ordinal),'[]'::jsonb) INTO rule_values
        FROM ad_v4_candidate_app_rules r
        JOIN ad_v4_candidate_app_semantic_nodes n ON n.id=r.semantic_node_id
       WHERE r.projection_id=p_projection_id;

      SELECT coalesce(jsonb_agg(jsonb_build_object(
        'hintKey',h.hint_key,'productRole',h.product_role,
        'sourceDisplayText',paprnav_v4_app_assertion_json(p_projection_id,h.source_display_assertion_node_id),
        'manufacturerModelGroups',(SELECT coalesce(jsonb_agg(
          paprnav_v4_app_search_group_json(p_projection_id,g.semantic_node_id)
          ORDER BY g.canonical_ordinal),'[]'::jsonb)
          FROM ad_v4_candidate_app_search_hint_groups g
         WHERE g.projection_id=p_projection_id AND g.hint_node_id=h.semantic_node_id),
        'controlling',h.controlling,'exhaustive',h.exhaustive,
        'evidenceKeys',paprnav_v4_app_evidence_json(p_projection_id,h.semantic_node_id))
        ORDER BY n.canonical_ordinal),'[]'::jsonb) INTO hint_values
        FROM ad_v4_candidate_app_search_hints h
        JOIN ad_v4_candidate_app_semantic_nodes n ON n.id=h.semantic_node_id
       WHERE h.projection_id=p_projection_id;

      RETURN jsonb_build_object(
        'productScopes',product_values,'conditionDefinitions',condition_values,
        'applicabilityRules',rule_values,'applicabilitySearchHints',hint_values);
    END; $$ LANGUAGE plpgsql STABLE STRICT
    """)
    op.execute(r"""
    CREATE FUNCTION paprnav_v4_candidate_app_require_complete(p_projection_id text) RETURNS void AS $$
    DECLARE
      projection ad_v4_candidate_app_projections%ROWTYPE;
      proposal ad_v4_candidate_proposals%ROWTYPE;
      subtree jsonb; envelope jsonb; correction record; expected_correction jsonb;
      actual_refs jsonb; actual_evidence jsonb; original_document jsonb; correcting_document jsonb;
      expected_hash text; expected_identity text; node record; node_value jsonb; node_root jsonb;
      expected_node_type text; expected_node_key text; expected_parent text;
      expected_ordinal integer; expected_node_count integer; matching_targets integer;
      relation jsonb; expected_target_id text;
    BEGIN
      SELECT * INTO projection FROM ad_v4_candidate_app_projections WHERE id=p_projection_id FOR SHARE;
      IF projection.id IS NULL THEN RAISE EXCEPTION 'V4 applicability projection is missing'; END IF;
      SELECT * INTO proposal FROM ad_v4_candidate_proposals WHERE id=projection.proposal_id FOR SHARE;
      PERFORM paprnav_v4_lock_app_ad_numbers(proposal.id);
      subtree:=jsonb_build_object(
        'productScopes',proposal.parsed_json::jsonb->'productScopes',
        'conditionDefinitions',proposal.parsed_json::jsonb->'conditionDefinitions',
        'applicabilityRules',proposal.parsed_json::jsonb->'applicabilityRules',
        'applicabilitySearchHints',proposal.parsed_json::jsonb->'applicabilitySearchHints');
      envelope:=convert_from(projection.projection_canonical_bytes,'UTF8')::jsonb;

      IF (SELECT count(*) FROM ad_v4_candidate_app_data WHERE projection_id=projection.id)<>projection.datum_count
         OR (SELECT count(*) FROM ad_v4_candidate_app_semantic_nodes WHERE projection_id=projection.id AND source_pointer NOT LIKE '/incomingSupersessionSignals/%')<>projection.semantic_node_count
         OR (SELECT count(*) FROM ad_v4_candidate_app_evidence_links WHERE projection_id=projection.id)<>projection.evidence_link_count
         OR (SELECT count(*) FROM ad_v4_candidate_app_identity_mappings WHERE projection_id=projection.id)<>projection.identity_mapping_count
         OR (SELECT count(*) FROM ad_v4_candidate_app_projection_events WHERE projection_id=projection.id AND event_type='materialized')<>1
         OR EXISTS (
           WITH expected AS (SELECT * FROM paprnav_v4_json_nodes(subtree)),
           actual AS (SELECT * FROM ad_v4_candidate_app_data WHERE projection_id=projection.id)
           SELECT 1 FROM expected e FULL JOIN actual a USING (json_pointer)
            WHERE e.json_pointer IS NULL OR a.json_pointer IS NULL
               OR e.parent_pointer IS DISTINCT FROM a.parent_pointer
               OR e.property_name IS DISTINCT FROM a.property_name
               OR e.array_ordinal IS DISTINCT FROM a.array_ordinal
               OR e.value_kind IS DISTINCT FROM a.value_kind
               OR e.string_value IS DISTINCT FROM a.string_value
               OR e.boolean_value IS DISTINCT FROM a.boolean_value)
         OR envelope->'semanticNodeHashes' IS DISTINCT FROM (
           SELECT coalesce(jsonb_agg(identity_hash ORDER BY identity_hash),'[]'::jsonb)
             FROM ad_v4_candidate_app_semantic_nodes WHERE projection_id=projection.id AND source_pointer NOT LIKE '/incomingSupersessionSignals/%')
         OR envelope->'evidenceLinkHashes' IS DISTINCT FROM (
           SELECT coalesce(jsonb_agg(link_hash ORDER BY link_hash),'[]'::jsonb)
             FROM ad_v4_candidate_app_evidence_links WHERE projection_id=projection.id)
      THEN RAISE EXCEPTION 'V4 applicability relational graph is incomplete or differs from candidate'; END IF;

      SELECT count(*) INTO expected_node_count FROM paprnav_v4_json_nodes(subtree) walked
       WHERE jsonb_typeof(paprnav_v4_pointer_value(subtree,walked.json_pointer))='object'
         AND (
           paprnav_v4_pointer_value(subtree,walked.json_pointer) ? 'nodeType'
           OR paprnav_v4_pointer_value(subtree,walked.json_pointer) ? 'scopeKey'
           OR paprnav_v4_pointer_value(subtree,walked.json_pointer) ? 'conditionKey'
           OR paprnav_v4_pointer_value(subtree,walked.json_pointer) ? 'ruleKey'
           OR paprnav_v4_pointer_value(subtree,walked.json_pointer) ? 'hintKey'
           OR paprnav_v4_pointer_value(subtree,walked.json_pointer) ? 'groupKey'
           OR paprnav_v4_pointer_value(subtree,walked.json_pointer) ? 'memberKey'
           OR ((paprnav_v4_pointer_value(subtree,walked.json_pointer) ? 'kind') AND
               walked.json_pointer ~ '/(modelScope|serialScope|partNumberScope)$'));
      expected_node_count:=expected_node_count+jsonb_array_length(proposal.parsed_json::jsonb->'supersessionRelations');
      SELECT expected_node_count+count(*) INTO expected_node_count
        FROM paprnav_v4_json_nodes(subtree) walked
       WHERE walked.json_pointer ~ '/modelScope/sourceDesignations/[0-9]+$'
         AND jsonb_typeof(paprnav_v4_pointer_value(subtree,walked.json_pointer))='string';
      -- Physical source/scope owners add one manufacturer assertion, one range
      -- node per canonical range, and one identity-mapping node per exact
      -- manufacturer/designation/member occurrence.
      SELECT expected_node_count+count(*)*2 INTO expected_node_count
        FROM paprnav_v4_json_nodes(subtree) walked
       WHERE walked.json_pointer ~ '^/productScopes/[0-9]+/manufacturer/sourceValue$'
         AND jsonb_typeof(paprnav_v4_pointer_value(subtree,walked.json_pointer))='string';
      SELECT expected_node_count+count(*) INTO expected_node_count
        FROM paprnav_v4_json_nodes(subtree) walked
       WHERE walked.json_pointer ~ '/(modelScope|serialScope|partNumberScope)/ranges/[0-9]+$'
         AND jsonb_typeof(paprnav_v4_pointer_value(subtree,walked.json_pointer))='object';
      SELECT expected_node_count+count(*) INTO expected_node_count
        FROM paprnav_v4_json_nodes(subtree) walked
       WHERE walked.json_pointer ~ '/(modelScope|serialScope|partNumberScope)/sourceDesignations/[0-9]+$'
         AND jsonb_typeof(paprnav_v4_pointer_value(subtree,walked.json_pointer))='string';
      SELECT expected_node_count+count(*) INTO expected_node_count
        FROM paprnav_v4_json_nodes(subtree) walked
       WHERE jsonb_typeof(paprnav_v4_pointer_value(subtree,walked.json_pointer))='object'
         AND paprnav_v4_pointer_value(subtree,walked.json_pointer) ? 'memberKey';
      -- Condition-family typed assertions and exact-occurrence mappings.
      SELECT expected_node_count+count(*) INTO expected_node_count
        FROM paprnav_v4_json_nodes(subtree) walked
       WHERE walked.json_pointer ~ '^/conditionDefinitions/[0-9]+/subject/(manufacturer|modelOrSeries|partNumber|serialNumber|stcNumber|attributeValue)$'
         AND jsonb_typeof(paprnav_v4_pointer_value(subtree,walked.json_pointer))='object';
      SELECT expected_node_count+count(*) INTO expected_node_count
        FROM paprnav_v4_json_nodes(subtree) walked
       WHERE walked.json_pointer ~ '^/conditionDefinitions/[0-9]+/subject/(manufacturer|modelOrSeries)$'
         AND paprnav_v4_pointer_value(subtree,walked.json_pointer)->>'state'='known';
      SELECT expected_node_count+count(*) INTO expected_node_count
        FROM paprnav_v4_json_nodes(subtree) walked
       WHERE walked.json_pointer ~ '^/conditionDefinitions/[0-9]+/subject/designationGroup/sourceDisplayText$'
         AND jsonb_typeof(paprnav_v4_pointer_value(subtree,walked.json_pointer))='object';
      SELECT expected_node_count+count(*) INTO expected_node_count
        FROM paprnav_v4_json_nodes(subtree) walked
       WHERE walked.json_pointer ~ '^/conditionDefinitions/[0-9]+/subject/designationGroup/members/[0-9]+/manufacturer$'
         AND jsonb_typeof(paprnav_v4_pointer_value(subtree,walked.json_pointer))='object';
      SELECT expected_node_count+count(*) INTO expected_node_count
        FROM paprnav_v4_json_nodes(subtree) walked
       WHERE walked.json_pointer ~ '^/conditionDefinitions/[0-9]+/subject/designationGroup/members/[0-9]+/manufacturer$'
         AND paprnav_v4_pointer_value(subtree,walked.json_pointer)->>'state'='known';
      -- Search-hint display/manufacturer assertions and exact occurrence mappings.
      SELECT expected_node_count+count(*) INTO expected_node_count
        FROM paprnav_v4_json_nodes(subtree) walked
       WHERE walked.json_pointer ~ '^/applicabilitySearchHints/[0-9]+/(sourceDisplayText|manufacturerModelGroups/[0-9]+/manufacturer|manufacturerModelGroups/[0-9]+/members/[0-9]+/manufacturer)$'
         AND jsonb_typeof(paprnav_v4_pointer_value(subtree,walked.json_pointer))='object';
      SELECT expected_node_count+count(*) INTO expected_node_count
        FROM paprnav_v4_json_nodes(subtree) walked
       WHERE walked.json_pointer ~ '^/applicabilitySearchHints/[0-9]+/manufacturerModelGroups/[0-9]+/(manufacturer|members/[0-9]+/manufacturer)$'
         AND paprnav_v4_pointer_value(subtree,walked.json_pointer)->>'state'='known';
      IF expected_node_count<>(SELECT count(*) FROM ad_v4_candidate_app_semantic_nodes WHERE projection_id=projection.id AND source_pointer NOT LIKE '/incomingSupersessionSignals/%')
      THEN RAISE EXCEPTION 'V4 applicability semantic-node set is incomplete'; END IF;

      FOR node IN SELECT * FROM ad_v4_candidate_app_semantic_nodes WHERE projection_id=projection.id AND source_pointer NOT LIKE '/incomingSupersessionSignals/%' LOOP
        node_root:=CASE WHEN node.source_pointer LIKE '/supersessionRelations/%' THEN proposal.parsed_json::jsonb ELSE subtree END;
        node_value:=paprnav_v4_pointer_value(node_root,node.source_pointer);
        expected_node_type:=NULL; expected_node_key:=NULL;
        IF node.node_type='identity_mapping' THEN
          expected_node_type:='identity_mapping';
          expected_node_key:=node.parent_node_id;
        ELSIF node.node_type='value_assertion'
              AND (node.source_pointer ~ '^/productScopes/[0-9]+/manufacturer/sourceValue$'
                OR node.source_pointer ~ '^/conditionDefinitions/[0-9]+/subject/(manufacturer|modelOrSeries|partNumber|serialNumber|stcNumber|attributeValue)$'
                OR node.source_pointer ~ '^/conditionDefinitions/[0-9]+/subject/designationGroup/sourceDisplayText$'
                OR node.source_pointer ~ '^/conditionDefinitions/[0-9]+/subject/designationGroup/members/[0-9]+/manufacturer$'
                OR node.source_pointer ~ '^/applicabilitySearchHints/[0-9]+/(sourceDisplayText|manufacturerModelGroups/[0-9]+/manufacturer|manufacturerModelGroups/[0-9]+/members/[0-9]+/manufacturer)$') THEN
          expected_node_type:='value_assertion'; expected_node_key:=node.source_pointer;
        ELSIF node.node_type='designation_range'
              AND node.source_pointer ~ '/(modelScope|serialScope|partNumberScope)/ranges/[0-9]+$' THEN
          expected_node_type:='designation_range'; expected_node_key:=node.source_pointer;
        ELSIF node.source_pointer LIKE '/supersessionRelations/%' THEN
          expected_node_type:='change_dependency';
          expected_node_key:=(node_value->>'relationType')||':'||(node_value->>'predecessorAdNumber');
        ELSIF node_value ? 'nodeType' THEN
          IF node.source_pointer LIKE '/applicabilityRules/%'
             AND node_value->>'nodeType'='requirement_state_ref' THEN
            RAISE EXCEPTION 'V4 applicability rule contains requirement-state reference';
          END IF;
          expected_node_type:='expression'; expected_node_key:=node.source_pointer;
        ELSIF node_value ? 'scopeKey' THEN expected_node_type:='product_scope'; expected_node_key:=node_value->>'scopeKey';
        ELSIF node_value ? 'conditionKey' THEN expected_node_type:='condition'; expected_node_key:=node_value->>'conditionKey';
        ELSIF node_value ? 'ruleKey' THEN expected_node_type:='applicability_rule'; expected_node_key:=node_value->>'ruleKey';
        ELSIF node_value ? 'hintKey' THEN expected_node_type:='search_hint'; expected_node_key:=node_value->>'hintKey';
        ELSIF node_value ? 'groupKey' THEN
          expected_node_type:=CASE WHEN node.source_pointer LIKE '%/manufacturerModelGroups/%' THEN 'search_hint_group' ELSE 'designation_group' END;
          expected_node_key:=node.source_pointer;
        ELSIF node_value ? 'memberKey' THEN
          expected_node_type:=CASE WHEN node.source_pointer LIKE '%/manufacturerModelGroups/%' THEN 'search_hint_model' ELSE 'designation_group_member' END;
          expected_node_key:=node.source_pointer;
        ELSIF node_value ? 'kind' AND node.source_pointer ~ '/(modelScope|serialScope|partNumberScope)$' THEN
          expected_node_type:='designation_scope'; expected_node_key:=node.source_pointer;
        ELSIF jsonb_typeof(node_value)='string' AND node.source_pointer ~ '/(modelScope|serialScope|partNumberScope)/sourceDesignations/[0-9]+$' THEN
          expected_node_type:='designation_value';
          SELECT parent.node_key||':'||regexp_replace(node.source_pointer,'^.*/','')
            INTO expected_node_key FROM ad_v4_candidate_app_semantic_nodes parent
           WHERE parent.projection_id=projection.id AND parent.node_type='designation_scope'
             AND node.source_pointer LIKE parent.source_pointer||'/%'
           ORDER BY length(parent.source_pointer) DESC LIMIT 1;
        END IF;
        SELECT id INTO expected_parent FROM ad_v4_candidate_app_semantic_nodes parent
         WHERE parent.projection_id=projection.id AND parent.id<>node.id
           AND parent.node_type<>'identity_mapping'
           AND node.source_pointer LIKE parent.source_pointer||'/%'
         ORDER BY length(parent.source_pointer) DESC LIMIT 1;
        IF node.node_type='identity_mapping' THEN
          SELECT parent.id INTO expected_parent
            FROM ad_v4_candidate_app_semantic_nodes parent
           WHERE parent.id=node.parent_node_id AND parent.projection_id=projection.id
             AND parent.source_pointer=node.source_pointer
             AND parent.node_type IN ('value_assertion','designation_value','designation_group_member','search_hint_model');
        END IF;
        expected_ordinal:=CASE WHEN regexp_replace(node.source_pointer,'^.*/','') ~ '^[0-9]+$'
          THEN regexp_replace(node.source_pointer,'^.*/','')::integer ELSE 0 END;
        expected_hash:=encode(sha256(convert_to(paprnav_v4_jcs(node_value),'UTF8')),'hex');
        expected_identity:=CASE WHEN expected_node_type='designation_value' THEN
          encode(sha256(
            convert_to('paprnav:ad_extraction_v4:applicability-row:2','UTF8')||decode('00','hex')||
            convert_to(paprnav_v4_jcs(jsonb_build_object(
              'table','designation-value','identity',jsonb_build_object(
                'projectionId',projection.id,'pointer',node.source_pointer,
                'value',node_value #>> '{}'))),'UTF8')),'hex')
        ELSE encode(sha256(
          convert_to('paprnav:ad_extraction_v4:applicability-row:2','UTF8')||decode('00','hex')||
          convert_to(paprnav_v4_jcs(jsonb_build_object(
            'table','semantic-node','identity',jsonb_build_object(
              'projectionId',projection.id,'nodeType',node.node_type,
              'nodeKey',node.node_key,'pointer',node.source_pointer))),'UTF8')),'hex') END;
        IF node_value IS NULL OR expected_node_type IS NULL
           OR node.node_type IS DISTINCT FROM expected_node_type
           OR node.node_key IS DISTINCT FROM expected_node_key
           OR node.parent_node_id IS DISTINCT FROM expected_parent
           OR node.canonical_ordinal IS DISTINCT FROM expected_ordinal
           OR node.canonical_node_hash IS DISTINCT FROM expected_hash
           OR node.id IS DISTINCT FROM 'avn_'||left(expected_identity,32)
           OR node.identity_hash IS DISTINCT FROM expected_identity
        THEN RAISE EXCEPTION 'V4 applicability semantic node differs from candidate: id=% type=%/% key=%/% parent=%/% ordinal=%/% canonical=%/% identity=%/%',
          node.id,node.node_type,expected_node_type,node.node_key,expected_node_key,
          node.parent_node_id,expected_parent,node.canonical_ordinal,expected_ordinal,
          node.canonical_node_hash,expected_hash,node.identity_hash,expected_identity;
        END IF;
      END LOOP;

      IF EXISTS (
        SELECT 1 FROM ad_v4_candidate_app_data datum
         WHERE datum.projection_id=projection.id AND (
           datum.semantic_node_id IS DISTINCT FROM (
             SELECT owner.id FROM ad_v4_candidate_app_semantic_nodes owner
              WHERE owner.projection_id=projection.id AND owner.node_type<>'identity_mapping'
                AND (datum.json_pointer=owner.source_pointer OR datum.json_pointer LIKE owner.source_pointer||'/%')
              ORDER BY length(owner.source_pointer) DESC LIMIT 1)
           OR datum.value_hash<>encode(sha256(
             convert_to('paprnav:ad_extraction_v4:applicability-row:2','UTF8')||decode('00','hex')||
             convert_to(paprnav_v4_jcs(jsonb_build_object(
               'table','datum','identity',jsonb_build_object(
                 'projectionId',projection.id,'pointer',datum.json_pointer,
                 'kind',datum.value_kind,'value',CASE
                   WHEN datum.value_kind='string' THEN to_jsonb(datum.string_value)
                   WHEN datum.value_kind='boolean' THEN to_jsonb(datum.boolean_value)
                   ELSE to_jsonb(datum.value_kind) END))),'UTF8')),'hex'))
      ) THEN RAISE EXCEPTION 'V4 applicability datum ownership or identity differs'; END IF;

      -- Every semantic node, including target-local incoming dependency nodes,
      -- has exactly one physical owner of the matching type. No typed row may
      -- hang off another type.
      IF EXISTS (
        SELECT 1 FROM ad_v4_candidate_app_semantic_nodes n
         WHERE n.projection_id=projection.id
           AND n.node_type IN ('value_assertion','identity_mapping','product_scope','designation_scope','designation_value','designation_range','condition','designation_group','designation_group_member','applicability_rule','expression','search_hint','search_hint_group','search_hint_model','change_dependency')
           AND (CASE n.node_type
             WHEN 'value_assertion' THEN (SELECT count(*) FROM ad_v4_candidate_app_value_assertions o WHERE o.semantic_node_id=n.id)
             WHEN 'identity_mapping' THEN (SELECT count(*) FROM ad_v4_candidate_app_identity_mappings o WHERE o.semantic_node_id=n.id)
             WHEN 'product_scope' THEN (SELECT count(*) FROM ad_v4_candidate_app_product_scopes o WHERE o.semantic_node_id=n.id)
             WHEN 'designation_scope' THEN (SELECT count(*) FROM ad_v4_candidate_app_designation_scopes o WHERE o.semantic_node_id=n.id)
             WHEN 'designation_value' THEN (SELECT count(*) FROM ad_v4_candidate_app_designation_values o WHERE o.semantic_node_id=n.id)
             WHEN 'designation_range' THEN (SELECT count(*) FROM ad_v4_candidate_app_designation_ranges o WHERE o.semantic_node_id=n.id)
             WHEN 'condition' THEN (SELECT count(*) FROM ad_v4_candidate_app_conditions o WHERE o.semantic_node_id=n.id)
             WHEN 'designation_group' THEN (SELECT count(*) FROM ad_v4_candidate_app_designation_groups o WHERE o.semantic_node_id=n.id)
             WHEN 'designation_group_member' THEN (SELECT count(*) FROM ad_v4_candidate_app_designation_group_members o WHERE o.semantic_node_id=n.id)
             WHEN 'applicability_rule' THEN (SELECT count(*) FROM ad_v4_candidate_app_rules o WHERE o.semantic_node_id=n.id)
             WHEN 'expression' THEN (SELECT count(*) FROM ad_v4_candidate_app_expressions o WHERE o.semantic_node_id=n.id)
             WHEN 'search_hint' THEN (SELECT count(*) FROM ad_v4_candidate_app_search_hints o WHERE o.semantic_node_id=n.id)
             WHEN 'search_hint_group' THEN (SELECT count(*) FROM ad_v4_candidate_app_search_hint_groups o WHERE o.semantic_node_id=n.id)
             WHEN 'search_hint_model' THEN (SELECT count(*) FROM ad_v4_candidate_app_search_hint_members o WHERE o.semantic_node_id=n.id)
             WHEN 'change_dependency' THEN (SELECT count(*) FROM ad_v4_candidate_app_change_dependencies o WHERE o.semantic_node_id=n.id)
           END)<>1
      ) OR EXISTS (
        SELECT 1 FROM (
          SELECT semantic_node_id,projection_id,'value_assertion' AS owner_type FROM ad_v4_candidate_app_value_assertions
          UNION ALL SELECT semantic_node_id,projection_id,'identity_mapping' FROM ad_v4_candidate_app_identity_mappings
          UNION ALL SELECT semantic_node_id,projection_id,'product_scope' FROM ad_v4_candidate_app_product_scopes
          UNION ALL SELECT semantic_node_id,projection_id,'designation_scope' FROM ad_v4_candidate_app_designation_scopes
          UNION ALL SELECT semantic_node_id,projection_id,'designation_value' FROM ad_v4_candidate_app_designation_values
          UNION ALL SELECT semantic_node_id,projection_id,'designation_range' FROM ad_v4_candidate_app_designation_ranges
          UNION ALL SELECT semantic_node_id,projection_id,'condition' FROM ad_v4_candidate_app_conditions
          UNION ALL SELECT semantic_node_id,projection_id,'designation_group' FROM ad_v4_candidate_app_designation_groups
          UNION ALL SELECT semantic_node_id,projection_id,'designation_group_member' FROM ad_v4_candidate_app_designation_group_members
          UNION ALL SELECT semantic_node_id,projection_id,'applicability_rule' FROM ad_v4_candidate_app_rules
          UNION ALL SELECT semantic_node_id,projection_id,'expression' FROM ad_v4_candidate_app_expressions
          UNION ALL SELECT semantic_node_id,projection_id,'search_hint' FROM ad_v4_candidate_app_search_hints
          UNION ALL SELECT semantic_node_id,projection_id,'search_hint_group' FROM ad_v4_candidate_app_search_hint_groups
          UNION ALL SELECT semantic_node_id,projection_id,'search_hint_model' FROM ad_v4_candidate_app_search_hint_members
          UNION ALL SELECT semantic_node_id,projection_id,'change_dependency' FROM ad_v4_candidate_app_change_dependencies
        ) owner
        JOIN ad_v4_candidate_app_semantic_nodes n ON n.id=owner.semantic_node_id
       WHERE owner.projection_id=projection.id AND n.node_type<>owner.owner_type
      ) THEN RAISE EXCEPTION 'V4 semantic ownership differs'; END IF;

      IF EXISTS (
        SELECT 1 FROM ad_v4_candidate_app_identity_mappings m
         WHERE m.projection_id=projection.id AND (
           m.id<>'avi_'||left(m.identity_hash,32)
           OR m.identity_hash<>encode(sha256(
             convert_to('paprnav:ad_extraction_v4:applicability-row:2','UTF8')||decode('00','hex')||
             convert_to(paprnav_v4_jcs(jsonb_build_object(
               'table','identity-mapping','identity',jsonb_build_object(
                 'projectionId',projection.id,'kind',m.identity_kind,
                 'occurrence',m.source_occurrence_node_id))),'UTF8')),'hex')
           OR m.review_state<>'unreviewed_candidate'
           OR NOT EXISTS (
             SELECT 1
               FROM ad_v4_candidate_app_semantic_nodes mapping_node
               JOIN ad_v4_candidate_app_semantic_nodes occurrence
                 ON occurrence.id=m.source_occurrence_node_id
              WHERE mapping_node.id=m.semantic_node_id
                AND mapping_node.projection_id=m.projection_id
                AND mapping_node.proposal_id=m.proposal_id
                AND occurrence.projection_id=m.projection_id
                AND occurrence.proposal_id=m.proposal_id
                AND mapping_node.node_type='identity_mapping'
                AND mapping_node.parent_node_id=occurrence.id
                AND mapping_node.node_key=occurrence.id
                AND mapping_node.source_pointer=occurrence.source_pointer
                AND mapping_node.canonical_node_hash=occurrence.canonical_node_hash
                AND mapping_node.canonical_ordinal=occurrence.canonical_ordinal
           )
         )
      ) THEN RAISE EXCEPTION 'V4 identity-mapping identity differs'; END IF;

      IF EXISTS (
        WITH expected AS (
          SELECT '/productScopes/'||(p.ordinality-1) AS pointer,p.value
            FROM jsonb_array_elements(subtree->'productScopes') WITH ORDINALITY p(value,ordinality)
        ), actual AS (
          SELECT n.source_pointer AS pointer,o.*,n.id AS node_id
            FROM ad_v4_candidate_app_product_scopes o
            JOIN ad_v4_candidate_app_semantic_nodes n ON n.id=o.semantic_node_id
           WHERE o.projection_id=projection.id
        )
        SELECT 1 FROM expected e FULL JOIN actual a USING(pointer)
         WHERE e.pointer IS NULL OR a.pointer IS NULL
            OR a.proposal_id<>proposal.id OR a.node_id<>a.semantic_node_id
            OR a.scope_key IS DISTINCT FROM e.value->>'scopeKey'
            OR a.product_role IS DISTINCT FROM e.value->>'productRole'
            OR a.manufacturer_presence IS DISTINCT FROM CASE WHEN e.value ? 'manufacturer' THEN 'present' ELSE 'property_absent' END
            OR a.manufacturer_source_value IS DISTINCT FROM e.value->'manufacturer'->>'sourceValue'
            OR a.model_presence IS DISTINCT FROM CASE WHEN e.value ? 'modelScope' THEN 'present' ELSE 'property_absent' END
            OR a.serial_presence IS DISTINCT FROM CASE WHEN e.value ? 'serialScope' THEN 'present' ELSE 'property_absent' END
            OR a.part_number_presence IS DISTINCT FROM CASE WHEN e.value ? 'partNumberScope' THEN 'present' ELSE 'property_absent' END
            OR (e.value ? 'manufacturer' AND NOT EXISTS (
              SELECT 1
                FROM ad_v4_candidate_app_value_assertions assertion
                JOIN ad_v4_candidate_app_semantic_nodes an ON an.id=assertion.semantic_node_id
                JOIN ad_v4_candidate_app_identity_mappings mapping
                  ON mapping.semantic_node_id=a.manufacturer_identity_mapping_node_id
                JOIN ad_v4_candidate_app_semantic_nodes mn ON mn.id=mapping.semantic_node_id
               WHERE assertion.parent_semantic_node_id=a.semantic_node_id
                 AND assertion.field_code='manufacturer' AND assertion.state='known'
                 AND assertion.value_type='text'
                 AND assertion.text_value=e.value->'manufacturer'->>'sourceValue'
                 AND assertion.reason IS NULL AND assertion.temporal_scope IS NULL
                 AND an.source_pointer=e.pointer||'/manufacturer/sourceValue'
                 AND mapping.source_occurrence_node_id=assertion.semantic_node_id
                 AND mapping.evidence_parent_node_id=a.semantic_node_id
                 AND mapping.identity_kind='manufacturer'
                 AND mapping.source_value=e.value->'manufacturer'->>'sourceValue'
                 AND mn.parent_node_id=assertion.semantic_node_id
                 AND CASE WHEN e.value->'manufacturer'->'normalizedIdentity'->>'state'='known'
                   THEN mapping.normalization_origin='candidate_payload'
                     AND mapping.normalized_state='known'
                     AND mapping.normalized_value=e.value->'manufacturer'->'normalizedIdentity'->>'value'
                     AND mapping.reason IS NULL AND mapping.temporal_scope IS NULL
                     AND mapping.normalization_namespace='candidate' AND mapping.normalization_version='1'
                   ELSE mapping.normalization_origin='candidate_payload'
                     AND mapping.normalized_state=e.value->'manufacturer'->'normalizedIdentity'->>'state'
                     AND mapping.normalized_value IS NULL
                     AND mapping.reason=e.value->'manufacturer'->'normalizedIdentity'->>'reason'
                     AND mapping.temporal_scope=e.value->'manufacturer'->'normalizedIdentity'->'temporalScope'->>'kind'
                     AND mapping.normalization_namespace IS NULL AND mapping.normalization_version IS NULL
                 END
            ))
      ) THEN RAISE EXCEPTION 'V4 product-scope owner graph differs from candidate'; END IF;

      IF EXISTS (
        WITH expected AS (
          SELECT '/productScopes/'||(p.ordinality-1)||'/manufacturer/sourceValue' AS pointer,
                 e.value #>> '{}' AS evidence_key,(e.ordinality-1)::integer AS ordinal
            FROM jsonb_array_elements(subtree->'productScopes') WITH ORDINALITY p(value,ordinality)
            CROSS JOIN LATERAL jsonb_array_elements(CASE WHEN p.value ? 'manufacturer'
              THEN p.value->'manufacturer'->'normalizedIdentity'->'evidenceKeys' ELSE '[]'::jsonb END)
              WITH ORDINALITY e(value,ordinality)
        ), actual AS (
          SELECT n.source_pointer AS pointer,l.evidence_key,l.canonical_ordinal AS ordinal,l.purpose,l.link_hash,l.semantic_node_id,l.candidate_binding_id
            FROM ad_v4_candidate_app_evidence_links l
            JOIN ad_v4_candidate_app_semantic_nodes n ON n.id=l.semantic_node_id
           WHERE l.projection_id=projection.id AND n.node_type='value_assertion'
             AND n.source_pointer ~ '^/productScopes/[0-9]+/manufacturer/sourceValue$'
        )
        SELECT 1 FROM expected e FULL JOIN actual a USING(pointer,evidence_key,ordinal)
         WHERE e.pointer IS NULL OR a.pointer IS NULL OR a.purpose<>'identity_support'
            OR a.link_hash<>encode(sha256(
              convert_to('paprnav:ad_extraction_v4:applicability-row:2','UTF8')||decode('00','hex')||
              convert_to(paprnav_v4_jcs(jsonb_build_object(
                'table','evidence-link','identity',jsonb_build_object(
                  'projectionId',projection.id,'nodeId',a.semantic_node_id,
                  'purpose','identity_support','evidenceKey',a.evidence_key))),'UTF8')),'hex')
            OR NOT EXISTS (SELECT 1 FROM ad_v4_candidate_evidence_bindings b
              WHERE b.id=a.candidate_binding_id AND b.proposal_id=proposal.id AND b.evidence_key=a.evidence_key)
      ) THEN RAISE EXCEPTION 'V4 source assertion evidence differs from candidate'; END IF;

      IF EXISTS (
        WITH expected AS (
          SELECT '/productScopes/'||(p.ordinality-1)||'/'||f.field_name AS pointer,
                 '/productScopes/'||(p.ordinality-1) AS product_pointer,
                 f.field_kind,f.value
            FROM jsonb_array_elements(subtree->'productScopes') WITH ORDINALITY p(value,ordinality)
            CROSS JOIN LATERAL (VALUES
              ('modelScope','model',p.value->'modelScope'),
              ('serialScope','serial',p.value->'serialScope'),
              ('partNumberScope','part_number',p.value->'partNumberScope')
            ) f(field_name,field_kind,value)
           WHERE f.value IS NOT NULL
        ), actual AS (
          SELECT n.source_pointer AS pointer,pn.source_pointer AS product_pointer,o.*
            FROM ad_v4_candidate_app_designation_scopes o
            JOIN ad_v4_candidate_app_semantic_nodes n ON n.id=o.semantic_node_id
            JOIN ad_v4_candidate_app_semantic_nodes pn ON pn.id=o.product_scope_node_id
           WHERE o.projection_id=projection.id
        )
        SELECT 1 FROM expected e FULL JOIN actual a USING(pointer)
         WHERE e.pointer IS NULL OR a.pointer IS NULL
            OR a.product_pointer IS DISTINCT FROM e.product_pointer
            OR a.field_kind IS DISTINCT FROM e.field_kind
            OR a.scope_kind IS DISTINCT FROM e.value->>'kind'
            OR a.series_expression IS DISTINCT FROM e.value->>'expression'
            OR a.reason IS DISTINCT FROM e.value->>'reason'
            OR a.temporal_scope IS DISTINCT FROM e.value->'temporalScope'->>'kind'
            OR a.evaluation_state IS DISTINCT FROM CASE WHEN e.value->>'kind'='series_expression' THEN 'unknown' ELSE 'unevaluated' END
            OR a.evaluator_contract IS DISTINCT FROM CASE WHEN e.value->>'kind'='series_expression' THEN 'unsupported_expression' ELSE 'none' END
            OR (SELECT count(*) FROM ad_v4_candidate_app_designation_values v WHERE v.designation_scope_id=a.semantic_node_id)
               <>CASE WHEN e.value->>'kind'='listed' THEN jsonb_array_length(e.value->'sourceDesignations') ELSE 0 END
            OR (SELECT count(*) FROM ad_v4_candidate_app_designation_ranges r WHERE r.designation_scope_id=a.semantic_node_id)
               <>CASE WHEN e.value->>'kind'='ranges' THEN jsonb_array_length(e.value->'ranges') ELSE 0 END
      ) THEN RAISE EXCEPTION 'V4 designation-scope owner graph differs from candidate'; END IF;

      IF EXISTS (
        WITH expected AS (
          SELECT '/productScopes/'||(p.ordinality-1)||'/'||f.field_name||'/sourceDesignations/'||(v.ordinality-1) AS pointer,
                 '/productScopes/'||(p.ordinality-1)||'/'||f.field_name AS scope_pointer,
                 v.value #>> '{}' AS source_value,(v.ordinality-1)::integer AS ordinal
            FROM jsonb_array_elements(subtree->'productScopes') WITH ORDINALITY p(value,ordinality)
            CROSS JOIN LATERAL (VALUES ('modelScope',p.value->'modelScope'),('serialScope',p.value->'serialScope'),('partNumberScope',p.value->'partNumberScope')) f(field_name,value)
            CROSS JOIN LATERAL jsonb_array_elements(CASE WHEN f.value->>'kind'='listed' THEN f.value->'sourceDesignations' ELSE '[]'::jsonb END) WITH ORDINALITY v(value,ordinality)
        ), actual AS (
          SELECT n.source_pointer AS pointer,sn.source_pointer AS scope_pointer,o.*
            FROM ad_v4_candidate_app_designation_values o
            JOIN ad_v4_candidate_app_semantic_nodes n ON n.id=o.semantic_node_id
            JOIN ad_v4_candidate_app_semantic_nodes sn ON sn.id=o.designation_scope_id
           WHERE o.projection_id=projection.id
        )
        SELECT 1 FROM expected e FULL JOIN actual a USING(pointer)
         WHERE e.pointer IS NULL OR a.pointer IS NULL
            OR a.scope_pointer IS DISTINCT FROM e.scope_pointer
            OR a.source_value IS DISTINCT FROM e.source_value
            OR a.canonical_ordinal IS DISTINCT FROM e.ordinal
            OR (a.scope_pointer LIKE '%/modelScope' AND NOT EXISTS (
              SELECT 1 FROM ad_v4_candidate_app_identity_mappings m
              JOIN ad_v4_candidate_app_semantic_nodes mn ON mn.id=m.semantic_node_id
               WHERE m.semantic_node_id=a.identity_mapping_node_id
                 AND m.source_occurrence_node_id=a.semantic_node_id
                 AND m.evidence_parent_node_id=a.designation_scope_id
                 AND m.identity_kind='model'
                 AND m.source_value=e.source_value
                 AND m.normalization_origin='no_normalized_identity'
                 AND m.normalized_state='unknown' AND m.normalized_value IS NULL
                 AND m.reason='not_extracted' AND m.temporal_scope='directive_version'
                 AND m.normalization_namespace IS NULL AND m.normalization_version IS NULL
                 AND m.review_state='unreviewed_candidate'
                 AND mn.parent_node_id=a.semantic_node_id))
            OR (a.scope_pointer NOT LIKE '%/modelScope' AND a.identity_mapping_node_id IS NOT NULL)
      ) THEN RAISE EXCEPTION 'V4 designation-value owner graph differs from candidate'; END IF;

      IF EXISTS (
        WITH expected AS (
          SELECT '/productScopes/'||(p.ordinality-1)||'/'||f.field_name||'/ranges/'||(r.ordinality-1) AS pointer,
                 '/productScopes/'||(p.ordinality-1)||'/'||f.field_name AS scope_pointer,
                 r.value,(r.ordinality-1)::integer AS ordinal
            FROM jsonb_array_elements(subtree->'productScopes') WITH ORDINALITY p(value,ordinality)
            CROSS JOIN LATERAL (VALUES ('modelScope',p.value->'modelScope'),('serialScope',p.value->'serialScope'),('partNumberScope',p.value->'partNumberScope')) f(field_name,value)
            CROSS JOIN LATERAL jsonb_array_elements(CASE WHEN f.value->>'kind'='ranges' THEN f.value->'ranges' ELSE '[]'::jsonb END) WITH ORDINALITY r(value,ordinality)
        ), actual AS (
          SELECT n.source_pointer AS pointer,sn.source_pointer AS scope_pointer,o.*
            FROM ad_v4_candidate_app_designation_ranges o
            JOIN ad_v4_candidate_app_semantic_nodes n ON n.id=o.semantic_node_id
            JOIN ad_v4_candidate_app_semantic_nodes sn ON sn.id=o.designation_scope_id
           WHERE o.projection_id=projection.id
        )
        SELECT 1 FROM expected e FULL JOIN actual a USING(pointer)
         WHERE e.pointer IS NULL OR a.pointer IS NULL OR a.scope_pointer IS DISTINCT FROM e.scope_pointer
            OR a.lower_value IS DISTINCT FROM e.value->>'lower' OR a.upper_value IS DISTINCT FROM e.value->>'upper'
            OR a.lower_inclusive IS DISTINCT FROM (e.value->>'lowerInclusive')::boolean
            OR a.upper_inclusive IS DISTINCT FROM (e.value->>'upperInclusive')::boolean
            OR a.polarity IS DISTINCT FROM e.value->>'polarity'
            OR a.canonical_ordinal IS DISTINCT FROM e.ordinal
            OR a.comparator_version<>'lexical_source_only_v1'
      ) THEN RAISE EXCEPTION 'V4 designation-range owner graph differs from candidate'; END IF;

      IF EXISTS (
        WITH expected AS (
          SELECT n.id AS semantic_node_id,
                 CASE n.node_type WHEN 'product_scope' THEN 'scope_clause' ELSE 'designation_scope' END AS purpose,
                 e.value #>> '{}' AS evidence_key,(e.ordinality-1)::integer AS ordinal
            FROM ad_v4_candidate_app_semantic_nodes n
            CROSS JOIN LATERAL jsonb_array_elements(
              paprnav_v4_pointer_value(subtree,n.source_pointer)->'evidenceKeys'
            ) WITH ORDINALITY e(value,ordinality)
           WHERE n.projection_id=projection.id AND n.node_type IN ('product_scope','designation_scope')
        ), actual AS (
          SELECT l.semantic_node_id,l.purpose,l.evidence_key,l.canonical_ordinal AS ordinal,
                 l.id,l.link_hash,l.candidate_binding_id
            FROM ad_v4_candidate_app_evidence_links l
            JOIN ad_v4_candidate_app_semantic_nodes n ON n.id=l.semantic_node_id
           WHERE l.projection_id=projection.id AND n.node_type IN ('product_scope','designation_scope')
        )
        SELECT 1 FROM expected e FULL JOIN actual a USING(semantic_node_id,purpose,evidence_key,ordinal)
         WHERE e.semantic_node_id IS NULL OR a.semantic_node_id IS NULL
            OR a.id<>'avl_'||left(a.link_hash,32)
            OR a.link_hash<>encode(sha256(
              convert_to('paprnav:ad_extraction_v4:applicability-row:2','UTF8')||decode('00','hex')||
              convert_to(paprnav_v4_jcs(jsonb_build_object(
                'table','evidence-link','identity',jsonb_build_object(
                  'projectionId',projection.id,'nodeId',a.semantic_node_id,
                  'purpose',a.purpose,'evidenceKey',a.evidence_key))),'UTF8')),'hex')
            OR NOT EXISTS (SELECT 1 FROM ad_v4_candidate_evidence_bindings b
              WHERE b.id=a.candidate_binding_id AND b.proposal_id=proposal.id AND b.evidence_key=a.evidence_key)
      ) THEN RAISE EXCEPTION 'V4 product/designation evidence differs from candidate'; END IF;

      -- Conditions are compared as a closed family.  The canonical object is
      -- authoritative for optional-property presence as well as scalar values.
      IF EXISTS (
        WITH expected AS (
          SELECT '/conditionDefinitions/'||(c.ordinality-1) AS pointer,c.value
            FROM jsonb_array_elements(subtree->'conditionDefinitions') WITH ORDINALITY c(value,ordinality)
        ), actual AS (
          SELECT n.source_pointer AS pointer,o.*
            FROM ad_v4_candidate_app_conditions o
            JOIN ad_v4_candidate_app_semantic_nodes n ON n.id=o.semantic_node_id
           WHERE o.projection_id=projection.id
        )
        SELECT 1 FROM expected e FULL JOIN actual a USING(pointer)
         WHERE e.pointer IS NULL OR a.pointer IS NULL
            OR a.proposal_id IS DISTINCT FROM proposal.id
            OR a.condition_key IS DISTINCT FROM e.value->>'conditionKey'
            OR a.condition_type IS DISTINCT FROM e.value->>'conditionType'
            OR a.operator IS DISTINCT FROM e.value->>'operator'
            OR a.temporal_basis IS DISTINCT FROM e.value->'temporalBasis'->>'kind'
            OR a.comparator_presence IS DISTINCT FROM CASE WHEN e.value ? 'comparatorVersion' THEN 'present' ELSE 'property_absent' END
            OR a.comparator_version IS DISTINCT FROM e.value->>'comparatorVersion'
            OR a.subject_product_role_presence IS DISTINCT FROM CASE WHEN e.value->'subject' ? 'productRole' THEN 'present' ELSE 'property_absent' END
            OR a.subject_product_role IS DISTINCT FROM e.value->'subject'->>'productRole'
            OR a.subject_attribute_key_presence IS DISTINCT FROM CASE WHEN e.value->'subject' ? 'attributeKey' THEN 'present' ELSE 'property_absent' END
            OR a.subject_attribute_key IS DISTINCT FROM e.value->'subject'->>'attributeKey'
            OR a.designation_group_presence IS DISTINCT FROM CASE WHEN e.value->'subject' ? 'designationGroup' THEN 'present' ELSE 'property_absent' END
            OR a.designation_group_node_id IS DISTINCT FROM CASE WHEN e.value->'subject' ? 'designationGroup' THEN
                 (SELECT n.id FROM ad_v4_candidate_app_semantic_nodes n
                   WHERE n.projection_id=projection.id AND n.node_type='designation_group'
                     AND n.source_pointer=e.pointer||'/subject/designationGroup') ELSE NULL END
            OR a.evaluation_state<>'unevaluated' OR a.evaluator_contract<>'none'
      ) THEN RAISE EXCEPTION 'V4 condition owner graph differs from candidate'; END IF;

      IF EXISTS (
        WITH conditions AS (
          SELECT '/conditionDefinitions/'||(c.ordinality-1) AS pointer,c.value
            FROM jsonb_array_elements(subtree->'conditionDefinitions') WITH ORDINALITY c(value,ordinality)
        ), expected AS (
          SELECT c.pointer||'/subject/'||f.key AS pointer,c.pointer AS parent_pointer,
                 CASE f.key WHEN 'modelOrSeries' THEN 'model_or_series'
                   WHEN 'partNumber' THEN 'part_number' WHEN 'serialNumber' THEN 'serial_number'
                   WHEN 'stcNumber' THEN 'stc_number' WHEN 'attributeValue' THEN 'attribute_value'
                   ELSE 'manufacturer' END AS field_code,
                 f.value,'subject_value'::text AS purpose
            FROM conditions c CROSS JOIN LATERAL jsonb_each(c.value->'subject') f
           WHERE f.key IN ('manufacturer','modelOrSeries','partNumber','serialNumber','stcNumber','attributeValue')
          UNION ALL
          SELECT c.pointer||'/subject/designationGroup/sourceDisplayText',
                 c.pointer||'/subject/designationGroup','source_display_text',
                 c.value->'subject'->'designationGroup'->'sourceDisplayText','subject_value'
            FROM conditions c WHERE c.value->'subject' ? 'designationGroup'
          UNION ALL
          SELECT c.pointer||'/subject/designationGroup/members/'||(m.ordinality-1)||'/manufacturer',
                 c.pointer||'/subject/designationGroup/members/'||(m.ordinality-1),
                 'manufacturer',m.value->'manufacturer','identity_support'
            FROM conditions c
            CROSS JOIN LATERAL jsonb_array_elements(CASE WHEN c.value->'subject' ? 'designationGroup'
              THEN c.value->'subject'->'designationGroup'->'members' ELSE '[]'::jsonb END)
              WITH ORDINALITY m(value,ordinality)
        ), actual AS (
          SELECT n.source_pointer AS pointer,pn.source_pointer AS parent_pointer,o.*
            FROM ad_v4_candidate_app_value_assertions o
            JOIN ad_v4_candidate_app_semantic_nodes n ON n.id=o.semantic_node_id
            JOIN ad_v4_candidate_app_semantic_nodes pn ON pn.id=o.parent_semantic_node_id
           WHERE o.projection_id=projection.id
             AND n.source_pointer ~ '^/conditionDefinitions/[0-9]+/'
        )
        SELECT 1 FROM expected e FULL JOIN actual a USING(pointer)
         WHERE e.pointer IS NULL OR a.pointer IS NULL
            OR a.proposal_id IS DISTINCT FROM proposal.id
            OR a.parent_pointer IS DISTINCT FROM e.parent_pointer
            OR a.field_code IS DISTINCT FROM e.field_code OR a.value_type<>'text'
            OR a.state IS DISTINCT FROM e.value->>'state'
            OR a.text_value IS DISTINCT FROM e.value->>'value'
            OR a.reason IS DISTINCT FROM e.value->>'reason'
            OR a.temporal_scope IS DISTINCT FROM e.value->'temporalScope'->>'kind'
      ) THEN RAISE EXCEPTION 'V4 condition value-assertion graph differs from candidate'; END IF;

      IF EXISTS (
        WITH conditions AS (
          SELECT '/conditionDefinitions/'||(c.ordinality-1) AS condition_pointer,c.value->'subject'->'designationGroup' AS value
            FROM jsonb_array_elements(subtree->'conditionDefinitions') WITH ORDINALITY c(value,ordinality)
           WHERE c.value->'subject' ? 'designationGroup'
        ), expected AS (
          SELECT condition_pointer||'/subject/designationGroup' AS pointer,condition_pointer,value
            FROM conditions
        ), actual AS (
          SELECT n.source_pointer AS pointer,cn.source_pointer AS condition_pointer,o.*
            FROM ad_v4_candidate_app_designation_groups o
            JOIN ad_v4_candidate_app_semantic_nodes n ON n.id=o.semantic_node_id
            JOIN ad_v4_candidate_app_semantic_nodes cn ON cn.id=o.condition_node_id
           WHERE o.projection_id=projection.id
        )
        SELECT 1 FROM expected e FULL JOIN actual a USING(pointer)
         WHERE e.pointer IS NULL OR a.pointer IS NULL
            OR a.proposal_id IS DISTINCT FROM proposal.id
            OR a.condition_pointer IS DISTINCT FROM e.condition_pointer
            OR a.group_key IS DISTINCT FROM e.value->>'groupKey'
            OR a.association IS DISTINCT FROM e.value->>'association'
            OR a.source_display_assertion_node_id IS DISTINCT FROM (
                 SELECT n.id FROM ad_v4_candidate_app_semantic_nodes n
                  WHERE n.projection_id=projection.id AND n.node_type='value_assertion'
                    AND n.source_pointer=e.pointer||'/sourceDisplayText')
            OR a.reason IS DISTINCT FROM e.value->>'reason'
            OR a.temporal_scope IS DISTINCT FROM e.value->'temporalScope'->>'kind'
            OR a.canonical_ordinal<>0
            OR (SELECT count(*) FROM ad_v4_candidate_app_designation_group_members m
                 WHERE m.group_node_id=a.semantic_node_id)<>jsonb_array_length(e.value->'members')
      ) THEN RAISE EXCEPTION 'V4 condition designation-group graph differs from candidate'; END IF;

      IF EXISTS (
        WITH groups AS (
          SELECT '/conditionDefinitions/'||(c.ordinality-1)||'/subject/designationGroup' AS pointer,
                 c.value->'subject'->'designationGroup' AS value
            FROM jsonb_array_elements(subtree->'conditionDefinitions') WITH ORDINALITY c(value,ordinality)
           WHERE c.value->'subject' ? 'designationGroup'
        ), expected AS (
          SELECT g.pointer||'/members/'||(m.ordinality-1) AS pointer,g.pointer AS group_pointer,
                 m.value,(m.ordinality-1)::integer AS ordinal
            FROM groups g CROSS JOIN LATERAL jsonb_array_elements(g.value->'members') WITH ORDINALITY m(value,ordinality)
        ), actual AS (
          SELECT n.source_pointer AS pointer,gn.source_pointer AS group_pointer,o.*
            FROM ad_v4_candidate_app_designation_group_members o
            JOIN ad_v4_candidate_app_semantic_nodes n ON n.id=o.semantic_node_id
            JOIN ad_v4_candidate_app_semantic_nodes gn ON gn.id=o.group_node_id
           WHERE o.projection_id=projection.id
        )
        SELECT 1 FROM expected e FULL JOIN actual a USING(pointer)
         WHERE e.pointer IS NULL OR a.pointer IS NULL
            OR a.proposal_id IS DISTINCT FROM proposal.id
            OR a.group_pointer IS DISTINCT FROM e.group_pointer
            OR a.member_key IS DISTINCT FROM e.value->>'memberKey'
            OR a.designation_kind IS DISTINCT FROM e.value->>'designationKind'
            OR a.source_designation IS DISTINCT FROM e.value->>'sourceDesignation'
            OR a.expression_text IS DISTINCT FROM e.value->>'expressionText'
            OR a.manufacturer_assertion_node_id IS DISTINCT FROM (
                 SELECT n.id FROM ad_v4_candidate_app_semantic_nodes n
                  WHERE n.projection_id=projection.id AND n.node_type='value_assertion'
                    AND n.source_pointer=e.pointer||'/manufacturer')
            OR a.manufacturer_state IS DISTINCT FROM e.value->'manufacturer'->>'state'
            OR a.manufacturer_value IS DISTINCT FROM e.value->'manufacturer'->>'value'
            OR a.manufacturer_reason IS DISTINCT FROM e.value->'manufacturer'->>'reason'
            OR a.manufacturer_temporal_scope IS DISTINCT FROM e.value->'manufacturer'->'temporalScope'->>'kind'
            OR a.evaluation_state IS DISTINCT FROM CASE WHEN e.value->>'designationKind'='series_expression' THEN 'unevaluated' ELSE NULL END
            OR a.evaluation_reason IS DISTINCT FROM CASE WHEN e.value->>'designationKind'='series_expression' THEN 'unsupported_expression' ELSE NULL END
            OR a.canonical_ordinal IS DISTINCT FROM e.ordinal
            OR a.designation_identity_mapping_node_id IS DISTINCT FROM (
                 SELECT m.semantic_node_id FROM ad_v4_candidate_app_identity_mappings m
                 JOIN ad_v4_candidate_app_semantic_nodes occurrence ON occurrence.id=m.source_occurrence_node_id
                  WHERE m.projection_id=projection.id AND occurrence.source_pointer=e.pointer)
      ) THEN RAISE EXCEPTION 'V4 condition designation-member graph differs from candidate'; END IF;

      -- Every condition-family identity mapping is exact and no additional
      -- mapping can be hidden behind a self-consistent envelope/hash count.
      IF EXISTS (
        WITH conditions AS (
          SELECT '/conditionDefinitions/'||(c.ordinality-1) AS pointer,c.value
            FROM jsonb_array_elements(subtree->'conditionDefinitions') WITH ORDINALITY c(value,ordinality)
        ), expected AS (
          SELECT c.pointer||'/subject/'||f.key AS occurrence_pointer,c.pointer AS context_pointer,
                 CASE f.key WHEN 'manufacturer' THEN 'manufacturer' ELSE 'model_or_series' END AS identity_kind,
                 f.value->>'value' AS source_value
            FROM conditions c CROSS JOIN LATERAL jsonb_each(c.value->'subject') f
           WHERE f.key IN ('manufacturer','modelOrSeries') AND f.value->>'state'='known'
          UNION ALL
          SELECT c.pointer||'/subject/designationGroup/members/'||(m.ordinality-1),
                 c.pointer||'/subject/designationGroup',
                 CASE WHEN m.value->>'designationKind'='model' THEN 'model' ELSE 'series' END,
                 CASE WHEN m.value->>'designationKind'='model' THEN m.value->>'sourceDesignation' ELSE m.value->>'expressionText' END
            FROM conditions c CROSS JOIN LATERAL jsonb_array_elements(CASE WHEN c.value->'subject' ? 'designationGroup'
              THEN c.value->'subject'->'designationGroup'->'members' ELSE '[]'::jsonb END) WITH ORDINALITY m(value,ordinality)
          UNION ALL
          SELECT c.pointer||'/subject/designationGroup/members/'||(m.ordinality-1)||'/manufacturer',
                 c.pointer||'/subject/designationGroup','manufacturer',m.value->'manufacturer'->>'value'
            FROM conditions c CROSS JOIN LATERAL jsonb_array_elements(CASE WHEN c.value->'subject' ? 'designationGroup'
              THEN c.value->'subject'->'designationGroup'->'members' ELSE '[]'::jsonb END) WITH ORDINALITY m(value,ordinality)
           WHERE m.value->'manufacturer'->>'state'='known'
        ), actual AS (
          SELECT occurrence.source_pointer AS occurrence_pointer,context.source_pointer AS context_pointer,
                 m.*
            FROM ad_v4_candidate_app_identity_mappings m
            JOIN ad_v4_candidate_app_semantic_nodes occurrence ON occurrence.id=m.source_occurrence_node_id
            JOIN ad_v4_candidate_app_semantic_nodes context ON context.id=m.evidence_parent_node_id
           WHERE m.projection_id=projection.id
             AND occurrence.source_pointer ~ '^/conditionDefinitions/[0-9]+/'
        )
        SELECT 1 FROM expected e FULL JOIN actual a USING(occurrence_pointer)
         WHERE e.occurrence_pointer IS NULL OR a.occurrence_pointer IS NULL
            OR a.proposal_id IS DISTINCT FROM proposal.id
            OR a.context_pointer IS DISTINCT FROM e.context_pointer
            OR a.identity_kind IS DISTINCT FROM e.identity_kind
            OR a.source_value IS DISTINCT FROM e.source_value
            OR a.normalization_origin<>'source_only' OR a.normalized_state<>'unknown'
            OR a.normalized_value IS NOT NULL OR a.reason<>'not_extracted'
            OR a.temporal_scope<>'directive_version'
            OR a.normalization_namespace IS NOT NULL OR a.normalization_version IS NOT NULL
            OR a.review_state<>'unreviewed_candidate'
      ) THEN RAISE EXCEPTION 'V4 condition identity-mapping graph differs from candidate'; END IF;

      IF EXISTS (
        WITH conditions AS (
          SELECT '/conditionDefinitions/'||(c.ordinality-1) AS pointer,c.value
            FROM jsonb_array_elements(subtree->'conditionDefinitions') WITH ORDINALITY c(value,ordinality)
        ), expected_nodes AS (
          SELECT pointer,value->'evidenceKeys' AS keys,'condition_clause'::text AS purpose FROM conditions
          UNION ALL
          SELECT c.pointer||'/subject/'||f.key,f.value->'evidenceKeys','subject_value'
            FROM conditions c CROSS JOIN LATERAL jsonb_each(c.value->'subject') f
           WHERE f.key IN ('manufacturer','modelOrSeries','partNumber','serialNumber','stcNumber','attributeValue')
          UNION ALL
          SELECT c.pointer||'/subject/designationGroup',c.value->'subject'->'designationGroup'->'evidenceKeys','condition_clause'
            FROM conditions c WHERE c.value->'subject' ? 'designationGroup'
          UNION ALL
          SELECT c.pointer||'/subject/designationGroup/sourceDisplayText',c.value->'subject'->'designationGroup'->'sourceDisplayText'->'evidenceKeys','subject_value'
            FROM conditions c WHERE c.value->'subject' ? 'designationGroup'
          UNION ALL
          SELECT c.pointer||'/subject/designationGroup/members/'||(m.ordinality-1),m.value->'evidenceKeys','subject_value'
            FROM conditions c CROSS JOIN LATERAL jsonb_array_elements(CASE WHEN c.value->'subject' ? 'designationGroup'
              THEN c.value->'subject'->'designationGroup'->'members' ELSE '[]'::jsonb END) WITH ORDINALITY m(value,ordinality)
          UNION ALL
          SELECT c.pointer||'/subject/designationGroup/members/'||(m.ordinality-1)||'/manufacturer',
                 m.value->'manufacturer'->'evidenceKeys','identity_support'
            FROM conditions c CROSS JOIN LATERAL jsonb_array_elements(CASE WHEN c.value->'subject' ? 'designationGroup'
              THEN c.value->'subject'->'designationGroup'->'members' ELSE '[]'::jsonb END) WITH ORDINALITY m(value,ordinality)
        ), expected AS (
          SELECT n.id AS semantic_node_id,e.value #>> '{}' AS evidence_key,
                 (e.ordinality-1)::integer AS ordinal,x.purpose
            FROM expected_nodes x
            JOIN ad_v4_candidate_app_semantic_nodes n
              ON n.projection_id=projection.id AND n.source_pointer=x.pointer AND n.node_type<>'identity_mapping'
            CROSS JOIN LATERAL jsonb_array_elements(x.keys) WITH ORDINALITY e(value,ordinality)
        ), actual AS (
          SELECT l.semantic_node_id,l.evidence_key,l.canonical_ordinal AS ordinal,l.purpose,
                 l.id,l.link_hash,l.candidate_binding_id
            FROM ad_v4_candidate_app_evidence_links l
            JOIN ad_v4_candidate_app_semantic_nodes n ON n.id=l.semantic_node_id
           WHERE l.projection_id=projection.id
             AND n.source_pointer ~ '^/conditionDefinitions/[0-9]+($|/)'
             AND n.node_type<>'identity_mapping'
        )
        SELECT 1 FROM expected e FULL JOIN actual a USING(semantic_node_id,evidence_key,ordinal)
         WHERE e.semantic_node_id IS NULL OR a.semantic_node_id IS NULL
            OR a.purpose IS DISTINCT FROM e.purpose
            OR a.id<>'avl_'||left(a.link_hash,32)
            OR a.link_hash<>encode(sha256(
              convert_to('paprnav:ad_extraction_v4:applicability-row:2','UTF8')||decode('00','hex')||
              convert_to(paprnav_v4_jcs(jsonb_build_object(
                'table','evidence-link','identity',jsonb_build_object(
                  'projectionId',projection.id,'nodeId',a.semantic_node_id,
                  'purpose',a.purpose,'evidenceKey',a.evidence_key))),'UTF8')),'hex')
            OR NOT EXISTS (SELECT 1 FROM ad_v4_candidate_evidence_bindings b
              WHERE b.id=a.candidate_binding_id AND b.proposal_id=proposal.id AND b.evidence_key=a.evidence_key)
      ) THEN RAISE EXCEPTION 'V4 condition evidence graph differs from candidate'; END IF;

      -- Rules, recursive expressions, ordered edges, exclusions, and their
      -- typed references are an exact projection of the canonical rule graph.
      IF subtree->'applicabilityRules' IS DISTINCT FROM (
           SELECT coalesce(jsonb_agg(value ORDER BY value->>'ruleKey'),'[]'::jsonb)
             FROM jsonb_array_elements(subtree->'applicabilityRules') value)
         OR (SELECT count(*) FROM jsonb_array_elements(subtree->'applicabilityRules'))
            <>(SELECT count(DISTINCT value->>'ruleKey') FROM jsonb_array_elements(subtree->'applicabilityRules') value)
      THEN RAISE EXCEPTION 'V4 applicability rule set is not canonical'; END IF;

      IF EXISTS (
        WITH expected AS (
          SELECT '/applicabilityRules/'||(r.ordinality-1) AS pointer,r.value
            FROM jsonb_array_elements(subtree->'applicabilityRules') WITH ORDINALITY r(value,ordinality)
        ), actual AS (
          SELECT n.source_pointer AS pointer,o.*,n.id AS node_id,
                 scope_node.source_pointer AS scope_pointer,
                 condition_node.source_pointer AS condition_pointer
            FROM ad_v4_candidate_app_rules o
            JOIN ad_v4_candidate_app_semantic_nodes n ON n.id=o.semantic_node_id
            JOIN ad_v4_candidate_app_semantic_nodes scope_node ON scope_node.id=o.scope_expression_node_id
            LEFT JOIN ad_v4_candidate_app_semantic_nodes condition_node ON condition_node.id=o.condition_expression_node_id
           WHERE o.projection_id=projection.id
        )
        SELECT 1 FROM expected e FULL JOIN actual a USING(pointer)
         WHERE e.pointer IS NULL OR a.pointer IS NULL
            OR a.proposal_id IS DISTINCT FROM proposal.id
            OR a.node_id IS DISTINCT FROM a.semantic_node_id
            OR a.rule_key IS DISTINCT FROM e.value->>'ruleKey'
            OR a.scope_pointer IS DISTINCT FROM e.pointer||'/scopeExpression'
            OR a.condition_presence IS DISTINCT FROM CASE WHEN e.value ? 'conditionExpression' THEN 'present' ELSE 'property_absent' END
            OR a.condition_pointer IS DISTINCT FROM CASE WHEN e.value ? 'conditionExpression' THEN e.pointer||'/conditionExpression' ELSE NULL END
            OR a.evaluator_contract<>'none'
            OR NOT (e.value ?& ARRAY['ruleKey','scopeExpression','exclusionRuleKeys','evidenceKeys'])
            OR (e.value-ARRAY['ruleKey','scopeExpression','conditionExpression','exclusionRuleKeys','evidenceKeys'])<>'{}'::jsonb
            OR jsonb_typeof(e.value->'ruleKey')<>'string'
            OR jsonb_typeof(e.value->'scopeExpression')<>'object'
            OR (e.value ? 'conditionExpression' AND jsonb_typeof(e.value->'conditionExpression')<>'object')
            OR jsonb_typeof(e.value->'exclusionRuleKeys')<>'array'
            OR jsonb_typeof(e.value->'evidenceKeys')<>'array'
            OR jsonb_array_length(e.value->'evidenceKeys')=0
            OR e.value->'exclusionRuleKeys' IS DISTINCT FROM (
              SELECT coalesce(jsonb_agg(x ORDER BY x #>> '{}'),'[]'::jsonb)
                FROM jsonb_array_elements(e.value->'exclusionRuleKeys') x)
            OR e.value->'evidenceKeys' IS DISTINCT FROM (
              SELECT coalesce(jsonb_agg(x ORDER BY x #>> '{}'),'[]'::jsonb)
                FROM jsonb_array_elements(e.value->'evidenceKeys') x)
      ) THEN RAISE EXCEPTION 'V4 applicability rule owners differ from candidate'; END IF;

      IF EXISTS (
        WITH actual AS (
          SELECT n.source_pointer AS pointer,n.parent_node_id,n.canonical_ordinal,o.*,
                 substring(n.source_pointer from '^(/applicabilityRules/[0-9]+)') AS rule_pointer,
                 CASE WHEN n.source_pointer ~ '^/applicabilityRules/[0-9]+/scopeExpression($|/)'
                      THEN 'scope' ELSE 'condition' END AS expected_context,
                 coalesce(nullif(regexp_replace(n.source_pointer,
                   '^/applicabilityRules/[0-9]+/(scopeExpression|conditionExpression)',''),''),'/') AS expected_path,
                 paprnav_v4_pointer_value(subtree,n.source_pointer) AS value
            FROM ad_v4_candidate_app_expressions o
            JOIN ad_v4_candidate_app_semantic_nodes n ON n.id=o.semantic_node_id
           WHERE o.projection_id=projection.id
        )
        SELECT 1 FROM actual a
         WHERE a.value IS NULL OR a.proposal_id<>proposal.id
            OR a.owning_rule_node_id IS DISTINCT FROM (
              SELECT r.id FROM ad_v4_candidate_app_semantic_nodes r
               WHERE r.projection_id=projection.id AND r.node_type='applicability_rule'
                 AND r.source_pointer=a.rule_pointer)
            OR a.expression_context IS DISTINCT FROM a.expected_context
            OR a.expression_path IS DISTINCT FROM a.expected_path
            OR a.expression_node_type IS DISTINCT FROM a.value->>'nodeType'
            OR a.result_domain<>'true_false_unknown' OR a.evaluator_contract<>'none'
            OR a.scope_node_id IS DISTINCT FROM CASE WHEN a.value->>'nodeType'='scope_ref' THEN (
              SELECT n.id FROM ad_v4_candidate_app_semantic_nodes n
               WHERE n.projection_id=projection.id AND n.node_type='product_scope'
                 AND n.node_key=a.value->>'scopeKey') ELSE NULL END
            OR a.condition_node_id IS DISTINCT FROM CASE WHEN a.value->>'nodeType'='predicate_ref' THEN (
              SELECT n.id FROM ad_v4_candidate_app_semantic_nodes n
               WHERE n.projection_id=projection.id AND n.node_type='condition'
                 AND n.node_key=a.value->>'conditionKey') ELSE NULL END
            OR a.referenced_rule_node_id IS DISTINCT FROM CASE WHEN a.value->>'nodeType'='rule_ref' THEN (
              SELECT n.id FROM ad_v4_candidate_app_semantic_nodes n
               WHERE n.projection_id=projection.id AND n.node_type='applicability_rule'
                 AND n.node_key=a.value->>'ruleKey') ELSE NULL END
            OR CASE a.value->>'nodeType'
                 WHEN 'scope_ref' THEN (a.value-ARRAY['nodeType','scopeKey'])<>'{}'::jsonb OR NOT (a.value ? 'scopeKey')
                 WHEN 'predicate_ref' THEN (a.value-ARRAY['nodeType','conditionKey'])<>'{}'::jsonb OR NOT (a.value ? 'conditionKey')
                 WHEN 'rule_ref' THEN (a.value-ARRAY['nodeType','ruleKey'])<>'{}'::jsonb OR NOT (a.value ? 'ruleKey')
                 WHEN 'not' THEN (a.value-ARRAY['nodeType','operand'])<>'{}'::jsonb OR NOT (a.value ? 'operand') OR jsonb_typeof(a.value->'operand')<>'object'
                 WHEN 'all' THEN (a.value-ARRAY['nodeType','operands'])<>'{}'::jsonb OR jsonb_typeof(a.value->'operands')<>'array' OR jsonb_array_length(a.value->'operands')<2 OR EXISTS (SELECT 1 FROM jsonb_array_elements(a.value->'operands') operand WHERE jsonb_typeof(operand)<>'object')
                 WHEN 'any' THEN (a.value-ARRAY['nodeType','operands'])<>'{}'::jsonb OR jsonb_typeof(a.value->'operands')<>'array' OR jsonb_array_length(a.value->'operands')<2 OR EXISTS (SELECT 1 FROM jsonb_array_elements(a.value->'operands') operand WHERE jsonb_typeof(operand)<>'object')
                 ELSE true END
      ) THEN RAISE EXCEPTION 'V4 applicability expression owners or references differ from candidate'; END IF;

      IF EXISTS (
        WITH expected AS (
          SELECT parent.semantic_node_id AS parent_expression_id,
                 child.semantic_node_id AS child_expression_id,
                 child_node.canonical_ordinal AS sequence,
                 parent.owning_rule_node_id,parent.expression_context
            FROM ad_v4_candidate_app_expressions child
            JOIN ad_v4_candidate_app_semantic_nodes child_node ON child_node.id=child.semantic_node_id
            JOIN ad_v4_candidate_app_expressions parent ON parent.semantic_node_id=child_node.parent_node_id
           WHERE child.projection_id=projection.id
        ), actual AS (
          SELECT * FROM ad_v4_candidate_app_expression_edges WHERE projection_id=projection.id
        )
        SELECT 1 FROM expected e FULL JOIN actual a USING(parent_expression_id,sequence)
         WHERE e.parent_expression_id IS NULL OR a.parent_expression_id IS NULL
            OR a.proposal_id IS DISTINCT FROM proposal.id
            OR a.child_expression_id IS DISTINCT FROM e.child_expression_id
            OR a.owning_rule_node_id IS DISTINCT FROM e.owning_rule_node_id
            OR a.expression_context IS DISTINCT FROM e.expression_context
      ) THEN RAISE EXCEPTION 'V4 applicability expression edge graph differs from candidate'; END IF;

      IF EXISTS (
        WITH rules AS (
          SELECT '/applicabilityRules/'||(r.ordinality-1) AS pointer,r.value
            FROM jsonb_array_elements(subtree->'applicabilityRules') WITH ORDINALITY r(value,ordinality)
        ), expected AS (
          SELECT source.id AS rule_node_id,target.id AS excluded_rule_node_id,
                 (x.ordinality-1)::integer AS canonical_ordinal
            FROM rules r
            JOIN ad_v4_candidate_app_semantic_nodes source
              ON source.projection_id=projection.id AND source.node_type='applicability_rule'
             AND source.source_pointer=r.pointer
            CROSS JOIN LATERAL jsonb_array_elements(r.value->'exclusionRuleKeys') WITH ORDINALITY x(value,ordinality)
            LEFT JOIN ad_v4_candidate_app_semantic_nodes target
              ON target.projection_id=projection.id AND target.node_type='applicability_rule'
             AND target.node_key=x.value #>> '{}'
        ), actual AS (
          SELECT * FROM ad_v4_candidate_app_rule_exclusions WHERE projection_id=projection.id
        )
        SELECT 1 FROM expected e FULL JOIN actual a USING(rule_node_id,canonical_ordinal)
         WHERE e.rule_node_id IS NULL OR a.rule_node_id IS NULL
            OR e.excluded_rule_node_id IS NULL
            OR a.proposal_id IS DISTINCT FROM proposal.id
            OR a.excluded_rule_node_id IS DISTINCT FROM e.excluded_rule_node_id
      ) THEN RAISE EXCEPTION 'V4 applicability rule exclusions differ from candidate'; END IF;

      IF EXISTS (
        WITH RECURSIVE direct_edges(source_key,target_key) AS (
          SELECT source.rule_key::text,target.rule_key::text
            FROM ad_v4_candidate_app_expressions expression
            JOIN ad_v4_candidate_app_rules source ON source.semantic_node_id=expression.owning_rule_node_id
            JOIN ad_v4_candidate_app_rules target ON target.semantic_node_id=expression.referenced_rule_node_id
           WHERE expression.projection_id=projection.id AND expression.expression_node_type='rule_ref'
          UNION
          SELECT source.rule_key::text,target.rule_key::text
            FROM ad_v4_candidate_app_rule_exclusions exclusion
            JOIN ad_v4_candidate_app_rules source ON source.semantic_node_id=exclusion.rule_node_id
            JOIN ad_v4_candidate_app_rules target ON target.semantic_node_id=exclusion.excluded_rule_node_id
           WHERE exclusion.projection_id=projection.id
        ), walk(source_key,target_key,path,is_cycle) AS (
          SELECT source_key,target_key,ARRAY[source_key,target_key],source_key=target_key
            FROM direct_edges
          UNION ALL
          SELECT walk.source_key,direct_edges.target_key,
                 walk.path||direct_edges.target_key,
                 direct_edges.target_key=ANY(walk.path)
            FROM walk JOIN direct_edges ON direct_edges.source_key=walk.target_key
           WHERE NOT walk.is_cycle
        )
        SELECT 1 FROM walk WHERE is_cycle
      ) THEN RAISE EXCEPTION 'V4 applicability rule dependency graph is cyclic'; END IF;

      IF EXISTS (
        WITH rules AS (
          SELECT '/applicabilityRules/'||(r.ordinality-1) AS pointer,r.value
            FROM jsonb_array_elements(subtree->'applicabilityRules') WITH ORDINALITY r(value,ordinality)
        ), expected AS (
          SELECT n.id AS semantic_node_id,e.value #>> '{}' AS evidence_key,
                 (e.ordinality-1)::integer AS ordinal,'rule_clause'::text AS purpose
            FROM rules r
            JOIN ad_v4_candidate_app_semantic_nodes n
              ON n.projection_id=projection.id AND n.node_type='applicability_rule'
             AND n.source_pointer=r.pointer
            CROSS JOIN LATERAL jsonb_array_elements(r.value->'evidenceKeys') WITH ORDINALITY e(value,ordinality)
        ), actual AS (
          SELECT l.semantic_node_id,l.evidence_key,l.canonical_ordinal AS ordinal,l.purpose,
                 l.id,l.link_hash,l.candidate_binding_id
            FROM ad_v4_candidate_app_evidence_links l
            JOIN ad_v4_candidate_app_semantic_nodes n ON n.id=l.semantic_node_id
           WHERE l.projection_id=projection.id
             AND n.source_pointer ~ '^/applicabilityRules/[0-9]+($|/)'
        )
        SELECT 1 FROM expected e FULL JOIN actual a USING(semantic_node_id,evidence_key,ordinal)
         WHERE e.semantic_node_id IS NULL OR a.semantic_node_id IS NULL
            OR a.purpose IS DISTINCT FROM e.purpose
            OR a.id<>'avl_'||left(a.link_hash,32)
            OR a.link_hash<>encode(sha256(
              convert_to('paprnav:ad_extraction_v4:applicability-row:2','UTF8')||decode('00','hex')||
              convert_to(paprnav_v4_jcs(jsonb_build_object(
                'table','evidence-link','identity',jsonb_build_object(
                  'projectionId',projection.id,'nodeId',a.semantic_node_id,
                  'purpose',a.purpose,'evidenceKey',a.evidence_key))),'UTF8')),'hex')
            OR NOT EXISTS (SELECT 1 FROM ad_v4_candidate_evidence_bindings b
              WHERE b.id=a.candidate_binding_id AND b.proposal_id=proposal.id AND b.evidence_key=a.evidence_key)
      ) THEN RAISE EXCEPTION 'V4 applicability rule evidence graph differs from candidate'; END IF;

      -- Non-controlling search hints, manufacturer groups, and members are an
      -- exact typed projection. Canonical shape is checked here independently
      -- of the application validator so a direct writer cannot self-attest it.
      IF subtree->'applicabilitySearchHints' IS DISTINCT FROM (
           SELECT coalesce(jsonb_agg(value ORDER BY value->>'hintKey'),'[]'::jsonb)
             FROM jsonb_array_elements(subtree->'applicabilitySearchHints') value)
         OR (SELECT count(*) FROM jsonb_array_elements(subtree->'applicabilitySearchHints'))
            <>(SELECT count(DISTINCT value->>'hintKey') FROM jsonb_array_elements(subtree->'applicabilitySearchHints') value)
      THEN RAISE EXCEPTION 'V4 applicability search-hint set is not canonical'; END IF;

      IF EXISTS (
        WITH expected AS (
          SELECT '/applicabilitySearchHints/'||(h.ordinality-1) AS pointer,h.value
            FROM jsonb_array_elements(subtree->'applicabilitySearchHints') WITH ORDINALITY h(value,ordinality)
        ), actual AS (
          SELECT n.source_pointer AS pointer,o.*,display.source_pointer AS display_pointer
            FROM ad_v4_candidate_app_search_hints o
            JOIN ad_v4_candidate_app_semantic_nodes n ON n.id=o.semantic_node_id
            JOIN ad_v4_candidate_app_semantic_nodes display ON display.id=o.source_display_assertion_node_id
           WHERE o.projection_id=projection.id
        )
        SELECT 1 FROM expected e FULL JOIN actual a USING(pointer)
         WHERE e.pointer IS NULL OR a.pointer IS NULL
            OR a.proposal_id IS DISTINCT FROM proposal.id
            OR a.hint_key IS DISTINCT FROM e.value->>'hintKey'
            OR a.product_role IS DISTINCT FROM e.value->>'productRole'
            OR a.display_pointer IS DISTINCT FROM e.pointer||'/sourceDisplayText'
            OR a.controlling IS DISTINCT FROM false OR a.exhaustive IS DISTINCT FROM false
            OR NOT (e.value ?& ARRAY['hintKey','productRole','sourceDisplayText','manufacturerModelGroups','controlling','exhaustive','evidenceKeys'])
            OR (e.value-ARRAY['hintKey','productRole','sourceDisplayText','manufacturerModelGroups','controlling','exhaustive','evidenceKeys'])<>'{}'::jsonb
            OR jsonb_typeof(e.value->'hintKey')<>'string'
            OR e.value->>'hintKey' !~ '^[a-z][a-z0-9]*(-[a-z0-9]+)*$'
            OR char_length(e.value->>'hintKey') NOT BETWEEN 3 AND 128
            OR jsonb_typeof(e.value->'productRole')<>'string'
            OR jsonb_typeof(e.value->'sourceDisplayText')<>'object'
            OR jsonb_typeof(e.value->'manufacturerModelGroups')<>'array'
            OR jsonb_array_length(e.value->'manufacturerModelGroups')<1
            OR e.value->'manufacturerModelGroups' IS DISTINCT FROM (
                 SELECT coalesce(jsonb_agg(x ORDER BY x->>'groupKey'),'[]'::jsonb)
                   FROM jsonb_array_elements(e.value->'manufacturerModelGroups') x)
            OR e.value->'controlling' IS DISTINCT FROM 'false'::jsonb
            OR e.value->'exhaustive' IS DISTINCT FROM 'false'::jsonb
            OR jsonb_typeof(e.value->'evidenceKeys')<>'array'
            OR jsonb_array_length(e.value->'evidenceKeys')<1
            OR e.value->'evidenceKeys' IS DISTINCT FROM (
                 SELECT coalesce(jsonb_agg(x ORDER BY x #>> '{}'),'[]'::jsonb)
                   FROM jsonb_array_elements(e.value->'evidenceKeys') x)
      ) THEN RAISE EXCEPTION 'V4 applicability search-hint owners differ from candidate'; END IF;

      IF EXISTS (
        WITH hints AS (
          SELECT '/applicabilitySearchHints/'||(h.ordinality-1) AS pointer,h.value
            FROM jsonb_array_elements(subtree->'applicabilitySearchHints') WITH ORDINALITY h(value,ordinality)
        ), expected AS (
          SELECT h.pointer||'/manufacturerModelGroups/'||(g.ordinality-1) AS pointer,
                 h.pointer AS hint_pointer,g.value,(g.ordinality-1)::integer AS ordinal
            FROM hints h CROSS JOIN LATERAL jsonb_array_elements(h.value->'manufacturerModelGroups') WITH ORDINALITY g(value,ordinality)
        ), actual AS (
          SELECT n.source_pointer AS pointer,hn.source_pointer AS hint_pointer,o.*,
                 manufacturer.source_pointer AS manufacturer_pointer
            FROM ad_v4_candidate_app_search_hint_groups o
            JOIN ad_v4_candidate_app_semantic_nodes n ON n.id=o.semantic_node_id
            JOIN ad_v4_candidate_app_semantic_nodes hn ON hn.id=o.hint_node_id
            JOIN ad_v4_candidate_app_semantic_nodes manufacturer ON manufacturer.id=o.manufacturer_assertion_node_id
           WHERE o.projection_id=projection.id
        )
        SELECT 1 FROM expected e FULL JOIN actual a USING(pointer)
         WHERE e.pointer IS NULL OR a.pointer IS NULL
            OR a.proposal_id IS DISTINCT FROM proposal.id
            OR a.hint_pointer IS DISTINCT FROM e.hint_pointer
            OR a.group_key IS DISTINCT FROM e.value->>'groupKey'
            OR e.value->>'groupKey' !~ '^[a-z][a-z0-9]*(-[a-z0-9]+)*$'
            OR char_length(e.value->>'groupKey') NOT BETWEEN 3 AND 128
            OR a.manufacturer_pointer IS DISTINCT FROM e.pointer||'/manufacturer'
            OR a.manufacturer_state IS DISTINCT FROM e.value->'manufacturer'->>'state'
            OR a.manufacturer_value IS DISTINCT FROM e.value->'manufacturer'->>'value'
            OR a.manufacturer_reason IS DISTINCT FROM e.value->'manufacturer'->>'reason'
            OR a.manufacturer_temporal_scope IS DISTINCT FROM e.value->'manufacturer'->'temporalScope'->>'kind'
            OR a.association IS DISTINCT FROM e.value->>'association'
            OR a.reason IS DISTINCT FROM e.value->>'reason'
            OR a.temporal_scope IS DISTINCT FROM e.value->'temporalScope'->>'kind'
            OR a.canonical_ordinal IS DISTINCT FROM e.ordinal
            OR (SELECT count(*) FROM ad_v4_candidate_app_search_hint_members m
                 WHERE m.group_node_id=a.semantic_node_id)<>jsonb_array_length(e.value->'members')
            OR NOT (e.value ?& ARRAY['groupKey','manufacturer','association','members','evidenceKeys'])
            OR (e.value-ARRAY['groupKey','manufacturer','association','members','reason','temporalScope','evidenceKeys'])<>'{}'::jsonb
            OR jsonb_typeof(e.value->'manufacturer')<>'object'
            OR jsonb_typeof(e.value->'members')<>'array' OR jsonb_array_length(e.value->'members')<1
            OR e.value->'members' IS DISTINCT FROM (
                 SELECT coalesce(jsonb_agg(x ORDER BY x->>'memberKey'),'[]'::jsonb)
                   FROM jsonb_array_elements(e.value->'members') x)
            OR jsonb_typeof(e.value->'evidenceKeys')<>'array' OR jsonb_array_length(e.value->'evidenceKeys')<1
            OR e.value->'evidenceKeys' IS DISTINCT FROM (
                 SELECT coalesce(jsonb_agg(x ORDER BY x #>> '{}'),'[]'::jsonb)
                   FROM jsonb_array_elements(e.value->'evidenceKeys') x)
            OR CASE WHEN e.value->>'association'='unknown'
                 THEN NOT (e.value ?& ARRAY['reason','temporalScope'])
                      OR e.value->>'reason' NOT IN ('not_observed','unavailable','not_obtained','not_extracted','not_yet_reviewed','not_yet_verified','conflicting_evidence','source_ambiguous','unsupported_expression')
                      OR jsonb_typeof(e.value->'temporalScope')<>'object'
                      OR ((e.value->'temporalScope')-'kind')<>'{}'::jsonb
                      OR e.value->'temporalScope'->>'kind' NOT IN ('directive_version','publication_version','at_applicability_evaluation','at_compliance_evaluation','source_observation')
                 ELSE e.value ? 'reason' OR e.value ? 'temporalScope' END
      ) THEN RAISE EXCEPTION 'V4 applicability search-hint group graph differs from candidate'; END IF;

      IF EXISTS (
        WITH hints AS (
          SELECT '/applicabilitySearchHints/'||(h.ordinality-1) AS pointer,h.value
            FROM jsonb_array_elements(subtree->'applicabilitySearchHints') WITH ORDINALITY h(value,ordinality)
        ), groups AS (
          SELECT h.pointer||'/manufacturerModelGroups/'||(g.ordinality-1) AS pointer,g.value
            FROM hints h CROSS JOIN LATERAL jsonb_array_elements(h.value->'manufacturerModelGroups') WITH ORDINALITY g(value,ordinality)
        ), expected AS (
          SELECT g.pointer||'/members/'||(m.ordinality-1) AS pointer,g.pointer AS group_pointer,
                 m.value,(m.ordinality-1)::integer AS ordinal
            FROM groups g CROSS JOIN LATERAL jsonb_array_elements(g.value->'members') WITH ORDINALITY m(value,ordinality)
        ), actual AS (
          SELECT n.source_pointer AS pointer,gn.source_pointer AS group_pointer,o.*,
                 manufacturer.source_pointer AS manufacturer_pointer
            FROM ad_v4_candidate_app_search_hint_members o
            JOIN ad_v4_candidate_app_semantic_nodes n ON n.id=o.semantic_node_id
            JOIN ad_v4_candidate_app_semantic_nodes gn ON gn.id=o.group_node_id
            JOIN ad_v4_candidate_app_semantic_nodes manufacturer ON manufacturer.id=o.manufacturer_assertion_node_id
           WHERE o.projection_id=projection.id
        )
        SELECT 1 FROM expected e FULL JOIN actual a USING(pointer)
         WHERE e.pointer IS NULL OR a.pointer IS NULL
            OR a.proposal_id IS DISTINCT FROM proposal.id
            OR a.group_pointer IS DISTINCT FROM e.group_pointer
            OR a.member_key IS DISTINCT FROM e.value->>'memberKey'
            OR e.value->>'memberKey' !~ '^[a-z][a-z0-9]*(-[a-z0-9]+)*$'
            OR char_length(e.value->>'memberKey') NOT BETWEEN 3 AND 128
            OR a.designation_kind IS DISTINCT FROM e.value->>'designationKind'
            OR a.source_designation IS DISTINCT FROM e.value->>'sourceDesignation'
            OR a.expression_text IS DISTINCT FROM e.value->>'expressionText'
            OR a.manufacturer_pointer IS DISTINCT FROM e.pointer||'/manufacturer'
            OR a.manufacturer_state IS DISTINCT FROM e.value->'manufacturer'->>'state'
            OR a.manufacturer_value IS DISTINCT FROM e.value->'manufacturer'->>'value'
            OR a.manufacturer_reason IS DISTINCT FROM e.value->'manufacturer'->>'reason'
            OR a.manufacturer_temporal_scope IS DISTINCT FROM e.value->'manufacturer'->'temporalScope'->>'kind'
            OR a.evaluation_state IS DISTINCT FROM CASE WHEN e.value->>'designationKind'='series_expression' THEN 'unevaluated' ELSE NULL END
            OR a.evaluation_reason IS DISTINCT FROM CASE WHEN e.value->>'designationKind'='series_expression' THEN 'unsupported_expression' ELSE NULL END
            OR a.canonical_ordinal IS DISTINCT FROM e.ordinal
            OR a.designation_identity_mapping_node_id IS DISTINCT FROM (
                 SELECT m.semantic_node_id FROM ad_v4_candidate_app_identity_mappings m
                 JOIN ad_v4_candidate_app_semantic_nodes occurrence ON occurrence.id=m.source_occurrence_node_id
                  WHERE m.projection_id=projection.id AND occurrence.source_pointer=e.pointer)
            OR CASE e.value->>'designationKind'
                 WHEN 'model' THEN NOT (e.value ?& ARRAY['memberKey','designationKind','sourceDesignation','manufacturer','evidenceKeys'])
                      OR (e.value-ARRAY['memberKey','designationKind','sourceDesignation','manufacturer','evidenceKeys'])<>'{}'::jsonb
                      OR jsonb_typeof(e.value->'sourceDesignation')<>'string'
                      OR char_length(e.value->>'sourceDesignation') NOT BETWEEN 1 AND 512
                 WHEN 'series_expression' THEN NOT (e.value ?& ARRAY['memberKey','designationKind','expressionText','evaluationState','reason','manufacturer','evidenceKeys'])
                      OR (e.value-ARRAY['memberKey','designationKind','expressionText','evaluationState','reason','manufacturer','evidenceKeys'])<>'{}'::jsonb
                      OR jsonb_typeof(e.value->'expressionText')<>'string'
                      OR char_length(e.value->>'expressionText') NOT BETWEEN 1 AND 512
                      OR e.value->>'evaluationState'<>'unknown' OR e.value->>'reason'<>'unsupported_expression'
                 ELSE true END
            OR jsonb_typeof(e.value->'manufacturer')<>'object'
            OR jsonb_typeof(e.value->'evidenceKeys')<>'array' OR jsonb_array_length(e.value->'evidenceKeys')<1
            OR e.value->'evidenceKeys' IS DISTINCT FROM (
                 SELECT coalesce(jsonb_agg(x ORDER BY x #>> '{}'),'[]'::jsonb)
                   FROM jsonb_array_elements(e.value->'evidenceKeys') x)
      ) THEN RAISE EXCEPTION 'V4 applicability search-hint member graph differs from candidate'; END IF;

      IF EXISTS (
        WITH hints AS (
          SELECT '/applicabilitySearchHints/'||(h.ordinality-1) AS pointer,h.value
            FROM jsonb_array_elements(subtree->'applicabilitySearchHints') WITH ORDINALITY h(value,ordinality)
        ), groups AS (
          SELECT h.pointer||'/manufacturerModelGroups/'||(g.ordinality-1) AS pointer,g.value
            FROM hints h CROSS JOIN LATERAL jsonb_array_elements(h.value->'manufacturerModelGroups') WITH ORDINALITY g(value,ordinality)
        ), members AS (
          SELECT g.pointer||'/members/'||(m.ordinality-1) AS pointer,m.value
            FROM groups g CROSS JOIN LATERAL jsonb_array_elements(g.value->'members') WITH ORDINALITY m(value,ordinality)
        ), expected AS (
          SELECT h.pointer||'/sourceDisplayText' AS pointer,h.pointer AS parent_pointer,
                 'source_display_text'::text AS field_code,h.value->'sourceDisplayText' AS value
            FROM hints h
          UNION ALL
          SELECT g.pointer||'/manufacturer',g.pointer,'manufacturer',g.value->'manufacturer' FROM groups g
          UNION ALL
          SELECT m.pointer||'/manufacturer',m.pointer,'manufacturer',m.value->'manufacturer' FROM members m
        ), actual AS (
          SELECT n.source_pointer AS pointer,parent.source_pointer AS parent_pointer,o.*
            FROM ad_v4_candidate_app_value_assertions o
            JOIN ad_v4_candidate_app_semantic_nodes n ON n.id=o.semantic_node_id
            JOIN ad_v4_candidate_app_semantic_nodes parent ON parent.id=o.parent_semantic_node_id
           WHERE o.projection_id=projection.id
             AND n.source_pointer ~ '^/applicabilitySearchHints/[0-9]+/'
        )
        SELECT 1 FROM expected e FULL JOIN actual a USING(pointer)
         WHERE e.pointer IS NULL OR a.pointer IS NULL
            OR a.proposal_id IS DISTINCT FROM proposal.id
            OR a.parent_pointer IS DISTINCT FROM e.parent_pointer
            OR a.field_code IS DISTINCT FROM e.field_code OR a.value_type<>'text'
            OR a.state IS DISTINCT FROM e.value->>'state'
            OR a.text_value IS DISTINCT FROM e.value->>'value'
            OR a.reason IS DISTINCT FROM e.value->>'reason'
            OR a.temporal_scope IS DISTINCT FROM e.value->'temporalScope'->>'kind'
            OR jsonb_typeof(e.value)<>'object'
            OR NOT (e.value ?& ARRAY['state','evidenceKeys'])
            OR (e.value-ARRAY['state','value','reason','temporalScope','evidenceKeys'])<>'{}'::jsonb
            OR jsonb_typeof(e.value->'evidenceKeys')<>'array' OR jsonb_array_length(e.value->'evidenceKeys')<1
            OR e.value->'evidenceKeys' IS DISTINCT FROM (
                 SELECT coalesce(jsonb_agg(x ORDER BY x #>> '{}'),'[]'::jsonb)
                   FROM jsonb_array_elements(e.value->'evidenceKeys') x)
            OR CASE e.value->>'state'
                 WHEN 'known' THEN NOT (e.value ? 'value') OR e.value ? 'reason' OR e.value ? 'temporalScope'
                      OR jsonb_typeof(e.value->'value')<>'string'
                      OR char_length(e.value->>'value') NOT BETWEEN 1 AND 512
                 WHEN 'unknown' THEN e.value ? 'value' OR NOT (e.value ?& ARRAY['reason','temporalScope'])
                      OR e.value->>'reason' NOT IN ('not_observed','unavailable','not_obtained','not_extracted','not_yet_reviewed','not_yet_verified','conflicting_evidence','source_ambiguous','unsupported_expression')
                      OR jsonb_typeof(e.value->'temporalScope')<>'object'
                      OR ((e.value->'temporalScope')-'kind')<>'{}'::jsonb
                      OR e.value->'temporalScope'->>'kind' NOT IN ('directive_version','publication_version','at_applicability_evaluation','at_compliance_evaluation','source_observation')
                 WHEN 'not_applicable' THEN e.value ? 'value' OR NOT (e.value ?& ARRAY['reason','temporalScope'])
                      OR jsonb_typeof(e.value->'reason')<>'string'
                      OR char_length(e.value->>'reason') NOT BETWEEN 1 AND 512
                      OR jsonb_typeof(e.value->'temporalScope')<>'object'
                      OR ((e.value->'temporalScope')-'kind')<>'{}'::jsonb
                      OR e.value->'temporalScope'->>'kind' NOT IN ('directive_version','publication_version','at_applicability_evaluation','at_compliance_evaluation','source_observation')
                 ELSE true END
      ) THEN RAISE EXCEPTION 'V4 applicability search-hint assertion graph differs from candidate'; END IF;

      IF EXISTS (
        WITH hints AS (
          SELECT '/applicabilitySearchHints/'||(h.ordinality-1) AS pointer,h.value
            FROM jsonb_array_elements(subtree->'applicabilitySearchHints') WITH ORDINALITY h(value,ordinality)
        ), groups AS (
          SELECT h.pointer||'/manufacturerModelGroups/'||(g.ordinality-1) AS pointer,g.value
            FROM hints h CROSS JOIN LATERAL jsonb_array_elements(h.value->'manufacturerModelGroups') WITH ORDINALITY g(value,ordinality)
        ), members AS (
          SELECT g.pointer||'/members/'||(m.ordinality-1) AS pointer,g.pointer AS context_pointer,m.value
            FROM groups g CROSS JOIN LATERAL jsonb_array_elements(g.value->'members') WITH ORDINALITY m(value,ordinality)
        ), expected AS (
          SELECT g.pointer||'/manufacturer' AS occurrence_pointer,g.pointer AS context_pointer,
                 'manufacturer'::text AS identity_kind,g.value->'manufacturer'->>'value' AS source_value
            FROM groups g WHERE g.value->'manufacturer'->>'state'='known'
          UNION ALL
          SELECT m.pointer,m.context_pointer,
                 CASE WHEN m.value->>'designationKind'='model' THEN 'model' ELSE 'series' END,
                 CASE WHEN m.value->>'designationKind'='model' THEN m.value->>'sourceDesignation' ELSE m.value->>'expressionText' END
            FROM members m
          UNION ALL
          SELECT m.pointer||'/manufacturer',m.context_pointer,'manufacturer',m.value->'manufacturer'->>'value'
            FROM members m WHERE m.value->'manufacturer'->>'state'='known'
        ), actual AS (
          SELECT occurrence.source_pointer AS occurrence_pointer,context.source_pointer AS context_pointer,m.*
            FROM ad_v4_candidate_app_identity_mappings m
            JOIN ad_v4_candidate_app_semantic_nodes occurrence ON occurrence.id=m.source_occurrence_node_id
            JOIN ad_v4_candidate_app_semantic_nodes context ON context.id=m.evidence_parent_node_id
           WHERE m.projection_id=projection.id
             AND occurrence.source_pointer ~ '^/applicabilitySearchHints/[0-9]+/'
        )
        SELECT 1 FROM expected e FULL JOIN actual a USING(occurrence_pointer)
         WHERE e.occurrence_pointer IS NULL OR a.occurrence_pointer IS NULL
            OR a.proposal_id IS DISTINCT FROM proposal.id
            OR a.context_pointer IS DISTINCT FROM e.context_pointer
            OR a.identity_kind IS DISTINCT FROM e.identity_kind
            OR a.source_value IS DISTINCT FROM e.source_value
            OR a.normalization_origin<>'source_only' OR a.normalized_state<>'unknown'
            OR a.normalized_value IS NOT NULL OR a.reason<>'not_extracted'
            OR a.temporal_scope<>'directive_version'
            OR a.normalization_namespace IS NOT NULL OR a.normalization_version IS NOT NULL
            OR a.review_state<>'unreviewed_candidate'
      ) THEN RAISE EXCEPTION 'V4 applicability search-hint identity-mapping graph differs from candidate'; END IF;

      IF EXISTS (
        WITH hints AS (
          SELECT '/applicabilitySearchHints/'||(h.ordinality-1) AS pointer,h.value
            FROM jsonb_array_elements(subtree->'applicabilitySearchHints') WITH ORDINALITY h(value,ordinality)
        ), groups AS (
          SELECT h.pointer||'/manufacturerModelGroups/'||(g.ordinality-1) AS pointer,g.value
            FROM hints h CROSS JOIN LATERAL jsonb_array_elements(h.value->'manufacturerModelGroups') WITH ORDINALITY g(value,ordinality)
        ), members AS (
          SELECT g.pointer||'/members/'||(m.ordinality-1) AS pointer,m.value
            FROM groups g CROSS JOIN LATERAL jsonb_array_elements(g.value->'members') WITH ORDINALITY m(value,ordinality)
        ), expected_nodes AS (
          SELECT pointer,value->'evidenceKeys' AS keys,'search_hint_clause'::text AS purpose FROM hints
          UNION ALL SELECT pointer||'/sourceDisplayText',value->'sourceDisplayText'->'evidenceKeys','search_hint_clause' FROM hints
          UNION ALL SELECT pointer,value->'evidenceKeys','search_hint_clause' FROM groups
          UNION ALL SELECT pointer||'/manufacturer',value->'manufacturer'->'evidenceKeys','identity_support' FROM groups
          UNION ALL SELECT pointer,value->'evidenceKeys','search_hint_clause' FROM members
          UNION ALL SELECT pointer||'/manufacturer',value->'manufacturer'->'evidenceKeys','identity_support' FROM members
        ), expected AS (
          SELECT n.id AS semantic_node_id,e.value #>> '{}' AS evidence_key,
                 (e.ordinality-1)::integer AS ordinal,x.purpose
            FROM expected_nodes x
            JOIN ad_v4_candidate_app_semantic_nodes n
              ON n.projection_id=projection.id AND n.source_pointer=x.pointer AND n.node_type<>'identity_mapping'
            CROSS JOIN LATERAL jsonb_array_elements(x.keys) WITH ORDINALITY e(value,ordinality)
        ), actual AS (
          SELECT l.semantic_node_id,l.evidence_key,l.canonical_ordinal AS ordinal,l.purpose,
                 l.id,l.link_hash,l.candidate_binding_id
            FROM ad_v4_candidate_app_evidence_links l
            JOIN ad_v4_candidate_app_semantic_nodes n ON n.id=l.semantic_node_id
           WHERE l.projection_id=projection.id
             AND n.source_pointer ~ '^/applicabilitySearchHints/[0-9]+($|/)'
             AND n.node_type<>'identity_mapping'
        )
        SELECT 1 FROM expected e FULL JOIN actual a USING(semantic_node_id,evidence_key,ordinal)
         WHERE e.semantic_node_id IS NULL OR a.semantic_node_id IS NULL
            OR a.purpose IS DISTINCT FROM e.purpose
            OR a.id<>'avl_'||left(a.link_hash,32)
            OR a.link_hash<>encode(sha256(
              convert_to('paprnav:ad_extraction_v4:applicability-row:2','UTF8')||decode('00','hex')||
              convert_to(paprnav_v4_jcs(jsonb_build_object(
                'table','evidence-link','identity',jsonb_build_object(
                  'projectionId',projection.id,'nodeId',a.semantic_node_id,
                  'purpose',a.purpose,'evidenceKey',a.evidence_key))),'UTF8')),'hex')
            OR NOT EXISTS (SELECT 1 FROM ad_v4_candidate_evidence_bindings b
              WHERE b.id=a.candidate_binding_id AND b.proposal_id=proposal.id AND b.evidence_key=a.evidence_key)
      ) THEN RAISE EXCEPTION 'V4 applicability search-hint evidence graph differs from candidate'; END IF;

      IF EXISTS (
        SELECT 1 FROM ad_v4_candidate_app_evidence_links l
        JOIN ad_v4_candidate_app_semantic_nodes n ON n.id=l.semantic_node_id
         WHERE l.projection_id=projection.id AND n.node_type='identity_mapping'
      ) THEN RAISE EXCEPTION 'V4 identity mapping must not own evidence'; END IF;

      IF EXISTS (
        SELECT 1 FROM ad_v4_candidate_app_semantic_nodes n
        LEFT JOIN ad_v4_candidate_app_change_dependencies incoming
          ON incoming.semantic_node_id=n.id AND incoming.projection_id=n.projection_id
        LEFT JOIN ad_v4_candidate_app_change_dependencies source
          ON source.id=incoming.source_dependency_id
        WHERE n.projection_id=projection.id AND n.source_pointer LIKE '/incomingSupersessionSignals/%'
          AND (incoming.id IS NULL OR source.id IS NULL
            OR n.node_type<>'change_dependency'
            OR n.node_key<>'incoming:'||source.id
            OR n.source_pointer<>'/incomingSupersessionSignals/'||source.id
            OR n.parent_node_id IS NOT NULL OR n.canonical_ordinal<>0
            OR incoming.dependency_kind<>'incoming_supersession_signal'
            OR incoming.resolution_state<>'resolved_candidate' OR incoming.unresolved_reason IS NOT NULL
            OR incoming.target_projection_id<>projection.id
            OR source.target_projection_id<>projection.id
            OR source.resolution_state<>'resolved_candidate'
            OR incoming.predecessor_ad_number<>source.predecessor_ad_number
            OR incoming.successor_ad_number<>source.successor_ad_number
            OR n.canonical_node_hash<>encode(sha256(convert_to(paprnav_v4_jcs(jsonb_build_object(
                 'sourceDependencyId',source.id,'targetProjectionId',projection.id)),'UTF8')),'hex')
            OR n.identity_hash<>encode(sha256(
                 convert_to('paprnav:ad_extraction_v4:applicability-row:2','UTF8')||decode('00','hex')||
                 convert_to(paprnav_v4_jcs(jsonb_build_object(
                   'table','semantic-node','identity',jsonb_build_object(
                     'projectionId',projection.id,'nodeType','change_dependency',
                     'nodeKey','incoming:'||source.id,
                     'pointer','/incomingSupersessionSignals/'||source.id))),'UTF8')),'hex'))
      ) THEN RAISE EXCEPTION 'V4 incoming supersession dependency differs'; END IF;

      IF (SELECT count(*) FROM ad_v4_candidate_app_change_dependencies d
           WHERE d.projection_id=projection.id
             AND d.dependency_kind IN ('outgoing_supersedes','outgoing_partially_supersedes'))
           <>jsonb_array_length(proposal.parsed_json::jsonb->'supersessionRelations')
      THEN RAISE EXCEPTION 'V4 outgoing supersession dependency count differs'; END IF;

      FOR node IN
        SELECT * FROM ad_v4_candidate_app_semantic_nodes
         WHERE projection_id=projection.id AND source_pointer LIKE '/supersessionRelations/%'
         ORDER BY canonical_ordinal
      LOOP
        relation:=paprnav_v4_pointer_value(proposal.parsed_json::jsonb,node.source_pointer);
        SELECT count(*),min(candidate_projection.id) INTO matching_targets,expected_target_id
          FROM ad_v4_candidate_app_projections candidate_projection
          JOIN ad_v4_candidate_proposals candidate_proposal
            ON candidate_proposal.id=candidate_projection.proposal_id
         WHERE candidate_projection.id<>projection.id
           AND candidate_proposal.parsed_json::jsonb->'directiveIdentity'->'adNumber'->>'state'='known'
           AND candidate_proposal.parsed_json::jsonb->'directiveIdentity'->'adNumber'->>'value'=relation->>'predecessorAdNumber';
        IF NOT EXISTS (
          SELECT 1 FROM ad_v4_candidate_app_change_dependencies d
           WHERE d.projection_id=projection.id AND d.proposal_id=proposal.id
             AND d.semantic_node_id=node.id
             AND d.dependency_key=(relation->>'relationType')||':'||(relation->>'predecessorAdNumber')
             AND d.dependency_kind=CASE WHEN relation->>'relationType'='supersedes'
                  THEN 'outgoing_supersedes' ELSE 'outgoing_partially_supersedes' END
             AND d.predecessor_ad_number=relation->>'predecessorAdNumber'
             AND d.successor_ad_number=relation->>'successorAdNumber'
             AND d.source_dependency_id IS NULL
             AND d.dependency_hash=encode(sha256(
               convert_to('paprnav:ad_extraction_v4:applicability-row:2','UTF8')||decode('00','hex')||
               convert_to(paprnav_v4_jcs(jsonb_build_object(
                 'table','change-dependency','identity',jsonb_build_object(
                   'projectionId',projection.id,
                   'dependencyKey',(relation->>'relationType')||':'||(relation->>'predecessorAdNumber'),
                   'predecessorAdNumber',relation->>'predecessorAdNumber',
                   'successorAdNumber',relation->>'successorAdNumber'))),'UTF8')),'hex')
             AND CASE
               WHEN proposal.parsed_json::jsonb->'directiveIdentity'->'adNumber'->>'state'<>'known'
                 THEN d.resolution_state='unresolved' AND d.unresolved_reason='successor_identity_unknown' AND d.target_projection_id IS NULL
               WHEN relation->>'successorAdNumber'<>proposal.parsed_json::jsonb->'directiveIdentity'->'adNumber'->>'value'
                 THEN d.resolution_state='unresolved' AND d.unresolved_reason='successor_not_this_proposal' AND d.target_projection_id IS NULL
               WHEN matching_targets=1
                 THEN d.resolution_state='resolved_candidate' AND d.unresolved_reason IS NULL AND d.target_projection_id=expected_target_id
               WHEN matching_targets>1
                 THEN d.resolution_state='ambiguous' AND d.unresolved_reason='multiple_predecessor_candidates' AND d.target_projection_id IS NULL
               ELSE d.resolution_state='unresolved' AND d.unresolved_reason='target_candidate_not_resolved' AND d.target_projection_id IS NULL
             END
        ) THEN RAISE EXCEPTION 'V4 outgoing supersession dependency differs'; END IF;
      END LOOP;

      IF EXISTS (
        SELECT 1 FROM ad_v4_candidate_app_change_dependencies source
         WHERE source.target_projection_id=projection.id
           AND source.dependency_kind IN ('outgoing_supersedes','outgoing_partially_supersedes')
           AND source.resolution_state='resolved_candidate'
           AND NOT EXISTS (
             SELECT 1 FROM ad_v4_candidate_app_change_dependencies incoming
              JOIN ad_v4_candidate_app_semantic_nodes n ON n.id=incoming.semantic_node_id
              WHERE incoming.source_dependency_id=source.id
                AND incoming.projection_id=projection.id
                AND incoming.proposal_id=projection.proposal_id
                AND incoming.dependency_key='incoming:'||source.id
                AND incoming.dependency_kind='incoming_supersession_signal'
                AND incoming.predecessor_ad_number=source.predecessor_ad_number
                AND incoming.successor_ad_number=source.successor_ad_number
                AND incoming.resolution_state='resolved_candidate'
                AND incoming.unresolved_reason IS NULL
                AND incoming.target_projection_id=projection.id
                AND incoming.dependency_hash=encode(sha256(
                  convert_to('paprnav:ad_extraction_v4:applicability-row:2','UTF8')||decode('00','hex')||
                  convert_to(paprnav_v4_jcs(jsonb_build_object(
                    'table','incoming-change-dependency','identity',jsonb_build_object(
                      'projectionId',projection.id,'sourceDependencyId',source.id))),'UTF8')),'hex')
                AND n.projection_id=projection.id AND n.proposal_id=projection.proposal_id
                AND n.node_type='change_dependency' AND n.node_key='incoming:'||source.id
           )
      ) THEN RAISE EXCEPTION 'V4 resolved supersession is missing its target-local cause'; END IF;

      IF proposal.parsed_json::jsonb->'directiveIdentity'->'adNumber'->>'state'='known'
         AND EXISTS (
           SELECT 1 FROM ad_v4_candidate_app_change_dependencies source
            WHERE source.resolution_state='resolved_candidate'
              AND source.dependency_kind IN ('outgoing_supersedes','outgoing_partially_supersedes')
              AND source.predecessor_ad_number=proposal.parsed_json::jsonb->'directiveIdentity'->'adNumber'->>'value'
              AND (SELECT count(*)
                     FROM ad_v4_candidate_app_projections candidate_projection
                     JOIN ad_v4_candidate_proposals candidate_proposal
                       ON candidate_proposal.id=candidate_projection.proposal_id
                    WHERE candidate_proposal.parsed_json::jsonb->'directiveIdentity'->'adNumber'->>'state'='known'
                      AND candidate_proposal.parsed_json::jsonb->'directiveIdentity'->'adNumber'->>'value'=source.predecessor_ad_number)<>1
         )
      THEN RAISE EXCEPTION 'V4 resolved supersession predecessor is no longer unique'; END IF;

      IF (SELECT count(*) FROM ad_v4_candidate_corrections WHERE proposal_id=proposal.id)
           <>jsonb_array_length(proposal.parsed_json::jsonb->'authoritativeCorrections')
      THEN RAISE EXCEPTION 'V4 correction foundation count differs'; END IF;

      FOR correction IN
        SELECT * FROM ad_v4_candidate_corrections WHERE proposal_id=proposal.id ORDER BY canonical_ordinal
      LOOP
        expected_correction:=proposal.parsed_json::jsonb->'authoritativeCorrections'->correction.canonical_ordinal;
        SELECT coalesce(jsonb_agg(jsonb_build_object('namespace',namespace,'key',semantic_key) ORDER BY canonical_ordinal),'[]'::jsonb)
          INTO actual_refs FROM ad_v4_candidate_correction_refs WHERE correction_id=correction.id;
        SELECT coalesce(jsonb_agg(evidence_key ORDER BY canonical_ordinal),'[]'::jsonb)
          INTO actual_evidence FROM ad_v4_candidate_correction_evidence_links WHERE correction_id=correction.id;
        SELECT value INTO original_document FROM jsonb_array_elements(proposal.parsed_json::jsonb->'officialDocuments')
          WHERE value->>'officialDocumentKey'=correction.original_document_ref_key;
        SELECT value INTO correcting_document FROM jsonb_array_elements(proposal.parsed_json::jsonb->'officialDocuments')
          WHERE value->>'officialDocumentKey'=correction.correcting_document_ref_key;
        expected_hash:=encode(sha256(convert_to(paprnav_v4_jcs(expected_correction),'UTF8')),'hex');
        IF expected_correction IS NULL OR original_document IS NULL OR correcting_document IS NULL
           OR correction.correction_key<>expected_correction->>'correctionKey'
           OR correction.correction_type<>expected_correction->>'correctionType'
           OR correction.original_document_ref_key<>expected_correction->>'originalDocumentRefKey'
           OR correction.correcting_document_ref_key<>expected_correction->>'correctingDocumentRefKey'
           OR correction.canonical_hash<>expected_hash
           OR correction.foundation_version<>'paprnav-ad-v4-correction-foundation-1'
           OR correction.generation<>1
           OR correction.expected_ref_count<>jsonb_array_length(expected_correction->'changedSemanticRefs')
           OR correction.expected_evidence_count<>jsonb_array_length(expected_correction->'evidenceKeys')
           OR actual_refs IS DISTINCT FROM expected_correction->'changedSemanticRefs'
           OR actual_evidence IS DISTINCT FROM expected_correction->'evidenceKeys'
           OR EXISTS (
             SELECT 1 FROM ad_v4_candidate_correction_refs r
              WHERE r.correction_id=correction.id
              HAVING count(*)>0 AND (min(r.canonical_ordinal)<>0 OR max(r.canonical_ordinal)<>count(*)-1))
           OR EXISTS (
             SELECT 1 FROM ad_v4_candidate_correction_evidence_links e
              WHERE e.correction_id=correction.id
              HAVING count(*)>0 AND (min(e.canonical_ordinal)<>0 OR max(e.canonical_ordinal)<>count(*)-1))
           OR correction.original_document_identity_hash<>encode(sha256(
                convert_to('paprnav:ad_extraction_v4:applicability-row:2','UTF8')||decode('00','hex')||
                convert_to(paprnav_v4_jcs(jsonb_build_object('officialDocument',original_document)),'UTF8')),'hex')
           OR correction.correcting_document_identity_hash<>encode(sha256(
                convert_to('paprnav:ad_extraction_v4:applicability-row:2','UTF8')||decode('00','hex')||
                convert_to(paprnav_v4_jcs(jsonb_build_object('officialDocument',correcting_document)),'UTF8')),'hex')
           OR EXISTS (
             SELECT 1 FROM ad_v4_candidate_correction_refs r
              WHERE r.correction_id=correction.id AND (
                r.reference_hash<>encode(sha256(
                  convert_to('paprnav:ad_extraction_v4:applicability-row:2','UTF8')||decode('00','hex')||
                  convert_to(paprnav_v4_jcs(jsonb_build_object(
                    'table','correction-ref','identity',jsonb_build_object(
                      'correctionId',correction.id,'namespace',r.namespace,'key',r.semantic_key))),'UTF8')),'hex')
                OR r.owner_slice<>CASE
                  WHEN r.namespace IN ('productScopes','conditionDefinitions','applicabilityRules') THEN 'slice_3a'
                  WHEN r.namespace IN ('directiveIdentity','supersessionRelations') THEN 'foundation'
                  ELSE 'slice_3b' END
                OR (r.owner_slice='slice_3a' AND (SELECT count(*) FROM ad_v4_candidate_correction_semantic_bindings b WHERE b.correction_ref_id=r.id)<>1)
                OR (r.owner_slice<>'slice_3a' AND EXISTS (SELECT 1 FROM ad_v4_candidate_correction_semantic_bindings b WHERE b.correction_ref_id=r.id))
                OR EXISTS (
                  SELECT 1 FROM ad_v4_candidate_correction_semantic_bindings b
                  JOIN ad_v4_candidate_app_semantic_nodes n ON n.id=b.semantic_node_id
                  WHERE b.correction_ref_id=r.id AND (
                    b.proposal_id<>proposal.id OR b.projection_id<>projection.id
                    OR b.binding_slice<>'slice_3a' OR b.generation<>1
                    OR n.projection_id<>projection.id
                    OR n.node_type<>CASE r.namespace WHEN 'productScopes' THEN 'product_scope' WHEN 'conditionDefinitions' THEN 'condition' ELSE 'applicability_rule' END
                    OR n.node_key<>r.semantic_key
                    OR b.binding_hash<>encode(sha256(
                      convert_to('paprnav:ad_extraction_v4:applicability-row:2','UTF8')||decode('00','hex')||
                      convert_to(paprnav_v4_jcs(jsonb_build_object(
                        'table','correction-binding','identity',jsonb_build_object('refId',r.id,'semanticId',n.id))),'UTF8')),'hex')))))
           OR EXISTS (
             SELECT 1 FROM ad_v4_candidate_correction_evidence_links e
             WHERE e.correction_id=correction.id AND (
               e.link_hash<>encode(sha256(
                 convert_to('paprnav:ad_extraction_v4:applicability-row:2','UTF8')||decode('00','hex')||
                 convert_to(paprnav_v4_jcs(jsonb_build_object(
                   'table','correction-evidence','identity',jsonb_build_object(
                     'correctionId',correction.id,'evidenceKey',e.evidence_key))),'UTF8')),'hex')))
        THEN RAISE EXCEPTION 'V4 correction foundation is incomplete or differs from candidate'; END IF;
      END LOOP;
      IF paprnav_v4_candidate_app_typed_subtree(projection.id) IS DISTINCT FROM subtree
      THEN RAISE EXCEPTION 'V4 typed-owner reconstruction differs from candidate subtree'; END IF;
    END; $$ LANGUAGE plpgsql
    """)
    op.execute(r"""
    CREATE FUNCTION paprnav_v4_candidate_app_mark_dirty() RETURNS trigger AS $$
    DECLARE target_projection_id text; target_projection_ids text[]:=ARRAY[]::text[];
    BEGIN
      IF to_regclass('pg_temp.paprnav_v4_app_validation_state') IS NULL THEN
        CREATE TEMP TABLE paprnav_v4_app_validation_state(
          projection_id text PRIMARY KEY,
          generation bigint NOT NULL,
          validated_generation bigint NOT NULL
        ) ON COMMIT DROP;
      END IF;
      IF TG_OP<>'INSERT' THEN
        IF TG_TABLE_NAME='ad_v4_candidate_app_projections' THEN
          target_projection_id:=to_jsonb(OLD)->>'id';
        ELSE
          target_projection_id:=to_jsonb(OLD)->>'projection_id';
          IF target_projection_id IS NULL AND to_jsonb(OLD)->>'proposal_id' IS NOT NULL THEN
            SELECT id INTO target_projection_id FROM ad_v4_candidate_app_projections
             WHERE proposal_id=to_jsonb(OLD)->>'proposal_id'
               AND materializer_version='paprnav-ad-v4-app-materializer-2';
          END IF;
        END IF;
        IF target_projection_id IS NOT NULL THEN
          target_projection_ids:=array_append(target_projection_ids,target_projection_id);
        END IF;
      END IF;
      IF TG_OP<>'DELETE' THEN
        target_projection_id:=NULL;
        IF TG_TABLE_NAME='ad_v4_candidate_app_projections' THEN
          target_projection_id:=to_jsonb(NEW)->>'id';
        ELSE
          target_projection_id:=to_jsonb(NEW)->>'projection_id';
          IF target_projection_id IS NULL AND to_jsonb(NEW)->>'proposal_id' IS NOT NULL THEN
            SELECT id INTO target_projection_id FROM ad_v4_candidate_app_projections
             WHERE proposal_id=to_jsonb(NEW)->>'proposal_id'
               AND materializer_version='paprnav-ad-v4-app-materializer-2';
          END IF;
        END IF;
        IF target_projection_id IS NOT NULL THEN
          target_projection_ids:=array_append(target_projection_ids,target_projection_id);
        END IF;
      END IF;
      FOREACH target_projection_id IN ARRAY target_projection_ids LOOP
        INSERT INTO paprnav_v4_app_validation_state(projection_id,generation,validated_generation)
          VALUES(target_projection_id,1,0)
        ON CONFLICT(projection_id) DO UPDATE
          SET generation=paprnav_v4_app_validation_state.generation+1;
      END LOOP;
      IF TG_OP='DELETE' THEN RETURN OLD; ELSE RETURN NEW; END IF;
    END; $$ LANGUAGE plpgsql
    """)
    for table in APP_TABLES[1:]:
        op.execute(
            f"CREATE TRIGGER trg_{table}_mark_dirty "
            f"BEFORE INSERT OR UPDATE OR DELETE ON {table} FOR EACH ROW "
            "EXECUTE FUNCTION paprnav_v4_candidate_app_mark_dirty()"
        )
    op.execute(r"""
    CREATE FUNCTION paprnav_v4_candidate_app_complete_trigger() RETURNS trigger AS $$
    DECLARE target_projection_id text; target_projection_ids text[]:=ARRAY[]::text[];
      dirty_generation bigint; clean_generation bigint;
    BEGIN
      IF TG_OP<>'INSERT' THEN
        IF TG_TABLE_NAME='ad_v4_candidate_app_projections' THEN
          target_projection_id:=to_jsonb(OLD)->>'id';
        ELSE
          target_projection_id:=to_jsonb(OLD)->>'projection_id';
          IF target_projection_id IS NULL AND to_jsonb(OLD)->>'proposal_id' IS NOT NULL THEN
            SELECT id INTO target_projection_id FROM ad_v4_candidate_app_projections
             WHERE proposal_id=to_jsonb(OLD)->>'proposal_id'
               AND materializer_version='paprnav-ad-v4-app-materializer-2';
          END IF;
        END IF;
        IF target_projection_id IS NOT NULL THEN
          target_projection_ids:=array_append(target_projection_ids,target_projection_id);
        END IF;
      END IF;
      IF TG_OP<>'DELETE' THEN
        target_projection_id:=NULL;
        IF TG_TABLE_NAME='ad_v4_candidate_app_projections' THEN
          target_projection_id:=to_jsonb(NEW)->>'id';
        ELSE
          target_projection_id:=to_jsonb(NEW)->>'projection_id';
          IF target_projection_id IS NULL AND to_jsonb(NEW)->>'proposal_id' IS NOT NULL THEN
            SELECT id INTO target_projection_id FROM ad_v4_candidate_app_projections
             WHERE proposal_id=to_jsonb(NEW)->>'proposal_id'
               AND materializer_version='paprnav-ad-v4-app-materializer-2';
          END IF;
        END IF;
        IF target_projection_id IS NOT NULL THEN
          target_projection_ids:=array_append(target_projection_ids,target_projection_id);
        END IF;
      END IF;
      IF cardinality(target_projection_ids)=0 AND TG_TABLE_NAME LIKE 'ad_v4_candidate_correction%' THEN
        RAISE EXCEPTION 'V4 correction foundation requires its applicability projection';
      END IF;
      FOR target_projection_id IN SELECT DISTINCT value FROM unnest(target_projection_ids) AS ids(value) LOOP
        SELECT s.generation,s.validated_generation INTO dirty_generation,clean_generation
          FROM paprnav_v4_app_validation_state s WHERE s.projection_id=target_projection_id;
        IF dirty_generation IS NULL OR dirty_generation IS DISTINCT FROM clean_generation THEN
          PERFORM paprnav_v4_candidate_app_require_complete(target_projection_id);
          IF dirty_generation IS NOT NULL THEN
            UPDATE paprnav_v4_app_validation_state s
               SET validated_generation=s.generation
             WHERE s.projection_id=target_projection_id;
          END IF;
        END IF;
      END LOOP;
      RETURN NULL;
    END; $$ LANGUAGE plpgsql
    """)
    for table in APP_TABLES[1:]:
        op.execute(
            f"CREATE CONSTRAINT TRIGGER trg_{table}_complete "
            f"AFTER INSERT OR UPDATE OR DELETE ON {table} DEFERRABLE INITIALLY DEFERRED FOR EACH ROW "
            "EXECUTE FUNCTION paprnav_v4_candidate_app_complete_trigger()"
        )


def downgrade() -> None:
    op.execute("LOCK TABLE ad_v4_candidate_proposals IN ACCESS EXCLUSIVE MODE")
    op.execute("LOCK TABLE ad_v4_feature_gates IN ACCESS EXCLUSIVE MODE")
    for table in CHILD_TABLES:
        op.execute(f"LOCK TABLE {table} IN ACCESS EXCLUSIVE MODE")
    for table in APP_TABLES[1:]:
        op.execute(f"LOCK TABLE {table} IN ACCESS EXCLUSIVE MODE")
    bind = op.get_bind()
    if bind.execute(sa.text("SELECT 1 FROM ad_v4_candidate_proposals WHERE validator_version=:v LIMIT 1"), {"v": V2_VALIDATOR}).first() is not None:
        raise RuntimeError("Revision 0027 contains immutable validator-2 candidates; retain dual readers")
    for table in APP_TABLES[1:]:
        if bind.execute(sa.text(f"SELECT 1 FROM {table} LIMIT 1")).first() is not None:
            raise RuntimeError("Revision 0027 contains immutable Slice-3A rows; retain dual readers")
    for table in APP_TABLES[1:]:
        op.execute(f"DROP TRIGGER IF EXISTS trg_{table}_complete ON {table}")
        op.execute(f"DROP TRIGGER IF EXISTS trg_{table}_mark_dirty ON {table}")
    op.execute("DROP FUNCTION IF EXISTS paprnav_v4_candidate_app_complete_trigger()")
    op.execute("DROP FUNCTION IF EXISTS paprnav_v4_candidate_app_mark_dirty()")
    op.execute("DROP FUNCTION IF EXISTS paprnav_v4_candidate_app_require_complete(text)")
    op.execute("DROP FUNCTION IF EXISTS paprnav_v4_candidate_app_typed_subtree(text)")
    op.execute("DROP FUNCTION IF EXISTS paprnav_v4_app_search_group_json(text,text)")
    op.execute("DROP FUNCTION IF EXISTS paprnav_v4_app_condition_group_json(text,text)")
    op.execute("DROP FUNCTION IF EXISTS paprnav_v4_app_expression_json(text,text)")
    op.execute("DROP FUNCTION IF EXISTS paprnav_v4_app_designation_json(text,text)")
    op.execute("DROP FUNCTION IF EXISTS paprnav_v4_app_normalized_json(text,text,text)")
    op.execute("DROP FUNCTION IF EXISTS paprnav_v4_app_assertion_json(text,text)")
    op.execute("DROP FUNCTION IF EXISTS paprnav_v4_app_evidence_json(text,text)")
    for table in reversed(APP_TABLES):
        op.drop_table(table)
    op.execute("DROP FUNCTION IF EXISTS paprnav_v4_candidate_app_complete_trigger()")
    op.execute("DROP FUNCTION IF EXISTS paprnav_v4_candidate_app_mark_dirty()")
    op.execute("DROP FUNCTION IF EXISTS paprnav_v4_candidate_app_require_complete(text)")
    op.execute("DROP FUNCTION IF EXISTS paprnav_v4_jcs(jsonb)")
    op.execute("DROP FUNCTION IF EXISTS paprnav_v4_pointer_value(jsonb,text)")
    op.execute("DROP FUNCTION IF EXISTS paprnav_v4_json_nodes(jsonb,text,text,text,integer)")
    op.execute("DROP FUNCTION IF EXISTS paprnav_v4_validate_app_event()")
    op.execute("DROP FUNCTION IF EXISTS paprnav_v4_validate_app_request()")
    op.execute("DROP FUNCTION IF EXISTS paprnav_v4_validate_app_projection()")
    op.execute("DROP FUNCTION IF EXISTS paprnav_v4_lock_app_ad_numbers(text)")
    op.drop_constraint("uq_ad_v4_binding_parent_identity", "ad_v4_candidate_evidence_bindings", type_="unique")
    op.drop_constraint("uq_ad_v4_proposal_content_v2", "ad_v4_candidate_proposals", type_="unique")
    op.create_unique_constraint("uq_ad_v4_proposal_content", "ad_v4_candidate_proposals", ["directive_id", "canonicalization_version", "canonical_hash"])
    for table in reversed(CHILD_TABLES):
        op.drop_constraint(f"ck_{table}_version_pair", table, type_="check")
        op.drop_column(table, "canonicalization_version")
        op.drop_column(table, "validator_version")
    op.execute("DROP FUNCTION IF EXISTS paprnav_set_v4_feature_gate(text,boolean,text)")
    op.execute("DROP FUNCTION IF EXISTS paprnav_v4_capabilities()")
    # A physical downgrade is legal only for v1-only state. Deployment must run
    # revision-0026 code after Alembic completes; pre-v2 code is forbidden while
    # any v2 row exists by the checks above.
