# OCR Feasibility Status

Last updated: 2026-07-24

## Current Slice

Goal: prove whether paprnav can receive a scanned maintenance-log page, improve OCR through layout-first region recognition, persist evidence-aligned OCR results into the app schema, attribute billable OCR work to an account/aircraft, and expose the result for review. AWS Textract remains the baseline comparison.

Runtime choice:

- Continue with ECS/Fargate for the pilot.
- Keep OCR orchestration in the backend/worker container path.
- Do not make Lambda the primary OCR logic path.
- Keep PostgreSQL as the authoritative OCR queue/workflow store and add leased, bounded-retry execution before increasing volume.
- Use the layout-first OCR approach demonstrated by Neural Maze to improve paprnav's OCR engine: detect page regions, crop them, and recognize each crop with a vision model.
- Do not adopt Neural Maze's Rust gateway, Redis state, batching worker, Kubernetes/KEDA deployment, or scaling architecture.
- The local experiment is implemented behind the provider-neutral interface as `PAPRNAV_OCR_PROVIDER=layout_first_vlm`; Textract Analysis remains the production baseline until benchmark results justify a change.
- Retain the Mistral adapter, but do not send customer documents through direct Mistral until an approved US-based/private channel and data terms are available.

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
- Added the layout-first provider using PP-DocLayout-V3 region detection and local GLM-OCR crop recognition.
- Preserved full region boxes, polygons, reading order, layout confidence, recognition model, content hash, latency, and billable page count.
- Persisted the raw response hash and byte count with runtime/device channel
  metadata. The raw response is not duplicated into database JSON; governed,
  bounded S3 artifact retention remains a production-hardening item.
- Kept recognition confidence `null` because the local GLM-OCR response does not provide a calibrated text-confidence score.
- Added structured table-HTML conversion and extraction support for `REGION_*` spans.
- Added a repeatable local runner at `backend/app/scripts/run_layout_first_feasibility.py`.

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

## Local Layout-First Run Result

Command:

```bash
cd backend
PAPRNAV_DISABLE_DOTENV=1 \
.venv-glmocr/bin/python -m app.scripts.run_layout_first_feasibility
```

Result:

- Processing stayed local through PP-DocLayout-V3 and Ollama `glm-ocr:latest`.
- Input pages: `1`
- Detected regions: `2`, matching the two visible logbook entries.
- Billable page count: `1`
- Integrated provider latency: approximately `17.5-21.8` seconds on a 16 GB Apple Silicon Mac after model installation.
- Output: `backend/.data/ocr-feasibility/output/N3671L_page2_layout_first_summary.json`
- Left candidate:
  - date: `2012-12-17`
  - tach: `1276.8`
  - total time: `5405.5`
  - full-entry evidence region: `glm-region-0`
- Right candidate:
  - OCR date candidate: `2013-12-05`, still requiring visual confirmation
  - tach: `null`
  - total time: `null`
  - full-entry evidence region: `glm-region-1`
- Both candidates remain `needs_review` because recognition confidence is unavailable and handwritten details are not authoritative.
- The layout-first result recovered substantially more maintenance text and separated the two entries more directly than the current Textract result.
- The result still contains recognition defects and concatenated fields, including uncertain handwritten values and imperfect credential/part-number transcription. It is an improvement candidate, not verified maintenance data.

## AWS-Coupled Layout-First Acceptance Result

Date: 2026-07-24

Result:

- The approved one-page PDF was read from the paprnav S3 artifact path while
  PP-DocLayout-V3 and GLM-OCR inference ran locally through the provider-neutral
  backend path.
- Final ingestion job: `job_0554117882644078b0aaa943366b364a`
- Upload: `upl_bc1f9df21e1748849b7ea246a838c1a0`
- Billable account tag: `paprnav-internal-test`
- Billable aircraft tag: `aircraft-N3671L`
- Billable page count: `1`
- Estimated internal cost: `$0.00` because the local feasibility rate remains
  intentionally unconfigured; page units are still attributed for later pricing.
- Candidate 1: date `2012-12-17`, tach `1276.8`, total `5405.5`.
- Candidate 2: OCR date candidate `2013-12-05`, tach `null`, total `null`.
- Both candidates remain `needs_review`.
- Review URL:
  `http://localhost:3000/logbook/N3671L/ingestion/job_0554117882644078b0aaa943366b364a`
- Browser acceptance confirmed two editable candidates and a loaded
  `2708 x 733` evidence underlay.
- Backend verification: `59` tests pass in both the existing Python 3.9
  development environment and the isolated Python 3.12 OCR environment.
- Claude Sonnet review was run after two self-review passes. Its packaging,
  cost metadata, header-only region, date-removal, polygon, and confidence-scale
  findings were addressed and covered by tests.

## Same-Page Provider Decision

Date: 2026-07-24

The stored Textract Analysis job `job_d4a5faf7869b40a287aa763d1518822a`
and local layout-first job `job_0554117882644078b0aaa943366b364a`
processed uploads with the identical SHA-256
`a751b7f7ecb656eb6c8b513d3362b614185e2c10d808f4f4353323e4b84d9304`.

| Criterion | Textract Analysis | Local layout-first |
| --- | --- | --- |
| Entry separation | Two candidates with current parser | Two directly detected regions |
| Left date/tach/total | `2012-12-17`, `1276.8`, `5405.5` | Same |
| Explicit AD text | Preserves `C/W AD 11-10-09` after date-cleanup fix | Preserves the same claim coherently |
| Jones date | Unresolved/null from malformed low-confidence text | Emits uncertain `2013-12-05` |
| Evidence | Granular line boxes | Coarse whole-entry regions |
| Recognition confidence | Calibrated per line | Unavailable/null |
| Current measured local runtime | Not re-invoked in this loop | `22.302147` seconds on one page |
| Pricing | Configured per-page rate | Configured compute-hour rate |

Decision: Textract Analysis remains primary. The local path remains a retained
challenger because its coherent region recognition may reduce correction effort,
but the unsupported-looking Jones date blocks promotion. Widen the benchmark to
representative approved pages before building the dedicated ECS OCR worker
image.

Future platform consideration: if evidence later supports replacing ECS/Fargate
with EKS, evaluate packaging the local OCR engine or suitable pipeline components
as WebAssembly before adopting large Kubernetes OCR containers. Compare WASM
against a dedicated OCI worker using actual model compatibility, accelerator
access, startup latency, memory, model distribution, isolation, observability,
and customer-attributed compute cost. This does not change the current
ECS/Fargate pilot decision.

Provider-neutral usage metering is now first-class on `OCRRun`:

- customer account and aircraft tags
- provider and model/version
- billable page count
- processing seconds
- pricing unit and configured rate
- estimated run cost

Elapsed processing time is populated for fixture, Textract, local layout-first,
and Mistral adapter results. Pricing rates and estimated costs use
fixed-precision database values for customer and aircraft rollups.

Recognition confidence remains field/span evidence metadata and is nullable. It
is not used as a billing dimension.

The deterministic maintenance parser now extracts explicit normalized AD
references and claim context without treating ordinary entry dates as ADs. AD
matcher `0.3.0` requires a verified entry with an explicit positive compliance or
inspection claim before producing `candidate_satisfied`; ambiguous, mentioned,
negated, or unverified claims route to adjudication. Structured maintenance
text is parsed once per entry for an aircraft matching run, and the ordinary
match-list API excludes stale results produced by earlier matcher versions and
reports `pending_recomputation` until the AD matcher worker produces current
results.
Recurring ADs remain unresolved until current due status can be calculated
rather than inferred from the mere existence of a prior compliance entry.

## Next Loop

Continue in small, verified OCR loops. Do not split this work into a parallel provider/scaling chore list.

### Loop 1: Close the current human-review slice

1. Re-open `http://localhost:3000/logbook/N3671L/ingestion/job_d4a5faf7869b40a287aa763d1518822a` and review the two candidates against the scan underlay.
2. Manually set the Jones date only if the reviewer is comfortable asserting the source value from the scan; leave it blank/null otherwise.
3. Add save/finalize semantics that distinguish `needs_review` from `verified` after required human fields are resolved.
4. Improve bbox alignment and entry-region selection using server-side page image dimensions and OCR span union rules.
5. Keep billing summary output grouped by account tag, aircraft tag, provider, API mode, billable pages, and estimated provider cost.
6. Re-run the same N3671L single-page slice and compare candidate quality before widening to 2-3 pages.

Exit condition: both candidates can be reviewed, corrected, finalized, and traced to visible source evidence without inventing an unsupported field value.

### Loop 2: Implement the layout-first OCR improvement

Status: provider path, AWS-coupled N3671L acceptance run, audit metadata, and
critical review fixes are implemented; failure-fixture closure remains.

1. Record the selected region detector, vision recognizer, SDK documentation, versions, and licenses in `.ai/PROVIDER_REFERENCES.md`.
2. Add `PAPRNAV_OCR_PROVIDER=layout_first_vlm` behind the existing provider-neutral result objects.
3. Render only approved pages, detect semantic regions, and preserve detector labels, geometry, and detector scores.
4. Crop accepted regions, recognize each crop with the configured vision model, and reassemble them in deterministic page reading order.
5. Preserve geometry, polygons, reading order, model/configuration versions, raw
   response hash/size, latency, page count, and internal cost metadata. Add a raw
   artifact reference only with bounded, encrypted object storage and lifecycle
   retention.
6. Keep layout confidence separate from recognition confidence. Record recognition confidence as unavailable when the model cannot provide a calibrated value.
7. Use fixtures to cover malformed regions, missing geometry, overlapping regions, empty recognition, timeout, partial failure, and model/configuration changes.

Exit condition: the same paprnav ingestion/review flow can consume a layout-first OCR result with correctly aligned evidence, separate the two known N3671L entries, and avoid inventing recognition confidence or absent field values.

### Loop 3: Compare providers on the same evidence

1. Start with the existing one-page N3671L slice, then widen only to approved or de-identified pages covering handwriting, typed text, tables, side-by-side entries, skew, signatures, stamps, and blank/dash semantics.
2. Run Textract Analysis and the layout-first OCR pipeline with versioned configurations against identical pages. Include Mistral only after an approved US-based/private channel is available.
3. Measure entry separation; date, tach, total-time, and credential accuracy; blank/dash preservation; evidence-region overlap; unsupported/hallucinated fields; latency; cost; reviewer corrections; and reviewer time.
4. Include failures, page-limit results, retries, and timeouts instead of scoring successful pages only.
5. Define promotion thresholds before widening the corpus toward approximately 50-100 representative pages.

Exit condition: evidence shows whether the layout-first improvement materially reduces field error or reviewer effort while meeting privacy, audit, latency, and cost constraints. Textract remains the default until that condition is met.

### Loop 4: Make each OCR run recoverable before adding volume

1. Add a transactional PostgreSQL job lease with attempt number, lease owner/expiry, heartbeat, and next-attempt time.
2. Run provider calls outside the claim transaction and make expired leases reclaimable.
3. Classify retryable failures, add bounded exponential backoff, and add a terminal manual-repair/dead-letter state.
4. Make partial page/span persistence safe to retry without duplicates or unique-constraint failure.
5. Run the worker continuously or on a deployed short schedule with graceful shutdown.
6. Exercise concurrent claim, crash/lease-expiry, timeout, partial-write, retry-success, exhausted-attempt, and duplicate-delivery cases.

Exit condition: a killed or duplicated worker cannot lose a job, create duplicate evidence, or leave the job permanently unclaimable.

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
