# paprnav Frontend

paprnav is a digital aviation logbook application for aircraft owners and maintenance shops. This frontend currently provides the authenticated app shell, aircraft/logbook screens, upload UI, profile UI, theme switching, and Shadcn/ui-style components.

The app is still early-stage. Most screens use static mock data and form submissions are not wired to the backend yet.

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

Start a production build:

```bash
npm run start
```

## Scripts

- `npm run dev`: starts the Next.js development server.
- `npm run lint`: runs ESLint.
- `npm run build`: creates a production build.
- `npm run start`: serves the production build.

## Route Overview

- `/`: login screen.
- `/register`: registration screen.
- `/logbook`: role-switched dashboard for aircraft owners and maintenance shops.
- `/logbook/[nNumber]`: aircraft logbook detail page with airframe, engine, and propeller tabs.
- `/logbook/[nNumber]/upload`: upload UI for scanned logbook records.
- `/logbook/[nNumber]/entry/[entryId]`: individual logbook entry detail page.
- `/profile`: profile and account screen.

Route groups:

- `src/app/(auth)`: login and registration screens.
- `src/app/(authenticated)`: authenticated application shell and app pages.

## Current Data State

The frontend uses backend auth sessions and fetches dashboard aircraft and logbook entry data from the backend API. Manual logbook entries and uploaded logbook files are created through the backend API.

Known limitations:

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
