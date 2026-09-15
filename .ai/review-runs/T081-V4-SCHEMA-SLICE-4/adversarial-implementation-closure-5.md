# T081 V4 Schema Slice 4 implementation closure review 5

Outcome: **PASS**  
Reviewer runtime: `/root/v4_s4_design_adversary`  
Builder/coordinator: `/root`  
Base: `4840a0b4bc5d7334ddcf51a80e39c8fa84b7b0c2`  
Reviewed packet SHA-256: `b531efdaba8866893e8c0dcdb4d60f19922c87bfab95371892e455551ba9647a`

The reviewer verified the packet hash and all 23 implementation-manifest file
hashes, inspected staged, unstaged, and untracked scope plus relevant callers,
readers, SQL, migration paths, tests, and contracts, and made no repository
edits. No staged changes were present and `git diff --check` passed.

## Finding dispositions

### T081-V4-S4-IMPL-M-001 — closed

The obligation observation inherits the applicability parent's individual
preflight failure before child reconstruction can read that parent's audit
payload. Scalar projection identity, count, and byte metadata are collected
before full projection loading. Controlled nonverification returns before
reconstruction when the budget fails. The queue uses the same prepared
metadata and observation path after cumulative-budget checks.

The reviewer checked the exact-parent assumption: the database contract
requires the obligation's same-proposal applicability parent, matching parent
hash, and supported materializer version; proposal/materializer uniqueness
prevents another valid supported parent from bypassing dependency propagation.

The populated `obligation_count`, `parent_count`, and `parent_bytes` tests
passed. The reviewer also independently exercised real detail and queue readers
against persisted projections:

- parent-count overflow used three valid parent requests and one event while
  the child remained individually within budget;
- parent-byte overflow used eight valid parent requests totaling 2,679 audit
  bytes while the child's 1,405 bytes and source evidence remained within the
  selected test budget.

For both counterexamples, detail and queue returned matching input identities,
both parent and child were `integrity_error`, and ORM selection instrumentation
observed no projection request/event payload-byte columns, directly or through
child reconstruction.

### Previously closed findings

- T081-V4-S4-IMPL-H-003 remains closed. The current PostgreSQL run passed the
  near-ceiling lifecycle test through request, rejection, and successor. The
  independently verified exact two-byte-residual and corrupt stored-phase
  probes remain applicable to unchanged implementation.
- T081-V4-S4-IMPL-M-002 remains closed. The reviewer inspected the unchanged
  lock-order transformation, exact downgrade inverse, full inherited-function
  comparison, helper removal, and independent downgrade gates. The prior
  independent four-test fresh-database rollback run remains its execution
  evidence.
- T081-V4-S4-IMPL-B-001, H-001, and H-002 remain closed. Targeted inspection
  and current suites found no regression in SQL/Python observation parity,
  lock ordering, or allowlisted storage-error handling.

No new blocker, high, or medium finding was identified.

## Independent verification

- Host service/bounds/storage suites: **93 passed**.
- PostgreSQL migration, lock-order, and service suites: **86 passed**.
- Additional populated parent-count and parent-byte probes: passed for both
  detail and queue with zero prohibited projection payload selections.

## Gate conclusion

**PASS for the frozen rejection-only implementation vertical.** M-001 is
closed and no implementation blocker remains.

This does not approve the entire Slice 4 feature set. Acceptance, actionable
classification, reviewer UI, publication/current selection, supporting-document
admission, and V3 freeze behavior remain intentionally absent and outside this
approval.
