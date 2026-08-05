from __future__ import annotations

import hashlib
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.models.core import ADSourceDocument, ADSourceSnapshot
from app.services.ad_costs import record_ad_cost_entry
from app.services.storage import safe_filename, store_bytes


CATALOG_PARSER_NAME = "provider_neutral_ad_source_catalog"
CATALOG_PARSER_VERSION = "0.1.0"


class GovInfoClient:
    def __init__(
        self,
        *,
        api_key: str,
        base_url: str = "https://api.govinfo.gov",
        timeout_seconds: float = 30.0,
    ) -> None:
        if not api_key.strip():
            raise ValueError("GovInfo API key is required")
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds

    def search_all(
        self,
        query: str,
        *,
        page_size: int = 100,
        historical: bool = True,
        max_pages: int | None = None,
    ) -> dict[str, Any]:
        if not 1 <= page_size <= 1000:
            raise ValueError("GovInfo page_size must be between 1 and 1000")
        results: list[dict[str, Any]] = []
        offset_mark = "*"
        pages: list[dict[str, Any]] = []
        while True:
            body = {
                "query": query,
                "pageSize": str(page_size),
                "offsetMark": offset_mark,
                "historical": historical,
                "sorts": [{"field": "publishdate", "sortOrder": "ASC"}],
            }
            with httpx.Client(
                base_url=self.base_url,
                timeout=self.timeout_seconds,
            ) as client:
                response = client.post(
                    "/search",
                    params={"api_key": self.api_key},
                    json=body,
                )
                response.raise_for_status()
                payload = response.json()
            page_results = list(payload.get("results") or [])
            pages.append(
                {
                    "offsetMark": offset_mark,
                    "returned": len(page_results),
                    "declaredCount": payload.get("count"),
                }
            )
            results.extend(page_results)
            next_mark = payload.get("offsetMark")
            if not page_results or not next_mark or next_mark == offset_mark:
                break
            offset_mark = str(next_mark)
            if max_pages is not None and len(pages) >= max_pages:
                break
        return {
            "query": query,
            "declaredCount": pages[-1]["declaredCount"] if pages else 0,
            "retrievedCount": len(results),
            "pages": pages,
            "results": results,
            "exhausted": (
                max_pages is None
                or len(pages) < max_pages
                or not pages
                or pages[-1]["returned"] == 0
            ),
        }

    def fetch(self, url: str) -> tuple[bytes, str | None]:
        with httpx.Client(timeout=self.timeout_seconds, follow_redirects=True) as client:
            response = client.get(url, params={"api_key": self.api_key})
            response.raise_for_status()
            return response.content, response.headers.get("content-type")


def retain_source_document(
    db: Session,
    *,
    data: bytes,
    source_system: str,
    source_type: str,
    source_identifier: str,
    source_url: str | None,
    filename: str,
    media_type: str | None,
    settings: Settings | None = None,
    source_snapshot: ADSourceSnapshot | None = None,
    parent_source_identifier: str | None = None,
    publication_date: date | None = None,
    metadata: dict[str, Any] | None = None,
) -> tuple[ADSourceDocument, bool]:
    settings = settings or get_settings()
    digest = hashlib.sha256(data).hexdigest()
    existing = db.scalar(
        select(ADSourceDocument).where(
            ADSourceDocument.source_system == source_system,
            ADSourceDocument.source_type == source_type,
            ADSourceDocument.source_identifier == source_identifier,
            ADSourceDocument.content_hash == digest,
        )
    )
    if existing is not None:
        return existing, False

    storage_key = (
        f"ad-sources/{safe_filename(source_system)}/{digest[:2]}/{digest}/"
        f"{safe_filename(Path(filename).name)}"
    )
    stored = store_bytes(
        data,
        settings=settings,
        storage_key=storage_key,
        content_type=media_type or "application/octet-stream",
        cost_allocation_tags={
            "paprnav:cost-scope": "shared-ad-source",
            "paprnav:source-system": source_system,
        },
    )
    document = ADSourceDocument(
        source_snapshot_id=source_snapshot.id if source_snapshot else None,
        source_system=source_system,
        source_type=source_type,
        source_identifier=source_identifier,
        parent_source_identifier=parent_source_identifier,
        source_url=source_url,
        storage_backend=stored.storage_backend,
        storage_key=stored.storage_key,
        media_type=media_type,
        content_hash=stored.sha256,
        storage_bytes=stored.file_size_bytes,
        captured_at=datetime.now(timezone.utc),
        publication_date=publication_date,
        status="retained",
        parser_name=CATALOG_PARSER_NAME,
        parser_version=CATALOG_PARSER_VERSION,
        metadata_json=metadata or {},
    )
    db.add(document)
    db.flush()
    record_ad_cost_entry(
        db,
        idempotency_key=f"ad-source-document:{source_system}:{digest}",
        scope_type="shared_source",
        cost_category="source_storage",
        usage_quantity=stored.file_size_bytes,
        usage_unit="physical_byte",
        source_snapshot_id=source_snapshot.id if source_snapshot else None,
        actual_cost_usd=0,
        allocated_cost_usd=0,
        attribution_status="platform_shared_unallocated",
        metadata={
            "sourceSystem": source_system,
            "sourceIdentifier": source_identifier,
            "billingActive": False,
        },
    )
    return document, True
