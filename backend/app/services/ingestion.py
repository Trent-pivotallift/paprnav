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
    min_confidence: float
    requires_review: bool = False


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
        result = provider.process_upload(
            original_filename=upload.original_filename,
            content_type=upload.content_type,
            storage_backend=upload.storage_backend,
            storage_key=upload.storage_key,
        )
        if result.metadata:
            run.cost_allocation_tags = {
                **(run.cost_allocation_tags or {}),
                "OCRProvider": result.provider_name,
                "OCRProviderVersion": result.provider_version,
                **result.metadata,
            }
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
                        polygon=[],
                        rotation_degrees=page_result.rotation_degrees,
                        reading_order=span_result.reading_order,
                        relationships=span_result.relationships,
                    )
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

    drafts: list[ExtractedEntryDraft] = []
    for page in sorted(job.pages, key=lambda item: item.current_page_order):
        drafts.extend(entry_drafts_from_page(page))

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
                and draft.date_was_extracted
                and draft.min_confidence >= LOW_CONFIDENCE_THRESHOLD
                else "needs_review"
            ),
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
            )

    job.entry_extraction_status = "complete"
    job.status = "complete"
    job.completed_at = datetime.now(timezone.utc)
    db.commit()
    return entries


ISO_DATE_PATTERN = re.compile(r"\b(\d{4})-(\d{2})-(\d{2})\b")
SHORT_DATE_PATTERN = re.compile(r"\b(\d{1,2})\s*[-/]\s*(\d{1,2})\s*[-/]\s*(\d{2,4})\b")


def entry_drafts_from_page(page: IngestionPage) -> list[ExtractedEntryDraft]:
    line_spans = [
        span
        for span in page.ocr_spans
        if span.span_type.upper() == "LINE" and not is_ignorable_logbook_line(effective_span_text(span))
    ]
    if not line_spans:
        return []
    line_spans = sorted(line_spans, key=lambda item: (span_center_y(item), item.bbox_left or 0, item.reading_order))
    clusters = split_logbook_entry_line_clusters(page, line_spans)
    requires_review = len(clusters) > 1
    return [draft_from_line_cluster(page, cluster, requires_review=requires_review) for cluster in clusters if cluster]


def split_logbook_entry_line_clusters(page: IngestionPage, line_spans: list[OCRTextSpan]) -> list[list[OCRTextSpan]]:
    has_analysis_structure = any(
        span.span_type.upper() in {"TABLE", "CELL", "MERGED_CELL", "LAYOUT_TABLE", "SIGNATURE"}
        for span in page.ocr_spans
    )
    if has_analysis_structure:
        column_clusters = split_side_by_side_logbook_columns(line_spans)
        if len(column_clusters) > 1:
            return column_clusters

    anchors = [span for span in line_spans if is_entry_anchor_line(span)]
    if not has_analysis_structure or len(anchors) <= 1:
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
    if len(line_spans) < 2:
        return False
    text = "\n".join(effective_span_text(span).lower() for span in line_spans)
    signals = ("aircraft service", "avionics", "annual inspection", "transponder", "altimeter", "tach", "total time")
    return any(signal in text for signal in signals) or any(is_entry_anchor_line(span) for span in line_spans)


def draft_from_line_cluster(page: IngestionPage, line_spans: list[OCRTextSpan], *, requires_review: bool = False) -> ExtractedEntryDraft:
    lines = [effective_span_text(span) for span in line_spans]
    anchor_span = next((span for span in line_spans if is_entry_anchor_line(span)), line_spans[0])
    anchor_text = effective_span_text(anchor_span)
    entry_date, date_was_extracted = parse_date(anchor_text)
    description = build_entry_description(lines)
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
    min_confidence = min((span.confidence or 0 for span in line_spans), default=0)
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
    lowered = text.lower()
    has_logbook_signal = any(token in lowered for token in ("tach", "total", "date", "aircraft", "avionics", "service"))
    return has_logbook_signal or date_appears_near_line_start(text)


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
    header_fragments = (
        "description of inspections",
        "entries must be endorsed",
        "recording",
        "today's",
        "total time in service",
        "year:",
    )
    if lowered in {"total", "tach", "flight", "date"}:
        return True
    if lowered in {"time", "time in", "service"}:
        return True
    if lowered.startswith("facility.") or "see back pages" in lowered:
        return True
    return any(fragment == lowered or lowered.startswith(fragment) for fragment in header_fragments)


def is_table_column_heading(text: str) -> bool:
    lowered = text.strip().lower()
    return lowered in {"total", "today's", "today", "recording", "year:", "tach", "date", "flight"}


def build_entry_description(lines: list[str]) -> str:
    useful_lines = []
    for line in lines:
        if line.strip().lower().startswith("date") and not parse_date(line)[1]:
            continue
        text = strip_entry_metrics(strip_date(line)).strip()
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

    performer_span = find_line_span(line_spans, lambda text: text.lower().startswith("performer:"))
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
    match = ISO_DATE_PATTERN.search(text)
    if match:
        return datetime(int(match.group(1)), int(match.group(2)), int(match.group(3))).date(), True
    match = SHORT_DATE_PATTERN.search(text)
    if not match:
        return None, False
    month = int(match.group(1))
    day = int(match.group(2))
    year = int(match.group(3))
    if year < 100:
        year += 2000 if year < 70 else 1900
    try:
        return datetime(year, month, day).date(), True
    except ValueError:
        return None, False


def date_appears_near_line_start(text: str) -> bool:
    iso_match = ISO_DATE_PATTERN.search(text)
    short_match = SHORT_DATE_PATTERN.search(text)
    positions = [match.start() for match in (iso_match, short_match) if match]
    return bool(positions and min(positions) <= 16)


def strip_date(text: str) -> str:
    text = ISO_DATE_PATTERN.sub("", text, count=1).strip()
    text = SHORT_DATE_PATTERN.sub("", text, count=1).strip()
    return re.sub(r"^\s*(Date|DATE)\s*[:=]?\s*", "", text).strip()


def strip_entry_metrics(text: str) -> str:
    text = re.sub(r"\bTach\s*[:=]?\s*[0-9]+(?:\.[0-9]+)?\b", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\bTotal(?:\s+Time)?\s*[:=]?\s*[0-9]+(?:\.[0-9]+)?\b", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\bHobbs\s*[:=]?\s*[0-9]+(?:\.[0-9]+)?\b", "", text, flags=re.IGNORECASE)
    return re.sub(r"\s{2,}", " ", text).strip(" -;")


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
    labels = [field_name]
    if field_name.lower() == "total":
        labels.append("Total Time")
    label_pattern = "|".join(re.escape(label) for label in labels)
    pattern = re.compile(rf"\b(?:{label_pattern})\s*[:=]?\s*([0-9]+(?:\.[0-9]+)?)", re.IGNORECASE)
    for line in lines:
        match = pattern.search(line)
        if match:
            return float(match.group(1))
    return None
