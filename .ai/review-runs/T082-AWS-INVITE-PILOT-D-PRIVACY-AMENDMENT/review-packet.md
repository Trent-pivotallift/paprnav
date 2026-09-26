# Review packet: T082-AWS-INVITE-PILOT-D-PRIVACY-AMENDMENT

Stage: closure
Generated: 2026-09-19T22:11:56+00:00
Base: `HEAD`
Head: `19fe8e2e170687ed65deed78cb1af99d60f601e9`
Scope fingerprint: `eb7f8d120061d36f7502149756ad57dc56d3bbf6bda17ffc6e8e182bb4260346`

## Reviewer instructions

Read `.ai/agents/ADVERSARIAL_REVIEWER.md`. Inspect repository files directly.
Treat the manifest as a starting point and report missing consumers or unjustified
scope exclusions as findings.

## Decision packet

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


## Current finding ledger

```json
[
  {
    "id": "PRIV-001",
    "stage": "design",
    "reviewer": "/root/t082_package_d_privacy_review_2",
    "severity": "high",
    "status": "closed",
    "invariant": "Cancellation of an older completed or non-current request cannot close a transport now owned by a successor request.",
    "summary": "The proposed unconditional captured-cycle transport close can abort an overlapping keep-alive successor.",
    "evidence": ["adversarial-design-initial.md", "decision.md", "backend/app/core/http_protocol.py"],
    "impact": "A prior request's cancellation can terminate an unrelated in-flight successor response on the same client connection.",
    "requiredClosure": "Define connection ownership transfer and a current-cycle close rule, with overlapping and grouped-cancellation evidence.",
    "closureEvidence": ["decision.md", "design-remediation-1.md", "adversarial-design-final.md"]
  },
  {
    "id": "PRIV-002",
    "stage": "design",
    "reviewer": "/root/t082_package_d_privacy_review_2",
    "severity": "medium",
    "status": "closed",
    "invariant": "Disconnect and shutdown guarantees match the states observable by the application and server task owners.",
    "summary": "A disconnected cycle can coexist with application code suspended away from receive/send, so disconnect alone does not finish the request.",
    "evidence": ["adversarial-design-initial.md", "decision.md"],
    "impact": "The design overstates liveness and its oracle can hide a pending task during cleanup.",
    "requiredClosure": "Define a safe task owner or narrow the guarantee to observed I/O states and separately own bounded shutdown of unrelated waits.",
    "closureEvidence": ["decision.md", "design-remediation-1.md", "adversarial-design-final.md"]
  },
  {
    "id": "PRIV-CLOSURE-001",
    "stage": "closure",
    "reviewer": "/root/t082_package_d_closure_review",
    "severity": "blocker",
    "status": "closed",
    "invariant": "Closure records exact model and effort disclosure wording for every meaningful phase and the closure reviewer assignment.",
    "summary": "The child closure model summary is incomplete and uses ambiguous shorthand.",
    "evidence": ["adversarial-closure-initial.md", "closure.md", ".ai/MODEL_ROUTING.md"],
    "impact": "The child run cannot close under mandatory routing-evidence policy.",
    "requiredClosure": "Use exact wording and enumerate design remediation, focused verification, coordinator, and closure-review assignments.",
    "closureEvidence": ["closure.md", "adversarial-closure-initial.md", "adversarial-closure-remediation.md"]
  },
  {
    "id": "PRIV-CLOSURE-002",
    "stage": "closure",
    "reviewer": "/root/t082_package_d_closure_review",
    "severity": "blocker",
    "status": "closed",
    "invariant": "The decision packet exposes the validator-required Objective, Safety and correctness invariants, Proposed design, and Test strategy sections.",
    "summary": "The approved decision has equivalent substance but lacks the exact required headings.",
    "evidence": ["adversarial-closure-initial.md", "decision.md"],
    "impact": "The review-run validator cannot close the child run.",
    "requiredClosure": "Add non-semantic heading anchors referencing the approved design without changing it.",
    "closureEvidence": ["decision.md", "adversarial-closure-initial.md", "adversarial-closure-remediation.md"]
  },
  {
    "id": "PRIV-CLOSURE-003",
    "stage": "closure",
    "reviewer": "/root/t082_package_d_closure_review",
    "severity": "blocker",
    "status": "closed",
    "invariant": "The fresh child closure packet hash-binds the active modified model-routing policy.",
    "summary": "The child closure packet omits .ai/MODEL_ROUTING.md.",
    "evidence": ["adversarial-closure-initial.md", "manifest.json", ".ai/MODEL_ROUTING.md"],
    "impact": "Closure cannot prove compliance with its governing policy.",
    "requiredClosure": "Add .ai/MODEL_ROUTING.md as a closure review input and regenerate the packet.",
    "closureEvidence": ["closure.md", "adversarial-closure-initial.md", "adversarial-closure-remediation.md", ".ai/MODEL_ROUTING.md"]
  }
]

```

## Hash-bound review inputs

### `.ai/review-runs/T082-AWS-INVITE-PILOT-D-PRIVACY-AMENDMENT/decision.md`

size=19689; sha256=422d36b8d4ed85953771733d727d65ee3d5ef0dbf2f1525168d5db0808bdcfb8

```text
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

```
### `.ai/review-runs/T082-AWS-INVITE-PILOT-D-PRIVACY-AMENDMENT/findings.json`

size=4148; sha256=a44b813a2fc0f153af140b31d183b3514f4dc27cea593ee18240805428533194

```text
[
  {
    "id": "PRIV-001",
    "stage": "design",
    "reviewer": "/root/t082_package_d_privacy_review_2",
    "severity": "high",
    "status": "closed",
    "invariant": "Cancellation of an older completed or non-current request cannot close a transport now owned by a successor request.",
    "summary": "The proposed unconditional captured-cycle transport close can abort an overlapping keep-alive successor.",
    "evidence": ["adversarial-design-initial.md", "decision.md", "backend/app/core/http_protocol.py"],
    "impact": "A prior request's cancellation can terminate an unrelated in-flight successor response on the same client connection.",
    "requiredClosure": "Define connection ownership transfer and a current-cycle close rule, with overlapping and grouped-cancellation evidence.",
    "closureEvidence": ["decision.md", "design-remediation-1.md", "adversarial-design-final.md"]
  },
  {
    "id": "PRIV-002",
    "stage": "design",
    "reviewer": "/root/t082_package_d_privacy_review_2",
    "severity": "medium",
    "status": "closed",
    "invariant": "Disconnect and shutdown guarantees match the states observable by the application and server task owners.",
    "summary": "A disconnected cycle can coexist with application code suspended away from receive/send, so disconnect alone does not finish the request.",
    "evidence": ["adversarial-design-initial.md", "decision.md"],
    "impact": "The design overstates liveness and its oracle can hide a pending task during cleanup.",
    "requiredClosure": "Define a safe task owner or narrow the guarantee to observed I/O states and separately own bounded shutdown of unrelated waits.",
    "closureEvidence": ["decision.md", "design-remediation-1.md", "adversarial-design-final.md"]
  },
  {
    "id": "PRIV-CLOSURE-001",
    "stage": "closure",
    "reviewer": "/root/t082_package_d_closure_review",
    "severity": "blocker",
    "status": "closed",
    "invariant": "Closure records exact model and effort disclosure wording for every meaningful phase and the closure reviewer assignment.",
    "summary": "The child closure model summary is incomplete and uses ambiguous shorthand.",
    "evidence": ["adversarial-closure-initial.md", "closure.md", ".ai/MODEL_ROUTING.md"],
    "impact": "The child run cannot close under mandatory routing-evidence policy.",
    "requiredClosure": "Use exact wording and enumerate design remediation, focused verification, coordinator, and closure-review assignments.",
    "closureEvidence": ["closure.md", "adversarial-closure-initial.md", "adversarial-closure-remediation.md"]
  },
  {
    "id": "PRIV-CLOSURE-002",
    "stage": "closure",
    "reviewer": "/root/t082_package_d_closure_review",
    "severity": "blocker",
    "status": "closed",
    "invariant": "The decision packet exposes the validator-required Objective, Safety and correctness invariants, Proposed design, and Test strategy sections.",
    "summary": "The approved decision has equivalent substance but lacks the exact required headings.",
    "evidence": ["adversarial-closure-initial.md", "decision.md"],
    "impact": "The review-run validator cannot close the child run.",
    "requiredClosure": "Add non-semantic heading anchors referencing the approved design without changing it.",
    "closureEvidence": ["decision.md", "adversarial-closure-initial.md", "adversarial-closure-remediation.md"]
  },
  {
    "id": "PRIV-CLOSURE-003",
    "stage": "closure",
    "reviewer": "/root/t082_package_d_closure_review",
    "severity": "blocker",
    "status": "closed",
    "invariant": "The fresh child closure packet hash-binds the active modified model-routing policy.",
    "summary": "The child closure packet omits .ai/MODEL_ROUTING.md.",
    "evidence": ["adversarial-closure-initial.md", "manifest.json", ".ai/MODEL_ROUTING.md"],
    "impact": "Closure cannot prove compliance with its governing policy.",
    "requiredClosure": "Add .ai/MODEL_ROUTING.md as a closure review input and regenerate the packet.",
    "closureEvidence": ["closure.md", "adversarial-closure-initial.md", "adversarial-closure-remediation.md", ".ai/MODEL_ROUTING.md"]
  }
]

```
### `.ai/MODEL_ROUTING.md`

size=10194; sha256=043890c6138ba45f88dcb8a4ea209d288f4a8e8625cf60d9127408c1ff240261

```text
# Paprnav model-routing policy

This policy is mandatory for every Codex task in this repository. Route each
meaningful phase independently; do not choose one model for an entire task when
later phases have different risk or review needs.

## Routing tiers

Choose the highest tier triggered by the work. Complexity, safety impact, and
review history override convenience or expected speed.

| Work | Preferred routing |
| --- | --- |
| Mechanical, localized, low-risk edits with an obvious oracle and limited blast radius | GPT-5.6 Luna (`gpt-5.6-luna`) or GPT-5.6 Terra (`gpt-5.6-terra`), medium |
| Coherent multi-file implementation whose design is already approved | GPT-5.6 Sol (`gpt-5.6-sol`), high |
| Schema or migration design; authorization; regulatory or safety semantics; invariant synthesis; adversarial review; closure review | GPT-6 Astra (`gpt-6-astra`), high or xhigh |

Use xhigh for interacting invariants, ambiguous trust boundaries, concurrency or
rollback reasoning, closure after substantive findings, or when high effort has
not resolved the review class. Use high for a well-framed problem with explicit
invariants and a strong test oracle.

Low-risk routing applies only when all of these are true:

- the change is localized and mechanically checkable;
- failure cannot alter authorization, regulatory meaning, safety behavior,
  persisted schema, audit evidence, billing/provider choice, or a public
  contract;
- rollback is straightforward; and
- no review-history escalation below applies.

When a phase mixes tiers, use the highest triggered tier or split it into
bounded phases with explicit handoffs. An approved design is required before
routing coherent high-risk implementation to Sol; design and invariant work
remain Astra work.

## Risk-adjusted planning and review cadence

For multi-phase work, score each remaining package independently from 1 (low)
to 5 (high) on risk, technical complexity, dependency centrality, and
uncertainty. Record dependencies, downstream consumers, reversibility, the
strength of deterministic oracles, design-approval state, and relevant review
history. File count and apparent edit size are not risk scores: a one-line ACL
or migration change can be high-risk, while a large generated rewrite can be
mechanical.

Optimize expected total effort, including likely rework and review cost. Route
to Astra earlier when ambiguity, centrality, or repeated findings make a Sol
pass likely to require another implementation/review loop. Conversely, use
Terra medium or Sol medium for deterministic work mechanically derived from an
approved authority, even when it touches many generated files.

Review once at each meaningful invariant-bearing family boundary:

- review a coherent design together with its generated contracts, manifests,
  hashes, counts, and deterministic validator results;
- do not create standalone reviewer turns for each generated artifact or for
  mechanical implementation that stays within the approved design;
- request one implementation review after the coherent family and its full
  positive/negative evidence are complete;
- repeat a review or broad test only when changed dependencies can invalidate
  prior evidence; and
- retain independent design, implementation, and closure review for high-risk
  schema, migration, authorization, regulatory, IAM, or invariant work.

If an agent has completed the technical analysis but continues expanding prose,
direct it to publish a compact reviewable artifact and return. Drafting length
is not additional verification.

## Review-history escalation

Count substantive failures within the current finding family or review loop.
Formatting-only feedback and infrastructure/transient failures do not count.

1. After the first substantive failed review, increase reasoning effort for the
   next pass and reassess whether the issue is a local defect, a missing
   invariant, a design error, an oracle gap, or a scope omission.
2. After the second failed review, or whenever the same finding family recurs,
   route the next pass to GPT-6 Astra and stop counterexample-by-counterexample
   patching. Restate the complete invariant and close the coherent family with
   its positive and negative matrix.
3. After the third unsuccessful loop, pause implementation. Identify and record
   the missing invariant, architecture decision, or shared test oracle before
   further code changes. Resume only after that gap is resolved and, for work
   governed by the adversarial-review process, independently reviewed.

Examples:

- A first concurrency-review failure moves the next pass to higher effort and
  reclassifies the issue as lock ordering, transaction isolation, or test
  coverage before editing.
- A second malformed-row counterexample in the same schema family moves the
  work to Astra and replaces one-off trigger patches with a complete union and
  corruption matrix.
- A third reconstruction mismatch stops implementation until the canonical
  mapping invariant and shared oracle are explicit.

Escalation never authorizes broader product scope or bypasses an approval gate.

## Builder and reviewer separation

Builder/reviewer separation is mandatory regardless of model. A model upgrade
does not make self-review independent. Qualifying work must still follow
`AGENTS.md`, `.ai/REVIEW_PROCESS.md`, and the repository-local
`adversarial-review` skill.

- Assign design, implementation, and closure adversaries as separate read-only
  project subagents unless the coordinator explicitly assigns a later fix task.
- Do not let the builder attest its own review stage, even when builder and
  reviewer would use the same model family.
- Record the actual runtime reviewer identity; a model name is not an identity.

## Dynamic availability and fallbacks

Use the preferred model when it is available. Otherwise choose the closest
available capability tier that can safely perform the phase:

1. For Astra-routed work, prefer the strongest available model at high or xhigh
   and preserve the mandatory independent-review gates. If no available model
   is adequate for the risk, pause and report the limitation.
2. For Sol-routed work, fall back to Astra at high, or to the strongest
   available implementation model at high when Astra is unavailable.
3. For Luna/Terra-routed work, use the other model at medium, then the closest
   available general implementation tier at medium.

Never silently claim or imply use of an unavailable model. In the phase notice
and any review artifact, record the actual fallback model and the reason. If the
runtime does not expose its model, write exactly `model not exposed by runtime`
rather than inferring it. If effort is not exposed, say `effort not exposed`.

## Required status commentary

At the start of every meaningful phase, report the role, exact model, reasoning
effort, and routing trigger. Report again whenever the role, model, or effort
changes. A meaningful phase includes framing/design, implementation, focused
verification, adversarial review, remediation after a failed review, and final
closure. Do not repeat the notice during routine progress updates when none of
those fields changed.

Use exactly this shape:

```text
Model routing: <role> → <exact model> (<effort>). Trigger: <brief reason>.
```

For a fallback, include it in the trigger, for example:

```text
Model routing: implementation builder → gpt-5.6-terra (high). Trigger: approved multi-file implementation; gpt-5.6-sol unavailable, closest implementation fallback.
```

Identify delegated builder and reviewer models in coordinator commentary. When
a delegated runtime does not expose its model, use the required unavailable
metadata wording rather than the requested model name.

## Review artifacts and closure

When known, every adversarial-review artifact must record:

- builder runtime identity, actual model, and effort;
- reviewer runtime identity, actual model, and effort;
- the routing trigger; and
- any fallback, unavailability, or unexposed runtime metadata.

Use a `## Model routing` section in each new design, implementation, remediation,
and closure-review artifact. Use a `## Model assignments` section in
`closure.md` to summarize the full run. These sections are the authoritative,
human-readable evidence locations; do not rely on task-local commentary or
model-selection requests as proof of the runtime used.

The independent closure reviewer must verify these sections against the phase
notices, returned runtime identities, and known delegation metadata. Missing,
inconsistent, inferred, or silently substituted model/effort evidence is a
closure blocker even if `validate-review-run.py` otherwise passes. Record
`model not exposed by runtime` or `effort not exposed` when applicable; that is
valid evidence of unavailable metadata, not permission to guess.

Do not rewrite historical attestations merely because model metadata was not
previously required. New review reports and closure evidence must be accurate
about what the runtime exposed. Final closure must summarize model assignments
for design, implementation, remediation, implementation review, and closure
review, including fallbacks.

For a review run already in progress when this policy is adopted, completed
reports are historical for this purpose even if they are still uncommitted. Do
not rewrite those immutable reports. Instead, bind this policy and the current
working tree into a fresh closure packet, summarize every known, unexposed, and
requested assignment in `closure.md`, and obtain a compliant independent
closure re-attestation before the files share a commit.

## Delegation mechanics

Use project subagents for bounded model-specific work when repository policy
and the active task permit delegation. Give each subagent one coherent role,
explicit scope, requested model and effort, and required evidence. Use the
repository's subagent mechanism so work remains attached to the current task;
do not create user-visible tasks merely to switch models.

The coordinator remains responsible for integrating results, checking actual
runtime metadata, preserving the working tree, and enforcing review gates.

```
### `.ai/review-runs/T082-AWS-INVITE-PILOT-D-PRIVACY-AMENDMENT/closure.md`

size=4566; sha256=d9d889da28469907e798bbe7569c744c184333e5218fac1345d859518ac626e9

```text
# Closure report: T082-AWS-INVITE-PILOT-D-PRIVACY-AMENDMENT

## Outcome

The post-third-loop privacy amendment is ready for independent closure review.
Its architecture and implementation passed independent design and implementation
review. PRIV-001 and PRIV-002 are closed; parent findings D004, D007, D008, and
D009 are independently closed. No open blocker remains in this child run.

## Invariants verified

- Process-start logging ownership precedes Uvicorn configuration and app load;
  handler-internal diagnostics and raw access logs are disabled while healthy
  operational records remain.
- Delivery attempts become terminal before await; uncertain sends never
  authorize a second response.
- Cancellation has no recovery send, uses type-only classification, preserves
  non-HTTP propagation, and cannot let an old completed/non-current request
  close or mutate its successor.
- Correlation context is neutral during synchronous successor-task creation and
  isolated across sequential/pipelined requests.
- Disconnect claims are limited to observed I/O. Uvicorn owns shutdown
  cancellation of unrelated waits; deadlines are measured before cleanup.
- The self-contained `/app` oracle runs against the exact unchanged locked image
  dependency set and includes independent negative controls.

## Findings disposition summary

- PRIV-001: closed by current-cycle/transport/final-send ownership rules and
  overlapping cancellation evidence.
- PRIV-002: closed by narrowed disconnect semantics, explicit shutdown owner,
  and pre-cleanup liveness measurement.
- Open blockers, accepted risks, and deferred findings: none.

## Verification performed

- Exact locked image oracle: 113 passed; independent rerun also 113 passed.
  Network disabled, no host mounts or credentials; `pip check` passed.
- Uvicorn 0.53.0 and other imported versions match the unchanged lock.
- Independent actual-Starlette cancellation and short-content-length probes
  passed.
- Image/tree hashes, Docker launcher, ECS no-command-override boundary, locked
  server behavior, negative controls, real streams, database outage, and
  non-HTTP propagation were inspected.

## Final scope reviewed

`backend/pilot_server.py`, `backend/Dockerfile`, the ASGI boundary, protocol
adapter, request context, dedicated privacy oracle, parent test separation,
unchanged lock, streaming consumers, and ECS command wiring. Schema/migration,
T081/0030, Terraform mutation, AWS, provider, cost UI, and unrelated dirty work
were outside this child scope.

## Accepted risks and deferred work

No finding is accepted or deferred. A failed sink may lose safe evidence;
non-HTTP explicit diagnostics and uncooperative blocked code are outside the
bounded local guarantee. These are documented limits, not verified live claims.

## Not verified

Live image/digest/command, network/ALB/socket behavior, CloudWatch delivery and
retention, console backpressure, ECS task replacement, Budget notification,
provider activation, and paid-attempt reconciliation remain Package E gates.

## Model assignments

- Design builder: `/root/t082_package_d_privacy_amendment_design`; requested
  GPT-6 Astra xhigh, actual `model not exposed by runtime`, `effort not exposed`.
- Design-remediation builder: `/root/t082_package_d_privacy_amendment_design`;
  requested GPT-6 Astra xhigh, actual `model not exposed by runtime`, `effort not exposed`.
- Design reviewer: `/root/t082_package_d_privacy_review_2`; requested GPT-6
  Astra xhigh, actual `model not exposed by runtime`, `effort not exposed`; initial FAIL and final PASS.
- Implementation builder: `/root/t082_package_d_privacy_remediation_3`;
  requested GPT-6 Astra xhigh, actual `model not exposed by runtime`, `effort not exposed`.
- Focused-verification builder: `/root/t082_package_d_privacy_remediation_3`;
  requested GPT-6 Astra xhigh, actual `model not exposed by runtime`, `effort not exposed`.
- Implementation reviewer: `/root/t082_package_d_privacy_review_2`; requested
  GPT-6 Astra xhigh, actual `model not exposed by runtime`, `effort not exposed`; PASS.
- `/root` coordinated design remediation, implementation integration, focused
  verification integration, and closure; `model not exposed by runtime`,
  `effort not exposed`.
  Independent closure reviewer: `/root/t082_package_d_closure_review`; requested
  GPT-6 Astra xhigh, actual `model not exposed by runtime`, `effort not exposed`;
  initial documentation FAIL followed by verified remediation; the final
  attestation and `reviews.json` are authoritative for the closure outcome.

```
### `.ai/review-runs/T082-AWS-INVITE-PILOT-D-PRIVACY-AMENDMENT/adversarial-closure-initial.md`

size=1285; sha256=6ee113d6b082311f806ecf47f659c73f7ba94cce4f1c80c03b96e67460d70ffd

```text
# Privacy amendment closure review — FAIL

## Model routing

- Closure coordinator: `/root`; actual `model not exposed by runtime`, `effort not exposed`.
- Independent closure reviewer: `/root/t082_package_d_closure_review`.
- Requested reviewer route: GPT-6 Astra, xhigh.
- Actual reviewer model: `model not exposed by runtime`.
- Actual reviewer effort: `effort not exposed`.
- Trigger: final closure of the post-third-loop privacy amendment.

## Outcome

FAIL for documentation/integrity only. No implementation or design defect was
found.

## Findings

- **PRIV-CLOSURE-001:** Model assignments require the exact unexposed-model and
  effort phrases, complete phase coverage, and this closure reviewer identity.
- **PRIV-CLOSURE-002:** `decision.md` lacks validator-required exact headings:
  Objective, Safety and correctness invariants, Proposed design, Test strategy.
- **PRIV-CLOSURE-003:** The closure packet does not hash-bind the modified
  `.ai/MODEL_ROUTING.md`.

## Checks

The packet remained current. Both child findings have independent evidence;
review artifacts/hashes, retained implementation evidence, image identity, and
Package E limits agree. No suite was repeated. Reviewed packet SHA-256:
`c2a1f06fe4aa849bae0af97fa47077181cf20278e6496a9704bc489868446148`.

```
### `.ai/review-runs/T082-AWS-INVITE-PILOT-D-PRIVACY-AMENDMENT/adversarial-closure-remediation.md`

size=1033; sha256=521469b52297df0d20f386310c9471cd041d9564b853a82a6c593ded3799d96b

```text
# Privacy amendment closure remediation verification — PASS

## Model routing

- Closure coordinator: `/root`; `model not exposed by runtime`, `effort not exposed`.
- Independent reviewer: `/root/t082_package_d_closure_review`.
- Requested reviewer route: GPT-6 Astra, xhigh.
- Actual reviewer model: `model not exposed by runtime`.
- Actual reviewer effort: `effort not exposed`.

## Outcome

Documentation remediation passed for PRIV-CLOSURE-001 through -003. The closure
summary uses exact routing wording and complete phase assignments; the decision
has validator-visible headings without semantic change; and the current packet
binds `.ai/MODEL_ROUTING.md`.

All implementation/lock and non-review dirty-file hashes were unchanged; no
suite rerun was necessary. Reviewed packet SHA-256:
`7ff0f26f2cefafa01d0259138c7f2e77773c2ed18397a5dba972f0a1a580fe70`.

The reviewer authorized the coordinator to close these findings, regenerate the
packet, and obtain one final packet-current re-attestation before recording
closure PASS.

```
### `.ai/review-runs/T082-AWS-INVITE-PILOT-D-PRIVACY-AMENDMENT/adversarial-closure-final.md`

size=1089; sha256=5c02003819162a8fde11936036ceec2f803582978e1f96d47ba3351abcd3ac48

```text
# Privacy amendment final closure — PASS

## Model routing

- Closure coordinator: `/root`; `model not exposed by runtime`, `effort not exposed`.
- Independent reviewer: `/root/t082_package_d_closure_review`.
- Requested reviewer route: GPT-6 Astra, xhigh.
- Actual reviewer model: `model not exposed by runtime`.
- Actual reviewer effort: `effort not exposed`.
- Trigger: final packet-current re-attestation of the post-third-loop privacy
  design, implementation, and documentation remediation.

## Outcome

PASS. All child findings are closed with existing evidence paths. Policy and
validator fixes remain bound without changing approved design semantics, and
all 286 non-review file hashes remain unchanged.

The authoritative final scope fingerprint is recorded by `record-review.py` in
`reviews.json` against the current hash-bound packet. It is intentionally not
embedded here because this report is itself a packet input.

Package E live gates remain unchanged. The reviewer performed no edit or test
rerun and authorized recording closure PASS and running the final validator.

```
### `.ai/review-runs/T082-AWS-INVITE-PILOT-D/adversarial-closure-final.md`

size=1174; sha256=ab710ce245c2a799d0737f53e32aba9b48990de9c9ac7ce8ee7147def7ec6c14

```text
# Package D final closure — PASS

## Model routing

- Closure coordinator: `/root`; `model not exposed by runtime`, `effort not exposed`.
- Independent reviewer: `/root/t082_package_d_closure_review`.
- Requested reviewer route: GPT-6 Astra, xhigh.
- Actual reviewer model: `model not exposed by runtime`.
- Actual reviewer effort: `effort not exposed`.
- Trigger: final packet-current re-attestation after substantive findings and
  documentation/integrity remediation.

## Outcome

PASS. All Package D findings are closed with existing evidence paths. The model
policy, child decision headings, and historical recording-delta explanation are
hash-bound. Approved design semantics and all 286 non-review file hashes remain
unchanged. Historical attestations remain intact.

The authoritative final scope fingerprint is recorded by `record-review.py` in
`reviews.json` against the current hash-bound packet. It is intentionally not
embedded here because this report is itself a packet input.

Package E deployment and live-evidence gates remain unchanged. The reviewer
performed no edit or test rerun and authorized recording closure PASS and
running the final validator.

```
### `.ai/review-runs/T082-AWS-INVITE-PILOT-D-PRIVACY-AMENDMENT/adversarial-design-final.md`

size=2525; sha256=6673a7801c24caabcfabf8f6a83d3d1d6e3289f3864e1215dfe0cd5902c9d493

```text
# Privacy amendment design re-review — PASS

## Model routing

- Design builder: `/root/t082_package_d_privacy_amendment_design`.
- Independent reviewer: `/root/t082_package_d_privacy_review_2`.
- Requested builder/reviewer route: GPT-6 Astra, xhigh.
- Actual builder/reviewer model: `model not exposed by runtime`.
- Actual effort: `effort not exposed`.
- Trigger: re-review of cancellation ownership and disconnect/liveness semantics
  after the post-third-loop architecture reassessment.

## Outcome

PASS. PRIV-001 and PRIV-002 are resolved at the design level. No new finding
was identified. Implementation may resume only within this approved amendment
and remains subject to locked-image and independent implementation review.

## Finding dispositions

### PRIV-001 — closed at design

Connection-close authority now requires matching current cycle and transport
identities, no confirmed final-send completion, and no intervening await.
Completed and non-current tasks cannot close a successor's transport. The
design distinguishes successful final-send return from Uvicorn's earlier
`response_complete` flag, preserving safe handling of uncertain final writes.

### PRIV-002 — closed at design

Disconnect guarantees now cover only states observed through receive, send, or
drain. Unrelated application waits may remain pending. Uvicorn's request-task
owner explicitly owns graceful-shutdown cancellation, and liveness deadlines
are measured before separate cleanup using non-cancelling observation.

## Other conclusions

- The no-await ownership check is enforceable under the inspected event-loop
  protocol; successor creation occurs synchronously during response completion.
- Marking only an old captured cycle disconnected does not mutate the successor.
- Plain, pure-grouped, and mixed/nested cancellation are covered. Mixed groups
  remain sanitized unexpected failures rather than successful responses.
- Process-start logging policy, evidence-loss ownership, rollback, and Package E
  boundaries remain sound.
- The dedicated `/app/tests/test_pilot_privacy.py` oracle removes repository
  layout dependencies; D005/D006 evidence remains unchanged.

## Verification

The refreshed packet was verified twice. The reviewer inspected the amended
decision, remediation report, child ledger, protocol transitions, and preserved
hashes. Reviewed packet SHA-256:
`c6d7708f399fb935de3b0b541d70c1cd14efd4a2fcaefae89afede8d5a987230`.
No implementation, image build, staging, commit, or cloud mutation occurred.

```
### `.ai/review-runs/T082-AWS-INVITE-PILOT-D-PRIVACY-AMENDMENT/implementation.md`

size=9955; sha256=801ca317131d2627925418f95649b52b1881bc893fe0c3a0a2013b5979f33530

```text
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

```
### `.ai/review-runs/T082-AWS-INVITE-PILOT-D-PRIVACY-AMENDMENT/adversarial-implementation-final.md`

size=1923; sha256=623e3d3875acd071d9a4782d8d696108988b83f5d7fabb895a5c9cdc9776d5a7

```text
# Privacy amendment implementation review — PASS

## Model routing

- Builder: `/root/t082_package_d_privacy_remediation_3`.
- Independent reviewer: `/root/t082_package_d_privacy_review_2`.
- Requested builder/reviewer route: GPT-6 Astra, xhigh.
- Actual builder/reviewer model: `model not exposed by runtime`.
- Actual effort: `effort not exposed`.
- Trigger: implementation review of the independently approved post-third-loop
  logging/privacy architecture and exact locked-runtime oracle.

## Outcome

PASS. The implementation conforms to the approved amendment. PRIV-001 and
PRIV-002 remain resolved; no new finding or blocker was identified.

## Evidence

- Process-start logging ownership, healthy operational logging, handler failure
  suppression, disabled access logs, exact protocol selection, and the ECS
  command boundary match the design.
- Delivery states, terminal cancellation, current/completed/non-current cycle
  ownership, successor correlation isolation, observed-disconnect scope,
  shutdown cancellation, non-HTTP propagation, and real stream paths passed.
- The independent locked-image run produced 113 passed, 5 warnings in 29.40
  seconds with network disabled and no host mounts.
- Python 3.12.11 and Uvicorn 0.53.0 match the unchanged production lock; ten
  inspected image/source/test/route/lock hashes match the working tree.
- Independent actual-Starlette cancellation and short-content-length probes
  found no second response, context leak, sentinel, or exception attachment.
- Child packet freshness passed immediately before reporting. Packet SHA-256:
  `0cb79e09bd581eb2cf3a01179722692a1e5833792d720d5c3839a8b03f6551bb`.
- Reviewed image:
  `sha256:4e07ccf55d64d8011c712d12095faf01615099bc22070b15a1cf0fd50a80c2db`.

Package E retains all live deployment and evidence-delivery gates. The reviewer
was read-only; no repository, cloud, provider, staging, or commit mutation
occurred.

```
### `.ai/review-runs/T082-AWS-INVITE-PILOT-D/package-d-remediation-3.md`

size=5091; sha256=756fa5484b929519c62077a2745afe78918690e514c7e4c8aaeb7eb1188ae8aa

```text
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

```
### `.ai/review-runs/T082-AWS-INVITE-PILOT-D/findings.json`

size=12492; sha256=8a91536049d36f9431a9b2b08733737e3df3168ddeae683824871e6a17b3879c

```text
[
  {
    "id": "T082-D-001",
    "stage": "design",
    "reviewer": "/root/t082_pilot_design_adversary",
    "severity": "high",
    "status": "closed",
    "invariant": "Pilot cost reporting distinguishes recorded-run evidence from complete paid-attempt exposure and never converts missing price, attribution, or rows into zero or certainty.",
    "summary": "OCRRun commits after the provider call, so recorded rows cannot establish complete paid-attempt exposure.",
    "evidence": ["adversarial-design-inheritance.md", "backend/app/services/ingestion.py", "decision.md"],
    "impact": "The pilot dashboard could understate or misclassify cost after a crash or ambiguous provider outcome.",
    "requiredClosure": "Define a recorded-run partial projection, independent classifications, historical attribution semantics, and a visible Package E completeness gate.",
    "closureEvidence": ["decision.md", "adversarial-design-closure.md"]
  },
  {
    "id": "T082-D-002",
    "stage": "design",
    "reviewer": "/root/t082_pilot_design_adversary",
    "severity": "high",
    "status": "closed",
    "invariant": "Extracted-entry achievement evidence is written atomically only for newly created entries with an explicit authenticated pilot actor.",
    "summary": "The service commits entries before the HTTP route can write atomic events and also has a non-HTTP caller.",
    "evidence": ["adversarial-design-inheritance.md", "backend/app/services/ingestion.py", "backend/app/api/routes/ingestion.py", "backend/app/scripts/run_ocr_feasibility.py"],
    "impact": "Retries can mint false achievements or real entry creation can lack same-transaction evidence and correct actor semantics.",
    "requiredClosure": "Move new-entry event ownership into the service with explicit actor context, no retry duplicates, and preserved non-HTTP behavior.",
    "closureEvidence": ["decision.md", "adversarial-design-closure.md"]
  },
  {
    "id": "T082-D-003",
    "stage": "design",
    "reviewer": "/root/t082_pilot_design_adversary",
    "severity": "medium",
    "status": "closed",
    "invariant": "Achievement projection selects a deterministic first-success representative before filtering, grouping, and display limits.",
    "summary": "The approved identity key did not define representative or ordering semantics.",
    "evidence": ["adversarial-design-inheritance.md", "decision.md"],
    "impact": "Duplicate rows can shift apparent dates or actors and crowd out legitimate recent achievements.",
    "requiredClosure": "Select earliest event_time and id per identity before filters/grouping/limits; keep counts independent of display limits.",
    "closureEvidence": ["decision.md", "adversarial-design-closure.md"]
  },
  {
    "id": "T082-D-004",
    "stage": "implementation",
    "reviewer": "/root/t082_package_d_implementation_review",
    "severity": "high",
    "status": "closed",
    "invariant": "Unexpected failures across the complete ASGI response lifecycle produce sanitized correlated evidence without exposing exception text or request content.",
    "summary": "Generator errors are contained, but transport failure during the first send triggers an unsafe second response-start attempt and lets secret-bearing transport text escape.",
    "evidence": ["adversarial-implementation-initial.md", "package-d-remediation-1.md", "adversarial-implementation-remediation-1.md", "backend/app/main.py", "backend/app/api/routes/uploads.py", "backend/app/api/routes/ingestion.py"],
    "impact": "A disconnect or transport failure can expose exception content through the server traceback path and violate ASGI response sequencing.",
    "requiredClosure": "Close the complete response lifecycle across normal, pre-start, post-start, and transport-failure states; treat attempted delivery as uncertain; contain recovery-send failures; retain executable upload and page-image evidence.",
    "closureEvidence": ["package-d-remediation-1.md", "package-d-remediation-2.md", "../T082-AWS-INVITE-PILOT-D-PRIVACY-AMENDMENT/decision.md", "../T082-AWS-INVITE-PILOT-D-PRIVACY-AMENDMENT/implementation.md", "package-d-remediation-3.md", "adversarial-implementation-remediation-3.md"]
  },
  {
    "id": "T082-D-005",
    "stage": "implementation",
    "reviewer": "/root/t082_package_d_implementation_review",
    "severity": "medium",
    "status": "closed",
    "invariant": "Every canonical achievement success point has executable positive, rollback, retry or conflict, and actor-context evidence appropriate to its write path.",
    "summary": "Retained tests directly insert achievements and use source-string assertions for central extracted-entry and AD-conflict behavior.",
    "evidence": ["adversarial-implementation-initial.md", "backend/tests/test_pilot_package_d.py"],
    "impact": "Atomicity, actor attribution, retry, and rejected-request regressions can pass the retained oracle.",
    "requiredClosure": "Add bounded executable coverage for the six success-point families, emphasizing extraction and AD decision paths, and correct overstated coverage claims.",
    "closureEvidence": ["package-d-remediation-1.md", "adversarial-implementation-remediation-1.md"]
  },
  {
    "id": "T082-D-006",
    "stage": "implementation",
    "reviewer": "/root/t082_package_d_implementation_review",
    "severity": "medium",
    "status": "closed",
    "invariant": "The administrator UI exposes the approved independent recorded-run lifecycle, pricing, attribution, billing, and partial-estimate distinctions.",
    "summary": "The UI collapses cost reporting and omits most approved independent classifications.",
    "evidence": ["adversarial-implementation-initial.md", "frontend/paprnav-frontend/src/app/(authenticated)/observability/page.tsx"],
    "impact": "Administrators cannot distinguish pending or failed exposure, unattributed runs, billing state, or completed priced estimates.",
    "requiredClosure": "Render every independent category, label partial estimates explicitly, and retain focused frontend checks.",
    "closureEvidence": ["package-d-remediation-1.md", "adversarial-implementation-remediation-1.md"]
  },
  {
    "id": "T082-D-007",
    "stage": "implementation",
    "reviewer": "/root/t082_package_d_implementation_review",
    "severity": "high",
    "status": "closed",
    "invariant": "Effective production HTTP logging is content-free and never records raw query strings, exception text, request bodies, credentials, or session material.",
    "summary": "The backend image launches Uvicorn with default access logging, which records the raw query string outside the application sanitizer.",
    "evidence": ["adversarial-implementation-remediation-1.md", "package-d-remediation-2.md", "adversarial-implementation-remediation-2.md", "backend/Dockerfile", "backend/app/main.py", "backend/app/core/http_protocol.py"],
    "impact": "Secrets supplied in request queries can be retained in the configured container log stream on successful or error responses.",
    "requiredClosure": "Verify the no-access-log and custom-protocol production configuration against the exact locked Uvicorn version and retain effective success/error request-cycle evidence.",
    "closureEvidence": ["package-d-remediation-2.md", "../T082-AWS-INVITE-PILOT-D-PRIVACY-AMENDMENT/decision.md", "../T082-AWS-INVITE-PILOT-D-PRIVACY-AMENDMENT/implementation.md", "package-d-remediation-3.md", "adversarial-implementation-remediation-3.md"]
  },
  {
    "id": "T082-D-008",
    "stage": "implementation",
    "reviewer": "/root/t082_package_d_privacy_review_2",
    "severity": "high",
    "status": "closed",
    "invariant": "Failures inside the production logging sink cannot print exception text, traceback data, request content, or credentials to stderr or any retained server log.",
    "summary": "Standard logging handlers invoke handleError internally, bypassing the middleware's outer exception catch and printing sink exception text and traceback to stderr.",
    "evidence": ["adversarial-implementation-remediation-2.md", "backend/app/main.py"],
    "impact": "A logging transport or handler failure can disclose sensitive exception content through the container's stderr log stream.",
    "requiredClosure": "Approve a production logging ownership/configuration design that suppresses or sanitizes handler-internal diagnostics while preserving content-free failure evidence, and retain an effective sink-failure test.",
    "closureEvidence": ["../T082-AWS-INVITE-PILOT-D-PRIVACY-AMENDMENT/decision.md", "../T082-AWS-INVITE-PILOT-D-PRIVACY-AMENDMENT/implementation.md", "package-d-remediation-3.md", "adversarial-implementation-remediation-3.md"]
  },
  {
    "id": "T082-D-009",
    "stage": "implementation",
    "reviewer": "/root/t082_package_d_privacy_review_2",
    "severity": "medium",
    "status": "closed",
    "invariant": "The retained server-protocol privacy oracle runs against and asserts the exact Uvicorn version pinned into the production image.",
    "summary": "The lockfile pins Uvicorn 0.53.0, but the current test environment imports 0.52.1 and the oracle does not enforce agreement.",
    "evidence": ["adversarial-implementation-remediation-2.md", "backend/requirements.lock", "backend/tests/test_pilot_package_d.py"],
    "impact": "Protocol-internal compatibility and logging claims are not proven for the actual production dependency set.",
    "requiredClosure": "Run the focused protocol contract against the locked version and make version agreement a deterministic gate.",
    "closureEvidence": ["../T082-AWS-INVITE-PILOT-D-PRIVACY-AMENDMENT/decision.md", "../T082-AWS-INVITE-PILOT-D-PRIVACY-AMENDMENT/implementation.md", "package-d-remediation-3.md", "adversarial-implementation-remediation-3.md"]
  },
  {
    "id": "T082-D-CLOSURE-001",
    "stage": "closure",
    "reviewer": "/root/t082_package_d_closure_review",
    "severity": "blocker",
    "status": "closed",
    "invariant": "Closure records every meaningful phase with exact runtime model and effort disclosure wording and the closure reviewer assignment.",
    "summary": "The closure model summary uses ambiguous shorthand and omits required phases and the closure reviewer.",
    "evidence": ["adversarial-closure-initial.md", "closure.md", ".ai/MODEL_ROUTING.md"],
    "impact": "The run cannot close under the repository's mandatory routing-evidence policy.",
    "requiredClosure": "Use exact model/effort wording, correct the initial reviewer request, and enumerate remediation, verification, coordinator, and closure-review assignments.",
    "closureEvidence": ["closure.md", "adversarial-closure-initial.md", "adversarial-closure-remediation.md"]
  },
  {
    "id": "T082-D-CLOSURE-003",
    "stage": "closure",
    "reviewer": "/root/t082_package_d_closure_review",
    "severity": "blocker",
    "status": "closed",
    "invariant": "The fresh closure packet hash-binds the active modified model-routing policy governing this in-progress run.",
    "summary": "The closure packet omits .ai/MODEL_ROUTING.md from its review inputs.",
    "evidence": ["adversarial-closure-initial.md", "manifest.json", ".ai/MODEL_ROUTING.md"],
    "impact": "Closure cannot prove compliance with the policy it cites.",
    "requiredClosure": "Add .ai/MODEL_ROUTING.md as a closure review input and regenerate the packet.",
    "closureEvidence": ["closure.md", "adversarial-closure-initial.md", "adversarial-closure-remediation.md", ".ai/MODEL_ROUTING.md"]
  },
  {
    "id": "T082-D-CLOSURE-004",
    "stage": "closure",
    "reviewer": "/root/t082_package_d_closure_review",
    "severity": "blocker",
    "status": "closed",
    "invariant": "Historical review fingerprint differences are preserved and explained so an attestation is not represented as covering a different packet silently.",
    "summary": "The initial implementation report and reviews.json record different packet fingerprints without an explanation.",
    "evidence": ["adversarial-closure-initial.md", "adversarial-implementation-initial.md", "reviews.json"],
    "impact": "Historical review provenance is ambiguous even though later current-tree implementation review supersedes it.",
    "requiredClosure": "Preserve the immutable report, document the ledger-update/rebuild recording delta and its limits, and obtain closure re-attestation.",
    "closureEvidence": ["review-recording-delta.md", "closure.md", "adversarial-closure-initial.md", "adversarial-closure-remediation.md"]
  }
]

```
### `backend/requirements.lock`

size=64899; sha256=729a4a4316e863db493204ecc103c41943162cb7986af3fe5669a10e8d66462d

```text
# This file was autogenerated by uv via the following command:
#    uv pip compile backend/requirements.txt --generate-hashes --python-version 3.12 --python-platform x86_64-manylinux_2_28 -o backend/requirements.lock
alembic==1.20.0 \
    --hash=sha256:77eb101048d95f982c0353e9233404889dcd7a6fc244c107836c0e2fc9cf7d9d \
    --hash=sha256:db505480647bc60386c5369402f4a57a506b7539c9e9ef5e270d45cbbe4939bf
    # via -r backend/requirements.txt
annotated-doc==0.0.5 \
    --hash=sha256:117bac03a25ede5df5440e855b32d556049ca169ead221505badf432fed4b101 \
    --hash=sha256:c7e58ce09192557605d8bbd92836d7e1d520ac9580096042c0bfd197efacf1bb
    # via fastapi
annotated-types==0.8.0 \
    --hash=sha256:13b2beaad985e05e2d6407ee4c4f35590b11f8d693a258a561055cac8f64cab7 \
    --hash=sha256:f072f4d804ea359e4eaf198b1af7a8b0943881a87f31bb764f8bf219bb9419e0
    # via pydantic
anyio==4.15.1 \
    --hash=sha256:6152fdbbf9a77fdec97731721bebf7c4c44f7c29b424b0065826173efc7ed101 \
    --hash=sha256:9f28306018cbd6d329e64a36d58256edff76dd996fe423bc957326e578b82a94
    # via
    #   httpx
    #   starlette
boto3==1.43.98 \
    --hash=sha256:1ec732e023fb29c12dc8520f925b5bbbed29eeb36b5764b5a5c26052d7c721f7 \
    --hash=sha256:7454f666a9e852a56db0a7fa23be33a899f64e27828930eac43c3edba7b34e17
    # via -r backend/requirements.txt
botocore==1.43.98 \
    --hash=sha256:6135dd639ea6d1b3b49381bc253c8a139d61f7d44cb5f7dae8e7cd1791758572 \
    --hash=sha256:84b35b10402c2fc0c265f634fbf86336eecc6489ee23f55074b329924b2cfd6f
    # via
    #   boto3
    #   s3transfer
certifi==2026.7.22 \
    --hash=sha256:62f22742b58a1a33014a2b6b706588a8d7e2a88ae7bd1a6ebe8c992928483775 \
    --hash=sha256:741e2c3b351ddf169a738da9f2c048608ff7f2c5cc02f1ebc6b118bb090d5d55
    # via
    #   httpcore
    #   httpx
charset-normalizer==3.5.1 \
    --hash=sha256:00668ebb0609751758682eb0b5857e7c35b9f00e84dfdef062e103244ec94d45 \
    --hash=sha256:012a22b88a77ca2e59b98ac5889b0deb604147666032f45e6d6e217634d2550d \
    --hash=sha256:01e93745f7f219b703b60ba7afead36cfc4242782be5af484673fc500df12da5 \
    --hash=sha256:04368edf83514385ffc3e1cfd4546e595f4f1272dd23ba437a93a9cc3741d47b \
    --hash=sha256:0722590aabf9dc6a6c0343d523c05458fa2b5047dbe6302fd526bb570600753f \
    --hash=sha256:07ffd07412fc5d5e84cd8952acf9ff7e4ed7a708e69d1bada19d8ba91711353f \
    --hash=sha256:09a7bba9f739468c8e78c36a75c33768e53cb1959fc638f510454c14683f00d5 \
    --hash=sha256:0b2b1b3fa5670c127b246df1d0c059defd41f689a868a3b9d79df9b1cac42d22 \
    --hash=sha256:0c6dfb5ca6723eeed15aa8e564a014d69fcb8812f94eef11fe3631e0508199f5 \
    --hash=sha256:0d929fc574b4d6fd9e7c0f5c2ede8716a41911923aa7fa5fce38e0818aa4a1ac \
    --hash=sha256:13e3afe97712e8887cd516e960c63f0b93122971e5b5e4b2622fe7701771e838 \
    --hash=sha256:15f024313246a4ed976c60f440bb8d257815513a681d212ff74fd46f7d715a90 \
    --hash=sha256:195ce897c6153c0700078142cf8efe3e6454ca4cf4357499e4078dfd83396626 \
    --hash=sha256:19a3dd5aa73cef1c99687c4fc57db016a9c17104ae1185da88ba566a5d3bebe4 \
    --hash=sha256:1d1c7a53a6c2103925cdd6d7229f8c567379f211c869793df679f2e9f738c369 \
    --hash=sha256:1f5883d77fd409a261abb5dc8ccbe335720d798b1de4abb3b1d47ccbbc76b53b \
    --hash=sha256:21b82d8082f6f5e7f456ef0bd16323d08de1266efbfeb476e64b2a91d1471a4e \
    --hash=sha256:252d099029bcbea642f2a06c4ed5046bdf8b5a8150b64afa5e027e88b106e5ee \
    --hash=sha256:256dd4d85d9e4dc595e2bc983c980e73f62ddeb3165c58b4c3dfe78c5c8548c1 \
    --hash=sha256:26422d45fd13551cf564c58932f7d72b4f58b93b0fcf18c35ba6be12b46bb102 \
    --hash=sha256:2679de311c7946dde5d3b6f44941844133ff5c7cb86099c0061ab1e8901c20a8 \
    --hash=sha256:29880d17a8eb0b5cfdfd8944b468322928059aa35f1f5fa8ff22b149ec0b42f8 \
    --hash=sha256:2bced4061f000f7187254a02ad3433ae17eaf991747ceea2f478422590a5bba9 \
    --hash=sha256:2e9cf9253119d8e5d111f05d71626786fd3d6193817316eab1ca088cdb8593cf \
    --hash=sha256:2f06b7eae9dbe77fe1d644ca244dad508de8d302870a43f3c559b521270938a0 \
    --hash=sha256:2f293479cce755c75f1697e87c409b7ae4c555c7dfecb6e988ad13abba943031 \
    --hash=sha256:329fc3ccb63ad22d867d84c2adea759a64079a37ba4a343433b02c7a2816871e \
    --hash=sha256:343fb4f2821043bd87095f7b08a1a181febc8e36ac64212143bbfd0a0e1bc235 \
    --hash=sha256:3588e376b3ea2eea84976f67273d679f229e24c66dce7b82ae45aef04ff6e072 \
    --hash=sha256:35aea775dc2bd5f54cd84a1cd2696cc3207c479cb9cf0bd346f0d343e4300ddb \
    --hash=sha256:35fe081843b35aad20ffeccec3eeffbe637b15d14f3fb22cc1b59cd8ec17e93c \
    --hash=sha256:36047af20e17097c3bb9476c2b7655f2f7aa51322c0ba58c07695bedf755a950 \
    --hash=sha256:3617ac3cfd8b9888f145ad89dd6e692285834b0201c6074a5eeaad3fd4d668c2 \
    --hash=sha256:366ec70f5547c640d3ce1985722490f23faf4eb5216a7eeba78277490e78dacb \
    --hash=sha256:394fea06235c8543390050ed5f529187074b029fb027213f6c46ac11ab5d950e \
    --hash=sha256:3d27167433c0d5f18dc850f07d0b3816221984fecdc405d6c157a6f0b8f8e9e6 \
    --hash=sha256:3e5e1224c0a6a90e05843e07adfec669edebec17801c67072f51e59561d63c0b \
    --hash=sha256:41876ee62a3dddf48ff1121ad8f0798032aa03f2fd35f21f34a4cab14f18d8d2 \
    --hash=sha256:433c5a81eade63b47e522303bad236f59dba55ea6951746f5558355eeed8c75d \
    --hash=sha256:4582c27e8c889d64811987b5967fbd3ae0c823fe1fd933b543d55ac20bb475fa \
    --hash=sha256:485a0d363cafefcd2538a73c7c838daa2035f09b2c9f9b5e3133f80c6aeb84c2 \
    --hash=sha256:494b70049a4d69aec6e8137c13af4cf8db8c9f9820a1392ac293b0dd2987a818 \
    --hash=sha256:496846868fea80e479324862fa877f02411f2fd0f83b79ccee2607aa68b2a032 \
    --hash=sha256:4abdc5f9ad448c1ecbfae2974b820535d6bc6e7eef63babbab3d81cf46968c71 \
    --hash=sha256:4b599739b93b2cbeded49645ae3c8d1405c29ddfbceac1545c87a3f9580a9e96 \
    --hash=sha256:4bea7f8ebe90bbd7f0e4a2de42ca6924ba23e3e76418c408ff82f1d46fabd687 \
    --hash=sha256:4c4fb141a727957c93edfe5c32a26ceb6b5f6461d67146e2d39f51e16170bea8 \
    --hash=sha256:4c9548dc78002099910abaebc0a72ac58b7d30931869e0351c09b507dff4ece3 \
    --hash=sha256:4d26f14f041e83dd8edfd61f4cd4fa7285d31798b5bf1f28e70c367ba6c41d61 \
    --hash=sha256:4f298bdadb8f0b9e5672877f647d1be9373ef5320c9e2f049795e26cad28b6a9 \
    --hash=sha256:52ec005752a56ae79547a05c0139ca2501a0c866390b6115008456b9f0e7cde1 \
    --hash=sha256:55261ac0d2941c42f196dd576f543d87a8ee03cd6f5e30dfb4d807b2e3b9121a \
    --hash=sha256:56490c595a28b1bb27dfc583e816152a9767721ef58b2c03b13f954d2f707420 \
    --hash=sha256:58d3e12c88e0950bca850ae1f7c256055c097639c2edb9eb123af9807d8b15e4 \
    --hash=sha256:58d4aa13a59c969dbfdf9e6a9560e242cbfd9e8a8f50c2747714df1a423adf65 \
    --hash=sha256:59171c6e45bf07d0d5cab3b0bf81d945035530f6873398b3b531c31184d46663 \
    --hash=sha256:5b6d1386bf0096d26d3a863dc0a487a5b4eb9aa93cf5ba69683d29dde6b9d60f \
    --hash=sha256:5c0ea61a470e070686aa30892fed79e297d2c8d0ab46b8bcdf027d38c51da591 \
    --hash=sha256:5c84bec0ab5ae0c64bfe73a7d2adcb5ce73b467523fc27fd6a28ab2aa6cbe35a \
    --hash=sha256:5ca0555312ae2fe82715cada7fac375530c2f3349e1eaa1bcb33d0283ac79a18 \
    --hash=sha256:5d8531a6569d025f68e2321e7638fb7978f23db58e5f69f56913837aae03816e \
    --hash=sha256:5e2d0e146dcb57034f8b97dc58d2d512cb90aba253960ce449f695fec6a82c6f \
    --hash=sha256:5fc45d653ea8c9a20479167e11d4a0f8cb2fa3470737ab6f9c827532313187b7 \
    --hash=sha256:6117b84ea48435e5356dc737f5121485c30920ba43375fa7b434fd753df0eac3 \
    --hash=sha256:6199d5606e2bbf2b096cf64d03f8b6790c91081d5ac866b8e7bb6422738cc60c \
    --hash=sha256:62b55f6722735a6c472f88361cde6640608773d9443cebdbb51abf436a1fcdd3 \
    --hash=sha256:687c9ca3035544b113bea2055e180af96fb63c0c476e22a9180f51925186e7b7 \
    --hash=sha256:6b7430cf5728e68f6c462254009a6ef4086e1bea43cf2f57aa9c55fb4f50ff96 \
    --hash=sha256:6ba32c4d2abf1d2fe7cf27d280f4cca5664233b0f885549c7761719eb977f486 \
    --hash=sha256:6c9cdde8becb25a7fde49924511aa2644d6f8081cc8df8e9452724303348d8e3 \
    --hash=sha256:6df0ec430f9a831772c23ca5a224cba36517a58a84bb32c32bb59a9fa67c47f6 \
    --hash=sha256:6e2912d4babbc65196ac13c2f53468dc57fb8b9c25ef913e8c59ddf7c6dc0e1b \
    --hash=sha256:6e5e4d73d588ca5ed09df1b7dcd1b203d1df3c542e3f50d126c947d432b10731 \
    --hash=sha256:70055ff39b97c99e7ae40ea3e393fb62aa2e44dbd9b29f8d14f42fb0025c3959 \
    --hash=sha256:706bfd38730a5ac7a365793269a00f4e988178cec121391f4248d84ad8c972e9 \
    --hash=sha256:7235dc28fc6dd9d832ac7c7bce95367dedb85929f17368a0c2bee1e080b9acbf \
    --hash=sha256:774d157f112367ff4abd29019f38f023c24e00e56edc7829c20e358a5a913ad8 \
    --hash=sha256:77efcff2b23071c349402ac1066667a3d011f62398d81408c9b88ad991747c9e \
    --hash=sha256:789b8982559ae28dad2356519f841655756cdcd96616410590ae0b17454ee64f \
    --hash=sha256:7ac76cf9afd34929d76eb7fcb63be476a4853d8a96f0dcf2d0db68a0cbdf9885 \
    --hash=sha256:7c0c10730342b0c9b35dd1d619beb8214e520bd96a1f870f452680b238aab3e0 \
    --hash=sha256:823f82903d189af463d7df250ef1f7f696f3cee08cc8d91deb565e8d425f6506 \
    --hash=sha256:838648accb3a7fd9803fd45c87bce8509648eb0c11bc34e216141300977244f2 \
    --hash=sha256:854066be00447fa8de2ccbbe893e2ffc4b123ef16d897af794c1e18bd4a714b0 \
    --hash=sha256:85d5855daafc240cc045c026d7a15fd198a09b0fc8ff6f5ecbb5297b509cb11e \
    --hash=sha256:85de3134b5379856e323ba37c19c9256d39425f7b76a63af52b09fb4664c2e8f \
    --hash=sha256:87e4f41d375c0b9be2fb5251aee4b8a689169e134535aed81bf085c3b647451e \
    --hash=sha256:88ca277405c2d3b71c4e1c2ee0e7966e807bcba86a69d11e19ba199d18ae4491 \
    --hash=sha256:88e85ab89cb822c1e635f51d6d32e488f94e002e70e2f492bdb8b945543f345a \
    --hash=sha256:8ac8c94b6539074e0f40899301273ac8402b9b3e01c7b7ba269ff30340aaaf20 \
    --hash=sha256:8fe532b3c966d1fb794e0698e4589d0444017ae77fc0b31edea13c0e35bcc449 \
    --hash=sha256:9085f87b0e38a2b92b8923059b4e8789fe40d9279712d15dcc670048d77079af \
    --hash=sha256:90b7481fb62fbe172c558bc6fd1c4c98d82004a54a7551f20e11ac9bf0b8708c \
    --hash=sha256:92caef967d287a407085d61176fce4012b1dd62daed4eb6d5ceb26d3d2538712 \
    --hash=sha256:9362dd90aa7dab48c0054a21187791ccf05473f7dba5d92b8033ae62164675e7 \
    --hash=sha256:94d78ecec2605a8d0398b0f365d5f12a63248438516f5dac536a5eff7337df4a \
    --hash=sha256:94fbf1c0c6cc0d3d5e50f9a9313a8cdca90dd696d34b381cd1704f8c9e939f20 \
    --hash=sha256:950f23cb393f85543777b0433f082cddd25b51ab398eac7971146495679efe5f \
    --hash=sha256:96eefc178f8636b9c760c5829345307fd81cfae9ab1e80997dbddeb0f54ee9a3 \
    --hash=sha256:96fef3e886d6a9874b14f27fc193fbdc69d5d8035783d86aa4e1cea594e695f9 \
    --hash=sha256:977cdbd483a9cff38179bea4fd754289a6f2195c7abd414aba85410b3e66cc5e \
    --hash=sha256:978eab16f55b4ab2c2a745be9a0a840bf8f09a7f227d9c76eb30214d078865a5 \
    --hash=sha256:994e883d17c559cdfd38c84003c8b27d25424a1077272a17e7cd27bfe0bf57b2 \
    --hash=sha256:9ac4444d8d4fd4c4bd08bf451ed3167aa9e7ec6cdb41b648794f1d1103652e36 \
    --hash=sha256:9b5db6052055d34d41230fb78d7c439c23dc536a9896f6cb039e8dd92cfc1263 \
    --hash=sha256:9d9a0dc7cbe9bec24c3f767c9122c41fe5a1bc43f47cd099d00d393e09769de4 \
    --hash=sha256:9dbdd9205662134957cf0c324f639bdc5031c0ca056e2369e238db75187c0f11 \
    --hash=sha256:9eea3ab2597a5e65fe65296e2d6a84570845a6b55532d90333d740d48bbc850a \
    --hash=sha256:a2028475ba855475b8b4d3cfeb4994269c967aea8b9892dfba907f4263a863a3 \
    --hash=sha256:a3a370082ce34d0612f421e15fe011c53bb1feff21a26d06ad4fb244dab5a375 \
    --hash=sha256:a545775cfe815855ea32d7c27731d79da358ef2055b4a25830231b1622dd18aa \
    --hash=sha256:a5cbd90ecf0fc62e64726917ad083b73001f0563657a87ec3c0b504e277dc90d \
    --hash=sha256:a6d095662e73e74f0a49988e0593373e243e3a52e27bfeea0a859e88acf4a0f5 \
    --hash=sha256:a6dac12ff6b846103483683f60c5f8fee205121adc58ffd87e90a90a3af69e99 \
    --hash=sha256:a951ad59cad9145664a730d3036b40b844e74d2d3683da40111463cd3a83845d \
    --hash=sha256:aa1099b956fb795e686d073568f6dc002a0bb89765ea6d5b055dd7d9bf1b116c \
    --hash=sha256:aa2bb0b37202dca27175591f761108b5d34096ade1191ffe4808bdf6b1571488 \
    --hash=sha256:aae2ee51122d3ae968a3837d97dc24a0aeebb0dea23694422cd172bd30017cd6 \
    --hash=sha256:ab743e9bc90c1f73552ec33e10e3331315acd2c397b36065b591b0181de533cc \
    --hash=sha256:ac00177c4831ffa650f8609e4bdddd5fe09c03b1c0c47acece7e6ea20421598b \
    --hash=sha256:ac13b004224fb341e1e25a1ed5e19d32f57cdb2a403e01f003b46f051a550f6f \
    --hash=sha256:acaf604462bf330b0d07e7a07c1d6e4adac79e5fb13e9c5140590542cafacc00 \
    --hash=sha256:ae31a1a1db2ee6cc2942fccaf695c934bc7f3db9f2133a3fef1f367cf1a4ab10 \
    --hash=sha256:ae4a097991662cd4fff0ddc74e0fe7874f82e00042fa0ea00855645ed0c79598 \
    --hash=sha256:aea996a6aba25260827c9ea511d1addfde2da9eb686ac961838509086188b7e6 \
    --hash=sha256:b39b69b347e5e47a3b5b8cfc005c68c1ba347474e3960236c4944a8ecd174962 \
    --hash=sha256:b54e7e13267d49ffbfe68e25b3cbd774dab38fa37238f71265e91b36146eb21c \
    --hash=sha256:b9af956078716df40d985fb0dfeb2c2120c5ca92ba4ff4b388acfd01cdc14d08 \
    --hash=sha256:ba2f37ee79e6338845261a3c5b1784e5d1acdff2c0785b284f1b633033d136ab \
    --hash=sha256:ba501e667c17d8411f98e67a022d9604ef179aff0e459b7e292c796837c13573 \
    --hash=sha256:baf3775a2635e5a11fbd5e4e64ee69c7e86875d224a5c72aca4c141064589a90 \
    --hash=sha256:bb57753e36e4855b8ca375069482250a6246372331a3e4f3407eaebb007443f5 \
    --hash=sha256:bd6c173f04743d483881bffa1478d5a4624475b8cd1d2194956a75548e191c18 \
    --hash=sha256:be47f99644b208bff7766314013f9acf57b056b04191d570d68ad14022cf5b1d \
    --hash=sha256:c010f5581d9c612804cc59fcf7b524b707fbcb72828551237ab545bb5c7034af \
    --hash=sha256:c1dcc36dcb96abc02236e182d17e0f71430152a6c2c7447421da2d2dc144edea \
    --hash=sha256:c428c6c31eb5f4277d7f8eccaf767fbd548ddd5ce3c8b4f4cbbfab3d96b5904c \
    --hash=sha256:c658c50ac0c98cd755a2dd50b7977d3bca7df401dcc47fbdfa87db53ef7d4e8b \
    --hash=sha256:c71fb0d56c920c269cd3e2e3fe7c610e3f1fdb21a6ce60efa6430ff63676cea6 \
    --hash=sha256:c7b742bf31c88566b4bb6335a7f393bb322e580b6bb98df7bd0c25e6e3519ce8 \
    --hash=sha256:cc0329df4caaceb950d2f580b5ac716a377f7059624a0bafaeaf8a218c6ed774 \
    --hash=sha256:cc5d36d96478aa9c60654bd932525bf32964c62a7281eafdf16d85003a8d6004 \
    --hash=sha256:ce854f5f478050ade5a238731c4ca985a7d3b3cb53ff600a9b5c3b689b5f0a7a \
    --hash=sha256:ced3fdd71aaa83ce593746c2edb42b7a59cb4c19c8b5c407781c72e493aae55a \
    --hash=sha256:cee5dd7c6fb5dd52a0fe2a740f9bc6e3593f5f8b1788bde49de02086f30182b2 \
    --hash=sha256:cfa1c0cc3a8f9f53f1243a5a99ac36fd003880199383b37672e86ddda9cb07e2 \
    --hash=sha256:d1ee1e296209fdce05b81b663250eefa02213a2da7b41bf26f7829b8ba3545aa \
    --hash=sha256:d59b75732e9b6f27388e10c14b0259cc5f2e48c78627d185e6a177b58ad3cffe \
    --hash=sha256:d63600d620ad0064c3a748b950ac5ea38a80190e5498532efefa4b7b3f1da1f3 \
    --hash=sha256:dd732602a7009217f658d5863d12d79d373a4de0eebc111094bcdd3bb8e0a6cc \
    --hash=sha256:e06efa066f7dbadbc84ebc126a97c452a6451dfcf589d89d788484949e1cf795 \
    --hash=sha256:e199fb99720074809a7720f1c0b4d919eea8b87e88713e0f8f602f7bef543d9d \
    --hash=sha256:e4b018dc5a0eee4676e38fe84a47a427816c590b93b55d9025274ec4d6ffc2dc \
    --hash=sha256:e6621fb2a4988d6e53eedc455e5903e2679f3967b8acb3d639f1b63c14a2e893 \
    --hash=sha256:e71c909f353863b2b89c83de2ebed71ea6d0df8a6ef65a128193c5e650766bef \
    --hash=sha256:e90251c0c7bdd54a100a0dce3c07b7e637278c93af29dbf78ebb89a58c4bac7d \
    --hash=sha256:e9fbdce1e47394b09bc9f26ab117dfc8d6491977a11d86f592bb42c779db2fda \
    --hash=sha256:eb12fb2ba69ffa05f8695f61c69e591dc4b4a12ac3757ac8af8adb259bf56d17 \
    --hash=sha256:eda059b6bc8bc0812d626fd91a7ce01bf583df0a61296eff390fd94141a34e30 \
    --hash=sha256:f03ac127268b43ef4fe9e6ab6794a6794b49485a0cc0c1db79876d2f33f75bc7 \
    --hash=sha256:f298e218441525d3794428b4c8b8fb8662c6d3ea79925d4807ee6b9a96a3bca5 \
    --hash=sha256:f5542f9b941279d82d41eb0aa9f98eba36fe4df5c7086c651df7944935b37182 \
    --hash=sha256:f6f7deae3feb4edfa2efaf7c574fe88cbf055038a6abdb40188e4fff66d5699f \
    --hash=sha256:f9b1e28d0e8dbfa858abdba91d6b547beaf2df1a59bec6da6faae7b96a4991a9 \
    --hash=sha256:f9f8405c2c758532c74fed975dbee57be1f31a6e865c031870c79a6ed3212ada \
    --hash=sha256:fa48b1b63d639f9483e0633e092f5851e2348c352f1f9bb6c8182f87884ef876 \
    --hash=sha256:fb78f6e7fcd8ad785d28cd577168bc1aaee827b25bb8755638f694794ea98f0a \
    --hash=sha256:fbc597639158fd7c14d55e808718848319540f51b0e6746e3eefa59723a4a348 \
    --hash=sha256:fce8cbd4997efeb450bd298b54f755dcdff18d496f7a5ddbb4867c6d7c88fdc3 \
    --hash=sha256:fd0350afdc3aabd5576f60ea109228bd5538139713c7b094c5cd27c73a98bc6f \
    --hash=sha256:fd0a274c0e5f9a21565cd9d3dd749b61f96b7aa1e20a93aa1ba4029518f2e5c0 \
    --hash=sha256:fdb8a068947befafba9952162645dc2fecaeb400e64584829ed5e9b2fbe21a7f
    # via reportlab
click==8.5.0 \
    --hash=sha256:255bc9599cf7748b4b1a446ccc735421bd08a2ae529a8b88597d3de5664ee360 \
    --hash=sha256:ba0d2089de75ea0310e2dde03160e6ca10009947fb95a182f9b54021bb272e34
    # via uvicorn
fastapi==0.141.1 \
    --hash=sha256:bfb91aa2d334c61cb35ba9a116fc123b3d3df31640b801cf57a7a78ec3f603b3 \
    --hash=sha256:e8822fc40db1e1858054d7a949a888695bc9bdce70139178e33bd2871a453ca1
    # via -r backend/requirements.txt
greenlet==3.5.6 \
    --hash=sha256:0616b8f878098c5681fd8f0dc92d887551717402342a70f0abcbfea5f5ad8a44 \
    --hash=sha256:06c0e933290fba8ffe53ead4ae1b8044b0e9754b75cebf381aa2bc3e50d82fac \
    --hash=sha256:128813fc29f2336a21b4d06eedd5e16bcc7ea46f59e9ff1cb30ea70e48195d88 \
    --hash=sha256:188bf333769b7145e2b0b4a7f09615ec550ed44d3a2a8395fb7b36f0e9901e13 \
    --hash=sha256:1c20ea32a73d17b9b60e3371240e17b0068120c98a5ec01a224a7dd8c89733ba \
    --hash=sha256:2ab5f42ac6c238eb71770715e6e909ad9a1a92b6c681ccb64cd5a0f07edb953f \
    --hash=sha256:301102a49120b095e72a7838792b41233975fc1c155daec6d98f81c00c9280e0 \
    --hash=sha256:311018b46472fb26ee85870847fb89eb64cc8aaddb617400789d87076f7cfeec \
    --hash=sha256:3ac3494c381dab876cad7d0b22f3a722f3e0c8deb3a65b9e7f35ad7f58b8fcb3 \
    --hash=sha256:3c6dede9133e1da41d561bc3fb14e92b47e2ce39ae60edefaad145658ea7c5e2 \
    --hash=sha256:3dbb4596a6a4e5d47121a33ff20533a81e60f302d9e67b69909a8bc21a43f0a7 \
    --hash=sha256:3deccbb57a481e3a408fe61cdfd5c13e0678fc0a30fdd09597917ca87b4be877 \
    --hash=sha256:45663c01a4de48b9a64a2ee1509d92d1dfd3afb02b2ccfc9333029d11aef996a \
    --hash=sha256:45bfd2b51e38aaa5f9849f114d9c7c1d75f69187c849b3549cd64c465283abfa \
    --hash=sha256:460e70b033aba8ed47e2ac9b5d0d2157b05a34fbfa30a241400aef4118902cdc \
    --hash=sha256:4fb8e59f68845d56c23c031dcd79c329f345e4a9d2ffac91c3d1ab366bdc457b \
    --hash=sha256:520648db8fb92eef7b3e6013f5a6f901cdf0d6685f639c2f7a245879f865bef7 \
    --hash=sha256:5599b380c1f28efeb724e81569eac80cd92f99a85bd9775456caaf3225d40b11 \
    --hash=sha256:59deccd347735a7774223b05a93773fddbb298aba3cea21be4337fb4752dbe32 \
    --hash=sha256:5a0b2791239c99992a86c1b635b787fe2a877d9eaaa26f8891ce943832b585ae \
    --hash=sha256:5adcbbfe78bdc242c71740a02e0991cc1b2f34d33c8bb15ca45eee8fd1140942 \
    --hash=sha256:5b602b4201b965a8354d74e232364a66ff243dd142e350d035f46169bb36e13d \
    --hash=sha256:5bbda3c70dd35d60671bc33b01916802707a052130d9e50cdb871d34594d35cb \
    --hash=sha256:602024dae6d77e161f4b89491b62ca1d4f19949d79d47b2db057e476d21179d6 \
    --hash=sha256:61a61b4a95a4f97922c3a6f5606d3e360851584bd47e500a5161373c53810e3d \
    --hash=sha256:63aff70fe5aac59c72215f42ec39fcb59ff46774fa966e717f8ecb6ee2273577 \
    --hash=sha256:71890d5247020c25c21a6b65202782bfc281d4e6e244842419d30e3492bb6dcc \
    --hash=sha256:73a29b5ba642e35433166a03a3e02935e7238c4b3467fbd77523b99edea23e5b \
    --hash=sha256:7969bffa322c097bd46ae595ada6a931cefda613f18ba64587e9cff4cb320756 \
    --hash=sha256:7ac4abb3877c43af320392c664774eef6fa2cc063c79a55fc02d844a3cbe7395 \
    --hash=sha256:7f731ebac68ea06d628658295cb2d217b10186329fcf9a3b6a149045059bf92e \
    --hash=sha256:7f924a5a9d5890649566f2f6682e0d8ad8ca23028bacffbbac36dbd7fd680176 \
    --hash=sha256:874cea8bb1ec1ddccbacbd027856f6bf496f6bc18aba97a918c20e067edab236 \
    --hash=sha256:876077e7ebb8c84ed068e2b23d4c62ebb010d60df84b9591af1be2f39010ffb2 \
    --hash=sha256:886bcf1870af74c32bc310fd00a6b803445e17e51b7d5a107c7b35c0f362cc16 \
    --hash=sha256:8b27df301f56e3b3d2298095c8f7d6b68f2521f6b1693e901fa039bdbae34424 \
    --hash=sha256:8b7c73d1cef3d9ae963e9ff03f6222df43efbb9054ffd2f1969c935b7fc84c02 \
    --hash=sha256:8cda13494d86a4f12429641117cb6ac4bbbc9c30a33f711f7d3a2e5fbe4b0b7e \
    --hash=sha256:8cddea1b8339451c2fb3388e138347b6126744f33b611bdb55b7357361cfef46 \
    --hash=sha256:8dba0129b93e7091dfefaf4cf7000172741bff7f47bf6326fcf17f32fbb54d6b \
    --hash=sha256:8e67c43bdfc88d5fee6db0d3e40175b362fc95fb85f0412d233b9b203c53a575 \
    --hash=sha256:9133d68624b1f2e89ec2f554d56aea8a5b0d7168cd9320200ba58d4d794845a4 \
    --hash=sha256:916f92f2a8db10508f739d0b5e00b83defe5d1115a997c54532a6d7cf8c95404 \
    --hash=sha256:9297fb9c39b9a2c039dbcd306c410bd6906b95244dec3bba4318d36c718c164c \
    --hash=sha256:95e7c44d072db623a1aab04ce488cf9533294a77ed9d072cd503a3596f4106ac \
    --hash=sha256:975736b002ed080d124cf81a79cb7e05cb26d6b3f5c7a7b651c0fcce70353aa1 \
    --hash=sha256:97c5a53e8c1754df58e73f047a99e287d4da1bdfe64b0072fb25c87000897951 \
    --hash=sha256:9a09d59bef1db94f384b5bcc2d523694d338f3df6b757aeeaf7baca5d0c0be88 \
    --hash=sha256:a364c1ea75dc51b83a17f52fe0c79cf8bc4ddf740403bebd4581c7666eea017d \
    --hash=sha256:a3b4a01c6da07ef9f80d4fe8933b994bc99747bcea3eab0330a9c34d3c12655b \
    --hash=sha256:a5876d0a60355af98d535c47f6cd6eb0f8a432396dab26845d380b92f8412422 \
    --hash=sha256:a6a4b98a9132e0f45c9fc245a63894cfd8c45fb7a0d6bffc5eab3ec327cf7324 \
    --hash=sha256:a6b4ff33f7e011bbaa148238d131c4fd4f8afbab3c104ddfbdb2b12b74ff7016 \
    --hash=sha256:a93ee7c6e8fd0f8a83525a51bd777be57ee17787e91d805bd8d6faf9dcada18e \
    --hash=sha256:b374e79ffa7511afc11773aef40a4ccea6191fba1c856ea2f9c56738dca69d7a \
    --hash=sha256:b7d501d5eb5d4f67207df364752ad697465b834268744be7581c18d81d35d41d \
    --hash=sha256:c59acfa8eb73a1e0d484392dc002bdf001fd4ce73394e0132df3d1ab6093d7cb \
    --hash=sha256:c75116c9de79949de23006e2d9b35ee82874c594fcf5c0311b439acaa14b8441 \
    --hash=sha256:ca80a49b53ed1d22f7282da7255f7bb2fd1935fd0f623d8613fda38745f18961 \
    --hash=sha256:cad5782f93f7f738b62c6527b6f32a60694d924029f299a8b524758cfa53d815 \
    --hash=sha256:ccadce0130fd813ec86ebfe969a6c58b42acc1d0fe55a47525375b740e07b605 \
    --hash=sha256:d701eab36200c36224833d07dbdb709adb7fd4253429548ddb5e547b8ed40586 \
    --hash=sha256:dad3d233d441a022c1f7155f0fb9d5aff7b97c1ea8c7dfa02cce586b16ab2d0b \
    --hash=sha256:dd0b83bed3405b586a3133629f1d1a5bc7bfd64822a3b7ab342bdc68e6dbc61b \
    --hash=sha256:de3de000d459402cda015068fd135aa50c0bf6f2477a80d4da1e646f123b4e78 \
    --hash=sha256:de9923832f2d8c1a5ecd8d7260465a6ca5a86888a0d129e3bd5cf0406d2fc5bf \
    --hash=sha256:df19e2d0b1620039af5102563fbd96e8938c7f5c3f5828528d641d9fc585525e \
    --hash=sha256:e85880b538e59a59f55117b81f208a6660ad5ac328aad9305f812d9b8bc67a0f \
    --hash=sha256:ee7d9da3bf493909cf811a3f038840cb34fab5ae2956b8a263919f6e289ab188 \
    --hash=sha256:eed88b64a5e5da72d6a71cdc5aaeefaa5ced9b748f8d19f89800b339961dad39 \
    --hash=sha256:f0ba7c2a329d650628f4c8572fd1db29f0a59dd70a3e3e0710dcf18a35cce9d8 \
    --hash=sha256:f8e63209c3e1e828ee6a457529b4a6d8b05d050fe0ae03a7ae49e967c5d312e0 \
    --hash=sha256:f8f0bd690e1a41294ac87905e8121c81a3761ec2583c768f13467428606c8c7a \
    --hash=sha256:f96f0e30b5a95c7631b12bfe214cbc90ec8fe8cfa36920596c10514a65743519 \
    --hash=sha256:f98e8215e172f567ce80eeaed9107fb4d32b6c44f26983d9b8334658136a205a \
    --hash=sha256:f9fe868463ec7e1363733af77e38a5fda3e9b63940337048c945d69e0c80ff24 \
    --hash=sha256:fdacf26402389bdd89857ad3c045a26fe8f3314f9a8b28226f82f88463a65b77 \
    --hash=sha256:fe3170a69fe039b18ad18171e66faa9a75f6fe9d78f968fd9b54e09fbd714d81 \
    --hash=sha256:fea4427d1ffdb3b523d7daa6712038428a4c16c450b9777bdd1221cfee0eab49
    # via sqlalchemy
h11==0.16.0 \
    --hash=sha256:4e35b956cf45792e4caa5885e69fba00bdbc6ffafbfa020300e549b208ee5ff1 \
    --hash=sha256:63cf8bbe7522de3bf65932fda1d9c2772064ffb3dae62d55932da54b31cb6c86
    # via
    #   httpcore
    #   uvicorn
httpcore==1.0.9 \
    --hash=sha256:2d400746a40668fc9dec9810239072b40b4484b640a8c38fd654a024c7a1bf55 \
    --hash=sha256:6e34463af53fd2ab5d807f399a9b45ea31c3dfa2276f15a2c3f00afff6e176e8
    # via httpx
httpx==0.28.1 \
    --hash=sha256:75e98c5f16b0f35b567856f597f06ff2270a374470a5c2392242528e3e3e42fc \
    --hash=sha256:d909fcccc110f8c7faf814ca82a9a4d816bc5a6dbfea25d6591d6985b8ba59ad
    # via -r backend/requirements.txt
idna==3.20 \
    --hash=sha256:a7db850025b95ded1eae8a46181a1a6c56c92c96f0e2b005d9ff8dc0210cab44 \
    --hash=sha256:ab7ae7122974553370f0bdb919e1a960b2cd1bc1ef0276416d896db81c14582c
    # via
    #   anyio
    #   httpx
iniconfig==2.3.0 \
    --hash=sha256:c76315c77db068650d49c5b56314774a7804df16fee4402c1f19d6d15d8c4730 \
    --hash=sha256:f631c04d2c48c52b84d0d0549c99ff3859c98df65b3101406327ecc7d53fbf12
    # via pytest
jmespath==1.1.0 \
    --hash=sha256:472c87d80f36026ae83c6ddd0f1d05d4e510134ed462851fd5f754c8c3cbb88d \
    --hash=sha256:a5663118de4908c91729bea0acadca56526eb2698e83de10cd116ae0f4e97c64
    # via
    #   boto3
    #   botocore
mako==1.4.1 \
    --hash=sha256:a359d9a94a541213958742b2698d0a7757bb83551767bc468a74b9905aba9617 \
    --hash=sha256:d7904710b662996425a21627710c4777c45053146942cf8a7aebf757c92b8c27
    # via alembic
markupsafe==3.0.3 \
    --hash=sha256:0303439a41979d9e74d18ff5e2dd8c43ed6c6001fd40e5bf2e43f7bd9bbc523f \
    --hash=sha256:068f375c472b3e7acbe2d5318dea141359e6900156b5b2ba06a30b169086b91a \
    --hash=sha256:0bf2a864d67e76e5c9a34dc26ec616a66b9888e25e7b9460e1c76d3293bd9dbf \
    --hash=sha256:0db14f5dafddbb6d9208827849fad01f1a2609380add406671a26386cdf15a19 \
    --hash=sha256:0eb9ff8191e8498cca014656ae6b8d61f39da5f95b488805da4bb029cccbfbaf \
    --hash=sha256:0f4b68347f8c5eab4a13419215bdfd7f8c9b19f2b25520968adfad23eb0ce60c \
    --hash=sha256:1085e7fbddd3be5f89cc898938f42c0b3c711fdcb37d75221de2666af647c175 \
    --hash=sha256:116bb52f642a37c115f517494ea5feb03889e04df47eeff5b130b1808ce7c219 \
    --hash=sha256:12c63dfb4a98206f045aa9563db46507995f7ef6d83b2f68eda65c307c6829eb \
    --hash=sha256:133a43e73a802c5562be9bbcd03d090aa5a1fe899db609c29e8c8d815c5f6de6 \
    --hash=sha256:1353ef0c1b138e1907ae78e2f6c63ff67501122006b0f9abad68fda5f4ffc6ab \
    --hash=sha256:15d939a21d546304880945ca1ecb8a039db6b4dc49b2c5a400387cdae6a62e26 \
    --hash=sha256:177b5253b2834fe3678cb4a5f0059808258584c559193998be2601324fdeafb1 \
    --hash=sha256:1872df69a4de6aead3491198eaf13810b565bdbeec3ae2dc8780f14458ec73ce \
    --hash=sha256:1b4b79e8ebf6b55351f0d91fe80f893b4743f104bff22e90697db1590e47a218 \
    --hash=sha256:1b52b4fb9df4eb9ae465f8d0c228a00624de2334f216f178a995ccdcf82c4634 \
    --hash=sha256:1ba88449deb3de88bd40044603fafffb7bc2b055d626a330323a9ed736661695 \
    --hash=sha256:1cc7ea17a6824959616c525620e387f6dd30fec8cb44f649e31712db02123dad \
    --hash=sha256:218551f6df4868a8d527e3062d0fb968682fe92054e89978594c28e642c43a73 \
    --hash=sha256:26a5784ded40c9e318cfc2bdb30fe164bdb8665ded9cd64d500a34fb42067b1c \
    --hash=sha256:2713baf880df847f2bece4230d4d094280f4e67b1e813eec43b4c0e144a34ffe \
    --hash=sha256:2a15a08b17dd94c53a1da0438822d70ebcd13f8c3a95abe3a9ef9f11a94830aa \
    --hash=sha256:2f981d352f04553a7171b8e44369f2af4055f888dfb147d55e42d29e29e74559 \
    --hash=sha256:32001d6a8fc98c8cb5c947787c5d08b0a50663d139f1305bac5885d98d9b40fa \
    --hash=sha256:3524b778fe5cfb3452a09d31e7b5adefeea8c5be1d43c4f810ba09f2ceb29d37 \
    --hash=sha256:3537e01efc9d4dccdf77221fb1cb3b8e1a38d5428920e0657ce299b20324d758 \
    --hash=sha256:35add3b638a5d900e807944a078b51922212fb3dedb01633a8defc4b01a3c85f \
    --hash=sha256:38664109c14ffc9e7437e86b4dceb442b0096dfe3541d7864d9cbe1da4cf36c8 \
    --hash=sha256:3a7e8ae81ae39e62a41ec302f972ba6ae23a5c5396c8e60113e9066ef893da0d \
    --hash=sha256:3b562dd9e9ea93f13d53989d23a7e775fdfd1066c33494ff43f5418bc8c58a5c \
    --hash=sha256:457a69a9577064c05a97c41f4e65148652db078a3a509039e64d3467b9e7ef97 \
    --hash=sha256:4bd4cd07944443f5a265608cc6aab442e4f74dff8088b0dfc8238647b8f6ae9a \
    --hash=sha256:4e885a3d1efa2eadc93c894a21770e4bc67899e3543680313b09f139e149ab19 \
    --hash=sha256:4faffd047e07c38848ce017e8725090413cd80cbc23d86e55c587bf979e579c9 \
    --hash=sha256:509fa21c6deb7a7a273d629cf5ec029bc209d1a51178615ddf718f5918992ab9 \
    --hash=sha256:5678211cb9333a6468fb8d8be0305520aa073f50d17f089b5b4b477ea6e67fdc \
    --hash=sha256:591ae9f2a647529ca990bc681daebdd52c8791ff06c2bfa05b65163e28102ef2 \
    --hash=sha256:5a7d5dc5140555cf21a6fefbdbf8723f06fcd2f63ef108f2854de715e4422cb4 \
    --hash=sha256:69c0b73548bc525c8cb9a251cddf1931d1db4d2258e9599c28c07ef3580ef354 \
    --hash=sha256:6b5420a1d9450023228968e7e6a9ce57f65d148ab56d2313fcd589eee96a7a50 \
    --hash=sha256:722695808f4b6457b320fdc131280796bdceb04ab50fe1795cd540799ebe1698 \
    --hash=sha256:729586769a26dbceff69f7a7dbbf59ab6572b99d94576a5592625d5b411576b9 \
    --hash=sha256:77f0643abe7495da77fb436f50f8dab76dbc6e5fd25d39589a0f1fe6548bfa2b \
    --hash=sha256:795e7751525cae078558e679d646ae45574b47ed6e7771863fcc079a6171a0fc \
    --hash=sha256:7be7b61bb172e1ed687f1754f8e7484f1c8019780f6f6b0786e76bb01c2ae115 \
    --hash=sha256:7c3fb7d25180895632e5d3148dbdc29ea38ccb7fd210aa27acbd1201a1902c6e \
    --hash=sha256:7e68f88e5b8799aa49c85cd116c932a1ac15caaa3f5db09087854d218359e485 \
    --hash=sha256:83891d0e9fb81a825d9a6d61e3f07550ca70a076484292a70fde82c4b807286f \
    --hash=sha256:8485f406a96febb5140bfeca44a73e3ce5116b2501ac54fe953e488fb1d03b12 \
    --hash=sha256:8709b08f4a89aa7586de0aadc8da56180242ee0ada3999749b183aa23df95025 \
    --hash=sha256:8f71bc33915be5186016f675cd83a1e08523649b0e33efdb898db577ef5bb009 \
    --hash=sha256:915c04ba3851909ce68ccc2b8e2cd691618c4dc4c4232fb7982bca3f41fd8c3d \
    --hash=sha256:949b8d66bc381ee8b007cd945914c721d9aba8e27f71959d750a46f7c282b20b \
    --hash=sha256:94c6f0bb423f739146aec64595853541634bde58b2135f27f61c1ffd1cd4d16a \
    --hash=sha256:9a1abfdc021a164803f4d485104931fb8f8c1efd55bc6b748d2f5774e78b62c5 \
    --hash=sha256:9b79b7a16f7fedff2495d684f2b59b0457c3b493778c9eed31111be64d58279f \
    --hash=sha256:a320721ab5a1aba0a233739394eb907f8c8da5c98c9181d1161e77a0c8e36f2d \
    --hash=sha256:a4afe79fb3de0b7097d81da19090f4df4f8d3a2b3adaa8764138aac2e44f3af1 \
    --hash=sha256:ad2cf8aa28b8c020ab2fc8287b0f823d0a7d8630784c31e9ee5edea20f406287 \
    --hash=sha256:b8512a91625c9b3da6f127803b166b629725e68af71f8184ae7e7d54686a56d6 \
    --hash=sha256:bc51efed119bc9cfdf792cdeaa4d67e8f6fcccab66ed4bfdd6bde3e59bfcbb2f \
    --hash=sha256:bdc919ead48f234740ad807933cdf545180bfbe9342c2bb451556db2ed958581 \
    --hash=sha256:bdd37121970bfd8be76c5fb069c7751683bdf373db1ed6c010162b2a130248ed \
    --hash=sha256:be8813b57049a7dc738189df53d69395eba14fb99345e0a5994914a3864c8a4b \
    --hash=sha256:c0c0b3ade1c0b13b936d7970b1d37a57acde9199dc2aecc4c336773e1d86049c \
    --hash=sha256:c47a551199eb8eb2121d4f0f15ae0f923d31350ab9280078d1e5f12b249e0026 \
    --hash=sha256:c4ffb7ebf07cfe8931028e3e4c85f0357459a3f9f9490886198848f4fa002ec8 \
    --hash=sha256:ccfcd093f13f0f0b7fdd0f198b90053bf7b2f02a3927a30e63f3ccc9df56b676 \
    --hash=sha256:d2ee202e79d8ed691ceebae8e0486bd9a2cd4794cec4824e1c99b6f5009502f6 \
    --hash=sha256:d53197da72cc091b024dd97249dfc7794d6a56530370992a5e1a08983ad9230e \
    --hash=sha256:d6dd0be5b5b189d31db7cda48b91d7e0a9795f31430b7f271219ab30f1d3ac9d \
    --hash=sha256:d88b440e37a16e651bda4c7c2b930eb586fd15ca7406cb39e211fcff3bf3017d \
    --hash=sha256:de8a88e63464af587c950061a5e6a67d3632e36df62b986892331d4620a35c01 \
    --hash=sha256:df2449253ef108a379b8b5d6b43f4b1a8e81a061d6537becd5582fba5f9196d7 \
    --hash=sha256:e1c1493fb6e50ab01d20a22826e57520f1284df32f2d8601fdd90b6304601419 \
    --hash=sha256:e1cf1972137e83c5d4c136c43ced9ac51d0e124706ee1c8aa8532c1287fa8795 \
    --hash=sha256:e2103a929dfa2fcaf9bb4e7c091983a49c9ac3b19c9061b6d5427dd7d14d81a1 \
    --hash=sha256:e56b7d45a839a697b5eb268c82a71bd8c7f6c94d6fd50c3d577fa39a9f1409f5 \
    --hash=sha256:e8afc3f2ccfa24215f8cb28dcf43f0113ac3c37c2f0f0806d8c70e4228c5cf4d \
    --hash=sha256:e8fc20152abba6b83724d7ff268c249fa196d8259ff481f3b1476383f8f24e42 \
    --hash=sha256:eaa9599de571d72e2daf60164784109f19978b327a3910d3e9de8c97b5b70cfe \
    --hash=sha256:ec15a59cf5af7be74194f7ab02d0f59a62bdcf1a537677ce67a2537c9b87fcda \
    --hash=sha256:f190daf01f13c72eac4efd5c430a8de82489d9cff23c364c3ea822545032993e \
    --hash=sha256:f34c41761022dd093b4b6896d4810782ffbabe30f2d443ff5f083e0cbbb8c737 \
    --hash=sha256:f3e98bb3798ead92273dc0e5fd0f31ade220f59a266ffd8a4f6065e0a3ce0523 \
    --hash=sha256:f42d0984e947b8adf7dd6dde396e720934d12c506ce84eea8476409563607591 \
    --hash=sha256:f71a396b3bf33ecaa1626c255855702aca4d3d9fea5e051b41ac59a9c1c41edc \
    --hash=sha256:f9e130248f4462aaa8e2552d547f36ddadbeaa573879158d721bbd33dfe4743a \
    --hash=sha256:fed51ac40f757d41b7c48425901843666a6677e3e8eb0abcff09e4ba6e664f50
    # via mako
packaging==26.3 \
    --hash=sha256:94edc256424af38762eb31306eed28beb9f0efc50a8837492c9d6fd6004aed79 \
    --hash=sha256:d7193f7c8e4e93f444fde0262bf90af30e16fa0ad0ad44cb553c87339b23cd1c
    # via pytest
pillow==12.3.0 \
    --hash=sha256:00808c5e14ef63ac5161091d242999076604ff74b883423a11e5d7bbb38bf756 \
    --hash=sha256:04f01d28a6aaff387bf842a13be313df23ba0597a44f1a976c9feb3c6ff4711a \
    --hash=sha256:06ff022112bc9cbf83b60f8e028d94ad87b60621706487e65f673de61610ab59 \
    --hash=sha256:0740a512dc522224c77d9aa5a8d70d8b7d73fb91f2c21125d8d025d3b8990e45 \
    --hash=sha256:0847a763afefb695bc912d7c131e7e0632d4edc1d8698f58ddabec8e46b8b6d3 \
    --hash=sha256:0dd2064cbc55aaec028ef5fbb60fa47bb6c3e7918e07ff17935284b227a9d2df \
    --hash=sha256:0feb2e9d6ad6c9e3c06effe9d00f3f1e618a6643273576b016f591e9315a7139 \
    --hash=sha256:10e41f0fbf1eec8cfd234b8fe17a4caac7c9d0db4c204d3c173a8f9f6ef3232b \
    --hash=sha256:1182d52bc2d5e5d7d0949503aa7e36d12f42205dc287e4883f407b1988820d39 \
    --hash=sha256:164b31cd1a0490ab6efae01aa5df49da7061be0af1b30e035b6e9a1bfe34ee6e \
    --hash=sha256:1657923d2d45afb66526e5b933e5b3052e6bdea196c90d3abb2424e18c77dae8 \
    --hash=sha256:186941b6aef820ad110fb01fb06eb925374dc3a21b17e37ec9a53b250c6fe2d1 \
    --hash=sha256:1cca606cd25738df4ed873d5ad46bbdb3d83b5cbca291f6b4ff13a4df6b0bbe8 \
    --hash=sha256:21900ce7ba264168cd50defae43cd75d25c833ad4ad6e73ffc5596d12e25ac89 \
    --hash=sha256:236ff70b9312fb68943c703aa842ca6a758abfa45ac187a5e7c1452e96ef72b5 \
    --hash=sha256:23aceaa007d6172b02c277f0cd359c79492bbb14f7072b4ede9fbcaf20648130 \
    --hash=sha256:23d27a3e0307ec2244cc51e7287b919aa68d097504ebe19df4e76a98a3eea5bd \
    --hash=sha256:24870b09b224f7ae3c39ed07d10e819d06f8720bc551847b1d623832b5b0e28d \
    --hash=sha256:251bf95b67017e27b13d82f5b326234ca62d70f9cf4c2b9032de2358a3b12c7b \
    --hash=sha256:25b9b82bb22e6e2b3cd07b39c68b7b862001226cb3dff7130d1cb914121b39ed \
    --hash=sha256:28ce87c5ab450a9dd970b52e5aca5fe63ed432d18a2eaddd1979a00a1ba24ace \
    --hash=sha256:300557495eb45ebb8aec96c2da9c4be642fbf7cd937278b4013ba894ea8eb0eb \
    --hash=sha256:30f2aa603c41533cc25c05acd0da21636e84a315768feb631c937177db558931 \
    --hash=sha256:331b624368d4f1d069149002f25f44bc61c8919ce8ddb3c45bdad8f6e2d89510 \
    --hash=sha256:37d6d0a00072fd2948eb22bce7e1475f34569d90c87c59f7a2ec59541b77f7a6 \
    --hash=sha256:37dc8f7bbb66efe481bb60defacef820c950c24713fb44962ed6aa2a50966de1 \
    --hash=sha256:3b8182a766685eaa002637e28b4ec8d6b18819a0c71f579bf0dbaa5830297cce \
    --hash=sha256:3edce1d53195db527e0191f84b71d02022de0540bf43a16ed734ed7537b07385 \
    --hash=sha256:446c34dcc4324b084a53b705127dc15717b22c5e140ae0a3c38349d4efec071e \
    --hash=sha256:4998562bf62a445225f22e07c896bb04b35b1b1f2eb6d760584c9c51d7a5f78c \
    --hash=sha256:4b0a7fe987b14c31ebda6083f74f22b561fd3739bc0ac51e019622e3d72668c7 \
    --hash=sha256:4e8c2a84d977f50b9daed6eeaf3baef67d00d5d74d932288f02cb94518ee3ace \
    --hash=sha256:4f883547d4b7f0495ebe7056b0cc2aea76094e7a4abc8e933540f3271df27d9c \
    --hash=sha256:514435a37670e3e5e08f3945b68718b6ed329bb84367777e16f9f4dfe1e61a0f \
    --hash=sha256:53aa02d20d10c3d814d536aa4e5ac9b84ca0ff5a88377963b085ad6822f93e64 \
    --hash=sha256:5594fc43d548a7ed94949d139aa1341b270f1863f11cfd37f5a6c8b778a6b67f \
    --hash=sha256:571b9fcb07b97ef3a492028fb3d2dc0993ca23a06138b0315286566d29ef718a \
    --hash=sha256:57b3d78c95ba9059768b10e28b813002261d3f3dfc55cc48b0c988f625175827 \
    --hash=sha256:5afb51d599ea772b8365ae807ae557f18bccfe46ab261fd1c2a9ed700fc6eb17 \
    --hash=sha256:6b02afb9b97f65fbca5f31db6a2a3ba21aa93030225f150fa3f249717e938fb4 \
    --hash=sha256:6c0016e7b354317c4e9e525b937ac8596c38d2d232b419529b9cd7a1cd46e39a \
    --hash=sha256:71d6097b330eea8fd15097780c8e89cb1a8ce7838669f48c5bacd6f663dd4701 \
    --hash=sha256:756c768d0c9c2955feb7a56c37ea24aea2e369f8d36a88da270b6a9f19e62b5e \
    --hash=sha256:78cb2c6865a35ab8ff8b75fd122f6033b92a62c82801110e48ddd6c936a45d91 \
    --hash=sha256:7a743ff716f746fc19a9557f60dab1600d4613255f8a7aeb3cdde4db7eb15a66 \
    --hash=sha256:85f998ea1848bc6757289e739cfbdda3a04adfd58b02fc018ce54d754a5ce468 \
    --hash=sha256:8728f216dcdb6e6d555cf971cb34076139ad74b31fc2c14da4fafc741c5f6217 \
    --hash=sha256:877c3f311ff35410f690861c4409e7ccbf0cd2f878e50628a28e5a0bb689e658 \
    --hash=sha256:8cd2f7bdda092d99c9fc2fb7391354f306d01443d22785d0cbfafa2e2c8bb418 \
    --hash=sha256:8e95e1385e4998ae9694eeaa4730ba5457ff61185b3a55e2e7bea0880aef452a \
    --hash=sha256:962864dc93511324d51ddbb5b9f8731bf71675b93ca612a07441896f4688fb8c \
    --hash=sha256:9cf95fe4d0f84c82d282745d9bb08ad9f926efa00be4697e767b814ce40d4330 \
    --hash=sha256:9e881fca225083806662a5c43d627d215f258ff43c890f831966c7d7ba9c7402 \
    --hash=sha256:a2b55dd6b2a4c4b7d87ffa56bdb33fdc5fdb9a462173861a7bc097f17d91cb09 \
    --hash=sha256:a45650e8ce7fafffd731db8550230db6b0d306d181a90b67d3e6bca2f1990930 \
    --hash=sha256:a876864214e136f0eb367788dbd7df045f4806801518e2cfe9e13229cfe06d8f \
    --hash=sha256:ae26d61dfa7a47befdc7572b521024e8745f3d809bd95ca9505a7bba9ef849ec \
    --hash=sha256:af8d94b0db561cf68b88a267c5c44b49e134f525d0dc2cb7ed413a66bc23559a \
    --hash=sha256:b343699e8308bdc51978310e1c959c584e7869cc8c40780058c87da7781a1e94 \
    --hash=sha256:b3c777e849237620b022f7f297dd67705f9f5cf1685f09f02e46f93e92725468 \
    --hash=sha256:b629de27fda84b42cde7edef0d85f13b958b47f6e9bbcbba9b673c562a89bd8b \
    --hash=sha256:ba09209fbe443b4acccebe845d8a138b89a8f4fbaeedd44953490b5315d5e965 \
    --hash=sha256:ba54cfebe86920a559a7c4d6b9050791c20513650a1952ebe3368c7dc70306f8 \
    --hash=sha256:bcb46e2f9feff8d06323983bd83ed00c201fdcab3d74973e7072a889b3979fcd \
    --hash=sha256:bcc33feacfaefce60c12fd500a277533bdc02b10a19f7f6d348763d8140bbba7 \
    --hash=sha256:bf16ba1b4d0b6b7c8e534936632270cf70eb00dbe09005bc345b2677b726855c \
    --hash=sha256:cf1845d02ad822a369a49f2bb9345b1614744267682e7a03527dc3bf6eea1777 \
    --hash=sha256:d69141514cc30b774ceea5e3ed3a6635c8d8a96edf664689b890f4089111fb35 \
    --hash=sha256:d9c7f76c0673154f044e9d78c8655fb4213f6ca31a836df48b40fe5d187717b9 \
    --hash=sha256:dbce0b29841537a2fa4a214c2bbf14de3587c9680caa9b4e217568472490b28f \
    --hash=sha256:dc624f6bc473dacdf7ef7eb8678d0d08edf15cd94fad6ae5c7d6cc67a4e4902f \
    --hash=sha256:e158cb00350dc278f3b91551101aa7d12415a66ebf2c91d8d5ac14e56ddd3ad0 \
    --hash=sha256:e491916b378fba47242221bb9ead245211b70d504f495d105d17b14a24b4907c \
    --hash=sha256:e795b7eb908249c4e43c7c99fac7c2c75dab0c43566e37db472a355f63693d71 \
    --hash=sha256:e7e480451b9fa137494bccd3a7d69adbe8ac65a87d97be61e11f1b1050a5bac3 \
    --hash=sha256:e91206ee562682b51b98ef4b26a6ef48fd84e15fd4c4bc5ec768eb641d206838 \
    --hash=sha256:e9871b1ffbfa9656b60aeee92ed5136a5742696006fa322b29ea3d8da0ecc9cf \
    --hash=sha256:e9aeb04d6aef139de265b29683e119b638208f88cf73cdd1658aa07221165321 \
    --hash=sha256:ebaea975e03d3141d9d3a507df75c9b3ec90fa9d2ffd07567b3a978d9d790b26 \
    --hash=sha256:f0606c8bf2cdefea14a43530f7657cbbb7ecf1c4222512492ef4a4434a9501ec \
    --hash=sha256:f13c32a3abd6079a66d9526e18dad9b6d280384d49d7c54040cd57b6424041d9 \
    --hash=sha256:f7401aebd7f581d7f83a439d87d474999317ee099218e5ad25d125290990ba65 \
    --hash=sha256:fa4ecea169a355be7a3ade2c783e2ed12f0e40d2c5621cda8b3297faf7fbb9f5 \
    --hash=sha256:fbd139c8447d25dd750ab79ee274cc5e1fe80fc56340ab10b18a195e1b6eca3e \
    --hash=sha256:fdafc9cce40277e0f7a0feabce0ee50dd2fa1800f3b38015e51296b5e814048d \
    --hash=sha256:fe3cca2e4e8a592be0f269a1ca4835c25199d9f3ce815c8491048f785b0a0198 \
    --hash=sha256:ffd0c5368496f41b0944be820fcb7a838aa6e623d250b01acf2643939c3f99d7
    # via
    #   -r backend/requirements.txt
    #   reportlab
pluggy==1.6.0 \
    --hash=sha256:7dcc130b76258d33b90f61b658791dede3486c3e6bfb003ee5c9bfb396dd22f3 \
    --hash=sha256:e920276dd6813095e9377c0bc5566d94c932c33b27a3e3945d8389c374dd4746
    # via pytest
psycopg==3.3.6 \
    --hash=sha256:a1db9f7148b06a28606767efaca51fa6f9398c5c0a3810519be69d7000bdb631 \
    --hash=sha256:c081f2250df751a943036e42db6df4571c66cd0aabe8291a7a506512b12007d2
    # via -r backend/requirements.txt
psycopg-binary==3.3.6 \
    --hash=sha256:05a83ac9fd52b9bca7cb5ab04b3691163170bd16f53defa27216ea3aa07ee781 \
    --hash=sha256:0a52991594ac4db888c7d39bccef331797e30cb31a95cae02cf2607f83a42dc2 \
    --hash=sha256:0bf08b749cc144f33b44a91b78e3f71c60eb07963746a0df5a100b36ce3d7475 \
    --hash=sha256:0ebfad5d131de9f892ae9e70cc7616207768b6714b66a52d4612b8ceaf78b372 \
    --hash=sha256:1679a1cb93fbe5a6d1fd58d82cbddcc6fcb8c61446ba7cae6eb2a7b19bc585de \
    --hash=sha256:198a48e68cc99ccac03ba95ac857e73aa66f3bf6be77019fafb0832a05f7ad03 \
    --hash=sha256:1fbd30e537dab22cafdf080608f10148fe2a5f3a61294ddb5113caac8a623840 \
    --hash=sha256:289aadd6a00e151203c081f708348ec89f1e483c9b510ef4ac3981f847f01f79 \
    --hash=sha256:2f122603f36050937982abf9668d8bc4769a79f7c93a65013b1c49f1cab7b56b \
    --hash=sha256:303732e798fe6729f8e12021b9c96107df8e95ecec4dd487c67b98ec2a59435e \
    --hash=sha256:31cd942c23f613276b81a6e6598cefa12960058b0f46e1e874b540c793f6aca5 \
    --hash=sha256:366db6e97e66b37211475f20c4c1324a2dc0dd825e46d4e87f9d599304d276f9 \
    --hash=sha256:373704aea331d3f3e3402c125a1543f5875e2986ebb54f97d1647942161f803f \
    --hash=sha256:37d40450659401600e6d043ff586c89a71a69f33cbb8bcdba6cdb2569beecdbe \
    --hash=sha256:37e517c146b185f9c0c6e8d0a0ebbdeeeb67896af28466e032bc810d0c7dc7a7 \
    --hash=sha256:3af90f92769d8cc10f94515ee7a0aef36ea85ca733a0ce22858f6e0953f41138 \
    --hash=sha256:3c9e663b2e800e3218994cf948c11bcc2844e6491b34aa80d089baf6531827bf \
    --hash=sha256:3f84dab25e0385692ee13274c68678377e0b1a70ab9d14e56264cbf61f60c62d \
    --hash=sha256:4690cf67738f0e0e49a32aeec99bf0e4595cc2b4f1af984a4345394b1dcff91a \
    --hash=sha256:566dd827f17728efdf7d88a5b066f815170f6fdad13967ae952842d90e6aaa9f \
    --hash=sha256:5927b7ba63153cd8e9862987290a2b783a5c590daf2a4ef981700cc3569166d4 \
    --hash=sha256:5ad8f35e67cc16d1fad1fa8c88972dc9b3a3141ea67897399904edab96a301b6 \
    --hash=sha256:5ea8beeb5541780b4b50b462eeacbc4f594ce3b911dc20c81c75f267876f71d2 \
    --hash=sha256:5f598f19fa9a91540b5cee17932ffd227b7b53a481605bcc4573c0eafa647300 \
    --hash=sha256:612382ac3ed13651c7fa44b5fee9fbf7baaa2ddbc6f500391672682c5f1df9e0 \
    --hash=sha256:6ff05561e4a067d35507dc5c90f1deb2ec1c9703ac5cccc1bc26e08a197f9c5a \
    --hash=sha256:7308c93cf0b19bbaf8e6ff0a6ad50d3c442385739245fe15a8d593bf841734a6 \
    --hash=sha256:79a2a1c3449f6c3409427078ed1cec10de79f3023cb5f2504f0597d350ad46c7 \
    --hash=sha256:7beb3e41c9a1e509f3ed85263386588cbe3e975aa67be21f79f44fd35ffaeefc \
    --hash=sha256:86147cb5d140341c3363fb5bacce31f8d5543902a46699d3c536b101bbceaf9e \
    --hash=sha256:889e42acec10450185e0cdfb396f375e2c1a8d7737c114830a7fde4654f59e30 \
    --hash=sha256:910ace140e3e7b7596898d083f37a8fe90c5c40684252ad4e682364b2cd3deba \
    --hash=sha256:955e3dd94da361e052d2e49acf591017158dc8f8ed2c8a42c2e3943403c39dc2 \
    --hash=sha256:9892188bb15e5803beb51afe8a25add6b56be391a53058e8bca03b74e1e6bf22 \
    --hash=sha256:98c02090d88f2ebc0ec1e8da538f77d225ce0fffecf372aa39262e62a1b054ef \
    --hash=sha256:9b2f11794e017ce340934e35de46181c46ef71ec75ea3d85dd75cd836761c01e \
    --hash=sha256:a2e44a342d2aee40508e28a563d8961c39d9bbd8cae36d8578f0a3c6658aab0f \
    --hash=sha256:a4ee3bdd5468a725f2a4d9aab8a74b6d0279f768c8b5d3aeb102c5307ff3d59c \
    --hash=sha256:a5165300324efd5a772c48a88ab3a928513ab3979fca76553e62ee815f7b2b9c \
    --hash=sha256:a9348c5b43a3bb5ef8c2e89d5237c9c87eeafb01d338c84a7aebbc5cd0313299 \
    --hash=sha256:aa73160077345ec21b3f51e8e24b3de2e99586217e497629326eb9b2ea88c52e \
    --hash=sha256:ad1c785e784cfd87e8436c6b7702f2d321fc39601bbaf29bc63a41a867091638 \
    --hash=sha256:b3f75dee0f9afafabe4edc52c4842f1e1878ed2069bd05b22d6fe961e97e4dba \
    --hash=sha256:b599defe9190b17e9907c8b4d114c181e702c87efcd1b8a0ad40971cdcc4634a \
    --hash=sha256:b82491019b884d62318b5f30706c3d7e6d4e5a6cb7eabcb3edc0c1b0fdaceae9 \
    --hash=sha256:b8ece331509f7a975b90501f41e83ad905e4141753fedf3f2711b2bc70a8efbc \
    --hash=sha256:b979a42815410432420275412633960807178b1ce26591a16ce06e78a5bd4bb2 \
    --hash=sha256:be4f9b3c9338ac5dd217c5847e21521b396c8117f78dc420d495a5c49bbef874 \
    --hash=sha256:bf8c8481d026b85dd70c5fa7dde85b2333aed0b32a2602bcd38a900cbd78a49c \
    --hash=sha256:c61617eaae0112ca154da87ffb99b73af2c74067acac28dfb9a4455b019dff2e \
    --hash=sha256:c6d19cb4999d03231e8730a5f66c8f5068bc3b532677eb39dab0f600bff3e312 \
    --hash=sha256:c7753871eb57e6a5f4646f6168590c6653073dea5e9e720b201c8875332df4c8 \
    --hash=sha256:c7f92daa0d2a1c76f07264abddf8cbabd30152a2f09c3270e50f0c7efdf5dcac \
    --hash=sha256:cbd5f73073ed19c378d4c35499db1e3e703a5b1a324e521204065967bfaa7a18 \
    --hash=sha256:cec5ea900390897d0b46130f60bc2883bf19c314f9044235217c8be88b0ef269 \
    --hash=sha256:d636338c8f21b0df2f84657b00bc34f9313f826ef93f1155bc743607e4a0c5eb \
    --hash=sha256:dc75da5a20951049f7b773145f998f69d181adad9c58a0ff36e0cf1d73c10e10 \
    --hash=sha256:e23a66a763fbe83fcc210bc77c27e5a5ea380ebf091c06f34d8561b695e5a40f \
    --hash=sha256:e8cbb54454dbf1bbf2ff08dd7693e8d94ac94b1a20f70f4b3b813d52ecb5cbc1 \
    --hash=sha256:ee2c4728c691245e24501fcd7a97b5b381236b9985bc445bba88cdce7d1b5784 \
    --hash=sha256:f0535693ce476a722b718b002d5d2c27d47e71ca945276ac194409c98e74c492 \
    --hash=sha256:f19cc87343eaa55255e76b31259a570072ac95d6ae82c92dd34b97691f5e49dc \
    --hash=sha256:f21d057f3e5f5491067e5b292498073b73847d48799b099803fef100775fcc52 \
    --hash=sha256:f87dbdc42e78ee0f7ea180c03f8c78e80a949e373066629bd90fefff10552dff \
    --hash=sha256:fa34eb47969297471db7b7f193622c7e3ee839ec05abd05f1fe104d5b1b1dcf4 \
    --hash=sha256:fdccb3a0e184b03e9baa673b15a809cf36c339c85dbda0ebc25a698846dfbee8
    # via psycopg
pydantic==2.13.5 \
    --hash=sha256:346a034f080da3755d8e9cb5e00e8b07de1d39e4f6e2c87d8ab7cafa0b269a73 \
    --hash=sha256:51a9c5f7b2f8e636f04c6cada605d9b6a3bf1348fdf945a3d8869b19bba0ee08
    # via fastapi
pydantic-core==2.46.5 \
    --hash=sha256:013d6f3483d81e02e7c328831808f336c8596ee33b4bd4026b9ffb1e960b8942 \
    --hash=sha256:03b9666e41e35d8909852ba191a0607520f81b74eaf12ccf8737005dbb313821 \
    --hash=sha256:045ab3b6d308439e32b81cc173bba5b9018bc6ed896afd0c65b3b009b1699af5 \
    --hash=sha256:0bddb4020d8f04175865ccd17eff3040874fc11fb593f424edb452653b4b947c \
    --hash=sha256:0cdbada856a1c69a7624a64d3d9aefe79300bd6ef827b43a4f265010b9b55184 \
    --hash=sha256:0fc5be0abd4a407e200d844b404e33639a554e7bd0d448e7b9ae181be4789ac2 \
    --hash=sha256:10416c15b8839ecc4ef4d0885da76da6fd0f67333a0eb8aff6d93c4b8f2910fc \
    --hash=sha256:15f4a94963c95accac15b7b657bb177d3ad82bb90b0d0526d9a9b85079925db5 \
    --hash=sha256:18a09e1e1011b462f2e32774f25859ef1223d5c2b0546a633cf56654710721e0 \
    --hash=sha256:193375f3548919d3f0b60936ca113ada3e38f264f91b9b8e0508efaad57be931 \
    --hash=sha256:1a353f84de772f423b5ffb11d7ae352fbbef0f446f3c0b0af0f8236d7233606e \
    --hash=sha256:1e449def1945a462c464331254e5a44fca7c3b4f9aedf59ec2f50f8066dd8e25 \
    --hash=sha256:1e5aad1220a1192c42341c8fd4a8686657e73ab2a920c970bdc4de334fe3193d \
    --hash=sha256:200aa3dc9f8d54f0754f43247c0bad0999fdcfbfd2488384dd44f37279271fe6 \
    --hash=sha256:2471fd51c61c610e1dcf7de44d7299283661654d11264ab4802b303368d69c47 \
    --hash=sha256:24922243639cbdac66c75fcb6fd6495a9cb52b213d62f9a0d16f0310b1ff8038 \
    --hash=sha256:28a6a556cd3b6066bea827857f9d9cce027c96f776e512f544a581f9e42161f8 \
    --hash=sha256:2bc9419666990c06d7397831f2126a1ecc3594aaa3ff7de5bf2d066802f4e07b \
    --hash=sha256:2cbd9a5eff05e51c447c34dfa4632145b26b09120cf04bd0c871e44c1a5e1c9a \
    --hash=sha256:2d330aaba8621b1edcec8ae2c4050f63b84ccf6d98723a8f212e9684713abf0e \
    --hash=sha256:2d5d76654becf5efd62c9e51c3756c67b49498b0c9a40884934c40807adbd074 \
    --hash=sha256:337639ba62a11acde6ef3aeb08c8ea755f8ef1fe5e513356c0f36a2b0d7568b0 \
    --hash=sha256:347ec774390c87326a2e4929d58d3f7e8763a104d5d35f4cd595a4c952366433 \
    --hash=sha256:356c8368cbc321050b169595683a2e1d63413b1e0e2868b330af9fc14c616d3f \
    --hash=sha256:37ae34309d7bd8c0d61ab839668058f2a7962ea1fc51d105d2db228fe0618034 \
    --hash=sha256:37ea7b83c935e5b0d68c9449b82651accf78a10828b2c02b2f2d9e9496446c21 \
    --hash=sha256:3a3e26b6a8274211bddee2d0e4d0d42778f17a34510f49d2ec44b58abfc41736 \
    --hash=sha256:3aa166e99c4f2985407fb8714aebede877ecb5455cf321b606adca926d30d5a0 \
    --hash=sha256:3d2652072b2d774947ba5cf78a9e59644ac62ee572daf6dd2e1dfe905e15b2b7 \
    --hash=sha256:40375c2d05acec10323e45dfe2077ac44bc74659008614af5069034e2cfc781c \
    --hash=sha256:413a717a410d0c817ef5b786a059415550b3794e1d0c2abffd9efb93a3d9f7b4 \
    --hash=sha256:46c25dda9d092a06c08db76ffe0a197107904d0dfac653f7d5306bbcd6d6119c \
    --hash=sha256:49776eab08766a08dfff7012f8b422dcd7e25e43b316eedf0477c24fcfa84b7c \
    --hash=sha256:4d44cf99ddebf875f9b68cc267aa684c99b7b44fe63ee1cac4ec163807290069 \
    --hash=sha256:4dedce55295becb61921e386b99d4f2706045306e7fa52249a33004c837379fb \
    --hash=sha256:4f8507560a9284e1370bb048ed4282012fbef4e8d109875b95e884d228552061 \
    --hash=sha256:4fdc8b93a41521988916eeaa271173fcca7fa0803d62f87675aac8dcec1c8e29 \
    --hash=sha256:5086029a57366b8cf81b130a43908738095c270c21a8d7f0e8bdfdb89718e2f3 \
    --hash=sha256:52e24eacdb536cade636aa90fb851835222becff8484b7001fdc78cb0290f2aa \
    --hash=sha256:53feb344243bb9510a9dec7bf3cf1b64d88a98af5dc7872a5160465f8b198c8e \
    --hash=sha256:545f26c504b27c3758439a5e6d9349931f0a04f855668d5fe323c89e82300a38 \
    --hash=sha256:54d510bac3ee52247af28ed4bb18a1e799f040ac60fd2bf5ccd4c92f1fbe786f \
    --hash=sha256:5cb482e9e84c851f4e623fe4acc1ced89168cf1fe18f7089db4548c8f5bbb65b \
    --hash=sha256:5e81740c09e310f5aa5cbd3e434a01c154d4bef93241c7877b39f211d2b78ba8 \
    --hash=sha256:5ee239d575f80b08eca11f6e20f90c4c695de7825c67eefe6091fbf20dda648e \
    --hash=sha256:5f194189415698233dd1114a093a9b56e61e2c57e11b469be3b0506f46f0771c \
    --hash=sha256:5f93c5fe914d75fbec9a49209b00da5f08e9e467d69da2b1510c81940cfd10be \
    --hash=sha256:657b40d6240c0a7b6a64b30f22d1e3aa631c7e846c621b0c0f6d1d75e2e15ea6 \
    --hash=sha256:6d30e1a4f138b8951063e9a394752a9179b51da288ffa507b1e659222f4c1793 \
    --hash=sha256:6f7b393a8b3da82f5c1fc0751e6d01ac6c55b93c18226a60bdfba4a724efafd1 \
    --hash=sha256:701b2e04b560eeb4bddf7a25ab8ca476176e34fdbd9a0e18196f0d12d4685f0b \
    --hash=sha256:771cf63ae0b1b50dd22e5f3e3549fab5f3f4ff1635d352a9e1a97fe01c7b2e64 \
    --hash=sha256:79bdfa52f843137045b2d081cc05c120ba6665d29b7559c2c47690906f39279f \
    --hash=sha256:7ac031912d54f3d83ef3b3eb98dfabc1608802e2202263d25957eeed40b94761 \
    --hash=sha256:7b0fc826b16c55e561e5d2a0c5c77b051ba1d92808118c4e4b5390f5e0cf191d \
    --hash=sha256:7c6be839a5a8312626b32029a415644a0846b420bc8b52b95b28cd92da162168 \
    --hash=sha256:816ff0a6550ffc06c098ccd2e0698600f9aa7da192a79eaa6f9af504a35db869 \
    --hash=sha256:82a36973cf8a2ef5406f4fe2edbf8ed0c99629535d959e0b100c76a32535a111 \
    --hash=sha256:837b396ca3d7b74091ca623f6cbd8351bd42d670a79c2683e79fb089f06a2de5 \
    --hash=sha256:850a08d167dde16db8702c274f320c7be9d7da6f6dff2b58b18f9e815bd94f5b \
    --hash=sha256:8816f3d218beb4b787de5c9759c259b8fa61f9dec42dc7811f320a33771778b7 \
    --hash=sha256:892a881d5f68c2b9ea304b7a6c2c60d9343df578a311b0f86b94bc8f1ffe8129 \
    --hash=sha256:895395f8918627b04efb1ad2a4cf605387143300ba03304cd1dfa6d03f5e095e \
    --hash=sha256:8b10e3e8fd7ddc2bd915848a2768e44c15b22936f1cc54c462ad1164deb02655 \
    --hash=sha256:8e24d8f05fa2d28513d94e877e9c75ad66175376209b3977f916e240e623193c \
    --hash=sha256:8feeac04b5794e513e710af2f9c87d49f31a6dc47967bb264a1fed61a8989bec \
    --hash=sha256:9432f3598db432cb51c5b37fdbf29a60fcccc79e30d37a05022776a6bc4ab689 \
    --hash=sha256:976e1128455aa595ea04c79ccfedff1aaeab96ee013fcc916bed120c4f0ad94f \
    --hash=sha256:978e7b97d4824b5be09c69fb70507cbde3b0323fc147332ca40a94d9a6a0ebbf \
    --hash=sha256:97bf8de4d541598c94a59344eeb988a94c08ff76b5723c41f6567ec18c7892ea \
    --hash=sha256:97cf3eb53a8cccacf9d46686a0926186c9bfb5574f2ed66d3639d5fe117cd3a9 \
    --hash=sha256:9b68938dd5b0c783d88ff8e2dcc69451b5eb936fe212d516b21b9d5567f6d464 \
    --hash=sha256:9c4b71f10dd532fb7a5cbc8f58707779e64f03a258c2bf8bfbaecfcd9970b519 \
    --hash=sha256:9f47b8a949e60f027f0aa0a6f6c7b7e9c55cbf4380d10b344e282fa4e7ab1e1b \
    --hash=sha256:a1dee1b804ff4d11c663636cf15d2ea47e9f79cd56c033fb1cbf08924842a48f \
    --hash=sha256:a2468d93d181667a7abd66e1b64bb9f76f361b0fef8faddf687456453576f5ee \
    --hash=sha256:a2a5e1d0ff29adddc9f6d6821a66302e4493f8ca898b715b6b1182c2c201ea0a \
    --hash=sha256:a39ac25a9a2fa4072efdb429833c4a4c8009a51ff9eea3eeae131713cd27991e \
    --hash=sha256:a445486499897b88a7d6c310c88ed64dd37b1b59bfd7ae9107490bbb362f47d6 \
    --hash=sha256:a91c17edf6eea2402cb5457b4c89e99bc5ed1004aa34c4adf1d4258c1a5c22c2 \
    --hash=sha256:ab4b66edffb32d9e951efb3814bd104b8367a7501b81b955cacb5726d897389f \
    --hash=sha256:aca6c767f552b21b10f774aeac128e828eafb796adfa1b666a18bf6321453c3a \
    --hash=sha256:acf8a67ba51f4ca9ddbd0e6b3000a65ac51ab734661778b3e7ba64d99a710f2f \
    --hash=sha256:b10ec717381bdbfafef34607824db4c91de69ff085e4fca3b2af91b4fa17e68a \
    --hash=sha256:b49924c73a235e969511bf2aabdff3beebf9820931f646c80274d5d780010c47 \
    --hash=sha256:b6acfb46a814762367fb7ba0828b0a17d441b92ce249a0e007474c9072662dda \
    --hash=sha256:b7ca9034437b6022f941f4857459562ee00a560b97e7cce8a0ec5a74fc6766e0 \
    --hash=sha256:b98134087d9de723658d17a42c7d0da8d6e2ef08015dee7dc93889047315f5e4 \
    --hash=sha256:b9fe6fb92520e3fd61f2e49000b6911b188824f089b75973ea06d6267f0b476d \
    --hash=sha256:bce57638e08ac148e5778cce7feb968307a727d66f8e2274a543d0cf0c9ad6a3 \
    --hash=sha256:c14ad3bdc85ee7f318742c457ca3968a92126d144b15721c759033bfb06296c2 \
    --hash=sha256:c1c43ad4339643d70ebb8124e1305a7dab423001eff58bb41a0f731adbc98355 \
    --hash=sha256:c3471e5c4a949c26ec00a77f01df59096aa9495877de76fd60a980f8ee6be461 \
    --hash=sha256:c583b927a8838dab890706a6fa7573fbb8b70e24000ef9f7238e2d6f6435a5ed \
    --hash=sha256:c76fe65e607be28c7fd4d56fc3c42b1583aa058ce3408b7ad0fd540171d31f9f \
    --hash=sha256:c7ea57fc63aa7da93a1bd2d644e6577befae10c52c4e36377635eea1056a74f5 \
    --hash=sha256:cd5214352ae68f3b5e9af7768bdc5253695ee069675db3480518420b3be881f2 \
    --hash=sha256:cdbb78909f52b981d3b2d56b97328d71eb0b974c36bd77c920123a7ebb192829 \
    --hash=sha256:cdc8b74ecc48c0cb1e9607a05ec4e9e88db60a19ffcc9a1d5f9088ede40c8dc0 \
    --hash=sha256:d0a24b40877af2de4950252be9d21eaf7fb07660f3c2cae1f56c6b599ada5266 \
    --hash=sha256:d22a945598fb91236b4dd793a6e42e4f3dd7740bb5aace5ebd7d4c08d13bb575 \
    --hash=sha256:d2f9fc07a8042a8f95925b35c4f04f469707c981fc33245b6ca187cf5d2dd290 \
    --hash=sha256:d625a186a65201c23a9e3b8ed9c47e90a026e03256608cc91851c6709096844f \
    --hash=sha256:d925f3d9afd05a8c0fb3a1031463a8d59ebe5e2afad297e29c78be19e13b4e62 \
    --hash=sha256:e64e88d5585bea9ce95861079de72006c7fa6d3df4e3a3b65ba31eb979c15c9f \
    --hash=sha256:e652ab17569c94bff5475520f907b7148b8c24036a8ebbe5cf7cf7493d28579a \
    --hash=sha256:e7b891faeedeafba41b2983e5001a81b6a915b69544c7e7570d1989ce1c36ac7 \
    --hash=sha256:e80675d75ae2cd14372cb65cad5400d9347a3d3f6c13000183f22dfd027283ed \
    --hash=sha256:e9c134bb666dd54b778b9fc0d2b50cbb7f979b9e3716f26a88c9ab3b6fc1dd0f \
    --hash=sha256:eb7d8d0e5886a89a55d2eef490e272fa965a9d57c6b29a5b5088a7997ec2cad1 \
    --hash=sha256:ecb42011e12ee19cafbc312887cbf3546959fe02fbad44f272d4be5baa997615 \
    --hash=sha256:ef3fbbf161dc9351a2fe0422e51b129f9e97e42385bd0320b309c15f7d287dd8 \
    --hash=sha256:efd62a42486f1bda5d24cb4f63d15a3c7768375fe83d36f9417b4ad7a2fb20b3 \
    --hash=sha256:f077d0b97ab11fa7dcc633fca53515f290bca8a8a633e966d5b6d1879d9ed01a \
    --hash=sha256:f332f0e72a5a0400141f830744e141bf9f97917878dbe968669e8a7fefea78ff \
    --hash=sha256:f7b0ec93a2893de856652154d73b7ba622f26fa97726487dcac373de5f4c6084 \
    --hash=sha256:fa10ef4112775900e7a0661068635eb67b2ab824fbde764de6e0e21982a93db0 \
    --hash=sha256:fc5d783bd4a2387e97b8a2d5ec781cfb92b3d893bf82370548e99db5915935d3 \
    --hash=sha256:fc8515076c11f3cfdf4fb142dcca0fe384b1230a3b5415458ac84f3e0903ec13 \
    --hash=sha256:ff218293c9c806138dca139765e3b067621be52bcd93cdc14c7711be7ddc90a9
    # via pydantic
pygments==2.21.0 \
    --hash=sha256:2363c69b61c4a97c838da3b130dcd6468f4848992b21a82f2a63ec34377137d9 \
    --hash=sha256:610ca751c9bc2492b38eb9a38a7fbc93edbbb2d7182edaf34e66ae493dee5c8c
    # via pytest
pypdf==6.19.0 \
    --hash=sha256:7e5d6e730e7dae87d560a2cee218b852f6498c8be61966f3cd02ead971e48d14 \
    --hash=sha256:bbc43aca292369ccc6cbc8a921991ecf2538a3587ab5a116eff06c321d647155
    # via -r backend/requirements.txt
pytest==9.1.1 \
    --hash=sha256:1088fbde8f2b49d95a549a195707afa7a76a3ce9bcadc26b6d71f0ffda5fe313 \
    --hash=sha256:37a86b45efb9a47a61a36449063e8e18d0cab3161329fc099eb21783169c4f0c
    # via -r backend/requirements.txt
python-dateutil==2.9.0.post0 \
    --hash=sha256:37dd54208da7e1cd875388217d5e00ebd4179249f90fb72437e91a35459a0ad3 \
    --hash=sha256:a8b2bc7bffae282281c8140a97d3aa9c14da0b136dfe83f850eea9a5f7470427
    # via botocore
python-multipart==0.0.32 \
    --hash=sha256:be54b7f3fa167bb83e4fcd936b887b708f4e57fe75911c02aebf53efaf8d938e \
    --hash=sha256:ff6d3f776f16878c894e52e107296ffc890e913c611b1a4ec6c44e2821fe2e23
    # via -r backend/requirements.txt
reportlab==5.0.1 \
    --hash=sha256:1c36e6bb0e71780c72331eba60da7f602e8d4389a8723825af71342e49d791e8 \
    --hash=sha256:ebd13154be1c8515e665de70bd2d303ae9ddc3ef47e44afd5116441ca0283a26
    # via -r backend/requirements.txt
s3transfer==0.19.2 \
    --hash=sha256:ba0309fd86be3c27dbf78cdd813c13c5e1df16e5874b99d2535ebbdfb9892993 \
    --hash=sha256:d8168eccca828cbb2cd573675333f3bddd254313a9c42494b84c76b539e8ba25
    # via boto3
six==1.17.0 \
    --hash=sha256:4721f391ed90541fddacab5acf947aa0d3dc7d27b2e1e8eda2be8970586c3274 \
    --hash=sha256:ff70335d468e7eb6ec65b95b99d3a2836546063f63acc5171de367e834932a81
    # via python-dateutil
sqlalchemy==2.0.54 \
    --hash=sha256:03cbf8d9a67da618bd65500a5eb3ddac89caf4c61e99b2f03fa4a1952a0725a9 \
    --hash=sha256:0e7a76d5dce712ce50435d0f97181eb955ec27d138c004176f01282e063bac52 \
    --hash=sha256:1019abef05a4b5eafc8eae6fb483167fa28a4dbe5f518d577b744f31a5276a37 \
    --hash=sha256:18a8b6417cbb7b735cf91c2b59453c2a554cefa0a8d7bd15aa35740739410d77 \
    --hash=sha256:1d887fbd5d248e250807bd801e697fc73e3b44866ce5f093dbc90512e75bde25 \
    --hash=sha256:24ae093dec196ba37fc2beb0316de53e7871d3d246a50faecbbb53034e41ded2 \
    --hash=sha256:264460333ed0b177cbb1956355d0ee4e0cab83fb415c934ce12a25db2e7be39c \
    --hash=sha256:279bde5bfedb0f3e0f1bdbcffa2daa39c6c54d90f9408ef3b1802001597199f0 \
    --hash=sha256:2f61a70b3b82e2ec7ad6a4f2301422b9ca93ff06917983e41317bcae878bddf6 \
    --hash=sha256:31d5458672a6f72db2c087f4a5098b3c8503ea0254186ff29205d63afa9401a4 \
    --hash=sha256:32de6deded25e8b9b11d07428d496ff24dfbc882b8e990c177266948cb5f3d9e \
    --hash=sha256:330d35f9ce815d35cb1daab038d4d7ec0e907f4d7ed0fc8bcb2411d1f23d0b50 \
    --hash=sha256:34e10af7d274a5c4b7cd0fced5e7361008c5e07d97dd48a93852d5b2f1142a1c \
    --hash=sha256:3de32cc6721eb42c3aad35bcfb244bb7a18f66c00f3582aae6281d6287a339b5 \
    --hash=sha256:415239eb2ddbbc508ba4cac97affb91c0f210548fd1731edda6e529b0bb93015 \
    --hash=sha256:48611087a75d26d798003645c688c7d3cfc26b89dbe4a2c568d6b378d330deae \
    --hash=sha256:4e55a0b96a1577a1e108c91ccdeeb9cd92768f28ce206597311c3bf6d6423abd \
    --hash=sha256:4e8a4afcc7d714cc3c8a57facdff4c3529f5f93d71e54b7da1e03e022c9089c9 \
    --hash=sha256:5417322b3c025dd82918725d3bf09ec105fac95efc195722b8b06e1d9c381139 \
    --hash=sha256:5800ddea045c2c860ef1d359a07a3066c7c0c426f45e3abc3874e116cb3c6937 \
    --hash=sha256:63cae7210fea9899e0bf35c1f1ae55d3ddd9c6d47cae8b6b43d945afa79dd65b \
    --hash=sha256:68d994e9b0d0423a02a20039631fa6fcbb7fa829a992f7605025774940305d19 \
    --hash=sha256:69cab115c40fd02c5a22c68e4ee630fa6ef9a1650f1de944419aab1f7096fc4f \
    --hash=sha256:6b6d4e601c4f6d85e99bb3416107cc9418c5603ca73d4ee0f5f8d79c2a1ed9e8 \
    --hash=sha256:6f84099e4b04a5c2d44500a2a8302eee5af4bc6fee63e8c6e9cf6786e747280e \
    --hash=sha256:7108f410f596c5ac22fe43ba467e864d27c4e1477ae89e90c6c87120b2c1be23 \
    --hash=sha256:744fb219a390561a57dbbd59cd69a22b5b5b2facfde794c1f79236dd847fa67a \
    --hash=sha256:762cfe4d340c56368256d936a98b620a9a5650e49c1c84eba51d6edd17ffefb2 \
    --hash=sha256:7b973e4facc2f80e42f5a27b841feb7e202661881a6320580abbe597a28a007f \
    --hash=sha256:7d03084f3352dd92048cb19c71d90f116d076c9c7937e0ebc7752c4685de6d38 \
    --hash=sha256:7e33a631ab1474f8fe6b910bd1a07b7b8009c4c78cdd3fb18001b03e3bc2e1d2 \
    --hash=sha256:842540e4382472f23c79589995752648d14696a8200d0807ed8c5c59c92ade44 \
    --hash=sha256:87ba8834318b0d8dc94fc6f405d071b5c08be32a6c3fd68107fd6952ee949615 \
    --hash=sha256:92622fbbda1b1fe1632f3402a6e516a93c0e41d9158839c6b3dfb12117f26b72 \
    --hash=sha256:a0956dc754d3884da7fe60097110ec7a8a105d26afa2f0844468f4b1598c6912 \
    --hash=sha256:abd6b21bc58e91c1932eb5d6d7f1bd44a551dfec7b6a7f517c3638ccd67233a0 \
    --hash=sha256:b374e3bc91e246a942592a98ba6a23be76fff21358b00546ac8c0ebc0fd0e00b \
    --hash=sha256:b67749f7da3985a529cefbb1474783cb91ef44371cb9713630bade3de908760d \
    --hash=sha256:b67c1744e453af833667fc1b84de07adb4a64f3536ef52a8ec5ac2b941d43970 \
    --hash=sha256:b6c419c83a87fd901f0b1b5338ffcb82471c3ac32a86bb8883688c18f8eb85d3 \
    --hash=sha256:b9086b8ad48280ef6a7ba68262d5e44f7db1c4cb1973e8cdae8a9f467ae66f51 \
    --hash=sha256:baa8521e8ee9f24e75dfc7aaabc08020e551ef0d48d7c3e3536f5cddf277586b \
    --hash=sha256:c1a3455a88f66e4851792bedb098ed942912253d31caed1dbc58afbfa9e875cd \
    --hash=sha256:ca05f4e7852cf48083b0cf157e4f9504b7068780422a50fa82f45353b8c5e14a \
    --hash=sha256:cad78d04254967bdbcccbed5e631d88fe4868530946ab0929aa45e9032849518 \
    --hash=sha256:cf89e92bf0d4204a6afcc17af27b9271ed9c7e34e17d6f80c085d431ea4a1747 \
    --hash=sha256:d31a2bc06a854ee52dd86b455be4df7c750b28817e2d1b884e31fff126c4fd7b \
    --hash=sha256:d566099d60cded87d175d4171dc899b9613d2e3b663573364565ca1b27ccd241 \
    --hash=sha256:d65f8ca742ef1e1e14bc417ef59dc2ddf207a7b66b30cfdc6152447314e030cf \
    --hash=sha256:d6adf80277372a89910a0f3ccfe960b846d279dc55b366dd5c5ec07f41c84758 \
    --hash=sha256:deeab253fe01a770f634c7007c73702df2324c868a79ae756507a9a1a76294fe \
    --hash=sha256:e08397c6c42f53b2488acde9108b8bfefd52d7afd1bf2f03d2ffcab7a204aceb \
    --hash=sha256:e1f455db400289f77ba2f7b62fffafe8875153812d0e3777aa4ff2b34a0fc1f7 \
    --hash=sha256:f3ea33bcf0aa599c1511fe5c9fb126f45aa450419084c4823f786155fe4c79f1 \
    --hash=sha256:f4e8f955d13af83fb4e35c3472e5377ee22d3445eada1e5e48199588edb69835 \
    --hash=sha256:f5c09090b1a7c4d389d1431f820931e8df318f82caafc53f9a72c872fef467c5 \
    --hash=sha256:f8cc6532f930c27974e9239e5ce5abebe7600ba9807cea4fcf42f1b6cab18fe7 \
    --hash=sha256:ffba7eb2d67c7505e82a0902aa854d8824b74c28a183820d6a8bd3cfd0f812c2
    # via
    #   -r backend/requirements.txt
    #   alembic
starlette==1.6.0 \
    --hash=sha256:a86dd39d14bb45f85a3d18525215a9ef0cfd1f192ac793220e72598c90335f0c \
    --hash=sha256:d4e3ac5e546444960c710297a3c9fc3f7ebae1b7e963f3d36173b49da535be9b
    # via fastapi
typing-extensions==4.16.0 \
    --hash=sha256:481caa481374e813c1b176ada14e97f1f67a4539ce9cfeb3f350d78d6370c2e8 \
    --hash=sha256:dc983d19a509c94dba722ee6abd33940f7c05a89e243c47e907eb4db6f1a43e5
    # via
    #   alembic
    #   anyio
    #   fastapi
    #   psycopg
    #   pydantic
    #   pydantic-core
    #   sqlalchemy
    #   starlette
    #   typing-inspection
typing-inspection==0.4.4 \
    --hash=sha256:547274fa6b0a561ccf549cc9524b999a578e737d015d8709d021f9d0d13bea47 \
    --hash=sha256:65b8397ba37ccbce054456aaccddfc91e6e3083c92824df348d96ca832f3f147
    # via
    #   fastapi
    #   pydantic
urllib3==2.8.0 \
    --hash=sha256:0cf3cae568d36aa9576b28dfb35f11328f1cb974ca7647d9475ebb86c75ac6e3 \
    --hash=sha256:63bf2ead4c879426ebf22ef2a781eeb4aa3b4ae798a0435506f8687fd5bb9b63
    # via botocore
uvicorn==0.53.0 \
    --hash=sha256:a9356f0cb89b3b8621529c5d5eebd69bfe154f4c3f68b4cf2de47e45fa855c2e \
    --hash=sha256:e8dca71ec86dce5f04e333f0d56cdedf942446e6643b9cea1af0d6d3a02cb03e
    # via -r backend/requirements.txt

```
### `infra/terraform/ecs_runtime.tf`

size=15832; sha256=6f0c3e1296ff67269841d421fbf94f404036676a3ef36654f73240d794633891

```text
data "aws_iam_policy_document" "ecs_task_assume_role" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["ecs-tasks.amazonaws.com"]
    }
  }
}

locals {
  execution_role_names = toset(["api", "frontend", "worker", "bootstrap"])
  app_environment_base = [
    { name = "PAPRNAV_ENV", value = "pilot" },
    { name = "PAPRNAV_STORAGE_BACKEND", value = "s3" },
    { name = "PAPRNAV_S3_UPLOAD_BUCKET", value = aws_s3_bucket.app_artifacts.bucket },
    { name = "PAPRNAV_S3_UPLOAD_PREFIX", value = "uploads" },
    { name = "PAPRNAV_CORS_ORIGINS", value = "https://${var.pilot_hostname}" },
    { name = "PAPRNAV_SESSION_COOKIE_SECURE", value = "true" },
    { name = "PAPRNAV_AD_V4_ROUTES_ENABLED", value = "false" },
    { name = "PAPRNAV_AD_V4_VALIDATOR2_WRITES_ENABLED", value = "false" },
    { name = "PAPRNAV_AD_V4_SLICE3A_ROUTES_ENABLED", value = "false" },
    { name = "PAPRNAV_AD_V4_SLICE3B_ROUTES_ENABLED", value = "false" },
    { name = "PAPRNAV_AD_V4_SLICE4_READS_ENABLED", value = "false" },
    { name = "PAPRNAV_AD_V4_SLICE4_DRAFTS_ENABLED", value = "false" },
    { name = "PAPRNAV_AD_V4_SLICE4_DECISIONS_ENABLED", value = "false" },
    { name = "AWS_REGION", value = var.aws_region },
  ]
  api_environment = concat(local.app_environment_base, [
    { name = "PAPRNAV_OCR_PROVIDER", value = "deterministic" },
  ])
  worker_environment = concat(local.app_environment_base, [
    { name = "PAPRNAV_OCR_PROVIDER", value = "textract" },
  ])
  api_secrets = [
    { name = "DATABASE_URL", valueFrom = "${aws_secretsmanager_secret.database_url.arn}:DATABASE_URL::" },
    { name = "PAPRNAV_INVITE_SIGNING_SECRET", valueFrom = aws_secretsmanager_secret.invitation_signing.arn },
  ]
  worker_secrets = [
    { name = "DATABASE_URL", valueFrom = "${aws_secretsmanager_secret.database_url.arn}:DATABASE_URL::" },
  ]
  bootstrap_common_environment = [
    { name = "PAPRNAV_ENV", value = "pilot" },
    { name = "PAPRNAV_ADMIN_SECRET_ARN", value = aws_db_instance.postgres.master_user_secret[0].secret_arn },
    { name = "PAPRNAV_DATABASE_NAME", value = aws_db_instance.postgres.db_name },
    { name = "AWS_REGION", value = var.aws_region },
  ]
}

resource "aws_iam_role" "ecs_execution" {
  for_each           = local.execution_role_names
  name               = "${local.name_prefix}-${each.key}-execution-role"
  assume_role_policy = data.aws_iam_policy_document.ecs_task_assume_role.json
}

resource "aws_iam_role_policy_attachment" "ecs_execution_managed" {
  for_each   = local.execution_role_names
  role       = aws_iam_role.ecs_execution[each.key].name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

data "aws_iam_policy_document" "api_execution_secrets" {
  statement {
    actions   = ["secretsmanager:GetSecretValue", "secretsmanager:DescribeSecret"]
    resources = [aws_secretsmanager_secret.database_url.arn, aws_secretsmanager_secret.invitation_signing.arn]
  }
}

resource "aws_iam_role_policy" "api_execution_secrets" {
  name   = "${local.name_prefix}-api-execution-secrets"
  role   = aws_iam_role.ecs_execution["api"].id
  policy = data.aws_iam_policy_document.api_execution_secrets.json
}

data "aws_iam_policy_document" "worker_execution_secrets" {
  statement {
    actions   = ["secretsmanager:GetSecretValue", "secretsmanager:DescribeSecret"]
    resources = [aws_secretsmanager_secret.database_url.arn]
  }
}

resource "aws_iam_role_policy" "worker_execution_secrets" {
  name   = "${local.name_prefix}-worker-execution-secrets"
  role   = aws_iam_role.ecs_execution["worker"].id
  policy = data.aws_iam_policy_document.worker_execution_secrets.json
}

resource "aws_iam_role" "api_task" {
  name               = "${local.name_prefix}-api-task-role"
  assume_role_policy = data.aws_iam_policy_document.ecs_task_assume_role.json
}

resource "aws_iam_role" "frontend_task" {
  name               = "${local.name_prefix}-frontend-task-role"
  assume_role_policy = data.aws_iam_policy_document.ecs_task_assume_role.json
}

resource "aws_iam_role" "worker_task" {
  name               = "${local.name_prefix}-worker-task-role"
  assume_role_policy = data.aws_iam_policy_document.ecs_task_assume_role.json
}

resource "aws_iam_role" "migration_reference_task" {
  name               = "${local.name_prefix}-migration-reference-task-role"
  assume_role_policy = data.aws_iam_policy_document.ecs_task_assume_role.json
}

resource "aws_iam_role" "runtime_role_task" {
  name               = "${local.name_prefix}-runtime-role-task-role"
  assume_role_policy = data.aws_iam_policy_document.ecs_task_assume_role.json
}

resource "aws_iam_role" "first_admin_task" {
  name               = "${local.name_prefix}-first-admin-task-role"
  assume_role_policy = data.aws_iam_policy_document.ecs_task_assume_role.json
}

data "aws_iam_policy_document" "api_task" {
  statement {
    actions   = ["s3:GetObject", "s3:PutObject", "s3:DeleteObject", "s3:GetObjectTagging", "s3:PutObjectTagging"]
    resources = ["${aws_s3_bucket.app_artifacts.arn}/*"]
  }
  statement {
    actions   = ["s3:ListBucket"]
    resources = [aws_s3_bucket.app_artifacts.arn]
  }
}

resource "aws_iam_role_policy" "api_task" {
  name   = "${local.name_prefix}-api-task"
  role   = aws_iam_role.api_task.id
  policy = data.aws_iam_policy_document.api_task.json
}

data "aws_iam_policy_document" "worker_task" {
  statement {
    actions   = ["s3:GetObject", "s3:PutObject", "s3:DeleteObject", "s3:GetObjectTagging", "s3:PutObjectTagging"]
    resources = ["${aws_s3_bucket.app_artifacts.arn}/*"]
  }
  statement {
    actions   = ["s3:ListBucket"]
    resources = [aws_s3_bucket.app_artifacts.arn]
  }
  statement {
    actions   = ["textract:DetectDocumentText", "textract:StartDocumentTextDetection", "textract:GetDocumentTextDetection"]
    resources = ["*"]
  }
}

resource "aws_iam_role_policy" "worker_task" {
  name   = "${local.name_prefix}-worker-task"
  role   = aws_iam_role.worker_task.id
  policy = data.aws_iam_policy_document.worker_task.json
}

data "aws_iam_policy_document" "migration_reference_secrets" {
  statement {
    actions   = ["secretsmanager:GetSecretValue", "secretsmanager:DescribeSecret"]
    resources = [aws_db_instance.postgres.master_user_secret[0].secret_arn]
  }
}

resource "aws_iam_role_policy" "migration_reference_secrets" {
  name   = "${local.name_prefix}-migration-reference-secrets"
  role   = aws_iam_role.migration_reference_task.id
  policy = data.aws_iam_policy_document.migration_reference_secrets.json
}

data "aws_iam_policy_document" "runtime_role_secrets" {
  statement {
    actions   = ["secretsmanager:GetSecretValue", "secretsmanager:DescribeSecret"]
    resources = [aws_db_instance.postgres.master_user_secret[0].secret_arn]
  }
  statement {
    actions   = ["secretsmanager:PutSecretValue", "secretsmanager:DescribeSecret"]
    resources = [aws_secretsmanager_secret.database_url.arn]
  }
}

resource "aws_iam_role_policy" "runtime_role_secrets" {
  name   = "${local.name_prefix}-runtime-role-secrets"
  role   = aws_iam_role.runtime_role_task.id
  policy = data.aws_iam_policy_document.runtime_role_secrets.json
}

data "aws_iam_policy_document" "first_admin_secrets" {
  statement {
    actions = ["secretsmanager:GetSecretValue", "secretsmanager:DescribeSecret"]
    resources = [
      aws_db_instance.postgres.master_user_secret[0].secret_arn,
      aws_secretsmanager_secret.first_admin_password.arn,
    ]
  }
}

resource "aws_iam_role_policy" "first_admin_secrets" {
  name   = "${local.name_prefix}-first-admin-secrets"
  role   = aws_iam_role.first_admin_task.id
  policy = data.aws_iam_policy_document.first_admin_secrets.json
}

resource "aws_ecs_task_definition" "api" {
  family                   = "${local.name_prefix}-api"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = var.ecs_task_cpu
  memory                   = var.ecs_task_memory
  execution_role_arn       = aws_iam_role.ecs_execution["api"].arn
  task_role_arn            = aws_iam_role.api_task.arn

  container_definitions = jsonencode([{
    name         = "api"
    image        = var.api_image
    essential    = true
    portMappings = [{ containerPort = var.api_container_port, hostPort = var.api_container_port, protocol = "tcp" }]
    environment  = local.api_environment
    secrets      = local.api_secrets
    logConfiguration = {
      logDriver = "awslogs"
      options = {
        awslogs-group = aws_cloudwatch_log_group.api.name, awslogs-region = var.aws_region, awslogs-stream-prefix = "api"
      }
    }
  }])
}

resource "aws_ecs_task_definition" "frontend" {
  family                   = "${local.name_prefix}-frontend"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = var.ecs_task_cpu
  memory                   = var.ecs_task_memory
  execution_role_arn       = aws_iam_role.ecs_execution["frontend"].arn
  task_role_arn            = aws_iam_role.frontend_task.arn

  container_definitions = jsonencode([{
    name         = "frontend"
    image        = var.frontend_image
    essential    = true
    portMappings = [{ containerPort = var.frontend_container_port, hostPort = var.frontend_container_port, protocol = "tcp" }]
    environment  = [{ name = "PAPRNAV_ENV", value = "pilot" }]
    secrets      = []
    logConfiguration = {
      logDriver = "awslogs"
      options = {
        awslogs-group = aws_cloudwatch_log_group.frontend.name, awslogs-region = var.aws_region, awslogs-stream-prefix = "frontend"
      }
    }
  }])
}

resource "aws_ecs_task_definition" "worker" {
  family                   = "${local.name_prefix}-worker"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = var.ecs_task_cpu
  memory                   = var.ecs_task_memory
  execution_role_arn       = aws_iam_role.ecs_execution["worker"].arn
  task_role_arn            = aws_iam_role.worker_task.arn

  container_definitions = jsonencode([{
    name        = "worker", image = var.api_image, essential = true, command = ["python", "-m", "app.workers.ocr"]
    environment = local.worker_environment
    secrets     = local.worker_secrets
    logConfiguration = {
      logDriver = "awslogs"
      options = {
        awslogs-group = aws_cloudwatch_log_group.worker.name, awslogs-region = var.aws_region, awslogs-stream-prefix = "worker"
      }
    }
  }])
}

locals {
  bootstrap_tasks = {
    migration = {
      command     = ["migration"]
      role        = aws_iam_role.migration_reference_task.arn
      environment = local.bootstrap_common_environment
    }
    reference = {
      command     = ["reference"]
      role        = aws_iam_role.migration_reference_task.arn
      environment = local.bootstrap_common_environment
    }
    runtime-role = {
      command = ["runtime-role"]
      role    = aws_iam_role.runtime_role_task.arn
      environment = concat(local.bootstrap_common_environment, [
        { name = "PAPRNAV_APP_DATABASE_SECRET_ARN", value = aws_secretsmanager_secret.database_url.arn },
      ])
    }
    first-admin = {
      command = ["first-admin"]
      role    = aws_iam_role.first_admin_task.arn
      environment = concat(local.bootstrap_common_environment, [
        { name = "PAPRNAV_FIRST_ADMIN_SECRET_ARN", value = aws_secretsmanager_secret.first_admin_password.arn },
        { name = "PAPRNAV_FIRST_ADMIN_EMAIL", value = var.first_admin_email },
        { name = "PAPRNAV_FIRST_ADMIN_NAME", value = var.first_admin_name },
        { name = "PAPRNAV_FIRST_ADMIN_ORGANIZATION", value = var.first_admin_organization },
      ])
    }
  }
}

resource "aws_ecs_task_definition" "bootstrap" {
  for_each                 = local.bootstrap_tasks
  family                   = "${local.name_prefix}-bootstrap-${each.key}"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = var.ecs_task_cpu
  memory                   = var.ecs_task_memory
  execution_role_arn       = aws_iam_role.ecs_execution["bootstrap"].arn
  task_role_arn            = each.value.role

  container_definitions = jsonencode([{
    name                   = "bootstrap"
    image                  = var.bootstrap_image
    essential              = true
    command                = each.value.command
    environment            = each.value.environment
    secrets                = []
    readonlyRootFilesystem = true
    linuxParameters        = { initProcessEnabled = true }
    logConfiguration = {
      logDriver = "awslogs"
      options = {
        awslogs-group = aws_cloudwatch_log_group.bootstrap.name, awslogs-region = var.aws_region, awslogs-stream-prefix = each.key
      }
    }
  }])
}

resource "aws_ecs_service" "api" {
  name            = "${local.name_prefix}-api"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.api.arn
  desired_count   = 0
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = aws_subnet.public[*].id
    security_groups  = [aws_security_group.api.id]
    assign_public_ip = true
  }
  load_balancer {
    target_group_arn = aws_lb_target_group.api.arn
    container_name   = "api"
    container_port   = var.api_container_port
  }
  depends_on = [aws_lb_listener.https]
}

resource "aws_ecs_service" "frontend" {
  name            = "${local.name_prefix}-frontend"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.frontend.arn
  desired_count   = 0
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = aws_subnet.public[*].id
    security_groups  = [aws_security_group.frontend.id]
    assign_public_ip = true
  }
  load_balancer {
    target_group_arn = aws_lb_target_group.frontend.arn
    container_name   = "frontend"
    container_port   = var.frontend_container_port
  }
  depends_on = [aws_lb_listener.https]
}

data "aws_iam_policy_document" "scheduler_assume_role" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["scheduler.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "worker_scheduler" {
  name               = "${local.name_prefix}-worker-scheduler-role"
  assume_role_policy = data.aws_iam_policy_document.scheduler_assume_role.json
}

data "aws_iam_policy_document" "worker_scheduler" {
  statement {
    actions   = ["ecs:RunTask"]
    resources = [aws_ecs_task_definition.worker.arn]
    condition {
      test     = "ArnEquals"
      variable = "ecs:cluster"
      values   = [aws_ecs_cluster.main.arn]
    }
  }
  statement {
    actions   = ["iam:PassRole"]
    resources = [aws_iam_role.ecs_execution["worker"].arn, aws_iam_role.worker_task.arn]
    condition {
      test     = "StringEquals"
      variable = "iam:PassedToService"
      values   = ["ecs-tasks.amazonaws.com"]
    }
  }
}

resource "aws_iam_role_policy" "worker_scheduler" {
  name   = "${local.name_prefix}-worker-scheduler"
  role   = aws_iam_role.worker_scheduler.id
  policy = data.aws_iam_policy_document.worker_scheduler.json
}

resource "aws_scheduler_schedule" "worker" {
  name                = "${local.name_prefix}-worker"
  group_name          = "default"
  state               = "DISABLED"
  schedule_expression = "rate(15 minutes)"
  flexible_time_window { mode = "OFF" }

  target {
    arn      = aws_ecs_cluster.main.arn
    role_arn = aws_iam_role.worker_scheduler.arn
    ecs_parameters {
      launch_type         = "FARGATE"
      task_definition_arn = aws_ecs_task_definition.worker.arn
      network_configuration {
        subnets          = aws_subnet.public[*].id
        security_groups  = [aws_security_group.worker.id]
        assign_public_ip = true
      }
    }
  }
}

```

## Changed-file manifest

```json
{
  "taskId": "T082-AWS-INVITE-PILOT-D-PRIVACY-AMENDMENT",
  "stage": "closure",
  "generatedAt": "2026-09-19T22:11:56+00:00",
  "baseRef": "HEAD",
  "head": "19fe8e2e170687ed65deed78cb1af99d60f601e9",
  "scopePaths": [
    "backend/pilot_server.py",
    "backend/Dockerfile",
    "backend/app/main.py",
    "backend/app/core/http_protocol.py",
    "backend/app/core/request_context.py",
    "backend/tests/test_pilot_privacy.py",
    "backend/tests/test_pilot_package_d.py"
  ],
  "scopeFingerprint": "eb7f8d120061d36f7502149756ad57dc56d3bbf6bda17ffc6e8e182bb4260346",
  "files": [
    {
      "path": "backend/Dockerfile",
      "status": " M",
      "size": 887,
      "sha256": "c820c3dfa260b84e87bc5819fa5f5634139ee78477e1691ca9ed43402638d7c7",
      "readStatus": "readable"
    },
    {
      "path": "backend/app/core/http_protocol.py",
      "status": "??",
      "size": 4266,
      "sha256": "6637260d2e6a3ea33ba8d92fc9afb9930a68a31851d4fc75f48b264ea3f7c111",
      "readStatus": "readable"
    },
    {
      "path": "backend/app/core/request_context.py",
      "status": "??",
      "size": 852,
      "sha256": "fa76d8621cd0990107f3a7b965515764a88b67950b5290eb7b4e667748d61540",
      "readStatus": "readable"
    },
    {
      "path": "backend/app/main.py",
      "status": " M",
      "size": 11580,
      "sha256": "4038b6e0c885c07c8cb618eeb8b9f83fb4d0c9007209e6c447ad4f1343e6fc67",
      "readStatus": "readable"
    },
    {
      "path": "backend/pilot_server.py",
      "status": "??",
      "size": 981,
      "sha256": "654360f675b07b821a13f50984e11626e26b9e48671051ae988d48b04979ce33",
      "readStatus": "readable"
    },
    {
      "path": "backend/tests/test_pilot_package_d.py",
      "status": "??",
      "size": 25226,
      "sha256": "ab7a29bbd966c9ccf7889b6aa346d11323a6fe53ff082d726f8ffb5f88095871",
      "readStatus": "readable"
    },
    {
      "path": "backend/tests/test_pilot_privacy.py",
      "status": "??",
      "size": 49111,
      "sha256": "e964a838bef83270d47bf380076c08dc0b2465a303264a2b80454552d7def976",
      "readStatus": "readable"
    }
  ],
  "reviewInputs": [
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-D-PRIVACY-AMENDMENT/decision.md",
      "status": "review_input",
      "size": 19689,
      "sha256": "422d36b8d4ed85953771733d727d65ee3d5ef0dbf2f1525168d5db0808bdcfb8",
      "readStatus": "readable"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-D-PRIVACY-AMENDMENT/findings.json",
      "status": "review_input",
      "size": 4148,
      "sha256": "a44b813a2fc0f153af140b31d183b3514f4dc27cea593ee18240805428533194",
      "readStatus": "readable"
    },
    {
      "path": ".ai/MODEL_ROUTING.md",
      "status": "review_input",
      "size": 10194,
      "sha256": "043890c6138ba45f88dcb8a4ea209d288f4a8e8625cf60d9127408c1ff240261",
      "readStatus": "readable"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-D-PRIVACY-AMENDMENT/closure.md",
      "status": "review_input",
      "size": 4566,
      "sha256": "d9d889da28469907e798bbe7569c744c184333e5218fac1345d859518ac626e9",
      "readStatus": "readable"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-D-PRIVACY-AMENDMENT/adversarial-closure-initial.md",
      "status": "review_input",
      "size": 1285,
      "sha256": "6ee113d6b082311f806ecf47f659c73f7ba94cce4f1c80c03b96e67460d70ffd",
      "readStatus": "readable"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-D-PRIVACY-AMENDMENT/adversarial-closure-remediation.md",
      "status": "review_input",
      "size": 1033,
      "sha256": "521469b52297df0d20f386310c9471cd041d9564b853a82a6c593ded3799d96b",
      "readStatus": "readable"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-D-PRIVACY-AMENDMENT/adversarial-closure-final.md",
      "status": "review_input",
      "size": 1089,
      "sha256": "5c02003819162a8fde11936036ceec2f803582978e1f96d47ba3351abcd3ac48",
      "readStatus": "readable"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-D/adversarial-closure-final.md",
      "status": "review_input",
      "size": 1174,
      "sha256": "ab710ce245c2a799d0737f53e32aba9b48990de9c9ac7ce8ee7147def7ec6c14",
      "readStatus": "readable"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-D-PRIVACY-AMENDMENT/adversarial-design-final.md",
      "status": "review_input",
      "size": 2525,
      "sha256": "6673a7801c24caabcfabf8f6a83d3d1d6e3289f3864e1215dfe0cd5902c9d493",
      "readStatus": "readable"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-D-PRIVACY-AMENDMENT/implementation.md",
      "status": "review_input",
      "size": 9955,
      "sha256": "801ca317131d2627925418f95649b52b1881bc893fe0c3a0a2013b5979f33530",
      "readStatus": "readable"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-D-PRIVACY-AMENDMENT/adversarial-implementation-final.md",
      "status": "review_input",
      "size": 1923,
      "sha256": "623e3d3875acd071d9a4782d8d696108988b83f5d7fabb895a5c9cdc9776d5a7",
      "readStatus": "readable"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-D/package-d-remediation-3.md",
      "status": "review_input",
      "size": 5091,
      "sha256": "756fa5484b929519c62077a2745afe78918690e514c7e4c8aaeb7eb1188ae8aa",
      "readStatus": "readable"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-D/findings.json",
      "status": "review_input",
      "size": 12492,
      "sha256": "8a91536049d36f9431a9b2b08733737e3df3168ddeae683824871e6a17b3879c",
      "readStatus": "readable"
    },
    {
      "path": "backend/requirements.lock",
      "status": "review_input",
      "size": 64899,
      "sha256": "729a4a4316e863db493204ecc103c41943162cb7986af3fe5669a10e8d66462d",
      "readStatus": "readable"
    },
    {
      "path": "infra/terraform/ecs_runtime.tf",
      "status": "review_input",
      "size": 15832,
      "sha256": "6f0c3e1296ff67269841d421fbf94f404036676a3ef36654f73240d794633891",
      "readStatus": "readable"
    }
  ],
  "outOfScopeDirtyFiles": [
    {
      "path": ".ai/MODEL_ROUTING.md",
      "status": " M"
    },
    {
      "path": ".ai/PILOT_RELEASE_BOUNDARY.md",
      "status": "??"
    },
    {
      "path": ".ai/pilot-package-c-context-v1.json",
      "status": "??"
    },
    {
      "path": ".ai/pilot-release-boundary-v1.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/acceptance-bootstrap-ast-executor.py",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/acceptance-bootstrap-ast-schema-v1.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/acceptance-bootstrap-reference-program-v1.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/acceptance-calibration-goldens.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/acceptance-design-results.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/acceptance-design-validator.py",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/acceptance-mapping-reconstruction-provenance.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/acceptance-mapping-v1.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/acceptance-mapping.schema.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/acceptance-persistence-bootstrap-provenance.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/acceptance-persistence-bootstrap-results.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/acceptance-persistence-bootstrap-validator.py",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/acceptance-persistence-requirements-v1.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/acceptance-persistence-requirements-v2.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/acceptance-persistence-v1.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/acceptance-persistence.schema.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/acceptance-semantic-fixtures-v1.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/acceptance-semantic-goldens-v1.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/acceptance-semantic-interpreter.py",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/acceptance-semantic-mutations-v1.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/acceptance-semantic-oracle-provenance.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/acceptance-semantic-oracle-results.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/acceptance-source-catalog-v1.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/acceptance-source-catalog.schema.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/acceptance-source-schema-v2.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/acceptance-source-validator.py",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/acceptance-synthetic-results.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/acceptance-synthetic-vectors.py",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/adversarial-architecture-reassessment.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/adversarial-authority-dag-closure-1.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/adversarial-authority-dag-closure-2.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/adversarial-authority-dag-closure-3.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/adversarial-authority-dag.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/adversarial-authority-versioning-bootstrap.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/adversarial-authority-versioning-remediation-4.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/adversarial-bootstrap-closure-1.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/adversarial-bootstrap-inputs.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/adversarial-design-closure-1.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/adversarial-design-closure-2.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/adversarial-design-initial.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/adversarial-design-integration-final.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/adversarial-local-cloud-partition-amendment.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/adversarial-local-semantic-kernel-remediation-2.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/adversarial-local-semantic-kernel-remediation-3.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/adversarial-local-semantic-kernel.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/adversarial-local-semantic-predicate-oracle-design-remediation-2.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/adversarial-local-semantic-predicate-oracle-design-remediation-3.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/adversarial-local-semantic-predicate-oracle-design-remediation-4.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/adversarial-local-semantic-predicate-oracle-design-remediation-5.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/adversarial-local-semantic-predicate-oracle-design-remediation-6.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/adversarial-local-semantic-predicate-oracle-design.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/adversarial-mapping-reconstruction.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/adversarial-orm-source-authority-design.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/adversarial-orm-source-authority-implementation.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/adversarial-persistence-acl-canonicalization-remediation-2.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/adversarial-persistence-acl-canonicalization-remediation.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/adversarial-persistence-acl-rollback-blocker.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/adversarial-persistence-dag-implementation.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/adversarial-persistence-runtime-authority-reassessment.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/adversarial-platform-runtime-authority-local-blocker.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/adversarial-platform-runtime-authority-local-v2.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/adversarial-platform-runtime-authority-profile-v2.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/adversarial-platform-runtime-authority-profile.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/adversarial-platform-runtime-authority-rds-preflight.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/adversarial-platform-runtime-authority-rds-prerequisite-remediation-2.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/adversarial-platform-runtime-authority-rds-prerequisite.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/adversarial-resource-rebinding.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/architecture-oracle-reassessment.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/authority-dag-remediation-2.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/authority-dag-remediation-3.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/authority-dag-remediation.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/authority-history/decision-authority-map-v1/acceptance-persistence-v1.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/authority-history/decision-authority-map-v1/resource-accounting-v2.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/authority-versioning-remediation-4.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/closure.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/decision-authority-map-v1.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/decision-authority-map-v2.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/decision-authority-map-v2.schema.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/decision-authority-map.schema.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/decision.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/design-integration-provenance.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/design-remediation-2.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/design-remediation.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/findings.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/independent-acceptance-enumerator.py",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/local-cloud-partition-amendment.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/local-semantic-kernel/entry-fence-v2.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/local-semantic-kernel/entry-fence.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/local-semantic-kernel/implementation.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/local-semantic-kernel/predicate-cases-v1.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/local-semantic-kernel/predicate-oracle-results-v1.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/local-semantic-kernel/predicate-registry-v1.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/local-semantic-kernel/results.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/local-semantic-kernel/semantic_harness.py",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/local-semantic-kernel/semantic_kernel.py",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/local-semantic-predicate-oracle-design.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/manifest.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/normative-acceptance-matrix.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/oracle-provenance.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/orm-source-authority-decision.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/orm-source-authority-implementation.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/persistence-acl-canonicalization-remediation-2.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/persistence-acl-canonicalization-remediation.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/persistence-acl-rollback-blocker.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/persistence-implementation.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/persistence-runtime-authority-reassessment.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/platform-runtime-authority-0029-binary-manifest.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/platform-runtime-authority-0029-binary-provenance.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/platform-runtime-authority-0029-binary.tar.gz",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/platform-runtime-authority-local-oracle-v2.py",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/platform-runtime-authority-local-oracle.py",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/platform-runtime-authority-local-provenance-v2.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/platform-runtime-authority-local-provenance.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/platform-runtime-authority-local-results-v2.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/platform-runtime-authority-local-results.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/platform-runtime-authority-oracle-plan-v2.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/platform-runtime-authority-oracle-plan.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/platform-runtime-authority-profile-v1.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/platform-runtime-authority-profile-v1.schema.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/platform-runtime-authority-profile-v2.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/platform-runtime-authority-profile-v2.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/platform-runtime-authority-profile-v2.schema.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/platform-runtime-authority-profile.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/platform-runtime-authority-rds-execution-manifest.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/platform-runtime-authority-rds-preflight-provenance.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/platform-runtime-authority-rds-preflight-results.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/platform-runtime-authority-rds-preflight.py",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/platform-runtime-authority-rds-prerequisite-amendment.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/platform-runtime-authority-relationship-oracle.py",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/platform-runtime-authority-relationship-results.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/resource-accounting-results.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/resource-accounting-v2.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/resource-accounting-vectors.py",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/resource-accounting.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/resource-accounting.schema.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/resource-contract-builder.py",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/resource-reconstruction-provenance.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/review-packet.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/reviews.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/risk-adjusted-routing-audit.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/run-trusted-sentinel.sh",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/sql-topology-benchmark.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/state.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/trusted-sentinel-harness.sql",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/trusted-sentinel-output.txt",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-B/adversarial-design-inheritance.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-B/adversarial-implementation-initial.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-B/adversarial-implementation-remediation-1.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-B/closure.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-B/decision.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-B/findings.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-B/manifest.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-B/package-b-remediation-1.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-B/review-packet.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-B/reviews.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-B/state.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-C-ACM-AMENDMENT/adversarial-design.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-C-ACM-AMENDMENT/closure.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-C-ACM-AMENDMENT/decision.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-C-ACM-AMENDMENT/findings.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-C-ACM-AMENDMENT/implementation.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-C-ACM-AMENDMENT/manifest.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-C-ACM-AMENDMENT/review-packet.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-C-ACM-AMENDMENT/reviews.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-C-ACM-AMENDMENT/state.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-C/adversarial-closure-final.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-C/adversarial-closure-initial.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-C/adversarial-design-closure-1.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-C/adversarial-design-closure-2.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-C/adversarial-design-initial.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-C/adversarial-implementation-initial.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-C/adversarial-implementation-remediation-1.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-C/adversarial-implementation-remediation-2.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-C/aws-readonly-preflight.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-C/closure.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-C/decision.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-C/design-remediation-1.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-C/findings.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-C/manifest.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-C/package-c-implementation.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-C/package-c-remediation-1.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-C/package-c-remediation-2.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-C/review-packet.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-C/reviews.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-C/state.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-D/adversarial-closure-final.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-D/adversarial-closure-initial.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-D/adversarial-closure-remediation.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-D/adversarial-design-closure.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-D/adversarial-design-inheritance.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-D/adversarial-implementation-initial.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-D/adversarial-implementation-remediation-1.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-D/adversarial-implementation-remediation-2.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-D/adversarial-implementation-remediation-3.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-D/closure.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-D/decision.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-D/findings.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-D/manifest.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-D/package-d-implementation.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-D/package-d-remediation-1.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-D/package-d-remediation-2.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-D/package-d-remediation-3.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-D/review-packet.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-D/review-recording-delta.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-D/reviews.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-D/state.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT/adversarial-authority-architecture-amendment.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT/adversarial-design-closure-1.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT/adversarial-design-initial.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT/adversarial-implementation-package-a-initial.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT/adversarial-implementation-package-a-remediation-1.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT/adversarial-implementation-package-a-remediation-2.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT/adversarial-implementation-package-a-remediation-3.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT/closure.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT/decision.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT/design-remediation-1.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT/findings.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT/manifest.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT/package-a-authority-architecture-amendment.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT/package-a-implementation.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT/package-a-remediation-1.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT/package-a-remediation-2.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT/package-a-remediation-3.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT/package-b-implementation.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT/review-packet.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT/reviews.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT/state.json",
      "status": "??"
    },
    {
      "path": "backend/.env.example",
      "status": " M"
    },
    {
      "path": "backend/app/api/deps.py",
      "status": " M"
    },
    {
      "path": "backend/app/api/routes/admin.py",
      "status": " M"
    },
    {
      "path": "backend/app/api/routes/ads.py",
      "status": " M"
    },
    {
      "path": "backend/app/api/routes/aircraft.py",
      "status": " M"
    },
    {
      "path": "backend/app/api/routes/auth.py",
      "status": " M"
    },
    {
      "path": "backend/app/api/routes/ingestion.py",
      "status": " M"
    },
    {
      "path": "backend/app/api/routes/logbook_entries.py",
      "status": " M"
    },
    {
      "path": "backend/app/api/routes/observability.py",
      "status": " M"
    },
    {
      "path": "backend/app/api/routes/uploads.py",
      "status": " M"
    },
    {
      "path": "backend/app/core/config.py",
      "status": " M"
    },
    {
      "path": "backend/app/db/migrations/sql/20260916_0030_candidate_acceptance_contract.json",
      "status": "??"
    },
    {
      "path": "backend/app/db/migrations/sql/20260916_0030_candidate_acceptance_integrity.sql",
      "status": "??"
    },
    {
      "path": "backend/app/db/migrations/versions/20260916_0030_add_ad_v4_candidate_acceptance.py",
      "status": "??"
    },
    {
      "path": "backend/app/models/core.py",
      "status": " M"
    },
    {
      "path": "backend/app/schemas/auth.py",
      "status": " M"
    },
    {
      "path": "backend/app/schemas/observability.py",
      "status": " M"
    },
    {
      "path": "backend/app/scripts/revoke_auth_sessions.py",
      "status": "??"
    },
    {
      "path": "backend/app/scripts/run_ocr_feasibility.py",
      "status": " M"
    },
    {
      "path": "backend/app/services/ad_v4_acceptance_persistence_contract.py",
      "status": "??"
    },
    {
      "path": "backend/app/services/ingestion.py",
      "status": " M"
    },
    {
      "path": "backend/app/services/invitations.py",
      "status": "??"
    },
    {
      "path": "backend/app/services/pilot_achievements.py",
      "status": "??"
    },
    {
      "path": "backend/app/services/pilot_summary.py",
      "status": "??"
    },
    {
      "path": "backend/app/services/session_revocation.py",
      "status": "??"
    },
    {
      "path": "backend/requirements.lock",
      "status": "??"
    },
    {
      "path": "backend/tests/test_ad_matching.py",
      "status": " M"
    },
    {
      "path": "backend/tests/test_ad_v4_acceptance_persistence.py",
      "status": "??"
    },
    {
      "path": "backend/tests/test_ad_v4_acceptance_persistence_postgres.py",
      "status": "??"
    },
    {
      "path": "backend/tests/test_ad_v4_model_source_authority.py",
      "status": "??"
    },
    {
      "path": "backend/tests/test_ad_v4_model_source_authority_postgres.py",
      "status": "??"
    },
    {
      "path": "backend/tests/test_pilot_invite_tenant_boundary.py",
      "status": "??"
    },
    {
      "path": "backend/tests/test_pilot_package_c.py",
      "status": "??"
    },
    {
      "path": "backend/tests/test_pilot_release_boundary.py",
      "status": "??"
    },
    {
      "path": "frontend/paprnav-frontend/.dockerignore",
      "status": "??"
    },
    {
      "path": "frontend/paprnav-frontend/.env.example",
      "status": " M"
    },
    {
      "path": "frontend/paprnav-frontend/Dockerfile",
      "status": "??"
    },
    {
      "path": "frontend/paprnav-frontend/next.config.ts",
      "status": " M"
    },
    {
      "path": "frontend/paprnav-frontend/package-lock.json",
      "status": " M"
    },
    {
      "path": "frontend/paprnav-frontend/package.json",
      "status": " M"
    },
    {
      "path": "frontend/paprnav-frontend/src/app/(auth)/invite/page.tsx",
      "status": "??"
    },
    {
      "path": "frontend/paprnav-frontend/src/app/(auth)/page.tsx",
      "status": " M"
    },
    {
      "path": "frontend/paprnav-frontend/src/app/(auth)/register/page.tsx",
      "status": " M"
    },
    {
      "path": "frontend/paprnav-frontend/src/app/(authenticated)/observability/page.tsx",
      "status": " M"
    },
    {
      "path": "frontend/paprnav-frontend/src/app/api/backend/[...path]/route.ts",
      "status": " M"
    },
    {
      "path": "frontend/paprnav-frontend/src/lib/api.ts",
      "status": " M"
    },
    {
      "path": "frontend/paprnav-frontend/src/lib/pilot-ocr-summary.ts",
      "status": "??"
    },
    {
      "path": "frontend/paprnav-frontend/tests/pilot-observability.test.mjs",
      "status": "??"
    },
    {
      "path": "infra/aws-iam/pilot-policy-matrix.json",
      "status": "??"
    },
    {
      "path": "infra/bootstrap/Dockerfile",
      "status": "??"
    },
    {
      "path": "infra/bootstrap/bootstrap.py",
      "status": "??"
    },
    {
      "path": "infra/bootstrap/grant-manifest.json",
      "status": "??"
    },
    {
      "path": "infra/bootstrap/reference-data.json",
      "status": "??"
    },
    {
      "path": "infra/bootstrap/requirements.in",
      "status": "??"
    },
    {
      "path": "infra/bootstrap/requirements.lock",
      "status": "??"
    },
    {
      "path": "infra/terraform/database.tf",
      "status": " M"
    },
    {
      "path": "infra/terraform/ecs_runtime.tf",
      "status": " M"
    },
    {
      "path": "infra/terraform/load_balancer.tf",
      "status": " M"
    },
    {
      "path": "infra/terraform/main.tf",
      "status": " M"
    },
    {
      "path": "infra/terraform/network.tf",
      "status": " M"
    },
    {
      "path": "infra/terraform/outputs.tf",
      "status": " M"
    },
    {
      "path": "infra/terraform/tests/package_c.tftest.hcl",
      "status": "??"
    },
    {
      "path": "infra/terraform/variables.tf",
      "status": " M"
    },
    {
      "path": "infra/terraform/versions.tf",
      "status": " M"
    },
    {
      "path": "scripts/build_pilot_migration_context.py",
      "status": "??"
    },
    {
      "path": "scripts/build_pilot_release_context.py",
      "status": "??"
    },
    {
      "path": "scripts/generate-ad-v4-acceptance-persistence.py",
      "status": "??"
    },
    {
      "path": "scripts/generate_pilot_deploy_policy.py",
      "status": "??"
    },
    {
      "path": "scripts/verify_pilot_release_boundary.py",
      "status": "??"
    }
  ],
  "outOfScopeReason": "Closure covers only the approved post-third-loop HTTP logging/privacy amendment and its exact-runtime evidence; live deployment remains Package E and unrelated dirty work remains excluded."
}
```

## Diff against base

```diff
diff --git a/backend/Dockerfile b/backend/Dockerfile
index 1411be0..9f0fa72 100644
--- a/backend/Dockerfile
+++ b/backend/Dockerfile
@@ -1,4 +1,5 @@
-FROM python:3.12-slim
+ARG PYTHON_BASE=python:3.12.11-slim-bookworm@sha256:519591d6871b7bc437060736b9f7456b8731f1499a57e22e6c285135ae657bf7
+FROM ${PYTHON_BASE}
 
 ENV PYTHONDONTWRITEBYTECODE=1
 ENV PYTHONUNBUFFERED=1
@@ -9,13 +10,18 @@ RUN apt-get update \
     && apt-get install --no-install-recommends --yes mdbtools poppler-utils \
     && rm -rf /var/lib/apt/lists/*
 
-RUN python -m pip install --upgrade pip
-
-COPY requirements.txt .
-RUN pip install --no-cache-dir -r requirements.txt
+COPY requirements.lock .
+RUN pip install --no-cache-dir --require-hashes -r requirements.lock
 
 COPY . .
 
+RUN addgroup --system --gid 10001 paprnav \
+    && adduser --system --uid 10001 --ingroup paprnav --home /nonexistent --no-create-home paprnav \
+    && chown -R 10001:10001 /app
+
 EXPOSE 8000
 
-CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
+USER 10001:10001
+HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
+  CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3).read()"]
+CMD ["python", "-m", "pilot_server"]
diff --git a/backend/app/main.py b/backend/app/main.py
index 910f197..1af57d2 100644
--- a/backend/app/main.py
+++ b/backend/app/main.py
@@ -1,12 +1,275 @@
-from fastapi import FastAPI
+import json
+import logging
+from enum import Enum
+
+from fastapi import FastAPI, Request
 from fastapi.middleware.cors import CORSMiddleware
+from fastapi.responses import JSONResponse
+from starlette.datastructures import MutableHeaders
+from starlette.types import ASGIApp, Message, Receive, Scope, Send
+from starlette._utils import get_route_path
+from urllib.parse import urlsplit
 
+from app.api.deps import SESSION_COOKIE_NAME
 from app.api.router import api_router
-from app.core.config import get_settings
+from app.core.config import get_settings, validate_runtime_settings
+from app.core.http_protocol import cancellation_kind
+from app.core.request_context import (
+    CORRELATION_ID_HEADER,
+    choose_correlation_id,
+    reset_correlation_id,
+    set_correlation_id,
+)
+
+
+unexpected_error_logger = logging.getLogger("paprnav.unexpected_error")
+
+
+class HTTPDeliveryState(Enum):
+    NEW = "not_started"
+    PENDING = "start_buffered"
+    START_ATTEMPTED = "start_delivery_uncertain"
+    STARTED = "start_delivered"
+    BODY_ATTEMPTED = "body_delivery_uncertain"
+    STREAMING = "body_delivered"
+    END_ATTEMPTED = "end_delivery_uncertain"
+    COMPLETE = "complete"
+    DISCONNECTED = "disconnected"
+
+
+class HTTPDeliveryStopped(Exception):
+    """Unwind an HTTP producer without retaining transport exception content."""
+
+
+class PilotRequestBoundaryMiddleware:
+    """Own correlation and sanitized failures for the complete HTTP lifecycle."""
+
+    def __init__(self, app: ASGIApp, *, settings) -> None:
+        self.app = app
+        self.settings = settings
+
+    async def __call__(
+        self,
+        scope: Scope,
+        receive: Receive,
+        send: Send,
+    ) -> None:
+        if scope["type"] != "http":
+            await self.app(scope, receive, send)
+            return
+
+        request = Request(scope, receive=receive)
+        correlation_id = choose_correlation_id(
+            request.headers.get(CORRELATION_ID_HEADER)
+        )
+        correlation_token = set_correlation_id(correlation_id)
+        request.state.correlation_id = correlation_id
+        pending_start: Message | None = None
+        delivery_state = HTTPDeliveryState.NEW
+        response_status: int | None = None
+        failure_state: HTTPDeliveryState | None = None
+        cancellation: BaseException | None = None
+
+        async def receive_with_disconnect() -> Message:
+            nonlocal delivery_state
+            message = await receive()
+            if (
+                message["type"] == "http.disconnect"
+                and delivery_state != HTTPDeliveryState.COMPLETE
+            ):
+                delivery_state = HTTPDeliveryState.DISCONNECTED
+            return message
+
+        async def deliver(
+            message: Message,
+            attempted: HTTPDeliveryState,
+            delivered: HTTPDeliveryState,
+        ) -> None:
+            nonlocal delivery_state
+            # A send can fail before or after writing bytes. Set the state
+            # before awaiting it; an exception must never authorize a retry.
+            delivery_state = attempted
+            await send(message)
+            if delivery_state == HTTPDeliveryState.DISCONNECTED:
+                raise HTTPDeliveryStopped()
+            delivery_state = delivered
+
+        async def send_with_correlation(message: Message) -> None:
+            nonlocal pending_start, delivery_state, response_status
+            message_type = message["type"]
+            if message_type == "http.response.start":
+                if delivery_state != HTTPDeliveryState.NEW:
+                    raise HTTPDeliveryStopped()
+                pending_start = dict(message)
+                pending_start["headers"] = list(message.get("headers", []))
+                MutableHeaders(scope=pending_start)[CORRELATION_ID_HEADER] = (
+                    correlation_id
+                )
+                delivery_state = HTTPDeliveryState.PENDING
+                return
+
+            if message_type != "http.response.body" or delivery_state not in {
+                HTTPDeliveryState.PENDING,
+                HTTPDeliveryState.STARTED,
+                HTTPDeliveryState.STREAMING,
+            }:
+                raise HTTPDeliveryStopped()
+
+            if delivery_state == HTTPDeliveryState.PENDING:
+                response_status = pending_start["status"]
+                await deliver(
+                    pending_start,
+                    HTTPDeliveryState.START_ATTEMPTED,
+                    HTTPDeliveryState.STARTED,
+                )
+                pending_start = None
+
+            final_body = not message.get("more_body", False)
+            await deliver(
+                message,
+                HTTPDeliveryState.END_ATTEMPTED if final_body else HTTPDeliveryState.BODY_ATTEMPTED,
+                HTTPDeliveryState.COMPLETE if final_body else HTTPDeliveryState.STREAMING,
+            )
+
+        async def send_generic_error() -> None:
+            response = JSONResponse(
+                status_code=500,
+                content={
+                    "detail": "Unexpected server error",
+                    "correlationId": correlation_id,
+                },
+            )
+
+            await response(scope, receive_with_disconnect, send_with_correlation)
+
+        try:
+            try:
+                if not self.settings.ad_v4_routes_enabled and is_ad_v4_path(
+                    get_route_path(scope)
+                ):
+                    response = JSONResponse(
+                        status_code=404,
+                        content={"detail": "Not Found"},
+                    )
+                    await response(scope, receive_with_disconnect, send_with_correlation)
+                elif (
+                    self.settings.environment == "pilot"
+                    and request.method.upper() in {"POST", "PUT", "PATCH", "DELETE"}
+                    and request.cookies.get(SESSION_COOKIE_NAME)
+                    and request_origin(request) != self.settings.cors_origins[0]
+                ):
+                    response = JSONResponse(
+                        status_code=403,
+                        content={"detail": "Cross-origin request rejected"},
+                    )
+                    await response(scope, receive_with_disconnect, send_with_correlation)
+                else:
+                    await self.app(scope, receive_with_disconnect, send_with_correlation)
+
+                if delivery_state == HTTPDeliveryState.PENDING:
+                    await send_with_correlation(
+                        {
+                            "type": "http.response.body",
+                            "body": b"",
+                            "more_body": False,
+                        }
+                    )
+                elif delivery_state in {
+                    HTTPDeliveryState.NEW,
+                    HTTPDeliveryState.STARTED,
+                    HTTPDeliveryState.STREAMING,
+                }:
+                    raise HTTPDeliveryStopped()
+            except BaseException as error:
+                # Uvicorn logs even cancellation/BaseExceptionGroup failures
+                # with exc_info. The HTTP boundary owns that entire path.
+                failure_state = delivery_state
+                if cancellation_kind(error) is not None:
+                    cancellation = error
+                try:
+                    if cancellation is not None:
+                        pass
+                    elif delivery_state in {HTTPDeliveryState.NEW, HTTPDeliveryState.PENDING}:
+                        pending_start = None
+                        delivery_state = HTTPDeliveryState.NEW
+                        await send_generic_error()
+                    elif delivery_state in {HTTPDeliveryState.STARTED, HTTPDeliveryState.STREAMING}:
+                        # Only confirmed delivery permits a terminator for the
+                        # existing response. Never retry any uncertain send.
+                        await send_with_correlation(
+                            {"type": "http.response.body", "body": b"", "more_body": False}
+                        )
+                except BaseException as recovery_error:
+                    # Recovery shares the same state machine and containment.
+                    # A transport failure cannot reach Uvicorn's traceback log.
+                    if cancellation_kind(recovery_error) is not None:
+                        cancellation = recovery_error
+            if failure_state is not None or delivery_state not in {HTTPDeliveryState.COMPLETE}:
+                route = scope.get("route")
+                route_template = getattr(route, "path", None) or "unmatched"
+                method = request.method.upper()
+                log_record = {
+                    "event": "unexpected_request_error",
+                    "routeTemplate": route_template,
+                    "method": method if method in {"GET", "HEAD", "POST", "PUT", "DELETE", "CONNECT", "OPTIONS", "TRACE", "PATCH"} else "OTHER",
+                    "status": 500,
+                    "release": self.settings.app_version,
+                    "correlationId": correlation_id,
+                    "failureState": (failure_state or delivery_state).value,
+                    "deliveryState": delivery_state.value,
+                    "responseStatus": response_status,
+                }
+                if cancellation is not None:
+                    log_record["failureKind"] = cancellation_kind(cancellation)
+                for state_name, output_name in (
+                    ("actor_user_id", "actorUserId"),
+                    ("organization_id", "organizationId"),
+                    ("aircraft_id", "aircraftId"),
+                ):
+                    value = getattr(request.state, state_name, None)
+                    if value:
+                        log_record[output_name] = value
+                try:
+                    unexpected_error_logger.error(
+                        json.dumps(log_record, sort_keys=True, separators=(",", ":"))
+                    )
+                except Exception:
+                    # A broken log sink must not expose its exception context
+                    # through the default server traceback logger either.
+                    pass
+            if cancellation is not None:
+                # The owned HTTP protocol consumes cancellation only after
+                # request-local evidence and context cleanup, without a send.
+                raise cancellation
+        finally:
+            reset_correlation_id(correlation_token)
+
+
+def is_ad_v4_path(path: str) -> bool:
+    segments = [segment for segment in path.split("/") if segment]
+    return (
+        len(segments) >= 4
+        and segments[:3] == ["api", "v1", "ads"]
+        and "v4" in segments[3:]
+    )
+
+
+def request_origin(request: Request) -> str | None:
+    origin = request.headers.get("origin")
+    if origin:
+        return origin
+    referer = request.headers.get("referer")
+    if not referer:
+        return None
+    parsed = urlsplit(referer)
+    if not parsed.scheme or not parsed.netloc:
+        return None
+    return f"{parsed.scheme}://{parsed.netloc}"
 
 
 def create_app() -> FastAPI:
     settings = get_settings()
+    validate_runtime_settings(settings)
     app = FastAPI(title=settings.app_name, version=settings.app_version)
 
     app.add_middleware(
@@ -16,6 +279,7 @@ def create_app() -> FastAPI:
         allow_methods=["*"],
         allow_headers=["*"],
     )
+    app.add_middleware(PilotRequestBoundaryMiddleware, settings=settings)
 
     app.include_router(api_router)
 

```

## Untracked text files

### `backend/app/core/http_protocol.py`

size=4266; sha256=6637260d2e6a3ea33ba8d92fc9afb9930a68a31851d4fc75f48b264ea3f7c111; truncated=false

```text
"""Production HTTP transport boundary for the pinned Uvicorn h11 protocol."""

from asyncio import CancelledError

from starlette.types import Message, Receive, Scope, Send
from uvicorn.protocols.http.h11_impl import H11Protocol

from app.core.request_context import reset_correlation_id, set_correlation_id


def cancellation_kind(error: BaseException) -> str | None:
    """Classify by types only, including mixed nested cancellation groups."""
    if isinstance(error, CancelledError):
        return "cancelled"
    pending = [error]
    while pending:
        current = pending.pop()
        if isinstance(current, CancelledError):
            return "cancelled_group"
        if isinstance(current, BaseExceptionGroup):
            pending.extend(current.exceptions)
    return None


class HTTPTransportStopped(Exception):
    """An observed disconnect makes this request's delivery terminal."""


class PilotH11Protocol(H11Protocol):
    """Make an uncertain send terminal before Uvicorn considers a fallback 500."""

    def on_response_complete(self) -> None:
        # Uvicorn can spawn a pipelined successor here, inside the old task's
        # final send. Give the new task a neutral correlation context while
        # retaining the old task's own context for its remaining cleanup.
        token = set_correlation_id(None)
        try:
            super().on_response_complete()
        finally:
            reset_correlation_id(token)

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        application = self.app

        async def transport_boundary(scope: Scope, receive: Receive, send: Send) -> None:
            # Capture this request's cycle before a keep-alive request can
            # replace self.cycle. WebSocket upgrades use their own protocol.
            if scope["type"] != "http":
                await application(scope, receive, send)
                return
            cycle = self.cycle
            transport = self.transport
            final_send_returned = False

            def abort_owned_cycle() -> None:
                # Successful completion transfers connection ownership even
                # while this application's task continues unwinding. The
                # server's response_complete flag precedes its final write,
                # so it cannot stand in for successful final-send return.
                if final_send_returned:
                    return
                cycle.disconnected = True
                cycle.keep_alive = False
                # No await may intervene between this check and close. An old
                # task must never close a successor's shared transport.
                if self.cycle is cycle and self.transport is transport:
                    try:
                        transport.close()
                    except BaseException:
                        pass

            async def send_once(message: Message) -> None:
                nonlocal final_send_returned
                try:
                    if cycle.disconnected:
                        raise HTTPTransportStopped()
                    await send(message)
                    if cycle.disconnected:
                        raise HTTPTransportStopped()
                    if message["type"] == "http.response.body" and not message.get("more_body", False):
                        final_send_returned = True
                except BaseException:
                    # In particular, flow.drain() can fail before Uvicorn sets
                    # response_started. Returning to run_asgi with disconnected
                    # false would authorize its own second response attempt.
                    abort_owned_cycle()
                    raise

            try:
                await application(scope, receive, send_once)
            except BaseException as error:
                if cancellation_kind(error) is None:
                    raise
                # Cancellation is terminal, including before any send or at an
                # unrelated application await. Never expose it to run_asgi's
                # traceback/fallback response path and never attempt recovery.
                abort_owned_cycle()

        self.app = transport_boundary

```
### `backend/app/core/request_context.py`

size=852; sha256=fa76d8621cd0990107f3a7b965515764a88b67950b5290eb7b4e667748d61540; truncated=false

```text
from __future__ import annotations

from contextvars import ContextVar, Token
import re
from uuid import uuid4


CORRELATION_ID_HEADER = "X-Correlation-ID"
_CORRELATION_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")
_correlation_id: ContextVar[str | None] = ContextVar(
    "paprnav_correlation_id",
    default=None,
)


def valid_correlation_id(value: str | None) -> bool:
    return bool(value and _CORRELATION_ID_PATTERN.fullmatch(value))


def choose_correlation_id(value: str | None) -> str:
    return value if valid_correlation_id(value) else uuid4().hex


def set_correlation_id(value: str | None) -> Token[str | None]:
    return _correlation_id.set(value)


def reset_correlation_id(token: Token[str | None]) -> None:
    _correlation_id.reset(token)


def get_correlation_id() -> str | None:
    return _correlation_id.get()

```
### `backend/pilot_server.py`

size=981; sha256=654360f675b07b821a13f50984e11626e26b9e48671051ae988d48b04979ce33; truncated=false

```text
"""The production API entry point; logging policy precedes all server imports."""

import logging

# StreamHandler/lastResort/shutdown failures must not print their exception,
# traceback or record arguments. Failed evidence can be lost; never retry it in
# another sink. Keep this policy for the entire process, including shutdown.
logging.raiseExceptions = False


def create_config():
    import uvicorn

    return uvicorn.Config(
        "main:app",
        host="0.0.0.0",
        port=8000,
        http="app.core.http_protocol:PilotH11Protocol",
        access_log=False,
        log_level="info",
        timeout_graceful_shutdown=10,
    )


def main():
    import sys

    # The image has one reviewed configuration, not a second CLI for overrides.
    if len(sys.argv) != 1:
        raise SystemExit("The pilot API launcher accepts no arguments")
    config = create_config()
    import uvicorn

    uvicorn.Server(config).run()


if __name__ == "__main__":
    main()

```
### `backend/tests/test_pilot_package_d.py`

size=25226; sha256=ab7a29bbd966c9ccf7889b6aa346d11323a6fe53ff082d726f8ffb5f88095871; truncated=false

```text
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from io import BytesIO
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.core import (
    ADExtraction,
    ADExtractionReview,
    ADMatchResult,
    AirworthinessDirective,
    IngestionJob,
    IngestionPage,
    LogbookEntry,
    OCRRun,
    OCRTextSpan,
    ProductEvent,
    Upload,
)
from app.services.ingestion import extract_entries_from_job
from app.services.invitations import create_invitation
from app.services.pilot_achievements import (
    ACHIEVEMENT_SPECS,
    PILOT_ACHIEVEMENT_TAXONOMY,
    project_pilot_achievements,
    record_pilot_achievement,
)
from tests.conftest import (
    TEST_PASSWORD,
    add_membership,
    create_aircraft,
    create_organization,
    create_user,
    login,
)


INVITE_SECRET = "package-d-invitation-secret-at-least-32-bytes"
def _event_count(db: Session) -> int:
    return db.scalar(
        select(func.count()).select_from(ProductEvent).where(
            ProductEvent.event_source == PILOT_ACHIEVEMENT_TAXONOMY
        )
    ) or 0


def _achievement_events(db: Session, event_type: str) -> list[ProductEvent]:
    return list(
        db.scalars(
            select(ProductEvent).where(
                ProductEvent.event_source == PILOT_ACHIEVEMENT_TAXONOMY,
                ProductEvent.event_type == event_type,
            )
        ).all()
    )


def _add_verified_extraction_job(
    db: Session,
    *,
    aircraft,
    user,
    suffix: str,
) -> IngestionJob:
    upload = Upload(
        aircraft_id=aircraft.id,
        uploaded_by_user_id=user.id,
        original_filename=f"{suffix}.pdf",
        content_type="application/pdf",
        file_size_bytes=100,
        storage_backend="local",
        storage_key=f"fixtures/{suffix}.pdf",
        sha256=suffix.rjust(64, "0"),
        status="processed",
        pilot_consent_accepted=True,
    )
    db.add(upload)
    db.flush()
    job = IngestionJob(
        upload_id=upload.id,
        aircraft_id=aircraft.id,
        created_by_user_id=user.id,
        status="ready_for_entry_extraction",
        page_extraction_status="complete",
        ocr_status="complete",
        verification_status="verified",
        entry_extraction_status="ready",
        logbook_section_key="airframe",
    )
    db.add(job)
    db.flush()
    page = IngestionPage(
        ingestion_job_id=job.id,
        upload_id=upload.id,
        source_page_number=1,
        current_page_order=1,
        page_label="Page 1",
    )
    db.add(page)
    db.flush()
    run = OCRRun(
        ingestion_job_id=job.id,
        provider_name="package_d_test",
        provider_version="1",
        configuration_hash=suffix,
        status="complete",
        billing_status="not_billable",
    )
    db.add(run)
    db.flush()
    db.add(
        OCRTextSpan(
            ocr_run_id=run.id,
            ingestion_page_id=page.id,
            provider_block_id=f"{suffix}-line",
            span_type="LINE",
            text="2026-09-01 Annual inspection completed.",
            confidence=95,
            bbox_left=0.1,
            bbox_top=0.1,
            bbox_width=0.8,
            bbox_height=0.1,
            bbox_units="ratio",
            reading_order=1,
        )
    )
    db.commit()
    return job


def _add_ocr_run(
    db: Session,
    *,
    aircraft,
    user,
    suffix: str,
    status: str,
    billing_status: str,
    account_tag: str | None,
    aircraft_tag: str | None,
    pages: int | None,
    rate: Decimal | None,
) -> OCRRun:
    upload = Upload(
        aircraft_id=aircraft.id,
        uploaded_by_user_id=user.id,
        original_filename=f"{suffix}.pdf",
        content_type="application/pdf",
        file_size_bytes=100,
        storage_backend="local",
        storage_key=f"fixtures/{suffix}.pdf",
        sha256=suffix.rjust(64, "0"),
        status="processed",
        pilot_consent_accepted=True,
    )
    db.add(upload)
    db.flush()
    job = IngestionJob(
        upload_id=upload.id,
        aircraft_id=aircraft.id,
        created_by_user_id=user.id,
        status="processing",
        page_extraction_status="complete",
        ocr_status=status,
        verification_status="not_started",
        entry_extraction_status="not_started",
    )
    db.add(job)
    db.flush()
    run = OCRRun(
        ingestion_job_id=job.id,
        provider_name="test_provider",
        provider_version="1",
        configuration_hash=suffix,
        status=status,
        billing_status=billing_status,
        billable_account_tag=account_tag,
        billable_aircraft_tag=aircraft_tag,
        billable_page_count=pages,
        pricing_unit="page" if pages is not None else None,
        pricing_rate_usd=rate,
    )
    db.add(run)
    db.flush()
    return run


def test_achievement_transaction_projection_and_fixed_properties(
    db_session: Session,
    demo_data: dict[str, object],
) -> None:
    actor = demo_data["owner_user"]
    aircraft = demo_data["aircraft"]
    assert set(ACHIEVEMENT_SPECS) == {
        "invite_accepted",
        "aircraft_created",
        "upload_received",
        "page_review_completed",
        "logbook_entry_created",
        "ad_review_completed",
    }

    first = record_pilot_achievement(
        db_session,
        event_type="upload_received",
        subject_type="upload",
        subject_id="upl_first",
        actor=actor,
        organization_id=aircraft.owner_organization_id,
        aircraft_id=aircraft.id,
        properties={
            "contentType": "application/pdf",
            "storageBackend": "local",
            "filename": "secret-logbook.pdf",
            "token": "secret",
            "nested": {"raw_text": "maintenance content"},
        },
    )
    db_session.commit()
    assert first.properties_json == {
        "contentType": "application/pdf",
        "storageBackend": "local",
        "taxonomyVersion": PILOT_ACHIEVEMENT_TAXONOMY,
    }
    committed_count = _event_count(db_session)

    record_pilot_achievement(
        db_session,
        event_type="upload_received",
        subject_type="upload",
        subject_id="upl_rolled_back",
        actor=actor,
    )
    db_session.rollback()
    assert _event_count(db_session) == committed_count

    other_actor = create_user(db_session, "achievement.other@paprnav.local", "Other Actor")
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    first.event_time = now - timedelta(minutes=3)
    duplicate = record_pilot_achievement(
        db_session,
        event_type="upload_received",
        subject_type="upload",
        subject_id="upl_first",
        actor=other_actor,
    )
    duplicate.event_time = now - timedelta(minutes=2)
    second = record_pilot_achievement(
        db_session,
        event_type="upload_received",
        subject_type="upload",
        subject_id="upl_second",
        actor=other_actor,
    )
    second.event_time = now - timedelta(minutes=1)
    db_session.commit()

    counts, recent = project_pilot_achievements(db_session, recent_limit=1)
    assert counts["upload_received"] == 2
    assert [row.subject_id for row in recent] == ["upl_second"]
    actor_counts, actor_recent = project_pilot_achievements(
        db_session,
        actor_user_id=other_actor.id,
        recent_limit=10,
    )
    assert actor_counts["upload_received"] == 1
    assert [row.subject_id for row in actor_recent] == ["upl_second"]


def test_success_conflict_admin_boundary_and_recorded_cost_categories(
    client: TestClient,
    db_session: Session,
    demo_data: dict[str, object],
) -> None:
    owner = demo_data["owner_user"]
    aircraft = demo_data["aircraft"]
    second_owner = create_user(db_session, "pilot.second@paprnav.local", "Second Pilot")
    second_org = create_organization(db_session, "Second Pilot Org", "owner")
    add_membership(db_session, second_org, second_owner, "owner_admin")
    second_aircraft = create_aircraft(db_session, second_org, second_owner, n_number="N822PD")
    admin = create_user(db_session, "pilot.admin@paprnav.local", "Pilot Admin")
    admin_org = create_organization(db_session, "Pilot Operations", "platform")
    admin_membership = add_membership(db_session, admin_org, admin, "platform_admin")

    record_pilot_achievement(
        db_session,
        event_type="aircraft_created",
        subject_type="aircraft",
        subject_id=aircraft.id,
        actor=owner,
        organization_id=aircraft.owner_organization_id,
        aircraft_id=aircraft.id,
    )
    record_pilot_achievement(
        db_session,
        event_type="aircraft_created",
        subject_type="aircraft",
        subject_id=second_aircraft.id,
        actor=second_owner,
        organization_id=second_org.id,
        aircraft_id=second_aircraft.id,
    )
    _add_ocr_run(
        db_session,
        aircraft=aircraft,
        user=owner,
        suffix="priced",
        status="complete",
        billing_status="chargeable",
        account_tag="historical-account",
        aircraft_tag="historical-aircraft",
        pages=2,
        rate=Decimal("0.020"),
    )
    _add_ocr_run(
        db_session,
        aircraft=aircraft,
        user=owner,
        suffix="failed",
        status="failed",
        billing_status="disputed",
        account_tag=None,
        aircraft_tag=None,
        pages=None,
        rate=None,
    )
    _add_ocr_run(
        db_session,
        aircraft=second_aircraft,
        user=second_owner,
        suffix="pending",
        status="running",
        billing_status="not_billable",
        account_tag="second-account",
        aircraft_tag="second-aircraft",
        pages=1,
        rate=Decimal("0.010"),
    )
    db_session.commit()

    login(client, "owner.test@paprnav.local")
    assert client.get("/api/v1/admin/pilot-summary").status_code == 403
    client.post("/api/v1/auth/logout")
    login(client, "pilot.admin@paprnav.local")
    response = client.get("/api/v1/admin/pilot-summary", params={"recentLimit": 1})
    assert response.status_code == 200
    payload = response.json()
    assert payload["achievements"]["counts"]["aircraft_created"] == 2
    assert len(payload["achievements"]["recent"]) == 1
    assert payload["ocr"] == {
        "recordedRunsOnly": True,
        "paidAttemptCoverageComplete": False,
        "reconciliationCompletenessAvailable": False,
        "missingRowVisibilityAvailable": False,
        "attributionBasis": "recorded_billing_tags",
        "historicalTagsReattributed": False,
        "recordedRunCount": 3,
        "lifecycleCounts": {"completed": 1, "failed": 1, "pending": 1},
        "pricingCounts": {"priced": 2, "unpriced": 1},
        "attributionCounts": {"attributed": 2, "unattributed": 1},
        "billingCounts": {
            "chargeable": 1,
            "not_billable": 1,
            "credited": 0,
            "disputed": 1,
            "other": 0,
        },
        "reconciliationRequiredRunCount": 2,
        "knownEstimateRunCount": 2,
        "unknownAmountRunCount": 1,
        "knownPartialEstimateUsd": 0.05,
        "completedPricedEstimateUsd": 0.04,
        "estimateIsPartial": True,
    }

    admin_membership.status = "revoked"
    db_session.commit()
    assert client.get("/api/v1/admin/pilot-summary").status_code == 403


def test_route_success_points_emit_only_after_canonical_success(
    client: TestClient,
    db_session: Session,
    demo_data: dict[str, object],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("PAPRNAV_INVITE_SIGNING_SECRET", INVITE_SECRET)
    get_settings.cache_clear()
    invitation_code, _ = create_invitation(
        secret=INVITE_SECRET,
        email="package.d.invitee@example.test",
        name="Package D Invitee",
        organization_name="Package D Hangar",
        organization_type="owner",
        role="owner_admin",
    )
    accepted = client.post(
        "/api/v1/auth/invitations/accept",
        json={"invitationCode": invitation_code, "password": TEST_PASSWORD},
    )
    assert accepted.status_code == 201
    invite_events = _achievement_events(db_session, "invite_accepted")
    assert len(invite_events) == 1
    assert invite_events[0].actor_user_id == accepted.json()["user"]["id"]
    assert invite_events[0].subject_id == accepted.json()["user"]["id"]
    replay = client.post(
        "/api/v1/auth/invitations/accept",
        json={"invitationCode": invitation_code, "password": TEST_PASSWORD},
    )
    assert replay.status_code == 404
    assert len(_achievement_events(db_session, "invite_accepted")) == 1

    owner = demo_data["owner_user"]
    aircraft = demo_data["aircraft"]
    login(client, "owner.test@paprnav.local")
    aircraft_payload = {
        "nNumber": "N82PD",
        "make": "Cessna",
        "model": "172R",
        "serialNumber": "D-82",
    }
    created_aircraft = client.post("/api/v1/aircraft", json=aircraft_payload)
    assert created_aircraft.status_code == 201
    aircraft_events = _achievement_events(db_session, "aircraft_created")
    assert len(aircraft_events) == 1
    assert aircraft_events[0].actor_user_id == owner.id
    assert aircraft_events[0].subject_id == created_aircraft.json()["id"]
    assert aircraft_events[0].properties_json == {
        "hasAccountTag": True,
        "hasAircraftTag": True,
        "taxonomyVersion": PILOT_ACHIEVEMENT_TAXONOMY,
    }
    conflict = client.post("/api/v1/aircraft", json=aircraft_payload)
    assert conflict.status_code == 409
    assert len(_achievement_events(db_session, "aircraft_created")) == 1

    rejected_upload = client.post(
        f"/api/v1/aircraft/{aircraft.id}/uploads",
        data={"section": "airframe", "pilotConsentAccepted": "false"},
        files={"file": ("rejected.pdf", BytesIO(b"rejected"), "application/pdf")},
    )
    assert rejected_upload.status_code == 400
    assert _achievement_events(db_session, "upload_received") == []
    accepted_upload = client.post(
        f"/api/v1/aircraft/{aircraft.id}/uploads",
        data={"section": "airframe", "pilotConsentAccepted": "true"},
        files={"file": ("accepted.pdf", BytesIO(b"accepted"), "application/pdf")},
    )
    assert accepted_upload.status_code == 201
    upload_events = _achievement_events(db_session, "upload_received")
    assert len(upload_events) == 1
    assert upload_events[0].actor_user_id == owner.id
    assert upload_events[0].subject_id == accepted_upload.json()["upload"]["id"]

    manual_entry = client.post(
        f"/api/v1/aircraft/{aircraft.id}/logbook-entries",
        json={
            "section": "airframe",
            "entryDate": "2026-09-01",
            "description": "Annual inspection completed.",
        },
    )
    assert manual_entry.status_code == 201
    manual_event = _achievement_events(db_session, "logbook_entry_created")[-1]
    assert manual_event.subject_id == manual_entry.json()["id"]
    assert manual_event.actor_user_id == owner.id
    assert manual_event.properties_json["sourceType"] == "manual"

    job_id = accepted_upload.json()["ingestionJob"]["id"]
    job = db_session.get(IngestionJob, job_id)
    job.status = "awaiting_page_review"
    job.page_extraction_status = "complete"
    job.ocr_status = "complete"
    page = IngestionPage(
        ingestion_job_id=job.id,
        upload_id=job.upload_id,
        source_page_number=1,
        current_page_order=1,
        page_label="Page 1",
    )
    db_session.add(page)
    db_session.commit()
    verification_payload = {
        "pages": [{"pageId": page.id, "currentPageOrder": 1}],
        "isOrderConfirmed": True,
        "isComplete": False,
    }
    incomplete = client.post(
        f"/api/v1/ingestion-jobs/{job.id}/page-verification",
        json=verification_payload,
    )
    assert incomplete.status_code == 200
    assert _achievement_events(db_session, "page_review_completed") == []
    verification_payload["isComplete"] = True
    assert client.post(
        f"/api/v1/ingestion-jobs/{job.id}/page-verification",
        json=verification_payload,
    ).status_code == 200
    assert client.post(
        f"/api/v1/ingestion-jobs/{job.id}/page-verification",
        json=verification_payload,
    ).status_code == 200
    page_events = _achievement_events(db_session, "page_review_completed")
    assert len(page_events) == 1
    assert page_events[0].actor_user_id == owner.id
    assert page_events[0].subject_id == job.id


def test_extracted_entry_actor_retry_actorless_and_rollback(
    db_session: Session,
    demo_data: dict[str, object],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    owner = demo_data["owner_user"]
    aircraft = demo_data["aircraft"]
    job = _add_verified_extraction_job(
        db_session,
        aircraft=aircraft,
        user=owner,
        suffix="actor",
    )
    entries = extract_entries_from_job(db_session, job, pilot_actor=owner)
    assert len(entries) == 1
    events = _achievement_events(db_session, "logbook_entry_created")
    assert len(events) == 1
    assert events[0].subject_id == entries[0].id
    assert events[0].actor_user_id == owner.id
    assert events[0].organization_id == aircraft.owner_organization_id
    assert events[0].aircraft_id == aircraft.id

    retried = extract_entries_from_job(
        db_session,
        job,
        pilot_actor=demo_data["shop_user"],
    )
    assert [entry.id for entry in retried] == [entries[0].id]
    events = _achievement_events(db_session, "logbook_entry_created")
    assert len(events) == 1
    assert events[0].actor_user_id == owner.id

    actorless_job = _add_verified_extraction_job(
        db_session,
        aircraft=aircraft,
        user=owner,
        suffix="actorless",
    )
    actorless_entries = extract_entries_from_job(
        db_session,
        actorless_job,
        pilot_actor=None,
    )
    assert len(actorless_entries) == 1
    assert len(_achievement_events(db_session, "logbook_entry_created")) == 1

    rollback_job = _add_verified_extraction_job(
        db_session,
        aircraft=aircraft,
        user=owner,
        suffix="rollback",
    )
    entry_count_before = db_session.scalar(
        select(func.count()).select_from(LogbookEntry)
    )

    def fail_after_achievement(*args, **kwargs):
        record_pilot_achievement(*args, **kwargs)
        raise RuntimeError("force transaction rollback")

    monkeypatch.setattr(
        "app.services.ingestion.record_pilot_achievement",
        fail_after_achievement,
    )
    with pytest.raises(RuntimeError, match="force transaction rollback"):
        extract_entries_from_job(db_session, rollback_job, pilot_actor=owner)
    db_session.rollback()
    assert db_session.scalar(select(func.count()).select_from(LogbookEntry)) == entry_count_before
    assert len(_achievement_events(db_session, "logbook_entry_created")) == 1


def test_ad_decision_success_rejections_and_conflict_are_transactional(
    client: TestClient,
    db_session: Session,
    demo_data: dict[str, object],
) -> None:
    match_directive = AirworthinessDirective(
        ad_number="2026-82-00",
        title="Package D match fixture",
        status="accepted",
        source_content_hash="c" * 64,
        extraction_status="complete",
        review_status="approved",
    )
    db_session.add(match_directive)
    db_session.flush()
    match_extraction = ADExtraction(
        directive_id=match_directive.id,
        provider_name="package_d_test",
        provider_version="1",
        schema_version="ad_extraction_v3",
        input_content_hash="b" * 64,
        status="approved",
        confidence=0.9,
        output={"requirements": [], "applicabilityGroups": []},
        raw_response={
            "retainedSourcePagesCached": True,
            "retainedSourcePages": [],
        },
    )
    db_session.add(match_extraction)
    db_session.flush()
    match = ADMatchResult(
        aircraft_id=demo_data["aircraft"].id,
        directive_id=match_directive.id,
        extraction_id=match_extraction.id,
        status="needs_adjudication",
        match_type="unresolved",
        confidence=0.5,
        rationale="Bounded Package D match fixture.",
        unresolved_reasons=["human_review_required"],
        algorithm_name="package_d_test",
        algorithm_version="1",
        input_hash="a" * 64,
        is_current=True,
    )
    db_session.add(match)

    directive = AirworthinessDirective(
        ad_number="2026-82-01",
        title="Package D review fixture",
        status="candidate",
        source_content_hash="d" * 64,
        extraction_status="needs_review",
        review_status="pending",
    )
    db_session.add(directive)
    db_session.flush()
    extraction = ADExtraction(
        directive_id=directive.id,
        provider_name="package_d_test",
        provider_version="1",
        schema_version="ad_extraction_v3",
        input_content_hash="e" * 64,
        status="needs_review",
        confidence=0.5,
        output={"requirements": [], "applicabilityGroups": []},
        raw_response={
            "retainedSourcePagesCached": True,
            "retainedSourcePages": [],
        },
    )
    db_session.add(extraction)
    db_session.flush()
    review = ADExtractionReview(
        extraction_id=extraction.id,
        status="pending",
        proposed_output=extraction.output,
    )
    db_session.add(review)
    admin = create_user(db_session, "package.d.admin@example.test", "Package D Admin")
    admin_org = create_organization(db_session, "Package D Operations", "platform")
    add_membership(db_session, admin_org, admin, "platform_admin")
    db_session.commit()

    login(client, "owner.test@paprnav.local")
    owner_match_decision = client.post(
        f"/api/v1/ads/matches/{match.id}/adjudication",
        json={
            "decision": "needs_more_info",
            "notes": "Owner must not adjudicate.",
            "futureImprovementTags": [],
        },
    )
    assert owner_match_decision.status_code == 403
    assert _achievement_events(db_session, "ad_review_completed") == []

    login(client, "shop.test@paprnav.local")
    match_decision = client.post(
        f"/api/v1/ads/matches/{match.id}/adjudication",
        json={
            "decision": "needs_more_info",
            "notes": "Need additional evidence.",
            "futureImprovementTags": ["evidence_gap"],
        },
    )
    assert match_decision.status_code == 200
    match_events = _achievement_events(db_session, "ad_review_completed")
    assert len(match_events) == 1
    assert match_events[0].actor_user_id == demo_data["shop_user"].id
    assert match_events[0].subject_type == "ad_match_adjudication"
    assert match_events[0].properties_json["decisionKind"] == "aircraft_match"

    login(client, "owner.test@paprnav.local")
    unauthorized = client.post(
        f"/api/v1/ads/extraction-reviews/{review.id}/decision",
        json={"decision": "rejected"},
    )
    assert unauthorized.status_code == 403
    assert len(_achievement_events(db_session, "ad_review_completed")) == 1

    login(client, admin.email)
    invalid = client.post(
        f"/api/v1/ads/extraction-reviews/{review.id}/decision",
        json={"decision": "unsupported"},
    )
    assert invalid.status_code == 422
    assert len(_achievement_events(db_session, "ad_review_completed")) == 1

    rejected = client.post(
        f"/api/v1/ads/extraction-reviews/{review.id}/decision",
        json={"decision": "rejected", "notes": "Human review completed."},
    )
    assert rejected.status_code == 200
    ad_events = _achievement_events(db_session, "ad_review_completed")
    assert len(ad_events) == 2
    extraction_event = next(
        event for event in ad_events if event.subject_type == "ad_extraction_review"
    )
    assert extraction_event.actor_user_id == admin.id
    assert extraction_event.subject_id == review.id
    assert extraction_event.properties_json["decision"] == "rejected"

    conflict = client.post(
        f"/api/v1/ads/extraction-reviews/{review.id}/decision",
        json={"decision": "approved"},
    )
    assert conflict.status_code == 409
    assert len(_achievement_events(db_session, "ad_review_completed")) == 2


def test_static_budget_and_worker_gates():
    root = Path(__file__).resolve().parents[2]
    terraform_main = (root / "infra/terraform/main.tf").read_text(encoding="utf-8")
    terraform_vars = (root / "infra/terraform/variables.tf").read_text(encoding="utf-8")
    terraform_ecs = (root / "infra/terraform/ecs_runtime.tf").read_text(encoding="utf-8")
    assert 'variable "budget_notification_email"' in terraform_vars
    assert "no repository default" in terraform_vars
    assert "!endswith(var.budget_notification_email, \".invalid\")" in terraform_main
    assert "subscriber_email_addresses = [var.budget_notification_email]" in terraform_main
    assert 'resource "aws_scheduler_schedule" "worker"' in terraform_ecs
    assert 'state               = "DISABLED"' in terraform_ecs

```
### `backend/tests/test_pilot_privacy.py`

size=49111; sha256=e964a838bef83270d47bf380076c08dc0b2465a303264a2b80454552d7def976; truncated=false

```text
"""Backend-only production privacy oracle. Run against requirements.lock; no skips."""
from __future__ import annotations

import asyncio
import importlib
import importlib.metadata
import json
import logging
import os
from pathlib import Path
import re
import subprocess
import sys
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from uvicorn import Server
from uvicorn.server import ServerState

from app.core.config import get_settings
from app.core.http_protocol import cancellation_kind
from app.core.request_context import get_correlation_id
from app.db.session import get_db
from app.main import PilotRequestBoundaryMiddleware
from app.models.core import IngestionJob, IngestionPage, Upload
from tests.conftest import login


BACKEND_ROOT = Path(__file__).resolve().parents[1]


def _assert_locked_versions(versions):
    lock = (BACKEND_ROOT / "requirements.lock").read_text()
    for name, actual in versions.items():
        pins = re.findall(rf"^{re.escape(name)}==([^\s]+)", lock, re.MULTILINE)
        assert len(pins) == 1, (name, pins)
        assert actual == pins[0], (name, actual, pins[0])


@pytest.fixture(scope="module", autouse=True)
def locked_runtime_gate():
    # Runs before every case in this module. A stale venv is a failure, not a
    # skipped image assertion or a second source of expected package versions.
    names = ("uvicorn", "h11", "starlette", "anyio", "fastapi")
    _assert_locked_versions({name: importlib.metadata.version(name) for name in names})
    result = subprocess.run([sys.executable, "-m", "pip", "check"], capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stdout + result.stderr
    for name in names:
        module_path = Path(importlib.import_module(name).__file__).resolve()
        assert module_path.is_file()
        assert "site-packages" in module_path.parts


def _fresh_process(code, *args):
    # Deliberately do not inherit host credentials or configurable providers.
    environment = {
        "PATH": os.environ["PATH"], "PYTHONPATH": str(BACKEND_ROOT),
        "PAPRNAV_DISABLE_DOTENV": "1", "DATABASE_URL": "sqlite+pysqlite:///:memory:",
        "PAPRNAV_ENV": "local", "AWS_EC2_METADATA_DISABLED": "true",
    }
    result = subprocess.run([sys.executable, "-c", code, *args], cwd=BACKEND_ROOT,
                            env=environment, capture_output=True, text=True, timeout=15)
    assert result.returncode == 0, result.stdout + result.stderr
    return result


def test_launcher_startup_shutdown_and_handler_graph():
    command = next(line for line in (BACKEND_ROOT / "Dockerfile").read_text().splitlines() if line.startswith("CMD "))
    assert json.loads(command[4:]) == ["python", "-m", "pilot_server"]
    result = _fresh_process('''
import asyncio, builtins, logging, sys
original_import = builtins.__import__
seen = []
def checked_import(name, *args, **kwargs):
    if name == "uvicorn" or name == "app.main":
        assert logging.raiseExceptions is False
        seen.append(name)
    return original_import(name, *args, **kwargs)
builtins.__import__ = checked_import
import pilot_server
assert "uvicorn" not in sys.modules
config = pilot_server.create_config()
assert logging.raiseExceptions is False
assert config.app == "main:app" and config.host == "0.0.0.0" and config.port == 8000
assert config.http == "app.core.http_protocol:PilotH11Protocol"
assert config.access_log is False and config.log_level == "info"
assert config.timeout_graceful_shutdown == 10
config.load()
assert config.http_protocol_class.__name__ == "PilotH11Protocol"
assert not logging.getLogger("uvicorn.access").hasHandlers()
assert logging.getLogger("uvicorn.error").isEnabledFor(logging.INFO)
assert not logging.getLogger("uvicorn.error").isEnabledFor(logging.DEBUG)
assert not logging.getLogger("uvicorn.error").isEnabledFor(5)
handlers = logging.getLogger("uvicorn").handlers
assert len(handlers) == 1 and type(handlers[0]) is logging.StreamHandler
assert not handlers[0].filters
assert type(logging.lastResort).__name__ == "_StderrHandler"
assert not logging.lastResort.filters
assert not logging.getLogger().handlers
assert not logging.getLogger("paprnav.unexpected_error").handlers
logging.getLogger("uvicorn.error").info("healthy operational record")
logging.getLogger("paprnav.unexpected_error").error("healthy safe application record")
async def lifecycle():
    lifespan = config.lifespan_class(config)
    await lifespan.startup()
    assert not lifespan.should_exit and logging.raiseExceptions is False
    await lifespan.shutdown()
    assert logging.raiseExceptions is False
asyncio.run(lifecycle())
logging.shutdown()
assert logging.raiseExceptions is False
assert "uvicorn" in seen and "app.main" in seen
sys.argv = ["pilot_server", "--log-level=trace"]
try:
    pilot_server.main()
except SystemExit:
    pass
else:
    raise AssertionError("launcher allowed an override")
print("startup-shutdown-policy-ok")
''')
    assert "startup-shutdown-policy-ok" in result.stdout
    assert "healthy operational record" in result.stderr
    assert "healthy safe application record" in result.stderr
    assert "Traceback" not in result.stderr


SINK_PROBE = '''
import asyncio, io, json, logging, sys
import pilot_server
pilot_server.create_config()
from app.core.config import get_settings
from app.core.request_context import get_correlation_id
from app.main import PilotRequestBoundaryMiddleware
family, failure, negative = sys.argv[1:]
secret = "sink-" + failure + "-private-sentinel"
records, handle_errors = [], []
original_factory = logging.getLogRecordFactory()
def factory(*args, **kwargs):
    record = original_factory(*args, **kwargs)
    records.append(record)
    return record
logging.setLogRecordFactory(factory)
logger = logging.getLogger("uvicorn.error" if family == "uvicorn" else "paprnav.unexpected_error")
handler = logging.getLogger("uvicorn").handlers[0] if family == "uvicorn" else logging.lastResort
old_stderr, old_stdout = sys.stderr, sys.stdout
diagnostics, output, partial = io.StringIO(), io.StringIO(), io.StringIO()
class BrokenStream:
    def write(self, value):
        if failure == "write_partial":
            partial.write(value[:9])
        if failure in ("write", "write_partial"):
            raise OSError(secret)
        partial.write(value)
    def flush(self):
        if failure in ("flush", "shutdown"):
            raise OSError(secret)
class BrokenFormatter(logging.Formatter):
    def format(self, record):
        raise ValueError(secret)
saved_formatter = handler.formatter
saved_handle_error = handler.handleError
def observe_handle_error(record):
    handle_errors.append(record)
    # _StderrHandler's stream is dynamic. Separate the failing sink from the
    # stderr diagnostic channel while invoking the real stdlib implementation.
    sys.stderr = diagnostics
    try:
        saved_handle_error(record)
    finally:
        sys.stderr = broken if family == "fallback" else diagnostics
handler.handleError = observe_handle_error
broken = BrokenStream()
if family == "uvicorn":
    handler.stream = broken
    sys.stderr = diagnostics
else:
    sys.stderr = broken
sys.stdout = output
if failure == "formatter":
    handler.setFormatter(BrokenFormatter())
if negative == "true":
    logging.raiseExceptions = True
if failure == "shutdown":
    # Exercise the real shutdown branch against this exact effective handler.
    import weakref
    logging.shutdown([weakref.ref(handler)])
else:
    if family == "fallback":
        sent = []
        async def application(scope, receive, send):
            raise RuntimeError("application-private-sentinel")
        async def send(message):
            sent.append(message)
        async def receive():
            return {"type": "http.request", "body": b"private body"}
        async def request():
            scope = {"type": "http", "method": "GET", "path": "/private-path", "root_path": "",
                     "headers": [(b"x-correlation-id", b"sink-request")], "query_string": b"secret=query", "state": {}}
            await PilotRequestBoundaryMiddleware(application, settings=get_settings())(scope, receive, send)
            assert get_correlation_id() is None
        asyncio.run(request())
        assert len(sent) == 2 and sent[0]["status"] == 500
        assert json.loads(sent[1]["body"])["correlationId"] == "sink-request"
    else:
        logger.error("sanitized failure event")
    assert len(records) == 1 and len(handle_errors) == 1
assert all(r.exc_info is None and r.exc_text is None and r.stack_info is None for r in records)
assert secret not in repr([r.__dict__ for r in records])
handler.handleError = saved_handle_error
handler.setFormatter(saved_formatter)
if family == "uvicorn":
    handler.stream = old_stderr
sys.stderr, sys.stdout = old_stderr, old_stdout
logging.raiseExceptions = False
logger.error("later healthy record")
print(json.dumps({"diagnostics": diagnostics.getvalue(), "stdout": output.getvalue(),
                  "partial": partial.getvalue(), "secret": secret, "records": len(records)}))
'''


@pytest.mark.parametrize("family", ["uvicorn", "fallback"])
@pytest.mark.parametrize("failure", ["formatter", "write", "write_partial", "flush", "shutdown"])
def test_effective_handler_failures(family, failure):
    result = _fresh_process(SINK_PROBE, family, failure, "false")
    evidence = json.loads(result.stdout)
    assert evidence["diagnostics"] == evidence["stdout"] == ""
    assert evidence["secret"] not in evidence["partial"] + result.stderr
    assert "Traceback" not in result.stdout + result.stderr
    assert "application-private-sentinel" not in result.stdout + result.stderr
    assert "later healthy record" in result.stderr
    assert evidence["records"] == (1 if failure == "shutdown" else 2)


def test_negative_controls_detect_version_and_handler_policy():
    with pytest.raises(AssertionError):
        _assert_locked_versions({"uvicorn": "0.0.0"})
    result = _fresh_process(SINK_PROBE, "uvicorn", "write", "true")
    evidence = json.loads(result.stdout)
    assert evidence["secret"] in evidence["diagnostics"]
    assert "Traceback" in evidence["diagnostics"]


def test_nested_cancellation_classification_never_formats_or_recurses():
    class PrivateError(RuntimeError):
        def __str__(self):
            raise AssertionError("exception was serialized")
        def __repr__(self):
            raise AssertionError("exception was serialized")
    grouped = BaseExceptionGroup("private group", [asyncio.CancelledError(), PrivateError()])
    ordinary = ExceptionGroup("private group", [PrivateError()])
    for _ in range(1200):
        grouped = BaseExceptionGroup("private group", [grouped])
        ordinary = ExceptionGroup("private group", [ordinary])
    assert cancellation_kind(grouped) == "cancelled_group"
    assert cancellation_kind(ordinary) is None


HTTP_SECRETS = {
    name: f"private-{name}-sentinel"
    for name in ("query", "body", "cookie", "authorization", "filename", "exception", "storage-key", "session", "path")
}


def _http_scope():
    return {
        "type": "http", "asgi": {"version": "3.0", "spec_version": "2.4"},
        "http_version": "1.1", "method": "GET", "scheme": "http",
        "path": f"/probe/{HTTP_SECRETS['path']}", "root_path": "",
        "query_string": f"token={HTTP_SECRETS['query']}".encode(),
        "headers": [
            (b"host", b"testserver"), (b"x-correlation-id", b"http-matrix-1"),
            (b"cookie", f"paprnav_session={HTTP_SECRETS['cookie']}".encode()),
            (b"authorization", HTTP_SECRETS["authorization"].encode()),
        ],
        "client": ("127.0.0.1", 1234), "server": ("127.0.0.1", 8000), "state": {},
    }


def _http_scenario(scenario):
    async def application(scope, receive, send):
        scope["route"] = SimpleNamespace(path="/probe/{subject_id}")
        scope["state"].update(
            actor_user_id="server-actor", organization_id="server-org", aircraft_id="server-aircraft",
        )
        if scenario == "before_start":
            raise RuntimeError(HTTP_SECRETS["exception"])
        if scenario == "disconnect_before":
            await receive()
        await send({"type": "http.response.start", "status": 403 if scenario == "http_error" else 200, "headers": []})
        if scenario == "disconnect_pending":
            await receive()
        if scenario == "before_body":
            raise RuntimeError(HTTP_SECRETS["exception"])
        if scenario == "cancelled":
            raise asyncio.CancelledError(HTTP_SECRETS["exception"])
        await send({"type": "http.response.body", "body": b"first", "more_body": True})
        if scenario == "disconnect_body":
            await receive()
        if scenario == "after_body":
            raise RuntimeError(HTTP_SECRETS["exception"])
        await send({"type": "http.response.body", "body": b"second", "more_body": True})
        await send({"type": "http.response.body", "body": b"", "more_body": False})
        if scenario == "after_complete":
            raise RuntimeError(HTTP_SECRETS["exception"])

    return PilotRequestBoundaryMiddleware(application, settings=get_settings())


def _assert_private_http_logs(caplog, *, expected_errors, context=True):
    records = [record for record in caplog.records if record.name in {"paprnav.unexpected_error", "uvicorn.error", "uvicorn.access"}]
    retained = repr([record.__dict__ for record in records]) + caplog.text
    assert all(secret not in retained for secret in HTTP_SECRETS.values())
    assert all(record.exc_info is None and record.stack_info is None for record in records)
    assert not any(record.name.startswith("uvicorn.") for record in records)
    errors = [json.loads(record.getMessage()) for record in records]
    assert len(errors) == expected_errors
    for error in errors:
        assert error["correlationId"] == "http-matrix-1"
        assert error["routeTemplate"] == "/probe/{subject_id}"
        if context:
            assert error["actorUserId"] == "server-actor"
            assert error["organizationId"] == "server-org"
            assert error["aircraftId"] == "server-aircraft"
    return errors


@pytest.mark.parametrize(
    "scenario,fail_at,after_effect,attempt_count,status,delivery_state",
    [
        ("success", None, False, 4, 200, None),
        ("http_error", None, False, 4, 403, None),
        ("before_start", None, False, 2, 500, "complete"),
        ("before_body", None, False, 2, 500, "complete"),
        ("after_body", None, False, 3, 200, "complete"),
        ("after_complete", None, False, 4, 200, "complete"),
        ("success", 1, False, 1, 200, "start_delivery_uncertain"),
        ("success", 1, True, 1, 200, "start_delivery_uncertain"),
        ("success", 2, False, 2, 200, "body_delivery_uncertain"),
        ("success", 2, True, 2, 200, "body_delivery_uncertain"),
        ("success", 3, False, 3, 200, "body_delivery_uncertain"),
        ("success", 3, True, 3, 200, "body_delivery_uncertain"),
        ("success", 4, False, 4, 200, "end_delivery_uncertain"),
        ("success", 4, True, 4, 200, "end_delivery_uncertain"),
        ("before_start", 1, False, 1, 500, "start_delivery_uncertain"),
        ("before_start", 1, True, 1, 500, "start_delivery_uncertain"),
        ("before_start", 2, False, 2, 500, "end_delivery_uncertain"),
        ("before_start", 2, True, 2, 500, "end_delivery_uncertain"),
        ("before_body", 2, False, 2, 500, "end_delivery_uncertain"),
        ("before_body", 2, True, 2, 500, "end_delivery_uncertain"),
        ("after_body", 3, True, 3, 200, "end_delivery_uncertain"),
        ("after_body", 3, False, 3, 200, "end_delivery_uncertain"),
        ("disconnect_before", None, False, 0, None, "disconnected"),
        ("disconnect_pending", None, False, 0, None, "disconnected"),
        ("disconnect_body", None, False, 2, 200, "disconnected"),
    ],
)
def test_http_delivery_lifecycle_matrix(
    scenario, fail_at, after_effect, attempt_count, status, delivery_state, caplog,
):
    caplog.set_level(logging.ERROR)
    attempts, delivered = [], []

    async def receive():
        if scenario.startswith("disconnect"):
            return {"type": "http.disconnect"}
        return {"type": "http.request", "body": HTTP_SECRETS["body"].encode(), "more_body": False}

    async def send(message):
        attempts.append(message)
        failing = len(attempts) == fail_at
        if not failing or after_effect:
            delivered.append(message)
        if failing:
            raise OSError(" ".join(HTTP_SECRETS.values()))

    asyncio.run(_http_scenario(scenario)(_http_scope(), receive, send))
    assert len(attempts) == attempt_count
    starts = [message for message in attempts if message["type"] == "http.response.start"]
    assert len(starts) == (status is not None)
    if starts:
        assert starts[0]["status"] == status
        assert (b"x-correlation-id", b"http-matrix-1") in starts[0]["headers"]
    assert len(delivered) == attempt_count - (fail_at is not None and not after_effect)
    errors = _assert_private_http_logs(caplog, expected_errors=int(delivery_state is not None))
    if errors:
        assert errors[0]["deliveryState"] == delivery_state
    assert get_correlation_id() is None


@pytest.fixture
def production_http_config(monkeypatch, caplog):
    """Use the shipped launcher configuration, substituting only the probe app."""
    import pilot_server
    # Restore logging configuration after exercising Config.configure_logging.
    for name in ("uvicorn", "uvicorn.access", "uvicorn.error"):
        logger = logging.getLogger(name)
        for attribute in ("handlers", "propagate", "level", "disabled"):
            monkeypatch.setattr(logger, attribute, getattr(logger, attribute))

    def configure(application):
        config = pilot_server.create_config()
        assert config.app == "main:app"
        assert config.access_log is False
        assert config.http == "app.core.http_protocol:PilotH11Protocol"
        assert config.log_level == "info"
        assert config.timeout_graceful_shutdown == 10
        config.app = application
        config.load()
        assert not logging.getLogger("uvicorn.access").hasHandlers()
        logging.getLogger("uvicorn.error").addHandler(caplog.handler)
        return config

    return configure


class ProbeTransport(asyncio.Transport):
    def __init__(self, *, fail_write=None, after_effect=False):
        self.writes = []
        self.attempts = 0
        self.close_count = 0
        self.fail_write = fail_write
        self.after_effect = after_effect
        self.on_write = lambda: None

    def get_extra_info(self, name, default=None):
        return ("127.0.0.1", 8000) if name in {"sockname", "peername"} else default

    def is_closing(self):
        return bool(self.close_count)

    def close(self):
        self.close_count += 1

    def write(self, data):
        self.attempts += 1
        failing = self.attempts == self.fail_write
        if not failing or self.after_effect:
            self.writes.append(data)
        if failing:
            raise OSError(" ".join(HTTP_SECRETS.values()))
        self.on_write()

    def pause_reading(self):
        pass

    def resume_reading(self):
        pass


def _request_bytes(correlation="http-matrix-1"):
    return (f"GET /probe/{HTTP_SECRETS['path']}?token={HTTP_SECRETS['query']} HTTP/1.1\r\n"
            f"Host: testserver\r\nX-Correlation-ID: {correlation}\r\n"
            f"Cookie: paprnav_session={HTTP_SECRETS['cookie']}\r\n"
            f"Authorization: {HTTP_SECRETS['authorization']}\r\n\r\n").encode()


def _protocol(configure, application, transport=None):
    contexts = []
    async def observed(scope, receive, send):
        try:
            await application(scope, receive, send)
        finally:
            if scope["type"] == "http":
                contexts.append(get_correlation_id())
    config = configure(observed)
    state = ServerState()
    protocol = config.http_protocol_class(config, state, {})
    transport = transport or ProbeTransport()
    protocol.connection_made(transport)
    return config, state, protocol, transport, contexts


async def _done_before_cleanup(tasks, transport):
    # asyncio.wait never cancels the subject to manufacture completion. Save
    # the pre-cleanup state in the assertion so a failure remains diagnosable.
    done, pending = await asyncio.wait(tasks, timeout=1)
    snapshot = {"pending": len(pending), "writes": transport.attempts,
                "closed": transport.is_closing(), "cancel_counts": [t.cancelling() for t in tasks]}
    assert not pending, snapshot
    for task in done:
        task.result()
    return snapshot


async def _cleanup(state, protocol):
    protocol._unset_keepalive_if_required()
    remaining = [task for task in state.tasks if not task.done()]
    for task in remaining:
        task.cancel()
    if remaining:
        await asyncio.gather(*remaining, return_exceptions=True)


def _cancellation(kind):
    plain = asyncio.CancelledError(HTTP_SECRETS["exception"])
    if kind == "plain":
        return plain
    pure = BaseExceptionGroup(HTTP_SECRETS["body"], [plain])
    if kind == "pure_group":
        return pure
    return BaseExceptionGroup(HTTP_SECRETS["cookie"], [RuntimeError(HTTP_SECRETS["storage-key"]), pure])


@pytest.mark.parametrize("kind", ["plain", "pure_group", "mixed_group"])
@pytest.mark.parametrize("place,expected_writes", [("before_start", 0), ("body", 2), ("recovery", 0), ("unrelated", 0)])
def test_single_cancellation_is_terminal(kind, place, expected_writes, production_http_config, caplog):
    caplog.set_level(logging.ERROR)
    async def run():
        suspended = asyncio.Event()
        async def application(scope, receive, send):
            if place in {"before_start", "unrelated"}:
                suspended.set()
                try:
                    await asyncio.Event().wait()
                except asyncio.CancelledError:
                    raise _cancellation(kind)
            if place == "recovery":
                raise RuntimeError(HTTP_SECRETS["exception"])
            await send({"type": "http.response.start", "status": 200, "headers": []})
            await send({"type": "http.response.body", "body": b"first", "more_body": True})
            await send({"type": "http.response.body", "body": b"second"})
        boundary = PilotRequestBoundaryMiddleware(application, settings=get_settings())
        _, state, protocol, transport, contexts = _protocol(production_http_config, boundary)
        drain = protocol.flow.drain
        async def observed_drain():
            suspended.set()
            try:
                await drain()
            except asyncio.CancelledError:
                raise _cancellation(kind)
        protocol.flow.drain = observed_drain
        if place == "recovery":
            protocol.pause_writing()
        elif place == "body":
            transport.on_write = lambda: protocol.pause_writing() if transport.attempts == 2 else None
        protocol.data_received(_request_bytes())
        tasks = list(state.tasks)
        try:
            await asyncio.wait_for(suspended.wait(), timeout=1)
            assert not tasks[0].done()
            tasks[0].cancel()
            snapshot = await _done_before_cleanup(tasks, transport)
            assert snapshot["cancel_counts"] == [1]
            assert transport.attempts == expected_writes
            assert protocol.cycle.disconnected and not protocol.cycle.keep_alive
            assert transport.is_closing()
            assert contexts == [None]
        finally:
            await _cleanup(state, protocol)
    asyncio.run(run())
    records = [record for record in caplog.records if record.name in {"paprnav.unexpected_error", "uvicorn.error", "uvicorn.access"}]
    assert len(records) == 1 and records[0].name == "paprnav.unexpected_error"
    assert json.loads(records[0].getMessage())["failureKind"] == ("cancelled" if kind == "plain" else "cancelled_group")
    assert all(secret not in repr([r.__dict__ for r in records]) for secret in HTTP_SECRETS.values())
    assert records[0].exc_info is None and records[0].exc_text is None


@pytest.mark.parametrize("action,expected_writes,errors", [("resume", 5, 0), ("disconnect", 0, 1)])
def test_actual_paused_output(action, expected_writes, errors, production_http_config, caplog):
    caplog.set_level(logging.ERROR)
    async def run():
        _, state, protocol, transport, contexts = _protocol(production_http_config, _http_scenario("success"))
        protocol.pause_writing()
        entered = asyncio.Event()
        original = protocol.flow.drain
        async def drain():
            entered.set()
            await original()
        protocol.flow.drain = drain
        protocol.data_received(_request_bytes())
        tasks = list(state.tasks)
        try:
            await asyncio.wait_for(entered.wait(), timeout=1)
            assert not tasks[0].done() and transport.attempts == 0
            if action == "resume":
                protocol.resume_writing()
            else:
                protocol.connection_lost(None)
            await _done_before_cleanup(tasks, transport)
            assert transport.attempts == expected_writes and contexts == [None]
            if action == "resume":
                wire = b"".join(transport.writes)
                assert b"first" in wire and b"second" in wire and wire.endswith(b"0\r\n\r\n")
                assert not transport.is_closing()
            else:
                assert protocol.cycle.disconnected and transport.is_closing()
        finally:
            await _cleanup(state, protocol)
    asyncio.run(run())
    _assert_private_http_logs(caplog, expected_errors=errors)


def test_negative_controls_detect_access_logs_and_adapter_bypass(production_http_config, caplog):
    async def run():
        # Mutations affect this test process only. Both controls must visibly
        # fail the same privacy oracle used by the positive matrix.
        config = production_http_config(_http_scenario("success"))
        access = logging.getLogger("uvicorn.access")
        access.addHandler(caplog.handler)
        access.setLevel(logging.INFO)
        state = ServerState()
        protocol = config.http_protocol_class(config, state, {})
        transport = ProbeTransport()
        protocol.connection_made(transport)
        assert protocol.access_log
        protocol.data_received(_request_bytes())
        try:
            await _done_before_cleanup(list(state.tasks), transport)
            with pytest.raises(AssertionError):
                _assert_private_http_logs(caplog, expected_errors=0)
            assert any(HTTP_SECRETS["query"] in r.getMessage() for r in caplog.records if r.name == "uvicorn.access")
        finally:
            await _cleanup(state, protocol)
        caplog.clear()
        from uvicorn.protocols.http.h11_impl import H11Protocol
        config = production_http_config(_http_scenario("success"))
        state = ServerState()
        protocol = H11Protocol(config, state, {})
        transport = ProbeTransport()
        protocol.connection_made(transport)
        protocol.pause_writing()
        calls = []
        async def fail_first_drain():
            calls.append(None)
            if len(calls) == 1:
                raise OSError(HTTP_SECRETS["exception"])
        protocol.flow.drain = fail_first_drain
        protocol.data_received(_request_bytes())
        try:
            await _done_before_cleanup(list(state.tasks), transport)
            with pytest.raises(AssertionError):
                _assert_private_http_logs(caplog, expected_errors=1)
            assert b"Internal Server Error" in b"".join(transport.writes)
            assert len(calls) == 3  # initial failure plus stock fallback start/body
        finally:
            await _cleanup(state, protocol)
    asyncio.run(run())


def test_group_without_cancellation_keeps_sanitized_recovery(production_http_config, caplog):
    caplog.set_level(logging.ERROR)
    async def application(scope, receive, send):
        raise ExceptionGroup(HTTP_SECRETS["body"], [RuntimeError(HTTP_SECRETS["exception"])])
    async def run():
        _, state, protocol, transport, contexts = _protocol(
            production_http_config, PilotRequestBoundaryMiddleware(application, settings=get_settings()))
        protocol.data_received(_request_bytes())
        try:
            await _done_before_cleanup(list(state.tasks), transport)
            assert b"HTTP/1.1 500" in b"".join(transport.writes)
            assert not transport.is_closing() and contexts == [None]
        finally:
            await _cleanup(state, protocol)
    asyncio.run(run())
    records = [r for r in caplog.records if r.name == "paprnav.unexpected_error"]
    assert len(records) == 1 and "failureKind" not in json.loads(records[0].getMessage())
    assert all(secret not in repr([r.__dict__ for r in caplog.records]) for secret in HTTP_SECRETS.values())


def test_sequential_keepalive_context_isolation(production_http_config, caplog):
    async def run():
        _, state, protocol, transport, contexts = _protocol(production_http_config, _http_scenario("success"))
        try:
            for correlation in ("sequential-A", "sequential-B"):
                protocol.data_received(_request_bytes(correlation))
                await _done_before_cleanup(list(state.tasks), transport)
                assert protocol.cycle.response_complete and not transport.is_closing()
            wire = b"".join(transport.writes)
            assert wire.count(b"HTTP/1.1 200") == 2
            assert wire.count(b"x-correlation-id: sequential-A") == 1
            assert wire.count(b"x-correlation-id: sequential-B") == 1
            assert contexts == [None, None]
        finally:
            await _cleanup(state, protocol)
    asyncio.run(run())
    _assert_private_http_logs(caplog, expected_errors=0)


def test_disconnect_unrelated_await_requires_real_shutdown_owner(production_http_config, caplog):
    async def run():
        entered, cancelled = asyncio.Event(), asyncio.Event()
        async def application(scope, receive, send):
            if scope["type"] == "lifespan":
                while True:
                    message = await receive()
                    await send({"type": message["type"] + ".complete"})
                    if message["type"] == "lifespan.shutdown":
                        return
            entered.set()
            try:
                await asyncio.Event().wait()
            except asyncio.CancelledError:
                cancelled.set()
                raise
        config, state, protocol, transport, contexts = _protocol(
            production_http_config, PilotRequestBoundaryMiddleware(application, settings=get_settings()))
        protocol.data_received(_request_bytes())
        tasks = list(state.tasks)
        try:
            await asyncio.wait_for(entered.wait(), timeout=1)
            protocol.connection_lost(None)
            done, pending = await asyncio.wait(tasks, timeout=0.03)
            # This observation precedes shutdown and every cleanup cancellation.
            assert not done and pending == set(tasks)
            assert not cancelled.is_set() and tasks[0].cancelling() == 0
            config.timeout_graceful_shutdown = 0.01
            server = Server(config)
            server.server_state = state
            server.servers = []
            server.lifespan = config.lifespan_class(config)
            await asyncio.wait_for(server.lifespan.startup(), timeout=1)
            shutdown = asyncio.create_task(server.shutdown())
            await asyncio.wait_for(cancelled.wait(), timeout=1)
            snapshot = await _done_before_cleanup(tasks, transport)
            assert snapshot["cancel_counts"] == [1]
            assert contexts == [None] and transport.attempts == 0
            await asyncio.wait_for(shutdown, timeout=1)
        finally:
            await _cleanup(state, protocol)
    asyncio.run(run())
    records = [r for r in caplog.records if r.name in {"uvicorn.error", "paprnav.unexpected_error"}]
    assert any("timeout graceful shutdown exceeded" in r.getMessage() for r in records)
    assert all(r.exc_info is None for r in records)
    assert all(secret not in repr([r.__dict__ for r in records]) for secret in HTTP_SECRETS.values())


@pytest.mark.parametrize("kind", ["plain", "pure_group", "mixed_group"])
@pytest.mark.parametrize("ownership", ["completed_current", "completed_successor", "noncurrent_incomplete", "different_transport"])
def test_cancellation_cannot_abort_successor(kind, ownership, production_http_config, caplog):
    caplog.set_level(logging.ERROR)
    async def run():
        old_waiting, successor_waiting, release_successor = asyncio.Event(), asyncio.Event(), asyncio.Event()
        correlations = []
        async def application(scope, receive, send):
            correlation = get_correlation_id()
            correlations.append(correlation)
            if correlation == "successor-B":
                successor_waiting.set()
                await release_successor.wait()
                await send({"type": "http.response.start", "status": 201, "headers": []})
                await send({"type": "http.response.body", "body": b"successor"})
                return
            if ownership.startswith("completed"):
                await send({"type": "http.response.start", "status": 200, "headers": []})
                await send({"type": "http.response.body", "body": b"old"})
            old_waiting.set()
            try:
                await asyncio.Event().wait()
            except asyncio.CancelledError:
                raise _cancellation(kind)
        _, state, protocol, transport, contexts = _protocol(
            production_http_config, PilotRequestBoundaryMiddleware(application, settings=get_settings()))
        protocol.data_received(_request_bytes("old-A"))
        old_task = next(iter(state.tasks))
        old_cycle = protocol.cycle
        try:
            if ownership == "completed_successor":
                # Pipeline B before A completes so on_response synchronously
                # transfers the current cycle before A's final send returns.
                protocol.data_received(_request_bytes("successor-B"))
                await asyncio.wait_for(successor_waiting.wait(), timeout=1)
                assert protocol.cycle is not old_cycle
            await asyncio.wait_for(old_waiting.wait(), timeout=1)
            if ownership == "noncurrent_incomplete":
                # Explicitly exercise the identity guard even when the old
                # wrapper has never observed a successful final send.
                protocol.cycle = SimpleNamespace(disconnected=False, keep_alive=True, response_complete=False)
            elif ownership == "different_transport":
                protocol.transport = ProbeTransport()
            current = protocol.cycle
            before = (current.disconnected, current.keep_alive, transport.attempts)
            old_task.cancel()
            await _done_before_cleanup([old_task], transport)
            assert not transport.is_closing()
            assert not protocol.transport.is_closing()
            assert transport.attempts == before[2]
            if ownership != "different_transport":
                assert (current.disconnected, current.keep_alive) == before[:2]
            if ownership == "completed_successor":
                assert not current.response_complete
                release_successor.set()
                await _done_before_cleanup(list(state.tasks), transport)
                assert current.response_complete
                wire = b"".join(transport.writes)
                assert wire.count(b"HTTP/1.1 ") == 2 and b"successor" in wire
                assert correlations == ["old-A", "successor-B"]
                assert contexts == [None, None]
            else:
                assert contexts == [None]
            if ownership in {"noncurrent_incomplete", "different_transport"}:
                assert old_cycle.disconnected and not old_cycle.keep_alive
            else:
                assert not old_cycle.disconnected and old_cycle.keep_alive
        finally:
            await _cleanup(state, protocol)
    asyncio.run(run())
    records = [r for r in caplog.records if r.name in {"paprnav.unexpected_error", "uvicorn.error", "uvicorn.access"}]
    assert len(records) == 1 and records[0].name == "paprnav.unexpected_error"
    assert json.loads(records[0].getMessage())["correlationId"] == "old-A"
    assert all(secret not in repr([r.__dict__ for r in records]) for secret in HTTP_SECRETS.values())


@pytest.mark.parametrize(
    "scenario,fail_write,drain_failure,status",
    [
        ("success", None, False, 200), ("http_error", None, False, 403),
        ("before_start", None, False, 500), ("before_body", None, False, 500),
        ("after_body", None, False, 200), ("after_complete", None, False, 200),
        ("success", None, True, None), ("success", 1, False, None),
        ("success", 2, False, 200), ("success", 3, False, 200),
        ("success", 5, False, 200), ("before_start", 1, False, None),
        ("before_body", 2, False, 500), ("after_body", 4, False, 200),
        ("disconnect_before", None, False, None),
        ("disconnect_pending", None, False, None),
        ("disconnect_body", None, False, 200),
    ],
)
@pytest.mark.parametrize("after_effect", [False, True])
def test_effective_uvicorn_http_logging(
    scenario, fail_write, drain_failure, status, after_effect, production_http_config, caplog,
):
    caplog.set_level(logging.ERROR)

    class Transport(asyncio.Transport):
        def __init__(self):
            self.writes = []
            self.attempts = 0
            self.closed = False
            self.on_disconnect = lambda: None

        def get_extra_info(self, name, default=None):
            return ("127.0.0.1", 8000) if name in {"sockname", "peername"} else default

        def is_closing(self):
            return self.closed

        def close(self):
            self.closed = True

        def write(self, data):
            self.attempts += 1
            failing = self.attempts == fail_write
            if not failing or after_effect:
                self.writes.append(data)
            if failing:
                raise OSError(" ".join(HTTP_SECRETS.values()))
            if scenario == "disconnect_body" and self.attempts == 2:
                self.close()
                self.on_disconnect()

    async def run():
        config = production_http_config(_http_scenario(scenario))
        server = ServerState()
        protocol = config.http_protocol_class(config, server, {})
        assert protocol.access_log is False
        # Capture any erroneously emitted access record without changing the
        # protocol's effective decision, made from the real configured logger.
        logging.getLogger("uvicorn.access").addHandler(caplog.handler)
        transport = Transport()
        protocol.connection_made(transport)
        transport.on_disconnect = lambda: protocol.connection_lost(None)
        if drain_failure:
            protocol.flow.write_paused = True

            async def fail_drain():
                raise OSError(" ".join(HTTP_SECRETS.values()))

            protocol.flow.drain = fail_drain
        scope = _http_scope()
        target = scope["path"].encode() + b"?" + scope["query_string"]
        request = b"GET " + target + b" HTTP/1.1\r\n"
        request += b"\r\n".join(name + b": " + value for name, value in scope["headers"])
        body = HTTP_SECRETS["body"].encode()
        request += b"\r\nContent-Length: " + str(len(body)).encode() + b"\r\n\r\n" + body
        protocol.data_received(request)
        if scenario in {"disconnect_before", "disconnect_pending"}:
            transport.close()
            transport.on_disconnect()
        try:
            await _done_before_cleanup(list(server.tasks), transport)
            assert get_correlation_id() is None
            return transport, protocol.cycle
        finally:
            await _cleanup(server, protocol)

    transport, cycle = asyncio.run(run())
    wire = b"".join(transport.writes)
    if fail_write == 1 and after_effect:
        status = 500 if scenario in {"before_start", "before_body"} else 200
    if status is None:
        assert b"HTTP/1.1" not in wire
    else:
        assert wire.count(b"HTTP/1.1 ") == 1
        assert wire.startswith(f"HTTP/1.1 {status}".encode())
        assert b"x-correlation-id: http-matrix-1" in wire
    if fail_write or drain_failure:
        assert cycle.disconnected and transport.closed
        assert transport.attempts == (fail_write or 0)
        if scenario == "success" and fail_write == 5:
            # The pinned server has already set response_complete, but the
            # final write is still uncertain and must close the current cycle.
            assert cycle.response_complete
    elif scenario.startswith("disconnect"):
        assert cycle.disconnected and transport.closed
        assert transport.attempts == (2 if scenario == "disconnect_body" else 0)
    else:
        assert cycle.response_complete
    _assert_private_http_logs(caplog, expected_errors=int(scenario not in {"success", "http_error"} or fail_write is not None or drain_failure))


@pytest.mark.parametrize("scope_type", ["lifespan", "websocket"])
@pytest.mark.parametrize("kind", ["ordinary", "plain", "pure_group", "mixed_group"])
def test_http_boundary_preserves_non_http_behavior(scope_type, kind, production_http_config):
    observed = []
    error = RuntimeError("non-http behavior unchanged") if kind == "ordinary" else _cancellation(kind)

    async def application(scope, receive, send):
        observed.append(scope["type"])
        assert get_correlation_id() is None
        raise error

    async def run():
        boundary = PilotRequestBoundaryMiddleware(application, settings=get_settings())
        config = production_http_config(boundary)
        protocol = config.http_protocol_class(config, ServerState(), {})
        await protocol.app({"type": scope_type}, None, None)
    with pytest.raises(BaseException) as caught:
        asyncio.run(run())
    assert caught.value is error
    assert observed == [scope_type]


@pytest.mark.parametrize("download_kind", ["upload", "page_image"])
def test_streaming_download_failures_are_sanitized_before_and_after_headers(
    client: TestClient,
    db_session: Session,
    demo_data: dict[str, object],
    monkeypatch: pytest.MonkeyPatch,
    caplog,
    download_kind,
) -> None:
    aircraft = demo_data["aircraft"]
    owner = demo_data["owner_user"]
    upload = Upload(
        aircraft_id=aircraft.id,
        uploaded_by_user_id=owner.id,
        original_filename=f"{HTTP_SECRETS['filename']}.pdf",
        content_type="application/pdf",
        file_size_bytes=7,
        storage_backend="s3",
        storage_key=f"package-d/{HTTP_SECRETS['storage-key']}.pdf",
        sha256="f" * 64,
        status="stored",
        pilot_consent_accepted=True,
    )
    db_session.add(upload)
    db_session.flush()
    job = IngestionJob(
        upload_id=upload.id, aircraft_id=aircraft.id, created_by_user_id=owner.id,
    )
    db_session.add(job)
    db_session.flush()
    page = IngestionPage(
        ingestion_job_id=job.id, upload_id=upload.id, source_page_number=1,
        current_page_order=1, page_label="Page 1", image_storage_backend="s3",
        image_storage_key=f"package-d/{HTTP_SECRETS['storage-key']}.png",
    )
    db_session.add(page)
    db_session.commit()
    url = (
        f"/api/v1/uploads/{upload.id}/download" if download_kind == "upload"
        else f"/api/v1/ingestion-jobs/{job.id}/pages/{page.id}/image"
    )
    route_template = (
        "/api/v1/uploads/{upload_id}/download" if download_kind == "upload"
        else "/api/v1/ingestion-jobs/{job_id}/pages/{page_id}/image"
    )

    observed_correlations: list[str | None] = []

    class FailingBody:
        def __init__(self, *, yield_first: bool, fail: bool) -> None:
            self.yield_first = yield_first
            self.fail = fail

        def iter_chunks(self):
            observed_correlations.append(get_correlation_id())
            if self.yield_first:
                yield b"partial"
            if self.fail:
                raise RuntimeError(" ".join(HTTP_SECRETS.values()))

    class FakeS3Client:
        def __init__(self) -> None:
            self.yield_first = False
            self.fail = True

        def get_object(self, **_kwargs):
            return {"Body": FailingBody(yield_first=self.yield_first, fail=self.fail)}

    fake_s3 = FakeS3Client()
    monkeypatch.setenv("PAPRNAV_S3_UPLOAD_BUCKET", "package-d-test-bucket")
    monkeypatch.setattr(
        f"app.api.routes.{'uploads' if download_kind == 'upload' else 'ingestion'}.get_s3_client",
        lambda _region: fake_s3,
    )
    get_settings.cache_clear()
    login(client, "owner.test@paprnav.local")
    caplog.set_level(logging.ERROR)

    before_headers = client.get(
        url + f"?token={HTTP_SECRETS['query']}",
        headers={"X-Correlation-ID": "stream-preheader"},
    )
    assert before_headers.status_code == 500
    assert before_headers.json() == {
        "detail": "Unexpected server error",
        "correlationId": "stream-preheader",
    }
    assert before_headers.headers["X-Correlation-ID"] == "stream-preheader"

    fake_s3.yield_first = True
    after_headers = client.get(
        url + f"?token={HTTP_SECRETS['query']}",
        headers={"X-Correlation-ID": "stream-postheader"},
    )
    assert after_headers.status_code == 200
    assert after_headers.content == b"partial"
    assert after_headers.headers["X-Correlation-ID"] == "stream-postheader"
    fake_s3.fail = False
    successful = client.get(url, headers={"X-Correlation-ID": "stream-success"})
    assert successful.status_code == 200
    assert successful.content == b"partial"
    assert observed_correlations == ["stream-preheader", "stream-postheader", "stream-success"]

    records = [
        json.loads(record.message)
        for record in caplog.records
        if record.name == "paprnav.unexpected_error"
    ]
    assert [record["correlationId"] for record in records] == [
        "stream-preheader",
        "stream-postheader",
    ]
    for record in records:
        assert record["routeTemplate"] == route_template
        assert record["actorUserId"] == owner.id
        assert record["organizationId"] == aircraft.owner_organization_id
        assert record["aircraftId"] == aircraft.id
        assert record["status"] == 500
    retained = caplog.text + repr([record.__dict__ for record in caplog.records])
    assert all(secret not in retained for secret in HTTP_SECRETS.values())
    assert all(record.exc_info is None for record in caplog.records)
    assert "traceback" not in caplog.text.lower()


def test_correlation_generic_error_db_outage(
    client: TestClient,
    caplog,
) -> None:
    valid = client.get("/health", headers={"X-Correlation-ID": "pilot.safe-123"})
    assert valid.status_code == 200
    assert valid.headers["X-Correlation-ID"] == "pilot.safe-123"
    invalid = client.get("/health", headers={"X-Correlation-ID": "bad token/value"})
    assert invalid.status_code == 200
    assert invalid.headers["X-Correlation-ID"] != "bad token/value"
    assert len(invalid.headers["X-Correlation-ID"]) == 32

    def unavailable_database():
        raise RuntimeError("postgres://user:password@db secret exception text")

    client.app.dependency_overrides[get_db] = unavailable_database
    caplog.set_level(logging.ERROR, logger="paprnav.unexpected_error")
    response = client.get(
        "/api/v1/admin/pilot-summary?token=query-secret",
        headers={
            "X-Correlation-ID": "db-outage-1",
            "Cookie": "paprnav_session=cookie-secret",
            "Authorization": "Bearer header-secret",
        },
    )
    client.app.dependency_overrides.pop(get_db, None)
    assert response.status_code == 500
    assert response.json() == {
        "detail": "Unexpected server error",
        "correlationId": "db-outage-1",
    }
    assert response.headers["X-Correlation-ID"] == "db-outage-1"
    log_payload = json.loads(caplog.records[-1].message)
    assert log_payload == {
        "correlationId": "db-outage-1",
        "event": "unexpected_request_error",
        "method": "GET",
        "release": "0.1.0",
        "routeTemplate": "/api/v1/admin/pilot-summary",
        "status": 500,
        "failureState": "not_started",
        "deliveryState": "complete",
        "responseStatus": 500,
    }
    lowered_logs = caplog.text.lower()
    for forbidden in (
        "query-secret",
        "cookie-secret",
        "header-secret",
        "password",
        "exception text",
    ):
        assert forbidden not in lowered_logs

```
