# paprnav AI Project State

Last updated: 2026-06-16

This folder is the shared project memory for AI agents working on paprnav. Keep it concise, current, and useful for handoffs.

## Project Summary

paprnav is intended to be an OCR-assisted digital aviation logbook and AD compliance decision-support application for aircraft owners and maintenance shops.

The current codebase is early-stage:

- `frontend/paprnav-frontend` is a Next.js app with Shadcn/ui-inspired components, route groups for auth and authenticated pages, role-switched logbook dashboards, aircraft logbook detail pages, upload UI, profile UI, and static mock data.
- `backend` is a minimal FastAPI service with a root endpoint and a local Postgres `docker-compose.yml`.
- There is no implemented frontend-to-backend API integration yet.
- There is no auth implementation yet; login/register forms are visual only.
- There is no persisted domain model yet beyond the Postgres container scaffold.
- There is no AWS infrastructure code or GitHub Actions workflow in this checkout.

## Important Paths

- Frontend app: `frontend/paprnav-frontend`
- Backend app: `backend`
- Frontend package scripts: `frontend/paprnav-frontend/package.json`
- Backend entrypoint: `backend/main.py`
- Local database compose file: `backend/docker-compose.yml`
- AI project memory: `.ai`
- MVP definition: `.ai/MVP_COMPLETION.md`
- AD ingestion review: `.ai/AD_INGESTION_REVIEW.md`

## Useful Local Commands

Frontend:

```bash
cd frontend/paprnav-frontend
npm run dev
npm run lint
npm run build
```

Backend:

```bash
cd backend
uvicorn main:app --reload
docker compose up db
```

## Current Repo Notes

- The Git repository is nested at `frontend/paprnav-frontend`, not at the project root.
- `origin/main` currently points to `18f8000`, matching local `main`.
- Latest commit: `Modernize frontend with Shadcn/ui and theme switching`.
- Project root is not a Git repository at the time of this note.
- Avoid treating `.next` or `node_modules` as source of truth.

## How Agents Should Work Here

1. Read `.ai/MVP_COMPLETION.md`, `.ai/REQUIREMENTS.md`, and `.ai/DECISIONS.md` before making product or architecture changes.
2. Pick one bounded task from `.ai/GOAL_TASKS.md` when using `/goal`.
3. Update `.ai/DECISIONS.md` when making a durable architecture or product choice.
4. Update `.ai/GOAL_TASKS.md` when a task is completed, split, blocked, or made obsolete.
5. Read `.ai/AD_INGESTION_REVIEW.md` before changing AD ingestion or matching behavior.
6. Keep changes scoped. Prefer working vertical slices that can be linted or built.
