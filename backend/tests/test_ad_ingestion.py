from typing import Any

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.core import ADDiscoveryRecord, ADExtractionReview, AirworthinessDirective
from app.services.ad_discovery import FederalRegisterSearchResult, discover_federal_register_ads
from app.services.ad_extraction import process_pending_ad_extractions
from tests.conftest import login


class FakeFederalRegisterClient:
    def search_airworthiness_directive_candidates(self, page: int = 1, per_page: int = 20) -> FederalRegisterSearchResult:
        _ = page
        _ = per_page
        return FederalRegisterSearchResult(
            description="Federal Aviation Administration Rule documents matching Airworthiness Directives",
            count=2,
            total_pages=1,
            next_page_url=None,
            results=[candidate_document(), non_ad_rule_document()],
            raw_response={"results": [candidate_document(), non_ad_rule_document()]},
        )


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
) -> None:
    discover_federal_register_ads(db_session, client=FakeFederalRegisterClient())

    extraction_stats = process_pending_ad_extractions(db_session)

    assert extraction_stats["seen"] == 1
    assert extraction_stats["review_queued"] == 1
    review = db_session.scalar(select(ADExtractionReview))
    assert review is not None
    assert review.status == "pending"
    assert review.extraction.provider_name == "deterministic_ad_extractor"
    assert review.extraction.schema_version == "ad_extraction_v1"

    login(client, "owner.test@paprnav.local")
    list_response = client.get("/api/v1/ads/extraction-reviews")
    assert list_response.status_code == 200
    reviews = list_response.json()["reviews"]
    assert len(reviews) == 1
    assert reviews[0]["directive"]["federalRegisterDocumentNumber"] == "2026-12052"
    assert reviews[0]["extraction"]["inputContentHash"] == review.extraction.input_content_hash
    assert "Airworthiness Directives" in reviews[0]["sourceText"]

    edited_output: dict[str, Any] = reviews[0]["proposedOutput"]
    edited_output["affectedProducts"] = ["Airbus Helicopters Model H160-B"]
    decision_response = client.post(
        f"/api/v1/ads/extraction-reviews/{reviews[0]['id']}/decision",
        json={"decision": "edited", "output": edited_output, "notes": "Confirmed from source PDF."},
    )
    assert decision_response.status_code == 200
    decided = decision_response.json()["review"]
    assert decided["status"] == "edited"
    assert decided["decisionOutput"]["affectedProducts"] == ["Airbus Helicopters Model H160-B"]

    db_session.refresh(review)
    assert review.extraction.status == "approved"
    assert review.extraction.directive.review_status == "approved"
    assert review.extraction.directive.extraction_status == "complete"


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
