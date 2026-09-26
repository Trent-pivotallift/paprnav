# Package A remediation 1

## Finding classes

The first implementation review failed on two high-severity missing-oracle
classes, not isolated counterexamples:

- `T082-A-001`: canonicalization mismatch at the route-authority boundary.
- `T082-A-002`: release-authority and migration-oracle mismatch.

## Remediation

The route boundary now classifies `starlette._utils.get_route_path(scope)`, the
same decoded ASGI path authority used by the Starlette router. This avoids
reconstructing and reparsing a URL after percent decoding and deliberately
accounts for mounted `root_path`. The boundary remains outside CORS.

The negative oracle now covers both `%3F` and `%23` path delimiters, CORS
preflight, an injected authentication sentinel, and a raw ASGI request whose
receive callable fails if any code reads the body. A mounted decoded path is
included.

The release verifier now binds the exact 29-file migration source inventory and
SHA-256 of every approved migration blob. Any source addition, removal, rename,
or byte change requires a reviewed policy amendment. Independently of the hash
binding, metadata must have exactly one module-scope assignment, predecessor
references must exist, duplicate predecessors are rejected, and a full graph
walk rejects cycles even when they are disconnected from the expected head.

The negative oracle modifies the actual 0029 candidate content in memory by
appending a second executed revision assignment and proves both blob drift and
duplicate metadata fail. A separate synthetic disconnected cycle must also
fail.

## Verification

- Package A boundary tests: 23 passed.
- Existing V4 API tests: 16 passed.
- Explicit `HEAD` verifier: pass, 29 migration blobs matched, head
  `20260913_0029`, protected model blob matched, no excluded committed paths.
- Changed Python compilation: pass.
- `git diff --check`: pass.

The verifier still evaluates the pre-Package-A `HEAD` until the task's commit
gate opens. It must be rerun against the eventual reviewed candidate commit;
the documentation retains that limitation.

## Model routing

- Remediation builder runtime identity: `/root`.
- Builder model: `model not exposed by runtime`.
- Builder effort: `effort not exposed`.
- Trigger: first substantive implementation-review failure; reasoning was
  escalated and each finding was reframed as an invariant/oracle class.
- Required verifier: `/root/t082_pilot_design_adversary`, requested GPT-6 Astra
  high, read-only. Actual model and effort must be recorded as exposed by that
  runtime.
