from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.core import (
    ADExtraction,
    ADExtractionReview,
    ADPublication,
    ADTargetApplicability,
    AirworthinessDirective,
    User,
)
from app.services.ad_extraction import (
    SCHEMA_VERSION,
    bounded_source_document_pages,
    extraction_approval_blockers,
    extraction_input_hash,
    persisted_source_pages,
    structured_output_hash,
)
from app.services.ad_applicability import populate_applicability_from_extraction
from app.services.ad_recurrence import materialize_requirements_from_extraction


def extraction_has_signed_release(extraction: ADExtraction) -> bool:
    if extraction.status != "approved" or extraction.schema_version != SCHEMA_VERSION:
        return False
    if extraction.input_content_hash != extraction_input_hash(extraction.directive):
        return False
    review = next(
        (
            item for item in extraction.reviews
            if item.status in {"approved", "edited"}
            and item.decision in {"approved", "edited"}
        ),
        None,
    )
    if (
        review is None
        or review.reviewer is None
        or review.reviewer.status != "active"
        or review.reviewed_at is None
        or review.decision_output is None
        or structured_output_hash(extraction.output)
        != structured_output_hash(review.decision_output)
    ):
        return False
    if not any(
        membership.status == "active" and membership.role == "platform_admin"
        for membership in review.reviewer.memberships
    ):
        return False
    cached, pages = persisted_source_pages(extraction.directive, extraction)
    if not cached:
        return False
    scoped_pages = bounded_source_document_pages(
        pages,
        ad_number=extraction.directive.ad_number,
        title=extraction.directive.title,
    )
    return not extraction_approval_blockers(
        extraction,
        extraction.output,
        scoped_pages,
    )


def released_signed_extractions(db: Session) -> list[ADExtraction]:
    candidates = db.scalars(
        select(ADExtraction)
        .where(
            ADExtraction.status == "approved",
            ADExtraction.schema_version == SCHEMA_VERSION,
        )
        .options(
            selectinload(ADExtraction.reviews)
            .selectinload(ADExtractionReview.reviewer)
            .selectinload(User.memberships),
            selectinload(ADExtraction.directive)
            .selectinload(AirworthinessDirective.discovery_record),
            selectinload(ADExtraction.directive)
            .selectinload(AirworthinessDirective.publications)
            .selectinload(ADPublication.source_document),
            selectinload(ADExtraction.directive)
            .selectinload(AirworthinessDirective.target_applicabilities)
            .selectinload(ADTargetApplicability.target),
            selectinload(ADExtraction.directive)
            .selectinload(AirworthinessDirective.superseded_by_edges),
        )
        .order_by(ADExtraction.created_at.desc(), ADExtraction.id.desc())
    ).all()
    current_by_directive: dict[str, ADExtraction] = {}
    for extraction in candidates:
        if not extraction_has_signed_release(extraction):
            continue
        # Every consumer receives relational rows deterministically reconciled
        # from the signed packet. Out-of-band row mutations cannot influence
        # search, matching, or due state.
        populate_applicability_from_extraction(db, extraction)
        materialize_requirements_from_extraction(db, extraction)
        db.flush()
        current_by_directive.setdefault(extraction.directive_id, extraction)
    return list(current_by_directive.values())


def applicability_belongs_to_release(
    applicability: ADTargetApplicability | None,
    extraction: ADExtraction,
) -> bool:
    return (
        applicability is not None
        and applicability.status == "current"
        and applicability.source_extraction_id == extraction.id
    )


def released_extraction_for_directive(
    directive: AirworthinessDirective,
) -> ADExtraction | None:
    for extraction in sorted(
        directive.extractions,
        key=lambda item: (item.created_at, item.id),
        reverse=True,
    ):
        if extraction_has_signed_release(extraction):
            return extraction
    return None
