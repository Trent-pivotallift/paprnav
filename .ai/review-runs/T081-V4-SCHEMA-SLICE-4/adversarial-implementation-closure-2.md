# T081 V4 Schema Slice 4 implementation closure review 2

Outcome: **FAIL**  
Reviewer runtime: `/root/v4_s4_design_adversary`  
Packet SHA-256: `d66b273688a22b9ff05b7ab896c66b0688fd2cf30131e13576b10273b7292338`  
Base: `4840a0b4bc5d7334ddcf51a80e39c8fa84b7b0c2`

The packet hash remained unchanged. All 23 manifest file hashes matched the
working tree, no files were staged, and the reviewer inspected changed,
untracked, and surrounding implementation without editing repository files.

## T081-V4-S4-IMPL-H-003 — high — open

Legal drafts can consume the entire 16 MiB case budget without reserving space
for the mandatory request and rejection lifecycle. The reviewer reproduced
this on PostgreSQL with all constraints and triggers enabled: nine legal drafts
left a case at 16,777,214 authoritative bytes, `request_review` failed with
`review_history_limit`, and successor creation failed with `review_case_open`.
Because history is immutable, that candidate's workflow is permanently
stranded.

Required closure: enforce phase-aware byte reservations in Python and SQL so
admitted drafts preserve space for request, rejection, companion events, and
signoff. Add fully sealed PostgreSQL boundary tests proving request, rejection,
and successor creation remain possible after maximal admitted drafts.

## T081-V4-S4-IMPL-M-001 — medium — remains open

Case-byte accounting and retained-object bounds improved, but metadata-only
authorship, cutoff, and frozen-source verification still select complete
submission, relationship, and fragment entities, including large
`request_canonical_bytes` and `exact_text` values outside the work budget.
Cutoff head construction also traverses the complete lifecycle chain through
the unbounded evidence lifecycle verifier. Allocation-light probes confirmed a
1 MiB unused submission blob was selected and oversized evidence re-entered
full-text materialization after the observation branch declined that work.

Required closure: use explicit scalar projections for metadata-only reads,
prevent deferred blob loads, and bound or replace lifecycle traversal with a
reviewed bounded-head strategy. Apply the work policy across observation,
authorship, cutoff, and historical verification, with query-shape and overflow
tests proving prohibited payload columns are not selected.

## T081-V4-S4-IMPL-M-002 — medium — open

The verification document attributes exact downgrade restoration and helper
removal to automated gates, but current tests only assert final user-first lock
order. The exact definition comparison was an ad hoc probe, and only the draft
reviewer gate—not each gate independently—was tested for downgrade refusal.

Required closure: add an isolated `0028 -> 0029 -> 0028` regression comparing
both complete function definitions and verifying helper removal; test each
reviewer gate independently; correct the evidence document.

## Closed findings reverified

- `T081-V4-S4-IMPL-H-001`: closed. Both inherited functions now use the
  user-before-membership order, reject definition drift, and pass forced
  direct-SQL interleavings.
- `T081-V4-S4-IMPL-B-001`: remains closed. Observation-union, ownership,
  nested-digest, and SQL/Python parity tests pass.
- `T081-V4-S4-IMPL-H-002`: remains closed. Expected retained-storage failures
  and size overflow stay controlled; unexpected failures remain distinguishable.

## Independent verification

- Host review/service/storage suites: 91 passed.
- PostgreSQL migration, lock-order, and service suites: 82 passed.
- Legal lifecycle probe reproduced H-003.
- Source-query probes confirmed residual M-001 paths.
- `git diff --check`: passed.
- Manifest verification: 23 files matched with no packet drift.

Acceptance, decision graphs, publication/current selection, document
admission, the V3 freeze, and frontend UI remain outside this rejection-only
vertical. The implementation gate remains closed.
