from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from app.services.google_document_ai import GoogleDocumentAIOCRProvider
from app.services.ocr_benchmark import load_ocr_benchmark_manifest, resolve_ocr_benchmark_selection
from app.services.page_images import (
    CANONICAL_RENDER_DPI,
    CANONICAL_RENDER_PROFILE,
    png_dimensions,
    render_pdf_page_png,
)


DEFAULT_SOURCE_DIR = Path("backend/.data/ocr-feasibility/input")
DEFAULT_OUTPUT = Path(
    "backend/.data/ocr-feasibility/output/google_document_ai_11_page_evaluation.json"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run Google Document AI against only the frozen 11-page OCR "
            "refinement partition using Paprnav canonical page renders."
        )
    )
    parser.add_argument("--source-dir", type=Path, default=DEFAULT_SOURCE_DIR)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--limit", type=int)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    manifest = load_ocr_benchmark_manifest()
    provider = GoogleDocumentAIOCRProvider()
    results: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    expected_total = manifest["partitions"]["ocr_refinement"]["pageCount"]
    selected_count = 0

    for document_name in ("aircraft", "engine"):
        document_config = manifest["documents"][document_name]
        source_path = (args.source_dir / document_config["filename"]).resolve()
        selection = resolve_ocr_benchmark_selection(
            source_path=source_path,
            document=document_name,
            partition="ocr_refinement",
        )
        document_bytes = source_path.read_bytes()
        for source_page_number in selection.source_pages:
            if args.limit is not None and selected_count >= args.limit:
                break
            selected_count += 1
            record: dict[str, Any] = {
                "document": document_name,
                "sourceFilename": source_path.name,
                "sourceSha256": selection.source_sha256,
                "sourcePageNumber": source_page_number,
            }
            try:
                canonical = render_pdf_page_png(
                    document_bytes, source_page_number, dpi=CANONICAL_RENDER_DPI
                )
                if canonical is None:
                    raise RuntimeError("canonical_render_unavailable")
                dimensions = png_dimensions(canonical)
                if dimensions is None:
                    raise RuntimeError("canonical_png_dimensions_unavailable")
                result = provider.process_canonical_page(
                    png_bytes=canonical,
                    source_page_number=source_page_number,
                    labels={
                        "account": "paprnav-internal-test",
                        "aircraft": "n3671l",
                        "benchmark": "ocr-refinement-2026-07-25",
                        "document": document_name,
                    },
                )
                page = result.pages[0]
                lines = [span for span in page.spans if span.span_type == "LINE"]
                words = [span for span in page.spans if span.span_type == "WORD"]
                geometry_valid = all(
                    span.bbox_units == "ratio"
                    and 0 <= span.bbox_left <= 1
                    and 0 <= span.bbox_top <= 1
                    and 0 <= span.bbox_width <= 1
                    and 0 <= span.bbox_height <= 1
                    and span.bbox_left + span.bbox_width <= 1.000001
                    and span.bbox_top + span.bbox_height <= 1.000001
                    for span in page.spans
                )
                passed = bool(lines) and bool(words) and geometry_valid
                record.update({
                    "passed": passed,
                    "failureReasons": [] if passed else ["empty_or_invalid_output"],
                    "canonicalRenderProfile": CANONICAL_RENDER_PROFILE,
                    "canonicalDpi": CANONICAL_RENDER_DPI,
                    "canonicalSha256": sha256(canonical).hexdigest(),
                    "canonicalWidthPx": dimensions[0],
                    "canonicalHeightPx": dimensions[1],
                    "provider": result.provider_name,
                    "providerVersion": result.provider_version,
                    "configurationHash": result.configuration_hash,
                    "lineCount": len(lines),
                    "wordCount": len(words),
                    "meanLineConfidence": page.extraction_confidence,
                    "geometryValid": geometry_valid,
                    "processingSeconds": result.metadata["processing_seconds"],
                    "estimatedCostUsd": result.metadata["estimated_cost_usd"],
                    "imageQuality": result.metadata.get("image_quality"),
                    "text": "\n".join(line.text for line in lines),
                    "lines": [{
                        "text": line.text,
                        "confidence": line.confidence,
                        "bbox": [
                            line.bbox_left,
                            line.bbox_top,
                            line.bbox_width,
                            line.bbox_height,
                        ],
                    } for line in lines],
                })
                if not passed:
                    failures.append(record)
            except Exception as exc:
                record.update({
                    "passed": False,
                    "failureReasons": [type(exc).__name__, str(exc)],
                })
                failures.append(record)
            results.append(record)
        if args.limit is not None and selected_count >= args.limit:
            break

    summary = {
        "evaluation": "google-document-ai-ocr-refinement-v1",
        "mode": "evaluation_only",
        "activeRoutingChanged": False,
        "partition": "ocr_refinement",
        "expectedPageCount": expected_total,
        "attemptedPageCount": len(results),
        "passedPageCount": sum(bool(result.get("passed")) for result in results),
        "failedPageCount": len(failures),
        "estimatedCostUsd": round(
            sum(float(result.get("estimatedCostUsd") or 0) for result in results), 6
        ),
        "processingSeconds": round(
            sum(float(result.get("processingSeconds") or 0) for result in results), 6
        ),
        "pages": results,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({
        "evaluation": summary["evaluation"],
        "attemptedPageCount": summary["attemptedPageCount"],
        "passedPageCount": summary["passedPageCount"],
        "failedPageCount": summary["failedPageCount"],
        "estimatedCostUsd": summary["estimatedCostUsd"],
        "processingSeconds": summary["processingSeconds"],
    }, indent=2, sort_keys=True))
    print(f"summary={args.output}")
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
