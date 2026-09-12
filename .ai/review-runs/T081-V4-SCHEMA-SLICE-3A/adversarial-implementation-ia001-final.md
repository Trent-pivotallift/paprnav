# Holistic adversarial implementation review — IA-001

- Review run: `T081-V4-SCHEMA-SLICE-3A`
- Reviewer runtime: `/root/v4_s3a_impl_adversary`
- Builder runtime: `/root`
- Stage: implementation (not closure and not commit authorization)
- Mode: independent whole-tree review; product, tests, ledgers, packet, reviews, and prior artifacts remained read-only
- Packet SHA-256 verified: `d78b4a257935f45ec161bcc3af99daac8d371871e0eb72ebcb6a1a4f03384748`
- Verdict: **PASS**
- IA-001 disposition: **eligible to close**; no blocker or high-severity residual remains

## Findings

No blocker, high, or other material residual was found in the complete approved IA-001 implementation scope.

## Original blocker disposition

The original IA-001 blocker is closed by implementation evidence. Migration 0027 no longer relies on generic semantic/datum rows as the semantic projection. It defines physical typed owners for value assertions, identity mappings, product/designation scopes and values/ranges, conditions and designation groups/members, rules/expressions/edges/exclusions, search hints/groups/members, and change dependencies. The database enforces closed unions, exact references, ownership, order, cardinality, evidence, identity, and canonical equivalence at transaction end. Python verified reads independently enforce the same graph and construct a second typed representation.

## Whole-contract assessment

1. **Exactly one typed owner for every semantic type — PASS.** Python enumerates all fifteen node types, including both outgoing and target-local incoming `change_dependency` nodes, and requires the complete owner ID set to equal the semantic-node ID set with exactly the singleton matching type (`backend/app/services/ad_v4_applicability.py:996-1057`). PostgreSQL performs the same count-per-type and full owner-union check (`backend/app/db/migrations/versions/20260907_0027_add_ad_v4_applicability.py:1512-1555`). Primary keys, composite projection/proposal FKs, and the global union reject missing, extra, duplicate, wrong-type, and cross-projection owners.

2. **Source/product/designation family — PASS.** Physical owners preserve optional manufacturer presence, all normalized-identity states and provenance, all/listed/series/ranges/unknown/not-applicable designation branches, model-only listed occurrence mappings, mapping-free serial/part values, exact ranges, and evidence inheritance/absence. Generic semantic validation recomputes node type/key/pointer/nearest parent/ordinal/canonical hash/deterministic ID; mapping validation binds mapping nodes to the exact source occurrence and context. Python and SQL family full joins reject changed, missing, extra, reordered, misclassified, or cross-wired owners.

3. **Conditions, assertions, and designation groups — PASS.** C1-C15 have closed typed unions and optional-presence columns, exact one assertion per canonical subject field, exact known-only identity occurrences, all four condition-group associations, both member kinds, group-context evidence inheritance, ordered member cardinality, and fixed unevaluated evaluator semantics. Application, read verifier, SQL deferred oracle, and tests agree on all 90 type/operator pairs, all 18 known-string branches, association branches, and 1/64/65/511/512 boundaries with rejection beyond the canonical limit.

4. **Rules and recursive expressions — PASS.** R1-R11 are represented by exact rule/expression owners, explicit optional condition-root presence, same-projection typed references, context-relative paths, all six legal expression branches, exact not/all/any arity, ordered contiguous edges, one incoming edge for non-roots, exact exclusions, and combined rule-reference/exclusion acyclicity. `requirement_state_ref` and catch-all storage are absent from applicability-rule projection, including the independently checked fully restamped validator-2 parent attack. Pointer-derived keys beyond 255 characters remain lossless.

5. **Non-controlling search hints — PASS.** H1-H11 have fixed false controlling/exhaustive flags, exact display/group/member owners, all association and value unions, known-only manufacturer mappings, per-occurrence model/series mappings, group evidence-parent semantics, exact evidence, and ordered cardinalities. No expression or released path can reference/promote a hint. The 2002 calibration remains one hint, seven groups, twenty members, nineteen models, and one opaque series expression without invented expansion.

6. **Independent reconstruction and cross-family drift control — PASS.** Generic datum reconstruction is first compared with the parent candidate, stored canonical bytes, and hashes. Every family verifier then checks its typed graph. `_verify_global_owner_graph` closes the full partition, after which `_typed_reconstruct_applicability` rebuilds all four fields solely from typed owners, semantic reference keys/order, assertions, mappings, evidence, edges, and exclusions and is exact-compared to generic reconstruction and candidate (`service :955-1409`). PostgreSQL has separate typed helper functions and compares `paprnav_v4_candidate_app_typed_subtree` with the candidate subtree using `IS DISTINCT FROM` after detailed family enforcement (`migration :1020-1285,2773-2774`). Cross-family substitutions, NULL/empty-set tricks, alternate valid shapes, and three-valued SQL bypasses therefore cannot commit as equivalent.

7. **Evidence, identity, hashes, references, order, and counts — PASS.** Shared application and SQL verifiers recompute deterministic semantic, datum, evidence-link, and mapping identities/hashes; bind evidence to the exact proposal evidence binding; prohibit evidence owned by identity mappings; enforce mapping origin/state/reason/temporal/namespace/version/review state and exact inherited parent; and full-join every expected family set. Projection counts cover base semantic nodes, datum, evidence, and mappings, while target-local incoming dependency nodes are intentionally outside the immutable candidate base count but remain in the global owner and dependency graph.

8. **Direct-SQL threat model — PASS.** The PostgreSQL suite disables immutability selectively and exercises missing, extra, deleted, reordered, changed-value, wrong union/type/parent/reference/projection/evidence/mapping/hash/cardinality owners across every family. It includes fully self-restamped candidate/projection/datum/semantic attacks, forged validator-2 grammar, duplicate dependency ownership, SET-CONSTRAINTS-then-later-write, cycle, stale/dependency concurrency, and stored-count drift. These failures are generated by constraint/deferred database enforcement rather than by calling the Python verifier.

9. **Read behavior and query boundary — PASS.** Detail, reconstruction, and list all traverse `verified_app_projection`/serialization and full reconstruction; integrity failures map to controlled `409 projection_integrity`. The count-drift vector proves all three audit reads fail closed. Reads are detection-only: stale repair and audit-event writes remain reachable only inside the authorized, doubly gated, locked materialization POST transaction. Repository-wide consumer search found no released/customer, V3, aircraft matching, compliance, due-state, provider, CLI, cron, or background consumer of the new typed projection tables.

10. **Mutation ordering, migration, and rollback — PASS.** Every Slice-3A child relation has generated BEFORE dirty and deferred AFTER INSERT/UPDATE/DELETE triggers. OLD and NEW projection IDs are dirtied, generations prevent validation elision after an early `SET CONSTRAINTS`, and one final exact validation is performed per dirty generation. Migration is additive and preserves v1 readers. Downgrade locks the affected tables, refuses validator-2 or occupied Slice-3A state, drops triggers/helpers before reverse-dependency table teardown, restores the prior constraints/columns, and has clean empty downgrade/re-upgrade coverage.

11. **Calibration and test-claim sufficiency — PASS.** The five validator-2 calibration packets pass schema/canonical determinism and real-evidence materialization/exact reconstruction. The complete host suite covers controlled read/auth/gate/no-cutover behavior. The fresh PostgreSQL suite includes all family positive matrices, direct-SQL corruption matrices, migration rollback/refusal, concurrency/idempotency, incoming/outgoing dependencies, and global typed reconstruction. The global positive case combines typed designation unions, recursive rules, hints, dual evidence, and dependency ownership in one projection, addressing cross-family composition rather than merely isolated family cases.

## Verification accounting

- Verified the requested packet digest and inspected the actual staged, unstaged, and untracked working tree plus all surrounding consumers.
- Re-read the original IA-001 blocker, complete normative matrix and physical appendix, checkpoint, implementation evidence, bounded review artifacts, migration/model/service/API paths, calibration fixtures, and host/PostgreSQL tests.
- Attempted counterexamples involving missing/extra/duplicate/wrong owner, valid-shape cross-family swaps, mapping occurrence/context swaps, NULL and empty branches, changed and reordered values, cross-projection references, forged hashes/parents, expression and rule cycles, incoming dependency ownership, typed-helper exceptions, stale repair via reads, and alternate query consumers.
- Independently reran safe non-database checks: `git diff --check` passed and Python compilation of the service and migration passed.
- Credited the coordinator's latest clean evidence after static validation: focused host/calibration **25/25**, complete V4 host **75/75**, and freshly migrated disposable PostgreSQL `t081_ia001_s` **24/24**. No database was accessed by this reviewer.

## Decision

**PASS. T081-V4-S3A-IA-001 may be closed at the implementation stage.** This report is not a closure-stage attestation, staging/commit authorization, or a conclusion on any finding outside IA-001.
