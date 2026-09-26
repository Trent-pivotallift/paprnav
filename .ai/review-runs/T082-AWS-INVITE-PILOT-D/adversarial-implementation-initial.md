# Package D implementation review — FAIL

## Model routing

- Builder runtime identity: `/root/t082_package_d_implementation`.
- Reviewer runtime identity: `/root/t082_package_d_implementation_review`.
- Requested builder route: GPT-5.6 Sol, high.
- Requested reviewer route: GPT-6 Astra, high.
- Actual builder/reviewer model: `model not exposed by runtime`.
- Actual effort: `effort not exposed`.
- Trigger: complete-family review spanning administrator authorization, cost
  truthfulness, transaction atomicity, and telemetry privacy.

## Scope and packet

The reviewer inspected the current Package D implementation, staged,
unstaged, and untracked state, and surrounding callers and readers. The
reviewed packet SHA-256 was
`96740f9eb6477d40addeb42927a2811e7197d2e18bda4ae5856d19c5de6167ed`;
packet-current verification passed for scope fingerprint
`1cd0d961c97c840d2803b1ed43bb9f60aa390b19dc73b45e5a460e211881b1b1`.
No repository edit, staging, commit, or cloud mutation occurred during review.

## Findings

### T082-D-004 — High — Streamed-response errors bypass sanitization

The middleware in `backend/app/main.py` catches failures during `call_next`,
but not failures while a returned response is streamed. A bounded
counterexample through the real upload-download route yielded bytes and then
raised a sentinel-bearing exception: the exception escaped, no
`paprnav.unexpected_error` record was emitted, and Uvicorn's ASGI failure path
would log the exception with `exc_info`. Page-image downloads have the same
shape.

Close by covering the complete ASGI response lifecycle, preserving correlation
and actor context while streaming, emitting only sanitized evidence, and
explicitly handling a failure after headers have started. Retain a real
download-stream regression.

### T082-D-005 — Medium — Success-point verification is weaker than claimed

The retained Package D oracle directly inserts many achievement rows. Its
extracted-entry and AD-conflict checks rely on source-string ordering rather
than executing the service and route contracts. This does not prove atomic
rollback, actor attribution, retry behavior, actorless behavior, or absence of
canonical events for rejected requests.

Close with bounded executable cases for the six success-point families,
especially extracted-entry success, retry, actorless invocation, rollback,
and AD-decision conflict behavior. Correct the implementation handoff's
coverage claim to match the retained proof.

### T082-D-006 — Medium — Administrator UI omits approved cost distinctions

The administrator observability page renders the combined known estimate,
recorded-run count, unknown amounts, and reconciliation count, but omits the
API's independent lifecycle, pricing, attribution, billing, and
completed-priced estimate categories.

Close by rendering the independent categories, clearly labeling the combined
amount as a partial recorded-run estimate, and retaining a focused rendering
check.

## Verification performed

- Packet freshness passed before and after review.
- `PYTHONPATH=. .venv/bin/pytest -q tests/test_pilot_package_d.py`: 3 passed.
- `npm run test:pilot`: 2 passed.
- Two bounded streamed-response counterexamples, including the real S3
  download route, reproduced T082-D-004.
- The reviewer traced first-success deduplication, authorization and
  revocation, property inputs, historical-tag cost classification, the
  actorless feasibility caller, and inherited budget and worker controls.

## Residual limitations

Recorded OCR rows do not establish complete paid-attempt coverage. Live
CloudWatch and Budget verification and provider activation remain Package E
gates. The review did not edit models, migrations, T081/0030 work, or any
other repository file.
