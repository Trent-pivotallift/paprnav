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

The frontend currently uses inline mock data for aircraft, client aircraft, and logbook entries. The upload page simulates a successful upload after a delay.

Known limitations:

- Login and registration forms are visual only.
- Dashboard data is not fetched from an API.
- Uploads are not persisted.
- Logbook entries are mock records.
- Role switching is local UI state, not an authenticated permission model.

## Backend Relationship

The backend is currently separate and minimal at `../../backend`. It is a FastAPI app with a placeholder root endpoint and a local Postgres `docker-compose.yml`.

There is not yet a frontend API client or stable backend contract. Future work should add explicit API contracts before replacing mock data with persisted data.

## Project Memory

Shared AI/project context lives in `../../.ai`.

Start there before larger changes:

- `../../.ai/README.md`
- `../../.ai/REQUIREMENTS.md`
- `../../.ai/DECISIONS.md`
- `../../.ai/GOAL_TASKS.md`

Use `.ai/GOAL_TASKS.md` to pick bounded work for `/goal` runs and update the `.ai` files when decisions or task status changes.
