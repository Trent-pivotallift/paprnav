# Pilot release boundary

The invite-only AWS pilot is built from an explicit reviewed Git commit. It is
not built from the current working directory. Before packaging a candidate,
run:

```bash
python3 scripts/verify_pilot_release_boundary.py --ref <commit>
```

The verifier reads the commit tree named by `--ref`, applies
`.ai/pilot-release-boundary-v1.json`, and fails unless:

- the approved pilot baseline is an ancestor;
- the migration graph has the single reviewed head `20260913_0029`;
- the exact 44-file migration authority inventory and every SHA-256 match the
  reviewed policy, with no duplicate metadata, missing predecessor, graph cycle,
  extra root, or unsupported dependency/branch metadata;
- the reviewed `backend/app/models/core.py` blob is unchanged; and
- no T081 Slice 4B or unreviewed 0030 artifact is present.

The authority inventory includes every committed file under
`backend/app/db/migrations/`, regardless of extension: all 29 revision sources,
all three SQL sidecars executed by 0028/0029, `env.py`, `script.py.mako`, and the
directory's remaining files. It also includes `backend/alembic.ini` and the
minimal repository support modules used by `env.py`: `app/core/config.py`,
`app/db/base.py`, `app/models/core.py`, and their package `__init__.py` files.
The separate expected-head and protected-model checks remain mandatory.

All inventory names and hashes come from baseline commit
`19fe8e2e170687ed65deed78cb1af99d60f601e9`, except the explicitly recorded
`app/core/config.py` target amendment containing the Package A V4 gates and
Package B pilot trust-boundary settings. Its exact SHA-256 is
`a9015bedd4362c5cbfc3bda6b05ccce4e92984c958b8087d4dd8d10344562cf4` and must
receive independent implementation approval. The baseline therefore fails with
exactly that configuration difference. A mocked candidate containing the
approved target bytes passes; this is not evidence that a release commit
already exists. Run the verifier on the eventual reviewed candidate commit
before image construction.

Additions, removals, renames, and content changes in these source inputs require
an explicit reviewed policy amendment. This verifier proves source inventory,
hashes, and graph correctness. A source pass does not prove import isolation
when running from the full checkout.
Git names are enumerated as raw NUL-delimited bytes, compared as bytes, and
decoded with `surrogateescape` only for ASCII-escaped JSON output. Quoted,
tab/newline, non-ASCII, and non-UTF-8 names cannot bypass the authority or T081
prefix checks.

Build the migration execution context separately:

```bash
backend/.venv/bin/python scripts/build_pilot_migration_context.py build --ref <reviewed-commit> --destination /private/tmp/paprnav-migration-<unique>
backend/.venv/bin/python scripts/build_pilot_migration_context.py verify --ref <reviewed-commit> --destination /private/tmp/paprnav-migration-<unique>
```

The destination and every ancestor must be real directories with no symlink
traversal; the destination itself must not exist. The builder resolves the ref
once, reads Git blobs and modes at that commit, validates all inputs before
creation, and maps `backend/alembic.ini` to `alembic.ini` and each approved
`backend/app/...` source to `app/...`. It copies no arbitrary checkout input,
regardless of current or future driver/import name. In particular, `.env`,
bytecode, tests, and unapproved replacement modules never enter the context.

The exact output is 44 regular files plus `migration-context.json`. Each entry
records source/destination paths, Git mode, byte length, and SHA-256. The
manifest records the exact source commit and a deterministic SHA-256 over
canonical JSON without the digest field. Source mode must be `100644`; context
files are `0444` and directories `0555`. Verification compares the manifest and
every file byte back to the reviewed commit/policy and rejects extra/missing
files or directories, symlinks, hard links, and mode drift. Unsafe, duplicate,
or non-UTF-8 manifest paths fail. A failed write leaves an incomplete directory
for inspection; it cannot be reused or pass verification.

The script's local `run` mode requires an explicit nonempty `DATABASE_URL`,
verifies the context before/after execution, forces `PAPRNAV_DISABLE_DOTENV=1`
and `PYTHONDONTWRITEBYTECODE=1`, and launches `python -I -B -m alembic` from the
context with its absolute configuration path and fixed head `20260913_0029`.
`-B` is explicit because `-I` ignores Python environment variables. Runtime
credentials are never recorded in the context/manifest or passed as command
arguments; child output is suppressed because driver errors may contain URLs.
The local wrapper needs repository access for verification and is not the
production task entrypoint.

Package A's execution oracle runs the actual committed `env.py` through Alembic
and actual SQLAlchemy `engine_from_config`, stopping after driver loading and
before any database connection. Both `psycopg.py` and `psycopg/__init__.py`
sentinels execute in the vulnerable checkout control. In the sealed control,
the real installed psycopg, Alembic, and SQLAlchemy resolve to the interpreter's
canonical site-packages, and no checkout source directory is on `sys.path`.
The local virtual environment is located beneath the repository; only its
exact installed site-packages root is allowed, never application/editable
source paths. Output remains unchanged and contains no bytecode after execution.

Package E must bind the dedicated migration image, interpreter, installed
dependencies/startup hooks, read-only context, command/environment, image labels,
and task definition to an immutable image digest. It must prove the application
checkout is absent from the task filesystem/import path and cannot reenter via
mounts or overrides, require the migration-only runtime secret, and prove a fresh
PostgreSQL upgrade. These local tests do not establish container isolation,
package provenance, database migration success, or AWS execution readiness.

`PAPRNAV_ENV=pilot` defaults the pilot-wide V4 route gate off. Startup also
fails if that gate or any narrower V4 write, projection, draft, or decision
gate is enabled. Every `/api/v1/ads/**/v4/**` request then receives a generic
404 before authentication or request-body parsing. Local and test environments
retain their existing V4 behavior unless the route gate is explicitly false.

Passing this check is necessary release evidence, not authorization to deploy.
It does not validate an image digest, modify AWS, migrate a database, or close
the preserved T081 review run. Those remain later reviewed pilot gates.
