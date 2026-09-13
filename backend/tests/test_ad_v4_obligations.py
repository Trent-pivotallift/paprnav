import hashlib
import importlib.util
import json
import subprocess
import sys
import re
from collections import UserDict
from copy import deepcopy
from dataclasses import fields, replace
from decimal import Decimal
from pathlib import Path
from types import MappingProxyType

import pytest

from app.services import ad_v4_applicability, ad_v4_obligations
from app.models.core import Base
from app.services.ad_v4_candidates import CANONICALIZATION_VERSION_V2, canonical_bytes
from app.services.ad_v4_obligation_mapping_v1 import (
    CORRECTION_COMPATIBILITY,
    DOMAINS,
    GENERATOR_SOURCE_SHA256,
    GENERATOR_VERSION,
    GLOBAL_ALGORITHMS,
    MAPPING_DIGEST,
    MAPPING_MANIFEST,
    MAPPING_MANIFEST_JSON,
    MAPPING_VERSION,
    OCCURRENCES,
    OWNER_CONTRACTS,
    RELATIONSHIPS,
    RESOURCE_LIMITS,
    ROOT_FIELDS,
    STRUCTURAL_COUNTS,
    expected_reference_targets,
    normalized_union_discriminator,
    select_occurrences,
)
from app.services.ad_v4_obligations import (
    ObligationIntegrityError,
    _verify_combined_requirement_graph,
    build_correction_reference_snapshot,
    make_applicability_target,
    materialize_authority_family,
    materialize_correction_binding_family,
    materialize_document_family,
    materialize_expression_family,
    materialize_obligation_projection_graph,
    materialize_recurrence_group_family,
    materialize_requirement_family,
    materialize_requirement_relationship_family,
    materialize_timing_recurrence_family,
    obligation_record_bytes,
    reconstruct_obligation_datums,
    verify_document_family,
    verify_authority_family,
    verify_correction_binding_family,
    verify_expression_family,
    verify_recurrence_group_family,
    verify_requirement_family,
    verify_requirement_relationship_family,
    verify_timing_recurrence_family,
)
from app.services.ad_v4_obligation_persistence import (
    persist_obligation_projection_graph,
)


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = REPOSITORY_ROOT / "backend/app/contracts/ad_v4_obligation_mapping_v1.json"
GENERATOR_PATH = REPOSITORY_ROOT / "scripts/generate_ad_v4_obligation_mapping.py"


def test_obligation_mapping_manifest_and_generated_outputs_are_exact():
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    canonical = json.dumps(manifest, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode()
    assert hashlib.sha256(canonical).hexdigest() == MAPPING_DIGEST
    assert MAPPING_DIGEST == "e229c6008f323cb6622e96b286b6ecb93ec7f2be47a5e4dd48bec294af51465d"
    assert MAPPING_VERSION == "paprnav-ad-v4-obligation-mapping-1"
    assert GENERATOR_VERSION == "paprnav-ad-v4-obligation-mapgen-1"
    assert manifest["generatorSourceSha256"] == GENERATOR_SOURCE_SHA256
    assert json.loads(MAPPING_MANIFEST_JSON) == manifest
    completed = subprocess.run(
        [sys.executable, str(GENERATOR_PATH), "--check"],
        cwd=REPOSITORY_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr
    assert completed.stdout.strip() == MAPPING_DIGEST


def test_generated_correction_compatibility_is_shared_by_both_slices():
    expected_namespaces = [
        ("directiveIdentity", "foundation", None),
        ("supersessionRelations", "foundation", None),
        ("productScopes", "slice_3a", "product_scope"),
        ("conditionDefinitions", "slice_3a", "condition"),
        ("applicabilityRules", "slice_3a", "applicability_rule"),
        ("requirements", "slice_3b", "requirement"),
        ("recurrenceGroups", "slice_3b", "recurrence_group"),
        ("amocAuthorityProvisions", "slice_3b", "amoc_provision"),
    ]
    assert [
        (row["namespace"], row["ownerSlice"], row["targetNodeType"])
        for row in CORRECTION_COMPATIBILITY["namespaces"]
    ] == expected_namespaces
    assert dict(CORRECTION_COMPATIBILITY["identityDomainKeys"]) == {
        "correctionRoot": "legacyApplicabilityRow",
        "correctionReference": "legacyApplicabilityRow",
        "slice3aBinding": "legacyApplicabilityRow",
        "slice3bBinding": "row",
    }
    assert ad_v4_applicability._CORRECTION_OWNER_BY_NAMESPACE == {
        namespace: owner_slice
        for namespace, owner_slice, _ in expected_namespaces
    }
    assert ad_v4_obligations._CORRECTION_OWNER_BY_NAMESPACE == (
        ad_v4_applicability._CORRECTION_OWNER_BY_NAMESPACE
    )
    assert DOMAINS["legacyApplicabilityRow"] == ad_v4_applicability.ROW_DOMAIN
    assert DOMAINS["row"] != ad_v4_applicability.ROW_DOMAIN
    ad_v4_applicability._validate_correction_compatibility_contract()


@pytest.mark.parametrize("namespace", [
    "directiveIdentity", "supersessionRelations", "productScopes",
    "conditionDefinitions", "applicabilityRules", "requirements",
    "recurrenceGroups", "amocAuthorityProvisions",
])
def test_obligation_contract_rejects_each_namespace_classification_drift(
    monkeypatch, namespace,
):
    changed = dict(ad_v4_obligations._CORRECTION_OWNER_BY_NAMESPACE)
    changed[namespace] = "slice_3b" if changed[namespace] != "slice_3b" else "foundation"
    monkeypatch.setattr(
        ad_v4_obligations, "_CORRECTION_OWNER_BY_NAMESPACE", changed,
    )
    with pytest.raises(ObligationIntegrityError, match="contract differs"):
        ad_v4_obligations._validate_correction_binding_contract()
    changed_3a = dict(ad_v4_applicability._CORRECTION_OWNER_BY_NAMESPACE)
    changed_3a[namespace] = changed[namespace]
    monkeypatch.setattr(
        ad_v4_applicability, "_CORRECTION_OWNER_BY_NAMESPACE", changed_3a,
    )
    with pytest.raises(ad_v4_applicability.ADV4Error, match="contract differs"):
        ad_v4_applicability._validate_correction_compatibility_contract()


@pytest.mark.parametrize("namespace", [
    "productScopes", "conditionDefinitions", "applicabilityRules",
    "requirements", "recurrenceGroups", "amocAuthorityProvisions",
])
def test_slice3a_rejects_each_correction_target_type_drift(monkeypatch, namespace):
    changed = dict(ad_v4_applicability._CORRECTION_TARGET_TYPE_BY_NAMESPACE)
    changed[namespace] = "wrong_type"
    monkeypatch.setattr(
        ad_v4_applicability, "_CORRECTION_TARGET_TYPE_BY_NAMESPACE", changed,
    )
    with pytest.raises(ad_v4_applicability.ADV4Error, match="contract differs"):
        ad_v4_applicability._validate_correction_compatibility_contract()


@pytest.mark.parametrize("domain_name", [
    "correctionRoot", "correctionReference", "slice3aBinding",
    "slice3bBinding",
])
def test_both_slices_reject_each_correction_identity_domain_drift(
    monkeypatch, domain_name,
):
    changed = dict(CORRECTION_COMPATIBILITY["identityDomainKeys"])
    changed[domain_name] = (
        "row" if changed[domain_name] != "row" else "legacyApplicabilityRow"
    )
    monkeypatch.setattr(
        ad_v4_obligations, "_CORRECTION_IDENTITY_DOMAIN_KEYS", changed,
    )
    with pytest.raises(ObligationIntegrityError, match="contract differs"):
        ad_v4_obligations._validate_correction_binding_contract()
    monkeypatch.setattr(
        ad_v4_applicability, "_CORRECTION_IDENTITY_DOMAIN_KEYS", changed,
    )
    with pytest.raises(ad_v4_applicability.ADV4Error, match="contract differs"):
        ad_v4_applicability._validate_correction_compatibility_contract()


def test_obligation_mapping_closes_domains_counts_owners_and_relationships():
    assert ROOT_FIELDS == (
        "incorporatedDocuments",
        "requirements",
        "recurrenceGroups",
        "amocAuthorityProvisions",
    )
    assert len(STRUCTURAL_COUNTS) == len(set(STRUCTURAL_COUNTS)) == 22
    assert dict(RESOURCE_LIMITS) == {
        "maxDepth": 64,
        "maxTotalNodes": 75_000,
        "maxStringLength": 16_384,
        "maxArrayItems": 2_000,
        "maxAstNodes": 20_000,
        "maxGraphEdges": 40_000,
        "maxInternalInteger": 2_147_483_647,
    }
    assert all(value.endswith(b"\x00") and not value.endswith(b"\\0") for value in DOMAINS.values())
    assert {value["nodeType"] for value in OCCURRENCES} == {
        "incorporated_document",
        "value_assertion",
        "requirement",
        "action",
        "action_step",
        "branch",
        "expression",
        "timing_group",
        "timing_term",
        "recurrence",
        "terminating_effect",
        "recurrence_group",
        "amoc_provision",
    }


def test_obligation_owner_orm_columns_and_nullability_match_generated_contract():
    for owner in OWNER_CONTRACTS:
        table = Base.metadata.tables[owner["table"]]
        expected = {column["name"]: column["nullable"] for column in owner["columns"]}
        actual = {column.name: column.nullable for column in table.columns}
        assert actual == expected


def _complete_projection_graph_fixture():
    documents = _document_vectors()[:2]
    requirements = _expression_requirements()
    requirements[0]["action"]["orderedSteps"] = [f"step-{index}" for index in range(12)]
    requirements[0]["terminatingEffect"] = {
        "kind": "terminates", "requirementKeys": [],
        "evidenceKeys": ["req-b-termination"],
    }
    provisions = [_authority_provision("authority-main", {
        "state": "known", "value": "Manager, Certification Office",
        "evidenceKeys": ["authority-main-assertion"],
    })]
    proposal = {
        "incorporatedDocuments": documents,
        "requirements": requirements,
        "recurrenceGroups": [],
        "amocAuthorityProvisions": provisions,
        "authoritativeCorrections": [],
    }
    return proposal, _all_evidence_bindings(proposal)


def test_complete_projection_graph_closes_owner_counts_hashes_and_generic_reconstruction():
    proposal, bindings = _complete_projection_graph_fixture()
    kwargs = {
        "proposal_id": "proposal-1",
        "directive_id": "directive-1",
        "proposal_canonical_hash": "1" * 64,
        "evidence_binding_hash": "2" * 64,
        "app_projection_id": "app-projection-1",
        "app_projection_hash": "3" * 64,
        "canonical_proposal": proposal,
        "evidence_bindings": bindings,
        "app_targets": _expression_app_targets(),
        "foundation_refs": build_correction_reference_snapshot(
            proposal_id="proposal-1", canonical_corrections=[],
        ),
    }
    graph = materialize_obligation_projection_graph(**kwargs)
    assert graph == materialize_obligation_projection_graph(**kwargs)
    assert graph.projection.id.startswith("aox_")
    assert len(graph.projection.identity_hash) == 64
    assert graph.projection.counts["semanticNodeCount"] == len(graph.semantic_nodes)
    assert graph.projection.counts["datumCount"] == len(graph.datums)
    assert graph.projection.counts["evidenceLinkCount"] == len(graph.evidence_links)
    assert graph.projection.counts["terminatingEffectCount"] == 2
    assert graph.projection.counts["terminationEdgeCount"] == 0
    assert tuple(graph.projection.counts) == STRUCTURAL_COUNTS
    expected_subtree = json.loads(canonical_bytes(
        {field: proposal[field] for field in ROOT_FIELDS},
        CANONICALIZATION_VERSION_V2,
    ))
    assert reconstruct_obligation_datums(graph.datums) == expected_subtree
    envelope = json.loads(graph.projection.projection_canonical_bytes)
    assert envelope["counts"] == dict(graph.projection.counts)
    assert envelope["obligationSubtreeHash"] == graph.projection.obligation_subtree_hash
    assert graph.projection.projection_hash == hashlib.sha256(
        DOMAINS["projection"] + graph.projection.projection_canonical_bytes
    ).hexdigest()


def test_generic_projection_reconstruction_rejects_array_reordering():
    proposal, bindings = _complete_projection_graph_fixture()
    graph = materialize_obligation_projection_graph(
        proposal_id="proposal-1", directive_id="directive-1",
        proposal_canonical_hash="1" * 64, evidence_binding_hash="2" * 64,
        app_projection_id="app-projection-1", app_projection_hash="3" * 64,
        canonical_proposal=proposal, evidence_bindings=bindings,
        app_targets=_expression_app_targets(),
        foundation_refs=build_correction_reference_snapshot(
            proposal_id="proposal-1", canonical_corrections=[],
        ),
    )
    target = next(
        index for index, row in enumerate(graph.datums)
        if row.json_pointer == "/requirements/1"
    )
    corrupted = list(graph.datums)
    corrupted[target] = replace(corrupted[target], array_ordinal=7)
    with pytest.raises(ObligationIntegrityError, match="array order"):
        reconstruct_obligation_datums(corrupted)


def test_complete_projection_graph_maps_to_every_structural_orm_table():
    proposal, bindings = _complete_projection_graph_fixture()
    graph = materialize_obligation_projection_graph(
        proposal_id="proposal-1", directive_id="directive-1",
        proposal_canonical_hash="1" * 64, evidence_binding_hash="2" * 64,
        app_projection_id="app-projection-1", app_projection_hash="3" * 64,
        canonical_proposal=proposal, evidence_bindings=bindings,
        app_targets=_expression_app_targets(),
        foundation_refs=build_correction_reference_snapshot(
            proposal_id="proposal-1", canonical_corrections=[],
        ),
    )

    class RecordingSession:
        def __init__(self):
            self.rows = []
            self.flushes = 0

        def add(self, row):
            self.rows.append(row)

        def add_all(self, rows):
            self.rows.extend(rows)

        def flush(self):
            self.flushes += 1

    db = RecordingSession()
    projection = persist_obligation_projection_graph(db, graph)
    assert projection.id == graph.projection.id
    assert projection.semantic_node_count == len(graph.semantic_nodes)
    assert projection.datum_count == len(graph.datums)
    assert db.flushes == 3
    table_counts = {}
    for row in db.rows:
        table_counts[row.__tablename__] = table_counts.get(row.__tablename__, 0) + 1
    assert table_counts["ad_v4_candidate_obligation_projections"] == 1
    assert table_counts["ad_v4_candidate_obligation_semantic_nodes"] == len(graph.semantic_nodes)
    assert table_counts["ad_v4_candidate_obligation_data"] == len(graph.datums)
    assert table_counts["ad_v4_candidate_obligation_evidence_links"] == len(graph.evidence_links)
    assert table_counts["ad_v4_candidate_obligation_documents"] == graph.projection.counts["documentCount"]
    assert table_counts["ad_v4_candidate_obligation_requirements"] == graph.projection.counts["requirementCount"]
    assert table_counts["ad_v4_candidate_obligation_expressions"] == graph.projection.counts["expressionCount"]
    assert table_counts["ad_v4_candidate_obligation_amoc_provisions"] == graph.projection.counts["amocProvisionCount"]

    projection = Base.metadata.tables["ad_v4_candidate_obligation_projections"]
    count_columns = {
        re.sub(r"(?<!^)(?=[A-Z])", "_", count).lower()
        for count in STRUCTURAL_COUNTS
    }
    assert count_columns <= set(projection.columns.keys())
    assert len({value["id"] for value in OCCURRENCES}) == len(OCCURRENCES)
    assert len(OWNER_CONTRACTS) == 13
    assert {
        occurrence_id
        for contract in OWNER_CONTRACTS
        for occurrence_id in contract["occurrences"]
    } == {value["id"] for value in OCCURRENCES}
    assert {value["tableLabel"] for value in RELATIONSHIPS} == {
        "action-document-ref",
        "termination-edge",
        "requirement-dependency",
        "expression-edge",
        "recurrence-group-member",
        "correction-binding",
        "materialization-request",
        "projection-event",
    }
    assert GLOBAL_ALGORITHMS == {
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


def _generator_module():
    spec = importlib.util.spec_from_file_location("obligation_mapgen", GENERATOR_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize(
    "mutate",
    [
        lambda value: value["occurrences"].pop(2),
        lambda value: value["occurrences"][1]["selector"].append({"op": "field", "name": "wrong"}),
        lambda value: value["relationships"][0].update({"identityProperties": ["projectionId", "wrong"]}),
        lambda value: value["relationships"][0].update({"table": "ad_v4_candidate_obligation_wrong"}),
        lambda value: value["domains"].update({"row": "paprnav:wrong\\0"}),
        lambda value: value["globalAlgorithms"].append("event_fold"),
        lambda value: value["ownerContracts"][1]["columns"].pop(),
        lambda value: value["ownerContracts"][1]["columns"][5].update({"nullable": False}),
        lambda value: value["ownerContracts"][1]["union"]["branches"].pop(),
        lambda value: value["ownerContracts"][2]["references"][0].update({"target": "D1"}),
        lambda value: value["ownerContracts"][3]["children"][0].update({"cardinality": "exactly_one"}),
    ],
)
def test_obligation_mapping_rejects_every_material_contract_mutation(mutate):
    module = _generator_module()
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    mutate(manifest)
    with pytest.raises(ValueError):
        module._validate_manifest(manifest)


def test_generated_mapping_is_recursively_immutable_and_selectors_execute():
    with pytest.raises(TypeError):
        MAPPING_MANIFEST["occurrences"][0]["selector"][0]["name"] = "wrong"
    with pytest.raises(AttributeError):
        MAPPING_MANIFEST["ownerContracts"][0]["columns"].append("wrong")

    selected = select_occurrences({
        "incorporatedDocuments": [{
            "documentRefKey": "doc-a",
            "documentNumber": {"state": "known"},
            "revision": {"state": "unknown"},
            "retention": {"state": "unknown"},
        }],
        "requirements": [],
        "recurrenceGroups": [],
        "amocAuthorityProvisions": [],
    })
    assert [(item.descriptor_id, item.source_pointer) for item in selected] == [
        ("D1", "/incorporatedDocuments/0"),
        ("D2", "/incorporatedDocuments/0/documentNumber"),
        ("D3", "/incorporatedDocuments/0/revision"),
        ("D4", "/incorporatedDocuments/0/retention"),
    ]


def test_mapping_schema_parity_for_specialized_unions_and_references():
    occurrences = {value["id"]: value for value in OCCURRENCES}
    contracts = {value["nodeType"]: value for value in OWNER_CONTRACTS}
    assert occurrences["D4"]["allowedUnionBranches"] == ("unknown",)
    assert occurrences["R6"]["allowedUnionBranches"] == ("known",)
    assert next(
        value["source"]
        for value in contracts["expression"]["columns"]
        if value["name"] == "required_state"
    ) == "requirementState"
    expression_targets = {
        branch["value"]: tuple(
            (target["column"], target["targetNodeType"])
            for target in branch.get("referenceTargets", ())
        )
        for branch in contracts["expression"]["union"]["branches"]
    }
    assert expression_targets == {
        "scope_ref": (("app_target_node_id", "product_scope"),),
        "predicate_ref": (("app_target_node_id", "condition"),),
        "rule_ref": (("app_target_node_id", "applicability_rule"),),
        "requirement_state_ref": (("requirement_target_node_id", "requirement"),),
        "not": (),
        "all": (),
        "any": (),
    }
    assert next(
        child for child in contracts["recurrence_group"]["children"]
        if child["target"] == "G2"
    )["cardinality"] == "two_or_more"
    correction = next(value for value in RELATIONSHIPS if value["id"] == "CB")
    assert "/changedSemanticRefs/" in correction["sourcePattern"]

    timing_selected = select_occurrences({
        "incorporatedDocuments": [],
        "requirements": [{"recurrence": {"kind": "interval", "timing": {"logic": "all", "terms": []}}}],
        "recurrenceGroups": [],
        "amocAuthorityProvisions": [],
    })
    recurrence_timing = next(value for value in timing_selected if value.descriptor_id == "R6")
    assert normalized_union_discriminator(recurrence_timing) == "known"

    invalid_retention = select_occurrences({
        "incorporatedDocuments": [{"retention": {"state": "known"}}],
        "requirements": [],
        "recurrenceGroups": [],
        "amocAuthorityProvisions": [],
    })
    retention = next(value for value in invalid_retention if value.descriptor_id == "D4")
    with pytest.raises(ValueError, match="forbidden union branch"):
        normalized_union_discriminator(retention)

    for node_type, expected in {
        "scope_ref": (("app_target_node_id", "product_scope"),),
        "predicate_ref": (("app_target_node_id", "condition"),),
        "rule_ref": (("app_target_node_id", "applicability_rule"),),
        "requirement_state_ref": (("requirement_target_node_id", "requirement"),),
    }.items():
        expression = {"nodeType": node_type}
        selected = select_occurrences({
            "incorporatedDocuments": [],
            "requirements": [{"activationExpression": expression}],
            "recurrenceGroups": [],
            "amocAuthorityProvisions": [],
        })
        activation = next(value for value in selected if value.descriptor_id == "EACT")
        assert expected_reference_targets(activation) == expected


def test_generated_sql_uses_collision_safe_body_tag_and_executable_selector():
    module = _generator_module()
    digest = "a" * 12 + "b" * 52
    first_tag = "$paprnav_obligation_aaaaaaaaaaaa$"
    tag = module._sql_body_tag(f"hostile {first_tag} and ' quote", digest)
    assert tag != first_tag
    sql = (REPOSITORY_ROOT / "backend/app/db/migrations/sql/20260911_0028_obligation_expectations.sql").read_text()
    assert "paprnav_v4_obligation_select_occurrences" in sql
    assert "jsonb_array_elements(CASE" in sql


def _known(value: str, evidence_key: str) -> dict:
    return {"state": "known", "value": value, "evidenceKeys": [evidence_key]}


def _unknown(evidence_key: str, reason: str = "not_obtained") -> dict:
    return {
        "state": "unknown",
        "reason": reason,
        "temporalScope": {"kind": "source_observation"},
        "evidenceKeys": [evidence_key],
    }


def _not_applicable(evidence_key: str, reason: str = "not used by this publication") -> dict:
    return {
        "state": "not_applicable",
        "reason": reason,
        "temporalScope": {"kind": "publication_version"},
        "evidenceKeys": [evidence_key],
    }


def _document_vectors() -> list[dict]:
    types = [
        "service_bulletin",
        "service_letter",
        "service_instruction",
        "maintenance_manual",
        "approved_data",
        "other_reviewed",
    ]
    branches = [
        (_known("DOC-1", "num-1"), _known("REV-A", "rev-1")),
        (_unknown("num-2"), _unknown("rev-2", "source_ambiguous")),
        (_not_applicable("num-3"), _not_applicable("rev-3", "revision does not apply")),
        (_known("DOC-4", "num-4"), _unknown("rev-4")),
        (_unknown("num-5"), _not_applicable("rev-5")),
        (_not_applicable("num-6"), _known("REV-F", "rev-6")),
    ]
    return [
        {
            "documentRefKey": f"document-{ordinal}",
            "documentType": document_type,
            "documentNumber": number,
            "revision": revision,
            "retention": _unknown(f"ret-{ordinal}"),
            "evidenceKeys": [f"doc-{ordinal}"],
        }
        for ordinal, (document_type, (number, revision)) in enumerate(zip(types, branches), 1)
    ]


def _document_bindings(documents: list[dict]) -> dict[str, str]:
    keys = {
        evidence_key
        for document in documents
        for assertion in (
            document,
            document["documentNumber"],
            document["revision"],
            document["retention"],
        )
        for evidence_key in assertion["evidenceKeys"]
    }
    return {key: f"binding-{key}" for key in keys}


def test_document_family_materializes_all_document_types_and_assertion_unions_exactly():
    documents = _document_vectors()
    bindings = _document_bindings(documents)
    family = materialize_document_family(
        proposal_id="proposal-1",
        projection_id="projection-1",
        canonical_documents=documents,
        evidence_bindings=bindings,
    )

    assert len(family.documents) == 6
    assert len(family.value_assertions) == 18
    assert len(family.semantic_nodes) == 24
    assert len(family.evidence_links) == 24
    assert {row.document_type for row in family.documents} == {
        "service_bulletin", "service_letter", "service_instruction",
        "maintenance_manual", "approved_data", "other_reviewed",
    }
    assert {
        row.state for row in family.value_assertions if row.field_code != "retention"
    } == {"known", "unknown", "not_applicable"}
    assert {
        row.state for row in family.value_assertions if row.field_code == "retention"
    } == {"unknown"}

    nodes = {row.id: row for row in family.semantic_nodes}
    for ordinal, owner in enumerate(family.documents):
        document_node = nodes[owner.semantic_node_id]
        assert document_node.parent_node_id is None
        assert document_node.canonical_ordinal == ordinal
        assert owner.canonical_ordinal == ordinal
        for child_ordinal, child_id in enumerate((
            owner.document_number_node_id,
            owner.revision_node_id,
            owner.retention_node_id,
        )):
            child = nodes[child_id]
            assert child.parent_node_id == document_node.id
            assert child.canonical_ordinal == child_ordinal
            assert child.node_key == child.source_pointer

    assert {
        link.purpose for link in family.evidence_links
    } == {"incorporated_document_clause", "document_identity", "document_retention"}
    verify_document_family(
        proposal_id="proposal-1",
        projection_id="projection-1",
        canonical_documents=documents,
        evidence_bindings=bindings,
        family=family,
    )


def test_document_family_ids_and_hashes_are_deterministic_and_occurrence_specific():
    documents = _document_vectors()[:1]
    bindings = _document_bindings(documents)
    family = materialize_document_family(
        proposal_id="proposal-1",
        projection_id="projection-1",
        canonical_documents=documents,
        evidence_bindings=bindings,
    )
    repeated = materialize_document_family(
        proposal_id="proposal-1",
        projection_id="projection-1",
        canonical_documents=documents,
        evidence_bindings=bindings,
    )
    assert family == repeated

    root = family.semantic_nodes[0]
    identity = {
        "projectionId": "projection-1",
        "nodeType": "incorporated_document",
        "nodeKey": "document-1",
        "pointer": "/incorporatedDocuments/0",
    }
    expected_hash = hashlib.sha256(
        DOMAINS["row"]
        + obligation_record_bytes({"table": "semantic-node", "identity": identity})
    ).hexdigest()
    assert root.id == f"aon_{expected_hash[:32]}"
    assert root.identity_hash == expected_hash
    assert root.canonical_node_hash == hashlib.sha256(
        canonical_bytes(documents[0], CANONICALIZATION_VERSION_V2)
    ).hexdigest()
    assert family.semantic_nodes[1].id != family.semantic_nodes[2].id


def test_internal_record_canonicalization_is_exact_and_narrower_than_general_json():
    assert obligation_record_bytes({"z": 0, "a": None, "b": True}) == b'{"a":null,"b":true,"z":0}'
    with pytest.raises(ObligationIntegrityError, match="nonnegative"):
        obligation_record_bytes({"ordinal": -1})
    with pytest.raises(ObligationIntegrityError, match="unsupported"):
        obligation_record_bytes({"ordinal": 1.5})


@pytest.mark.parametrize(
    "value",
    [
        ("tuple",),
        {"nested": ("tuple",)},
        UserDict({"value": "mapping"}),
        MappingProxyType({"value": "mapping"}),
        type("DictSubclass", (dict,), {})({"value": "mapping"}),
        type("ListSubclass", (list,), {})(["value"]),
        type("StringSubclass", (str,), {})("value"),
        type("IntegerSubclass", (int,), {})(1),
        {"nested": UserDict({"value": "mapping"})},
        {"nested": MappingProxyType({"value": "mapping"})},
    ],
)
def test_internal_record_rejects_non_json_container_types(value):
    with pytest.raises(ObligationIntegrityError, match="unsupported"):
        obligation_record_bytes(value)


@pytest.mark.parametrize("as_key", [False, True])
def test_internal_record_rejects_nested_nul_strings(as_key):
    value = {"outer": [{"\x00" if as_key else "value": "ok" if as_key else "\x00"}]}
    with pytest.raises(ObligationIntegrityError, match=r"U\+0000"):
        obligation_record_bytes(value)


def test_internal_record_rejects_cycles_and_excessive_depth_cleanly():
    cyclic_list = []
    cyclic_list.append(cyclic_list)
    cyclic_dict = {}
    cyclic_dict["self"] = cyclic_dict
    for value in (cyclic_list, cyclic_dict):
        with pytest.raises(ObligationIntegrityError, match="cycle"):
            obligation_record_bytes(value)

    value = "leaf"
    for _ in range(RESOURCE_LIMITS["maxDepth"] + 1):
        value = [value]
    with pytest.raises(ObligationIntegrityError, match="depth"):
        obligation_record_bytes(value)


def test_internal_record_integer_storage_boundary_is_explicit():
    maximum = RESOURCE_LIMITS["maxInternalInteger"]
    assert obligation_record_bytes({"value": maximum}) == (
        f'{{"value":{maximum}}}'.encode()
    )
    with pytest.raises(ObligationIntegrityError, match="storage limit"):
        obligation_record_bytes({"value": maximum + 1})
    with pytest.raises(ObligationIntegrityError, match="storage limit"):
        obligation_record_bytes({"value": 10**4500})


def test_document_materialization_rejects_forged_nested_nul_source():
    documents = _document_vectors()[:1]
    documents[0]["documentNumber"]["value"] = "\x00"
    with pytest.raises(ObligationIntegrityError, match=r"U\+0000"):
        materialize_document_family(
            proposal_id="proposal-1",
            projection_id="projection-1",
            canonical_documents=documents,
            evidence_bindings=_document_bindings(documents),
        )


def _replace_family_row(family, collection: str, ordinal: int, **changes):
    rows = list(getattr(family, collection))
    rows[ordinal] = replace(rows[ordinal], **changes)
    return replace(family, **{collection: tuple(rows)})


@pytest.mark.parametrize(
    "mutate",
    [
        lambda family: replace(family, semantic_nodes=family.semantic_nodes[:-1]),
        lambda family: replace(family, semantic_nodes=family.semantic_nodes + (family.semantic_nodes[-1],)),
        lambda family: _replace_family_row(family, "semantic_nodes", 0, node_type="value_assertion"),
        lambda family: _replace_family_row(family, "semantic_nodes", 1, parent_node_id="aon_cross_projection"),
        lambda family: _replace_family_row(family, "semantic_nodes", 1, canonical_ordinal=2),
        lambda family: _replace_family_row(family, "semantic_nodes", 1, canonical_node_hash="0" * 64),
        lambda family: _replace_family_row(family, "semantic_nodes", 1, node_key="/wrong"),
        lambda family: replace(family, documents=family.documents[::-1]),
        lambda family: _replace_family_row(family, "documents", 0, revision_node_id="aon_wrong"),
        lambda family: replace(family, value_assertions=family.value_assertions[:-1]),
        lambda family: _replace_family_row(family, "value_assertions", 0, field_code="revision"),
        lambda family: _replace_family_row(family, "value_assertions", 0, value="different"),
        lambda family: replace(family, evidence_links=family.evidence_links[:-1]),
        lambda family: _replace_family_row(family, "evidence_links", 0, purpose="document_identity"),
        lambda family: _replace_family_row(family, "evidence_links", 0, candidate_binding_id="binding-other"),
        lambda family: _replace_family_row(family, "evidence_links", 0, canonical_ordinal=1),
        lambda family: _replace_family_row(family, "evidence_links", 0, link_hash="f" * 64),
        lambda family: replace(family, projection_id="projection-other"),
    ],
)
def test_document_family_verified_read_fails_closed_on_every_typed_graph_drift(mutate):
    documents = _document_vectors()[:2]
    bindings = _document_bindings(documents)
    family = materialize_document_family(
        proposal_id="proposal-1",
        projection_id="projection-1",
        canonical_documents=documents,
        evidence_bindings=bindings,
    )
    with pytest.raises(ObligationIntegrityError, match="typed projection differs"):
        verify_document_family(
            proposal_id="proposal-1",
            projection_id="projection-1",
            canonical_documents=documents,
            evidence_bindings=bindings,
            family=mutate(family),
        )


@pytest.mark.parametrize(
    ("mutate", "message"),
    [
        (lambda docs: docs[0].update(documentType="unsupported"), "document type"),
        (lambda docs: docs[0]["retention"].update(state="known", value="forever"), "retention assertion state"),
        (lambda docs: docs[0]["documentNumber"].update(value=""), "known document_number"),
        (lambda docs: docs[0].update(revision=_unknown("rev-1", "x" * 513)), "unknown revision"),
        (lambda docs: docs[0]["evidenceKeys"].clear(), "evidence set"),
    ],
)
def test_document_family_rejects_invalid_closed_shapes(mutate, message):
    documents = _document_vectors()[:1]
    mutate(documents)
    with pytest.raises(ObligationIntegrityError, match=message):
        materialize_document_family(
            proposal_id="proposal-1",
            projection_id="projection-1",
            canonical_documents=documents,
            evidence_bindings=_document_bindings(documents),
        )


def test_document_family_rejects_non_json_tuple_arrays_before_canonical_ordering():
    documents = _document_vectors()[:1]
    documents[0]["evidenceKeys"] = ("ev-zed", "ev-alpha")
    with pytest.raises(ObligationIntegrityError, match="source type is invalid"):
        materialize_document_family(
            proposal_id="proposal-1",
            projection_id="projection-1",
            canonical_documents=documents,
            evidence_bindings={"ev-zed": "binding-zed", "ev-alpha": "binding-alpha"},
        )
    with pytest.raises(ObligationIntegrityError, match="collection is invalid"):
        materialize_document_family(
            proposal_id="proposal-1",
            projection_id="projection-1",
            canonical_documents=tuple(_document_vectors()[:1]),
            evidence_bindings={},
        )


def test_document_family_requires_exact_evidence_binding_and_accepts_512_char_na_reason():
    documents = _document_vectors()[:1]
    documents[0]["revision"] = _not_applicable("rev-1", "r" * 512)
    bindings = _document_bindings(documents)
    materialize_document_family(
        proposal_id="proposal-1",
        projection_id="projection-1",
        canonical_documents=documents,
        evidence_bindings=bindings,
    )
    bindings.pop("rev-1")
    with pytest.raises(ObligationIntegrityError, match="missing evidence binding"):
        materialize_document_family(
            proposal_id="proposal-1",
            projection_id="projection-1",
            canonical_documents=documents,
            evidence_bindings=bindings,
        )


def test_document_family_establishes_canonical_document_and_evidence_set_order():
    documents = _document_vectors()[:2][::-1]
    documents[0]["evidenceKeys"] = ["ev-zed", "ev-alpha"]
    bindings = _document_bindings(documents)
    family = materialize_document_family(
        proposal_id="proposal-1",
        projection_id="projection-1",
        canonical_documents=documents,
        evidence_bindings=bindings,
    )
    assert [row.document_ref_key for row in family.documents] == ["document-1", "document-2"]
    assert [row.canonical_ordinal for row in family.documents] == [0, 1]
    second_links = [
        row for row in family.evidence_links
        if row.semantic_node_id == family.documents[1].semantic_node_id
    ]
    assert [(row.evidence_key, row.canonical_ordinal) for row in second_links] == [
        ("ev-alpha", 0), ("ev-zed", 1),
    ]


@pytest.mark.parametrize(
    ("trusted_proposal_id", "trusted_projection_id"),
    [("proposal-1", "projection-other"), ("proposal-other", "projection-1")],
)
def test_document_family_verified_read_rejects_consistently_restamped_foreign_graph(
    trusted_proposal_id, trusted_projection_id,
):
    documents = _document_vectors()[:1]
    bindings = _document_bindings(documents)
    foreign = materialize_document_family(
        proposal_id="proposal-other",
        projection_id="projection-other",
        canonical_documents=documents,
        evidence_bindings=bindings,
    )
    with pytest.raises(ObligationIntegrityError, match="typed projection differs"):
        verify_document_family(
            proposal_id=trusted_proposal_id,
            projection_id=trusted_projection_id,
            canonical_documents=documents,
            evidence_bindings=bindings,
            family=foreign,
        )


def test_document_family_enforces_nested_array_and_aggregate_resource_limits_before_rows():
    documents = _document_vectors()[:1]
    exact_keys = [f"ev-{ordinal:04d}" for ordinal in range(2_000)]
    documents[0]["evidenceKeys"] = exact_keys
    bindings = _document_bindings(documents)
    exact = materialize_document_family(
        proposal_id="proposal-1",
        projection_id="projection-1",
        canonical_documents=documents,
        evidence_bindings=bindings,
    )
    assert len([
        row for row in exact.evidence_links
        if row.semantic_node_id == exact.documents[0].semantic_node_id
    ]) == 2_000

    documents[0]["evidenceKeys"].append("ev-2000")
    with pytest.raises(ObligationIntegrityError, match="array limit exceeded"):
        materialize_document_family(
            proposal_id="proposal-1",
            projection_id="projection-1",
            canonical_documents=documents,
            evidence_bindings=_document_bindings(documents),
        )

    exact_keys = exact_keys[:2_000]
    aggregate_documents = []
    evidence_counts = [2_000] * 37 + [639, 1, 1]
    for ordinal in range(10):
        document = deepcopy(_document_vectors()[0])
        document["documentRefKey"] = f"aggregate-document-{ordinal}"
        for assertion, evidence_count in zip((
            document,
            document["documentNumber"],
            document["revision"],
            document["retention"],
        ), evidence_counts[ordinal * 4:(ordinal + 1) * 4]):
            assertion["evidenceKeys"] = exact_keys[:evidence_count]
        aggregate_documents.append(document)
    aggregate_bindings = {key: f"binding-{key}" for key in exact_keys}
    exact_aggregate = materialize_document_family(
        proposal_id="proposal-1",
        projection_id="projection-1",
        canonical_documents=aggregate_documents,
        evidence_bindings=aggregate_bindings,
    )
    assert len(exact_aggregate.evidence_links) == 74_641

    aggregate_documents[-1]["retention"]["evidenceKeys"].append("ev-0001")
    with pytest.raises(ObligationIntegrityError, match="node limit exceeded"):
        materialize_document_family(
            proposal_id="proposal-1",
            projection_id="projection-1",
            canonical_documents=aggregate_documents,
            evidence_bindings=aggregate_bindings,
        )


def test_document_family_runtime_metadata_matches_every_generated_d_descriptor():
    documents = _document_vectors()[:1]
    bindings = _document_bindings(documents)
    family = materialize_document_family(
        proposal_id="proposal-1",
        projection_id="projection-1",
        canonical_documents=documents,
        evidence_bindings=bindings,
    )
    descriptors = {row["id"]: row for row in OCCURRENCES if row["id"].startswith("D")}
    nodes = {row.source_pointer: row for row in family.semantic_nodes}
    for descriptor_id in ("D1", "D2", "D3", "D4"):
        descriptor = descriptors[descriptor_id]
        property_name = None if descriptor_id == "D1" else descriptor["selector"][-1]["name"]
        pointer = "/incorporatedDocuments/0" + (f"/{property_name}" if property_name else "")
        node = nodes[pointer]
        assert node.node_type == descriptor["nodeType"]
        expected_ordinal = 0 if descriptor["ordinal"]["op"] == "array_ordinal" else descriptor["ordinal"]["value"]
        assert node.canonical_ordinal == expected_ordinal
        assert {
            link.purpose for link in family.evidence_links
            if link.semantic_node_id == node.id
        } == {descriptor["evidence"]["purpose"]}
    assert descriptors["D4"]["allowedUnionBranches"] == ("unknown",)
    contracts = {row["nodeType"]: row for row in OWNER_CONTRACTS}
    assert {field.name for field in fields(type(family.documents[0]))} == {
        column["name"] for column in contracts["incorporated_document"]["columns"]
    }
    assert {field.name for field in fields(type(family.value_assertions[0]))} == {
        column["name"] for column in contracts["value_assertion"]["columns"]
    }
    assert contracts["incorporated_document"]["union"] is None
    assert {
        (reference["column"], reference["target"], reference["targetNodeType"],
         reference["scope"], reference["cardinality"])
        for reference in contracts["incorporated_document"]["references"]
    } == {
        ("document_number_node_id", "D2", "value_assertion", "same_projection", "required_one"),
        ("revision_node_id", "D3", "value_assertion", "same_projection", "required_one"),
        ("retention_node_id", "D4", "value_assertion", "same_projection", "required_one"),
    }
    assert {
        (child["target"], child["cardinality"], child["ordering"])
        for child in contracts["incorporated_document"]["children"]
    } == {
        ("D2", "exactly_one", "fixed_slot"),
        ("D3", "exactly_one", "fixed_slot"),
        ("D4", "exactly_one", "fixed_slot"),
    }
    assert contracts["value_assertion"]["references"] == ()
    assert contracts["value_assertion"]["children"] == ()
    assert {
        branch["value"]: (
            frozenset(branch["requiredColumns"]),
            frozenset(branch["forbiddenColumns"]),
        )
        for branch in contracts["value_assertion"]["union"]["branches"]
    } == {
        "known": (frozenset({"value"}), frozenset({"reason", "temporal_kind"})),
        "unknown": (frozenset({"reason", "temporal_kind"}), frozenset({"value"})),
        "not_applicable": (frozenset({"reason", "temporal_kind"}), frozenset({"value"})),
    }
    for descriptor in descriptors.values():
        assert descriptor["presence"] == "required"
        assert descriptor["ownerTable"] == contracts[descriptor["nodeType"]]["table"]
        assert descriptor["evidence"] == {
            "source": "own",
            "purpose": descriptor["evidence"]["purpose"],
            "cardinality": "one_or_more",
            "inheritance": "none",
        }


def _timing_unknown(key: str) -> dict:
    return {
        "state": "unknown", "reason": "not_obtained",
        "temporalScope": {"kind": "source_observation"},
        "evidenceKeys": [key],
    }


def _requirement(
    key: str,
    sequence: int,
    *,
    requirement_type: str = "inspection",
    action_type: str = "inspect",
    branch: dict | None = None,
    ordered_steps=...,
    document_keys: list[str] | None = None,
) -> dict:
    action = {
        "actionType": action_type,
        "approvedDataDocumentRefKeys": document_keys or [],
        "evidenceKeys": [f"{key}-action"],
    }
    if ordered_steps is not ...:
        action["orderedSteps"] = ordered_steps
    return {
        "requirementKey": key,
        "sequence": str(sequence),
        "activationExpression": {"nodeType": "scope_ref", "scopeKey": "scope-main"},
        "requirementType": requirement_type,
        "action": action,
        "prerequisiteRequirementKeys": [],
        "branch": branch or {"kind": "required", "evidenceKeys": [f"{key}-branch"]},
        "initialTiming": _timing_unknown(f"{key}-timing"),
        "recurrence": {"kind": "none", "evidenceKeys": [f"{key}-recurrence"]},
        "terminatingEffect": {"kind": "none", "evidenceKeys": [f"{key}-termination"]},
        "evidenceKeys": [f"{key}-requirement"],
    }


def _all_evidence_bindings(value) -> dict[str, str]:
    keys: set[str] = set()
    stack = [value]
    while stack:
        current = stack.pop()
        if isinstance(current, dict):
            for key, child in current.items():
                if key == "evidenceKeys":
                    keys.update(child)
                else:
                    stack.append(child)
        elif isinstance(current, list):
            stack.extend(current)
    return {key: f"binding-{key}" for key in keys}


def _requirement_document_context():
    documents = _document_vectors()[:2]
    bindings = _document_bindings(documents)
    family = materialize_document_family(
        proposal_id="proposal-1", projection_id="projection-1",
        canonical_documents=documents, evidence_bindings=bindings,
    )
    return documents, bindings, family


def test_requirement_action_branch_family_covers_all_enums_unions_and_presence_states():
    requirement_types = [
        "inspection", "replacement", "modification", "software_update",
        "limitation", "reporting", "installation_prohibition",
        "corrective_action", "other_reviewed",
    ]
    action_types = [
        "inspect", "replace", "repair", "modify", "software_update",
        "revise_limitation", "report", "installation_prohibition", "remove",
        "rework", "other_reviewed",
    ]
    branches = [
        {"kind": "required", "evidenceKeys": ["branch-required"]},
        {
            "kind": "conditional",
            "conditionExpression": {"nodeType": "predicate_ref", "conditionKey": "condition-a"},
            "evidenceKeys": ["branch-conditional"],
        },
        {
            "kind": "exception",
            "conditionExpression": {"nodeType": "rule_ref", "ruleKey": "rule-a"},
            "evidenceKeys": ["branch-exception"],
        },
        {
            "kind": "alternative_member", "alternativeGroupKey": "alternative-a",
            "exclusive": False, "evidenceKeys": ["branch-alternative"],
        },
    ]
    requirements = [
        _requirement(
            f"req-{ordinal:02d}", ordinal,
            requirement_type=requirement_types[(ordinal - 1) % len(requirement_types)],
            action_type=action_type,
            branch=deepcopy(branches[(ordinal - 1) % len(branches)]),
            ordered_steps=(... if ordinal == 1 else [] if ordinal == 2 else ["step-a", "step-a"]),
            document_keys=["document-2", "document-1"] if ordinal == 3 else [],
        )
        for ordinal, action_type in enumerate(action_types, 1)
    ][::-1]
    bindings = _all_evidence_bindings(requirements)
    documents, document_bindings, document_family = _requirement_document_context()
    family = materialize_requirement_family(
        proposal_id="proposal-1", projection_id="projection-1",
        canonical_requirements=requirements, evidence_bindings=bindings,
        document_family=document_family, canonical_documents=documents,
        document_evidence_bindings=document_bindings,
    )
    assert len(family.requirements) == len(family.actions) == len(family.branches) == 11
    assert {row.requirement_type for row in family.requirements} == set(requirement_types)
    assert {row.action_type for row in family.actions} == set(action_types)
    assert {row.kind for row in family.branches} == {
        "required", "conditional", "exception", "alternative_member",
    }
    assert [row.requirement_key for row in family.requirements] == [
        f"req-{ordinal:02d}" for ordinal in range(1, 12)
    ]
    assert [(row.ordered_steps_present, row.step_count) for row in family.actions[:3]] == [
        (False, 0), (True, 0), (True, 2),
    ]
    third_refs = [
        row for row in family.action_document_refs
        if row.action_node_id == family.actions[2].semantic_node_id
    ]
    assert [row.document_ref_key for row in third_refs] == ["document-1", "document-2"]
    assert [row.canonical_ordinal for row in third_refs] == [0, 1]
    assert family.action_steps[0].step_text == family.action_steps[1].step_text == "step-a"
    assert family.action_steps[0].semantic_node_id != family.action_steps[1].semantic_node_id
    assert all(
        (row.condition_root_node_id is not None) == (row.kind in {"conditional", "exception"})
        for row in family.branches
    )


def test_requirement_family_preserves_fixed_child_slots_and_deterministic_document_ref_hash():
    requirements = [_requirement(
        "req-one", 1, ordered_steps=["inspect-area"],
        document_keys=["document-1"],
    )]
    documents, document_bindings, document_family = _requirement_document_context()
    family = materialize_requirement_family(
        proposal_id="proposal-1", projection_id="projection-1",
        canonical_requirements=requirements,
        evidence_bindings=_all_evidence_bindings(requirements),
        document_family=document_family, canonical_documents=documents,
        document_evidence_bindings=document_bindings,
    )
    nodes = {node.id: node for node in family.semantic_nodes}
    requirement = family.requirements[0]
    assert nodes[requirement.action_node_id].canonical_ordinal == 0
    assert nodes[requirement.branch_node_id].canonical_ordinal == 2
    relationship = family.action_document_refs[0]
    identity = {
        "projectionId": "projection-1", "actionNodeId": requirement.action_node_id,
        "documentNodeId": relationship.document_node_id, "ordinal": 0,
    }
    expected_hash = hashlib.sha256(
        DOMAINS["row"] + obligation_record_bytes({
            "table": "action-document-ref", "identity": identity,
        })
    ).hexdigest()
    assert relationship.id == f"aor_{expected_hash[:32]}"
    assert relationship.identity_hash == expected_hash
    assert requirement.sequence_text == "1" and requirement.sequence_value == 1


@pytest.mark.parametrize(
    "mutate",
    [
        lambda family: replace(family, requirements=family.requirements[:-1]),
        lambda family: _replace_family_row(family, "semantic_nodes", 0, node_key="wrong"),
        lambda family: _replace_family_row(family, "actions", 0, ordered_steps_present=False),
        lambda family: _replace_family_row(family, "actions", 0, step_count=9),
        lambda family: _replace_family_row(family, "action_steps", 0, step_text="different"),
        lambda family: _replace_family_row(family, "branches", 0, kind="conditional"),
        lambda family: _replace_family_row(family, "branches", 0, alternative_group_key="cross"),
        lambda family: _replace_family_row(family, "action_document_refs", 0, document_node_id="aon-cross"),
        lambda family: _replace_family_row(family, "action_document_refs", 0, canonical_ordinal=1),
        lambda family: _replace_family_row(family, "action_document_refs", 0, identity_hash="0" * 64),
        lambda family: replace(family, evidence_links=family.evidence_links[:-1]),
    ],
)
def test_requirement_family_verified_read_fails_closed_on_typed_drift(mutate):
    requirements = [_requirement(
        "req-one", 1, ordered_steps=["step-one"], document_keys=["document-1"],
    )]
    bindings = _all_evidence_bindings(requirements)
    canonical_documents, document_bindings, documents = _requirement_document_context()
    family = materialize_requirement_family(
        proposal_id="proposal-1", projection_id="projection-1",
        canonical_requirements=requirements, evidence_bindings=bindings,
        document_family=documents, canonical_documents=canonical_documents,
        document_evidence_bindings=document_bindings,
    )
    with pytest.raises(ObligationIntegrityError, match="typed projection differs"):
        verify_requirement_family(
            proposal_id="proposal-1", projection_id="projection-1",
            canonical_requirements=requirements, evidence_bindings=bindings,
            document_family=documents, canonical_documents=canonical_documents,
            document_evidence_bindings=document_bindings, family=mutate(family),
        )


def test_requirement_family_rejects_sequence_branch_reference_and_projection_failures():
    canonical_documents, document_bindings, documents = _requirement_document_context()
    requirements = [_requirement("req-one", 2, document_keys=["document-missing"])]
    with pytest.raises(ObligationIntegrityError, match="sequence set differs"):
        materialize_requirement_family(
            proposal_id="proposal-1", projection_id="projection-1",
            canonical_requirements=requirements,
            evidence_bindings=_all_evidence_bindings(requirements),
            document_family=documents, canonical_documents=canonical_documents,
            document_evidence_bindings=document_bindings,
        )
    requirements[0]["sequence"] = "1"
    with pytest.raises(ObligationIntegrityError, match="unresolved"):
        materialize_requirement_family(
            proposal_id="proposal-1", projection_id="projection-1",
            canonical_requirements=requirements,
            evidence_bindings=_all_evidence_bindings(requirements),
            document_family=documents, canonical_documents=canonical_documents,
            document_evidence_bindings=document_bindings,
        )
    requirements[0]["action"]["approvedDataDocumentRefKeys"] = []
    requirements[0]["branch"] = {
        "kind": "required", "conditionExpression": {
            "nodeType": "scope_ref", "scopeKey": "scope-main",
        },
        "evidenceKeys": ["bad-branch"],
    }
    with pytest.raises(ObligationIntegrityError, match="branch shape differs"):
        materialize_requirement_family(
            proposal_id="proposal-1", projection_id="projection-1",
            canonical_requirements=requirements,
            evidence_bindings=_all_evidence_bindings(requirements),
            document_family=documents, canonical_documents=canonical_documents,
            document_evidence_bindings=document_bindings,
        )
    with pytest.raises(ObligationIntegrityError, match="action document projection differs"):
        materialize_requirement_family(
            proposal_id="proposal-1", projection_id="projection-other",
            canonical_requirements=[], evidence_bindings={}, document_family=documents,
            canonical_documents=canonical_documents,
            document_evidence_bindings=document_bindings,
        )


def test_requirement_family_rejects_corrupt_or_restamped_document_dependency():
    canonical_documents, document_bindings, documents = _requirement_document_context()
    requirements = [_requirement("req-one", 1, document_keys=["document-1"])]
    bindings = _all_evidence_bindings(requirements)
    swapped = list(documents.documents)
    swapped[0] = replace(swapped[0], document_ref_key=documents.documents[1].document_ref_key)
    swapped[1] = replace(swapped[1], document_ref_key=documents.documents[0].document_ref_key)
    corrupt = replace(documents, documents=tuple(swapped))
    with pytest.raises(ObligationIntegrityError, match="incorporated document typed projection differs"):
        materialize_requirement_family(
            proposal_id="proposal-1", projection_id="projection-1",
            canonical_requirements=requirements, evidence_bindings=bindings,
            document_family=corrupt, canonical_documents=canonical_documents,
            document_evidence_bindings=document_bindings,
        )


def test_requirement_family_verified_read_rejects_fully_restamped_q_graph():
    canonical_documents, document_bindings, documents = _requirement_document_context()
    requirements = [_requirement("req-one", 1)]
    bindings = _all_evidence_bindings(requirements)
    foreign_documents = materialize_document_family(
        proposal_id="proposal-other", projection_id="projection-other",
        canonical_documents=canonical_documents, evidence_bindings=document_bindings,
    )
    foreign = materialize_requirement_family(
        proposal_id="proposal-other", projection_id="projection-other",
        canonical_requirements=requirements, evidence_bindings=bindings,
        document_family=foreign_documents, canonical_documents=canonical_documents,
        document_evidence_bindings=document_bindings,
    )
    with pytest.raises(ObligationIntegrityError, match="requirement/action/branch typed projection differs"):
        verify_requirement_family(
            proposal_id="proposal-1", projection_id="projection-1",
            canonical_requirements=requirements, evidence_bindings=bindings,
            document_family=documents, canonical_documents=canonical_documents,
            document_evidence_bindings=document_bindings, family=foreign,
        )
    duplicate = replace(
        documents,
        documents=(documents.documents[0], replace(
            documents.documents[1], document_ref_key=documents.documents[0].document_ref_key,
        )),
    )
    with pytest.raises(ObligationIntegrityError, match="typed projection differs"):
        materialize_requirement_family(
            proposal_id="proposal-1", projection_id="projection-1",
            canonical_requirements=requirements, evidence_bindings=bindings,
            document_family=duplicate, canonical_documents=canonical_documents,
            document_evidence_bindings=document_bindings,
        )
    foreign = materialize_document_family(
        proposal_id="proposal-other", projection_id="projection-other",
        canonical_documents=canonical_documents, evidence_bindings=document_bindings,
    )
    with pytest.raises(ObligationIntegrityError, match="action document projection differs"):
        materialize_requirement_family(
            proposal_id="proposal-1", projection_id="projection-1",
            canonical_requirements=requirements, evidence_bindings=bindings,
            document_family=foreign, canonical_documents=canonical_documents,
            document_evidence_bindings=document_bindings,
        )


def test_requirement_family_physical_owner_columns_match_generated_contracts():
    from app.services.ad_v4_obligations import (
        ObligationActionOwner, ObligationActionStepOwner,
        ObligationBranchOwner, ObligationRequirementOwner,
    )

    contracts = {row["nodeType"]: row for row in OWNER_CONTRACTS}
    for owner_type, node_type in (
        (ObligationRequirementOwner, "requirement"),
        (ObligationActionOwner, "action"),
        (ObligationActionStepOwner, "action_step"),
        (ObligationBranchOwner, "branch"),
    ):
        assert {field.name for field in fields(owner_type)} == {
            column["name"] for column in contracts[node_type]["columns"]
        }
    expected_columns = {
        "requirement": (
            ("semantic_node_id", "$node.id", False, "derived"),
            ("proposal_id", "$projection.proposalId", False, "derived"),
            ("projection_id", "$projection.id", False, "derived"),
            ("requirement_key", "requirementKey", False, "always"),
            ("sequence_text", "sequence", False, "always"),
            ("sequence_value", "$sequencePrecheck.value", False, "derived"),
            ("requirement_type", "requirementType", False, "always"),
            ("canonical_ordinal", "$node.ordinal", False, "derived"),
            ("recurrence_group_present", "$presence.recurrenceGroupKey", False, "derived"),
            ("recurrence_group_key", "recurrenceGroupKey", True, "optional"),
            ("action_node_id", "$child.Q2.id", False, "derived"),
            ("activation_root_node_id", "$child.EACT.id", False, "derived"),
            ("branch_node_id", "$child.Q5.id", False, "derived"),
            ("initial_timing_node_id", "$child.T1.id", False, "derived"),
            ("recurrence_node_id", "$child.R1.id", False, "derived"),
            ("terminating_effect_node_id", "$child.Q7.id", False, "derived"),
        ),
        "action": (
            ("semantic_node_id", "$node.id", False, "derived"),
            ("proposal_id", "$projection.proposalId", False, "derived"),
            ("projection_id", "$projection.id", False, "derived"),
            ("requirement_node_id", "$parent.id", False, "derived"),
            ("action_type", "actionType", False, "always"),
            ("ordered_steps_present", "$presence.orderedSteps", False, "derived"),
            ("step_count", "$count.Q3", False, "derived"),
            ("document_ref_count", "$count.Q4", False, "derived"),
        ),
        "action_step": (
            ("semantic_node_id", "$node.id", False, "derived"),
            ("proposal_id", "$projection.proposalId", False, "derived"),
            ("projection_id", "$projection.id", False, "derived"),
            ("action_node_id", "$parent.id", False, "derived"),
            ("step_text", "$value", False, "always"),
            ("canonical_ordinal", "$node.ordinal", False, "derived"),
        ),
        "branch": (
            ("semantic_node_id", "$node.id", False, "derived"),
            ("proposal_id", "$projection.proposalId", False, "derived"),
            ("projection_id", "$projection.id", False, "derived"),
            ("requirement_node_id", "$parent.id", False, "derived"),
            ("kind", "kind", False, "always"),
            ("alternative_group_key", "alternativeGroupKey", True, "branch"),
            ("exclusive", "exclusive", True, "branch"),
            ("condition_root_node_id", "$child.EBR.id", True, "branch"),
        ),
    }
    for node_type, expected in expected_columns.items():
        assert tuple(
            (column["name"], column["source"], column["nullable"], column["presence"])
            for column in contracts[node_type]["columns"]
        ) == expected
    descriptors = {row["id"]: row for row in OCCURRENCES}
    assert {
        descriptor_id: (
            descriptors[descriptor_id]["parent"], descriptors[descriptor_id]["presence"],
            descriptors[descriptor_id]["ownerTable"], descriptors[descriptor_id]["key"],
            descriptors[descriptor_id]["ordinal"], descriptors[descriptor_id]["evidence"],
        )
        for descriptor_id in ("Q1", "Q2", "Q3", "Q5")
    } == {
        "Q1": ({"op": "root"}, "required", contracts["requirement"]["table"],
               {"op": "property", "name": "requirementKey"}, {"op": "array_ordinal"},
               {"source": "own", "purpose": "requirement_clause", "cardinality": "one_or_more", "inheritance": "none"}),
        "Q2": ({"op": "ancestor", "name": "Q1"}, "required", contracts["action"]["table"],
               {"op": "source_pointer"}, {"op": "constant", "value": 0},
               {"source": "own", "purpose": "action_clause", "cardinality": "one_or_more", "inheritance": "none"}),
        "Q3": ({"op": "ancestor", "name": "Q2"}, "optional", contracts["action_step"]["table"],
               {"op": "source_pointer"}, {"op": "array_ordinal"},
               {"source": "none", "purpose": None, "cardinality": "zero", "inheritance": "none"}),
        "Q5": ({"op": "ancestor", "name": "Q1"}, "required", contracts["branch"]["table"],
               {"op": "source_pointer"}, {"op": "constant", "value": 2},
               {"source": "own", "purpose": "branch_clause", "cardinality": "one_or_more", "inheritance": "none"}),
    }
    q4 = next(row for row in RELATIONSHIPS if row["id"] == "Q4")
    assert q4 == {
        "id": "Q4",
        "sourcePattern": "/requirements/{i}/action/approvedDataDocumentRefKeys/{j}",
        "table": "ad_v4_candidate_obligation_action_document_refs",
        "tableLabel": "action-document-ref",
        "idPrefix": "aor",
        "identityProperties": ("projectionId", "actionNodeId", "documentNodeId", "ordinal"),
        "ordering": "canonical_ordinal",
        "cardinality": "zero_or_more",
    }


def _known_timing(key: str) -> dict:
    return {
        "logic": "all",
        "terms": [{
            "metric": "calendar", "interval": "10", "unit": "days",
            "comparator": "within", "anchor": "effective_date",
            "evidenceKeys": [f"{key}-term"],
        }],
        "evidenceKeys": [key],
    }


def _expression_app_targets(proposal_id="proposal-1", projection_id="app-projection-1"):
    return [
        make_applicability_target(
            proposal_id=proposal_id, projection_id=projection_id,
            node_type="product_scope", node_key="scope-main",
            source_pointer="/productScopes/0", canonical_value={"scopeKey": "scope-main"},
        ),
        make_applicability_target(
            proposal_id=proposal_id, projection_id=projection_id,
            node_type="condition", node_key="condition-a",
            source_pointer="/conditionDefinitions/0", canonical_value={"conditionKey": "condition-a"},
        ),
        make_applicability_target(
            proposal_id=proposal_id, projection_id=projection_id,
            node_type="applicability_rule", node_key="rule-a",
            source_pointer="/applicabilityRules/0", canonical_value={"ruleKey": "rule-a"},
        ),
    ]


def _expression_requirements():
    first = _requirement(
        "req-a", 1,
        branch={
            "kind": "conditional",
            "conditionExpression": {"nodeType": "predicate_ref", "conditionKey": "condition-a"},
            "evidenceKeys": ["req-a-branch"],
        },
    )
    first["activationExpression"] = {
        "nodeType": "all",
        "operands": [
            {"nodeType": "scope_ref", "scopeKey": "scope-main"},
            {"nodeType": "not", "operand": {
                "nodeType": "predicate_ref", "conditionKey": "condition-a",
            }},
            {"nodeType": "any", "operands": [
                {"nodeType": "rule_ref", "ruleKey": "rule-a"},
                {
                    "nodeType": "requirement_state_ref", "requirementKey": "req-b",
                    "requirementState": "not_satisfied",
                },
            ]},
            {"nodeType": "scope_ref", "scopeKey": "scope-main"},
        ],
    }
    first["recurrence"] = {
        "kind": "conditioned",
        "conditionExpression": {"nodeType": "rule_ref", "ruleKey": "rule-a"},
        "timing": _known_timing("req-a-recurrence-timing"),
        "evidenceKeys": ["req-a-recurrence"],
    }
    second = _requirement("req-b", 2)
    return [second, first]


def _expression_context(requirements=None):
    requirements = requirements or _expression_requirements()
    canonical_documents, document_bindings, document_family = _requirement_document_context()
    bindings = _all_evidence_bindings(requirements)
    requirement_family = materialize_requirement_family(
        proposal_id="proposal-1", projection_id="projection-1",
        canonical_requirements=requirements, evidence_bindings=bindings,
        document_family=document_family, canonical_documents=canonical_documents,
        document_evidence_bindings=document_bindings,
    )
    return (
        requirements, bindings, canonical_documents, document_bindings,
        document_family, requirement_family,
    )


def test_expression_family_covers_all_seven_branches_and_three_contexts_exactly():
    requirements, bindings, documents, document_bindings, document_family, q_family = _expression_context()
    family = materialize_expression_family(
        proposal_id="proposal-1", projection_id="projection-1",
        app_projection_id="app-projection-1",
        canonical_requirements=requirements, evidence_bindings=bindings,
        document_family=document_family, canonical_documents=documents,
        document_evidence_bindings=document_bindings,
        requirement_family=q_family, app_targets=_expression_app_targets(),
    )
    assert {owner.node_type for owner in family.expressions} == {
        "scope_ref", "predicate_ref", "rule_ref", "requirement_state_ref",
        "not", "all", "any",
    }
    assert {owner.context for owner in family.expressions} == {
        "activation", "branch_condition", "recurrence_condition",
    }
    assert not hasattr(family, "evidence_links")
    nodes = {node.id: node for node in family.semantic_nodes}
    q_by_key = {row.requirement_key: row for row in q_family.requirements}
    activation = next(
        owner for owner in family.expressions
        if owner.context == "activation" and owner.expression_path == "/"
        and owner.requirement_node_id == q_by_key["req-a"].semantic_node_id
    )
    assert activation.semantic_node_id == q_by_key["req-a"].activation_root_node_id
    assert nodes[activation.semantic_node_id].canonical_ordinal == 1
    branch_root = next(
        owner for owner in family.expressions
        if owner.context == "branch_condition" and owner.expression_path == "/"
    )
    assert nodes[branch_root.semantic_node_id].canonical_ordinal == 0
    recurrence_root = next(
        owner for owner in family.expressions
        if owner.context == "recurrence_condition" and owner.expression_path == "/"
    )
    assert nodes[recurrence_root.semantic_node_id].parent_node_id == q_by_key["req-a"].recurrence_node_id
    state_ref = next(owner for owner in family.expressions if owner.node_type == "requirement_state_ref")
    assert state_ref.required_state == "not_satisfied"
    assert state_ref.requirement_target_node_id == q_by_key["req-b"].semantic_node_id
    assert all(
        owner.app_target_projection_id == "app-projection-1"
        for owner in family.expressions
        if owner.node_type in {"scope_ref", "predicate_ref", "rule_ref"}
    )
    assert all(nodes[edge.child_expression_id].parent_node_id == edge.parent_expression_id for edge in family.edges)
    assert len({node.id for node in family.semantic_nodes}) == len(family.semantic_nodes)
    repeated_scopes = [
        owner for owner in family.expressions
        if owner.context == "activation"
        and owner.node_type == "scope_ref"
        and owner.requirement_node_id == q_by_key["req-a"].semantic_node_id
    ]
    assert len(repeated_scopes) == 2
    assert repeated_scopes[0].semantic_node_id != repeated_scopes[1].semantic_node_id


@pytest.mark.parametrize(
    "mutate",
    [
        lambda family: replace(family, semantic_nodes=family.semantic_nodes[:-1]),
        lambda family: _replace_family_row(family, "semantic_nodes", 0, parent_node_id="aon-wrong"),
        lambda family: _replace_family_row(family, "expressions", 0, expression_path="/wrong"),
        lambda family: _replace_family_row(family, "expressions", 0, app_target_node_id="avn-wrong"),
        lambda family: replace(family, edges=family.edges[:-1]),
        lambda family: _replace_family_row(family, "edges", 0, canonical_ordinal=7),
        lambda family: _replace_family_row(family, "edges", 0, child_expression_id="aon-wrong"),
        lambda family: replace(family, app_projection_id="app-other"),
    ],
)
def test_expression_verified_read_fails_closed_on_graph_drift(mutate):
    requirements, bindings, documents, document_bindings, document_family, q_family = _expression_context()
    targets = _expression_app_targets()
    family = materialize_expression_family(
        proposal_id="proposal-1", projection_id="projection-1",
        app_projection_id="app-projection-1",
        canonical_requirements=requirements, evidence_bindings=bindings,
        document_family=document_family, canonical_documents=documents,
        document_evidence_bindings=document_bindings,
        requirement_family=q_family, app_targets=targets,
    )
    with pytest.raises(ObligationIntegrityError, match="expression typed projection differs"):
        verify_expression_family(
            proposal_id="proposal-1", projection_id="projection-1",
            app_projection_id="app-projection-1",
            canonical_requirements=requirements, evidence_bindings=bindings,
            document_family=document_family, canonical_documents=documents,
            document_evidence_bindings=document_bindings,
            requirement_family=q_family, app_targets=targets, family=mutate(family),
        )


def test_expression_family_rejects_missing_corrupt_self_and_cyclic_targets():
    requirements, bindings, documents, document_bindings, document_family, q_family = _expression_context()
    targets = _expression_app_targets()
    with pytest.raises(ObligationIntegrityError, match="Slice-3A target is unresolved"):
        materialize_expression_family(
            proposal_id="proposal-1", projection_id="projection-1",
            app_projection_id="app-projection-1", canonical_requirements=requirements,
            evidence_bindings=bindings, document_family=document_family,
            canonical_documents=documents, document_evidence_bindings=document_bindings,
            requirement_family=q_family, app_targets=targets[:2],
        )
    corrupt_targets = [replace(targets[0], identity_hash="0" * 64), *targets[1:]]
    with pytest.raises(ObligationIntegrityError, match="target differs"):
        materialize_expression_family(
            proposal_id="proposal-1", projection_id="projection-1",
            app_projection_id="app-projection-1", canonical_requirements=requirements,
            evidence_bindings=bindings, document_family=document_family,
            canonical_documents=documents, document_evidence_bindings=document_bindings,
            requirement_family=q_family, app_targets=corrupt_targets,
        )
    corrupt_hash_targets = [
        replace(targets[0], canonical_node_hash="f" * 64), *targets[1:],
    ]
    with pytest.raises(ObligationIntegrityError, match="target differs"):
        materialize_expression_family(
            proposal_id="proposal-1", projection_id="projection-1",
            app_projection_id="app-projection-1", canonical_requirements=requirements,
            evidence_bindings=bindings, document_family=document_family,
            canonical_documents=documents, document_evidence_bindings=document_bindings,
            requirement_family=q_family, app_targets=corrupt_hash_targets,
        )
    malformed_targets = [
        replace(
            targets[0],
            canonical_node_bytes=b'{"scopeKey":"scope-main","ordinal":1}',
        ),
        *targets[1:],
    ]
    with pytest.raises(ObligationIntegrityError, match="canonical bytes differ"):
        materialize_expression_family(
            proposal_id="proposal-1", projection_id="projection-1",
            app_projection_id="app-projection-1", canonical_requirements=requirements,
            evidence_bindings=bindings, document_family=document_family,
            canonical_documents=documents, document_evidence_bindings=document_bindings,
            requirement_family=q_family, app_targets=malformed_targets,
        )
    with pytest.raises(ObligationIntegrityError, match="duplicate Slice-3A"):
        materialize_expression_family(
            proposal_id="proposal-1", projection_id="projection-1",
            app_projection_id="app-projection-1", canonical_requirements=requirements,
            evidence_bindings=bindings, document_family=document_family,
            canonical_documents=documents, document_evidence_bindings=document_bindings,
            requirement_family=q_family, app_targets=[*targets, targets[0]],
        )

    self_requirements = [_requirement("req-self", 1)]
    self_requirements[0]["activationExpression"] = {
        "nodeType": "requirement_state_ref", "requirementKey": "req-self",
        "requirementState": "satisfied",
    }
    self_context = _expression_context(self_requirements)
    with pytest.raises(ObligationIntegrityError, match="self-reference"):
        materialize_expression_family(
            proposal_id="proposal-1", projection_id="projection-1",
            app_projection_id="app-projection-1",
            canonical_requirements=self_context[0], evidence_bindings=self_context[1],
            canonical_documents=self_context[2], document_evidence_bindings=self_context[3],
            document_family=self_context[4], requirement_family=self_context[5],
            app_targets=targets,
        )

    cyclic = [_requirement("req-a", 1), _requirement("req-b", 2)]
    cyclic[0]["activationExpression"] = {
        "nodeType": "requirement_state_ref", "requirementKey": "req-b",
        "requirementState": "unknown",
    }
    cyclic[1]["activationExpression"] = {
        "nodeType": "requirement_state_ref", "requirementKey": "req-a",
        "requirementState": "unknown",
    }
    cyclic_context = _expression_context(cyclic)
    with pytest.raises(ObligationIntegrityError, match="cycle"):
        materialize_expression_family(
            proposal_id="proposal-1", projection_id="projection-1",
            app_projection_id="app-projection-1",
            canonical_requirements=cyclic_context[0], evidence_bindings=cyclic_context[1],
            canonical_documents=cyclic_context[2], document_evidence_bindings=cyclic_context[3],
            document_family=cyclic_context[4], requirement_family=cyclic_context[5],
            app_targets=targets,
        )


@pytest.mark.parametrize("cross_edge", ["prerequisite", "termination"])
def test_expression_family_rejects_mixed_requirement_graph_cycles(cross_edge):
    requirements = [_requirement("req-a", 1), _requirement("req-b", 2)]
    requirements[0]["activationExpression"] = {
        "nodeType": "requirement_state_ref", "requirementKey": "req-b",
        "requirementState": "unknown",
    }
    if cross_edge == "prerequisite":
        requirements[1]["prerequisiteRequirementKeys"] = ["req-a"]
    else:
        requirements[1]["terminatingEffect"] = {
            "kind": "terminates", "requirementKeys": ["req-a"],
            "evidenceKeys": ["req-b-termination"],
        }
    context = _expression_context(requirements)
    with pytest.raises(ObligationIntegrityError, match="combined requirement graph cycle"):
        materialize_expression_family(
            proposal_id="proposal-1", projection_id="projection-1",
            app_projection_id="app-projection-1",
            canonical_requirements=context[0], evidence_bindings=context[1],
            canonical_documents=context[2], document_evidence_bindings=context[3],
            document_family=context[4], requirement_family=context[5],
            app_targets=_expression_app_targets(),
        )


def test_expression_family_accepts_acyclic_mixed_requirement_graph():
    requirements = [
        _requirement("req-a", 1), _requirement("req-b", 2),
        _requirement("req-c", 3),
    ]
    requirements[0]["activationExpression"] = {
        "nodeType": "requirement_state_ref", "requirementKey": "req-b",
        "requirementState": "satisfied",
    }
    requirements[1]["prerequisiteRequirementKeys"] = ["req-c"]
    requirements[0]["terminatingEffect"] = {
        "kind": "terminates", "requirementKeys": ["req-c"],
        "evidenceKeys": ["req-a-termination"],
    }
    context = _expression_context(requirements)
    family = materialize_expression_family(
        proposal_id="proposal-1", projection_id="projection-1",
        app_projection_id="app-projection-1",
        canonical_requirements=context[0], evidence_bindings=context[1],
        canonical_documents=context[2], document_evidence_bindings=context[3],
        document_family=context[4], requirement_family=context[5],
        app_targets=_expression_app_targets(),
    )
    assert len(family.expressions) == 3


def test_combined_requirement_graph_counts_source_edge_occurrences_at_exact_limit():
    requirement_count = 2_000
    keys = [f"req-{ordinal:04d}" for ordinal in range(requirement_count)]
    requirements = []
    for ordinal, key in enumerate(keys):
        targets = keys[max(0, ordinal - 20):ordinal]
        if 21 <= ordinal < 231:
            targets.append(keys[ordinal - 21])
        requirements.append({
            "requirementKey": key,
            "prerequisiteRequirementKeys": targets,
            "terminatingEffect": {"kind": "none"},
        })
    dependencies = {key: set() for key in keys}
    _verify_combined_requirement_graph(
        requirements=requirements,
        expression_dependencies=dependencies,
        expression_reference_count=0,
    )

    requirements[-1]["terminatingEffect"] = {
        "kind": "terminates",
        "requirementKeys": [requirements[-1]["prerequisiteRequirementKeys"][0]],
    }
    with pytest.raises(ObligationIntegrityError, match="edge limit exceeded"):
        _verify_combined_requirement_graph(
            requirements=requirements,
            expression_dependencies=dependencies,
            expression_reference_count=0,
        )


def test_expression_family_handles_long_requirement_chains_without_python_recursion():
    requirement_count = 1_100
    requirements = [
        _requirement(f"req-{ordinal:04d}", ordinal + 1)
        for ordinal in range(requirement_count)
    ]
    for ordinal in range(requirement_count - 1):
        requirements[ordinal]["activationExpression"] = {
            "nodeType": "requirement_state_ref",
            "requirementKey": requirements[ordinal + 1]["requirementKey"],
            "requirementState": "unknown",
        }
    context = _expression_context(requirements)
    family = materialize_expression_family(
        proposal_id="proposal-1", projection_id="projection-1",
        app_projection_id="app-projection-1",
        canonical_requirements=context[0], evidence_bindings=context[1],
        canonical_documents=context[2], document_evidence_bindings=context[3],
        document_family=context[4], requirement_family=context[5],
        app_targets=_expression_app_targets(),
    )
    assert len(family.expressions) == requirement_count

    requirements[-1]["activationExpression"] = {
        "nodeType": "requirement_state_ref",
        "requirementKey": requirements[0]["requirementKey"],
        "requirementState": "unknown",
    }
    cyclic_context = _expression_context(requirements)
    with pytest.raises(ObligationIntegrityError, match="combined requirement graph cycle"):
        materialize_expression_family(
            proposal_id="proposal-1", projection_id="projection-1",
            app_projection_id="app-projection-1",
            canonical_requirements=cyclic_context[0],
            evidence_bindings=cyclic_context[1],
            canonical_documents=cyclic_context[2],
            document_evidence_bindings=cyclic_context[3],
            document_family=cyclic_context[4], requirement_family=cyclic_context[5],
            app_targets=_expression_app_targets(),
        )


def test_expression_family_preserves_long_pointer_and_repeated_subtree_occurrences():
    expression = {"nodeType": "scope_ref", "scopeKey": "scope-main"}
    for _ in range(40):
        expression = {"nodeType": "not", "operand": expression}
    requirements = [_requirement("req-long", 1)]
    requirements[0]["activationExpression"] = expression
    context = _expression_context(requirements)
    family = materialize_expression_family(
        proposal_id="proposal-1", projection_id="projection-1",
        app_projection_id="app-projection-1",
        canonical_requirements=context[0], evidence_bindings=context[1],
        canonical_documents=context[2], document_evidence_bindings=context[3],
        document_family=context[4], requirement_family=context[5],
        app_targets=_expression_app_targets(),
    )
    assert max(len(node.node_key) for node in family.semantic_nodes) > 255
    assert len(family.semantic_nodes) == 41 and len(family.edges) == 40


def test_expression_edges_use_exact_generated_identity_preimage():
    context = _expression_context()
    family = materialize_expression_family(
        proposal_id="proposal-1", projection_id="projection-1",
        app_projection_id="app-projection-1",
        canonical_requirements=context[0], evidence_bindings=context[1],
        canonical_documents=context[2], document_evidence_bindings=context[3],
        document_family=context[4], requirement_family=context[5],
        app_targets=_expression_app_targets(),
    )
    edge = family.edges[0]
    identity = {
        "projectionId": edge.projection_id,
        "requirementNodeId": edge.requirement_node_id,
        "context": edge.context,
        "parentExpressionId": edge.parent_expression_id,
        "childExpressionId": edge.child_expression_id,
        "ordinal": edge.canonical_ordinal,
    }
    expected_hash = hashlib.sha256(
        DOMAINS["row"] + obligation_record_bytes({
            "table": "expression-edge", "identity": identity,
        })
    ).hexdigest()
    assert edge.id == f"aog_{expected_hash[:32]}"
    assert edge.identity_hash == expected_hash


def test_expression_verified_read_rejects_fully_restamped_foreign_graph():
    requirements, bindings, documents, document_bindings, document_family, q_family = _expression_context()
    foreign_documents = materialize_document_family(
        proposal_id="proposal-other", projection_id="projection-other",
        canonical_documents=documents, evidence_bindings=document_bindings,
    )
    foreign_q = materialize_requirement_family(
        proposal_id="proposal-other", projection_id="projection-other",
        canonical_requirements=requirements, evidence_bindings=bindings,
        document_family=foreign_documents, canonical_documents=documents,
        document_evidence_bindings=document_bindings,
    )
    foreign_targets = _expression_app_targets(
        proposal_id="proposal-other", projection_id="app-projection-other",
    )
    foreign = materialize_expression_family(
        proposal_id="proposal-other", projection_id="projection-other",
        app_projection_id="app-projection-other",
        canonical_requirements=requirements, evidence_bindings=bindings,
        document_family=foreign_documents, canonical_documents=documents,
        document_evidence_bindings=document_bindings,
        requirement_family=foreign_q, app_targets=foreign_targets,
    )
    with pytest.raises(ObligationIntegrityError, match="expression typed projection differs"):
        verify_expression_family(
            proposal_id="proposal-1", projection_id="projection-1",
            app_projection_id="app-projection-1",
            canonical_requirements=requirements, evidence_bindings=bindings,
            document_family=document_family, canonical_documents=documents,
            document_evidence_bindings=document_bindings,
            requirement_family=q_family, app_targets=_expression_app_targets(),
            family=foreign,
        )


def test_expression_physical_columns_match_generated_contract():
    from app.services.ad_v4_obligations import ObligationExpressionOwner

    contract = next(row for row in OWNER_CONTRACTS if row["nodeType"] == "expression")
    assert {field.name for field in fields(ObligationExpressionOwner)} == {
        column["name"] for column in contract["columns"]
    }
    assert {branch["value"] for branch in contract["union"]["branches"]} == {
        "scope_ref", "predicate_ref", "rule_ref", "requirement_state_ref",
        "not", "all", "any",
    }


def _timing_recurrence_context(requirements):
    context = _expression_context(requirements)
    expression_family = materialize_expression_family(
        proposal_id="proposal-1", projection_id="projection-1",
        app_projection_id="app-projection-1",
        canonical_requirements=context[0], evidence_bindings=context[1],
        canonical_documents=context[2], document_evidence_bindings=context[3],
        document_family=context[4], requirement_family=context[5],
        app_targets=_expression_app_targets(),
    )
    return (*context, expression_family)


def _materialize_timing_context(context):
    return materialize_timing_recurrence_family(
        proposal_id="proposal-1", projection_id="projection-1",
        app_projection_id="app-projection-1",
        canonical_requirements=context[0], evidence_bindings=context[1],
        canonical_documents=context[2], document_evidence_bindings=context[3],
        document_family=context[4], requirement_family=context[5],
        app_targets=_expression_app_targets(), expression_family=context[6],
    )


def test_timing_recurrence_family_covers_all_unions_terms_and_fixed_slots():
    requirements = [
        _requirement("req-known", 1), _requirement("req-unknown", 2),
        _requirement("req-na", 3), _requirement("req-conditioned", 4),
    ]
    requirements[0]["initialTiming"] = _known_timing("known-initial")
    requirements[0]["initialTiming"]["terms"][0]["interval"] = "0"
    requirements[1]["recurrence"] = {
        "kind": "interval", "timing": _known_timing("interval-recurrence"),
        "evidenceKeys": ["interval-recurrence-owner"],
    }
    requirements[2]["initialTiming"] = {
        "state": "not_applicable", "reason": "no timing applies",
        "temporalScope": {"kind": "directive_version"},
        "evidenceKeys": ["na-initial"],
    }
    requirements[2]["recurrence"] = {
        "kind": "unknown", "reason": "not_observed",
        "temporalScope": {"kind": "directive_version"},
        "evidenceKeys": ["unknown-recurrence"],
    }
    requirements[3]["initialTiming"] = _known_timing("conditioned-initial")
    requirements[3]["recurrence"] = {
        "kind": "conditioned",
        "conditionExpression": {"nodeType": "rule_ref", "ruleKey": "rule-a"},
        "timing": _known_timing("conditioned-recurrence"),
        "evidenceKeys": ["conditioned-recurrence-owner"],
    }
    context = _timing_recurrence_context(requirements)
    family = _materialize_timing_context(context)
    assert {row.state for row in family.timing_groups} == {
        "known", "unknown", "not_applicable",
    }
    assert {row.kind for row in family.recurrences} == {
        "none", "interval", "conditioned", "unknown",
    }
    assert len(family.timing_groups) == 6
    assert len(family.timing_terms) == 4
    zero = next(row for row in family.timing_terms if row.interval_text == "0")
    assert str(zero.interval_numeric) == "0"
    q_by_key = {row.requirement_key: row for row in context[5].requirements}
    nodes = {row.id: row for row in family.semantic_nodes}
    initial = next(
        row for row in family.timing_groups
        if row.owner_node_id == q_by_key["req-known"].semantic_node_id
    )
    assert nodes[initial.semantic_node_id].canonical_ordinal == 3
    conditioned = next(row for row in family.recurrences if row.kind == "conditioned")
    assert conditioned.condition_root_node_id is not None
    assert nodes[conditioned.timing_node_id].canonical_ordinal == 1


@pytest.mark.parametrize(
    "mutate",
    [
        lambda family: replace(family, semantic_nodes=family.semantic_nodes[:-1]),
        lambda family: _replace_family_row(family, "semantic_nodes", 0, canonical_ordinal=3.0),
        lambda family: _replace_family_row(family, "evidence_links", 0, canonical_ordinal=False),
        lambda family: _replace_family_row(family, "timing_groups", 0, state="unknown"),
        lambda family: _replace_family_row(family, "timing_groups", 0, term_count=99),
        lambda family: _replace_family_row(family, "timing_groups", 0, term_count=True),
        lambda family: _replace_family_row(family, "timing_groups", 0, canonical_ordinal=3.0),
        lambda family: _replace_family_row(family, "timing_terms", 0, interval_text="11"),
        lambda family: _replace_family_row(family, "timing_terms", 0, canonical_ordinal=0.0),
        lambda family: _replace_family_row(family, "timing_terms", 0, interval_numeric=Decimal("11")),
        lambda family: _replace_family_row(family, "timing_terms", 0, interval_numeric=10),
        lambda family: _replace_family_row(family, "timing_terms", 0, interval_numeric=10.0),
        lambda family: _replace_family_row(family, "timing_terms", 0, interval_numeric=True),
        lambda family: _replace_family_row(family, "timing_terms", 0, interval_numeric=Decimal("10.0")),
        lambda family: _replace_family_row(family, "recurrences", 0, kind="unknown"),
        lambda family: replace(family, projection_id="projection-other"),
    ],
)
def test_timing_recurrence_verified_read_fails_closed_on_drift(mutate):
    requirements = [_requirement("req-one", 1)]
    requirements[0]["initialTiming"] = _known_timing("initial")
    requirements[0]["recurrence"] = {
        "kind": "conditioned",
        "conditionExpression": {"nodeType": "rule_ref", "ruleKey": "rule-a"},
        "timing": _known_timing("recurring"),
        "evidenceKeys": ["recurrence"],
    }
    context = _timing_recurrence_context(requirements)
    family = _materialize_timing_context(context)
    with pytest.raises(
        ObligationIntegrityError,
        match="timing/recurrence typed projection differs|timing interval numeric|timing ordinal/count numeric",
    ):
        verify_timing_recurrence_family(
            proposal_id="proposal-1", projection_id="projection-1",
            app_projection_id="app-projection-1",
            canonical_requirements=context[0], evidence_bindings=context[1],
            canonical_documents=context[2], document_evidence_bindings=context[3],
            document_family=context[4], requirement_family=context[5],
            app_targets=_expression_app_targets(), expression_family=context[6],
            family=mutate(family),
        )


def test_timing_recurrence_physical_columns_match_generated_contracts():
    from app.services.ad_v4_obligations import (
        ObligationRecurrenceOwner, ObligationTimingGroupOwner,
        ObligationTimingTermOwner,
    )

    classes = {
        "timing_group": ObligationTimingGroupOwner,
        "timing_term": ObligationTimingTermOwner,
        "recurrence": ObligationRecurrenceOwner,
    }
    for node_type, cls in classes.items():
        contract = next(row for row in OWNER_CONTRACTS if row["nodeType"] == node_type)
        assert {field.name for field in fields(cls)} == {
            column["name"] for column in contract["columns"]
        }


def test_timing_term_enum_cartesian_matrix_and_independent_evidence_are_exact():
    metrics = ["calendar", "aircraft_time", "component_time", "cycles", "other_reviewed"]
    units = ["days", "months", "years", "hours", "cycles", "source_defined"]
    comparators = ["within", "before", "at_or_before", "after", "at_or_after"]
    anchors = ["effective_date", "last_compliance", "installation", "manufacture", "source_defined"]
    terms = []
    for metric in metrics:
        for unit in units:
            for comparator in comparators:
                for anchor in anchors:
                    terms.append({
                        "metric": metric, "interval": str(len(terms) + 1),
                        "unit": unit, "comparator": comparator, "anchor": anchor,
                        "evidenceKeys": ["shared-term-evidence"],
                    })
    requirements = [_requirement("req-matrix", 1)]
    requirements[0]["initialTiming"] = {
        "logic": "whichever_later", "terms": terms,
        "evidenceKeys": ["timing-owner-evidence"],
    }
    context = _timing_recurrence_context(requirements)
    family = _materialize_timing_context(context)
    assert len(family.timing_terms) == len(terms) == 750
    assert {
        (row.metric, row.unit, row.comparator, row.anchor)
        for row in family.timing_terms
    } == {
        (metric, unit, comparator, anchor)
        for metric in metrics for unit in units
        for comparator in comparators for anchor in anchors
    }
    timing = family.timing_groups[0]
    timing_links = [row for row in family.evidence_links if row.semantic_node_id == timing.semantic_node_id]
    term_links = [row for row in family.evidence_links if row.semantic_node_id == family.timing_terms[0].semantic_node_id]
    assert [(row.evidence_key, row.purpose) for row in timing_links] == [
        ("timing-owner-evidence", "timing_clause"),
    ]
    assert [(row.evidence_key, row.purpose) for row in term_links] == [
        ("shared-term-evidence", "timing_term_clause"),
    ]


def test_timing_decimal_text_boundary_is_prechecked_and_lossless():
    requirements = [_requirement("req-decimal", 1)]
    requirements[0]["initialTiming"] = _known_timing("decimal")
    requirements[0]["initialTiming"]["terms"][0]["interval"] = "1" * 16_384
    context = _timing_recurrence_context(requirements)
    family = _materialize_timing_context(context)
    assert family.timing_terms[0].interval_text == "1" * 16_384
    assert str(family.timing_terms[0].interval_numeric) == "1" * 16_384

    requirements[0]["initialTiming"]["terms"][0]["interval"] += "1"
    with pytest.raises(ObligationIntegrityError, match="string limit exceeded"):
        _timing_recurrence_context(requirements)

    requirements[0]["initialTiming"]["terms"][0]["interval"] = "01"
    malformed_context = _timing_recurrence_context(requirements)
    with pytest.raises(ObligationIntegrityError, match="interval text differs"):
        _materialize_timing_context(malformed_context)


def test_not_applicable_timing_reason_uses_exact_identifier_length_bound():
    requirements = [_requirement("req-na-bound", 1)]
    requirements[0]["initialTiming"] = {
        "state": "not_applicable", "reason": "r" * 512,
        "temporalScope": {"kind": "directive_version"},
        "evidenceKeys": ["na-bound"],
    }
    family = _materialize_timing_context(_timing_recurrence_context(requirements))
    assert family.timing_groups[0].reason == "r" * 512

    requirements[0]["initialTiming"]["reason"] += "r"
    context = _timing_recurrence_context(requirements)
    with pytest.raises(ObligationIntegrityError, match="non-known timing value differs"):
        _materialize_timing_context(context)


def _relationship_context(requirements):
    return _timing_recurrence_context(requirements)


def _materialize_relationship_context(context):
    return materialize_requirement_relationship_family(
        proposal_id="proposal-1", projection_id="projection-1",
        app_projection_id="app-projection-1",
        canonical_requirements=context[0], evidence_bindings=context[1],
        canonical_documents=context[2], document_evidence_bindings=context[3],
        document_family=context[4], requirement_family=context[5],
        app_targets=_expression_app_targets(), expression_family=context[6],
    )


def _verify_relationship_context(context, family):
    verify_requirement_relationship_family(
        proposal_id="proposal-1", projection_id="projection-1",
        app_projection_id="app-projection-1",
        canonical_requirements=context[0], evidence_bindings=context[1],
        canonical_documents=context[2], document_evidence_bindings=context[3],
        document_family=context[4], requirement_family=context[5],
        app_targets=_expression_app_targets(), expression_family=context[6],
        family=family,
    )


def _restamp_relationship_family(family):
    collections = (
        "semantic_nodes", "evidence_links", "terminating_effects",
        "termination_edges", "requirement_dependencies",
    )
    changes = {
        collection: tuple(
            replace(row, proposal_id="proposal-other", projection_id="projection-other")
            for row in getattr(family, collection)
        )
        for collection in collections
    }
    return replace(
        family, proposal_id="proposal-other", projection_id="projection-other",
        **changes,
    )


def test_requirement_relationship_family_preserves_unions_order_and_exact_hashes():
    requirements = [
        _requirement("req-a", 1), _requirement("req-b", 2),
        _requirement("req-c", 3),
    ]
    requirements[0]["prerequisiteRequirementKeys"] = ["req-c", "req-b"]
    requirements[0]["terminatingEffect"] = {
        "kind": "terminates", "requirementKeys": ["req-c", "req-b"],
        "evidenceKeys": ["req-a-termination"],
    }
    requirements[2]["terminatingEffect"] = {
        "kind": "terminates", "requirementKeys": [],
        "evidenceKeys": ["req-c-termination"],
    }
    context = _relationship_context(requirements)
    family = _materialize_relationship_context(context)
    assert [row.kind for row in family.terminating_effects] == [
        "terminates", "none", "terminates",
    ]
    assert [row.edge_count for row in family.terminating_effects] == [2, 0, 0]
    assert [row.terminated_requirement_key for row in family.termination_edges] == [
        "req-b", "req-c",
    ]
    assert [row.prerequisite_requirement_key for row in family.requirement_dependencies] == [
        "req-b", "req-c",
    ]
    assert all(row.dependency_kind == "prerequisite" for row in family.requirement_dependencies)
    nodes = {row.id: row for row in family.semantic_nodes}
    assert all(nodes[row.semantic_node_id].canonical_ordinal == 5 for row in family.terminating_effects)
    edge = family.termination_edges[0]
    identity = {
        "projectionId": edge.projection_id, "effectNodeId": edge.effect_node_id,
        "terminatedRequirementNodeId": edge.terminated_requirement_node_id,
        "ordinal": edge.canonical_ordinal,
    }
    expected_hash = hashlib.sha256(
        DOMAINS["row"] + obligation_record_bytes({
            "table": "termination-edge", "identity": identity,
        })
    ).hexdigest()
    assert (edge.id, edge.identity_hash) == (f"aot_{expected_hash[:32]}", expected_hash)
    dependency = family.requirement_dependencies[0]
    dependency_identity = {
        "projectionId": dependency.projection_id,
        "requirementNodeId": dependency.requirement_node_id,
        "prerequisiteRequirementNodeId": dependency.prerequisite_requirement_node_id,
        "ordinal": dependency.canonical_ordinal,
    }
    dependency_hash = hashlib.sha256(
        DOMAINS["row"] + obligation_record_bytes({
            "table": "requirement-dependency", "identity": dependency_identity,
        })
    ).hexdigest()
    assert (dependency.id, dependency.identity_hash) == (
        f"aop_{dependency_hash[:32]}", dependency_hash,
    )

    effect = family.terminating_effects[0]
    effect_node = nodes[effect.semantic_node_id]
    assert (
        effect_node.node_type, effect_node.node_key, effect_node.source_pointer,
        effect_node.parent_node_id,
    ) == (
        "terminating_effect", "/requirements/0/terminatingEffect",
        "/requirements/0/terminatingEffect", effect.requirement_node_id,
    )
    effect_identity = {
        "projectionId": "projection-1", "nodeType": "terminating_effect",
        "nodeKey": "/requirements/0/terminatingEffect",
        "pointer": "/requirements/0/terminatingEffect",
    }
    effect_hash = hashlib.sha256(
        DOMAINS["row"] + obligation_record_bytes({
            "table": "semantic-node", "identity": effect_identity,
        })
    ).hexdigest()
    assert (effect_node.id, effect_node.identity_hash) == (
        f"aon_{effect_hash[:32]}", effect_hash,
    )

    effect_links = [
        row for row in family.evidence_links
        if row.semantic_node_id == effect.semantic_node_id
    ]
    assert [(row.evidence_key, row.purpose) for row in effect_links] == [
        ("req-a-termination", "termination_clause"),
    ]
    link = effect_links[0]
    link_identity = {
        "projectionId": "projection-1", "semanticNodeId": effect.semantic_node_id,
        "purpose": "termination_clause", "evidenceKey": "req-a-termination",
        "ordinal": 0,
    }
    link_hash = hashlib.sha256(
        DOMAINS["row"] + obligation_record_bytes({
            "table": "evidence-link", "identity": link_identity,
        })
    ).hexdigest()
    assert (link.id, link.link_hash) == (f"aoe_{link_hash[:32]}", link_hash)
    requirement_links = [
        row for row in context[5].evidence_links
        if row.semantic_node_id == effect.requirement_node_id
    ]
    assert [(row.evidence_key, row.purpose) for row in requirement_links] == [
        ("req-a-requirement", "requirement_clause"),
    ]


@pytest.mark.parametrize(
    "mutate, message",
    [
        (lambda values: values.__setitem__(0, "invalid"), "source is invalid"),
        (lambda values: values[0].__setitem__("requirementKey", "Req-A"), "key is invalid"),
        (lambda values: values[0].__setitem__("requirementKey", "aa"), "key is invalid"),
        (lambda values: values[0].__setitem__("requirementKey", "a" * 129), "key is invalid"),
        (lambda values: values[0].__setitem__("prerequisiteRequirementKeys", "req-b"), "prerequisite requirement set"),
        (lambda values: values[0].__setitem__("prerequisiteRequirementKeys", [["req-b"]]), "prerequisite requirement set"),
        (lambda values: values[0].__setitem__("prerequisiteRequirementKeys", ["req-b", "req-b"]), "prerequisite requirement set"),
        (lambda values: values[0].__setitem__("terminatingEffect", None), "terminating effect shape"),
        (lambda values: values[0]["terminatingEffect"].__setitem__("kind", []), "terminating effect shape"),
        (lambda values: values[0]["terminatingEffect"].__setitem__("kind", {}), "terminating effect shape"),
        (lambda values: values[0].__setitem__("terminatingEffect", {"kind": "none", "requirementKeys": [], "evidenceKeys": ["req-a-termination"]}), "terminating effect shape"),
        (lambda values: values[0].__setitem__("terminatingEffect", {"kind": "terminates", "evidenceKeys": ["req-a-termination"]}), "terminating effect shape"),
        (lambda values: values[0]["terminatingEffect"].__setitem__("evidenceKeys", []), "effect evidence set"),
        (lambda values: values[0].__setitem__("terminatingEffect", {"kind": "terminates", "requirementKeys": [["req-b"]], "evidenceKeys": ["req-a-termination"]}), "termination requirement set"),
        (lambda values: values.__setitem__(0, MappingProxyType(values[0])), "source is invalid"),
        (lambda values: values.__setitem__(0, UserDict(values[0])), "source is invalid"),
        (lambda values: values[0].__setitem__("terminatingEffect", MappingProxyType(values[0]["terminatingEffect"])), "terminating effect shape"),
        (lambda values: values[0].__setitem__("terminatingEffect", UserDict(values[0]["terminatingEffect"])), "terminating effect shape"),
    ],
)
def test_requirement_relationship_source_shapes_fail_closed_before_dependency_rebuild(
    mutate, message,
):
    requirements = [_requirement("req-a", 1), _requirement("req-b", 2)]
    context = _relationship_context(requirements)
    family = _materialize_relationship_context(context)
    malformed = deepcopy(context[0])
    mutate(malformed)
    malformed_context = (malformed, *context[1:])
    with pytest.raises(ObligationIntegrityError, match=message):
        _materialize_relationship_context(malformed_context)
    with pytest.raises(ObligationIntegrityError, match=message):
        _verify_relationship_context(malformed_context, family)


@pytest.mark.parametrize(
    "mutate",
    [
        lambda family: replace(family, semantic_nodes=family.semantic_nodes[:-1]),
        lambda family: _replace_family_row(family, "terminating_effects", 0, kind="none"),
        lambda family: _replace_family_row(family, "terminating_effects", 0, edge_count=2.0),
        lambda family: _replace_family_row(family, "termination_edges", 0, terminated_requirement_key="req-c"),
        lambda family: _replace_family_row(family, "termination_edges", 0, canonical_ordinal=False),
        lambda family: _replace_family_row(family, "termination_edges", 0, identity_hash="0" * 64),
        lambda family: replace(family, termination_edges=family.termination_edges[::-1]),
        lambda family: replace(family, termination_edges=family.termination_edges + family.termination_edges[:1]),
        lambda family: _replace_family_row(family, "requirement_dependencies", 0, dependency_kind="termination"),
        lambda family: _replace_family_row(family, "requirement_dependencies", 0, prerequisite_requirement_node_id="aon-cross"),
        lambda family: _replace_family_row(family, "requirement_dependencies", 0, prerequisite_requirement_key="req-a"),
        lambda family: _replace_family_row(family, "evidence_links", 0, purpose="requirement_clause"),
        lambda family: replace(family, projection_id="projection-other"),
        _restamp_relationship_family,
    ],
)
def test_requirement_relationship_verified_read_fails_closed_on_drift(mutate):
    requirements = [
        _requirement("req-a", 1), _requirement("req-b", 2),
        _requirement("req-c", 3),
    ]
    requirements[0]["prerequisiteRequirementKeys"] = ["req-b", "req-c"]
    requirements[0]["terminatingEffect"] = {
        "kind": "terminates", "requirementKeys": ["req-b", "req-c"],
        "evidenceKeys": ["req-a-termination"],
    }
    context = _relationship_context(requirements)
    family = _materialize_relationship_context(context)
    with pytest.raises(
        ObligationIntegrityError,
        match="requirement relationship typed projection differs|requirement relationship numeric type differs",
    ):
        _verify_relationship_context(context, mutate(family))


def test_requirement_relationship_physical_shapes_match_generated_contract():
    from app.services.ad_v4_obligations import (
        ObligationRequirementDependency,
        ObligationTerminatingEffectOwner,
        ObligationTerminationEdge,
    )

    contract = next(row for row in OWNER_CONTRACTS if row["nodeType"] == "terminating_effect")
    assert {field.name for field in fields(ObligationTerminatingEffectOwner)} == {
        column["name"] for column in contract["columns"]
    }
    relationships = {row["id"]: row for row in RELATIONSHIPS}
    assert relationships["Q9"]["identityProperties"] == (
        "projectionId", "effectNodeId", "terminatedRequirementNodeId", "ordinal",
    )
    assert relationships["Q10"]["identityProperties"] == (
        "projectionId", "requirementNodeId", "prerequisiteRequirementNodeId", "ordinal",
    )
    assert {field.name for field in fields(ObligationTerminationEdge)} == {
        "id", "identity_hash", "proposal_id", "projection_id", "effect_node_id",
        "terminated_requirement_node_id", "terminated_requirement_key",
        "canonical_ordinal",
    }
    assert {field.name for field in fields(ObligationRequirementDependency)} == {
        "id", "identity_hash", "proposal_id", "projection_id", "requirement_node_id",
        "prerequisite_requirement_node_id", "prerequisite_requirement_key",
        "dependency_kind", "canonical_ordinal",
    }


def _group_not_applicable(key: str) -> dict:
    return {
        "state": "not_applicable", "reason": "not required for this group",
        "temporalScope": {"kind": "directive_version"},
        "evidenceKeys": [key],
    }


def _recurrence_group(
    key: str, requirement_keys: list[str], initial_timing: dict,
    recurring_timing: dict,
) -> dict:
    return {
        "recurrenceGroupKey": key,
        "requirementKeys": requirement_keys,
        "completionPolicy": "all_active_requirements",
        "initialTiming": initial_timing,
        "recurringTiming": recurring_timing,
        "evidenceKeys": [f"{key}-evidence"],
    }


def _recurrence_group_context(requirements, groups):
    canonical_documents, document_bindings, document_family = _requirement_document_context()
    evidence_bindings = _all_evidence_bindings([requirements, groups])
    requirement_family = materialize_requirement_family(
        proposal_id="proposal-1", projection_id="projection-1",
        canonical_requirements=requirements, evidence_bindings=evidence_bindings,
        document_family=document_family, canonical_documents=canonical_documents,
        document_evidence_bindings=document_bindings,
    )
    expression_family = materialize_expression_family(
        proposal_id="proposal-1", projection_id="projection-1",
        app_projection_id="app-projection-1",
        canonical_requirements=requirements, evidence_bindings=evidence_bindings,
        document_family=document_family, canonical_documents=canonical_documents,
        document_evidence_bindings=document_bindings,
        requirement_family=requirement_family,
        app_targets=_expression_app_targets(),
    )
    timing_family = materialize_timing_recurrence_family(
        proposal_id="proposal-1", projection_id="projection-1",
        app_projection_id="app-projection-1",
        canonical_requirements=requirements, evidence_bindings=evidence_bindings,
        document_family=document_family, canonical_documents=canonical_documents,
        document_evidence_bindings=document_bindings,
        requirement_family=requirement_family,
        app_targets=_expression_app_targets(), expression_family=expression_family,
    )
    return (
        requirements, groups, evidence_bindings, canonical_documents,
        document_bindings, document_family, requirement_family,
        expression_family, timing_family,
    )


def _materialize_recurrence_group_context(context):
    return materialize_recurrence_group_family(
        proposal_id="proposal-1", projection_id="projection-1",
        app_projection_id="app-projection-1",
        canonical_requirements=context[0], canonical_recurrence_groups=context[1],
        evidence_bindings=context[2], canonical_documents=context[3],
        document_evidence_bindings=context[4], document_family=context[5],
        requirement_family=context[6], app_targets=_expression_app_targets(),
        expression_family=context[7], timing_recurrence_family=context[8],
    )


def _verify_recurrence_group_context(context, family):
    verify_recurrence_group_family(
        proposal_id="proposal-1", projection_id="projection-1",
        app_projection_id="app-projection-1",
        canonical_requirements=context[0], canonical_recurrence_groups=context[1],
        evidence_bindings=context[2], canonical_documents=context[3],
        document_evidence_bindings=context[4], document_family=context[5],
        requirement_family=context[6], app_targets=_expression_app_targets(),
        expression_family=context[7], timing_recurrence_family=context[8],
        family=family,
    )


def _restamp_recurrence_group_family(family):
    collections = (
        "semantic_nodes", "evidence_links", "recurrence_groups", "members",
        "timing_groups", "timing_terms",
    )
    changes = {
        collection: tuple(
            replace(row, proposal_id="proposal-other", projection_id="projection-other")
            for row in getattr(family, collection)
        )
        for collection in collections
    }
    return replace(
        family, proposal_id="proposal-other", projection_id="projection-other",
        **changes,
    )


def test_recurrence_group_family_covers_all_group_timing_union_pairs_and_order():
    timing_values = (
        lambda key: _known_timing(key),
        lambda key: _timing_unknown(key),
        lambda key: _group_not_applicable(key),
    )
    requirements = []
    groups = []
    sequence = 1
    for initial_index, initial in enumerate(timing_values):
        for recurring_index, recurring in enumerate(timing_values):
            group_key = f"group-{initial_index}{recurring_index}"
            member_keys = [f"req-{initial_index}{recurring_index}-b", f"req-{initial_index}{recurring_index}-a"]
            for member_key in member_keys:
                requirement = _requirement(member_key, sequence)
                requirement["recurrenceGroupKey"] = group_key
                requirements.append(requirement)
                sequence += 1
            groups.append(_recurrence_group(
                group_key, member_keys,
                initial(f"{group_key}-initial"),
                recurring(f"{group_key}-recurring"),
            ))
    context = _recurrence_group_context(list(reversed(requirements)), list(reversed(groups)))
    family = _materialize_recurrence_group_context(context)

    assert [row.recurrence_group_key for row in family.recurrence_groups] == sorted(
        group["recurrenceGroupKey"] for group in groups
    )
    assert all(row.completion_policy == "all_active_requirements" for row in family.recurrence_groups)
    assert all(row.member_count == 2 for row in family.recurrence_groups)
    assert len(family.members) == 18
    assert len(family.timing_groups) == 18
    assert {row.state for row in family.timing_groups} == {
        "known", "unknown", "not_applicable",
    }
    assert {row.owner_kind for row in family.timing_groups} == {
        "recurrence_group_initial", "recurrence_group_recurring",
    }
    assert len(family.timing_terms) == 6
    assert all(
        row.requirement_key.endswith("-a")
        for row in family.members[::2]
    )
    nodes = {row.id: row for row in family.semantic_nodes}
    for group in family.recurrence_groups:
        assert nodes[group.semantic_node_id].parent_node_id is None
        assert nodes[group.initial_timing_node_id].parent_node_id == group.semantic_node_id
        assert nodes[group.initial_timing_node_id].canonical_ordinal == 0
        assert nodes[group.recurring_timing_node_id].parent_node_id == group.semantic_node_id
        assert nodes[group.recurring_timing_node_id].canonical_ordinal == 1
    first_group = family.recurrence_groups[0]
    group_links = [
        row for row in family.evidence_links
        if row.semantic_node_id == first_group.semantic_node_id
    ]
    initial_links = [
        row for row in family.evidence_links
        if row.semantic_node_id == first_group.initial_timing_node_id
    ]
    assert [(row.evidence_key, row.purpose) for row in group_links] == [
        (f"{first_group.recurrence_group_key}-evidence", "recurrence_clause"),
    ]
    assert [(row.evidence_key, row.purpose) for row in initial_links] == [
        (f"{first_group.recurrence_group_key}-initial", "timing_clause"),
    ]


def test_recurrence_group_family_supports_no_groups_and_ungrouped_requirements():
    context = _recurrence_group_context([_requirement("req-free", 1)], [])
    family = _materialize_recurrence_group_context(context)
    assert family.semantic_nodes == ()
    assert family.evidence_links == ()
    assert family.recurrence_groups == ()
    assert family.members == ()
    assert family.timing_groups == ()
    assert family.timing_terms == ()


def test_recurrence_group_member_uses_exact_generated_identity_preimage():
    requirements = [_requirement("req-b", 2), _requirement("req-a", 1)]
    for requirement in requirements:
        requirement["recurrenceGroupKey"] = "group-main"
    group = _recurrence_group(
        "group-main", ["req-b", "req-a"],
        _timing_unknown("group-initial"), _known_timing("group-recurring"),
    )
    family = _materialize_recurrence_group_context(
        _recurrence_group_context(requirements, [group]),
    )
    member = family.members[0]
    assert member.requirement_key == "req-a"
    identity = {
        "projectionId": member.projection_id,
        "groupNodeId": member.group_node_id,
        "requirementNodeId": member.requirement_node_id,
        "ordinal": member.canonical_ordinal,
    }
    expected_hash = hashlib.sha256(
        DOMAINS["row"] + obligation_record_bytes({
            "table": "recurrence-group-member", "identity": identity,
        })
    ).hexdigest()
    assert (member.id, member.identity_hash) == (
        f"aom_{expected_hash[:32]}", expected_hash,
    )
    owner = family.recurrence_groups[0]
    nodes = {row.id: row for row in family.semantic_nodes}
    expected_nodes = (
        (
            nodes[owner.semantic_node_id], "recurrence_group", "group-main",
            "/recurrenceGroups/0", group, None, 0,
        ),
        (
            nodes[owner.initial_timing_node_id], "timing_group",
            "/recurrenceGroups/0/initialTiming",
            "/recurrenceGroups/0/initialTiming", group["initialTiming"],
            owner.semantic_node_id, 0,
        ),
        (
            nodes[owner.recurring_timing_node_id], "timing_group",
            "/recurrenceGroups/0/recurringTiming",
            "/recurrenceGroups/0/recurringTiming", group["recurringTiming"],
            owner.semantic_node_id, 1,
        ),
    )
    for node, node_type, node_key, pointer, source_value, parent_id, ordinal in expected_nodes:
        node_identity = {
            "projectionId": "projection-1", "nodeType": node_type,
            "nodeKey": node_key, "pointer": pointer,
        }
        node_hash = hashlib.sha256(
            DOMAINS["row"] + obligation_record_bytes({
                "table": "semantic-node", "identity": node_identity,
            })
        ).hexdigest()
        assert (node.id, node.identity_hash) == (
            f"aon_{node_hash[:32]}", node_hash,
        )
        assert node.parent_node_id == parent_id
        assert node.canonical_ordinal == ordinal
        assert node.canonical_node_hash == hashlib.sha256(
            canonical_bytes(source_value, CANONICALIZATION_VERSION_V2)
        ).hexdigest()
    group_link = next(
        row for row in family.evidence_links
        if row.semantic_node_id == owner.semantic_node_id
    )
    evidence_identity = {
        "projectionId": "projection-1", "semanticNodeId": owner.semantic_node_id,
        "purpose": "recurrence_clause", "evidenceKey": "group-main-evidence",
        "ordinal": 0,
    }
    evidence_hash = hashlib.sha256(
        DOMAINS["row"] + obligation_record_bytes({
            "table": "evidence-link", "identity": evidence_identity,
        })
    ).hexdigest()
    assert (group_link.id, group_link.link_hash) == (
        f"aoe_{evidence_hash[:32]}", evidence_hash,
    )


@pytest.mark.parametrize(
    "mutate, message",
    [
        (lambda requirements, groups: groups.__setitem__(0, "invalid"), "group shape differs"),
        (lambda requirements, groups: groups[0].__setitem__("completionPolicy", "any"), "completion policy"),
        (lambda requirements, groups: groups[0].__setitem__("requirementKeys", ["req-a"]), "member set differs"),
        (lambda requirements, groups: groups[0].__setitem__("requirementKeys", ["req-a", "req-a"]), "member set differs"),
        (lambda requirements, groups: groups[0].__setitem__("requirementKeys", ["req-a", "req-missing"]), "member is unresolved"),
        (lambda requirements, groups: requirements[0].__setitem__("recurrenceGroupKey", "group-other"), "typed projection differs|membership differs"),
        (lambda requirements, groups: requirements[0].pop("recurrenceGroupKey"), "typed projection differs|membership differs"),
        (lambda requirements, groups: groups[0].__setitem__("initialTiming", MappingProxyType(groups[0]["initialTiming"])), "timing object differs"),
        (lambda requirements, groups: groups[0]["initialTiming"].__setitem__("state", []), "timing value differs"),
        (lambda requirements, groups: groups[0]["recurringTiming"].__setitem__("logic", []), "known timing shape differs"),
        (lambda requirements, groups: groups[0]["recurringTiming"]["terms"][0].__setitem__("metric", []), "timing term value differs"),
        (lambda requirements, groups: groups[0]["recurringTiming"]["terms"].__setitem__(0, MappingProxyType(groups[0]["recurringTiming"]["terms"][0])), "timing term value differs"),
        (lambda requirements, groups: groups[0].__setitem__("recurrenceGroupKey", "Group-Main"), "key set differs"),
        (lambda requirements, groups: requirements[0].__setitem__("recurrenceGroupKey", []), "requirement recurrence group key"),
    ],
)
def test_recurrence_group_source_and_membership_fail_closed(mutate, message):
    requirements = [_requirement("req-a", 1), _requirement("req-b", 2)]
    for requirement in requirements:
        requirement["recurrenceGroupKey"] = "group-main"
    groups = [_recurrence_group(
        "group-main", ["req-a", "req-b"],
        _timing_unknown("group-initial"), _known_timing("group-recurring"),
    )]
    context = _recurrence_group_context(requirements, groups)
    family = _materialize_recurrence_group_context(context)
    malformed_requirements = deepcopy(context[0])
    malformed_groups = deepcopy(context[1])
    mutate(malformed_requirements, malformed_groups)
    malformed_context = (
        malformed_requirements, malformed_groups, *context[2:],
    )
    with pytest.raises(ObligationIntegrityError, match=message):
        _materialize_recurrence_group_context(malformed_context)
    with pytest.raises(ObligationIntegrityError, match=message):
        _verify_recurrence_group_context(malformed_context, family)


@pytest.mark.parametrize("field", ["initialTiming", "recurringTiming"])
def test_grouped_requirements_forbid_inline_known_timing_or_recurrence(field):
    requirements = [_requirement("req-a", 1), _requirement("req-b", 2)]
    for requirement in requirements:
        requirement["recurrenceGroupKey"] = "group-main"
    if field == "initialTiming":
        requirements[0]["initialTiming"] = _known_timing("inline-known")
    else:
        requirements[0]["recurrence"] = {
            "kind": "interval", "timing": _known_timing("inline-repeat"),
            "evidenceKeys": ["inline-repeat-owner"],
        }
    groups = [_recurrence_group(
        "group-main", ["req-a", "req-b"],
        _timing_unknown("group-initial"), _known_timing("group-recurring"),
    )]
    context = _recurrence_group_context(requirements, groups)
    with pytest.raises(ObligationIntegrityError, match="grouped requirement timing differs"):
        _materialize_recurrence_group_context(context)


def test_recurrence_group_rejects_member_overlap_across_groups():
    requirements = [
        _requirement("req-a", 1), _requirement("req-b", 2),
        _requirement("req-c", 3), _requirement("req-d", 4),
    ]
    for requirement in requirements[:2]:
        requirement["recurrenceGroupKey"] = "group-one"
    for requirement in requirements[2:]:
        requirement["recurrenceGroupKey"] = "group-two"
    groups = [
        _recurrence_group(
            "group-one", ["req-a", "req-b"],
            _timing_unknown("one-initial"), _timing_unknown("one-recurring"),
        ),
        _recurrence_group(
            "group-two", ["req-a", "req-c"],
            _timing_unknown("two-initial"), _timing_unknown("two-recurring"),
        ),
    ]
    context = _recurrence_group_context(requirements, groups)
    with pytest.raises(ObligationIntegrityError, match="duplicate recurrence group membership"):
        _materialize_recurrence_group_context(context)


@pytest.mark.parametrize(
    "mutate",
    [
        lambda family: replace(family, semantic_nodes=family.semantic_nodes[:-1]),
        lambda family: replace(family, evidence_links=family.evidence_links[:-1]),
        lambda family: replace(family, members=family.members[::-1]),
        lambda family: replace(family, members=family.members + family.members[:1]),
        lambda family: _replace_family_row(family, "recurrence_groups", 0, member_count=2.0),
        lambda family: _replace_family_row(family, "recurrence_groups", 0, completion_policy="any"),
        lambda family: _replace_family_row(family, "members", 0, canonical_ordinal=False),
        lambda family: _replace_family_row(family, "members", 0, requirement_key="req-b"),
        lambda family: _replace_family_row(family, "members", 0, identity_hash="0" * 64),
        lambda family: _replace_family_row(family, "timing_groups", 0, owner_kind="recurrence_group_recurring"),
        lambda family: _replace_family_row(family, "timing_terms", 0, interval_numeric=1.0),
        lambda family: replace(family, projection_id="projection-other"),
        _restamp_recurrence_group_family,
    ],
)
def test_recurrence_group_verified_read_fails_closed_on_drift(mutate):
    requirements = [_requirement("req-a", 1), _requirement("req-b", 2)]
    for requirement in requirements:
        requirement["recurrenceGroupKey"] = "group-main"
    groups = [_recurrence_group(
        "group-main", ["req-b", "req-a"],
        _known_timing("group-initial"), _known_timing("group-recurring"),
    )]
    context = _recurrence_group_context(requirements, groups)
    family = _materialize_recurrence_group_context(context)
    with pytest.raises(ObligationIntegrityError):
        _verify_recurrence_group_context(context, mutate(family))


def test_recurrence_group_rejects_equal_valued_q11_boolean_corruption():
    requirements = [_requirement("req-a", 1), _requirement("req-b", 2)]
    for requirement in requirements:
        requirement["recurrenceGroupKey"] = "group-main"
    groups = [_recurrence_group(
        "group-main", ["req-a", "req-b"],
        _timing_unknown("group-initial"), _timing_unknown("group-recurring"),
    )]
    context = _recurrence_group_context(requirements, groups)
    requirement_family = _replace_family_row(
        context[6], "requirements", 0, recurrence_group_present=1,
    )
    corrupt_context = (*context[:6], requirement_family, *context[7:])
    with pytest.raises(ObligationIntegrityError, match="presence boolean type differs"):
        _materialize_recurrence_group_context(corrupt_context)


def test_recurrence_group_physical_shapes_match_generated_contract():
    from app.services.ad_v4_obligations import (
        ObligationRecurrenceGroupMember,
        ObligationRecurrenceGroupOwner,
    )

    contract = next(row for row in OWNER_CONTRACTS if row["nodeType"] == "recurrence_group")
    assert {field.name for field in fields(ObligationRecurrenceGroupOwner)} == {
        column["name"] for column in contract["columns"]
    }
    assert {field.name for field in fields(ObligationRecurrenceGroupMember)} == {
        "id", "identity_hash", "proposal_id", "projection_id", "group_node_id",
        "requirement_node_id", "requirement_key", "canonical_ordinal",
    }
    relationship = next(row for row in RELATIONSHIPS if row["id"] == "G2")
    assert relationship == {
        "id": "G2",
        "sourcePattern": "/recurrenceGroups/{i}/requirementKeys/{j}",
        "table": "ad_v4_candidate_obligation_recurrence_group_members",
        "tableLabel": "recurrence-group-member", "idPrefix": "aom",
        "identityProperties": (
            "projectionId", "groupNodeId", "requirementNodeId", "ordinal",
        ),
        "ordering": "canonical_ordinal", "cardinality": "zero_or_more",
    }


def _authority_provision(key: str, assertion: dict) -> dict:
    return {
        "provisionKey": key, "approvingAuthority": assertion,
        "evidenceKeys": [f"{key}-provision"],
    }


def test_authority_family_preserves_all_assertion_unions_and_independent_evidence():
    provisions = [
        _authority_provision("authority-known", {
            "state": "known", "value": "Manager, Certification Office",
            "evidenceKeys": ["authority-known-assertion"],
        }),
        _authority_provision("authority-unknown", {
            "state": "unknown", "reason": "not_obtained",
            "temporalScope": {"kind": "source_observation"},
            "evidenceKeys": ["authority-unknown-assertion"],
        }),
        _authority_provision("authority-na", {
            "state": "not_applicable", "reason": "No approving authority named",
            "temporalScope": {"kind": "directive_version"},
            "evidenceKeys": ["authority-na-assertion"],
        }),
    ]
    bindings = _all_evidence_bindings(provisions)
    family = materialize_authority_family(
        proposal_id="proposal-1", projection_id="projection-1",
        canonical_provisions=list(reversed(provisions)), evidence_bindings=bindings,
    )
    assert [row.provision_key for row in family.amoc_provisions] == [
        "authority-known", "authority-na", "authority-unknown",
    ]
    assert [row.state for row in family.value_assertions] == [
        "known", "not_applicable", "unknown",
    ]
    assert all(row.field_code == "approving_authority" for row in family.value_assertions)
    nodes = {row.id: row for row in family.semantic_nodes}
    for owner, assertion in zip(family.amoc_provisions, family.value_assertions, strict=True):
        assert nodes[owner.semantic_node_id].parent_node_id is None
        assert nodes[owner.authority_assertion_node_id].parent_node_id == owner.semantic_node_id
        assert nodes[owner.authority_assertion_node_id].canonical_ordinal == 0
        owner_links = [
            row for row in family.evidence_links
            if row.semantic_node_id == owner.semantic_node_id
        ]
        assertion_links = [
            row for row in family.evidence_links
            if row.semantic_node_id == assertion.semantic_node_id
        ]
        assert owner_links[0].purpose == "amoc_authority_clause"
        assert assertion_links[0].purpose == "amoc_authority_clause"
        assert owner_links[0].semantic_node_id != assertion_links[0].semantic_node_id
    owner = family.amoc_provisions[0]
    node = nodes[owner.semantic_node_id]
    identity = {
        "projectionId": "projection-1", "nodeType": "amoc_provision",
        "nodeKey": "authority-known", "pointer": "/amocAuthorityProvisions/0",
    }
    expected_hash = hashlib.sha256(
        DOMAINS["row"] + obligation_record_bytes({
            "table": "semantic-node", "identity": identity,
        })
    ).hexdigest()
    assert (node.id, node.identity_hash) == (
        f"aon_{expected_hash[:32]}", expected_hash,
    )
    assertion_node = nodes[owner.authority_assertion_node_id]
    assert (
        assertion_node.node_key, assertion_node.source_pointer,
        assertion_node.parent_node_id, assertion_node.canonical_ordinal,
    ) == (
        "/amocAuthorityProvisions/0/approvingAuthority",
        "/amocAuthorityProvisions/0/approvingAuthority",
        owner.semantic_node_id, 0,
    )


def test_authority_family_supports_empty_source():
    family = materialize_authority_family(
        proposal_id="proposal-1", projection_id="projection-1",
        canonical_provisions=[], evidence_bindings={},
    )
    assert family.semantic_nodes == ()
    assert family.evidence_links == ()
    assert family.amoc_provisions == ()
    assert family.value_assertions == ()


@pytest.mark.parametrize(
    "temporal_kind",
    [
        "directive_version", "publication_version",
        "at_applicability_evaluation", "at_compliance_evaluation",
        "source_observation",
    ],
)
def test_authority_family_accepts_every_closed_temporal_scope(temporal_kind):
    provision = _authority_provision("authority-main", {
        "state": "not_applicable", "reason": "x" * 512,
        "temporalScope": {"kind": temporal_kind},
        "evidenceKeys": ["authority-assertion"],
    })
    family = materialize_authority_family(
        proposal_id="proposal-1", projection_id="projection-1",
        canonical_provisions=[provision],
        evidence_bindings=_all_evidence_bindings([provision]),
    )
    assert family.value_assertions[0].temporal_kind == temporal_kind


def test_authority_family_rejects_reason_above_contract_limit():
    provision = _authority_provision("authority-main", {
        "state": "not_applicable", "reason": "x" * 513,
        "temporalScope": {"kind": "directive_version"},
        "evidenceKeys": ["authority-assertion"],
    })
    with pytest.raises(ObligationIntegrityError, match="non-known authority assertion"):
        materialize_authority_family(
            proposal_id="proposal-1", projection_id="projection-1",
            canonical_provisions=[provision],
            evidence_bindings=_all_evidence_bindings([provision]),
        )


@pytest.mark.parametrize(
    "mutate, message",
    [
        (lambda values: values.__setitem__(0, MappingProxyType(values[0])), "provision shape"),
        (lambda values: values[0].update({"approvedMethod": "invented"}), "provision shape"),
        (lambda values: values[0].__setitem__("provisionKey", "Bad-Key"), "key set"),
        (lambda values: values[0].__setitem__("approvingAuthority", UserDict(values[0]["approvingAuthority"])), "assertion source object"),
        (lambda values: values[0]["approvingAuthority"].__setitem__("state", []), "assertion state"),
        (lambda values: values[0]["approvingAuthority"].__setitem__("value", ""), "known authority assertion"),
        (lambda values: values[0]["approvingAuthority"].__setitem__("value", "x" * 513), "known authority assertion"),
        (lambda values: values[0]["approvingAuthority"].__setitem__("evidenceKeys", []), "evidence set"),
    ],
)
def test_authority_source_shapes_fail_closed_at_materialize_and_verify(mutate, message):
    provisions = [_authority_provision("authority-main", {
        "state": "known", "value": "FAA", "evidenceKeys": ["authority-assertion"],
    })]
    bindings = _all_evidence_bindings(provisions)
    family = materialize_authority_family(
        proposal_id="proposal-1", projection_id="projection-1",
        canonical_provisions=provisions, evidence_bindings=bindings,
    )
    malformed = deepcopy(provisions)
    mutate(malformed)
    with pytest.raises(ObligationIntegrityError, match=message):
        materialize_authority_family(
            proposal_id="proposal-1", projection_id="projection-1",
            canonical_provisions=malformed, evidence_bindings=bindings,
        )
    with pytest.raises(ObligationIntegrityError, match=message):
        verify_authority_family(
            proposal_id="proposal-1", projection_id="projection-1",
            canonical_provisions=malformed, evidence_bindings=bindings,
            family=family,
        )


@pytest.mark.parametrize(
    "collection_name, malformed",
    [
        ("semantic_nodes", None),
        ("semantic_nodes", {}),
        ("semantic_nodes", ({},)),
        ("semantic_nodes", ("x",)),
        ("semantic_nodes", (UserDict({}),)),
        ("evidence_links", ({},)),
        ("amoc_provisions", ("x",)),
        ("value_assertions", (UserDict({}),)),
    ],
)
def test_authority_verified_read_normalizes_hostile_row_shapes(
    collection_name, malformed,
):
    provision = _authority_provision("authority-main", {
        "state": "known", "value": "FAA",
        "evidenceKeys": ["authority-assertion"],
    })
    bindings = _all_evidence_bindings([provision])
    family = materialize_authority_family(
        proposal_id="proposal-1", projection_id="projection-1",
        canonical_provisions=[provision], evidence_bindings=bindings,
    )
    with pytest.raises(ObligationIntegrityError, match="row collection differs"):
        verify_authority_family(
            proposal_id="proposal-1", projection_id="projection-1",
            canonical_provisions=[provision], evidence_bindings=bindings,
            family=replace(family, **{collection_name: malformed}),
        )


@pytest.mark.parametrize(
    "evidence_key", ["authority-main-provision", "authority-assertion"],
)
@pytest.mark.parametrize("malformed", [[], {}, 0, True])
def test_authority_rejects_non_string_evidence_binding_targets_at_both_boundaries(
    evidence_key, malformed,
):
    provision = _authority_provision("authority-main", {
        "state": "known", "value": "FAA",
        "evidenceKeys": ["authority-assertion"],
    })
    bindings = _all_evidence_bindings([provision])
    family = materialize_authority_family(
        proposal_id="proposal-1", projection_id="projection-1",
        canonical_provisions=[provision], evidence_bindings=bindings,
    )
    malformed_bindings = dict(bindings)
    malformed_bindings[evidence_key] = malformed
    with pytest.raises(ObligationIntegrityError, match="target.*invalid"):
        materialize_authority_family(
            proposal_id="proposal-1", projection_id="projection-1",
            canonical_provisions=[provision],
            evidence_bindings=malformed_bindings,
        )
    with pytest.raises(ObligationIntegrityError, match="target.*invalid"):
        verify_authority_family(
            proposal_id="proposal-1", projection_id="projection-1",
            canonical_provisions=[provision],
            evidence_bindings=malformed_bindings, family=family,
        )


@pytest.mark.parametrize("malformed_bindings", [None, []])
def test_authority_rejects_non_mapping_evidence_binding_collections(
    malformed_bindings,
):
    provision = _authority_provision("authority-main", {
        "state": "known", "value": "FAA",
        "evidenceKeys": ["authority-assertion"],
    })
    with pytest.raises(ObligationIntegrityError, match="binding map"):
        materialize_authority_family(
            proposal_id="proposal-1", projection_id="projection-1",
            canonical_provisions=[provision],
            evidence_bindings=malformed_bindings,
        )


@pytest.mark.parametrize(
    "mutate",
    [
        lambda family: replace(family, semantic_nodes=family.semantic_nodes[:-1]),
        lambda family: replace(family, evidence_links=family.evidence_links[:-1]),
        lambda family: replace(family, amoc_provisions=family.amoc_provisions[::-1]),
        lambda family: _replace_family_row(family, "amoc_provisions", 0, canonical_ordinal=False),
        lambda family: _replace_family_row(family, "amoc_provisions", 0, authority_assertion_node_id="aon-cross"),
        lambda family: _replace_family_row(family, "value_assertions", 0, field_code="revision"),
        lambda family: _replace_family_row(family, "value_assertions", 0, value="Different authority"),
        lambda family: _replace_family_row(family, "evidence_links", 0, purpose="requirement_clause"),
        lambda family: replace(family, projection_id="projection-other"),
    ],
)
def test_authority_verified_read_fails_closed_on_drift(mutate):
    provisions = [
        _authority_provision("authority-a", {
            "state": "known", "value": "FAA", "evidenceKeys": ["authority-a-assertion"],
        }),
        _authority_provision("authority-b", {
            "state": "unknown", "reason": "not_obtained",
            "temporalScope": {"kind": "source_observation"},
            "evidenceKeys": ["authority-b-assertion"],
        }),
    ]
    bindings = _all_evidence_bindings(provisions)
    family = materialize_authority_family(
        proposal_id="proposal-1", projection_id="projection-1",
        canonical_provisions=provisions, evidence_bindings=bindings,
    )
    with pytest.raises(ObligationIntegrityError):
        verify_authority_family(
            proposal_id="proposal-1", projection_id="projection-1",
            canonical_provisions=provisions, evidence_bindings=bindings,
            family=mutate(family),
        )


def _correction_binding_context():
    requirements = [_requirement("req-a", 1), _requirement("req-b", 2)]
    for requirement in requirements:
        requirement["recurrenceGroupKey"] = "group-main"
    groups = [_recurrence_group(
        "group-main", ["req-a", "req-b"],
        _timing_unknown("group-initial"), _known_timing("group-recurring"),
    )]
    provision = _authority_provision("authority-main", {
        "state": "known", "value": "FAA", "evidenceKeys": ["authority-assertion"],
    })
    group_context = _recurrence_group_context(requirements, groups)
    evidence_bindings = dict(group_context[2])
    evidence_bindings.update(_all_evidence_bindings([provision]))
    group_context = (
        *group_context[:2], evidence_bindings, *group_context[3:],
    )
    group_family = _materialize_recurrence_group_context(group_context)
    authority_family = materialize_authority_family(
        proposal_id="proposal-1", projection_id="projection-1",
        canonical_provisions=[provision], evidence_bindings=evidence_bindings,
    )
    corrections = [{
        "correctionKey": "correction-main",
        "correctionType": "official_correction",
        "originalDocumentRefKey": "official-original",
        "correctingDocumentRefKey": "official-correction",
        "changedSemanticRefs": [
            {"namespace": "requirements", "key": "req-a"},
            {"namespace": "recurrenceGroups", "key": "group-main"},
            {"namespace": "amocAuthorityProvisions", "key": "authority-main"},
            {"namespace": "productScopes", "key": "scope-main"},
            {"namespace": "directiveIdentity", "key": "ad-number"},
        ],
        "evidenceKeys": ["correction-evidence"],
    }]
    refs = build_correction_reference_snapshot(
        proposal_id="proposal-1", canonical_corrections=corrections,
    )
    return group_context, group_family, [provision], authority_family, corrections, refs


def _correction_binding_kwargs(context):
    group_context, group_family, provisions, authority_family, corrections, refs = context
    return {
        "proposal_id": "proposal-1", "projection_id": "projection-1",
        "app_projection_id": "app-projection-1",
        "canonical_corrections": corrections, "foundation_refs": refs,
        "canonical_requirements": group_context[0],
        "canonical_recurrence_groups": group_context[1],
        "canonical_provisions": provisions,
        "evidence_bindings": group_context[2],
        "canonical_documents": group_context[3],
        "document_evidence_bindings": group_context[4],
        "document_family": group_context[5],
        "requirement_family": group_context[6],
        "app_targets": _expression_app_targets(),
        "expression_family": group_context[7],
        "timing_recurrence_family": group_context[8],
        "recurrence_group_family": group_family,
        "authority_family": authority_family,
    }


def test_correction_binding_family_selects_only_exact_slice_3b_roots_and_fold():
    context = _correction_binding_context()
    kwargs = _correction_binding_kwargs(context)
    family = materialize_correction_binding_family(**kwargs)
    assert len(context[5]) == 5
    assert len(family.bindings) == 3
    assert all(row.binding_slice == "slice_3b" and row.generation == 1 for row in family.bindings)
    assert all(row.projection_id is None and row.semantic_node_id is None for row in family.bindings)
    assert all(row.obligation_projection_id == "projection-1" for row in family.bindings)
    targets = {
        row.obligation_semantic_node_id for row in family.bindings
    }
    assert targets == {
        kwargs["requirement_family"].requirements[0].semantic_node_id,
        kwargs["recurrence_group_family"].recurrence_groups[0].semantic_node_id,
        kwargs["authority_family"].amoc_provisions[0].semantic_node_id,
    }
    binding = family.bindings[0]
    identity = {
        "refId": binding.correction_ref_id,
        "semanticId": binding.obligation_semantic_node_id,
    }
    expected_hash = hashlib.sha256(
        DOMAINS["row"] + obligation_record_bytes({
            "table": "correction-binding", "identity": identity,
        })
    ).hexdigest()
    assert (binding.id, binding.binding_hash) == (
        f"avk_{expected_hash[:32]}", expected_hash,
    )
    records = json.loads(family.binding_set_bytes)
    assert records == sorted(
        records,
        key=lambda row: (
            row["correctionRefId"], row["bindingSlice"],
            row["targetSemanticNodeId"],
        ),
    )
    assert family.binding_set_hash == hashlib.sha256(
        DOMAINS["correctionBindingSet"] + family.binding_set_bytes
    ).hexdigest()
    requirement_ref = next(
        row for row in context[5] if row.namespace == "requirements"
    )
    correction_identity = {
        "proposalId": "proposal-1", "correctionKey": "correction-main",
    }
    correction_hash = hashlib.sha256(
        b"paprnav:ad_extraction_v4:applicability-row:2\x00"
        + canonical_bytes({
            "table": "correction", "identity": correction_identity,
        }, CANONICALIZATION_VERSION_V2)
    ).hexdigest()
    correction_id = f"avc_{correction_hash[:32]}"
    ref_identity = {
        "correctionId": correction_id,
        "namespace": "requirements", "key": "req-a",
    }
    ref_hash = hashlib.sha256(
        b"paprnav:ad_extraction_v4:applicability-row:2\x00"
        + canonical_bytes({
            "table": "correction-ref", "identity": ref_identity,
        }, CANONICALIZATION_VERSION_V2)
    ).hexdigest()
    assert (
        requirement_ref.correction_id, requirement_ref.id,
        requirement_ref.reference_hash,
    ) == (correction_id, f"avf_{ref_hash[:32]}", ref_hash)
    legacy_domain_hash = hashlib.sha256(
        b"paprnav:ad_extraction_v4:applicability-row:2\x00"
        + canonical_bytes({
            "table": "correction-binding", "identity": identity,
        }, CANONICALIZATION_VERSION_V2)
    ).hexdigest()
    assert binding.binding_hash != legacy_domain_hash


def test_correction_binding_empty_set_is_exact():
    context = _correction_binding_context()
    kwargs = _correction_binding_kwargs(context)
    kwargs["canonical_corrections"] = []
    kwargs["foundation_refs"] = ()
    family = materialize_correction_binding_family(**kwargs)
    assert family.bindings == ()
    assert family.binding_set_bytes == b"[]"
    assert family.binding_set_hash == hashlib.sha256(
        DOMAINS["correctionBindingSet"] + b"[]"
    ).hexdigest()


def test_distinct_corrections_can_bind_the_same_semantic_node_exactly_once_each():
    context = _correction_binding_context()
    kwargs = _correction_binding_kwargs(context)
    second = deepcopy(kwargs["canonical_corrections"][0])
    second["correctionKey"] = "correction-second"
    second["changedSemanticRefs"] = [
        {"namespace": "requirements", "key": "req-a"},
    ]
    kwargs["canonical_corrections"] = [
        *kwargs["canonical_corrections"], second,
    ]
    kwargs["foundation_refs"] = build_correction_reference_snapshot(
        proposal_id="proposal-1",
        canonical_corrections=kwargs["canonical_corrections"],
    )
    family = materialize_correction_binding_family(**kwargs)
    requirement_node_id = kwargs[
        "requirement_family"
    ].requirements[0].semantic_node_id
    requirement_bindings = [
        row for row in family.bindings
        if row.obligation_semantic_node_id == requirement_node_id
    ]
    assert len(requirement_bindings) == 2
    assert len({row.correction_ref_id for row in requirement_bindings}) == 2
    assert len({row.id for row in requirement_bindings}) == 2


def test_correction_binding_resolves_equal_keys_by_namespace_and_owner_type():
    requirements = [
        _requirement("shared-key", 1), _requirement("req-second", 2),
    ]
    groups = [_recurrence_group(
        "shared-key", ["shared-key", "req-second"],
        _timing_unknown("group-initial"), _known_timing("group-recurring"),
    )]
    for requirement in requirements:
        requirement["recurrenceGroupKey"] = "shared-key"
    provision = _authority_provision("shared-key", {
        "state": "known", "value": "FAA",
        "evidenceKeys": ["authority-assertion"],
    })
    group_context = _recurrence_group_context(requirements, groups)
    evidence_bindings = dict(group_context[2])
    evidence_bindings.update(_all_evidence_bindings([provision]))
    group_context = (
        *group_context[:2], evidence_bindings, *group_context[3:],
    )
    group_family = _materialize_recurrence_group_context(group_context)
    authority_family = materialize_authority_family(
        proposal_id="proposal-1", projection_id="projection-1",
        canonical_provisions=[provision], evidence_bindings=evidence_bindings,
    )
    corrections = [{
        "correctionKey": "correction-shared",
        "correctionType": "official_correction",
        "originalDocumentRefKey": "official-original",
        "correctingDocumentRefKey": "official-correction",
        "changedSemanticRefs": [
            {"namespace": "requirements", "key": "shared-key"},
            {"namespace": "recurrenceGroups", "key": "shared-key"},
            {"namespace": "amocAuthorityProvisions", "key": "shared-key"},
        ],
        "evidenceKeys": ["correction-evidence"],
    }]
    kwargs = {
        "proposal_id": "proposal-1", "projection_id": "projection-1",
        "app_projection_id": "app-projection-1",
        "canonical_corrections": corrections,
        "foundation_refs": build_correction_reference_snapshot(
            proposal_id="proposal-1", canonical_corrections=corrections,
        ),
        "canonical_requirements": group_context[0],
        "canonical_recurrence_groups": group_context[1],
        "canonical_provisions": [provision],
        "evidence_bindings": evidence_bindings,
        "canonical_documents": group_context[3],
        "document_evidence_bindings": group_context[4],
        "document_family": group_context[5],
        "requirement_family": group_context[6],
        "app_targets": _expression_app_targets(),
        "expression_family": group_context[7],
        "timing_recurrence_family": group_context[8],
        "recurrence_group_family": group_family,
        "authority_family": authority_family,
    }
    family = materialize_correction_binding_family(**kwargs)
    nodes = {
        node.id: node
        for node in (
            *kwargs["requirement_family"].semantic_nodes,
            *group_family.semantic_nodes,
            *authority_family.semantic_nodes,
        )
    }
    assert [
        nodes[row.obligation_semantic_node_id].node_type
        for row in family.bindings
    ] == ["amoc_provision", "recurrence_group", "requirement"]


@pytest.mark.parametrize(
    "mutate, message",
    [
        (lambda corrections: corrections.__setitem__(0, MappingProxyType(corrections[0])), "source shape"),
        (lambda corrections: corrections[0]["changedSemanticRefs"].__setitem__(0, UserDict(corrections[0]["changedSemanticRefs"][0])), "reference shape"),
        (lambda corrections: corrections[0]["changedSemanticRefs"][0].__setitem__("namespace", []), "reference value"),
        (lambda corrections: corrections[0]["changedSemanticRefs"].append(deepcopy(corrections[0]["changedSemanticRefs"][0])), "reference value"),
        (lambda corrections: corrections[0].__setitem__("correctionType", "silent_edit"), "correction type"),
    ],
)
def test_correction_binding_source_shapes_fail_closed_at_both_boundaries(mutate, message):
    context = _correction_binding_context()
    kwargs = _correction_binding_kwargs(context)
    family = materialize_correction_binding_family(**kwargs)
    malformed = deepcopy(kwargs["canonical_corrections"])
    mutate(malformed)
    kwargs["canonical_corrections"] = malformed
    with pytest.raises(ObligationIntegrityError, match=message):
        materialize_correction_binding_family(**kwargs)
    with pytest.raises(ObligationIntegrityError, match=message):
        verify_correction_binding_family(**kwargs, family=family)


@pytest.mark.parametrize(
    "mutate",
    [
        lambda refs: refs[:-1],
        lambda refs: refs + refs[:1],
        lambda refs: _replace_tuple_row(refs, 0, owner_slice="slice_3b"),
        lambda refs: _replace_tuple_row(refs, 0, reference_hash="0" * 64),
        lambda refs: _replace_tuple_row(refs, 0, canonical_ordinal=False),
    ],
)
def test_correction_binding_rejects_incomplete_or_relabeled_foundation_refs(mutate):
    context = _correction_binding_context()
    kwargs = _correction_binding_kwargs(context)
    kwargs["foundation_refs"] = mutate(kwargs["foundation_refs"])
    with pytest.raises(ObligationIntegrityError):
        materialize_correction_binding_family(**kwargs)


@pytest.mark.parametrize(
    "malformed_refs",
    [None, {}, [{}], ["x"], [UserDict({})]],
)
def test_correction_binding_normalizes_hostile_foundation_row_shapes_at_both_boundaries(
    malformed_refs,
):
    context = _correction_binding_context()
    kwargs = _correction_binding_kwargs(context)
    family = materialize_correction_binding_family(**kwargs)
    kwargs["foundation_refs"] = malformed_refs
    with pytest.raises(ObligationIntegrityError, match="row collection differs"):
        materialize_correction_binding_family(**kwargs)
    with pytest.raises(ObligationIntegrityError, match="row collection differs"):
        verify_correction_binding_family(**kwargs, family=family)


def _replace_tuple_row(rows, ordinal: int, **changes):
    result = list(rows)
    result[ordinal] = replace(result[ordinal], **changes)
    return tuple(result)


@pytest.mark.parametrize(
    "mutate",
    [
        lambda family: replace(family, bindings=family.bindings[:-1]),
        lambda family: replace(family, bindings=family.bindings[::-1]),
        lambda family: _replace_family_row(family, "bindings", 0, generation=True),
        lambda family: _replace_family_row(family, "bindings", 0, binding_slice="slice_3a"),
        lambda family: _replace_family_row(family, "bindings", 0, projection_id="app-projection-1"),
        lambda family: _replace_family_row(family, "bindings", 0, obligation_projection_id="projection-other"),
        lambda family: _replace_family_row(family, "bindings", 0, obligation_semantic_node_id="aon-cross"),
        lambda family: _replace_family_row(family, "bindings", 0, binding_hash="0" * 64),
        lambda family: replace(family, binding_set_bytes=bytearray(family.binding_set_bytes)),
        lambda family: replace(family, binding_set_hash="0" * 64),
    ],
)
def test_correction_binding_verified_read_fails_closed_on_drift(mutate):
    context = _correction_binding_context()
    kwargs = _correction_binding_kwargs(context)
    family = materialize_correction_binding_family(**kwargs)
    with pytest.raises(ObligationIntegrityError):
        verify_correction_binding_family(**kwargs, family=mutate(family))


@pytest.mark.parametrize(
    "malformed_bindings",
    [None, {}, ({},), ("x",), (UserDict({}),)],
)
def test_correction_binding_verified_read_normalizes_hostile_binding_row_shapes(
    malformed_bindings,
):
    context = _correction_binding_context()
    kwargs = _correction_binding_kwargs(context)
    family = materialize_correction_binding_family(**kwargs)
    with pytest.raises(ObligationIntegrityError, match="row collection differs"):
        verify_correction_binding_family(
            **kwargs, family=replace(family, bindings=malformed_bindings),
        )


def test_authority_and_correction_physical_shapes_match_generated_contract():
    from app.services.ad_v4_obligations import (
        ObligationAmocProvisionOwner,
        ObligationCorrectionSemanticBinding,
    )

    contract = next(row for row in OWNER_CONTRACTS if row["nodeType"] == "amoc_provision")
    assert {field.name for field in fields(ObligationAmocProvisionOwner)} == {
        column["name"] for column in contract["columns"]
    }
    assert {field.name for field in fields(ObligationCorrectionSemanticBinding)} == {
        "id", "correction_ref_id", "proposal_id", "projection_id",
        "semantic_node_id", "obligation_projection_id",
        "obligation_semantic_node_id", "binding_slice", "generation",
        "binding_hash",
    }
    correction = next(row for row in RELATIONSHIPS if row["id"] == "CB")
    assert correction["identityProperties"] == ("refId", "semanticId")
