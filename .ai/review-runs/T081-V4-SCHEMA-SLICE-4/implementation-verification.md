# T081 V4 Schema Slice 4 implementation verification

Verification date: 2026-09-13  
Builder/coordinator: `/root`  
Base commit: `4840a0b4bc5d7334ddcf51a80e39c8fa84b7b0c2`

## Static gates

- `git diff --check`: passed.
- `python3 -m py_compile` over every changed Python implementation, migration,
  and Slice-4 test module: passed.
- No files were staged or committed.

## Host API, service, reconstruction, and calibration gate

Command (from `backend`):

```text
PAPRNAV_DISABLE_DOTENV=1 PYTHONPATH=. .venv/bin/pytest -q \
  tests/test_storage.py tests/test_ad_v4_api.py tests/test_ad_v4_candidates.py \
  tests/test_ad_v4_applicability.py tests/test_ad_v4_obligations.py \
  tests/test_ad_v4_calibration.py tests/test_ad_v4_applicability_calibration.py \
  tests/test_ad_v4_obligations_calibration.py \
  tests/test_ad_v4_review_service_bounds.py tests/test_ad_v4_reviews.py
```

Result: **532 passed, 1 skipped** in 191.41 seconds. This includes the five
retained-source calibration packets through validator-2, Slice-3A, and
Slice-3B exact reconstruction. The previously reported isolated-container
page-text mismatch did not recur when the repository's exact six retained PDF
fixtures were used.

The focused review/service/storage subset also passed independently after the
final bounded-work changes: **93 passed** in 8.49 seconds.

## Fresh PostgreSQL migration and Slice-4 gate

Disposable database `paprnav_s4_closure7` was created empty and migrated
through every revision from 0001 to `20260913_0029` using the final working
tree. Migration succeeded.

Command:

```text
PAPRNAV_TEST_POSTGRES_URL=postgresql+psycopg://.../paprnav_s4_closure7 \
  PYTHONPATH=. .venv/bin/pytest -q \
  tests/test_ad_v4_review_case_migration_postgres.py \
  tests/test_ad_v4_review_lock_order_postgres.py \
  tests/test_ad_v4_review_service_postgres.py
```

Result: **86 passed** in 36.66 seconds.

This gate includes:

- every closed observation branch accepted by both SQL and Python;
- fully resealed malformed observation, digest, source-row, head, ordinal,
  cross-directive, and capacity counterexamples rejected at commit;
- cutoff source arrays accepted at 2,000 and rejected at 2,001;
- six two-administrator candidate/review interleavings covering new content and
  reuse against case creation, review request, and rejection;
- forced direct-SQL same-actor submission/review and applicability-request/review
  interleavings, proving the final inherited trigger definitions lock user
  before membership and both transactions commit without SQLSTATE `40P01`;
- phase-aware 16 MiB draft, 28 MiB requested, and 40 MiB terminal aggregate
  authoritative-byte boundaries enforced by both service preflight and
  commit-time SQL before JSON parsing;
- an exact near-ceiling PostgreSQL lifecycle that fills the draft phase to
  within 1 KiB, proves the next draft is refused, and then commits request,
  rejection, and successor creation across partial flushes;
- a combined 64 MiB evidence-text/retained-source work budget and 2,000-binding
  and lifecycle-event queue budget, including lifecycle reason bytes,
  controlled handling of individually oversized proposals, bounded local/S3
  retained-object reads, metadata-only authorship/cutoff/frozen-source queries,
  and head-only cutoff selection;
- scalar preflight of applicability/obligation projection counts, accumulated
  materialization-request/event counts, and canonical payload bytes before
  reconstruction, including populated obligation-over-count,
  applicability-parent-over-count, and applicability-parent-over-byte cases;
- exact dependency propagation from an over-budget applicability projection to
  its obligation child, which returns controlled `projection_integrity` without
  directly or indirectly selecting the parent's request payload;
- a complete service rejection lifecycle with deferred constraints forced
  immediate before commit.

## Isolated prior-slice PostgreSQL regressions

Migration tests intentionally change the schema revision, so each suite was
run against its own newly created database migrated from empty to 0029:

- candidate persistence (`paprnav_s4_final_candidate3`): **5 passed**;
- Slice-3A applicability (`paprnav_s4_final_app3`): **24 passed**;
- Slice-3B obligation persistence and serializer
  (`paprnav_s4_final_obligation3`): **68 passed**;
- Slice-3B old-reader rollout (`paprnav_s4_final_oldreader3`): **1 passed**.

Two legacy downgrade assertions were updated from old head 0028 to current
head 0029. No production behavior was weakened.

## Slice-4 downgrade/rollback gate

Disposable database `paprnav_s4_rollout4` was created empty and
migrated 0001 to 0029. The dedicated rollback module then proved:

- empty/disabled 0029 downgrades to 0028 and re-upgrades cleanly;
- each reviewer gate independently refuses downgrade without schema loss;
- immutable review occupancy refuses downgrade without row loss.

The empty-history test additionally captures both complete 0028 inherited
function definitions, upgrades, downgrades again, proves exact definition
equality, and proves the Slice-4 aggregate-byte helper is absent after each
downgrade.

Result: **4 passed** in 4.01 seconds.

## Invalid combined-run disclosure

An earlier attempt ran all PostgreSQL migration modules sequentially in one
database. Legacy tests deliberately downgraded that shared schema, cascading
into later missing-function and gate failures. That run was invalid as a test
isolation strategy. The modules were subsequently rerun on the separate fresh
databases listed above; every isolated suite passed.
