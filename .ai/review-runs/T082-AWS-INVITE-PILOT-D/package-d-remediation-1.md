# Package D remediation 1

Date: 2026-09-19

Builder: `/root/t082_package_d_remediation_1`

Purpose: one coherent remediation pass for open findings T082-D-004,
T082-D-005, and T082-D-006. This is builder evidence for a separate
adversarial reviewer. It does not change the finding ledger or assert closure.

## Remediation outcome

### T082-D-004 — complete ASGI failure boundary

- Replaced the request/response convenience middleware with a pure ASGI
  boundary that remains active while a streaming body is emitted.
- The boundary defers `http.response.start` until the first body message. A
  failure before the first body is therefore replaced with a generic JSON 500
  containing the correlation ID, without exposing exception or request text.
- After the response has started, the boundary records a sanitized correlated
  failure and sends only an empty terminal body message. The already-started
  status and already-emitted bytes are preserved; no invalid second response is
  attempted.
- Correlation state remains set for the full stream. Authorized upload and page
  image download routes attach server-derived organization and aircraft context
  to request state before entering the shared storage-body iterator, so the
  sanitized record retains actor, tenant, and aircraft attribution.
- A real upload-download route regression uses a fake S3 body that yields one
  chunk and then raises a secret-bearing exception. It also covers failure
  before the first chunk and correlation visibility inside the generator.

### T082-D-005 — executable success-point evidence

The earlier immutable handoff's source-string coverage description is
superseded by the executable evidence in this remediation handoff. Bounded
transaction tests now exercise the six canonical families: invitation
acceptance, aircraft creation, consent/upload completion, manual logbook entry,
extracted logbook entry, and AD match/extraction-review decisions.

Representative negative and transaction cases include invitation replay,
aircraft conflict, consent rejection, incomplete and repeated page
verification, extracted-entry retry, actorless feasibility use, forced
achievement-write rollback, unauthorized AD requests, invalid AD decisions,
and a post-decision AD conflict. Extracted-entry retry testing exposed duplicate
ORM results when an existing entry had multiple evidence links; the retry query
now applies ORM result de-duplication before enforcing the single-entry
invariant. Tests assert explicit actor, organization, aircraft, subject type,
and success-point event properties rather than inserting achievement rows as
proof of the writers.

### T082-D-006 — independent OCR classifications

The administrator view now renders recorded-run lifecycle, pricing, recorded
attribution, billing, completed-priced estimate, unknown amount, and
reconciliation categories independently. The combined known amount is labeled
`Partial recorded-run estimate`, and adjacent copy states that paid-attempt
coverage is incomplete. A server-rendered frontend assertion verifies every
category and the partial-estimate qualification.

## Changed-file hashes

These hashes bind the complete current file bytes in the shared dirty worktree;
some files also contain pre-existing Package D work outside this remediation's
specific edits.

| File | SHA-256 |
| --- | --- |
| `backend/app/main.py` | `a4f0cf1604de161d6cd490137ea6e26d06926b40b6fa231c0444f2085622605e` |
| `backend/app/api/routes/uploads.py` | `c7a167656c54a39bdba19b1ed8265ab07c1761e68b0e875da85315b92382b083` |
| `backend/app/api/routes/ingestion.py` | `8e4ef7198cb12ba8b0b64a399083ad12f70ff48e054c473e39681e2536bf76d3` |
| `backend/app/services/ingestion.py` | `55bf79db60e56178bc0617d950ccbb1076aaf7976879e9b588aaf55620fb7d85` |
| `backend/tests/test_pilot_package_d.py` | `4268fc8481b982dd082e29587561630a56b4f63e96ac1dc996859d5b63b8ace9` |
| `frontend/paprnav-frontend/src/app/(authenticated)/observability/page.tsx` | `5fab235cc19d95cd2bdbe1ea06d8ecab76bf6d0d20b846b5763dec23f7c3bf6b` |
| `frontend/paprnav-frontend/src/lib/pilot-ocr-summary.ts` | `a127a7065ab586e6b6e400eabdcd6806f99ab364c357b1cb5b1d084b9237b2db` |
| `frontend/paprnav-frontend/tests/pilot-observability.test.mjs` | `3d4d7d7946fe3793f297b39e632a52cbeb1fd6ec8d613f32246f53a64cc1c238` |

This handoff intentionally does not self-hash.

## Exact bounded validation

All commands were run from the repository root unless a directory is stated.

1. From `backend`:

   ```text
   PYTHONPATH=. .venv/bin/pytest -q tests/test_pilot_package_d.py
   ```

   Initial remediation run: `5 passed, 2 failed`. The failures identified the
   extracted-entry join duplication described above and a stale source-text UI
   assertion. After fixing the query and replacing string-only proof with
   executable rendering coverage, the final result was `7 passed, 89 warnings
   in 3.19s`.

2. From `frontend/paprnav-frontend`:

   ```text
   npm run test:pilot
   ```

   Result: `3 passed`.

3. From `frontend/paprnav-frontend`:

   ```text
   ./node_modules/.bin/tsc --noEmit
   ```

   Result: exit 0, no output.

4. From `backend`, adjacent download/invite/release-boundary compatibility:

   ```text
   PYTHONPATH=. .venv/bin/pytest -q tests/test_mvp_endpoints.py::test_upload_create_download_validation_and_access_boundary tests/test_mvp_endpoints.py::test_ingestion_page_image_download_for_image_upload tests/test_mvp_endpoints.py::test_s3_upload_download_streams_from_configured_bucket tests/test_pilot_invite_tenant_boundary.py::test_pilot_invitation_acceptance_is_atomic_and_non_replayable tests/test_pilot_release_boundary.py::test_safe_pilot_configuration_disables_all_v4_routes tests/test_pilot_release_boundary.py::test_encoded_path_delimiters_cannot_reach_authentication tests/test_pilot_release_boundary.py::test_decoded_scope_path_and_root_path_gate_without_reading_body tests/test_pilot_release_boundary.py::test_local_environment_retains_v4_route_inventory
   ```

   Result: `9 passed, 85 warnings in 2.18s`.

5. Final scoped hygiene and Python compile check:

   ```text
   git diff --check -- backend/app/main.py backend/app/api/routes/uploads.py backend/app/api/routes/ingestion.py backend/app/services/ingestion.py backend/tests/test_pilot_package_d.py 'frontend/paprnav-frontend/src/app/(authenticated)/observability/page.tsx' frontend/paprnav-frontend/src/lib/pilot-ocr-summary.ts frontend/paprnav-frontend/tests/pilot-observability.test.mjs
   PYTHONPATH=backend backend/.venv/bin/python -m compileall -q backend/app/main.py backend/app/api/routes/uploads.py backend/app/api/routes/ingestion.py backend/app/services/ingestion.py backend/tests/test_pilot_package_d.py
   ```

   Result: both exit 0, no output.

The retained warnings are existing dependency deprecations and test-database
cleanup warnings; no bounded validation case is failing.

## Findings addressed and remaining gates

- T082-D-004: implementation and executable regression evidence supplied;
  independent reviewer verification remains required.
- T082-D-005: executable positive, retry, rollback, actor, actorless, rejected,
  and conflict evidence supplied; independent reviewer verification remains
  required.
- T082-D-006: independent UI classifications and rendering evidence supplied;
  independent reviewer verification remains required.

The post-header failure behavior necessarily cannot replace an already-started
response with a 500. Clients receive only bytes already emitted plus a clean
stream terminator, while operators receive the sanitized correlated failure.
OCR totals remain explicitly limited to recorded runs and are not a provider
billing reconciliation. Package E must retain that distinction while proving
its billing/provider and operational gates. This pass did not modify migrations,
Terraform, AWS resources, provider settings, review ledgers, or finding status.

## Model routing

- Role: remediation builder; not the independent implementation reviewer.
- Requested route: GPT-5.6 Sol at `xhigh` effort.
- Trigger: first substantive failed implementation review under an approved
  design, covering a cross-layer ASGI safety boundary, transactional audit
  evidence, and administrator billing semantics.
- Actual model/effort: model not exposed by runtime (effort not exposed).
- Independent closure: the coordinator must assign a separate reviewer and
  record that reviewer identity; this builder does not claim closure.
