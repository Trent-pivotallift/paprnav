# Formal whole-family implementation closure review 1

Reviewer: Codex `/root/v4_s3b_design_adversary` (independent, read-only)

Reviewed packet SHA-256:
`59d2ac3d8bcc923eb104c1c9ac37a10b10ce5dee73bb63e61f32720ac32a0c58`

Base: `9ad410b7c4021244ac36a6fab44b1dd021f5d05c`

## Verdict

**FAIL — no blocker or HIGH remains; two MEDIUM regression-proof defects
remain.**

## Residual findings

1. `PERSIST-PREFLIGHT-005` production lock order is fixed, but the durable
   concurrency test uses `sleep(0.4)` and process liveness rather than observing
   that Alembic is actually waiting on the projection-root lock. Add a unique
   `application_name` and a `pg_stat_activity`/`pg_locks` synchronization
   barrier before probing the correction-child lock.
2. `PERSIST-IMPL-011` failure-phase labels omit the real post-event boundary.
   The flush sequence is root, semantic nodes, remaining children/corrections,
   request, event. Correct the indices, add flush 5, and assert the intended
   transient rows existed before rollback.

## Closed in this review

- `PERSIST-IMPL-007`: all four API routes map every declared SQLSTATE and
  re-raise unknown errors.
- `PERSIST-IMPL-010`: all nine GET/transition snapshots are wholly-before or
  wholly-after and read-only.
- Old-reader rollout, gate/authority, maximum decimal, V3/released snapshots,
  and all previously closed typed-owner, correction, event, anchor,
  reconstruction, calibration, and generated-contract invariants showed no
  regression.

Independent evidence included 68/68 host API tests, 36/36 fresh PostgreSQL
persistence/concurrency tests, 1/1 exact-old-reader rollout test, and 2/2
fresh five-packet calibration/snapshot tests.

No external critic, mandatory final closure, staged-state attestation,
deployment, staging, or commit is authorized by this FAIL.
