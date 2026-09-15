"""Immutable V4 review cases through graph-free rejection.

Revision ID: 20260913_0029
Revises: 20260911_0028
"""
from pathlib import Path

from alembic import op
import sqlalchemy as sa

revision = "20260913_0029"
down_revision = "20260911_0028"
branch_labels = None
depends_on = None

TABLES = ("ad_v4_review_cases", "ad_v4_review_draft_revisions", "ad_v4_review_requests", "ad_v4_review_rejections", "ad_v4_signoff_events", "ad_v4_review_case_events")
GATES = ("validator2_write_enabled", "materializer3a_enabled", "materializer3b_enabled", "reviewer4_draft_enabled", "reviewer4_decision_enabled")
SQL_PATH = Path(__file__).resolve().parents[1] / "sql/20260913_0029_review_case_integrity.sql"
MAX_CASES_PER_PROPOSAL = 100
MAX_DRAFT_REVISIONS_PER_CASE = 1000
MAX_EVENTS_PER_CASE = 1003


def _column(name: str, kind: str = "id", nullable: bool = False) -> sa.Column:
    types = {"id": sa.String(36), "hash": sa.String(64), "bytes": sa.LargeBinary(), "time": sa.DateTime(timezone=True), "int": sa.Integer(), "str": sa.String(32), "version": sa.String(64), "action": sa.String(96), "key": sa.String(255)}
    return sa.Column(name, types[kind], nullable=nullable, primary_key=name == "id")


def _create_tables() -> None:
    specs = (
        "proposal_canonical_hash:hash case_sequence:int predecessor_case_id:id? row_hash:hash created_at:time",
        "case_id:id revision_number:int predecessor_draft_id:id? expected_predecessor_event_hash:hash annotation_bytes:bytes annotation_hash:hash intended_action:str row_hash:hash created_at:time",
        "case_id:id draft_revision_id:id? expected_predecessor_event_hash:hash cutoff_bytes:bytes cutoff_hash:hash authorship_set_bytes:bytes authorship_set_hash:hash authorship_source_count:int row_hash:hash requested_at:time",
        "case_id:id request_id:id proposal_canonical_hash:hash requested_input_identity_hash:hash requested_observation_hash:hash decision_input_identity_bytes:bytes decision_input_identity_hash:hash decision_observation_bytes:bytes decision_observation_hash:hash decision_observed_at:time reasons_bytes:bytes reasons_hash:hash expected_predecessor_event_hash:hash row_hash:hash rejected_at:time",
        "case_id:id request_id:id rejection_id:id action:str rejection_hash:hash requested_input_identity_hash:hash requested_observation_hash:hash decision_input_identity_hash:hash decision_observation_hash:hash authorization_observation_hash:hash signature_hash:hash row_hash:hash signed_at:time",
        "case_id:id sequence_number:int predecessor_event_hash:hash? event_type:str resulting_state:str draft_revision_id:id? review_request_id:id? rejection_id:id? signoff_id:id? event_hash:hash occurred_at:time",
    )
    common = "id:id proposal_id:id directive_id:id actor_user_id:id authorizing_membership_id:id organization_id:id auth_snapshot_bytes:bytes auth_snapshot_hash:hash auth_policy_version:version endpoint_action:action idempotency_key:key request_canonical_bytes:bytes request_hash:hash contract_version:version canonical_bytes:bytes"
    observation = "input_identity_bytes:bytes input_identity_hash:hash observation_bytes:bytes observation_hash:hash observed_at:time"
    for ordinal, (table, spec) in enumerate(zip(TABLES, specs)):
        fields = (common + " " + spec + (" " + observation if ordinal < 3 else "")).split()
        columns = []
        for field in fields:
            name, kind = field.split(":")
            columns.append(_column(name, kind.rstrip("?"), kind.endswith("?")))
        constraints = [sa.UniqueConstraint("id", "proposal_id", "directive_id", name=f"uq_ar4_{ordinal}_identity"), sa.CheckConstraint("contract_version='paprnav-ad-v4-candidate-review-1'", name=f"ck_ar4_{ordinal}_version")]
        for local, target in (("proposal_id", "ad_v4_candidate_proposals.id"), ("directive_id", "airworthiness_directives.id"), ("actor_user_id", "users.id"), ("authorizing_membership_id", "organization_memberships.id"), ("organization_id", "organizations.id")):
            constraints.append(sa.ForeignKeyConstraint([local], [target], ondelete="RESTRICT"))
        for column in columns:
            if column.name.endswith("_hash"):
                constraints.append(sa.CheckConstraint(f"length({column.name})=64", name=f"ck_ar4_{ordinal}_{column.name}"))
            elif column.name.endswith("_bytes"):
                constraints.append(sa.CheckConstraint(f"length({column.name}) BETWEEN 2 AND 1048576", name=f"ck_ar4_{ordinal}_{column.name}"))
        if ordinal:
            constraints.append(sa.UniqueConstraint("id", "case_id", name=f"uq_ar4_{ordinal}_case_identity"))
        op.create_table(table, *columns, *constraints)

    def check(ordinal, name, expression):
        op.create_check_constraint(name, TABLES[ordinal], expression)

    def unique(ordinal, name, fields):
        op.create_unique_constraint(name, TABLES[ordinal], fields)

    def foreign(ordinal, name, fields, target, remote):
        op.create_foreign_key(name, TABLES[ordinal], TABLES[target], fields, remote, ondelete="RESTRICT", deferrable=True, initially="DEFERRED")

    for ordinal in range(1, 6):
        foreign(ordinal, f"fk_ar4_{ordinal}_case", ["case_id", "proposal_id", "directive_id"], 0, ["id", "proposal_id", "directive_id"])
    unique(0, "uq_ar4_case_sequence", ["proposal_id", "case_sequence"])
    check(0, "ck_ar4_case_capacity", f"case_sequence BETWEEN 0 AND {MAX_CASES_PER_PROPOSAL - 1}")
    op.create_index("ix_ar4_case_queue", TABLES[0], ["created_at", "id"])
    op.create_index("ix_ar4_case_directive", TABLES[0], ["directive_id", "created_at", "id"])
    check(0, "ck_ar4_case_predecessor", "(case_sequence=0 AND predecessor_case_id IS NULL) OR (case_sequence>0 AND predecessor_case_id IS NOT NULL)")
    foreign(0, "fk_ar4_case_predecessor", ["predecessor_case_id", "proposal_id", "directive_id"], 0, ["id", "proposal_id", "directive_id"])
    unique(1, "uq_ar4_draft_revision", ["case_id", "revision_number"])
    check(1, "ck_ar4_draft_capacity", f"revision_number BETWEEN 0 AND {MAX_DRAFT_REVISIONS_PER_CASE - 1}")
    check(1, "ck_ar4_draft_predecessor", "(revision_number=0 AND predecessor_draft_id IS NULL) OR (revision_number>0 AND predecessor_draft_id IS NOT NULL)")
    check(1, "ck_ar4_draft_intent", "intended_action IN ('undecided','reject')")
    for ordinal in (2, 3, 4):
        unique(ordinal, f"uq_ar4_{ordinal}_one_per_case", ["case_id"])
    check(2, "ck_ar4_request_authorship_count", "authorship_source_count>=0")
    unique(3, "uq_ar4_rejection_request", ["request_id"])
    unique(4, "uq_ar4_signoff_rejection", ["rejection_id"])
    check(4, "ck_ar4_signoff_action", "action='reject'")
    for ordinal, column, target in ((1, "predecessor_draft_id", 1), (2, "draft_revision_id", 1), (3, "request_id", 2), (4, "request_id", 2), (4, "rejection_id", 3), (5, "draft_revision_id", 1), (5, "review_request_id", 2), (5, "rejection_id", 3), (5, "signoff_id", 4)):
        foreign(ordinal, f"fk_ar4_{ordinal}_{column}", [column, "case_id"], target, ["id", "case_id"])
    unique(5, "uq_ar4_event_sequence", ["case_id", "sequence_number"])
    check(5, "ck_ar4_event_capacity", f"sequence_number BETWEEN 0 AND {MAX_EVENTS_PER_CASE - 1}")
    unique(5, "uq_ar4_event_hash", ["case_id", "event_hash"])
    unique(5, "uq_ar4_event_predecessor", ["case_id", "predecessor_event_hash"])
    unique(5, "uq_ar4_event_idempotency", ["actor_user_id", "authorizing_membership_id", "endpoint_action", "auth_policy_version", "idempotency_key"])
    check(5, "ck_ar4_event_predecessor", "(sequence_number=0 AND predecessor_event_hash IS NULL AND event_type='case_created') OR (sequence_number>0 AND predecessor_event_hash IS NOT NULL AND event_type<>'case_created')")
    check(5, "ck_ar4_event_union", "(event_type='case_created' AND resulting_state='draft' AND draft_revision_id IS NULL AND review_request_id IS NULL AND rejection_id IS NULL AND signoff_id IS NULL) OR (event_type='draft_saved' AND resulting_state='draft' AND draft_revision_id IS NOT NULL AND review_request_id IS NULL AND rejection_id IS NULL AND signoff_id IS NULL) OR (event_type='review_requested' AND resulting_state='pending_review' AND draft_revision_id IS NULL AND review_request_id IS NOT NULL AND rejection_id IS NULL AND signoff_id IS NULL) OR (event_type='review_rejected' AND resulting_state='rejected' AND draft_revision_id IS NULL AND review_request_id IS NOT NULL AND rejection_id IS NOT NULL AND signoff_id IS NOT NULL)")
    op.create_index("uq_ar4_terminal", TABLES[5], ["case_id"], unique=True, postgresql_where=sa.text("event_type='review_rejected'"))


def _capabilities(enabled: bool) -> None:
    gates = GATES if enabled else GATES[:3]
    revision_value = revision if enabled else down_revision
    gate_sql = ",".join("'" + gate + "'" for gate in gates)
    op.drop_constraint("ck_ad_v4_feature_gate_key", "ad_v4_feature_gates", type_="check")
    op.create_check_constraint("ck_ad_v4_feature_gate_key", "ad_v4_feature_gates", f"gate_key IN ({gate_sql})")
    op.execute(f"""CREATE OR REPLACE FUNCTION paprnav_v4_capabilities() RETURNS jsonb AS $$
      SELECT jsonb_build_object('revision','{revision_value}',
        'validatorPairs',jsonb_build_array(jsonb_build_array('paprnav-ad-v4-validator-1','paprnav-ad-v4-c14n-1'),jsonb_build_array('paprnav-ad-v4-validator-2','paprnav-ad-v4-c14n-2')),
        'materializers',jsonb_build_array('paprnav-ad-v4-app-materializer-2','paprnav-ad-v4-obligation-materializer-1'))
        || (SELECT jsonb_object_agg(gate_key,enabled) FROM ad_v4_feature_gates WHERE gate_key IN ({gate_sql}));
      $$ LANGUAGE sql STABLE""")
    op.execute(f"""CREATE OR REPLACE FUNCTION paprnav_set_v4_feature_gate(p_key text,p_enabled boolean,p_actor text) RETURNS void AS $$
      BEGIN
        IF p_key IS NULL OR p_key NOT IN ({gate_sql}) OR p_enabled IS NULL OR p_actor IS NULL OR length(trim(p_actor))=0 THEN RAISE EXCEPTION 'invalid V4 feature gate change'; END IF;
        PERFORM gate_key FROM ad_v4_feature_gates WHERE gate_key IN ({gate_sql}) ORDER BY CASE gate_key WHEN 'validator2_write_enabled' THEN 1 WHEN 'materializer3a_enabled' THEN 2 WHEN 'materializer3b_enabled' THEN 3 WHEN 'reviewer4_draft_enabled' THEN 4 ELSE 5 END FOR UPDATE;
        UPDATE ad_v4_feature_gates SET enabled=p_enabled,changed_at=now(),changed_by=p_actor WHERE gate_key=p_key;
        IF NOT FOUND THEN RAISE EXCEPTION 'unknown V4 feature gate'; END IF;
      END; $$ LANGUAGE plpgsql""")


def _candidate_audit_lock_order(*, user_first: bool) -> None:
    # Preserve the frozen 0028 validator bodies exactly except for these two
    # adjacent locks. Fail migration on unexpected upstream definition drift.
    for function, mode in (("paprnav_v4_validate_submission", "UPDATE"), ("paprnav_v4_validate_app_request", "SHARE")):
        definition = op.get_bind().execute(sa.text(f"SELECT pg_get_functiondef('{function}()'::regprocedure)")).scalar_one()
        member = f"      SELECT * INTO m FROM organization_memberships WHERE id=NEW.authorizing_membership_id FOR {mode};\n"
        user = f"      SELECT * INTO u FROM users WHERE id=NEW.actor_user_id FOR {mode};\n"
        before, after = (member + user, user + member) if user_first else (user + member, member + user)
        if definition.count(before) != 1:
            raise RuntimeError(f"Revision 0029 cannot reorder {function}: frozen definition drifted")
        with op.get_bind().connection.driver_connection.cursor() as cursor:
            cursor.execute(definition.replace(before, after, 1))


def upgrade() -> None:
    _candidate_audit_lock_order(user_first=True)
    _capabilities(True)
    op.execute("INSERT INTO ad_v4_feature_gates(gate_key,enabled) VALUES ('reviewer4_draft_enabled',false),('reviewer4_decision_enabled',false)")
    _create_tables()
    # The 0028 commit validator also requires its writer gates to be enabled.
    # Review is permitted while materialization is disabled, so freeze an
    # otherwise identical verifier under a new name. Never weaken the writer.
    definition = op.get_bind().execute(sa.text("SELECT pg_get_functiondef('paprnav_v4_candidate_obligation_require_complete(text)'::regprocedure)")).scalar_one()
    gate_clause = """     OR (SELECT count(*) FROM ad_v4_feature_gates
          WHERE gate_key IN (
            'validator2_write_enabled','materializer3a_enabled','materializer3b_enabled')
            AND enabled)<>3
"""
    if definition.count(gate_clause) != 1:
        raise RuntimeError("Revision 0029 cannot freeze review verifier: 0028 definition drifted")
    definition = definition.replace("paprnav_v4_candidate_obligation_require_complete", "paprnav_v4_review_verify_obligation", 1).replace(gate_clause, "")
    with op.get_bind().connection.driver_connection.cursor() as cursor:
        cursor.execute(definition)
    with op.get_bind().connection.driver_connection.cursor() as cursor:
        cursor.execute(SQL_PATH.read_text(encoding="utf-8"))
    for ordinal, table in enumerate(TABLES):
        op.execute(f"CREATE TRIGGER trg_ar4_{ordinal}_immutable BEFORE UPDATE OR DELETE ON {table} FOR EACH ROW EXECUTE FUNCTION paprnav_v4_reject_mutation()")
        op.execute(f"CREATE TRIGGER trg_ar4_{ordinal}_guard BEFORE INSERT ON {table} FOR EACH ROW EXECUTE FUNCTION paprnav_v4_review_insert_guard()")
        op.execute(f"CREATE CONSTRAINT TRIGGER trg_ar4_{ordinal}_complete AFTER INSERT ON {table} DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION paprnav_v4_review_complete_trigger()")


def downgrade() -> None:
    op.execute("SET LOCAL lock_timeout='5s'")
    op.execute("LOCK TABLE " + ",".join((*TABLES, "ad_v4_feature_gates")) + " IN ACCESS EXCLUSIVE MODE")
    bind = op.get_bind()
    if bind.execute(sa.text("SELECT 1 FROM ad_v4_feature_gates WHERE gate_key IN ('reviewer4_draft_enabled','reviewer4_decision_enabled') AND enabled LIMIT 1")).first():
        raise RuntimeError("Revision 0029 reviewer gates are enabled")
    for table in TABLES:
        if bind.execute(sa.text(f"SELECT 1 FROM {table} LIMIT 1")).first():
            raise RuntimeError("Revision 0029 contains immutable review history")
    for ordinal, table in reversed(tuple(enumerate(TABLES))):
        for suffix in ("immutable", "guard", "complete"):
            op.execute(f"DROP TRIGGER trg_ar4_{ordinal}_{suffix} ON {table}")
    for table in TABLES:
        for constraint in sa.inspect(bind).get_foreign_keys(table):
            if constraint["referred_table"] in TABLES:
                op.drop_constraint(constraint["name"], table, type_="foreignkey")
    for function, args in (("paprnav_v4_review_complete_trigger", ""), ("paprnav_v4_review_require_complete", "text"), ("paprnav_v4_review_case_authoritative_bytes", "text"), ("paprnav_v4_review_insert_guard", ""), ("paprnav_v4_review_validate_auth", "jsonb"), ("paprnav_v4_review_validate_observation", "bytea,text,bytea,text,timestamp with time zone,text,text"), ("paprnav_v4_review_verify_obligation", "text"), ("paprnav_v4_review_authors", "text"), ("paprnav_v4_review_cutoff", "text"), ("paprnav_v4_review_hash", "text,bytea")):
        op.execute(f"DROP FUNCTION IF EXISTS {function}({args})")
    for table in reversed(TABLES):
        op.drop_table(table)
    _candidate_audit_lock_order(user_first=False)
    op.execute("DELETE FROM ad_v4_feature_gates WHERE gate_key IN ('reviewer4_draft_enabled','reviewer4_decision_enabled')")
    _capabilities(False)
