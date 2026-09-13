CREATE OR REPLACE FUNCTION paprnav_v4_obligation_evidence_json(
  p_projection_id text, p_node_id text
) RETURNS jsonb AS $$
  SELECT coalesce(jsonb_agg(to_jsonb(evidence_key) ORDER BY canonical_ordinal),'[]'::jsonb)
    FROM ad_v4_candidate_obligation_evidence_links
   WHERE projection_id=p_projection_id AND semantic_node_id=p_node_id
$$ LANGUAGE sql STABLE;

CREATE OR REPLACE FUNCTION paprnav_v4_obligation_assertion_json(
  p_projection_id text, p_node_id text
) RETURNS jsonb AS $$
DECLARE a ad_v4_candidate_obligation_value_assertions%ROWTYPE;
BEGIN
  SELECT * INTO STRICT a FROM ad_v4_candidate_obligation_value_assertions
   WHERE projection_id=p_projection_id AND semantic_node_id=p_node_id;
  IF a.state='known' THEN
    RETURN jsonb_build_object(
      'state',a.state,'value',a.value,
      'evidenceKeys',paprnav_v4_obligation_evidence_json(p_projection_id,p_node_id));
  END IF;
  RETURN jsonb_build_object(
    'state',a.state,'reason',a.reason,
    'temporalScope',jsonb_build_object('kind',a.temporal_kind),
    'evidenceKeys',paprnav_v4_obligation_evidence_json(p_projection_id,p_node_id));
END; $$ LANGUAGE plpgsql STABLE STRICT;

CREATE OR REPLACE FUNCTION paprnav_v4_obligation_expression_json(
  p_projection_id text, p_expression_node_id text
) RETURNS jsonb AS $$
DECLARE e ad_v4_candidate_obligation_expressions%ROWTYPE; result jsonb;
BEGIN
  SELECT * INTO STRICT e FROM ad_v4_candidate_obligation_expressions
   WHERE projection_id=p_projection_id AND semantic_node_id=p_expression_node_id;
  result:=jsonb_build_object('nodeType',e.node_type);
  IF e.node_type='scope_ref' THEN
    RETURN result||jsonb_build_object('scopeKey',(
      SELECT node_key FROM ad_v4_candidate_app_semantic_nodes
       WHERE id=e.app_target_node_id AND projection_id=e.app_target_projection_id
         AND node_type='product_scope'));
  ELSIF e.node_type='predicate_ref' THEN
    RETURN result||jsonb_build_object('conditionKey',(
      SELECT node_key FROM ad_v4_candidate_app_semantic_nodes
       WHERE id=e.app_target_node_id AND projection_id=e.app_target_projection_id
         AND node_type='condition'));
  ELSIF e.node_type='rule_ref' THEN
    RETURN result||jsonb_build_object('ruleKey',(
      SELECT node_key FROM ad_v4_candidate_app_semantic_nodes
       WHERE id=e.app_target_node_id AND projection_id=e.app_target_projection_id
         AND node_type='applicability_rule'));
  ELSIF e.node_type='requirement_state_ref' THEN
    RETURN result||jsonb_build_object(
      'requirementKey',(SELECT requirement_key
        FROM ad_v4_candidate_obligation_requirements
       WHERE semantic_node_id=e.requirement_target_node_id
         AND projection_id=p_projection_id),
      'requirementState',e.required_state);
  ELSIF e.node_type='not' THEN
    RETURN result||jsonb_build_object('operand',(
      SELECT paprnav_v4_obligation_expression_json(
        p_projection_id,child_expression_id)
        FROM ad_v4_candidate_obligation_expression_edges
       WHERE projection_id=p_projection_id
         AND parent_expression_id=p_expression_node_id
       ORDER BY canonical_ordinal LIMIT 1));
  END IF;
  RETURN result||jsonb_build_object('operands',(
    SELECT coalesce(jsonb_agg(
      paprnav_v4_obligation_expression_json(p_projection_id,child_expression_id)
      ORDER BY canonical_ordinal),'[]'::jsonb)
      FROM ad_v4_candidate_obligation_expression_edges
     WHERE projection_id=p_projection_id
       AND parent_expression_id=p_expression_node_id));
END; $$ LANGUAGE plpgsql STABLE STRICT;

CREATE OR REPLACE FUNCTION paprnav_v4_obligation_timing_json(
  p_projection_id text, p_timing_node_id text
) RETURNS jsonb AS $$
DECLARE t ad_v4_candidate_obligation_timing_groups%ROWTYPE;
BEGIN
  SELECT * INTO STRICT t FROM ad_v4_candidate_obligation_timing_groups
   WHERE projection_id=p_projection_id AND semantic_node_id=p_timing_node_id;
  IF t.state='known' THEN
    RETURN jsonb_build_object(
      'logic',t.logic,
      'terms',(SELECT coalesce(jsonb_agg(jsonb_build_object(
        'metric',term.metric,'interval',term.interval_text,'unit',term.unit,
        'comparator',term.comparator,'anchor',term.anchor,
        'evidenceKeys',paprnav_v4_obligation_evidence_json(
          p_projection_id,term.semantic_node_id))
        ORDER BY term.canonical_ordinal),'[]'::jsonb)
        FROM ad_v4_candidate_obligation_timing_terms term
       WHERE term.projection_id=p_projection_id
         AND term.timing_group_node_id=p_timing_node_id),
      'evidenceKeys',paprnav_v4_obligation_evidence_json(
        p_projection_id,p_timing_node_id));
  END IF;
  RETURN jsonb_build_object(
    'state',t.state,'reason',t.reason,
    'temporalScope',jsonb_build_object('kind',t.temporal_kind),
    'evidenceKeys',paprnav_v4_obligation_evidence_json(
      p_projection_id,p_timing_node_id));
END; $$ LANGUAGE plpgsql STABLE STRICT;

CREATE OR REPLACE FUNCTION paprnav_v4_obligation_action_json(
  p_projection_id text, p_action_node_id text
) RETURNS jsonb AS $$
DECLARE a ad_v4_candidate_obligation_actions%ROWTYPE; result jsonb;
BEGIN
  SELECT * INTO STRICT a FROM ad_v4_candidate_obligation_actions
   WHERE projection_id=p_projection_id AND semantic_node_id=p_action_node_id;
  result:=jsonb_build_object(
    'actionType',a.action_type,
    'approvedDataDocumentRefKeys',(SELECT coalesce(jsonb_agg(
      to_jsonb(document_ref_key) ORDER BY canonical_ordinal),'[]'::jsonb)
      FROM ad_v4_candidate_obligation_action_document_refs
     WHERE projection_id=p_projection_id AND action_node_id=p_action_node_id),
    'evidenceKeys',paprnav_v4_obligation_evidence_json(
      p_projection_id,p_action_node_id));
  IF a.ordered_steps_present THEN
    result:=result||jsonb_build_object('orderedSteps',(
      SELECT coalesce(jsonb_agg(to_jsonb(step_text) ORDER BY canonical_ordinal),'[]'::jsonb)
        FROM ad_v4_candidate_obligation_action_steps
       WHERE projection_id=p_projection_id AND action_node_id=p_action_node_id));
  END IF;
  RETURN result;
END; $$ LANGUAGE plpgsql STABLE STRICT;

CREATE OR REPLACE FUNCTION paprnav_v4_obligation_branch_json(
  p_projection_id text, p_branch_node_id text
) RETURNS jsonb AS $$
DECLARE b ad_v4_candidate_obligation_branches%ROWTYPE; result jsonb;
BEGIN
  SELECT * INTO STRICT b FROM ad_v4_candidate_obligation_branches
   WHERE projection_id=p_projection_id AND semantic_node_id=p_branch_node_id;
  result:=jsonb_build_object(
    'kind',b.kind,'evidenceKeys',paprnav_v4_obligation_evidence_json(
      p_projection_id,p_branch_node_id));
  IF b.kind IN ('conditional','exception') THEN
    result:=result||jsonb_build_object(
      'conditionExpression',paprnav_v4_obligation_expression_json(
        p_projection_id,b.condition_root_node_id));
  ELSIF b.kind='alternative_member' THEN
    result:=result||jsonb_build_object(
      'alternativeGroupKey',b.alternative_group_key,'exclusive',b.exclusive);
  END IF;
  RETURN result;
END; $$ LANGUAGE plpgsql STABLE STRICT;

CREATE OR REPLACE FUNCTION paprnav_v4_obligation_recurrence_json(
  p_projection_id text, p_recurrence_node_id text
) RETURNS jsonb AS $$
DECLARE r ad_v4_candidate_obligation_recurrences%ROWTYPE; result jsonb;
BEGIN
  SELECT * INTO STRICT r FROM ad_v4_candidate_obligation_recurrences
   WHERE projection_id=p_projection_id AND semantic_node_id=p_recurrence_node_id;
  result:=jsonb_build_object(
    'kind',r.kind,'evidenceKeys',paprnav_v4_obligation_evidence_json(
      p_projection_id,p_recurrence_node_id));
  IF r.kind IN ('interval','conditioned') THEN
    result:=result||jsonb_build_object(
      'timing',paprnav_v4_obligation_timing_json(
        p_projection_id,r.timing_node_id));
  END IF;
  IF r.kind='conditioned' THEN
    result:=result||jsonb_build_object(
      'conditionExpression',paprnav_v4_obligation_expression_json(
        p_projection_id,r.condition_root_node_id));
  ELSIF r.kind='unknown' THEN
    result:=result||jsonb_build_object(
      'reason',r.reason,
      'temporalScope',jsonb_build_object('kind',r.temporal_kind));
  END IF;
  RETURN result;
END; $$ LANGUAGE plpgsql STABLE STRICT;

CREATE OR REPLACE FUNCTION paprnav_v4_candidate_obligation_typed_subtree(
  p_projection_id text
) RETURNS jsonb AS $$
DECLARE documents jsonb; requirements jsonb; groups jsonb; provisions jsonb;
BEGIN
  SELECT coalesce(jsonb_agg(jsonb_build_object(
    'documentRefKey',d.document_ref_key,'documentType',d.document_type,
    'documentNumber',paprnav_v4_obligation_assertion_json(
      p_projection_id,d.document_number_node_id),
    'revision',paprnav_v4_obligation_assertion_json(
      p_projection_id,d.revision_node_id),
    'retention',paprnav_v4_obligation_assertion_json(
      p_projection_id,d.retention_node_id),
    'evidenceKeys',paprnav_v4_obligation_evidence_json(
      p_projection_id,d.semantic_node_id)) ORDER BY d.canonical_ordinal),'[]'::jsonb)
    INTO documents FROM ad_v4_candidate_obligation_documents d
   WHERE d.projection_id=p_projection_id;

  SELECT coalesce(jsonb_agg(
    jsonb_build_object(
      'requirementKey',q.requirement_key,'sequence',q.sequence_text,
      'activationExpression',paprnav_v4_obligation_expression_json(
        p_projection_id,q.activation_root_node_id),
      'requirementType',q.requirement_type,
      'action',paprnav_v4_obligation_action_json(p_projection_id,q.action_node_id),
      'prerequisiteRequirementKeys',(SELECT coalesce(jsonb_agg(
        to_jsonb(prerequisite_requirement_key) ORDER BY canonical_ordinal),'[]'::jsonb)
        FROM ad_v4_candidate_obligation_requirement_dependencies
       WHERE projection_id=p_projection_id AND requirement_node_id=q.semantic_node_id),
      'branch',paprnav_v4_obligation_branch_json(p_projection_id,q.branch_node_id),
      'initialTiming',paprnav_v4_obligation_timing_json(
        p_projection_id,q.initial_timing_node_id),
      'recurrence',paprnav_v4_obligation_recurrence_json(
        p_projection_id,q.recurrence_node_id),
      'terminatingEffect',(SELECT jsonb_build_object(
        'kind',effect.kind,
        'evidenceKeys',paprnav_v4_obligation_evidence_json(
          p_projection_id,effect.semantic_node_id))
        ||CASE WHEN effect.kind='terminates' THEN jsonb_build_object(
          'requirementKeys',(SELECT coalesce(jsonb_agg(
            to_jsonb(terminated_requirement_key) ORDER BY canonical_ordinal),'[]'::jsonb)
            FROM ad_v4_candidate_obligation_termination_edges
           WHERE projection_id=p_projection_id
             AND effect_node_id=effect.semantic_node_id))
          ELSE '{}'::jsonb END
        FROM ad_v4_candidate_obligation_terminating_effects effect
       WHERE effect.projection_id=p_projection_id
         AND effect.semantic_node_id=q.terminating_effect_node_id),
      'evidenceKeys',paprnav_v4_obligation_evidence_json(
        p_projection_id,q.semantic_node_id))
    ||CASE WHEN q.recurrence_group_present
      THEN jsonb_build_object('recurrenceGroupKey',q.recurrence_group_key)
      ELSE '{}'::jsonb END
    ORDER BY q.canonical_ordinal),'[]'::jsonb)
    INTO requirements FROM ad_v4_candidate_obligation_requirements q
   WHERE q.projection_id=p_projection_id;

  SELECT coalesce(jsonb_agg(jsonb_build_object(
    'recurrenceGroupKey',g.recurrence_group_key,
    'requirementKeys',(SELECT coalesce(jsonb_agg(
      to_jsonb(requirement_key) ORDER BY canonical_ordinal),'[]'::jsonb)
      FROM ad_v4_candidate_obligation_recurrence_group_members
     WHERE projection_id=p_projection_id AND group_node_id=g.semantic_node_id),
    'completionPolicy',g.completion_policy,
    'initialTiming',paprnav_v4_obligation_timing_json(
      p_projection_id,g.initial_timing_node_id),
    'recurringTiming',paprnav_v4_obligation_timing_json(
      p_projection_id,g.recurring_timing_node_id),
    'evidenceKeys',paprnav_v4_obligation_evidence_json(
      p_projection_id,g.semantic_node_id)) ORDER BY g.canonical_ordinal),'[]'::jsonb)
    INTO groups FROM ad_v4_candidate_obligation_recurrence_groups g
   WHERE g.projection_id=p_projection_id;

  SELECT coalesce(jsonb_agg(jsonb_build_object(
    'provisionKey',a.provision_key,
    'approvingAuthority',paprnav_v4_obligation_assertion_json(
      p_projection_id,a.authority_assertion_node_id),
    'evidenceKeys',paprnav_v4_obligation_evidence_json(
      p_projection_id,a.semantic_node_id)) ORDER BY a.canonical_ordinal),'[]'::jsonb)
    INTO provisions FROM ad_v4_candidate_obligation_amoc_provisions a
   WHERE a.projection_id=p_projection_id;

  RETURN jsonb_build_object(
    'incorporatedDocuments',documents,'requirements',requirements,
    'recurrenceGroups',groups,'amocAuthorityProvisions',provisions);
END; $$ LANGUAGE plpgsql STABLE STRICT;

CREATE OR REPLACE FUNCTION paprnav_v4_obligation_datum_json(
  p_projection_id text, p_pointer text
) RETURNS jsonb AS $$
DECLARE d ad_v4_candidate_obligation_data%ROWTYPE; result jsonb;
BEGIN
  SELECT * INTO STRICT d FROM ad_v4_candidate_obligation_data
   WHERE projection_id=p_projection_id AND json_pointer=p_pointer;
  IF d.value_kind='string' THEN RETURN to_jsonb(d.string_value); END IF;
  IF d.value_kind='boolean' THEN RETURN to_jsonb(d.boolean_value); END IF;
  IF d.value_kind='array' THEN
    SELECT coalesce(jsonb_agg(paprnav_v4_obligation_datum_json(
      p_projection_id,child.json_pointer) ORDER BY child.array_ordinal),'[]'::jsonb)
      INTO result FROM ad_v4_candidate_obligation_data child
     WHERE child.projection_id=p_projection_id
       AND child.parent_pointer=p_pointer;
    RETURN result;
  END IF;
  SELECT coalesce(jsonb_object_agg(child.property_name,
    paprnav_v4_obligation_datum_json(p_projection_id,child.json_pointer)),'{}'::jsonb)
    INTO result FROM ad_v4_candidate_obligation_data child
   WHERE child.projection_id=p_projection_id AND child.parent_pointer=p_pointer;
  RETURN result;
END; $$ LANGUAGE plpgsql STABLE STRICT;

CREATE OR REPLACE FUNCTION paprnav_v4_obligation_semantic_expected(
  p_subtree jsonb, p_pointer text
) RETURNS jsonb AS $$
DECLARE
  value jsonb; node_type text; node_key text; parent_pointer text;
  canonical_ordinal integer; purpose text; evidence_keys jsonb;
BEGIN
  value:=paprnav_v4_pointer_value(p_subtree,p_pointer);
  IF value IS NULL THEN RETURN NULL; END IF;

  IF jsonb_typeof(value)='object'
     AND value->>'nodeType' IN (
       'scope_ref','predicate_ref','rule_ref','requirement_state_ref',
       'not','all','any') THEN
    node_type:='expression'; node_key:=p_pointer; purpose:=NULL;
    evidence_keys:='[]'::jsonb;
    IF p_pointer ~ '/activationExpression$' THEN
      parent_pointer:=regexp_replace(p_pointer,'/activationExpression$','');
      canonical_ordinal:=1;
    ELSIF p_pointer ~ '/branch/conditionExpression$' THEN
      parent_pointer:=regexp_replace(p_pointer,'/conditionExpression$','');
      canonical_ordinal:=0;
    ELSIF p_pointer ~ '/recurrence/conditionExpression$' THEN
      parent_pointer:=regexp_replace(p_pointer,'/conditionExpression$','');
      canonical_ordinal:=0;
    ELSIF p_pointer ~ '/operand$' THEN
      parent_pointer:=regexp_replace(p_pointer,'/operand$','');
      canonical_ordinal:=0;
    ELSIF p_pointer ~ '/operands/[0-9]+$' THEN
      parent_pointer:=regexp_replace(p_pointer,'/operands/[0-9]+$','');
      canonical_ordinal:=regexp_replace(p_pointer,'^.*/','')::integer;
    ELSE RETURN NULL; END IF;
  ELSIF p_pointer ~ '^/incorporatedDocuments/[0-9]+$' THEN
    node_type:='incorporated_document'; node_key:=value->>'documentRefKey';
    parent_pointer:=NULL; canonical_ordinal:=regexp_replace(p_pointer,'^.*/','')::integer;
    purpose:='incorporated_document_clause'; evidence_keys:=value->'evidenceKeys';
  ELSIF p_pointer ~ '^/incorporatedDocuments/[0-9]+/(documentNumber|revision|retention)$' THEN
    node_type:='value_assertion'; node_key:=p_pointer;
    parent_pointer:=regexp_replace(p_pointer,'/[^/]+$','');
    canonical_ordinal:=CASE regexp_replace(p_pointer,'^.*/','')
      WHEN 'documentNumber' THEN 0 WHEN 'revision' THEN 1 ELSE 2 END;
    purpose:=CASE WHEN p_pointer ~ '/retention$'
      THEN 'document_retention' ELSE 'document_identity' END;
    evidence_keys:=value->'evidenceKeys';
  ELSIF p_pointer ~ '^/requirements/[0-9]+$' THEN
    node_type:='requirement'; node_key:=value->>'requirementKey';
    parent_pointer:=NULL; canonical_ordinal:=regexp_replace(p_pointer,'^.*/','')::integer;
    purpose:='requirement_clause'; evidence_keys:=value->'evidenceKeys';
  ELSIF p_pointer ~ '^/requirements/[0-9]+/action$' THEN
    node_type:='action'; node_key:=p_pointer;
    parent_pointer:=regexp_replace(p_pointer,'/action$',''); canonical_ordinal:=0;
    purpose:='action_clause'; evidence_keys:=value->'evidenceKeys';
  ELSIF p_pointer ~ '^/requirements/[0-9]+/action/orderedSteps/[0-9]+$' THEN
    node_type:='action_step'; node_key:=p_pointer;
    parent_pointer:=regexp_replace(p_pointer,'/orderedSteps/[0-9]+$','');
    canonical_ordinal:=regexp_replace(p_pointer,'^.*/','')::integer;
    purpose:=NULL; evidence_keys:='[]'::jsonb;
  ELSIF p_pointer ~ '^/requirements/[0-9]+/branch$' THEN
    node_type:='branch'; node_key:=p_pointer;
    parent_pointer:=regexp_replace(p_pointer,'/branch$',''); canonical_ordinal:=2;
    purpose:='branch_clause'; evidence_keys:=value->'evidenceKeys';
  ELSIF p_pointer ~ '^/requirements/[0-9]+/initialTiming$' THEN
    node_type:='timing_group'; node_key:=p_pointer;
    parent_pointer:=regexp_replace(p_pointer,'/initialTiming$',''); canonical_ordinal:=3;
    purpose:='timing_clause'; evidence_keys:=value->'evidenceKeys';
  ELSIF p_pointer ~ '^/requirements/[0-9]+/initialTiming/terms/[0-9]+$'
     OR p_pointer ~ '^/requirements/[0-9]+/recurrence/timing/terms/[0-9]+$'
     OR p_pointer ~ '^/recurrenceGroups/[0-9]+/(initialTiming|recurringTiming)/terms/[0-9]+$' THEN
    node_type:='timing_term'; node_key:=p_pointer;
    parent_pointer:=regexp_replace(p_pointer,'/terms/[0-9]+$','');
    canonical_ordinal:=regexp_replace(p_pointer,'^.*/','')::integer;
    purpose:='timing_term_clause'; evidence_keys:=value->'evidenceKeys';
  ELSIF p_pointer ~ '^/requirements/[0-9]+/recurrence$' THEN
    node_type:='recurrence'; node_key:=p_pointer;
    parent_pointer:=regexp_replace(p_pointer,'/recurrence$',''); canonical_ordinal:=4;
    purpose:='recurrence_clause'; evidence_keys:=value->'evidenceKeys';
  ELSIF p_pointer ~ '^/requirements/[0-9]+/recurrence/timing$' THEN
    node_type:='timing_group'; node_key:=p_pointer;
    parent_pointer:=regexp_replace(p_pointer,'/timing$',''); canonical_ordinal:=1;
    purpose:='timing_clause'; evidence_keys:=value->'evidenceKeys';
  ELSIF p_pointer ~ '^/requirements/[0-9]+/terminatingEffect$' THEN
    node_type:='terminating_effect'; node_key:=p_pointer;
    parent_pointer:=regexp_replace(p_pointer,'/terminatingEffect$',''); canonical_ordinal:=5;
    purpose:='termination_clause'; evidence_keys:=value->'evidenceKeys';
  ELSIF p_pointer ~ '^/recurrenceGroups/[0-9]+$' THEN
    node_type:='recurrence_group'; node_key:=value->>'recurrenceGroupKey';
    parent_pointer:=NULL; canonical_ordinal:=regexp_replace(p_pointer,'^.*/','')::integer;
    purpose:='recurrence_clause'; evidence_keys:=value->'evidenceKeys';
  ELSIF p_pointer ~ '^/recurrenceGroups/[0-9]+/(initialTiming|recurringTiming)$' THEN
    node_type:='timing_group'; node_key:=p_pointer;
    parent_pointer:=regexp_replace(p_pointer,'/(initialTiming|recurringTiming)$','');
    canonical_ordinal:=CASE WHEN p_pointer ~ '/initialTiming$' THEN 0 ELSE 1 END;
    purpose:='timing_clause'; evidence_keys:=value->'evidenceKeys';
  ELSIF p_pointer ~ '^/amocAuthorityProvisions/[0-9]+$' THEN
    node_type:='amoc_provision'; node_key:=value->>'provisionKey';
    parent_pointer:=NULL; canonical_ordinal:=regexp_replace(p_pointer,'^.*/','')::integer;
    purpose:='amoc_authority_clause'; evidence_keys:=value->'evidenceKeys';
  ELSIF p_pointer ~ '^/amocAuthorityProvisions/[0-9]+/approvingAuthority$' THEN
    node_type:='value_assertion'; node_key:=p_pointer;
    parent_pointer:=regexp_replace(p_pointer,'/approvingAuthority$',''); canonical_ordinal:=0;
    purpose:='amoc_authority_clause'; evidence_keys:=value->'evidenceKeys';
  ELSE RETURN NULL; END IF;

  RETURN jsonb_build_object(
    'nodeType',node_type,'nodeKey',node_key,'parentPointer',parent_pointer,
    'canonicalOrdinal',canonical_ordinal,'purpose',purpose,
    'evidenceKeys',evidence_keys);
END; $$ LANGUAGE plpgsql IMMUTABLE STRICT;

CREATE OR REPLACE FUNCTION paprnav_v4_candidate_obligation_require_complete(
  p_projection_id text
) RETURNS void AS $$
DECLARE
  projection ad_v4_candidate_obligation_projections%ROWTYPE;
  proposal ad_v4_candidate_proposals%ROWTYPE;
  app_projection ad_v4_candidate_app_projections%ROWTYPE;
  subtree jsonb; envelope jsonb; expected_hash text; node record;
  expected_semantic_count integer; owner_count integer; owner_type text;
  semantic_expected jsonb; expected_parent_id text; actual_evidence jsonb;
  binding_set jsonb; binding_set_hash text; request_row record; event_row record;
  request_value jsonb; claims_value jsonb; event_value jsonb;
BEGIN
  -- Read immutable routing identity without locking it, then take the shared
  -- proposal/gate prefix in the same order as both supported materializers and
  -- the direct-request guard. Re-lock the root before using its payload.
  SELECT * INTO projection FROM ad_v4_candidate_obligation_projections
   WHERE id=p_projection_id;
  IF projection.id IS NULL THEN
    RAISE EXCEPTION 'V4 obligation projection is missing';
  END IF;
  SELECT * INTO proposal FROM ad_v4_candidate_proposals
   WHERE id=projection.proposal_id FOR SHARE;
  PERFORM gate_key FROM ad_v4_feature_gates
   WHERE gate_key IN (
     'validator2_write_enabled','materializer3a_enabled','materializer3b_enabled')
   ORDER BY CASE gate_key
     WHEN 'validator2_write_enabled' THEN 1
     WHEN 'materializer3a_enabled' THEN 2 ELSE 3 END
   FOR SHARE;
  SELECT * INTO projection FROM ad_v4_candidate_obligation_projections
   WHERE id=p_projection_id FOR SHARE;
  SELECT * INTO app_projection FROM ad_v4_candidate_app_projections
   WHERE id=projection.app_projection_id FOR SHARE;
  IF proposal.id IS NULL OR app_projection.id IS NULL
     OR app_projection.proposal_id<>proposal.id
     OR projection.directive_id<>proposal.directive_id
     OR projection.validator_version<>'paprnav-ad-v4-validator-2'
     OR projection.canonicalization_version<>'paprnav-ad-v4-c14n-2'
     OR proposal.validator_version<>projection.validator_version
     OR proposal.canonicalization_version<>projection.canonicalization_version
     OR projection.proposal_canonical_hash<>proposal.canonical_hash
     OR projection.evidence_binding_hash<>proposal.evidence_binding_hash
     OR projection.app_projection_hash<>app_projection.projection_hash
     OR projection.app_materializer_version<>app_projection.materializer_version
     OR projection.app_materializer_version<>'paprnav-ad-v4-app-materializer-2'
     OR projection.materializer_version<>'paprnav-ad-v4-obligation-materializer-1'
     OR projection.mapping_version<>'paprnav-ad-v4-obligation-mapping-1'
     OR projection.mapping_digest<>paprnav_v4_obligation_mapping_digest()
     OR projection.gate<>'candidate_only'
     OR (SELECT count(*) FROM ad_v4_feature_gates
          WHERE gate_key IN (
            'validator2_write_enabled','materializer3a_enabled','materializer3b_enabled')
            AND enabled)<>3
  THEN RAISE EXCEPTION 'V4 obligation projection parent/envelope differs'; END IF;
  PERFORM paprnav_v4_candidate_app_require_complete(app_projection.id);

  subtree:=jsonb_build_object(
    'incorporatedDocuments',proposal.parsed_json::jsonb->'incorporatedDocuments',
    'requirements',proposal.parsed_json::jsonb->'requirements',
    'recurrenceGroups',proposal.parsed_json::jsonb->'recurrenceGroups',
    'amocAuthorityProvisions',proposal.parsed_json::jsonb->'amocAuthorityProvisions');
  expected_hash:=encode(sha256(
    convert_to('paprnav:ad_extraction_v4:obligation-subtree:paprnav-ad-v4-c14n-2','UTF8')
    ||decode('00','hex')||convert_to(paprnav_v4_obligation_record(subtree),'UTF8')),'hex');
  IF projection.obligation_subtree_bytes<>convert_to(
       paprnav_v4_obligation_record(subtree),'UTF8')
     OR projection.obligation_subtree_hash<>expected_hash
  THEN RAISE EXCEPTION 'V4 obligation subtree bytes/hash differ'; END IF;

  IF (SELECT count(*) FROM ad_v4_candidate_obligation_semantic_nodes WHERE projection_id=projection.id)<>projection.semantic_node_count
     OR (SELECT count(*) FROM ad_v4_candidate_obligation_data WHERE projection_id=projection.id)<>projection.datum_count
     OR (SELECT count(*) FROM ad_v4_candidate_obligation_evidence_links WHERE projection_id=projection.id)<>projection.evidence_link_count
     OR (SELECT count(*) FROM ad_v4_candidate_obligation_documents WHERE projection_id=projection.id)<>projection.document_count
     OR (SELECT count(*) FROM ad_v4_candidate_obligation_value_assertions WHERE projection_id=projection.id)<>projection.value_assertion_count
     OR (SELECT count(*) FROM ad_v4_candidate_obligation_requirements WHERE projection_id=projection.id)<>projection.requirement_count
     OR (SELECT count(*) FROM ad_v4_candidate_obligation_actions WHERE projection_id=projection.id)<>projection.action_count
     OR (SELECT count(*) FROM ad_v4_candidate_obligation_action_steps WHERE projection_id=projection.id)<>projection.action_step_count
     OR (SELECT count(*) FROM ad_v4_candidate_obligation_action_document_refs WHERE projection_id=projection.id)<>projection.action_document_ref_count
     OR (SELECT count(*) FROM ad_v4_candidate_obligation_branches WHERE projection_id=projection.id)<>projection.branch_count
     OR (SELECT count(*) FROM ad_v4_candidate_obligation_expressions WHERE projection_id=projection.id)<>projection.expression_count
     OR (SELECT count(*) FROM ad_v4_candidate_obligation_expression_edges WHERE projection_id=projection.id)<>projection.expression_edge_count
     OR (SELECT count(*) FROM ad_v4_candidate_obligation_requirement_dependencies WHERE projection_id=projection.id)<>projection.requirement_dependency_count
     OR (SELECT count(*) FROM ad_v4_candidate_obligation_timing_groups WHERE projection_id=projection.id)<>projection.timing_group_count
     OR (SELECT count(*) FROM ad_v4_candidate_obligation_timing_terms WHERE projection_id=projection.id)<>projection.timing_term_count
     OR (SELECT count(*) FROM ad_v4_candidate_obligation_recurrences WHERE projection_id=projection.id)<>projection.recurrence_count
     OR (SELECT count(*) FROM ad_v4_candidate_obligation_terminating_effects WHERE projection_id=projection.id)<>projection.terminating_effect_count
     OR (SELECT count(*) FROM ad_v4_candidate_obligation_termination_edges WHERE projection_id=projection.id)<>projection.termination_edge_count
     OR (SELECT count(*) FROM ad_v4_candidate_obligation_recurrence_groups WHERE projection_id=projection.id)<>projection.recurrence_group_count
     OR (SELECT count(*) FROM ad_v4_candidate_obligation_recurrence_group_members WHERE projection_id=projection.id)<>projection.recurrence_group_member_count
     OR (SELECT count(*) FROM ad_v4_candidate_obligation_amoc_provisions WHERE projection_id=projection.id)<>projection.amoc_provision_count
     OR (SELECT count(*) FROM ad_v4_candidate_correction_semantic_bindings WHERE obligation_projection_id=projection.id)<>projection.correction_binding_count
  THEN RAISE EXCEPTION 'V4 obligation structural counts differ'; END IF;

  IF EXISTS (
    WITH expected AS (SELECT * FROM paprnav_v4_json_nodes(subtree)),
    actual AS (SELECT * FROM ad_v4_candidate_obligation_data WHERE projection_id=projection.id)
    SELECT 1 FROM expected e FULL JOIN actual a USING (json_pointer)
     WHERE e.json_pointer IS NULL OR a.json_pointer IS NULL
        OR e.parent_pointer IS DISTINCT FROM a.parent_pointer
        OR e.property_name IS DISTINCT FROM a.property_name
        OR e.array_ordinal IS DISTINCT FROM a.array_ordinal
        OR e.value_kind IS DISTINCT FROM a.value_kind
        OR e.string_value IS DISTINCT FROM a.string_value
        OR e.boolean_value IS DISTINCT FROM a.boolean_value)
     OR paprnav_v4_obligation_datum_json(projection.id,'') IS DISTINCT FROM subtree
  THEN RAISE EXCEPTION 'V4 obligation generic datum graph differs'; END IF;

  SELECT count(*) INTO expected_semantic_count
    FROM paprnav_v4_obligation_select_occurrences(subtree)
   WHERE occurrence_id NOT IN ('EACT','EBR','EREC');
  SELECT expected_semantic_count+count(*) INTO expected_semantic_count
    FROM paprnav_v4_json_nodes(subtree) walked
   WHERE jsonb_typeof(paprnav_v4_pointer_value(subtree,walked.json_pointer))='object'
     AND paprnav_v4_pointer_value(subtree,walked.json_pointer) ? 'nodeType';
  IF expected_semantic_count<>projection.semantic_node_count
  THEN RAISE EXCEPTION 'V4 obligation semantic-node count differs from source'; END IF;

  FOR node IN SELECT * FROM ad_v4_candidate_obligation_semantic_nodes
    WHERE projection_id=projection.id LOOP
    semantic_expected:=paprnav_v4_obligation_semantic_expected(
      subtree,node.source_pointer);
    expected_parent_id:=NULL;
    IF semantic_expected->>'parentPointer' IS NOT NULL THEN
      SELECT id INTO expected_parent_id
        FROM ad_v4_candidate_obligation_semantic_nodes
       WHERE projection_id=projection.id
         AND source_pointer=semantic_expected->>'parentPointer';
    END IF;
    expected_hash:=encode(sha256(convert_to(paprnav_v4_obligation_record(
      paprnav_v4_pointer_value(subtree,node.source_pointer)),'UTF8')),'hex');
    IF semantic_expected IS NULL
       OR semantic_expected->>'nodeType' IS DISTINCT FROM node.node_type
       OR semantic_expected->>'nodeKey' IS DISTINCT FROM node.node_key
       OR (semantic_expected->>'canonicalOrdinal')::integer
          IS DISTINCT FROM node.canonical_ordinal
       OR expected_parent_id IS DISTINCT FROM node.parent_node_id
       OR node.canonical_node_hash<>expected_hash
       OR node.identity_hash<>encode(sha256(
         convert_to('paprnav:ad_extraction_v4:obligation-row:1','UTF8')||decode('00','hex')||
         convert_to(paprnav_v4_obligation_record(jsonb_build_object(
           'table','semantic-node','identity',jsonb_build_object(
             'projectionId',projection.id,'nodeType',node.node_type,
             'nodeKey',node.node_key,'pointer',node.source_pointer))),'UTF8')),'hex')
       OR node.id<>'aon_'||substr(node.identity_hash,1,32)
    THEN RAISE EXCEPTION 'V4 obligation semantic-node identity/hash differs'; END IF;
    SELECT count(*),min(owners.node_type) INTO owner_count,owner_type FROM (
      SELECT semantic_node_id,'incorporated_document' AS node_type FROM ad_v4_candidate_obligation_documents WHERE projection_id=projection.id
      UNION ALL SELECT semantic_node_id,'value_assertion' FROM ad_v4_candidate_obligation_value_assertions WHERE projection_id=projection.id
      UNION ALL SELECT semantic_node_id,'requirement' FROM ad_v4_candidate_obligation_requirements WHERE projection_id=projection.id
      UNION ALL SELECT semantic_node_id,'action' FROM ad_v4_candidate_obligation_actions WHERE projection_id=projection.id
      UNION ALL SELECT semantic_node_id,'action_step' FROM ad_v4_candidate_obligation_action_steps WHERE projection_id=projection.id
      UNION ALL SELECT semantic_node_id,'branch' FROM ad_v4_candidate_obligation_branches WHERE projection_id=projection.id
      UNION ALL SELECT semantic_node_id,'expression' FROM ad_v4_candidate_obligation_expressions WHERE projection_id=projection.id
      UNION ALL SELECT semantic_node_id,'timing_group' FROM ad_v4_candidate_obligation_timing_groups WHERE projection_id=projection.id
      UNION ALL SELECT semantic_node_id,'timing_term' FROM ad_v4_candidate_obligation_timing_terms WHERE projection_id=projection.id
      UNION ALL SELECT semantic_node_id,'recurrence' FROM ad_v4_candidate_obligation_recurrences WHERE projection_id=projection.id
      UNION ALL SELECT semantic_node_id,'terminating_effect' FROM ad_v4_candidate_obligation_terminating_effects WHERE projection_id=projection.id
      UNION ALL SELECT semantic_node_id,'recurrence_group' FROM ad_v4_candidate_obligation_recurrence_groups WHERE projection_id=projection.id
      UNION ALL SELECT semantic_node_id,'amoc_provision' FROM ad_v4_candidate_obligation_amoc_provisions WHERE projection_id=projection.id
    ) owners WHERE owners.semantic_node_id=node.id;
    IF owner_count<>1 OR owner_type IS DISTINCT FROM node.node_type THEN
      RAISE EXCEPTION 'V4 obligation semantic exactly-one-owner union differs';
    END IF;
    SELECT coalesce(jsonb_agg(to_jsonb(e.evidence_key)
      ORDER BY e.canonical_ordinal),'[]'::jsonb) INTO actual_evidence
      FROM ad_v4_candidate_obligation_evidence_links e
     WHERE e.projection_id=projection.id AND e.semantic_node_id=node.id;
    IF actual_evidence IS DISTINCT FROM semantic_expected->'evidenceKeys'
       OR EXISTS (
         SELECT 1 FROM ad_v4_candidate_obligation_evidence_links e
          WHERE e.projection_id=projection.id AND e.semantic_node_id=node.id
            AND (e.purpose IS DISTINCT FROM semantic_expected->>'purpose'
              OR e.link_hash<>encode(sha256(
                convert_to('paprnav:ad_extraction_v4:obligation-row:1','UTF8')
                ||decode('00','hex')||convert_to(paprnav_v4_obligation_record(
                  jsonb_build_object('table','evidence-link','identity',
                    jsonb_build_object(
                      'projectionId',projection.id,
                      'semanticNodeId',node.id,'purpose',e.purpose,
                      'evidenceKey',e.evidence_key,
                      'ordinal',e.canonical_ordinal))),'UTF8')),'hex')
              OR e.id<>'aoe_'||substr(e.link_hash,1,32)))
    THEN RAISE EXCEPTION 'V4 obligation evidence ownership/hash differs'; END IF;
  END LOOP;

  IF EXISTS (
    SELECT 1 FROM (
      SELECT canonical_ordinal,
        row_number() OVER (
          PARTITION BY semantic_node_id,purpose ORDER BY canonical_ordinal)-1 AS expected
        FROM ad_v4_candidate_obligation_evidence_links
       WHERE projection_id=projection.id
    ) ordered WHERE canonical_ordinal<>expected
  ) THEN RAISE EXCEPTION 'V4 obligation evidence ordinal sequence differs'; END IF;

  IF EXISTS (
    SELECT 1 FROM ad_v4_candidate_obligation_data d
    LEFT JOIN LATERAL (
      SELECT n.id FROM ad_v4_candidate_obligation_semantic_nodes n
       WHERE n.projection_id=projection.id
         AND (n.source_pointer=d.json_pointer
           OR (n.source_pointer<>'' AND left(
             d.json_pointer,length(n.source_pointer)+1)=n.source_pointer||'/'))
       ORDER BY length(n.source_pointer) DESC LIMIT 1
    ) owner ON TRUE
    WHERE d.projection_id=projection.id AND (
      d.semantic_node_id IS DISTINCT FROM owner.id
      OR d.identity_hash<>encode(sha256(
        convert_to('paprnav:ad_extraction_v4:obligation-row:1','UTF8')
        ||decode('00','hex')||convert_to(paprnav_v4_obligation_record(
          jsonb_build_object('table','datum','identity',jsonb_build_object(
            'projectionId',projection.id,'pointer',d.json_pointer,
            'kind',d.value_kind,'value',CASE d.value_kind
              WHEN 'string' THEN to_jsonb(d.string_value)
              WHEN 'boolean' THEN to_jsonb(d.boolean_value)
              ELSE to_jsonb(d.value_kind) END))),'UTF8')),'hex')
      OR d.value_hash<>d.identity_hash
      OR d.id<>'aod_'||substr(d.identity_hash,1,32)))
  THEN RAISE EXCEPTION 'V4 obligation datum ownership/identity/hash differs'; END IF;

  IF EXISTS (
    WITH relationships AS (
      SELECT id,identity_hash,'aor'::text AS prefix,
        jsonb_build_object('table','action-document-ref','identity',
          jsonb_build_object('projectionId',projection_id,
            'actionNodeId',action_node_id,'documentNodeId',document_node_id,
            'ordinal',canonical_ordinal)) AS record
        FROM ad_v4_candidate_obligation_action_document_refs
       WHERE projection_id=projection.id
      UNION ALL
      SELECT id,identity_hash,'aog',
        jsonb_build_object('table','expression-edge','identity',
          jsonb_build_object('projectionId',projection_id,
            'requirementNodeId',requirement_node_id,'context',context,
            'parentExpressionId',parent_expression_id,
            'childExpressionId',child_expression_id,
            'ordinal',canonical_ordinal))
        FROM ad_v4_candidate_obligation_expression_edges
       WHERE projection_id=projection.id
      UNION ALL
      SELECT id,identity_hash,'aop',
        jsonb_build_object('table','requirement-dependency','identity',
          jsonb_build_object('projectionId',projection_id,
            'requirementNodeId',requirement_node_id,
            'prerequisiteRequirementNodeId',prerequisite_requirement_node_id,
            'ordinal',canonical_ordinal))
        FROM ad_v4_candidate_obligation_requirement_dependencies
       WHERE projection_id=projection.id
      UNION ALL
      SELECT id,identity_hash,'aot',
        jsonb_build_object('table','termination-edge','identity',
          jsonb_build_object('projectionId',projection_id,
            'effectNodeId',effect_node_id,
            'terminatedRequirementNodeId',terminated_requirement_node_id,
            'ordinal',canonical_ordinal))
        FROM ad_v4_candidate_obligation_termination_edges
       WHERE projection_id=projection.id
      UNION ALL
      SELECT id,identity_hash,'aom',
        jsonb_build_object('table','recurrence-group-member','identity',
          jsonb_build_object('projectionId',projection_id,
            'groupNodeId',group_node_id,'requirementNodeId',requirement_node_id,
            'ordinal',canonical_ordinal))
        FROM ad_v4_candidate_obligation_recurrence_group_members
       WHERE projection_id=projection.id
    )
    SELECT 1 FROM relationships r
     WHERE r.identity_hash<>encode(sha256(
       convert_to('paprnav:ad_extraction_v4:obligation-row:1','UTF8')
       ||decode('00','hex')||convert_to(
         paprnav_v4_obligation_record(r.record),'UTF8')),'hex')
        OR r.id<>r.prefix||'_'||substr(r.identity_hash,1,32)
  ) THEN RAISE EXCEPTION 'V4 obligation relationship identity/hash differs'; END IF;

  IF EXISTS (
    SELECT 1 FROM (
      SELECT canonical_ordinal,row_number() OVER (
        PARTITION BY family,parent_id ORDER BY canonical_ordinal)-1 AS expected
      FROM (
        SELECT 'action-document'::text AS family,action_node_id AS parent_id,
          canonical_ordinal FROM ad_v4_candidate_obligation_action_document_refs
         WHERE projection_id=projection.id
        UNION ALL SELECT 'expression',parent_expression_id,canonical_ordinal
          FROM ad_v4_candidate_obligation_expression_edges
         WHERE projection_id=projection.id
        UNION ALL SELECT 'dependency',requirement_node_id,canonical_ordinal
          FROM ad_v4_candidate_obligation_requirement_dependencies
         WHERE projection_id=projection.id
        UNION ALL SELECT 'termination',effect_node_id,canonical_ordinal
          FROM ad_v4_candidate_obligation_termination_edges
         WHERE projection_id=projection.id
        UNION ALL SELECT 'group-member',group_node_id,canonical_ordinal
          FROM ad_v4_candidate_obligation_recurrence_group_members
         WHERE projection_id=projection.id
      ) relationships
    ) ordered WHERE canonical_ordinal<>expected
  ) THEN RAISE EXCEPTION 'V4 obligation relationship ordinal sequence differs'; END IF;

  IF EXISTS (
    SELECT 1 FROM ad_v4_candidate_obligation_actions a
     WHERE a.projection_id=projection.id AND (
       a.step_count<>(SELECT count(*) FROM ad_v4_candidate_obligation_action_steps s
         WHERE s.projection_id=projection.id AND s.action_node_id=a.semantic_node_id)
       OR a.document_ref_count<>(SELECT count(*) FROM ad_v4_candidate_obligation_action_document_refs r
         WHERE r.projection_id=projection.id AND r.action_node_id=a.semantic_node_id))
  ) OR EXISTS (
    SELECT 1 FROM ad_v4_candidate_obligation_timing_groups t
     WHERE t.projection_id=projection.id
       AND t.term_count<>(SELECT count(*) FROM ad_v4_candidate_obligation_timing_terms x
         WHERE x.projection_id=projection.id AND x.timing_group_node_id=t.semantic_node_id)
  ) OR EXISTS (
    SELECT 1 FROM ad_v4_candidate_obligation_terminating_effects e
     WHERE e.projection_id=projection.id
       AND e.edge_count<>(SELECT count(*) FROM ad_v4_candidate_obligation_termination_edges x
         WHERE x.projection_id=projection.id AND x.effect_node_id=e.semantic_node_id)
  ) OR EXISTS (
    SELECT 1 FROM ad_v4_candidate_obligation_recurrence_groups g
     WHERE g.projection_id=projection.id
       AND g.member_count<>(SELECT count(*) FROM ad_v4_candidate_obligation_recurrence_group_members x
         WHERE x.projection_id=projection.id AND x.group_node_id=g.semantic_node_id)
  ) OR EXISTS (
    SELECT 1 FROM ad_v4_candidate_obligation_requirements q
     WHERE q.projection_id=projection.id AND (
       q.sequence_text !~ '^[1-9][0-9]*$'
       OR q.sequence_value<>q.sequence_text::integer)
  ) THEN RAISE EXCEPTION 'V4 obligation child count/numeric projection differs'; END IF;

  IF EXISTS (
    SELECT 1 FROM ad_v4_candidate_obligation_action_document_refs r
    LEFT JOIN ad_v4_candidate_obligation_documents d
      ON d.projection_id=r.projection_id AND d.semantic_node_id=r.document_node_id
     WHERE r.projection_id=projection.id
       AND (d.semantic_node_id IS NULL
         OR r.document_ref_key IS DISTINCT FROM d.document_ref_key)
  ) OR EXISTS (
    SELECT 1 FROM ad_v4_candidate_obligation_requirement_dependencies r
    LEFT JOIN ad_v4_candidate_obligation_requirements q
      ON q.projection_id=r.projection_id
     AND q.semantic_node_id=r.prerequisite_requirement_node_id
     WHERE r.projection_id=projection.id
       AND (q.semantic_node_id IS NULL
         OR r.prerequisite_requirement_key IS DISTINCT FROM q.requirement_key)
  ) OR EXISTS (
    SELECT 1 FROM ad_v4_candidate_obligation_termination_edges r
    LEFT JOIN ad_v4_candidate_obligation_requirements q
      ON q.projection_id=r.projection_id
     AND q.semantic_node_id=r.terminated_requirement_node_id
     WHERE r.projection_id=projection.id
       AND (q.semantic_node_id IS NULL
         OR r.terminated_requirement_key IS DISTINCT FROM q.requirement_key)
  ) OR EXISTS (
    SELECT 1 FROM ad_v4_candidate_obligation_recurrence_group_members r
    LEFT JOIN ad_v4_candidate_obligation_requirements q
      ON q.projection_id=r.projection_id AND q.semantic_node_id=r.requirement_node_id
     WHERE r.projection_id=projection.id AND (q.semantic_node_id IS NULL
       OR r.requirement_key IS DISTINCT FROM q.requirement_key)
  ) THEN RAISE EXCEPTION 'V4 obligation relationship target/key differs'; END IF;

  -- Forward owner references are source-position identities, not merely
  -- same-type/value aliases. This rejects swaps between equal subtrees.
  IF EXISTS (
    SELECT 1 FROM ad_v4_candidate_obligation_documents o
    JOIN ad_v4_candidate_obligation_semantic_nodes n ON n.id=o.semantic_node_id
     WHERE o.projection_id=projection.id AND (
       o.document_number_node_id IS DISTINCT FROM (SELECT c.id
         FROM ad_v4_candidate_obligation_semantic_nodes c
        WHERE c.projection_id=projection.id
          AND c.source_pointer=n.source_pointer||'/documentNumber')
       OR o.revision_node_id IS DISTINCT FROM (SELECT c.id
         FROM ad_v4_candidate_obligation_semantic_nodes c
        WHERE c.projection_id=projection.id
          AND c.source_pointer=n.source_pointer||'/revision')
       OR o.retention_node_id IS DISTINCT FROM (SELECT c.id
         FROM ad_v4_candidate_obligation_semantic_nodes c
        WHERE c.projection_id=projection.id
          AND c.source_pointer=n.source_pointer||'/retention'))
  ) OR EXISTS (
    SELECT 1 FROM ad_v4_candidate_obligation_requirements o
    JOIN ad_v4_candidate_obligation_semantic_nodes n ON n.id=o.semantic_node_id
     WHERE o.projection_id=projection.id AND (
       o.action_node_id IS DISTINCT FROM (SELECT c.id
         FROM ad_v4_candidate_obligation_semantic_nodes c
        WHERE c.projection_id=projection.id
          AND c.source_pointer=n.source_pointer||'/action')
       OR o.activation_root_node_id IS DISTINCT FROM (SELECT c.id
         FROM ad_v4_candidate_obligation_semantic_nodes c
        WHERE c.projection_id=projection.id
          AND c.source_pointer=n.source_pointer||'/activationExpression')
       OR o.branch_node_id IS DISTINCT FROM (SELECT c.id
         FROM ad_v4_candidate_obligation_semantic_nodes c
        WHERE c.projection_id=projection.id
          AND c.source_pointer=n.source_pointer||'/branch')
       OR o.initial_timing_node_id IS DISTINCT FROM (SELECT c.id
         FROM ad_v4_candidate_obligation_semantic_nodes c
        WHERE c.projection_id=projection.id
          AND c.source_pointer=n.source_pointer||'/initialTiming')
       OR o.recurrence_node_id IS DISTINCT FROM (SELECT c.id
         FROM ad_v4_candidate_obligation_semantic_nodes c
        WHERE c.projection_id=projection.id
          AND c.source_pointer=n.source_pointer||'/recurrence')
       OR o.terminating_effect_node_id IS DISTINCT FROM (SELECT c.id
         FROM ad_v4_candidate_obligation_semantic_nodes c
        WHERE c.projection_id=projection.id
          AND c.source_pointer=n.source_pointer||'/terminatingEffect'))
  ) OR EXISTS (
    SELECT 1 FROM ad_v4_candidate_obligation_branches o
    JOIN ad_v4_candidate_obligation_semantic_nodes n ON n.id=o.semantic_node_id
     WHERE o.projection_id=projection.id
       AND o.condition_root_node_id IS DISTINCT FROM CASE
         WHEN o.kind IN ('conditional','exception') THEN (SELECT c.id
           FROM ad_v4_candidate_obligation_semantic_nodes c
          WHERE c.projection_id=projection.id
            AND c.source_pointer=n.source_pointer||'/conditionExpression')
         ELSE NULL END
  ) OR EXISTS (
    SELECT 1 FROM ad_v4_candidate_obligation_recurrences o
    JOIN ad_v4_candidate_obligation_semantic_nodes n ON n.id=o.semantic_node_id
     WHERE o.projection_id=projection.id AND (
       o.timing_node_id IS DISTINCT FROM CASE
         WHEN o.kind IN ('interval','conditioned') THEN (SELECT c.id
           FROM ad_v4_candidate_obligation_semantic_nodes c
          WHERE c.projection_id=projection.id
            AND c.source_pointer=n.source_pointer||'/timing')
         ELSE NULL END
       OR o.condition_root_node_id IS DISTINCT FROM CASE
         WHEN o.kind='conditioned' THEN (SELECT c.id
           FROM ad_v4_candidate_obligation_semantic_nodes c
          WHERE c.projection_id=projection.id
            AND c.source_pointer=n.source_pointer||'/conditionExpression')
         ELSE NULL END)
  ) OR EXISTS (
    SELECT 1 FROM ad_v4_candidate_obligation_recurrence_groups o
    JOIN ad_v4_candidate_obligation_semantic_nodes n ON n.id=o.semantic_node_id
     WHERE o.projection_id=projection.id AND (
       o.initial_timing_node_id IS DISTINCT FROM (SELECT c.id
         FROM ad_v4_candidate_obligation_semantic_nodes c
        WHERE c.projection_id=projection.id
          AND c.source_pointer=n.source_pointer||'/initialTiming')
       OR o.recurring_timing_node_id IS DISTINCT FROM (SELECT c.id
         FROM ad_v4_candidate_obligation_semantic_nodes c
        WHERE c.projection_id=projection.id
          AND c.source_pointer=n.source_pointer||'/recurringTiming'))
  ) OR EXISTS (
    SELECT 1 FROM ad_v4_candidate_obligation_amoc_provisions o
    JOIN ad_v4_candidate_obligation_semantic_nodes n ON n.id=o.semantic_node_id
     WHERE o.projection_id=projection.id
       AND o.authority_assertion_node_id IS DISTINCT FROM (SELECT c.id
         FROM ad_v4_candidate_obligation_semantic_nodes c
        WHERE c.projection_id=projection.id
          AND c.source_pointer=n.source_pointer||'/approvingAuthority')
  ) OR EXISTS (
    SELECT 1 FROM ad_v4_candidate_obligation_value_assertions o
    JOIN ad_v4_candidate_obligation_semantic_nodes n ON n.id=o.semantic_node_id
     WHERE o.projection_id=projection.id
       AND o.field_code IS DISTINCT FROM CASE
         WHEN n.source_pointer LIKE '%/documentNumber' THEN 'document_number'
         WHEN n.source_pointer LIKE '%/revision' THEN 'revision'
         WHEN n.source_pointer LIKE '%/retention' THEN 'retention'
         WHEN n.source_pointer LIKE '%/approvingAuthority' THEN 'approving_authority'
         ELSE NULL END
  ) THEN RAISE EXCEPTION 'V4 obligation exact owner child/reference differs'; END IF;

  IF EXISTS (
    SELECT 1 FROM ad_v4_candidate_obligation_actions o
    JOIN ad_v4_candidate_obligation_semantic_nodes n ON n.id=o.semantic_node_id
     WHERE o.projection_id=projection.id
       AND o.requirement_node_id IS DISTINCT FROM n.parent_node_id
  ) OR EXISTS (
    SELECT 1 FROM ad_v4_candidate_obligation_action_steps o
    JOIN ad_v4_candidate_obligation_semantic_nodes n ON n.id=o.semantic_node_id
     WHERE o.projection_id=projection.id
       AND o.action_node_id IS DISTINCT FROM n.parent_node_id
  ) OR EXISTS (
    SELECT 1 FROM ad_v4_candidate_obligation_branches o
    JOIN ad_v4_candidate_obligation_semantic_nodes n ON n.id=o.semantic_node_id
     WHERE o.projection_id=projection.id
       AND o.requirement_node_id IS DISTINCT FROM n.parent_node_id
  ) OR EXISTS (
    SELECT 1 FROM ad_v4_candidate_obligation_timing_groups o
    JOIN ad_v4_candidate_obligation_semantic_nodes n ON n.id=o.semantic_node_id
     WHERE o.projection_id=projection.id AND (
       o.owner_node_id IS DISTINCT FROM n.parent_node_id
       OR o.owner_kind IS DISTINCT FROM CASE
         WHEN n.source_pointer ~ '^/requirements/[0-9]+/initialTiming$'
           THEN 'requirement_initial'
         WHEN n.source_pointer ~ '^/requirements/[0-9]+/recurrence/timing$'
           THEN 'requirement_recurrence'
         WHEN n.source_pointer ~ '/initialTiming$'
           THEN 'recurrence_group_initial'
         ELSE 'recurrence_group_recurring' END)
  ) OR EXISTS (
    SELECT 1 FROM ad_v4_candidate_obligation_timing_terms o
    JOIN ad_v4_candidate_obligation_semantic_nodes n ON n.id=o.semantic_node_id
     WHERE o.projection_id=projection.id
       AND o.timing_group_node_id IS DISTINCT FROM n.parent_node_id
  ) OR EXISTS (
    SELECT 1 FROM ad_v4_candidate_obligation_recurrences o
    JOIN ad_v4_candidate_obligation_semantic_nodes n ON n.id=o.semantic_node_id
     WHERE o.projection_id=projection.id
       AND o.requirement_node_id IS DISTINCT FROM n.parent_node_id
  ) OR EXISTS (
    SELECT 1 FROM ad_v4_candidate_obligation_terminating_effects o
    JOIN ad_v4_candidate_obligation_semantic_nodes n ON n.id=o.semantic_node_id
     WHERE o.projection_id=projection.id
       AND o.requirement_node_id IS DISTINCT FROM n.parent_node_id
  ) OR EXISTS (
    SELECT 1 FROM (
      SELECT semantic_node_id,canonical_ordinal,projection_id
        FROM ad_v4_candidate_obligation_documents
      UNION ALL SELECT semantic_node_id,canonical_ordinal,projection_id
        FROM ad_v4_candidate_obligation_requirements
      UNION ALL SELECT semantic_node_id,canonical_ordinal,projection_id
        FROM ad_v4_candidate_obligation_action_steps
      UNION ALL SELECT semantic_node_id,canonical_ordinal,projection_id
        FROM ad_v4_candidate_obligation_timing_groups
      UNION ALL SELECT semantic_node_id,canonical_ordinal,projection_id
        FROM ad_v4_candidate_obligation_timing_terms
      UNION ALL SELECT semantic_node_id,canonical_ordinal,projection_id
        FROM ad_v4_candidate_obligation_recurrence_groups
      UNION ALL SELECT semantic_node_id,canonical_ordinal,projection_id
        FROM ad_v4_candidate_obligation_amoc_provisions
    ) o JOIN ad_v4_candidate_obligation_semantic_nodes n ON n.id=o.semantic_node_id
     WHERE o.projection_id=projection.id
       AND o.canonical_ordinal IS DISTINCT FROM n.canonical_ordinal
  ) THEN RAISE EXCEPTION 'V4 obligation typed-owner parent differs'; END IF;

  IF EXISTS (
    SELECT 1 FROM ad_v4_candidate_obligation_expressions e
    JOIN ad_v4_candidate_obligation_semantic_nodes n ON n.id=e.semantic_node_id
    LEFT JOIN ad_v4_candidate_obligation_requirements q
      ON q.projection_id=e.projection_id AND q.semantic_node_id=e.requirement_node_id
    CROSS JOIN LATERAL (SELECT
      CASE
        WHEN n.source_pointer LIKE '%/activationExpression%'
          THEN substring(n.source_pointer from '^/requirements/[0-9]+')||'/activationExpression'
        WHEN n.source_pointer LIKE '%/branch/conditionExpression%'
          THEN substring(n.source_pointer from '^/requirements/[0-9]+')||'/branch/conditionExpression'
        ELSE substring(n.source_pointer from '^/requirements/[0-9]+')||'/recurrence/conditionExpression'
      END AS base_pointer,
      CASE
        WHEN n.source_pointer LIKE '%/activationExpression%' THEN 'activation'
        WHEN n.source_pointer LIKE '%/branch/conditionExpression%' THEN 'branch_condition'
        ELSE 'recurrence_condition'
      END AS expected_context
    ) expected
     WHERE e.projection_id=projection.id AND (
       q.semantic_node_id IS NULL
       OR e.context IS DISTINCT FROM expected.expected_context
       OR e.expression_path IS DISTINCT FROM CASE
         WHEN n.source_pointer=expected.base_pointer THEN '/'
         ELSE substr(n.source_pointer,length(expected.base_pointer)+1) END)
  ) OR EXISTS (
    SELECT 1 FROM ad_v4_candidate_obligation_expressions e
    LEFT JOIN ad_v4_candidate_app_semantic_nodes a
      ON a.id=e.app_target_node_id
     AND a.projection_id=e.app_target_projection_id
     AND a.proposal_id=e.proposal_id
    LEFT JOIN ad_v4_candidate_obligation_requirements q
      ON q.semantic_node_id=e.requirement_target_node_id
     AND q.projection_id=e.projection_id
     WHERE e.projection_id=projection.id AND (
       (e.node_type IN ('scope_ref','predicate_ref','rule_ref') AND (
         a.id IS NULL OR e.app_target_projection_id<>projection.app_projection_id
         OR a.node_type IS DISTINCT FROM CASE e.node_type
           WHEN 'scope_ref' THEN 'product_scope'
           WHEN 'predicate_ref' THEN 'condition'
           ELSE 'applicability_rule' END))
       OR (e.node_type='requirement_state_ref' AND q.semantic_node_id IS NULL))
  ) OR EXISTS (
    SELECT 1 FROM ad_v4_candidate_obligation_expressions e
     WHERE e.projection_id=projection.id AND (
       (e.node_type IN ('scope_ref','predicate_ref','rule_ref','requirement_state_ref')
         AND (SELECT count(*) FROM ad_v4_candidate_obligation_expression_edges x
           WHERE x.projection_id=projection.id
             AND x.parent_expression_id=e.semantic_node_id)<>0)
       OR (e.node_type='not' AND (SELECT count(*)
           FROM ad_v4_candidate_obligation_expression_edges x
          WHERE x.projection_id=projection.id
            AND x.parent_expression_id=e.semantic_node_id)<>1)
       OR (e.node_type IN ('all','any') AND (SELECT count(*)
           FROM ad_v4_candidate_obligation_expression_edges x
          WHERE x.projection_id=projection.id
            AND x.parent_expression_id=e.semantic_node_id)<2))
  ) OR EXISTS (
    SELECT 1 FROM ad_v4_candidate_obligation_expression_edges x
    LEFT JOIN ad_v4_candidate_obligation_expressions p
      ON p.projection_id=x.projection_id AND p.semantic_node_id=x.parent_expression_id
    LEFT JOIN ad_v4_candidate_obligation_expressions c
      ON c.projection_id=x.projection_id AND c.semantic_node_id=x.child_expression_id
    LEFT JOIN ad_v4_candidate_obligation_semantic_nodes n
      ON n.projection_id=x.projection_id AND n.id=x.child_expression_id
     WHERE x.projection_id=projection.id AND (
       p.semantic_node_id IS NULL OR c.semantic_node_id IS NULL OR n.id IS NULL
       OR x.requirement_node_id IS DISTINCT FROM p.requirement_node_id
       OR x.requirement_node_id IS DISTINCT FROM c.requirement_node_id
       OR x.context IS DISTINCT FROM p.context OR x.context IS DISTINCT FROM c.context
       OR n.parent_node_id IS DISTINCT FROM x.parent_expression_id
       OR n.canonical_ordinal IS DISTINCT FROM x.canonical_ordinal)
  ) THEN RAISE EXCEPTION 'V4 obligation expression ownership/arity differs'; END IF;

  IF EXISTS (
    SELECT 1 FROM ad_v4_candidate_obligation_expressions e
     WHERE e.projection_id=projection.id AND
       (SELECT count(*) FROM ad_v4_candidate_obligation_expression_edges x
         WHERE x.projection_id=projection.id AND x.child_expression_id=e.semantic_node_id)
       +(SELECT count(*) FROM (
          SELECT activation_root_node_id AS id
            FROM ad_v4_candidate_obligation_requirements WHERE projection_id=projection.id
          UNION ALL SELECT condition_root_node_id
            FROM ad_v4_candidate_obligation_branches WHERE projection_id=projection.id
              AND condition_root_node_id IS NOT NULL
          UNION ALL SELECT condition_root_node_id
            FROM ad_v4_candidate_obligation_recurrences WHERE projection_id=projection.id
              AND condition_root_node_id IS NOT NULL
        ) roots WHERE roots.id=e.semantic_node_id)<>1
  ) OR (
    WITH RECURSIVE roots(id) AS (
      SELECT activation_root_node_id FROM ad_v4_candidate_obligation_requirements
       WHERE projection_id=projection.id
      UNION SELECT condition_root_node_id FROM ad_v4_candidate_obligation_branches
       WHERE projection_id=projection.id AND condition_root_node_id IS NOT NULL
      UNION SELECT condition_root_node_id FROM ad_v4_candidate_obligation_recurrences
       WHERE projection_id=projection.id AND condition_root_node_id IS NOT NULL
    ), reachable(id) AS (
      SELECT id FROM roots
      UNION
      SELECT x.child_expression_id
        FROM reachable r
        JOIN ad_v4_candidate_obligation_expression_edges x
          ON x.projection_id=projection.id AND x.parent_expression_id=r.id
    )
    SELECT count(*) FROM reachable
  )<>projection.expression_count
  THEN RAISE EXCEPTION 'V4 obligation expression graph differs'; END IF;

  IF (
    SELECT count(*) FROM (
      SELECT requirement_node_id AS source_id,requirement_target_node_id AS target_id
        FROM ad_v4_candidate_obligation_expressions
       WHERE projection_id=projection.id AND requirement_target_node_id IS NOT NULL
      UNION ALL
      SELECT requirement_node_id,prerequisite_requirement_node_id
        FROM ad_v4_candidate_obligation_requirement_dependencies
       WHERE projection_id=projection.id
      UNION ALL
      SELECT e.requirement_node_id,x.terminated_requirement_node_id
        FROM ad_v4_candidate_obligation_termination_edges x
        JOIN ad_v4_candidate_obligation_terminating_effects e
          ON e.projection_id=x.projection_id AND e.semantic_node_id=x.effect_node_id
       WHERE x.projection_id=projection.id
    ) raw_graph
  )>40000 THEN
    RAISE EXCEPTION 'V4 obligation combined requirement graph edge budget exceeded';
  END IF;

  IF EXISTS (
    WITH RECURSIVE graph(source_id,target_id) AS (
      SELECT requirement_node_id,requirement_target_node_id
        FROM ad_v4_candidate_obligation_expressions
       WHERE projection_id=projection.id AND requirement_target_node_id IS NOT NULL
      UNION
      SELECT requirement_node_id,prerequisite_requirement_node_id
        FROM ad_v4_candidate_obligation_requirement_dependencies
       WHERE projection_id=projection.id
      UNION
      SELECT e.requirement_node_id,x.terminated_requirement_node_id
        FROM ad_v4_candidate_obligation_termination_edges x
        JOIN ad_v4_candidate_obligation_terminating_effects e
          ON e.projection_id=x.projection_id AND e.semantic_node_id=x.effect_node_id
       WHERE x.projection_id=projection.id
    ), walk(origin,current) AS (
      SELECT source_id,target_id FROM graph
      UNION
      SELECT w.origin,g.target_id
        FROM walk w JOIN graph g ON g.source_id=w.current
    ) SELECT 1 FROM walk WHERE origin=current
  ) THEN RAISE EXCEPTION 'V4 obligation combined requirement graph cycle'; END IF;

  IF EXISTS (
    SELECT 1 FROM ad_v4_candidate_correction_refs r
    LEFT JOIN ad_v4_candidate_correction_semantic_bindings b
      ON b.correction_ref_id=r.id
    LEFT JOIN ad_v4_candidate_obligation_semantic_nodes n
      ON n.id=b.obligation_semantic_node_id
     AND n.projection_id=b.obligation_projection_id
     AND n.proposal_id=b.proposal_id
     WHERE r.proposal_id=projection.proposal_id AND r.owner_slice='slice_3b'
       AND (b.id IS NULL OR b.binding_slice<>'slice_3b' OR b.generation<>1
         OR b.proposal_id<>projection.proposal_id
         OR b.projection_id IS NOT NULL OR b.semantic_node_id IS NOT NULL
         OR b.obligation_projection_id<>projection.id OR n.id IS NULL
         OR n.node_key<>r.semantic_key
         OR n.node_type IS DISTINCT FROM CASE r.namespace
           WHEN 'requirements' THEN 'requirement'
           WHEN 'recurrenceGroups' THEN 'recurrence_group'
           WHEN 'amocAuthorityProvisions' THEN 'amoc_provision' END
         OR b.binding_hash<>encode(sha256(
           convert_to('paprnav:ad_extraction_v4:obligation-row:1','UTF8')
           ||decode('00','hex')||convert_to(paprnav_v4_obligation_record(
             jsonb_build_object('table','correction-binding','identity',
               jsonb_build_object('refId',r.id,'semanticId',n.id))),'UTF8')),'hex')
         OR b.id<>'avk_'||substr(b.binding_hash,1,32))
  ) OR EXISTS (
    SELECT 1 FROM ad_v4_candidate_correction_semantic_bindings b
    LEFT JOIN ad_v4_candidate_correction_refs r ON r.id=b.correction_ref_id
     WHERE b.obligation_projection_id=projection.id
       AND (r.id IS NULL OR r.proposal_id<>projection.proposal_id
         OR r.owner_slice<>'slice_3b')
  ) THEN RAISE EXCEPTION 'V4 obligation correction binding differs'; END IF;

  SELECT coalesce(jsonb_agg(jsonb_build_object(
    'bindingId',b.id,'bindingHash',b.binding_hash,
    'bindingSlice',b.binding_slice,'generation',b.generation,
    'correctionRefId',b.correction_ref_id,
    'targetProjectionId',b.obligation_projection_id,
    'targetSemanticNodeId',b.obligation_semantic_node_id)
    ORDER BY b.correction_ref_id,b.binding_slice,b.obligation_semantic_node_id),
    '[]'::jsonb) INTO binding_set
    FROM ad_v4_candidate_correction_semantic_bindings b
   WHERE b.obligation_projection_id=projection.id;
  binding_set_hash:=encode(sha256(
    convert_to('paprnav:ad_extraction_v4:obligation-correction-binding-set:1','UTF8')
    ||decode('00','hex')||convert_to(
      paprnav_v4_obligation_record(binding_set),'UTF8')),'hex');

  IF EXISTS (SELECT 1 FROM ad_v4_candidate_obligation_timing_terms
    WHERE projection_id=projection.id
      AND ((interval_text)::numeric IS DISTINCT FROM interval_numeric))
     OR paprnav_v4_candidate_obligation_typed_subtree(projection.id)
        IS DISTINCT FROM subtree
  THEN RAISE EXCEPTION 'V4 obligation typed-owner reconstruction differs'; END IF;

  envelope:=jsonb_build_object(
    'proposalId',projection.proposal_id,'directiveId',projection.directive_id,
    'validatorVersion',projection.validator_version,
    'canonicalizationVersion',projection.canonicalization_version,
    'proposalCanonicalHash',projection.proposal_canonical_hash,
    'evidenceBindingHash',projection.evidence_binding_hash,
    'appProjectionId',projection.app_projection_id,
    'appProjectionHash',projection.app_projection_hash,
    'appMaterializerVersion',projection.app_materializer_version,
    'materializerVersion',projection.materializer_version,
    'mappingVersion',projection.mapping_version,
    'mappingDigest',projection.mapping_digest,
    'obligationSubtreeHash',projection.obligation_subtree_hash,
    'gate',projection.gate,
    'counts',jsonb_build_object(
      'semanticNodeCount',projection.semantic_node_count,
      'datumCount',projection.datum_count,
      'evidenceLinkCount',projection.evidence_link_count,
      'documentCount',projection.document_count,
      'valueAssertionCount',projection.value_assertion_count,
      'requirementCount',projection.requirement_count,
      'actionCount',projection.action_count,
      'actionStepCount',projection.action_step_count,
      'actionDocumentRefCount',projection.action_document_ref_count,
      'branchCount',projection.branch_count,
      'expressionCount',projection.expression_count,
      'expressionEdgeCount',projection.expression_edge_count,
      'requirementDependencyCount',projection.requirement_dependency_count,
      'timingGroupCount',projection.timing_group_count,
      'timingTermCount',projection.timing_term_count,
      'recurrenceCount',projection.recurrence_count,
      'terminatingEffectCount',projection.terminating_effect_count,
      'terminationEdgeCount',projection.termination_edge_count,
      'recurrenceGroupCount',projection.recurrence_group_count,
      'recurrenceGroupMemberCount',projection.recurrence_group_member_count,
      'amocProvisionCount',projection.amoc_provision_count,
      'correctionBindingCount',projection.correction_binding_count));
  expected_hash:=encode(sha256(
    convert_to('paprnav:ad_extraction_v4:obligation-projection:1','UTF8')||decode('00','hex')||
    convert_to(paprnav_v4_obligation_record(envelope),'UTF8')),'hex');
  IF projection.projection_canonical_bytes<>convert_to(
       paprnav_v4_obligation_record(envelope),'UTF8')
     OR projection.projection_hash<>expected_hash
     OR projection.identity_hash<>encode(sha256(
       convert_to('paprnav:ad_extraction_v4:obligation-row:1','UTF8')||decode('00','hex')||
       convert_to(paprnav_v4_obligation_record(jsonb_build_object(
         'table','projection','identity',jsonb_build_object(
           'proposalId',projection.proposal_id,
           'appProjectionId',projection.app_projection_id,
           'materializerVersion',projection.materializer_version,
           'subtreeHash',projection.obligation_subtree_hash))),'UTF8')),'hex')
     OR projection.id<>'aox_'||substr(projection.identity_hash,1,32)
  THEN RAISE EXCEPTION 'V4 obligation projection identity/hash differs'; END IF;

  IF (SELECT count(*) FROM ad_v4_candidate_obligation_materialization_requests
       WHERE projection_id=projection.id)<1
  THEN RAISE EXCEPTION 'V4 obligation materialization request is missing'; END IF;
  FOR request_row IN
    SELECT * FROM ad_v4_candidate_obligation_materialization_requests
     WHERE projection_id=projection.id
  LOOP
    request_value:=jsonb_build_object(
      'action',request_row.endpoint_action,
      'directiveId',request_row.directive_id,
      'proposalId',request_row.proposal_id,
      'appProjectionId',request_row.app_projection_id,
      'validatorVersion',projection.validator_version,
      'canonicalizationVersion',projection.canonicalization_version,
      'appMaterializerVersion',projection.app_materializer_version,
      'materializerVersion',projection.materializer_version,
      'mappingVersion',projection.mapping_version,
      'mappingDigest',projection.mapping_digest);
    claims_value:=jsonb_build_object(
      'actorUserId',request_row.actor_user_id,
      'authorizingMembershipId',request_row.authorizing_membership_id,
      'organizationId',request_row.organization_id,
      'role',request_row.actor_role,'status',request_row.actor_status,
      'endpointAction',request_row.endpoint_action,
      'authPolicyVersion',request_row.auth_policy_version);
    IF request_row.proposal_id<>projection.proposal_id
       OR request_row.directive_id<>projection.directive_id
       OR request_row.app_projection_id<>projection.app_projection_id
       OR request_row.actor_role<>'platform_admin'
       OR request_row.actor_status<>'active'
       OR request_row.auth_policy_name<>'paprnav-platform-admin-v4-obligation-materialize'
       OR request_row.auth_policy_version<>'1'
       OR request_row.endpoint_action<>'materialize_ad_v4_obligations'
       OR NOT EXISTS (
         SELECT 1 FROM users u
          WHERE u.id=request_row.actor_user_id AND u.status='active')
       OR NOT EXISTS (
         SELECT 1 FROM organization_memberships m
          WHERE m.id=request_row.authorizing_membership_id
            AND m.user_id=request_row.actor_user_id
            AND m.organization_id=request_row.organization_id
            AND m.role=request_row.actor_role AND m.status=request_row.actor_status)
       OR request_row.auth_claims_hash<>encode(sha256(
         convert_to('paprnav:ad_extraction_v4:obligation-auth-claims:1','UTF8')
         ||decode('00','hex')||convert_to(
           paprnav_v4_obligation_record(claims_value),'UTF8')),'hex')
       OR request_row.request_canonical_bytes<>convert_to(
         paprnav_v4_obligation_record(request_value),'UTF8')
       OR request_row.request_hash<>encode(sha256(
         convert_to('paprnav:ad_extraction_v4:obligation-request:1','UTF8')
         ||decode('00','hex')||convert_to(
           paprnav_v4_obligation_record(request_value),'UTF8')),'hex')
       OR request_row.identity_hash<>encode(sha256(
         convert_to('paprnav:ad_extraction_v4:obligation-row:1','UTF8')
         ||decode('00','hex')||convert_to(paprnav_v4_obligation_record(
           jsonb_build_object('table','materialization-request','identity',
             jsonb_build_object(
               'actorUserId',request_row.actor_user_id,
               'authorizingMembershipId',request_row.authorizing_membership_id,
               'endpointAction',request_row.endpoint_action,
               'authPolicyVersion',request_row.auth_policy_version,
               'idempotencyKey',request_row.idempotency_key))),'UTF8')),'hex')
       OR request_row.id<>'aoq_'||substr(request_row.identity_hash,1,32)
    THEN RAISE EXCEPTION 'V4 obligation materialization request differs'; END IF;
  END LOOP;

  IF (SELECT count(*) FROM ad_v4_candidate_obligation_projection_events
       WHERE projection_id=projection.id AND sequence_number=0
         AND event_type='materialized')<>1
     OR EXISTS (
       SELECT 1 FROM (
         SELECT sequence_number,
           row_number() OVER (ORDER BY sequence_number)-1 AS expected_sequence,
           lag(event_hash) OVER (ORDER BY sequence_number) AS expected_predecessor,
           predecessor_event_hash
           FROM ad_v4_candidate_obligation_projection_events
          WHERE projection_id=projection.id
       ) chain WHERE sequence_number<>expected_sequence
          OR predecessor_event_hash IS DISTINCT FROM expected_predecessor)
  THEN RAISE EXCEPTION 'V4 obligation projection event chain differs'; END IF;
  FOR event_row IN
    SELECT * FROM ad_v4_candidate_obligation_projection_events
     WHERE projection_id=projection.id ORDER BY sequence_number
  LOOP
    event_value:=jsonb_build_object(
      'eventType',event_row.event_type,
      'projectionId',event_row.projection_id,
      'proposalId',event_row.proposal_id,
      'appProjectionId',event_row.app_projection_id,
      'sequenceNumber',event_row.sequence_number,
      'predecessorEventHash',event_row.predecessor_event_hash,
      'proposalCanonicalHash',event_row.proposal_canonical_hash,
      'evidenceBindingHash',event_row.evidence_binding_hash,
      'appProjectionHash',event_row.app_projection_hash,
      'obligationSubtreeHash',event_row.obligation_subtree_hash,
      'projectionHash',event_row.projection_hash,
      'correctionBindingSetHash',event_row.correction_binding_set_hash,
      'causingRequestId',event_row.causing_request_id,
      'cause',CASE WHEN event_row.cause_kind IS NULL THEN NULL::jsonb
        ELSE jsonb_build_object('kind',event_row.cause_kind,
          'id',event_row.cause_id,'hash',event_row.cause_hash) END);
    IF event_row.proposal_id<>projection.proposal_id
       OR event_row.app_projection_id<>projection.app_projection_id
       OR event_row.proposal_canonical_hash<>projection.proposal_canonical_hash
       OR event_row.evidence_binding_hash<>projection.evidence_binding_hash
       OR event_row.app_projection_hash<>projection.app_projection_hash
       OR event_row.obligation_subtree_hash<>projection.obligation_subtree_hash
       OR event_row.projection_hash<>projection.projection_hash
       OR event_row.correction_binding_set_hash<>binding_set_hash
       OR NOT EXISTS (
         SELECT 1 FROM ad_v4_candidate_obligation_materialization_requests r
          WHERE r.id=event_row.causing_request_id
            AND r.projection_id=projection.id)
       OR event_row.cause_kind IS DISTINCT FROM (CASE event_row.event_type
         WHEN 'materialized' THEN NULL
         WHEN 'evidence_invalidated' THEN 'evidence_lifecycle_event'
         WHEN 'parent_app_stale' THEN 'app_projection_event'
         WHEN 'candidate_corrected' THEN 'candidate_relationship'
         WHEN 'candidate_replaced' THEN 'candidate_relationship' END)
       OR (event_row.event_type='evidence_invalidated' AND NOT EXISTS (
         SELECT 1 FROM ad_evidence_fragment_lifecycle_events cause
         JOIN ad_evidence_fragments fragment ON fragment.id=cause.fragment_id
         JOIN ad_v4_candidate_evidence_bindings binding
           ON binding.fragment_id=cause.fragment_id
          AND binding.proposal_id=projection.proposal_id
          WHERE cause.id=event_row.cause_id
            AND cause.event_hash=event_row.cause_hash
            AND cause.event_type IN ('superseded','quarantined')
            AND cause.sequence_number>0
            AND cause.predecessor_event_hash IS NOT NULL
            AND cause.event_hash=paprnav_hash_parts(
              cause.fragment_id,fragment.fragment_hash,cause.event_type,
              cause.actor_user_id,cause.reason,cause.sequence_number::text,
              cause.predecessor_event_hash)))
       OR (event_row.event_type='parent_app_stale' AND NOT EXISTS (
         SELECT 1 FROM ad_v4_candidate_app_projection_events cause
          WHERE cause.id=event_row.cause_id
            AND cause.projection_id=projection.app_projection_id
            AND cause.event_hash=event_row.cause_hash
            AND cause.event_type='stale_marked'
            AND cause.sequence_number>0
            AND cause.predecessor_event_hash IS NOT NULL
            AND cause.event_hash=encode(sha256(
              convert_to('paprnav:ad_extraction_v4:applicability-projection-event:2','UTF8')
              ||decode('00','hex')||cause.canonical_bytes),'hex')))
       OR (event_row.event_type IN ('candidate_corrected','candidate_replaced')
         AND NOT EXISTS (
           SELECT 1 FROM ad_v4_candidate_submission_relationships cause
            WHERE cause.id=event_row.cause_id
              AND cause.predecessor_proposal_id=projection.proposal_id
              AND cause.relationship_hash=event_row.cause_hash
              AND cause.relation_type=CASE event_row.event_type
                WHEN 'candidate_corrected' THEN 'corrects_candidate'
                ELSE 'replaces_candidate' END
              AND cause.relationship_hash=encode(sha256(
                convert_to(CASE cause.validator_version
                  WHEN 'paprnav-ad-v4-validator-2'
                    THEN 'paprnav:ad_extraction_v4:submission-relationship:2'
                  ELSE 'paprnav:ad_extraction_v4:submission-relationship:1' END,'UTF8')
                ||decode('00','hex')||cause.canonical_bytes),'hex')))
       OR event_row.canonical_bytes<>convert_to(
         paprnav_v4_obligation_record(event_value),'UTF8')
       OR event_row.event_hash<>encode(sha256(
         convert_to('paprnav:ad_extraction_v4:obligation-projection-event:1','UTF8')
         ||decode('00','hex')||convert_to(
           paprnav_v4_obligation_record(event_value),'UTF8')),'hex')
       OR event_row.identity_hash<>encode(sha256(
         convert_to('paprnav:ad_extraction_v4:obligation-row:1','UTF8')
         ||decode('00','hex')||convert_to(paprnav_v4_obligation_record(
           jsonb_build_object('table','projection-event','identity',
             jsonb_build_object('projectionId',projection.id,
               'sequenceNumber',event_row.sequence_number,
               'eventHash',event_row.event_hash))),'UTF8')),'hex')
       OR event_row.id<>'aov_'||substr(event_row.identity_hash,1,32)
    THEN RAISE EXCEPTION 'V4 obligation projection event differs'; END IF;
  END LOOP;
END; $$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION paprnav_v4_candidate_obligation_mark_dirty()
RETURNS trigger AS $$
BEGIN
  -- Deliberately no caller-writable clean cache. Deferred callbacks always run
  -- the authoritative validator for every OLD and NEW root they can resolve.
  IF TG_OP='DELETE' THEN RETURN OLD; ELSE RETURN NEW; END IF;
END; $$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION paprnav_v4_lock_key(value text)
RETURNS bigint
LANGUAGE sql
IMMUTABLE
STRICT
PARALLEL SAFE
AS $$
  SELECT (('x'||substr(encode(sha256(convert_to(value,'UTF8')),'hex'),1,16))
    ::bit(64)::bigint)
$$;

CREATE OR REPLACE FUNCTION paprnav_v4_candidate_obligation_request_guard()
RETURNS trigger AS $$
DECLARE
  root ad_v4_candidate_obligation_projections%ROWTYPE;
  actor users%ROWTYPE;
  membership organization_memberships%ROWTYPE;
  lock_value bigint;
BEGIN
  -- Read immutable routing identity without a row lock, then acquire every
  -- mutable authority/input lock in the same order as the Python writer. This
  -- BEFORE INSERT guard runs before PostgreSQL obtains request FKs.
  SELECT * INTO root FROM ad_v4_candidate_obligation_projections
   WHERE id=NEW.projection_id;
  IF root.id IS NULL THEN
    RAISE EXCEPTION 'V4 obligation request projection is missing';
  END IF;
  SELECT * INTO actor FROM users WHERE id=NEW.actor_user_id FOR UPDATE;
  SELECT * INTO membership FROM organization_memberships
   WHERE id=NEW.authorizing_membership_id FOR UPDATE;
  IF actor.id IS NULL OR actor.status<>'active'
     OR membership.id IS NULL OR membership.user_id<>actor.id
     OR membership.organization_id<>NEW.organization_id
     OR membership.role<>'platform_admin' OR membership.status<>'active'
  THEN RAISE EXCEPTION 'V4 obligation request authority differs'; END IF;

  lock_value:=paprnav_v4_lock_key(
    'idem:'||NEW.actor_user_id||':'||NEW.authorizing_membership_id||':'||
    NEW.endpoint_action||':'||NEW.auth_policy_version||':'||NEW.idempotency_key);
  PERFORM pg_advisory_xact_lock(lock_value);
  PERFORM id FROM ad_v4_candidate_proposals
   WHERE id=root.proposal_id FOR UPDATE;
  PERFORM gate_key FROM ad_v4_feature_gates
   WHERE gate_key IN (
     'validator2_write_enabled','materializer3a_enabled','materializer3b_enabled')
   ORDER BY CASE gate_key
     WHEN 'validator2_write_enabled' THEN 1
     WHEN 'materializer3a_enabled' THEN 2 ELSE 3 END
   FOR UPDATE;
  IF (SELECT count(*) FROM ad_v4_feature_gates
       WHERE gate_key IN (
         'validator2_write_enabled','materializer3a_enabled','materializer3b_enabled')
         AND enabled)<>3
  THEN RAISE EXCEPTION 'V4 obligation request gate differs'; END IF;
  PERFORM id FROM ad_v4_candidate_evidence_bindings
   WHERE proposal_id=root.proposal_id ORDER BY id FOR SHARE;
  PERFORM fragment.id FROM ad_evidence_fragments fragment
   JOIN ad_v4_candidate_evidence_bindings binding
     ON binding.fragment_id=fragment.id
   WHERE binding.proposal_id=root.proposal_id
   ORDER BY fragment.id FOR SHARE OF fragment;

  lock_value:=paprnav_v4_lock_key(
    'projection:'||root.proposal_id||':paprnav-ad-v4-app-materializer-2');
  PERFORM pg_advisory_xact_lock(lock_value);
  PERFORM id FROM ad_v4_candidate_app_projections
   WHERE id=root.app_projection_id FOR UPDATE;
  PERFORM id FROM ad_v4_candidate_corrections
   WHERE proposal_id=root.proposal_id ORDER BY id FOR UPDATE;
  PERFORM id FROM ad_v4_candidate_correction_refs
   WHERE proposal_id=root.proposal_id ORDER BY id FOR UPDATE;
  lock_value:=paprnav_v4_lock_key(
    'projection:'||root.proposal_id||':paprnav-ad-v4-obligation-materializer-1');
  PERFORM pg_advisory_xact_lock(lock_value);
  PERFORM id FROM ad_v4_candidate_obligation_projections
   WHERE id=NEW.projection_id FOR UPDATE;
  RETURN NEW;
END; $$ LANGUAGE plpgsql;

CREATE TRIGGER trg_aob_request_insert_guard
BEFORE INSERT ON ad_v4_candidate_obligation_materialization_requests
FOR EACH ROW EXECUTE FUNCTION
paprnav_v4_candidate_obligation_request_guard();

CREATE OR REPLACE FUNCTION paprnav_v4_candidate_obligation_complete_trigger()
RETURNS trigger AS $$
DECLARE
  old_projection_id text;
  new_projection_id text;
  new_table_max_cmin bigint;
  anchor_cmin bigint;
  anchor_xmin text;
  new_insert_precedes_anchor boolean:=false;
BEGIN
  IF TG_OP<>'INSERT' THEN
    old_projection_id:=CASE
      WHEN TG_TABLE_NAME='ad_v4_candidate_obligation_projections'
        THEN to_jsonb(OLD)->>'id'
      WHEN TG_TABLE_NAME='ad_v4_candidate_correction_semantic_bindings'
        THEN to_jsonb(OLD)->>'obligation_projection_id'
      ELSE to_jsonb(OLD)->>'projection_id' END;
  END IF;
  IF TG_OP<>'DELETE' THEN
    new_projection_id:=CASE
      WHEN TG_TABLE_NAME='ad_v4_candidate_obligation_projections'
        THEN to_jsonb(NEW)->>'id'
      WHEN TG_TABLE_NAME='ad_v4_candidate_correction_semantic_bindings'
        THEN to_jsonb(NEW)->>'obligation_projection_id'
      ELSE to_jsonb(NEW)->>'projection_id' END;
  END IF;

  -- Normal materialization inserts the immutable graph, its audit request,
  -- and finally the sequence-zero materialized event.  That last event is the
  -- transaction's validation anchor.  PostgreSQL-owned xmin/cmin metadata lets
  -- earlier INSERT callbacks coalesce into the anchor without a caller-writable
  -- "clean" cache.  The anchor callback itself validates the complete graph.
  -- Any INSERT after the anchor, and every UPDATE/DELETE, still validates its
  -- affected root even if a client makes the constraints deferred again.
  IF TG_OP='INSERT' AND new_projection_id IS NOT NULL THEN
    EXECUTE format(
      'SELECT max(cmin::text::bigint) FROM %I WHERE %I=$1',
      TG_TABLE_NAME,
      CASE
        WHEN TG_TABLE_NAME='ad_v4_candidate_obligation_projections' THEN 'id'
        WHEN TG_TABLE_NAME='ad_v4_candidate_correction_semantic_bindings'
          THEN 'obligation_projection_id'
        ELSE 'projection_id'
      END)
      INTO new_table_max_cmin USING new_projection_id;
    SELECT cmin::text::bigint, xmin::text
      INTO anchor_cmin, anchor_xmin
      FROM ad_v4_candidate_obligation_projection_events
     WHERE projection_id=new_projection_id
       AND sequence_number=0
       AND event_type='materialized';
    new_insert_precedes_anchor:=coalesce((
      anchor_xmin=pg_current_xact_id()::text
      AND new_table_max_cmin IS NOT NULL
      AND anchor_cmin>new_table_max_cmin
    ),false);
  END IF;

  IF old_projection_id IS NOT NULL THEN
    PERFORM paprnav_v4_candidate_obligation_require_complete(old_projection_id);
  END IF;
  IF new_projection_id IS NOT NULL
     AND new_projection_id IS DISTINCT FROM old_projection_id
     AND NOT new_insert_precedes_anchor THEN
    PERFORM paprnav_v4_candidate_obligation_require_complete(new_projection_id);
  END IF;
  RETURN NULL;
END; $$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION paprnav_v4_reject_obligation_mutation()
RETURNS trigger AS $$
BEGIN
  RAISE EXCEPTION 'V4 obligation projection rows are immutable';
END; $$ LANGUAGE plpgsql;
