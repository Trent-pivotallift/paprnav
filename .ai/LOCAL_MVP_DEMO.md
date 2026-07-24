# paprnav Local MVP Demo Path

Last verified: 2026-06-27

This document captures the local end-to-end demo path verified against the current FastAPI, Postgres, and Next.js MVP.

## Start The Stack

From `backend`:

```bash
docker compose up -d db api
docker compose run --rm migrate
docker compose run --rm seed
```

From `frontend/paprnav-frontend`:

```bash
npm run dev
```

Open `http://localhost:3000`.

Demo users:

- Owner: `owner.demo@paprnav.local`
- Maintenance shop: `shop.demo@paprnav.local`
- Password for both: `demo-password`

Seeded demo aircraft:

- `N123AB`
- Make/model: `Cessna 172R`

## Human Demo Flow

1. Sign in as `owner.demo@paprnav.local`.
2. Open `Dashboard` and confirm `N123AB` is visible.
3. Open `N123AB`, then use the upload action for the airframe logbook.
4. Upload a PDF or image fixture.
5. Run OCR processing from `backend`:

   ```bash
   docker compose exec -T api python -m app.workers.ocr
   ```

6. Open the ingestion review page linked after upload.
7. Confirm page order and completeness.
8. Save at least one low-confidence OCR correction.
9. Run structured entry extraction from the ingestion page.
10. Open `ADs` and review a pending AD extraction.
11. Run AD matching from `backend`:

    ```bash
    docker compose exec -T api python -m app.workers.ad_matching --aircraft-id <aircraft-id>
    ```

12. Open `N123AB` and review the `AD Compliance Worklist`.
13. Adjudicate a `needs_adjudication` AD item.
14. Open `Observability` and confirm product events plus workflow timeline entries are present.

## Verification Evidence From 2026-06-27

Local stack:

- `docker compose up -d db api` reported `backend-db-1` healthy and `backend-api-1` running.
- `docker compose run --rm migrate` completed against Alembic head `20260620_0007`.
- `docker compose run --rm seed` seeded demo users, organizations, aircraft, sections, assignments, and logbook entries.
- `npm run dev` served the frontend at `http://localhost:3000`.

End-to-end verified:

- Frontend smoke script passed login, route, aircraft dashboard, manual entry, upload, and ingestion-job creation through the same-origin proxy.
- OCR worker processed queued jobs to `awaiting_page_review`.
- Ingestion job `job_fc59f4961bce4f2a9d6448885201fcbc` was page-verified, corrected, and extracted into structured logbook entries through the frontend proxy API.
- AD review fixture `2026-99-77` was reviewed as `edited` through the frontend proxy API.
- AD matching produced component-aware worklist entries for `N123AB`.
- AD `2026-99-79` produced a HITL item and was adjudicated as `needs_more_info`.
- Browser UI checks verified:
  - Login reaches `/logbook`.
  - `N123AB` shows `AD Compliance Worklist`.
  - The worklist shows `2026-99-77` as candidate satisfied and `2026-99-79` as adjudicated needs more info.
  - The ingestion review page shows OCR complete, page review verified, entry extraction complete, and the saved correction text.
  - The observability page shows upload ingestion, OCR correction, AD extraction, AD matching, and HITL adjudication workflow events.
  - The AD review page renders pending and reviewed extraction-review content.

Checks run:

```bash
cd backend
./.venv/bin/python -m pytest

cd ../frontend/paprnav-frontend
npm run lint
npm run build
npm run smoke
```

Result:

- Backend tests: `14 passed`
- Frontend lint: passed
- Frontend build: passed
- Frontend smoke: passed

## Demo Notes

- The local AD review and HITL demo used deterministic local fixture ADs instead of live FAA network calls.
- The product remains decision support, not official compliance attestation.
- `backend/app/services/ad_reconciliation.py` is currently service-level code with tests; there is not yet a dedicated reconciliation CLI worker module.
