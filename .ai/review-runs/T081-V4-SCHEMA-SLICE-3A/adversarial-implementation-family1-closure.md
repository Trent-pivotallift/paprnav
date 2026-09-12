# T081 V4 Slice 3A — Family 1 Targeted Closure Review

Outcome: **PASS**  
Reviewer runtime: `/root/v4_s3a_impl_adversary`  
Builder runtime: `/root`  
Packet SHA-256: `a613ca3b54ad2181a47adcc896f93c86ab0c975913b55d6318927bb38c2de46f`  
Scope: closure of `T081-V4-S3A-F1-IA-001` and `T081-V4-S3A-F1-IA-002`, including the coordinator-found mapping cross-wire candidate. IA-001 remains open.

## Finding dispositions

### T081-V4-S3A-F1-IA-001 — CLOSED

The dirty trigger and deferred completeness constraint trigger now cover
INSERT, UPDATE, and DELETE on every child table. The dirty function resolves
OLD and NEW projection identities, so a moved row dirties both affected
projections. The deferred function independently resolves the same identity
set, deduplicates it, validates only when generation differs from the validated
generation, and records the generation only after the full verifier succeeds.

Queued trigger events observe the latest transaction-local generation. Thus the
first event validates the final visible graph and later events for that
generation skip redundant work. A write after `SET CONSTRAINTS ALL IMMEDIATE`
increments the generation and, because the constraints remain immediate,
forces validation again in that statement.

PostgreSQL test 18 disables only the immutable trigger for UPDATE/DELETE
vectors and relies on `SET CONSTRAINTS ALL IMMEDIATE`; it no longer calls the
full verifier manually. It also validates a clean generation and then inserts
an extra Family-1 owner, proving the later generation cannot reuse the earlier
validation.

### T081-V4-S3A-F1-IA-002 — CLOSED

The expanded PostgreSQL matrix now covers changed owner/assertion/group values,
a valid alternate assertion union, optional-presence drift, member ordinal,
mapping context/provenance, a self-consistent changed mapping identity and
occurrence, evidence purpose and distinct binding-set substitution, semantic
hash and wrong-type drift, missing owners/mappings/evidence, cross-projection
parentage, extra evidence and mapping graphs, wrong-type duplicate owner, and
the post-validation later insert. These mutations exercise immediate CHECK/FK
rejection and automatic deferred set-equality rejection as appropriate.

The reconstruction endpoint matrix covers owner/group/member/assertion values,
valid alternate union state, mapping context/provenance, evidence purpose,
semantic hash, and missing/extra owner rows, with controlled HTTP 409 results.

The positive Family-1 fixture continues to cover 90 type/operator pairs, the
18 six-field known-string branches, four group associations, model and series
members, distinct occurrence/context evidence, and the 512-character boundary.

## Coordinator cross-wire candidate — REJECTED AS FIXED

The database global mapping validator explicitly joins the mapping semantic
node to the row's exact `source_occurrence_node_id` and requires:

- mapping-node parent and node key equal that occurrence ID;
- mapping-node pointer, canonical hash, and ordinal equal the occurrence;
- mapping and occurrence projection/proposal equal the mapping row; and
- mapping row ID/full hash recompute from the same kind and occurrence.

The ordinary semantic-node validator independently recomputes the mapping
node's deterministic ID and identity hash. A self-consistent mapping row cannot
therefore be cross-wired to another same-family occurrence while retaining the
old semantic owner. PostgreSQL test 18 includes the corresponding changed-ID,
changed-hash, changed-occurrence mutation and requires rejection.

No residual blocker was found in this bounded Family-1 closure review.
