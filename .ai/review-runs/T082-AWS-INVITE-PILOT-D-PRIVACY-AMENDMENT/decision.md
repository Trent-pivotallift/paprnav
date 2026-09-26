# Package D privacy architecture amendment

Parent: `T082-AWS-INVITE-PILOT-D`. Date: 2026-09-19.
Status: proposed; independent design review pending.

## Objective

Close the parent Package D HTTP logging/privacy findings with a minimal
process-start logging policy, safe request/transport ownership, and an exact
locked-runtime oracle. The authoritative decision remains the detailed sections
below; this heading is a validator-visible summary, not a semantic amendment.

## Safety and correctness invariants

HTTP-derived failures and diagnostics cannot expose request or exception
content, authorize a second uncertain send, leak request context to a successor,
or let an old task abort a successor connection. Evidence may be lost when the
sink fails, and disconnect guarantees are limited to owned observable states.

## Proposed design

Use the process launcher, stdlib handler policy, ASGI boundary, protocol adapter,
cycle ownership, cancellation, and disconnect rules defined in `Decision and
gate`, `Ownership and startup`, and `Delivery, backpressure and cancellation`.

## Test strategy

Use the independent bounded matrix and exact locked-image gate defined in
`Shared bounded oracle` and `Exact locked-runtime gate`; do not substitute the
stale developer virtualenv or repository-root-only tests.

## Decision and gate

**No implementation resumes until this amendment receives an independent design
PASS.** The third unsuccessful privacy loop exposed missing process ownership
of logging diagnostics and a missing shared oracle bound to production
dependencies. More individual exception patches do not resolve those gaps.

Use a small production launcher to set `logging.raiseExceptions = False` before
Uvicorn imports/configures logging or imports the application. Retain stdlib
console handlers, the sanitized ASGI boundary, the terminal-send protocol
adapter, and disabled access logging. Treat cancellation as terminal rather than
recovering through a possibly paused transport. Verify the family against the
hash-locked backend image, capturing stderr, raw log records, and HTTP bytes.

This addresses D008/D009 and remaining production proof for D004/D007. D005
(transactional achievement evidence) and D006 (independent OCR cost categories
in the UI) remain closed under remediation-1 review; preserve their behavior,
tests, and evidence. This packet changes no parent finding disposition and
claims no implementation or closure result.

## Evidence and falsifiable invariant

Read authority: parent decision/findings, initial implementation review, both
remediation handoffs/reviews, current `main.py`, protocol/context modules,
Dockerfile/lock, Package D tests, configuration and ECS API launch wiring.
Local Python source confirms `StreamHandler.emit()` catches ordinary
format/write/flush errors internally; `Handler.handleError()` then writes the
exception, traceback, stack and record arguments to stderr when
`raiseExceptions=True`. `lastResort` uses the same machinery; shutdown also
consults that flag. An outer `logger.error()` catch cannot govern this path.

Local Uvicorn configures logging before application load, logs escaped ASGI
`BaseException` with `exc_info`, and waits in `flow.drain()` before marking a
response started. These are observations of Python 3.12.13/Uvicorn 0.52.1,
not production proof: the image pins Python 3.12.11 by digest and the hash lock
pins Uvicorn 0.53.0/h11 0.16.0.

Invariant: HTTP failures, cancellation, and logging failures while reporting
them cannot emit request/exception content through an alternate diagnostic path,
authorize another uncertain send, or let an old request abort a successor.
Once cancellation reaches the owned boundary, cooperative HTTP tasks finish
without another cancellation; disconnect alone has the narrower scope below.
Evidence delivery depends on a working sink; privacy does not.

## Ownership and startup

1. One stdlib-first API launcher owns the process policy. Docker invokes it with
   the existing application/protocol/access-log options. Set the flag before
   importing Uvicorn, constructing `Config`, loading `main:app`, or starting
   lifespan; leave it false through logging shutdown. Do not toggle it per
   request, `create_app()`, or lifespan. Test global variants in subprocesses.
2. `logging.raiseExceptions=False` is authoritative for **stdlib handler-internal
   diagnostics**, including Uvicorn's console and Python's fallback stderr
   handlers. Keep the application catch for ordinary exceptions escaping a
   logging call. Inventory the effective handler graph: a custom handler/filter
   printing outside this contract is not approved implicitly.
3. The ASGI boundary remains the request-content authority. Emit only the
   existing fixed event, route template, bounded method, release, correlation,
   delivery/status fields and authenticated server identifiers. Never attach
   exceptions, `exc_info`, `exc_text`, stacks, raw targets/queries, bodies,
   cookies, credentials, filenames or storage keys. The flag is not a redactor
   and cannot sanitize an explicitly logged traceback.
4. Keep normal `uvicorn.error` operational messages enabled and raw
   `uvicorn.access` disabled. The reviewed launcher must not permit TRACE/debug
   or other launch overrides to bypass these settings. Contain all HTTP
   failures before Uvicorn's traceback/fallback-500 path; no Uvicorn error
   record is expected for a contained HTTP failure.
5. Lifespan/WebSocket control flow remains pass-through; the global handler
   policy also applies during startup and shutdown. This is an HTTP-content
   plus handler-failure guarantee, not blanket redaction of independently
   logged non-HTTP exceptions, direct stderr writes, interpreter fatal errors,
   or native diagnostics. The current app has no custom lifespan handler or
   WebSocket routes. New non-HTTP producers, handlers or launch paths require
   review of their content boundary; do not imply they are covered by this flag.
6. Drop a failed logging attempt without formatting the sink exception,
   recursively logging it, retrying, or opening another sink/file/DB write.
   Failed/partial writes may lose or truncate a safe event. Preserve response
   policy and correlation cleanup. A healthy sink still receives one sanitized
   event per unexpected request failure; a broken sink provides no delivery
   guarantee. Absence of errors never establishes success. Pilot operations
   owns this evidence-loss limitation and Package E verifies live delivery.

## Delivery, backpressure and cancellation

Preserve buffering and marking delivery attempted **before** awaiting send.
Only NEW/PENDING application errors may become a generic correlated 500.
Confirmed STARTED/STREAMING permits at most one same-response terminator.
Uncertain start/body/end, observed disconnect, or completion permits no further
send. Recovery follows the same rules.

**Connection ownership (PRIV-001):** capture the request cycle and transport
identity at wrapper entry. A request's permission to close the connection ends
when its final send returns successfully or the protocol's current cycle changes
to a successor, whichever occurs first. Immediately before any adapter close,
with no intervening await, require both captured identities still match the
protocol and that this request has not confirmed final-send completion. Apply
this rule to every abort path, including transport failures and cancellation.
Uvicorn's `response_complete` alone is insufficient: it may become true before
the final transport write succeeds. Track successful final-send return at the
owned boundary; an uncertain final write on a still-current cycle may still
require closing it. A non-current cycle must never close the shared transport,
even if its own wrapper has not yet observed final-send return.

| Cancellation target | Required action |
| --- | --- |
| Current, incomplete request | Emit at most one safe cancellation event, reset context, mark its cycle disconnected/disable its keep-alive, and close only under the ownership check; no recovery send. |
| Completed request, with or without a successor | Consume cancellation after request-local logging/context cleanup. No send, transport close or successor mutation. Preserve the completed response and connection. |
| Non-current request whose task still unwinds | Clean up only that request. If incomplete, mark only its captured cycle disconnected to prevent its own fallback; never close the transport or change the current cycle. |

The middleware passes cancellation to the owned HTTP protocol wrapper, which
consumes it before `run_asgi` can log it. Classify by exception **types**, never
messages/repr/tracebacks: a plain `CancelledError`, an all-cancellation group,
and a mixed nested group containing any cancellation leaf are terminal with no
response recovery. Use fixed `cancelled`/`cancelled_group` classifications; the
mixed group's other failures remain failures, are not re-raised to Uvicorn, and
are not serialized. Groups without cancellation keep ordinary sanitized error
handling. Preserve non-HTTP propagation. Cancellation during recovery follows
the same ownership rules.

**Disconnect scope (PRIV-002):** do not add a disconnect watcher/task owner.
Receive/send/drain interception owns only disconnects observed through those
operations: prohibit subsequent sends and unwind interrupted delivery using the
terminal rules. Normal paused output resumes without dropped bytes. A
cooperative application exiting on an observed disconnect must finish without
flow resumption or another cancellation. Receiving disconnect does not compel
application code to exit; code suspended at an unrelated await, or ignoring
disconnect after receive, may remain pending. Do not claim disconnect alone
terminates such a task.

Uvicorn's registered request-task owner supplies termination during graceful
shutdown: stop accepting traffic, allow the explicit 10-second grace period,
then issue cancellation to remaining tasks. The owned boundaries must finish
cooperative suspended tasks within one second **after cancellation is delivered**
in the local oracle, without a second cancellation. Verify shutdown with a
shorter injected grace timeout. This is not a ten-second hard process-exit
promise: an application that suppresses cancellation, a blocked event loop, or
an indefinitely blocked console write is outside that local liveness bound and
remains a Package E operational limit.

## Shared bounded oracle

Retain one matrix with independent expected transitions/counts; do not compute
expectations from implementation state. Exercise direct ASGI and real configured
Uvicorn cycles, retaining real upload/page-image success/early/late failures and
the DB-outage correlation case.

| Dimension | Required positive and negative cases |
| --- | --- |
| Startup | Fresh process: flag false before Uvicorn configuration/app import, after lifespan and through shutdown; effective CMD, protocol, access setting and handlers verified. Healthy application and ordinary server records still emit. Non-HTTP control flow is preserved. |
| Delivery | Success/handled HTTP error; failures before start, buffered, first/later body, completed; start/body/end send failures before/after simulated write effect; recovery start/body/end failures; disconnect before/buffered/streaming. Assert exact attempts/starts, status/bytes, close and context reset. |
| Sink | Healthy, formatter error, write error before/after partial effect, flush error, shutdown flush error. Inject distinct secret-bearing ordinary exceptions into effective Uvicorn and fallback handlers using real `handleError`; capture stderr/stdout separately from the failing stream and inspect raw records. No traceback, secret, recursive/fallback emission; allow lost/truncated safe output. Restore sink and prove later logging works. |
| Flow/cancellation | Actual pause/resume success; drain raises; paused drain then disconnect; single cancellation before start, during body/recovery and at an unrelated application await; plain, pure-grouped and mixed/nested cancellation. Cooperative observed-I/O exits finish within one second of observation; cancellation cases finish within one second of delivery. No recovery retry or second cancellation. |
| Disconnect/shutdown | Hold an application at an event-controlled unrelated await, disconnect, then record that its task is still pending before any cleanup. Invoke the real server shutdown/task owner with a short grace timeout; prove cancellation is issued and then the one-second cooperative-task completion bound. Initial pending observation is expected here, not a failed claim of automatic disconnect termination. |
| Isolation/ownership | Sequential/keep-alive requests and overlapping pipelined tasks have distinct context. Complete old response A while successor B remains incomplete, cancel A (plain/grouped), and prove no close or B mutation and successful completion of B. Also cancel a completed current cycle without a successor, a current incomplete cycle, and a non-current old task. Retain uncertain final-write failure even when Uvicorn has set `response_complete`. Invalid correlation is replaced; success/HTTP errors/unexpected errors never create raw access or private diagnostic records. |
| Negative controls | Version mismatch fails before cases; enabling access logs is detected; restoring `raiseExceptions=True` with a failing handler is detected; bypassing the adapter on pre-start drain failure is detected. Mutations are isolated test-process changes. |

For each liveness case, capture task/transport/state and deadline outcome
**before** cleanup. A case expecting completion fails on timeout even if later
cleanup cancellation releases it. Only the explicitly pending-disconnect case
expects an initial live task; its subsequent shutdown is a separate asserted
phase. Use non-cancelling deadline observation (for example, a timed task wait),
then separate cleanup, so the measurement cannot cancel the subject silently.

## Exact locked-runtime gate

Build a disposable **local** backend image from the actual Dockerfile and
unchanged `requirements.lock`, targeting `linux/amd64` as compiled in the lock.
Run the focused oracle inside it with network disabled, synthetic configuration,
no host credentials or developer venv, and retained source/tests; pytest is
already locked. The image oracle must be self-contained under `/app`: retain a
dedicated backend-only `tests/test_pilot_privacy.py` containing this matrix,
real streaming-route cases and the runtime DB-outage/correlation assertions.
Run `python -m pytest -q tests/test_pilot_privacy.py` from `/app`. Resolve the
backend Dockerfile and lock from that backend root; use only backend fixtures,
synthetic data and temporary files. Do not collect the mixed Package D static
Terraform gate or require `/infra`, frontend files, a repository parent, host
mounts, or UI tests. Keep those separate repository compatibility checks intact.
Record source/Dockerfile/lock hashes, base/image IDs, Python
version, imported package versions and module paths. Assert imported Uvicorn
equals the unique lock pin (currently 0.53.0), h11 equals its pin, and `pip check`
passes. Derive expected versions from the lock rather than an independent
hard-coded value. Inspect relevant **locked** server source and exercise the
same effective launcher configuration; a skipped check is not a passing gate.

If Docker is unavailable, a fresh Python 3.12 disposable environment installed
with `--require-hashes -r backend/requirements.lock` may prove exact dependency
behavior, with platform/Python differences recorded. The built-image gate still
remains before production closure. Never upgrade the shared `.venv` or relabel
its results as pinned-runtime proof. This design pass ran no locked oracle and
built no image; Docker inspection was unavailable in the sandbox. Any locked
source incompatibility returns to design rather than an undocumented patch.

## Alternatives and affected scope

- Only catch `logger.error()`, patch the protocol, or set the flag in lifespan:
  rejected because none governs early process-wide handler diagnostics.
- Custom handlers, queues, emergency sinks, global traceback redaction or a
  logging service: rejected for this slice; they add sink/recursion/liveness or
  content-classification policies beyond the required stdlib-handler guarantee.
- Disable all logging: rejected because healthy sanitized evidence and ordinary
  operational messages remain needed. The flag alone is also insufficient for
  explicitly logged `exc_info`; preserve the HTTP boundary.
- Trust the stale venv, mock `logger.error`, or inspect only Docker text:
  rejected because those miss effective handler, stderr and dependency behavior.

After design PASS, the coherent slice may write the small launcher, Docker CMD,
`app/main.py`, `app/core/http_protocol.py`, focused Package D tests and new review
evidence. Read dependencies include `backend/main.py`, request context,
configuration/import order, both streaming-route consumers, locked Python/
Uvicorn/Starlette/AnyIO behavior and ECS API wiring (currently no command
override). Operators and Package E read console events/correlation headers.
Runtime writes are logging configuration, console events and HTTP bytes.
There is no DB/schema/event rewrite, provider call, worker activation, AWS write
or UI change. Preserve D005/D006 and adjacent compatibility evidence.

| Remaining phase | Risk / complexity / centrality / uncertainty (1–5) | Dependency and route |
| --- | --- | --- |
| Independent design | 4 / 4 / 5 / 3 | This packet; Astra xhigh |
| Remediation and locked oracle | 4 / 4 / 5 / 4 | Design PASS; Astra xhigh after repeated failures |
| Implementation/closure review | 4 / 4 / 5 / 3 | Complete matrix and bound runtime evidence; independent Astra xhigh |

## Impact, rollback and live limits

Failure can disclose content, lose operational evidence, or stall shutdown.
The launcher, command, cancellation behavior and protocol form one reversible
image change with no data migration. Roll them back together; never leave a
launcher/protocol mismatch. Returning to the currently known privacy defects is
not an approved pilot release: keep deployment gated or stop pilot traffic until
a reviewed image exists. Lost sink evidence cannot be reconstructed by rollback.

Package E owns deployed image/command identity, real socket/ALB behavior,
CloudWatch routing/delivery/retention and permissions, console backpressure,
graceful task replacement and Budget alert proof. In-memory transports do not
prove these. OCR remains recorded-run-only; provider activation, worker
enablement, paid-attempt completeness and billing reconciliation remain separate
gates.

## Model routing

- Builder identity: `/root/t082_package_d_privacy_amendment_design`; role:
  architecture/invariant builder, not independent reviewer.
- Requested: `gpt-6-astra`, `xhigh`. Actual model: `model not exposed by runtime`.
  Actual effort: `effort not exposed`.
- Trigger: third unsuccessful privacy loop, interacting process/ASGI/protocol
  ownership and absent shared version/sink/cancellation oracle; this amendment
  pass resolves the design of PRIV-001/PRIV-002, not their independent closure.
- Coordinator: `/root`. Initial independent reviewer:
  `/root/t082_package_d_privacy_review_2`; requested `gpt-6-astra`, `xhigh`,
  actual model `model not exposed by runtime`, effort `effort not exposed`.
  Its immutable `adversarial-design-initial.md` reports FAIL. Independent
  re-review and a recorded PASS remain required before implementation.
