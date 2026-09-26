# Package A architecture amendment: sealed migration execution context

## Why implementation is paused

`T082-A-002` failed three implementation reviews in the same
release-authority/oracle family. The missing invariant is broader than a list
of known imports:

> Code running with migration credentials may execute repository bytes only
> from a sealed, reviewed migration context. No other file from the application
> checkout may be present on its import path or in its filesystem view.

Enumerating names such as `sqlalchemy`, `alembic`, and `psycopg` cannot prove
that invariant because dependencies may add or change transitive imports. No
further implementation is authorized until this amendment is independently
approved.

## Decision

Build and run migrations from a separate sealed context assembled from an
explicit manifest at the exact reviewed Git commit. The context contains only:

- `backend/alembic.ini` with the reviewed `script_location` and
  `prepend_sys_path` behavior;
- every reviewed file beneath `backend/app/db/migrations/`;
- the minimal repository package/import closure required by `env.py`:
  `app/core/config.py`, `app/db/base.py`, `app/models/core.py`, and the required
  package initializers; and
- a generated manifest recording source commit, path, Git mode, byte length,
  and SHA-256 for every context file.

The builder reads blobs from the named Git commit, never from the working tree.
It rejects symlinks, submodules, non-regular modes, duplicate or non-UTF-8
manifest paths, path traversal, and any source/manifest mismatch. The output
directory is newly created and must contain exactly the manifest plus the
listed files. Arbitrary repository files—including `backend/psycopg.py`, any
future driver name, `.env`, bytecode, tests, scripts, and T081/0030 artifacts—
are excluded by construction rather than discovered by import-name rules.

The migration task receives only this context and installed third-party
packages. It runs from the sealed directory with `PAPRNAV_DISABLE_DOTENV=1`, a
database URL supplied at runtime from the separately scoped migration secret,
and an explicit command equivalent to:

```text
python -I -m alembic -c /migration/alembic.ini upgrade 20260913_0029
```

Alembic may add the sealed directory to `sys.path`; that directory cannot
contain an unapproved top-level replacement module. The application checkout
is not copied or mounted into the migration task. The image records the source
commit and context-manifest digest as labels and uses an immutable image digest.

## Boundary by package

Package A resumes only to implement the deterministic context builder,
manifest verifier, and local execution-backed oracle. Package A does not push
an image, contact AWS, or run an AWS migration. Its implementation review must
bind the builder, manifest, policy, tests, and current Package A route gate.

The later AWS/image package must:

- create a dedicated migration image/stage containing the sealed context and
  pinned installed dependencies, but no application checkout;
- prove the image file inventory and labels match the reviewed context manifest
  and exact Git commit;
- run the image by immutable digest with the migration-only database identity;
- prove a fresh disposable PostgreSQL upgrade to `20260913_0029`; and
- record the image digest before any AWS database migration is authorized.

External Python package bytes are owned by that immutable-image boundary, not
by Package A's repository manifest. The source verifier must stop claiming it
proves the complete transitive import closure; it proves the inputs to the
sealed context and the migration graph. The context and later image digest
together prove the execution boundary.

## Shared oracle and exit evidence

One execution-backed oracle governs construction and review:

1. Build twice from the same explicit commit; manifests and file bytes are
   identical.
2. Add arbitrary top-level replacement modules/packages to a synthetic
   candidate tree, including randomized names and known DBAPI/import names.
   Build the context and prove none appears in its inventory or import path.
3. Run a subprocess from the sealed context with the reviewed Alembic config.
   Instrument imports and `engine_from_config`; prove repository sentinels never
   execute and DBAPI/Alembic/SQLAlchemy resolve outside the context.
4. Mutate, remove, rename, add, symlink, or mode-change every manifest class;
   construction or verification fails closed.
5. Prove the migration graph/head, SQL sidecar hashes, protected model hash,
   T081/0030 exclusions, and V4 route/startup gates still pass their existing
   focused oracles.
6. Before image construction, run the release verifier and context builder
   against the exact reviewed candidate commit; a pre-Package-A `HEAD` is not
   release evidence.

The oracle remains bounded by the number of manifest files and mutation
classes. It does not generate combinatorial database rows or broad application
test matrices.

## Alternatives rejected

- **Continue adding import names:** rejected because every new transitive import
  creates another bypass and another review loop.
- **Bind the full repository only:** exact commit identity is necessary release
  provenance, but copying the full checkout still places unrelated modules on
  the privileged import path and creates avoidable review/rework coupling.
- **Install the full application package and remove repository paths:** viable
  later, but the repository has no closed packaging contract today and the full
  application is a larger migration credential surface than the minimal sealed
  context.
- **Rely on `python -I` alone:** insufficient because Alembic's reviewed config
  deliberately adds its script root to `sys.path`; isolation must also control
  the directory contents.

## Failure, rollback, and residual limits

Any manifest, context, commit, graph, image-label, or digest mismatch blocks the
migration task. Rollback selects the prior reviewed image digest only when its
schema compatibility is explicit; this design does not authorize automatic
downgrade. A failed migration leaves ECS service counts at zero until the
operator dispositions it.

This boundary does not authenticate repository reviewers, secure third-party
package provenance by itself, authorize an AWS apply, or close T081. Those
remain review-process and later image/deployment gates.

## Model routing

- Architecture author: `/root`.
- Actual model: `model not exposed by runtime`.
- Actual effort: `effort not exposed`.
- Requested routing: GPT-6 Astra xhigh after the third unsuccessful invariant
  loop. A new Astra subagent turn was attempted but rejected by the runtime
  thread limit, so no unavailable model is claimed.
- Required reviewer: independent `/root/t082_pilot_design_adversary`, GPT-6
  Astra xhigh requested; implementation remains paused until a pass is recorded.
