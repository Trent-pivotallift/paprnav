# T081 V4 schema adversarial design review — initial

Reviewer: `/root/v4_schema_adversary`  
Outcome: **FAIL**  
Verification: **0 passed out of 1 design gates**

No implementation or tests were run. The review was read-only.

## Blockers

### T081-V4-DA-001 — Review artifact does not bind the proposed schema

The generated packet hashes the domain contract but excludes the decision and
the 907-line schema proposal from its manifest. A recorded review could remain
current after the proposed schema changed. Rebuild the packet with the domain
contract, decision, proposal, and relevant dirty consumers explicitly included
and hashed, then rerun design review.

### T081-V4-DA-002 — Applicability and branch logic has no complete semantics

The proposal defines only one-level `all`/`any`/`none`, permits requirements to
reference multiple rules without defining AND/OR semantics, and assigns branch
kinds without conditional predicates. Define a typed Boolean and branch
algebra, three-valued truth tables, explicit semantics for every
multi-reference, relational representation, evaluator versioning, cycle rules,
and positive/negative calibration cases.

### T081-V4-DA-003 — Evidence fragments can self-authenticate inaccurate text

The fragment hash includes supplied `exact_text`, but no immutable,
source-hash-bound page rendition/text version proves that text came from the
retained PDF. Fragment status is also described as mutable on an otherwise
immutable row, and `not_applicable` has no evidence. Define immutable page
renditions/text versions, bind fragments through offsets or coordinates and
parser hashes, move lifecycle transitions to separate events, and require
evidence for safety-relevant negative assertions.

### T081-V4-DA-004 — PostgreSQL cannot losslessly enforce or round-trip V4

The relational sketch reduces field-level known/not-applicable/unknown values
to nullable columns without complete temporal scope or value-level evidence,
while leaving STC and other matching predicates in generic JSON. Supply a
field-by-field lossless mapping with CHECK/unique/FK constraints, typed
STC/series/identifier/temporal structures, value-level evidence links, canonical
round-trip tests, and database-negative tests.

### T081-V4-DA-005 — Publication behavior for explicit unknowns is undecided

The domain owner must decide whether a reviewed unknown may enter a distinct
candidate-only publication state or whether it keeps the directive in
remediation. The design must then enforce node-level automation gates so an
unknown cannot produce affirmative applicability, compliance, terminating
credit, or a due value.

### T081-V4-DA-006 — No source-complete calibration proves the redesign

The illustrative JSON explicitly is not source-complete and the calibration
section lists future assertions rather than executable gold cases. Provide
source-complete V4 gold packets for real ADs covering every contract pattern,
including expected searches and negative aircraft/component outcomes.

## High findings

### T081-V4-DA-007 — Lifecycle and rollback are not auditable state machines

Mutable lifecycle status is stored on rows described as append-only, while
correction, supersession, invalidation, and rollback eligibility lack explicit
events and edges. Define immutable lifecycle events, correction/supersession/
invalidation edges, compare-and-swap selection, one-current-version constraints,
deterministic rollback eligibility, and failure-injection rehearsal.

### T081-V4-DA-008 — Signoff lacks an attributable authority binding

Reviewer user, organization, and role do not preserve the membership or
aircraft-assignment authority snapshot. Bind decisions to membership/assignment
IDs and authorization snapshots, define scope and self-review policy, append
rather than overwrite determinations, and test direct API authorization and
concurrency.

## Decision classification

Domain-owner decisions are required for candidate-only publication of unknowns,
normalization governance, service-bulletin exposure/licensing, single versus
dual control and self-review, the V3 approval freeze point, and corrected-V4 to
V3 rollback policy. Temporal interval encoding and database-reference versus
application-enum mechanics are engineering choices constrained by the domain
contract.
