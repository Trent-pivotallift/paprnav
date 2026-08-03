from __future__ import annotations

from typing import Any

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.core import (
    ADCoverageSet,
    ADCoverageSubscription,
    ADDiscoveryRecord,
    ADExtraction,
    ADExtractionReview,
    ADTargetApplicability,
    AirworthinessDirective,
    ProductEvent,
)
from app.services.ad_discovery import FederalRegisterSearchResult, discover_federal_register_ads
from app.services.ad_extraction import process_pending_ad_extractions
from app.services.ad_matching import match_aircraft_ads
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

    aircraft = demo_data["aircraft"]
    initial_stats = match_aircraft_ads(db_session, aircraft.id)
    assert initial_stats["directives_seen"] == 0

    login(client, "owner.test@paprnav.local")
    assert client.get("/api/v1/ads/extraction-reviews").status_code == 403

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
    reviews = list_response.json()["reviews"]
    assert len(reviews) == 1
    assert reviews[0]["directive"]["federalRegisterDocumentNumber"] == "2026-12052"
    assert reviews[0]["extraction"]["inputContentHash"] == review.extraction.input_content_hash
    assert "Airworthiness Directives" in reviews[0]["sourceText"]

    edited_output: dict[str, Any] = reviews[0]["proposedOutput"]
    edited_output["affectedProducts"] = []
    empty_applicability = client.post(
        f"/api/v1/ads/extraction-reviews/{reviews[0]['id']}/decision",
        json={
            "decision": "edited",
            "output": edited_output,
            "notes": "Applicability could not be attributed.",
        },
    )
    assert empty_applicability.status_code == 422
    assert "at least one attributable product" in empty_applicability.json()["detail"]

    edited_output["affectedProducts"] = ["Cessna 172R"]
    decision_response = client.post(
        f"/api/v1/ads/extraction-reviews/{reviews[0]['id']}/decision",
        json={"decision": "edited", "output": edited_output, "notes": "Confirmed from source PDF."},
    )
    assert decision_response.status_code == 200
    decided = decision_response.json()["review"]
    assert decided["status"] == "edited"
    assert decided["decisionOutput"]["affectedProducts"] == ["Cessna 172R"]
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
    assert "applicability_disagreement" in extraction.raw_response["reviewReasons"]
    assert "provider_uncertainty" in extraction.raw_response["reviewReasons"]
    assert db_session.scalar(select(ADExtractionReview)) is not None
    assert db_session.scalars(select(ADTargetApplicability)).all() == []


def test_provider_backed_extraction_can_approve_valid_consistent_output(db_session: Session) -> None:
    discover_federal_register_ads(db_session, client=FakeFederalRegisterClient())
    provider = FakeProviderBackedExtractor(output=provider_output())

    stats = process_pending_ad_extractions(db_session, llm_provider=provider)

    assert stats["seen"] == 1
    assert stats["approved"] == 1
    extraction = db_session.scalar(select(ADExtraction).where(ADExtraction.provider_name == provider.provider_name))
    assert extraction is not None
    assert extraction.status == "approved"
    assert extraction.raw_response["reviewReasons"] == []
    assert db_session.scalar(select(ADExtractionReview)) is None
    applicabilities = db_session.scalars(select(ADTargetApplicability)).all()
    assert len(applicabilities) == 1


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
    return {
        "adNumber": "2026-12-01",
        "title": "Airworthiness Directives; Airbus Helicopters",
        "effectiveDate": None,
        "publicationDate": "2026-06-16",
        "affectedProducts": affected_products if affected_products is not None else ["Airbus Helicopters"],
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
    }
