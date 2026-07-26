# PDF Stages 2-4 Refinement Result

Date: 2026-07-26

> Historical stage boundary. Native text was shadow-only during these
> regressions. The later controlled-fixture gate activated selective native
> routing; real early-adopter native pages require the review checkpoint in
> `.ai/EARLY_ADOPTER_NATIVE_TEXT_REVIEW.md`.

## Boundaries Preserved

- Textract remains the authoritative recognition provider.
- Native PDF text remains shadow-only and cannot bypass OCR.
- Original PDFs and canonical page images remain unmodified.
- The 11-page ingestion/AD holdout was not opened.
- Layout-first GLM-OCR, Ollama, and local OCR work remain paused.

## Stage 2 - Provider-Neutral Page Extraction Plans

Implemented:

- persisted logical regions relative to the canonical source page;
- deterministic left/right regions for confidently wide two-page spreads;
- full-page regions for attachments and uncertain orientation;
- physical source-page identity preservation;
- post-recognition extraction plans with provider and version;
- native-text/Textract agreement measurement when native text is reliable;
- mandatory-review reasons;
- page-stage status, attempt, failure code, and retry eligibility;
- retry-safe region and extraction-plan persistence.

Regression verification:

**11 passed out of 11 frozen refinement pages.**

- Nine pages produced left/right logical regions.
- Two pages remained full-page regions.
- No logical region exceeded canonical-page bounds.
- Textract remained selected and native-text bypass remained disabled.
- Focused PDF, planning, and ingestion regression: 25 passed out of 25.

## Stage 3 - Provider-Neutral Candidate Validation

Implemented a validation stage between parser candidates and acceptance:

- source-supported and plausible dates;
- non-negative tach, Hobbs, and total values;
- tach/Hobbs versus total-time conflict detection;
- explicit-zero enforcement;
- source-supported description and field decisions;
- performer-name and credential credibility checks;
- explicit AD reference capture without inference;
- rejected, passed-with-review, and passed outcomes;
- field-level validation results attached to evidence;
- page-level validation stage results and candidate counts.

Regression verification:

- Dedicated validation cases: **3 passed out of 3**.
- Validation plus ingestion integration gate: **19 passed out of 19**.

The frozen PDFs were not resubmitted to paid Textract during this stage.
Candidate-value accuracy on all 11 pages therefore remains a later measured
OCR/ground-truth exercise, not a result claimed by this implementation gate.

## Stage 4 - Evidence-Backed Review Metrics

Implemented:

- job-level review metrics API;
- extracted, reviewed, and verified entry counts;
- verification rate;
- median review duration;
- mean edited-field count;
- accepted-field accuracy;
- accepted, null, and unresolved field counts;
- source-supported date evidence requirement before OCR candidates can be
  marked verified;
- review-metric display in the ingestion review UI;
- canonical-page evidence remains the review surface with exact span or
  candidate-region fallback.

Regression verification:

- Review-metrics unit and ingestion endpoint tests passed.
- Production frontend build passed.
- Complete backend suite: **94 passed out of 94**.
- Alembic has one head: `20260726_0015`.

## Render Regression

All 11 Stage 2 canonical PNG hashes were identical to the approved Stage 1
canonical PNG hashes: **11 passed out of 11**.
