from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from app.services.ocr_benchmark import (
    load_ocr_benchmark_manifest,
    resolve_ocr_benchmark_selection,
)
from app.services.page_images import (
    CANONICAL_RENDER_DPI,
    CANONICAL_RENDER_PROFILE,
    pdftoppm_version,
    png_dimensions,
    rendered_visual_metrics,
    render_pdf_page_png,
)
from app.services.pdf_inspection import enrich_classification_from_render, inspect_pdf_bytes
from app.services.page_planning import (
    logical_region_specs,
    native_text_routing_assessment,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Verify the frozen OCR-refinement pages against PDF Stage 1."
    )
    parser.add_argument(
        "--input-dir",
        type=Path,
        required=True,
        help="Directory containing the source PDFs named in the benchmark manifest.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        help="Optional directory for canonical page PNGs used during visual review.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest = load_ocr_benchmark_manifest()
    partition = manifest["partitions"]["ocr_refinement"]
    results: list[dict] = []
    renderer_version = pdftoppm_version()

    if args.output_dir:
        args.output_dir.mkdir(parents=True, exist_ok=True)

    for document_name, source_pages in partition["pages"].items():
        filename = manifest["documents"][document_name]["filename"]
        source_path = args.input_dir / filename
        selection = resolve_ocr_benchmark_selection(
            source_path=source_path,
            document=document_name,
            partition="ocr_refinement",
        )
        document_bytes = source_path.read_bytes()
        inspection = inspect_pdf_bytes(document_bytes)
        inspected_by_page = {
            page["pageNumber"]: page for page in inspection.metadata["pages"]
        }

        for source_page_number in source_pages:
            failures: list[str] = []
            inspected = inspected_by_page.get(source_page_number)
            rendered = render_pdf_page_png(
                document_bytes,
                source_page_number,
                dpi=CANONICAL_RENDER_DPI,
            )
            dimensions = png_dimensions(rendered) if rendered else None
            if inspected is not None and rendered is not None:
                inspected["classification"] = enrich_classification_from_render(
                    inspected["classification"],
                    {"visualMetrics": rendered_visual_metrics(rendered)},
                    declared_rotation=inspected["declaredRotationDegrees"],
                )
            regions = (
                logical_region_specs(inspected["classification"])
                if inspected is not None
                else []
            )
            native_routing = (
                native_text_routing_assessment(
                    inspected["nativeText"],
                    inspected["classification"],
                )
                if inspected is not None
                else None
            )
            if inspected is None:
                failures.append("inspection_missing")
            if rendered is None:
                failures.append("canonical_render_missing")
            if dimensions is None:
                failures.append("canonical_dimensions_missing")
            if inspected is not None:
                if len(inspected["sourcePageFingerprint"]) != 64:
                    failures.append("source_page_fingerprint_invalid")
                if not inspected["classification"].get("routingClass"):
                    failures.append("routing_class_missing")
                if not inspected["classification"].get("documentRole"):
                    failures.append("document_role_missing")
                if not inspected["classification"].get("attributes"):
                    failures.append("classification_attributes_missing")
                if inspected["nativeText"].get("mode") != "calibration":
                    failures.append("native_text_not_in_calibration_mode")
                for required_metric in (
                    "validGlyphRatio",
                    "positionedSampleRatio",
                    "plausibleFontRatio",
                    "duplicateLineRatio",
                    "extractorAgreement",
                    "estimatedImageCoverage",
                    "textSha256",
                ):
                    if required_metric not in inspected["nativeText"]:
                        failures.append(f"native_metric_missing:{required_metric}")
                if not regions:
                    failures.append("logical_regions_missing")
                if any(
                    region["bboxLeft"] < 0
                    or region["bboxTop"] < 0
                    or region["bboxLeft"] + region["bboxWidth"] > 1
                    or region["bboxTop"] + region["bboxHeight"] > 1
                    for region in regions
                ):
                    failures.append("logical_region_out_of_bounds")
                if (
                    "side_by_side" in inspected["classification"]["attributes"]
                    and [region["regionKey"] for region in regions]
                    != ["left", "right"]
                ):
                    failures.append("spread_regions_invalid")
                plan = inspected["extractionPlan"]
                if plan.get("selectedProvider") != "aws_textract":
                    failures.append("textract_not_selected")
                if plan.get("nativeTextMayBypassOCR") is not False:
                    failures.append("native_text_bypass_enabled")

            output_path = None
            if args.output_dir and rendered is not None:
                output_path = args.output_dir / (
                    f"{document_name}-page-{source_page_number:04d}.png"
                )
                output_path.write_bytes(rendered)

            results.append(
                {
                    "document": document_name,
                    "sourcePageNumber": source_page_number,
                    "passed": not failures,
                    "failures": failures,
                    "renderProfile": CANONICAL_RENDER_PROFILE,
                    "rendererVersion": renderer_version,
                    "dimensions": list(dimensions) if dimensions else None,
                    "classification": inspected["classification"] if inspected else None,
                    "logicalRegions": regions,
                    "nativeText": inspected["nativeText"] if inspected else None,
                    "nativeTextRouting": native_routing,
                    "renderedPath": str(output_path) if output_path else None,
                }
            )

        if selection.source_pages != source_pages:
            raise RuntimeError(f"Manifest selection changed for {document_name}")

    passed = sum(1 for result in results if result["passed"])
    summary = {
        "partition": "ocr_refinement",
        "expectedPageCount": partition["pageCount"],
        "passedPageCount": passed,
        "failedPageCount": len(results) - passed,
        "result": f"{passed} passed out of {len(results)}",
        "reliablyNativePageCount": sum(
            page["nativeText"]["reliableCandidate"] is True
            for page in results
            if page["nativeText"] is not None
        ),
        "wouldBypassTextractPageCount": sum(
            page["nativeTextRouting"]["wouldBypassTextract"] is True
            for page in results
            if page["nativeTextRouting"] is not None
        ),
        "textractRoutedPageCount": sum(
            page["nativeTextRouting"]["wouldBypassTextract"] is not True
            for page in results
            if page["nativeTextRouting"] is not None
        ),
        "pages": results,
    }
    print(json.dumps(summary, indent=2))
    return 0 if passed == len(results) == partition["pageCount"] else 1


if __name__ == "__main__":
    sys.exit(main())
