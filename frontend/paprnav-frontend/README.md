# paprnav Frontend

paprnav is a digital aviation logbook application for aircraft owners and maintenance shops. This frontend currently provides the authenticated app shell, aircraft/logbook screens, upload UI, profile UI, theme switching, and Shadcn/ui-style components.

The app is still early-stage. Auth, aircraft, logbook entry, upload, profile, maintenance assignment, deterministic OCR review, and OCR-to-logbook extraction flows are wired to the local backend; AD workflows are not implemented yet.

## Tech Stack

- Next.js App Router
- React
- TypeScript
- Tailwind CSS
- Radix UI primitives
- lucide-react icons
- Local UI components in `src/components/ui`

## Local Setup

Install dependencies:

```bash
npm install
```

Start the frontend development server:

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

Run lint checks:

```bash
npm run lint
```

Build for production:

```bash
npm run build
```

Run smoke checks against a running local frontend/backend:

```bash
npm run smoke
```

Start a production build:

```bash
npm run start
```

## Scripts

- `npm run dev`: starts the Next.js development server.
- `npm run lint`: runs ESLint.
- `npm run build`: creates a production build.
- `npm run start`: serves the production build.
- `npm run smoke`: checks key routes, authenticated manual-entry creation, upload creation, and ingestion review route rendering through the frontend backend proxy.

## Route Overview

- `/`: login screen.
- `/register`: registration screen.
- `/logbook`: role-switched dashboard for aircraft owners and maintenance shops.
- `/logbook/[nNumber]`: aircraft logbook detail page with airframe, engine, and propeller tabs.
- `/logbook/[nNumber]/upload`: upload UI for scanned logbook records.
- `/logbook/[nNumber]/ingestion/[jobId]`: OCR page review, low-confidence correction, and structured entry extraction.
- `/logbook/[nNumber]/entry/[entryId]`: individual logbook entry detail page.
- `/profile`: profile and account screen.

Route groups:

- `src/app/(auth)`: login and registration screens.
- `src/app/(authenticated)`: authenticated application shell and app pages.

## Current Data State

The frontend uses backend auth sessions and fetches dashboard aircraft and logbook entry data from the backend API. Manual logbook entries and uploaded logbook files are created through the backend API.

## Smoke Checks

With the backend Docker API running, database migrated/seeded, and the frontend dev server available at `http://localhost:3000`, run:

```bash
npm run smoke
```

The smoke script checks key routes and exercises authenticated manual-entry creation, upload creation, and ingestion review route rendering through the frontend same-origin backend proxy.

Optional overrides:

```bash
PAPRNAV_FRONTEND_URL=http://localhost:3000
PAPRNAV_SMOKE_EMAIL=owner.demo@paprnav.local
PAPRNAV_SMOKE_PASSWORD=demo-password
```

Known limitations:

- AD workflows are not implemented yet.
- Full role/permission UX is still minimal; backend authorization is enforced by the API.

## Backend Relationship

The backend lives at `../../backend`. It is a FastAPI app with local Postgres Docker Compose support, auth/session endpoints, aircraft endpoints, logbook entry endpoints, and upload create/download endpoints.

The frontend proxies browser API calls through `/api/backend/*` to preserve same-origin cookie behavior in local development. Set `PAPRNAV_BACKEND_URL` for the Next server if the backend is not running at `http://127.0.0.1:8000`.

## Project Memory

Shared AI/project context lives in `../../.ai`.

Start there before larger changes:

- `../../.ai/README.md`
- `../../.ai/REQUIREMENTS.md`
- `../../.ai/DECISIONS.md`
- `../../.ai/GOAL_TASKS.md`

Use `.ai/GOAL_TASKS.md` to pick bounded work for `/goal` runs and update the `.ai` files when decisions or task status changes.
