# paprnav AI Project State

Last updated: 2026-06-18

This folder is the shared project memory for AI agents working on paprnav. Keep it concise, current, and useful for handoffs.

## Project Summary

paprnav is intended to be an OCR-assisted digital aviation logbook and AD compliance decision-support application for aircraft owners and maintenance shops.

The current codebase is an early local MVP build:

- `frontend/paprnav-frontend` is a Next.js app with auth wiring, authenticated dashboards, aircraft logbook detail pages, manual entry, upload UI, profile UI, and a same-origin backend proxy.
- `backend` is a FastAPI service with root, health, version, auth/session, aircraft, logbook entry, upload, download, ingestion, AD review, and AD matching endpoints.
- Local development uses Docker Compose for the backend API and Postgres database.
- Persisted SQLAlchemy/Alembic models exist for users, organizations, memberships, aircraft, assignments, logbook sections, logbook entries, auth sessions, and uploads.
- Backend endpoint tests now cover auth, aircraft visibility, logbook entry, upload/download, and unauthorized access boundaries.
- There is no AWS infrastructure code or GitHub Actions workflow in this checkout.
- Deterministic local OCR ingestion, page verification, OCR correction, and structured logbook extraction are implemented for the local MVP slice.
- Federal Register AD discovery, AD persistence, deterministic structured extraction, AD extraction review, first-pass AD-to-logbook matching, HITL match adjudication, compliance worklist, and human product observability are implemented locally.

## Important Paths

- Frontend app: `frontend/paprnav-frontend`
- Backend app: `backend`
- Frontend package scripts: `frontend/paprnav-frontend/package.json`
- Backend entrypoint: `backend/main.py`
- Local database compose file: `backend/docker-compose.yml`
- AI project memory: `.ai`
- MVP definition: `.ai/MVP_COMPLETION.md`
- AD ingestion review: `.ai/AD_INGESTION_REVIEW.md`
- Backend/OCR data model plan: `.ai/DATA_MODEL.md`
- MVP AD ingestion spec: `.ai/AD_INGESTION_MVP_SPEC.md`
- AD collection handoff findings: `.ai/AD_COLLECTION_HANDOFF.md`
- AD matching rules: `.ai/AD_MATCHING_RULES.md`
- Interim API contract: `.ai/API_CONTRACT.md`
- Environment variable guide: `.ai/ENVIRONMENT.md`
- External provider references: `.ai/PROVIDER_REFERENCES.md`

## Useful Local Commands

Frontend:

```bash
cd frontend/paprnav-frontend
npm run dev
npm run lint
npm run build
npm run smoke
```

Backend:

```bash
cd backend
uvicorn main:app --reload
docker compose up db
docker compose up api
docker compose run --rm migrate
docker compose exec -T api python -m pytest
docker compose exec -T api python -m app.workers.ad_discovery
docker compose exec -T api python -m app.workers.ad_extraction
docker compose exec -T api python -m app.workers.ad_matching
```

## Current Repo Notes

- The Git repository is at the project root.
- Latest known pushed checkpoint before this task wave: `b37b285 Build local MVP backend integration`.
- Avoid treating `.next` or `node_modules` as source of truth.

## How Agents Should Work Here

1. Read `.ai/MVP_COMPLETION.md`, `.ai/REQUIREMENTS.md`, and `.ai/DECISIONS.md` before making product or architecture changes.
2. Pick one bounded task from `.ai/GOAL_TASKS.md` when using `/goal`.
3. Update `.ai/DECISIONS.md` when making a durable architecture or product choice.
4. Update `.ai/GOAL_TASKS.md` when a task is completed, split, blocked, or made obsolete.
5. Read `.ai/AD_INGESTION_REVIEW.md` before changing AD ingestion or matching behavior.
6. Check current official docs before specifying or implementing external provider behavior.
7. Record provider docs, date checked, verified fields, and mapping notes in `.ai/PROVIDER_REFERENCES.md`.
8. Keep changes scoped. Prefer working vertical slices that can be linted or built.

## Run Closeout Expectations

After any `/goal` or `/agent` run, include a concise closeout with:

- Recap of what changed.
- Evidence and checks run.
- Current git state, including uncommitted or untracked files.
- Human demo point, if one exists.
- Recommended next tasks in order.
- Explicit blockers or external permissions, if any.
