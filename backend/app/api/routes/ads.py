from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response
from sqlalchemy import or_, select, update
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_current_user
from app.api.routes.admin import ensure_platform_admin
from app.api.routes.aircraft import (
    ensure_maintenance_review_access,
    get_visible_aircraft_or_404,
)
from app.core.config import get_settings
from app.db.session import get_db
from app.models.core import (
    ADDiscoveryRecord,
    ADCoverageSet,
    ADCoverageSubscription,
    ADExtraction,
    ADExtractionReview,
    ADExtractionReviewDecision,
    ADPublication,
    ADSourceDocument,
    ADMatchAdjudication,
    ADMatchDueStateLink,
    ADMatchEvidence,
    ADMatchResult,
    ADTargetApplicability,
    AircraftADDueState,
    AirworthinessDirective,
    ApplicabilityTarget,
    LogbookEntry,
    ProductEvent,
    User,
)
from app.schemas.ads import (
    ADDiscoveryRecordResponse,
    ADExtractionResponse,
    ADExtractionReviewListResponse,
    ADExtractionReviewResponse,
    ADEvidenceFragmentCreateRequest,
    ADEvidenceFragmentResponse,
    ADProposalProvenanceResponse,
    ADSourcePageEvidenceResponse,
    ADSourcePageMaterializeRequest,
    ADSourceDocumentResponse,
    ADMatchAdjudicationResponse,
    ADMatchAdjudicationDecisionRequest,
    ADMatchAdjudicationDecisionResponse,
    ADMatchApplicabilityResponse,
    ADMatchComponentResponse,
    ADMatchEvidenceResponse,
    ADMatchResultListResponse,
    ADMatchResultResponse,
    ADMatchPublicationResponse,
    ADMatchTargetResponse,
    ADDueStateResponse,
    ADReviewDecisionRequest,
    ADReviewDecisionResponse,
    ADDirectiveApplicabilityTargetResponse,
    AirworthinessDirectiveResponse,
)
from app.services.ad_extraction import (
    bounded_source_document_pages,
    derive_compliance_action_summaries,
    ensure_persisted_source_pages,
    extraction_approval_blockers,
    extraction_input_hash,
    official_ad_number,
    persisted_source_pages,
    source_evidence_status,
    structured_output_hash,
    retained_document_bytes_match,
    verified_retained_document_bytes,
)
from app.services.ad_applicability import populate_applicability_from_extraction
from app.services.ad_coverage import summarize_aircraft_coverage_status
from app.services.ad_coverage import resolve_aircraft_ad_coverage
from app.services.ad_matching import (
    ALGORITHM_NAME,
    ALGORITHM_VERSION,
    invalidate_aircraft_match_results,
)
from app.services.ad_recurrence import materialize_requirements_from_extraction
from app.services.ad_release import (
    extraction_has_signed_release,
    released_extraction_for_directive,
    released_signed_extractions,
)
from app.services.ad_extraction import full_text_pages_for_extraction
from app.services.ad_evidence import (
    ADEvidenceError,
    admit_evidence_fragment,
    get_materialized_source_page,
    materialize_source_page,
)
from app.services.ad_recurrence import due_state_payload
from app.services.installed_components import component_display_name
from app.services.observability import record_product_event, record_workflow_status
from app.services.storage import safe_filename

router = APIRouter(prefix="/api/v1/ads", tags=["airworthiness-directives"])


def ensure_ad_extraction_reviewer(user: User) -> None:
    ensure_platform_admin(user)


def is_platform_admin(user: User) -> bool:
    return any(
        membership.status == "active" and membership.role == "platform_admin"
        for membership in user.memberships
    )


@router.get("/source-documents/{source_document_id}/content")
def open_retained_source_document(
    source_document_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ensure_ad_extraction_reviewer(current_user)
    document = db.scalar(
        select(ADSourceDocument).where(ADSourceDocument.id == source_document_id)
    )
    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Retained AD source document not found")
    filename = safe_filename(Path(document.storage_key).name or f"{document.id}.pdf")
    headers = {"Content-Disposition": f"inline; filename*=UTF-8''{quote(filename)}"}
    settings = get_settings()
    try:
        payload = verified_retained_document_bytes(document, settings=settings)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Retained AD source document hash mismatch",
        ) from exc
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Retained AD source document not found") from exc
    return Response(
        content=payload,
        media_type=document.media_type or "application/octet-stream",
        headers=headers,
    )


def evidence_http_error(exc: ADEvidenceError) -> HTTPException:
    if exc.code in {"not_found", "page_not_materialized"}:
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    if exc.code == "source_unavailable":
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    if exc.code in {
        "source_hash_mismatch", "rendition_hash_mismatch", "page_text_hash_mismatch",
        "fragment_not_admitted",
    }:
        return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    return HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc))


@router.get(
    "/source-documents/{source_document_id}/pages/{page_number}",
    response_model=ADSourcePageEvidenceResponse,
)
def get_retained_source_page_evidence(
    source_document_id: str,
    page_number: int,
    directive_id: str = Query(alias="directiveId"),
    expected_source_content_hash: str = Query(
        alias="expectedSourceContentHash", min_length=64, max_length=64
    ),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ADSourcePageEvidenceResponse:
    ensure_ad_extraction_reviewer(current_user)
    try:
        rendition, text_version = get_materialized_source_page(
            db,
            directive_id=directive_id,
            source_document_id=source_document_id,
            page_number=page_number,
            expected_source_content_hash=expected_source_content_hash,
        )
    except ADEvidenceError as exc:
        raise evidence_http_error(exc) from exc
    return ADSourcePageEvidenceResponse(
        sourceDocumentId=source_document_id,
        directiveId=directive_id,
        sourceContentHash=rendition.source_content_hash,
        pageNumber=rendition.page_number,
        pageTextVersionId=text_version.id,
        pageTextHash=text_version.text_hash,
        pageText=text_version.page_text,
        renditionId=rendition.id,
        renditionHash=rendition.rendition_hash,
        renditionMediaType=rendition.media_type,
        renditionWidthPx=rendition.width_px,
        renditionHeightPx=rendition.height_px,
    )


@router.post(
    "/source-documents/{source_document_id}/pages/{page_number}/materialization",
    response_model=ADSourcePageEvidenceResponse,
)
def materialize_retained_source_page_evidence(
    source_document_id: str,
    page_number: int,
    request: ADSourcePageMaterializeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ADSourcePageEvidenceResponse:
    ensure_ad_extraction_reviewer(current_user)
    try:
        rendition, text_version = materialize_source_page(
            db,
            directive_id=request.directiveId,
            source_document_id=source_document_id,
            page_number=page_number,
            expected_source_content_hash=request.expectedSourceContentHash,
        )
    except ADEvidenceError as exc:
        raise evidence_http_error(exc) from exc
    db.commit()
    return ADSourcePageEvidenceResponse(
        sourceDocumentId=source_document_id,
        directiveId=request.directiveId,
        sourceContentHash=rendition.source_content_hash,
        pageNumber=rendition.page_number,
        pageTextVersionId=text_version.id,
        pageTextHash=text_version.text_hash,
        pageText=text_version.page_text,
        renditionId=rendition.id,
        renditionHash=rendition.rendition_hash,
        renditionMediaType=rendition.media_type,
        renditionWidthPx=rendition.width_px,
        renditionHeightPx=rendition.height_px,
    )


@router.post(
    "/source-documents/{source_document_id}/fragments",
    response_model=ADEvidenceFragmentResponse,
)
def create_retained_source_evidence_fragment(
    source_document_id: str,
    request: ADEvidenceFragmentCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ADEvidenceFragmentResponse:
    ensure_ad_extraction_reviewer(current_user)
    try:
        fragment, created = admit_evidence_fragment(
            db,
            directive_id=request.directiveId,
            source_document_id=source_document_id,
            page_number=request.pageNumber,
            expected_source_content_hash=request.expectedSourceContentHash,
            expected_page_text_hash=request.expectedPageTextHash,
            character_start=request.characterStart,
            character_end=request.characterEnd,
            actor=current_user,
            reason=request.reason,
            paragraph_locator=request.paragraphLocator,
            table_locator=request.tableLocator,
            row_locator=request.rowLocator,
            note_locator=request.noteLocator,
        )
    except ADEvidenceError as exc:
        raise evidence_http_error(exc) from exc
    db.commit()
    db.refresh(fragment)
    return ADEvidenceFragmentResponse(
        id=fragment.id,
        directiveId=fragment.directive_id,
        sourceDocumentId=fragment.source_document_id,
        sourceContentHash=fragment.source_content_hash,
        pageTextVersionId=fragment.page_text_version_id,
        pageStart=fragment.page_start,
        pageEnd=fragment.page_end,
        characterStart=fragment.character_start,
        characterEnd=fragment.character_end,
        paragraphLocator=fragment.paragraph_locator,
        tableLocator=fragment.table_locator,
        rowLocator=fragment.row_locator,
        noteLocator=fragment.note_locator,
        exactText=fragment.exact_text,
        fragmentHash=fragment.fragment_hash,
        createdByUserId=fragment.created_by_user_id,
        createdAt=fragment.created_at,
        created=created,
    )


@router.get("/discovery-records", response_model=list[ADDiscoveryRecordResponse])
def list_discovery_records(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[ADDiscoveryRecordResponse]:
    _ = current_user
    records = db.scalars(select(ADDiscoveryRecord).order_by(ADDiscoveryRecord.publication_date.desc())).all()
    return [serialize_discovery_record(record) for record in records]


@router.get("/directives", response_model=list[AirworthinessDirectiveResponse])
def list_directives(
    q: str | None = Query(default=None, max_length=200),
    ad_number: str | None = Query(default=None, max_length=64),
    directive_status: str | None = Query(default=None, alias="status", max_length=64),
    product_type: str | None = Query(default=None, alias="productType", max_length=64),
    manufacturer: str | None = Query(default=None, max_length=255),
    model: str | None = Query(default=None, max_length=255),
    include_unreviewed: bool = Query(default=False, alias="includeUnreviewed"),
    limit: int = Query(default=200, ge=1, le=500),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[AirworthinessDirectiveResponse]:
    if include_unreviewed and not is_platform_admin(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Paprnav administrator access required for unreleased directives",
        )
    statement = select(AirworthinessDirective).options(
        selectinload(AirworthinessDirective.discovery_record),
        selectinload(AirworthinessDirective.extractions)
        .selectinload(ADExtraction.reviews)
        .selectinload(ADExtractionReview.reviewer)
        .selectinload(User.memberships),
        selectinload(AirworthinessDirective.publications).selectinload(
            ADPublication.source_document
        ),
        selectinload(AirworthinessDirective.target_applicabilities).selectinload(
            ADTargetApplicability.target
        ),
    )
    if not include_unreviewed:
        statement = statement.where(AirworthinessDirective.review_status == "approved")
    if q and include_unreviewed:
        term = f"%{q.strip()}%"
        statement = statement.where(
            or_(
                AirworthinessDirective.title.ilike(term),
                AirworthinessDirective.ad_number.ilike(term),
                current_target_exists(search_term=term),
            )
        )
    if ad_number:
        normalized_number = ad_number.upper().removeprefix("AD ").strip()
        statement = statement.where(AirworthinessDirective.ad_number.ilike(f"%{normalized_number}%"))
    if directive_status:
        statement = statement.where(AirworthinessDirective.status == directive_status)
    if (product_type or manufacturer or model) and include_unreviewed:
        statement = statement.where(current_target_exists(
            product_type=product_type,
            manufacturer=manufacturer,
            model=model,
        ))
    ordered = statement.order_by(
        AirworthinessDirective.ad_number.desc(),
        AirworthinessDirective.created_at.desc(),
    )
    if include_unreviewed:
        ordered = ordered.limit(limit)
    directives = db.scalars(ordered).all()
    if not include_unreviewed:
        released_by_directive = {
            extraction.directive_id: extraction
            for extraction in released_signed_extractions(db)
        }
        directives = [
            directive for directive in directives
            if directive.id in released_by_directive
        ]
        directives = [
            directive
            for directive in directives
            if directive_has_verified_release_evidence(directive)
            and released_directive_matches_query(
                directive,
                q=q,
                product_type=product_type,
                manufacturer=manufacturer,
                model=model,
            )
        ][:limit]
    return [serialize_directive(directive) for directive in directives]


def current_target_exists(
    *,
    search_term: str | None = None,
    product_type: str | None = None,
    manufacturer: str | None = None,
    model: str | None = None,
):
    target_query = (
        select(ADTargetApplicability.id)
        .join(
            ApplicabilityTarget,
            ApplicabilityTarget.id == ADTargetApplicability.target_id,
        )
        .where(
            ADTargetApplicability.directive_id == AirworthinessDirective.id,
            ADTargetApplicability.status == "current",
        )
    )
    if search_term:
        target_query = target_query.where(or_(
            ApplicabilityTarget.make.ilike(search_term),
            ApplicabilityTarget.model.ilike(search_term),
            ApplicabilityTarget.product_type.ilike(search_term),
            ApplicabilityTarget.product_subtype.ilike(search_term),
        ))
    if product_type:
        target_query = target_query.where(ApplicabilityTarget.product_type.ilike(product_type.strip()))
    if manufacturer:
        target_query = target_query.where(ApplicabilityTarget.make.ilike(f"%{manufacturer.strip()}%"))
    if model:
        target_query = target_query.where(ApplicabilityTarget.model.ilike(f"%{model.strip()}%"))
    return target_query.exists()


def directive_has_verified_release_evidence(directive: AirworthinessDirective) -> bool:
    return released_extraction_for_directive(directive) is not None


def released_directive_matches_query(
    directive: AirworthinessDirective,
    *,
    q: str | None,
    product_type: str | None,
    manufacturer: str | None,
    model: str | None,
) -> bool:
    extraction = released_extraction_for_directive(directive)
    if extraction is None:
        return False
    targets = [
        item.target
        for item in directive.target_applicabilities
        if item.status == "current"
        and item.source_extraction_id == extraction.id
        and item.target is not None
    ]
    if q:
        needle = q.strip().lower()
        searchable = [directive.title, directive.ad_number]
        searchable.extend(
            value
            for target in targets
            for value in (
                target.make,
                target.model,
                target.product_type,
                target.product_subtype,
            )
        )
        if not any(needle in str(value or "").lower() for value in searchable):
            return False
    if product_type and not any(
        target.product_type.lower() == product_type.strip().lower()
        for target in targets
    ):
        return False
    if manufacturer and not any(
        manufacturer.strip().lower() in str(target.make or "").lower()
        for target in targets
    ):
        return False
    if model and not any(
        model.strip().lower() in str(target.model or "").lower()
        for target in targets
    ):
        return False
    return True


@router.get("/extraction-reviews", response_model=ADExtractionReviewListResponse)
def list_extraction_reviews(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=1, ge=1, le=20),
    review_id: str | None = Query(default=None, alias="reviewId", max_length=64),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ADExtractionReviewListResponse:
    ensure_ad_extraction_reviewer(current_user)
    all_reviews = db.scalars(
        select(ADExtractionReview)
        .options(
            selectinload(ADExtractionReview.extraction)
            .selectinload(ADExtraction.directive)
            .selectinload(AirworthinessDirective.discovery_record),
            selectinload(ADExtractionReview.extraction)
            .selectinload(ADExtraction.directive)
            .selectinload(AirworthinessDirective.publications)
            .selectinload(ADPublication.source_document),
        )
        .order_by(ADExtractionReview.created_at.desc(), ADExtractionReview.id)
    ).all()
    review_statuses = [review.status for review in all_reviews]
    current_offset = offset
    if review_id:
        matching_index = next(
            (index for index, review in enumerate(all_reviews) if review.id == review_id),
            None,
        )
        selected_models = (
            [all_reviews[matching_index]]
            if matching_index is not None
            else []
        )
        current_offset = matching_index or 0
    else:
        selected_models = all_reviews[offset:offset + limit]
    # Exact retained-byte/text verification is intentionally limited to the
    # selected page. Re-parsing every retained Federal Register PDF just to
    # render queue counters made the reviewer UI unavailable. Aggregate counts
    # are triage hints derived from the persisted source cache; the selected
    # review, approval action, and release gate all re-derive exact source text.
    selected_reviews = [serialize_review(review) for review in selected_models]
    aggregate_states = [review_queue_candidate_state(review) for review in all_reviews]
    verified_count = sum(state[0] for state in aggregate_states)
    return ADExtractionReviewListResponse(
        reviews=selected_reviews,
        currentOffset=current_offset,
        totalCount=len(review_statuses),
        pendingCount=sum(review_status == "pending" for review_status in review_statuses),
        reviewedCount=sum(review_status != "pending" for review_status in review_statuses),
        verifiedCount=verified_count,
        quarantinedCount=len(all_reviews) - verified_count,
        approvalReadyCount=sum(state[1] for state in aggregate_states),
    )


@router.get("/aircraft/{aircraft_id}/matches", response_model=ADMatchResultListResponse)
def list_aircraft_matches(
    aircraft_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ADMatchResultListResponse:
    get_visible_aircraft_or_404(db, current_user, aircraft_id)
    matches = db.scalars(
        select(ADMatchResult)
        .where(
            ADMatchResult.aircraft_id == aircraft_id,
            ADMatchResult.algorithm_name == ALGORITHM_NAME,
            ADMatchResult.algorithm_version == ALGORITHM_VERSION,
            ADMatchResult.is_current.is_(True),
        )
        .options(
            selectinload(ADMatchResult.aircraft),
            selectinload(ADMatchResult.directive).selectinload(AirworthinessDirective.discovery_record),
            selectinload(ADMatchResult.directive).selectinload(AirworthinessDirective.publications),
            selectinload(ADMatchResult.directive).selectinload(AirworthinessDirective.extractions),
            selectinload(ADMatchResult.extraction)
            .selectinload(ADExtraction.reviews)
            .selectinload(ADExtractionReview.reviewer)
            .selectinload(User.memberships),
            selectinload(ADMatchResult.directive)
            .selectinload(AirworthinessDirective.publications)
            .selectinload(ADPublication.source_document),
            selectinload(ADMatchResult.installed_component),
            selectinload(ADMatchResult.target_applicability).selectinload(ADTargetApplicability.target),
            selectinload(ADMatchResult.target_applicability).selectinload(ADTargetApplicability.source_publication),
            selectinload(ADMatchResult.due_state).selectinload(AircraftADDueState.requirement),
            selectinload(ADMatchResult.due_state_links)
            .selectinload(ADMatchDueStateLink.due_state)
            .selectinload(AircraftADDueState.requirement),
            selectinload(ADMatchResult.evidence_links).selectinload(ADMatchEvidence.logbook_entry).selectinload(LogbookEntry.logbook_section),
            selectinload(ADMatchResult.adjudication),
        )
        .order_by(ADMatchResult.status.desc(), ADMatchResult.confidence.desc(), ADMatchResult.created_at.desc())
    ).all()
    matches = [
        match for match in matches
        if extraction_has_signed_release(match.extraction)
        and match_has_signed_materialization_chain(match)
    ]
    latest_matching_event = db.scalar(
        select(ProductEvent)
        .where(
            ProductEvent.aircraft_id == aircraft_id,
            ProductEvent.event_type.in_(
                {"ad_matching_completed", "ad_matching_invalidated"}
            ),
        )
        .order_by(ProductEvent.event_time.desc(), ProductEvent.created_at.desc())
        .limit(1)
    )
    completion_properties = (
        latest_matching_event.properties_json
        if latest_matching_event and latest_matching_event.properties_json
        else {}
    )
    completed_with_current_version = (
        latest_matching_event is not None
        and latest_matching_event.event_type == "ad_matching_completed"
        and completion_properties.get("algorithm_name") == ALGORITHM_NAME
        and completion_properties.get("algorithm_version") == ALGORITHM_VERSION
    )
    matching_was_invalidated = (
        latest_matching_event is not None
        and latest_matching_event.event_type == "ad_matching_invalidated"
    )
    has_stale_results = db.scalar(
        select(ADMatchResult.id)
        .where(
            ADMatchResult.aircraft_id == aircraft_id,
            ADMatchResult.algorithm_name == ALGORITHM_NAME,
            (
                (ADMatchResult.algorithm_version != ALGORITHM_VERSION)
                | ADMatchResult.is_current.is_(False)
            ),
        )
        .limit(1)
    ) is not None
    if matches or completed_with_current_version:
        matcher_status = "current"
    elif matching_was_invalidated or has_stale_results:
        matcher_status = "pending_recomputation"
    else:
        matcher_status = "not_run"
    coverage = summarize_aircraft_coverage_status(db, aircraft_id)
    return ADMatchResultListResponse(
        matches=[serialize_match_result(match) for match in matches],
        matcherStatus=matcher_status,
        algorithmName=ALGORITHM_NAME,
        algorithmVersion=ALGORITHM_VERSION,
        reprocessingRequired=matcher_status == "pending_recomputation",
        **coverage,
    )


def match_has_signed_materialization_chain(match: ADMatchResult) -> bool:
    applicability = match.target_applicability
    if (
        applicability is None
        or applicability.status != "current"
        or applicability.source_extraction_id != match.extraction_id
    ):
        return False
    due_states = [
        link.due_state for link in match.due_state_links
        if link.due_state is not None
    ]
    if match.due_state is not None and all(
        state.id != match.due_state.id for state in due_states
    ):
        due_states.append(match.due_state)
    for state in due_states:
        requirement = state.requirement
        if (
            not state.is_current
            or state.aircraft_id != match.aircraft_id
            or state.installed_component_id != match.installed_component_id
            or requirement is None
            or requirement.status != "current"
            or requirement.source_extraction_id != match.extraction_id
            or requirement.target_applicability_id != applicability.id
        ):
            return False
    return True


@router.post("/matches/{match_id}/adjudication", response_model=ADMatchAdjudicationDecisionResponse)
def decide_match_adjudication(
    match_id: str,
    payload: ADMatchAdjudicationDecisionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ADMatchAdjudicationDecisionResponse:
    allowed = {"satisfied", "not_satisfied", "not_applicable", "needs_more_info", "deferred"}
    if payload.decision not in allowed:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Unsupported adjudication decision")
    match = db.scalar(
        select(ADMatchResult)
        .where(ADMatchResult.id == match_id)
        .options(
            selectinload(ADMatchResult.aircraft),
            selectinload(ADMatchResult.directive).selectinload(AirworthinessDirective.discovery_record),
            selectinload(ADMatchResult.directive).selectinload(AirworthinessDirective.publications),
            selectinload(ADMatchResult.installed_component),
            selectinload(ADMatchResult.target_applicability).selectinload(ADTargetApplicability.target),
            selectinload(ADMatchResult.target_applicability).selectinload(ADTargetApplicability.source_publication),
            selectinload(ADMatchResult.evidence_links).selectinload(ADMatchEvidence.logbook_entry).selectinload(LogbookEntry.logbook_section),
            selectinload(ADMatchResult.adjudication),
        )
    )
    if not match:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="AD match not found")
    aircraft = get_visible_aircraft_or_404(db, current_user, match.aircraft_id)
    ensure_maintenance_review_access(db, aircraft, current_user)
    if not match.is_current:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="AD match is stale and must be recomputed before adjudication",
        )
    adjudication = match.adjudication
    if adjudication is None:
        adjudication = ADMatchAdjudication(match_result_id=match.id)
        db.add(adjudication)
        db.flush()
        match.adjudication = adjudication
    adjudication.status = "reviewed"
    adjudication.decision = payload.decision
    adjudication.reviewer_user_id = current_user.id
    adjudication.notes = payload.notes
    adjudication.future_improvement_tags = payload.futureImprovementTags
    adjudication.reviewed_at = datetime.now(timezone.utc)
    match.status = f"adjudicated_{payload.decision}"
    record_product_event(
        db,
        event_type="ad_match_adjudicated",
        subject_type="ad_match",
        subject_id=match.id,
        actor=current_user,
        aircraft_id=match.aircraft_id,
        properties={
            "decision": payload.decision,
            "tags": payload.futureImprovementTags,
            "matchStatus": match.status,
        },
    )
    record_workflow_status(
        db,
        workflow_type="hitl_adjudication",
        workflow_id=adjudication.id,
        previous_status="pending",
        new_status="reviewed",
        reason=payload.decision,
        actor_type="reviewer",
        actor=current_user,
    )
    db.commit()
    match = db.scalar(
        select(ADMatchResult)
        .where(ADMatchResult.id == match_id)
        .options(
            selectinload(ADMatchResult.aircraft),
            selectinload(ADMatchResult.directive).selectinload(AirworthinessDirective.discovery_record),
            selectinload(ADMatchResult.directive).selectinload(AirworthinessDirective.publications),
            selectinload(ADMatchResult.installed_component),
            selectinload(ADMatchResult.target_applicability).selectinload(ADTargetApplicability.target),
            selectinload(ADMatchResult.target_applicability).selectinload(ADTargetApplicability.source_publication),
            selectinload(ADMatchResult.evidence_links).selectinload(ADMatchEvidence.logbook_entry).selectinload(LogbookEntry.logbook_section),
            selectinload(ADMatchResult.adjudication),
        )
    )
    return ADMatchAdjudicationDecisionResponse(match=serialize_match_result(match))


@router.post("/extraction-reviews/{review_id}/decision", response_model=ADReviewDecisionResponse)
def decide_extraction_review(
    review_id: str,
    payload: ADReviewDecisionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ADReviewDecisionResponse:
    ensure_ad_extraction_reviewer(current_user)
    review = db.scalar(
        select(ADExtractionReview)
        .where(ADExtractionReview.id == review_id)
        .with_for_update()
        .options(
            selectinload(ADExtractionReview.extraction)
            .selectinload(ADExtraction.directive)
            .selectinload(AirworthinessDirective.discovery_record),
            selectinload(ADExtractionReview.extraction)
            .selectinload(ADExtraction.directive)
            .selectinload(AirworthinessDirective.publications)
            .selectinload(ADPublication.source_document),
        )
    )
    if review is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="AD extraction review not found")
    if review.status != "pending":
        attempted_output = derive_compliance_action_summaries(
            payload.output if payload.output is not None else review.proposed_output
        )
        db.add(ADExtractionReviewDecision(
            review_id=review.id,
            extraction_id=review.extraction_id,
            decision=payload.decision,
            output_hash=structured_output_hash(attempted_output),
            decision_output=attempted_output,
            actor_user_id=current_user.id,
            decided_at=datetime.now(timezone.utc),
            notes=payload.notes,
            event_type="decision_conflict",
            metadata_json={
                "directiveId": review.extraction.directive_id,
                "terminalStatusObserved": review.status,
                "terminalReviewerUserId": review.reviewer_user_id,
            },
        ))
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Review has already been decided; the conflicting attempt was recorded",
        )
    if payload.decision not in {"approved", "edited", "rejected"}:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Unsupported review decision")

    decision_output = derive_compliance_action_summaries(
        payload.output if payload.output is not None else review.proposed_output
    )
    affected_aircraft_ids = set(
        db.scalars(
            select(ADMatchResult.aircraft_id)
            .where(
                ADMatchResult.directive_id == review.extraction.directive_id,
                ADMatchResult.is_current.is_(True),
            )
            .distinct()
        )
        .all()
    )
    if payload.decision in {"approved", "edited"}:
        source_pages = bounded_source_document_pages(
            ensure_persisted_source_pages(
                review.extraction.directive,
                review.extraction,
            ),
            ad_number=review.extraction.directive.ad_number,
            title=review.extraction.directive.title,
        )
        evidence_status, evidence_message = source_evidence_status(
            review.extraction.directive.ad_number,
            source_pages,
        )
        if evidence_status != "verified":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=evidence_message,
            )
        approval_blockers = extraction_approval_blockers(
            review.extraction,
            decision_output,
            source_pages,
        )
        if approval_blockers:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=" ".join(approval_blockers),
            )
        review.extraction.output = decision_output
        db.execute(
            update(ADExtraction)
            .where(
                ADExtraction.directive_id == review.extraction.directive_id,
                ADExtraction.id != review.extraction.id,
                ADExtraction.status == "approved",
            )
            .values(status="superseded")
        )
        review.extraction.status = "approved"
        review.extraction.directive.extraction_status = "complete"
        review.extraction.directive.review_status = "approved"
        review.extraction.directive.approved_at = datetime.now(timezone.utc)
        populate_applicability_from_extraction(db, review.extraction)
        materialize_requirements_from_extraction(db, review.extraction)
        db.flush()
        target_ids = db.scalars(
            select(ADTargetApplicability.target_id)
            .where(
                ADTargetApplicability.directive_id
                == review.extraction.directive_id,
                ADTargetApplicability.status == "current",
                ADTargetApplicability.source_extraction_id == review.extraction.id,
            )
            .distinct()
        ).all()
        if target_ids:
            affected_aircraft_ids.update(
                db.scalars(
                    select(ADCoverageSubscription.aircraft_id)
                    .join(
                        ADCoverageSet,
                        ADCoverageSet.id
                        == ADCoverageSubscription.coverage_set_id,
                    )
                    .where(
                        ADCoverageSet.target_id.in_(target_ids),
                        ADCoverageSubscription.status == "active",
                    )
                    .distinct()
                ).all()
            )
    else:
        review.extraction.status = "rejected"
        review.extraction.directive.review_status = "rejected"

    decision_time = datetime.now(timezone.utc)
    db.add(ADExtractionReviewDecision(
        review_id=review.id,
        extraction_id=review.extraction_id,
        decision=payload.decision,
        output_hash=structured_output_hash(decision_output),
        decision_output=decision_output,
        actor_user_id=current_user.id,
        decided_at=decision_time,
        notes=payload.notes,
        event_type="review_decision",
        metadata_json={"directiveId": review.extraction.directive_id},
    ))
    review.status = payload.decision
    review.decision = payload.decision
    review.decision_output = decision_output
    review.reviewer_user_id = current_user.id
    review.notes = payload.notes
    review.reviewed_at = decision_time
    for aircraft_id in affected_aircraft_ids:
        resolve_aircraft_ad_coverage(db, aircraft_id)
        invalidate_aircraft_match_results(
            db,
            aircraft_id=aircraft_id,
            actor=current_user,
        )
    record_product_event(
        db,
        event_type="ad_extraction_review_decided",
        subject_type="ad_review",
        subject_id=review.id,
        actor=current_user,
        properties={
            "decision": payload.decision,
            "directiveId": review.extraction.directive_id,
            "extractionStatus": review.extraction.status,
        },
    )
    record_workflow_status(
        db,
        workflow_type="ad_extraction",
        workflow_id=review.extraction_id,
        previous_status="needs_review",
        new_status=review.extraction.status,
        reason=payload.decision,
        actor_type="reviewer",
        actor=current_user,
    )
    db.commit()
    db.refresh(review)
    return ADReviewDecisionResponse(review=serialize_review(review))


def serialize_discovery_record(record: ADDiscoveryRecord) -> ADDiscoveryRecordResponse:
    return ADDiscoveryRecordResponse(
        id=record.id,
        federalRegisterDocumentNumber=record.federal_register_document_number,
        title=record.title,
        documentType=record.document_type,
        publicationDate=record.publication_date,
        htmlUrl=record.html_url,
        pdfUrl=record.pdf_url,
        classification=record.classification,
        classificationConfidence=record.classification_confidence,
        classificationReason=record.classification_reason,
        contentHash=record.content_hash,
    )


def serialize_directive(directive: AirworthinessDirective) -> AirworthinessDirectiveResponse:
    record = directive.discovery_record
    return AirworthinessDirectiveResponse(
        id=directive.id,
        discoveryRecordId=directive.discovery_record_id,
        adNumber=directive.ad_number,
        officialAdNumber=official_ad_number(directive.ad_number),
        title=directive.title,
        status=directive.status,
        extractionStatus=directive.extraction_status,
        reviewStatus=directive.review_status,
        federalRegisterDocumentNumber=record.federal_register_document_number if record else None,
        publicationDate=record.publication_date if record else first_publication_date(directive),
        htmlUrl=record.html_url if record else first_publication_url(directive, "html_url"),
        pdfUrl=record.pdf_url if record else first_publication_url(directive, "pdf_url"),
        applicabilityTargets=serialize_directive_applicability_targets(directive),
    )


def serialize_directive_applicability_targets(
    directive: AirworthinessDirective,
) -> list[ADDirectiveApplicabilityTargetResponse]:
    released_extraction = released_extraction_for_directive(directive)
    released_extraction_id = released_extraction.id if released_extraction else None
    rows: list[ADDirectiveApplicabilityTargetResponse] = []
    seen: set[tuple[str | None, str, str | None, str | None]] = set()
    for applicability in directive.target_applicabilities:
        if (
            applicability.status != "current"
            or applicability.target is None
            or applicability.source_extraction_id != released_extraction_id
        ):
            continue
        target = applicability.target
        identity = applicability.source_identity or {}
        source_manufacturer = identity.get("manufacturer") or {}
        source_model = identity.get("model") or {}
        key = (
            applicability.applicability_group_key,
            target.product_type,
            target.make,
            target.model,
        )
        if key in seen:
            continue
        seen.add(key)
        rows.append(ADDirectiveApplicabilityTargetResponse(
            groupKey=applicability.applicability_group_key,
            productType=target.product_type,
            productSubtype=target.product_subtype,
            manufacturer=target.make,
            model=target.model,
            sourceManufacturer=source_manufacturer.get("sourceName"),
            sourceModel=source_model.get("sourceDesignation"),
        ))
    return rows


def serialize_extraction(extraction: ADExtraction) -> ADExtractionResponse:
    return ADExtractionResponse(
        id=extraction.id,
        directiveId=extraction.directive_id,
        providerName=extraction.provider_name,
        providerVersion=extraction.provider_version,
        schemaVersion=extraction.schema_version,
        inputContentHash=extraction.input_content_hash,
        status=extraction.status,
        confidence=extraction.confidence,
        output=extraction.output,
        citations=extraction.citations or [],
    )


def review_queue_candidate_state(
    review: ADExtractionReview,
) -> tuple[bool, bool]:
    """Return cheap triage counts without asserting a release decision.

    The selected review is always serialized through ``persisted_source_pages``
    and therefore re-derived from verified bytes. These aggregate values only
    keep the queue responsive; they never authorize approval or publication.
    """

    raw_response = review.extraction.raw_response or {}
    cached_pages = raw_response.get("retainedSourcePages")
    if (
        not raw_response.get("retainedSourcePagesCached")
        or not isinstance(cached_pages, list)
        or review.extraction.input_content_hash
        != extraction_input_hash(review.extraction.directive)
    ):
        return False, False
    source_pages = bounded_source_document_pages(
        cached_pages,
        ad_number=review.extraction.directive.ad_number,
        title=review.extraction.directive.title,
    )
    evidence_status, _ = source_evidence_status(
        review.extraction.directive.ad_number,
        source_pages,
    )
    source_candidate = evidence_status == "verified"
    if not source_candidate:
        return False, False
    proposed_output = derive_compliance_action_summaries(
        review.decision_output
        if review.decision_output is not None
        else review.proposed_output
    )
    blockers = extraction_approval_blockers(
        review.extraction,
        proposed_output,
        source_pages,
    )
    return True, review.status == "pending" and not blockers


def serialize_review(review: ADExtractionReview) -> ADExtractionReviewResponse:
    source_pages = bounded_source_document_pages(
        full_text_pages_for_extraction(review.extraction),
        ad_number=review.extraction.directive.ad_number,
        title=review.extraction.directive.title,
    )
    evidence_status, evidence_message = source_evidence_status(
        review.extraction.directive.ad_number,
        source_pages,
    )
    proposed_output = derive_compliance_action_summaries(review.proposed_output)
    decision_output = (
        derive_compliance_action_summaries(review.decision_output)
        if review.decision_output is not None
        else None
    )
    output = decision_output or proposed_output
    requirements = output.get("requirements") or []
    approval_blockers = extraction_approval_blockers(
        review.extraction,
        output,
        source_pages,
    )
    source_document_ids = {
        str(page.get("sourceDocumentId"))
        for page in source_pages
        if page.get("sourceDocumentId")
    }
    source_documents: list[ADSourceDocumentResponse] = []
    relevant_pages_by_document: dict[str, list[int]] = {}
    for page in source_pages:
        document_id = page.get("sourceDocumentId")
        page_number = page.get("pageNumber")
        if document_id and isinstance(page_number, int):
            relevant_pages_by_document.setdefault(str(document_id), []).append(page_number)
    seen_document_ids: set[str] = set()
    for publication in review.extraction.directive.publications:
        document = publication.source_document
        if (
            document is None
            or document.id not in source_document_ids
            or document.id in seen_document_ids
        ):
            continue
        seen_document_ids.add(document.id)
        source_documents.append(serialize_source_document(
            document,
            relevant_page_numbers=relevant_pages_by_document.get(document.id, []),
        ))
    provenance = None
    staging_decision_id = (review.extraction.raw_response or {}).get(
        "latestProposalStagingDecisionId"
    )
    if staging_decision_id:
        staging_decision = next(
            (
                decision
                for decision in review.decision_history
                if decision.id == staging_decision_id
                and decision.event_type == "proposal_staged"
                and decision.decision == "proposal_staged"
            ),
            None,
        )
        if staging_decision is not None:
            metadata = staging_decision.metadata_json or {}
            provenance = ADProposalProvenanceResponse(
                stagingDecisionId=staging_decision.id,
                actorUserId=staging_decision.actor_user_id,
                stagedAt=staging_decision.decided_at,
                stagingMode=(
                    "allow_incomplete"
                    if metadata.get("allowIncomplete")
                    else "strict"
                ),
            )
    return ADExtractionReviewResponse(
        id=review.id,
        status=review.status,
        proposedOutput=proposed_output,
        decisionOutput=decision_output,
        decision=review.decision,
        notes=review.notes,
        extraction=serialize_extraction(review.extraction),
        directive=serialize_directive(review.extraction.directive),
        sourceText="\n\n".join(page["text"] for page in source_pages),
        sourcePages=source_pages,
        sourceDocuments=source_documents,
        requirementCount=len(requirements),
        unresolvedRequirementCount=(
            sum(bool(item.get("uncertaintyReasons")) for item in requirements)
            + sum(
                bool(item.get("uncertaintyReasons"))
                for item in output.get("applicabilityGroups") or []
            )
        ),
        evidenceStatus=evidence_status,
        evidenceMessage=evidence_message,
        canApprove=review.status == "pending" and not approval_blockers,
        approvalBlockers=approval_blockers,
        proposalProvenance=provenance,
    )


def serialize_source_document(
    document: ADSourceDocument,
    *,
    relevant_page_numbers: list[int] | None = None,
) -> ADSourceDocumentResponse:
    page_numbers = sorted(set(relevant_page_numbers or []))
    content_url = f"/api/v1/ads/source-documents/{document.id}/content"
    navigation_url = (
        f"{content_url}#page={page_numbers[0]}" if page_numbers else content_url
    )
    pages_contiguous = bool(page_numbers) and page_numbers == list(
        range(page_numbers[0], page_numbers[-1] + 1)
    )
    return ADSourceDocumentResponse(
        id=document.id,
        sourceSystem=document.source_system,
        sourceType=document.source_type,
        sourceIdentifier=document.source_identifier,
        parentSourceIdentifier=document.parent_source_identifier,
        sourceUrl=document.source_url,
        contentUrl=content_url,
        mediaType=document.media_type,
        contentHash=document.content_hash,
        storageBytes=document.storage_bytes,
        capturedAt=document.captured_at,
        publicationDate=document.publication_date,
        parserName=document.parser_name,
        parserVersion=document.parser_version,
        relevantPageStart=page_numbers[0] if page_numbers else None,
        relevantPageEnd=page_numbers[-1] if page_numbers else None,
        relevantPageNumbers=page_numbers,
        relevantPagesContiguous=pages_contiguous,
        navigationUrl=navigation_url,
    )


def serialize_match_result(match: ADMatchResult) -> ADMatchResultResponse:
    due_states = [
        link.due_state
        for link in match.due_state_links
        if link.due_state is not None
    ]
    if not due_states and match.due_state is not None:
        due_states = [match.due_state]
    return ADMatchResultResponse(
        id=match.id,
        aircraftId=match.aircraft_id,
        aircraftFacts={
            "nNumber": match.aircraft.n_number_normalized if match.aircraft else None,
            "make": match.aircraft.make if match.aircraft else None,
            "model": match.aircraft.model if match.aircraft else None,
            "serialNumber": match.aircraft.serial_number if match.aircraft else None,
            "engineMake": match.aircraft.engine_make if match.aircraft else None,
            "engineModel": match.aircraft.engine_model if match.aircraft else None,
            "propellerMake": match.aircraft.propeller_make if match.aircraft else None,
            "propellerModel": match.aircraft.propeller_model if match.aircraft else None,
        },
        directive=serialize_directive(match.directive),
        status=match.status,
        matchType=match.match_type,
        confidence=match.confidence,
        rationale=match.rationale,
        unresolvedReasons=match.unresolved_reasons or [],
        applicability=serialize_match_applicability(match),
        dueState=(
            ADDueStateResponse(**due_state_payload(due_states[0]))
            if len(due_states) == 1
            else None
        ),
        dueStates=[
            ADDueStateResponse(**due_state_payload(state))
            for state in due_states
        ],
        algorithmName=match.algorithm_name,
        algorithmVersion=match.algorithm_version,
        inputHash=match.input_hash,
        evidence=[serialize_match_evidence(evidence) for evidence in match.evidence_links],
        adjudication=serialize_match_adjudication(match.adjudication) if match.adjudication else None,
    )


def serialize_match_applicability(match: ADMatchResult) -> ADMatchApplicabilityResponse | None:
    applicability = match.target_applicability
    component = match.installed_component
    publications = []
    if applicability and applicability.source_publication:
        publications.append(applicability.source_publication)
    publications.extend([publication for publication in match.directive.publications if publication not in publications])
    if not applicability and not component and not publications and not match.applicability_snapshot:
        return None
    target = applicability.target if applicability else None
    return ADMatchApplicabilityResponse(
        component=ADMatchComponentResponse(
            id=component.id if component else None,
            role=component.role if component else None,
            componentType=component.component_type if component else None,
            displayName=component_display_name(component),
            make=component.make if component else None,
            model=component.model if component else None,
            serialNumber=component.serial_number if component else None,
            source=component.source if component else None,
        )
        if component
        else None,
        target=ADMatchTargetResponse(
            id=target.id,
            productType=target.product_type,
            productSubtype=target.product_subtype,
            make=target.make,
            model=target.model,
        )
        if target
        else None,
        basis=applicability.applicability_basis if applicability else None,
        confidence=applicability.confidence if applicability else None,
        status=applicability.status if applicability else None,
        sourceStatus=(publications[0].status if publications else None),
        serialStatus=(match.applicability_snapshot or {}).get("serialStatus"),
        publications=[
            ADMatchPublicationResponse(
                sourceSystem=publication.source_system,
                sourceType=publication.source_type,
                sourceIdentifier=publication.source_identifier,
                status=publication.status,
                htmlUrl=publication.html_url,
                pdfUrl=publication.pdf_url,
            )
            for publication in publications
        ],
        snapshot=match.applicability_snapshot,
    )


def first_publication_date(directive: AirworthinessDirective):
    publication = next(iter(directive.publications), None)
    return publication.publication_date if publication else None


def first_publication_url(directive: AirworthinessDirective, field_name: str) -> str | None:
    for publication in directive.publications:
        value = getattr(publication, field_name)
        if value:
            return value
    return None


def serialize_match_evidence(evidence: ADMatchEvidence) -> ADMatchEvidenceResponse:
    entry = evidence.logbook_entry
    return ADMatchEvidenceResponse(
        id=evidence.id,
        logbookEntryId=evidence.logbook_entry_id,
        entryDate=entry.entry_date,
        section=entry.logbook_section.key,
        evidenceType=evidence.evidence_type,
        fieldName=evidence.field_name,
        matchedText=evidence.matched_text,
        confidence=evidence.confidence,
        rationale=evidence.rationale,
    )


def serialize_match_adjudication(adjudication: ADMatchAdjudication) -> ADMatchAdjudicationResponse:
    return ADMatchAdjudicationResponse(
        id=adjudication.id,
        status=adjudication.status,
        decision=adjudication.decision,
        notes=adjudication.notes,
        futureImprovementTags=adjudication.future_improvement_tags or [],
    )
