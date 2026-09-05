# Independent implementation review: T081-V4-SCHEMA-SLICE-2

- Reviewer: `/root/v4_schema_adversary`
- Builder: `/root/v4_schema_builder`
- Stage: implementation
- Outcome: **FAIL**
- Scope fingerprint: `c375bf76a73ec0485f0a36048d8ab283b82b8e90240f72842724390d1a41d5d2`
- Packet SHA-256: `f50ec9dafe5282e2e683c80c70ffd41b06abec2a0dec151de51ea89a0032ab43`
- Packet verification: **1 passed out of 1**; **17 scoped files** and **45 review inputs** are bound
- Implementation finding gate: **0 closed out of 9**; **5 open blockers**; **4 open high findings**

## Findings by severity

### Blockers

1. `T081-V4-S2-IA-001` — the pure semantic validator is incomplete. Live
   counterexamples accepted a dangling `scope_ref` and duplicate `scopeKey`;
   most typed references, uniqueness rules, cycles, recurrence rules, and
   correcting-document evidence rules are absent.
2. `T081-V4-S2-IA-002` — canonicalization is not schema-aware. Reordering the
   accepted 2002 `searchHint.models` set changed canonical bytes; ranges and
   supersession relations are also outside the runtime sort registry.
3. `T081-V4-S2-IA-003` — PostgreSQL hashes caller-supplied byte blobs without
   binding their complete envelope contents to relational binding,
   submission, relationship, and event columns. Recomputed but contradictory
   direct-SQL records can satisfy the current triggers.
4. `T081-V4-S2-IA-004` — the five calibration packets do not pass through
   Slice-1 admission or V4 persistence. Tests substitute `exactTextHash` for a
   real fragment hash, and the five negative cases exercise only bespoke
   fixture assertions rather than the validator/store boundary.
5. `T081-V4-S2-IA-005` — the mandatory PostgreSQL integrity/concurrency gate is
   unexecuted and the sole draft test does not cover the reviewed matrix.

### High

1. `T081-V4-S2-IA-006` — fragment locks follow caller JSON object order rather
   than lexicographic fragment ID, leaving a reversed-order deadlock path.
2. `T081-V4-S2-IA-007` — audit APIs expose only the newest submission ID and
   omit authorization provenance, correction relationships, and earlier
   deduplicated-content origins.
3. `T081-V4-S2-IA-008` — streaming, depth, node, edge, array, model, and other
   reviewed resource limits are missing; `request.body()` buffers before the
   final byte-length check.
4. `T081-V4-S2-IA-009` — `relationship_hash` is globally unique although its
   envelope omits submission identity, so a second legitimate origin with the
   same correction edge fails instead of preserving provenance.

## Independent verification

- Current review packet: **1 passed out of 1**.
- Bounded host candidate/API/calibration suite: **30 passed out of 30** with
  one Starlette deprecation warning.
- PostgreSQL suite on this reviewer host: **0 passed out of 1; 1 skipped**
  because `PAPRNAV_TEST_POSTGRES_URL` was absent.
- Executable adversarial counterexamples: **3 defects reproduced out of 3**:
  dangling scope reference accepted, duplicate scope key accepted, and
  schema-declared model-set reordering changed canonical bytes.
- Source files/PDF hashes and manifest offsets were inspected. The current
  calibration result is not counted as five source-admitted/persisted packet
  passes because the test never creates Slice-1 retained evidence rows.

## Confirmed limitation, not a finding

Candidate-only isolation remains intact in the inspected tree: repository
search found no released-catalog, matching, compliance, due-state, cache, or
V3 reader consuming the new tables, and the focused V3 response-isolation test
passed.

## Gate disposition

Implementation review **FAILS**. Do not advance to `implementation_reviewed`
or closure until all blockers are independently closed and the PostgreSQL and
source-admitted calibration gates have current evidence. No product code was
changed during this review.
