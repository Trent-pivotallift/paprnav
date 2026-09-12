# T081 V4 Slice 3A — Family 1 Implementation Adversarial Review

Outcome: **FAIL**  
Reviewer runtime: `/root/v4_s3a_impl_adversary`  
Builder runtime: `/root`  
Packet SHA-256: `b68844073dfdc0b229c65c35353761025595fdc4e2caec460fb3cb858e2af489`  
Scope: matrix C1–C15, shared identity/evidence behavior, and transaction-generation deferred validation only. IA-001 remains open.

## Findings

### T081-V4-S3A-F1-IA-001 — Deferred validation does not cover UPDATE or DELETE

Severity: high

Invariant: The normative matrix section 3.1 requires the database completeness validator to be a deferred constraint trigger on every graph-changing table for INSERT, UPDATE, and DELETE. Immutability is explicitly not a substitute for equivalence validation.

Evidence:

- Migration `_install_projection_completeness` creates `trg_<table>_mark_dirty` as `BEFORE INSERT` only at lines 1823–1827.
- It creates `trg_<table>_complete` as `AFTER INSERT` only at lines 1861–1865.
- The condition corruption test disables the immutable trigger, performs UPDATEs, and invokes `paprnav_v4_candidate_app_require_complete` explicitly. It does not prove that transaction-end deferred validation rejects UPDATE or DELETE.

Impact: Once an immutable trigger is disabled for an administrative repair, migration, or corruption test, an UPDATE or DELETE can commit without marking the projection generation dirty and without running deferred completeness. Audit reads may later detect the drift, but the database commit-time invariant is not enforced as designed.

Required closure:

1. Make the dirty trigger handle INSERT, UPDATE, and DELETE, resolving both OLD and NEW projection/proposal identities safely.
2. Make deferred completeness cover INSERT, UPDATE, and DELETE, including moved/cross-projection rows if such updates can reach the trigger.
3. Add PostgreSQL tests that disable only immutability, perform an UPDATE and a DELETE, and prove COMMIT or `SET CONSTRAINTS ALL IMMEDIATE` rejects the incomplete graph without directly calling the verifier.

### T081-V4-S3A-F1-IA-002 — Required direct-SQL and validation-generation matrix is not demonstrated

Severity: high

Invariant: For each Family-1 physical owner and relationship, the approved matrix requires rejection of missing, extra, reordered, cross-projection, misclassified, differently valued, union/presence, evidence, identity, cardinality, and hash corruption. It also requires proof against `SET CONSTRAINTS ... IMMEDIATE` followed by later writes.

Evidence:

- PostgreSQL test 18 exercises six UPDATE mutations: one condition value, one assertion value, one group association, one member ordinal, one mapping evidence parent, and one evidence purpose.
- It does not exercise missing or extra Family-1 owners/nodes/mappings/evidence, cross-projection relationships, wrong semantic owner type, atomic assertion presence/absence, known/unknown/not-applicable nullability, model-versus-series misclassification, source/context evidence-set swapping, mapping hash/occurrence/provenance, group member count/order variants, or semantic identity/hash drift.
- The only `SET CONSTRAINTS ALL IMMEDIATE` test predates Family 1 and inserts one extra generic datum. There is no test that first validates a generation, then inserts a later Family-1 row and proves the new generation is revalidated.

Impact: The broad implementation closure claim rests principally on one positive mega-fixture and selected field mutations. It does not provide the mandatory independent database evidence for the owner-set and transaction-generation threat model.

Required closure:

1. Add a table-driven Family-1 PostgreSQL corruption matrix covering every X-* class named by the normative matrix across conditions, assertions, groups, members, mappings, evidence, and semantic nodes.
2. Include missing, extra, wrong-type, reordered/gapped, cross-projection, union/nullability, occurrence/context evidence, identity/provenance/hash, and cardinality cases.
3. Add an explicit `SET CONSTRAINTS ALL IMMEDIATE` → valid state → later Family-1 INSERT counterexample and require immediate or commit-time rejection.
4. Exercise read-side missing/extra and union/provenance corruptions through the actual audit endpoint, not only seven selected UPDATE fields.

## Verified positive scope

- The positive fixture contains 90 condition type/operator combinations, 18 atomic known-string branches, four group associations, model and series members, and a 512-character not-applicable reason.
- Application materialization preserves atomic and member assertion unions, `model_or_series`, model/series member discrimination, exact occurrence/context evidence parents, and exact source values.
- PostgreSQL expected/actual comparisons use `IS DISTINCT FROM` for the principal Family-1 owner relations and compare exact Family-1 evidence and mapping relations.
- Verified reads compare exact expected Family-1 owner, assertion, member, mapping, evidence, and semantic-node sets for the exercised graph.

These positives do not close the two findings above.
