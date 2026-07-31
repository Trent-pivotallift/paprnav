# paprnav Requirements

Last updated: 2026-07-27

These requirements describe the intended product direction and the current known implementation gaps. They should be refined as the project gains real backend behavior and customer validation.

## Product Purpose

paprnav helps aircraft owners and maintenance providers turn scanned aircraft logbooks into structured maintenance records, ingest FAA Airworthiness Directives, and identify likely AD compliance gaps with evidence and human review.

## Primary Users

- Aircraft owner: manages one or more aircraft, views logbooks, uploads records, checks compliance status.
- Maintenance shop user: manages client aircraft, searches/filter client records, adds or reviews maintenance entries.
- Future administrator: manages users, organizations, aircraft ownership, permissions, and system configuration.

## Core User Requirements

- Users can sign in and register.
- Users can view aircraft assigned to them.
- Aircraft owners can see a fleet dashboard with each aircraft's type, last log entry date, and AD/compliance status.
- Maintenance users can see client aircraft with owner, type, compliance status, and quick actions.
- Users can open an aircraft logbook page by N-number.
- Aircraft logbooks are organized into at least airframe, engine, and propeller sections.
- Users can view logbook entries with date, description, and performer/credential information.
- Users can upload scanned logbook records as PDF, JPG, JPEG, or PNG.
- Upload flow should validate file type and size before submitting.
- Uploaded logbooks are processed through OCR.
- Users can verify page order and confirm upload completeness before ingestion is treated as final.
- Each scanned page can receive an explicit maintenance review. The page UI should
  display a checkmark only when a currently authorized maintenance reviewer has
  completed that review, and should expose the reviewer, organization, role,
  timestamp, outcome, and notes.
- Maintenance review status must remain distinct from owner upload-completeness
  confirmation, OCR correction, verified structured entries, AD adjudication,
  and any regulatory approval or return-to-service signature.
- Low-confidence OCR regions are presented as highlighted snippets requiring user correction.
- User corrections are stored as auditable HITL annotations.
- Verified OCR plus user corrections populate structured logbook entries.
- Users can manually add logbook entries.
- Manually added entries begin unverified and require an assigned maintenance
  reviewer before they can participate in AD matching.
- Authorized users can add additional logbook volumes or component logs to an
  aircraft, give each log a clear label, associate it with the applicable
  component/serial number and date range when known, and then upload pages or
  add entries to that log.
- Users can open individual logbook entry details.
- Users can manage profile/account details.
- The system ingests FAA Airworthiness Directives from the FAA DRS bulk ZIP/Access database first, then compares and enriches those ADs with Federal Register publication records.
- The system matches AD requirements against structured logbook entries and creates HITL adjudication tasks when judgment is required.

## Compliance And Aviation Domain Requirements

- N-number is a central aircraft identifier and should be normalized consistently.
- Logbook records should preserve original uploaded files.
- Each logbook entry should track at minimum aircraft, logbook section, date, description, performer, source type, created user, and timestamps.
- Compliance status should distinguish compliant, warning/upcoming, and overdue states.
- Airworthiness Directive tracking is a core MVP compliance domain.
- AD ingestion must preserve DRS applicability provenance, Federal Register publication metadata when matched, structured extraction, confidence, supersession, and review status.
- AD matching must handle recurring/cyclical ADs, component-specific applicability, conditional applicability, and superseded ADs.
- DRS bulk source releases are stored once as platform-shared snapshots. Aircraft onboarding materializes or reuses target coverage and must not redownload a snapshot for a second client with an already covered make/model/component identity.
- Coverage identity must include installed engine, propeller, rotorcraft, drivetrain, and appliance targets when present; the admin UI may group by airframe make/model but matching and attribution must not collapse component applicability into an airframe-only key.
- AD source, coverage-set, and aircraft-comparison usage must be separately attributed. The first client to trigger coverage is provenance only and is not automatically charged for shared setup or storage.
- Actual incurred cost and future allocated cost must remain separate. Customer allocation is informational and non-billable until a versioned allocation policy is explicitly activated.
- Only human-verified logbook entries may participate in AD compliance matching.
- Only a user in an actively assigned maintenance organization may verify an
  OCR-derived entry or adjudicate an aircraft AD match. Each verification must
  retain the reviewer user and server timestamp. AD extraction approval is a
  platform-administrator action.
- If DRS bulk ingestion fails, users must see a degraded-coverage warning rather than a false complete worklist; the warning should mention that historical and DRS-indexed AD coverage is unverified or may be incomplete.
- Pre-1994 ADs are supported when present in DRS bulk data, but the product must not claim complete historical coverage until validation against DRS Web UI samples and historical FAA/index sources proves completeness. The 2026-06-21 T071 validation result is conditional and does not prove complete historical coverage.
- DRS collection failures must create admin-visible repair or reconciliation work items.
- HITL adjudications must be documented for software/admin review and future rule/model improvements.
- Auditability matters: future changes to maintenance records should retain history rather than silently overwrite.

## Technical Requirements

- Frontend uses Next.js App Router, React, TypeScript, Tailwind, and local UI components under `src/components/ui`.
- Backend uses FastAPI.
- Local database is Postgres, currently scaffolded via `backend/docker-compose.yml`.
- Frontend and backend should communicate through explicit API contracts.
- Shared mock data in frontend should be replaced with typed API-backed data.
- Authentication should be implemented before persisting user-specific data in production paths.
- OCR, AD ingestion, and matching may run as separate worker processes or microservices, but should first integrate through clear database/API boundaries.
- PostgreSQL is the authoritative OCR workflow and evidence store. OCR workers must use leases, bounded retries, idempotent recovery, and a terminal repair/dead-letter state before pilot volume is increased.
- OCR improvements may be added only behind the provider-neutral OCR interface. The layout-first improvement detects page regions, recognizes each crop, and returns evidence geometry without owning paprnav job state or creating authoritative logbook records directly.
- Textract Analysis remains the production OCR baseline until a common aviation-logbook benchmark demonstrates that another provider improves accepted-page quality or reviewer effort while meeting evidence, safety, latency, privacy, and cost gates.
- Direct Mistral processing of customer documents remains disabled until an approved US-based/private channel and data terms are available.
- The app should remain usable on desktop and mobile.
- Keep UI patterns consistent with the existing Shadcn/ui-style components.
- Run `npm run lint` and preferably `npm run build` after frontend changes.

## Infrastructure Requirements

- No AWS infrastructure is currently represented in the repo.
- No GitHub Actions workflow is currently present.
- Before uploading infrastructure changes, create explicit IaC files and document:
  - target AWS account and region
  - deployment tool
  - state storage
  - environment names
  - rollback expectations
  - secrets handling

## Known Gaps

Code review on 2026-06-20 confirms the earlier gap list was stale. The local MVP codebase now includes functional auth/session routes and UI, API-backed aircraft dashboards, manual logbook entries, upload/download APIs, ingestion job state, deterministic fixture-backed OCR processing, page verification, OCR correction, structured logbook extraction, Federal Register AD discovery, deterministic AD extraction, AD extraction review, first-pass AD/logbook matching, HITL AD adjudication, an evidence-backed compliance worklist, product observability, Alembic migrations, and backend tests.

Remaining known gaps:

- OCR is still deterministic fixture-backed for the local MVP slice; real OCR provider integration, rendered page/image artifacts, and production Textract/Tesseract behavior remain future work.
- AD ingestion is DRS-bulk-first with Federal Register comparison/enrichment. Fixture-backed Access parsing, DRS provenance storage, applicability targets, publications, reusable target coverage, client/aircraft coverage associations, and cost attribution are implemented. Full Federal Register XML/body artifact persistence and durable Federal Register delta monitoring remain incomplete.
- AD applicability is modeled with first-class `applicability_targets`, `installed_components`, `ad_publications`, `ad_target_applicability`, `ad_coverage_sets`, and `ad_coverage_subscriptions`. Matching retains approved extraction JSON for audit/replay while using structured component applicability when available.
- Aircraft component identity supports active installed-component rows and airframe/engine/propeller roles. Rich installation history, serial-range evaluation, appliances, twin-engine cases, and rotorcraft/drivetrain cases still require broader fixtures and refinement.
- AD extraction is shallow and deterministic. Full applicability/compliance extraction, source-section citations, structured compliance intervals, provider-backed LLM extraction, cache behavior, and richer review reconciliation remain incomplete.
- AD matching handles first-pass one-time and simple recurring cases and now uses installed components plus DRS/extraction applicability rows when present. It invalidates current results after logbook evidence changes and exposes incomplete-identity or stale-snapshot coverage warnings, but does not yet fully apply serial ranges, conditional applicability, component installation history, or deeper source reconciliation.
- FAA DRS bulk ZIP/Access fixture-first importing is implemented for identifier/source/applicability rows. Browser/Web UI scraping is not the default ingestion path and should be limited to validation/diagnostics unless a later decision changes that.
- DRS degraded-mode reconciliation issues are implemented for backend worker/admin surfacing; user-facing degraded-mode UX remains to be finished.
- Federal Register AD-to-FR matching for ADs discovered from DRS bulk data has an initial implementation; the reconciliation worker now flags missing FR matches and correction/supersession publication signals, but deeper legal/source conflict resolution remains future work.
- The AD cost admin view reports recorded physical source storage, estimated logical coverage storage, actual cost, allocated cost, and benefiting clients/aircraft. Provider/storage rates and a customer allocation policy remain intentionally inactive and uncalibrated.
- OpenAPI export and generated frontend TypeScript types are not wired yet; frontend types are still manually maintained.
- CI is not established in committed repository state. A local workflow draft may exist, but GitHub Actions cannot be treated as active until it is committed and pushed with proper credentials.
- No production infrastructure as code or deployment automation is committed. AWS work remains blocked until infrastructure, state, secrets, and rollback plans are explicitly modeled.
- Authorization is sufficient for the local owner/maintenance MVP flows, but full administrator workflows, invite flows, revocation UI, and fine-grained permissions remain future work.
