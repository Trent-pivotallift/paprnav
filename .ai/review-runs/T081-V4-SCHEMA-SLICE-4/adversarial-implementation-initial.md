# T081 V4 Schema Slice 4 — implementation adversary (initial)

Outcome: **FAIL**

Reviewer runtime: `/root/v4_s4_design_adversary`

Exact packet SHA-256:
`a30f4b621611111f636caa94d7b858e3b012bbc51cf890b03af6ddb04b771994`

Base: `4840a0b4bc5d7334ddcf51a80e39c8fa84b7b0c2`

The independent reviewer inspected the staged, unstaged, and untracked tree,
the candidate/evidence/projection writers and readers, migration SQL, API and
schema contracts, storage behavior, tests, and rollout contract. It ran the
focused API/service and PostgreSQL suites and additional rollback-only probes.

The rejection-only boundary is correctly preserved: there is no acceptance,
decision-node graph, publication/current selection, V3 authority mutation, or
reviewer UI in this vertical. The implementation is not approved because one
Blocker, two Highs, and one Medium remain:

1. `T081-V4-S4-IMPL-B-001`: PostgreSQL accepted a fully resealed nonverified
   observation with a malformed nested hash that Python historical reads
   reject. SQL must enforce the complete branch/field/digest/source contract
   and gain direct-SQL parity tests.
2. `T081-V4-S4-IMPL-H-001`: candidate submission locks evidence fragments
   before the relationship graph while review writers do the reverse. A forced
   interleaving reproduced SQLSTATE `40P01`; candidate error translation is
   also incomplete.
3. `T081-V4-S4-IMPL-H-002`: expected S3 missing/access/transport errors escape
   retained-source observation rather than becoming a bounded nonverified
   remediation state.
4. `T081-V4-S4-IMPL-M-001`: response paging does not bound full history,
   predecessor, and source verification work.

The reviewer independently observed 3 API/service tests and 13 PostgreSQL
migration/service tests passing and found `git diff --check` clean. Those
passing tests do not close the four findings above.
