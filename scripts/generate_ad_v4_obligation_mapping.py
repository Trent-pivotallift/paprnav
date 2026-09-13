#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any


GENERATOR_VERSION = "paprnav-ad-v4-obligation-mapgen-1"
GENERATOR_SOURCE_SHA256 = "d3968bbf4a53c99cd7315441c06a671a94b436631238e0c442f420f488da4c9d"
EXPECTED_MANIFEST_SHAPE_SHA256 = "ec017c75fec315c7351229b9e70d2b5d8187504d7d6b4109038a492b979da62e"
SOURCE_DIGEST_PATTERN = re.compile(
    rb'(?m)^(GENERATOR_SOURCE_SHA256 = ")[0-9a-f]{64}("$)'
)
ZERO_DIGEST = b"0" * 64

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = REPOSITORY_ROOT / "backend/app/contracts/ad_v4_obligation_mapping_v1.json"
PYTHON_OUTPUT = REPOSITORY_ROOT / "backend/app/services/ad_v4_obligation_mapping_v1.py"
SQL_OUTPUT = REPOSITORY_ROOT / "backend/app/db/migrations/sql/20260911_0028_obligation_expectations.sql"

EXPECTED_ROOT_FIELDS = [
    "incorporatedDocuments",
    "requirements",
    "recurrenceGroups",
    "amocAuthorityProvisions",
]
EXPECTED_COUNTS = [
    "semanticNodeCount",
    "datumCount",
    "evidenceLinkCount",
    "documentCount",
    "valueAssertionCount",
    "requirementCount",
    "actionCount",
    "actionStepCount",
    "actionDocumentRefCount",
    "branchCount",
    "expressionCount",
    "expressionEdgeCount",
    "requirementDependencyCount",
    "timingGroupCount",
    "timingTermCount",
    "recurrenceCount",
    "terminatingEffectCount",
    "terminationEdgeCount",
    "recurrenceGroupCount",
    "recurrenceGroupMemberCount",
    "amocProvisionCount",
    "correctionBindingCount",
]
EXPECTED_ALGORITHMS = {
    "restricted_jcs",
    "expression_tree_walk",
    "graph_cycle_check",
    "decimal_precheck",
    "sequence_precheck",
    "typed_reconstruction",
    "projection_fold",
    "request_fold",
    "event_fold",
}
EXPECTED_LIMITS = {
    "maxDepth": 64,
    "maxTotalNodes": 75_000,
    "maxStringLength": 16_384,
    "maxArrayItems": 2_000,
    "maxAstNodes": 20_000,
    "maxGraphEdges": 40_000,
    "maxInternalInteger": 2_147_483_647,
}


def _generator_source_digest() -> str:
    source = Path(__file__).read_bytes()
    normalized, replacements = SOURCE_DIGEST_PATTERN.subn(
        rb'\g<1>' + ZERO_DIGEST + rb'\g<2>', source
    )
    if replacements != 1:
        raise ValueError("generator source digest marker is missing or ambiguous")
    return hashlib.sha256(normalized).hexdigest()


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def _manifest_digest(manifest: dict[str, Any]) -> str:
    return hashlib.sha256(_canonical_json(manifest).encode("utf-8")).hexdigest()


def _manifest_shape_digest(manifest: dict[str, Any]) -> str:
    normalized = json.loads(_canonical_json(manifest))
    normalized["generatorSourceSha256"] = "0" * 64
    return hashlib.sha256(_canonical_json(normalized).encode("utf-8")).hexdigest()


def _require_exact_keys(value: dict[str, Any], expected: set[str], label: str) -> None:
    if set(value) != expected:
        raise ValueError(f"{label} keys differ: expected={sorted(expected)} actual={sorted(value)}")


def _validate_manifest(manifest: dict[str, Any]) -> None:
    _require_exact_keys(
        manifest,
        {
            "mappingVersion",
            "generatorVersion",
            "generatorSourceSha256",
            "resourceLimits",
            "domains",
            "correctionCompatibility",
            "rootFields",
            "structuralCounts",
            "occurrences",
            "ownerContracts",
            "relationships",
            "globalAlgorithms",
        },
        "manifest",
    )
    if manifest["mappingVersion"] != "paprnav-ad-v4-obligation-mapping-1":
        raise ValueError("mappingVersion differs")
    if manifest["generatorVersion"] != GENERATOR_VERSION:
        raise ValueError("generatorVersion differs")
    source_digest = _generator_source_digest()
    if GENERATOR_SOURCE_SHA256 != source_digest:
        raise ValueError("generator source constant is stale")
    if manifest["generatorSourceSha256"] != source_digest:
        raise ValueError("manifest generatorSourceSha256 differs")
    if manifest["resourceLimits"] != EXPECTED_LIMITS:
        raise ValueError("resource limits differ from the reviewed contract")
    if manifest["rootFields"] != EXPECTED_ROOT_FIELDS:
        raise ValueError("root field order differs")
    if manifest["structuralCounts"] != EXPECTED_COUNTS:
        raise ValueError("structural count inventory/order differs")
    if len(manifest["globalAlgorithms"]) != len(set(manifest["globalAlgorithms"])):
        raise ValueError("global algorithm registry contains duplicates")
    if set(manifest["globalAlgorithms"]) != EXPECTED_ALGORITHMS:
        raise ValueError("global algorithm registry differs")
    domains = manifest["domains"]
    expected_domains = {
        "subtree", "projection", "row", "request", "authClaims", "event",
        "correctionBindingSet", "legacyApplicabilityRow",
    }
    _require_exact_keys(domains, expected_domains, "domains")
    if any(not isinstance(value, str) or not value.endswith("\\0") for value in domains.values()):
        raise ValueError("every domain must carry the literal manifest NUL marker")
    correction_compatibility = manifest["correctionCompatibility"]
    expected_namespaces = [
        {"namespace": "directiveIdentity", "ownerSlice": "foundation", "targetNodeType": None},
        {"namespace": "supersessionRelations", "ownerSlice": "foundation", "targetNodeType": None},
        {"namespace": "productScopes", "ownerSlice": "slice_3a", "targetNodeType": "product_scope"},
        {"namespace": "conditionDefinitions", "ownerSlice": "slice_3a", "targetNodeType": "condition"},
        {"namespace": "applicabilityRules", "ownerSlice": "slice_3a", "targetNodeType": "applicability_rule"},
        {"namespace": "requirements", "ownerSlice": "slice_3b", "targetNodeType": "requirement"},
        {"namespace": "recurrenceGroups", "ownerSlice": "slice_3b", "targetNodeType": "recurrence_group"},
        {"namespace": "amocAuthorityProvisions", "ownerSlice": "slice_3b", "targetNodeType": "amoc_provision"},
    ]
    if correction_compatibility != {
        "namespaces": expected_namespaces,
        "identityDomainKeys": {
            "correctionRoot": "legacyApplicabilityRow",
            "correctionReference": "legacyApplicabilityRow",
            "slice3aBinding": "legacyApplicabilityRow",
            "slice3bBinding": "row",
        },
    }:
        raise ValueError("correction compatibility contract differs")
    for domain_key in correction_compatibility["identityDomainKeys"].values():
        if domain_key not in domains:
            raise ValueError("correction identity domain key is unknown")
    if _manifest_shape_digest(manifest) != EXPECTED_MANIFEST_SHAPE_SHA256:
        raise ValueError("manifest semantics differ from the reviewed shape")

    occurrences = manifest["occurrences"]
    occurrence_ids = [item.get("id") for item in occurrences]
    if len(occurrence_ids) != len(set(occurrence_ids)):
        raise ValueError("occurrence IDs must be unique")
    owner_types = {item.get("nodeType") for item in occurrences}
    expected_owner_types = {
        "incorporated_document", "value_assertion", "requirement", "action",
        "action_step", "branch", "expression", "timing_group", "timing_term",
        "recurrence", "terminating_effect", "recurrence_group", "amoc_provision",
    }
    if owner_types != expected_owner_types:
        raise ValueError("semantic owner union differs")
    for item in occurrences:
        if not isinstance(item.get("selector"), list) or not item["selector"]:
            raise ValueError(f"{item.get('id')} selector is empty")
        for step in item["selector"]:
            if step.get("op") not in {"field", "each"}:
                raise ValueError(f"{item['id']} uses an unsupported selector operation")
        if item["evidence"]["inheritance"] != "none":
            raise ValueError(f"{item['id']} enables implicit evidence inheritance")

    by_occurrence = {item["id"]: item for item in occurrences}
    owner_contracts = manifest["ownerContracts"]
    if len(owner_contracts) != len(expected_owner_types):
        raise ValueError("typed owner contract count differs")
    if {item["nodeType"] for item in owner_contracts} != expected_owner_types:
        raise ValueError("typed owner contract union differs")
    contracted_occurrences: list[str] = []
    for contract in owner_contracts:
        columns = contract["columns"]
        column_names = [column["name"] for column in columns]
        if len(column_names) != len(set(column_names)):
            raise ValueError(f"{contract['nodeType']} owner columns are duplicated")
        for occurrence_id in contract["occurrences"]:
            occurrence = by_occurrence.get(occurrence_id)
            if occurrence is None:
                raise ValueError(f"{contract['nodeType']} references unknown occurrence {occurrence_id}")
            if occurrence["nodeType"] != contract["nodeType"] or occurrence["ownerTable"] != contract["table"]:
                raise ValueError(f"{occurrence_id} owner contract differs from its occurrence")
            contracted_occurrences.append(occurrence_id)
        for reference in contract["references"]:
            if reference["column"] not in column_names:
                raise ValueError(f"{contract['nodeType']} reference column is not stored")
        union = contract["union"]
        if union is not None:
            if union["discriminator"] not in column_names:
                raise ValueError(f"{contract['nodeType']} union discriminator is not stored")
            branch_values = [branch["value"] for branch in union["branches"]]
            if len(branch_values) != len(set(branch_values)):
                raise ValueError(f"{contract['nodeType']} union branches are duplicated")
            for branch in union["branches"]:
                governed = set(branch["requiredColumns"]) | set(branch["forbiddenColumns"])
                if not governed.issubset(column_names):
                    raise ValueError(f"{contract['nodeType']} union governs an unknown column")
                for target in branch.get("referenceTargets", []):
                    if target["column"] not in column_names:
                        raise ValueError(f"{contract['nodeType']} union targets an unknown column")
            allowed_values = set(branch_values)
            for occurrence_id in contract["occurrences"]:
                occurrence_allowed = by_occurrence[occurrence_id].get("allowedUnionBranches")
                if occurrence_allowed is not None and not set(occurrence_allowed).issubset(allowed_values):
                    raise ValueError(f"{occurrence_id} allows an unknown union branch")
        elif any(by_occurrence[value].get("allowedUnionBranches") for value in contract["occurrences"]):
            raise ValueError(f"{contract['nodeType']} has occurrence union limits without a union")
    if sorted(contracted_occurrences) != sorted(occurrence_ids):
        raise ValueError("each occurrence must belong to exactly one typed owner contract")

    relationships = manifest["relationships"]
    relationship_ids = [item.get("id") for item in relationships]
    if len(relationship_ids) != len(set(relationship_ids)):
        raise ValueError("relationship IDs must be unique")
    table_labels = {item["tableLabel"] for item in relationships}
    required_labels = {
        "action-document-ref", "termination-edge", "requirement-dependency",
        "expression-edge", "recurrence-group-member", "correction-binding",
        "materialization-request", "projection-event",
    }
    if table_labels != required_labels:
        raise ValueError("relationship identity registry differs")


def _sql_literal(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def _sql_body_tag(content: str, digest: str) -> str:
    offset = 0
    while True:
        tag = f"$paprnav_obligation_{digest[offset:offset + 12]}$"
        if tag not in content:
            return tag
        offset += 1


def _render_selector_sql(occurrence: dict[str, Any], owner_contract: dict[str, Any]) -> str:
    from_clause = "FROM (SELECT proposal AS value, ''::text AS pointer, '{}'::jsonb AS captures) AS s0"
    prior = "s0"
    joins: list[str] = []
    for index, step in enumerate(occurrence["selector"], start=1):
        alias = f"s{index}"
        if step["op"] == "field":
            name = step["name"]
            pointer_token = name.replace("~", "~0").replace("/", "~1")
            joins.append(
                "CROSS JOIN LATERAL (SELECT "
                f"{prior}.value -> {_sql_literal(name)} AS value, "
                f"{prior}.pointer || '/' || {_sql_literal(pointer_token)} AS pointer, "
                f"{prior}.captures AS captures "
                f"WHERE jsonb_typeof({prior}.value) = 'object' AND {prior}.value ? {_sql_literal(name)}) AS {alias}"
            )
        else:
            capture = step["capture"]
            joins.append(
                "CROSS JOIN LATERAL (SELECT item.value, "
                f"{prior}.pointer || '/' || (item.ordinality - 1)::text AS pointer, "
                f"{prior}.captures || jsonb_build_object({_sql_literal(capture)}, item.ordinality - 1) AS captures "
                "FROM jsonb_array_elements(CASE "
                f"WHEN jsonb_typeof({prior}.value) = 'array' THEN {prior}.value ELSE '[]'::jsonb END) "
                "WITH ORDINALITY AS item(value, ordinality)) AS " + alias
            )
        prior = alias
    descriptor = _sql_literal(_canonical_json(occurrence)) + "::jsonb"
    contract = _sql_literal(_canonical_json(owner_contract)) + "::jsonb"
    union = owner_contract["union"]
    if union is None:
        normalized_discriminator = "NULL::text"
        union_allowed = "TRUE"
    else:
        discriminator_column = next(
            value for value in owner_contract["columns"]
            if value["name"] == union["discriminator"]
        )
        source = discriminator_column["source"]
        if source == "$derive.timing_state:state_or_known":
            normalized_discriminator = f"COALESCE({prior}.value ->> 'state', 'known')"
        else:
            normalized_discriminator = f"{prior}.value ->> {_sql_literal(source)}"
        allowed = occurrence.get(
            "allowedUnionBranches",
            [branch["value"] for branch in union["branches"]],
        )
        allowed_sql = ", ".join(_sql_literal(value) for value in allowed)
        union_allowed = f"({normalized_discriminator}) IN ({allowed_sql})"
    return (
        f"SELECT {_sql_literal(occurrence['id'])}::text AS occurrence_id, "
        f"{prior}.pointer AS source_pointer, {prior}.value AS canonical_value, "
        f"{prior}.captures AS captures, {descriptor} AS descriptor, "
        f"{contract} AS owner_contract, {normalized_discriminator} AS normalized_discriminator, "
        f"{union_allowed} AS union_allowed\n"
        + from_clause + "\n" + "\n".join(joins)
    )


def _render_python(manifest: dict[str, Any], digest: str) -> str:
    manifest_json = _canonical_json(manifest)
    return f'''# Generated by scripts/generate_ad_v4_obligation_mapping.py. Do not edit.
from __future__ import annotations

import json
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any

MAPPING_VERSION = {manifest["mappingVersion"]!r}
MAPPING_DIGEST = {digest!r}
GENERATOR_VERSION = {GENERATOR_VERSION!r}
GENERATOR_SOURCE_SHA256 = {GENERATOR_SOURCE_SHA256!r}
MAPPING_MANIFEST_JSON = {manifest_json!r}

def _freeze(value: Any) -> Any:
    if isinstance(value, dict):
        return MappingProxyType({{key: _freeze(child) for key, child in value.items()}})
    if isinstance(value, list):
        return tuple(_freeze(child) for child in value)
    return value

MAPPING_MANIFEST = _freeze(json.loads(MAPPING_MANIFEST_JSON))
RESOURCE_LIMITS = MAPPING_MANIFEST["resourceLimits"]
DOMAINS = MappingProxyType({{key: value[:-2].encode("utf-8") + b"\\x00" for key, value in MAPPING_MANIFEST["domains"].items()}})
CORRECTION_COMPATIBILITY = MAPPING_MANIFEST["correctionCompatibility"]
ROOT_FIELDS = tuple(MAPPING_MANIFEST["rootFields"])
STRUCTURAL_COUNTS = tuple(MAPPING_MANIFEST["structuralCounts"])
OCCURRENCES = MAPPING_MANIFEST["occurrences"]
OWNER_CONTRACTS = MAPPING_MANIFEST["ownerContracts"]
RELATIONSHIPS = MAPPING_MANIFEST["relationships"]
GLOBAL_ALGORITHMS = frozenset(MAPPING_MANIFEST["globalAlgorithms"])

@dataclass(frozen=True)
class SelectedOccurrence:
    descriptor_id: str
    source_pointer: str
    canonical_value: Any
    captures: MappingProxyType
    descriptor: MappingProxyType
    owner_contract: MappingProxyType

def _escape_pointer(value: str) -> str:
    return value.replace("~", "~0").replace("/", "~1")

def select_occurrences(proposal: dict[str, Any]) -> tuple[SelectedOccurrence, ...]:
    selected: list[SelectedOccurrence] = []
    contracts = {{value["nodeType"]: value for value in OWNER_CONTRACTS}}
    for descriptor in OCCURRENCES:
        states: list[tuple[Any, str, dict[str, int]]] = [(proposal, "", {{}})]
        for step in descriptor["selector"]:
            next_states: list[tuple[Any, str, dict[str, int]]] = []
            if step["op"] == "field":
                name = step["name"]
                for value, pointer, captures in states:
                    if isinstance(value, dict) and name in value:
                        next_states.append((value[name], pointer + "/" + _escape_pointer(name), captures))
            else:
                capture = step["capture"]
                for value, pointer, captures in states:
                    if isinstance(value, list):
                        for ordinal, child in enumerate(value):
                            child_captures = dict(captures)
                            child_captures[capture] = ordinal
                            next_states.append((child, pointer + "/" + str(ordinal), child_captures))
            states = next_states
        selected.extend(
            SelectedOccurrence(
                descriptor["id"], pointer, value, MappingProxyType(dict(captures)),
                descriptor, contracts[descriptor["nodeType"]],
            )
            for value, pointer, captures in states
        )
    return tuple(selected)

def normalized_union_discriminator(selected: SelectedOccurrence) -> str | None:
    union = selected.owner_contract["union"]
    if union is None:
        return None
    column = next(value for value in selected.owner_contract["columns"] if value["name"] == union["discriminator"])
    source = column["source"]
    if source == "$derive.timing_state:state_or_known":
        result = selected.canonical_value.get("state", "known")
    else:
        result = selected.canonical_value.get(source)
    allowed = selected.descriptor.get("allowedUnionBranches")
    if allowed is None:
        allowed = tuple(branch["value"] for branch in union["branches"])
    if result not in allowed:
        raise ValueError(f"{{selected.descriptor_id}} uses forbidden union branch {{result!r}}")
    return result

def expected_reference_targets(selected: SelectedOccurrence) -> tuple[tuple[str, str], ...]:
    discriminator = normalized_union_discriminator(selected)
    if discriminator is None:
        return ()
    branch = next(value for value in selected.owner_contract["union"]["branches"] if value["value"] == discriminator)
    return tuple((value["column"], value["targetNodeType"]) for value in branch.get("referenceTargets", ()))
'''


def _render_sql(manifest: dict[str, Any], digest: str) -> str:
    manifest_json = _canonical_json(manifest).replace("'", "''")
    owner_by_type = {value["nodeType"]: value for value in manifest["ownerContracts"]}
    selector_body = "\nUNION ALL\n".join(
        _render_selector_sql(value, owner_by_type[value["nodeType"]])
        for value in manifest["occurrences"]
    )
    full_body = manifest_json + selector_body
    tag = _sql_body_tag(full_body, digest)
    return f'''-- Generated by scripts/generate_ad_v4_obligation_mapping.py. Do not edit.
-- mapping-version: {manifest["mappingVersion"]}
-- mapping-sha256: {digest}
-- generator-version: {GENERATOR_VERSION}
-- generator-source-sha256: {GENERATOR_SOURCE_SHA256}

CREATE OR REPLACE FUNCTION paprnav_v4_obligation_mapping_digest()
RETURNS text
LANGUAGE sql
IMMUTABLE
PARALLEL SAFE
AS {tag} SELECT '{digest}'::text {tag};

CREATE OR REPLACE FUNCTION paprnav_v4_obligation_mapping_manifest()
RETURNS jsonb
LANGUAGE sql
IMMUTABLE
PARALLEL SAFE
AS {tag} SELECT '{manifest_json}'::jsonb {tag};

CREATE OR REPLACE FUNCTION paprnav_v4_obligation_utf16_sort_key(p_value text)
RETURNS bytea
LANGUAGE plpgsql
IMMUTABLE
STRICT
PARALLEL SAFE
AS {tag}
DECLARE
    result bytea := ''::bytea;
    codepoint integer;
    adjusted integer;
    code_unit integer;
    position integer;
BEGIN
    FOR position IN 1..char_length(p_value) LOOP
        codepoint := ascii(substr(p_value, position, 1));
        IF codepoint <= 65535 THEN
            code_unit := codepoint;
            result := result || decode(lpad(to_hex(code_unit), 4, '0'), 'hex');
        ELSE
            adjusted := codepoint - 65536;
            code_unit := 55296 + (adjusted >> 10);
            result := result || decode(lpad(to_hex(code_unit), 4, '0'), 'hex');
            code_unit := 56320 + (adjusted & 1023);
            result := result || decode(lpad(to_hex(code_unit), 4, '0'), 'hex');
        END IF;
    END LOOP;
    RETURN result;
END
{tag};

CREATE OR REPLACE FUNCTION paprnav_v4_obligation_record_at(p_value jsonb, p_depth integer)
RETURNS text
LANGUAGE plpgsql
IMMUTABLE
STRICT
PARALLEL SAFE
AS {tag}
DECLARE
    result text;
    value_type text := jsonb_typeof(p_value);
BEGIN
    IF p_depth < 0 OR p_depth > {manifest["resourceLimits"]["maxDepth"]} THEN
        RAISE EXCEPTION 'internal canonical nesting depth exceeded'
            USING ERRCODE = '22023';
    END IF;
    CASE value_type
        WHEN 'object' THEN
            SELECT '{{' || coalesce(string_agg(
                to_jsonb(key)::text || ':' || paprnav_v4_obligation_record_at(value, p_depth + 1),
                ',' ORDER BY paprnav_v4_obligation_utf16_sort_key(key)
            ), '') || '}}'
            INTO result
            FROM jsonb_each(p_value);
        WHEN 'array' THEN
            SELECT '[' || coalesce(string_agg(
                paprnav_v4_obligation_record_at(value, p_depth + 1), ',' ORDER BY ordinality
            ), '') || ']'
            INTO result
            FROM jsonb_array_elements(p_value) WITH ORDINALITY;
        WHEN 'string' THEN
            result := p_value::text;
        WHEN 'boolean' THEN
            result := p_value::text;
        WHEN 'null' THEN
            result := 'null';
        WHEN 'number' THEN
            result := p_value::text;
            IF result !~ '^(0|[1-9][0-9]*)$' THEN
                RAISE EXCEPTION 'unsupported internal canonical number: %', result
                    USING ERRCODE = '22023';
            END IF;
            IF result::numeric > {manifest["resourceLimits"]["maxInternalInteger"]} THEN
                RAISE EXCEPTION 'internal canonical integer exceeds storage limit: %', result
                    USING ERRCODE = '22023';
            END IF;
        ELSE
            RAISE EXCEPTION 'unsupported internal canonical JSON type: %', value_type
                USING ERRCODE = '22023';
    END CASE;
    RETURN result;
END
{tag};

CREATE OR REPLACE FUNCTION paprnav_v4_obligation_record(p_value jsonb)
RETURNS text
LANGUAGE sql
IMMUTABLE
STRICT
PARALLEL SAFE
AS {tag}
    SELECT paprnav_v4_obligation_record_at(p_value, 0)
{tag};

CREATE OR REPLACE FUNCTION paprnav_v4_obligation_select_occurrences(proposal jsonb)
RETURNS TABLE(
    occurrence_id text,
    source_pointer text,
    canonical_value jsonb,
    captures jsonb,
    descriptor jsonb,
    owner_contract jsonb,
    normalized_discriminator text,
    union_allowed boolean
)
LANGUAGE sql
IMMUTABLE
PARALLEL SAFE
AS {tag}
{selector_body}
{tag};
'''


def _write_or_check(path: Path, content: str, *, check: bool) -> bool:
    if check:
        if not path.exists() or path.read_text(encoding="utf-8") != content:
            print(f"stale generated file: {path.relative_to(REPOSITORY_ROOT)}", file=sys.stderr)
            return False
        return True
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return True


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--print-source-digest", action="store_true")
    args = parser.parse_args()
    if args.print_source_digest:
        print(_generator_source_digest())
        return 0
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    _validate_manifest(manifest)
    digest = _manifest_digest(manifest)
    outputs = {
        PYTHON_OUTPUT: _render_python(manifest, digest),
        SQL_OUTPUT: _render_sql(manifest, digest),
    }
    valid = all(_write_or_check(path, content, check=args.check) for path, content in outputs.items())
    if not valid:
        return 1
    print(digest)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
