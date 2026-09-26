# T082 Package A independent implementation review

## Outcome

**FAIL.** Existing tests pass, but independent counterexamples disprove the
route and migration-verifier guarantees. Two high-severity findings remain
open.

## Findings

### T082-A-001 — High: reconstructed URL parsing bypasses the V4 boundary

`backend/app/main.py` checks `request.url.path`, while routing uses the decoded
ASGI scope path. Requests to
`/api/v1/ads/directives/id%3Fquery/v4/candidate-proposals` and the `%23fragment`
variant reached an injected authentication sentinel. Both returned
`500 / AUTH_REACHED`; the ordinary path returned the generic 404 without
invoking authentication.

An encoded `?` or `#` becomes part of the decoded identifier, then URL
reconstruction/reparsing truncates the path before `/v4/`. The router still
sees the decoded segment. Pilot requests can therefore enter authentication or
validation despite the route boundary.

Required remediation: classify the router's decoded scope path, handle
`root_path` deliberately, and add encoded-delimiter negative tests using
authentication and body-read sentinels, including preflight.

Finding family: canonicalization mismatch at the route-authority boundary and
a missing negative oracle.

### T082-A-002 — High: migration verification does not establish the executed graph

`scripts/verify_pilot_release_boundary.py` accepts the first literal metadata
assignment and calculates heads using set subtraction without detecting cycles.
An in-memory committed 0029 migration blob with an appended
`revision = "unreviewed_revision"` still passed as head `20260913_0029`, even
though Python executes the later assignment. A disconnected two-revision cycle
beside the expected head also returned the expected head.

A candidate with different executed metadata or an invalid migration graph can
therefore receive a release-boundary pass.

Required remediation: bind the complete migration inventory and blob hashes to
the approved baseline, requiring an explicit policy amendment for migrations,
or implement strict single-assignment metadata validation plus complete
acyclic-graph validation. Add candidate-content negative tests; changing only
the expected policy value is insufficient.

Finding family: release-authority/oracle mismatch.

## Verification and inspected scope

- Focused boundary plus existing V4 API tests: 34 passed.
- Current packet verifier and explicit `HEAD` verification passed for the
  baseline.
- `HEAD^` correctly failed ancestry, model-blob, and migration-head checks.
- `git diff --check` passed.
- Independent encoded-path/auth-sentinel and migration-metadata probes produced
  the counterexamples above.

The reviewer inspected all seven Package A files, the implementation artifact,
packet and bound inputs, staged/unstaged/untracked inventory, API router and V4
handlers, configuration consumers and service gates, database session/test
setup, committed migration metadata, and preserved T081 differences. No files
were edited or staged.

The documentation correctly says `HEAD` predates Package A and that verification
must run against the eventual reviewed candidate. Passing this check is
explicitly insufficient for deployment approval.

## Model routing

- Builder runtime identity: `/root`.
- Builder model: `model not exposed by runtime`.
- Builder effort: `effort not exposed`.
- Reviewer runtime identity: `/root/t082_pilot_design_adversary`.
- Reviewer model: `model not exposed by runtime`.
- Reviewer effort: `effort not exposed`.
- Routing trigger: independent implementation review of feature isolation and
  release/migration authority; GPT-6 Astra high was requested.
