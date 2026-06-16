# paprnav

paprnav is an OCR-assisted aviation logbook and Airworthiness Directive decision-support application.

The MVP direction is:

- Customers upload scanned aircraft logbooks.
- The app OCRs the scans and asks users to verify page order and completeness.
- Low-confidence OCR regions are highlighted for human correction.
- Verified OCR is ingested into structured logbook records.
- FAA Airworthiness Directives are ingested from the Federal Register API.
- The app matches ADs against logbook entries and routes uncertain cases to human-in-the-loop adjudication.

The product provides decision support with citations and review trails. It is not an official compliance attestation.

## Project Layout

- `frontend/paprnav-frontend`: Next.js frontend app.
- `backend`: FastAPI backend scaffold.
- `.ai`: project memory, requirements, decisions, MVP definition, and `/goal` task roadmap.
- `ad-ingestion-spec.md`: legacy AD ingestion architecture draft, now marked as historical context.

## Start Here

Read these before starting feature work:

- `.ai/MVP_COMPLETION.md`
- `.ai/REQUIREMENTS.md`
- `.ai/DECISIONS.md`
- `.ai/GOAL_TASKS.md`
- `.ai/AD_INGESTION_REVIEW.md`

## Frontend

```bash
cd frontend/paprnav-frontend
npm install
npm run dev
npm run lint
npm run build
```

## Backend

```bash
cd backend
docker compose up db
uvicorn main:app --reload
```

The backend is currently minimal and exposes only the placeholder FastAPI app.

