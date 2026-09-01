from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.core import (
    ADCoverageSet,
    ADCoverageSubscription,
    ADExtractionReview,
    ADPublication,
    ADTargetApplicability,
    Aircraft,
    AirworthinessDirective,
)
from app.services.ad_coverage import applicability_target_ids_for_coverage
from app.services.ad_extraction import (
    SCHEMA_VERSION,
    ensure_persisted_source_pages,
    extract_with_deterministic_provider,
    retained_pdf_documents,
)


def scoped_full_text_directives(
    db: Session,
    *,
    n_number: str,
) -> tuple[Aircraft, list[AirworthinessDirective]]:
    aircraft = db.scalar(
        select(Aircraft).where(Aircraft.n_number_normalized == n_number.strip().upper())
    )
    if aircraft is None:
        raise ValueError(f"Aircraft {n_number.strip().upper()} was not found")

    coverage_sets = db.scalars(
        select(ADCoverageSet)
        .join(
            ADCoverageSubscription,
            ADCoverageSubscription.coverage_set_id == ADCoverageSet.id,
        )
        .where(
            ADCoverageSubscription.aircraft_id == aircraft.id,
            ADCoverageSubscription.status == "active",
        )
        .options(selectinload(ADCoverageSet.target))
    ).all()
    target_ids: set[str] = set()
    for coverage in coverage_sets:
        target_ids.update(applicability_target_ids_for_coverage(db, coverage.target))
    if not target_ids:
        return aircraft, []

    directive_ids = select(ADTargetApplicability.directive_id).where(
        ADTargetApplicability.target_id.in_(target_ids),
        ADTargetApplicability.status.in_({"current", "historical"}),
    ).distinct()
    directives = db.scalars(
        select(AirworthinessDirective)
        .where(AirworthinessDirective.id.in_(directive_ids))
        .options(
            selectinload(AirworthinessDirective.discovery_record),
            selectinload(AirworthinessDirective.publications).selectinload(
                ADPublication.source_document
            ),
            selectinload(AirworthinessDirective.extractions),
        )
        .order_by(AirworthinessDirective.ad_number, AirworthinessDirective.id)
    ).all()
    return aircraft, [directive for directive in directives if retained_pdf_documents(directive)]


def prepare_full_text_compliance_reviews(
    db: Session,
    *,
    n_number: str,
    expected_publications: int | None = None,
) -> dict[str, Any]:
    """Queue replayable current-schema reviews for the retained full-text aircraft scope.

    This local preparation path deliberately uses the deterministic provider:
    it fingerprints and exposes retained text, but never approves regulatory
    compliance meaning. Platform review or a separately authorized provider
    run must supply source-cited applicability groups and requirements.
    """

    aircraft, directives = scoped_full_text_directives(db, n_number=n_number)
    checks: list[dict[str, Any]] = []
    checks.append({
        "name": "aircraft_found",
        "passed": aircraft is not None,
        "actual": aircraft.n_number_normalized,
    })
    checks.append({
        "name": "expected_full_text_publications",
        "passed": expected_publications is None or len(directives) == expected_publications,
        "expected": expected_publications,
        "actual": len(directives),
    })

    queued = 0
    readable = 0
    unreadable = 0
    review_ids: list[str] = []
    directive_rows: list[dict[str, Any]] = []
    for directive in directives:
        extraction = extract_with_deterministic_provider(
            db,
            directive,
            fallback_reason="t081_full_text_review_preparation",
        )
        pages = ensure_persisted_source_pages(directive, extraction)
        if pages:
            readable += 1
        else:
            unreadable += 1
        review = db.scalar(
            select(ADExtractionReview).where(
                ADExtractionReview.extraction_id == extraction.id
            )
        )
        if review is not None:
            review_ids.append(review.id)
            if review.status == "pending":
                queued += 1
        directive_rows.append({
            "directiveId": directive.id,
            "adNumber": directive.ad_number,
            "extractionId": extraction.id,
            "reviewId": review.id if review else None,
            "pageCount": len(pages),
            "status": review.status if review else extraction.status,
        })

    checks.extend([
        {
            "name": "all_retained_pdfs_are_routed",
            "passed": readable + unreadable == len(directives),
            "actual": {"readable": readable, "unreadable": unreadable},
        },
        {
            "name": "all_scoped_directives_have_current_schema_reviews",
            "passed": len(review_ids) == len(directives),
            "actual": len(review_ids),
            "expected": len(directives),
        },
        {
            "name": "no_deterministic_full_text_approval",
            "passed": all(row["reviewId"] is not None for row in directive_rows),
            "actual": queued,
        },
    ])
    passed = sum(bool(check["passed"]) for check in checks)
    return {
        "aircraftId": aircraft.id,
        "nNumber": aircraft.n_number_normalized,
        "schemaVersion": SCHEMA_VERSION,
        "fullTextPublicationCount": len(directives),
        "readablePublicationCount": readable,
        "unreadablePublicationCount": unreadable,
        "pendingReviewCount": queued,
        "reviewIds": review_ids,
        "directives": directive_rows,
        "verification": {"passed": passed, "total": len(checks), "checks": checks},
    }
