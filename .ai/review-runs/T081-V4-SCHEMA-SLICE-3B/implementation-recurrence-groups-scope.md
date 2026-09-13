# Recurrence-group implementation review scope

This is a bounded pre-persistence implementation review for
G1/G2/G3/G4/T5GI/T5GR and Q11 membership agreement. It claims the pure
construction and verified-read oracle for recurrence groups, their ordered
membership relationships, and both grouped timing roots and terms.

## Normative authority

This review is explicitly bound to
`.ai/review-runs/T081-V4-SCHEMA-SLICE-3B/normative-mapping-matrix.md`, the generated
mapping manifest, and the approved Slice 3B decision. This scope does not replace
or narrow those authorities.

## In-scope claims

- G1 is a root semantic owner keyed by exact `recurrenceGroupKey`, ordered by
  canonical group-key order, with fixed `all_active_requirements` completion
  policy, one G3 child at slot 0, one G4 child at slot 1, at least two G2
  members, and own one-or-more `recurrence_clause` evidence.
- G2 is a relationship rather than a semantic owner. It preserves exact
  same-projection Q1 target node/key, canonical member-set ordinal, generated
  identity preimage, ID, and hash.
- Q11 requirement-side presence/key and G2 group-side membership agree exactly
  in both directions. Unknown groups, unresolved members, duplicates within or
  across groups, and one-sided membership fail closed. Membership adds no
  dependency-cycle edges.
- Grouped Q1 sources have non-known inline initial timing and recurrence kind
  `none`; ungrouped requirements remain unrestricted.
- G3 and G4 each support the full known/unknown/not-applicable timing union.
  Known roots require one-or-more ordered terms; non-known roots forbid terms.
  Each timing root and term owns independent exact evidence.
- Timing terms preserve exact enum values, canonical decimal text, exact finite
  nonnegative `Decimal` representation, semantic identity, parent, and ordinal.
- Source boundaries require exact JSON dictionary/list/scalar types before
  canonicalization or discriminator/set membership. Unsupported mappings and
  unhashable timing states/logics/enums fail through controlled
  `ObligationIntegrityError` at materialize and verified-read entry points.
- D/Q/E and per-requirement timing/recurrence dependencies are fully reverified
  from trusted caller context. Verified read reconstructs and compares the
  complete G family without sorting supplied rows.
- Supplied-family verification requires exact nonnegative integer types for all
  ordinals/counts, exact booleans for Q11 and ordered-step presence, exact branch
  booleans, and exact Decimal type/representation.
- Runtime contract gates pin every G descriptor plus the exact G1 owner and G2
  relationship tables, references, children, evidence, identities, ordering,
  and cardinalities.

## Builder evidence

- Recurrence-group-focused tests: 33 passed.
- Candidate + obligation host regression: 204 passed.
- Python compilation and `git diff --check` passed.
- Positive coverage includes no groups, ungrouped requirements, multiple
  disjoint groups, canonical source reordering, all nine G3 x G4 timing union
  combinations, both owner kinds, ordered known terms, independent evidence,
  and exact G1/G3/G4/G2/evidence golden identities and hashes.
- Negative coverage includes malformed group/timing/term objects, unhashable
  state/logic/enum values, unsupported mapping types, invalid keys/policy,
  zero/one/duplicate/unresolved/overlapping membership, both Q11 mismatch
  directions, grouped inline timing/recurrence conflicts, missing/extra/reordered
  rows, target/kind/evidence/hash drift, numeric type drift, Q11 bool-to-int
  corruption, and full-family foreign restamping.

## Explicitly out of scope

- A1/A2 AMOC authority/value-assertion owners;
- correction semantic bindings;
- ORM models, migration, PostgreSQL commit-time enforcement and internal-record
  serialization, API materialization/read verification, authorization/audit,
  downgrade, calibration packets, whole-tree closure, staging, or commit.

These remain mandatory Slice 3B gates. `T081-V4-S3B-DOC-001` remains open until
the PostgreSQL canonical serializer and cross-language golden vectors pass
independent review. A pass here is not a final Slice 3B implementation pass and
must not be recorded as one.
