# Native Text Reliability Calibration

Date: 2026-07-26

## Result

Frozen 11-page OCR-refinement partition:

**11 passed out of 11**

| Result | Pages |
| --- | ---: |
| Reliably native | 0 |
| Would bypass Textract | 0 |
| Remain Textract-routed | 11 |

All 11 pages are image scans with no meaningful embedded text. Each page was
correctly rejected by `native-text-reliability-v2` and remains assigned to
Textract.

## Strengthened Reliability Gate

A native page must satisfy all of the following:

- at least 50 meaningful characters and 8 words;
- valid glyph ratio at least 0.995;
- positioned text sample ratio at least 0.98;
- plausible font geometry ratio at least 0.98;
- duplicate-line ratio no greater than 0.05;
- agreement between normal and layout extraction modes at least 0.98;
- estimated displayed-image coverage no greater than 0.25;
- routing classification exactly `native_text`;
- no handwritten, side-by-side, faint, degraded, uncertain-orientation,
  uncertain-layout, or uncertain-text-mode attribute.

The evaluation also records the extracted-text SHA-256, image placement count,
estimated image coverage, rejection reasons, and gate decisions.

## Initial Activation Decision

Selective native-text routing was not activated from the original 11 pages.

The 11-page partition contains zero native-positive examples, so it cannot
demonstrate either visible completeness or structured equivalence for a page
that would bypass Textract. Zero failures among zero eligible pages is not
evidence that bypass is safe.

The activation state is explicitly:

`blocked_no_positive_refinement_sample`

This replaces an open-ended shadow designation with a concrete unmet gate.
This initial limitation was resolved with the separately frozen controlled
fixture supplement documented in
`NATIVE_TEXT_ROUTING_ACTIVATION_2026-07-26.md`. Selective routing is now active
under `active_controlled_fixture_gate_v1`; the original 11 pages remain
Textract-routed.

## Evidence Needed to Activate

Before activation, add a small approved calibration supplement containing
known-native PDFs, without opening the 11-page ingestion/AD holdout. It should
include:

1. a text-only native maintenance page;
2. a native page containing a table or multi-column layout;
3. a mixed native-plus-image page expected to remain Textract-routed.

For every native-positive page:

- visually compare the extracted text with the canonical rendering;
- confirm no visible text, numbers, symbols, stamps, or annotations are lost;
- confirm parser candidates and validation outcomes match the Textract
  comparison;
- require all structured fields and evidence coordinates to agree;
- require zero critical omissions.

Only then should `wouldBypassTextract` be enabled for pages satisfying the
complete reliability gate.

## Current Routing

The following refinement pages remain Textract-routed:

- aircraft pages 2, 3, 4, and 5;
- engine pages 3, 4, 5, 6, 7, 8, and 9.

Scanned, handwritten, mixed, degraded, and uncertain pages remain permanently
ineligible for the native-text bypass.
