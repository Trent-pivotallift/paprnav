# Privacy amendment implementation

Date: 2026-09-19. Builder evidence only; independent review and closure remain
required. Authority: child decision, design-remediation-1, and independent
adversarial-design-final PASS. Parent findings D004/D007/D008/D009 and child
PRIV-001/PRIV-002 are addressed by this slice; no finding disposition is changed.

## Implementation

The production CMD now invokes `python -m pilot_server`. Its stdlib-first
launcher sets `logging.raiseExceptions=False` before Uvicorn import/configuration
or application loading, retains INFO operational logging, disables access logs,
selects PilotH11Protocol, fixes graceful shutdown to 10 seconds, and rejects CLI
arguments. Handler failures may lose/truncate safe evidence; there is no retry,
emergency sink, recursive logging, or DB fallback.

Cancellation classification uses only types and an iterative group traversal.
Plain, pure-grouped, and mixed cancellation never initiate recovery sends.
Middleware emits at most one safe event, resets request context and passes
cancellation to the protocol, which consumes it before Uvicorn's traceback path.
Every abort checks successful final-send return and synchronously matches captured
cycle/transport identities before closing. Non-current incomplete cycles only
change their own state; completed cycles do not change their transport/successor.
Observed disconnects stop delivery; unrelated waits remain pending until the real
server task owner cancels them. Non-HTTP failures propagate unchanged.

The full-image oracle exposed inherited predecessor correlation after pipelined
task creation. The protocol now clears correlation around Uvicorn's synchronous
response-complete callback and restores the old task's context afterward.
`set_correlation_id` accepts None for this neutral task-creation context. This
implements the approved isolation invariant; no dependency incompatibility or
architecture deviation was found.

Privacy matrices, real streaming-route cases and runtime DB-outage assertions
moved into backend-only `tests/test_pilot_privacy.py`. Parent Package D retains
six achievement/cost/static-gate tests, including unchanged D005/D006 behavior.

## Locked-image evidence

Exact final build from repository root:

```text
docker build --platform linux/amd64 --tag paprnav-privacy-remediation-3:local backend
docker run --rm --platform linux/amd64 --network none --env PAPRNAV_DISABLE_DOTENV=1 --env DATABASE_URL=sqlite+pysqlite:///:memory: --env AWS_EC2_METADATA_DISABLED=true --env PAPRNAV_ENV=local paprnav-privacy-remediation-3:local python -m pytest -q tests/test_pilot_privacy.py
```

Result: **113 passed, 5 warnings in 31.91s**. No skipped gate. The container runs
from /app as 10001:10001, without host mounts, host credentials, frontend,
Terraform or repository-parent dependencies. Docker access used the scoped
execution permission; containers were removed. The local image remains available
for independent review.

- Base reference: `python:3.12.11-slim-bookworm@sha256:519591d6871b7bc437060736b9f7456b8731f1499a57e22e6c285135ae657bf7`.
- Final Docker image ID: `sha256:4e07ccf55d64d8011c712d12095faf01615099bc22070b15a1cf0fd50a80c2db`.
- Linux/amd64 manifest: `sha256:473af8f1ae19d30d368ecd8b2c35f0652ebba109fc830fe841c66925e0c26c76`.
- Image configuration: `sha256:6ff9a2238f2f5ed54ab27ed62a5367c4c86e63787b210b432c36cf32867c8bab`.
- Python 3.12.11, GCC 12.2.0; Linux 6.12.76-linuxkit x86_64, glibc 2.36.
- Imported Uvicorn 0.53.0, h11 0.16.0, Starlette 1.6.0, AnyIO 4.15.1,
  FastAPI 0.141.1. Each module path is
  `/usr/local/lib/python3.12/site-packages/<name>/__init__.py`.
- The module gate derives each unique expected version from requirements.lock,
  asserts imported agreement before cases, and runs `python -m pip check`.
  An additional final-image pip check returned **No broken requirements found**.
- Inspected locked RequestResponseCycle.send/run_asgi, FlowControl,
  H11Protocol.on_response_complete/connection_lost, and Server.shutdown.
  Effective launcher/protocol/access/handler graph is executed in fresh processes.

| Invariant family | Final result |
| --- | --- |
| Startup, operational logging, handler graph, shutdown policy, override rejection | Pass |
| Formatter/write/partial-write/flush/shutdown-flush failures in effective Uvicorn and fallback handlers, real handleError, later healthy sink; fallback request retains generic 500/context cleanup | Pass |
| Direct delivery and real server cycles: before/buffered/streaming/completed errors, uncertain start/body/end before/after write effect, recovery failures and observed disconnect | Pass |
| Plain/pure/mixed cancellation before send, body, recovery and unrelated await; no second cancellation or recovery send | Pass |
| Actual paused-output resume preserves bytes; paused-output disconnect finishes within one second | Pass |
| Unrelated-await task is observed pending after disconnect; actual Server.shutdown issues cancellation after injected short grace; cooperative request finishes within one second | Pass |
| Completed-current/pipelined-successor/non-current-incomplete/different-transport ownership; uncertain final write despite response_complete; sequential/pipelined correlation isolation | Pass |
| Non-HTTP propagation; ordinary groups recover; deeply nested classification does not serialize or recurse | Pass |
| Real upload/page-image success and early/late stream failure; DB outage and invalid correlation replacement | Pass |
| Negative controls: version mismatch, enabled access logs, raiseExceptions=True and adapter bypass all detected | Pass |

Deadline observations use asyncio.wait before separate cleanup; cleanup cannot
turn a missed deadline into a pass. Early harness runs were stopped for missing
synthetic lifespan setup; the first complete run had 108 pass/3 fail for inherited
pipelined correlation. That correction passed 112 cases, then the final iterative
group robustness case produced the 113-case result above.

## Bounded local checks

From backend: `PYTHONPATH=. .venv/bin/pytest -q tests/test_pilot_package_d.py`:
**6 passed**. This is compatibility evidence, not locked-runtime proof.

From frontend/paprnav-frontend: `npm run test:pilot`: **3 passed**.

From backend:

```text
PYTHONPATH=. .venv/bin/pytest -q --disable-warnings tests/test_mvp_endpoints.py::test_upload_create_download_validation_and_access_boundary tests/test_mvp_endpoints.py::test_ingestion_page_image_download_for_image_upload tests/test_mvp_endpoints.py::test_s3_upload_download_streams_from_configured_bucket tests/test_pilot_release_boundary.py::test_safe_pilot_configuration_disables_all_v4_routes tests/test_pilot_release_boundary.py::test_encoded_path_delimiters_cannot_reach_authentication tests/test_pilot_release_boundary.py::test_decoded_scope_path_and_root_path_gate_without_reading_body tests/test_pilot_release_boundary.py::test_local_environment_retains_v4_route_inventory tests/test_pilot_package_c.py::test_three_dockerfiles_are_pinned_non_root_and_bootstrap_inventory_is_sealed
```

**9 passed**. Scoped git diff --check and compileall of changed Python files:
**exit 0**. Warnings concern existing deprecations/SQLite teardown and local pytest
temporary-directory cleanup; no broad suite, cloud or provider operation ran.

## Source binding

These complete-file hashes match both working tree and final image. They include
pre-existing shared changes; the lock was not modified.

| Backend file | SHA-256 |
| --- | --- |
| `pilot_server.py` | `654360f675b07b821a13f50984e11626e26b9e48671051ae988d48b04979ce33` |
| `Dockerfile` | `c820c3dfa260b84e87bc5819fa5f5634139ee78477e1691ca9ed43402638d7c7` |
| `app/main.py` | `4038b6e0c885c07c8cb618eeb8b9f83fb4d0c9007209e6c447ad4f1343e6fc67` |
| `app/core/http_protocol.py` | `6637260d2e6a3ea33ba8d92fc9afb9930a68a31851d4fc75f48b264ea3f7c111` |
| `app/core/request_context.py` | `fa76d8621cd0990107f3a7b965515764a88b67950b5290eb7b4e667748d61540` |
| `tests/test_pilot_privacy.py` | `e964a838bef83270d47bf380076c08dc0b2465a303264a2b80454552d7def976` |
| `tests/test_pilot_package_d.py` | `ab7a29bbd966c9ccf7889b6aa346d11323a6fe53ff082d726f8ffb5f88095871` |
| `requirements.lock` (unchanged) | `729a4a4316e863db493204ecc103c41943162cb7986af3fe5669a10e8d66462d` |

## Residual limits and ownership

Pilot operations owns evidence loss with an unavailable sink; absence of errors
does not establish success. Package E still must prove deployed image/command,
socket/ALB behavior, CloudWatch delivery/retention/permissions, console
backpressure, graceful replacement and Budget alerts. The local one-second bound
begins after cancellation reaches cooperative code, not at disconnect; blocked
loops, suppressed cancellation and indefinitely blocked console writes remain
outside it. Non-HTTP explicit exception logging/direct stderr/native diagnostics
are not blanket-redacted. OCR is still recorded-run-only; no provider/worker or
billing-completeness gate is opened. Roll back launcher/protocol/command together.

No models, migrations, T081/0030, Terraform, AWS/provider settings, ledgers,
attestations, decisions, state or prior reports were edited. Nothing was staged
or committed. The adversarial-review skill governed builder evidence; this
artifact is not independent closure.

## Model routing

- Builder runtime: `/root/t082_package_d_privacy_remediation_3`.
- Roles: implementation/remediation builder, then focused-verification builder.
- Requested: `gpt-6-astra`, `xhigh`; actual: `model not exposed by runtime`,
  `effort not exposed`.
- Trigger: independently approved architecture after the third privacy loop;
  interacting handler diagnostics, cancellation/cycle ownership and locked proof.
- Coordinator: `/root`. Approved design reviewer:
  `/root/t082_package_d_privacy_review_2`, actual `model not exposed by runtime`,
  `effort not exposed`. Independent implementation/closure assignment remains
  with the coordinator.
