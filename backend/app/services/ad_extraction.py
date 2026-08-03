from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from typing import Any, Protocol

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.config import get_settings
from app.models.core import ADExtraction, ADExtractionReview, AirworthinessDirective
from app.services.ad_applicability import populate_applicability_from_extraction
from app.services.ad_discovery import extract_ad_number
from app.services.observability import record_product_event, record_workflow_status

PROVIDER_NAME = "deterministic_ad_extractor"
PROVIDER_VERSION = "0.1.0"
OPENAI_PROVIDER_NAME = "openai_responses_ad_extractor"
OPENAI_PROMPT_VERSION = "ad_extraction_prompt_v1"
SCHEMA_VERSION = "ad_extraction_v1"
REVIEW_THRESHOLD = 0.86
LLM_REVIEW_THRESHOLD = 0.80
AD_NUMBER_PATTERN = re.compile(r"\b(?:AD\s*)?(\d{4}-\d{2}-\d{2})\b", re.IGNORECASE)
AD_EXTRACTION_SYSTEM_PROMPT = """Extract structured FAA Airworthiness Directive data for paprnav.
Return only facts supported by the supplied source text. Use null or empty lists when the source does not support a field.
Confidence is your 0.0-1.0 estimate that the extracted fields are complete and source-supported.
Set uncertaintyReasons when applicability, compliance, dates, or supersession data are missing or ambiguous."""
AD_EXTRACTION_JSON_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "adNumber",
        "title",
        "effectiveDate",
        "publicationDate",
        "affectedProducts",
        "complianceActions",
        "complianceIntervals",
        "supersedesAdNumbers",
        "sourceUrls",
        "confidence",
        "citations",
        "uncertaintyReasons",
    ],
    "properties": {
        "adNumber": {"type": ["string", "null"]},
        "title": {"type": ["string", "null"]},
        "effectiveDate": {"type": ["string", "null"]},
        "publicationDate": {"type": ["string", "null"]},
        "affectedProducts": {"type": "array", "items": {"type": "string"}},
        "complianceActions": {"type": "array", "items": {"type": "string"}},
        "complianceIntervals": {"type": "array", "items": {"type": "string"}},
        "supersedesAdNumbers": {"type": "array", "items": {"type": "string"}},
        "sourceUrls": {
            "type": "object",
            "additionalProperties": False,
            "required": ["html", "pdf", "publicInspectionPdf"],
            "properties": {
                "html": {"type": ["string", "null"]},
                "pdf": {"type": ["string", "null"]},
                "publicInspectionPdf": {"type": ["string", "null"]},
            },
        },
        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
        "citations": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["field", "source", "text"],
                "properties": {
                    "field": {"type": "string"},
                    "source": {"type": "string"},
                    "text": {"type": "string"},
                },
            },
        },
        "uncertaintyReasons": {"type": "array", "items": {"type": "string"}},
    },
}


class ADExtractionProvider(Protocol):
    provider_name: str
    provider_version: str

    def extract(self, directive: AirworthinessDirective) -> dict[str, Any]:
        ...


def process_pending_ad_extractions(
    db: Session,
    limit: int = 20,
    llm_provider: ADExtractionProvider | None = None,
) -> dict[str, int]:
    directives = db.scalars(
        select(AirworthinessDirective)
        .where(AirworthinessDirective.extraction_status.in_(["not_started", "needs_review"]))
        .options(selectinload(AirworthinessDirective.discovery_record), selectinload(AirworthinessDirective.extractions))
        .limit(limit)
    ).all()
    stats = {"seen": 0, "extracted": 0, "review_queued": 0, "approved": 0}
    for directive in directives:
        stats["seen"] += 1
        extraction = extract_directive(db, directive, llm_provider=llm_provider)
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


def extract_directive(
    db: Session,
    directive: AirworthinessDirective,
    llm_provider: ADExtractionProvider | None = None,
) -> ADExtraction:
    if llm_provider is None:
        llm_provider = configured_llm_provider()
    if llm_provider is not None:
        provider_extraction = extract_with_llm_provider(db, directive, llm_provider)
        if provider_extraction is not None:
            return provider_extraction

    return extract_with_deterministic_provider(db, directive, fallback_reason=None)


def extract_with_deterministic_provider(
    db: Session,
    directive: AirworthinessDirective,
    fallback_reason: str | None,
) -> ADExtraction:
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
        if fallback_reason and existing.raw_response:
            existing.raw_response = {**existing.raw_response, "latestFallbackReason": fallback_reason}
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
        raw_response={
            "mode": "deterministic",
            "schemaVersion": SCHEMA_VERSION,
            "fallbackReason": fallback_reason,
        },
    )
    db.add(extraction)
    db.flush()
    ensure_review_for_extraction(db, directive, extraction)
    return extraction


def extract_with_llm_provider(
    db: Session,
    directive: AirworthinessDirective,
    provider: ADExtractionProvider,
) -> ADExtraction | None:
    existing = db.scalar(
        select(ADExtraction).where(
            ADExtraction.directive_id == directive.id,
            ADExtraction.input_content_hash == directive.source_content_hash,
            ADExtraction.provider_name == provider.provider_name,
            ADExtraction.provider_version == provider.provider_version,
            ADExtraction.schema_version == SCHEMA_VERSION,
        )
    )
    if existing:
        ensure_review_for_extraction(db, directive, existing)
        return existing

    deterministic_output, _, _ = build_extraction_output(directive)
    try:
        provider_payload = provider.extract(directive)
        output, confidence, citations, raw_provider = normalize_provider_payload(provider_payload)
        validate_extraction_output(output)
    except Exception as exc:
        return extract_with_deterministic_provider(db, directive, fallback_reason=f"{type(exc).__name__}: {exc}")

    review_reasons = review_reasons_for_provider_output(output, confidence, raw_provider, deterministic_output)
    status = "needs_review" if review_reasons else "approved"
    extraction = ADExtraction(
        directive_id=directive.id,
        provider_name=provider.provider_name,
        provider_version=provider.provider_version,
        schema_version=SCHEMA_VERSION,
        input_content_hash=directive.source_content_hash,
        status=status,
        confidence=confidence,
        output=output,
        citations=citations,
        raw_response={
            **raw_provider,
            "mode": "llm",
            "schemaVersion": SCHEMA_VERSION,
            "reviewReasons": review_reasons,
        },
    )
    db.add(extraction)
    db.flush()
    ensure_review_for_extraction(db, directive, extraction)
    return extraction


class OpenAIResponsesADExtractionProvider:
    provider_name = OPENAI_PROVIDER_NAME

    def __init__(self, api_key: str, base_url: str, model: str, timeout_seconds: float) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout_seconds = timeout_seconds
        self.prompt_hash = prompt_hash()
        self.provider_version = f"{model}:{OPENAI_PROMPT_VERSION}:{self.prompt_hash}"

    def extract(self, directive: AirworthinessDirective) -> dict[str, Any]:
        request_body = {
            "model": self.model,
            "input": [
                {
                    "role": "system",
                    "content": [{"type": "input_text", "text": AD_EXTRACTION_SYSTEM_PROMPT}],
                },
                {
                    "role": "user",
                    "content": [{"type": "input_text", "text": source_text_for_directive(directive)}],
                },
            ],
            "text": {
                "format": {
                    "type": "json_schema",
                    "name": "paprnav_ad_extraction",
                    "schema": AD_EXTRACTION_JSON_SCHEMA,
                    "strict": True,
                }
            },
        }
        response = httpx.post(
            f"{self.base_url}/responses",
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
            json=request_body,
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()
        response_payload = response.json()
        parsed_text = response_payload.get("output_text") or response_output_text(response_payload)
        provider_output = json.loads(parsed_text)
        return {
            "output": provider_output,
            "raw_response": {
                "providerResponseId": response_payload.get("id"),
                "providerModel": response_payload.get("model"),
                "usage": response_payload.get("usage"),
                "promptHash": self.prompt_hash,
                "promptVersion": OPENAI_PROMPT_VERSION,
                "request": {
                    "model": self.model,
                    "textFormat": "json_schema",
                    "strict": True,
                },
            },
        }


def configured_llm_provider() -> ADExtractionProvider | None:
    settings = get_settings()
    if settings.ad_extraction_provider != "openai" or not settings.openai_api_key:
        return None
    return OpenAIResponsesADExtractionProvider(
        api_key=settings.openai_api_key,
        base_url=settings.openai_base_url,
        model=settings.openai_ad_extraction_model,
        timeout_seconds=settings.ad_extraction_timeout_seconds,
    )


def normalize_provider_payload(payload: dict[str, Any]) -> tuple[dict[str, Any], float, list[dict[str, str]], dict[str, Any]]:
    raw_provider = dict(payload.get("raw_response") or {})
    provider_output = dict(payload.get("output") or payload)
    confidence = provider_output.pop("confidence", None)
    if not isinstance(confidence, (int, float)):
        raise ValueError("AD provider output confidence must be numeric")
    citations = provider_output.pop("citations", [])
    if not isinstance(citations, list):
        raise ValueError("AD provider output citations must be a list")
    uncertainty_reasons = provider_output.pop("uncertaintyReasons", [])
    if not isinstance(uncertainty_reasons, list):
        raise ValueError("AD provider output uncertaintyReasons must be a list")
    raw_provider["uncertaintyReasons"] = uncertainty_reasons
    return provider_output, float(confidence), citations, raw_provider


def review_reasons_for_provider_output(
    output: dict[str, Any],
    confidence: float,
    raw_provider: dict[str, Any],
    deterministic_output: dict[str, Any],
) -> list[str]:
    reasons: list[str] = []
    if confidence < LLM_REVIEW_THRESHOLD:
        reasons.append("low_confidence")
    if not output.get("affectedProducts"):
        reasons.append("missing_affected_products")
    if not output.get("complianceActions"):
        reasons.append("missing_compliance_actions")
    if raw_provider.get("uncertaintyReasons"):
        reasons.append("provider_uncertainty")
    if normalize_scalar(output.get("adNumber")) != normalize_scalar(deterministic_output.get("adNumber")):
        reasons.append("ad_number_disagreement")
    if normalize_list(output.get("supersedesAdNumbers")) != normalize_list(deterministic_output.get("supersedesAdNumbers")):
        reasons.append("supersession_disagreement")
    if deterministic_output.get("affectedProducts") and normalize_list(output.get("affectedProducts")) != normalize_list(
        deterministic_output.get("affectedProducts")
    ):
        reasons.append("applicability_disagreement")
    return sorted(set(reasons))


def ensure_review_for_extraction(db: Session, directive: AirworthinessDirective, extraction: ADExtraction) -> None:
    if extraction.status == "approved":
        directive.extraction_status = "complete"
        directive.review_status = "approved"
        directive.approved_at = directive.approved_at or datetime.now(timezone.utc)
        populate_applicability_from_extraction(db, extraction)
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
    source_text = "\n".join(filter(None, [record.title, record.abstract, record.excerpts])) if record else directive.title
    title = record.title if record else directive.title
    title_subject = subject_from_title(title)
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
        "title": title,
        "effectiveDate": record.effective_date.isoformat() if record and record.effective_date else None,
        "publicationDate": record.publication_date.isoformat() if record and record.publication_date else None,
        "affectedProducts": [title_subject] if title_subject else [],
        "complianceActions": [],
        "complianceIntervals": [],
        "supersedesAdNumbers": superseded_numbers,
        "sourceUrls": {
            "html": record.html_url if record else None,
            "pdf": record.pdf_url if record else None,
            "publicInspectionPdf": record.public_inspection_pdf_url if record else None,
        },
    }
    if "airworthiness directive" in source_text.lower():
        output["complianceActions"].append("Review source document for required corrective actions.")

    citations = [
        {
            "field": "title",
            "source": "federal_register" if record else "directive",
            "text": title,
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
    affected_products = [
        str(item).strip()
        for item in output["affectedProducts"]
        if str(item).strip()
    ]
    if not affected_products:
        raise ValueError(
            "AD extraction field affectedProducts must contain at least one attributable product"
        )
    if not isinstance(output["sourceUrls"], dict):
        raise ValueError("AD extraction field sourceUrls must be an object")


def subject_from_title(title: str | None) -> str | None:
    if not title:
        return None
    if ";" in title:
        return title.split(";", 1)[1].strip() or None
    return None


def source_text_for_directive(directive: AirworthinessDirective) -> str:
    record = directive.discovery_record
    if record:
        fields = [
            f"Title: {record.title}",
            f"Abstract: {record.abstract}",
            f"Excerpts: {record.excerpts}",
            f"Federal Register document number: {record.federal_register_document_number}",
            f"Publication date: {record.publication_date.isoformat() if record.publication_date else None}",
            f"Effective date: {record.effective_date.isoformat() if record.effective_date else None}",
            f"HTML URL: {record.html_url}",
            f"PDF URL: {record.pdf_url}",
            f"Public inspection PDF URL: {record.public_inspection_pdf_url}",
        ]
        return "\n".join(field for field in fields if not field.endswith(": None"))
    return directive.title


def response_output_text(payload: dict[str, Any]) -> str:
    for output_item in payload.get("output", []) or []:
        for content_item in output_item.get("content", []) or []:
            if "text" in content_item:
                return str(content_item["text"])
    raise ValueError("OpenAI response did not include output text")


def prompt_hash() -> str:
    material = json.dumps(
        {
            "promptVersion": OPENAI_PROMPT_VERSION,
            "prompt": AD_EXTRACTION_SYSTEM_PROMPT,
            "schema": AD_EXTRACTION_JSON_SCHEMA,
        },
        sort_keys=True,
    )
    return hashlib.sha256(material.encode("utf-8")).hexdigest()[:16]


def normalize_scalar(value: Any) -> str:
    return " ".join(str(value or "").strip().lower().split())


def normalize_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return sorted(normalize_scalar(item) for item in value if normalize_scalar(item))
