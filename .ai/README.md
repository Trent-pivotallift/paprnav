# paprnav AI Project State

Last updated: 2026-08-02

This folder is the shared project memory for AI agents working on paprnav. Keep it concise, current, and useful for handoffs.

## Project Summary

paprnav is intended to be an OCR-assisted digital aviation logbook and AD compliance decision-support application for aircraft owners and maintenance shops.

The current codebase is an early local MVP build:

- `frontend/paprnav-frontend` is a Next.js app with auth wiring, authenticated dashboards, aircraft logbook detail pages, manual entry, upload UI, profile UI, and a same-origin backend proxy.
- `backend` is a FastAPI service with root, health, version, auth/session, aircraft, logbook entry, upload, download, ingestion, AD review, and AD matching endpoints.
- Local development uses Docker Compose for the backend API and Postgres database.
- Persisted SQLAlchemy/Alembic models exist for users, organizations, memberships, aircraft, assignments, logbook sections, logbook entries, auth sessions, and uploads.
- Backend endpoint tests now cover auth, aircraft visibility, logbook entry, upload/download, and unauthorized access boundaries.
- AWS pilot infrastructure now exists under `infra/terraform` and has been applied for the foundation slice: S3 artifacts/state buckets, ECR repos, ECS cluster, CloudWatch log groups, and AWS Budget. Terraform state is remote in S3. GitHub Actions workflow remains blocked by credential scope.
- The OCR path is closed for the approved refinement scope: immutable PDF/page
  evidence, conservative native-text bypass, Textract fallback, deterministic
  validation, structured extraction, and evidence-backed review are
  implemented. See `.ai/OCR_PATH_CLOSURE_2026-07-26.md`.
- The AD pipeline is DRS-first for applicability indexing, with mandatory
  Federal Register/GovInfo catalog ingestion, retained official/historical
  artifacts, and exhaustive source reconciliation before any completeness
  claim. This local source proof precedes AWS deployment; see D025 and T077.
- DRS bulk fixture import, Federal Register enrichment/matching, AD persistence, deterministic structured extraction, AD extraction review, component-aware AD-to-logbook matching, HITL match adjudication, compliance worklist, reconciliation, and human product observability are implemented locally.
- The retained Cessna 172G/O-300-D source proof is documented in
  `.ai/AD_SOURCE_PROOF_2026-08-04.md`: 40 DRS-indexed 172G entries, 11 O-300-D
  engine entries, exact pagination-gap classification, repeatable manifests,
  and conservative historical publication adjudication.
- Reusable AD coverage now links normalized airframe/component targets to one retained DRS source snapshot. Later clients reuse existing coverage without duplicate downloads. A platform-admin view reports physical source storage, estimated logical coverage storage, benefiting clients/aircraft, actual cost, and separate inactive future allocation. See `.ai/AD_COVERAGE_ATTRIBUTION_REFINEMENT_2026-07-26.md`.

## Important Paths

- Frontend app: `frontend/paprnav-frontend`
- Backend app: `backend`
- Frontend package scripts: `frontend/paprnav-frontend/package.json`
- Backend entrypoint: `backend/main.py`
- Local database compose file: `backend/docker-compose.yml`
- AI project memory: `.ai`
- MVP definition: `.ai/MVP_COMPLETION.md`
- AD ingestion review: `.ai/AD_INGESTION_REVIEW.md`
- Local MVP demo path: `.ai/LOCAL_MVP_DEMO.md`
- Backend/OCR data model plan: `.ai/DATA_MODEL.md`
- MVP AD ingestion spec: `.ai/AD_INGESTION_MVP_SPEC.md`
- AD collection handoff findings: `.ai/AD_COLLECTION_HANDOFF.md`
- AD matching rules: `.ai/AD_MATCHING_RULES.md`
- Interim API contract: `.ai/API_CONTRACT.md`
- Environment variable guide: `.ai/ENVIRONMENT.md`
- Infrastructure and CI unblock plan: `.ai/INFRASTRUCTURE.md`
- AWS pilot Terraform planning loop: `.ai/AWS_PILOT_TERRAFORM_PLAN.md`
- AWS CLI profile names and deploy role: `.ai/AWS_PROFILES.md`
- Current AWS deployment status: `.ai/AWS_DEPLOYMENT_STATUS.md`
- AD coverage/cost refinement closure: `.ai/AD_COVERAGE_ATTRIBUTION_REFINEMENT_2026-07-26.md`
- External provider references: `.ai/PROVIDER_REFERENCES.md`
- Pilot onboarding GUI: `/logbook/onboarding`
- Claude reviewer workflow: `.ai/CLAUDE_REVIEWER.md`

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

AD reconciliation is currently implemented as `backend/app/services/ad_reconciliation.py` and exercised by `backend/tests/test_ad_reconciliation.py`; there is not yet a dedicated CLI worker module for it.

## Current Repo Notes

- The Git repository is at the project root.
- Latest known pushed checkpoint before the 2026-06-27 roadmap reconciliation: `9640b5f Add AD reconciliation worker`.
- `.ai/GOAL_TASKS.md` was reconciled on 2026-06-27 to mark stale early ready tasks as completed or superseded and to refresh blocked CI/infrastructure/release-audit tasks.
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
