# Package A remediation 2: complete migration authority

## Invariant and scope

`T082-A-002` is a release-authority/oracle gap. A candidate can pass only when
its complete repository migration authority inventory and bytes equal the
reviewed target, its entire revision graph is valid, and its separately bound
head/model/exclusion checks pass. This remediation closes that family together;
it does not change the already-closed route behavior.

Changed files are the release verifier, its JSON policy and operator document,
the focused boundary tests, this artifact, and the T082 findings ledger.
No T081 file, model source, migration source, Git index/commit, or cloud resource
was edited by this builder.

## Authority and provenance

The policy now binds exactly 44 files: every committed file beneath
`backend/app/db/migrations/` (including 29 revisions, three executable SQL
sidecars, environment, template, README, and placeholder), `backend/alembic.ini`,
and the complete repository import closure executed by `env.py`:
`app/core/config.py`, `app/db/base.py`, `app/models/core.py`, and four package
initializers. This closure was traced through the committed environment,
revision imports/read calls, configuration loader, and model imports. The
directory inventory deliberately has no extension filter, so new SQL, JSON,
templates, configuration, bytecode, or unknown sidecars require review.

All hashes are read from baseline commit
`19fe8e2e170687ed65deed78cb1af99d60f601e9` except the exact Package A target
configuration bytes, SHA-256
`482af947a0fe1cd31a9974b634435dccf7041b50903ae365e365c20507a07f0d`.
The coordinator explicitly directed this target amendment because `env.py`
imports the configuration containing the already implemented pilot gate. The
policy records the amendment; it remains subject to the independent Package A
implementation pass. It is not an exemption for arbitrary configuration drift.

New dotenv input, replacements for direct-import modules/packages, and
imported-package bytecode are also classified as authority and rejected as
unapproved additions. External Python package contents and deployment/container
execution configuration remain the later immutable-image/migration-task
boundary; no site-package dependency crawl is claimed. The operator document
states the reviewed invocation and forbids treating this source check as proof
of the packaged/runtime environment.

Git inventory uses `git ls-tree -rz --name-only`. Names remain bytes for all
authority/exclusion comparisons and blob lookup. JSON-facing names use
`surrogateescape`; ASCII-escaped JSON preserves tabs, newlines, quotes,
backslashes, UTF-8, and non-UTF-8 bytes without lossy decoding.

The graph independently requires one literal module-level assignment for each
of `revision`, `down_revision`, `branch_labels`, and `depends_on`. The approved
graph has no branch aliases or dependency edges, so non-null values fail
explicitly. Duplicate revisions/predecessors, malformed or missing
predecessors, empty predecessor sequences, cycles in any component, and
multiple roots fail. The separate expected head remains `20260913_0029`, and
`core.py` retains its separate protected-blob comparison.

## Verification

- `PYTHONPATH=backend backend/.venv/bin/python -m pytest -q backend/tests/test_pilot_release_boundary.py backend/tests/test_ad_v4_api.py`:
  **124 passed** (108 boundary cases and 16 existing V4 API cases).
- The positive mocked candidate uses real committed baseline blobs plus the
  actual Package A configuration bytes and passes all 44 authority hashes.
- Candidate-content negatives cover removal, rename, and executable byte drift
  for Alembic configuration/environment/template, all SQL sidecars, a revision,
  configuration/base/model imports, and every loaded package initializer.
- Candidate-tree additions cover revisions, SQL, JSON, unknown sidecars,
  configuration/templates, dotenv, import replacement packages/modules, and
  bytecode. Raw Git output negatives cover quotes, backslashes, tabs, newlines,
  UTF-8 and non-UTF-8 names beneath both migration authority and excluded T081
  prefixes; JSON round trips remain valid.
- Synthetic candidate revision sources exercise 16 graph/metadata corruption
  cases, retaining the disconnected-cycle and duplicate/nested-assignment
  regressions from remediation 1.
- `python3 scripts/verify_pilot_release_boundary.py --ref HEAD`: expected
  **fail**, exit 1, with exactly one error for the old committed
  `app/core/config.py`; all 43 remaining hashes, the graph/head, protected model,
  and exclusions pass. This supersedes the historical HEAD-pass evidence in
  remediation 1. The eventual reviewed candidate commit must pass before image
  construction; no candidate commit was created here.
- Changed verifier/test Python compilation: pass. `git diff --check`: pass.

Existing FastAPI/Starlette deprecation and dirty-tree ORM teardown warnings
remain; no new test failure occurred. `T082-A-002` is
`fixed_pending_verification`, not closed. Independent verification belongs to
`/root/t082_pilot_design_adversary`.

## Model routing

- Builder runtime identity: `/root/t082_package_a_migration_authority`.
- Actual builder model: `model not exposed by runtime`.
- Actual builder effort: `effort not exposed`.
- Trigger: second substantive failed review in the release-authority/oracle
  family; complete invariant remediation and focused verification. Repository
  policy requests GPT-6 Astra xhigh for this phase; the runtime does not expose
  actual model/effort metadata, so none is inferred.
- Independent reviewer assignment retained by coordinator:
  `/root/t082_pilot_design_adversary`; this builder performed no independent
  review or closure attestation.
