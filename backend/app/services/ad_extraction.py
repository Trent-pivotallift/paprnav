import re
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.core import ADExtraction, ADExtractionReview, AirworthinessDirective
from app.services.ad_discovery import extract_ad_number
from app.services.observability import record_product_event, record_workflow_status

PROVIDER_NAME = "deterministic_ad_extractor"
PROVIDER_VERSION = "0.1.0"
SCHEMA_VERSION = "ad_extraction_v1"
REVIEW_THRESHOLD = 0.86
AD_NUMBER_PATTERN = re.compile(r"\b(?:AD\s*)?(\d{4}-\d{2}-\d{2})\b", re.IGNORECASE)


def process_pending_ad_extractions(db: Session, limit: int = 20) -> dict[str, int]:
    directives = db.scalars(
        select(AirworthinessDirective)
        .where(AirworthinessDirective.extraction_status.in_(["not_started", "needs_review"]))
        .options(selectinload(AirworthinessDirective.discovery_record), selectinload(AirworthinessDirective.extractions))
        .limit(limit)
    ).all()
    stats = {"seen": 0, "extracted": 0, "review_queued": 0, "approved": 0}
    for directive in directives:
        stats["seen"] += 1
        extraction = extract_directive(db, directive)
        stats["extracted"] += 1
        if extraction.status == "needs_review":
            stats["review_queued"] += 1
        if extraction.status == "approved":
            stats["approved"] += 1
    record_product_event(
        db,
        event_type="ad_extraction_worker_completed",
        subject_type="ad_extraction",
        subject_id="batch",
        event_source="worker",
        properties=stats,
    )
    record_workflow_status(
        db,
        workflow_type="ad_extraction",
        workflow_id="batch",
        new_status="complete",
        reason=f"extracted={stats['extracted']} review_queued={stats['review_queued']}",
        actor_type="worker",
    )
    db.commit()
    return stats


def extract_directive(db: Session, directive: AirworthinessDirective) -> ADExtraction:
    record = directive.discovery_record
    existing = db.scalar(
        select(ADExtraction).where(
            ADExtraction.directive_id == directive.id,
            ADExtraction.input_content_hash == directive.source_content_hash,
            ADExtraction.provider_name == PROVIDER_NAME,
            ADExtraction.provider_version == PROVIDER_VERSION,
            ADExtraction.schema_version == SCHEMA_VERSION,
        )
    )
    if existing:
        ensure_review_for_extraction(db, directive, existing)
        return existing

    output, confidence, citations = build_extraction_output(directive)
    validate_extraction_output(output)
    status = "approved" if confidence >= REVIEW_THRESHOLD else "needs_review"
    extraction = ADExtraction(
        directive_id=directive.id,
        provider_name=PROVIDER_NAME,
        provider_version=PROVIDER_VERSION,
        schema_version=SCHEMA_VERSION,
        input_content_hash=directive.source_content_hash,
        status=status,
        confidence=confidence,
        output=output,
        citations=citations,
        raw_response={"mode": "deterministic", "schemaVersion": SCHEMA_VERSION},
    )
    db.add(extraction)
    db.flush()
    ensure_review_for_extraction(db, directive, extraction)
    return extraction


def ensure_review_for_extraction(db: Session, directive: AirworthinessDirective, extraction: ADExtraction) -> None:
    if extraction.status == "approved":
        directive.extraction_status = "complete"
        directive.review_status = "approved"
        directive.approved_at = directive.approved_at or datetime.now(timezone.utc)
        return

    directive.extraction_status = "needs_review"
    directive.review_status = "pending"
    existing_review = db.scalar(select(ADExtractionReview).where(ADExtractionReview.extraction_id == extraction.id))
    if existing_review:
        return
    db.add(
        ADExtractionReview(
            extraction_id=extraction.id,
            status="pending",
            proposed_output=extraction.output,
        )
    )
    db.flush()


def build_extraction_output(directive: AirworthinessDirective) -> tuple[dict[str, Any], float, list[dict[str, str]]]:
    record = directive.discovery_record
    source_text = "\n".join(filter(None, [record.title, record.abstract, record.excerpts]))
    title_subject = subject_from_title(record.title)
    ad_number = directive.ad_number or extract_ad_number(source_text)
    superseded_numbers = sorted({match for match in AD_NUMBER_PATTERN.findall(source_text) if match != ad_number})
    confidence = 0.72
    if ad_number:
        confidence += 0.08
    if title_subject:
        confidence += 0.04
    if "supersed" in source_text.lower():
        confidence += 0.03
    confidence = min(confidence, 0.93)

    output = {
        "adNumber": ad_number,
        "title": record.title,
        "effectiveDate": record.effective_date.isoformat() if record.effective_date else None,
        "publicationDate": record.publication_date.isoformat() if record.publication_date else None,
        "affectedProducts": [title_subject] if title_subject else [],
        "complianceActions": [],
        "complianceIntervals": [],
        "supersedesAdNumbers": superseded_numbers,
        "sourceUrls": {
            "html": record.html_url,
            "pdf": record.pdf_url,
            "publicInspectionPdf": record.public_inspection_pdf_url,
        },
    }
    if "airworthiness directive" in source_text.lower():
        output["complianceActions"].append("Review source document for required corrective actions.")

    citations = [
        {
            "field": "title",
            "source": "federal_register",
            "text": record.title,
        }
    ]
    return output, confidence, citations


def validate_extraction_output(output: dict[str, Any]) -> None:
    required_keys = {
        "adNumber",
        "title",
        "effectiveDate",
        "publicationDate",
        "affectedProducts",
        "complianceActions",
        "complianceIntervals",
        "supersedesAdNumbers",
        "sourceUrls",
    }
    missing = required_keys.difference(output)
    if missing:
        raise ValueError(f"AD extraction output is missing required keys: {', '.join(sorted(missing))}")
    for list_key in ["affectedProducts", "complianceActions", "complianceIntervals", "supersedesAdNumbers"]:
        if not isinstance(output[list_key], list):
            raise ValueError(f"AD extraction field {list_key} must be a list")
    if not isinstance(output["sourceUrls"], dict):
        raise ValueError("AD extraction field sourceUrls must be an object")


def subject_from_title(title: str | None) -> str | None:
    if not title:
        return None
    if ";" in title:
        return title.split(";", 1)[1].strip() or None
    return None
