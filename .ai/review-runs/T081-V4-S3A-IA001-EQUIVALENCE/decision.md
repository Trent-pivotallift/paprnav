# Decision: exact canonical graph plus typed relational views

Date: 2026-09-09  
Owner/builder: `/root`  
Parent finding: `T081-V4-S3A-IA-001`

## Objective and decision requested

Approve or reject an equivalence amendment for Slice 3A. Instead of persisting
fourteen additional mutable typed-owner copies, revision 0027 retains one exact,
immutable canonical datum/semantic graph and adds typed read-only relational
views for every approved owner/query shape. The amendment is acceptable only if
the database-enforced graph plus views provides guarantees at least as strong as
the original typed-table design. If this proof fails, implementation must use
the original physical typed tables.

The user-visible outcome is unchanged: bounded platform administrators can
materialize and audit candidate-only applicability. No released/customer read,
aircraft matching, legal supersession, compliance, due-state, or approval is
introduced.

## Non-negotiable safety and correctness invariants

1. A projection cannot commit unless its complete datum graph is exactly equal
   to the immutable validator-2 candidate's four-field applicability subtree.
2. Missing, extra, reordered, differently valued, cross-projection, or
   differently owned rows fail at deferred commit, including direct SQL.
3. Every semantic node's type, key, source pointer, parent, ordinal, canonical
   hash, and deterministic identity is recomputed from canonical candidate
   bytes. Synthetic designation-value and incoming-dependency nodes have
   separately closed derivations.
4. Evidence links bind exact candidate evidence rows and reconstruct each
   source object's canonical evidence-key set, order, purpose, and link hash.
5. Identity mappings retain exact occurrence and evidence-parent FKs and closed
   origin/state/reason/temporal rules. Equal strings at different occurrences
   never collapse.
6. Conditions and expressions remain unevaluated. No view or service computes a
   truth value, series/range membership, aircraft match, or legal current state.
7. Typed query consumers never parse display text or punctuation. Group/member,
   manufacturer/model/series, rule/ref, and exclusion relationships come only
   from canonical typed members and exact semantic occurrence pointers.
8. The datum table is an integrity/reconstruction representation, not a public
   query escape hatch. Typed research uses closed views; released readers remain
   absent.
9. Views are read-only and derive from immutable proposal/projection rows. They
   cannot drift, be partially populated, or introduce a second writer.
10. Downgrade drops views before helper functions/tables and retains occupied
    state refusal.

## Current behavior and why the initial implementation failed

The initial implementation had only a root-envelope INSERT trigger. Counts and
hashes were trusted, semantic identities were not recomputed, correction and
dependency graphs were application-only, and no typed query surface existed.
It was not equivalent; IA-001, IA-002, and IA-005 were valid.

The current implementation changes the premise: deferred constraint triggers
run for every Slice-3A table; recursive database reconstruction compares every
pointer, property, ordinal, kind, and scalar value to the immutable candidate;
semantic ownership/identity and datum nearest-owner identity are recomputed;
correction, evidence, dependency, event, and concurrency facts are checked at
commit and verified on reads; and PostgreSQL-native sorted AD locks cover
application and direct writers. The legal stored graph is therefore not
arbitrary JSON: its state set is exactly the validator-2 candidate projection
state set.

## Proposed design and equivalence proof

Let `C` be the immutable validator-2 proposal, `A(C)` its four-field
applicability subtree, `G` the stored datum/semantic/evidence graph, and `T_i`
an approved typed owner relation.

The deferred validator proves `G = F(A(C))`, where `F` is deterministic and
injective over every JSON node and approved synthetic occurrence. Exact
reconstruction proves `F^-1(G) = A(C)`. Validator-2 proves closed shapes, enums,
references, array policies, and acyclicity at the immutable boundary. Each typed
relation is then a deterministic relational projection `T_i = V_i(C,G)`. A view
cannot admit an invalid row independently: that would require invalid `C` or
`G != F(A(C))`, both rejected before commit.

This removes the second mutable state that physical typed owner tables would
create. The tradeoff is query cost, not semantic weakness; Slice 3A makes no
hot-path or matching-readiness claim.

## Closed typed view contract

Revision 0027 creates these non-updatable views. Every view includes projection
and proposal IDs, deterministic occurrence/semantic IDs, canonical ordinal when
applicable, and the typed columns below. No view exposes a generic JSON value.

- `ad_v4_candidate_app_value_assertions`: parent occurrence, field code,
  `known|unknown|not_applicable`, exact text, controlled reason, temporal kind.
- `ad_v4_candidate_app_product_scopes`: scope key, product role, manufacturer
  presence/source/mapping and independent model/serial/part presence.
- `ad_v4_candidate_app_designation_scopes`: product scope, field/scope kind,
  exact series expression, reason/temporal, fixed comparison/evaluation.
- `ad_v4_candidate_app_designation_values`: designation scope, exact source
  value, canonical ordinal, exact-occurrence mapping ID.
- `ad_v4_candidate_app_designation_ranges`: exact bounds/inclusivity/polarity,
  ordinal, fixed lexical comparator.
- `ad_v4_candidate_app_conditions`: key, type, operator, temporal basis,
  optional comparator/product-role/attribute-key presence/value and fixed
  `unevaluated/none`.
- `ad_v4_candidate_app_designation_groups` and
  `ad_v4_candidate_app_designation_group_members`: canonical keys, association,
  display/designation/expression, explicit manufacturer union,
  unknown/evaluation fields, ordinal, and mapping relation.
- `ad_v4_candidate_app_expressions` and
  `ad_v4_candidate_app_expression_edges`: owning rule, context, path, node type,
  typed scope/condition/rule refs, child sequence, result/evaluator contract.
- `ad_v4_candidate_app_rules` and
  `ad_v4_candidate_app_rule_exclusions`: rule key, scope/condition roots,
  condition presence, exclusion relation/ordinal, evaluator version.
- `ad_v4_candidate_app_search_hints`,
  `ad_v4_candidate_app_search_hint_groups`, and
  `ad_v4_candidate_app_search_hint_members`: source-faithful typed hint/group/
  member identity, manufacturer/model/series relationships, association,
  unknown/evaluation fields, mapping relation, and fixed noncontrolling flags.

Definitions use `jsonb_array_elements(... WITH ORDINALITY)`, closed property
selection, and joins to exact semantic nodes/identity mappings. They never infer
members from strings. Physical identity mappings, evidence links, corrections,
dependencies, and events remain tables because they add candidate-local audit
facts rather than merely expose a typed projection of canonical bytes.

## Trust, authorization, reads, and writes

Only the already-authorized, gated materialization POST creates projection
state. Database triggers enforce the same graph for direct SQL. Audit GETs are
detection-only. Views grant no new endpoint and are administrator-research
relations only. No provider, CLI, cron, worker, seed, V3 translator, generic
CRUD path, or released reader is added.

## Migration, compatibility, correction, and rollback

Views are additive and contain no backfill. Validator-1 rows have no Slice-3A
projection and therefore yield no rows. Correction and supersession foundations
retain their independently closed physical/audit contracts. Application rollback
disables routes while dual candidate readers remain. Physical downgrade refuses
occupied validator-2/Slice-3A state, then drops views before tables/functions.

## Test strategy and acceptance gates

- PostgreSQL catalog proof that every named view exists and is non-updatable.
- Five-packet row/cardinality checks, including 81/6/182/224/182 listed model
  occurrences and the 19-model plus one unevaluated series hint.
- Typed 2002 condition-group and manufacturer/model hint queries without display
  parsing, plus the 2024 all-members Garmin group.
- 90/90 condition type/operator rows as `unevaluated/none`.
- Expression edge sequence/root/ref and rule exclusion reconstruction.
- Existing candidate/deferred negatives for cross-projection ownership,
  reordered arrays, changed refs, and cycles.
- Search proving released/customer/V3 readers use neither datum table nor views.
- Exact whole-subtree reconstruction remains the authoritative read check.

## Alternatives considered

Physical typed tables remain the fallback. They provide cheaper indexed reads
but create fourteen more immutable row sets whose completeness and parity must
be enforced. JSON-only queries without closed views are rejected because they
do not provide the approved typed research contract. Deferring all typed query
shapes is rejected because IA-001 explicitly requires queryability.

## Expected file scope and known uncertainty

Expected implementation changes are migration 0027 and PostgreSQL/calibration
tests. Service/model changes are unnecessary unless a typed admin response is
added; no such response is proposed.

The principal uncertainty is whether read-only derived relations satisfy the
original phrase "typed owner row." Reviewers must judge guarantees rather than
storage preference and construct a specific committed-state or typed-query
counterexample. Any invariant that still depends only on application checks is
a blocker. If the exact/injective proof or any required typed relation fails,
this amendment is rejected and physical typed tables are required.
