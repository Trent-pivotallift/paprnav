# paprnav Decisions

Last updated: 2026-06-20

Record decisions here when they affect future implementation. Keep entries short and include the reason.

## Active Decisions

### D001: Use Next.js App Router for the frontend

Status: accepted

The frontend is already built with Next.js App Router under `frontend/paprnav-frontend/src/app`. Continue using route groups for auth and authenticated application areas.

### D002: Keep the UI component approach aligned with Shadcn/ui patterns

Status: accepted

The current UI uses local components in `src/components/ui`, Radix primitives, Tailwind, lucide-react icons, and `cn` utilities. New UI should reuse and extend this pattern before introducing new UI libraries.

### D003: Use FastAPI for the backend API

Status: accepted

The backend is currently a minimal FastAPI app in `backend/main.py`. Continue with FastAPI unless there is a deliberate architecture change.

### D004: Use Postgres as the relational datastore

Status: accepted

`backend/docker-compose.yml` already provisions Postgres 16. The aviation logbook domain has relational entities and audit/history needs that fit Postgres well.

### D005: Treat the current frontend data as mock data only

Status: accepted

Dummy aircraft and logbook arrays in frontend pages are placeholders. Do not build additional product behavior on them as if they are persistent state.

### D006: No AWS changes until infrastructure is explicitly modeled

Status: accepted

AWS credentials are available in the local environment, but this repo currently has no IaC, workflows, or deployment manifest. Any AWS deployment work should first add documented infrastructure definitions and reviewable deployment commands.

### D007: Use `.ai` as the AI handoff and planning folder

Status: accepted

Future agents should use `.ai/README.md`, `.ai/REQUIREMENTS.md`, `.ai/DECISIONS.md`, and `.ai/GOAL_TASKS.md` as the starting context for `/goal` work.

### D008: Treat OCR-assisted logbook ingestion and AD matching as core MVP behavior

Status: accepted

The MVP is not complete with CRUD logbooks alone. It must support scanned logbook upload, OCR, page-order/completeness verification, low-confidence OCR correction, structured logbook ingestion, AD ingestion, AD-to-logbook matching, and HITL adjudication.

### D009: Retain AD data after ingestion

Status: accepted

Keep structured AD data indefinitely and retain raw/source artifacts or source snapshots with content-hash de-duplication and lifecycle policies for bulky files. Re-fetching later should be a fallback, not the primary audit strategy, because matching must be reproducible and supersession/HITL decisions require citations.

### D010: Use FastAPI-owned session auth for the local MVP

Status: accepted

For the MVP, implement auth in FastAPI with Postgres-backed users, password hashes, server-managed sessions, and secure HTTP-only cookies. This keeps local development unblocked without requiring AWS Cognito or another hosted provider before infrastructure exists. User records should include room for future external identity fields so production can later move to Cognito or another provider without rewriting domain ownership.

Follow-up implementation tasks:

- T017 should include user and session-compatible identity fields.
- T019 should implement register, login, logout/session, and current-user endpoints.
- T020 should wire the frontend to cookie-based auth and remove the dev dashboard bypass.
- T033 should document session secret and cookie/security environment variables.

### D011: Let FastAPI own OpenAPI schemas and generate frontend types

Status: accepted

Backend request/response contracts should be defined with Pydantic schemas in the FastAPI app. FastAPI's OpenAPI document is the source of truth for API shape. The frontend should use generated TypeScript types from that OpenAPI schema once backend schemas exist, with `.ai/API_CONTRACT.md` serving as the interim human-readable contract before code generation is wired.

Follow-up implementation tasks:

- T016 should create a backend app structure with a clear schema module.
- T021, T023, T027, T040, and later AD/OCR endpoints should define Pydantic request and response models.
- A future tooling task should add an OpenAPI export command and TypeScript type generation step.

### D012: Use SQLAlchemy 2.0 plus Alembic for persistence and migrations

Status: accepted

Use SQLAlchemy 2.0 ORM models for Postgres persistence and Alembic for database migrations. This matches FastAPI/Postgres conventions, supports local Docker Postgres and future AWS RDS/Aurora, and gives reviewable schema diffs before persistent data is introduced.

Follow-up implementation tasks:

- T016 should add backend settings, database engine/session wiring, and migration placeholders.
- T017 should add the initial schema and first Alembic migration.
- T033 should document `DATABASE_URL` and migration commands.

### D013: Use a storage abstraction with local filesystem for dev and S3 for production

Status: accepted

Uploaded logbook files and retained AD source artifacts should go through a storage interface. Local development should store files under a configurable local data directory, such as `backend/.data`, which must not contain committed user uploads. Production should use S3 or S3-compatible object storage with bucket/key references, content hashes, server-side encryption, and lifecycle policies for bulky artifacts.

Implementation expectations:

- Persist `storage_backend`, `storage_key`, content type, file size, and SHA-256 hash in Postgres.
- Keep original uploaded logbook files retrievable.
- Use environment variables for local data path, production bucket, and maximum upload size.
- Default maximum upload size should be `100 MB` until real sample logbooks prove a different limit is needed.
- Do not store AWS keys or storage secrets in the repo; production should prefer IAM role credentials and managed secret/config services.
- Start with backend-mediated uploads for MVP; presigned S3 uploads can be added later if file size or deployment shape requires it.
- T012/T034 should include an S3 bucket, encryption, IAM access, lifecycle policies, and rollback expectations when production infrastructure is modeled.

### D014: Use an OCR provider abstraction with a deterministic local provider first

Status: accepted

The OCR pipeline should depend on a provider interface, not directly on a cloud SDK. For local MVP implementation, start with a deterministic fixture/mock provider or local adapter that can persist page, text, bounding-box, and confidence records without requiring AWS. The production-oriented provider target is AWS Textract, because paprnav is expected to live in AWS and Textract returns page geometry and confidence data needed for HITL review.

Required provider-neutral OCR output:

- page number and rendered page/image reference
- span type: word, line, block, or region
- text
- confidence score, stored with an explicit scale; Textract maps naturally to `0-100`
- bounding box coordinates and units; Textract maps to ratio units, while Tesseract adapters may emit pixel units
- optional polygon and rotation metadata when providers expose it
- reading order
- provider block/span ID and source relationships where available
- provider name, provider version, configuration hash
- raw provider artifact reference when useful for audit/replay

Follow-up implementation tasks:

- T041 should define the provider interface and include a deterministic local provider.
- T041 must check current official Textract docs and any selected local OCR adapter docs before finalizing the interface, then record the mapping in `.ai/PROVIDER_REFERENCES.md`.
- A later provider task can add Textract behind the same interface.
- T043 should consume provider-neutral low-confidence spans rather than provider-specific objects.

### D015: Use hybrid deterministic and LLM-assisted AD extraction

Status: accepted

AD extraction should start with deterministic parsing/classification for Federal Register metadata, title/body AD detection, dates, AD numbers, and obvious supersession text. Structured applicability and compliance requirements should allow LLM-assisted extraction behind a provider interface, with schema validation and review routing before results become authoritative for matching.

Required extraction metadata:

- provider name and version
- extraction schema version
- ruleset version or prompt hash
- input content hash
- output content hash when useful
- confidence score
- source citations
- review status

Review thresholds:

- Route to review when extraction confidence is below `0.80`.
- For the local deterministic AD extractor, route to review when confidence is below `0.86` because applicability and compliance details are intentionally shallow until provider-backed extraction is added.
- Route to review when applicability, compliance interval, or supersession fields are missing or uncertain.
- Route to review when deterministic and LLM outputs disagree on safety-critical fields.

Follow-up implementation tasks:

- T047 should persist source records, extraction metadata, applicability, requirements, supersession, and review state.
- T049 should validate extraction output against a schema and route low-confidence outputs to review.
- T050 should expose the review queue for accept/edit/reject/defer decisions.

### D016: Verify external provider behavior from current official docs before implementation

Status: accepted

When a task depends on an external service, SDK, API, CLI, file format, or provider-specific output shape, do not design or implement from memory. Check current official documentation or another primary source first, record the docs checked in `.ai/PROVIDER_REFERENCES.md`, and map paprnav's provider-neutral abstractions back to the source fields.

This applies especially to AWS services, OCR engines, Federal Register APIs, LLM/extraction providers, GitHub Actions, deployment tooling, and any future production infrastructure.

Acceptance expectations for affected tasks:

- Cite the official docs or primary source checked.
- Record the date checked.
- List source fields/behaviors used by the implementation.
- Explain any provider-neutral normalization, units, confidence scales, IDs, pagination, rate limits, or async behavior.
- Keep raw provider artifacts or hashes where needed for audit/replay.

### D017: Use DRS bulk data first, then Federal Register comparison

Status: accepted

For the revised AD ingestion build, the primary AD corpus and applicability path should start from the FAA DRS bulk download. The current public DRS bulk package was validated on 2026-06-20 as a ZIP containing an Access database (`ADFinalRulesEmergencyADs_05312026.accdb`) with AD identifiers from 1941 through 2026. Federal Register ingestion remains mandatory, but its role shifts to comparison, enrichment, source-of-record metadata for published rules, XML/body extraction when available, correction/supersession reconciliation, and scheduled delta monitoring.

Reason:

- The product question is aircraft/component-specific: "which ADs apply to this aircraft and installed equipment?"
- DRS is closer to the indexed applicability workflow for aircraft, engine, propeller, and appliance targets, including older ADs that may not be covered cleanly by modern Federal Register API discovery.
- The DRS bulk ZIP validation found 100% full-source coverage for the 2024 Federal Register AD identifier set. The weaker 91.58% AD-year surrogate coverage was a date-window artifact because early-2024 Federal Register publications included late-2023 AD numbers that were present in the full DRS ZIP.
- Federal Register is still valuable for authoritative publication metadata and text, but FR-first discovery can miss or delay the target-specific applicability universe the app needs for a compliance worklist.

Implementation expectations:

- DRS bulk ZIP retrieval and Access database parsing are the default implementation path. Browser/UI scraping is not the default ingestion path.
- The pipeline should store the DRS bulk ZIP/Access artifact or a content-hashed retained source snapshot, parse DRS rows into directives/publications/applicability targets, and then match each AD to Federal Register records when possible.
- If future DRS bulk retrieval fails, the system should fail visibly and create admin repair work rather than silently switching to an apparently complete Federal Register-only corpus.
- DRS Web UI automation may be used as a validation or diagnostic path to compare sampled UI results against the bulk database, but it must remain manually gated, rate-limited, fixture-backed, and disabled in CI.
- Federal Register delta polling should still detect new FAA AD publications and mark affected targets stale or in need of reconciliation.
- If DRS bulk ingestion fails or appears stale/broken, the app must show a degraded-coverage warning instead of implying a complete AD universe. Do not claim pre-1994 coverage is unavailable by default; the current DRS bulk data contains substantial pre-1994 coverage. Warn that historical and DRS-indexed AD coverage is unverified or may be incomplete until DRS collection is restored.
- DRS failures must create admin-visible reconciliation/workflow issues so maintainers know source retrieval, parser logic, or fixture assumptions need review.
- Pre-1994 completeness is not proven by the current validation. Treat it as supported where present in DRS bulk data, and add separate validation against DRS Web UI samples and historical FAA/index sources before claiming complete historical coverage.
- The user-facing output remains decision support, not compliance attestation.

### D018: Keep PostgreSQL as the durable OCR workflow queue and system of record

Status: accepted 2026-07-23

Paprnav will not replace its ingestion-job, OCR-run, page, span, correction, and evidence records with a Redis task/result store. PostgreSQL remains the authoritative workflow state and durable queue for the pilot. Workers claim jobs with a lease using transactional row locking (`FOR UPDATE SKIP LOCKED` or an equivalent compare-and-set), renew the lease while working, and finish attempts idempotently.

Required execution semantics:

- A job claim records attempt number, lease owner, lease expiry, started time, and heartbeat time.
- A worker crash makes the job reclaimable after lease expiry; claiming work must not remove the only durable copy of the job.
- Retries are bounded and use exponential backoff with jitter.
- Exhausted or non-retryable work enters a terminal dead-letter/manual-repair state with sanitized error details.
- A new attempt either resumes from an explicitly valid checkpoint or removes/replaces that attempt's partial page/span output transactionally before retrying.
- Provider calls and long-running provider polling must not hold an open database transaction.
- Provider request identifiers and attempt metadata are persisted for reconciliation and cost review.
- Redis may be introduced later for cache, notifications, rate limiting, or disposable acceleration, but not as the sole owner of documents, workflow state, or OCR results.

Scaling decision:

- Run the API and ordinary background workers on ECS/Fargate for the pilot.
- Trigger workers continuously or on a short schedule; do not rely on a manually invoked run-once database drain.
- Scale worker task count from leased/pending-job age and queue depth, while protecting each provider with explicit concurrency and rate limits.
- Revisit SQS only when PostgreSQL polling or operational contention is measured as a bottleneck. If adopted, SQS is a wake-up/delivery mechanism and PostgreSQL remains authoritative.

Apply this decision incrementally through the OCR feasibility `Next Loop` in `.ai/OCR_FEASIBILITY_STATUS.md`.

### D019: Improve paprnav OCR with a layout-first vision pipeline

Status: accepted 2026-07-23

Paprnav will use the layout-first OCR approach demonstrated by Neural Maze to improve OCR quality: render a page, detect semantic regions, crop those regions, recognize each crop with a vision model, and reassemble the results in deterministic reading order. Neural Maze is research input for this OCR improvement, not a service or architecture to integrate. No other Neural Maze component or architecture is adopted.

The implementation remains behind paprnav's existing `OCRProvider` interface as `PAPRNAV_OCR_PROVIDER=layout_first_vlm`. Paprnav continues to own uploads, job state, retries, OCR runs, evidence, review, and billing records.

The pipeline stages are:

1. Render only the selected PDF pages into bounded-resolution page images.
2. Detect semantic regions and preserve each detector label, bounding box or polygon, and detector score.
3. Crop each accepted region using the detected geometry.
4. Recognize each crop with the configured vision model.
5. Reassemble recognized regions by page and deterministic reading order.
6. Map the result into `OCRProviderResult`, `OCRPageResult`, and `OCRSpanResult`.

The integration contract must preserve:

- page number and page dimensions
- semantic region/span type
- recognized text
- normalized bounding boxes or polygons with declared units
- deterministic reading order
- region/provider IDs and parent/child relationships
- provider/model/layout-model versions and configuration hash
- layout confidence separately from recognition confidence
- per-page or per-region recognition confidence only when the recognizer provides a calibrated value
- raw result content hash and byte count for audit; retain a raw artifact
  reference only after bounded object storage, encryption, access, and lifecycle
  retention are configured
- billable page count, latency, hardware/channel metadata, and estimated internal cost

If the recognizer cannot provide calibrated confidence, paprnav records recognition confidence as unavailable. A layout detector score describes region detection only and must not be presented as confidence in the recognized text. Generative output never becomes authoritative merely because it is fluent.

Provider policy:

- Textract Analysis remains the production baseline until benchmark results justify a change.
- The layout-first pipeline is an OCR-quality improvement candidate for difficult handwriting, multiple entries on one page, side-by-side entries, and page-layout recovery.
- The first acceptance case is the existing N3671L page: detect its two maintenance entries separately, associate recognized text and evidence geometry with the correct entry, preserve truly absent tach/total values as null, and reduce manual correction without adding unsupported text.
- The Mistral adapter remains implemented but direct processing of customer documents stays disabled until an approved US-based/private processing channel and data terms are available.
- Provider selection is configuration- and policy-driven, not embedded in domain extraction logic.

Apply this decision incrementally through the OCR feasibility `Next Loop` in `.ai/OCR_FEASIBILITY_STATUS.md`.

### D020: Keep Textract Analysis primary and the local layout-first path as a challenger

Status: accepted 2026-07-24

The one-page N3671L A/B comparison used two uploads with the identical SHA-256
`a751b7f7ecb656eb6c8b513d3362b614185e2c10d808f4f4353323e4b84d9304`.
Textract Analysis and the local PP-DocLayout-V3 plus GLM-OCR path both produced
two candidate maintenance entries after the current entry parser was applied.

Textract Analysis remains the production baseline because it provides granular
line evidence and calibrated recognition confidence, preserves the uncertain
Jones date as unresolved, and runs through the intended AWS worker path. The
local path recovered a more coherent left-entry narrative and separated the two
page regions directly, but it also produced a plausible-looking uncertain Jones
date and concatenated several right-entry fields. Its recognition confidence is
unavailable and must remain `null`.

The local provider stays in the repository as a benchmark challenger. It is not
yet promoted to an ECS runtime. Promotion requires a representative-page
benchmark showing lower accepted-field error or reviewer effort without
unsupported fields, plus a calibrated compute rate and an ECS-compatible
dedicated OCR worker image. Do not add the local model stack to the ordinary API
image.

All providers write usage to `OCRRun` with customer and aircraft attribution,
billable pages, elapsed processing time, pricing unit, configured pricing rate,
and estimated run cost. Textract uses a configured per-page rate. Local OCR uses
an hourly compute rate, even when that rate is intentionally zero during
feasibility work. Pricing rates and estimated costs use fixed-precision database
columns so account and aircraft rollups do not accumulate binary floating-point
error.

Deterministic AD matching version `0.3.0` normalizes explicit two- and four-digit
AD references. Candidate satisfaction requires an explicit normalized AD
reference, compliance or inspection language, and a verified logbook entry.
Negated claims such as `not complied` or `inspection not completed`, mere
mentions, keyword overlap, and unverified OCR candidates require adjudication.
Disposition parsing is scoped to the OCR-line context owned by each explicit AD
citation and bounded by neighboring AD citations and sentence separators.
Internal comma-set-off phrases remain in the claim, while decimal regulation
references such as `43.13` are not treated as sentence boundaries. Negative
evidence is evaluated conservatively across that citation context; positive
compliance or inspection evidence must occur in the citation's immediate clause
so an unrelated later action cannot promote the AD to satisfied.
Recurring directives also require adjudication until the matcher can calculate
current due status from verified intervals and aircraft/component time state.
Structured maintenance text is parsed once per entry for each aircraft matching
run, and the normal match-list API exposes only the current matcher version;
older replay records remain stored for audit. The list response reports
`pending_recomputation` when only stale results exist so an empty current result
set cannot be mistaken for a completed no-match result. Recalculation remains a
worker operation rather than a side effect of a read request.

## Proposed Decisions To Resolve Soon

### P001: Authentication provider

Resolved by D010.

### P002: API boundary and schema format

Resolved by D011.

### P003: File storage target

Resolved by D013.

### P004: Migration tool

Resolved by D012.

### P005: Monorepo layout

Decide whether to make the project root a Git repo containing both frontend and backend, or keep the nested frontend repo and manage backend separately.

### P006: OCR provider

Resolved by D014.

### P007: AD extraction provider

Resolved by D015.

### P008: AD source ordering

Resolved by D017.
