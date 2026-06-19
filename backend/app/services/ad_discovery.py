import hashlib
import json
import re
from dataclasses import dataclass
from datetime import date, datetime, timezone
from typing import Any

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.core import ADDiscoveryRecord, AirworthinessDirective

FEDERAL_REGISTER_API_BASE_URL = "https://www.federalregister.gov"
FEDERAL_REGISTER_DOCUMENTS_PATH = "/api/v1/documents.json"
CLASSIFIER_NAME = "deterministic_ad_classifier"
CLASSIFIER_VERSION = "0.1.0"
AD_NUMBER_PATTERN = re.compile(r"\b(?:AD\s*)?(\d{4}-\d{2}-\d{2})\b", re.IGNORECASE)


@dataclass(frozen=True)
class FederalRegisterSearchResult:
    description: str | None
    count: int | None
    total_pages: int | None
    next_page_url: str | None
    results: list[dict[str, Any]]
    raw_response: dict[str, Any]


class FederalRegisterClient:
    def __init__(self, base_url: str = FEDERAL_REGISTER_API_BASE_URL, timeout_seconds: float = 20.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds

    def search_airworthiness_directive_candidates(self, page: int = 1, per_page: int = 20) -> FederalRegisterSearchResult:
        params: list[tuple[str, str | int]] = [
            ("conditions[agencies][]", "federal-aviation-administration"),
            ("conditions[type][]", "RULE"),
            ("conditions[term]", "Airworthiness Directives"),
            ("order", "newest"),
            ("page", page),
            ("per_page", per_page),
        ]
        with httpx.Client(base_url=self.base_url, timeout=self.timeout_seconds) as client:
            response = client.get(FEDERAL_REGISTER_DOCUMENTS_PATH, params=params)
            response.raise_for_status()
            payload = response.json()

        return FederalRegisterSearchResult(
            description=payload.get("description"),
            count=payload.get("count"),
            total_pages=payload.get("total_pages"),
            next_page_url=payload.get("next_page_url"),
            results=list(payload.get("results") or []),
            raw_response=payload,
        )


def discover_federal_register_ads(
    db: Session,
    client: FederalRegisterClient | None = None,
    page: int = 1,
    per_page: int = 20,
) -> dict[str, int]:
    client = client or FederalRegisterClient()
    search_result = client.search_airworthiness_directive_candidates(page=page, per_page=per_page)
    stats = {"seen": 0, "created": 0, "updated": 0, "candidates": 0, "rejected": 0}
    for document in search_result.results:
        stats["seen"] += 1
        record, created = upsert_discovery_record(db, document)
        stats["created" if created else "updated"] += 1
        if record.classification == "ad_candidate":
            stats["candidates"] += 1
            ensure_directive_for_record(db, record)
        else:
            stats["rejected"] += 1
    db.commit()
    return stats


def upsert_discovery_record(db: Session, document: dict[str, Any]) -> tuple[ADDiscoveryRecord, bool]:
    document_number = str(document.get("document_number") or "").strip()
    if not document_number:
        raise ValueError("Federal Register document is missing document_number")

    classification, confidence, reason = classify_document(document)
    existing = db.scalar(
        select(ADDiscoveryRecord).where(ADDiscoveryRecord.federal_register_document_number == document_number)
    )
    content_hash = hash_json(document)
    values = {
        "title": str(document.get("title") or "").strip(),
        "document_type": document.get("type"),
        "abstract": document.get("abstract"),
        "publication_date": parse_date(document.get("publication_date")),
        "effective_date": parse_date(document.get("effective_on") or document.get("effective_date")),
        "html_url": document.get("html_url"),
        "pdf_url": document.get("pdf_url"),
        "public_inspection_pdf_url": document.get("public_inspection_pdf_url"),
        "agency_names": agency_names(document),
        "excerpts": flatten_excerpts(document.get("excerpts")),
        "api_snapshot": document,
        "content_hash": content_hash,
        "classification": classification,
        "classification_confidence": confidence,
        "classification_reason": reason,
        "classifier_name": CLASSIFIER_NAME,
        "classifier_version": CLASSIFIER_VERSION,
        "classified_at": datetime.now(timezone.utc),
    }
    if existing:
        for key, value in values.items():
            setattr(existing, key, value)
        db.flush()
        return existing, False

    record = ADDiscoveryRecord(
        federal_register_document_number=document_number,
        **values,
    )
    db.add(record)
    db.flush()
    return record, True


def ensure_directive_for_record(db: Session, record: ADDiscoveryRecord) -> AirworthinessDirective:
    existing = db.scalar(select(AirworthinessDirective).where(AirworthinessDirective.discovery_record_id == record.id))
    ad_number = extract_ad_number(record.title, record.abstract, record.excerpts)
    if existing:
        existing.ad_number = ad_number or existing.ad_number
        existing.title = record.title
        existing.source_content_hash = record.content_hash
        db.flush()
        return existing

    directive = AirworthinessDirective(
        discovery_record_id=record.id,
        ad_number=ad_number,
        title=record.title,
        status="candidate",
        source_content_hash=record.content_hash,
        extraction_status="not_started",
        review_status="not_started",
    )
    db.add(directive)
    db.flush()
    return directive


def classify_document(document: dict[str, Any]) -> tuple[str, float, str]:
    title = str(document.get("title") or "")
    abstract = str(document.get("abstract") or "")
    excerpts = flatten_excerpts(document.get("excerpts"))
    searchable = " ".join([title, abstract, excerpts]).lower()
    document_type = str(document.get("type") or "").upper()

    if "airworthiness directives" in searchable or "airworthiness directive" in searchable:
        return "ad_candidate", 0.96, "Title, abstract, or excerpt explicitly mentions Airworthiness Directive."
    if document_type == "RULE" and AD_NUMBER_PATTERN.search(searchable):
        return "ad_candidate", 0.78, "FAA rule contains an AD number pattern but needs extraction review."
    if document_type == "RULE":
        return "non_ad_rule", 0.82, "FAA rule does not contain AD wording or an AD number pattern."
    return "rejected", 0.9, "Document type is not a final rule candidate."


def extract_ad_number(*values: str | None) -> str | None:
    for value in values:
        if not value:
            continue
        match = AD_NUMBER_PATTERN.search(value)
        if match:
            return match.group(1)
    return None


def agency_names(document: dict[str, Any]) -> list[str]:
    agencies = document.get("agencies") or []
    return [str(item.get("name") or item.get("slug") or "").strip() for item in agencies if isinstance(item, dict)]


def flatten_excerpts(excerpts: Any) -> str:
    if isinstance(excerpts, list):
        return "\n".join(str(item) for item in excerpts if item)
    if isinstance(excerpts, dict):
        return "\n".join(str(value) for value in excerpts.values() if value)
    if excerpts is None:
        return ""
    return str(excerpts)


def parse_date(value: Any) -> date | None:
    if not value:
        return None
    if isinstance(value, date):
        return value
    return datetime.fromisoformat(str(value)).date()


def hash_json(value: dict[str, Any]) -> str:
    normalized = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()
