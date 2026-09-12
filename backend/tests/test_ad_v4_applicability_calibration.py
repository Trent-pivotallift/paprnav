from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from app.core.config import get_settings
from app.models.core import (
    ADV4CandidateAppChangeDependency,
    ADV4CandidateAppCondition,
    ADV4CandidateAppEvidenceLink,
    ADV4CandidateAppDesignationScope,
    ADV4CandidateAppDesignationGroup,
    ADV4CandidateAppDesignationGroupMember,
    ADV4CandidateAppDesignationValue,
    ADV4CandidateAppIdentityMapping,
    ADV4CandidateAppProjection,
    ADV4CandidateAppProductScope,
    ADV4CandidateAppSearchHint,
    ADV4CandidateAppSearchHintGroup,
    ADV4CandidateAppSearchHintMember,
    ADV4CandidateAppSemanticNode,
    ADV4CandidateAppValueAssertion,
    ADV4CandidateCorrection,
    ADV4CandidateCorrectionEvidenceLink,
    ADV4CandidateCorrectionRef,
    ADV4CandidateCorrectionSemanticBinding,
    ADV4FeatureGate,
    AirworthinessDirective,
)
from app.services.ad_evidence import admit_evidence_fragment
from app.services.ad_v4_applicability import materialize_applicability, reconstruct_applicability
from app.services.ad_v4_candidates import (
    ADV4Error,
    CANONICALIZATION_VERSION_V2,
    VALIDATOR_VERSION,
    VALIDATOR_VERSION_V2,
    canonical_bytes,
    parse_v4_request_bytes,
    store_v4_candidate,
    validate_v4_envelope,
)
from conftest import add_membership, create_organization, create_user
from test_ad_v4_calibration import (
    SOURCES,
    _executable,
    _load_template,
    _packet_fragments,
    _retain_packet_sources,
)


def _known(value: str, evidence_key: str) -> dict:
    return {"state": "known", "value": value, "evidenceKeys": [evidence_key]}


def _member(key: str, designation: str, manufacturer: str, evidence_key: str) -> dict:
    return {
        "memberKey": key,
        "designationKind": "model",
        "sourceDesignation": designation,
        "manufacturer": _known(manufacturer, evidence_key),
        "evidenceKeys": [evidence_key],
    }


def validator2_calibration_envelope(packet_key: str, envelope: dict) -> dict:
    """Test fixture transform approved by Slice-3A; retained evidence is unchanged."""
    value = copy.deepcopy(envelope)
    proposal = value["proposal"]
    conditions = {item["conditionKey"]: item for item in proposal["conditionDefinitions"]}
    if packet_key == "1998-17-11":
        conditions["condition-provenance-unknown"]["subject"]["attributeValue"] = {
            "state": "unknown",
            "reason": "not_observed",
            "temporalScope": {"kind": "at_applicability_evaluation"},
            "evidenceKeys": ["ev-unknown-provenance"],
        }
    elif packet_key == "2002-13-04":
        group_specs = {
            "condition-magneto-installed": (
                "6314,6324,6364", "Unison Industries (Slick)",
                ["6314", "6324", "6364"], "ev-applicability-conflict",
            ),
            "condition-family-a": (
                "C-125,C145,O-300,IO-360,TSIO-360", "Teledyne Continental Motors (TCM)",
                ["C-125", "C145", "O-300", "IO-360", "TSIO-360"], "ev-family-a",
            ),
            "condition-family-b": (
                "LTSIO-520-AE", "Teledyne Continental Motors (TCM)",
                ["LTSIO-520-AE"], "ev-family-b",
            ),
        }
        for condition_key, (display, manufacturer, designations, evidence_key) in group_specs.items():
            subject = conditions[condition_key]["subject"]
            subject.pop("modelOrSeries", None)
            subject["designationGroup"] = {
                "groupKey": f"group-{condition_key.removeprefix('condition-')}",
                "sourceDisplayText": _known(display, evidence_key),
                "association": "any_member" if len(designations) > 1 else "source_group",
                "members": [
                    _member(f"member-{condition_key.removeprefix('condition-')}-{index}", item, manufacturer, evidence_key)
                    for index, item in enumerate(designations, start=1)
                ],
                "evidenceKeys": [evidence_key],
            }
        evidence_key = "ev-applicability-conflict"
        groups = [
            ("cessna", "Cessna", ["170", "170A", "170B", "172", "172XP", "336", "337", "T303"]),
            ("beagle", "Beagle", ["B242-C"]),
            ("cirrus", "Cirrus", ["SR20", "SR22"]),
            ("globe-swift", "Globe Swift", ["GC-1A", "GC-1B"]),
            ("maule", "Maule", ["M4"]),
            ("piper", "Piper", ["PA-28R-201T", "PA-34"]),
            ("reims-cessna", "Reims (Cessna)", ["FA172", "F337", "FR172"]),
        ]
        manufacturer_groups = []
        for group_key, manufacturer, models in groups:
            members = [
                _member(f"member-{group_key}-{index}", model, manufacturer, evidence_key)
                for index, model in enumerate(models, start=1)
            ]
            if group_key == "cessna":
                members.append({
                    "memberKey": "member-cessna-series-172a-through-172h",
                    "designationKind": "series_expression",
                    "expressionText": "172A through 172H",
                    "evaluationState": "unknown",
                    "reason": "unsupported_expression",
                    "manufacturer": _known(manufacturer, evidence_key),
                    "evidenceKeys": [evidence_key],
                })
            manufacturer_groups.append({
                "groupKey": f"hint-group-{group_key}",
                "manufacturer": _known(manufacturer, evidence_key),
                "association": "paired",
                "members": members,
                "evidenceKeys": [evidence_key],
            })
        proposal["applicabilitySearchHints"] = [{
            "hintKey": "hint-airframes",
            "productRole": "airframe",
            "sourceDisplayText": _known(
                "These engines are used on, but not limited to Cessna, Beagle, Cirrus, Globe Swift, Maule, Piper, and Reims (Cessna) airplanes.",
                evidence_key,
            ),
            "manufacturerModelGroups": manufacturer_groups,
            "controlling": False,
            "exhaustive": False,
            "evidenceKeys": [evidence_key],
        }]
    elif packet_key == "2024-14-03":
        evidence_key = "ev-applicability"
        subject = conditions["condition-gfc500-gsa28-stc"]["subject"]
        subject.pop("modelOrSeries")
        subject["designationGroup"] = {
            "groupKey": "group-gfc500-gsa28",
            "sourceDisplayText": _known("GFC 500 and GSA 28", evidence_key),
            "association": "all_members",
            "members": [
                _member("member-gfc500", "GFC 500", "Garmin", evidence_key),
                _member("member-gsa28", "GSA 28", "Garmin", evidence_key),
            ],
            "evidenceKeys": [evidence_key],
        }
    return value


def _enable_v2(monkeypatch, db_session) -> None:
    monkeypatch.setenv("PAPRNAV_AD_V4_VALIDATOR2_WRITES_ENABLED", "true")
    monkeypatch.setenv("PAPRNAV_AD_V4_SLICE3A_ROUTES_ENABLED", "true")
    get_settings.cache_clear()
    db_session.add_all([
        ADV4FeatureGate(gate_key="validator2_write_enabled", enabled=True, changed_by="calibration"),
        ADV4FeatureGate(gate_key="materializer3a_enabled", enabled=True, changed_by="calibration"),
    ])
    db_session.flush()


@pytest.mark.parametrize("packet", SOURCES["packets"], ids=lambda item: item["packet"])
def test_validator2_five_packet_schema_and_canonical_determinism(packet):
    directive_id = "ad-" + packet["packet"]
    original = _executable(packet, _load_template(packet))
    corrected = validator2_calibration_envelope(packet["packet"], original)
    parsed = parse_v4_request_bytes(json.dumps(corrected, ensure_ascii=False, separators=(",", ":")).encode())
    proposal, _ = validate_v4_envelope(parsed, directive_id, validator_version=VALIDATOR_VERSION_V2)
    expected = canonical_bytes(proposal, CANONICALIZATION_VERSION_V2)
    reversed_proposal = copy.deepcopy(proposal)
    reversed_proposal["productScopes"].reverse()
    assert canonical_bytes(reversed_proposal, CANONICALIZATION_VERSION_V2) == expected
    if packet["packet"] == "1998-17-11":
        assert original["proposal"]["conditionDefinitions"][1]["subject"]["attributeValue"]["value"] == "unknown_requires_compliance"
        legacy, _ = validate_v4_envelope(
            parse_v4_request_bytes(json.dumps(original, separators=(",", ":")).encode()),
            directive_id,
            validator_version=VALIDATOR_VERSION,
        )
        assert canonical_bytes(legacy) == canonical_bytes(original["proposal"])


@pytest.mark.parametrize("packet", SOURCES["packets"], ids=lambda item: item["packet"])
def test_validator2_five_packet_real_evidence_materialization_roundtrip(
    packet, db_session, tmp_path: Path, monkeypatch,
):
    _enable_v2(monkeypatch, db_session)
    storage_root = tmp_path / "retained-evidence"
    monkeypatch.setenv("PAPRNAV_LOCAL_STORAGE_PATH", str(storage_root))
    get_settings.cache_clear()
    actor = create_user(db_session, f"v2-{packet['packet']}@example.test", "V2 Calibration Admin")
    organization = create_organization(db_session, f"V2 Calibration {packet['packet']}", "platform")
    membership = add_membership(db_session, organization, actor, "platform_admin")
    directive = AirworthinessDirective(ad_number=packet["adNumber"], title="", status="candidate", source_content_hash=packet["documents"][0]["sha256"])
    db_session.add(directive)
    db_session.flush()
    retained = _retain_packet_sources(db_session, packet, directive, storage_root)
    db_session.expire(directive, ["publications"])
    admitted = {}
    for item in _packet_fragments(packet["packet"]).values():
        document = retained[item["sourceKey"]]
        locators = item.get("locators", {})
        fragment, _ = admit_evidence_fragment(
            db_session, directive_id=directive.id, source_document_id=document.id,
            page_number=int(item["pageNumber"]), expected_source_content_hash=document.content_hash,
            expected_page_text_hash=item["pageTextHash"], character_start=int(item["characterStart"]),
            character_end=int(item["characterEnd"]), actor=actor, reason="validator-2 calibration",
            paragraph_locator=locators.get("paragraph"), table_locator=locators.get("table"),
            row_locator=locators.get("row"), note_locator=locators.get("note"),
        )
        admitted[item["evidenceKey"]] = fragment
    envelope = validator2_calibration_envelope(packet["packet"], _executable(
        packet, _load_template(packet), admitted_fragments=admitted,
        retained_documents=retained, directive_id=directive.id,
    ))
    stored = store_v4_candidate(
        db_session, directive_id=directive.id,
        parsed=parse_v4_request_bytes(json.dumps(envelope, ensure_ascii=False, separators=(",", ":")).encode()),
        actor=actor, membership_id=membership.id, idempotency_key="v2-calibration",
        validator_version=VALIDATOR_VERSION_V2,
    )
    result = materialize_applicability(
        db_session, directive_id=directive.id, proposal_id=stored.proposal.id,
        actor=actor, membership_id=membership.id, idempotency_key="materialize-calibration",
    )
    reconstructed = reconstruct_applicability(db_session, result.projection)
    assert canonical_bytes(reconstructed, CANONICALIZATION_VERSION_V2) == canonical_bytes(
        {key: envelope["proposal"][key] for key in ("productScopes", "conditionDefinitions", "applicabilityRules", "applicabilitySearchHints")},
        CANONICALIZATION_VERSION_V2,
    )
    nodes = db_session.query(ADV4CandidateAppSemanticNode).all()
    assert len([node for node in nodes if node.node_type == "product_scope"]) == len(envelope["proposal"]["productScopes"])
    assert db_session.query(ADV4CandidateAppProductScope).count() == len(envelope["proposal"]["productScopes"])
    assert db_session.query(ADV4CandidateAppValueAssertion).join(
        ADV4CandidateAppProductScope,
        ADV4CandidateAppValueAssertion.parent_semantic_node_id
        == ADV4CandidateAppProductScope.semantic_node_id,
    ).filter(ADV4CandidateAppValueAssertion.field_code == "manufacturer").count() == len(envelope["proposal"]["productScopes"])
    assert db_session.query(ADV4CandidateAppCondition).count() == len(
        envelope["proposal"]["conditionDefinitions"]
    )
    expected_groups = sum(
        "designationGroup" in condition["subject"]
        for condition in envelope["proposal"]["conditionDefinitions"]
    )
    expected_group_members = sum(
        len(condition["subject"].get("designationGroup", {}).get("members", []))
        for condition in envelope["proposal"]["conditionDefinitions"]
    )
    assert db_session.query(ADV4CandidateAppDesignationGroup).count() == expected_groups
    assert db_session.query(ADV4CandidateAppDesignationGroupMember).count() == expected_group_members
    assert db_session.query(ADV4CandidateAppDesignationScope).count() == sum(
        field in scope
        for scope in envelope["proposal"]["productScopes"]
        for field in ("modelScope", "serialScope", "partNumberScope")
    )
    model_count = sum(len(scope["modelScope"].get("sourceDesignations", [])) for scope in envelope["proposal"]["productScopes"])
    assert db_session.query(ADV4CandidateAppIdentityMapping).filter_by(identity_kind="model", normalization_origin="no_normalized_identity").count() == model_count
    assert db_session.query(ADV4CandidateAppDesignationValue).count() == model_count
    assert db_session.query(ADV4CandidateAppSemanticNode).filter_by(node_type="identity_mapping").count() == db_session.query(ADV4CandidateAppIdentityMapping).count()
    assert db_session.query(ADV4CandidateAppEvidenceLink).join(
        ADV4CandidateAppSemanticNode,
        ADV4CandidateAppEvidenceLink.semantic_node_id == ADV4CandidateAppSemanticNode.id,
    ).filter(ADV4CandidateAppSemanticNode.node_type == "designation_value").count() == 0
    if packet["packet"] == "2024-14-03":
        assert model_count == 182
    elif packet["packet"] == "2011-10-09":
        assert model_count == 224
        dependency = db_session.query(ADV4CandidateAppChangeDependency).one()
        assert dependency.successor_ad_number == packet["adNumber"]
        assert dependency.resolution_state == "unresolved" and dependency.target_projection_id is None
    elif packet["packet"] == "2002-13-04":
        hint = reconstructed["applicabilitySearchHints"][0]
        members = [member for group in hint["manufacturerModelGroups"] for member in group["members"]]
        assert db_session.query(ADV4CandidateAppSearchHint).count() == 1
        assert db_session.query(ADV4CandidateAppSearchHintGroup).count() == 7
        assert db_session.query(ADV4CandidateAppSearchHintMember).count() == 20
        assert sum(member["designationKind"] == "model" for member in members) == 19
        assert [member["expressionText"] for member in members if member["designationKind"] == "series_expression"] == ["172A through 172H"]
        assert not {"172B", "172H"}.intersection(member.get("sourceDesignation") for member in members)
    elif packet["packet"] == "2008-26-10":
        correction = db_session.query(ADV4CandidateCorrection).one()
        assert correction.expected_ref_count == 2 and correction.expected_evidence_count == 2
        assert db_session.query(ADV4CandidateCorrectionRef).count() == 2
        assert db_session.query(ADV4CandidateCorrectionSemanticBinding).count() == 1
        assert db_session.query(ADV4CandidateCorrectionEvidenceLink).count() == 2
        missing_link = db_session.query(ADV4CandidateCorrectionEvidenceLink).first()
        db_session.delete(missing_link)
        db_session.flush()
        with pytest.raises(ADV4Error, match="Correction foundation"):
            reconstruct_applicability(db_session, result.projection)
