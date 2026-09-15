-- Frozen rejection-only review contract. No function selects or publishes authority.
CREATE OR REPLACE FUNCTION paprnav_v4_review_hash(domain text, payload bytea) RETURNS text
LANGUAGE sql IMMUTABLE STRICT AS $$
 SELECT encode(sha256(convert_to(domain,'UTF8')||decode('00','hex')||payload),'hex')
$$;

CREATE OR REPLACE FUNCTION paprnav_v4_review_authors(p_proposal text) RETURNS jsonb
LANGUAGE sql STABLE AS $$
 SELECT jsonb_build_object('version','paprnav-ad-v4-review-authorship-1','bindings',
   coalesce(jsonb_agg(jsonb_build_object('sourceTable',source_table,'sourceId',source_id,
     'userId',user_id,'authorshipRole',authorship_role,'boundHash',bound_hash)
     ORDER BY source_table,source_id,user_id,authorship_role),'[]'::jsonb))
 FROM (
   SELECT 'ad_v4_candidate_submissions' source_table,id source_id,actor_user_id user_id,
     'candidate_submitter' authorship_role,request_hash bound_hash
   FROM ad_v4_candidate_submissions WHERE proposal_id=p_proposal
   UNION
   SELECT 'ad_evidence_fragments',f.id,f.created_by_user_id,'fragment_creator',f.fragment_hash
   FROM ad_v4_candidate_evidence_bindings b JOIN ad_evidence_fragments f ON f.id=b.fragment_id
   WHERE b.proposal_id=p_proposal
   UNION
   SELECT 'ad_evidence_fragment_lifecycle_events',e.id,e.actor_user_id,'fragment_admitter',e.event_hash
   FROM ad_v4_candidate_evidence_bindings b JOIN ad_evidence_fragment_lifecycle_events e ON e.id=b.admitted_event_id
   WHERE b.proposal_id=p_proposal
 ) sources
$$;

CREATE OR REPLACE FUNCTION paprnav_v4_review_cutoff(p_proposal text) RETURNS jsonb
LANGUAGE sql STABLE AS $$
 SELECT jsonb_build_object('version','paprnav-ad-v4-review-cutoff-1','proposalId',p_proposal,
   'submissions',(SELECT coalesce(jsonb_agg(jsonb_build_object('id',id,'hash',request_hash) ORDER BY id),'[]'::jsonb) FROM (SELECT id,request_hash FROM ad_v4_candidate_submissions WHERE proposal_id=p_proposal ORDER BY id LIMIT 2001) bounded_submissions),
   'relationships',(SELECT coalesce(jsonb_agg(jsonb_build_object('id',id,'hash',relationship_hash) ORDER BY id),'[]'::jsonb) FROM (SELECT r.id,r.relationship_hash FROM ad_v4_candidate_submission_relationships r JOIN ad_v4_candidate_submissions s ON s.id=r.submission_id WHERE s.proposal_id=p_proposal OR r.predecessor_proposal_id=p_proposal ORDER BY r.id LIMIT 2001) bounded_relationships),
   'fragmentHeads',(SELECT coalesce(jsonb_agg(jsonb_build_object('fragmentId',fragment_id,'eventId',id,'eventHash',event_hash,'sequenceNumber',sequence_number) ORDER BY fragment_id),'[]'::jsonb) FROM (SELECT DISTINCT ON (e.fragment_id) e.* FROM ad_evidence_fragment_lifecycle_events e JOIN ad_v4_candidate_evidence_bindings b ON b.fragment_id=e.fragment_id WHERE b.proposal_id=p_proposal ORDER BY e.fragment_id,e.sequence_number DESC) heads),
   'applicabilityHeads',(SELECT coalesce(jsonb_agg(jsonb_build_object('projectionId',projection_id,'eventId',id,'eventHash',event_hash,'sequenceNumber',sequence_number) ORDER BY projection_id),'[]'::jsonb) FROM (SELECT DISTINCT ON (e.projection_id) e.* FROM ad_v4_candidate_app_projection_events e JOIN ad_v4_candidate_app_projections p ON p.id=e.projection_id WHERE p.proposal_id=p_proposal ORDER BY e.projection_id,e.sequence_number DESC) heads),
   'obligationHeads',(SELECT coalesce(jsonb_agg(jsonb_build_object('projectionId',projection_id,'eventId',id,'eventHash',event_hash,'sequenceNumber',sequence_number) ORDER BY projection_id),'[]'::jsonb) FROM (SELECT DISTINCT ON (e.projection_id) e.* FROM ad_v4_candidate_obligation_projection_events e JOIN ad_v4_candidate_obligation_projections p ON p.id=e.projection_id WHERE p.proposal_id=p_proposal ORDER BY e.projection_id,e.sequence_number DESC) heads))
$$;

CREATE OR REPLACE FUNCTION paprnav_v4_review_validate_auth(r jsonb) RETURNS void
LANGUAGE plpgsql AS $$
DECLARE a users%ROWTYPE; m organization_memberships%ROWTYPE; auth jsonb; stable jsonb;
BEGIN
 SELECT * INTO a FROM users WHERE id=r->>'actor_user_id' FOR UPDATE;
 SELECT * INTO m FROM organization_memberships WHERE id=r->>'authorizing_membership_id' FOR UPDATE;
 IF a.id IS NULL OR m.id IS NULL OR a.status<>'active' OR m.status<>'active'
   OR m.role<>'platform_admin' OR m.user_id<>a.id OR m.organization_id IS DISTINCT FROM r->>'organization_id'
 THEN RAISE EXCEPTION 'V4 review forbidden: active platform administrator required'; END IF;
 auth:=convert_from(decode(substr(r->>'auth_snapshot_bytes',3),'hex'),'UTF8')::jsonb;
 IF auth->>'version' IS DISTINCT FROM 'paprnav-ad-v4-review-authorization-1'
   OR auth->>'policyName' IS DISTINCT FROM 'paprnav-ad-v4-candidate-review-1'
   OR auth->>'policyVersion' IS DISTINCT FROM '1'
   OR auth->>'actorUserId' IS DISTINCT FROM a.id
   OR auth->>'authorizingMembershipId' IS DISTINCT FROM m.id
   OR auth->>'organizationId' IS DISTINCT FROM m.organization_id
   OR auth->>'userStatus' IS DISTINCT FROM 'active'
   OR auth->>'membershipStatus' IS DISTINCT FROM 'active'
   OR auth->>'role' IS DISTINCT FROM 'platform_admin'
   OR auth->>'validityRule' IS DISTINCT FROM 'status_only_v1'
   OR auth->'validFrom' IS DISTINCT FROM 'null'::jsonb
   OR auth->'validUntil' IS DISTINCT FROM 'null'::jsonb
   OR auth->'serverAuthorized' IS DISTINCT FROM 'true'::jsonb
   OR auth->>'userUpdatedAt' IS DISTINCT FROM to_char(a.updated_at AT TIME ZONE 'UTC','YYYY-MM-DD"T"HH24:MI:SS.US"Z"')
   OR auth->>'membershipUpdatedAt' IS DISTINCT FROM to_char(m.updated_at AT TIME ZONE 'UTC','YYYY-MM-DD"T"HH24:MI:SS.US"Z"')
   OR auth->>'action' NOT IN ('create_ad_v4_review_case','save_ad_v4_review_draft','request_ad_v4_review','reject_ad_v4_review')
   OR NOT auth ?& ARRAY['action','decisionTime','authorizationObservationHash','claimsHash']
   OR (SELECT count(*) FROM jsonb_object_keys(auth))<>19
 THEN RAISE EXCEPTION 'V4 review authorization snapshot differs'; END IF;
 IF auth->>'decisionTime' !~ '^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{6}Z$'
 THEN RAISE EXCEPTION 'V4 review authorization time differs'; END IF;
 stable:=auth-ARRAY['authorizationObservationHash','claimsHash','decisionTime'];
 IF auth->>'authorizationObservationHash' IS DISTINCT FROM paprnav_v4_review_hash('paprnav-ad-v4-review-auth-observation-1',convert_to(paprnav_v4_jcs(stable),'UTF8'))
   OR auth->>'claimsHash' IS DISTINCT FROM paprnav_v4_review_hash('paprnav-ad-v4-review-claims-1',convert_to(paprnav_v4_jcs(stable),'UTF8'))
 THEN RAISE EXCEPTION 'V4 review authorization observation differs'; END IF;
END $$;

CREATE OR REPLACE FUNCTION paprnav_v4_review_validate_observation(identity_bytes bytea,identity_hash text,audit_bytes bytea,audit_hash text,observed_at timestamptz,p_proposal text,p_directive text) RETURNS void
LANGUAGE plpgsql AS $$
DECLARE identity jsonb; audit jsonb; component jsonb; family text; state text;
 p ad_v4_candidate_proposals%ROWTYPE; projection record; expected_head text; heads jsonb;
 required_keys text[]; allowed_keys text[];
BEGIN
 identity:=convert_from(identity_bytes,'UTF8')::jsonb;
 audit:=convert_from(audit_bytes,'UTF8')::jsonb;
 IF identity_bytes<>convert_to(paprnav_v4_jcs(identity),'UTF8')
   OR audit_bytes<>convert_to(paprnav_v4_jcs(audit),'UTF8')
   OR identity_hash<>paprnav_v4_review_hash('paprnav-ad-v4-review-input-identity-1',identity_bytes)
   OR audit_hash<>paprnav_v4_review_hash('paprnav-ad-v4-review-observation-1',audit_bytes)
   OR identity->>'version' IS DISTINCT FROM 'paprnav-ad-v4-review-input-identity-1'
   OR identity->>'directiveId' IS DISTINCT FROM p_directive
   OR NOT identity ?& ARRAY['proposal','evidence','applicabilityProjection','obligationProjection']
   OR (SELECT count(*) FROM jsonb_object_keys(identity))<>6
   OR audit IS DISTINCT FROM jsonb_build_object('version','paprnav-ad-v4-review-observation-1','inputIdentityHash',identity_hash,'observedAt',to_char(observed_at AT TIME ZONE 'UTC','YYYY-MM-DD"T"HH24:MI:SS.US"Z"'))
 THEN RAISE EXCEPTION 'V4 review observation identity differs'; END IF;
 SELECT * INTO p FROM ad_v4_candidate_proposals WHERE id=p_proposal;
 IF p.id IS NULL OR p.directive_id<>p_directive THEN RAISE EXCEPTION 'V4 review proposal binding differs'; END IF;
 FOREACH family IN ARRAY ARRAY['proposal','evidence','applicabilityProjection','obligationProjection'] LOOP
   component:=identity->family; state:=component->>'state';
   IF jsonb_typeof(component) IS DISTINCT FROM 'object' OR state IS NULL
     OR state NOT IN ('verified','missing','stale','integrity_error','unsupported_version')
     OR EXISTS(SELECT 1 FROM jsonb_each(component) WHERE jsonb_typeof(value)<>'string')
   THEN RAISE EXCEPTION 'V4 review observation branch differs'; END IF;
   -- No branch may hide an invalid nested digest behind a valid outer digest.
   IF EXISTS(SELECT 1 FROM jsonb_each_text(component) item WHERE item.key LIKE '%Hash' AND item.value !~ '^[0-9a-f]{64}$')
     OR (component ? 'id' AND length(component->>'id') NOT BETWEEN 1 AND 36)
   THEN RAISE EXCEPTION 'V4 review observation nested identity encoding differs'; END IF;
   IF family='proposal' THEN
     required_keys:=ARRAY['state','id','storedCanonicalHash',CASE WHEN state='verified' THEN 'verifiedCanonicalHash' ELSE 'errorCode' END];
     allowed_keys:=required_keys;
   ELSIF family='evidence' THEN
     required_keys:=CASE state
       WHEN 'verified' THEN ARRAY['state','storedBindingHash','verifiedBindingHash','headSetHash']
       WHEN 'stale' THEN ARRAY['state','storedBindingHash','errorCode','headSetHash']
       ELSE ARRAY['state','storedBindingHash','errorCode'] END;
     allowed_keys:=CASE WHEN state IN ('integrity_error','unsupported_version') THEN required_keys||ARRAY['headSetHash'] ELSE required_keys END;
   ELSE
     required_keys:=CASE state
       WHEN 'missing' THEN ARRAY['state','errorCode']
       WHEN 'verified' THEN ARRAY['state','id','storedHash','eventHeadHash']
       WHEN 'stale' THEN ARRAY['state','id','storedHash','eventHeadHash','errorCode']
       ELSE ARRAY['state','id','storedHash','errorCode'] END;
     allowed_keys:=CASE WHEN state IN ('integrity_error','unsupported_version') THEN required_keys||ARRAY['eventHeadHash'] ELSE required_keys END;
   END IF;
   IF NOT component ?& required_keys OR EXISTS(SELECT 1 FROM jsonb_object_keys(component) key WHERE NOT key=ANY(allowed_keys))
   THEN RAISE EXCEPTION 'V4 review observation required or forbidden keys differ'; END IF;
   IF state='verified' THEN
     IF component ? 'errorCode' THEN RAISE EXCEPTION 'V4 verified observation has error'; END IF;
   ELSE
     IF component->>'errorCode' IS NULL OR component->>'errorCode' NOT IN ('candidate_integrity','evidence_integrity','evidence_not_current','projection_integrity','projection_missing','projection_stale','unsupported_version','unsupported_validator','missing_evidence','source_identity_or_evidence_missing')
       OR component ?| ARRAY['verifiedCanonicalHash','verifiedBindingHash']
     THEN RAISE EXCEPTION 'V4 review observation error differs'; END IF;
   END IF;
   IF family='proposal' THEN
     IF state='missing' OR component->>'id' IS DISTINCT FROM p.id OR component->>'storedCanonicalHash' IS DISTINCT FROM p.canonical_hash
       OR EXISTS(SELECT 1 FROM jsonb_object_keys(component) k WHERE k NOT IN ('state','id','storedCanonicalHash','verifiedCanonicalHash','errorCode'))
       OR (state='verified' AND component->>'verifiedCanonicalHash' IS DISTINCT FROM p.canonical_hash)
     THEN RAISE EXCEPTION 'V4 review observed proposal differs'; END IF;
     IF state='verified' AND (p.validator_version<>'paprnav-ad-v4-validator-2' OR p.canonicalization_version<>'paprnav-ad-v4-c14n-2'
       OR p.canonical_hash<>paprnav_v4_review_hash('paprnav:ad_extraction_v4:proposal:paprnav-ad-v4-c14n-2',p.canonical_bytes)
       OR convert_from(p.canonical_bytes,'UTF8')::jsonb IS DISTINCT FROM p.parsed_json::jsonb)
     THEN RAISE EXCEPTION 'V4 review falsely verified proposal'; END IF;
   ELSIF family='evidence' THEN
     IF component->>'storedBindingHash' IS DISTINCT FROM p.evidence_binding_hash
       OR EXISTS(SELECT 1 FROM jsonb_object_keys(component) k WHERE k NOT IN ('state','storedBindingHash','verifiedBindingHash','headSetHash','errorCode'))
       OR (state='verified' AND (component->>'verifiedBindingHash' IS DISTINCT FROM p.evidence_binding_hash OR NOT component ? 'headSetHash'))
     THEN RAISE EXCEPTION 'V4 review observed evidence differs'; END IF;
     IF state='missing' AND EXISTS(SELECT 1 FROM ad_v4_candidate_evidence_bindings WHERE proposal_id=p.id)
     THEN RAISE EXCEPTION 'V4 review falsely missing evidence'; END IF;
     heads:=paprnav_v4_review_cutoff(p.id)->'fragmentHeads';
     IF component ? 'headSetHash' AND (jsonb_array_length(heads)=0 OR component->>'headSetHash' IS DISTINCT FROM paprnav_v4_review_hash('paprnav-ad-v4-review-evidence-heads-1',convert_to(paprnav_v4_jcs(heads),'UTF8')))
     THEN RAISE EXCEPTION 'V4 review observed evidence head set differs'; END IF;
     IF state='verified' THEN
       IF component->>'headSetHash' IS DISTINCT FROM paprnav_v4_review_hash('paprnav-ad-v4-review-evidence-heads-1',convert_to(paprnav_v4_jcs(heads),'UTF8'))
         OR NOT EXISTS(SELECT 1 FROM ad_v4_candidate_evidence_bindings WHERE proposal_id=p.id)
         OR EXISTS(SELECT 1 FROM ad_v4_candidate_evidence_bindings b LEFT JOIN ad_evidence_fragments f ON f.id=b.fragment_id LEFT JOIN LATERAL (SELECT * FROM ad_evidence_fragment_lifecycle_events WHERE fragment_id=b.fragment_id ORDER BY sequence_number DESC LIMIT 1) e ON true WHERE b.proposal_id=p.id AND (f.id IS NULL OR f.fragment_hash IS DISTINCT FROM b.fragment_hash OR e.id IS DISTINCT FROM b.admitted_event_id OR e.event_hash IS DISTINCT FROM b.admitted_event_hash OR e.event_type IS DISTINCT FROM 'admitted'))
       THEN RAISE EXCEPTION 'V4 review falsely verified evidence'; END IF;
     END IF;
   ELSE
     IF EXISTS(SELECT 1 FROM jsonb_object_keys(component) k WHERE k NOT IN ('state','id','storedHash','eventHeadHash','errorCode'))
       OR (state='missing' AND component ?| ARRAY['id','storedHash','eventHeadHash'])
       OR (state='verified' AND NOT component ?& ARRAY['id','storedHash','eventHeadHash'])
     THEN RAISE EXCEPTION 'V4 review observed projection shape differs'; END IF;
     IF family='applicabilityProjection' THEN
       SELECT id,proposal_id,directive_id,projection_hash,materializer_version INTO projection FROM ad_v4_candidate_app_projections WHERE proposal_id=p.id ORDER BY (materializer_version='paprnav-ad-v4-app-materializer-2') DESC,id LIMIT 1;
       SELECT event_hash INTO expected_head FROM ad_v4_candidate_app_projection_events WHERE projection_id=projection.id ORDER BY sequence_number DESC LIMIT 1;
     ELSE
       SELECT id,proposal_id,directive_id,projection_hash,materializer_version INTO projection FROM ad_v4_candidate_obligation_projections WHERE proposal_id=p.id ORDER BY (materializer_version='paprnav-ad-v4-obligation-materializer-1') DESC,id LIMIT 1;
       SELECT event_hash INTO expected_head FROM ad_v4_candidate_obligation_projection_events WHERE projection_id=projection.id ORDER BY sequence_number DESC LIMIT 1;
     END IF;
     IF (state='missing' AND projection.id IS NOT NULL)
       OR (state<>'missing' AND projection.id IS NULL)
       OR (projection.id IS NOT NULL AND projection.directive_id IS DISTINCT FROM p_directive)
       OR (projection.id IS NOT NULL AND NOT component ?& ARRAY['id','storedHash'])
       OR (component ? 'id' AND component->>'id' IS DISTINCT FROM projection.id)
       OR (component ? 'storedHash' AND component->>'storedHash' IS DISTINCT FROM projection.projection_hash)
       OR (component ? 'eventHeadHash' AND component->>'eventHeadHash' IS DISTINCT FROM expected_head)
       OR (projection.id IS NOT NULL AND ((expected_head IS NOT NULL) IS DISTINCT FROM (component ? 'eventHeadHash')))
     THEN RAISE EXCEPTION 'V4 review observed projection binding differs'; END IF;
     IF state='verified' THEN
       IF projection.id IS NULL OR projection.directive_id<>p_directive THEN RAISE EXCEPTION 'V4 review verified projection missing'; END IF;
       IF family='applicabilityProjection' THEN
         IF projection.materializer_version<>'paprnav-ad-v4-app-materializer-2' THEN RAISE EXCEPTION 'V4 review falsely verified unsupported applicability'; END IF;
         PERFORM paprnav_v4_candidate_app_require_complete(projection.id);
         IF EXISTS(SELECT 1 FROM ad_v4_candidate_app_projection_events WHERE projection_id=projection.id AND event_type='stale_marked') THEN RAISE EXCEPTION 'V4 review falsely verified stale applicability'; END IF;
       ELSE
         IF projection.materializer_version<>'paprnav-ad-v4-obligation-materializer-1' THEN RAISE EXCEPTION 'V4 review falsely verified unsupported obligations'; END IF;
         PERFORM paprnav_v4_review_verify_obligation(projection.id);
         IF EXISTS(SELECT 1 FROM ad_v4_candidate_obligation_projection_events WHERE projection_id=projection.id AND event_type<>'materialized') THEN RAISE EXCEPTION 'V4 review falsely verified stale obligations'; END IF;
       END IF;
     END IF;
   END IF;
 END LOOP;
END $$;

CREATE OR REPLACE FUNCTION paprnav_v4_review_insert_guard() RETURNS trigger
LANGUAGE plpgsql AS $$
DECLARE r jsonb; auth jsonb; item record; payload bytea; parsed jsonb; expected jsonb;
 domain text; hash_column text; stamp text; required_action text; terminal boolean; gate_count integer;
BEGIN
 r:=to_jsonb(NEW);
 PERFORM paprnav_v4_review_validate_auth(r);
 auth:=convert_from(NEW.auth_snapshot_bytes,'UTF8')::jsonb;
 required_action:=CASE TG_TABLE_NAME WHEN 'ad_v4_review_cases' THEN 'create_ad_v4_review_case' WHEN 'ad_v4_review_draft_revisions' THEN 'save_ad_v4_review_draft' WHEN 'ad_v4_review_requests' THEN 'request_ad_v4_review' WHEN 'ad_v4_review_case_events' THEN r->>'endpoint_action' ELSE 'reject_ad_v4_review' END;
 IF auth->>'action' IS DISTINCT FROM required_action THEN RAISE EXCEPTION 'V4 review action differs'; END IF;
 IF NEW.auth_policy_version<>'1' OR NEW.endpoint_action IS DISTINCT FROM required_action OR length(trim(NEW.idempotency_key))=0 THEN RAISE EXCEPTION 'V4 review request scope differs'; END IF;
 PERFORM pg_advisory_xact_lock(paprnav_v4_lock_key('idem:'||NEW.actor_user_id||':'||NEW.authorizing_membership_id||':'||NEW.endpoint_action||':'||NEW.auth_policy_version||':'||NEW.idempotency_key));
 PERFORM pg_advisory_xact_lock(paprnav_v4_lock_key('candidate-relationship-graph:'||NEW.directive_id));
 PERFORM id FROM ad_v4_candidate_proposals WHERE id=NEW.proposal_id AND directive_id=NEW.directive_id FOR UPDATE;
 IF NOT FOUND THEN RAISE EXCEPTION 'V4 review proposal binding differs'; END IF;
 terminal:=required_action='reject_ad_v4_review';
 PERFORM gate_key FROM ad_v4_feature_gates WHERE gate_key IN ('validator2_write_enabled','materializer3a_enabled','materializer3b_enabled','reviewer4_draft_enabled') OR (terminal AND gate_key='reviewer4_decision_enabled') ORDER BY CASE gate_key WHEN 'validator2_write_enabled' THEN 1 WHEN 'materializer3a_enabled' THEN 2 WHEN 'materializer3b_enabled' THEN 3 WHEN 'reviewer4_draft_enabled' THEN 4 ELSE 5 END FOR SHARE;
 SELECT count(*) INTO gate_count FROM ad_v4_feature_gates WHERE enabled AND (gate_key='reviewer4_draft_enabled' OR (terminal AND gate_key='reviewer4_decision_enabled'));
 IF gate_count<>(CASE WHEN terminal THEN 2 ELSE 1 END) THEN RAISE EXCEPTION 'V4 review feature gate disabled'; END IF;
 PERFORM id FROM ad_v4_candidate_evidence_bindings WHERE proposal_id=NEW.proposal_id ORDER BY id FOR SHARE;
 PERFORM f.id FROM ad_evidence_fragments f JOIN ad_v4_candidate_evidence_bindings b ON b.fragment_id=f.id WHERE b.proposal_id=NEW.proposal_id ORDER BY f.id FOR SHARE OF f;
 PERFORM pg_advisory_xact_lock(paprnav_v4_lock_key('projection:'||NEW.proposal_id||':paprnav-ad-v4-app-materializer-2'));
 PERFORM id FROM ad_v4_candidate_app_projections WHERE proposal_id=NEW.proposal_id ORDER BY id FOR SHARE;
 PERFORM pg_advisory_xact_lock(paprnav_v4_lock_key('projection:'||NEW.proposal_id||':paprnav-ad-v4-obligation-materializer-1'));
 PERFORM id FROM ad_v4_candidate_obligation_projections WHERE proposal_id=NEW.proposal_id ORDER BY id FOR SHARE;
 PERFORM pg_advisory_xact_lock(paprnav_v4_lock_key('review-case:'||NEW.proposal_id));
 IF TG_TABLE_NAME<>'ad_v4_review_cases' THEN
   PERFORM id FROM ad_v4_review_cases WHERE id=NEW.case_id FOR UPDATE;
 END IF;

 -- Each blob is bounded, canonical, domain separated and bound by scalar hash.
 FOR item IN SELECT key,value FROM jsonb_each(r) LOOP
   IF item.key LIKE '%\_hash' ESCAPE '\' AND item.value<>'null'::jsonb AND item.value #>> '{}' !~ '^[0-9a-f]{64}$' THEN RAISE EXCEPTION 'V4 review digest encoding differs'; END IF;
   IF item.key NOT LIKE '%\_bytes' ESCAPE '\' OR item.key='canonical_bytes' THEN CONTINUE; END IF;
   payload:=decode(substr(item.value #>> '{}',3),'hex'); parsed:=convert_from(payload,'UTF8')::jsonb;
   IF payload<>convert_to(paprnav_v4_jcs(parsed),'UTF8') THEN RAISE EXCEPTION 'V4 review canonical blob differs'; END IF;
   domain:=CASE item.key WHEN 'auth_snapshot_bytes' THEN 'paprnav-ad-v4-review-authorization-1' WHEN 'input_identity_bytes' THEN 'paprnav-ad-v4-review-input-identity-1' WHEN 'decision_input_identity_bytes' THEN 'paprnav-ad-v4-review-input-identity-1' WHEN 'observation_bytes' THEN 'paprnav-ad-v4-review-observation-1' WHEN 'decision_observation_bytes' THEN 'paprnav-ad-v4-review-observation-1' WHEN 'annotation_bytes' THEN 'paprnav-ad-v4-review-annotation-1' WHEN 'cutoff_bytes' THEN 'paprnav-ad-v4-review-cutoff-1' WHEN 'authorship_set_bytes' THEN 'paprnav-ad-v4-review-authorship-1' WHEN 'reasons_bytes' THEN 'paprnav-ad-v4-review-reasons-1' WHEN 'request_canonical_bytes' THEN 'paprnav-ad-v4-review-request-1' END;
   hash_column:=CASE item.key WHEN 'request_canonical_bytes' THEN 'request_hash' ELSE replace(item.key,'_bytes','_hash') END;
   IF domain IS NULL OR r->>hash_column IS DISTINCT FROM paprnav_v4_review_hash(domain,payload) THEN RAISE EXCEPTION 'V4 review blob hash differs'; END IF;
 END LOOP;
 expected:=r-ARRAY['canonical_bytes','row_hash','event_hash','signature_hash'];
 FOR item IN SELECT key,value FROM jsonb_each(expected) LOOP
   IF item.key LIKE '%\_bytes' ESCAPE '\' THEN expected:=expected-item.key;
   ELSIF item.key IN ('created_at','observed_at','requested_at','decision_observed_at','rejected_at','signed_at','occurred_at') THEN
     expected:=jsonb_set(expected,ARRAY[item.key],to_jsonb(to_char((item.value #>> '{}')::timestamptz AT TIME ZONE 'UTC','YYYY-MM-DD"T"HH24:MI:SS.US"Z"')));
   END IF;
 END LOOP;
 expected:=jsonb_build_object('version',NEW.contract_version,'table',TG_TABLE_NAME,'record',expected);
 IF NEW.canonical_bytes<>convert_to(paprnav_v4_jcs(expected),'UTF8')
   OR coalesce(r->>'row_hash',r->>'event_hash')<>paprnav_v4_review_hash('paprnav-ad-v4-review-row-1',NEW.canonical_bytes)
 THEN RAISE EXCEPTION 'V4 review canonical record differs'; END IF;
 stamp:=CASE TG_TABLE_NAME WHEN 'ad_v4_review_cases' THEN r->>'created_at' WHEN 'ad_v4_review_draft_revisions' THEN r->>'created_at' WHEN 'ad_v4_review_requests' THEN r->>'requested_at' WHEN 'ad_v4_review_rejections' THEN r->>'rejected_at' WHEN 'ad_v4_signoff_events' THEN r->>'signed_at' ELSE r->>'occurred_at' END;
 IF auth->>'decisionTime' IS DISTINCT FROM to_char(stamp::timestamptz AT TIME ZONE 'UTC','YYYY-MM-DD"T"HH24:MI:SS.US"Z"') THEN RAISE EXCEPTION 'V4 review decision time differs'; END IF;

 IF TG_TABLE_NAME IN ('ad_v4_review_cases','ad_v4_review_draft_revisions','ad_v4_review_requests') THEN
   PERFORM paprnav_v4_review_validate_observation(NEW.input_identity_bytes,NEW.input_identity_hash,NEW.observation_bytes,NEW.observation_hash,NEW.observed_at,NEW.proposal_id,NEW.directive_id);
 END IF;
 IF TG_TABLE_NAME='ad_v4_review_cases' THEN
   IF NEW.proposal_canonical_hash IS DISTINCT FROM (SELECT canonical_hash FROM ad_v4_candidate_proposals WHERE id=NEW.proposal_id) THEN RAISE EXCEPTION 'V4 case proposal hash differs'; END IF;
 ELSIF TG_TABLE_NAME='ad_v4_review_draft_revisions' THEN
   parsed:=convert_from(NEW.annotation_bytes,'UTF8')::jsonb;
   IF parsed->>'version' IS DISTINCT FROM 'paprnav-ad-v4-review-annotation-1' OR jsonb_typeof(parsed->'annotations') IS DISTINCT FROM 'array' OR (SELECT count(*) FROM jsonb_object_keys(parsed))<>2 OR jsonb_array_length(parsed->'annotations')>128 THEN RAISE EXCEPTION 'V4 review annotation shape differs'; END IF;
   IF EXISTS(SELECT 1 FROM jsonb_array_elements(parsed->'annotations') value WHERE jsonb_typeof(value) IS DISTINCT FROM 'object' OR NOT value ?& ARRAY['pointer','text'] OR (SELECT count(*) FROM jsonb_object_keys(value))<>2 OR jsonb_typeof(value->'pointer') IS DISTINCT FROM 'string' OR jsonb_typeof(value->'text') IS DISTINCT FROM 'string' OR length(value->>'pointer') NOT BETWEEN 1 AND 1024 OR left(value->>'pointer',1)<>'/' OR value->>'pointer' ~ '~([^01]|$)' OR length(value->>'text') NOT BETWEEN 1 AND 4096 OR value->>'text' !~ '[^[:space:]]') THEN RAISE EXCEPTION 'V4 review annotation bounds differ'; END IF;
 ELSIF TG_TABLE_NAME='ad_v4_review_requests' THEN
   parsed:=convert_from(NEW.cutoff_bytes,'UTF8')::jsonb;
   expected:=paprnav_v4_review_cutoff(NEW.proposal_id);
   IF jsonb_array_length(parsed->'submissions')>2000 OR jsonb_array_length(parsed->'relationships')>2000
     OR jsonb_array_length(expected->'submissions')>2000 OR jsonb_array_length(expected->'relationships')>2000
   THEN RAISE EXCEPTION 'V4 review cutoff capacity exceeded'; END IF;
   IF parsed IS DISTINCT FROM expected
     OR convert_from(NEW.authorship_set_bytes,'UTF8')::jsonb IS DISTINCT FROM paprnav_v4_review_authors(NEW.proposal_id)
     OR NEW.authorship_source_count<>jsonb_array_length(paprnav_v4_review_authors(NEW.proposal_id)->'bindings')
   THEN RAISE EXCEPTION 'V4 review request cutoff differs'; END IF;
 ELSIF TG_TABLE_NAME='ad_v4_review_rejections' THEN
   PERFORM paprnav_v4_review_validate_observation(NEW.decision_input_identity_bytes,NEW.decision_input_identity_hash,NEW.decision_observation_bytes,NEW.decision_observation_hash,NEW.decision_observed_at,NEW.proposal_id,NEW.directive_id);
   parsed:=convert_from(NEW.reasons_bytes,'UTF8')::jsonb;
   IF parsed->>'version' IS DISTINCT FROM 'paprnav-ad-v4-review-reasons-1' OR jsonb_typeof(parsed->'codes') IS DISTINCT FROM 'array' OR jsonb_typeof(parsed->'explanation') IS DISTINCT FROM 'string' OR (SELECT count(*) FROM jsonb_object_keys(parsed))<>3 OR length(parsed->>'explanation') NOT BETWEEN 1 AND 4096 OR parsed->>'explanation' !~ '[^[:space:]]' OR jsonb_array_length(parsed->'codes') NOT BETWEEN 1 AND 7 THEN RAISE EXCEPTION 'V4 review rejection reasons differ'; END IF;
   IF EXISTS(SELECT 1 FROM jsonb_array_elements_text(parsed->'codes') code WHERE code NOT IN ('candidate_integrity','source_identity_or_evidence_missing','evidence_not_current','projection_integrity','unsupported_version','input_changed','remediation_requested')) OR parsed->'codes' IS DISTINCT FROM (SELECT jsonb_agg(code ORDER BY code) FROM (SELECT DISTINCT value code FROM jsonb_array_elements_text(parsed->'codes')) codes) THEN RAISE EXCEPTION 'V4 review rejection reason codes differ'; END IF;
 ELSIF TG_TABLE_NAME='ad_v4_signoff_events' THEN
   IF NEW.signature_hash<>paprnav_v4_review_hash('paprnav-ad-v4-review-signature-1',NEW.canonical_bytes) OR NEW.authorization_observation_hash IS DISTINCT FROM auth->>'authorizationObservationHash' THEN RAISE EXCEPTION 'V4 review signoff digest differs'; END IF;
 ELSIF TG_TABLE_NAME='ad_v4_review_case_events' THEN
   parsed:=convert_from(NEW.request_canonical_bytes,'UTF8')::jsonb;
   IF NEW.auth_policy_version<>'1' OR NEW.endpoint_action IS DISTINCT FROM (CASE NEW.event_type WHEN 'case_created' THEN 'create_ad_v4_review_case' WHEN 'draft_saved' THEN 'save_ad_v4_review_draft' WHEN 'review_requested' THEN 'request_ad_v4_review' WHEN 'review_rejected' THEN 'reject_ad_v4_review' END) OR length(trim(NEW.idempotency_key))=0
     OR parsed->>'version' IS DISTINCT FROM NEW.contract_version OR parsed->>'action' IS DISTINCT FROM NEW.endpoint_action OR parsed->>'directiveId' IS DISTINCT FROM NEW.directive_id OR parsed->>'proposalId' IS DISTINCT FROM NEW.proposal_id
     OR parsed->'caseId' IS DISTINCT FROM (CASE WHEN NEW.event_type='case_created' THEN 'null'::jsonb ELSE to_jsonb(NEW.case_id) END)
     OR jsonb_typeof(parsed->'body') IS DISTINCT FROM 'object' OR (SELECT count(*) FROM jsonb_object_keys(parsed))<>6
     OR (NEW.event_type<>'case_created' AND parsed->'body'->>'expectedPredecessorEventHash' IS DISTINCT FROM NEW.predecessor_event_hash)
   THEN RAISE EXCEPTION 'V4 review canonical request routing differs'; END IF;
 END IF;
 RETURN NEW;
END $$;

-- Aggregate retained authoritative bytes without decoding JSON or copying
-- bytea values through to_jsonb. Keep every frozen *_bytes column explicit;
-- the migration test compares this sum against metadata-driven accounting.
CREATE OR REPLACE FUNCTION paprnav_v4_review_case_authoritative_bytes(p_case text) RETURNS bigint
LANGUAGE sql STABLE AS $$
 SELECT coalesce(sum(size_bytes),0)::bigint FROM (
   SELECT coalesce(octet_length(auth_snapshot_bytes),0)::bigint + coalesce(octet_length(request_canonical_bytes),0) + coalesce(octet_length(canonical_bytes),0) + coalesce(octet_length(input_identity_bytes),0) + coalesce(octet_length(observation_bytes),0) AS size_bytes
     FROM ad_v4_review_cases WHERE id=p_case
   UNION ALL
   SELECT coalesce(octet_length(auth_snapshot_bytes),0)::bigint + coalesce(octet_length(request_canonical_bytes),0) + coalesce(octet_length(canonical_bytes),0) + coalesce(octet_length(input_identity_bytes),0) + coalesce(octet_length(observation_bytes),0) + coalesce(octet_length(annotation_bytes),0)
     FROM ad_v4_review_draft_revisions WHERE case_id=p_case
   UNION ALL
   SELECT coalesce(octet_length(auth_snapshot_bytes),0)::bigint + coalesce(octet_length(request_canonical_bytes),0) + coalesce(octet_length(canonical_bytes),0) + coalesce(octet_length(input_identity_bytes),0) + coalesce(octet_length(observation_bytes),0) + coalesce(octet_length(cutoff_bytes),0) + coalesce(octet_length(authorship_set_bytes),0)
     FROM ad_v4_review_requests WHERE case_id=p_case
   UNION ALL
   SELECT coalesce(octet_length(auth_snapshot_bytes),0)::bigint + coalesce(octet_length(request_canonical_bytes),0) + coalesce(octet_length(canonical_bytes),0) + coalesce(octet_length(decision_input_identity_bytes),0) + coalesce(octet_length(decision_observation_bytes),0) + coalesce(octet_length(reasons_bytes),0)
     FROM ad_v4_review_rejections WHERE case_id=p_case
   UNION ALL
   SELECT coalesce(octet_length(auth_snapshot_bytes),0)::bigint + coalesce(octet_length(request_canonical_bytes),0) + coalesce(octet_length(canonical_bytes),0)
     FROM ad_v4_signoff_events WHERE case_id=p_case
   UNION ALL
   SELECT coalesce(octet_length(auth_snapshot_bytes),0)::bigint + coalesce(octet_length(request_canonical_bytes),0) + coalesce(octet_length(canonical_bytes),0)
     FROM ad_v4_review_case_events WHERE case_id=p_case
 ) authoritative_rows
$$;

CREATE OR REPLACE FUNCTION paprnav_v4_review_require_complete(p_case text) RETURNS void
LANGUAGE plpgsql AS $$
DECLARE c ad_v4_review_cases%ROWTYPE; e ad_v4_review_case_events%ROWTYPE;
 previous ad_v4_review_case_events%ROWTYPE; d ad_v4_review_draft_revisions%ROWTYPE;
 q ad_v4_review_requests%ROWTYPE; rejection ad_v4_review_rejections%ROWTYPE;
 signoff ad_v4_signoff_events%ROWTYPE; latest_draft text; expected_sequence integer:=0;
 expected_revision integer:=0; authoritative_bytes bigint; object_auth text; object_bytes bytea; object_time timestamptz; object_identity text; body jsonb; body_keys text[]; expected_codes jsonb; object_record jsonb;
BEGIN
 SELECT * INTO c FROM ad_v4_review_cases WHERE id=p_case;
 IF c.id IS NULL THEN RAISE EXCEPTION 'V4 review case missing'; END IF;
 -- Closed ordinal ranges and uniqueness enforce these budgets for healthy
 -- rows. Bounded recounts also fail before traversing corrupted history.
 IF c.case_sequence NOT BETWEEN 0 AND 99
   OR (SELECT count(*) FROM (SELECT 1 FROM ad_v4_review_cases WHERE proposal_id=c.proposal_id LIMIT 101) bounded_cases)>100
   OR (SELECT count(*) FROM (SELECT 1 FROM ad_v4_review_draft_revisions WHERE case_id=c.id LIMIT 1001) bounded_drafts)>1000
   OR (SELECT count(*) FROM (SELECT 1 FROM ad_v4_review_case_events WHERE case_id=c.id LIMIT 1004) bounded_events)>1003
 THEN RAISE EXCEPTION 'V4 review history capacity exceeded'; END IF;
 -- Phase ceilings reserve the per-column worst case for every remaining
 -- immutable transition: request+event needs at most 10 MiB, while
 -- rejection+signoff+event needs at most 12 MiB. The 2 MiB cushions make the
 -- reservation explicit while every authoritative byte column is capped at
 -- 1 MiB by table CHECKs.
 authoritative_bytes:=paprnav_v4_review_case_authoritative_bytes(c.id);
 IF (NOT EXISTS(SELECT 1 FROM ad_v4_review_case_events phase_event
                  WHERE phase_event.case_id=c.id AND phase_event.event_type='review_requested')
       AND authoritative_bytes>16777216)
   OR (EXISTS(SELECT 1 FROM ad_v4_review_case_events phase_event
                  WHERE phase_event.case_id=c.id AND phase_event.event_type='review_requested')
       AND NOT EXISTS(SELECT 1 FROM ad_v4_review_case_events phase_event
                  WHERE phase_event.case_id=c.id AND phase_event.event_type='review_rejected')
       AND authoritative_bytes>29360128)
   OR (EXISTS(SELECT 1 FROM ad_v4_review_case_events phase_event
                  WHERE phase_event.case_id=c.id AND phase_event.event_type='review_rejected')
       AND authoritative_bytes>41943040)
 THEN RAISE EXCEPTION 'V4 review authoritative byte capacity exceeded'; END IF;
 IF c.case_sequence>0 AND NOT EXISTS(SELECT 1 FROM ad_v4_review_cases p WHERE p.id=c.predecessor_case_id AND p.proposal_id=c.proposal_id AND p.case_sequence=c.case_sequence-1 AND EXISTS(SELECT 1 FROM ad_v4_review_case_events prior_event WHERE prior_event.case_id=p.id AND prior_event.event_type='review_rejected')) THEN RAISE EXCEPTION 'V4 successor case predecessor differs'; END IF;
 IF (SELECT count(*) FROM ad_v4_review_cases p WHERE p.proposal_id=c.proposal_id AND NOT EXISTS(SELECT 1 FROM ad_v4_review_case_events x WHERE x.case_id=p.id AND x.event_type='review_rejected'))>1 THEN RAISE EXCEPTION 'V4 proposal has multiple open review cases'; END IF;
 FOR e IN SELECT * FROM ad_v4_review_case_events WHERE case_id=c.id ORDER BY sequence_number LOOP
   IF e.sequence_number<>expected_sequence OR e.predecessor_event_hash IS DISTINCT FROM previous.event_hash THEN RAISE EXCEPTION 'V4 review event chain differs'; END IF;
   IF expected_sequence=0 AND e.event_type<>'case_created' THEN RAISE EXCEPTION 'V4 review creation event missing'; END IF;
   IF expected_sequence>0 AND NOT ((previous.resulting_state='draft' AND e.event_type IN ('draft_saved','review_requested')) OR (previous.resulting_state='pending_review' AND e.event_type='review_rejected')) THEN RAISE EXCEPTION 'V4 review lifecycle transition differs'; END IF;
   IF e.event_type='case_created' THEN object_auth:=c.auth_snapshot_hash; object_bytes:=c.auth_snapshot_bytes; object_time:=c.created_at; object_identity:=c.input_identity_hash; object_record:=to_jsonb(c);
   ELSIF e.event_type='draft_saved' THEN
     SELECT * INTO d FROM ad_v4_review_draft_revisions WHERE id=e.draft_revision_id AND case_id=c.id;
     IF d.id IS NULL OR d.revision_number<>expected_revision OR d.predecessor_draft_id IS DISTINCT FROM latest_draft OR d.expected_predecessor_event_hash<>e.predecessor_event_hash THEN RAISE EXCEPTION 'V4 review draft binding differs'; END IF;
     latest_draft:=d.id; expected_revision:=expected_revision+1; object_auth:=d.auth_snapshot_hash; object_bytes:=d.auth_snapshot_bytes; object_time:=d.created_at; object_identity:=d.input_identity_hash; object_record:=to_jsonb(d);
   ELSIF e.event_type='review_requested' THEN
     SELECT * INTO q FROM ad_v4_review_requests WHERE id=e.review_request_id AND case_id=c.id;
     IF q.id IS NULL OR q.draft_revision_id IS DISTINCT FROM latest_draft OR q.expected_predecessor_event_hash<>e.predecessor_event_hash THEN RAISE EXCEPTION 'V4 review request binding differs'; END IF;
     object_auth:=q.auth_snapshot_hash; object_bytes:=q.auth_snapshot_bytes; object_time:=q.requested_at; object_identity:=q.input_identity_hash; object_record:=to_jsonb(q);
   ELSE
     SELECT * INTO rejection FROM ad_v4_review_rejections WHERE id=e.rejection_id AND case_id=c.id;
     SELECT * INTO signoff FROM ad_v4_signoff_events WHERE id=e.signoff_id AND case_id=c.id;
     IF q.id IS NULL OR rejection.id IS NULL OR signoff.id IS NULL OR e.review_request_id<>q.id
       OR rejection.request_id<>q.id OR signoff.request_id<>q.id OR signoff.rejection_id<>rejection.id
       OR rejection.proposal_canonical_hash<>c.proposal_canonical_hash
       OR rejection.requested_input_identity_hash<>q.input_identity_hash OR rejection.requested_observation_hash<>q.observation_hash
       OR signoff.requested_input_identity_hash<>q.input_identity_hash OR signoff.requested_observation_hash<>q.observation_hash
       OR signoff.decision_input_identity_hash<>rejection.decision_input_identity_hash OR signoff.decision_observation_hash<>rejection.decision_observation_hash
       OR signoff.rejection_hash<>rejection.row_hash OR rejection.expected_predecessor_event_hash<>e.predecessor_event_hash
       OR signoff.auth_snapshot_hash<>rejection.auth_snapshot_hash OR signoff.auth_snapshot_bytes<>rejection.auth_snapshot_bytes OR signoff.signed_at<>rejection.rejected_at
       OR signoff.auth_policy_version<>rejection.auth_policy_version OR signoff.endpoint_action<>rejection.endpoint_action OR signoff.idempotency_key<>rejection.idempotency_key OR signoff.request_hash<>rejection.request_hash OR signoff.request_canonical_bytes<>rejection.request_canonical_bytes
     THEN RAISE EXCEPTION 'V4 rejection signoff binding differs'; END IF;
     IF rejection.decision_input_identity_hash<>q.input_identity_hash AND NOT (convert_from(rejection.reasons_bytes,'UTF8')::jsonb->'codes' ? 'input_changed') THEN RAISE EXCEPTION 'V4 rejection input mismatch reason missing'; END IF;
     object_auth:=rejection.auth_snapshot_hash; object_bytes:=rejection.auth_snapshot_bytes; object_time:=rejection.rejected_at; object_identity:=rejection.decision_input_identity_hash; object_record:=to_jsonb(rejection);
   END IF;
   IF object_auth IS DISTINCT FROM e.auth_snapshot_hash OR object_bytes IS DISTINCT FROM e.auth_snapshot_bytes OR object_time IS DISTINCT FROM e.occurred_at THEN RAISE EXCEPTION 'V4 review object-event authorization differs'; END IF;
   IF object_record->>'auth_policy_version' IS DISTINCT FROM e.auth_policy_version OR object_record->>'endpoint_action' IS DISTINCT FROM e.endpoint_action OR object_record->>'idempotency_key' IS DISTINCT FROM e.idempotency_key OR object_record->>'request_hash' IS DISTINCT FROM e.request_hash OR object_record->'request_canonical_bytes' IS DISTINCT FROM to_jsonb(e)->'request_canonical_bytes' THEN RAISE EXCEPTION 'V4 review object-event idempotency differs'; END IF;
   body:=convert_from(e.request_canonical_bytes,'UTF8')::jsonb->'body';
   body_keys:=CASE e.event_type
     WHEN 'case_created' THEN ARRAY['expectedAuthorizationObservationHash','expectedInputIdentityHash']
     WHEN 'draft_saved' THEN ARRAY['expectedAuthorizationObservationHash','expectedInputIdentityHash','expectedPredecessorEventHash','annotations','intendedAction']
     WHEN 'review_requested' THEN ARRAY['expectedAuthorizationObservationHash','expectedInputIdentityHash','expectedPredecessorEventHash','draftRevisionId']
     ELSE ARRAY['expectedAuthorizationObservationHash','expectedInputIdentityHash','expectedPredecessorEventHash','expectedRequestId','reasonCodes','explanation'] END;
   IF NOT body ?& body_keys OR (SELECT count(*) FROM jsonb_object_keys(body))<>cardinality(body_keys) THEN RAISE EXCEPTION 'V4 review request body shape differs'; END IF;
   IF body->>'expectedAuthorizationObservationHash' IS DISTINCT FROM (convert_from(e.auth_snapshot_bytes,'UTF8')::jsonb->>'authorizationObservationHash')
     OR (e.event_type<>'case_created' AND body->>'expectedInputIdentityHash' IS DISTINCT FROM object_identity)
     OR (e.event_type='case_created' AND body->>'expectedInputIdentityHash' IS NOT NULL AND body->>'expectedInputIdentityHash' IS DISTINCT FROM object_identity)
     OR (e.event_type='review_rejected' AND body->>'expectedRequestId' IS DISTINCT FROM q.id)
   THEN RAISE EXCEPTION 'V4 review request compare-and-swap differs'; END IF;
   IF e.event_type='draft_saved' AND (convert_from(d.annotation_bytes,'UTF8')::jsonb IS DISTINCT FROM jsonb_build_object('version','paprnav-ad-v4-review-annotation-1','annotations',body->'annotations') OR d.intended_action IS DISTINCT FROM body->>'intendedAction') THEN RAISE EXCEPTION 'V4 review draft request content differs'; END IF;
   IF e.event_type='review_requested' AND body->'draftRevisionId' IS DISTINCT FROM coalesce(to_jsonb(q.draft_revision_id),'null'::jsonb) THEN RAISE EXCEPTION 'V4 review frozen draft request differs'; END IF;
   IF e.event_type='review_rejected' THEN
     IF jsonb_typeof(body->'reasonCodes') IS DISTINCT FROM 'array' OR jsonb_typeof(body->'explanation') IS DISTINCT FROM 'string' OR jsonb_array_length(body->'reasonCodes') NOT BETWEEN 1 AND 7 OR body->'reasonCodes' IS DISTINCT FROM (SELECT jsonb_agg(code ORDER BY code) FROM (SELECT DISTINCT value code FROM jsonb_array_elements_text(body->'reasonCodes')) codes) THEN RAISE EXCEPTION 'V4 review rejection request reasons differ'; END IF;
     SELECT jsonb_agg(code ORDER BY code) INTO expected_codes FROM (SELECT value code FROM jsonb_array_elements_text(body->'reasonCodes') UNION SELECT 'input_changed' WHERE rejection.decision_input_identity_hash<>q.input_identity_hash) codes;
     IF convert_from(rejection.reasons_bytes,'UTF8')::jsonb IS DISTINCT FROM jsonb_build_object('version','paprnav-ad-v4-review-reasons-1','codes',expected_codes,'explanation',body->'explanation') THEN RAISE EXCEPTION 'V4 review rejection request content differs'; END IF;
   END IF;
   previous:=e; expected_sequence:=expected_sequence+1;
 END LOOP;
 IF expected_sequence=0 OR expected_revision<>(SELECT count(*) FROM ad_v4_review_draft_revisions WHERE case_id=c.id)
   OR (SELECT count(*) FROM ad_v4_review_requests WHERE case_id=c.id)<>(SELECT count(*) FROM ad_v4_review_case_events WHERE case_id=c.id AND event_type='review_requested')
   OR (SELECT count(*) FROM ad_v4_review_rejections WHERE case_id=c.id)<>(SELECT count(*) FROM ad_v4_review_case_events WHERE case_id=c.id AND event_type='review_rejected')
   OR (SELECT count(*) FROM ad_v4_signoff_events WHERE case_id=c.id)<>(SELECT count(*) FROM ad_v4_review_case_events WHERE case_id=c.id AND event_type='review_rejected')
 THEN RAISE EXCEPTION 'V4 review object-event completeness differs'; END IF;
END $$;

CREATE OR REPLACE FUNCTION paprnav_v4_review_complete_trigger() RETURNS trigger
LANGUAGE plpgsql AS $$
DECLARE r jsonb; terminal boolean;
BEGIN
 -- The bounded count/byte preflight in this validator precedes even the
 -- newly inserted snapshot's JSON parsing. BEFORE INSERT already acquired
 -- actor/membership locks; the fresh authorization recheck still follows.
 IF TG_TABLE_NAME='ad_v4_review_cases' THEN
   PERFORM paprnav_v4_review_require_complete(NEW.id);
 ELSE
   PERFORM paprnav_v4_review_require_complete(NEW.case_id);
 END IF;
 -- Recheck only the newly inserted authority snapshot. Historical snapshots
 -- retain their meaning after later membership changes.
 PERFORM paprnav_v4_review_validate_auth(to_jsonb(NEW));
 r:=to_jsonb(NEW);
 terminal:=convert_from(NEW.auth_snapshot_bytes,'UTF8')::jsonb->>'action'='reject_ad_v4_review';
 IF NOT EXISTS(SELECT 1 FROM ad_v4_feature_gates WHERE gate_key='reviewer4_draft_enabled' AND enabled)
   OR (terminal AND NOT EXISTS(SELECT 1 FROM ad_v4_feature_gates WHERE gate_key='reviewer4_decision_enabled' AND enabled))
 THEN RAISE EXCEPTION 'V4 review feature gate disabled at commit'; END IF;
 IF TG_TABLE_NAME='ad_v4_review_requests' THEN
   IF jsonb_array_length(paprnav_v4_review_cutoff(NEW.proposal_id)->'submissions')>2000
     OR jsonb_array_length(paprnav_v4_review_cutoff(NEW.proposal_id)->'relationships')>2000
   THEN RAISE EXCEPTION 'V4 review cutoff capacity exceeded'; END IF;
   IF convert_from(NEW.cutoff_bytes,'UTF8')::jsonb IS DISTINCT FROM paprnav_v4_review_cutoff(NEW.proposal_id)
     OR convert_from(NEW.authorship_set_bytes,'UTF8')::jsonb IS DISTINCT FROM paprnav_v4_review_authors(NEW.proposal_id)
   THEN RAISE EXCEPTION 'V4 review request cutoff changed before commit'; END IF;
 END IF;
 RETURN NULL;
END $$;
