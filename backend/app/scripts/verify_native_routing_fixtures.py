from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
from types import SimpleNamespace

from app.services.ingestion import entry_drafts_from_page
from app.services.page_images import render_pdf_page_png, rendered_visual_metrics
from app.services.page_planning import native_text_routing_assessment
from app.services.pdf_inspection import (
    enrich_classification_from_render,
    inspect_pdf_bytes,
)
from app.services.selective_ocr import native_page_result


FIXTURE_DIR = Path(__file__).resolve().parents[2] / "tests" / "fixtures" / "native_text"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--activation", choices=("pre", "post"), required=True)
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args()
    manifest = json.loads((FIXTURE_DIR / "manifest.json").read_text())
    results = []

    if args.output_dir:
        args.output_dir.mkdir(parents=True, exist_ok=True)

    for name, expected in manifest["fixtures"].items():
        failures = []
        path = FIXTURE_DIR / expected["filename"]
        data = path.read_bytes()
        if sha256(data).hexdigest() != expected["sha256"]:
            failures.append("fixture_hash_mismatch")
        inspected = inspect_pdf_bytes(data).metadata["pages"][0]
        rendered = render_pdf_page_png(data, 1, dpi=300)
        if rendered is None:
            failures.append("render_failed")
        else:
            inspected["classification"] = enrich_classification_from_render(
                inspected["classification"],
                {"visualMetrics": rendered_visual_metrics(rendered)},
                declared_rotation=inspected["declaredRotationDegrees"],
            )
            if args.output_dir:
                (args.output_dir / f"{name}.png").write_bytes(rendered)

        assessment = native_text_routing_assessment(
            inspected["nativeText"],
            inspected["classification"],
            activated=args.activation == "post",
        )
        actual_route = (
            "native_text"
            if assessment["wouldBypassTextract"]
            else "aws_textract"
        )
        expected_route = (
            "aws_textract"
            if args.activation == "pre"
            else expected["expectedRoute"]
        )
        if actual_route != expected_route:
            failures.append(
                f"route_mismatch:{actual_route}!={expected_route}"
            )

        extracted_text = inspected["nativeText"]["textPreview"]
        missing_text = [
            text for text in expected["expectedText"] if text not in extracted_text
        ]
        if missing_text:
            failures.append(f"missing_native_text:{missing_text}")

        structured = []
        if name != "mixed_native_image":
            from pypdf import PdfReader

            page_result = native_page_result(PdfReader(path).pages[0], 1)
            page = SimpleNamespace(
                source_page_number=1,
                current_page_order=1,
                ocr_spans=[
                    SimpleNamespace(
                        id=span.provider_block_id,
                        provider_block_id=span.provider_block_id,
                        span_type=span.span_type,
                        text=span.text,
                        confidence=span.confidence,
                        bbox_left=span.bbox_left,
                        bbox_top=span.bbox_top,
                        bbox_width=span.bbox_width,
                        bbox_height=span.bbox_height,
                        bbox_units=span.bbox_units,
                        reading_order=span.reading_order,
                        relationships=span.relationships,
                        corrections=[],
                    )
                    for span in page_result.spans
                ],
            )
            drafts = entry_drafts_from_page(page)
            structured = [
                {
                    "entryDate": draft.entry_date.isoformat()
                    if draft.entry_date
                    else None,
                    "tachTime": draft.tach_time,
                    "hobbsTime": draft.hobbs_time,
                    "totalTime": draft.total_time,
                }
                for draft in drafts
            ]
            if len(structured) != expected["expectedEntryCount"]:
                failures.append("entry_count_mismatch")
            for expected_entry in expected["expectedEntries"]:
                if not any(
                    all(candidate.get(key) == value for key, value in expected_entry.items())
                    for candidate in structured
                ):
                    failures.append(
                        f"structured_entry_missing:{expected_entry}"
                    )

        results.append(
            {
                "fixture": name,
                "passed": not failures,
                "failures": failures,
                "expectedRoute": expected_route,
                "actualRoute": actual_route,
                "assessment": assessment,
                "classification": inspected["classification"],
                "nativeText": inspected["nativeText"],
                "structuredEntries": structured,
            }
        )

    passed = sum(result["passed"] for result in results)
    output = {
        "activation": args.activation,
        "result": f"{passed} passed out of {len(results)}",
        "nativeRouted": sum(
            result["actualRoute"] == "native_text" for result in results
        ),
        "textractRouted": sum(
            result["actualRoute"] == "aws_textract" for result in results
        ),
        "fixtures": results,
    }
    print(json.dumps(output, indent=2))
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
