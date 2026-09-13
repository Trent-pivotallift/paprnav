from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from types import MappingProxyType
from typing import Any, Mapping, Sequence

from app.services.ad_v4_candidates import CANONICALIZATION_VERSION_V2, canonical_bytes
from app.services.ad_v4_graph import first_cycle_node
from app.services.ad_v4_obligation_mapping_v1 import (
    CORRECTION_COMPATIBILITY,
    DOMAINS,
    GLOBAL_ALGORITHMS,
    MAPPING_DIGEST,
    MAPPING_VERSION,
    OCCURRENCES,
    OWNER_CONTRACTS,
    RESOURCE_LIMITS,
    RELATIONSHIPS,
    ROOT_FIELDS,
    STRUCTURAL_COUNTS,
    select_occurrences,
)


MATERIALIZER_VERSION = "paprnav-ad-v4-obligation-materializer-1"
APP_MATERIALIZER_VERSION = "paprnav-ad-v4-app-materializer-2"


@dataclass(frozen=True)
class ObligationSemanticNode:
    id: str
    identity_hash: str
    proposal_id: str
    projection_id: str
    parent_node_id: str | None
    node_type: str
    node_key: str
    source_pointer: str
    canonical_node_hash: str
    canonical_ordinal: int


@dataclass(frozen=True)
class ObligationEvidenceLink:
    id: str
    projection_id: str
    proposal_id: str
    semantic_node_id: str
    candidate_binding_id: str
    evidence_key: str
    purpose: str
    canonical_ordinal: int
    link_hash: str


@dataclass(frozen=True)
class ObligationDocumentOwner:
    semantic_node_id: str
    proposal_id: str
    projection_id: str
    document_ref_key: str
    document_type: str
    canonical_ordinal: int
    document_number_node_id: str
    revision_node_id: str
    retention_node_id: str


@dataclass(frozen=True)
class ObligationValueAssertionOwner:
    semantic_node_id: str
    proposal_id: str
    projection_id: str
    field_code: str
    state: str
    value: str | None
    reason: str | None
    temporal_kind: str | None


@dataclass(frozen=True)
class ObligationDocumentFamily:
    proposal_id: str
    projection_id: str
    semantic_nodes: tuple[ObligationSemanticNode, ...]
    evidence_links: tuple[ObligationEvidenceLink, ...]
    documents: tuple[ObligationDocumentOwner, ...]
    value_assertions: tuple[ObligationValueAssertionOwner, ...]


@dataclass(frozen=True)
class ObligationRequirementOwner:
    semantic_node_id: str
    proposal_id: str
    projection_id: str
    requirement_key: str
    sequence_text: str
    sequence_value: int
    requirement_type: str
    canonical_ordinal: int
    recurrence_group_present: bool
    recurrence_group_key: str | None
    action_node_id: str
    activation_root_node_id: str
    branch_node_id: str
    initial_timing_node_id: str
    recurrence_node_id: str
    terminating_effect_node_id: str


@dataclass(frozen=True)
class ObligationActionOwner:
    semantic_node_id: str
    proposal_id: str
    projection_id: str
    requirement_node_id: str
    action_type: str
    ordered_steps_present: bool
    step_count: int
    document_ref_count: int


@dataclass(frozen=True)
class ObligationActionStepOwner:
    semantic_node_id: str
    proposal_id: str
    projection_id: str
    action_node_id: str
    step_text: str
    canonical_ordinal: int


@dataclass(frozen=True)
class ObligationBranchOwner:
    semantic_node_id: str
    proposal_id: str
    projection_id: str
    requirement_node_id: str
    kind: str
    alternative_group_key: str | None
    exclusive: bool | None
    condition_root_node_id: str | None


@dataclass(frozen=True)
class ObligationActionDocumentRef:
    id: str
    identity_hash: str
    proposal_id: str
    projection_id: str
    action_node_id: str
    document_node_id: str
    document_ref_key: str
    canonical_ordinal: int


@dataclass(frozen=True)
class ObligationRequirementFamily:
    proposal_id: str
    projection_id: str
    semantic_nodes: tuple[ObligationSemanticNode, ...]
    evidence_links: tuple[ObligationEvidenceLink, ...]
    requirements: tuple[ObligationRequirementOwner, ...]
    actions: tuple[ObligationActionOwner, ...]
    action_steps: tuple[ObligationActionStepOwner, ...]
    branches: tuple[ObligationBranchOwner, ...]
    action_document_refs: tuple[ObligationActionDocumentRef, ...]


@dataclass(frozen=True)
class ObligationApplicabilityTarget:
    id: str
    identity_hash: str
    proposal_id: str
    projection_id: str
    node_type: str
    node_key: str
    source_pointer: str
    canonical_node_bytes: bytes
    canonical_node_hash: str


@dataclass(frozen=True)
class ObligationExpressionOwner:
    semantic_node_id: str
    proposal_id: str
    projection_id: str
    requirement_node_id: str
    context: str
    expression_path: str
    node_type: str
    required_state: str | None
    app_target_projection_id: str | None
    app_target_node_id: str | None
    requirement_target_node_id: str | None


@dataclass(frozen=True)
class ObligationExpressionEdge:
    id: str
    identity_hash: str
    proposal_id: str
    projection_id: str
    requirement_node_id: str
    context: str
    parent_expression_id: str
    child_expression_id: str
    canonical_ordinal: int


@dataclass(frozen=True)
class ObligationExpressionFamily:
    proposal_id: str
    projection_id: str
    app_projection_id: str
    semantic_nodes: tuple[ObligationSemanticNode, ...]
    expressions: tuple[ObligationExpressionOwner, ...]
    edges: tuple[ObligationExpressionEdge, ...]


@dataclass(frozen=True)
class ObligationTimingGroupOwner:
    semantic_node_id: str
    proposal_id: str
    projection_id: str
    owner_kind: str
    owner_node_id: str
    state: str
    logic: str | None
    reason: str | None
    temporal_kind: str | None
    canonical_ordinal: int
    term_count: int


@dataclass(frozen=True)
class ObligationTimingTermOwner:
    semantic_node_id: str
    proposal_id: str
    projection_id: str
    timing_group_node_id: str
    metric: str
    interval_text: str
    interval_numeric: Decimal
    unit: str
    comparator: str
    anchor: str
    canonical_ordinal: int


@dataclass(frozen=True)
class ObligationRecurrenceOwner:
    semantic_node_id: str
    proposal_id: str
    projection_id: str
    requirement_node_id: str
    kind: str
    timing_node_id: str | None
    condition_root_node_id: str | None
    reason: str | None
    temporal_kind: str | None


@dataclass(frozen=True)
class ObligationTimingRecurrenceFamily:
    proposal_id: str
    projection_id: str
    semantic_nodes: tuple[ObligationSemanticNode, ...]
    evidence_links: tuple[ObligationEvidenceLink, ...]
    timing_groups: tuple[ObligationTimingGroupOwner, ...]
    timing_terms: tuple[ObligationTimingTermOwner, ...]
    recurrences: tuple[ObligationRecurrenceOwner, ...]


@dataclass(frozen=True)
class ObligationTerminatingEffectOwner:
    semantic_node_id: str
    proposal_id: str
    projection_id: str
    requirement_node_id: str
    kind: str
    edge_count: int


@dataclass(frozen=True)
class ObligationTerminationEdge:
    id: str
    identity_hash: str
    proposal_id: str
    projection_id: str
    effect_node_id: str
    terminated_requirement_node_id: str
    terminated_requirement_key: str
    canonical_ordinal: int


@dataclass(frozen=True)
class ObligationRequirementDependency:
    id: str
    identity_hash: str
    proposal_id: str
    projection_id: str
    requirement_node_id: str
    prerequisite_requirement_node_id: str
    prerequisite_requirement_key: str
    dependency_kind: str
    canonical_ordinal: int


@dataclass(frozen=True)
class ObligationRequirementRelationshipFamily:
    proposal_id: str
    projection_id: str
    semantic_nodes: tuple[ObligationSemanticNode, ...]
    evidence_links: tuple[ObligationEvidenceLink, ...]
    terminating_effects: tuple[ObligationTerminatingEffectOwner, ...]
    termination_edges: tuple[ObligationTerminationEdge, ...]
    requirement_dependencies: tuple[ObligationRequirementDependency, ...]


@dataclass(frozen=True)
class ObligationRecurrenceGroupOwner:
    semantic_node_id: str
    proposal_id: str
    projection_id: str
    recurrence_group_key: str
    canonical_ordinal: int
    completion_policy: str
    initial_timing_node_id: str
    recurring_timing_node_id: str
    member_count: int


@dataclass(frozen=True)
class ObligationRecurrenceGroupMember:
    id: str
    identity_hash: str
    proposal_id: str
    projection_id: str
    group_node_id: str
    requirement_node_id: str
    requirement_key: str
    canonical_ordinal: int


@dataclass(frozen=True)
class ObligationRecurrenceGroupFamily:
    proposal_id: str
    projection_id: str
    semantic_nodes: tuple[ObligationSemanticNode, ...]
    evidence_links: tuple[ObligationEvidenceLink, ...]
    recurrence_groups: tuple[ObligationRecurrenceGroupOwner, ...]
    members: tuple[ObligationRecurrenceGroupMember, ...]
    timing_groups: tuple[ObligationTimingGroupOwner, ...]
    timing_terms: tuple[ObligationTimingTermOwner, ...]


@dataclass(frozen=True)
class ObligationAmocProvisionOwner:
    semantic_node_id: str
    proposal_id: str
    projection_id: str
    provision_key: str
    canonical_ordinal: int
    authority_assertion_node_id: str


@dataclass(frozen=True)
class ObligationAuthorityFamily:
    proposal_id: str
    projection_id: str
    semantic_nodes: tuple[ObligationSemanticNode, ...]
    evidence_links: tuple[ObligationEvidenceLink, ...]
    amoc_provisions: tuple[ObligationAmocProvisionOwner, ...]
    value_assertions: tuple[ObligationValueAssertionOwner, ...]


@dataclass(frozen=True)
class ObligationCorrectionReference:
    id: str
    correction_id: str
    proposal_id: str
    canonical_ordinal: int
    namespace: str
    semantic_key: str
    owner_slice: str
    reference_hash: str


@dataclass(frozen=True)
class ObligationCorrectionSemanticBinding:
    id: str
    correction_ref_id: str
    proposal_id: str
    projection_id: str | None
    semantic_node_id: str | None
    obligation_projection_id: str | None
    obligation_semantic_node_id: str | None
    binding_slice: str
    generation: int
    binding_hash: str


@dataclass(frozen=True)
class ObligationCorrectionBindingFamily:
    proposal_id: str
    projection_id: str
    bindings: tuple[ObligationCorrectionSemanticBinding, ...]
    binding_set_bytes: bytes
    binding_set_hash: str


@dataclass(frozen=True)
class ObligationDatum:
    id: str
    identity_hash: str
    proposal_id: str
    projection_id: str
    semantic_node_id: str | None
    json_pointer: str
    parent_pointer: str | None
    property_name: str | None
    array_ordinal: int | None
    value_kind: str
    string_value: str | None
    boolean_value: bool | None
    value_hash: str


@dataclass(frozen=True)
class ObligationProjection:
    id: str
    identity_hash: str
    proposal_id: str
    directive_id: str
    validator_version: str
    canonicalization_version: str
    proposal_canonical_hash: str
    evidence_binding_hash: str
    app_projection_id: str
    app_projection_hash: str
    app_materializer_version: str
    materializer_version: str
    mapping_version: str
    mapping_digest: str
    obligation_subtree_bytes: bytes
    obligation_subtree_hash: str
    projection_canonical_bytes: bytes
    projection_hash: str
    gate: str
    counts: Mapping[str, int]


@dataclass(frozen=True)
class ObligationProjectionGraph:
    projection: ObligationProjection
    datums: tuple[ObligationDatum, ...]
    semantic_nodes: tuple[ObligationSemanticNode, ...]
    evidence_links: tuple[ObligationEvidenceLink, ...]
    document_family: ObligationDocumentFamily
    requirement_family: ObligationRequirementFamily
    expression_family: ObligationExpressionFamily
    timing_recurrence_family: ObligationTimingRecurrenceFamily
    requirement_relationship_family: ObligationRequirementRelationshipFamily
    recurrence_group_family: ObligationRecurrenceGroupFamily
    authority_family: ObligationAuthorityFamily
    correction_binding_family: ObligationCorrectionBindingFamily


class ObligationIntegrityError(ValueError):
    """A canonical obligation family and its exact typed projection disagree."""


_DOCUMENT_TYPES = frozenset({
    "service_bulletin",
    "service_letter",
    "service_instruction",
    "maintenance_manual",
    "approved_data",
    "other_reviewed",
})
_ASSERTION_STATES = frozenset({"known", "unknown", "not_applicable"})
_UNKNOWN_REASONS = frozenset({
    "not_observed",
    "unavailable",
    "not_obtained",
    "not_extracted",
    "not_yet_reviewed",
    "not_yet_verified",
    "conflicting_evidence",
    "source_ambiguous",
    "unsupported_expression",
})
_TEMPORAL_KINDS = frozenset({
    "directive_version",
    "publication_version",
    "at_applicability_evaluation",
    "at_compliance_evaluation",
    "source_observation",
})
_D_DESCRIPTORS = {
    descriptor["id"]: descriptor
    for descriptor in OCCURRENCES
    if descriptor["id"] in {"D1", "D2", "D3", "D4"}
}
_DOCUMENT_DESCRIPTOR = _D_DESCRIPTORS["D1"]
_OWNER_CONTRACT_BY_TYPE = {contract["nodeType"]: contract for contract in OWNER_CONTRACTS}
_DOCUMENT_OWNER_CONTRACT = _OWNER_CONTRACT_BY_TYPE["incorporated_document"]
_ASSERTION_OWNER_CONTRACT = _OWNER_CONTRACT_BY_TYPE["value_assertion"]
_ASSERTION_DESCRIPTORS = tuple(
    sorted(
        (_D_DESCRIPTORS[descriptor_id] for descriptor_id in ("D2", "D3", "D4")),
        key=lambda descriptor: descriptor["ordinal"]["value"],
    )
)
_STABLE_KEY_RE = re.compile(r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$")
_REQUIREMENT_TYPES = frozenset({
    "inspection", "replacement", "modification", "software_update",
    "limitation", "reporting", "installation_prohibition",
    "corrective_action", "other_reviewed",
})
_ACTION_TYPES = frozenset({
    "inspect", "replace", "repair", "modify", "software_update",
    "revise_limitation", "report", "installation_prohibition", "remove",
    "rework", "other_reviewed",
})
_Q_DESCRIPTOR_IDS = frozenset({
    "Q1", "Q2", "Q3", "Q5", "EACT", "EBR", "EREC", "T1", "T5I",
    "R1", "R6", "T5R", "Q7",
})
_Q_DESCRIPTORS = {
    descriptor["id"]: descriptor
    for descriptor in OCCURRENCES
    if descriptor["id"] in _Q_DESCRIPTOR_IDS
}
_ACTION_DOCUMENT_RELATIONSHIP = next(
    relationship for relationship in RELATIONSHIPS if relationship["id"] == "Q4"
)
_EXPRESSION_OWNER_CONTRACT = _OWNER_CONTRACT_BY_TYPE["expression"]
_EXPRESSION_EDGE_RELATIONSHIP = next(
    relationship for relationship in RELATIONSHIPS if relationship["id"] == "EEDGE"
)
_TIMING_OWNER_CONTRACT = _OWNER_CONTRACT_BY_TYPE["timing_group"]
_TIMING_TERM_OWNER_CONTRACT = _OWNER_CONTRACT_BY_TYPE["timing_term"]
_RECURRENCE_OWNER_CONTRACT = _OWNER_CONTRACT_BY_TYPE["recurrence"]
_TERMINATING_EFFECT_OWNER_CONTRACT = _OWNER_CONTRACT_BY_TYPE["terminating_effect"]
_TERMINATION_EDGE_RELATIONSHIP = next(
    relationship for relationship in RELATIONSHIPS if relationship["id"] == "Q9"
)
_REQUIREMENT_DEPENDENCY_RELATIONSHIP = next(
    relationship for relationship in RELATIONSHIPS if relationship["id"] == "Q10"
)
_G_DESCRIPTOR_IDS = frozenset({"G1", "G3", "T5GI", "G4", "T5GR"})
_G_DESCRIPTORS = {
    descriptor["id"]: descriptor
    for descriptor in OCCURRENCES if descriptor["id"] in _G_DESCRIPTOR_IDS
}
_RECURRENCE_GROUP_OWNER_CONTRACT = _OWNER_CONTRACT_BY_TYPE["recurrence_group"]
_RECURRENCE_GROUP_MEMBER_RELATIONSHIP = next(
    relationship for relationship in RELATIONSHIPS if relationship["id"] == "G2"
)
_A_DESCRIPTOR_IDS = frozenset({"A1", "A2"})
_A_DESCRIPTORS = {
    descriptor["id"]: descriptor
    for descriptor in OCCURRENCES if descriptor["id"] in _A_DESCRIPTOR_IDS
}
_AMOC_PROVISION_OWNER_CONTRACT = _OWNER_CONTRACT_BY_TYPE["amoc_provision"]
_CORRECTION_BINDING_RELATIONSHIP = next(
    relationship for relationship in RELATIONSHIPS if relationship["id"] == "CB"
)
_CORRECTION_OWNER_BY_NAMESPACE = {
    row["namespace"]: row["ownerSlice"]
    for row in CORRECTION_COMPATIBILITY["namespaces"]
}
_CORRECTION_TARGET_TYPE_BY_NAMESPACE = {
    row["namespace"]: row["targetNodeType"]
    for row in CORRECTION_COMPATIBILITY["namespaces"]
    if row["targetNodeType"] is not None
}
_CORRECTION_IDENTITY_DOMAIN_KEYS = CORRECTION_COMPATIBILITY[
    "identityDomainKeys"
]
_APP_ROW_DOMAIN = DOMAINS[
    _CORRECTION_IDENTITY_DOMAIN_KEYS["correctionReference"]
]
_Q_OWNED_DESCRIPTOR_IDS = ("Q1", "Q2", "Q3", "Q5")


def _is_stable_key(value: Any) -> bool:
    return (
        isinstance(value, str)
        and 3 <= len(value) <= 128
        and _STABLE_KEY_RE.fullmatch(value) is not None
    )


def _validate_requirement_mapping_contract() -> None:
    expected_presence = {"Q1": "required", "Q2": "required", "Q3": "optional", "Q5": "required"}
    for descriptor_id in _Q_OWNED_DESCRIPTOR_IDS:
        descriptor = _Q_DESCRIPTORS[descriptor_id]
        contract = _OWNER_CONTRACT_BY_TYPE[descriptor["nodeType"]]
        if (
            descriptor["presence"] != expected_presence[descriptor_id]
            or descriptor["ownerTable"] != contract["table"]
        ):
            raise ObligationIntegrityError("requirement owner mapping differs")
    expected_relationship = {
        "table": "ad_v4_candidate_obligation_action_document_refs",
        "tableLabel": "action-document-ref", "idPrefix": "aor",
        "identityProperties": (
            "projectionId", "actionNodeId", "documentNodeId", "ordinal",
        ),
        "ordering": "canonical_ordinal", "cardinality": "zero_or_more",
    }
    if any(
        _ACTION_DOCUMENT_RELATIONSHIP[key] != value
        for key, value in expected_relationship.items()
    ):
        raise ObligationIntegrityError("action document relationship contract differs")
    expected_children = {
        "requirement": {
            ("Q2", "exactly_one", "fixed_slot"),
            ("EACT", "exactly_one", "fixed_slot"),
            ("Q5", "exactly_one", "fixed_slot"),
            ("T1", "exactly_one", "fixed_slot"),
            ("R1", "exactly_one", "fixed_slot"),
            ("Q7", "exactly_one", "fixed_slot"),
            ("Q10", "zero_or_more", "canonical_ordinal"),
        },
        "action": {
            ("Q3", "zero_or_more", "canonical_ordinal"),
            ("Q4", "zero_or_more", "canonical_ordinal"),
        },
        "action_step": set(),
        "branch": {("EBR", "branch_defined", "fixed_slot")},
    }
    for node_type, expected in expected_children.items():
        actual = {
            (child["target"], child["cardinality"], child["ordering"])
            for child in _OWNER_CONTRACT_BY_TYPE[node_type]["children"]
        }
        if actual != expected:
            raise ObligationIntegrityError("requirement child contract differs")
    expected_references = {
        "requirement": {
            ("action_node_id", "Q2", "action", "required_one"),
            ("activation_root_node_id", "EACT", "expression", "required_one"),
            ("branch_node_id", "Q5", "branch", "required_one"),
            ("initial_timing_node_id", "T1", "timing_group", "required_one"),
            ("recurrence_node_id", "R1", "recurrence", "required_one"),
            ("terminating_effect_node_id", "Q7", "terminating_effect", "required_one"),
            ("recurrence_group_key", "G1", "recurrence_group", "optional_one"),
        },
        "action": {("requirement_node_id", "Q1", "requirement", "required_one")},
        "action_step": {("action_node_id", "Q2", "action", "required_one")},
        "branch": {
            ("requirement_node_id", "Q1", "requirement", "required_one"),
            ("condition_root_node_id", "EBR", "expression", "optional_one"),
        },
    }
    for node_type, expected in expected_references.items():
        actual = {
            (
                reference["column"], reference["target"],
                reference["targetNodeType"], reference["cardinality"],
            )
            for reference in _OWNER_CONTRACT_BY_TYPE[node_type]["references"]
            if reference["scope"] == "same_projection"
        }
        if actual != expected:
            raise ObligationIntegrityError("requirement reference contract differs")


def _hash(domain: bytes, value: Any) -> str:
    return hashlib.sha256(domain + obligation_record_bytes(value)).hexdigest()


def _utf16_sort_key(value: str) -> bytes:
    if "\x00" in value:
        raise ObligationIntegrityError(
            "internal canonical string contains unsupported U+0000"
        )
    try:
        return value.encode("utf-16-be", "strict")
    except UnicodeEncodeError as exc:
        raise ObligationIntegrityError(
            "internal canonical string is not a Unicode scalar sequence"
        ) from exc


def _normalize_record(
    value: Any,
    *,
    depth: int = 0,
    active_containers: set[int] | None = None,
) -> Any:
    if depth > RESOURCE_LIMITS["maxDepth"]:
        raise ObligationIntegrityError("internal canonical nesting depth exceeded")
    if active_containers is None:
        active_containers = set()
    if value is None or type(value) is bool:
        return value
    if type(value) is str:
        if "\x00" in value:
            raise ObligationIntegrityError(
                "internal canonical string contains unsupported U+0000"
            )
        try:
            value.encode("utf-8", "strict")
        except UnicodeEncodeError as exc:
            raise ObligationIntegrityError(
                "internal canonical string is not a Unicode scalar sequence"
            ) from exc
        return value
    if type(value) is int:
        if value < 0:
            raise ObligationIntegrityError("internal canonical integers must be nonnegative")
        if value > RESOURCE_LIMITS["maxInternalInteger"]:
            raise ObligationIntegrityError("internal canonical integer exceeds storage limit")
        return value
    if type(value) not in {dict, list}:
        raise ObligationIntegrityError(
            f"unsupported internal canonical value {type(value).__name__}"
        )
    identity = id(value)
    if identity in active_containers:
        raise ObligationIntegrityError("internal canonical container cycle detected")
    active_containers.add(identity)
    try:
        if type(value) is dict:
            if any(type(key) is not str for key in value):
                raise ObligationIntegrityError("internal canonical object keys must be strings")
            for key in value:
                _utf16_sort_key(key)
            return {
                key: _normalize_record(
                    value[key],
                    depth=depth + 1,
                    active_containers=active_containers,
                )
                for key in sorted(value, key=_utf16_sort_key)
            }
        return [
            _normalize_record(
                child,
                depth=depth + 1,
                active_containers=active_containers,
            )
            for child in value
        ]
    finally:
        active_containers.remove(identity)


def obligation_record_bytes(value: Any) -> bytes:
    """Canonicalize closed internal records; source c14n-2 remains number-free."""
    return json.dumps(
        _normalize_record(value),
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
    ).encode("utf-8")


def _validate_source_resources(value: Any) -> None:
    max_array_items = RESOURCE_LIMITS["maxArrayItems"]
    max_total_nodes = RESOURCE_LIMITS["maxTotalNodes"]
    max_depth = RESOURCE_LIMITS["maxDepth"]
    max_string_length = RESOURCE_LIMITS["maxStringLength"]
    total = 0
    stack: list[tuple[Any, int]] = [(value, 0)]
    while stack:
        current, depth = stack.pop()
        total += 1
        if total > max_total_nodes:
            raise ObligationIntegrityError("incorporated document node limit exceeded")
        if depth > max_depth:
            raise ObligationIntegrityError("incorporated document depth limit exceeded")
        if isinstance(current, str):
            if len(current) > max_string_length:
                raise ObligationIntegrityError("incorporated document string limit exceeded")
            if "\x00" in current:
                raise ObligationIntegrityError(
                    "incorporated document contains unsupported U+0000"
                )
            if any(0xD800 <= ord(char) <= 0xDFFF for char in current):
                raise ObligationIntegrityError("incorporated document unicode scalar is invalid")
            if unicodedata.normalize("NFC", current) != current:
                raise ObligationIntegrityError("incorporated document string is not NFC")
        elif isinstance(current, Mapping):
            for key, child in current.items():
                stack.append((key, depth + 1))
                stack.append((child, depth + 1))
        elif isinstance(current, list):
            if len(current) > max_array_items:
                raise ObligationIntegrityError("incorporated document array limit exceeded")
            stack.extend((child, depth + 1) for child in current)
        elif current is None or (
            isinstance(current, (int, float)) and not isinstance(current, bool)
        ):
            raise ObligationIntegrityError("incorporated document source value is forbidden")
        elif not isinstance(current, bool):
            raise ObligationIntegrityError("incorporated document source type is invalid")


def _canonical_document_source(
    canonical_documents: Sequence[Mapping[str, Any]],
) -> tuple[dict[str, Any], tuple[Any, ...]]:
    if not isinstance(canonical_documents, list):
        raise ObligationIntegrityError("incorporated document collection is invalid")
    source = {
        "incorporatedDocuments": list(canonical_documents),
        "requirements": [],
        "recurrenceGroups": [],
        "amocAuthorityProvisions": [],
    }
    _validate_source_resources(source)
    canonical_source = json.loads(
        canonical_bytes(source, CANONICALIZATION_VERSION_V2)
    )
    selected = tuple(
        occurrence
        for occurrence in select_occurrences(canonical_source)
        if occurrence.descriptor_id in _D_DESCRIPTORS
    )
    return canonical_source, selected


def _row_id(prefix: str, table: str, identity: Mapping[str, Any]) -> tuple[str, str]:
    row_hash = _hash(DOMAINS["row"], {"table": table, "identity": identity})
    return f"{prefix}_{row_hash[:32]}", row_hash


def _app_row_id(prefix: str, table: str, identity: Mapping[str, Any]) -> tuple[str, str]:
    row_hash = hashlib.sha256(
        _APP_ROW_DOMAIN
        + canonical_bytes({"table": table, "identity": identity}, CANONICALIZATION_VERSION_V2)
    ).hexdigest()
    return f"{prefix}_{row_hash[:32]}", row_hash


def _plain_hash(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value, CANONICALIZATION_VERSION_V2)).hexdigest()


def _node(
    *,
    proposal_id: str,
    projection_id: str,
    parent_node_id: str | None,
    node_type: str,
    node_key: str,
    source_pointer: str,
    canonical_value: Any,
    canonical_ordinal: int,
) -> ObligationSemanticNode:
    identity = {
        "projectionId": projection_id,
        "nodeType": node_type,
        "nodeKey": node_key,
        "pointer": source_pointer,
    }
    node_id, identity_hash = _row_id("aon", "semantic-node", identity)
    return ObligationSemanticNode(
        id=node_id,
        identity_hash=identity_hash,
        proposal_id=proposal_id,
        projection_id=projection_id,
        parent_node_id=parent_node_id,
        node_type=node_type,
        node_key=node_key,
        source_pointer=source_pointer,
        canonical_node_hash=_plain_hash(canonical_value),
        canonical_ordinal=canonical_ordinal,
    )


def _evidence_links(
    *,
    proposal_id: str,
    projection_id: str,
    semantic_node_id: str,
    evidence_keys: Sequence[str],
    evidence_policy: Mapping[str, Any],
    evidence_bindings: Mapping[str, str],
) -> tuple[ObligationEvidenceLink, ...]:
    if not isinstance(evidence_bindings, Mapping):
        raise ObligationIntegrityError("evidence binding map is invalid")
    if (
        not isinstance(evidence_keys, list)
        or not evidence_keys
        or any(not _is_stable_key(key) for key in evidence_keys)
        or len(evidence_keys) != len(set(evidence_keys))
    ):
        raise ObligationIntegrityError("semantic evidence set is invalid")
    if (
        evidence_policy.get("source") != "own"
        or evidence_policy.get("cardinality") != "one_or_more"
        or evidence_policy.get("inheritance") != "none"
        or not isinstance(evidence_policy.get("purpose"), str)
    ):
        raise ObligationIntegrityError("unsupported document evidence policy")
    purpose = evidence_policy["purpose"]
    links: list[ObligationEvidenceLink] = []
    for ordinal, evidence_key in enumerate(evidence_keys):
        binding_id = evidence_bindings.get(evidence_key)
        if binding_id is None:
            raise ObligationIntegrityError(f"missing evidence binding {evidence_key!r}")
        if type(binding_id) is not str:
            raise ObligationIntegrityError(
                f"evidence binding target for {evidence_key!r} is invalid"
            )
        identity = {
            "projectionId": projection_id,
            "semanticNodeId": semantic_node_id,
            "purpose": purpose,
            "evidenceKey": evidence_key,
            "ordinal": ordinal,
        }
        link_id, link_hash = _row_id("aoe", "evidence-link", identity)
        links.append(ObligationEvidenceLink(
            id=link_id,
            projection_id=projection_id,
            proposal_id=proposal_id,
            semantic_node_id=semantic_node_id,
            candidate_binding_id=binding_id,
            evidence_key=evidence_key,
            purpose=purpose,
            canonical_ordinal=ordinal,
            link_hash=link_hash,
        ))
    if not links:
        raise ObligationIntegrityError("semantic evidence sets must be non-empty")
    return tuple(links)


def _assertion_owner(
    *,
    node: ObligationSemanticNode,
    descriptor: Mapping[str, Any],
    value: Mapping[str, Any],
) -> ObligationValueAssertionOwner:
    if type(value) is not dict:
        raise ObligationIntegrityError("value assertion source object differs")
    field_code = descriptor["ownerKind"]
    state = value.get("state")
    allowed_states = tuple(descriptor.get("allowedUnionBranches", _ASSERTION_STATES))
    if (
        not isinstance(state, str)
        or state not in _ASSERTION_STATES
        or state not in allowed_states
    ):
        raise ObligationIntegrityError(f"invalid {field_code} assertion state {state!r}")
    if state == "known":
        known_value = value.get("value")
        if (
            not isinstance(known_value, str)
            or not (1 <= len(known_value) <= 512)
            or set(value) != {"state", "value", "evidenceKeys"}
        ):
            raise ObligationIntegrityError(f"invalid known {field_code} assertion")
        reason = temporal_kind = None
    else:
        reason = value.get("reason")
        temporal = value.get("temporalScope")
        temporal_kind = temporal.get("kind") if isinstance(temporal, Mapping) else None
        if (
            not isinstance(reason, str)
            or (state == "unknown" and reason not in _UNKNOWN_REASONS)
            or not (1 <= len(reason) <= 512)
            or type(temporal) is not dict
            or set(temporal) != {"kind"}
            or not isinstance(temporal_kind, str)
            or temporal_kind not in _TEMPORAL_KINDS
            or set(value) != {"state", "reason", "temporalScope", "evidenceKeys"}
        ):
            raise ObligationIntegrityError(f"invalid {state} {field_code} assertion")
        known_value = None
    owner = ObligationValueAssertionOwner(
        semantic_node_id=node.id,
        proposal_id=node.proposal_id,
        projection_id=node.projection_id,
        field_code=field_code,
        state=state,
        value=known_value,
        reason=reason,
        temporal_kind=temporal_kind,
    )
    branch = next(
        branch for branch in _ASSERTION_OWNER_CONTRACT["union"]["branches"]
        if branch["value"] == state
    )
    columns = {
        "value": owner.value,
        "reason": owner.reason,
        "temporal_kind": owner.temporal_kind,
    }
    if any(columns[name] is None for name in branch["requiredColumns"]):
        raise ObligationIntegrityError(f"missing required {field_code} assertion column")
    if any(columns[name] is not None for name in branch["forbiddenColumns"]):
        raise ObligationIntegrityError(f"forbidden {field_code} assertion column")
    return owner


def _descriptor_key(descriptor: Mapping[str, Any], source_pointer: str, value: Mapping[str, Any]) -> str:
    key_rule = descriptor["key"]
    if key_rule["op"] == "source_pointer":
        return source_pointer
    if key_rule["op"] == "property":
        return value[key_rule["name"]]
    raise ObligationIntegrityError("unsupported document node key rule")


def _descriptor_ordinal(descriptor: Mapping[str, Any], array_ordinal: int) -> int:
    ordinal_rule = descriptor["ordinal"]
    if ordinal_rule["op"] == "array_ordinal":
        return array_ordinal
    if ordinal_rule["op"] == "constant":
        return ordinal_rule["value"]
    raise ObligationIntegrityError("unsupported document ordinal rule")


def _descriptor_parent(
    descriptor: Mapping[str, Any], document_node_id: str | None,
) -> str | None:
    parent_rule = descriptor["parent"]
    if parent_rule["op"] == "root":
        return None
    if parent_rule["op"] == "ancestor" and parent_rule.get("name") == "D1":
        if document_node_id is None:
            raise ObligationIntegrityError("document assertion parent is missing")
        return document_node_id
    raise ObligationIntegrityError("unsupported document parent rule")


def _validate_document_mapping_contract() -> None:
    if set(_D_DESCRIPTORS) != {"D1", "D2", "D3", "D4"}:
        raise ObligationIntegrityError("document occurrence registry differs")
    for descriptor in _D_DESCRIPTORS.values():
        contract = _OWNER_CONTRACT_BY_TYPE[descriptor["nodeType"]]
        if (
            descriptor["presence"] != "required"
            or descriptor["ownerTable"] != contract["table"]
        ):
            raise ObligationIntegrityError("document owner mapping differs")
    if (
        _DOCUMENT_OWNER_CONTRACT["union"] is not None
        or _ASSERTION_OWNER_CONTRACT["references"]
        or _ASSERTION_OWNER_CONTRACT["children"]
        or _ASSERTION_OWNER_CONTRACT["union"] is None
    ):
        raise ObligationIntegrityError("document owner contract shape differs")


def _build_document_family(
    *,
    proposal_id: str,
    projection_id: str,
    canonical_documents: Sequence[Mapping[str, Any]],
    evidence_bindings: Mapping[str, str],
) -> ObligationDocumentFamily:
    _validate_document_mapping_contract()
    canonical_source, selected = _canonical_document_source(canonical_documents)
    documents = canonical_source["incorporatedDocuments"]
    selected_by_descriptor_and_index = {
        (occurrence.descriptor_id, occurrence.captures["i"]): occurrence
        for occurrence in selected
    }
    if len(selected_by_descriptor_and_index) != len(documents) * len(_D_DESCRIPTORS):
        raise ObligationIntegrityError("document occurrence cardinality differs")
    nodes: list[ObligationSemanticNode] = []
    links: list[ObligationEvidenceLink] = []
    owners: list[ObligationDocumentOwner] = []
    assertions: list[ObligationValueAssertionOwner] = []

    for document_ordinal, document in enumerate(documents):
        if not isinstance(document, Mapping):
            raise ObligationIntegrityError("incorporated document must be an object")
        if document.get("documentType") not in _DOCUMENT_TYPES:
            raise ObligationIntegrityError("invalid incorporated document type")
        if (
            not _is_stable_key(document.get("documentRefKey"))
        ):
            raise ObligationIntegrityError("invalid incorporated document key")
        if set(document) != {
            "documentRefKey", "documentType", "documentNumber", "revision",
            "retention", "evidenceKeys",
        }:
            raise ObligationIntegrityError("incorporated document shape differs")
        document_occurrence = selected_by_descriptor_and_index[("D1", document_ordinal)]
        pointer = document_occurrence.source_pointer
        document_node = _node(
            proposal_id=proposal_id,
            projection_id=projection_id,
            parent_node_id=_descriptor_parent(_DOCUMENT_DESCRIPTOR, None),
            node_type=_DOCUMENT_DESCRIPTOR["nodeType"],
            node_key=_descriptor_key(_DOCUMENT_DESCRIPTOR, pointer, document),
            source_pointer=pointer,
            canonical_value=document,
            canonical_ordinal=_descriptor_ordinal(
                _DOCUMENT_DESCRIPTOR, document_ordinal
            ),
        )
        nodes.append(document_node)
        links.extend(_evidence_links(
            proposal_id=proposal_id,
            projection_id=projection_id,
            semantic_node_id=document_node.id,
            evidence_keys=document["evidenceKeys"],
            evidence_policy=_DOCUMENT_DESCRIPTOR["evidence"],
            evidence_bindings=evidence_bindings,
        ))

        child_ids: dict[str, str] = {}
        for descriptor in _ASSERTION_DESCRIPTORS:
            assertion_occurrence = selected_by_descriptor_and_index[
                (descriptor["id"], document_ordinal)
            ]
            property_name = descriptor["selector"][-1]["name"]
            assertion_value = assertion_occurrence.canonical_value
            assertion_pointer = assertion_occurrence.source_pointer
            assertion_node = _node(
                proposal_id=proposal_id,
                projection_id=projection_id,
                parent_node_id=_descriptor_parent(descriptor, document_node.id),
                node_type=descriptor["nodeType"],
                node_key=_descriptor_key(descriptor, assertion_pointer, assertion_value),
                source_pointer=assertion_pointer,
                canonical_value=assertion_value,
                canonical_ordinal=_descriptor_ordinal(descriptor, document_ordinal),
            )
            nodes.append(assertion_node)
            child_ids[descriptor["id"]] = assertion_node.id
            assertions.append(_assertion_owner(
                node=assertion_node,
                descriptor=descriptor,
                value=assertion_value,
            ))
            links.extend(_evidence_links(
                proposal_id=proposal_id,
                projection_id=projection_id,
                semantic_node_id=assertion_node.id,
                evidence_keys=assertion_value["evidenceKeys"],
                evidence_policy=descriptor["evidence"],
                evidence_bindings=evidence_bindings,
            ))

        document_references = {
            reference["column"]: child_ids[reference["target"]]
            for reference in _DOCUMENT_OWNER_CONTRACT["references"]
        }
        if {
            child["target"] for child in _DOCUMENT_OWNER_CONTRACT["children"]
        } != set(child_ids) or any(
            child["cardinality"] != "exactly_one"
            or child["ordering"] != "fixed_slot"
            for child in _DOCUMENT_OWNER_CONTRACT["children"]
        ):
            raise ObligationIntegrityError("unsupported incorporated document child contract")
        owners.append(ObligationDocumentOwner(
            semantic_node_id=document_node.id,
            proposal_id=proposal_id,
            projection_id=projection_id,
            document_ref_key=document["documentRefKey"],
            document_type=document["documentType"],
            canonical_ordinal=document_ordinal,
            **document_references,
        ))

    return ObligationDocumentFamily(
        proposal_id=proposal_id,
        projection_id=projection_id,
        semantic_nodes=tuple(nodes),
        evidence_links=tuple(links),
        documents=tuple(owners),
        value_assertions=tuple(assertions),
    )


def materialize_document_family(
    *,
    proposal_id: str,
    projection_id: str,
    canonical_documents: Sequence[Mapping[str, Any]],
    evidence_bindings: Mapping[str, str],
) -> ObligationDocumentFamily:
    family = _build_document_family(
        proposal_id=proposal_id,
        projection_id=projection_id,
        canonical_documents=canonical_documents,
        evidence_bindings=evidence_bindings,
    )
    verify_document_family(
        proposal_id=proposal_id,
        projection_id=projection_id,
        canonical_documents=canonical_documents,
        evidence_bindings=evidence_bindings,
        family=family,
    )
    return family


def verify_document_family(
    *,
    proposal_id: str,
    projection_id: str,
    canonical_documents: Sequence[Mapping[str, Any]],
    evidence_bindings: Mapping[str, str],
    family: ObligationDocumentFamily,
) -> None:
    """Fail closed unless the complete D1-D4 graph equals the canonical source."""
    expected = _build_document_family(
        proposal_id=proposal_id,
        projection_id=projection_id,
        canonical_documents=canonical_documents,
        evidence_bindings=evidence_bindings,
    )
    if family != expected:
        raise ObligationIntegrityError("incorporated document typed projection differs")


def _node_from_occurrence(
    occurrence: Any,
    *,
    proposal_id: str,
    projection_id: str,
    parent_node_id: str | None,
    parent_descriptor_id: str | None,
) -> ObligationSemanticNode:
    descriptor = occurrence.descriptor
    parent_rule = descriptor["parent"]
    if parent_descriptor_id is None:
        if parent_rule["op"] != "root" or parent_node_id is not None:
            raise ObligationIntegrityError("requirement semantic parent rule differs")
    elif (
        parent_rule["op"] != "ancestor"
        or parent_rule.get("name") != parent_descriptor_id
        or parent_node_id is None
    ):
        raise ObligationIntegrityError("requirement semantic parent rule differs")
    ordinal_rule = descriptor["ordinal"]
    if ordinal_rule["op"] == "constant":
        ordinal = ordinal_rule["value"]
    elif ordinal_rule["op"] == "array_ordinal":
        ordinal = occurrence.captures[
            "j" if "j" in occurrence.captures else "i"
        ]
    else:
        raise ObligationIntegrityError("unsupported requirement ordinal rule")
    value = occurrence.canonical_value
    node_key = _descriptor_key(descriptor, occurrence.source_pointer, value)
    return _node(
        proposal_id=proposal_id,
        projection_id=projection_id,
        parent_node_id=parent_node_id,
        node_type=descriptor["nodeType"],
        node_key=node_key,
        source_pointer=occurrence.source_pointer,
        canonical_value=value,
        canonical_ordinal=ordinal,
    )


def _canonical_requirement_source(
    canonical_requirements: Sequence[Mapping[str, Any]],
) -> tuple[dict[str, Any], tuple[Any, ...]]:
    if not isinstance(canonical_requirements, list):
        raise ObligationIntegrityError("requirement collection is invalid")
    source = {
        "incorporatedDocuments": [],
        "requirements": canonical_requirements,
        "recurrenceGroups": [],
        "amocAuthorityProvisions": [],
    }
    _validate_source_resources(source)
    canonical_source = json.loads(canonical_bytes(source, CANONICALIZATION_VERSION_V2))
    selected = tuple(
        occurrence for occurrence in select_occurrences(canonical_source)
        if occurrence.descriptor_id in _Q_DESCRIPTOR_IDS
    )
    return canonical_source, selected


def _validate_branch_columns(owner: ObligationBranchOwner) -> None:
    contract = _OWNER_CONTRACT_BY_TYPE["branch"]
    valid_kinds = {branch["value"] for branch in contract["union"]["branches"]}
    if owner.kind not in valid_kinds:
        raise ObligationIntegrityError("invalid branch kind")
    branch = next(
        branch for branch in contract["union"]["branches"]
        if branch["value"] == owner.kind
    )
    values = {
        "alternative_group_key": owner.alternative_group_key,
        "exclusive": owner.exclusive,
        "condition_root_node_id": owner.condition_root_node_id,
    }
    if any(values[name] is None for name in branch["requiredColumns"]):
        raise ObligationIntegrityError("branch required column is missing")
    if any(values[name] is not None for name in branch["forbiddenColumns"]):
        raise ObligationIntegrityError("branch forbidden column is present")


def _build_requirement_family(
    *,
    proposal_id: str,
    projection_id: str,
    canonical_requirements: Sequence[Mapping[str, Any]],
    evidence_bindings: Mapping[str, str],
    document_family: ObligationDocumentFamily,
    canonical_documents: Sequence[Mapping[str, Any]],
    document_evidence_bindings: Mapping[str, str],
) -> ObligationRequirementFamily:
    _validate_requirement_mapping_contract()
    if (
        document_family.proposal_id != proposal_id
        or document_family.projection_id != projection_id
    ):
        raise ObligationIntegrityError("action document projection differs")
    verify_document_family(
        proposal_id=proposal_id, projection_id=projection_id,
        canonical_documents=canonical_documents,
        evidence_bindings=document_evidence_bindings,
        family=document_family,
    )
    canonical_source, selected = _canonical_requirement_source(canonical_requirements)
    requirements = canonical_source["requirements"]
    selected_by_id_i = {
        (occurrence.descriptor_id, occurrence.captures["i"]): occurrence
        for occurrence in selected
        if "j" not in occurrence.captures
    }
    selected_steps = {
        (occurrence.captures["i"], occurrence.captures["j"]): occurrence
        for occurrence in selected if occurrence.descriptor_id == "Q3"
    }
    expected_sequences = {str(ordinal) for ordinal in range(1, len(requirements) + 1)}
    actual_sequences = [value.get("sequence") for value in requirements]
    if (
        any(not isinstance(value, str) for value in actual_sequences)
        or set(actual_sequences) != expected_sequences
    ):
        raise ObligationIntegrityError("requirement sequence set differs")

    document_nodes = {node.id: node for node in document_family.semantic_nodes}
    document_by_key: dict[str, ObligationSemanticNode] = {}
    for owner in document_family.documents:
        node = document_nodes.get(owner.semantic_node_id)
        if (
            node is None
            or node.node_type != _DOCUMENT_DESCRIPTOR["nodeType"]
            or node.projection_id != projection_id
            or node.proposal_id != proposal_id
            or node.node_key != owner.document_ref_key
        ):
            raise ObligationIntegrityError("action document owner differs")
        if owner.document_ref_key in document_by_key:
            raise ObligationIntegrityError("duplicate action document owner key")
        document_by_key[owner.document_ref_key] = node

    nodes: list[ObligationSemanticNode] = []
    links: list[ObligationEvidenceLink] = []
    requirement_owners: list[ObligationRequirementOwner] = []
    action_owners: list[ObligationActionOwner] = []
    step_owners: list[ObligationActionStepOwner] = []
    branch_owners: list[ObligationBranchOwner] = []
    document_refs: list[ObligationActionDocumentRef] = []

    for requirement_ordinal, requirement in enumerate(requirements):
        required_requirement_fields = {
            "requirementKey", "sequence", "activationExpression", "requirementType",
            "action", "prerequisiteRequirementKeys", "branch", "initialTiming",
            "recurrence", "terminatingEffect", "evidenceKeys",
        }
        if frozenset(requirement) not in {
            frozenset(required_requirement_fields),
            frozenset(required_requirement_fields | {"recurrenceGroupKey"}),
        }:
            raise ObligationIntegrityError("requirement shape differs")
        q1 = selected_by_id_i[("Q1", requirement_ordinal)]
        requirement_node = _node_from_occurrence(
            q1, proposal_id=proposal_id, projection_id=projection_id,
            parent_node_id=None, parent_descriptor_id=None,
        )
        nodes.append(requirement_node)
        links.extend(_evidence_links(
            proposal_id=proposal_id, projection_id=projection_id,
            semantic_node_id=requirement_node.id,
            evidence_keys=requirement["evidenceKeys"],
            evidence_policy=q1.descriptor["evidence"],
            evidence_bindings=evidence_bindings,
        ))
        if requirement.get("requirementType") not in _REQUIREMENT_TYPES:
            raise ObligationIntegrityError("invalid requirement type")

        q2 = selected_by_id_i[("Q2", requirement_ordinal)]
        action = q2.canonical_value
        required_action_fields = {
            "actionType", "approvedDataDocumentRefKeys", "evidenceKeys",
        }
        if frozenset(action) not in {
            frozenset(required_action_fields),
            frozenset(required_action_fields | {"orderedSteps"}),
        }:
            raise ObligationIntegrityError("action shape differs")
        action_node = _node_from_occurrence(
            q2, proposal_id=proposal_id, projection_id=projection_id,
            parent_node_id=requirement_node.id, parent_descriptor_id="Q1",
        )
        nodes.append(action_node)
        links.extend(_evidence_links(
            proposal_id=proposal_id, projection_id=projection_id,
            semantic_node_id=action_node.id, evidence_keys=action["evidenceKeys"],
            evidence_policy=q2.descriptor["evidence"],
            evidence_bindings=evidence_bindings,
        ))
        if action.get("actionType") not in _ACTION_TYPES:
            raise ObligationIntegrityError("invalid action type")
        ordered_steps_present = "orderedSteps" in action
        steps = action.get("orderedSteps", [])
        for step_ordinal, step_text in enumerate(steps):
            occurrence = selected_steps[(requirement_ordinal, step_ordinal)]
            if not isinstance(step_text, str) or not (1 <= len(step_text) <= 512):
                raise ObligationIntegrityError("invalid action step")
            step_node = _node_from_occurrence(
                occurrence, proposal_id=proposal_id, projection_id=projection_id,
                parent_node_id=action_node.id, parent_descriptor_id="Q2",
            )
            nodes.append(step_node)
            step_owners.append(ObligationActionStepOwner(
                semantic_node_id=step_node.id, proposal_id=proposal_id,
                projection_id=projection_id, action_node_id=action_node.id,
                step_text=step_text, canonical_ordinal=step_ordinal,
            ))

        referenced_keys = action["approvedDataDocumentRefKeys"]
        for ref_ordinal, document_key in enumerate(referenced_keys):
            document_node = document_by_key.get(document_key)
            if document_node is None:
                raise ObligationIntegrityError(
                    f"action document reference {document_key!r} is unresolved"
                )
            identity_values = {
                "projectionId": projection_id,
                "actionNodeId": action_node.id,
                "documentNodeId": document_node.id,
                "ordinal": ref_ordinal,
            }
            identity = {
                property_name: identity_values[property_name]
                for property_name in _ACTION_DOCUMENT_RELATIONSHIP["identityProperties"]
            }
            ref_id, ref_hash = _row_id(
                _ACTION_DOCUMENT_RELATIONSHIP["idPrefix"],
                _ACTION_DOCUMENT_RELATIONSHIP["tableLabel"], identity,
            )
            document_refs.append(ObligationActionDocumentRef(
                id=ref_id, identity_hash=ref_hash, proposal_id=proposal_id,
                projection_id=projection_id, action_node_id=action_node.id,
                document_node_id=document_node.id, document_ref_key=document_key,
                canonical_ordinal=ref_ordinal,
            ))
        action_owners.append(ObligationActionOwner(
            semantic_node_id=action_node.id, proposal_id=proposal_id,
            projection_id=projection_id, requirement_node_id=requirement_node.id,
            action_type=action["actionType"],
            ordered_steps_present=ordered_steps_present,
            step_count=len(steps), document_ref_count=len(referenced_keys),
        ))

        q5 = selected_by_id_i[("Q5", requirement_ordinal)]
        branch = q5.canonical_value
        branch_fields = {
            "required": {"kind", "evidenceKeys"},
            "conditional": {"kind", "conditionExpression", "evidenceKeys"},
            "exception": {"kind", "conditionExpression", "evidenceKeys"},
            "alternative_member": {
                "kind", "alternativeGroupKey", "exclusive", "evidenceKeys",
            },
        }
        if branch.get("kind") not in branch_fields or set(branch) != branch_fields[branch["kind"]]:
            raise ObligationIntegrityError("branch shape differs")
        branch_node = _node_from_occurrence(
            q5, proposal_id=proposal_id, projection_id=projection_id,
            parent_node_id=requirement_node.id, parent_descriptor_id="Q1",
        )
        nodes.append(branch_node)
        links.extend(_evidence_links(
            proposal_id=proposal_id, projection_id=projection_id,
            semantic_node_id=branch_node.id, evidence_keys=branch["evidenceKeys"],
            evidence_policy=q5.descriptor["evidence"],
            evidence_bindings=evidence_bindings,
        ))
        condition_root_id = None
        if branch.get("kind") in {"conditional", "exception"}:
            condition_occurrence = selected_by_id_i[("EBR", requirement_ordinal)]
            condition_root_id = _node_from_occurrence(
                condition_occurrence, proposal_id=proposal_id,
                projection_id=projection_id, parent_node_id=branch_node.id,
                parent_descriptor_id="Q5",
            ).id
        branch_owner = ObligationBranchOwner(
            semantic_node_id=branch_node.id, proposal_id=proposal_id,
            projection_id=projection_id, requirement_node_id=requirement_node.id,
            kind=branch["kind"],
            alternative_group_key=branch.get("alternativeGroupKey"),
            exclusive=branch.get("exclusive"),
            condition_root_node_id=condition_root_id,
        )
        _validate_branch_columns(branch_owner)
        branch_owners.append(branch_owner)

        deferred_children = {
            descriptor_id: _node_from_occurrence(
                selected_by_id_i[(descriptor_id, requirement_ordinal)],
                proposal_id=proposal_id, projection_id=projection_id,
                parent_node_id=requirement_node.id, parent_descriptor_id="Q1",
            ).id
            for descriptor_id in ("EACT", "T1", "R1", "Q7")
        }
        requirement_owners.append(ObligationRequirementOwner(
            semantic_node_id=requirement_node.id, proposal_id=proposal_id,
            projection_id=projection_id,
            requirement_key=requirement["requirementKey"],
            sequence_text=requirement["sequence"],
            sequence_value=int(requirement["sequence"]),
            requirement_type=requirement["requirementType"],
            canonical_ordinal=requirement_ordinal,
            recurrence_group_present="recurrenceGroupKey" in requirement,
            recurrence_group_key=requirement.get("recurrenceGroupKey"),
            action_node_id=action_node.id,
            activation_root_node_id=deferred_children["EACT"],
            branch_node_id=branch_node.id,
            initial_timing_node_id=deferred_children["T1"],
            recurrence_node_id=deferred_children["R1"],
            terminating_effect_node_id=deferred_children["Q7"],
        ))

    return ObligationRequirementFamily(
        proposal_id=proposal_id, projection_id=projection_id,
        semantic_nodes=tuple(nodes), evidence_links=tuple(links),
        requirements=tuple(requirement_owners), actions=tuple(action_owners),
        action_steps=tuple(step_owners), branches=tuple(branch_owners),
        action_document_refs=tuple(document_refs),
    )


def materialize_requirement_family(
    *, proposal_id: str, projection_id: str,
    canonical_requirements: Sequence[Mapping[str, Any]],
    evidence_bindings: Mapping[str, str],
    document_family: ObligationDocumentFamily,
    canonical_documents: Sequence[Mapping[str, Any]],
    document_evidence_bindings: Mapping[str, str],
) -> ObligationRequirementFamily:
    family = _build_requirement_family(
        proposal_id=proposal_id, projection_id=projection_id,
        canonical_requirements=canonical_requirements,
        evidence_bindings=evidence_bindings, document_family=document_family,
        canonical_documents=canonical_documents,
        document_evidence_bindings=document_evidence_bindings,
    )
    verify_requirement_family(
        proposal_id=proposal_id, projection_id=projection_id,
        canonical_requirements=canonical_requirements,
        evidence_bindings=evidence_bindings, document_family=document_family,
        canonical_documents=canonical_documents,
        document_evidence_bindings=document_evidence_bindings,
        family=family,
    )
    return family


def verify_requirement_family(
    *, proposal_id: str, projection_id: str,
    canonical_requirements: Sequence[Mapping[str, Any]],
    evidence_bindings: Mapping[str, str],
    document_family: ObligationDocumentFamily,
    canonical_documents: Sequence[Mapping[str, Any]],
    document_evidence_bindings: Mapping[str, str],
    family: ObligationRequirementFamily,
) -> None:
    nonnegative_integers = [
        *(node.canonical_ordinal for node in family.semantic_nodes),
        *(link.canonical_ordinal for link in family.evidence_links),
        *(row.canonical_ordinal for row in family.requirements),
        *(row.step_count for row in family.actions),
        *(row.document_ref_count for row in family.actions),
        *(row.canonical_ordinal for row in family.action_steps),
        *(row.canonical_ordinal for row in family.action_document_refs),
    ]
    if any(type(value) is not int or value < 0 for value in nonnegative_integers):
        raise ObligationIntegrityError("requirement ordinal/count numeric type differs")
    if any(
        type(row.sequence_value) is not int or row.sequence_value < 1
        for row in family.requirements
    ):
        raise ObligationIntegrityError("requirement sequence numeric type differs")
    if any(
        type(row.recurrence_group_present) is not bool
        for row in family.requirements
    ) or any(type(row.ordered_steps_present) is not bool for row in family.actions):
        raise ObligationIntegrityError("requirement presence boolean type differs")
    if any(
        row.exclusive is not None and type(row.exclusive) is not bool
        for row in family.branches
    ):
        raise ObligationIntegrityError("branch exclusive boolean type differs")
    expected = _build_requirement_family(
        proposal_id=proposal_id, projection_id=projection_id,
        canonical_requirements=canonical_requirements,
        evidence_bindings=evidence_bindings, document_family=document_family,
        canonical_documents=canonical_documents,
        document_evidence_bindings=document_evidence_bindings,
    )
    if family != expected:
        raise ObligationIntegrityError("requirement/action/branch typed projection differs")


def make_applicability_target(
    *, proposal_id: str, projection_id: str, node_type: str, node_key: str,
    source_pointer: str, canonical_value: Mapping[str, Any],
) -> ObligationApplicabilityTarget:
    identity = {
        "projectionId": projection_id, "nodeType": node_type,
        "nodeKey": node_key, "pointer": source_pointer,
    }
    identity_hash = hashlib.sha256(
        _APP_ROW_DOMAIN + obligation_record_bytes({
            "table": "semantic-node", "identity": identity,
        })
    ).hexdigest()
    node_bytes = canonical_bytes(canonical_value, CANONICALIZATION_VERSION_V2)
    return ObligationApplicabilityTarget(
        id=f"avn_{identity_hash[:32]}", identity_hash=identity_hash,
        proposal_id=proposal_id, projection_id=projection_id,
        node_type=node_type, node_key=node_key, source_pointer=source_pointer,
        canonical_node_bytes=node_bytes,
        canonical_node_hash=hashlib.sha256(node_bytes).hexdigest(),
    )


def _verified_app_target_lookup(
    *, proposal_id: str, app_projection_id: str,
    app_targets: Sequence[ObligationApplicabilityTarget],
) -> dict[tuple[str, str], ObligationApplicabilityTarget]:
    result: dict[tuple[str, str], ObligationApplicabilityTarget] = {}
    for target in app_targets:
        try:
            canonical_value = json.loads(target.canonical_node_bytes)
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ObligationIntegrityError("Slice-3A target canonical bytes differ") from exc
        try:
            round_trip_bytes = canonical_bytes(
                canonical_value, CANONICALIZATION_VERSION_V2,
            )
        except (TypeError, ValueError) as exc:
            raise ObligationIntegrityError("Slice-3A target canonical bytes differ") from exc
        key_field = {
            "product_scope": "scopeKey",
            "condition": "conditionKey",
            "applicability_rule": "ruleKey",
        }.get(target.node_type)
        identity = {
            "projectionId": app_projection_id, "nodeType": target.node_type,
            "nodeKey": target.node_key, "pointer": target.source_pointer,
        }
        expected_hash = hashlib.sha256(
            _APP_ROW_DOMAIN + obligation_record_bytes({
                "table": "semantic-node", "identity": identity,
            })
        ).hexdigest()
        if (
            target.proposal_id != proposal_id
            or target.projection_id != app_projection_id
            or target.node_type not in {"product_scope", "condition", "applicability_rule"}
            or target.id != f"avn_{expected_hash[:32]}"
            or target.identity_hash != expected_hash
            or key_field is None
            or not isinstance(canonical_value, dict)
            or canonical_value.get(key_field) != target.node_key
            or round_trip_bytes != target.canonical_node_bytes
            or hashlib.sha256(target.canonical_node_bytes).hexdigest()
            != target.canonical_node_hash
        ):
            raise ObligationIntegrityError("Slice-3A expression target differs")
        key = (target.node_type, target.node_key)
        if key in result:
            raise ObligationIntegrityError("duplicate Slice-3A expression target")
        result[key] = target
    return result


def _validate_expression_contract() -> None:
    if "graph_cycle_check" not in GLOBAL_ALGORITHMS:
        raise ObligationIntegrityError("expression graph algorithm contract differs")
    if set(_EXPRESSION_OWNER_CONTRACT["occurrences"]) != {"EACT", "EBR", "EREC"}:
        raise ObligationIntegrityError("expression occurrence contract differs")
    expected_descriptors = {
        "EACT": ("required", "Q1", 1, "activation"),
        "EBR": ("union", "Q5", 0, "branch_condition"),
        "EREC": ("union", "R1", 0, "recurrence_condition"),
    }
    for descriptor_id, (presence, parent, ordinal, context) in expected_descriptors.items():
        descriptor = _Q_DESCRIPTORS[descriptor_id]
        if (
            descriptor["nodeType"] != "expression"
            or descriptor["ownerTable"] != _EXPRESSION_OWNER_CONTRACT["table"]
            or descriptor["key"]["op"] != "source_pointer"
            or descriptor["presence"] != presence
            or descriptor["parent"] != {"op": "ancestor", "name": parent}
            or descriptor["ordinal"] != {"op": "constant", "value": ordinal}
            or descriptor["context"] != context
            or descriptor["evidence"] != {
                "source": "none", "purpose": None,
                "cardinality": "zero", "inheritance": "none",
            }
        ):
            raise ObligationIntegrityError("expression descriptor contract differs")
    expected_edge = {
        "table": "ad_v4_candidate_obligation_expression_edges",
        "tableLabel": "expression-edge", "idPrefix": "aog",
        "identityProperties": (
            "projectionId", "requirementNodeId", "context",
            "parentExpressionId", "childExpressionId", "ordinal",
        ),
        "ordering": "canonical_ordinal", "cardinality": "zero_or_more",
    }
    if any(_EXPRESSION_EDGE_RELATIONSHIP[key] != value for key, value in expected_edge.items()):
        raise ObligationIntegrityError("expression edge contract differs")
    expected_branches = {
        "scope_ref": (("app_target_projection_id", "app_target_node_id"), ("required_state", "requirement_target_node_id"), (), ("EEDGE",)),
        "predicate_ref": (("app_target_projection_id", "app_target_node_id"), ("required_state", "requirement_target_node_id"), (), ("EEDGE",)),
        "rule_ref": (("app_target_projection_id", "app_target_node_id"), ("required_state", "requirement_target_node_id"), (), ("EEDGE",)),
        "requirement_state_ref": (
            ("required_state", "requirement_target_node_id"),
            ("app_target_projection_id", "app_target_node_id"), (), ("EEDGE",),
        ),
        "not": ((), (
            "required_state", "app_target_projection_id", "app_target_node_id",
            "requirement_target_node_id",
        ), ("EEDGE:1",), ()),
        "all": ((), (
            "required_state", "app_target_projection_id", "app_target_node_id",
            "requirement_target_node_id",
        ), ("EEDGE:2+",), ()),
        "any": ((), (
            "required_state", "app_target_projection_id", "app_target_node_id",
            "requirement_target_node_id",
        ), ("EEDGE:2+",), ()),
    }
    for branch in _EXPRESSION_OWNER_CONTRACT["union"]["branches"]:
        required, forbidden, required_children, forbidden_children = expected_branches[branch["value"]]
        if (
            set(branch["requiredColumns"]) != set(required)
            or set(branch["forbiddenColumns"]) != set(forbidden)
            or tuple(branch["requiredChildren"]) != required_children
            or tuple(branch["forbiddenChildren"]) != forbidden_children
        ):
            raise ObligationIntegrityError("expression union contract differs")
    expected_target_types = {
        "scope_ref": "product_scope", "predicate_ref": "condition",
        "rule_ref": "applicability_rule", "requirement_state_ref": "requirement",
    }
    for branch in _EXPRESSION_OWNER_CONTRACT["union"]["branches"]:
        expected_type = expected_target_types.get(branch["value"])
        actual_types = tuple(
            target["targetNodeType"] for target in branch.get("referenceTargets", ())
        )
        if actual_types != (() if expected_type is None else (expected_type,)):
            raise ObligationIntegrityError("expression reference target type differs")
    if {
        (reference["column"], reference["scope"], reference["cardinality"])
        for reference in _EXPRESSION_OWNER_CONTRACT["references"]
    } != {
        ("app_target_node_id", "same_proposal_slice_3a", "optional_one"),
        ("requirement_target_node_id", "same_projection", "optional_one"),
    } or _EXPRESSION_OWNER_CONTRACT["children"] != ({
        "target": "EEDGE", "cardinality": "branch_defined",
        "ordering": "canonical_ordinal",
    },):
        raise ObligationIntegrityError("expression reference contract differs")


def _verify_combined_requirement_graph(
    *, requirements: Sequence[Mapping[str, Any]],
    expression_dependencies: Mapping[str, set[str]],
    expression_reference_count: int,
) -> None:
    """Verify the one requirement graph shared by E, Q9, and Q10 families."""
    requirement_keys = {
        requirement["requirementKey"] for requirement in requirements
    }
    if set(expression_dependencies) != requirement_keys:
        raise ObligationIntegrityError("requirement graph source set differs")
    graph = {
        requirement_key: set(expression_dependencies[requirement_key])
        for requirement_key in requirement_keys
    }
    source_edge_count = expression_reference_count
    for requirement in requirements:
        requirement_key = requirement["requirementKey"]
        prerequisites = requirement["prerequisiteRequirementKeys"]
        effect = requirement["terminatingEffect"]
        terminated = effect.get("requirementKeys", ())
        source_edge_count += len(prerequisites) + len(terminated)
        for target_key in (*prerequisites, *terminated):
            if target_key not in requirement_keys:
                raise ObligationIntegrityError("requirement graph target is unresolved")
            graph[requirement_key].add(target_key)
    if source_edge_count > RESOURCE_LIMITS["maxGraphEdges"]:
        raise ObligationIntegrityError("requirement graph edge limit exceeded")

    if first_cycle_node(graph) is not None:
        raise ObligationIntegrityError("combined requirement graph cycle")


def _build_expression_family(
    *, proposal_id: str, projection_id: str, app_projection_id: str,
    canonical_requirements: Sequence[Mapping[str, Any]],
    evidence_bindings: Mapping[str, str],
    document_family: ObligationDocumentFamily,
    canonical_documents: Sequence[Mapping[str, Any]],
    document_evidence_bindings: Mapping[str, str],
    requirement_family: ObligationRequirementFamily,
    app_targets: Sequence[ObligationApplicabilityTarget],
) -> ObligationExpressionFamily:
    _validate_expression_contract()
    verify_requirement_family(
        proposal_id=proposal_id, projection_id=projection_id,
        canonical_requirements=canonical_requirements,
        evidence_bindings=evidence_bindings, document_family=document_family,
        canonical_documents=canonical_documents,
        document_evidence_bindings=document_evidence_bindings,
        family=requirement_family,
    )
    canonical_source, selected = _canonical_requirement_source(canonical_requirements)
    requirements = canonical_source["requirements"]
    roots = {
        (occurrence.descriptor_id, occurrence.captures["i"]): occurrence
        for occurrence in selected
        if occurrence.descriptor_id in {"EACT", "EBR", "EREC"}
    }
    app_lookup = _verified_app_target_lookup(
        proposal_id=proposal_id, app_projection_id=app_projection_id,
        app_targets=app_targets,
    )
    requirements_by_key = {row.requirement_key: row for row in requirement_family.requirements}
    requirements_by_ordinal = {
        row.canonical_ordinal: row for row in requirement_family.requirements
    }
    branches_by_requirement = {
        row.requirement_node_id: row for row in requirement_family.branches
    }
    nodes: list[ObligationSemanticNode] = []
    owners: list[ObligationExpressionOwner] = []
    edges: list[ObligationExpressionEdge] = []
    state_dependencies: dict[str, set[str]] = {
        row.requirement_key: set() for row in requirement_family.requirements
    }
    expression_reference_count = 0

    def walk(
        value: Mapping[str, Any], *, pointer: str, expression_path: str,
        parent_node_id: str, ordinal: int, requirement: ObligationRequirementOwner,
        context: str, depth: int,
    ) -> ObligationSemanticNode:
        nonlocal expression_reference_count
        if depth > RESOURCE_LIMITS["maxDepth"]:
            raise ObligationIntegrityError("expression depth limit exceeded")
        if len(nodes) >= RESOURCE_LIMITS["maxAstNodes"]:
            raise ObligationIntegrityError("expression AST node limit exceeded")
        if not isinstance(value, Mapping):
            raise ObligationIntegrityError("expression node must be an object")
        node_type = value.get("nodeType")
        shapes = {
            "scope_ref": {"nodeType", "scopeKey"},
            "predicate_ref": {"nodeType", "conditionKey"},
            "rule_ref": {"nodeType", "ruleKey"},
            "requirement_state_ref": {"nodeType", "requirementKey", "requirementState"},
            "not": {"nodeType", "operand"},
            "all": {"nodeType", "operands"},
            "any": {"nodeType", "operands"},
        }
        if node_type not in shapes or set(value) != shapes[node_type]:
            raise ObligationIntegrityError("expression union shape differs")
        union_branch = next(
            branch for branch in _EXPRESSION_OWNER_CONTRACT["union"]["branches"]
            if branch["value"] == node_type
        )
        node = _node(
            proposal_id=proposal_id, projection_id=projection_id,
            parent_node_id=parent_node_id, node_type="expression",
            node_key=pointer, source_pointer=pointer, canonical_value=value,
            canonical_ordinal=ordinal,
        )
        nodes.append(node)
        required_state = None
        app_target_projection = None
        app_target_node = None
        requirement_target_node = None
        child_values: list[tuple[Mapping[str, Any], str, str, int]] = []
        if node_type in {"scope_ref", "predicate_ref", "rule_ref"}:
            target_type = union_branch["referenceTargets"][0]["targetNodeType"]
            key_field = {
                "scope_ref": "scopeKey", "predicate_ref": "conditionKey",
                "rule_ref": "ruleKey",
            }[node_type]
            target = app_lookup.get((target_type, value[key_field]))
            if target is None:
                raise ObligationIntegrityError("expression Slice-3A target is unresolved")
            app_target_projection = app_projection_id
            app_target_node = target.id
        elif node_type == "requirement_state_ref":
            target = requirements_by_key.get(value["requirementKey"])
            if target is None:
                raise ObligationIntegrityError("expression requirement target is unresolved")
            if target.semantic_node_id == requirement.semantic_node_id:
                raise ObligationIntegrityError("expression requirement self-reference")
            if value["requirementState"] not in {"satisfied", "not_satisfied", "unknown"}:
                raise ObligationIntegrityError("expression requirement state differs")
            required_state = value["requirementState"]
            requirement_target_node = target.semantic_node_id
            state_dependencies[requirement.requirement_key].add(target.requirement_key)
            expression_reference_count += 1
        elif node_type == "not":
            child_values = [(
                value["operand"],
                f"{pointer}/operand",
                f"{expression_path.rstrip('/')}/operand",
                0,
            )]
        else:
            operands = value["operands"]
            if not isinstance(operands, list) or len(operands) < 2:
                raise ObligationIntegrityError("expression operand cardinality differs")
            child_values = [
                (child, f"{pointer}/operands/{child_ordinal}",
                 f"{expression_path.rstrip('/')}/operands/{child_ordinal}",
                 child_ordinal)
                for child_ordinal, child in enumerate(operands)
            ]
        owner = ObligationExpressionOwner(
            semantic_node_id=node.id, proposal_id=proposal_id,
            projection_id=projection_id, requirement_node_id=requirement.semantic_node_id,
            context=context, expression_path=expression_path, node_type=node_type,
            required_state=required_state,
            app_target_projection_id=app_target_projection,
            app_target_node_id=app_target_node,
            requirement_target_node_id=requirement_target_node,
        )
        branch = union_branch
        owner_values = {
            "required_state": owner.required_state,
            "app_target_projection_id": owner.app_target_projection_id,
            "app_target_node_id": owner.app_target_node_id,
            "requirement_target_node_id": owner.requirement_target_node_id,
        }
        if any(owner_values[name] is None for name in branch["requiredColumns"]):
            raise ObligationIntegrityError("expression required column is missing")
        if any(owner_values[name] is not None for name in branch["forbiddenColumns"]):
            raise ObligationIntegrityError("expression forbidden column is present")
        owners.append(owner)
        for child_value, child_pointer, child_path, child_ordinal in child_values:
            child = walk(
                child_value, pointer=child_pointer, expression_path=child_path,
                parent_node_id=node.id, ordinal=child_ordinal,
                requirement=requirement, context=context, depth=depth + 1,
            )
            if len(edges) >= RESOURCE_LIMITS["maxGraphEdges"]:
                raise ObligationIntegrityError("expression edge limit exceeded")
            identity_values = {
                "projectionId": projection_id,
                "requirementNodeId": requirement.semantic_node_id,
                "context": context, "parentExpressionId": node.id,
                "childExpressionId": child.id, "ordinal": child_ordinal,
            }
            identity = {
                name: identity_values[name]
                for name in _EXPRESSION_EDGE_RELATIONSHIP["identityProperties"]
            }
            edge_id, edge_hash = _row_id(
                _EXPRESSION_EDGE_RELATIONSHIP["idPrefix"],
                _EXPRESSION_EDGE_RELATIONSHIP["tableLabel"], identity,
            )
            edges.append(ObligationExpressionEdge(
                id=edge_id, identity_hash=edge_hash, proposal_id=proposal_id,
                projection_id=projection_id,
                requirement_node_id=requirement.semantic_node_id,
                context=context, parent_expression_id=node.id,
                child_expression_id=child.id, canonical_ordinal=child_ordinal,
            ))
        expected_child_rule = branch["requiredChildren"]
        if node_type == "not" and len(child_values) != 1:
            raise ObligationIntegrityError("not expression child count differs")
        if node_type in {"all", "any"} and len(child_values) < 2:
            raise ObligationIntegrityError("expression child count differs")
        if not expected_child_rule and child_values:
            raise ObligationIntegrityError("leaf expression has children")
        return node

    for requirement_ordinal, _ in enumerate(requirements):
        requirement = requirements_by_ordinal[requirement_ordinal]
        branch = branches_by_requirement[requirement.semantic_node_id]
        contexts = [("EACT", requirement.semantic_node_id, "activation")]
        if branch.kind in {"conditional", "exception"}:
            contexts.append(("EBR", branch.semantic_node_id, "branch_condition"))
        if requirements[requirement_ordinal]["recurrence"]["kind"] == "conditioned":
            contexts.append(("EREC", requirement.recurrence_node_id, "recurrence_condition"))
        for descriptor_id, parent_id, context in contexts:
            occurrence = roots[(descriptor_id, requirement_ordinal)]
            root = walk(
                occurrence.canonical_value, pointer=occurrence.source_pointer,
                expression_path="/", parent_node_id=parent_id,
                ordinal=occurrence.descriptor["ordinal"]["value"],
                requirement=requirement, context=context, depth=0,
            )
            if descriptor_id == "EACT" and root.id != requirement.activation_root_node_id:
                raise ObligationIntegrityError("activation expression root differs")
            if descriptor_id == "EBR" and root.id != branch.condition_root_node_id:
                raise ObligationIntegrityError("branch expression root differs")

    _verify_combined_requirement_graph(
        requirements=requirements,
        expression_dependencies=state_dependencies,
        expression_reference_count=expression_reference_count,
    )

    return ObligationExpressionFamily(
        proposal_id=proposal_id, projection_id=projection_id,
        app_projection_id=app_projection_id,
        semantic_nodes=tuple(nodes), expressions=tuple(owners), edges=tuple(edges),
    )


def materialize_expression_family(
    *, proposal_id: str, projection_id: str, app_projection_id: str,
    canonical_requirements: Sequence[Mapping[str, Any]],
    evidence_bindings: Mapping[str, str], document_family: ObligationDocumentFamily,
    canonical_documents: Sequence[Mapping[str, Any]],
    document_evidence_bindings: Mapping[str, str],
    requirement_family: ObligationRequirementFamily,
    app_targets: Sequence[ObligationApplicabilityTarget],
) -> ObligationExpressionFamily:
    family = _build_expression_family(
        proposal_id=proposal_id, projection_id=projection_id,
        app_projection_id=app_projection_id,
        canonical_requirements=canonical_requirements,
        evidence_bindings=evidence_bindings, document_family=document_family,
        canonical_documents=canonical_documents,
        document_evidence_bindings=document_evidence_bindings,
        requirement_family=requirement_family, app_targets=app_targets,
    )
    verify_expression_family(
        proposal_id=proposal_id, projection_id=projection_id,
        app_projection_id=app_projection_id,
        canonical_requirements=canonical_requirements,
        evidence_bindings=evidence_bindings, document_family=document_family,
        canonical_documents=canonical_documents,
        document_evidence_bindings=document_evidence_bindings,
        requirement_family=requirement_family, app_targets=app_targets,
        family=family,
    )
    return family


def verify_expression_family(
    *, proposal_id: str, projection_id: str, app_projection_id: str,
    canonical_requirements: Sequence[Mapping[str, Any]],
    evidence_bindings: Mapping[str, str], document_family: ObligationDocumentFamily,
    canonical_documents: Sequence[Mapping[str, Any]],
    document_evidence_bindings: Mapping[str, str],
    requirement_family: ObligationRequirementFamily,
    app_targets: Sequence[ObligationApplicabilityTarget],
    family: ObligationExpressionFamily,
) -> None:
    expected = _build_expression_family(
        proposal_id=proposal_id, projection_id=projection_id,
        app_projection_id=app_projection_id,
        canonical_requirements=canonical_requirements,
        evidence_bindings=evidence_bindings, document_family=document_family,
        canonical_documents=canonical_documents,
        document_evidence_bindings=document_evidence_bindings,
        requirement_family=requirement_family, app_targets=app_targets,
    )
    if family != expected:
        raise ObligationIntegrityError("expression typed projection differs")


def _validate_timing_recurrence_contract() -> None:
    expected_descriptors = {
        "T1": ("timing_group", "Q1", 3, "requirement_initial", "required"),
        "T5I": ("timing_term", "T1", None, "requirement_initial", "union"),
        "R1": ("recurrence", "Q1", 4, None, "required"),
        "R6": ("timing_group", "R1", 1, "requirement_recurrence", "union"),
        "T5R": ("timing_term", "R6", None, "requirement_recurrence", "union"),
    }
    contracts = {
        "timing_group": _TIMING_OWNER_CONTRACT,
        "timing_term": _TIMING_TERM_OWNER_CONTRACT,
        "recurrence": _RECURRENCE_OWNER_CONTRACT,
    }
    for descriptor_id, (node_type, parent, ordinal, owner_kind, presence) in expected_descriptors.items():
        descriptor = _Q_DESCRIPTORS[descriptor_id]
        ordinal_rule = (
            {"op": "array_ordinal"} if ordinal is None
            else {"op": "constant", "value": ordinal}
        )
        if (
            descriptor["nodeType"] != node_type
            or descriptor["ownerTable"] != contracts[node_type]["table"]
            or descriptor["key"] != {"op": "source_pointer"}
            or descriptor["parent"] != {"op": "ancestor", "name": parent}
            or descriptor["ordinal"] != ordinal_rule
            or descriptor["presence"] != presence
            or descriptor.get("ownerKind") != owner_kind
            or descriptor["evidence"] != {
                "source": "own",
                "purpose": (
                    "recurrence_clause" if descriptor_id == "R1"
                    else "timing_term_clause" if descriptor_id in {"T5I", "T5R"}
                    else "timing_clause"
                ),
                "cardinality": "one_or_more", "inheritance": "none",
            }
            or (
                descriptor_id == "R6"
                and tuple(descriptor.get("allowedUnionBranches", ())) != ("known",)
            )
        ):
            raise ObligationIntegrityError("timing occurrence contract differs")
    if tuple(_TIMING_OWNER_CONTRACT["occurrences"]) != ("T1", "R6", "G3", "G4"):
        raise ObligationIntegrityError("timing owner occurrence contract differs")
    if tuple(_TIMING_TERM_OWNER_CONTRACT["occurrences"]) != (
        "T5I", "T5R", "T5GI", "T5GR",
    ) or tuple(_RECURRENCE_OWNER_CONTRACT["occurrences"]) != ("R1",):
        raise ObligationIntegrityError("timing owner occurrence contract differs")
    if (
        tuple(_TIMING_OWNER_CONTRACT["references"]) != ()
        or tuple(_TIMING_OWNER_CONTRACT["children"]) != ({
            "target": "T5I|T5R|T5GI|T5GR",
            "cardinality": "branch_defined", "ordering": "canonical_ordinal",
        },)
        or tuple(_TIMING_TERM_OWNER_CONTRACT["references"]) != ({
            "column": "timing_group_node_id", "target": "T1|R6|G3|G4",
            "targetNodeType": "timing_group", "scope": "same_projection",
            "cardinality": "required_one",
        },)
        or tuple(_TIMING_TERM_OWNER_CONTRACT["children"]) != ()
        or tuple(_RECURRENCE_OWNER_CONTRACT["references"]) != (
            {"column": "requirement_node_id", "target": "Q1", "targetNodeType": "requirement", "scope": "same_projection", "cardinality": "required_one"},
            {"column": "timing_node_id", "target": "R6", "targetNodeType": "timing_group", "scope": "same_projection", "cardinality": "optional_one"},
            {"column": "condition_root_node_id", "target": "EREC", "targetNodeType": "expression", "scope": "same_projection", "cardinality": "optional_one"},
        )
        or tuple(_RECURRENCE_OWNER_CONTRACT["children"]) != (
            {"target": "R6", "cardinality": "branch_defined", "ordering": "fixed_slot"},
            {"target": "EREC", "cardinality": "branch_defined", "ordering": "fixed_slot"},
        )
    ):
        raise ObligationIntegrityError("timing reference/child contract differs")
    expected_timing_unions = {
        "known": ({"logic"}, {"reason", "temporal_kind"}, ("timing_term:1+",), ()),
        "unknown": ({"reason", "temporal_kind"}, {"logic"}, (), ("timing_term",)),
        "not_applicable": ({"reason", "temporal_kind"}, {"logic"}, (), ("timing_term",)),
    }
    for branch in _TIMING_OWNER_CONTRACT["union"]["branches"]:
        required, forbidden, children, forbidden_children = expected_timing_unions[branch["value"]]
        if (
            set(branch["requiredColumns"]) != required
            or set(branch["forbiddenColumns"]) != forbidden
            or tuple(branch["requiredChildren"]) != children
            or tuple(branch["forbiddenChildren"]) != forbidden_children
        ):
            raise ObligationIntegrityError("timing union contract differs")
    expected_recurrence_unions = {
        "none": (set(), {"timing_node_id", "condition_root_node_id", "reason", "temporal_kind"}, (), ("R6", "EREC")),
        "interval": ({"timing_node_id"}, {"condition_root_node_id", "reason", "temporal_kind"}, ("R6",), ("EREC",)),
        "conditioned": ({"timing_node_id", "condition_root_node_id"}, {"reason", "temporal_kind"}, ("R6", "EREC"), ()),
        "unknown": ({"reason", "temporal_kind"}, {"timing_node_id", "condition_root_node_id"}, (), ("R6", "EREC")),
    }
    for branch in _RECURRENCE_OWNER_CONTRACT["union"]["branches"]:
        required, forbidden, children, forbidden_children = expected_recurrence_unions[branch["value"]]
        if (
            set(branch["requiredColumns"]) != required
            or set(branch["forbiddenColumns"]) != forbidden
            or tuple(branch["requiredChildren"]) != children
            or tuple(branch["forbiddenChildren"]) != forbidden_children
        ):
            raise ObligationIntegrityError("recurrence union contract differs")


_DECIMAL_TEXT_RE = re.compile(r"^(?:0|[1-9][0-9]*)(?:\.[0-9]*[1-9])?$")
_TIMING_LOGIC = frozenset({"all", "whichever_first", "whichever_later"})
_TIMING_METRICS = frozenset({"calendar", "aircraft_time", "component_time", "cycles", "other_reviewed"})
_TIMING_UNITS = frozenset({"days", "months", "years", "hours", "cycles", "source_defined"})
_TIMING_COMPARATORS = frozenset({"within", "before", "at_or_before", "after", "at_or_after"})
_TIMING_ANCHORS = frozenset({"effective_date", "last_compliance", "installation", "manufacture", "source_defined"})
_UNKNOWN_REASONS = frozenset({
    "not_observed", "unavailable", "not_obtained", "not_extracted",
    "not_yet_reviewed", "not_yet_verified", "conflicting_evidence",
    "source_ambiguous", "unsupported_expression",
})
_TEMPORAL_KINDS = frozenset({
    "directive_version", "publication_version", "at_applicability_evaluation",
    "at_compliance_evaluation", "source_observation",
})


def _validate_timing_value(value: Mapping[str, Any], *, known_only: bool) -> str:
    if type(value) is not dict:
        raise ObligationIntegrityError("timing source object differs")
    if "logic" in value:
        if (
            set(value) != {"logic", "terms", "evidenceKeys"}
            or not isinstance(value["logic"], str)
            or value["logic"] not in _TIMING_LOGIC
            or not isinstance(value["terms"], list)
            or not value["terms"]
        ):
            raise ObligationIntegrityError("known timing shape differs")
        return "known"
    if known_only:
        raise ObligationIntegrityError("recurrence timing must be known")
    if set(value) != {"state", "reason", "temporalScope", "evidenceKeys"}:
        raise ObligationIntegrityError("non-known timing shape differs")
    state = value["state"]
    temporal = value["temporalScope"]
    if (
        not isinstance(state, str)
        or state not in {"unknown", "not_applicable"}
        or type(temporal) is not dict
        or set(temporal) != {"kind"}
        or not isinstance(temporal["kind"], str)
        or temporal["kind"] not in _TEMPORAL_KINDS
        or not isinstance(value["reason"], str)
        or not value["reason"]
        or (state == "unknown" and value["reason"] not in _UNKNOWN_REASONS)
        or (state == "not_applicable" and len(value["reason"]) > 512)
    ):
        raise ObligationIntegrityError("non-known timing value differs")
    return state


def _validate_timing_term_value(term: Mapping[str, Any]) -> None:
    if (
        type(term) is not dict
        or
        set(term) != {"metric", "interval", "unit", "comparator", "anchor", "evidenceKeys"}
        or any(
            not isinstance(term[name], str)
            for name in ("metric", "interval", "unit", "comparator", "anchor")
        )
        or term["metric"] not in _TIMING_METRICS
        or term["unit"] not in _TIMING_UNITS
        or term["comparator"] not in _TIMING_COMPARATORS
        or term["anchor"] not in _TIMING_ANCHORS
    ):
        raise ObligationIntegrityError("timing term value differs")


def _validate_recurrence_value(value: Mapping[str, Any]) -> str:
    if type(value) is not dict:
        raise ObligationIntegrityError("recurrence shape differs")
    kind = value.get("kind")
    expected_keys = {
        "none": {"kind", "evidenceKeys"},
        "interval": {"kind", "timing", "evidenceKeys"},
        "conditioned": {"kind", "conditionExpression", "timing", "evidenceKeys"},
        "unknown": {"kind", "reason", "temporalScope", "evidenceKeys"},
    }
    if (
        not isinstance(kind, str)
        or kind not in expected_keys
        or set(value) != expected_keys[kind]
    ):
        raise ObligationIntegrityError("recurrence shape differs")
    if kind == "unknown":
        temporal = value["temporalScope"]
        if (
            not isinstance(value["reason"], str)
            or value["reason"] not in _UNKNOWN_REASONS
            or type(temporal) is not dict
            or set(temporal) != {"kind"}
            or not isinstance(temporal["kind"], str)
            or temporal["kind"] not in _TEMPORAL_KINDS
        ):
            raise ObligationIntegrityError("recurrence unknown value differs")
    return kind


def _timing_decimal(value: Any) -> Decimal:
    if (
        not isinstance(value, str)
        or len(value) > RESOURCE_LIMITS["maxStringLength"]
        or _DECIMAL_TEXT_RE.fullmatch(value) is None
    ):
        raise ObligationIntegrityError("timing interval text differs")
    try:
        parsed = Decimal(value)
    except InvalidOperation as exc:
        raise ObligationIntegrityError("timing interval decimal differs") from exc
    if not parsed.is_finite() or parsed < 0:
        raise ObligationIntegrityError("timing interval decimal differs")
    return parsed


def _validate_union_owner(owner: Any, contract: Mapping[str, Any], message: str) -> None:
    discriminator = contract["union"]["discriminator"]
    value = getattr(owner, discriminator)
    branch = next(
        (item for item in contract["union"]["branches"] if item["value"] == value),
        None,
    )
    if branch is None:
        raise ObligationIntegrityError(message)
    if any(getattr(owner, name) is None for name in branch["requiredColumns"]):
        raise ObligationIntegrityError(message)
    if any(getattr(owner, name) is not None for name in branch["forbiddenColumns"]):
        raise ObligationIntegrityError(message)


def _build_timing_recurrence_family(
    *, proposal_id: str, projection_id: str, app_projection_id: str,
    canonical_requirements: Sequence[Mapping[str, Any]],
    evidence_bindings: Mapping[str, str], document_family: ObligationDocumentFamily,
    canonical_documents: Sequence[Mapping[str, Any]],
    document_evidence_bindings: Mapping[str, str],
    requirement_family: ObligationRequirementFamily,
    app_targets: Sequence[ObligationApplicabilityTarget],
    expression_family: ObligationExpressionFamily,
) -> ObligationTimingRecurrenceFamily:
    _validate_timing_recurrence_contract()
    verify_expression_family(
        proposal_id=proposal_id, projection_id=projection_id,
        app_projection_id=app_projection_id,
        canonical_requirements=canonical_requirements,
        evidence_bindings=evidence_bindings, document_family=document_family,
        canonical_documents=canonical_documents,
        document_evidence_bindings=document_evidence_bindings,
        requirement_family=requirement_family, app_targets=app_targets,
        family=expression_family,
    )
    canonical_source, selected = _canonical_requirement_source(canonical_requirements)
    requirements = canonical_source["requirements"]
    occurrences = {
        (row.descriptor_id, row.captures.get("i"), row.captures.get("j")): row
        for row in selected
        if row.descriptor_id in {"T1", "T5I", "R1", "R6", "T5R"}
    }
    requirements_by_ordinal = {
        row.canonical_ordinal: row for row in requirement_family.requirements
    }
    recurrence_roots = {
        row.requirement_node_id: row.semantic_node_id
        for row in expression_family.expressions
        if row.context == "recurrence_condition" and row.expression_path == "/"
    }
    nodes: list[ObligationSemanticNode] = []
    links: list[ObligationEvidenceLink] = []
    timing_groups: list[ObligationTimingGroupOwner] = []
    timing_terms: list[ObligationTimingTermOwner] = []
    recurrences: list[ObligationRecurrenceOwner] = []

    def add_timing(
        *, descriptor_id: str, term_descriptor_id: str, requirement_ordinal: int,
        parent_node_id: str, parent_descriptor_id: str,
    ) -> ObligationSemanticNode:
        occurrence = occurrences[(descriptor_id, requirement_ordinal, None)]
        descriptor = occurrence.descriptor
        value = occurrence.canonical_value
        state = _validate_timing_value(value, known_only=descriptor_id == "R6")
        node = _node_from_occurrence(
            occurrence, proposal_id=proposal_id, projection_id=projection_id,
            parent_node_id=parent_node_id, parent_descriptor_id=parent_descriptor_id,
        )
        nodes.append(node)
        links.extend(_evidence_links(
            proposal_id=proposal_id, projection_id=projection_id,
            semantic_node_id=node.id, evidence_keys=value["evidenceKeys"],
            evidence_policy=descriptor["evidence"], evidence_bindings=evidence_bindings,
        ))
        term_occurrences = sorted(
            (row for (kind, i, _), row in occurrences.items()
             if kind == term_descriptor_id and i == requirement_ordinal),
            key=lambda row: row.captures["j"],
        )
        if state == "known" and not term_occurrences:
            raise ObligationIntegrityError("known timing has no terms")
        if state != "known" and term_occurrences:
            raise ObligationIntegrityError("non-known timing has terms")
        owner = ObligationTimingGroupOwner(
            semantic_node_id=node.id, proposal_id=proposal_id,
            projection_id=projection_id, owner_kind=descriptor["ownerKind"],
            owner_node_id=parent_node_id, state=state,
            logic=value.get("logic"), reason=value.get("reason"),
            temporal_kind=value.get("temporalScope", {}).get("kind"),
            canonical_ordinal=node.canonical_ordinal, term_count=len(term_occurrences),
        )
        _validate_union_owner(owner, _TIMING_OWNER_CONTRACT, "timing union differs")
        timing_groups.append(owner)
        for term_occurrence in term_occurrences:
            term = term_occurrence.canonical_value
            _validate_timing_term_value(term)
            term_node = _node_from_occurrence(
                term_occurrence, proposal_id=proposal_id, projection_id=projection_id,
                parent_node_id=node.id, parent_descriptor_id=descriptor_id,
            )
            nodes.append(term_node)
            links.extend(_evidence_links(
                proposal_id=proposal_id, projection_id=projection_id,
                semantic_node_id=term_node.id, evidence_keys=term["evidenceKeys"],
                evidence_policy=term_occurrence.descriptor["evidence"],
                evidence_bindings=evidence_bindings,
            ))
            timing_terms.append(ObligationTimingTermOwner(
                semantic_node_id=term_node.id, proposal_id=proposal_id,
                projection_id=projection_id, timing_group_node_id=node.id,
                metric=term["metric"], interval_text=term["interval"],
                interval_numeric=_timing_decimal(term["interval"]), unit=term["unit"],
                comparator=term["comparator"], anchor=term["anchor"],
                canonical_ordinal=term_node.canonical_ordinal,
            ))
        return node

    for requirement_ordinal, requirement_value in enumerate(requirements):
        requirement = requirements_by_ordinal[requirement_ordinal]
        initial = add_timing(
            descriptor_id="T1", term_descriptor_id="T5I",
            requirement_ordinal=requirement_ordinal,
            parent_node_id=requirement.semantic_node_id, parent_descriptor_id="Q1",
        )
        if initial.id != requirement.initial_timing_node_id:
            raise ObligationIntegrityError("initial timing root differs")
        recurrence_occurrence = occurrences[("R1", requirement_ordinal, None)]
        recurrence_node = _node_from_occurrence(
            recurrence_occurrence, proposal_id=proposal_id, projection_id=projection_id,
            parent_node_id=requirement.semantic_node_id, parent_descriptor_id="Q1",
        )
        if recurrence_node.id != requirement.recurrence_node_id:
            raise ObligationIntegrityError("recurrence root differs")
        nodes.append(recurrence_node)
        recurrence_value = requirement_value["recurrence"]
        links.extend(_evidence_links(
            proposal_id=proposal_id, projection_id=projection_id,
            semantic_node_id=recurrence_node.id,
            evidence_keys=recurrence_value["evidenceKeys"],
            evidence_policy=recurrence_occurrence.descriptor["evidence"],
            evidence_bindings=evidence_bindings,
        ))
        kind = _validate_recurrence_value(recurrence_value)
        timing_node_id = None
        if kind in {"interval", "conditioned"}:
            recurrence_timing = add_timing(
                descriptor_id="R6", term_descriptor_id="T5R",
                requirement_ordinal=requirement_ordinal,
                parent_node_id=recurrence_node.id, parent_descriptor_id="R1",
            )
            timing_node_id = recurrence_timing.id
        condition_root_node_id = recurrence_roots.get(requirement.semantic_node_id)
        owner = ObligationRecurrenceOwner(
            semantic_node_id=recurrence_node.id, proposal_id=proposal_id,
            projection_id=projection_id, requirement_node_id=requirement.semantic_node_id,
            kind=kind, timing_node_id=timing_node_id,
            condition_root_node_id=condition_root_node_id,
            reason=recurrence_value.get("reason"),
            temporal_kind=recurrence_value.get("temporalScope", {}).get("kind"),
        )
        _validate_union_owner(owner, _RECURRENCE_OWNER_CONTRACT, "recurrence union differs")
        recurrences.append(owner)

    return ObligationTimingRecurrenceFamily(
        proposal_id=proposal_id, projection_id=projection_id,
        semantic_nodes=tuple(nodes), evidence_links=tuple(links),
        timing_groups=tuple(timing_groups), timing_terms=tuple(timing_terms),
        recurrences=tuple(recurrences),
    )


def materialize_timing_recurrence_family(
    *, proposal_id: str, projection_id: str, app_projection_id: str,
    canonical_requirements: Sequence[Mapping[str, Any]],
    evidence_bindings: Mapping[str, str], document_family: ObligationDocumentFamily,
    canonical_documents: Sequence[Mapping[str, Any]],
    document_evidence_bindings: Mapping[str, str],
    requirement_family: ObligationRequirementFamily,
    app_targets: Sequence[ObligationApplicabilityTarget],
    expression_family: ObligationExpressionFamily,
) -> ObligationTimingRecurrenceFamily:
    family = _build_timing_recurrence_family(
        proposal_id=proposal_id, projection_id=projection_id,
        app_projection_id=app_projection_id,
        canonical_requirements=canonical_requirements,
        evidence_bindings=evidence_bindings, document_family=document_family,
        canonical_documents=canonical_documents,
        document_evidence_bindings=document_evidence_bindings,
        requirement_family=requirement_family, app_targets=app_targets,
        expression_family=expression_family,
    )
    verify_timing_recurrence_family(
        proposal_id=proposal_id, projection_id=projection_id,
        app_projection_id=app_projection_id,
        canonical_requirements=canonical_requirements,
        evidence_bindings=evidence_bindings, document_family=document_family,
        canonical_documents=canonical_documents,
        document_evidence_bindings=document_evidence_bindings,
        requirement_family=requirement_family, app_targets=app_targets,
        expression_family=expression_family, family=family,
    )
    return family


def verify_timing_recurrence_family(
    *, proposal_id: str, projection_id: str, app_projection_id: str,
    canonical_requirements: Sequence[Mapping[str, Any]],
    evidence_bindings: Mapping[str, str], document_family: ObligationDocumentFamily,
    canonical_documents: Sequence[Mapping[str, Any]],
    document_evidence_bindings: Mapping[str, str],
    requirement_family: ObligationRequirementFamily,
    app_targets: Sequence[ObligationApplicabilityTarget],
    expression_family: ObligationExpressionFamily,
    family: ObligationTimingRecurrenceFamily,
) -> None:
    numeric_fields = [
        *(node.canonical_ordinal for node in family.semantic_nodes),
        *(link.canonical_ordinal for link in family.evidence_links),
        *(group.canonical_ordinal for group in family.timing_groups),
        *(group.term_count for group in family.timing_groups),
        *(term.canonical_ordinal for term in family.timing_terms),
    ]
    if any(type(value) is not int or value < 0 for value in numeric_fields):
        raise ObligationIntegrityError("timing ordinal/count numeric type differs")
    for term in family.timing_terms:
        if type(term.interval_numeric) is not Decimal:
            raise ObligationIntegrityError("timing interval numeric type differs")
        expected_numeric = _timing_decimal(term.interval_text)
        if (
            not term.interval_numeric.is_finite()
            or term.interval_numeric < 0
            or term.interval_numeric.as_tuple() != expected_numeric.as_tuple()
        ):
            raise ObligationIntegrityError("timing interval numeric representation differs")
    expected = _build_timing_recurrence_family(
        proposal_id=proposal_id, projection_id=projection_id,
        app_projection_id=app_projection_id,
        canonical_requirements=canonical_requirements,
        evidence_bindings=evidence_bindings, document_family=document_family,
        canonical_documents=canonical_documents,
        document_evidence_bindings=document_evidence_bindings,
        requirement_family=requirement_family, app_targets=app_targets,
        expression_family=expression_family,
    )
    if family != expected:
        raise ObligationIntegrityError("timing/recurrence typed projection differs")


def _validate_requirement_relationship_contract() -> None:
    q7 = _Q_DESCRIPTORS["Q7"]
    if (
        q7["nodeType"] != "terminating_effect"
        or q7["key"] != {"op": "source_pointer"}
        or q7["parent"] != {"op": "ancestor", "name": "Q1"}
        or q7["ordinal"] != {"op": "constant", "value": 5}
        or q7["presence"] != "required"
        or q7["ownerTable"] != _TERMINATING_EFFECT_OWNER_CONTRACT["table"]
        or q7["evidence"] != {
            "source": "own", "purpose": "termination_clause",
            "cardinality": "one_or_more", "inheritance": "none",
        }
    ):
        raise ObligationIntegrityError("terminating effect occurrence contract differs")
    if (
        tuple(_TERMINATING_EFFECT_OWNER_CONTRACT["occurrences"]) != ("Q7",)
        or tuple(_TERMINATING_EFFECT_OWNER_CONTRACT["references"]) != ({
            "column": "requirement_node_id", "target": "Q1",
            "targetNodeType": "requirement", "scope": "same_projection",
            "cardinality": "required_one",
        },)
        or tuple(_TERMINATING_EFFECT_OWNER_CONTRACT["children"]) != ({
            "target": "Q9", "cardinality": "zero_or_more",
            "ordering": "canonical_ordinal",
        },)
    ):
        raise ObligationIntegrityError("terminating effect owner contract differs")
    branches = {
        branch["value"]: branch
        for branch in _TERMINATING_EFFECT_OWNER_CONTRACT["union"]["branches"]
    }
    if (
        set(branches) != {"none", "terminates"}
        or tuple(branches["none"]["forbiddenChildren"]) != ("Q9",)
        or tuple(branches["terminates"]["forbiddenChildren"]) != ()
        or any(
            branch["requiredColumns"] or branch["forbiddenColumns"]
            or branch["requiredChildren"]
            for branch in branches.values()
        )
    ):
        raise ObligationIntegrityError("terminating effect union contract differs")
    expected_relationships = {
        "Q9": (
            _TERMINATION_EDGE_RELATIONSHIP,
            "ad_v4_candidate_obligation_termination_edges", "termination-edge", "aot",
            ("projectionId", "effectNodeId", "terminatedRequirementNodeId", "ordinal"),
            "/requirements/{i}/terminatingEffect/requirementKeys/{j}",
        ),
        "Q10": (
            _REQUIREMENT_DEPENDENCY_RELATIONSHIP,
            "ad_v4_candidate_obligation_requirement_dependencies", "requirement-dependency", "aop",
            ("projectionId", "requirementNodeId", "prerequisiteRequirementNodeId", "ordinal"),
            "/requirements/{i}/prerequisiteRequirementKeys/{j}",
        ),
    }
    for relationship_id, (
        relationship, table, label, prefix, properties, pattern,
    ) in expected_relationships.items():
        if relationship != {
            "id": relationship_id, "sourcePattern": pattern, "table": table,
            "tableLabel": label, "idPrefix": prefix,
            "identityProperties": properties, "ordering": "canonical_ordinal",
            "cardinality": "zero_or_more",
        }:
            raise ObligationIntegrityError("requirement relationship contract differs")


def _validate_requirement_relationship_source(
    canonical_requirements: Sequence[Mapping[str, Any]],
) -> None:
    """Validate Q7/Q9/Q10 source shapes before any dependent family rebuild."""
    if not isinstance(canonical_requirements, list):
        raise ObligationIntegrityError("requirement collection is invalid")
    max_items = RESOURCE_LIMITS["maxArrayItems"]
    for requirement in canonical_requirements:
        if type(requirement) is not dict:
            raise ObligationIntegrityError("requirement relationship source is invalid")
        requirement_key = requirement.get("requirementKey")
        if (
            not _is_stable_key(requirement_key)
        ):
            raise ObligationIntegrityError("requirement relationship key is invalid")

        prerequisites = requirement.get("prerequisiteRequirementKeys")
        if (
            not isinstance(prerequisites, list)
            or len(prerequisites) > max_items
            or any(not _is_stable_key(key) for key in prerequisites)
            or len(prerequisites) != len(set(prerequisites))
        ):
            raise ObligationIntegrityError("prerequisite requirement set is invalid")

        effect = requirement.get("terminatingEffect")
        if type(effect) is not dict:
            raise ObligationIntegrityError("terminating effect shape differs")
        kind = effect.get("kind")
        expected_fields = {
            "none": {"kind", "evidenceKeys"},
            "terminates": {"kind", "requirementKeys", "evidenceKeys"},
        }
        if (
            not isinstance(kind, str)
            or kind not in expected_fields
            or set(effect) != expected_fields[kind]
        ):
            raise ObligationIntegrityError("terminating effect shape differs")
        evidence_keys = effect.get("evidenceKeys")
        if (
            not isinstance(evidence_keys, list)
            or not evidence_keys
            or len(evidence_keys) > max_items
            or any(not _is_stable_key(key) for key in evidence_keys)
            or len(evidence_keys) != len(set(evidence_keys))
        ):
            raise ObligationIntegrityError("terminating effect evidence set is invalid")
        terminated = effect.get("requirementKeys", [])
        if (
            not isinstance(terminated, list)
            or len(terminated) > max_items
            or any(not _is_stable_key(key) for key in terminated)
            or len(terminated) != len(set(terminated))
        ):
            raise ObligationIntegrityError("termination requirement set is invalid")


def _build_requirement_relationship_family(
    *, proposal_id: str, projection_id: str, app_projection_id: str,
    canonical_requirements: Sequence[Mapping[str, Any]],
    evidence_bindings: Mapping[str, str], document_family: ObligationDocumentFamily,
    canonical_documents: Sequence[Mapping[str, Any]],
    document_evidence_bindings: Mapping[str, str],
    requirement_family: ObligationRequirementFamily,
    app_targets: Sequence[ObligationApplicabilityTarget],
    expression_family: ObligationExpressionFamily,
) -> ObligationRequirementRelationshipFamily:
    _validate_requirement_relationship_contract()
    _validate_requirement_relationship_source(canonical_requirements)
    verify_expression_family(
        proposal_id=proposal_id, projection_id=projection_id,
        app_projection_id=app_projection_id,
        canonical_requirements=canonical_requirements,
        evidence_bindings=evidence_bindings, document_family=document_family,
        canonical_documents=canonical_documents,
        document_evidence_bindings=document_evidence_bindings,
        requirement_family=requirement_family, app_targets=app_targets,
        family=expression_family,
    )
    canonical_source, selected = _canonical_requirement_source(canonical_requirements)
    requirements = canonical_source["requirements"]
    q7_by_ordinal = {
        occurrence.captures["i"]: occurrence
        for occurrence in selected if occurrence.descriptor_id == "Q7"
    }
    requirements_by_ordinal = {
        owner.canonical_ordinal: owner for owner in requirement_family.requirements
    }
    requirements_by_key = {
        owner.requirement_key: owner for owner in requirement_family.requirements
    }
    nodes: list[ObligationSemanticNode] = []
    links: list[ObligationEvidenceLink] = []
    effects: list[ObligationTerminatingEffectOwner] = []
    termination_edges: list[ObligationTerminationEdge] = []
    dependencies: list[ObligationRequirementDependency] = []

    for requirement_ordinal, requirement_value in enumerate(requirements):
        requirement = requirements_by_ordinal[requirement_ordinal]
        effect_value = requirement_value["terminatingEffect"]
        kind = effect_value["kind"]
        q7 = q7_by_ordinal[requirement_ordinal]
        effect_node = _node_from_occurrence(
            q7, proposal_id=proposal_id, projection_id=projection_id,
            parent_node_id=requirement.semantic_node_id, parent_descriptor_id="Q1",
        )
        if effect_node.id != requirement.terminating_effect_node_id:
            raise ObligationIntegrityError("terminating effect root differs")
        nodes.append(effect_node)
        links.extend(_evidence_links(
            proposal_id=proposal_id, projection_id=projection_id,
            semantic_node_id=effect_node.id,
            evidence_keys=effect_value["evidenceKeys"],
            evidence_policy=q7.descriptor["evidence"], evidence_bindings=evidence_bindings,
        ))
        terminated_keys = effect_value.get("requirementKeys", [])
        for edge_ordinal, target_key in enumerate(terminated_keys):
            target = requirements_by_key.get(target_key)
            if target is None:
                raise ObligationIntegrityError("termination target is unresolved")
            values = {
                "projectionId": projection_id, "effectNodeId": effect_node.id,
                "terminatedRequirementNodeId": target.semantic_node_id,
                "ordinal": edge_ordinal,
            }
            identity = {
                name: values[name]
                for name in _TERMINATION_EDGE_RELATIONSHIP["identityProperties"]
            }
            edge_id, edge_hash = _row_id(
                _TERMINATION_EDGE_RELATIONSHIP["idPrefix"],
                _TERMINATION_EDGE_RELATIONSHIP["tableLabel"], identity,
            )
            termination_edges.append(ObligationTerminationEdge(
                id=edge_id, identity_hash=edge_hash, proposal_id=proposal_id,
                projection_id=projection_id, effect_node_id=effect_node.id,
                terminated_requirement_node_id=target.semantic_node_id,
                terminated_requirement_key=target_key,
                canonical_ordinal=edge_ordinal,
            ))
        effects.append(ObligationTerminatingEffectOwner(
            semantic_node_id=effect_node.id, proposal_id=proposal_id,
            projection_id=projection_id,
            requirement_node_id=requirement.semantic_node_id,
            kind=kind, edge_count=len(terminated_keys),
        ))

        for edge_ordinal, target_key in enumerate(
            requirement_value["prerequisiteRequirementKeys"],
        ):
            target = requirements_by_key.get(target_key)
            if target is None:
                raise ObligationIntegrityError("prerequisite target is unresolved")
            values = {
                "projectionId": projection_id,
                "requirementNodeId": requirement.semantic_node_id,
                "prerequisiteRequirementNodeId": target.semantic_node_id,
                "ordinal": edge_ordinal,
            }
            identity = {
                name: values[name]
                for name in _REQUIREMENT_DEPENDENCY_RELATIONSHIP["identityProperties"]
            }
            edge_id, edge_hash = _row_id(
                _REQUIREMENT_DEPENDENCY_RELATIONSHIP["idPrefix"],
                _REQUIREMENT_DEPENDENCY_RELATIONSHIP["tableLabel"], identity,
            )
            dependencies.append(ObligationRequirementDependency(
                id=edge_id, identity_hash=edge_hash, proposal_id=proposal_id,
                projection_id=projection_id,
                requirement_node_id=requirement.semantic_node_id,
                prerequisite_requirement_node_id=target.semantic_node_id,
                prerequisite_requirement_key=target_key,
                dependency_kind="prerequisite", canonical_ordinal=edge_ordinal,
            ))

    return ObligationRequirementRelationshipFamily(
        proposal_id=proposal_id, projection_id=projection_id,
        semantic_nodes=tuple(nodes), evidence_links=tuple(links),
        terminating_effects=tuple(effects),
        termination_edges=tuple(termination_edges),
        requirement_dependencies=tuple(dependencies),
    )


def materialize_requirement_relationship_family(
    *, proposal_id: str, projection_id: str, app_projection_id: str,
    canonical_requirements: Sequence[Mapping[str, Any]],
    evidence_bindings: Mapping[str, str], document_family: ObligationDocumentFamily,
    canonical_documents: Sequence[Mapping[str, Any]],
    document_evidence_bindings: Mapping[str, str],
    requirement_family: ObligationRequirementFamily,
    app_targets: Sequence[ObligationApplicabilityTarget],
    expression_family: ObligationExpressionFamily,
) -> ObligationRequirementRelationshipFamily:
    family = _build_requirement_relationship_family(
        proposal_id=proposal_id, projection_id=projection_id,
        app_projection_id=app_projection_id,
        canonical_requirements=canonical_requirements,
        evidence_bindings=evidence_bindings, document_family=document_family,
        canonical_documents=canonical_documents,
        document_evidence_bindings=document_evidence_bindings,
        requirement_family=requirement_family, app_targets=app_targets,
        expression_family=expression_family,
    )
    verify_requirement_relationship_family(
        proposal_id=proposal_id, projection_id=projection_id,
        app_projection_id=app_projection_id,
        canonical_requirements=canonical_requirements,
        evidence_bindings=evidence_bindings, document_family=document_family,
        canonical_documents=canonical_documents,
        document_evidence_bindings=document_evidence_bindings,
        requirement_family=requirement_family, app_targets=app_targets,
        expression_family=expression_family, family=family,
    )
    return family


def verify_requirement_relationship_family(
    *, proposal_id: str, projection_id: str, app_projection_id: str,
    canonical_requirements: Sequence[Mapping[str, Any]],
    evidence_bindings: Mapping[str, str], document_family: ObligationDocumentFamily,
    canonical_documents: Sequence[Mapping[str, Any]],
    document_evidence_bindings: Mapping[str, str],
    requirement_family: ObligationRequirementFamily,
    app_targets: Sequence[ObligationApplicabilityTarget],
    expression_family: ObligationExpressionFamily,
    family: ObligationRequirementRelationshipFamily,
) -> None:
    numeric_fields = [
        *(node.canonical_ordinal for node in family.semantic_nodes),
        *(link.canonical_ordinal for link in family.evidence_links),
        *(owner.edge_count for owner in family.terminating_effects),
        *(edge.canonical_ordinal for edge in family.termination_edges),
        *(edge.canonical_ordinal for edge in family.requirement_dependencies),
    ]
    if any(type(value) is not int or value < 0 for value in numeric_fields):
        raise ObligationIntegrityError("requirement relationship numeric type differs")
    expected = _build_requirement_relationship_family(
        proposal_id=proposal_id, projection_id=projection_id,
        app_projection_id=app_projection_id,
        canonical_requirements=canonical_requirements,
        evidence_bindings=evidence_bindings, document_family=document_family,
        canonical_documents=canonical_documents,
        document_evidence_bindings=document_evidence_bindings,
        requirement_family=requirement_family, app_targets=app_targets,
        expression_family=expression_family,
    )
    if family != expected:
        raise ObligationIntegrityError("requirement relationship typed projection differs")


def _validate_recurrence_group_contract() -> None:
    expected_descriptors = {
        "G1": ("recurrence_group", None, None, None, "recurrence_clause"),
        "G3": ("timing_group", "G1", 0, "recurrence_group_initial", "timing_clause"),
        "T5GI": ("timing_term", "G3", None, "recurrence_group_initial", "timing_term_clause"),
        "G4": ("timing_group", "G1", 1, "recurrence_group_recurring", "timing_clause"),
        "T5GR": ("timing_term", "G4", None, "recurrence_group_recurring", "timing_term_clause"),
    }
    contracts = {
        "recurrence_group": _RECURRENCE_GROUP_OWNER_CONTRACT,
        "timing_group": _TIMING_OWNER_CONTRACT,
        "timing_term": _TIMING_TERM_OWNER_CONTRACT,
    }
    for descriptor_id, (
        node_type, parent_id, ordinal, owner_kind, purpose,
    ) in expected_descriptors.items():
        descriptor = _G_DESCRIPTORS[descriptor_id]
        expected_key = (
            {"op": "property", "name": "recurrenceGroupKey"}
            if descriptor_id == "G1" else {"op": "source_pointer"}
        )
        expected_parent = (
            {"op": "root"} if parent_id is None
            else {"op": "ancestor", "name": parent_id}
        )
        expected_ordinal = (
            {"op": "array_ordinal"} if ordinal is None
            else {"op": "constant", "value": ordinal}
        )
        expected_presence = "union" if descriptor_id in {"T5GI", "T5GR"} else "required"
        if (
            descriptor["nodeType"] != node_type
            or descriptor["ownerTable"] != contracts[node_type]["table"]
            or descriptor["key"] != expected_key
            or descriptor["parent"] != expected_parent
            or descriptor["ordinal"] != expected_ordinal
            or descriptor["presence"] != expected_presence
            or descriptor.get("ownerKind") != owner_kind
            or descriptor["evidence"] != {
                "source": "own", "purpose": purpose,
                "cardinality": "one_or_more", "inheritance": "none",
            }
        ):
            raise ObligationIntegrityError("recurrence group occurrence contract differs")
    if (
        tuple(_RECURRENCE_GROUP_OWNER_CONTRACT["occurrences"]) != ("G1",)
        or tuple(_RECURRENCE_GROUP_OWNER_CONTRACT["references"]) != (
            {"column": "initial_timing_node_id", "target": "G3", "targetNodeType": "timing_group", "scope": "same_projection", "cardinality": "required_one"},
            {"column": "recurring_timing_node_id", "target": "G4", "targetNodeType": "timing_group", "scope": "same_projection", "cardinality": "required_one"},
        )
        or tuple(_RECURRENCE_GROUP_OWNER_CONTRACT["children"]) != (
            {"target": "G2", "cardinality": "two_or_more", "ordering": "canonical_ordinal"},
            {"target": "G3", "cardinality": "exactly_one", "ordering": "fixed_slot"},
            {"target": "G4", "cardinality": "exactly_one", "ordering": "fixed_slot"},
        )
    ):
        raise ObligationIntegrityError("recurrence group owner contract differs")
    expected_relationship = {
        "id": "G2",
        "sourcePattern": "/recurrenceGroups/{i}/requirementKeys/{j}",
        "table": "ad_v4_candidate_obligation_recurrence_group_members",
        "tableLabel": "recurrence-group-member", "idPrefix": "aom",
        "identityProperties": (
            "projectionId", "groupNodeId", "requirementNodeId", "ordinal",
        ),
        "ordering": "canonical_ordinal", "cardinality": "zero_or_more",
    }
    if _RECURRENCE_GROUP_MEMBER_RELATIONSHIP != expected_relationship:
        raise ObligationIntegrityError("recurrence group member contract differs")


def _canonical_recurrence_group_source(
    canonical_requirements: Sequence[Mapping[str, Any]],
    canonical_recurrence_groups: Sequence[Mapping[str, Any]],
) -> tuple[dict[str, Any], tuple[Any, ...]]:
    if not isinstance(canonical_requirements, list):
        raise ObligationIntegrityError("requirement collection is invalid")
    if not isinstance(canonical_recurrence_groups, list):
        raise ObligationIntegrityError("recurrence group collection is invalid")
    for requirement in canonical_requirements:
        if type(requirement) is not dict:
            raise ObligationIntegrityError("recurrence group requirement source differs")
        if (
            "recurrenceGroupKey" in requirement
            and not _is_stable_key(requirement["recurrenceGroupKey"])
        ):
            raise ObligationIntegrityError("requirement recurrence group key differs")
    max_items = RESOURCE_LIMITS["maxArrayItems"]
    seen_group_keys: set[str] = set()
    for group in canonical_recurrence_groups:
        if type(group) is not dict or set(group) != {
            "recurrenceGroupKey", "requirementKeys", "completionPolicy",
            "initialTiming", "recurringTiming", "evidenceKeys",
        }:
            raise ObligationIntegrityError("recurrence group shape differs")
        group_key = group["recurrenceGroupKey"]
        if not _is_stable_key(group_key) or group_key in seen_group_keys:
            raise ObligationIntegrityError("recurrence group key set differs")
        seen_group_keys.add(group_key)
        member_keys = group["requirementKeys"]
        if (
            not isinstance(member_keys, list)
            or not 2 <= len(member_keys) <= max_items
            or any(not _is_stable_key(key) for key in member_keys)
            or len(member_keys) != len(set(member_keys))
        ):
            raise ObligationIntegrityError("recurrence group member set differs")
        if group["completionPolicy"] != "all_active_requirements":
            raise ObligationIntegrityError("recurrence group completion policy differs")
        if type(group["initialTiming"]) is not dict or type(group["recurringTiming"]) is not dict:
            raise ObligationIntegrityError("recurrence group timing object differs")
        evidence_keys = group["evidenceKeys"]
        if (
            not isinstance(evidence_keys, list)
            or not evidence_keys
            or len(evidence_keys) > max_items
            or any(not _is_stable_key(key) for key in evidence_keys)
            or len(evidence_keys) != len(set(evidence_keys))
        ):
            raise ObligationIntegrityError("recurrence group evidence set differs")
        for timing_name in ("initialTiming", "recurringTiming"):
            timing = group[timing_name]
            state = _validate_timing_value(timing, known_only=False)
            timing_evidence = timing["evidenceKeys"]
            if (
                not isinstance(timing_evidence, list)
                or not timing_evidence
                or len(timing_evidence) > max_items
                or any(not _is_stable_key(key) for key in timing_evidence)
                or len(timing_evidence) != len(set(timing_evidence))
            ):
                raise ObligationIntegrityError("recurrence group timing evidence set differs")
            if state == "known":
                if len(timing["terms"]) > max_items:
                    raise ObligationIntegrityError("recurrence group timing term set differs")
                for term in timing["terms"]:
                    _validate_timing_term_value(term)
                    term_evidence = term["evidenceKeys"]
                    if (
                        not isinstance(term_evidence, list)
                        or not term_evidence
                        or len(term_evidence) > max_items
                        or any(not _is_stable_key(key) for key in term_evidence)
                        or len(term_evidence) != len(set(term_evidence))
                    ):
                        raise ObligationIntegrityError(
                            "recurrence group timing term evidence set differs"
                        )
    source = {
        "incorporatedDocuments": [],
        "requirements": canonical_requirements,
        "recurrenceGroups": canonical_recurrence_groups,
        "amocAuthorityProvisions": [],
    }
    _validate_source_resources(source)
    canonical_source = json.loads(canonical_bytes(source, CANONICALIZATION_VERSION_V2))
    selected = tuple(
        occurrence for occurrence in select_occurrences(canonical_source)
        if occurrence.descriptor_id in _G_DESCRIPTOR_IDS
    )
    return canonical_source, selected


def _build_recurrence_group_family(
    *, proposal_id: str, projection_id: str, app_projection_id: str,
    canonical_requirements: Sequence[Mapping[str, Any]],
    canonical_recurrence_groups: Sequence[Mapping[str, Any]],
    evidence_bindings: Mapping[str, str], document_family: ObligationDocumentFamily,
    canonical_documents: Sequence[Mapping[str, Any]],
    document_evidence_bindings: Mapping[str, str],
    requirement_family: ObligationRequirementFamily,
    app_targets: Sequence[ObligationApplicabilityTarget],
    expression_family: ObligationExpressionFamily,
    timing_recurrence_family: ObligationTimingRecurrenceFamily,
) -> ObligationRecurrenceGroupFamily:
    _validate_recurrence_group_contract()
    canonical_source, selected = _canonical_recurrence_group_source(
        canonical_requirements, canonical_recurrence_groups,
    )
    verify_timing_recurrence_family(
        proposal_id=proposal_id, projection_id=projection_id,
        app_projection_id=app_projection_id,
        canonical_requirements=canonical_requirements,
        evidence_bindings=evidence_bindings, document_family=document_family,
        canonical_documents=canonical_documents,
        document_evidence_bindings=document_evidence_bindings,
        requirement_family=requirement_family, app_targets=app_targets,
        expression_family=expression_family, family=timing_recurrence_family,
    )
    requirements = canonical_source["requirements"]
    groups = canonical_source["recurrenceGroups"]
    occurrences = {
        (row.descriptor_id, row.captures.get("i"), row.captures.get("j")): row
        for row in selected
    }
    requirements_by_key = {
        row.requirement_key: row for row in requirement_family.requirements
    }
    if len(requirements_by_key) != len(requirements):
        raise ObligationIntegrityError("recurrence group requirement owner set differs")
    declared_memberships: dict[str, str] = {}
    for requirement in requirements:
        requirement_key = requirement["requirementKey"]
        owner = requirements_by_key.get(requirement_key)
        if owner is None:
            raise ObligationIntegrityError("recurrence group requirement owner is missing")
        group_key = requirement.get("recurrenceGroupKey")
        if owner.recurrence_group_present != (group_key is not None) or owner.recurrence_group_key != group_key:
            raise ObligationIntegrityError("requirement recurrence group reference differs")
        if group_key is not None:
            if "logic" in requirement["initialTiming"] or requirement["recurrence"].get("kind") != "none":
                raise ObligationIntegrityError("grouped requirement timing differs")
            declared_memberships[requirement_key] = group_key

    group_memberships: dict[str, str] = {}
    for group in groups:
        for requirement_key in group["requirementKeys"]:
            if requirement_key not in requirements_by_key:
                raise ObligationIntegrityError("recurrence group member is unresolved")
            if requirement_key in group_memberships:
                raise ObligationIntegrityError("duplicate recurrence group membership")
            group_memberships[requirement_key] = group["recurrenceGroupKey"]
    if declared_memberships != group_memberships:
        raise ObligationIntegrityError("recurrence group membership differs")

    nodes: list[ObligationSemanticNode] = []
    links: list[ObligationEvidenceLink] = []
    group_owners: list[ObligationRecurrenceGroupOwner] = []
    members: list[ObligationRecurrenceGroupMember] = []
    timing_groups: list[ObligationTimingGroupOwner] = []
    timing_terms: list[ObligationTimingTermOwner] = []

    def add_timing(
        *, descriptor_id: str, term_descriptor_id: str, group_ordinal: int,
        parent_node_id: str,
    ) -> ObligationSemanticNode:
        occurrence = occurrences[(descriptor_id, group_ordinal, None)]
        descriptor = occurrence.descriptor
        value = occurrence.canonical_value
        state = _validate_timing_value(value, known_only=False)
        node = _node_from_occurrence(
            occurrence, proposal_id=proposal_id, projection_id=projection_id,
            parent_node_id=parent_node_id, parent_descriptor_id="G1",
        )
        nodes.append(node)
        links.extend(_evidence_links(
            proposal_id=proposal_id, projection_id=projection_id,
            semantic_node_id=node.id, evidence_keys=value["evidenceKeys"],
            evidence_policy=descriptor["evidence"], evidence_bindings=evidence_bindings,
        ))
        term_occurrences = sorted(
            (
                row for (kind, index, _), row in occurrences.items()
                if kind == term_descriptor_id and index == group_ordinal
            ),
            key=lambda row: row.captures["j"],
        )
        if state == "known" and not term_occurrences:
            raise ObligationIntegrityError("known group timing has no terms")
        if state != "known" and term_occurrences:
            raise ObligationIntegrityError("non-known group timing has terms")
        owner = ObligationTimingGroupOwner(
            semantic_node_id=node.id, proposal_id=proposal_id,
            projection_id=projection_id, owner_kind=descriptor["ownerKind"],
            owner_node_id=parent_node_id, state=state,
            logic=value.get("logic"), reason=value.get("reason"),
            temporal_kind=value.get("temporalScope", {}).get("kind"),
            canonical_ordinal=node.canonical_ordinal,
            term_count=len(term_occurrences),
        )
        _validate_union_owner(owner, _TIMING_OWNER_CONTRACT, "group timing union differs")
        timing_groups.append(owner)
        for term_occurrence in term_occurrences:
            term = term_occurrence.canonical_value
            _validate_timing_term_value(term)
            term_node = _node_from_occurrence(
                term_occurrence, proposal_id=proposal_id,
                projection_id=projection_id, parent_node_id=node.id,
                parent_descriptor_id=descriptor_id,
            )
            nodes.append(term_node)
            links.extend(_evidence_links(
                proposal_id=proposal_id, projection_id=projection_id,
                semantic_node_id=term_node.id, evidence_keys=term["evidenceKeys"],
                evidence_policy=term_occurrence.descriptor["evidence"],
                evidence_bindings=evidence_bindings,
            ))
            timing_terms.append(ObligationTimingTermOwner(
                semantic_node_id=term_node.id, proposal_id=proposal_id,
                projection_id=projection_id, timing_group_node_id=node.id,
                metric=term["metric"], interval_text=term["interval"],
                interval_numeric=_timing_decimal(term["interval"]), unit=term["unit"],
                comparator=term["comparator"], anchor=term["anchor"],
                canonical_ordinal=term_node.canonical_ordinal,
            ))
        return node

    for group_ordinal, group in enumerate(groups):
        occurrence = occurrences[("G1", group_ordinal, None)]
        group_node = _node_from_occurrence(
            occurrence, proposal_id=proposal_id, projection_id=projection_id,
            parent_node_id=None, parent_descriptor_id=None,
        )
        nodes.append(group_node)
        links.extend(_evidence_links(
            proposal_id=proposal_id, projection_id=projection_id,
            semantic_node_id=group_node.id, evidence_keys=group["evidenceKeys"],
            evidence_policy=occurrence.descriptor["evidence"],
            evidence_bindings=evidence_bindings,
        ))
        initial_node = add_timing(
            descriptor_id="G3", term_descriptor_id="T5GI",
            group_ordinal=group_ordinal, parent_node_id=group_node.id,
        )
        recurring_node = add_timing(
            descriptor_id="G4", term_descriptor_id="T5GR",
            group_ordinal=group_ordinal, parent_node_id=group_node.id,
        )
        member_keys = group["requirementKeys"]
        for member_ordinal, requirement_key in enumerate(member_keys):
            requirement = requirements_by_key[requirement_key]
            values = {
                "projectionId": projection_id, "groupNodeId": group_node.id,
                "requirementNodeId": requirement.semantic_node_id,
                "ordinal": member_ordinal,
            }
            identity = {
                name: values[name]
                for name in _RECURRENCE_GROUP_MEMBER_RELATIONSHIP["identityProperties"]
            }
            member_id, member_hash = _row_id(
                _RECURRENCE_GROUP_MEMBER_RELATIONSHIP["idPrefix"],
                _RECURRENCE_GROUP_MEMBER_RELATIONSHIP["tableLabel"], identity,
            )
            members.append(ObligationRecurrenceGroupMember(
                id=member_id, identity_hash=member_hash,
                proposal_id=proposal_id, projection_id=projection_id,
                group_node_id=group_node.id,
                requirement_node_id=requirement.semantic_node_id,
                requirement_key=requirement_key,
                canonical_ordinal=member_ordinal,
            ))
        group_owners.append(ObligationRecurrenceGroupOwner(
            semantic_node_id=group_node.id, proposal_id=proposal_id,
            projection_id=projection_id,
            recurrence_group_key=group["recurrenceGroupKey"],
            canonical_ordinal=group_ordinal,
            completion_policy=group["completionPolicy"],
            initial_timing_node_id=initial_node.id,
            recurring_timing_node_id=recurring_node.id,
            member_count=len(member_keys),
        ))

    return ObligationRecurrenceGroupFamily(
        proposal_id=proposal_id, projection_id=projection_id,
        semantic_nodes=tuple(nodes), evidence_links=tuple(links),
        recurrence_groups=tuple(group_owners), members=tuple(members),
        timing_groups=tuple(timing_groups), timing_terms=tuple(timing_terms),
    )


def materialize_recurrence_group_family(
    *, proposal_id: str, projection_id: str, app_projection_id: str,
    canonical_requirements: Sequence[Mapping[str, Any]],
    canonical_recurrence_groups: Sequence[Mapping[str, Any]],
    evidence_bindings: Mapping[str, str], document_family: ObligationDocumentFamily,
    canonical_documents: Sequence[Mapping[str, Any]],
    document_evidence_bindings: Mapping[str, str],
    requirement_family: ObligationRequirementFamily,
    app_targets: Sequence[ObligationApplicabilityTarget],
    expression_family: ObligationExpressionFamily,
    timing_recurrence_family: ObligationTimingRecurrenceFamily,
) -> ObligationRecurrenceGroupFamily:
    family = _build_recurrence_group_family(
        proposal_id=proposal_id, projection_id=projection_id,
        app_projection_id=app_projection_id,
        canonical_requirements=canonical_requirements,
        canonical_recurrence_groups=canonical_recurrence_groups,
        evidence_bindings=evidence_bindings, document_family=document_family,
        canonical_documents=canonical_documents,
        document_evidence_bindings=document_evidence_bindings,
        requirement_family=requirement_family, app_targets=app_targets,
        expression_family=expression_family,
        timing_recurrence_family=timing_recurrence_family,
    )
    verify_recurrence_group_family(
        proposal_id=proposal_id, projection_id=projection_id,
        app_projection_id=app_projection_id,
        canonical_requirements=canonical_requirements,
        canonical_recurrence_groups=canonical_recurrence_groups,
        evidence_bindings=evidence_bindings, document_family=document_family,
        canonical_documents=canonical_documents,
        document_evidence_bindings=document_evidence_bindings,
        requirement_family=requirement_family, app_targets=app_targets,
        expression_family=expression_family,
        timing_recurrence_family=timing_recurrence_family, family=family,
    )
    return family


def verify_recurrence_group_family(
    *, proposal_id: str, projection_id: str, app_projection_id: str,
    canonical_requirements: Sequence[Mapping[str, Any]],
    canonical_recurrence_groups: Sequence[Mapping[str, Any]],
    evidence_bindings: Mapping[str, str], document_family: ObligationDocumentFamily,
    canonical_documents: Sequence[Mapping[str, Any]],
    document_evidence_bindings: Mapping[str, str],
    requirement_family: ObligationRequirementFamily,
    app_targets: Sequence[ObligationApplicabilityTarget],
    expression_family: ObligationExpressionFamily,
    timing_recurrence_family: ObligationTimingRecurrenceFamily,
    family: ObligationRecurrenceGroupFamily,
) -> None:
    numeric_fields = [
        *(node.canonical_ordinal for node in family.semantic_nodes),
        *(link.canonical_ordinal for link in family.evidence_links),
        *(group.canonical_ordinal for group in family.recurrence_groups),
        *(group.member_count for group in family.recurrence_groups),
        *(member.canonical_ordinal for member in family.members),
        *(group.canonical_ordinal for group in family.timing_groups),
        *(group.term_count for group in family.timing_groups),
        *(term.canonical_ordinal for term in family.timing_terms),
    ]
    if any(type(value) is not int or value < 0 for value in numeric_fields):
        raise ObligationIntegrityError("recurrence group ordinal/count numeric type differs")
    for term in family.timing_terms:
        if type(term.interval_numeric) is not Decimal:
            raise ObligationIntegrityError("recurrence group interval numeric type differs")
        expected_numeric = _timing_decimal(term.interval_text)
        if (
            not term.interval_numeric.is_finite()
            or term.interval_numeric < 0
            or term.interval_numeric.as_tuple() != expected_numeric.as_tuple()
        ):
            raise ObligationIntegrityError("recurrence group interval numeric representation differs")
    expected = _build_recurrence_group_family(
        proposal_id=proposal_id, projection_id=projection_id,
        app_projection_id=app_projection_id,
        canonical_requirements=canonical_requirements,
        canonical_recurrence_groups=canonical_recurrence_groups,
        evidence_bindings=evidence_bindings, document_family=document_family,
        canonical_documents=canonical_documents,
        document_evidence_bindings=document_evidence_bindings,
        requirement_family=requirement_family, app_targets=app_targets,
        expression_family=expression_family,
        timing_recurrence_family=timing_recurrence_family,
    )
    if family != expected:
        raise ObligationIntegrityError("recurrence group typed projection differs")


def _validate_authority_contract() -> None:
    a1 = _A_DESCRIPTORS["A1"]
    a2 = _A_DESCRIPTORS["A2"]
    expected_evidence = {
        "source": "own", "purpose": "amoc_authority_clause",
        "cardinality": "one_or_more", "inheritance": "none",
    }
    if (
        a1["nodeType"] != "amoc_provision"
        or a1["key"] != {"op": "property", "name": "provisionKey"}
        or a1["parent"] != {"op": "root"}
        or a1["ordinal"] != {"op": "array_ordinal"}
        or a1["presence"] != "required"
        or a1["ownerTable"] != _AMOC_PROVISION_OWNER_CONTRACT["table"]
        or a1["evidence"] != expected_evidence
        or a2["nodeType"] != "value_assertion"
        or a2["key"] != {"op": "source_pointer"}
        or a2["parent"] != {"op": "ancestor", "name": "A1"}
        or a2["ordinal"] != {"op": "constant", "value": 0}
        or a2["presence"] != "required"
        or a2["ownerKind"] != "approving_authority"
        or a2["ownerTable"] != _ASSERTION_OWNER_CONTRACT["table"]
        or a2["evidence"] != expected_evidence
    ):
        raise ObligationIntegrityError("AMOC authority occurrence contract differs")
    if (
        tuple(_AMOC_PROVISION_OWNER_CONTRACT["occurrences"]) != ("A1",)
        or tuple(_AMOC_PROVISION_OWNER_CONTRACT["references"]) != ({
            "column": "authority_assertion_node_id", "target": "A2",
            "targetNodeType": "value_assertion", "scope": "same_projection",
            "cardinality": "required_one",
        },)
        or tuple(_AMOC_PROVISION_OWNER_CONTRACT["children"]) != ({
            "target": "A2", "cardinality": "exactly_one",
            "ordering": "fixed_slot",
        },)
        or "A2" not in _ASSERTION_OWNER_CONTRACT["occurrences"]
    ):
        raise ObligationIntegrityError("AMOC authority owner contract differs")


def _validate_authority_assertion_source(value: Any) -> None:
    if type(value) is not dict:
        raise ObligationIntegrityError("authority assertion source object differs")
    state = value.get("state")
    if not isinstance(state, str) or state not in _ASSERTION_STATES:
        raise ObligationIntegrityError("authority assertion state differs")
    if state == "known":
        if (
            set(value) != {"state", "value", "evidenceKeys"}
            or not isinstance(value["value"], str)
            or not 1 <= len(value["value"]) <= 512
        ):
            raise ObligationIntegrityError("known authority assertion differs")
    else:
        if set(value) != {"state", "reason", "temporalScope", "evidenceKeys"}:
            raise ObligationIntegrityError("non-known authority assertion differs")
        reason = value["reason"]
        temporal = value["temporalScope"]
        if (
            not isinstance(reason, str)
            or not 1 <= len(reason) <= 512
            or (state == "unknown" and reason not in _UNKNOWN_REASONS)
            or type(temporal) is not dict
            or set(temporal) != {"kind"}
            or not isinstance(temporal["kind"], str)
            or temporal["kind"] not in _TEMPORAL_KINDS
        ):
            raise ObligationIntegrityError("non-known authority assertion differs")
    evidence_keys = value["evidenceKeys"]
    if (
        not isinstance(evidence_keys, list)
        or not evidence_keys
        or len(evidence_keys) > RESOURCE_LIMITS["maxArrayItems"]
        or any(not _is_stable_key(key) for key in evidence_keys)
        or len(evidence_keys) != len(set(evidence_keys))
    ):
        raise ObligationIntegrityError("authority assertion evidence set differs")


def _canonical_authority_source(
    canonical_provisions: Sequence[Mapping[str, Any]],
) -> tuple[dict[str, Any], tuple[Any, ...]]:
    if not isinstance(canonical_provisions, list):
        raise ObligationIntegrityError("AMOC authority collection is invalid")
    seen_keys: set[str] = set()
    for provision in canonical_provisions:
        if type(provision) is not dict or set(provision) != {
            "provisionKey", "approvingAuthority", "evidenceKeys",
        }:
            raise ObligationIntegrityError("AMOC authority provision shape differs")
        provision_key = provision["provisionKey"]
        if not _is_stable_key(provision_key) or provision_key in seen_keys:
            raise ObligationIntegrityError("AMOC authority provision key set differs")
        seen_keys.add(provision_key)
        evidence_keys = provision["evidenceKeys"]
        if (
            not isinstance(evidence_keys, list)
            or not evidence_keys
            or len(evidence_keys) > RESOURCE_LIMITS["maxArrayItems"]
            or any(not _is_stable_key(key) for key in evidence_keys)
            or len(evidence_keys) != len(set(evidence_keys))
        ):
            raise ObligationIntegrityError("AMOC authority evidence set differs")
        _validate_authority_assertion_source(provision["approvingAuthority"])
    source = {
        "incorporatedDocuments": [], "requirements": [],
        "recurrenceGroups": [], "amocAuthorityProvisions": canonical_provisions,
    }
    _validate_source_resources(source)
    canonical_source = json.loads(canonical_bytes(source, CANONICALIZATION_VERSION_V2))
    selected = tuple(
        occurrence for occurrence in select_occurrences(canonical_source)
        if occurrence.descriptor_id in _A_DESCRIPTOR_IDS
    )
    return canonical_source, selected


def _build_authority_family(
    *, proposal_id: str, projection_id: str,
    canonical_provisions: Sequence[Mapping[str, Any]],
    evidence_bindings: Mapping[str, str],
) -> ObligationAuthorityFamily:
    _validate_authority_contract()
    canonical_source, selected = _canonical_authority_source(canonical_provisions)
    provisions = canonical_source["amocAuthorityProvisions"]
    occurrences = {
        (row.descriptor_id, row.captures["i"]): row for row in selected
    }
    nodes: list[ObligationSemanticNode] = []
    links: list[ObligationEvidenceLink] = []
    owners: list[ObligationAmocProvisionOwner] = []
    assertions: list[ObligationValueAssertionOwner] = []
    for ordinal, provision in enumerate(provisions):
        a1 = occurrences[("A1", ordinal)]
        provision_node = _node_from_occurrence(
            a1, proposal_id=proposal_id, projection_id=projection_id,
            parent_node_id=None, parent_descriptor_id=None,
        )
        nodes.append(provision_node)
        links.extend(_evidence_links(
            proposal_id=proposal_id, projection_id=projection_id,
            semantic_node_id=provision_node.id,
            evidence_keys=provision["evidenceKeys"],
            evidence_policy=a1.descriptor["evidence"],
            evidence_bindings=evidence_bindings,
        ))
        a2 = occurrences[("A2", ordinal)]
        assertion_value = provision["approvingAuthority"]
        assertion_node = _node_from_occurrence(
            a2, proposal_id=proposal_id, projection_id=projection_id,
            parent_node_id=provision_node.id, parent_descriptor_id="A1",
        )
        nodes.append(assertion_node)
        links.extend(_evidence_links(
            proposal_id=proposal_id, projection_id=projection_id,
            semantic_node_id=assertion_node.id,
            evidence_keys=assertion_value["evidenceKeys"],
            evidence_policy=a2.descriptor["evidence"],
            evidence_bindings=evidence_bindings,
        ))
        assertion = _assertion_owner(
            node=assertion_node, descriptor=a2.descriptor,
            value=assertion_value,
        )
        if assertion.field_code != "approving_authority":
            raise ObligationIntegrityError("authority assertion field differs")
        assertions.append(assertion)
        owners.append(ObligationAmocProvisionOwner(
            semantic_node_id=provision_node.id, proposal_id=proposal_id,
            projection_id=projection_id, provision_key=provision["provisionKey"],
            canonical_ordinal=ordinal,
            authority_assertion_node_id=assertion_node.id,
        ))
    return ObligationAuthorityFamily(
        proposal_id=proposal_id, projection_id=projection_id,
        semantic_nodes=tuple(nodes), evidence_links=tuple(links),
        amoc_provisions=tuple(owners), value_assertions=tuple(assertions),
    )


def materialize_authority_family(
    *, proposal_id: str, projection_id: str,
    canonical_provisions: Sequence[Mapping[str, Any]],
    evidence_bindings: Mapping[str, str],
) -> ObligationAuthorityFamily:
    family = _build_authority_family(
        proposal_id=proposal_id, projection_id=projection_id,
        canonical_provisions=canonical_provisions,
        evidence_bindings=evidence_bindings,
    )
    verify_authority_family(
        proposal_id=proposal_id, projection_id=projection_id,
        canonical_provisions=canonical_provisions,
        evidence_bindings=evidence_bindings, family=family,
    )
    return family


def _require_row_collection(
    value: Any, row_type: type[Any], label: str, *, allow_list: bool = False,
) -> None:
    allowed_container_types = (tuple, list) if allow_list else (tuple,)
    if type(value) not in allowed_container_types or any(
        type(row) is not row_type for row in value
    ):
        raise ObligationIntegrityError(f"{label} row collection differs")


def verify_authority_family(
    *, proposal_id: str, projection_id: str,
    canonical_provisions: Sequence[Mapping[str, Any]],
    evidence_bindings: Mapping[str, str], family: ObligationAuthorityFamily,
) -> None:
    if type(family) is not ObligationAuthorityFamily:
        raise ObligationIntegrityError("AMOC authority family type differs")
    _require_row_collection(
        family.semantic_nodes, ObligationSemanticNode,
        "AMOC authority semantic-node",
    )
    _require_row_collection(
        family.evidence_links, ObligationEvidenceLink,
        "AMOC authority evidence-link",
    )
    _require_row_collection(
        family.amoc_provisions, ObligationAmocProvisionOwner,
        "AMOC authority provision-owner",
    )
    _require_row_collection(
        family.value_assertions, ObligationValueAssertionOwner,
        "AMOC authority assertion-owner",
    )
    numeric_fields = [
        *(node.canonical_ordinal for node in family.semantic_nodes),
        *(link.canonical_ordinal for link in family.evidence_links),
        *(owner.canonical_ordinal for owner in family.amoc_provisions),
    ]
    if any(type(value) is not int or value < 0 for value in numeric_fields):
        raise ObligationIntegrityError("AMOC authority ordinal numeric type differs")
    expected = _build_authority_family(
        proposal_id=proposal_id, projection_id=projection_id,
        canonical_provisions=canonical_provisions,
        evidence_bindings=evidence_bindings,
    )
    if family != expected:
        raise ObligationIntegrityError("AMOC authority typed projection differs")


def _validate_correction_binding_contract() -> None:
    expected = {
        "id": "CB",
        "sourcePattern": "/authoritativeCorrections/{i}/changedSemanticRefs/{j}[owner_slice=slice_3b]",
        "table": "ad_v4_candidate_correction_semantic_bindings",
        "tableLabel": "correction-binding", "idPrefix": "avk",
        "identityProperties": ("refId", "semanticId"),
        "ordering": "unique_reference", "cardinality": "exactly_one_per_reference",
    }
    expected_owners = {
        "directiveIdentity": "foundation",
        "supersessionRelations": "foundation",
        "productScopes": "slice_3a",
        "conditionDefinitions": "slice_3a",
        "applicabilityRules": "slice_3a",
        "requirements": "slice_3b",
        "recurrenceGroups": "slice_3b",
        "amocAuthorityProvisions": "slice_3b",
    }
    expected_target_types = {
        "productScopes": "product_scope",
        "conditionDefinitions": "condition",
        "applicabilityRules": "applicability_rule",
        "requirements": "requirement",
        "recurrenceGroups": "recurrence_group",
        "amocAuthorityProvisions": "amoc_provision",
    }
    expected_domain_keys = {
        "correctionRoot": "legacyApplicabilityRow",
        "correctionReference": "legacyApplicabilityRow",
        "slice3aBinding": "legacyApplicabilityRow",
        "slice3bBinding": "row",
    }
    if (
        _CORRECTION_BINDING_RELATIONSHIP != expected
        or _CORRECTION_OWNER_BY_NAMESPACE != expected_owners
        or _CORRECTION_TARGET_TYPE_BY_NAMESPACE != expected_target_types
        or dict(_CORRECTION_IDENTITY_DOMAIN_KEYS) != expected_domain_keys
        or DOMAINS[expected_domain_keys["correctionRoot"]] != _APP_ROW_DOMAIN
        or DOMAINS[expected_domain_keys["correctionReference"]] != _APP_ROW_DOMAIN
        or DOMAINS[expected_domain_keys["slice3aBinding"]] != _APP_ROW_DOMAIN
        or DOMAINS[expected_domain_keys["slice3bBinding"]] != DOMAINS["row"]
    ):
        raise ObligationIntegrityError("correction binding contract differs")


def _canonical_corrections(
    canonical_corrections: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    if not isinstance(canonical_corrections, list):
        raise ObligationIntegrityError("correction collection is invalid")
    max_items = RESOURCE_LIMITS["maxArrayItems"]
    seen_correction_keys: set[str] = set()
    for correction in canonical_corrections:
        if type(correction) is not dict or set(correction) != {
            "correctionKey", "correctionType", "originalDocumentRefKey",
            "correctingDocumentRefKey", "changedSemanticRefs", "evidenceKeys",
        }:
            raise ObligationIntegrityError("correction source shape differs")
        correction_key = correction["correctionKey"]
        if not _is_stable_key(correction_key) or correction_key in seen_correction_keys:
            raise ObligationIntegrityError("correction key set differs")
        seen_correction_keys.add(correction_key)
        if correction["correctionType"] != "official_correction":
            raise ObligationIntegrityError("correction type differs")
        if not _is_stable_key(correction["originalDocumentRefKey"]) or not _is_stable_key(
            correction["correctingDocumentRefKey"]
        ):
            raise ObligationIntegrityError("correction document key differs")
        refs = correction["changedSemanticRefs"]
        if not isinstance(refs, list) or not refs or len(refs) > max_items:
            raise ObligationIntegrityError("correction reference set differs")
        seen_refs: set[tuple[str, str]] = set()
        for ref in refs:
            if type(ref) is not dict or set(ref) != {"namespace", "key"}:
                raise ObligationIntegrityError("correction reference shape differs")
            namespace = ref["namespace"]
            semantic_key = ref["key"]
            if (
                not isinstance(namespace, str)
                or namespace not in _CORRECTION_OWNER_BY_NAMESPACE
                or not _is_stable_key(semantic_key)
                or (namespace, semantic_key) in seen_refs
            ):
                raise ObligationIntegrityError("correction reference value differs")
            seen_refs.add((namespace, semantic_key))
        evidence_keys = correction["evidenceKeys"]
        if (
            not isinstance(evidence_keys, list)
            or not evidence_keys
            or len(evidence_keys) > max_items
            or any(not _is_stable_key(key) for key in evidence_keys)
            or len(evidence_keys) != len(set(evidence_keys))
        ):
            raise ObligationIntegrityError("correction evidence set differs")
    source = {"authoritativeCorrections": canonical_corrections}
    _validate_source_resources(source)
    return json.loads(canonical_bytes(source, CANONICALIZATION_VERSION_V2))[
        "authoritativeCorrections"
    ]


def build_correction_reference_snapshot(
    *, proposal_id: str,
    canonical_corrections: Sequence[Mapping[str, Any]],
) -> tuple[ObligationCorrectionReference, ...]:
    """Build the complete neutral correction-ref surface expected from Slice 3A."""
    _validate_correction_binding_contract()
    corrections = _canonical_corrections(canonical_corrections)
    result: list[ObligationCorrectionReference] = []
    for correction in corrections:
        correction_id, _ = _app_row_id(
            "avc", "correction", {
                "proposalId": proposal_id,
                "correctionKey": correction["correctionKey"],
            },
        )
        for ordinal, ref in enumerate(correction["changedSemanticRefs"]):
            identity = {
                "correctionId": correction_id,
                "namespace": ref["namespace"], "key": ref["key"],
            }
            ref_id, ref_hash = _app_row_id("avf", "correction-ref", identity)
            result.append(ObligationCorrectionReference(
                id=ref_id, correction_id=correction_id, proposal_id=proposal_id,
                canonical_ordinal=ordinal, namespace=ref["namespace"],
                semantic_key=ref["key"],
                owner_slice=_CORRECTION_OWNER_BY_NAMESPACE[ref["namespace"]],
                reference_hash=ref_hash,
            ))
    return tuple(result)


def _build_correction_binding_family(
    *, proposal_id: str, projection_id: str, app_projection_id: str,
    canonical_corrections: Sequence[Mapping[str, Any]],
    foundation_refs: Sequence[ObligationCorrectionReference],
    canonical_requirements: Sequence[Mapping[str, Any]],
    canonical_recurrence_groups: Sequence[Mapping[str, Any]],
    canonical_provisions: Sequence[Mapping[str, Any]],
    evidence_bindings: Mapping[str, str], document_family: ObligationDocumentFamily,
    canonical_documents: Sequence[Mapping[str, Any]],
    document_evidence_bindings: Mapping[str, str],
    requirement_family: ObligationRequirementFamily,
    app_targets: Sequence[ObligationApplicabilityTarget],
    expression_family: ObligationExpressionFamily,
    timing_recurrence_family: ObligationTimingRecurrenceFamily,
    recurrence_group_family: ObligationRecurrenceGroupFamily,
    authority_family: ObligationAuthorityFamily,
) -> ObligationCorrectionBindingFamily:
    _validate_correction_binding_contract()
    _require_row_collection(
        foundation_refs, ObligationCorrectionReference,
        "correction reference foundation", allow_list=True,
    )
    verify_recurrence_group_family(
        proposal_id=proposal_id, projection_id=projection_id,
        app_projection_id=app_projection_id,
        canonical_requirements=canonical_requirements,
        canonical_recurrence_groups=canonical_recurrence_groups,
        evidence_bindings=evidence_bindings, document_family=document_family,
        canonical_documents=canonical_documents,
        document_evidence_bindings=document_evidence_bindings,
        requirement_family=requirement_family, app_targets=app_targets,
        expression_family=expression_family,
        timing_recurrence_family=timing_recurrence_family,
        family=recurrence_group_family,
    )
    verify_authority_family(
        proposal_id=proposal_id, projection_id=projection_id,
        canonical_provisions=canonical_provisions,
        evidence_bindings=evidence_bindings, family=authority_family,
    )
    expected_refs = build_correction_reference_snapshot(
        proposal_id=proposal_id, canonical_corrections=canonical_corrections,
    )
    if any(
        type(ref.canonical_ordinal) is not int or ref.canonical_ordinal < 0
        for ref in foundation_refs
    ):
        raise ObligationIntegrityError("correction reference ordinal numeric type differs")
    if tuple(foundation_refs) != expected_refs:
        raise ObligationIntegrityError("correction reference foundation differs")

    targets = {
        ("requirements", row.requirement_key): (
            "requirement", row.semantic_node_id,
        )
        for row in requirement_family.requirements
    }
    targets.update({
        ("recurrenceGroups", row.recurrence_group_key): (
            "recurrence_group", row.semantic_node_id,
        )
        for row in recurrence_group_family.recurrence_groups
    })
    targets.update({
        ("amocAuthorityProvisions", row.provision_key): (
            "amoc_provision", row.semantic_node_id,
        )
        for row in authority_family.amoc_provisions
    })
    semantic_nodes = {
        node.id: node
        for node in (
            *requirement_family.semantic_nodes,
            *recurrence_group_family.semantic_nodes,
            *authority_family.semantic_nodes,
        )
    }
    bindings: list[ObligationCorrectionSemanticBinding] = []
    for ref in expected_refs:
        if ref.owner_slice != "slice_3b":
            continue
        target = targets.get((ref.namespace, ref.semantic_key))
        if target is None:
            raise ObligationIntegrityError("correction Slice-3B target is unresolved")
        expected_type, semantic_id = target
        semantic = semantic_nodes.get(semantic_id)
        if (
            semantic is None
            or semantic.proposal_id != proposal_id
            or semantic.projection_id != projection_id
            or semantic.node_type != expected_type
            or semantic.node_key != ref.semantic_key
        ):
            raise ObligationIntegrityError("correction Slice-3B target differs")
        identity = {"refId": ref.id, "semanticId": semantic.id}
        binding_id, binding_hash = _row_id(
            _CORRECTION_BINDING_RELATIONSHIP["idPrefix"],
            _CORRECTION_BINDING_RELATIONSHIP["tableLabel"], identity,
        )
        bindings.append(ObligationCorrectionSemanticBinding(
            id=binding_id, correction_ref_id=ref.id, proposal_id=proposal_id,
            projection_id=None, semantic_node_id=None,
            obligation_projection_id=projection_id,
            obligation_semantic_node_id=semantic.id,
            binding_slice="slice_3b", generation=1,
            binding_hash=binding_hash,
        ))
    normalized = sorted(
        ({
            "bindingId": row.id, "bindingHash": row.binding_hash,
            "bindingSlice": row.binding_slice, "generation": row.generation,
            "correctionRefId": row.correction_ref_id,
            "targetProjectionId": row.obligation_projection_id,
            "targetSemanticNodeId": row.obligation_semantic_node_id,
        } for row in bindings),
        key=lambda row: (
            row["correctionRefId"], row["bindingSlice"],
            row["targetSemanticNodeId"],
        ),
    )
    binding_set_bytes = obligation_record_bytes(normalized)
    binding_set_hash = hashlib.sha256(
        DOMAINS["correctionBindingSet"] + binding_set_bytes
    ).hexdigest()
    return ObligationCorrectionBindingFamily(
        proposal_id=proposal_id, projection_id=projection_id,
        bindings=tuple(bindings), binding_set_bytes=binding_set_bytes,
        binding_set_hash=binding_set_hash,
    )


def materialize_correction_binding_family(
    *, proposal_id: str, projection_id: str, app_projection_id: str,
    canonical_corrections: Sequence[Mapping[str, Any]],
    foundation_refs: Sequence[ObligationCorrectionReference],
    canonical_requirements: Sequence[Mapping[str, Any]],
    canonical_recurrence_groups: Sequence[Mapping[str, Any]],
    canonical_provisions: Sequence[Mapping[str, Any]],
    evidence_bindings: Mapping[str, str], document_family: ObligationDocumentFamily,
    canonical_documents: Sequence[Mapping[str, Any]],
    document_evidence_bindings: Mapping[str, str],
    requirement_family: ObligationRequirementFamily,
    app_targets: Sequence[ObligationApplicabilityTarget],
    expression_family: ObligationExpressionFamily,
    timing_recurrence_family: ObligationTimingRecurrenceFamily,
    recurrence_group_family: ObligationRecurrenceGroupFamily,
    authority_family: ObligationAuthorityFamily,
) -> ObligationCorrectionBindingFamily:
    family = _build_correction_binding_family(
        proposal_id=proposal_id, projection_id=projection_id,
        app_projection_id=app_projection_id,
        canonical_corrections=canonical_corrections,
        foundation_refs=foundation_refs,
        canonical_requirements=canonical_requirements,
        canonical_recurrence_groups=canonical_recurrence_groups,
        canonical_provisions=canonical_provisions,
        evidence_bindings=evidence_bindings,
        document_family=document_family,
        canonical_documents=canonical_documents,
        document_evidence_bindings=document_evidence_bindings,
        requirement_family=requirement_family, app_targets=app_targets,
        expression_family=expression_family,
        timing_recurrence_family=timing_recurrence_family,
        recurrence_group_family=recurrence_group_family,
        authority_family=authority_family,
    )
    verify_correction_binding_family(
        proposal_id=proposal_id, projection_id=projection_id,
        app_projection_id=app_projection_id,
        canonical_corrections=canonical_corrections,
        foundation_refs=foundation_refs,
        canonical_requirements=canonical_requirements,
        canonical_recurrence_groups=canonical_recurrence_groups,
        canonical_provisions=canonical_provisions,
        evidence_bindings=evidence_bindings,
        document_family=document_family,
        canonical_documents=canonical_documents,
        document_evidence_bindings=document_evidence_bindings,
        requirement_family=requirement_family, app_targets=app_targets,
        expression_family=expression_family,
        timing_recurrence_family=timing_recurrence_family,
        recurrence_group_family=recurrence_group_family,
        authority_family=authority_family, family=family,
    )
    return family


def verify_correction_binding_family(
    *, proposal_id: str, projection_id: str, app_projection_id: str,
    canonical_corrections: Sequence[Mapping[str, Any]],
    foundation_refs: Sequence[ObligationCorrectionReference],
    canonical_requirements: Sequence[Mapping[str, Any]],
    canonical_recurrence_groups: Sequence[Mapping[str, Any]],
    canonical_provisions: Sequence[Mapping[str, Any]],
    evidence_bindings: Mapping[str, str], document_family: ObligationDocumentFamily,
    canonical_documents: Sequence[Mapping[str, Any]],
    document_evidence_bindings: Mapping[str, str],
    requirement_family: ObligationRequirementFamily,
    app_targets: Sequence[ObligationApplicabilityTarget],
    expression_family: ObligationExpressionFamily,
    timing_recurrence_family: ObligationTimingRecurrenceFamily,
    recurrence_group_family: ObligationRecurrenceGroupFamily,
    authority_family: ObligationAuthorityFamily,
    family: ObligationCorrectionBindingFamily,
) -> None:
    if type(family) is not ObligationCorrectionBindingFamily:
        raise ObligationIntegrityError("correction binding family type differs")
    _require_row_collection(
        family.bindings, ObligationCorrectionSemanticBinding,
        "correction binding", allow_list=True,
    )
    if any(
        type(binding.generation) is not int or binding.generation != 1
        for binding in family.bindings
    ):
        raise ObligationIntegrityError("correction binding generation numeric type differs")
    if type(family.binding_set_bytes) is not bytes:
        raise ObligationIntegrityError("correction binding set bytes type differs")
    expected = _build_correction_binding_family(
        proposal_id=proposal_id, projection_id=projection_id,
        app_projection_id=app_projection_id,
        canonical_corrections=canonical_corrections,
        foundation_refs=foundation_refs,
        canonical_requirements=canonical_requirements,
        canonical_recurrence_groups=canonical_recurrence_groups,
        canonical_provisions=canonical_provisions,
        evidence_bindings=evidence_bindings,
        document_family=document_family,
        canonical_documents=canonical_documents,
        document_evidence_bindings=document_evidence_bindings,
        requirement_family=requirement_family, app_targets=app_targets,
        expression_family=expression_family,
        timing_recurrence_family=timing_recurrence_family,
        recurrence_group_family=recurrence_group_family,
        authority_family=authority_family,
    )
    if family != expected:
        raise ObligationIntegrityError("correction binding typed projection differs")


def _build_obligation_datums(
    *, proposal_id: str, projection_id: str, subtree: Mapping[str, Any],
    semantic_nodes: Sequence[ObligationSemanticNode],
) -> tuple[ObligationDatum, ...]:
    nodes_by_pointer = {node.source_pointer: node for node in semantic_nodes}
    if len(nodes_by_pointer) != len(semantic_nodes):
        raise ObligationIntegrityError("semantic source pointer set differs")
    rows: list[ObligationDatum] = []

    def walk(
        value: Any, *, pointer: str, parent_pointer: str | None,
        property_name: str | None, array_ordinal: int | None,
        owner_node_id: str | None,
    ) -> None:
        node = nodes_by_pointer.get(pointer)
        current_owner = node.id if node is not None else owner_node_id
        if type(value) is dict:
            kind = "object"
            identity_value: Any = kind
            string_value = None
            boolean_value = None
        elif type(value) is list:
            kind = "array"
            identity_value = kind
            string_value = None
            boolean_value = None
        elif type(value) is str:
            kind = "string"
            identity_value = value
            string_value = value
            boolean_value = None
        elif type(value) is bool:
            kind = "boolean"
            identity_value = value
            string_value = None
            boolean_value = value
        else:
            raise ObligationIntegrityError("obligation datum value kind differs")
        identity = {
            "projectionId": projection_id,
            "pointer": pointer,
            "kind": kind,
            "value": identity_value,
        }
        row_id, row_hash = _row_id("aod", "datum", identity)
        rows.append(ObligationDatum(
            id=row_id, identity_hash=row_hash, proposal_id=proposal_id,
            projection_id=projection_id, semantic_node_id=current_owner,
            json_pointer=pointer, parent_pointer=parent_pointer,
            property_name=property_name, array_ordinal=array_ordinal,
            value_kind=kind, string_value=string_value,
            boolean_value=boolean_value, value_hash=row_hash,
        ))
        if type(value) is dict:
            for key in sorted(value, key=_utf16_sort_key):
                escaped = key.replace("~", "~0").replace("/", "~1")
                child_pointer = f"{pointer}/{escaped}" if pointer else f"/{escaped}"
                walk(
                    value[key], pointer=child_pointer, parent_pointer=pointer,
                    property_name=key, array_ordinal=None,
                    owner_node_id=current_owner,
                )
        elif type(value) is list:
            for ordinal, child in enumerate(value):
                walk(
                    child, pointer=f"{pointer}/{ordinal}",
                    parent_pointer=pointer, property_name=None,
                    array_ordinal=ordinal, owner_node_id=current_owner,
                )

    walk(
        subtree, pointer="", parent_pointer=None, property_name=None,
        array_ordinal=None, owner_node_id=None,
    )
    return tuple(rows)


def reconstruct_obligation_datums(rows: Sequence[ObligationDatum]) -> dict[str, Any]:
    """Rebuild the canonical four-field subtree from generic datum rows."""
    if type(rows) not in {tuple, list} or any(type(row) is not ObligationDatum for row in rows):
        raise ObligationIntegrityError("obligation datum row collection differs")
    def pointer_order(pointer: str) -> tuple[tuple[int, int | bytes], ...]:
        return tuple(
            (0, int(token)) if token.isdigit() else (1, _utf16_sort_key(token))
            for token in pointer.strip("/").split("/") if token
        )

    ordered = sorted(rows, key=lambda row: (
        row.json_pointer.count("/"), pointer_order(row.json_pointer),
    ))
    values: dict[str, Any] = {}
    for row in ordered:
        if row.json_pointer in values:
            raise ObligationIntegrityError("obligation datum pointer is duplicated")
        if row.value_kind == "object":
            value: Any = {}
        elif row.value_kind == "array":
            value = []
        elif row.value_kind == "string" and row.string_value is not None and row.boolean_value is None:
            value = row.string_value
        elif row.value_kind == "boolean" and row.string_value is None and row.boolean_value is not None:
            value = row.boolean_value
        else:
            raise ObligationIntegrityError("obligation datum union differs")
        values[row.json_pointer] = value
        if row.json_pointer == "":
            if any(item is not None for item in (
                row.parent_pointer, row.property_name, row.array_ordinal,
            )):
                raise ObligationIntegrityError("obligation root datum metadata differs")
            continue
        parent = values.get(row.parent_pointer or "")
        if type(parent) is list:
            if row.property_name is not None or row.array_ordinal != len(parent):
                raise ObligationIntegrityError("obligation array order differs")
            parent.append(value)
        elif type(parent) is dict:
            if row.property_name is None or row.array_ordinal is not None or row.property_name in parent:
                raise ObligationIntegrityError("obligation object property differs")
            parent[row.property_name] = value
        else:
            raise ObligationIntegrityError("obligation datum parent differs")
    root = values.get("")
    if type(root) is not dict or set(root) != set(ROOT_FIELDS):
        raise ObligationIntegrityError("obligation datum root differs")
    return root


def materialize_obligation_projection_graph(
    *, proposal_id: str, directive_id: str,
    proposal_canonical_hash: str, evidence_binding_hash: str,
    app_projection_id: str, app_projection_hash: str,
    canonical_proposal: Mapping[str, Any],
    evidence_bindings: Mapping[str, str],
    app_targets: Sequence[ObligationApplicabilityTarget],
    foundation_refs: Sequence[ObligationCorrectionReference],
) -> ObligationProjectionGraph:
    """Build the complete deterministic Slice-3B graph before any SQL writes."""
    if type(canonical_proposal) is not dict:
        raise ObligationIntegrityError("canonical proposal type differs")
    if any(
        type(value) is not str or len(value) != 64
        for value in (
            proposal_canonical_hash, evidence_binding_hash, app_projection_hash,
        )
    ):
        raise ObligationIntegrityError("projection parent hash differs")
    if any(field not in canonical_proposal for field in ROOT_FIELDS):
        raise ObligationIntegrityError("obligation subtree field is missing")
    subtree_source = {field: canonical_proposal[field] for field in ROOT_FIELDS}
    _validate_source_resources(subtree_source)
    subtree_bytes = canonical_bytes(subtree_source, CANONICALIZATION_VERSION_V2)
    subtree = json.loads(subtree_bytes)
    subtree_hash = hashlib.sha256(DOMAINS["subtree"] + subtree_bytes).hexdigest()
    projection_identity = {
        "proposalId": proposal_id,
        "appProjectionId": app_projection_id,
        "materializerVersion": MATERIALIZER_VERSION,
        "subtreeHash": subtree_hash,
    }
    projection_id, projection_identity_hash = _row_id(
        "aox", "projection", projection_identity,
    )

    documents = materialize_document_family(
        proposal_id=proposal_id, projection_id=projection_id,
        canonical_documents=subtree["incorporatedDocuments"],
        evidence_bindings=evidence_bindings,
    )
    requirements = materialize_requirement_family(
        proposal_id=proposal_id, projection_id=projection_id,
        canonical_requirements=subtree["requirements"],
        evidence_bindings=evidence_bindings, document_family=documents,
        canonical_documents=subtree["incorporatedDocuments"],
        document_evidence_bindings=evidence_bindings,
    )
    expressions = materialize_expression_family(
        proposal_id=proposal_id, projection_id=projection_id,
        app_projection_id=app_projection_id,
        canonical_requirements=subtree["requirements"],
        evidence_bindings=evidence_bindings, document_family=documents,
        canonical_documents=subtree["incorporatedDocuments"],
        document_evidence_bindings=evidence_bindings,
        requirement_family=requirements, app_targets=app_targets,
    )
    timing = materialize_timing_recurrence_family(
        proposal_id=proposal_id, projection_id=projection_id,
        app_projection_id=app_projection_id,
        canonical_requirements=subtree["requirements"],
        evidence_bindings=evidence_bindings, document_family=documents,
        canonical_documents=subtree["incorporatedDocuments"],
        document_evidence_bindings=evidence_bindings,
        requirement_family=requirements, app_targets=app_targets,
        expression_family=expressions,
    )
    requirement_relationships = materialize_requirement_relationship_family(
        proposal_id=proposal_id, projection_id=projection_id,
        app_projection_id=app_projection_id,
        canonical_requirements=subtree["requirements"],
        evidence_bindings=evidence_bindings, document_family=documents,
        canonical_documents=subtree["incorporatedDocuments"],
        document_evidence_bindings=evidence_bindings,
        requirement_family=requirements, app_targets=app_targets,
        expression_family=expressions,
    )
    recurrence_groups = materialize_recurrence_group_family(
        proposal_id=proposal_id, projection_id=projection_id,
        app_projection_id=app_projection_id,
        canonical_requirements=subtree["requirements"],
        canonical_recurrence_groups=subtree["recurrenceGroups"],
        evidence_bindings=evidence_bindings, document_family=documents,
        canonical_documents=subtree["incorporatedDocuments"],
        document_evidence_bindings=evidence_bindings,
        requirement_family=requirements, app_targets=app_targets,
        expression_family=expressions, timing_recurrence_family=timing,
    )
    authority = materialize_authority_family(
        proposal_id=proposal_id, projection_id=projection_id,
        canonical_provisions=subtree["amocAuthorityProvisions"],
        evidence_bindings=evidence_bindings,
    )
    corrections = materialize_correction_binding_family(
        proposal_id=proposal_id, projection_id=projection_id,
        app_projection_id=app_projection_id,
        canonical_corrections=canonical_proposal.get("authoritativeCorrections", []),
        foundation_refs=foundation_refs,
        canonical_requirements=subtree["requirements"],
        canonical_recurrence_groups=subtree["recurrenceGroups"],
        canonical_provisions=subtree["amocAuthorityProvisions"],
        evidence_bindings=evidence_bindings, document_family=documents,
        canonical_documents=subtree["incorporatedDocuments"],
        document_evidence_bindings=evidence_bindings,
        requirement_family=requirements, app_targets=app_targets,
        expression_family=expressions, timing_recurrence_family=timing,
        recurrence_group_family=recurrence_groups, authority_family=authority,
    )

    semantic_nodes = tuple(sorted((
        *documents.semantic_nodes,
        *requirements.semantic_nodes,
        *expressions.semantic_nodes,
        *timing.semantic_nodes,
        *requirement_relationships.semantic_nodes,
        *recurrence_groups.semantic_nodes,
        *authority.semantic_nodes,
    ), key=lambda row: (
        row.source_pointer.count("/"), _utf16_sort_key(row.source_pointer),
        row.node_type,
    )))
    evidence_links = tuple((
        *documents.evidence_links,
        *requirements.evidence_links,
        *timing.evidence_links,
        *requirement_relationships.evidence_links,
        *recurrence_groups.evidence_links,
        *authority.evidence_links,
    ))
    if len({node.id for node in semantic_nodes}) != len(semantic_nodes):
        raise ObligationIntegrityError("semantic node identity set differs")
    if len({link.id for link in evidence_links}) != len(evidence_links):
        raise ObligationIntegrityError("evidence link identity set differs")

    owners_by_type: dict[str, Sequence[Any]] = {
        "incorporated_document": documents.documents,
        "value_assertion": (*documents.value_assertions, *authority.value_assertions),
        "requirement": requirements.requirements,
        "action": requirements.actions,
        "action_step": requirements.action_steps,
        "branch": requirements.branches,
        "expression": expressions.expressions,
        "timing_group": (*timing.timing_groups, *recurrence_groups.timing_groups),
        "timing_term": (*timing.timing_terms, *recurrence_groups.timing_terms),
        "recurrence": timing.recurrences,
        "terminating_effect": requirement_relationships.terminating_effects,
        "recurrence_group": recurrence_groups.recurrence_groups,
        "amoc_provision": authority.amoc_provisions,
    }
    owner_registry: dict[str, list[str]] = {}
    for node_type, owners in owners_by_type.items():
        for owner in owners:
            owner_registry.setdefault(owner.semantic_node_id, []).append(node_type)
    if set(owner_registry) != {node.id for node in semantic_nodes} or any(
        owner_registry.get(node.id) != [node.node_type] for node in semantic_nodes
    ):
        raise ObligationIntegrityError("semantic exactly-one-owner union differs")

    datums = _build_obligation_datums(
        proposal_id=proposal_id, projection_id=projection_id,
        subtree=subtree, semantic_nodes=semantic_nodes,
    )
    if reconstruct_obligation_datums(datums) != subtree:
        raise ObligationIntegrityError("generic obligation reconstruction differs")
    counts = {
        "semanticNodeCount": len(semantic_nodes),
        "datumCount": len(datums),
        "evidenceLinkCount": len(evidence_links),
        "documentCount": len(documents.documents),
        "valueAssertionCount": len(documents.value_assertions) + len(authority.value_assertions),
        "requirementCount": len(requirements.requirements),
        "actionCount": len(requirements.actions),
        "actionStepCount": len(requirements.action_steps),
        "actionDocumentRefCount": len(requirements.action_document_refs),
        "branchCount": len(requirements.branches),
        "expressionCount": len(expressions.expressions),
        "expressionEdgeCount": len(expressions.edges),
        "requirementDependencyCount": len(requirement_relationships.requirement_dependencies),
        "timingGroupCount": len(timing.timing_groups) + len(recurrence_groups.timing_groups),
        "timingTermCount": len(timing.timing_terms) + len(recurrence_groups.timing_terms),
        "recurrenceCount": len(timing.recurrences),
        "terminatingEffectCount": len(requirement_relationships.terminating_effects),
        "terminationEdgeCount": len(requirement_relationships.termination_edges),
        "recurrenceGroupCount": len(recurrence_groups.recurrence_groups),
        "recurrenceGroupMemberCount": len(recurrence_groups.members),
        "amocProvisionCount": len(authority.amoc_provisions),
        "correctionBindingCount": len(corrections.bindings),
    }
    if tuple(counts) != STRUCTURAL_COUNTS:
        raise ObligationIntegrityError("projection structural count registry differs")
    envelope = {
        "proposalId": proposal_id,
        "directiveId": directive_id,
        "validatorVersion": "paprnav-ad-v4-validator-2",
        "canonicalizationVersion": CANONICALIZATION_VERSION_V2,
        "proposalCanonicalHash": proposal_canonical_hash,
        "evidenceBindingHash": evidence_binding_hash,
        "appProjectionId": app_projection_id,
        "appProjectionHash": app_projection_hash,
        "appMaterializerVersion": APP_MATERIALIZER_VERSION,
        "materializerVersion": MATERIALIZER_VERSION,
        "mappingVersion": MAPPING_VERSION,
        "mappingDigest": MAPPING_DIGEST,
        "obligationSubtreeHash": subtree_hash,
        "gate": "candidate_only",
        "counts": counts,
    }
    projection_bytes = obligation_record_bytes(envelope)
    projection_hash = hashlib.sha256(
        DOMAINS["projection"] + projection_bytes
    ).hexdigest()
    projection = ObligationProjection(
        id=projection_id, identity_hash=projection_identity_hash,
        proposal_id=proposal_id, directive_id=directive_id,
        validator_version="paprnav-ad-v4-validator-2",
        canonicalization_version=CANONICALIZATION_VERSION_V2,
        proposal_canonical_hash=proposal_canonical_hash,
        evidence_binding_hash=evidence_binding_hash,
        app_projection_id=app_projection_id,
        app_projection_hash=app_projection_hash,
        app_materializer_version=APP_MATERIALIZER_VERSION,
        materializer_version=MATERIALIZER_VERSION,
        mapping_version=MAPPING_VERSION, mapping_digest=MAPPING_DIGEST,
        obligation_subtree_bytes=subtree_bytes,
        obligation_subtree_hash=subtree_hash,
        projection_canonical_bytes=projection_bytes,
        projection_hash=projection_hash, gate="candidate_only",
        counts=MappingProxyType(counts),
    )
    return ObligationProjectionGraph(
        projection=projection, datums=datums,
        semantic_nodes=semantic_nodes, evidence_links=evidence_links,
        document_family=documents, requirement_family=requirements,
        expression_family=expressions, timing_recurrence_family=timing,
        requirement_relationship_family=requirement_relationships,
        recurrence_group_family=recurrence_groups,
        authority_family=authority, correction_binding_family=corrections,
    )
