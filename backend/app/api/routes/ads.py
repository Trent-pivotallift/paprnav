from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_current_user
from app.api.routes.aircraft import get_visible_aircraft_or_404
from app.db.session import get_db
from app.models.core import (
    ADDiscoveryRecord,
    ADExtraction,
    ADExtractionReview,
    ADMatchAdjudication,
    ADMatchEvidence,
    ADMatchResult,
    AirworthinessDirective,
    LogbookEntry,
    User,
)
from app.schemas.ads import (
    ADDiscoveryRecordResponse,
    ADExtractionResponse,
    ADExtractionReviewListResponse,
    ADExtractionReviewResponse,
    ADMatchAdjudicationResponse,
    ADMatchAdjudicationDecisionRequest,
    ADMatchAdjudicationDecisionResponse,
    ADMatchEvidenceResponse,
    ADMatchResultListResponse,
    ADMatchResultResponse,
    ADReviewDecisionRequest,
    ADReviewDecisionResponse,
    AirworthinessDirectiveResponse,
)
from app.services.ad_extraction import validate_extraction_output
from app.services.observability import record_product_event, record_workflow_status

router = APIRouter(prefix="/api/v1/ads", tags=["airworthiness-directives"])


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
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[AirworthinessDirectiveResponse]:
    _ = current_user
    directives = db.scalars(
        select(AirworthinessDirective)
        .options(selectinload(AirworthinessDirective.discovery_record))
        .order_by(AirworthinessDirective.created_at.desc())
    ).all()
    return [serialize_directive(directive) for directive in directives]


@router.get("/extraction-reviews", response_model=ADExtractionReviewListResponse)
def list_extraction_reviews(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ADExtractionReviewListResponse:
    _ = current_user
    reviews = db.scalars(
        select(ADExtractionReview)
        .options(
            selectinload(ADExtractionReview.extraction)
            .selectinload(ADExtraction.directive)
            .selectinload(AirworthinessDirective.discovery_record)
        )
        .order_by(ADExtractionReview.created_at.desc())
    ).all()
    return ADExtractionReviewListResponse(reviews=[serialize_review(review) for review in reviews])


@router.get("/aircraft/{aircraft_id}/matches", response_model=ADMatchResultListResponse)
def list_aircraft_matches(
    aircraft_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ADMatchResultListResponse:
    get_visible_aircraft_or_404(db, current_user, aircraft_id)
    matches = db.scalars(
        select(ADMatchResult)
        .where(ADMatchResult.aircraft_id == aircraft_id)
        .options(
            selectinload(ADMatchResult.aircraft),
            selectinload(ADMatchResult.directive).selectinload(AirworthinessDirective.discovery_record),
            selectinload(ADMatchResult.evidence_links).selectinload(ADMatchEvidence.logbook_entry).selectinload(LogbookEntry.logbook_section),
            selectinload(ADMatchResult.adjudication),
        )
        .order_by(ADMatchResult.status.desc(), ADMatchResult.confidence.desc(), ADMatchResult.created_at.desc())
    ).all()
    return ADMatchResultListResponse(matches=[serialize_match_result(match) for match in matches])


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
            selectinload(ADMatchResult.evidence_links).selectinload(ADMatchEvidence.logbook_entry).selectinload(LogbookEntry.logbook_section),
            selectinload(ADMatchResult.adjudication),
        )
    )
    if not match:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="AD match not found")
    get_visible_aircraft_or_404(db, current_user, match.aircraft_id)
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
    review = db.scalar(
        select(ADExtractionReview)
        .where(ADExtractionReview.id == review_id)
        .options(
            selectinload(ADExtractionReview.extraction)
            .selectinload(ADExtraction.directive)
            .selectinload(AirworthinessDirective.discovery_record)
        )
    )
    if review is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="AD extraction review not found")
    if review.status != "pending":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Review has already been decided")
    if payload.decision not in {"approved", "edited", "rejected"}:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Unsupported review decision")

    decision_output = payload.output if payload.output is not None else review.proposed_output
    if payload.decision in {"approved", "edited"}:
        validate_extraction_output(decision_output)
        review.extraction.output = decision_output
        review.extraction.status = "approved"
        review.extraction.directive.extraction_status = "complete"
        review.extraction.directive.review_status = "approved"
        review.extraction.directive.approved_at = datetime.now(timezone.utc)
    else:
        review.extraction.status = "rejected"
        review.extraction.directive.review_status = "rejected"

    review.status = payload.decision
    review.decision = payload.decision
    review.decision_output = decision_output
    review.reviewer_user_id = current_user.id
    review.notes = payload.notes
    review.reviewed_at = datetime.now(timezone.utc)
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
        title=directive.title,
        status=directive.status,
        extractionStatus=directive.extraction_status,
        reviewStatus=directive.review_status,
        federalRegisterDocumentNumber=record.federal_register_document_number,
        publicationDate=record.publication_date,
        htmlUrl=record.html_url,
        pdfUrl=record.pdf_url,
    )


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


def serialize_review(review: ADExtractionReview) -> ADExtractionReviewResponse:
    record = review.extraction.directive.discovery_record
    source_text = "\n\n".join(filter(None, [record.title, record.abstract, record.excerpts]))
    return ADExtractionReviewResponse(
        id=review.id,
        status=review.status,
        proposedOutput=review.proposed_output,
        decisionOutput=review.decision_output,
        decision=review.decision,
        notes=review.notes,
        extraction=serialize_extraction(review.extraction),
        directive=serialize_directive(review.extraction.directive),
        sourceText=source_text,
    )


def serialize_match_result(match: ADMatchResult) -> ADMatchResultResponse:
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
        algorithmName=match.algorithm_name,
        algorithmVersion=match.algorithm_version,
        inputHash=match.input_hash,
        evidence=[serialize_match_evidence(evidence) for evidence in match.evidence_links],
        adjudication=serialize_match_adjudication(match.adjudication) if match.adjudication else None,
    )


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
