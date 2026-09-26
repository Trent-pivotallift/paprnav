# Package D privacy remediation 3

Date: 2026-09-19. Builder: `/root/t082_package_d_privacy_remediation_3`.
Implements the independently approved D-PRIVACY-AMENDMENT. This supplies evidence
for D004/D007/D008/D009 and PRIV-001/PRIV-002; it changes no finding status and
claims no independent closure.

The stdlib-first production launcher suppresses handler-internal diagnostics
before Uvicorn import/configuration, preserves healthy operational logging,
disables raw access logs, selects the owned protocol, fixes the graceful timeout
at 10 seconds and rejects CLI overrides. Terminal cancellation is safely
classified across plain/pure/mixed groups without serialization or recursive
classification. Captured cycle/transport plus confirmed final-send completion
govern every abort. Completed/non-current old tasks cannot abort successors.

The locked oracle exposed predecessor context inheritance during pipelined task
creation; neutral correlation around the protocol response-complete callback
fixes it while preserving old-task cleanup. Disconnect claims remain limited to
observed I/O; unrelated waits are explicitly observed pending before the real
server shutdown owner cancels them. Deadlines are captured before cleanup.

Full exact commands, invariant matrix, package paths, image metadata, initial
failures and corrections, and Package E limitations are retained in
[the child implementation handoff](../T082-AWS-INVITE-PILOT-D-PRIVACY-AMENDMENT/implementation.md).

## Verification

- Actual Dockerfile + unchanged hash lock, linux/amd64 local image;
  `python -m pytest -q tests/test_pilot_privacy.py` inside /app with network none,
  synthetic configuration and no credentials/mounts: **113 passed, 5 warnings,
  31.91s**.
- Runtime gate derives versions from lock: Python 3.12.11, Uvicorn 0.53.0,
  h11 0.16.0, Starlette 1.6.0, AnyIO 4.15.1, FastAPI 0.141.1; imported modules
  reside in /usr/local/lib/python3.12/site-packages. **pip check passed**.
- Effective fresh-process startup/shutdown/handler graph and sink errors;
  direct/real-Uvicorn delivery; cancellation/backpressure/disconnect/shutdown;
  current/completed/pipelined ownership; real streams/DB outage; non-HTTP and
  four negative controls: **pass**, without skipped gates.
- Parent Package D `PYTHONPATH=. .venv/bin/pytest -q tests/test_pilot_package_d.py`:
  **6 passed**. D005/D006 behavior retained; duplicate privacy matrices moved to
  the backend-only oracle.
- Frontend `npm run test:pilot`: **3 passed**. Bounded direct download/release/
  Docker compatibility command in child handoff: **9 passed**.
- Scoped diff whitespace and changed Python compile checks: **exit 0**.

Final image ID:
`sha256:4e07ccf55d64d8011c712d12095faf01615099bc22070b15a1cf0fd50a80c2db`.
Base:
`python:3.12.11-slim-bookworm@sha256:519591d6871b7bc437060736b9f7456b8731f1499a57e22e6c285135ae657bf7`.
The disposable local image remains available for review; containers were removed.

## Changed-file hashes

Complete bytes, matched in the final image; lock is unchanged.

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

## Residual limits

A failed/partial sink may lose evidence; Pilot operations owns that limitation.
Package E owns live image/command, ALB/socket/CloudWatch/backpressure/retention,
shutdown replacement and Budget verification. One-second local liveness starts
after cancellation delivery to cooperative code. Explicit non-HTTP diagnostics,
blocked loops/console writes and cancellation-suppressing code are outside this
guarantee. Recorded OCR rows still do not establish paid-attempt completeness.
No provider/worker activation, cloud operation, broad suite, migration, model,
Terraform, ledger/state/decision/prior-report change, staging or commit occurred.

## Model routing

- Builder identity: `/root/t082_package_d_privacy_remediation_3`.
- Implementation and focused-verification roles; requested `gpt-6-astra`,
  `xhigh`; actual `model not exposed by runtime`, `effort not exposed`.
- Trigger: approved architecture after the third privacy loop and interacting
  logging, task ownership and exact-runtime invariants.
- Repository adversarial-review skill governed this builder handoff. Coordinator
  `/root` owns independent reviewer assignment and final disposition; no
  self-review or closure attestation is supplied.
