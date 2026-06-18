# paprnav Backend

This directory contains the early FastAPI backend for paprnav. It supports the current local MVP API surface for auth, aircraft, logbook entries, and file uploads, but it is not yet a complete OCR or AD-compliance backend.

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
  - `/api/v1/aircraft/{aircraftId}/logbook-entries/*` provides authenticated logbook entry endpoints.
  - `/api/v1/aircraft/{aircraftId}/uploads` stores uploaded PDF/JPG/PNG files and metadata.
  - `/api/v1/uploads/{uploadId}/download` retrieves stored original uploads for authorized users.

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
PAPRNAV_MAX_UPLOAD_SIZE_BYTES=104857600
```

Local uploaded files are stored under `.data/`, which is ignored by git. Production storage should use the selected S3-compatible storage target from `.ai/DECISIONS.md`.

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
- Authenticated logbook entry list, create, view, and update endpoints under `/api/v1/aircraft/{aircraftId}/logbook-entries`
- Authenticated upload create and download endpoints
- Owner-versus-maintenance aircraft visibility boundaries

## Missing Backend Pieces

The backend does not yet have:

- OCR ingestion jobs
- FAA Airworthiness Directive ingestion or matching

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
