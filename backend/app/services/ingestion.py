import re
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.core import (
    IngestionJob,
    IngestionPage,
    LogbookEntry,
    LogbookEntryEvidence,
    LogbookSection,
    OCRCorrection,
    OCRRun,
    OCRTextSpan,
    Upload,
)
from app.services.ocr_provider import OCRProvider, get_ocr_provider

LOW_CONFIDENCE_THRESHOLD = 80.0
EXTRACTION_PROVIDER_NAME = "deterministic_logbook_extractor"
EXTRACTION_PROVIDER_VERSION = "0.1.0"
EXTRACTION_SCHEMA_VERSION = "logbook_entry_v1"


def create_ingestion_job(db: Session, upload: Upload, created_by_user_id: str, section: str | None) -> IngestionJob:
    job = IngestionJob(
        upload_id=upload.id,
        aircraft_id=upload.aircraft_id,
        created_by_user_id=created_by_user_id,
        status="queued",
        page_extraction_status="queued",
        ocr_status="queued",
        verification_status="not_started",
        entry_extraction_status="not_started",
        logbook_section_key=section,
    )
    db.add(job)
    db.flush()
    return job


def process_ingestion_job(db: Session, job: IngestionJob, provider: OCRProvider | None = None) -> IngestionJob:
    provider = provider or get_ocr_provider()
    upload = db.get(Upload, job.upload_id)
    if not upload:
        job.status = "failed"
        job.error_code = "upload_missing"
        job.error_message = "Upload not found"
        db.commit()
        return job

    existing_run = db.scalar(select(OCRRun).where(OCRRun.ingestion_job_id == job.id, OCRRun.status == "complete"))
    if existing_run:
        return job

    now = datetime.now(timezone.utc)
    job.status = "ocr_processing"
    job.page_extraction_status = "running"
    job.ocr_status = "running"
    run = OCRRun(
        ingestion_job_id=job.id,
        provider_name=provider.provider_name,
        provider_version=provider.provider_version,
        configuration_hash=provider.configuration_hash,
        status="running",
        started_at=now,
    )
    db.add(run)
    db.flush()

    try:
        result = provider.process_upload(original_filename=upload.original_filename, content_type=upload.content_type)
        for page_result in result.pages:
            page = IngestionPage(
                ingestion_job_id=job.id,
                upload_id=upload.id,
                source_page_number=page_result.source_page_number,
                current_page_order=page_result.source_page_number,
                page_label=page_result.page_label,
                image_storage_backend=upload.storage_backend,
                image_storage_key=upload.storage_key,
                width_px=page_result.width_px,
                height_px=page_result.height_px,
                rotation_degrees=page_result.rotation_degrees,
                extraction_confidence=page_result.extraction_confidence,
            )
            db.add(page)
            db.flush()
            for span_result in page_result.spans:
                db.add(
                    OCRTextSpan(
                        ocr_run_id=run.id,
                        ingestion_page_id=page.id,
                        provider_block_id=span_result.provider_block_id,
                        span_type=span_result.span_type,
                        text=span_result.text,
                        confidence=span_result.confidence,
                        confidence_scale="0_100",
                        bbox_left=span_result.bbox_left,
                        bbox_top=span_result.bbox_top,
                        bbox_width=span_result.bbox_width,
                        bbox_height=span_result.bbox_height,
                        bbox_units=span_result.bbox_units,
                        polygon=[],
                        rotation_degrees=page_result.rotation_degrees,
                        reading_order=span_result.reading_order,
                        relationships=span_result.relationships,
                    )
                )

        run.status = "complete"
        run.completed_at = datetime.now(timezone.utc)
        job.status = "awaiting_page_review"
        job.page_extraction_status = "complete"
        job.ocr_status = "complete"
        job.verification_status = "awaiting_review"
        db.commit()
        db.refresh(job)
        return job
    except Exception as exc:
        run.status = "failed"
        run.error_message = str(exc)
        job.status = "failed"
        job.page_extraction_status = "failed"
        job.ocr_status = "failed"
        job.error_code = "ocr_provider_failed"
        job.error_message = str(exc)
        db.commit()
        return job


def latest_correction_by_span(page: IngestionPage) -> dict[str, OCRCorrection]:
    corrections: dict[str, OCRCorrection] = {}
    for correction in page.corrections:
        corrections[correction.ocr_text_span_id] = correction
    return corrections


def effective_span_text(span: OCRTextSpan) -> str:
    if span.corrections:
        return span.corrections[-1].corrected_text
    return span.text


def extract_entries_from_job(db: Session, job: IngestionJob) -> list[LogbookEntry]:
    if job.verification_status != "verified":
        raise ValueError("Page order and completeness must be verified before extraction")

    existing = db.scalars(
        select(LogbookEntry)
        .join(LogbookEntryEvidence)
        .where(LogbookEntryEvidence.ingestion_job_id == job.id)
    ).all()
    if existing:
        return existing

    section_key = job.logbook_section_key or "airframe"
    section = db.scalar(select(LogbookSection).where(LogbookSection.key == section_key))
    if section is None:
        raise ValueError("Unknown logbook section")

    entries: list[LogbookEntry] = []
    for page in sorted(job.pages, key=lambda item: item.current_page_order):
        line_spans = [span for span in page.ocr_spans if span.span_type.upper() == "LINE"]
        if not line_spans:
            continue
        lines = [effective_span_text(span) for span in sorted(line_spans, key=lambda item: item.reading_order)]
        entry_date = parse_date(lines[0])
        description = strip_date(lines[0])
        performer_name, performer_credential = parse_performer(lines)
        tach_time = parse_float_field(lines, "Tach")
        hobbs_time = parse_float_field(lines, "Hobbs")
        total_time = parse_float_field(lines, "Total")
        min_confidence = min((span.confidence or 0 for span in line_spans), default=0)

        entry = LogbookEntry(
            aircraft_id=job.aircraft_id,
            logbook_section_id=section.id,
            entry_date=entry_date,
            description=description,
            performer_name=performer_name,
            performer_credential=performer_credential,
            source_type="ocr_ingestion",
            created_by_user_id=job.created_by_user_id,
            tach_time=tach_time,
            hobbs_time=hobbs_time,
            total_time=total_time,
            raw_text="\n".join(lines),
            review_status="verified" if min_confidence >= LOW_CONFIDENCE_THRESHOLD else "needs_review",
        )
        db.add(entry)
        db.flush()
        entries.append(entry)

        for span in line_spans:
            correction = span.corrections[-1] if span.corrections else None
            db.add(
                LogbookEntryEvidence(
                    logbook_entry_id=entry.id,
                    upload_id=job.upload_id,
                    ingestion_job_id=job.id,
                    ingestion_page_id=page.id,
                    ocr_text_span_id=span.id,
                    ocr_correction_id=correction.id if correction else None,
                    evidence_type="correction" if correction else "ocr_span",
                    field_name="description",
                    confidence=span.confidence,
                    extraction_provider_name=EXTRACTION_PROVIDER_NAME,
                    extraction_provider_version=EXTRACTION_PROVIDER_VERSION,
                    extraction_schema_version=EXTRACTION_SCHEMA_VERSION,
                )
            )

    job.entry_extraction_status = "complete"
    job.status = "complete"
    job.completed_at = datetime.now(timezone.utc)
    db.commit()
    return entries


def parse_date(text: str):
    match = re.search(r"\b(\d{4})-(\d{2})-(\d{2})\b", text)
    if not match:
        return datetime.now(timezone.utc).date()
    return datetime(int(match.group(1)), int(match.group(2)), int(match.group(3))).date()


def strip_date(text: str) -> str:
    return re.sub(r"^\s*\d{4}-\d{2}-\d{2}\s*", "", text).strip()


def parse_performer(lines: list[str]) -> tuple[str | None, str | None]:
    for line in lines:
        if line.lower().startswith("performer:"):
            value = line.split(":", 1)[1].strip()
            if " A&P" in value:
                name, credential = value.split(" A&P", 1)
                return name.strip(), f"A&P{credential}".strip()
            return value, None
    return None, None


def parse_float_field(lines: list[str], field_name: str) -> float | None:
    pattern = re.compile(rf"{field_name}:\s*([0-9]+(?:\.[0-9]+)?)", re.IGNORECASE)
    for line in lines:
        match = pattern.search(line)
        if match:
            return float(match.group(1))
    return None
