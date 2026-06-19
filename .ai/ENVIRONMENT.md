# paprnav Environment Variables

Last updated: 2026-06-18

This file documents local environment variables and the shape of future production configuration. Do not commit real secrets.

## Local Backend

Example file: `backend/.env.example`

| Variable | Required | Default | Purpose |
| --- | --- | --- | --- |
| `PAPRNAV_APP_NAME` | No | `paprnav` | FastAPI app name. |
| `PAPRNAV_APP_VERSION` | No | `0.1.0` | Version returned by `/version`. |
| `PAPRNAV_ENV` | No | `local` | Runtime environment label. |
| `DATABASE_URL` | No for local Docker, yes for non-default DBs | Local Postgres URL | SQLAlchemy database URL. |
| `PAPRNAV_CORS_ORIGINS` | No | Local Next.js origins | Comma-separated browser origins allowed by FastAPI CORS. |
| `PAPRNAV_LOCAL_STORAGE_PATH` | No | `.data` | Local uploaded-file storage root. |
| `PAPRNAV_MAX_UPLOAD_SIZE_BYTES` | No | `104857600` | Maximum accepted upload size. |

## Local Frontend

Example file: `frontend/paprnav-frontend/.env.example`

| Variable | Required | Default | Purpose |
| --- | --- | --- | --- |
| `PAPRNAV_BACKEND_URL` | No | `http://127.0.0.1:8000` | Server-side backend target for the Next.js same-origin proxy. |
| `NEXT_PUBLIC_PAPRNAV_API_BASE_URL` | No | `/api/backend` | Browser API base. Keep this same-origin locally to preserve cookie behavior. |
| `PAPRNAV_FRONTEND_URL` | No | `http://localhost:3000` | Target URL for `npm run smoke`. |
| `PAPRNAV_SMOKE_EMAIL` | No | `owner.demo@paprnav.local` | Smoke-test login email. |
| `PAPRNAV_SMOKE_PASSWORD` | No | `demo-password` | Local-only smoke-test password. |

## Future AWS Target

Production should not use checked-in `.env` files. Expected AWS-sourced values:

- Database connection string from managed secret storage.
- Object storage bucket/key configuration for uploaded files.
- Auth/session secrets once the MVP session strategy is hardened.
- OCR provider credentials and regional settings.
- AD extraction provider credentials if the selected provider requires them.
- Frontend/backend public URLs and allowed CORS origins.

## Local Copy Commands

```bash
cp backend/.env.example backend/.env
cp frontend/paprnav-frontend/.env.example frontend/paprnav-frontend/.env.local
```

The copied files are ignored by git.
