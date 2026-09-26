# Package D remediation 1 review — FAIL

## Model routing

- Builder runtime identity: `/root/t082_package_d_remediation_1`.
- Reviewer runtime identity: `/root/t082_package_d_implementation_review`.
- Requested builder route: GPT-5.6 Sol, xhigh.
- Requested reviewer route: GPT-6 Astra, high.
- Actual builder/reviewer model: `model not exposed by runtime`.
- Actual effort: `effort not exposed`.
- Trigger: first-failure remediation review of the complete Package D family,
  including privacy, transaction evidence, and cost-display semantics.

## Outcome

FAIL. T082-D-005 and T082-D-006 are independently verified resolved.
T082-D-004 remains open, and T082-D-007 records a second high-severity gap in
the same HTTP logging/privacy invariant family.

## Finding dispositions

### T082-D-004 — High — remains open

Application and generator exceptions are now contained for the normal,
pre-start, and post-start upload and page-image stream paths. Correlation,
actor, organization, and aircraft context are retained. A bounded disconnect
counterexample still causes an unsafe recovery sequence: when the first
`send()` raises a secret-bearing `OSError`, the middleware attempts a second
`http.response.start` and allows the transport exception to escape to the
server's default traceback path.

Close by treating send completion as uncertain once delivery is attempted,
containing recovery-send failures, and retaining a complete normal,
pre-start, post-start, and transport-failure lifecycle matrix.

### T082-D-005 — Medium — verified resolved

Executable tests now cover all six achievement families, extracted-entry
actor/retry/actorless/rollback behavior, and rejected and conflicting AD
decisions. The retry query de-duplicates ORM results before enforcing its
single-entry invariant. The remediation handoff supersedes the original
coverage overstatement.

### T082-D-006 — Medium — verified resolved

The wired administrator component renders lifecycle, pricing, recorded
historical attribution, billing, completed-priced estimate, unknown amount,
and reconciliation categories, with explicit partial recorded-run labels.
Focused rendering evidence passed.

### T082-D-007 — High — Default access logging exposes query strings

The backend image starts Uvicorn with default access logging enabled. The
application sanitizer does not govern `uvicorn.access`. An actual Uvicorn
request-cycle counterexample sent an erroring admin-summary request with a
secret query parameter: the application record was sanitized, but the access
record retained the query secret.

Close by disabling raw access logging or replacing it with a content-free
route-template logger, and test the effective server configuration for success
and error responses.

## Verification performed

- Packet freshness passed before and after review.
- Package D backend oracle: 7 passed.
- Frontend pilot tests: 3 passed; TypeScript check passed.
- Four parametrized release-boundary cases passed.
- Read-only normal, early, late, and disconnect ASGI matrix reproduced the
  remaining D004 gap.
- Real page-image early/late streaming cases passed.
- An installed-Uvicorn request-cycle probe reproduced D007.
- The index remained empty; no repository or cloud mutation occurred during
  review.

## Escalation and residual limitations

This is the second unsuccessful implementation review in the same privacy
family. The next pass must restate and close the complete HTTP logging
invariant across application failure, delivery state, disconnect recovery,
Uvicorn error logging, and access logging rather than adding another isolated
counterexample fix. Recorded-run cost limitations and live CloudWatch, Budget,
provider, and worker evidence remain Package E gates.
