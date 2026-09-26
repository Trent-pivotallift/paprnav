# Privacy amendment design review — FAIL

## Model routing

- Design builder: `/root/t082_package_d_privacy_amendment_design`.
- Independent reviewer: `/root/t082_package_d_privacy_review_2`.
- Requested builder/reviewer route: GPT-6 Astra, xhigh.
- Actual builder/reviewer model: `model not exposed by runtime`.
- Actual effort: `effort not exposed`.
- Trigger: independent review of the architecture/oracle reassessment required
  after the third unsuccessful HTTP privacy loop.

## Outcome

FAIL. The process-start logging policy and locked-runtime approach are sound,
but implementation remains paused until cancellation ownership and disconnect
scope are explicit.

## Findings

### PRIV-001 — High — A completed request can close a successor connection

The decision requires cancellation to close the captured cycle's transport in
every state. A bounded pipelining probe showed that the completed prior
response task and an incomplete successor request can overlap on the same
transport. Capturing the old cycle does not isolate `transport.close()`; the
old task could abort the successor.

Close by defining connection ownership transfer, prohibiting completed or
non-current cycles from closing a successor transport, and retaining
overlapping-task cancellation and grouped-cancellation cases.

### PRIV-002 — Medium — Disconnect completion exceeds the mechanism

The decision promises that disconnect finishes a request, but receive/send
interception cannot terminate an application suspended at an unrelated await.
A bounded probe marked the cycle disconnected while its application task
remained pending.

Close by either defining a safe task owner that observes disconnect and
cancels the application, or narrowing the guarantee to observed
receive/send/drain states and assigning bounded shutdown of unrelated waits.
Tests must not let cleanup turn a timeout into a pass.

## Verified design elements

- `logging.raiseExceptions=False` at process start governs standard handler
  write, flush, formatter, shutdown, fallback-stderr diagnostics while healthy
  records still emit.
- Startup ownership, evidence-loss semantics, explicit-traceback/direct-stderr
  exclusions, rollback, and Package E partition are appropriate.
- The locked-image oracle and negative controls are proportionate, but the
  implementation must avoid repository-root assumptions: the backend image
  contains `/app`, not the repository's `/infra` tree.
- D005 and D006 remain preserved.

## Verification

Packet freshness passed before and after review. Reviewed packet SHA-256:
`4366a0fd73d190ce65878c6cf269ffd07e543e772abf65c1641a02dcec27dab8`.
No implementation, image build, broad suite, repository edit, staging, commit,
or cloud mutation occurred during review.
