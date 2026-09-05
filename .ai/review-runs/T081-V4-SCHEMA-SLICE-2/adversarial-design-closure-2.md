# Adversarial design closure review 2: T081-V4-SCHEMA-SLICE-2

- Reviewer: `/root/v4_schema_adversary`
- Builder: `/root/v4_schema_builder`
- Stage: targeted design closure re-review
- Outcome: **PASS**
- Scope fingerprint: `00f17d89814ff5fe8340479fa2b3d1857b153b2f9e5cf7da91e1d78ab054d9c0`
- Packet SHA-256: `6ce9a458dd5c1d9eebbb32df9b86e87bfcc6f3b085c19b6dfe776b144a9a563f`
- Packet verification: **1 passed out of 1**; **22 review inputs out of 22** are bound
- Finding gate: **10 closed out of 10**; **0 open blockers**; **0 open high findings**

## Targeted closure

### T081-V4-S2-DA-002 — closed

The design now defines all five hash domains as displayed ASCII/UTF-8 followed
by exactly one NUL byte and supplies complete normative hex. Independent
decoding verified **5 exact separators out of 5**. The proposal root fixes
`schemaVersion: "ad_extraction_v4"`; the evidence, candidate-event,
submission, and submission-relationship envelopes each have an exact fixed
version literal and closed field set. Positive and negative byte vectors and
Python/PostgreSQL digest parity remain mandatory implementation evidence.

### T081-V4-S2-DA-006 — closed

The canonical root now contains `officialDocuments`, a uniquely keyed and
typed namespace distinct from supporting `incorporatedDocuments`. Each entry
binds an `ad_rule|official_correction` role to a same-directive
`ad_publications` source document, retained content hash, and admitted
same-document fragment evidence. Both authoritative-correction references
resolve exactly once in this namespace, with the correcting reference limited
to `official_correction`. Cross-directive, wrong-role, incorporated-document,
hash, and evidence mismatches are required negative cases.

## Regression check

The eight previously closed invariants remain specified: raw-byte parsing;
singleton evidence admission and lifecycle locking; principal-scoped
idempotency and lock order; submission-scoped correction edges; honest
source-backed calibration gating; incorporated-document unknown-only behavior;
authorization provenance; and current packet/predecessor binding. The five
source-complete calibration fixtures remain honestly **0 passed out of 5; 5
unexecuted** and are a mandatory implementation-review gate, not design proof.

## Gate disposition

The slice-2 design gate passes. Implementation may begin within the bounded
storage-only candidate scope. This review did not run runtime implementation
tests and did not change product code.
