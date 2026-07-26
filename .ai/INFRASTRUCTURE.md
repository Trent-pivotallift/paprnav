# paprnav Infrastructure Plan

Last updated: 2026-06-27

This file records the current local deployment shape, selected near-term AWS assumptions, and CI unblock plan. It is planning documentation only: no AWS resources, IaC state, deployment credentials, or GitHub Actions workflows have been applied from this file.

## Current State

- No AWS infrastructure as code is committed.
- No `.github/workflows/*.yml` workflow is committed.
- Local backend orchestration is defined in `backend/docker-compose.yml`.
- Local frontend development runs from `frontend/paprnav-frontend` with `npm run dev`.
- Backend tests use SQLite fixtures and do not require Postgres, AWS, DRS live access, Textract, or provider-backed LLM calls.
- Frontend lint/build use the checked-in Next.js project under `frontend/paprnav-frontend`.

## Local Assumptions

- Backend API: FastAPI served by Uvicorn on port `8000`.
- Local database: Postgres 16 from Docker Compose for application runs; SQLite in-memory fixtures for backend tests.
- Local storage: filesystem under `backend/.data`, configured by `PAPRNAV_LOCAL_STORAGE_PATH`.
- Frontend: Next.js App Router served on port `3000`.
- Local browser-to-API path: same-origin frontend proxy with `NEXT_PUBLIC_PAPRNAV_API_BASE_URL=/api/backend`.
- Local API-to-backend path: `PAPRNAV_BACKEND_URL=http://127.0.0.1:8000` for frontend server-side proxy calls.
- Local worker model: explicit Python worker commands against the same backend database.

## Selected AWS Planning Assumptions

These are the assumptions for the next reviewable production plan. They are not applied infrastructure.

- Account model: one AWS account for the first production slice, with separate `dev` and `prod` environments modeled in IaC variables or workspaces.
- Region: `us-east-1` as the default planning region until a customer, compliance, latency, or cost requirement selects another region.
- IaC tool: Terraform or OpenTofu is the preferred first IaC shape because it supports reviewable `plan` output, explicit remote state, and provider-neutral CI checks. Final tool selection should be recorded before T034 implementation.
- Runtime shape: containerized FastAPI backend and worker commands, plus a separately deployed Next.js frontend. Exact hosting target remains open between ECS/Fargate, App Runner, or another AWS container/web hosting choice.
- Database: managed Postgres through RDS or Aurora PostgreSQL, with migrations run as an explicit deployment step.
- Object storage: S3 for uploaded logbooks and retained AD source artifacts, with server-side encryption, bucket versioning or object retention decisions, lifecycle policies, and least-privilege IAM access.
- Secrets/config: AWS Secrets Manager or SSM Parameter Store for database URLs, session secrets, provider API keys, OCR credentials, and external provider settings. No production secrets should be committed to the repo or GitHub workflow files.
- OCR path: conservatively reliable native PDF text may bypass OCR; scanned,
  handwritten, mixed, degraded, and uncertain pages route to AWS Textract
  through the provider-neutral abstraction. Google, Mistral, and local
  layout-first providers are not active production routes.
- AD ingestion: FAA DRS bulk ZIP/Access ingestion remains fixture-first in CI; live DRS retrieval or Web UI validation stays manually gated and out of CI.
- AD extraction: provider-backed LLM extraction remains env-gated; CI uses deterministic and fake-provider tests only.
- Observability: product/workflow observability remains in Postgres for MVP. Infrastructure logs/metrics should be added in the deployment design, not treated as a substitute for product events.
- Rollback: first production plan must include image rollback, migration rollback/forward policy, and data/artifact retention implications before any dry run is considered complete.

## State And Access Assumptions

- Terraform/OpenTofu state should not be local for shared environments.
- Proposed remote state: encrypted, versioned S3 state bucket with Terraform S3 lockfile support, created by a separately reviewed bootstrap step. DynamoDB locking should not be the default because current Terraform documentation marks that mechanism deprecated for future removal.
- GitHub Actions should not use long-lived AWS access keys for deployment.
- Later deployment workflows should use GitHub OIDC to assume an AWS role constrained to this repository, branch or environment, and least-privilege deployment actions.
- The first CI workflow is verification-only and should not request AWS credentials, deployment secrets, or `id-token: write`.

## CI Unblock Plan

Current blocker: the available GitHub credential previously could not create or update `.github/workflows/ci.yml` because it lacked `workflow` scope. Keep the workflow absent until credentials with workflow scope are available.

The first workflow should be committed as `.github/workflows/ci.yml` once credentials can push workflow files. It should:

- Trigger on pull requests and pushes to `main`.
- Use least-privilege `permissions: contents: read`.
- Run backend tests with Python 3.11 or 3.12 against SQLite fixtures.
- Run frontend `npm ci`, `npm run lint`, and `npm run build`.
- Avoid Docker services, Postgres service containers, AWS credentials, provider API keys, DRS live network access, Textract calls, and LLM provider calls.
- Use dependency caches only after the first workflow is green, unless cache setup is reviewed separately.

Draft workflow to commit after the credential unblock:

```yaml
name: CI

on:
  pull_request:
  push:
    branches:
      - main

permissions:
  contents: read

jobs:
  backend:
    name: Backend tests
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: backend
    steps:
      - name: Check out repository
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install backend dependencies
        run: python -m pip install --upgrade pip && python -m pip install -r requirements.txt

      - name: Run backend tests
        run: python -m pytest

  frontend:
    name: Frontend lint and build
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: frontend/paprnav-frontend
    steps:
      - name: Check out repository
        uses: actions/checkout@v4

      - name: Set up Node
        uses: actions/setup-node@v4
        with:
          node-version: "22"

      - name: Install frontend dependencies
        run: npm ci

      - name: Run frontend lint
        run: npm run lint

      - name: Build frontend
        run: npm run build
```

## Production Planning Sequence

1. Confirm AWS account ID, region, environment names, and IaC tool.
2. Check current official docs for selected AWS services and deployment tooling, then record references in `.ai/PROVIDER_REFERENCES.md`.
3. Review `.ai/AWS_PILOT_TERRAFORM_PLAN.md`, then add IaC skeleton for network/runtime/database/storage/secrets without applying it.
4. Add a non-destructive plan command and document expected local/CI invocation.
5. Review IAM, state, secret, migration, rollback, and retention design.
6. Only after the above, run a deployment dry-run/plan. Do not apply cloud changes until explicitly requested.

## Open Decisions

- Final IaC tool: Terraform, OpenTofu, AWS CDK, or another tool.
- Runtime hosting target for FastAPI and workers.
- Frontend hosting target and whether the backend proxy remains in Next.js production hosting.
- Exact AWS account ID, region, domain, certificate, and environment naming.
- RDS vs Aurora PostgreSQL, backup/retention targets, and migration rollback policy.
- S3 object lock/versioning/lifecycle details for audit artifacts.
- Whether deployment CI should be separate from verification CI once T034 is complete.
