from __future__ import annotations

import copy
import hashlib
import json
import os
import shutil
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

import pytest
import pypdf
from pypdf import PdfReader

from app.core.config import get_settings
from app.models.core import (
    ADEvidenceFragmentLifecycleEvent,
    ADPublication,
    ADSourceDocument,
    ADV4CandidateProposal,
    ADV4CandidateSubmission,
    AirworthinessDirective,
)
from app.services.ad_evidence import admit_evidence_fragment
from app.services.ad_extraction import bounded_issue_pages, bounded_source_document_pages
from app.services.ad_v4_candidates import (
    ADV4Error,
    canonical_bytes,
    parse_v4_request_bytes,
    store_v4_candidate,
    validate_v4_envelope,
)
from conftest import add_membership, create_organization, create_user


FIXTURE_ROOT = Path(__file__).parent / "fixtures" / "ad_v4_calibration"
REPOSITORY_ROOT = Path(__file__).parents[2]
SOURCES = json.loads((FIXTURE_ROOT / "sources.manifest.json").read_text())
FRAGMENTS = json.loads((FIXTURE_ROOT / "fragments.manifest.json").read_text())


def _source_root() -> Path:
    configured = os.getenv(SOURCES["sourceRootEnvironment"])
    return Path(configured) if configured else REPOSITORY_ROOT / SOURCES["defaultSourceRoot"]


def _normalized_page_text(page) -> str:
    value = (page.extract_text() or "").replace("\r\n", "\n").replace("\r", "\n")
    return unicodedata.normalize("NFC", value)


def _packet_fragments(packet_key: str) -> dict[str, dict]:
    packet = next(item for item in FRAGMENTS["packets"] if item["packet"] == packet_key)
    return {item["evidenceKey"]: item for item in packet["fragments"]}


def _assert_claim_evidence(item: dict, claim_kind: str, fragments: dict[str, dict]) -> None:
    keys = item["evidenceKeys"]
    assert keys, f"{claim_kind} claim has no evidence"
    assert set(keys) <= set(fragments)
    assert any(claim_kind in fragments[key]["claimKinds"] for key in keys), (
        claim_kind,
        keys,
    )


def _assert_claim_by_claim_evidence(packet_key: str, proposal: dict) -> None:
    """Prove each safety semantic resolves to a clause typed for that claim."""

    fragments = _packet_fragments(packet_key)
    for scope in proposal["productScopes"]:
        for item in (
            scope,
            scope["manufacturer"]["normalizedIdentity"],
            scope["modelScope"],
            scope["serialScope"],
            scope["partNumberScope"],
        ):
            _assert_claim_evidence(item, "applicability", fragments)
    for condition in proposal["conditionDefinitions"]:
        _assert_claim_evidence(condition, "applicability", fragments)
    for rule in proposal["applicabilityRules"]:
        _assert_claim_evidence(rule, "applicability", fragments)
    for requirement in proposal["requirements"]:
        _assert_claim_evidence(requirement["action"], "action", fragments)
        _assert_claim_evidence(requirement["branch"], "branch", fragments)
        _assert_claim_evidence(requirement["initialTiming"], "timing", fragments)
        for term in requirement["initialTiming"].get("terms", []):
            _assert_claim_evidence(term, "timing", fragments)
        if requirement["terminatingEffect"]["kind"] != "none":
            _assert_claim_evidence(requirement["terminatingEffect"], "terminating_action", fragments)
    for group in proposal["recurrenceGroups"]:
        _assert_claim_evidence(group["initialTiming"], "timing", fragments)
        _assert_claim_evidence(group["recurringTiming"], "timing", fragments)
    for relation in proposal["supersessionRelations"]:
        _assert_claim_evidence(relation, "supersession_status", fragments)
    for correction in proposal["authoritativeCorrections"]:
        _assert_claim_evidence(correction, "correction", fragments)
    for provision in proposal["amocAuthorityProvisions"]:
        _assert_claim_evidence(provision, "amoc", fragments)
    for document in proposal["incorporatedDocuments"]:
        _assert_claim_evidence(document, "service_information", fragments)


def _calibration_admission_oracle(packet_key: str, envelope: dict) -> dict:
    """Test-only gold boundary; production must never hard-code these five ADs."""

    try:
        expected = _packet_fragments(packet_key)
        bindings = envelope["proposal"]["evidenceBindings"]
        assert set(bindings) == set(expected)
        assert all(bindings[key]["fragmentHash"] == item["exactTextHash"] for key, item in expected.items())
        _assert_packet_contract(packet_key, envelope)
        _assert_claim_by_claim_evidence(packet_key, envelope["proposal"])
    except AssertionError as exc:
        raise ADV4Error(
            "calibration_semantic_mismatch",
            "/proposal",
            f"Proposal diverges from source-accounted calibration packet {packet_key}",
        ) from exc
    return envelope["proposal"]


def _load_template(packet: dict) -> dict:
    raw = (FIXTURE_ROOT / packet["proposalTemplate"]).read_bytes()
    value = json.loads(raw)
    stable = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    assert hashlib.sha256(stable).hexdigest() == packet["proposalTemplateSha256"]
    return value


def _executable(
    packet: dict,
    template: dict,
    *,
    admitted_fragments: dict[str, object] | None = None,
    retained_documents: dict[str, ADSourceDocument] | None = None,
    directive_id: str | None = None,
) -> dict:
    fragments = _packet_fragments(packet["packet"])
    value = copy.deepcopy(template)
    if directive_id is not None:
        value["proposal"]["directiveIdentity"]["directiveId"] = directive_id
    for key, binding in value["proposal"]["evidenceBindings"].items():
        fragment = fragments[key]
        admitted = admitted_fragments.get(key) if admitted_fragments is not None else None
        binding["fragmentId"] = admitted.id if admitted is not None else "aef-cal-" + fragment["exactTextHash"][:24]
        binding["fragmentHash"] = admitted.fragment_hash if admitted is not None else fragment["exactTextHash"]
    for document in value["proposal"]["officialDocuments"]:
        source = next(item for item in packet["documents"] if item["logicalKey"] == document["officialDocumentKey"])
        retained = retained_documents.get(source["logicalKey"]) if retained_documents is not None else None
        document["sourceDocumentId"] = retained.id if retained is not None else "asd-cal-" + source["sha256"][:24]
    return value


def _retain_packet_sources(db_session, packet: dict, directive: AirworthinessDirective, storage_root: Path) -> dict[str, ADSourceDocument]:
    retained: dict[str, ADSourceDocument] = {}
    for source in packet["documents"]:
        source_path = _source_root() / source["relativePath"]
        storage_key = f"calibration/{packet['packet']}/{source_path.name}"
        destination = storage_root / storage_key
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source_path, destination)
        document = ADSourceDocument(
            source_system="calibration-retained-official",
            source_type="issue_pdf" if int(source["pageCount"]) > 50 else "document_pdf",
            source_identifier=f"{packet['packet']}:{source['logicalKey']}",
            storage_backend="local",
            storage_key=storage_key,
            media_type="application/pdf",
            content_hash=source["sha256"],
            storage_bytes=int(source["byteLength"]),
            captured_at=datetime.now(timezone.utc),
            status="retained",
        )
        db_session.add(document)
        db_session.flush()
        db_session.add(ADPublication(
            directive_id=directive.id,
            source_document_id=document.id,
            source_system=document.source_system,
            source_type=document.source_type,
            source_identifier=document.source_identifier,
            title=f"Official source for {packet['adNumber']}",
            status="retained",
            content_hash=document.content_hash,
        ))
        retained[source["logicalKey"]] = document
    db_session.flush()
    return retained


def _all_models(proposal: dict) -> list[str]:
    return [model for scope in proposal["productScopes"] for model in scope["modelScope"]["sourceDesignations"]]


def _assert_packet_contract(packet_key: str, envelope: dict) -> None:
    proposal = envelope["proposal"]
    scopes = proposal["productScopes"]
    requirements = proposal["requirements"]
    models = _all_models(proposal)
    assert [item["sequence"] for item in requirements] == [str(i) for i in range(1, len(requirements) + 1)]

    if packet_key == "2024-14-03":
        assert len(scopes) == 5 and len(models) == len(set(models)) == 182
        manufacturer_values = {scope["manufacturer"]["sourceValue"] for scope in scopes}
        assert not manufacturer_values.intersection(models)
        assert all(scope["serialScope"]["kind"] == "not_applicable" for scope in scopes)
        assert all(scope["serialScope"]["evidenceKeys"] == ["ev-applicability"] for scope in scopes)
        assert len(proposal["conditionDefinitions"]) == 1
        subject = proposal["conditionDefinitions"][0]["subject"]
        assert subject["modelOrSeries"]["value"] == "GFC 500 and GSA 28"
        assert subject["stcNumber"]["value"] == "SA01866WI"
        assert subject["attributeKey"] == "master-drawing"
        assert len(proposal["applicabilityRules"]) == 1
        assert {item["requirementKey"] for item in requirements} == {
            "req-software-update", "req-installation-prohibition"
        }
        prohibition = next(item for item in requirements if item["requirementKey"] == "req-installation-prohibition")
        assert prohibition["branch"]["kind"] == "required"
        assert prohibition["activationExpression"]["nodeType"] == "predicate_ref"
    elif packet_key == "2011-10-09":
        assert len(scopes) == 1 and len(models) == len(set(models)) == 224
        assert "172S" not in models and scopes[0]["serialScope"]["kind"] == "all"
        assert len(requirements) == 10 and all(item["recurrenceGroupKey"] == "recurrence-seat-rail" for item in requirements)
        assert requirements[0]["prerequisiteRequirementKeys"] == []
        assert [item["prerequisiteRequirementKeys"] for item in requirements[1:]] == [[f"req-g{i}"] for i in range(1, 10)]
        assert [item["action"]["orderedSteps"][0] for item in requirements] == [
            "inspect-rail-debris", "remove-seat", "inspect-locking-pin-holes",
            "inspect-rollers-and-washers", "inspect-tang-thickness", "inspect-tang-length",
            "inspect-lock-pin-springs", "inspect-seat-rails-for-cracks", "reinstall-seat",
            "inspect-locking-pin-engagement",
        ]
        assert all(item["terminatingEffect"]["kind"] == "none" for item in requirements)
        group = proposal["recurrenceGroups"][0]
        assert group["completionPolicy"] == "all_active_requirements"
        assert set(group["requirementKeys"]) == {item["requirementKey"] for item in requirements}
        assert [term["interval"] for term in group["initialTiming"]["terms"]] == ["100", "12"]
        assert group["initialTiming"]["logic"] == group["recurringTiming"]["logic"] == "whichever_first"
        assert group["initialTiming"]["terms"][0]["anchor"] == "source_defined"
        assert {term["anchor"] for term in group["recurringTiming"]["terms"]} == {"last_compliance"}
        assert proposal["supersessionRelations"][0]["predecessorAdNumber"] == "87-20-03-r2"
    elif packet_key == "2002-13-04":
        assert len(scopes) == 1 and set(models) == {"C-125", "C145", "O-300", "IO-360", "TSIO-360", "LTSIO-520-AE"}
        serial = scopes[0]["serialScope"]
        assert serial["kind"] == "unknown" and serial["reason"] == "conflicting_evidence"
        assert set(serial["evidenceKeys"]) == {"ev-applicability-conflict", "ev-action-range"}
        conditions = {item["conditionKey"]: item for item in proposal["conditionDefinitions"]}
        assert set(conditions) == {"condition-magneto-installed", "condition-pin-missing", "condition-family-a", "condition-family-b"}
        family_a = set(conditions["condition-family-a"]["subject"]["modelOrSeries"]["value"].split(","))
        family_b = set(conditions["condition-family-b"]["subject"]["modelOrSeries"]["value"].split(","))
        assert family_a.isdisjoint(family_b)
        branch_conditions = {item["branch"].get("conditionExpression", {}).get("conditionKey") for item in requirements}
        assert {"condition-family-a", "condition-family-b"} <= branch_conditions
        assert any(item["requirementType"] == "installation_prohibition" for item in requirements)
        hint = proposal["applicabilitySearchHints"][0]
        assert hint["controlling"] is False and hint["exhaustive"] is False
        assert "hint-airframes" not in canonical_bytes(proposal["applicabilityRules"]).decode()
    elif packet_key == "1998-17-11":
        assert len(scopes) == 2 and len(models) == 81
        assert all(len(items := scope["modelScope"]["sourceDesignations"]) == len(set(items)) for scope in scopes)
        assert {scope["productRole"] for scope in scopes} == {"engine"}
        conditions = {item["conditionKey"]: item for item in proposal["conditionDefinitions"]}
        assert conditions["condition-provenance-unknown"]["subject"]["attributeValue"]["value"] == "unknown_requires_compliance"
        assert set(conditions["condition-provenance"]["evidenceKeys"]) == {
            "ev-work-orders-a", "ev-work-orders-b", "ev-work-orders-c", "ev-work-orders-d", "ev-work-orders-e"
        }
        condition_expression = proposal["applicabilityRules"][0]["conditionExpression"]
        assert condition_expression["nodeType"] == "any"
        assert {item["conditionKey"] for item in condition_expression["operands"]} == {
            "condition-provenance", "condition-provenance-unknown"
        }
        assert sum(item["branch"]["kind"] == "alternative_member" for item in requirements) == 2
        assert any(item["branch"]["kind"] == "conditional" for item in requirements)
        rework = next(item for item in requirements if item["requirementKey"] == "req-approved-rework")
        assert rework["requirementType"] == "other_reviewed"
        assert rework["action"]["actionType"] == "rework"
        assert rework["action"]["approvedDataDocumentRefKeys"] == ["doc-approved-rework-data"]
        assert not any("workOrder" in item or "engineSerial" in item for item in requirements)
    elif packet_key == "2008-26-10":
        assert len(scopes) == 1 and len(models) == len(set(models)) == 182 and "188" not in models
        assert {item["documentRole"] for item in proposal["officialDocuments"]} == {"ad_rule", "official_correction"}
        assert len(proposal["incorporatedDocuments"]) == 4
        assert all(item["retention"]["state"] == "unknown" and item["retention"]["reason"] == "not_obtained" for item in proposal["incorporatedDocuments"])
        assert len(requirements) == 6
        expression = proposal["applicabilityRules"][0]["conditionExpression"]
        assert expression["nodeType"] == "all"
        assert expression["operands"][0]["nodeType"] == "any"
        assert expression["operands"][1] == {
            "nodeType": "not", "operand": {"nodeType": "predicate_ref", "conditionKey": "condition-exception"}
        }
        by_key = {item["requirementKey"]: item for item in requirements}
        assert by_key["req-non-ifr"]["activationExpression"]["operands"][1]["nodeType"] == "not"
        assert by_key["req-ifr-inspect"]["activationExpression"]["operands"][1]["conditionKey"] == "condition-ifr"
        assert by_key["req-ifr-placard"]["branch"]["alternativeGroupKey"] == "alternative-ifr-initial"
        timing_logic = {item["initialTiming"].get("logic") for item in requirements if "logic" in item["initialTiming"]}
        assert {"whichever_first", "whichever_later"} <= timing_logic
        assert by_key["req-report"]["action"]["orderedSteps"] == ["report-to-corrected-1801-airport-road"]
        assert by_key["req-report"]["action"]["evidenceKeys"] == ["ev-report", "ev-correction-b"]
        correction = proposal["authoritativeCorrections"][0]
        assert correction["originalDocumentRefKey"] == "official-rule"
        assert correction["correctingDocumentRefKey"] == "official-correction"
        assert set(correction["evidenceKeys"]) == {"ev-correction-a", "ev-correction-b"}
        assert len(proposal["amocAuthorityProvisions"]) == 1
        assert set(proposal["amocAuthorityProvisions"][0]) == {
            "provisionKey", "approvingAuthority", "evidenceKeys"
        }
    else:
        raise AssertionError(packet_key)


@pytest.mark.parametrize("packet", SOURCES["packets"], ids=lambda packet: packet["packet"])
def test_source_complete_executable_calibration_packet(packet):
    source_root = _source_root()
    extracted_pages: list[dict] = []
    for document in packet["documents"]:
        path = source_root / document["relativePath"]
        payload = path.read_bytes()
        assert len(payload) == int(document["byteLength"])
        assert hashlib.sha256(payload).hexdigest() == document["sha256"]
        reader = PdfReader(path)
        assert len(reader.pages) == int(document["pageCount"])
        document_pages = []
        for page_number, page in enumerate(reader.pages, start=1):
            text = (page.extract_text() or "").strip()
            if text:
                document_pages.append({
                    "sourceDocumentId": document["logicalKey"],
                    "contentHash": document["sha256"],
                    "pageNumber": page_number,
                    "text": text,
                })
        if int(document["pageCount"]) > 50:
            document_pages = bounded_issue_pages(document_pages, ad_number=packet["adNumber"], title="")
        extracted_pages.extend(document_pages)
    bounded_pages = bounded_source_document_pages(extracted_pages, ad_number=packet["adNumber"], title="")
    source_pages = {
        (str(page["sourceDocumentId"]), str(page["pageNumber"])): str(page["text"])
        for page in bounded_pages
    }

    fragments = _packet_fragments(packet["packet"])
    assert fragments
    for fragment in fragments.values():
        page = source_pages[(fragment["sourceKey"], fragment["pageNumber"])]
        assert hashlib.sha256(page.encode()).hexdigest() == fragment["pageTextHash"]
        start = int(fragment["characterStart"])
        end = int(fragment["characterEnd"])
        exact = page[start:end]
        assert exact.strip()
        assert hashlib.sha256(exact.encode()).hexdigest() == fragment["exactTextHash"]
        selection = fragment["selection"]
        assert exact.startswith(selection["startAnchor"])
        if selection["endAnchor"] is not None:
            assert page[end:].startswith(selection["endAnchor"])
        assert start > 0 or end < len(page), "page-wide evidence is not clause-narrow"
        assert len(fragment["locators"]) == 1
        assert fragment["claimKinds"]
        assert fragment["fragmentHashInputs"][-3:] == ["exactText", "parserName", "parserVersion"]

    template = _load_template(packet)
    assert set(template["proposal"]["evidenceBindings"]) == set(fragments)
    serialized = json.dumps(template["proposal"], ensure_ascii=False)
    assert not any(source_pages[key] in serialized for key in source_pages)
    executable = _executable(packet, template)
    parsed = parse_v4_request_bytes(json.dumps(executable, ensure_ascii=False, separators=(",", ":")).encode())
    validated, relationships = validate_v4_envelope(parsed, "ad-" + packet["packet"])
    assert relationships == []
    assert canonical_bytes(validated) == canonical_bytes(json.loads(canonical_bytes(validated)))
    _assert_packet_contract(packet["packet"], executable)
    _assert_claim_by_claim_evidence(packet["packet"], executable["proposal"])
    expected = packet["expectedSemantics"]
    proposal = executable["proposal"]
    if "models" in expected:
        assert len(_all_models(proposal)) == int(expected["models"])
    if "requirements" in expected:
        assert len(proposal["requirements"]) == int(expected["requirements"])
    if "conditions" in expected:
        assert len(proposal["conditionDefinitions"]) == int(expected["conditions"])
    cases = packet["expectedCases"]
    assert {item["polarity"] for item in cases} == {"positive", "negative"}
    positive = next(item for item in cases if item["polarity"] == "positive")
    assert positive["model"] in _all_models(proposal)
    for case in cases:
        if case["expected"] == "not_listed":
            assert case["model"] not in _all_models(proposal)


@pytest.mark.parametrize("packet", SOURCES["packets"], ids=lambda packet: packet["packet"])
def test_calibration_packet_uses_real_admitted_evidence_and_persists_candidate(
    packet,
    db_session,
    tmp_path,
    monkeypatch,
):
    """Prove each portable packet crosses the Slice-1/Slice-2 trust boundary."""

    storage_root = tmp_path / "retained-evidence"
    monkeypatch.setenv("PAPRNAV_LOCAL_STORAGE_PATH", str(storage_root))
    get_settings.cache_clear()
    actor = create_user(db_session, f"cal-{packet['packet']}@example.test", "Calibration Admin")
    organization = create_organization(db_session, f"Calibration {packet['packet']}", "platform")
    membership = add_membership(db_session, organization, actor, "platform_admin")
    directive = AirworthinessDirective(
        ad_number=packet["adNumber"],
        title="",
        status="candidate",
        source_content_hash=packet["documents"][0]["sha256"],
    )
    db_session.add(directive)
    db_session.flush()
    retained = _retain_packet_sources(db_session, packet, directive, storage_root)
    db_session.expire(directive, ["publications"])

    admitted: dict[str, object] = {}
    for item in _packet_fragments(packet["packet"]).values():
        document = retained[item["sourceKey"]]
        locators = item.get("locators", {})
        fragment, created = admit_evidence_fragment(
            db_session,
            directive_id=directive.id,
            source_document_id=document.id,
            page_number=int(item["pageNumber"]),
            expected_source_content_hash=document.content_hash,
            expected_page_text_hash=item["pageTextHash"],
            character_start=int(item["characterStart"]),
            character_end=int(item["characterEnd"]),
            actor=actor,
            reason=f"source-accounted V4 calibration {packet['packet']}",
            paragraph_locator=locators.get("paragraph"),
            table_locator=locators.get("table"),
            row_locator=locators.get("row"),
            note_locator=locators.get("note"),
        )
        assert created is True
        admitted[item["evidenceKey"]] = fragment

    cache = db_session.info["paprnav_ad_evidence_bounded_page_cache"]
    index_entries = [(key, value) for key, value in cache.items() if key[0] == "index"]
    assert len(index_entries) == 1
    (_, base_key), bounded_identity_hash = index_entries[0]
    assert base_key[1] == pypdf.__version__
    assert {identity[1] for identity in base_key[5]} == {
        source["sha256"] for source in packet["documents"]
    }
    assert cache[(base_key, bounded_identity_hash)]
    assert len(bounded_identity_hash) == 64

    executable = _executable(
        packet,
        _load_template(packet),
        admitted_fragments=admitted,
        retained_documents=retained,
        directive_id=directive.id,
    )
    raw = json.dumps(executable, ensure_ascii=False, separators=(",", ":")).encode()
    stored = store_v4_candidate(
        db_session,
        directive_id=directive.id,
        parsed=parse_v4_request_bytes(raw),
        actor=actor,
        membership_id=membership.id,
        idempotency_key=f"calibration-{packet['packet']}",
    )
    db_session.commit()

    assert stored.proposal.gate == "candidate_only"
    assert db_session.query(ADV4CandidateProposal).count() == 1
    assert db_session.query(ADV4CandidateSubmission).count() == 1
    assert db_session.query(ADEvidenceFragmentLifecycleEvent).count() == len(admitted)
    assert stored.proposal.binding_count == len(admitted)


@pytest.mark.parametrize("packet", SOURCES["packets"], ids=lambda packet: packet["packet"])
def test_calibration_packet_rejects_required_negative(packet):
    envelope = _executable(packet, _load_template(packet))
    proposal = envelope["proposal"]
    key = packet["packet"]
    if key == "2024-14-03":
        proposal["conditionDefinitions"][0]["subject"]["modelOrSeries"]["value"] = "GFC 500"
    elif key == "2011-10-09":
        proposal["productScopes"][0]["modelScope"]["sourceDesignations"].append("172S")
    elif key == "2002-13-04":
        proposal["productScopes"][0]["serialScope"] = {
            "kind": "ranges",
            "ranges": [{
                "lower": "99110001",
                "upper": "99129999",
                "lowerInclusive": True,
                "upperInclusive": True,
                "polarity": "included",
            }],
            "evidenceKeys": ["ev-applicability-conflict", "ev-action-range"],
        }
    elif key == "1998-17-11":
        proposal["conditionDefinitions"][1]["subject"]["attributeValue"]["value"] = "not_applicable"
    elif key == "2008-26-10":
        proposal["productScopes"][0]["modelScope"]["sourceDesignations"].append("188")

    raw = json.dumps(envelope, ensure_ascii=False, separators=(",", ":")).encode()
    parsed = parse_v4_request_bytes(raw)
    validated, relationships = validate_v4_envelope(parsed, "ad-" + key)
    assert relationships == []
    assert canonical_bytes(validated) == canonical_bytes(parsed.value["proposal"])
    with pytest.raises(ADV4Error) as error:
        _calibration_admission_oracle(key, parsed.value)
    assert error.value.code == "calibration_semantic_mismatch"
    assert error.value.pointer == "/proposal"


@pytest.mark.parametrize("packet", SOURCES["packets"], ids=lambda packet: packet["packet"])
def test_structurally_invalid_calibration_mutation_is_rejected_by_real_validator(packet):
    envelope = _executable(packet, _load_template(packet))
    envelope["proposal"]["requirements"][0]["sequence"] = "0"
    parsed = parse_v4_request_bytes(
        json.dumps(envelope, ensure_ascii=False, separators=(",", ":")).encode()
    )
    with pytest.raises(ADV4Error) as error:
        validate_v4_envelope(parsed, "ad-" + packet["packet"])
    assert error.value.code == "schema_validation"
