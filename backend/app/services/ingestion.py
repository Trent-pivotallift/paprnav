from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
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
from app.services.cost_tags import upload_billable_account_tag
from app.services.page_images import attach_page_image
from app.services.pdf_inspection import inspect_and_prepare_upload
from app.services.page_planning import (
    finalize_page_extraction_plan,
    mark_page_stage_failure,
)
from app.services.candidate_validation import validate_entry_candidate
from app.services.selective_ocr import process_upload_with_selective_routing

LOW_CONFIDENCE_THRESHOLD = 80.0
EXTRACTION_PROVIDER_NAME = "deterministic_logbook_extractor"
EXTRACTION_PROVIDER_VERSION = "0.1.0"
EXTRACTION_SCHEMA_VERSION = "logbook_entry_v1"
RIGHT_DESCRIPTION_COLUMN_LEFT = 0.45
ENTRY_ANCHOR_LOOKBACK_RATIO = 0.14
ENTRY_ANCHOR_GAP_RATIO = 0.02


@dataclass
class ExtractedEntryDraft:
    page: IngestionPage
    line_spans: list[OCRTextSpan]
    lines: list[str]
    field_spans: dict[str, OCRTextSpan]
    field_evidence_types: dict[str, str]
    entry_date: date | None
    date_was_extracted: bool
    description: str
    performer_name: str | None
    performer_credential: str | None
    tach_time: float | None
    hobbs_time: float | None
    total_time: float | None
    min_confidence: float | None
    requires_review: bool = False
    validation_result: dict | None = None


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
    settings = get_settings()
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

    job.status = "document_inspection"
    job.page_extraction_status = "running"
    inspect_and_prepare_upload(
        db=db,
        settings=settings,
        upload=upload,
        job=job,
    )
    provider = provider or get_ocr_provider()
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
        billing_status="chargeable" if upload.pilot_consent_accepted else "not_billable",
        billable_account_tag=upload_billable_account_tag(upload),
        billable_aircraft_tag=upload.cost_allocation_tags.get("Aircraft") if upload.cost_allocation_tags else None,
        cost_allocation_tags=upload.cost_allocation_tags,
    )
    db.add(run)
    db.flush()

    try:
        result = process_upload_with_selective_routing(
            settings=settings,
            upload=upload,
            pages=list(job.pages),
            provider=provider,
        )
        run.provider_name = result.provider_name
        run.provider_version = result.provider_version
        run.configuration_hash = result.configuration_hash
        if result.metadata:
            run.cost_allocation_tags = {
                **(run.cost_allocation_tags or {}),
                "OCRProvider": result.provider_name,
                "OCRProviderVersion": result.provider_version,
                **result.metadata,
            }
            run.processing_seconds = metadata_float(
                result.metadata,
                "processing_seconds",
            )
            run.pricing_unit = metadata_string(
                result.metadata,
                "pricing_unit",
            )
            run.pricing_rate_usd = metadata_float(
                result.metadata,
                "pricing_rate_usd",
                fallback_key="estimated_unit_cost_usd_per_page",
            )
            run.estimated_cost_usd = metadata_float(
                result.metadata,
                "estimated_cost_usd",
            )
        for page_result in result.pages:
            page = db.scalar(
                select(IngestionPage).where(
                    IngestionPage.ingestion_job_id == job.id,
                    IngestionPage.source_page_number == page_result.source_page_number,
                )
            )
            if page is None:
                page = IngestionPage(
                    ingestion_job_id=job.id,
                    upload_id=upload.id,
                    source_page_number=page_result.source_page_number,
                    current_page_order=page_result.source_page_number,
                    image_storage_backend=upload.storage_backend,
                    image_storage_key=upload.storage_key,
                )
                db.add(page)
                db.flush()
            page.page_label = page_result.page_label
            page.width_px = page.width_px or page_result.width_px
            page.height_px = page.height_px or page_result.height_px
            page.rotation_degrees = (
                page.rotation_degrees
                if page.rotation_degrees is not None
                else page_result.rotation_degrees
            )
            page.extraction_confidence = page_result.extraction_confidence
            if page.image_storage_key in {None, upload.storage_key}:
                attach_page_image(settings=settings, upload=upload, page=page)
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
                        polygon=span_result.polygon,
                        rotation_degrees=page_result.rotation_degrees,
                        reading_order=span_result.reading_order,
                        relationships=span_result.relationships,
                    )
                )
            db.flush()
            db.expire(page, ["ocr_spans"])
            finalize_page_extraction_plan(
                db,
                page=page,
                provider_name=page_result.source_provider_name or result.provider_name,
                provider_version=page_result.source_provider_version or result.provider_version,
            )

        returned_page_numbers = {
            page_result.source_page_number for page_result in result.pages
        }
        for page in job.pages:
            if page.source_page_number not in returned_page_numbers:
                mark_page_stage_failure(
                    page,
                    stage="recognition",
                    error_code="provider_page_missing",
                    retry_eligible=True,
                )

        run.status = "complete"
        run.billable_page_count = result.billable_page_count or len(result.pages)
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
        run.processing_seconds = max(
            (datetime.now(timezone.utc) - now).total_seconds(),
            0,
        )
        job.status = "failed"
        job.page_extraction_status = "failed"
        job.ocr_status = "failed"
        job.error_code = "ocr_provider_failed"
        job.error_message = str(exc)
        db.commit()
        return job


def metadata_float(
    metadata: dict,
    key: str,
    *,
    fallback_key: str | None = None,
) -> float | None:
    value = metadata.get(key)
    if value is None and fallback_key is not None:
        value = metadata.get(fallback_key)
    if value is None or isinstance(value, bool):
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed >= 0 else None


def metadata_string(metadata: dict, key: str) -> str | None:
    value = metadata.get(key)
    if not isinstance(value, str):
        return None
    normalized = value.strip()
    return normalized[:64] or None


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

    drafts: list[ExtractedEntryDraft] = []
    for page in sorted(job.pages, key=lambda item: item.current_page_order):
        page_drafts = entry_drafts_from_page(page)
        for draft in page_drafts:
            draft.validation_result = validate_entry_candidate(draft)
        drafts.extend(page_drafts)
        stages = dict(page.stage_results or {})
        stages["validation"] = {
            "status": "complete",
            "attemptNumber": 1,
            "profile": "logbook-candidate-validation-v1",
            "candidateCount": len(page_drafts),
            "rejectedCandidateCount": sum(
                draft.validation_result["status"] == "rejected"
                for draft in page_drafts
            ),
        }
        page.stage_results = stages

    entries: list[LogbookEntry] = []
    for draft in sorted(drafts, key=lambda item: (item.entry_date or date.max, item.page.current_page_order)):
        entry = LogbookEntry(
            aircraft_id=job.aircraft_id,
            logbook_section_id=section.id,
            entry_date=draft.entry_date,
            description=draft.description,
            performer_name=draft.performer_name,
            performer_credential=draft.performer_credential,
            source_type="ocr_ingestion",
            created_by_user_id=job.created_by_user_id,
            tach_time=draft.tach_time,
            hobbs_time=draft.hobbs_time,
            total_time=draft.total_time,
            raw_text="\n".join(draft.lines),
            review_status=(
                "verified"
                if not draft.requires_review
                and draft.validation_result is not None
                and draft.validation_result["acceptedForAutomaticVerification"]
                and draft.date_was_extracted
                and draft.min_confidence is not None
                and draft.min_confidence >= LOW_CONFIDENCE_THRESHOLD
                else "needs_review"
            ),
            validation_status=(
                draft.validation_result["status"]
                if draft.validation_result
                else "not_run"
            ),
            validation_results=draft.validation_result,
        )
        db.add(entry)
        db.flush()
        entries.append(entry)

        for field_name, span in draft.field_spans.items():
            add_entry_evidence(
                db,
                job,
                entry,
                draft.page,
                span,
                field_name,
                evidence_type=draft.field_evidence_types.get(field_name),
                validation_result=draft.validation_result,
            )

    job.entry_extraction_status = "complete"
    job.status = "complete"
    job.completed_at = datetime.now(timezone.utc)
    db.commit()
    return entries


ISO_DATE_PATTERN = re.compile(r"(?<!\d)(\d{4})-(\d{2})-(\d{2})(?!\d)")
SHORT_DATE_PATTERN = re.compile(
    r"(?<!\d)(\d{1,2})\s*[-/]\s*(\d{1,2})\s*[-/]\s*(\d{2,4})(?!\d)"
)


def entry_drafts_from_page(page: IngestionPage) -> list[ExtractedEntryDraft]:
    line_spans = [
        span
        for span in page.ocr_spans
        if is_text_bearing_ocr_span(span)
        and not is_ignorable_logbook_line(effective_span_text(span))
    ]
    if not line_spans:
        return []
    line_spans = sorted(line_spans, key=lambda item: (span_center_y(item), item.bbox_left or 0, item.reading_order))
    clusters = [
        cluster
        for cluster in split_logbook_entry_line_clusters(page, line_spans)
        if cluster_has_logbook_entry_signal(cluster)
    ]
    requires_review = len(clusters) > 1
    return [draft_from_line_cluster(page, cluster, requires_review=requires_review) for cluster in clusters if cluster]


def split_logbook_entry_line_clusters(page: IngestionPage, line_spans: list[OCRTextSpan]) -> list[list[OCRTextSpan]]:
    has_analysis_structure = any(
        span.span_type.upper()
        in {"TABLE", "CELL", "MERGED_CELL", "LAYOUT_TABLE", "SIGNATURE"}
        or span.span_type.upper().startswith("REGION_")
        for span in page.ocr_spans
    )
    if has_analysis_structure:
        column_clusters = split_side_by_side_logbook_columns(line_spans)
        if len(column_clusters) > 1:
            return column_clusters

    anchors = [span for span in line_spans if is_entry_anchor_line(span)]
    if len(anchors) <= 1:
        return [line_spans]

    anchors = sorted(anchors, key=lambda item: (span_center_y(item), item.bbox_left or 0))
    clusters: list[list[OCRTextSpan]] = []
    for index, anchor in enumerate(anchors):
        previous_anchor = anchors[index - 1] if index else None
        next_anchor = anchors[index + 1] if index + 1 < len(anchors) else None
        anchor_top = float(anchor.bbox_top or 0)
        start_top = max(0.0, anchor_top - ENTRY_ANCHOR_LOOKBACK_RATIO)
        if previous_anchor is not None:
            start_top = max(start_top, midpoint(span_center_y(previous_anchor), span_center_y(anchor)))
        end_top = 1.0
        if next_anchor is not None:
            end_top = max(start_top, span_center_y(next_anchor) - ENTRY_ANCHOR_GAP_RATIO)

        cluster = [
            span
            for span in line_spans
            if start_top <= span_center_y(span) < end_top and entry_cluster_line_is_relevant(span, anchor)
        ]
        if anchor not in cluster:
            cluster.append(anchor)
        clusters.append(sorted(unique_spans(cluster), key=lambda item: (span_center_y(item), item.bbox_left or 0, item.reading_order)))

    return clusters


def split_side_by_side_logbook_columns(line_spans: list[OCRTextSpan]) -> list[list[OCRTextSpan]]:
    left_cluster = [
        span
        for span in line_spans
        if span_center_x(span) < RIGHT_DESCRIPTION_COLUMN_LEFT and not is_table_column_heading(effective_span_text(span))
    ]
    right_cluster = [
        span
        for span in line_spans
        if span_center_x(span) >= RIGHT_DESCRIPTION_COLUMN_LEFT and not is_table_column_heading(effective_span_text(span))
    ]
    clusters = [cluster for cluster in (left_cluster, right_cluster) if cluster_has_logbook_entry_signal(cluster)]
    if len(clusters) < 2:
        return []
    return [
        sorted(unique_spans(cluster), key=lambda item: (span_center_y(item), item.bbox_left or 0, item.reading_order))
        for cluster in clusters
    ]


def cluster_has_logbook_entry_signal(line_spans: list[OCRTextSpan]) -> bool:
    if not line_spans:
        return False
    text = "\n".join(effective_span_text(span).lower() for span in line_spans)
    if any(is_entry_anchor_line(span) for span in line_spans):
        return True
    if re.search(
        r"\b(?:annual inspection|maintenance (?:accomplished|completed|performed))\b",
        text,
        flags=re.IGNORECASE,
    ):
        return True
    if re.search(
        r"\b(?:tach|hobbs|total(?:\s+time)?)\s*[:=]?\s*\d",
        text,
        flags=re.IGNORECASE,
    ):
        return True
    if re.search(
        r"\b(?:n\d{1,5}[a-z]{0,2}|a&p|ia\b|faa\s+crs|part\s+no|p/n|"
        r"serial\s+no|ser\.?\s*no|far\s+\d|cfr\s*\d|ad\s+\d{1,4}[-/]\d)",
        text,
        flags=re.IGNORECASE,
    ):
        return True
    has_action = re.search(
        r"\b(?:checked|complied|inspected|installed|lubricated|overhauled|"
        r"removed|repaired|replaced|serviced|tested)\b",
        text,
        flags=re.IGNORECASE,
    )
    has_maintenance_subject = re.search(
        r"\b(?:aircraft|altimeter|battery|brake|elt|engine|filter|fuel|"
        r"magneto|oil|propeller|seat|transponder|tire)\b",
        text,
        flags=re.IGNORECASE,
    )
    return bool(has_action and has_maintenance_subject)


def draft_from_line_cluster(page: IngestionPage, line_spans: list[OCRTextSpan], *, requires_review: bool = False) -> ExtractedEntryDraft:
    lines = [
        line.strip()
        for span in line_spans
        for line in effective_span_text(span).splitlines()
        if line.strip()
    ]
    anchor_span = next((span for span in line_spans if is_entry_anchor_line(span)), line_spans[0])
    anchor_text = effective_span_text(anchor_span)
    entry_date, date_was_extracted = parse_date(anchor_text)
    description = build_entry_description(lines, entry_date=entry_date)
    performer_name, performer_credential = parse_performer(lines)
    tach_time = parse_float_field(lines, "Tach")
    hobbs_time = parse_float_field(lines, "Hobbs")
    total_time = parse_float_field(lines, "Total")
    field_spans, field_evidence_types = extraction_field_spans(line_spans)
    field_spans["entry_date"] = anchor_span
    if date_was_extracted:
        field_evidence_types.pop("entry_date", None)
    else:
        field_evidence_types["entry_date"] = "fallback"
    available_confidences = [
        span.confidence
        for span in line_spans
        if span.confidence is not None
    ]
    min_confidence = (
        min(available_confidences)
        if available_confidences
        else None
    )
    return ExtractedEntryDraft(
        page=page,
        line_spans=line_spans,
        lines=lines,
        field_spans=field_spans,
        field_evidence_types=field_evidence_types,
        entry_date=entry_date,
        date_was_extracted=date_was_extracted,
        description=description,
        performer_name=performer_name,
        performer_credential=performer_credential,
        tach_time=tach_time,
        hobbs_time=hobbs_time,
        total_time=total_time,
        min_confidence=min_confidence,
        requires_review=requires_review,
    )


def is_entry_anchor_line(span: OCRTextSpan) -> bool:
    text = effective_span_text(span)
    if not parse_date(text)[1]:
        return False
    if re.search(
        r"\bAD(?:s|'s)?\s*[:#]?\s*\d{2,4}[-/]\d{1,2}[-/]\d{1,2}\b",
        text,
        flags=re.IGNORECASE,
    ):
        return False
    lowered = text.lower()
    has_logbook_signal = any(token in lowered for token in ("tach", "total", "date", "aircraft", "avionics", "service"))
    return has_logbook_signal or date_appears_near_line_start(text)


def is_text_bearing_ocr_span(span: OCRTextSpan) -> bool:
    span_type = span.span_type.upper()
    return span_type == "LINE" or span_type.startswith("REGION_")


def span_requires_raw_ocr_correction(span: OCRTextSpan) -> bool:
    return (
        span.span_type.upper() == "LINE"
        and span.confidence is not None
        and span.confidence < LOW_CONFIDENCE_THRESHOLD
    )


def entry_cluster_line_is_relevant(span: OCRTextSpan, anchor: OCRTextSpan) -> bool:
    text = effective_span_text(span)
    if is_ignorable_logbook_line(text):
        return False
    left = float(span.bbox_left or 0)
    anchor_left = float(anchor.bbox_left or 0)
    if left >= RIGHT_DESCRIPTION_COLUMN_LEFT:
        return True
    if abs(span_center_y(span) - span_center_y(anchor)) <= 0.12:
        return True
    return anchor_left < RIGHT_DESCRIPTION_COLUMN_LEFT and left < RIGHT_DESCRIPTION_COLUMN_LEFT


def is_ignorable_logbook_line(text: str) -> bool:
    normalized = text.strip()
    lowered = normalized.lower()
    if not normalized or normalized == "-":
        return True
    if "\n" in normalized:
        return all(
            is_ignorable_logbook_line(line)
            for line in normalized.splitlines()
            if line.strip()
        )
    header_fragments = (
        "description of inspections",
        "entries must be endorsed",
        "recording",
        "today's",
        "total time in service",
        "year:",
    )
    if lowered in {"total", "tach", "flight", "date", "year"}:
        return True
    if lowered in {"time", "time in", "service"}:
        return True
    if lowered.startswith("facility.") or lowered.startswith("see back pages"):
        return True
    return any(fragment == lowered or lowered.startswith(fragment) for fragment in header_fragments)


def is_table_column_heading(text: str) -> bool:
    lowered = text.strip().lower()
    return lowered in {"total", "today's", "today", "recording", "year:", "tach", "date", "flight"}


def build_entry_description(
    lines: list[str],
    *,
    entry_date: date | None = None,
) -> str:
    useful_lines = []
    entry_date_removed = False
    for line in lines:
        if line.strip().lower().startswith("date") and not parse_date(line)[1]:
            continue
        if entry_date is not None and not entry_date_removed:
            line, entry_date_removed = strip_matching_date(line, entry_date)
        text = strip_entry_metrics(line).strip()
        if text and not is_ignorable_logbook_line(text):
            useful_lines.append(text)
    return "\n".join(dict.fromkeys(useful_lines)).strip()


def span_center_y(span: OCRTextSpan) -> float:
    return float(span.bbox_top or 0) + float(span.bbox_height or 0) / 2


def span_center_x(span: OCRTextSpan) -> float:
    return float(span.bbox_left or 0) + float(span.bbox_width or 0) / 2


def unique_spans(spans: list[OCRTextSpan]) -> list[OCRTextSpan]:
    seen: set[str] = set()
    unique: list[OCRTextSpan] = []
    for span in spans:
        span_id = span.id or span.provider_block_id or str(id(span))
        if span_id in seen:
            continue
        seen.add(span_id)
        unique.append(span)
    return unique


def midpoint(first: float, second: float) -> float:
    return first + (second - first) / 2


def add_entry_evidence(
    db: Session,
    job: IngestionJob,
    entry: LogbookEntry,
    page: IngestionPage,
    span: OCRTextSpan,
    field_name: str,
    evidence_type: str | None = None,
    validation_result: dict | None = None,
) -> None:
    correction = span.corrections[-1] if span.corrections else None
    db.add(
        LogbookEntryEvidence(
            logbook_entry_id=entry.id,
            upload_id=job.upload_id,
            ingestion_job_id=job.id,
            ingestion_page_id=page.id,
            ocr_text_span_id=span.id,
            ocr_correction_id=correction.id if correction else None,
            evidence_type=evidence_type or ("correction" if correction else "ocr_span"),
            field_name=field_name,
            confidence=span.confidence,
            extraction_provider_name=EXTRACTION_PROVIDER_NAME,
            extraction_provider_version=EXTRACTION_PROVIDER_VERSION,
            extraction_schema_version=EXTRACTION_SCHEMA_VERSION,
            review_metadata={
                "validationProfile": validation_result.get("profile"),
                "validationStatus": validation_result.get("status"),
                "fieldValidation": validation_result.get("fieldResults", {}).get(field_name),
            }
            if validation_result
            else None,
        )
    )


def extraction_field_spans(line_spans: list[OCRTextSpan]) -> tuple[dict[str, OCRTextSpan], dict[str, str]]:
    field_spans: dict[str, OCRTextSpan] = {}
    field_evidence_types: dict[str, str] = {}
    if not line_spans:
        return field_spans, field_evidence_types

    first_line = effective_span_text(line_spans[0])
    field_spans["entry_date"] = line_spans[0]
    if not parse_date(first_line)[1]:
        field_evidence_types["entry_date"] = "fallback"
    field_spans["description"] = line_spans[0]

    performer_span = find_line_span(
        line_spans,
        lambda text: any(
            parse_performer([line]) != (None, None)
            for line in text.splitlines()
        ),
    )
    if performer_span is not None:
        field_spans["performer_name"] = performer_span
        field_spans["performer_credential"] = performer_span

    for field_name in ("tach_time", "hobbs_time", "total_time"):
        span = find_float_field_span(line_spans, field_name)
        if span is not None:
            field_spans[field_name] = span

    return field_spans, field_evidence_types


def find_line_span(line_spans: list[OCRTextSpan], predicate) -> OCRTextSpan | None:
    for span in line_spans:
        if predicate(effective_span_text(span)):
            return span
    return None


def find_float_field_span(line_spans: list[OCRTextSpan], field_name: str) -> OCRTextSpan | None:
    label = field_name.removesuffix("_time").replace("_", " ").title()
    for span in line_spans:
        if parse_float_field([effective_span_text(span)], label) is not None:
            return span
    return None


def parse_date(text: str) -> tuple[date | None, bool]:
    matches = [
        (match.start(), "iso", match)
        for match in ISO_DATE_PATTERN.finditer(text)
    ]
    matches.extend(
        (match.start(), "short", match)
        for match in SHORT_DATE_PATTERN.finditer(text)
    )
    if not matches:
        return None, False
    for _, date_format, match in sorted(matches, key=lambda item: item[0]):
        if date_format == "iso":
            year = int(match.group(1))
            month = int(match.group(2))
            day = int(match.group(3))
        else:
            month = int(match.group(1))
            day = int(match.group(2))
            year = int(match.group(3))
        if year < 100:
            year += 2000 if year < 70 else 1900
        try:
            return datetime(year, month, day).date(), True
        except ValueError:
            continue
    return None, False


def date_appears_near_line_start(text: str) -> bool:
    iso_match = ISO_DATE_PATTERN.search(text)
    short_match = SHORT_DATE_PATTERN.search(text)
    positions = [match.start() for match in (iso_match, short_match) if match]
    return bool(positions and min(positions) <= 16)


def strip_matching_date(text: str, entry_date: date) -> tuple[str, bool]:
    matches = sorted(
        (
            match
            for pattern in (ISO_DATE_PATTERN, SHORT_DATE_PATTERN)
            for match in pattern.finditer(text)
        ),
        key=lambda item: item.start(),
    )
    for match in matches:
        parsed_date, extracted = parse_date(match.group(0))
        if extracted and parsed_date == entry_date:
            updated = f"{text[:match.start()]}{text[match.end():]}"
            updated = re.sub(
                r"(Date|DATE)\s*[:=]?\s*$",
                "",
                updated[: match.start()],
            ) + updated[match.start():]
            return re.sub(r"\s{2,}", " ", updated).strip(), True
    return text, False


def strip_date(text: str) -> str:
    matches = sorted(
        (
            match
            for pattern in (ISO_DATE_PATTERN, SHORT_DATE_PATTERN)
            for match in pattern.finditer(text)
        ),
        key=lambda item: item.start(),
    )
    if not matches:
        return text
    match = matches[0]
    prefix = text[: match.start()].strip()
    if prefix and not re.fullmatch(r"Date\s*[:=]?", prefix, flags=re.IGNORECASE):
        return text
    parsed_date, extracted = parse_date(match.group(0))
    if not extracted or parsed_date is None:
        return text
    updated, _ = strip_matching_date(text, parsed_date)
    return re.sub(r"^\s*(Date|DATE)\s*[:=]?\s*", "", updated).strip()


def strip_entry_metrics(text: str) -> str:
    text = re.sub(r"\bTach\s*[-:=]?\s*[0-9]+(?:\.[0-9]+)?\b", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\bTotal(?:\s+Time)?\s*[-:=]?\s*[0-9]+(?:\.[0-9]+)?\b", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\bHobbs\s*[-:=]?\s*[0-9]+(?:\.[0-9]+)?\b", "", text, flags=re.IGNORECASE)
    return re.sub(r"\s{2,}", " ", text).strip(" -;")


def parse_performer(lines: list[str]) -> tuple[str | None, str | None]:
    clean_lines = [line.strip() for line in lines if line.strip()]
    for line in clean_lines:
        if line.lower().startswith("performer:"):
            value = line.split(":", 1)[1].strip()
            if " A&P" in value:
                name, credential = value.split(" A&P", 1)
                return name.strip(), f"A&P{credential}".strip()
            return value, None
    joined = "\n".join(clean_lines)
    facility_match = re.search(
        r"(?m)^([A-Z][A-Za-z0-9 &'./-]{2,80}?)\s+FAA\s+CRS\s*#?\s*"
        r"([A-Z0-9-]+)(?=\s|$)",
        joined,
    )
    work_order_match = re.search(
        r"\bW\.?\s*O\.?\s*(?:(?:Reference|Ref\.?)\s*#?\s*|#\s*)"
        r"([A-Z0-9-]+)",
        joined,
        re.IGNORECASE,
    )
    if facility_match:
        credentials = [f"FAA CRS#{facility_match.group(2)}"]
        if work_order_match:
            credentials.append(f"W.O. #{work_order_match.group(1)}")
        return facility_match.group(1).strip(), "; ".join(credentials)

    credential_pattern = re.compile(
        r"\bA\s*&\s*P\s*#?\s*([A-Z0-9-]+)(?:\s+(I\.?\s*A\.?))?",
        re.IGNORECASE,
    )
    for index, line in enumerate(clean_lines):
        credential_match = credential_pattern.search(line)
        if not credential_match:
            continue
        credential = f"A&P#{credential_match.group(1)}"
        if credential_match.group(2):
            credential += " I.A."
        name_prefix = line[:credential_match.start()].strip(" ,-/")
        if name_prefix and re.fullmatch(r"[A-Za-z][A-Za-z .'-]{2,80}", name_prefix):
            return name_prefix, credential
        if index > 0:
            previous = clean_lines[index - 1].strip(" ,-/")
            if (
                not previous.lower().startswith(("this date", "date"))
                and re.fullmatch(r"[A-Za-z][A-Za-z .'-]{2,80}", previous)
            ):
                return previous, credential
        return None, credential
    return None, None


def parse_float_field(lines: list[str], field_name: str) -> float | None:
    labels = [field_name]
    if field_name.lower() == "total":
        labels.append("Total Time")
    label_pattern = "|".join(re.escape(label) for label in labels)
    pattern = re.compile(rf"\b(?:{label_pattern})\s*[-:=]?\s*([0-9]+(?:\.[0-9]+)?)", re.IGNORECASE)
    for line in lines:
        match = pattern.search(line)
        if match:
            candidate_text = match.group(1)
            standalone_values = [
                standalone.group(1)
                for item in lines
                if (standalone := re.fullmatch(
                    r"\s*([0-9]{3,6}(?:\.[0-9]+)?)\s*(?:hrs?\.?)?\s*",
                    item,
                    re.IGNORECASE,
                ))
            ]
            if any(
                value != candidate_text
                and len(value.split(".", 1)[0]) == len(candidate_text.split(".", 1)[0])
                and sum(
                    first != second
                    for first, second in zip(
                        value.split(".", 1)[0],
                        candidate_text.split(".", 1)[0],
                    )
                ) == 1
                for value in standalone_values
            ):
                return None
            return float(match.group(1))
    return None
