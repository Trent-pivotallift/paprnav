from __future__ import annotations

from dataclasses import replace
from hashlib import sha256
from io import BytesIO
from typing import Any

from app.core.config import Settings
from app.models.core import IngestionPage, Upload
from app.services.ocr_provider import (
    OCRPageResult,
    OCRProvider,
    OCRProviderResult,
    OCRSpanResult,
)
from app.services.page_planning import native_text_routing_assessment
from app.services.storage import (
    derived_storage_key,
    read_stored_file_bytes,
    store_bytes,
)


ROUTER_NAME = "provider_neutral_selective_router"
ROUTER_VERSION = "native-text-routing-v1"


def process_upload_with_selective_routing(
    *,
    settings: Settings,
    upload: Upload,
    pages: list[IngestionPage],
    provider: OCRProvider,
) -> OCRProviderResult:
    if upload.content_type != "application/pdf":
        return provider.process_upload(
            original_filename=upload.original_filename,
            content_type=upload.content_type,
            storage_backend=upload.storage_backend,
            storage_key=upload.storage_key,
        )

    native_pages = [
        page
        for page in pages
        if native_text_routing_assessment(
            page.native_text_evaluation,
            page.page_classification,
        )["wouldBypassTextract"]
    ]
    if not native_pages:
        return provider.process_upload(
            original_filename=upload.original_filename,
            content_type=upload.content_type,
            storage_backend=upload.storage_backend,
            storage_key=upload.storage_key,
        )

    document_bytes = read_stored_file_bytes(
        settings=settings,
        storage_backend=upload.storage_backend,
        storage_key=upload.storage_key,
    )
    from pypdf import PdfReader

    reader = PdfReader(BytesIO(document_bytes))
    native_numbers = {page.source_page_number for page in native_pages}
    textract_numbers = [
        page.source_page_number
        for page in pages
        if page.source_page_number not in native_numbers
    ]
    results = [
        native_page_result(reader.pages[page_number - 1], page_number)
        for page_number in sorted(native_numbers)
    ]

    delegate_metadata: dict[str, Any] = {}
    billable_page_count = 0
    if textract_numbers:
        subset_bytes = materialize_pdf_pages(document_bytes, textract_numbers)
        artifact_settings = replace(settings, storage_backend=upload.storage_backend)
        subset_key = derived_storage_key(
            settings.s3_upload_prefix or "uploads",
            upload.aircraft_id,
            upload.id,
            "ocr-routing/textract-pages.pdf",
        )
        stored = store_bytes(
            subset_bytes,
            settings=artifact_settings,
            storage_key=subset_key,
            content_type="application/pdf",
            cost_allocation_tags={
                **(upload.cost_allocation_tags or {}),
                "PaprnavArtifact": "textract-page-subset",
                "SourceUploadId": upload.id,
            },
        )
        delegated = provider.process_upload(
            original_filename="textract-pages.pdf",
            content_type="application/pdf",
            storage_backend=stored.storage_backend,
            storage_key=stored.storage_key,
        )
        for delegated_page in delegated.pages:
            source_index = delegated_page.source_page_number - 1
            if source_index < 0 or source_index >= len(textract_numbers):
                raise ValueError("Textract subset returned an unexpected page number")
            results.append(
                replace(
                    delegated_page,
                    source_page_number=textract_numbers[source_index],
                    source_provider_name=delegated.provider_name,
                    source_provider_version=delegated.provider_version,
                )
            )
        delegate_metadata = delegated.metadata
        billable_page_count = (
            delegated.billable_page_count
            if delegated.billable_page_count is not None
            else len(delegated.pages)
        )
    else:
        delegate_metadata = {
            "provider_channel": "local",
            "provider_mode": "native_text_only",
            "pricing_unit": "page",
            "pricing_rate_usd": 0,
            "estimated_cost_usd": 0,
        }

    return OCRProviderResult(
        provider_name=ROUTER_NAME,
        provider_version=ROUTER_VERSION,
        configuration_hash=sha256(
            f"{ROUTER_VERSION}:{provider.configuration_hash}".encode()
        ).hexdigest(),
        pages=sorted(results, key=lambda page: page.source_page_number),
        billable_page_count=billable_page_count,
        metadata={
            **delegate_metadata,
            "routing_mode": "selective_native_text",
            "native_bypass_page_count": len(native_numbers),
            "textract_page_count": len(textract_numbers),
            "native_source_pages": sorted(native_numbers),
            "textract_source_pages": textract_numbers,
        },
    )


def native_page_result(page: Any, source_page_number: int) -> OCRPageResult:
    spans: list[OCRSpanResult] = []
    page_width = max(float(page.mediabox.width), 1.0)
    page_height = max(float(page.mediabox.height), 1.0)

    def visitor(text: str, _cm: Any, tm: Any, _font: Any, font_size: Any) -> None:
        normalized = text.strip()
        if not normalized:
            return
        size = max(float(font_size or 10), 4.0)
        left = min(max(float(tm[4]) / page_width, 0.0), 1.0)
        top = min(max(1.0 - (float(tm[5]) + size) / page_height, 0.0), 1.0)
        width = min(max(len(normalized) * size * 0.5 / page_width, 0.001), 1.0 - left)
        height = min(max(size * 1.2 / page_height, 0.001), 1.0 - top)
        spans.append(
            OCRSpanResult(
                provider_block_id=f"native-p{source_page_number}-{len(spans) + 1}",
                span_type="LINE",
                text=normalized,
                confidence=100.0,
                bbox_left=left,
                bbox_top=top,
                bbox_width=width,
                bbox_height=height,
                bbox_units="ratio",
                reading_order=len(spans) + 1,
                relationships=[{"type": "source", "provider": "pdf_native_text"}],
            )
        )

    page.extract_text(visitor_text=visitor)
    return OCRPageResult(
        source_page_number=source_page_number,
        page_label=f"Native PDF page {source_page_number}",
        width_px=0,
        height_px=0,
        rotation_degrees=float(page.rotation or 0),
        extraction_confidence=100.0,
        spans=spans,
        source_provider_name="pdf_native_text",
        source_provider_version="pypdf-native-v1",
    )


def materialize_pdf_pages(document_bytes: bytes, page_numbers: list[int]) -> bytes:
    from pypdf import PdfReader, PdfWriter

    reader = PdfReader(BytesIO(document_bytes))
    writer = PdfWriter()
    for page_number in page_numbers:
        writer.add_page(reader.pages[page_number - 1])
    output = BytesIO()
    writer.write(output)
    return output.getvalue()
