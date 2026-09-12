# Adversarial implementation review — IA-001 Family 3

- Run: `T081-V4-SCHEMA-SLICE-3A`
- Reviewer runtime: `/root/v4_s3a_impl_adversary`
- Builder runtime: `/root`
- Mode: independent bounded review; product, tests, and ledger remained read-only
- Scope: normative matrix H1-H11 only (non-controlling applicability search hints, manufacturer/model groups, members, assertions, occurrence mappings, and shared integrity machinery)
- Packet: `.ai/review-runs/T081-V4-SCHEMA-SLICE-3A/review-packet.md`
- Verified packet SHA-256: `8eda25ce2c303107d6dcaba583bc5f56c2c9b8313b5748f5b43b8a63072b2072`
- Verdict: **PASS — bounded Family 3**
- IA-001 overall: **OPEN** pending the final global family and whole-tree gates

## Findings

No blocker or high-severity finding remains in this bounded slice.

## Adversarial disposition

1. **H1-H3 owners, cardinality, non-promotion, and ordering — PASS.** The migration defines primary-key typed owners, same-projection/proposal parent FKs, closed role/association domains, fixed `controlling=false` and `exhaustive=false`, nonnegative ordinals, and per-parent key/ordinal uniqueness (`backend/app/db/migrations/versions/20260907_0027_add_ad_v4_applicability.py:466-507`). Deferred SQL full-joins canonical hints/groups to stored rows, requires at least one group and member, checks sorted unique keys, exact parent/assertion pointers, ordinals, all fields, and closed property sets (`:1975-2077`). No hint ID is present in the applicability-expression reference union (`:411-432`), and repository caller search found no alternate hint promotion/reference consumer.

2. **H2/H4/H8 assertion union and evidence — PASS.** Materialization emits one text assertion for the hint display and each group/member manufacturer (`backend/app/services/ad_v4_applicability.py:834-922`). SQL reconstructs the exact expected assertion set and validates the closed known/unknown/not-applicable union, 1–512 bounds, allowed reasons/temporal scopes, parent, field, and evidence (`migration :2139-2197,2242-2287`). Read verification recomputes the semantic identity, parent, pointer, ordinal, canonical hash, typed row, union values, and exact evidence (`service :1937-1963,1991-1995,2025-2035,2082-2089`).

3. **H5/H9/H10/H11 identity mappings — PASS.** `_identity_rows` creates mappings per exact occurrence: only known group/member manufacturers, every model or series member designation, and group-relative evidence parents (`service :343-425`). The Family-3 read verifier requires exact mapping presence or absence and checks kind, source, origin/state/reason/temporal/namespace/version/review state through the shared mapping verifier (`:2036-2049,2090-2120`). Its final occurrence and semantic-node set comparison rejects missing, extra, duplicate, or cross-wired mappings (`:2122-2157`). SQL independently full-joins the exact expected occurrence set and checks the enclosing group context and all provenance fields (`migration :2199-2240`); the shared mapping oracle binds mapping ID/hash and its semantic node exactly to `source_occurrence_node_id` (`:1290-1325`). Repeated spellings therefore do not collapse occurrences.

4. **H6/H7 closed member union and source fidelity — PASS.** Schema checks distinguish model source designation from opaque series expression and require the physical `unevaluated/unsupported_expression` state for series (`migration :509-538`). Materialization copies the branch without expansion (`service :889-919`). SQL and read verification compare every field, exact ordered member set, branch-specific canonical properties, 1–512 source boundary, manufacturer assertion, and required designation mapping (`migration :2079-2137`; service `:2051-2120`).

5. **Semantic identity, ownership, hash, and cardinality — PASS.** Search-hint assertions and known-manufacturer synthetic mappings are included in the expected semantic count (`migration :1080-1128`). The generic semantic oracle recomputes type, key, nearest parent, pointer ordinal, canonical hash, and deterministic identity (`:1130-1215`). Exactly-one typed-owner enforcement includes all three hint owner tables and rejects wrong-type extra owners (`:1240-1284`). Family-specific full joins then reject missing/extra/reordered/differently-valued rows.

6. **Self-restamped/direct-SQL threat model — PASS.** PostgreSQL test 22 disables immutability per vector and proves the deferred database validator rejects changed hint role, assertion values, group association/order/assertion reference, member value/order/mapping reference, mapping evidence parent, evidence purpose, missing member, cross-projection parent, and extra typed owner (`backend/tests/test_ad_v4_applicability_postgres.py:1639-1800`). It then restamps candidate/projection bytes and hashes, semantic hash, datum, and count with an extra `unsafePromotion` property; the independent closed SQL grammar rejects it (`:1802-1860`). These are database checks, not calls to the Python verifier.

7. **Read-time fail-closed behavior — PASS.** Reconstruction compares the datum-built subtree and all canonical hashes before invoking all typed verifiers, including `_verify_search_hint_owners` (`backend/app/services/ad_v4_applicability.py:956-979`). The API corruption test obtains controlled `409 projection_integrity` for hint/group/member/assertion/mapping/evidence/semantic drift and missing/extra owners (`backend/tests/test_ad_v4_applicability.py:450-579`). Verification covers more fields than the mutation sample, including every mapping provenance field and exact semantic/evidence sets.

8. **I/U/D dirty/deferred enforcement — PASS.** All three hint tables are in `APP_TABLES` (`migration :29-52`). Generated BEFORE dirty triggers and deferred AFTER constraint triggers cover INSERT, UPDATE, and DELETE for every table; OLD and NEW projection IDs are collected and distinct dirty generations are validated (`:2520-2618` in the current migration). The generation comparison prevents a prior `SET CONSTRAINTS ALL IMMEDIATE` from blessing a later write.

9. **Positive branches, boundaries, and calibration — PASS.** PostgreSQL test 21 covers six product roles, all three associations, all assertion states, both member kinds, a 512-character reason, and exact counts 6 hints / 6 groups / 12 members / 24 assertions / 18 mappings (`backend/tests/test_ad_v4_applicability_postgres.py:1586-1637`). The five-packet calibration retains exact reconstruction; packet `2002-13-04` specifically asserts 1 hint, 7 groups, 20 members, 19 models, one opaque series, and absence of invented series expansion endpoints (`backend/tests/test_ad_v4_applicability_calibration.py:292-300`).

10. **Downgrade — PASS.** Downgrade locks all Slice-3A tables, refuses rollback with validator-2 candidates or any populated Slice-3A table, drops tables in reverse dependency order, then removes helper functions (`migration :2620-2640` in the current tree). The three hint child/parent tables are ordered safely in `APP_TABLES`.

## Verification accounting

- Read the repository adversarial process and reviewer brief, complete normative matrix, checkpoint, implementation evidence, ledger, current packet, and actual staged/unstaged/untracked tree.
- Inspected model parity, semantic augmentation, identity construction, typed materialization, reconstruction/read verification, API caller, migration upgrade/deferred validator/dirty triggers/downgrade, and relevant host/PostgreSQL/calibration tests.
- Credited only after static trace: host applicability and calibration **24/24**; freshly migrated disposable PostgreSQL `t081_ia001_q` **23/23**; compile/JSON/diff checks as recorded by the coordinator.
- No database was accessed or mutated and no test was rerun by this reviewer.

## Boundary

This report authorizes closure only of the H1-H11 Family-3 implementation slice. It does not close IA-001, certify the final global family, or authorize staging/commit/overall closure.
