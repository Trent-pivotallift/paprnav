from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any, Iterable

from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.core import (
    ADEvidenceFragmentLifecycleEvent,
    ADV4CandidateAppChangeDependency,
    ADV4CandidateAppCondition,
    ADV4CandidateAppDatum,
    ADV4CandidateAppDesignationGroup,
    ADV4CandidateAppDesignationGroupMember,
    ADV4CandidateAppEvidenceLink,
    ADV4CandidateAppExpression,
    ADV4CandidateAppExpressionEdge,
    ADV4CandidateAppDesignationRange,
    ADV4CandidateAppDesignationScope,
    ADV4CandidateAppDesignationValue,
    ADV4CandidateAppIdentityMapping,
    ADV4CandidateAppMaterializationRequest,
    ADV4CandidateAppProjection,
    ADV4CandidateAppProjectionEvent,
    ADV4CandidateAppProductScope,
    ADV4CandidateAppRule,
    ADV4CandidateAppRuleExclusion,
    ADV4CandidateAppSearchHint,
    ADV4CandidateAppSearchHintGroup,
    ADV4CandidateAppSearchHintMember,
    ADV4CandidateAppSemanticNode,
    ADV4CandidateAppValueAssertion,
    ADV4CandidateCorrection,
    ADV4CandidateCorrectionEvidenceLink,
    ADV4CandidateCorrectionRef,
    ADV4CandidateCorrectionSemanticBinding,
    ADV4CandidateEvidenceBinding,
    ADV4CandidateProposal,
    ADV4CandidateSubmissionRelationship,
    OrganizationMembership,
    User,
)
from app.services.ad_v4_candidates import (
    ADV4Error,
    CANONICALIZATION_VERSION_V2,
    VALIDATOR_VERSION_V2,
    _advisory_lock,
    _authorization,
    canonical_bytes,
    require_v4_database_gate,
    verified_candidate,
)


MATERIALIZER_VERSION = "paprnav-ad-v4-app-materializer-2"
POLICY_NAME = "paprnav-platform-admin-v4-applicability-materialize"
POLICY_VERSION = "1"
ENDPOINT_ACTION = "materialize_ad_v4_applicability"
SUBTREE_DOMAIN = b"paprnav:ad_extraction_v4:applicability-subtree:paprnav-ad-v4-c14n-2\x00"
PROJECTION_DOMAIN = b"paprnav:ad_extraction_v4:applicability-projection:2\x00"
EVENT_DOMAIN = b"paprnav:ad_extraction_v4:applicability-projection-event:2\x00"
ROW_DOMAIN = b"paprnav:ad_extraction_v4:applicability-row:2\x00"
APP_FIELDS = (
    "productScopes", "conditionDefinitions", "applicabilityRules",
    "applicabilitySearchHints",
)


@dataclass(frozen=True)
class MaterializedApplicability:
    projection: ADV4CandidateAppProjection
    request: ADV4CandidateAppMaterializationRequest
    created: bool
    idempotent_retry: bool


def _hash(domain: bytes, value: Any) -> str:
    return hashlib.sha256(domain + canonical_bytes(value, CANONICALIZATION_VERSION_V2)).hexdigest()


def _row_id(prefix: str, table: str, identity: Any) -> tuple[str, str]:
    full = _hash(ROW_DOMAIN, {"table": table, "identity": identity})
    return f"{prefix}_{full[:32]}", full


def _app_subtree(proposal: dict[str, Any]) -> dict[str, Any]:
    return {field: proposal[field] for field in APP_FIELDS}


def _require_application_gate(*, materialize: bool) -> None:
    settings = get_settings()
    if not settings.ad_v4_slice3a_routes_enabled:
        raise ADV4Error("capability_disabled", "", "Slice-3A application capability is disabled", http_status=404)
    if materialize and not settings.ad_v4_validator2_writes_enabled:
        raise ADV4Error("validator2_write_gate_disabled", "", "Validator-2 application capability is disabled", http_status=409)


def _lock_database_gates(db: Session, *, materialize: bool) -> None:
    if materialize:
        require_v4_database_gate(db, "validator2_write_enabled", lock=True)
    require_v4_database_gate(db, "materializer3a_enabled", lock=materialize)


def _lock_supersession_ad_numbers(db: Session, candidate: ADV4CandidateProposal) -> None:
    if db.bind is not None and db.bind.dialect.name == "postgresql":
        db.execute(
            text("SELECT paprnav_v4_lock_app_ad_numbers(:proposal_id)"),
            {"proposal_id": candidate.id},
        )
        return
    proposal = candidate.parsed_json
    numbers = {
        value
        for value in (
            proposal["directiveIdentity"]["adNumber"].get("value"),
            *(
                number
                for relation in proposal["supersessionRelations"]
                for number in (relation["predecessorAdNumber"], relation["successorAdNumber"])
            ),
        )
        if value is not None
    }
    for ad_number in sorted(numbers):
        _advisory_lock(db, f"applicability-ad-resolution:{ad_number}")


def _reject_new_predecessor_ambiguity(db: Session, candidate: ADV4CandidateProposal) -> None:
    ad_number = candidate.parsed_json["directiveIdentity"]["adNumber"]
    if ad_number.get("state") != "known":
        return
    if db.scalar(select(ADV4CandidateAppProjection.id).where(
        ADV4CandidateAppProjection.proposal_id == candidate.id,
        ADV4CandidateAppProjection.materializer_version == MATERIALIZER_VERSION,
    )) is not None:
        return
    existing_ids = []
    for possible in db.scalars(select(ADV4CandidateAppProjection)).all():
        possible_candidate = verified_candidate(db, possible.proposal_id)
        possible_ad = possible_candidate.parsed_json["directiveIdentity"]["adNumber"]
        if possible_ad.get("state") == "known" and possible_ad.get("value") == ad_number["value"]:
            existing_ids.append(possible.id)
    if existing_ids and db.scalar(select(ADV4CandidateAppChangeDependency.id).where(
        ADV4CandidateAppChangeDependency.resolution_state == "resolved_candidate",
        ADV4CandidateAppChangeDependency.target_projection_id.in_(existing_ids),
    ).limit(1)) is not None:
        raise ADV4Error(
            "supersession_resolution_conflict", "",
            "A resolved successor already depends on the unique predecessor identity",
            http_status=409,
        )


def authorize_projection_audit(db: Session, actor: User, membership_id: str) -> OrganizationMembership:
    _require_application_gate(materialize=False)
    membership = _authorization(db, actor, membership_id)
    _lock_database_gates(db, materialize=False)
    return membership


def _verify_live_evidence(db: Session, proposal: ADV4CandidateProposal) -> dict[str, ADV4CandidateEvidenceBinding]:
    bindings = db.scalars(
        select(ADV4CandidateEvidenceBinding)
        .where(ADV4CandidateEvidenceBinding.proposal_id == proposal.id)
        .order_by(ADV4CandidateEvidenceBinding.fragment_id, ADV4CandidateEvidenceBinding.evidence_key)
        .with_for_update()
    ).all()
    if len(bindings) != proposal.binding_count:
        raise ADV4Error("candidate_integrity", "", "Candidate evidence binding count differs", http_status=409)
    result: dict[str, ADV4CandidateEvidenceBinding] = {}
    for binding in bindings:
        events = db.scalars(
            select(ADEvidenceFragmentLifecycleEvent)
            .where(ADEvidenceFragmentLifecycleEvent.fragment_id == binding.fragment_id)
            .order_by(ADEvidenceFragmentLifecycleEvent.sequence_number)
        ).all()
        if (
            len(events) != 1
            or events[0].id != binding.admitted_event_id
            or events[0].event_type != "admitted"
            or events[0].event_hash != binding.admitted_event_hash
        ):
            raise ADV4Error("evidence_not_admitted", "", "Candidate evidence is no longer an admitted root", http_status=409)
        if binding.validator_version != proposal.validator_version or binding.canonicalization_version != proposal.canonicalization_version:
            raise ADV4Error("candidate_integrity", "", "Candidate evidence version differs", http_status=409)
        result[binding.evidence_key] = binding
    return result


def _semantic_type(pointer: str, value: dict[str, Any]) -> tuple[str, str] | None:
    if "nodeType" in value:
        return "expression", pointer
    candidates = (
        ("scopeKey", "product_scope"), ("conditionKey", "condition"),
        ("ruleKey", "applicability_rule"), ("hintKey", "search_hint"),
        ("groupKey", "designation_group"), ("memberKey", "designation_group_member"),
    )
    for key, kind in candidates:
        if key in value:
            if "/manufacturerModelGroups/" in pointer:
                kind = "search_hint_group" if key == "groupKey" else "search_hint_model"
            return kind, str(value[key])
    if "kind" in value and pointer.endswith(("/modelScope", "/serialScope", "/partNumberScope")):
        return "designation_scope", pointer.rsplit("/", 1)[-1]
    return None


def _flatten(
    value: Any,
    *,
    pointer: str,
    projection_id: str,
    proposal_id: str,
    parent_node_id: str | None,
    semantic_rows: list[ADV4CandidateAppSemanticNode],
    datum_rows: list[ADV4CandidateAppDatum],
    node_by_pointer: dict[str, ADV4CandidateAppSemanticNode],
    ordinal: int = 0,
) -> None:
    current_node_id = parent_node_id
    if isinstance(value, dict):
        semantic = _semantic_type(pointer, value)
        if semantic is not None:
            node_type, node_key = semantic
            if node_type in {
                "designation_scope", "designation_group", "designation_group_member",
                "search_hint_group", "search_hint_model",
            }:
                # These keys are only container-local in the canonical schema.
                # The source pointer is the proposal-scoped occurrence identity.
                node_key = pointer
            node_id, identity_hash = _row_id("avn", "semantic-node", {
                "projectionId": projection_id, "nodeType": node_type,
                "nodeKey": node_key, "pointer": pointer,
            })
            node = ADV4CandidateAppSemanticNode(
                id=node_id, identity_hash=identity_hash, projection_id=projection_id,
                proposal_id=proposal_id, parent_node_id=parent_node_id,
                node_type=node_type, node_key=node_key, source_pointer=pointer,
                canonical_node_hash=hashlib.sha256(canonical_bytes(value, CANONICALIZATION_VERSION_V2)).hexdigest(),
                canonical_ordinal=ordinal,
            )
            semantic_rows.append(node)
            node_by_pointer[pointer] = node
            current_node_id = node_id
    kind = "object" if isinstance(value, dict) else "array" if isinstance(value, list) else "boolean" if isinstance(value, bool) else "string"
    datum_id, datum_hash = _row_id("avd", "datum", {"projectionId": projection_id, "pointer": pointer, "kind": kind, "value": value if kind in {"string", "boolean"} else kind})
    datum_rows.append(ADV4CandidateAppDatum(
        id=datum_id, projection_id=projection_id, proposal_id=proposal_id,
        semantic_node_id=current_node_id, json_pointer=pointer,
        parent_pointer=None if pointer == "" else pointer.rsplit("/", 1)[0],
        property_name=None if pointer == "" or pointer.rsplit("/", 1)[-1].isdigit() else pointer.rsplit("/", 1)[-1],
        array_ordinal=ordinal if pointer and pointer.rsplit("/", 1)[-1].isdigit() else None,
        value_kind=kind, string_value=value if isinstance(value, str) else None,
        boolean_value=value if isinstance(value, bool) else None, value_hash=datum_hash,
    ))
    if isinstance(value, dict):
        for key in sorted(value, key=lambda item: item.encode("utf-16-be")):
            child_pointer = f"{pointer}/{key}" if pointer else f"/{key}"
            _flatten(value[key], pointer=child_pointer, projection_id=projection_id,
                     proposal_id=proposal_id, parent_node_id=current_node_id,
                     semantic_rows=semantic_rows, datum_rows=datum_rows,
                     node_by_pointer=node_by_pointer)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _flatten(child, pointer=f"{pointer}/{index}", projection_id=projection_id,
                     proposal_id=proposal_id, parent_node_id=current_node_id,
                     semantic_rows=semantic_rows, datum_rows=datum_rows,
                     node_by_pointer=node_by_pointer, ordinal=index)


def _evidence_purpose(node: ADV4CandidateAppSemanticNode) -> str:
    if node.node_type == "value_assertion":
        if node.source_pointer.startswith("/applicabilitySearchHints/") and node.source_pointer.endswith("/sourceDisplayText"):
            return "search_hint_clause"
        if node.source_pointer.startswith("/conditionDefinitions/"):
            if "/members/" in node.source_pointer and node.source_pointer.endswith("/manufacturer"):
                return "identity_support"
            return "subject_value"
        return "identity_support"
    return {
        "product_scope": "scope_clause", "designation_scope": "designation_scope",
        "condition": "condition_clause", "designation_group": "condition_clause",
        "designation_group_member": "subject_value", "applicability_rule": "rule_clause",
        "search_hint": "search_hint_clause", "search_hint_group": "search_hint_clause",
        "search_hint_model": "search_hint_clause",
        "change_dependency": "supersession_clause",
    }.get(node.node_type, "identity_support")


def _semantic_evidence_keys(proposal: dict[str, Any], node: ADV4CandidateAppSemanticNode) -> list[str]:
    if node.node_type == "identity_mapping":
        return []
    value = _node_value(proposal, node.source_pointer)
    if isinstance(value, dict):
        return value.get("evidenceKeys", [])
    if node.node_type == "value_assertion" and node.source_pointer.endswith("/manufacturer/sourceValue"):
        manufacturer_pointer = node.source_pointer.rsplit("/", 1)[0]
        manufacturer = _node_value(proposal, manufacturer_pointer)
        return manufacturer["normalizedIdentity"]["evidenceKeys"]
    return []


def _node_value(proposal: dict[str, Any], pointer: str) -> Any:
    first = pointer.strip("/").split("/", 1)[0] if pointer else ""
    value: Any = _app_subtree(proposal) if first in APP_FIELDS else proposal
    if pointer:
        for token in pointer.strip("/").split("/"):
            value = value[int(token)] if isinstance(value, list) else value[token]
    return value


def _identity_rows(
    projection: ADV4CandidateAppProjection,
    proposal: dict[str, Any],
    semantic_rows: list[ADV4CandidateAppSemanticNode],
    datum_rows: list[ADV4CandidateAppDatum],
) -> list[ADV4CandidateAppIdentityMapping]:
    rows: list[ADV4CandidateAppIdentityMapping] = []
    by_pointer = {row.source_pointer: row for row in semantic_rows}
    for node in list(semantic_rows):
        value = _node_value(proposal, node.source_pointer)
        occurrences: list[dict[str, Any]] = []
        if node.node_type == "product_scope" and isinstance(value.get("manufacturer"), dict):
            manufacturer = value["manufacturer"]
            normalized_identity = manufacturer["normalizedIdentity"]
            state = normalized_identity["state"]
            occurrences.append({
                "kind": "manufacturer", "source": manufacturer["sourceValue"],
                "origin": "candidate_payload", "state": state,
                "normalized": normalized_identity.get("value"),
                "reason": normalized_identity.get("reason"),
                "temporal": normalized_identity.get("temporalScope", {}).get("kind"),
                "namespace": "candidate" if state == "known" else None,
                "version": "1" if state == "known" else None,
                "occurrence": by_pointer[f"{node.source_pointer}/manufacturer/sourceValue"],
                "evidence_parent": node,
            })
        elif (
            node.node_type == "designation_scope"
            and value.get("kind") == "listed"
            and node.source_pointer.endswith("/modelScope")
        ):
            for index, source in enumerate(value["sourceDesignations"]):
                child_pointer = f"{node.source_pointer}/sourceDesignations/{index}"
                child = by_pointer.get(child_pointer)
                if child is None:
                    child_id, child_hash = _row_id("avn", "designation-value", {"projectionId": projection.id, "pointer": child_pointer, "value": source})
                    child = ADV4CandidateAppSemanticNode(id=child_id, identity_hash=child_hash, projection_id=projection.id, proposal_id=projection.proposal_id, parent_node_id=node.id, node_type="designation_value", node_key=f"{node.node_key}:{index}", source_pointer=child_pointer, canonical_node_hash=hashlib.sha256(canonical_bytes(source, CANONICALIZATION_VERSION_V2)).hexdigest(), canonical_ordinal=index)
                    semantic_rows.append(child)
                    by_pointer[child_pointer] = child
                    for datum in datum_rows:
                        if datum.json_pointer == child_pointer:
                            datum.semantic_node_id = child.id
                            break
                occurrences.append({
                    "kind": "model", "source": source,
                    "origin": "no_normalized_identity", "state": "unknown",
                    "normalized": None, "reason": "not_extracted",
                    "temporal": "directive_version", "namespace": None,
                    "version": None, "occurrence": child,
                    "evidence_parent": node,
                })
        elif node.node_type == "condition":
            subject = value["subject"]
            for canonical_field, identity_kind in (
                ("manufacturer", "manufacturer"),
                ("modelOrSeries", "model_or_series"),
            ):
                assertion_value = subject.get(canonical_field)
                if isinstance(assertion_value, dict) and assertion_value.get("state") == "known":
                    occurrence = by_pointer[f"{node.source_pointer}/subject/{canonical_field}"]
                    occurrences.append({
                        "kind": identity_kind, "source": assertion_value["value"],
                        "origin": "source_only", "state": "unknown",
                        "normalized": None, "reason": "not_extracted",
                        "temporal": "directive_version", "namespace": None,
                        "version": None, "occurrence": occurrence,
                        "evidence_parent": node,
                    })
        elif node.node_type == "search_hint_group":
            manufacturer = value["manufacturer"]
            if manufacturer["state"] == "known":
                occurrence = by_pointer[f"{node.source_pointer}/manufacturer"]
                occurrences.append({
                    "kind": "manufacturer", "source": manufacturer["value"],
                    "origin": "source_only", "state": "unknown",
                    "normalized": None, "reason": "not_extracted",
                    "temporal": "directive_version", "namespace": None,
                    "version": None, "occurrence": occurrence,
                    "evidence_parent": node,
                })
        elif node.node_type in {"designation_group_member", "search_hint_model"}:
            source = value.get("sourceDesignation") or value.get("expressionText")
            evidence_parent = by_pointer[node.source_pointer.rsplit("/members/", 1)[0]]
            occurrences.append({
                "kind": "model" if value["designationKind"] == "model" else "series",
                "source": source, "origin": "source_only", "state": "unknown",
                "normalized": None, "reason": "not_extracted",
                "temporal": "directive_version", "namespace": None,
                "version": None, "occurrence": node,
                "evidence_parent": evidence_parent,
            })
            manufacturer = value["manufacturer"]
            if manufacturer["state"] == "known":
                occurrence = by_pointer[f"{node.source_pointer}/manufacturer"]
                occurrences.append({
                    "kind": "manufacturer", "source": manufacturer["value"],
                    "origin": "source_only", "state": "unknown",
                    "normalized": None, "reason": "not_extracted",
                    "temporal": "directive_version", "namespace": None,
                    "version": None, "occurrence": occurrence,
                    "evidence_parent": evidence_parent,
                })
        for item in occurrences:
            identity_kind = item["kind"]
            source = item["source"]
            occurrence = item["occurrence"]
            row_id, full_hash = _row_id("avi", "identity-mapping", {"projectionId": projection.id, "kind": identity_kind, "occurrence": occurrence.id})
            mapping_node_id, mapping_node_hash = _row_id("avn", "semantic-node", {
                "projectionId": projection.id, "nodeType": "identity_mapping",
                "nodeKey": occurrence.id, "pointer": occurrence.source_pointer,
            })
            mapping_node = ADV4CandidateAppSemanticNode(
                id=mapping_node_id, identity_hash=mapping_node_hash,
                projection_id=projection.id, proposal_id=projection.proposal_id,
                parent_node_id=occurrence.id, node_type="identity_mapping",
                node_key=occurrence.id, source_pointer=occurrence.source_pointer,
                canonical_node_hash=hashlib.sha256(
                    canonical_bytes(_node_value(proposal, occurrence.source_pointer), CANONICALIZATION_VERSION_V2)
                ).hexdigest(),
                canonical_ordinal=occurrence.canonical_ordinal,
            )
            semantic_rows.append(mapping_node)
            rows.append(ADV4CandidateAppIdentityMapping(
                id=row_id, semantic_node_id=mapping_node.id,
                projection_id=projection.id, proposal_id=projection.proposal_id,
                source_occurrence_node_id=occurrence.id,
                evidence_parent_node_id=item["evidence_parent"].id,
                identity_kind=identity_kind, source_value=source,
                normalization_origin=item["origin"], normalized_state=item["state"],
                normalized_value=item["normalized"], reason=item["reason"],
                temporal_scope=item["temporal"],
                normalization_namespace=item["namespace"],
                normalization_version=item["version"],
                review_state="unreviewed_candidate", identity_hash=full_hash,
            ))
    return rows


def _augment_source_scope_semantics(
    projection_id: str,
    proposal_id: str,
    proposal: dict[str, Any],
    semantic_rows: list[ADV4CandidateAppSemanticNode],
    datum_rows: list[ADV4CandidateAppDatum],
) -> None:
    by_pointer = {row.source_pointer: row for row in semantic_rows}

    def add_assertion(pointer: str, parent: ADV4CandidateAppSemanticNode, value: Any) -> ADV4CandidateAppSemanticNode:
        node_id, node_hash = _row_id("avn", "semantic-node", {
            "projectionId": projection_id, "nodeType": "value_assertion",
            "nodeKey": pointer, "pointer": pointer,
        })
        assertion = ADV4CandidateAppSemanticNode(
            id=node_id, identity_hash=node_hash, projection_id=projection_id,
            proposal_id=proposal_id, parent_node_id=parent.id,
            node_type="value_assertion", node_key=pointer, source_pointer=pointer,
            canonical_node_hash=hashlib.sha256(
                canonical_bytes(value, CANONICALIZATION_VERSION_V2)
            ).hexdigest(),
            canonical_ordinal=0,
        )
        semantic_rows.append(assertion)
        by_pointer[pointer] = assertion
        for datum in datum_rows:
            if datum.json_pointer == pointer or datum.json_pointer.startswith(f"{pointer}/"):
                datum.semantic_node_id = assertion.id
        return assertion

    for product in [row for row in semantic_rows if row.node_type == "product_scope"]:
        value = _node_value(proposal, product.source_pointer)
        if "manufacturer" in value:
            pointer = f"{product.source_pointer}/manufacturer/sourceValue"
            source = value["manufacturer"]["sourceValue"]
            add_assertion(pointer, product, source)
    condition_fields = {
        "manufacturer": "manufacturer",
        "modelOrSeries": "model_or_series",
        "partNumber": "part_number",
        "serialNumber": "serial_number",
        "stcNumber": "stc_number",
        "attributeValue": "attribute_value",
    }
    for condition in [row for row in semantic_rows if row.node_type == "condition"]:
        value = _node_value(proposal, condition.source_pointer)
        subject = value["subject"]
        for canonical_field in condition_fields:
            if canonical_field in subject:
                pointer = f"{condition.source_pointer}/subject/{canonical_field}"
                add_assertion(pointer, condition, subject[canonical_field])
        group_pointer = f"{condition.source_pointer}/subject/designationGroup"
        group = by_pointer.get(group_pointer)
        if group is None:
            continue
        group_value = subject["designationGroup"]
        add_assertion(f"{group_pointer}/sourceDisplayText", group, group_value["sourceDisplayText"])
        for index, member_value in enumerate(group_value["members"]):
            member_pointer = f"{group_pointer}/members/{index}"
            member = by_pointer[member_pointer]
            add_assertion(f"{member_pointer}/manufacturer", member, member_value["manufacturer"])
    for hint in [row for row in semantic_rows if row.node_type == "search_hint"]:
        hint_value = _node_value(proposal, hint.source_pointer)
        add_assertion(f"{hint.source_pointer}/sourceDisplayText", hint, hint_value["sourceDisplayText"])
        for group_ordinal, group_value in enumerate(hint_value["manufacturerModelGroups"]):
            group_pointer = f"{hint.source_pointer}/manufacturerModelGroups/{group_ordinal}"
            group = by_pointer[group_pointer]
            add_assertion(f"{group_pointer}/manufacturer", group, group_value["manufacturer"])
            for member_ordinal, member_value in enumerate(group_value["members"]):
                member_pointer = f"{group_pointer}/members/{member_ordinal}"
                member = by_pointer[member_pointer]
                add_assertion(f"{member_pointer}/manufacturer", member, member_value["manufacturer"])
    for scope in [row for row in semantic_rows if row.node_type == "designation_scope"]:
        value = _node_value(proposal, scope.source_pointer)
        for ordinal, source in enumerate(value.get("sourceDesignations", [])):
            pointer = f"{scope.source_pointer}/sourceDesignations/{ordinal}"
            node_id, node_hash = _row_id("avn", "designation-value", {
                "projectionId": projection_id, "pointer": pointer, "value": source,
            })
            value_node = ADV4CandidateAppSemanticNode(
                id=node_id, identity_hash=node_hash, projection_id=projection_id,
                proposal_id=proposal_id, parent_node_id=scope.id,
                node_type="designation_value", node_key=f"{scope.node_key}:{ordinal}",
                source_pointer=pointer,
                canonical_node_hash=hashlib.sha256(canonical_bytes(source, CANONICALIZATION_VERSION_V2)).hexdigest(),
                canonical_ordinal=ordinal,
            )
            semantic_rows.append(value_node)
            by_pointer[pointer] = value_node
            for datum in datum_rows:
                if datum.json_pointer == pointer:
                    datum.semantic_node_id = value_node.id
                    break
        for ordinal, range_value in enumerate(value.get("ranges", [])):
            pointer = f"{scope.source_pointer}/ranges/{ordinal}"
            node_id, node_hash = _row_id("avn", "semantic-node", {
                "projectionId": projection_id, "nodeType": "designation_range",
                "nodeKey": pointer, "pointer": pointer,
            })
            range_node = ADV4CandidateAppSemanticNode(
                id=node_id, identity_hash=node_hash, projection_id=projection_id,
                proposal_id=proposal_id, parent_node_id=scope.id,
                node_type="designation_range", node_key=pointer, source_pointer=pointer,
                canonical_node_hash=hashlib.sha256(canonical_bytes(range_value, CANONICALIZATION_VERSION_V2)).hexdigest(),
                canonical_ordinal=ordinal,
            )
            semantic_rows.append(range_node)
            by_pointer[pointer] = range_node
            for datum in datum_rows:
                if datum.json_pointer == pointer or datum.json_pointer.startswith(f"{pointer}/"):
                    datum.semantic_node_id = range_node.id


def _source_scope_owner_rows(
    projection: ADV4CandidateAppProjection,
    proposal: dict[str, Any],
    semantic_rows: list[ADV4CandidateAppSemanticNode],
    identities: list[ADV4CandidateAppIdentityMapping],
) -> list[Any]:
    rows: list[Any] = []
    by_pointer_type = {(node.source_pointer, node.node_type): node for node in semantic_rows}
    mapping_by_occurrence = {row.source_occurrence_node_id: row for row in identities}

    def append_assertion(
        node: ADV4CandidateAppSemanticNode,
        parent_id: str,
        field_code: str,
        value: dict[str, Any] | str,
    ) -> None:
        if isinstance(value, str):
            state, text_value, reason, temporal_scope = "known", value, None, None
        else:
            state = value["state"]
            text_value = value.get("value")
            reason = value.get("reason")
            temporal_scope = value.get("temporalScope", {}).get("kind")
        rows.append(ADV4CandidateAppValueAssertion(
            semantic_node_id=node.id, projection_id=projection.id,
            proposal_id=projection.proposal_id, parent_semantic_node_id=parent_id,
            field_code=field_code, state=state, value_type="text",
            text_value=text_value, reason=reason, temporal_scope=temporal_scope,
        ))

    for product in [node for node in semantic_rows if node.node_type == "product_scope"]:
        value = _node_value(proposal, product.source_pointer)
        assertion = by_pointer_type.get((f"{product.source_pointer}/manufacturer/sourceValue", "value_assertion"))
        mapping = mapping_by_occurrence.get(assertion.id) if assertion is not None else None
        if assertion is not None:
            append_assertion(assertion, product.id, "manufacturer", value["manufacturer"]["sourceValue"])
        rows.append(ADV4CandidateAppProductScope(
            semantic_node_id=product.id, projection_id=projection.id,
            proposal_id=projection.proposal_id, scope_key=value["scopeKey"],
            product_role=value["productRole"],
            manufacturer_presence="present" if assertion is not None else "property_absent",
            manufacturer_source_value=value.get("manufacturer", {}).get("sourceValue"),
            manufacturer_identity_mapping_node_id=mapping.semantic_node_id if mapping else None,
            model_presence="present" if "modelScope" in value else "property_absent",
            serial_presence="present" if "serialScope" in value else "property_absent",
            part_number_presence="present" if "partNumberScope" in value else "property_absent",
        ))
    for scope in [node for node in semantic_rows if node.node_type == "designation_scope"]:
        value = _node_value(proposal, scope.source_pointer)
        field_name = scope.source_pointer.rsplit("/", 1)[-1]
        field_kind = {"modelScope": "model", "serialScope": "serial", "partNumberScope": "part_number"}[field_name]
        rows.append(ADV4CandidateAppDesignationScope(
            semantic_node_id=scope.id, projection_id=projection.id,
            proposal_id=projection.proposal_id, product_scope_node_id=scope.parent_node_id,
            field_kind=field_kind, scope_kind=value["kind"],
            series_expression=value.get("expression"), reason=value.get("reason"),
            temporal_scope=value.get("temporalScope", {}).get("kind"),
            evaluation_state="unknown" if value["kind"] == "series_expression" else "unevaluated",
            evaluator_contract="unsupported_expression" if value["kind"] == "series_expression" else "none",
        ))
    for node in [node for node in semantic_rows if node.node_type == "designation_value"]:
        mapping = mapping_by_occurrence.get(node.id)
        rows.append(ADV4CandidateAppDesignationValue(
            semantic_node_id=node.id, projection_id=projection.id,
            proposal_id=projection.proposal_id, designation_scope_id=node.parent_node_id,
            source_value=_node_value(proposal, node.source_pointer),
            canonical_ordinal=node.canonical_ordinal,
            identity_mapping_node_id=mapping.semantic_node_id if mapping else None,
        ))
    for node in [node for node in semantic_rows if node.node_type == "designation_range"]:
        value = _node_value(proposal, node.source_pointer)
        rows.append(ADV4CandidateAppDesignationRange(
            semantic_node_id=node.id, projection_id=projection.id,
            proposal_id=projection.proposal_id, designation_scope_id=node.parent_node_id,
            lower_value=value["lower"], upper_value=value["upper"],
            lower_inclusive=value["lowerInclusive"], upper_inclusive=value["upperInclusive"],
            polarity=value["polarity"], canonical_ordinal=node.canonical_ordinal,
            comparator_version="lexical_source_only_v1",
        ))
    condition_field_codes = {
        "manufacturer": "manufacturer",
        "modelOrSeries": "model_or_series",
        "partNumber": "part_number",
        "serialNumber": "serial_number",
        "stcNumber": "stc_number",
        "attributeValue": "attribute_value",
    }
    for condition in [node for node in semantic_rows if node.node_type == "condition"]:
        value = _node_value(proposal, condition.source_pointer)
        subject = value["subject"]
        group_pointer = f"{condition.source_pointer}/subject/designationGroup"
        group = by_pointer_type.get((group_pointer, "designation_group"))
        rows.append(ADV4CandidateAppCondition(
            semantic_node_id=condition.id, projection_id=projection.id,
            proposal_id=projection.proposal_id, condition_key=value["conditionKey"],
            condition_type=value["conditionType"], operator=value["operator"],
            temporal_basis=value["temporalBasis"]["kind"],
            comparator_presence="present" if "comparatorVersion" in value else "property_absent",
            comparator_version=value.get("comparatorVersion"),
            subject_product_role_presence="present" if "productRole" in subject else "property_absent",
            subject_product_role=subject.get("productRole"),
            subject_attribute_key_presence="present" if "attributeKey" in subject else "property_absent",
            subject_attribute_key=subject.get("attributeKey"),
            designation_group_presence="present" if group is not None else "property_absent",
            designation_group_node_id=group.id if group is not None else None,
            evaluation_state="unevaluated", evaluator_contract="none",
        ))
        for canonical_field, field_code in condition_field_codes.items():
            if canonical_field not in subject:
                continue
            assertion = by_pointer_type[(
                f"{condition.source_pointer}/subject/{canonical_field}",
                "value_assertion",
            )]
            append_assertion(assertion, condition.id, field_code, subject[canonical_field])
        if group is None:
            continue
        group_value = subject["designationGroup"]
        display = by_pointer_type[(f"{group_pointer}/sourceDisplayText", "value_assertion")]
        rows.append(ADV4CandidateAppDesignationGroup(
            semantic_node_id=group.id, projection_id=projection.id,
            proposal_id=projection.proposal_id, condition_node_id=condition.id,
            group_key=group_value["groupKey"], association=group_value["association"],
            source_display_assertion_node_id=display.id,
            reason=group_value.get("reason"),
            temporal_scope=group_value.get("temporalScope", {}).get("kind"),
            canonical_ordinal=0,
        ))
        append_assertion(display, group.id, "source_display_text", group_value["sourceDisplayText"])
        for ordinal, member_value in enumerate(group_value["members"]):
            member_pointer = f"{group_pointer}/members/{ordinal}"
            member = by_pointer_type[(member_pointer, "designation_group_member")]
            manufacturer = by_pointer_type[(f"{member_pointer}/manufacturer", "value_assertion")]
            designation_mapping = mapping_by_occurrence[member.id]
            rows.append(ADV4CandidateAppDesignationGroupMember(
                semantic_node_id=member.id, projection_id=projection.id,
                proposal_id=projection.proposal_id, group_node_id=group.id,
                member_key=member_value["memberKey"],
                designation_kind=member_value["designationKind"],
                source_designation=member_value.get("sourceDesignation"),
                expression_text=member_value.get("expressionText"),
                manufacturer_assertion_node_id=manufacturer.id,
                manufacturer_state=member_value["manufacturer"]["state"],
                manufacturer_value=member_value["manufacturer"].get("value"),
                manufacturer_reason=member_value["manufacturer"].get("reason"),
                manufacturer_temporal_scope=member_value["manufacturer"].get("temporalScope", {}).get("kind"),
                evaluation_state="unevaluated" if member_value["designationKind"] == "series_expression" else None,
                evaluation_reason="unsupported_expression" if member_value["designationKind"] == "series_expression" else None,
                canonical_ordinal=ordinal,
                designation_identity_mapping_node_id=designation_mapping.semantic_node_id,
            ))
            append_assertion(manufacturer, member.id, "manufacturer", member_value["manufacturer"])
    return rows


def _rule_owner_rows(
    projection: ADV4CandidateAppProjection,
    proposal: dict[str, Any],
    semantic_rows: list[ADV4CandidateAppSemanticNode],
) -> list[Any]:
    rows: list[Any] = []
    by_pointer = {node.source_pointer: node for node in semantic_rows}
    scopes_by_key = {
        node.node_key: node for node in semantic_rows if node.node_type == "product_scope"
    }
    conditions_by_key = {
        node.node_key: node for node in semantic_rows if node.node_type == "condition"
    }
    rules_by_key = {
        node.node_key: node for node in semantic_rows if node.node_type == "applicability_rule"
    }

    def append_expression(
        value: dict[str, Any],
        *,
        pointer: str,
        root_pointer: str,
        owning_rule: ADV4CandidateAppSemanticNode,
        context: str,
    ) -> None:
        node = by_pointer[pointer]
        node_type = value["nodeType"]
        if node_type == "requirement_state_ref":
            raise ADV4Error(
                "cross_namespace_reference", pointer,
                "Applicability rules cannot reference requirement state",
            )
        scope_node = scopes_by_key.get(value.get("scopeKey"))
        condition_node = conditions_by_key.get(value.get("conditionKey"))
        referenced_rule = rules_by_key.get(value.get("ruleKey"))
        if (
            (node_type == "scope_ref" and scope_node is None)
            or (node_type == "predicate_ref" and condition_node is None)
            or (node_type == "rule_ref" and referenced_rule is None)
        ):
            raise ADV4Error("unresolved_reference", pointer, "Expression reference is unresolved")
        relative_path = "/" if pointer == root_pointer else pointer[len(root_pointer):]
        rows.append(ADV4CandidateAppExpression(
            semantic_node_id=node.id, projection_id=projection.id,
            proposal_id=projection.proposal_id,
            owning_rule_node_id=owning_rule.id,
            expression_context=context, expression_path=relative_path,
            expression_node_type=node_type,
            result_domain="true_false_unknown", evaluator_contract="none",
            scope_node_id=scope_node.id if node_type == "scope_ref" else None,
            condition_node_id=condition_node.id if node_type == "predicate_ref" else None,
            referenced_rule_node_id=referenced_rule.id if node_type == "rule_ref" else None,
        ))
        children: list[tuple[str, dict[str, Any]]] = []
        if node_type == "not":
            children = [(f"{pointer}/operand", value["operand"])]
        elif node_type in {"all", "any"}:
            children = [
                (f"{pointer}/operands/{ordinal}", child)
                for ordinal, child in enumerate(value["operands"])
            ]
        for sequence, (child_pointer, child_value) in enumerate(children):
            child = by_pointer[child_pointer]
            rows.append(ADV4CandidateAppExpressionEdge(
                projection_id=projection.id, proposal_id=projection.proposal_id,
                owning_rule_node_id=owning_rule.id,
                expression_context=context, parent_expression_id=node.id,
                child_expression_id=child.id, sequence=sequence,
            ))
            append_expression(
                child_value, pointer=child_pointer, root_pointer=root_pointer,
                owning_rule=owning_rule, context=context,
            )

    for ordinal, value in enumerate(proposal["applicabilityRules"]):
        pointer = f"/applicabilityRules/{ordinal}"
        rule_node = by_pointer[pointer]
        scope_pointer = f"{pointer}/scopeExpression"
        condition_pointer = f"{pointer}/conditionExpression"
        scope_root = by_pointer[scope_pointer]
        condition_root = by_pointer.get(condition_pointer)
        rows.append(ADV4CandidateAppRule(
            semantic_node_id=rule_node.id, projection_id=projection.id,
            proposal_id=projection.proposal_id, rule_key=value["ruleKey"],
            scope_expression_node_id=scope_root.id,
            condition_presence="present" if "conditionExpression" in value else "property_absent",
            condition_expression_node_id=condition_root.id if condition_root else None,
            evaluator_contract="none",
        ))
        append_expression(
            value["scopeExpression"], pointer=scope_pointer,
            root_pointer=scope_pointer, owning_rule=rule_node, context="scope",
        )
        if condition_root is not None:
            append_expression(
                value["conditionExpression"], pointer=condition_pointer,
                root_pointer=condition_pointer, owning_rule=rule_node,
                context="condition",
            )
        for exclusion_ordinal, excluded_key in enumerate(value["exclusionRuleKeys"]):
            excluded_rule = rules_by_key.get(excluded_key)
            if excluded_rule is None:
                raise ADV4Error("unresolved_reference", pointer, "Rule exclusion is unresolved")
            rows.append(ADV4CandidateAppRuleExclusion(
                projection_id=projection.id, proposal_id=projection.proposal_id,
                rule_node_id=rule_node.id,
                excluded_rule_node_id=excluded_rule.id,
                canonical_ordinal=exclusion_ordinal,
            ))
    return rows


def _search_hint_owner_rows(
    projection: ADV4CandidateAppProjection,
    proposal: dict[str, Any],
    semantic_rows: list[ADV4CandidateAppSemanticNode],
    identities: list[ADV4CandidateAppIdentityMapping],
) -> list[Any]:
    rows: list[Any] = []
    by_pointer_type = {(node.source_pointer, node.node_type): node for node in semantic_rows}
    mapping_by_occurrence = {row.source_occurrence_node_id: row for row in identities}

    def append_assertion(
        node: ADV4CandidateAppSemanticNode,
        parent_id: str,
        field_code: str,
        value: dict[str, Any],
    ) -> None:
        rows.append(ADV4CandidateAppValueAssertion(
            semantic_node_id=node.id, projection_id=projection.id,
            proposal_id=projection.proposal_id, parent_semantic_node_id=parent_id,
            field_code=field_code, state=value["state"], value_type="text",
            text_value=value.get("value"), reason=value.get("reason"),
            temporal_scope=value.get("temporalScope", {}).get("kind"),
        ))

    for hint_ordinal, hint_value in enumerate(proposal["applicabilitySearchHints"]):
        hint_pointer = f"/applicabilitySearchHints/{hint_ordinal}"
        hint = by_pointer_type[(hint_pointer, "search_hint")]
        display = by_pointer_type[(f"{hint_pointer}/sourceDisplayText", "value_assertion")]
        rows.append(ADV4CandidateAppSearchHint(
            semantic_node_id=hint.id, projection_id=projection.id,
            proposal_id=projection.proposal_id, hint_key=hint_value["hintKey"],
            product_role=hint_value["productRole"],
            source_display_assertion_node_id=display.id,
            controlling=False, exhaustive=False,
        ))
        append_assertion(display, hint.id, "source_display_text", hint_value["sourceDisplayText"])
        for group_ordinal, group_value in enumerate(hint_value["manufacturerModelGroups"]):
            group_pointer = f"{hint_pointer}/manufacturerModelGroups/{group_ordinal}"
            group = by_pointer_type[(group_pointer, "search_hint_group")]
            manufacturer = by_pointer_type[(f"{group_pointer}/manufacturer", "value_assertion")]
            rows.append(ADV4CandidateAppSearchHintGroup(
                semantic_node_id=group.id, projection_id=projection.id,
                proposal_id=projection.proposal_id, hint_node_id=hint.id,
                group_key=group_value["groupKey"],
                manufacturer_assertion_node_id=manufacturer.id,
                manufacturer_state=group_value["manufacturer"]["state"],
                manufacturer_value=group_value["manufacturer"].get("value"),
                manufacturer_reason=group_value["manufacturer"].get("reason"),
                manufacturer_temporal_scope=group_value["manufacturer"].get("temporalScope", {}).get("kind"),
                association=group_value["association"], reason=group_value.get("reason"),
                temporal_scope=group_value.get("temporalScope", {}).get("kind"),
                canonical_ordinal=group_ordinal,
            ))
            append_assertion(manufacturer, group.id, "manufacturer", group_value["manufacturer"])
            for member_ordinal, member_value in enumerate(group_value["members"]):
                member_pointer = f"{group_pointer}/members/{member_ordinal}"
                member = by_pointer_type[(member_pointer, "search_hint_model")]
                member_manufacturer = by_pointer_type[(f"{member_pointer}/manufacturer", "value_assertion")]
                designation_mapping = mapping_by_occurrence[member.id]
                rows.append(ADV4CandidateAppSearchHintMember(
                    semantic_node_id=member.id, projection_id=projection.id,
                    proposal_id=projection.proposal_id, group_node_id=group.id,
                    member_key=member_value["memberKey"],
                    designation_kind=member_value["designationKind"],
                    source_designation=member_value.get("sourceDesignation"),
                    expression_text=member_value.get("expressionText"),
                    manufacturer_assertion_node_id=member_manufacturer.id,
                    manufacturer_state=member_value["manufacturer"]["state"],
                    manufacturer_value=member_value["manufacturer"].get("value"),
                    manufacturer_reason=member_value["manufacturer"].get("reason"),
                    manufacturer_temporal_scope=member_value["manufacturer"].get("temporalScope", {}).get("kind"),
                    evaluation_state="unevaluated" if member_value["designationKind"] == "series_expression" else None,
                    evaluation_reason="unsupported_expression" if member_value["designationKind"] == "series_expression" else None,
                    canonical_ordinal=member_ordinal,
                    designation_identity_mapping_node_id=designation_mapping.semantic_node_id,
                ))
                append_assertion(member_manufacturer, member.id, "manufacturer", member_value["manufacturer"])
    return rows


def _reconstruct_data(rows: Iterable[ADV4CandidateAppDatum]) -> dict[str, Any]:
    def pointer_order(pointer: str) -> tuple[tuple[int, int | str], ...]:
        return tuple(
            (0, int(token)) if token.isdigit() else (1, token)
            for token in pointer.strip("/").split("/") if token
        )

    ordered = sorted(
        rows,
        key=lambda row: (row.json_pointer.count("/"), pointer_order(row.json_pointer)),
    )
    values: dict[str, Any] = {}
    for row in ordered:
        if row.value_kind == "object":
            value: Any = {}
        elif row.value_kind == "array":
            value = []
        elif row.value_kind == "boolean":
            value = row.boolean_value
        else:
            value = row.string_value
        values[row.json_pointer] = value
        if row.json_pointer == "":
            continue
        parent = values.get(row.parent_pointer or "")
        if parent is None:
            raise ADV4Error("projection_integrity", row.json_pointer, "Projection parent datum is missing", http_status=409)
        if isinstance(parent, list):
            if row.array_ordinal != len(parent):
                raise ADV4Error("projection_integrity", row.json_pointer, "Projection array ordinal is noncontiguous", http_status=409)
            parent.append(value)
        elif isinstance(parent, dict) and row.property_name is not None:
            parent[row.property_name] = value
        else:
            raise ADV4Error("projection_integrity", row.json_pointer, "Projection parent/container mismatch", http_status=409)
    root = values.get("")
    if not isinstance(root, dict):
        raise ADV4Error("projection_integrity", "", "Projection root is missing", http_status=409)
    return root


def reconstruct_applicability(db: Session, projection: ADV4CandidateAppProjection) -> dict[str, Any]:
    proposal = verified_candidate(db, projection.proposal_id)
    if proposal.validator_version != VALIDATOR_VERSION_V2 or proposal.canonicalization_version != CANONICALIZATION_VERSION_V2:
        raise ADV4Error("predecessor_semantic_defect", "", "Only validator-2 candidates can be projected", http_status=422)
    rows = db.scalars(select(ADV4CandidateAppDatum).where(ADV4CandidateAppDatum.projection_id == projection.id)).all()
    if len(rows) != projection.datum_count:
        raise ADV4Error("projection_integrity", "", "Projection datum count differs", http_status=409)
    reconstructed = _reconstruct_data(rows)
    expected = _app_subtree(proposal.parsed_json)
    payload = canonical_bytes(reconstructed, CANONICALIZATION_VERSION_V2)
    if (
        reconstructed != expected
        or payload != projection.applicability_subtree_bytes
        or hashlib.sha256(SUBTREE_DOMAIN + payload).hexdigest() != projection.applicability_subtree_hash
        or hashlib.sha256(PROJECTION_DOMAIN + projection.projection_canonical_bytes).hexdigest() != projection.projection_hash
    ):
        raise ADV4Error("projection_integrity", "", "Relational reconstruction differs from candidate", http_status=409)
    _verify_source_scope_owners(db, projection, proposal)
    _verify_condition_owners(db, projection, proposal)
    _verify_rule_owners(db, projection, proposal)
    _verify_search_hint_owners(db, projection, proposal)
    _verify_correction_foundation(db, projection, proposal)
    _verify_change_dependencies(db, projection, proposal)
    _verify_global_owner_graph(db, projection)
    typed = _typed_reconstruct_applicability(db, projection)
    typed_payload = canonical_bytes(typed, CANONICALIZATION_VERSION_V2)
    if (
        typed != reconstructed
        or typed != expected
        or typed_payload != projection.applicability_subtree_bytes
        or hashlib.sha256(SUBTREE_DOMAIN + typed_payload).hexdigest()
        != projection.applicability_subtree_hash
    ):
        raise ADV4Error(
            "projection_integrity", "",
            "Typed-owner reconstruction differs from relational/candidate subtree",
            http_status=409,
        )
    return typed


def _verify_global_owner_graph(
    db: Session,
    projection: ADV4CandidateAppProjection,
) -> None:
    """Prove the complete semantic-node/physical-owner partition on reads."""
    nodes = db.scalars(select(ADV4CandidateAppSemanticNode).where(
        ADV4CandidateAppSemanticNode.projection_id == projection.id,
    )).all()
    base_nodes = [
        node for node in nodes
        if not node.source_pointer.startswith("/incomingSupersessionSignals/")
    ]
    evidence = db.scalars(select(ADV4CandidateAppEvidenceLink).where(
        ADV4CandidateAppEvidenceLink.projection_id == projection.id,
    )).all()
    mappings = db.scalars(select(ADV4CandidateAppIdentityMapping).where(
        ADV4CandidateAppIdentityMapping.projection_id == projection.id,
    )).all()
    if (
        len(base_nodes) != projection.semantic_node_count
        or len(evidence) != projection.evidence_link_count
        or len(mappings) != projection.identity_mapping_count
    ):
        raise ADV4Error(
            "projection_integrity", "", "Projection graph count differs",
            http_status=409,
        )

    owner_models: tuple[tuple[type[Any], str], ...] = (
        (ADV4CandidateAppValueAssertion, "value_assertion"),
        (ADV4CandidateAppIdentityMapping, "identity_mapping"),
        (ADV4CandidateAppProductScope, "product_scope"),
        (ADV4CandidateAppDesignationScope, "designation_scope"),
        (ADV4CandidateAppDesignationValue, "designation_value"),
        (ADV4CandidateAppDesignationRange, "designation_range"),
        (ADV4CandidateAppCondition, "condition"),
        (ADV4CandidateAppDesignationGroup, "designation_group"),
        (ADV4CandidateAppDesignationGroupMember, "designation_group_member"),
        (ADV4CandidateAppRule, "applicability_rule"),
        (ADV4CandidateAppExpression, "expression"),
        (ADV4CandidateAppSearchHint, "search_hint"),
        (ADV4CandidateAppSearchHintGroup, "search_hint_group"),
        (ADV4CandidateAppSearchHintMember, "search_hint_model"),
        (ADV4CandidateAppChangeDependency, "change_dependency"),
    )
    owners: dict[str, list[str]] = {}
    for model, node_type in owner_models:
        rows = db.scalars(select(model).where(model.projection_id == projection.id)).all()
        for row in rows:
            owners.setdefault(row.semantic_node_id, []).append(node_type)
    nodes_by_id = {node.id: node for node in nodes}
    if len(nodes_by_id) != len(nodes) or set(owners) != set(nodes_by_id):
        raise ADV4Error(
            "projection_integrity", "", "Semantic owner set differs",
            http_status=409,
        )
    for node_id, node in nodes_by_id.items():
        if owners[node_id] != [node.node_type]:
            raise ADV4Error(
                "projection_integrity", "", "Semantic node does not have exactly one matching typed owner",
                http_status=409,
            )


def _typed_reconstruct_applicability(
    db: Session,
    projection: ADV4CandidateAppProjection,
) -> dict[str, Any]:
    """Rebuild the canonical four-field subtree from physical typed owners."""
    projection_id = projection.id
    nodes = db.scalars(select(ADV4CandidateAppSemanticNode).where(
        ADV4CandidateAppSemanticNode.projection_id == projection_id,
    )).all()
    node_by_id = {row.id: row for row in nodes}
    evidence_rows = db.scalars(select(ADV4CandidateAppEvidenceLink).where(
        ADV4CandidateAppEvidenceLink.projection_id == projection_id,
    ).order_by(
        ADV4CandidateAppEvidenceLink.semantic_node_id,
        ADV4CandidateAppEvidenceLink.canonical_ordinal,
    )).all()
    evidence_by_node: dict[str, list[str]] = {}
    for row in evidence_rows:
        evidence_by_node.setdefault(row.semantic_node_id, []).append(row.evidence_key)

    assertion_rows = db.scalars(select(ADV4CandidateAppValueAssertion).where(
        ADV4CandidateAppValueAssertion.projection_id == projection_id,
    )).all()
    assertion_by_id = {row.semantic_node_id: row for row in assertion_rows}
    assertions_by_parent = {
        (row.parent_semantic_node_id, row.field_code): row for row in assertion_rows
    }
    mapping_rows = db.scalars(select(ADV4CandidateAppIdentityMapping).where(
        ADV4CandidateAppIdentityMapping.projection_id == projection_id,
    )).all()
    mapping_by_node = {row.semantic_node_id: row for row in mapping_rows}

    def temporal(kind: str) -> dict[str, str]:
        return {"kind": kind}

    def assertion_value(assertion_id: str) -> dict[str, Any]:
        row = assertion_by_id[assertion_id]
        value: dict[str, Any] = {
            "state": row.state,
            "evidenceKeys": evidence_by_node.get(assertion_id, []),
        }
        if row.state == "known":
            value["value"] = row.text_value
        else:
            value["reason"] = row.reason
            value["temporalScope"] = temporal(row.temporal_scope)
        return value

    def normalized_identity(mapping_node_id: str, assertion_id: str) -> dict[str, Any]:
        row = mapping_by_node[mapping_node_id]
        value: dict[str, Any] = {
            "state": row.normalized_state,
            "evidenceKeys": evidence_by_node.get(assertion_id, []),
        }
        if row.normalized_state == "known":
            value["value"] = row.normalized_value
        else:
            value["reason"] = row.reason
            value["temporalScope"] = temporal(row.temporal_scope)
        return value

    designation_rows = db.scalars(select(ADV4CandidateAppDesignationScope).where(
        ADV4CandidateAppDesignationScope.projection_id == projection_id,
    )).all()
    designations_by_product = {
        (row.product_scope_node_id, row.field_kind): row for row in designation_rows
    }
    designation_values = db.scalars(select(ADV4CandidateAppDesignationValue).where(
        ADV4CandidateAppDesignationValue.projection_id == projection_id,
    ).order_by(
        ADV4CandidateAppDesignationValue.designation_scope_id,
        ADV4CandidateAppDesignationValue.canonical_ordinal,
    )).all()
    values_by_scope: dict[str, list[ADV4CandidateAppDesignationValue]] = {}
    for row in designation_values:
        values_by_scope.setdefault(row.designation_scope_id, []).append(row)
    designation_ranges = db.scalars(select(ADV4CandidateAppDesignationRange).where(
        ADV4CandidateAppDesignationRange.projection_id == projection_id,
    ).order_by(
        ADV4CandidateAppDesignationRange.designation_scope_id,
        ADV4CandidateAppDesignationRange.canonical_ordinal,
    )).all()
    ranges_by_scope: dict[str, list[ADV4CandidateAppDesignationRange]] = {}
    for row in designation_ranges:
        ranges_by_scope.setdefault(row.designation_scope_id, []).append(row)

    def designation_value(row: ADV4CandidateAppDesignationScope) -> dict[str, Any]:
        value: dict[str, Any] = {
            "kind": row.scope_kind,
            "evidenceKeys": evidence_by_node.get(row.semantic_node_id, []),
        }
        if row.scope_kind == "listed":
            value["sourceDesignations"] = [
                item.source_value for item in values_by_scope.get(row.semantic_node_id, [])
            ]
        elif row.scope_kind == "series_expression":
            value["expression"] = row.series_expression
        elif row.scope_kind == "ranges":
            value["ranges"] = [
                {
                    "lower": item.lower_value,
                    "upper": item.upper_value,
                    "lowerInclusive": item.lower_inclusive,
                    "upperInclusive": item.upper_inclusive,
                    "polarity": item.polarity,
                }
                for item in ranges_by_scope.get(row.semantic_node_id, [])
            ]
        elif row.scope_kind in {"unknown", "not_applicable"}:
            value["reason"] = row.reason
            value["temporalScope"] = temporal(row.temporal_scope)
        return value

    product_rows = db.scalars(select(ADV4CandidateAppProductScope).where(
        ADV4CandidateAppProductScope.projection_id == projection_id,
    )).all()
    product_rows.sort(key=lambda row: node_by_id[row.semantic_node_id].canonical_ordinal)
    products: list[dict[str, Any]] = []
    for row in product_rows:
        value: dict[str, Any] = {
            "scopeKey": row.scope_key,
            "productRole": row.product_role,
            "evidenceKeys": evidence_by_node.get(row.semantic_node_id, []),
        }
        if row.manufacturer_presence == "present":
            assertion = assertions_by_parent[(row.semantic_node_id, "manufacturer")]
            value["manufacturer"] = {
                "sourceValue": row.manufacturer_source_value,
                "normalizedIdentity": normalized_identity(
                    row.manufacturer_identity_mapping_node_id,
                    assertion.semantic_node_id,
                ),
            }
        for field_kind, canonical_key, presence in (
            ("model", "modelScope", row.model_presence),
            ("serial", "serialScope", row.serial_presence),
            ("part_number", "partNumberScope", row.part_number_presence),
        ):
            if presence == "present":
                value[canonical_key] = designation_value(
                    designations_by_product[(row.semantic_node_id, field_kind)]
                )
        products.append(value)

    group_rows = db.scalars(select(ADV4CandidateAppDesignationGroup).where(
        ADV4CandidateAppDesignationGroup.projection_id == projection_id,
    )).all()
    group_by_condition = {row.condition_node_id: row for row in group_rows}
    condition_members = db.scalars(select(ADV4CandidateAppDesignationGroupMember).where(
        ADV4CandidateAppDesignationGroupMember.projection_id == projection_id,
    ).order_by(
        ADV4CandidateAppDesignationGroupMember.group_node_id,
        ADV4CandidateAppDesignationGroupMember.canonical_ordinal,
    )).all()
    condition_members_by_group: dict[str, list[ADV4CandidateAppDesignationGroupMember]] = {}
    for row in condition_members:
        condition_members_by_group.setdefault(row.group_node_id, []).append(row)

    def group_member_value(row: ADV4CandidateAppDesignationGroupMember) -> dict[str, Any]:
        value: dict[str, Any] = {
            "memberKey": row.member_key,
            "designationKind": row.designation_kind,
            "manufacturer": assertion_value(row.manufacturer_assertion_node_id),
            "evidenceKeys": evidence_by_node.get(row.semantic_node_id, []),
        }
        if row.designation_kind == "model":
            value["sourceDesignation"] = row.source_designation
        else:
            value.update({
                "expressionText": row.expression_text,
                "evaluationState": "unknown",
                "reason": row.evaluation_reason,
            })
        return value

    condition_rows = db.scalars(select(ADV4CandidateAppCondition).where(
        ADV4CandidateAppCondition.projection_id == projection_id,
    )).all()
    condition_rows.sort(key=lambda row: node_by_id[row.semantic_node_id].canonical_ordinal)
    canonical_field_by_code = {
        "manufacturer": "manufacturer",
        "model_or_series": "modelOrSeries",
        "part_number": "partNumber",
        "serial_number": "serialNumber",
        "stc_number": "stcNumber",
        "attribute_value": "attributeValue",
    }
    conditions: list[dict[str, Any]] = []
    for row in condition_rows:
        subject: dict[str, Any] = {}
        if row.subject_product_role_presence == "present":
            subject["productRole"] = row.subject_product_role
        if row.subject_attribute_key_presence == "present":
            subject["attributeKey"] = row.subject_attribute_key
        for (parent_id, field_code), assertion in assertions_by_parent.items():
            if parent_id == row.semantic_node_id and field_code in canonical_field_by_code:
                subject[canonical_field_by_code[field_code]] = assertion_value(
                    assertion.semantic_node_id
                )
        if row.designation_group_presence == "present":
            group = group_by_condition[row.semantic_node_id]
            group_value: dict[str, Any] = {
                "groupKey": group.group_key,
                "sourceDisplayText": assertion_value(group.source_display_assertion_node_id),
                "association": group.association,
                "members": [
                    group_member_value(member)
                    for member in condition_members_by_group.get(group.semantic_node_id, [])
                ],
                "evidenceKeys": evidence_by_node.get(group.semantic_node_id, []),
            }
            if group.association == "unknown":
                group_value["reason"] = group.reason
                group_value["temporalScope"] = temporal(group.temporal_scope)
            subject["designationGroup"] = group_value
        value = {
            "conditionKey": row.condition_key,
            "conditionType": row.condition_type,
            "operator": row.operator,
            "subject": subject,
            "temporalBasis": temporal(row.temporal_basis),
            "evidenceKeys": evidence_by_node.get(row.semantic_node_id, []),
        }
        if row.comparator_presence == "present":
            value["comparatorVersion"] = row.comparator_version
        conditions.append(value)

    expression_rows = db.scalars(select(ADV4CandidateAppExpression).where(
        ADV4CandidateAppExpression.projection_id == projection_id,
    )).all()
    expression_by_id = {row.semantic_node_id: row for row in expression_rows}
    edge_rows = db.scalars(select(ADV4CandidateAppExpressionEdge).where(
        ADV4CandidateAppExpressionEdge.projection_id == projection_id,
    ).order_by(
        ADV4CandidateAppExpressionEdge.parent_expression_id,
        ADV4CandidateAppExpressionEdge.sequence,
    )).all()
    children_by_parent: dict[str, list[str]] = {}
    for row in edge_rows:
        children_by_parent.setdefault(row.parent_expression_id, []).append(
            row.child_expression_id
        )

    def expression_value(node_id: str, active: frozenset[str] = frozenset()) -> dict[str, Any]:
        if node_id in active:
            raise ADV4Error("projection_integrity", "", "Typed expression cycle", http_status=409)
        row = expression_by_id[node_id]
        value: dict[str, Any] = {"nodeType": row.expression_node_type}
        if row.expression_node_type == "scope_ref":
            value["scopeKey"] = node_by_id[row.scope_node_id].node_key
        elif row.expression_node_type == "predicate_ref":
            value["conditionKey"] = node_by_id[row.condition_node_id].node_key
        elif row.expression_node_type == "rule_ref":
            value["ruleKey"] = node_by_id[row.referenced_rule_node_id].node_key
        elif row.expression_node_type == "not":
            value["operand"] = expression_value(
                children_by_parent[node_id][0], active | {node_id}
            )
        else:
            value["operands"] = [
                expression_value(child_id, active | {node_id})
                for child_id in children_by_parent.get(node_id, [])
            ]
        return value

    exclusion_rows = db.scalars(select(ADV4CandidateAppRuleExclusion).where(
        ADV4CandidateAppRuleExclusion.projection_id == projection_id,
    ).order_by(
        ADV4CandidateAppRuleExclusion.rule_node_id,
        ADV4CandidateAppRuleExclusion.canonical_ordinal,
    )).all()
    exclusions_by_rule: dict[str, list[str]] = {}
    for row in exclusion_rows:
        exclusions_by_rule.setdefault(row.rule_node_id, []).append(
            node_by_id[row.excluded_rule_node_id].node_key
        )
    rule_rows = db.scalars(select(ADV4CandidateAppRule).where(
        ADV4CandidateAppRule.projection_id == projection_id,
    )).all()
    rule_rows.sort(key=lambda row: node_by_id[row.semantic_node_id].canonical_ordinal)
    rules: list[dict[str, Any]] = []
    for row in rule_rows:
        value = {
            "ruleKey": row.rule_key,
            "scopeExpression": expression_value(row.scope_expression_node_id),
            "exclusionRuleKeys": exclusions_by_rule.get(row.semantic_node_id, []),
            "evidenceKeys": evidence_by_node.get(row.semantic_node_id, []),
        }
        if row.condition_presence == "present":
            value["conditionExpression"] = expression_value(
                row.condition_expression_node_id
            )
        rules.append(value)

    search_group_rows = db.scalars(select(ADV4CandidateAppSearchHintGroup).where(
        ADV4CandidateAppSearchHintGroup.projection_id == projection_id,
    ).order_by(
        ADV4CandidateAppSearchHintGroup.hint_node_id,
        ADV4CandidateAppSearchHintGroup.canonical_ordinal,
    )).all()
    search_groups_by_hint: dict[str, list[ADV4CandidateAppSearchHintGroup]] = {}
    for row in search_group_rows:
        search_groups_by_hint.setdefault(row.hint_node_id, []).append(row)
    search_member_rows = db.scalars(select(ADV4CandidateAppSearchHintMember).where(
        ADV4CandidateAppSearchHintMember.projection_id == projection_id,
    ).order_by(
        ADV4CandidateAppSearchHintMember.group_node_id,
        ADV4CandidateAppSearchHintMember.canonical_ordinal,
    )).all()
    search_members_by_group: dict[str, list[ADV4CandidateAppSearchHintMember]] = {}
    for row in search_member_rows:
        search_members_by_group.setdefault(row.group_node_id, []).append(row)

    def search_member_value(row: ADV4CandidateAppSearchHintMember) -> dict[str, Any]:
        value: dict[str, Any] = {
            "memberKey": row.member_key,
            "designationKind": row.designation_kind,
            "manufacturer": assertion_value(row.manufacturer_assertion_node_id),
            "evidenceKeys": evidence_by_node.get(row.semantic_node_id, []),
        }
        if row.designation_kind == "model":
            value["sourceDesignation"] = row.source_designation
        else:
            value.update({
                "expressionText": row.expression_text,
                "evaluationState": "unknown",
                "reason": row.evaluation_reason,
            })
        return value

    hint_rows = db.scalars(select(ADV4CandidateAppSearchHint).where(
        ADV4CandidateAppSearchHint.projection_id == projection_id,
    )).all()
    hint_rows.sort(key=lambda row: node_by_id[row.semantic_node_id].canonical_ordinal)
    hints: list[dict[str, Any]] = []
    for row in hint_rows:
        groups: list[dict[str, Any]] = []
        for group in search_groups_by_hint.get(row.semantic_node_id, []):
            group_value: dict[str, Any] = {
                "groupKey": group.group_key,
                "manufacturer": assertion_value(group.manufacturer_assertion_node_id),
                "association": group.association,
                "members": [
                    search_member_value(member)
                    for member in search_members_by_group.get(group.semantic_node_id, [])
                ],
                "evidenceKeys": evidence_by_node.get(group.semantic_node_id, []),
            }
            if group.association == "unknown":
                group_value["reason"] = group.reason
                group_value["temporalScope"] = temporal(group.temporal_scope)
            groups.append(group_value)
        hints.append({
            "hintKey": row.hint_key,
            "productRole": row.product_role,
            "sourceDisplayText": assertion_value(row.source_display_assertion_node_id),
            "manufacturerModelGroups": groups,
            "controlling": row.controlling,
            "exhaustive": row.exhaustive,
            "evidenceKeys": evidence_by_node.get(row.semantic_node_id, []),
        })

    return {
        "productScopes": products,
        "conditionDefinitions": conditions,
        "applicabilityRules": rules,
        "applicabilitySearchHints": hints,
    }


class _TypedGraphVerifier:
    def __init__(
        self,
        db: Session,
        projection: ADV4CandidateAppProjection,
        candidate: ADV4CandidateProposal,
    ) -> None:
        self.db = db
        self.projection = projection
        self.candidate = candidate
        self.nodes = db.scalars(select(ADV4CandidateAppSemanticNode).where(
            ADV4CandidateAppSemanticNode.projection_id == projection.id
        )).all()
        self.node_by_id = {node.id: node for node in self.nodes}

    def node(
        self,
        node: ADV4CandidateAppSemanticNode | None,
        *,
        node_type: str,
        node_key: str,
        pointer: str,
        value: Any,
        parent_id: str | None,
        ordinal: int,
        identity_table: str = "semantic-node",
        identity_value: dict[str, Any] | None = None,
    ) -> None:
        identity = identity_value or {
            "projectionId": self.projection.id, "nodeType": node_type,
            "nodeKey": node_key, "pointer": pointer,
        }
        expected_id, expected_identity = _row_id("avn", identity_table, identity)
        if (
            node is None or node.id != expected_id or node.identity_hash != expected_identity
            or node.projection_id != self.projection.id
            or node.proposal_id != self.candidate.id
            or node.parent_node_id != parent_id or node.node_type != node_type
            or node.node_key != node_key or node.source_pointer != pointer
            or node.canonical_node_hash != hashlib.sha256(
                canonical_bytes(value, CANONICALIZATION_VERSION_V2)
            ).hexdigest()
            or node.canonical_ordinal != ordinal
        ):
            raise ADV4Error("projection_integrity", "", "Typed semantic node differs", http_status=409)

    def evidence(self, node_id: str, expected_keys: list[str], purpose: str) -> None:
        links = self.db.scalars(select(ADV4CandidateAppEvidenceLink).where(
            ADV4CandidateAppEvidenceLink.semantic_node_id == node_id,
        ).order_by(ADV4CandidateAppEvidenceLink.canonical_ordinal)).all()
        if [link.evidence_key for link in links] != expected_keys or any(
            link.purpose != purpose for link in links
        ):
            raise ADV4Error("projection_integrity", "", "Typed owner evidence set differs", http_status=409)
        for ordinal, link in enumerate(links):
            binding = self.db.get(ADV4CandidateEvidenceBinding, link.candidate_binding_id)
            expected_id, expected_hash = _row_id("avl", "evidence-link", {
                "projectionId": self.projection.id, "nodeId": node_id,
                "purpose": purpose, "evidenceKey": link.evidence_key,
            })
            if (
                link.id != expected_id or link.link_hash != expected_hash
                or link.canonical_ordinal != ordinal
                or link.projection_id != self.projection.id
                or link.proposal_id != self.candidate.id
                or binding is None or binding.proposal_id != self.candidate.id
                or binding.evidence_key != link.evidence_key
            ):
                raise ADV4Error("projection_integrity", "", "Typed owner evidence link differs", http_status=409)

    def mapping(
        self,
        mapping_node_id: str | None,
        occurrence_id: str,
        evidence_parent_id: str,
        identity_kind: str,
        source_value: str,
        *,
        origin: str,
        normalized_state: str,
        normalized_value: str | None,
        reason: str | None,
        temporal_scope: str | None,
        namespace: str | None,
        version: str | None,
    ) -> None:
        mapping = self.db.scalar(select(ADV4CandidateAppIdentityMapping).where(
            ADV4CandidateAppIdentityMapping.semantic_node_id == mapping_node_id
        )) if mapping_node_id else None
        mapping_node = self.node_by_id.get(mapping_node_id or "")
        occurrence_node = self.node_by_id.get(occurrence_id)
        expected_id, expected_hash = _row_id("avi", "identity-mapping", {
            "projectionId": self.projection.id, "kind": identity_kind,
            "occurrence": occurrence_id,
        })
        expected_node_id, expected_node_hash = _row_id("avn", "semantic-node", {
            "projectionId": self.projection.id, "nodeType": "identity_mapping",
            "nodeKey": occurrence_id,
            "pointer": occurrence_node.source_pointer if occurrence_node else "",
        })
        if (
            mapping is None or mapping_node is None or occurrence_node is None
            or mapping_node.node_type != "identity_mapping"
            or mapping_node.parent_node_id != occurrence_id
            or mapping_node.id != expected_node_id
            or mapping_node.identity_hash != expected_node_hash
            or mapping_node.node_key != occurrence_id
            or mapping_node.source_pointer != occurrence_node.source_pointer
            or mapping_node.canonical_node_hash != occurrence_node.canonical_node_hash
            or mapping_node.canonical_ordinal != occurrence_node.canonical_ordinal
            or mapping.projection_id != self.projection.id
            or mapping.proposal_id != self.candidate.id
            or mapping.source_occurrence_node_id != occurrence_id
            or mapping.evidence_parent_node_id != evidence_parent_id
            or mapping.identity_kind != identity_kind or mapping.source_value != source_value
            or mapping.normalization_origin != origin
            or mapping.normalized_state != normalized_state
            or mapping.normalized_value != normalized_value or mapping.reason != reason
            or mapping.temporal_scope != temporal_scope
            or mapping.normalization_namespace != namespace
            or mapping.normalization_version != version
            or mapping.review_state != "unreviewed_candidate"
            or mapping.id != expected_id or mapping.identity_hash != expected_hash
        ):
            raise ADV4Error("projection_integrity", "", "Typed identity mapping differs", http_status=409)
        if self.db.scalar(select(func.count()).select_from(ADV4CandidateAppEvidenceLink).where(
            ADV4CandidateAppEvidenceLink.semantic_node_id == mapping_node_id
        )) != 0:
            raise ADV4Error("projection_integrity", "", "Identity mapping duplicates inherited evidence", http_status=409)


def _verify_source_scope_owners(
    db: Session,
    projection: ADV4CandidateAppProjection,
    candidate: ADV4CandidateProposal,
) -> None:
    verifier = _TypedGraphVerifier(db, projection, candidate)
    node_by_id = verifier.node_by_id
    verify_node = verifier.node
    verify_evidence = verifier.evidence
    verify_mapping = verifier.mapping
    products = db.scalars(select(ADV4CandidateAppProductScope).where(
        ADV4CandidateAppProductScope.projection_id == projection.id
    )).all()
    product_by_key = {row.scope_key: row for row in products}
    canonical_products = candidate.parsed_json["productScopes"]
    if len(products) != len(canonical_products):
        raise ADV4Error("projection_integrity", "", "Product-scope owner count differs", http_status=409)
    expected_designations: dict[str, tuple[dict[str, Any], str, str]] = {}
    expected_assertions = 0
    for value in canonical_products:
        row = product_by_key.get(value["scopeKey"])
        node = node_by_id.get(row.semantic_node_id) if row else None
        manufacturer = value.get("manufacturer")
        if (
            row is None or node is None or node.node_type != "product_scope"
            or row.projection_id != projection.id or row.proposal_id != candidate.id
            or row.product_role != value["productRole"]
            or row.manufacturer_presence != ("present" if manufacturer else "property_absent")
            or row.manufacturer_source_value != (manufacturer or {}).get("sourceValue")
            or row.model_presence != ("present" if "modelScope" in value else "property_absent")
            or row.serial_presence != ("present" if "serialScope" in value else "property_absent")
            or row.part_number_presence != ("present" if "partNumberScope" in value else "property_absent")
        ):
            raise ADV4Error("projection_integrity", "", "Product-scope owner differs", http_status=409)
        product_ordinal = int(node.source_pointer.rsplit("/", 1)[-1])
        verify_node(
            node, node_type="product_scope", node_key=value["scopeKey"],
            pointer=node.source_pointer, value=value, parent_id=None,
            ordinal=product_ordinal,
        )
        verify_evidence(row.semantic_node_id, value["evidenceKeys"], "scope_clause")
        if manufacturer:
            expected_assertions += 1
            assertion = db.scalar(select(ADV4CandidateAppValueAssertion).where(
                ADV4CandidateAppValueAssertion.parent_semantic_node_id == row.semantic_node_id,
                ADV4CandidateAppValueAssertion.field_code == "manufacturer",
            ))
            normalized = manufacturer["normalizedIdentity"]
            if (
                assertion is None
                or node_by_id.get(assertion.semantic_node_id) is None
                or node_by_id[assertion.semantic_node_id].node_type != "value_assertion"
                or node_by_id[assertion.semantic_node_id].source_pointer != f"{node.source_pointer}/manufacturer/sourceValue"
                or node_by_id[assertion.semantic_node_id].parent_node_id != row.semantic_node_id
                or assertion.parent_semantic_node_id != row.semantic_node_id
                or assertion.state != "known" or assertion.value_type != "text"
                or assertion.text_value != manufacturer["sourceValue"]
                or assertion.reason is not None or assertion.temporal_scope is not None
            ):
                raise ADV4Error("projection_integrity", "", "Manufacturer assertion/mapping differs", http_status=409)
            assertion_node = node_by_id[assertion.semantic_node_id]
            verify_node(
                assertion_node, node_type="value_assertion",
                node_key=assertion_node.source_pointer,
                pointer=f"{node.source_pointer}/manufacturer/sourceValue",
                value=manufacturer["sourceValue"], parent_id=row.semantic_node_id,
                ordinal=0,
            )
            verify_evidence(
                assertion.semantic_node_id, normalized["evidenceKeys"], "identity_support",
            )
            known = normalized["state"] == "known"
            verify_mapping(
                row.manufacturer_identity_mapping_node_id,
                assertion.semantic_node_id, row.semantic_node_id,
                "manufacturer", manufacturer["sourceValue"],
                origin="candidate_payload",
                normalized_state=normalized["state"],
                normalized_value=normalized.get("value"),
                reason=normalized.get("reason"),
                temporal_scope=normalized.get("temporalScope", {}).get("kind"),
                namespace="candidate" if known else None,
                version="1" if known else None,
            )
        for field_name, field_kind in (
            ("modelScope", "model"), ("serialScope", "serial"),
            ("partNumberScope", "part_number"),
        ):
            if field_name in value:
                expected_designations[f"{node.source_pointer}/{field_name}"] = (
                    value[field_name], field_kind, row.semantic_node_id,
                )
    product_node_ids = {row.semantic_node_id for row in products}
    assertions = db.scalars(select(ADV4CandidateAppValueAssertion).where(
        ADV4CandidateAppValueAssertion.projection_id == projection.id,
        ADV4CandidateAppValueAssertion.parent_semantic_node_id.in_(product_node_ids),
    )).all() if product_node_ids else []
    if len(assertions) != expected_assertions:
        raise ADV4Error("projection_integrity", "", "Source assertion owner count differs", http_status=409)
    scopes = db.scalars(select(ADV4CandidateAppDesignationScope).where(
        ADV4CandidateAppDesignationScope.projection_id == projection.id
    )).all()
    if len(scopes) != len(expected_designations):
        raise ADV4Error("projection_integrity", "", "Designation-scope owner count differs", http_status=409)
    for scope in scopes:
        node = node_by_id.get(scope.semantic_node_id)
        expected = expected_designations.get(node.source_pointer if node else "")
        if expected is None:
            raise ADV4Error("projection_integrity", "", "Designation-scope owner is unexpected", http_status=409)
        value, field_kind, product_node_id = expected
        if (
            scope.projection_id != projection.id or scope.proposal_id != candidate.id
            or
            scope.product_scope_node_id != product_node_id or scope.field_kind != field_kind
            or scope.scope_kind != value["kind"] or scope.series_expression != value.get("expression")
            or scope.reason != value.get("reason")
            or scope.temporal_scope != value.get("temporalScope", {}).get("kind")
            or scope.evaluation_state != ("unknown" if value["kind"] == "series_expression" else "unevaluated")
            or scope.evaluator_contract != ("unsupported_expression" if value["kind"] == "series_expression" else "none")
        ):
            raise ADV4Error("projection_integrity", "", "Designation-scope owner differs", http_status=409)
        verify_node(
            node, node_type="designation_scope", node_key=node.source_pointer,
            pointer=node.source_pointer, value=value, parent_id=product_node_id,
            ordinal=0,
        )
        verify_evidence(scope.semantic_node_id, value["evidenceKeys"], "designation_scope")
        values = db.scalars(select(ADV4CandidateAppDesignationValue).where(
            ADV4CandidateAppDesignationValue.designation_scope_id == scope.semantic_node_id
        ).order_by(ADV4CandidateAppDesignationValue.canonical_ordinal)).all()
        ranges = db.scalars(select(ADV4CandidateAppDesignationRange).where(
            ADV4CandidateAppDesignationRange.designation_scope_id == scope.semantic_node_id
        ).order_by(ADV4CandidateAppDesignationRange.canonical_ordinal)).all()
        if [item.source_value for item in values] != value.get("sourceDesignations", []):
            raise ADV4Error("projection_integrity", "", "Designation values differ", http_status=409)
        for item in values:
            item_node = node_by_id.get(item.semantic_node_id)
            expected_pointer = f"{node.source_pointer}/sourceDesignations/{item.canonical_ordinal}"
            if (
                item.projection_id != projection.id or item.proposal_id != candidate.id
                or item.designation_scope_id != scope.semantic_node_id
            ):
                raise ADV4Error("projection_integrity", "", "Designation value semantic owner differs", http_status=409)
            verify_node(
                item_node, node_type="designation_value",
                node_key=f"{node.node_key}:{item.canonical_ordinal}",
                pointer=expected_pointer, value=item.source_value,
                parent_id=scope.semantic_node_id, ordinal=item.canonical_ordinal,
                identity_table="designation-value",
                identity_value={
                    "projectionId": projection.id, "pointer": expected_pointer,
                    "value": item.source_value,
                },
            )
            if field_kind == "model":
                verify_mapping(
                    item.identity_mapping_node_id, item.semantic_node_id,
                    scope.semantic_node_id, "model", item.source_value,
                    origin="no_normalized_identity", normalized_state="unknown",
                    normalized_value=None, reason="not_extracted",
                    temporal_scope="directive_version", namespace=None, version=None,
                )
            elif item.identity_mapping_node_id is not None:
                raise ADV4Error("projection_integrity", "", "Non-model designation has an identity mapping", http_status=409)
        expected_ranges = value.get("ranges", [])
        if len(ranges) != len(expected_ranges) or any(
            (row.canonical_ordinal, row.lower_value, row.upper_value, row.lower_inclusive, row.upper_inclusive, row.polarity, row.comparator_version)
            != (ordinal, item["lower"], item["upper"], item["lowerInclusive"], item["upperInclusive"], item["polarity"], "lexical_source_only_v1")
            for ordinal, (row, item) in enumerate(zip(ranges, expected_ranges, strict=True))
        ):
            raise ADV4Error("projection_integrity", "", "Designation ranges differ", http_status=409)
        for ordinal, (row, expected_range) in enumerate(zip(ranges, expected_ranges, strict=True)):
            range_node = node_by_id.get(row.semantic_node_id)
            if (
                row.projection_id != projection.id or row.proposal_id != candidate.id
                or row.designation_scope_id != scope.semantic_node_id
            ):
                raise ADV4Error("projection_integrity", "", "Designation range semantic owner differs", http_status=409)
            pointer = f"{node.source_pointer}/ranges/{ordinal}"
            verify_node(
                range_node, node_type="designation_range", node_key=pointer,
                pointer=pointer, value=expected_range,
                parent_id=scope.semantic_node_id, ordinal=ordinal,
            )


def _document_identity(document: dict[str, Any]) -> str:
    return _hash(ROW_DOMAIN, {"officialDocument": document})


def _verify_change_dependencies(
    db: Session,
    projection: ADV4CandidateAppProjection,
    candidate: ADV4CandidateProposal,
) -> None:
    """Verify immutable outgoing facts and target-local incoming causes."""
    dependencies = db.scalars(
        select(ADV4CandidateAppChangeDependency)
        .where(ADV4CandidateAppChangeDependency.projection_id == projection.id)
        .order_by(ADV4CandidateAppChangeDependency.dependency_key)
    ).all()
    outgoing = [row for row in dependencies if row.dependency_kind != "incoming_supersession_signal"]
    relations = candidate.parsed_json["supersessionRelations"]
    if len(outgoing) != len(relations):
        raise ADV4Error("projection_integrity", "", "Supersession dependency count differs", http_status=409)
    canonical_ad = candidate.parsed_json["directiveIdentity"]["adNumber"]
    by_key = {row.dependency_key: row for row in outgoing}
    for relation in relations:
        key = f"{relation['relationType']}:{relation['predecessorAdNumber']}"
        row = by_key.get(key)
        node = db.get(ADV4CandidateAppSemanticNode, row.semantic_node_id) if row else None
        if (
            row is None
            or row.proposal_id != candidate.id
            or row.dependency_kind != (
                "outgoing_supersedes" if relation["relationType"] == "supersedes"
                else "outgoing_partially_supersedes"
            )
            or row.predecessor_ad_number != relation["predecessorAdNumber"]
            or row.successor_ad_number != relation["successorAdNumber"]
            or row.source_dependency_id is not None
            or node is None
            or node.projection_id != projection.id
            or node.node_type != "change_dependency"
            or node.node_key != key
        ):
            raise ADV4Error("projection_integrity", "", "Outgoing supersession dependency differs", http_status=409)
        successor_matches = (
            canonical_ad.get("state") == "known"
            and relation["successorAdNumber"] == canonical_ad.get("value")
        )
        if not successor_matches and (
            row.resolution_state != "unresolved"
            or row.target_projection_id is not None
            or row.unresolved_reason not in {"successor_identity_unknown", "successor_not_this_proposal"}
        ):
            raise ADV4Error("projection_integrity", "", "Mismatched successor was resolved", http_status=409)
        if row.resolution_state == "resolved_candidate":
            incoming = db.scalar(select(ADV4CandidateAppChangeDependency).where(
                ADV4CandidateAppChangeDependency.source_dependency_id == row.id,
                ADV4CandidateAppChangeDependency.dependency_kind == "incoming_supersession_signal",
            ))
            if (
                not successor_matches
                or row.target_projection_id is None
                or row.unresolved_reason is not None
                or incoming is None
                or incoming.projection_id != row.target_projection_id
                or incoming.target_projection_id != row.target_projection_id
                or incoming.proposal_id == row.proposal_id
                or incoming.resolution_state != "resolved_candidate"
                or incoming.unresolved_reason is not None
                or incoming.predecessor_ad_number != row.predecessor_ad_number
                or incoming.successor_ad_number != row.successor_ad_number
            ):
                raise ADV4Error("projection_integrity", "", "Resolved supersession dependency is incomplete", http_status=409)
        elif row.target_projection_id is not None:
            raise ADV4Error("projection_integrity", "", "Unresolved supersession has a target", http_status=409)

    for incoming in (row for row in dependencies if row.dependency_kind == "incoming_supersession_signal"):
        source = db.get(ADV4CandidateAppChangeDependency, incoming.source_dependency_id)
        node = db.get(ADV4CandidateAppSemanticNode, incoming.semantic_node_id)
        if (
            source is None
            or source.dependency_kind not in {"outgoing_supersedes", "outgoing_partially_supersedes"}
            or source.resolution_state != "resolved_candidate"
            or source.target_projection_id != projection.id
            or incoming.target_projection_id != projection.id
            or incoming.proposal_id != projection.proposal_id
            or incoming.resolution_state != "resolved_candidate"
            or incoming.unresolved_reason is not None
            or node is None
            or node.projection_id != projection.id
            or node.node_type != "change_dependency"
            or node.node_key != f"incoming:{source.id}"
        ):
            raise ADV4Error("projection_integrity", "", "Incoming supersession dependency differs", http_status=409)


def _verify_condition_owners(
    db: Session,
    projection: ADV4CandidateAppProjection,
    candidate: ADV4CandidateProposal,
) -> None:
    verifier = _TypedGraphVerifier(db, projection, candidate)
    node_by_id = verifier.node_by_id
    nodes_by_pointer_type = {
        (node.source_pointer, node.node_type): node for node in verifier.nodes
    }
    mappings = db.scalars(select(ADV4CandidateAppIdentityMapping).where(
        ADV4CandidateAppIdentityMapping.projection_id == projection.id
    )).all()
    mapping_by_occurrence = {row.source_occurrence_node_id: row for row in mappings}
    conditions = db.scalars(select(ADV4CandidateAppCondition).where(
        ADV4CandidateAppCondition.projection_id == projection.id
    )).all()
    condition_by_key = {row.condition_key: row for row in conditions}
    groups = db.scalars(select(ADV4CandidateAppDesignationGroup).where(
        ADV4CandidateAppDesignationGroup.projection_id == projection.id
    )).all()
    group_by_condition = {row.condition_node_id: row for row in groups}
    members = db.scalars(select(ADV4CandidateAppDesignationGroupMember).where(
        ADV4CandidateAppDesignationGroupMember.projection_id == projection.id
    )).all()
    members_by_group: dict[str, list[ADV4CandidateAppDesignationGroupMember]] = {}
    for member in members:
        members_by_group.setdefault(member.group_node_id, []).append(member)
    for group_members in members_by_group.values():
        group_members.sort(key=lambda row: row.canonical_ordinal)

    expected_assertion_ids: set[str] = set()
    expected_mapping_occurrences: set[str] = set()
    expected_mapping_node_ids: set[str] = set()
    expected_group_ids: set[str] = set()
    expected_member_ids: set[str] = set()
    field_codes = {
        "manufacturer": "manufacturer",
        "modelOrSeries": "model_or_series",
        "partNumber": "part_number",
        "serialNumber": "serial_number",
        "stcNumber": "stc_number",
        "attributeValue": "attribute_value",
    }

    def verify_assertion(
        pointer: str,
        parent_id: str,
        field_code: str,
        value: dict[str, Any],
        purpose: str,
    ) -> ADV4CandidateAppSemanticNode:
        node = nodes_by_pointer_type.get((pointer, "value_assertion"))
        assertion = db.get(ADV4CandidateAppValueAssertion, node.id) if node else None
        if (
            node is None or assertion is None
            or assertion.projection_id != projection.id
            or assertion.proposal_id != candidate.id
            or assertion.parent_semantic_node_id != parent_id
            or assertion.field_code != field_code or assertion.state != value["state"]
            or assertion.value_type != "text"
            or assertion.text_value != value.get("value")
            or assertion.reason != value.get("reason")
            or assertion.temporal_scope != value.get("temporalScope", {}).get("kind")
        ):
            raise ADV4Error("projection_integrity", "", "Condition value assertion differs", http_status=409)
        verifier.node(
            node, node_type="value_assertion", node_key=pointer,
            pointer=pointer, value=value, parent_id=parent_id, ordinal=0,
        )
        verifier.evidence(node.id, value["evidenceKeys"], purpose)
        expected_assertion_ids.add(node.id)
        return node

    canonical_conditions = candidate.parsed_json["conditionDefinitions"]
    if len(conditions) != len(canonical_conditions):
        raise ADV4Error("projection_integrity", "", "Condition owner count differs", http_status=409)
    for ordinal, value in enumerate(canonical_conditions):
        pointer = f"/conditionDefinitions/{ordinal}"
        row = condition_by_key.get(value["conditionKey"])
        node = node_by_id.get(row.semantic_node_id) if row else None
        subject = value["subject"]
        group_value = subject.get("designationGroup")
        group = group_by_condition.get(row.semantic_node_id) if row else None
        if (
            row is None or node is None
            or row.projection_id != projection.id or row.proposal_id != candidate.id
            or row.condition_type != value["conditionType"]
            or row.operator != value["operator"]
            or row.temporal_basis != value["temporalBasis"]["kind"]
            or row.comparator_presence != ("present" if "comparatorVersion" in value else "property_absent")
            or row.comparator_version != value.get("comparatorVersion")
            or row.subject_product_role_presence != ("present" if "productRole" in subject else "property_absent")
            or row.subject_product_role != subject.get("productRole")
            or row.subject_attribute_key_presence != ("present" if "attributeKey" in subject else "property_absent")
            or row.subject_attribute_key != subject.get("attributeKey")
            or row.designation_group_presence != ("present" if group_value is not None else "property_absent")
            or row.designation_group_node_id != (group.semantic_node_id if group else None)
            or row.evaluation_state != "unevaluated" or row.evaluator_contract != "none"
        ):
            raise ADV4Error("projection_integrity", "", "Condition owner differs", http_status=409)
        verifier.node(
            node, node_type="condition", node_key=value["conditionKey"],
            pointer=pointer, value=value, parent_id=None, ordinal=ordinal,
        )
        verifier.evidence(node.id, value["evidenceKeys"], "condition_clause")

        for canonical_field, field_code in field_codes.items():
            assertion_value = subject.get(canonical_field)
            assertion_pointer = f"{pointer}/subject/{canonical_field}"
            assertion_node = nodes_by_pointer_type.get((assertion_pointer, "value_assertion"))
            if assertion_value is None:
                if assertion_node is not None:
                    raise ADV4Error("projection_integrity", "", "Unexpected condition assertion", http_status=409)
                continue
            assertion_node = verify_assertion(
                assertion_pointer, node.id, field_code, assertion_value,
                "subject_value",
            )
            mapping = mapping_by_occurrence.get(assertion_node.id)
            identity_kind = {
                "manufacturer": "manufacturer",
                "modelOrSeries": "model_or_series",
            }.get(canonical_field)
            if identity_kind is not None and assertion_value["state"] == "known":
                if mapping is None:
                    raise ADV4Error("projection_integrity", "", "Condition identity mapping is missing", http_status=409)
                verifier.mapping(
                    mapping.semantic_node_id, assertion_node.id, node.id,
                    identity_kind, assertion_value["value"],
                    origin="source_only", normalized_state="unknown",
                    normalized_value=None, reason="not_extracted",
                    temporal_scope="directive_version", namespace=None, version=None,
                )
                expected_mapping_occurrences.add(assertion_node.id)
                expected_mapping_node_ids.add(mapping.semantic_node_id)
            elif mapping is not None:
                raise ADV4Error("projection_integrity", "", "Condition assertion has an invalid identity mapping", http_status=409)

        if group_value is None:
            if group is not None:
                raise ADV4Error("projection_integrity", "", "Unexpected condition designation group", http_status=409)
            continue
        group_pointer = f"{pointer}/subject/designationGroup"
        group_node = node_by_id.get(group.semantic_node_id) if group else None
        display_pointer = f"{group_pointer}/sourceDisplayText"
        display_node = nodes_by_pointer_type.get((display_pointer, "value_assertion"))
        if (
            group is None or group_node is None or display_node is None
            or group.projection_id != projection.id or group.proposal_id != candidate.id
            or group.condition_node_id != node.id
            or group.group_key != group_value["groupKey"]
            or group.association != group_value["association"]
            or group.source_display_assertion_node_id != display_node.id
            or group.reason != group_value.get("reason")
            or group.temporal_scope != group_value.get("temporalScope", {}).get("kind")
            or group.canonical_ordinal != 0
        ):
            raise ADV4Error("projection_integrity", "", "Condition designation group differs", http_status=409)
        verifier.node(
            group_node, node_type="designation_group", node_key=group_pointer,
            pointer=group_pointer, value=group_value, parent_id=node.id, ordinal=0,
        )
        verifier.evidence(group_node.id, group_value["evidenceKeys"], "condition_clause")
        expected_group_ids.add(group_node.id)
        verify_assertion(
            display_pointer, group_node.id, "source_display_text",
            group_value["sourceDisplayText"], "subject_value",
        )
        stored_members = members_by_group.get(group_node.id, [])
        if len(stored_members) != len(group_value["members"]):
            raise ADV4Error("projection_integrity", "", "Condition group member count differs", http_status=409)
        for member_ordinal, (member, member_value) in enumerate(zip(
            stored_members, group_value["members"], strict=True,
        )):
            member_pointer = f"{group_pointer}/members/{member_ordinal}"
            member_node = node_by_id.get(member.semantic_node_id)
            manufacturer_pointer = f"{member_pointer}/manufacturer"
            manufacturer_node = nodes_by_pointer_type.get((manufacturer_pointer, "value_assertion"))
            is_series = member_value["designationKind"] == "series_expression"
            if (
                member_node is None or manufacturer_node is None
                or member.projection_id != projection.id or member.proposal_id != candidate.id
                or member.group_node_id != group_node.id
                or member.member_key != member_value["memberKey"]
                or member.designation_kind != member_value["designationKind"]
                or member.source_designation != member_value.get("sourceDesignation")
                or member.expression_text != member_value.get("expressionText")
                or member.manufacturer_assertion_node_id != manufacturer_node.id
                or member.manufacturer_state != member_value["manufacturer"]["state"]
                or member.manufacturer_value != member_value["manufacturer"].get("value")
                or member.manufacturer_reason != member_value["manufacturer"].get("reason")
                or member.manufacturer_temporal_scope != member_value["manufacturer"].get("temporalScope", {}).get("kind")
                or member.evaluation_state != ("unevaluated" if is_series else None)
                or member.evaluation_reason != ("unsupported_expression" if is_series else None)
                or member.canonical_ordinal != member_ordinal
            ):
                raise ADV4Error("projection_integrity", "", "Condition group member differs", http_status=409)
            verifier.node(
                member_node, node_type="designation_group_member",
                node_key=member_pointer, pointer=member_pointer,
                value=member_value, parent_id=group_node.id, ordinal=member_ordinal,
            )
            verifier.evidence(member_node.id, member_value["evidenceKeys"], "subject_value")
            expected_member_ids.add(member_node.id)
            manufacturer_node = verify_assertion(
                manufacturer_pointer, member_node.id, "manufacturer",
                member_value["manufacturer"], "identity_support",
            )
            designation_mapping = mapping_by_occurrence.get(member_node.id)
            if designation_mapping is None or member.designation_identity_mapping_node_id != designation_mapping.semantic_node_id:
                raise ADV4Error("projection_integrity", "", "Condition member identity mapping is missing", http_status=409)
            verifier.mapping(
                designation_mapping.semantic_node_id, member_node.id, group_node.id,
                "series" if is_series else "model",
                member_value.get("expressionText") if is_series else member_value["sourceDesignation"],
                origin="source_only", normalized_state="unknown",
                normalized_value=None, reason="not_extracted",
                temporal_scope="directive_version", namespace=None, version=None,
            )
            expected_mapping_occurrences.add(member_node.id)
            expected_mapping_node_ids.add(designation_mapping.semantic_node_id)
            manufacturer_mapping = mapping_by_occurrence.get(manufacturer_node.id)
            if member_value["manufacturer"]["state"] == "known":
                if manufacturer_mapping is None:
                    raise ADV4Error("projection_integrity", "", "Condition member manufacturer mapping is missing", http_status=409)
                verifier.mapping(
                    manufacturer_mapping.semantic_node_id, manufacturer_node.id,
                    group_node.id, "manufacturer",
                    member_value["manufacturer"]["value"], origin="source_only",
                    normalized_state="unknown", normalized_value=None,
                    reason="not_extracted", temporal_scope="directive_version",
                    namespace=None, version=None,
                )
                expected_mapping_occurrences.add(manufacturer_node.id)
                expected_mapping_node_ids.add(manufacturer_mapping.semantic_node_id)
            elif manufacturer_mapping is not None:
                raise ADV4Error("projection_integrity", "", "Unknown member manufacturer has a mapping", http_status=409)

    if len(groups) != len(expected_group_ids) or len(members) != len(expected_member_ids):
        raise ADV4Error("projection_integrity", "", "Condition group owner set differs", http_status=409)
    condition_parent_ids = {
        row.semantic_node_id for row in conditions
    } | expected_group_ids | expected_member_ids
    stored_assertions = db.scalars(select(ADV4CandidateAppValueAssertion).where(
        ADV4CandidateAppValueAssertion.projection_id == projection.id,
        ADV4CandidateAppValueAssertion.parent_semantic_node_id.in_(condition_parent_ids),
    )).all() if condition_parent_ids else []
    if {row.semantic_node_id for row in stored_assertions} != expected_assertion_ids:
        raise ADV4Error("projection_integrity", "", "Condition assertion owner set differs", http_status=409)
    condition_family_node_ids = {
        node.id for node in verifier.nodes
        if node.source_pointer.startswith("/conditionDefinitions/")
        and node.node_type in {
            "condition", "value_assertion", "designation_group",
            "designation_group_member", "identity_mapping",
        }
    }
    expected_condition_node_ids = (
        {row.semantic_node_id for row in conditions}
        | expected_assertion_ids | expected_group_ids | expected_member_ids
        | expected_mapping_node_ids
    )
    condition_mappings = [
        row for row in mappings
        if row.source_occurrence_node_id in condition_family_node_ids
    ]
    actual_mapping_occurrences = [row.source_occurrence_node_id for row in condition_mappings]
    if (
        set(actual_mapping_occurrences) != expected_mapping_occurrences
        or len(actual_mapping_occurrences) != len(expected_mapping_occurrences)
        or condition_family_node_ids != expected_condition_node_ids
    ):
        raise ADV4Error("projection_integrity", "", "Condition identity mapping set differs", http_status=409)


def _verify_rule_owners(
    db: Session,
    projection: ADV4CandidateAppProjection,
    candidate: ADV4CandidateProposal,
) -> None:
    verifier = _TypedGraphVerifier(db, projection, candidate)
    nodes_by_pointer_type = {
        (node.source_pointer, node.node_type): node for node in verifier.nodes
    }
    nodes_by_type_key = {
        (node.node_type, node.node_key): node for node in verifier.nodes
    }
    rules = db.scalars(select(ADV4CandidateAppRule).where(
        ADV4CandidateAppRule.projection_id == projection.id
    )).all()
    rule_by_key = {row.rule_key: row for row in rules}
    expressions = db.scalars(select(ADV4CandidateAppExpression).where(
        ADV4CandidateAppExpression.projection_id == projection.id
    )).all()
    expression_by_node = {row.semantic_node_id: row for row in expressions}
    edges = db.scalars(select(ADV4CandidateAppExpressionEdge).where(
        ADV4CandidateAppExpressionEdge.projection_id == projection.id
    )).all()
    edges_by_parent: dict[str, list[ADV4CandidateAppExpressionEdge]] = {}
    for edge in edges:
        edges_by_parent.setdefault(edge.parent_expression_id, []).append(edge)
    for children in edges_by_parent.values():
        children.sort(key=lambda row: row.sequence)
    exclusions = db.scalars(select(ADV4CandidateAppRuleExclusion).where(
        ADV4CandidateAppRuleExclusion.projection_id == projection.id
    )).all()
    exclusions_by_rule: dict[str, list[ADV4CandidateAppRuleExclusion]] = {}
    for exclusion in exclusions:
        exclusions_by_rule.setdefault(exclusion.rule_node_id, []).append(exclusion)
    for rule_exclusions in exclusions_by_rule.values():
        rule_exclusions.sort(key=lambda row: row.canonical_ordinal)

    expected_rule_ids: set[str] = set()
    expected_expression_ids: set[str] = set()
    expected_edges: set[tuple[str, int]] = set()
    expected_exclusions: set[tuple[str, int]] = set()
    dependency_graph: dict[str, set[str]] = {
        value["ruleKey"]: set() for value in candidate.parsed_json["applicabilityRules"]
    }

    def verify_expression(
        value: dict[str, Any],
        *,
        pointer: str,
        root_pointer: str,
        parent_id: str,
        ordinal: int,
        owning_rule_id: str,
        owning_rule_key: str,
        context: str,
    ) -> None:
        node = nodes_by_pointer_type.get((pointer, "expression"))
        row = expression_by_node.get(node.id) if node else None
        node_type = value.get("nodeType")
        if node_type == "requirement_state_ref":
            raise ADV4Error(
                "projection_integrity", pointer,
                "Applicability expression contains a requirement-state reference",
                http_status=409,
            )
        if node_type not in {"scope_ref", "predicate_ref", "rule_ref", "not", "all", "any"}:
            raise ADV4Error("projection_integrity", pointer, "Unknown applicability expression", http_status=409)
        scope_node = nodes_by_type_key.get(("product_scope", value.get("scopeKey")))
        condition_node = nodes_by_type_key.get(("condition", value.get("conditionKey")))
        referenced_rule = nodes_by_type_key.get(("applicability_rule", value.get("ruleKey")))
        expected_scope = scope_node.id if node_type == "scope_ref" and scope_node else None
        expected_condition = condition_node.id if node_type == "predicate_ref" and condition_node else None
        expected_rule = referenced_rule.id if node_type == "rule_ref" and referenced_rule else None
        if (
            (node_type == "scope_ref" and scope_node is None)
            or (node_type == "predicate_ref" and condition_node is None)
            or (node_type == "rule_ref" and referenced_rule is None)
        ):
            raise ADV4Error("projection_integrity", pointer, "Applicability expression reference is unresolved", http_status=409)
        relative_path = "/" if pointer == root_pointer else pointer[len(root_pointer):]
        if (
            node is None or row is None
            or row.projection_id != projection.id or row.proposal_id != candidate.id
            or row.owning_rule_node_id != owning_rule_id
            or row.expression_context != context or row.expression_path != relative_path
            or row.expression_node_type != node_type
            or row.result_domain != "true_false_unknown"
            or row.evaluator_contract != "none"
            or row.scope_node_id != expected_scope
            or row.condition_node_id != expected_condition
            or row.referenced_rule_node_id != expected_rule
        ):
            raise ADV4Error("projection_integrity", pointer, "Expression owner differs", http_status=409)
        verifier.node(
            node, node_type="expression", node_key=pointer,
            pointer=pointer, value=value, parent_id=parent_id, ordinal=ordinal,
        )
        verifier.evidence(node.id, [], "identity_support")
        expected_expression_ids.add(node.id)
        if node_type == "rule_ref":
            dependency_graph[owning_rule_key].add(value["ruleKey"])

        child_values: list[tuple[str, dict[str, Any]]] = []
        if node_type == "not":
            child_values = [(f"{pointer}/operand", value["operand"])]
        elif node_type in {"all", "any"}:
            child_values = [
                (f"{pointer}/operands/{index}", child)
                for index, child in enumerate(value["operands"])
            ]
            if len(child_values) < 2:
                raise ADV4Error("projection_integrity", pointer, "Expression arity differs", http_status=409)
        actual_edges = edges_by_parent.get(node.id, [])
        if len(actual_edges) != len(child_values):
            raise ADV4Error("projection_integrity", pointer, "Expression edge cardinality differs", http_status=409)
        for sequence, ((child_pointer, child_value), edge) in enumerate(zip(child_values, actual_edges, strict=True)):
            child_node = nodes_by_pointer_type.get((child_pointer, "expression"))
            if (
                child_node is None or edge.sequence != sequence
                or edge.projection_id != projection.id or edge.proposal_id != candidate.id
                or edge.owning_rule_node_id != owning_rule_id
                or edge.expression_context != context
                or edge.parent_expression_id != node.id
                or edge.child_expression_id != child_node.id
            ):
                raise ADV4Error("projection_integrity", pointer, "Expression edge differs", http_status=409)
            expected_edges.add((node.id, sequence))
            verify_expression(
                child_value, pointer=child_pointer, root_pointer=root_pointer,
                parent_id=node.id, ordinal=sequence,
                owning_rule_id=owning_rule_id,
                owning_rule_key=owning_rule_key, context=context,
            )

    canonical_rules = candidate.parsed_json["applicabilityRules"]
    if len(rules) != len(canonical_rules):
        raise ADV4Error("projection_integrity", "", "Rule owner count differs", http_status=409)
    for ordinal, value in enumerate(canonical_rules):
        pointer = f"/applicabilityRules/{ordinal}"
        row = rule_by_key.get(value["ruleKey"])
        node = nodes_by_pointer_type.get((pointer, "applicability_rule"))
        scope_pointer = f"{pointer}/scopeExpression"
        condition_pointer = f"{pointer}/conditionExpression"
        scope_node = nodes_by_pointer_type.get((scope_pointer, "expression"))
        condition_node = nodes_by_pointer_type.get((condition_pointer, "expression"))
        if (
            row is None or node is None or scope_node is None
            or row.semantic_node_id != node.id
            or row.projection_id != projection.id or row.proposal_id != candidate.id
            or row.scope_expression_node_id != scope_node.id
            or row.condition_presence != ("present" if "conditionExpression" in value else "property_absent")
            or row.condition_expression_node_id != (condition_node.id if "conditionExpression" in value and condition_node else None)
            or row.evaluator_contract != "none"
        ):
            raise ADV4Error("projection_integrity", pointer, "Rule owner differs", http_status=409)
        verifier.node(
            node, node_type="applicability_rule", node_key=value["ruleKey"],
            pointer=pointer, value=value, parent_id=None, ordinal=ordinal,
        )
        verifier.evidence(node.id, value["evidenceKeys"], "rule_clause")
        expected_rule_ids.add(node.id)
        verify_expression(
            value["scopeExpression"], pointer=scope_pointer,
            root_pointer=scope_pointer, parent_id=node.id, ordinal=0,
            owning_rule_id=node.id, owning_rule_key=value["ruleKey"], context="scope",
        )
        if "conditionExpression" in value:
            if condition_node is None:
                raise ADV4Error("projection_integrity", condition_pointer, "Condition expression root is missing", http_status=409)
            verify_expression(
                value["conditionExpression"], pointer=condition_pointer,
                root_pointer=condition_pointer, parent_id=node.id, ordinal=0,
                owning_rule_id=node.id, owning_rule_key=value["ruleKey"], context="condition",
            )
        elif condition_node is not None:
            raise ADV4Error("projection_integrity", condition_pointer, "Unexpected condition expression root", http_status=409)

        stored_exclusions = exclusions_by_rule.get(node.id, [])
        if len(stored_exclusions) != len(value["exclusionRuleKeys"]):
            raise ADV4Error("projection_integrity", pointer, "Rule exclusion count differs", http_status=409)
        for exclusion_ordinal, (stored, excluded_key) in enumerate(zip(
            stored_exclusions, value["exclusionRuleKeys"], strict=True,
        )):
            excluded = nodes_by_type_key.get(("applicability_rule", excluded_key))
            if (
                excluded is None or stored.canonical_ordinal != exclusion_ordinal
                or stored.projection_id != projection.id or stored.proposal_id != candidate.id
                or stored.rule_node_id != node.id
                or stored.excluded_rule_node_id != excluded.id
            ):
                raise ADV4Error("projection_integrity", pointer, "Rule exclusion differs", http_status=409)
            expected_exclusions.add((node.id, exclusion_ordinal))
            dependency_graph[value["ruleKey"]].add(excluded_key)

    if (
        {row.semantic_node_id for row in rules} != expected_rule_ids
        or {row.semantic_node_id for row in expressions} != expected_expression_ids
        or {(row.parent_expression_id, row.sequence) for row in edges} != expected_edges
        or {(row.rule_node_id, row.canonical_ordinal) for row in exclusions} != expected_exclusions
    ):
        raise ADV4Error("projection_integrity", "", "Rule/expression owner set differs", http_status=409)
    family_node_ids = {
        node.id for node in verifier.nodes
        if node.source_pointer.startswith("/applicabilityRules/")
        and node.node_type in {"applicability_rule", "expression"}
    }
    if family_node_ids != expected_rule_ids | expected_expression_ids:
        raise ADV4Error("projection_integrity", "", "Rule/expression semantic set differs", http_status=409)

    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(rule_key: str) -> None:
        if rule_key in visiting:
            raise ADV4Error("projection_integrity", "", "Rule dependency graph is cyclic", http_status=409)
        if rule_key in visited:
            return
        visiting.add(rule_key)
        for target in dependency_graph[rule_key]:
            if target not in dependency_graph:
                raise ADV4Error("projection_integrity", "", "Rule dependency target is missing", http_status=409)
            visit(target)
        visiting.remove(rule_key)
        visited.add(rule_key)

    for key in dependency_graph:
        visit(key)


def _verify_search_hint_owners(
    db: Session,
    projection: ADV4CandidateAppProjection,
    candidate: ADV4CandidateProposal,
) -> None:
    verifier = _TypedGraphVerifier(db, projection, candidate)
    node_by_id = verifier.node_by_id
    nodes_by_pointer_type = {
        (node.source_pointer, node.node_type): node for node in verifier.nodes
    }
    mappings = db.scalars(select(ADV4CandidateAppIdentityMapping).where(
        ADV4CandidateAppIdentityMapping.projection_id == projection.id
    )).all()
    mapping_by_occurrence = {row.source_occurrence_node_id: row for row in mappings}
    hints = db.scalars(select(ADV4CandidateAppSearchHint).where(
        ADV4CandidateAppSearchHint.projection_id == projection.id
    )).all()
    hint_by_key = {row.hint_key: row for row in hints}
    groups = db.scalars(select(ADV4CandidateAppSearchHintGroup).where(
        ADV4CandidateAppSearchHintGroup.projection_id == projection.id
    )).all()
    groups_by_hint: dict[str, list[ADV4CandidateAppSearchHintGroup]] = {}
    for group in groups:
        groups_by_hint.setdefault(group.hint_node_id, []).append(group)
    for values in groups_by_hint.values():
        values.sort(key=lambda row: row.canonical_ordinal)
    members = db.scalars(select(ADV4CandidateAppSearchHintMember).where(
        ADV4CandidateAppSearchHintMember.projection_id == projection.id
    )).all()
    members_by_group: dict[str, list[ADV4CandidateAppSearchHintMember]] = {}
    for member in members:
        members_by_group.setdefault(member.group_node_id, []).append(member)
    for values in members_by_group.values():
        values.sort(key=lambda row: row.canonical_ordinal)

    expected_hint_ids: set[str] = set()
    expected_group_ids: set[str] = set()
    expected_member_ids: set[str] = set()
    expected_assertion_ids: set[str] = set()
    expected_mapping_occurrences: set[str] = set()
    expected_mapping_node_ids: set[str] = set()

    def verify_assertion(
        pointer: str,
        parent_id: str,
        field_code: str,
        value: dict[str, Any],
        purpose: str,
    ) -> ADV4CandidateAppSemanticNode:
        node = nodes_by_pointer_type.get((pointer, "value_assertion"))
        row = db.get(ADV4CandidateAppValueAssertion, node.id) if node else None
        if (
            node is None or row is None
            or row.projection_id != projection.id or row.proposal_id != candidate.id
            or row.parent_semantic_node_id != parent_id
            or row.field_code != field_code or row.value_type != "text"
            or row.state != value["state"] or row.text_value != value.get("value")
            or row.reason != value.get("reason")
            or row.temporal_scope != value.get("temporalScope", {}).get("kind")
        ):
            raise ADV4Error("projection_integrity", pointer, "Search-hint assertion differs", http_status=409)
        verifier.node(
            node, node_type="value_assertion", node_key=pointer,
            pointer=pointer, value=value, parent_id=parent_id, ordinal=0,
        )
        verifier.evidence(node.id, value["evidenceKeys"], purpose)
        expected_assertion_ids.add(node.id)
        return node

    canonical_hints = candidate.parsed_json["applicabilitySearchHints"]
    if len(hints) != len(canonical_hints):
        raise ADV4Error("projection_integrity", "", "Search-hint owner count differs", http_status=409)
    for hint_ordinal, hint_value in enumerate(canonical_hints):
        hint_pointer = f"/applicabilitySearchHints/{hint_ordinal}"
        row = hint_by_key.get(hint_value["hintKey"])
        node = nodes_by_pointer_type.get((hint_pointer, "search_hint"))
        display_pointer = f"{hint_pointer}/sourceDisplayText"
        display_node = nodes_by_pointer_type.get((display_pointer, "value_assertion"))
        if (
            row is None or node is None or display_node is None
            or row.semantic_node_id != node.id
            or row.projection_id != projection.id or row.proposal_id != candidate.id
            or row.hint_key != hint_value["hintKey"]
            or row.product_role != hint_value["productRole"]
            or row.source_display_assertion_node_id != display_node.id
            or row.controlling is not False or row.exhaustive is not False
            or hint_value["controlling"] is not False or hint_value["exhaustive"] is not False
        ):
            raise ADV4Error("projection_integrity", hint_pointer, "Search-hint owner differs", http_status=409)
        verifier.node(
            node, node_type="search_hint", node_key=hint_value["hintKey"],
            pointer=hint_pointer, value=hint_value, parent_id=None,
            ordinal=hint_ordinal,
        )
        verifier.evidence(node.id, hint_value["evidenceKeys"], "search_hint_clause")
        expected_hint_ids.add(node.id)
        verify_assertion(
            display_pointer, node.id, "source_display_text",
            hint_value["sourceDisplayText"], "search_hint_clause",
        )

        stored_groups = groups_by_hint.get(node.id, [])
        canonical_groups = hint_value["manufacturerModelGroups"]
        if len(stored_groups) != len(canonical_groups):
            raise ADV4Error("projection_integrity", hint_pointer, "Search-hint group count differs", http_status=409)
        for group_ordinal, (group, group_value) in enumerate(zip(
            stored_groups, canonical_groups, strict=True,
        )):
            group_pointer = f"{hint_pointer}/manufacturerModelGroups/{group_ordinal}"
            group_node = nodes_by_pointer_type.get((group_pointer, "search_hint_group"))
            manufacturer_pointer = f"{group_pointer}/manufacturer"
            manufacturer_node = nodes_by_pointer_type.get((manufacturer_pointer, "value_assertion"))
            if (
                group_node is None or manufacturer_node is None
                or group.semantic_node_id != group_node.id
                or group.projection_id != projection.id or group.proposal_id != candidate.id
                or group.hint_node_id != node.id or group.group_key != group_value["groupKey"]
                or group.manufacturer_assertion_node_id != manufacturer_node.id
                or group.manufacturer_state != group_value["manufacturer"]["state"]
                or group.manufacturer_value != group_value["manufacturer"].get("value")
                or group.manufacturer_reason != group_value["manufacturer"].get("reason")
                or group.manufacturer_temporal_scope != group_value["manufacturer"].get("temporalScope", {}).get("kind")
                or group.association != group_value["association"]
                or group.reason != group_value.get("reason")
                or group.temporal_scope != group_value.get("temporalScope", {}).get("kind")
                or group.canonical_ordinal != group_ordinal
            ):
                raise ADV4Error("projection_integrity", group_pointer, "Search-hint group differs", http_status=409)
            verifier.node(
                group_node, node_type="search_hint_group", node_key=group_pointer,
                pointer=group_pointer, value=group_value, parent_id=node.id,
                ordinal=group_ordinal,
            )
            verifier.evidence(group_node.id, group_value["evidenceKeys"], "search_hint_clause")
            expected_group_ids.add(group_node.id)
            manufacturer_node = verify_assertion(
                manufacturer_pointer, group_node.id, "manufacturer",
                group_value["manufacturer"], "identity_support",
            )
            group_manufacturer_mapping = mapping_by_occurrence.get(manufacturer_node.id)
            if group_value["manufacturer"]["state"] == "known":
                if group_manufacturer_mapping is None:
                    raise ADV4Error("projection_integrity", group_pointer, "Search-hint group manufacturer mapping is missing", http_status=409)
                verifier.mapping(
                    group_manufacturer_mapping.semantic_node_id, manufacturer_node.id,
                    group_node.id, "manufacturer", group_value["manufacturer"]["value"],
                    origin="source_only", normalized_state="unknown",
                    normalized_value=None, reason="not_extracted",
                    temporal_scope="directive_version", namespace=None, version=None,
                )
                expected_mapping_occurrences.add(manufacturer_node.id)
                expected_mapping_node_ids.add(group_manufacturer_mapping.semantic_node_id)
            elif group_manufacturer_mapping is not None:
                raise ADV4Error("projection_integrity", group_pointer, "Unknown search-hint group manufacturer has a mapping", http_status=409)

            stored_members = members_by_group.get(group_node.id, [])
            if len(stored_members) != len(group_value["members"]):
                raise ADV4Error("projection_integrity", group_pointer, "Search-hint member count differs", http_status=409)
            for member_ordinal, (member, member_value) in enumerate(zip(
                stored_members, group_value["members"], strict=True,
            )):
                member_pointer = f"{group_pointer}/members/{member_ordinal}"
                member_node = nodes_by_pointer_type.get((member_pointer, "search_hint_model"))
                member_manufacturer_pointer = f"{member_pointer}/manufacturer"
                member_manufacturer_node = nodes_by_pointer_type.get((member_manufacturer_pointer, "value_assertion"))
                is_series = member_value["designationKind"] == "series_expression"
                if (
                    member_node is None or member_manufacturer_node is None
                    or member.semantic_node_id != member_node.id
                    or member.projection_id != projection.id or member.proposal_id != candidate.id
                    or member.group_node_id != group_node.id
                    or member.member_key != member_value["memberKey"]
                    or member.designation_kind != member_value["designationKind"]
                    or member.source_designation != member_value.get("sourceDesignation")
                    or member.expression_text != member_value.get("expressionText")
                    or member.manufacturer_assertion_node_id != member_manufacturer_node.id
                    or member.manufacturer_state != member_value["manufacturer"]["state"]
                    or member.manufacturer_value != member_value["manufacturer"].get("value")
                    or member.manufacturer_reason != member_value["manufacturer"].get("reason")
                    or member.manufacturer_temporal_scope != member_value["manufacturer"].get("temporalScope", {}).get("kind")
                    or member.evaluation_state != ("unevaluated" if is_series else None)
                    or member.evaluation_reason != ("unsupported_expression" if is_series else None)
                    or member.canonical_ordinal != member_ordinal
                ):
                    raise ADV4Error("projection_integrity", member_pointer, "Search-hint member differs", http_status=409)
                verifier.node(
                    member_node, node_type="search_hint_model", node_key=member_pointer,
                    pointer=member_pointer, value=member_value, parent_id=group_node.id,
                    ordinal=member_ordinal,
                )
                verifier.evidence(member_node.id, member_value["evidenceKeys"], "search_hint_clause")
                expected_member_ids.add(member_node.id)
                member_manufacturer_node = verify_assertion(
                    member_manufacturer_pointer, member_node.id, "manufacturer",
                    member_value["manufacturer"], "identity_support",
                )
                designation_mapping = mapping_by_occurrence.get(member_node.id)
                if designation_mapping is None or member.designation_identity_mapping_node_id != designation_mapping.semantic_node_id:
                    raise ADV4Error("projection_integrity", member_pointer, "Search-hint designation mapping is missing", http_status=409)
                verifier.mapping(
                    designation_mapping.semantic_node_id, member_node.id, group_node.id,
                    "series" if is_series else "model",
                    member_value.get("expressionText") if is_series else member_value["sourceDesignation"],
                    origin="source_only", normalized_state="unknown",
                    normalized_value=None, reason="not_extracted",
                    temporal_scope="directive_version", namespace=None, version=None,
                )
                expected_mapping_occurrences.add(member_node.id)
                expected_mapping_node_ids.add(designation_mapping.semantic_node_id)
                member_manufacturer_mapping = mapping_by_occurrence.get(member_manufacturer_node.id)
                if member_value["manufacturer"]["state"] == "known":
                    if member_manufacturer_mapping is None:
                        raise ADV4Error("projection_integrity", member_pointer, "Search-hint member manufacturer mapping is missing", http_status=409)
                    verifier.mapping(
                        member_manufacturer_mapping.semantic_node_id,
                        member_manufacturer_node.id, group_node.id, "manufacturer",
                        member_value["manufacturer"]["value"], origin="source_only",
                        normalized_state="unknown", normalized_value=None,
                        reason="not_extracted", temporal_scope="directive_version",
                        namespace=None, version=None,
                    )
                    expected_mapping_occurrences.add(member_manufacturer_node.id)
                    expected_mapping_node_ids.add(member_manufacturer_mapping.semantic_node_id)
                elif member_manufacturer_mapping is not None:
                    raise ADV4Error("projection_integrity", member_pointer, "Unknown search-hint member manufacturer has a mapping", http_status=409)

    if (
        {row.semantic_node_id for row in hints} != expected_hint_ids
        or {row.semantic_node_id for row in groups} != expected_group_ids
        or {row.semantic_node_id for row in members} != expected_member_ids
    ):
        raise ADV4Error("projection_integrity", "", "Search-hint owner set differs", http_status=409)
    parent_ids = expected_hint_ids | expected_group_ids | expected_member_ids
    stored_assertions = db.scalars(select(ADV4CandidateAppValueAssertion).where(
        ADV4CandidateAppValueAssertion.projection_id == projection.id,
        ADV4CandidateAppValueAssertion.parent_semantic_node_id.in_(parent_ids),
    )).all() if parent_ids else []
    if {row.semantic_node_id for row in stored_assertions} != expected_assertion_ids:
        raise ADV4Error("projection_integrity", "", "Search-hint assertion owner set differs", http_status=409)
    family_node_ids = {
        node.id for node in verifier.nodes
        if node.source_pointer.startswith("/applicabilitySearchHints/")
        and node.node_type in {
            "search_hint", "search_hint_group", "search_hint_model",
            "value_assertion", "identity_mapping",
        }
    }
    expected_node_ids = (
        expected_hint_ids | expected_group_ids | expected_member_ids
        | expected_assertion_ids | expected_mapping_node_ids
    )
    family_mappings = [
        row for row in mappings if row.source_occurrence_node_id in family_node_ids
    ]
    actual_mapping_occurrences = [row.source_occurrence_node_id for row in family_mappings]
    if (
        set(actual_mapping_occurrences) != expected_mapping_occurrences
        or len(actual_mapping_occurrences) != len(expected_mapping_occurrences)
        or family_node_ids != expected_node_ids
    ):
        raise ADV4Error("projection_integrity", "", "Search-hint identity/semantic set differs", http_status=409)


def _verify_correction_foundation(
    db: Session,
    projection: ADV4CandidateAppProjection,
    candidate: ADV4CandidateProposal,
) -> list[dict[str, Any]]:
    """Reconstruct and verify the proposal-scoped correction foundation exactly."""
    expected = candidate.parsed_json["authoritativeCorrections"]
    documents = {
        item["officialDocumentKey"]: item
        for item in candidate.parsed_json["officialDocuments"]
    }
    roots = db.scalars(
        select(ADV4CandidateCorrection)
        .where(ADV4CandidateCorrection.proposal_id == candidate.id)
        .order_by(ADV4CandidateCorrection.canonical_ordinal)
    ).all()
    if len(roots) != len(expected):
        raise ADV4Error("projection_integrity", "", "Correction foundation count differs", http_status=409)
    reconstructed: list[dict[str, Any]] = []
    three_a_types = {
        "productScopes": "product_scope",
        "conditionDefinitions": "condition",
        "applicabilityRules": "applicability_rule",
    }
    for ordinal, (root, canonical) in enumerate(zip(roots, expected, strict=True)):
        refs = db.scalars(
            select(ADV4CandidateCorrectionRef)
            .where(ADV4CandidateCorrectionRef.correction_id == root.id)
            .order_by(ADV4CandidateCorrectionRef.canonical_ordinal)
        ).all()
        evidence = db.scalars(
            select(ADV4CandidateCorrectionEvidenceLink)
            .where(ADV4CandidateCorrectionEvidenceLink.correction_id == root.id)
            .order_by(ADV4CandidateCorrectionEvidenceLink.canonical_ordinal)
        ).all()
        value = {
            "correctionKey": root.correction_key,
            "correctionType": root.correction_type,
            "originalDocumentRefKey": root.original_document_ref_key,
            "correctingDocumentRefKey": root.correcting_document_ref_key,
            "changedSemanticRefs": [
                {"namespace": ref.namespace, "key": ref.semantic_key}
                for ref in refs
            ],
            "evidenceKeys": [link.evidence_key for link in evidence],
        }
        original = documents.get(root.original_document_ref_key)
        correcting = documents.get(root.correcting_document_ref_key)
        if (
            root.canonical_ordinal != ordinal
            or root.foundation_version != "paprnav-ad-v4-correction-foundation-1"
            or root.generation != 1
            or root.expected_ref_count != len(refs)
            or root.expected_evidence_count != len(evidence)
            or original is None
            or correcting is None
            or root.original_document_identity_hash != _document_identity(original)
            or root.correcting_document_identity_hash != _document_identity(correcting)
            or root.canonical_hash
            != hashlib.sha256(canonical_bytes(value, CANONICALIZATION_VERSION_V2)).hexdigest()
            or value != canonical
        ):
            raise ADV4Error("projection_integrity", "", "Correction foundation differs from candidate", http_status=409)
        for ref_ordinal, ref in enumerate(refs):
            expected_owner = "slice_3a" if ref.namespace in three_a_types else (
                "foundation" if ref.namespace in {"directiveIdentity", "supersessionRelations"} else "slice_3b"
            )
            bindings = db.scalars(
                select(ADV4CandidateCorrectionSemanticBinding).where(
                    ADV4CandidateCorrectionSemanticBinding.correction_ref_id == ref.id
                )
            ).all()
            if (
                ref.canonical_ordinal != ref_ordinal
                or ref.owner_slice != expected_owner
                or ref.reference_hash
                != _row_id("avf", "correction-ref", {
                    "correctionId": root.id,
                    "namespace": ref.namespace,
                    "key": ref.semantic_key,
                })[1]
                or len(bindings) != (1 if expected_owner == "slice_3a" else 0)
            ):
                raise ADV4Error("projection_integrity", "", "Correction reference is incomplete", http_status=409)
            if bindings:
                binding = bindings[0]
                node = db.get(ADV4CandidateAppSemanticNode, binding.semantic_node_id)
                if (
                    binding.proposal_id != candidate.id
                    or binding.projection_id != projection.id
                    or binding.binding_slice != "slice_3a"
                    or binding.generation != 1
                    or node is None
                    or node.projection_id != projection.id
                    or node.node_type != three_a_types[ref.namespace]
                    or node.node_key != ref.semantic_key
                ):
                    raise ADV4Error("projection_integrity", "", "Correction semantic binding differs", http_status=409)
        for evidence_ordinal, link in enumerate(evidence):
            binding = db.get(ADV4CandidateEvidenceBinding, link.candidate_binding_id)
            if (
                link.canonical_ordinal != evidence_ordinal
                or binding is None
                or binding.proposal_id != candidate.id
                or binding.evidence_key != link.evidence_key
            ):
                raise ADV4Error("projection_integrity", "", "Correction evidence differs", http_status=409)
        reconstructed.append(value)
    return reconstructed


def materialize_applicability(
    db: Session,
    *,
    directive_id: str,
    proposal_id: str,
    actor: User,
    membership_id: str,
    idempotency_key: str,
) -> MaterializedApplicability:
    _require_application_gate(materialize=True)
    membership = _authorization(db, actor, membership_id)
    scope = f"{actor.id}:{membership.id}:{ENDPOINT_ACTION}:{POLICY_VERSION}:{idempotency_key}"
    _advisory_lock(db, f"idem:{scope}")
    candidate = db.scalar(select(ADV4CandidateProposal).where(ADV4CandidateProposal.id == proposal_id).with_for_update())
    if candidate is None or candidate.directive_id != directive_id:
        raise ADV4Error("not_found", "", "Candidate proposal not found", http_status=404)
    _lock_database_gates(db, materialize=True)
    candidate = verified_candidate(db, candidate.id)
    if candidate.gate != "candidate_only" or candidate.validator_version != VALIDATOR_VERSION_V2 or candidate.canonicalization_version != CANONICALIZATION_VERSION_V2:
        raise ADV4Error("predecessor_semantic_defect", "", "Candidate is not eligible for Slice-3A materialization", http_status=422)
    bindings = _verify_live_evidence(db, candidate)
    _lock_supersession_ad_numbers(db, candidate)
    _reject_new_predecessor_ambiguity(db, candidate)
    _advisory_lock(db, f"projection:{proposal_id}:{MATERIALIZER_VERSION}")
    request_value = {
        "action": ENDPOINT_ACTION, "directiveId": directive_id,
        "proposalId": proposal_id, "validatorVersion": VALIDATOR_VERSION_V2,
        "canonicalizationVersion": CANONICALIZATION_VERSION_V2,
        "materializerVersion": MATERIALIZER_VERSION,
    }
    request_bytes = canonical_bytes(request_value, CANONICALIZATION_VERSION_V2)
    request_hash = hashlib.sha256(ROW_DOMAIN + request_bytes).hexdigest()
    prior = db.scalar(select(ADV4CandidateAppMaterializationRequest).where(
        ADV4CandidateAppMaterializationRequest.actor_user_id == actor.id,
        ADV4CandidateAppMaterializationRequest.authorizing_membership_id == membership.id,
        ADV4CandidateAppMaterializationRequest.endpoint_action == ENDPOINT_ACTION,
        ADV4CandidateAppMaterializationRequest.auth_policy_version == POLICY_VERSION,
        ADV4CandidateAppMaterializationRequest.idempotency_key == idempotency_key,
    ))
    if prior is not None:
        if prior.request_hash != request_hash or prior.proposal_id != proposal_id:
            raise ADV4Error("idempotency_conflict", "", "Idempotency key was used for another projection", http_status=409)
        projection = db.get(ADV4CandidateAppProjection, prior.projection_id)
        if projection is None:
            raise ADV4Error("projection_integrity", "", "Idempotent request lost its projection", http_status=409)
        reconstruct_applicability(db, projection)
        _repair_stale_projection_on_materialization(db, projection)
        return MaterializedApplicability(projection, prior, False, True)

    projection = db.scalar(select(ADV4CandidateAppProjection).where(
        ADV4CandidateAppProjection.proposal_id == proposal_id,
        ADV4CandidateAppProjection.materializer_version == MATERIALIZER_VERSION,
    ))
    created = projection is None
    if projection is None:
        subtree = _app_subtree(candidate.parsed_json)
        subtree_bytes = canonical_bytes(subtree, CANONICALIZATION_VERSION_V2)
        subtree_hash = hashlib.sha256(SUBTREE_DOMAIN + subtree_bytes).hexdigest()
        provisional_id, identity_hash = _row_id("avx", "projection", {"proposalId": proposal_id, "materializerVersion": MATERIALIZER_VERSION, "subtreeHash": subtree_hash})
        semantic_rows: list[ADV4CandidateAppSemanticNode] = []
        datum_rows: list[ADV4CandidateAppDatum] = []
        nodes: dict[str, ADV4CandidateAppSemanticNode] = {}
        _flatten(subtree, pointer="", projection_id=provisional_id, proposal_id=proposal_id,
                 parent_node_id=None, semantic_rows=semantic_rows, datum_rows=datum_rows,
                 node_by_pointer=nodes)
        _augment_source_scope_semantics(
            provisional_id, proposal_id, candidate.parsed_json,
            semantic_rows, datum_rows,
        )
        for relation_index, relation in enumerate(candidate.parsed_json["supersessionRelations"]):
            pointer = f"/supersessionRelations/{relation_index}"
            node_key = f"{relation['relationType']}:{relation['predecessorAdNumber']}"
            node_id, node_hash = _row_id("avn", "semantic-node", {
                "projectionId": provisional_id, "nodeType": "change_dependency",
                "nodeKey": node_key, "pointer": pointer,
            })
            node = ADV4CandidateAppSemanticNode(
                id=node_id, identity_hash=node_hash, projection_id=provisional_id,
                proposal_id=proposal_id, parent_node_id=None,
                node_type="change_dependency",
                node_key=node_key,
                source_pointer=pointer,
                canonical_node_hash=hashlib.sha256(
                    canonical_bytes(relation, CANONICALIZATION_VERSION_V2)
                ).hexdigest(),
                canonical_ordinal=relation_index,
            )
            semantic_rows.append(node)
            nodes[pointer] = node
        identity_rows = _identity_rows(
            ADV4CandidateAppProjection(id=provisional_id, identity_hash=identity_hash, proposal_id=proposal_id, directive_id=directive_id, schema_version=candidate.schema_version, validator_version=candidate.validator_version, canonicalization_version=candidate.canonicalization_version, proposal_canonical_hash=candidate.canonical_hash, evidence_binding_hash=candidate.evidence_binding_hash, materializer_version=MATERIALIZER_VERSION, applicability_subtree_bytes=subtree_bytes, applicability_subtree_hash=subtree_hash, projection_canonical_bytes=b"", projection_hash="", gate="candidate_only", semantic_node_count=0, datum_count=0, evidence_link_count=0, identity_mapping_count=0),
            candidate.parsed_json, semantic_rows, datum_rows,
        )
        source_scope_rows = _source_scope_owner_rows(
            ADV4CandidateAppProjection(
                id=provisional_id, identity_hash=identity_hash, proposal_id=proposal_id,
                directive_id=directive_id, schema_version=candidate.schema_version,
                validator_version=candidate.validator_version,
                canonicalization_version=candidate.canonicalization_version,
                proposal_canonical_hash=candidate.canonical_hash,
                evidence_binding_hash=candidate.evidence_binding_hash,
                materializer_version=MATERIALIZER_VERSION,
                applicability_subtree_bytes=subtree_bytes,
                applicability_subtree_hash=subtree_hash,
                projection_canonical_bytes=b"", projection_hash="", gate="candidate_only",
                semantic_node_count=0, datum_count=0, evidence_link_count=0,
                identity_mapping_count=0,
            ),
            candidate.parsed_json, semantic_rows, identity_rows,
        )
        rule_owner_rows = _rule_owner_rows(
            ADV4CandidateAppProjection(
                id=provisional_id, identity_hash=identity_hash, proposal_id=proposal_id,
                directive_id=directive_id, schema_version=candidate.schema_version,
                validator_version=candidate.validator_version,
                canonicalization_version=candidate.canonicalization_version,
                proposal_canonical_hash=candidate.canonical_hash,
                evidence_binding_hash=candidate.evidence_binding_hash,
                materializer_version=MATERIALIZER_VERSION,
                applicability_subtree_bytes=subtree_bytes,
                applicability_subtree_hash=subtree_hash,
                projection_canonical_bytes=b"", projection_hash="", gate="candidate_only",
                semantic_node_count=0, datum_count=0, evidence_link_count=0,
                identity_mapping_count=0,
            ),
            candidate.parsed_json, semantic_rows,
        )
        search_hint_owner_rows = _search_hint_owner_rows(
            ADV4CandidateAppProjection(
                id=provisional_id, identity_hash=identity_hash, proposal_id=proposal_id,
                directive_id=directive_id, schema_version=candidate.schema_version,
                validator_version=candidate.validator_version,
                canonicalization_version=candidate.canonicalization_version,
                proposal_canonical_hash=candidate.canonical_hash,
                evidence_binding_hash=candidate.evidence_binding_hash,
                materializer_version=MATERIALIZER_VERSION,
                applicability_subtree_bytes=subtree_bytes,
                applicability_subtree_hash=subtree_hash,
                projection_canonical_bytes=b"", projection_hash="", gate="candidate_only",
                semantic_node_count=0, datum_count=0, evidence_link_count=0,
                identity_mapping_count=0,
            ),
            candidate.parsed_json, semantic_rows, identity_rows,
        )
        binding_by_key = bindings
        evidence_rows: list[ADV4CandidateAppEvidenceLink] = []
        for node in semantic_rows:
            keys = _semantic_evidence_keys(candidate.parsed_json, node)
            for ordinal, evidence_key in enumerate(keys):
                binding = binding_by_key[evidence_key]
                purpose = _evidence_purpose(node)
                link_id, link_hash = _row_id("avl", "evidence-link", {"projectionId": provisional_id, "nodeId": node.id, "purpose": purpose, "evidenceKey": evidence_key})
                evidence_rows.append(ADV4CandidateAppEvidenceLink(id=link_id, projection_id=provisional_id, proposal_id=proposal_id, semantic_node_id=node.id, candidate_binding_id=binding.id, evidence_key=evidence_key, purpose=purpose, canonical_ordinal=ordinal, link_hash=link_hash))
        projection_envelope = {
            "version": "ad-v4-applicability-projection-v2", "proposalId": proposal_id,
            "proposalCanonicalHash": candidate.canonical_hash,
            "evidenceBindingHash": candidate.evidence_binding_hash,
            "validatorVersion": candidate.validator_version,
            "canonicalizationVersion": candidate.canonicalization_version,
            "materializerVersion": MATERIALIZER_VERSION,
            "applicabilitySubtreeHash": subtree_hash,
            "semanticNodeHashes": sorted(row.identity_hash for row in semantic_rows),
            "evidenceLinkHashes": sorted(row.link_hash for row in evidence_rows),
        }
        projection_bytes = canonical_bytes(projection_envelope, CANONICALIZATION_VERSION_V2)
        projection = ADV4CandidateAppProjection(
            id=provisional_id, identity_hash=identity_hash, proposal_id=proposal_id,
            directive_id=directive_id, schema_version=candidate.schema_version,
            validator_version=candidate.validator_version,
            canonicalization_version=candidate.canonicalization_version,
            proposal_canonical_hash=candidate.canonical_hash,
            evidence_binding_hash=candidate.evidence_binding_hash,
            materializer_version=MATERIALIZER_VERSION,
            applicability_subtree_bytes=subtree_bytes,
            applicability_subtree_hash=subtree_hash,
            projection_canonical_bytes=projection_bytes,
            projection_hash=hashlib.sha256(PROJECTION_DOMAIN + projection_bytes).hexdigest(), gate="candidate_only",
            semantic_node_count=len(semantic_rows), datum_count=len(datum_rows),
            evidence_link_count=len(evidence_rows), identity_mapping_count=len(identity_rows),
        )
        db.add(projection)
        db.flush([projection])
        db.add_all(semantic_rows)
        db.flush(semantic_rows)
        db.add_all(
            datum_rows + identity_rows + source_scope_rows + rule_owner_rows
            + search_hint_owner_rows + evidence_rows
        )
        db.flush()
        stale_targets = _materialize_dependencies(db, projection, candidate, nodes)
        _materialize_corrections(db, projection, candidate, bindings, nodes)
    else:
        stale_targets = []

    claims = {"userId": actor.id, "membershipId": membership.id, "organizationId": membership.organization_id, "role": membership.role, "status": membership.status, "policy": POLICY_NAME, "version": POLICY_VERSION}
    request_id, _ = _row_id("avq", "materialization-request", {"scope": scope, "requestHash": request_hash})
    request = ADV4CandidateAppMaterializationRequest(
        id=request_id, projection_id=projection.id, proposal_id=proposal_id,
        directive_id=directive_id, actor_user_id=actor.id,
        authorizing_membership_id=membership.id, organization_id=membership.organization_id,
        actor_role=membership.role, actor_status=membership.status,
        auth_policy_name=POLICY_NAME, auth_policy_version=POLICY_VERSION,
        auth_claims_hash=hashlib.sha256(canonical_bytes(claims, CANONICALIZATION_VERSION_V2)).hexdigest(),
        endpoint_action=ENDPOINT_ACTION, idempotency_key=idempotency_key,
        request_canonical_bytes=request_bytes, request_hash=request_hash,
    )
    db.add(request)
    db.flush([request])
    if created:
        event_value = {"version": "ad-v4-applicability-event-v2", "eventType": "materialized", "projectionId": projection.id, "proposalId": proposal_id, "sequence": "0", "requestId": request.id, "predecessorEventHash": "none"}
        event_bytes = canonical_bytes(event_value, CANONICALIZATION_VERSION_V2)
        event_hash = hashlib.sha256(EVENT_DOMAIN + event_bytes).hexdigest()
        event_id, _ = _row_id("avz", "projection-event", {"projectionId": projection.id, "eventHash": event_hash})
        db.add(ADV4CandidateAppProjectionEvent(id=event_id, projection_id=projection.id, proposal_id=proposal_id, sequence_number=0, event_type="materialized", reason_code="explicit_admin_materialization", causing_request_id=request.id, causing_relationship_id=None, causing_lifecycle_event_id=None, causing_dependency_id=None, predecessor_event_hash=None, canonical_bytes=event_bytes, event_hash=event_hash, actor_kind="platform_admin"))
    db.flush()
    for target in stale_targets:
        _repair_stale_projection_on_materialization(db, target)
    reconstruct_applicability(db, projection)
    _repair_stale_projection_on_materialization(db, projection)
    return MaterializedApplicability(projection, request, created, False)


def _materialize_corrections(
    db: Session,
    projection: ADV4CandidateAppProjection,
    candidate: ADV4CandidateProposal,
    bindings: dict[str, ADV4CandidateEvidenceBinding],
    nodes: dict[str, ADV4CandidateAppSemanticNode],
) -> None:
    documents = {item["officialDocumentKey"]: item for item in candidate.parsed_json["officialDocuments"]}
    node_by_key = {(node.node_type, node.node_key): node for node in nodes.values()}
    owner = {
        "directiveIdentity": "foundation", "supersessionRelations": "foundation",
        "productScopes": "slice_3a", "conditionDefinitions": "slice_3a",
        "applicabilityRules": "slice_3a", "requirements": "slice_3b",
        "recurrenceGroups": "slice_3b", "amocAuthorityProvisions": "slice_3b",
    }
    type_by_namespace = {"productScopes": "product_scope", "conditionDefinitions": "condition", "applicabilityRules": "applicability_rule"}
    for ordinal, value in enumerate(candidate.parsed_json["authoritativeCorrections"]):
        root_id, root_hash = _row_id("avc", "correction", {"proposalId": candidate.id, "correctionKey": value["correctionKey"]})
        original = documents[value["originalDocumentRefKey"]]
        correcting = documents[value["correctingDocumentRefKey"]]
        root = ADV4CandidateCorrection(id=root_id, identity_hash=root_hash, proposal_id=candidate.id, correction_key=value["correctionKey"], correction_type=value["correctionType"], original_document_ref_key=value["originalDocumentRefKey"], correcting_document_ref_key=value["correctingDocumentRefKey"], original_document_identity_hash=_document_identity(original), correcting_document_identity_hash=_document_identity(correcting), canonical_hash=hashlib.sha256(canonical_bytes(value, CANONICALIZATION_VERSION_V2)).hexdigest(), canonical_ordinal=ordinal, foundation_version="paprnav-ad-v4-correction-foundation-1", generation=1, expected_ref_count=len(value["changedSemanticRefs"]), expected_evidence_count=len(value["evidenceKeys"]))
        db.add(root)
        db.flush([root])
        for ref_ordinal, ref in enumerate(value["changedSemanticRefs"]):
            ref_id, ref_hash = _row_id("avf", "correction-ref", {"correctionId": root.id, "namespace": ref["namespace"], "key": ref["key"]})
            ref_row = ADV4CandidateCorrectionRef(id=ref_id, correction_id=root.id, proposal_id=candidate.id, canonical_ordinal=ref_ordinal, namespace=ref["namespace"], semantic_key=ref["key"], owner_slice=owner[ref["namespace"]], reference_hash=ref_hash)
            db.add(ref_row)
            db.flush([ref_row])
            if ref["namespace"] in type_by_namespace:
                semantic = node_by_key.get((type_by_namespace[ref["namespace"]], ref["key"]))
                if semantic is None:
                    raise ADV4Error("projection_integrity", "", "Correction 3A reference does not resolve")
                binding_id, binding_hash = _row_id("avk", "correction-binding", {"refId": ref_id, "semanticId": semantic.id})
                db.add(ADV4CandidateCorrectionSemanticBinding(id=binding_id, correction_ref_id=ref_id, proposal_id=candidate.id, projection_id=projection.id, semantic_node_id=semantic.id, binding_slice="slice_3a", generation=1, binding_hash=binding_hash))
        for evidence_ordinal, evidence_key in enumerate(value["evidenceKeys"]):
            evidence_id, link_hash = _row_id("avh", "correction-evidence", {"correctionId": root.id, "evidenceKey": evidence_key})
            db.add(ADV4CandidateCorrectionEvidenceLink(id=evidence_id, correction_id=root.id, proposal_id=candidate.id, candidate_binding_id=bindings[evidence_key].id, evidence_key=evidence_key, canonical_ordinal=evidence_ordinal, link_hash=link_hash))


def _materialize_dependencies(
    db: Session,
    projection: ADV4CandidateAppProjection,
    candidate: ADV4CandidateProposal,
    nodes: dict[str, ADV4CandidateAppSemanticNode],
) -> list[ADV4CandidateAppProjection]:
    plans: list[tuple[dict[str, Any], ADV4CandidateAppSemanticNode, str, str, str, str | None, ADV4CandidateAppProjection | None]] = []
    stale_targets: dict[str, ADV4CandidateAppProjection] = {}
    canonical_ad = candidate.parsed_json["directiveIdentity"]["adNumber"]
    for ordinal, relation in enumerate(candidate.parsed_json["supersessionRelations"]):
        pointer = f"/supersessionRelations/{ordinal}"
        node = nodes[pointer]
        dependency_key = f"{relation['relationType']}:{relation['predecessorAdNumber']}"
        dependency_id, dependency_hash = _row_id("avj", "change-dependency", {
            "projectionId": projection.id,
            "dependencyKey": dependency_key,
            "predecessorAdNumber": relation["predecessorAdNumber"],
            "successorAdNumber": relation["successorAdNumber"],
        })
        target: ADV4CandidateAppProjection | None = None
        if canonical_ad.get("state") != "known":
            resolution_state = "unresolved"
            unresolved_reason = "successor_identity_unknown"
        elif relation["successorAdNumber"] != canonical_ad["value"]:
            resolution_state = "unresolved"
            unresolved_reason = "successor_not_this_proposal"
        else:
            matches: list[ADV4CandidateAppProjection] = []
            for possible in db.scalars(select(ADV4CandidateAppProjection).where(
                ADV4CandidateAppProjection.id != projection.id
            )).all():
                possible_candidate = verified_candidate(db, possible.proposal_id)
                possible_ad = possible_candidate.parsed_json["directiveIdentity"]["adNumber"]
                if possible_ad.get("state") == "known" and possible_ad.get("value") == relation["predecessorAdNumber"]:
                    matches.append(possible)
            if len(matches) == 1:
                target = matches[0]
                resolution_state = "resolved_candidate"
                unresolved_reason = None
            elif matches:
                resolution_state = "ambiguous"
                unresolved_reason = "multiple_predecessor_candidates"
            else:
                resolution_state = "unresolved"
                unresolved_reason = "target_candidate_not_resolved"
        plans.append((relation, node, dependency_id, dependency_hash, resolution_state, unresolved_reason, target))
        if target is not None:
            stale_targets[target.id] = target

    # Resolve first, then lock every affected predecessor root in lexical ID
    # order before appending any target-local cause or event.
    for target_id in sorted(stale_targets):
        locked = db.scalar(select(ADV4CandidateAppProjection).where(
            ADV4CandidateAppProjection.id == target_id
        ).with_for_update())
        if locked is None:
            raise ADV4Error("projection_integrity", "", "Resolved supersession target disappeared", http_status=409)
        stale_targets[target_id] = locked

    for relation, node, dependency_id, dependency_hash, resolution_state, unresolved_reason, target in plans:
        dependency_key = f"{relation['relationType']}:{relation['predecessorAdNumber']}"
        target = stale_targets.get(target.id) if target is not None else None
        outgoing = ADV4CandidateAppChangeDependency(
            id=dependency_id, projection_id=projection.id, proposal_id=candidate.id,
            semantic_node_id=node.id, dependency_key=dependency_key,
            dependency_kind=(
                "outgoing_supersedes" if relation["relationType"] == "supersedes"
                else "outgoing_partially_supersedes"
            ), predecessor_ad_number=relation["predecessorAdNumber"],
            successor_ad_number=relation["successorAdNumber"],
            resolution_state=resolution_state, unresolved_reason=unresolved_reason,
            target_projection_id=target.id if target is not None else None, source_dependency_id=None,
            dependency_hash=dependency_hash,
        )
        db.add(outgoing)
        db.flush([outgoing])
        if target is None:
            continue
        # The target-local signal and event are appended under deterministic
        # identities and the target projection lock. They carry no evidence
        # text; the immutable source dependency retains that evidence binding.
        incoming_pointer = f"/incomingSupersessionSignals/{outgoing.id}"
        incoming_key = f"incoming:{outgoing.id}"
        incoming_value = {
            "sourceDependencyId": outgoing.id,
            "targetProjectionId": target.id,
        }
        node_id, node_hash = _row_id("avn", "semantic-node", {
            "projectionId": target.id, "nodeType": "change_dependency",
            "nodeKey": incoming_key, "pointer": incoming_pointer,
        })
        incoming_node = ADV4CandidateAppSemanticNode(
            id=node_id, identity_hash=node_hash, projection_id=target.id,
            proposal_id=target.proposal_id, parent_node_id=None,
            node_type="change_dependency", node_key=incoming_key,
            source_pointer=incoming_pointer,
            canonical_node_hash=hashlib.sha256(
                canonical_bytes(incoming_value, CANONICALIZATION_VERSION_V2)
            ).hexdigest(), canonical_ordinal=0,
        )
        db.add(incoming_node)
        db.flush([incoming_node])
        incoming_id, incoming_hash = _row_id("avj", "incoming-change-dependency", {
            "projectionId": target.id, "sourceDependencyId": outgoing.id,
        })
        db.add(ADV4CandidateAppChangeDependency(
            id=incoming_id, projection_id=target.id, proposal_id=target.proposal_id,
            semantic_node_id=incoming_node.id, dependency_key=incoming_key,
            dependency_kind="incoming_supersession_signal",
            predecessor_ad_number=outgoing.predecessor_ad_number,
            successor_ad_number=outgoing.successor_ad_number,
            resolution_state="resolved_candidate", unresolved_reason=None,
            target_projection_id=target.id, source_dependency_id=outgoing.id,
            dependency_hash=incoming_hash,
        ))
    db.flush()
    return list(stale_targets.values())


def verified_app_projection(db: Session, *, directive_id: str, proposal_id: str) -> ADV4CandidateAppProjection:
    projection = db.scalar(select(ADV4CandidateAppProjection).where(
        ADV4CandidateAppProjection.proposal_id == proposal_id,
        ADV4CandidateAppProjection.directive_id == directive_id,
        ADV4CandidateAppProjection.materializer_version == MATERIALIZER_VERSION,
    ))
    if projection is None:
        raise ADV4Error("not_found", "", "Applicability projection not found", http_status=404)
    reconstruct_applicability(db, projection)
    return projection


def _detect_projection_state(
    db: Session,
    projection: ADV4CandidateAppProjection,
) -> tuple[str, list[str], str | None, str | None, str | None]:
    reasons: list[str] = []
    candidate = verified_candidate(db, projection.proposal_id)
    causing_lifecycle_event_id: str | None = None
    try:
        _verify_live_evidence(db, candidate)
    except ADV4Error:
        reasons.append("evidence_invalidated")
        binding = db.scalar(select(ADV4CandidateEvidenceBinding).where(
            ADV4CandidateEvidenceBinding.proposal_id == candidate.id
        ).order_by(ADV4CandidateEvidenceBinding.fragment_id))
        if binding is not None:
            causing = db.scalar(select(ADEvidenceFragmentLifecycleEvent).where(
                ADEvidenceFragmentLifecycleEvent.fragment_id == binding.fragment_id,
                ADEvidenceFragmentLifecycleEvent.id != binding.admitted_event_id,
            ).order_by(ADEvidenceFragmentLifecycleEvent.sequence_number.desc()))
            causing_lifecycle_event_id = causing.id if causing is not None else None
    relation = db.scalar(select(ADV4CandidateSubmissionRelationship).where(
        ADV4CandidateSubmissionRelationship.predecessor_proposal_id == projection.proposal_id
    ).order_by(ADV4CandidateSubmissionRelationship.created_at, ADV4CandidateSubmissionRelationship.id))
    if relation is not None:
        reasons.append("candidate_corrected_or_replaced")
    dependency = db.scalar(select(ADV4CandidateAppChangeDependency).where(
        ADV4CandidateAppChangeDependency.projection_id == projection.id,
        ADV4CandidateAppChangeDependency.dependency_kind == "incoming_supersession_signal",
        ADV4CandidateAppChangeDependency.resolution_state == "resolved_candidate",
    ).order_by(ADV4CandidateAppChangeDependency.id))
    if dependency is not None:
        reasons.append("candidate_supersession_signal")
    return (
        "candidate_stale" if reasons else "candidate_verified",
        reasons,
        relation.id if relation is not None else None,
        causing_lifecycle_event_id,
        dependency.id if dependency is not None else None,
    )


def projection_state(db: Session, projection: ADV4CandidateAppProjection) -> tuple[str, list[str]]:
    """Detect current derived state without mutating rows or appending events."""
    state, reasons, _, _, _ = _detect_projection_state(db, projection)
    return state, reasons


def _repair_stale_projection_on_materialization(
    db: Session,
    projection: ADV4CandidateAppProjection,
) -> None:
    """Append deterministic repair only inside the authorized materialization POST."""
    _, reasons, relationship_id, lifecycle_event_id, dependency_id = _detect_projection_state(db, projection)
    if not reasons:
        return
    _repair_stale_projection(
        db,
        projection,
        reasons,
        causing_relationship_id=relationship_id,
        causing_lifecycle_event_id=lifecycle_event_id,
        causing_dependency_id=dependency_id,
    )


def _repair_stale_projection(
    db: Session,
    projection: ADV4CandidateAppProjection,
    reasons: list[str],
    *,
    causing_relationship_id: str | None,
    causing_lifecycle_event_id: str | None,
    causing_dependency_id: str | None,
) -> None:
    db.scalar(select(ADV4CandidateAppProjection).where(
        ADV4CandidateAppProjection.id == projection.id
    ).with_for_update())
    prior = db.scalar(select(ADV4CandidateAppProjectionEvent).where(
        ADV4CandidateAppProjectionEvent.projection_id == projection.id,
        ADV4CandidateAppProjectionEvent.event_type == "stale_marked",
    ))
    if prior is not None:
        return
    last = db.scalar(select(ADV4CandidateAppProjectionEvent).where(
        ADV4CandidateAppProjectionEvent.projection_id == projection.id
    ).order_by(ADV4CandidateAppProjectionEvent.sequence_number.desc()).limit(1))
    if last is None:
        raise ADV4Error("projection_integrity", "", "Projection event root is missing", http_status=409)
    sequence = last.sequence_number + 1
    event_value = {
        "version": "ad-v4-applicability-event-v2", "eventType": "stale_marked",
        "projectionId": projection.id, "proposalId": projection.proposal_id,
        "sequence": str(sequence), "reasons": sorted(reasons),
        "cause": {
            "kind": (
                "candidate_relationship" if causing_relationship_id is not None
                else "supersession_dependency" if causing_dependency_id is not None
                else "evidence_lifecycle"
            ),
            "id": causing_relationship_id or causing_dependency_id or causing_lifecycle_event_id,
        },
        "predecessorEventHash": last.event_hash,
    }
    event_bytes = canonical_bytes(event_value, CANONICALIZATION_VERSION_V2)
    event_hash = hashlib.sha256(EVENT_DOMAIN + event_bytes).hexdigest()
    event_id, _ = _row_id("avz", "projection-event", {
        "projectionId": projection.id, "eventHash": event_hash,
    })
    db.add(ADV4CandidateAppProjectionEvent(
        id=event_id, projection_id=projection.id, proposal_id=projection.proposal_id,
        sequence_number=sequence, event_type="stale_marked",
        reason_code="multiple" if len(reasons) > 1 else reasons[0],
        causing_request_id=None,
        causing_relationship_id=causing_relationship_id,
        causing_lifecycle_event_id=(
            None if causing_relationship_id is not None or causing_dependency_id is not None
            else causing_lifecycle_event_id
        ),
        causing_dependency_id=(
            causing_dependency_id if causing_relationship_id is None else None
        ), predecessor_event_hash=last.event_hash,
        canonical_bytes=event_bytes, event_hash=event_hash, actor_kind="system_repair",
    ))
    db.flush()
