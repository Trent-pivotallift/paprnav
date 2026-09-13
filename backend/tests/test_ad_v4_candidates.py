import hashlib
import json
from copy import deepcopy
from pathlib import Path

import pytest

import app.services.ad_v4_candidates as ad_v4_candidates

from app.models.core import (
    ADEvidenceFragment,
    ADEvidenceFragmentLifecycleEvent,
    ADV4CandidateEvidenceBinding,
    ADV4CandidateProposal,
    ADV4CandidateProposalEvent,
    ADV4CandidateSubmission,
    ADV4CandidateSubmissionRelationship,
    AirworthinessDirective,
)
from app.services.ad_evidence import _hash_parts
from app.services.ad_v4_candidates import (
    ADV4Error,
    DOMAINS,
    DOMAINS_V2,
    canonical_bytes,
    parse_v4_request_bytes,
    store_v4_candidate,
    validate_v4_envelope,
    verified_candidate,
)
from conftest import add_membership, create_organization, create_user


def _setup(db):
    actor = create_user(db, "v4.admin@paprnav.local", "V4 Admin")
    org = create_organization(db, "Paprnav", "platform")
    membership = add_membership(db, org, actor, "platform_admin")
    directive = AirworthinessDirective(
        ad_number="2024-14-03", title="Autopilot System", source_content_hash="a" * 64,
        status="candidate", extraction_status="not_started", review_status="not_started",
    )
    db.add(directive)
    db.flush()
    fragment = ADEvidenceFragment(
        directive_id=directive.id, source_document_id="asd_test", source_content_hash="b" * 64,
        rendition_id="asr_test", page_text_version_id="ast_test", page_start=1, page_end=1,
        character_start=0, character_end=12, exact_text="Official text",
        fragment_hash="c" * 64, parser_name="fixture", parser_version="1",
        created_by_user_id=actor.id,
    )
    db.add(fragment)
    db.flush()
    event = ADEvidenceFragmentLifecycleEvent(
        fragment_id=fragment.id, event_type="admitted", actor_user_id=actor.id,
        reason="fixture", sequence_number=0, predecessor_event_hash=None,
        event_hash="0" * 64,
    )
    event.event_hash = _hash_parts(
        fragment.id, fragment.fragment_hash, event.event_type, actor.id,
        event.reason, event.sequence_number, event.predecessor_event_hash,
    )
    db.add(event)
    db.flush()
    return actor, membership, directive, fragment


def _envelope(directive, fragment, *, decision_key="decision-2024-14-03"):
    ev = "ev-rule"
    proposal = {
        "schemaVersion": "ad_extraction_v4",
        "decisionKey": decision_key,
        "directiveIdentity": {
            "directiveId": directive.id,
            "adNumber": {"state": "known", "value": directive.ad_number, "evidenceKeys": [ev]},
        },
        "officialDocuments": [{
            "officialDocumentKey": "official-ad-rule", "documentRole": "ad_rule",
            "sourceDocumentId": fragment.source_document_id,
            "sourceContentHash": fragment.source_content_hash,
            "publicationDocumentNumber": "2024-15529", "evidenceKeys": [ev],
        }],
        "evidenceBindings": {ev: {"fragmentId": fragment.id, "fragmentHash": fragment.fragment_hash}},
        "incorporatedDocuments": [],
        "productScopes": [{"scopeKey": "scope-airframe", "productRole": "airframe", "evidenceKeys": [ev]}],
        "conditionDefinitions": [],
        "applicabilityRules": [{"ruleKey": "rule-main", "scopeExpression": {"nodeType": "scope_ref", "scopeKey": "scope-airframe"}, "exclusionRuleKeys": [], "evidenceKeys": [ev]}],
        "requirements": [{
            "requirementKey": "requirement-action",
            "sequence": "1",
            "activationExpression": {"nodeType": "rule_ref", "ruleKey": "rule-main"},
            "requirementType": "corrective_action",
            "action": {"actionType": "other_reviewed", "approvedDataDocumentRefKeys": [], "evidenceKeys": [ev]},
            "prerequisiteRequirementKeys": [],
            "branch": {"kind": "required", "evidenceKeys": [ev]},
            "initialTiming": {"state": "unknown", "reason": "not_yet_reviewed", "temporalScope": {"kind": "directive_version"}, "evidenceKeys": [ev]},
            "recurrence": {"kind": "none", "evidenceKeys": [ev]},
            "terminatingEffect": {"kind": "none", "evidenceKeys": [ev]},
            "evidenceKeys": [ev],
        }],
        "recurrenceGroups": [],
        "applicabilitySearchHints": [],
        "amocAuthorityProvisions": [],
        "supersessionRelations": [],
        "authoritativeCorrections": [],
    }
    return {"proposal": proposal, "submissionContext": {"relationships": []}}


def _parsed(value):
    return parse_v4_request_bytes(json.dumps(value, separators=(",", ":")).encode())


@pytest.mark.parametrize("raw,code", [
    (b'{"proposal":{},"proposal":{}}', "duplicate_key"),
    (b'{"value":1}', "invalid_number"),
    (b'{"value":null}', "forbidden_json_value"),
    (b'\xff', "invalid_utf8"),
    (b'{"value":"\\ud800"}', "invalid_unicode_scalar"),
    (b'{"value":"\\u0000"}', "unsupported_unicode_character"),
    (b'{"\\u0000":"value"}', "unsupported_unicode_character"),
    (b'{"nested":[{"value":"\\u0000"}]}', "unsupported_unicode_character"),
    (b'{"nested":[{"\\u0000":"value"}]}', "unsupported_unicode_character"),
])
def test_raw_parser_rejects_noncanonical_inputs(raw, code):
    with pytest.raises(ADV4Error) as caught:
        parsed = parse_v4_request_bytes(raw)
        canonical_bytes(parsed.value)
    assert caught.value.code == code


def test_canonical_set_order_and_domain_are_stable():
    left = {"productScopes": [{"scopeKey": "scope-z"}, {"scopeKey": "scope-a"}], "flag": True}
    right = {"flag": True, "productScopes": [{"scopeKey": "scope-a"}, {"scopeKey": "scope-z"}]}
    assert canonical_bytes(left) == canonical_bytes(right)
    assert DOMAINS["proposal"].endswith(b"\x00")
    assert not DOMAINS["proposal"].endswith(b"\\0")


def test_schema_declared_model_range_and_supersession_sets_are_order_invariant():
    model_left = {"models": ["Z", "A", "M"]}
    model_right = {"models": ["M", "Z", "A"]}
    assert canonical_bytes(model_left) == canonical_bytes(model_right)
    ranges = [
        {"lower": "20", "upper": "30", "lowerInclusive": True, "upperInclusive": False, "polarity": "included"},
        {"lower": "01", "upper": "10", "lowerInclusive": True, "upperInclusive": True, "polarity": "excluded"},
    ]
    assert canonical_bytes({"ranges": ranges}) == canonical_bytes({"ranges": list(reversed(ranges))})
    relations = [
        {"relationType": "supersedes", "predecessorAdNumber": "02-01-01", "successorAdNumber": "03-01-01", "evidenceKeys": ["ev-b"]},
        {"relationType": "supersedes", "predecessorAdNumber": "01-01-01", "successorAdNumber": "03-01-01", "evidenceKeys": ["ev-a"]},
    ]
    assert canonical_bytes({"supersessionRelations": relations}) == canonical_bytes({"supersessionRelations": list(reversed(relations))})


def test_checked_in_schema_closes_every_object_and_annotates_every_array():
    schema_path = Path(__file__).resolve().parents[1] / "app" / "schemas" / "ad_extraction_v4.schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))

    def walk(node, pointer=""):
        if isinstance(node, dict):
            if node.get("type") == "object":
                assert node.get("additionalProperties") is False, pointer
            if node.get("type") == "array":
                assert node.get("x-paprnav-array-kind") in {"set", "sequence"}, pointer
                assert "items" in node, pointer
            for key, child in node.items():
                walk(child, f"{pointer}/{key}")
        elif isinstance(node, list):
            for index, child in enumerate(node):
                walk(child, f"{pointer}/{index}")

    walk(schema)


@pytest.mark.parametrize("mutate,expected_pointer", [
    (lambda value: value["proposal"]["directiveIdentity"].update({"adNubmer": {}}), "/proposal/directiveIdentity/adNubmer"),
    (lambda value: value["proposal"]["officialDocuments"][0].update({"sourceHash": "x"}), "/proposal/officialDocuments/0/sourceHash"),
    (lambda value: value["proposal"]["evidenceBindings"]["ev-rule"].update({"text": "copied"}), "/proposal/evidenceBindings/ev-rule/text"),
    (lambda value: value["proposal"]["productScopes"][0].update({"modelNames": []}), "/proposal/productScopes/0/modelNames"),
    (lambda value: value["proposal"]["applicabilityRules"][0]["scopeExpression"].update({"scope": "wrong"}), "/proposal/applicabilityRules/0/scopeExpression"),
    (lambda value: value["proposal"]["requirements"][0]["action"].update({"actionText": "copied"}), "/proposal/requirements/0/action/actionText"),
])
def test_runtime_schema_rejects_nested_additional_properties(db_session, mutate, expected_pointer):
    _, _, directive, fragment = _setup(db_session)
    value = deepcopy(_envelope(directive, fragment))
    mutate(value)
    with pytest.raises(ADV4Error) as caught:
        validate_v4_envelope(_parsed(value), directive.id)
    assert caught.value.code == "schema_validation"
    assert caught.value.pointer == expected_pointer


def test_requirement_sequence_is_typed_unique_and_contiguous(db_session):
    _, _, directive, fragment = _setup(db_session)
    malformed = deepcopy(_envelope(directive, fragment))
    malformed["proposal"]["requirements"][0]["sequence"] = "01"
    with pytest.raises(ADV4Error) as typed:
        validate_v4_envelope(_parsed(malformed), directive.id)
    assert typed.value.code == "schema_validation"
    assert typed.value.pointer == "/proposal/requirements/0/sequence"

    duplicate = deepcopy(_envelope(directive, fragment))
    second = deepcopy(duplicate["proposal"]["requirements"][0])
    second["requirementKey"] = "requirement-second"
    duplicate["proposal"]["requirements"].append(second)
    with pytest.raises(ADV4Error) as sequence:
        validate_v4_envelope(_parsed(duplicate), directive.id)
    assert sequence.value.code == "invalid_requirement_sequence"

    oversized_integer = deepcopy(_envelope(directive, fragment))
    oversized_integer["proposal"]["requirements"][0]["sequence"] = "9" * 5_000
    with pytest.raises(ADV4Error) as safe_conversion:
        validate_v4_envelope(_parsed(oversized_integer), directive.id)
    assert safe_conversion.value.code == "invalid_requirement_sequence"
    assert safe_conversion.value.http_status == 422

    beyond_raw_limit = deepcopy(_envelope(directive, fragment))
    beyond_raw_limit["proposal"]["requirements"][0]["sequence"] = "9" * 16_385
    with pytest.raises(ADV4Error) as resource_limit:
        _parsed(beyond_raw_limit)
    assert resource_limit.value.code == "resource_limit"
    assert resource_limit.value.http_status == 413


def test_verified_candidate_rejects_forged_requirement_count_before_allocation(db_session):
    actor, membership, directive, fragment = _setup(db_session)
    stored = store_v4_candidate(
        db_session,
        directive_id=directive.id,
        parsed=_parsed(_envelope(directive, fragment)),
        actor=actor,
        membership_id=membership.id,
        idempotency_key="sequence-forged-parent",
    )
    db_session.commit()

    forged = deepcopy(stored.proposal.parsed_json)
    template = forged["requirements"][0]
    forged["requirements"] = []
    for value in range(1, 2_002):
        requirement = deepcopy(template)
        requirement["requirementKey"] = f"requirement-{value:04d}"
        requirement["sequence"] = str(value)
        forged["requirements"].append(requirement)
    candidate = stored.proposal
    candidate.parsed_json = forged
    candidate.canonical_bytes = canonical_bytes(forged, candidate.canonicalization_version)
    domains = DOMAINS_V2 if candidate.validator_version.endswith("-2") else DOMAINS
    candidate.canonical_hash = hashlib.sha256(domains["proposal"] + candidate.canonical_bytes).hexdigest()
    db_session.commit()

    with pytest.raises(ADV4Error) as rejected:
        verified_candidate(db_session, candidate.id)
    assert rejected.value.code == "requirement_sequence_resource_limit"
    assert rejected.value.http_status == 409


def test_semantic_validator_rejects_dangling_duplicate_and_cyclic_refs(db_session):
    _, _, directive, fragment = _setup(db_session)
    dangling = deepcopy(_envelope(directive, fragment))
    dangling["proposal"]["applicabilityRules"][0]["scopeExpression"]["scopeKey"] = "scope-missing"
    with pytest.raises(ADV4Error) as missing:
        validate_v4_envelope(_parsed(dangling), directive.id)
    assert missing.value.code == "missing_typed_reference"

    duplicate = deepcopy(_envelope(directive, fragment))
    repeated = deepcopy(duplicate["proposal"]["productScopes"][0])
    repeated["productRole"] = "engine"
    duplicate["proposal"]["productScopes"].append(repeated)
    with pytest.raises(ADV4Error) as repeated_key:
        validate_v4_envelope(_parsed(duplicate), directive.id)
    assert repeated_key.value.code == "duplicate_stable_key"

    cyclic = deepcopy(_envelope(directive, fragment))
    cyclic["proposal"]["applicabilityRules"][0]["exclusionRuleKeys"] = ["rule-main"]
    with pytest.raises(ADV4Error) as cycle:
        validate_v4_envelope(_parsed(cyclic), directive.id)
    assert cycle.value.code == "cyclic_reference"


def test_semantic_validator_handles_long_requirement_chains_without_python_recursion(db_session):
    _, _, directive, fragment = _setup(db_session)
    value = deepcopy(_envelope(directive, fragment))
    template = value["proposal"]["requirements"][0]
    requirement_count = 1_100
    requirements = []
    for ordinal in range(requirement_count):
        requirement = deepcopy(template)
        requirement["requirementKey"] = f"requirement-{ordinal:04d}"
        requirement["sequence"] = str(ordinal + 1)
        if ordinal + 1 < requirement_count:
            requirement["activationExpression"] = {
                "nodeType": "requirement_state_ref",
                "requirementKey": f"requirement-{ordinal + 1:04d}",
                "requirementState": "unknown",
            }
        requirements.append(requirement)
    value["proposal"]["requirements"] = requirements

    validate_v4_envelope(_parsed(value), directive.id)

    value["proposal"]["requirements"][-1]["activationExpression"] = {
        "nodeType": "requirement_state_ref",
        "requirementKey": "requirement-0000",
        "requirementState": "unknown",
    }
    with pytest.raises(ADV4Error) as cycle:
        validate_v4_envelope(_parsed(value), directive.id)
    assert cycle.value.code == "cyclic_reference"


def test_graph_edge_budget_counts_duplicate_source_occurrences_across_families(
    db_session, monkeypatch,
):
    _, _, directive, fragment = _setup(db_session)
    value = deepcopy(_envelope(directive, fragment))
    source = value["proposal"]["requirements"][0]
    target = deepcopy(source)
    source["activationExpression"] = {
        "nodeType": "scope_ref", "scopeKey": "scope-airframe",
    }
    target["activationExpression"] = {
        "nodeType": "scope_ref", "scopeKey": "scope-airframe",
    }
    target["requirementKey"] = "requirement-target"
    target["sequence"] = "2"
    source["prerequisiteRequirementKeys"] = ["requirement-target"]
    source["terminatingEffect"] = {
        "kind": "terminates", "requirementKeys": ["requirement-target"],
        "evidenceKeys": ["ev-rule"],
    }
    value["proposal"]["requirements"].append(target)

    monkeypatch.setattr(ad_v4_candidates, "MAX_GRAPH_EDGES", 2)
    validate_v4_envelope(_parsed(value), directive.id)

    monkeypatch.setattr(ad_v4_candidates, "MAX_GRAPH_EDGES", 1)
    with pytest.raises(ADV4Error) as caught:
        validate_v4_envelope(_parsed(value), directive.id)
    assert caught.value.code == "resource_limit"
    assert caught.value.http_status == 413


def test_parser_resource_limits_fail_closed_before_schema():
    too_many = json.dumps({"values": ["x"] * 2001}, separators=(",", ":")).encode()
    with pytest.raises(ADV4Error) as array_limit:
        parse_v4_request_bytes(too_many)
    assert array_limit.value.code == "resource_limit"
    nested = '"leaf"'
    for _ in range(66):
        nested = '{"x":' + nested + '}'
    with pytest.raises(ADV4Error) as depth_limit:
        parse_v4_request_bytes(nested.encode())
    assert depth_limit.value.code == "resource_limit"

    hostile = ('{"x":' * 10_000 + '"leaf"' + '}' * 10_000).encode()
    with pytest.raises(ADV4Error) as hostile_depth:
        parse_v4_request_bytes(hostile)
    assert hostile_depth.value.code == "resource_limit"
    assert hostile_depth.value.http_status == 413


def test_supersession_composite_identity_and_multi_edge_cycles_fail_closed(db_session):
    _, _, directive, fragment = _setup(db_session)
    relation = {
        "relationType": "supersedes",
        "predecessorAdNumber": "2001-01-01",
        "successorAdNumber": "2002-01-01",
        "evidenceKeys": ["ev-rule"],
    }
    duplicate = deepcopy(relation)
    duplicate["evidenceKeys"] = ["ev-other"]
    with pytest.raises(ADV4Error) as tied:
        canonical_bytes({"supersessionRelations": [relation, duplicate]})
    assert tied.value.code == "duplicate_stable_key"

    cyclic = deepcopy(_envelope(directive, fragment))
    cyclic["proposal"]["supersessionRelations"] = [
        relation,
        {
            "relationType": "supersedes",
            "predecessorAdNumber": "2002-01-01",
            "successorAdNumber": "2001-01-01",
            "evidenceKeys": ["ev-rule"],
        },
    ]
    with pytest.raises(ADV4Error) as cycle:
        validate_v4_envelope(_parsed(cyclic), directive.id)
    assert cycle.value.code == "cyclic_reference"


def test_conditioned_recurrence_expression_is_semantically_traversed(db_session):
    _, _, directive, fragment = _setup(db_session)
    value = deepcopy(_envelope(directive, fragment))
    requirement = value["proposal"]["requirements"][0]
    requirement["recurrence"] = {
        "kind": "conditioned",
        "conditionExpression": {
            "nodeType": "predicate_ref",
            "conditionKey": "condition-missing",
        },
        "timing": {
            "logic": "all",
            "terms": [{
                "metric": "calendar", "interval": "30", "unit": "days",
                "comparator": "within", "anchor": "last_compliance",
                "evidenceKeys": ["ev-rule"],
            }],
            "evidenceKeys": ["ev-rule"],
        },
        "evidenceKeys": ["ev-rule"],
    }
    with pytest.raises(ADV4Error) as missing:
        validate_v4_envelope(_parsed(value), directive.id)
    assert missing.value.code == "missing_typed_reference"


def test_official_correction_cycle_and_group_inline_timing_fail_closed(db_session):
    _, _, directive, fragment = _setup(db_session)
    correction_cycle = _envelope(directive, fragment)
    correction_cycle["proposal"]["officialDocuments"].extend([
        {
            "officialDocumentKey": key, "documentRole": "official_correction",
            "sourceDocumentId": fragment.source_document_id,
            "sourceContentHash": fragment.source_content_hash,
            "publicationDocumentNumber": number, "evidenceKeys": ["ev-rule"],
        }
        for key, number in (("correction-one", "C1"), ("correction-two", "C2"))
    ])
    correction_cycle["proposal"]["authoritativeCorrections"] = [
        {
            "correctionKey": "correction-link-one", "correctionType": "official_correction",
            "originalDocumentRefKey": "correction-one", "correctingDocumentRefKey": "correction-two",
            "changedSemanticRefs": [{"namespace": "requirements", "key": "requirement-action"}],
            "evidenceKeys": ["ev-rule"],
        },
        {
            "correctionKey": "correction-link-two", "correctionType": "official_correction",
            "originalDocumentRefKey": "correction-two", "correctingDocumentRefKey": "correction-one",
            "changedSemanticRefs": [{"namespace": "requirements", "key": "requirement-action"}],
            "evidenceKeys": ["ev-rule"],
        },
    ]
    with pytest.raises(ADV4Error) as cycle:
        validate_v4_envelope(_parsed(correction_cycle), directive.id)
    assert cycle.value.code == "cyclic_reference"

    timing_conflict = _envelope(directive, fragment)
    first = timing_conflict["proposal"]["requirements"][0]
    second = deepcopy(first)
    second["requirementKey"] = "requirement-second"
    second["sequence"] = "2"
    for requirement in (first, second):
        requirement["recurrenceGroupKey"] = "recurrence-group"
    first["initialTiming"] = {
        "logic": "all",
        "terms": [{
            "metric": "calendar", "interval": "30", "unit": "days",
            "comparator": "within", "anchor": "effective_date", "evidenceKeys": ["ev-rule"],
        }],
        "evidenceKeys": ["ev-rule"],
    }
    timing_conflict["proposal"]["requirements"].append(second)
    timing_conflict["proposal"]["recurrenceGroups"] = [{
        "recurrenceGroupKey": "recurrence-group",
        "requirementKeys": ["requirement-action", "requirement-second"],
        "initialTiming": deepcopy(first["initialTiming"]),
        "recurringTiming": deepcopy(first["initialTiming"]),
        "completionPolicy": "all_active_requirements",
        "evidenceKeys": ["ev-rule"],
    }]
    with pytest.raises(ADV4Error) as conflict:
        validate_v4_envelope(_parsed(timing_conflict), directive.id)
    assert conflict.value.code == "recurrence_timing_conflict"


def test_store_retry_and_content_reuse_are_candidate_only(db_session):
    actor, membership, directive, fragment = _setup(db_session)
    parsed = _parsed(_envelope(directive, fragment))
    first = store_v4_candidate(
        db_session, directive_id=directive.id, parsed=parsed, actor=actor,
        membership_id=membership.id, idempotency_key="request-1",
    )
    db_session.commit()
    retry = store_v4_candidate(
        db_session, directive_id=directive.id, parsed=parsed, actor=actor,
        membership_id=membership.id, idempotency_key="request-1",
    )
    assert retry.idempotent_retry is True
    second = store_v4_candidate(
        db_session, directive_id=directive.id, parsed=parsed, actor=actor,
        membership_id=membership.id, idempotency_key="request-2",
    )
    db_session.commit()
    assert second.content_reused is True
    assert second.proposal.id == first.proposal.id
    assert second.proposal.gate == "candidate_only"
    assert db_session.query(ADV4CandidateProposal).count() == 1
    assert db_session.query(ADV4CandidateSubmission).count() == 2
    assert db_session.query(ADV4CandidateProposalEvent).count() == 1


def test_candidate_correction_graph_rejects_multi_proposal_cycle(db_session):
    actor, membership, directive, fragment = _setup(db_session)
    first_value = _envelope(directive, fragment, decision_key="candidate-a")
    first = store_v4_candidate(
        db_session, directive_id=directive.id, parsed=_parsed(first_value), actor=actor,
        membership_id=membership.id, idempotency_key="candidate-a",
    )
    db_session.commit()

    self_value = _envelope(directive, fragment, decision_key="candidate-a")
    self_value["submissionContext"]["relationships"] = [{
        "relationshipKey": "a-corrects-itself",
        "relationType": "corrects_candidate",
        "predecessorProposalId": first.proposal.id,
        "reason": "Invalid self edge",
        "evidenceKeys": ["ev-rule"],
    }]
    with pytest.raises(ADV4Error) as self_edge:
        store_v4_candidate(
            db_session, directive_id=directive.id, parsed=_parsed(self_value), actor=actor,
            membership_id=membership.id, idempotency_key="candidate-a-self",
        )
    assert self_edge.value.code == "invalid_predecessor"
    db_session.rollback()

    second_value = _envelope(directive, fragment, decision_key="candidate-b")
    second_value["submissionContext"]["relationships"] = [{
        "relationshipKey": "b-corrects-a",
        "relationType": "corrects_candidate",
        "predecessorProposalId": first.proposal.id,
        "reason": "B corrects A",
        "evidenceKeys": ["ev-rule"],
    }]
    second = store_v4_candidate(
        db_session, directive_id=directive.id, parsed=_parsed(second_value), actor=actor,
        membership_id=membership.id, idempotency_key="candidate-b",
    )
    db_session.commit()

    cycle_value = _envelope(directive, fragment, decision_key="candidate-a")
    cycle_value["submissionContext"]["relationships"] = [{
        "relationshipKey": "a-corrects-b",
        "relationType": "corrects_candidate",
        "predecessorProposalId": second.proposal.id,
        "reason": "Invalid cycle",
        "evidenceKeys": ["ev-rule"],
    }]
    with pytest.raises(ADV4Error) as cycle:
        store_v4_candidate(
            db_session, directive_id=directive.id, parsed=_parsed(cycle_value), actor=actor,
            membership_id=membership.id, idempotency_key="candidate-a-cycle",
        )
    assert cycle.value.code == "cyclic_reference"


def test_new_candidate_flushes_integrity_parents_in_dependency_order(db_session, monkeypatch):
    actor, membership, directive, fragment = _setup(db_session)
    observed_flushes: list[tuple[list[str], list[str]]] = []
    actual_flush = db_session.flush

    def observed_flush(objects=None):
        requested = [type(item).__name__ for item in objects] if objects is not None else []
        pending = sorted(type(item).__name__ for item in db_session.new)
        observed_flushes.append((requested, pending))
        return actual_flush(objects)

    monkeypatch.setattr(db_session, "flush", observed_flush)
    stored = store_v4_candidate(
        db_session,
        directive_id=directive.id,
        parsed=_parsed(_envelope(directive, fragment)),
        actor=actor,
        membership_id=membership.id,
        idempotency_key="parent-before-bindings",
    )

    assert [requested for requested, _ in observed_flushes[:4]] == [
        ["ADV4CandidateProposal"],
        ["ADV4CandidateEvidenceBinding"],
        ["ADV4CandidateSubmission"],
        [],
    ]
    assert observed_flushes[0][1] == ["ADV4CandidateProposal"]
    assert observed_flushes[1][1] == ["ADV4CandidateEvidenceBinding"]
    assert observed_flushes[2][1] == ["ADV4CandidateSubmission"]
    assert observed_flushes[3][1] == ["ADV4CandidateProposalEvent"]
    assert db_session.query(ADV4CandidateEvidenceBinding).filter_by(
        proposal_id=stored.proposal.id
    ).count() == 1


def test_idempotency_conflict_and_ineligible_lifecycle_fail_closed(db_session):
    actor, membership, directive, fragment = _setup(db_session)
    original = _parsed(_envelope(directive, fragment))
    store_v4_candidate(
        db_session, directive_id=directive.id, parsed=original, actor=actor,
        membership_id=membership.id, idempotency_key="same-key",
    )
    db_session.commit()
    changed_value = _envelope(directive, fragment, decision_key="different-decision")
    with pytest.raises(ADV4Error, match="Idempotency key") as conflict:
        store_v4_candidate(
            db_session, directive_id=directive.id, parsed=_parsed(changed_value), actor=actor,
            membership_id=membership.id, idempotency_key="same-key",
        )
    assert conflict.value.http_status == 409
    db_session.rollback()
    root = db_session.query(ADEvidenceFragmentLifecycleEvent).filter_by(fragment_id=fragment.id).one()
    db_session.add(ADEvidenceFragmentLifecycleEvent(
        fragment_id=fragment.id, event_type="quarantined", actor_user_id=actor.id,
        reason="stale", sequence_number=1, predecessor_event_hash=root.event_hash,
        event_hash="d" * 64,
    ))
    db_session.commit()
    with pytest.raises(ADV4Error) as lifecycle:
        store_v4_candidate(
            db_session, directive_id=directive.id, parsed=_parsed(changed_value), actor=actor,
            membership_id=membership.id, idempotency_key="new-key",
        )
    assert lifecycle.value.code == "evidence_not_admitted"


def test_maintenance_membership_cannot_write(db_session):
    actor, _, directive, fragment = _setup(db_session)
    shop = create_organization(db_session, "Shop", "maintenance_shop")
    shop_membership = add_membership(db_session, shop, actor, "maintenance_admin")
    with pytest.raises(ADV4Error) as caught:
        store_v4_candidate(
            db_session, directive_id=directive.id,
            parsed=_parsed(_envelope(directive, fragment)), actor=actor,
            membership_id=shop_membership.id, idempotency_key="denied",
        )
    assert caught.value.http_status == 403


def test_distinct_origins_preserve_same_correction_relationship(db_session):
    actor, membership, directive, fragment = _setup(db_session)
    first = store_v4_candidate(
        db_session, directive_id=directive.id, parsed=_parsed(_envelope(directive, fragment)),
        actor=actor, membership_id=membership.id, idempotency_key="origin-base",
    )
    db_session.commit()
    corrected = _envelope(directive, fragment, decision_key="decision-corrected")
    corrected["submissionContext"]["relationships"] = [{
        "relationshipKey": "correction-base",
        "relationType": "corrects_candidate",
        "predecessorProposalId": first.proposal.id,
        "reason": "source-backed correction",
        "evidenceKeys": ["ev-rule"],
    }]
    one = store_v4_candidate(
        db_session, directive_id=directive.id, parsed=_parsed(corrected), actor=actor,
        membership_id=membership.id, idempotency_key="origin-correction-1",
    )
    db_session.commit()
    two = store_v4_candidate(
        db_session, directive_id=directive.id, parsed=_parsed(corrected), actor=actor,
        membership_id=membership.id, idempotency_key="origin-correction-2",
    )
    db_session.commit()
    assert one.proposal.id == two.proposal.id
    assert one.submission.id != two.submission.id
    rows = db_session.query(ADV4CandidateSubmissionRelationship).filter_by(
        predecessor_proposal_id=first.proposal.id
    ).all()
    assert len(rows) == 2
    assert len({row.relationship_hash for row in rows}) == 2
