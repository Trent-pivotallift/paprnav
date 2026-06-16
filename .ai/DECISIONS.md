# paprnav Decisions

Last updated: 2026-06-16

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

Status: proposed

Recommendation: keep structured AD data indefinitely and retain raw/source artifacts or source snapshots with content-hash de-duplication and lifecycle policies for bulky files. Re-fetching later should be a fallback, not the primary audit strategy, because matching must be reproducible and supersession/HITL decisions require citations.

## Proposed Decisions To Resolve Soon

### P001: Authentication provider

Options include custom JWT/session auth in FastAPI, managed auth such as Cognito, or a frontend-friendly provider. This should be decided before implementing persistent user-specific workflows.

### P002: API boundary and schema format

Decide whether the backend owns OpenAPI-generated client types, hand-written TypeScript interfaces, or a shared schema process.

### P003: File storage target

Decide where uploaded PDFs/images live in production. Likely candidates are S3 or equivalent object storage. This decision affects backend upload API, security, and infrastructure.

### P004: Migration tool

Pick a backend migration workflow before adding database tables. Alembic is the likely default for FastAPI plus SQLAlchemy.

### P005: Monorepo layout

Decide whether to make the project root a Git repo containing both frontend and backend, or keep the nested frontend repo and manage backend separately.

### P006: OCR provider

Decide whether MVP OCR uses a local/open-source OCR engine, AWS Textract, another managed OCR provider, or a pluggable abstraction with one default provider.

### P007: AD extraction provider

Decide whether structured AD extraction starts with deterministic parsing plus LLM review, managed LLM extraction, or a provider abstraction with persisted provider/version metadata.
