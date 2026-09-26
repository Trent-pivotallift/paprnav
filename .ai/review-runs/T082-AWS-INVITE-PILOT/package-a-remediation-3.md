# Package A remediation 3: sealed migration context

## Outcome and scope

Implemented the independently approved authority architecture in
`scripts/build_pilot_migration_context.py`, with matching source-verifier,
policy, documentation, and focused-test updates. `T082-A-002` is
`fixed_pending_verification`; this is builder evidence, not independent closure.
No migration/model/T081 source, cloud resource, Git index, or commit was changed.

## Implemented boundary

The builder resolves one exact commit and reads only its Git blobs/modes for
the reviewed 44 inputs. Mapping is exact: `backend/alembic.ini` becomes
`alembic.ini`; approved `backend/app/...` files become `app/...`. Arbitrary
checkout files are excluded by construction. The incomplete import-name
blacklist was removed from the source verifier, which now claims only source
inventory/hash/graph correctness.

Construction rejects missing/hash-drifted inputs, modes other than regular
`100644` blobs, unsafe/non-UTF-8 manifest paths, duplicate names/keys, reused
destinations, and symlink traversal. Exclusive descriptor-based creation writes
44 files plus a canonical manifest with source commit, source/destination paths,
Git mode, byte length, SHA-256, and deterministic manifest digest. Files are
`0444`; directories are `0555`. Verification compares every output byte and the
complete file/directory inventory to the commit/policy, rejecting added,
removed, renamed, mutable, linked, or tampered output.

The local launcher requires nonempty runtime `DATABASE_URL`, forces dotenv
off and bytecode suppression, supplies a minimal environment, and launches
`python -I -B -m alembic` from the verified context with its absolute config and
head `20260913_0029`. Credentials are absent from manifests/arguments, and child
output is suppressed because driver errors may expose URLs. The local wrapper
is not the production task entrypoint.

## Execution-backed oracle

The subprocess executes actual committed `env.py` through Alembic and actual
SQLAlchemy `engine_from_config`. Both a candidate `backend/psycopg.py` and
`backend/psycopg/__init__.py` sentinel execute under the vulnerable checkout
control. Both sealed controls load real installed `psycopg`; canonical driver,
Alembic, and SQLAlchemy origins are inside the interpreter's site-packages and
outside the context. No checkout source/editable path is on `sys.path`.

The installed local environment is under ignored `backend/.venv`; the oracle
allows only its exact canonical site-packages root there. An initial overly
broad path assertion was corrected to express that distinction. The oracle
stops after driver loading, before any database connection, verifies explicit
database selection and disabled dotenv, and leaves the read-only context
unchanged with no bytecode.

## Verification

- Focused boundary suite: **292 passed**. Existing V4 API cases: **16 passed**.
  All 308 distinct final focused cases are green in coordinator verification.
- Matrix includes reproducible double builds, randomized/known replacement
  modules, dotenv/bytecode exclusion, source/output inventory and byte
  mutations, source symlink/submodule/executable/tree modes, output symlinks and
  mode drift, unsafe paths, duplicates, and existing-destination preservation.
- Real baseline Git mode reads pass. Source verifier and context builder reject
  pre-Package-A `HEAD` solely for the intentionally target-bound config blob;
  construction creates no output. Mocked target candidates pass. Exact reviewed
  candidate-commit verification remains mandatory before image construction.
- Changed Python compilation and `git diff --check`: pass. The test finalizer
  now restores permissions on deliberately read-only temporary contexts before
  pytest teardown. Existing FastAPI, Starlette, and SQLAlchemy dependency
  warnings remain; stale cleanup warnings from the earlier interrupted run do
  not represent current test failures.

Package E must prove the immutable image/task, installed dependencies and
startup hooks, read-only mount, absent checkout/mount overrides, runtime secret,
and fresh PostgreSQL upgrade. No container isolation or migration success is
claimed here.

## Model routing

- Builder identity: `/root/t082_package_a_migration_authority`.
- Actual model: `model not exposed by runtime`; actual effort:
  `effort not exposed`.
- Requested routing: GPT-6 Astra xhigh; trigger: implementation and focused
  verification after independent approval of the architecture amendment
  required by the third repeated authority finding.
- Independent reviewer remains `/root/t082_pilot_design_adversary`; no
  independent review or closure was performed by this builder.
