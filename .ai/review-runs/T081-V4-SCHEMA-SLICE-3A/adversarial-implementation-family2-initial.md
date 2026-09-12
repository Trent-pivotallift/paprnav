# Adversarial implementation review — IA-001 Family 2

- Review run: `T081-V4-SCHEMA-SLICE-3A`
- Reviewer runtime: `/root/v4_s3a_impl_adversary`
- Builder runtime: `/root`
- Review mode: independent, bounded, read-only product review
- Scope: normative matrix R1-R11 only (`applicability_rule`, recursive `expression`, expression edges, and rule exclusions), including shared semantic/evidence enforcement, read verification, mutation-trigger coverage, and downgrade behavior
- Packet reviewed: `.ai/review-runs/T081-V4-SCHEMA-SLICE-3A/review-packet.md`
- Packet SHA-256 verified: `d287a97e1cad781ab0712a82ba5ff54e8e530faef31814ac91ed1bc44e46610a`
- Verdict: **PASS (bounded Family-2 slice)**
- IA-001 overall status: **OPEN**; this verdict does not cover later families.

## Findings

No blocker, major, or minor implementation finding remains in the bounded scope.

## Invariant and counterexample disposition

1. **Exact owners and semantic identity (R1-R9): PASS.** The migration gives rules and expressions one primary-key typed owner and closed reference unions (`20260907_0027_add_ad_v4_applicability.py:390-432`). The global deferred oracle counts exactly one owner for every rule/expression semantic node and rejects extra owners (`:1145-1183`). Its generic node reconstruction recomputes type, key, full pointer, parent, ordinal, canonical hash, and deterministic ID, including direct-stamped validator-2 candidates (`:1038-1070` and the surrounding semantic-node comparison). Thus self-consistent forged typed rows cannot conceal a wrong semantic parent or identity.

2. **Materialization and reference resolution: PASS.** `_rule_owner_rows` constructs registries from typed semantic nodes, rejects `requirement_state_ref`, resolves scope/condition/rule references, preserves context-relative paths, emits ordered edges recursively, and resolves exclusions only after the rule registry exists (`backend/app/services/ad_v4_applicability.py:696-805`). The unbounded text path/key representation is exercised above 255 characters by PostgreSQL test 19 (`backend/tests/test_ad_v4_applicability_postgres.py:1213-1251`).

3. **Presence, arity, edge ownership/order, and orphan rejection (R2-R10): PASS.** Rule constraints bind condition presence to nullable-root state; expression constraints close the legal branch/reference union; edge constraints enforce nonnegative sequence and one incoming edge per child (`20260907_0027_add_ad_v4_applicability.py:390-447`). Deferred SQL reconstructs the canonical branch grammar, exact references and paths (`:1728-1771`) and full-joins the expected parent/ordinal edge graph against stored edges (`:1773-1792`). Generic semantic-parent validation plus exact edge comparison rejects missing, extra, reordered, cross-owner/context/projection, orphaned, and differently-valued trees. Leaves therefore have zero edges, `not` exactly one at zero, and `all`/`any` the exact canonical contiguous sequence with at least two children.

4. **Exclusions and combined dependency cycles (R11): PASS.** Relational constraints enforce nonnegative unique ordinals and unique rule/target pairs (`:449-465`). Deferred SQL derives the exact ordered exclusion rows from canonical keys (`:1794-1817`) and checks cycles over the union of `rule_ref` and exclusion edges (`:1819-1843`), including direct self-edges.

5. **Evidence semantics: PASS.** Rule evidence is reconstructed exactly with purpose `rule_clause`, deterministic link identity/hash, and a proposal-local evidence binding; the actual set includes all nodes below each rule, so any expression evidence is an unmatched extra and is rejected (`:1845-1877`). The Python verifier likewise requires exact rule evidence and the empty evidence set for every expression (`backend/app/services/ad_v4_applicability.py:1653-1658,1715-1720`).

6. **Controlled read failure: PASS.** Reconstruction always invokes `_verify_rule_owners` before returning (`backend/app/services/ad_v4_applicability.py:849-868`), and the API maps integrity failures to controlled 409 responses. The endpoint test covers owner presence, reference/path drift, edge order/missing edge, exclusion drift, evidence drift, semantic hash drift, missing rule, and extra rule (`backend/tests/test_ad_v4_applicability.py:293-445`). Static verification additionally covers typed IDs, node parent/key/pointer/ordinal/hash/identity, exact set cardinality, expression-evidence absence, and combined cycles.

7. **Direct-SQL and deferred-validation threat model: PASS.** Test 20 disables immutability selectively and proves the independent deferred validator rejects presence, path, reference, type/arity, reordered/deleted edges, changed/deleted exclusions, evidence, semantic-parent, missing/extra owner, cross-projection reference, direct illegal expression type, a cycle-forming edge, and a fully restamped validator-2 parent containing `requirement_state_ref` (`backend/tests/test_ad_v4_applicability_postgres.py:1254-1518`). These mutations exercise the database oracle rather than a manual application verifier.

8. **Mutation dirtiness and repeated immediate validation: PASS.** Rules, expressions, edges, and exclusions are all in `APP_TABLES`; generated BEFORE triggers dirty both OLD and NEW projection IDs on INSERT/UPDATE/DELETE (`20260907_0027_add_ad_v4_applicability.py:29-49,2110-2147`). Generated deferred constraint triggers cover the same operations on every table, validate each distinct dirty projection generation, and record only the generation actually validated (`:2148-2207`). Consequently `SET CONSTRAINTS ALL IMMEDIATE` followed by a later mutation re-dirties and revalidates rather than relying on an earlier clean result.

9. **Downgrade: PASS.** Downgrade takes exclusive locks, refuses rollback with any validator-2 candidate or Slice-3A row, drops tables in reverse dependency order, and then removes trigger/helper functions (`:2210-2230`). Family-2 child relations therefore precede their rule/expression parents in teardown.

## Verification accounting

- Independently verified packet digest and inspected the complete staged/unstaged/untracked status.
- Statically reviewed the normative R1-R11 contract, migration schema and deferred SQL oracle, application materialization, reconstruction verifier, API caller, PostgreSQL negative/positive vectors, host read-corruption vectors, dirty-generation triggers, and downgrade ordering.
- Credited coordinator gates only after source inspection: host applicability plus calibration `23/23`; fresh empty migration and full PostgreSQL suite `t081_ia001_n` `21/21`; Python compile, JSON, and diff checks passed.
- No additional database run was required; no database, including `paprnav_db`, was accessed or modified by this reviewer.

## Authorization boundary

This PASS authorizes closure of the bounded Family-2 R1-R11 implementation review only. It does not close IA-001 as a whole and makes no claim for expressions/rules used by later requirement, hint, or global families beyond absence of a regression introduced by this slice.
