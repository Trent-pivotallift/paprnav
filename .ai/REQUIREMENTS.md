# paprnav Requirements

Last updated: 2026-06-20

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
- Low-confidence OCR regions are presented as highlighted snippets requiring user correction.
- User corrections are stored as auditable HITL annotations.
- Verified OCR plus user corrections populate structured logbook entries.
- Users can manually add logbook entries.
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
- AD ingestion is still a Federal Register discovery/extraction prototype. The revised target architecture is DRS bulk ZIP/Access ingestion first, then Federal Register comparison/enrichment. DRS bulk parsing, DRS provenance storage, full Federal Register XML/body artifact persistence, and durable Federal Register delta monitoring remain incomplete.
- AD applicability is not yet modeled with first-class `applicability_targets`, `installed_components`, `ad_publications`, or `ad_target_applicability` tables. Existing matching still relies on approved extraction JSON and flat aircraft/component fields.
- Aircraft component identity is still mostly represented as flat aircraft fields. Installed component history, roles, serial-specific applicability, removals, appliances, twin-engine cases, and rotorcraft/drivetrain cases remain to be modeled.
- AD extraction is shallow and deterministic. Full applicability/compliance extraction, source-section citations, structured compliance intervals, provider-backed LLM extraction, cache behavior, and richer review reconciliation remain incomplete.
- AD matching handles first-pass one-time and simple recurring cases and now uses installed components plus DRS/extraction applicability rows when present, but does not yet fully apply serial ranges, conditional applicability, component installation history, or stale-source reconciliation.
- FAA DRS bulk ZIP/Access fixture-first importing is implemented for identifier/source/applicability rows. Browser/Web UI scraping is not the default ingestion path and should be limited to validation/diagnostics unless a later decision changes that.
- DRS degraded-mode UX and admin repair alerts are not implemented.
- Federal Register AD-to-FR matching for ADs discovered from DRS bulk data has an initial implementation; deeper correction/supersession conflict handling remains future reconciliation work.
- OpenAPI export and generated frontend TypeScript types are not wired yet; frontend types are still manually maintained.
- CI is not established in committed repository state. A local workflow draft may exist, but GitHub Actions cannot be treated as active until it is committed and pushed with proper credentials.
- No production infrastructure as code or deployment automation is committed. AWS work remains blocked until infrastructure, state, secrets, and rollback plans are explicitly modeled.
- Authorization is sufficient for the local owner/maintenance MVP flows, but full administrator workflows, invite flows, revocation UI, and fine-grained permissions remain future work.
