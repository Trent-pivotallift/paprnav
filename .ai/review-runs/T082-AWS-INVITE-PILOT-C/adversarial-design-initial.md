# Package C design review — FAIL

Three high and two medium findings remain. Implementation is paused pending
design closure.

## Findings

### T082-C-001 — High — Privileged bootstrap reintroduces the application checkout

The decision reuses the backend application image for bootstrap. Its Dockerfile
copies the entire backend, contradicting the approved sealed-context invariant.
Running a sealed migration child does not isolate its credential-bearing
bootstrap parent.

Required closure: specify a dedicated, digest-pinned migration/bootstrap image
containing only reviewed context files and pinned dependencies. Explicitly
review any bootstrap extension to Package A's manifest. Prove the entire
credential-holding execution path excludes application checkout files, mounts,
and import overrides.

### T082-C-002 — High — First-admin authority is weaker than the approved boundary and lacks concurrency semantics

The decision permits bootstrap whenever no active administrator exists, while
the parent permits it only on an empty deployment. Revoking a previous
administrator would reopen the proposed guard. Concurrent bootstrap commands
also lack a serialized check/create transaction.

Required closure: resolve the inherited wording explicitly; enforce
first-use-only eligibility under a database lock, with user, organization,
membership, and audit creation atomic. Test concurrent distinct identities, a
populated deployment, revoked prior administrators, and transaction failure.

### T082-C-003 — High — IAM prerequisite omits actual resources and updater authority

The proposed amendment covers only ACM/WAF/Route53/service-linked-role
permissions. Existing secret permissions match `secret:paprnav-*`, while
Terraform creates `/paprnav/pilot/...` secrets. RDS-managed master secrets need
additional prerequisites. The documented bootstrap identity policy grants only
`AssumeRole`, not direct policy updates.

Required closure: provide an action/resource matrix covering application,
invitation, and RDS-managed secret resources, keeping execution-role and
task-role authority separate. Identify an authorized policy-updater principal
or an explicit operator-admin prerequisite.

### T082-C-004 — Medium — Runtime grants do not exclude migration control state

The decision specifies broad DML/default privileges without defining the
creating role or object scope. Blanket defaults could grant DML on
`alembic_version`, contradicting the runtime migration-control negative.

Required disposition: define creating role/schema and runtime grants
explicitly, exclude migration-control tables, verify after migration, and
specify recovery if password rotation succeeds before secret publication.

### T082-C-005 — Medium — WAF design lacks an upload-compatible body policy

Managed common protections were selected without upload exceptions. Existing
multipart uploads accept up to 100 MiB while the standard managed rule group's
body-size rule is much smaller.

Required disposition: define narrowly scoped upload-compatible rule overrides
and oversize handling while preserving auth rate limits; add representative
multipart acceptance evidence.

## Verification and inspected scope

Packet SHA-256 matched
`c50ffa46dfcad64d0dc02508b6640f76a8d7fbe28ec79367d7f315a1076691b9`;
packet verification passed with scope fingerprint
`1a5eeb66b1def109c7fa804a478c75920ca5a2a83fb29df7e4da25bfdf20b8ca`.

The reviewer inspected the decision/preflight, inherited Package A/B evidence,
sealed-context architecture, Terraform, IAM/bootstrap documentation,
Docker/build inputs, frontend configuration, migration environment, identity
model, upload consumers, and all dirty-tree partitions. No file was staged and
no AWS resource changed.

Zero service counts, disabled workers, immutable references, security-group
separation, and durable-resource rollback protections remain appropriate.
Missing operator inputs and denied inventories permit provisional planning
only, not an execution-ready refreshed plan.

- Reviewer: `/root/t082_pilot_design_adversary`
- Requested routing: GPT-6 Astra xhigh
- Actual model: `model not exposed by runtime`
- Actual effort: `effort not exposed`

