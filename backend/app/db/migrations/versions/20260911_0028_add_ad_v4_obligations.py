"""add candidate-only V4 obligation projection persistence

Revision ID: 20260911_0028
Revises: 20260907_0027
Create Date: 2026-09-11
"""

from pathlib import Path

from alembic import op
import sqlalchemy as sa


revision = "20260911_0028"
down_revision = "20260907_0027"
branch_labels = None
depends_on = None

V2_VALIDATOR = "paprnav-ad-v4-validator-2"
V2_C14N = "paprnav-ad-v4-c14n-2"
MATERIALIZER = "paprnav-ad-v4-obligation-materializer-1"
MAPPING_VERSION = "paprnav-ad-v4-obligation-mapping-1"

SQL_PATH = (
    Path(__file__).resolve().parents[1]
    / "sql/20260911_0028_obligation_expectations.sql"
)
INTEGRITY_SQL_PATH = (
    Path(__file__).resolve().parents[1]
    / "sql/20260911_0028_obligation_integrity.sql"
)

OWNER_TABLES = (
    "ad_v4_candidate_obligation_documents",
    "ad_v4_candidate_obligation_value_assertions",
    "ad_v4_candidate_obligation_requirements",
    "ad_v4_candidate_obligation_actions",
    "ad_v4_candidate_obligation_action_steps",
    "ad_v4_candidate_obligation_branches",
    "ad_v4_candidate_obligation_expressions",
    "ad_v4_candidate_obligation_timing_groups",
    "ad_v4_candidate_obligation_timing_terms",
    "ad_v4_candidate_obligation_recurrences",
    "ad_v4_candidate_obligation_terminating_effects",
    "ad_v4_candidate_obligation_recurrence_groups",
    "ad_v4_candidate_obligation_amoc_provisions",
)

RELATIONSHIP_TABLES = (
    "ad_v4_candidate_obligation_action_document_refs",
    "ad_v4_candidate_obligation_expression_edges",
    "ad_v4_candidate_obligation_requirement_dependencies",
    "ad_v4_candidate_obligation_termination_edges",
    "ad_v4_candidate_obligation_recurrence_group_members",
)

OBLIGATION_TABLES = (
    "ad_v4_candidate_obligation_projections",
    "ad_v4_candidate_obligation_materialization_requests",
    "ad_v4_candidate_obligation_semantic_nodes",
    "ad_v4_candidate_obligation_data",
    "ad_v4_candidate_obligation_evidence_links",
    *OWNER_TABLES,
    *RELATIONSHIP_TABLES,
    "ad_v4_candidate_obligation_projection_events",
)

# Downgrade competes with the supported root-first materialization protocol.
# Keep every dependent table after the projection root and keep the shared
# correction/gate tables last so ACCESS EXCLUSIVE DDL never holds a child while
# waiting for a writer's parent lock.
DOWNGRADE_LOCK_TABLES = (
    "ad_v4_candidate_obligation_projections",
    "ad_v4_candidate_obligation_materialization_requests",
    "ad_v4_candidate_obligation_semantic_nodes",
    "ad_v4_candidate_obligation_data",
    "ad_v4_candidate_obligation_evidence_links",
    "ad_v4_candidate_obligation_documents",
    "ad_v4_candidate_obligation_value_assertions",
    "ad_v4_candidate_obligation_requirements",
    "ad_v4_candidate_obligation_actions",
    "ad_v4_candidate_obligation_branches",
    "ad_v4_candidate_obligation_expressions",
    "ad_v4_candidate_obligation_timing_groups",
    "ad_v4_candidate_obligation_recurrences",
    "ad_v4_candidate_obligation_terminating_effects",
    "ad_v4_candidate_obligation_recurrence_groups",
    "ad_v4_candidate_obligation_amoc_provisions",
    "ad_v4_candidate_obligation_action_steps",
    "ad_v4_candidate_obligation_action_document_refs",
    "ad_v4_candidate_obligation_expression_edges",
    "ad_v4_candidate_obligation_requirement_dependencies",
    "ad_v4_candidate_obligation_timing_terms",
    "ad_v4_candidate_obligation_termination_edges",
    "ad_v4_candidate_obligation_recurrence_group_members",
    "ad_v4_candidate_obligation_projection_events",
    "ad_v4_candidate_correction_semantic_bindings",
    "ad_v4_feature_gates",
)


_APP_VALIDATOR_CORRECTION_V0027 = """                OR (r.owner_slice='slice_3a' AND (SELECT count(*) FROM ad_v4_candidate_correction_semantic_bindings b WHERE b.correction_ref_id=r.id)<>1)
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
                        'table','correction-binding','identity',jsonb_build_object('refId',r.id,'semanticId',n.id))),'UTF8')),'hex')))))"""


_APP_VALIDATOR_CORRECTION_V0028 = """                OR (r.owner_slice='slice_3a' AND (SELECT count(*) FROM ad_v4_candidate_correction_semantic_bindings b WHERE b.correction_ref_id=r.id)<>1)
                OR (r.owner_slice='foundation' AND EXISTS (SELECT 1 FROM ad_v4_candidate_correction_semantic_bindings b WHERE b.correction_ref_id=r.id))
                OR (r.owner_slice='slice_3b' AND (SELECT count(*) FROM ad_v4_candidate_correction_semantic_bindings b WHERE b.correction_ref_id=r.id) NOT IN (0,1))
                OR EXISTS (
                  SELECT 1 FROM ad_v4_candidate_correction_semantic_bindings b
                  JOIN ad_v4_candidate_obligation_semantic_nodes n ON n.id=b.obligation_semantic_node_id
                  WHERE b.correction_ref_id=r.id AND b.binding_slice='slice_3b' AND (
                    b.proposal_id<>proposal.id OR b.projection_id IS NOT NULL OR b.semantic_node_id IS NOT NULL
                    OR b.obligation_projection_id IS NULL OR b.generation<>1
                    OR n.projection_id<>b.obligation_projection_id OR n.proposal_id<>proposal.id
                    OR n.node_type<>CASE r.namespace WHEN 'requirements' THEN 'requirement' WHEN 'recurrenceGroups' THEN 'recurrence_group' ELSE 'amoc_provision' END
                    OR n.node_key<>r.semantic_key
                    OR b.binding_hash<>encode(sha256(
                      convert_to('paprnav:ad_extraction_v4:obligation-row:1','UTF8')||decode('00','hex')||
                      convert_to(paprnav_v4_obligation_record(jsonb_build_object(
                        'table','correction-binding','identity',jsonb_build_object('refId',r.id,'semanticId',n.id))),'UTF8')),'hex')
                    OR b.id<>'avk_'||substr(b.binding_hash,1,32)))
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
                        'table','correction-binding','identity',jsonb_build_object('refId',r.id,'semanticId',n.id))),'UTF8')),'hex')))))"""


def _set_app_validator_slice3b_compatibility(*, enabled: bool) -> None:
    """Patch only the 0027 correction clause; fail if its installed shape drifted."""
    source = _APP_VALIDATOR_CORRECTION_V0027 if enabled else _APP_VALIDATOR_CORRECTION_V0028
    target = _APP_VALIDATOR_CORRECTION_V0028 if enabled else _APP_VALIDATOR_CORRECTION_V0027
    bind = op.get_bind()
    definition = bind.execute(sa.text(
        "SELECT pg_get_functiondef("
        "'paprnav_v4_candidate_app_require_complete(text)'::regprocedure)"
    )).scalar_one()
    if definition.count(source) != 1 or target in definition:
        direction = "upgrade" if enabled else "downgrade"
        raise RuntimeError(
            f"Revision 0028 cannot {direction}: installed Slice-3A validator drifted"
        )
    with bind.connection.driver_connection.cursor() as cursor:
        cursor.execute(definition.replace(source, target))


def _id(name: str, *, primary: bool = False, nullable: bool = False) -> sa.Column:
    return sa.Column(name, sa.String(36), primary_key=primary, nullable=nullable)


def _owner_table(name: str, *items: object) -> None:
    op.create_table(
        name,
        _id("semantic_node_id", primary=True),
        _id("proposal_id"),
        _id("projection_id"),
        *items,
        sa.ForeignKeyConstraint(
            ["proposal_id"], ["ad_v4_candidate_proposals.id"], ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["projection_id", "proposal_id"],
            ["ad_v4_candidate_obligation_projections.id", "ad_v4_candidate_obligation_projections.proposal_id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["semantic_node_id", "projection_id", "proposal_id"],
            ["ad_v4_candidate_obligation_semantic_nodes.id", "ad_v4_candidate_obligation_semantic_nodes.projection_id", "ad_v4_candidate_obligation_semantic_nodes.proposal_id"],
            ondelete="RESTRICT",
        ),
    )


def _relationship_table(name: str, *items: object) -> None:
    op.create_table(
        name,
        _id("id", primary=True),
        sa.Column("identity_hash", sa.String(64), nullable=False, unique=True),
        _id("proposal_id"),
        _id("projection_id"),
        *items,
        sa.ForeignKeyConstraint(
            ["proposal_id"], ["ad_v4_candidate_proposals.id"], ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["projection_id", "proposal_id"],
            ["ad_v4_candidate_obligation_projections.id", "ad_v4_candidate_obligation_projections.proposal_id"],
            ondelete="RESTRICT",
        ),
    )


def _create_projection_root() -> None:
    count_names = (
        "semantic_node_count", "datum_count", "evidence_link_count",
        "document_count", "value_assertion_count", "requirement_count",
        "action_count", "action_step_count", "action_document_ref_count",
        "branch_count", "expression_count", "expression_edge_count",
        "requirement_dependency_count", "timing_group_count",
        "timing_term_count", "recurrence_count", "terminating_effect_count",
        "termination_edge_count", "recurrence_group_count",
        "recurrence_group_member_count", "amoc_provision_count",
        "correction_binding_count",
    )
    op.create_table(
        "ad_v4_candidate_obligation_projections",
        _id("id", primary=True),
        sa.Column("identity_hash", sa.String(64), nullable=False, unique=True),
        _id("proposal_id"),
        _id("directive_id"),
        sa.Column("validator_version", sa.String(64), nullable=False),
        sa.Column("canonicalization_version", sa.String(64), nullable=False),
        sa.Column("proposal_canonical_hash", sa.String(64), nullable=False),
        sa.Column("evidence_binding_hash", sa.String(64), nullable=False),
        _id("app_projection_id"),
        sa.Column("app_projection_hash", sa.String(64), nullable=False),
        sa.Column("app_materializer_version", sa.String(64), nullable=False),
        sa.Column("materializer_version", sa.String(64), nullable=False),
        sa.Column("mapping_version", sa.String(64), nullable=False),
        sa.Column("mapping_digest", sa.String(64), nullable=False),
        sa.Column("obligation_subtree_bytes", sa.LargeBinary(), nullable=False),
        sa.Column("obligation_subtree_hash", sa.String(64), nullable=False),
        sa.Column("projection_canonical_bytes", sa.LargeBinary(), nullable=False),
        sa.Column("projection_hash", sa.String(64), nullable=False),
        sa.Column("gate", sa.String(32), nullable=False),
        *(sa.Column(name, sa.Integer(), nullable=False) for name in count_names),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(
            ["proposal_id"], ["ad_v4_candidate_proposals.id"], ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["directive_id"], ["airworthiness_directives.id"], ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["app_projection_id", "proposal_id"],
            ["ad_v4_candidate_app_projections.id", "ad_v4_candidate_app_projections.proposal_id"],
            ondelete="RESTRICT",
        ),
        sa.CheckConstraint("gate='candidate_only'", name="ck_ad_v4_obligation_projection_gate"),
        sa.CheckConstraint(
            f"validator_version='{V2_VALIDATOR}' AND canonicalization_version='{V2_C14N}'",
            name="ck_ad_v4_obligation_projection_v2",
        ),
        sa.CheckConstraint(
            f"materializer_version='{MATERIALIZER}'",
            name="ck_ad_v4_obligation_materializer",
        ),
        sa.CheckConstraint(
            f"mapping_version='{MAPPING_VERSION}'",
            name="ck_ad_v4_obligation_mapping_version",
        ),
        sa.CheckConstraint(
            "semantic_node_count>=0 AND datum_count>=0 AND evidence_link_count>=0 "
            "AND document_count>=0 AND value_assertion_count>=0 AND requirement_count>=0 "
            "AND action_count>=0 AND action_step_count>=0 AND action_document_ref_count>=0 "
            "AND branch_count>=0 AND expression_count>=0 AND expression_edge_count>=0 "
            "AND requirement_dependency_count>=0 AND timing_group_count>=0 "
            "AND timing_term_count>=0 AND recurrence_count>=0 AND terminating_effect_count>=0 "
            "AND termination_edge_count>=0 AND recurrence_group_count>=0 "
            "AND recurrence_group_member_count>=0 AND amoc_provision_count>=0 "
            "AND correction_binding_count>=0",
            name="ck_ad_v4_obligation_projection_counts",
        ),
        sa.UniqueConstraint(
            "id", "proposal_id", name="uq_ad_v4_obligation_projection_parent_identity",
        ),
        sa.UniqueConstraint(
            "proposal_id", "materializer_version",
            name="uq_ad_v4_obligation_projection_parent",
        ),
    )
    op.create_index(
        "ix_ad_v4_obligation_projection_proposal",
        "ad_v4_candidate_obligation_projections",
        ["proposal_id", "materializer_version"],
    )


def _create_request_and_generic_tables() -> None:
    op.create_table(
        "ad_v4_candidate_obligation_materialization_requests",
        _id("id", primary=True),
        sa.Column("identity_hash", sa.String(64), nullable=False, unique=True),
        _id("projection_id"), _id("proposal_id"), _id("directive_id"),
        _id("app_projection_id"), _id("actor_user_id"),
        _id("authorizing_membership_id"), _id("organization_id"),
        sa.Column("actor_role", sa.String(64), nullable=False),
        sa.Column("actor_status", sa.String(32), nullable=False),
        sa.Column("auth_policy_name", sa.String(96), nullable=False),
        sa.Column("auth_policy_version", sa.String(64), nullable=False),
        sa.Column("auth_claims_hash", sa.String(64), nullable=False),
        sa.Column("endpoint_action", sa.String(96), nullable=False),
        sa.Column("idempotency_key", sa.String(255), nullable=False),
        sa.Column("request_canonical_bytes", sa.LargeBinary(), nullable=False),
        sa.Column("request_hash", sa.String(64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(
            ["projection_id", "proposal_id"],
            ["ad_v4_candidate_obligation_projections.id", "ad_v4_candidate_obligation_projections.proposal_id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(["directive_id"], ["airworthiness_directives.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["app_projection_id", "proposal_id"],
            ["ad_v4_candidate_app_projections.id", "ad_v4_candidate_app_projections.proposal_id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(["actor_user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["authorizing_membership_id"], ["organization_memberships.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="RESTRICT"),
        sa.CheckConstraint("actor_role='platform_admin' AND actor_status='active'", name="ck_ad_v4_obligation_request_actor"),
        sa.CheckConstraint("endpoint_action='materialize_ad_v4_obligations'", name="ck_ad_v4_obligation_request_action"),
        sa.UniqueConstraint(
            "actor_user_id", "authorizing_membership_id", "endpoint_action",
            "auth_policy_version", "idempotency_key",
            name="uq_ad_v4_obligation_request_idempotency",
        ),
    )
    op.create_table(
        "ad_v4_candidate_obligation_semantic_nodes",
        _id("id", primary=True),
        sa.Column("identity_hash", sa.String(64), nullable=False, unique=True),
        _id("projection_id"), _id("proposal_id"),
        _id("parent_node_id", nullable=True),
        sa.Column("node_type", sa.String(64), nullable=False),
        sa.Column("node_key", sa.Text(), nullable=False),
        sa.Column("source_pointer", sa.Text(), nullable=False),
        sa.Column("canonical_node_hash", sa.String(64), nullable=False),
        sa.Column("canonical_ordinal", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(
            ["projection_id", "proposal_id"],
            ["ad_v4_candidate_obligation_projections.id", "ad_v4_candidate_obligation_projections.proposal_id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["parent_node_id", "projection_id", "proposal_id"],
            ["ad_v4_candidate_obligation_semantic_nodes.id", "ad_v4_candidate_obligation_semantic_nodes.projection_id", "ad_v4_candidate_obligation_semantic_nodes.proposal_id"],
            ondelete="RESTRICT",
        ),
        sa.CheckConstraint("canonical_ordinal BETWEEN 0 AND 2147483647", name="ck_ad_v4_obligation_node_ordinal"),
        sa.CheckConstraint(
            "node_type IN ('incorporated_document','value_assertion','requirement','action','action_step','branch','expression','timing_group','timing_term','recurrence','terminating_effect','recurrence_group','amoc_provision')",
            name="ck_ad_v4_obligation_node_type",
        ),
        sa.UniqueConstraint("id", "projection_id", "proposal_id", name="uq_ad_v4_obligation_node_parent_identity"),
        sa.UniqueConstraint("projection_id", "node_type", "node_key", name="uq_ad_v4_obligation_node_key"),
        sa.UniqueConstraint("projection_id", "source_pointer", name="uq_ad_v4_obligation_node_pointer"),
    )
    op.create_index("ix_ad_v4_obligation_node_projection", "ad_v4_candidate_obligation_semantic_nodes", ["projection_id", "node_type"])
    op.create_table(
        "ad_v4_candidate_obligation_data",
        _id("id", primary=True),
        sa.Column("identity_hash", sa.String(64), nullable=False, unique=True),
        _id("projection_id"), _id("proposal_id"),
        _id("semantic_node_id", nullable=True),
        sa.Column("json_pointer", sa.Text(), nullable=False),
        sa.Column("parent_pointer", sa.Text(), nullable=True),
        sa.Column("property_name", sa.Text(), nullable=True),
        sa.Column("array_ordinal", sa.Integer(), nullable=True),
        sa.Column("value_kind", sa.String(16), nullable=False),
        sa.Column("string_value", sa.Text(), nullable=True),
        sa.Column("boolean_value", sa.Boolean(), nullable=True),
        sa.Column("value_hash", sa.String(64), nullable=False),
        sa.ForeignKeyConstraint(
            ["projection_id", "proposal_id"],
            ["ad_v4_candidate_obligation_projections.id", "ad_v4_candidate_obligation_projections.proposal_id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(["proposal_id"], ["ad_v4_candidate_proposals.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["semantic_node_id", "projection_id", "proposal_id"],
            ["ad_v4_candidate_obligation_semantic_nodes.id", "ad_v4_candidate_obligation_semantic_nodes.projection_id", "ad_v4_candidate_obligation_semantic_nodes.proposal_id"],
            ondelete="RESTRICT",
        ),
        sa.CheckConstraint("value_kind IN ('object','array','string','boolean')", name="ck_ad_v4_obligation_datum_kind"),
        sa.CheckConstraint(
            "(value_kind='string' AND string_value IS NOT NULL AND boolean_value IS NULL) OR "
            "(value_kind='boolean' AND string_value IS NULL AND boolean_value IS NOT NULL) OR "
            "(value_kind IN ('object','array') AND string_value IS NULL AND boolean_value IS NULL)",
            name="ck_ad_v4_obligation_datum_union",
        ),
        sa.UniqueConstraint("projection_id", "json_pointer", name="uq_ad_v4_obligation_datum_pointer"),
    )
    op.create_table(
        "ad_v4_candidate_obligation_evidence_links",
        _id("id", primary=True), _id("projection_id"), _id("proposal_id"),
        _id("semantic_node_id"), _id("candidate_binding_id"),
        sa.Column("evidence_key", sa.String(128), nullable=False),
        sa.Column("purpose", sa.String(64), nullable=False),
        sa.Column("canonical_ordinal", sa.Integer(), nullable=False),
        sa.Column("link_hash", sa.String(64), nullable=False, unique=True),
        sa.ForeignKeyConstraint(
            ["projection_id", "proposal_id"],
            ["ad_v4_candidate_obligation_projections.id", "ad_v4_candidate_obligation_projections.proposal_id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(["proposal_id"], ["ad_v4_candidate_proposals.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["semantic_node_id", "projection_id", "proposal_id"],
            ["ad_v4_candidate_obligation_semantic_nodes.id", "ad_v4_candidate_obligation_semantic_nodes.projection_id", "ad_v4_candidate_obligation_semantic_nodes.proposal_id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["proposal_id", "candidate_binding_id", "evidence_key"],
            ["ad_v4_candidate_evidence_bindings.proposal_id", "ad_v4_candidate_evidence_bindings.id", "ad_v4_candidate_evidence_bindings.evidence_key"],
            ondelete="RESTRICT",
        ),
        sa.CheckConstraint("canonical_ordinal BETWEEN 0 AND 2147483647", name="ck_ad_v4_obligation_evidence_ordinal"),
        sa.CheckConstraint(
            "purpose IN ('incorporated_document_clause','document_identity','document_retention','requirement_clause','action_clause','branch_clause','timing_clause','timing_term_clause','recurrence_clause','termination_clause','amoc_authority_clause')",
            name="ck_ad_v4_obligation_evidence_purpose",
        ),
        sa.UniqueConstraint("semantic_node_id", "purpose", "evidence_key", name="uq_ad_v4_obligation_evidence_link"),
        sa.UniqueConstraint("semantic_node_id", "purpose", "canonical_ordinal", name="uq_ad_v4_obligation_evidence_ordinal"),
    )


def _create_owner_tables() -> None:
    _owner_table(
        "ad_v4_candidate_obligation_documents",
        sa.Column("document_ref_key", sa.String(128), nullable=False),
        sa.Column("document_type", sa.String(64), nullable=False),
        sa.Column("canonical_ordinal", sa.Integer(), nullable=False),
        _id("document_number_node_id"), _id("revision_node_id"), _id("retention_node_id"),
        sa.CheckConstraint("document_type IN ('service_bulletin','service_letter','service_instruction','maintenance_manual','approved_data','other_reviewed')", name="ck_ad_v4_obligation_document_type"),
        sa.UniqueConstraint("projection_id", "document_ref_key", name="uq_ad_v4_obligation_document_key"),
        sa.UniqueConstraint("projection_id", "canonical_ordinal", name="uq_ad_v4_obligation_document_ordinal"),
    )
    _owner_table(
        "ad_v4_candidate_obligation_value_assertions",
        sa.Column("field_code", sa.String(64), nullable=False),
        sa.Column("state", sa.String(32), nullable=False),
        sa.Column("value", sa.Text(), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("temporal_kind", sa.String(64), nullable=True),
        sa.CheckConstraint("field_code IN ('document_number','revision','retention','approving_authority')", name="ck_ad_v4_obligation_assertion_field"),
        sa.CheckConstraint("state IN ('known','unknown','not_applicable')", name="ck_ad_v4_obligation_assertion_state"),
        sa.CheckConstraint("(state='known' AND value IS NOT NULL AND reason IS NULL AND temporal_kind IS NULL) OR (state IN ('unknown','not_applicable') AND value IS NULL AND reason IS NOT NULL AND temporal_kind IS NOT NULL)", name="ck_ad_v4_obligation_assertion_union"),
        sa.CheckConstraint("field_code<>'retention' OR state='unknown'", name="ck_ad_v4_obligation_retention_unknown"),
        sa.UniqueConstraint("projection_id", "semantic_node_id", name="uq_ad_v4_obligation_assertion_node"),
    )
    _owner_table(
        "ad_v4_candidate_obligation_requirements",
        sa.Column("requirement_key", sa.String(128), nullable=False),
        sa.Column("sequence_text", sa.Text(), nullable=False),
        sa.Column("sequence_value", sa.Integer(), nullable=False),
        sa.Column("requirement_type", sa.String(64), nullable=False),
        sa.Column("canonical_ordinal", sa.Integer(), nullable=False),
        sa.Column("recurrence_group_present", sa.Boolean(), nullable=False),
        sa.Column("recurrence_group_key", sa.String(128), nullable=True),
        _id("action_node_id"), _id("activation_root_node_id"), _id("branch_node_id"),
        _id("initial_timing_node_id"), _id("recurrence_node_id"), _id("terminating_effect_node_id"),
        sa.CheckConstraint("sequence_value BETWEEN 1 AND 2000", name="ck_ad_v4_obligation_requirement_sequence"),
        sa.CheckConstraint("canonical_ordinal BETWEEN 0 AND 1999", name="ck_ad_v4_obligation_requirement_ordinal"),
        sa.CheckConstraint("requirement_type IN ('inspection','replacement','modification','software_update','limitation','reporting','installation_prohibition','corrective_action','other_reviewed')", name="ck_ad_v4_obligation_requirement_type"),
        sa.CheckConstraint("recurrence_group_present=(recurrence_group_key IS NOT NULL)", name="ck_ad_v4_obligation_requirement_group_presence"),
        sa.UniqueConstraint("projection_id", "requirement_key", name="uq_ad_v4_obligation_requirement_key"),
        sa.UniqueConstraint("projection_id", "sequence_value", name="uq_ad_v4_obligation_requirement_sequence"),
        sa.UniqueConstraint("projection_id", "canonical_ordinal", name="uq_ad_v4_obligation_requirement_ordinal"),
    )
    _owner_table(
        "ad_v4_candidate_obligation_actions",
        _id("requirement_node_id"),
        sa.Column("action_type", sa.String(64), nullable=False),
        sa.Column("ordered_steps_present", sa.Boolean(), nullable=False),
        sa.Column("step_count", sa.Integer(), nullable=False),
        sa.Column("document_ref_count", sa.Integer(), nullable=False),
        sa.CheckConstraint("action_type IN ('inspect','replace','repair','modify','software_update','revise_limitation','report','installation_prohibition','remove','rework','other_reviewed')", name="ck_ad_v4_obligation_action_type"),
        sa.CheckConstraint("step_count BETWEEN 0 AND 2000 AND document_ref_count BETWEEN 0 AND 2000", name="ck_ad_v4_obligation_action_counts"),
        sa.CheckConstraint("ordered_steps_present OR step_count=0", name="ck_ad_v4_obligation_action_step_presence"),
        sa.UniqueConstraint("projection_id", "requirement_node_id", name="uq_ad_v4_obligation_action_requirement"),
    )
    _owner_table(
        "ad_v4_candidate_obligation_action_steps",
        _id("action_node_id"), sa.Column("step_text", sa.Text(), nullable=False),
        sa.Column("canonical_ordinal", sa.Integer(), nullable=False),
        sa.CheckConstraint("canonical_ordinal BETWEEN 0 AND 1999", name="ck_ad_v4_obligation_action_step_ordinal"),
        sa.UniqueConstraint("action_node_id", "canonical_ordinal", name="uq_ad_v4_obligation_action_step_ordinal"),
    )
    _owner_table(
        "ad_v4_candidate_obligation_branches",
        _id("requirement_node_id"), sa.Column("kind", sa.String(32), nullable=False),
        sa.Column("alternative_group_key", sa.String(128), nullable=True),
        sa.Column("exclusive", sa.Boolean(), nullable=True), _id("condition_root_node_id", nullable=True),
        sa.CheckConstraint("kind IN ('required','conditional','exception','alternative_member')", name="ck_ad_v4_obligation_branch_kind"),
        sa.CheckConstraint("(kind='required' AND alternative_group_key IS NULL AND exclusive IS NULL AND condition_root_node_id IS NULL) OR (kind IN ('conditional','exception') AND alternative_group_key IS NULL AND exclusive IS NULL AND condition_root_node_id IS NOT NULL) OR (kind='alternative_member' AND alternative_group_key IS NOT NULL AND exclusive IS NOT NULL AND condition_root_node_id IS NULL)", name="ck_ad_v4_obligation_branch_union"),
        sa.UniqueConstraint("projection_id", "requirement_node_id", name="uq_ad_v4_obligation_branch_requirement"),
    )
    _owner_table(
        "ad_v4_candidate_obligation_expressions",
        _id("requirement_node_id"), sa.Column("context", sa.String(32), nullable=False),
        sa.Column("expression_path", sa.Text(), nullable=False),
        sa.Column("node_type", sa.String(32), nullable=False),
        sa.Column("required_state", sa.String(32), nullable=True),
        _id("app_target_projection_id", nullable=True), _id("app_target_node_id", nullable=True),
        _id("requirement_target_node_id", nullable=True),
        sa.CheckConstraint("context IN ('activation','branch_condition','recurrence_condition')", name="ck_ad_v4_obligation_expression_context"),
        sa.CheckConstraint("node_type IN ('scope_ref','predicate_ref','rule_ref','requirement_state_ref','not','all','any')", name="ck_ad_v4_obligation_expression_type"),
        sa.CheckConstraint("(node_type IN ('scope_ref','predicate_ref','rule_ref') AND required_state IS NULL AND app_target_projection_id IS NOT NULL AND app_target_node_id IS NOT NULL AND requirement_target_node_id IS NULL) OR (node_type='requirement_state_ref' AND required_state IS NOT NULL AND app_target_projection_id IS NULL AND app_target_node_id IS NULL AND requirement_target_node_id IS NOT NULL) OR (node_type IN ('not','all','any') AND required_state IS NULL AND app_target_projection_id IS NULL AND app_target_node_id IS NULL AND requirement_target_node_id IS NULL)", name="ck_ad_v4_obligation_expression_union"),
        sa.UniqueConstraint("projection_id", "requirement_node_id", "context", "expression_path", name="uq_ad_v4_obligation_expression_path"),
    )
    _owner_table(
        "ad_v4_candidate_obligation_timing_groups",
        sa.Column("owner_kind", sa.String(64), nullable=False), _id("owner_node_id"),
        sa.Column("state", sa.String(32), nullable=False),
        sa.Column("logic", sa.String(32), nullable=True), sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("temporal_kind", sa.String(64), nullable=True),
        sa.Column("canonical_ordinal", sa.Integer(), nullable=False),
        sa.Column("term_count", sa.Integer(), nullable=False),
        sa.CheckConstraint("owner_kind IN ('requirement_initial','requirement_recurrence','recurrence_group_initial','recurrence_group_recurring')", name="ck_ad_v4_obligation_timing_owner_kind"),
        sa.CheckConstraint("state IN ('known','unknown','not_applicable')", name="ck_ad_v4_obligation_timing_state"),
        sa.CheckConstraint("(state='known' AND logic IS NOT NULL AND logic IN ('all','whichever_first','whichever_later') AND reason IS NULL AND temporal_kind IS NULL AND term_count>=1) OR (state IN ('unknown','not_applicable') AND logic IS NULL AND reason IS NOT NULL AND temporal_kind IS NOT NULL AND term_count=0)", name="ck_ad_v4_obligation_timing_union"),
        sa.CheckConstraint("canonical_ordinal BETWEEN 0 AND 1999 AND term_count BETWEEN 0 AND 2000", name="ck_ad_v4_obligation_timing_counts"),
        sa.UniqueConstraint("projection_id", "owner_node_id", "owner_kind", name="uq_ad_v4_obligation_timing_owner"),
    )
    _owner_table(
        "ad_v4_candidate_obligation_timing_terms",
        _id("timing_group_node_id"), sa.Column("metric", sa.String(32), nullable=False),
        sa.Column("interval_text", sa.Text(), nullable=False),
        sa.Column("interval_numeric", sa.Numeric(), nullable=False),
        sa.Column("unit", sa.String(32), nullable=False),
        sa.Column("comparator", sa.String(32), nullable=False),
        sa.Column("anchor", sa.String(32), nullable=False),
        sa.Column("canonical_ordinal", sa.Integer(), nullable=False),
        sa.CheckConstraint("metric IN ('calendar','aircraft_time','component_time','cycles','other_reviewed')", name="ck_ad_v4_obligation_timing_metric"),
        sa.CheckConstraint("unit IN ('days','months','years','hours','cycles','source_defined')", name="ck_ad_v4_obligation_timing_unit"),
        sa.CheckConstraint("comparator IN ('within','before','at_or_before','after','at_or_after')", name="ck_ad_v4_obligation_timing_comparator"),
        sa.CheckConstraint("anchor IN ('effective_date','last_compliance','installation','manufacture','source_defined')", name="ck_ad_v4_obligation_timing_anchor"),
        sa.CheckConstraint("canonical_ordinal BETWEEN 0 AND 1999", name="ck_ad_v4_obligation_timing_term_ordinal"),
        sa.UniqueConstraint("timing_group_node_id", "canonical_ordinal", name="uq_ad_v4_obligation_timing_term_ordinal"),
    )
    _owner_table(
        "ad_v4_candidate_obligation_recurrences",
        _id("requirement_node_id"), sa.Column("kind", sa.String(32), nullable=False),
        _id("timing_node_id", nullable=True), _id("condition_root_node_id", nullable=True),
        sa.Column("reason", sa.Text(), nullable=True), sa.Column("temporal_kind", sa.String(64), nullable=True),
        sa.CheckConstraint("kind IN ('none','interval','conditioned','unknown')", name="ck_ad_v4_obligation_recurrence_kind"),
        sa.CheckConstraint("(kind='none' AND timing_node_id IS NULL AND condition_root_node_id IS NULL AND reason IS NULL AND temporal_kind IS NULL) OR (kind='interval' AND timing_node_id IS NOT NULL AND condition_root_node_id IS NULL AND reason IS NULL AND temporal_kind IS NULL) OR (kind='conditioned' AND timing_node_id IS NOT NULL AND condition_root_node_id IS NOT NULL AND reason IS NULL AND temporal_kind IS NULL) OR (kind='unknown' AND timing_node_id IS NULL AND condition_root_node_id IS NULL AND reason IS NOT NULL AND temporal_kind IS NOT NULL)", name="ck_ad_v4_obligation_recurrence_union"),
        sa.UniqueConstraint("projection_id", "requirement_node_id", name="uq_ad_v4_obligation_recurrence_requirement"),
    )
    _owner_table(
        "ad_v4_candidate_obligation_terminating_effects",
        _id("requirement_node_id"), sa.Column("kind", sa.String(32), nullable=False),
        sa.Column("edge_count", sa.Integer(), nullable=False),
        sa.CheckConstraint("kind IN ('none','terminates')", name="ck_ad_v4_obligation_termination_kind"),
        sa.CheckConstraint("(kind='none' AND edge_count=0) OR (kind='terminates' AND edge_count>=0)", name="ck_ad_v4_obligation_termination_union"),
        sa.UniqueConstraint("projection_id", "requirement_node_id", name="uq_ad_v4_obligation_termination_requirement"),
    )
    _owner_table(
        "ad_v4_candidate_obligation_recurrence_groups",
        sa.Column("recurrence_group_key", sa.String(128), nullable=False),
        sa.Column("canonical_ordinal", sa.Integer(), nullable=False),
        sa.Column("completion_policy", sa.String(32), nullable=False),
        _id("initial_timing_node_id"), _id("recurring_timing_node_id"),
        sa.Column("member_count", sa.Integer(), nullable=False),
        sa.CheckConstraint("completion_policy='all_active_requirements'", name="ck_ad_v4_obligation_group_completion"),
        sa.CheckConstraint("canonical_ordinal BETWEEN 0 AND 1999 AND member_count BETWEEN 2 AND 2000", name="ck_ad_v4_obligation_group_counts"),
        sa.UniqueConstraint("projection_id", "recurrence_group_key", name="uq_ad_v4_obligation_group_key"),
        sa.UniqueConstraint("projection_id", "canonical_ordinal", name="uq_ad_v4_obligation_group_ordinal"),
    )
    _owner_table(
        "ad_v4_candidate_obligation_amoc_provisions",
        sa.Column("provision_key", sa.String(128), nullable=False),
        sa.Column("canonical_ordinal", sa.Integer(), nullable=False),
        _id("authority_assertion_node_id"),
        sa.CheckConstraint("canonical_ordinal BETWEEN 0 AND 1999", name="ck_ad_v4_obligation_amoc_ordinal"),
        sa.UniqueConstraint("projection_id", "provision_key", name="uq_ad_v4_obligation_amoc_key"),
        sa.UniqueConstraint("projection_id", "canonical_ordinal", name="uq_ad_v4_obligation_amoc_ordinal"),
    )


def _create_relationship_tables() -> None:
    _relationship_table(
        "ad_v4_candidate_obligation_action_document_refs",
        _id("action_node_id"), _id("document_node_id"),
        sa.Column("document_ref_key", sa.String(128), nullable=False),
        sa.Column("canonical_ordinal", sa.Integer(), nullable=False),
        sa.UniqueConstraint("action_node_id", "document_node_id", name="uq_ad_v4_obligation_action_document_target"),
        sa.UniqueConstraint("action_node_id", "canonical_ordinal", name="uq_ad_v4_obligation_action_document_ordinal"),
    )
    _relationship_table(
        "ad_v4_candidate_obligation_expression_edges",
        _id("requirement_node_id"), sa.Column("context", sa.String(32), nullable=False),
        _id("parent_expression_id"), _id("child_expression_id"),
        sa.Column("canonical_ordinal", sa.Integer(), nullable=False),
        sa.CheckConstraint("context IN ('activation','branch_condition','recurrence_condition')", name="ck_ad_v4_obligation_expression_edge_context"),
        sa.UniqueConstraint("parent_expression_id", "child_expression_id", name="uq_ad_v4_obligation_expression_edge_target"),
        sa.UniqueConstraint("parent_expression_id", "canonical_ordinal", name="uq_ad_v4_obligation_expression_edge_ordinal"),
    )
    _relationship_table(
        "ad_v4_candidate_obligation_requirement_dependencies",
        _id("requirement_node_id"), _id("prerequisite_requirement_node_id"),
        sa.Column("prerequisite_requirement_key", sa.String(128), nullable=False),
        sa.Column("dependency_kind", sa.String(32), nullable=False),
        sa.Column("canonical_ordinal", sa.Integer(), nullable=False),
        sa.CheckConstraint("dependency_kind='prerequisite'", name="ck_ad_v4_obligation_requirement_dependency_kind"),
        sa.UniqueConstraint("requirement_node_id", "prerequisite_requirement_node_id", name="uq_ad_v4_obligation_requirement_dependency_target"),
        sa.UniqueConstraint("requirement_node_id", "canonical_ordinal", name="uq_ad_v4_obligation_requirement_dependency_ordinal"),
    )
    _relationship_table(
        "ad_v4_candidate_obligation_termination_edges",
        _id("effect_node_id"), _id("terminated_requirement_node_id"),
        sa.Column("terminated_requirement_key", sa.String(128), nullable=False),
        sa.Column("canonical_ordinal", sa.Integer(), nullable=False),
        sa.UniqueConstraint("effect_node_id", "terminated_requirement_node_id", name="uq_ad_v4_obligation_termination_edge_target"),
        sa.UniqueConstraint("effect_node_id", "canonical_ordinal", name="uq_ad_v4_obligation_termination_edge_ordinal"),
    )
    _relationship_table(
        "ad_v4_candidate_obligation_recurrence_group_members",
        _id("group_node_id"), _id("requirement_node_id"),
        sa.Column("requirement_key", sa.String(128), nullable=False),
        sa.Column("canonical_ordinal", sa.Integer(), nullable=False),
        sa.UniqueConstraint("group_node_id", "requirement_node_id", name="uq_ad_v4_obligation_group_member_target"),
        sa.UniqueConstraint("group_node_id", "canonical_ordinal", name="uq_ad_v4_obligation_group_member_ordinal"),
    )
    for table in RELATIONSHIP_TABLES:
        op.create_check_constraint(
            f"ck_{table}_ordinal", table, "canonical_ordinal BETWEEN 0 AND 1999",
        )


def _install_same_projection_references() -> None:
    node_target = "ad_v4_candidate_obligation_semantic_nodes"

    def node_fk(table: str, column: str, name: str) -> None:
        op.create_foreign_key(
            name, table, node_target,
            [column, "projection_id", "proposal_id"],
            ["id", "projection_id", "proposal_id"],
            ondelete="RESTRICT",
        )

    obligation_refs = {
        "ad_v4_candidate_obligation_documents": (
            ("document_number_node_id", "fk_aob_doc_number"),
            ("revision_node_id", "fk_aob_doc_revision"),
            ("retention_node_id", "fk_aob_doc_retention"),
        ),
        "ad_v4_candidate_obligation_requirements": (
            ("action_node_id", "fk_aob_req_action"),
            ("activation_root_node_id", "fk_aob_req_activation"),
            ("branch_node_id", "fk_aob_req_branch"),
            ("initial_timing_node_id", "fk_aob_req_initial_timing"),
            ("recurrence_node_id", "fk_aob_req_recurrence"),
            ("terminating_effect_node_id", "fk_aob_req_termination"),
        ),
        "ad_v4_candidate_obligation_actions": (
            ("requirement_node_id", "fk_aob_action_requirement"),
        ),
        "ad_v4_candidate_obligation_action_steps": (
            ("action_node_id", "fk_aob_step_action"),
        ),
        "ad_v4_candidate_obligation_branches": (
            ("requirement_node_id", "fk_aob_branch_requirement"),
            ("condition_root_node_id", "fk_aob_branch_condition"),
        ),
        "ad_v4_candidate_obligation_expressions": (
            ("requirement_node_id", "fk_aob_expr_requirement"),
            ("requirement_target_node_id", "fk_aob_expr_req_target"),
        ),
        "ad_v4_candidate_obligation_timing_groups": (
            ("owner_node_id", "fk_aob_timing_owner"),
        ),
        "ad_v4_candidate_obligation_timing_terms": (
            ("timing_group_node_id", "fk_aob_term_timing"),
        ),
        "ad_v4_candidate_obligation_recurrences": (
            ("requirement_node_id", "fk_aob_recurrence_requirement"),
            ("timing_node_id", "fk_aob_recurrence_timing"),
            ("condition_root_node_id", "fk_aob_recurrence_condition"),
        ),
        "ad_v4_candidate_obligation_terminating_effects": (
            ("requirement_node_id", "fk_aob_effect_requirement"),
        ),
        "ad_v4_candidate_obligation_recurrence_groups": (
            ("initial_timing_node_id", "fk_aob_group_initial_timing"),
            ("recurring_timing_node_id", "fk_aob_group_recurring_timing"),
        ),
        "ad_v4_candidate_obligation_amoc_provisions": (
            ("authority_assertion_node_id", "fk_aob_amoc_authority"),
        ),
        "ad_v4_candidate_obligation_action_document_refs": (
            ("action_node_id", "fk_aob_docref_action"),
            ("document_node_id", "fk_aob_docref_document"),
        ),
        "ad_v4_candidate_obligation_expression_edges": (
            ("requirement_node_id", "fk_aob_expr_edge_requirement"),
            ("parent_expression_id", "fk_aob_expr_edge_parent"),
            ("child_expression_id", "fk_aob_expr_edge_child"),
        ),
        "ad_v4_candidate_obligation_requirement_dependencies": (
            ("requirement_node_id", "fk_aob_dep_requirement"),
            ("prerequisite_requirement_node_id", "fk_aob_dep_prerequisite"),
        ),
        "ad_v4_candidate_obligation_termination_edges": (
            ("effect_node_id", "fk_aob_term_edge_effect"),
            ("terminated_requirement_node_id", "fk_aob_term_edge_requirement"),
        ),
        "ad_v4_candidate_obligation_recurrence_group_members": (
            ("group_node_id", "fk_aob_member_group"),
            ("requirement_node_id", "fk_aob_member_requirement"),
        ),
    }
    for table, references in obligation_refs.items():
        for column, name in references:
            node_fk(table, column, name)

    op.create_foreign_key(
        "fk_aob_expr_app_projection",
        "ad_v4_candidate_obligation_expressions",
        "ad_v4_candidate_app_projections",
        ["app_target_projection_id", "proposal_id"], ["id", "proposal_id"],
        ondelete="RESTRICT",
    )
    op.create_foreign_key(
        "fk_aob_expr_app_node",
        "ad_v4_candidate_obligation_expressions",
        "ad_v4_candidate_app_semantic_nodes",
        ["app_target_node_id", "app_target_projection_id", "proposal_id"],
        ["id", "projection_id", "proposal_id"], ondelete="RESTRICT",
    )


def _create_event_table() -> None:
    op.create_table(
        "ad_v4_candidate_obligation_projection_events",
        _id("id", primary=True),
        sa.Column("identity_hash", sa.String(64), nullable=False, unique=True),
        _id("projection_id"), _id("proposal_id"), _id("app_projection_id"),
        sa.Column("sequence_number", sa.Integer(), nullable=False),
        sa.Column("event_type", sa.String(64), nullable=False),
        sa.Column("predecessor_event_hash", sa.String(64), nullable=True),
        sa.Column("proposal_canonical_hash", sa.String(64), nullable=False),
        sa.Column("evidence_binding_hash", sa.String(64), nullable=False),
        sa.Column("app_projection_hash", sa.String(64), nullable=False),
        sa.Column("obligation_subtree_hash", sa.String(64), nullable=False),
        sa.Column("projection_hash", sa.String(64), nullable=False),
        sa.Column("correction_binding_set_hash", sa.String(64), nullable=False),
        _id("causing_request_id"),
        sa.Column("cause_kind", sa.String(64), nullable=True),
        _id("cause_id", nullable=True),
        sa.Column("cause_hash", sa.String(64), nullable=True),
        sa.Column("canonical_bytes", sa.LargeBinary(), nullable=False),
        sa.Column("event_hash", sa.String(64), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(
            ["projection_id", "proposal_id"],
            ["ad_v4_candidate_obligation_projections.id", "ad_v4_candidate_obligation_projections.proposal_id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(["proposal_id"], ["ad_v4_candidate_proposals.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["app_projection_id", "proposal_id"],
            ["ad_v4_candidate_app_projections.id", "ad_v4_candidate_app_projections.proposal_id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(["causing_request_id"], ["ad_v4_candidate_obligation_materialization_requests.id"], ondelete="RESTRICT"),
        sa.CheckConstraint("sequence_number BETWEEN 0 AND 2147483647", name="ck_ad_v4_obligation_event_sequence"),
        sa.CheckConstraint("event_type IN ('materialized','evidence_invalidated','parent_app_stale','candidate_corrected','candidate_replaced')", name="ck_ad_v4_obligation_event_type"),
        sa.CheckConstraint("(event_type='materialized' AND sequence_number=0 AND predecessor_event_hash IS NULL AND cause_kind IS NULL AND cause_id IS NULL AND cause_hash IS NULL) OR (event_type<>'materialized' AND sequence_number>0 AND predecessor_event_hash IS NOT NULL AND cause_kind IS NOT NULL AND cause_id IS NOT NULL AND cause_hash IS NOT NULL)", name="ck_ad_v4_obligation_event_union"),
        sa.UniqueConstraint("projection_id", "sequence_number", name="uq_ad_v4_obligation_event_sequence"),
        sa.UniqueConstraint("projection_id", "event_hash", name="uq_ad_v4_obligation_event_hash"),
    )
    op.create_index(
        "uq_ad_v4_obligation_event_cause",
        "ad_v4_candidate_obligation_projection_events",
        ["projection_id", "cause_kind", "cause_id"], unique=True,
        postgresql_where=sa.text("cause_id IS NOT NULL"),
    )


def _expand_correction_bindings() -> None:
    op.execute("LOCK TABLE ad_v4_candidate_correction_semantic_bindings IN SHARE ROW EXCLUSIVE MODE")
    bind = op.get_bind()
    invalid = bind.execute(sa.text("""
        SELECT 1 FROM ad_v4_candidate_correction_semantic_bindings
         WHERE binding_slice<>'slice_3a' OR projection_id IS NULL
            OR semantic_node_id IS NULL OR generation<>1 LIMIT 1
    """)).first()
    if invalid is not None:
        raise RuntimeError("Revision 0028 requires valid immutable Slice-3A correction bindings")
    op.add_column("ad_v4_candidate_correction_semantic_bindings", sa.Column("obligation_projection_id", sa.String(36), nullable=True))
    op.add_column("ad_v4_candidate_correction_semantic_bindings", sa.Column("obligation_semantic_node_id", sa.String(36), nullable=True))
    op.alter_column("ad_v4_candidate_correction_semantic_bindings", "projection_id", nullable=True)
    op.alter_column("ad_v4_candidate_correction_semantic_bindings", "semantic_node_id", nullable=True)
    op.create_foreign_key(
        "fk_ad_v4_correction_binding_obligation_projection",
        "ad_v4_candidate_correction_semantic_bindings",
        "ad_v4_candidate_obligation_projections",
        ["obligation_projection_id", "proposal_id"], ["id", "proposal_id"],
        ondelete="RESTRICT",
    )
    op.create_foreign_key(
        "fk_ad_v4_correction_binding_obligation_node",
        "ad_v4_candidate_correction_semantic_bindings",
        "ad_v4_candidate_obligation_semantic_nodes",
        ["obligation_semantic_node_id", "obligation_projection_id", "proposal_id"],
        ["id", "projection_id", "proposal_id"], ondelete="RESTRICT",
    )
    op.create_check_constraint(
        "ck_ad_v4_correction_binding_owner_slice",
        "ad_v4_candidate_correction_semantic_bindings",
        "(binding_slice='slice_3a' AND projection_id IS NOT NULL AND semantic_node_id IS NOT NULL AND obligation_projection_id IS NULL AND obligation_semantic_node_id IS NULL) OR "
        "(binding_slice='slice_3b' AND projection_id IS NULL AND semantic_node_id IS NULL AND obligation_projection_id IS NOT NULL AND obligation_semantic_node_id IS NOT NULL)",
    )
    op.execute("DROP TRIGGER IF EXISTS trg_ad_v4_candidate_correction_semantic_bindings_mark_dirty ON ad_v4_candidate_correction_semantic_bindings")
    op.execute("DROP TRIGGER IF EXISTS trg_ad_v4_candidate_correction_semantic_bindings_complete ON ad_v4_candidate_correction_semantic_bindings")
    op.execute("""
        CREATE TRIGGER trg_ad_v4_correction_binding_slice3a_insert_dirty
        BEFORE INSERT ON ad_v4_candidate_correction_semantic_bindings
        FOR EACH ROW WHEN (NEW.binding_slice='slice_3a')
        EXECUTE FUNCTION paprnav_v4_candidate_app_mark_dirty()
    """)
    op.execute("""
        CREATE CONSTRAINT TRIGGER trg_ad_v4_correction_binding_slice3a_insert_complete
        AFTER INSERT ON ad_v4_candidate_correction_semantic_bindings
        DEFERRABLE INITIALLY DEFERRED FOR EACH ROW WHEN (NEW.binding_slice='slice_3a')
        EXECUTE FUNCTION paprnav_v4_candidate_app_complete_trigger()
    """)
    op.execute("""
        CREATE TRIGGER trg_ad_v4_correction_binding_slice3a_update_dirty
        BEFORE UPDATE ON ad_v4_candidate_correction_semantic_bindings
        FOR EACH ROW WHEN (OLD.binding_slice='slice_3a' OR NEW.binding_slice='slice_3a')
        EXECUTE FUNCTION paprnav_v4_candidate_app_mark_dirty()
    """)
    op.execute("""
        CREATE CONSTRAINT TRIGGER trg_ad_v4_correction_binding_slice3a_update_complete
        AFTER UPDATE ON ad_v4_candidate_correction_semantic_bindings
        DEFERRABLE INITIALLY DEFERRED FOR EACH ROW
        WHEN (OLD.binding_slice='slice_3a' OR NEW.binding_slice='slice_3a')
        EXECUTE FUNCTION paprnav_v4_candidate_app_complete_trigger()
    """)
    op.execute("""
        CREATE TRIGGER trg_ad_v4_correction_binding_slice3a_delete_dirty
        BEFORE DELETE ON ad_v4_candidate_correction_semantic_bindings
        FOR EACH ROW WHEN (OLD.binding_slice='slice_3a')
        EXECUTE FUNCTION paprnav_v4_candidate_app_mark_dirty()
    """)
    op.execute("""
        CREATE CONSTRAINT TRIGGER trg_ad_v4_correction_binding_slice3a_delete_complete
        AFTER DELETE ON ad_v4_candidate_correction_semantic_bindings
        DEFERRABLE INITIALLY DEFERRED FOR EACH ROW WHEN (OLD.binding_slice='slice_3a')
        EXECUTE FUNCTION paprnav_v4_candidate_app_complete_trigger()
    """)


def _install_obligation_integrity() -> None:
    with op.get_bind().connection.driver_connection.cursor() as cursor:
        cursor.execute(INTEGRITY_SQL_PATH.read_text(encoding="utf-8"))
    for ordinal, table in enumerate(OBLIGATION_TABLES):
        op.execute(
            f"CREATE TRIGGER trg_aob_{ordinal}_immutable BEFORE UPDATE OR DELETE "
            f"ON {table} FOR EACH ROW EXECUTE FUNCTION "
            "paprnav_v4_reject_obligation_mutation()"
        )
        op.execute(
            f"CREATE TRIGGER trg_aob_{ordinal}_dirty BEFORE INSERT OR UPDATE OR DELETE "
            f"ON {table} FOR EACH ROW EXECUTE FUNCTION "
            "paprnav_v4_candidate_obligation_mark_dirty()"
        )
        op.execute(
            f"CREATE CONSTRAINT TRIGGER trg_aob_{ordinal}_complete "
            f"AFTER INSERT OR UPDATE OR DELETE ON {table} "
            "DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION "
            "paprnav_v4_candidate_obligation_complete_trigger()"
        )
    op.execute("""
        CREATE TRIGGER trg_aob_correction_insert_dirty
        BEFORE INSERT ON ad_v4_candidate_correction_semantic_bindings
        FOR EACH ROW WHEN (NEW.binding_slice='slice_3b')
        EXECUTE FUNCTION paprnav_v4_candidate_obligation_mark_dirty()
    """)
    op.execute("""
        CREATE CONSTRAINT TRIGGER trg_aob_correction_insert_complete
        AFTER INSERT ON ad_v4_candidate_correction_semantic_bindings
        DEFERRABLE INITIALLY DEFERRED FOR EACH ROW WHEN (NEW.binding_slice='slice_3b')
        EXECUTE FUNCTION paprnav_v4_candidate_obligation_complete_trigger()
    """)
    op.execute("""
        CREATE TRIGGER trg_aob_correction_update_dirty
        BEFORE UPDATE ON ad_v4_candidate_correction_semantic_bindings
        FOR EACH ROW WHEN (OLD.binding_slice='slice_3b' OR NEW.binding_slice='slice_3b')
        EXECUTE FUNCTION paprnav_v4_candidate_obligation_mark_dirty()
    """)
    op.execute("""
        CREATE CONSTRAINT TRIGGER trg_aob_correction_update_complete
        AFTER UPDATE ON ad_v4_candidate_correction_semantic_bindings
        DEFERRABLE INITIALLY DEFERRED FOR EACH ROW
        WHEN (OLD.binding_slice='slice_3b' OR NEW.binding_slice='slice_3b')
        EXECUTE FUNCTION paprnav_v4_candidate_obligation_complete_trigger()
    """)
    op.execute("""
        CREATE TRIGGER trg_aob_correction_delete_dirty
        BEFORE DELETE ON ad_v4_candidate_correction_semantic_bindings
        FOR EACH ROW WHEN (OLD.binding_slice='slice_3b')
        EXECUTE FUNCTION paprnav_v4_candidate_obligation_mark_dirty()
    """)
    op.execute("""
        CREATE CONSTRAINT TRIGGER trg_aob_correction_delete_complete
        AFTER DELETE ON ad_v4_candidate_correction_semantic_bindings
        DEFERRABLE INITIALLY DEFERRED FOR EACH ROW WHEN (OLD.binding_slice='slice_3b')
        EXECUTE FUNCTION paprnav_v4_candidate_obligation_complete_trigger()
    """)


def upgrade() -> None:
    op.drop_constraint("ck_ad_v4_feature_gate_key", "ad_v4_feature_gates", type_="check")
    op.create_check_constraint(
        "ck_ad_v4_feature_gate_key", "ad_v4_feature_gates",
        "gate_key IN ('validator2_write_enabled','materializer3a_enabled','materializer3b_enabled')",
    )
    op.execute("INSERT INTO ad_v4_feature_gates(gate_key,enabled) VALUES ('materializer3b_enabled',false)")
    op.execute("""
        CREATE OR REPLACE FUNCTION paprnav_v4_capabilities() RETURNS jsonb AS $$
          SELECT jsonb_build_object(
            'revision','20260911_0028',
            'validatorPairs',jsonb_build_array(
              jsonb_build_array('paprnav-ad-v4-validator-1','paprnav-ad-v4-c14n-1'),
              jsonb_build_array('paprnav-ad-v4-validator-2','paprnav-ad-v4-c14n-2')),
            'materializers',jsonb_build_array(
              'paprnav-ad-v4-app-materializer-2',
              'paprnav-ad-v4-obligation-materializer-1'),
            'validator2_write_enabled',(SELECT enabled FROM ad_v4_feature_gates WHERE gate_key='validator2_write_enabled'),
            'materializer3a_enabled',(SELECT enabled FROM ad_v4_feature_gates WHERE gate_key='materializer3a_enabled'),
            'materializer3b_enabled',(SELECT enabled FROM ad_v4_feature_gates WHERE gate_key='materializer3b_enabled'));
        $$ LANGUAGE sql STABLE
    """)
    op.execute("""
        CREATE OR REPLACE FUNCTION paprnav_set_v4_feature_gate(
          p_key text,p_enabled boolean,p_actor text
        ) RETURNS void AS $$
        BEGIN
          IF p_key NOT IN (
            'validator2_write_enabled','materializer3a_enabled','materializer3b_enabled'
          ) OR length(trim(p_actor))=0 THEN
            RAISE EXCEPTION 'invalid V4 feature gate change';
          END IF;
          UPDATE ad_v4_feature_gates
             SET enabled=p_enabled,changed_at=now(),changed_by=p_actor
           WHERE gate_key=p_key;
          IF NOT FOUND THEN RAISE EXCEPTION 'unknown V4 feature gate'; END IF;
        END; $$ LANGUAGE plpgsql
    """)
    _create_projection_root()
    _create_request_and_generic_tables()
    _create_owner_tables()
    _create_relationship_tables()
    _install_same_projection_references()
    _create_event_table()
    for ordinal, table in enumerate((
        "ad_v4_candidate_obligation_materialization_requests",
        "ad_v4_candidate_obligation_evidence_links",
        "ad_v4_candidate_obligation_action_steps",
        "ad_v4_candidate_obligation_action_document_refs",
        "ad_v4_candidate_obligation_expression_edges",
        "ad_v4_candidate_obligation_requirement_dependencies",
        "ad_v4_candidate_obligation_timing_terms",
        "ad_v4_candidate_obligation_termination_edges",
        "ad_v4_candidate_obligation_recurrence_group_members",
    )):
        op.create_index(
            f"ix_aob_projection_{ordinal}", table, ["projection_id"],
        )
    _expand_correction_bindings()
    with op.get_bind().connection.driver_connection.cursor() as cursor:
        cursor.execute(SQL_PATH.read_text(encoding="utf-8"))
    _install_obligation_integrity()
    _set_app_validator_slice3b_compatibility(enabled=True)


def downgrade() -> None:
    op.execute("SET LOCAL lock_timeout='5s'")
    op.execute(
        "LOCK TABLE " + ",".join(DOWNGRADE_LOCK_TABLES)
        + " IN ACCESS EXCLUSIVE MODE"
    )
    bind = op.get_bind()
    if bind.execute(sa.text("SELECT enabled FROM ad_v4_feature_gates WHERE gate_key='materializer3b_enabled'")).scalar_one():
        raise RuntimeError("Revision 0028 materializer3b gate is enabled")
    if bind.execute(sa.text("SELECT 1 FROM ad_v4_candidate_correction_semantic_bindings WHERE binding_slice='slice_3b' LIMIT 1")).first() is not None:
        raise RuntimeError("Revision 0028 contains immutable Slice-3B correction bindings")
    for table in OBLIGATION_TABLES:
        if bind.execute(sa.text(f"SELECT 1 FROM {table} LIMIT 1")).first() is not None:
            raise RuntimeError("Revision 0028 contains immutable Slice-3B rows")

    _set_app_validator_slice3b_compatibility(enabled=False)

    op.execute("DROP TRIGGER IF EXISTS trg_ad_v4_correction_binding_slice3a_insert_complete ON ad_v4_candidate_correction_semantic_bindings")
    op.execute("DROP TRIGGER IF EXISTS trg_ad_v4_correction_binding_slice3a_insert_dirty ON ad_v4_candidate_correction_semantic_bindings")
    op.execute("DROP TRIGGER IF EXISTS trg_ad_v4_correction_binding_slice3a_update_complete ON ad_v4_candidate_correction_semantic_bindings")
    op.execute("DROP TRIGGER IF EXISTS trg_ad_v4_correction_binding_slice3a_update_dirty ON ad_v4_candidate_correction_semantic_bindings")
    op.execute("DROP TRIGGER IF EXISTS trg_ad_v4_correction_binding_slice3a_delete_complete ON ad_v4_candidate_correction_semantic_bindings")
    op.execute("DROP TRIGGER IF EXISTS trg_ad_v4_correction_binding_slice3a_delete_dirty ON ad_v4_candidate_correction_semantic_bindings")
    op.execute("DROP TRIGGER IF EXISTS trg_aob_correction_insert_complete ON ad_v4_candidate_correction_semantic_bindings")
    op.execute("DROP TRIGGER IF EXISTS trg_aob_correction_insert_dirty ON ad_v4_candidate_correction_semantic_bindings")
    op.execute("DROP TRIGGER IF EXISTS trg_aob_correction_update_complete ON ad_v4_candidate_correction_semantic_bindings")
    op.execute("DROP TRIGGER IF EXISTS trg_aob_correction_update_dirty ON ad_v4_candidate_correction_semantic_bindings")
    op.execute("DROP TRIGGER IF EXISTS trg_aob_correction_delete_complete ON ad_v4_candidate_correction_semantic_bindings")
    op.execute("DROP TRIGGER IF EXISTS trg_aob_correction_delete_dirty ON ad_v4_candidate_correction_semantic_bindings")
    for ordinal, table in enumerate(OBLIGATION_TABLES):
        op.execute(f"DROP TRIGGER IF EXISTS trg_aob_{ordinal}_complete ON {table}")
        op.execute(f"DROP TRIGGER IF EXISTS trg_aob_{ordinal}_dirty ON {table}")
        op.execute(f"DROP TRIGGER IF EXISTS trg_aob_{ordinal}_immutable ON {table}")
    op.execute(
        "DROP TRIGGER IF EXISTS trg_aob_request_insert_guard ON "
        "ad_v4_candidate_obligation_materialization_requests"
    )
    op.drop_constraint("ck_ad_v4_correction_binding_owner_slice", "ad_v4_candidate_correction_semantic_bindings", type_="check")
    op.drop_constraint("fk_ad_v4_correction_binding_obligation_node", "ad_v4_candidate_correction_semantic_bindings", type_="foreignkey")
    op.drop_constraint("fk_ad_v4_correction_binding_obligation_projection", "ad_v4_candidate_correction_semantic_bindings", type_="foreignkey")
    op.alter_column("ad_v4_candidate_correction_semantic_bindings", "semantic_node_id", nullable=False)
    op.alter_column("ad_v4_candidate_correction_semantic_bindings", "projection_id", nullable=False)
    op.drop_column("ad_v4_candidate_correction_semantic_bindings", "obligation_semantic_node_id")
    op.drop_column("ad_v4_candidate_correction_semantic_bindings", "obligation_projection_id")
    op.execute("""
        CREATE TRIGGER trg_ad_v4_candidate_correction_semantic_bindings_mark_dirty
        BEFORE INSERT OR UPDATE OR DELETE ON ad_v4_candidate_correction_semantic_bindings
        FOR EACH ROW EXECUTE FUNCTION paprnav_v4_candidate_app_mark_dirty()
    """)
    op.execute("""
        CREATE CONSTRAINT TRIGGER trg_ad_v4_candidate_correction_semantic_bindings_complete
        AFTER INSERT OR UPDATE OR DELETE ON ad_v4_candidate_correction_semantic_bindings
        DEFERRABLE INITIALLY DEFERRED FOR EACH ROW
        EXECUTE FUNCTION paprnav_v4_candidate_app_complete_trigger()
    """)
    op.execute("DROP FUNCTION IF EXISTS paprnav_v4_obligation_select_occurrences(jsonb)")
    op.execute("DROP FUNCTION IF EXISTS paprnav_v4_obligation_record(jsonb)")
    op.execute("DROP FUNCTION IF EXISTS paprnav_v4_obligation_record_at(jsonb,integer)")
    op.execute("DROP FUNCTION IF EXISTS paprnav_v4_obligation_utf16_sort_key(text)")
    op.execute("DROP FUNCTION IF EXISTS paprnav_v4_obligation_mapping_manifest()")
    op.execute("DROP FUNCTION IF EXISTS paprnav_v4_obligation_mapping_digest()")
    op.execute("DROP FUNCTION IF EXISTS paprnav_v4_reject_obligation_mutation()")
    op.execute("DROP FUNCTION IF EXISTS paprnav_v4_candidate_obligation_complete_trigger()")
    op.execute("DROP FUNCTION IF EXISTS paprnav_v4_candidate_obligation_mark_dirty()")
    op.execute("DROP FUNCTION IF EXISTS paprnav_v4_candidate_obligation_request_guard()")
    op.execute("DROP FUNCTION IF EXISTS paprnav_v4_lock_key(text)")
    op.execute("DROP FUNCTION IF EXISTS paprnav_v4_candidate_obligation_require_complete(text)")
    op.execute("DROP FUNCTION IF EXISTS paprnav_v4_obligation_semantic_expected(jsonb,text)")
    op.execute("DROP FUNCTION IF EXISTS paprnav_v4_obligation_datum_json(text,text)")
    op.execute("DROP FUNCTION IF EXISTS paprnav_v4_candidate_obligation_typed_subtree(text)")
    op.execute("DROP FUNCTION IF EXISTS paprnav_v4_obligation_recurrence_json(text,text)")
    op.execute("DROP FUNCTION IF EXISTS paprnav_v4_obligation_branch_json(text,text)")
    op.execute("DROP FUNCTION IF EXISTS paprnav_v4_obligation_action_json(text,text)")
    op.execute("DROP FUNCTION IF EXISTS paprnav_v4_obligation_timing_json(text,text)")
    op.execute("DROP FUNCTION IF EXISTS paprnav_v4_obligation_expression_json(text,text)")
    op.execute("DROP FUNCTION IF EXISTS paprnav_v4_obligation_assertion_json(text,text)")
    op.execute("DROP FUNCTION IF EXISTS paprnav_v4_obligation_evidence_json(text,text)")
    for table in reversed(OBLIGATION_TABLES):
        op.drop_table(table)
    op.execute("DELETE FROM ad_v4_feature_gates WHERE gate_key='materializer3b_enabled'")
    op.drop_constraint("ck_ad_v4_feature_gate_key", "ad_v4_feature_gates", type_="check")
    op.create_check_constraint(
        "ck_ad_v4_feature_gate_key", "ad_v4_feature_gates",
        "gate_key IN ('validator2_write_enabled','materializer3a_enabled')",
    )
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
        CREATE OR REPLACE FUNCTION paprnav_set_v4_feature_gate(
          p_key text,p_enabled boolean,p_actor text
        ) RETURNS void AS $$
        BEGIN
          IF p_key NOT IN ('validator2_write_enabled','materializer3a_enabled')
             OR length(trim(p_actor))=0 THEN
            RAISE EXCEPTION 'invalid V4 feature gate change';
          END IF;
          UPDATE ad_v4_feature_gates
             SET enabled=p_enabled,changed_at=now(),changed_by=p_actor
           WHERE gate_key=p_key;
          IF NOT FOUND THEN RAISE EXCEPTION 'unknown V4 feature gate'; END IF;
        END; $$ LANGUAGE plpgsql
    """)
