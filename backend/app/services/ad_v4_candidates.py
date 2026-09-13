from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from copy import deepcopy
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.models.core import (
    ADEvidenceFragment,
    ADEvidenceFragmentLifecycleEvent,
    ADV4CandidateEvidenceBinding,
    ADV4CandidateProposal,
    ADV4CandidateProposalEvent,
    ADV4CandidateSubmission,
    ADV4CandidateSubmissionRelationship,
    ADV4FeatureGate,
    AirworthinessDirective,
    OrganizationMembership,
    User,
    new_id,
)
from app.core.config import get_settings
from app.services.ad_evidence import _hash_parts
from app.services.ad_v4_graph import first_cycle_node


SCHEMA_VERSION = "ad_extraction_v4"
CANONICALIZATION_VERSION = "paprnav-ad-v4-c14n-1"
VALIDATOR_VERSION = "paprnav-ad-v4-validator-1"
CANONICALIZATION_VERSION_V2 = "paprnav-ad-v4-c14n-2"
VALIDATOR_VERSION_V2 = "paprnav-ad-v4-validator-2"
SUPPORTED_V4_VALIDATOR_PAIRS = frozenset({
    (VALIDATOR_VERSION, CANONICALIZATION_VERSION),
    (VALIDATOR_VERSION_V2, CANONICALIZATION_VERSION_V2),
})
POLICY_NAME = "paprnav-platform-admin-candidate-write"
POLICY_VERSION = "1"
ENDPOINT_ACTION = "create_ad_v4_candidate"
MAX_REQUEST_BYTES = 2_000_000
MAX_DEPTH = 64
MAX_TOTAL_NODES = 75_000
MAX_STRING_LENGTH = 16_384
MAX_ARRAY_ITEMS = 2_000
MAX_EVIDENCE_BINDINGS = 512
MAX_AST_NODES = 20_000
MAX_GRAPH_EDGES = 40_000
KEY_RE = re.compile(r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$")
HASH_RE = re.compile(r"^[0-9a-f]{64}$")

DOMAINS = {
    "proposal": b"paprnav:ad_extraction_v4:proposal:paprnav-ad-v4-c14n-1\x00",
    "bindings": b"paprnav:ad_extraction_v4:evidence-bindings:1\x00",
    "event": b"paprnav:ad_extraction_v4:candidate-event:1\x00",
    "submission": b"paprnav:ad_extraction_v4:submission:1\x00",
    "relationship": b"paprnav:ad_extraction_v4:submission-relationship:1\x00",
}
DOMAINS_V2 = {
    "proposal": b"paprnav:ad_extraction_v4:proposal:paprnav-ad-v4-c14n-2\x00",
    "bindings": b"paprnav:ad_extraction_v4:evidence-bindings:2\x00",
    "event": b"paprnav:ad_extraction_v4:candidate-event:2\x00",
    "submission": b"paprnav:ad_extraction_v4:submission:2\x00",
    "relationship": b"paprnav:ad_extraction_v4:submission-relationship:2\x00",
}

PROFILE_ENVELOPES = {
    VALIDATOR_VERSION: {
        "binding": "ad-v4-evidence-bindings-v1",
        "event": "ad-v4-candidate-created-v1",
        "submission": "ad-v4-submission-v1",
        "relationship": "ad-v4-submission-relationship-v1",
    },
    VALIDATOR_VERSION_V2: {
        "binding": "ad-v4-evidence-bindings-v2",
        "event": "ad-v4-candidate-created-v2",
        "submission": "ad-v4-submission-v2",
        "relationship": "ad-v4-submission-relationship-v2",
    },
}

ROOT_FIELDS = {
    "schemaVersion", "decisionKey", "directiveIdentity", "officialDocuments",
    "evidenceBindings", "incorporatedDocuments", "productScopes",
    "conditionDefinitions", "applicabilityRules", "requirements",
    "recurrenceGroups", "applicabilitySearchHints", "amocAuthorityProvisions",
    "supersessionRelations", "authoritativeCorrections",
}
REQUIRED_ROOT = ROOT_FIELDS
FORBIDDEN_FIELDS = {
    "affectedProducts", "complianceActions", "complianceIntervals", "confidence",
    "assessment", "assessmentLabel", "dueDate", "reviewDecision", "releaseState",
}
UNKNOWN_REASONS = {
    "not_observed", "unavailable", "not_obtained", "not_extracted",
    "not_yet_reviewed", "not_yet_verified", "conflicting_evidence",
    "source_ambiguous", "unsupported_expression",
}
INTERNAL_ARRAY_POLICIES: dict[str, tuple[str, str | tuple[str, ...] | None]] = {
    "bindings": ("set", "evidenceKey"),
    "semanticNodeHashes": ("set", None),
    "evidenceLinkHashes": ("set", None),
    "reasons": ("set", None),
}


class ADV4Error(ValueError):
    def __init__(self, code: str, pointer: str, message: str, *, http_status: int = 422) -> None:
        super().__init__(message)
        self.code = code
        self.pointer = pointer
        self.http_status = http_status


@dataclass(frozen=True)
class ParsedV4Request:
    raw_bytes: bytes
    value: dict[str, Any]
    raw_hash: str


@dataclass(frozen=True)
class StoredV4Candidate:
    proposal: ADV4CandidateProposal
    submission: ADV4CandidateSubmission
    content_reused: bool
    idempotent_retry: bool


def _reject_constant(value: str) -> None:
    raise ADV4Error("invalid_number", "", f"Numeric token {value!r} is forbidden")


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ADV4Error("duplicate_key", "", f"Duplicate object key: {key}")
        result[key] = value
    return result


def _walk_unicode(value: Any, pointer: str = "", *, depth: int = 0, counter: list[int] | None = None) -> None:
    if counter is None:
        counter = [0]
    counter[0] += 1
    if counter[0] > MAX_TOTAL_NODES:
        raise ADV4Error("resource_limit", pointer, "JSON node limit exceeded", http_status=413)
    if depth > MAX_DEPTH:
        raise ADV4Error("resource_limit", pointer, "JSON nesting depth exceeded", http_status=413)
    if value is None:
        raise ADV4Error("forbidden_json_value", pointer, "JSON null is forbidden")
    if isinstance(value, str):
        if len(value) > MAX_STRING_LENGTH:
            raise ADV4Error("resource_limit", pointer, "String length limit exceeded", http_status=413)
        if "\x00" in value:
            raise ADV4Error(
                "unsupported_unicode_character",
                pointer,
                "U+0000 is not representable by the PostgreSQL JSONB storage boundary",
            )
        if any(0xD800 <= ord(char) <= 0xDFFF for char in value):
            raise ADV4Error("invalid_unicode_scalar", pointer, "Lone surrogate is forbidden")
        if unicodedata.normalize("NFC", value) != value:
            raise ADV4Error("non_nfc_string", pointer, "Strings and keys must already be NFC")
    elif isinstance(value, dict):
        for key, child in value.items():
            _walk_unicode(key, f"{pointer}/{_escape_pointer(key)}", depth=depth + 1, counter=counter)
            _walk_unicode(child, f"{pointer}/{_escape_pointer(key)}", depth=depth + 1, counter=counter)
    elif isinstance(value, list):
        if len(value) > MAX_ARRAY_ITEMS:
            raise ADV4Error("resource_limit", pointer, "Array item limit exceeded", http_status=413)
        for index, child in enumerate(value):
            _walk_unicode(child, f"{pointer}/{index}", depth=depth + 1, counter=counter)
    elif isinstance(value, (int, float)) and not isinstance(value, bool):
        raise ADV4Error("invalid_number", pointer, "JSON numbers are forbidden")


def parse_v4_request_bytes(raw: bytes) -> ParsedV4Request:
    if not raw or len(raw) > MAX_REQUEST_BYTES:
        raise ADV4Error("invalid_request_size", "", "V4 request body is empty or exceeds the byte limit")
    try:
        decoded = raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise ADV4Error("invalid_utf8", "", "Request is not strict UTF-8") from exc
    try:
        value = json.loads(
            decoded,
            object_pairs_hook=_pairs,
            parse_int=_reject_constant,
            parse_float=_reject_constant,
            parse_constant=_reject_constant,
        )
    except ADV4Error:
        raise
    except RecursionError as exc:
        raise ADV4Error(
            "resource_limit", "", "JSON nesting exceeds the parser recursion limit", http_status=413,
        ) from exc
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        raise ADV4Error("invalid_json", "", "Request is not valid strict JSON") from exc
    if not isinstance(value, dict):
        raise ADV4Error("invalid_envelope", "", "Request root must be an object")
    _walk_unicode(value)
    return ParsedV4Request(raw, value, hashlib.sha256(raw).hexdigest())


def _escape_pointer(value: str) -> str:
    return value.replace("~", "~0").replace("/", "~1")


def _utf16_sort_key(value: str) -> bytes:
    return value.encode("utf-16-be", errors="strict")


def _resolved_schema(schema: dict[str, Any], root: dict[str, Any]) -> dict[str, Any]:
    seen: set[str] = set()
    while "$ref" in schema:
        reference = schema["$ref"]
        if not isinstance(reference, str) or not reference.startswith("#/$defs/") or reference in seen:
            raise RuntimeError(f"Invalid recursive array-policy reference: {reference!r}")
        seen.add(reference)
        schema = root["$defs"][reference.removeprefix("#/$defs/")]
    return schema


@lru_cache(maxsize=2)
def _array_policies(canonicalization_version: str = CANONICALIZATION_VERSION) -> dict[str, tuple[str, str | tuple[str, ...] | None]]:
    root = _v4_schema(
        VALIDATOR_VERSION_V2 if canonicalization_version == CANONICALIZATION_VERSION_V2 else VALIDATOR_VERSION
    )
    policies: dict[str, tuple[str, str | tuple[str, ...] | None]] = {}

    def walk(node: Any, property_name: str | None = None, seen: frozenset[str] = frozenset()) -> None:
        if not isinstance(node, dict):
            return
        if "$ref" in node:
            reference = node["$ref"]
            if reference in seen:
                return
            target = root["$defs"][reference.removeprefix("#/$defs/")]
            walk(target, property_name, seen | {reference})
            return
        if node.get("type") == "array" and property_name is not None:
            kind = node.get("x-paprnav-array-kind")
            raw_sort = node.get("x-paprnav-sort-key")
            sort_key: str | tuple[str, ...] | None
            sort_key = tuple(raw_sort) if isinstance(raw_sort, list) else raw_sort
            candidate = (kind, sort_key)
            prior = policies.get(property_name)
            if prior is not None and prior != candidate:
                raise RuntimeError(f"Conflicting V4 array policy for {property_name}: {prior} vs {candidate}")
            policies[property_name] = candidate
        for key, child in node.get("properties", {}).items():
            walk(child, key, seen)
        for child in node.get("oneOf", []):
            walk(child, property_name, seen)
        if "items" in node:
            walk(node["items"], None, seen)

    walk(root)
    return policies


def _set_sort_key(item: Any, sort_key: str | tuple[str, ...] | None, canonicalization_version: str) -> bytes:
    if sort_key is None:
        return canonical_bytes(item, canonicalization_version)
    if not isinstance(item, dict):
        raise ADV4Error("invalid_set_item", "", "Keyed set item must be an object")
    fields = (sort_key,) if isinstance(sort_key, str) else sort_key
    try:
        return b"\x00".join(canonical_bytes(item[field], canonicalization_version) for field in fields)
    except KeyError as exc:
        raise ADV4Error("missing_stable_key", "", f"Set item lacks {exc.args[0]}") from exc


def _normalize(value: Any, parent_key: str | None = None, canonicalization_version: str = CANONICALIZATION_VERSION) -> Any:
    if value is None or (isinstance(value, (int, float)) and not isinstance(value, bool)):
        raise ADV4Error("forbidden_json_value", "", "JSON null and numbers are forbidden")
    if isinstance(value, dict):
        return {key: _normalize(value[key], key, canonicalization_version) for key in sorted(value, key=_utf16_sort_key)}
    if isinstance(value, list):
        items = [_normalize(item, None, canonicalization_version) for item in value]
        policy = INTERNAL_ARRAY_POLICIES.get(parent_key or "") or _array_policies(canonicalization_version).get(parent_key or "")
        if parent_key is None:
            policy = ("sequence", None)
        if policy is None:
            raise ADV4Error("unregistered_array", "", f"Array {parent_key!r} has no schema canonicalization policy")
        kind, sort_key = policy
        if kind == "set":
            encoded = [canonical_bytes(item, canonicalization_version) for item in items]
            if len(encoded) != len(set(encoded)):
                raise ADV4Error("duplicate_set_item", "", f"Set array {parent_key} contains duplicates")
            identities = [_set_sort_key(item, sort_key, canonicalization_version) for item in items]
            if sort_key is not None and len(identities) != len(set(identities)):
                raise ADV4Error(
                    "duplicate_stable_key", "",
                    f"Set array {parent_key} contains duplicate composite identity",
                )
            items.sort(key=lambda item: _set_sort_key(item, sort_key, canonicalization_version))
        elif kind != "sequence":
            raise RuntimeError(f"Invalid V4 array kind for {parent_key}: {kind}")
        return items
    return value


def canonical_bytes(value: Any, canonicalization_version: str = CANONICALIZATION_VERSION) -> bytes:
    if canonicalization_version not in {CANONICALIZATION_VERSION, CANONICALIZATION_VERSION_V2}:
        raise ADV4Error("unsupported_canonicalization", "", "Unsupported V4 canonicalization version")
    normalized = _normalize(value, canonicalization_version=canonicalization_version)
    return json.dumps(
        normalized, ensure_ascii=False, allow_nan=False, separators=(",", ":"),
    ).encode("utf-8")


def _domain_hash(domain: str, value: Any, canonicalization_version: str = CANONICALIZATION_VERSION) -> str:
    domains = DOMAINS_V2 if canonicalization_version == CANONICALIZATION_VERSION_V2 else DOMAINS
    return hashlib.sha256(domains[domain] + canonical_bytes(value, canonicalization_version)).hexdigest()


def _require_object(value: Any, pointer: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ADV4Error("schema_type", pointer, "Expected object")
    return value


def _require_key(value: Any, pointer: str) -> str:
    if not isinstance(value, str) or not (3 <= len(value) <= 128) or not KEY_RE.fullmatch(value):
        raise ADV4Error("invalid_stable_key", pointer, "Stable key has invalid format")
    return value


@lru_cache(maxsize=2)
def _v4_schema(validator_version: str = VALIDATOR_VERSION) -> dict[str, Any]:
    path = Path(__file__).resolve().parents[1] / "schemas" / "ad_extraction_v4.schema.json"
    schema = json.loads(path.read_text(encoding="utf-8"))
    if validator_version == VALIDATOR_VERSION:
        return schema
    if validator_version != VALIDATOR_VERSION_V2:
        raise ADV4Error("unsupported_validator", "", "Unsupported V4 validator version")
    schema = deepcopy(schema)
    defs = schema["$defs"]
    member_base = {
        "type": "object", "additionalProperties": False,
        "required": ["memberKey", "designationKind", "manufacturer", "evidenceKeys"],
        "properties": {
            "memberKey": {"$ref": "#/$defs/stableKey"},
            "designationKind": {},
            "manufacturer": {"$ref": "#/$defs/knownString"},
            "evidenceKeys": {"$ref": "#/$defs/evidenceKeys"},
        },
    }
    model_member = deepcopy(member_base)
    model_member["required"].append("sourceDesignation")
    model_member["properties"].update({
        "designationKind": {"const": "model"},
        "sourceDesignation": {"$ref": "#/$defs/identifier"},
    })
    series_member = deepcopy(member_base)
    series_member["required"].extend(["expressionText", "evaluationState", "reason"])
    series_member["properties"].update({
        "designationKind": {"const": "series_expression"},
        "expressionText": {"$ref": "#/$defs/identifier"},
        "evaluationState": {"const": "unknown"},
        "reason": {"const": "unsupported_expression"},
    })
    defs["designationMemberV2"] = {"oneOf": [model_member, series_member]}
    defs["designationGroupV2"] = {
        "type": "object", "additionalProperties": False,
        "required": ["groupKey", "sourceDisplayText", "association", "members", "evidenceKeys"],
        "properties": {
            "groupKey": {"$ref": "#/$defs/stableKey"},
            "sourceDisplayText": {"$ref": "#/$defs/knownString"},
            "association": {"enum": ["all_members", "any_member", "source_group", "unknown"]},
            "members": {"type": "array", "minItems": 1, "items": {"$ref": "#/$defs/designationMemberV2"}, "x-paprnav-array-kind": "set", "x-paprnav-sort-key": "memberKey"},
            "reason": {"enum": sorted(UNKNOWN_REASONS)},
            "temporalScope": {"$ref": "#/$defs/temporalScope"},
            "evidenceKeys": {"$ref": "#/$defs/evidenceKeys"},
        },
    }
    defs["conditionSubject"]["properties"]["designationGroup"] = {"$ref": "#/$defs/designationGroupV2"}
    defs["manufacturerModelGroupV2"] = {
        "type": "object", "additionalProperties": False,
        "required": ["groupKey", "manufacturer", "association", "members", "evidenceKeys"],
        "properties": {
            "groupKey": {"$ref": "#/$defs/stableKey"},
            "manufacturer": {"$ref": "#/$defs/knownString"},
            "association": {"enum": ["paired", "source_group", "unknown"]},
            "members": {"type": "array", "minItems": 1, "items": {"$ref": "#/$defs/designationMemberV2"}, "x-paprnav-array-kind": "set", "x-paprnav-sort-key": "memberKey"},
            "reason": {"enum": sorted(UNKNOWN_REASONS)},
            "temporalScope": {"$ref": "#/$defs/temporalScope"},
            "evidenceKeys": {"$ref": "#/$defs/evidenceKeys"},
        },
    }
    defs["searchHint"] = {
        "type": "object", "additionalProperties": False,
        "required": ["hintKey", "productRole", "sourceDisplayText", "manufacturerModelGroups", "controlling", "exhaustive", "evidenceKeys"],
        "properties": {
            "hintKey": {"$ref": "#/$defs/stableKey"},
            "productRole": {"enum": ["airframe", "engine", "propeller", "appliance", "installed_part", "modification"]},
            "sourceDisplayText": {"$ref": "#/$defs/knownString"},
            "manufacturerModelGroups": {"type": "array", "minItems": 1, "items": {"$ref": "#/$defs/manufacturerModelGroupV2"}, "x-paprnav-array-kind": "set", "x-paprnav-sort-key": "groupKey"},
            "controlling": {"const": False}, "exhaustive": {"const": False},
            "evidenceKeys": {"$ref": "#/$defs/evidenceKeys"},
        },
    }
    return schema


def _schema_pointer(pointer: str, key: str | int) -> str:
    escaped = str(key) if isinstance(key, int) else _escape_pointer(key)
    return f"{pointer}/{escaped}" if pointer else f"/{escaped}"


def _schema_error(pointer: str, message: str) -> ADV4Error:
    return ADV4Error("schema_validation", pointer, message)


def _validate_schema_node(value: Any, schema: dict[str, Any], root: dict[str, Any], pointer: str) -> None:
    reference = schema.get("$ref")
    if reference is not None:
        prefix = "#/$defs/"
        if not isinstance(reference, str) or not reference.startswith(prefix):
            raise RuntimeError(f"Unsupported V4 schema reference: {reference!r}")
        name = reference[len(prefix):]
        target = root.get("$defs", {}).get(name)
        if not isinstance(target, dict):
            raise RuntimeError(f"Missing V4 schema definition: {name}")
        _validate_schema_node(value, target, root, pointer)
        return

    alternatives = schema.get("oneOf")
    if alternatives is not None:
        matches = 0
        errors: list[ADV4Error] = []
        for alternative in alternatives:
            try:
                _validate_schema_node(value, alternative, root, pointer)
                matches += 1
            except ADV4Error as exc:
                errors.append(exc)
        if matches != 1:
            detail = errors[0] if errors else None
            message = "Value must match exactly one closed schema variant"
            if detail is not None:
                message = f"{message}: {detail}"
            raise _schema_error(pointer, message)
        return

    if "const" in schema and value != schema["const"]:
        raise _schema_error(pointer, f"Expected constant {schema['const']!r}")
    if "enum" in schema and value not in schema["enum"]:
        raise _schema_error(pointer, "Value is outside the closed enum")

    expected_type = schema.get("type")
    if expected_type == "object":
        if not isinstance(value, dict):
            raise _schema_error(pointer, "Expected object")
        required = schema.get("required", [])
        missing = [key for key in required if key not in value]
        if missing:
            raise _schema_error(pointer, f"Missing required properties: {missing}")
        if len(value) < schema.get("minProperties", 0):
            raise _schema_error(pointer, "Object has too few properties")
        properties = schema.get("properties", {})
        patterns = [(re.compile(pattern), child) for pattern, child in schema.get("patternProperties", {}).items()]
        for key, child in value.items():
            child_schema = properties.get(key)
            if child_schema is not None:
                _validate_schema_node(child, child_schema, root, _schema_pointer(pointer, key))
                continue
            matching = [candidate for pattern, candidate in patterns if pattern.fullmatch(key)]
            if matching:
                for candidate in matching:
                    _validate_schema_node(child, candidate, root, _schema_pointer(pointer, key))
                continue
            if schema.get("additionalProperties") is False:
                raise _schema_error(_schema_pointer(pointer, key), "Additional property is forbidden")
        return
    if expected_type == "array":
        if not isinstance(value, list):
            raise _schema_error(pointer, "Expected array")
        if len(value) < schema.get("minItems", 0):
            raise _schema_error(pointer, "Array has too few items")
        if schema.get("uniqueItems"):
            encoded = [canonical_bytes(item) for item in value]
            if len(encoded) != len(set(encoded)):
                raise _schema_error(pointer, "Array items must be unique")
        item_schema = schema.get("items")
        if isinstance(item_schema, dict):
            for index, child in enumerate(value):
                _validate_schema_node(child, item_schema, root, _schema_pointer(pointer, index))
        return
    if expected_type == "string":
        if not isinstance(value, str):
            raise _schema_error(pointer, "Expected string")
        if len(value) < schema.get("minLength", 0) or len(value) > schema.get("maxLength", len(value)):
            raise _schema_error(pointer, "String length is outside schema bounds")
        pattern = schema.get("pattern")
        if pattern is not None and re.fullmatch(pattern, value) is None:
            raise _schema_error(pointer, "String does not match schema pattern")
        return
    if expected_type == "boolean" and not isinstance(value, bool):
        raise _schema_error(pointer, "Expected boolean")


def validate_v4_schema(value: dict[str, Any], validator_version: str = VALIDATOR_VERSION) -> None:
    """Validate the checked-in closed schema before semantic/reference checks."""
    schema = _v4_schema(validator_version)
    _validate_schema_node(value, schema, schema, "")


def _key_registry(items: list[dict[str, Any]], key_name: str, pointer: str) -> dict[str, dict[str, Any]]:
    registry: dict[str, dict[str, Any]] = {}
    for index, item in enumerate(items):
        key = item[key_name]
        if key in registry:
            raise ADV4Error("duplicate_stable_key", f"{pointer}/{index}/{key_name}", f"Duplicate {key_name}: {key}")
        registry[key] = item
    return registry


def _require_ref(key: str, registry: dict[str, Any], pointer: str, namespace: str) -> None:
    if key not in registry:
        raise ADV4Error("missing_typed_reference", pointer, f"{key!r} does not resolve in {namespace}")


def _assert_acyclic(graph: dict[str, set[str]], pointer: str) -> None:
    cycle_node = first_cycle_node(graph)
    if cycle_node is not None:
        raise ADV4Error("cyclic_reference", pointer, f"Cycle includes {cycle_node}")


def _count_graph_edge(counters: dict[str, int], pointer: str) -> None:
    """Count source occurrences, even when graph adjacency deduplicates targets."""
    counters["edges"] += 1
    if counters["edges"] > MAX_GRAPH_EDGES:
        raise ADV4Error(
            "resource_limit", pointer, "Graph edge limit exceeded", http_status=413,
        )


def _validate_expression_refs(
    expression: dict[str, Any], *, pointer: str,
    scopes: dict[str, Any], conditions: dict[str, Any], rules: dict[str, Any],
    requirements: dict[str, Any], allow_requirement_ref: bool,
    rule_edges: set[str], requirement_edges: set[str], counters: dict[str, int],
) -> None:
    counters["ast"] += 1
    if counters["ast"] > MAX_AST_NODES:
        raise ADV4Error("resource_limit", pointer, "AST node limit exceeded", http_status=413)
    node_type = expression["nodeType"]
    if node_type == "scope_ref":
        _require_ref(expression["scopeKey"], scopes, f"{pointer}/scopeKey", "productScopes")
    elif node_type == "predicate_ref":
        _require_ref(expression["conditionKey"], conditions, f"{pointer}/conditionKey", "conditionDefinitions")
    elif node_type == "rule_ref":
        _require_ref(expression["ruleKey"], rules, f"{pointer}/ruleKey", "applicabilityRules")
        _count_graph_edge(counters, pointer)
        rule_edges.add(expression["ruleKey"])
    elif node_type == "requirement_state_ref":
        if not allow_requirement_ref:
            raise ADV4Error("cross_namespace_reference", pointer, "Applicability rules cannot reference requirement state")
        _require_ref(expression["requirementKey"], requirements, f"{pointer}/requirementKey", "requirements")
        _count_graph_edge(counters, pointer)
        requirement_edges.add(expression["requirementKey"])
    elif node_type == "not":
        _validate_expression_refs(
            expression["operand"], pointer=f"{pointer}/operand", scopes=scopes,
            conditions=conditions, rules=rules, requirements=requirements,
            allow_requirement_ref=allow_requirement_ref, rule_edges=rule_edges,
            requirement_edges=requirement_edges, counters=counters,
        )
    elif node_type in {"all", "any"}:
        for index, operand in enumerate(expression["operands"]):
            _validate_expression_refs(
                operand, pointer=f"{pointer}/operands/{index}", scopes=scopes,
                conditions=conditions, rules=rules, requirements=requirements,
                allow_requirement_ref=allow_requirement_ref, rule_edges=rule_edges,
                requirement_edges=requirement_edges, counters=counters,
            )


def _validate_semantic_graph(proposal: dict[str, Any]) -> None:
    scopes = _key_registry(proposal["productScopes"], "scopeKey", "/proposal/productScopes")
    conditions = _key_registry(proposal["conditionDefinitions"], "conditionKey", "/proposal/conditionDefinitions")
    rules = _key_registry(proposal["applicabilityRules"], "ruleKey", "/proposal/applicabilityRules")
    requirements = _key_registry(proposal["requirements"], "requirementKey", "/proposal/requirements")
    documents = _key_registry(proposal["incorporatedDocuments"], "documentRefKey", "/proposal/incorporatedDocuments")
    official = _key_registry(proposal["officialDocuments"], "officialDocumentKey", "/proposal/officialDocuments")
    recurrence_groups = _key_registry(proposal["recurrenceGroups"], "recurrenceGroupKey", "/proposal/recurrenceGroups")
    _key_registry(proposal["applicabilitySearchHints"], "hintKey", "/proposal/applicabilitySearchHints")
    _key_registry(proposal["amocAuthorityProvisions"], "provisionKey", "/proposal/amocAuthorityProvisions")
    _key_registry(proposal["authoritativeCorrections"], "correctionKey", "/proposal/authoritativeCorrections")
    counters = {"ast": 0, "edges": 0}

    rule_graph = {key: set() for key in rules}
    for index, rule in enumerate(proposal["applicabilityRules"]):
        key = rule["ruleKey"]
        requirement_edges: set[str] = set()
        _validate_expression_refs(
            rule["scopeExpression"], pointer=f"/proposal/applicabilityRules/{index}/scopeExpression",
            scopes=scopes, conditions=conditions, rules=rules, requirements=requirements,
            allow_requirement_ref=False, rule_edges=rule_graph[key], requirement_edges=requirement_edges,
            counters=counters,
        )
        if "conditionExpression" in rule:
            _validate_expression_refs(
                rule["conditionExpression"], pointer=f"/proposal/applicabilityRules/{index}/conditionExpression",
                scopes=scopes, conditions=conditions, rules=rules, requirements=requirements,
                allow_requirement_ref=False, rule_edges=rule_graph[key], requirement_edges=requirement_edges,
                counters=counters,
            )
        for exclusion in rule["exclusionRuleKeys"]:
            _require_ref(exclusion, rules, f"/proposal/applicabilityRules/{index}/exclusionRuleKeys", "applicabilityRules")
            _count_graph_edge(counters, f"/proposal/applicabilityRules/{index}/exclusionRuleKeys")
            rule_graph[key].add(exclusion)
        if key in rule_graph[key]:
            raise ADV4Error("cyclic_reference", f"/proposal/applicabilityRules/{index}", "Rule cannot reference itself")
    _assert_acyclic(rule_graph, "/proposal/applicabilityRules")

    requirement_graph = {key: set() for key in requirements}
    memberships: dict[str, str] = {}
    for index, requirement in enumerate(proposal["requirements"]):
        key = requirement["requirementKey"]
        rule_edges: set[str] = set()
        _validate_expression_refs(
            requirement["activationExpression"], pointer=f"/proposal/requirements/{index}/activationExpression",
            scopes=scopes, conditions=conditions, rules=rules, requirements=requirements,
            allow_requirement_ref=True, rule_edges=rule_edges, requirement_edges=requirement_graph[key],
            counters=counters,
        )
        for prerequisite in requirement["prerequisiteRequirementKeys"]:
            _require_ref(prerequisite, requirements, f"/proposal/requirements/{index}/prerequisiteRequirementKeys", "requirements")
            _count_graph_edge(counters, f"/proposal/requirements/{index}/prerequisiteRequirementKeys")
            requirement_graph[key].add(prerequisite)
        effect = requirement["terminatingEffect"]
        for terminated in effect.get("requirementKeys", []):
            _require_ref(terminated, requirements, f"/proposal/requirements/{index}/terminatingEffect", "requirements")
            _count_graph_edge(counters, f"/proposal/requirements/{index}/terminatingEffect")
            requirement_graph[key].add(terminated)
        for document_key in requirement["action"]["approvedDataDocumentRefKeys"]:
            _require_ref(document_key, documents, f"/proposal/requirements/{index}/action/approvedDataDocumentRefKeys", "incorporatedDocuments")
        group_key = requirement.get("recurrenceGroupKey")
        if group_key is not None:
            _require_ref(group_key, recurrence_groups, f"/proposal/requirements/{index}/recurrenceGroupKey", "recurrenceGroups")
            memberships[key] = group_key
        branch_expression = requirement["branch"].get("conditionExpression")
        if branch_expression is not None:
            _validate_expression_refs(
                branch_expression, pointer=f"/proposal/requirements/{index}/branch/conditionExpression",
                scopes=scopes, conditions=conditions, rules=rules, requirements=requirements,
                allow_requirement_ref=True, rule_edges=rule_edges, requirement_edges=requirement_graph[key], counters=counters,
            )
        recurrence = requirement["recurrence"]
        recurrence_expression = recurrence.get("conditionExpression")
        if recurrence_expression is not None:
            _validate_expression_refs(
                recurrence_expression,
                pointer=f"/proposal/requirements/{index}/recurrence/conditionExpression",
                scopes=scopes, conditions=conditions, rules=rules,
                requirements=requirements, allow_requirement_ref=True,
                rule_edges=rule_edges, requirement_edges=requirement_graph[key],
                counters=counters,
            )
        if group_key is not None and (
            "logic" in requirement["initialTiming"] or recurrence.get("kind") != "none"
        ):
            raise ADV4Error(
                "recurrence_timing_conflict", f"/proposal/requirements/{index}",
                "Grouped requirements may not repeat group timing inline",
            )
    _assert_acyclic(requirement_graph, "/proposal/requirements")

    group_members: dict[str, str] = {}
    for index, group in enumerate(proposal["recurrenceGroups"]):
        if len(group["requirementKeys"]) < 2:
            raise ADV4Error("invalid_recurrence_group", f"/proposal/recurrenceGroups/{index}", "Recurrence group requires at least two members")
        for member in group["requirementKeys"]:
            _require_ref(member, requirements, f"/proposal/recurrenceGroups/{index}/requirementKeys", "requirements")
            if member in group_members:
                raise ADV4Error("duplicate_recurrence_membership", f"/proposal/recurrenceGroups/{index}", f"{member} belongs to multiple groups")
            group_members[member] = group["recurrenceGroupKey"]
    if memberships != group_members:
        raise ADV4Error("recurrence_membership_mismatch", "/proposal/recurrenceGroups", "Requirement and group memberships must agree exactly")

    semantic_namespaces: dict[str, dict[str, Any]] = {
        "productScopes": scopes, "conditionDefinitions": conditions,
        "applicabilityRules": rules, "requirements": requirements,
        "recurrenceGroups": recurrence_groups,
        "amocAuthorityProvisions": {x["provisionKey"]: x for x in proposal["amocAuthorityProvisions"]},
        "supersessionRelations": {
            f"{x['relationType']}-{x['predecessorAdNumber']}-{x['successorAdNumber']}": x
            for x in proposal["supersessionRelations"]
        },
    }
    correction_graph = {key: set() for key in official}
    for index, correction in enumerate(proposal["authoritativeCorrections"]):
        original_key = correction["originalDocumentRefKey"]
        correcting_key = correction["correctingDocumentRefKey"]
        _require_ref(original_key, official, f"/proposal/authoritativeCorrections/{index}/originalDocumentRefKey", "officialDocuments")
        _require_ref(correcting_key, official, f"/proposal/authoritativeCorrections/{index}/correctingDocumentRefKey", "officialDocuments")
        if official[correcting_key]["documentRole"] != "official_correction":
            raise ADV4Error("correction_document_mismatch", f"/proposal/authoritativeCorrections/{index}", "Correcting document must be an official correction")
        if not set(correction["evidenceKeys"]).issubset(set(official[correcting_key]["evidenceKeys"])):
            raise ADV4Error("correction_evidence_mismatch", f"/proposal/authoritativeCorrections/{index}/evidenceKeys", "Correction evidence must come from correcting document")
        correction_graph[original_key].add(correcting_key)
        _count_graph_edge(counters, f"/proposal/authoritativeCorrections/{index}")
        for ref_index, changed in enumerate(correction["changedSemanticRefs"]):
            namespace = changed["namespace"]
            if namespace == "directiveIdentity":
                if changed["key"] not in proposal["directiveIdentity"]:
                    raise ADV4Error("missing_typed_reference", f"/proposal/authoritativeCorrections/{index}/changedSemanticRefs/{ref_index}", "Directive identity field does not resolve")
            else:
                _require_ref(changed["key"], semantic_namespaces[namespace], f"/proposal/authoritativeCorrections/{index}/changedSemanticRefs/{ref_index}", namespace)
    _assert_acyclic(correction_graph, "/proposal/authoritativeCorrections")

    supersession_graph: dict[str, set[str]] = {}
    for index, relation in enumerate(proposal["supersessionRelations"]):
        if relation["predecessorAdNumber"] == relation["successorAdNumber"]:
            raise ADV4Error("cyclic_reference", f"/proposal/supersessionRelations/{index}", "Directive cannot supersede itself")
        supersession_graph.setdefault(relation["predecessorAdNumber"], set()).add(
            relation["successorAdNumber"]
        )
        _count_graph_edge(counters, f"/proposal/supersessionRelations/{index}")
        supersession_graph.setdefault(relation["successorAdNumber"], set())
    _assert_acyclic(supersession_graph, "/proposal/supersessionRelations")

def _validate_union(node: dict[str, Any], pointer: str) -> None:
    state = node.get("state")
    if state not in {"known", "unknown", "not_applicable"}:
        return
    evidence = node.get("evidenceKeys")
    if not isinstance(evidence, list) or not evidence:
        raise ADV4Error("missing_union_evidence", pointer, "Safety union requires evidenceKeys")
    if state == "known":
        if "value" not in node:
            raise ADV4Error("missing_known_value", pointer, "Known union requires value")
    else:
        if not isinstance(node.get("reason"), str) or not node["reason"].strip():
            raise ADV4Error("missing_union_reason", pointer, "Unknown/not-applicable requires reason")
        if state == "unknown" and node["reason"] not in UNKNOWN_REASONS:
            raise ADV4Error("invalid_unknown_reason", pointer, "Unknown reason is not controlled")
        temporal = node.get("temporalScope")
        if not isinstance(temporal, dict) or not isinstance(temporal.get("kind"), str):
            raise ADV4Error("missing_temporal_scope", pointer, "Unknown/not-applicable requires temporalScope")


def _collect_and_validate(value: Any, evidence: set[str], used: set[str], pointer: str = "") -> None:
    if isinstance(value, dict):
        if FORBIDDEN_FIELDS.intersection(value):
            field = sorted(FORBIDDEN_FIELDS.intersection(value))[0]
            raise ADV4Error("forbidden_derived_field", f"{pointer}/{field}", "Derived/customer field is forbidden")
        _validate_union(value, pointer)
        keys = value.get("evidenceKeys")
        if keys is not None:
            if not isinstance(keys, list) or not keys or len(keys) != len(set(keys)):
                raise ADV4Error("invalid_evidence_keys", f"{pointer}/evidenceKeys", "Evidence keys must be a nonempty unique array")
            for key in keys:
                if key not in evidence:
                    raise ADV4Error("missing_evidence_reference", f"{pointer}/evidenceKeys", f"Unknown evidence key {key}")
                used.add(key)
        for key, child in value.items():
            _collect_and_validate(child, evidence, used, f"{pointer}/{_escape_pointer(key)}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _collect_and_validate(child, evidence, used, f"{pointer}/{index}")


def _validated_requirement_sequences(
    proposal: dict[str, Any],
    *,
    integrity_read: bool = False,
) -> list[int]:
    requirements = proposal.get("requirements")
    if not isinstance(requirements, list):
        return []
    if len(requirements) > MAX_ARRAY_ITEMS:
        raise ADV4Error(
            "requirement_sequence_resource_limit",
            "/proposal/requirements",
            "Requirement count exceeds the array resource limit",
            http_status=409 if integrity_read else 413,
        )
    expected = {str(value): value for value in range(1, len(requirements) + 1)}
    seen: set[str] = set()
    result: list[int] = []
    status = 409 if integrity_read else 422
    for index, requirement in enumerate(requirements):
        sequence = requirement.get("sequence") if isinstance(requirement, dict) else None
        pointer = f"/proposal/requirements/{index}/sequence"
        if isinstance(sequence, str) and len(sequence) > MAX_STRING_LENGTH:
            raise ADV4Error(
                "requirement_sequence_resource_limit",
                pointer,
                "Requirement sequence exceeds the string resource limit",
                http_status=409 if integrity_read else 413,
            )
        if not isinstance(sequence, str) or sequence not in expected or sequence in seen:
            raise ADV4Error(
                "invalid_requirement_sequence",
                "/proposal/requirements",
                "Requirement sequence values must be unique and contiguous from 1",
                http_status=status,
            )
        seen.add(sequence)
        result.append(expected[sequence])
    if seen != set(expected):
        raise ADV4Error(
            "invalid_requirement_sequence",
            "/proposal/requirements",
            "Requirement sequence values must be unique and contiguous from 1",
            http_status=status,
        )
    return result


def _validate_v2_semantics(proposal: dict[str, Any]) -> None:
    for condition_index, condition in enumerate(proposal["conditionDefinitions"]):
        subject = condition["subject"]
        attribute = subject.get("attributeValue")
        if isinstance(attribute, dict) and attribute.get("state") == "known" and attribute.get("value") == "unknown_requires_compliance":
            raise ADV4Error(
                "semantic_unknown_sentinel",
                f"/proposal/conditionDefinitions/{condition_index}/subject/attributeValue/value",
                "Unknown applicability must use the explicit unknown union",
            )
        group = subject.get("designationGroup")
        if group is not None:
            unknown = group["association"] == "unknown"
            if unknown != ("reason" in group and "temporalScope" in group):
                raise ADV4Error("schema_validation", f"/proposal/conditionDefinitions/{condition_index}/subject/designationGroup", "Unknown group association requires reason and temporalScope only")
    for hint_index, hint in enumerate(proposal["applicabilitySearchHints"]):
        for group_index, group in enumerate(hint["manufacturerModelGroups"]):
            unknown = group["association"] == "unknown"
            if unknown != ("reason" in group and "temporalScope" in group):
                raise ADV4Error("schema_validation", f"/proposal/applicabilitySearchHints/{hint_index}/manufacturerModelGroups/{group_index}", "Unknown group association requires reason and temporalScope only")


def validate_v4_envelope(
    parsed: ParsedV4Request,
    directive_id: str,
    *,
    validator_version: str = VALIDATOR_VERSION,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    envelope = parsed.value
    validate_v4_schema(envelope, validator_version)
    if set(envelope) != {"proposal", "submissionContext"}:
        raise ADV4Error("closed_envelope", "", "Envelope properties must be proposal and submissionContext")
    proposal = _require_object(envelope["proposal"], "/proposal")
    if set(proposal) != REQUIRED_ROOT:
        missing = sorted(REQUIRED_ROOT - set(proposal))
        extra = sorted(set(proposal) - ROOT_FIELDS)
        raise ADV4Error("closed_root", "/proposal", f"Root mismatch missing={missing} extra={extra}")
    if proposal.get("schemaVersion") != SCHEMA_VERSION:
        raise ADV4Error("wrong_schema_version", "/proposal/schemaVersion", "Expected ad_extraction_v4")
    _require_key(proposal.get("decisionKey"), "/proposal/decisionKey")
    directive_identity = _require_object(proposal.get("directiveIdentity"), "/proposal/directiveIdentity")
    if directive_identity.get("directiveId") != directive_id:
        raise ADV4Error("directive_mismatch", "/proposal/directiveIdentity/directiveId", "Directive identity differs from route")
    for name in REQUIRED_ROOT - {"schemaVersion", "decisionKey", "directiveIdentity", "evidenceBindings"}:
        if not isinstance(proposal[name], list):
            raise ADV4Error("schema_type", f"/proposal/{name}", "Expected array")
    if not proposal["productScopes"] or not proposal["applicabilityRules"] or not proposal["requirements"]:
        raise ADV4Error("minimum_candidate", "/proposal", "Candidate requires scope, rule, and requirement")
    _validated_requirement_sequences(proposal)
    bindings = _require_object(proposal["evidenceBindings"], "/proposal/evidenceBindings")
    if not bindings:
        raise ADV4Error("missing_evidence", "/proposal/evidenceBindings", "At least one evidence binding is required")
    if len(bindings) > MAX_EVIDENCE_BINDINGS:
        raise ADV4Error("resource_limit", "/proposal/evidenceBindings", "Evidence binding limit exceeded", http_status=413)
    for key, binding in bindings.items():
        _require_key(key, f"/proposal/evidenceBindings/{key}")
        item = _require_object(binding, f"/proposal/evidenceBindings/{key}")
        if set(item) != {"fragmentId", "fragmentHash"} or not HASH_RE.fullmatch(str(item.get("fragmentHash", ""))):
            raise ADV4Error("invalid_evidence_binding", f"/proposal/evidenceBindings/{key}", "Binding must contain fragmentId and lowercase SHA-256")
    used: set[str] = set()
    _collect_and_validate({key: value for key, value in proposal.items() if key != "evidenceBindings"}, set(bindings), used, "/proposal")
    if used != set(bindings):
        raise ADV4Error("unused_evidence", "/proposal/evidenceBindings", f"Unused bindings: {sorted(set(bindings) - used)}")
    _validate_semantic_graph(proposal)
    if validator_version == VALIDATOR_VERSION_V2:
        _validate_v2_semantics(proposal)
    context = _require_object(envelope["submissionContext"], "/submissionContext")
    if set(context) != {"relationships"} or not isinstance(context["relationships"], list):
        raise ADV4Error("closed_submission_context", "/submissionContext", "Only relationships array is permitted")
    relationships = context["relationships"]
    seen: set[str] = set()
    for index, relation in enumerate(relationships):
        relation = _require_object(relation, f"/submissionContext/relationships/{index}")
        required = {"relationshipKey", "relationType", "predecessorProposalId", "reason", "evidenceKeys"}
        if set(relation) != required:
            raise ADV4Error("closed_relationship", f"/submissionContext/relationships/{index}", "Relationship shape is closed")
        key = _require_key(relation["relationshipKey"], f"/submissionContext/relationships/{index}/relationshipKey")
        if key in seen or relation["relationType"] not in {"corrects_candidate", "replaces_candidate"}:
            raise ADV4Error("invalid_relationship", f"/submissionContext/relationships/{index}", "Duplicate key or relation type")
        seen.add(key)
        if not str(relation["reason"]).strip() or not relation["evidenceKeys"]:
            raise ADV4Error("invalid_relationship", f"/submissionContext/relationships/{index}", "Reason and evidence are required")
        if not set(relation["evidenceKeys"]).issubset(bindings):
            raise ADV4Error("missing_evidence_reference", f"/submissionContext/relationships/{index}", "Relationship evidence does not resolve")
    return proposal, relationships


def _advisory_lock(db: Session, value: str) -> None:
    if db.bind is not None and db.bind.dialect.name == "postgresql":
        lock = int.from_bytes(hashlib.sha256(value.encode()).digest()[:8], "big", signed=True)
        db.execute(text("SELECT pg_advisory_xact_lock(:lock)"), {"lock": lock})


def _authorization(db: Session, actor: User, membership_id: str) -> OrganizationMembership:
    actor_row = db.scalar(select(User).where(User.id == actor.id).with_for_update())
    membership = db.scalar(
        select(OrganizationMembership).where(OrganizationMembership.id == membership_id).with_for_update()
    )
    if actor_row is None or actor_row.status != "active" or membership is None:
        raise ADV4Error("forbidden", "", "Active platform administrator membership required", http_status=403)
    if membership.user_id != actor.id or membership.status != "active" or membership.role != "platform_admin":
        raise ADV4Error("forbidden", "", "Active platform administrator membership required", http_status=403)
    return membership


def require_v4_database_gate(db: Session, gate_key: str, *, lock: bool = False) -> None:
    query = select(ADV4FeatureGate).where(ADV4FeatureGate.gate_key == gate_key)
    if lock:
        query = query.with_for_update(read=True)
    try:
        gate = db.scalar(query)
    except Exception as exc:
        raise ADV4Error("schema_capability_mismatch", "", "V4 database capability is unavailable", http_status=409) from exc
    if gate is None or not gate.enabled:
        code = {
            "validator2_write_enabled": "validator2_write_gate_disabled",
            "materializer3a_enabled": "materializer3a_gate_disabled",
            "materializer3b_enabled": "materializer3b_gate_disabled",
        }.get(gate_key, "schema_capability_mismatch")
        raise ADV4Error(code, "", f"V4 database gate {gate_key} is disabled", http_status=409)


def _binding_snapshot(db: Session, directive_id: str, proposal: dict[str, Any]) -> list[dict[str, Any]]:
    snapshots: list[dict[str, Any]] = []
    requested_bindings = proposal["evidenceBindings"]
    fragment_ids = sorted({requested["fragmentId"] for requested in requested_bindings.values()})
    fragments = db.scalars(
        select(ADEvidenceFragment)
        .where(ADEvidenceFragment.id.in_(fragment_ids))
        .order_by(ADEvidenceFragment.id)
        .with_for_update()
    ).all()
    by_fragment_id = {fragment.id: fragment for fragment in fragments}
    if set(by_fragment_id) != set(fragment_ids):
        raise ADV4Error("evidence_mismatch", "/proposal/evidenceBindings", "Evidence fragment does not exist")
    for evidence_key, requested in requested_bindings.items():
        fragment = by_fragment_id[requested["fragmentId"]]
        if fragment is None or fragment.directive_id != directive_id or fragment.fragment_hash != requested["fragmentHash"]:
            raise ADV4Error("evidence_mismatch", f"/proposal/evidenceBindings/{evidence_key}", "Evidence fragment identity or directive mismatches")
        events = db.scalars(
            select(ADEvidenceFragmentLifecycleEvent)
            .where(ADEvidenceFragmentLifecycleEvent.fragment_id == fragment.id)
            .order_by(ADEvidenceFragmentLifecycleEvent.sequence_number)
        ).all()
        if len(events) != 1 or events[0].event_type != "admitted" or events[0].sequence_number != 0 or events[0].predecessor_event_hash is not None:
            raise ADV4Error("evidence_not_admitted", f"/proposal/evidenceBindings/{evidence_key}", "Evidence lifecycle is not an exact admitted root")
        event = events[0]
        expected_event_hash = _hash_parts(
            fragment.id, fragment.fragment_hash, event.event_type,
            event.actor_user_id, event.reason, event.sequence_number,
            event.predecessor_event_hash,
        )
        if event.event_hash != expected_event_hash:
            raise ADV4Error("evidence_not_admitted", f"/proposal/evidenceBindings/{evidence_key}", "Evidence admission hash is invalid")
        snapshots.append({
            "evidenceKey": evidence_key, "fragmentId": fragment.id,
            "fragmentHash": fragment.fragment_hash, "admittedEventId": event.id,
            "admittedEventHash": event.event_hash,
        })
    snapshots.sort(key=lambda item: item["evidenceKey"])
    by_key = {item["evidenceKey"]: item for item in snapshots}
    for document in proposal["officialDocuments"]:
        role = document.get("documentRole")
        if role not in {"ad_rule", "official_correction"}:
            raise ADV4Error("invalid_official_document", "/proposal/officialDocuments", "Invalid official document role")
        for key in document.get("evidenceKeys", []):
            fragment = next(item for item in fragments if item.id == by_key[key]["fragmentId"])
            if fragment.source_document_id != document.get("sourceDocumentId") or fragment.source_content_hash != document.get("sourceContentHash"):
                raise ADV4Error("official_document_mismatch", "/proposal/officialDocuments", "Official document does not match retained evidence")
    official = {item.get("officialDocumentKey"): item for item in proposal["officialDocuments"]}
    for correction in proposal["authoritativeCorrections"]:
        original = official.get(correction.get("originalDocumentRefKey"))
        correcting = official.get(correction.get("correctingDocumentRefKey"))
        if original is None or correcting is None or correcting.get("documentRole") != "official_correction":
            raise ADV4Error("correction_document_mismatch", "/proposal/authoritativeCorrections", "Correction references do not resolve to official documents")
    return snapshots


def _validate_candidate_relationship_graph(
    db: Session,
    *,
    directive_id: str,
    proposal_id: str,
    relationships: list[dict[str, Any]],
) -> dict[str, ADV4CandidateProposal]:
    """Serialize and reject candidate correction/replacement graph cycles."""

    if not relationships:
        return {}
    _advisory_lock(db, f"candidate-relationship-graph:{directive_id}")
    rows = db.execute(
        select(
            ADV4CandidateSubmission.proposal_id,
            ADV4CandidateSubmissionRelationship.predecessor_proposal_id,
        )
        .join(
            ADV4CandidateSubmissionRelationship,
            ADV4CandidateSubmissionRelationship.submission_id == ADV4CandidateSubmission.id,
        )
        .where(ADV4CandidateSubmission.directive_id == directive_id)
    ).all()
    graph: dict[str, set[str]] = {}
    for current_id, predecessor_id in rows:
        graph.setdefault(current_id, set()).add(predecessor_id)
        graph.setdefault(predecessor_id, set())
    predecessors: dict[str, ADV4CandidateProposal] = {}
    for index, relation in enumerate(relationships):
        predecessor_id = relation["predecessorProposalId"]
        predecessor = db.get(ADV4CandidateProposal, predecessor_id)
        if (
            predecessor is None
            or predecessor.directive_id != directive_id
            or predecessor.id == proposal_id
        ):
            raise ADV4Error(
                "invalid_predecessor", f"/submissionContext/relationships/{index}",
                "Predecessor must be another candidate for this directive",
            )
        predecessors[predecessor_id] = predecessor
        graph.setdefault(proposal_id, set()).add(predecessor_id)
        graph.setdefault(predecessor_id, set())
    _assert_acyclic(graph, "/submissionContext/relationships")
    return predecessors


def store_v4_candidate(
    db: Session, *, directive_id: str, parsed: ParsedV4Request, actor: User,
    membership_id: str, idempotency_key: str,
    validator_version: str | None = None,
) -> StoredV4Candidate:
    if validator_version is None:
        validator_version = (
            VALIDATOR_VERSION_V2
            if get_settings().ad_v4_validator2_writes_enabled
            else VALIDATOR_VERSION
        )
    if validator_version not in {VALIDATOR_VERSION, VALIDATOR_VERSION_V2}:
        raise ADV4Error("unsupported_validator", "", "Unsupported V4 validator version")
    canonicalization_version = (
        CANONICALIZATION_VERSION_V2
        if validator_version == VALIDATOR_VERSION_V2
        else CANONICALIZATION_VERSION
    )
    if validator_version == VALIDATOR_VERSION_V2:
        if not get_settings().ad_v4_validator2_writes_enabled:
            raise ADV4Error("capability_disabled", "", "Validator-2 application capability is disabled", http_status=409)
        if db.bind is not None and db.bind.dialect.name == "postgresql":
            db.execute(text("LOCK TABLE ad_v4_candidate_proposals IN ROW EXCLUSIVE MODE"))
        require_v4_database_gate(db, "validator2_write_enabled", lock=True)
    proposal_value, relationships = validate_v4_envelope(
        parsed, directive_id, validator_version=validator_version,
    )
    if db.get(AirworthinessDirective, directive_id) is None:
        raise ADV4Error("not_found", "", "Directive not found", http_status=404)
    membership = _authorization(db, actor, membership_id)
    scope = f"{actor.id}:{membership.id}:{ENDPOINT_ACTION}:{POLICY_VERSION}:{idempotency_key}"
    _advisory_lock(db, f"idem:{scope}")
    proposal_payload = canonical_bytes(proposal_value, canonicalization_version)
    # Persist the exact JSON value represented by canonical_bytes. The c14n-2
    # profile normalizes semantic-set arrays, so retaining the transport order
    # in parsed_json would make PostgreSQL's JSON/byte identity check disagree
    # with the authoritative payload for otherwise valid proposals.
    canonical_proposal_value = json.loads(proposal_payload)
    domains = DOMAINS_V2 if validator_version == VALIDATOR_VERSION_V2 else DOMAINS
    envelopes = PROFILE_ENVELOPES[validator_version]
    proposal_hash = hashlib.sha256(domains["proposal"] + proposal_payload).hexdigest()
    request_envelope = {
        "version": envelopes["submission"], "directiveId": directive_id,
        "proposalCanonicalHash": proposal_hash, "relationships": relationships,
    }
    if validator_version == VALIDATOR_VERSION_V2:
        request_envelope.update({
            "validatorVersion": validator_version,
            "canonicalizationVersion": canonicalization_version,
        })
    request_hash = _domain_hash("submission", request_envelope, canonicalization_version)
    prior = db.scalar(select(ADV4CandidateSubmission).where(
        ADV4CandidateSubmission.actor_user_id == actor.id,
        ADV4CandidateSubmission.authorizing_membership_id == membership.id,
        ADV4CandidateSubmission.endpoint_action == ENDPOINT_ACTION,
        ADV4CandidateSubmission.auth_policy_version == POLICY_VERSION,
        ADV4CandidateSubmission.idempotency_key == idempotency_key,
    ))
    if prior is not None:
        if prior.directive_id != directive_id or prior.request_hash != request_hash:
            raise ADV4Error("idempotency_conflict", "", "Idempotency key was used for different canonical content", http_status=409)
        return StoredV4Candidate(db.get(ADV4CandidateProposal, prior.proposal_id), prior, True, True)  # type: ignore[arg-type]
    snapshots = _binding_snapshot(db, directive_id, proposal_value)
    binding_envelope = {"version": envelopes["binding"], "bindings": snapshots}
    if validator_version == VALIDATOR_VERSION_V2:
        binding_envelope.update({"validatorVersion": validator_version, "canonicalizationVersion": canonicalization_version})
    binding_hash = _domain_hash("bindings", binding_envelope, canonicalization_version)
    _advisory_lock(db, f"content:{directive_id}:{validator_version}:{canonicalization_version}:{proposal_hash}")
    candidate = db.scalar(select(ADV4CandidateProposal).where(
        ADV4CandidateProposal.directive_id == directive_id,
        ADV4CandidateProposal.validator_version == validator_version,
        ADV4CandidateProposal.canonicalization_version == canonicalization_version,
        ADV4CandidateProposal.canonical_hash == proposal_hash,
    ))
    reused = candidate is not None
    if candidate is None:
        candidate = ADV4CandidateProposal(
            id=new_id("avp"), directive_id=directive_id, schema_version=SCHEMA_VERSION,
            canonicalization_version=canonicalization_version,
            validator_version=validator_version, canonical_bytes=proposal_payload,
            parsed_json=canonical_proposal_value, canonical_hash=proposal_hash,
            evidence_binding_bytes=canonical_bytes(binding_envelope, canonicalization_version),
            evidence_binding_hash=binding_hash, binding_count=len(snapshots), gate="candidate_only",
        )
        db.add(candidate)
        # Evidence bindings use scalar foreign-key ids rather than ORM
        # relationships. Make the parent visible to PostgreSQL's immediate
        # binding-integrity trigger before any child INSERT; the proposal's
        # completeness constraint remains deferred until transaction commit.
        db.flush([candidate])
        binding_rows = []
        for item in snapshots:
            binding = ADV4CandidateEvidenceBinding(
                proposal_id=candidate.id, directive_id=directive_id,
                evidence_key=item["evidenceKey"], fragment_id=item["fragmentId"],
                fragment_hash=item["fragmentHash"], admitted_event_id=item["admittedEventId"],
                admitted_event_hash=item["admittedEventHash"],
                validator_version=validator_version,
                canonicalization_version=canonicalization_version,
            )
            db.add(binding)
            binding_rows.append(binding)
        # Bindings have an immediate integrity trigger and must be visible
        # before the submission/event layer is constructed. Proposal
        # completeness itself remains deferred to commit.
        db.flush(binding_rows)
    else:
        if candidate.evidence_binding_hash != binding_hash:
            raise ADV4Error("binding_identity_conflict", "", "Canonical content has a different evidence lifecycle snapshot", http_status=409)
    predecessors = _validate_candidate_relationship_graph(
        db,
        directive_id=directive_id,
        proposal_id=candidate.id,
        relationships=relationships,
    )
    claims = {"userId": actor.id, "membershipId": membership.id, "organizationId": membership.organization_id, "role": membership.role, "status": membership.status, "policy": POLICY_NAME, "version": POLICY_VERSION}
    submission = ADV4CandidateSubmission(
        id=new_id("avs"), proposal_id=candidate.id, directive_id=directive_id,
        actor_kind="platform_admin", actor_user_id=actor.id,
        authorizing_membership_id=membership.id, organization_id=membership.organization_id,
        actor_role=membership.role, actor_status=membership.status,
        auth_policy_name=POLICY_NAME, auth_policy_version=POLICY_VERSION,
        auth_claims_hash=hashlib.sha256(canonical_bytes(claims, canonicalization_version)).hexdigest(),
        endpoint_action=ENDPOINT_ACTION, idempotency_key=idempotency_key,
        request_hash=request_hash, request_canonical_bytes=canonical_bytes(request_envelope, canonicalization_version),
        raw_transport_hash=parsed.raw_hash,
        validator_version=validator_version,
        canonicalization_version=canonicalization_version,
    )
    db.add(submission)
    # Relationship and candidate-created event triggers both resolve their
    # immutable creator submission immediately. Flush that parent first;
    # submission relationship completeness remains deferred to commit.
    db.flush([submission])
    for relation in relationships:
        predecessor = predecessors[relation["predecessorProposalId"]]
        relation_envelope = {
            "version": envelopes["relationship"],
            "submissionId": submission.id,
            **relation,
        }
        if validator_version == VALIDATOR_VERSION_V2:
            relation_envelope.update({"validatorVersion": validator_version, "canonicalizationVersion": canonicalization_version})
        relation_bytes = canonical_bytes(relation_envelope, canonicalization_version)
        db.add(ADV4CandidateSubmissionRelationship(
            submission_id=submission.id, relationship_key=relation["relationshipKey"],
            relation_type=relation["relationType"], predecessor_proposal_id=predecessor.id,
            reason=relation["reason"], evidence_keys=relation["evidenceKeys"],
            canonical_bytes=relation_bytes,
            relationship_hash=_domain_hash("relationship", relation_envelope, canonicalization_version),
            validator_version=validator_version,
            canonicalization_version=canonicalization_version,
        ))
    if not reused:
        event_envelope = {
            "version": envelopes["event"], "eventType": "candidate_created",
            "proposalId": candidate.id, "directiveId": directive_id,
            "proposalCanonicalHash": proposal_hash, "evidenceBindingHash": binding_hash,
            "createdBySubmissionId": submission.id,
        }
        if validator_version == VALIDATOR_VERSION_V2:
            event_envelope.update({"validatorVersion": validator_version, "canonicalizationVersion": canonicalization_version})
        event_bytes = canonical_bytes(event_envelope, canonicalization_version)
        db.add(ADV4CandidateProposalEvent(
            proposal_id=candidate.id, directive_id=directive_id,
            created_by_submission_id=submission.id, event_type="candidate_created",
            sequence_number=0, proposal_canonical_hash=proposal_hash,
            evidence_binding_hash=binding_hash, predecessor_event_hash=None,
            canonical_bytes=event_bytes,
            event_hash=_domain_hash("event", event_envelope, canonicalization_version),
            validator_version=validator_version,
            canonicalization_version=canonicalization_version,
        ))
    db.flush()
    return StoredV4Candidate(candidate, submission, reused, False)


def verified_candidate(db: Session, proposal_id: str) -> ADV4CandidateProposal:
    candidate = db.get(ADV4CandidateProposal, proposal_id)
    if candidate is None:
        raise ADV4Error("not_found", "", "Candidate not found", http_status=404)
    pair = (candidate.validator_version, candidate.canonicalization_version)
    if pair not in SUPPORTED_V4_VALIDATOR_PAIRS:
        raise ADV4Error("candidate_integrity", "", "Stored validator/canonicalization pair is unsupported", http_status=409)
    if canonical_bytes(candidate.parsed_json, candidate.canonicalization_version) != candidate.canonical_bytes:
        raise ADV4Error("candidate_integrity", "", "Stored canonical bytes and JSON differ", http_status=409)
    domains = DOMAINS_V2 if candidate.validator_version == VALIDATOR_VERSION_V2 else DOMAINS
    if hashlib.sha256(domains["proposal"] + candidate.canonical_bytes).hexdigest() != candidate.canonical_hash:
        raise ADV4Error("candidate_integrity", "", "Stored canonical hash differs", http_status=409)
    validate_v4_schema({"proposal": candidate.parsed_json, "submissionContext": {"relationships": []}}, candidate.validator_version)
    _validated_requirement_sequences(candidate.parsed_json, integrity_read=True)
    return candidate


def verified_submission(db: Session, submission: ADV4CandidateSubmission) -> list[ADV4CandidateSubmissionRelationship]:
    candidate = verified_candidate(db, submission.proposal_id)
    if (
        submission.validator_version != candidate.validator_version
        or submission.canonicalization_version != candidate.canonicalization_version
    ):
        raise ADV4Error("candidate_integrity", "", "Submission version pair differs from proposal", http_status=409)
    canonicalization_version = candidate.canonicalization_version
    envelopes = PROFILE_ENVELOPES[candidate.validator_version]
    if (
        submission.actor_kind != "platform_admin"
        or submission.actor_role != "platform_admin"
        or submission.actor_status != "active"
        or submission.auth_policy_name != POLICY_NAME
        or submission.auth_policy_version != POLICY_VERSION
        or submission.endpoint_action != ENDPOINT_ACTION
        or not re.fullmatch(r"[0-9a-f]{64}", submission.raw_transport_hash or "")
    ):
        raise ADV4Error("candidate_integrity", "", "Submission authorization provenance differs", http_status=409)
    try:
        request_value = json.loads(submission.request_canonical_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ADV4Error("candidate_integrity", "", "Submission canonical bytes are invalid", http_status=409) from exc
    if canonical_bytes(request_value, canonicalization_version) != submission.request_canonical_bytes:
        raise ADV4Error("candidate_integrity", "", "Submission bytes are not canonical", http_status=409)
    if _domain_hash("submission", request_value, canonicalization_version) != submission.request_hash:
        raise ADV4Error("candidate_integrity", "", "Submission hash differs", http_status=409)
    if request_value.get("version") != envelopes["submission"] or request_value.get("directiveId") != submission.directive_id or request_value.get("proposalCanonicalHash") != candidate.canonical_hash:
        raise ADV4Error("candidate_integrity", "", "Submission envelope differs from relational identity", http_status=409)
    if candidate.validator_version == VALIDATOR_VERSION_V2 and (
        request_value.get("validatorVersion") != candidate.validator_version
        or request_value.get("canonicalizationVersion") != canonicalization_version
    ):
        raise ADV4Error("candidate_integrity", "", "Submission envelope version differs", http_status=409)
    claims = {
        "userId": submission.actor_user_id,
        "membershipId": submission.authorizing_membership_id,
        "organizationId": submission.organization_id,
        "role": submission.actor_role,
        "status": submission.actor_status,
        "policy": submission.auth_policy_name,
        "version": submission.auth_policy_version,
    }
    if hashlib.sha256(canonical_bytes(claims, canonicalization_version)).hexdigest() != submission.auth_claims_hash:
        raise ADV4Error("candidate_integrity", "", "Authorization snapshot hash differs", http_status=409)
    relationships = db.scalars(
        select(ADV4CandidateSubmissionRelationship)
        .where(ADV4CandidateSubmissionRelationship.submission_id == submission.id)
        .order_by(ADV4CandidateSubmissionRelationship.relationship_key)
    ).all()
    relational_relationships = []
    candidate_evidence_keys = set(candidate.parsed_json.get("evidenceBindings", {}))
    for relationship in relationships:
        envelope = {
            "version": envelopes["relationship"],
            "submissionId": submission.id,
            "relationshipKey": relationship.relationship_key,
            "relationType": relationship.relation_type,
            "predecessorProposalId": relationship.predecessor_proposal_id,
            "reason": relationship.reason,
            "evidenceKeys": relationship.evidence_keys,
        }
        if candidate.validator_version == VALIDATOR_VERSION_V2:
            envelope.update({"validatorVersion": candidate.validator_version, "canonicalizationVersion": canonicalization_version})
        expected_bytes = canonical_bytes(envelope, canonicalization_version)
        predecessor = db.get(ADV4CandidateProposal, relationship.predecessor_proposal_id)
        if (
            relationship.canonical_bytes != expected_bytes
            or relationship.relationship_hash != _domain_hash("relationship", envelope, canonicalization_version)
            or relationship.validator_version != candidate.validator_version
            or relationship.canonicalization_version != canonicalization_version
            or predecessor is None
            or predecessor.directive_id != candidate.directive_id
            or predecessor.id == candidate.id
            or not set(relationship.evidence_keys).issubset(candidate_evidence_keys)
        ):
            raise ADV4Error("candidate_integrity", "", "Relationship audit envelope differs", http_status=409)
        relational_relationships.append({
            "relationshipKey": relationship.relationship_key,
            "relationType": relationship.relation_type,
            "predecessorProposalId": relationship.predecessor_proposal_id,
            "reason": relationship.reason,
            "evidenceKeys": relationship.evidence_keys,
        })
    if request_value.get("relationships") != sorted(relational_relationships, key=lambda item: item["relationshipKey"]):
        raise ADV4Error("candidate_integrity", "", "Submission relationship set differs", http_status=409)
    return relationships
