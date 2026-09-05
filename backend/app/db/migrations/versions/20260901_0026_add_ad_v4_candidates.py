"""add immutable candidate-only AD extraction V4 storage

Revision ID: 20260901_0026
Revises: 20260830_0025
Create Date: 2026-09-01
"""

from alembic import op
import sqlalchemy as sa


revision = "20260901_0026"
down_revision = "20260830_0025"
branch_labels = None
depends_on = None

TABLES = (
    "ad_v4_candidate_proposals",
    "ad_v4_candidate_evidence_bindings",
    "ad_v4_candidate_submissions",
    "ad_v4_candidate_submission_relationships",
    "ad_v4_candidate_proposal_events",
)


def upgrade() -> None:
    op.create_table(
        "ad_v4_candidate_proposals",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("directive_id", sa.String(36), sa.ForeignKey("airworthiness_directives.id"), nullable=False),
        sa.Column("schema_version", sa.String(64), nullable=False),
        sa.Column("canonicalization_version", sa.String(64), nullable=False),
        sa.Column("validator_version", sa.String(64), nullable=False),
        sa.Column("canonical_bytes", sa.LargeBinary(), nullable=False),
        sa.Column("parsed_json", sa.JSON(), nullable=False),
        sa.Column("canonical_hash", sa.String(64), nullable=False),
        sa.Column("evidence_binding_bytes", sa.LargeBinary(), nullable=False),
        sa.Column("evidence_binding_hash", sa.String(64), nullable=False),
        sa.Column("binding_count", sa.Integer(), nullable=False),
        sa.Column("gate", sa.String(32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("schema_version = 'ad_extraction_v4'", name="ck_ad_v4_proposal_schema"),
        sa.CheckConstraint("gate = 'candidate_only'", name="ck_ad_v4_proposal_gate"),
        sa.CheckConstraint("length(canonical_hash) = 64", name="ck_ad_v4_proposal_hash"),
        sa.CheckConstraint("length(evidence_binding_hash) = 64", name="ck_ad_v4_binding_hash"),
        sa.CheckConstraint("binding_count > 0", name="ck_ad_v4_binding_count"),
        sa.UniqueConstraint("directive_id", "canonicalization_version", "canonical_hash", name="uq_ad_v4_proposal_content"),
    )
    op.create_index("ix_ad_v4_candidate_proposals_directive_id", "ad_v4_candidate_proposals", ["directive_id"])
    op.create_index("ix_ad_v4_candidate_proposals_canonical_hash", "ad_v4_candidate_proposals", ["canonical_hash"])

    op.create_table(
        "ad_v4_candidate_evidence_bindings",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("proposal_id", sa.String(36), sa.ForeignKey("ad_v4_candidate_proposals.id"), nullable=False),
        sa.Column("directive_id", sa.String(36), sa.ForeignKey("airworthiness_directives.id"), nullable=False),
        sa.Column("evidence_key", sa.String(128), nullable=False),
        sa.Column("fragment_id", sa.String(36), sa.ForeignKey("ad_evidence_fragments.id"), nullable=False),
        sa.Column("fragment_hash", sa.String(64), nullable=False),
        sa.Column("admitted_event_id", sa.String(36), sa.ForeignKey("ad_evidence_fragment_lifecycle_events.id"), nullable=False),
        sa.Column("admitted_event_hash", sa.String(64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("proposal_id", "evidence_key", name="uq_ad_v4_binding_key"),
    )
    op.create_index("ix_ad_v4_candidate_evidence_bindings_proposal_id", "ad_v4_candidate_evidence_bindings", ["proposal_id"])
    op.create_index("ix_ad_v4_candidate_evidence_bindings_fragment_id", "ad_v4_candidate_evidence_bindings", ["fragment_id"])

    op.create_table(
        "ad_v4_candidate_submissions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("proposal_id", sa.String(36), sa.ForeignKey("ad_v4_candidate_proposals.id"), nullable=False),
        sa.Column("directive_id", sa.String(36), sa.ForeignKey("airworthiness_directives.id"), nullable=False),
        sa.Column("actor_kind", sa.String(32), nullable=False),
        sa.Column("actor_user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("authorizing_membership_id", sa.String(36), sa.ForeignKey("organization_memberships.id"), nullable=False),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("actor_role", sa.String(64), nullable=False),
        sa.Column("actor_status", sa.String(32), nullable=False),
        sa.Column("auth_policy_name", sa.String(64), nullable=False),
        sa.Column("auth_policy_version", sa.String(64), nullable=False),
        sa.Column("auth_claims_hash", sa.String(64), nullable=False),
        sa.Column("endpoint_action", sa.String(64), nullable=False),
        sa.Column("idempotency_key", sa.String(255), nullable=False),
        sa.Column("request_hash", sa.String(64), nullable=False),
        sa.Column("request_canonical_bytes", sa.LargeBinary(), nullable=False),
        sa.Column("raw_transport_hash", sa.String(64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("actor_kind = 'platform_admin'", name="ck_ad_v4_submission_actor"),
        sa.CheckConstraint("actor_role = 'platform_admin'", name="ck_ad_v4_submission_role"),
        sa.CheckConstraint("actor_status = 'active'", name="ck_ad_v4_submission_status"),
        sa.UniqueConstraint("actor_user_id", "authorizing_membership_id", "endpoint_action", "auth_policy_version", "idempotency_key", name="uq_ad_v4_submission_idempotency"),
    )
    op.create_index("ix_ad_v4_candidate_submissions_proposal_id", "ad_v4_candidate_submissions", ["proposal_id"])
    op.create_index("ix_ad_v4_candidate_submissions_actor_user_id", "ad_v4_candidate_submissions", ["actor_user_id"])

    op.create_table(
        "ad_v4_candidate_submission_relationships",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("submission_id", sa.String(36), sa.ForeignKey("ad_v4_candidate_submissions.id"), nullable=False),
        sa.Column("relationship_key", sa.String(128), nullable=False),
        sa.Column("relation_type", sa.String(32), nullable=False),
        sa.Column("predecessor_proposal_id", sa.String(36), sa.ForeignKey("ad_v4_candidate_proposals.id"), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("evidence_keys", sa.JSON(), nullable=False),
        sa.Column("canonical_bytes", sa.LargeBinary(), nullable=False),
        sa.Column("relationship_hash", sa.String(64), nullable=False, unique=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("relation_type IN ('corrects_candidate', 'replaces_candidate')", name="ck_ad_v4_relationship_type"),
        sa.CheckConstraint("length(reason) > 0", name="ck_ad_v4_relationship_reason"),
        sa.UniqueConstraint("submission_id", "relationship_key", name="uq_ad_v4_relationship_key"),
    )
    op.create_index("ix_ad_v4_candidate_submission_relationships_submission_id", "ad_v4_candidate_submission_relationships", ["submission_id"])

    op.create_table(
        "ad_v4_candidate_proposal_events",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("proposal_id", sa.String(36), sa.ForeignKey("ad_v4_candidate_proposals.id"), nullable=False),
        sa.Column("directive_id", sa.String(36), sa.ForeignKey("airworthiness_directives.id"), nullable=False),
        sa.Column("created_by_submission_id", sa.String(36), sa.ForeignKey("ad_v4_candidate_submissions.id"), nullable=False),
        sa.Column("event_type", sa.String(32), nullable=False),
        sa.Column("sequence_number", sa.Integer(), nullable=False),
        sa.Column("proposal_canonical_hash", sa.String(64), nullable=False),
        sa.Column("evidence_binding_hash", sa.String(64), nullable=False),
        sa.Column("predecessor_event_hash", sa.String(64), nullable=True),
        sa.Column("canonical_bytes", sa.LargeBinary(), nullable=False),
        sa.Column("event_hash", sa.String(64), nullable=False, unique=True),
        sa.Column("occurred_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("event_type = 'candidate_created'", name="ck_ad_v4_event_type"),
        sa.CheckConstraint("sequence_number = 0", name="ck_ad_v4_event_sequence"),
        sa.CheckConstraint("predecessor_event_hash IS NULL", name="ck_ad_v4_event_root"),
        sa.UniqueConstraint("proposal_id", "sequence_number", name="uq_ad_v4_event_sequence"),
    )
    op.create_index("ix_ad_v4_candidate_proposal_events_proposal_id", "ad_v4_candidate_proposal_events", ["proposal_id"])

    op.execute("""
      CREATE FUNCTION paprnav_v4_reject_mutation() RETURNS trigger AS $$
      BEGIN RAISE EXCEPTION 'immutable AD V4 candidate rows cannot be updated or deleted'; END;
      $$ LANGUAGE plpgsql
    """)
    for table in TABLES:
        op.execute(f"CREATE TRIGGER trg_{table}_immutable BEFORE UPDATE OR DELETE ON {table} FOR EACH ROW EXECUTE FUNCTION paprnav_v4_reject_mutation()")

    op.execute("""
      CREATE FUNCTION paprnav_v4_lock_fragment_lifecycle() RETURNS trigger AS $$
      BEGIN
        PERFORM 1 FROM ad_evidence_fragments WHERE id = NEW.fragment_id FOR UPDATE;
        IF NOT FOUND THEN RAISE EXCEPTION 'AD evidence lifecycle fragment missing'; END IF;
        RETURN NEW;
      END; $$ LANGUAGE plpgsql
    """)
    op.execute("CREATE TRIGGER trg_aaa_ad_evidence_lifecycle_lock BEFORE INSERT ON ad_evidence_fragment_lifecycle_events FOR EACH ROW EXECUTE FUNCTION paprnav_v4_lock_fragment_lifecycle()")

    op.execute("""
      CREATE FUNCTION paprnav_v4_validate_proposal() RETURNS trigger AS $$
      BEGIN
        IF convert_from(NEW.canonical_bytes, 'UTF8')::jsonb IS DISTINCT FROM NEW.parsed_json::jsonb THEN
          RAISE EXCEPTION 'V4 canonical bytes/JSON mismatch';
        END IF;
        IF NEW.canonical_hash <> encode(sha256(convert_to('paprnav:ad_extraction_v4:proposal:paprnav-ad-v4-c14n-1', 'UTF8') || decode('00','hex') || NEW.canonical_bytes), 'hex') THEN
          RAISE EXCEPTION 'V4 proposal hash mismatch';
        END IF;
        IF NEW.evidence_binding_hash <> encode(sha256(convert_to('paprnav:ad_extraction_v4:evidence-bindings:1', 'UTF8') || decode('00','hex') || NEW.evidence_binding_bytes), 'hex') THEN
          RAISE EXCEPTION 'V4 evidence binding hash mismatch';
        END IF;
        IF NEW.schema_version <> 'ad_extraction_v4'
           OR NEW.canonicalization_version <> 'paprnav-ad-v4-c14n-1'
           OR NEW.validator_version <> 'paprnav-ad-v4-validator-1'
           OR NEW.gate <> 'candidate_only'
           OR NEW.parsed_json::jsonb->>'schemaVersion' <> NEW.schema_version
           OR NEW.parsed_json::jsonb->'directiveIdentity'->>'directiveId' <> NEW.directive_id
           OR jsonb_typeof(NEW.parsed_json::jsonb->'evidenceBindings') <> 'object' THEN
          RAISE EXCEPTION 'V4 proposal envelope/relational identity mismatch';
        END IF;
        RETURN NEW;
      END; $$ LANGUAGE plpgsql
    """)
    op.execute("CREATE TRIGGER trg_ad_v4_candidate_proposals_validate BEFORE INSERT ON ad_v4_candidate_proposals FOR EACH ROW EXECUTE FUNCTION paprnav_v4_validate_proposal()")

    op.execute("""
      CREATE FUNCTION paprnav_v4_validate_binding() RETURNS trigger AS $$
      DECLARE f ad_evidence_fragments%ROWTYPE; e ad_evidence_fragment_lifecycle_events%ROWTYPE;
              p ad_v4_candidate_proposals%ROWTYPE; declared jsonb; event_count integer;
      BEGIN
        SELECT * INTO f FROM ad_evidence_fragments WHERE id = NEW.fragment_id FOR UPDATE;
        SELECT count(*) INTO event_count FROM ad_evidence_fragment_lifecycle_events WHERE fragment_id = NEW.fragment_id;
        SELECT * INTO e FROM ad_evidence_fragment_lifecycle_events WHERE id = NEW.admitted_event_id AND fragment_id = NEW.fragment_id;
        IF f.id IS NULL OR f.directive_id <> NEW.directive_id OR f.fragment_hash <> NEW.fragment_hash
           OR event_count <> 1 OR e.event_type <> 'admitted' OR e.sequence_number <> 0
           OR e.predecessor_event_hash IS NOT NULL OR e.event_hash <> NEW.admitted_event_hash THEN
          RAISE EXCEPTION 'V4 evidence binding is not an exact attributable admitted root';
        END IF;
        SELECT * INTO p FROM ad_v4_candidate_proposals WHERE id=NEW.proposal_id;
        declared := p.parsed_json::jsonb->'evidenceBindings'->NEW.evidence_key;
        IF p.id IS NULL OR p.directive_id<>NEW.directive_id
           OR declared IS NULL
           OR declared->>'fragmentId'<>NEW.fragment_id
           OR declared->>'fragmentHash'<>NEW.fragment_hash THEN
          RAISE EXCEPTION 'V4 evidence binding directive mismatch';
        END IF;
        RETURN NEW;
      END; $$ LANGUAGE plpgsql
    """)
    op.execute("CREATE TRIGGER trg_ad_v4_candidate_bindings_validate BEFORE INSERT ON ad_v4_candidate_evidence_bindings FOR EACH ROW EXECUTE FUNCTION paprnav_v4_validate_binding()")

    op.execute("""
      CREATE FUNCTION paprnav_v4_validate_submission() RETURNS trigger AS $$
      DECLARE m organization_memberships%ROWTYPE; u users%ROWTYPE; p ad_v4_candidate_proposals%ROWTYPE;
              payload jsonb; auth_payload text;
      BEGIN
        SELECT * INTO m FROM organization_memberships WHERE id=NEW.authorizing_membership_id FOR UPDATE;
        SELECT * INTO u FROM users WHERE id=NEW.actor_user_id FOR UPDATE;
        SELECT * INTO p FROM ad_v4_candidate_proposals WHERE id=NEW.proposal_id;
        IF m.id IS NULL OR u.id IS NULL OR u.status<>'active'
           OR m.user_id<>NEW.actor_user_id OR m.organization_id<>NEW.organization_id
           OR m.role<>'platform_admin' OR m.status<>'active'
           OR NEW.actor_kind<>'platform_admin' OR NEW.actor_role<>m.role OR NEW.actor_status<>m.status
           OR NEW.auth_policy_name<>'paprnav-platform-admin-candidate-write'
           OR NEW.auth_policy_version<>'1' OR NEW.endpoint_action<>'create_ad_v4_candidate'
           OR p.directive_id<>NEW.directive_id THEN
          RAISE EXCEPTION 'V4 submission authorization/proposal mismatch';
        END IF;
        IF NEW.request_hash !~ '^[0-9a-f]{64}$' OR NEW.raw_transport_hash !~ '^[0-9a-f]{64}$'
           OR NEW.auth_claims_hash !~ '^[0-9a-f]{64}$' THEN
          RAISE EXCEPTION 'V4 submission hash shape mismatch';
        END IF;
        auth_payload := '{"membershipId":'||to_jsonb(NEW.authorizing_membership_id)::text
          ||',"organizationId":'||to_jsonb(NEW.organization_id)::text
          ||',"policy":'||to_jsonb(NEW.auth_policy_name)::text
          ||',"role":'||to_jsonb(NEW.actor_role)::text
          ||',"status":'||to_jsonb(NEW.actor_status)::text
          ||',"userId":'||to_jsonb(NEW.actor_user_id)::text
          ||',"version":'||to_jsonb(NEW.auth_policy_version)::text||'}';
        IF NEW.auth_claims_hash <> encode(sha256(convert_to(auth_payload,'UTF8')),'hex') THEN
          RAISE EXCEPTION 'V4 submission authorization hash mismatch';
        END IF;
        IF NEW.request_hash <> encode(sha256(convert_to('paprnav:ad_extraction_v4:submission:1','UTF8') || decode('00','hex') || NEW.request_canonical_bytes),'hex') THEN
          RAISE EXCEPTION 'V4 submission hash mismatch';
        END IF;
        payload := convert_from(NEW.request_canonical_bytes, 'UTF8')::jsonb;
        IF payload->>'version' <> 'ad-v4-submission-v1'
           OR payload->>'directiveId' <> NEW.directive_id
           OR payload->>'proposalCanonicalHash' <> p.canonical_hash
           OR jsonb_typeof(payload->'relationships') <> 'array' THEN
          RAISE EXCEPTION 'V4 submission envelope/relational identity mismatch';
        END IF;
        RETURN NEW;
      END; $$ LANGUAGE plpgsql
    """)
    op.execute("CREATE TRIGGER trg_ad_v4_candidate_submissions_validate BEFORE INSERT ON ad_v4_candidate_submissions FOR EACH ROW EXECUTE FUNCTION paprnav_v4_validate_submission()")

    op.execute("""
      CREATE FUNCTION paprnav_v4_validate_relationship() RETURNS trigger AS $$
      DECLARE current_directive text; current_proposal text; predecessor_directive text;
              proposal_payload jsonb; payload jsonb; unresolved integer;
      BEGIN
        SELECT p.directive_id,p.id,p.parsed_json::jsonb INTO current_directive,current_proposal,proposal_payload
          FROM ad_v4_candidate_submissions s JOIN ad_v4_candidate_proposals p ON p.id=s.proposal_id
          WHERE s.id=NEW.submission_id;
        SELECT directive_id INTO predecessor_directive FROM ad_v4_candidate_proposals WHERE id=NEW.predecessor_proposal_id;
        IF current_directive IS NULL OR current_directive<>predecessor_directive
           OR current_proposal=NEW.predecessor_proposal_id THEN
          RAISE EXCEPTION 'V4 relationship directive/self mismatch';
        END IF;
        PERFORM pg_advisory_xact_lock(hashtextextended('candidate-relationship-graph:'||current_directive, 0));
        IF NEW.relationship_hash <> encode(sha256(convert_to('paprnav:ad_extraction_v4:submission-relationship:1','UTF8') || decode('00','hex') || NEW.canonical_bytes),'hex') THEN RAISE EXCEPTION 'V4 relationship hash mismatch'; END IF;
        payload := convert_from(NEW.canonical_bytes, 'UTF8')::jsonb;
        IF payload <> jsonb_build_object(
          'version','ad-v4-submission-relationship-v1', 'submissionId',NEW.submission_id,
          'relationshipKey',NEW.relationship_key, 'relationType',NEW.relation_type,
          'predecessorProposalId',NEW.predecessor_proposal_id, 'reason',NEW.reason,
          'evidenceKeys',NEW.evidence_keys::jsonb
        ) THEN RAISE EXCEPTION 'V4 relationship envelope/relational identity mismatch'; END IF;
        IF jsonb_typeof(NEW.evidence_keys::jsonb)<>'array' OR jsonb_array_length(NEW.evidence_keys::jsonb)=0 THEN
          RAISE EXCEPTION 'V4 relationship evidence is empty';
        END IF;
        IF jsonb_array_length(NEW.evidence_keys::jsonb)<>(
          SELECT count(DISTINCT value) FROM jsonb_array_elements_text(NEW.evidence_keys::jsonb)
        ) THEN RAISE EXCEPTION 'V4 relationship evidence contains duplicates'; END IF;
        SELECT count(*) INTO unresolved FROM jsonb_array_elements_text(NEW.evidence_keys::jsonb) AS k
          WHERE NOT (proposal_payload->'evidenceBindings' ? k);
        IF unresolved<>0 THEN RAISE EXCEPTION 'V4 relationship evidence does not resolve'; END IF;
        IF EXISTS (
          WITH RECURSIVE edges(current_id, predecessor_id) AS (
            SELECT s.proposal_id,r.predecessor_proposal_id
              FROM ad_v4_candidate_submission_relationships r
              JOIN ad_v4_candidate_submissions s ON s.id=r.submission_id
              WHERE s.directive_id=current_directive
          ), reachable(node) AS (
            SELECT NEW.predecessor_proposal_id
            UNION
            SELECT e.predecessor_id FROM edges e JOIN reachable x ON e.current_id=x.node
          ) SELECT 1 FROM reachable WHERE node=current_proposal
        ) THEN RAISE EXCEPTION 'V4 candidate relationship cycle'; END IF;
        RETURN NEW;
      END; $$ LANGUAGE plpgsql
    """)
    op.execute("CREATE TRIGGER trg_ad_v4_candidate_relationships_validate BEFORE INSERT ON ad_v4_candidate_submission_relationships FOR EACH ROW EXECUTE FUNCTION paprnav_v4_validate_relationship()")

    op.execute("""
      CREATE FUNCTION paprnav_v4_validate_event() RETURNS trigger AS $$
      DECLARE p ad_v4_candidate_proposals%ROWTYPE; payload jsonb;
      BEGIN
        SELECT * INTO p FROM ad_v4_candidate_proposals WHERE id=NEW.proposal_id;
        IF p.id IS NULL OR p.directive_id<>NEW.directive_id OR p.canonical_hash<>NEW.proposal_canonical_hash OR p.evidence_binding_hash<>NEW.evidence_binding_hash THEN RAISE EXCEPTION 'V4 event proposal mismatch'; END IF;
        IF NOT EXISTS (SELECT 1 FROM ad_v4_candidate_submissions s WHERE s.id=NEW.created_by_submission_id AND s.proposal_id=NEW.proposal_id) THEN RAISE EXCEPTION 'V4 event creator mismatch'; END IF;
        IF NEW.event_hash <> encode(sha256(convert_to('paprnav:ad_extraction_v4:candidate-event:1','UTF8') || decode('00','hex') || NEW.canonical_bytes),'hex') THEN RAISE EXCEPTION 'V4 event hash mismatch'; END IF;
        payload := convert_from(NEW.canonical_bytes, 'UTF8')::jsonb;
        IF payload <> jsonb_build_object(
          'version','ad-v4-candidate-created-v1', 'eventType',NEW.event_type,
          'proposalId',NEW.proposal_id, 'directiveId',NEW.directive_id,
          'proposalCanonicalHash',NEW.proposal_canonical_hash,
          'evidenceBindingHash',NEW.evidence_binding_hash,
          'createdBySubmissionId',NEW.created_by_submission_id
        ) THEN RAISE EXCEPTION 'V4 event envelope/relational identity mismatch'; END IF;
        RETURN NEW;
      END; $$ LANGUAGE plpgsql
    """)
    op.execute("CREATE TRIGGER trg_ad_v4_candidate_events_validate BEFORE INSERT ON ad_v4_candidate_proposal_events FOR EACH ROW EXECUTE FUNCTION paprnav_v4_validate_event()")

    op.execute("""
      CREATE FUNCTION paprnav_v4_require_complete_proposal() RETURNS trigger AS $$
      DECLARE expected_bindings jsonb; binding_payload jsonb;
      BEGIN
        SELECT coalesce(jsonb_agg(jsonb_build_object(
          'evidenceKey',b.evidence_key, 'fragmentId',b.fragment_id,
          'fragmentHash',b.fragment_hash, 'admittedEventId',b.admitted_event_id,
          'admittedEventHash',b.admitted_event_hash
        ) ORDER BY b.evidence_key), '[]'::jsonb)
        INTO expected_bindings FROM ad_v4_candidate_evidence_bindings b WHERE b.proposal_id=NEW.id;
        binding_payload := convert_from(NEW.evidence_binding_bytes, 'UTF8')::jsonb;
        IF (SELECT count(*) FROM ad_v4_candidate_evidence_bindings WHERE proposal_id=NEW.id)<>NEW.binding_count
           OR (SELECT count(*) FROM ad_v4_candidate_proposal_events WHERE proposal_id=NEW.id AND event_type='candidate_created')<>1
           OR binding_payload <> jsonb_build_object('version','ad-v4-evidence-bindings-v1','bindings',expected_bindings)
           OR (NEW.parsed_json::jsonb->'evidenceBindings') <> (
             SELECT coalesce(jsonb_object_agg(b.evidence_key, jsonb_build_object('fragmentId',b.fragment_id,'fragmentHash',b.fragment_hash)), '{}'::jsonb)
             FROM ad_v4_candidate_evidence_bindings b WHERE b.proposal_id=NEW.id
           ) THEN
          RAISE EXCEPTION 'V4 proposal is incomplete';
        END IF;
        RETURN NULL;
      END; $$ LANGUAGE plpgsql
    """)
    op.execute("CREATE CONSTRAINT TRIGGER trg_ad_v4_proposal_complete AFTER INSERT ON ad_v4_candidate_proposals DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION paprnav_v4_require_complete_proposal()")

    op.execute("""
      CREATE FUNCTION paprnav_v4_require_binding_parent_complete() RETURNS trigger AS $$
      DECLARE p ad_v4_candidate_proposals%ROWTYPE; expected_bindings jsonb; binding_payload jsonb;
      BEGIN
        SELECT * INTO p FROM ad_v4_candidate_proposals WHERE id=NEW.proposal_id;
        SELECT coalesce(jsonb_agg(jsonb_build_object(
          'evidenceKey',b.evidence_key, 'fragmentId',b.fragment_id,
          'fragmentHash',b.fragment_hash, 'admittedEventId',b.admitted_event_id,
          'admittedEventHash',b.admitted_event_hash
        ) ORDER BY b.evidence_key), '[]'::jsonb)
        INTO expected_bindings FROM ad_v4_candidate_evidence_bindings b WHERE b.proposal_id=NEW.proposal_id;
        binding_payload := convert_from(p.evidence_binding_bytes, 'UTF8')::jsonb;
        IF p.id IS NULL OR (SELECT count(*) FROM ad_v4_candidate_evidence_bindings WHERE proposal_id=p.id)<>p.binding_count
           OR binding_payload<>jsonb_build_object('version','ad-v4-evidence-bindings-v1','bindings',expected_bindings)
           OR p.parsed_json::jsonb->'evidenceBindings'<>(
             SELECT coalesce(jsonb_object_agg(b.evidence_key,jsonb_build_object('fragmentId',b.fragment_id,'fragmentHash',b.fragment_hash)),'{}'::jsonb)
             FROM ad_v4_candidate_evidence_bindings b WHERE b.proposal_id=p.id
           ) THEN RAISE EXCEPTION 'V4 proposal binding set is incomplete'; END IF;
        RETURN NULL;
      END; $$ LANGUAGE plpgsql
    """)
    op.execute("CREATE CONSTRAINT TRIGGER trg_ad_v4_binding_parent_complete AFTER INSERT ON ad_v4_candidate_evidence_bindings DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION paprnav_v4_require_binding_parent_complete()")

    op.execute("""
      CREATE FUNCTION paprnav_v4_require_complete_submission() RETURNS trigger AS $$
      DECLARE expected_relationships jsonb; payload jsonb;
      BEGIN
        SELECT coalesce(jsonb_agg(jsonb_build_object(
          'relationshipKey',r.relationship_key, 'relationType',r.relation_type,
          'predecessorProposalId',r.predecessor_proposal_id, 'reason',r.reason,
          'evidenceKeys',r.evidence_keys::jsonb
        ) ORDER BY r.relationship_key), '[]'::jsonb)
        INTO expected_relationships FROM ad_v4_candidate_submission_relationships r WHERE r.submission_id=NEW.id;
        payload := convert_from(NEW.request_canonical_bytes, 'UTF8')::jsonb;
        IF payload->'relationships' <> expected_relationships THEN
          RAISE EXCEPTION 'V4 submission relationship envelope mismatch';
        END IF;
        RETURN NULL;
      END; $$ LANGUAGE plpgsql
    """)
    op.execute("CREATE CONSTRAINT TRIGGER trg_ad_v4_submission_complete AFTER INSERT ON ad_v4_candidate_submissions DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION paprnav_v4_require_complete_submission()")
    op.execute("""
      CREATE FUNCTION paprnav_v4_require_relationship_parent_complete() RETURNS trigger AS $$
      DECLARE expected_relationships jsonb; payload jsonb;
      BEGIN
        SELECT coalesce(jsonb_agg(jsonb_build_object(
          'relationshipKey',r.relationship_key, 'relationType',r.relation_type,
          'predecessorProposalId',r.predecessor_proposal_id, 'reason',r.reason,
          'evidenceKeys',r.evidence_keys::jsonb
        ) ORDER BY r.relationship_key), '[]'::jsonb)
        INTO expected_relationships FROM ad_v4_candidate_submission_relationships r WHERE r.submission_id=NEW.submission_id;
        SELECT convert_from(s.request_canonical_bytes,'UTF8')::jsonb INTO payload
          FROM ad_v4_candidate_submissions s WHERE s.id=NEW.submission_id;
        IF payload IS NULL OR payload->'relationships'<>expected_relationships THEN
          RAISE EXCEPTION 'V4 submission relationship set is incomplete';
        END IF;
        RETURN NULL;
      END; $$ LANGUAGE plpgsql
    """)
    op.execute("CREATE CONSTRAINT TRIGGER trg_ad_v4_relationship_parent_complete AFTER INSERT ON ad_v4_candidate_submission_relationships DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION paprnav_v4_require_relationship_parent_complete()")


def downgrade() -> None:
    op.execute("LOCK TABLE " + ", ".join(reversed(TABLES)) + " IN ACCESS EXCLUSIVE MODE")
    occupied = op.get_bind().execute(sa.text("SELECT 1 WHERE " + " OR ".join(f"EXISTS (SELECT 1 FROM {table} LIMIT 1)" for table in TABLES))).first()
    if occupied is not None:
        raise RuntimeError("Revision 0026 contains immutable V4 candidates; restore a verified pre-0026 backup instead of deleting audit data")
    op.execute("DROP TRIGGER IF EXISTS trg_aaa_ad_evidence_lifecycle_lock ON ad_evidence_fragment_lifecycle_events")
    op.execute("DROP FUNCTION IF EXISTS paprnav_v4_lock_fragment_lifecycle()")
    for name, table in (
        ("trg_ad_v4_relationship_parent_complete", "ad_v4_candidate_submission_relationships"),
        ("trg_ad_v4_binding_parent_complete", "ad_v4_candidate_evidence_bindings"),
        ("trg_ad_v4_submission_complete", "ad_v4_candidate_submissions"),
        ("trg_ad_v4_proposal_complete", "ad_v4_candidate_proposals"),
        ("trg_ad_v4_candidate_events_validate", "ad_v4_candidate_proposal_events"),
        ("trg_ad_v4_candidate_relationships_validate", "ad_v4_candidate_submission_relationships"),
        ("trg_ad_v4_candidate_submissions_validate", "ad_v4_candidate_submissions"),
        ("trg_ad_v4_candidate_bindings_validate", "ad_v4_candidate_evidence_bindings"),
        ("trg_ad_v4_candidate_proposals_validate", "ad_v4_candidate_proposals"),
    ):
        op.execute(f"DROP TRIGGER IF EXISTS {name} ON {table}")
    for table in TABLES:
        op.execute(f"DROP TRIGGER IF EXISTS trg_{table}_immutable ON {table}")
    for function in (
        "paprnav_v4_require_relationship_parent_complete",
        "paprnav_v4_require_binding_parent_complete",
        "paprnav_v4_require_complete_submission",
        "paprnav_v4_require_complete_proposal", "paprnav_v4_validate_event",
        "paprnav_v4_validate_relationship", "paprnav_v4_validate_submission",
        "paprnav_v4_validate_binding", "paprnav_v4_validate_proposal",
        "paprnav_v4_reject_mutation",
    ):
        op.execute(f"DROP FUNCTION IF EXISTS {function}()")
    for table in reversed(TABLES):
        op.drop_table(table)
