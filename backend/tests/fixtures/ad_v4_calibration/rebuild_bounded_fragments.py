"""Render clause-narrow fragment metadata from retained Slice-1 source text.

This script is intentionally read-only. It emits a deterministic manifest to
stdout so fixture changes still have to be reviewed and applied as a patch.
Selectors are exact retained-text anchors, not page-relative guesses.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from pypdf import PdfReader

from app.services.ad_extraction import bounded_issue_pages, bounded_source_document_pages


FIXTURE_ROOT = Path(__file__).parent
REPOSITORY_ROOT = Path(__file__).parents[4]
SOURCES_PATH = FIXTURE_ROOT / "sources.manifest.json"
HASH_INPUTS = [
    "directiveId", "sourceDocumentId", "sourceContentHash", "renditionId",
    "pageTextVersionId", "pageStart", "pageEnd", "characterStart",
    "characterEnd", "paragraphLocator", "tableLocator", "rowLocator",
    "noteLocator", "regionMapHash", "exactText", "parserName", "parserVersion",
]

# packet: (key, document, page, inclusive start anchor, exclusive end anchor,
#          locator kind, locator, claim kinds)
SELECTORS = {
    "1998-17-11": [
        ("ev-identity", "official-rule", 18, "98±17±11 Textron", "Textron Lycoming (LYC)", "paragraph", "§39.13 rule heading", ["identity"]),
        ("ev-product-scope", "official-rule", 18, "Textron Lycoming (LYC)", "TABLE 1", "paragraph", "applicability provision", ["applicability"]),
        ("ev-work-orders-a", "official-rule", 18, "TABLE 1", None, "table", "Table 1, first segment", ["applicability"]),
        ("ev-work-orders-b", "official-rule", 19, "TABLE 1", None, "table", "Table 1, continuation 1", ["applicability"]),
        ("ev-work-orders-c", "official-rule", 20, "TABLE 1", None, "table", "Table 1, continuation 2", ["applicability"]),
        ("ev-work-orders-d", "official-rule", 21, "TABLE 1", None, "table", "Table 1, continuation 3", ["applicability"]),
        ("ev-work-orders-e", "official-rule", 22, "TABLE 1", "Note 1:", "table", "Table 1, final segment", ["applicability"]),
        ("ev-unknown-provenance", "official-rule", 22, "(4) If it cannot be determined", "(5) If the engine", "paragraph", "paragraph (a)(4)", ["branch", "applicability"]),
        ("ev-determination", "official-rule", 22, "Compliance: Required as indicated", "(b) Within 10 hours", "paragraph", "compliance and paragraphs (a)(1)-(5)", ["timing", "action", "branch"]),
        ("ev-inspection-alternative", "official-rule", 22, "(b) Within 10 hours", "(3) Replace any crankshaft", "paragraph", "paragraphs (b)(1)-(2)", ["timing", "action", "branch"]),
        ("ev-rework-alternative", "official-rule", 22, "(3) Replace any crankshaft", "Note 4:", "paragraph", "paragraphs (b)(3)-(4)", ["action", "branch", "terminating_action", "service_information"]),
        ("ev-amoc-a", "official-rule", 22, "(c) An alternative method", None, "paragraph", "paragraph (c), first segment", ["amoc"]),
        ("ev-amoc-b", "official-rule", 23, "provides an acceptable level", "(d) Special flight permits", "paragraph", "paragraph (c), continuation", ["amoc"]),
        ("ev-effective", "official-rule", 23, "(e) This amendment becomes effective", "Issued in Burlington", "paragraph", "paragraph (e)", ["effective_date"]),
    ],
    "2002-13-04": [
        ("ev-identity", "official-rule", 2, "2002–13–04 Teledyne", "Applicability", "paragraph", "§39.13 rule heading", ["identity"]),
        ("ev-applicability-conflict", "official-rule", 2, "Applicability", "Note 1:", "paragraph", "applicability provision", ["applicability"]),
        ("ev-compliance-time", "official-rule", 2, "Compliance", "Replacement of Magneto", "paragraph", "compliance provision", ["timing"]),
        ("ev-action-range", "official-rule", 2, "Replacement of Magneto", "Inspections", "paragraph", "paragraph (a)", ["action", "applicability", "branch"]),
        ("ev-pin-condition", "official-rule", 2, "Inspections", "(1) For C–125", "paragraph", "paragraph (b) predicate", ["applicability", "action", "branch"]),
        ("ev-family-a", "official-rule", 2, "(1) For C–125", "(2) For LTSIO", "paragraph", "paragraph (b)(1)", ["applicability", "action", "branch"]),
        ("ev-family-b", "official-rule", 2, "(2) For LTSIO", "(c) After the effective date", "paragraph", "paragraph (b)(2)", ["applicability", "action", "branch"]),
        ("ev-installation-prohibition", "official-rule", 2, "(c) After the effective date", "Note 3:", "paragraph", "paragraph (c)", ["action", "timing", "branch"]),
        ("ev-amoc", "official-rule", 3, "Alternative Methods of Compliance", "Special Flight Permits", "paragraph", "paragraph (d)", ["amoc"]),
        ("ev-effective", "official-rule", 3, "Effective Date", "Issued in Burlington", "paragraph", "paragraph (f)", ["effective_date"]),
    ],
    "2008-26-10": [
        ("ev-identity", "official-rule", 2, "2008–26–10 Cessna", "Effective Date", "paragraph", "§39.13 rule heading", ["identity"]),
        ("ev-effective", "official-rule", 2, "Effective Date", "Affected ADs", "paragraph", "paragraph (a)", ["effective_date"]),
        ("ev-related-ads", "official-rule", 2, "Affected ADs", "VerDate", "paragraph", "paragraph (b)", ["supersession_status"]),
        ("ev-applicability", "official-rule", 3, "Applicability", "Note 1:", "paragraph", "paragraph (c)", ["applicability", "branch"]),
        ("ev-models-a", "official-rule", 3, "TABLE 1", "VerDate", "table", "Table 1, first segment", ["applicability"]),
        ("ev-models-b", "official-rule", 4, "TABLE 1", "Unsafe Condition", "table", "Table 1, final segment", ["applicability"]),
        ("ev-non-ifr", "official-rule", 4, "(1) For all affected airplanes", "(2) For all affected airplanes", "table", "actions table paragraph (e)(1)", ["action", "timing", "branch", "service_information"]),
        ("ev-ifr-initial", "official-rule", 4, "(2) For all affected airplanes", "(3) For all affected airplanes", "table", "actions table paragraph (e)(2)", ["applicability", "action", "timing", "branch", "service_information"]),
        ("ev-ifr-followup", "official-rule", 4, "(3) For all affected airplanes", "(4) For all affected airplanes", "table", "actions table paragraph (e)(3)", ["action", "timing", "branch", "service_information"]),
        ("ev-obstruction", "official-rule", 4, "(4) For all affected airplanes", "VerDate", "table", "actions table paragraph (e)(4)", ["action", "timing", "branch", "service_information"]),
        ("ev-installation", "official-rule", 5, "(5) For all affected airplanes", "(f) Report to the FAA", "table", "actions table paragraph (e)(5)", ["action", "timing", "branch"]),
        ("ev-report", "official-rule", 5, "(f) Report to the FAA", "(3) The Office of Management", "paragraph", "paragraphs (f)(1)-(2)", ["action", "timing", "branch"]),
        ("ev-amoc", "official-rule", 6, "Alternative Methods of Compliance", "Material Incorporated by Reference", "paragraph", "paragraphs (g)-(h)", ["amoc"]),
        ("ev-ibr", "official-rule", 6, "Material Incorporated by Reference", "(1) The Director", "paragraph", "paragraph (i)", ["service_information"]),
        ("ev-correction-a", "official-correction", 1, "14 CFR Part 39", "ADDRESSES:", "paragraph", "correction identity, summary, and dates", ["correction", "effective_date"]),
        ("ev-correction-b", "official-correction", 2, "As published, the Information", "Issued in Kansas City", "paragraph", "correction diagnosis and instructions", ["correction", "applicability", "action"]),
    ],
    "2011-10-09": [
        ("ev-identity", "official-rule", 4, "2011–10–09 Cessna", "Effective Date", "paragraph", "§39.13 rule heading", ["identity"]),
        ("ev-effective", "official-rule", 4, "Effective Date", "Affected ADs", "paragraph", "paragraph (a)", ["effective_date"]),
        ("ev-supersession", "official-rule", 4, "Affected ADs", "Applicability", "paragraph", "paragraph (b)", ["supersession_status"]),
        ("ev-models-a", "official-rule", 4, "Applicability", "VerDate", "table", "paragraph (c), model groups (1)-(3)", ["applicability"]),
        ("ev-models-b", "official-rule", 5, "(4) 172", "Subject", "table", "paragraph (c), model groups (4)-(18)", ["applicability"]),
        ("ev-cycle", "official-rule", 5, "Compliance", "(1) Visually inspect", "paragraph", "paragraphs (f)-(g), shared cycle", ["timing", "branch"]),
        ("ev-g1", "official-rule", 5, "(1) Visually inspect", "(2) Remove the seat", "paragraph", "paragraph (g)(1)", ["action", "branch"]),
        ("ev-g2", "official-rule", 5, "(2) Remove the seat", "(3) Inspect the diameter", "paragraph", "paragraph (g)(2)", ["action", "branch"]),
        ("ev-g3-a", "official-rule", 5, "(3) Inspect the diameter", "VerDate", "paragraph", "paragraph (g)(3), first segment", ["action", "branch", "terminating_action"]),
        ("ev-g3-b", "official-rule", 6, "(ii) Rail replacement", "(4) Visually inspect", "paragraph", "paragraph (g)(3)(ii)", ["terminating_action"]),
        ("ev-g4", "official-rule", 6, "(4) Visually inspect", "(5) Inspect the thickness", "paragraph", "paragraph (g)(4)", ["action", "branch"]),
        ("ev-g5", "official-rule", 6, "(5) Inspect the thickness", "VerDate", "paragraph", "paragraph (g)(5)", ["action", "branch", "terminating_action"]),
        ("ev-g6", "official-rule", 7, "(6) Due to wear", "(7) Inspect the springs", "paragraph", "paragraph (g)(6)", ["action", "branch", "terminating_action"]),
        ("ev-g7", "official-rule", 7, "(7) Inspect the springs", "(8) Visually inspect", "paragraph", "paragraph (g)(7)", ["action", "branch"]),
        ("ev-g8", "official-rule", 7, "(8) Visually inspect", "VerDate", "paragraph", "paragraph (g)(8)", ["action", "branch", "terminating_action"]),
        ("ev-g9", "official-rule", 8, "(9) Reinstall the seat", "(10) Lift up", "paragraph", "paragraph (g)(9)", ["action", "branch"]),
        ("ev-g10", "official-rule", 8, "(10) Lift up", "Paperwork Reduction", "paragraph", "paragraph (g)(10)", ["action", "branch", "terminating_action"]),
        ("ev-amoc", "official-rule", 8, "Alternative Methods of Compliance", "Related Information", "paragraph", "paragraph (i)", ["amoc"]),
    ],
    "2024-14-03": [
        ("ev-identity", "official-rule", 2, "2024–14–03 Various", "(a) Effective Date", "paragraph", "§39.13 rule heading", ["identity"]),
        ("ev-effective", "official-rule", 2, "(a) Effective Date", "(b) Affected ADs", "paragraph", "paragraph (a)", ["effective_date"]),
        ("ev-applicability", "official-rule", 3, "(c) Applicability", "BILLING CODE", "paragraph", "paragraph (c)", ["applicability"]),
        ("ev-models-a", "official-rule", 3, "Table 1 to Paragraph", None, "table", "Table 1, first segment", ["applicability"]),
        ("ev-models-b", "official-rule", 4, "Type certificate holder", None, "table", "Table 1, final segment", ["applicability"]),
        ("ev-software-update", "official-rule", 5, "(g) Required Action", "Note 1 to paragraph", "paragraph", "paragraph (g)", ["action", "timing", "branch"]),
        ("ev-update-method", "official-rule", 5, "Note 1 to paragraph", "(h) Installation Prohibition", "note", "note 1 to paragraph (g)", ["service_information"]),
        ("ev-installation-prohibition", "official-rule", 5, "(h) Installation Prohibition", "(i) Alternative Methods", "paragraph", "paragraph (h)", ["action", "timing", "branch"]),
        ("ev-amoc", "official-rule", 5, "(i) Alternative Methods", "(j) Additional Information", "paragraph", "paragraph (i)", ["amoc"]),
    ],
}


def _bounded_pages(packet: dict, source_root: Path) -> dict[tuple[str, int], str]:
    extracted: list[dict[str, object]] = []
    for document in packet["documents"]:
        pages = []
        for page_number, page in enumerate(PdfReader(source_root / document["relativePath"]).pages, 1):
            text = (page.extract_text() or "").strip()
            if text:
                pages.append({"sourceDocumentId": document["logicalKey"], "contentHash": document["sha256"], "pageNumber": page_number, "text": text})
        if int(document["pageCount"]) > 50:
            pages = bounded_issue_pages(pages, ad_number=packet["adNumber"], title="")
        extracted.extend(pages)
    bounded = bounded_source_document_pages(extracted, ad_number=packet["adNumber"], title="")
    return {(str(page["sourceDocumentId"]), int(page["pageNumber"])): str(page["text"]) for page in bounded}


def main() -> None:
    sources = json.loads(SOURCES_PATH.read_text())
    source_root = REPOSITORY_ROOT / sources["defaultSourceRoot"]
    packets = []
    for packet in sources["packets"]:
        pages = _bounded_pages(packet, source_root)
        fragments = []
        for key, source_key, page_number, start_anchor, end_anchor, locator_kind, locator, claim_kinds in SELECTORS[packet["packet"]]:
            page = pages[(source_key, page_number)]
            start = page.index(start_anchor)
            end = page.index(end_anchor, start + len(start_anchor)) if end_anchor else len(page)
            exact = page[start:end]
            fragments.append({
                "evidenceKey": key,
                "sourceKey": source_key,
                "pageNumber": str(page_number),
                "characterStart": str(start),
                "characterEnd": str(end),
                "pageTextHash": hashlib.sha256(page.encode()).hexdigest(),
                "exactTextHash": hashlib.sha256(exact.encode()).hexdigest(),
                "selection": {"startAnchor": start_anchor, "endAnchor": end_anchor},
                "claimKinds": claim_kinds,
                "locators": {locator_kind: locator},
                "fragmentHashInputs": HASH_INPUTS,
            })
        packets.append({"packet": packet["packet"], "fragments": fragments})
    result = {
        "manifestVersion": "2",
        "textNormalization": "slice-1-pypdf-strip-v1",
        "parser": {"name": "pypdf-native-text", "version": __import__("pypdf").__version__},
        "fragmentHashAlgorithm": "paprnav-hash-parts-sha256-v1",
        "packets": packets,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
