# Independent design closure review: T081-V4-SCHEMA-SLICE-3A

Reviewer: `/root/v4_schema_adversary`  
Builder: `/root/v4_schema_builder`  
Stage: design  
Outcome: **FAIL**  
Reviewed packet fingerprint: `7509d50e2d6787da6ac86f4398ffa879063d968de3972bb294c4bb8d2902f4d2`

## Gate result

**8 passed out of 10 finding gates.** Eight original findings are closed.
`T081-V4-S3A-DA-004` remains an open blocker, and new blocker
`T081-V4-S3A-DA-010` records the validator/canonicalization rollback defect.
Slice 3A remains framed and implementation is not authorized.

## Closed findings

- `DA-001`: exact designation occurrences now own distinct mapping rows while
  sharing one evidence parent; the 10-scope calibration cardinality is
  representable.
- `DA-002`: one proposal-scoped correction foundation owns the full ordered
  reference set and evidence once; Slice 3B can append only its semantic
  binding without mutating or duplicating correction authority.
- `DA-003`: the corrected 1998 candidate uses explicit unknown and leaves the
  validator-1 candidate immutable/auditable.
- `DA-005`: source-only and no-normalized-identity origins are explicit,
  unknown, and evidence-inheriting.
- `DA-006`: supersession signals require successor/candidate AD equality and
  name an exact target-local dependency cause.
- `DA-007`: POST and both GETs select, lock, and validate the exact acting
  membership.
- `DA-008`: all 90 current type/operator pairs remain representable but
  unevaluated; no compatibility semantics are invented.
- `DA-009`: unusable matching indexes and readiness claims were removed.

## Open blockers

### `T081-V4-S3A-DA-004`

The typed group direction is sound, but its concrete 2002 plan is not
source-faithful and its canonical version is unsafe. The retained source says
`172A through 172H`; the proposed 27-model total expands that expression into
eight exact models despite the explicit unsupported-series/no-inference rule.
It must remain one source series expression with unknown evaluation unless a
separately reviewed series grammar establishes membership. In addition, the
new group/member arrays cannot remain under `paprnav-ad-v4-c14n-1`: the closed
Slice-2 contract requires a new canonicalization version whenever an array is
added.

### `T081-V4-S3A-DA-010`

Validator-2 rows live in existing Slice-2 tables, but the downgrade emptiness
gate covers only Slice-3A tables. An unmaterialized validator-2 candidate can
therefore survive a physical downgrade to migration 0026, whose trigger and
application support only validator-1. The design must define versioned hash
dispatch and make both application and physical rollback preserve or refuse
all newer immutable rows.

## Verification summary

- Incoming packet freshness: **1 passed out of 1** at fingerprint `7509d50e...`.
- Explicit packet inputs: **32 inspected out of 32**.
- Original finding closures: **8 passed out of 9**; DA-004 failed.
- Total finding gate after the newly identified rollback defect: **8 passed
  out of 10**.
- Model occurrence cardinality: **10 representable out of 10 listed scopes**
  using distinct occurrence nodes and shared evidence parents.
- Correction-2010 reconstruction: **1 passed out of 1** shared roots; 2 refs,
  2 evidence links once, 1 current 3A binding, and 1 reserved 3B binding.
- Retained 2002 source check: **1 failed out of 1** proposed exact-model
  expansions because `172A through 172H` is a source expression, not eight
  reviewed identities.
- Current product-code isolation remains intact: no Slice-3A implementation or
  released-reader import exists yet.

A refreshed decision and independent closure review are required before a
design PASS may be recorded.
