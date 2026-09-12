# Independent design closure review 2: T081-V4-SCHEMA-SLICE-3A

Reviewer: `/root/v4_schema_adversary`  
Builder: `/root/v4_schema_builder`  
Stage: design  
Outcome: **PASS**

## Gate result

**10 passed out of 10 finding gates.** `T081-V4-S3A-DA-004` and
`T081-V4-S3A-DA-010` are independently closed. The eight findings closed in
closure review 1 were rechecked for regression and remain closed. There are
zero open blockers and zero open or unaccepted high findings.

## Targeted closure evidence

### T081-V4-S3A-DA-004

The revised design assigns all new canonical arrays to the distinct closed
`paprnav-ad-v4-c14n-2` profile and validator 2. Every new array has a normative
set key, and the v2 proposal and audit domains are byte-exact and versioned.

The retained 2002 source expression `172A through 172H` is represented once as
a typed `series_expression`, not expanded into inferred models. The relational
`ad_v4_candidate_app_search_hint_members` row carries the branch discriminator,
exact expression text, fixed unevaluated/unsupported semantics, source-only
unknown identity provenance, canonical ordinal, and one inherited evidence
parent. Reconstruction uses the discriminator and fixed v2 branch fields; it
does not parse display text. The exact oracle is seven manufacturer groups,
19 exact model occurrences, and one series expression, with no exact `172B` or
`172H` row. The 2024 `GFC 500 and GSA 28` source display remains one
`all_members` group with two typed model members, while STC and master-drawing
assertions remain separate.

### T081-V4-S3A-DA-010

Stored proposals and every dependent audit envelope dispatch by their recorded
validator/canonicalization pair. V1 bytes and hashes remain immutable and
readable; v2 uses distinct domains, identities, and same-version reuse. The
deployment sequence installs dual database/application readers before enabling
v2 writes or the 3A materializer. Application rollback retains that dual
reader and disables feature exposure and new v2 writes.

Physical downgrade now takes `ACCESS EXCLUSIVE` on the Slice-2 proposal table
before any Slice-2 child or 3A table. Candidate creation and materialization use
the same proposal-first boundary. A writer/materializer therefore either
commits before downgrade and makes its refusal gate true, or waits without
holding a conflicting 3A lock; the prior parent/child lock inversion is gone.
Downgrade refuses any v2 proposal or dependent row even when 3A is empty, and
only the v1-only path may restore 0026 and prove downgrade/re-upgrade parity.

## Regression check

- DA-001: source occurrences remain one-to-one with identity mappings while
  evidence stays shared at its canonical parent.
- DA-002: correction-2010 remains one proposal-scoped foundation with its
  complete ordered references/evidence and append-only 3A/3B bindings.
- DA-003: validator-1 remains immutable; validator-2 encodes source uncertainty
  through the explicit unknown union.
- DA-005: source-only/no-normalized-identity origins remain explicit and
  evidence-inheriting.
- DA-006: supersession effects require proposal-successor identity equality and
  a target-local causal dependency.
- DA-007: POST and both GETs select, lock, and authorize one exact active
  platform-admin membership.
- DA-008: all 90 existing type/operator combinations remain representable but
  unevaluated.
- DA-009: no matching, normalized-token, source-spelling, or aircraft-ID index
  or released-reader claim was reintroduced.

## Verification accounting

- Incoming packet freshness: **1 passed out of 1** at fingerprint
  `1029601ac4fbf6a2aeb1289983c3f8b8d308e701fdb9924ec5e7ee0d9c5b638c`.
- Explicit bound inputs: **33 inspected out of 33**.
- Targeted finding closures: **2 passed out of 2**.
- Preserved prior finding closures: **8 passed out of 8**.
- Total design finding gate: **10 passed out of 10**.
- Retained 2002 cardinality/source-expression check: **1 passed out of 1**.
- Validator/canonicalization and rollback design check: **1 passed out of 1**.

This is a design PASS only. The five corrected validator-2 calibration
proposals and all migration/concurrency tests remain implementation gates; no
runtime success is claimed here.
