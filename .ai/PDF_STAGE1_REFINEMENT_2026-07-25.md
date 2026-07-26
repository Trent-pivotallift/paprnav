# PDF Stage 1 Refinement Result

Date: 2026-07-25

> Historical stage result. Native text was shadow-only at this stage.
> Selective routing was subsequently activated by
> `.ai/NATIVE_TEXT_ROUTING_ACTIVATION_2026-07-26.md`; early-adopter production
> proof is governed by `.ai/EARLY_ADOPTER_NATIVE_TEXT_REVIEW.md`.

## Outcome

Stage 1 is implemented with Textract retained as the active OCR adapter.
Layout-first GLM-OCR and Ollama work remain paused.

Frozen OCR-refinement verification:

**11 passed out of 11**

The verified partition contains aircraft pages 2-5 and engine pages 3-9 from
the source documents and hashes fixed in `OCR_BENCHMARK_PARTITIONS.json`.

## Implemented

- PDF inspection occurs before OCR provider invocation.
- The original uploaded PDF remains unchanged and retains its upload SHA-256.
- Every valid PDF page receives a source-content fingerprint.
- Canonical pages use `canonical-pdf-page-v1`:
  - Poppler `pdftoppm`;
  - 300 DPI;
  - RGB PNG;
  - declared PDF rotation applied;
  - no deskew or visual enhancement.
- Canonical PNG SHA-256, dimensions, renderer version, configuration, and
  basic visual metrics are persisted.
- Page classification persists:
  - routing class;
  - document role;
  - layout and difficulty attributes;
  - confidence and recognition-confirmation requirement.
- Native PDF text is evaluated under `native-text-shadow-v1`.
- Native text cannot bypass OCR in Stage 1.
- Every extraction plan explicitly selects Textract.
- Inspection and rendering metadata are available from ingestion detail APIs.
- Reprocessing reuses existing page records and canonical artifacts.

## Verification Criteria

Each of the 11 pages passed all of the following:

- source document hash matched the frozen manifest;
- structural page inspection completed;
- canonical PNG rendered successfully;
- rendered dimensions were readable;
- source page fingerprint was present;
- routing class, document role, and classification attributes were present;
- native-text result was recorded in shadow mode;
- Textract remained selected;
- native-text OCR bypass remained disabled.

All 11 canonical pages were also visually inspected. Content was complete and
legible at the canonical resolution. Engine page 4 contains visually sideways
source content without a declared PDF rotation. Paprnav preserves those pixels
and classifies that case conservatively as `wide_layout` with
`orientation_unverified`; it does not silently rotate the audit artifact.

## Automated Regression

- Focused PDF/ingestion tests: 19 passed out of 19 before final refinements.
- Final full backend suite: 88 passed out of 88.
