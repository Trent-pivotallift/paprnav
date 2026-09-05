# Adversarial design closure review: T081-V4-SCHEMA-SLICE-2

- Reviewer: `/root/v4_schema_adversary`
- Builder: `/root/v4_schema_builder`
- Stage: design closure re-review
- Outcome: **FAIL**
- Packet SHA-256: `0775025d5e71b73644513ba4f978043482da905dd6839565119066a07117a714`
- Packet verification: **1 passed out of 1**; **22 review inputs out of 22** are bound
- Finding gate: **8 closed out of 10**; **2 open blockers**; **0 open high findings**

## Independently closed

`T081-V4-S2-DA-001`, `T081-V4-S2-DA-003`, `T081-V4-S2-DA-004`,
`T081-V4-S2-DA-005`, `T081-V4-S2-DA-007`, `T081-V4-S2-DA-008`,
`T081-V4-S2-DA-009`, and `T081-V4-S2-DA-010` satisfy their recorded required
closures in the current packet. In particular, the raw-byte parser boundary,
singleton admitted lifecycle and lock order, principal-scoped idempotency,
submission-scoped corrections, unknown-only incorporated-document behavior,
authorization/provenance, and packet binding are now specified. The five
source-complete calibration fixtures are honestly recorded as **0 passed out of
5; 5 unexecuted**, making their successful execution a later implementation
gate rather than falsely claimed design proof.

## Open blockers

### T081-V4-S2-DA-002 — canonical byte contract remains ambiguous

Invariant: equal accepted semantic content must produce one reproducible byte
sequence and hash in Python and PostgreSQL.

Exact evidence: `decision.md` specifies the proposal hash-domain terminator as
the literal file bytes `\\\\0`, while the evidence, event, and submission
domains use `\\0`. It also does not fix the exact values of the `version`
members included in the creation/submission canonical hash objects.

Impact: conforming implementations can hash different byte sequences for the
same accepted proposal, defeating identity, deduplication, and independent
database verification.

Required closure: define one unambiguous byte-level domain separator for every
hash, fix every canonical envelope version value, and provide matching
positive and negative canonical vectors for the implementation gate.

### T081-V4-S2-DA-006 — authoritative correction references have no closed namespace

Invariant: every canonical reference must resolve to a typed, retained object
without misclassifying regulatory evidence.

Exact evidence: `decision.md` adds `authoritativeCorrections` with
`originalDocumentRefKey` and `correctingDocumentRefKey`, but the closed schema
defines no authoritative official-document collection or key namespace. The
only predecessor `documentRefKey` namespace is `incorporatedDocuments`, which
this slice correctly restricts to unknown-only supporting-document metadata.
An official AD or correction document therefore cannot be referenced without
being falsely classified as an incorporated document.

Impact: correction provenance is non-resolvable, so a proposal could appear
internally valid while its original/correcting regulatory documents are absent
or wrongly typed.

Required closure: add a typed official-document reference collection and
referential-integrity rules, or remove/defer `authoritativeCorrections` from the
slice-2 canonical surface. Bind the resolution rule into schema validation and
calibration vectors.

## Gate disposition

Design implementation is **not authorized** while either blocker remains open.
No product code was changed and no runtime suite was run for this design-only
closure review.
