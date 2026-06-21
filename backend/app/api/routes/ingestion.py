from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_current_user
from app.api.routes.aircraft import get_visible_aircraft_or_404
from app.db.session import get_db
from app.models.core import IngestionJob, IngestionPage, OCRCorrection, OCRTextSpan, User
from app.schemas.ingestion import (
    ExtractedLogbookEntryResponse,
    ExtractLogbookEntriesResponse,
    IngestionJobDetailResponse,
    IngestionJobSummary,
    IngestionPageResponse,
    OCRCorrectionRequest,
    OCRCorrectionResponse,
    OCRTextSpanResponse,
    PageVerificationRequest,
    PageVerificationResponse,
)
from app.services.ingestion import extract_entries_from_job
from app.services.observability import record_product_event, record_workflow_status

router = APIRouter(prefix="/api/v1/ingestion-jobs", tags=["ingestion"])


def serialize_job(job: IngestionJob) -> IngestionJobSummary:
    return IngestionJobSummary(
        id=job.id,
        uploadId=job.upload_id,
        aircraftId=job.aircraft_id,
        status=job.status,
        pageExtractionStatus=job.page_extraction_status,
        ocrStatus=job.ocr_status,
        verificationStatus=job.verification_status,
        entryExtractionStatus=job.entry_extraction_status,
        logbookSection=job.logbook_section_key,
        errorCode=job.error_code,
        errorMessage=job.error_message,
    )


def serialize_correction(correction: OCRCorrection) -> OCRCorrectionResponse:
    return OCRCorrectionResponse(
        id=correction.id,
        ocrTextSpanId=correction.ocr_text_span_id,
        originalText=correction.original_text,
        correctedText=correction.corrected_text,
        originalConfidence=correction.original_confidence,
        correctionReason=correction.correction_reason,
        notes=correction.notes,
    )


def serialize_span(span: OCRTextSpan) -> OCRTextSpanResponse:
    return OCRTextSpanResponse(
        id=span.id,
        ingestionPageId=span.ingestion_page_id,
        providerBlockId=span.provider_block_id,
        spanType=span.span_type,
        text=span.text,
        confidence=span.confidence,
        confidenceScale=span.confidence_scale,
        bboxLeft=span.bbox_left,
        bboxTop=span.bbox_top,
        bboxWidth=span.bbox_width,
        bboxHeight=span.bbox_height,
        bboxUnits=span.bbox_units,
        readingOrder=span.reading_order,
        corrections=[serialize_correction(correction) for correction in span.corrections],
    )


def serialize_page(page: IngestionPage) -> IngestionPageResponse:
    return IngestionPageResponse(
        id=page.id,
        sourcePageNumber=page.source_page_number,
        currentPageOrder=page.current_page_order,
        pageLabel=page.page_label,
        imageStorageBackend=page.image_storage_backend,
        imageStorageKey=page.image_storage_key,
        widthPx=page.width_px,
        heightPx=page.height_px,
        rotationDegrees=page.rotation_degrees,
        extractionConfidence=page.extraction_confidence,
        spans=[serialize_span(span) for span in page.ocr_spans],
    )


def serialize_verification(job: IngestionJob) -> PageVerificationResponse | None:
    if not job.verifications:
        return None
    verification = job.verifications[-1]
    return PageVerificationResponse(
        id=verification.id,
        isOrderConfirmed=verification.is_order_confirmed,
        isComplete=verification.is_complete,
        missingOrUncertainNotes=verification.missing_or_uncertain_notes,
    )


def get_visible_job_or_404(db: Session, user: User, job_id: str) -> IngestionJob:
    job = db.scalar(
        select(IngestionJob)
        .where(IngestionJob.id == job_id)
        .options(
            selectinload(IngestionJob.pages).selectinload(IngestionPage.ocr_spans).selectinload(OCRTextSpan.corrections),
            selectinload(IngestionJob.verifications),
        )
    )
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ingestion job not found")
    get_visible_aircraft_or_404(db, user, job.aircraft_id)
    return job


@router.get("/{job_id}", response_model=IngestionJobDetailResponse)
def get_ingestion_job(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> IngestionJobDetailResponse:
    job = get_visible_job_or_404(db, current_user, job_id)
    return IngestionJobDetailResponse(
        job=serialize_job(job),
        pages=[serialize_page(page) for page in job.pages],
        latestVerification=serialize_verification(job),
    )


@router.post("/{job_id}/page-verification", response_model=IngestionJobDetailResponse)
def verify_pages(
    job_id: str,
    payload: PageVerificationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> IngestionJobDetailResponse:
    job = get_visible_job_or_404(db, current_user, job_id)
    pages_by_id = {page.id: page for page in job.pages}
    snapshot: list[dict] = []
    for page_update in payload.pages:
        page = pages_by_id.get(page_update.pageId)
        if not page:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown ingestion page")
        page.current_page_order = page_update.currentPageOrder
        snapshot.append({"pageId": page.id, "currentPageOrder": page.current_page_order})

    from app.models.core import PageVerification

    db.add(
        PageVerification(
            ingestion_job_id=job.id,
            verified_by_user_id=current_user.id,
            is_order_confirmed=payload.isOrderConfirmed,
            is_complete=payload.isComplete,
            missing_or_uncertain_notes=payload.missingOrUncertainNotes,
            page_order_snapshot={"pages": snapshot},
        )
    )
    job.verification_status = "verified" if payload.isOrderConfirmed and payload.isComplete else "needs_review"
    previous_status = job.status
    if job.verification_status == "verified":
        has_low_confidence = any((span.confidence or 0) < 80 for page in job.pages for span in page.ocr_spans)
        job.status = "awaiting_ocr_corrections" if has_low_confidence else "ready_for_entry_extraction"
        job.entry_extraction_status = "ready"

    record_product_event(
        db,
        event_type="page_verification_saved",
        subject_type="ingestion_job",
        subject_id=job.id,
        actor=current_user,
        aircraft_id=job.aircraft_id,
        properties={
            "isOrderConfirmed": payload.isOrderConfirmed,
            "isComplete": payload.isComplete,
            "verificationStatus": job.verification_status,
            "pageCount": len(payload.pages),
        },
    )
    record_workflow_status(
        db,
        workflow_type="page_verification",
        workflow_id=job.id,
        previous_status=previous_status,
        new_status=job.status,
        reason=job.verification_status,
        actor_type="user",
        actor=current_user,
    )
    db.commit()
    job = get_visible_job_or_404(db, current_user, job_id)
    return IngestionJobDetailResponse(
        job=serialize_job(job),
        pages=[serialize_page(page) for page in job.pages],
        latestVerification=serialize_verification(job),
    )


@router.post("/{job_id}/ocr-corrections", response_model=OCRCorrectionResponse, status_code=status.HTTP_201_CREATED)
def create_ocr_correction(
    job_id: str,
    payload: OCRCorrectionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> OCRCorrectionResponse:
    job = get_visible_job_or_404(db, current_user, job_id)
    span = db.get(OCRTextSpan, payload.ocrTextSpanId)
    if not span or span.ingestion_page.ingestion_job_id != job.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="OCR span not found")

    correction = OCRCorrection(
        ingestion_job_id=job.id,
        ingestion_page_id=span.ingestion_page_id,
        ocr_text_span_id=span.id,
        corrected_by_user_id=current_user.id,
        original_text=span.text,
        corrected_text=payload.correctedText.strip(),
        original_confidence=span.confidence,
        correction_reason=payload.correctionReason,
        notes=payload.notes,
    )
    db.add(correction)
    db.flush()
    previous_status = job.status
    job.status = "ready_for_entry_extraction"
    job.entry_extraction_status = "ready"
    record_product_event(
        db,
        event_type="ocr_correction_created",
        subject_type="ocr_correction",
        subject_id=correction.id,
        actor=current_user,
        aircraft_id=job.aircraft_id,
        properties={
            "ingestionJobId": job.id,
            "originalConfidence": span.confidence,
            "correctionReason": payload.correctionReason,
        },
    )
    record_workflow_status(
        db,
        workflow_type="ocr_correction",
        workflow_id=job.id,
        previous_status=previous_status,
        new_status=job.status,
        reason="correction_created",
        actor_type="user",
        actor=current_user,
    )
    db.commit()
    db.refresh(correction)
    return serialize_correction(correction)


@router.post("/{job_id}/extract-logbook-entries", response_model=ExtractLogbookEntriesResponse)
def extract_logbook_entries(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ExtractLogbookEntriesResponse:
    job = get_visible_job_or_404(db, current_user, job_id)
    try:
        entries = extract_entries_from_job(db, job)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    record_product_event(
        db,
        event_type="logbook_entries_extracted",
        subject_type="ingestion_job",
        subject_id=job.id,
        actor=current_user,
        aircraft_id=job.aircraft_id,
        properties={"entryCount": len(entries), "status": job.status},
    )
    record_workflow_status(
        db,
        workflow_type="upload_ingestion",
        workflow_id=job.id,
        previous_status="ready_for_entry_extraction",
        new_status=job.status,
        reason="entries_extracted",
        actor_type="user",
        actor=current_user,
    )
    db.commit()
    return ExtractLogbookEntriesResponse(
        entries=[
            ExtractedLogbookEntryResponse(
                id=entry.id,
                entryDate=entry.entry_date,
                section=entry.logbook_section.key,
                description=entry.description,
                performerName=entry.performer_name,
                performerCredential=entry.performer_credential,
                reviewStatus=entry.review_status,
            )
            for entry in entries
        ]
    )
