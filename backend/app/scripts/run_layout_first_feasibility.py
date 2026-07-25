from __future__ import annotations

import argparse
from dataclasses import asdict
import json
from pathlib import Path

from app.models.core import IngestionPage, OCRTextSpan
from app.services.ingestion import entry_drafts_from_page
from app.services.layout_first_ocr import LayoutFirstVLMOCRProvider


DEFAULT_INPUT = Path(".data/ocr-feasibility/input/N3671L_page2.pdf")
DEFAULT_OUTPUT = Path(
    ".data/ocr-feasibility/output/N3671L_page2_layout_first_summary.json"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the local layout-first OCR feasibility provider."
    )
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    input_path = args.input.resolve()
    if not input_path.is_file():
        raise FileNotFoundError(input_path)

    provider = LayoutFirstVLMOCRProvider(storage_root=str(input_path.parent))
    result = provider.process_upload(
        original_filename=input_path.name,
        content_type=(
            "application/pdf"
            if input_path.suffix.lower() == ".pdf"
            else "image/png"
        ),
        storage_backend="local",
        storage_key=input_path.name,
    )
    payload = asdict(result)
    payload["candidate_entries"] = [
        candidate
        for page in result.pages
        for candidate in candidate_previews(page)
    ]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(payload, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "output": str(args.output.resolve()),
                "provider": result.provider_name,
                "providerVersion": result.provider_version,
                "pages": len(result.pages),
                "regions": sum(len(page.spans) for page in result.pages),
                "billablePages": result.billable_page_count,
                "latencyMs": result.metadata.get("processing_latency_ms"),
            },
            indent=2,
        )
    )


def candidate_previews(page_result) -> list[dict]:
    page = IngestionPage(
        id=f"feasibility-page-{page_result.source_page_number}",
        ingestion_job_id="feasibility-job",
        upload_id="feasibility-upload",
        source_page_number=page_result.source_page_number,
        current_page_order=page_result.source_page_number,
        width_px=page_result.width_px,
        height_px=page_result.height_px,
    )
    page.ocr_spans = [
        OCRTextSpan(
            id=f"feasibility-span-{page_result.source_page_number}-{index}",
            ocr_run_id="feasibility-run",
            ingestion_page_id=page.id,
            provider_block_id=span.provider_block_id,
            span_type=span.span_type,
            text=span.text,
            confidence=span.confidence,
            confidence_scale="0_100",
            bbox_left=span.bbox_left,
            bbox_top=span.bbox_top,
            bbox_width=span.bbox_width,
            bbox_height=span.bbox_height,
            bbox_units=span.bbox_units,
            polygon=span.polygon,
            reading_order=span.reading_order,
            relationships=span.relationships,
        )
        for index, span in enumerate(page_result.spans, start=1)
    ]
    return [
        {
            "entryDate": draft.entry_date.isoformat() if draft.entry_date else None,
            "dateWasExtracted": draft.date_was_extracted,
            "description": draft.description,
            "performerName": draft.performer_name,
            "performerCredential": draft.performer_credential,
            "tachTime": draft.tach_time,
            "hobbsTime": draft.hobbs_time,
            "totalTime": draft.total_time,
            "requiresReview": draft.requires_review,
            "evidenceRegionIds": [
                span.provider_block_id for span in draft.line_spans
            ],
        }
        for draft in entry_drafts_from_page(page)
    ]


if __name__ == "__main__":
    main()
