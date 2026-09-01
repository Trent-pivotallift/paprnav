# T081 design closure review 1

Reviewer: `/root/t081_design_closure`

Outcome: FAIL

The reviewer accepted the revised fail-closed design for T081-DA-1, DA-3,
DA-5, DA-6, DA-7, DA-8, DA-9, and DA-10, pending implementation. Three design
blockers remained:

## T081-DC-1 — Blocker — `0022` downgrade does not reconstruct revision `0021`

Revision `0021` owns a five-column constraint including
`applicability_group_key`; therefore `0022 -> 0021` must restore that exact
constraint. Only `0021 -> 0020` restores the legacy four-column constraint.
Downgrade preflight must occur before destructive DDL and be PostgreSQL-tested.

## T081-DC-2 — Blocker — AMOC repair lacks an unambiguous affected-row rule

Migration `0023` did not record touched IDs, so a later missing-key predicate
cannot find the altered rows and an empty-list predicate could include a
legitimate human decision. The design must choose a conservative deterministic
deployment cohort, preserve both pre-repair/synthetic hashes and output, reopen
every ambiguous decision, and prove no ambiguous approved row survives.

## T081-DC-3 — Blocker — Applicability lacks exact signed-extraction identity

`ADTargetApplicability` is keyed by directive/target/publication/basis/group and
can be overwritten by a later extraction. The design must add immutable source
extraction/materialization identity, quarantine ambiguous legacy rows, and make
all consumers join through that exact signed identity.

**DESIGN OUTCOME: FAIL**
