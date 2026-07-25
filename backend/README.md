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

Optional OCR provider configuration:

```bash
PAPRNAV_OCR_PROVIDER=deterministic
PAPRNAV_OCR_MAX_PDF_PAGES=3
```

The local layout-first feasibility provider detects document regions with
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
- Product observability and feedback endpoints
- Owner-versus-maintenance aircraft visibility boundaries

## Missing Backend Pieces

The backend does not yet have:

- Production AWS worker scheduling or object storage

See `.ai/GOAL_TASKS.md` from the project root for the current implementation roadmap.

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
