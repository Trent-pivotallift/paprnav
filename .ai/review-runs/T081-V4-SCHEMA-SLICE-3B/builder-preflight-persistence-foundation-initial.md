# Slice 3B persistence foundation — Astra builder preflight

Reviewer: `/root/v4_s3b_q7_edges_preflight` (builder-side preflight only)

Scope: unstaged ORM models, migration `20260911_0028`, migration `0027`,
generated mapping/SQL, correction readers, and PostgreSQL runtime catalog.
The reviewer was read-only and made no edits. This is not an implementation or
closure verdict.

## Findings

1. **High:** correction-binding UPDATE/DELETE lost deferred validation when the
   immutable trigger is disabled; both OLD and NEW owners must be revalidated.
2. **High:** valid 3B correction bindings are rejected by the existing Python
   and PostgreSQL 3A completeness readers.
3. **High:** the foundation lacked composite same-projection endpoint FKs and
   ORM/migration constraint parity.
4. **High:** the timing-group known branch admitted SQL NULL `logic` because a
   CHECK expression evaluating NULL passes PostgreSQL.
5. **High:** downgrade did not refuse an enabled 3B gate and used an unbounded,
   child-first lock sequence.
6. **High design hazard:** copying 0027's caller-writable temporary
   generation/validated-generation cache would let direct SQL suppress deferred
   validation. Dirty state may narrow roots but must never authorize skipping
   exact validation.
7. **Medium:** `paprnav_set_v4_feature_gate` and the capabilities response did
   not recognize Slice 3B.
8. **High:** `terminates` incorrectly required one or more termination edges,
   although the canonical schema permits an empty target list.

## Runtime evidence

- Transactional 0025→0026→0027→0028 upgrade and empty downgrade succeeded on
  PostgreSQL 16; no identifier collision surfaced.
- Enabling `materializer3b_enabled` through the administrator function failed.
- An enabled gate did not prevent downgrade in the inspected snapshot.
- A known timing row with NULL `logic` made the old CHECK evaluate NULL.
- A transaction-local reproduction showed 0027's writable validation-state
  cache can be forged to skip an otherwise failing deferred callback.
- All preflight probes were rolled back.

## Required direction

Complete physical reference integrity first; install immutable and complete
INSERT/UPDATE/DELETE trigger coverage; validate every affected OLD and NEW
root without trusting caller-writable clean state; implement one exact
`paprnav_v4_candidate_obligation_require_complete` boundary; fail when an OLD
root disappears; and test migration/catalog parity, direct-SQL corruption,
constraint timing, cache tampering, and downgrade concurrency before freezing a
review packet.
