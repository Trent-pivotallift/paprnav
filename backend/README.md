# paprnav Backend

This directory contains the early FastAPI backend for paprnav. It supports the current local MVP API surface for auth, aircraft, logbook entries, file uploads, deterministic OCR ingestion, OCR-to-logbook extraction, Federal Register AD ingestion, first-pass AD matching, HITL adjudication, and product observability.

## Current Status

- Uvicorn entrypoint: `main.py`
- FastAPI app factory: `app/main.py`
- Routers: `app/api`
- Settings: `app/core/config.py`
- Database setup: `app/db`
- Alembic migration scaffold: `alembic.ini` and `app/db/migrations`
- Docker app image: `Dockerfile`
- Local database service: Postgres 16 via `docker-compose.yml`
- Implemented API surface:
  - `GET /` returns a placeholder welcome message.
  - `GET /health` returns a stable health response for local checks and future probes.
  - `GET /version` returns the app name and version.
  - `/api/v1/auth/*` provides local cookie-backed auth/session endpoints.
  - `/api/v1/aircraft/*` provides authenticated aircraft endpoints.
  - `/api/v1/aircraft/{aircraftId}/assignments` provides owner-managed maintenance organization assignment endpoints.
  - `/api/v1/aircraft/{aircraftId}/logbook-entries/*` provides authenticated logbook entry endpoints.
  - `/api/v1/aircraft/{aircraftId}/uploads` stores uploaded PDF/JPG/PNG files and metadata.
  - `/api/v1/uploads/{uploadId}/download` retrieves stored original uploads for authorized users.
  - `/api/v1/ingestion-jobs/*` provides OCR ingestion status, page verification, correction, and structured entry extraction endpoints.

## Setup

Use a Python virtual environment from this directory:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run The API

```bash
uvicorn main:app --reload
```

The API will be available at `http://127.0.0.1:8000` by default.

Useful local checks:

```bash
curl http://127.0.0.1:8000/
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/version
```

FastAPI also exposes interactive API docs locally:

```text
http://127.0.0.1:8000/docs
```

## Docker

```bash
docker compose up db
```

The compose file starts a local Postgres database with development credentials:

- Database: `paprnav_db`
- User: `paprnav_user`
- Password: `paprnav_password`
- Port: `5432`

These credentials are local-only defaults. Do not reuse them for production.

Run the backend API and database together:

```bash
docker compose up api
```

Apply database migrations through Docker:

```bash
docker compose run --rm migrate
```

Seed repeatable local demo data:

```bash
docker compose run --rm seed
```

Process queued OCR ingestion jobs locally:

```bash
docker compose exec -T api python -m app.workers.ocr
```

Seeded demo users use the local-only password `demo-password`.

The API container uses `DATABASE_URL=postgresql+psycopg://paprnav_user:paprnav_password@db:5432/paprnav_db` so it connects to the compose database service rather than `localhost`.

## Environment

The backend currently works without required environment variables.

Optional local database configuration:

```bash
DATABASE_URL=postgresql+psycopg://paprnav_user:paprnav_password@localhost:5432/paprnav_db
```

Optional local CORS configuration:

```bash
PAPRNAV_CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

If `PAPRNAV_CORS_ORIGINS` is not set, the API allows the local Next.js development origins above.

Optional local upload storage configuration:

```bash
PAPRNAV_LOCAL_STORAGE_PATH=.data
PAPRNAV_STORAGE_BACKEND=local
PAPRNAV_MAX_UPLOAD_SIZE_BYTES=104857600
```

Local uploaded files are stored under `.data/`, which is ignored by git.

Optional S3 upload storage configuration:

```bash
PAPRNAV_STORAGE_BACKEND=s3
PAPRNAV_S3_UPLOAD_BUCKET=paprnav-pilot-artifacts-527257972989
PAPRNAV_S3_UPLOAD_PREFIX=uploads
AWS_REGION=us-east-1
```

S3-backed uploads are written with `AES256` server-side encryption and non-sensitive paprnav object metadata tags, including customer account, aircraft, upload, and billing stage tags. These object tags are for paprnav metadata/reconciliation; customer OCR chargeback is calculated from database OCR run records, not AWS Cost Explorer object-tag attribution. Local remains the default for development and CI.

Platform administrators can inspect app-side OCR usage with
`GET /api/v1/admin/ocr-billing`. The report groups runs by billable customer
account and aircraft tags, separates chargeable from non-billable pages and
estimated cost, shows provider/API mode, and supports `dateFrom`, `dateTo`,
`accountTag`, `aircraftTag`, and `billingStatus` filters. Estimated cost comes
from pricing metadata persisted on each OCR run; the report does not infer
customer costs from S3 tags or AWS Cost Explorer. `unpricedRunCount` identifies
runs that lack enough persisted metadata to estimate cost, so unknown cost is
not silently presented as a calibrated zero. The report aggregates completed
runs only and exposes the number of excluded failed/in-flight attempts. Date
ranges are half-open (`dateFrom` inclusive, `dateTo` exclusive), allowing
adjacent reporting periods without double counting; timezone-naive filter
values are interpreted as UTC. Native bypass, Textract
page use, non-page pricing, unattributed runs, and credited/disputed statuses
remain visible as separate quantities.

Optional OCR provider configuration:

```bash
PAPRNAV_OCR_PROVIDER=deterministic
PAPRNAV_OCR_MAX_PDF_PAGES=3
```

PDF ingestion now inspects and fingerprints the source, renders immutable
canonical pages, classifies layout/content, and applies provider-neutral
routing. Pages that satisfy the conservative native-text gate bypass Textract;
scanned, handwritten, mixed, degraded, image-dominant, spread, and uncertain
pages continue to Textract. See
`.ai/NATIVE_TEXT_ROUTING_ACTIVATION_2026-07-26.md`.

All OCR-derived logbook entries begin in `needs_review`, regardless of provider
confidence or native-text routing. An ingestion job remains
`awaiting_entry_review` until an assigned maintenance reviewer explicitly
verifies every extracted entry. Verification stores the reviewer and a server
timestamp even when optional client timing is absent. Only individually
verified entries are eligible as evidence in AD matching; a zero-entry
extraction remains open as `awaiting_manual_entry_review`.
Manually transcribed entries also begin in `needs_review` and require the same
assigned-maintenance verification before they can participate in AD matching.

The approved OCR-refinement path and provider decisions are closed in
`.ai/OCR_PATH_CLOSURE_2026-07-26.md`. Early-adopter review and worker
reliability are subsequent operational stages, not unfinished OCR engine work.

The controlled native fixtures are not final production proof. When
early-adopter PDFs are ingested, every initially native-routed page must be
reviewed against its canonical render using
`.ai/EARLY_ADOPTER_NATIVE_TEXT_REVIEW.md`.

Google Document AI has an evaluation-only adapter in
`app/services/google_document_ai.py`. Install
`requirements-google-ocr.txt` in an isolated environment and use
`app.scripts.run_google_document_ai_evaluation` only with the frozen
OCR-refinement partition. The 2026-07-26 run passed technical mapping 11 out
of 11 but passed the existing three-page quality gate 0 out of 3, so Google is
not registered in active provider selection.

Historical/paused: the local layout-first feasibility provider detects document regions with
PP-DocLayout-V3 and recognizes each crop with GLM-OCR through local Ollama:

```bash
PAPRNAV_OCR_PROVIDER=layout_first_vlm
PAPRNAV_LAYOUT_FIRST_LAYOUT_MODEL=PaddlePaddle/PP-DocLayoutV3_safetensors
PAPRNAV_LAYOUT_FIRST_LAYOUT_DEVICE=cpu
PAPRNAV_LAYOUT_FIRST_LAYOUT_THRESHOLD=0.3
PAPRNAV_LAYOUT_FIRST_RECOGNITION_MODEL=glm-ocr:latest
PAPRNAV_LAYOUT_FIRST_OLLAMA_BASE_URL=http://127.0.0.1:11434
PAPRNAV_LAYOUT_FIRST_TIMEOUT_SECONDS=120
PAPRNAV_LAYOUT_FIRST_PDF_DPI=200
PAPRNAV_LAYOUT_FIRST_COMPUTE_RATE_USD_PER_HOUR=0
```

Install the optional model dependencies separately from the ordinary API image:

```bash
python -m venv .venv-glmocr
.venv-glmocr/bin/pip install -r requirements-layout-ocr.txt
ollama pull glm-ocr:latest
```

Run the guarded local one-page acceptance slice:

```bash
.venv-glmocr/bin/python -m app.scripts.run_layout_first_feasibility
```

This path keeps the test document local, records one billable work unit per
processed page, preserves detector confidence separately from recognition
confidence, and reports recognition confidence as unavailable when GLM-OCR
does not provide a calibrated score. Local internal cost uses measured
processing seconds and `PAPRNAV_LAYOUT_FIRST_COMPUTE_RATE_USD_PER_HOUR`; the
default zero rate means cost is not yet calibrated while page units remain
attributed to the customer account and aircraft. The local Ollama path is a
feasibility runtime, not yet the ECS production topology.

AWS Textract remains the AWS baseline provider:

```bash
PAPRNAV_OCR_PROVIDER=textract
PAPRNAV_TEXTRACT_API_MODE=async
PAPRNAV_TEXTRACT_ASYNC_POLL_SECONDS=2
PAPRNAV_TEXTRACT_ASYNC_TIMEOUT_SECONDS=300
PAPRNAV_TEXTRACT_ESTIMATED_UNIT_COST_USD_PER_PAGE=0
```

Mistral OCR is reserved for A/B testing unless explicitly promoted:

```bash
PAPRNAV_OCR_PROVIDER=mistral
PAPRNAV_MISTRAL_API_KEY=
PAPRNAV_MISTRAL_BASE_URL=https://api.mistral.ai/v1
PAPRNAV_MISTRAL_OCR_MODEL=mistral-ocr-4-0
PAPRNAV_MISTRAL_OCR_CHANNEL=direct_api
PAPRNAV_MISTRAL_SAGEMAKER_ENDPOINT_NAME=
PAPRNAV_MISTRAL_SAGEMAKER_REGION=
PAPRNAV_MISTRAL_OCR_MODE=ab_test
PAPRNAV_MISTRAL_OCR_MAX_PDF_PAGES=3
```

Local development and feasibility scripts load `backend/.env` automatically when present. Explicit process environment variables still take precedence. Tests set `PAPRNAV_DISABLE_DOTENV=1` so real local secrets are not read during automated test runs.

When a third-party OCR provider such as Mistral is used, the upload/review flow should show a conditional third-party processing note. Customer OCR chargeback must be calculated from paprnav `OCRRun` records by provider/model, API mode, billable page count, billable account tag, billable aircraft tag, and configured unit price.

## Database Migrations

Alembic is scaffolded with an initial schema migration for users, organizations, aircraft, logbook sections, logbook entries, and upload metadata.

Create a migration after SQLAlchemy models change:

```bash
alembic revision --autogenerate -m "describe schema change"
```

Apply migrations:

```bash
alembic upgrade head
```

Show migration status:

```bash
alembic current
```

Seed repeatable local demo data:

```bash
python -m app.scripts.seed_dev
```

Seeded demo users:

- `owner.demo@paprnav.local`
- `shop.demo@paprnav.local`

Both use the local-only password `demo-password`.

## Implemented API Pieces

The backend currently has:

- Root, health, and version endpoints
- Cookie-backed local auth/session endpoints under `/api/v1/auth`
- Authenticated aircraft list, create, view, and update endpoints under `/api/v1/aircraft`
- Owner-only aircraft assignment endpoints for granting maintenance shop access
- Authenticated logbook entry list, create, view, and update endpoints under `/api/v1/aircraft/{aircraftId}/logbook-entries`
- Authenticated upload create and download endpoints
- Deterministic local OCR ingestion job, page verification, OCR correction, and structured extraction endpoints
- Federal Register AD discovery, structured AD extraction, AD extraction review, and first-pass AD-to-logbook match endpoints
- HITL AD match adjudication endpoints
- Reusable airframe/component AD coverage resolution backed by one retained DRS source snapshot
- Platform-admin AD/DRS storage and cost-attribution summary at `GET /api/v1/admin/ad-costs`
- Product observability and feedback endpoints
- Owner-versus-maintenance aircraft visibility boundaries

## Missing Backend Pieces

The backend does not yet have:

- Production AWS worker scheduling or object storage

See `.ai/GOAL_TASKS.md` from the project root for the current implementation roadmap.

Aircraft creation/update and the AD matching worker resolve reusable AD
coverage from the current retained DRS snapshot. A later client with the same
airframe/component applicability targets links to the existing coverage rather
than downloading or duplicating DRS data.

The aircraft AD-match response reports DRS coverage health separately from
individual match results. Missing, degraded, or pending coverage produces
explicit warnings so a completed matcher run cannot be mistaken for complete
AD coverage. Incomplete component identity and DRS snapshots older than
`PAPRNAV_DRS_MAX_SNAPSHOT_AGE_DAYS` (default `7`) also prevent a `current`
coverage status. Superseded or plausibly applicable but identity-uncertain
directives require adjudication. Logbook evidence changes invalidate the
current match immediately; retained historical rows are not returned as
current worklist results.

Local retained-source proof commands:

```bash
python -m app.scripts.run_ad_source_proof --help
python -m app.scripts.run_ad_publication_proof --help
```

The production backend image includes `mdbtools` for FAA Access imports and
Poppler for canonical PDF inspection/rendering. GovInfo reconciliation uses
`GOVINFO_API_KEY`; source artifacts are content-addressed and repeat runs are
idempotent. See `.ai/AD_SOURCE_PROOF_2026-08-04.md` from the repository root.
Aircraft identity changes and newly approved AD applicability also invalidate
affected worklists, including prior zero-result runs. AD extraction approval
requires at least one attributable affected product so subscription-based
invalidation cannot be bypassed by empty applicability.

The admin cost response separates physical shared-source storage, estimated
logical coverage storage, and aircraft-specific comparison usage. Actual and
future allocated costs remain separate; customer allocation is not active.

## Checks

Compile the current backend module:

```bash
python -m py_compile main.py
```

Run the backend endpoint tests:

```bash
python -m pytest
```

When using the Dockerized API container:

```bash
docker compose exec -T api python -m pytest
```
