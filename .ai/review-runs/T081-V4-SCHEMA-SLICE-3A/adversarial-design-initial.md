# Independent design review: T081-V4-SCHEMA-SLICE-3A

Reviewer: `/root/v4_schema_adversary`  
Builder: `/root/v4_schema_builder`  
Stage: design  
Outcome: **FAIL**  
Reviewed packet fingerprint: `abe88e1271ad0fa8e7f2c6c36885e7853de5f333c773466c70df53c7b55ec71c`

## Gate result

**0 passed out of 9 finding gates.** There are **4 open blockers** and **5
open high-severity findings**. Slice 3A must remain framed; implementation is
not authorized.

## Findings by severity

### Blockers

1. `T081-V4-S3A-DA-001` — the proposed identity-mapping uniqueness permits
   only one model mapping per designation scope. All 10 listed scopes in the
   five calibration packets contain multiple models, so 0 of 5 packets is
   materializable under the stated schema.
2. `T081-V4-S3A-DA-002` — the shared correction root/generation boundary is
   deferred, although the 2008 fixture has one authoritative correction
   spanning applicability and requirement namespaces. Count-only deferral
   cannot preserve the one canonical correction object for a later complete
   relational round-trip.
3. `T081-V4-S3A-DA-003` — the mandatory 1998 fixture represents “cannot be
   determined” as a `known` value named `unknown_requires_compliance`, contrary
   to the approved explicit-unknown contract and the design's own invariant.
4. `T081-V4-S3A-DA-004` — compound condition identities and the multi-maker
   search hint remain flattened strings. The existing calibration test itself
   parses comma-delimited text to infer membership, which the domain contract
   prohibits future product readers from doing.

### High

5. `T081-V4-S3A-DA-005` — the identity-mapping origin enum cannot honestly
   represent source-only manufacturers/models in condition subjects or search
   hints.
6. `T081-V4-S3A-DA-006` — supersession propagation does not bind the
   successor AD number to the proposal's own canonical AD identity and the
   event schema lacks an FK to its causal dependency row.
7. `T081-V4-S3A-DA-007` — audit GETs omit an acting-membership selector while
   invariant 24 requires exact active membership authorization for audits as
   well as writes.
8. `T081-V4-S3A-DA-008` — a normative condition type/operator compatibility
   matrix is required but not enumerated or enforced at the closed Slice-2
   boundary.
9. `T081-V4-S3A-DA-009` — the proposed model-token indexes are empty by design
   and have no reviewed identity bridge, so they cannot support the claimed
   future aircraft-ID lookup path.

The finding ledger records the violated invariant, exact evidence, impact, and
required closure for each stable ID.

## Independent checks

- Initial packet freshness: **1 passed out of 1** at the fingerprint above.
- Bound input readability: **26 passed out of 26**.
- Predecessor state: Slice 1 and Slice 2 state files are `closed`; Slice 2 has
  independent implementation and closure PASS records.
- Current implementation isolation: repository search found **0 Slice-3A
  product references out of all inspected current readers**; only Slice-2 V4
  candidate code exists today, and released matching/coverage/recurrence paths
  remain V3-bound.
- Calibration source structure: **5 inspected out of 5** proposal packets,
  with the stated scope/model/condition/rule counts confirmed.
- Proposed model-mapping cardinality counterexample: **10 conflicts out of 10
  listed designation scopes**; model counts were 51, 30, 6, 182, 224, 7, 2,
  10, 33, and 130.
- Proposed positive materialization feasibility: **0 passed out of 5** under
  the current mapping contract.

## Confirmed strengths

- The candidate-only boundary, exact Slice-2 parent/hash/evidence binding,
  source-text non-duplication, append-only posture, and V3/released-reader
  isolation are directionally sound.
- The four-field applicability subtree and relational-to-parent equality gate
  are appropriately strict for a derived candidate projection.
- The 2024 design shares one condition/rule across 182 model rows and does not
  copy PDF bytes or source prose per model.
- Series-expression execution, aircraft matching, publication, due state, and
  human approval are honestly excluded from this slice.

Those strengths do not resolve the infeasible cardinality, explicit-unknown,
flattened-identity, cross-slice correction, supersession-causality,
authorization, and future-identity gaps. A revised current packet and
independent design closure review are required before implementation.
