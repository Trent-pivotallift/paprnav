# Adversarial implementation review — IA-001 final global family

- Run: `T081-V4-SCHEMA-SLICE-3A`
- Reviewer runtime: `/root/v4_s3a_impl_adversary`
- Builder runtime: `/root`
- Mode: independent bounded review; product, tests, ledger, packet, and prior artifacts remained read-only
- Verified packet SHA-256: `e250bc919acc55acf4578c7ee12c1e2c1c45c80e293a2fa1fa4ddbd299b467fd`
- Verdict: **PASS — bounded final global family**
- IA-001 overall: **OPEN** pending a whole-tree IA-001 implementation review and closure gates

## Findings

No blocker or high-severity residual was found in the bounded global scope.

## Adversarial disposition

1. **Complete Python owner partition and stored counts — PASS.** `_verify_global_owner_graph` independently checks base semantic, evidence, and mapping counts against the projection envelope, enumerates all fifteen semantic types, including `change_dependency`, and compares the complete physical-owner ID set to every semantic node (`backend/app/services/ad_v4_applicability.py:996-1057`). Because owners are accumulated across tables and compared as the exact singleton `[node.node_type]`, missing, extra, duplicate cross-type, and wrong-type owners fail. Incoming `/incomingSupersessionSignals/` nodes are excluded only from the immutable base count, not from owner partitioning; both outgoing and incoming dependency rows are included.

2. **Independent Python typed reconstruction — PASS.** `_typed_reconstruct_applicability` reads semantic metadata, typed owner tables, refs, assertions, mappings, evidence, edges, exclusions, and stored ordinals to rebuild all four canonical fields (`service :1060-1370`). It does not read candidate JSON or generic datum rows. Product optional branches and designation unions, all condition assertion/group branches, recursive rule expressions/exclusions, and complete search-hint groups/members are reconstructed from typed relations. `reconstruct_applicability` first verifies the generic datum subtree and each family, then the global owner partition, then exact-compares typed output to generic output, parent candidate, canonical bytes, and subtree hash (`:955-993`).

3. **PostgreSQL typed reconstruction — PASS.** The SQL helpers reconstruct evidence, assertions, normalized identities, designation unions, condition/search groups, and recursive expressions; `paprnav_v4_candidate_app_typed_subtree` composes all four ordered top-level arrays solely from typed relations (`backend/app/db/migrations/versions/20260907_0027_add_ad_v4_applicability.py:1040-1285`). The deferred validator performs the canonical/datum/family/reference/cardinality checks before the final `IS DISTINCT FROM` typed-subtree comparison (`:1288-2774`). Thus malformed NULLs, missing strict-helper targets, wrong arity, and cycles are rejected earlier rather than accepted through helper NULL behavior.

4. **Complete database owner union — PASS.** Deferred SQL covers all semantic types, including `change_dependency`, counts the matching physical owner for every node, and unions every owner table to reject a row hung from another semantic type (`migration :1475-1535` in the current tree). Composite projection/proposal FKs prevent cross-projection ownership; primary keys prevent same-table duplicate ownership; cross-table duplicates are detected by the union. Incoming dependency nodes participate in this global check even though they are deliberately excluded from the candidate-derived base semantic count.

5. **Dependency-node treatment — PASS.** Existing dependency verification runs before the global owner and typed reconstruction checks (`service :976-978`) and verifies outgoing canonical relations plus target-local incoming signals. PostgreSQL dependency validation likewise covers exact outgoing and incoming identities/links. The prior concurrency matrix contains a resolved outgoing/incoming pair (`backend/tests/test_ad_v4_applicability_postgres.py:700-755`), while global test 23 proves a second dependency owner on one semantic node is rejected (`:1860-1910`).

6. **Read fail-closed behavior and detection-only semantics — PASS.** `verified_app_projection` always calls full reconstruction (`service :3099-3108`); detail and reconstruction use it, and list serializes each returned projection through the same verified path (`backend/app/api/routes/ads.py:482-570`). `projection_state` only detects stale state; repair remains confined to the authorized materialization POST (`service :3110-3160` versus `:2725-2950`). All `ADV4Error` integrity failures are translated to controlled HTTP errors. Global count-drift test coverage proves detail, reconstruction, and list each return `409 projection_integrity` without repair (`backend/tests/test_ad_v4_applicability.py:580-612`).

7. **Counterexamples and error containment — PASS.** Valid-shape substitutions in typed rows cannot survive the family verifiers and the typed-vs-generic-vs-candidate comparison. Missing/extra/empty/reordered rows fail exact family sets or typed equality; cross-projection refs fail composite FKs; altered identity/evidence/hash state fails the shared verifiers; expression cycles/arity fail before recursive reconstruction. Python lookup operations occur only after the family verifiers establish required referenced rows, so the inspected corruption classes produce controlled `ADV4Error` rather than an uncaught `KeyError`. The SQL final comparison uses `IS DISTINCT FROM`, avoiding three-valued equality bypass.

8. **Dirty generation and downgrade/re-upgrade — PASS.** Every projection/owner/evidence/dependency table is in `APP_TABLES`. Generated BEFORE dirty triggers and deferred AFTER constraint triggers cover INSERT/UPDATE/DELETE and both OLD/NEW projection IDs; generation comparison forces validation again after `SET CONSTRAINTS ALL IMMEDIATE` followed by a later write (`migration :2777-2893`). Downgrade locks/refuses occupied state, drops constraint/dirty triggers and typed helper functions before reverse-order tables, and restores the v1 schema only after proving no v2/Slice-3A rows (`:2896-2945`). Existing PostgreSQL migration tests cover empty downgrade/re-upgrade and occupied refusal.

9. **Positive and negative proof — PASS.** PostgreSQL test 23 combines typed scope shapes, full rule and hint matrices, dual evidence, and an outgoing dependency, then exact-compares both SQL and Python typed reconstructions to the candidate; it rejects a duplicate dependency owner and forged stored semantic count (`backend/tests/test_ad_v4_applicability_postgres.py:1860-1925`). Earlier family PostgreSQL/read corruption matrices exercise each typed family, while the resolved dependency test covers incoming ownership. The coordinator-reported fresh PostgreSQL and host gates are consistent with the inspected tests; no claim was credited beyond static evidence.

## Verification accounting

- Verified the requested packet digest and inspected the complete staged, unstaged, and untracked working tree.
- Traced global Python verification and reconstruction, every SQL typed helper and final deferred comparison, global owner unions, dependency handling, API callers, detection/repair separation, trigger generation, downgrade, and relevant positive/negative tests.
- Attempted NULL, empty-set, order, cardinality, cross-projection, hash/reference, duplicate-owner, incoming-dependency, recursive-cycle, helper-exception, and candidate/generic-data shortcut counterexamples.
- Per assignment, no database was accessed or mutated and no product, test, ledger, packet, or earlier artifact was edited.

## Boundary

This PASS closes only the bounded final-global-family review. IA-001 remains open until the coordinator obtains a fresh holistic whole-tree implementation review and the required closure attestations.
