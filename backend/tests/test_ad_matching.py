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
)
from app.services.ad_discovery import hash_json
from app.services.ad_matching import match_aircraft_ads
from tests.conftest import login


def test_ad_matching_creates_evidence_and_unresolved_review_tasks(
    client: TestClient,
    db_session: Session,
    demo_data: dict[str, object],
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

    stats = match_aircraft_ads(db_session, aircraft.id)

    assert stats["directives_seen"] == 3
    assert stats["matched"] == 2
    assert stats["unresolved"] == 1
    one_time_match = db_session.scalar(
        select(ADMatchResult).where(ADMatchResult.status == "candidate_satisfied", ADMatchResult.match_type == "one_time")
    )
    assert one_time_match is not None
    assert one_time_match.confidence > 0.7
    assert db_session.scalar(select(ADMatchEvidence).where(ADMatchEvidence.match_result_id == one_time_match.id)) is not None

    recurring_match = db_session.scalar(select(ADMatchResult).where(ADMatchResult.match_type == "simple_recurring"))
    assert recurring_match is not None
    assert recurring_match.status == "candidate_satisfied"

    adjudication_count = len(db_session.scalars(select(ADMatchAdjudication)).all())
    assert adjudication_count == 1

    login(client, "owner.test@paprnav.local")
    response = client.get(f"/api/v1/ads/aircraft/{aircraft.id}/matches")
    assert response.status_code == 200
    matches = response.json()["matches"]
    assert len(matches) == 3
    candidate = next(match for match in matches if match["status"] == "candidate_satisfied")
    assert candidate["evidence"][0]["logbookEntryId"]
    assert "logbook evidence" in candidate["rationale"]


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
    return extraction
