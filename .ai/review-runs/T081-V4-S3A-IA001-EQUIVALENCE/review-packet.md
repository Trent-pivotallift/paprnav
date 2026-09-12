# Review packet: T081-V4-S3A-IA001-EQUIVALENCE

Stage: design
Generated: 2026-09-10T02:04:22+00:00
Base: `28f6be0`
Head: `28f6be0eab225abc4b68830345e04d6fb6df454f`
Scope fingerprint: `eb6f3fd11dbfc40571ec6931601c2682810c3a251a0473e4e30496b300e7caf4`

## Reviewer instructions

Read `.ai/agents/ADVERSARIAL_REVIEWER.md`. Inspect repository files directly.
Treat the manifest as a starting point and report missing consumers or unjustified
scope exclusions as findings.

## Decision packet

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


## Current finding ledger

```json
[]

```

## Hash-bound review inputs

### `.ai/review-runs/T081-V4-S3A-IA001-EQUIVALENCE/decision.md`

size=9830; sha256=08bf9a8ec53274dbdbbc1218a24e68d139b3e222af951e9ea5a5026baac554f5

```text
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

```
### `.ai/review-runs/T081-V4-S3A-IA001-EQUIVALENCE/findings.json`

size=3; sha256=37517e5f3dc66819f61f5a7bb8ace1921282415f10551d2defa5c3eb0985b570

```text
[]

```

## Changed-file manifest

```json
{
  "taskId": "T081-V4-S3A-IA001-EQUIVALENCE",
  "stage": "design",
  "generatedAt": "2026-09-10T02:04:22+00:00",
  "baseRef": "28f6be0",
  "head": "28f6be0eab225abc4b68830345e04d6fb6df454f",
  "scopePaths": [],
  "scopeFingerprint": "eb6f3fd11dbfc40571ec6931601c2682810c3a251a0473e4e30496b300e7caf4",
  "files": [
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-3A/CURRENT_CHECKPOINT.md",
      "status": "??",
      "size": 9035,
      "sha256": "ce5cd27e815b55317f01708f9e70f8c2c3b99e6b2f7bda76a233a44f0ce13ac0",
      "readStatus": "readable"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-3A/adversarial-design-closure-1.md",
      "status": "??",
      "size": 3714,
      "sha256": "4dc29c60271e0909275f816d3252f2691b1549e96abdcdb34d73c327580f4f45",
      "readStatus": "readable"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-3A/adversarial-design-closure-2.md",
      "status": "??",
      "size": 4222,
      "sha256": "b9524760acfb8632c681b05c0dd32e393d0c7ba89a4a751b93542115f9a2788f",
      "readStatus": "readable"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-3A/adversarial-design-initial.md",
      "status": "??",
      "size": 4487,
      "sha256": "b617aa132d2825d9140540f7d0d41f6d489bf67ec007c1997a5f3dd47a6c328d",
      "readStatus": "readable"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-3A/adversarial-external-critic-closure-1.md",
      "status": "??",
      "size": 4727,
      "sha256": "95d1931fa67301070cad10c7353a29843178d38bed669b44a6659043c111c054",
      "readStatus": "readable"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-3A/adversarial-implementation-ia002-ia005-closure.md",
      "status": "??",
      "size": 1402,
      "sha256": "12df90292e9c0c53764ca44289ae852ba0426440c54bc0344d3f572a0f35360c",
      "readStatus": "readable"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-3A/adversarial-implementation-ia003-closure.md",
      "status": "??",
      "size": 1916,
      "sha256": "8bc033f2545f85ec8dbb453b8599310e1897201d99466a5844df185fbd8c7b1e",
      "readStatus": "readable"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-3A/adversarial-implementation-ia004-closure.md",
      "status": "??",
      "size": 1005,
      "sha256": "8d985334209fe3eca35fbd228d7783aeff03e028fc041385e91f73a6d54b363f",
      "readStatus": "readable"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-3A/adversarial-implementation-initial.md",
      "status": "??",
      "size": 5127,
      "sha256": "6125935f42332e4bd4add0f15c09cf30fb62773ac8c0cfac1645adb8bd36fc76",
      "readStatus": "readable"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-3A/claude-external-critic-20260906T235706Z.findings.json",
      "status": "??",
      "size": 7255,
      "sha256": "077940e41ca6e0678f39e5e10a634d2ba25d63e354126eca4078250172c263dc",
      "readStatus": "readable"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-3A/claude-external-critic-20260906T235706Z.md",
      "status": "??",
      "size": 14994,
      "sha256": "0bee68926fcc21fa7dafb1a3cf06c239e3d91821710df8c19f54e4721d2289aa",
      "readStatus": "readable"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-3A/closure.md",
      "status": "??",
      "size": 217,
      "sha256": "a082505d61b0ad9d35647c1072f4f0d077223bf705d766bf60827bef6163361f",
      "readStatus": "readable"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-3A/decision.md",
      "status": "??",
      "size": 91684,
      "sha256": "50effad6a01fdb75a1d4594b170bed35f3c977464f4f83a81919793d553df466",
      "readStatus": "readable"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-3A/findings.json",
      "status": "??",
      "size": 51518,
      "sha256": "72d2441a64ca83bcad32e2358300ced5a4ba184bcd072ffb7518067fb83164d9",
      "readStatus": "readable"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-3A/implementation-slice-3a.md",
      "status": "??",
      "size": 5336,
      "sha256": "8b0e9c5f64ea267383c888046965fc6ea4240a5d4bb4d97ee28c516f30d83208",
      "readStatus": "readable"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-3A/latest",
      "status": "??",
      "size": 100452,
      "sha256": "5421f3b3dc6f6e061d55cc27d040d1b1090a1c21cd5edd50dfcb5bfb1a5b2d96",
      "readStatus": "readable"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-3A/manifest.json",
      "status": "??",
      "size": 3430,
      "sha256": "c0f543a203d6aae4fcc89c314c60c48bb96a3acb646c8020b7c19f0db9abd914",
      "readStatus": "readable"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-3A/review-packet.md",
      "status": "??",
      "size": 557352,
      "sha256": "a3084bacf0b883bbe3d1da74553671ab69635560de9a82ed9e3c1b64064e47cf",
      "readStatus": "readable"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-3A/reviews.json",
      "status": "??",
      "size": 2162,
      "sha256": "fed1d13b11caac1d5d5378a4f106265f64fe9cafb30313473d3313f85f373a31",
      "readStatus": "readable"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-3A/state.json",
      "status": "??",
      "size": 62,
      "sha256": "857a5e9aa8f0011d71f451bfa2c8160002ffa4ca02d2ebffe4a6ccabe9a589b3",
      "readStatus": "readable"
    },
    {
      "path": "backend/app/api/routes/ads.py",
      "status": " M",
      "size": 70840,
      "sha256": "c19bbf01d2ce4a479a162922702f2626668ada382c440d5d9cbd4f4f38cd2385",
      "readStatus": "readable"
    },
    {
      "path": "backend/app/core/config.py",
      "status": " M",
      "size": 7979,
      "sha256": "d285cc55e960d5f740278b9a5ef5f87e47ba8c80eaa3e453474fc9119bc635e7",
      "readStatus": "readable"
    },
    {
      "path": "backend/app/db/migrations/versions/20260907_0027_add_ad_v4_applicability.py",
      "status": "??",
      "size": 82407,
      "sha256": "26968c0697bf5021de5e8c11888c254f07934815184407d0a56a87deec95f660",
      "readStatus": "readable"
    },
    {
      "path": "backend/app/models/core.py",
      "status": " M",
      "size": 113180,
      "sha256": "bfecfab846338278709c36ea429a92dfd0147c8cdf28ad3e0bb5a7dfa34c6f02",
      "readStatus": "readable"
    },
    {
      "path": "backend/app/schemas/ads.py",
      "status": " M",
      "size": 10462,
      "sha256": "7f19a3219e4bd483df7249a444ad485c38c6d72fb80451876ee1d2018bf1b4fa",
      "readStatus": "readable"
    },
    {
      "path": "backend/app/services/ad_v4_applicability.py",
      "status": "??",
      "size": 58050,
      "sha256": "7b31dca53a704446c92f193ec5c8537fd7d442f7bef89b916257e4769257c0d3",
      "readStatus": "readable"
    },
    {
      "path": "backend/app/services/ad_v4_candidates.py",
      "status": " M",
      "size": 69544,
      "sha256": "0f888f836a0e9782264e3791d7409ba68f3f5b58679662eeed07744ca093ee55",
      "readStatus": "readable"
    },
    {
      "path": "backend/tests/test_ad_v4_applicability.py",
      "status": "??",
      "size": 13437,
      "sha256": "31ee8d71b596673408b1be13e8488d128093843bf5e6db9dfe54be98c2b118b9",
      "readStatus": "readable"
    },
    {
      "path": "backend/tests/test_ad_v4_applicability_calibration.py",
      "status": "??",
      "size": 13708,
      "sha256": "74bd5aacc1164e9c5c928645e30c965d56267e50c6ff5306748f9410ba2affa9",
      "readStatus": "readable"
    },
    {
      "path": "backend/tests/test_ad_v4_applicability_postgres.py",
      "status": "??",
      "size": 27935,
      "sha256": "3e300ebeb4c192c1a3ee4f1fb79314321acda34bf5f42bb2f87a41887d8ccbe0",
      "readStatus": "readable"
    },
    {
      "path": "backend/tests/test_ad_v4_postgres.py",
      "status": " M",
      "size": 42190,
      "sha256": "d78c799679e2c007a8be07c05437f8c18865149edb6c3dbbad59bb03c82ff892",
      "readStatus": "readable"
    }
  ],
  "reviewInputs": [
    {
      "path": ".ai/review-runs/T081-V4-S3A-IA001-EQUIVALENCE/decision.md",
      "status": "review_input",
      "size": 9830,
      "sha256": "08bf9a8ec53274dbdbbc1218a24e68d139b3e222af951e9ea5a5026baac554f5",
      "readStatus": "readable"
    },
    {
      "path": ".ai/review-runs/T081-V4-S3A-IA001-EQUIVALENCE/findings.json",
      "status": "review_input",
      "size": 3,
      "sha256": "37517e5f3dc66819f61f5a7bb8ace1921282415f10551d2defa5c3eb0985b570",
      "readStatus": "readable"
    }
  ],
  "outOfScopeDirtyFiles": [],
  "outOfScopeReason": null
}
```

## Diff against base

```diff
diff --git a/backend/app/api/routes/ads.py b/backend/app/api/routes/ads.py
index 13a48d3..497b246 100644
--- a/backend/app/api/routes/ads.py
+++ b/backend/app/api/routes/ads.py
@@ -32,6 +32,8 @@ from app.models.core import (
     ADMatchResult,
     ADTargetApplicability,
     ADV4CandidateProposal,
+    ADV4CandidateAppMaterializationRequest,
+    ADV4CandidateAppProjection,
     ADV4CandidateSubmission,
     AircraftADDueState,
     AirworthinessDirective,
@@ -49,6 +51,9 @@ from app.schemas.ads import (
     ADEvidenceFragmentResponse,
     ADV4CandidateListResponse,
     ADV4CandidateResponse,
+    ADV4ApplicabilityProjectionListResponse,
+    ADV4ApplicabilityProjectionResponse,
+    ADV4ApplicabilityReconstructionResponse,
     ADV4SubmissionAuditResponse,
     ADV4SubmissionRelationshipAuditResponse,
     ADProposalProvenanceResponse,
@@ -113,6 +118,14 @@ from app.services.ad_v4_candidates import (
     verified_candidate,
     verified_submission,
 )
+from app.services.ad_v4_applicability import (
+    POLICY_VERSION as APP_PROJECTION_POLICY_VERSION,
+    authorize_projection_audit,
+    materialize_applicability,
+    projection_state,
+    reconstruct_applicability,
+    verified_app_projection,
+)
 from app.services.ad_recurrence import due_state_payload
 from app.services.installed_components import component_display_name
 from app.services.observability import record_product_event, record_workflow_status
@@ -405,6 +418,148 @@ def get_v4_candidate_proposal(
         raise v4_http_error(exc) from exc
 
 
+def serialize_v4_app_projection(
+    db: Session,
+    projection: ADV4CandidateAppProjection,
+    *,
+    acting_membership_id: str,
+    request_row: ADV4CandidateAppMaterializationRequest | None = None,
+    created: bool = False,
+    idempotent_retry: bool = False,
+) -> ADV4ApplicabilityProjectionResponse:
+    state_value, reasons = projection_state(db, projection)
+    return ADV4ApplicabilityProjectionResponse(
+        projectionId=projection.id,
+        proposalId=projection.proposal_id,
+        directiveId=projection.directive_id,
+        validatorVersion=projection.validator_version,
+        canonicalizationVersion=projection.canonicalization_version,
+        materializerVersion=projection.materializer_version,
+        proposalCanonicalHash=projection.proposal_canonical_hash,
+        evidenceBindingHash=projection.evidence_binding_hash,
+        applicabilitySubtreeHash=projection.applicability_subtree_hash,
+        projectionHash=projection.projection_hash,
+        gate=projection.gate,
+        projectionState=state_value,
+        stateReasons=reasons,
+        semanticNodeCount=projection.semantic_node_count,
+        datumCount=projection.datum_count,
+        evidenceLinkCount=projection.evidence_link_count,
+        identityMappingCount=projection.identity_mapping_count,
+        requestId=request_row.id if request_row else None,
+        created=created,
+        idempotentRetry=idempotent_retry,
+        actingMembershipId=acting_membership_id,
+        authPolicyVersion=APP_PROJECTION_POLICY_VERSION,
+        createdAt=projection.created_at,
+    )
+
+
+@router.post(
+    "/directives/{directive_id}/v4/candidate-proposals/{proposal_id}/applicability-projection",
+    response_model=ADV4ApplicabilityProjectionResponse,
+    status_code=status.HTTP_201_CREATED,
+)
+def create_v4_applicability_projection(
+    directive_id: str,
+    proposal_id: str,
+    response: Response,
+    idempotency_key: str = Header(alias="Idempotency-Key", min_length=1, max_length=255),
+    acting_membership_id: str = Header(alias="Paprnav-Acting-Membership-Id", min_length=1, max_length=36),
+    current_user: User = Depends(get_current_user),
+    db: Session = Depends(get_db),
+) -> ADV4ApplicabilityProjectionResponse:
+    try:
+        result = materialize_applicability(
+            db, directive_id=directive_id, proposal_id=proposal_id,
+            actor=current_user, membership_id=acting_membership_id,
+            idempotency_key=idempotency_key,
+        )
+        db.commit()
+        db.refresh(result.projection)
+        db.refresh(result.request)
+        if not result.created:
+            response.status_code = status.HTTP_200_OK
+        return serialize_v4_app_projection(
+            db, result.projection, acting_membership_id=acting_membership_id,
+            request_row=result.request, created=result.created,
+            idempotent_retry=result.idempotent_retry,
+        )
+    except ADV4Error as exc:
+        db.rollback()
+        raise v4_http_error(exc) from exc
+
+
+@router.get(
+    "/directives/{directive_id}/v4/candidate-proposals/{proposal_id}/applicability-projection",
+    response_model=ADV4ApplicabilityProjectionResponse,
+)
+def get_v4_applicability_projection(
+    directive_id: str,
+    proposal_id: str,
+    acting_membership_id: str = Header(alias="Paprnav-Acting-Membership-Id", min_length=1, max_length=36),
+    current_user: User = Depends(get_current_user),
+    db: Session = Depends(get_db),
+) -> ADV4ApplicabilityProjectionResponse:
+    try:
+        authorize_projection_audit(db, current_user, acting_membership_id)
+        projection = verified_app_projection(db, directive_id=directive_id, proposal_id=proposal_id)
+        return serialize_v4_app_projection(db, projection, acting_membership_id=acting_membership_id)
+    except ADV4Error as exc:
+        db.rollback()
+        raise v4_http_error(exc) from exc
+
+
+@router.get(
+    "/directives/{directive_id}/v4/candidate-proposals/{proposal_id}/applicability-projection/reconstruction",
+    response_model=ADV4ApplicabilityReconstructionResponse,
+)
+def get_v4_applicability_reconstruction(
+    directive_id: str,
+    proposal_id: str,
+    acting_membership_id: str = Header(alias="Paprnav-Acting-Membership-Id", min_length=1, max_length=36),
+    current_user: User = Depends(get_current_user),
+    db: Session = Depends(get_db),
+) -> ADV4ApplicabilityReconstructionResponse:
+    try:
+        authorize_projection_audit(db, current_user, acting_membership_id)
+        projection = verified_app_projection(db, directive_id=directive_id, proposal_id=proposal_id)
+        subtree = reconstruct_applicability(db, projection)
+        return ADV4ApplicabilityReconstructionResponse(
+            projectionId=projection.id, proposalId=projection.proposal_id,
+            directiveId=projection.directive_id, gate=projection.gate,
+            applicabilitySubtreeHash=projection.applicability_subtree_hash,
+            projectionHash=projection.projection_hash,
+            canonicalApplicability=subtree,
+            actingMembershipId=acting_membership_id,
+            authPolicyVersion=APP_PROJECTION_POLICY_VERSION,
+        )
+    except ADV4Error as exc:
+        db.rollback()
+        raise v4_http_error(exc) from exc
+
+
+@router.get(
+    "/directives/{directive_id}/v4/applicability-projections",
+    response_model=ADV4ApplicabilityProjectionListResponse,
+)
+def list_v4_applicability_projections(
+    directive_id: str,
+    limit: int = Query(default=50, ge=1, le=100),
+    offset: int = Query(default=0, ge=0),
+    acting_membership_id: str = Header(alias="Paprnav-Acting-Membership-Id", min_length=1, max_length=36),
+    current_user: User = Depends(get_current_user),
+    db: Session = Depends(get_db),
+) -> ADV4ApplicabilityProjectionListResponse:
+    try:
+        authorize_projection_audit(db, current_user, acting_membership_id)
+        total = db.scalar(select(func.count()).select_from(ADV4CandidateAppProjection).where(ADV4CandidateAppProjection.directive_id == directive_id)) or 0
+        rows = db.scalars(select(ADV4CandidateAppProjection).where(ADV4CandidateAppProjection.directive_id == directive_id).order_by(ADV4CandidateAppProjection.created_at.desc(), ADV4CandidateAppProjection.id.desc()).offset(offset).limit(limit)).all()
+        responses = [serialize_v4_app_projection(db, row, acting_membership_id=acting_membership_id) for row in rows]
+        return ADV4ApplicabilityProjectionListResponse(projections=responses, count=len(responses), total=total, limit=limit, offset=offset)
+    except ADV4Error as exc:
+        db.rollback()
+        raise v4_http_error(exc) from exc
 @router.get(
     "/source-documents/{source_document_id}/pages/{page_number}",
     response_model=ADSourcePageEvidenceResponse,
diff --git a/backend/app/core/config.py b/backend/app/core/config.py
index c07a4d6..0a5c0f3 100644
--- a/backend/app/core/config.py
+++ b/backend/app/core/config.py
@@ -82,6 +82,14 @@ class Settings:
     govinfo_api_key: Optional[str]
     govinfo_base_url: str
     drs_max_snapshot_age_days: int = 7
+    ad_v4_validator2_writes_enabled: bool = False
+    ad_v4_slice3a_routes_enabled: bool = False
+
+
+def parse_bool(value: Optional[str], default: bool = False) -> bool:
+    if value is None:
+        return default
+    return value.strip().lower() in {"1", "true", "yes", "on"}
 
 
 @lru_cache
@@ -170,4 +178,10 @@ def get_settings() -> Settings:
         drs_max_snapshot_age_days=int(
             os.getenv("PAPRNAV_DRS_MAX_SNAPSHOT_AGE_DAYS", "7")
         ),
+        ad_v4_validator2_writes_enabled=parse_bool(
+            os.getenv("PAPRNAV_AD_V4_VALIDATOR2_WRITES_ENABLED")
+        ),
+        ad_v4_slice3a_routes_enabled=parse_bool(
+            os.getenv("PAPRNAV_AD_V4_SLICE3A_ROUTES_ENABLED")
+        ),
     )
diff --git a/backend/app/models/core.py b/backend/app/models/core.py
index f81803f..9da3fbd 100644
--- a/backend/app/models/core.py
+++ b/backend/app/models/core.py
@@ -3,7 +3,7 @@ from datetime import date as PythonDate
 from decimal import Decimal
 from typing import Optional
 
-from sqlalchemy import BigInteger, Boolean, CheckConstraint, Date, DateTime, Float, ForeignKey, ForeignKeyConstraint, Index, Integer, JSON, LargeBinary, Numeric, String, Text, UniqueConstraint, func
+from sqlalchemy import BigInteger, Boolean, CheckConstraint, Date, DateTime, Float, ForeignKey, ForeignKeyConstraint, Index, Integer, JSON, LargeBinary, Numeric, String, Text, UniqueConstraint, func, text
 from sqlalchemy.orm import Mapped, mapped_column, relationship
 
 from app.db.base import Base
@@ -819,6 +819,8 @@ class ADV4CandidateEvidenceBinding(Base):
     fragment_hash: Mapped[str] = mapped_column(String(64), nullable=False)
     admitted_event_id: Mapped[str] = mapped_column(ForeignKey("ad_evidence_fragment_lifecycle_events.id"), nullable=False)
     admitted_event_hash: Mapped[str] = mapped_column(String(64), nullable=False)
+    validator_version: Mapped[str] = mapped_column(String(64), nullable=False, default="paprnav-ad-v4-validator-1")
+    canonicalization_version: Mapped[str] = mapped_column(String(64), nullable=False, default="paprnav-ad-v4-c14n-1")
     created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
 
 
@@ -851,6 +853,8 @@ class ADV4CandidateSubmission(Base):
     request_hash: Mapped[str] = mapped_column(String(64), nullable=False)
     request_canonical_bytes: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
     raw_transport_hash: Mapped[str] = mapped_column(String(64), nullable=False)
+    validator_version: Mapped[str] = mapped_column(String(64), nullable=False, default="paprnav-ad-v4-validator-1")
+    canonicalization_version: Mapped[str] = mapped_column(String(64), nullable=False, default="paprnav-ad-v4-c14n-1")
     created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
 
 
@@ -873,6 +877,8 @@ class ADV4CandidateSubmissionRelationship(Base):
     evidence_keys: Mapped[list] = mapped_column(JSON, nullable=False)
     canonical_bytes: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
     relationship_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
+    validator_version: Mapped[str] = mapped_column(String(64), nullable=False, default="paprnav-ad-v4-validator-1")
+    canonicalization_version: Mapped[str] = mapped_column(String(64), nullable=False, default="paprnav-ad-v4-c14n-1")
     created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
 
 
@@ -895,6 +901,302 @@ class ADV4CandidateProposalEvent(Base):
     predecessor_event_hash: Mapped[str] = mapped_column(String(64), nullable=True)
     canonical_bytes: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
     event_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
+    validator_version: Mapped[str] = mapped_column(String(64), nullable=False, default="paprnav-ad-v4-validator-1")
+    canonicalization_version: Mapped[str] = mapped_column(String(64), nullable=False, default="paprnav-ad-v4-c14n-1")
+    occurred_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
+
+
+class ADV4FeatureGate(Base):
+    __tablename__ = "ad_v4_feature_gates"
+
+    gate_key: Mapped[str] = mapped_column(String(64), primary_key=True)
+    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
+    changed_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
+    changed_by: Mapped[str] = mapped_column(String(128), nullable=False, default="migration")
+
+
+class ADV4CandidateAppProjection(Base):
+    __tablename__ = "ad_v4_candidate_app_projections"
+    __table_args__ = (
+        CheckConstraint("gate = 'candidate_only'", name="ck_ad_v4_app_projection_gate"),
+        UniqueConstraint("proposal_id", "materializer_version", name="uq_ad_v4_app_projection_parent"),
+        UniqueConstraint("identity_hash", name="uq_ad_v4_app_projection_identity"),
+    )
+
+    id: Mapped[str] = mapped_column(String(36), primary_key=True)
+    identity_hash: Mapped[str] = mapped_column(String(64), nullable=False)
+    proposal_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_proposals.id"), nullable=False, index=True)
+    directive_id: Mapped[str] = mapped_column(ForeignKey("airworthiness_directives.id"), nullable=False)
+    schema_version: Mapped[str] = mapped_column(String(64), nullable=False)
+    validator_version: Mapped[str] = mapped_column(String(64), nullable=False)
+    canonicalization_version: Mapped[str] = mapped_column(String(64), nullable=False)
+    proposal_canonical_hash: Mapped[str] = mapped_column(String(64), nullable=False)
+    evidence_binding_hash: Mapped[str] = mapped_column(String(64), nullable=False)
+    materializer_version: Mapped[str] = mapped_column(String(64), nullable=False)
+    applicability_subtree_bytes: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
+    applicability_subtree_hash: Mapped[str] = mapped_column(String(64), nullable=False)
+    projection_canonical_bytes: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
+    projection_hash: Mapped[str] = mapped_column(String(64), nullable=False)
+    gate: Mapped[str] = mapped_column(String(32), nullable=False, default="candidate_only")
+    semantic_node_count: Mapped[int] = mapped_column(Integer, nullable=False)
+    datum_count: Mapped[int] = mapped_column(Integer, nullable=False)
+    evidence_link_count: Mapped[int] = mapped_column(Integer, nullable=False)
+    identity_mapping_count: Mapped[int] = mapped_column(Integer, nullable=False)
+    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
+
+
+class ADV4CandidateAppMaterializationRequest(Base):
+    __tablename__ = "ad_v4_candidate_app_materialization_requests"
+    __table_args__ = (
+        CheckConstraint("actor_role = 'platform_admin'", name="ck_ad_v4_app_request_role"),
+        CheckConstraint("actor_status = 'active'", name="ck_ad_v4_app_request_status"),
+        UniqueConstraint(
+            "actor_user_id", "authorizing_membership_id", "endpoint_action",
+            "auth_policy_version", "idempotency_key", name="uq_ad_v4_app_request_idempotency",
+        ),
+    )
+
+    id: Mapped[str] = mapped_column(String(36), primary_key=True)
+    projection_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_app_projections.id"), nullable=False, index=True)
+    proposal_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_proposals.id"), nullable=False)
+    directive_id: Mapped[str] = mapped_column(ForeignKey("airworthiness_directives.id"), nullable=False)
+    actor_user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
+    authorizing_membership_id: Mapped[str] = mapped_column(ForeignKey("organization_memberships.id"), nullable=False)
+    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"), nullable=False)
+    actor_role: Mapped[str] = mapped_column(String(64), nullable=False)
+    actor_status: Mapped[str] = mapped_column(String(32), nullable=False)
+    auth_policy_name: Mapped[str] = mapped_column(String(96), nullable=False)
+    auth_policy_version: Mapped[str] = mapped_column(String(64), nullable=False)
+    auth_claims_hash: Mapped[str] = mapped_column(String(64), nullable=False)
+    endpoint_action: Mapped[str] = mapped_column(String(96), nullable=False)
+    idempotency_key: Mapped[str] = mapped_column(String(255), nullable=False)
+    request_canonical_bytes: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
+    request_hash: Mapped[str] = mapped_column(String(64), nullable=False)
+    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
+
+
+class ADV4CandidateAppSemanticNode(Base):
+    __tablename__ = "ad_v4_candidate_app_semantic_nodes"
+    __table_args__ = (
+        UniqueConstraint("projection_id", "node_type", "node_key", name="uq_ad_v4_app_node_key"),
+        UniqueConstraint("identity_hash", name="uq_ad_v4_app_node_identity"),
+    )
+
+    id: Mapped[str] = mapped_column(String(36), primary_key=True)
+    identity_hash: Mapped[str] = mapped_column(String(64), nullable=False)
+    projection_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_app_projections.id"), nullable=False, index=True)
+    proposal_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_proposals.id"), nullable=False)
+    parent_node_id: Mapped[Optional[str]] = mapped_column(ForeignKey("ad_v4_candidate_app_semantic_nodes.id"), nullable=True)
+    node_type: Mapped[str] = mapped_column(String(64), nullable=False)
+    node_key: Mapped[str] = mapped_column(String(255), nullable=False)
+    source_pointer: Mapped[str] = mapped_column(Text, nullable=False)
+    canonical_node_hash: Mapped[str] = mapped_column(String(64), nullable=False)
+    canonical_ordinal: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
+    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
+
+
+class ADV4CandidateAppDatum(Base):
+    """Closed scalar/container projection used for byte-exact subtree reconstruction."""
+
+    __tablename__ = "ad_v4_candidate_app_data"
+    __table_args__ = (
+        CheckConstraint("value_kind IN ('object','array','string','boolean')", name="ck_ad_v4_app_datum_kind"),
+        UniqueConstraint("projection_id", "json_pointer", name="uq_ad_v4_app_datum_pointer"),
+    )
+
+    id: Mapped[str] = mapped_column(String(36), primary_key=True)
+    projection_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_app_projections.id"), nullable=False, index=True)
+    proposal_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_proposals.id"), nullable=False)
+    semantic_node_id: Mapped[Optional[str]] = mapped_column(ForeignKey("ad_v4_candidate_app_semantic_nodes.id"), nullable=True)
+    json_pointer: Mapped[str] = mapped_column(Text, nullable=False)
+    parent_pointer: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
+    property_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
+    array_ordinal: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
+    value_kind: Mapped[str] = mapped_column(String(16), nullable=False)
+    string_value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
+    boolean_value: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
+    value_hash: Mapped[str] = mapped_column(String(64), nullable=False)
+
+
+class ADV4CandidateAppEvidenceLink(Base):
+    __tablename__ = "ad_v4_candidate_app_evidence_links"
+    __table_args__ = (
+        UniqueConstraint("semantic_node_id", "purpose", "evidence_key", name="uq_ad_v4_app_evidence_link"),
+    )
+
+    id: Mapped[str] = mapped_column(String(36), primary_key=True)
+    projection_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_app_projections.id"), nullable=False, index=True)
+    proposal_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_proposals.id"), nullable=False)
+    semantic_node_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_app_semantic_nodes.id"), nullable=False)
+    candidate_binding_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_evidence_bindings.id"), nullable=False)
+    evidence_key: Mapped[str] = mapped_column(String(128), nullable=False)
+    purpose: Mapped[str] = mapped_column(String(64), nullable=False)
+    canonical_ordinal: Mapped[int] = mapped_column(Integer, nullable=False)
+    link_hash: Mapped[str] = mapped_column(String(64), nullable=False)
+
+
+class ADV4CandidateAppIdentityMapping(Base):
+    __tablename__ = "ad_v4_candidate_app_identity_mappings"
+    __table_args__ = (
+        CheckConstraint("review_state = 'unreviewed_candidate'", name="ck_ad_v4_app_identity_review"),
+        UniqueConstraint("projection_id", "identity_kind", "source_occurrence_node_id", name="uq_ad_v4_app_identity_occurrence"),
+    )
+
+    id: Mapped[str] = mapped_column(String(36), primary_key=True)
+    projection_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_app_projections.id"), nullable=False, index=True)
+    proposal_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_proposals.id"), nullable=False)
+    source_occurrence_node_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_app_semantic_nodes.id"), nullable=False)
+    evidence_parent_node_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_app_semantic_nodes.id"), nullable=False)
+    identity_kind: Mapped[str] = mapped_column(String(32), nullable=False)
+    source_value: Mapped[str] = mapped_column(Text, nullable=False)
+    normalization_origin: Mapped[str] = mapped_column(String(64), nullable=False)
+    normalized_state: Mapped[str] = mapped_column(String(32), nullable=False)
+    normalized_value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
+    reason: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
+    temporal_scope: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
+    normalization_namespace: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
+    normalization_version: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
+    review_state: Mapped[str] = mapped_column(String(32), nullable=False, default="unreviewed_candidate")
+    identity_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
+
+
+class ADV4CandidateCorrection(Base):
+    __tablename__ = "ad_v4_candidate_corrections"
+    __table_args__ = (
+        CheckConstraint("canonical_ordinal >= 0", name="ck_ad_v4_correction_ordinal_nonnegative"),
+        UniqueConstraint("proposal_id", "correction_key", name="uq_ad_v4_correction_key"),
+        UniqueConstraint("proposal_id", "canonical_ordinal", name="uq_ad_v4_correction_ordinal"),
+    )
+
+    id: Mapped[str] = mapped_column(String(36), primary_key=True)
+    identity_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
+    proposal_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_proposals.id"), nullable=False, index=True)
+    correction_key: Mapped[str] = mapped_column(String(128), nullable=False)
+    correction_type: Mapped[str] = mapped_column(String(64), nullable=False)
+    original_document_ref_key: Mapped[str] = mapped_column(String(128), nullable=False)
+    correcting_document_ref_key: Mapped[str] = mapped_column(String(128), nullable=False)
+    original_document_identity_hash: Mapped[str] = mapped_column(String(64), nullable=False)
+    correcting_document_identity_hash: Mapped[str] = mapped_column(String(64), nullable=False)
+    canonical_hash: Mapped[str] = mapped_column(String(64), nullable=False)
+    canonical_ordinal: Mapped[int] = mapped_column(Integer, nullable=False)
+    foundation_version: Mapped[str] = mapped_column(String(64), nullable=False)
+    generation: Mapped[int] = mapped_column(Integer, nullable=False)
+    expected_ref_count: Mapped[int] = mapped_column(Integer, nullable=False)
+    expected_evidence_count: Mapped[int] = mapped_column(Integer, nullable=False)
+
+
+class ADV4CandidateCorrectionRef(Base):
+    __tablename__ = "ad_v4_candidate_correction_refs"
+    __table_args__ = (
+        CheckConstraint("canonical_ordinal >= 0", name="ck_ad_v4_correction_ref_ordinal_nonnegative"),
+        UniqueConstraint("correction_id", "namespace", "semantic_key", name="uq_ad_v4_correction_ref_key"),
+        UniqueConstraint("correction_id", "canonical_ordinal", name="uq_ad_v4_correction_ref_ordinal"),
+    )
+
+    id: Mapped[str] = mapped_column(String(36), primary_key=True)
+    correction_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_corrections.id"), nullable=False, index=True)
+    proposal_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_proposals.id"), nullable=False)
+    canonical_ordinal: Mapped[int] = mapped_column(Integer, nullable=False)
+    namespace: Mapped[str] = mapped_column(String(64), nullable=False)
+    semantic_key: Mapped[str] = mapped_column(String(128), nullable=False)
+    owner_slice: Mapped[str] = mapped_column(String(32), nullable=False)
+    reference_hash: Mapped[str] = mapped_column(String(64), nullable=False)
+
+
+class ADV4CandidateCorrectionSemanticBinding(Base):
+    __tablename__ = "ad_v4_candidate_correction_semantic_bindings"
+
+    id: Mapped[str] = mapped_column(String(36), primary_key=True)
+    correction_ref_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_correction_refs.id"), nullable=False, unique=True)
+    proposal_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_proposals.id"), nullable=False)
+    projection_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_app_projections.id"), nullable=False)
+    semantic_node_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_app_semantic_nodes.id"), nullable=False)
+    binding_slice: Mapped[str] = mapped_column(String(32), nullable=False)
+    generation: Mapped[int] = mapped_column(Integer, nullable=False)
+    binding_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
+
+
+class ADV4CandidateCorrectionEvidenceLink(Base):
+    __tablename__ = "ad_v4_candidate_correction_evidence_links"
+    __table_args__ = (
+        CheckConstraint("canonical_ordinal >= 0", name="ck_ad_v4_correction_evidence_ordinal_nonnegative"),
+        UniqueConstraint("correction_id", "evidence_key", name="uq_ad_v4_correction_evidence"),
+        UniqueConstraint("correction_id", "canonical_ordinal", name="uq_ad_v4_correction_evidence_ordinal"),
+    )
+
+    id: Mapped[str] = mapped_column(String(36), primary_key=True)
+    correction_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_corrections.id"), nullable=False, index=True)
+    proposal_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_proposals.id"), nullable=False)
+    candidate_binding_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_evidence_bindings.id"), nullable=False)
+    evidence_key: Mapped[str] = mapped_column(String(128), nullable=False)
+    canonical_ordinal: Mapped[int] = mapped_column(Integer, nullable=False)
+    link_hash: Mapped[str] = mapped_column(String(64), nullable=False)
+
+
+class ADV4CandidateAppChangeDependency(Base):
+    __tablename__ = "ad_v4_candidate_app_change_dependencies"
+    __table_args__ = (
+        CheckConstraint(
+            "dependency_kind IN ('outgoing_supersedes','outgoing_partially_supersedes','incoming_supersession_signal')",
+            name="ck_ad_v4_app_dependency_kind",
+        ),
+        UniqueConstraint("id", "projection_id", name="uq_ad_v4_app_dependency_parent_identity"),
+        UniqueConstraint("projection_id", "dependency_key", name="uq_ad_v4_app_dependency"),
+    )
+
+    id: Mapped[str] = mapped_column(String(36), primary_key=True)
+    projection_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_app_projections.id"), nullable=False, index=True)
+    proposal_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_proposals.id"), nullable=False)
+    semantic_node_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_app_semantic_nodes.id"), nullable=False)
+    dependency_key: Mapped[str] = mapped_column(String(255), nullable=False)
+    dependency_kind: Mapped[str] = mapped_column(String(64), nullable=False)
+    predecessor_ad_number: Mapped[str] = mapped_column(String(64), nullable=False)
+    successor_ad_number: Mapped[str] = mapped_column(String(64), nullable=False)
+    resolution_state: Mapped[str] = mapped_column(String(32), nullable=False)
+    unresolved_reason: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
+    target_projection_id: Mapped[Optional[str]] = mapped_column(ForeignKey("ad_v4_candidate_app_projections.id"), nullable=True)
+    source_dependency_id: Mapped[Optional[str]] = mapped_column(ForeignKey("ad_v4_candidate_app_change_dependencies.id"), nullable=True)
+    dependency_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
+
+
+class ADV4CandidateAppProjectionEvent(Base):
+    __tablename__ = "ad_v4_candidate_app_projection_events"
+    __table_args__ = (
+        ForeignKeyConstraint(
+            ["causing_dependency_id", "projection_id"],
+            ["ad_v4_candidate_app_change_dependencies.id", "ad_v4_candidate_app_change_dependencies.projection_id"],
+            name="fk_ad_v4_app_event_same_projection_dependency",
+        ),
+        UniqueConstraint("projection_id", "sequence_number", name="uq_ad_v4_app_event_sequence"),
+        UniqueConstraint("projection_id", "event_hash", name="uq_ad_v4_app_event_hash"),
+        Index(
+            "uq_ad_v4_app_event_dependency_cause", "projection_id", "event_type", "causing_dependency_id",
+            unique=True, postgresql_where=text("causing_dependency_id IS NOT NULL"),
+        ),
+        Index(
+            "uq_ad_v4_app_event_relationship_cause", "projection_id", "event_type", "causing_relationship_id",
+            unique=True, postgresql_where=text("causing_relationship_id IS NOT NULL"),
+        ),
+        Index(
+            "uq_ad_v4_app_event_lifecycle_cause", "projection_id", "event_type", "causing_lifecycle_event_id",
+            unique=True, postgresql_where=text("causing_lifecycle_event_id IS NOT NULL"),
+        ),
+    )
+
+    id: Mapped[str] = mapped_column(String(36), primary_key=True)
+    projection_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_app_projections.id"), nullable=False, index=True)
+    proposal_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_proposals.id"), nullable=False)
+    sequence_number: Mapped[int] = mapped_column(Integer, nullable=False)
+    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
+    reason_code: Mapped[str] = mapped_column(String(64), nullable=False)
+    causing_request_id: Mapped[Optional[str]] = mapped_column(ForeignKey("ad_v4_candidate_app_materialization_requests.id"), nullable=True)
+    causing_relationship_id: Mapped[Optional[str]] = mapped_column(ForeignKey("ad_v4_candidate_submission_relationships.id"), nullable=True)
+    causing_lifecycle_event_id: Mapped[Optional[str]] = mapped_column(ForeignKey("ad_evidence_fragment_lifecycle_events.id"), nullable=True)
+    causing_dependency_id: Mapped[Optional[str]] = mapped_column(ForeignKey("ad_v4_candidate_app_change_dependencies.id"), nullable=True)
+    predecessor_event_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
+    canonical_bytes: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
+    event_hash: Mapped[str] = mapped_column(String(64), nullable=False)
+    actor_kind: Mapped[str] = mapped_column(String(32), nullable=False)
     occurred_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
 
 
diff --git a/backend/app/schemas/ads.py b/backend/app/schemas/ads.py
index b56ea19..fd7bf26 100644
--- a/backend/app/schemas/ads.py
+++ b/backend/app/schemas/ads.py
@@ -191,6 +191,52 @@ class ADV4CandidateListResponse(BaseModel):
     offset: int
 
 
+class ADV4ApplicabilityProjectionResponse(BaseModel):
+    projectionId: str
+    proposalId: str
+    directiveId: str
+    validatorVersion: str
+    canonicalizationVersion: str
+    materializerVersion: str
+    proposalCanonicalHash: str
+    evidenceBindingHash: str
+    applicabilitySubtreeHash: str
+    projectionHash: str
+    gate: str
+    projectionState: str
+    stateReasons: list[str]
+    semanticNodeCount: int
+    datumCount: int
+    evidenceLinkCount: int
+    identityMappingCount: int
+    requestId: Optional[str] = None
+    created: bool = False
+    idempotentRetry: bool = False
+    actingMembershipId: str
+    authPolicyVersion: str
+    createdAt: datetime
+
+
+class ADV4ApplicabilityProjectionListResponse(BaseModel):
+    projections: list[ADV4ApplicabilityProjectionResponse]
+    count: int
+    total: int
+    limit: int
+    offset: int
+
+
+class ADV4ApplicabilityReconstructionResponse(BaseModel):
+    projectionId: str
+    proposalId: str
+    directiveId: str
+    gate: str
+    applicabilitySubtreeHash: str
+    projectionHash: str
+    canonicalApplicability: dict[str, Any]
+    actingMembershipId: str
+    authPolicyVersion: str
+
+
 class ADProposalProvenanceResponse(BaseModel):
     stagingDecisionId: str
     actorUserId: Optional[str]
diff --git a/backend/app/services/ad_v4_candidates.py b/backend/app/services/ad_v4_candidates.py
index 50583a1..4aecc52 100644
--- a/backend/app/services/ad_v4_candidates.py
+++ b/backend/app/services/ad_v4_candidates.py
@@ -4,6 +4,7 @@ import hashlib
 import json
 import re
 import unicodedata
+from copy import deepcopy
 from dataclasses import dataclass
 from functools import lru_cache
 from pathlib import Path
@@ -20,17 +21,25 @@ from app.models.core import (
     ADV4CandidateProposalEvent,
     ADV4CandidateSubmission,
     ADV4CandidateSubmissionRelationship,
+    ADV4FeatureGate,
     AirworthinessDirective,
     OrganizationMembership,
     User,
     new_id,
 )
+from app.core.config import get_settings
 from app.services.ad_evidence import _hash_parts
 
 
 SCHEMA_VERSION = "ad_extraction_v4"
 CANONICALIZATION_VERSION = "paprnav-ad-v4-c14n-1"
 VALIDATOR_VERSION = "paprnav-ad-v4-validator-1"
+CANONICALIZATION_VERSION_V2 = "paprnav-ad-v4-c14n-2"
+VALIDATOR_VERSION_V2 = "paprnav-ad-v4-validator-2"
+SUPPORTED_V4_VALIDATOR_PAIRS = frozenset({
+    (VALIDATOR_VERSION, CANONICALIZATION_VERSION),
+    (VALIDATOR_VERSION_V2, CANONICALIZATION_VERSION_V2),
+})
 POLICY_NAME = "paprnav-platform-admin-candidate-write"
 POLICY_VERSION = "1"
 ENDPOINT_ACTION = "create_ad_v4_candidate"
@@ -52,6 +61,28 @@ DOMAINS = {
     "submission": b"paprnav:ad_extraction_v4:submission:1\x00",
     "relationship": b"paprnav:ad_extraction_v4:submission-relationship:1\x00",
 }
+DOMAINS_V2 = {
+    "proposal": b"paprnav:ad_extraction_v4:proposal:paprnav-ad-v4-c14n-2\x00",
+    "bindings": b"paprnav:ad_extraction_v4:evidence-bindings:2\x00",
+    "event": b"paprnav:ad_extraction_v4:candidate-event:2\x00",
+    "submission": b"paprnav:ad_extraction_v4:submission:2\x00",
+    "relationship": b"paprnav:ad_extraction_v4:submission-relationship:2\x00",
+}
+
+PROFILE_ENVELOPES = {
+    VALIDATOR_VERSION: {
+        "binding": "ad-v4-evidence-bindings-v1",
+        "event": "ad-v4-candidate-created-v1",
+        "submission": "ad-v4-submission-v1",
+        "relationship": "ad-v4-submission-relationship-v1",
+    },
+    VALIDATOR_VERSION_V2: {
+        "binding": "ad-v4-evidence-bindings-v2",
+        "event": "ad-v4-candidate-created-v2",
+        "submission": "ad-v4-submission-v2",
+        "relationship": "ad-v4-submission-relationship-v2",
+    },
+}
 
 ROOT_FIELDS = {
     "schemaVersion", "decisionKey", "directiveIdentity", "officialDocuments",
@@ -72,6 +103,9 @@ UNKNOWN_REASONS = {
 }
 INTERNAL_ARRAY_POLICIES: dict[str, tuple[str, str | tuple[str, ...] | None]] = {
     "bindings": ("set", "evidenceKey"),
+    "semanticNodeHashes": ("set", None),
+    "evidenceLinkHashes": ("set", None),
+    "reasons": ("set", None),
 }
 
 
@@ -189,9 +223,11 @@ def _resolved_schema(schema: dict[str, Any], root: dict[str, Any]) -> dict[str,
     return schema
 
 
-@lru_cache(maxsize=1)
-def _array_policies() -> dict[str, tuple[str, str | tuple[str, ...] | None]]:
-    root = _v4_schema()
+@lru_cache(maxsize=2)
+def _array_policies(canonicalization_version: str = CANONICALIZATION_VERSION) -> dict[str, tuple[str, str | tuple[str, ...] | None]]:
+    root = _v4_schema(
+        VALIDATOR_VERSION_V2 if canonicalization_version == CANONICALIZATION_VERSION_V2 else VALIDATOR_VERSION
+    )
     policies: dict[str, tuple[str, str | tuple[str, ...] | None]] = {}
 
     def walk(node: Any, property_name: str | None = None, seen: frozenset[str] = frozenset()) -> None:
@@ -225,57 +261,60 @@ def _array_policies() -> dict[str, tuple[str, str | tuple[str, ...] | None]]:
     return policies
 
 
-def _set_sort_key(item: Any, sort_key: str | tuple[str, ...] | None) -> bytes:
+def _set_sort_key(item: Any, sort_key: str | tuple[str, ...] | None, canonicalization_version: str) -> bytes:
     if sort_key is None:
-        return canonical_bytes(item)
+        return canonical_bytes(item, canonicalization_version)
     if not isinstance(item, dict):
         raise ADV4Error("invalid_set_item", "", "Keyed set item must be an object")
     fields = (sort_key,) if isinstance(sort_key, str) else sort_key
     try:
-        return b"\x00".join(canonical_bytes(item[field]) for field in fields)
+        return b"\x00".join(canonical_bytes(item[field], canonicalization_version) for field in fields)
     except KeyError as exc:
         raise ADV4Error("missing_stable_key", "", f"Set item lacks {exc.args[0]}") from exc
 
 
-def _normalize(value: Any, parent_key: str | None = None) -> Any:
+def _normalize(value: Any, parent_key: str | None = None, canonicalization_version: str = CANONICALIZATION_VERSION) -> Any:
     if value is None or (isinstance(value, (int, float)) and not isinstance(value, bool)):
         raise ADV4Error("forbidden_json_value", "", "JSON null and numbers are forbidden")
     if isinstance(value, dict):
-        return {key: _normalize(value[key], key) for key in sorted(value, key=_utf16_sort_key)}
+        return {key: _normalize(value[key], key, canonicalization_version) for key in sorted(value, key=_utf16_sort_key)}
     if isinstance(value, list):
-        items = [_normalize(item) for item in value]
-        policy = INTERNAL_ARRAY_POLICIES.get(parent_key or "") or _array_policies().get(parent_key or "")
+        items = [_normalize(item, None, canonicalization_version) for item in value]
+        policy = INTERNAL_ARRAY_POLICIES.get(parent_key or "") or _array_policies(canonicalization_version).get(parent_key or "")
         if parent_key is None:
             policy = ("sequence", None)
         if policy is None:
             raise ADV4Error("unregistered_array", "", f"Array {parent_key!r} has no schema canonicalization policy")
         kind, sort_key = policy
         if kind == "set":
-            encoded = [canonical_bytes(item) for item in items]
+            encoded = [canonical_bytes(item, canonicalization_version) for item in items]
             if len(encoded) != len(set(encoded)):
                 raise ADV4Error("duplicate_set_item", "", f"Set array {parent_key} contains duplicates")
-            identities = [_set_sort_key(item, sort_key) for item in items]
+            identities = [_set_sort_key(item, sort_key, canonicalization_version) for item in items]
             if sort_key is not None and len(identities) != len(set(identities)):
                 raise ADV4Error(
                     "duplicate_stable_key", "",
                     f"Set array {parent_key} contains duplicate composite identity",
                 )
-            items.sort(key=lambda item: _set_sort_key(item, sort_key))
+            items.sort(key=lambda item: _set_sort_key(item, sort_key, canonicalization_version))
         elif kind != "sequence":
             raise RuntimeError(f"Invalid V4 array kind for {parent_key}: {kind}")
         return items
     return value
 
 
-def canonical_bytes(value: Any) -> bytes:
-    normalized = _normalize(value)
+def canonical_bytes(value: Any, canonicalization_version: str = CANONICALIZATION_VERSION) -> bytes:
+    if canonicalization_version not in {CANONICALIZATION_VERSION, CANONICALIZATION_VERSION_V2}:
+        raise ADV4Error("unsupported_canonicalization", "", "Unsupported V4 canonicalization version")
+    normalized = _normalize(value, canonicalization_version=canonicalization_version)
     return json.dumps(
         normalized, ensure_ascii=False, allow_nan=False, separators=(",", ":"),
     ).encode("utf-8")
 
 
-def _domain_hash(domain: str, value: Any) -> str:
-    return hashlib.sha256(DOMAINS[domain] + canonical_bytes(value)).hexdigest()
+def _domain_hash(domain: str, value: Any, canonicalization_version: str = CANONICALIZATION_VERSION) -> str:
+    domains = DOMAINS_V2 if canonicalization_version == CANONICALIZATION_VERSION_V2 else DOMAINS
+    return hashlib.sha256(domains[domain] + canonical_bytes(value, canonicalization_version)).hexdigest()
 
 
 def _require_object(value: Any, pointer: str) -> dict[str, Any]:
@@ -290,10 +329,81 @@ def _require_key(value: Any, pointer: str) -> str:
     return value
 
 
-@lru_cache(maxsize=1)
-def _v4_schema() -> dict[str, Any]:
+@lru_cache(maxsize=2)
+def _v4_schema(validator_version: str = VALIDATOR_VERSION) -> dict[str, Any]:
     path = Path(__file__).resolve().parents[1] / "schemas" / "ad_extraction_v4.schema.json"
-    return json.loads(path.read_text(encoding="utf-8"))
+    schema = json.loads(path.read_text(encoding="utf-8"))
+    if validator_version == VALIDATOR_VERSION:
+        return schema
+    if validator_version != VALIDATOR_VERSION_V2:
+        raise ADV4Error("unsupported_validator", "", "Unsupported V4 validator version")
+    schema = deepcopy(schema)
+    defs = schema["$defs"]
+    member_base = {
+        "type": "object", "additionalProperties": False,
+        "required": ["memberKey", "designationKind", "manufacturer", "evidenceKeys"],
+        "properties": {
+            "memberKey": {"$ref": "#/$defs/stableKey"},
+            "designationKind": {},
+            "manufacturer": {"$ref": "#/$defs/knownString"},
+            "evidenceKeys": {"$ref": "#/$defs/evidenceKeys"},
+        },
+    }
+    model_member = deepcopy(member_base)
+    model_member["required"].append("sourceDesignation")
+    model_member["properties"].update({
+        "designationKind": {"const": "model"},
+        "sourceDesignation": {"$ref": "#/$defs/identifier"},
+    })
+    series_member = deepcopy(member_base)
+    series_member["required"].extend(["expressionText", "evaluationState", "reason"])
+    series_member["properties"].update({
+        "designationKind": {"const": "series_expression"},
+        "expressionText": {"$ref": "#/$defs/identifier"},
+        "evaluationState": {"const": "unknown"},
+        "reason": {"const": "unsupported_expression"},
+    })
+    defs["designationMemberV2"] = {"oneOf": [model_member, series_member]}
+    defs["designationGroupV2"] = {
+        "type": "object", "additionalProperties": False,
+        "required": ["groupKey", "sourceDisplayText", "association", "members", "evidenceKeys"],
+        "properties": {
+            "groupKey": {"$ref": "#/$defs/stableKey"},
+            "sourceDisplayText": {"$ref": "#/$defs/knownString"},
+            "association": {"enum": ["all_members", "any_member", "source_group", "unknown"]},
+            "members": {"type": "array", "minItems": 1, "items": {"$ref": "#/$defs/designationMemberV2"}, "x-paprnav-array-kind": "set", "x-paprnav-sort-key": "memberKey"},
+            "reason": {"enum": sorted(UNKNOWN_REASONS)},
+            "temporalScope": {"$ref": "#/$defs/temporalScope"},
+            "evidenceKeys": {"$ref": "#/$defs/evidenceKeys"},
+        },
+    }
+    defs["conditionSubject"]["properties"]["designationGroup"] = {"$ref": "#/$defs/designationGroupV2"}
+    defs["manufacturerModelGroupV2"] = {
+        "type": "object", "additionalProperties": False,
+        "required": ["groupKey", "manufacturer", "association", "members", "evidenceKeys"],
+        "properties": {
+            "groupKey": {"$ref": "#/$defs/stableKey"},
+            "manufacturer": {"$ref": "#/$defs/knownString"},
+            "association": {"enum": ["paired", "source_group", "unknown"]},
+            "members": {"type": "array", "minItems": 1, "items": {"$ref": "#/$defs/designationMemberV2"}, "x-paprnav-array-kind": "set", "x-paprnav-sort-key": "memberKey"},
+            "reason": {"enum": sorted(UNKNOWN_REASONS)},
+            "temporalScope": {"$ref": "#/$defs/temporalScope"},
+            "evidenceKeys": {"$ref": "#/$defs/evidenceKeys"},
+        },
+    }
+    defs["searchHint"] = {
+        "type": "object", "additionalProperties": False,
+        "required": ["hintKey", "productRole", "sourceDisplayText", "manufacturerModelGroups", "controlling", "exhaustive", "evidenceKeys"],
+        "properties": {
+            "hintKey": {"$ref": "#/$defs/stableKey"},
+            "productRole": {"enum": ["airframe", "engine", "propeller", "appliance", "installed_part", "modification"]},
+            "sourceDisplayText": {"$ref": "#/$defs/knownString"},
+            "manufacturerModelGroups": {"type": "array", "minItems": 1, "items": {"$ref": "#/$defs/manufacturerModelGroupV2"}, "x-paprnav-array-kind": "set", "x-paprnav-sort-key": "groupKey"},
+            "controlling": {"const": False}, "exhaustive": {"const": False},
+            "evidenceKeys": {"$ref": "#/$defs/evidenceKeys"},
+        },
+    }
+    return schema
 
 
 def _schema_pointer(pointer: str, key: str | int) -> str:
@@ -393,9 +503,9 @@ def _validate_schema_node(value: Any, schema: dict[str, Any], root: dict[str, An
         raise _schema_error(pointer, "Expected boolean")
 
 
-def validate_v4_schema(value: dict[str, Any]) -> None:
+def validate_v4_schema(value: dict[str, Any], validator_version: str = VALIDATOR_VERSION) -> None:
     """Validate the checked-in closed schema before semantic/reference checks."""
-    schema = _v4_schema()
+    schema = _v4_schema(validator_version)
     _validate_schema_node(value, schema, schema, "")
 
 
@@ -658,9 +768,36 @@ def _collect_and_validate(value: Any, evidence: set[str], used: set[str], pointe
             _collect_and_validate(child, evidence, used, f"{pointer}/{index}")
 
 
-def validate_v4_envelope(parsed: ParsedV4Request, directive_id: str) -> tuple[dict[str, Any], list[dict[str, Any]]]:
+def _validate_v2_semantics(proposal: dict[str, Any]) -> None:
+    for condition_index, condition in enumerate(proposal["conditionDefinitions"]):
+        subject = condition["subject"]
+        attribute = subject.get("attributeValue")
+        if isinstance(attribute, dict) and attribute.get("state") == "known" and attribute.get("value") == "unknown_requires_compliance":
+            raise ADV4Error(
+                "semantic_unknown_sentinel",
+                f"/proposal/conditionDefinitions/{condition_index}/subject/attributeValue/value",
+                "Unknown applicability must use the explicit unknown union",
+            )
+        group = subject.get("designationGroup")
+        if group is not None:
+            unknown = group["association"] == "unknown"
+            if unknown != ("reason" in group and "temporalScope" in group):
+                raise ADV4Error("schema_validation", f"/proposal/conditionDefinitions/{condition_index}/subject/designationGroup", "Unknown group association requires reason and temporalScope only")
+    for hint_index, hint in enumerate(proposal["applicabilitySearchHints"]):
+        for group_index, group in enumerate(hint["manufacturerModelGroups"]):
+            unknown = group["association"] == "unknown"
+            if unknown != ("reason" in group and "temporalScope" in group):
+                raise ADV4Error("schema_validation", f"/proposal/applicabilitySearchHints/{hint_index}/manufacturerModelGroups/{group_index}", "Unknown group association requires reason and temporalScope only")
+
+
+def validate_v4_envelope(
+    parsed: ParsedV4Request,
+    directive_id: str,
+    *,
+    validator_version: str = VALIDATOR_VERSION,
+) -> tuple[dict[str, Any], list[dict[str, Any]]]:
     envelope = parsed.value
-    validate_v4_schema(envelope)
+    validate_v4_schema(envelope, validator_version)
     if set(envelope) != {"proposal", "submissionContext"}:
         raise ADV4Error("closed_envelope", "", "Envelope properties must be proposal and submissionContext")
     proposal = _require_object(envelope["proposal"], "/proposal")
@@ -701,6 +838,8 @@ def validate_v4_envelope(parsed: ParsedV4Request, directive_id: str) -> tuple[di
     if used != set(bindings):
         raise ADV4Error("unused_evidence", "/proposal/evidenceBindings", f"Unused bindings: {sorted(set(bindings) - used)}")
     _validate_semantic_graph(proposal)
+    if validator_version == VALIDATOR_VERSION_V2:
+        _validate_v2_semantics(proposal)
     context = _require_object(envelope["submissionContext"], "/submissionContext")
     if set(context) != {"relationships"} or not isinstance(context["relationships"], list):
         raise ADV4Error("closed_submission_context", "/submissionContext", "Only relationships array is permitted")
@@ -740,6 +879,19 @@ def _authorization(db: Session, actor: User, membership_id: str) -> Organization
     return membership
 
 
+def require_v4_database_gate(db: Session, gate_key: str, *, lock: bool = False) -> None:
+    query = select(ADV4FeatureGate).where(ADV4FeatureGate.gate_key == gate_key)
+    if lock:
+        query = query.with_for_update(read=True)
+    try:
+        gate = db.scalar(query)
+    except Exception as exc:
+        raise ADV4Error("schema_capability_mismatch", "", "V4 database capability is unavailable", http_status=409) from exc
+    if gate is None or not gate.enabled:
+        code = "validator2_write_gate_disabled" if gate_key == "validator2_write_enabled" else "materializer3a_gate_disabled"
+        raise ADV4Error(code, "", f"V4 database gate {gate_key} is disabled", http_status=409)
+
+
 def _binding_snapshot(db: Session, directive_id: str, proposal: dict[str, Any]) -> list[dict[str, Any]]:
     snapshots: list[dict[str, Any]] = []
     requested_bindings = proposal["evidenceBindings"]
@@ -846,20 +998,49 @@ def _validate_candidate_relationship_graph(
 def store_v4_candidate(
     db: Session, *, directive_id: str, parsed: ParsedV4Request, actor: User,
     membership_id: str, idempotency_key: str,
+    validator_version: str | None = None,
 ) -> StoredV4Candidate:
-    proposal_value, relationships = validate_v4_envelope(parsed, directive_id)
+    if validator_version is None:
+        validator_version = (
+            VALIDATOR_VERSION_V2
+            if get_settings().ad_v4_validator2_writes_enabled
+            else VALIDATOR_VERSION
+        )
+    if validator_version not in {VALIDATOR_VERSION, VALIDATOR_VERSION_V2}:
+        raise ADV4Error("unsupported_validator", "", "Unsupported V4 validator version")
+    canonicalization_version = (
+        CANONICALIZATION_VERSION_V2
+        if validator_version == VALIDATOR_VERSION_V2
+        else CANONICALIZATION_VERSION
+    )
+    if validator_version == VALIDATOR_VERSION_V2:
+        if not get_settings().ad_v4_validator2_writes_enabled:
+            raise ADV4Error("capability_disabled", "", "Validator-2 application capability is disabled", http_status=409)
+        if db.bind is not None and db.bind.dialect.name == "postgresql":
+            db.execute(text("LOCK TABLE ad_v4_candidate_proposals IN ROW EXCLUSIVE MODE"))
+        require_v4_database_gate(db, "validator2_write_enabled", lock=True)
+    proposal_value, relationships = validate_v4_envelope(
+        parsed, directive_id, validator_version=validator_version,
+    )
     if db.get(AirworthinessDirective, directive_id) is None:
         raise ADV4Error("not_found", "", "Directive not found", http_status=404)
     membership = _authorization(db, actor, membership_id)
     scope = f"{actor.id}:{membership.id}:{ENDPOINT_ACTION}:{POLICY_VERSION}:{idempotency_key}"
     _advisory_lock(db, f"idem:{scope}")
-    proposal_payload = canonical_bytes(proposal_value)
-    proposal_hash = hashlib.sha256(DOMAINS["proposal"] + proposal_payload).hexdigest()
+    proposal_payload = canonical_bytes(proposal_value, canonicalization_version)
+    domains = DOMAINS_V2 if validator_version == VALIDATOR_VERSION_V2 else DOMAINS
+    envelopes = PROFILE_ENVELOPES[validator_version]
+    proposal_hash = hashlib.sha256(domains["proposal"] + proposal_payload).hexdigest()
     request_envelope = {
-        "version": "ad-v4-submission-v1", "directiveId": directive_id,
+        "version": envelopes["submission"], "directiveId": directive_id,
         "proposalCanonicalHash": proposal_hash, "relationships": relationships,
     }
-    request_hash = _domain_hash("submission", request_envelope)
+    if validator_version == VALIDATOR_VERSION_V2:
+        request_envelope.update({
+            "validatorVersion": validator_version,
+            "canonicalizationVersion": canonicalization_version,
+        })
+    request_hash = _domain_hash("submission", request_envelope, canonicalization_version)
     prior = db.scalar(select(ADV4CandidateSubmission).where(
         ADV4CandidateSubmission.actor_user_id == actor.id,
         ADV4CandidateSubmission.authorizing_membership_id == membership.id,
@@ -872,22 +1053,25 @@ def store_v4_candidate(
             raise ADV4Error("idempotency_conflict", "", "Idempotency key was used for different canonical content", http_status=409)
         return StoredV4Candidate(db.get(ADV4CandidateProposal, prior.proposal_id), prior, True, True)  # type: ignore[arg-type]
     snapshots = _binding_snapshot(db, directive_id, proposal_value)
-    binding_envelope = {"version": "ad-v4-evidence-bindings-v1", "bindings": snapshots}
-    binding_hash = _domain_hash("bindings", binding_envelope)
-    _advisory_lock(db, f"content:{directive_id}:{CANONICALIZATION_VERSION}:{proposal_hash}")
+    binding_envelope = {"version": envelopes["binding"], "bindings": snapshots}
+    if validator_version == VALIDATOR_VERSION_V2:
+        binding_envelope.update({"validatorVersion": validator_version, "canonicalizationVersion": canonicalization_version})
+    binding_hash = _domain_hash("bindings", binding_envelope, canonicalization_version)
+    _advisory_lock(db, f"content:{directive_id}:{validator_version}:{canonicalization_version}:{proposal_hash}")
     candidate = db.scalar(select(ADV4CandidateProposal).where(
         ADV4CandidateProposal.directive_id == directive_id,
-        ADV4CandidateProposal.canonicalization_version == CANONICALIZATION_VERSION,
+        ADV4CandidateProposal.validator_version == validator_version,
+        ADV4CandidateProposal.canonicalization_version == canonicalization_version,
         ADV4CandidateProposal.canonical_hash == proposal_hash,
     ))
     reused = candidate is not None
     if candidate is None:
         candidate = ADV4CandidateProposal(
             id=new_id("avp"), directive_id=directive_id, schema_version=SCHEMA_VERSION,
-            canonicalization_version=CANONICALIZATION_VERSION,
-            validator_version=VALIDATOR_VERSION, canonical_bytes=proposal_payload,
+            canonicalization_version=canonicalization_version,
+            validator_version=validator_version, canonical_bytes=proposal_payload,
             parsed_json=proposal_value, canonical_hash=proposal_hash,
-            evidence_binding_bytes=canonical_bytes(binding_envelope),
+            evidence_binding_bytes=canonical_bytes(binding_envelope, canonicalization_version),
             evidence_binding_hash=binding_hash, binding_count=len(snapshots), gate="candidate_only",
         )
         db.add(candidate)
@@ -903,6 +1087,8 @@ def store_v4_candidate(
                 evidence_key=item["evidenceKey"], fragment_id=item["fragmentId"],
                 fragment_hash=item["fragmentHash"], admitted_event_id=item["admittedEventId"],
                 admitted_event_hash=item["admittedEventHash"],
+                validator_version=validator_version,
+                canonicalization_version=canonicalization_version,
             )
             db.add(binding)
             binding_rows.append(binding)
@@ -926,10 +1112,12 @@ def store_v4_candidate(
         authorizing_membership_id=membership.id, organization_id=membership.organization_id,
         actor_role=membership.role, actor_status=membership.status,
         auth_policy_name=POLICY_NAME, auth_policy_version=POLICY_VERSION,
-        auth_claims_hash=hashlib.sha256(canonical_bytes(claims)).hexdigest(),
+        auth_claims_hash=hashlib.sha256(canonical_bytes(claims, canonicalization_version)).hexdigest(),
         endpoint_action=ENDPOINT_ACTION, idempotency_key=idempotency_key,
-        request_hash=request_hash, request_canonical_bytes=canonical_bytes(request_envelope),
+        request_hash=request_hash, request_canonical_bytes=canonical_bytes(request_envelope, canonicalization_version),
         raw_transport_hash=parsed.raw_hash,
+        validator_version=validator_version,
+        canonicalization_version=canonicalization_version,
     )
     db.add(submission)
     # Relationship and candidate-created event triggers both resolve their
@@ -939,33 +1127,41 @@ def store_v4_candidate(
     for relation in relationships:
         predecessor = predecessors[relation["predecessorProposalId"]]
         relation_envelope = {
-            "version": "ad-v4-submission-relationship-v1",
+            "version": envelopes["relationship"],
             "submissionId": submission.id,
             **relation,
         }
-        relation_bytes = canonical_bytes(relation_envelope)
+        if validator_version == VALIDATOR_VERSION_V2:
+            relation_envelope.update({"validatorVersion": validator_version, "canonicalizationVersion": canonicalization_version})
+        relation_bytes = canonical_bytes(relation_envelope, canonicalization_version)
         db.add(ADV4CandidateSubmissionRelationship(
             submission_id=submission.id, relationship_key=relation["relationshipKey"],
             relation_type=relation["relationType"], predecessor_proposal_id=predecessor.id,
             reason=relation["reason"], evidence_keys=relation["evidenceKeys"],
             canonical_bytes=relation_bytes,
-            relationship_hash=_domain_hash("relationship", relation_envelope),
+            relationship_hash=_domain_hash("relationship", relation_envelope, canonicalization_version),
+            validator_version=validator_version,
+            canonicalization_version=canonicalization_version,
         ))
     if not reused:
         event_envelope = {
-            "version": "ad-v4-candidate-created-v1", "eventType": "candidate_created",
+            "version": envelopes["event"], "eventType": "candidate_created",
             "proposalId": candidate.id, "directiveId": directive_id,
             "proposalCanonicalHash": proposal_hash, "evidenceBindingHash": binding_hash,
             "createdBySubmissionId": submission.id,
         }
-        event_bytes = canonical_bytes(event_envelope)
+        if validator_version == VALIDATOR_VERSION_V2:
+            event_envelope.update({"validatorVersion": validator_version, "canonicalizationVersion": canonicalization_version})
+        event_bytes = canonical_bytes(event_envelope, canonicalization_version)
         db.add(ADV4CandidateProposalEvent(
             proposal_id=candidate.id, directive_id=directive_id,
             created_by_submission_id=submission.id, event_type="candidate_created",
             sequence_number=0, proposal_canonical_hash=proposal_hash,
             evidence_binding_hash=binding_hash, predecessor_event_hash=None,
             canonical_bytes=event_bytes,
-            event_hash=_domain_hash("event", event_envelope),
+            event_hash=_domain_hash("event", event_envelope, canonicalization_version),
+            validator_version=validator_version,
+            canonicalization_version=canonicalization_version,
         ))
     db.flush()
     return StoredV4Candidate(candidate, submission, reused, False)
@@ -975,15 +1171,27 @@ def verified_candidate(db: Session, proposal_id: str) -> ADV4CandidateProposal:
     candidate = db.get(ADV4CandidateProposal, proposal_id)
     if candidate is None:
         raise ADV4Error("not_found", "", "Candidate not found", http_status=404)
-    if canonical_bytes(candidate.parsed_json) != candidate.canonical_bytes:
+    pair = (candidate.validator_version, candidate.canonicalization_version)
+    if pair not in SUPPORTED_V4_VALIDATOR_PAIRS:
+        raise ADV4Error("candidate_integrity", "", "Stored validator/canonicalization pair is unsupported", http_status=409)
+    if canonical_bytes(candidate.parsed_json, candidate.canonicalization_version) != candidate.canonical_bytes:
         raise ADV4Error("candidate_integrity", "", "Stored canonical bytes and JSON differ", http_status=409)
-    if hashlib.sha256(DOMAINS["proposal"] + candidate.canonical_bytes).hexdigest() != candidate.canonical_hash:
+    domains = DOMAINS_V2 if candidate.validator_version == VALIDATOR_VERSION_V2 else DOMAINS
+    if hashlib.sha256(domains["proposal"] + candidate.canonical_bytes).hexdigest() != candidate.canonical_hash:
         raise ADV4Error("candidate_integrity", "", "Stored canonical hash differs", http_status=409)
+    validate_v4_schema({"proposal": candidate.parsed_json, "submissionContext": {"relationships": []}}, candidate.validator_version)
     return candidate
 
 
 def verified_submission(db: Session, submission: ADV4CandidateSubmission) -> list[ADV4CandidateSubmissionRelationship]:
     candidate = verified_candidate(db, submission.proposal_id)
+    if (
+        submission.validator_version != candidate.validator_version
+        or submission.canonicalization_version != candidate.canonicalization_version
+    ):
+        raise ADV4Error("candidate_integrity", "", "Submission version pair differs from proposal", http_status=409)
+    canonicalization_version = candidate.canonicalization_version
+    envelopes = PROFILE_ENVELOPES[candidate.validator_version]
     if (
         submission.actor_kind != "platform_admin"
         or submission.actor_role != "platform_admin"
@@ -998,12 +1206,17 @@ def verified_submission(db: Session, submission: ADV4CandidateSubmission) -> lis
         request_value = json.loads(submission.request_canonical_bytes.decode("utf-8"))
     except (UnicodeDecodeError, json.JSONDecodeError) as exc:
         raise ADV4Error("candidate_integrity", "", "Submission canonical bytes are invalid", http_status=409) from exc
-    if canonical_bytes(request_value) != submission.request_canonical_bytes:
+    if canonical_bytes(request_value, canonicalization_version) != submission.request_canonical_bytes:
         raise ADV4Error("candidate_integrity", "", "Submission bytes are not canonical", http_status=409)
-    if _domain_hash("submission", request_value) != submission.request_hash:
+    if _domain_hash("submission", request_value, canonicalization_version) != submission.request_hash:
         raise ADV4Error("candidate_integrity", "", "Submission hash differs", http_status=409)
-    if request_value.get("version") != "ad-v4-submission-v1" or request_value.get("directiveId") != submission.directive_id or request_value.get("proposalCanonicalHash") != candidate.canonical_hash:
+    if request_value.get("version") != envelopes["submission"] or request_value.get("directiveId") != submission.directive_id or request_value.get("proposalCanonicalHash") != candidate.canonical_hash:
         raise ADV4Error("candidate_integrity", "", "Submission envelope differs from relational identity", http_status=409)
+    if candidate.validator_version == VALIDATOR_VERSION_V2 and (
+        request_value.get("validatorVersion") != candidate.validator_version
+        or request_value.get("canonicalizationVersion") != canonicalization_version
+    ):
+        raise ADV4Error("candidate_integrity", "", "Submission envelope version differs", http_status=409)
     claims = {
         "userId": submission.actor_user_id,
         "membershipId": submission.authorizing_membership_id,
@@ -1013,7 +1226,7 @@ def verified_submission(db: Session, submission: ADV4CandidateSubmission) -> lis
         "policy": submission.auth_policy_name,
         "version": submission.auth_policy_version,
     }
-    if hashlib.sha256(canonical_bytes(claims)).hexdigest() != submission.auth_claims_hash:
+    if hashlib.sha256(canonical_bytes(claims, canonicalization_version)).hexdigest() != submission.auth_claims_hash:
         raise ADV4Error("candidate_integrity", "", "Authorization snapshot hash differs", http_status=409)
     relationships = db.scalars(
         select(ADV4CandidateSubmissionRelationship)
@@ -1024,7 +1237,7 @@ def verified_submission(db: Session, submission: ADV4CandidateSubmission) -> lis
     candidate_evidence_keys = set(candidate.parsed_json.get("evidenceBindings", {}))
     for relationship in relationships:
         envelope = {
-            "version": "ad-v4-submission-relationship-v1",
+            "version": envelopes["relationship"],
             "submissionId": submission.id,
             "relationshipKey": relationship.relationship_key,
             "relationType": relationship.relation_type,
@@ -1032,11 +1245,15 @@ def verified_submission(db: Session, submission: ADV4CandidateSubmission) -> lis
             "reason": relationship.reason,
             "evidenceKeys": relationship.evidence_keys,
         }
-        expected_bytes = canonical_bytes(envelope)
+        if candidate.validator_version == VALIDATOR_VERSION_V2:
+            envelope.update({"validatorVersion": candidate.validator_version, "canonicalizationVersion": canonicalization_version})
+        expected_bytes = canonical_bytes(envelope, canonicalization_version)
         predecessor = db.get(ADV4CandidateProposal, relationship.predecessor_proposal_id)
         if (
             relationship.canonical_bytes != expected_bytes
-            or relationship.relationship_hash != _domain_hash("relationship", envelope)
+            or relationship.relationship_hash != _domain_hash("relationship", envelope, canonicalization_version)
+            or relationship.validator_version != candidate.validator_version
+            or relationship.canonicalization_version != canonicalization_version
             or predecessor is None
             or predecessor.directive_id != candidate.directive_id
             or predecessor.id == candidate.id
diff --git a/backend/tests/test_ad_v4_postgres.py b/backend/tests/test_ad_v4_postgres.py
index 3d1fdc8..1a2ee81 100644
--- a/backend/tests/test_ad_v4_postgres.py
+++ b/backend/tests/test_ad_v4_postgres.py
@@ -42,13 +42,13 @@ POSTGRES_URL = os.getenv("PAPRNAV_TEST_POSTGRES_URL")
 pytestmark = pytest.mark.skipif(not POSTGRES_URL, reason="PAPRNAV_TEST_POSTGRES_URL required")
 
 
-def _seed(db: Session):
+def _seed(db: Session, *, ad_number: str = "2024-14-03"):
     token = uuid.uuid4().hex
     user = User(email=f"v4-{token}@example.test", name="V4 Admin", password_hash="x", status="active")
     organization = Organization(name=f"Paprnav {token}", type="platform")
     db.add_all([user, organization]); db.flush()
     membership = OrganizationMembership(organization_id=organization.id, user_id=user.id, role="platform_admin", status="active")
-    directive = AirworthinessDirective(ad_number="2024-14-03", title="V4 fixture", source_content_hash="1" * 64, status="candidate", extraction_status="not_started", review_status="not_started")
+    directive = AirworthinessDirective(ad_number=ad_number, title="V4 fixture", source_content_hash="1" * 64, status="candidate", extraction_status="not_started", review_status="not_started")
     document = ADSourceDocument(source_system="federal_register", source_type="document_pdf", source_identifier=token, storage_backend="local", storage_key=f"fixture/{token}.pdf", media_type="application/pdf", content_hash=hashlib.sha256(token.encode()).hexdigest(), storage_bytes=1, captured_at=datetime.now(timezone.utc), status="retained")
     db.add_all([membership, directive, document]); db.flush()
     db.add(ADPublication(directive_id=directive.id, source_document_id=document.id, source_system="federal_register", source_type="document_pdf", source_identifier=token, content_hash=document.content_hash)); db.flush()
@@ -77,6 +77,9 @@ def _request(
     relationships=None,
     extra_binding=None,
     reverse_bindings=False,
+    listed_designation=False,
+    ad_number="2024-14-03",
+    supersession_relations=None,
 ):
     ev = "ev-official"
     bindings = [(ev, {"fragmentId": fragment_id, "fragmentHash": fragment_hash})]
@@ -90,14 +93,20 @@ def _request(
         bindings.reverse()
     proposal = {
         "schemaVersion": "ad_extraction_v4", "decisionKey": decision_key,
-        "directiveIdentity": {"directiveId": directive_id, "adNumber": {"state": "known", "value": "2024-14-03", "evidenceKeys": [ev]}},
+        "directiveIdentity": {"directiveId": directive_id, "adNumber": {"state": "known", "value": ad_number, "evidenceKeys": [ev]}},
         "officialDocuments": [{"officialDocumentKey": "official-rule", "documentRole": "ad_rule", "sourceDocumentId": document_id, "sourceContentHash": source_hash, "publicationDocumentNumber": "2024-15529", "evidenceKeys": document_evidence}],
         "evidenceBindings": dict(bindings),
         "incorporatedDocuments": [], "productScopes": [{"scopeKey": "scope-main", "productRole": "airframe", "evidenceKeys": [ev]}],
         "conditionDefinitions": [], "applicabilityRules": [{"ruleKey": "rule-main", "scopeExpression": {"nodeType": "scope_ref", "scopeKey": "scope-main"}, "exclusionRuleKeys": [], "evidenceKeys": [ev]}],
         "requirements": [{"requirementKey": "requirement-main", "sequence": "1", "activationExpression": {"nodeType": "rule_ref", "ruleKey": "rule-main"}, "requirementType": "corrective_action", "action": {"actionType": "other_reviewed", "approvedDataDocumentRefKeys": [], "evidenceKeys": [ev]}, "prerequisiteRequirementKeys": [], "branch": {"kind": "required", "evidenceKeys": [ev]}, "initialTiming": {"state": "unknown", "reason": "not_yet_reviewed", "temporalScope": {"kind": "directive_version"}, "evidenceKeys": [ev]}, "recurrence": {"kind": "none", "evidenceKeys": [ev]}, "terminatingEffect": {"kind": "none", "evidenceKeys": [ev]}, "evidenceKeys": [ev]}],
-        "recurrenceGroups": [], "applicabilitySearchHints": [], "amocAuthorityProvisions": [], "supersessionRelations": [], "authoritativeCorrections": [],
+        "recurrenceGroups": [], "applicabilitySearchHints": [], "amocAuthorityProvisions": [], "supersessionRelations": supersession_relations or [], "authoritativeCorrections": [],
     }
+    if listed_designation:
+        proposal["productScopes"][0]["modelScope"] = {
+            "kind": "listed",
+            "sourceDesignations": ["Model 100", "Model 200"],
+            "evidenceKeys": [ev],
+        }
     return parse_v4_request_bytes(json.dumps({
         "proposal": proposal,
         "submissionContext": {"relationships": relationships or []},

```

## Untracked text files

### `.ai/review-runs/T081-V4-SCHEMA-SLICE-3A/CURRENT_CHECKPOINT.md`

size=9035; sha256=ce5cd27e815b55317f01708f9e70f8c2c3b99e6b2f7bda76a233a44f0ce13ac0; truncated=false

```text
# T081 V4 Slice 3A Current Checkpoint

Date: 2026-09-07 (post-initial implementation review)  
Repository: `/Users/hostiletakeover/Projects/paprnav`  
Branch: `codex/ad-source-catalog-proof`  
Committed base: `28f6be0 feat: add immutable AD V4 candidate foundation`

## Current outcome

Slice 3A is **partially implemented and failed independent implementation
review**. It is not ready for staging, closure, or commit. The green host,
calibration, and PostgreSQL tests below are valid but insufficient because the
reviewer disproved several approved database and audit invariants.

The active review run is:

```text
.ai/review-runs/T081-V4-SCHEMA-SLICE-3A
```

The review phase is `implementation`.

## Completed review gates

- The Codex design adversary closed **10 findings out of 10**.
- Claude returned three additional findings: two medium and one low.
- All Claude findings were entered into the durable ledger and independently
  verified by the Codex adversary.
- The combined design ledger is **13 closed out of 13**.
- The authoritative design PASS is recorded in `reviews.json`; the run was
  advanced from `design_reviewed` to `implementation` before product edits.
- The final design/external-critic fingerprint before implementation was
  `838675669b7b863ed798cbbe2db29d3fd4a653ee172a0c1bd6c482550f09a5cc`.

The design PASS does not certify the current implementation. The current
external-critic packet predates the product changes and is expected to be stale.

## Approved Slice 3A boundary

Slice 3A creates candidate-only normalized applicability projections:

- validator/canonicalizer v1 and v2 dispatch without rewriting v1 candidates;
- default-off validator-v2 writer and Slice-3A materializer/read gates;
- exact active platform-admin membership authorization;
- immutable candidate-bound materialization requests and events;
- shared proposal-scoped authoritative-correction foundations;
- semantic nodes and evidence links;
- source-faithful values and explicitly unreviewed identity mappings;
- product roles/scopes, model values or unevaluated series expressions;
- serial and part-number scopes;
- conditions, three-valued expressions, applicability rules, and
  noncontrolling search hints;
- deterministic materialization and exact applicability-subtree reconstruction;
- bounded platform-admin materialize/list/detail/reconstruction endpoints; and
- inline/opportunistic deterministic stale repair within existing authorized
  service transactions.

This slice must not add human approval, publication, reviewer GUI, released
catalog reads, aircraft matching, coverage, compliance, due-state calculation,
V3 mutation, aircraft identity migration, provider writers, CLI writers, cron,
or background workers.

## Partial implementation on disk

Tracked files modified:

```text
backend/app/api/routes/ads.py
backend/app/core/config.py
backend/app/models/core.py
backend/app/schemas/ads.py
backend/app/services/ad_v4_candidates.py
```

New product/test files:

```text
backend/app/db/migrations/versions/20260907_0027_add_ad_v4_applicability.py
backend/app/services/ad_v4_applicability.py
backend/tests/test_ad_v4_applicability.py
backend/tests/test_ad_v4_applicability_calibration.py
backend/tests/test_ad_v4_applicability_postgres.py
```

The new review-run directory is also untracked. Nothing is staged and no Slice
3A commit exists.

## Verification credited at this checkpoint

On 2026-09-07, after the interruption:

- Focused Slice-3A local suite: **10 passed out of 10** in 2.02 seconds.
- Combined candidate/API/applicability host suite: **40 passed out of 40** in
  4.98 seconds.
- New Slice-3A test collection: **24 tests collected** across applicability,
  calibration, and PostgreSQL files.
- Python compilation of the new service, migration, and three new test files:
  **5 passed out of 5**.
- `git diff --check`: **1 passed out of 1**.

Two deprecation warnings were reported; neither was a test failure.

## Verification completed after resumption

- Five-packet validator-v2 calibration: **10 passed out of 10** as bounded
  per-packet schema/canonical and real-evidence materialization/round-trip runs.
- Disposable PostgreSQL Slice-3A matrix: **4 passed out of 4** after explicit
  migration to 0027 in database `t081_v4_s3a_20260907b`; cleanup dropped it and
  `paprnav_db` was never targeted.
- Candidate/API/applicability host suite: **40 passed out of 40**.
- Existing ingestion/matching/recurrence/full-readiness isolation suite:
  **81 passed out of 81**.
- Compilation: **6 passed out of 6**; `git diff --check`: **1 passed out of 1**.
- Exact evidence is in `implementation-slice-3a.md`.

## Independent implementation review

Reviewer `/root/v4_s3a_impl_adversary` returned **FAIL**. The immutable report is
`adversarial-implementation-initial.md`; the failed review is recorded in
`reviews.json`. Five findings are open in `findings.json`:

- `IA-001` blocker: generic JSON-pointer persistence is not the approved typed
  relational schema and lacks its normative constraints.
- `IA-002` blocker: **closed after independent targeted re-review**. Deferred
  validation now rejects incomplete, extra, changed, reordered, or
  cross-referenced projection graphs, including listed-designation nodes.
- `IA-003` blocker: **closed after independent targeted re-review**. Exact
  successor/unique-predecessor resolution, target-local causal dependencies,
  canonical event causes, sorted application/database advisory locks, and a
  deferred global uniqueness check close sequential and concurrent direct-SQL
  write-skew. See `adversarial-implementation-ia003-closure.md`.
- `IA-004` high: **closed after independent targeted re-review**. Detail/list/
  reconstruction GETs are detection-only; repair is reachable only from the
  authorized, gated materialization POST. See
  `adversarial-implementation-ia004-closure.md`.
- `IA-005` high: **closed after independent targeted re-review**. Correction
  roots, ordered refs/evidence, document identities, 3A bindings, ordinals, and
  hashes are verified at commit and read.

## Verification not yet credited

- A passing independent implementation review: **0 passed out of 1**; the
  initial review failed with five findings.
- Closure review: not started.

## Runtime and data safety state

- The prior builder agent is interrupted and not running.
- Docker shows only the normal `backend-api-1` and healthy `backend-db-1`
  services. No one-off test container was present.
- A read-only PostgreSQL catalog query found **0 disposable databases** matching
  the Slice-3A or 0027 verification naming patterns.
- The normal `paprnav_db` was not used for the interrupted Slice-3A PostgreSQL
  verification and must not be used for future migration tests.

## Required continuation order

1. Address the sole remaining blocker, `IA-001`: replace the generic
   semantic-node/datum representation with the approved typed owner tables and
   their database-enforced shape/cardinality/reference/evidence constraints.
2. Fix `IA-005` in the same integrity slice by adding exact correction
   reconstruction and deferred correction/document/evidence completeness.
3. Fix `IA-003` with proposal-bound dependency resolution and exact causal FKs.
4. Preserve the independently closed `IA-004` detection-only GET behavior while
   rebuilding the schema/service.
5. Re-run bounded host, calibration, and freshly disposable PostgreSQL gates.
6. Update implementation evidence and build a fresh implementation packet.
7. Return fixes to the same independent reviewer for closure verification; the
   builder may not close its own findings.
8. Obtain a separate closure review and validate the review run.
9. Only after implementation and closure PASS: stage the exact reviewed tree,
    obtain a staged-state attestation, and ask before committing.

## Immediate short commands

Run from the repository root unless noted:

```bash
git status --short
git diff --check

cd backend
PYTHONPATH=. .venv/bin/pytest -q tests/test_ad_v4_applicability.py
PYTHONPATH=. .venv/bin/pytest --collect-only -q \
  tests/test_ad_v4_applicability.py \
  tests/test_ad_v4_applicability_calibration.py \
  tests/test_ad_v4_applicability_postgres.py
```

Do not start the PostgreSQL matrix until its database target has been resolved
to a new explicit disposable name and checked against `paprnav_db`.

## Copy-ready prompt for a fresh Codex task

```text
Continue T081-V4-SCHEMA-SLICE-3A from
.ai/review-runs/T081-V4-SCHEMA-SLICE-3A/CURRENT_CHECKPOINT.md.

Use the adversarial-review skill and preserve builder/reviewer separation.
Do not restart the work or redo completed design review. Inspect the existing
partial implementation, then finish the bounded calibration and disposable
PostgreSQL gates, write exact implementation evidence, build the current packet,
and obtain independent implementation review. Do not use paprnav_db, do not
enable released/customer readers, and do not stage or commit without asking.
Report verification as x passed out of x.
```

```
### `.ai/review-runs/T081-V4-SCHEMA-SLICE-3A/adversarial-design-closure-1.md`

size=3714; sha256=4dc29c60271e0909275f816d3252f2691b1549e96abdcdb34d73c327580f4f45; truncated=false

```text
# Independent design closure review: T081-V4-SCHEMA-SLICE-3A

Reviewer: `/root/v4_schema_adversary`  
Builder: `/root/v4_schema_builder`  
Stage: design  
Outcome: **FAIL**  
Reviewed packet fingerprint: `7509d50e2d6787da6ac86f4398ffa879063d968de3972bb294c4bb8d2902f4d2`

## Gate result

**8 passed out of 10 finding gates.** Eight original findings are closed.
`T081-V4-S3A-DA-004` remains an open blocker, and new blocker
`T081-V4-S3A-DA-010` records the validator/canonicalization rollback defect.
Slice 3A remains framed and implementation is not authorized.

## Closed findings

- `DA-001`: exact designation occurrences now own distinct mapping rows while
  sharing one evidence parent; the 10-scope calibration cardinality is
  representable.
- `DA-002`: one proposal-scoped correction foundation owns the full ordered
  reference set and evidence once; Slice 3B can append only its semantic
  binding without mutating or duplicating correction authority.
- `DA-003`: the corrected 1998 candidate uses explicit unknown and leaves the
  validator-1 candidate immutable/auditable.
- `DA-005`: source-only and no-normalized-identity origins are explicit,
  unknown, and evidence-inheriting.
- `DA-006`: supersession signals require successor/candidate AD equality and
  name an exact target-local dependency cause.
- `DA-007`: POST and both GETs select, lock, and validate the exact acting
  membership.
- `DA-008`: all 90 current type/operator pairs remain representable but
  unevaluated; no compatibility semantics are invented.
- `DA-009`: unusable matching indexes and readiness claims were removed.

## Open blockers

### `T081-V4-S3A-DA-004`

The typed group direction is sound, but its concrete 2002 plan is not
source-faithful and its canonical version is unsafe. The retained source says
`172A through 172H`; the proposed 27-model total expands that expression into
eight exact models despite the explicit unsupported-series/no-inference rule.
It must remain one source series expression with unknown evaluation unless a
separately reviewed series grammar establishes membership. In addition, the
new group/member arrays cannot remain under `paprnav-ad-v4-c14n-1`: the closed
Slice-2 contract requires a new canonicalization version whenever an array is
added.

### `T081-V4-S3A-DA-010`

Validator-2 rows live in existing Slice-2 tables, but the downgrade emptiness
gate covers only Slice-3A tables. An unmaterialized validator-2 candidate can
therefore survive a physical downgrade to migration 0026, whose trigger and
application support only validator-1. The design must define versioned hash
dispatch and make both application and physical rollback preserve or refuse
all newer immutable rows.

## Verification summary

- Incoming packet freshness: **1 passed out of 1** at fingerprint `7509d50e...`.
- Explicit packet inputs: **32 inspected out of 32**.
- Original finding closures: **8 passed out of 9**; DA-004 failed.
- Total finding gate after the newly identified rollback defect: **8 passed
  out of 10**.
- Model occurrence cardinality: **10 representable out of 10 listed scopes**
  using distinct occurrence nodes and shared evidence parents.
- Correction-2010 reconstruction: **1 passed out of 1** shared roots; 2 refs,
  2 evidence links once, 1 current 3A binding, and 1 reserved 3B binding.
- Retained 2002 source check: **1 failed out of 1** proposed exact-model
  expansions because `172A through 172H` is a source expression, not eight
  reviewed identities.
- Current product-code isolation remains intact: no Slice-3A implementation or
  released-reader import exists yet.

A refreshed decision and independent closure review are required before a
design PASS may be recorded.

```
### `.ai/review-runs/T081-V4-SCHEMA-SLICE-3A/adversarial-design-closure-2.md`

size=4222; sha256=b9524760acfb8632c681b05c0dd32e393d0c7ba89a4a751b93542115f9a2788f; truncated=false

```text
# Independent design closure review 2: T081-V4-SCHEMA-SLICE-3A

Reviewer: `/root/v4_schema_adversary`  
Builder: `/root/v4_schema_builder`  
Stage: design  
Outcome: **PASS**

## Gate result

**10 passed out of 10 finding gates.** `T081-V4-S3A-DA-004` and
`T081-V4-S3A-DA-010` are independently closed. The eight findings closed in
closure review 1 were rechecked for regression and remain closed. There are
zero open blockers and zero open or unaccepted high findings.

## Targeted closure evidence

### T081-V4-S3A-DA-004

The revised design assigns all new canonical arrays to the distinct closed
`paprnav-ad-v4-c14n-2` profile and validator 2. Every new array has a normative
set key, and the v2 proposal and audit domains are byte-exact and versioned.

The retained 2002 source expression `172A through 172H` is represented once as
a typed `series_expression`, not expanded into inferred models. The relational
`ad_v4_candidate_app_search_hint_members` row carries the branch discriminator,
exact expression text, fixed unevaluated/unsupported semantics, source-only
unknown identity provenance, canonical ordinal, and one inherited evidence
parent. Reconstruction uses the discriminator and fixed v2 branch fields; it
does not parse display text. The exact oracle is seven manufacturer groups,
19 exact model occurrences, and one series expression, with no exact `172B` or
`172H` row. The 2024 `GFC 500 and GSA 28` source display remains one
`all_members` group with two typed model members, while STC and master-drawing
assertions remain separate.

### T081-V4-S3A-DA-010

Stored proposals and every dependent audit envelope dispatch by their recorded
validator/canonicalization pair. V1 bytes and hashes remain immutable and
readable; v2 uses distinct domains, identities, and same-version reuse. The
deployment sequence installs dual database/application readers before enabling
v2 writes or the 3A materializer. Application rollback retains that dual
reader and disables feature exposure and new v2 writes.

Physical downgrade now takes `ACCESS EXCLUSIVE` on the Slice-2 proposal table
before any Slice-2 child or 3A table. Candidate creation and materialization use
the same proposal-first boundary. A writer/materializer therefore either
commits before downgrade and makes its refusal gate true, or waits without
holding a conflicting 3A lock; the prior parent/child lock inversion is gone.
Downgrade refuses any v2 proposal or dependent row even when 3A is empty, and
only the v1-only path may restore 0026 and prove downgrade/re-upgrade parity.

## Regression check

- DA-001: source occurrences remain one-to-one with identity mappings while
  evidence stays shared at its canonical parent.
- DA-002: correction-2010 remains one proposal-scoped foundation with its
  complete ordered references/evidence and append-only 3A/3B bindings.
- DA-003: validator-1 remains immutable; validator-2 encodes source uncertainty
  through the explicit unknown union.
- DA-005: source-only/no-normalized-identity origins remain explicit and
  evidence-inheriting.
- DA-006: supersession effects require proposal-successor identity equality and
  a target-local causal dependency.
- DA-007: POST and both GETs select, lock, and authorize one exact active
  platform-admin membership.
- DA-008: all 90 existing type/operator combinations remain representable but
  unevaluated.
- DA-009: no matching, normalized-token, source-spelling, or aircraft-ID index
  or released-reader claim was reintroduced.

## Verification accounting

- Incoming packet freshness: **1 passed out of 1** at fingerprint
  `1029601ac4fbf6a2aeb1289983c3f8b8d308e701fdb9924ec5e7ee0d9c5b638c`.
- Explicit bound inputs: **33 inspected out of 33**.
- Targeted finding closures: **2 passed out of 2**.
- Preserved prior finding closures: **8 passed out of 8**.
- Total design finding gate: **10 passed out of 10**.
- Retained 2002 cardinality/source-expression check: **1 passed out of 1**.
- Validator/canonicalization and rollback design check: **1 passed out of 1**.

This is a design PASS only. The five corrected validator-2 calibration
proposals and all migration/concurrency tests remain implementation gates; no
runtime success is claimed here.

```
### `.ai/review-runs/T081-V4-SCHEMA-SLICE-3A/adversarial-design-initial.md`

size=4487; sha256=b617aa132d2825d9140540f7d0d41f6d489bf67ec007c1997a5f3dd47a6c328d; truncated=false

```text
# Independent design review: T081-V4-SCHEMA-SLICE-3A

Reviewer: `/root/v4_schema_adversary`  
Builder: `/root/v4_schema_builder`  
Stage: design  
Outcome: **FAIL**  
Reviewed packet fingerprint: `abe88e1271ad0fa8e7f2c6c36885e7853de5f333c773466c70df53c7b55ec71c`

## Gate result

**0 passed out of 9 finding gates.** There are **4 open blockers** and **5
open high-severity findings**. Slice 3A must remain framed; implementation is
not authorized.

## Findings by severity

### Blockers

1. `T081-V4-S3A-DA-001` — the proposed identity-mapping uniqueness permits
   only one model mapping per designation scope. All 10 listed scopes in the
   five calibration packets contain multiple models, so 0 of 5 packets is
   materializable under the stated schema.
2. `T081-V4-S3A-DA-002` — the shared correction root/generation boundary is
   deferred, although the 2008 fixture has one authoritative correction
   spanning applicability and requirement namespaces. Count-only deferral
   cannot preserve the one canonical correction object for a later complete
   relational round-trip.
3. `T081-V4-S3A-DA-003` — the mandatory 1998 fixture represents “cannot be
   determined” as a `known` value named `unknown_requires_compliance`, contrary
   to the approved explicit-unknown contract and the design's own invariant.
4. `T081-V4-S3A-DA-004` — compound condition identities and the multi-maker
   search hint remain flattened strings. The existing calibration test itself
   parses comma-delimited text to infer membership, which the domain contract
   prohibits future product readers from doing.

### High

5. `T081-V4-S3A-DA-005` — the identity-mapping origin enum cannot honestly
   represent source-only manufacturers/models in condition subjects or search
   hints.
6. `T081-V4-S3A-DA-006` — supersession propagation does not bind the
   successor AD number to the proposal's own canonical AD identity and the
   event schema lacks an FK to its causal dependency row.
7. `T081-V4-S3A-DA-007` — audit GETs omit an acting-membership selector while
   invariant 24 requires exact active membership authorization for audits as
   well as writes.
8. `T081-V4-S3A-DA-008` — a normative condition type/operator compatibility
   matrix is required but not enumerated or enforced at the closed Slice-2
   boundary.
9. `T081-V4-S3A-DA-009` — the proposed model-token indexes are empty by design
   and have no reviewed identity bridge, so they cannot support the claimed
   future aircraft-ID lookup path.

The finding ledger records the violated invariant, exact evidence, impact, and
required closure for each stable ID.

## Independent checks

- Initial packet freshness: **1 passed out of 1** at the fingerprint above.
- Bound input readability: **26 passed out of 26**.
- Predecessor state: Slice 1 and Slice 2 state files are `closed`; Slice 2 has
  independent implementation and closure PASS records.
- Current implementation isolation: repository search found **0 Slice-3A
  product references out of all inspected current readers**; only Slice-2 V4
  candidate code exists today, and released matching/coverage/recurrence paths
  remain V3-bound.
- Calibration source structure: **5 inspected out of 5** proposal packets,
  with the stated scope/model/condition/rule counts confirmed.
- Proposed model-mapping cardinality counterexample: **10 conflicts out of 10
  listed designation scopes**; model counts were 51, 30, 6, 182, 224, 7, 2,
  10, 33, and 130.
- Proposed positive materialization feasibility: **0 passed out of 5** under
  the current mapping contract.

## Confirmed strengths

- The candidate-only boundary, exact Slice-2 parent/hash/evidence binding,
  source-text non-duplication, append-only posture, and V3/released-reader
  isolation are directionally sound.
- The four-field applicability subtree and relational-to-parent equality gate
  are appropriately strict for a derived candidate projection.
- The 2024 design shares one condition/rule across 182 model rows and does not
  copy PDF bytes or source prose per model.
- Series-expression execution, aircraft matching, publication, due state, and
  human approval are honestly excluded from this slice.

Those strengths do not resolve the infeasible cardinality, explicit-unknown,
flattened-identity, cross-slice correction, supersession-causality,
authorization, and future-identity gaps. A revised current packet and
independent design closure review are required before implementation.

```
### `.ai/review-runs/T081-V4-SCHEMA-SLICE-3A/adversarial-external-critic-closure-1.md`

size=4727; sha256=95d1931fa67301070cad10c7353a29843178d38bed669b44a6659043c111c054; truncated=false

```text
# Independent external-critic closure review: T081-V4-SCHEMA-SLICE-3A

Reviewer: `/root/v4_schema_adversary`  
Builder: `/root/v4_schema_builder`  
Boundary: Claude external-critic dispositions  
Outcome: **PASS**

## Gate result

**13 passed out of 13 finding gates.** Claude findings CC-001 through CC-003
are independently closed, and the ten previously closed Codex design findings
remain closed with no regression. There are zero open blockers, highs,
mediums, or lows. The existing design PASS remains authoritative; this artifact
does not create a second design attestation.

## Claude finding dispositions

### CC-001 — concrete rollout gates

The revision defines two independent application flags and two independent
database gates, all default-off. Migration 0027 cannot enable them. The
deployment role alone can change database gates through an audited procedure;
the application role can only read them. Fixed compiled capability declarations
and the 0027 capability function are checked at startup and again in the write
transaction after the proposal lock.

Validator-2 candidate POST requires its application flag and database gate.
The 3A materialization POST requires both application flags, both database
gates, and both compiled capabilities. Audit GET requires only the 3A/read gate
and cannot materialize a missing projection. The four-state matrix explicitly
uses a preexisting v2 candidate: `v2-off/3A-on` permits audit of an existing
projection but rejects materialization with zero request, projection,
dependency, correction, or event rows. Proposal-before-gate locking plus
`FOR SHARE`/audited `FOR UPDATE` gate access gives deterministic concurrent
disable outcomes. Compatibility-release, mixed-instance, drain, rollback, and
database-capability mismatch cases are mandatory implementation tests; no flag
claims to prove fleet-wide rollout.

### CC-002 — correction-foundation scope

The Objective, invariant 3, detailed design, and Expected file scope now agree.
Slice 3A explicitly owns the shared proposal-scoped correction foundation and
its four named tables. It may read and verify canonical
`authoritativeCorrections` and referenced `officialDocuments` identity/evidence
fields only, reconstructing corrections separately from the four-field
applicability subtree. Complete ordered references into future Slice-3B
namespaces are retained to preserve one identity, while requirements,
recurrence, AMOC, incorporated-document, and service-bulletin semantics remain
deferred.

### CC-003 — inline repair only

The stale-event repair helper runs only opportunistically inside the existing,
authorized materialization POST transaction. It uses the same capability and
membership checks, total lock order, deterministic cause identity, and
idempotent event identity. Audit GET invokes detection-only behavior and is
side-effect-free. The design explicitly forbids a cron process, worker, queue
consumer, scheduler, CLI, startup sweep, repair endpoint, or other operational
writer.

## Prior-finding regression check

- DA-001 through DA-010 remain `closed` with their prior independent evidence.
- Added database gate rows preserve DA-010's proposal-first global lock order:
  writers take the proposal boundary before a gate lock, and downgrade takes
  the proposal table before the feature-gate table and all child/3A tables.
- The new scope wording preserves DA-002's single shared correction identity
  and does not add Slice-3B materialization.
- The repair clarification preserves DA-006's deterministic causal dependency,
  DA-007's exact-membership authorization, and append-only audit behavior.
- Candidate-only isolation, v1/v2 hash semantics, exact unknown handling,
  source-faithful series expressions, and absence of released readers or
  matching indexes are unchanged.

## Verification accounting

- Incoming external-critic packet freshness: **1 passed out of 1** at
  fingerprint
  `a3664385537c5f5492f53616b7d9b229f446af77e79256879ec9b06bc7eab70b`.
- Incoming packet SHA-256: 
  `2c473fbca1572cb0f7d46a47dd2aed251017652c6bc1a9334bb35b4c53a008a1`.
- Explicit bound inputs: **36 inspected out of 36**, including the successful
  Claude markdown and structured findings sidecar.
- Claude finding closures: **3 passed out of 3**.
- Preserved Codex design closures: **10 passed out of 10**.
- Total finding gate: **13 passed out of 13**.
- Packet/source scope: design-only; no implementation runtime result is claimed.

Implementation may advance under the existing design PASS, but the feature
gates, capability checks, four-state matrix, concurrent-disable behavior,
correction-foundation boundary, and inline repair semantics remain mandatory
implementation-review gates.

```
### `.ai/review-runs/T081-V4-SCHEMA-SLICE-3A/adversarial-implementation-ia002-ia005-closure.md`

size=1402; sha256=12df90292e9c0c53764ca44289ae852ba0426440c54bc0344d3f572a0f35360c; truncated=false

```text
# Targeted implementation closure: IA-002 and IA-005

Reviewer: `/root/v4_s3a_impl_adversary`  
Packet SHA-256: `0679973bdd6846fb025a77f8ed37187ee7e1773821c277037ed4b65465e2ecd8`  
Outcome: **PASS / PASS**

## IA-002

The reviewer verified that deferred PostgreSQL validation now derives the full
semantic set including synthetic designation-value nodes; verifies node type,
key, parent, ordinal, canonical hash, and deterministic identity; binds every
datum to its nearest semantic owner; and recomputes datum identities using
null-safe comparisons. Missing, extra, reordered, changed-value, wrong-owner,
forged-node, and stored-hash counterexamples are rejected. The listed-model
PostgreSQL test commits and reconstructs two synthesized designation nodes.

## IA-005

The reviewer verified exact correction counts/content/order, zero-based
contiguous ordinals, document identities, root/ref/evidence hashes, owner slice,
binding target type/key, generation, and binding hashes under deferred triggers
covering every Slice-3A table. Negative-index, incomplete, reordered,
wrong-binding, append-before/after, and SQL-null bypasses are closed. Downgrade
preserves locked occupancy refusal and removes every helper function.

The full disposable PostgreSQL matrix passed 9 out of 9 in
`t081_blockers_l`; cleanup dropped it and `paprnav_db` was not targeted. No
residual IA-002 or IA-005 finding remains.

```
### `.ai/review-runs/T081-V4-SCHEMA-SLICE-3A/adversarial-implementation-ia003-closure.md`

size=1916; sha256=8bc033f2545f85ec8dbb453b8599310e1897201d99466a5844df185fbd8c7b1e; truncated=false

```text
# Targeted implementation closure: IA-003

Date: 2026-09-09  
Reviewer: `/root/v4_s3a_impl_adversary`  
Builder/coordinator: `/root`  
Packet SHA-256: `a3084bacf0b883bbe3d1da74553671ab69635560de9a82ed9e3c1b64064e47cf`

## Verdict

**PASS.** No residual IA-003 finding.

## Independent closure evidence

- Canonical successor identity is compared exactly before resolution; unknown,
  mismatched, missing, and ambiguous targets remain non-resolved and create no
  target-local row or stale event.
- Deterministic outgoing dependencies resolve only to one exact predecessor AD
  projection. Each resolved signal creates one deterministic target-local
  incoming dependency, and the stale event names that exact same-projection
  cause through a composite foreign key and canonical cause envelope.
- PostgreSQL derives the proposal's own, predecessor, and successor AD numbers,
  sorts/deduplicates them, and obtains deterministic transaction advisory locks.
  The application, direct projection INSERT trigger, and deferred validator use
  the same database helper, closing both application and direct-SQL phantom
  predecessor races.
- Causal partial unique indexes, deterministic hashes, deferred global
  uniqueness validation, and direct-SQL negative coverage prevent forged,
  duplicate, or cross-projection event causes.
- PostgreSQL tests 09-11 cover exact, mismatched, and ambiguous resolution;
  test 12 covers both concurrent application orderings; test 13 proves a raw
  projection INSERT blocks on the database-native AD lock.
- The clean disposable PostgreSQL matrix passed 14/14. Focused host tests passed
  36/36 and the broader relevant host/calibration/API suite passed 50/50. All
  disposable databases were removed and `paprnav_db` was not targeted.

The reviewer also verified downgrade dependency order: tables/triggers are
removed before the advisory-lock helper, leaving no dangling dependency.

```
### `.ai/review-runs/T081-V4-SCHEMA-SLICE-3A/adversarial-implementation-ia004-closure.md`

size=1005; sha256=8d985334209fe3eca35fbd228d7783aeff03e028fc041385e91f73a6d54b363f; truncated=false

```text
# Targeted implementation closure: IA-004

Reviewer: `/root/v4_s3a_impl_adversary`  
Outcome: **PASS**

The reviewer verified that detail, reconstruction, and list GET paths perform
detection only and contain no commit, flush, event insertion, or repair call.
`projection_state()` is non-mutating. Stale repair is reachable only through
`materialize_applicability()` after application authorization and both database
write-gate checks; both normal materialization and idempotent retry invoke that
gated helper. Caller search found no alternate repair path.

The focused regression snapshots projection-event count across detail,
reconstruction, and list GET and proves it remains unchanged. The coordinator's
focused candidate/API/applicability suite passed 40 out of 40.

The reviewer noted that evidence verification can acquire a row lock, so the
detection docstring was narrowed from claiming no write locks to the exact
guarantee: no row mutation or event append. No residual IA-004 finding remains.

```
### `.ai/review-runs/T081-V4-SCHEMA-SLICE-3A/adversarial-implementation-initial.md`

size=5127; sha256=6125935f42332e4bd4add0f15c09cf30fb62773ac8c0cfac1645adb8bd36fc76; truncated=false

```text
# Adversarial implementation review — initial

Task: `T081-V4-SCHEMA-SLICE-3A`  
Reviewer runtime identity: `/root/v4_s3a_impl_adversary`  
Role: independent read-only implementation adversary  
Outcome: **FAIL — implementation gate blocked**

## Findings

### F1 — Blocker: implemented schema is not the approved typed relational design

Violated invariants: 5–7, 9, 11–18, 26–27; DA-001, DA-004, DA-005,
DA-008. Decision lines 663–924 require typed owner/value/scope/condition/
expression/rule/hint tables and deferred ownership/cardinality/cycle/evidence
checks. Migration 0027 lines 93–208 instead create broad semantic-node and
JSON-pointer datum tables. `_flatten` persists arbitrary shapes, while the
90-pair test proves only Python round trip and attribute absence.

Impact: direct SQL can commit malformed semantic shapes and references while
retaining valid-looking projection metadata; the implementation materially
deviates from the reviewed design.

Required closure: implement all approved typed tables and their discriminator,
ownership, cardinality, ordinal, reference, arity, and acyclicity constraints,
or return to design review and prove equivalent database enforcement for the
generic representation. Add PostgreSQL negative tests for every normative
typed constraint.

### F2 — Blocker: a projection root can commit with zero or partial children

Violated invariants: 4–7, 18–20, 27, especially invariant 5. Projection counts
are ordinary integers. `paprnav_v4_validate_app_projection` is a BEFORE INSERT
root trigger that validates copied bytes/envelope only; no deferred child-graph
constraint exists. The PostgreSQL forged-root test changes the root hash and
does not attempt a valid root with missing/extra/reordered/different children.

Impact: a direct writer can commit an incomplete immutable relational graph;
later application reconstruction is not database commit-time refusal.

Required closure: add deferred PostgreSQL validation that reconstructs the
complete typed representation, verifies counts/hashes/evidence/ownership, and
compares it to the exact candidate subtree. Add direct-SQL negative tests for
empty, missing, extra, reordered, differently-valued, and cross-reference
graphs.

### F3 — Blocker: supersession handling reopens DA-006

Violated invariants: 21–23 and DA-006. `projection_state` treats the first
relationship naming a proposal as predecessor as a stale cause without proving
successor canonical AD equality or unique predecessor resolution.
`_repair_stale_projection` writes `causing_dependency_id=None`; materialized
dependency rows remain unresolved with no target projection.

Impact: an untrusted candidate relation can stale a projection without the
approved evidence-bound resolution, and the event lacks exact causal identity.

Required closure: persist dependency resolution using successor-AD equality and
unique predecessor rules. Require stale events to reference the exact
same-projection dependency. Ambiguous/mismatched signals must remain unresolved.
Add positive and negative PostgreSQL/API tests.

### F4 — High: audit GET and list endpoints are write paths

Violated invariants: 21, 24 and CC-003. `projection_state` calls the mutating
repair helper; detail and list GET routes commit the resulting events.

Impact: audit reads become alternate writers and viewing a list can lock and
mutate multiple projections.

Required closure: make every GET/list/reconstruction path detection-only.
Invoke repair solely inside the authorized materialization POST transaction
with its request identity, locks, and both write gates. Prove GETs leave all
table/event counts unchanged.

### F5 — High: correction integrity and reconstruction are incomplete

Violated invariants: 3, 6–7 and DA-002. Correction rows are inserted, but no
exact correction reconstruction/verification exists. Expected child counts,
official-document identity, ordinals, owner slice, and evidence set are not
deferred database invariants. Verified reads ignore the correction foundation.

Impact: a projection can report verified with an absent, incomplete,
overcomplete, or disconnected shared correction foundation.

Required closure: reconstruct corrections exactly from their relational graph,
compare them to canonical proposal corrections, enforce completeness and
identity at commit, fail verified reads closed, and add direct-SQL negative
tests plus an exact 2008 fixture round trip.

## Verification accounting

- Packet digest verified as
  `34b8c671c36cf239a718bb03bbd521b02d2a719a930af319861bf039e8b61dd4`.
- All staged, unstaged, and untracked scope was inspected; nothing was staged.
- Callers/readers, migration, models, routes, schemas, services, fixtures, and
  tests were inspected. No released/customer consumer was found.
- A reviewer host-test attempt did not complete before its tool boundary and is
  not credited. PostgreSQL was not rerun by the reviewer and `paprnav_db` was
  never targeted.
- No files were edited by the reviewer.

Implementation review result: **FAIL; five findings remain open, including
three blockers.**

```
### `.ai/review-runs/T081-V4-SCHEMA-SLICE-3A/claude-external-critic-20260906T235706Z.findings.json`

size=7255; sha256=077940e41ca6e0678f39e5e10a634d2ba25d63e354126eca4078250172c263dc; truncated=false

```text
[
  {
    "id": "T081-V4-SCHEMA-SLICE-3A-CC-001",
    "severity": "medium",
    "invariant": "Every other safety/correctness invariant in this design is enforced by the database or application transaction rather than by operator discipline (e.g., invariant 2's 'creation-time validity is not trusted'); the staged validator-2/3A rollout should meet the same bar.",
    "summary": "The mandatory deployment order (apply 0027 -> dual-reader app -> enable v2 writer -> enable 3A routes) has no concrete code-level gate. The codebase has no existing feature-flag mechanism, so nothing prevents a rolling deploy from serving v2 writes or 3A routes from an instance before all instances are dual-readers.",
    "evidence": [
      "review-packet.md:1262-1269 'Deployment order is mandatory: 1. apply 0027 ... 2. deploy the compatibility application ... 3. enable the v2 writer after all serving instances are dual readers; and 4. enable the 3A materializer/routes only after v2 writes are proven.'",
      "grep for feature_flag/FEATURE_FLAG/ENABLE_*/settings.FEATURE across backend/app returned zero matches, confirming there is no existing toggle mechanism this design could rely on.",
      "Every other invariant in the same document (e.g., invariant 2, invariant 24) is phrased as a transaction-enforced or trigger-enforced guarantee, not a manual rollout instruction."
    ],
    "impact": "A rolling/blue-green deploy that briefly runs mixed old/new application instances (a routine production pattern) could serve v2 candidate writes or 3A materialization from a not-yet-fully-rolled-out fleet, or could enable 3A routes before the v2 writer has been proven safe in production, silently violating the design's own stated sequencing without any error, log, or DB rejection.",
    "requiredClosure": "Define a concrete, code-level gate (e.g., an environment/config flag read at router-registration or write-path time) that makes 'v2 writer enabled' and '3A routes enabled' explicit, independently togglable states rather than an implicit consequence of which code version is deployed. Add a test or startup check proving the 3A routes/v2 writer cannot activate merely because migration 0027 has run."
  },
  {
    "id": "T081-V4-SCHEMA-SLICE-3A-CC-002",
    "severity": "medium",
    "invariant": "The design's stated in-scope/out-of-scope boundary (Objective section) and its 'Expected file scope' section should name every namespace and table Slice 3A is authorized to touch, so an implementer or later reviewer can verify boundary compliance without re-deriving it from a 1,500-line design body.",
    "summary": "Section 2.1.1 requires Slice 3A to create a shared, proposal-scoped correction foundation that stores canonical `authoritativeCorrections` content and verified `officialDocuments` identity hashes -- two top-level V4 namespaces distinct from the four-field applicability subtree {productScopes, conditionDefinitions, applicabilityRules, applicabilitySearchHints}. Neither namespace is mentioned in the Objective's in/out-of-scope bullet list, nor explicitly named in the 'Expected file scope' section, even though the mandatory 2008-26-10 calibration assertion depends on it.",
    "evidence": [
      "review-packet.md:28-63 (Objective) lists what's out of scope for 3A/deferred to 3B but never mentions `authoritativeCorrections` or `officialDocuments`.",
      "review-packet.md:581-655 (section 2.1.1) defines `ad_v4_candidate_corrections`, `_correction_refs`, `_correction_semantic_bindings`, `_correction_evidence_links` storing `officialDocuments reference keys`, their `verified document-identity hashes`, and namespace refs spanning `requirements|recurrenceGroups|amocAuthorityProvisions` (3B-owned) in addition to 3A-owned namespaces.",
      "backend/app/schemas/ad_extraction_v4.schema.json $defs.proposal.properties includes `authoritativeCorrections` and `officialDocuments` as independent top-level arrays, confirming these are namespaces outside the four-field subtree definition in invariant 3.",
      "review-packet.md:1458-1489 ('Expected file scope') mentions only 'the additive 3A tables' generically and never names the correction-foundation tables or namespaces, while the mandatory test for 2008-26-10 (review-packet.md:1369-1372) requires 'exact shared correction-2010 foundation with two ordered refs, two evidence links once, one 3A scope binding, and one explicit future-3B requirement ref'."
    ],
    "impact": "An implementer following the Objective/Expected-file-scope sections literally could reasonably treat the correction-foundation tables as unauthorized scope creep and omit them, causing the mandatory 2008-26-10 reconstruction test (and the whole DA-002 closure) to fail; conversely, a later reviewer auditing 'did 3A only touch what it said it would' has no single authoritative scope list to check against, since the two scope-defining sections disagree with the detailed design.",
    "requiredClosure": "Update the Objective's out-of-scope list and the 'Expected file scope' section to explicitly name the correction-foundation tables and the `authoritativeCorrections`/`officialDocuments` namespaces they read/verify, so the document's own scope statement is internally consistent with section 2.1.1 and the mandatory calibration test."
  },
  {
    "id": "T081-V4-SCHEMA-SLICE-3A-CC-003",
    "severity": "low",
    "invariant": "'Write paths and administrative paths' asserts no new operational writer (job/CLI/seed/etc.) is added beyond the single platform-admin POST service.",
    "summary": "The stale-fold section introduces 'a background repair function [that] may append missing deterministic events after a crash,' which reads as a new asynchronous/scheduled process, apparently in tension with the explicit claim elsewhere that no provider job, CLI, seed, or generic writer is added.",
    "evidence": [
      "review-packet.md:1081-1085 'A background repair function may append missing deterministic events after a crash; it uses the same locks and event identity and requires no human review.'",
      "review-packet.md:1205-1213 ('Write paths and administrative paths') states 'No provider job, CLI, seed, V3 translator, calibration loader, frontend form, or generic ORM CRUD writer is added,' and that 'Its internal deterministic stale-event helper is part of the same service/repository boundary,' without clarifying whether the crash-repair helper is invoked synchronously (e.g., opportunistically on the next POST/GET) or via a new scheduled/background worker process."
    ],
    "impact": "If implementation interprets 'background repair function' as a new cron/worker process, that is new operational surface (deployment unit, scheduling, monitoring) not accounted for anywhere else in the design's operational sections, and could be missed by an implementation reviewer who only checks for 'no new job' against the explicit write-paths sentence.",
    "requiredClosure": "Clarify in the design that the repair helper is invoked inline/opportunistically from existing request paths (not a new scheduled process), or, if a real background worker is intended, add it explicitly to the write-paths/operational sections and its own authorization/idempotency contract."
  }
]

```
### `.ai/review-runs/T081-V4-SCHEMA-SLICE-3A/claude-external-critic-20260906T235706Z.md`

size=14994; sha256=0bee68926fcc21fa7dafb1a3cf06c239e3d91821710df8c19f54e4721d2289aa; truncated=false

```text
## 1. Scope Limitations

- This review run has **no code diff**. `git diff HEAD` and the packet's own "Diff against base" section are both empty; the working tree is clean except for the untracked `.ai/review-runs/T081-V4-SCHEMA-SLICE-3A/` review-run directory itself. The task is therefore a pure **design-decision review** (`decision.md`, embedded twice in the packet plus two internal adversarial rounds), not a review of implemented code, migrations, or tests.
- No AWS/IAM/Terraform/billing artifacts exist in this scope; the design is entirely a PostgreSQL/FastAPI schema-and-service proposal, so those review dimensions do not apply here.
- I independently re-derived the five v2 hash-domain hex strings (proposal, evidence-bindings, candidate-event, submission, submission-relationship, subtree, projection) in Python and they match the packet byte-for-byte. I cross-checked the design's characterization of the current schema (`ad_extraction_v4.schema.json`), migration `20260901_0026`, and calibration fixtures against the actual files in the repo; every specific claim I checked (condition subject shape, search-hint shape, expression node types, `changedSemanticRef` namespace enum, `officialDocument` shape, existing v1 hash domains, existing "any active membership" auth helper, existing deferred-constraint-trigger precedent, absence of a feature-flag mechanism) was accurate.
- I did not re-derive every one of the 28 numbered invariants line-by-line against every calibration fixture (e.g., full 224-row and 182-row cardinality re-enumeration); I relied on spot checks plus the internal adversary's already-closed, evidence-backed findings for those, per instructions not to repeat adequately-closed findings.
- Because there is no implementation yet, several of my observations are about the decision document's internal consistency and enforceability rather than runtime defects.

<!-- CLAUDE_FINDINGS_JSON -->
```json
[
  {
    "id": "T081-V4-SCHEMA-SLICE-3A-CC-001",
    "severity": "medium",
    "invariant": "Every other safety/correctness invariant in this design is enforced by the database or application transaction rather than by operator discipline (e.g., invariant 2's 'creation-time validity is not trusted'); the staged validator-2/3A rollout should meet the same bar.",
    "summary": "The mandatory deployment order (apply 0027 -> dual-reader app -> enable v2 writer -> enable 3A routes) has no concrete code-level gate. The codebase has no existing feature-flag mechanism, so nothing prevents a rolling deploy from serving v2 writes or 3A routes from an instance before all instances are dual-readers.",
    "evidence": [
      "review-packet.md:1262-1269 'Deployment order is mandatory: 1. apply 0027 ... 2. deploy the compatibility application ... 3. enable the v2 writer after all serving instances are dual readers; and 4. enable the 3A materializer/routes only after v2 writes are proven.'",
      "grep for feature_flag/FEATURE_FLAG/ENABLE_*/settings.FEATURE across backend/app returned zero matches, confirming there is no existing toggle mechanism this design could rely on.",
      "Every other invariant in the same document (e.g., invariant 2, invariant 24) is phrased as a transaction-enforced or trigger-enforced guarantee, not a manual rollout instruction."
    ],
    "impact": "A rolling/blue-green deploy that briefly runs mixed old/new application instances (a routine production pattern) could serve v2 candidate writes or 3A materialization from a not-yet-fully-rolled-out fleet, or could enable 3A routes before the v2 writer has been proven safe in production, silently violating the design's own stated sequencing without any error, log, or DB rejection.",
    "requiredClosure": "Define a concrete, code-level gate (e.g., an environment/config flag read at router-registration or write-path time) that makes 'v2 writer enabled' and '3A routes enabled' explicit, independently togglable states rather than an implicit consequence of which code version is deployed. Add a test or startup check proving the 3A routes/v2 writer cannot activate merely because migration 0027 has run."
  },
  {
    "id": "T081-V4-SCHEMA-SLICE-3A-CC-002",
    "severity": "medium",
    "invariant": "The design's stated in-scope/out-of-scope boundary (Objective section) and its 'Expected file scope' section should name every namespace and table Slice 3A is authorized to touch, so an implementer or later reviewer can verify boundary compliance without re-deriving it from a 1,500-line design body.",
    "summary": "Section 2.1.1 requires Slice 3A to create a shared, proposal-scoped correction foundation that stores canonical `authoritativeCorrections` content and verified `officialDocuments` identity hashes -- two top-level V4 namespaces distinct from the four-field applicability subtree {productScopes, conditionDefinitions, applicabilityRules, applicabilitySearchHints}. Neither namespace is mentioned in the Objective's in/out-of-scope bullet list, nor explicitly named in the 'Expected file scope' section, even though the mandatory 2008-26-10 calibration assertion depends on it.",
    "evidence": [
      "review-packet.md:28-63 (Objective) lists what's out of scope for 3A/deferred to 3B but never mentions `authoritativeCorrections` or `officialDocuments`.",
      "review-packet.md:581-655 (section 2.1.1) defines `ad_v4_candidate_corrections`, `_correction_refs`, `_correction_semantic_bindings`, `_correction_evidence_links` storing `officialDocuments reference keys`, their `verified document-identity hashes`, and namespace refs spanning `requirements|recurrenceGroups|amocAuthorityProvisions` (3B-owned) in addition to 3A-owned namespaces.",
      "backend/app/schemas/ad_extraction_v4.schema.json $defs.proposal.properties includes `authoritativeCorrections` and `officialDocuments` as independent top-level arrays, confirming these are namespaces outside the four-field subtree definition in invariant 3.",
      "review-packet.md:1458-1489 ('Expected file scope') mentions only 'the additive 3A tables' generically and never names the correction-foundation tables or namespaces, while the mandatory test for 2008-26-10 (review-packet.md:1369-1372) requires 'exact shared correction-2010 foundation with two ordered refs, two evidence links once, one 3A scope binding, and one explicit future-3B requirement ref'."
    ],
    "impact": "An implementer following the Objective/Expected-file-scope sections literally could reasonably treat the correction-foundation tables as unauthorized scope creep and omit them, causing the mandatory 2008-26-10 reconstruction test (and the whole DA-002 closure) to fail; conversely, a later reviewer auditing 'did 3A only touch what it said it would' has no single authoritative scope list to check against, since the two scope-defining sections disagree with the detailed design.",
    "requiredClosure": "Update the Objective's out-of-scope list and the 'Expected file scope' section to explicitly name the correction-foundation tables and the `authoritativeCorrections`/`officialDocuments` namespaces they read/verify, so the document's own scope statement is internally consistent with section 2.1.1 and the mandatory calibration test."
  },
  {
    "id": "T081-V4-SCHEMA-SLICE-3A-CC-003",
    "severity": "low",
    "invariant": "'Write paths and administrative paths' asserts no new operational writer (job/CLI/seed/etc.) is added beyond the single platform-admin POST service.",
    "summary": "The stale-fold section introduces 'a background repair function [that] may append missing deterministic events after a crash,' which reads as a new asynchronous/scheduled process, apparently in tension with the explicit claim elsewhere that no provider job, CLI, seed, or generic writer is added.",
    "evidence": [
      "review-packet.md:1081-1085 'A background repair function may append missing deterministic events after a crash; it uses the same locks and event identity and requires no human review.'",
      "review-packet.md:1205-1213 ('Write paths and administrative paths') states 'No provider job, CLI, seed, V3 translator, calibration loader, frontend form, or generic ORM CRUD writer is added,' and that 'Its internal deterministic stale-event helper is part of the same service/repository boundary,' without clarifying whether the crash-repair helper is invoked synchronously (e.g., opportunistically on the next POST/GET) or via a new scheduled/background worker process."
    ],
    "impact": "If implementation interprets 'background repair function' as a new cron/worker process, that is new operational surface (deployment unit, scheduling, monitoring) not accounted for anywhere else in the design's operational sections, and could be missed by an implementation reviewer who only checks for 'no new job' against the explicit write-paths sentence.",
    "requiredClosure": "Clarify in the design that the repair helper is invoked inline/opportunistically from existing request paths (not a new scheduled process), or, if a real background worker is intended, add it explicitly to the write-paths/operational sections and its own authorization/idempotency contract."
  }
]
```

## 2. Findings

### T081-V4-SCHEMA-SLICE-3A-CC-001 — Rollout sequencing has no code-enforced gate

See JSON above for full evidence. Every other safety property in this document is backed by a database trigger, composite FK, or in-transaction recheck (the document is explicit about this philosophy — e.g. "Eligibility is rechecked inside the write transaction; creation-time validity is not trusted"). The one exception is the mandatory four-step production rollout order, which currently depends entirely on operators deploying instances in the right sequence, in a codebase that has no existing feature-flag primitive to fall back on. This is exactly the kind of migration/rollout risk the review brief asks to be scrutinized closely.

### T081-V4-SCHEMA-SLICE-3A-CC-002 — Scope statement omits the correction-foundation namespaces it actually requires

See JSON above. This is a documentation-consistency finding, not a logic defect in section 2.1.1 itself (which I independently traced against the real `2008-26-10.proposal.json` correction-2010 object and schema and found accurate). The risk is that the parts of the document meant to bound scope (Objective, Expected file scope) don't match the part that actually defines the work (section 2.1.1), which is the exact kind of drift the "expected file scope" gate exists to prevent for later implementation reviewers.

### T081-V4-SCHEMA-SLICE-3A-CC-003 — "Background repair function" wording conflicts with the "no new job" claim

See JSON above. Low severity because it's a clarity/definition gap rather than a demonstrated defect, but worth resolving before implementation since it touches the operational-surface guarantee the design otherwise takes seriously.

## 3. Open Questions

- The design's own "Known uncertainty" item 4 (PostgreSQL deferred-constraint-trigger reconstruction cost on the 224-model packet) is an honestly flagged, accepted risk rather than a hidden one; I did not find a stronger technical objection to it beyond what's already recorded, but I'd still ask for a concrete statement-timeout/measurement plan before merging the migration, since it's the one place a "correctness" gate could become a production incident if it times out under load rather than just failing a test.
- Section 2.1.1's correction root is fixed at `generation 1` with no described path for a second generation (e.g., a later re-correction of the same official document pair). This is presumably deferred by design, but the document doesn't say so explicitly — worth a one-line confirmation that generation versioning is out of scope for 3A/3B and reserved for a future slice.
- Is `platform_admin` scoped globally to the user (so "another valid membership" language in invariant 24 is about the user having admin rights in a *different* org) or could a user hold `platform_admin` in one org and a non-admin role in another? The design's authorization contract reads correctly either way, but a one-line model description would remove ambiguity for implementers.

## 4. Verification Notes

- Confirmed via direct hex computation that all seven v2 hash-domain byte strings in the packet are correct.
- Confirmed the existing v1 hash-domain constants in `backend/app/services/ad_v4_candidates.py:49-53` follow the same naming convention the v2 domains extend.
- Confirmed `conditionSubject`, `searchHint`, `expression`, `applicabilityRule`, `changedSemanticRef`, `officialDocument`, and `knownString` definitions in `backend/app/schemas/ad_extraction_v4.schema.json` match every specific structural claim made about them in the decision packet.
- Confirmed the existing `ensure_platform_admin`-style "any active membership" authorization pattern in `backend/app/api/routes/admin.py:19-26` and the `Idempotency-Key`/`Paprnav-Acting-Membership-Id` header conventions in `backend/app/api/routes/ads.py`, both cited as evidence in the closed DA-007 finding — accurate.
- Confirmed `CREATE CONSTRAINT TRIGGER ... DEFERRABLE INITIALLY DEFERRED` is already used four times in `20260901_0026_add_ad_v4_candidates.py`, supporting the technical feasibility of the proposed deferred-completeness-check pattern for Slice 3A.
- Confirmed the real `2008-26-10.proposal.json` fixture's `authoritativeCorrections` content matches the packet's stated correction-2010 example exactly (two changed-semantic-refs, two evidence keys).
- Confirmed the currently-stored `2002-13-04.proposal.json` fixture still uses the old flattened v1 `manufacturer: "multiple"` / 6-model hint shape, consistent with this being a design-only phase where the "corrected" v2 fixtures described in the decision are not yet implemented.
- Did not run backend tests or lint, since there is no code change in this review's scope (diff against base is empty); running the existing v1 test suite would not exercise anything this design changes.

## 5. Brief Summary

This is a mature, twice-adversarially-reviewed design document with no accompanying code change. All ten previously-closed internal findings that I spot-checked (DA-004's series-expression/canonicalization-version fix, DA-010's rollout/downgrade lock ordering, plus cross-checks of DA-001/002/005/006/007/008/009 against the real schema and fixtures) are supported by accurate evidence and appear genuinely closed. My independent pass surfaces three new, non-blocking findings: an unenforced production rollout sequence (CC-001), a scope-statement/detailed-design inconsistency around the correction-foundation namespaces (CC-002), and an ambiguous "background repair function" description (CC-003). None of these are blockers to a design PASS, but CC-001 and CC-002 should be resolved before implementation begins, given the document's own stated bar of "server-enforced, not operator-trusted" invariants.
```
### `.ai/review-runs/T081-V4-SCHEMA-SLICE-3A/closure.md`

size=217; sha256=a082505d61b0ad9d35647c1072f4f0d077223bf705d766bf60827bef6163361f; truncated=false

```text
# Closure report: T081-V4-SCHEMA-SLICE-3A

## Outcome

## Invariants verified

## Findings disposition summary

## Verification performed

## Final scope reviewed

## Accepted risks and deferred work

## Not verified

```
### `.ai/review-runs/T081-V4-SCHEMA-SLICE-3A/decision.md`

size=91684; sha256=50effad6a01fdb75a1d4594b170bed35f3c977464f4f83a81919793d553df466; truncated=false

```text
# Decision packet: T081-V4-SCHEMA-SLICE-3A

Status: design reviewed; external-critic remediations pending independent verification

Builder: `/root/v4_schema_builder`

Governing contract: `.ai/AD_EXTRACTION_DOMAIN_CONTRACT.md` version 1.1

Predecessor: closed `T081-V4-SCHEMA-SLICE-2` candidate-validation and
immutable-proposal boundary

## Objective

After design approval, implement one additive, candidate-only relational
projection of the applicability subset of an immutable V4 proposal. The slice
materializes and reconstructs only:

- `productScopes` and their product roles, source manufacturer values,
  manufacturer normalization assertions, model lists or series expressions,
  and serial/part-number scopes;
- `conditionDefinitions`, their typed subjects and explicit three-valued
  values;
- the nested three-valued expression trees and `applicabilityRules` that refer
  to those scopes and conditions; and
- non-controlling `applicabilitySearchHints`.

Slice 3A also creates the shared, proposal-scoped correction foundation named
in section 2.1.1. It reads and verifies the canonical
`authoritativeCorrections` namespace and the referenced `officialDocuments`
identity/evidence fields, materializes
`ad_v4_candidate_corrections`, `ad_v4_candidate_correction_refs`,
`ad_v4_candidate_correction_semantic_bindings`, and
`ad_v4_candidate_correction_evidence_links`, and reconstructs each correction
object separately from the four-field applicability subtree. This is explicit
3A scope needed to preserve one cross-slice correction identity; it does not
materialize obligation or document semantics.

The projection is bound to one Slice-2 candidate proposal, its canonical hash,
its evidence-binding hash, and a fixed materializer version. It remains
unreviewed and `candidate_only`. Relational reconstruction must reproduce the
canonical applicability subtree exactly and must never copy retained source
text.

This is deliberately the first half of the originally proposed normalized
schema slice. The following are not part of Slice 3A:

- requirements, actions, timing, recurrence groups, branches, terminating
  effects, incorporated-document/service-bulletin content, AMOC provisions,
  or aircraft-specific AMOC use (Slice 3B). The shared correction foundation
  records complete ordered references into these deferred namespaces but does
  not interpret or materialize their 3B semantics;
- human approval, signoff, rejection, publication, current selection, or a
  reviewer GUI;
- released catalog, aircraft matching, coverage, compliance, or due-state
  readers;
- V3 mutation, translation, fallback, or compatibility-row materialization;
- aircraft/component canonical identity migration or aircraft configuration;
  and
- fuzzy aliases, inferred series membership, or an authoritative manufacturer
  or model registry.

## User-visible outcome

There is no maintenance-shop or customer-visible behavior change. An active
platform administrator may explicitly request deterministic materialization of
an existing V4 candidate and inspect its verified projection for audit. The
response identifies the candidate proposal, projection/materializer version,
applicability-subtree hash, counts, evidence-binding hash, and a computed
candidate projection state. It never calls the released AD catalog or claims
that any aircraft is or is not affected.

The endpoint and database use the label `candidate_only`; they do not use
`approved`, `current`, `released`, `actionable`, `applicable`, or `not
applicable` as a projection-level decision. A canonical field may itself carry
the source-supported three-valued state `not_applicable`; that field state does
not turn the candidate projection into an approved conclusion.

## Safety and correctness invariants

The following are falsifiable design and implementation gates.

1. A projection references exactly one immutable
   `ad_v4_candidate_proposals` row and repeats its directive ID, schema version,
   validator version, canonicalization version, canonical hash, and
   evidence-binding hash under composite FK/trigger enforcement.
2. Only a proposal with database gate `candidate_only`, valid canonical bytes,
   valid Slice-2 envelopes, and a currently eligible exact Slice-1 evidence
   lifecycle may be materialized. Eligibility is rechecked inside the write
   transaction; creation-time validity is not trusted.
3. The applicability materialized source is the four-field canonical subtree
   `{productScopes, conditionDefinitions, applicabilityRules,
   applicabilitySearchHints}` extracted from verified proposal bytes. The only
   additional top-level namespaces read are the explicitly scoped
   `authoritativeCorrections` and referenced `officialDocuments` fields used by
   the shared correction foundation. No other namespace is silently projected.
4. Reconstructing that subtree solely from relational rows, including every
   property-presence choice and array order, then applying the Slice-2
   canonicalizer produces byte-identical subtree bytes and the stored subtree
   hash.
5. PostgreSQL deferred checks compare the reconstructed relational JSONB to the
   exact four-field subtree in the parent proposal's verified JSONB mirror.
   Direct SQL cannot commit a partial, cross-candidate, or differently valued
   projection whose root hashes appear valid.
6. Every semantic node belongs to the same projection and proposal. Every
   typed child, expression edge/reference, rule exclusion, identity mapping,
   dependency, and evidence link uses a composite same-projection FK; a bare ID
   is never the only relationship guard.
7. Every evidence-bearing canonical object has exactly the evidence-key set in
   the candidate. Evidence links resolve to Slice-2
   `ad_v4_candidate_evidence_bindings` for the same proposal. They store IDs and
   hashes only; no fragment text, page text, PDF bytes, or repeated citation
   prose exists in any Slice-3A table.
8. Source manufacturer values and model/series designations are preserved
   byte-for-byte as validated NFC strings. They are never case-folded, trimmed,
   punctuation-folded, concatenated, or replaced by a normalized identity.
9. Candidate normalization is a separate assertion with explicit origin,
   version, review state, and evidence. A known normalized manufacturer value
   comes only from the canonical proposal. Current V4 supplies no per-model
   normalized value, so model normalization is explicitly `unknown` with
   reason `not_extracted`; it is never inferred from spelling similarity. The
   model mapping is one-to-one with its exact designation-value occurrence,
   inherits source support from one parent designation-scope node, and does not
   repeat an evidence link for every listed model.
10. Every normalization row is `unreviewed_candidate`. No aircraft row or
    released directive may reference it, and no matching/current-selection
    reader exists in this slice.
11. SQL `NULL` means only that a property is absent or that a column is unused
    by the row's checked discriminator. Regulatory uncertainty is always an
    explicit `unknown` state with controlled reason, temporal scope, and
    evidence; `not_applicable` has the same explicit support.
12. A source property that is absent is recorded as `property_absent`, distinct
    from an explicit canonical `unknown`. Reconstruction omits an absent
    property and emits an explicit unknown object for an unknown property.
13. Listed models, serial/part values, and identifier ranges remain exact
    source values. A series expression is preserved as source text and has
    evaluation state `unknown/unsupported_expression`; Slice 3A executes no
    regex, prefix, series, serial, or part-number comparator.
14. Conditions preserve their exact type, operator, optional comparator
    version, temporal-basis discriminator, subject property presence, compound
    source display text, typed designation groups/members, and three-valued
    subject assertions. Every condition type/operator pair accepted by the
    Slice-2 schema is representable but explicitly `unevaluated`; 3A invents no
    unreviewed compatibility matrix. No display JSON or opaque predicate JSON
    is relational authority.
15. Expression rows implement only `scope_ref`, `predicate_ref`, `rule_ref`,
    `not`, `all`, and `any` for applicability rules. Requirement-state refs are
    rejected at this boundary. Arity, sequence, same-projection reference
    types, rule cycles, and exclusion cycles are enforced again at materialize
    and reconstruct time.
16. Expression evaluation is out of scope. Stored expression nodes declare the
    fixed result domain `kleene_true_false_unknown_v1` and evaluator version,
    but no row records a truth result for an aircraft.
17. Search hints remain `controlling = false` and `exhaustive = false`, have
    no FK route from an expression, and cannot establish or suppress a match.
18. One source condition, rule, and evidence binding shared by 182 models
    produces one condition row, one rule row, and no per-model evidence-link
    copies. All links reuse Slice-2 binding IDs rather than copying source
    identity or text. The 2024-14-03 fixture is the mandatory bloat regression.
19. Materialization is deterministic and idempotent for
    `(proposal_id, materializer_version)`. Identical retries return the same
    root; different request keys may record separate audit requests without
    duplicating semantic content.
20. Concurrent materialization of the same proposal converges on one complete
    root and one deterministic row set. No uniqueness race returns 500, leaks a
    partial graph, or produces different node identities.
21. Correction or replacement never updates a projection. A later candidate
    relationship appends a hash-chained stale event for the predecessor
    projection. Evidence lifecycle change is detected live and may append the
    same derived stale fact; it never rewrites prior rows.
22. A candidate supersession relation is stored only as an evidence-bound,
    untrusted dependency signal. It can cause a stale event only when its
    successor AD number equals this proposal's known, evidence-bound canonical
    AD number and its predecessor resolves uniquely. Otherwise it remains
    unresolved with no side effect. Every stale event names that exact
    same-projection dependency row. It never changes released AD status or
    proves legal supersession.
23. Projection reads fold the immutable event chain and recheck parent/evidence
    integrity. Missing, ambiguous, contradictory, or invalidated dependencies
    fail closed to `candidate_stale` or `dependency_unresolved`; no stale root
    is presented as verified/current.
24. POST and both audit GET endpoints require
    `Paprnav-Acting-Membership-Id`. Only the exact selected active membership
    belonging to the caller and carrying `platform_admin` may authorize the
    transaction. POST snapshots membership, organization, role, status,
    action, policy version, and claims hash. GET locks and revalidates the exact
    selected membership for that transaction. Another valid membership cannot
    rescue an inactive, shop, foreign, or revoked selected membership.
25. V1/V2/V3 rows and all released/search/matching/compliance/due readers are
    behaviorally unchanged. Repository search and route tests prove that no
    existing reader imports or queries a Slice-3A table.
26. Slice 3A creates only integrity, reconstruction, audit, and stale-fold
    indexes used by its own bounded service. It creates no normalized-token,
    aircraft-identity, or matching hot-path index and makes no readiness claim.
    A reviewed identity bridge and its indexes belong to the later matching
    slice.
27. All Slice-3A rows are append-only. PostgreSQL rejects UPDATE and DELETE,
    including attempted normalization or stale-state edits.
28. Upgrade performs only the locked Slice-2 v1 version-metadata backfill and
    no semantic/canonical/evidence backfill. Downgrade locks the Slice-2
    proposal boundary first, then child and 3A tables, refuses while any 3A or
    v2 row exists, and succeeds/re-upgrades only for v1-only/empty-3A state.
    Concurrent insert/drop cannot deadlock or lose rows.
29. Validator-2 writes and Slice-3A routes have independent, default-off
    application flags and database gates. A 3A materialization requires both
    write and 3A gates; audit requires only the 3A/read gate. Every request also
    proves the compiled application version and migration-0027 capability at
    startup and inside its transaction. Migration presence alone never enables
    either surface, and a gate is not evidence that a fleet-wide compatibility
    rollout completed.

## Current behavior and authoritative representation

Slice 1 retains immutable source documents, page renditions, text versions,
single-page exact evidence fragments, and fragment lifecycle chains. Slice 2
validates raw V4 bytes, canonicalizes the full proposal, snapshots exact
admitted evidence bindings, and stores immutable candidate content,
submissions, relationships, and creation events. Its database gate is always
`candidate_only`.

The Slice-2 canonical bytes remain candidate authority. Slice 3A is a derived,
lossless relational projection used only for audit and later reviewed
development. The projection never becomes official evidence or reviewed
structured AD truth merely because round-trip equality succeeds.

Existing V3 `applicability_targets`, `ad_target_applicability`, compliance
requirements, released catalog rows, and their copied JSON/citations are not a
source for Slice 3A and are not populated by it. They remain isolated legacy
representations.

The five executable Slice-2 calibration proposals currently contain:

| AD | scopes | listed models | conditions | rules | hints | applicability-relevant change signal |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| 1998-17-11 | 2 | 81 | 2 | 1 | 0 | none |
| 2002-13-04 | 1 | 6 | 4 | 1 | 1 | none |
| 2008-26-10 | 1 | 182 | 4 | 1 | 0 | authoritative correction |
| 2011-10-09 | 1 | 224 | 0 | 1 | 0 | supersession relation |
| 2024-14-03 | 5 | 182 | 1 | 1 | 0 | none |

Those are calibration expectations, not facts to hard-code in the
materializer.

## Proposed design

### 0. Required backward-compatible Slice-2 schema corrections

Slice 3A cannot faithfully materialize known predecessor defects. Its future
implementation therefore includes a narrowly versioned correction to the
Slice-2 canonical boundary before any 3A row is written.

The current schema, validator, and canonicalization artifacts are frozen as
`paprnav-ad-v4-validator-1` and `paprnav-ad-v4-c14n-1` for verification of
already stored candidates. A new closed schema/semantic profile
`paprnav-ad-v4-validator-2` remains `schemaVersion: ad_extraction_v4` and uses
the distinct canonicalization profile `paprnav-ad-v4-c14n-2`. New submissions
use only the v2 pair. Stored v1 candidates retain their bytes, hashes, events,
audit readability, and `candidate_only` gate. They are neither rewritten nor
deleted. A validator-1 proposal containing either defect below receives stable
materializer refusal
`predecessor_semantic_defect`; the safe path is a new validator-2 candidate
linked by `corrects_candidate`. Refusal to derive new rows is not mutation or
invalidation of the stored candidate.

#### Explicit uncertainty for the 1998 packet

The source wording “If it cannot be determined” remains in its admitted exact
evidence fragment. It is not persisted as the artificial known value
`unknown_requires_compliance`. The corrected `condition-provenance-unknown`
uses the already closed known/unknown/not-applicable union:

```json
"attributeValue": {
  "state": "unknown",
  "reason": "not_observed",
  "temporalScope": {"kind": "at_applicability_evaluation"},
  "evidenceKeys": ["ev-unknown-provenance"]
}
```

Its condition remains a typed `reviewed_manual_predicate/requires_review` leaf.
Kleene evaluation is not performed in 3A, but any future evaluator must treat
the unknown operand as unknown/fail-closed, not false. Validator 2 rejects the
exact reserved semantic sentinel `unknown_requires_compliance` in a known
union. It does not guess from broad words such as “unknown” in authentic source
text. A schema negative and semantic negative enforce the reserved-token rule.

Implementation must preserve byte-identical validator-1/c14n-1 artifacts and
dispatch stored read verification by the row's recorded validator and
canonicalization versions; new writes and the corrected 1998 calibration
candidate use validator-2/c14n-2. Regression gates prove the old stored
candidate still verifies under v1, the new validator rejects the sentinel, the
corrected proposal stores under v2 with a new canonical hash, and no existing
row/event changes.

#### Compound designation groups and search-hint associations

Validator 2 adds closed, optional typed designation-group structures. Source
display wording is stored separately and is never parsed to create members.
For a condition subject the shape is:

```json
"designationGroup": {
  "groupKey": "...",
  "sourceDisplayText": {"state":"known","value":"...","evidenceKeys":["..."]},
  "association": "all_members|any_member|source_group|unknown",
  "members": [
    {
      "memberKey":"...",
      "designationKind":"model|series_expression",
      "sourceDesignation":"...",
      "manufacturer": {"state":"known|unknown|not_applicable", "...":"..."},
      "evidenceKeys":["..."]
    }
  ],
  "evidenceKeys":["..."]
}
```

For `association: unknown`, the group also requires controlled reason and
temporal scope. Member manufacturer uses the existing explicit union. Member
and group keys are unique; member ordering is a canonical set keyed by
`memberKey`. `sourceDisplayText` is display/evidence fidelity only. No service
splits commas, slashes, conjunctions, whitespace, or prefixes.

The corrected 2002 candidate represents:

- exact display `6314,6324,6364` plus three `any_member` magneto model members;
- exact display `C-125,C145,O-300,IO-360,TSIO-360` plus five `any_member`
  engine model/series members;
- `LTSIO-520-AE` as one atomic member; and
- its non-exhaustive airframe hint as seven explicit manufacturer groups and
  20 source-faithful typed members: 19 exact model-designation members plus one
  Cessna `series_expression` member whose exact expression text is
  `172A through 172H`, evaluation state is `unknown`, and reason is
  `unsupported_expression`. Cessna has eight exact model members plus that one
  expression; Beagle has 1, Cirrus 2, Globe Swift 2, Maule 1, Piper 2, and
  Reims (Cessna) 3 exact models. The old fabricated manufacturer value
  `multiple` is not a normalized identity. No exact `172A`, `172B`, ...,
  `172H` member is inferred from the expression.

The retained-source count oracle is exact: Cessna model members are `170`,
`170A`, `170B`, `172`, `172XP`, `336`, `337`, and `T303`, plus the one series
expression; Beagle is `B242-C`; Cirrus is `SR20`,`SR22`; Globe Swift is
`GC-1A`,`GC-1B`; Maule is `M4`; Piper is `PA-28R-201T`,`PA-34`; and Reims
(Cessna) is `FA172`,`F337`,`FR172`. These are 19 exact models + 1 expression,
not 27 exact models.

The corrected 2024 candidate preserves exact display `GFC 500 and GSA 28` and
uses `all_members` with two Garmin model members. Its STC and master-drawing
fields remain separate condition-subject assertions.

Validator-2 search hints replace the ambiguous flat manufacturer/models pair
with `sourceDisplayText` plus `manufacturerModelGroups`. Each group has a
manufacturer explicit union, exact model-member rows, association state, and
evidence. If the source does not establish a pairing, manufacturer association
is explicit `unknown/source_ambiguous`; models remain individually queryable
but not assigned to a maker. Hints remain fixed `controlling:false` and
`exhaustive:false` and cannot be referenced by an expression.

Validator-1 candidates remain readable. Validator 2 accepts the old atomic
`modelOrSeries` only as one unparsed source value and forbids using it as a
typed member set. Corrected calibration fixtures use the group form wherever
the source expresses more than one designation. The implementation scope
therefore includes versioned schema/validator dispatch, the 1998, 2002, and
2024 proposal corrections, and predecessor calibration/service regressions;
retained PDFs and fragment selections do not change.

#### Validator-2 canonicalization and hash domains

Validator 2 closes every new object with `additionalProperties:false` and
uses these normative shapes:

- condition `designationGroup` requires exactly `groupKey`,
  `sourceDisplayText`, `association`, `members`, and `evidenceKeys`; it permits
  `reason` and `temporalScope` only when `association:"unknown"`, when both are
  required;
- each designation-group member requires `memberKey`, `designationKind`,
  `manufacturer`, and `evidenceKeys`. The closed `model` branch additionally
  requires `sourceDesignation`. The closed `series_expression` branch instead
  requires `expressionText`, fixed `evaluationState:"unknown"`, and fixed
  `reason:"unsupported_expression"`; it forbids `sourceDesignation` and any
  parsed lower/upper/prefix member fields;
- each v2 applicability search hint requires exactly `hintKey`, `productRole`,
  `sourceDisplayText`, `manufacturerModelGroups`, `controlling:false`,
  `exhaustive:false`, and `evidenceKeys`; the v1 flat `manufacturer`/`models`
  pair is not legal in validator 2;
- each manufacturer/model group requires `groupKey`, the existing explicit
  manufacturer union, `association`, `members`, and `evidenceKeys`; unknown
  association additionally requires controlled `reason` and `temporalScope`;
  and
- each hint member uses the same closed `model|series_expression` one-of and
  exact field exclusions as a designation-group member.

`sourceDisplayText`, manufacturer unions, temporal scope, identifiers, and
evidence keys reuse the already closed V4 definitions. No new open object,
free-form discriminator, or unannotated array is permitted.

`paprnav-ad-v4-c14n-2` inherits every scalar, object-key, decimal, Unicode,
date, and existing-array rule from c14n-1. It adds only these closed array
annotations introduced by validator 2:

- `designationGroup.members`: set keyed by unique `memberKey`;
- `applicabilitySearchHints[].manufacturerModelGroups`: set keyed by unique
  `groupKey`; and
- `manufacturerModelGroups[].members`: set keyed by unique `memberKey`.

The `designationGroup` and `sourceDisplayText` shapes are objects, not arrays.
Every v2 array, including inherited arrays, has an explicit
`x-paprnav-array-kind`; validator-2 meta-tests fail any missing annotation.
Within a group, `model` members carry one exact designation; a
`series_expression` member carries one exact expression plus fixed
`evaluationState:"unknown"` and `reason:"unsupported_expression"`. C14n-2
does not expand, parse, or reorder characters within that expression. Adding
or changing any array shape requires c14n-3 and a new reviewed boundary.

Every separator below is the displayed ASCII/UTF-8 string followed by exactly
one NUL byte `0x00`. Complete bytes, including the final `00`, are normative:

| v2 hash object | ASCII before NUL | complete hex bytes |
| --- | --- | --- |
| proposal | `paprnav:ad_extraction_v4:proposal:paprnav-ad-v4-c14n-2` | `706170726e61763a61645f65787472616374696f6e5f76343a70726f706f73616c3a706170726e61762d61642d76342d6331346e2d3200` |
| evidence bindings | `paprnav:ad_extraction_v4:evidence-bindings:2` | `706170726e61763a61645f65787472616374696f6e5f76343a65766964656e63652d62696e64696e67733a3200` |
| candidate event | `paprnav:ad_extraction_v4:candidate-event:2` | `706170726e61763a61645f65787472616374696f6e5f76343a63616e6469646174652d6576656e743a3200` |
| submission | `paprnav:ad_extraction_v4:submission:2` | `706170726e61763a61645f65787472616374696f6e5f76343a7375626d697373696f6e3a3200` |
| submission relationship | `paprnav:ad_extraction_v4:submission-relationship:2` | `706170726e61763a61645f65787472616374696f6e5f76343a7375626d697373696f6e2d72656c6174696f6e736869703a3200` |

For each object, `hash = lowercase_hex(SHA-256(domain_bytes ||
restricted_jcs_v2(envelope)))`. The proposal envelope is the closed v2 root.
Other v2 envelopes retain the v1 field meanings but use fixed literal versions
`ad-v4-evidence-bindings-v2`, `ad-v4-candidate-created-v2`,
`ad-v4-submission-v2`, and `ad-v4-submission-relationship-v2`. Each v2 audit
envelope additionally contains exactly
`validatorVersion:"paprnav-ad-v4-validator-2"` and
`canonicalizationVersion:"paprnav-ad-v4-c14n-2"`. These fields are
server-derived. V1 rows retain their exact v1 envelope bytes and v1 domains;
their hashes are never recomputed under v2.

Proposal content identity and reuse are scoped by `(directive_id,
validator_version, canonicalization_version, canonical_hash)`. Therefore the
same logical source values submitted under v1/c14n-1 and v2/c14n-2 produce
distinct proposal/hash identities, even if their restricted-JCS payload bytes
happen to match. Binding, submission, relationship, and event identity/retry
comparison likewise occurs only within an identical validator/canonicalization
pair and its version-specific domain. Cross-version equality never causes
reuse.

### 1. Projection and hash boundary

Define canonical applicability subtree `A(P)` from verified proposal `P` as
exactly:

```json
{
  "productScopes": P.productScopes,
  "conditionDefinitions": P.conditionDefinitions,
  "applicabilityRules": P.applicabilityRules,
  "applicabilitySearchHints": P.applicabilitySearchHints
}
```

The properties appear under validator-2/c14n-2 canonical object ordering. The
3A materializer accepts only `paprnav-ad-v4-validator-2` with
`paprnav-ad-v4-c14n-2`; v1 candidates remain dual-reader auditable but are not
projected. Array set/sequence behavior is the explicit c14n-2 contract above;
Slice 3A defines no alternative canonicalizer.

`applicability_subtree_hash` is lowercase hex SHA-256 of:

```text
UTF-8("paprnav:ad_extraction_v4:applicability-subtree:paprnav-ad-v4-c14n-2")
|| 0x00 || restricted_jcs(A(P))
```

The complete subtree domain bytes, including the final NUL, are
`706170726e61763a61645f65787472616374696f6e5f76343a6170706c69636162696c6974792d737562747265653a706170726e61762d61642d76342d6331346e2d3200`.

Materializer version is fixed as `paprnav-ad-v4-app-materializer-2`.
Projection identity hash uses:

```text
UTF-8("paprnav:ad_extraction_v4:applicability-projection:2") || 0x00 ||
restricted_jcs({
  "version":"ad-v4-applicability-projection-v2",
  "proposalId": proposal_id,
  "proposalCanonicalHash": proposal_canonical_hash,
  "evidenceBindingHash": evidence_binding_hash,
  "validatorVersion":"paprnav-ad-v4-validator-2",
  "canonicalizationVersion":"paprnav-ad-v4-c14n-2",
  "materializerVersion":"paprnav-ad-v4-app-materializer-2",
  "applicabilitySubtreeHash": applicability_subtree_hash,
  "semanticNodeHashes":[...sorted by node type and node key...],
  "evidenceLinkHashes":[...sorted by node key and evidence key...]
})
```

The complete projection domain bytes, including final NUL, are
`706170726e61763a61645f65787472616374696f6e5f76343a6170706c69636162696c6974792d70726f6a656374696f6e3a3200`.

Every row ID is server-derived as its table prefix plus the first 32 lowercase
hex characters of a domain-separated full identity hash. Each row stores the
full identity hash and a uniqueness constraint; a truncated-ID collision with
a different full hash is an integrity error, not reuse.

### 2. Additive PostgreSQL mapping

All tables use explicit stable string codes plus CHECK constraints rather than
application-only enums. Every FK named below is `ON DELETE RESTRICT`; every
table receives an UPDATE/DELETE rejection trigger.

#### 2.1 Root, request, lifecycle, and dependencies

`ad_v4_candidate_app_projections`

- `id`, full `identity_hash`, `proposal_id`, `directive_id`;
- repeated `schema_version`, `validator_version`, `canonicalization_version`,
  `proposal_canonical_hash`, and `evidence_binding_hash`;
- fixed `materializer_version`, `applicability_subtree_hash`,
  `projection_hash`, and constant `gate = 'candidate_only'`;
- exact counts for semantic nodes, typed rows, and evidence links;
- `created_at`; no mutable status/current/approval/release column;
- UNIQUE `(proposal_id, materializer_version)`, UNIQUE `identity_hash`, and
  UNIQUE `(id, proposal_id)`; and
- a composite parent check/trigger requiring all repeated columns to equal the
  referenced Slice-2 candidate proposal and its gate to remain candidate-only.

`ad_v4_candidate_app_materialization_requests`

- immutable `id`, projection/proposal/directive IDs, actor user, exact
  authorizing membership and organization, snapshotted role/status, fixed
  policy name/version/claims hash, fixed endpoint action, idempotency key,
  request hash, and created time;
- actor/role/status CHECKs require active platform admin;
- UNIQUE `(actor_user_id, authorizing_membership_id, endpoint_action,
  auth_policy_version, idempotency_key)`; and
- composite FKs require request projection/proposal/directive equality.

`ad_v4_candidate_app_projection_events`

- `id`, projection/proposal IDs, `sequence_number`, event type
  `materialized|candidate_corrected|candidate_replaced|
  evidence_invalidated|candidate_supersession_signal`, reason code, optional
  causing Slice-2 relationship ID, lifecycle-event ID, projection ID, or
  `causing_dependency_id`; predecessor event hash, canonical event bytes/hash,
  actor kind `platform_admin|system`, actor request ID when platform-admin,
  and occurred time;
- sequence 0 is exactly one `materialized` root with null predecessor; later
  events require the previous same-projection hash;
- closed discriminator checks require: `materialized` names only its request;
  `candidate_corrected|candidate_replaced` name only the matching Slice-2
  relationship; `evidence_invalidated` names only the matching lifecycle
  event; and `candidate_supersession_signal` names only a same-projection
  incoming dependency row through composite FK `(projection_id,
  causing_dependency_id)`;
- system events have no human actor and name exactly one deterministic causal
  row;
  platform-admin events require a request; and
- UNIQUE `(projection_id, sequence_number)`, UNIQUE `(projection_id,
  event_hash)`, UNIQUE `(projection_id, event_type, causing_dependency_id)`
  where a dependency is present, and equivalent partial causal uniqueness keys
  for relationship and lifecycle causes.

`ad_v4_candidate_app_change_dependencies`

- semantic node/projection/proposal IDs and dependency kind
  `outgoing_supersedes|outgoing_partially_supersedes|
  incoming_supersession_signal`;
- an outgoing supersession row preserves predecessor and successor AD numbers
  exactly as stated and is evidence-bound to both the relation and this
  proposal's known `directiveIdentity.adNumber` assertion;
- resolution state `resolved_candidate|unresolved|ambiguous`, with target
  directive/projection IDs used only for a uniquely resolved candidate signal;
- explicit unresolved reason instead of a nullable target meaning unknown; and
- evidence links to the dependency semantic node. No dependency row changes a
  released directive or becomes legal supersession authority.

For every canonical relation, the successor must equal the proposal's known,
evidence-bound canonical AD number before resolution is attempted. A mismatch
stores one outgoing row as `unresolved/successor_not_this_proposal` and creates
no target-local row or event. When the predecessor resolves uniquely, the
service locks both projection roots in lexical order and creates a deterministic
`incoming_supersession_signal` row in each affected predecessor projection.
That row references the outgoing source row, repeats no evidence text, and is
the exact same-projection cause of the stale event. Multiple, contradictory, or
unresolved relations produce only unresolved dependency rows and no side
effect. Retry and concurrent workers converge on the same incoming dependency
and event by full cause hash plus the causal unique constraint.

#### 2.1.1 Shared authoritative-correction foundation

Slice 3A creates a shared proposal-scoped correction foundation used unchanged
by Slice 3B. It is not an applicability-only copy.

`ad_v4_candidate_corrections`

- immutable proposal-scoped correction root with proposal ID (and no
  applicability- or obligation-projection ownership), canonical
  `correction_key`, correction type, original and correcting
  `officialDocuments` reference keys, their verified document-identity hashes,
  the correction object's canonical hash, canonical ordinal, foundation
  version `paprnav-ad-v4-correction-foundation-1`, and generation `1`;
- expected changed-reference count and expected evidence-key count from the
  canonical object; and
- UNIQUE `(proposal_id, correction_key)`, UNIQUE full identity hash, and
  composite parent/document FKs. The root owns the correction evidence links
  once; neither 3A nor 3B copies those links.

`ad_v4_candidate_correction_refs`

- correction root/proposal IDs, canonical ordinal, namespace, exact
  key, owner slice, and canonical reference hash;
- namespace is closed to the complete canonical set:
  `directiveIdentity|productScopes|conditionDefinitions|applicabilityRules|
  requirements|recurrenceGroups|amocAuthorityProvisions|
  supersessionRelations`;
- owner slice is `foundation|slice_3a|slice_3b`, fixed by namespace:
  directive identity and supersession relations are foundation-owned;
  product scopes, conditions, and applicability rules are 3A-owned; and
  requirements, recurrence groups, and AMOC authority provisions are
  3B-owned; and
- UNIQUE `(correction_id, namespace, key)` and UNIQUE `(correction_id,
  canonical_ordinal)` preserve the complete ordered reference set now,
  including future-3B references. No count-only placeholder is allowed.

`ad_v4_candidate_correction_semantic_bindings`

- correction-reference/proposal IDs, binding generation, binding slice,
  owner-projection kind/ID, semantic node type/ID, and binding hash;
- a same-proposal composite FK binds a 3A reference to exactly the semantic
  node in its applicability projection reconstructed from that canonical key;
  Slice 3B later binds to its own same-proposal obligation projection, so the
  shared root is never reassigned between projections; and
- UNIQUE `(correction_ref_id, binding_slice, binding_generation)`.

`ad_v4_candidate_correction_evidence_links`

- correction root/proposal IDs, exact Slice-2 candidate binding ID and evidence
  key, purpose `correction_clause`, canonical ordinal, and link hash;
- composite FK to the same-proposal Slice-2 evidence snapshot; and
- UNIQUE `(correction_id, evidence_key)` plus unique canonical ordinal. These
  are the correction's one authoritative evidence-link set; applicability
  nodes referenced by the correction retain only their own canonical evidence,
  not a second copy of correction evidence.

Foundation completeness requires one root per canonical correction, exact
official-document identity, the complete ordered changed-reference namespace,
and the exact evidence set before the 3A transaction commits. Generation 1 is
3A-complete only when every 3A-owned reference has one binding; foundation and
3B-owned references remain explicit rows with their owner state and never use
SQL NULL as a placeholder. Slice 3B later inserts immutable generation-1
bindings for its owned refs under the same roots. It neither updates nor
duplicates roots, refs, official-document attribution, or evidence links.

For calibration correction `correction-2010`, reconstruction is exact: one
root retains its original/correcting official-document keys, two evidence keys
linked once, and the complete ordered reference set
`productScopes/scope-cessna`, `requirements/req-report`. Slice 3A binds only
`scope-cessna`; `req-report` remains explicitly `slice_3b` owned. After 3B it
receives one requirement binding. Joining root + ordered refs + the one root
evidence set reconstructs the same canonical correction object before and
after 3B; semantic bindings are validation edges and are not serialized into
the canonical correction JSON.

#### 2.2 Semantic nodes and evidence links

`ad_v4_candidate_app_semantic_nodes`

- `id`, full identity hash, projection/proposal IDs, node type, stable node key,
  canonical source pointer, canonical node hash, and created time;
- node types are exactly `product_scope|designation_scope|value_assertion|
  identity_mapping|designation_value|designation_range|designation_group|
  designation_group_member|condition|expression|applicability_rule|
  search_hint|search_hint_group|search_hint_model|change_dependency`;
- UNIQUE `(projection_id, node_type, node_key)`, UNIQUE `identity_hash`, and
  UNIQUE `(id, projection_id, proposal_id)`; and
- a deferred ownership trigger requires exactly one matching typed owner row
  for each node and rejects typed rows with the wrong node type.

`ad_v4_candidate_app_evidence_links`

- `id`, projection/proposal IDs, semantic node ID, Slice-2 candidate binding
  ID, evidence key, purpose code, canonical ordinal, and link hash;
- purpose is a closed code such as `scope_clause`, `identity_support`,
  `designation_scope`, `condition_clause`, `subject_value`, `rule_clause`,
  `search_hint_clause`, `correction_clause`, or `supersession_clause`;
- composite FK `(projection_id, proposal_id, semantic_node_id)` binds the
  owner; composite FK `(proposal_id, candidate_binding_id, evidence_key)` binds
  the exact Slice-2 evidence snapshot; and
- UNIQUE `(semantic_node_id, purpose, evidence_key)`. A deferred check requires
  the exact canonical evidence-key set for each evidence-bearing source
  pointer. There is no text column.

The 3A migration may add the supporting UNIQUE constraint
`(proposal_id,id,evidence_key)` to the immutable Slice-2 binding table; it does
not change or backfill its data.

#### 2.3 Source values and candidate identity normalization

`ad_v4_candidate_app_value_assertions`

- semantic node/projection/proposal IDs, parent semantic node ID, field code,
  state `known|unknown|not_applicable`, value type `text`, optional exact text
  value, controlled reason code, and temporal-scope kind;
- known => text value present and reason/temporal unused;
- unknown/not-applicable => text value unused and reason/temporal present;
- UNIQUE `(parent_semantic_node_id, field_code)`; and
- deferred evidence requires one or more exact binding links for every row.

`ad_v4_candidate_app_identity_mappings`

- semantic node/projection/proposal IDs, exact `source_occurrence_node_id`, one
  `evidence_parent_node_id`, identity kind `manufacturer|model|series`, exact
  source value, normalization origin
  `candidate_payload|source_only|no_normalized_identity`, normalized state,
  normalized value, controlled reason and temporal scope, normalization
  namespace/version, and fixed review state `unreviewed_candidate`;
- `source_occurrence_node_id` is the exact manufacturer assertion,
  designation-value, designation-group-member, or hint-group-member node whose
  source value is mapped. A composite FK requires that node, its evidence
  parent, projection, and proposal to agree. Each exact occurrence receives one
  mapping even when equal source strings occur elsewhere;
- `candidate_payload` is legal only when that exact canonical occurrence has a
  `normalizedIdentity`; it requires known state/value and reconstructs that
  canonical property. The application cannot relabel source spelling as a
  normalized identity;
- `source_only` is used when a condition or search-hint occurrence has source
  identity text but its canonical shape offers no normalized identity;
  `no_normalized_identity` is used for a listed designation, designation-group
  member, or series occurrence whose closed canonical object has no normalized
  property;
- both non-payload origins require state `unknown`, controlled reason
  `not_extracted|not_yet_reviewed`, temporal scope
  `source_observation|directive_version`, and inherited evidence through the
  single `evidence_parent_node_id`; they cannot carry a normalized value,
  namespace, version, or token; and
- UNIQUE `(projection_id, identity_kind, source_occurrence_node_id)`. No global
  aircraft/manufacturer/model table references these rows and no per-occurrence
  evidence-link copy is created.

The 2002 condition member `6314` maps as `model/source_only/unknown`, inheriting
the `condition-magneto-models` group evidence once. A Cessna hint model member
maps as `model/source_only/unknown`, inheriting that manufacturer-model group's
evidence once. A product-scope manufacturer with an actual canonical
`normalizedIdentity` maps as `manufacturer/candidate_payload/known`. These
origins cannot be interchanged.

#### 2.4 Product and designation scopes

`ad_v4_candidate_app_product_scopes`

- product-scope semantic node/projection/proposal IDs, `scope_key`, product role
  `airframe|engine|propeller|appliance|installed_part|modification`;
- manufacturer presence `property_absent|present`, exact source manufacturer
  value when present, and candidate manufacturer identity-mapping node ID when
  present;
- independent model/serial/part property-presence codes; and
- UNIQUE `(projection_id, scope_key)`. CHECKs require value/mapping only for a
  present manufacturer and distinguish omission from explicit unknown.

`ad_v4_candidate_app_designation_scopes`

- designation-scope semantic node/projection/proposal IDs, parent product scope
  node ID, field kind `model|serial|part_number`, and scope kind
  `all|listed|series_expression|ranges|unknown|not_applicable`;
- exact series expression only for `series_expression`;
- controlled reason and temporal-scope kind only for unknown/not-applicable;
- fixed comparison/evaluation state. Series expressions are
  `unknown/unsupported_expression`, not executable patterns;
- UNIQUE `(product_scope_node_id, field_kind)`; and
- deferred cardinality checks: listed has one or more values and no ranges;
  ranges has one or more ranges and no values; other kinds have neither.

`ad_v4_candidate_app_designation_values`

- semantic node/projection/proposal and designation-scope IDs, exact source
  value, canonical ordinal, and model/series identity-mapping node for that
  exact designation-value semantic node;
- the mapping's `source_occurrence_node_id` must equal this row's semantic-node
  ID, while its `evidence_parent_node_id` equals the one designation-scope node.
  Thus 51 values create 51 mappings but still one parent evidence link;
- UNIQUE `(designation_scope_id, source_value)` and UNIQUE
  `(designation_scope_id, canonical_ordinal)`; and
- ordinals must equal the Slice-2 canonical exact-string set order.

Static cardinality proof over the five calibration packets is mandatory:

| packet | listed value occurrences | identity mappings | parent-scope inheritance edges |
| --- | ---: | ---: | ---: |
| 1998-17-11 | 51 + 30 = 81 | 81 | 2 |
| 2002-13-04 | 6 | 6 | 1 |
| 2008-26-10 | 182 | 182 | 1 |
| 2011-10-09 | 224 | 224 | 1 |
| 2024-14-03 | 7 + 2 + 10 + 33 + 130 = 182 | 182 | 5 |

The multi-model uniqueness gate is therefore feasible for 5 of 5 packets and
cannot collapse two exact value occurrences into one mapping.

`ad_v4_candidate_app_designation_ranges`

- semantic node/projection/proposal and designation-scope IDs, exact lower and
  upper strings, lower/upper inclusive booleans, polarity
  `included|excluded`, canonical ordinal, and fixed lexical comparator version;
- composite uniqueness across the five canonical range identity fields and
  unique ordinal; and
- no numeric coercion or range membership result is stored.

#### 2.5 Conditions and three-valued expressions

`ad_v4_candidate_app_conditions`

- condition semantic node/projection/proposal IDs, `condition_key`, exact
  condition type and operator closed to the V4 enums, temporal-basis kind,
  comparator property presence/value, subject product-role
  presence/value, and subject attribute-key presence/value;
- fixed `evaluation_state = 'unevaluated'` and
  `evaluator_contract = 'none'`;
- UNIQUE `(projection_id, condition_key)`; and
- closed enum and shape checks require the exact subject properties,
  designation groups, group members, and value-assertion children found in the
  canonical candidate. There is deliberately no type/operator compatibility
  matrix in 3A.

Every pair from the independent Slice-2 `conditionType` and `operator` enums
is representable and reconstructable as `unevaluated` when the enclosing
closed schema shape is valid. This representation does not declare that every
pair is meaningful or executable. A future evaluator may narrow semantics only
through a separately reviewed, versioned canonical-boundary and evaluator
contract; it may not reinterpret existing 3A rows.

Subject fields `manufacturer`, atomic `modelOrSeries`, `partNumber`,
`serialNumber`, `stcNumber`, and `attributeValue` are
`ad_v4_candidate_app_value_assertions` children using those exact field codes.
The validator-2 `designationGroup` is stored as one source-faithful group row,
one exact display assertion, and typed member rows with explicit association;
it is never derived from the display string. Manufacturer/model/series
occurrences receive separate unreviewed identity mappings; the assertion and
display values remain source-faithful.

`ad_v4_candidate_app_designation_groups`

- semantic node/projection/proposal and owning-condition IDs, group key,
  association `all_members|any_member|source_group|unknown`, exact source
  display assertion ID, controlled unknown reason and temporal scope, and
  canonical ordinal;
- non-unknown association forbids unknown reason/temporal; unknown association
  requires both plus exact evidence; and
- UNIQUE `(condition_node_id, group_key)` and unique ordinal.

`ad_v4_candidate_app_designation_group_members`

- semantic node/projection/proposal and group IDs, member key, designation kind
  `model|series_expression`, exact source designation/expression, explicit
  manufacturer union state and value/reason/temporal fields, fixed evaluation
  state/reason for series expressions, canonical ordinal, and exact-occurrence
  identity-mapping node;
- group association and typed members come only from canonical validator-2
  bytes, never from source display punctuation; and
- UNIQUE `(group_id, member_key)`, UNIQUE `(group_id, canonical_ordinal)`, and
  composite same-projection FKs for group, manufacturer assertion, and mapping.

`ad_v4_candidate_app_expressions`

- expression semantic node/projection/proposal IDs, owning rule ID, expression
  context `scope|condition`, deterministic expression path, node type, fixed
  result domain/evaluator version, and nullable typed ref columns for scope,
  condition, or rule;
- leaf CHECKs require exactly the correct ref; `not|all|any` have no ref;
- UNIQUE `(owning_rule_id, expression_context, expression_path)`; and
- composite FKs bind every leaf ref to the same projection/proposal.

`ad_v4_candidate_app_expression_edges`

- projection/proposal IDs, parent expression ID, child expression ID, and
  sequence;
- UNIQUE `(parent_expression_id, sequence)`, UNIQUE
  `(parent_expression_id, child_expression_id)`; and
- deferred checks enforce no cross-context edge, no cycle, `not` arity 1,
  `all|any` arity >=2, leaf arity 0, one root per rule/context, and contiguous
  sequence from zero. Sequence is regulatory/canonical and is not sorted.

`ad_v4_candidate_app_rules`

- rule semantic node/projection/proposal IDs, `rule_key`, scope-root expression
  ID, condition property presence and optional condition-root expression ID,
  and fixed evaluator version;
- UNIQUE `(projection_id, rule_key)`; and
- composite FKs bind both roots to the same rule/projection and correct
  expression context.

`ad_v4_candidate_app_rule_exclusions`

- projection/proposal IDs, rule ID, excluded rule ID, and canonical ordinal;
- UNIQUE `(rule_id, excluded_rule_id)` and unique ordinal; and
- same-projection FKs plus deferred acyclicity. Empty exclusions are represented
  by zero rows, not a nullable array.

#### 2.6 Non-controlling search hints

`ad_v4_candidate_app_search_hints`

- search-hint semantic node/projection/proposal IDs, `hint_key`, product role,
  exact source display text, fixed `controlling = false`, fixed
  `exhaustive = false`;
- UNIQUE `(projection_id, hint_key)`; and
- no expression table has a hint-reference column or FK.

`ad_v4_candidate_app_search_hint_groups` and
`ad_v4_candidate_app_search_hint_members`

- group rows preserve canonical group key/ordinal, manufacturer explicit
  union, association `paired|source_group|unknown`, controlled unknown reason,
  temporal scope, and evidence parent;
- member rows preserve group ID, `member_key`, typed `designation_kind`
  `model|series_expression`, canonical ordinal, exact-occurrence unreviewed
  identity mapping, and the single inherited group evidence-parent edge;
- a `model` member requires exact `source_designation` and forbids expression,
  evaluation, and reason columns. A `series_expression` member instead requires
  exact `expression_text`, `evaluation_state = 'unevaluated'`, controlled
  `reason = 'unsupported_expression'`, normalization origin `source_only`,
  normalized state `unknown`, and forbids an exact model designation;
- UNIQUE `(hint_id, group_key)`, UNIQUE `(group_id, member_key)`, and UNIQUE
  `(group_id, canonical_ordinal)`; exact source values are not overloaded as
  relational discriminators; and
- rows may support administrator research only. They are excluded from rule
  reconstruction except as the hint's exact canonical group/member arrays.

The reconstruction discriminator emits every canonical-v2 member variant from
these typed columns. It never decides the variant from punctuation or parses
`expression_text`; evidence is inherited from the group once and not copied per
member.

The 2002 hint reconstructs seven manufacturer groups, 19 exact model members,
and one source-faithful `series_expression` member for `172A through 172H`;
no row contains manufacturer `multiple`, no `172A` through `172H` exact rows
are inferred, and no comma/range/prefix parsing is used.
The 2024 condition reconstructs one Garmin `all_members` group with exact GFC
500 and GSA 28 members; STC and master-drawing assertions remain separate. If
a hint's source does not establish manufacturer/model pairing, the group uses
`association=unknown`, reason `source_ambiguous`, temporal scope, and evidence;
the materializer never assigns a manufacturer heuristically.

### 3. Database completeness and reconstruction contract

At deferred commit, `paprnav_v4_candidate_app_require_complete(projection_id)`
must:

1. lock and verify the parent candidate proposal and exact repeated hashes;
2. verify its Slice-2 canonical bytes/JSON mirror and evidence-binding rows;
3. require exactly one materialized root event and the recorded row counts;
4. require exactly one typed owner for every semantic node and no unowned typed
   row;
5. verify every composite same-projection reference, expression arity/cycle,
   condition child/group set, designation child set, identity occurrence
   mapping, and exact evidence-key set;
6. verify one correction foundation per canonical correction, its exact
   official-document identities, complete ordered reference namespace, one
   evidence set, and all 3A-owned semantic bindings for generation 1;
7. reconstruct the four-field JSONB subtree in canonical array order;
8. require JSONB equality with those four fields extracted from the parent
   proposal mirror;
9. require the application-supplied restricted-JCS subtree bytes/hash and
   projection hash to match server-generated values; and
10. fail the transaction on any mismatch.

PostgreSQL need not implement restricted JCS. It verifies SHA-256 over the
already canonical subtree bytes, relational-to-parent JSONB equality, every
envelope field, and the aggregate row identity/hash set. The application
reconstructs, canonicalizes, and verifies bytes/hash before insert and every
audit read. This follows the reviewed Slice-2 division of responsibility while
preventing self-consistently rehashed forged relational rows.

Property-presence columns are normative. Reconstruction never guesses whether
an absent optional property was unknown. Set arrays sort using the checked-in
Slice-2 schema annotations; expression operands retain stored sequence.

### 4. Index contract without read cutover

The migration creates only integrity, reconstruction, source-audit, and
stale-fold indexes used by the bounded 3A service, in addition to primary,
foreign-key-supporting, and uniqueness indexes:

- projection `(proposal_id, materializer_version)` and request idempotency;
- semantic-node `(projection_id, node_type, node_key)` and typed-owner
  composite-FK support;
- evidence-link `(proposal_id, candidate_binding_id, evidence_key)` and
  `(semantic_node_id, purpose, canonical_ordinal)`;
- designation/group/member parent + canonical-ordinal indexes used for exact
  reconstruction, never source-string lookup;
- expression-edge parent/sequence and child indexes, and exact scope,
  condition, and rule reference-FK indexes;
- correction-root `(proposal_id, correction_key)`, correction-ref
  `(correction_id, canonical_ordinal)`, and binding completeness indexes;
- dependency causal/source IDs and exact predecessor-AD resolution support;
  and
- event `(projection_id, sequence_number)` and partial cause indexes required
  by the stale fold.

There is no index on source manufacturer/model spelling, normalized values or
tokens, product-role lookup, search hints, aircraft IDs, or candidate make/model
combinations. Slice 3A makes no hot-path or matching-readiness claim. The later
reviewed identity bridge must define its own aircraft/canonical-identity join
and indexes in the matching slice; it cannot reuse an unreviewed candidate
mapping as authority. Repository tests assert both the absence of these
premature index definitions and the absence of released readers using 3A.

### 5. Materializer, authorization, and concurrency contract

#### 5.1 Default-off capability gates

Two independent application settings are introduced with literal defaults of
`false`:

- `PAPRNAV_AD_V4_VALIDATOR2_WRITES_ENABLED=false`; and
- `PAPRNAV_AD_V4_SLICE3A_ROUTES_ENABLED=false`.

The first gates every validator-2 candidate POST before parsing or persistence.
The second gates registration/exposure of the 3A materialization POST and both
3A audit GET routes. Migration 0027 also creates two database gate keys,
`validator2_write_enabled` and `materializer3a_enabled`, both default false.
The application role may read but not enable them; only the deployment database
role may change them through the audited gate procedure. Enabling one gate or
flag never implies the other. Merely running 0027 cannot expose a v2 writer or
a 3A route.

The application has fixed compiled capabilities
`SUPPORTED_V4_VALIDATOR_PAIRS` and `SUPPORTED_V4_MATERIALIZERS`. Migration 0027
provides a read-only database capability function returning the exact revision,
supported validator/canonicalization pairs, materializer version, and the two
gate states. Startup and every write transaction require all three layers:

1. every required application flag and database gate is true;
2. the compiled application capability contains the requested fixed version;
   and
3. the database capability function exists and returns the exact compatible
   0027 capability.

Missing/mismatched database capability, unknown compiled version, or a required
false application/database gate fails closed before writes with stable
`capability_disabled`, `validator2_write_gate_disabled`, or
`materializer3a_gate_disabled`, or
`schema_capability_mismatch`; it never falls back to v1. The transaction repeats
the database capability check after acquiring the proposal/version lock so a
startup check is not trusted as a write-time guarantee. Audit routes require
the 3A application flag, database `materializer3a_enabled`, and compatible
reader capability, but do not require `validator2_write_enabled`: they may read
and verify already-existing projection rows only. They never materialize a
missing projection. Authorization remains the separate exact-membership check
below.

The validator-2 candidate POST requires its application flag plus database
`validator2_write_enabled`. The 3A materialization POST/service transaction
requires **both** application flags, **both** database gates
`validator2_write_enabled` and `materializer3a_enabled`, and both compiled
capabilities. This dependency remains true for a preexisting v2 candidate. If
validator-2 writes are disabled while 3A audit is enabled, materialization
returns stable `validator2_write_gate_disabled` and writes zero request,
projection, dependency, correction, or event rows; audit GET may inspect only a
projection that already exists.

The materializer may perform an unlocked early rejection, but after locking its
parent proposal and before any 3A row it reads both database gate rows `FOR
SHARE`. The audited deployment procedure disables a gate under `FOR UPDATE`.
Therefore a concurrent disable either commits first and the materialization
rejects with zero rows, or waits for an already-authorized materialization to
commit and then prevents every later write. No transaction observes a
half-disabled gate pair.

The validator-2 candidate writer follows the same global proposal-before-gate
order: before reading `validator2_write_enabled` under `FOR SHARE`, it
explicitly acquires `ROW EXCLUSIVE` on the Slice-2 proposal table (the mode its
later INSERT requires). Thus downgrade's proposal-table lock cannot invert with
a candidate writer holding a feature-gate row.

These gates prove only this process's configuration/code and the connected
database schema. They do not prove that every application instance in a fleet
has completed rollout. Therefore the compatibility release—dual v1/v2 readers
with both flags still false—must be fully deployed and externally verified
before deployment configuration may enable the validator-2 gate. The 3A flag
is enabled only in a later configuration rollout after v2 write verification.

One 3A HTTP writer is in scope when its route gate is enabled:

`POST /api/v1/ads/directives/{directive_id}/v4/candidate-proposals/{proposal_id}/applicability-projection`

It requires `Idempotency-Key` and `Paprnav-Acting-Membership-Id`, has no JSON
body, and derives the fixed materializer version server-side. Only an active
platform admin may call it. It returns 201 for a new complete projection and
request, 200 for exact retry or reuse, 409 for an idempotency mismatch or
integrity/stale-parent conflict, 422 for a proposal that cannot be projected,
and 403 for authorization denial.

Platform-admin-only audit endpoints are:

- `GET .../{proposal_id}/applicability-projection`; and
- `GET .../{proposal_id}/applicability-projection/reconstruction`.

Both GETs require the same `Paprnav-Acting-Membership-Id` header as POST. For
all three endpoints the server begins one transaction, loads the authenticated
user and the exact selected membership under row lock, and verifies membership
user ID, active status, and `platform_admin` role before loading any candidate
metadata. A selected inactive/shop/foreign membership is denied even if the
same user has another active platform-admin membership. A concurrent revocation
either commits before the lock and denies the call or waits until the
authorized transaction ends; authorization cannot be assembled from multiple
memberships. GET is side-effect-free and does not create an audit row, but the
response includes the selected membership ID and evaluated policy version as
ephemeral authorization context.

The first returns verified metadata/counts/event-fold state. The second returns
only the verified four-field reconstructed candidate subtree and hashes. It is
explicitly labeled candidate-only and does not return source text. There is no
list/search/match endpoint.

The service uses this total lock order:

1. active user and exact active membership rows;
2. advisory idempotency lock over actor, membership, action, policy version,
   and key;
3. parent candidate proposal row;
4. database feature-gate rows in lexical gate-key order, `FOR SHARE`;
5. all bound Slice-1 fragments in lexical fragment-ID order, followed by full
   lifecycle revalidation;
6. advisory projection lock over proposal ID and materializer version;
7. correction foundations/refs and outgoing dependencies in canonical order;
8. any predecessor/target projection roots that may receive target-local
   dependency rows or stale events, locked in lexical projection-ID order; and
9. semantic insertion followed by deferred completeness checks and commit.

The request hash covers the directive ID, proposal ID, fixed action, exact
validator/canonicalization pair, and fixed materializer version. Same
key/different request returns 409 with no rows.
Same key/same request returns the same request/root. Two keys for one proposal
append two request audit rows but reuse one projection. Deterministic node IDs,
unique constraints, advisory locking, and post-conflict equality verification
make concurrent creation converge without 500.

The materializer parses only verified canonical proposal bytes through the
Slice-2 validator. It has no dict-only bypass, fixture loader, provider writer,
CLI writer, seed path, or direct-SQL helper. Tests may use direct SQL only to
prove database rejection.

### 6. Correction, supersession, and stale fold

The projection root and semantic rows never change. Candidate staleness is a
derived fold over immutable facts:

1. start at the sequence-0 `materialized` event;
2. verify the hash chain and fold later stale events;
3. revalidate parent proposal bytes/hash/gate and every bound fragment's live
   lifecycle;
4. inspect Slice-2 `corrects_candidate|replaces_candidate` relationships whose
   predecessor is this proposal;
5. inspect evidence-bound 3A correction and supersession dependency signals;
   and
6. return `candidate_verified`, `candidate_stale`, or
   `dependency_unresolved` plus all reason codes.

`candidate_verified` means only that the derived projection still agrees with
its unreviewed parent candidate; it does not mean approved or applicable.

When materializing a successor, explicit same-directive candidate
relationships append deterministic `candidate_corrected` or
`candidate_replaced` events to already materialized predecessors. The internal
repair helper is not a background process. It runs only inline and
opportunistically inside an already authorized 3A materialization service
transaction, using the same locks, capability gates, cause identity, and event
idempotency. An authorized audit transaction may invoke the same helper only in
detection mode: GET reports a missing convenience event but remains
side-effect-free. There is no cron, queue consumer, worker, scheduler, CLI,
repair endpoint, startup sweep, or new operational writer. On every read, the
live fold still detects the relationship even if the convenience event has not
yet been appended.

For a canonical supersession relation, target resolution is exact AD number.
Before lookup, the relation's successor must byte-equal this proposal's known,
evidence-bound canonical AD number. Missing/unknown AD identity or a different
successor records `unresolved` with a stable reason and produces no target
lookup, incoming dependency, or event. Exactly one matching predecessor
directive permits a candidate-only signal: a deterministic target-local
incoming dependency is created and the target projection event names it via
same-projection composite FK. Zero or multiple matches records explicit
unresolved or ambiguous state and affects no other row. Contradictory candidate
signals fail closed and never choose a legal winner. Canonical cause hashing,
causal uniqueness, sorted locks, and equality-on-conflict make retries and
concurrent signal workers converge. No V3/released status or current pointer
is read or modified.

An authoritative correction contained in the same candidate is represented by
the shared correction foundation and its complete ordered refs, with 3A-owned
refs bound to changed applicability nodes. It describes why the candidate has
its present content; it does not stale that same projection. Only a later
candidate relationship or evidence change stales it.

## Alternatives considered

### Materialize the entire V4 proposal in one migration

Rejected. Requirements, timing, branches, documents, and AMOC semantics have
different correctness and human-signoff risks. Splitting 3A makes
applicability round-trip and bloat behavior independently reviewable.

### Populate existing V3 applicability tables

Rejected. Those tables feed current readers and contain flattened/copy-heavy
representations. Reuse would create an accidental read cutover, mix V3 and V4,
and erase the candidate-only boundary.

### Add JSONB indexes to the Slice-2 proposal

Rejected. JSONB path indexes do not enforce typed references, same-candidate
graphs, evidence links, explicit uncertainty, or relational reconstruction.
They also leave the 182-model/shared-condition bloat question unanswered.

### Store canonical source text on each semantic row

Rejected. Slice 1 stores exact source clauses once and Slice 2 binds them once
per proposal. Repetition would reintroduce the defect this design is intended
to remove and allow copied text to drift from retained bytes.

### Create a global authoritative manufacturer/model registry now

Rejected. Current V4 has no per-model reviewed normalized identity, no human
signoff occurs in 3A, and aircraft canonical identity migration is excluded.
Candidate identity assertions remain separate and untrusted.

### Automatically normalize model spelling, prefixes, or series

Rejected. Case/punctuation/prefix heuristics can broaden applicability across
manufacturers or models. Current model normalization is explicit unknown, and
series expressions are preserved but not executed.

### Materialize automatically inside the Slice-2 candidate POST

Rejected. It would change the closed Slice-2 transaction and make candidate
storage depend on the larger normalized schema. An explicit idempotent 3A
service permits existing candidates, independent rollback, and bounded review.

### Mutable projection status or in-place correction

Rejected. Mutable flags lose the causal record and race with readers. Immutable
events plus live validation make stale state reproducible.

### Treat candidate supersession as authoritative

Rejected. An unreviewed candidate can only generate an evidence-bound stale
signal among candidate projections. Publication and legal current-state
selection require later human review.

## Trust, authorization, and audit boundaries

- Official PDFs and Slice-1 fragments remain source evidence. The Slice-2 V4
  candidate remains an unsigned machine/admin proposal. Slice-3A normalized
  rows are a derived candidate projection of that proposal.
- Round-trip equality proves lossless representation, not regulatory truth,
  identity correctness, series membership, or aircraft applicability.
- The server derives all IDs, hashes, gate, versions, actor context, identity
  mapping origin, and stale events. The caller supplies no normalized rows,
  hash, status, or event payload.
- The materializer actor may later be disqualified from sole human approval;
  no approval exists here.
- Platform-admin membership is rechecked under lock at each POST. Audit GETs
  apply the same role boundary. Unauthorized callers receive no candidate JSON
  or evidence metadata.
- Automated stale marking is deterministic recalculation from immutable facts
  and requires no human review. It cannot alter a signed decision or convert
  uncertainty into an affirmative result.
- Database immutability protects against application and direct-SQL mutation;
  database-owner bypass remains operational authority and is not presented as
  an application security boundary.

## Read paths and consumers

In-scope reads are limited to:

- the materializer's verification of Slice-2 proposal/evidence rows;
- its post-insert relational reconstruction and stale fold;
- platform-admin projection metadata and reconstruction audit endpoints; and
- migration/test inspection.

The implementation review must search all callers/readers and prove these
remain unchanged and do not query 3A tables: V3 extraction/review,
`applicability_targets`, `ad_target_applicability`, released AD catalog,
aircraft AD pages, matching, coverage, compliance requirements, due state,
observability counts, exports, jobs, frontend APIs, and UI.

No query in this slice answers “does this AD apply to this aircraft?” The
candidate-shaped indexes are unused until a later publication/matching slice
introduces reviewed global identities and a separately reviewed read contract.

## Write paths and administrative paths

The only supported writer is the projection service called by the platform-
admin POST. Its internal deterministic stale-event helper is part of the same
service/repository boundary and can append only within that authorized POST
transaction. GET calls its detection-only path and is strictly
side-effect-free: it folds stored events and live immutable dependencies but
neither enqueues nor writes repair. The response never depends on a convenience
stale event existing.

No provider job, CLI, seed, V3 translator, calibration loader, frontend form,
or generic ORM CRUD writer is added. Tests construct positive rows through the
service. Direct SQL appears only in negative PostgreSQL tests.

## Migration, compatibility, correction, and rollback

Implementation requires migration `0027` after `20260901_0026`. It introduces
the validator-2/c14n-2 compatibility boundary and Slice-3A together. It creates
the 3A tables, constraints, triggers, functions, and indexes above, plus the
version constraints required to keep existing Slice-2 candidate/audit rows
verifiable.

The proposal table already records `validator_version` and
`canonicalization_version`; 0027 verifies every existing row is the exact v1
pair and rejects an unrecognized value. It adds both non-null columns to
`ad_v4_candidate_evidence_bindings`, `ad_v4_candidate_submissions`,
`ad_v4_candidate_submission_relationships`, and
`ad_v4_candidate_proposal_events`. Existing child rows are backfilled in one
locked transaction from their parent proposal/submission as
`paprnav-ad-v4-validator-1` / `paprnav-ad-v4-c14n-1`, verified against their
unchanged v1 canonical bytes/hashes, then constrained `NOT NULL`. This is a
version-metadata backfill only; no canonical bytes, hash, proposal identity,
evidence binding, provenance, or event is rewritten.

Composite FKs/triggers require:

- binding and submission version pair = parent proposal pair;
- relationship pair = owning submission pair, while its predecessor proposal
  may independently be v1 or v2 and remains named by immutable ID;
- event pair = both its proposal and creator submission pair; and
- every 3A root/request/node/event repeats the v2 proposal pair exactly.

Database hash validators dispatch only the closed pairs
`validator-1/c14n-1` and `validator-2/c14n-2`; mixed pairs or unknown versions
fail. V1 rows use the exact existing v1 domains/envelopes. V2 rows use the
domains/envelopes in section 0. Proposal content uniqueness becomes
`(directive_id, validator_version, canonicalization_version, canonical_hash)`.
Idempotency and same-content reuse occur only within an identical version pair
and its hash semantics. A logically similar v1 and v2 payload therefore creates
two distinct immutable proposal identities, never a cross-version reuse.

Existing candidate proposals remain valid and unmaterialized until explicitly
requested. The 3A materializer accepts only the v2 pair; dual-version audit
readers verify both. V3 bytes, hashes, reviews, materializations, and readers
remain unchanged.

Correction/replacement creates a new Slice-2 candidate and a new 3A projection.
The old projection is retained and append-staled. Canonical authoritative
corrections and supersession relations become evidence-bound dependency rows;
they do not rewrite prior projections or released state.

Deployment order is mandatory:

1. apply 0027, whose database validators accept/read both closed pairs and
   remain compatible with the existing v1 writer;
2. deploy the compatibility application that reads/verifies v1 and v2 but
   continues writing only v1, with both new settings explicitly false;
3. externally verify that compatibility release across the serving fleet;
   this operational evidence is a prerequisite but is not inferred from the
   flags themselves;
4. after capability checks pass, the deployment role enables database
   `validator2_write_enabled`, then configuration
   `PAPRNAV_AD_V4_VALIDATOR2_WRITES_ENABLED`; and
5. only after v2 writes are proven, enable database
   `materializer3a_enabled`, then configuration
   `PAPRNAV_AD_V4_SLICE3A_ROUTES_ENABLED` in a separate rollout.

Application rollback reverses feature exposure, not data meaning: set the 3A
application flag false and drain those requests, disable database
`materializer3a_enabled`, then set the v2-write application flag false and
drain writes before disabling database `validator2_write_enabled`, while
retaining the dual-version reader/verifier.
All immutable v2 rows remain candidate-only and audit-readable. Deploying any
pre-v2 application or database code while a v2 proposal or dependent audit row
exists is explicitly prohibited. Nothing falls back to V3, and no released
behavior can resurrect because 3A never feeds a released reader.

Physical downgrade uses a fixed dependency-safe lock order and executes in one
transaction:

1. acquire `ACCESS EXCLUSIVE` on the Slice-2 proposal table first, before
   inspecting a proposal or touching any 3A table. This is the global boundary:
   candidate creation and every 3A materializer also acquire/lock the Slice-2
   parent proposal before any 3A root or child;
2. while retaining that lock, lock the database feature-gate table, then
   Slice-2 binding, submission, relationship, and event tables in that fixed
   order, then every 3A root and child table in the same parent-before-child
   order used by the materializer. DDL drops objects only later and in reverse
   dependency order;
3. refuse before DDL if any 3A row exists;
4. independently refuse if any proposal uses validator-2/c14n-2 or if any
   binding, submission, relationship, or event carries the v2 pair, even when
   every 3A table is empty;
5. verify all remaining Slice-2 rows are internally consistent v1 rows;
6. only for a v1-only database, drop 3A objects, restore the exact 0026 v1
   functions/constraints, and remove the child version columns; and
7. return to 0026, prove all v1 rows remain readable, then prove re-upgrade
   backfills the same metadata and preserves every byte/hash.

A concurrent v2 candidate creation that reaches the proposal first commits and
causes downgrade refusal; if downgrade owns the proposal-table lock first, the
writer waits and then either observes 0026/v1-only mode and refuses v2 or
continues after a failed downgrade. A materializer that locks its parent first
either commits before downgrade's proposal lock and makes the 3A emptiness gate
refuse, or waits without holding a 3A lock. Downgrade never waits on a 3A lock
while a materializer waits on the proposal lock, so the old lock inversion and
deadlock are impossible. No interleaving silently loses a candidate or
projection. An empty-3A database with one unmaterialized v2 proposal still
refuses downgrade. No downgrade truncates, deletes, or rewrites candidate data.
Because v2 rows are immutable, a used-v2 installation is rolled back
operationally with dual readers or recovered into a separately verified pre-v2
snapshot/new database; it is never forced to 0026.

## Test strategy

Every verification report uses `x passed out of x` and names skipped or
unexecuted gates separately.

### Five-packet positive and reconstruction gates

For each of the five source-accounted calibration packets after the reviewed
validator-2 candidate corrections in section 0 (not by mutating any stored
validator-1 proposal):

1. enter through the real Slice-1 retained-evidence admission and Slice-2
   candidate persistence boundary;
2. call the 3A materializer, never direct fixture SQL;
3. reconstruct solely from 3A rows;
4. require JSON equality and canonical byte/hash equality with `A(P)`; and
5. prove exact retry and a second-origin request reuse the same projection.

Expected: **5 passed out of 5 materializations**, **5 passed out of 5
relational reconstructions**, **5 passed out of 5 subtree hashes**, and **5
passed out of 5 evidence-set reconciliations**.

Predecessor compatibility is a separate gate: the original validator-1 1998
candidate remains hash-verifiable and audit-readable **1 passed out of 1**, is
refused for 3A materialization with `predecessor_semantic_defect` **1 passed
out of 1**, and remains byte/row/event unchanged after the corrected
validator-2 candidate is stored **1 unchanged out of 1**.

A generated representation gate covers the current 9 condition-type values ×
10 operator values: **90 represented and reconstructed out of 90** with fixed
`unevaluated/none`, without claiming executable compatibility. Separate schema
negatives reject unknown enum values, missing discriminator-required fields,
extra properties, or a stored evaluation result.

Packet-specific assertions:

- 2024-14-03: exactly 5 product scopes, 182 model rows, 1 condition, 1 rule,
  and one shared condition/evidence identity; no source-text column, 0 model-
  level evidence links, 182 exact-occurrence unknown identity mappings
  using 5 parent-scope inheritance edges, and no per-model
  condition/rule/evidence
  copy. The GFC 500/GSA 28 group is `all_members`, not parsed display text.
- 2011-10-09: exactly 1 scope, 224 model rows, 0 conditions, 1 rule, an
  evidence-bound supersession dependency signal whose successor equals the
  proposal AD number, and no requirement/timing row.
- 2002-13-04: exact conflicting-evidence serial `unknown`, 4 conditions, 1
  rule, articulated 3-member/5-member/atomic designation groups, and 1
  non-controlling/non-exhaustive search hint with seven manufacturer groups
  and exactly 20 typed members: 19 exact model members plus one exact
  `series_expression` value `172A through 172H`; hint IDs are absent from all
  expressions. There are zero inferred exact `172A` through `172H` model rows,
  specifically no exact `172B` or `172H` row.
- 1998-17-11: 2 scopes, 81 models, 2 conditions, 1 rule; component-owned work
  facts remain candidate condition values and do not become aircraft records.
  The unknown provenance operand uses explicit unknown state; the legacy known
  sentinel is rejected for new materialization.
- 2008-26-10: 1 scope, 182 models, 4 conditions, 1 rule, and exact
  shared `correction-2010` foundation with two ordered refs, two evidence links
  once, one 3A scope binding, and one explicit future-3B requirement ref; no
  service-bulletin/document/AMOC semantic row is created in 3A.

### Structural and semantic negatives

Reject through the production materializer and, where stated, direct
PostgreSQL:

- wrong proposal/directive, non-candidate gate, changed canonical/hash/binding
  envelope, invalid or transitioned evidence, and parent changed between
  validation and insert;
- any partial projection, count/hash mismatch, orphan typed node, duplicated
  stable key, wrong node type owner, or reconstructed JSON differing by one
  property/value/order/presence bit;
- cross-projection/cross-proposal scope, condition, expression, exclusion,
  identity, dependency, or evidence link;
- evidence key from another proposal, fragment ID/hash substituted under a
  valid key, missing node evidence, or copied source text submitted to a table
  that has no such column;
- known assertion without value, unknown/not-applicable without reason,
  temporal scope, or evidence, and SQL NULL used as an unknown state;
- listed scope with zero values, ranges with zero ranges, child rows on `all`,
  series expression made executable, duplicate source values/ranges, or
  noncanonical ordinals;
- a condition pair accepted by Slice 2 that cannot be represented exactly,
  any non-`unevaluated` state, omitted/present subject mismatch, unexpected
  subject/group member, display-text parsing, or opaque predicate JSON;
- leaf expression with wrong/multiple refs, `not` with other than one child,
  `all|any` with fewer than two children, noncontiguous sequence, cycle,
  cross-context edge, rule/exclusion cycle, or requirement-state ref;
- search hint marked controlling/exhaustive or referenced by an expression;
- expansion of `172A through 172H` into any exact 172A-H member, construction
  of exact 172B/172H rows, prefix/range execution of that expression, or a
  series-expression row without `unknown/unsupported_expression`;
- model normalization claimed known without an actual canonical
  `normalizedIdentity`, `candidate_payload` origin without that exact property,
  source-only origin without unknown reason/temporal/evidence inheritance,
  one mapping reused by two value occurrences, and normalization that
  case/punctuation-folds a source value; and
- incomplete, reordered, duplicated, or cross-proposal correction refs;
  duplicated correction evidence; missing 3A correction binding; or a 3B
  binding that attempts to create a second correction root;
- self-consistently rehashed direct-SQL forgeries of root, node, link, request,
  event, dependency, or reconstruction bytes.

### Idempotency, concurrency, stale state, and authorization

- default configuration exposes 0 v2 write paths and 0 3A routes; applying
  0027 alone leaves both disabled; expected **2 passed out of 2**;
- the exact four application/database gate combinations are exercised with a
  preexisting v2 candidate: off/off exposes no writer or audit; on/off permits
  v2 candidate writes but no 3A POST/GET; off/on permits audit GET of an
  existing projection only, while materialization rejects
  `validator2_write_gate_disabled` and leaves 0 request, projection,
  dependency, correction, or event rows;
  on/on permits the reviewed v2-write/materialize/audit sequence; expected
  **4 passed out of 4**;
- application/DB disagreement for either named gate always resolves to off;
  neither config nor a database gate alone enables its surface;
- either enabled flag with missing/old database capability or absent compiled
  application capability fails startup and the transactional write guard;
  migration mismatch during a running process fails the repeated in-transaction
  check with no rows; expected **5 passed out of 5**;
- compatibility-release startup holds both flags false, and rollback tests
  disable/drain 3A then v2 writes while dual-version reads remain available;
  tests assert no flag or migration claims fleet-wide rollout completion;
- deterministic concurrent gate-disable/materialization barriers prove either
  materialization commits fully before disable or disable wins and the POST
  writes 0 request/projection/dependency/correction/event rows: expected
  **2 passed out of 2**;
- new/exact retry/new key same proposal: expected **3 passed out of 3**;
- POST and each GET with selected platform admin versus maintenance shop,
  owner, organization admin, inactive/foreign selected membership, another
  valid membership present, and revocation under lock;
- concurrent same key, different keys/same proposal, same key/different
  proposal, and rollback after child failure: expected **4 passed out of 4**;
- two concurrent materializations with reversed evidence order and overlapping
  correction/supersession targets complete without deadlock or 500: expected
  **2 passed out of 2**;
- correction/replacement relation, evidence lifecycle transition, uniquely
  resolved supersession signal, unrelated successor, unknown proposal AD
  identity, ambiguous AD-number target, contradictory candidate signals,
  exact retry, and concurrent insertion fold fail-closed without UPDATE;
- direct UPDATE/DELETE rejection on every new table plus event-chain forgery.

### Isolation, index, and migration gates

- snapshot existing V3/released reader results before/after materializing all
  five candidates: expected **5 unchanged out of 5**;
- repository import/SQL route scan finds **0 existing released readers out of
  all inspected readers** referencing a 3A table;
- catalog/matching/coverage/due endpoints remain unchanged and return no
  candidate projection;
- PostgreSQL catalog asserts every named integrity/audit/stale index exactly
  and asserts zero normalized-token, source-spelling, aircraft-ID, or matching
  indexes;
- v1/c14n-1 and v2/c14n-2 reader/hash parity vectors; v1 and v2 same logical
  values produce distinct identities; same-version retries reuse exactly;
  child rows reject a different pair; and all five v2 envelope/domain hex
  vectors match Python/PostgreSQL;
- fresh 0027 upgrade/backfill preserves all v1 bytes/hashes; empty-3A with one
  unmaterialized v2 proposal refuses downgrade; any v2 dependent audit row
  refuses downgrade; concurrent v2-write/downgrade and
  materializer/downgrade races serialize safely; v1-only empty-3A downgrade
  returns to 0026 with v1 readable; and re-upgrade restores exact metadata;
- UPDATE/DELETE rejection preserves immutable v2 proposals, bindings,
  submissions, relationships, and events; and
- migration/model parity plus deferred constraint execution on PostgreSQL, not
  SQLite substitutes.

## External-critic nonfinding clarifications

- **224-model performance:** implementation must run the complete 2011 packet
  through PostgreSQL materialization, deferred completeness, and reconstruction
  for 20 measured iterations with `SET LOCAL statement_timeout = '5s'` and
  `lock_timeout = '2s'`. Every run must complete inside 5 seconds and measured
  p95 must remain below 2.5 seconds, with query plans and row counts attached to
  implementation evidence. Failure blocks the migration; it cannot be fixed by
  weakening exact reconstruction or silently moving integrity to Python.
- **Correction generations:** only foundation/binding generation 1 is defined
  in 3A/3B. A second generation or re-correction of the same canonical
  correction key requires a future reviewed validator/schema/migration. V2
  rejects duplicate correction keys, and 3A never invents generation 2.
- **Platform administrator scope:** `platform_admin` is a role on one
  organization-membership row, not a global user flag. One user may hold that
  role in one organization and a non-admin role elsewhere. The exact selected
  active membership alone authorizes each request; roles are never combined
  across memberships.

## Expected file scope

This framing phase edits only:

- `.ai/review-runs/T081-V4-SCHEMA-SLICE-3A/decision.md`; and
- generated design packet artifacts inside that same new review run.

Expected implementation scope after design PASS is additive and bounded to:

- one backward-compatible validator-2/c14n-2 schema/profile and all five exact
  v2 hash domains while retaining byte-identical validator-1/c14n-1 read/hash
  dispatch for stored candidates;
- corrected 1998 explicit-unknown and 2002/2024 designation-group/search-hint
  calibration proposals, an exact hash-locked legacy validator-1 1998 fixture,
  plus schema, service, canonical, and evidence regressions proving existing
  stored validator-1 proposals remain immutable and auditable;
- migration 0027 after 0026, including locked v1 metadata backfill on Slice-2
  audit children, dual-version constraints/triggers, and the additive 3A
  tables, plus matching ORM models;
- the shared correction-foundation tables
  `ad_v4_candidate_corrections`, `ad_v4_candidate_correction_refs`,
  `ad_v4_candidate_correction_semantic_bindings`, and
  `ad_v4_candidate_correction_evidence_links`; their service may read and
  verify only canonical `authoritativeCorrections` plus referenced
  `officialDocuments` identity/evidence fields. Complete future-3B namespace
  refs are retained, but requirement/recurrence/AMOC/document semantics remain
  deferred;
- default-off application configuration for validator-2 writes and 3A routes,
  fixed compiled capability declarations, and the 0027 database capability
  function, default-off gate rows, deployment-role-only audited gate procedure,
  and transactional checks;
- one candidate applicability materializer/reconstructor/stale-fold service;
- narrow platform-admin request/response schemas and POST/audit GET routes;
- focused materializer, reconstruction, authorization, concurrency,
  PostgreSQL, migration, isolation, and five-packet calibration tests; and
- implementation evidence inside the Slice-3A run.

The reviewed validator-2 correction above is the only permitted V4 schema and
calibration edit. It must not mutate prior review records, retained source
PDFs/fragments, or stored validator-1 candidate rows. Implementation must not
edit the domain contract, V3 models/services/data, released readers,
frontend/UI, aircraft identity or configuration, requirement/timing/document/
AMOC semantic materialization, publication, matching, compliance, or due state.

## Known uncertainty and design-review questions

1. Canonical V4 intentionally has no per-model normalized identity. This design
   resolves the gap conservatively as explicit `unknown/not_extracted` in a
   separate unreviewed candidate mapping. The adversary should test that no
   implementation is tempted to promote exact source spelling or a heuristic
   alias to reviewed identity.
2. `series_expression` is source text, not a reviewed comparator grammar. It is
   stored losslessly with evaluation disabled. A later identity/series review
   must define executable membership before any matching cutover.
3. `airworthiness_directives.ad_number` is not currently a guaranteed unique,
   non-null identity. Candidate supersession resolution therefore permits only
   exactly-one resolution, records zero/multiple as explicit unresolved/
   ambiguous, and never changes released state.
4. PostgreSQL relational reconstruction must be measured against the 224-model
   packet. If one deferred function exceeds bounded transaction/statement
   limits, implementation must optimize its relational aggregation without
   weakening the exact-equality gate or silently moving all integrity to
   Python.
5. No candidate normalization, source-spelling, or aircraft hot-path index is
   created. A later matching decision must define the reviewed identity bridge
   and own any usable lookup index.
6. The cross-slice correction identity is resolved here: 3A creates the shared
   immutable foundation and complete ordered namespace; 3B may add only its
   owned immutable semantic bindings under that foundation.

None of these questions permits source-text copying, null-as-unknown,
manufacturer/model concatenation, candidate publication, V3 fallback, aircraft
matching, or a hidden writer.

```
### `.ai/review-runs/T081-V4-SCHEMA-SLICE-3A/findings.json`

size=51518; sha256=72d2441a64ca83bcad32e2358300ced5a4ba184bcd072ffb7518067fb83164d9; truncated=false

```text
[
  {
    "id": "T081-V4-S3A-DA-001",
    "stage": "design",
    "reviewer": "/root/v4_schema_adversary",
    "severity": "blocker",
    "status": "closed",
    "invariant": "Every valid calibration candidate can be materialized deterministically, including every listed model, while model normalization remains explicit unknown and does not duplicate evidence.",
    "summary": "The model identity-mapping cardinality allows only one mapping per designation scope, but every calibration designation scope contains multiple model values.",
    "evidence": [
      ".ai/review-runs/T081-V4-SCHEMA-SLICE-3A/decision.md:381-388 requires each model mapping to reference its parent designation-scope node and declares UNIQUE (projection_id, identity_kind, source_semantic_node_id).",
      ".ai/review-runs/T081-V4-SCHEMA-SLICE-3A/decision.md:424-435 requires every model designation-value row to name its model identity-mapping node.",
      "Independent enumeration found 10 listed designation scopes out of 10 with more than one model: counts are 51, 30, 6, 182, 224, 7, 2, 10, 33, and 130. The proposed uniqueness therefore conflicts on the second model in every scope and makes 0 of 5 calibration materializations feasible as written."
    ],
    "impact": "The positive 5/5 gate cannot execute. Any implementation must either omit required per-model mappings, violate its own uniqueness constraint, or collapse multiple exact source designations into one row and lose round-trip identity.",
    "requiredClosure": "Define a nonconflicting identity for one mapping per exact designation occurrence, such as a composite including the designation-value node or exact source value, while retaining one parent-scope evidence inheritance edge and no per-model evidence copy. Provide a row/key/FK example for a multi-model scope and a static 5/5 cardinality proof.",
    "closureEvidence": [
      "decision.md Safety invariant 9 and section 2.3 make source_occurrence_node_id the exact designation-value/member node, require one mapping per occurrence, and inherit source support through one evidence_parent_node_id without per-model links.",
      "decision.md section 2.4 gives the 5/5 static cardinality proof: [51,30], [6], [182], [224], and [7,2,10,33,130] exact value occurrences produce 81, 6, 182, 224, and 182 distinct mappings with 2,1,1,1,5 parent-scope inheritance edges.",
      "Independent closure review recomputed 10 listed scopes out of 10 and verified that source_occurrence_node_id is now the per-value semantic node while evidence_parent_node_id remains the shared designation-scope node. UNIQUE (projection_id, identity_kind, source_occurrence_node_id) therefore permits every occurrence without per-model evidence links."
    ]
  },
  {
    "id": "T081-V4-S3A-DA-002",
    "stage": "design",
    "reviewer": "/root/v4_schema_adversary",
    "severity": "blocker",
    "status": "closed",
    "invariant": "Splitting applicability from obligations preserves one exact, evidence-bound correction object and permits a later full relational round-trip without duplicate or disconnected authority.",
    "summary": "The shared correction-generation boundary is deferred even though a current calibration correction spans Slice 3A and Slice 3B namespaces.",
    "evidence": [
      ".ai/review-runs/T081-V4-SCHEMA-SLICE-3A/decision.md:306-324 creates per-applicability change-dependency nodes, reduces out-of-scope correction references to a count, and assigns their typed projection to Slice 3B.",
      ".ai/review-runs/T081-V4-SCHEMA-SLICE-3A/decision.md:973-976 explicitly leaves the shared projection-generation root as a later design question.",
      "backend/tests/fixtures/ad_v4_calibration/2008-26-10.proposal.json:1064-1083 contains one correction-2010 object whose changedSemanticRefs set includes both productScopes/scope-cessna and requirements/req-report under one document pair and one evidence-key set."
    ],
    "impact": "Slice 3A can neither prove nor preserve the future one-object correction identity. Slice 3B would have to duplicate correction provenance/evidence or invent an unreviewed merge convention, and the combined relational model could not prove an exact full-proposal correction round-trip.",
    "requiredClosure": "Resolve the shared foundation before 3A: define one proposal-scoped immutable correction root keyed to the canonical correction object, with exact evidence/document identity and namespace edges that 3A and 3B can add under one completeness/generation contract. Alternatively defer the whole correction projection, but then remove 3A correction-derived state. Demonstrate exact reconstruction of correction-2010 after both slices without repeated evidence links or count-only placeholders.",
    "closureEvidence": [
      "decision.md section 2.1.1 defines one immutable proposal-scoped correction root, complete ordered refs for all current and future-3B namespaces, one correction evidence set, immutable generation bindings, and namespace ownership/completeness rules.",
      "decision.md section 2.1.1 reconstructs correction-2010 as one root, two ordered refs (productScopes/scope-cessna and requirements/req-report), two evidence links once, one 3A binding, and one later 3B binding without duplicating correction/document/evidence identity.",
      "Independent closure review traced correction-2010 against the canonical fixture: the foundation stores the complete two-ref set and one two-key evidence set at generation 1; 3A binds only scope-cessna and 3B can append only the req-report semantic binding without updating the root/ref/evidence authority or changing serialized correction JSON."
    ]
  },
  {
    "id": "T081-V4-S3A-DA-003",
    "stage": "design",
    "reviewer": "/root/v4_schema_adversary",
    "severity": "blocker",
    "status": "closed",
    "invariant": "Regulatory or configuration uncertainty is an explicit unknown state with reason, temporal scope, and evidence; a known text value cannot stand in for uncertainty.",
    "summary": "The mandatory 1998 calibration encodes an unknown repairer state as a known string, contradicting the contract and Slice 3A's own unknown invariant.",
    "evidence": [
      ".ai/AD_EXTRACTION_DOMAIN_CONTRACT.md:103-112 requires missing, ambiguous, or unsupported applicability facts to remain uncertain and requires explicit unknown with reason, evidence, and temporal scope.",
      ".ai/review-runs/T081-V4-SCHEMA-SLICE-3A/decision.md:108-112 and 360-368 repeat that unknown cannot be represented as a known or null value.",
      "backend/tests/fixtures/ad_v4_calibration/1998-17-11.proposal.json:334-352 stores condition-provenance-unknown.attributeValue as state known with value unknown_requires_compliance.",
      "backend/tests/test_ad_v4_calibration.py:264-266 affirmatively locks that placeholder-as-known representation into the existing oracle; the source fragment is explicitly anchored by '(4) If it cannot be determined'."
    ],
    "impact": "A purportedly lossless 3A projection would persist uncertainty as affirmative known data. Later condition evaluation or review could treat the sentinel as an ordinary value, violating the fail-closed domain contract while still passing byte-for-byte reconstruction.",
    "requiredClosure": "Correct the canonical calibration representation to an explicit unknown union with controlled reason, temporal scope, and evidence, and rerun the predecessor schema/canonical/evidence review needed for that fixture change. Add a negative gate rejecting semantic sentinels such as unknown_requires_compliance in known assertions when they encode uncertainty.",
    "closureEvidence": [
      "decision.md section 0 freezes validator-1 for immutable stored candidates and specifies validator-2 for new writes, with materializer refusal rather than mutation/invalidation of old sentinel-bearing candidates.",
      "decision.md Explicit uncertainty subsection replaces unknown_requires_compliance with an unknown union carrying reason not_observed, temporal scope, and evidence; new schema/service/calibration and legacy-verification regressions are explicit implementation gates.",
      "Independent closure review verified the corrected 1998 shape uses the already-existing V4 unknown union and retains ev-unknown-provenance plus at_applicability_evaluation. The legacy bytes remain validator-1 candidate-only and are refused for 3A rather than rewritten; implementation must still satisfy the separate validator-2 rollback/version finding DA-010."
    ]
  },
  {
    "id": "T081-V4-S3A-DA-004",
    "stage": "design",
    "reviewer": "/root/v4_schema_adversary",
    "severity": "blocker",
    "status": "closed",
    "invariant": "Applicability relationships remain queryable as manufacturer, model, series, and installed-equipment identities without parsing flattened display strings.",
    "summary": "Condition subjects and the search-hint fixture retain compound display strings rather than articulated identity relationships.",
    "evidence": [
      ".ai/AD_EXTRACTION_DOMAIN_CONTRACT.md:88-101 requires manufacturer, model, and series relationships to remain distinguishable; lines 346-355 require the search questions to be answerable without parsing flattened display strings.",
      "backend/app/schemas/ad_extraction_v4.schema.json:118-123 defines conditionSubject.modelOrSeries as one knownString rather than a typed designation set.",
      "backend/tests/fixtures/ad_v4_calibration/2002-13-04.proposal.json:135-153 stores 6314,6324,6364 in one value and lines 184-195 store five engine models in one comma-delimited value. backend/tests/test_ad_v4_calibration.py:251-253 must split the string to reason about membership.",
      "backend/tests/fixtures/ad_v4_calibration/2024-14-03.proposal.json:504-511 similarly combines GFC 500 and GSA 28 in one modelOrSeries value.",
      "backend/tests/fixtures/ad_v4_calibration/2002-13-04.proposal.json:485-503 uses manufacturer 'multiple' with models belonging to different manufacturers, so the hint cannot retain model-to-manufacturer relationships."
    ],
    "impact": "The relational projection is byte-lossless but not semantically articulated enough for safe future model/installed-equipment queries. A future reader would have to parse punctuation/conjunctions or infer manufacturer associations, exactly the behavior the domain contract prohibits.",
    "requiredClosure": "Define source-faithful compound text separately from a typed, explicitly unreviewed designation/member relationship with evidence and unknown normalization, or revise the canonical schema through a separately reviewed predecessor change. Represent multi-manufacturer hints as source-preserving groups/pairs or explicit unknown associations. Prove the 2002 and 2024 examples can be queried without string parsing and without treating hints as controlling.",
    "closureEvidence": [
      "decision.md section 0 defines a closed sourceDisplayText/designationGroup/member representation and manufacturerModelGroups with explicit association or source_ambiguous unknown; display punctuation is never parsed.",
      "decision.md records exact 2002 groups (3 magnetos, 5 engine families, atomic LTSIO, 7 manufacturer groups/27 models) and exact 2024 Garmin all_members GFC 500/GSA 28 representation while hints remain noncontrolling.",
      "Independent closure review found the repair is not canonical-version safe: decision.md section 0 adds designationGroup.members and manufacturerModelGroups/member arrays while retaining paprnav-ad-v4-c14n-1, but the closed Slice-2 decision states that adding any array requires a new reviewed canonicalization version.",
      "Independent source inspection of retained 2002 page 2 found the text '172A through 172H'. The remediation's Cessna count of 16 and overall 27 exact model members can be reached only by expanding that source series expression into eight model identities. That contradicts invariants 8/13 and the no-parsing/no-inferred-series rule; source-faithful representation would preserve the expression as an unevaluated series member rather than claim eight exact models.",
      "Targeted remediation assigns all new closed designation/search-group objects and member arrays to paprnav-ad-v4-validator-2 and paprnav-ad-v4-c14n-2, specifies every new array key/order rule, and pins byte-exact v2 proposal/binding/event/submission/relationship hash domains and envelope literals.",
      "The corrected retained-source oracle now has seven manufacturer groups, 19 exact model members, and one Cessna series_expression member with exact text '172A through 172H' and unknown/unsupported_expression; it explicitly forbids inferred exact 172A-H rows and tests absence of 172B and 172H.",
      "Bounded closure-2 remediation replaces the model-only hint table with typed search_hint_members: model rows require source_designation, series_expression rows require exact expression_text plus unevaluated/unsupported_expression and source_only/unknown identity provenance, with canonical ordinal and one inherited evidence-parent edge. Exact reconstruction uses the discriminator and never parses text.",
      "Independent closure-2 review verified the c14n-2 member one-of and relational discriminator are lossless: the retained phrase '172A through 172H' remains one series_expression occurrence, reconstruction emits its fixed canonical unknown/unsupported_expression branch from typed columns, and the 2002 oracle is exactly 19 model members plus 1 expression with no inferred 172B/172H rows. The 2024 Garmin pair remains an all_members group with no display-string parsing."
    ]
  },
  {
    "id": "T081-V4-S3A-DA-005",
    "stage": "design",
    "reviewer": "/root/v4_schema_adversary",
    "severity": "high",
    "status": "closed",
    "invariant": "Every source-to-normalized identity assertion has an honest, schema-representable origin and never implies candidate-supplied normalization where none exists.",
    "summary": "The normalization-origin enum has no valid state for source-only manufacturers or model/series values in conditions and search hints.",
    "evidence": [
      ".ai/review-runs/T081-V4-SCHEMA-SLICE-3A/decision.md:370-388 permits only candidate_payload or materializer_missing_model_mapping and says candidate_payload manufacturer mappings reconstruct canonical normalizedIdentity.",
      "backend/app/schemas/ad_extraction_v4.schema.json:118-123 and 226-237 provide only source knownString/identifier values for condition and hint manufacturers/models; they contain no normalizedIdentity payload.",
      ".ai/review-runs/T081-V4-SCHEMA-SLICE-3A/decision.md:459-463 and 503-515 nevertheless require identity mappings for those source-only fields. The 2002 fixture exercises both paths."
    ],
    "impact": "An implementation must mislabel a source-only manufacturer as payload-normalized, misuse a model-specific missing origin for a manufacturer, or omit a required mapping. Any choice corrupts provenance and makes normalized-token indexes/audit responses misleading.",
    "requiredClosure": "Add explicit closed origins for source-only/no-normalized-identity assertions across manufacturer, model, and series, define their mandatory unknown reason/temporal/evidence inheritance, and give exact mapping rows for the 2002 condition and search hint. Candidate_payload must remain legal only where normalizedIdentity actually exists in canonical bytes.",
    "closureEvidence": [
      "decision.md section 2.3 closes origin to candidate_payload, source_only, or no_normalized_identity; candidate_payload is legal only for an actual normalizedIdentity property.",
      "The same section requires unknown state, controlled reason, temporal scope, and single-parent evidence inheritance for the other origins and gives exact 2002 condition-member and hint-member examples.",
      "Independent closure review verified candidate_payload is restricted to an actual normalizedIdentity occurrence, while source_only and no_normalized_identity are forced to explicit unknown without token/value and inherit one same-projection evidence parent."
    ]
  },
  {
    "id": "T081-V4-S3A-DA-006",
    "stage": "design",
    "reviewer": "/root/v4_schema_adversary",
    "severity": "high",
    "status": "closed",
    "invariant": "A candidate supersession signal is proposal-bound, causal, idempotent, and cannot stale another candidate based on an unrelated relation.",
    "summary": "Supersession propagation neither binds the relation's successor to the materialized proposal nor records the dependency row as the stale event's causal identity.",
    "evidence": [
      ".ai/review-runs/T081-V4-SCHEMA-SLICE-3A/decision.md:291-304 lists causing Slice-2 relationship, lifecycle-event, or projection IDs but no causing change-dependency ID, while also requiring every system event to name a deterministic causal row.",
      ".ai/review-runs/T081-V4-SCHEMA-SLICE-3A/decision.md:306-318 stores the canonical supersession relation in a 3A change-dependency row, which is the missing causal row type.",
      ".ai/review-runs/T081-V4-SCHEMA-SLICE-3A/decision.md:664-669 permits exact predecessor resolution to stale existing projections but never requires successorAdNumber to equal the current proposal's evidence-bound directive AD number.",
      "backend/app/schemas/ad_extraction_v4.schema.json:240-243 permits any non-self predecessor/successor strings, and backend/app/services/ad_v4_candidates.py:605-613 checks only self/cycle structure, not binding to the proposal's own AD identity."
    ],
    "impact": "A valid candidate for AD C can carry an evidence-bound A-to-B relation and automatically append a stale signal to A's projection even though the proposal is not B. Multiple distinct dependency signals also lack an exact event-cause FK, weakening deduplication and audit reconstruction.",
    "requiredClosure": "Require a supersession dependency to prove that its successor equals the proposal's known canonical AD number before any cross-projection signal; otherwise retain it as unresolved without side effects. Add a same-projection causing_dependency_id composite FK and closed event discriminator/causal uniqueness definition. Test unrelated-successor, multiple/contradictory relations, retry, and concurrent signal insertion.",
    "closureEvidence": [
      "decision.md sections 2.1 and 6 require successor byte-equality with this proposal's known evidence-bound canonical AD number before lookup; mismatch/unknown/ambiguous relations remain unresolved and have no side effect.",
      "Target-local incoming dependency rows are the stale event's same-projection composite-FK cause, with closed event discriminators, causal uniqueness, deterministic hashes, sorted locks, retry and concurrency convergence tests.",
      "Independent closure review verified unrelated/unknown successors remain outgoing unresolved rows with no target lookup, incoming row, or event; the incoming dependency ID is now the target-local composite-FK event cause and has a dedicated causal uniqueness key."
    ]
  },
  {
    "id": "T081-V4-S3A-DA-007",
    "stage": "design",
    "reviewer": "/root/v4_schema_adversary",
    "severity": "high",
    "status": "closed",
    "invariant": "Every materialize and audit call is authorized through one exact active platform-admin membership, rather than through any membership attached to the user.",
    "summary": "The POST selects an acting membership, but the two audit GET contracts omit that selector while claiming the same exact-membership boundary.",
    "evidence": [
      ".ai/review-runs/T081-V4-SCHEMA-SLICE-3A/decision.md:142-146 requires an exact active membership for materialize or audit endpoints.",
      ".ai/review-runs/T081-V4-SCHEMA-SLICE-3A/decision.md:593-605 names Paprnav-Acting-Membership-Id only for POST and specifies no equivalent input for either GET.",
      ".ai/review-runs/T081-V4-SCHEMA-SLICE-3A/decision.md:744-746 says GET uses the same role boundary without defining exact-membership selection/locking.",
      "backend/app/api/routes/admin.py:19-26 and backend/app/api/routes/ads.py:330-395 show the current audit pattern authorizes when any loaded membership is active platform_admin, demonstrating that 'platform-admin-only' is not by itself the decision's stronger exact-membership contract."
    ],
    "impact": "Implementations can satisfy the endpoint prose using the existing any-membership helper while violating invariant 24. With multiple organizations/memberships, the audit authorization context is ambiguous and cannot be attributed or tested as specified.",
    "requiredClosure": "Specify whether audit GETs require Paprnav-Acting-Membership-Id (recommended) and define exact user/membership/status/role validation under one transaction. If the domain intentionally permits any active global membership, revise invariant 24 and the audit contract explicitly rather than relying on the current helper. Add GET-specific multi-membership, inactive-selected-membership, shop/admin, and revocation-race tests.",
    "closureEvidence": [
      "decision.md section 5 requires Paprnav-Acting-Membership-Id for POST and both GET audit endpoints and transactionally locks/validates the exact selected membership's user, active status, and platform_admin role before candidate reads.",
      "The contract denies selected inactive/shop/foreign memberships even when another valid admin membership exists and defines deterministic revocation-race and multi-membership tests.",
      "Independent closure review verified both GET contracts now require the membership header and lock/revalidate that exact membership; another active platform-admin membership cannot rescue an invalid selected row."
    ]
  },
  {
    "id": "T081-V4-S3A-DA-008",
    "stage": "design",
    "reviewer": "/root/v4_schema_adversary",
    "severity": "high",
    "status": "closed",
    "invariant": "Every Slice-2-valid condition has one deterministic relational representation, and Slice 3A does not invent an unversioned semantic restriction after canonical persistence.",
    "summary": "The proposed condition type/operator compatibility matrix is normative but never defined and is not present in the closed Slice-2 schema/validator.",
    "evidence": [
      ".ai/review-runs/T081-V4-SCHEMA-SLICE-3A/decision.md:448-457 requires a checked type/operator compatibility matrix but provides no allowed pairs or version.",
      "backend/app/schemas/ad_extraction_v4.schema.json:125-136 declares independent conditionType and operator enums without conditional pair constraints.",
      "backend/app/services/ad_v4_candidates.py:475-615 validates keys/references/cycles but does not validate condition type/operator pairs.",
      "The five packets cover only a small subset of possible enum combinations, so their 5/5 success cannot define the missing matrix."
    ],
    "impact": "Two conforming implementations can accept different Slice-2 candidates, or 3A can reject a previously valid immutable candidate based on an invented rule. Database CHECKs and reconstruction tests cannot be written against a unique contract.",
    "requiredClosure": "Either enumerate and version every permitted type/operator/subject-shape combination and apply that rule at the Slice-2 canonical boundary through a separately reviewed change, or declare all currently schema-valid pairs representable but unevaluated in 3A and remove the undefined compatibility claim. Add one positive and one negative vector for every normative pair/shape rule.",
    "closureEvidence": [
      "decision.md invariants 14/16 and section 2.5 remove the undefined compatibility matrix and require every Slice-2-schema-valid enum pair to be represented with evaluation_state=unevaluated and evaluator_contract=none.",
      "The test strategy requires 90 represented/reconstructed out of 90 current type/operator pairs plus closed-shape/enum negatives; evaluation and matching remain prohibited pending a separately reviewed future contract.",
      "Independent closure review confirmed no semantic pair matrix is invented: every current enum cross-product is stored with evaluation_state unevaluated/evaluator_contract none, while schema shape and unknown enum validation remain at the canonical boundary."
    ]
  },
  {
    "id": "T081-V4-S3A-DA-009",
    "stage": "design",
    "reviewer": "/root/v4_schema_adversary",
    "severity": "high",
    "status": "closed",
    "invariant": "Any index described as future aircraft-ID lookup support has a safe, reviewed identity join path and is not permanently empty under the only accepted canonical schema.",
    "summary": "The model-token indexes are knowingly empty and have no future reviewed-identity bridge, so they do not support the claimed aircraft-ID lookup shape.",
    "evidence": [
      ".ai/review-runs/T081-V4-SCHEMA-SLICE-3A/decision.md:381-393 requires all current model mappings to be unknown and requires a later reviewed mapping relation rather than updating these rows.",
      ".ai/review-runs/T081-V4-SCHEMA-SLICE-3A/decision.md:563-585 creates model-token indexes and admits they are empty for current listed models.",
      ".ai/review-runs/T081-V4-SCHEMA/codex-schema-proposal.md:830-859 defines the future hot path as a reviewed canonical model-identity ID join, not a source-string or unreviewed hash match.",
      "No 3A table has an aircraft/canonical-registry FK, and the design explicitly defers the reviewed relation that would own the usable index."
    ],
    "impact": "The migration adds write/DDL cost and a misleading appearance of lookup readiness without a safe join path. A future matching slice must create different reviewed-relation indexes anyway, or risk joining aircraft identities to unreviewed candidate tokens.",
    "requiredClosure": "Remove the vacuous token indexes and explicitly defer reviewed lookup indexes to the identity/matching slice, or define a stable non-authoritative designation-node bridge that the later reviewed identity relation will reference and state that the usable index belongs there. Do not claim current candidate-token indexes support aircraft-ID matching, and retain tests proving no reader uses them.",
    "closureEvidence": [
      "decision.md invariant 26 and section 4 remove source-spelling, normalized-token, aircraft-ID, make/model, search-hint, and product-role hot-path indexes and make no readiness claim.",
      "Only integrity, reconstruction, audit, correction-completeness, dependency, and stale-fold indexes remain; the future reviewed identity/matching slice owns its bridge and usable indexes, with absence and released-reader isolation tests.",
      "Independent closure review verified the decision removed the normalized/source/aircraft/matching index list and now requires PostgreSQL catalog negatives proving those indexes are absent; no readiness claim remains."
    ]
  },
  {
    "id": "T081-V4-S3A-DA-010",
    "stage": "design",
    "reviewer": "/root/v4_schema_adversary",
    "severity": "blocker",
    "status": "closed",
    "invariant": "Validator-2/canonicalization evolution and physical or application rollback preserve the meaning and readability of every immutable Slice-2 candidate without leaving newer rows under an older schema contract.",
    "summary": "The validator-2 proposal changes the existing Slice-2 storage boundary, but the downgrade checks only Slice-3A tables and can strand validator-2 candidates at revision 0026, whose database writer and application know only validator-1.",
    "evidence": [
      ".ai/review-runs/T081-V4-SCHEMA-SLICE-3A/decision.md:227-267 makes all new candidate submissions use validator-2 and retains those immutable rows in the existing ad_v4_candidate_proposals table.",
      "backend/app/db/migrations/versions/20260901_0026_add_ad_v4_candidates.py:155-177 hardcodes paprnav-ad-v4-validator-1 in the proposal INSERT trigger; backend/app/services/ad_v4_candidates.py:33 likewise has only validator-1.",
      ".ai/review-runs/T081-V4-SCHEMA-SLICE-3A/decision.md:1097-1112 says application rollback disables only 3A routes and physical downgrade checks only new 3A tables before returning to 0026. A validator-2 proposal can exist without a 3A projection, so those checks can pass while incompatible Slice-2 rows remain.",
      "The closed Slice-2 decision's canonicalization section states that adding an array requires a new reviewed canonicalization version. The revised design adds multiple typed group/member arrays but keeps paprnav-ad-v4-c14n-1, compounding the rollback/hash-dispatch ambiguity."
    ],
    "impact": "An empty 3A schema could downgrade successfully while immutable validator-2/canonicalization rows remain. Revision 0026 and an old application cannot create, validate, or reliably attest those rows under their recorded contract; rollback therefore ceases to be truthful and mixed-version deployments can disagree about proposal identity.",
    "requiredClosure": "Assign the added arrays a new canonicalization version and domain, define validator/canonicalizer dispatch for every stored proposal, and include validator/canonicalization version in all repeated projection envelopes. Define mixed-version deployment order. Physical downgrade must lock the Slice-2 proposal table and refuse while any validator-2/new-canonicalization proposal or dependent submission/event exists (or retain a backward verifier in an explicitly non-downgraded compatibility revision). Application rollback must preserve read verification for both versions. Add empty-3A/nonempty-validator2 downgrade refusal, old/new read parity, same-content reuse, and re-upgrade tests.",
    "closureEvidence": [
      "decision.md Validator-2 canonicalization and hash domains defines validator-2/c14n-2, byte-exact NUL-terminated domains, fixed v2 envelopes, version-scoped proposal/audit identity, and no cross-version content reuse.",
      "decision.md Migration, compatibility, correction, and rollback requires migration 0027 to backfill explicit v1 version metadata on Slice-2 audit children without changing bytes/hashes, constrain all child rows to parent versions, deploy dual readers before v2 writers/3A, and prohibit pre-v2 applications while v2 rows exist.",
      "The physical downgrade contract locks all 3A and Slice-2 proposal/submission/relationship/event/binding tables and refuses any v2 proposal or dependent audit row even with empty 3A; tests cover v1/v2 parity/distinct identity/retry, empty-3A nonempty-v2 refusal, races, immutable v2 rows, and v1-only downgrade/re-upgrade.",
      "Bounded closure-2 remediation establishes one proposal-first global order: downgrade takes Slice-2 proposal ACCESS EXCLUSIVE before Slice-2 children and all 3A tables, while each materializer locks its proposal before any 3A row. The decision enumerates candidate-create/materialize/downgrade outcomes and removes the proposal/3A lock inversion.",
      "Independent closure-2 review verified the global serialization boundary: candidate creation and materialization touch/lock the Slice-2 proposal before any 3A row, downgrade takes ACCESS EXCLUSIVE on that parent table before Slice-2 children and 3A tables, and the stated commit-first/wait-first outcomes cannot form the former parent/child lock cycle. Empty-3A v2 rows still refuse downgrade; v1-only downgrade/re-upgrade and dual-reader application rollback preserve immutable bytes and hashes."
    ]
  },
  {
    "id": "T081-V4-SCHEMA-SLICE-3A-CC-001",
    "stage": "external-critic",
    "reviewer": "claude-external-critic-20260906T235706Z",
    "severity": "medium",
    "status": "closed",
    "invariant": "Every other safety/correctness invariant in this design is enforced by the database or application transaction rather than by operator discipline (e.g., invariant 2's 'creation-time validity is not trusted'); the staged validator-2/3A rollout should meet the same bar.",
    "summary": "The mandatory deployment order (apply 0027 -> dual-reader app -> enable v2 writer -> enable 3A routes) has no concrete code-level gate. The codebase has no existing feature-flag mechanism, so nothing prevents a rolling deploy from serving v2 writes or 3A routes from an instance before all instances are dual-readers.",
    "evidence": [
      "review-packet.md:1262-1269 'Deployment order is mandatory: 1. apply 0027 ... 2. deploy the compatibility application ... 3. enable the v2 writer after all serving instances are dual readers; and 4. enable the 3A materializer/routes only after v2 writes are proven.'",
      "grep for feature_flag/FEATURE_FLAG/ENABLE_*/settings.FEATURE across backend/app returned zero matches, confirming there is no existing toggle mechanism this design could rely on.",
      "Every other invariant in the same document (e.g., invariant 2, invariant 24) is phrased as a transaction-enforced or trigger-enforced guarantee, not a manual rollout instruction."
    ],
    "impact": "A rolling/blue-green deploy that briefly runs mixed old/new application instances (a routine production pattern) could serve v2 candidate writes or 3A materialization from a not-yet-fully-rolled-out fleet, or could enable 3A routes before the v2 writer has been proven safe in production, silently violating the design's own stated sequencing without any error, log, or DB rejection.",
    "requiredClosure": "Define a concrete, code-level gate (e.g., an environment/config flag read at router-registration or write-path time) that makes 'v2 writer enabled' and '3A routes enabled' explicit, independently togglable states rather than an implicit consequence of which code version is deployed. Add a test or startup check proving the 3A routes/v2 writer cannot activate merely because migration 0027 has run.",
    "closureEvidence": [
      "decision.md section 5.1 defines independent default-off PAPRNAV_AD_V4_VALIDATOR2_WRITES_ENABLED and PAPRNAV_AD_V4_SLICE3A_ROUTES_ENABLED settings, fixed compiled capabilities, and migration-0027 database capability checks at startup and again inside write transactions.",
      "The deployment contract requires the dual-reader compatibility release with both flags false before any config enablement, states that the gate does not prove fleet-wide rollout, and adds default-off, independent-toggle, schema-mismatch, transactional recheck, and rollback tests.",
      "Targeted correction requires the 3A materialization POST to observe both application flags and both database gates validator2_write_enabled/materializer3a_enabled, while audit GET requires only the 3A/read gate and cannot create a missing projection.",
      "The four-combination matrix now proves that v2-write off plus 3A on rejects materialization of a preexisting v2 candidate with validator2_write_gate_disabled and zero request/projection/dependency/correction/event rows; proposal-before-gate locking defines both outcomes for concurrent disable versus materialization.",
      "Independent external-critic closure review verified the gates are concrete and independently controlled rather than operator prose: both application flags and both deployment-role-controlled database gates default false; validator-2 POST requires its paired flag/gate; 3A POST requires both pairs; audit GET requires only the 3A/read pair and cannot create missing rows. Startup plus in-transaction capability checks, the exact four-state preexisting-v2 matrix, concurrent disable barriers, mixed-release false defaults, and rollback/drain order are all mandatory implementation tests."
    ]
  },
  {
    "id": "T081-V4-SCHEMA-SLICE-3A-CC-002",
    "stage": "external-critic",
    "reviewer": "claude-external-critic-20260906T235706Z",
    "severity": "medium",
    "status": "closed",
    "invariant": "The design's stated in-scope/out-of-scope boundary (Objective section) and its 'Expected file scope' section should name every namespace and table Slice 3A is authorized to touch, so an implementer or later reviewer can verify boundary compliance without re-deriving it from a 1,500-line design body.",
    "summary": "Section 2.1.1 requires Slice 3A to create a shared, proposal-scoped correction foundation that stores canonical `authoritativeCorrections` content and verified `officialDocuments` identity hashes -- two top-level V4 namespaces distinct from the four-field applicability subtree {productScopes, conditionDefinitions, applicabilityRules, applicabilitySearchHints}. Neither namespace is mentioned in the Objective's in/out-of-scope bullet list, nor explicitly named in the 'Expected file scope' section, even though the mandatory 2008-26-10 calibration assertion depends on it.",
    "evidence": [
      "review-packet.md:28-63 (Objective) lists what's out of scope for 3A/deferred to 3B but never mentions `authoritativeCorrections` or `officialDocuments`.",
      "review-packet.md:581-655 (section 2.1.1) defines `ad_v4_candidate_corrections`, `_correction_refs`, `_correction_semantic_bindings`, `_correction_evidence_links` storing `officialDocuments reference keys`, their `verified document-identity hashes`, and namespace refs spanning `requirements|recurrenceGroups|amocAuthorityProvisions` (3B-owned) in addition to 3A-owned namespaces.",
      "backend/app/schemas/ad_extraction_v4.schema.json $defs.proposal.properties includes `authoritativeCorrections` and `officialDocuments` as independent top-level arrays, confirming these are namespaces outside the four-field subtree definition in invariant 3.",
      "review-packet.md:1458-1489 ('Expected file scope') mentions only 'the additive 3A tables' generically and never names the correction-foundation tables or namespaces, while the mandatory test for 2008-26-10 (review-packet.md:1369-1372) requires 'exact shared correction-2010 foundation with two ordered refs, two evidence links once, one 3A scope binding, and one explicit future-3B requirement ref'."
    ],
    "impact": "An implementer following the Objective/Expected-file-scope sections literally could reasonably treat the correction-foundation tables as unauthorized scope creep and omit them, causing the mandatory 2008-26-10 reconstruction test (and the whole DA-002 closure) to fail; conversely, a later reviewer auditing 'did 3A only touch what it said it would' has no single authoritative scope list to check against, since the two scope-defining sections disagree with the detailed design.",
    "requiredClosure": "Update the Objective's out-of-scope list and the 'Expected file scope' section to explicitly name the correction-foundation tables and the `authoritativeCorrections`/`officialDocuments` namespaces they read/verify, so the document's own scope statement is internally consistent with section 2.1.1 and the mandatory calibration test.",
    "closureEvidence": [
      "decision.md Objective now explicitly authorizes the shared correction foundation, all four correction tables, and read/verification of authoritativeCorrections plus referenced officialDocuments identity/evidence while deferring 3B obligation/document semantics.",
      "decision.md Expected file scope repeats the exact tables/namespaces and implementation boundary, eliminating the scope conflict with section 2.1.1 and the 2008 calibration gate.",
      "Independent external-critic closure review verified both scope-defining sections now name the four shared correction-foundation tables and authorize only canonical authoritativeCorrections plus referenced officialDocuments identity/evidence fields. Complete ordered future-3B references are retained, but requirement, recurrence, AMOC, incorporated-document, and service-bulletin semantics remain explicitly deferred."
    ]
  },
  {
    "id": "T081-V4-SCHEMA-SLICE-3A-CC-003",
    "stage": "external-critic",
    "reviewer": "claude-external-critic-20260906T235706Z",
    "severity": "low",
    "status": "closed",
    "invariant": "'Write paths and administrative paths' asserts no new operational writer (job/CLI/seed/etc.) is added beyond the single platform-admin POST service.",
    "summary": "The stale-fold section introduces 'a background repair function [that] may append missing deterministic events after a crash,' which reads as a new asynchronous/scheduled process, apparently in tension with the explicit claim elsewhere that no provider job, CLI, seed, or generic writer is added.",
    "evidence": [
      "review-packet.md:1081-1085 'A background repair function may append missing deterministic events after a crash; it uses the same locks and event identity and requires no human review.'",
      "review-packet.md:1205-1213 ('Write paths and administrative paths') states 'No provider job, CLI, seed, V3 translator, calibration loader, frontend form, or generic ORM CRUD writer is added,' and that 'Its internal deterministic stale-event helper is part of the same service/repository boundary,' without clarifying whether the crash-repair helper is invoked synchronously (e.g., opportunistically on the next POST/GET) or via a new scheduled/background worker process."
    ],
    "impact": "If implementation interprets 'background repair function' as a new cron/worker process, that is new operational surface (deployment unit, scheduling, monitoring) not accounted for anywhere else in the design's operational sections, and could be missed by an implementation reviewer who only checks for 'no new job' against the explicit write-paths sentence.",
    "requiredClosure": "Clarify in the design that the repair helper is invoked inline/opportunistically from existing request paths (not a new scheduled process), or, if a real background worker is intended, add it explicitly to the write-paths/operational sections and its own authorization/idempotency contract.",
    "closureEvidence": [
      "decision.md section 6 and Write paths now state the repair helper runs inline only inside an authorized materialization POST transaction; audit GET invokes detection-only mode and remains side-effect-free.",
      "The design explicitly forbids cron, queue consumer, worker, scheduler, CLI, repair endpoint, startup sweep, or any new operational writer.",
      "Independent external-critic closure review verified repair is inline only in the already-authorized materialization POST transaction and reuses its locks, capability gates, deterministic cause identity, and idempotent event key. GET executes detection-only logic and remains side-effect-free; no asynchronous or alternate writer surface is authorized."
    ]
  },
  {
    "id": "T081-V4-S3A-IA-001",
    "stage": "implementation",
    "reviewer": "/root/v4_s3a_impl_adversary",
    "severity": "blocker",
    "status": "open",
    "invariant": "The implementation uses the approved typed relational design with database-enforced ownership, closed shapes, cardinality, order, references, arity, acyclicity, evidence, and unevaluated semantics.",
    "summary": "Migration 0027 substitutes generic semantic-node and JSON-pointer datum tables for the approved typed applicability tables and constraints.",
    "evidence": ["decision.md:663-924 specifies typed tables and constraints", "backend/app/db/migrations/versions/20260907_0027_add_ad_v4_applicability.py:93-208 creates generic semantic-node and datum tables", "backend/app/services/ad_v4_applicability.py:_flatten serializes arbitrary JSON shapes"],
    "impact": "Malformed or executable-looking semantic graphs can be stored without the reviewed database guarantees, and the implementation differs materially from the approved design.",
    "requiredClosure": "Implement the approved typed schema and PostgreSQL negative tests, or return to design review and prove an equivalent generic design."
  },
  {
    "id": "T081-V4-S3A-IA-002",
    "stage": "implementation",
    "reviewer": "/root/v4_s3a_impl_adversary",
    "severity": "blocker",
    "status": "closed",
    "invariant": "A projection root and its complete exact relational children are validated together at commit.",
    "summary": "PostgreSQL permits a valid-looking projection root with zero or partial relational children.",
    "evidence": ["Projection counts are ordinary root columns", "paprnav_v4_validate_app_projection is only a BEFORE INSERT root-envelope trigger", "No deferred child-graph constraint or decisive direct-SQL partial-graph test exists"],
    "impact": "A direct writer can commit incomplete immutable derived state that only later application reads may detect.",
    "requiredClosure": "Add deferred full-graph reconstruction/count/hash/evidence validation and direct-SQL empty, missing, extra, reordered, changed-value, and cross-reference tests.",
    "closureEvidence": [
      "Migration 0027 now installs recursive JSON-node expansion plus a deferred constraint trigger on every projection/child/correction table; it compares the exact relational datum graph, counts, semantic/evidence hash sets, materialized root event, and candidate subtree at commit.",
      "PostgreSQL test 04 copies a byte-valid legitimate root, rolls back its children, inserts only the root, and proves deferred commit rejection; test 05 proves an extra direct-SQL child is rejected when constraints are forced immediate.",
      "The expanded disposable PostgreSQL matrix passed 9 out of 9 in t081_blockers_l, which was dropped; paprnav_db was not targeted.",
      "Independent targeted closure review adversarial-implementation-ia002-ia005-closure.md verified all residual semantic ownership/hash and listed-designation counterexamples and returned IA-002 PASS."
    ]
  },
  {
    "id": "T081-V4-S3A-IA-003",
    "stage": "implementation",
    "reviewer": "/root/v4_s3a_impl_adversary",
    "severity": "blocker",
    "status": "closed",
    "invariant": "Supersession stale state is proposal-bound, uniquely resolved, evidence-backed, and names the exact same-projection dependency cause.",
    "summary": "Stale folding accepts the first predecessor relationship without successor-AD equality or unique resolution and emits events with no dependency cause.",
    "evidence": ["backend/app/services/ad_v4_applicability.py:613 treats a matching predecessor relationship as stale", "backend/app/services/ad_v4_applicability.py:661 stores causing_dependency_id=None", "Materialized dependencies remain unresolved"],
    "impact": "An unrelated candidate relationship can stale a projection and leave an incomplete audit chain.",
    "requiredClosure": "Resolve dependencies under successor canonical AD equality and unique predecessor rules, require the exact dependency FK on stale events, and test positive and negative cases.",
    "closureEvidence": [
      "Application and deferred database verification require exact successor/candidate AD equality and exactly one predecessor projection; unknown, mismatched, missing, and ambiguous relations remain non-resolved without cross-projection effects.",
      "Resolved outgoing dependencies create deterministic target-local incoming rows; stale events carry the exact same-projection dependency through a composite FK, canonical cause envelope, deterministic hash, and causal partial uniqueness key.",
      "The application, projection BEFORE INSERT trigger, and deferred full-graph validator all invoke the same PostgreSQL helper, which locks sorted distinct canonical/predecessor/successor AD numbers and prevents application or direct-SQL phantom predecessor write-skew.",
      "PostgreSQL tests 09-13 cover exact, mismatch, ambiguity, concurrent application orderings, forged cross-projection causes, and a raw projection INSERT blocked by the database-native lock; the clean matrix passed 14/14.",
      "Independent targeted closure review adversarial-implementation-ia003-closure.md verified the original race and direct-SQL variant are closed and returned IA-003 PASS."
    ]
  },
  {
    "id": "T081-V4-S3A-IA-004",
    "stage": "implementation",
    "reviewer": "/root/v4_s3a_impl_adversary",
    "severity": "high",
    "status": "closed",
    "invariant": "Audit GET/list/reconstruction paths are detection-only and never write repair events.",
    "summary": "Detail and list GET invoke mutating stale repair and commit events.",
    "evidence": ["backend/app/services/ad_v4_applicability.py:596 invokes repair from projection_state", "backend/app/api/routes/ads.py:493 and :544 commit after GET serialization"],
    "impact": "Viewing audit state becomes an alternate writer with unexpected locks and audit mutations.",
    "requiredClosure": "Make GETs side-effect-free, keep repair inside authorized materialization POST, and test unchanged table/event counts for every GET.",
    "closureEvidence": [
      "backend/app/services/ad_v4_applicability.py separates non-mutating projection_state detection from repair and calls repair only within materialize_applicability after authorization and database gates, on both normal and idempotent POST paths.",
      "backend/app/api/routes/ads.py detail and list GET paths no longer commit; reconstruction was already read-only.",
      "backend/tests/test_ad_v4_applicability.py snapshots the projection-event count across detail, reconstruction, and list GET; the focused suite passed 40 out of 40.",
      "Independent targeted closure review adversarial-implementation-ia004-closure.md by /root/v4_s3a_impl_adversary found no alternate repair caller and passed IA-004 with no residual finding."
    ]
  },
  {
    "id": "T081-V4-S3A-IA-005",
    "stage": "implementation",
    "reviewer": "/root/v4_s3a_impl_adversary",
    "severity": "high",
    "status": "closed",
    "invariant": "The shared correction foundation exactly reconstructs and verifies canonical corrections, official-document identities, ordered refs, and evidence at commit and read.",
    "summary": "Correction rows are inserted without exact reconstruction, deferred completeness/identity checks, or verified-read validation.",
    "evidence": ["_materialize_corrections has no corresponding exact reconstruction verifier", "Migration 0027 does not enforce expected child counts or official-document identity", "Calibration tests check selected counts/values rather than an independent correction round trip"],
    "impact": "A projection can report verified while its cross-slice correction foundation is incomplete or disconnected.",
    "requiredClosure": "Implement correction reconstruction and fail-closed verification, deferred completeness/identity enforcement, and direct-SQL negatives plus exact 2008 round trip.",
    "closureEvidence": [
      "Application verified reads now reconstruct each correction from ordered roots/refs/evidence and verify canonical equality, document identities, generation, owners, 3A bindings, and candidate evidence bindings.",
      "Migration 0027 deferred completeness validates exact correction count/order/content/hash, official-document identity hashes, exact refs/evidence, generation, and owner-slice binding cardinality; correction rows cannot commit without a projection.",
      "The 2008 real-evidence calibration round trip passes and deliberately removing one correction evidence link fails closed; the disposable PostgreSQL matrix passed 9 out of 9.",
      "Independent targeted closure review adversarial-implementation-ia002-ia005-closure.md verified binding targets, document and row hashes, zero-based contiguous ordinals, append ordering, and SQL-null behavior and returned IA-005 PASS."
    ]
  }
]

```
### `.ai/review-runs/T081-V4-SCHEMA-SLICE-3A/implementation-slice-3a.md`

size=5336; sha256=8b0e9c5f64ea267383c888046965fc6ea4240a5d4bb4d97ee28c516f30d83208; truncated=false

```text
# Implementation evidence: T081-V4-SCHEMA-SLICE-3A

Date: 2026-09-07  
Builder: `/root` (continuing the preserved partial implementation)  
Base: `28f6be0 feat: add immutable AD V4 candidate foundation`

## Implemented scope

- Added validator-2/canonicalizer-2 dispatch while preserving validator-1
  verification and storage semantics.
- Added default-off application and database capability gates for validator-2
  writes and Slice-3A materialization/read routes.
- Added migration 0027 with validator-version propagation, additive immutable
  applicability/correction/dependency/event tables, integrity validation,
  feature-gate administration, and downgrade refusal for validator-2 or Slice-3A
  state.
- Added candidate-only applicability materialization, exact relational subtree
  reconstruction, shared correction foundations, explicit unreviewed identity
  mappings, stale-state detection, and inline authorized repair.
- Added bounded platform-admin materialize/list/detail/reconstruction API
  surfaces using the exact acting membership.
- Added unit, API, five-packet calibration, and disposable PostgreSQL coverage.

No released/customer reader, aircraft matching, compliance, due-state, V3
mutation, provider/CLI/cron/background writer, publication, or reviewer UI was
added.

## Verification performed

- Focused applicability suite after interruption: **10 passed out of 10**.
- Candidate/API/applicability suite:
  `test_ad_v4_candidates.py`, `test_ad_v4_api.py`, and
  `test_ad_v4_applicability.py`: **40 passed out of 40** in 5.05 seconds.
- Existing ingestion/matching/recurrence/full-readiness isolation suite:
  **81 passed out of 81** in 16.80 seconds.
- Validator-2 five-packet schema and canonical determinism: **5 passed out of
  5**, run as bounded one-packet invocations.
- Validator-2 five-packet real-evidence materialization and exact round trip:
  **5 passed out of 5**, run as bounded one-packet invocations.
- Disposable PostgreSQL matrix after explicit upgrade to 0027: **4 passed out
  of 4** in 3.08 seconds. It covered empty and v1-only downgrade/re-upgrade,
  v2 downgrade refusal with head preservation, projection integrity and
  immutability, occupied downgrade refusal, concurrent same-key retry, and
  gate disable. Database `t081_v4_s3a_20260907b` was dropped by the cleanup
  trap; `paprnav_db` was not targeted.
- Python compilation of both changed services, migration 0027, and the three
  new Slice-3A test files: **6 passed out of 6**.
- `git diff --check`: **1 passed out of 1**.
- Application-reader search: Slice-3A model/service references occur only in
  `app/services/ad_v4_applicability.py`, bounded admin routes in
  `app/api/routes/ads.py`, model declarations, and migration code: **1 passed
  out of 1** scope checks; no released/customer consumer was found.

Two preexisting Starlette deprecation-warning categories remain: the TestClient
httpx compatibility warning and the renamed HTTP 413 constant. Neither is a
test failure or introduced safety behavior.

## Diagnostic correction

The first disposable PostgreSQL command created a fresh blank database and ran
the matrix without first applying migrations. Test 00 correctly rejected a
downgrade from an unversioned database, and the remaining tests lacked the 0027
gate function. This was a harness precondition error, not credited as product
verification. Its cleanup trap dropped `t081_v4_s3a_20260907`. The corrected
run explicitly upgraded a separately named database to 0027 before pytest and
passed all 4 cases.

Two initial host-suite commands referenced nonexistent filenames
`test_ads_api.py`, `test_ad_v3_service.py`, and `test_ad_v3_api.py`; pytest
collected no tests. The corrected 40-test and 81-test suites above are the
credited results.

## Deviations and unverified gates

- `IA-004` was fixed after the initial FAIL: audit GET/list/reconstruction are
  now detection-only, and deterministic repair is invoked only from the
  authorized, gated materialization POST on normal and idempotent paths. The
  focused applicability suite passed **10 out of 10**, the combined focused
  suite passed **40 out of 40**, and independent reviewer
  `/root/v4_s3a_impl_adversary` returned a targeted PASS recorded in
  `adversarial-implementation-ia004-closure.md`.
- `IA-002`, `IA-003`, and `IA-005` are closed after independent targeted
  verification. Migration 0027 performs deferred exact graph, correction, and
  supersession validation; verified reads independently reconstruct correction
  and dependency facts. PostgreSQL supersession coverage includes exact,
  mismatched, ambiguous, forged-cause, application-concurrent, and raw/direct
  lock cases.
- The final clean disposable PostgreSQL matrix passed **14 out of 14**. The
  focused host suite passed **36 out of 36**, and the broader relevant
  candidate/API/applicability/calibration suite passed **50 out of 50**.
- `IA-001` remains open: persistence is still the generic semantic-node/datum
  representation rather than the approved typed owner tables. This is a
  material implementation deviation and blocks commit/completion.
- Current implementation has not yet passed independent Codex implementation
  review.
- Closure review and review-run validation have not yet occurred.
- The working tree is not staged and no Slice-3A commit exists.

```
### `.ai/review-runs/T081-V4-SCHEMA-SLICE-3A/latest`

size=100452; sha256=5421f3b3dc6f6e061d55cc27d040d1b1090a1c21cd5edd50dfcb5bfb1a5b2d96; truncated=false

```text
2026-09-06T23:57:08.685Z [DEBUG] MDM settings load completed in 0ms
2026-09-06T23:57:08.700Z [DEBUG] Broken symlink or missing file encountered for settings.json at path: /Library/Application Support/ClaudeCode/managed-settings.json
2026-09-06T23:57:08.700Z [DEBUG] Broken symlink or missing file encountered for settings.json at path: /Users/hostiletakeover/Projects/paprnav/.claude/settings.json
2026-09-06T23:57:08.700Z [DEBUG] Broken symlink or missing file encountered for settings.json at path: /Users/hostiletakeover/Projects/paprnav/.claude/settings.local.json
2026-09-06T23:57:08.701Z [DEBUG] CA certs: Config fallback - globalEnv keys: , settingsEnv keys: none
2026-09-06T23:57:08.746Z [DEBUG] [init] configureGlobalMTLS starting
2026-09-06T23:57:08.746Z [DEBUG] [init] configureGlobalMTLS complete
2026-09-06T23:57:08.746Z [DEBUG] [init] configureGlobalAgents starting
2026-09-06T23:57:08.746Z [DEBUG] CA certs: stores=bundled,system, extraCertsPath=undefined
2026-09-06T23:57:08.746Z [DEBUG] CA certs: Loaded 121 bundled root certificates
2026-09-06T23:57:08.779Z [DEBUG] CA certs: Loaded 4 system CA certificates
2026-09-06T23:57:08.779Z [DEBUG] mTLS: Creating HTTPS agent with custom certificates
2026-09-06T23:57:08.779Z [DEBUG] [init] configureGlobalAgents complete
2026-09-06T23:57:08.781Z [DEBUG] Git remote URL: null
2026-09-06T23:57:08.781Z [DEBUG] No git remote URL found
2026-09-06T23:57:08.782Z [DEBUG] Error log sink initialized
2026-09-06T23:57:08.783Z [DEBUG] policyHelper: no helper configuration present at helper-pass time (remote managed settings eligible, no payload in cache); a payload landing later arms one only through a fetch cycle after preAction
2026-09-06T23:57:08.813Z [DEBUG] Loaded 1 installed plugins from /Users/hostiletakeover/.claude/plugins/installed_plugins.json
2026-09-06T23:57:08.816Z [DEBUG] Found 1 plugins (1 enabled, 0 disabled)
2026-09-06T23:57:08.816Z [DEBUG] [mcp-policy-cold-start] waiting on remote managed-settings load
2026-09-06T23:57:09.030Z [DEBUG] Remote settings: No settings found (404)
2026-09-06T23:57:09.032Z [DEBUG] Broken symlink or missing file encountered for settings.json at path: /Library/Application Support/ClaudeCode/managed-settings.json
2026-09-06T23:57:09.032Z [DEBUG] Broken symlink or missing file encountered for settings.json at path: /Users/hostiletakeover/Projects/paprnav/.claude/settings.json
2026-09-06T23:57:09.032Z [DEBUG] Broken symlink or missing file encountered for settings.json at path: /Users/hostiletakeover/Projects/paprnav/.claude/settings.local.json
2026-09-06T23:57:09.032Z [DEBUG] Cleared proxy agent cache
2026-09-06T23:57:09.032Z [DEBUG] Cleared CA certificates cache
2026-09-06T23:57:09.032Z [DEBUG] Cleared mTLS configuration cache
2026-09-06T23:57:09.032Z [DEBUG] CA certs: stores=bundled,system, extraCertsPath=undefined
2026-09-06T23:57:09.032Z [DEBUG] CA certs: Loaded 121 bundled root certificates
2026-09-06T23:57:09.032Z [DEBUG] CA certs: Loaded 4 system CA certificates
2026-09-06T23:57:09.032Z [DEBUG] mTLS: Creating HTTPS agent with custom certificates
2026-09-06T23:57:09.033Z [DEBUG] Remote settings: Saved to /Users/hostiletakeover/.claude/remote-settings.json
2026-09-06T23:57:09.033Z [DEBUG] Remote settings: Saved empty sentinel (404 response)
2026-09-06T23:57:09.033Z [DEBUG] Programmatic settings change notification for policySettings
2026-09-06T23:57:09.033Z [DEBUG] Broken symlink or missing file encountered for settings.json at path: /Library/Application Support/ClaudeCode/managed-settings.json
2026-09-06T23:57:09.034Z [DEBUG] [Claude in Chrome] Disabled: OAuth token has no scope accepted by /api/oauth/validate (needs user:profile, user:office, or user:ccr_inference; env-var and setup-token sessions default to user:inference only)
2026-09-06T23:57:09.034Z [DEBUG] Broken symlink or missing file encountered for settings.json at path: /Users/hostiletakeover/Projects/paprnav/.claude/settings.json
2026-09-06T23:57:09.034Z [DEBUG] Broken symlink or missing file encountered for settings.json at path: /Users/hostiletakeover/Projects/paprnav/.claude/settings.local.json
2026-09-06T23:57:09.052Z [DEBUG] [ToolSearch:optimistic] mode=tst, ENABLE_TOOL_SEARCH=undefined, result=true
2026-09-06T23:57:09.052Z [DEBUG] [STARTUP] Loading MCP configs...
2026-09-06T23:57:09.054Z [DEBUG] [STARTUP] Running setup()...
2026-09-06T23:57:09.056Z [DEBUG] Policy limits: Fetched successfully
2026-09-06T23:57:09.057Z [DEBUG] Policy limits: Saved to /Users/hostiletakeover/.claude/policy-limits.json
2026-09-06T23:57:09.057Z [DEBUG] Policy limits: Applied new restrictions successfully
2026-09-06T23:57:09.058Z [DEBUG] Total plugin workflows loaded: 0
2026-09-06T23:57:09.058Z [DEBUG] Broken symlink or missing file encountered for settings.json at path: /Library/Application Support/ClaudeCode/managed-settings.json
2026-09-06T23:57:09.059Z [DEBUG] Broken symlink or missing file encountered for settings.json at path: /Users/hostiletakeover/Projects/paprnav/.claude/settings.json
2026-09-06T23:57:09.059Z [DEBUG] Broken symlink or missing file encountered for settings.json at path: /Users/hostiletakeover/Projects/paprnav/.claude/settings.local.json
2026-09-06T23:57:09.060Z [DEBUG] Error log sink initialized
2026-09-06T23:57:09.061Z [DEBUG] Loading skills from: managed=/Library/Application Support/ClaudeCode/.claude/skills, user=/Users/hostiletakeover/.claude/skills, project=[]
2026-09-06T23:57:09.061Z [DEBUG] [reduced mode] Skipping skill dir discovery
2026-09-06T23:57:09.061Z [DEBUG] [STARTUP] setup() completed in 7ms
2026-09-06T23:57:09.061Z [DEBUG] Cleared mTLS configuration cache
2026-09-06T23:57:09.061Z [DEBUG] Cleared proxy agent cache
2026-09-06T23:57:09.061Z [DEBUG] mTLS: Creating HTTPS agent with custom certificates
2026-09-06T23:57:09.062Z [DEBUG] [STARTUP] Loading commands and agents...
2026-09-06T23:57:09.067Z [DEBUG] getSkills returning: 0 skill dir commands, 0 plugin skills, 41 bundled skills, 0 builtin plugin skills
2026-09-06T23:57:09.081Z [DEBUG] [STARTUP] Commands and agents loaded in 19ms
2026-09-06T23:57:09.082Z [DEBUG] Skipping startup prefetches, last ran 1788739029s ago
2026-09-06T23:57:09.082Z [DEBUG] [STARTUP] MCP configs resolved in 1ms (awaited at +30ms)
2026-09-06T23:57:09.083Z [DEBUG] Cleared mTLS configuration cache
2026-09-06T23:57:09.083Z [DEBUG] Cleared proxy agent cache
2026-09-06T23:57:09.083Z [DEBUG] mTLS: Creating HTTPS agent with custom certificates
2026-09-06T23:57:09.083Z [DEBUG] [3P telemetry] Waiting for remote managed settings fetch before telemetry init
2026-09-06T23:57:09.083Z [DEBUG] Fast mode unavailable: Fast mode is not available in the Agent SDK
2026-09-06T23:57:09.084Z [DEBUG] [MCP] --mcp-config servers running fully async (nonblocking)
2026-09-06T23:57:09.084Z [DEBUG] [MCP] claude.ai connectors running fully async (nonblocking)
2026-09-06T23:57:09.084Z [DEBUG] [3P telemetry] Remote managed settings fetch settled, initializing telemetry
2026-09-06T23:57:09.084Z [DEBUG] Cleared mTLS configuration cache
2026-09-06T23:57:09.084Z [DEBUG] Cleared proxy agent cache
2026-09-06T23:57:09.084Z [DEBUG] mTLS: Creating HTTPS agent with custom certificates
2026-09-06T23:57:09.090Z [DEBUG] Settings changed from policySettings, updating app state
2026-09-06T23:57:09.101Z [DEBUG] Broken symlink or missing file encountered for settings.json at path: /Library/Application Support/ClaudeCode/managed-settings.json
2026-09-06T23:57:09.102Z [DEBUG] Broken symlink or missing file encountered for settings.json at path: /Users/hostiletakeover/Projects/paprnav/.claude/settings.json
2026-09-06T23:57:09.102Z [DEBUG] Broken symlink or missing file encountered for settings.json at path: /Users/hostiletakeover/Projects/paprnav/.claude/settings.local.json
2026-09-06T23:57:09.103Z [DEBUG] Replacing all allow rules for destination 'userSettings' with 0 rule(s): []
2026-09-06T23:57:09.103Z [DEBUG] Replacing all deny rules for destination 'userSettings' with 0 rule(s): []
2026-09-06T23:57:09.103Z [DEBUG] Replacing all ask rules for destination 'userSettings' with 0 rule(s): []
2026-09-06T23:57:09.103Z [DEBUG] Replacing all allow rules for destination 'projectSettings' with 0 rule(s): []
2026-09-06T23:57:09.103Z [DEBUG] Replacing all deny rules for destination 'projectSettings' with 0 rule(s): []
2026-09-06T23:57:09.103Z [DEBUG] Replacing all ask rules for destination 'projectSettings' with 0 rule(s): []
2026-09-06T23:57:09.103Z [DEBUG] Replacing all allow rules for destination 'localSettings' with 0 rule(s): []
2026-09-06T23:57:09.103Z [DEBUG] Replacing all deny rules for destination 'localSettings' with 0 rule(s): []
2026-09-06T23:57:09.103Z [DEBUG] Replacing all ask rules for destination 'localSettings' with 0 rule(s): []
2026-09-06T23:57:09.103Z [DEBUG] Replacing all allow rules for destination 'flagSettings' with 0 rule(s): []
2026-09-06T23:57:09.103Z [DEBUG] Replacing all deny rules for destination 'flagSettings' with 0 rule(s): []
2026-09-06T23:57:09.103Z [DEBUG] Replacing all ask rules for destination 'flagSettings' with 0 rule(s): []
2026-09-06T23:57:09.103Z [DEBUG] Replacing all allow rules for destination 'policySettings' with 0 rule(s): []
2026-09-06T23:57:09.103Z [DEBUG] Replacing all deny rules for destination 'policySettings' with 0 rule(s): []
2026-09-06T23:57:09.103Z [DEBUG] Replacing all ask rules for destination 'policySettings' with 0 rule(s): []
2026-09-06T23:57:09.110Z [DEBUG] [ScheduledTasks] scheduler start() — enabled=false, hasTasks=false
2026-09-06T23:57:09.111Z [DEBUG] session.start: raised (surface none, not interactive)
2026-09-06T23:57:09.112Z [DEBUG] [Perfetto] initializePerfettoTracing called, env value: undefined
2026-09-06T23:57:09.112Z [DEBUG] [3P telemetry] isTelemetryEnabled=false (CLAUDE_CODE_ENABLE_TELEMETRY=undefined)
2026-09-06T23:57:09.116Z [WARN] [3P telemetry] Event dropped (no event logger initialized): plugin_loaded
2026-09-06T23:57:09.117Z [DEBUG] Git remote URL: https://github.com/Trent-pivotallift/paprnav.git
2026-09-06T23:57:09.117Z [DEBUG] Parsed repository: github.com/Trent-pivotallift/paprnav from URL: https://github.com/Trent-pivotallift/paprnav.git
2026-09-06T23:57:09.120Z [DEBUG] Total plugin workflows loaded: 0
2026-09-06T23:57:09.120Z [DEBUG] getSkills returning: 0 skill dir commands, 0 plugin skills, 41 bundled skills, 0 builtin plugin skills
2026-09-06T23:57:09.121Z [DEBUG] [sessionRegistry] sweep permitted (domain darwin)
2026-09-06T23:57:09.122Z [DEBUG] Fast mode unavailable: Fast mode is not available in the Agent SDK
2026-09-06T23:57:09.122Z [DEBUG] [session-notices] advertise=false mode=plan flag=true(disk) pollChannel=false remote=false remoteEnv=false nonInteractive=true
2026-09-06T23:57:09.124Z [DEBUG] [engine] turn 1 start
2026-09-06T23:57:09.127Z [DEBUG] autocompact: tokens=[REDACTED] level=ok effectiveWindow=980000
2026-09-06T23:57:09.150Z [DEBUG] [auto-mode] verifyAutoModeGateAccess: enabledState=enabled disabledBySettings=false model=claude-sonnet-5 modelSupported=true disableFastModeBreakerFires=false carouselAvailable=true canEnterAuto=true
2026-09-06T23:57:09.151Z [DEBUG] Tool search disabled: ToolSearchTool is not available (may have been disallowed via disallowedTools).
2026-09-06T23:57:09.152Z [DEBUG] attribution header x-anthropic-billing-header: cc_version=2.1.263.992; cc_entrypoint=sdk-cli; cch=00000; cc_prompt_id=51ed5dfe-6e13-480f-82d9-c21bda316023;
2026-09-06T23:57:09.153Z [DEBUG] Fast mode unavailable: Fast mode is not available in the Agent SDK
2026-09-06T23:57:09.153Z [DEBUG] Fast mode unavailable: Fast mode is not available in the Agent SDK
2026-09-06T23:57:09.155Z [DEBUG] Fast mode unavailable: Fast mode is not available in the Agent SDK
2026-09-06T23:57:09.156Z [DEBUG] [API:timing] dispatching to firstParty model=claude-sonnet-5
2026-09-06T23:57:09.156Z [DEBUG] [API REQUEST] /v1/messages x-client-request-id=2cb78a27-eb78-44cc-8bb6-d6cfaab6b98f source=sdk
2026-09-06T23:57:09.159Z [DEBUG] Preserving file permissions: 100600
2026-09-06T23:57:09.159Z [DEBUG] Writing to temp file: /Users/hostiletakeover/.claude.json.tmp.48303.24dee73d7fe9
2026-09-06T23:57:09.160Z [DEBUG] Applied original permissions to temp file
2026-09-06T23:57:09.160Z [DEBUG] Temp file written successfully, size: 62999 bytes
2026-09-06T23:57:09.160Z [DEBUG] Renaming /Users/hostiletakeover/.claude.json.tmp.48303.24dee73d7fe9 to /Users/hostiletakeover/.claude.json
2026-09-06T23:57:09.161Z [DEBUG] File /Users/hostiletakeover/.claude.json written atomically
2026-09-06T23:57:09.863Z [DEBUG] Stream started - received first chunk
2026-09-06T23:57:09.863Z [DEBUG] [API:timing] first byte after 708ms
2026-09-06T23:57:10.887Z [INFO] [Stall] tool_dispatch_start tool=Bash toolUseId=toolu_01CF6ytFnYWg4kYU1xg82akD permissionDecisionMs=3
2026-09-06T23:57:10.890Z [DEBUG] Creating shell snapshot for bash (/bin/bash)
2026-09-06T23:57:10.890Z [DEBUG] Looking for shell config file: /Users/hostiletakeover/.bashrc
2026-09-06T23:57:10.894Z [DEBUG] Snapshots directory: /Users/hostiletakeover/.claude/shell-snapshots
2026-09-06T23:57:10.895Z [DEBUG] Spawn-env probe captured 58 keys
2026-09-06T23:57:10.895Z [DEBUG] Creating snapshot at: /Users/hostiletakeover/.claude/shell-snapshots/snapshot-bash-1788739030894-bef4ww.sh
2026-09-06T23:57:10.895Z [DEBUG] Execution timeout: 10000ms
2026-09-06T23:57:11.716Z [DEBUG] Shell snapshot created successfully (181526 bytes)
2026-09-06T23:57:11.718Z [DEBUG] No session environment scripts found
2026-09-06T23:57:11.718Z [DEBUG] Spawning shell without login (-l flag skipped)
2026-09-06T23:57:11.751Z [INFO] [Stall] tool_dispatch_end tool=Bash toolUseId=toolu_01CF6ytFnYWg4kYU1xg82akD outcome=ok durationMs=864
2026-09-06T23:57:11.754Z [DEBUG] autocompact: tokens=[REDACTED] level=ok effectiveWindow=980000
2026-09-06T23:57:11.754Z [DEBUG] Tool search disabled: ToolSearchTool is not available (may have been disallowed via disallowedTools).
2026-09-06T23:57:11.755Z [DEBUG] attribution header x-anthropic-billing-header: cc_version=2.1.263.992; cc_entrypoint=sdk-cli; cch=00000; cc_prev_req=req_011Ceo6FZyg7uhx35hgRnzt5; cc_prompt_id=51ed5dfe-6e13-480f-82d9-c21bda316023;
2026-09-06T23:57:11.755Z [DEBUG] Fast mode unavailable: Fast mode is not available in the Agent SDK
2026-09-06T23:57:11.756Z [DEBUG] Fast mode unavailable: Fast mode is not available in the Agent SDK
2026-09-06T23:57:11.756Z [DEBUG] Fast mode unavailable: Fast mode is not available in the Agent SDK
2026-09-06T23:57:11.756Z [DEBUG] [API:timing] dispatching to firstParty model=claude-sonnet-5
2026-09-06T23:57:11.757Z [DEBUG] [API REQUEST] /v1/messages x-client-request-id=ea0f58fc-b56c-4c65-96b6-654f358a0ff0 source=sdk
2026-09-06T23:57:12.375Z [DEBUG] Stream started - received first chunk
2026-09-06T23:57:12.375Z [DEBUG] [API:timing] first byte after 619ms
2026-09-06T23:57:13.277Z [INFO] [Stall] tool_dispatch_start tool=Read toolUseId=toolu_01SBRmmDLMDkDXZm93WW1Q5U permissionDecisionMs=3
2026-09-06T23:57:13.280Z [WARN] [Stall] tool_dispatch_end tool=Read toolUseId=toolu_01SBRmmDLMDkDXZm93WW1Q5U outcome=error durationMs=3
2026-09-06T23:57:13.280Z [DEBUG] Read tool error (3ms): File content (940.5KB) exceeds maximum allowed size (256KB). Use offset and limit parameters to read specific portions of the file, or search for specific content instead of reading the whole file.
2026-09-06T23:57:13.290Z [DEBUG] autocompact: tokens=[REDACTED] level=ok effectiveWindow=980000
2026-09-06T23:57:13.291Z [DEBUG] Tool search disabled: ToolSearchTool is not available (may have been disallowed via disallowedTools).
2026-09-06T23:57:13.291Z [DEBUG] attribution header x-anthropic-billing-header: cc_version=2.1.263.992; cc_entrypoint=sdk-cli; cch=00000; cc_prev_req=req_011Ceo6Fko4EKgcUTqftLHBy; cc_prompt_id=51ed5dfe-6e13-480f-82d9-c21bda316023;
2026-09-06T23:57:13.291Z [DEBUG] Fast mode unavailable: Fast mode is not available in the Agent SDK
2026-09-06T23:57:13.291Z [DEBUG] Fast mode unavailable: Fast mode is not available in the Agent SDK
2026-09-06T23:57:13.292Z [DEBUG] Fast mode unavailable: Fast mode is not available in the Agent SDK
2026-09-06T23:57:13.292Z [DEBUG] [API:timing] dispatching to firstParty model=claude-sonnet-5
2026-09-06T23:57:13.292Z [DEBUG] [API REQUEST] /v1/messages x-client-request-id=0f9731d5-b8d6-4ad3-95a9-799dc8f6f675 source=sdk
2026-09-06T23:57:14.062Z [DEBUG] Stream started - received first chunk
2026-09-06T23:57:14.062Z [DEBUG] [API:timing] first byte after 770ms
2026-09-06T23:57:14.555Z [INFO] [Stall] tool_dispatch_start tool=Bash toolUseId=toolu_01R9v2vM4CR97eRDkaw9rqFK permissionDecisionMs=2
2026-09-06T23:57:14.556Z [DEBUG] Spawning shell without login (-l flag skipped)
2026-09-06T23:57:14.587Z [INFO] [Stall] tool_dispatch_end tool=Bash toolUseId=toolu_01R9v2vM4CR97eRDkaw9rqFK outcome=ok durationMs=32
2026-09-06T23:57:14.589Z [DEBUG] autocompact: tokens=[REDACTED] level=ok effectiveWindow=980000
2026-09-06T23:57:14.589Z [DEBUG] Tool search disabled: ToolSearchTool is not available (may have been disallowed via disallowedTools).
2026-09-06T23:57:14.590Z [DEBUG] attribution header x-anthropic-billing-header: cc_version=2.1.263.992; cc_entrypoint=sdk-cli; cch=00000; cc_prev_req=req_011Ceo6FsMwquSeS4Z8rV2h8; cc_prompt_id=51ed5dfe-6e13-480f-82d9-c21bda316023;
2026-09-06T23:57:14.590Z [DEBUG] Fast mode unavailable: Fast mode is not available in the Agent SDK
2026-09-06T23:57:14.590Z [DEBUG] Fast mode unavailable: Fast mode is not available in the Agent SDK
2026-09-06T23:57:14.590Z [DEBUG] Fast mode unavailable: Fast mode is not available in the Agent SDK
2026-09-06T23:57:14.591Z [DEBUG] [API:timing] dispatching to firstParty model=claude-sonnet-5
2026-09-06T23:57:14.591Z [DEBUG] [API REQUEST] /v1/messages x-client-request-id=3102f1ed-e9b7-4c9a-bfea-5c18e3dff05c source=sdk
2026-09-06T23:57:15.442Z [DEBUG] Stream started - received first chunk
2026-09-06T23:57:15.442Z [DEBUG] [API:timing] first byte after 851ms
2026-09-06T23:57:16.243Z [INFO] [Stall] tool_dispatch_start tool=Read toolUseId=toolu_019NfT1EosFgeo58pVHgHYnB permissionDecisionMs=2
2026-09-06T23:57:16.249Z [INFO] [Stall] tool_dispatch_end tool=Read toolUseId=toolu_019NfT1EosFgeo58pVHgHYnB outcome=ok durationMs=5
2026-09-06T23:57:16.251Z [DEBUG] autocompact: tokens=[REDACTED] level=ok effectiveWindow=980000
2026-09-06T23:57:16.252Z [DEBUG] Tool search disabled: ToolSearchTool is not available (may have been disallowed via disallowedTools).
2026-09-06T23:57:16.252Z [DEBUG] attribution header x-anthropic-billing-header: cc_version=2.1.263.992; cc_entrypoint=sdk-cli; cch=00000; cc_prev_req=req_011Ceo6FxuKTJAo5hUTHH9Yz; cc_prompt_id=51ed5dfe-6e13-480f-82d9-c21bda316023;
2026-09-06T23:57:16.252Z [DEBUG] Fast mode unavailable: Fast mode is not available in the Agent SDK
2026-09-06T23:57:16.252Z [DEBUG] Fast mode unavailable: Fast mode is not available in the Agent SDK
2026-09-06T23:57:16.253Z [DEBUG] Fast mode unavailable: Fast mode is not available in the Agent SDK
2026-09-06T23:57:16.253Z [DEBUG] [API:timing] dispatching to firstParty model=claude-sonnet-5
2026-09-06T23:57:16.253Z [DEBUG] [API REQUEST] /v1/messages x-client-request-id=94fef52c-f8c3-47e8-8702-312c5bfe5b23 source=sdk
2026-09-06T23:57:17.121Z [DEBUG] Stream started - received first chunk
2026-09-06T23:57:17.121Z [DEBUG] [API:timing] first byte after 869ms
2026-09-06T23:57:19.058Z [INFO] [Stall] tool_dispatch_start tool=Read toolUseId=toolu_016DwAZvy3p1MJrq4koKtYV6 permissionDecisionMs=2
2026-09-06T23:57:19.061Z [INFO] [Stall] tool_dispatch_end tool=Read toolUseId=toolu_016DwAZvy3p1MJrq4koKtYV6 outcome=ok durationMs=3
2026-09-06T23:57:19.067Z [DEBUG] autocompact: tokens=[REDACTED] level=ok effectiveWindow=980000
2026-09-06T23:57:19.067Z [DEBUG] Tool search disabled: ToolSearchTool is not available (may have been disallowed via disallowedTools).
2026-09-06T23:57:19.068Z [DEBUG] attribution header x-anthropic-billing-header: cc_version=2.1.263.992; cc_entrypoint=sdk-cli; cch=00000; cc_prev_req=req_011Ceo6G65v72agwg3kNVbsz; cc_prompt_id=51ed5dfe-6e13-480f-82d9-c21bda316023;
2026-09-06T23:57:19.068Z [DEBUG] Fast mode unavailable: Fast mode is not available in the Agent SDK
2026-09-06T23:57:19.068Z [DEBUG] Fast mode unavailable: Fast mode is not available in the Agent SDK
2026-09-06T23:57:19.069Z [DEBUG] Fast mode unavailable: Fast mode is not available in the Agent SDK
2026-09-06T23:57:19.069Z [DEBUG] [API:timing] dispatching to firstParty model=claude-sonnet-5
2026-09-06T23:57:19.069Z [DEBUG] [API REQUEST] /v1/messages x-client-request-id=5a4a1625-4c59-4ee6-be3a-a9de92fad990 source=sdk
2026-09-06T23:57:19.863Z [DEBUG] Stream started - received first chunk
2026-09-06T23:57:19.863Z [DEBUG] [API:timing] first byte after 794ms
2026-09-06T23:57:22.030Z [INFO] [Stall] tool_dispatch_start tool=Bash toolUseId=toolu_01GbGxYeKky7Twd2TGW7xYg4 permissionDecisionMs=5
2026-09-06T23:57:22.033Z [DEBUG] Spawning shell without login (-l flag skipped)
2026-09-06T23:57:22.225Z [INFO] [Stall] tool_dispatch_end tool=Bash toolUseId=toolu_01GbGxYeKky7Twd2TGW7xYg4 outcome=ok durationMs=195
2026-09-06T23:57:22.227Z [DEBUG] autocompact: tokens=[REDACTED] level=ok effectiveWindow=980000
2026-09-06T23:57:22.228Z [DEBUG] Tool search disabled: ToolSearchTool is not available (may have been disallowed via disallowedTools).
2026-09-06T23:57:22.228Z [DEBUG] attribution header x-anthropic-billing-header: cc_version=2.1.263.992; cc_entrypoint=sdk-cli; cch=00000; cc_prev_req=req_011Ceo6GJ6UcrXSTxvKuUAts; cc_prompt_id=51ed5dfe-6e13-480f-82d9-c21bda316023;
2026-09-06T23:57:22.228Z [DEBUG] Fast mode unavailable: Fast mode is not available in the Agent SDK
2026-09-06T23:57:22.229Z [DEBUG] Fast mode unavailable: Fast mode is not available in the Agent SDK
2026-09-06T23:57:22.229Z [DEBUG] Fast mode unavailable: Fast mode is not available in the Agent SDK
2026-09-06T23:57:22.229Z [DEBUG] [API:timing] dispatching to firstParty model=claude-sonnet-5
2026-09-06T23:57:22.230Z [DEBUG] [API REQUEST] /v1/messages x-client-request-id=109cb9d6-a4b3-4628-a0e6-aac559a85fcf source=sdk
2026-09-06T23:57:22.965Z [DEBUG] Stream started - received first chunk
2026-09-06T23:57:22.965Z [DEBUG] [API:timing] first byte after 736ms
2026-09-06T23:57:25.298Z [INFO] [Stall] tool_dispatch_start tool=Bash toolUseId=toolu_01TJnF7iNFoDM8QdZiCPC6GF permissionDecisionMs=4
2026-09-06T23:57:25.300Z [DEBUG] Spawning shell without login (-l flag skipped)
2026-09-06T23:57:25.354Z [INFO] [Stall] tool_dispatch_end tool=Bash toolUseId=toolu_01TJnF7iNFoDM8QdZiCPC6GF outcome=ok durationMs=56
2026-09-06T23:57:25.356Z [DEBUG] autocompact: tokens=[REDACTED] level=ok effectiveWindow=980000
2026-09-06T23:57:25.357Z [DEBUG] Tool search disabled: ToolSearchTool is not available (may have been disallowed via disallowedTools).
2026-09-06T23:57:25.357Z [DEBUG] attribution header x-anthropic-billing-header: cc_version=2.1.263.992; cc_entrypoint=sdk-cli; cch=00000; cc_prev_req=req_011Ceo6GXc5aY5yajYEvMqSx; cc_prompt_id=51ed5dfe-6e13-480f-82d9-c21bda316023;
2026-09-06T23:57:25.357Z [DEBUG] Fast mode unavailable: Fast mode is not available in the Agent SDK
2026-09-06T23:57:25.357Z [DEBUG] Fast mode unavailable: Fast mode is not available in the Agent SDK
2026-09-06T23:57:25.358Z [DEBUG] Fast mode unavailable: Fast mode is not available in the Agent SDK
2026-09-06T23:57:25.358Z [DEBUG] [API:timing] dispatching to firstParty model=claude-sonnet-5
2026-09-06T23:57:25.358Z [DEBUG] [API REQUEST] /v1/messages x-client-request-id=51cb6396-c968-4494-8ac6-41262fe62b79 source=sdk
2026-09-06T23:57:26.102Z [DEBUG] Stream started - received first chunk
2026-09-06T23:57:26.102Z [DEBUG] [API:timing] first byte after 744ms
2026-09-06T23:57:28.334Z [INFO] [Stall] tool_dispatch_start tool=Bash toolUseId=toolu_016GuTdoMffJxqNVZ8iGTeEs permissionDecisionMs=2
2026-09-06T23:57:28.334Z [DEBUG] Spawning shell without login (-l flag skipped)
2026-09-06T23:57:28.366Z [INFO] [Stall] tool_dispatch_end tool=Bash toolUseId=toolu_016GuTdoMffJxqNVZ8iGTeEs outcome=ok durationMs=33
2026-09-06T23:57:28.426Z [DEBUG] autocompact: tokens=[REDACTED] level=ok effectiveWindow=980000
2026-09-06T23:57:28.427Z [DEBUG] Tool search disabled: ToolSearchTool is not available (may have been disallowed via disallowedTools).
2026-09-06T23:57:28.427Z [DEBUG] attribution header x-anthropic-billing-header: cc_version=2.1.263.992; cc_entrypoint=sdk-cli; cch=00000; cc_prev_req=req_011Ceo6Gkw1q9oWM3fsW3vh8; cc_prompt_id=51ed5dfe-6e13-480f-82d9-c21bda316023;
2026-09-06T23:57:28.427Z [DEBUG] Fast mode unavailable: Fast mode is not available in the Agent SDK
2026-09-06T23:57:28.427Z [DEBUG] Fast mode unavailable: Fast mode is not available in the Agent SDK
2026-09-06T23:57:28.428Z [DEBUG] Fast mode unavailable: Fast mode is not available in the Agent SDK
2026-09-06T23:57:28.428Z [DEBUG] [API:timing] dispatching to firstParty model=claude-sonnet-5
2026-09-06T23:57:28.428Z [DEBUG] [API REQUEST] /v1/messages x-client-request-id=35a0dc8f-ba30-439a-9c95-1e0887ed3397 source=sdk
2026-09-06T23:57:29.306Z [DEBUG] Stream started - received first chunk
2026-09-06T23:57:29.306Z [DEBUG] [API:timing] first byte after 878ms
2026-09-06T23:57:31.089Z [INFO] [Stall] tool_dispatch_start tool=Bash toolUseId=toolu_015V7RNtCQV2TfYTsysg9y24 permissionDecisionMs=5
2026-09-06T23:57:31.091Z [DEBUG] Spawning shell without login (-l flag skipped)
2026-09-06T23:57:31.126Z [DEBUG] Invalidating session environment cache
2026-09-06T23:57:31.128Z [INFO] [Stall] tool_dispatch_end tool=Bash toolUseId=toolu_015V7RNtCQV2TfYTsysg9y24 outcome=ok durationMs=39
2026-09-06T23:57:31.130Z [DEBUG] autocompact: tokens=[REDACTED] level=ok effectiveWindow=980000
2026-09-06T23:57:31.130Z [DEBUG] Tool search disabled: ToolSearchTool is not available (may have been disallowed via disallowedTools).
2026-09-06T23:57:31.131Z [DEBUG] attribution header x-anthropic-billing-header: cc_version=2.1.263.992; cc_entrypoint=sdk-cli; cch=00000; cc_prev_req=req_011Ceo6Gz4Ym6LZfve2cheW4; cc_prompt_id=51ed5dfe-6e13-480f-82d9-c21bda316023;
2026-09-06T23:57:31.131Z [DEBUG] Fast mode unavailable: Fast mode is not available in the Agent SDK
2026-09-06T23:57:31.131Z [DEBUG] Fast mode unavailable: Fast mode is not available in the Agent SDK
2026-09-06T23:57:31.132Z [DEBUG] Fast mode unavailable: Fast mode is not available in the Agent SDK
2026-09-06T23:57:31.132Z [DEBUG] [API:timing] dispatching to firstParty model=claude-sonnet-5
2026-09-06T23:57:31.132Z [DEBUG] [API REQUEST] /v1/messages x-client-request-id=3b34f7e4-e138-4117-9ada-e544d26fcd98 source=sdk
2026-09-06T23:57:31.942Z [DEBUG] Stream started - received first chunk
2026-09-06T23:57:31.942Z [DEBUG] [API:timing] first byte after 810ms
2026-09-06T23:57:35.439Z [DEBUG] "Permission suggestions for Bash: [\n  {\n    \"type\": \"addRules\",\n    \"rules\": [\n      {\n        \"toolName\": \"Bash\",\n        \"ruleContent\": \"python3 -m json.tool\"\n      }\n    ],\n    \"behavior\": \"allow\",\n    \"destination\": \"localSettings\"\n  }\n]"
2026-09-06T23:57:35.441Z [DEBUG] [auto-mode] context comparison: mainLoopTokens=[REDACTED] classifierChars=130198 classifierTokensEst=[REDACTED] (sys=126435 tools=824 user=2939) transcriptEntries=7 messages=26
2026-09-06T23:57:35.441Z [DEBUG] [auto-mode] new action being classified: {"Bash":"cat findings.json | python3 -m json.tool | head -200"}
2026-09-06T23:57:35.442Z [INFO] [Stall] classifier_request_started reqId=33ac05dc-552d-4b1c-8dc9-cf821e926bf5 tool=Bash model=claude-sonnet-5[1m] stage=xml_s1 promptTokensEst=[REDACTED]
2026-09-06T23:57:35.443Z [DEBUG] attribution header x-anthropic-billing-header: cc_version=2.1.263.b6e; cc_entrypoint=sdk-cli; cch=00000;
2026-09-06T23:57:35.444Z [DEBUG] [API REQUEST] /v1/messages x-client-request-id=97bdcdfc-77a7-474e-b6b1-79b38f994f2d source=side_query
2026-09-06T23:57:36.822Z [INFO] [Stall] classifier_request_finished reqId=33ac05dc-552d-4b1c-8dc9-cf821e926bf5 tool=Bash stage=xml_s1 outcome=ok durationMs=1380
2026-09-06T23:57:36.826Z [INFO] [Stall] tool_dispatch_start tool=Bash toolUseId=toolu_01L2zGn5jfBXExgzgSShrHxU permissionDecisionMs=1390
2026-09-06T23:57:36.827Z [DEBUG] No session environment scripts found
2026-09-06T23:57:36.827Z [DEBUG] Spawning shell without login (-l flag skipped)
2026-09-06T23:57:36.893Z [INFO] [Stall] tool_dispatch_end tool=Bash toolUseId=toolu_01L2zGn5jfBXExgzgSShrHxU outcome=ok durationMs=67
2026-09-06T23:57:36.895Z [DEBUG] autocompact: tokens=[REDACTED] level=ok effectiveWindow=980000
2026-09-06T23:57:36.896Z [DEBUG] Tool search disabled: ToolSearchTool is not available (may have been disallowed via disallowedTools).
2026-09-06T23:57:36.897Z [DEBUG] attribution header x-anthropic-billing-header: cc_version=2.1.263.992; cc_entrypoint=sdk-cli; cch=00000; cc_prev_req=req_011Ceo6HBe4XJR4WXL2VJHse; cc_prompt_id=51ed5dfe-6e13-480f-82d9-c21bda316023;
2026-09-06T23:57:36.897Z [DEBUG] Fast mode unavailable: Fast mode is not available in the Agent SDK
2026-09-06T23:57:36.897Z [DEBUG] Fast mode unavailable: Fast mode is not available in the Agent SDK
2026-09-06T23:57:36.897Z [DEBUG] Fast mode unavailable: Fast mode is not available in the Agent SDK
2026-09-06T23:57:36.898Z [DEBUG] [API:timing] dispatching to firstParty model=claude-sonnet-5
2026-09-06T23:57:36.898Z [DEBUG] [API REQUEST] /v1/messages x-client-request-id=06bedd4e-f01b-4b27-8572-d3280d5e9684 source=sdk
2026-09-06T23:57:37.869Z [DEBUG] Stream started - received first chunk
2026-09-06T23:57:37.869Z [DEBUG] [API:timing] first byte after 972ms
2026-09-06T23:57:39.654Z [DEBUG] "Permission suggestions for Bash: [\n  {\n    \"type\": \"addRules\",\n    \"rules\": [\n      {\n        \"toolName\": \"Bash\",\n        \"ruleContent\": \"python3 -c ' *\"\n      }\n    ],\n    \"behavior\": \"allow\",\n    \"destination\": \"localSettings\"\n  }\n]"
2026-09-06T23:57:39.655Z [DEBUG] [auto-mode] context comparison: mainLoopTokens=[REDACTED] classifierChars=130354 classifierTokensEst=[REDACTED] (sys=126435 tools=980 user=2939) transcriptEntries=8 messages=29
2026-09-06T23:57:39.655Z [DEBUG] [auto-mode] new action being classified: {"Bash":"python3 -c \"\nimport json\nd = json.load(open('findings.json'))\nprint(len(d))\nfor f in d:\n    print(f['id'], f['severity'], f['status'])\n\""}
2026-09-06T23:57:39.655Z [INFO] [Stall] classifier_request_started reqId=592d3d73-4f8d-4fe8-adec-85816042a481 tool=Bash model=claude-sonnet-5[1m] stage=xml_s1 promptTokensEst=[REDACTED]
2026-09-06T23:57:39.656Z [DEBUG] attribution header x-anthropic-billing-header: cc_version=2.1.263.b6e; cc_entrypoint=sdk-cli; cch=00000;
2026-09-06T23:57:39.656Z [DEBUG] [API REQUEST] /v1/messages x-client-request-id=5e562c8d-d13b-4889-bded-7f92ff1b62f6 source=side_query
2026-09-06T23:57:41.117Z [INFO] [Stall] classifier_request_finished reqId=592d3d73-4f8d-4fe8-adec-85816042a481 tool=Bash stage=xml_s1 outcome=ok durationMs=1462
2026-09-06T23:57:41.121Z [INFO] [Stall] tool_dispatch_start tool=Bash toolUseId=toolu_017UUCcFDHmzCcELmc32vCKK permissionDecisionMs=1467
2026-09-06T23:57:41.124Z [DEBUG] Spawning shell without login (-l flag skipped)
2026-09-06T23:57:41.174Z [INFO] [Stall] tool_dispatch_end tool=Bash toolUseId=toolu_017UUCcFDHmzCcELmc32vCKK outcome=ok durationMs=53
2026-09-06T23:57:41.176Z [DEBUG] autocompact: tokens=[REDACTED] level=ok effectiveWindow=980000
2026-09-06T23:57:41.176Z [DEBUG] Tool search disabled: ToolSearchTool is not available (may have been disallowed via disallowedTools).
2026-09-06T23:57:41.177Z [DEBUG] attribution header x-anthropic-billing-header: cc_version=2.1.263.992; cc_entrypoint=sdk-cli; cch=00000; cc_prev_req=req_011Ceo6HcKsgp1eWXfj7aPJv; cc_prompt_id=51ed5dfe-6e13-480f-82d9-c21bda316023;
2026-09-06T23:57:41.177Z [DEBUG] Fast mode unavailable: Fast mode is not available in the Agent SDK
2026-09-06T23:57:41.177Z [DEBUG] Fast mode unavailable: Fast mode is not available in the Agent SDK
2026-09-06T23:57:41.178Z [DEBUG] Fast mode unavailable: Fast mode is not available in the Agent SDK
2026-09-06T23:57:41.178Z [DEBUG] [API:timing] dispatching to firstParty model=claude-sonnet-5
2026-09-06T23:57:41.178Z [DEBUG] [API REQUEST] /v1/messages x-client-request-id=124679b3-dd73-46d3-bdb5-970dd13fac8b source=sdk
2026-09-06T23:57:42.082Z [DEBUG] Stream started - received first chunk
2026-09-06T23:57:42.082Z [DEBUG] [API:timing] first byte after 904ms
2026-09-06T23:57:44.498Z [DEBUG] "Permission suggestions for Bash: [\n  {\n    \"type\": \"addRules\",\n    \"rules\": [\n      {\n        \"toolName\": \"Bash\",\n        \"ruleContent\": \"python3 -c ' *\"\n      }\n    ],\n    \"behavior\": \"allow\",\n    \"destination\": \"localSettings\"\n  }\n]"
2026-09-06T23:57:44.499Z [DEBUG] [auto-mode] context comparison: mainLoopTokens=[REDACTED] classifierChars=130522 classifierTokensEst=[REDACTED] (sys=126435 tools=1148 user=2939) transcriptEntries=9 messages=32
2026-09-06T23:57:44.499Z [DEBUG] [auto-mode] new action being classified: {"Bash":"python3 -c \"\nimport json\nd = json.load(open('findings.json'))\nf = [x for x in d if x['id']=='T081-V4-S3A-DA-010'][0]\nprint(json.dumps(f, indent=2))\n\""}
2026-09-06T23:57:44.499Z [INFO] [Stall] classifier_request_started reqId=2e8743e6-c667-49c1-9a41-d2263223b0ee tool=Bash model=claude-sonnet-5[1m] stage=xml_s1 promptTokensEst=[REDACTED]
2026-09-06T23:57:44.499Z [DEBUG] attribution header x-anthropic-billing-header: cc_version=2.1.263.b6e; cc_entrypoint=sdk-cli; cch=00000;
2026-09-06T23:57:44.500Z [DEBUG] [API REQUEST] /v1/messages x-client-request-id=d153b12e-29a6-4d1d-a3de-6827d6a4c1ae source=side_query
2026-09-06T23:57:45.999Z [INFO] [Stall] classifier_request_finished reqId=2e8743e6-c667-49c1-9a41-d2263223b0ee tool=Bash stage=xml_s1 outcome=ok durationMs=1500
2026-09-06T23:57:46.001Z [INFO] [Stall] tool_dispatch_start tool=Bash toolUseId=toolu_01McFiwvJkR7ZbSbLFFJQAGa permissionDecisionMs=1507
2026-09-06T23:57:46.002Z [DEBUG] Spawning shell without login (-l flag skipped)
2026-09-06T23:57:46.052Z [INFO] [Stall] tool_dispatch_end tool=Bash toolUseId=toolu_01McFiwvJkR7ZbSbLFFJQAGa outcome=ok durationMs=51
2026-09-06T23:57:46.054Z [DEBUG] autocompact: tokens=[REDACTED] level=ok effectiveWindow=980000
2026-09-06T23:57:46.054Z [DEBUG] Tool search disabled: ToolSearchTool is not available (may have been disallowed via disallowedTools).
2026-09-06T23:57:46.055Z [DEBUG] attribution header x-anthropic-billing-header: cc_version=2.1.263.992; cc_entrypoint=sdk-cli; cch=00000; cc_prev_req=req_011Ceo6HvbU9uFkXBdqKaU4K; cc_prompt_id=51ed5dfe-6e13-480f-82d9-c21bda316023;
2026-09-06T23:57:46.055Z [DEBUG] Fast mode unavailable: Fast mode is not available in the Agent SDK
2026-09-06T23:57:46.055Z [DEBUG] Fast mode unavailable: Fast mode is not available in the Agent SDK
2026-09-06T23:57:46.056Z [DEBUG] Fast mode unavailable: Fast mode is not available in the Agent SDK
2026-09-06T23:57:46.056Z [DEBUG] [API:timing] dispatching to firstParty model=claude-sonnet-5
2026-09-06T23:57:46.056Z [DEBUG] [API REQUEST] /v1/messages x-client-request-id=e2877dce-0625-455f-9975-23e7a8d693a5 source=sdk
2026-09-06T23:57:46.782Z [DEBUG] Stream started - received first chunk
2026-09-06T23:57:46.782Z [DEBUG] [API:timing] first byte after 727ms
2026-09-06T23:57:49.038Z [INFO] [Stall] tool_dispatch_start tool=Read toolUseId=toolu_017D5gcVUWaYvbb3o2JxVyp3 permissionDecisionMs=6
2026-09-06T23:57:49.041Z [INFO] [Stall] tool_dispatch_end tool=Read toolUseId=toolu_017D5gcVUWaYvbb3o2JxVyp3 outcome=ok durationMs=3
2026-09-06T23:57:49.049Z [DEBUG] autocompact: tokens=[REDACTED] level=ok effectiveWindow=980000
2026-09-06T23:57:49.049Z [DEBUG] Tool search disabled: ToolSearchTool is not available (may have been disallowed via disallowedTools).
2026-09-06T23:57:49.050Z [DEBUG] attribution header x-anthropic-billing-header: cc_version=2.1.263.992; cc_entrypoint=sdk-cli; cch=00000; cc_prev_req=req_011Ceo6JHTqPzEmW4h6Ud1mR; cc_prompt_id=51ed5dfe-6e13-480f-82d9-c21bda316023;
2026-09-06T23:57:49.050Z [DEBUG] Fast mode unavailable: Fast mode is not available in the Agent SDK
2026-09-06T23:57:49.050Z [DEBUG] Fast mode unavailable: Fast mode is not available in the Agent SDK
2026-09-06T23:57:49.051Z [DEBUG] Fast mode unavailable: Fast mode is not available in the Agent SDK
2026-09-06T23:57:49.051Z [DEBUG] [API:timing] dispatching to firstParty model=claude-sonnet-5
2026-09-06T23:57:49.051Z [DEBUG] [API REQUEST] /v1/messages x-client-request-id=713164b5-ec8b-4260-ba49-f037d4ba135a source=sdk
2026-09-06T23:57:50.037Z [DEBUG] Stream started - received first chunk
2026-09-06T23:57:50.037Z [DEBUG] [API:timing] first byte after 986ms
2026-09-06T23:57:51.556Z [INFO] [Stall] tool_dispatch_start tool=Read toolUseId=toolu_013ma7jQ2BnqEsDn92PBUnzc permissionDecisionMs=2
2026-09-06T23:57:51.560Z [DEBUG] [API REQUEST] /v1/messages/count_tokens x-client-request-id=7dcdac1c-4b3f-4cfe-8960-0ef30eb3f34c source=count_tokens
2026-09-06T23:57:51.661Z [INFO] [Stall] tool_dispatch_end tool=Read toolUseId=toolu_013ma7jQ2BnqEsDn92PBUnzc outcome=ok durationMs=105
2026-09-06T23:57:51.663Z [DEBUG] autocompact: tokens=[REDACTED] level=ok effectiveWindow=980000
2026-09-06T23:57:51.664Z [DEBUG] Tool search disabled: ToolSearchTool is not available (may have been disallowed via disallowedTools).
2026-09-06T23:57:51.664Z [DEBUG] attribution header x-anthropic-billing-header: cc_version=2.1.263.992; cc_entrypoint=sdk-cli; cch=00000; cc_prev_req=req_011Ceo6JWG23mfRsKLcMhfzp; cc_prompt_id=51ed5dfe-6e13-480f-82d9-c21bda316023;
2026-09-06T23:57:51.664Z [DEBUG] Fast mode unavailable: Fast mode is not available in the Agent SDK
2026-09-06T23:57:51.664Z [DEBUG] Fast mode unavailable: Fast mode is not available in the Agent SDK
2026-09-06T23:57:51.665Z [DEBUG] Fast mode unavailable: Fast mode is not available in the Agent SDK
2026-09-06T23:57:51.665Z [DEBUG] [API:timing] dispatching to firstParty model=claude-sonnet-5
2026-09-06T23:57:51.666Z [DEBUG] [API REQUEST] /v1/messages x-client-request-id=11497feb-3077-4550-a056-baa1ea4de028 source=sdk
2026-09-06T23:57:52.382Z [DEBUG] Stream started - received first chunk
2026-09-06T23:57:52.382Z [DEBUG] [API:timing] first byte after 717ms
2026-09-06T23:57:56.903Z [INFO] [Stall] tool_dispatch_start tool=Bash toolUseId=toolu_01QmqvbfjaYst8vyVPZnm7mR permissionDecisionMs=3
2026-09-06T23:57:56.905Z [DEBUG] Spawning shell without login (-l flag skipped)
2026-09-06T23:57:56.941Z [INFO] [Stall] tool_dispatch_end tool=Bash toolUseId=toolu_01QmqvbfjaYst8vyVPZnm7mR outcome=ok durationMs=38
2026-09-06T23:57:56.942Z [DEBUG] autocompact: tokens=[REDACTED] level=ok effectiveWindow=980000
2026-09-06T23:57:56.943Z [DEBUG] Tool search disabled: ToolSearchTool is not available (may have been disallowed via disallowedTools).
2026-09-06T23:57:56.943Z [DEBUG] attribution header x-anthropic-billing-header: cc_version=2.1.263.992; cc_entrypoint=sdk-cli; cch=00000; cc_prev_req=req_011Ceo6JhSioQHWCG9uu7ee9; cc_prompt_id=51ed5dfe-6e13-480f-82d9-c21bda316023;
2026-09-06T23:57:56.944Z [DEBUG] Fast mode unavailable: Fast mode is not available in the Agent SDK
2026-09-06T23:57:56.944Z [DEBUG] Fast mode unavailable: Fast mode is not available in the Agent SDK
2026-09-06T23:57:56.944Z [DEBUG] Fast mode unavailable: Fast mode is not available in the Agent SDK
2026-09-06T23:57:56.944Z [DEBUG] [API:timing] dispatching to firstParty model=claude-sonnet-5
2026-09-06T23:57:56.945Z [DEBUG] [API REQUEST] /v1/messages x-client-request-id=ce492e58-1f8f-491f-b04b-ee7eabdcb313 source=sdk
2026-09-06T23:57:57.799Z [DEBUG] Stream started - received first chunk
2026-09-06T23:57:57.799Z [DEBUG] [API:timing] first byte after 854ms
2026-09-06T23:58:04.492Z [INFO] [Stall] tool_dispatch_start tool=Read toolUseId=toolu_01XtgScxg2TFKotY6TsqYrmN permissionDecisionMs=2
2026-09-06T23:58:04.495Z [INFO] [Stall] tool_dispatch_end tool=Read toolUseId=toolu_01XtgScxg2TFKotY6TsqYrmN outcome=ok durationMs=3
2026-09-06T23:58:04.513Z [DEBUG] autocompact: tokens=[REDACTED] level=ok effectiveWindow=980000
2026-09-06T23:58:04.514Z [DEBUG] Tool search disabled: ToolSearchTool is not available (may have been disallowed via disallowedTools).
2026-09-06T23:58:04.515Z [DEBUG] attribution header x-anthropic-billing-header: cc_version=2.1.263.992; cc_entrypoint=sdk-cli; cch=00000; cc_prev_req=req_011Ceo6K65kne6LBWGY6DgPa; cc_prompt_id=51ed5dfe-6e13-480f-82d9-c21bda316023;
2026-09-06T23:58:04.515Z [DEBUG] Fast mode unavailable: Fast mode is not available in the Agent SDK
2026-09-06T23:58:04.515Z [DEBUG] Fast mode unavailable: Fast mode is not available in the Agent SDK
2026-09-06T23:58:04.516Z [DEBUG] Fast mode unavailable: Fast mode is not available in the Agent SDK
2026-09-06T23:58:04.516Z [DEBUG] [API:timing] dispatching to firstParty model=claude-sonnet-5
2026-09-06T23:58:04.517Z [DEBUG] [API REQUEST] /v1/messages x-client-request-id=e810e10b-e799-4d11-a6de-6958630db329 source=sdk
2026-09-06T23:58:05.517Z [DEBUG] Stream started - received first chunk
2026-09-06T23:58:05.517Z [DEBUG] [API:timing] first byte after 1001ms
2026-09-06T23:58:07.423Z [INFO] [Stall] tool_dispatch_start tool=Read toolUseId=toolu_015aiAf35j1Bh1rDypodMn5V permissionDecisionMs=1
2026-09-06T23:58:07.424Z [INFO] [Stall] tool_dispatch_end tool=Read toolUseId=toolu_015aiAf35j1Bh1rDypodMn5V outcome=ok durationMs=1
2026-09-06T23:58:07.435Z [DEBUG] autocompact: tokens=[REDACTED] level=ok effectiveWindow=980000
2026-09-06T23:58:07.435Z [DEBUG] Tool search disabled: ToolSearchTool is not available (may have been disallowed via disallowedTools).
2026-09-06T23:58:07.436Z [DEBUG] attribution header x-anthropic-billing-header: cc_version=2.1.263.992; cc_entrypoint=sdk-cli; cch=00000; cc_prev_req=req_011Ceo6KejXt489D7uk3ghnR; cc_prompt_id=51ed5dfe-6e13-480f-82d9-c21bda316023;
2026-09-06T23:58:07.436Z [DEBUG] Fast mode unavailable: Fast mode is not available in the Agent SDK
2026-09-06T23:58:07.436Z [DEBUG] Fast mode unavailable: Fast mode is not available in the Agent SDK
2026-09-06T23:58:07.437Z [DEBUG] Fast mode unavailable: Fast mode is not available in the Agent SDK
2026-09-06T23:58:07.437Z [DEBUG] [API:timing] dispatching to firstParty model=claude-sonnet-5
2026-09-06T23:58:07.437Z [DEBUG] [API REQUEST] /v1/messages x-client-request-id=ce11a9b5-7aba-46ae-850d-9d9a42a8e086 source=sdk
2026-09-06T23:58:08.322Z [DEBUG] Stream started - received first chunk
2026-09-06T23:58:08.322Z [DEBUG] [API:timing] first byte after 885ms
2026-09-06T23:58:39.910Z [DEBUG] "Permission suggestions for Bash: [\n  {\n    \"type\": \"addRules\",\n    \"rules\": [\n      {\n        \"toolName\": \"Bash\",\n        \"ruleContent\": \"python3 -\"\n      }\n    ],\n    \"behavior\": \"allow\",\n    \"destination\": \"localSettings\"\n  }\n]"
2026-09-06T23:58:39.913Z [DEBUG] [auto-mode] context comparison: mainLoopTokens=[REDACTED] classifierChars=130888 classifierTokensEst=[REDACTED] (sys=126435 tools=1514 user=2939) transcriptEntries=11 messages=49
2026-09-06T23:58:39.913Z [DEBUG] [auto-mode] new action being classified: {"Bash":"cd /Users/hostiletakeover/Projects/paprnav && python3 - <<'EOF'\nimport json\nd = json.load(open(\"backend/app/schemas/ad_extraction_v4.schema.json\"))\nprint(list(d.get(\"properties\", {}).keys()))\nEOF\n"}
2026-09-06T23:58:39.913Z [INFO] [Stall] classifier_request_started reqId=8f3f5082-090c-49a5-b95c-61ab826cc5e7 tool=Bash model=claude-sonnet-5[1m] stage=xml_s1 promptTokensEst=[REDACTED]
2026-09-06T23:58:39.916Z [DEBUG] attribution header x-anthropic-billing-header: cc_version=2.1.263.b6e; cc_entrypoint=sdk-cli; cch=00000;
2026-09-06T23:58:39.916Z [DEBUG] [API REQUEST] /v1/messages x-client-request-id=2b6c1a66-d578-4846-a591-3cd135a73af8 source=side_query
2026-09-06T23:58:41.196Z [INFO] [Stall] classifier_request_finished reqId=8f3f5082-090c-49a5-b95c-61ab826cc5e7 tool=Bash stage=xml_s1 outcome=ok durationMs=1283
2026-09-06T23:58:41.200Z [INFO] [Stall] tool_dispatch_start tool=Bash toolUseId=toolu_01DiRmreRocqAMswvDUjBJVh permissionDecisionMs=1295
2026-09-06T23:58:41.205Z [DEBUG] Spawning shell without login (-l flag skipped)
2026-09-06T23:58:41.265Z [DEBUG] Invalidating session environment cache
2026-09-06T23:58:41.266Z [INFO] [Stall] tool_dispatch_end tool=Bash toolUseId=toolu_01DiRmreRocqAMswvDUjBJVh outcome=ok durationMs=66
2026-09-06T23:58:41.268Z [DEBUG] autocompact: tokens=[REDACTED] level=ok effectiveWindow=980000
2026-09-06T23:58:41.269Z [DEBUG] Tool search disabled: ToolSearchTool is not available (may have been disallowed via disallowedTools).
2026-09-06T23:58:41.270Z [DEBUG] attribution header x-anthropic-billing-header: cc_version=2.1.263.992; cc_entrypoint=sdk-cli; cch=00000; cc_prev_req=req_011Ceo6Krsnbr4VyU5C63hmb; cc_prompt_id=51ed5dfe-6e13-480f-82d9-c21bda316023;
2026-09-06T23:58:41.270Z [DEBUG] Fast mode unavailable: Fast mode is not available in the Agent SDK
2026-09-06T23:58:41.270Z [DEBUG] Fast mode unavailable: Fast mode is not available in the Agent SDK
2026-09-06T23:58:41.271Z [DEBUG] Fast mode unavailable: Fast mode is not available in the Agent SDK
2026-09-06T23:58:41.271Z [DEBUG] [API:timing] dispatching to firstParty model=claude-sonnet-5
2026-09-06T23:58:41.271Z [DEBUG] [API REQUEST] /v1/messages x-client-request-id=aa18ce9c-33ba-4499-bd9a-8edcc08a270f source=sdk
2026-09-06T23:58:42.456Z [DEBUG] Stream started - received first chunk
2026-09-06T23:58:42.456Z [DEBUG] [API:timing] first byte after 1185ms
2026-09-06T23:58:43.275Z [DEBUG] "Permission suggestions for Bash: [\n  {\n    \"type\": \"addRules\",\n    \"rules\": [\n      {\n        \"toolName\": \"Bash\",\n        \"ruleContent\": \"python3 -\"\n      }\n    ],\n    \"behavior\": \"allow\",\n    \"destination\": \"localSettings\"\n  }\n]"
2026-09-06T23:58:43.276Z [DEBUG] [auto-mode] context comparison: mainLoopTokens=[REDACTED] classifierChars=131102 classifierTokensEst=[REDACTED] (sys=126435 tools=1728 user=2939) transcriptEntries=12 messages=52
2026-09-06T23:58:43.276Z [DEBUG] [auto-mode] new action being classified: {"Bash":"python3 - <<'EOF'\nimport json\nd = json.load(open(\"backend/app/schemas/ad_extraction_v4.schema.json\"))\nprop = d[\"properties\"][\"proposal\"]\nprint(list(prop.get(\"properties\", {}).keys()))\nEOF\n"}
2026-09-06T23:58:43.276Z [INFO] [Stall] classifier_request_started reqId=aef7e1db-f83b-4aba-9869-11b375a80667 tool=Bash model=claude-sonnet-5[1m] stage=xml_s1 promptTokensEst=[REDACTED]
2026-09-06T23:58:43.277Z [DEBUG] attribution header x-anthropic-billing-header: cc_version=2.1.263.b6e; cc_entrypoint=sdk-cli; cch=00000;
2026-09-06T23:58:43.277Z [DEBUG] [API REQUEST] /v1/messages x-client-request-id=2c47b31b-510d-4589-ac89-91e85a98200c source=side_query
2026-09-06T23:58:44.502Z [INFO] [Stall] classifier_request_finished reqId=aef7e1db-f83b-4aba-9869-11b375a80667 tool=Bash stage=xml_s1 outcome=ok durationMs=1226
2026-09-06T23:58:44.506Z [INFO] [Stall] tool_dispatch_start tool=Bash toolUseId=toolu_01JoVWZwXhmCxdh4bLnPSr4Y permissionDecisionMs=1232
2026-09-06T23:58:44.507Z [DEBUG] No session environment scripts found
2026-09-06T23:58:44.507Z [DEBUG] Spawning shell without login (-l flag skipped)
2026-09-06T23:58:44.553Z [INFO] [Stall] tool_dispatch_end tool=Bash toolUseId=toolu_01JoVWZwXhmCxdh4bLnPSr4Y outcome=ok durationMs=47
2026-09-06T23:58:44.554Z [DEBUG] autocompact: tokens=[REDACTED] level=ok effectiveWindow=980000
2026-09-06T23:58:44.555Z [DEBUG] Tool search disabled: ToolSearchTool is not available (may have been disallowed via disallowedTools).
2026-09-06T23:58:44.556Z [DEBUG] attribution header x-anthropic-billing-header: cc_version=2.1.263.992; cc_entrypoint=sdk-cli; cch=00000; cc_prev_req=req_011Ceo6NMei5V1oV8u8UrPB4; cc_prompt_id=51ed5dfe-6e13-480f-82d9-c21bda316023;
2026-09-06T23:58:44.556Z [DEBUG] Fast mode unavailable: Fast mode is not available in the Agent SDK
2026-09-06T23:58:44.556Z [DEBUG] Fast mode unavailable: Fast mode is not available in the Agent SDK
2026-09-06T23:58:44.556Z [DEBUG] Fast mode unavailable: Fast mode is not available in the Agent SDK
2026-09-06T23:58:44.557Z [DEBUG] [API:timing] dispatching to firstParty model=claude-sonnet-5
2026-09-06T23:58:44.557Z [DEBUG] [API REQUEST] /v1/messages x-client-request-id=5e8ef07e-f0c7-459a-a1c8-e62c7d70894e source=sdk
2026-09-06T23:58:45.588Z [DEBUG] Stream started - received first chunk
2026-09-06T23:58:45.588Z [DEBUG] [API:timing] first byte after 1032ms
2026-09-06T23:58:46.258Z [DEBUG] "Permission suggestions for Bash: [\n  {\n    \"type\": \"addRules\",\n    \"rules\": [\n      {\n        \"toolName\": \"Bash\",\n        \"ruleContent\": \"python3 -\"\n      }\n    ],\n    \"behavior\": \"allow\",\n    \"destination\": \"localSettings\"\n  }\n]"
2026-09-06T23:58:46.259Z [DEBUG] [auto-mode] context comparison: mainLoopTokens=[REDACTED] classifierChars=131295 classifierTokensEst=[REDACTED] (sys=126435 tools=1921 user=2939) transcriptEntries=13 messages=54
2026-09-06T23:58:46.259Z [DEBUG] [auto-mode] new action being classified: {"Bash":"python3 - <<'EOF'\nimport json\nd = json.load(open(\"backend/app/schemas/ad_extraction_v4.schema.json\"))\nprint(json.dumps(d[\"properties\"][\"proposal\"], indent=2)[:2000])\nEOF\n"}
2026-09-06T23:58:46.259Z [INFO] [Stall] classifier_request_started reqId=3ef2a18a-a972-479b-8527-aba86c346b57 tool=Bash model=claude-sonnet-5[1m] stage=xml_s1 promptTokensEst=[REDACTED]
2026-09-06T23:58:46.260Z [DEBUG] attribution header x-anthropic-billing-header: cc_version=2.1.263.b6e; cc_entrypoint=sdk-cli; cch=00000;
2026-09-06T23:58:46.260Z [DEBUG] [API REQUEST] /v1/messages x-client-request-id=20bb1e23-6640-4f7d-9bef-0e88b8b5dd41 source=side_query
2026-09-06T23:58:47.605Z [INFO] [Stall] classifier_request_finished reqId=3ef2a18a-a972-479b-8527-aba86c346b57 tool=Bash stage=xml_s1 outcome=ok durationMs=1346
2026-09-06T23:58:47.608Z [INFO] [Stall] tool_dispatch_start tool=Bash toolUseId=toolu_01AhdM7FKDg8Dy6M9dNwiueN permissionDecisionMs=1353
2026-09-06T23:58:47.609Z [DEBUG] Spawning shell without login (-l flag skipped)
2026-09-06T23:58:47.656Z [INFO] [Stall] tool_dispatch_end tool=Bash toolUseId=toolu_01AhdM7FKDg8Dy6M9dNwiueN outcome=ok durationMs=48
2026-09-06T23:58:47.658Z [DEBUG] autocompact: tokens=[REDACTED] level=ok effectiveWindow=980000
2026-09-06T23:58:47.658Z [DEBUG] Tool search disabled: ToolSearchTool is not available (may have been disallowed via disallowedTools).
2026-09-06T23:58:47.659Z [DEBUG] attribution header x-anthropic-billing-header: cc_version=2.1.263.992; cc_entrypoint=sdk-cli; cch=00000; cc_prev_req=req_011Ceo6Nbo1XRLhKSUzvnvHk; cc_prompt_id=51ed5dfe-6e13-480f-82d9-c21bda316023;
2026-09-06T23:58:47.659Z [DEBUG] Fast mode unavailable: Fast mode is not available in the Agent SDK
2026-09-06T23:58:47.659Z [DEBUG] Fast mode unavailable: Fast mode is not available in the Agent SDK
2026-09-06T23:58:47.659Z [DEBUG] Fast mode unavailable: Fast mode is not available in the Agent SDK
2026-09-06T23:58:47.660Z [DEBUG] [API:timing] dispatching to firstParty model=claude-sonnet-5
2026-09-06T23:58:47.660Z [DEBUG] [API REQUEST] /v1/messages x-client-request-id=97cb150a-01a3-43e0-9502-3eb981247260 source=sdk
2026-09-06T23:58:48.652Z [DEBUG] Stream started - received first chunk
2026-09-06T23:58:48.652Z [DEBUG] [API:timing] first byte after 992ms
2026-09-06T23:58:49.301Z [DEBUG] "Permission suggestions for Bash: [\n  {\n    \"type\": \"addRules\",\n    \"rules\": [\n      {\n        \"toolName\": \"Bash\",\n        \"ruleContent\": \"python3 -\"\n      }\n    ],\n    \"behavior\": \"allow\",\n    \"destination\": \"localSettings\"\n  }\n]"
2026-09-06T23:58:49.302Z [DEBUG] [auto-mode] context comparison: mainLoopTokens=[REDACTED] classifierChars=131511 classifierTokensEst=[REDACTED] (sys=126435 tools=2137 user=2939) transcriptEntries=14 messages=56
2026-09-06T23:58:49.302Z [DEBUG] [auto-mode] new action being classified: {"Bash":"python3 - <<'EOF'\nimport json\nd = json.load(open(\"backend/app/schemas/ad_extraction_v4.schema.json\"))\ndefs = d[\"$defs\"]\np = defs[\"proposal\"]\nprint(list(p.get(\"properties\", {}).keys()))\nEOF\n"}
2026-09-06T23:58:49.302Z [INFO] [Stall] classifier_request_started reqId=ad3d4f00-434c-4a44-8a3c-784a49d8814f tool=Bash model=claude-sonnet-5[1m] stage=xml_s1 promptTokensEst=[REDACTED]
2026-09-06T23:58:49.303Z [DEBUG] attribution header x-anthropic-billing-header: cc_version=2.1.263.b6e; cc_entrypoint=sdk-cli; cch=00000;
2026-09-06T23:58:49.304Z [DEBUG] [API REQUEST] /v1/messages x-client-request-id=9e535473-7eaa-471c-82f1-3da22fc75443 source=side_query
2026-09-06T23:58:50.585Z [INFO] [Stall] classifier_request_finished reqId=ad3d4f00-434c-4a44-8a3c-784a49d8814f tool=Bash stage=xml_s1 outcome=ok durationMs=1283
2026-09-06T23:58:50.589Z [INFO] [Stall] tool_dispatch_start tool=Bash toolUseId=toolu_018PQZWShYhjiTqke6onHMkf permissionDecisionMs=1292
2026-09-06T23:58:50.591Z [DEBUG] Spawning shell without login (-l flag skipped)
2026-09-06T23:58:50.637Z [INFO] [Stall] tool_dispatch_end tool=Bash toolUseId=toolu_018PQZWShYhjiTqke6onHMkf outcome=ok durationMs=48
2026-09-06T23:58:50.638Z [DEBUG] autocompact: tokens=[REDACTED] level=ok effectiveWindow=980000
2026-09-06T23:58:50.639Z [DEBUG] Tool search disabled: ToolSearchTool is not available (may have been disallowed via disallowedTools).
2026-09-06T23:58:50.639Z [DEBUG] attribution header x-anthropic-billing-header: cc_version=2.1.263.992; cc_entrypoint=sdk-cli; cch=00000; cc_prev_req=req_011Ceo6NppLmjKjozK5NemEv; cc_prompt_id=51ed5dfe-6e13-480f-82d9-c21bda316023;
2026-09-06T23:58:50.640Z [DEBUG] Fast mode unavailable: Fast mode is not available in the Agent SDK
2026-09-06T23:58:50.640Z [DEBUG] Fast mode unavailable: Fast mode is not available in the Agent SDK
2026-09-06T23:58:50.640Z [DEBUG] Fast mode unavailable: Fast mode is not available in the Agent SDK
2026-09-06T23:58:50.641Z [DEBUG] [API:timing] dispatching to firstParty model=claude-sonnet-5
2026-09-06T23:58:50.641Z [DEBUG] [API REQUEST] /v1/messages x-client-request-id=235926c7-5784-4339-a9b9-1d55056c9c0f source=sdk
2026-09-06T23:58:51.462Z [DEBUG] Stream started - received first chunk
2026-09-06T23:58:51.462Z [DEBUG] [API:timing] first byte after 821ms
2026-09-06T23:58:53.399Z [DEBUG] "Permission suggestions for Bash: [\n  {\n    \"type\": \"addRules\",\n    \"rules\": [\n      {\n        \"toolName\": \"Bash\",\n        \"ruleContent\": \"python3 -\"\n      }\n    ],\n    \"behavior\": \"allow\",\n    \"destination\": \"localSettings\"\n  }\n]"
2026-09-06T23:58:53.400Z [DEBUG] [auto-mode] context comparison: mainLoopTokens=[REDACTED] classifierChars=131783 classifierTokensEst=[REDACTED] (sys=126435 tools=2409 user=2939) transcriptEntries=15 messages=58
2026-09-06T23:58:53.400Z [DEBUG] [auto-mode] new action being classified: {"Bash":"python3 - <<'EOF'\nimport json\nd = json.load(open(\"backend/app/schemas/ad_extraction_v4.schema.json\"))\ndefs = d[\"$defs\"]\nprint(json.dumps(defs.get(\"authoritativeCorrection\", defs.get(\"authoritativeCorrections\",\"MISSING\")), indent=2)[:3000])\nEOF\n"}
2026-09-06T23:58:53.401Z [INFO] [Stall] classifier_request_started reqId=51c142e3-0e5d-4fb3-b4e2-83059db3d1e1 tool=Bash model=claude-sonnet-5[1m] stage=xml_s1 promptTokensEst=[REDACTED]
2026-09-06T23:58:53.401Z [DEBUG] attribution header x-anthropic-billing-header: cc_version=2.1.263.b6e; cc_entrypoint=sdk-cli; cch=00000;
2026-09-06T23:58:53.401Z [DEBUG] [API REQUEST] /v1/messages x-client-request-id=262b4074-722f-428d-a9c4-ce2865fc4ba0 source=side_query
2026-09-06T23:58:54.704Z [INFO] [Stall] classifier_request_finished reqId=51c142e3-0e5d-4fb3-b4e2-83059db3d1e1 tool=Bash stage=xml_s1 outcome=ok durationMs=1303
2026-09-06T23:58:54.707Z [INFO] [Stall] tool_dispatch_start tool=Bash toolUseId=toolu_01DSvnzvmVgBryqdt6xQgHiL permissionDecisionMs=1308
2026-09-06T23:58:54.709Z [DEBUG] Spawning shell without login (-l flag skipped)
2026-09-06T23:58:54.762Z [INFO] [Stall] tool_dispatch_end tool=Bash toolUseId=toolu_01DSvnzvmVgBryqdt6xQgHiL outcome=ok durationMs=55
2026-09-06T23:58:54.765Z [DEBUG] autocompact: tokens=[REDACTED] level=ok effectiveWindow=980000
2026-09-06T23:58:54.765Z [DEBUG] Tool search disabled: ToolSearchTool is not available (may have been disallowed via disallowedTools).
2026-09-06T23:58:54.766Z [DEBUG] attribution header x-anthropic-billing-header: cc_version=2.1.263.992; cc_entrypoint=sdk-cli; cch=00000; cc_prev_req=req_011Ceo6P3aoD1LhtpSi6dheP; cc_prompt_id=51ed5dfe-6e13-480f-82d9-c21bda316023;
2026-09-06T23:58:54.766Z [DEBUG] Fast mode unavailable: Fast mode is not available in the Agent SDK
2026-09-06T23:58:54.766Z [DEBUG] Fast mode unavailable: Fast mode is not available in the Agent SDK
2026-09-06T23:58:54.767Z [DEBUG] Fast mode unavailable: Fast mode is not available in the Agent SDK
2026-09-06T23:58:54.767Z [DEBUG] [API:timing] dispatching to firstParty model=claude-sonnet-5
2026-09-06T23:58:54.768Z [DEBUG] [API REQUEST] /v1/messages x-client-request-id=994fe4d3-3c5d-4d0e-b81d-29572a27d323 source=sdk
2026-09-06T23:58:55.639Z [DEBUG] Stream started - received first chunk
2026-09-06T23:58:55.639Z [DEBUG] [API:timing] first byte after 872ms
2026-09-06T23:59:22.465Z [DEBUG] Permission suggestions for Bash: []
2026-09-06T23:59:22.467Z [DEBUG] [auto-mode] context comparison: mainLoopTokens=[REDACTED] classifierChars=132460 classifierTokensEst=[REDACTED] (sys=126435 tools=3086 user=2939) transcriptEntries=16 messages=61
2026-09-06T23:59:22.467Z [DEBUG] [auto-mode] new action being classified: {"Bash":"python3 - <<'EOF'\nstrings = {\n \"proposal\": \"paprnav:ad_extraction_v4:proposal:paprnav-ad-v4-c14n-2\",\n \"evidence bindings\": \"paprnav:ad_extraction_v4:evidence-bindings:2\",\n \"candidate event\": \"paprnav:ad_extraction_v4:candidate-event:2\",\n \"submission\": \"paprnav:ad_extraction_v4:submission:2\",\n \"submission relationship\": \"paprnav:ad_extraction_v4:submission-relationship:2\",\n \"subtree\": \"paprnav:ad_extraction_v4:applicability-subtree:paprnav-ad-v4-c14n-2\",\n …
2026-09-06T23:59:22.467Z [INFO] [Stall] classifier_request_started reqId=790b389c-df3b-4c4d-8864-8359c2473dbe tool=Bash model=claude-sonnet-5[1m] stage=xml_s1 promptTokensEst=[REDACTED]
2026-09-06T23:59:22.468Z [DEBUG] attribution header x-anthropic-billing-header: cc_version=2.1.263.b6e; cc_entrypoint=sdk-cli; cch=00000;
2026-09-06T23:59:22.468Z [DEBUG] [API REQUEST] /v1/messages x-client-request-id=95eecc18-6416-4c43-8e56-af8d209e332b source=side_query
2026-09-06T23:59:23.937Z [INFO] [Stall] classifier_request_finished reqId=790b389c-df3b-4c4d-8864-8359c2473dbe tool=Bash stage=xml_s1 outcome=ok durationMs=1470
2026-09-06T23:59:23.939Z [INFO] [Stall] tool_dispatch_start tool=Bash toolUseId=toolu_01Y72D7naUMjFGfzJCABaXXM permissionDecisionMs=1478
2026-09-06T23:59:23.942Z [DEBUG] Spawning shell without login (-l flag skipped)
2026-09-06T23:59:23.991Z [INFO] [Stall] tool_dispatch_end tool=Bash toolUseId=toolu_01Y72D7naUMjFGfzJCABaXXM outcome=ok durationMs=52
2026-09-06T23:59:23.993Z [DEBUG] autocompact: tokens=[REDACTED] level=ok effectiveWindow=980000
2026-09-06T23:59:23.993Z [DEBUG] Tool search disabled: ToolSearchTool is not available (may have been disallowed via disallowedTools).
2026-09-06T23:59:23.994Z [DEBUG] attribution header x-anthropic-billing-header: cc_version=2.1.263.992; cc_entrypoint=sdk-cli; cch=00000; cc_prev_req=req_011Ceo6PMDCNyLCLcZ19U18x; cc_prompt_id=51ed5dfe-6e13-480f-82d9-c21bda316023;
2026-09-06T23:59:23.994Z [DEBUG] Fast mode unavailable: Fast mode is not available in the Agent SDK
2026-09-06T23:59:23.995Z [DEBUG] Fast mode unavailable: Fast mode is not available in the Agent SDK
2026-09-06T23:59:23.995Z [DEBUG] Fast mode unavailable: Fast mode is not available in the Agent SDK
2026-09-06T23:59:23.995Z [DEBUG] [API:timing] dispatching to firstParty model=claude-sonnet-5
2026-09-06T23:59:23.996Z [DEBUG] [API REQUEST] /v1/messages x-client-request-id=e1187eaf-7144-4480-9a37-c8357bbd087b source=sdk
2026-09-06T23:59:24.826Z [DEBUG] Stream started - received first chunk
2026-09-06T23:59:24.826Z [DEBUG] [API:timing] first byte after 831ms
2026-09-06T23:59:27.451Z [INFO] [Stall] tool_dispatch_start tool=Bash toolUseId=toolu_0174o2FvfsDgb75w3gxq9sJ3 permissionDecisionMs=3
2026-09-06T23:59:27.454Z [DEBUG] Spawning shell without login (-l flag skipped)
2026-09-06T23:59:27.489Z [INFO] [Stall] tool_dispatch_end tool=Bash toolUseId=toolu_0174o2FvfsDgb75w3gxq9sJ3 outcome=ok durationMs=38
2026-09-06T23:59:27.490Z [DEBUG] autocompact: tokens=[REDACTED] level=ok effectiveWindow=980000
2026-09-06T23:59:27.491Z [DEBUG] Tool search disabled: ToolSearchTool is not available (may have been disallowed via disallowedTools).
2026-09-06T23:59:27.492Z [DEBUG] attribution header x-anthropic-billing-header: cc_version=2.1.263.992; cc_entrypoint=sdk-cli; cch=00000; cc_prev_req=req_011Ceo6RWBkZ72hyawHgHonM; cc_prompt_id=51ed5dfe-6e13-480f-82d9-c21bda316023;
2026-09-06T23:59:27.492Z [DEBUG] Fast mode unavailable: Fast mode is not available in the Agent SDK
2026-09-06T23:59:27.492Z [DEBUG] Fast mode unavailable: Fast mode is not available in the Agent SDK
2026-09-06T23:59:27.492Z [DEBUG] Fast mode unavailable: Fast mode is not available in the Agent SDK
2026-09-06T23:59:27.493Z [DEBUG] [API:timing] dispatching to firstParty model=claude-sonnet-5
2026-09-06T23:59:27.493Z [DEBUG] [API REQUEST] /v1/messages x-client-request-id=48be5f57-ffa4-46ba-acc8-beb63c798013 source=sdk
2026-09-06T23:59:28.125Z [DEBUG] Stream started - received first chunk
2026-09-06T23:59:28.125Z [DEBUG] [API:timing] first byte after 632ms
2026-09-06T23:59:31.692Z [DEBUG] "Permission suggestions for Bash: [\n  {\n    \"type\": \"addRules\",\n    \"rules\": [\n      {\n        \"toolName\": \"Bash\",\n        \"ruleContent\": \"python3 -\"\n      }\n    ],\n    \"behavior\": \"allow\",\n    \"destination\": \"localSettings\"\n  }\n]"
2026-09-06T23:59:31.693Z [DEBUG] [auto-mode] context comparison: mainLoopTokens=[REDACTED] classifierChars=132984 classifierTokensEst=[REDACTED] (sys=126435 tools=3610 user=2939) transcriptEntries=18 messages=67
2026-09-06T23:59:31.693Z [DEBUG] [auto-mode] new action being classified: {"Bash":"python3 - <<'EOF'\nimport json\nd = json.load(open(\"/Users/hostiletakeover/Projects/paprnav/backend/app/schemas/ad_extraction_v4.schema.json\"))\ndefs = d[\"$defs\"]\nfor k in [\"conditionSubject\",\"applicabilitySearchHint\",\"normalizedIdentity\",\"manufacturerValue\"]:\n    if k in defs:\n        print(\"===\", k)\n        print(json.dumps(defs[k], indent=2)[:2000])\nEOF\n"}
2026-09-06T23:59:31.693Z [INFO] [Stall] classifier_request_started reqId=d6c6dac5-752f-4967-bab7-2797c526a955 tool=Bash model=claude-sonnet-5[1m] stage=xml_s1 promptTokensEst=[REDACTED]
2026-09-06T23:59:31.695Z [DEBUG] attribution header x-anthropic-billing-header: cc_version=2.1.263.b6e; cc_entrypoint=sdk-cli; cch=00000;
2026-09-06T23:59:31.695Z [DEBUG] [API REQUEST] /v1/messages x-client-request-id=7aa9ee5c-c03b-4710-879b-37a0d099fdcd source=side_query
2026-09-06T23:59:32.937Z [INFO] [Stall] classifier_request_finished reqId=d6c6dac5-752f-4967-bab7-2797c526a955 tool=Bash stage=xml_s1 outcome=ok durationMs=1244
2026-09-06T23:59:32.939Z [INFO] [Stall] tool_dispatch_start tool=Bash toolUseId=toolu_01LsfJG1FJdJ6aDo3TRJaqCd permissionDecisionMs=1250
2026-09-06T23:59:32.940Z [DEBUG] Spawning shell without login (-l flag skipped)
2026-09-06T23:59:32.995Z [INFO] [Stall] tool_dispatch_end tool=Bash toolUseId=toolu_01LsfJG1FJdJ6aDo3TRJaqCd outcome=ok durationMs=56
2026-09-06T23:59:32.997Z [DEBUG] autocompact: tokens=[REDACTED] level=ok effectiveWindow=980000
2026-09-06T23:59:32.997Z [DEBUG] Tool search disabled: ToolSearchTool is not available (may have been disallowed via disallowedTools).
2026-09-06T23:59:32.998Z [DEBUG] attribution header x-anthropic-billing-header: cc_version=2.1.263.992; cc_entrypoint=sdk-cli; cch=00000; cc_prev_req=req_011Ceo6Rm8BRBZkSibByefwo; cc_prompt_id=51ed5dfe-6e13-480f-82d9-c21bda316023;
2026-09-06T23:59:32.998Z [DEBUG] Fast mode unavailable: Fast mode is not available in the Agent SDK
2026-09-06T23:59:32.998Z [DEBUG] Fast mode unavailable: Fast mode is not available in the Agent SDK
2026-09-06T23:59:32.999Z [DEBUG] Fast mode unavailable: Fast mode is not available in the Agent SDK
2026-09-06T23:59:32.999Z [DEBUG] [API:timing] dispatching to firstParty model=claude-sonnet-5
2026-09-06T23:59:33.000Z [DEBUG] [API REQUEST] /v1/messages x-client-request-id=4d46bf2f-6bf7-4237-8cb4-3b56d547877f source=sdk
2026-09-06T23:59:33.922Z [DEBUG] Stream started - received first chunk
2026-09-06T23:59:33.922Z [DEBUG] [API:timing] first byte after 923ms
2026-09-06T23:59:36.641Z [DEBUG] "Permission suggestions for Bash: [\n  {\n    \"type\": \"addRules\",\n    \"rules\": [\n      {\n        \"toolName\": \"Bash\",\n        \"ruleContent\": \"python3 -\"\n      }\n    ],\n    \"behavior\": \"allow\",\n    \"destination\": \"localSettings\"\n  }\n]"
2026-09-06T23:59:36.645Z [DEBUG] [auto-mode] context comparison: mainLoopTokens=[REDACTED] classifierChars=133228 classifierTokensEst=[REDACTED] (sys=126435 tools=3854 user=2939) transcriptEntries=19 messages=70
2026-09-06T23:59:36.645Z [DEBUG] [auto-mode] new action being classified: {"Bash":"python3 - <<'EOF'\nimport json\nd = json.load(open(\"backend/tests/fixtures/ad_v4_calibration/2002-13-04.proposal.json\"))\np = d[\"proposal\"]\nimport pprint\nhints = p.get(\"applicabilitySearchHints\")\npprint.pprint(hints)\nEOF\n"}
2026-09-06T23:59:36.645Z [INFO] [Stall] classifier_request_started reqId=abdc55f3-ff06-4363-8c95-1c862016c160 tool=Bash model=claude-sonnet-5[1m] stage=xml_s1 promptTokensEst=[REDACTED]
2026-09-06T23:59:36.646Z [DEBUG] attribution header x-anthropic-billing-header: cc_version=2.1.263.b6e; cc_entrypoint=sdk-cli; cch=00000;
2026-09-06T23:59:36.646Z [DEBUG] [API REQUEST] /v1/messages x-client-request-id=39de7335-b994-487e-b7d7-6eb984f609e4 source=side_query
2026-09-06T23:59:37.934Z [INFO] [Stall] classifier_request_finished reqId=abdc55f3-ff06-4363-8c95-1c862016c160 tool=Bash stage=xml_s1 outcome=ok durationMs=1289
2026-09-06T23:59:37.938Z [INFO] [Stall] tool_dispatch_start tool=Bash toolUseId=toolu_01CmVeZQQUQtSaJiQVR5tGZo permissionDecisionMs=1298
2026-09-06T23:59:37.940Z [DEBUG] Spawning shell without login (-l flag skipped)
2026-09-06T23:59:38.006Z [INFO] [Stall] tool_dispatch_end tool=Bash toolUseId=toolu_01CmVeZQQUQtSaJiQVR5tGZo outcome=ok durationMs=68
2026-09-06T23:59:38.008Z [DEBUG] autocompact: tokens=[REDACTED] level=ok effectiveWindow=980000
2026-09-06T23:59:38.008Z [DEBUG] Tool search disabled: ToolSearchTool is not available (may have been disallowed via disallowedTools).
2026-09-06T23:59:38.009Z [DEBUG] attribution header x-anthropic-billing-header: cc_version=2.1.263.992; cc_entrypoint=sdk-cli; cch=00000; cc_prev_req=req_011Ceo6SAfHJFwgCB7E29Kse; cc_prompt_id=51ed5dfe-6e13-480f-82d9-c21bda316023;
2026-09-06T23:59:38.009Z [DEBUG] Fast mode unavailable: Fast mode is not available in the Agent SDK
2026-09-06T23:59:38.009Z [DEBUG] Fast mode unavailable: Fast mode is not available in the Agent SDK
2026-09-06T23:59:38.010Z [DEBUG] Fast mode unavailable: Fast mode is not available in the Agent SDK
2026-09-06T23:59:38.010Z [DEBUG] [API:timing] dispatching to firstParty model=claude-sonnet-5
2026-09-06T23:59:38.010Z [DEBUG] [API REQUEST] /v1/messages x-client-request-id=20c5306b-ed00-4269-8425-80612d00d881 source=sdk
2026-09-06T23:59:38.733Z [DEBUG] Stream started - received first chunk
2026-09-06T23:59:38.733Z [DEBUG] [API:timing] first byte after 724ms
2026-09-06T23:59:44.337Z [INFO] [Stall] tool_dispatch_start tool=Bash toolUseId=toolu_01HfDdLxgvdp2NDhnuNwV3Pa permissionDecisionMs=4
2026-09-06T23:59:44.340Z [DEBUG] Spawning shell without login (-l flag skipped)
2026-09-06T23:59:44.395Z [INFO] [Stall] tool_dispatch_end tool=Bash toolUseId=toolu_01HfDdLxgvdp2NDhnuNwV3Pa outcome=ok durationMs=58
2026-09-06T23:59:44.396Z [DEBUG] autocompact: tokens=[REDACTED] level=ok effectiveWindow=980000
2026-09-06T23:59:44.397Z [DEBUG] Tool search disabled: ToolSearchTool is not available (may have been disallowed via disallowedTools).
2026-09-06T23:59:44.398Z [DEBUG] attribution header x-anthropic-billing-header: cc_version=2.1.263.992; cc_entrypoint=sdk-cli; cch=00000; cc_prev_req=req_011Ceo6SY6Nkmxegq6xEb9Tj; cc_prompt_id=51ed5dfe-6e13-480f-82d9-c21bda316023;
2026-09-06T23:59:44.398Z [DEBUG] Fast mode unavailable: Fast mode is not available in the Agent SDK
2026-09-06T23:59:44.398Z [DEBUG] Fast mode unavailable: Fast mode is not available in the Agent SDK
2026-09-06T23:59:44.399Z [DEBUG] Fast mode unavailable: Fast mode is not available in the Agent SDK
2026-09-06T23:59:44.399Z [DEBUG] [API:timing] dispatching to firstParty model=claude-sonnet-5
2026-09-06T23:59:44.400Z [DEBUG] [API REQUEST] /v1/messages x-client-request-id=4f23be96-a7ea-4dc1-9d5c-c7a4083b904a source=sdk
2026-09-06T23:59:45.099Z [DEBUG] Stream started - received first chunk
2026-09-06T23:59:45.099Z [DEBUG] [API:timing] first byte after 700ms
2026-09-06T23:59:46.624Z [INFO] [Stall] tool_dispatch_start tool=Bash toolUseId=toolu_011UKmLdsfmCeYGoDVsdjfQo permissionDecisionMs=2
2026-09-06T23:59:46.627Z [DEBUG] Spawning shell without login (-l flag skipped)
2026-09-06T23:59:46.659Z [INFO] [Stall] tool_dispatch_end tool=Bash toolUseId=toolu_011UKmLdsfmCeYGoDVsdjfQo outcome=ok durationMs=35
2026-09-06T23:59:46.660Z [DEBUG] autocompact: tokens=[REDACTED] level=ok effectiveWindow=980000
2026-09-06T23:59:46.661Z [DEBUG] Tool search disabled: ToolSearchTool is not available (may have been disallowed via disallowedTools).
2026-09-06T23:59:46.662Z [DEBUG] attribution header x-anthropic-billing-header: cc_version=2.1.263.992; cc_entrypoint=sdk-cli; cch=00000; cc_prev_req=req_011Ceo6T1Sg8TH2PE1kWUZWH; cc_prompt_id=51ed5dfe-6e13-480f-82d9-c21bda316023;
2026-09-06T23:59:46.662Z [DEBUG] Fast mode unavailable: Fast mode is not available in the Agent SDK
2026-09-06T23:59:46.662Z [DEBUG] Fast mode unavailable: Fast mode is not available in the Agent SDK
2026-09-06T23:59:46.662Z [DEBUG] Fast mode unavailable: Fast mode is not available in the Agent SDK
2026-09-06T23:59:46.662Z [DEBUG] [API:timing] dispatching to firstParty model=claude-sonnet-5
2026-09-06T23:59:46.663Z [DEBUG] [API REQUEST] /v1/messages x-client-request-id=8931813f-8f7a-46bf-8ead-03b2db6cd3cd source=sdk
2026-09-06T23:59:47.958Z [DEBUG] Stream started - received first chunk
2026-09-06T23:59:47.958Z [DEBUG] [API:timing] first byte after 1296ms
2026-09-07T00:00:00.477Z [DEBUG] "Permission suggestions for Bash: [\n  {\n    \"type\": \"addRules\",\n    \"rules\": [\n      {\n        \"toolName\": \"Bash\",\n        \"ruleContent\": \"python3 -\"\n      }\n    ],\n    \"behavior\": \"allow\",\n    \"destination\": \"localSettings\"\n  }\n]"
2026-09-07T00:00:00.479Z [DEBUG] [auto-mode] context comparison: mainLoopTokens=[REDACTED] classifierChars=133723 classifierTokensEst=[REDACTED] (sys=126435 tools=4349 user=2939) transcriptEntries=22 messages=79
2026-09-07T00:00:00.479Z [DEBUG] [auto-mode] new action being classified: {"Bash":"python3 - <<'EOF'\nimport json\nd = json.load(open(\"/Users/hostiletakeover/Projects/paprnav/backend/app/schemas/ad_extraction_v4.schema.json\"))\ndefs = d[\"$defs\"]\nfor k in defs:\n    if \"expression\" in k.lower() or \"rule\" in k.lower():\n        print(k)\nEOF\n"}
2026-09-07T00:00:00.479Z [INFO] [Stall] classifier_request_started reqId=285c4b92-def6-47b5-86fe-a686c11d2c06 tool=Bash model=claude-sonnet-5[1m] stage=xml_s1 promptTokensEst=[REDACTED]
2026-09-07T00:00:00.484Z [DEBUG] attribution header x-anthropic-billing-header: cc_version=2.1.263.b6e; cc_entrypoint=sdk-cli; cch=00000;
2026-09-07T00:00:00.485Z [DEBUG] [API REQUEST] /v1/messages x-client-request-id=bb52fe19-7fb0-41d5-8345-b4b7f641e89b source=side_query
2026-09-07T00:00:01.882Z [INFO] [Stall] classifier_request_finished reqId=285c4b92-def6-47b5-86fe-a686c11d2c06 tool=Bash stage=xml_s1 outcome=ok durationMs=1403
2026-09-07T00:00:01.883Z [INFO] [Stall] tool_dispatch_start tool=Bash toolUseId=toolu_01NyFGZ1GnQbRmbHFYB6W8nE permissionDecisionMs=1407
2026-09-07T00:00:01.884Z [DEBUG] Spawning shell without login (-l flag skipped)
2026-09-07T00:00:01.945Z [INFO] [Stall] tool_dispatch_end tool=Bash toolUseId=toolu_01NyFGZ1GnQbRmbHFYB6W8nE outcome=ok durationMs=62
2026-09-07T00:00:01.947Z [DEBUG] autocompact: tokens=[REDACTED] level=ok effectiveWindow=980000
2026-09-07T00:00:01.947Z [DEBUG] Tool search disabled: ToolSearchTool is not available (may have been disallowed via disallowedTools).
2026-09-07T00:00:01.948Z [DEBUG] attribution header x-anthropic-billing-header: cc_version=2.1.263.992; cc_entrypoint=sdk-cli; cch=00000; cc_prev_req=req_011Ceo6TB8Ldj65aAmuTDA52; cc_prompt_id=51ed5dfe-6e13-480f-82d9-c21bda316023;
2026-09-07T00:00:01.948Z [DEBUG] Fast mode unavailable: Fast mode is not available in the Agent SDK
2026-09-07T00:00:01.949Z [DEBUG] Fast mode unavailable: Fast mode is not available in the Agent SDK
2026-09-07T00:00:01.949Z [DEBUG] Fast mode unavailable: Fast mode is not available in the Agent SDK
2026-09-07T00:00:01.949Z [DEBUG] [API:timing] dispatching to firstParty model=claude-sonnet-5
2026-09-07T00:00:01.950Z [DEBUG] [API REQUEST] /v1/messages x-client-request-id=9d4d38b5-4b0e-4b32-8d37-6363c37183f9 source=sdk
2026-09-07T00:00:02.975Z [DEBUG] Stream started - received first chunk
2026-09-07T00:00:02.975Z [DEBUG] [API:timing] first byte after 1026ms
2026-09-07T00:00:04.040Z [DEBUG] "Permission suggestions for Bash: [\n  {\n    \"type\": \"addRules\",\n    \"rules\": [\n      {\n        \"toolName\": \"Bash\",\n        \"ruleContent\": \"python3 -\"\n      }\n    ],\n    \"behavior\": \"allow\",\n    \"destination\": \"localSettings\"\n  }\n]"
2026-09-07T00:00:04.042Z [DEBUG] [auto-mode] context comparison: mainLoopTokens=[REDACTED] classifierChars=134034 classifierTokensEst=[REDACTED] (sys=126435 tools=4660 user=2939) transcriptEntries=23 messages=82
2026-09-07T00:00:04.042Z [DEBUG] [auto-mode] new action being classified: {"Bash":"python3 - <<'EOF'\nimport json\nd = json.load(open(\"/Users/hostiletakeover/Projects/paprnav/backend/app/schemas/ad_extraction_v4.schema.json\"))\ndefs = d[\"$defs\"]\nprint(json.dumps(defs[\"expression\"], indent=2))\nprint(\"====\")\nprint(json.dumps(defs[\"applicabilityRule\"], indent=2))\nEOF\n"}
2026-09-07T00:00:04.042Z [INFO] [Stall] classifier_request_started reqId=17cd1982-84b7-4d61-8f73-63b1301b47f6 tool=Bash model=claude-sonnet-5[1m] stage=xml_s1 promptTokensEst=[REDACTED]
2026-09-07T00:00:04.043Z [DEBUG] attribution header x-anthropic-billing-header: cc_version=2.1.263.b6e; cc_entrypoint=sdk-cli; cch=00000;
2026-09-07T00:00:04.043Z [DEBUG] [API REQUEST] /v1/messages x-client-request-id=2f892568-8d11-4039-a9f0-241d88b139af source=side_query
2026-09-07T00:00:05.382Z [INFO] [Stall] classifier_request_finished reqId=17cd1982-84b7-4d61-8f73-63b1301b47f6 tool=Bash stage=xml_s1 outcome=ok durationMs=1340
2026-09-07T00:00:05.384Z [INFO] [Stall] tool_dispatch_start tool=Bash toolUseId=toolu_01LnPvUpDPBBeBrGoYLy9SLu permissionDecisionMs=1346
2026-09-07T00:00:05.386Z [DEBUG] Spawning shell without login (-l flag skipped)
2026-09-07T00:00:05.465Z [INFO] [Stall] tool_dispatch_end tool=Bash toolUseId=toolu_01LnPvUpDPBBeBrGoYLy9SLu outcome=ok durationMs=81
2026-09-07T00:00:05.467Z [DEBUG] autocompact: tokens=[REDACTED] level=ok effectiveWindow=980000
2026-09-07T00:00:05.467Z [DEBUG] Tool search disabled: ToolSearchTool is not available (may have been disallowed via disallowedTools).
2026-09-07T00:00:05.468Z [DEBUG] attribution header x-anthropic-billing-header: cc_version=2.1.263.992; cc_entrypoint=sdk-cli; cch=00000; cc_prev_req=req_011Ceo6UJSPxryS5mTX9dBVp; cc_prompt_id=51ed5dfe-6e13-480f-82d9-c21bda316023;
2026-09-07T00:00:05.468Z [DEBUG] Fast mode unavailable: Fast mode is not available in the Agent SDK
2026-09-07T00:00:05.468Z [DEBUG] Fast mode unavailable: Fast mode is not available in the Agent SDK
2026-09-07T00:00:05.469Z [DEBUG] Fast mode unavailable: Fast mode is not available in the Agent SDK
2026-09-07T00:00:05.469Z [DEBUG] [API:timing] dispatching to firstParty model=claude-sonnet-5
2026-09-07T00:00:05.470Z [DEBUG] [API REQUEST] /v1/messages x-client-request-id=5d2f9f93-7bd0-4e68-946f-d8afd1a0e50a source=sdk
2026-09-07T00:00:06.767Z [DEBUG] Stream started - received first chunk
2026-09-07T00:00:06.767Z [DEBUG] [API:timing] first byte after 1298ms
2026-09-07T00:00:55.012Z [DEBUG] "Permission suggestions for Bash: [\n  {\n    \"type\": \"addRules\",\n    \"rules\": [\n      {\n        \"toolName\": \"Bash\",\n        \"ruleContent\": \"python3 -\"\n      }\n    ],\n    \"behavior\": \"allow\",\n    \"destination\": \"localSettings\"\n  }\n]"
2026-09-07T00:00:55.014Z [DEBUG] [auto-mode] context comparison: mainLoopTokens=[REDACTED] classifierChars=134262 classifierTokensEst=[REDACTED] (sys=126435 tools=4888 user=2939) transcriptEntries=24 messages=84
2026-09-07T00:00:55.014Z [DEBUG] [auto-mode] new action being classified: {"Bash":"python3 - <<'EOF'\nimport json\nd = json.load(open(\"backend/tests/fixtures/ad_v4_calibration/2008-26-10.proposal.json\"))\np = d[\"proposal\"]\nprint(json.dumps(p.get(\"authoritativeCorrections\"), indent=2))\nEOF\n"}
2026-09-07T00:00:55.014Z [INFO] [Stall] classifier_request_started reqId=411cf638-208f-4282-a88a-17724b4588cf tool=Bash model=claude-sonnet-5[1m] stage=xml_s1 promptTokensEst=[REDACTED]
2026-09-07T00:00:55.016Z [DEBUG] attribution header x-anthropic-billing-header: cc_version=2.1.263.b6e; cc_entrypoint=sdk-cli; cch=00000;
2026-09-07T00:00:55.017Z [DEBUG] [API REQUEST] /v1/messages x-client-request-id=6f7f4bf2-4148-4634-844b-e3de9dbc5035 source=side_query
2026-09-07T00:00:56.410Z [INFO] [Stall] classifier_request_finished reqId=411cf638-208f-4282-a88a-17724b4588cf tool=Bash stage=xml_s1 outcome=ok durationMs=1396
2026-09-07T00:00:56.413Z [INFO] [Stall] tool_dispatch_start tool=Bash toolUseId=toolu_01HYsVfwQRNw1QCMELS6mPRS permissionDecisionMs=1402
2026-09-07T00:00:56.415Z [DEBUG] Spawning shell without login (-l flag skipped)
2026-09-07T00:00:56.479Z [INFO] [Stall] tool_dispatch_end tool=Bash toolUseId=toolu_01HYsVfwQRNw1QCMELS6mPRS outcome=ok durationMs=66
2026-09-07T00:00:56.480Z [DEBUG] autocompact: tokens=[REDACTED] level=ok effectiveWindow=980000
2026-09-07T00:00:56.481Z [DEBUG] Tool search disabled: ToolSearchTool is not available (may have been disallowed via disallowedTools).
2026-09-07T00:00:56.482Z [DEBUG] attribution header x-anthropic-billing-header: cc_version=2.1.263.992; cc_entrypoint=sdk-cli; cch=00000; cc_prev_req=req_011Ceo6UZWmFHqzi94N7LHip; cc_prompt_id=51ed5dfe-6e13-480f-82d9-c21bda316023;
2026-09-07T00:00:56.482Z [DEBUG] Fast mode unavailable: Fast mode is not available in the Agent SDK
2026-09-07T00:00:56.482Z [DEBUG] Fast mode unavailable: Fast mode is not available in the Agent SDK
2026-09-07T00:00:56.483Z [DEBUG] Fast mode unavailable: Fast mode is not available in the Agent SDK
2026-09-07T00:00:56.483Z [DEBUG] [API:timing] dispatching to firstParty model=claude-sonnet-5
2026-09-07T00:00:56.484Z [DEBUG] [API REQUEST] /v1/messages x-client-request-id=e2ed8ea9-7bb8-4636-8b44-0b2a9e3b40a1 source=sdk
2026-09-07T00:00:57.625Z [DEBUG] Stream started - received first chunk
2026-09-07T00:00:57.625Z [DEBUG] [API:timing] first byte after 1142ms
2026-09-07T00:01:00.486Z [DEBUG] "Permission suggestions for Bash: [\n  {\n    \"type\": \"addRules\",\n    \"rules\": [\n      {\n        \"toolName\": \"Bash\",\n        \"ruleContent\": \"python3 -\"\n      }\n    ],\n    \"behavior\": \"allow\",\n    \"destination\": \"localSettings\"\n  }\n]"
2026-09-07T00:01:00.487Z [DEBUG] [auto-mode] context comparison: mainLoopTokens=[REDACTED] classifierChars=134506 classifierTokensEst=[REDACTED] (sys=126435 tools=5132 user=2939) transcriptEntries=25 messages=87
2026-09-07T00:01:00.487Z [DEBUG] [auto-mode] new action being classified: {"Bash":"python3 - <<'EOF'\nimport json\nd = json.load(open(\"/Users/hostiletakeover/Projects/paprnav/backend/app/schemas/ad_extraction_v4.schema.json\"))\ndefs = d[\"$defs\"]\nprint(json.dumps(defs[\"changedSemanticRef\"], indent=2))\nEOF\n"}
2026-09-07T00:01:00.488Z [INFO] [Stall] classifier_request_started reqId=f232f469-d9c4-4e67-8fd9-afb4db2e68bc tool=Bash model=claude-sonnet-5[1m] stage=xml_s1 promptTokensEst=[REDACTED]
2026-09-07T00:01:00.488Z [DEBUG] attribution header x-anthropic-billing-header: cc_version=2.1.263.b6e; cc_entrypoint=sdk-cli; cch=00000;
2026-09-07T00:01:00.489Z [DEBUG] [API REQUEST] /v1/messages x-client-request-id=dddc6a7f-0b01-4525-a5eb-730bdf1c484f source=side_query
2026-09-07T00:01:01.848Z [INFO] [Stall] classifier_request_finished reqId=f232f469-d9c4-4e67-8fd9-afb4db2e68bc tool=Bash stage=xml_s1 outcome=ok durationMs=1360
2026-09-07T00:01:01.852Z [INFO] [Stall] tool_dispatch_start tool=Bash toolUseId=toolu_01FxZdmCLPehUZX9PesfJ1VK permissionDecisionMs=1369
2026-09-07T00:01:01.856Z [DEBUG] Spawning shell without login (-l flag skipped)
2026-09-07T00:01:01.903Z [INFO] [Stall] tool_dispatch_end tool=Bash toolUseId=toolu_01FxZdmCLPehUZX9PesfJ1VK outcome=ok durationMs=51
2026-09-07T00:01:01.904Z [DEBUG] autocompact: tokens=[REDACTED] level=ok effectiveWindow=980000
2026-09-07T00:01:01.905Z [DEBUG] Tool search disabled: ToolSearchTool is not available (may have been disallowed via disallowedTools).
2026-09-07T00:01:01.906Z [DEBUG] attribution header x-anthropic-billing-header: cc_version=2.1.263.992; cc_entrypoint=sdk-cli; cch=00000; cc_prev_req=req_011Ceo6YL1GfRdVFUFekB5a8; cc_prompt_id=51ed5dfe-6e13-480f-82d9-c21bda316023;
2026-09-07T00:01:01.906Z [DEBUG] Fast mode unavailable: Fast mode is not available in the Agent SDK
2026-09-07T00:01:01.906Z [DEBUG] Fast mode unavailable: Fast mode is not available in the Agent SDK
2026-09-07T00:01:01.907Z [DEBUG] Fast mode unavailable: Fast mode is not available in the Agent SDK
2026-09-07T00:01:01.907Z [DEBUG] [API:timing] dispatching to firstParty model=claude-sonnet-5
2026-09-07T00:01:01.907Z [DEBUG] [API REQUEST] /v1/messages x-client-request-id=65d9d87e-6a67-4ac2-a0f1-dfab546182fb source=sdk
2026-09-07T00:01:02.868Z [DEBUG] Stream started - received first chunk
2026-09-07T00:01:02.868Z [DEBUG] [API:timing] first byte after 961ms
2026-09-07T00:01:05.707Z [DEBUG] "Permission suggestions for Bash: [\n  {\n    \"type\": \"addRules\",\n    \"rules\": [\n      {\n        \"toolName\": \"Bash\",\n        \"ruleContent\": \"python3 -\"\n      }\n    ],\n    \"behavior\": \"allow\",\n    \"destination\": \"localSettings\"\n  }\n]"
2026-09-07T00:01:05.708Z [DEBUG] [auto-mode] context comparison: mainLoopTokens=[REDACTED] classifierChars=134802 classifierTokensEst=[REDACTED] (sys=126435 tools=5428 user=2939) transcriptEntries=26 messages=90
2026-09-07T00:01:05.708Z [DEBUG] [auto-mode] new action being classified: {"Bash":"python3 - <<'EOF'\nimport json\nd = json.load(open(\"/Users/hostiletakeover/Projects/paprnav/backend/app/schemas/ad_extraction_v4.schema.json\"))\ndefs = d[\"$defs\"]\nfor k in defs:\n    if \"hint\" in k.lower():\n        print(k)\n        print(json.dumps(defs[k], indent=2))\nEOF\n"}
2026-09-07T00:01:05.708Z [INFO] [Stall] classifier_request_started reqId=5a90957f-1300-4eb7-b1b1-178a73395934 tool=Bash model=claude-sonnet-5[1m] stage=xml_s1 promptTokensEst=[REDACTED]
2026-09-07T00:01:05.709Z [DEBUG] attribution header x-anthropic-billing-header: cc_version=2.1.263.b6e; cc_entrypoint=sdk-cli; cch=00000;
2026-09-07T00:01:05.710Z [DEBUG] [API REQUEST] /v1/messages x-client-request-id=50471913-79ac-42d8-b838-2bff3ff90a26 source=side_query
2026-09-07T00:01:07.061Z [INFO] [Stall] classifier_request_finished reqId=5a90957f-1300-4eb7-b1b1-178a73395934 tool=Bash stage=xml_s1 outcome=ok durationMs=1353
2026-09-07T00:01:07.064Z [INFO] [Stall] tool_dispatch_start tool=Bash toolUseId=toolu_01USF4Jfu3G8YTEx1oUeLPFs permissionDecisionMs=1361
2026-09-07T00:01:07.065Z [DEBUG] Spawning shell without login (-l flag skipped)
2026-09-07T00:01:07.113Z [INFO] [Stall] tool_dispatch_end tool=Bash toolUseId=toolu_01USF4Jfu3G8YTEx1oUeLPFs outcome=ok durationMs=49
2026-09-07T00:01:07.115Z [DEBUG] autocompact: tokens=[REDACTED] level=ok effectiveWindow=980000
2026-09-07T00:01:07.115Z [DEBUG] Tool search disabled: ToolSearchTool is not available (may have been disallowed via disallowedTools).
2026-09-07T00:01:07.116Z [DEBUG] attribution header x-anthropic-billing-header: cc_version=2.1.263.992; cc_entrypoint=sdk-cli; cch=00000; cc_prev_req=req_011Ceo6Yioy6Jms6XnauxyBR; cc_prompt_id=51ed5dfe-6e13-480f-82d9-c21bda316023;
2026-09-07T00:01:07.116Z [DEBUG] Fast mode unavailable: Fast mode is not available in the Agent SDK
2026-09-07T00:01:07.116Z [DEBUG] Fast mode unavailable: Fast mode is not available in the Agent SDK
2026-09-07T00:01:07.117Z [DEBUG] Fast mode unavailable: Fast mode is not available in the Agent SDK
2026-09-07T00:01:07.117Z [DEBUG] [API:timing] dispatching to firstParty model=claude-sonnet-5
2026-09-07T00:01:07.118Z [DEBUG] [API REQUEST] /v1/messages x-client-request-id=0b711d4b-9df5-4c51-a25b-6a0f7a8a486b source=sdk
2026-09-07T00:01:08.120Z [DEBUG] Stream started - received first chunk
2026-09-07T00:01:08.120Z [DEBUG] [API:timing] first byte after 1003ms
2026-09-07T00:01:10.883Z [INFO] [Stall] tool_dispatch_start tool=Bash toolUseId=toolu_01PkWMEBGAC8umHnYPsSqoSS permissionDecisionMs=3
2026-09-07T00:01:10.884Z [DEBUG] Spawning shell without login (-l flag skipped)
2026-09-07T00:01:10.920Z [INFO] [Stall] tool_dispatch_end tool=Bash toolUseId=toolu_01PkWMEBGAC8umHnYPsSqoSS outcome=ok durationMs=37
2026-09-07T00:01:10.924Z [DEBUG] autocompact: tokens=[REDACTED] level=ok effectiveWindow=980000
2026-09-07T00:01:10.925Z [DEBUG] Tool search disabled: ToolSearchTool is not available (may have been disallowed via disallowedTools).
2026-09-07T00:01:10.926Z [DEBUG] attribution header x-anthropic-billing-header: cc_version=2.1.263.992; cc_entrypoint=sdk-cli; cch=00000; cc_prev_req=req_011Ceo6Z76AXaUbM9qyoTCdE; cc_prompt_id=51ed5dfe-6e13-480f-82d9-c21bda316023;
2026-09-07T00:01:10.926Z [DEBUG] Fast mode unavailable: Fast mode is not available in the Agent SDK
2026-09-07T00:01:10.926Z [DEBUG] Fast mode unavailable: Fast mode is not available in the Agent SDK
2026-09-07T00:01:10.927Z [DEBUG] Fast mode unavailable: Fast mode is not available in the Agent SDK
2026-09-07T00:01:10.927Z [DEBUG] [API:timing] dispatching to firstParty model=claude-sonnet-5
2026-09-07T00:01:10.927Z [DEBUG] [API REQUEST] /v1/messages x-client-request-id=3b3cacca-43cc-4378-af1e-961ed8a397c9 source=sdk
2026-09-07T00:01:11.998Z [DEBUG] Stream started - received first chunk
2026-09-07T00:01:11.998Z [DEBUG] [API:timing] first byte after 1072ms
2026-09-07T00:01:33.814Z [INFO] [Stall] tool_dispatch_start tool=Bash toolUseId=toolu_01MQQbtxBMAhux1p2AdvtYKR permissionDecisionMs=4
2026-09-07T00:01:33.816Z [DEBUG] Spawning shell without login (-l flag skipped)
2026-09-07T00:01:33.858Z [INFO] [Stall] tool_dispatch_end tool=Bash toolUseId=toolu_01MQQbtxBMAhux1p2AdvtYKR outcome=ok durationMs=44
2026-09-07T00:01:33.860Z [DEBUG] autocompact: tokens=[REDACTED] level=ok effectiveWindow=980000
2026-09-07T00:01:33.860Z [DEBUG] Tool search disabled: ToolSearchTool is not available (may have been disallowed via disallowedTools).
2026-09-07T00:01:33.861Z [DEBUG] attribution header x-anthropic-billing-header: cc_version=2.1.263.992; cc_entrypoint=sdk-cli; cch=00000; cc_prev_req=req_011Ceo6ZPMxX6uEdmwjbt9Js; cc_prompt_id=51ed5dfe-6e13-480f-82d9-c21bda316023;
2026-09-07T00:01:33.861Z [DEBUG] Fast mode unavailable: Fast mode is not available in the Agent SDK
2026-09-07T00:01:33.862Z [DEBUG] Fast mode unavailable: Fast mode is not available in the Agent SDK
2026-09-07T00:01:33.862Z [DEBUG] Fast mode unavailable: Fast mode is not available in the Agent SDK
2026-09-07T00:01:33.862Z [DEBUG] [API:timing] dispatching to firstParty model=claude-sonnet-5
2026-09-07T00:01:33.863Z [DEBUG] [API REQUEST] /v1/messages x-client-request-id=6fb5c26e-a17b-407d-a3e0-21a54dbe48f8 source=sdk
2026-09-07T00:01:34.853Z [DEBUG] Stream started - received first chunk
2026-09-07T00:01:34.853Z [DEBUG] [API:timing] first byte after 990ms
2026-09-07T00:01:36.638Z [INFO] [Stall] tool_dispatch_start tool=Bash toolUseId=toolu_01SaTDWr3FbwXh4Su2ahpnpJ permissionDecisionMs=6
2026-09-07T00:01:36.640Z [DEBUG] Spawning shell without login (-l flag skipped)
2026-09-07T00:01:36.669Z [DEBUG] Invalidating session environment cache
2026-09-07T00:01:36.670Z [INFO] [Stall] tool_dispatch_end tool=Bash toolUseId=toolu_01SaTDWr3FbwXh4Su2ahpnpJ outcome=ok durationMs=32
2026-09-07T00:01:36.671Z [DEBUG] autocompact: tokens=[REDACTED] level=ok effectiveWindow=980000
2026-09-07T00:01:36.672Z [DEBUG] Tool search disabled: ToolSearchTool is not available (may have been disallowed via disallowedTools).
2026-09-07T00:01:36.673Z [DEBUG] attribution header x-anthropic-billing-header: cc_version=2.1.263.992; cc_entrypoint=sdk-cli; cch=00000; cc_prev_req=req_011Ceo6b5Szou6v63GxeFJio; cc_prompt_id=51ed5dfe-6e13-480f-82d9-c21bda316023;
2026-09-07T00:01:36.673Z [DEBUG] Fast mode unavailable: Fast mode is not available in the Agent SDK
2026-09-07T00:01:36.673Z [DEBUG] Fast mode unavailable: Fast mode is not available in the Agent SDK
2026-09-07T00:01:36.673Z [DEBUG] Fast mode unavailable: Fast mode is not available in the Agent SDK
2026-09-07T00:01:36.674Z [DEBUG] [API:timing] dispatching to firstParty model=claude-sonnet-5
2026-09-07T00:01:36.674Z [DEBUG] [API REQUEST] /v1/messages x-client-request-id=ef147627-35a6-4c81-8d2a-d41ca1881c1e source=sdk
2026-09-07T00:01:37.649Z [DEBUG] Stream started - received first chunk
2026-09-07T00:01:37.649Z [DEBUG] [API:timing] first byte after 976ms
2026-09-07T00:01:48.248Z [DEBUG] "Permission suggestions for Bash: [\n  {\n    \"type\": \"addRules\",\n    \"rules\": [\n      {\n        \"toolName\": \"Bash\",\n        \"ruleContent\": \"python3 -\"\n      }\n    ],\n    \"behavior\": \"allow\",\n    \"destination\": \"localSettings\"\n  }\n]"
2026-09-07T00:01:48.250Z [DEBUG] [auto-mode] context comparison: mainLoopTokens=[REDACTED] classifierChars=135607 classifierTokensEst=[REDACTED] (sys=126435 tools=6233 user=2939) transcriptEntries=30 messages=102
2026-09-07T00:01:48.250Z [DEBUG] [auto-mode] new action being classified: {"Bash":"python3 - <<'EOF'\nimport json\nd = json.load(open(\"/Users/hostiletakeover/Projects/paprnav/backend/app/schemas/ad_extraction_v4.schema.json\"))\ndefs = d[\"$defs\"]\nprint(json.dumps(defs[\"knownString\"], indent=2))\nEOF\n"}
2026-09-07T00:01:48.250Z [INFO] [Stall] classifier_request_started reqId=402246c5-61d4-487e-8e08-383ad6266753 tool=Bash model=claude-sonnet-5[1m] stage=xml_s1 promptTokensEst=[REDACTED]
2026-09-07T00:01:48.252Z [DEBUG] attribution header x-anthropic-billing-header: cc_version=2.1.263.b6e; cc_entrypoint=sdk-cli; cch=00000;
2026-09-07T00:01:48.252Z [DEBUG] [API REQUEST] /v1/messages x-client-request-id=c6ec1f1a-8bf5-4ebe-98bf-33622cada8d3 source=side_query
2026-09-07T00:01:49.757Z [INFO] [Stall] classifier_request_finished reqId=402246c5-61d4-487e-8e08-383ad6266753 tool=Bash stage=xml_s1 outcome=ok durationMs=1507
2026-09-07T00:01:49.759Z [INFO] [Stall] tool_dispatch_start tool=Bash toolUseId=toolu_01WaroW8Cd7y8M4jfPmqZaMm permissionDecisionMs=1513
2026-09-07T00:01:49.760Z [DEBUG] No session environment scripts found
2026-09-07T00:01:49.760Z [DEBUG] Spawning shell without login (-l flag skipped)
2026-09-07T00:01:49.827Z [INFO] [Stall] tool_dispatch_end tool=Bash toolUseId=toolu_01WaroW8Cd7y8M4jfPmqZaMm outcome=ok durationMs=68
2026-09-07T00:01:49.829Z [DEBUG] autocompact: tokens=[REDACTED] level=ok effectiveWindow=980000
2026-09-07T00:01:49.829Z [DEBUG] Tool search disabled: ToolSearchTool is not available (may have been disallowed via disallowedTools).
2026-09-07T00:01:49.830Z [DEBUG] attribution header x-anthropic-billing-header: cc_version=2.1.263.992; cc_entrypoint=sdk-cli; cch=00000; cc_prev_req=req_011Ceo6bHS57XV4Rvvu57Te8; cc_prompt_id=51ed5dfe-6e13-480f-82d9-c21bda316023;
2026-09-07T00:01:49.830Z [DEBUG] Fast mode unavailable: Fast mode is not available in the Agent SDK
2026-09-07T00:01:49.831Z [DEBUG] Fast mode unavailable: Fast mode is not available in the Agent SDK
2026-09-07T00:01:49.831Z [DEBUG] Fast mode unavailable: Fast mode is not available in the Agent SDK
2026-09-07T00:01:49.831Z [DEBUG] [API:timing] dispatching to firstParty model=claude-sonnet-5
2026-09-07T00:01:49.832Z [DEBUG] [API REQUEST] /v1/messages x-client-request-id=d53ea9bc-3a67-4d35-a3e7-01fadae0097d source=sdk
2026-09-07T00:01:50.855Z [DEBUG] Stream started - received first chunk
2026-09-07T00:01:50.855Z [DEBUG] [API:timing] first byte after 1023ms
2026-09-07T00:01:57.736Z [DEBUG] "Permission suggestions for Bash: [\n  {\n    \"type\": \"addRules\",\n    \"rules\": [\n      {\n        \"toolName\": \"Bash\",\n        \"ruleContent\": \"python3 -\"\n      }\n    ],\n    \"behavior\": \"allow\",\n    \"destination\": \"localSettings\"\n  }\n]"
2026-09-07T00:01:57.737Z [DEBUG] [auto-mode] context comparison: mainLoopTokens=[REDACTED] classifierChars=135905 classifierTokensEst=[REDACTED] (sys=126435 tools=6531 user=2939) transcriptEntries=31 messages=105
2026-09-07T00:01:57.737Z [DEBUG] [auto-mode] new action being classified: {"Bash":"python3 - <<'EOF'\nimport json\nd = json.load(open(\"/Users/hostiletakeover/Projects/paprnav/backend/app/schemas/ad_extraction_v4.schema.json\"))\ndefs = d[\"$defs\"]\nprint(json.dumps(defs.get(\"officialDocument\", defs.get(\"officialDocuments\",\"MISSING\")), indent=2)[:2000])\nEOF\n"}
2026-09-07T00:01:57.737Z [INFO] [Stall] classifier_request_started reqId=6211c176-ac4c-4b3a-9c14-e56530805762 tool=Bash model=claude-sonnet-5[1m] stage=xml_s1 promptTokensEst=[REDACTED]
2026-09-07T00:01:57.738Z [DEBUG] attribution header x-anthropic-billing-header: cc_version=2.1.263.b6e; cc_entrypoint=sdk-cli; cch=00000;
2026-09-07T00:01:57.738Z [DEBUG] [API REQUEST] /v1/messages x-client-request-id=ab5c7e96-2944-40f9-8129-e7516db8eb30 source=side_query
2026-09-07T00:01:59.311Z [INFO] [Stall] classifier_request_finished reqId=6211c176-ac4c-4b3a-9c14-e56530805762 tool=Bash stage=xml_s1 outcome=ok durationMs=1574
2026-09-07T00:01:59.314Z [INFO] [Stall] tool_dispatch_start tool=Bash toolUseId=toolu_01X4dGK4rTFW5oQAxMP1MLcH permissionDecisionMs=1580
2026-09-07T00:01:59.315Z [DEBUG] Spawning shell without login (-l flag skipped)
2026-09-07T00:01:59.368Z [INFO] [Stall] tool_dispatch_end tool=Bash toolUseId=toolu_01X4dGK4rTFW5oQAxMP1MLcH outcome=ok durationMs=54
2026-09-07T00:01:59.370Z [DEBUG] autocompact: tokens=[REDACTED] level=ok effectiveWindow=980000
2026-09-07T00:01:59.370Z [DEBUG] Tool search disabled: ToolSearchTool is not available (may have been disallowed via disallowedTools).
2026-09-07T00:01:59.371Z [DEBUG] attribution header x-anthropic-billing-header: cc_version=2.1.263.992; cc_entrypoint=sdk-cli; cch=00000; cc_prev_req=req_011Ceo6cFiR5zQPvXXdaereh; cc_prompt_id=51ed5dfe-6e13-480f-82d9-c21bda316023;
2026-09-07T00:01:59.371Z [DEBUG] Fast mode unavailable: Fast mode is not available in the Agent SDK
2026-09-07T00:01:59.371Z [DEBUG] Fast mode unavailable: Fast mode is not available in the Agent SDK
2026-09-07T00:01:59.372Z [DEBUG] Fast mode unavailable: Fast mode is not available in the Agent SDK
2026-09-07T00:01:59.372Z [DEBUG] [API:timing] dispatching to firstParty model=claude-sonnet-5
2026-09-07T00:01:59.373Z [DEBUG] [API REQUEST] /v1/messages x-client-request-id=8bc25214-1af1-44cc-8a47-94ec612e8a81 source=sdk
2026-09-07T00:02:00.442Z [DEBUG] Stream started - received first chunk
2026-09-07T00:02:00.442Z [DEBUG] [API:timing] first byte after 1070ms
2026-09-07T00:02:09.247Z [DEBUG] [Anthropic telemetry] Metrics opt-out API response: enabled=true
2026-09-07T00:02:09.254Z [DEBUG] Preserving file permissions: 100600
2026-09-07T00:02:09.254Z [DEBUG] Writing to temp file: /Users/hostiletakeover/.claude.json.tmp.48303.ff152587519c
2026-09-07T00:02:09.255Z [DEBUG] Applied original permissions to temp file
2026-09-07T00:02:09.255Z [DEBUG] Temp file written successfully, size: 62999 bytes
2026-09-07T00:02:09.255Z [DEBUG] Renaming /Users/hostiletakeover/.claude.json.tmp.48303.ff152587519c to /Users/hostiletakeover/.claude.json
2026-09-07T00:02:09.256Z [DEBUG] File /Users/hostiletakeover/.claude.json written atomically
2026-09-07T00:02:09.328Z [DEBUG] [Anthropic telemetry] BigQuery metrics exported successfully
2026-09-07T00:02:09.328Z [DEBUG] "[Anthropic telemetry] BigQuery API Response: {\n  \"accepted_count\": 6,\n  \"rejected_count\": 0\n}"
2026-09-07T00:02:20.702Z [INFO] [Stall] tool_dispatch_start tool=Bash toolUseId=toolu_01GkrzszsNsX6E26C3xGeQWN permissionDecisionMs=2
2026-09-07T00:02:20.703Z [DEBUG] Spawning shell without login (-l flag skipped)
2026-09-07T00:02:20.761Z [INFO] [Stall] tool_dispatch_end tool=Bash toolUseId=toolu_01GkrzszsNsX6E26C3xGeQWN outcome=ok durationMs=59
2026-09-07T00:02:20.762Z [DEBUG] autocompact: tokens=[REDACTED] level=ok effectiveWindow=980000
2026-09-07T00:02:20.763Z [DEBUG] Tool search disabled: ToolSearchTool is not available (may have been disallowed via disallowedTools).
2026-09-07T00:02:20.764Z [DEBUG] attribution header x-anthropic-billing-header: cc_version=2.1.263.992; cc_entrypoint=sdk-cli; cch=00000; cc_prev_req=req_011Ceo6cxVML5GTnKFAnSKvW; cc_prompt_id=51ed5dfe-6e13-480f-82d9-c21bda316023;
2026-09-07T00:02:20.764Z [DEBUG] Fast mode unavailable: Fast mode is not available in the Agent SDK
2026-09-07T00:02:20.764Z [DEBUG] Fast mode unavailable: Fast mode is not available in the Agent SDK
2026-09-07T00:02:20.765Z [DEBUG] Fast mode unavailable: Fast mode is not available in the Agent SDK
2026-09-07T00:02:20.765Z [DEBUG] [API:timing] dispatching to firstParty model=claude-sonnet-5
2026-09-07T00:02:20.765Z [DEBUG] [API REQUEST] /v1/messages x-client-request-id=26606352-1f6e-4f50-af7d-8d69462c9e61 source=sdk
2026-09-07T00:02:21.730Z [DEBUG] Stream started - received first chunk
2026-09-07T00:02:21.730Z [DEBUG] [API:timing] first byte after 966ms
2026-09-07T00:02:29.665Z [INFO] [Stall] tool_dispatch_start tool=Bash toolUseId=toolu_01T2vBRw7NgkAA3fUoQX7rwd permissionDecisionMs=5
2026-09-07T00:02:29.667Z [DEBUG] Spawning shell without login (-l flag skipped)
2026-09-07T00:02:29.718Z [INFO] [Stall] tool_dispatch_end tool=Bash toolUseId=toolu_01T2vBRw7NgkAA3fUoQX7rwd outcome=ok durationMs=53
2026-09-07T00:02:29.719Z [DEBUG] autocompact: tokens=[REDACTED] level=ok effectiveWindow=980000
2026-09-07T00:02:29.719Z [DEBUG] Tool search disabled: ToolSearchTool is not available (may have been disallowed via disallowedTools).
2026-09-07T00:02:29.720Z [DEBUG] attribution header x-anthropic-billing-header: cc_version=2.1.263.992; cc_entrypoint=sdk-cli; cch=00000; cc_prev_req=req_011Ceo6eXyGbMfDYujMUT69Z; cc_prompt_id=51ed5dfe-6e13-480f-82d9-c21bda316023;
2026-09-07T00:02:29.720Z [DEBUG] Fast mode unavailable: Fast mode is not available in the Agent SDK
2026-09-07T00:02:29.720Z [DEBUG] Fast mode unavailable: Fast mode is not available in the Agent SDK
2026-09-07T00:02:29.721Z [DEBUG] Fast mode unavailable: Fast mode is not available in the Agent SDK
2026-09-07T00:02:29.721Z [DEBUG] [API:timing] dispatching to firstParty model=claude-sonnet-5
2026-09-07T00:02:29.722Z [DEBUG] [API REQUEST] /v1/messages x-client-request-id=dab1ee1f-ae3e-449d-892d-6e10a7dfee99 source=sdk
2026-09-07T00:02:30.670Z [DEBUG] Stream started - received first chunk
2026-09-07T00:02:30.670Z [DEBUG] [API:timing] first byte after 949ms
2026-09-07T00:03:50.160Z [DEBUG] [engine] turn 1 end (turns=41 usage in=82 out=31222 cost=$1.1067 api=373719ms stop=end_turn resultLen=14982)
2026-09-07T00:03:50.161Z [DEBUG] Fast mode unavailable: Fast mode is not available in the Agent SDK
2026-09-07T00:03:50.191Z [DEBUG] Cleaned up session snapshot: /Users/hostiletakeover/.claude/shell-snapshots/snapshot-bash-1788739030894-bef4ww.sh
2026-09-07T00:03:50.411Z [DEBUG] [Anthropic telemetry] BigQuery metrics exported successfully
2026-09-07T00:03:50.411Z [DEBUG] "[Anthropic telemetry] BigQuery API Response: {\n  \"accepted_count\": 6,\n  \"rejected_count\": 0\n}"
2026-09-07T00:03:50.412Z [DEBUG] [Anthropic telemetry] BigQuery metrics exporter flush complete
2026-09-07T00:03:50.412Z [DEBUG] [Anthropic telemetry] BigQuery metrics exporter flush complete
2026-09-07T00:03:50.412Z [DEBUG] [Anthropic telemetry] BigQuery metrics exporter shutdown complete
2026-09-07T00:03:50.828Z [ERROR] Failed to flush logs to Datadog: Error: socket hang up

```
### `.ai/review-runs/T081-V4-SCHEMA-SLICE-3A/manifest.json`

size=3430; sha256=c0f543a203d6aae4fcc89c314c60c48bb96a3acb646c8020b7c19f0db9abd914; truncated=false

```text
{
  "taskId": "T081-V4-SCHEMA-SLICE-3A",
  "stage": "implementation",
  "generatedAt": "2026-09-10T01:55:33+00:00",
  "baseRef": "28f6be0",
  "head": "28f6be0eab225abc4b68830345e04d6fb6df454f",
  "scopePaths": [],
  "scopeFingerprint": "ecf0b3d0f2af4325f4e60c12137668ede7f4c7d5a94b4a41ceab54a91cc23e8b",
  "files": [
    {
      "path": "backend/app/api/routes/ads.py",
      "status": " M",
      "size": 70840,
      "sha256": "c19bbf01d2ce4a479a162922702f2626668ada382c440d5d9cbd4f4f38cd2385",
      "readStatus": "readable"
    },
    {
      "path": "backend/app/core/config.py",
      "status": " M",
      "size": 7979,
      "sha256": "d285cc55e960d5f740278b9a5ef5f87e47ba8c80eaa3e453474fc9119bc635e7",
      "readStatus": "readable"
    },
    {
      "path": "backend/app/db/migrations/versions/20260907_0027_add_ad_v4_applicability.py",
      "status": "??",
      "size": 82407,
      "sha256": "26968c0697bf5021de5e8c11888c254f07934815184407d0a56a87deec95f660",
      "readStatus": "readable"
    },
    {
      "path": "backend/app/models/core.py",
      "status": " M",
      "size": 113180,
      "sha256": "bfecfab846338278709c36ea429a92dfd0147c8cdf28ad3e0bb5a7dfa34c6f02",
      "readStatus": "readable"
    },
    {
      "path": "backend/app/schemas/ads.py",
      "status": " M",
      "size": 10462,
      "sha256": "7f19a3219e4bd483df7249a444ad485c38c6d72fb80451876ee1d2018bf1b4fa",
      "readStatus": "readable"
    },
    {
      "path": "backend/app/services/ad_v4_applicability.py",
      "status": "??",
      "size": 58050,
      "sha256": "7b31dca53a704446c92f193ec5c8537fd7d442f7bef89b916257e4769257c0d3",
      "readStatus": "readable"
    },
    {
      "path": "backend/app/services/ad_v4_candidates.py",
      "status": " M",
      "size": 69544,
      "sha256": "0f888f836a0e9782264e3791d7409ba68f3f5b58679662eeed07744ca093ee55",
      "readStatus": "readable"
    },
    {
      "path": "backend/tests/test_ad_v4_applicability.py",
      "status": "??",
      "size": 13437,
      "sha256": "31ee8d71b596673408b1be13e8488d128093843bf5e6db9dfe54be98c2b118b9",
      "readStatus": "readable"
    },
    {
      "path": "backend/tests/test_ad_v4_applicability_calibration.py",
      "status": "??",
      "size": 13708,
      "sha256": "74bd5aacc1164e9c5c928645e30c965d56267e50c6ff5306748f9410ba2affa9",
      "readStatus": "readable"
    },
    {
      "path": "backend/tests/test_ad_v4_applicability_postgres.py",
      "status": "??",
      "size": 27935,
      "sha256": "3e300ebeb4c192c1a3ee4f1fb79314321acda34bf5f42bb2f87a41887d8ccbe0",
      "readStatus": "readable"
    },
    {
      "path": "backend/tests/test_ad_v4_postgres.py",
      "status": " M",
      "size": 42190,
      "sha256": "d78c799679e2c007a8be07c05437f8c18865149edb6c3dbbad59bb03c82ff892",
      "readStatus": "readable"
    }
  ],
  "reviewInputs": [
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-3A/decision.md",
      "status": "review_input",
      "size": 91684,
      "sha256": "50effad6a01fdb75a1d4594b170bed35f3c977464f4f83a81919793d553df466",
      "readStatus": "readable"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-3A/findings.json",
      "status": "review_input",
      "size": 50306,
      "sha256": "2dc54ae30c42127aaed5b7a5cb8854a1408747fdea2014c2a25f04577d150a00",
      "readStatus": "readable"
    }
  ],
  "outOfScopeDirtyFiles": [],
  "outOfScopeReason": null
}

```
### `.ai/review-runs/T081-V4-SCHEMA-SLICE-3A/review-packet.md`

size=557352; sha256=a3084bacf0b883bbe3d1da74553671ab69635560de9a82ed9e3c1b64064e47cf; truncated=true

```text
# Review packet: T081-V4-SCHEMA-SLICE-3A

Stage: implementation
Generated: 2026-09-10T01:55:33+00:00
Base: `28f6be0`
Head: `28f6be0eab225abc4b68830345e04d6fb6df454f`
Scope fingerprint: `ecf0b3d0f2af4325f4e60c12137668ede7f4c7d5a94b4a41ceab54a91cc23e8b`

## Reviewer instructions

Read `.ai/agents/ADVERSARIAL_REVIEWER.md`. Inspect repository files directly.
Treat the manifest as a starting point and report missing consumers or unjustified
scope exclusions as findings.

## Decision packet

# Decision packet: T081-V4-SCHEMA-SLICE-3A

Status: design reviewed; external-critic remediations pending independent verification

Builder: `/root/v4_schema_builder`

Governing contract: `.ai/AD_EXTRACTION_DOMAIN_CONTRACT.md` version 1.1

Predecessor: closed `T081-V4-SCHEMA-SLICE-2` candidate-validation and
immutable-proposal boundary

## Objective

After design approval, implement one additive, candidate-only relational
projection of the applicability subset of an immutable V4 proposal. The slice
materializes and reconstructs only:

- `productScopes` and their product roles, source manufacturer values,
  manufacturer normalization assertions, model lists or series expressions,
  and serial/part-number scopes;
- `conditionDefinitions`, their typed subjects and explicit three-valued
  values;
- the nested three-valued expression trees and `applicabilityRules` that refer
  to those scopes and conditions; and
- non-controlling `applicabilitySearchHints`.

Slice 3A also creates the shared, proposal-scoped correction foundation named
in section 2.1.1. It reads and verifies the canonical
`authoritativeCorrections` namespace and the referenced `officialDocuments`
identity/evidence fields, materializes
`ad_v4_candidate_corrections`, `ad_v4_candidate_correction_refs`,
`ad_v4_candidate_correction_semantic_bindings`, and
`ad_v4_candidate_correction_evidence_links`, and reconstructs each correction
object separately from the four-field applicability subtree. This is explicit
3A scope needed to preserve one cross-slice correction identity; it does not
materialize obligation or document semantics.

The projection is bound to one Slice-2 candidate proposal, its canonical hash,
its evidence-binding hash, and a fixed materializer version. It remains
unreviewed and `candidate_only`. Relational reconstruction must reproduce the
canonical applicability subtree exactly and must never copy retained source
text.

This is deliberately the first half of the originally proposed normalized
schema slice. The following are not part of Slice 3A:

- requirements, actions, timing, recurrence groups, branches, terminating
  effects, incorporated-document/service-bulletin content, AMOC provisions,
  or aircraft-specific AMOC use (Slice 3B). The shared correction foundation
  records complete ordered references into these deferred namespaces but does
  not interpret or materialize their 3B semantics;
- human approval, signoff, rejection, publication, current selection, or a
  reviewer GUI;
- released catalog, aircraft matching, coverage, compliance, or due-state
  readers;
- V3 mutation, translation, fallback, or compatibility-row materialization;
- aircraft/component canonical identity migration or aircraft configuration;
  and
- fuzzy aliases, inferred series membership, or an authoritative manufacturer
  or model registry.

## User-visible outcome

There is no maintenance-shop or customer-visible behavior change. An active
platform administrator may explicitly request deterministic materialization of
an existing V4 candidate and inspect its verified projection for audit. The
response identifies the candidate proposal, projection/materializer version,
applicability-subtree hash, counts, evidence-binding hash, and a computed
candidate projection state. It never calls the released AD catalog or claims
that any aircraft is or is not affected.

The endpoint and database use the label `candidate_only`; they do not use
`approved`, `current`, `released`, `actionable`, `applicable`, or `not
applicable` as a projection-level decision. A canonical field may itself carry
the source-supported three-valued state `not_applicable`; that field state does
not turn the candidate projection into an approved conclusion.

## Safety and correctness invariants

The following are falsifiable design and implementation gates.

1. A projection references exactly one immutable
   `ad_v4_candidate_proposals` row and repeats its directive ID, schema version,
   validator version, canonicalization version, canonical hash, and
   evidence-binding hash under composite FK/trigger enforcement.
2. Only a proposal with database gate `candidate_only`, valid canonical bytes,
   valid Slice-2 envelopes, and a currently eligible exact Slice-1 evidence
   lifecycle may be materialized. Eligibility is rechecked inside the write
   transaction; creation-time validity is not trusted.
3. The applicability materialized source is the four-field canonical subtree
   `{productScopes, conditionDefinitions, applicabilityRules,
   applicabilitySearchHints}` extracted from verified proposal bytes. The only
   additional top-level namespaces read are the explicitly scoped
   `authoritativeCorrections` and referenced `officialDocuments` fields used by
   the shared correction foundation. No other namespace is silently projected.
4. Reconstructing that subtree solely from relational rows, including every
   property-presence choice and array order, then applying the Slice-2
   canonicalizer produces byte-identical subtree bytes and the stored subtree
   hash.
5. PostgreSQL deferred checks compare the reconstructed relational JSONB to the
   exact four-field subtree in the parent proposal's verified JSONB mirror.
   Direct SQL cannot commit a partial, cross-candidate, or differently valued
   projection whose root hashes appear valid.
6. Every semantic node belongs to the same projection and proposal. Every
   typed child, expression edge/reference, rule exclusion, identity mapping,
   dependency, and evidence link uses a composite same-projection FK; a bare ID
   is never the only relationship guard.
7. Every evidence-bearing canonical object has exactly the evidence-key set in
   the candidate. Evidence links resolve to Slice-2
   `ad_v4_candidate_evidence_bindings` for the same proposal. They store IDs and
   hashes only; no fragment text, page text, PDF bytes, or repeated citation
   prose exists in any Slice-3A table.
8. Source manufacturer values and model/series designations are preserved
   byte-for-byte as validated NFC strings. They are never case-folded, trimmed,
   punctuation-folded, concatenated, or replaced by a normalized identity.
9. Candidate normalization is a separate assertion with explicit origin,
   version, review state, and evidence. A known normalized manufacturer value
   comes only from the canonical proposal. Current V4 supplies no per-model
   normalized value, so model normalization is explicitly `unknown` with
   reason `not_extracted`; it is never inferred from spelling similarity. The
   model mapping is one-to-one with its exact designation-value occurrence,
   inherits source support from one parent designation-scope node, and does not
   repeat an evidence link for every listed model.
10. Every normalization row is `unreviewed_candidate`. No aircraft row or
    released directive may reference it, and no matching/current-selection
    reader exists in this slice.
11. SQL `NULL` means only that a property is absent or that a column is unused
    by the row's checked discriminator. Regulatory uncertainty is always an
    explicit `unknown` state with controlled reason, temporal scope, and
    evidence; `not_applicable` has the same explicit support.
12. A source property that is absent is recorded as `property_absent`, distinct
    from an explicit canonical `unknown`. Reconstruction omits an absent
    property and emits an explicit unknown object for an unknown property.
13. Listed models, serial/part values, and identifier ranges remain exact
    source values. A series expression is preserved as source text and has
    evaluation state `unknown/unsupported_expression`; Slice 3A executes no
    regex, prefix, series, serial, or part-number comparator.
14. Conditions preserve their exact type, operator, optional comparator
    version, temporal-basis discriminator, subject property presence, compound
    source display text, typed designation groups/members, and three-valued
    subject assertions. Every condition type/operator pair accepted by the
    Slice-2 schema is representable but explicitly `unevaluated`; 3A invents no
    unreviewed compatibility matrix. No display JSON or opaque predicate JSON
    is relational authority.
15. Expression rows implement only `scope_ref`, `predicate_ref`, `rule_ref`,
    `not`, `all`, and `any` for applicability rules. Requirement-state refs are
    rejected at this boundary. Arity, sequence, same-projection reference
    types, rule cycles, and exclusion cycles are enforced again at materialize
    and reconstruct time.
16. Expression evaluation is out of scope. Stored expression nodes declare the
    fixed result domain `kleene_true_false_unknown_v1` and evaluator version,
    but no row records a truth result for an aircraft.
17. Search hints remain `controlling = false` and `exhaustive = false`, have
    no FK route from an expression, and cannot establish or suppress a match.
18. One source condition, rule, and evidence binding shared by 182 models
    produces one condition row, one rule row, and no per-model evidence-link
    copies. All links reuse Slice-2 binding IDs rather than copying source
    identity or text. The 2024-14-03 fixture is the mandatory bloat regression.
19. Materialization is deterministic and idempotent for
    `(proposal_id, materializer_version)`. Identical retries return the same
    root; different request keys may record separate audit requests without
    duplicating semantic content.
20. Concurrent materialization of the same proposal converges on one complete
    root and one deterministic row set. No uniqueness race returns 500, leaks a
    partial graph, or produces different node identities.
21. Correction or replacement never updates a projection. A later candidate
    relationship appends a hash-chained stale event for the predecessor
    projection. Evidence lifecycle change is detected live and may append the
    same derived stale fact; it never rewrites prior rows.
22. A candidate supersession relation is stored only as an evidence-bound,
    untrusted dependency signal. It can cause a stale event only when its
    successor AD number equals this proposal's known, evidence-bound canonical
    AD number and its predecessor resolves uniquely. Otherwise it remains
    unresolved with no side effect. Every stale event names that exact
    same-projection dependency row. It never changes released AD status or
    proves legal supersession.
23. Projection reads fold the immutable event chain and recheck parent/evidence
    integrity. Missing, ambiguous, contradictory, or invalidated dependencies
    fail closed to `candidate_stale` or `dependency_unresolved`; no stale root
    is presented as verified/current.
24. POST and both audit GET endpoints require
    `Paprnav-Acting-Membership-Id`. Only the exact selected active membership
    belonging to the caller and carrying `platform_admin` may authorize the
    transaction. POST snapshots membership, organization, role, status,
    action, policy version, and claims hash. GET locks and revalidates the exact
    selected membership for that transaction. Another valid membership cannot
    rescue an inactive, shop, foreign, or revoked selected membership.
25. V1/V2/V3 rows and all released/search/matching/compliance/due readers are
    behaviorally unchanged. Repository search and route tests prove that no
    existing reader imports or queries a Slice-3A table.
26. Slice 3A creates only integrity, reconstruction, audit, and stale-fold
    indexes used by its own bounded service. It creates no normalized-token,
    aircraft-identity, or matching hot-path index and makes no readiness claim.
    A reviewed identity bridge and its indexes belong to the later matching
    slice.
27. All Slice-3A rows are append-only. PostgreSQL rejects UPDATE and DELETE,
    including attempted normalization or stale-state edits.
28. Upgrade performs only the locked Slice-2 v1 version-metadata backfill and
    no semantic/canonical/evidence backfill. Downgrade locks the Slice-2
    proposal boundary first, then child and 3A tables, refuses while any 3A or
    v2 row exists, and succeeds/re-upgrades only for v1-only/empty-3A state.
    Concurrent insert/drop cannot deadlock or lose rows.
29. Validator-2 writes and Slice-3A routes have independent, default-off
    application flags and database gates. A 3A materialization requires both
    write and 3A gates; audit requires only the 3A/read gate. Every request also
    proves the compiled application version and migration-0027 capability at
    startup and inside its transaction. Migration presence alone never enables
    either surface, and a gate is not evidence that a fleet-wide compatibility
    rollout completed.

## Current behavior and authoritative representation

Slice 1 retains immutable source documents, page renditions, text versions,
single-page exact evidence fragments, and fragment lifecycle chains. Slice 2
validates raw V4 bytes, canonicalizes the full proposal, snapshots exact
admitted evidence bindings, and stores immutable candidate content,
submissions, relationships, and creation events. Its database gate is always
`candidate_only`.

The Slice-2 canonical bytes remain candidate authority. Slice 3A is a derived,
lossless relational projection used only for audit and later reviewed
development. The projection never becomes official evidence or reviewed
structured AD truth merely because round-trip equality succeeds.

Existing V3 `applicability_targets`, `ad_target_applicability`, compliance
requirements, released catalog rows, and their copied JSON/citations are not a
source for Slice 3A and are not populated by it. They remain isolated legacy
representations.

The five executable Slice-2 calibration proposals currently contain:

| AD | scopes | listed models | conditions | rules | hints | applicability-relevant change signal |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| 1998-17-11 | 2 | 81 | 2 | 1 | 0 | none |
| 2002-13-04 | 1 | 6 | 4 | 1 | 1 | none |
| 2008-26-10 | 1 | 182 | 4 | 1 | 0 | authoritative correction |
| 2011-10-09 | 1 | 224 | 0 | 1 | 0 | supersession relation |
| 2024-14-03 | 5 | 182 | 1 | 1 | 0 | none |

Those are calibration expectations, not facts to hard-code in the
materializer.

## Proposed design

### 0. Required backward-compatible Slice-2 schema corrections

Slice 3A cannot faithfully materialize known predecessor defects. Its future
implementation therefore includes a narrowly versioned correction to the
Slice-2 canonical boundary before any 3A row is written.

The current schema, validator, and canonicalization artifacts are frozen as
`paprnav-ad-v4-validator-1` and `paprnav-ad-v4-c14n-1` for verification of
already stored candidates. A new closed schema/semantic profile
`paprnav-ad-v4-validator-2` remains `schemaVersion: ad_extraction_v4` and uses
the distinct canonicalization profile `paprnav-ad-v4-c14n-2`. New submissions
use only the v2 pair. Stored v1 candidates retain their bytes, hashes, events,
audit readability, and `candidate_only` gate. They are neither rewritten nor
deleted. A validator-1 proposal containing either defect below receives stable
materializer refusal
`predecessor_semantic_defect`; the safe path is a new validator-2 candidate
linked by `corrects_candidate`. Refusal to derive new rows is not mutation or
invalidation of the stored candidate.

#### Explicit uncertainty for the 1998 packet

The source wording “If it cannot be determined” remains in its admitted exact
evidence fragment. It is not persisted as the artificial known value
`unknown_requires_compliance`. The corrected `condition-provenance-unknown`
uses the already closed known/unknown/not-applicable union:

```json
"attributeValue": {
  "state": "unknown",
  "reason": "not_observed",
  "temporalScope": {"kind": "at_applicability_evaluation"},
  "evidenceKeys": ["ev-unknown-provenance"]
}
```

Its condition remains a typed `reviewed_manual_predicate/requires_review` leaf.
Kleene evaluation is not performed in 3A, but any future evaluator must treat
the unknown operand as unknown/fail-closed, not false. Validator 2 rejects the
exact reserved semantic sentinel `unknown_requires_compliance` in a known
union. It does not guess from broad words such as “unknown” in authentic source
text. A schema negative and semantic negative enforce the reserved-token rule.

Implementation must preserve byte-identical validator-1/c14n-1 artifacts and
dispatch stored read verification by the row's recorded validator and
canonicalization versions; new writes and the corrected 1998 calibration
candidate use validator-2/c14n-2. Regression gates prove the old stored
candidate still verifies under v1, the new validator rejects the sentinel, the
corrected proposal stores under v2 with a new canonical hash, and no existing
row/event changes.

#### Compound designation groups and search-hint associations

Validator 2 adds closed, optional typed designation-group structures. Source
display wording is stored separately and is never parsed to create members.
For a condition subject the shape is:

```json
"designationGroup": {
  "groupKey": "...",
  "sourceDisplayText": {"state":"known","value":"...","evidenceKeys":["..."]},
  "association": "all_members|any_member|source_group|unknown",
  "members": [
    {
      "memberKey":"...",
      "designationKind":"model|series_expression",
      "sourceDesignation":"...",
      "manufacturer": {"state":"known|unknown|not_applicable", "...":"..."},
      "evidenceKeys":["..."]
    }
  ],
  "evidenceKeys":["..."]
}
```

For `association: unknown`, the group also requires controlled reason and
temporal scope. Member manufacturer uses the existing explicit union. Member
and group keys are unique; member ordering is a canonical set keyed by
`memberKey`. `sourceDisplayText` is display/evidence fidelity only. No service
splits commas, slashes, conjunctions, whitespace, or prefixes.

The corrected 2002 candidate represents:

- exact display `6314,6324,6364` plus three `any_member` magneto model members;
- exact display `C-125,C145,O-300,IO-360,TSIO-360` plus five `any_member`
  engine model/series members;
- `LTSIO-520-AE` as one atomic member; and
- its non-exhaustive airframe hint as seven explicit manufacturer groups and
  20 source-faithful typed members: 19 exact model-designation members plus one
  Cessna `series_expression` member whose exact expression text is
  `172A through 172H`, evaluation state is `unknown`, and reason is
  `unsupported_expression`. Cessna has eight exact model members plus that one
  expression; Beagle has 1, Cirrus 2, Globe Swift 2, Maule 1, Piper 2, and
  Reims (Cessna) 3 exact models. The old fabricated manufacturer value
  `multiple` is not a normalized identity. No exact `172A`, `172B`, ...,
  `172H` member is inferred from the expression.

The retained-source count oracle is exact: Cessna model members are `170`,
`170A`, `170B`, `172`, `172XP`, `336`, `337`, and `T303`, plus the one series
expression; Beagle is `B242-C`; Cirrus is `SR20`,`SR22`; Globe Swift is
`GC-1A`,`GC-1B`; Maule is `M4`; Piper is `PA-28R-201T`,`PA-34`; and Reims
(Cessna) is `FA172`,`F337`,`FR172`. These are 19 exact models + 1 expression,
not 27 exact models.

The corrected 2024 candidate preserves exact display `GFC 500 and GSA 28` and
uses `all_members` with two Garmin model members. Its STC and master-drawing
fields remain separate condition-subject assertions.

Validator-2 search hints replace the ambiguous flat manufacturer/models pair
with `sourceDisplayText` plus `manufacturerModelGroups`. Each group has a
manufacturer explicit union, exact model-member rows, association state, and
evidence. If the source does not establish a pairing, manufacturer association
is explicit `unknown/source_ambiguous`; models remain individually queryable
but not assigned to a maker. Hints remain fixed `controlling:false` and
`exhaustive:false` and cannot be referenced by an expression.

Validator-1 candidates remain readable. Validator 2 accepts the old atomic
`modelOrSeries` only as one unparsed source value and forbids using it as a
typed member set. Corrected calibration fixtures use the group form wherever
the source expresses more than one designation. The implementation scope
therefore includes versioned schema/validator dispatch, the 1998, 2002, and
2024 proposal corrections, and predecessor calibration/service regressions;
retained PDFs and fragment selections do not change.

#### Validator-2 canonicalization and hash domains

Validator 2 closes every new object with `additionalProperties:false` and
uses these normative shapes:

- condition `designationGroup` requires exactly `groupKey`,
  `sourceDisplayText`, `association`, `members`, and `evidenceKeys`; it permits
  `reason` and `temporalScope` only when `association:"unknown"`, when both are
  required;
- each designation-group member requires `memberKey`, `designationKind`,
  `manufacturer`, and `evidenceKeys`. The closed `model` branch additionally
  requires `sourceDesignation`. The closed `series_expression` branch instead
  requires `expressionText`, fixed `evaluationState:"unknown"`, and fixed
  `reason:"unsupported_expression"`; it forbids `sourceDesignation` and any
  parsed lower/upper/prefix member fields;
- each v2 applicability search hint requires exactly `hintKey`, `productRole`,
  `sourceDisplayText`, `manufacturerModelGroups`, `controlling:false`,
  `exhaustive:false`, and `evidenceKeys`; the v1 flat `manufacturer`/`models`
  pair is not legal in validator 2;
- each manufacturer/model group requires `groupKey`, the existing explicit
  manufacturer union, `association`, `members`, and `evidenceKeys`; unknown
  association additionally requires controlled `reason` and `temporalScope`;
  and
- each hint member uses the same closed `model|series_expression` one-of and
  exact field exclusions as a designation-group member.

`sourceDisplayText`, manufacturer unions, temporal scope, identifiers, and
evidence keys reuse the already closed V4 definitions. No new open object,
free-form discriminator, or unannotated array is permitted.

`paprnav-ad-v4-c14n-2` inherits every scalar, object-key, decimal, Unicode,
date, and existing-array rule from c14n-1. It adds only these closed array
annotations introduced by validator 2:

- `designationGroup.members`: set keyed by unique `memberKey`;
- `applicabilitySearchHints[].manufacturerModelGroups`: set keyed by unique
  `groupKey`; and
- `manufacturerModelGroups[].members`: set keyed by unique `memberKey`.

The `designationGroup` and `sourceDisplayText` shapes are objects, not arrays.
Every v2 array, including inherited arrays, has an explicit
`x-paprnav-array-kind`; validator-2 meta-tests fail any missing annotation.
Within a group, `model` members carry one exact designation; a
`series_expression` member carries one exact expression plus fixed
`evaluationState:"unknown"` and `reason:"unsupported_expression"`. C14n-2
does not expand, parse, or reorder characters within that expression. Adding
or changing any array shape requires c14n-3 and a new reviewed boundary.

Every separator below is the displayed ASCII/UTF-8 string followed by exactly
one NUL byte `0x00`. Complete bytes, including the final `00`, are normative:

| v2 hash object | ASCII before NUL | complete hex bytes |
| --- | --- | --- |
| proposal | `paprnav:ad_extraction_v4:proposal:paprnav-ad-v4-c14n-2` | `706170726e61763a61645f65787472616374696f6e5f76343a70726f706f73616c3a706170726e61762d61642d76342d6331346e2d3200` |
| evidence bindings | `paprnav:ad_extraction_v4:evidence-bindings:2` | `706170726e61763a61645f65787472616374696f6e5f76343a65766964656e63652d62696e64696e67733a3200` |
| candidate event | `paprnav:ad_extraction_v4:candidate-event:2` | `706170726e61763a61645f65787472616374696f6e5f76343a63616e6469646174652d6576656e743a3200` |
| submission | `paprnav:ad_extraction_v4:submission:2` | `706170726e61763a61645f65787472616374696f6e5f76343a7375626d697373696f6e3a3200` |
| submission relationship | `paprnav:ad_extraction_v4:submission-relationship:2` | `706170726e61763a61645f65787472616374696f6e5f76343a7375626d697373696f6e2d72656c6174696f6e736869703a3200` |

For each object, `hash = lowercase_hex(SHA-256(domain_bytes ||
restricted_jcs_v2(envelope)))`. The proposal envelope is the closed v2 root.
Other v2 envelopes retain the v1 field meanings but use fixed literal versions
`ad-v4-evidence-bindings-v2`, `ad-v4-candidate-created-v2`,
`ad-v4-submission-v2`, and `ad-v4-submission-relationship-v2`. Each v2 audit
envelope additionally contains exactly
`validatorVersion:"paprnav-ad-v4-validator-2"` and
`canonicalizationVersion:"paprnav-ad-v4-c14n-2"`. These fields are
server-derived. V1 rows retain their exact v1 envelope bytes and v1 domains;
their hashes are never recomputed under v2.

Proposal content identity and reuse are scoped by `(directive_id,
validator_version, canonicalization_version, canonical_hash)`. Therefore the
same logical source values submitted under v1/c14n-1 and v2/c14n-2 produce
distinct proposal/hash identities, even if their restricted-JCS payload bytes
happen to match. Binding, submission, relationship, and event identity/retry
comparison likewise occurs only within an identical validator/canonicalization
pair and its version-specific domain. Cross-version equality never causes
reuse.

### 1. Projection and hash boundary

Define canonical applicability subtree `A(P)` from verified proposal `P` as
exactly:

```json
{
  "productScopes": P.productScopes,
  "conditionDefinitions": P.conditionDefinitions,
  "applicabilityRules": P.applicabilityRules,
  "applicabilitySearchHints": P.applicabilitySearchHints
}
```

The properties appear under validator-2/c14n-2 canonical object ordering. The
3A materializer accepts only `paprnav-ad-v4-validator-2` with
`paprnav-ad-v4-c14n-2`; v1 candidates remain dual-reader auditable but are not
projected. Array set/sequence behavior is the explicit c14n-2 contract above;
Slice 3A defines no alternative canonicalizer.

`applicability_subtree_hash` is lowercase hex SHA-256 of:

```text
UTF-8("paprnav:ad_extraction_v4:applicability-subtree:paprnav-ad-v4-c14n-2")
|| 0x00 || restricted_jcs(A(P))
```

The complete subtree domain bytes, including the final NUL, are
`706170726e61763a61645f65787472616374696f6e5f76343a6170706c69636162696c6974792d737562747265653a706170726e61762d61642d76342d6331346e2d3200`.

Materializer version is fixed as `paprnav-ad-v4-app-materializer-2`.
Projection identity hash uses:

```text
UTF-8("paprnav:ad_extraction_v4:applicability-projection:2") || 0x00 ||
restricted_jcs({
  "version":"ad-v4-applicability-projection-v2",
  "proposalId": proposal_id,
  "proposalCanonicalHash": proposal_canonical_hash,
  "evidenceBindingHash": evidence_binding_hash,
  "validatorVersion":"paprnav-ad-v4-validator-2",
  "canonicalizationVersion":"paprnav-ad-v4-c14n-2",
  "materializerVersion":"paprnav-ad-v4-app-materializer-2",
  "applicabilitySubtreeHash": applicability_subtree_hash,
  "semanticNodeHashes":[...sorted by node type and node key...],
  "evidenceLinkHashes":[...sorted by node key and evidence key...]
})
```

The complete projection domain bytes, including final NUL, are
`706170726e61763a61645f65787472616374696f6e5f76343a6170706c69636162696c6974792d70726f6a656374696f6e3a3200`.

Every row ID is server-derived as its table prefix plus the first 32 lowercase
hex characters of a domain-separated full identity hash. Each row stores the
full identity hash and a uniqueness constraint; a truncated-ID collision with
a different full hash is an integrity error, not reuse.

### 2. Additive PostgreSQL mapping

All tables use explicit stable string codes plus CHECK constraints rather than
application-only enums. Every FK named below is `ON DELETE RESTRICT`; every
table receives an UPDATE/DELETE rejection trigger.

#### 2.1 Root, request, lifecycle, and dependencies

`ad_v4_candidate_app_projections`

- `id`, full `identity_hash`, `proposal_id`, `directive_id`;
- repeated `schema_version`, `validator_version`, `canonicalization_version`,
  `proposal_canonical_hash`, and `evidence_binding_hash`;
- fixed `materializer_version`, `applicability_subtree_hash`,
  `projection_hash`, and constant `gate = 'candidate_only'`;
- exact counts for semantic nodes, typed rows, and evidence links;
- `created_at`; no mutable status/current/approval/release column;
- UNIQUE `(proposal_id, materializer_version)`, UNIQUE `identity_hash`, and
  UNIQUE `(id, proposal_id)`; and
- a composite parent check/trigger requiring all repeated columns to equal the
  referenced Slice-2 candidate proposal and its gate to remain candidate-only.

`ad_v4_candidate_app_materialization_requests`

- immutable `id`, projection/proposal/directive IDs, actor user, exact
  authorizing membership and organization, snapshotted role/status, fixed
  policy name/version/claims hash, fixed endpoint action, idempotency key,
  request hash, and created time;
- actor/role/status CHECKs require active platform admin;
- UNIQUE `(actor_user_id, authorizing_membership_id, endpoint_action,
  auth_policy_version, idempotency_key)`; and
- composite FKs require request projection/proposal/directive equality.

`ad_v4_candidate_app_projection_events`

- `id`, projection/proposal IDs, `sequence_number`, event type
  `materialized|candidate_corrected|candidate_replaced|
  evidence_invalidated|candidate_supersession_signal`, reason code, optional
  causing Slice-2 relationship ID, lifecycle-event ID, projection ID, or
  `causing_dependency_id`; predecessor event hash, canonical event bytes/hash,
  actor kind `platform_admin|system`, actor request ID when platform-admin,
  and occurred time;
- sequence 0 is exactly one `materialized` root with null predecessor; later
  events require the previous same-projection hash;
- closed discriminator checks require: `materialized` names only its request;
  `candidate_corrected|candidate_replaced` name only the matching Slice-2
  relationship; `evidence_invalidated` names only the matching lifecycle
  event; and `candidate_supersession_signal` names only a same-projection
  incoming dependency row through composite FK `(projection_id,
  causing_dependency_id)`;
- system events have no human actor and name exactly one deterministic causal
  row;
  platform-admin events require a request; and
- UNIQUE `(projection_id, sequence_number)`, UNIQUE `(projection_id,
  event_hash)`, UNIQUE `(projection_id, event_type, causing_dependency_id)`
  where a dependency is present, and equivalent partial causal uniqueness keys
  for relationship and lifecycle causes.

`ad_v4_candidate_app_change_dependencies`

- semantic node/projection/proposal IDs and dependency kind
  `outgoing_supersedes|outgoing_partially_supersedes|
  incoming_supersession_signal`;
- an outgoing supersession row preserves predecessor and successor AD numbers
  exactly as stated and is evidence-bound to both the relation and this
  proposal's known `directiveIdentity.adNumber` assertion;
- resolution state `resolved_candidate|unresolved|ambiguous`, with target
  directive/projection IDs used only for a uniquely resolved candidate signal;
- explicit unresolved reason instead of a nullable target meaning unknown; and
- evidence links to the dependency semantic node. No dependency row changes a
  released directive or becomes legal supersession authority.

For every canonical relation, the successor must equal the proposal's known,
evidence-bound canonical AD number before resolution is attempted. A mismatch
stores one outgoing row as `unresolved/successor_not_this_proposal` and creates
no target-local row or event. When the predecessor resolves uniquely, the
service locks both projection roots in lexical order and creates a deterministic
`incoming_supersession_signal` row in each affected predecessor projection.
That row references the outgoing source row, repeats no evidence text, and is
the exact same-projection cause of the stale event. Multiple, contradictory, or
unresolved relations produce only unresolved dependency rows and no side
effect. Retry and concurrent workers converge on the same incoming dependency
and event by full cause hash plus the causal unique constraint.

#### 2.1.1 Shared authoritative-correction foundation

Slice 3A creates a shared proposal-scoped correction foundation used unchanged
by Slice 3B. It is not an applicability-only copy.

`ad_v4_candidate_corrections`

- immutable proposal-scoped correction root with proposal ID (and no
  applicability- or obligation-projection ownership), canonical
  `correction_key`, correction type, original and correcting
  `officialDocuments` reference keys, their verified document-identity hashes,
  the correction object's canonical hash, canonical ordinal, foundation
  version `paprnav-ad-v4-correction-foundation-1`, and generation `1`;
- expected changed-reference count and expected evidence-key count from the
  canonical object; and
- UNIQUE `(proposal_id, correction_key)`, UNIQUE full identity hash, and
  composite parent/document FKs. The root owns the correction evidence links
  once; neither 3A nor 3B copies those links.

`ad_v4_candidate_correction_refs`

- correction root/proposal IDs, canonical ordinal, namespace, exact
  key, owner slice, and canonical reference hash;
- namespace is closed to the complete canonical set:
  `directiveIdentity|productScopes|conditionDefinitions|applicabilityRules|
  requirements|recurrenceGroups|amocAuthorityProvisions|
  supersessionRelations`;
- owner slice is `foundation|slice_3a|slice_3b`, fixed by namespace:
  directive identity and supersession relations are foundation-owned;
  product scopes, conditions, and applicability rules are 3A-owned; and
  requirements, recurrence groups, and AMOC authority provisions are
  3B-owned; and
- UNIQUE `(correction_id, namespace, key)` and UNIQUE `(correction_id,
  canonical_ordinal)` preserve the complete ordered reference set now,
  including future-3B references. No count-only placeholder is allowed.

`ad_v4_candidate_correction_semantic_bindings`

- correction-reference/proposal IDs, binding generation, binding slice,
  owner-projection kind/ID, semantic node type/ID, and binding hash;
- a same-proposal composite FK binds a 3A reference to exactly the semantic
  node in its applicability projection reconstructed from that canonical key;
  Slice 3B later binds to its own same-proposal obligation projection, so the
  shared root is never reassigned between projections; and
- UNIQUE `(correction_ref_id, binding_slice, binding_generation)`.

`ad_v4_candidate_correction_evidence_links`

- correction root/proposal IDs, exact Slice-2 candidate binding ID and evidence
  key, purpose `correction_clause`, canonical ordinal, and link hash;
- composite FK to the same-proposal Slice-2 evidence snapshot; and
- UNIQUE `(correction_id, evidence_key)` plus unique canonical ordinal. These
  are the correction's one authoritative evidence-link set; applicability
  nodes referenced by the correction retain only their own canonical evidence,
  not a second copy of correction evidence.

Foundation completeness requires one root per canonical correction, exact
official-document identity, the complete ordered changed-reference namespace,
and the exact evidence set before the 3A transaction commits. Generation 1 is
3A-complete only when every 3A-owned reference has one binding; foundation and
3B-owned references remain explicit rows with their owner state and never use
SQL NULL as a placeholder. Slice 3B later inserts immutable generation-1
bindings for its owned refs under the same roots. It neither updates nor
duplicates roots, refs, official-document attribution, or evidence links.

For calibration correction `correction-2010`, reconstruction is exact: one
root retains its original/correcting official-document keys, two evidence keys
linked once, and the complete ordered reference set
`productScopes/scope-cessna`, `requirements/req-report`. Slice 3A binds only
`scope-cessna`; `req-report` remains explicitly `slice_3b` owned. After 3B it
receives one requirement binding. Joining root + ordered refs + the one root
evidence set reconstructs the same canonical correction object before and
after 3B; semantic bindings are validation edges and are not serialized into
the canonical correction JSON.

#### 2.2 Semantic nodes and evidence links

`ad_v4_candidate_app_semantic_nodes`

- `id`, full identity hash, projection/proposal IDs, node type, stable node key,
  canonical source pointer, canonical node hash, and created time;
- node types are exactly `product_scope|designation_scope|value_assertion|
  identity_mapping|designation_value|designation_range|designation_group|
  designation_group_member|condition|expression|applicability_rule|
  search_hint|search_hint_group|search_hint_model|change_dependency`;
- UNIQUE `(projection_id, node_type, node_key)`, UNIQUE `identity_hash`, and
  UNIQUE `(id, projection_id, proposal_id)`; and
- a deferred ownership trigger requires exactly one matching typed owner row
  for each node and rejects typed rows with the wrong node type.

`ad_v4_candidate_app_evidence_links`

- `id`, projection/proposal IDs, semantic node ID, Slice-2 candidate binding
  ID, evidence key, purpose code, canonical ordinal, and link hash;
- purpose is a closed code such as `scope_clause`, `identity_support`,
  `designation_scope`, `condition_clause`, `subject_value`, `rule_clause`,
  `search_hint_clause`, `correction_clause`, or `supersession_clause`;
- composite FK `(projection_id, proposal_id, semantic_node_id)` binds the
  owner; composite FK `(proposal_id, candidate_binding_id, evidence_key)` binds
  the exact Slice-2 evidence snapshot; and
- UNIQUE `(semantic_node_id, purpose, evidence_key)`. A deferred check requires
  the exact canonical evidence-key set for each evidence-bearing source
  pointer. There is no text column.

The 3A migration may add the supporting UNIQUE constraint
`(proposal_id,id,evidence_key)` to the immutable Slice-2 binding table; it does
not change or backfill its data.

#### 2.3 Source values and candidate identity normalization

`ad_v4_candidate_app_value_assertions`

- semantic node/projection/proposal IDs, parent semantic node ID, field code,
  state `known|unknown|not_applicable`, value type `text`, optional exact text
  value, controlled reason code, and temporal-scope kind;
- known => text value present and reason/temporal unused;
- unknown/not-applicable => text value unused and reason/temporal present;
- UNIQUE `(parent_semantic_node_id, field_code)`; and
- deferred evidence requires one or more exact binding links for every row.

`ad_v4_candidate_app_identity_mappings`

- semantic node/projection/proposal IDs, exact `source_occurrence_node_id`, one
  `evidence_parent_node_id`, identity kind `manufacturer|model|series`, exact
  source value, normalization origin
  `candidate_payload|source_only|no_normalized_identity`, normalized state,
  normalized value, controlled reason and temporal scope, normalization
  namespace/version, and fixed review state `unreviewed_candidate`;
- `source_occurrence_node_id` is the exact manufacturer assertion,
  designation-value, designation-group-member, or hint-group-member node whose
  source value is mapped. A composite FK requires that node, its evidence
  parent, projection, and proposal to agree. Each exact occurrence receives one
  mapping even when equal source strings occur elsewhere;
- `candidate_payload` is legal only when that exact canonical occurrence has a
  `normalizedIdentity`; it requires known state/value and reconstructs that
  canonical property. The application cannot relabel source spelling as a
  normalized identity;
- `source_only` is used when a condition or search-hint occurrence has source
  identity text but its canonical shape offers no normalized identity;
  `no_normalized_identity` is used for a listed designation, designation-group
  member, or series occurrence whose closed canonical object has no normalized
  property;
- both non-payload origins require state `unknown`, controlled reason
  `not_extracted|not_yet_reviewed`, temporal scope
  `source_observation|directive_version`, and inherited evidence through the
  single `evidence_parent_node_id`; they cannot carry a normalized value,
  namespace, version, or token; and
- UNIQUE `(projection_id, identity_kind, source_occurrence_node_id)`. No global
  aircraft/manufacturer/model table references these rows and no per-occurrence
  evidence-link copy is created.

The 2002 condition member `6314` maps as `model/source_only/unknown`, inheriting
the `condition-magneto-models` group evidence once. A Cessna hint model member
maps as `model/source_only/unknown`, inheriting that manufacturer-model group's
evidence once. A product-scope manufacturer with an actual canonical
`normalizedIdentity` maps as `manufacturer/candidate_payload/known`. These
origins cannot be interchanged.

#### 2.4 Product and designation scopes

`ad_v4_candidate_app_product_scopes`

- product-scope semantic node/projection/proposal IDs, `scope_key`, product role
  `airframe|engine|propeller|appliance|installed_part|modification`;
- manufacturer presence `property_absent|present`, exact source manufacturer
  value when present, and candidate manufacturer identity-mapping node ID when
  present;
- independent model/serial/part property-presence codes; and
- UNIQUE `(projection_id, scope_key)`. CHECKs require value/mapping only for a
  present manufacturer and distinguish omission from explicit unknown.

`ad_v4_candidate_app_designation_scopes`

- designation-scope semantic node/projection/proposal IDs, parent product scope
  node ID, field kind `model|serial|part_number`, and scope kind
  `all|listed|series_expression|ranges|unknown|not_applicable`;
- exact series expression only for `series_expression`;
- controlled reason and temporal-scope kind only for unknown/not-applicable;
- fixed comparison/evaluation state. Series expressions are
  `unknown/unsupported_expression`, not executable patterns;
- UNIQUE `(product_scope_node_id, field_kind)`; and
- deferred cardinality checks: listed has one or more values and no ranges;
  ranges has one or more ranges and no values; other kinds have neither.

`ad_v4_candidate_app_designation_values`

- semantic node/projection/proposal and designation-scope IDs, exact source
  value, canonical ordinal, and model/series identity-mapping node for that
  exact designation-value semantic node;
- the mapping's `source_occurrence_node_id` must equal this row's semantic-node
  ID, while its `evidence_parent_node_id` equals the one designation-scope node.
  Thus 51 values create 51 mappings but still one parent evidence link;
- UNIQUE `(designation_scope_id, source_value)` and UNIQUE
  `(designation_scope_id, canonical_ordinal)`; and
- ordinals must equal the Slice-2 canonical exact-string set order.

Static cardinality proof over the five calibration packets is mandatory:

| packet | listed value occurrences | identity mappings | parent-scope inheritance edges |
| --- | ---: | ---: | ---: |
| 1998-17-11 | 51 + 30 = 81 | 81 | 2 |
| 2002-13-04 | 6 | 6 | 1 |
| 2008-26-10 | 182 | 182 | 1 |
| 2011-10-09 | 224 | 224 | 1 |
| 2024-14-03 | 7 + 2 + 10 + 33 + 130 = 182 | 182 | 5 |

The multi-model uniqueness gate is therefore feasible for 5 of 5 packets and
cannot collapse two exact value occurrences into one mapping.

`ad_v4_candidate_app_designation_ranges`

- semantic node/projection/proposal and designation-scope IDs, exact lower and
  upper strings, lower/upper inclusive booleans, polarity
  `included|excluded`, canonical ordinal, and fixed lexical comparator version;
- composite uniqueness across the five canonical range identity fields and
  unique ordinal; and
- no numeric coercion or range membership result is stored.

#### 2.5 Conditions and three-valued expressions

`ad_v4_candidate_app_conditions`

- condition semantic node/projection/proposal IDs, `condition_key`, exact
  condition type and operator closed to the V4 enums, temporal-basis kind,
  comparator property presence/value, subject product-role
  presence/value, and subject attribute-key presence/value;
- fixed `evaluation_state = 'unevaluated'` and
  `evaluator_contract = 'none'`;
- UNIQUE `(projection_id, condition_key)`; and
- closed enum and shape checks require the exact subject properties,
  designation groups, group members, and value-assertion children found in the
  canonical candidate. There is deliberately no type/operator compatibility
  matrix in 3A.

Every pair from the independent Slice-2 `conditionType` and `operator` enums
is representable and reconstructable as `unevaluated` when the enclosing
closed schema shape is valid. This representation does not declare that every
pair is meaningful or executable. A future evaluator may narrow semantics only
through a separately reviewed, versioned canonical-boundary and evaluator
contract; it may not reinterpret existing 3A rows.

Subject fields `manufacturer`, atomic `modelOrSeries`, `partNumber`,
`serialNumber`, `stcNumber`, and `attributeValue` are
`ad_v4_candidate_app_value_assertions` children using those exact field codes.
The validator-2 `designationGroup` is stored as one source-faithful group row,
one exact display assertion, and typed member rows with explicit association;
it is never derived from the display string. Manufacturer/model/series
occurrences receive separate unreviewed identity mappings; the assertion and
display values remain source-faithful.

`ad_v4_candidate_app_designation_groups`

- semantic node/projection/proposal and owning-condition IDs, group key,
  association `all_members|any_member|source_group|unknown`, exact source
  display assertion ID, controlled unknown reason and temporal scope, and
  canonical ordinal;
- non-unknown association forbids unknown reason/temporal; unknown association
  requires both plus exact evidence; and
- UNIQUE `(condition_node_id, group_key)` and unique ordinal.

`ad_v4_candidate_app_designation_group_members`

- semantic node/projection/proposal and group IDs, member key, designation kind
  `model|series_expression`, exact source designation/expression, explicit
  manufacturer union state and value/reason/temporal fields, fixed evaluation
  state/reason for series expressions, canonical ordinal, and exact-occurrence
  identity-mapping node;
- group association and typed members come only from canonical validator-2
  bytes, never from source display punctuation; and
- UNIQUE `(group_id, member_key)`, UNIQUE `(group_id, canonical_ordinal)`, and
  composite same-projection FKs for group, manufacturer assertion, and mapping.

`ad_v4_candidate_app_expressions`

- expression semantic node/projection/proposal IDs, owning rule ID, expression
  context `scope|condition`, deterministic expression path, node type, fixed
  result domain/evaluator version, and nullable typed ref columns for scope,
  condition, or rule;
- leaf CHECKs require exactly the correct ref; `not|all|any` have no ref;
- UNIQUE `(owning_rule_id, expression_context, expression_path)`; and
- composite FKs bind every leaf ref to the same projection/proposal.

`ad_v4_candidate_app_expression_edges`

- projection/proposal IDs, parent expression ID, child expression ID, and
  sequence;
- UNIQUE `(parent_expression_id, sequence)`, UNIQUE
  `(parent_expression_id, child_expression_id)`; and
- deferred checks enforce no cross-context edge, no cycle, `not` arity 1,
  `all|any` arity >=2, leaf arity 0, one root per rule/context, and contiguous
  sequence from zero. Sequence is regulatory/canonical and is not sorted.

`ad_v4_candidate_app_rules`

- rule semantic node/projection/proposal IDs, `rule_key`, scope-root expression
  ID, condition property presence and optional condition-root expression ID,
  and fixed evaluator version;
- UNIQUE `(projection_id, rule_key)`; and
- composite FKs bind both roots to the same rule/projection and correct
  expression context.

`ad_v4_candidate_app_rule_exclusions`

- projection/proposal IDs, rule ID, excluded rule ID, and canonical ordinal;
- UNIQUE `(rule_id, excluded_rule_id)` and unique ordinal; and
- same-projection FKs plus deferred acyclicity. Empty exclusions are represented
  by zero rows, not a nullable array.

#### 2.6 Non-controlling search hints

`ad_v4_candidate_app_search_hints`

- search-hint semantic node/projection/proposal IDs, `hint_key`, product role,
  exact source display text, fixed `controlling = false`, fixed
  `exhaustive = false`;
- UNIQUE `(projection_id, hint_key)`; and
- no expression table has a hint-reference column or FK.

`ad_v4_candidate_app_search_hint_groups` and
`ad_v4_candidate_app_search_hint_members`

- group rows preserve canonical group key/ordinal, manufacturer explicit
  union, association `paired|source_group|unknown`, controlled unknown reason,
  temporal scope, and evidence parent;
- member rows preserve group ID, `member_key`, typed `designation_kind`
  `model|series_expression`, canonical ordinal, exact-occurrence unreviewed
  identity mapping, and the single inherited group evidence-parent edge;
- a `model` member requires exact `source_designation` and forbids expression,
  evaluation, and reason columns. A `series_expression` member instead requires
  exact `expression_text`, `evaluation_state = 'unevaluated'`, controlled
  `reason = 'unsupported_expression'`, normalization origin `source_only`,
  normalized state `unknown`, and forbids an exact model designation;
- UNIQUE `(hint_id, group_key)`, UNIQUE `(group_id, member_key)`, and UNIQUE
  `(group_id, canonical_ordinal)`; exact source values are not overloaded as
  relational discriminators; and
- rows may support administrator research only. They are excluded from rule
  reconstruction except as the hint's exact canonical group/member arrays.

The reconstruction discriminator emits every canonical-v2 member variant from
these typed columns. It never decides the variant from punctuation or parses
`expression_text`; evidence is inherited from the group once and not copied per
member.

The 2002 hint reconstructs seven manufacturer groups, 19 exact model members,
and one source-faithful `series_expression` member for `172A through 172H`;
no row contains manufacturer `multiple`, no `172A` through `172H` exact rows
are inferred, and no comma/range/prefix parsing is used.
The 2024 condition reconstructs one Garmin `all_members` group with exact GFC
500 and GSA 28 members; STC and master-drawing assertions remain separate. If
a hint's source does not establish manufacturer/model pairing, the group uses
`association=unknown`, reason `source_ambiguous`, temporal scope, and evidence;
the materializer never assigns a manufacturer heuristically.

### 3. Database completeness and reconstruction contract

At deferred commit, `paprnav_v4_candidate_app_require_complete(projection_id)`
must:

1. lock and verify the parent candidate proposal and exact repeated hashes;
2. verify its Slice-2 canonical bytes/JSON mirror and evidence-binding rows;
3. require exactly one materialized root event and the recorded row counts;
4. require exactly one typed owner for every semantic node and no unowned typed
   row;
5. verify every composite same-projection reference, expression arity/cycle,
   condition child/group set, designation child set, identity occurrence
   mapping, and exact evidence-key set;
6. verify one correction foundation per canonical correction, its exact
   official-document identities, complete ordered reference namespace, one
   evidence set, and all 3A-owned semantic bindings for generation 1;
7. reconstruct the four-field JSONB subtree in canonical array order;
8. require JSONB equality with those four fields extracted from the parent
   proposal mirror;
9. require the application-supplied restricted-JCS subtree bytes/hash and
   projection hash to match server-generated values; and
10. fail the transaction on any mismatch.

PostgreSQL need not implement restricted JCS. It verifies SHA-256 over the
already canonical subtree bytes, relational-to-parent JSONB equality, every
envelope field, and the aggregate row identity/hash set. The application
reconstructs, canonicalizes, and verifies bytes/hash before insert and every
audit read. This follows the reviewed Slice-2 division of responsibility while
preventing self-consistently rehashed forged relational rows.

Property-presence columns are normative. Reconstruction never guesses whether
an absent optional property was unknown. Set arrays sort using the checked-in
Slice-2 schema annotations; expression operands retain stored sequence.

### 4. Index contract without read cutover

The migration creates only integrity, reconstruction, source-audit, and
stale-fold indexes used by the bounded 3A service, in addition to primary,
foreign-key-supporting, and uniqueness indexes:

- projection `(proposal_id, materializer_version)` and request idempotency;
- semantic-node `(projection_id, node_type, node_key)` and typed-owner
  composite-FK support;
- evidence-link `(proposal_id, candidate_binding_id, evidence_key)` and
  `(semantic_node_id, purpose, canonical_ordinal)`;
- designation/group/member parent + canonical-ordinal indexes used for exact
  reconstruction, never source-string lookup;
- expression-edge parent/sequence and child indexes, and exact scope,
  condition, and rule reference-FK indexes;
- correction-root `(proposal_id, correction_key)`, correction-ref
  `(correction_id, canonical_ordinal)`, and binding completeness indexes;
- dependency causal/source IDs and exact predecessor-AD resolution support;
  and
- event `(projection_id, sequence_number)` and partial cause indexes required
  by the stale fold.

There is no index on source manufacturer/model spelling, normalized values or
tokens, product-role lookup, search hints, aircraft IDs, or candidate make/model
combinations. Slice 3A makes no hot-path or matching-readiness claim. The later
reviewed identity bridge must define its own aircraft/canonical-identity join
and indexes in the matching slice; it cannot reuse an unreviewed candidate
mapping as authority. Repository tests assert both the absence of these
premature index definitions and the absence of released readers using 3A.

### 5. Materializer, authorization, and concurrency contract

#### 5.1 Default-off capability gates

Two independent application settings are introduced with literal defaults of
`false`:

- `PAPRNAV_AD_V4_VALIDATOR2_WRITES_ENABLED=false`; and
- `PAPRNAV_AD_V4_SLICE3A_ROUTES_ENABLED=false`.

The first gates every validator-2 candidate POST before parsing or persistence.
The second gates registration/exposure of the 3A materialization POST and both
3A audit GET routes. Migration 0027 also creates two database gate keys,
`validator2_write_enabled` and `materializer3a_enabled`, both default false.
The application role may read but not enable them; only the deployment database
role may change them through the audited gate procedure. Enabling one gate or
flag never implies the other. Merely running 0027 cannot expose a v2 writer or
a 3A route.

The application has fixed compiled capabilities
`SUPPORTED_V4_VALIDATOR_PAIRS` and `SUPPORTED_V4_MATERIALIZERS`. Migration 0027
provides a read-only database capability function returning the exact revision,
supported validator/canonicalization pairs, materializer version, and the two
gate states. Startup and every write transaction require all three layers:

1. every required application flag and database gate is true;
2. the compiled application capability contains the requested fixed version;
   and
3. the database capability function exists and returns the exact compatible
   0027 capability.

Missing/mismatched database capability, unknown compiled version, or a required
false application/database gate fails closed before writes with stable
`capability_disabled`, `validator2_write_gate_disabled`, or
`materializer3a_gate_disabled`, or
`schema_capability_mismatch`; it never falls back to v1. The transaction repeats
the database capability check after acquiring the proposal/version lock so a
startup check is not trusted as a write-time guarantee. Audit routes require
the 3A application flag, database `materializer3a_enabled`, and compatible
reader capability, but do not require `validator2_write_enabled`: they may read
and verify already-existing projection rows only. They never materialize a
missing projection. Authorization remains the separate exact-membership check
below.

The validator-2 candidate POST requires its application flag plus database
`validator2_write_enabled`. The 3A materialization POST/service transaction
requires **both** application flags, **both** database gates
`validator2_write_enabled` and `materializer3a_enabled`, and both compiled
capabilities. This dependency remains true for a preexisting v2 candidate. If
validator-2 writes are disabled while 3A audit is enabled, materialization
returns stable `validator2_write_gate_disabled` and writes zero request,
projection, dependency, correction, or event rows; audit GET may inspect only a
projection that already exists.

The materializer may perform an unlocked early rejection, but after locking its
parent proposal and before any 3A row it reads both database gate rows `FOR
SHARE`. The audited deployment procedure disables a gate under `FOR UPDATE`.
Therefore a concurrent disable either commits first and the materialization
rejects with zero rows, or waits for an already-authorized materialization to
commit and then prevents every later write. No transaction observes a
half-disabled gate pair.

The validator-2 candidate writer follows the same global proposal-before-gate
order: before reading `validator2_write_enabled` under `FOR SHARE`, it
explicitly acquires `ROW EXCLUSIVE` on the Slice-2 proposal table (the mode its
later INSERT requires). Thus downgrade's proposal-table lock cannot invert with
a candidate writer holding a feature-gate row.

These gates prove only this process's configuration/code and the connected
database schema. They do not prove that every application instance in a fleet
has completed rollout. Therefore the compatibility release—dual v1/v2 readers
with both flags still false—must be fully deployed and externally verified
before deployment configuration may enable the validator-2 gate. The 3A flag
is enabled only in a later configuration rollout after v2 write verification.

One 3A HTTP writer is in scope when its route gate is enabled:

`POST /api/v1/ads/directives/{directive_id}/v4/candidate-proposals/{proposal_id}/applicability-projection`

It requires `Idempotency-Key` and `Paprnav-Acting-Membership-Id`, has no JSON
body, and derives the fixed materializer version server-side. Only an active
platform admin may call it. It returns 201 for a new complete projection and
request, 200 for exact retry or reuse, 409 for an idempotency mismatch or
integrity/stale-parent conflict, 422 for a proposal that cannot be projected,
and 403 for authorization denial.

Platform-admin-only audit endpoints are:

- `GET .../{proposal_id}/applicability-projection`; and
- `GET .../{proposal_id}/applicability-projection/reconstruction`.

Both GETs require the same `Paprnav-Acting-Membership-Id` header as POST. For
all three endpoints the server begins one transaction, loads the authenticated
user and the exact selected membership under row lock, and verifies membership
user ID, active status, and `platform_admin` role before loading any candidate
metadata. A selected inactive/shop/foreign membership is denied even if the
same user has another active platform-admin membership. A concurrent revocation
either commits before the lock and denies the call or waits until the
authorized transaction ends; authorization cannot be assembled from multiple
memberships. GET is side-effect-free and does not create an audit row, but the
response includes the selected membership ID and evaluated policy version as
ephemeral authorization context.

The first returns verified metadata/counts/event-fold state. The second returns
only the verified four-field reconstructed candidate subtree and hashes. It is
explicitly labeled candidate-only and does not return source text. There is no
list/search/match endpoint.

The service uses this total lock order:

1. active user and exact active membership rows;
2. advisory idempotency lock over actor, membership, action, policy version,
   and key;
3. parent candidate proposal row;
4. database feature-gate rows in lexical gate-key order, `FOR SHARE`;
5. all bound Slice-1 fragments in lexical fragment-ID order, followed by full
   lifecycle revalidation;
6. advisory projection lock over proposal ID and materializer version;
7. correction foundations/refs and outgoing dependencies in canonical order;
8. any predecessor/target projection roots that may receive target-local
   dependency rows or stale events, locked in lexical projection-ID order; and
9. semantic insertion followed by deferred completeness checks and commit.

The request hash covers the directive ID, proposal ID, fixed action, exact
validator/canonicalization pair, and fixed materializer version. Same
key/different request returns 409 with no rows.
Same key/same request returns the same request/root. Two keys for one proposal
append two request audit rows but reuse one projection. Deterministic node IDs,
unique constraints, advisory locking, and post-conflict equality verification
make concurrent creation converge without 500.

The materializer parses only verified canonical proposal bytes through the
Slice-2 validator. It has no dict-only bypass, fixture loader, provider writer,
CLI writer, seed path, or direct-SQL helper. Tests may use direct SQL only to
prove database rejection.

### 6. Correction, supersession, and stale fold

The projection root and semantic rows never change. Candidate staleness is a
derived fold over immutable facts:

1. start at the sequence-0 `materialized` event;
2. verify the hash chain and fold later stale events;
3. revalidate parent proposal bytes/hash/gate and every bound fragment's live
   lifecycle;
4. inspect Slice-2 `corrects_candidate|replaces_candidate` relationships whose
   predecessor is this proposal;
5. inspect evidence-bound 3A correction and supersession dependency signals;
   and
6. return `candidate_verified`, `candidate_stale`, or
   `dependency_unresolved` plus all reason codes.

`candidate_verified` means only that the derived projection still agrees with
its unreviewed parent candidate; it does not mean approved or applicable.

When materializing a successor, explicit same-directive candidate
relationships append deterministic `candidate_corrected` or
`candidate_replaced` events to already materialized predecessors. The internal
repair helper is not a background process. It runs only inline and
opportunistically inside an already authorized 3A materialization service
transaction, using the same locks, capability gates, cause identity, and event
idempotency. An authorized audit transaction may invoke the same helper only in
detection mode: GET reports a missing convenience event but remains
side-effect-free. There is no cron, queue consumer, worker, scheduler, CLI,
repair endpoint, startup sweep, or new operational writer. On every read, the
live fold still detects the relationship even if the convenience event has not
yet been appended.

For a canonical supersession relation, target resolution is exact AD number.
Before lookup, the relation's successor must byte-equal this proposal's known,
evidence-bound canonical AD number. Missing/unknown AD identity or a different
successor records `unresolved` with a stable reason and produces no target
lookup, incoming dependency, or event. Exactly one matching predecessor
directive permits a candidate-only signal: a deterministic target-local
incoming dependency is created and the target projection event names it via
same-projection composite FK. Zero or multiple matches records explicit
unresolved or ambiguous state and affects no other row. Contradictory candidate
signals fail closed and never choose a legal winner. Canonical cause hashing,
causal uniqueness, sorted locks, and equality-on-conflict make retries and
concurrent signal workers converge. No V3/released status or current pointer
is read or modified.

An authoritative correction contained in the same candidate is represented by
the shared correction foundation and its complete ordered refs, with 3A-owned
refs bound to changed applicability nodes. It describes why the candidate has
its present content; it does not stale that same projection. Only a later
candidate relationship or evidence change stales it.

## Alternatives considered

### Materialize the entire V4 proposal in one migration

Rejected. Requirements, timing, branches, documents, and AMOC semantics have
different correctness and human-signoff risks. Splitting 3A makes
applicability round-trip and bloat behavior independently reviewable.

### Populate existing V3 applicability tables

Rejected. Those tables feed current readers and contain flattened/copy-heavy
representations. Reuse would create an accidental read cutover, mix V3 and V4,
and erase the candidate-only boundary.

### Add JSONB indexes to the Slice-2 proposal

Rejected. JSONB path indexes do not enforce typed references, same-candidate
graphs, evidence links, explicit uncertainty, or relational reconstruction.
They also leave the 182-model/shared-condition bloat question unanswered.

### Store canonical source text on each semantic row

Rejected. Slice 1 stores exact source clauses once and Slice 2 binds them once
per proposal. Repetition would reintroduce the defect this design is intended
to remove and allow copied text to drift from retained bytes.

### Create a global authoritative manufacturer/model registry now

Rejected. Current V4 has no per-model reviewed normalized identity, no human
signoff occurs in 3A, and aircraft canonical identity migration is excluded.
Candidate identity assertions remain separate and untrusted.

### Automatically normalize model spelling, prefixes, or series

Rejected. Case/punctuation/prefix heuristics can broaden applicability across
manufacturers or models. Current model normalization is explicit unknown, and
series expressions are preserved but not executed.

### Materialize automatically inside the Slice-2 candidate POST

Rejected. It would change the closed Slice-2 transaction and make candidate
storage depend on the larger normalized schema. An explicit idempotent 3A
service permits existing candidates, independent rollback, and bounded review.

### Mutable projection status or in-place correction

Rejected. Mutable flags lose the causal record and race with readers. Immutable
events plus live validation make stale state reproducible.

### Treat candidate supersession as authoritative

Rejected. An unreviewed candidate can only generate an evidence-bound stale
signal among candidate projections. Publication and legal current-state
selection require later human review.

## Trust, authorization, and audit boundaries

- Official PDFs and Slice-1 fragments remain source evidence. The Slice-2 V4
  candidate remains an unsigned machine/admin proposal. Slice-3A normalized
  rows are a derived candidate projection of that proposal.
- Round-trip equality proves lossless representation, not regulatory truth,
  identity correctness, series membership, or aircraft applicability.
- The server derives all IDs, hashes, gate, versions, actor context, identity
  mapping origin, and stale events. The caller supplies no normalized rows,
  hash, status, or event payload.
- The materializer actor may later be disqualified from sole human approval;
  no approval exists here.
- Platform-admin membership is rechecked under lock at each POST. Audit GETs
  apply the same role boundary. Unauthorized callers receive no candidate JSON
  or evidence metadata.
- Automated stale marking is deterministic recalculation from immutable facts
  and requires no human review. It cannot alter a signed decision or convert
  uncertainty into an affirmative result.
- Database immutability protects against application and direct-SQL mutation;
  database-owner bypass remains operational authority and is not presented as
  an application security boundary.

## Read paths and consumers

In-scope reads are limited to:

- the materializer's verification of Slice-2 proposal/evidence rows;
- its post-insert relational reconstruction and stale fold;
- platform-admin projection metadata and reconstruction audit endpoints; and
- migration/test inspection.

The implementation review must search all callers/readers and prove these
remain unchanged and do not query 3A tables: V3 extraction/review,
`applicability_targets`, `ad_target_applicability`, released AD catalog,
aircraft AD pages, matching, coverage, compliance requirements, due state,
observability counts, exports, jobs, frontend APIs, and UI.

No query in this slice answers “does this AD apply to this aircraft?” The
candidate-shaped indexes are unused until a later publication/matching slice
introduces reviewed global identities and a separately reviewed read contract.

## Write paths and administrative paths

The only supported writer is the projection service called by the platform-
admin POST. Its internal deterministic stale-event helper is part of the same
service/repository boundary and can append only within that authorized POST
transaction. GET calls its detection-only path and is strictly
side-effect-free: it folds stored events and live immutable dependencies but
neither enqueues nor writes repair. The response never depends on a convenience
stale event existing.

No provider job, CLI, seed, V3 translator, calibration loader, frontend form,
or generic ORM CRUD writer is added. Tests construct positive rows through the
service. Direct SQL appears only in negative PostgreSQL tests.

## Migration, compatibility, correction, and rollback

Implementation requires migration `0027` after `20260901_0026`. It introduces
the validator-2/c14n-2 compatibility boundary and Slice-3A together. It creates
the 3A tables, constraints, triggers, functions, and indexes above, plus the
version constraints required to keep existing Slice-2 candidate/audit rows
verifiable.

The proposal table already records `validator_version` and
`canonicalization_version`; 0027 verifies every existing row is the exact v1
pair and rejects an unrecognized value. It adds both non-null columns to
`ad_v4_candidate_evidence_bindings`, `ad_v4_candidate_submissions`,
`ad_v4_candidate_submission_relationships`, and
`ad_v4_candidate_proposal_events`. Existing child rows are backfilled in one
locked transaction from their parent proposal/submission as
`paprnav-ad-v4-validator-1` / `paprnav-ad-v4-c14n-1`, verified against their
unchanged v1 canonical bytes/hashes, then constrained `NOT NULL`. This is a
version-metadata backfill only; no canonical bytes, hash, proposal identity,
evidence binding, provenance, or event is rewritten.

Composite FKs/triggers require:

- binding and submission version pair = parent proposal pair;
- relationship pair = owning submission pair, while its predecessor proposal
  may independently be v1 or v2 and remains named by immutable ID;
- event pair = both its proposal and creator submission pair; and
- every 3A root/request/node/event repeats the v2 proposal pair exactly.

Database hash validators dispatch only the closed pairs
`validator-1/c14n-1` and `validator-2/c14n-2`; mixed pairs or unknown versions
fail. V1 rows use the exact existing v1 domains/envelopes. V2 rows use the
domains/envelopes in section 0. Proposal content uniqueness becomes
`(directive_id, validator_version, canonicalization_version, canonical_hash)`.
Idempotency and same-content reuse occur only within an identical version pair
and its hash semantics. A logically similar v1 and v2 payload therefore creates
two distinct immutable proposal identities, never a cross-version reuse.

Existing candidate proposals remain valid and unmaterialized until explicitly
requested. The 3A materializer accepts only the v2 pair; dual-version audit
readers verify both. V3 bytes, hashes, reviews, materializations, and readers
remain unchanged.

Correction/replacement creates a new Slice-2 candidate and a new 3A projection.
The old projection is retained and append-staled. Canonical authoritative
corrections and supersession relations become evidence-bound dependency rows;
they do not rewrite prior projections or released state.

Deployment order is mandatory:

1. apply 0027, whose database validators accept/read both closed pairs and
   remain compatible with the existing v1 writer;
2. deploy the compatibility application that reads/verifies v1 and v2 but
   continues writing only v1, with both new settings explicitly false;
3. externally verify that compatibility release across the serving fleet;
   this operational evidence is a prerequisite but is not inferred from the
   flags themselves;
4. after capability checks pass, the deployment role enables database
   `validator2_write_enabled`, then configuration
   `PAPRNAV_AD_V4_VALIDATOR2_WRITES_ENABLED`; and
5. only after v2 writes are proven, enable database
   `materializer3a_enabled`, then configuration
   `PAPRNAV_AD_V4_SLICE3A_ROUTES_ENABLED` in a separate rollout.

Application rollback reverses feature exposure, not data meaning: set the 3A
application flag false and drain those requests, disable database
`materializer3a_enabled`, then set the v2-write application flag false and
drain writes before disabling database `validator2_write_enabled`, while
retaining the dual-version reader/verifier.
All immutable v2 rows remain candidate-only and audit-readable. Deploying any
pre-v2 application or database code while a v2 proposal or dependent audit row
exists is explicitly prohibited. Nothing falls back to V3, and no released
behavior can resurrect because 3A never feeds a released reader.

Physical downgrade uses a fixed dependency-safe lock order and executes in one
transaction:

1. acquire `ACCESS EXCLUSIVE` on the Slice-2 proposal table first, before
   inspecting a proposal or touching any 3A table. This is the global boundary:
   candidate creation and every 3A materializer also acquire/lock the Slice-2
   parent proposal before any 3A root or child;
2. while retaining that lock, lock the database feature-gate table, then
   Slice-2 binding, submission, relationship, and event tables in that fixed
   order, then every 3A root and child table in the same parent-before-child
   order used by the materializer. DDL drops objects only later and in reverse
   dependency order;
3. refuse before DDL if any 3A row exists;
4. independently refuse if any proposal uses validator-2/c14n-2 or if any
   binding, submission, relationship, or event carries the v2 pair, even when
   every 3A table is empty;
5. verify all remaining Slice-2 rows are internally consistent v1 rows;
6. only for a v1-only database, drop 3A objects, restore the exact 0026 v1
   functions/constraints, and remove the child version columns; and
7. return to 0026, prove all v1 rows remain readable, then prove re-upgrade
   backfills the same metadata and preserves every byte/hash.

A concurrent v2 candidate creation that reaches the proposal first commits and
causes downgrade refusal; if downgrade owns the proposal-table lock first, the
writer waits and then either observes 0026/v1-only mode and refuses v2 or
continues after a failed downgrade. A materializer that locks its parent first
either commits before downgrade's proposal lock and makes the 3A emptiness gate
refuse, or waits without holding a 3A lock. Downgrade never waits on a 3A lock
while a materializer waits on the proposal lock, so the old lock inversion and
deadlock are impossible. No interleaving silently loses a candidate or
projection. An empty-3A database with one unmaterialized v2 proposal still
refuses downgrade. No downgrade truncates, deletes, or rewrites candidate data.
Because v2 rows are immutable, a used-v2 installation is rolled back
operationally with dual readers or recovered into a separately verified pre-v2
snapshot/new database; it is never forced to 0026.

## Test strategy

Every verification report uses `x passed out of x` and names skipped or
unexecuted gates separately.

### Five-packet positive and reconstruction gates

For each of the five source-accounted calibration packets after the reviewed
validator-2 candidate corrections in section 0 (not by mutating any stored
validator-1 proposal):

1. enter through the real Slice-1 retained-evidence admission and Slice-2
   candidate persistence boundary;
2. call the 3A materializer, never direct fixture SQL;
3. reconstruct solely from 3A rows;
4. require JSON equality and canonical byte/hash equality with `A(P)`; and
5. prove exact retry and a second-origin request reuse the same projection.

Expected: **5 passed out of 5 materializations**, **5 passed out of 5
relational reconstructions**, **5 passed out of 5 subtree hashes**, and **5
passed out of 5 evidence-set reconciliations**.

Predecessor compatibility is a separate gate: the original validator-1 1998
candidate remains hash-verifiable and audit-readable **1 passed out of 1**, is
refused for 3A materialization with `predecessor_semantic_defect` **1 passed
out of 1**, and remains byte/row/event unchanged after the corrected
validator-2 candidate is stored **1 unchanged out of 1**.

A generated representation gate covers the current 9 condition-type values ×
10 operator values: **90 represented and reconstructed out of 90** with fixed
`unevaluated/none`, without claiming executable compatibility. Separate schema
negatives reject unknown enum values, missing discriminator-required fields,
extra properties, or a stored evaluation result.

Packet-specific assertions:

- 2024-14-03: exactly 5 product scopes, 182 model rows, 1 condition, 1 rule,
  and one shared condition/evidence identity; no source-text column, 0 model-
  level evidence links, 182 exact-occurrence unknown identity mappings
  using 5 parent-scope inheritance edges, and no per-model
  condition/rule/evidence
  copy. The GFC 500/GSA 28 group is `all_members`, not parsed display text.
- 2011-10-09: exactly 1 scope, 224 model rows, 0 conditions, 1 rule, an
  evidence-bound supersession dependency signal whose successor equals the
  proposal AD number, and no requirement/timing row.
- 2002-13-04: exact conflicting-evidence serial `unknown`, 4 conditions, 1
  rule, articulated 3-member/5-member/atomic designation groups, and 1
  non-controlling/non-exhaustive search hint with seven manufacturer groups
  and exactly 20 typed members: 19 exact model members plus one exact
  `series_expression` value `172A through 172H`; hint IDs are absent from all
  expressions. There are zero inferred exact `172A` through `172H` model rows,
  specifically no exact `172B` or `172H` row.
- 1998-17-11: 2 scopes, 81 models, 2 conditions, 1 rule; component-owned work
  facts remain candidate condition values and do not become aircraft records.
  The unknown provenance operand uses explicit unknown state; the legacy known
  sentinel is rejected for new materialization.
- 2008-26-10: 1 scope, 182 models, 4 conditions, 1 rule, and exact
  shared `correction-2010` foundation with two ordered refs, two evidence links
  once, one 3A scope binding, and one explicit future-3B requirement ref; no
  service-bulletin/document/AMOC semantic row is created in 3A.

### Structural and semantic negatives

Reject through the production materializer and, where stated, direct
PostgreSQL:

- wrong proposal/directive, non-candidate gate, changed canonical/hash/binding
  envelope, invalid or transitioned evidence, and parent changed between
  validation and insert;
- any partial projection, count/hash mismatch, orphan typed node, duplicated
  stable key, wrong node type owner, or reconstructed JSON differing by one
  property/value/order/presence bit;
- cross-projection/cross-proposal scope, condition, expression, exclusion,
  identity, dependency, or evidence link;
- evidence key from another proposal, fragment ID/hash substituted under a
  valid key, missing node evidence, or copied source text submitted to a table
  that has no such column;
- known assertion without value, unknown/not-applicable without reason,
  temporal scope, or evidence, and SQL NULL used as an unknown state;
- listed scope with zero values, ranges with zero ranges, child rows on `all`,
  series expression made executable, duplicate source values/ranges, or
  noncanonical ordinals;
- a condition pair accepted by Slice 2 that cannot be represented exactly,
  any non-`unevaluated` state, omitted/present subject mismatch, unexpected
  subject/group member, display-text parsing, or opaque predicate JSON;
- leaf expression with wrong/multiple refs, `not` with other than one child,
  `all|any` with fewer than two children, noncontiguous sequence, cycle,
  cross-context edge, rule/exclusion cycle, or requirement-state ref;
- search hint marked controlling/exhaustive or referenced by an expression;
- expansion of `172A through 172H` into any exact 172A-H member, construction
  of exact 172B/172H rows, prefix/range execution of that expression, or a
  series-expression row without `unknown/unsupported_expression`;
- model normalization claimed known without an actual canonical
  `normalizedIdentity`, `candidate_payload` origin without that exact property,
  source-only origin without unknown reason/temporal/evidence inheritance,
  one mapping reused by two value occurrences, and normalization that
  case/punctuation-folds a source value; and
- incomplete, reordered, duplicated, or cross-proposal correction refs;
  duplicated correction evidence; missing 3A correction binding; or a 3B
  binding that attempts to create a second correction root;
- self-consistently rehashed direct-SQL forgeries of root, node, link, request,
  event, dependency, or reconstruction bytes.

### Idempotency, concurrency, stale state, and authorization

- default configuration exposes 0 v2 write paths and 0 3A routes; applying
  0027 alone leaves both disabled; expected **2 passed out of 2**;
- the exact four application/database gate combinations are exercised with a
  preexisting v2 candidate: off/off exposes no writer or audit; on/off permits
  v2 candidate writes but no 3A POST/GET; off/on permits audit GET of an
  existing projection only, while materialization rejects
  `validator2_write_gate_disabled` and leaves 0 request, projection,
  dependency, correction, or event rows;
  on/on permits the reviewed v2-write/materialize/audit sequence; expected
  **4 passed out of 4**;
- application/DB disagreement for either named gate always resolves to off;
  neither config nor a database gate alone enables its surface;
- either enabled flag with missing/old database capability or absent compiled
  application capability fails startup and the transactional write guard;
  migration mismatch during a running process fails the repeated in-transaction
  check with no rows; expected **5 passed out of 5**;
- compatibility-release startup holds both flags false, and rollback tests
  disable/drain 3A then v2 writes while dual-version reads remain available;
  tests assert no flag or migration claims fleet-wide rollout completion;
- deterministic concurrent gate-disable/materialization barriers prove either
  materialization commits fully before disable or disable wins and the POST
  writes 0 request/projection/dependency/correction/event rows: expected
  **2 passed out of 2**;
- new/exact retry/new key same proposal: expected **3 passed out of 3**;
- POST and each GET with selected platform admin versus maintenance shop,
  owner, organization admin, inactive/foreign selected membership, another
  valid membership present, and revocation under lock;
- concurrent same key, different keys/same proposal, same key/different
  proposal, and rollback after child failure: expected **4 passed out of 4**;
- two concurrent materializations with reversed evidence order and overlapping
  correction/supersession targets complete without deadlock or 500: expected
  **2 passed out of 2**;
- correction/replacement relation, evidence lifecycle transition, uniquely
  resolved supersession signal, unrelated successor, unknown proposal AD
  identity, ambiguous AD-number target, contradictory candidate signals,
  exact retry, and concurrent insertion fold fail-closed without UPDATE;
- direct UPDATE/DELETE rejection on every new table plus event-chain forgery.

### Isolation, index, and migration gates

- snapshot existing V3/released reader results before/after materializing all
  five candidates: expected **5 unchanged out of 5**;
- repository import/SQL route scan finds **0 existing released readers out of
  all inspected readers** referencing a 3A table;
- catalog/matching/coverage/due endpoints remain unchanged and return no
  candidate projection;
- PostgreSQL catalog asserts every named integrity/audit/stale index exactly
  and asserts zero normalized-token, source-spelling, aircraft-ID, or matching
  indexes;
- v1/c14n-1 and v2/c14n-2 reader/hash parity vectors; v1 and v2 same logical
  values produce distinct identities; same-version retries reuse exactly;
  child rows reject a different pair; and all five v2 envelope/domain hex
  vectors match Python/PostgreSQL;
- fresh 0027 upgrade/backfill preserves all v1 bytes/hashes; empty-3A with one
  unmaterialized v2 proposal refuses downgrade; any v2 dependent audit row
  refuses downgrade; concurrent v2-write/downgrade and
  materializer/downgrade races serialize safely; v1-only empty-3A downgrade
  returns to 0026 with v1 readable; and re-upgrade restores exact metadata;
- UPDATE/DELETE rejection preserves immutable v2 proposals, bindings,
  submissions, relationships, and events; and
- migration/model parity plus deferred constraint execution on PostgreSQL, not
  SQLite substitutes.

## External-critic nonfinding clarifications

- **224-model performance:** implementation must run the complete 2011 packet
  through PostgreSQL materialization, deferred completeness, and reconstruction
  for 20 measured iterations with `SET LOCAL statement_timeout = '5s'` and
  `lock_timeout = '2s'`. Every run must complete inside 5 seconds and measured
  p95 must remain below 2.5 seconds, with query plans and row counts attached to
  implementation evidence. Failure blocks the migration; it cannot be fixed by
  weakening exact reconstruction or silently moving integrity to Python.
- **Correction generations:** only foundation/binding generation 1 is defined
  in 3A/3B. A second generation or re-correction of the same canonical
  correction key requires a future reviewed validator/schema/migration. V2
  rejects duplicate correction keys, and 3A never invents generation 2.
- **Platform administrator scope:** `platform_admin` is a role on one
  organization-membership row, not a global user flag. One user may hold that
  role in one organization and a non-admin role elsewhere. The exact selected
  active membership alone authorizes each request; roles are never combined
  across memberships.

## Expected file scope

This framing phase edits only:

- `.ai/review-runs/T081-V4-SCHEMA-SLICE-3A/decision.md`; and
- generated design packet artifacts inside that same new review run.

Expected implementation scope after design PASS is additive and bounded to:

- one backward-compatible validator-2/c14n-2 schema/profile and all five exact
  v2 hash domains while retaining byte-identical validator-1/c14n-1 read/hash
  dispatch for stored candidates;
- corrected 1998 explicit-unknown and 2002/2024 designation-group/search-hint
  calibration proposals, an exact hash-locked legacy validator-1 1998 fixture,
  plus schema, service, canonical, and evidence regressions proving existing
  stored validator-1 proposals remain immutable and auditable;
- migration 0027 after 0026, including locked v1 metadata backfill on Slice-2
  audit children, dual-version constraints/triggers, and the additive 3A
  tables, plus matching ORM models;
- the shared correction-foundation tables
  `ad_v4_candidate_corrections`, `ad_v4_candidate_correction_refs`,
  `ad_v4_candidate_correction_semantic_bindings`, and
  `ad_v4_candidate_correction_evidence_links`; their service may read and
  verify only canonical `authoritativeCorrections` plus referenced
  `officialDocuments` identity/evidence fields. Complete future-3B namespace
  refs are retained, but requirement/recurrence/AMOC/document semantics remain
  deferred;
- default-off application configuration for validator-2 writes and 3A routes,
  fixed compiled capability declarations, and the 0027 database capability
  function, default-off gate rows, deployment-role-only audited gate procedure,
  and transactional checks;
- one candidate applicability materializer/reconstructor/stale-fold service;
- narrow platform-admin request/response schemas and POST/audit GET routes;
- focused materializer, reconstruction, authorization, concurrency,
  PostgreSQL, migration, isolation, and five-packet calibration tests; and
- implementation evidence inside the Slice-3A run.

The reviewed validator-2 correction above is the only permitted V4 schema and
calibration edit. It must not mutate prior review records, retained source
PDFs/fragments, or stored validator-1 candidate rows. Implementation must not
edit the domain contract, V3 models/services/data, released readers,
frontend/UI, aircraft identity or configuration, requirement/timing/document/
AMOC semantic materialization, publication, matching, compliance, or due state.

## Known uncertainty and design-review questions

1. Canonical V4 intentionally has no per-model normalized identity. This design
   resolves the gap conservatively as explicit `unknown/not_extracted` in a
   separate unreviewed candidate mapping. The adversary should test that no
   implementation is tempted to promote exact source spelling or a heuristic
   alias to reviewed identity.
2. `series_expression` is source text, not a reviewed comparator grammar. It is
   stored losslessly with evaluation disabled. A later identity/series review
   must define executable membership before any matching cutover.
3. `airworthiness_directives.ad_number` is not currently a guaranteed unique,
   non-null identity. Candidate supersession resolution therefore permits only
   exactly-one resolution, records zero/multiple as explicit unresolved/
   ambiguous, and never changes released state.
4. PostgreSQL relational reconstruction must be measured against the 224-model
   packet. If one deferred function exceeds bounded transaction/statement
   limits, implementation must optimize its relational aggregation without
   weakening the exact-equality gate or silently moving all integrity to
   Python.
5. No candidate normalization, source-spelling, or aircraft hot-path index is
   created. A later matching decision must define the reviewed identity bridge
   and own any usable lookup index.
6. The cross-slice correction identity is resolved here: 3A creates the shared
   immutable foundation and complete ordered namespace; 3B may add only its
   owned immutable semantic bindings under that foundation.

None of these questions permits source-text copying, null-as-unknown,
manufacturer/model concatenation, candidate publication, V3 fallback, aircraft
matching, or a hidden writer.


## Current finding ledger

```json
[
  {
    "id": "T081-V4-S3A-DA-001",
    "stage": "design",
    "reviewer": "/root/v4_schema_adversary",
    "severity": "blocker",
    "status": "closed",
    "invariant": "Every valid calibration candidate can be materialized deterministically, including every listed model, while model normalization remains explicit unknown and does not duplicate evidence.",
    "summary": "The model identity-mapping cardinality allows only one mapping per designation scope, but every calibration designation scope contains multiple model values.",
    "evidence": [
      ".ai/review-runs/T081-V4-SCHEMA-SLICE-3A/decision.md:381-388 requires each model mapping to reference its parent designation-scope node and declares UNIQUE (projection_id, identity_kind, source_semantic_node_id).",
      ".ai/review-runs/T081-V4-SCHEMA-SLICE-3A/decision.md:424-435 requires every model designation-value row to name its model identity-mapping node.",
      "Independent enumeration found 10 listed designation scopes out of 10 with more than one model: counts are 51, 30, 6, 182, 224, 7, 2, 10, 33, and 130. The proposed uniqueness therefore conflicts on the second model in every scope and makes 0 of 5 calibration materializations feasible as written."
    ],
    "impact": "The positive 5/5 gate cannot execute. Any implementation must either omit required per-model mappings, violate its own uniqueness constraint, or collapse multiple exact source designations into one row and lose round-trip identity.",
    "requiredClosure": "Define a nonconflicting identity for one mapping per exact designation occurrence, such as a composite including the designation-value node or exact source value, while retaining one parent-scope evidence inheritance edge and no per-model evidence copy. Provide a row/key/FK example for a multi-model scope and a static 5/5 cardinality proof.",
    "closureEvidence": [
      "decision.md Safety invariant 9 and section 2.3 make source_occurrence_node_id the exact designation-value/member node, require one mapping per occurrence, and inherit source support through one evidence_parent_node_id without per-model links.",
      "decision.md section 2.4 gives the 5/5 static cardinality proof: [51,30], [6], [182], [224], and [7,2,10,33,130] exact value occurrences produce 81, 6, 182, 224, and 182 distinct mappings with 2,1,1,1,5 parent-scope inheritance edges.",
      "Independent closure review recomputed 10 listed scopes out of 10 and verified that source_occurrence_node_id is now the per-value semantic node while evidence_parent_node_id remains the shared designation-scope node. UNIQUE (projection_id, identity_kind, source_occurrence_node_id) therefore permits every occurrence without per-model evidence links."
    ]
  },
  {
    "id": "T081-V4-S3A-DA-002",
    "stage": "design",
    "reviewer": "/root/v4_schema_adversary",
    "severity": "blocker",
    "status": "closed",
    "invariant": "Splitting applicability from obligations preserves one exact, evidence-bound correction object and permits a later full relational round-trip without duplicate or disconnected authority.",
    "summary": "The shared correction-generation boundary is deferred even though a current calibration correction spans Slice 3A and Slice 3B namespaces.",
    "evidence": [
      ".ai/review-runs/T081-V4-SCHEMA-SLICE-3A/decision.md:306-324 creates per-applicability change-dependency nodes, reduces out-of-scope correction references to a count, and assigns their typed projection to Slice 3B.",
      ".ai/review-runs/T081-V4-SCHEMA-SLICE-3A/decision.md:973-976 explicitly leaves the shared projection-generation root as a later design question.",
      "backend/tests/fixtures/ad_v4_calibration/2008-26-10.proposal.json:1064-1083 contains one correction-2010 object whose changedSemanticRefs set includes both productScopes/scope-cessna and requirements/req-report under one document pair and one evidence-key set."
    ],
    "impact": "Slice 3A can neither prove nor preserve the future one-object correction identity. Slice 3B would have to duplicate correction provenance/evidence or invent an unreviewed merge convention, and the combined relational model could not prove an exact full-proposal correction round-trip.",
    "requiredClosure": "Resolve the shared foundation before 3A: define one proposal-scoped immutable correction root keyed to the canonical correction object, with exact evidence/document identity and namespace edges that 3A and 3B can add under one completeness/generation contract. Alternatively defer the whole correction projection, but then remove 3A correction-derived state. Demonstrate exact reconstruction of correction-2010 after both slices without repeated evidence links or count-only placeholders.",
    "closureEvidence": [
      "decision.md section 2.1.1 defines one immutable proposal-scoped correction root, complete ordered refs for all current and future-3B namespaces, one correction evidence set, immutable generation bindings, and namespace ownership/completeness rules.",
      "decision.md section 2.1.1 reconstructs correction-2010 as one root, two ordered refs (productScopes/scope-cessna and requirements/req-report), two evidence links once, one 3A binding, and one later 3B binding without duplicating correction/document/evidence identity.",
      "Independent closure review traced correction-2010 against the canonical fixture: the foundation stores the complete two-ref set and one two-key evidence set at generation 1; 3A binds only scope-cessna and 3B can append only the req-report semantic binding without updating the root/ref/evidence authority or changing serialized correction JSON."
    ]
  },
  {
    "id": "T081-V4-S3A-DA-003",
    "stage": "design",
    "reviewer": "/root/v4_schema_adversary",
    "severity": "blocker",
    "status": "closed",
    "invariant": "Regulatory or configuration uncertainty is an explicit unknown state with reason, temporal scope, and evidence; a known text value cannot stand in for uncertainty.",
    "summary": "The mandatory 1998 calibration encodes an unknown repairer state as a known string, contradicting the contract and Slice 3A's own unknown invariant.",
    "evidence": [
      ".ai/AD_EXTRACTION_DOMAIN_CONTRACT.md:103-112 requires missing, ambiguous, or unsupported applicability facts to remain uncertain and requires explicit unknown with reason, evidence, and temporal scope.",
      ".ai/review-runs/T081-V4-SCHEMA-SLICE-3A/decision.md:108-112 and 360-368 repeat that unknown cannot be represented as a known or null value.",
      "backend/tests/fixtures/ad_v4_calibration/1998-17-11.proposal.json:334-352 stores condition-provenance-unknown.attributeValue as state known with value unknown_requires_compliance.",
      "backend/tests/test_ad_v4_calibration.py:264-266 affirmatively locks that placeholder-as-known representation into the existing oracle; the source fragment is explicitly anchored by '(4) If it cannot be determined'."
    ],
    "impact": "A purportedly lossless 3A projection would persist uncertainty as affirmative known data. Later condition evaluation or review could treat the sentinel as an ordinary value, violating the fail-closed domain contract while still passing byte-for-byte reconstruction.",
    "requiredClosure": "Correct the canonical calibration representation to an explicit unknown union with controlled reason, temporal scope, and evidence, and rerun the predecessor schema/canonical/evidence review needed for that fixture change. Add a negative gate rejecting semantic sentinels such as unknown_requires_compliance in known assertions when they encode uncertainty.",
    "closureEvidence": [
      "decision.md section 0 freezes validator-1 for immutable stored candidates and specifies validator-2 for new writes, with materializer refusal rather than mutation/invalidation of old sentinel-bearing candidates.",
      "decision.md Explicit uncertainty subsection replaces unknown_requires_compliance with an unknown union carrying reason not_observed, temporal scope, and evidence; new schema/service/calibration and legacy-verification regressions are explicit implementation gates.",
      "Independent closure review verified the corrected 1998 shape uses the already-existing V4 unknown union and retains ev-unknown-provenance plus at_applicability_evaluation. The legacy bytes remain validator-1 candidate-only and are refused for 3A rather than rewritten; implementation must still satisfy the separate validator-2 rollback/version finding DA-010."
    ]
  },
  {
    "id": "T081-V4-S3A-DA-004",
    "stage": "design",
    "reviewer": "/root/v4_schema_adversary",
    "severity": "blocker",
    "status": "closed",
    "invariant": "Applicability relationships remain queryable as manufacturer, model, series, and installed-equipment identities without parsing flattened display strings.",
    "summary": "Condition subjects and the search-hint fixture retain compound display strings rather than articulated identity relationships.",
    "evidence": [
      ".ai/AD_EXTRACTION_DOMAIN_CONTRACT.md:88-101 requires manufacturer, model, and series relationships to remain distinguishable; lines 346-355 require the search questions to be answerable without parsing flattened display strings.",
      "backend/app/schemas/ad_extraction_v4.schema.json:118-123 defines conditionSubject.modelOrSeries as one knownString rather than a typed designation set.",
      "backend/tests/fixtures/ad_v4_calibration/2002-13-04.proposal.json:135-153 stores 6314,6324,6364 in one value and lines 184-195 store five engine models in one comma-delimited value. backend/tests/test_ad_v4_calibration.py:251-253 must split the string to reason about membership.",
      "backend/tests/fixtures/ad_v4_calibration/2024-14-03.proposal.json:504-511 similarly combines GFC 500 and GSA 28 in one modelOrSeries value.",
      "backend/tests/fixtures/ad_v4_calibration/2002-13-04.proposal.json:485-503 uses manufacturer 'multiple' with models belonging to different manufacturers, so the hint cannot retain model-to-manufacturer relationships."
    ],
    "impact": "The relational projection is byte-lossless but not semantically articulated enough for safe future model/installed-equipment queries. A future reader would have to parse punctuation/conjunctions or infer manufacturer associations, exactly the behavior the domain contract prohibits.",
    "requiredClosure": "Define source-faithful compound text separately from a typed, explicitly unreviewed designation/member relationship with evidence and unknown normalization, or revise the canonical schema through a separately reviewed predecessor change. Represent multi-manufacturer hints as source-preserving groups/pairs or explicit unknown associations. Prove the 2002 and 2024 examples can be queried without string parsing and without treating hints as controlling.",
    "closureEvidence": [
      "decision.md section 0 defines a closed sourceDisplayText/designationGroup/member representation and manufacturerModelGroups with explicit association or source_ambiguous unknown; display punctuation is never parsed.",
      "decision.md records exact 2002 groups (3 magnetos, 5 engine families, atomic LTSIO, 7 manufacturer groups/27 models) and exact 2024 Garmin all_members GFC 500/GSA 28 representation while hints remain noncontrolling.",
      "Independent closure review found the repair is not canonical-version safe: decision.md section 0 adds designationGroup.members and manufacturerModelGroups/member arrays while retaining paprnav-ad-v4-c14n-1, but the closed Slice-2 decision states that adding any array requires a new reviewed canonicalization version.",
      "Independent source inspection of retained 2002 page 2 found the text '172A through 172H'. The remediation's Cessna count of 16 and overall 27 exact model members can be reached only by expanding that source series expression into eight model identities. That contradicts invariants 8/13 and the no-parsing/no-inferred-series rule; source-faithful representation would preserve the expression as an unevaluated series member rather than claim eight exact models.",
      "Targeted remediation assigns all new closed designation/search-group objects and member arrays to paprnav-ad-v4-validator-2 and paprnav-ad-v4-c14n-2, specifies every new array key/order rule, and pins byte-exact v2 proposal/binding/event/submission/relationship hash domains and envelope literals.",
      "The corrected retained-source oracle now has seven manufacturer groups, 19 exact model members, and one Cessna series_expression member with exact text '172A through 172H' and unknown/unsupported_expression; it explicitly forbids inferred exact 172A-H rows and tests absence of 172B and 172H.",
      "Bounded closure-2 remediation replaces the model-only hint table with typed search_hint_members: model rows require source_designation, series_expression rows require exact expression_text plus unevaluated/unsupported_expression and source_only/unknown identity provenance, with canonical ordinal and one inherited evidence-parent edge. Exact reconstruction uses the discriminator and never parses text.",
      "Independent closure-2 review verified the c14n-2 member one-of and relational discriminator are lossless: the retained phrase '172A through 172H' remains one series_expression occurrence, reconstruction emits its fixed canonical unknown/unsupported_expression branch from typed columns, and the 2002 oracle is exactly 19 model members plus 1 expression with no inferred 172B/172H rows. The 2024 Garmin pair remains an all_members group with no display-string parsing."
    ]
  },
  {
    "id": "T081-V4-S3A-DA-005",
    "stage": "design",
    "reviewer": "/root/v4_schema_adversary",
    "severity": "high",
    "status": "closed",
    "invariant": "Every source-to-normalized identity assertion has an honest, schema-representable origin and never implies candidate-supplied normalization where none exists.",
    "summary": "The normalization-origin enum has no valid state for source-only manufacturers or model/series values in conditions and search hints.",
    "evidence": [
      ".ai/review-runs/T081-V4-SCHEMA-SLICE-3A/decision.md:370-388 permits only candidate_payload or materializer_missing_model_mapping and says candidate_payload manufacturer mappings reconstruct canonical normalizedIdentity.",
      "backend/app/schemas/ad_extraction_v4.schema.json:118-123 and 226-237 provide only source knownString/identifier values for condition and hint manufacturers/models; they contain no normalizedIdentity payload.",
      ".ai/review-runs/T081-V4-SCHEMA-SLICE-3A/decision.md:459-463 and 503-515 nevertheless require identity mappings for those source-only fields. The 2002 fixture exercises both paths."
    ],
    "impact": "An implementation must mislabel a source-only manufacturer as payload-normalized, misuse a model-specific missing origin for a manufacturer, or omit a required mapping. Any choice corrupts provenance and makes normalized-token indexes/audit responses misleading.",
    "requiredClosure": "Add explicit closed origins for source-only/no-normalized-identity assertions across manufacturer, model, and series, define their mandatory unknown reason/temporal/evidence inheritance, and give exact mapping rows for the 2002 condition and search hint. Candidate_payload must remain legal only where normalizedIdentity actually exists in canonical bytes.",
    "closureEvidence": [
      "decision.md section 2.3 closes origin to candidate_payload, source_only, or no_normalized_identity; candidate_payload is legal only for an actual normalizedIdentity property.",
      "The same section requires unknown state, controlled reason, temporal scope, and single-parent evidence inheritance for the other origins and gives exact 2002 condition-member and hint-member examples.",
      "Independent closure review verified candidate_payload is restricted to an actual normalizedIdentity occurrence, while source_only and no_normalized_identity are forced to explicit unknown without token/value and inherit one same-projection evidence parent."
    ]
  },
  {
    "id": "T081-V4-S3A-DA-006",
    "stage": "design",
    "reviewer": "/root/v4_schema_adversary",
    "severity": "high",
    "status": "closed",
    "invariant": "A candidate supersession signal is proposal-bound, causal, idempotent, and cannot stale another candidate based on an unrelated relation.",
    "summary": "Supersession propagation neither binds the relation's successor to the materialized proposal nor records the dependency row as the stale event's causal identity.",
    "evidence": [
      ".ai/review-runs/T081-V4-SCHEMA-SLICE-3A/decision.md:291-304 lists causing Slice-2 relationship, lifecycle-event, or projection IDs but no causing change-dependency ID, while also requiring every system event to name a deterministic causal row.",
      ".ai/review-runs/T081-V4-SCHEMA-SLICE-3A/decision.md:306-318 stores the canonical supersession relation in a 3A change-dependency row, which is the missing causal row type.",
      ".ai/review-runs/T081-V4-SCHEMA-SLICE-3A/decision.md:664-669 permits exact predecessor resolution to stale existing projections but never requires successorAdNumber to equal the current proposal's evidence-bound directive AD number.",
      "backend/app/schemas/ad_extraction_v4.schema.json:240-243 permits any non-self predecessor/successor strings, and backend/app/services/ad_v4_candidates.py:605-613 checks only self/cycle structure, not binding to the proposal's own AD identity."
    ],
    "impact": "A valid candidate for AD C can carry an evidence-bound A-to-B relation and automatically append a stale signal to A's projection even though the proposal is not B. Multiple distinct dependency signals also lack an exact event-cause FK, weakening deduplication and audit reconstruction.",
    "requiredClosure": "Require a supersession dependency to prove that its successor equals the proposal's known canonical AD number before any cross-projection signal; otherwise retain it as unresolved without side effects. Add a same-projection causing_dependency_id composite FK and closed event discriminator/causal uniqueness definition. Test unrelated-successor, multiple/contradictory relations, retry, and concurrent signal insertion.",
    "closureEvidence": [
      "decision.md sections 2.1 and 6 require successor byte-equality with this proposal's known evidence-bound canonical AD number before lookup; mismatch/unknown/ambiguous relations remain unresolved and have no side effect.",
      "Target-local incoming dependency rows are the stale event's same-projection composite-FK cause, with closed event discriminators, causal uniqueness, deterministic hashes, sorted locks, retry and concurrency convergence tests.",
      "Independent closure review verified unrelated/unknown successors remain outgoing unresolved rows with no target lookup, incoming row, or event; the incoming dependency ID is now the target-local composite-FK event cause and has a dedicated causal uniqueness key."
    ]
  },
  {
    "id": "T081-V4-S3A-DA-007",
    "stage": "design",
    "reviewer": "/root/v4_schema_adversary",
    "severity": "high",
    "status": "closed",
    "invariant": "Every materialize and audit call is authorized through one exact active platform-admin membership, rather than through any membership attached to the user.",
    "summary": "The POST selects an acting membership, but the two audit GET contracts omit that selector while claiming the same exact-membership boundary.",
    "evidence": [
      ".ai/review-runs/T081-V4-SCHEMA-SLICE-3A/decision.md:142-146 requires an exact active membership for materialize or audit endpoints.",
      ".ai/review-runs/T081-V4-SCHEMA-SLICE-3A/decision.md:593-605 names Paprnav-Acting-Membership-Id only for POST and specifies no equivalent input for either GET.",
      ".ai/review-runs/T081-V4-SCHEMA-SLICE-3A/decision.md:744-746 says GET uses the same role boundary without defining exact-membership selection/locking.",
      "backend/app/api/routes/admin.py:19-26 and backend/app/api/routes/ads.py:330-395 show the current audit pattern authorizes when any loaded membership is active platform_admin, demonstrating that 'platform-admin-only' is not by itself the decision's stronger exact-membership contract."
    ],
    "impact": "Implementations can satisfy the endpoint prose using the existing any-membership helper while violating invariant 24. With multiple organizations/memberships, the audit authorization context is ambiguous and cannot be attributed or tested as specified.",
    "requiredClosure": "Specify whether audit GETs require Paprnav-Acting-Membership-Id (recommended) and define exact user/membership/status/role validation under one transaction. If the domain intentionally permits any active global membership, revise invariant 24 and the audit contract explicitly rather than relying on the current helper. Add GET-specific multi-membership, inactive-selected-membership, shop/admin, and revocation-race tests.",
    "closureEvidence": [
      "decision.md section 5 requires Paprnav-Acting-Membership-Id for POST and both GET audit endpoints and transactionally locks/validates the exact selected membership's user, active status, and platform_admin role before candidate reads.",
      "The contract denies selected inactive/shop/foreign memberships even when another valid admin membership exists and defines deterministic revocation-race and multi-membership tests.",
      "Independent closure review verified both GET contracts now require the membership header and lock/revalidate that exact membership; another active platform-admin membership cannot rescue an invalid selected row."
    ]
  },
  {
    "id": "T081-V4-S3A-DA-008",
    "stage": "design",
    "reviewer": "/root/v4_schema_adversary",
    "severity": "high",
    "status": "closed",
    "invariant": "Every Slice-2-valid condition has one deterministic relational representation, and Slice 3A does not invent an unversioned semantic restriction after canonical persistence.",
    "summary": "The proposed condition type/operator compatibility matrix is normative but never defined and is not present in the closed Slice-2 schema/validator.",
    "evidence": [
      ".ai/review-runs/T081-V4-SCHEMA-SLICE-3A/decision.md:448-457 requires a checked type/operator compatibility matrix but provides no allowed pairs or version.",
      "backend/app/schemas/ad_extraction_v4.schema.json:125-136 declares independent conditionType and operator enums without conditional pair constraints.",
      "backend/app/services/ad_v4_candidates.py:475-615 validates keys/references/cycles but does not validate condition type/operator pairs.",
      "The five packets cover only a small subset of possible enum combinations, so their 5/5 success cannot define the missing matrix."
    ],
    "impact": "Two conforming implementations can accept different Slice-2 candidates, or 3A can reject a previously valid immutable candidate based on an invented rule. Database CHECKs and reconstruction tests cannot be written against a unique contract.",
    "requiredClosure": "Either enumerate and version every permitted type/operator/subject-shape combination and apply that rule at the Slice-2 canonical boundary through a separately reviewed change, or declare all currently schema-valid pairs representable but unevaluated in 3A and remove the undefined compatibility claim. Add one positive and one negative vector for every normative pair/shape rule.",
    "closureEvidence": [
      "decision.md invariants 14/16 and section 2.5 remove the undefined compatibility matrix and require every Slice-2-schema-valid enum pair to be represented with evaluation_state=unevaluated and evaluator_contract=none.",
      "The test strategy requires 90 represented/reconstructed out of 90 current type/operator pairs plus closed-shape/enum negatives; evaluation and matching remain prohibited pending a separately reviewed future contract.",
      "Independent closure review confirmed no semantic pair matrix is invented: every current enum cross-product is stored with evaluation_state unevaluated/evaluator_contract none, while schema shape and unknown enum validation remain at the canonical boundary."
    ]
  },
  {
    "id": "T081-V4-S3A-DA-009",
    "stage": "design",
    "reviewer": "/root/v4_schema_adversary",
    "severity": "high",
    "status": "closed",
    "invariant": "Any index described as future aircraft-ID lookup support has a safe, reviewed identity join path and is not permanently empty under the only accepted canonical schema.",
    "summary": "The model-token indexes are knowingly empty and have no future reviewed-identity bridge, so they do not support the claimed aircraft-ID lookup shape.",
    "evidence": [
      ".ai/review-runs/T081-V4-SCHEMA-SLICE-3A/decision.md:381-393 requires all current model mappings to be unknown and requires a later reviewed mapping relation rather than updating these rows.",
      ".ai/review-runs/T081-V4-SCHEMA-SLICE-3A/decision.md:563-585 creates model-token indexes and admits they are empty for current listed models.",
      ".ai/review-runs/T081-V4-SCHEMA/codex-schema-proposal.md:830-859 defines the future hot path as a reviewed canonical model-identity ID join, not a source-string or unreviewed hash match.",
      "No 3A table has an aircraft/canonical-registry FK, and the design explicitly defers the reviewed relation that would own the usable index."
    ],
    "impact": "The migration adds write/DDL cost and a misleading appearance of lookup readiness without a safe join path. A future matching slice must create different reviewed-relation indexes anyway, or risk joining aircraft identities to unreviewed candidate tokens.",
    "requiredClosure": "Remove the vacuous token indexes and explicitly defer reviewed lookup indexes to the identity/matching slice, or define a stable non-authoritative designation-node bridge that the later reviewed identity relation will reference and state that the usable index belongs there. Do not claim current candidate-token indexes support aircraft-ID matching, and retain tests proving no reader uses them.",
    "closureEvidence": [
      "decision.md invariant 26 and section 4 remove source-spelling, normalized-token, aircraft-ID, make/model, search-hint, and product-role hot-path indexes and make no readiness claim.",
      "Only integrity, reconstruction, audit, correction-completeness, dependency, and stale-fold indexes remain; the future reviewed identity/matching slice owns its bridge and usable indexes, with absence and released-reader isolation tests.",
      "Independent closure review verified the decision removed the normalized/source/aircraft/matching index list and now requires PostgreSQL catalog negatives proving those indexes are absent; no readiness claim remains."
    ]
  },
  {
    "id": "T081-V4-S3A-DA-010",
    "stage": "design",
    "reviewer": "/root/v4_schema_adversary",
    "severity": "blocker",
    "status": "closed",
    "invariant": "Validator-2/canonicalization evolution and physical or application rollback preserve the meaning and readability of every immutable Slice-2 candidate without leaving newer rows under an older schema contract.",
    "summary": "The validator-2 proposal changes the existing Slice-2 storage boundary, but the downgrade checks only Slice-3A tables and can strand validator-2 candidates at revision 0026, whose database writer and application know only validator-1.",
    "evidence": [
      ".ai/review-runs/T081-V4-SCHEMA-SLICE-3A/decision.md:227-267 makes all new candidate submissions use validator-2 and retains those immutable rows in the existing ad_v4_candidate_proposals table.",
      "backend/app/db/migrations/versions/20260901_0026_add_ad_v4_candidates.py:155-177 hardcodes paprnav-ad-v4-validator-1 in the proposal INSERT trigger; backend/app/services/ad_v4_candidates.py:33 likewise has only validator-1.",
      ".ai/review-runs/T081-V4-SCHEMA-SLICE-3A/decision.md:1097-1112 says application rollback disables only 3A routes and physical downgrade checks only new 3A tables before returning to 0026. A validator-2 proposal can exist without a 3A projection, so those checks can pass while incompatible Slice-2 rows remain.",
      "The closed Slice-2 decision's canonicalization section states that adding an array requires a new reviewed canonicalization version. The revised design adds multiple typed group/member arrays but keeps paprnav-ad-v4-c14n-1, compounding the rollback/hash-dispatch ambiguity."
    ],
    "impact": "An empty 3A schema could downgrade successfully while immutable validator-2/canonicalization rows remain. Revision 0026 and an old application cannot create, validate, or reliably attest those rows under their recorded contract; rollback therefore ceases to be truthful and mixed-version deployments can disagree about proposal identity.",
    "requiredClosure": "Assign the added arrays a new canonicalization version and domain, define validator/canonicalizer dispatch for every stored proposal, and include validator/canonicalization version in all repeated projection envelopes. Define mixed-version deployment order. Physical downgrade must lock the Slice-2 proposal table and refuse while any validator-2/new-canonicalization proposal or dependent submission/event exists (or retain a backward verifier in an explicitly non-downgraded compatibility revision). Application rollback must preserve read verification for both versions. Add empty-3A/nonempty-validator2 downgrade refusal, old/new read parity, same-content reuse, and re-upgrade tests.",
    "closureEvidence": [
      "decision.md Validator-2 canonicalization and hash domains defines validator-2/c14n-2, byte-exact NUL-terminated domains, fixed v2 envelopes, version-scoped proposal/audit identity, and no cross-version content reuse.",
      "decision.md Migration, compatibility, correction, and rollback requires migration 0027 to backfill explicit v1 version metadata on Slice-2 audit children without changing bytes/hashes, constrain all child rows to parent versions, deploy dual readers before v2 writers/3A, and prohibit pre-v2 applications while v2 rows exist.",
      "The physical downgrade contract locks all 3A and Slice-2 proposal/submission/relationship/event/binding tables and refuses any v2 proposal or dependent audit row even with empty 3A; tests cover v1/v2 parity/distinct identity/retry, empty-3A nonempty-v2 refusal, races, immutable v2 rows, and v1-only downgrade/re-upgrade.",
      "Bounded closure-2 remediation establishes one proposal-first global order: downgrade takes Slice-2 proposal ACCESS EXCLUSIVE before Slice-2 children and all 3A tables, while each materializer locks its proposal before any 3A row. The decision enumerates candidate-create/materialize/downgrade outcomes and removes the proposal/3A lock inversion.",
      "Independent closure-2 review verified the global serialization boundary: candidate creation and materialization touch/lock the Slice-2 proposal before any 3A row, downgrade takes ACCESS EXCLUSIVE on that parent table before Slice-2 children and 3A tables, and the stated commit-first/wait-first outcomes cannot form the former parent/child lock cycle. Empty-3A v2 rows still refuse downgrade; v1-only downgrade/re-upgrade and dual-reader application rollback preserve immutable bytes and hashes."
    ]
  },
  {
    "id": "T081-V4-SCHEMA-SLICE-3A-CC-001",
    "stage": "external-critic",
    "reviewer": "claude-external-critic-20260906T235706Z",
    "severity": "medium",
    "status": "closed",
    "invariant": "Every other safety/correctness invariant in this design is enforced by the database or application transaction rather than by operator discipline (e.g., invariant 2's 'creation-time validity is not trusted'); the staged validator-2/3A rollout should meet the same bar.",
    "summary": "The mandatory deployment order (apply 0027 -> dual-reader app -> enable v2 writer -> enable 3A routes) has no concrete code-level gate. The codebase has no existing feature-flag mechanism, so nothing prevents a rolling deploy from serving v2 writes or 3A routes from an instance before all instances are dual-readers.",
    "evidence": [
      "review-packet.md:1262-1269 'Deployment order is mandatory: 1. apply 0027 ... 2. deploy the compatibility application ... 3. enable the v2 writer after all serving instances are dual readers; and 4. enable the 3A materializer/routes only after v2 writes are proven.'",
      "grep for feature_flag/FEATURE_FLAG/ENABLE_*/settings.FEATURE across backend/app returned zero matches, confirming there is no existing toggle mechanism this design could rely on.",
      "Every other invariant in the same document (e.g., invariant 2, invariant 24) is phrased as a transaction-enforced or trigger-enforced guarantee, not a manual rollout instruction."
    ],
    "impact": "A rolling/blue-green deploy that briefly runs mixed old/new application instances (a routine production pattern) could serve v2 candidate writes or 3A materialization from a not-yet-fully-rolled-out fleet, or could enable 3A routes before the v2 writer has been proven safe in production, silently violating the design's own stated sequencing without any error, log, or DB rejection.",
    "requiredClosure": "Define a concrete, code-level gate (e.g., an environment/config flag read at router-registration or write-path time) that makes 'v2 writer enabled' and '3A routes enabled' explicit, independently togglable states rather than an implicit consequence of which code version is deployed. Add a test or startup check proving the 3A routes/v2 writer cannot activate merely because migration 0027 has run.",
    "closureEvidence": [
      "decision.md section 5.1 defines independent default-off PAPRNAV_AD_V4_VALIDATOR2_WRITES_ENABLED and PAPRNAV_AD_V4_SLICE3A_ROUTES_ENABLED settings, fixed compiled capabilities, and migration-0027 database capability checks at startup and again inside write transactions.",
      "The deployment contract requires the dual-reader compatibility release with both flags false before any config enablement, states that the gate does not prove fleet-wide rollout, and adds default-off, independent-toggle, schema-mismatch, transactional recheck, and rollback tests.",
      "Targeted correction requires the 3A materialization POST to observe both application flags and both database gates validator2_write_enabled/materializer3a_enabled, while audit GET requires only the 3A/read gate and cannot create a missing projection.",
      "The four-combination matrix now proves that v2-write off plus 3A on rejects materialization of a preexisting v2 candidate with validator2_write_gate_disabled and zero request/projection/dependency/correction/event rows; proposal-before-gate locking defines both outcomes for concurrent disable versus materialization.",
      "Independent external-critic closure review verified the gates are concrete and independently controlled rather than operator prose: both application flags and both deployment-role-controlled database gates default false; validator-2 POST requires its paired flag/gate; 3A POST requires both pairs; audit GET requires only the 3A/read pair and cannot create missing rows. Startup plus in-transaction capability checks, the exact four-state preexisting-v2 matrix, concurrent disable barriers, mixed-release false defaults, and rollback/drain order are all mandatory implementation tests."
    ]
  },
  {
    "id": "T081-V4-SCHEMA-SLICE-3A-CC-002",
    "stage": "external-critic",
    "reviewer": "claude-external-critic-20260906T235706Z",
    "severity": "medium",
    "status": "closed",
    "invariant": "The design's stated in-scope/out-of-scope boundary (Objective section) and its 'Expected file scope' section should name every namespace and table Slice 3A is authorized to touch, so an implementer or later reviewer can verify boundary compliance without re-deriving it from a 1,500-line design body.",
    "summary": "Section 2.1.1 requires Slice 3A to create a shared, proposal-scoped correction foundation that stores canonical `authoritativeCorrections` content and verified `officialDocuments` identity hashes -- two top-level V4 namespaces distinct from the four-field applicability subtree {productScopes, conditionDefinitions, applicabilityRules, applicabilitySearchHints}. Neither namespace is mentioned in the Objective's in/out-of-scope bullet list, nor explicitly named in the 'Expected file scope' section, even though the mandatory 2008-26-10 calibration assertion depends on it.",
    "evidence": [
      "review-packet.md:28-63 (Objective) lists what's out of scope for 3A/deferred to 3B but never mentions `authoritativeCorrections` or `officialDocuments`.",
      "review-packet.md:581-655 (section 2.1.1) defines `ad_v4_candidate_corrections`, `_correction_refs`, `_correction_semantic_bindings`, `_correction_evidence_links` storing `officialDocuments reference keys`, their `verified document-identity hashes`, and namespace refs spanning `requirements|recurrenceGroups|amocAuthorityProvisions` (3B-owned) in addition to 3A-owned namespaces.",
      "backend/app/schemas/ad_extraction_v4.schema.json $defs.proposal.properties includes `authoritativeCorrections` and `officialDocuments` as independent top-level arrays, confirming these are namespaces outside the four-field subtree definition in invariant 3.",
      "review-packet.md:1458-1489 ('Expected file scope') mentions only 'the additive 3A tables' generically and never names the correction-foundation tables or namespaces, while the mandatory test for 2008-26-10 (review-packet.md:1369-1372) requires 'exact shared correction-2010 foundation with two ordered refs, two evidence links once, one 3A scope binding, and one explicit future-3B requirement ref'."
    ],
    "impact": "An implementer following the Objective/Expected-file-scope sections literally could reasonably treat the correction-foundation tables as unauthorized scope creep and omit them, causing the mandatory 2008-26-10 reconstruction test (and the whole DA-002 closure) to fail; conversely, a later reviewer auditing 'did 3A only touch what it said it would' has no single authoritative scope list to check against, since the two scope-defining sections disagree with the detailed design.",
    "requiredClosure": "Update the Objective's out-of-scope list and the 'Expected file scope' section to explicitly name the correction-foundation tables and the `authoritativeCorrections`/`officialDocuments` namespaces they read/verify, so the document's own scope statement is internally consistent with section 2.1.1 and the mandatory calibration test.",
    "closureEvidence": [
      "decision.md Objective now explicitly authorizes the shared correction foundation, all four correction tables, and read/verification of authoritativeCorrections plus referenced officialDocuments identity/evidence while deferring 3B obligation/document semantics.",
      "decision.md Expected file scope repeats the exact tables/namespaces and implementation boundary, eliminating the scope conflict with section 2.1.1 and the 2008 calibration gate.",
      "Independent external-critic closure review verified both scope-defining sections now name the four shared correction-foundation tables and authorize only canonical authoritativeCorrections plus referenced officialDocuments identity/evidence fields. Complete ordered future-3B references are retained, but requirement, recurrence, AMOC, incorporated-document, and service-bulletin semantics remain explicitly deferred."
    ]
  },
  {
    "id": "T081-V4-SCHEMA-SLICE-3A-CC-003",
    "stage": "external-critic",
    "reviewer": "claude-external-critic-20260906T235706Z",
    "severity": "low",
    "status": "closed",
    "invariant": "'Write paths and administrative paths' asserts no new operational writer (job/CLI/seed/etc.) is added beyond the single platform-admin POST service.",
    "summary": "The stale-fold section introduces 'a background repair function [that] may append missing deterministic events after a crash,' which reads as a new asynchronous/scheduled process, apparently in tension with the explicit claim elsewhere that no provider job, CLI, seed, or generic writer is added.",
    "evidence": [
      "review-packet.md:1081-1085 'A background repair function may append missing deterministic events after a crash; it uses the same locks and event identity and requires no human review.'",
      "review-packet.md:1205-1213 ('Write paths and administrative paths') states 'No provider job, CLI, seed, V3 translator, calibration loader, frontend form, or generic ORM CRUD writer is added,' and that 'Its internal deterministic stale-event helper is part of the same service/repository boundary,' without clarifying whether the crash-repair helper is invoked synchronously (e.g., opportunistically on the next POST/GET) or via a new scheduled/background worker process."
    ],
    "impact": "If implementation interprets 'background repair function' as a new cron/worker process, that is new operational surface (deployment unit, scheduling, monitoring) not accounted for anywhere else in the design's operational sections, and could be missed by an implementation reviewer who only checks for 'no new job' against the explicit write-paths sentence.",
    "requiredClosure": "Clarify in the design that the repair helper is invoked inline/opportunistically from existing request paths (not a new scheduled process), or, if a real background worker is intended, add it explicitly to the write-paths/operational sections and its own authorization/idempotency contract.",
    "closureEvidence": [
      "decision.md section 6 and Write paths now state the repair helper runs inline only inside an authorized materialization POST transaction; audit GET invokes detection-only mode and remains side-effect-free.",
      "The design explicitly forbids cron, queue consumer, worker, scheduler, CLI, repair endpoint, startup sweep, or any new operational writer.",
      "Independent external-critic closure review verified repair is inline only in the already-authorized materialization POST transaction and reuses its locks, capability gates, deterministic cause identity, and idempotent event key. GET executes detection-only logic and remains side-effect-free; no asynchronous or alternate writer surface is authorized."
    ]
  },
  {
    "id": "T081-V4-S3A-IA-001",
    "stage": "implementation",
    "reviewer": "/root/v4_s3a_impl_adversary",
    "severity": "blocker",
    "status": "open",
    "invariant": "The implementation uses the approved typed relational design with database-enforced ownership, closed shapes, cardinality, order, references, arity, acyclicity, evidence, and unevaluated semantics.",
    "summary": "Migration 0027 substitutes generic semantic-node and JSON-pointer datum tables for the approved typed applicability tables and constraints.",
    "evidence": ["decision.md:663-924 specifies typed tables and constraints", "backend/app/db/migrations/versions/20260907_0027_add_ad_v4_applicability.py:93-208 creates generic semantic-node and datum tables", "backend/app/services/ad_v4_applicability.py:_flatten serializes arbitrary JSON shapes"],
    "impact": "Malformed or executable-looking semantic graphs can be stored without the reviewed database guarantees, and the implementation differs materially from the approved design.",
    "requiredClosure": "Implement the approved typed schema and PostgreSQL negative tests, or return to design review and prove an equivalent generic design."
  },
  {
    "id": "T081-V4-S3A-IA-002",
    "stage": "implementation",
    "reviewer": "/root/v4_s3a_impl_adversary",
    "severity": "blocker",
    "status": "closed",
    "invariant": "A projection root and its complete exact relational children are validated together at commit.",
    "summary": "PostgreSQL permits a valid-looking projection root with zero or partial relational children.",
    "evidence": ["Projection counts are ordinary root columns", "paprnav_v4_validate_app_projection is only a BEFORE INSERT root-envelope trigger", "No deferred child-graph constraint or decisive direct-SQL partial-graph test exists"],
    "impact": "A direct writer can commit incomplete immutable derived state that only later application reads may detect.",
    "requiredClosure": "Add deferred full-graph reconstruction/count/hash/evidence validation and direct-SQL empty, missing, extra, reordered, changed-value, and cross-reference tests.",
    "closureEvidence": [
      "Migration 0027 now installs recursive JSON-node expansion plus a deferred constraint trigger on every projection/child/correction table; it compares the exact relational datum graph, counts, semantic/evidence hash sets, materialized root event, and candidate subtree at commit.",
      "PostgreSQL test 04 copies a byte-valid legitimate root, rolls back its children, inserts only the root, and proves deferred commit rejection; test 05 proves an extra direct-SQL child is rejected when constraints are forced immediate.",
      "The expanded disposable PostgreSQL matrix passed 9 out of 9 in t081_blockers_l, which was dropped; paprnav_db was not targeted.",
      "Independent targeted closure review adversarial-implementation-ia002-ia005-closure.md verified all residual semantic ownership/hash and listed-designation counterexamples and returned IA-002 PASS."
    ]
  },
  {
    "id": "T081-V4-S3A-IA-003",
    "stage": "implementation",
    "reviewer": "/root/v4_s3a_impl_adversary",
    "severity": "blocker",
    "status": "open",
    "invariant": "Supersession stale state is proposal-bound, uniquely resolved, evidence-backed, and names the exact same-projection dependency cause.",
    "summary": "Stale folding accepts the first predecessor relationship without successor-AD equality or unique resolution and emits events with no dependency cause.",
    "evidence": ["backend/app/services/ad_v4_applicability.py:613 treats a matching predecessor relationship as stale", "backend/app/services/ad_v4_applicability.py:661 stores causing_dependency_id=None", "Materialized dependencies remain unresolved"],
    "impact": "An unrelated candidate relationship can stale a projection and leave an incomplete audit chain.",
    "requiredClosure": "Resolve dependencies under successor canonical AD equality and unique predecessor rules, require the exact dependency FK on stale events, and test positive and negative cases."
  },
  {
    "id": "T081-V4-S3A-IA-004",
    "stage": "implementation",
    "reviewer": "/root/v4_s3a_impl_adversary",
    "severity": "high",
    "status": "closed",
    "invariant": "Audit GET/list/reconstruction paths are detection-only and never write repair events.",
    "summary": "Detail and list GET invoke mutating stale repair and commit events.",
    "evidence": ["backend/app/services/ad_v4_applicability.py:596 invokes repair from projection_state", "backend/app/api/routes/ads.py:493 and :544 commit after GET serialization"],
    "impact": "Viewing audit state becomes an alternate writer with unexpected locks and audit mutations.",
    "requiredClosure": "Make GETs side-effect-free, keep repair inside authorized materialization POST, and test unchanged table/event counts for every GET.",
    "closureEvidence": [
      "backend/app/services/ad_v4_applicability.py separates non-mutating projection_state detection from repair and calls repair only within materialize_applicability after authorization and database gates, on both normal and idempotent POST paths.",
      "backend/app/api/routes/ads.py detail and list GET paths no longer commit; reconstruction was already read-only.",
      "backend/tests/test_ad_v4_applicability.py snapshots the projection-event count across detail, reconstruction, and list GET; the focused suite passed 40 out of 40.",
      "Independent targeted closure review adversarial-implementation-ia004-closure.md by /root/v4_s3a_impl_adversary found no alternate repair caller and passed IA-004 with no residual finding."
    ]
  },
  {
    "id": "T081-V4-S3A-IA-005",
    "stage": "implementation",
    "reviewer": "/root/v4_s3a_impl_adversary",
    "severity": "high",
    "status": "closed",
    "invariant": "The shared correction foundation exactly reconstructs and verifies canonical corrections, official-document identities, ordered refs, and evidence at commit and read.",
    "summary": "Correction rows are inserted without exact reconstruction, deferred completeness/identity checks, or verified-read validation.",
    "evidence": ["_materialize_corrections has no corresponding exact reconstruction verifier", "Migration 0027 does not enforce expected child counts or official-document identity", "Calibration tests check selected counts/values rather than an independent correction round trip"],
    "impact": "A projection can report verified while its cross-slice correction foundation is incomplete or disconnected.",
    "requiredClosure": "Implement correction reconstruction and fail-closed verification, deferred completeness/identity enforcement, and direct-SQL negatives plus exact 2008 round trip.",
    "closureEvidence": [
      "Application verified reads now reconstruct each correction from ordered roots/refs/evidence and verify canonical equality, document identities, generation, owners, 3A bindings, and candidate evidence bindings.",
      "Migration 0027 deferred completeness validates exact correction count/order/content/hash, official-document identity hashes, exact refs/evidence, generation, and owner-slice binding cardinality; correction rows cannot commit without a projection.",
      "The 2008 real-evidence calibration round trip passes and deliberately removing one correction evidence link fails closed; the disposable PostgreSQL matrix passed 9 out of 9.",
      "Independent targeted closure review adversarial-implementation-ia002-ia005-closure.md verified binding targets, document and row hashes, zero-based contiguous ordinals, append ordering, and SQL-null behavior and returned IA-005 PASS."
    ]
  }
]

```

## Hash-bound review inputs

### `.ai/review-runs/T081-V4-SCHEMA-SLICE-3A/decision.md`

size=91684; sha256=50effad6a01fdb75a1d4594b170bed35f3c977464f4f83a81919793d553df466

```text
# Decision packet: T081-V4-SCHEMA-SLICE-3A

Status: design reviewed; external-critic remediations pending independent verification

Builder: `/root/v4_schema_builder`

Governing contract: `.ai/AD_EXTRACTION_DOMAIN_CONTRACT.md` version 1.1

Predecessor: closed `T081-V4-SCHEMA-SLICE-2` candidate-validation and
immutable-proposal boundary

## Objective

After design approval, implement one additive, candidate-only relational
projection of the applicability subset of an immutable V4 proposal. The slice
materializes and reconstructs only:

- `productScopes` and their product roles, source manufacturer values,
  manufacturer normalization assertions, model lists or series expressions,
  and serial/part-number scopes;
- `conditionDefinitions`, their typed subjects and explicit three-valued
  values;
- the nested three-valued expression trees and `applicabilityRules` that refer
  to those scopes and conditions; and
- non-controlling `applicabilitySearchHints`.

Slice 3A also creates the shared, proposal-scoped correction foundation named
in section 2.1.1. It reads and verifies the canonical
`authoritativeCorrections` namespace and the referenced `officialDocuments`
identity/evidence fields, materializes
`ad_v4_candidate_corrections`, `ad_v4_candidate_correction_refs`,
`ad_v4_candidate_correction_semantic_bindings`, and
`ad_v4_candidate_correction_evidence_links`, and reconstructs each correction
object separately from the four-field applicability subtree. This is explicit
3A scope needed to preserve one cross-slice correction identity; it does not
materialize obligation or document semantics.

The projection is bound to one Slice-2 candidate proposal, its canonical hash,
its evidence-binding hash, and a fixed materializer version. It remains
unreviewed and `candidate_only`. Relational reconstruction must reproduce the
canonical applicability subtree exactly and must never copy retained source
text.

This is deliberately the first half of the originally proposed normalized
schema slice. The following are not part of Slice 3A:

- requirements, actions, timing, recurrence groups, branches, terminating
  effects, incorporated-document/service-bulletin content, AMOC provisions,
  or aircraft-specific AMOC use (Slice 3B). The shared correction foundation
  records complete ordered references into these deferred namespaces but does
  not interpret or materialize their 3B semantics;
- human approval, signoff, rejection, publication, current selection, or a
  reviewer GUI;
- released catalog, aircraft matching, coverage, compliance, or due-state
  readers;
- V3 mutation, translation, fallback, or compatibility-row materialization;
- aircraft/component canonical identity migration or aircraft configuration;
  and
- fuzzy aliases, inferred series membership, or an authoritative manufacturer
  or model registry.

## User-visible outcome

There is no maintenance-shop or customer-visible behavior change. An active
platform administrator may explicitly request deterministic materialization of
an existing V4 candidate and inspect its verified projection for audit. The
response identifies the candidate proposal, projection/materializer version,
applicability-subtree hash, counts, evidence-binding hash, and a computed
candidate projection state. It never calls the released AD catalog or claims
that any aircraft is or is not affected.

The endpoint and database use the label `candidate_only`; they do not use
`approved`, `current`, `released`, `actionable`, `applicable`, or `not
applicable` as a projection-level decision. A canonical field may itself carry
the source-supported three-valued state `not_applicable`; that field state does
not turn the candidate projection into an approved conclusion.

## Safety and correctness invariants

The following are falsifiable design and implementation gates.

1. A projection references exactly one immutable
   `ad_v4_candidate_proposals` row and repeats its directive ID, schema version,
   validator version, canonicalization version, canonical hash, and
   evidence-binding hash under composite FK/trigger enforcement.
2. Only a proposal with database gate `candidate_only`, valid canonical bytes,
   valid Slice-2 envelopes, and a currently eligible exact Slice-1 evidence
   lifecycle may be materialized. Eligibility is rechecked inside the write
   transaction; creation-time validity is not trusted.
3. The applicability materialized source is the four-field canonical subtree
   `{productScopes, conditionDefinitions, applicabilityRules,
   applicabilitySearchHints}` extracted from verified proposal bytes. The only
   additional top-level namespaces read are the explicitly scoped
   `authoritativeCorrections` and referenced `officialDocuments` fields used by
   the shared correction foundation. No other namespace is silently projected.
4. Reconstructing that subtree solely from relational rows, including every
   property-presence choice and array order, then applying the Slice-2
   canonicalizer produces byte-identical subtree bytes and the stored subtree
   hash.
5. PostgreSQL deferred checks compare the reconstructed relational JSONB to the
   exact four-field subtree in the parent proposal's verified JSONB mirror.
   Direct SQL cannot commit a partial, cross-candidate, or differently valued
   projection whose root hashes appear valid.
6. Every semantic node belongs to the same projection and proposal. Every
   typed child, expression edge/reference, rule exclusion, identity mapping,
   dependency, and evidence link uses a composite same-projection FK; a bare ID
   is never the only relationship guard.
7. Every evidence-bearing canonical object has exactly the evidence-key set in
   the candidate. Evidence links resolve to Slice-2
   `ad_v4_candidate_evidence_bindings` for the same proposal. They store IDs and
   hashes only; no fragment text, page text, PDF bytes, or repeated citation
   prose exists in any Slice-3A table.
8. Source manufacturer values and model/series designations are preserved
   byte-for-byte as validated NFC strings. They are never case-folded, trimmed,
   punctuation-folded, concatenated, or replaced by a normalized identity.
9. Candidate normalization is a separate assertion with explicit origin,
   version, review state, and evidence. A known normalized manufacturer value
   comes only from the canonical proposal. Current V4 supplies no per-model
   normalized value, so model normalization is explicitly `unknown` with
   reason `not_extracted`; it is never inferred from spelling similarity. The
   model mapping is one-to-one with its exact designation-value occurrence,
   inherits source support from one parent designation-scope node, and does not
   repeat an evidence link for every listed model.
10. Every normalization row is `unreviewed_candidate`. No aircraft row or
    released directive may reference it, and no matching/current-selection
    reader exists in this slice.
11. SQL `NULL` means only that a property is absent or that a column is unused
    by the row's checked discriminator. Regulatory uncertainty is always an
    explicit `unknown` state with controlled reason, temporal scope, and
    evidence; `not_applicable` has the same explicit support.
12. A source property that is absent is recorded as `property_absent`, distinct
    from an explicit canonical `unknown`. Reconstruction omits an absent
    property and emits an explicit unknown object for an unknown property.
13. Listed models, serial/part values, and identifier ranges remain exact
    source values. A series expression is preserved as source text and has
    evaluation state `unknown/unsupported_expression`; Slice 3A executes no
    regex, prefix, series, serial, or part-number comparator.
14. Conditions preserve their exact type, operator, optional comparator
    version, temporal-basis discriminator, subject property presence, compound
    source display text, typed designation groups/members, and three-valued
    subject assertions. Every condition type/operator pair accepted by the
    Slice-2 schema is representable but explicitly `unevaluated`; 3A invents no
    unreviewed compatibility matrix. No display JSON or opaque predicate JSON
    is relational authority.
15. Expression rows implement only `scope_ref`, `predicate_ref`, `rule_ref`,
    `not`, `all`, and `any` for applicability rules. Requirement-state refs are
    rejected at this boundary. Arity, sequence, same-projection reference
    types, rule cycles, and exclusion cycles are enforced again at materialize
    and reconstruct time.
16. Expression evaluation is out of scope. Stored expression nodes declare the
    fixed result domain `kleene_true_false_unknown_v1` and evaluator version,
    but no row records a truth result for an aircraft.
17. Search hints remain `controlling = false` and `exhaustive = false`, have
    no FK route from an expression, and cannot establish or suppress a match.
18. One source condition, rule, and evidence binding shared by 182 models
    produces one condition row, one rule row, and no per-model evidence-link
    copies. All links reuse Slice-2 binding IDs rather than copying source
    identity or text. The 2024-14-03 fixture is the mandatory bloat regression.
19. Materialization is deterministic and idempotent for
    `(proposal_id, materializer_version)`. Identical retries return the same
    root; different request keys may record separate audit requests without
    duplicating semantic content.
20. Concurrent materialization of the same proposal converges on one complete
    root and one deterministic row set. No uniqueness race returns 500, leaks a
    partial graph, or produces different node identities.
21. Correction or replacement never updates a projection. A later candidate
    relationship appends a hash-chained stale event for the predecessor
    projection. Evidence lifecycle change is detected live and may append the
    same derived stale fact; it never rewrites prior rows.
22. A candidate supersession relation is stored only as an evidence-bound,
    untrusted dependency signal. It can cause a stale event only when its
    successor AD number equals this proposal's known, evidence-bound canonical
    AD number and its predecessor resolves uniquely. Otherwise it remains
    unresolved with no side effect. Every stale event names that exact
    same-projection dependency row. It never changes released AD status or
    proves legal supersession.
23. Projection reads fold the immutable event chain and recheck parent/evidence
    integrity. Missing, ambiguous, contradictory, or invalidated dependencies
    fail closed to `candidate_stale` or `dependency_unresolved`; no stale root
    is presented as verified/current.
24. POST and both audit GET endpoints require
    `Paprnav-Acting-Membership-Id`. Only the exact selected active membership
    belonging to the caller and carrying `platform_admin` may authorize the
    transaction. POST snapshots membership, organization, role, status,
    action, policy version, and claims hash. GET locks and revalidates the exact
    selected membership for that transaction. Another valid membership cannot
    rescue an inactive, shop, foreign, or revoked selected membership.
25. V1/V2/V3 rows and all released/search/matching/compliance/due readers are
    behaviorally unchanged. Repository search and route tests prove that no
    existing reader imports or queries a Slice-3A table.
26. Slice 3A creates only integrity, reconstruction, audit, and stale-fold
    indexes used by its own bounded service. It creates no normalized-token,
    aircraft-identity, or matching hot-path index and makes no readiness claim.
    A reviewed identity bridge and its indexes belong to the later matching
    slice.
27. All Slice-3A rows are append-only. PostgreSQL rejects UPDATE and DELETE,
    including attempted normalization or stale-state edits.
28. Upgrade performs only the locked Slice-2 v1 version-metadata backfill and
    no semantic/canonical/evidence backfill. Downgrade locks the Slice-2
    proposal boundary first, then child and 3A tables, refuses while any 3A or
    v2 row exists, and succeeds/re-upgrades only for v1-only/empty-3A state.
    Concurrent insert/drop cannot deadlock or lose rows.
29. Validator-2 writes and Slice-3A routes have independent, default-off
    application flags and database gates. A 3A materialization requires both
    write and 3A gates; audit requires only the 3A/read gate. Every request also
    proves the compiled application version and migration-0027 capability at
    startup and inside its transaction. Migration presence alone never enables
    either surface, and a gate is not evidence that a fleet-wide compatibility
    rollout completed.

## Current behavior and authoritative representation

Slice 1 retains immutable source documents, page renditions, text versions,
single-page exact evidence fragments, and fragment lifecycle chains. Slice 2
validates raw V4 bytes, canonicalizes the full proposal, snapshots exact
admitted evidence bindings, and stores immutable candidate content,
submissions, relationships, and creation events. Its database gate is always
`candidate_only`.

The Slice-2 canonical bytes remain candidate authority. Slice 3A is a derived,
lossless relational projection used only for audit and later reviewed
development. The projection never becomes official evidence or reviewed
structured AD truth merely because round-trip equality succeeds.

Existing V3 `applicability_targets`, `ad_target_applicability`, compliance
requirements, released catalog rows, and their copied JSON/citations are not a
source for Slice 3A and are not populated by it. They remain isolated legacy
representations.

The five executable Slice-2 calibration proposals currently contain:

| AD | scopes | listed models | conditions | rules | hints | applicability-relevant change signal |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| 1998-17-11 | 2 | 81 | 2 | 1 | 0 | none |
| 2002-13-04 | 1 | 6 | 4 | 1 | 1 | none |
| 2008-26-10 | 1 | 182 | 4 | 1 | 0 | authoritative correction |
| 2011-10-09 | 1 | 224 | 0 | 1 | 0 | supersession relation |
| 2024-14-03 | 5 | 182 | 1 | 1 | 0 | none |

Those are calibration expectations, not facts to hard-code in the
materializer.

## Proposed design

### 0. Required backward-compatible Slice-2 schema corrections

Slice 3A cannot faithfully materialize known predecessor defects. Its future
implementation therefore includes a narrowly versioned correction to the
Slice-2 canonical boundary before any 3A row is written.

The current schema, validator, and canonicalization artifacts are frozen as
`paprnav-ad-v4-validator-1` and `paprnav-ad-v4-c14n-1` for verification of
already stored candidates. A new closed schema/semantic profile
`paprnav-ad-v4-validator-2` remains `schemaVersion: ad_extraction_v4` and uses
the distinct canonicalization profile `paprnav-ad-v4-c14n-2`. New submissions
use only the v2 pair. Stored v1 candidates retain their bytes, hashes, events,
audit readability, and `candidate_only` gate. They are neither rewritten nor
deleted. A validator-1 proposal containing either defect below receives stable
materializer refusal
`predecessor_semantic_defect`; the safe path is a new validator-2 candidate
linked by `corrects_candidate`. Refusal to derive new rows is not mutation or
invalidation of the stored candidate.

#### Explicit uncertainty for the 1998 packet

The source wording “If it cannot be determined” remains in its admitted exact
evidence fragment. It is not persisted as the artificial known value
`unknown_requires_compliance`. The corrected `condition-provenance-unknown`
uses the already closed known/unknown/not-applicable union:

```json
"attributeValue": {
  "state": "unknown",
  "reason": "not_observed",
  "temporalScope": {"kind": "at_applicability_evaluation"},
  "evidenceKeys": ["ev-unknown-provenance"]
}
```

Its condition remains a typed `reviewed_manual_predicate/requires_review` leaf.
Kleene evaluation is not performed in 3A, but any future evaluator must treat
the unknown operand as unknown/fail-closed, not false. Validator 2 rejects the
exact reserved semantic sentinel `unknown_requires_compliance` in a known
union. It does not guess from broad words such as “unknown” in authentic source
text. A schema negative and semantic negative enforce the reserved-token rule.

Implementation must preserve byte-identical validator-1/c14n-1 artifacts and
dispatch stored read verification by the row's recorded validator and
canonicalization versions; new writes and the corrected 1998 calibration
candidate use validator-2/c14n-2. Regression gates prove the old stored
candidate still verifies under v1, the new validator rejects the sentinel, the
corrected proposal stores under v2 with a new canonical hash, and no existing
row/event changes.

#### Compound designation groups and search-hint associations

Validator 2 adds closed, optional typed designation-group structures. Source
display wording is stored separately and is never parsed to create members.
For a condition subject the shape is:

```json
"designationGroup": {
  "groupKey": "...",
  "sourceDisplayText": {"state":"known","value":"...","evidenceKeys":["..."]},
  "association": "all_members|any_member|source_group|unknown",
  "members": [
    {
      "memberKey":"...",
      "designationKind":"model|series_expression",
      "sourceDesignation":"...",
      "manufacturer": {"state":"known|unknown|not_applicable", "...":"..."},
      "evidenceKeys":["..."]
    }
  ],
  "evidenceKeys":["..."]
}
```

For `association: unknown`, the group also requires controlled reason and
temporal scope. Member manufacturer uses the existing explicit union. Member
and group keys are unique; member ordering is a canonical set keyed by
`memberKey`. `sourceDisplayText` is display/evidence fidelity only. No service
splits commas, slashes, conjunctions, whitespace, or prefixes.

The corrected 2002 candidate represents:

- exact display `6314,6324,6364` plus three `any_member` magneto model members;
- exact display `C-125,C145,O-300,IO-360,TSIO-360` plus five `any_member`
  engine model/series members;
- `LTSIO-520-AE` as one atomic member; and
- its non-exhaustive airframe hint as seven explicit manufacturer groups and
  20 source-faithful typed members: 19 exact model-designation members plus one
  Cessna `series_expression` member whose exact expression text is
  `172A through 172H`, evaluation state is `unknown`, and reason is
  `unsupported_expression`. Cessna has eight exact model members plus that one
  expression; Beagle has 1, Cirrus 2, Globe Swift 2, Maule 1, Piper 2, and
  Reims (Cessna) 3 exact models. The old fabricated manufacturer value
  `multiple` is not a normalized identity. No exact `172A`, `172B`, ...,
  `172H` member is inferred from the expression.

The retained-source count oracle is exact: Cessna model members are `170`,
`170A`, `170B`, `172`, `172XP`, `336`, `337`, and `T303`, plus the one series
expression; Beagle is `B242-C`; Cirrus is `SR20`,`SR22`; Globe Swift is
`GC-1A`,`GC-1B`; Maule is `M4`; Piper is `PA-28R-201T`,`PA-34`; and Reims
(Cessna) is `FA172`,`F337`,`FR172`. These are 19 exact models + 1 expression,
not 27 exact models.

The corrected 2024 candidate preserves exact display `GFC 500 and GSA 28` and
uses `all_members` with two Garmin model members. Its STC and master-drawing
fields remain separate condition-subject assertions.

Validator-2 search hints replace the ambiguous flat manufacturer/models pair
with `sourceDisplayText` plus `manufacturerModelGroups`. Each group has a
manufacturer explicit union, exact model-member rows, association state, and
evidence. If the source does not establish a pairing, manufacturer association
is explicit `unknown/source_ambiguous`; models remain individually queryable
but not assigned to a maker. Hints remain fixed `controlling:false` and
`exhaustive:false` and cannot be referenced by an expression.

Validator-1 candidates remain readable. Validator 2 accepts the old atomic
`modelOrSeries` only as one unparsed source value and forbids using it as a
typed member set. Corrected calibration fixtures use the group form wherever
the source expresses more than one designation. The implementation scope
therefore includes versioned schema/validator dispatch, the 1998, 2002, and
2024 proposal corrections, and predecessor calibration/service regressions;
retained PDFs and fragment selections do not change.

#### Validator-2 canonicalization and hash domains

Validator 2 closes every new object with `additionalProperties:false` and
uses these normative shapes:

- condition `designationGroup` requires exactly `groupKey`,
  `sourceDisplayText`, `association`, `members`, and `evidenceKeys`; it permits
  `reason` and `temporalScope` only when `association:"unknown"`, when both are
  required;
- each designation-group member requires `memberKey`, `designationKind`,
  `manufacturer`, and `evidenceKeys`. The closed `model` branch additionally
  requires `sourceDesignation`. The closed `series_expression` branch instead
  requires `expressionText`, fixed `evaluationState:"unknown"`, and fixed
  `reason:"unsupported_expression"`; it forbids `sourceDesignation` and any
  parsed lower/upper/prefix member fields;
- each v2 applicability search hint requires exactly `hintKey`, `productRole`,
  `sourceDisplayText`, `manufacturerModelGroups`, `controlling:false`,
  `exhaustive:false`, and `evidenceKeys`; the v1 flat `manufacturer`/`models`
  pair is not legal in validator 2;
- each manufacturer/model group requires `groupKey`, the existing explicit
  manufacturer union, `association`, `members`, and `evidenceKeys`; unknown
  association additionally requires controlled `reason` and `temporalScope`;
  and
- each hint member uses the same closed `model|series_expression` one-of and
  exact field exclusions as a designation-group member.

`sourceDisplayText`, manufacturer unions, temporal scope, identifiers, and
evidence keys reuse the already closed V4 definitions. No new open object,
free-form discriminator, or unannotated array is permitted.

`paprnav-ad-v4-c14n-2` inherits every scalar, object-key, decimal, Unicode,
date, and existing-array rule from c14n-1. It adds only these closed array
annotations introduced by validator 2:

- `designationGroup.members`: set keyed by unique `memberKey`;
- `applicabilitySearchHints[].manufacturerModelGroups`: set keyed by unique
  `groupKey`; and
- `manufacturerModelGroups[].members`: set keyed by unique `memberKey`.

The `designationGroup` and `sourceDisplayText` shapes are objects, not arrays.
Every v2 array, including inherited arrays, has an explicit
`x-paprnav-array-kind`; validator-2 meta-tests fail any missing annotation.
Within a group, `model` members carry one exact designation; a
`series_expression` member carries one exact expression plus fixed
`evaluationState:"unknown"` and `reason:"unsupported_expression"`. C14n-2
does not expand, parse, or reorder characters within that expression. Adding
or changing any array shape requires c14n-3 and a new reviewed boundary.

Every separator below is the displayed ASCII/UTF-8 string followed by exactly
one NUL byte `0x00`. Complete bytes, including the final `00`, are normative:

| v2 hash object | ASCII before NUL | complete hex bytes |
| --- | --- | --- |
| proposal | `paprnav:ad_extraction_v4:proposal:paprnav-ad-v4-c14n-2` | `706170726e61763a61645f65787472616374696f6e5f76343a70726f706f73616c3a706170726e61762d61642d76342d6331346e2d3200` |
| evidence bindings | `paprnav:ad_extraction_v4:evidence-bindings:2` | `706170726e61763a61645f65787472616374696f6e5f76343a65766964656e63652d62696e64696e67733a3200` |
| candidate event | `paprnav:ad_extraction_v4:candidate-event:2` | `706170726e61763a61645f65787472616374696f6e5f76343a63616e6469646174652d6576656e743a3200` |
| submission | `paprnav:ad_extraction_v4:submission:2` | `706170726e61763a61645f65787472616374696f6e5f76343a7375626d697373696f6e3a3200` |
| submission relationship | `paprnav:ad_extraction_v4:submission-relationship:2` | `706170726e61763a61645f65787472616374696f6e5f76343a7375626d697373696f6e2d72656c6174696f6e736869703a3200` |

For each object, `hash = lowercase_hex(SHA-256(domain_bytes ||
restricted_jcs_v2(envelope)))`. The proposal envelope is the closed v2 root.
Other v2 envelopes retain the v1 field meanings but use fixed literal versions
`ad-v4-evidence-bindings-v2`, `ad-v4-candidate-created-v2`,
`ad-v4-submission-v2`, and `ad-v4-submission-relationship-v2`. Each v2 audit
envelope additionally contains exactly
`validatorVersion:"paprnav-ad-v4-validator-2"` and
`canonicalizationVersion:"paprnav-ad-v4-c14n-2"`. These fields are
server-derived. V1 rows retain their exact v1 envelope bytes and v1 domains;
their hashes are never recomputed under v2.

Proposal content identity and reuse are scoped by `(directive_id,
validator_version, canonicalization_version, canonical_hash)`. Therefore the
same logical source values submitted under v1/c14n-1 and v2/c14n-2 produce
distinct proposal/hash identities, even if their restricted-JCS payload bytes
happen to match. Binding, submission, relationship, and event identity/retry
comparison likewise occurs only within an identical validator/canonicalization
pair and its version-specific domain. Cross-version equality never causes
reuse.

### 1. Projection and hash boundary

Define canonical applicability subtree `A(P)` from verified proposal `P` as
exactly:

```json
{
  "productScopes": P.productScopes,
  "conditionDefinitions": P.conditionDefinitions,
  "applicabilityRules": P.applicabilityRules,
  "applicabilitySearchHints": P.applicabilitySearchHints
}
```

The properties appear under validator-2/c14n-2 canonical object ordering. The
3A materializer accepts only `paprnav-ad-v4-validator-2` with
`paprnav-ad-v4-c14n-2`; v1 candidates remain dual-reader auditable but are not
projected. Array set/sequence behavior is the explicit c14n-2 contract above;
Slice 3A defines no alternative canonicalizer.

`applicability_subtree_hash` is lowercase hex SHA-256 of:

```text
UTF-8("paprnav:ad_extraction_v4:applicability-subtree:paprnav-ad-v4-c14n-2")
|| 0x00 || restricted_jcs(A(P))
```

The complete subtree domain bytes, including the final NUL, are
`706170726e61763a61645f65787472616374696f6e5f76343a6170706c69636162696c6974792d737562747265653a706170726e61762d61642d76342d6331346e2d3200`.

Materializer version is fixed as `paprnav-ad-v4-app-materializer-2`.
Projection identity hash uses:

```text
UTF-8("paprnav:ad_extraction_v4:applicability-projection:2") || 0x00 ||
restricted_jcs({
  "version":"ad-v4-applicability-projection-v2",
  "proposalId": proposal_id,
  "proposalCanonicalHash": proposal_canonical_hash,
  "evidenceBindingHash": evidence_binding_hash,
  "validatorVersion":"paprnav-ad-v4-validator-2",
  "canonicalizationVersion":"paprnav-ad-v4-c14n-2",
  "materializerVersion":"paprnav-ad-v4-app-materializer-2",
  "applicabilitySubtreeHash": applicability_subtree_hash,
  "semanticNodeHashes":[...sorted by node type and node key...],
  "evidenceLinkHashes":[...sorted by node key and evidence key...]
})
```

The complete projection domain bytes, including final NUL, are
`706170726e61763a61645f65787472616374696f6e5f76343a6170706c69636162696c6974792d70726f6a656374696f6e3a3200`.

Every row ID is server-derived as its table prefix plus the first 32 lowercase
hex characters of a domain-separated full identity hash. Each row stores the
full identity hash and a uniqueness constraint; a truncated-ID collision with
a different full hash is an integrity error, not reuse.

### 2. Additive PostgreSQL mapping

All tables use explicit stable string codes plus CHECK constraints rather than
application-only enums. Every FK named below is `ON DELETE RESTRICT`; every
table receives an UPDATE/DELETE rejection trigger.

#### 2.1 Root, request, lifecycle, and dependencies

`ad_v4_candidate_app_projections`

- `id`, full `identity_hash`, `proposal_id`, `directive_id`;
- repeated `schema_version`, `validator_version`, `canonicalization_version`,
  `proposal_canonical_hash`, and `evidence_binding_hash`;
- fixed `materializer_version`, `applicability_subtree_hash`,
  `projection_hash`, and constant `gate = 'candidate_only'`;
- exact counts for semantic nodes, typed rows, and evidence links;
- `created_at`; no mutable status/current/approval/release column;
- UNIQUE `(proposal_id, materializer_version)`, UNIQUE `identity_hash`, and
  UNIQUE `(id, proposal_id)`; and
- a composite parent check/trigger requiring all repeated columns to equal the
  referenced Slice-2 candidate proposal and its gate to remain candidate-only.

`ad_v4_candidate_app_materialization_requests`

- immutable `id`, projection/proposal/directive IDs, actor user, exact
  authorizing membership and organization, snapshotted role/status, fixed
  policy name/version/claims hash, fixed endpoint action, idempotency key,
  request hash, and created time;
- actor/role/status CHECKs require active platform admin;
- UNIQUE `(actor_user_id, authorizing_membership_id, endpoint_action,
  auth_policy_version, idempotency_key)`; and
- composite FKs require request projection/proposal/directive equality.

`ad_v4_candidate_app_projection_events`

- `id`, projection/proposal IDs, `sequence_number`, event type
  `materialized|candidate_corrected|candidate_replaced|
  evidence_invalidated|candidate_supersession_signal`, reason code, optional
  causing Slice-2 relationship ID, lifecycle-event ID, projection ID, or
  `causing_dependency_id`; predecessor event hash, canonical event bytes/hash,
  actor kind `platform_admin|system`, actor request ID when platform-admin,
  and occurred time;
- sequence 0 is exactly one `materialized` root with null predecessor; later
  events require the previous same-projection hash;
- closed discriminator checks require: `materialized` names only its request;
  `candidate_corrected|candidate_replaced` name only the matching Slice-2
  relationship; `evidence_invalidated` names only the matching lifecycle
  event; and `candidate_supersession_signal` names only a same-projection
  incoming dependency row through composite FK `(projection_id,
  causing_dependency_id)`;
- system events have no human actor and name exactly one deterministic causal
  row;
  platform-admin events require a request; and
- UNIQUE `(projection_id, sequence_number)`, UNIQUE `(projection_id,
  event_hash)`, UNIQUE `(projection_id, event_type, causing_dependency_id)`
  where a dependency is present, and equivalent partial causal uniqueness keys
  for relationship and lifecycle causes.

`ad_v4_candidate_app_change_dependencies`

- semantic node/projection/proposal IDs and dependency kind
  `outgoing_supersedes|outgoing_partially_supersedes|
  incoming_supersession_signal`;
- an outgoing supersession row preserves predecessor and successor AD numbers
  exactly as stated and is evidence-bound to both the relation and this
  proposal's known `directiveIdentity.adNumber` assertion;
- resolution state `resolved_candidate|unresolved|ambiguous`, with target
  directive/projection IDs used only for a uniquely resolved candidate signal;
- explicit unresolved reason instead of a nullable target meaning unknown; and
- evidence links to the dependency semantic node. No dependency row changes a
  released directive or becomes legal supersession authority.

For every canonical relation, the successor must equal the proposal's known,
evidence-bound canonical AD number before resolution is attempted. A mismatch
stores one outgoing row as `unresolved/successor_not_this_proposal` and creates
no target-local row or event. When the predecessor resolves uniquely, the
service locks both projection roots in lexical order and creates a deterministic
`incoming_supersession_signal` row in each affected predecessor projection.
That row references the outgoing source row, repeats no evidence text, and is
the exact same-projection cause of the stale event. Multiple, contradictory, or
unresolved relations produce only unresolved dependency rows and no side
effect. Retry and concurrent workers converge on the same incoming dependency
and event by full cause hash plus the causal unique constraint.

#### 2.1.1 Shared authoritative-correction foundation

Slice 3A creates a shared proposal-scoped correction foundation used unchanged
by Slice 3B. It is not an applicability-only copy.

`ad_v4_candidate_corrections`

- immutable proposal-scoped correction root with proposal ID (and no
  applicability- or obligation-projection ownership), canonical
  `correction_key`, correction type, original and correcting
  `officialDocuments` reference keys, their verified document-identity hashes,
  the correction object's canonical hash, canonical ordinal, foundation
  version `paprnav-ad-v4-correction-foundation-1`, and generation `1`;
- expected changed-reference count and expected evidence-key count from the
  canonical object; and
- UNIQUE `(proposal_id, correction_key)`, UNIQUE full identity hash, and
  composite parent/document FKs. The root owns the correction evidence links
  once; neither 3A nor 3B copies those links.

`ad_v4_candidate_correction_refs`

- correction root/proposal IDs, canonical ordinal, namespace, exact
  key, owner slice, and canonical reference hash;
- namespace is closed to the complete canonical set:
  `directiveIdentity|productScopes|conditionDefinitions|applicabilityRules|
  requirements|recurrenceGroups|amocAuthorityProvisions|
  supersessionRelations`;
- owner slice is `foundation|slice_3a|slice_3b`, fixed by namespace:
  directive identity and supersession relations are foundation-owned;
  product scopes, conditions, and applicability rules are 3A-owned; and
  requirements, recurrence groups, and AMOC authority provisions are
  3B-owned; and
- UNIQUE `(correction_id, namespace, key)` and UNIQUE `(correction_id,
  canonical_ordinal)` preserve the complete ordered reference set now,
  including future-3B references. No count-only placeholder is allowed.

`ad_v4_candidate_correction_semantic_bindings`

- correction-reference/proposal IDs, binding generation, binding slice,
  owner-projection kind/ID, semantic node type/ID, and binding hash;
- a same-proposal composite FK binds a 3A reference to exactly the semantic
  node in its applicability projection reconstructed from that canonical key;
  Slice 3B later binds to its own same-proposal obligation projection, so the
  shared root is never reassigned between projections; and
- UNIQUE `(correction_ref_id, binding_slice, binding_generation)`.

`ad_v4_candidate_correction_evidence_links`

- correction root/proposal IDs, exact Slice-2 candidate binding ID and evidence
  key, purpose `correction_clause`, canonical ordinal, and link hash;
- composite FK to the same-proposal Slice-2 evidence snapshot; and
- UNIQUE `(correction_id, evidence_key)` plus unique canonical ordinal. These
  are the correction's one authoritative evidence-link set; applicability
  nodes referenced by the correction retain only their own canonical evidence,
  not a second copy of correction evidence.

Foundation completeness requires one root per canonical correction, exact
official-document identity, the complete ordered changed-reference namespace,
and the exact evidence set before the 3A transaction commits. Generation 1 is
3A-complete only when every 3A-owned reference has one binding; foundation and
3B-owned references remain explicit rows with their owner state and never use
SQL NULL as a placeholder. Slice 3B later inserts immutable generation-1
bindings for its owned refs under the same roots. It neither updates nor
duplicates roots, refs, official-document attribution, or evidence links.

For calibration correction `correction-2010`, reconstruction is exact: one
root retains its original/correcting official-document keys, two evidence keys
linked once, and the complete ordered reference set
`productScopes/scope-cessna`, `requirements/req-report`. Slice 3A binds only
`scope-cessna`; `req-report` remains explicitly `slice_3b` owned. After 3B it
receives one requirement binding. Joining root + ordered refs + the one root
evidence set reconstructs the same canonical correction object before and
after 3B; semantic bindings are validation edges and are not serialized into
the canonical correction JSON.

#### 2.2 Semantic nodes and evidence links

`ad_v4_candidate_app_semantic_nodes`

- `id`, full identity hash, projection/proposal IDs, node type, stable node key,
  canonical source pointer, canonical node hash, and created time;
- node types are exactly `product_scope|designation_scope|value_assertion|
  identity_mapping|designation_value|designation_range|designation_group|
  designation_group_member|condition|expression|applicability_rule|
  search_hint|search_hint_group|search_hint_model|change_dependency`;
- UNIQUE `(projection_id, node_type, node_key)`, UNIQUE `identity_hash`, and
  UNIQUE `(id, projection_id, proposal_id)`; and
- a deferred ownership trigger requires exactly one matching typed owner row
  for each node and rejects typed rows with the wrong node type.

`ad_v4_candidate_app_evidence_links`

- `id`, projection/proposal IDs, semantic node ID, Slice-2 candidate binding
  ID, evidence key, purpose code, canonical ordinal, and link hash;
- purpose is a closed code such as `scope_clause`, `identity_support`,
  `designation_scope`, `condition_clause`, `subject_value`, `rule_clause`,
  `search_hint_clause`, `correction_clause`, or `supersession_clause`;
- composite FK `(projection_id, proposal_id, semantic_node_id)` binds the
  owner; composite FK `(proposal_id, candidate_binding_id, evidence_key)` binds
  the exact Slice-2 evidence snapshot; and
- UNIQUE `(semantic_node_id, purpose, evidence_key)`. A deferred check requires
  the exact canonical evidence-key set for each evidence-bearing source
  pointer. There is no text column.

The 3A migration may add the supporting UNIQUE constraint
`(proposal_id,id,evidence_key)` to the immutable Slice-2 binding table; it does
not change or backfill its data.

#### 2.3 Source values and candidate identity normalization

`ad_v4_candidate_app_value_assertions`

- semantic node/projection/proposal IDs, parent semantic node ID, field code,
  state `known|unknown|not_applicable`, value type `text`, optional exact text
  value, controlled reason code, and temporal-scope kind;
- known => text value present and reason/temporal unused;
- unknown/not-applicable => text value unused and reason/temporal present;
- UNIQUE `(parent_semantic_node_id, field_code)`; and
- deferred evidence requires one or more exact binding links for every row.

`ad_v4_candidate_app_identity_mappings`

- semantic node/projection/proposal IDs, exact `source_occurrence_node_id`, one
  `evidence_parent_node_id`, identity kind `manufacturer|model|series`, exact
  source value, normalization origin
  `candidate_payload|source_only|no_normalized_identity`, normalized state,
  normalized value, controlled reason and temporal scope, normalization
  namespace/version, and fixed review state `unreviewed_candidate`;
- `source_occurrence_node_id` is the exact manufacturer assertion,
  designation-value, designation-group-member, or hint-group-member node whose
  source value is mapped. A composite FK requires that node, its evidence
  parent, projection, and proposal to agree. Each exact occurrence receives one
  mapping even when equal source strings occur elsewhere;
- `candidate_payload` is legal only when that exact canonical occurrence has a
  `normalizedIdentity`; it requires known state/value and reconstructs that
  canonical property. The application cannot relabel source spelling as a
  normalized identity;
- `source_only` is used when a condition or search-hint occurrence has source
  identity text but its canonical shape offers no normalized identity;
  `no_normalized_identity` is used for a listed designation, designation-group
  member, or series occurrence whose closed canonical object has no normalized
  property;
- both non-payload origins require state `unknown`, controlled reason
  `not_extracted|not_yet_reviewed`, temporal scope
  `source_observation|directive_version`, and inherited evidence through the
  single `evidence_parent_node_id`; they cannot carry a normalized value,
  namespace, version, or token; and
- UNIQUE `(projection_id, identity_kind, source_occurrence_node_id)`. No global
  aircraft/manufacturer/model table references these rows and no per-occurrence
  evidence-link copy is created.

The 2002 condition member `6314` maps as `model/source_only/unknown`, inheriting
the `condition-magneto-models` group evidence once. A Cessna hint model member
maps as `model/source_only/unknown`, inheriting that manufacturer-model group's
evidence once. A product-scope manufacturer with an actual canonical
`normalizedIdentity` maps as `manufacturer/candidate_payload/known`. These
origins cannot be interchanged.

#### 2.4 Product and designation scopes

`ad_v4_candidate_app_product_scopes`

- product-scope semantic node/projection/proposal IDs, `scope_key`, product role
  `airframe|engine|propeller|appliance|installed_part|modification`;
- manufacturer presence `property_absent|present`, exact source manufacturer
  value when present, and candidate manufacturer identity-mapping node ID when
  present;
- independent model/serial/part property-presence codes; and
- UNIQUE `(projection_id, scope_key)`. CHECKs require value/mapping only for a
  present manufacturer and distinguish omission from explicit unknown.

`ad_v4_candidate_app_designation_scopes`

- designation-scope semantic node/projection/proposal IDs, parent product scope
  node ID, field kind `model|serial|part_number`, and scope kind
  `all|listed|series_expression|ranges|unknown|not_applicable`;
- exact series expression only for `series_expression`;
- controlled reason and temporal-scope kind only for unknown/not-applicable;
- fixed comparison/evaluation state. Series expressions are
  `unknown/unsupported_expression`, not executable patterns;
- UNIQUE `(product_scope_node_id, field_kind)`; and
- deferred cardinality checks: listed has one or more values and no ranges;
  ranges has one or more ranges and no values; other kinds have neither.

`ad_v4_candidate_app_designation_values`

- semantic node/projection/proposal and designation-scope IDs, exact source
  value, canonical ordinal, and model/series identity-mapping node for that
  exact designation-value semantic node;
- the mapping's `source_occurrence_node_id` must equal this row's semantic-node
  ID, while its `evidence_parent_node_id` equals the one designation-scope node.
  Thus 51 values create 51 mappings but still one parent evidence link;
- UNIQUE `(designation_scope_id, source_value)` and UNIQUE
  `(designation_scope_id, canonical_ordinal)`; and
- ordinals must equal the Slice-2 canonical exact-string set order.

Static cardinality proof over the five calibration packets is mandatory:

| packet | listed value occurrences | identity mappings | parent-scope inheritance edges |
| --- | ---: | ---: | ---: |
| 1998-17-11 | 51 + 30 = 81 | 81 | 2 |
| 2002-13-04 | 6 | 6 | 1 |
| 2008-26-10 | 182 | 182 | 1 |
| 2011-10-09 | 224 | 224 | 1 |
| 2024-14-03 | 7 + 2 + 10 + 33 + 130 = 182 | 182 | 5 |

The multi-model uniqueness gate is therefore feasible for 5 of 5 packets and
cannot collapse two exact value occurrences into one mapping.

`ad_v4_candidate_app_designation_ranges`

- semantic node/projection/proposal and designation-scope IDs, exact lower and
  upper strings, lower/upper inclusive booleans, polarity
  `included|excluded`, canonical ordinal, and fixed lexical comparator version;
- composite uniqueness across the five canonical range identity fields and
  unique ordinal; and
- no numeric coercion or range membership result is stored.

#### 2.5 Conditions and three-valued expressions

`ad_v4_candidate_app_conditions`

- condition semantic node/projection/proposal IDs, `condition_key`, exact
  condition type and operator closed to the V4 enums, temporal-basis kind,
  comparator property presence/value, subject product-role
  presence/value, and subject attribute-key presence/value;
- fixed `evaluation_state = 'unevaluated'` and
  `evaluator_contract = 'none'`;
- UNIQUE `(projection_id, condition_key)`; and
- closed enum and shape checks require the exact subject properties,
  designation groups, group members, and value-assertion children found in the
  canonical candidate. There is deliberately no type/operator compatibility
  matrix in 3A.

Every pair from the independent Slice-2 `conditionType` and `operator` enums
is representable and reconstructable as `unevaluated` when the enclosing
closed schema shape is valid. This representation does not declare that every
pair is meaningful or executable. A future evaluator may narrow semantics only
through a separately reviewed, versioned canonical-boundary and evaluator
contract; it may not reinterpret existing 3A rows.

Subject fields `manufacturer`, atomic `modelOrSeries`, `partNumber`,
`serialNumber`, `stcNumber`, and `attributeValue` are
`ad_v4_candidate_app_value_assertions` children using those exact field codes.
The validator-2 `designationGroup` is stored as one source-faithful group row,
one exact display assertion, and typed member rows with explicit association;
it is never derived from the display string. Manufacturer/model/series
occurrences receive separate unreviewed identity mappings; the assertion and
display values remain source-faithful.

`ad_v4_candidate_app_designation_groups`

- semantic node/projection/proposal and owning-condition IDs, group key,
  association `all_members|any_member|source_group|unknown`, exact source
  display assertion ID, controlled unknown reason and temporal scope, and
  canonical ordinal;
- non-unknown association forbids unknown reason/temporal; unknown association
  requires both plus exact evidence; and
- UNIQUE `(condition_node_id, group_key)` and unique ordinal.

`ad_v4_candidate_app_designation_group_members`

- semantic node/projection/proposal and group IDs, member key, designation kind
  `model|series_expression`, exact source designation/expression, explicit
  manufacturer union state and value/reason/temporal fields, fixed evaluation
  state/reason for series expressions, canonical ordinal, and exact-occurrence
  identity-mapping node;
- group association and typed members come only from canonical validator-2
  bytes, never from source display punctuation; and
- UNIQUE `(group_id, member_key)`, UNIQUE `(group_id, canonical_ordinal)`, and
  composite same-projection FKs for group, manufacturer assertion, and mapping.

`ad_v4_candidate_app_expressions`

- expression semantic node/projection/proposal IDs, owning rule ID, expression
  context `scope|condition`, deterministic expression path, node type, fixed
  result domain/evaluator version, and nullable typed ref columns for scope,
  condition, or rule;
- leaf CHECKs require exactly the correct ref; `not|all|any` have no ref;
- UNIQUE `(owning_rule_id, expression_context, expression_path)`; and
- composite FKs bind every leaf ref to the same projection/proposal.

`ad_v4_candidate_app_expression_edges`

- projection/proposal IDs, parent expression ID, child expression ID, and
  sequence;
- UNIQUE `(parent_expression_id, sequence)`, UNIQUE
  `(parent_expression_id, child_expression_id)`; and
- deferred checks enforce no cross-context edge, no cycle, `not` arity 1,
  `all|any` arity >=2, leaf arity 0, one root per rule/context, and contiguous
  sequence from zero. Sequence is regulatory/canonical and is not sorted.

`ad_v4_candidate_app_rules`

- rule semantic node/projection/proposal IDs, `rule_key`, scope-root expression
  ID, condition property presence and optional condition-root expression ID,
  and fixed evaluator version;
- UNIQUE `(projection_id, rule_key)`; and
- composite FKs bind both roots to the same rule/projection and correct
  expression context.

`ad_v4_candidate_app_rule_exclusions`

- projection/proposal IDs, rule ID, excluded rule ID, and canonical ordinal;
- UNIQUE `(rule_id, excluded_rule_id)` and unique ordinal; and
- same-projection FKs plus deferred acyclicity. Empty exclusions are represented
  by zero rows, not a nullable array.

#### 2.6 Non-controlling search hints

`ad_v4_candidate_app_search_hints`

- search-hint semantic node/projection/proposal IDs, `hint_key`, product role,
  exact source display text, fixed `controlling = false`, fixed
  `exhaustive = false`;
- UNIQUE `(projection_id, hint_key)`; and
- no expression table has a hint-reference column or FK.

`ad_v4_candidate_app_search_hint_groups` and
`ad_v4_candidate_app_search_hint_members`

- group rows preserve canonical group key/ordinal, manufacturer explicit
  union, association `paired|source_group|unknown`, controlled unknown reason,
  temporal scope, and evidence parent;
- member rows preserve group ID, `member_key`, typed `designation_kind`
  `model|series_expression`, canonical ordinal, exact-occurrence unreviewed
  identity mapping, and the single inherited group evidence-parent edge;
- a `model` member requires exact `source_designation` and forbids expression,
  evaluation, and reason columns. A `series_expression` member instead requires
  exact `expression_text`, `evaluation_state = 'unevaluated'`, controlled
  `reason = 'unsupported_expression'`, normalization origin `source_only`,
  normalized state `unknown`, and forbids an exact model designation;
- UNIQUE `(hint_id, group_key)`, UNIQUE `(group_id, member_key)`, and UNIQUE
  `(group_id, canonical_ordinal)`; exact source values are not overloaded as
  relational discriminators; and
- rows may support administrator research only. They are excluded from rule
  reconstruction except as the hint's exact canonical group/member arrays.

The reconstruction discriminator emits every canonical-v2 member variant from
these typed columns. It never decides the variant from punctuation or parses
`expression_text`; evidence is inherited from the group once and not copied per
member.

The 2002 hint reconstructs seven manufacturer groups, 19 exact model members,
and one source-faithful `series_expression` member for `172A through 172H`;
no row contains manufacturer `multiple`, no `172A` through `172H` exact rows
are inferred, and no comma/range/prefix parsing is used.
The 2024 condition reconstructs one Garmin `all_members` group with exact GFC
500 and GSA 28 members; STC and master-drawing assertions remain separate. If
a hint's source does not establish manufacturer/model pairing, the group uses
`association=unknown`, reason `source_ambiguous`, temporal scope, and evidence;
the materializer never assigns a manufacturer heuristically.

### 3. Database completeness and reconstruction contract

At deferred commit, `paprnav_v4_candidate_app_require_complete(projection_id)`
must:

1. lock and verify the parent candidate proposal and exact repeated hashes;
2. verify its Slice-2 canonical bytes/JSON mirror and evidence-binding rows;
3. require exactly one materialized root event and the recorded row counts;
4. require exactly one typed owner for every semantic node and no unowned typed
   row;
5. verify every composite same-projection reference, expression arity/cycle,
   condition child/group set, designation child set, identity occurrence
   mapping, and exact evidence-key set;
6. verify one correction foundation per canonical correction, its exact
   official-document identities, complete ordered reference namespace, one
   evidence set, and all 3A-owned semantic bindings for generation 1;
7. reconstruct the four-field JSONB subtree in canonical array order;
8. require JSONB equality with those four fields extracted from the parent
   proposal mirror;
9. require the application-supplied restricted-JCS subtree bytes/hash and
   projection hash to match server-generated values; and
10. fail the transaction on any mismatch.

PostgreSQL need not implement restricted JCS. It verifies SHA-256 over the
already canonical subtree bytes, relational-to-parent JSONB equality, every
envelope field, and the aggregate row identity/hash set. The application
reconstructs, canonicalizes, and verifies bytes/hash before insert and every
audit read. This follows the reviewed Slice-2 division of responsibility while
preventing self-consistently rehashed forged relational rows.

Property-presence columns are normative. Reconstruction never guesses whether
an absent optional property was unknown. Set arrays sort using the checked-in
Slice-2 schema annotations; expression operands retain stored sequence.

### 4. Index contract without read cutover

The migration creates only integrity, reconstruction, source-audit, and
stale-fold indexes used by the bounded 3A service, in addition to primary,
foreign-key-supporting, and uniqueness indexes:

- projection `(proposal_id, materializer_version)` and request idempotency;
- semantic-node `(projection_id, node_type, node_key)` and typed-owner
  composite-FK support;
- evidence-link `(proposal_id, candidate_binding_id, evidence_key)` and
  `(semantic_node_id, purpose, canonical_ordinal)`;
- designation/group/member parent + canonical-ordinal indexes used for exact
  reconstruction, never source-string lookup;
- expression-edge parent/sequence and child indexes, and exact scope,
  condition, and rule reference-FK indexes;
- correction-root `(proposal_id, correction_key)`, correction-ref
  `(correction_id, canonical_ordinal)`, and binding completeness indexes;
- dependency causal/source IDs and exact predecessor-AD resolution support;
  and
- event `(projection_id, sequence_number)` and partial cause indexes required
  by the stale fold.

There is no index on source manufacturer/model spelling, normalized values or
tokens, product-role lookup, search hints, aircraft IDs, or candidate make/model
combinations. Slice 3A makes no hot-path or matching-readiness claim. The later
reviewed identity bridge must define its own aircraft/canonical-identity join
and indexes in the matching slice; it cannot reuse an unreviewed candidate
mapping as authority. Repository tests assert both the absence of these
premature index definitions and the absence of released readers using 3A.

### 5. Materializer, authorization, and concurrency contract

#### 5.1 Default-off capability gates

Two independent application settings are introduced with literal defaults of
`false`:

- `PAPRNAV_AD_V4_VALIDATOR2_WRITES_ENABLED=false`; and
- `PAPRNAV_AD_V4_SLICE3A_ROUTES_ENABLED=false`.

The first gates every validator-2 candidate POST before parsing or persistence.
The second gates registration/exposure of the 3A materialization POST and both
3A audit GET routes. Migration 0027 also creates two database gate keys,
`validator2_write_enabled` and `materializer3a_enabled`, both default false.
The application role may read but not enable them; only the deployment database
role may change them through the audited gate procedure. Enabling one gate or
flag never implies the other. Merely running 0027 cannot expose a v2 writer or
a 3A route.

The application has fixed compiled capabilities
`SUPPORTED_V4_VALIDATOR_PAIRS` and `SUPPORTED_V4_MATERIALIZERS`. Migration 0027
provides a read-only database capability function returning the exact revision,
supported validator/canonicalization pairs, materializer version, and the two
gate states. Startup and every write transaction require all three layers:

1. every required application flag and database gate is true;
2. the compiled application capability contains the requested fixed version;
   and
3. the database capability function exists and returns the exact compatible
   0027 capability.

Missing/mismatched database capability, unknown compiled version, or a required
false application/database gate fails closed before writes with stable
`capability_disabled`, `validator2_write_gate_disabled`, or
`materializer3a_gate_disabled`, or
`schema_capability_mismatch`; it never falls back to v1. The transaction repeats
the database capability check after acquiring the proposal/version lock so a
startup check is not trusted as a write-time guarantee. Audit routes require
the 3A application flag, database `materializer3a_enabled`, and compatible
reader capability, but do not require `validator2_write_enabled`: they may read
and verify already-existing projection rows only. They never materialize a
missing projection. Authorization remains the separate exact-membership check
below.

The validator-2 candidate POST requires its application flag plus database
`validator2_write_enabled`. The 3A materialization POST/service transaction
requires **both** application flags, **both** database gates
`validator2_write_enabled` and `materializer3a_enabled`, and both compiled
capabilities. This dependency remains true for a preexisting v2 candidate. If
validator-2 writes are disabled while 3A audit is enabled, materialization
returns stable `validator2_write_gate_disabled` and writes zero request,
projection, dependency, correction, or event rows; audit GET may inspect only a
projection that already exists.

The materializer may perform an unlocked early rejection, but after locking its
```
### `.ai/review-runs/T081-V4-SCHEMA-SLICE-3A/reviews.json`

size=2162; sha256=fed1d13b11caac1d5d5378a4f106265f64fe9cafb30313473d3313f85f373a31; truncated=false

```text
[
  {
    "stage": "design",
    "reviewer": "/root/v4_schema_adversary",
    "builder": "/root/v4_schema_builder",
    "outcome": "fail",
    "reviewedAt": "2026-09-05T03:01:54+00:00",
    "baseRef": "HEAD",
    "head": "28f6be0eab225abc4b68830345e04d6fb6df454f",
    "scopeFingerprint": "7cf76d678ffb1fdef544c989c4052333c92bffc5f7ac7a699beaec7eeadab5f8",
    "artifact": ".ai/review-runs/T081-V4-SCHEMA-SLICE-3A/adversarial-design-initial.md",
    "artifactSha256": "b617aa132d2825d9140540f7d0d41f6d489bf67ec007c1997a5f3dd47a6c328d"
  },
  {
    "stage": "design",
    "reviewer": "/root/v4_schema_adversary",
    "builder": "/root/v4_schema_builder",
    "outcome": "fail",
    "reviewedAt": "2026-09-05T03:22:23+00:00",
    "baseRef": "HEAD",
    "head": "28f6be0eab225abc4b68830345e04d6fb6df454f",
    "scopeFingerprint": "cf0e24c947223822cb12a4b2eefae1c95bd5f426cfb0c2bd3ee63a66c6c3262f",
    "artifact": ".ai/review-runs/T081-V4-SCHEMA-SLICE-3A/adversarial-design-closure-1.md",
    "artifactSha256": "4dc29c60271e0909275f816d3252f2691b1549e96abdcdb34d73c327580f4f45"
  },
  {
    "stage": "design",
    "reviewer": "/root/v4_schema_adversary",
    "builder": "/root/v4_schema_builder",
    "outcome": "pass",
    "reviewedAt": "2026-09-05T16:35:27+00:00",
    "baseRef": "HEAD",
    "head": "28f6be0eab225abc4b68830345e04d6fb6df454f",
    "scopeFingerprint": "a569ea1281b3d0a2508dfb965008209620b67bfcc5830e6f594878487168ca7c",
    "artifact": ".ai/review-runs/T081-V4-SCHEMA-SLICE-3A/adversarial-design-closure-2.md",
    "artifactSha256": "b9524760acfb8632c681b05c0dd32e393d0c7ba89a4a751b93542115f9a2788f"
  },
  {
    "stage": "implementation",
    "reviewer": "/root/v4_s3a_impl_adversary",
    "builder": "/root",
    "outcome": "fail",
    "reviewedAt": "2026-09-07T15:32:40+00:00",
    "baseRef": "28f6be0",
    "head": "28f6be0eab225abc4b68830345e04d6fb6df454f",
    "scopeFingerprint": "6b402ca82f3a91e99b1c4d12dd2c300d67a9b71c7227e54614c7bb9c76a00608",
    "artifact": ".ai/review-runs/T081-V4-SCHEMA-SLICE-3A/adversarial-implementation-initial.md",
    "artifactSha256": "6125935f42332e4bd4add0f15c09cf30fb62773ac8c0cfac1645adb8bd36fc76"
  }
]

```
### `.ai/review-runs/T081-V4-SCHEMA-SLICE-3A/state.json`

size=62; sha256=857a5e9aa8f0011d71f451bfa2c8160002ffa4ca02d2ebffe4a6ccabe9a589b3; truncated=false

```text
{
  "phase": "implementation",
  "bootstrapException": null
}

```
### `backend/app/db/migrations/versions/20260907_0027_add_ad_v4_applicability.py`

size=82407; sha256=26968c0697bf5021de5e8c11888c254f07934815184407d0a56a87deec95f660; truncated=false

```text
"""add validator-2 compatibility and candidate-only V4 applicability projection

Revision ID: 20260907_0027
Revises: 20260901_0026
Create Date: 2026-09-07
"""

from alembic import op
import sqlalchemy as sa


revision = "20260907_0027"
down_revision = "20260901_0026"
branch_labels = None
depends_on = None

V1_VALIDATOR = "paprnav-ad-v4-validator-1"
V1_C14N = "paprnav-ad-v4-c14n-1"
V2_VALIDATOR = "paprnav-ad-v4-validator-2"
V2_C14N = "paprnav-ad-v4-c14n-2"

CHILD_TABLES = (
    "ad_v4_candidate_evidence_bindings",
    "ad_v4_candidate_submissions",
    "ad_v4_candidate_submission_relationships",
    "ad_v4_candidate_proposal_events",
)

APP_TABLES = (
    "ad_v4_feature_gates",
    "ad_v4_candidate_app_projections",
    "ad_v4_candidate_app_materialization_requests",
    "ad_v4_candidate_app_semantic_nodes",
    "ad_v4_candidate_app_data",
    "ad_v4_candidate_app_evidence_links",
    "ad_v4_candidate_app_identity_mappings",
    "ad_v4_candidate_corrections",
    "ad_v4_candidate_correction_refs",
    "ad_v4_candidate_correction_semantic_bindings",
    "ad_v4_candidate_correction_evidence_links",
    "ad_v4_candidate_app_change_dependencies",
    "ad_v4_candidate_app_projection_events",
)


def _id(name: str, *, primary: bool = False) -> sa.Column:
    return sa.Column(name, sa.String(36), primary_key=primary, nullable=False)


def upgrade() -> None:
    for table in CHILD_TABLES:
        op.add_column(table, sa.Column("validator_version", sa.String(64), nullable=True))
        op.add_column(table, sa.Column("canonicalization_version", sa.String(64), nullable=True))
        op.execute(f"ALTER TABLE {table} DISABLE TRIGGER trg_{table}_immutable")
        if table == "ad_v4_candidate_submission_relationships":
            op.execute(f"""UPDATE {table} c SET validator_version=p.validator_version,
                       canonicalization_version=p.canonicalization_version
                  FROM ad_v4_candidate_submissions s, ad_v4_candidate_proposals p
                 WHERE s.id=c.submission_id AND p.id=s.proposal_id""")
        else:
            op.execute(f"""UPDATE {table} c SET validator_version=p.validator_version,
                       canonicalization_version=p.canonicalization_version
                  FROM ad_v4_candidate_proposals p WHERE p.id=c.proposal_id""")
        op.execute(f"ALTER TABLE {table} ENABLE TRIGGER trg_{table}_immutable")
        op.alter_column(table, "validator_version", nullable=False)
        op.alter_column(table, "canonicalization_version", nullable=False)
        op.create_check_constraint(
            f"ck_{table}_version_pair", table,
            "(validator_version='paprnav-ad-v4-validator-1' AND canonicalization_version='paprnav-ad-v4-c14n-1') OR "
            "(validator_version='paprnav-ad-v4-validator-2' AND canonicalization_version='paprnav-ad-v4-c14n-2')",
        )

    op.drop_constraint("uq_ad_v4_proposal_content", "ad_v4_candidate_proposals", type_="unique")
    op.create_unique_constraint(
        "uq_ad_v4_proposal_content_v2", "ad_v4_candidate_proposals",
        ["directive_id", "validator_version", "canonicalization_version", "canonical_hash"],
    )
    op.create_unique_constraint(
        "uq_ad_v4_binding_parent_identity", "ad_v4_candidate_evidence_bindings",
        ["proposal_id", "id", "evidence_key"],
    )

    op.create_table(
        "ad_v4_feature_gates",
        sa.Column("gate_key", sa.String(64), primary_key=True),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("changed_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("changed_by", sa.String(128), nullable=False, server_default="migration"),
        sa.CheckConstraint("gate_key IN ('validator2_write_enabled','materializer3a_enabled')", name="ck_ad_v4_feature_gate_key"),
    )
    op.execute("INSERT INTO ad_v4_feature_gates(gate_key,enabled) VALUES ('validator2_write_enabled',false),('materializer3a_enabled',false)")

    op.create_table(
        "ad_v4_candidate_app_projections",
        _id("id", primary=True), sa.Column("identity_hash", sa.String(64), nullable=False, unique=True),
        _id("proposal_id"), _id("directive_id"), sa.Column("schema_version", sa.String(64), nullable=False),
        sa.Column("validator_version", sa.String(64), nullable=False), sa.Column("canonicalization_version", sa.String(64), nullable=False),
        sa.Column("proposal_canonical_hash", sa.String(64), nullable=False), sa.Column("evidence_binding_hash", sa.String(64), nullable=False),
        sa.Column("materializer_version", sa.String(64), nullable=False), sa.Column("applicability_subtree_bytes", sa.LargeBinary(), nullable=False),
        sa.Column("applicability_subtree_hash", sa.String(64), nullable=False), sa.Column("projection_canonical_bytes", sa.LargeBinary(), nullable=False),
        sa.Column("projection_hash", sa.String(64), nullable=False), sa.Column("gate", sa.String(32), nullable=False),
        sa.Column("semantic_node_count", sa.Integer(), nullable=False), sa.Column("datum_count", sa.Integer(), nullable=False),
        sa.Column("evidence_link_count", sa.Integer(), nullable=False), sa.Column("identity_mapping_count", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["proposal_id"], ["ad_v4_candidate_proposals.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["directive_id"], ["airworthiness_directives.id"], ondelete="RESTRICT"),
        sa.CheckConstraint("gate='candidate_only'", name="ck_ad_v4_app_projection_gate"),
        sa.CheckConstraint(f"validator_version='{V2_VALIDATOR}' AND canonicalization_version='{V2_C14N}'", name="ck_ad_v4_app_projection_v2"),
        sa.UniqueConstraint("id", "proposal_id", name="uq_ad_v4_app_projection_parent_identity"),
        sa.UniqueConstraint("proposal_id", "materializer_version", name="uq_ad_v4_app_projection_parent"),
    )
    op.create_index("ix_ad_v4_app_projection_proposal", "ad_v4_candidate_app_projections", ["proposal_id", "materializer_version"])

    op.create_table(
        "ad_v4_candidate_app_materialization_requests",
        _id("id", primary=True), _id("projection_id"), _id("proposal_id"), _id("directive_id"),
        _id("actor_user_id"), _id("authorizing_membership_id"), _id("organization_id"),
        sa.Column("actor_role", sa.String(64), nullable=False), sa.Column("actor_status", sa.String(32), nullable=False),
        sa.Column("auth_policy_name", sa.String(96), nullable=False), sa.Column("auth_policy_version", sa.String(64), nullable=False),
        sa.Column("auth_claims_hash", sa.String(64), nullable=False), sa.Column("endpoint_action", sa.String(96), nullable=False),
        sa.Column("idempotency_key", sa.String(255), nullable=False), sa.Column("request_canonical_bytes", sa.LargeBinary(), nullable=False),
        sa.Column("request_hash", sa.String(64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["projection_id"], ["ad_v4_candidate_app_projections.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["projection_id", "proposal_id"], ["ad_v4_candidate_app_projections.id", "ad_v4_candidate_app_projections.proposal_id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["proposal_id"], ["ad_v4_candidate_proposals.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["directive_id"], ["airworthiness_directives.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["actor_user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["authorizing_membership_id"], ["organization_memberships.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="RESTRICT"),
        sa.CheckConstraint("actor_role='platform_admin' AND actor_status='active'", name="ck_ad_v4_app_request_auth"),
        sa.UniqueConstraint("actor_user_id", "authorizing_membership_id", "endpoint_action", "auth_policy_version", "idempotency_key", name="uq_ad_v4_app_request_idempotency"),
    )

    op.create_table(
        "ad_v4_candidate_app_semantic_nodes",
        _id("id", primary=True), sa.Column("identity_hash", sa.String(64), nullable=False, unique=True),
        _id("projection_id"), _id("proposal_id"), sa.Column("parent_node_id", sa.String(36), nullable=True),
        sa.Column("node_type", sa.String(64), nullable=False), sa.Column("node_key", sa.String(255), nullable=False),
        sa.Column("source_pointer", sa.Text(), nullable=False), sa.Column("canonical_node_hash", sa.String(64), nullable=False),
        sa.Column("canonical_ordinal", sa.Integer(), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["projection_id"], ["ad_v4_candidate_app_projections.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["proposal_id"], ["ad_v4_candidate_proposals.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["projection_id", "proposal_id"], ["ad_v4_candidate_app_projections.id", "ad_v4_candidate_app_projections.proposal_id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["parent_node_id"], ["ad_v4_candidate_app_semantic_nodes.id"], ondelete="RESTRICT"),
        sa.UniqueConstraint("id", "projection_id", "proposal_id", name="uq_ad_v4_app_node_parent_identity"),
        sa.UniqueConstraint("projection_id", "node_type", "node_key", name="uq_ad_v4_app_node_key"),
    )
    op.create_index("ix_ad_v4_app_node_reconstruct", "ad_v4_candidate_app_semantic_nodes", ["projection_id", "node_type", "node_key"])

    op.create_table(
        "ad_v4_candidate_app_data",
        _id("id", primary=True), _id("projection_id"), _id("proposal_id"),
        sa.Column("semantic_node_id", sa.String(36), nullable=True), sa.Column("json_pointer", sa.Text(), nullable=False),
        sa.Column("parent_pointer", sa.Text(), nullable=True), sa.Column("property_name", sa.String(255), nullable=True),
        sa.Column("array_ordinal", sa.Integer(), nullable=True), sa.Column("value_kind", sa.String(16), nullable=False),
        sa.Column("string_value", sa.Text(), nullable=True), sa.Column("boolean_value", sa.Boolean(), nullable=True),
        sa.Column("value_hash", sa.String(64), nullable=False),
        sa.ForeignKeyConstraint(["projection_id"], ["ad_v4_candidate_app_projections.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["proposal_id"], ["ad_v4_candidate_proposals.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["semantic_node_id"], ["ad_v4_candidate_app_semantic_nodes.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["projection_id", "proposal_id"], ["ad_v4_candidate_app_projections.id", "ad_v4_candidate_app_projections.proposal_id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["semantic_node_id", "projection_id", "proposal_id"], ["ad_v4_candidate_app_semantic_nodes.id", "ad_v4_candidate_app_semantic_nodes.projection_id", "ad_v4_candidate_app_semantic_nodes.proposal_id"], ondelete="RESTRICT"),
        sa.CheckConstraint("value_kind IN ('object','array','string','boolean')", name="ck_ad_v4_app_datum_kind"),
        sa.UniqueConstraint("projection_id", "json_pointer", name="uq_ad_v4_app_datum_pointer"),
    )
    op.create_index("ix_ad_v4_app_data_reconstruct", "ad_v4_candidate_app_data", ["projection_id"])

    op.create_table(
        "ad_v4_candidate_app_evidence_links",
        _id("id", primary=True), _id("projection_id"), _id("proposal_id"), _id("semantic_node_id"), _id("candidate_binding_id"),
        sa.Column("evidence_key", sa.String(128), nullable=False), sa.Column("purpose", sa.String(64), nullable=False),
        sa.Column("canonical_ordinal", sa.Integer(), nullable=False), sa.Column("link_hash", sa.String(64), nullable=False),
        sa.ForeignKeyConstraint(["projection_id"], ["ad_v4_candidate_app_projections.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["projection_id", "proposal_id"], ["ad_v4_candidate_app_projections.id", "ad_v4_candidate_app_projections.proposal_id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["proposal_id", "candidate_binding_id", "evidence_key"], ["ad_v4_candidate_evidence_bindings.proposal_id", "ad_v4_candidate_evidence_bindings.id", "ad_v4_candidate_evidence_bindings.evidence_key"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["semantic_node_id"], ["ad_v4_candidate_app_semantic_nodes.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["semantic_node_id", "projection_id", "proposal_id"], ["ad_v4_candidate_app_semantic_nodes.id", "ad_v4_candidate_app_semantic_nodes.projection_id", "ad_v4_candidate_app_semantic_nodes.proposal_id"], ondelete="RESTRICT"),
        sa.UniqueConstraint("semantic_node_id", "purpose", "evidence_key", name="uq_ad_v4_app_evidence_link"),
    )
    op.create_index("ix_ad_v4_app_evidence_reconstruct", "ad_v4_candidate_app_evidence_links", ["semantic_node_id", "purpose", "canonical_ordinal"])

    op.create_table(
        "ad_v4_candidate_app_identity_mappings",
        _id("id", primary=True), _id("projection_id"), _id("proposal_id"), _id("source_occurrence_node_id"), _id("evidence_parent_node_id"),
        sa.Column("identity_kind", sa.String(32), nullable=False), sa.Column("source_value", sa.Text(), nullable=False),
        sa.Column("normalization_origin", sa.String(64), nullable=False), sa.Column("normalized_state", sa.String(32), nullable=False),
        sa.Column("normalized_value", sa.Text(), nullable=True), sa.Column("reason", sa.String(64), nullable=True),
        sa.Column("temporal_scope", sa.String(64), nullable=True), sa.Column("normalization_namespace", sa.String(64), nullable=True),
        sa.Column("normalization_version", sa.String(64), nullable=True), sa.Column("review_state", sa.String(32), nullable=False),
        sa.Column("identity_hash", sa.String(64), nullable=False, unique=True),
        sa.ForeignKeyConstraint(["projection_id"], ["ad_v4_candidate_app_projections.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["proposal_id"], ["ad_v4_candidate_proposals.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["source_occurrence_node_id"], ["ad_v4_candidate_app_semantic_nodes.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["evidence_parent_node_id"], ["ad_v4_candidate_app_semantic_nodes.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["projection_id", "proposal_id"], ["ad_v4_candidate_app_projections.id", "ad_v4_candidate_app_projections.proposal_id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["source_occurrence_node_id", "projection_id", "proposal_id"], ["ad_v4_candidate_app_semantic_nodes.id", "ad_v4_candidate_app_semantic_nodes.projection_id", "ad_v4_candidate_app_semantic_nodes.proposal_id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["evidence_parent_node_id", "projection_id", "proposal_id"], ["ad_v4_candidate_app_semantic_nodes.id", "ad_v4_candidate_app_semantic_nodes.projection_id", "ad_v4_candidate_app_semantic_nodes.proposal_id"], ondelete="RESTRICT"),
        sa.CheckConstraint("review_state='unreviewed_candidate'", name="ck_ad_v4_app_identity_review"),
        sa.UniqueConstraint("projection_id", "identity_kind", "source_occurrence_node_id", name="uq_ad_v4_app_identity_occurrence"),
    )

    _create_correction_tables()
    _create_dependency_and_event_tables()
    _replace_v4_validation_functions()
    _install_projection_validation()
    _install_projection_audit_validation()
    _install_projection_completeness()
    _install_immutability()


def _create_correction_tables() -> None:
    op.create_table(
        "ad_v4_candidate_corrections", _id("id", primary=True), sa.Column("identity_hash", sa.String(64), nullable=False, unique=True),
        _id("proposal_id"), sa.Column("correction_key", sa.String(128), nullable=False), sa.Column("correction_type", sa.String(64), nullable=False),
        sa.Column("original_document_ref_key", sa.String(128), nullable=False), sa.Column("correcting_document_ref_key", sa.String(128), nullable=False),
        sa.Column("original_document_identity_hash", sa.String(64), nullable=False), sa.Column("correcting_document_identity_hash", sa.String(64), nullable=False),
        sa.Column("canonical_hash", sa.String(64), nullable=False), sa.Column("canonical_ordinal", sa.Integer(), nullable=False),
        sa.Column("foundation_version", sa.String(64), nullable=False), sa.Column("generation", sa.Integer(), nullable=False),
        sa.Column("expected_ref_count", sa.Integer(), nullable=False), sa.Column("expected_evidence_count", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["proposal_id"], ["ad_v4_candidate_proposals.id"], ondelete="RESTRICT"),
        sa.CheckConstraint("canonical_ordinal>=0", name="ck_ad_v4_correction_ordinal_nonnegative"),
        sa.UniqueConstraint("id", "proposal_id", name="uq_ad_v4_correction_parent_identity"),
        sa.UniqueConstraint("proposal_id", "correction_key", name="uq_ad_v4_correction_key"),
        sa.UniqueConstraint("proposal_id", "canonical_ordinal", name="uq_ad_v4_correction_ordinal"),
    )
    op.create_table(
        "ad_v4_candidate_correction_refs", _id("id", primary=True), _id("correction_id"), _id("proposal_id"),
        sa.Column("canonical_ordinal", sa.Integer(), nullable=False), sa.Column("namespace", sa.String(64), nullable=False),
        sa.Column("semantic_key", sa.String(128), nullable=False), sa.Column("owner_slice", sa.String(32), nullable=False),
        sa.Column("reference_hash", sa.String(64), nullable=False),
        sa.ForeignKeyConstraint(["correction_id"], ["ad_v4_candidate_corrections.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["correction_id", "proposal_id"], ["ad_v4_candidate_corrections.id", "ad_v4_candidate_corrections.proposal_id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["proposal_id"], ["ad_v4_candidate_proposals.id"], ondelete="RESTRICT"),
        sa.CheckConstraint("canonical_ordinal>=0", name="ck_ad_v4_correction_ref_ordinal_nonnegative"),
        sa.UniqueConstraint("id", "proposal_id", name="uq_ad_v4_correction_ref_parent_identity"),
        sa.UniqueConstraint("correction_id", "namespace", "semantic_key", name="uq_ad_v4_correction_ref_key"),
        sa.UniqueConstraint("correction_id", "canonical_ordinal", name="uq_ad_v4_correction_ref_ordinal"),
    )
    op.create_table(
        "ad_v4_candidate_correction_semantic_bindings", _id("id", primary=True), _id("correction_ref_id"), _id("proposal_id"), _id("projection_id"), _id("semantic_node_id"),
        sa.Column("binding_slice", sa.String(32), nullable=False), sa.Column("generation", sa.Integer(), nullable=False), sa.Column("binding_hash", sa.String(64), nullable=False, unique=True),
        sa.ForeignKeyConstraint(["correction_ref_id"], ["ad_v4_candidate_correction_refs.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["correction_ref_id", "proposal_id"], ["ad_v4_candidate_correction_refs.id", "ad_v4_candidate_correction_refs.proposal_id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["proposal_id"], ["ad_v4_candidate_proposals.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["projection_id"], ["ad_v4_candidate_app_projections.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["semantic_node_id"], ["ad_v4_candidate_app_semantic_nodes.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["projection_id", "proposal_id"], ["ad_v4_candidate_app_projections.id", "ad_v4_candidate_app_projections.proposal_id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["semantic_node_id", "projection_id", "proposal_id"], ["ad_v4_candidate_app_semantic_nodes.id", "ad_v4_candidate_app_semantic_nodes.projection_id", "ad_v4_candidate_app_semantic_nodes.proposal_id"], ondelete="RESTRICT"),
        sa.UniqueConstraint("correction_ref_id", name="uq_ad_v4_correction_semantic_ref"),
    )
    op.create_table(
        "ad_v4_candidate_correction_evidence_links", _id("id", primary=True), _id("correction_id"), _id("proposal_id"), _id("candidate_binding_id"),
        sa.Column("evidence_key", sa.String(128), nullable=False), sa.Column("canonical_ordinal", sa.Integer(), nullable=False), sa.Column("link_hash", sa.String(64), nullable=False),
        sa.ForeignKeyConstraint(["correction_id"], ["ad_v4_candidate_corrections.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["correction_id", "proposal_id"], ["ad_v4_candidate_corrections.id", "ad_v4_candidate_corrections.proposal_id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["proposal_id", "candidate_binding_id", "evidence_key"], ["ad_v4_candidate_evidence_bindings.proposal_id", "ad_v4_candidate_evidence_bindings.id", "ad_v4_candidate_evidence_bindings.evidence_key"], ondelete="RESTRICT"),
        sa.CheckConstraint("canonical_ordinal>=0", name="ck_ad_v4_correction_evidence_ordinal_nonnegative"),
        sa.UniqueConstraint("correction_id", "evidence_key", name="uq_ad_v4_correction_evidence"),
        sa.UniqueConstraint("correction_id", "canonical_ordinal", name="uq_ad_v4_correction_evidence_ordinal"),
    )


def _create_dependency_and_event_tables() -> None:
    op.create_table(
        "ad_v4_candidate_app_change_dependencies", _id("id", primary=True), _id("projection_id"), _id("proposal_id"), _id("semantic_node_id"),
        sa.Column("dependency_key", sa.String(255), nullable=False), sa.Column("dependency_kind", sa.String(64), nullable=False),
        sa.Column("predecessor_ad_number", sa.String(64), nullable=False), sa.Column("successor_ad_number", sa.String(64), nullable=False),
        sa.Column("resolution_state", sa.String(32), nullable=False), sa.Column("unresolved_reason", sa.String(64), nullable=True),
        sa.Column("target_projection_id", sa.String(36), nullable=True), sa.Column("source_dependency_id", sa.String(36), nullable=True),
        sa.Column("dependency_hash", sa.String(64), nullable=False, unique=True),
        sa.ForeignKeyConstraint(["projection_id"], ["ad_v4_candidate_app_projections.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["proposal_id"], ["ad_v4_candidate_proposals.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["projection_id", "proposal_id"], ["ad_v4_candidate_app_projections.id", "ad_v4_candidate_app_projections.proposal_id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["semantic_node_id"], ["ad_v4_candidate_app_semantic_nodes.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["semantic_node_id", "projection_id", "proposal_id"], ["ad_v4_candidate_app_semantic_nodes.id", "ad_v4_candidate_app_semantic_nodes.projection_id", "ad_v4_candidate_app_semantic_nodes.proposal_id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["target_projection_id"], ["ad_v4_candidate_app_projections.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["source_dependency_id"], ["ad_v4_candidate_app_change_dependencies.id"], ondelete="RESTRICT"),
        sa.CheckConstraint("dependency_kind IN ('outgoing_supersedes','outgoing_partially_supersedes','incoming_supersession_signal')", name="ck_ad_v4_app_dependency_kind"),
        sa.UniqueConstraint("id", "projection_id", name="uq_ad_v4_app_dependency_parent_identity"),
        sa.UniqueConstraint("projection_id", "dependency_key", name="uq_ad_v4_app_dependency"),
    )
    op.create_table(
        "ad_v4_candidate_app_projection_events", _id("id", primary=True), _id("projection_id"), _id("proposal_id"),
        sa.Column("sequence_number", sa.Integer(), nullable=False), sa.Column("event_type", sa.String(64), nullable=False),
        sa.Column("reason_code", sa.String(64), nullable=False), sa.Column("causing_request_id", sa.String(36), nullable=True),
        sa.Column("causing_relationship_id", sa.String(36), nullable=True), sa.Column("causing_lifecycle_event_id", sa.String(36), nullable=True),
        sa.Column("causing_dependency_id", sa.String(36), nullable=True), sa.Column("predecessor_event_hash", sa.String(64), nullable=True),
        sa.Column("canonical_bytes", sa.LargeBinary(), nullable=False), sa.Column("event_hash", sa.String(64), nullable=False),
        sa.Column("actor_kind", sa.String(32), nullable=False), sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["projection_id"], ["ad_v4_candidate_app_projections.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["proposal_id"], ["ad_v4_candidate_proposals.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["projection_id", "proposal_id"], ["ad_v4_candidate_app_projections.id", "ad_v4_candidate_app_projections.proposal_id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["causing_request_id"], ["ad_v4_candidate_app_materialization_requests.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["causing_relationship_id"], ["ad_v4_candidate_submission_relationships.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["causing_lifecycle_event_id"], ["ad_evidence_fragment_lifecycle_events.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["causing_dependency_id"], ["ad_v4_candidate_app_change_dependencies.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["causing_dependency_id", "projection_id"], ["ad_v4_candidate_app_change_dependencies.id", "ad_v4_candidate_app_change_dependencies.projection_id"], ondelete="RESTRICT", name="fk_ad_v4_app_event_same_projection_dependency"),
        sa.UniqueConstraint("projection_id", "sequence_number", name="uq_ad_v4_app_event_sequence"),
        sa.UniqueConstraint("projection_id", "event_hash", name="uq_ad_v4_app_event_hash"),
    )
    op.create_index("ix_ad_v4_app_event_fold", "ad_v4_candidate_app_projection_events", ["projection_id", "sequence_number"])
    op.create_index("uq_ad_v4_app_event_dependency_cause", "ad_v4_candidate_app_projection_events", ["projection_id", "event_type", "causing_dependency_id"], unique=True, postgresql_where=sa.text("causing_dependency_id IS NOT NULL"))
    op.create_index("uq_ad_v4_app_event_relationship_cause", "ad_v4_candidate_app_projection_events", ["projection_id", "event_type", "causing_relationship_id"], unique=True, postgresql_where=sa.text("causing_relationship_id IS NOT NULL"))
    op.create_index("uq_ad_v4_app_event_lifecycle_cause", "ad_v4_candidate_app_projection_events", ["projection_id", "event_type", "causing_lifecycle_event_id"], unique=True, postgresql_where=sa.text("causing_lifecycle_event_id IS NOT NULL"))


def _replace_v4_validation_functions() -> None:
    op.execute("""
    CREATE OR REPLACE FUNCTION paprnav_v4_capabilities() RETURNS jsonb AS $$
      SELECT jsonb_build_object(
        'revision','20260907_0027',
        'validatorPairs',jsonb_build_array(
          jsonb_build_array('paprnav-ad-v4-validator-1','paprnav-ad-v4-c14n-1'),
          jsonb_build_array('paprnav-ad-v4-validator-2','paprnav-ad-v4-c14n-2')),
        'materializers',jsonb_build_array('paprnav-ad-v4-app-materializer-2'),
        'validator2_write_enabled',(SELECT enabled FROM ad_v4_feature_gates WHERE gate_key='validator2_write_enabled'),
        'materializer3a_enabled',(SELECT enabled FROM ad_v4_feature_gates WHERE gate_key='materializer3a_enabled'));
    $$ LANGUAGE sql STABLE
    """)
    op.execute("""
    CREATE OR REPLACE FUNCTION paprnav_set_v4_feature_gate(p_key text,p_enabled boolean,p_actor text) RETURNS void AS $$
    BEGIN
      IF p_key NOT IN ('validator2_write_enabled','materializer3a_enabled') OR length(trim(p_actor))=0 THEN
        RAISE EXCEPTION 'invalid V4 feature gate change';
      END IF;
      UPDATE ad_v4_feature_gates SET enabled=p_enabled,changed_at=now(),changed_by=p_actor WHERE gate_key=p_key;
      IF NOT FOUND THEN RAISE EXCEPTION 'unknown V4 feature gate'; END IF;
    END; $$ LANGUAGE plpgsql
    """)
    op.execute("""
    CREATE OR REPLACE FUNCTION paprnav_v4_validate_proposal() RETURNS trigger AS $$
    DECLARE domain text;
    BEGIN
      IF (NEW.validator_version,NEW.canonicalization_version) NOT IN (
        ('paprnav-ad-v4-validator-1','paprnav-ad-v4-c14n-1'),
        ('paprnav-ad-v4-validator-2','paprnav-ad-v4-c14n-2')) THEN
        RAISE EXCEPTION 'V4 unsupported validator/canonicalization pair';
      END IF;
      domain := CASE WHEN NEW.validator_version='paprnav-ad-v4-validator-2'
        THEN 'paprnav:ad_extraction_v4:proposal:paprnav-ad-v4-c14n-2'
        ELSE 'paprnav:ad_extraction_v4:proposal:paprnav-ad-v4-c14n-1' END;
      IF convert_from(NEW.canonical_bytes,'UTF8')::jsonb IS DISTINCT FROM NEW.parsed_json::jsonb
         OR NEW.canonical_hash<>encode(sha256(convert_to(domain,'UTF8')||decode('00','hex')||NEW.canonical_bytes),'hex')
         OR NEW.schema_version<>'ad_extraction_v4' OR NEW.gate<>'candidate_only'
         OR NEW.parsed_json::jsonb->>'schemaVersion'<>NEW.schema_version
         OR NEW.parsed_json::jsonb->'directiveIdentity'->>'directiveId'<>NEW.directive_id THEN
        RAISE EXCEPTION 'V4 proposal envelope/relational identity mismatch';
      END IF;
      RETURN NEW;
    END; $$ LANGUAGE plpgsql
    """)
    op.execute("""
    CREATE OR REPLACE FUNCTION paprnav_v4_validate_relationship() RETURNS trigger AS $$
    DECLARE s ad_v4_candidate_submissions%ROWTYPE; p ad_v4_candidate_proposals%ROWTYPE; pred ad_v4_candidate_proposals%ROWTYPE; payload jsonb; domain text; version text;
    BEGIN
      SELECT * INTO s FROM ad_v4_candidate_submissions WHERE id=NEW.submission_id;
      SELECT * INTO p FROM ad_v4_candidate_proposals WHERE id=s.proposal_id;
      SELECT * INTO pred FROM ad_v4_candidate_proposals WHERE id=NEW.predecessor_proposal_id;
      domain:=CASE WHEN NEW.validator_version='paprnav-ad-v4-validator-2' THEN 'paprnav:ad_extraction_v4:submission-relationship:2' ELSE 'paprnav:ad_extraction_v4:submission-relationship:1' END;
      version:=CASE WHEN NEW.validator_version='paprnav-ad-v4-validator-2' THEN 'ad-v4-submission-relationship-v2' ELSE 'ad-v4-submission-relationship-v1' END;
      payload:=convert_from(NEW.canonical_bytes,'UTF8')::jsonb;
      IF s.id IS NULL OR p.id IS NULL OR pred.id IS NULL OR p.directive_id<>pred.directive_id OR p.id=pred.id
         OR NEW.validator_version<>s.validator_version OR NEW.canonicalization_version<>s.canonicalization_version
         OR NEW.relationship_hash<>encode(sha256(convert_to(domain,'UTF8')||decode('00','hex')||NEW.canonical_bytes),'hex')
         OR payload->>'version'<>version OR payload->>'submissionId'<>NEW.submission_id
         OR payload->>'relationshipKey'<>NEW.relationship_key OR payload->>'relationType'<>NEW.relation_type
         OR payload->>'predecessorProposalId'<>NEW.predecessor_proposal_id THEN
        RAISE EXCEPTION 'V4 relationship envelope mismatch';
      END IF;
      IF NEW.validator_version='paprnav-ad-v4-validator-2' AND (payload->>'validatorVersion'<>NEW.validator_version OR payload->>'canonicalizationVersion'<>NEW.canonicalization_version) THEN
        RAISE EXCEPTION 'V4 relationship v2 version mismatch';
      END IF;
      RETURN NEW;
    END; $$ LANGUAGE plpgsql
    """)
    op.execute("""
    CREATE OR REPLACE FUNCTION paprnav_v4_validate_event() RETURNS trigger AS $$
    DECLARE p ad_v4_candidate_proposals%ROWTYPE; s ad_v4_candidate_submissions%ROWTYPE; payload jsonb; domain text; version text;
    BEGIN
      SELECT * INTO p FROM ad_v4_candidate_proposals WHERE id=NEW.proposal_id;
      SELECT * INTO s FROM ad_v4_candidate_submissions WHERE id=NEW.created_by_submission_id;
      domain:=CASE WHEN NEW.validator_version='paprnav-ad-v4-validator-2' THEN 'paprnav:ad_extraction_v4:candidate-event:2' ELSE 'paprnav:ad_extraction_v4:candidate-event:1' END;
      version:=CASE WHEN NEW.validator_version='paprnav-ad-v4-validator-2' THEN 'ad-v4-candidate-created-v2' ELSE 'ad-v4-candidate-created-v1' END;
      payload:=convert_from(NEW.canonical_bytes,'UTF8')::jsonb;
      IF p.id IS NULL OR s.id IS NULL OR s.proposal_id<>p.id OR NEW.directive_id<>p.directive_id
         OR NEW.validator_version<>p.validator_version OR NEW.canonicalization_version<>p.canonicalization_version
         OR NEW.validator_version<>s.validator_version OR NEW.canonicalization_version<>s.canonicalization_version
         OR NEW.proposal_canonical_hash<>p.canonical_hash OR NEW.evidence_binding_hash<>p.evidence_binding_hash
         OR NEW.event_hash<>encode(sha256(convert_to(domain,'UTF8')||decode('00','hex')||NEW.canonical_bytes),'hex')
         OR payload->>'version'<>version OR payload->>'proposalId'<>NEW.proposal_id OR payload->>'createdBySubmissionId'<>NEW.created_by_submission_id THEN
        RAISE EXCEPTION 'V4 event envelope mismatch';
      END IF;
      IF NEW.validator_version='paprnav-ad-v4-validator-2' AND (payload->>'validatorVersion'<>NEW.validator_version OR payload->>'canonicalizationVersion'<>NEW.canonicalization_version) THEN
        RAISE EXCEPTION 'V4 event v2 version mismatch';
      END IF;
      RETURN NEW;
    END; $$ LANGUAGE plpgsql
    """)
    op.execute("""
    CREATE OR REPLACE FUNCTION paprnav_v4_validate_binding() RETURNS trigger AS $$
    DECLARE p ad_v4_candidate_proposals%ROWTYPE; f ad_evidence_fragments%ROWTYPE; e ad_evidence_fragment_lifecycle_events%ROWTYPE; n integer; declared jsonb;
    BEGIN
      SELECT * INTO p FROM ad_v4_candidate_proposals WHERE id=NEW.proposal_id;
      SELECT * INTO f FROM ad_evidence_fragments WHERE id=NEW.fragment_id FOR UPDATE;
      SELECT count(*) INTO n FROM ad_evidence_fragment_lifecycle_events WHERE fragment_id=NEW.fragment_id;
      SELECT * INTO e FROM ad_evidence_fragment_lifecycle_events WHERE id=NEW.admitted_event_id AND fragment_id=NEW.fragment_id;
      declared:=p.parsed_json::jsonb->'evidenceBindings'->NEW.evidence_key;
      IF p.id IS NULL OR NEW.validator_version<>p.validator_version OR NEW.canonicalization_version<>p.canonicalization_version
         OR f.id IS NULL OR f.directive_id<>NEW.directive_id OR f.fragment_hash<>NEW.fragment_hash
         OR n<>1 OR e.event_type<>'admitted' OR e.sequence_number<>0 OR e.predecessor_event_hash IS NOT NULL OR e.event_hash<>NEW.admitted_event_hash
         OR p.directive_id<>NEW.directive_id OR declared IS NULL OR declared->>'fragmentId'<>NEW.fragment_id OR declared->>'fragmentHash'<>NEW.fragment_hash THEN
        RAISE EXCEPTION 'V4 evidence binding mismatch';
      END IF;
      RETURN NEW;
    END; $$ LANGUAGE plpgsql
    """)
    op.execute("""
    CREATE OR REPLACE FUNCTION paprnav_v4_require_binding_parent_complete() RETURNS trigger AS $$
    DECLARE p ad_v4_candidate_proposals%ROWTYPE; expected jsonb; payload jsonb; version text;
    BEGIN
      SELECT * INTO p FROM ad_v4_candidate_proposals WHERE id=NEW.proposal_id;
      SELECT coalesce(jsonb_agg(jsonb_build_object('evidenceKey',b.evidence_key,'fragmentId',b.fragment_id,'fragmentHash',b.fragment_hash,'admittedEventId',b.admitted_event_id,'admittedEventHash',b.admitted_event_hash) ORDER BY b.evidence_key),'[]'::jsonb)
        INTO expected FROM ad_v4_candidate_evidence_bindings b WHERE b.proposal_id=NEW.proposal_id;
      payload:=convert_from(p.evidence_binding_bytes,'UTF8')::jsonb;
      version:=CASE WHEN p.validator_version='paprnav-ad-v4-validator-2' THEN 'ad-v4-evidence-bindings-v2' ELSE 'ad-v4-evidence-bindings-v1' END;
      IF p.id IS NULL OR payload->>'version'<>version OR payload->'bindings'<>expected
         OR (SELECT count(*) FROM ad_v4_candidate_evidence_bindings WHERE proposal_id=p.id)<>p.binding_count
         OR (p.validator_version='paprnav-ad-v4-validator-2' AND (payload->>'validatorVersion'<>p.validator_version OR payload->>'canonicalizationVersion'<>p.canonicalization_version)) THEN
        RAISE EXCEPTION 'V4 proposal binding set is incomplete';
      END IF;
      RETURN NULL;
    END; $$ LANGUAGE plpgsql
    """)
    op.execute("""
    CREATE OR REPLACE FUNCTION paprnav_v4_validate_submission() RETURNS trigger AS $$
    DECLARE p ad_v4_candidate_proposals%ROWTYPE; m organization_memberships%ROWTYPE; u users%ROWTYPE; payload jsonb; domain text; version text;
    BEGIN
      SELECT * INTO p FROM ad_v4_candidate_proposals WHERE id=NEW.proposal_id;
      SELECT * INTO m FROM organization_memberships WHERE id=NEW.authorizing_membership_id FOR UPDATE;
      SELECT * INTO u FROM users WHERE id=NEW.actor_user_id FOR UPDATE;
      domain:=CASE WHEN NEW.validator_version='paprnav-ad-v4-validator-2' THEN 'paprnav:ad_extraction_v4:submission:2' ELSE 'paprnav:ad_extraction_v4:submission:1' END;
      version:=CASE WHEN NEW.validator_version='paprnav-ad-v4-validator-2' THEN 'ad-v4-submission-v2' ELSE 'ad-v4-submission-v1' END;
      payload:=convert_from(NEW.request_canonical_bytes,'UTF8')::jsonb;
      IF p.id IS NULL OR NEW.validator_version<>p.validator_version OR NEW.canonicalization_version<>p.canonicalization_version
         OR m.id IS NULL OR u.id IS NULL OR u.status<>'active' OR m.user_id<>NEW.actor_user_id OR m.organization_id<>NEW.organization_id
         OR m.role<>'platform_admin' OR m.status<>'active' OR NEW.actor_role<>m.role OR NEW.actor_status<>m.status
         OR p.directive_id<>NEW.directive_id OR payload->>'version'<>version OR payload->>'proposalCanonicalHash'<>p.canonical_hash
         OR NEW.request_hash<>encode(sha256(convert_to(domain,'UTF8')||decode('00','hex')||NEW.request_canonical_bytes),'hex') THEN
        RAISE EXCEPTION 'V4 submission authorization/envelope mismatch';
      END IF;
      IF NEW.validator_version='paprnav-ad-v4-validator-2' AND (payload->>'validatorVersion'<>NEW.validator_version OR payload->>'canonicalizationVersion'<>NEW.canonicalization_version) THEN
        RAISE EXCEPTION 'V4 submission v2 version envelope mismatch';
      END IF;
      RETURN NEW;
    END; $$ LANGUAGE plpgsql
    """)
    op.execute("""
    CREATE OR REPLACE FUNCTION paprnav_v4_require_complete_proposal() RETURNS trigger AS $$
    DECLARE expected jsonb; payload jsonb; version text;
    BEGIN
      SELECT coalesce(jsonb_agg(jsonb_build_object('evidenceKey',b.evidence_key,'fragmentId',b.fragment_id,'fragmentHash',b.fragment_hash,'admittedEventId',b.admitted_event_id,'admittedEventHash',b.admitted_event_hash) ORDER BY b.evidence_key),'[]'::jsonb)
        INTO expected FROM ad_v4_candidate_evidence_bindings b WHERE b.proposal_id=NEW.id;
      payload:=convert_from(NEW.evidence_binding_bytes,'UTF8')::jsonb;
      version:=CASE WHEN NEW.validator_version='paprnav-ad-v4-validator-2' THEN 'ad-v4-evidence-bindings-v2' ELSE 'ad-v4-evidence-bindings-v1' END;
      IF (SELECT count(*) FROM ad_v4_candidate_evidence_bindings WHERE proposal_id=NEW.id)<>NEW.binding_count
         OR (SELECT count(*) FROM ad_v4_candidate_proposal_events WHERE proposal_id=NEW.id AND event_type='candidate_created')<>1
         OR payload->>'version'<>version OR payload->'bindings'<>expected
         OR (NEW.validator_version='paprnav-ad-v4-validator-2' AND (payload->>'validatorVersion'<>NEW.validator_version OR payload->>'canonicalizationVersion'<>NEW.canonicalization_version)) THEN
        RAISE EXCEPTION 'V4 proposal is incomplete';
      END IF;
      RETURN NULL;
    END; $$ LANGUAGE plpgsql
    """)


def _install_immutability() -> None:
    for table in APP_TABLES:
        if table == "ad_v4_feature_gates":
            continue
        op.execute(f"CREATE TRIGGER trg_{table}_immutable BEFORE UPDATE OR DELETE ON {table} FOR EACH ROW EXECUTE FUNCTION paprnav_v4_reject_mutation()")


def _install_projection_validation() -> None:
    op.execute(r"""
    CREATE FUNCTION paprnav_v4_lock_app_ad_numbers(p_proposal_id text) RETURNS void AS $$
    DECLARE ad_number text;
    BEGIN
      FOR ad_number IN
        SELECT DISTINCT value FROM (
          SELECT p.parsed_json::jsonb->'directiveIdentity'->'adNumber'->>'value' AS value
            FROM ad_v4_candidate_proposals p WHERE p.id=p_proposal_id
          UNION ALL
          SELECT relation->>'predecessorAdNumber'
            FROM ad_v4_candidate_proposals p,
                 jsonb_array_elements(p.parsed_json::jsonb->'supersessionRelations') relation
           WHERE p.id=p_proposal_id
          UNION ALL
          SELECT relation->>'successorAdNumber'
            FROM ad_v4_candidate_proposals p,
                 jsonb_array_elements(p.parsed_json::jsonb->'supersessionRelations') relation
           WHERE p.id=p_proposal_id
        ) numbers WHERE value IS NOT NULL ORDER BY value
      LOOP
        PERFORM pg_advisory_xact_lock(
          (('x'||substr(encode(sha256(
            convert_to('applicability-ad-resolution:'||ad_number,'UTF8')
          ),'hex'),1,16))::bit(64))::bigint
        );
      END LOOP;
    END; $$ LANGUAGE plpgsql
    """)
    op.execute("""
    CREATE FUNCTION paprnav_v4_validate_app_projection() RETURNS trigger AS $$
    DECLARE p ad_v4_candidate_proposals%ROWTYPE; subtree jsonb; envelope jsonb;
    BEGIN
      PERFORM paprnav_v4_lock_app_ad_numbers(NEW.proposal_id);
      SELECT * INTO p FROM ad_v4_candidate_proposals WHERE id=NEW.proposal_id FOR SHARE;
      subtree:=convert_from(NEW.applicability_subtree_bytes,'UTF8')::jsonb;
      envelope:=convert_from(NEW.projection_canonical_bytes,'UTF8')::jsonb;
      IF p.id IS NULL OR p.directive_id<>NEW.directive_id
         OR p.validator_version<>NEW.validator_version OR p.canonicalization_version<>NEW.canonicalization_version
         OR p.canonical_hash<>NEW.proposal_canonical_hash OR p.evidence_binding_hash<>NEW.evidence_binding_hash
         OR NEW.validator_version<>'paprnav-ad-v4-validator-2' OR NEW.canonicalization_version<>'paprnav-ad-v4-c14n-2'
         OR NEW.materializer_version<>'paprnav-ad-v4-app-materializer-2' OR NEW.gate<>'candidate_only'
         OR subtree IS DISTINCT FROM jsonb_build_object(
              'productScopes',p.parsed_json::jsonb->'productScopes',
              'conditionDefinitions',p.parsed_json::jsonb->'conditionDefinitions',
              'applicabilityRules',p.parsed_json::jsonb->'applicabilityRules',
              'applicabilitySearchHints',p.parsed_json::jsonb->'applicabilitySearchHints')
         OR NEW.applicability_subtree_hash<>encode(sha256(
              convert_to('paprnav:ad_extraction_v4:applicability-subtree:paprnav-ad-v4-c14n-2','UTF8')||decode('00','hex')||NEW.applicability_subtree_bytes),'hex')
         OR NEW.projection_hash<>encode(sha256(
              convert_to('paprnav:ad_extraction_v4:applicability-projection:2','UTF8')||decode('00','hex')||NEW.projection_canonical_bytes),'hex')
         OR envelope->>'version'<>'ad-v4-applicability-projection-v2'
         OR envelope->>'proposalId'<>NEW.proposal_id
         OR envelope->>'proposalCanonicalHash'<>NEW.proposal_canonical_hash
         OR envelope->>'evidenceBindingHash'<>NEW.evidence_binding_hash
         OR envelope->>'validatorVersion'<>NEW.validator_version
         OR envelope->>'canonicalizationVersion'<>NEW.canonicalization_version
         OR envelope->>'materializerVersion'<>NEW.materializer_version
         OR envelope->>'applicabilitySubtreeHash'<>NEW.applicability_subtree_hash THEN
        RAISE EXCEPTION 'V4 applicability projection envelope mismatch';
      END IF;
      RETURN NEW;
    END; $$ LANGUAGE plpgsql
    """)
    op.execute("CREATE TRIGGER trg_ad_v4_candidate_app_projections_validate BEFORE INSERT ON ad_v4_candidate_app_projections FOR EACH ROW EXECUTE FUNCTION paprnav_v4_validate_app_projection()")


def _install_projection_audit_validation() -> None:
    op.execute("""
    CREATE FUNCTION paprnav_v4_validate_app_request() RETURNS trigger AS $$
    DECLARE p ad_v4_candidate_app_projections%ROWTYPE; m organization_memberships%ROWTYPE; u users%ROWTYPE; payload jsonb;
    BEGIN
      SELECT * INTO p FROM ad_v4_candidate_app_projections WHERE id=NEW.projection_id;
      SELECT * INTO m FROM organization_memberships WHERE id=NEW.authorizing_membership_id FOR SHARE;
      SELECT * INTO u FROM users WHERE id=NEW.actor_user_id FOR SHARE;
      payload:=convert_from(NEW.request_canonical_bytes,'UTF8')::jsonb;
      IF p.id IS NULL OR p.proposal_id<>NEW.proposal_id OR p.directive_id<>NEW.directive_id
         OR m.id IS NULL OR u.id IS NULL OR u.status<>'active'
         OR m.user_id<>NEW.actor_user_id OR m.organization_id<>NEW.organization_id
         OR m.role<>'platform_admin' OR m.status<>'active'
         OR NEW.actor_role<>m.role OR NEW.actor_status<>m.status
         OR NEW.endpoint_action<>'materialize_ad_v4_applicability'
         OR payload->>'action'<>NEW.endpoint_action OR payload->>'directiveId'<>NEW.directive_id
         OR payload->>'proposalId'<>NEW.proposal_id
         OR payload->>'validatorVersion'<>p.validator_version
         OR payload->>'canonicalizationVersion'<>p.canonicalization_version
         OR payload->>'materializerVersion'<>p.materializer_version
         OR NEW.request_hash<>encode(sha256(
              convert_to('paprnav:ad_extraction_v4:applicability-row:2','UTF8')||decode('00','hex')||NEW.request_canonical_bytes),'hex') THEN
        RAISE EXCEPTION 'V4 applicability request authorization/envelope mismatch';
      END IF;
      RETURN NEW;
    END; $$ LANGUAGE plpgsql
    """)
    op.execute("CREATE TRIGGER trg_ad_v4_candidate_app_materialization_requests_validate BEFORE INSERT ON ad_v4_candidate_app_materialization_requests FOR EACH ROW EXECUTE FUNCTION paprnav_v4_validate_app_request()")
    op.execute("""
    CREATE FUNCTION paprnav_v4_validate_app_event() RETURNS trigger AS $$
    DECLARE p ad_v4_candidate_app_projections%ROWTYPE; previous ad_v4_candidate_app_projection_events%ROWTYPE; payload jsonb;
    BEGIN
      SELECT * INTO p FROM ad_v4_candidate_app_projections WHERE id=NEW.projection_id;
      payload:=convert_from(NEW.canonical_bytes,'UTF8')::jsonb;
      IF NEW.sequence_number>0 THEN
        SELECT * INTO previous FROM ad_v4_candidate_app_projection_events
         WHERE projection_id=NEW.projection_id AND sequence_number=NEW.sequence_number-1 FOR SHARE;
      END IF;
      IF p.id IS NULL OR p.proposal_id<>NEW.proposal_id
         OR payload->>'version'<>'ad-v4-applicability-event-v2'
         OR payload->>'eventType'<>NEW.event_type OR payload->>'projectionId'<>NEW.projection_id
         OR payload->>'proposalId'<>NEW.proposal_id OR (payload->>'sequence')::integer<>NEW.sequence_number
         OR NEW.event_hash<>encode(sha256(
              convert_to('paprnav:ad_extraction_v4:applicability-projection-event:2','UTF8')||decode('00','hex')||NEW.canonical_bytes),'hex')
         OR (NEW.sequence_number=0 AND (NEW.event_type<>'materialized' OR NEW.predecessor_event_hash IS NOT NULL
              OR NEW.causing_request_id IS NULL OR payload->>'requestId'<>NEW.causing_request_id
              OR num_nonnulls(NEW.causing_relationship_id,NEW.causing_lifecycle_event_id,NEW.causing_dependency_id)<>0))
         OR (NEW.sequence_number>0 AND (previous.id IS NULL OR previous.event_hash<>NEW.predecessor_event_hash OR payload->>'predecessorEventHash'<>NEW.predecessor_event_hash))
         OR (NEW.event_type='stale_marked' AND num_nonnulls(
              NEW.causing_relationship_id,NEW.causing_lifecycle_event_id,NEW.causing_dependency_id)<>1)
         OR (NEW.event_type='stale_marked' AND (NEW.causing_request_id IS NOT NULL OR NEW.actor_kind<>'system_repair'
              OR payload->'reasons' IS NULL OR jsonb_typeof(payload->'reasons')<>'array'
              OR NEW.reason_code<>CASE WHEN jsonb_array_length(payload->'reasons')=1
                   THEN payload->'reasons'->>0 ELSE 'multiple' END
              OR payload->'cause'->>'id'<>coalesce(NEW.causing_relationship_id,NEW.causing_dependency_id,NEW.causing_lifecycle_event_id)
              OR payload->'cause'->>'kind'<>CASE
                   WHEN NEW.causing_relationship_id IS NOT NULL THEN 'candidate_relationship'
                   WHEN NEW.causing_dependency_id IS NOT NULL THEN 'supersession_dependency'
                   ELSE 'evidence_lifecycle' END))
         OR (NEW.causing_dependency_id IS NOT NULL AND NOT EXISTS (
              SELECT 1 FROM ad_v4_candidate_app_change_dependencies d
               WHERE d.id=NEW.causing_dependency_id AND d.projection_id=NEW.projection_id
                 AND d.dependency_kind='incoming_supersession_signal'
                 AND d.resolution_state='resolved_candidate'))
         OR (NEW.event_type NOT IN ('materialized','stale_marked')) THEN
        RAISE EXCEPTION 'V4 applicability event chain/envelope mismatch';
      END IF;
      RETURN NEW;
    END; $$ LANGUAGE plpgsql
    """)
    op.execute("CREATE TRIGGER trg_ad_v4_candidate_app_projection_events_validate BEFORE INSERT ON ad_v4_candidate_app_projection_events FOR EACH ROW EXECUTE FUNCTION paprnav_v4_validate_app_event()")


def _install_projection_completeness() -> None:
    op.execute(r"""
    CREATE FUNCTION paprnav_v4_json_nodes(
      p_value jsonb, p_pointer text DEFAULT '', p_parent text DEFAULT NULL,
      p_property text DEFAULT NULL, p_ordinal integer DEFAULT NULL
    ) RETURNS TABLE(
      json_pointer text, parent_pointer text, property_name text,
      array_ordinal integer, value_kind text, string_value text,
      boolean_value boolean
    ) AS $$
    DECLARE child_key text; child_value jsonb; child_ordinal integer;
    BEGIN
      RETURN QUERY SELECT p_pointer,p_parent,p_property,p_ordinal,
        CASE jsonb_typeof(p_value)
          WHEN 'object' THEN 'object' WHEN 'array' THEN 'array'
          WHEN 'boolean' THEN 'boolean' ELSE 'string' END,
        CASE WHEN jsonb_typeof(p_value)='string' THEN p_value #>> '{}' ELSE NULL END,
        CASE WHEN jsonb_typeof(p_value)='boolean' THEN (p_value #>> '{}')::boolean ELSE NULL END;
      IF jsonb_typeof(p_value)='object' THEN
        FOR child_key,child_value IN SELECT key,value FROM jsonb_each(p_value) LOOP
          RETURN QUERY SELECT * FROM paprnav_v4_json_nodes(
            child_value,p_pointer||'/'||child_key,p_pointer,child_key,NULL);
        END LOOP;
      ELSIF jsonb_typeof(p_value)='array' THEN
        FOR child_value,child_ordinal IN
          SELECT value,(ordinality-1)::integer FROM jsonb_array_elements(p_value) WITH ORDINALITY
        LOOP
          RETURN QUERY SELECT * FROM paprnav_v4_json_nodes(
            child_value,p_pointer||'/'||child_ordinal::text,p_pointer,NULL,child_ordinal);
        END LOOP;
      END IF;
    END; $$ LANGUAGE plpgsql IMMUTABLE
    """)
    op.execute(r"""
    CREATE FUNCTION paprnav_v4_jcs(p_value jsonb) RETURNS text AS $$
    DECLARE result text;
    BEGIN
      CASE jsonb_typeof(p_value)
        WHEN 'object' THEN
          SELECT '{'||coalesce(string_agg(to_jsonb(key)::text||':'||paprnav_v4_jcs(value),',' ORDER BY key),'')||'}'
            INTO result FROM jsonb_each(p_value);
        WHEN 'array' THEN
          SELECT '['||coalesce(string_agg(paprnav_v4_jcs(value),',' ORDER BY ordinality),'')||']'
            INTO result FROM jsonb_array_elements(p_value) WITH ORDINALITY;
        ELSE result:=p_value::text;
      END CASE;
      RETURN result;
    END; $$ LANGUAGE plpgsql IMMUTABLE STRICT
    """)
    op.execute(r"""
    CREATE FUNCTION paprnav_v4_pointer_value(p_root jsonb,p_pointer text) RETURNS jsonb AS $$
    DECLARE result jsonb:=p_root; token text;
    BEGIN
      IF p_pointer='' THEN RETURN result; END IF;
      FOREACH token IN ARRAY string_to_array(trim(leading '/' FROM p_pointer),'/') LOOP
        IF jsonb_typeof(result)='array' THEN result:=result->token::integer;
        ELSE result:=result->token;
        END IF;
        IF result IS NULL THEN RETURN NULL; END IF;
      END LOOP;
      RETURN result;
    END; $$ LANGUAGE plpgsql IMMUTABLE STRICT
    """)
    op.execute(r"""
    CREATE FUNCTION paprnav_v4_candidate_app_require_complete(p_projection_id text) RETURNS void AS $$
    DECLARE
      projection ad_v4_candidate_app_projections%ROWTYPE;
      proposal ad_v4_candidate_proposals%ROWTYPE;
      subtree jsonb; envelope jsonb; correction record; expected_correction jsonb;
      actual_refs jsonb; actual_evidence jsonb; original_document jsonb; correcting_document jsonb;
      expected_hash text; expected_identity text; node record; node_value jsonb; node_root jsonb;
      expected_node_type text; expected_node_key text; expected_parent text;
      expected_ordinal integer; expected_node_count integer; matching_targets integer;
      relation jsonb; expected_target_id text;
    BEGIN
      SELECT * INTO projection FROM ad_v4_candidate_app_projections WHERE id=p_projection_id FOR SHARE;
      IF projection.id IS NULL THEN RAISE EXCEPTION 'V4 applicability projection is missing'; END IF;
      SELECT * INTO proposal FROM ad_v4_candidate_proposals WHERE id=projection.proposal_id FOR SHARE;
      PERFORM paprnav_v4_lock_app_ad_numbers(proposal.id);
      subtree:=jsonb_build_object(
        'productScopes',proposal.parsed_json::jsonb->'productScopes',
        'conditionDefinitions',proposal.parsed_json::jsonb->'conditionDefinitions',
        'applicabilityRules',proposal.parsed_json::jsonb->'applicabilityRules',
        'applicabilitySearchHints',proposal.parsed_json::jsonb->'applicabilitySearchHints');
      envelope:=convert_from(projection.projection_canonical_bytes,'UTF8')::jsonb;

      IF (SELECT count(*) FROM ad_v4_candidate_app_data WHERE projection_id=projection.id)<>projection.datum_count
         OR (SELECT count(*) FROM ad_v4_candidate_app_semantic_nodes WHERE projection_id=projection.id AND source_pointer NOT LIKE '/incomingSupersessionSignals/%')<>projection.semantic_node_count
         OR (SELECT count(*) FROM ad_v4_candidate_app_evidence_links WHERE projection_id=projection.id)<>projection.evidence_link_count
         OR (SELECT count(*) FROM ad_v4_candidate_app_identity_mappings WHERE projection_id=projection.id)<>projection.identity_mapping_count
         OR (SELECT count(*) FROM ad_v4_candidate_app_projection_events WHERE projection_id=projection.id AND event_type='materialized')<>1
         OR EXISTS (
           WITH expected AS (SELECT * FROM paprnav_v4_json_nodes(subtree)),
           actual AS (SELECT * FROM ad_v4_candidate_app_data WHERE projection_id=projection.id)
           SELECT 1 FROM expected e FULL JOIN actual a USING (json_pointer)
            WHERE e.json_pointer IS NULL OR a.json_pointer IS NULL
               OR e.parent_pointer IS DISTINCT FROM a.parent_pointer
               OR e.property_name IS DISTINCT FROM a.property_name
               OR e.array_ordinal IS DISTINCT FROM a.array_ordinal
               OR e.value_kind IS DISTINCT FROM a.value_kind
               OR e.string_value IS DISTINCT FROM a.string_value
               OR e.boolean_value IS DISTINCT FROM a.boolean_value)
         OR envelope->'semanticNodeHashes' IS DISTINCT FROM (
           SELECT coalesce(jsonb_agg(identity_hash ORDER BY identity_hash),'[]'::jsonb)
             FROM ad_v4_candidate_app_semantic_nodes WHERE projection_id=projection.id AND source_pointer NOT LIKE '/incomingSupersessionSignals/%')
         OR envelope->'evidenceLinkHashes' IS DISTINCT FROM (
           SELECT coalesce(jsonb_agg(link_hash ORDER BY link_hash),'[]'::jsonb)
             FROM ad_v4_candidate_app_evidence_links WHERE projection_id=projection.id)
      THEN RAISE EXCEPTION 'V4 applicability relational graph is incomplete or differs from candidate'; END IF;

      SELECT count(*) INTO expected_node_count FROM paprnav_v4_json_nodes(subtree) walked
       WHERE jsonb_typeof(paprnav_v4_pointer_value(subtree,walked.json_pointer))='object'
         AND (
           paprnav_v4_pointer_value(subtree,walked.json_pointer) ? 'nodeType'
           OR paprnav_v4_pointer_value(subtree,walked.json_pointer) ? 'scopeKey'
           OR paprnav_v4_pointer_value(subtree,walked.json_pointer) ? 'conditionKey'
           OR paprnav_v4_pointer_value(subtree,walked.json_pointer) ? 'ruleKey'
           OR paprnav_v4_pointer_value(subtree,walked.json_pointer) ? 'hintKey'
           OR paprnav_v4_pointer_value(subtree,walked.json_pointer) ? 'groupKey'
           OR paprnav_v4_pointer_value(subtree,walked.json_pointer) ? 'memberKey'
           OR ((paprnav_v4_pointer_value(subtree,walked.json_pointer) ? 'kind') AND
               walked.json_pointer ~ '/(modelScope|serialScope|partNumberScope)$'));
      expected_node_count:=expected_node_count+jsonb_array_length(proposal.parsed_json::jsonb->'supersessionRelations');
      SELECT expected_node_count+count(*) INTO expected_node_count
        FROM paprnav_v4_json_nodes(subtree) walked
       WHERE walked.json_pointer ~ '/(modelScope|serialScope|partNumberScope)/sourceDesignations/[0-9]+$'
         AND jsonb_typeof(paprnav_v4_pointer_value(subtree,walked.json_pointer))='string';
      IF expected_node_count<>(SELECT count(*) FROM ad_v4_candidate_app_semantic_nodes WHERE projection_id=projection.id AND source_pointer NOT LIKE '/incomingSupersessionSignals/%')
      THEN RAISE EXCEPTION 'V4 applicability semantic-node set is incomplete'; END IF;

      FOR node IN SELECT * FROM ad_v4_candidate_app_semantic_nodes WHERE projection_id=projection.id AND source_pointer NOT LIKE '/incomingSupersessionSignals/%' LOOP
        node_root:=CASE WHEN node.source_pointer LIKE '/supersessionRelations/%' THEN proposal.parsed_json::jsonb ELSE subtree END;
        node_value:=paprnav_v4_pointer_value(node_root,node.source_pointer);
        expected_node_type:=NULL; expected_node_key:=NULL;
        IF node.source_pointer LIKE '/supersessionRelations/%' THEN
          expected_node_type:='change_dependency';
          expected_node_key:=(node_value->>'relationType')||':'||(node_value->>'predecessorAdNumber');
        ELSIF node_value ? 'nodeType' THEN expected_node_type:='expression'; expected_node_key:=node.source_pointer;
        ELSIF node_value ? 'scopeKey' THEN expected_node_type:='product_scope'; expected_node_key:=node_value->>'scopeKey';
        ELSIF node_value ? 'conditionKey' THEN expected_node_type:='condition'; expected_node_key:=node_value->>'conditionKey';
        ELSIF node_value ? 'ruleKey' THEN expected_node_type:='applicability_rule'; expected_node_key:=node_value->>'ruleKey';
        ELSIF node_value ? 'hintKey' THEN expected_node_type:='search_hint'; expected_node_key:=node_value->>'hintKey';
        ELSIF node_value ? 'groupKey' THEN
          expected_node_type:=CASE WHEN node.source_pointer LIKE '%/manufacturerModelGroups/%' THEN 'search_hint_group' ELSE 'designation_group' END;
          expected_node_key:=node.source_pointer;
        ELSIF node_value ? 'memberKey' THEN
          expected_node_type:=CASE WHEN node.source_pointer LIKE '%/manufacturerModelGroups/%' THEN 'search_hint_model' ELSE 'designation_group_member' END;
          expected_node_key:=node.source_pointer;
        ELSIF node_value ? 'kind' AND node.source_pointer ~ '/(modelScope|serialScope|partNumberScope)$' THEN
          expected_node_type:='designation_scope'; expected_node_key:=node.source_pointer;
        ELSIF jsonb_typeof(node_value)='string' AND node.source_pointer ~ '/(modelScope|serialScope|partNumberScope)/sourceDesignations/[0-9]+$' THEN
          expected_node_type:='designation_value';
          SELECT parent.node_key||':'||regexp_replace(node.source_pointer,'^.*/','')
            INTO expected_node_key FROM ad_v4_candidate_app_semantic_nodes parent
           WHERE parent.projection_id=projection.id AND parent.node_type='designation_scope'
             AND node.source_pointer LIKE parent.source_pointer||'/%'
           ORDER BY length(parent.source_pointer) DESC LIMIT 1;
        END IF;
        SELECT id INTO expected_parent FROM ad_v4_candidate_app_semantic_nodes parent
         WHERE parent.projection_id=projection.id AND parent.id<>node.id
           AND node.source_pointer LIKE parent.source_pointer||'/%'
         ORDER BY length(parent.source_pointer) DESC LIMIT 1;
        expected_ordinal:=CASE WHEN regexp_replace(node.source_pointer,'^.*/','') ~ '^[0-9]+$'
          THEN regexp_replace(node.source_pointer,'^.*/','')::integer ELSE 0 END;
        expected_hash:=encode(sha256(convert_to(paprnav_v4_jcs(node_value),'UTF8')),'hex');
        expected_identity:=CASE WHEN expected_node_type='designation_value' THEN
          encode(sha256(
            convert_to('paprnav:ad_extraction_v4:applicability-row:2','UTF8')||decode('00','hex')||
            convert_to(paprnav_v4_jcs(jsonb_build_object(
              'table','designation-value','identity',jsonb_build_object(
                'projectionId',projection.id,'pointer',node.source_pointer,
                'value',node_value #>> '{}'))),'UTF8')),'hex')
        ELSE encode(sha256(
          convert_to('paprnav:ad_extraction_v4:applicability-row:2','UTF8')||decode('00','hex')||
          convert_to(paprnav_v4_jcs(jsonb_build_object(
            'table','semantic-node','identity',jsonb_build_object(
              'projectionId',projection.id,'nodeType',node.node_type,
              'nodeKey',node.node_key,'pointer',node.source_pointer))),'UTF8')),'hex') END;
        IF node_value IS NULL OR expected_node_type IS NULL
           OR node.node_type IS DISTINCT FROM expected_node_type
           OR node.node_key IS DISTINCT FROM expected_node_key
           OR node.parent_node_id IS DISTINCT FROM expected_parent
           OR node.canonical_ordinal IS DISTINCT FROM expected_ordinal
           OR node.canonical_node_hash IS DISTINCT FROM expected_hash
           OR node.identity_hash IS DISTINCT FROM expected_identity
        THEN RAISE EXCEPTION 'V4 applicability semantic node differs from candidate: id=% type=%/% key=%/% parent=%/% ordinal=%/% canonical=%/% identity=%/%',
          node.id,node.node_type,expected_node_type,node.node_key,expected_node_key,
          node.parent_node_id,expected_parent,node.canonical_ordinal,expected_ordinal,
          node.canonical_node_hash,expected_hash,node.identity_hash,expected_identity;
        END IF;
      END LOOP;

      IF EXISTS (
        SELECT 1 FROM ad_v4_candidate_app_data datum
         WHERE datum.projection_id=projection.id AND (
           datum.semantic_node_id IS DISTINCT FROM (
             SELECT owner.id FROM ad_v4_candidate_app_semantic_nodes owner
              WHERE owner.projection_id=projection.id
                AND (datum.json_pointer=owner.source_pointer OR datum.json_pointer LIKE owner.source_pointer||'/%')
              ORDER BY length(owner.source_pointer) DESC LIMIT 1)
           OR datum.value_hash<>encode(sha256(
             convert_to('paprnav:ad_extraction_v4:applicability-row:2','UTF8')||decode('00','hex')||
             convert_to(paprnav_v4_jcs(jsonb_build_object(
               'table','datum','identity',jsonb_build_object(
                 'projectionId',projection.id,'pointer',datum.json_pointer,
                 'kind',datum.value_kind,'value',CASE
                   WHEN datum.value_kind='string' THEN to_jsonb(datum.string_value)
                   WHEN datum.value_kind='boolean' THEN to_jsonb(datum.boolean_value)
                   ELSE to_jsonb(datum.value_kind) END))),'UTF8')),'hex'))
      ) THEN RAISE EXCEPTION 'V4 applicability datum ownership or identity differs'; END IF;

      IF EXISTS (
        SELECT 1 FROM ad_v4_candidate_app_semantic_nodes n
        LEFT JOIN ad_v4_candidate_app_change_dependencies incoming
          ON incoming.semantic_node_id=n.id AND incoming.projection_id=n.projection_id
        LEFT JOIN ad_v4_candidate_app_change_dependencies source
          ON source.id=incoming.source_dependency_id
        WHERE n.projection_id=projection.id AND n.source_pointer LIKE '/incomingSupersessionSignals/%'
          AND (incoming.id IS NULL OR source.id IS NULL
            OR n.node_type<>'change_dependency'
            OR n.node_key<>'incoming:'||source.id
            OR n.source_pointer<>'/incomingSupersessionSignals/'||source.id
            OR n.parent_node_id IS NOT NULL OR n.canonical_ordinal<>0
            OR incoming.dependency_kind<>'incoming_supersession_signal'
            OR incoming.resolution_state<>'resolved_candidate' OR incoming.unresolved_reason IS NOT NULL
            OR incoming.target_projection_id<>projection.id
            OR source.target_projection_id<>projection.id
            OR source.resolution_state<>'resolved_candidate'
            OR incoming.predecessor_ad_number<>source.predecessor_ad_number
            OR incoming.successor_ad_number<>source.successor_ad_number
            OR n.canonical_node_hash<>encode(sha256(convert_to(paprnav_v4_jcs(jsonb_build_object(
                 'sourceDependencyId',source.id,'targetProjectionId',projection.id)),'UTF8')),'hex')
            OR n.identity_hash<>encode(sha256(
                 convert_to('paprnav:ad_extraction_v4:applicability-row:2','UTF8')||decode('00','hex')||
                 convert_to(paprnav_v4_jcs(jsonb_build_object(
                   'table','semantic-node','identity',jsonb_build_object(
                     'projectionId',projection.id,'nodeType','change_dependency',
                     'nodeKey','incoming:'||source.id,
                     'pointer','/incomingSupersessionSignals/'||source.id))),'UTF8')),'hex'))
      ) THEN RAISE EXCEPTION 'V4 incoming supersession dependency differs'; END IF;

      IF (SELECT count(*) FROM ad_v4_candidate_app_change_dependencies d
           WHERE d.projection_id=projection.id
             AND d.dependency_kind IN ('outgoing_supersedes','outgoing_partially_supersedes'))
           <>jsonb_array_length(proposal.parsed_json::jsonb->'supersessionRelations')
      THEN RAISE EXCEPTION 'V4 outgoing supersession dependency count differs'; END IF;

      FOR node IN
        SELECT * FROM ad_v4_candidate_app_semantic_nodes
         WHERE projection_id=projection.id AND source_pointer LIKE '/supersessionRelations/%'
         ORDER BY canonical_ordinal
      LOOP
        relation:=paprnav_v4_pointer_value(proposal.parsed_json::jsonb,node.source_pointer);
        SELECT count(*),min(candidate_projection.id) INTO matching_targets,expected_target_id
          FROM ad_v4_candidate_app_projections candidate_projection
          JOIN ad_v4_candidate_proposals candidate_proposal
            ON candidate_proposal.id=candidate_projection.proposal_id
         WHERE candidate_projection.id<>projection.id
           AND candidate_proposal.parsed_json::jsonb->'directiveIdentity'->'adNumber'->>'state'='known'
           AND candidate_proposal.parsed_json::jsonb->'directiveIdentity'->'adNumber'->>'value'=relation->>'predecessorAdNumber';
        IF NOT EXISTS (
          SELECT 1 FROM ad_v4_candidate_app_change_dependencies d
           WHERE d.projection_id=projection.id AND d.proposal_id=proposal.id
             AND d.semantic_node_id=node.id
             AND d.dependency_key=(relation->>'relationType')||':'||(relation->>'predecessorAdNumber')
             AND d.dependency_kind=CASE WHEN relation->>'relationType'='supersedes'
                  THEN 'outgoing_supersedes' ELSE 'outgoing_partially_supersedes' END
             AND d.predecessor_ad_number=relation->>'predecessorAdNumber'
             AND d.successor_ad_number=relation->>'successorAdNumber'
             AND d.source_dependency_id IS NULL
             AND d.dependency_hash=encode(sha256(
               convert_to('paprnav:ad_extraction_v4:applicability-row:2','UTF8')||decode('00','hex')||
               convert_to(paprnav_v4_jcs(jsonb_build_object(
                 'table','change-dependency','identity',jsonb_build_object(
                   'projectionId',projection.id,
                   'dependencyKey',(relation->>'relationType')||':'||(relation->>'predecessorAdNumber'),
                   'predecessorAdNumber',relation->>'predecessorAdNumber',
                   'successorAdNumber',relation->>'successorAdNumber'))),'UTF8')),'hex')
             AND CASE
               WHEN proposal.parsed_json::jsonb->'directiveIdentity'->'adNumber'->>'state'<>'known'
                 THEN d.resolution_state='unresolved' AND d.unresolved_reason='successor_identity_unknown' AND d.target_projection_id IS NULL
               WHEN relation->>'successorAdNumber'<>proposal.parsed_json::jsonb->'directiveIdentity'->'adNumber'->>'value'
                 THEN d.resolution_state='unresolved' AND d.unresolved_reason='successor_not_this_proposal' AND d.target_projection_id IS NULL
               WHEN matching_targets=1
                 THEN d.resolution_state='resolved_candidate' AND d.unresolved_reason IS NULL AND d.target_projection_id=expected_target_id
               WHEN matching_targets>1
                 THEN d.resolution_state='ambiguous' AND d.unresolved_reason='multiple_predecessor_candidates' AND d.target_projection_id IS NULL
               ELSE d.resolution_state='unresolved' AND d.unresolved_reason='target_candidate_not_resolved' AND d.target_projection_id IS NULL
             END
        ) THEN RAISE EXCEPTION 'V4 outgoing supersession dependency differs'; END IF;
      END LOOP;

      IF EXISTS (
        SELECT 1 FROM ad_v4_candidate_app_change_dependencies source
         WHERE source.target_projection_id=projection.id
           AND source.dependency_kind IN ('outgoing_supersedes','outgoing_partially_supersedes')
           AND source.resolution_state='resolved_candidate'
           AND NOT EXISTS (
             SELECT 1 FROM ad_v4_candidate_app_change_dependencies incoming
              JOIN ad_v4_candidate_app_semantic_nodes n ON n.id=incoming.semantic_node_id
              WHERE incoming.source_dependency_id=source.id
                AND incoming.projection_id=projection.id
                AND incoming.proposal_id=projection.proposal_id
                AND incoming.dependency_key='incoming:'||source.id
                AND incoming.dependency_kind='incoming_supersession_signal'
                AND incoming.predecessor_ad_number=source.predecessor_ad_number
                AND incoming.successor_ad_number=source.successor_ad_number
                AND incoming.resolution_state='resolved_candidate'
                AND incoming.unresolved_reason IS NULL
                AND incoming.target_projection_id=projection.id
                AND incoming.dependency_hash=encode(sha256(
                  convert_to('paprnav:ad_extraction_v4:applicability-row:2','UTF8')||decode('00','hex')||
                  convert_to(paprnav_v4_jcs(jsonb_build_object(
                    'table','incoming-change-dependency','identity',jsonb_build_object(
                      'projectionId',projection.id,'sourceDependencyId',source.id))),'UTF8')),'hex')
                AND n.projection_id=projection.id AND n.proposal_id=projection.proposal_id
                AND n.node_type='change_dependency' AND n.node_key='incoming:'||source.id
           )
      ) THEN RAISE EXCEPTION 'V4 resolved supersession is missing its target-local cause'; END IF;

      IF proposal.parsed_json::jsonb->'directiveIdentity'->'adNumber'->>'state'='known'
         AND EXISTS (
           SELECT 1 FROM ad_v4_candidate_app_change_dependencies source
            WHERE source.resolution_state='resolved_candidate'
              AND source.dependency_kind IN ('outgoing_supersedes','outgoing_partially_supersedes')
              AND source.predecessor_ad_number=proposal.parsed_json::jsonb->'directiveIdentity'->'adNumber'->>'value'
              AND (SELECT count(*)
                     FROM ad_v4_candidate_app_projections candidate_projection
                     JOIN ad_v4_candidate_proposals candidate_proposal
                       ON candidate_proposal.id=candidate_projection.proposal_id
                    WHERE candidate_proposal.parsed_json::jsonb->'directiveIdentity'->'adNumber'->>'state'='known'
                      AND candidate_proposal.parsed_json::jsonb->'directiveIdentity'->'adNumber'->>'value'=source.predecessor_ad_number)<>1
         )
      THEN RAISE EXCEPTION 'V4 resolved supersession predecessor is no longer unique'; END IF;

      IF (SELECT count(*) FROM ad_v4_candidate_corrections WHERE proposal_id=proposal.id)
           <>jsonb_array_length(proposal.parsed_json::jsonb->'authoritativeCorrections')
      THEN RAISE EXCEPTION 'V4 correction foundation count differs'; END IF;

      FOR correction IN
        SELECT * FROM ad_v4_candidate_corrections WHERE proposal_id=proposal.id ORDER BY canonical_ordinal
      LOOP
        expected_correction:=proposal.parsed_json::jsonb->'authoritativeCorrections'->correction.canonical_ordinal;
        SELECT coalesce(jsonb_agg(jsonb_build_object('namespace',namespace,'key',semantic_key) ORDER BY canonical_ordinal),'[]'::jsonb)
          INTO actual_refs FROM ad_v4_candidate_correction_refs WHERE correction_id=correction.id;
        SELECT coalesce(jsonb_agg(evidence_key ORDER BY canonical_ordinal),'[]'::jsonb)
          INTO actual_evidence FROM ad_v4_candidate_correction_evidence_links WHERE correction_id=correction.id;
        SELECT value INTO original_document FROM jsonb_array_elements(proposal.parsed_json::jsonb->'officialDocuments')
          WHERE value->>'officialDocumentKey'=correction.original_document_ref_key;
        SELECT value INTO correcting_document FROM jsonb_array_elements(proposal.parsed_json::jsonb->'officialDocuments')
          WHERE value->>'officialDocumentKey'=correction.correcting_document_ref_key;
        expected_hash:=encode(sha256(convert_to(paprnav_v4_jcs(expected_correction),'UTF8')),'hex');
        IF expected_correction IS NULL OR original_document IS NULL OR correcting_document IS NULL
           OR correction.correction_key<>expected_correction->>'correctionKey'
           OR correction.correction_type<>expected_correction->>'correctionType'
           OR correction.original_document_ref_key<>expected_correction->>'originalDocumentRefKey'
           OR correction.correcting_document_ref_key<>expected_correction->>'correctingDocumentRefKey'
           OR correction.canonical_hash<>expected_hash
           OR correction.foundation_version<>'paprnav-ad-v4-correction-foundation-1'
           OR correction.generation<>1
           OR correction.expected_ref_count<>jsonb_array_length(expected_correction->'changedSemanticRefs')
           OR correction.expected_evidence_count<>jsonb_array_length(expected_correction->'evidenceKeys')
           OR actual_refs IS DISTINCT FROM expected_correction->'changedSemanticRefs'
           OR actual_evidence IS DISTINCT FROM expected_correction->'evidenceKeys'
           OR EXISTS (
             SELECT 1 FROM ad_v4_candidate_correction_refs r
              WHERE r.correction_id=correction.id
              HAVING count(*)>0 AND (min(r.canonical_ordinal)<>0 OR max(r.canonical_ordinal)<>count(*)-1))
           OR EXISTS (
             SELECT 1 FROM ad_v4_candidate_correction_evidence_links e
              WHERE e.correction_id=correction.id
              HAVING count(*)>0 AND (min(e.canonical_ordinal)<>0 OR max(e.canonical_ordinal)<>count(*)-1))
           OR correction.original_document_identity_hash<>encode(sha256(
                convert_to('paprnav:ad_extraction_v4:applicability-row:2','UTF8')||decode('00','hex')||
                convert_to(paprnav_v4_jcs(jsonb_build_object('officialDocument',original_document)),'UTF8')),'hex')
           OR correction.correcting_document_identity_hash<>encode(sha256(
                convert_to('paprnav:ad_extraction_v4:applicability-row:2','UTF8')||decode('00','hex')||
                convert_to(paprnav_v4_jcs(jsonb_build_object('officialDocument',correcting_document)),'UTF8')),'hex')
           OR EXISTS (
             SELECT 1 FROM ad_v4_candidate_correction_refs r
              WHERE r.correction_id=correction.id AND (
                r.reference_hash<>encode(sha256(
                  convert_to('paprnav:ad_extraction_v4:applicability-row:2','UTF8')||decode('00','hex')||
                  convert_to(paprnav_v4_jcs(jsonb_build_object(
                    'table','correction-ref','identity',jsonb_build_object(
                      'correctionId',correction.id,'namespace',r.namespace,'key',r.semantic_key))),'UTF8')),'hex')
                OR r.owner_slice<>CASE
                  WHEN r.namespace IN ('productScopes','conditionDefinitions','applicabilityRules') THEN 'slice_3a'
                  WHEN r.namespace IN ('directiveIdentity','supersessionRelations') THEN 'foundation'
                  ELSE 'slice_3b' END
                OR (r.owner_slice='slice_3a' AND (SELECT count(*) FROM ad_v4_candidate_correction_semantic_bindings b WHERE b.correction_ref_id=r.id)<>1)
                OR (r.owner_slice<>'slice_3a' AND EXISTS (SELECT 1 FROM ad_v4_candidate_correction_semantic_bindings b WHERE b.correction_ref_id=r.id))
                OR EXISTS (
                  SELECT 1 FROM ad_v4_candidate_correction_semantic_bindings b
                  JOIN ad_v4_candidate_app_semantic_nodes n ON n.id=b.semantic_node_id
                  WHERE b.correction_ref_id=r.id AND (
                    b.proposal_id<>proposal.id OR b.projection_id<>projection.id
                    OR b.binding_slice<>'slice_3a' OR b.generation<>1
                    OR n.projection_id<>projection.id
                    OR n.node_type<>CASE r.namespace WHEN 'productScopes' THEN 'product_scope' WHEN 'conditionDefinitions' THEN 'condition' ELSE 'applicability_rule' END
                    OR n.node_key<>r.semantic_key
                    OR b.binding_hash<>encode(sha256(
                      convert_to('paprnav:ad_extraction_v4:applicability-row:2','UTF8')||decode('00','hex')||
                      convert_to(paprnav_v4_jcs(jsonb_build_object(
                        'table','correction-binding','identity',jsonb_build_object('refId',r.id,'semanticId',n.id))),'UTF8')),'hex')))))
           OR EXISTS (
             SELECT 1 FROM ad_v4_candidate_correction_evidence_links e
             WHERE e.correction_id=correction.id AND (
               e.link_hash<>encode(sha256(
                 convert_to('paprnav:ad_extraction_v4:applicability-row:2','UTF8')||decode('00','hex')||
                 convert_to(paprnav_v4_jcs(jsonb_build_object(
                   'table','correction-evidence','identity',jsonb_build_object(
                     'correctionId',correction.id,'evidenceKey',e.evidence_key))),'UTF8')),'hex')))
        THEN RAISE EXCEPTION 'V4 correction foundation is incomplete or differs from candidate'; END IF;
      END LOOP;
    END; $$ LANGUAGE plpgsql
    """)
    op.execute(r"""
    CREATE FUNCTION paprnav_v4_candidate_app_complete_trigger() RETURNS trigger AS $$
    DECLARE projection_id text;
    BEGIN
      IF TG_TABLE_NAME='ad_v4_candidate_app_projections' THEN
        projection_id:=to_jsonb(NEW)->>'id';
      ELSE
        projection_id:=to_jsonb(NEW)->>'projection_id';
        IF projection_id IS NULL AND to_jsonb(NEW)->>'proposal_id' IS NOT NULL THEN
          SELECT id INTO projection_id FROM ad_v4_candidate_app_projections
           WHERE proposal_id=to_jsonb(NEW)->>'proposal_id'
             AND materializer_version='paprnav-ad-v4-app-materializer-2';
        END IF;
      END IF;
      IF projection_id IS NULL AND TG_TABLE_NAME LIKE 'ad_v4_candidate_correction%' THEN
        RAISE EXCEPTION 'V4 correction foundation requires its applicability projection';
      END IF;
      IF projection_id IS NOT NULL THEN PERFORM paprnav_v4_candidate_app_require_complete(projection_id); END IF;
      RETURN NULL;
    END; $$ LANGUAGE plpgsql
    """)
    for table in APP_TABLES[1:]:
        op.execute(
            f"CREATE CONSTRAINT TRIGGER trg_{table}_complete "
            f"AFTER INSERT ON {table} DEFERRABLE INITIALLY DEFERRED FOR EACH ROW "
            "EXECUTE FUNCTION paprnav_v4_candidate_app_complete_trigger()"
        )


def downgrade() -> None:
    op.execute("LOCK TABLE ad_v4_candidate_proposals IN ACCESS EXCLUSIVE MODE")
    op.execute("LOCK TABLE ad_v4_feature_gates IN ACCESS EXCLUSIVE MODE")
    for table in CHILD_TABLES:
        op.execute(f"LOCK TABLE {table} IN ACCESS EXCLUSIVE MODE")
    for table in APP_TABLES[1:]:
        op.execute(f"LOCK TABLE {table} IN ACCESS EXCLUSIVE MODE")
    bind = op.get_bind()
    if bind.execute(sa.text("SELECT 1 FROM ad_v4_candidate_proposals WHERE validator_version=:v LIMIT 1"), {"v": V2_VALIDATOR}).first() is not None:
        raise RuntimeError("Revision 0027 contains immutable validator-2 candidates; retain dual readers")
    for table in APP_TABLES[1:]:
        if bind.execute(sa.text(f"SELECT 1 FROM {table} LIMIT 1")).first() is not None:
            raise RuntimeError("Revision 0027 contains immutable Slice-3A rows; retain dual readers")
    for table in reversed(APP_TABLES):
        op.drop_table(table)
    op.execute("DROP FUNCTION IF EXISTS paprnav_v4_candidate_app_complete_trigger()")
    op.execute("DROP FUNCTION IF EXISTS paprnav_v4_candidate_app_require_complete(text)")
    op.execute("DROP FUNCTION IF EXISTS paprnav_v4_jcs(jsonb)")
    op.execute("DROP FUNCTION IF EXISTS paprnav_v4_pointer_value(jsonb,text)")
    op.execute("DROP FUNCTION IF EXISTS paprnav_v4_json_nodes(jsonb,text,text,text,integer)")
    op.execute("DROP FUNCTION IF EXISTS paprnav_v4_validate_app_event()")
    op.execute("DROP FUNCTION IF EXISTS paprnav_v4_validate_app_request()")
    op.execute("DROP FUNCTION IF EXISTS paprnav_v4_validate_app_projection()")
    op.execute("DROP FUNCTION IF EXISTS paprnav_v4_lock_app_ad_numbers(text)")
    op.drop_constraint("uq_ad_v4_binding_parent_identity", "ad_v4_candidate_evidence_bindings", type_="unique")
    op.drop_constraint("uq_ad_v4_proposal_content_v2", "ad_v4_candidate_proposals", type_="unique")
    op.create_unique_constraint("uq_ad_v4_proposal_content", "ad_v4_candidate_proposals", ["directive_id", "canonicalization_version", "canonical_hash"])
    for table in reversed(CHILD_TABLES):
        op.drop_constraint(f"ck_{table}_version_pair", table, type_="check")
        op.drop_column(table, "canonicalization_version")
        op.drop_column(table, "validator_version")
    op.execute("DROP FUNCTION IF EXISTS paprnav_set_v4_feature_gate(text,boolean,text)")
    op.execute("DROP FUNCTION IF EXISTS paprnav_v4_capabilities()")
    # A physical downgrade is legal only for v1-only state. Deployment must run
    # revision-0026 code after Alembic completes; pre-v2 code is forbidden while
    # any v2 row exists by the checks above.

```
### `backend/app/services/ad_v4_applicability.py`

size=58050; sha256=7b31dca53a704446c92f193ec5c8537fd7d442f7bef89b916257e4769257c0d3; truncated=false

```text
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any, Iterable

from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.core import (
    ADEvidenceFragmentLifecycleEvent,
    ADV4CandidateAppChangeDependency,
    ADV4CandidateAppDatum,
    ADV4CandidateAppEvidenceLink,
    ADV4CandidateAppIdentityMapping,
    ADV4CandidateAppMaterializationRequest,
    ADV4CandidateAppProjection,
    ADV4CandidateAppProjectionEvent,
    ADV4CandidateAppSemanticNode,
    ADV4CandidateCorrection,
    ADV4CandidateCorrectionEvidenceLink,
    ADV4CandidateCorrectionRef,
    ADV4CandidateCorrectionSemanticBinding,
    ADV4CandidateEvidenceBinding,
    ADV4CandidateProposal,
    ADV4CandidateSubmissionRelationship,
    OrganizationMembership,
    User,
)
from app.services.ad_v4_candidates import (
    ADV4Error,
    CANONICALIZATION_VERSION_V2,
    VALIDATOR_VERSION_V2,
    _advisory_lock,
    _authorization,
    canonical_bytes,
    require_v4_database_gate,
    verified_candidate,
)


MATERIALIZER_VERSION = "paprnav-ad-v4-app-materializer-2"
POLICY_NAME = "paprnav-platform-admin-v4-applicability-materialize"
POLICY_VERSION = "1"
ENDPOINT_ACTION = "materialize_ad_v4_applicability"
SUBTREE_DOMAIN = b"paprnav:ad_extraction_v4:applicability-subtree:paprnav-ad-v4-c14n-2\x00"
PROJECTION_DOMAIN = b"paprnav:ad_extraction_v4:applicability-projection:2\x00"
EVENT_DOMAIN = b"paprnav:ad_extraction_v4:applicability-projection-event:2\x00"
ROW_DOMAIN = b"paprnav:ad_extraction_v4:applicability-row:2\x00"
APP_FIELDS = (
    "productScopes", "conditionDefinitions", "applicabilityRules",
    "applicabilitySearchHints",
)


@dataclass(frozen=True)
class MaterializedApplicability:
    projection: ADV4CandidateAppProjection
    request: ADV4CandidateAppMaterializationRequest
    created: bool
    idempotent_retry: bool


def _hash(domain: bytes, value: Any) -> str:
    return hashlib.sha256(domain + canonical_bytes(value, CANONICALIZATION_VERSION_V2)).hexdigest()


def _row_id(prefix: str, table: str, identity: Any) -> tuple[str, str]:
    full = _hash(ROW_DOMAIN, {"table": table, "identity": identity})
    return f"{prefix}_{full[:32]}", full


def _app_subtree(proposal: dict[str, Any]) -> dict[str, Any]:
    return {field: proposal[field] for field in APP_FIELDS}


def _require_application_gate(*, materialize: bool) -> None:
    settings = get_settings()
    if not settings.ad_v4_slice3a_routes_enabled:
        raise ADV4Error("capability_disabled", "", "Slice-3A application capability is disabled", http_status=404)
    if materialize and not settings.ad_v4_validator2_writes_enabled:
        raise ADV4Error("validator2_write_gate_disabled", "", "Validator-2 application capability is disabled", http_status=409)


def _lock_database_gates(db: Session, *, materialize: bool) -> None:
    if materialize:
        require_v4_database_gate(db, "validator2_write_enabled", lock=True)
    require_v4_database_gate(db, "materializer3a_enabled", lock=materialize)


def _lock_supersession_ad_numbers(db: Session, candidate: ADV4CandidateProposal) -> None:
    if db.bind is not None and db.bind.dialect.name == "postgresql":
        db.execute(
            text("SELECT paprnav_v4_lock_app_ad_numbers(:proposal_id)"),
            {"proposal_id": candidate.id},
        )
        return
    proposal = candidate.parsed_json
    numbers = {
        value
        for value in (
            proposal["directiveIdentity"]["adNumber"].get("value"),
            *(
                number
                for relation in proposal["supersessionRelations"]
                for number in (relation["predecessorAdNumber"], relation["successorAdNumber"])
            ),
        )
        if value is not None
    }
    for ad_number in sorted(numbers):
        _advisory_lock(db, f"applicability-ad-resolution:{ad_number}")


def _reject_new_predecessor_ambiguity(db: Session, candidate: ADV4CandidateProposal) -> None:
    ad_number = candidate.parsed_json["directiveIdentity"]["adNumber"]
    if ad_number.get("state") != "known":
        return
    if db.scalar(select(ADV4CandidateAppProjection.id).where(
        ADV4CandidateAppProjection.proposal_id == candidate.id,
        ADV4CandidateAppProjection.materializer_version == MATERIALIZER_VERSION,
    )) is not None:
        return
    existing_ids = []
    for possible in db.scalars(select(ADV4CandidateAppProjection)).all():
        possible_candidate = verified_candidate(db, possible.proposal_id)
        possible_ad = possible_candidate.parsed_json["directiveIdentity"]["adNumber"]
        if possible_ad.get("state") == "known" and possible_ad.get("value") == ad_number["value"]:
            existing_ids.append(possible.id)
    if existing_ids and db.scalar(select(ADV4CandidateAppChangeDependency.id).where(
        ADV4CandidateAppChangeDependency.resolution_state == "resolved_candidate",
        ADV4CandidateAppChangeDependency.target_projection_id.in_(existing_ids),
    ).limit(1)) is not None:
        raise ADV4Error(
            "supersession_resolution_conflict", "",
            "A resolved successor already depends on the unique predecessor identity",
            http_status=409,
        )


def authorize_projection_audit(db: Session, actor: User, membership_id: str) -> OrganizationMembership:
    _require_application_gate(materialize=False)
    membership = _authorization(db, actor, membership_id)
    _lock_database_gates(db, materialize=False)
    return membership


def _verify_live_evidence(db: Session, proposal: ADV4CandidateProposal) -> dict[str, ADV4CandidateEvidenceBinding]:
    bindings = db.scalars(
        select(ADV4CandidateEvidenceBinding)
        .where(ADV4CandidateEvidenceBinding.proposal_id == proposal.id)
        .order_by(ADV4CandidateEvidenceBinding.fragment_id, ADV4CandidateEvidenceBinding.evidence_key)
        .with_for_update()
    ).all()
    if len(bindings) != proposal.binding_count:
        raise ADV4Error("candidate_integrity", "", "Candidate evidence binding count differs", http_status=409)
    result: dict[str, ADV4CandidateEvidenceBinding] = {}
    for binding in bindings:
        events = db.scalars(
            select(ADEvidenceFragmentLifecycleEvent)
            .where(ADEvidenceFragmentLifecycleEvent.fragment_id == binding.fragment_id)
            .order_by(ADEvidenceFragmentLifecycleEvent.sequence_number)
        ).all()
        if (
            len(events) != 1
            or events[0].id != binding.admitted_event_id
            or events[0].event_type != "admitted"
            or events[0].event_hash != binding.admitted_event_hash
        ):
            raise ADV4Error("evidence_not_admitted", "", "Candidate evidence is no longer an admitted root", http_status=409)
        if binding.validator_version != proposal.validator_version or binding.canonicalization_version != proposal.canonicalization_version:
            raise ADV4Error("candidate_integrity", "", "Candidate evidence version differs", http_status=409)
        result[binding.evidence_key] = binding
    return result


def _semantic_type(pointer: str, value: dict[str, Any]) -> tuple[str, str] | None:
    if "nodeType" in value:
        return "expression", pointer
    candidates = (
        ("scopeKey", "product_scope"), ("conditionKey", "condition"),
        ("ruleKey", "applicability_rule"), ("hintKey", "search_hint"),
        ("groupKey", "designation_group"), ("memberKey", "designation_group_member"),
    )
    for key, kind in candidates:
        if key in value:
            if "/manufacturerModelGroups/" in pointer:
                kind = "search_hint_group" if key == "groupKey" else "search_hint_model"
            return kind, str(value[key])
    if "kind" in value and pointer.endswith(("/modelScope", "/serialScope", "/partNumberScope")):
        return "designation_scope", pointer.rsplit("/", 1)[-1]
    return None


def _flatten(
    value: Any,
    *,
    pointer: str,
    projection_id: str,
    proposal_id: str,
    parent_node_id: str | None,
    semantic_rows: list[ADV4CandidateAppSemanticNode],
    datum_rows: list[ADV4CandidateAppDatum],
    node_by_pointer: dict[str, ADV4CandidateAppSemanticNode],
    ordinal: int = 0,
) -> None:
    current_node_id = parent_node_id
    if isinstance(value, dict):
        semantic = _semantic_type(pointer, value)
        if semantic is not None:
            node_type, node_key = semantic
            if node_type in {
                "designation_scope", "designation_group", "designation_group_member",
                "search_hint_group", "search_hint_model",
            }:
                # These keys are only container-local in the canonical schema.
                # The source pointer is the proposal-scoped occurrence identity.
                node_key = pointer
            node_id, identity_hash = _row_id("avn", "semantic-node", {
                "projectionId": projection_id, "nodeType": node_type,
                "nodeKey": node_key, "pointer": pointer,
            })
            node = ADV4CandidateAppSemanticNode(
                id=node_id, identity_hash=identity_hash, projection_id=projection_id,
                proposal_id=proposal_id, parent_node_id=parent_node_id,
                node_type=node_type, node_key=node_key, source_pointer=pointer,
                canonical_node_hash=hashlib.sha256(canonical_bytes(value, CANONICALIZATION_VERSION_V2)).hexdigest(),
                canonical_ordinal=ordinal,
            )
            semantic_rows.append(node)
            node_by_pointer[pointer] = node
            current_node_id = node_id
    kind = "object" if isinstance(value, dict) else "array" if isinstance(value, list) else "boolean" if isinstance(value, bool) else "string"
    datum_id, datum_hash = _row_id("avd", "datum", {"projectionId": projection_id, "pointer": pointer, "kind": kind, "value": value if kind in {"string", "boolean"} else kind})
    datum_rows.append(ADV4CandidateAppDatum(
        id=datum_id, projection_id=projection_id, proposal_id=proposal_id,
        semantic_node_id=current_node_id, json_pointer=pointer,
        parent_pointer=None if pointer == "" else pointer.rsplit("/", 1)[0],
        property_name=None if pointer == "" or pointer.rsplit("/", 1)[-1].isdigit() else pointer.rsplit("/", 1)[-1],
        array_ordinal=ordinal if pointer and pointer.rsplit("/", 1)[-1].isdigit() else None,
        value_kind=kind, string_value=value if isinstance(value, str) else None,
        boolean_value=value if isinstance(value, bool) else None, value_hash=datum_hash,
    ))
    if isinstance(value, dict):
        for key in sorted(value, key=lambda item: item.encode("utf-16-be")):
            child_pointer = f"{pointer}/{key}" if pointer else f"/{key}"
            _flatten(value[key], pointer=child_pointer, projection_id=projection_id,
                     proposal_id=proposal_id, parent_node_id=current_node_id,
                     semantic_rows=semantic_rows, datum_rows=datum_rows,
                     node_by_pointer=node_by_pointer)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _flatten(child, pointer=f"{pointer}/{index}", projection_id=projection_id,
                     proposal_id=proposal_id, parent_node_id=current_node_id,
                     semantic_rows=semantic_rows, datum_rows=datum_rows,
                     node_by_pointer=node_by_pointer, ordinal=index)


def _evidence_purpose(node_type: str) -> str:
    return {
        "product_scope": "scope_clause", "designation_scope": "designation_scope",
        "condition": "condition_clause", "designation_group": "condition_clause",
        "designation_group_member": "subject_value", "applicability_rule": "rule_clause",
        "search_hint": "search_hint_clause", "search_hint_group": "search_hint_clause",
        "search_hint_model": "search_hint_clause",
        "change_dependency": "supersession_clause",
    }.get(node_type, "identity_support")


def _node_value(proposal: dict[str, Any], pointer: str) -> Any:
    first = pointer.strip("/").split("/", 1)[0] if pointer else ""
    value: Any = _app_subtree(proposal) if first in APP_FIELDS else proposal
    if pointer:
        for token in pointer.strip("/").split("/"):
            value = value[int(token)] if isinstance(value, list) else value[token]
    return value


def _identity_rows(
    projection: ADV4CandidateAppProjection,
    proposal: dict[str, Any],
    semantic_rows: list[ADV4CandidateAppSemanticNode],
    datum_rows: list[ADV4CandidateAppDatum],
) -> list[ADV4CandidateAppIdentityMapping]:
    rows: list[ADV4CandidateAppIdentityMapping] = []
    by_pointer = {row.source_pointer: row for row in semantic_rows}
    for node in semantic_rows:
        value = _node_value(proposal, node.source_pointer)
        occurrences: list[tuple[str, str, str, str | None, dict[str, Any] | None]] = []
        if node.node_type == "product_scope" and isinstance(value.get("manufacturer"), dict):
            manufacturer = value["manufacturer"]
            normalized_identity = manufacturer["normalizedIdentity"]
            normalized_value = (
                normalized_identity.get("value")
                if normalized_identity.get("state") == "known"
                else None
            )
            occurrences.append((
                "manufacturer",
                manufacturer["sourceValue"],
                "candidate_payload" if normalized_value is not None else "no_normalized_identity",
                normalized_value,
                manufacturer,
            ))
        elif node.node_type == "designation_scope" and value.get("kind") == "listed":
            for index, source in enumerate(value["sourceDesignations"]):
                child_pointer = f"{node.source_pointer}/sourceDesignations/{index}"
                child = by_pointer.get(child_pointer)
                if child is None:
                    child_id, child_hash = _row_id("avn", "designation-value", {"projectionId": projection.id, "pointer": child_pointer, "value": source})
                    child = ADV4CandidateAppSemanticNode(id=child_id, identity_hash=child_hash, projection_id=projection.id, proposal_id=projection.proposal_id, parent_node_id=node.id, node_type="designation_value", node_key=f"{node.node_key}:{index}", source_pointer=child_pointer, canonical_node_hash=hashlib.sha256(canonical_bytes(source, CANONICALIZATION_VERSION_V2)).hexdigest(), canonical_ordinal=index)
                    semantic_rows.append(child)
                    by_pointer[child_pointer] = child
                    for datum in datum_rows:
                        if datum.json_pointer == child_pointer:
                            datum.semantic_node_id = child.id
                            break
                identity_kind = (
                    "model" if node.source_pointer.endswith("/modelScope")
                    else "series" if value.get("kind") == "series_expression"
                    else "model"
                )
                occurrences.append((identity_kind, source, "no_normalized_identity", None, {"_node": child}))
        elif node.node_type in {"designation_group_member", "search_hint_model"}:
            source = value.get("sourceDesignation") or value.get("expressionText")
            occurrences.append(("model" if value["designationKind"] == "model" else "series", source, "source_only", None, value))
        for identity_kind, source, origin, normalized, carrier in occurrences:
            occurrence = carrier.get("_node") if carrier else None
            occurrence = occurrence or node
            row_id, full_hash = _row_id("avi", "identity-mapping", {"projectionId": projection.id, "kind": identity_kind, "occurrence": occurrence.id})
            rows.append(ADV4CandidateAppIdentityMapping(
                id=row_id, projection_id=projection.id, proposal_id=projection.proposal_id,
                source_occurrence_node_id=occurrence.id, evidence_parent_node_id=node.id,
                identity_kind=identity_kind, source_value=source,
                normalization_origin=origin, normalized_state="known" if normalized else "unknown",
                normalized_value=normalized, reason=None if normalized else "not_extracted",
                temporal_scope=None if normalized else "directive_version",
                normalization_namespace="candidate" if normalized else None,
                normalization_version="1" if normalized else None,
                review_state="unreviewed_candidate", identity_hash=full_hash,
            ))
    return rows


def _reconstruct_data(rows: Iterable[ADV4CandidateAppDatum]) -> dict[str, Any]:
    def pointer_order(pointer: str) -> tuple[tuple[int, int | str], ...]:
        return tuple(
            (0, int(token)) if token.isdigit() else (1, token)
            for token in pointer.strip("/").split("/") if token
        )

    ordered = sorted(
        rows,
        key=lambda row: (row.json_pointer.count("/"), pointer_order(row.json_pointer)),
    )
    values: dict[str, Any] = {}
    for row in ordered:
        if row.value_kind == "object":
            value: Any = {}
        elif row.value_kind == "array":
            value = []
        elif row.value_kind == "boolean":
            value = row.boolean_value
        else:
            value = row.string_value
        values[row.json_pointer] = value
        if row.json_pointer == "":
            continue
        parent = values.get(row.parent_pointer or "")
        if parent is None:
            raise ADV4Error("projection_integrity", row.json_pointer, "Projection parent datum is missing", http_status=409)
        if isinstance(parent, list):
            if row.array_ordinal != len(parent):
                raise ADV4Error("projection_integrity", row.json_pointer, "Projection array ordinal is noncontiguous", http_status=409)
            parent.append(value)
        elif isinstance(parent, dict) and row.property_name is not None:
            parent[row.property_name] = value
        else:
            raise ADV4Error("projection_integrity", row.json_pointer, "Projection parent/container mismatch", http_status=409)
    root = values.get("")
    if not isinstance(root, dict):
        raise ADV4Error("projection_integrity", "", "Projection root is missing", http_status=409)
    return root


def reconstruct_applicability(db: Session, projection: ADV4CandidateAppProjection) -> dict[str, Any]:
    proposal = verified_candidate(db, projection.proposal_id)
    if proposal.validator_version != VALIDATOR_VERSION_V2 or proposal.canonicalization_version != CANONICALIZATION_VERSION_V2:
        raise ADV4Error("predecessor_semantic_defect", "", "Only validator-2 candidates can be projected", http_status=422)
    rows = db.scalars(select(ADV4CandidateAppDatum).where(ADV4CandidateAppDatum.projection_id == projection.id)).all()
    if len(rows) != projection.datum_count:
        raise ADV4Error("projection_integrity", "", "Projection datum count differs", http_status=409)
    reconstructed = _reconstruct_data(rows)
    expected = _app_subtree(proposal.parsed_json)
    payload = canonical_bytes(reconstructed, CANONICALIZATION_VERSION_V2)
    if (
        reconstructed != expected
        or payload != projection.applicability_subtree_bytes
        or hashlib.sha256(SUBTREE_DOMAIN + payload).hexdigest() != projection.applicability_subtree_hash
        or hashlib.sha256(PROJECTION_DOMAIN + projection.projection_canonical_bytes).hexdigest() != projection.projection_hash
    ):
        raise ADV4Error("projection_integrity", "", "Relational reconstruction differs from candidate", http_status=409)
    _verify_correction_foundation(db, projection, proposal)
    _verify_change_dependencies(db, projection, proposal)
    return reconstructed


def _document_identity(document: dict[str, Any]) -> str:
    return _hash(ROW_DOMAIN, {"officialDocument": document})


def _verify_change_dependencies(
    db: Session,
    projection: ADV4CandidateAppProjection,
    candidate: ADV4CandidateProposal,
) -> None:
    """Verify immutable outgoing facts and target-local incoming causes."""
    dependencies = db.scalars(
        select(ADV4CandidateAppChangeDependency)
        .where(ADV4CandidateAppChangeDependency.projection_id == projection.id)
        .order_by(ADV4CandidateAppChangeDependency.dependency_key)
    ).all()
    outgoing = [row for row in dependencies if row.dependency_kind != "incoming_supersession_signal"]
    relations = candidate.parsed_json["supersessionRelations"]
    if len(outgoing) != len(relations):
        raise ADV4Error("projection_integrity", "", "Supersession dependency count differs", http_status=409)
    canonical_ad = candidate.parsed_json["directiveIdentity"]["adNumber"]
    by_key = {row.dependency_key: row for row in outgoing}
    for relation in relations:
        key = f"{relation['relationType']}:{relation['predecessorAdNumber']}"
        row = by_key.get(key)
        node = db.get(ADV4CandidateAppSemanticNode, row.semantic_node_id) if row else None
        if (
            row is None
            or row.proposal_id != candidate.id
            or row.dependency_kind != (
                "outgoing_supersedes" if relation["relationType"] == "supersedes"
                else "outgoing_partially_supersedes"
            )
            or row.predecessor_ad_number != relation["predecessorAdNumber"]
            or row.successor_ad_number != relation["successorAdNumber"]
            or row.source_dependency_id is not None
            or node is None
            or node.projection_id != projection.id
            or node.node_type != "change_dependency"
            or node.node_key != key
        ):
            raise ADV4Error("projection_integrity", "", "Outgoing supersession dependency differs", http_status=409)
        successor_matches = (
            canonical_ad.get("state") == "known"
            and relation["successorAdNumber"] == canonical_ad.get("value")
        )
        if not successor_matches and (
            row.resolution_state != "unresolved"
            or row.target_projection_id is not None
            or row.unresolved_reason not in {"successor_identity_unknown", "successor_not_this_proposal"}
        ):
            raise ADV4Error("projection_integrity", "", "Mismatched successor was resolved", http_status=409)
        if row.resolution_state == "resolved_candidate":
            incoming = db.scalar(select(ADV4CandidateAppChangeDependency).where(
                ADV4CandidateAppChangeDependency.source_dependency_id == row.id,
                ADV4CandidateAppChangeDependency.dependency_kind == "incoming_supersession_signal",
            ))
            if (
                not successor_matches
                or row.target_projection_id is None
                or row.unresolved_reason is not None
                or incoming is None
                or incoming.projection_id != row.target_projection_id
                or incoming.target_projection_id != row.target_projection_id
                or incoming.proposal_id == row.proposal_id
                or incoming.resolution_state != "resolved_candidate"
                or incoming.unresolved_reason is not None
                or incoming.predecessor_ad_number != row.predecessor_ad_number
                or incoming.successor_ad_number != row.successor_ad_number
            ):
                raise ADV4Error("projection_integrity", "", "Resolved supersession dependency is incomplete", http_status=409)
        elif row.target_projection_id is not None:
            raise ADV4Error("projection_integrity", "", "Unresolved supersession has a target", http_status=409)

    for incoming in (row for row in dependencies if row.dependency_kind == "incoming_supersession_signal"):
        source = db.get(ADV4CandidateAppChangeDependency, incoming.source_dependency_id)
        node = db.get(ADV4CandidateAppSemanticNode, incoming.semantic_node_id)
        if (
            source is None
            or source.dependency_kind not in {"outgoing_supersedes", "outgoing_partially_supersedes"}
            or source.resolution_state != "resolved_candidate"
            or source.target_projection_id != projection.id
            or incoming.target_projection_id != projection.id
            or incoming.proposal_id != projection.proposal_id
            or incoming.resolution_state != "resolved_candidate"
            or incoming.unresolved_reason is not None
            or node is None
            or node.projection_id != projection.id
            or node.node_type != "change_dependency"
            or node.node_key != f"incoming:{source.id}"
        ):
            raise ADV4Error("projection_integrity", "", "Incoming supersession dependency differs", http_status=409)


def _verify_correction_foundation(
    db: Session,
    projection: ADV4CandidateAppProjection,
    candidate: ADV4CandidateProposal,
) -> list[dict[str, Any]]:
    """Reconstruct and verify the proposal-scoped correction foundation exactly."""
    expected = candidate.parsed_json["authoritativeCorrections"]
    documents = {
        item["officialDocumentKey"]: item
        for item in candidate.parsed_json["officialDocuments"]
    }
    roots = db.scalars(
        select(ADV4CandidateCorrection)
        .where(ADV4CandidateCorrection.proposal_id == candidate.id)
        .order_by(ADV4CandidateCorrection.canonical_ordinal)
    ).all()
    if len(roots) != len(expected):
        raise ADV4Error("projection_integrity", "", "Correction foundation count differs", http_status=409)
    reconstructed: list[dict[str, Any]] = []
    three_a_types = {
        "productScopes": "product_scope",
        "conditionDefinitions": "condition",
        "applicabilityRules": "applicability_rule",
    }
    for ordinal, (root, canonical) in enumerate(zip(roots, expected, strict=True)):
        refs = db.scalars(
            select(ADV4CandidateCorrectionRef)
            .where(ADV4CandidateCorrectionRef.correction_id == root.id)
            .order_by(ADV4CandidateCorrectionRef.canonical_ordinal)
        ).all()
        evidence = db.scalars(
            select(ADV4CandidateCorrectionEvidenceLink)
            .where(ADV4CandidateCorrectionEvidenceLink.correction_id == root.id)
            .order_by(ADV4CandidateCorrectionEvidenceLink.canonical_ordinal)
        ).all()
        value = {
            "correctionKey": root.correction_key,
            "correctionType": root.correction_type,
            "originalDocumentRefKey": root.original_document_ref_key,
            "correctingDocumentRefKey": root.correcting_document_ref_key,
            "changedSemanticRefs": [
                {"namespace": ref.namespace, "key": ref.semantic_key}
                for ref in refs
            ],
            "evidenceKeys": [link.evidence_key for link in evidence],
        }
        original = documents.get(root.original_document_ref_key)
        correcting = documents.get(root.correcting_document_ref_key)
        if (
            root.canonical_ordinal != ordinal
            or root.foundation_version != "paprnav-ad-v4-correction-foundation-1"
            or root.generation != 1
            or root.expected_ref_count != len(refs)
            or root.expected_evidence_count != len(evidence)
            or original is None
            or correcting is None
            or root.original_document_identity_hash != _document_identity(original)
            or root.correcting_document_identity_hash != _document_identity(correcting)
            or root.canonical_hash
            != hashlib.sha256(canonical_bytes(value, CANONICALIZATION_VERSION_V2)).hexdigest()
            or value != canonical
        ):
            raise ADV4Error("projection_integrity", "", "Correction foundation differs from candidate", http_status=409)
        for ref_ordinal, ref in enumerate(refs):
            expected_owner = "slice_3a" if ref.namespace in three_a_types else (
                "foundation" if ref.namespace in {"directiveIdentity", "supersessionRelations"} else "slice_3b"
            )
            bindings = db.scalars(
                select(ADV4CandidateCorrectionSemanticBinding).where(
                    ADV4CandidateCorrectionSemanticBinding.correction_ref_id == ref.id
                )
            ).all()
            if (
                ref.canonical_ordinal != ref_ordinal
                or ref.owner_slice != expected_owner
                or ref.reference_hash
                != _row_id("avf", "correction-ref", {
                    "correctionId": root.id,
                    "namespace": ref.namespace,
                    "key": ref.semantic_key,
                })[1]
                or len(bindings) != (1 if expected_owner == "slice_3a" else 0)
            ):
                raise ADV4Error("projection_integrity", "", "Correction reference is incomplete", http_status=409)
            if bindings:
                binding = bindings[0]
                node = db.get(ADV4CandidateAppSemanticNode, binding.semantic_node_id)
                if (
                    binding.proposal_id != candidate.id
                    or binding.projection_id != projection.id
                    or binding.binding_slice != "slice_3a"
                    or binding.generation != 1
                    or node is None
                    or node.projection_id != projection.id
                    or node.node_type != three_a_types[ref.namespace]
                    or node.node_key != ref.semantic_key
                ):
                    raise ADV4Error("projection_integrity", "", "Correction semantic binding differs", http_status=409)
        for evidence_ordinal, link in enumerate(evidence):
            binding = db.get(ADV4CandidateEvidenceBinding, link.candidate_binding_id)
            if (
                link.canonical_ordinal != evidence_ordinal
                or binding is None
                or binding.proposal_id != candidate.id
                or binding.evidence_key != link.evidence_key
            ):
                raise ADV4Error("projection_integrity", "", "Correction evidence differs", http_status=409)
        reconstructed.append(value)
    return reconstructed


def materialize_applicability(
    db: Session,
    *,
    directive_id: str,
    proposal_id: str,
    actor: User,
    membership_id: str,
    idempotency_key: str,
) -> MaterializedApplicability:
    _require_application_gate(materialize=True)
    membership = _authorization(db, actor, membership_id)
    scope = f"{actor.id}:{membership.id}:{ENDPOINT_ACTION}:{POLICY_VERSION}:{idempotency_key}"
    _advisory_lock(db, f"idem:{scope}")
    candidate = db.scalar(select(ADV4CandidateProposal).where(ADV4CandidateProposal.id == proposal_id).with_for_update())
    if candidate is None or candidate.directive_id != directive_id:
        raise ADV4Error("not_found", "", "Candidate proposal not found", http_status=404)
    _lock_database_gates(db, materialize=True)
    candidate = verified_candidate(db, candidate.id)
    if candidate.gate != "candidate_only" or candidate.validator_version != VALIDATOR_VERSION_V2 or candidate.canonicalization_version != CANONICALIZATION_VERSION_V2:
        raise ADV4Error("predecessor_semantic_defect", "", "Candidate is not eligible for Slice-3A materialization", http_status=422)
    bindings = _verify_live_evidence(db, candidate)
    _lock_supersession_ad_numbers(db, candidate)
    _reject_new_predecessor_ambiguity(db, candidate)
    _advisory_lock(db, f"projection:{proposal_id}:{MATERIALIZER_VERSION}")
    request_value = {
        "action": ENDPOINT_ACTION, "directiveId": directive_id,
        "proposalId": proposal_id, "validatorVersion": VALIDATOR_VERSION_V2,
        "canonicalizationVersion": CANONICALIZATION_VERSION_V2,
        "materializerVersion": MATERIALIZER_VERSION,
    }
    request_bytes = canonical_bytes(request_value, CANONICALIZATION_VERSION_V2)
    request_hash = hashlib.sha256(ROW_DOMAIN + request_bytes).hexdigest()
    prior = db.scalar(select(ADV4CandidateAppMaterializationRequest).where(
        ADV4CandidateAppMaterializationRequest.actor_user_id == actor.id,
        ADV4CandidateAppMaterializationRequest.authorizing_membership_id == membership.id,
        ADV4CandidateAppMaterializationRequest.endpoint_action == ENDPOINT_ACTION,
        ADV4CandidateAppMaterializationRequest.auth_policy_version == POLICY_VERSION,
        ADV4CandidateAppMaterializationRequest.idempotency_key == idempotency_key,
    ))
    if prior is not None:
        if prior.request_hash != request_hash or prior.proposal_id != proposal_id:
            raise ADV4Error("idempotency_conflict", "", "Idempotency key was used for another projection", http_status=409)
        projection = db.get(ADV4CandidateAppProjection, prior.projection_id)
        if projection is None:
            raise ADV4Error("projection_integrity", "", "Idempotent request lost its projection", http_status=409)
        reconstruct_applicability(db, projection)
        _repair_stale_projection_on_materialization(db, projection)
        return MaterializedApplicability(projection, prior, False, True)

    projection = db.scalar(select(ADV4CandidateAppProjection).where(
        ADV4CandidateAppProjection.proposal_id == proposal_id,
        ADV4CandidateAppProjection.materializer_version == MATERIALIZER_VERSION,
    ))
    created = projection is None
    if projection is None:
        subtree = _app_subtree(candidate.parsed_json)
        subtree_bytes = canonical_bytes(subtree, CANONICALIZATION_VERSION_V2)
        subtree_hash = hashlib.sha256(SUBTREE_DOMAIN + subtree_bytes).hexdigest()
        provisional_id, identity_hash = _row_id("avx", "projection", {"proposalId": proposal_id, "materializerVersion": MATERIALIZER_VERSION, "subtreeHash": subtree_hash})
        semantic_rows: list[ADV4CandidateAppSemanticNode] = []
        datum_rows: list[ADV4CandidateAppDatum] = []
        nodes: dict[str, ADV4CandidateAppSemanticNode] = {}
        _flatten(subtree, pointer="", projection_id=provisional_id, proposal_id=proposal_id,
                 parent_node_id=None, semantic_rows=semantic_rows, datum_rows=datum_rows,
                 node_by_pointer=nodes)
        for relation_index, relation in enumerate(candidate.parsed_json["supersessionRelations"]):
            pointer = f"/supersessionRelations/{relation_index}"
            node_key = f"{relation['relationType']}:{relation['predecessorAdNumber']}"
            node_id, node_hash = _row_id("avn", "semantic-node", {
                "projectionId": provisional_id, "nodeType": "change_dependency",
                "nodeKey": node_key, "pointer": pointer,
            })
            node = ADV4CandidateAppSemanticNode(
                id=node_id, identity_hash=node_hash, projection_id=provisional_id,
                proposal_id=proposal_id, parent_node_id=None,
                node_type="change_dependency",
                node_key=node_key,
                source_pointer=pointer,
                canonical_node_hash=hashlib.sha256(
                    canonical_bytes(relation, CANONICALIZATION_VERSION_V2)
                ).hexdigest(),
                canonical_ordinal=relation_index,
            )
            semantic_rows.append(node)
            nodes[pointer] = node
        identity_rows = _identity_rows(
            ADV4CandidateAppProjection(id=provisional_id, identity_hash=identity_hash, proposal_id=proposal_id, directive_id=directive_id, schema_version=candidate.schema_version, validator_version=candidate.validator_version, canonicalization_version=candidate.canonicalization_version, proposal_canonical_hash=candidate.canonical_hash, evidence_binding_hash=candidate.evidence_binding_hash, materializer_version=MATERIALIZER_VERSION, applicability_subtree_bytes=subtree_bytes, applicability_subtree_hash=subtree_hash, projection_canonical_bytes=b"", projection_hash="", gate="candidate_only", semantic_node_count=0, datum_count=0, evidence_link_count=0, identity_mapping_count=0),
            candidate.parsed_json, semantic_rows, datum_rows,
        )
        binding_by_key = bindings
        evidence_rows: list[ADV4CandidateAppEvidenceLink] = []
        for node in semantic_rows:
            node_value = _node_value(candidate.parsed_json, node.source_pointer)
            keys = node_value.get("evidenceKeys", []) if isinstance(node_value, dict) else []
            for ordinal, evidence_key in enumerate(keys):
                binding = binding_by_key[evidence_key]
                link_id, link_hash = _row_id("avl", "evidence-link", {"projectionId": provisional_id, "nodeId": node.id, "purpose": _evidence_purpose(node.node_type), "evidenceKey": evidence_key})
                evidence_rows.append(ADV4CandidateAppEvidenceLink(id=link_id, projection_id=provisional_id, proposal_id=proposal_id, semantic_node_id=node.id, candidate_binding_id=binding.id, evidence_key=evidence_key, purpose=_evidence_purpose(node.node_type), canonical_ordinal=ordinal, link_hash=link_hash))
        projection_envelope = {
            "version": "ad-v4-applicability-projection-v2", "proposalId": proposal_id,
            "proposalCanonicalHash": candidate.canonical_hash,
            "evidenceBindingHash": candidate.evidence_binding_hash,
            "validatorVersion": candidate.validator_version,
            "canonicalizationVersion": candidate.canonicalization_version,
            "materializerVersion": MATERIALIZER_VERSION,
            "applicabilitySubtreeHash": subtree_hash,
            "semanticNodeHashes": sorted(row.identity_hash for row in semantic_rows),
            "evidenceLinkHashes": sorted(row.link_hash for row in evidence_rows),
        }
        projection_bytes = canonical_bytes(projection_envelope, CANONICALIZATION_VERSION_V2)
        projection = ADV4CandidateAppProjection(
            id=provisional_id, identity_hash=identity_hash, proposal_id=proposal_id,
            directive_id=directive_id, schema_version=candidate.schema_version,
            validator_version=candidate.validator_version,
            canonicalization_version=candidate.canonicalization_version,
            proposal_canonical_hash=candidate.canonical_hash,
            evidence_binding_hash=candidate.evidence_binding_hash,
            materializer_version=MATERIALIZER_VERSION,
            applicability_subtree_bytes=subtree_bytes,
            applicability_subtree_hash=subtree_hash,
            projection_canonical_bytes=projection_bytes,
            projection_hash=hashlib.sha256(PROJECTION_DOMAIN + projection_bytes).hexdigest(), gate="candidate_only",
            semantic_node_count=len(semantic_rows), datum_count=len(datum_rows),
            evidence_link_count=len(evidence_rows), identity_mapping_count=len(identity_rows),
        )
        db.add(projection)
        db.flush([projection])
        db.add_all(semantic_rows)
        db.flush(semantic_rows)
        db.add_all(datum_rows + identity_rows + evidence_rows)
        db.flush()
        stale_targets = _materialize_dependencies(db, projection, candidate, nodes)
        _materialize_corrections(db, projection, candidate, bindings, nodes)
    else:
        stale_targets = []

    claims = {"userId": actor.id, "membershipId": membership.id, "organizationId": membership.organization_id, "role": membership.role, "status": membership.status, "policy": POLICY_NAME, "version": POLICY_VERSION}
    request_id, _ = _row_id("avq", "materialization-request", {"scope": scope, "requestHash": request_hash})
    request = ADV4CandidateAppMaterializationRequest(
        id=request_id, projection_id=projection.id, proposal_id=proposal_id,
        directive_id=directive_id, actor_user_id=actor.id,
        authorizing_membership_id=membership.id, organization_id=membership.organization_id,
        actor_role=membership.role, actor_status=membership.status,
        auth_policy_name=POLICY_NAME, auth_policy_version=POLICY_VERSION,
        auth_claims_hash=hashlib.sha256(canonical_bytes(claims, CANONICALIZATION_VERSION_V2)).hexdigest(),
        endpoint_action=ENDPOINT_ACTION, idempotency_key=idempotency_key,
        request_canonical_bytes=request_bytes, request_hash=request_hash,
    )
    db.add(request)
    db.flush([request])
    if created:
        event_value = {"version": "ad-v4-applicability-event-v2", "eventType": "materialized", "projectionId": projection.id, "proposalId": proposal_id, "sequence": "0", "requestId": request.id, "predecessorEventHash": "none"}
        event_bytes = canonical_bytes(event_value, CANONICALIZATION_VERSION_V2)
        event_hash = hashlib.sha256(EVENT_DOMAIN + event_bytes).hexdigest()
        event_id, _ = _row_id("avz", "projection-event", {"projectionId": projection.id, "eventHash": event_hash})
        db.add(ADV4CandidateAppProjectionEvent(id=event_id, projection_id=projection.id, proposal_id=proposal_id, sequence_number=0, event_type="materialized", reason_code="explicit_admin_materialization", causing_request_id=request.id, causing_relationship_id=None, causing_lifecycle_event_id=None, causing_dependency_id=None, predecessor_event_hash=None, canonical_bytes=event_bytes, event_hash=event_hash, actor_kind="platform_admin"))
    db.flush()
    for target in stale_targets:
        _repair_stale_projection_on_materialization(db, target)
    reconstruct_applicability(db, projection)
    _repair_stale_projection_on_materialization(db, projection)
    return MaterializedApplicability(projection, request, created, False)


def _materialize_corrections(
    db: Session,
    projection: ADV4CandidateAppProjection,
    candidate: ADV4CandidateProposal,
    bindings: dict[str, ADV4CandidateEvidenceBinding],
    nodes: dict[str, ADV4CandidateAppSemanticNode],
) -> None:
    documents = {item["officialDocumentKey"]: item for item in candidate.parsed_json["officialDocuments"]}
    node_by_key = {(node.node_type, node.node_key): node for node in nodes.values()}
    owner = {
        "directiveIdentity": "foundation", "supersessionRelations": "foundation",
        "productScopes": "slice_3a", "conditionDefinitions": "slice_3a",
        "applicabilityRules": "slice_3a", "requirements": "slice_3b",
        "recurrenceGroups": "slice_3b", "amocAuthorityProvisions": "slice_3b",
    }
    type_by_namespace = {"productScopes": "product_scope", "conditionDefinitions": "condition", "applicabilityRules": "applicability_rule"}
    for ordinal, value in enumerate(candidate.parsed_json["authoritativeCorrections"]):
        root_id, root_hash = _row_id("avc", "correction", {"proposalId": candidate.id, "correctionKey": value["correctionKey"]})
        original = documents[value["originalDocumentRefKey"]]
        correcting = documents[value["correctingDocumentRefKey"]]
        root = ADV4CandidateCorrection(id=root_id, identity_hash=root_hash, proposal_id=candidate.id, correction_key=value["correctionKey"], correction_type=value["correctionType"], original_document_ref_key=value["originalDocumentRefKey"], correcting_document_ref_key=value["correctingDocumentRefKey"], original_document_identity_hash=_document_identity(original), correcting_document_identity_hash=_document_identity(correcting), canonical_hash=hashlib.sha256(canonical_bytes(value, CANONICALIZATION_VERSION_V2)).hexdigest(), canonical_ordinal=ordinal, foundation_version="paprnav-ad-v4-correction-foundation-1", generation=1, expected_ref_count=len(value["changedSemanticRefs"]), expected_evidence_count=len(value["evidenceKeys"]))
        db.add(root)
        db.flush([root])
        for ref_ordinal, ref in enumerate(value["changedSemanticRefs"]):
            ref_id, ref_hash = _row_id("avf", "correction-ref", {"correctionId": root.id, "namespace": ref["namespace"], "key": ref["key"]})
            ref_row = ADV4CandidateCorrectionRef(id=ref_id, correction_id=root.id, proposal_id=candidate.id, canonical_ordinal=ref_ordinal, namespace=ref["namespace"], semantic_key=ref["key"], owner_slice=owner[ref["namespace"]], reference_hash=ref_hash)
            db.add(ref_row)
            db.flush([ref_row])
            if ref["namespace"] in type_by_namespace:
                semantic = node_by_key.get((type_by_namespace[ref["namespace"]], ref["key"]))
                if semantic is None:
                    raise ADV4Error("projection_integrity", "", "Correction 3A reference does not resolve")
                binding_id, binding_hash = _row_id("avk", "correction-binding", {"refId": ref_id, "semanticId": semantic.id})
                db.add(ADV4CandidateCorrectionSemanticBinding(id=binding_id, correction_ref_id=ref_id, proposal_id=candidate.id, projection_id=projection.id, semantic_node_id=semantic.id, binding_slice="slice_3a", generation=1, binding_hash=binding_hash))
        for evidence_ordinal, evidence_key in enumerate(value["evidenceKeys"]):
            evidence_id, link_hash = _row_id("avh", "correction-evidence", {"correctionId": root.id, "evidenceKey": evidence_key})
            db.add(ADV4CandidateCorrectionEvidenceLink(id=evidence_id, correction_id=root.id, proposal_id=candidate.id, candidate_binding_id=bindings[evidence_key].id, evidence_key=evidence_key, canonical_ordinal=evidence_ordinal, link_hash=link_hash))


def _materialize_dependencies(
    db: Session,
    projection: ADV4CandidateAppProjection,
    candidate: ADV4CandidateProposal,
    nodes: dict[str, ADV4CandidateAppSemanticNode],
) -> list[ADV4CandidateAppProjection]:
    plans: list[tuple[dict[str, Any], ADV4CandidateAppSemanticNode, str, str, str, str | None, ADV4CandidateAppProjection | None]] = []
    stale_targets: dict[str, ADV4CandidateAppProjection] = {}
    canonical_ad = candidate.parsed_json["directiveIdentity"]["adNumber"]
    for ordinal, relation in enumerate(candidate.parsed_json["supersessionRelations"]):
        pointer = f"/supersessionRelations/{ordinal}"
        node = nodes[pointer]
        dependency_key = f"{relation['relationType']}:{relation['predecessorAdNumber']}"
        dependency_id, dependency_hash = _row_id("avj", "change-dependency", {
            "projectionId": projection.id,
            "dependencyKey": dependency_key,
            "predecessorAdNumber": relation["predecessorAdNumber"],
            "successorAdNumber": relation["successorAdNumber"],
        })
        target: ADV4CandidateAppProjection | None = None
        if canonical_ad.get("state") != "known":
            resolution_state = "unresolved"
            unresolved_reason = "successor_identity_unknown"
        elif relation["successorAdNumber"] != canonical_ad["value"]:
            resolution_state = "unresolved"
            unresolved_reason = "successor_not_this_proposal"
        else:
            matches: list[ADV4CandidateAppProjection] = []
            for possible in db.scalars(select(ADV4CandidateAppProjection).where(
                ADV4CandidateAppProjection.id != projection.id
            )).all():
                possible_candidate = verified_candidate(db, possible.proposal_id)
                possible_ad = possible_candidate.parsed_json["directiveIdentity"]["adNumber"]
                if possible_ad.get("state") == "known" and possible_ad.get("value") == relation["predecessorAdNumber"]:
                    matches.append(possible)
            if len(matches) == 1:
                target = matches[0]
                resolution_state = "resolved_candidate"
                unresolved_reason = None
            elif matches:
                resolution_state = "ambiguous"
                unresolved_reason = "multiple_predecessor_candidates"
            else:
                resolution_state = "unresolved"
                unresolved_reason = "target_candidate_not_resolved"
        plans.append((relation, node, dependency_id, dependency_hash, resolution_state, unresolved_reason, target))
        if target is not None:
            stale_targets[target.id] = target

    # Resolve first, then lock every affected predecessor root in lexical ID
    # order before appending any target-local cause or event.
    for target_id in sorted(stale_targets):
        locked = db.scalar(select(ADV4CandidateAppProjection).where(
            ADV4CandidateAppProjection.id == target_id
        ).with_for_update())
        if locked is None:
            raise ADV4Error("projection_integrity", "", "Resolved supersession target disappeared", http_status=409)
        stale_targets[target_id] = locked

    for relation, node, dependency_id, dependency_hash, resolution_state, unresolved_reason, target in plans:
        dependency_key = f"{relation['relationType']}:{relation['predecessorAdNumber']}"
        target = stale_targets.get(target.id) if target is not None else None
        outgoing = ADV4CandidateAppChangeDependency(
            id=dependency_id, projection_id=projection.id, proposal_id=candidate.id,
            semantic_node_id=node.id, dependency_key=dependency_key,
            dependency_kind=(
                "outgoing_supersedes" if relation["relationType"] == "supersedes"
                else "outgoing_partially_supersedes"
            ), predecessor_ad_number=relation["predecessorAdNumber"],
            successor_ad_number=relation["successorAdNumber"],
            resolution_state=resolution_state, unresolved_reason=unresolved_reason,
            target_projection_id=target.id if target is not None else None, source_dependency_id=None,
            dependency_hash=dependency_hash,
        )
        db.add(outgoing)
        db.flush([outgoing])
        if target is None:
            continue
        # The target-local signal and event are appended under deterministic
        # identities and the target projection lock. They carry no evidence
        # text; the immutable source dependency retains that evidence binding.
        incoming_pointer = f"/incomingSupersessionSignals/{outgoing.id}"
        incoming_key = f"incoming:{outgoing.id}"
        incoming_value = {
            "sourceDependencyId": outgoing.id,
            "targetProjectionId": target.id,
        }
        node_id, node_hash = _row_id("avn", "semantic-node", {
            "projectionId": target.id, "nodeType": "change_dependency",
            "nodeKey": incoming_key, "pointer": incoming_pointer,
        })
        incoming_node = ADV4CandidateAppSemanticNode(
            id=node_id, identity_hash=node_hash, projection_id=target.id,
            proposal_id=target.proposal_id, parent_node_id=None,
            node_type="change_dependency", node_key=incoming_key,
            source_pointer=incoming_pointer,
            canonical_node_hash=hashlib.sha256(
                canonical_bytes(incoming_value, CANONICALIZATION_VERSION_V2)
            ).hexdigest(), canonical_ordinal=0,
        )
        db.add(incoming_node)
        db.flush([incoming_node])
        incoming_id, incoming_hash = _row_id("avj", "incoming-change-dependency", {
            "projectionId": target.id, "sourceDependencyId": outgoing.id,
        })
        db.add(ADV4CandidateAppChangeDependency(
            id=incoming_id, projection_id=target.id, proposal_id=target.proposal_id,
            semantic_node_id=incoming_node.id, dependency_key=incoming_key,
            dependency_kind="incoming_supersession_signal",
            predecessor_ad_number=outgoing.predecessor_ad_number,
            successor_ad_number=outgoing.successor_ad_number,
            resolution_state="resolved_candidate", unresolved_reason=None,
            target_projection_id=target.id, source_dependency_id=outgoing.id,
            dependency_hash=incoming_hash,
        ))
    db.flush()
    return list(stale_targets.values())


def verified_app_projection(db: Session, *, directive_id: str, proposal_id: str) -> ADV4CandidateAppProjection:
    projection = db.scalar(select(ADV4CandidateAppProjection).where(
        ADV4CandidateAppProjection.proposal_id == proposal_id,
        ADV4CandidateAppProjection.directive_id == directive_id,
        ADV4CandidateAppProjection.materializer_version == MATERIALIZER_VERSION,
    ))
    if projection is None:
        raise ADV4Error("not_found", "", "Applicability projection not found", http_status=404)
    reconstruct_applicability(db, projection)
    return projection


def _detect_projection_state(
    db: Session,
    projection: ADV4CandidateAppProjection,
) -> tuple[str, list[str], str | None, str | None, str | None]:
    reasons: list[str] = []
    candidate = verified_candidate(db, projection.proposal_id)
    causing_lifecycle_event_id: str | None = None
    try:
        _verify_live_evidence(db, candidate)
    except ADV4Error:
        reasons.append("evidence_invalidated")
        binding = db.scalar(select(ADV4CandidateEvidenceBinding).where(
            ADV4CandidateEvidenceBinding.proposal_id == candidate.id
        ).order_by(ADV4CandidateEvidenceBinding.fragment_id))
        if binding is not None:
            causing = db.scalar(select(ADEvidenceFragmentLifecycleEvent).where(
                ADEvidenceFragmentLifecycleEvent.fragment_id == binding.fragment_id,
                ADEvidenceFragmentLifecycleEvent.id != binding.admitted_event_id,
            ).order_by(ADEvidenceFragmentLifecycleEvent.sequence_number.desc()))
            causing_lifecycle_event_id = causing.id if causing is not None else None
    relation = db.scalar(select(ADV4CandidateSubmissionRelationship).where(
        ADV4CandidateSubmissionRelationship.predecessor_proposal_id == projection.proposal_id
    ).order_by(ADV4CandidateSubmissionRelationship.created_at, ADV4CandidateSubmissionRelationship.id))
    if relation is not None:
        reasons.append("candidate_corrected_or_replaced")
    dependency = db.scalar(select(ADV4CandidateAppChangeDependency).where(
        ADV4CandidateAppChangeDependency.projection_id == projection.id,
        ADV4CandidateAppChangeDependency.dependency_kind == "incoming_supersession_signal",
        ADV4CandidateAppChangeDependency.resolution_state == "resolved_candidate",
    ).order_by(ADV4CandidateAppChangeDependency.id))
    if dependency is not None:
        reasons.append("candidate_supersession_signal")
    return (
        "candidate_stale" if reasons else "candidate_verified",
        reasons,
        relation.id if relation is not None else None,
        causing_lifecycle_event_id,
        dependency.id if dependency is not None else None,
    )


def projection_state(db: Session, projection: ADV4CandidateAppProjection) -> tuple[str, list[str]]:
    """Detect current derived state without mutating rows or appending events."""
    state, reasons, _, _, _ = _detect_projection_state(db, projection)
    return state, reasons


def _repair_stale_projection_on_materialization(
    db: Session,
    projection: ADV4CandidateAppProjection,
) -> None:
    """Append deterministic repair only inside the authorized materialization POST."""
    _, reasons, relationship_id, lifecycle_event_id, dependency_id = _detect_projection_state(db, projection)
    if not reasons:
        return
    _repair_stale_projection(
        db,
        projection,
        reasons,
        causing_relationship_id=relationship_id,
        causing_lifecycle_event_id=lifecycle_event_id,
        causing_dependency_id=dependency_id,
    )


def _repair_stale_projection(
    db: Session,
    projection: ADV4CandidateAppProjection,
    reasons: list[str],
    *,
    causing_relationship_id: str | None,
    causing_lifecycle_event_id: str | None,
    causing_dependency_id: str | None,
) -> None:
    db.scalar(select(ADV4CandidateAppProjection).where(
        ADV4CandidateAppProjection.id == projection.id
    ).with_for_update())
    prior = db.scalar(select(ADV4CandidateAppProjectionEvent).where(
        ADV4CandidateAppProjectionEvent.projection_id == projection.id,
        ADV4CandidateAppProjectionEvent.event_type == "stale_marked",
    ))
    if prior is not None:
        return
    last = db.scalar(select(ADV4CandidateAppProjectionEvent).where(
        ADV4CandidateAppProjectionEvent.projection_id == projection.id
    ).order_by(ADV4CandidateAppProjectionEvent.sequence_number.desc()).limit(1))
    if last is None:
        raise ADV4Error("projection_integrity", "", "Projection event root is missing", http_status=409)
    sequence = last.sequence_number + 1
    event_value = {
        "version": "ad-v4-applicability-event-v2", "eventType": "stale_marked",
        "projectionId": projection.id, "proposalId": projection.proposal_id,
        "sequence": str(sequence), "reasons": sorted(reasons),
        "cause": {
            "kind": (
                "candidate_relationship" if causing_relationship_id is not None
                else "supersession_dependency" if causing_dependency_id is not None
                else "evidence_lifecycle"
            ),
            "id": causing_relationship_id or causing_dependency_id or causing_lifecycle_event_id,
        },
        "predecessorEventHash": last.event_hash,
    }
    event_bytes = canonical_bytes(event_value, CANONICALIZATION_VERSION_V2)
    event_hash = hashlib.sha256(EVENT_DOMAIN + event_bytes).hexdigest()
    event_id, _ = _row_id("avz", "projection-event", {
        "projectionId": projection.id, "eventHash": event_hash,
    })
    db.add(ADV4CandidateAppProjectionEvent(
        id=event_id, projection_id=projection.id, proposal_id=projection.proposal_id,
        sequence_number=sequence, event_type="stale_marked",
        reason_code="multiple" if len(reasons) > 1 else reasons[0],
        causing_request_id=None,
        causing_relationship_id=causing_relationship_id,
        causing_lifecycle_event_id=(
            None if causing_relationship_id is not None or causing_dependency_id is not None
            else causing_lifecycle_event_id
        ),
        causing_dependency_id=(
            causing_dependency_id if causing_relationship_id is None else None
        ), predecessor_event_hash=last.event_hash,
        canonical_bytes=event_bytes, event_hash=event_hash, actor_kind="system_repair",
    ))
    db.flush()

```
### `backend/tests/test_ad_v4_applicability.py`

size=13437; sha256=31ee8d71b596673408b1be13e8488d128093843bf5e6db9dfe54be98c2b118b9; truncated=false

```text
from __future__ import annotations

import json

import pytest

from app.core.config import get_settings
from app.models.core import (
    ADV4CandidateAppDatum,
    ADV4CandidateAppProjectionEvent,
    ADV4CandidateAppProjection,
    ADV4CandidateAppSemanticNode,
    ADV4FeatureGate,
    ADTargetApplicability,
)
from conftest import TEST_PASSWORD, login
from test_ad_v4_api import _envelope, _headers, _seed_candidate_source


def _enable(monkeypatch, db, *, validator: bool, materializer: bool) -> None:
    monkeypatch.setenv("PAPRNAV_AD_V4_VALIDATOR2_WRITES_ENABLED", "true" if validator else "false")
    monkeypatch.setenv("PAPRNAV_AD_V4_SLICE3A_ROUTES_ENABLED", "true" if materializer else "false")
    get_settings.cache_clear()
    db.add_all([
        ADV4FeatureGate(gate_key="validator2_write_enabled", enabled=validator, changed_by="test"),
        ADV4FeatureGate(gate_key="materializer3a_enabled", enabled=materializer, changed_by="test"),
    ])
    db.commit()


def test_v2_candidate_materialize_retry_and_reconstruct(client, db_session, monkeypatch) -> None:
    admin, membership, directive, fragment = _seed_candidate_source(db_session)
    _enable(monkeypatch, db_session, validator=True, materializer=True)
    login(client, admin.email)
    envelope = _envelope(directive, fragment)
    raw = json.dumps(envelope, separators=(",", ":")).encode()
    candidate_response = client.post(
        f"/api/v1/ads/directives/{directive.id}/v4/candidate-proposals",
        content=raw,
        headers=_headers(membership.id, "v2-candidate"),
    )
    assert candidate_response.status_code == 201, candidate_response.text
    candidate = candidate_response.json()
    assert candidate["validatorVersion"] == "paprnav-ad-v4-validator-2"
    assert candidate["canonicalizationVersion"] == "paprnav-ad-v4-c14n-2"

    path = f"/api/v1/ads/directives/{directive.id}/v4/candidate-proposals/{candidate['proposalId']}/applicability-projection"
    headers = {"Idempotency-Key": "materialize-one", "Paprnav-Acting-Membership-Id": membership.id}
    created = client.post(path, headers=headers)
    assert created.status_code == 201, created.text
    body = created.json()
    assert body["gate"] == "candidate_only"
    assert body["projectionState"] == "candidate_verified"
    assert body["identityMappingCount"] == 0

    retry = client.post(path, headers=headers)
    assert retry.status_code == 200, retry.text
    assert retry.json()["projectionId"] == body["projectionId"]
    assert retry.json()["idempotentRetry"] is True

    audit_headers = {"Paprnav-Acting-Membership-Id": membership.id}
    detail = client.get(path, headers=audit_headers)
    assert detail.status_code == 200, detail.text
    reconstruction = client.get(f"{path}/reconstruction", headers=audit_headers)
    assert reconstruction.status_code == 200, reconstruction.text
    assert reconstruction.json()["canonicalApplicability"] == {
        key: envelope["proposal"][key]
        for key in ("productScopes", "conditionDefinitions", "applicabilityRules", "applicabilitySearchHints")
    }
    assert db_session.query(ADV4CandidateAppProjection).count() == 1
    assert db_session.query(ADV4CandidateAppDatum).count() > 0
    assert db_session.query(ADV4CandidateAppSemanticNode).count() == 3


def test_feature_gate_matrix_preexisting_candidate(client, db_session, monkeypatch) -> None:
    admin, membership, directive, fragment = _seed_candidate_source(db_session)
    _enable(monkeypatch, db_session, validator=True, materializer=True)
    login(client, admin.email)
    raw = json.dumps(_envelope(directive, fragment), separators=(",", ":")).encode()
    candidate = client.post(
        f"/api/v1/ads/directives/{directive.id}/v4/candidate-proposals",
        content=raw,
        headers=_headers(membership.id, "v2-preexisting"),
    ).json()
    db_session.query(ADV4FeatureGate).filter_by(gate_key="validator2_write_enabled").update({"enabled": False})
    db_session.commit()
    path = f"/api/v1/ads/directives/{directive.id}/v4/candidate-proposals/{candidate['proposalId']}/applicability-projection"
    denied = client.post(path, headers={"Idempotency-Key": "disabled", "Paprnav-Acting-Membership-Id": membership.id})
    assert denied.status_code == 409
    assert denied.json()["detail"]["code"] == "validator2_write_gate_disabled"
    assert db_session.query(ADV4CandidateAppProjection).count() == 0


def test_v2_rejects_known_unknown_sentinel(db_session, monkeypatch) -> None:
    admin, membership, directive, fragment = _seed_candidate_source(db_session)
    _enable(monkeypatch, db_session, validator=True, materializer=True)
    envelope = _envelope(directive, fragment)
    envelope["proposal"]["conditionDefinitions"] = [{
        "conditionKey": "condition-unknown",
        "conditionType": "reviewed_manual_predicate",
        "operator": "requires_review",
        "subject": {"attributeKey": "source-status", "attributeValue": {"state": "known", "value": "unknown_requires_compliance", "evidenceKeys": ["ev-official"]}},
        "temporalBasis": {"kind": "at_applicability_evaluation"},
        "evidenceKeys": ["ev-official"],
    }]
    envelope["proposal"]["applicabilityRules"][0]["conditionExpression"] = {"nodeType": "predicate_ref", "conditionKey": "condition-unknown"}
    from app.services.ad_v4_candidates import ADV4Error, parse_v4_request_bytes, store_v4_candidate
    parsed = parse_v4_request_bytes(json.dumps(envelope, separators=(",", ":")).encode())
    try:
        store_v4_candidate(db_session, directive_id=directive.id, parsed=parsed, actor=admin, membership_id=membership.id, idempotency_key="sentinel")
    except ADV4Error as exc:
        assert exc.code == "semantic_unknown_sentinel"
    else:
        raise AssertionError("validator-2 accepted semantic unknown sentinel")


@pytest.mark.parametrize(
    ("validator_app", "materializer_app", "validator_db", "materializer_db", "expected"),
    [
        (False, True, True, True, "validator2_write_gate_disabled"),
        (True, False, True, True, "capability_disabled"),
        (True, True, False, True, "validator2_write_gate_disabled"),
        (True, True, True, False, "materializer3a_gate_disabled"),
    ],
)
def test_materializer_requires_all_application_and_database_gates(
    client, db_session, monkeypatch,
    validator_app, materializer_app, validator_db, materializer_db, expected,
) -> None:
    admin, membership, directive, fragment = _seed_candidate_source(db_session)
    _enable(monkeypatch, db_session, validator=True, materializer=True)
    login(client, admin.email)
    candidate = client.post(
        f"/api/v1/ads/directives/{directive.id}/v4/candidate-proposals",
        content=json.dumps(_envelope(directive, fragment), separators=(",", ":")).encode(),
        headers=_headers(membership.id, "gate-parent"),
    ).json()
    monkeypatch.setenv("PAPRNAV_AD_V4_VALIDATOR2_WRITES_ENABLED", "true" if validator_app else "false")
    monkeypatch.setenv("PAPRNAV_AD_V4_SLICE3A_ROUTES_ENABLED", "true" if materializer_app else "false")
    get_settings.cache_clear()
    db_session.query(ADV4FeatureGate).filter_by(gate_key="validator2_write_enabled").update({"enabled": validator_db})
    db_session.query(ADV4FeatureGate).filter_by(gate_key="materializer3a_enabled").update({"enabled": materializer_db})
    db_session.commit()
    response = client.post(
        f"/api/v1/ads/directives/{directive.id}/v4/candidate-proposals/{candidate['proposalId']}/applicability-projection",
        headers={"Idempotency-Key": "gate-attempt", "Paprnav-Acting-Membership-Id": membership.id},
    )
    assert response.status_code in {404, 409}
    assert response.json()["detail"]["code"] == expected
    assert db_session.query(ADV4CandidateAppProjection).count() == 0


def test_projection_audit_requires_exact_membership_and_does_not_feed_v3(client, db_session, monkeypatch) -> None:
    admin, membership, directive, fragment = _seed_candidate_source(db_session)
    _enable(monkeypatch, db_session, validator=True, materializer=True)
    login(client, admin.email)
    candidate = client.post(
        f"/api/v1/ads/directives/{directive.id}/v4/candidate-proposals",
        content=json.dumps(_envelope(directive, fragment), separators=(",", ":")).encode(),
        headers=_headers(membership.id, "audit-parent"),
    ).json()
    path = f"/api/v1/ads/directives/{directive.id}/v4/candidate-proposals/{candidate['proposalId']}/applicability-projection"
    assert client.post(path, headers={"Idempotency-Key": "audit-create", "Paprnav-Acting-Membership-Id": membership.id}).status_code == 201
    event_count = db_session.query(ADV4CandidateAppProjectionEvent).count()
    assert client.get(path).status_code == 422
    assert client.get(path, headers={"Paprnav-Acting-Membership-Id": "mem_missing"}).status_code == 403
    assert client.get(path, headers={"Paprnav-Acting-Membership-Id": membership.id}).status_code == 200
    reconstruction = client.get(
        f"{path}/reconstruction",
        headers={"Paprnav-Acting-Membership-Id": membership.id},
    )
    assert reconstruction.status_code == 200
    listing = client.get(
        f"/api/v1/ads/directives/{directive.id}/v4/applicability-projections?limit=1&offset=0",
        headers={"Paprnav-Acting-Membership-Id": membership.id},
    )
    assert listing.status_code == 200
    assert listing.json()["count"] == listing.json()["total"] == 1
    assert db_session.query(ADV4CandidateAppProjectionEvent).count() == event_count
    assert db_session.query(ADTargetApplicability).count() == 0


def test_validator1_candidate_remains_readable_but_is_not_materializable(client, db_session, monkeypatch) -> None:
    from app.services.ad_v4_candidates import VALIDATOR_VERSION

    admin, membership, directive, fragment = _seed_candidate_source(db_session)
    _enable(monkeypatch, db_session, validator=True, materializer=True)
    envelope = _envelope(directive, fragment)
    from app.services.ad_v4_candidates import parse_v4_request_bytes, store_v4_candidate
    stored = store_v4_candidate(
        db_session, directive_id=directive.id,
        parsed=parse_v4_request_bytes(json.dumps(envelope, separators=(",", ":")).encode()),
        actor=admin, membership_id=membership.id, idempotency_key="legacy-v1",
        validator_version=VALIDATOR_VERSION,
    )
    db_session.commit()
    login(client, admin.email)
    response = client.post(
        f"/api/v1/ads/directives/{directive.id}/v4/candidate-proposals/{stored.proposal.id}/applicability-projection",
        headers={"Idempotency-Key": "legacy-refusal", "Paprnav-Acting-Membership-Id": membership.id},
    )
    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "predecessor_semantic_defect"


def test_all_90_condition_type_operator_pairs_are_unevaluated_and_reconstructable() -> None:
    from app.services.ad_v4_applicability import _flatten, _reconstruct_data
    from app.services.ad_v4_candidates import VALIDATOR_VERSION_V2, parse_v4_request_bytes, validate_v4_envelope

    condition_types = [
        "identity", "identifier_range", "installed_equipment", "modification_or_stc",
        "configuration_attribute", "temporal_overlap", "source_inclusion",
        "source_exclusion", "reviewed_manual_predicate",
    ]
    operators = [
        "identity_equals", "identity_in", "identifier_in_range", "is_installed",
        "is_not_installed", "equals", "overlaps", "includes", "excludes",
        "requires_review",
    ]
    represented = 0
    for condition_type in condition_types:
        for operator in operators:
            directive = type("Directive", (), {"id": "ad-condition-matrix", "ad_number": "2024-14-03"})()
            fragment = type("Fragment", (), {
                "id": "aef-condition-matrix", "fragment_hash": "f" * 64,
                "source_document_id": "asd-condition-matrix", "source_content_hash": "a" * 64,
            })()
            envelope = _envelope(directive, fragment)
            envelope["proposal"]["conditionDefinitions"] = [{
                "conditionKey": "condition-matrix", "conditionType": condition_type,
                "operator": operator,
                "subject": {"attributeKey": "matrix", "attributeValue": {"state": "known", "value": "source-observation", "evidenceKeys": ["ev-official"]}},
                "temporalBasis": {"kind": "at_applicability_evaluation"},
                "evidenceKeys": ["ev-official"],
            }]
            envelope["proposal"]["applicabilityRules"][0]["conditionExpression"] = {"nodeType": "predicate_ref", "conditionKey": "condition-matrix"}
            raw = json.dumps(envelope, separators=(",", ":")).encode()
            proposal, _ = validate_v4_envelope(parse_v4_request_bytes(raw), directive.id, validator_version=VALIDATOR_VERSION_V2)
            subtree = {key: proposal[key] for key in ("productScopes", "conditionDefinitions", "applicabilityRules", "applicabilitySearchHints")}
            semantic_rows, datum_rows, nodes = [], [], {}
            _flatten(subtree, pointer="", projection_id="avx-matrix", proposal_id="avp-matrix", parent_node_id=None, semantic_rows=semantic_rows, datum_rows=datum_rows, node_by_pointer=nodes)
            assert _reconstruct_data(datum_rows) == subtree
            assert not any(hasattr(row, "evaluation_result") for row in semantic_rows)
            represented += 1
    assert represented == 90

```
### `backend/tests/test_ad_v4_applicability_calibration.py`

size=13708; sha256=74bd5aacc1164e9c5c928645e30c965d56267e50c6ff5306748f9410ba2affa9; truncated=false

```text
from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from app.core.config import get_settings
from app.models.core import (
    ADV4CandidateAppChangeDependency,
    ADV4CandidateAppEvidenceLink,
    ADV4CandidateAppIdentityMapping,
    ADV4CandidateAppProjection,
    ADV4CandidateAppSemanticNode,
    ADV4CandidateCorrection,
    ADV4CandidateCorrectionEvidenceLink,
    ADV4CandidateCorrectionRef,
    ADV4CandidateCorrectionSemanticBinding,
    ADV4FeatureGate,
    AirworthinessDirective,
)
from app.services.ad_evidence import admit_evidence_fragment
from app.services.ad_v4_applicability import materialize_applicability, reconstruct_applicability
from app.services.ad_v4_candidates import (
    ADV4Error,
    CANONICALIZATION_VERSION_V2,
    VALIDATOR_VERSION,
    VALIDATOR_VERSION_V2,
    canonical_bytes,
    parse_v4_request_bytes,
    store_v4_candidate,
    validate_v4_envelope,
)
from conftest import add_membership, create_organization, create_user
from test_ad_v4_calibration import (
    SOURCES,
    _executable,
    _load_template,
    _packet_fragments,
    _retain_packet_sources,
)


def _known(value: str, evidence_key: str) -> dict:
    return {"state": "known", "value": value, "evidenceKeys": [evidence_key]}


def _member(key: str, designation: str, manufacturer: str, evidence_key: str) -> dict:
    return {
        "memberKey": key,
        "designationKind": "model",
        "sourceDesignation": designation,
        "manufacturer": _known(manufacturer, evidence_key),
        "evidenceKeys": [evidence_key],
    }


def validator2_calibration_envelope(packet_key: str, envelope: dict) -> dict:
    """Test fixture transform approved by Slice-3A; retained evidence is unchanged."""
    value = copy.deepcopy(envelope)
    proposal = value["proposal"]
    conditions = {item["conditionKey"]: item for item in proposal["conditionDefinitions"]}
    if packet_key == "1998-17-11":
        conditions["condition-provenance-unknown"]["subject"]["attributeValue"] = {
            "state": "unknown",
            "reason": "not_observed",
            "temporalScope": {"kind": "at_applicability_evaluation"},
            "evidenceKeys": ["ev-unknown-provenance"],
        }
    elif packet_key == "2002-13-04":
        group_specs = {
            "condition-magneto-installed": (
                "6314,6324,6364", "Unison Industries (Slick)",
                ["6314", "6324", "6364"], "ev-applicability-conflict",
            ),
            "condition-family-a": (
                "C-125,C145,O-300,IO-360,TSIO-360", "Teledyne Continental Motors (TCM)",
                ["C-125", "C145", "O-300", "IO-360", "TSIO-360"], "ev-family-a",
            ),
            "condition-family-b": (
                "LTSIO-520-AE", "Teledyne Continental Motors (TCM)",
                ["LTSIO-520-AE"], "ev-family-b",
            ),
        }
        for condition_key, (display, manufacturer, designations, evidence_key) in group_specs.items():
            subject = conditions[condition_key]["subject"]
            subject.pop("modelOrSeries", None)
            subject["designationGroup"] = {
                "groupKey": f"group-{condition_key.removeprefix('condition-')}",
                "sourceDisplayText": _known(display, evidence_key),
                "association": "any_member" if len(designations) > 1 else "source_group",
                "members": [
                    _member(f"member-{condition_key.removeprefix('condition-')}-{index}", item, manufacturer, evidence_key)
                    for index, item in enumerate(designations, start=1)
                ],
                "evidenceKeys": [evidence_key],
            }
        evidence_key = "ev-applicability-conflict"
        groups = [
            ("cessna", "Cessna", ["170", "170A", "170B", "172", "172XP", "336", "337", "T303"]),
            ("beagle", "Beagle", ["B242-C"]),
            ("cirrus", "Cirrus", ["SR20", "SR22"]),
            ("globe-swift", "Globe Swift", ["GC-1A", "GC-1B"]),
            ("maule", "Maule", ["M4"]),
            ("piper", "Piper", ["PA-28R-201T", "PA-34"]),
            ("reims-cessna", "Reims (Cessna)", ["FA172", "F337", "FR172"]),
        ]
        manufacturer_groups = []
        for group_key, manufacturer, models in groups:
            members = [
                _member(f"member-{group_key}-{index}", model, manufacturer, evidence_key)
                for index, model in enumerate(models, start=1)
            ]
            if group_key == "cessna":
                members.append({
                    "memberKey": "member-cessna-series-172a-through-172h",
                    "designationKind": "series_expression",
                    "expressionText": "172A through 172H",
                    "evaluationState": "unknown",
                    "reason": "unsupported_expression",
                    "manufacturer": _known(manufacturer, evidence_key),
                    "evidenceKeys": [evidence_key],
                })
            manufacturer_groups.append({
                "groupKey": f"hint-group-{group_key}",
                "manufacturer": _known(manufacturer, evidence_key),
                "association": "paired",
                "members": members,
                "evidenceKeys": [evidence_key],
            })
        proposal["applicabilitySearchHints"] = [{
            "hintKey": "hint-airframes",
            "productRole": "airframe",
            "sourceDisplayText": _known(
                "These engines are used on, but not limited to Cessna, Beagle, Cirrus, Globe Swift, Maule, Piper, and Reims (Cessna) airplanes.",
                evidence_key,
            ),
            "manufacturerModelGroups": manufacturer_groups,
            "controlling": False,
            "exhaustive": False,
            "evidenceKeys": [evidence_key],
        }]
    elif packet_key == "2024-14-03":
        evidence_key = "ev-applicability"
        subject = conditions["condition-gfc500-gsa28-stc"]["subject"]
        subject.pop("modelOrSeries")
        subject["designationGroup"] = {
            "groupKey": "group-gfc500-gsa28",
            "sourceDisplayText": _known("GFC 500 and GSA 28", evidence_key),
            "association": "all_members",
            "members": [
                _member("member-gfc500", "GFC 500", "Garmin", evidence_key),
                _member("member-gsa28", "GSA 28", "Garmin", evidence_key),
            ],
            "evidenceKeys": [evidence_key],
        }
    return value


def _enable_v2(monkeypatch, db_session) -> None:
    monkeypatch.setenv("PAPRNAV_AD_V4_VALIDATOR2_WRITES_ENABLED", "true")
    monkeypatch.setenv("PAPRNAV_AD_V4_SLICE3A_ROUTES_ENABLED", "true")
    get_settings.cache_clear()
    db_session.add_all([
        ADV4FeatureGate(gate_key="validator2_write_enabled", enabled=True, changed_by="calibration"),
        ADV4FeatureGate(gate_key="materializer3a_enabled", enabled=True, changed_by="calibration"),
    ])
    db_session.flush()


@pytest.mark.parametrize("packet", SOURCES["packets"], ids=lambda item: item["packet"])
def test_validator2_five_packet_schema_and_canonical_determinism(packet):
    directive_id = "ad-" + packet["packet"]
    original = _executable(packet, _load_template(packet))
    corrected = validator2_calibration_envelope(packet["packet"], original)
    parsed = parse_v4_request_bytes(json.dumps(corrected, ensure_ascii=False, separators=(",", ":")).encode())
    proposal, _ = validate_v4_envelope(parsed, directive_id, validator_version=VALIDATOR_VERSION_V2)
    expected = canonical_bytes(proposal, CANONICALIZATION_VERSION_V2)
    reversed_proposal = copy.deepcopy(proposal)
    reversed_proposal["productScopes"].reverse()
    assert canonical_bytes(reversed_proposal, CANONICALIZATION_VERSION_V2) == expected
    if packet["packet"] == "1998-17-11":
        assert original["proposal"]["conditionDefinitions"][1]["subject"]["attributeValue"]["value"] == "unknown_requires_compliance"
        legacy, _ = validate_v4_envelope(
            parse_v4_request_bytes(json.dumps(original, separators=(",", ":")).encode()),
            directive_id,
            validator_version=VALIDATOR_VERSION,
        )
        assert canonical_bytes(legacy) == canonical_bytes(original["proposal"])


@pytest.mark.parametrize("packet", SOURCES["packets"], ids=lambda item: item["packet"])
def test_validator2_five_packet_real_evidence_materialization_roundtrip(
    packet, db_session, tmp_path: Path, monkeypatch,
):
    _enable_v2(monkeypatch, db_session)
    storage_root = tmp_path / "retained-evidence"
    monkeypatch.setenv("PAPRNAV_LOCAL_STORAGE_PATH", str(storage_root))
    get_settings.cache_clear()
    actor = create_user(db_session, f"v2-{packet['packet']}@example.test", "V2 Calibration Admin")
    organization = create_organization(db_session, f"V2 Calibration {packet['packet']}", "platform")
    membership = add_membership(db_session, organization, actor, "platform_admin")
    directive = AirworthinessDirective(ad_number=packet["adNumber"], title="", status="candidate", source_content_hash=packet["documents"][0]["sha256"])
    db_session.add(directive)
    db_session.flush()
    retained = _retain_packet_sources(db_session, packet, directive, storage_root)
    db_session.expire(directive, ["publications"])
    admitted = {}
    for item in _packet_fragments(packet["packet"]).values():
        document = retained[item["sourceKey"]]
        locators = item.get("locators", {})
        fragment, _ = admit_evidence_fragment(
            db_session, directive_id=directive.id, source_document_id=document.id,
            page_number=int(item["pageNumber"]), expected_source_content_hash=document.content_hash,
            expected_page_text_hash=item["pageTextHash"], character_start=int(item["characterStart"]),
            character_end=int(item["characterEnd"]), actor=actor, reason="validator-2 calibration",
            paragraph_locator=locators.get("paragraph"), table_locator=locators.get("table"),
            row_locator=locators.get("row"), note_locator=locators.get("note"),
        )
        admitted[item["evidenceKey"]] = fragment
    envelope = validator2_calibration_envelope(packet["packet"], _executable(
        packet, _load_template(packet), admitted_fragments=admitted,
        retained_documents=retained, directive_id=directive.id,
    ))
    stored = store_v4_candidate(
        db_session, directive_id=directive.id,
        parsed=parse_v4_request_bytes(json.dumps(envelope, ensure_ascii=False, separators=(",", ":")).encode()),
        actor=actor, membership_id=membership.id, idempotency_key="v2-calibration",
        validator_version=VALIDATOR_VERSION_V2,
    )
    result = materialize_applicability(
        db_session, directive_id=directive.id, proposal_id=stored.proposal.id,
        actor=actor, membership_id=membership.id, idempotency_key="materialize-calibration",
    )
    reconstructed = reconstruct_applicability(db_session, result.projection)
    assert canonical_bytes(reconstructed, CANONICALIZATION_VERSION_V2) == canonical_bytes(
        {key: envelope["proposal"][key] for key in ("productScopes", "conditionDefinitions", "applicabilityRules", "applicabilitySearchHints")},
        CANONICALIZATION_VERSION_V2,
    )
    nodes = db_session.query(ADV4CandidateAppSemanticNode).all()
    assert len([node for node in nodes if node.node_type == "product_scope"]) == len(envelope["proposal"]["productScopes"])
    model_count = sum(len(scope["modelScope"].get("sourceDesignations", [])) for scope in envelope["proposal"]["productScopes"])
    assert db_session.query(ADV4CandidateAppIdentityMapping).filter_by(identity_kind="model", normalization_origin="no_normalized_identity").count() == model_count
    assert db_session.query(ADV4CandidateAppEvidenceLink).join(
        ADV4CandidateAppSemanticNode,
        ADV4CandidateAppEvidenceLink.semantic_node_id == ADV4CandidateAppSemanticNode.id,
    ).filter(ADV4CandidateAppSemanticNode.node_type == "designation_value").count() == 0
    if packet["packet"] == "2024-14-03":
        assert model_count == 182
    elif packet["packet"] == "2011-10-09":
        assert model_count == 224
        dependency = db_session.query(ADV4CandidateAppChangeDependency).one()
        assert dependency.successor_ad_number == packet["adNumber"]
        assert dependency.resolution_state == "unresolved" and dependency.target_projection_id is None
    elif packet["packet"] == "2002-13-04":
        hint = reconstructed["applicabilitySearchHints"][0]
        members = [member for group in hint["manufacturerModelGroups"] for member in group["members"]]
        assert sum(member["designationKind"] == "model" for member in members) == 19
        assert [member["expressionText"] for member in members if member["designationKind"] == "series_expression"] == ["172A through 172H"]
        assert not {"172B", "172H"}.intersection(member.get("sourceDesignation") for member in members)
    elif packet["packet"] == "2008-26-10":
        correction = db_session.query(ADV4CandidateCorrection).one()
        assert correction.expected_ref_count == 2 and correction.expected_evidence_count == 2
        assert db_session.query(ADV4CandidateCorrectionRef).count() == 2
        assert db_session.query(ADV4CandidateCorrectionSemanticBinding).count() == 1
        assert db_session.query(ADV4CandidateCorrectionEvidenceLink).count() == 2
        missing_link = db_session.query(ADV4CandidateCorrectionEvidenceLink).first()
        db_session.delete(missing_link)
        db_session.flush()
        with pytest.raises(ADV4Error, match="Correction foundation"):
            reconstruct_applicability(db_session, result.projection)

```
### `backend/tests/test_ad_v4_applicability_postgres.py`

size=27935; sha256=3e300ebeb4c192c1a3ee4f1fb79314321acda34bf5f42bb2f87a41887d8ccbe0; truncated=false

```text
from __future__ import annotations

import json
import hashlib
import os
import subprocess
import sys
import threading
from concurrent.futures import ThreadPoolExecutor

import pytest
from sqlalchemy import create_engine, select, text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings
from app.models.core import (
    ADV4CandidateAppProjection,
    ADV4CandidateAppChangeDependency,
    ADV4CandidateAppProjectionEvent,
    ADV4CandidateAppSemanticNode,
    ADV4CandidateProposal,
    ADV4CandidateCorrection,
    User,
)
from app.services.ad_v4_applicability import EVENT_DOMAIN, materialize_applicability, reconstruct_applicability
from app.services.ad_v4_candidates import VALIDATOR_VERSION, VALIDATOR_VERSION_V2, store_v4_candidate
from app.services.ad_v4_candidates import CANONICALIZATION_VERSION_V2, canonical_bytes
from test_ad_v4_postgres import _request, _seed


POSTGRES_URL = os.getenv("PAPRNAV_TEST_POSTGRES_URL")
pytestmark = pytest.mark.skipif(not POSTGRES_URL, reason="PAPRNAV_TEST_POSTGRES_URL required")


def _alembic(*args: str) -> subprocess.CompletedProcess[str]:
    environment = os.environ.copy()
    environment["DATABASE_URL"] = POSTGRES_URL or ""
    return subprocess.run(
        [sys.executable, "-m", "alembic", *args], cwd=os.path.dirname(os.path.dirname(__file__)),
        env=environment, text=True, capture_output=True, timeout=25, check=False,
    )


def _engine():
    return create_engine(
        POSTGRES_URL,
        pool_pre_ping=True,
        pool_timeout=5,
        connect_args={"connect_timeout": 5, "options": "-c statement_timeout=10000 -c lock_timeout=5000 -c idle_in_transaction_session_timeout=15000"},
    )


def _enable(db: Session) -> None:
    db.execute(text("SELECT paprnav_set_v4_feature_gate('validator2_write_enabled',true,'postgres-test')"))
    db.execute(text("SELECT paprnav_set_v4_feature_gate('materializer3a_enabled',true,'postgres-test')"))
    db.commit()
    os.environ["PAPRNAV_AD_V4_VALIDATOR2_WRITES_ENABLED"] = "true"
    os.environ["PAPRNAV_AD_V4_SLICE3A_ROUTES_ENABLED"] = "true"
    get_settings.cache_clear()


def _store(
    db: Session,
    *,
    validator_version: str,
    suffix: str,
    listed_designation: bool = False,
    ad_number: str = "2024-14-03",
    supersession_relations: list[dict] | None = None,
):
    user_id, membership_id, directive_id, document_id, source_hash, fragment_id, fragment_hash = _seed(
        db, ad_number=ad_number,
    )
    actor = db.get(User, user_id)
    stored = store_v4_candidate(
        db, directive_id=directive_id,
        parsed=_request(
            directive_id, document_id, source_hash, fragment_id, fragment_hash,
            decision_key=f"decision-{suffix}",
            listed_designation=listed_designation,
            ad_number=ad_number,
            supersession_relations=supersession_relations,
        ),
        actor=actor, membership_id=membership_id, idempotency_key=f"candidate-{suffix}",
        validator_version=validator_version,
    )
    db.commit()
    return user_id, membership_id, directive_id, stored.proposal.id


def _materialize_stored(
    db: Session,
    *,
    validator_version: str,
    suffix: str,
    ad_number: str = "2024-14-03",
    supersession_relations: list[dict] | None = None,
):
    user_id, membership_id, directive_id, proposal_id = _store(
        db,
        validator_version=validator_version,
        suffix=suffix,
        ad_number=ad_number,
        supersession_relations=supersession_relations,
    )
    result = materialize_applicability(
        db,
        directive_id=directive_id,
        proposal_id=proposal_id,
        actor=db.get(User, user_id),
        membership_id=membership_id,
        idempotency_key=f"materialize-{suffix}",
    )
    db.commit()
    return result.projection


def test_00_empty_upgrade_and_v1_only_downgrade_reupgrade() -> None:
    down = _alembic("downgrade", "20260901_0026")
    assert down.returncode == 0, down.stdout + down.stderr
    up = _alembic("upgrade", "20260907_0027")
    assert up.returncode == 0, up.stdout + up.stderr
    engine = _engine()
    with Session(engine) as db:
        _store(db, validator_version=VALIDATOR_VERSION, suffix="v1-only")
    down = _alembic("downgrade", "20260901_0026")
    assert down.returncode == 0, down.stdout + down.stderr
    up = _alembic("upgrade", "20260907_0027")
    assert up.returncode == 0, up.stdout + up.stderr
    with engine.connect() as connection:
        assert connection.scalar(text("SELECT count(*) FROM ad_v4_candidate_proposals WHERE validator_version='paprnav-ad-v4-validator-1'")) == 1
    engine.dispose()


def test_01_v2_empty_projection_downgrade_refusal_preserves_head() -> None:
    engine = _engine()
    with Session(engine) as db:
        _enable(db)
        _store(db, validator_version=VALIDATOR_VERSION_V2, suffix="v2-downgrade-refusal")
    down = _alembic("downgrade", "20260901_0026")
    assert down.returncode != 0
    with engine.connect() as connection:
        assert connection.scalar(text("SELECT version_num FROM alembic_version")) == "20260907_0027"
        assert connection.scalar(text("SELECT count(*) FROM ad_v4_candidate_app_projections")) == 0
    engine.dispose()


def test_02_projection_integrity_immutability_and_occupied_downgrade() -> None:
    engine = _engine()
    with Session(engine) as db:
        _enable(db)
        user_id, membership_id, directive_id, proposal_id = _store(db, validator_version=VALIDATOR_VERSION_V2, suffix="projection")
        result = materialize_applicability(
            db, directive_id=directive_id, proposal_id=proposal_id, actor=db.get(User, user_id),
            membership_id=membership_id, idempotency_key="materialize-projection",
        )
        db.commit()
        assert reconstruct_applicability(db, result.projection)["productScopes"]
        projection_id = result.projection.id
        with pytest.raises(DBAPIError):
            db.execute(text("UPDATE ad_v4_candidate_app_projections SET gate='released' WHERE id=:id"), {"id": projection_id})
            db.commit()
        db.rollback()
        with pytest.raises(DBAPIError):
            db.execute(text("""
              INSERT INTO ad_v4_candidate_app_projections
              SELECT 'avx_forged',repeat('f',64),proposal_id,directive_id,schema_version,
                     validator_version,canonicalization_version,repeat('0',64),evidence_binding_hash,
                     materializer_version,applicability_subtree_bytes,applicability_subtree_hash,
                     projection_canonical_bytes,projection_hash,gate,semantic_node_count,datum_count,
                     evidence_link_count,identity_mapping_count,now()
                FROM ad_v4_candidate_app_projections WHERE id=:id
            """), {"id": projection_id})
            db.commit()
        db.rollback()
        other = db.scalar(select(ADV4CandidateProposal).where(ADV4CandidateProposal.validator_version == VALIDATOR_VERSION))
        node = db.scalar(select(ADV4CandidateAppSemanticNode).where(ADV4CandidateAppSemanticNode.projection_id == projection_id))
        with pytest.raises(DBAPIError):
            db.execute(text("""
              INSERT INTO ad_v4_candidate_app_data
                (id,projection_id,proposal_id,semantic_node_id,json_pointer,parent_pointer,property_name,array_ordinal,value_kind,string_value,boolean_value,value_hash)
              VALUES ('avd_cross',:projection,:proposal,:node,'/forged','', 'forged',NULL,'string','x',NULL,repeat('0',64))
            """), {"projection": projection_id, "proposal": other.id, "node": node.id})
            db.commit()
        db.rollback()
    down = _alembic("downgrade", "20260901_0026")
    assert down.returncode != 0
    engine.dispose()


def test_03_concurrent_retry_and_gate_disable_serialize_without_partial_rows() -> None:
    engine = _engine()
    SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
    with SessionLocal() as db:
        _enable(db)
        user_id, membership_id, directive_id, proposal_id = _store(db, validator_version=VALIDATOR_VERSION_V2, suffix="concurrent")
    barrier = threading.Barrier(2)

    def write():
        with SessionLocal() as db:
            barrier.wait(timeout=5)
            value = materialize_applicability(
                db, directive_id=directive_id, proposal_id=proposal_id, actor=db.get(User, user_id),
                membership_id=membership_id, idempotency_key="same-materialization",
            )
            db.commit()
            return value.projection.id

    with ThreadPoolExecutor(max_workers=2) as pool:
        ids = [future.result(timeout=15) for future in [pool.submit(write), pool.submit(write)]]
    assert len(set(ids)) == 1
    with SessionLocal() as db:
        assert db.scalar(
            select(text("count(*)")).select_from(ADV4CandidateAppProjection).where(
                ADV4CandidateAppProjection.proposal_id == proposal_id
            )
        ) == 1
        db.execute(text("SELECT paprnav_set_v4_feature_gate('validator2_write_enabled',false,'postgres-test-disable')"))
        db.commit()
        with pytest.raises(Exception):
            materialize_applicability(
                db, directive_id=directive_id, proposal_id=proposal_id, actor=db.get(User, user_id),
                membership_id=membership_id, idempotency_key="disabled-after-existing",
            )
    engine.dispose()


def test_04_valid_projection_root_without_children_is_rejected_at_commit() -> None:
    engine = _engine()
    with Session(engine) as db:
        _enable(db)
        user_id, membership_id, directive_id, proposal_id = _store(
            db, validator_version=VALIDATOR_VERSION_V2, suffix="empty-graph",
        )
        result = materialize_applicability(
            db, directive_id=directive_id, proposal_id=proposal_id,
            actor=db.get(User, user_id), membership_id=membership_id,
            idempotency_key="capture-valid-root",
        )
        db.flush()
        root_values = {
            column.name: getattr(result.projection, column.name)
            for column in ADV4CandidateAppProjection.__table__.columns
        }
        db.rollback()

        db.execute(ADV4CandidateAppProjection.__table__.insert().values(**root_values))
        with pytest.raises(DBAPIError, match="relational graph is incomplete"):
            db.commit()
        db.rollback()
        assert db.get(ADV4CandidateAppProjection, root_values["id"]) is None
    engine.dispose()


def test_05_extra_relational_child_is_rejected_by_deferred_validation() -> None:
    engine = _engine()
    with Session(engine) as db:
        _enable(db)
        user_id, membership_id, directive_id, proposal_id = _store(
            db, validator_version=VALIDATOR_VERSION_V2, suffix="extra-child",
        )
        result = materialize_applicability(
            db, directive_id=directive_id, proposal_id=proposal_id,
            actor=db.get(User, user_id), membership_id=membership_id,
            idempotency_key="extra-child-projection",
        )
        db.execute(text("""
          INSERT INTO ad_v4_candidate_app_data
            (id,projection_id,proposal_id,semantic_node_id,json_pointer,
             parent_pointer,property_name,array_ordinal,value_kind,string_value,
             boolean_value,value_hash)
          VALUES
            ('avd_extra',:projection,:proposal,NULL,'/forged','',
             'forged',NULL,'string','forged',NULL,repeat('0',64))
        """), {"projection": result.projection.id, "proposal": proposal_id})
        with pytest.raises(DBAPIError, match="relational graph is incomplete"):
            db.execute(text("SET CONSTRAINTS ALL IMMEDIATE"))
        db.rollback()
    engine.dispose()


def test_06_forged_semantic_identity_is_rejected_by_deferred_validation() -> None:
    engine = _engine()
    with Session(engine) as db:
        _enable(db)
        user_id, membership_id, directive_id, proposal_id = _store(
            db, validator_version=VALIDATOR_VERSION_V2, suffix="semantic-forgery",
        )
        result = materialize_applicability(
            db, directive_id=directive_id, proposal_id=proposal_id,
            actor=db.get(User, user_id), membership_id=membership_id,
            idempotency_key="semantic-forgery-projection",
        )
        node = db.scalar(select(ADV4CandidateAppSemanticNode).where(
            ADV4CandidateAppSemanticNode.projection_id == result.projection.id
        ))
        projection_id = result.projection.id
        node_id = node.id
        db.commit()
        db.execute(text(
            "ALTER TABLE ad_v4_candidate_app_semantic_nodes "
            "DISABLE TRIGGER trg_ad_v4_candidate_app_semantic_nodes_immutable"
        ))
        db.execute(text(
            "UPDATE ad_v4_candidate_app_semantic_nodes SET node_key='forged' WHERE id=:id"
        ), {"id": node_id})
        with pytest.raises(DBAPIError, match="semantic node differs"):
            db.execute(
                text("SELECT paprnav_v4_candidate_app_require_complete(:projection)"),
                {"projection": projection_id},
            )
        db.rollback()
    engine.dispose()


def test_07_listed_designation_semantic_nodes_commit_and_verify() -> None:
    engine = _engine()
    with Session(engine) as db:
        _enable(db)
        user_id, membership_id, directive_id, proposal_id = _store(
            db, validator_version=VALIDATOR_VERSION_V2,
            suffix="listed-designation", listed_designation=True,
        )
        result = materialize_applicability(
            db, directive_id=directive_id, proposal_id=proposal_id,
            actor=db.get(User, user_id), membership_id=membership_id,
            idempotency_key="listed-designation-projection",
        )
        db.commit()
        assert db.scalar(select(text("count(*)")).select_from(
            ADV4CandidateAppSemanticNode
        ).where(
            ADV4CandidateAppSemanticNode.projection_id == result.projection.id,
            ADV4CandidateAppSemanticNode.node_type == "designation_value",
        )) == 2
        assert reconstruct_applicability(db, result.projection)["productScopes"][0]["modelScope"]["sourceDesignations"] == [
            "Model 100", "Model 200",
        ]
    engine.dispose()


def test_08_negative_correction_ordinal_is_rejected() -> None:
    engine = _engine()
    with Session(engine) as db:
        _enable(db)
        _, _, _, proposal_id = _store(
            db, validator_version=VALIDATOR_VERSION_V2, suffix="negative-correction-ordinal",
        )
        db.add(ADV4CandidateCorrection(
            id="avc_negative", identity_hash="a" * 64, proposal_id=proposal_id,
            correction_key="negative", correction_type="official_correction",
            original_document_ref_key="official-rule",
            correcting_document_ref_key="official-rule",
            original_document_identity_hash="b" * 64,
            correcting_document_identity_hash="b" * 64,
            canonical_hash="c" * 64, canonical_ordinal=-1,
            foundation_version="paprnav-ad-v4-correction-foundation-1",
            generation=1, expected_ref_count=0, expected_evidence_count=0,
        ))
        with pytest.raises(DBAPIError, match="ordinal_nonnegative"):
            db.flush()
        db.rollback()
    engine.dispose()


def test_09_exact_supersession_creates_target_local_cause_and_stale_event() -> None:
    engine = _engine()
    with Session(engine) as db:
        _enable(db)
        predecessor = _materialize_stored(
            db, validator_version=VALIDATOR_VERSION_V2,
            suffix="supersession-predecessor", ad_number="2020-01-01",
        )
        successor = _materialize_stored(
            db, validator_version=VALIDATOR_VERSION_V2,
            suffix="supersession-successor", ad_number="2024-14-03",
            supersession_relations=[{
                "relationType": "supersedes",
                "predecessorAdNumber": "2020-01-01",
                "successorAdNumber": "2024-14-03",
                "evidenceKeys": ["ev-official"],
            }],
        )
        outgoing = db.scalar(select(ADV4CandidateAppChangeDependency).where(
            ADV4CandidateAppChangeDependency.projection_id == successor.id,
            ADV4CandidateAppChangeDependency.dependency_kind == "outgoing_supersedes",
        ))
        incoming = db.scalar(select(ADV4CandidateAppChangeDependency).where(
            ADV4CandidateAppChangeDependency.projection_id == predecessor.id,
            ADV4CandidateAppChangeDependency.dependency_kind == "incoming_supersession_signal",
        ))
        event = db.scalar(select(ADV4CandidateAppProjectionEvent).where(
            ADV4CandidateAppProjectionEvent.projection_id == predecessor.id,
            ADV4CandidateAppProjectionEvent.event_type == "stale_marked",
        ))
        assert outgoing is not None and incoming is not None and event is not None
        assert outgoing.resolution_state == "resolved_candidate"
        assert outgoing.target_projection_id == predecessor.id
        assert incoming.source_dependency_id == outgoing.id
        assert event.causing_dependency_id == incoming.id
        assert event.reason_code == "candidate_supersession_signal"
        reconstruct_applicability(db, predecessor)
        reconstruct_applicability(db, successor)

        forged_value = {
            "version": "ad-v4-applicability-event-v2",
            "eventType": "stale_marked",
            "projectionId": predecessor.id,
            "proposalId": predecessor.proposal_id,
            "sequence": "2",
            "reasons": ["candidate_supersession_signal"],
            "cause": {"kind": "supersession_dependency", "id": outgoing.id},
            "predecessorEventHash": event.event_hash,
        }
        forged_bytes = canonical_bytes(forged_value, CANONICALIZATION_VERSION_V2)
        with pytest.raises(DBAPIError, match="event chain/envelope mismatch"):
            db.execute(text("""
              INSERT INTO ad_v4_candidate_app_projection_events
                (id,projection_id,proposal_id,sequence_number,event_type,reason_code,
                 causing_request_id,causing_relationship_id,causing_lifecycle_event_id,
                 causing_dependency_id,predecessor_event_hash,canonical_bytes,event_hash,actor_kind)
              VALUES
                ('avz_cross_projection_cause',:projection,:proposal,2,'stale_marked',
                 'candidate_supersession_signal',NULL,NULL,NULL,:dependency,:predecessor,
                 :canonical_bytes,:event_hash,'system_repair')
            """), {
                "projection": predecessor.id,
                "proposal": predecessor.proposal_id,
                "dependency": outgoing.id,
                "predecessor": event.event_hash,
                "canonical_bytes": forged_bytes,
                "event_hash": hashlib.sha256(EVENT_DOMAIN + forged_bytes).hexdigest(),
            })
            db.flush()
        db.rollback()
    engine.dispose()


def test_10_mismatched_successor_remains_unresolved_without_side_effect() -> None:
    engine = _engine()
    with Session(engine) as db:
        _enable(db)
        predecessor = _materialize_stored(
            db, validator_version=VALIDATOR_VERSION_V2,
            suffix="mismatch-predecessor", ad_number="2020-02-01",
        )
        successor = _materialize_stored(
            db, validator_version=VALIDATOR_VERSION_V2,
            suffix="mismatch-successor", ad_number="2024-14-03",
            supersession_relations=[{
                "relationType": "supersedes",
                "predecessorAdNumber": "2020-02-01",
                "successorAdNumber": "2025-01-01",
                "evidenceKeys": ["ev-official"],
            }],
        )
        outgoing = db.scalar(select(ADV4CandidateAppChangeDependency).where(
            ADV4CandidateAppChangeDependency.projection_id == successor.id,
        ))
        assert outgoing.resolution_state == "unresolved"
        assert outgoing.unresolved_reason == "successor_not_this_proposal"
        assert outgoing.target_projection_id is None
        assert db.scalar(select(text("count(*)")).select_from(ADV4CandidateAppChangeDependency).where(
            ADV4CandidateAppChangeDependency.projection_id == predecessor.id,
        )) == 0
        assert db.scalar(select(text("count(*)")).select_from(ADV4CandidateAppProjectionEvent).where(
            ADV4CandidateAppProjectionEvent.projection_id == predecessor.id,
            ADV4CandidateAppProjectionEvent.event_type == "stale_marked",
        )) == 0
    engine.dispose()


def test_11_ambiguous_predecessor_remains_ambiguous_without_side_effect() -> None:
    engine = _engine()
    with Session(engine) as db:
        _enable(db)
        first = _materialize_stored(
            db, validator_version=VALIDATOR_VERSION_V2,
            suffix="ambiguous-predecessor-a", ad_number="2020-03-01",
        )
        second = _materialize_stored(
            db, validator_version=VALIDATOR_VERSION_V2,
            suffix="ambiguous-predecessor-b", ad_number="2020-03-01",
        )
        successor = _materialize_stored(
            db, validator_version=VALIDATOR_VERSION_V2,
            suffix="ambiguous-successor", ad_number="2024-14-03",
            supersession_relations=[{
                "relationType": "supersedes",
                "predecessorAdNumber": "2020-03-01",
                "successorAdNumber": "2024-14-03",
                "evidenceKeys": ["ev-official"],
            }],
        )
        outgoing = db.scalar(select(ADV4CandidateAppChangeDependency).where(
            ADV4CandidateAppChangeDependency.projection_id == successor.id,
        ))
        assert outgoing.resolution_state == "ambiguous"
        assert outgoing.unresolved_reason == "multiple_predecessor_candidates"
        assert outgoing.target_projection_id is None
        for predecessor in (first, second):
            assert db.scalar(select(text("count(*)")).select_from(ADV4CandidateAppChangeDependency).where(
                ADV4CandidateAppChangeDependency.projection_id == predecessor.id,
            )) == 0
            assert db.scalar(select(text("count(*)")).select_from(ADV4CandidateAppProjectionEvent).where(
                ADV4CandidateAppProjectionEvent.projection_id == predecessor.id,
                ADV4CandidateAppProjectionEvent.event_type == "stale_marked",
            )) == 0
    engine.dispose()


def test_12_concurrent_second_predecessor_cannot_invalidate_unique_resolution() -> None:
    engine = _engine()
    SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
    with SessionLocal() as db:
        _enable(db)
        first = _materialize_stored(
            db, validator_version=VALIDATOR_VERSION_V2,
            suffix="race-predecessor-a", ad_number="2020-04-01",
        )
        p2_user, p2_membership, p2_directive, p2_proposal = _store(
            db, validator_version=VALIDATOR_VERSION_V2,
            suffix="race-predecessor-b", ad_number="2020-04-01",
        )
        s_user, s_membership, s_directive, s_proposal = _store(
            db, validator_version=VALIDATOR_VERSION_V2,
            suffix="race-successor", ad_number="2024-14-03",
            supersession_relations=[{
                "relationType": "supersedes",
                "predecessorAdNumber": "2020-04-01",
                "successorAdNumber": "2024-14-03",
                "evidenceKeys": ["ev-official"],
            }],
        )

    barrier = threading.Barrier(2)

    def materialize_one(user_id, membership_id, directive_id, proposal_id, key):
        with SessionLocal() as db:
            barrier.wait(timeout=5)
            try:
                result = materialize_applicability(
                    db, directive_id=directive_id, proposal_id=proposal_id,
                    actor=db.get(User, user_id), membership_id=membership_id,
                    idempotency_key=key,
                )
                db.commit()
                return ("committed", result.projection.id)
            except Exception as exc:
                db.rollback()
                return (getattr(exc, "code", type(exc).__name__), None)

    with ThreadPoolExecutor(max_workers=2) as pool:
        p2_future = pool.submit(
            materialize_one, p2_user, p2_membership, p2_directive, p2_proposal, "race-p2",
        )
        successor_future = pool.submit(
            materialize_one, s_user, s_membership, s_directive, s_proposal, "race-successor",
        )
        p2_result = p2_future.result(timeout=20)
        successor_result = successor_future.result(timeout=20)

    assert successor_result[0] == "committed"
    assert p2_result[0] in {"committed", "supersession_resolution_conflict"}
    with SessionLocal() as db:
        successor = db.get(ADV4CandidateAppProjection, successor_result[1])
        outgoing = db.scalar(select(ADV4CandidateAppChangeDependency).where(
            ADV4CandidateAppChangeDependency.projection_id == successor.id,
            ADV4CandidateAppChangeDependency.dependency_kind == "outgoing_supersedes",
        ))
        matching_predecessors = []
        for projection in db.scalars(select(ADV4CandidateAppProjection).where(
            ADV4CandidateAppProjection.id != successor.id
        )).all():
            candidate = db.get(ADV4CandidateProposal, projection.proposal_id)
            ad = candidate.parsed_json["directiveIdentity"]["adNumber"]
            if ad.get("state") == "known" and ad.get("value") == "2020-04-01":
                matching_predecessors.append(projection.id)
        if p2_result[0] == "committed":
            assert len(matching_predecessors) == 2
            assert outgoing.resolution_state == "ambiguous"
            assert outgoing.target_projection_id is None
        else:
            assert matching_predecessors == [first.id]
            assert outgoing.resolution_state == "resolved_candidate"
            assert outgoing.target_projection_id == first.id
    engine.dispose()


def test_13_direct_projection_insert_participates_in_database_ad_lock() -> None:
    engine = _engine()
    SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
    with SessionLocal() as db:
        _enable(db)
        user_id, membership_id, directive_id, proposal_id = _store(
            db, validator_version=VALIDATOR_VERSION_V2,
            suffix="direct-lock", ad_number="2030-01-01",
        )
        result = materialize_applicability(
            db, directive_id=directive_id, proposal_id=proposal_id,
            actor=db.get(User, user_id), membership_id=membership_id,
            idempotency_key="capture-direct-lock-root",
        )
        db.flush()
        root_values = {
            column.name: getattr(result.projection, column.name)
            for column in ADV4CandidateAppProjection.__table__.columns
        }
        db.rollback()

    ready = threading.Event()
    release = threading.Event()

    def hold_database_lock():
        with SessionLocal() as db:
            db.execute(
                text("SELECT paprnav_v4_lock_app_ad_numbers(:proposal)"),
                {"proposal": proposal_id},
            )
            ready.set()
            release.wait(timeout=5)
            db.rollback()

    with ThreadPoolExecutor(max_workers=1) as pool:
        holder = pool.submit(hold_database_lock)
        assert ready.wait(timeout=5)
        try:
            with SessionLocal() as db:
                db.execute(text("SET LOCAL lock_timeout='300ms'"))
                with pytest.raises(DBAPIError, match="lock timeout"):
                    db.execute(ADV4CandidateAppProjection.__table__.insert().values(**root_values))
                    db.flush()
                db.rollback()
        finally:
            release.set()
        holder.result(timeout=5)
    engine.dispose()

```
