# paprnav Requirements

Last updated: 2026-06-16

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
- The system ingests FAA Airworthiness Directives from the Federal Register API.
- The system matches AD requirements against structured logbook entries and creates HITL adjudication tasks when judgment is required.

## Compliance And Aviation Domain Requirements

- N-number is a central aircraft identifier and should be normalized consistently.
- Logbook records should preserve original uploaded files.
- Each logbook entry should track at minimum aircraft, logbook section, date, description, performer, source type, created user, and timestamps.
- Compliance status should distinguish compliant, warning/upcoming, and overdue states.
- Airworthiness Directive tracking is a core MVP compliance domain.
- AD ingestion must preserve source metadata, structured extraction, confidence, supersession, and review status.
- AD matching must handle recurring/cyclical ADs, component-specific applicability, conditional applicability, and superseded ADs.
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

- Auth screens are non-functional.
- Dashboard data is hardcoded.
- Upload flow simulates success and does not call an API.
- No OCR pipeline exists.
- No page-order/completeness verification exists.
- No low-confidence OCR correction workflow exists.
- No AD ingestion or AD/logbook matching exists.
- No HITL adjudication model exists.
- Backend exposes only placeholder/local-readiness endpoints: `/`, `/health`, and `/version`.
- No database schema or migrations exist.
- No tests exist in the checked files reviewed for this note.
- Frontend README has been replaced, but backend and root project docs are still thin.
- No deployment/infrastructure automation exists.
