# Timing and requirement-recurrence implementation review scope

This is a bounded pre-persistence implementation review for T1, T5I, R1, R6,
and T5R. It claims the pure construction and verified-read oracle for
requirement initial timing, inline recurrence, and their timing terms.

## In-scope claims

- T1 exists exactly once at Q1 fixed slot 3. R1 exists exactly once at Q1
  fixed slot 4. R6 exists only for interval/conditioned recurrence at R1 fixed
  slot 1.
- Timing owners preserve exact known/unknown/not-applicable unions. Known plans
  require exact logic and one or more ordered terms; non-known plans preserve
  exact reason/temporal scope and forbid terms. R6 is known-only.
- Recurrence preserves all four branches: none, interval, conditioned, and
  unknown. Required/forbidden timing and expression-root references are exact.
- Timing terms preserve metric, original canonical decimal text, arbitrary-
  precision `Decimal`, unit, comparator, anchor, ordinal, semantic identity,
  and independent term evidence. Decimal syntax and the 16,384-character bound
  are checked before persistence conversion.
- Generated descriptors, evidence policies, owner union columns,
  references/children, and physical dataclass columns are contract-bound.
- D, Q, and E dependencies are fully reverified against trusted canonical
  inputs before construction. Verified read rebuilds the complete family from
  those inputs and requires immutable-family equality.

## Builder evidence

- Timing/recurrence-focused tests: 21 passed.
- Candidate + Slice-3A applicability + obligation host regression: 149 passed.
- Positive coverage includes all timing/recurrence unions, fixed slots,
  independent evidence, all 750 metric/unit/comparator/anchor combinations,
  decimal `0`, and exact 16,384/16,385 string boundaries.
- Mutation coverage includes semantic-node loss, owner state/count drift,
  decimal text/numeric drift (including equal-valued int/float/bool and altered
  Decimal scale), recurrence-kind drift, and root restamping.

## Explicitly out of scope

- recurrence-group owners/members and their G3/G4 timing families;
- prerequisite, termination, authority, and correction-binding owners/edges;
- ORM/migration/PostgreSQL decimal conversion and commit-time validation, API,
  authorization/audit/capabilities, downgrade, whole-tree closure, staging, or
  commit.

These remain required Slice-3B gates. DOC-001 remains open until the dedicated
PostgreSQL internal-record serializer and cross-language goldens pass review.
