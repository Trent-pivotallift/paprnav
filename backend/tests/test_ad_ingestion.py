from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Session

from app.models.core import (
    ADCoverageSet,
    ADCoverageSubscription,
    ADDiscoveryRecord,
    ADExtraction,
    ADExtractionReview,
    ADExtractionReviewDecision,
    ADTargetApplicability,
    AirworthinessDirective,
    ProductEvent,
    ADPublication,
    ADSourceDocument,
)
from app.core.config import get_settings
from app.services.ad_discovery import FederalRegisterSearchResult, discover_federal_register_ads
from app.services.ad_extraction import AD_EXTRACTION_JSON_SCHEMA, process_pending_ad_extractions
from app.services.ad_extraction import derive_compliance_action_summaries
from app.services.ad_extraction import validate_extraction_output
from app.services.ad_extraction import (
    bounded_issue_pages,
    bounded_source_document_pages,
    extraction_approval_blockers,
    extraction_input_hash,
    full_text_pages_for_directive,
    full_text_pages_for_extraction,
    official_ad_number,
    persisted_source_pages,
    retained_pdf_documents,
    source_evidence_status,
    validate_extraction_json_schema,
    validate_requirement_evidence,
    verified_retained_document_bytes,
)
from app.api.routes.ads import match_has_signed_materialization_chain, serialize_review
from app.services.ad_matching import match_aircraft_ads
from app.scripts.correct_approved_ad_review import supersede_amoc_provisions_statement
from app.scripts.stage_ad_review_proposal import (
    main as stage_review_proposal_main,
    stage_review_proposal,
    visual_ocr_validation_shadow,
)
from tests.conftest import (
    add_membership,
    create_organization,
    create_user,
    login,
)


class FakeFederalRegisterClient:
    def search_airworthiness_directive_candidates(
        self,
        page: int = 1,
        per_page: int = 20,
        term: str = "Airworthiness Directives",
    ) -> FederalRegisterSearchResult:
        _ = page
        _ = per_page
        _ = term
        return FederalRegisterSearchResult(
            description="Federal Aviation Administration Rule documents matching Airworthiness Directives",
            count=2,
            total_pages=1,
            next_page_url=None,
            results=[candidate_document(), non_ad_rule_document()],
            raw_response={"results": [candidate_document(), non_ad_rule_document()]},
        )


def test_v3_schema_requires_page_citations_for_each_requirement() -> None:
    output = provider_output()
    output.pop("confidence")
    output.pop("citations")
    output.pop("uncertaintyReasons")
    output["requirements"] = [{
        "requirementKey": "inspection",
        "applicabilityGroupKeys": ["airbus-as350"],
        "requirementType": "recurring",
        "actionText": "Inspect the affected part.",
        "initialThresholds": [],
        "recurringTriggers": [{"metric": "tach_hours", "value": 100, "unit": "hours", "anchorKind": "last_compliance", "sourceText": "every 100 hours"}],
        "combinationLogic": "all",
        "conditions": [],
        "terminatingAction": None,
        "citations": [],
        "confidence": 0.9,
        "uncertaintyReasons": [],
    }]

    try:
        validate_extraction_output(output)
    except ValueError as exc:
        assert "page citations" in str(exc)
    else:
        raise AssertionError("uncited v2 requirement was accepted")


def test_v3_schema_accepts_installation_prohibition_requirement() -> None:
    output = provider_output()
    output["requirements"] = [{
        "requirementKey": "replacement-part-installation",
        "applicabilityGroupKeys": ["airbus-as350"],
        "requirementType": "installation_prohibition",
        "actionText": "Install only a replacement part that passed inspection.",
        "initialThresholds": [],
        "recurringTriggers": [],
        "combinationLogic": "all",
        "conditions": ["A replacement part is installed."],
        "terminatingAction": None,
        "citations": [{
            "sourceDocumentId": "asd_example",
            "pageNumber": 2,
            "text": "Only install a replacement part that passed inspection.",
        }],
        "confidence": 0.95,
        "uncertaintyReasons": [],
    }]

    validate_extraction_output(output, require_v2_requirements=True)


def test_v2_compliance_actions_are_derived_from_requirement_objects() -> None:
    output = provider_output()
    output["complianceActions"] = []
    output["requirements"] = [
        {"actionText": "Inspect the impulse coupling stop pin."},
        {"actionText": "Replace a missing stop pin."},
        {"actionText": "Inspect the impulse coupling stop pin."},
    ]

    normalized = derive_compliance_action_summaries(output)

    assert normalized["complianceActions"] == [
        "Inspect the impulse coupling stop pin.",
        "Replace a missing stop pin.",
    ]
    assert output["complianceActions"] == []


def test_requirement_evidence_rejects_paraphrased_action_text() -> None:
    source_pages = [{
        "sourceDocumentId": "asd_source",
        "pageNumber": 5,
        "text": "Within 12 months, update the software to a version that is not 8.01 or earlier.",
    }]
    output = {"requirements": [{
        "actionText": "Install a software version later than 8.01.",
        "citations": [{
            "sourceDocumentId": "asd_source",
            "pageNumber": 5,
            "text": "Within 12 months, update the software to a version that is not 8.01 or earlier.",
        }],
    }]}

    try:
        validate_requirement_evidence(output, source_pages)
    except ValueError as exc:
        assert "preserve wording" in str(exc)
    else:
        raise AssertionError("paraphrased actionText was accepted")


def test_requirement_evidence_accepts_source_wording_with_pdf_typography_changes() -> None:
    source_pages = [{
        "sourceDocumentId": "asd_source",
        "pageNumber": 5,
        "text": "Do not install auto-\npilot software in the pilot’s airplane.",
    }]
    action = "Do not install autopilot software in the pilot's airplane."

    validate_requirement_evidence(
        {"requirements": [{
            "actionText": action,
            "citations": [{
                "sourceDocumentId": "asd_source",
                "pageNumber": 5,
                "text": action,
            }],
        }]},
        source_pages,
    )


def test_requirement_evidence_accepts_source_wording_assembled_from_ordered_citations() -> None:
    source_pages = [{
        "sourceDocumentId": "asd_source",
        "pageNumber": 8,
        "text": "(i) Replace the worn component. (ii) Continue the repetitive inspections.",
    }]

    validate_requirement_evidence(
        {"requirements": [{
            "actionText": "Replace the worn component. Continue the repetitive inspections.",
            "citations": [{
                "sourceDocumentId": "asd_source",
                "pageNumber": 8,
                "text": "Replace the worn component.",
            }, {
                "sourceDocumentId": "asd_source",
                "pageNumber": 8,
                "text": "Continue the repetitive inspections.",
            }],
        }]},
        source_pages,
    )


def test_requirement_evidence_rejects_hallucinated_threshold_value() -> None:
    source_text = "Inspect the part within 10 hours after the effective date."
    source_pages = [{
        "sourceDocumentId": "asd_source",
        "pageNumber": 3,
        "text": source_text,
    }]
    output = {"requirements": [{
        "actionText": source_text,
        "initialThresholds": [{
            "metric": "total_time_hours",
            "value": 100,
            "unit": "hours",
            "anchorKind": "effective_date",
            "sourceText": source_text,
        }],
        "recurringTriggers": [],
        "terminatingAction": None,
        "citations": [{
            "sourceDocumentId": "asd_source",
            "pageNumber": 3,
            "text": source_text,
        }],
    }]}

    try:
        validate_requirement_evidence(output, source_pages)
    except ValueError as exc:
        assert "value is not present" in str(exc)
    else:
        raise AssertionError("unsupported threshold value was accepted")


def test_amoc_authority_text_must_be_source_cited() -> None:
    source_pages = [{
        "sourceDocumentId": "asd_source",
        "pageNumber": 9,
        "text": "The Manager, New York ACO Branch, FAA, has the authority to approve AMOCs for this AD.",
    }]
    output = {
        "requirements": [],
        "amocProvisions": [{
            "authorityText": "Any mechanic may approve an AMOC.",
            "citations": [{
                "sourceDocumentId": "asd_source",
                "pageNumber": 9,
                "text": source_pages[0]["text"],
            }],
        }],
    }

    try:
        validate_requirement_evidence(output, source_pages)
    except ValueError as exc:
        assert "authorityText must preserve wording" in str(exc)
    else:
        raise AssertionError("uncited AMOC authority was accepted")


def test_applicability_identity_and_serial_scope_must_be_source_cited() -> None:
    cited = "This AD applies to Cessna Model 172R airplanes, serial numbers 17280001 through 17280099."
    source_pages = [{
        "sourceDocumentId": "asd_source",
        "pageNumber": 1,
        "text": cited,
    }]
    group = v3_applicability_group(
        source_document_id="asd_source",
        citation_text=cited,
        manufacturer="Cessna",
        model="172R",
        group_key="cessna-172r",
    )
    group["serialNumberApplicability"] = {
        "kind": "ranges",
        "values": [],
        "ranges": [{"start": "17280001", "end": "17280999"}],
        "excludedValues": [],
        "sourceText": cited,
    }

    try:
        validate_requirement_evidence(
            {"applicabilityGroups": [group], "requirements": [], "amocProvisions": []},
            source_pages,
        )
    except ValueError as exc:
        assert "serial range endpoint" in str(exc)
    else:
        raise AssertionError("hallucinated serial endpoint was accepted")


def test_applicability_rejects_unreviewed_normalized_identity_override() -> None:
    cited = "This AD applies to Lycoming Model O-320 engines, all serial numbers."
    source_pages = [{
        "sourceDocumentId": "asd_source",
        "pageNumber": 1,
        "text": cited,
    }]
    group = v3_applicability_group(
        source_document_id="asd_source",
        citation_text=cited,
        manufacturer="Lycoming",
        model="O-320",
        group_key="lycoming-o-320",
    )
    group["productType"] = "engine"
    group["manufacturer"]["normalizedName"] = "Continental Motors"

    with pytest.raises(ValueError, match="reviewed canonical identity mapping"):
        validate_requirement_evidence(
            {"applicabilityGroups": [group], "requirements": [], "amocProvisions": []},
            source_pages,
        )
    group["manufacturer"]["normalizedName"] = "Lycoming"
    group["modelApplicability"]["models"][0]["normalizedDesignation"] = "IO-360"
    with pytest.raises(ValueError, match="normalizedDesignation"):
        validate_requirement_evidence(
            {"applicabilityGroups": [group], "requirements": [], "amocProvisions": []},
            source_pages,
        )


def test_applicability_scope_kind_cannot_broaden_cited_scope() -> None:
    cited = "This AD applies to Cessna Model 172R airplanes, serial numbers 1 through 10."
    source_pages = [{"sourceDocumentId": "asd_source", "pageNumber": 1, "text": cited}]
    group = v3_applicability_group(
        source_document_id="asd_source",
        citation_text=cited,
        manufacturer="Cessna",
        model="172R",
        group_key="cessna-172r",
    )
    group["modelApplicability"] = {
        "kind": "all", "models": [], "sourceText": "Cessna Model 172R airplanes",
    }
    with pytest.raises(ValueError, match="all-model scope"):
        validate_requirement_evidence(
            {"applicabilityGroups": [group], "requirements": [], "amocProvisions": []},
            source_pages,
        )

    group["modelApplicability"] = {
        "kind": "listed",
        "models": [{"sourceDesignation": "172R", "normalizedDesignation": None, "aliases": []}],
        "sourceText": "Cessna Model 172R airplanes",
    }
    group["serialNumberApplicability"] = {
        "kind": "all", "values": [], "ranges": [], "excludedValues": [],
        "sourceText": "serial numbers 1 through 10",
    }
    with pytest.raises(ValueError, match="all-serial scope"):
        validate_requirement_evidence(
            {"applicabilityGroups": [group], "requirements": [], "amocProvisions": []},
            source_pages,
        )


def test_requirement_timing_and_combination_semantics_are_source_bound() -> None:
    cited = "Inspect within 10 hours after installation, whichever occurs first."
    source_pages = [{"sourceDocumentId": "asd_source", "pageNumber": 1, "text": cited}]
    requirement = {
        "requirementType": "one_time",
        "actionText": cited,
        "initialThresholds": [{
            "metric": "total_time_hours", "value": 10, "unit": "hours",
            "anchorKind": "effective_date", "sourceText": cited,
        }],
        "recurringTriggers": [], "combinationLogic": "whichever_first",
        "conditions": [], "terminatingAction": None,
        "citations": [{"sourceDocumentId": "asd_source", "pageNumber": 1, "text": cited}],
    }
    with pytest.raises(ValueError, match="anchorKind"):
        validate_requirement_evidence(
            {"requirements": [requirement], "amocProvisions": []}, source_pages,
        )
    requirement["initialThresholds"][0]["anchorKind"] = "installation"
    requirement["combinationLogic"] = "whichever_later"
    with pytest.raises(ValueError, match="whichever_later"):
        validate_requirement_evidence(
            {"requirements": [requirement], "amocProvisions": []}, source_pages,
        )


def test_requirement_condition_and_product_type_are_source_bound() -> None:
    cited = "This AD applies to Cessna Model 172R airplanes. Inspect the seat rail."
    source_pages = [{"sourceDocumentId": "asd_source", "pageNumber": 1, "text": cited}]
    group = v3_applicability_group(
        source_document_id="asd_source", citation_text=cited,
        manufacturer="Cessna", model="172R", group_key="cessna-172r",
    )
    group["productType"] = "engine"
    with pytest.raises(ValueError, match="productType"):
        validate_requirement_evidence(
            {"applicabilityGroups": [group], "requirements": [], "amocProvisions": []},
            source_pages,
        )

    requirement = {
        "requirementType": "conditional", "actionText": "Inspect the seat rail.",
        "initialThresholds": [], "recurringTriggers": [], "combinationLogic": "all",
        "conditions": ["Only when floats are installed."], "terminatingAction": None,
        "citations": [{"sourceDocumentId": "asd_source", "pageNumber": 1, "text": cited}],
    }
    with pytest.raises(ValueError, match="condition 0"):
        validate_requirement_evidence(
            {"requirements": [requirement], "amocProvisions": []}, source_pages,
        )

def test_reviewed_dates_must_be_present_in_retained_source() -> None:
    source_pages = [{
        "sourceDocumentId": "asd_source", "pageNumber": 1,
        "text": "This amendment becomes effective on August 30, 2026.",
    }]
    with pytest.raises(ValueError, match="effectiveDate"):
        validate_requirement_evidence(
            {"effectiveDate": "2026-09-30", "requirements": [], "amocProvisions": []},
            source_pages,
        )
    validate_requirement_evidence(
        {"effectiveDate": "2026-08-30", "requirements": [], "amocProvisions": []},
        source_pages,
    )

def test_amoc_authority_details_and_conditions_must_be_source_cited() -> None:
    cited = "The Manager, New York ACO Branch, may approve AMOCs submitted through the principal inspector."
    source_pages = [{
        "sourceDocumentId": "asd_source",
        "pageNumber": 9,
        "text": cited,
    }]
    provision = {
        "authorityText": cited,
        "approvingAuthority": "New York ACO Branch",
        "submissionInstructions": "Submit through an unrelated office.",
        "conditions": [],
        "citations": [{
            "sourceDocumentId": "asd_source",
            "pageNumber": 9,
            "text": cited,
        }],
    }

    try:
        validate_requirement_evidence(
            {"requirements": [], "amocProvisions": [provision]},
            source_pages,
        )
    except ValueError as exc:
        assert "submissionInstructions" in str(exc)
    else:
        raise AssertionError("uncited AMOC submission instruction was accepted")


def test_requirement_uncertainty_blocks_approval() -> None:
    extraction = SimpleNamespace(
        schema_version="ad_extraction_v3",
        directive=SimpleNamespace(ad_number="2026-12-01", title="Example AD"),
    )
    source_pages = [{
        "sourceDocumentId": "asd_source",
        "pageNumber": 1,
        "text": (
            "Federal Register, June 16, 2026.\n14 CFR Part 39\n"
            "Section 39.13 is amended by adding the following new "
            "airworthiness directive: AD 2026-12-01. This AD applies to Airbus "
            "Helicopters Model AS350, all serial numbers. Inspect the seat rail."
        ),
    }]
    output = provider_output()
    output["applicabilityGroups"][0]["citations"] = [{
        "sourceDocumentId": "asd_source",
        "pageNumber": 1,
        "text": "This AD applies to Airbus Helicopters Model AS350, all serial numbers.",
    }]
    output["requirements"] = [{
        "requirementKey": "g-inspection",
        "applicabilityGroupKeys": ["airbus-as350"],
        "requirementType": "one_time",
        "actionText": "Inspect the seat rail.",
        "initialThresholds": [],
        "recurringTriggers": [],
        "combinationLogic": "all",
        "conditions": [],
        "terminatingAction": None,
        "citations": [{
            "sourceDocumentId": "asd_source",
            "pageNumber": 1,
            "text": "Inspect the seat rail.",
        }],
        "confidence": 0.8,
        "uncertaintyReasons": ["Confirm whether paragraph (g)(2) is a separate requirement."],
    }]

    blockers = extraction_approval_blockers(extraction, output, source_pages)

    assert blockers == ["Resolve 1 requirement uncertainty reason(s) before approval."]


def test_v3_provider_schema_closes_and_requires_every_object_field() -> None:
    def assert_strict_objects(node: Any) -> None:
        if isinstance(node, dict):
            if node.get("type") == "object":
                assert node.get("additionalProperties") is False
                assert set(node.get("required") or []) == set((node.get("properties") or {}).keys())
            for value in node.values():
                assert_strict_objects(value)
        elif isinstance(node, list):
            for value in node:
                assert_strict_objects(value)

    assert_strict_objects(AD_EXTRACTION_JSON_SCHEMA)


def test_operational_v3_schema_rejects_partial_extra_nested_and_nonfinite_values() -> None:
    output = provider_output()
    validate_extraction_json_schema(output)

    missing = dict(output)
    missing.pop("confidence")
    with pytest.raises(ValueError, match="missing required properties: confidence"):
        validate_extraction_json_schema(missing)

    extra = dict(output)
    extra["unsupported"] = True
    with pytest.raises(ValueError, match="unsupported properties: unsupported"):
        validate_extraction_json_schema(extra)

    nested = provider_output()
    nested["applicabilityGroups"][0]["manufacturer"]["unsupported"] = "value"
    with pytest.raises(ValueError, match="unsupported properties: unsupported"):
        validate_extraction_json_schema(nested)

    invalid_confidence = provider_output()
    invalid_confidence["confidence"] = 2
    with pytest.raises(ValueError, match="must be at most 1"):
        validate_extraction_json_schema(invalid_confidence)

    nonfinite = provider_output()
    nonfinite["confidence"] = float("nan")
    with pytest.raises(ValueError, match="must be number"):
        validate_extraction_json_schema(nonfinite)


def test_retained_pdf_text_preserves_document_and_page_identity(tmp_path, monkeypatch) -> None:
    from reportlab.pdfgen import canvas

    pdf_path = tmp_path / "source.pdf"
    writer = canvas.Canvas(str(pdf_path))
    writer.drawString(72, 720, "Compliance: inspect within 100 hours.")
    writer.showPage()
    writer.drawString(72, 720, "Thereafter inspect every 50 hours.")
    writer.save()
    pdf_bytes = pdf_path.read_bytes()
    document = SimpleNamespace(
        id="asd_retained",
        media_type="application/pdf",
        storage_backend="local",
        storage_key="source.pdf",
        content_hash=hashlib.sha256(pdf_bytes).hexdigest(),
        storage_bytes=len(pdf_bytes),
    )
    directive = SimpleNamespace(
        publications=[SimpleNamespace(source_document=document)],
        source_content_hash="b" * 64,
    )
    monkeypatch.setattr(
        "app.services.ad_extraction.get_settings",
        lambda: SimpleNamespace(
            local_storage_path=str(tmp_path),
            storage_backend="local",
            ad_extraction_provider="deterministic",
            openai_api_key=None,
        ),
    )

    pages = full_text_pages_for_directive(directive)

    assert [(page["sourceDocumentId"], page["pageNumber"]) for page in pages] == [
        ("asd_retained", 1),
        ("asd_retained", 2),
    ]
    assert "inspect within 100 hours" in pages[0]["text"]
    assert extraction_input_hash(directive) != directive.source_content_hash


def test_cached_source_pages_are_rejected_after_retained_bytes_change(
    tmp_path,
    monkeypatch,
) -> None:
    from reportlab.pdfgen import canvas

    source_path = tmp_path / "source.pdf"
    writer = canvas.Canvas(str(source_path))
    writer.drawString(72, 720, "original retained evidence")
    writer.showPage()
    writer.drawString(72, 720, "later compliance exception")
    writer.save()
    original = source_path.read_bytes()
    content_hash = hashlib.sha256(original).hexdigest()
    document = SimpleNamespace(
        id="asd_retained",
        media_type="application/pdf",
        source_system="federal_register",
        source_type="rule_pdf",
        storage_backend="local",
        storage_key="source.pdf",
        content_hash=content_hash,
        storage_bytes=len(original),
    )
    directive = SimpleNamespace(
        publications=[SimpleNamespace(source_document=document)],
    )
    extraction = SimpleNamespace(raw_response={
        "retainedSourcePagesCached": True,
        "retainedSourcePages": [{
            "sourceDocumentId": document.id,
            "contentHash": content_hash,
            "pageNumber": 1,
            "text": "original retained evidence",
        }, {
            "sourceDocumentId": document.id,
            "contentHash": content_hash,
            "pageNumber": 2,
            "text": "later compliance exception",
        }],
    })
    monkeypatch.setattr(
        "app.services.ad_extraction.get_settings",
        lambda: SimpleNamespace(local_storage_path=str(tmp_path)),
    )

    assert persisted_source_pages(directive, extraction)[0] is True
    omitted_page = extraction.raw_response["retainedSourcePages"].pop()
    assert persisted_source_pages(directive, extraction) == (False, [])
    extraction.raw_response["retainedSourcePages"].append(omitted_page)
    extraction.raw_response["retainedSourcePages"][0]["text"] = "invented retained evidence"
    assert persisted_source_pages(directive, extraction) == (False, [])
    extraction.raw_response["retainedSourcePages"][0]["text"] = "original retained evidence"
    source_path.write_bytes(b"%PDF-1.4\ntampered retained evidence\n%%EOF\n")
    assert persisted_source_pages(directive, extraction) == (False, [])


def test_retained_source_set_includes_individual_and_issue_pdfs() -> None:
    def document(document_id: str, source_type: str) -> SimpleNamespace:
        return SimpleNamespace(
            id=document_id, media_type="application/pdf",
            source_system="federal_register", source_type=source_type,
        )

    original = document("asd_original", "document_pdf")
    correction = document("asd_correction_issue", "issue_pdf")
    directive = SimpleNamespace(publications=[
        SimpleNamespace(source_document=original),
        SimpleNamespace(source_document=correction),
    ])
    assert [item.id for item in retained_pdf_documents(directive)] == [
        "asd_original", "asd_correction_issue",
    ]


def test_match_due_state_chain_rejects_cross_extraction_or_stale_state() -> None:
    applicability = SimpleNamespace(
        id="ata_expected", status="current", source_extraction_id="adx_expected",
    )
    requirement = SimpleNamespace(
        status="current", source_extraction_id="adx_other",
        target_applicability_id="ata_expected",
    )
    state = SimpleNamespace(
        id="adu_fixture", is_current=True, aircraft_id="air_fixture",
        installed_component_id="cmp_fixture", requirement=requirement,
    )
    match = SimpleNamespace(
        target_applicability=applicability, extraction_id="adx_expected",
        aircraft_id="air_fixture", installed_component_id="cmp_fixture",
        due_state_links=[SimpleNamespace(due_state=state)], due_state=None,
    )
    assert match_has_signed_materialization_chain(match) is False
    requirement.source_extraction_id = "adx_expected"
    assert match_has_signed_materialization_chain(match) is True
    state.is_current = False
    assert match_has_signed_materialization_chain(match) is False


def test_deterministic_full_text_extraction_always_requires_review(
    db_session: Session,
    tmp_path,
    monkeypatch,
) -> None:
    from datetime import datetime, timezone
    from reportlab.pdfgen import canvas

    discover_federal_register_ads(db_session, client=FakeFederalRegisterClient())
    directive = db_session.scalar(select(AirworthinessDirective))
    pdf_path = tmp_path / "retained.pdf"
    writer = canvas.Canvas(str(pdf_path))
    writer.drawString(72, 720, "Compliance: inspect the affected part every 100 hours.")
    writer.save()
    retained_bytes = pdf_path.read_bytes()
    document = ADSourceDocument(
        source_system="federal_register",
        source_type="rule_pdf",
        source_identifier="fixture-retained-pdf",
        storage_backend="local",
        storage_key="retained.pdf",
        media_type="application/pdf",
        content_hash=hashlib.sha256(retained_bytes).hexdigest(),
        storage_bytes=pdf_path.stat().st_size,
        captured_at=datetime.now(timezone.utc),
        status="retained",
    )
    db_session.add(document)
    db_session.flush()
    db_session.add(ADPublication(
        directive_id=directive.id,
        source_document_id=document.id,
        source_system="federal_register",
        source_type="rule_pdf",
        source_identifier="fixture-retained-publication",
        content_hash=document.content_hash,
        status="retained",
    ))
    db_session.flush()
    monkeypatch.setattr(
        "app.services.ad_extraction.get_settings",
        lambda: SimpleNamespace(
            local_storage_path=str(tmp_path),
            storage_backend="local",
            ad_extraction_provider="deterministic",
            openai_api_key=None,
        ),
    )

    stats = process_pending_ad_extractions(db_session)

    extraction = db_session.scalar(select(ADExtraction))
    assert stats["review_queued"] == 1
    assert extraction.schema_version == "ad_extraction_v3"
    assert extraction.status == "needs_review"
    assert extraction.raw_response["retainedSourcePagesCached"] is True
    assert len(extraction.raw_response["retainedSourcePages"]) == 1
    byte_reads = 0

    def verified_read(**_) -> bytes:
        nonlocal byte_reads
        byte_reads += 1
        return retained_bytes

    monkeypatch.setattr(
        "app.services.ad_extraction.read_stored_file_bytes",
        verified_read,
    )
    assert len(full_text_pages_for_extraction(extraction)) == 1
    assert byte_reads == 1
    document.content_hash = "b" * 64
    db_session.flush()
    assert persisted_source_pages(directive, extraction) == (False, [])
    assert db_session.scalar(select(ADExtractionReview)) is not None


def test_retained_document_verification_never_accepts_a_second_read(
    monkeypatch,
) -> None:
    expected = b"official retained bytes"
    document = SimpleNamespace(
        storage_backend="local",
        storage_key="retained.pdf",
        content_hash=hashlib.sha256(expected).hexdigest(),
        storage_bytes=len(expected),
    )
    payloads = iter([b"tampered first read", expected])
    reads = 0

    def alternating_read(**_) -> bytes:
        nonlocal reads
        reads += 1
        return next(payloads)

    monkeypatch.setattr(
        "app.services.ad_extraction.read_stored_file_bytes",
        alternating_read,
    )

    with pytest.raises(ValueError, match="hash or size mismatch"):
        verified_retained_document_bytes(document, settings=SimpleNamespace())
    assert reads == 1


def test_approved_correction_amoc_revocation_compiles_for_postgresql() -> None:
    statement = supersede_amoc_provisions_statement("adx_fixture")

    compiled = str(statement.compile(dialect=postgresql.dialect()))

    assert "UPDATE ad_amoc_provisions SET status=" in compiled
    assert "review_status" not in compiled


def test_complete_issue_text_is_bounded_to_ad_section() -> None:
    pages = [
        {"pageNumber": 1, "text": "Unrelated FAA rule. [FR Doc. 2026-10000]"},
        {"pageNumber": 2, "text": "14 CFR Part 39\n[Docket No. FAA-2026-1]\nAirworthiness Directive AD 2026-12-01 begins."},
        {"pageNumber": 3, "text": "Compliance actions continue here."},
        {"pageNumber": 4, "text": "Issued in Washington. [FR Doc. 2026-12052]\nAnother unrelated rule."},
        {"pageNumber": 5, "text": "Unrelated appendix."},
    ]

    selected = bounded_issue_pages(pages, ad_number="2026-12-01", title="Affected Part")

    assert [page["pageNumber"] for page in selected] == [2, 3, 4]
    assert "Another unrelated rule" not in selected[-1]["text"]
    assert bounded_issue_pages(pages, ad_number="1999-99-99") == []
    title_selected = bounded_issue_pages(
        pages,
        ad_number="1999-99-99",
        title="Compliance Actions",
    )
    assert [page["pageNumber"] for page in title_selected] == [2, 3, 4]


def test_issue_bounding_fails_closed_without_a_footer() -> None:
    pages = [{
        "pageNumber": 1,
        "text": "14 CFR Part 39\nAD 2026-12-01\nInspect the affected part.",
    }]

    assert bounded_issue_pages(pages, ad_number="2026-12-01") == []


def test_issue_bounding_fails_closed_with_an_ocr_corrupted_footer() -> None:
    pages = [{
        "pageNumber": 1,
        "text": (
            "14 CFR Part 39\nAD 2026-12-01\nInspect the affected part.\n"
            "[F8 D0c 2026-12052 Filed 6-15-26]"
        ),
    }]

    assert bounded_issue_pages(pages, ad_number="2026-12-01") == []


def test_issue_bounding_rejects_a_later_rules_footer() -> None:
    pages = [{
        "pageNumber": 1,
        "text": (
            "14 CFR Part 39\nAD 2026-12-01\nInspect the affected part.\n"
            "14 CFR Part 39\nAD 2026-12-02\nReplace another part.\n"
            "[FR Doc. 2026-12053 Filed 6-15-26]"
        ),
    }]

    assert bounded_issue_pages(pages, ad_number="2026-12-01") == []


def test_issue_bounding_rejects_a_non_part_39_neighbors_footer() -> None:
    pages = [{
        "pageNumber": 1,
        "text": (
            "14 CFR Part 39\nAD 2026-12-01\nInspect the affected part.\n"
            "[F8 D0c 2026-12052 Filed 6-15-26]\n"
            "DEPARTMENT OF AGRICULTURE\nForest Service\n"
            "NeighborCo model N-1 grazing notice.\n"
            "[FR Doc. 2026-12054 Filed 6-15-26]"
        ),
    }]

    assert bounded_issue_pages(pages, ad_number="2026-12-01") == []


def test_issue_bounding_allows_internal_billing_code_before_table() -> None:
    pages = [{
        "pageNumber": 1,
        "text": (
            "14 CFR Part 39\n[Docket No. FAA-2026-1; AD 2026-12-01]\n"
            "This AD applies to the listed airplanes.\n"
            "BILLING CODE 4910-13-P\n"
            "Table 1—Applicable Airplane Models\n"
            "Comply within 12 months.\n"
            "[FR Doc. 2026-12052 Filed 6-15-26]"
        ),
    }]

    selected = bounded_issue_pages(pages, ad_number="2026-12-01")

    assert len(selected) == 1
    assert "Table 1—Applicable Airplane Models" in selected[0]["text"]


def test_issue_bounding_allows_target_part_39_amendment_after_preamble() -> None:
    pages = [{
        "pageNumber": 1,
        "text": (
            "14 CFR Part 39\n"
            "[Docket No. FAA-2026-1; Amendment 39-1; AD 2026-12-01]\n"
            "The FAA proposed to amend 14 CFR part 39 by adding an AD.\n"
            "PART 39—AIRWORTHINESS DIRECTIVES\n"
            "2026-12-01 Example Aircraft: Amendment 39-1.\n"
            "Inspect the affected part.\n"
            "BILLING CODE 4910-13-P\n"
            "[FR Doc. 2026-12052 Filed 6-15-26]"
        ),
    }]

    selected = bounded_issue_pages(pages, ad_number="2026-12-01")

    assert len(selected) == 1
    assert "Inspect the affected part" in selected[0]["text"]


def test_formal_target_heading_wins_over_earlier_cross_reference() -> None:
    pages = [
        {
            "sourceDocumentId": "superseding-rule",
            "pageNumber": 1,
            "text": "14 CFR Part 39\nAD 2023-17-04 supersedes AD 2022-04-04.\n[FR Doc. 2023-10000]",
        },
        {
            "sourceDocumentId": "target-rule",
            "pageNumber": 1,
            "text": "14 CFR Part 39\nThe FAA amends section 39.13 by adding the following new AD: 2022-04-04 Continental Motors.",
        },
        {
            "sourceDocumentId": "target-rule",
            "pageNumber": 2,
            "text": "Compliance is required.\n[FR Doc. 2022-10000]",
        },
    ]

    selected = bounded_issue_pages(pages, ad_number="2022-04-04")

    assert {page["sourceDocumentId"] for page in selected} == {"target-rule"}
    assert [page["pageNumber"] for page in selected] == [1, 2]
    assert "supersedes" not in selected[0]["text"]


def test_document_bounding_retains_original_rule_and_correction() -> None:
    pages = [
        {
            "sourceDocumentId": "original",
            "pageNumber": 1,
            "text": (
                "14 CFR Part 39\n[AD 2008-26-10]\nCompliance\n"
                "Inspect the valve.\n[FR Doc. E8-30465 Filed 12-23-08]"
            ),
        },
        {
            "sourceDocumentId": "correction",
            "pageNumber": 1,
            "text": (
                "14 CFR Part 39\nAirworthiness Directive 2008-26-10\n"
                "Correction of Regulatory Text\nChange paragraph (e) to (d).\n"
                "[FR Doc. 2010-28579 Filed 11-15-10]"
            ),
        },
    ]

    selected = bounded_source_document_pages(pages, ad_number="2008-26-10")

    assert [page["sourceDocumentId"] for page in selected] == ["original", "correction"]
    assert "Inspect the valve" in selected[0]["text"]
    assert "Change paragraph" in selected[1]["text"]


def test_document_bounding_rejects_foreign_rule_that_only_references_target_ad() -> None:
    pages = [
        {
            "sourceDocumentId": "target",
            "pageNumber": 1,
            "text": (
                "Federal Register, June 16, 2026.\n14 CFR Part 39\n"
                "Section 39.13 is amended by adding the following new "
                "airworthiness directive: AD 2011-10-09. Inspect the seat rail.\n"
                "[FR Doc. 2011-10988]"
            ),
        },
        {
            "sourceDocumentId": "foreign",
            "pageNumber": 1,
            "text": (
                "14 CFR Part 39\nSection 39.13 is amended by adding the following new "
                "airworthiness directive: AD 2020-21-22. A commenter referred to AD 2011-10-09.\n"
                "[FR Doc. 2020-24046]"
            ),
        },
    ]

    selected = bounded_source_document_pages(pages, ad_number="2011-10-09")

    assert {page["sourceDocumentId"] for page in selected} == {"target"}


def test_source_evidence_requires_official_identifier_and_part_39_heading() -> None:
    assert official_ad_number("1995-21-15") == "95-21-15"
    assert official_ad_number("2024-14-03") == "2024-14-03"
    status, _ = source_evidence_status(
        "1995-21-15",
        [{"text": "14 CFR Part 39\nSection 39.13 is amended by adding the following new airworthiness directive:\n95±21±15 Teledyne Continental Motors"}],
    )
    assert status == "verified"
    mismatch_status, mismatch_message = source_evidence_status(
        "2000-06-01",
        [{"text": "14 CFR Part 39\nSection 39.13 is amended by adding the following new airworthiness directive:\n2005-05-09 EMBRAER.\nThis AD references Brazilian airworthiness directive 2000-06-01."}],
    )
    assert mismatch_status == "identity_mismatch"
    assert "AD 2005-05-09" in mismatch_message
    missing_status, _ = source_evidence_status("1994-14-12", [])
    assert missing_status == "missing"


class FakeProviderBackedExtractor:
    provider_name = "openai_responses_ad_extractor"
    provider_version = "gpt-test:ad_extraction_prompt_v1:testhash"

    def __init__(self, output: dict[str, Any] | None = None, error: Exception | None = None) -> None:
        self.output = output or provider_output()
        self.error = error
        self.calls = 0

    def extract(self, directive: AirworthinessDirective) -> dict[str, Any]:
        self.calls += 1
        if self.error:
            raise self.error
        return {
            "output": self.output,
            "raw_response": {
                "providerResponseId": "resp_test",
                "providerModel": "gpt-test",
                "promptHash": "testhash",
                "promptVersion": "ad_extraction_prompt_v1",
                "usage": {"input_tokens": 10, "output_tokens": 20},
            },
        }


def test_federal_register_discovery_classifies_and_persists_ad_candidates(db_session: Session) -> None:
    stats = discover_federal_register_ads(db_session, client=FakeFederalRegisterClient())

    assert stats == {"seen": 2, "created": 2, "updated": 0, "candidates": 1, "rejected": 1}
    records = db_session.scalars(select(ADDiscoveryRecord)).all()
    assert len(records) == 2
    candidate = next(record for record in records if record.classification == "ad_candidate")
    rejected = next(record for record in records if record.classification == "non_ad_rule")
    assert candidate.federal_register_document_number == "2026-12052"
    assert candidate.pdf_url == "https://www.govinfo.gov/content/pkg/FR-2026-06-16/pdf/2026-12052.pdf"
    assert candidate.content_hash
    assert rejected.federal_register_document_number == "2026-99999"

    directive = db_session.scalar(select(AirworthinessDirective))
    assert directive is not None
    assert directive.discovery_record_id == candidate.id
    assert directive.ad_number == "2026-12-01"


def test_ad_extraction_routes_low_confidence_output_to_review(
    client: TestClient,
    db_session: Session,
    demo_data: dict[str, object],
    monkeypatch,
) -> None:
    discover_federal_register_ads(db_session, client=FakeFederalRegisterClient())

    extraction_stats = process_pending_ad_extractions(db_session)

    assert extraction_stats["seen"] == 1
    assert extraction_stats["review_queued"] == 1
    review = db_session.scalar(select(ADExtractionReview))
    assert review is not None
    assert review.status == "pending"
    assert review.extraction.provider_name == "deterministic_ad_extractor"
    assert review.extraction.schema_version == "ad_extraction_v3"
    retained_pdf = b"%PDF-1.4\nretained AD test source\n%%EOF\n"
    storage_key = "ad-sources/test/retained-ad.pdf"
    retained_path = Path(get_settings().local_storage_path) / storage_key
    retained_path.parent.mkdir(parents=True, exist_ok=True)
    retained_path.write_bytes(retained_pdf)
    source_document = ADSourceDocument(
        source_system="federal_register",
        source_type="document_pdf",
        source_identifier="2026-12052",
        source_url="https://www.govinfo.gov/content/pkg/FR-2026-06-16/pdf/2026-12052.pdf",
        storage_backend="local",
        storage_key=storage_key,
        media_type="application/pdf",
        content_hash=hashlib.sha256(retained_pdf).hexdigest(),
        storage_bytes=len(retained_pdf),
        captured_at=datetime.now(timezone.utc),
        status="retained",
        parser_name="test-parser",
        parser_version="1",
        metadata_json={},
    )
    db_session.add(source_document)
    db_session.flush()
    publication = db_session.scalar(
        select(ADPublication).where(
            ADPublication.directive_id == review.extraction.directive_id
        )
    )
    if publication is None:
        publication = ADPublication(
            directive_id=review.extraction.directive_id,
            source_system="federal_register",
            source_type="document_pdf",
            source_identifier="2026-12052",
            title=review.extraction.directive.title,
            pdf_url=source_document.source_url,
            status="retained",
            content_hash=source_document.content_hash,
        )
        db_session.add(publication)
    publication.source_document = source_document
    verified_source_pages = [{
        "sourceDocumentId": source_document.id,
        "contentHash": source_document.content_hash,
        "pageNumber": 1,
        "text": "Federal Register, June 16, 2026\n14 CFR Part 39\nSection 39.13 is amended by adding the following new airworthiness directive:\nAD 2026-12-01.\nThis AD applies to Cessna Model 172R airplanes, all serial numbers.\nReview the required corrective action.\n[FR Doc. 2026-12052]",
    }]
    review_ready_output = {
        **review.proposed_output,
        "confidence": 0.9,
        "citations": [],
        "uncertaintyReasons": [],
        "applicabilityGroups": [v3_applicability_group(
            source_document_id=source_document.id,
            citation_text="This AD applies to Cessna Model 172R airplanes, all serial numbers.",
            manufacturer="Cessna",
            model="172R",
            group_key="cessna-172r",
        )],
        "requirements": [{
            "requirementKey": "source-review",
            "applicabilityGroupKeys": ["cessna-172r"],
            "requirementType": "one_time",
            "actionText": "Review the required corrective action.",
            "initialThresholds": [],
            "recurringTriggers": [],
            "combinationLogic": "all",
            "conditions": [],
            "terminatingAction": None,
            "citations": [{
                "sourceDocumentId": source_document.id,
                "pageNumber": 1,
                "text": "Review the required corrective action.",
            }],
            "confidence": 0.9,
            "uncertaintyReasons": [],
        }],
    }
    review.proposed_output = review_ready_output
    review.extraction.output = review_ready_output
    db_session.flush()
    db_session.expire(review.extraction.directive, ["publications"])
    review.extraction.input_content_hash = extraction_input_hash(
        review.extraction.directive
    )
    review.extraction.raw_response = {
        **(review.extraction.raw_response or {}),
        "retainedSourcePagesCached": True,
        "retainedSourcePages": verified_source_pages,
        "sourcePageParser": "test-parser",
    }
    db_session.flush()
    monkeypatch.setattr(
        "app.api.routes.ads.full_text_pages_for_extraction",
        lambda _: verified_source_pages,
    )
    monkeypatch.setattr(
        "app.api.routes.ads.ensure_persisted_source_pages",
        lambda *_: verified_source_pages,
    )

    aircraft = demo_data["aircraft"]
    initial_stats = match_aircraft_ads(db_session, aircraft.id)
    assert initial_stats["directives_seen"] == 0

    login(client, "owner.test@paprnav.local")
    assert client.get("/api/v1/ads/extraction-reviews").status_code == 403

    login(client, "shop.test@paprnav.local")
    shop_list_response = client.get("/api/v1/ads/extraction-reviews")
    assert shop_list_response.status_code == 403
    assert client.get(f"/api/v1/ads/source-documents/{source_document.id}/content").status_code == 403

    admin = create_user(
        db_session,
        "ad.admin@paprnav.local",
        "AD Platform Admin",
    )
    admin_org = create_organization(
        db_session,
        "Paprnav AD Operations",
        "platform",
    )
    add_membership(db_session, admin_org, admin, "platform_admin")
    db_session.commit()
    login(client, "ad.admin@paprnav.local")
    list_response = client.get("/api/v1/ads/extraction-reviews")
    assert list_response.status_code == 200
    assert list_response.json()["currentOffset"] == 0
    reviews = list_response.json()["reviews"]
    assert len(reviews) == 1
    assert list_response.json()["verifiedCount"] == 1
    assert list_response.json()["quarantinedCount"] == 0
    assert list_response.json()["approvalReadyCount"] == 1, reviews[0]["approvalBlockers"]
    assert reviews[0]["directive"]["federalRegisterDocumentNumber"] == "2026-12052"
    assert reviews[0]["extraction"]["inputContentHash"] == review.extraction.input_content_hash
    assert "14 CFR Part 39" in reviews[0]["sourceText"]
    assert reviews[0]["canApprove"] is True
    assert reviews[0]["directive"]["officialAdNumber"] == "2026-12-01"
    assert reviews[0]["sourceDocuments"][0]["sourceIdentifier"] == "2026-12052"
    retained_response = client.get(reviews[0]["sourceDocuments"][0]["contentUrl"])
    assert retained_response.status_code == 200
    assert retained_response.content == retained_pdf
    assert retained_response.headers["content-type"] == "application/pdf"
    direct_review_response = client.get(
        f"/api/v1/ads/extraction-reviews?reviewId={reviews[0]['id']}"
    )
    assert direct_review_response.status_code == 200
    assert direct_review_response.json()["currentOffset"] == 0
    assert direct_review_response.json()["reviews"][0]["id"] == reviews[0]["id"]

    edited_output: dict[str, Any] = reviews[0]["proposedOutput"]
    edited_output["applicabilityGroups"] = []
    empty_applicability = client.post(
        f"/api/v1/ads/extraction-reviews/{reviews[0]['id']}/decision",
        json={
            "decision": "edited",
            "output": edited_output,
            "notes": "Applicability could not be attributed.",
        },
    )
    assert empty_applicability.status_code == 422
    assert "at least one applicability group" in empty_applicability.json()["detail"]

    edited_output["applicabilityGroups"] = review_ready_output["applicabilityGroups"]
    decision_response = client.post(
        f"/api/v1/ads/extraction-reviews/{reviews[0]['id']}/decision",
        json={"decision": "edited", "output": edited_output, "notes": "Confirmed from source PDF."},
    )
    assert decision_response.status_code == 200
    decided = decision_response.json()["review"]
    assert decided["status"] == "edited"
    assert decided["decisionOutput"]["affectedProducts"] == ["Cessna 172R"]
    decision_history = db_session.scalar(
        select(ADExtractionReviewDecision).where(
            ADExtractionReviewDecision.review_id == review.id
        )
    )
    assert decision_history is not None
    assert decision_history.actor_user_id == admin.id
    assert decision_history.decision == "edited"
    assert decision_history.decision_output == review.extraction.output
    second_admin = create_user(
        db_session,
        "second.ad.admin@paprnav.local",
        "Second AD Platform Admin",
    )
    second_admin_org = create_organization(
        db_session,
        "Second Paprnav AD Operations",
        "platform",
    )
    add_membership(db_session, second_admin_org, second_admin, "platform_admin")
    db_session.commit()
    login(client, "second.ad.admin@paprnav.local")
    conflicting_response = client.post(
        f"/api/v1/ads/extraction-reviews/{reviews[0]['id']}/decision",
        json={
            "decision": "rejected",
            "notes": "Concurrent reviewer reached a different conclusion.",
        },
    )
    assert conflicting_response.status_code == 409
    conflict = db_session.scalar(
        select(ADExtractionReviewDecision).where(
            ADExtractionReviewDecision.review_id == review.id,
            ADExtractionReviewDecision.event_type == "decision_conflict",
        )
    )
    assert conflict is not None
    assert conflict.actor_user_id == second_admin.id
    assert conflict.metadata_json["terminalReviewerUserId"] == admin.id
    retained_path.write_bytes(b"%PDF-1.4\ntampered source\n%%EOF\n")
    tampered_response = client.get(
        f"/api/v1/ads/source-documents/{source_document.id}/content"
    )
    assert tampered_response.status_code == 409
    retained_path.write_bytes(retained_pdf)
    target_ids = db_session.scalars(
        select(ADTargetApplicability.target_id).where(
            ADTargetApplicability.directive_id == review.extraction.directive_id
        )
    ).all()
    assert target_ids
    assert db_session.scalar(
        select(ADCoverageSubscription.id)
        .join(
            ADCoverageSet,
            ADCoverageSet.id == ADCoverageSubscription.coverage_set_id,
        )
        .where(
            ADCoverageSet.target_id.in_(target_ids),
            ADCoverageSubscription.aircraft_id == aircraft.id,
        )
    ) is not None
    assert db_session.scalar(
        select(ProductEvent.id).where(
            ProductEvent.aircraft_id == aircraft.id,
            ProductEvent.event_type == "ad_matching_invalidated",
        )
    ) is not None

    login(client, "owner.test@paprnav.local")
    match_response = client.get(
        f"/api/v1/ads/aircraft/{aircraft.id}/matches"
    )
    assert match_response.status_code == 200
    assert match_response.json()["matcherStatus"] == "pending_recomputation"
    assert match_response.json()["reprocessingRequired"] is True

    db_session.refresh(review)
    assert review.extraction.status == "approved"
    assert review.extraction.directive.review_status == "approved"
    assert review.extraction.directive.extraction_status == "complete"

    login(client, "shop.test@paprnav.local")
    monkeypatch.setattr(
        "app.services.ad_release.persisted_source_pages",
        lambda *_: (False, []),
    )
    assert client.get("/api/v1/ads/directives").json() == []
    monkeypatch.setattr(
        "app.services.ad_release.persisted_source_pages",
        lambda *_: (True, verified_source_pages),
    )
    assert review.extraction.input_content_hash == extraction_input_hash(
        review.extraction.directive
    ), (
        review.extraction.input_content_hash,
        extraction_input_hash(review.extraction.directive),
    )
    released = client.get("/api/v1/ads/directives")
    assert released.status_code == 200
    assert [item["officialAdNumber"] for item in released.json()] == ["2026-12-01"]
    structured = client.get(
        "/api/v1/ads/directives?productType=aircraft&manufacturer=Cessna&model=172R"
    )
    assert structured.status_code == 200
    assert [item["officialAdNumber"] for item in structured.json()] == ["2026-12-01"]
    assert structured.json()[0]["applicabilityTargets"] == [{
        "groupKey": "cessna-172r",
        "productType": "aircraft",
        "productSubtype": None,
        "manufacturer": "Cessna",
        "model": "172R",
        "sourceManufacturer": "Cessna",
        "sourceModel": "172R",
    }]
    assert client.get("/api/v1/ads/directives?manufacturer=Piper").json() == []
    assert [item["officialAdNumber"] for item in client.get("/api/v1/ads/directives?q=172R").json()] == [
        "2026-12-01"
    ]
    applicability = db_session.scalar(
        select(ADTargetApplicability).where(
            ADTargetApplicability.source_extraction_id == review.extraction_id,
            ADTargetApplicability.status == "current",
        )
    )
    applicability.target.make = "Piper"
    db_session.flush()
    assert client.get("/api/v1/ads/directives?manufacturer=Piper").json() == []
    assert len(client.get("/api/v1/ads/directives?manufacturer=Cessna").json()) == 1
    correction_bytes = b"%PDF-1.4\nlater correction\n%%EOF\n"
    correction_document = ADSourceDocument(
        source_system="federal_register",
        source_type="document_pdf",
        source_identifier="2026-12052-correction",
        storage_backend="local",
        storage_key="ad-sources/test/later-correction.pdf",
        media_type="application/pdf",
        content_hash=hashlib.sha256(correction_bytes).hexdigest(),
        storage_bytes=len(correction_bytes),
        captured_at=datetime.now(timezone.utc),
        status="retained",
    )
    db_session.add(correction_document)
    db_session.flush()
    db_session.add(ADPublication(
        directive_id=review.extraction.directive_id,
        source_document_id=correction_document.id,
        source_system="federal_register",
        source_type="document_pdf",
        source_identifier="2026-12052-correction",
        content_hash=correction_document.content_hash,
        status="retained",
    ))
    db_session.flush()
    db_session.expire(review.extraction.directive, ["publications"])
    blockers = extraction_approval_blockers(
        review.extraction, review.extraction.output, verified_source_pages,
    )
    assert any("source document set changed" in blocker for blocker in blockers)
    assert client.get("/api/v1/ads/directives").json() == []


def test_provider_backed_extraction_uses_cache_and_routes_disagreement_to_review(db_session: Session) -> None:
    discover_federal_register_ads(db_session, client=FakeFederalRegisterClient())
    provider = FakeProviderBackedExtractor(
        output=provider_output(
            affected_products=["Cessna 172R"],
            confidence=0.91,
            uncertainty_reasons=["Applicability text differs from deterministic baseline."],
        ),
    )

    first_stats = process_pending_ad_extractions(db_session, llm_provider=provider)
    second_stats = process_pending_ad_extractions(db_session, llm_provider=provider)

    assert first_stats["seen"] == 1
    assert first_stats["review_queued"] == 1
    assert second_stats["seen"] == 1
    assert provider.calls == 1

    extraction = db_session.scalar(select(ADExtraction).where(ADExtraction.provider_name == provider.provider_name))
    assert extraction is not None
    assert extraction.provider_version == provider.provider_version
    assert extraction.status == "needs_review"
    assert "invalid_requirement_evidence" in extraction.raw_response["reviewReasons"]
    assert "provider_uncertainty" in extraction.raw_response["reviewReasons"]
    assert db_session.scalar(select(ADExtractionReview)) is not None
    assert db_session.scalars(select(ADTargetApplicability)).all() == []


def test_provider_backed_extraction_without_retained_pages_requires_review(db_session: Session) -> None:
    discover_federal_register_ads(db_session, client=FakeFederalRegisterClient())
    provider = FakeProviderBackedExtractor(output=provider_output())

    stats = process_pending_ad_extractions(db_session, llm_provider=provider)

    assert stats["seen"] == 1
    assert stats["approved"] == 0
    assert stats["review_queued"] == 1
    extraction = db_session.scalar(select(ADExtraction).where(ADExtraction.provider_name == provider.provider_name))
    assert extraction is not None
    assert extraction.status == "needs_review"
    assert "invalid_requirement_evidence" in extraction.raw_response["reviewReasons"]
    assert db_session.scalar(select(ADExtractionReview)) is not None
    applicabilities = db_session.scalars(select(ADTargetApplicability)).all()
    assert applicabilities == []


def test_provider_backed_extraction_falls_back_to_deterministic_on_provider_error(db_session: Session) -> None:
    discover_federal_register_ads(db_session, client=FakeFederalRegisterClient())
    provider = FakeProviderBackedExtractor(error=RuntimeError("provider unavailable"))

    stats = process_pending_ad_extractions(db_session, llm_provider=provider)

    assert stats["seen"] == 1
    assert stats["review_queued"] == 1
    assert provider.calls == 1
    extraction = db_session.scalar(select(ADExtraction))
    assert extraction is not None
    assert extraction.provider_name == "deterministic_ad_extractor"
    assert extraction.raw_response["fallbackReason"] == "RuntimeError: provider unavailable"


def candidate_document() -> dict[str, Any]:
    return {
        "title": "Airworthiness Directives; Airbus Helicopters",
        "type": "RULE",
        "abstract": "The FAA is adopting a new airworthiness directive (AD) 2026-12-01.",
        "document_number": "2026-12052",
        "html_url": "https://www.federalregister.gov/documents/2026/06/16/2026-12052/example",
        "pdf_url": "https://www.govinfo.gov/content/pkg/FR-2026-06-16/pdf/2026-12052.pdf",
        "public_inspection_pdf_url": None,
        "publication_date": "2026-06-16",
        "agencies": [{"name": "Federal Aviation Administration", "slug": "federal-aviation-administration"}],
        "excerpts": "Airworthiness Directives; AD 2026-12-01.",
    }


def non_ad_rule_document() -> dict[str, Any]:
    return {
        "title": "Amendment of Class E Airspace; Example, Kansas",
        "type": "RULE",
        "abstract": "This action amends Class E airspace.",
        "document_number": "2026-99999",
        "html_url": "https://www.federalregister.gov/documents/2026/06/16/2026-99999/example",
        "pdf_url": "https://www.govinfo.gov/content/pkg/FR-2026-06-16/pdf/2026-99999.pdf",
        "publication_date": "2026-06-16",
        "agencies": [{"name": "Federal Aviation Administration", "slug": "federal-aviation-administration"}],
        "excerpts": "Amends controlled airspace for an airport.",
    }


def provider_output(
    *,
    affected_products: list[str] | None = None,
    confidence: float = 0.92,
    uncertainty_reasons: list[str] | None = None,
) -> dict[str, Any]:
    product = (affected_products or ["Airbus Helicopters AS350"])[0]
    if product == "Cessna 172R":
        manufacturer, model, group_key = "Cessna", "172R", "cessna-172r"
    else:
        manufacturer, model, group_key = "Airbus Helicopters", "AS350", "airbus-as350"
    return {
        "adNumber": "2026-12-01",
        "title": "Airworthiness Directives; Airbus Helicopters",
        "effectiveDate": None,
        "publicationDate": "2026-06-16",
        "affectedProducts": affected_products if affected_products is not None else ["Airbus Helicopters"],
        "applicabilityGroups": [{
            "groupKey": group_key,
            "productType": "rotorcraft",
            "productSubtype": None,
            "manufacturer": {
                "sourceName": manufacturer,
                "normalizedName": None,
            },
            "modelApplicability": {
                "kind": "listed",
                "models": [{
                    "sourceDesignation": model,
                    "normalizedDesignation": None,
                    "aliases": [],
                }],
                "sourceText": f"{manufacturer} Model {model}",
            },
            "serialNumberApplicability": {
                "kind": "all",
                "values": [],
                "ranges": [],
                "excludedValues": [],
                "sourceText": "all serial numbers",
            },
            "equipmentCombinationLogic": "all",
            "equipmentConditions": [],
            "conditions": [],
            "citations": [{
                "sourceDocumentId": "asd_example",
                "pageNumber": 1,
                "text": f"{manufacturer} Model {model}",
            }],
            "confidence": 0.95,
            "uncertaintyReasons": [],
        }],
        "complianceActions": ["Review source document for required corrective actions."],
        "complianceIntervals": [],
        "supersedesAdNumbers": [],
        "sourceUrls": {
            "html": "https://www.federalregister.gov/documents/2026/06/16/2026-12052/example",
            "pdf": "https://www.govinfo.gov/content/pkg/FR-2026-06-16/pdf/2026-12052.pdf",
            "publicInspectionPdf": None,
        },
        "confidence": confidence,
        "citations": [{"field": "title", "source": "federal_register", "text": "Airworthiness Directives; Airbus Helicopters"}],
        "uncertaintyReasons": uncertainty_reasons or [],
        "requirements": [],
        "amocProvisions": [],
    }


def v3_applicability_group(
    *,
    source_document_id: str,
    citation_text: str,
    manufacturer: str,
    model: str,
    group_key: str,
) -> dict[str, Any]:
    return {
        "groupKey": group_key,
        "productType": "aircraft",
        "productSubtype": None,
        "manufacturer": {"sourceName": manufacturer, "normalizedName": None},
        "modelApplicability": {
            "kind": "listed",
            "models": [{
                "sourceDesignation": model,
                "normalizedDesignation": None,
                "aliases": [],
            }],
            "sourceText": citation_text,
        },
        "serialNumberApplicability": {
            "kind": "all",
            "values": [],
            "ranges": [],
            "excludedValues": [],
            "sourceText": "all serial numbers",
        },
        "equipmentCombinationLogic": "all",
        "equipmentConditions": [],
        "conditions": [],
        "citations": [{
            "sourceDocumentId": source_document_id,
            "pageNumber": 1,
            "text": citation_text,
        }],
        "confidence": 0.95,
        "uncertaintyReasons": [],
    }


def test_visual_ocr_draft_exception_is_limited_to_an_exact_cited_model_cell() -> None:
    source_pages = [{
        "sourceDocumentId": "asd_table",
        "pageNumber": 4,
        "text": "Textron Aviation Tnc. 172D, 172T, 172K",
    }]
    proposal = {"applicabilityGroups": [{
        "modelApplicability": {
            "models": [{
                "sourceDesignation": "172I",
                "normalizedDesignation": None,
                "aliases": [],
            }],
        },
        "citations": [{
            "sourceDocumentId": "asd_table",
            "pageNumber": 4,
            "text": "Textron Aviation Tnc. 172D, 172T, 172K",
        }],
        "uncertaintyReasons": [
            "visual_ocr_model_cell_mismatch|modelIndex=0|visual=172I|parsed=172T|sourceDocumentId=asd_table|pageNumber=4"
        ],
    }]}

    shadow, records = visual_ocr_validation_shadow(proposal, source_pages)

    assert proposal["applicabilityGroups"][0]["modelApplicability"]["models"][0]["sourceDesignation"] == "172I"
    assert shadow["applicabilityGroups"][0]["modelApplicability"]["models"][0]["sourceDesignation"] == "172T"
    assert records == [{
        "groupIndex": 0,
        "modelIndex": 0,
        "visual": "172I",
        "parsed": "172T",
        "sourceDocumentId": "asd_table",
        "pageNumber": 4,
    }]

    proposal["applicabilityGroups"][0]["citations"][0]["sourceDocumentId"] = "asd_other"
    with pytest.raises(ValueError, match="admitted cited page"):
        visual_ocr_validation_shadow(proposal, source_pages)

    proposal["applicabilityGroups"][0]["citations"][0]["sourceDocumentId"] = "asd_table"
    proposal["applicabilityGroups"][0]["modelApplicability"]["models"][0][
        "normalizedDesignation"
    ] = "UNSUPPORTED-CANONICAL"
    with pytest.raises(ValueError, match="normalizedDesignation must be null"):
        visual_ocr_validation_shadow(proposal, source_pages)


def test_staging_complete_proposal_is_audited_idempotent_and_reversible(
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    actor = create_user(db_session, "proposal.admin@paprnav.local", "Proposal Admin")
    organization = create_organization(db_session, "Proposal Operations", "platform")
    add_membership(db_session, organization, actor, "platform_admin")
    directive = AirworthinessDirective(
        ad_number="2026-12-01",
        title="Airworthiness Directives; Airbus Helicopters",
        status="candidate",
        source_content_hash="source-hash",
        extraction_status="needs_review",
        review_status="pending",
    )
    db_session.add(directive)
    db_session.flush()
    source_text = (
        "14 CFR Part 39 [Docket No. FAA-2026-1; Amendment 39-1; AD 2026-12-01] "
        "Airworthiness Directives; Airbus Helicopters Model AS350 all serial numbers. "
        "Inspect the rotorcraft."
    )
    source_pages = [{
        "sourceDocumentId": "asd_example",
        "pageNumber": 1,
        "text": source_text,
    }]

    def complete_proposal(title: str) -> dict[str, Any]:
        output = provider_output()
        output["title"] = title
        group = output["applicabilityGroups"][0]
        group["modelApplicability"]["sourceText"] = "Airbus Helicopters Model AS350"
        group["serialNumberApplicability"]["sourceText"] = "all serial numbers"
        group["citations"] = [{
            "sourceDocumentId": "asd_example",
            "pageNumber": 1,
            "text": "Airbus Helicopters Model AS350 all serial numbers",
        }]
        group["uncertaintyReasons"] = ["Human confirmation of applicability is pending."]
        output["requirements"] = [{
            "requirementKey": "inspection",
            "applicabilityGroupKeys": ["airbus-as350"],
            "requirementType": "one_time",
            "actionText": "Inspect the rotorcraft.",
            "initialThresholds": [],
            "recurringTriggers": [],
            "combinationLogic": "all",
            "conditions": [],
            "terminatingAction": None,
            "citations": [{
                "sourceDocumentId": "asd_example",
                "pageNumber": 1,
                "text": "Inspect the rotorcraft.",
            }],
            "confidence": 0.9,
            "uncertaintyReasons": [],
        }]
        return output

    prior = complete_proposal("Prior complete proposal")
    extraction = ADExtraction(
        directive_id=directive.id,
        provider_name="test",
        provider_version="1",
        schema_version="ad_extraction_v3",
        input_content_hash="source-hash",
        status="needs_review",
        confidence=0.8,
        output=prior,
        citations=[],
        raw_response={},
    )
    db_session.add(extraction)
    db_session.flush()
    review = ADExtractionReview(
        extraction_id=extraction.id,
        status="pending",
        proposed_output=prior,
    )
    db_session.add(review)
    db_session.flush()
    monkeypatch.setattr(
        "app.scripts.stage_ad_review_proposal.ensure_persisted_source_pages",
        lambda *_: source_pages,
    )
    monkeypatch.setattr(
        "app.scripts.stage_ad_review_proposal.bounded_source_document_pages",
        lambda pages, **_: pages,
    )
    proposed = complete_proposal("New complete proposal")

    with pytest.raises(ValueError, match="applicability uncertainty"):
        stage_review_proposal(
            db_session,
            ad_number=directive.ad_number,
            review_id=review.id,
            actor_user_id=actor.id,
            loaded_proposal=proposed,
            allow_incomplete=False,
        )

    first = stage_review_proposal(
        db_session,
        ad_number=directive.ad_number,
        review_id=review.id,
        actor_user_id=actor.id,
        loaded_proposal=proposed,
        allow_incomplete=True,
    )
    assert first["idempotent"] is False
    assert review.status == "pending"
    assert extraction.status == "needs_review"
    history = db_session.scalars(
        select(ADExtractionReviewDecision).where(
            ADExtractionReviewDecision.review_id == review.id,
            ADExtractionReviewDecision.event_type == "proposal_staged",
        )
    ).all()
    assert len(history) == 1
    assert history[0].metadata_json["priorOutput"] == prior
    assert history[0].metadata_json["priorExtractionOutput"] == prior
    assert history[0].decision_output == review.proposed_output

    monkeypatch.setattr(
        "app.api.routes.ads.full_text_pages_for_extraction",
        lambda *_: source_pages,
    )
    serialized = serialize_review(review)
    assert serialized.proposalProvenance is not None
    assert serialized.proposalProvenance.stagingDecisionId == history[0].id
    assert serialized.proposalProvenance.actorUserId == actor.id
    assert serialized.proposalProvenance.stagingMode == "allow_incomplete"

    replay = stage_review_proposal(
        db_session,
        ad_number=directive.ad_number,
        review_id=review.id,
        actor_user_id=actor.id,
        loaded_proposal=proposed,
        allow_incomplete=True,
    )
    assert replay["idempotent"] is True
    assert len(db_session.scalars(
        select(ADExtractionReviewDecision).where(
            ADExtractionReviewDecision.review_id == review.id,
            ADExtractionReviewDecision.event_type == "proposal_staged",
        )
    ).all()) == 1

    dry_run = complete_proposal("Dry-run proposal")
    dry_run_path = tmp_path / "dry-run-proposal.json"
    dry_run_path.write_text(json.dumps(dry_run), encoding="utf-8")
    connection = db_session.connection()
    monkeypatch.setattr(
        "app.scripts.stage_ad_review_proposal.SessionLocal",
        lambda: Session(bind=connection, join_transaction_mode="create_savepoint"),
    )
    monkeypatch.setattr(
        "sys.argv",
        [
            "stage_ad_review_proposal",
            "--ad-number", directive.ad_number,
            "--review-id", review.id,
            "--actor-user-id", actor.id,
            "--input", str(dry_run_path),
            "--allow-incomplete",
        ],
    )
    before_history_count = len(db_session.scalars(
        select(ADExtractionReviewDecision).where(
            ADExtractionReviewDecision.review_id == review.id,
            ADExtractionReviewDecision.event_type == "proposal_staged",
        )
    ).all())
    stage_review_proposal_main()
    db_session.expire_all()
    review = db_session.get(ADExtractionReview, review.id)
    extraction = db_session.get(ADExtraction, extraction.id)
    assert review is not None and review.proposed_output["title"] == "New complete proposal"
    assert extraction is not None and extraction.output["title"] == "New complete proposal"
    assert len(db_session.scalars(
        select(ADExtractionReviewDecision).where(
            ADExtractionReviewDecision.review_id == review.id,
            ADExtractionReviewDecision.event_type == "proposal_staged",
        )
    ).all()) == before_history_count

    extraction.output = prior
    with pytest.raises(ValueError, match="output diverge"):
        stage_review_proposal(
            db_session,
            ad_number=directive.ad_number,
            review_id=review.id,
            actor_user_id=actor.id,
            loaded_proposal=proposed,
            allow_incomplete=True,
        )
    extraction.output = dict(review.proposed_output)

    with pytest.raises(ValueError, match="belongs to AD"):
        stage_review_proposal(
            db_session,
            ad_number="2026-99-99",
            review_id=review.id,
            actor_user_id=actor.id,
            loaded_proposal=proposed,
            allow_incomplete=True,
        )

    rollback = stage_review_proposal(
        db_session,
        ad_number=directive.ad_number,
        review_id=review.id,
        actor_user_id=actor.id,
        loaded_proposal=prior,
        allow_incomplete=True,
    )
    assert rollback["idempotent"] is False
    assert review.proposed_output["title"] == "Prior complete proposal"
    history = db_session.scalars(
        select(ADExtractionReviewDecision).where(
            ADExtractionReviewDecision.review_id == review.id,
            ADExtractionReviewDecision.event_type == "proposal_staged",
        ).order_by(ADExtractionReviewDecision.decided_at)
    ).all()
    assert len(history) == 2
    assert history[-1].metadata_json["priorOutput"]["title"] == "New complete proposal"

    review.status = "approved"
    with pytest.raises(ValueError, match="terminal"):
        stage_review_proposal(
            db_session,
            ad_number=directive.ad_number,
            review_id=review.id,
            actor_user_id=actor.id,
            loaded_proposal=prior,
            allow_incomplete=True,
        )
