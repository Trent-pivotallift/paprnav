# Package D implementation handoff

## Outcome

Implemented the bounded Package D telemetry/cost family without a model or
migration change and without enabling a provider, worker, service, or AWS
mutation. This is builder evidence for independent implementation review; it is
not an approval or closure claim.

- Added the declarative six-event `pilot-achievement-v1` recorder and
  projection. Properties are event-specific allowlists, identity is
  server-derived, canonical writes share the success transaction, and the
  report selects the earliest `(event_time, id)` representative before date,
  actor, grouping, or recent-limit behavior. Counts are independent of the
  display limit.
- Wired invite acceptance, aircraft creation after cost identifiers, consented
  upload plus ingestion job, the first completed-OCR/order/completeness page
  review, manual and newly extracted logbook entries, and successful human AD
  extraction/match decisions. Conflict/409 paths do not emit achievements.
  Extracted-entry events are owned by `extract_entries_from_job` before its
  existing commit, require the explicit HTTP actor, skip returned existing
  entries, and remain disabled for the actorless feasibility caller.
- Added strict `X-Correlation-ID` validation/context/response propagation and a
  generic unexpected-500 path. Structured error logs contain only the route
  template, method, status, release, correlation ID, and available
  server-derived identifiers; they omit request content and exception text.
- Added the platform-admin-only `/api/v1/admin/pilot-summary` schema/service/
  endpoint and compact admin cards. Achievement recent rows and failure/
  feedback records are bounded and content-free. OCR is explicitly a
  recorded-run projection with `recordedRunsOnly=true`,
  `paidAttemptCoverageComplete=false`, missing-row/reconciliation completeness
  unavailable, independent lifecycle/pricing/recorded-attribution/billing
  counts, nullable known partial estimates, unknown amounts, and explicit
  unpriced/unattributed/failed/pending/reconciliation-required counts. Stored
  billing tags are not reassigned to a current owner.
- Ordinary observability continues to use the Package B scoped endpoint and
  does not request the admin summary. The existing real budget-subscriber gate
  and disabled worker schedule were not changed and are asserted by the oracle.

## Changed files and SHA-256

| File | SHA-256 |
| --- | --- |
| `backend/app/core/request_context.py` | `eabf19024e88141fb46901bc1dc0b7332163a99c35abc6c68fbefb6360ab92b3` |
| `backend/app/services/pilot_achievements.py` | `729fd6449da29b1f3b041b13372f033949508c9375813cafe170b2bb955135ce` |
| `backend/app/services/pilot_summary.py` | `bd1398b13d5991d4da2bdbe7e85a561f5ef208e92f48dbe8a622f3adcad7d50f` |
| `backend/app/main.py` | `2f7731aa561677814631350500d344bd47277d6265384dc533c1f7291f4c9c56` |
| `backend/app/api/deps.py` | `ec2aafb81aa33d7d01f8360d65c7b73fe48311c457b037563d2f93eec9ab57d0` |
| `backend/app/schemas/observability.py` | `3f475541c49bb872e96954f511e766ba4634d33d7c90ae9d01289e382228e29b` |
| `backend/app/api/routes/admin.py` | `efca8e79087300b20e18c0c1301d8fed3c9308745f01b0f485a561264e123d45` |
| `backend/app/api/routes/auth.py` | `ac8b64d406c154e42dbe3f723a5f3d1a41a9ab567d4820d706a75fc2c8c2e4a8` |
| `backend/app/api/routes/aircraft.py` | `8c32bf149ab884515a31bd049fbc41d3e4ecd504b2413b49d8eb0be847b16096` |
| `backend/app/api/routes/uploads.py` | `4b6e34ffb83857324d16f71358550bd9c3fee091f57fccdae48a14ade22560ef` |
| `backend/app/api/routes/ingestion.py` | `01253f621a60ca1956c338a12172d9ab61696914bfa2c010b0dd2d8107f4f18c` |
| `backend/app/api/routes/logbook_entries.py` | `175756361522e89ea96d511c5d6e92f2656cf003f3ea0fece0eb1db6342b69b8` |
| `backend/app/services/ingestion.py` | `868fdf4949c5bd60aefbb6c3b0b95d5e1c0d63d91152aab7772be8d5d61b7119` |
| `backend/app/scripts/run_ocr_feasibility.py` | `7f991267e16c3ec1fc0c90df398c3c93650edf891ef99a93a7e8aed70c7109cb` |
| `backend/app/api/routes/ads.py` | `1120b38fd163d4caa8fe296f64154a223c4cf2d6fbc87dfab8a2cbfc7f4d6ec9` |
| `backend/tests/test_pilot_package_d.py` | `ae4b39c13acf1a2c2559a1b87244a488c68c29dd39982bf98fb808963ff1cc17` |
| `frontend/paprnav-frontend/src/app/(authenticated)/observability/page.tsx` | `3b3f1874393fd19d89cfd3f957aca9ee5f594cfbaef47ea0cebc1983e03974d8` |
| `frontend/paprnav-frontend/src/lib/api.ts` | `51f59fd391f506dfed88de107cd6c3b61788b461be99af463d213187c8ded7cf` |
| `frontend/paprnav-frontend/tests/pilot-observability.test.mjs` | `3d1930db6d66df4feea8ccecfc5df01ab6a3722e14930958510b8134dc41dacb` |

The hashes bind the current shared working-tree bytes, including pre-existing
Package A-C edits in overlapping files. This handoff artifact is intentionally
not self-hashed.

## Verification

- `PYTHONPATH=. .venv/bin/pytest -q tests/test_pilot_package_d.py` from
  `backend`: **3 passed**. The retained oracle covers rollback/success,
  duplicate representative/order and limit-independent counts, fixed-property
  sanitization, correlation/error negatives including a database outage,
  two-tenant/admin and revoked-admin authorization, recorded OCR categories,
  extracted-entry/conflict source ordering, frontend admin-only rendering,
  and Terraform budget/worker gates. Existing pytest/SQLAlchemy teardown and
  deprecation warnings remained non-failing.
- `npm run test:pilot`: **2 passed**.
- `./node_modules/.bin/tsc --noEmit`: **passed**.
- Targeted Python `compileall` for changed backend modules: **passed**.
- Direct compatibility check for invite boundary, existing OCR billing, and AD
  matching: **23 passed**. No broad repository or T081 suite was run.
- Scoped `git diff --check` and new-file trailing-whitespace scan: **passed**.
- Two initial command-selection attempts failed before tests ran (`.venv` was
  addressed from the repository root, and no generic frontend `npm test`
  script exists); both were corrected to the commands above and were not code
  failures.

## Limitations and Package E gates

Package D reports only committed `OCRRun` rows. It cannot observe a provider
attempt lost before row commit, prove paid-attempt coverage, prove invoice
accuracy, or make reconciliation complete. Package E still requires the
separately reviewed durable pre-call attempt/idempotency/claim protocol,
ambiguous-outcome reconciliation, verified paid-provider mode and page ceiling,
worker/image/secret enablement evidence, live CloudWatch redaction/ingestion
evidence, real AWS Budget notification evidence, and Cost Explorer/CUR
reconciliation. No live AWS status, historical reattribution, customer billing,
provider invocation, image rebuild, Terraform apply, migration, service
activation, staging, or commit occurred.

## Model routing

- Role: implementation builder for `/root/t082_package_d_implementation`.
- Requested route: GPT-5.6 Sol, high, for an approved coherent multi-file
  implementation.
- Actual model: `model not exposed by runtime`.
- Actual effort: `effort not exposed`.
- Trigger: approved Package D design with high-risk audit/authorization/cost
  contracts; independent implementation and closure review remain mandatory.
