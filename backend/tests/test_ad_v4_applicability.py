from __future__ import annotations

import json

import pytest

from app.core.config import get_settings
from app.models.core import (
    ADV4CandidateAppCondition,
    ADV4CandidateAppDatum,
    ADV4CandidateAppDesignationGroup,
    ADV4CandidateAppDesignationGroupMember,
    ADV4CandidateAppEvidenceLink,
    ADV4CandidateAppExpression,
    ADV4CandidateAppExpressionEdge,
    ADV4CandidateAppDesignationRange,
    ADV4CandidateAppIdentityMapping,
    ADV4CandidateAppProjectionEvent,
    ADV4CandidateAppProjection,
    ADV4CandidateAppRule,
    ADV4CandidateAppRuleExclusion,
    ADV4CandidateAppSearchHint,
    ADV4CandidateAppSearchHintGroup,
    ADV4CandidateAppSearchHintMember,
    ADV4CandidateAppSemanticNode,
    ADV4CandidateAppValueAssertion,
    ADV4FeatureGate,
    ADTargetApplicability,
)
from conftest import TEST_PASSWORD, login
from test_ad_v4_api import _envelope, _headers, _seed_candidate_source


def _enable(monkeypatch, db, *, validator: bool, materializer: bool) -> None:
    monkeypatch.setenv("PAPRNAV_AD_V4_VALIDATOR2_WRITES_ENABLED", "true" if validator else "false")
    monkeypatch.setenv("PAPRNAV_AD_V4_SLICE3A_ROUTES_ENABLED", "true" if materializer else "false")
    get_settings.cache_clear()
    db.add_all([
        ADV4FeatureGate(gate_key="validator2_write_enabled", enabled=validator, changed_by="test"),
        ADV4FeatureGate(gate_key="materializer3a_enabled", enabled=materializer, changed_by="test"),
    ])
    db.commit()


def test_v2_candidate_materialize_retry_and_reconstruct(client, db_session, monkeypatch) -> None:
    admin, membership, directive, fragment = _seed_candidate_source(db_session)
    _enable(monkeypatch, db_session, validator=True, materializer=True)
    login(client, admin.email)
    envelope = _envelope(directive, fragment)
    raw = json.dumps(envelope, separators=(",", ":")).encode()
    candidate_response = client.post(
        f"/api/v1/ads/directives/{directive.id}/v4/candidate-proposals",
        content=raw,
        headers=_headers(membership.id, "v2-candidate"),
    )
    assert candidate_response.status_code == 201, candidate_response.text
    candidate = candidate_response.json()
    assert candidate["validatorVersion"] == "paprnav-ad-v4-validator-2"
    assert candidate["canonicalizationVersion"] == "paprnav-ad-v4-c14n-2"

    path = f"/api/v1/ads/directives/{directive.id}/v4/candidate-proposals/{candidate['proposalId']}/applicability-projection"
    headers = {"Idempotency-Key": "materialize-one", "Paprnav-Acting-Membership-Id": membership.id}
    created = client.post(path, headers=headers)
    assert created.status_code == 201, created.text
    body = created.json()
    assert body["gate"] == "candidate_only"
    assert body["projectionState"] == "candidate_verified"
    assert body["identityMappingCount"] == 0

    retry = client.post(path, headers=headers)
    assert retry.status_code == 200, retry.text
    assert retry.json()["projectionId"] == body["projectionId"]
    assert retry.json()["idempotentRetry"] is True

    audit_headers = {"Paprnav-Acting-Membership-Id": membership.id}
    detail = client.get(path, headers=audit_headers)
    assert detail.status_code == 200, detail.text
    reconstruction = client.get(f"{path}/reconstruction", headers=audit_headers)
    assert reconstruction.status_code == 200, reconstruction.text
    assert reconstruction.json()["canonicalApplicability"] == {
        key: envelope["proposal"][key]
        for key in ("productScopes", "conditionDefinitions", "applicabilityRules", "applicabilitySearchHints")
    }
    assert db_session.query(ADV4CandidateAppProjection).count() == 1
    assert db_session.query(ADV4CandidateAppDatum).count() > 0
    assert db_session.query(ADV4CandidateAppSemanticNode).count() == 3


def test_reconstruction_api_rejects_typed_identity_hash_drift(client, db_session, monkeypatch) -> None:
    admin, membership, directive, fragment = _seed_candidate_source(db_session)
    _enable(monkeypatch, db_session, validator=True, materializer=True)
    login(client, admin.email)
    envelope = _envelope(directive, fragment)
    envelope["proposal"]["productScopes"][0]["manufacturer"] = {
        "sourceValue": "Example Aircraft",
        "normalizedIdentity": {
            "state": "known", "value": "Example Aircraft",
            "evidenceKeys": ["ev-official"],
        },
    }
    envelope["proposal"]["productScopes"][0]["modelScope"] = {
        "kind": "listed", "sourceDesignations": ["Model 100", "Model 200"],
        "evidenceKeys": ["ev-official"],
    }
    envelope["proposal"]["productScopes"][0]["serialScope"] = {
        "kind": "ranges", "ranges": [{
            "lower": "100", "upper": "200", "lowerInclusive": True,
            "upperInclusive": True, "polarity": "included",
        }],
        "evidenceKeys": ["ev-official"],
    }
    candidate = client.post(
        f"/api/v1/ads/directives/{directive.id}/v4/candidate-proposals",
        content=json.dumps(envelope, separators=(",", ":")).encode(),
        headers=_headers(membership.id, "typed-read-parent"),
    ).json()
    path = f"/api/v1/ads/directives/{directive.id}/v4/candidate-proposals/{candidate['proposalId']}/applicability-projection"
    assert client.post(path, headers={
        "Idempotency-Key": "typed-read-create",
        "Paprnav-Acting-Membership-Id": membership.id,
    }).status_code == 201
    mapping = db_session.query(ADV4CandidateAppIdentityMapping).filter_by(
        identity_kind="manufacturer",
    ).one()
    mapping_node = db_session.get(ADV4CandidateAppSemanticNode, mapping.semantic_node_id)
    product_node = db_session.query(ADV4CandidateAppSemanticNode).filter_by(node_type="product_scope").one()
    evidence_link = db_session.query(ADV4CandidateAppEvidenceLink).filter_by(
        semantic_node_id=mapping.source_occurrence_node_id,
    ).one()
    designation_value_node = db_session.query(ADV4CandidateAppSemanticNode).filter_by(
        node_type="designation_value",
    ).first()
    designation_range_node = db_session.query(ADV4CandidateAppSemanticNode).filter_by(
        node_type="designation_range",
    ).one()
    designation_range = db_session.query(ADV4CandidateAppDesignationRange).one()
    mutations = [
        (mapping, {"identity_hash": "f" * 64}),
        (mapping, {"source_occurrence_node_id": product_node.id}),
        (mapping, {"evidence_parent_node_id": mapping.source_occurrence_node_id}),
        (mapping, {"identity_kind": "series"}),
        (mapping, {
            "normalization_origin": "source_only", "normalized_state": "unknown",
            "normalized_value": None, "reason": "not_yet_reviewed",
            "temporal_scope": "source_observation",
            "normalization_namespace": None, "normalization_version": None,
        }),
        (mapping_node, {"parent_node_id": product_node.id}),
        (evidence_link, {"link_hash": "e" * 64}),
        (product_node, {"identity_hash": "d" * 64}),
        (designation_value_node, {"identity_hash": "c" * 64}),
        (designation_range_node, {"canonical_node_hash": "b" * 64}),
        (designation_range, {"canonical_ordinal": 1}),
    ]
    for target, changes in mutations:
        originals = {field: getattr(target, field) for field in changes}
        for field, value in changes.items():
            setattr(target, field, value)
        db_session.commit()
        response = client.get(
            f"{path}/reconstruction",
            headers={"Paprnav-Acting-Membership-Id": membership.id},
        )
        assert response.status_code == 409
        assert response.json()["detail"]["code"] == "projection_integrity"
        for field, value in originals.items():
            setattr(target, field, value)
        db_session.commit()


def test_reconstruction_api_rejects_condition_family_drift(client, db_session, monkeypatch) -> None:
    admin, membership, directive, fragment = _seed_candidate_source(db_session)
    _enable(monkeypatch, db_session, validator=True, materializer=True)
    login(client, admin.email)
    envelope = _envelope(directive, fragment)
    envelope["proposal"]["conditionDefinitions"] = [{
        "conditionKey": "condition-group",
        "conditionType": "identity",
        "operator": "identity_in",
        "subject": {
            "designationGroup": {
                "groupKey": "group-models",
                "sourceDisplayText": {
                    "state": "known", "value": "Models A and B",
                    "evidenceKeys": ["ev-official"],
                },
                "association": "all_members",
                "members": [{
                    "memberKey": "member-model-a", "designationKind": "model",
                    "sourceDesignation": "Model A",
                    "manufacturer": {
                        "state": "known", "value": "Maker A",
                        "evidenceKeys": ["ev-official"],
                    },
                    "evidenceKeys": ["ev-official"],
                }],
                "evidenceKeys": ["ev-official"],
            },
        },
        "temporalBasis": {"kind": "directive_version"},
        "evidenceKeys": ["ev-official"],
    }]
    envelope["proposal"]["applicabilityRules"][0]["conditionExpression"] = {
        "nodeType": "predicate_ref", "conditionKey": "condition-group",
    }
    candidate = client.post(
        f"/api/v1/ads/directives/{directive.id}/v4/candidate-proposals",
        content=json.dumps(envelope, separators=(",", ":")).encode(),
        headers=_headers(membership.id, "condition-read-parent"),
    ).json()
    path = f"/api/v1/ads/directives/{directive.id}/v4/candidate-proposals/{candidate['proposalId']}/applicability-projection"
    assert client.post(path, headers={
        "Idempotency-Key": "condition-read-create",
        "Paprnav-Acting-Membership-Id": membership.id,
    }).status_code == 201
    condition = db_session.query(ADV4CandidateAppCondition).one()
    group = db_session.query(ADV4CandidateAppDesignationGroup).one()
    member = db_session.query(ADV4CandidateAppDesignationGroupMember).one()
    assertion = db_session.query(ADV4CandidateAppValueAssertion).filter_by(
        parent_semantic_node_id=member.semantic_node_id,
    ).one()
    mapping = db_session.query(ADV4CandidateAppIdentityMapping).filter_by(
        source_occurrence_node_id=member.semantic_node_id,
    ).one()
    evidence = db_session.query(ADV4CandidateAppEvidenceLink).filter_by(
        semantic_node_id=group.semantic_node_id,
    ).one()
    group_node = db_session.get(ADV4CandidateAppSemanticNode, group.semantic_node_id)
    mutations = [
        (condition, {"operator": "equals"}),
        (group, {"association": "any_member"}),
        (member, {"source_designation": "Model B"}),
        (assertion, {"text_value": "Maker B"}),
        (assertion, {
            "state": "unknown", "text_value": None,
            "reason": "not_observed", "temporal_scope": "directive_version",
        }),
        (mapping, {"evidence_parent_node_id": condition.semantic_node_id}),
        (mapping, {
            "reason": "not_yet_reviewed", "temporal_scope": "source_observation",
        }),
        (evidence, {"purpose": "subject_value"}),
        (group_node, {"canonical_node_hash": "f" * 64}),
    ]
    for target, changes in mutations:
        originals = {field: getattr(target, field) for field in changes}
        for field, value in changes.items():
            setattr(target, field, value)
        db_session.commit()
        response = client.get(
            f"{path}/reconstruction",
            headers={"Paprnav-Acting-Membership-Id": membership.id},
        )
        assert response.status_code == 409
        assert response.json()["detail"]["code"] == "projection_integrity"
        for field, value in originals.items():
            setattr(target, field, value)
        db_session.commit()

    group_values = {
        column.name: getattr(group, column.name)
        for column in ADV4CandidateAppDesignationGroup.__table__.columns
    }
    db_session.delete(group)
    db_session.commit()
    missing = client.get(
        f"{path}/reconstruction",
        headers={"Paprnav-Acting-Membership-Id": membership.id},
    )
    assert missing.status_code == 409
    db_session.execute(ADV4CandidateAppDesignationGroup.__table__.insert().values(**group_values))
    db_session.commit()

    extra = ADV4CandidateAppCondition(
        semantic_node_id=group.semantic_node_id,
        projection_id=condition.projection_id, proposal_id=condition.proposal_id,
        condition_key="forged-extra-condition", condition_type="identity",
        operator="identity_equals", temporal_basis="directive_version",
        comparator_presence="property_absent", comparator_version=None,
        subject_product_role_presence="property_absent", subject_product_role=None,
        subject_attribute_key_presence="property_absent", subject_attribute_key=None,
        designation_group_presence="property_absent", designation_group_node_id=None,
        evaluation_state="unevaluated", evaluator_contract="none",
    )
    db_session.add(extra)
    db_session.commit()
    unexpected = client.get(
        f"{path}/reconstruction",
        headers={"Paprnav-Acting-Membership-Id": membership.id},
    )
    assert unexpected.status_code == 409
    db_session.delete(extra)
    db_session.commit()


def test_reconstruction_api_rejects_rule_expression_family_drift(client, db_session, monkeypatch) -> None:
    admin, membership, directive, fragment = _seed_candidate_source(db_session)
    _enable(monkeypatch, db_session, validator=True, materializer=True)
    login(client, admin.email)
    envelope = _envelope(directive, fragment)
    proposal = envelope["proposal"]
    proposal["conditionDefinitions"] = [{
        "conditionKey": "condition-rule", "conditionType": "identity",
        "operator": "identity_equals",
        "subject": {"attributeKey": "configuration", "attributeValue": {
            "state": "known", "value": "configured",
            "evidenceKeys": ["ev-official"],
        }},
        "temporalBasis": {"kind": "at_applicability_evaluation"},
        "evidenceKeys": ["ev-official"],
    }]
    proposal["applicabilityRules"] = [
        {
            "ruleKey": "rule-base",
            "scopeExpression": {"nodeType": "scope_ref", "scopeKey": "scope-main"},
            "exclusionRuleKeys": [], "evidenceKeys": ["ev-official"],
        },
        {
            "ruleKey": "rule-complex",
            "scopeExpression": {"nodeType": "all", "operands": [
                {"nodeType": "scope_ref", "scopeKey": "scope-main"},
                {"nodeType": "not", "operand": {
                    "nodeType": "scope_ref", "scopeKey": "scope-main",
                }},
            ]},
            "conditionExpression": {"nodeType": "any", "operands": [
                {"nodeType": "predicate_ref", "conditionKey": "condition-rule"},
                {"nodeType": "rule_ref", "ruleKey": "rule-base"},
            ]},
            "exclusionRuleKeys": ["rule-base"],
            "evidenceKeys": ["ev-official"],
        },
    ]
    proposal["requirements"][0]["activationExpression"] = {
        "nodeType": "rule_ref", "ruleKey": "rule-complex",
    }
    candidate = client.post(
        f"/api/v1/ads/directives/{directive.id}/v4/candidate-proposals",
        content=json.dumps(envelope, separators=(",", ":")).encode(),
        headers=_headers(membership.id, "rule-read-parent"),
    ).json()
    path = f"/api/v1/ads/directives/{directive.id}/v4/candidate-proposals/{candidate['proposalId']}/applicability-projection"
    assert client.post(path, headers={
        "Idempotency-Key": "rule-read-create",
        "Paprnav-Acting-Membership-Id": membership.id,
    }).status_code == 201
    complex_rule = db_session.query(ADV4CandidateAppRule).filter_by(
        rule_key="rule-complex",
    ).one()
    base_rule = db_session.query(ADV4CandidateAppRule).filter_by(
        rule_key="rule-base",
    ).one()
    scope_leaf = db_session.query(ADV4CandidateAppExpression).filter_by(
        owning_rule_node_id=complex_rule.semantic_node_id,
        expression_node_type="scope_ref",
    ).first()
    rule_ref = db_session.query(ADV4CandidateAppExpression).filter_by(
        owning_rule_node_id=complex_rule.semantic_node_id,
        expression_node_type="rule_ref",
    ).one()
    not_expression = db_session.query(ADV4CandidateAppExpression).filter_by(
        owning_rule_node_id=complex_rule.semantic_node_id,
        expression_node_type="not",
    ).one()
    not_edge = db_session.query(ADV4CandidateAppExpressionEdge).filter_by(
        parent_expression_id=not_expression.semantic_node_id,
    ).one()
    exclusion = db_session.query(ADV4CandidateAppRuleExclusion).filter_by(
        rule_node_id=complex_rule.semantic_node_id,
    ).one()
    evidence = db_session.query(ADV4CandidateAppEvidenceLink).filter_by(
        semantic_node_id=complex_rule.semantic_node_id,
    ).one()
    expression_node = db_session.get(ADV4CandidateAppSemanticNode, scope_leaf.semantic_node_id)

    mutations = [
        (complex_rule, {
            "condition_presence": "property_absent",
            "condition_expression_node_id": None,
        }),
        (scope_leaf, {"expression_path": "/forged"}),
        (rule_ref, {"referenced_rule_node_id": complex_rule.semantic_node_id}),
        (not_edge, {"sequence": 9}),
        (exclusion, {"excluded_rule_node_id": complex_rule.semantic_node_id}),
        (evidence, {"purpose": "condition_clause"}),
        (expression_node, {"canonical_node_hash": "f" * 64}),
    ]
    for target, changes in mutations:
        originals = {field: getattr(target, field) for field in changes}
        for field, value in changes.items():
            setattr(target, field, value)
        db_session.commit()
        response = client.get(
            f"{path}/reconstruction",
            headers={"Paprnav-Acting-Membership-Id": membership.id},
        )
        assert response.status_code == 409
        assert response.json()["detail"]["code"] == "projection_integrity"
        for field, value in originals.items():
            setattr(target, field, value)
        db_session.commit()

    edge_values = {
        column.name: getattr(not_edge, column.name)
        for column in ADV4CandidateAppExpressionEdge.__table__.columns
    }
    db_session.delete(not_edge)
    db_session.commit()
    missing_edge = client.get(
        f"{path}/reconstruction",
        headers={"Paprnav-Acting-Membership-Id": membership.id},
    )
    assert missing_edge.status_code == 409
    db_session.execute(ADV4CandidateAppExpressionEdge.__table__.insert().values(**edge_values))
    db_session.commit()

    rule_values = {
        column.name: getattr(base_rule, column.name)
        for column in ADV4CandidateAppRule.__table__.columns
    }
    db_session.delete(base_rule)
    db_session.commit()
    missing_rule = client.get(
        f"{path}/reconstruction",
        headers={"Paprnav-Acting-Membership-Id": membership.id},
    )
    assert missing_rule.status_code == 409
    db_session.execute(ADV4CandidateAppRule.__table__.insert().values(**rule_values))
    db_session.commit()

    extra = ADV4CandidateAppRule(
        semantic_node_id=scope_leaf.semantic_node_id,
        projection_id=complex_rule.projection_id,
        proposal_id=complex_rule.proposal_id,
        rule_key="forged-extra-rule",
        scope_expression_node_id=scope_leaf.semantic_node_id,
        condition_presence="property_absent",
        condition_expression_node_id=None, evaluator_contract="none",
    )
    db_session.add(extra)
    db_session.commit()
    unexpected = client.get(
        f"{path}/reconstruction",
        headers={"Paprnav-Acting-Membership-Id": membership.id},
    )
    assert unexpected.status_code == 409
    assert unexpected.json()["detail"]["code"] == "projection_integrity"


def test_reconstruction_api_rejects_search_hint_family_drift(client, db_session, monkeypatch) -> None:
    admin, membership, directive, fragment = _seed_candidate_source(db_session)
    _enable(monkeypatch, db_session, validator=True, materializer=True)
    login(client, admin.email)
    envelope = _envelope(directive, fragment)
    envelope["proposal"]["applicabilitySearchHints"] = [{
        "hintKey": "hint-airframe", "productRole": "airframe",
        "sourceDisplayText": {
            "state": "known", "value": "Maker models",
            "evidenceKeys": ["ev-official"],
        },
        "manufacturerModelGroups": [{
            "groupKey": "hint-group-maker",
            "manufacturer": {
                "state": "known", "value": "Maker",
                "evidenceKeys": ["ev-official"],
            },
            "association": "paired",
            "members": [
                {
                    "memberKey": "hint-member-model", "designationKind": "model",
                    "sourceDesignation": "Model A",
                    "manufacturer": {
                        "state": "known", "value": "Maker",
                        "evidenceKeys": ["ev-official"],
                    },
                    "evidenceKeys": ["ev-official"],
                },
                {
                    "memberKey": "hint-member-series", "designationKind": "series_expression",
                    "expressionText": "Model B through Model Z",
                    "evaluationState": "unknown", "reason": "unsupported_expression",
                    "manufacturer": {
                        "state": "known", "value": "Maker",
                        "evidenceKeys": ["ev-official"],
                    },
                    "evidenceKeys": ["ev-official"],
                },
            ],
            "evidenceKeys": ["ev-official"],
        }],
        "controlling": False, "exhaustive": False,
        "evidenceKeys": ["ev-official"],
    }]
    candidate = client.post(
        f"/api/v1/ads/directives/{directive.id}/v4/candidate-proposals",
        content=json.dumps(envelope, separators=(",", ":")).encode(),
        headers=_headers(membership.id, "hint-read-parent"),
    ).json()
    path = f"/api/v1/ads/directives/{directive.id}/v4/candidate-proposals/{candidate['proposalId']}/applicability-projection"
    assert client.post(path, headers={
        "Idempotency-Key": "hint-read-create",
        "Paprnav-Acting-Membership-Id": membership.id,
    }).status_code == 201
    hint = db_session.query(ADV4CandidateAppSearchHint).one()
    group = db_session.query(ADV4CandidateAppSearchHintGroup).one()
    member = db_session.query(ADV4CandidateAppSearchHintMember).filter_by(
        designation_kind="model",
    ).one()
    display = db_session.get(ADV4CandidateAppValueAssertion, hint.source_display_assertion_node_id)
    member_manufacturer = db_session.get(
        ADV4CandidateAppValueAssertion, member.manufacturer_assertion_node_id,
    )
    mapping = db_session.query(ADV4CandidateAppIdentityMapping).filter_by(
        source_occurrence_node_id=member.semantic_node_id,
    ).one()
    evidence = db_session.query(ADV4CandidateAppEvidenceLink).filter_by(
        semantic_node_id=group.semantic_node_id,
    ).one()
    member_node = db_session.get(ADV4CandidateAppSemanticNode, member.semantic_node_id)
    mutations = [
        (hint, {"product_role": "engine"}),
        (display, {"text_value": "forged display"}),
        (group, {"association": "source_group"}),
        (group, {"manufacturer_value": "Other Maker"}),
        (member, {"source_designation": "Model X"}),
        (member, {"canonical_ordinal": 7}),
        (member_manufacturer, {"text_value": "Other Maker"}),
        (mapping, {"evidence_parent_node_id": hint.semantic_node_id}),
        (evidence, {"purpose": "scope_clause"}),
        (member_node, {"canonical_node_hash": "f" * 64}),
    ]
    for target, changes in mutations:
        originals = {field: getattr(target, field) for field in changes}
        for field, value in changes.items():
            setattr(target, field, value)
        db_session.commit()
        response = client.get(
            f"{path}/reconstruction",
            headers={"Paprnav-Acting-Membership-Id": membership.id},
        )
        assert response.status_code == 409
        assert response.json()["detail"]["code"] == "projection_integrity"
        for field, value in originals.items():
            setattr(target, field, value)
        db_session.commit()

    group_values = {
        column.name: getattr(group, column.name)
        for column in ADV4CandidateAppSearchHintGroup.__table__.columns
    }
    db_session.delete(group)
    db_session.commit()
    missing = client.get(
        f"{path}/reconstruction",
        headers={"Paprnav-Acting-Membership-Id": membership.id},
    )
    assert missing.status_code == 409
    db_session.execute(ADV4CandidateAppSearchHintGroup.__table__.insert().values(**group_values))
    db_session.commit()

    extra = ADV4CandidateAppSearchHint(
        semantic_node_id=group.semantic_node_id,
        projection_id=hint.projection_id, proposal_id=hint.proposal_id,
        hint_key="forged-extra-hint", product_role="airframe",
        source_display_assertion_node_id=display.semantic_node_id,
        controlling=False, exhaustive=False,
    )
    db_session.add(extra)
    db_session.commit()
    unexpected = client.get(
        f"{path}/reconstruction",
        headers={"Paprnav-Acting-Membership-Id": membership.id},
    )
    assert unexpected.status_code == 409
    assert unexpected.json()["detail"]["code"] == "projection_integrity"


def test_audit_reads_reject_global_projection_count_drift(client, db_session, monkeypatch) -> None:
    admin, membership, directive, fragment = _seed_candidate_source(db_session)
    _enable(monkeypatch, db_session, validator=True, materializer=True)
    login(client, admin.email)
    envelope = _envelope(directive, fragment)
    candidate = client.post(
        f"/api/v1/ads/directives/{directive.id}/v4/candidate-proposals",
        content=json.dumps(envelope, separators=(",", ":")).encode(),
        headers=_headers(membership.id, "global-count-parent"),
    ).json()
    path = f"/api/v1/ads/directives/{directive.id}/v4/candidate-proposals/{candidate['proposalId']}/applicability-projection"
    assert client.post(path, headers={
        "Idempotency-Key": "global-count-create",
        "Paprnav-Acting-Membership-Id": membership.id,
    }).status_code == 201
    projection = db_session.query(ADV4CandidateAppProjection).one()
    projection.semantic_node_count += 1
    db_session.commit()
    headers = {"Paprnav-Acting-Membership-Id": membership.id}
    for audit_path in (
        path,
        f"{path}/reconstruction",
        f"/api/v1/ads/directives/{directive.id}/v4/applicability-projections?limit=10&offset=0",
    ):
        response = client.get(audit_path, headers=headers)
        assert response.status_code == 409
        assert response.json()["detail"]["code"] == "projection_integrity"


def test_feature_gate_matrix_preexisting_candidate(client, db_session, monkeypatch) -> None:
    admin, membership, directive, fragment = _seed_candidate_source(db_session)
    _enable(monkeypatch, db_session, validator=True, materializer=True)
    login(client, admin.email)
    raw = json.dumps(_envelope(directive, fragment), separators=(",", ":")).encode()
    candidate = client.post(
        f"/api/v1/ads/directives/{directive.id}/v4/candidate-proposals",
        content=raw,
        headers=_headers(membership.id, "v2-preexisting"),
    ).json()
    db_session.query(ADV4FeatureGate).filter_by(gate_key="validator2_write_enabled").update({"enabled": False})
    db_session.commit()
    path = f"/api/v1/ads/directives/{directive.id}/v4/candidate-proposals/{candidate['proposalId']}/applicability-projection"
    denied = client.post(path, headers={"Idempotency-Key": "disabled", "Paprnav-Acting-Membership-Id": membership.id})
    assert denied.status_code == 409
    assert denied.json()["detail"]["code"] == "validator2_write_gate_disabled"
    assert db_session.query(ADV4CandidateAppProjection).count() == 0


def test_v2_rejects_known_unknown_sentinel(db_session, monkeypatch) -> None:
    admin, membership, directive, fragment = _seed_candidate_source(db_session)
    _enable(monkeypatch, db_session, validator=True, materializer=True)
    envelope = _envelope(directive, fragment)
    envelope["proposal"]["conditionDefinitions"] = [{
        "conditionKey": "condition-unknown",
        "conditionType": "reviewed_manual_predicate",
        "operator": "requires_review",
        "subject": {"attributeKey": "source-status", "attributeValue": {"state": "known", "value": "unknown_requires_compliance", "evidenceKeys": ["ev-official"]}},
        "temporalBasis": {"kind": "at_applicability_evaluation"},
        "evidenceKeys": ["ev-official"],
    }]
    envelope["proposal"]["applicabilityRules"][0]["conditionExpression"] = {"nodeType": "predicate_ref", "conditionKey": "condition-unknown"}
    from app.services.ad_v4_candidates import ADV4Error, parse_v4_request_bytes, store_v4_candidate
    parsed = parse_v4_request_bytes(json.dumps(envelope, separators=(",", ":")).encode())
    try:
        store_v4_candidate(db_session, directive_id=directive.id, parsed=parsed, actor=admin, membership_id=membership.id, idempotency_key="sentinel")
    except ADV4Error as exc:
        assert exc.code == "semantic_unknown_sentinel"
    else:
        raise AssertionError("validator-2 accepted semantic unknown sentinel")


@pytest.mark.parametrize(
    ("validator_app", "materializer_app", "validator_db", "materializer_db", "expected"),
    [
        (False, True, True, True, "validator2_write_gate_disabled"),
        (True, False, True, True, "capability_disabled"),
        (True, True, False, True, "validator2_write_gate_disabled"),
        (True, True, True, False, "materializer3a_gate_disabled"),
    ],
)
def test_materializer_requires_all_application_and_database_gates(
    client, db_session, monkeypatch,
    validator_app, materializer_app, validator_db, materializer_db, expected,
) -> None:
    admin, membership, directive, fragment = _seed_candidate_source(db_session)
    _enable(monkeypatch, db_session, validator=True, materializer=True)
    login(client, admin.email)
    candidate = client.post(
        f"/api/v1/ads/directives/{directive.id}/v4/candidate-proposals",
        content=json.dumps(_envelope(directive, fragment), separators=(",", ":")).encode(),
        headers=_headers(membership.id, "gate-parent"),
    ).json()
    monkeypatch.setenv("PAPRNAV_AD_V4_VALIDATOR2_WRITES_ENABLED", "true" if validator_app else "false")
    monkeypatch.setenv("PAPRNAV_AD_V4_SLICE3A_ROUTES_ENABLED", "true" if materializer_app else "false")
    get_settings.cache_clear()
    db_session.query(ADV4FeatureGate).filter_by(gate_key="validator2_write_enabled").update({"enabled": validator_db})
    db_session.query(ADV4FeatureGate).filter_by(gate_key="materializer3a_enabled").update({"enabled": materializer_db})
    db_session.commit()
    response = client.post(
        f"/api/v1/ads/directives/{directive.id}/v4/candidate-proposals/{candidate['proposalId']}/applicability-projection",
        headers={"Idempotency-Key": "gate-attempt", "Paprnav-Acting-Membership-Id": membership.id},
    )
    assert response.status_code in {404, 409}
    assert response.json()["detail"]["code"] == expected
    assert db_session.query(ADV4CandidateAppProjection).count() == 0


def test_projection_audit_requires_exact_membership_and_does_not_feed_v3(client, db_session, monkeypatch) -> None:
    admin, membership, directive, fragment = _seed_candidate_source(db_session)
    _enable(monkeypatch, db_session, validator=True, materializer=True)
    login(client, admin.email)
    candidate = client.post(
        f"/api/v1/ads/directives/{directive.id}/v4/candidate-proposals",
        content=json.dumps(_envelope(directive, fragment), separators=(",", ":")).encode(),
        headers=_headers(membership.id, "audit-parent"),
    ).json()
    path = f"/api/v1/ads/directives/{directive.id}/v4/candidate-proposals/{candidate['proposalId']}/applicability-projection"
    assert client.post(path, headers={"Idempotency-Key": "audit-create", "Paprnav-Acting-Membership-Id": membership.id}).status_code == 201
    event_count = db_session.query(ADV4CandidateAppProjectionEvent).count()
    assert client.get(path).status_code == 422
    assert client.get(path, headers={"Paprnav-Acting-Membership-Id": "mem_missing"}).status_code == 403
    assert client.get(path, headers={"Paprnav-Acting-Membership-Id": membership.id}).status_code == 200
    reconstruction = client.get(
        f"{path}/reconstruction",
        headers={"Paprnav-Acting-Membership-Id": membership.id},
    )
    assert reconstruction.status_code == 200
    listing = client.get(
        f"/api/v1/ads/directives/{directive.id}/v4/applicability-projections?limit=1&offset=0",
        headers={"Paprnav-Acting-Membership-Id": membership.id},
    )
    assert listing.status_code == 200
    assert listing.json()["count"] == listing.json()["total"] == 1
    assert db_session.query(ADV4CandidateAppProjectionEvent).count() == event_count
    assert db_session.query(ADTargetApplicability).count() == 0


def test_validator1_candidate_remains_readable_but_is_not_materializable(client, db_session, monkeypatch) -> None:
    from app.services.ad_v4_candidates import VALIDATOR_VERSION

    admin, membership, directive, fragment = _seed_candidate_source(db_session)
    _enable(monkeypatch, db_session, validator=True, materializer=True)
    envelope = _envelope(directive, fragment)
    from app.services.ad_v4_candidates import parse_v4_request_bytes, store_v4_candidate
    stored = store_v4_candidate(
        db_session, directive_id=directive.id,
        parsed=parse_v4_request_bytes(json.dumps(envelope, separators=(",", ":")).encode()),
        actor=admin, membership_id=membership.id, idempotency_key="legacy-v1",
        validator_version=VALIDATOR_VERSION,
    )
    db_session.commit()
    login(client, admin.email)
    response = client.post(
        f"/api/v1/ads/directives/{directive.id}/v4/candidate-proposals/{stored.proposal.id}/applicability-projection",
        headers={"Idempotency-Key": "legacy-refusal", "Paprnav-Acting-Membership-Id": membership.id},
    )
    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "predecessor_semantic_defect"


def test_all_90_condition_type_operator_pairs_are_unevaluated_and_reconstructable() -> None:
    from app.services.ad_v4_applicability import _flatten, _reconstruct_data
    from app.services.ad_v4_candidates import VALIDATOR_VERSION_V2, parse_v4_request_bytes, validate_v4_envelope

    condition_types = [
        "identity", "identifier_range", "installed_equipment", "modification_or_stc",
        "configuration_attribute", "temporal_overlap", "source_inclusion",
        "source_exclusion", "reviewed_manual_predicate",
    ]
    operators = [
        "identity_equals", "identity_in", "identifier_in_range", "is_installed",
        "is_not_installed", "equals", "overlaps", "includes", "excludes",
        "requires_review",
    ]
    represented = 0
    for condition_type in condition_types:
        for operator in operators:
            directive = type("Directive", (), {"id": "ad-condition-matrix", "ad_number": "2024-14-03"})()
            fragment = type("Fragment", (), {
                "id": "aef-condition-matrix", "fragment_hash": "f" * 64,
                "source_document_id": "asd-condition-matrix", "source_content_hash": "a" * 64,
            })()
            envelope = _envelope(directive, fragment)
            envelope["proposal"]["conditionDefinitions"] = [{
                "conditionKey": "condition-matrix", "conditionType": condition_type,
                "operator": operator,
                "subject": {"attributeKey": "matrix", "attributeValue": {"state": "known", "value": "source-observation", "evidenceKeys": ["ev-official"]}},
                "temporalBasis": {"kind": "at_applicability_evaluation"},
                "evidenceKeys": ["ev-official"],
            }]
            envelope["proposal"]["applicabilityRules"][0]["conditionExpression"] = {"nodeType": "predicate_ref", "conditionKey": "condition-matrix"}
            raw = json.dumps(envelope, separators=(",", ":")).encode()
            proposal, _ = validate_v4_envelope(parse_v4_request_bytes(raw), directive.id, validator_version=VALIDATOR_VERSION_V2)
            subtree = {key: proposal[key] for key in ("productScopes", "conditionDefinitions", "applicabilityRules", "applicabilitySearchHints")}
            semantic_rows, datum_rows, nodes = [], [], {}
            _flatten(subtree, pointer="", projection_id="avx-matrix", proposal_id="avp-matrix", parent_node_id=None, semantic_rows=semantic_rows, datum_rows=datum_rows, node_by_pointer=nodes)
            assert _reconstruct_data(datum_rows) == subtree
            assert not any(hasattr(row, "evaluation_result") for row in semantic_rows)
            represented += 1
    assert represented == 90
