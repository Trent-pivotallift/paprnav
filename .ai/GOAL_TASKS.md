# paprnav Agent-Digestible Tasks

Last updated: 2026-06-16

Use these as candidates for `/goal`. Each task should be small enough for one agent run to complete, verify, and summarize without needing broad product decisions.

This file should describe a path to a working webapp, not only documentation and cleanup. The early tasks reduce ambiguity; the later tasks turn paprnav into an integrated MVP.

## Task Format For `/goal`

Suggested prompt shape:

```text
/goal Complete task T### from .ai/GOAL_TASKS.md. Read .ai/README.md, .ai/REQUIREMENTS.md, and .ai/DECISIONS.md first. Keep changes scoped, run relevant checks, and update .ai files if decisions or task status change.
```

## Ready Tasks

### T001: Replace default frontend README with paprnav-specific developer README

Status: completed 2026-06-16

Goal: Update `frontend/paprnav-frontend/README.md` so it describes paprnav, local setup, scripts, route overview, and current mock-data limitations.

Acceptance:

- README no longer reads like a default Create Next App file.
- Includes frontend setup commands.
- Mentions backend is currently separate and minimal.
- Mentions `.ai` as project memory.
- No behavior changes.

Suggested checks:

```bash
cd frontend/paprnav-frontend
npm run lint
```

### T002: Add backend developer README

Status: completed 2026-06-16

Goal: Add `backend/README.md` describing FastAPI startup, Postgres compose usage, environment assumptions, and current API surface.

Acceptance:

- Documents `uvicorn main:app --reload`.
- Documents `docker compose up db`.
- Calls out current placeholder endpoint.
- Notes missing migrations/schema.

Suggested checks:

```bash
cd backend
python -m py_compile main.py
```

### T003: Define initial backend domain model plan

Status: completed 2026-06-16

Goal: Create a design note, likely `.ai/DATA_MODEL.md`, for users, organizations, aircraft, logbook sections, logbook entries, uploads, and compliance statuses.

Acceptance:

- Defines entities and relationships.
- Lists required fields and open questions.
- Does not implement database tables yet.
- Updates `.ai/DECISIONS.md` only if a durable choice is made.

Suggested checks:

```bash
find .ai -maxdepth 1 -type f -name '*.md' -print
```

### T004: Add typed frontend mock data module

Status: ready

Goal: Move hardcoded aircraft and logbook mock arrays from pages into a typed module under `frontend/paprnav-frontend/src/lib` or `src/data`.

Acceptance:

- Pages import typed mock data instead of declaring arrays inline.
- Types represent owner aircraft, client aircraft, and logbook entries.
- UI behavior remains the same.
- Lint passes.

Suggested checks:

```bash
cd frontend/paprnav-frontend
npm run lint
npm run build
```

### T005: Wire upload page to a local API abstraction

Status: ready

Goal: Add a frontend API helper for logbook uploads and update the upload page to call it, while the helper can still simulate success until the backend endpoint exists.

Acceptance:

- Upload page no longer contains raw fake delay logic inline.
- API helper has a clear function signature for future backend integration.
- Existing success/error UI still works.
- File validation remains or improves.

Suggested checks:

```bash
cd frontend/paprnav-frontend
npm run lint
npm run build
```

### T006: Add FastAPI health and version endpoints

Status: completed 2026-06-16

Goal: Expand `backend/main.py` with `/health` and `/version` endpoints suitable for local checks and future deployment probes.

Acceptance:

- `/health` returns a stable JSON status.
- `/version` returns app name and version.
- Existing `/` still works or redirects intentionally.
- Backend Python compile check passes.

Suggested checks:

```bash
cd backend
python -m py_compile main.py
```

### T007: Add backend CORS configuration for local frontend development

Status: completed 2026-06-16

Goal: Configure FastAPI CORS middleware so the local Next dev server can call the API.

Acceptance:

- CORS origins are explicit for local development.
- Configuration is easy to adjust via environment variables or constants.
- `requirements.txt` remains sufficient or is updated if needed.
- Backend Python compile check passes.

Suggested checks:

```bash
cd backend
python -m py_compile main.py
```

### T008: Create initial API contract document

Status: ready

Goal: Add `.ai/API_CONTRACT.md` describing first-pass endpoints for aircraft list, logbook entries, upload initiation/completion, and auth assumptions.

Acceptance:

- Documents routes, methods, sample request/response shapes.
- Marks unresolved auth and file storage decisions.
- Does not implement code.

Suggested checks:

```bash
find .ai -maxdepth 1 -type f -name '*.md' -print
```

### T009: Add frontend empty/loading/error states for dashboard data

Status: ready after T004

Goal: Prepare dashboard pages for API-backed data by adding explicit loading, empty, and error rendering states around aircraft lists.

Acceptance:

- Owner and maintenance dashboard states are visually coherent.
- Existing mock data path still renders.
- Lint/build pass.

Suggested checks:

```bash
cd frontend/paprnav-frontend
npm run lint
npm run build
```

### T010: Decide and scaffold database migrations

Status: superseded by T015 and T017

Goal: Choose a migration tool and add the minimal migration scaffolding for the backend.

Acceptance:

- Migration tool choice is recorded in `.ai/DECISIONS.md`.
- Backend has clear commands to create/apply migrations.
- No production schema is invented beyond the approved initial model.

### T011: Decide and scaffold file storage

Status: superseded by T026 and T027

Goal: Choose local and production object storage strategy for uploaded logbook files.

Acceptance:

- Storage decision is recorded.
- Local dev path is documented.
- Production path does not expose secrets in repo.

### T012: Add infrastructure planning document

Status: ready

Goal: Add `.ai/INFRASTRUCTURE.md` to define desired environments, AWS target account/region assumptions, deployment tool options, and secrets/state handling questions.

Acceptance:

- Explicitly states no AWS IaC currently exists.
- Lists recommended next decision points before deployment.
- Does not run AWS commands or modify cloud resources.

## MVP Completion Definition

The authoritative MVP definition is `.ai/MVP_COMPLETION.md`.

In short: the webapp is not complete until scanned logbooks can be uploaded, OCR processed, page-order/completeness verified, low-confidence OCR decoded by users, ingested into structured logbook records, compared against ingested FAA AD data, and routed through HITL adjudication when matching is uncertain.

## MVP Implementation Tasks

### T013: Decide MVP auth strategy

Status: completed 2026-06-16

Goal: Resolve P001 in `.ai/DECISIONS.md` with a concrete authentication approach for the MVP.

Acceptance:

- Records the chosen auth provider/session strategy in `.ai/DECISIONS.md`.
- Explains why it fits a small MVP.
- Lists follow-up implementation tasks that depend on the decision.
- Does not implement auth yet unless it is a tiny supporting proof.

Suggested checks:

```bash
sed -n '1,220p' .ai/DECISIONS.md
```

### T014: Decide API schema and client typing strategy

Status: completed 2026-06-16

Goal: Resolve P002 in `.ai/DECISIONS.md` so backend and frontend can integrate without ad hoc types.

Acceptance:

- Records how API request/response schemas are defined.
- Records how frontend TypeScript types stay aligned.
- Updates or creates `.ai/API_CONTRACT.md` if useful.

Suggested checks:

```bash
find .ai -maxdepth 1 -type f -name '*.md' -print
```

### T015: Decide database migration stack

Status: completed 2026-06-16

Goal: Resolve P004 in `.ai/DECISIONS.md`, likely by choosing SQLAlchemy plus Alembic unless there is a better local reason.

Acceptance:

- Records ORM/database access and migration choices.
- Adds implementation follow-up tasks if needed.
- Does not create tables unless the migration approach is also scaffolded cleanly.

Suggested checks:

```bash
sed -n '1,240p' .ai/DECISIONS.md
```

### T016: Scaffold backend settings and app structure

Status: completed 2026-06-17 via T016a

Goal: Refactor backend from a single placeholder file into a small FastAPI app structure with configuration, routers, and database module placeholders.

Implementation note:

- T016a created the app package, settings module, router structure, and database placeholders without adding domain tables.

Acceptance:

- Backend has a clear app package layout.
- Existing root, health, or version endpoints still work if already added.
- Settings include database URL and local development defaults.
- Python compile check passes.

Suggested checks:

```bash
cd backend
python -m py_compile main.py
```

### T017: Add initial database models and migrations

Status: completed 2026-06-17

Goal: Implement the first persisted schema for users, organizations, memberships/roles, aircraft, logbook sections, logbook entries, and upload metadata.

Implementation note:

- T017a added Alembic migration scaffolding and dependency declarations.
- T017b added SQLAlchemy models and an initial schema migration for users, organizations, memberships/roles, aircraft, aircraft assignments, logbook sections, logbook entries, and upload metadata.
- Docker support was added for the backend API, Postgres, and one-shot migration runs.

Acceptance:

- Migrations create the MVP tables.
- Models include timestamps and stable identifiers.
- N-number normalization is represented.
- Migration apply command is documented.
- Does not include AD rule automation unless separately designed.

Suggested checks:

```bash
cd backend
python -m py_compile main.py
```

### T018: Seed local development data

Status: completed 2026-06-17

Goal: Add a repeatable local seed process that creates an owner user, maintenance user, sample aircraft, and sample logbook entries.

Acceptance:

- Seed command is documented.
- Seed data matches frontend demo scenarios.
- Re-running the seed is safe or clearly documented.

Suggested checks:

```bash
cd backend
python -m py_compile main.py
```

### T019: Implement backend auth endpoints

Status: completed 2026-06-17

Goal: Add register, login, logout/session, and current-user endpoints based on the selected auth strategy.

Acceptance:

- Users can register and authenticate through API endpoints.
- Passwords/secrets are not stored in plaintext.
- Current user endpoint returns identity and role context.
- Critical auth paths have tests or documented manual verification.

Suggested checks:

```bash
cd backend
python -m py_compile main.py
```

### T020: Implement frontend auth integration

Status: completed 2026-06-17

Goal: Wire login/register UI to backend auth and protect authenticated app routes.

Implementation:

- Login and register forms call backend auth endpoints through a same-origin frontend API proxy.
- Authenticated app routes load the current backend session and redirect signed-out users to login.
- Header and mobile nav show the signed-in user and call backend logout.
- Removed the temporary dashboard bypass link.

Acceptance:

- Login form calls the API and handles success/failure.
- Register form calls the API and handles success/failure.
- Authenticated pages require a signed-in user.
- Sign-out flow exists.
- The dev dashboard bypass link is removed.

Suggested checks:

```bash
cd frontend/paprnav-frontend
npm run lint
npm run build
```

### T021: Implement aircraft API endpoints

Status: completed 2026-06-17

Goal: Add backend endpoints to list, create, view, and update aircraft visible to the authenticated user.

Implementation:

- Added authenticated `GET /api/v1/aircraft`, `POST /api/v1/aircraft`, `GET /api/v1/aircraft/{aircraftId}`, and `PATCH /api/v1/aircraft/{aircraftId}` endpoints.
- Owner organization members can create, view, and update owned aircraft.
- Maintenance organization members can view assigned client aircraft through `aircraft_assignments` but cannot update owner records.
- No-organization users receive an empty aircraft list.

Acceptance:

- Owner users can create and view their aircraft.
- Maintenance users can view assigned client aircraft.
- API enforces role/ownership boundaries.
- Responses match the API contract.

Suggested checks:

```bash
cd backend
python -m py_compile main.py
curl -b /tmp/paprnav-owner.cookies http://127.0.0.1:8000/api/v1/aircraft
```

### T022: Replace dashboard mock data with aircraft API data

Status: completed 2026-06-17

Goal: Update `/logbook` so owner and maintenance dashboard views use API-backed aircraft data.

Implementation:

- Replaced inline dashboard aircraft/client arrays with `GET /api/v1/aircraft`.
- Added typed frontend API client models for auth and aircraft responses.
- Added loading, retryable error, and empty states.
- Dashboard defaults to maintenance view for users with only maintenance memberships.

Acceptance:

- Inline aircraft arrays are removed from the dashboard page.
- Loading, empty, and error states are visible.
- Owner and maintenance role views still work.
- Lint/build pass.

Suggested checks:

```bash
cd frontend/paprnav-frontend
npm run lint
npm run build
```

### T023: Implement logbook entry API endpoints

Status: completed 2026-06-17

Goal: Add backend endpoints to list, create, view, and update logbook entries by aircraft and logbook section.

Implementation:

- Added authenticated `GET /api/v1/aircraft/{aircraftId}/logbook-entries`, `POST /api/v1/aircraft/{aircraftId}/logbook-entries`, `GET /api/v1/aircraft/{aircraftId}/logbook-entries/{entryId}`, and `PATCH /api/v1/aircraft/{aircraftId}/logbook-entries/{entryId}` endpoints.
- Supports `airframe`, `engine`, and `propeller` sections.
- Owners and assigned maintenance users can create and update manual entries for visible aircraft.
- Unrelated users receive `404` for aircraft they cannot access.

Acceptance:

- Supports airframe, engine, and propeller sections.
- Manual entries can be created.
- Entry detail can be fetched by ID.
- Authorization checks prevent cross-aircraft access.
- Responses match the API contract.

Suggested checks:

```bash
cd backend
python -m py_compile main.py
curl -b /tmp/paprnav-owner-t023.cookies http://127.0.0.1:8000/api/v1/aircraft/{aircraftId}/logbook-entries
```

### T024: Replace logbook detail mock data with API data

Status: completed 2026-06-17

Goal: Update `/logbook/[nNumber]` and `/logbook/[nNumber]/entry/[entryId]` to use backend logbook entry APIs.

Implementation:

- Replaced inline dummy logbook entries in `/logbook/[nNumber]` with `GET /api/v1/aircraft/{aircraftId}/logbook-entries?section=...`.
- Entry links now use real backend logbook entry IDs.
- `/logbook/[nNumber]/entry/[entryId]` resolves visible aircraft by N-number and loads the entry from the backend API.
- Entry detail save now calls the backend `PATCH` endpoint instead of simulating a save.
- Added loading, empty, retryable error, and not-found states.

Acceptance:

- Inline dummy logbook entries are removed.
- Logbook tabs load API data by section.
- Entry detail page renders API data.
- Loading, empty, and error states are handled.
- Lint/build pass.

Suggested checks:

```bash
cd frontend/paprnav-frontend
npm run lint
npm run build
```

### T025: Build manual logbook entry form

Status: completed 2026-06-17

Goal: Add a real manual-entry workflow separate from upload, or mode-switch the existing add/upload page clearly.

Implementation:

- Added `/logbook/[nNumber]/new?logbook=...` as a dedicated manual-entry workflow.
- Form captures date, section, description, performer, credential, notes, tach, Hobbs, and total time.
- Required date and description validation prevents empty submissions.
- Successful submission calls `POST /api/v1/aircraft/{aircraftId}/logbook-entries` and redirects to the created entry detail page.
- Logbook list and maintenance row "add" actions now route to the manual-entry workflow; scanned upload actions remain separate.

Acceptance:

- User can enter date, section, description, performer, credentials, and notes.
- Form validates required fields.
- Successful submission persists through the API and returns to the entry list/detail.
- Lint/build pass.

Suggested checks:

```bash
cd frontend/paprnav-frontend
npm run lint
npm run build
```

### T026: Decide file storage target for MVP

Status: completed 2026-06-16

Goal: Resolve P003 in `.ai/DECISIONS.md` with local development and production storage targets.

Acceptance:

- Records local file storage behavior.
- Records production storage target, likely S3 if AWS remains the plan.
- States secret handling and maximum upload assumptions.
- Adds infrastructure follow-up tasks if production storage requires them.

Suggested checks:

```bash
sed -n '1,260p' .ai/DECISIONS.md
```

### T027: Implement backend upload API

Status: completed 2026-06-17

Goal: Add backend support for uploading PDF/JPG/PNG logbook files and creating upload metadata linked to an aircraft/logbook entry.

Implementation:

- Added authenticated `POST /api/v1/aircraft/{aircraftId}/uploads` for multipart PDF/JPG/PNG uploads.
- Added authenticated `GET /api/v1/uploads/{uploadId}/download` for retrieving stored originals.
- Local development stores files under configurable `PAPRNAV_LOCAL_STORAGE_PATH`, defaulting to `.data`.
- Upload responses expose metadata and a `downloadUrl` without leaking local filesystem paths.
- Upload metadata persists to Postgres with storage backend, storage key, file size, content type, SHA-256 hash, and status.

Acceptance:

- Validates file type and size server-side.
- Stores original file using the selected storage strategy.
- Persists upload metadata.
- Provides a way to retrieve/download the file.
- Authorization prevents cross-aircraft access.

Suggested checks:

```bash
cd backend
python -m py_compile main.py
```

### T028: Wire frontend upload page to backend upload API

Status: completed 2026-06-17

Goal: Replace simulated upload success with a real API call.

Implementation:

- Upload page resolves visible aircraft by N-number and submits selected file to `POST /api/v1/aircraft/{aircraftId}/uploads` through the frontend same-origin proxy.
- Pending, success, and error states now reflect backend responses.
- Success state links back to the relevant logbook section and exposes the authorized download URL through the proxy.
- Upload size copy now matches the backend default `100 MB` limit.

Acceptance:

- Upload page submits selected file to the backend.
- Progress/pending/success/error states remain clear.
- Success links or routes the user back to the relevant entry/logbook context.
- Lint/build pass.

Suggested checks:

```bash
cd frontend/paprnav-frontend
npm run lint
npm run build
```

### T029: Implement profile API and frontend persistence

Status: completed 2026-06-18

Goal: Make profile/account screens display and update authenticated user data from the backend.

Architecture decision:

- Current-user profile editing stays under the existing FastAPI-owned auth/session boundary for the MVP.
- `PATCH /api/v1/auth/profile` updates the authenticated user's display name only; email remains read-only until email verification and account recovery are defined.

Implementation:

- Added `PATCH /api/v1/auth/profile`.
- Added frontend API typing and profile page persistence.
- Profile now shows current user email and active organization memberships from the backend.
- Removed the fake password-change form and replaced it with an honest security status card.
- Added backend endpoint coverage proving profile changes persist through `GET /api/v1/auth/me`.

Acceptance:

- Profile page reads current-user/profile API data.
- Editable fields persist through the backend.
- Error and success states are handled.
- Lint/build and backend compile checks pass.

Suggested checks:

```bash
cd frontend/paprnav-frontend
npm run lint
npm run build
cd ../../backend
python -m py_compile main.py
```

### T030: Implement role and organization assignment workflow

Status: completed 2026-06-18

Goal: Add the minimal workflow needed to associate maintenance-shop users with client aircraft.

Architecture decision:

- MVP aircraft access assignment is owner-managed and organization-scoped.
- Owners assign an aircraft by entering an existing maintenance user's email; the backend resolves that user's active maintenance organization and creates or reactivates an aircraft assignment.
- Invite flows, new maintenance account provisioning, revocation UI, and fine-grained per-user aircraft permissions are deferred until the role model needs them.

Implementation:

- Added owner-only `GET /api/v1/aircraft/{aircraftId}/assignments`.
- Added owner-only `POST /api/v1/aircraft/{aircraftId}/assignments`.
- Assignment creation enforces owner access and requires the target user to belong to an active maintenance organization.
- Aircraft detail page now has a maintenance access panel for owner users.
- Backend tests prove assigned maintenance users can see client aircraft and cannot manage assignments.

Acceptance:

- Role model is enforced in backend.
- Maintenance user can see assigned client aircraft.
- Owner-only aircraft are not exposed to unrelated users.
- The UI has a practical way to represent assignments for MVP.

Suggested checks:

```bash
cd backend
python -m py_compile main.py
cd ../frontend/paprnav-frontend
npm run lint
```

### T031: Add backend endpoint tests for MVP flows

Status: completed 2026-06-17

Goal: Add automated tests for auth, aircraft, logbook entry, and upload metadata behaviors.

Implementation:

- Added pytest-based backend endpoint tests using FastAPI `TestClient`.
- Added an isolated SQLite test database fixture with dependency-overridden sessions.
- Covered auth register/me/logout, aircraft visibility, logbook entry create/list/update/read, upload create/download validation, and unauthorized access boundaries.
- Added a small session-expiry timezone guard so tests and lightweight SQLite-backed runs handle naive datetimes safely.

Acceptance:

- Tests cover happy paths and at least one unauthorized access case per protected domain.
- Test database setup is documented.
- Tests run locally with a documented command.

Suggested checks:

```bash
cd backend
docker compose exec -T api python -m pytest
```

### T032: Add frontend smoke tests or interaction checks

Status: completed 2026-06-18

Goal: Add practical frontend checks for login, dashboard, logbook detail, manual entry, and upload flows.

Architecture decision:

- The first frontend smoke check is an HTTP-level local smoke script rather than a browser automation suite.
- It uses the Next.js same-origin backend proxy so it validates the browser-facing integration path without adding Playwright/Cypress dependencies before CI is in place.
- Full browser interaction coverage remains a future upgrade once the core OCR workflow stabilizes.

Implementation:

- Added `npm run smoke`.
- Smoke script checks critical routes and performs login plus manual logbook entry creation through `/api/backend`.
- Frontend README documents the smoke-test assumptions and environment overrides.

Acceptance:

- Test approach is documented.
- Critical routes render without crashing.
- At least one form workflow is exercised.
- Lint/build pass.

Suggested checks:

```bash
cd frontend/paprnav-frontend
npm run lint
npm run build
```

## Human Product Observability Tasks

These tasks add human-visible product observability: demo/support timelines, user feedback, workflow state evidence, and lightweight admin/reviewer visibility. This is not a substitute for infrastructure logs or cloud monitoring.

### T055: Add product observability data model and migration

Status: completed 2026-06-19

Goal: Add persisted models for product events, user feedback, and workflow status events based on `.ai/DATA_MODEL.md`.

Acceptance:

- Models store product events without raw logbook text, secrets, or uploaded file contents.
- User feedback can link to aircraft, uploads, ingestion jobs, OCR corrections, AD review tasks, or compliance worklist items.
- Workflow status events can represent upload, OCR, AD ingestion, AD extraction, matching, and adjudication state transitions.
- Migration applies locally and is documented.

Suggested checks:

```bash
cd backend
python -m py_compile main.py
```

Evidence:

- Added `ProductEvent`, `UserFeedback`, and `WorkflowStatusEvent` models.
- Added migration `20260619_0006_add_observability_and_adjudication.py`.
- Event properties are sanitized by `backend/app/services/observability.py`.
- Feedback can link to aircraft and workflow subjects.

### T056: Add backend product observability capture helpers

Status: completed 2026-06-19

Goal: Add a backend service/helper for recording product events and workflow status transitions from API routes and workers.

Acceptance:

- Helper accepts actor, event type, subject, safe properties, and request/session context.
- Helper redacts or rejects sensitive fields.
- Existing health/version routes remain unchanged.
- Backend compile check passes.

Suggested checks:

```bash
cd backend
python -m py_compile main.py
```

Evidence:

- Added `record_product_event`, `record_workflow_status`, and `sanitize_properties` helpers.
- Sensitive keys such as password, token, secret, raw text, OCR text, and file content are stripped before persistence.
- Health/version routes remain unchanged.

### T057: Instrument core MVP workflow events

Status: completed 2026-06-19

Goal: Record product events for auth, aircraft creation, logbook entry creation, upload, ingestion job creation/status changes, page verification, OCR correction, and AD review actions as those workflows become available.

Acceptance:

- Key user and worker actions write product events.
- Long-running workflow status changes write workflow status events.
- Events include enough IDs and statuses to reconstruct demo/support timelines.
- Events avoid raw uploaded content, OCR text payloads, passwords, and secrets.

Suggested checks:

```bash
cd backend
python -m py_compile main.py
```

Evidence:

- Instrumented auth registration/login/profile update, aircraft creation/assignment, logbook entry creation, upload/ingestion job creation, page verification, OCR correction, logbook extraction, AD extraction review decisions, AD discovery, AD extraction, AD matching, and HITL adjudication.
- Worker events use `event_source=worker`.
- Events store IDs, statuses, counts, confidence/status summaries, and avoid raw uploaded/OCR/logbook text payloads.

### T058: Build internal product observability view

Status: completed 2026-06-19

Goal: Add a lightweight authenticated internal/admin view for recent product events, workflow timelines, and user feedback.

Acceptance:

- Internal user can filter by aircraft, upload, ingestion job, user, event type, and status.
- Workflow timeline makes demo/support state understandable to a human.
- User feedback can be created and triaged.
- No raw uploaded file content, secrets, or full OCR text are shown in the event stream.
- Lint/build and backend compile checks pass.

Suggested checks:

```bash
cd frontend/paprnav-frontend
npm run lint
npm run build
cd ../../backend
python -m py_compile main.py
```

Evidence:

- Added `/api/v1/observability` list endpoint with filters for aircraft, user, event type, subject type, status, and workflow id.
- Added feedback create and triage endpoints.
- Added authenticated frontend page `/observability` with filters, workflow timeline, product event stream, and feedback capture/triage.
- Added desktop and mobile navigation links.

### T033: Add environment variable documentation and examples

Status: completed 2026-06-18

Goal: Document required frontend/backend environment variables and add safe example files if appropriate.

Architecture decision:

- Local examples are committed as `.env.example` files only.
- Real `.env` and `.env.local` files remain ignored.
- Future AWS secrets are documented as managed secret inputs, not committed placeholders.

Implementation:

- Added `backend/.env.example`.
- Added `frontend/paprnav-frontend/.env.example`.
- Added `.ai/ENVIRONMENT.md`.
- Updated root and AI handoff docs to point at the environment guide.

Acceptance:

- No real secrets are committed.
- Frontend and backend env vars are documented.
- Local dev setup is reproducible from docs.

Suggested checks:

```bash
find . -name '.env*' -maxdepth 4 -print
```

### T034: Create production infrastructure as code

Status: blocked pending T012, T026, and environment decisions

Goal: Add reviewable IaC for the selected AWS production architecture.

Acceptance:

- Current official docs for selected AWS services and deployment tooling are checked and recorded in `.ai/PROVIDER_REFERENCES.md` before implementation.
- IaC defines frontend hosting, backend hosting, database, storage, networking, secrets, and logs as needed for MVP.
- State handling and target AWS account/region are documented.
- Plan/diff command is documented.
- Does not apply cloud changes without explicit approval.

### T035: Add CI workflow

Status: blocked pending GitHub credential with `workflow` scope

Goal: Add GitHub Actions workflows for frontend lint/build and backend tests.

Architecture decision:

- CI is verification-only at this stage.
- Backend tests run against the SQLite test fixtures and require no Postgres or AWS services.
- No deployment secrets, AWS credentials, or production actions are required for the first CI gate.

Blocked note:

- A local `.github/workflows/ci.yml` draft exists, but GitHub rejected the push because the current OAuth credential cannot create or update workflow files without `workflow` scope.
- Do not mark this task complete until the workflow file is committed and pushed with a credential that has the required scope.

Acceptance:

- Workflow runs on pull requests and main branch pushes.
- Frontend lint/build is included.
- Backend tests are included once available.
- No deployment secrets are required for basic checks.

### T036: Production deployment dry run

Status: blocked pending T034 and T035

Goal: Execute a non-destructive deployment plan/diff and document the exact deployment steps.

Acceptance:

- Plan/diff output is reviewed.
- Required secrets and AWS permissions are listed.
- Rollback steps are documented.
- No infrastructure is applied unless explicitly approved.

### T037: MVP release audit

Status: blocked pending OCR, AD ingestion, matching, HITL, tests, and deployment tasks

Goal: Audit the app against the MVP Completion Definition and close remaining gaps.

Acceptance:

- Every item in the MVP Completion Definition is verified with file evidence, test output, or manual runtime evidence.
- `.ai/GOAL_TASKS.md` is updated with completed/remaining tasks.
- Known risks are documented.

## OCR, AD, And HITL MVP Tasks

### T038: Design OCR ingestion data model

Status: completed 2026-06-16

Goal: Extend the data model design for upload batches, pages, OCR text spans, bounding boxes, confidence scores, page-order verification, completeness confirmation, and HITL OCR corrections.

Acceptance:

- `.ai/DATA_MODEL.md` or equivalent includes OCR ingestion entities and relationships.
- Defines traceability from structured logbook entry back to upload, page, OCR span, and correction.
- Identifies required fields for audit and user correction.
- Does not implement tables unless paired with a migration task.

Suggested checks:

```bash
find .ai -maxdepth 1 -type f -name '*.md' -print
```

### T039: Decide OCR provider and abstraction

Status: completed 2026-06-16

Goal: Resolve P006 in `.ai/DECISIONS.md` with the MVP OCR provider strategy.

Acceptance:

- Records selected OCR provider or provider abstraction.
- Explains local dev behavior and production behavior.
- Lists confidence data required from OCR output.
- Adds follow-up implementation tasks if provider choice changes the roadmap.

Suggested checks:

```bash
sed -n '1,280p' .ai/DECISIONS.md
```

### T040: Implement upload ingestion job API

Status: completed 2026-06-18

Goal: Change upload handling from "store a file" to "create an ingestion job" with upload status, page extraction status, OCR status, verification status, and error states.

Architecture decision:

- Upload remains the immutable original-file record.
- Each upload now creates a separate ingestion job that owns processing state and downstream OCR/HITL workflow.
- The upload response includes the queued ingestion job so the frontend can route directly to review/status UI.

Implementation:

- Added OCR ingestion persistence models and Alembic migration.
- Upload API creates an ingestion job tied to upload, aircraft, user, and optional logbook section hint.
- Added `GET /api/v1/ingestion-jobs/{jobId}` for status and page/span detail.
- Original upload download behavior remains unchanged.

Acceptance:

- Backend creates ingestion jobs tied to aircraft and user.
- Job status can be queried.
- Original upload remains retrievable.
- API response supports frontend progress/status UI.

Suggested checks:

```bash
cd backend
python -m py_compile main.py
```

### T041: Implement OCR processing worker skeleton

Status: completed 2026-06-18

Goal: Add a backend worker/service entrypoint that can process an ingestion job into pages and OCR records through the chosen OCR abstraction.

Architecture decision:

- The first local OCR provider is deterministic and fixture-backed.
- Provider-neutral storage uses Textract-compatible `0-100` confidence and explicit geometry units, with provider block IDs and relationships preserved where available.
- The worker is a local Python entrypoint that can later be replaced or wrapped by queue processing.

Implementation:

- Added deterministic OCR provider abstraction and fixture provider.
- Added `python -m app.workers.ocr`.
- Worker persists ingestion pages, OCR runs, and OCR spans with confidence, bounding boxes, provider IDs, and reading order.
- Worker failures set job failure state.

Acceptance:

- Current official Textract docs and any selected local OCR adapter docs are checked and recorded in `.ai/PROVIDER_REFERENCES.md`.
- Provider-neutral OCR schema maps explicitly to source provider fields, including confidence scale, geometry units, page numbers, IDs, and relationships.
- Worker can be run locally.
- OCR provider interface is explicit.
- Stub or real provider persists page/text/confidence records.
- Failures are recorded on the ingestion job.

Suggested checks:

```bash
cd backend
python -m py_compile main.py
```

### T042: Build page-order and completeness verification UI

Status: completed 2026-06-18

Goal: Add UI for users to review uploaded pages, reorder pages if needed, and confirm whether the logbook upload is complete.

Architecture decision:

- Page review is part of the aircraft logbook workflow at `/logbook/{nNumber}/ingestion/{jobId}`.
- The first UI shows page placeholders and order controls from API data; rendered page images can replace placeholders later without changing the API contract.

Implementation:

- Added OCR review page.
- Added page-order controls and completeness/notes submission.
- Backend persists page verification and updates ingestion job status.

Acceptance:

- Shows upload pages or page placeholders from API data.
- User can set/confirm page order.
- User can confirm completeness or mark missing/uncertain pages.
- Verification state persists through the backend.
- Lint/build pass.

Suggested checks:

```bash
cd frontend/paprnav-frontend
npm run lint
npm run build
```

### T043: Build low-confidence OCR correction workflow

Status: completed 2026-06-18

Goal: Present low-confidence OCR regions as highlighted snippets with focused correction fields.

Architecture decision:

- Low-confidence correction is span-based and preserves original OCR text.
- Corrections are additive records; OCR text is not overwritten.

Implementation:

- OCR review page lists spans below the confidence threshold.
- User can submit corrected text.
- Backend stores original text, corrected text, confidence, reason, user, and timestamp.

Acceptance:

- UI shows OCR snippet context and source page region reference.
- User can submit corrected text.
- Corrections persist as HITL annotations.
- Backend records original OCR text, corrected text, confidence, user, and timestamp.
- Lint/build and backend compile checks pass.

Suggested checks:

```bash
cd frontend/paprnav-frontend
npm run lint
npm run build
cd ../../backend
python -m py_compile main.py
```

### T044: Implement structured logbook ingestion from verified OCR

Status: completed 2026-06-18

Goal: Convert verified OCR text plus corrections into structured logbook entries.

Architecture decision:

- The first extractor is deterministic and conservative.
- It only runs after page verification and stores evidence links back to upload/page/span/correction records.
- Low-confidence source material creates `needs_review` entries rather than silently treating extraction as final.

Implementation:

- Added `POST /api/v1/ingestion-jobs/{jobId}/extract-logbook-entries`.
- Deterministic extractor parses date, description, performer, credential, and time fields from fixture OCR lines.
- Created logbook entries use `source_type=ocr_ingestion`.
- Added logbook entry evidence persistence with extraction provider metadata.

Acceptance:

- Creates logbook entries with date, section, description, performer, credential, times when available, and source evidence links.
- Ambiguous fields are marked for review rather than silently guessed.
- Structured entries can be viewed through existing logbook APIs/pages.
- Extraction provider/version metadata is persisted.

Suggested checks:

```bash
cd backend
python -m py_compile main.py
```

### T045: Rewrite AD ingestion spec for MVP architecture

Status: completed 2026-06-16

Goal: Create `.ai/AD_INGESTION_MVP_SPEC.md` using `.ai/AD_INGESTION_REVIEW.md` and the legacy `ad-ingestion-spec.md`.

Acceptance:

- Specifies Federal Register discovery, AD classification, persistence, extraction, supersession, and review.
- Uses Postgres plus object storage abstraction for MVP.
- Marks DynamoDB/OpenSearch/EventBridge/SQS/Lambda as optional future production architecture.
- Explicitly recommends retaining AD data with content-hash de-duplication and lifecycle policies.

Suggested checks:

```bash
find .ai -maxdepth 1 -type f -name '*AD*' -print
```

### T046: Implement Federal Register AD discovery prototype

Status: completed 2026-06-18

Goal: Add a backend script or worker that queries the Federal Register API and classifies FAA rules as AD candidates.

Acceptance:

- Current official Federal Register API docs are checked and recorded in `.ai/PROVIDER_REFERENCES.md`.
- API query parameters, pagination/limits, source URLs, publication dates, document numbers, and raw response retention are mapped before implementation.
- Uses Federal Register API as primary source.
- Does not assume every FAA Rule is an AD.
- Stores discovery metadata and candidate/rejected classification.
- Can run locally without applying AWS changes.

Suggested checks:

```bash
cd backend
python -m py_compile main.py
```

Evidence:

- Official Federal Register API docs checked and recorded in `.ai/PROVIDER_REFERENCES.md`.
- Implemented `backend/app/services/ad_discovery.py` and `backend/app/workers/ad_discovery.py`.
- Discovery persists raw Federal Register result snapshots, source URLs, publication dates, document numbers, content hashes, and AD/non-AD classification.
- Backend test covers one AD candidate and one non-AD FAA rule fixture.
- Live Docker worker run: `ad_discovery seen=20 candidates=20 rejected=0`.

### T047: Implement AD persistence and supersession model

Status: completed 2026-06-18

Goal: Add database support for AD source records, extracted structured data, applicability, compliance requirements, source snapshots, confidence, and supersession relationships.

Acceptance:

- AD records persist in Postgres.
- Supersedes/superseded-by can be represented as graph relationships.
- Source metadata includes Federal Register document number, URLs, publication date, and content hash.
- Low-confidence extraction can be queued for review.

Suggested checks:

```bash
cd backend
python -m py_compile main.py
```

Evidence:

- Added SQLAlchemy models for `ADDiscoveryRecord`, `AirworthinessDirective`, `ADExtraction`, `ADExtractionReview`, and `ADSupersession`.
- Added Alembic migration `20260618_0004_add_ad_ingestion.py`.
- Docker Postgres upgraded from `20260618_0003` to `20260618_0004`.
- Local database after live worker run: 20 discovery records, 20 directives, 13 pending reviews.
- Data model documented in `.ai/DATA_MODEL.md`.

### T048: Decide AD extraction provider

Status: completed 2026-06-16

Goal: Resolve P007 in `.ai/DECISIONS.md`.

Acceptance:

- Records deterministic parsing, LLM extraction, or hybrid extraction strategy.
- Defines provider/version/prompt/hash metadata that must be persisted.
- Defines confidence thresholds for review routing.

Suggested checks:

```bash
sed -n '1,320p' .ai/DECISIONS.md
```

### T049: Implement structured AD extraction worker

Status: completed 2026-06-18

Goal: Extract applicability, compliance actions, intervals, effective date, and supersession clues from AD source records.

Acceptance:

- Current extraction provider docs are checked and recorded in `.ai/PROVIDER_REFERENCES.md` before provider-backed behavior is implemented.
- Provider request/response shape, model/version metadata, structured output validation, confidence/uncertainty behavior, citations, and retry/idempotency expectations are mapped.
- Extraction output validates against a schema.
- Low-confidence outputs route to AD extraction review.
- Provider/version metadata is persisted.
- Extraction can be re-run idempotently by content hash.

Suggested checks:

```bash
cd backend
python -m py_compile main.py
```

Evidence:

- Implemented `backend/app/services/ad_extraction.py` and `backend/app/workers/ad_extraction.py`.
- Extraction persists provider name/version, schema version, input content hash, confidence, citations, raw response metadata, and structured output.
- Extraction validates required schema keys before persistence/review approval.
- Idempotency enforced by directive, input content hash, provider name, provider version, and schema version.
- Live Docker worker run: `ad_extraction seen=20 extracted=20 review_queued=13`.

### T050: Build AD extraction review queue

Status: completed 2026-06-18

Goal: Add backend and frontend review flow for low-confidence AD extraction results.

Acceptance:

- Reviewer can inspect source text/PDF link and proposed extraction.
- Reviewer can accept, edit, or reject extracted fields.
- Review decisions are audited.
- Approved extraction becomes available for matching.

Suggested checks:

```bash
cd frontend/paprnav-frontend
npm run lint
npm run build
cd ../../backend
python -m py_compile main.py
```

Evidence:

- Added protected AD review API routes under `/api/v1/ads`.
- Added frontend review page at `/logbook/ads`.
- Reviewers can inspect source text plus Federal Register/govinfo links, edit structured JSON, approve, save edits, or reject.
- Review decisions persist reviewer, decision, decision output, notes, and reviewed timestamp.
- Approved/edited reviews mark extraction approved and directive review status approved for future matching.
- Browser verification rendered `/logbook/ads` with 13 pending AD extraction reviews and approve/edit/reject controls.

### T051: Design AD-to-logbook matching rules

Status: completed 2026-06-18

Goal: Create a matching design for one-time, recurring/cyclical, conditional, component-specific, and superseded ADs.

Acceptance:

- Documents matching inputs, outputs, confidence, and unresolved reasons.
- Defines how candidate logbook entries are cited.
- Defines when HITL adjudication is required.
- Does not claim official compliance attestation.

Suggested checks:

```bash
find .ai -maxdepth 1 -type f -name '*.md' -print
```

Evidence:

- Added `.ai/AD_MATCHING_RULES.md`.
- Documents inputs, outputs, statuses, match types, confidence, candidate logbook entry citation, HITL adjudication triggers, supersession handling, and the non-attestation boundary.
- Defines current matcher as `deterministic_ad_logbook_matcher` version `0.1.0`.

### T052: Implement first-pass AD-to-logbook matcher

Status: completed 2026-06-18

Goal: Add backend matching job that compares applicable ADs against structured logbook entries and produces candidate match/unresolved records.

Acceptance:

- Handles at least one-time ADs and simple recurring ADs.
- Superseded ADs do not appear as currently required unless history is explicitly requested.
- Uncertain/conditional cases create HITL adjudication tasks.
- Matcher output includes evidence and rationale.

Suggested checks:

```bash
cd backend
python -m py_compile main.py
```

Evidence:

- Added `ADMatchResult`, `ADMatchEvidence`, and `ADMatchAdjudication` models plus migration `20260618_0005_add_ad_matching.py`.
- Implemented matcher service and worker in `backend/app/services/ad_matching.py` and `backend/app/workers/ad_matching.py`.
- Matcher handles one-time and simple recurring AD extraction output, cites candidate logbook entries, skips non-applicable products, and creates pending adjudication for unresolved cases.
- Added `GET /api/v1/ads/aircraft/{aircraft_id}/matches`.
- Added aircraft logbook AD Matching panel in the frontend.
- Backend test `tests/test_ad_matching.py` proves one-time match evidence, simple recurring match evidence, unresolved adjudication, and API response shape.

### T053: Build HITL AD adjudication workflow

Status: completed 2026-06-19

Goal: Add UI and API for humans to adjudicate unresolved AD/logbook matches.

Acceptance:

- Reviewer sees AD, aircraft/component facts, candidate logbook entries, and system rationale.
- Reviewer can mark satisfied, not satisfied, not applicable, needs more info, or defer.
- Decision stores reviewer, notes, timestamp, and future-improvement tags.
- Decisions are visible to software/admin review.

Suggested checks:

```bash
cd frontend/paprnav-frontend
npm run lint
npm run build
cd ../../backend
python -m py_compile main.py
```

Evidence:

- Added `POST /api/v1/ads/matches/{match_id}/adjudication`.
- Reviewer can mark satisfied, not satisfied, not applicable, needs more info, or deferred.
- Decision stores reviewer, notes, timestamp, and future-improvement tags.
- Aircraft logbook AD Compliance Worklist shows AD, aircraft facts, candidate logbook evidence, system rationale, source links, unresolved reasons, and reviewer controls.
- Backend test covers adjudication decision persistence and event recording.

### T054: Build aircraft compliance worklist

Status: completed 2026-06-19

Goal: Replace simple compliance status badges with an evidence-backed worklist of AD candidates, matched items, unresolved items, and HITL decisions.

Acceptance:

- User can see AD status by aircraft.
- Each item links to source AD evidence and logbook evidence where available.
- Unresolved items clearly ask for review rather than implying compliance.
- Lint/build pass.

Suggested checks:

```bash
cd frontend/paprnav-frontend
npm run lint
npm run build
```

Evidence:

- Aircraft logbook page now renders an evidence-backed AD Compliance Worklist instead of a simple status-only view.
- Each item links to Federal Register/source PDF evidence and logbook entry evidence when available.
- Unresolved items show review controls and unresolved reasons instead of implying compliance.
- Human decisions render after adjudication.
