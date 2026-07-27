from datetime import date

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.core import (
    ADDiscoveryRecord,
    ADExtraction,
    ADMatchAdjudication,
    ADMatchEvidence,
    ADMatchResult,
    AirworthinessDirective,
    LogbookEntry,
    LogbookSection,
    ProductEvent,
    UserFeedback,
    WorkflowStatusEvent,
)
from app.services.ad_discovery import hash_json
from app.services.ad_applicability import populate_applicability_from_extraction
from app.services import ad_matching
from app.services.ad_matching import match_aircraft_ads
from tests.conftest import login


def test_match_status_distinguishes_not_run_from_current_empty(
    client: TestClient,
    db_session: Session,
    demo_data: dict[str, object],
) -> None:
    aircraft = demo_data["aircraft"]
    login(client, "owner.test@paprnav.local")

    not_run_response = client.get(
        f"/api/v1/ads/aircraft/{aircraft.id}/matches"
    )
    assert not_run_response.status_code == 200
    assert not_run_response.json()["matches"] == []
    assert not_run_response.json()["matcherStatus"] == "not_run"
    assert not_run_response.json()["reprocessingRequired"] is False

    stats = match_aircraft_ads(db_session, aircraft.id)

    assert stats["directives_seen"] == 0
    current_response = client.get(
        f"/api/v1/ads/aircraft/{aircraft.id}/matches"
    )
    assert current_response.status_code == 200
    assert current_response.json()["matches"] == []
    assert current_response.json()["matcherStatus"] == "current"
    assert current_response.json()["reprocessingRequired"] is False


def test_ad_matching_creates_evidence_and_unresolved_review_tasks(
    client: TestClient,
    db_session: Session,
    demo_data: dict[str, object],
    monkeypatch,
) -> None:
    aircraft = demo_data["aircraft"]
    owner_user = demo_data["owner_user"]
    airframe = db_session.scalar(select(LogbookSection).where(LogbookSection.key == "airframe"))
    assert airframe is not None
    db_session.add(
        LogbookEntry(
            aircraft_id=aircraft.id,
            logbook_section_id=airframe.id,
            entry_date=date(2026, 5, 1),
            description="Complied with AD 2026-99-01 by inspecting the Cessna 172R elevator trim system.",
            performer_name="A. Mechanic",
            performer_credential="A&P IA",
            source_type="ocr_ingestion",
            created_by_user_id=owner_user.id,
            tach_time=1100.0,
            raw_text="Complied with AD 2026-99-01 by inspecting the Cessna 172R elevator trim system.",
            review_status="verified",
        )
    )
    db_session.add(
        LogbookEntry(
            aircraft_id=aircraft.id,
            logbook_section_id=airframe.id,
            entry_date=date(2026, 5, 20),
            description="Recurring AD 2026-99-02 inspection completed on Cessna 172R seat rails.",
            performer_name="A. Mechanic",
            performer_credential="A&P IA",
            source_type="ocr_ingestion",
            created_by_user_id=owner_user.id,
            tach_time=1120.0,
            raw_text="Recurring AD 2026-99-02 inspection completed on Cessna 172R seat rails.",
            review_status="verified",
        )
    )
    create_approved_extraction(
        db_session,
        title="Airworthiness Directives; Cessna 172R Airplanes",
        document_number="2026-99001",
        ad_number="2026-99-01",
        affected_products=["Cessna 172R"],
        compliance_actions=["Inspect elevator trim system."],
        compliance_intervals=[],
    )
    create_approved_extraction(
        db_session,
        title="Airworthiness Directives; Cessna 172R Airplanes",
        document_number="2026-99002",
        ad_number="2026-99-02",
        affected_products=["Cessna 172R"],
        compliance_actions=["Inspect seat rails every 100 tach hours."],
        compliance_intervals=[{"type": "tach_hours", "intervalHours": 100}],
    )
    create_approved_extraction(
        db_session,
        title="Airworthiness Directives; Cessna 172R Airplanes",
        document_number="2026-99003",
        ad_number="2026-99-03",
        affected_products=["Cessna 172R"],
        compliance_actions=[],
        compliance_intervals=[],
    )
    db_session.commit()

    extraction_calls = 0
    original_extractor = ad_matching.extract_structured_maintenance_data

    def recording_extractor(lines: list[str]) -> dict:
        nonlocal extraction_calls
        extraction_calls += 1
        return original_extractor(lines)

    monkeypatch.setattr(
        ad_matching,
        "extract_structured_maintenance_data",
        recording_extractor,
    )
    stats = match_aircraft_ads(db_session, aircraft.id)

    assert stats["directives_seen"] == 3
    assert stats["matched"] == 1
    assert stats["unresolved"] == 2
    entry_count = len(
        db_session.scalars(
            select(LogbookEntry).where(
                LogbookEntry.aircraft_id == aircraft.id,
                LogbookEntry.entry_date.is_not(None),
            )
        ).all()
    )
    assert extraction_calls == entry_count
    one_time_match = db_session.scalar(
        select(ADMatchResult).where(ADMatchResult.status == "candidate_satisfied", ADMatchResult.match_type == "one_time")
    )
    assert one_time_match is not None
    assert one_time_match.confidence > 0.7
    assert db_session.scalar(select(ADMatchEvidence).where(ADMatchEvidence.match_result_id == one_time_match.id)) is not None

    recurring_match = db_session.scalar(select(ADMatchResult).where(ADMatchResult.match_type == "simple_recurring"))
    assert recurring_match is not None
    assert recurring_match.status == "needs_adjudication"
    assert "recurring_due_status_unknown" in recurring_match.unresolved_reasons

    adjudication_count = len(db_session.scalars(select(ADMatchAdjudication)).all())
    assert adjudication_count == 2

    db_session.add(
        ADMatchResult(
            aircraft_id=one_time_match.aircraft_id,
            directive_id=one_time_match.directive_id,
            extraction_id=one_time_match.extraction_id,
            status="candidate_satisfied",
            match_type="one_time",
            confidence=0.99,
            rationale="Stale matcher result that must not be surfaced.",
            unresolved_reasons=[],
            algorithm_name="deterministic_ad_logbook_matcher",
            algorithm_version="0.1.0",
            input_hash="stale-version-result",
        )
    )
    db_session.commit()

    login(client, "owner.test@paprnav.local")
    response = client.get(f"/api/v1/ads/aircraft/{aircraft.id}/matches")
    assert response.status_code == 200
    match_payload = response.json()
    assert match_payload["matcherStatus"] == "current"
    assert match_payload["algorithmVersion"] == "0.3.0"
    assert match_payload["reprocessingRequired"] is False
    matches = match_payload["matches"]
    assert len(matches) == 3
    candidate = next(match for match in matches if match["status"] == "candidate_satisfied")
    assert candidate["evidence"][0]["logbookEntryId"]
    assert "logbook evidence" in candidate["rationale"]
    assert candidate["applicability"]["component"]["role"] == "airframe"
    assert candidate["applicability"]["target"]["make"] == "Cessna"

    unresolved = next(match for match in matches if match["status"] == "needs_adjudication")
    decision_response = client.post(
        f"/api/v1/ads/matches/{unresolved['id']}/adjudication",
        json={
            "decision": "needs_more_info",
            "notes": "Need component serial confirmation.",
            "futureImprovementTags": ["serial_lookup", "component_identity"],
        },
    )
    assert decision_response.status_code == 200
    decided_match = decision_response.json()["match"]
    assert decided_match["status"] == "adjudicated_needs_more_info"
    assert decided_match["adjudication"]["futureImprovementTags"] == ["serial_lookup", "component_identity"]

    assert db_session.scalar(select(ProductEvent).where(ProductEvent.event_type == "ad_match_adjudicated")) is not None
    assert db_session.scalar(select(WorkflowStatusEvent).where(WorkflowStatusEvent.workflow_type == "hitl_adjudication")) is not None

    feedback_response = client.post(
        "/api/v1/observability/feedback",
        json={"subjectType": "ad_match", "subjectId": unresolved["id"], "feedbackType": "demo_note", "message": "Reviewer hesitated here."},
    )
    assert feedback_response.status_code == 201
    feedback_id = feedback_response.json()["feedback"]["id"]
    triage_response = client.patch(f"/api/v1/observability/feedback/{feedback_id}", json={"status": "triaged"})
    assert triage_response.status_code == 200
    assert db_session.get(UserFeedback, feedback_id).status == "triaged"

    observability_response = client.get("/api/v1/observability")
    assert observability_response.status_code == 200
    assert observability_response.json()["events"]
    assert observability_response.json()["workflowEvents"]
    assert observability_response.json()["feedback"]

    current_results = db_session.scalars(
        select(ADMatchResult).where(
            ADMatchResult.aircraft_id == aircraft.id,
            ADMatchResult.algorithm_version == "0.3.0",
        )
    ).all()
    for result in current_results:
        result.algorithm_version = "0.2.0"
    completion_event = db_session.scalar(
        select(ProductEvent)
        .where(
            ProductEvent.aircraft_id == aircraft.id,
            ProductEvent.event_type == "ad_matching_completed",
        )
        .order_by(ProductEvent.event_time.desc())
    )
    assert completion_event is not None
    completion_event.properties_json = {
        **(completion_event.properties_json or {}),
        "algorithm_version": "0.2.0",
    }
    db_session.commit()

    stale_response = client.get(
        f"/api/v1/ads/aircraft/{aircraft.id}/matches"
    )
    assert stale_response.status_code == 200
    assert stale_response.json()["matches"] == []
    assert stale_response.json()["matcherStatus"] == "pending_recomputation"
    assert stale_response.json()["reprocessingRequired"] is True


def test_ad_matching_normalizes_legacy_ad_numbers_and_requires_verified_claims(
    db_session: Session,
    demo_data: dict[str, object],
) -> None:
    aircraft = demo_data["aircraft"]
    owner_user = demo_data["owner_user"]
    airframe = db_session.scalar(
        select(LogbookSection).where(LogbookSection.key == "airframe")
    )
    assert airframe is not None
    entries = [
        (
            date(2012, 12, 17),
            "C/W AD 11-10-09 on seat rails by inspecting.",
            "verified",
        ),
        (
            date(2013, 1, 10),
            "Complied with AD 2012-01-02 by replacement.",
            "needs_review",
        ),
        (
            date(2013, 2, 10),
            "AD 2013-02-03 reviewed for planning.",
            "verified",
        ),
        (
            date(2014, 3, 10),
            "AD 2014-03-04 will not be complied with until parts arrive.",
            "verified",
        ),
    ]
    for entry_date, text, review_status in entries:
        db_session.add(
            LogbookEntry(
                aircraft_id=aircraft.id,
                logbook_section_id=airframe.id,
                entry_date=entry_date,
                description=text,
                performer_name="A. Mechanic",
                performer_credential="A&P IA",
                source_type="ocr_ingestion",
                created_by_user_id=owner_user.id,
                raw_text=text,
                review_status=review_status,
            )
        )

    for index, ad_number in enumerate(
        ("2011-10-09", "2012-01-02", "2013-02-03", "2014-03-04"),
        start=1,
    ):
        create_approved_extraction(
            db_session,
            title="Airworthiness Directives; Cessna 172R Seat Rails",
            document_number=f"legacy-{index}",
            ad_number=ad_number,
            affected_products=["Cessna 172R"],
            compliance_actions=["Inspect or replace seat rail components."],
            compliance_intervals=[],
        )
    db_session.commit()

    stats = match_aircraft_ads(db_session, aircraft.id)

    assert stats["matched"] == 1
    assert stats["unresolved"] == 3
    results = db_session.scalars(
        select(ADMatchResult).order_by(ADMatchResult.created_at)
    ).all()
    results_by_ad = {
        result.directive.ad_number: result
        for result in results
    }
    assert results_by_ad["2011-10-09"].status == "candidate_satisfied"
    assert results_by_ad["2011-10-09"].confidence > 0.8
    assert results_by_ad["2012-01-02"].evidence_links == []
    assert "logbook_entry_unverified" not in results_by_ad["2012-01-02"].unresolved_reasons
    assert (
        "explicit_compliance_claim_missing"
        in results_by_ad["2013-02-03"].unresolved_reasons
    )
    assert results_by_ad["2014-03-04"].status == "needs_adjudication"
    assert (
        "explicit_compliance_claim_missing"
        in results_by_ad["2014-03-04"].unresolved_reasons
    )


def create_approved_extraction(
    db: Session,
    title: str,
    document_number: str,
    ad_number: str,
    affected_products: list[str],
    compliance_actions: list[str],
    compliance_intervals: list[dict],
) -> ADExtraction:
    snapshot = {
        "title": title,
        "document_number": document_number,
        "type": "RULE",
        "publication_date": "2026-06-18",
    }
    record = ADDiscoveryRecord(
        federal_register_document_number=document_number,
        title=title,
        document_type="RULE",
        abstract=f"AD {ad_number}",
        publication_date=date(2026, 6, 18),
        effective_date=None,
        html_url=f"https://www.federalregister.gov/documents/2026/06/18/{document_number}/example",
        pdf_url=f"https://www.govinfo.gov/content/pkg/FR-2026-06-18/pdf/{document_number}.pdf",
        public_inspection_pdf_url=None,
        agency_names=["Federal Aviation Administration"],
        excerpts=f"Airworthiness Directives; {ad_number}",
        api_snapshot=snapshot,
        content_hash=hash_json(snapshot),
        classification="ad_candidate",
        classification_confidence=0.96,
        classification_reason="fixture",
        classifier_name="fixture",
        classifier_version="0.1.0",
    )
    db.add(record)
    db.flush()
    directive = AirworthinessDirective(
        discovery_record_id=record.id,
        ad_number=ad_number,
        title=title,
        status="candidate",
        source_content_hash=record.content_hash,
        extraction_status="complete",
        review_status="approved",
    )
    db.add(directive)
    db.flush()
    output = {
        "adNumber": ad_number,
        "title": title,
        "effectiveDate": None,
        "publicationDate": "2026-06-18",
        "affectedProducts": affected_products,
        "complianceActions": compliance_actions,
        "complianceIntervals": compliance_intervals,
        "supersedesAdNumbers": [],
        "sourceUrls": {"html": record.html_url, "pdf": record.pdf_url, "publicInspectionPdf": None},
    }
    extraction = ADExtraction(
        directive_id=directive.id,
        provider_name="fixture",
        provider_version="0.1.0",
        schema_version="ad_extraction_v1",
        input_content_hash=record.content_hash,
        status="approved",
        confidence=0.91,
        output=output,
        citations=[],
        raw_response={"fixture": True},
    )
    db.add(extraction)
    db.flush()
    populate_applicability_from_extraction(db, extraction)
    return extraction
