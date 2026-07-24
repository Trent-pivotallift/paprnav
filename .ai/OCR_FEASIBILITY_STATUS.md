# OCR Feasibility Status

Last updated: 2026-07-20

## Current Slice

Goal: prove whether paprnav can receive a scanned maintenance-log page, run AWS Textract close to the application infrastructure shape, persist OCR results into the app schema, attribute billable OCR work to an account/aircraft, and expose the result for review.

Runtime choice:

- Continue with ECS/Fargate for the pilot.
- Keep OCR orchestration in the backend/worker container path.
- Do not make Lambda the primary OCR logic path.
- Mistral OCR may be used for A/B testing only until paprnav explicitly promotes it as a Textract replacement or augmentation.

Third-party OCR note:

- Target secret/env var: `PAPRNAV_MISTRAL_API_KEY`.
- Target A/B model: `mistral-ocr-4-0`.
- Mistral OCR 4 may also be available through Amazon SageMaker. Treat this as a separate deployment channel from the direct Mistral API because IAM, network path, data residency, logging, and cost attribution differ.
- For SageMaker A/B access, use `PAPRNAV_MISTRAL_OCR_CHANNEL=sagemaker`, `PAPRNAV_MISTRAL_SAGEMAKER_ENDPOINT_NAME`, and `PAPRNAV_MISTRAL_SAGEMAKER_REGION`.
- A Mistral-backed OCR run must disclose that a third-party OCR provider was used before or during upload review.
- The provider name, provider version/model, API mode, billable page count, billable account tag, billable aircraft tag, and estimated provider unit cost must be persisted in paprnav records before using it for customer-billable work.
- Mistral should not become the default OCR provider until the A/B run demonstrates better extraction quality, evidence-region support, and acceptable per-page cost.
- Direct Mistral A/B uses `https://api.mistral.ai/v1` unless a regional/private channel is explicitly configured. Current regional docs show the US endpoint as not generally available, so do not send customer documents to direct Mistral by default.

## Test Input

Private local input:

- `backend/.data/ocr-feasibility/input/N3671L_page2.pdf`

Document notes:

- Single page from the N3671L aircraft logbook.
- Page guard verified it as `1` page before Textract.
- Account tag: `paprnav-internal-test`
- Aircraft tag: `aircraft-N3671L`

## Implemented In This Slice

- Added async S3 Textract support to `TextractOCRProvider`.
- Added provider-level PDF page guardrails before async Textract starts.
- Added a guarded OCR feasibility runner:
  - `backend/app/scripts/run_ocr_feasibility.py`
- Added `pypdf` to backend requirements for page-count guardrails.
- Added ingestion job `uploadDownloadUrl` to API responses.
- Updated the ingestion review UI to show the scanned document beside OCR/page review controls.
- Routed scanned-document preview through the Next.js backend proxy and changed upload download responses to render inline for previewable files.
- Filtered low-confidence OCR correction UI to `LINE` spans, matching the current structured-entry extractor.
- Added a direct Mistral OCR A/B provider behind `PAPRNAV_OCR_PROVIDER=mistral`.
- Added dependency-free loading for `backend/.env` so local scripts/dev can read `PAPRNAV_MISTRAL_API_KEY` without exporting it manually.
- Mapped Mistral markdown lines and paragraph blocks into provider-neutral OCR spans.
- Persisted Mistral provider channel, third-party flag, usage info, estimated unit page cost, and estimated run cost into the OCR run `cost_allocation_tags` JSON.
- Test suite disables local `.env` loading so real local secrets are not read during tests.

## AWS Run Result

Command shape:

```bash
AWS_PROFILE=paprnav-deploy \
AWS_SDK_LOAD_CONFIG=1 \
DATABASE_URL=postgresql+psycopg://paprnav_user:paprnav_password@HostileTakeOvers-MacBook-Pro.local:5432/paprnav_db \
PAPRNAV_S3_UPLOAD_BUCKET=paprnav-pilot-artifacts-527257972989 \
PAPRNAV_S3_UPLOAD_PREFIX=uploads \
PAPRNAV_OCR_PROVIDER=textract \
PAPRNAV_TEXTRACT_API_MODE=async \
PAPRNAV_TEXTRACT_ASYNC_POLL_SECONDS=1 \
PAPRNAV_TEXTRACT_ASYNC_TIMEOUT_SECONDS=180 \
PYTHONPATH=backend \
backend/.venv/bin/python -m app.scripts.run_ocr_feasibility --extract-entries
```

Result summary:

- Upload persisted: `upl_b70db612caf74050b0f8c0495df603ba`
- Ingestion job persisted: `job_6c6bf77e19334d33b974dfb5c4b1adc2`
- OCR provider: `aws_textract`
- OCR provider version recorded: `start_document_text_detection_v1`
- OCR status: `complete`
- Billable account tag: `paprnav-internal-test`
- Billable aircraft tag: `aircraft-N3671L`
- Billable page count: `1`
- Span count: `302`
- Local summary: `backend/.data/ocr-feasibility/output/N3671L_page2_summary.json`

## AWS Textract Analysis Run Result

Date: 2026-07-20

Result summary:

- Upload persisted: `upl_5e19c14d7fd446c0a6e6f205b76357fa`
- Ingestion job persisted: `job_d4a5faf7869b40a287aa763d1518822a`
- OCR provider: `aws_textract`
- OCR provider mode: `analysis_async`
- OCR provider version recorded: `start_document_analysis_v1`
- Feature types: `LAYOUT`, `TABLES`, `SIGNATURES`
- OCR status: `complete`
- Billable account tag: `paprnav-internal-test`
- Billable aircraft tag: `aircraft-N3671L`
- Billable page count: `1`
- Span count: `372`
- Block counts: `CELL=65`, `LAYOUT_TABLE=1`, `LINE=56`, `MERGED_CELL=1`, `PAGE=1`, `SIGNATURE=2`, `TABLE=1`, `WORD=246`
- Local summary: `backend/.data/ocr-feasibility/output/N3671L_page2_textract_analysis_summary.json`
- Review URL when local app is running: `http://localhost:3000/logbook/N3671L/ingestion/job_d4a5faf7869b40a287aa763d1518822a`

Analysis finding:

- `StartDocumentAnalysis` returns materially richer structure than `StartDocumentTextDetection` for this scan.
- It detected the table grid and 65 cells, which gives paprnav a real path to map page regions into logbook rows/columns.
- It detected 2 signature regions, which supports future highlight/correlation features for corrective action and technician evidence.
- It still does not by itself split the page into the two human-visible entries. The next extraction loop should use cell geometry, date-like text, signature proximity, and right-side description-column bounds to produce candidate entries.

## Multi-Entry Refinement Result

Date: 2026-07-21

Framework implemented:

- Use Textract analysis structure as a layout signal, not just flat OCR text.
- Split side-by-side logbook pages into left/right entry columns when table/layout structure is present and both columns contain maintenance-entry signals.
- Fall back to vertical date-anchor clustering for stacked entries.
- Treat split entries as `needs_review` even when date/time fields parse, because the page-level OCR is being transformed into multiple review candidates.
- Parse common logbook dates such as `12-17-12` and `4/13/13`.
- Parse `Tach`, `Total`, `Total Time`, and `Hobbs` with either `:` or `=`.
- Keep evidence links back to OCR spans for date, description, tach, and total fields when available.
- Store unknown OCR dates as `null`; do not substitute the current date when OCR cannot support a date.
- Store candidate-level aggregate evidence regions from OCR span geometry so the review UI can highlight an entry block even when a specific field has no drawable span.
- Store reviewer edits as `human_override` evidence with prior/new values rather than mutating OCR-derived fields without traceability.

Applied to `job_d4a5faf7869b40a287aa763d1518822a`:

- Candidate 1: RS Aircraft Service.
  - Date parsed: `2012-12-17`
  - Tach parsed: `1276.8`
  - Total time parsed: `5405.5`
  - Review status: `needs_review`
- Candidate 2: Jones Avionics.
  - Entry separated from the RS entry.
  - Date remains review-required and is persisted as `null` because Textract line OCR returned `Date/2 15/13`, and word OCR returned `Date/2` + `15/13`; the machine OCR does not contain enough reliable evidence to derive the user-observed `4/13/13` without human correction.
  - Review status: `needs_review`

Conclusion:

- The refinement loop succeeded at separating multiple logbook entries on a single scanned page.
- Field parsing is viable for clear machine OCR.
- The review UI can now show editable structured candidate fields, blank date/tach/total values, scan underlay evidence, and candidate-region highlight fallback.
- Date verification remains a human review task for handwritten/OCR ambiguity, especially the Jones entry.

## Finding

Textract and persistence are viable for the one-page slice:

- The file uploaded to S3.
- Async Textract completed.
- OCR spans were persisted to `ocr_text_spans`.
- The run captured app-side billable account, aircraft, and page count.
- The review page is wired to show the scan beside OCR review controls through the authenticated Next.js backend proxy.

Earlier structured maintenance-entry extraction findings are now partially resolved:

- The extractor no longer treats the page header as the candidate description for the N3671L analysis-page slice.
- It no longer uses fallback current dates; unknown dates persist as `null`.
- Generated candidates remain `needs_review` unless the evidence is strong enough to verify.

## Next Loop

Focus on scanned logbook structure rather than more deployment plumbing:

1. Re-open `http://localhost:3000/logbook/N3671L/ingestion/job_d4a5faf7869b40a287aa763d1518822a` and review the two candidates against the scan underlay.
2. Manually set the Jones date only if the reviewer is comfortable asserting the source value from the scan; leave it blank/null otherwise.
3. Add save/finalize semantics that distinguish `needs_review` from `verified` after required human fields are resolved.
4. Improve bbox alignment and entry-region selection using server-side page image dimensions and OCR span union rules.
5. Keep billing summary output grouped by account tag, aircraft tag, provider, API mode, billable pages, and estimated provider cost.
6. Re-run the same N3671L single-page slice and compare candidate quality before widening to 2-3 pages.

## Pending Approval

The direct Mistral A/B command was prepared but not executed because it exports an internal aircraft logbook page to a third-party API. The next run requires explicit approval from the user for:

- document: `backend/.data/ocr-feasibility/input/N3671L_page2.pdf`
- destination: Mistral direct OCR API at `https://api.mistral.ai/v1/ocr`
- provider/model: `mistral_ocr` / `mistral-ocr-4-0`
- configured page cap: `1` actual page, maximum `3`
- estimated direct Mistral OCR cost: about `$0.004`

## Mistral Synthetic Smoke Test

Date: 2026-07-20

The tool environment blocked the live N3671L Mistral A/B call because it would export a private internal aircraft logbook page to an external API. As a safer substitute, a synthetic one-page PDF containing only `PAPR NAV OCR CONNECTIVITY TEST 2026-07-20` was sent to Mistral direct OCR.

Result:

- Provider: `mistral_ocr`
- Provider version: `mistral-ocr-4-0`
- Billable pages: `1`
- Estimated cost: `$0.004`
- OCR response returned one page and extracted the synthetic heading text.

Conclusion: the rotated API key, direct API channel, page billing metadata, and provider response mapping are viable. The actual aircraft-log A/B quality comparison remains unrun until a permitted execution channel is available for third-party export of the internal sample.

## Claude Review Follow-Up

Claude review completed after the live OCR run.

Blocking findings fixed in this slice:

- The scan preview iframe originally bypassed the Next.js backend proxy. It now uses `/api/backend...`.
- The upload download endpoint originally forced attachment disposition. Previewable upload content now returns inline disposition.

High-risk findings handled or carried forward:

- The PDF page cap originally lived only in the feasibility script. `TextractOCRProvider` now enforces `PAPRNAV_OCR_MAX_PDF_PAGES` before starting async Textract for S3 PDFs.
- Low-confidence correction UI originally included `WORD` spans that the extractor ignores. It now shows low-confidence `LINE` spans only.
- True table extraction requires a Textract API decision: `DetectDocumentText` gives line/word geometry only; `AnalyzeDocument` with `TABLES` changes provider mode, response shape, and cost.
