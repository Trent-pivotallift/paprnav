# Package D remediation 2 — HTTP logging/privacy family

Date: 2026-09-19. Builder: `/root/t082_package_d_privacy_remediation_2`.
This is implementation evidence for T082-D-004 and T082-D-007, not independent
verification or finding closure. No ledger, review attestation, state, or decision
packet was edited.

## Complete invariant and lifecycle matrix

For the production Docker command, every HTTP request keeps its validated or
generated correlation ID throughout application execution and body streaming.
Only server route templates, allowlisted HTTP methods, release, correlation,
numeric status, delivery-state labels, and authenticated server-derived actor,
organization, and aircraft identifiers enter unexpected-error records. Raw paths,
queries, bodies, cookies, authorization headers, filenames, exception text,
storage keys, and session material never enter those records. Exception objects,
tracebacks, and stack information are not attached. Raw `uvicorn.access` is
disabled for successful responses, HTTP errors, and unexpected failures alike.

A start remains buffered until the first body message. Each transport attempt
changes state **before** awaiting `send`; a failed attempt has an uncertain
delivery outcome and is terminal. No layer may send a second response after a
start attempt. Only confirmed delivery permits an empty terminator for that same
response. Recovery uses the same state machine, and recovery-send exceptions
cannot escape into Uvicorn's default traceback path. Disconnect is terminal.
Correlation context is reset on exit; non-HTTP application behavior is unchanged.

| Lifecycle condition | Delivery rule | Error evidence / server behavior |
| --- | --- | --- |
| Successful response or handled HTTP error | Preserve status/body; one start with correlation header | No unexpected-error event; no raw access record |
| Application failure before start | One generic correlated JSON 500 | One sanitized application event; no Uvicorn traceback |
| Generator failure after buffered start, before first body | Discard buffered start; one generic correlated JSON 500 | Same; real upload and page-image coverage retained |
| Application/generator failure after confirmed start/body | Preserve delivered status/bytes; at most one empty terminator | One sanitized event; no second start |
| Failure after complete response | No additional send | One sanitized event; original completed response retained |
| Transport failure before start is recorded by Uvicorn (`flow.drain`) | Start attempt remains uncertain; close/disconnect cycle | No application retry or Uvicorn fallback 500; sanitized event |
| Transport failure before/while writing start | Terminal uncertain-start state | Same, including failure after a simulated write effect |
| Transport failure at first body or later body | Terminal uncertain-body state | No terminator retry; close/disconnect cycle; sanitized event |
| Transport failure at terminator | Terminal uncertain-end state | No terminator retry; sanitized event, including failed recovery terminator |
| Generic-500 recovery start/body fails | Terminal corresponding uncertain state | No further recovery; no exception-text/traceback logging |
| Disconnect before start, with buffered start, or after body | No further send | Sanitized correlated disconnect evidence; server sees disconnected cycle |
| HTTP cancellation / base-exception failure | Same state rules as other HTTP failures | Contained before Uvicorn's `BaseException` traceback handler |
| Lifespan / WebSocket application invocation | Pass through unchanged | Existing non-HTTP exception semantics preserved |

The existing `status: 500` field classifies unexpected failures. Added
`responseStatus` records the attempted response status (or null), while
`failureState` and `deliveryState` distinguish failure origin and final delivery
knowledge; they do not assert receipt by the client.

## Implementation and finding evidence

- `backend/app/main.py`: explicit delivery states replace completion booleans;
  guarded buffering/delivery/recovery, disconnect observation, HTTP cancellation
  containment, one content-free failure record, and bounded method vocabulary.
- `backend/app/core/http_protocol.py`: small adapter around the pinned Uvicorn
  h11 protocol. A failed send marks its captured request cycle disconnected and
  closes the transport before the application boundary handles the exception.
  This is necessary because stock Uvicorn's `run_asgi` can otherwise attempt its
  own 500 when `flow.drain()` fails before `response_started` becomes true.
- `backend/Dockerfile`: explicitly selects that adapter with `--http
  app.core.http_protocol:PilotH11Protocol` and disables raw access logging with
  `--no-access-log`. The current ECS API definition has no command override.
- Retained Package D tests use shared helpers and representative parameter rows:
  18 direct delivery cases, 17 installed-Uvicorn request cycles, two non-HTTP
  passthrough cases, and the existing real download test parameterized across
  uploads and page images, each with successful, early-failure, and late-failure
  streams. The existing DB-outage correlation case remains.

The effective-server oracle parses the actual Docker CMD with installed
Uvicorn's CLI, creates its real `Config`, loads the selected protocol, checks the
effective access logger/flag, and feeds HTTP bytes through that protocol and
`run_asgi`. It injects write and pre-start flow-control failures and disconnects,
asserts exact send/write counts, and captures application, access, and error
records. Secret sentinels are checked in both rendered logs and raw log-record
fields; exception/stack attachments are absent. Real routes prove authenticated
actor/org/aircraft context and correlation inside the storage generator.

T082-D-004 therefore has builder evidence across application, generator,
transport, recovery, disconnect, and server fallback states. T082-D-007 has
effective production configuration plus success/error request-cycle evidence.
Both require the coordinator's separate adversarial review before disposition.

## Exact bounded checks

From `backend`:

```text
PYTHONPATH=. .venv/bin/pytest -q tests/test_pilot_package_d.py -k 'http_delivery or effective_uvicorn or preserves_non_http'
```

Initial matrix check: **34 passed, 7 deselected, 1 warning in 0.16s**. After
adding the retained production disconnect rows and page-image stream case:

```text
PYTHONPATH=. .venv/bin/pytest -q tests/test_pilot_package_d.py
```

**45 passed, 90 warnings in 3.91s**.

From `frontend/paprnav-frontend`:

```text
npm run test:pilot
```

**3 passed**, no failures.

From `backend`, only directly affected compatibility tests:

```text
PYTHONPATH=. .venv/bin/pytest -q tests/test_mvp_endpoints.py::test_upload_create_download_validation_and_access_boundary tests/test_mvp_endpoints.py::test_ingestion_page_image_download_for_image_upload tests/test_mvp_endpoints.py::test_s3_upload_download_streams_from_configured_bucket tests/test_pilot_release_boundary.py::test_safe_pilot_configuration_disables_all_v4_routes tests/test_pilot_release_boundary.py::test_encoded_path_delimiters_cannot_reach_authentication tests/test_pilot_release_boundary.py::test_decoded_scope_path_and_root_path_gate_without_reading_body tests/test_pilot_release_boundary.py::test_local_environment_retains_v4_route_inventory
```

**8 passed, 84 warnings in 1.99s**.

```text
PYTHONPATH=. .venv/bin/pytest -q --disable-warnings tests/test_pilot_package_c.py::test_three_dockerfiles_are_pinned_non_root_and_bootstrap_inventory_is_sealed
```

**1 passed, 1 warning in 0.06s**.

From the repository root:

```text
git diff --check -- backend/app/main.py backend/app/core/http_protocol.py backend/Dockerfile backend/tests/test_pilot_package_d.py
PYTHONPATH=backend backend/.venv/bin/python -m compileall -q backend/app/main.py backend/app/core/http_protocol.py backend/tests/test_pilot_package_d.py
```

Both **exit 0**, no output. Test warnings concern existing dependency
deprecations, SQLite teardown dependency ordering, pytest temporary-directory
cleanup, and Node module-type detection. No broad suite or cloud/provider call
was run.

## Changed-file hashes

Hashes bind complete current bytes, including pre-existing work in the shared
dirty tree. This handoff does not self-hash.

| File | SHA-256 |
| --- | --- |
| `backend/app/main.py` | `ce2c79461df40a4aed1fac0e312fcaf3ab50ae8d0436a9b9fd56bca17e4ad0c3` |
| `backend/app/core/http_protocol.py` | `e7586e1053a1b592d37b27b2c955ee82a29b5c10bbdd8c3ad44078fb9435a975` |
| `backend/Dockerfile` | `3ca64880d08568ca2720c3217b953b24f5189eff06f2cb72633811e1680d4ed9` |
| `backend/tests/test_pilot_package_d.py` | `6b4fc6d1d5c5d59f7cda3ac54e97194974099d9261c7b75d829078547e81a5d5` |

## Residual Package E limits

The oracle exercises the installed pinned server with in-memory transports; it
does not claim a rebuilt/deployed image, socket/network fault injection, live
CloudWatch retention/delivery, ALB logging, or AWS Budget alert verification.
The reviewed release must include the new protocol module and production command
together; overriding the command/protocol/logging requires new evidence. Uvicorn
upgrades require rerunning this protocol contract oracle. An already delivered
response cannot be replaced, and a disconnected client cannot be guaranteed an
error body or correlation header. A failed logging sink cannot guarantee evidence
delivery; the boundary contains ordinary sink exceptions without default traceback
fallback. Recorded OCR runs still do not prove complete paid-attempt coverage;
provider activation, worker enablement, spend reconciliation, and live operational
verification remain Package E gates.

No models, migrations, T081/0030 artifacts, Terraform, AWS/provider settings,
review ledgers, or prior reports were modified. Nothing was staged or committed.

## Model routing

- Runtime builder identity: `/root/t082_package_d_privacy_remediation_2`.
- Roles: remediation/invariant builder, then focused-verification builder.
- Requested model/effort: `gpt-6-astra`, `xhigh`.
- Actual model: `model not exposed by runtime`.
- Actual effort: `effort not exposed`.
- Trigger: second unsuccessful review and repeated HTTP logging/privacy family;
  complete lifecycle invariant and positive/negative matrix required by
  `.ai/MODEL_ROUTING.md`.
- Repository adversarial-review skill used for the remediation handoff.
  This builder did not assign or act as an independent reviewer; reviewer
  assignment, finding disposition, and closure remain with the coordinator.
