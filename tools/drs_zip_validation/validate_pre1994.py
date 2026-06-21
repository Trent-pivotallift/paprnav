#!/usr/bin/env python3
"""Summarize fixture-backed pre-1994 DRS historical validation.

This script is intentionally conservative. It does not scrape DRS. It reads a
committed validation-source fixture, optionally cross-checks sampled identifiers
against the local extracted ZIP identifier set, and writes an audit report.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_SOURCES = BASE_DIR / "pre1994_validation_sources.json"
DEFAULT_ZIP_SET = BASE_DIR / "data" / "zip_set.json"
DEFAULT_REPORT = BASE_DIR / "pre1994_findings.md"
DEFAULT_JSON = BASE_DIR / "pre1994_validation_report.json"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sources", type=Path, default=DEFAULT_SOURCES)
    parser.add_argument("--zip-set", type=Path, default=DEFAULT_ZIP_SET)
    parser.add_argument("--out", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON)
    args = parser.parse_args()

    sources = json.loads(args.sources.read_text())
    zip_set = load_zip_set(args.zip_set)
    report = build_report(sources, zip_set)
    args.json_out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    args.out.write_text(render_markdown(report))
    print(f"Wrote {args.out}")
    print(f"Wrote {args.json_out}")
    return 0


def load_zip_set(path: Path) -> set[str] | None:
    if not path.exists():
        return None
    return set(json.loads(path.read_text()))


def build_report(sources: dict[str, Any], zip_set: set[str] | None) -> dict[str, Any]:
    samples = sources.get("samples") or []
    status_counts = Counter(str(sample.get("status") or "ambiguous") for sample in samples)
    checked_samples = []
    for sample in samples:
        ad_number = sample.get("adNumber")
        checked = dict(sample)
        checked["bulkIdentifierPresent"] = ad_number in zip_set if zip_set is not None else None
        if zip_set is not None and ad_number not in zip_set:
            checked["status"] = "missing"
        checked_samples.append(checked)

    missing = [sample for sample in checked_samples if sample.get("status") == "missing"]
    ambiguous = [
        sample
        for sample in checked_samples
        if sample.get("status") in {"ambiguous", "snapshot_unparseable", "historical_source_unavailable"}
    ]
    confidence = "conditional"
    if missing:
        confidence = "low"
    elif not ambiguous and checked_samples:
        confidence = "high"

    return {
        "validationVersion": sources.get("validationVersion"),
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "bulkSource": sources.get("bulkSource") or {},
        "sampleCount": len(checked_samples),
        "statusCounts": dict(status_counts),
        "zipSetCrossCheckAvailable": zip_set is not None,
        "confidenceLevel": confidence,
        "coverageClaim": sources.get("coverageClaim"),
        "samples": checked_samples,
        "missingSamples": missing,
        "ambiguousSamples": ambiguous,
        "requiredProductCopy": (
            "Pre-1994 ADs are included when present in the current DRS bulk data; "
            "complete historical coverage has not been proven."
        ),
    }


def render_markdown(report: dict[str, Any]) -> str:
    bulk = report["bulkSource"]
    lines = [
        "# Pre-1994 DRS Historical Validation",
        "",
        f"Generated at: {report['generatedAt']}",
        "",
        "## Bulk Evidence",
        "",
        f"- Source ZIP: `{bulk.get('sourceFilename')}`",
        f"- Access database: `{bulk.get('accessDatabase')}`",
        f"- Normalized AD identifiers: {bulk.get('normalizedAdIdentifierCount')}",
        f"- Pre-1994 identifiers: {bulk.get('pre1994IdentifierCount')}",
        f"- Earliest pre-1994 identifier: `{bulk.get('earliestPre1994AdNumber')}`",
        f"- Latest pre-1994 identifier: `{bulk.get('latestPre1994AdNumber')}`",
        f"- Sample method: {bulk.get('sampleMethod')}",
        "",
        "## Verdict",
        "",
        f"- Confidence level: **{report['confidenceLevel']}**",
        f"- Coverage claim: {report['coverageClaim']}",
        f"- Product copy requirement: {report['requiredProductCopy']}",
        f"- Local ZIP set cross-check available: {report['zipSetCrossCheckAvailable']}",
        "",
        "## Sample Status Counts",
        "",
    ]
    for status, count in sorted(report["statusCounts"].items()):
        lines.append(f"- `{status}`: {count}")
    lines.extend(["", "## Samples", ""])
    for sample in report["samples"]:
        lines.extend(
            [
                f"### {sample.get('sampleId')}",
                "",
                f"- AD number: `{sample.get('adNumber')}`",
                f"- Status: `{sample.get('status')}`",
                f"- Bulk identifier present: `{sample.get('bulkIdentifierPresent')}`",
                f"- Target query: `{sample.get('targetQuery')}`",
                f"- DRS Web UI snapshot: `{sample.get('drsWebUiSnapshot')}`",
                f"- Historical sources: `{sample.get('historicalSources')}`",
                f"- Notes: {sample.get('notes')}",
                "",
            ]
        )
    lines.extend(
        [
            "## Required Follow-Up",
            "",
            "- Capture rendered DRS result-list snapshots for unresolved target samples.",
            "- Find or digitize independent historical FAA/index sources where available.",
            "- Keep pre-1994 coverage claims conservative until ambiguous samples are resolved.",
            "",
        ]
    )
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())

