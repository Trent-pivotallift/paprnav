# paprnav Decisions

Last updated: 2026-06-18

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
