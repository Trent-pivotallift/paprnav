from __future__ import annotations

from datetime import date
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_current_user
from app.api.routes.aircraft import get_visible_aircraft_or_404
from app.db.session import get_db
from app.models.core import IngestionJob, IngestionPage, OCRCorrection, OCRTextSpan, User
from app.models.core import LogbookEntry, LogbookEntryEvidence
from app.schemas.ingestion import (
    CandidateRegionResponse,
    ExtractedLogbookEntryCandidateResponse,
    ExtractedLogbookEntryResponse,
    ExtractLogbookEntriesResponse,
    IngestionJobDetailResponse,
    IngestionJobSummary,
    IngestionPageResponse,
    IngestionReviewMetricsResponse,
    LogicalPageRegionResponse,
    LogbookEntryEvidenceResponse,
    OCRCorrectionRequest,
    OCRCorrectionResponse,
    OCRTextSpanResponse,
    PageVerificationRequest,
    PageVerificationResponse,
)
from app.services.ingestion import (
    extract_entries_from_job,
    span_requires_raw_ocr_correction,
)
from app.services.review_metrics import calculate_ingestion_review_metrics
from app.services.observability import record_product_event, record_workflow_status
from app.core.config import get_settings
from app.api.routes.uploads import get_s3_client, local_upload_path, s3_body_iterator

router = APIRouter(prefix="/api/v1/ingestion-jobs", tags=["ingestion"])
MAX_CORRECTION_ORDER_ATTEMPTS = 3


def serialize_job(job: IngestionJob) -> IngestionJobSummary:
    return IngestionJobSummary(
        id=job.id,
        uploadId=job.upload_id,
        uploadDownloadUrl=f"/api/v1/uploads/{job.upload_id}/download",
        aircraftId=job.aircraft_id,
        status=job.status,
        pageExtractionStatus=job.page_extraction_status,
        ocrStatus=job.ocr_status,
        verificationStatus=job.verification_status,
        entryExtractionStatus=job.entry_extraction_status,
        logbookSection=job.logbook_section_key,
        errorCode=job.error_code,
        errorMessage=job.error_message,
        documentInspection=job.document_inspection,
    )


def serialize_correction(correction: OCRCorrection) -> OCRCorrectionResponse:
    return OCRCorrectionResponse(
        id=correction.id,
        ocrTextSpanId=correction.ocr_text_span_id,
        correctionOrder=correction.correction_order,
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
    has_page_image = Path(page.image_storage_key or "").suffix.lower() in {".png", ".jpg", ".jpeg"}
    return IngestionPageResponse(
        id=page.id,
        sourcePageNumber=page.source_page_number,
        currentPageOrder=page.current_page_order,
        pageLabel=page.page_label,
        imageStorageBackend=page.image_storage_backend,
        imageStorageKey=page.image_storage_key,
        imageDownloadUrl=f"/api/v1/ingestion-jobs/{page.ingestion_job_id}/pages/{page.id}/image" if has_page_image else None,
        widthPx=page.width_px,
        heightPx=page.height_px,
        rotationDegrees=page.rotation_degrees,
        extractionConfidence=page.extraction_confidence,
        inspectionStatus=page.inspection_status,
        sourcePageFingerprint=page.source_page_fingerprint,
        canonicalImageSha256=page.canonical_image_sha256,
        renderProfile=page.render_profile,
        renderMetadata=page.render_metadata,
        pageClassification=page.page_classification,
        nativeTextEvaluation=page.native_text_evaluation,
        extractionPlan=page.extraction_plan,
        stageResults=page.stage_results,
        logicalRegions=[
            LogicalPageRegionResponse(
                id=region.id,
                regionKey=region.region_key,
                regionType=region.region_type,
                bboxLeft=region.bbox_left,
                bboxTop=region.bbox_top,
                bboxWidth=region.bbox_width,
                bboxHeight=region.bbox_height,
                bboxUnits=region.bbox_units,
                readingOrder=region.reading_order,
                classification=region.classification,
            )
            for region in page.logical_regions
        ],
        spans=[serialize_span(span) for span in page.ocr_spans],
    )


def page_image_media_type(page: IngestionPage) -> str:
    suffix = Path(page.image_storage_key or "").suffix.lower()
    if suffix in {".jpg", ".jpeg"}:
        return "image/jpeg"
    return "image/png"


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


@router.get(
    "/{job_id}/review-metrics",
    response_model=IngestionReviewMetricsResponse,
)
def get_ingestion_review_metrics(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> IngestionReviewMetricsResponse:
    job = get_visible_job_or_404(db, current_user, job_id)
    return IngestionReviewMetricsResponse(
        **calculate_ingestion_review_metrics(job)
    )


def get_visible_job_or_404(db: Session, user: User, job_id: str) -> IngestionJob:
    job = db.scalar(
        select(IngestionJob)
        .where(IngestionJob.id == job_id)
        .options(
            selectinload(IngestionJob.pages).selectinload(IngestionPage.ocr_spans).selectinload(OCRTextSpan.corrections),
            selectinload(IngestionJob.verifications),
            selectinload(IngestionJob.evidence_links)
            .selectinload(LogbookEntryEvidence.logbook_entry)
            .selectinload(LogbookEntry.logbook_section),
            selectinload(IngestionJob.evidence_links)
            .selectinload(LogbookEntryEvidence.ocr_text_span)
            .selectinload(OCRTextSpan.corrections),
        )
    )
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ingestion job not found")
    get_visible_aircraft_or_404(db, user, job.aircraft_id)
    return job


def response_float(value: float | None) -> float | None:
    if value is None:
        return None
    return round(value, 2)


def candidate_region(evidence_items: list[LogbookEntryEvidence]) -> CandidateRegionResponse | None:
    grouped_spans: dict[str, list[OCRTextSpan]] = {}
    for evidence in evidence_items:
        span = evidence.ocr_text_span
        if span is None or span.bbox_units != "ratio":
            continue
        if None in (span.bbox_left, span.bbox_top, span.bbox_width, span.bbox_height):
            continue
        grouped_spans.setdefault(span.ingestion_page_id, []).append(span)
    if not grouped_spans:
        return None

    page_id, spans = max(grouped_spans.items(), key=lambda item: len(item[1]))
    left = min(float(span.bbox_left or 0) for span in spans)
    top = min(float(span.bbox_top or 0) for span in spans)
    right = max(float(span.bbox_left or 0) + float(span.bbox_width or 0) for span in spans)
    bottom = max(float(span.bbox_top or 0) + float(span.bbox_height or 0) for span in spans)
    return CandidateRegionResponse(
        pageId=page_id,
        bboxLeft=left,
        bboxTop=top,
        bboxWidth=right - left,
        bboxHeight=bottom - top,
    )


def serialize_extracted_entries(job: IngestionJob) -> list[ExtractedLogbookEntryCandidateResponse]:
    evidence_by_entry: dict[str, list[LogbookEntryEvidence]] = {}
    for evidence in job.evidence_links:
        if evidence.logbook_entry is None:
            continue
        evidence_by_entry.setdefault(evidence.logbook_entry_id, []).append(evidence)

    entries = sorted(
        {evidence.logbook_entry_id: evidence.logbook_entry for evidence in job.evidence_links if evidence.logbook_entry}.values(),
        key=lambda entry: (entry.entry_date or date.max, entry.created_at),
    )
    return [
        ExtractedLogbookEntryCandidateResponse(
            id=entry.id,
            entryDate=entry.entry_date,
            section=entry.logbook_section.key,
            description=entry.description,
            performerName=entry.performer_name,
            performerCredential=entry.performer_credential,
            tachTime=response_float(entry.tach_time),
            hobbsTime=response_float(entry.hobbs_time),
            totalTime=response_float(entry.total_time),
            reviewStatus=entry.review_status,
            validationStatus=entry.validation_status,
            validationResults=entry.validation_results,
            region=candidate_region(evidence_by_entry.get(entry.id, [])),
            evidence=[
                LogbookEntryEvidenceResponse(
                    id=evidence.id,
                    fieldName=evidence.field_name,
                    evidenceType=evidence.evidence_type,
                    confidence=evidence.confidence,
                    span=serialize_span(evidence.ocr_text_span) if evidence.ocr_text_span else None,
                    reviewMetadata=evidence.review_metadata,
                )
                for evidence in sorted(
                    evidence_by_entry.get(entry.id, []),
                    key=lambda item: (
                        item.field_name or "",
                        item.ocr_text_span.reading_order if item.ocr_text_span else 0,
                    ),
                )
            ],
        )
        for entry in entries
    ]


def create_ordered_ocr_correction(
    db: Session,
    *,
    job: IngestionJob,
    span: OCRTextSpan,
    current_user: User,
    payload: OCRCorrectionRequest,
) -> OCRCorrection:
    for _attempt in range(MAX_CORRECTION_ORDER_ATTEMPTS):
        latest_order = db.scalar(
            select(func.max(OCRCorrection.correction_order)).where(OCRCorrection.ocr_text_span_id == span.id)
        )
        correction = OCRCorrection(
            ingestion_job_id=job.id,
            ingestion_page_id=span.ingestion_page_id,
            ocr_text_span_id=span.id,
            corrected_by_user_id=current_user.id,
            original_text=span.text,
            corrected_text=payload.correctedText.strip(),
            original_confidence=span.confidence,
            correction_order=(latest_order or 0) + 1,
            correction_reason=payload.correctionReason,
            notes=payload.notes,
        )
        try:
            with db.begin_nested():
                db.add(correction)
                db.flush()
            return correction
        except IntegrityError:
            continue

    raise HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail="Unable to assign OCR correction order; retry the correction",
    )


@router.get("/{job_id}/pages/{page_id}/image")
def download_page_image(
    job_id: str,
    page_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    job = get_visible_job_or_404(db, current_user, job_id)
    page = next((item for item in job.pages if item.id == page_id), None)
    if (
        page is None
        or not page.image_storage_key
        or not page.image_storage_backend
        or Path(page.image_storage_key).suffix.lower() not in {".png", ".jpg", ".jpeg"}
    ):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Page image not found")

    settings = get_settings()
    media_type = page_image_media_type(page)
    if page.image_storage_backend == "s3":
        if not settings.s3_upload_bucket:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="S3 upload bucket is not configured")
        try:
            response = get_s3_client(settings.aws_region).get_object(Bucket=settings.s3_upload_bucket, Key=page.image_storage_key)
        except Exception as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Page image not found") from exc
        return StreamingResponse(s3_body_iterator(response["Body"]), media_type=media_type)

    file_path = local_upload_path(settings.local_storage_path, page.image_storage_key)
    if not file_path.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Page image not found")
    return FileResponse(path=file_path, media_type=media_type)


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
        extractedEntries=serialize_extracted_entries(job),
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
        has_low_confidence = any(
            span_requires_raw_ocr_correction(span)
            for page in job.pages
            for span in page.ocr_spans
        )
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
        extractedEntries=serialize_extracted_entries(job),
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

    correction = create_ordered_ocr_correction(
        db,
        job=job,
        span=span,
        current_user=current_user,
        payload=payload,
    )
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
                tachTime=response_float(entry.tach_time),
                hobbsTime=response_float(entry.hobbs_time),
                totalTime=response_float(entry.total_time),
                reviewStatus=entry.review_status,
            )
            for entry in entries
        ]
    )
