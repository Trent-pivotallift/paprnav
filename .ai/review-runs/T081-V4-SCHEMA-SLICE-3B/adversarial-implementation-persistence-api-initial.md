# Formal whole-family implementation review — initial

Reviewer: Codex `/root/v4_s3b_design_adversary` (independent, read-only)

Reviewed packet SHA-256:
`2a898fc45c640c2d38e18887163e4214ba16cedfeb0f34bc6481f1149cf843ad`

Base: `9ad410b7c4021244ac36a6fab44b1dd021f5d05c`

## Verdict

**FAIL — two HIGH and two MEDIUM findings remain open.**

The reviewer independently reverified packet currentness and reproduced the
builder gates. The xmin/cmin sequence-zero validation anchor rejected missing,
deleted, forged/restamped, post-anchor, and immediate-to-deferred hostile
writes and was accepted as fail-closed.

## Open findings

1. **HIGH — `PERSIST-PREFLIGHT-005`: downgrade lock order remains unsafe.**
   Migration `0028` lexically sorts the affected tables, placing the projection
   root at position 14. A rolled-back two-connection probe reproduced `40P01`
   between a root-first writer and the downgrade's exact `ACCESS EXCLUSIVE`
   order. Replace lexical sorting with an explicit parent-before-child order
   and add a durable contention test proving bounded no-DDL refusal without a
   deadlock victim.
2. **HIGH — `PERSIST-IMPL-007`: expected database failures escape GET and
   lock-timeout boundaries.** POST does not map `55P03`, and detail,
   reconstruction, and list GET routes do not catch mapped `DBAPIError`
   classes. One bounded boundary must map `P0001`, `23*`, `40P01`, `40001`,
   `57014`, and `55P03` on all four routes while unknown errors remain visible.
3. **MEDIUM — `PERSIST-IMPL-010`: required GET snapshot interleavings lack
   durable proof.** Add forced two-connection detail/list/reconstruction races
   across evidence invalidation, correction/replacement, and parent Slice-3A
   stale transitions, plus a read-only write rejection.
4. **MEDIUM — `PERSIST-IMPL-011`: the approved final regression matrix is
   incomplete.** Add the upgraded-empty old-reader/no-old-binary boundary,
   complete application/database gate and authorization combinations, phase
   failure injection, the PostgreSQL 16,384-character decimal boundary, and
   V3/released endpoint/matching/coverage/recurrence/due-state before/after
   calibration snapshots.

## Independently satisfied dispositions

- `PERSIST-PREFLIGHT-001`, `002`, `003`, `004`, `006`, `007`, and `008`;
- `PERSIST-IMPL-001` through `006`, plus `008` and `009`;
- `CAL-IMPL-001`, `CAL-TEST-001`, and `CAL-IMPL-003`.

`CAL-IMPL-002` remains correctly rejected because the authoritative canonical
proposal resolved the symptom without weakening canonical ordering.

## Independent evidence

- non-PostgreSQL V4 host set: 382/382 passed, one PostgreSQL-only skip;
- fresh PostgreSQL serializer plus persistence: 50/50 passed;
- fresh Slice-3A PostgreSQL: 24/24 passed;
- fresh parent candidate PostgreSQL: 5/5 passed;
- all five calibration packets round-tripped exactly on fresh PostgreSQL;
- fresh 0001→0028 and empty 0028→0027→0028 passed;
- enabled and occupied downgrade refusals preserved head/data; and
- generated mapping digest remained
  `e229c6008f323cb6622e96b286b6ecb93ec7f2be47a5e4dd48bec294af51465d`.

No external critic, closure review, staged-state attestation, production
deployment, staging, or commit is authorized by this FAIL.
