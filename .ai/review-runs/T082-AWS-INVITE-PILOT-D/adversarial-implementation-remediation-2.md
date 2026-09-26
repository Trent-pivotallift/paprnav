# Package D remediation 2 review — FAIL

## Model routing

- Builder runtime identity: `/root/t082_package_d_privacy_remediation_2`.
- Reviewer runtime identity: `/root/t082_package_d_privacy_review_2`.
- Requested builder route: GPT-6 Astra, xhigh.
- Requested reviewer route: GPT-6 Astra, xhigh.
- Actual builder/reviewer model: `model not exposed by runtime`.
- Actual effort: `effort not exposed`.
- Trigger: repeated high-severity HTTP logging/privacy findings and review of
  the full application/server delivery boundary.

## Outcome

FAIL. T082-D-004 and T082-D-007 have strong implementation evidence for the
tested runtime, and T082-D-005/D-006 remain resolved. T082-D-008 and
T082-D-009 prevent complete production privacy closure. This is the third
unsuccessful privacy loop, so implementation must pause for an independently
reviewed invariant, architecture, and oracle reassessment.

## Findings

### T082-D-008 — High — Logging-sink failures disclose exception text

The middleware catches exceptions raised out of `logger.error()`, but standard
logging handlers normally catch their own sink failures and invoke
`handleError()`. With the effective fallback stderr handler and
`logging.raiseExceptions=True`, an injected sink `OSError` printed its secret
sentinel and traceback to stderr. The original application exception remained
private, but the claimed sink-failure containment is false.

Close only after defining the production logging ownership boundary, suppressing
or sanitizing handler-internal diagnostics, and retaining an effective
production-configuration sink-failure oracle.

### T082-D-009 — Medium — Locked Uvicorn version is not the tested runtime

`backend/requirements.lock` pins Uvicorn 0.53.0, while the current virtual
environment imports 0.52.1. No compatibility defect was demonstrated, but the
retained oracle does not assert version agreement and the handoff's installed
pinned-runtime claim is unsupported.

Close by running the focused protocol contract against the locked version and
making version agreement an explicit deterministic gate.

## Prior finding dispositions

- T082-D-004: tested uncertain-send and recovery states pass, including real
  upload and page-image streams; complete privacy closure remains dependent on
  D008/D009.
- T082-D-007: the Docker command selects the custom protocol and disables raw
  access logging, and ECS has no command override; production closure remains
  dependent on D009.
- T082-D-005 and T082-D-006 remain independently closed; relevant source and
  test hashes match remediation 1.

## Verification performed

- Packet freshness passed before and after review; reviewed packet SHA-256 was
  `7abd95fa793b6b11d77f8da08bf71d6e64fab7e013482a53a0b435b182fa7ae9`.
- Focused HTTP/privacy selection: 40 passed, 5 deselected.
- Independent keep-alive/pipelining probe produced two valid responses with
  distinct correlation contexts and no private log fields.
- A production-style logging sink counterexample reproduced D008.
- Runtime/lock comparison reproduced D009.
- Cancellation under paused output required a second cancellation to complete;
  no new regression was classified because the inspected stock server has
  related recovery behavior. The amended oracle must retain backpressure and
  shutdown evidence.

## Required architecture pause

Before more implementation, define and independently approve:

1. which layer owns logging-handler failures and stderr diagnostics in the
   production process;
2. how production logging configuration prevents handler-internal traceback
   disclosure without hiding ordinary operational failures;
3. how the protocol adapter is tested against the exact locked server version;
4. how backpressure, cancellation, and shutdown are represented in the bounded
   lifecycle oracle; and
5. which guarantees remain Package E live-deployment evidence.

No repository file, review ledger, AWS resource, provider, migration, or T081
artifact was edited by the reviewer.
