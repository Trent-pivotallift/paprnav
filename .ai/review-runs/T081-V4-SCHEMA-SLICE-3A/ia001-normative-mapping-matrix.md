# T081 V4 Slice 3A — IA-001 Normative Mapping Matrix

Status: **pre-implementation design baseline; IA-001 remains open**  
Date: 2026-09-10  
Mapping contract: `paprnav-ad-v4-applicability-mapping-1`  
Canonical input: validator `paprnav-ad-v4-validator-2`, canonicalization
`paprnav-ad-v4-c14n-2`  
Scope: `{productScopes, conditionDefinitions, applicabilityRules,
applicabilitySearchHints}` only

This document replaces counterexample-led implementation with a single closed
mapping contract. It is normative for the remainder of IA-001, subject to an
independent design review before more schema or service code is changed. It
includes the already implemented source/product/designation family so its
rules can be compared with every unfinished family.

## 1. Common notation and invariants

Pointers below are RFC 6901 pointers relative to the four-field applicability
subtree. Array indices are indices **after** validator-2 canonicalization.
`i`, `j`, and `k` denote canonical zero-based ordinals.

`J(x)` is restricted-JCS canonical bytes under c14n-2. `H(x)` is SHA-256.
The common deterministic row function is:

```text
row(prefix, table, identity) =
  prefix + "_" + first32hex(H(ROW_DOMAIN || J({"table": table,
                                                  "identity": identity})))
```

Unless an exception is called out below, a semantic occurrence uses:

```text
node identity = {
  "projectionId": projection_id,
  "nodeType": node_type,
  "nodeKey": node_key,
  "pointer": source_pointer
}
semantic_node_id = row("avn", "semantic-node", node identity)
identity_hash = full hash used by row(...)
canonical_node_hash = H(J(the exact canonical value at source_pointer))
```

Every semantic node repeats the same non-null `projection_id` and `proposal_id`
as its projection. Its `parent_node_id`, type, key, pointer, ordinal, ID,
identity hash, and canonical-node hash are exact, not hints. Object-property
children use ordinal `0`; set/sequence members use their canonical array
ordinal.

Every typed owner uses `semantic_node_id` as its primary row identity unless a
different identity is explicitly listed. All same-projection relationships use
composite foreign keys carrying `(projection_id, proposal_id, node_id)`; a
single-column FK is insufficient.

### 1.1 Closed ordering rules

| Canonical collection | Kind | Canonical order |
| --- | --- | --- |
| `productScopes` | set | `scopeKey` |
| `conditionDefinitions` | set | `conditionKey` |
| `applicabilityRules` | set | `ruleKey` |
| `applicabilitySearchHints` | set | `hintKey` |
| designation `sourceDesignations` | set | canonical scalar bytes |
| designation `ranges` | set | `(lower, upper, lowerInclusive, upperInclusive, polarity)` |
| group `members` | set | `memberKey` |
| hint `manufacturerModelGroups` | set | `groupKey` |
| expression `operands` | sequence | source order, unchanged |
| rule `exclusionRuleKeys` | set | canonical scalar bytes |
| every `evidenceKeys` | set | canonical scalar bytes |

Every stored child collection has exact count, minimum/maximum ordinal, unique
ordinal, contiguous ordinal, exact canonical value at each ordinal, and no
extra rows. Zero-row optional collections are represented by zero rows, never
by a sentinel row or SQL `NULL` element.

### 1.2 Evidence and identity rules

An evidence-bearing semantic occurrence gets exactly one evidence-link row per
canonical key, in canonical key order. Link identity is
`row("avl", "evidence-link", {projectionId, nodeId, purpose, evidenceKey})`.
Each link binds the exact immutable Slice-2 candidate evidence binding through
`(proposal_id, candidate_binding_id, evidence_key)`. Non-evidence-bearing
nodes, expression nodes, designation values/ranges, and identity-mapping nodes
must have zero links.

An identity mapping never duplicates evidence links. It points to exactly one
`evidence_parent_node_id`, whose meaning is **context evidence owner**, not a
replacement for evidence on the source occurrence. The auditable support for a
mapping is the independently verified ordered pair
`(source-occurrence evidence, context-owner evidence)`. The first proves the
exact source spelling or normalized-identity assertion; the second proves the
canonical condition/group/scope context in which that occurrence participates.
Either set may differ from the other and neither may be silently substituted or
unioned into a new evidence-link set.

Mapping identity retains the already implemented and approved exact preimage
spelling:
`row("avi", "identity-mapping", {projectionId, kind, occurrence})`; its
semantic-node key and parent are the source
occurrence node ID, its pointer/hash/ordinal equal the source occurrence, and
it has exactly one `ad_v4_candidate_app_identity_mappings` owner.

The required identity golden vector is:

```text
identity payload:
  {"projectionId":"avp_example","kind":"model","occurrence":"avn_example"}
canonical row preimage after ROW_DOMAIN:
  {"identity":{"kind":"model","occurrence":"avn_example","projectionId":"avp_example"},"table":"identity-mapping"}
full identity hash:
  614f2232f10e1dfcf4ce68528b0b1357dd9de1a86ed07f5d3c698aca9578f836
row ID:
  avi_614f2232f10e1dfcf4ce68528b0b1357
```

Python, generated SQL, and read verification must reproduce that exact vector.
The key name `sourceOccurrenceNodeId` is forbidden in this version; changing a
preimage property name requires a new mapping-contract version and an explicit
migration/compatibility decision.

Origins remain:

| Origin | Required state | Required values | Forbidden values |
| --- | --- | --- | --- |
| `candidate_payload` | exact canonical `known|unknown|not_applicable` | known: normalized value, namespace `candidate`, version `1`; unknown/not-applicable: exact reason and temporal scope | known forbids reason/temporal; unknown/not-applicable forbid normalized value/namespace/version |
| `source_only` | `unknown` | reason `not_extracted`, temporal `directive_version` | normalized value/namespace/version |
| `no_normalized_identity` | `unknown` | reason `not_extracted`, temporal `directive_version` | normalized value/namespace/version |

All mappings have review state `unreviewed_candidate`. Equal strings at two
source occurrences produce two mappings. Serial numbers, part numbers, STC
numbers, arbitrary attribute values, and display text never receive identity
mappings.

The evidence pair for every mapping family is fixed as follows:

| Mapping family | Source-occurrence evidence | Context evidence owner | Required audit support |
| --- | --- | --- | --- |
| product manufacturer | P2 source assertion's exact canonical `normalizedIdentity.evidenceKeys` | P1 product scope | verify both ordered sets independently |
| listed model | no occurrence links; source is a scalar designation value | P5 designation scope | exact P5 set only |
| atomic condition manufacturer/modelOrSeries | C5 assertion evidence | C1 condition | verify both sets independently |
| condition member designation | C10/C11 member evidence | C8 designation group | verify both sets independently |
| condition member manufacturer | C12 assertion evidence | C8 designation group | verify both sets independently |
| hint-group manufacturer | H4 assertion evidence | H3 hint group | verify both sets independently |
| hint-member designation | H6/H7 member evidence | H3 hint group | verify both sets independently |
| hint-member manufacturer | H8 assertion evidence | H3 hint group | verify both sets independently |

The positive oracle deliberately assigns different evidence keys to occurrence
and context in every two-set row. Corruption tests swap the occurrence and
context parents/links, omit either side, and prove rejection. This establishes
that `evidence_parent_node_id` is contextual provenance while the occurrence
node retains its own source support.

### 1.3 Known-string assertion union

Every matrix row marked `VA(field)` creates a `value_assertion` semantic node
at the exact known-string object pointer, except the existing product
manufacturer special case described in P2. Its typed owner has:

| Canonical branch | Non-null columns | Null columns |
| --- | --- | --- |
| `state=known` | `state`, `value_type=text`, `text_value` | `reason`, `temporal_scope` |
| `state=unknown` | `state`, `value_type=text`, controlled `reason`, `temporal_scope` | `text_value` |
| `state=not_applicable` | `state`, `value_type=text`, exact free-text `reason`, `temporal_scope` | `text_value` |

The owner identity is `(parent_semantic_node_id, field_code)` and all columns
are required except the branch-null columns above. Its evidence purpose is the
purpose named in the matrix and its exact evidence set is the known-string
object's `evidenceKeys`.

## 2. Complete canonical occurrence-to-owner matrix

The `DB/read/tests` column uses test-vector IDs defined in section 4. `Exact`
means both the deferred PostgreSQL validator and the verified read compare the
complete expected tuple, count, IDs/hashes, parentage, evidence, and absence of
unlisted children; neither layer merely checks a subset.

### 2.1 Products, designations, and their identity mappings

| ID | Canonical path / branch | Semantic node `(type, key, parent, ordinal)` | Physical owner and row identity | Required/optional columns and child/evidence/identity rule | Python materialization | DB/read/tests |
| --- | --- | --- | --- | --- | --- | --- |
| P1 | `/productScopes/{i}` | `product_scope`, `scopeKey`, root, `i` | `app_product_scopes`; PK node ID; unique `(projection,scope_key)` | Required key/role and four property-presence codes. Manufacturer source/mapping nullable only when property absent. Exact evidence, purpose `scope_clause`. Exact 0/1 manufacturer and designation children according to presence. | Emit from canonical object; never infer absent fields. | Exact; T-PRODUCT, X-NODE, X-OWNER, X-EVIDENCE, X-CARDINALITY. |
| P2 | `/productScopes/{i}/manufacturer/sourceValue` when manufacturer property exists | `value_assertion`, pointer, P1, `0`; **existing special pointer is scalar source value** | `app_value_assertions`; PK node ID; unique `(P1,manufacturer)` | Fixed known/text/sourceValue; no reason/temporal. Evidence comes from sibling `normalizedIdentity.evidenceKeys`, purpose `identity_support`. Exactly one manufacturer mapping. | Preserve existing special case and reassign the scalar datum to this node. | Exact; T-PRODUCT, X-VALUE, X-EVIDENCE, X-IDENTITY. |
| P3 | P2 mapping, `normalizedIdentity.state=known` | `identity_mapping`, P2 node ID, P2, P2 ordinal | `app_identity_mappings`; deterministic `avi`; unique exact occurrence | `manufacturer/candidate_payload/known`, exact normalized value, namespace/version; evidence parent P1; zero own evidence. | Emit only from this exact occurrence. | Exact; X-IDENTITY, X-HASH. |
| P4 | P2 mapping, `normalizedIdentity.state=unknown|not_applicable` | same | same | `manufacturer/candidate_payload/{exact state}`; exact canonical reason and temporal scope; no normalized value/namespace/version; evidence parent P1. The discriminator and free-text not-applicable reason remain exact in typed reconstruction. `no_normalized_identity` is forbidden because the canonical property is present. | Emit the exact canonical normalized union without substituting `not_extracted`. | Exact; T-PRODUCT-UNION, X-IDENTITY, X-VALUE. |
| P5 | `/productScopes/{i}/{modelScope|serialScope|partNumberScope}` when property exists | `designation_scope`, full pointer, P1, `0` | `app_designation_scopes`; PK node; unique `(P1,field_kind)` | Required field kind, scope kind, evaluation state/contract. Branch-null columns below. Exact evidence, purpose `designation_scope`. | Emit one owner for each present property. | Exact; all T-DESIG-* and X-* generic vectors. |
| P6 | P5 `kind=all` | same | same | `series_expression`, `reason`, `temporal_scope` null; `unevaluated/none`; zero values and ranges. | Branch map only. | T-DESIG-ALL, X-UNION, X-CARDINALITY. |
| P7 | P5 `kind=listed` | same | same | branch-null fields null; `unevaluated/none`; one or more P11 values, zero ranges. | Emit canonical list children. | T-DESIG-LISTED, X-ORDER, X-CARDINALITY. |
| P8 | P5 `kind=series_expression` | same | same | exact expression non-null; reason/temporal null; `unknown/unsupported_expression`; zero values/ranges. No executable pattern. | Copy expression; do not parse. | T-DESIG-SERIES, X-UNION. |
| P9 | P5 `kind=ranges` | same | same | branch-null fields null; `unevaluated/none`; one or more P13 ranges, zero values. | Emit canonical range children. | T-DESIG-RANGES, X-ORDER, X-CARDINALITY. |
| P10 | P5 `kind=unknown|not_applicable` | same | same | exact reason and temporal non-null; expression null; `unevaluated/none`; zero values/ranges. | Copy union without coercion. | T-DESIG-UNKNOWN, T-DESIG-NA, X-UNION. |
| P11 | P7 `/sourceDesignations/{j}` | `designation_value`, `{P5.key}:{j}`, P5, `j`; legacy identity exception uses table `designation-value` and identity `{projectionId,pointer,value}` | `app_designation_values`; PK node; unique `(P5,source_value)` and `(P5,ordinal)` | Exact source and ordinal. Listed model requires one P12 mapping. Listed serial/part forbids a mapping. Zero evidence links. | Emit scalar child and reassign its datum owner. | Exact; T-DESIG-LISTED, X-ORDER, X-HASH, X-IDENTITY. |
| P12 | Mapping for P11 only when P5 field kind is model | `identity_mapping`, P11 node ID, P11, `j` | `app_identity_mappings` | `model/no_normalized_identity/unknown`; evidence parent P5; zero own links. | One per exact model occurrence. | Exact; five-packet cardinalities plus X-IDENTITY. |
| P13 | P9 `/ranges/{j}` | `designation_range`, pointer, P5, `j` | `app_designation_ranges`; PK node; unique exact five-field range identity and ordinal | Exact lower/upper strings, inclusive flags, polarity; comparator `lexical_source_only_v1`; zero evidence/mapping. | Copy fields; never coerce or evaluate. | Exact; T-DESIG-RANGES, X-ORDER, X-HASH. |

### 2.2 Conditions, assertions, designation groups, and members

| ID | Canonical path / branch | Semantic node `(type, key, parent, ordinal)` | Physical owner and row identity | Required/optional columns and child/evidence/identity rule | Python materialization | DB/read/tests |
| --- | --- | --- | --- | --- | --- | --- |
| C1 | `/conditionDefinitions/{i}` | `condition`, `conditionKey`, root, `i` | `app_conditions`; PK node; unique `(projection,condition_key)` | Required condition type/operator, temporal-basis kind, four property-presence codes for comparator, product role, attribute key, and designation group; values non-null iff present; fixed `unevaluated/none`. Exact evidence purpose `condition_clause`. Exact assertion/group child set. No type/operator compatibility matrix. | Copy all closed fields and explicit presence. | Exact; T-COND-90, T-COND-OPTIONALS, X-UNION, X-CARDINALITY. |
| C2 | C1 `comparatorVersion` optional scalar | no child semantic node | columns on C1 | `comparator_presence=present` and exact value, or `property_absent` and null. | Never synthesize a version. | Exact; T-COND-OPTIONALS, X-PRESENCE. |
| C3 | C1 `subject.productRole` optional scalar | no child semantic node | columns on C1 | Same explicit presence/value rule; enum is the canonical product-role enum. | Copy only. | Exact; T-COND-OPTIONALS, X-PRESENCE. |
| C4 | C1 `subject.attributeKey` optional scalar | no child semantic node | columns on C1 | Same explicit presence/value rule. | Copy only. | Exact; T-COND-OPTIONALS, X-PRESENCE. |
| C5 | C1 `/subject/{manufacturer|modelOrSeries|partNumber|serialNumber|stcNumber|attributeValue}` when present; all three known-string branches | `value_assertion`, full object pointer, C1, `0` | `app_value_assertions`; PK node; unique `(C1, exact field code)` | Exact VA union. Evidence purpose `subject_value`. Known manufacturer gets C6. Known modelOrSeries gets C7. Other fields and all unknown/not-applicable branches forbid mappings. | Walk the fixed six-field registry; emit no row for absent property. | Exact; T-VALUE-18 (6 fields x 3 branches), X-VALUE, X-EVIDENCE, X-CARDINALITY. |
| C6 | Known C5 manufacturer mapping | `identity_mapping`, C5 node ID, C5, `0` | `app_identity_mappings` | `manufacturer/source_only/unknown`; evidence parent C1; zero own evidence. | Emit once for exact known occurrence. | Exact; T-COND-IDENTITY, X-IDENTITY. |
| C7 | Known C5 modelOrSeries mapping | `identity_mapping`, C5 node ID, C5, `0` | `app_identity_mappings` | **Proposed fidelity fix:** `model_or_series/source_only/unknown`; evidence parent C1. The canonical field has no discriminator, so `model` or `series` would be a false fact. Requires reviewed expansion of the mapping-kind CHECK before implementation. | Emit once with the ambiguity-preserving kind. | Exact; T-COND-IDENTITY, X-MISCLASSIFY. |
| C8 | `/conditionDefinitions/{i}/subject/designationGroup` when present | `designation_group`, full pointer, C1, `0` | `app_designation_groups`; PK node; unique `(C1,group_key)` and ordinal | Required group key, association, source-display assertion ID, ordinal. For `unknown`, reason+temporal required; otherwise forbidden. Exact group evidence purpose `condition_clause`. Exactly one C9 and at least one member across C10 ∪ C11, with exact total count and contiguous ordinals; mutually exclusive with atomic modelOrSeries is **not** implied unless schema says so. | Emit solely from canonical v2 group object; never parse display punctuation. | Exact; T-CGROUP-ASSOCIATIONS, X-UNION, X-CARDINALITY. |
| C9 | C8 `/sourceDisplayText`, all VA branches | `value_assertion`, pointer, C8, `0` | `app_value_assertions` | Field `source_display_text`; exact VA union; purpose `subject_value`; no identity mapping. | Emit required assertion. | Exact; T-CGROUP-DISPLAY, X-VALUE, X-EVIDENCE. |
| C10 | C8 `/members/{j}`, `designationKind=model` | `designation_group_member`, full pointer, C8, `j` | `app_designation_group_members`; PK node; unique `(C8,member_key)` and ordinal | Required key/kind, exact `source_designation`; expression/evaluation/reason null; manufacturer assertion ID and exact manufacturer union columns; designation mapping ID required. Exact member evidence purpose `subject_value`. | Copy source spelling; do not split or normalize. Emit C12 and C13/C14. | Exact; T-CGROUP-MODEL, X-ORDER, X-UNION, X-EVIDENCE. |
| C11 | C8 `/members/{j}`, `designationKind=series_expression` | same type/key/parent/ordinal as C10 | same | Exact `expression_text`; source designation null; physical evaluation `unevaluated`, reason `unsupported_expression`; manufacturer assertion/union and series mapping required. Exact member evidence purpose `subject_value`; expression is never executed. | Copy expression; emit C12 and C15 plus optional C14. | Exact; T-CGROUP-SERIES, X-UNION, X-MISCLASSIFY. |
| C12 | C10/C11 `/manufacturer`, all VA branches | `value_assertion`, pointer, member, `0` | `app_value_assertions` | Field `manufacturer`; exact VA union; purpose `identity_support`. Known creates C14; unknown/not-applicable forbids manufacturer mapping. | Emit required assertion. | Exact; T-CGROUP-MANUFACTURER, X-VALUE, X-EVIDENCE. |
| C13 | C10 designation mapping | `identity_mapping`, member node ID, member, `j` | `app_identity_mappings` | `model/source_only/unknown`; evidence parent C8, source value exact `sourceDesignation`; zero own evidence. | One per exact model member. | Exact; T-CGROUP-MODEL, X-IDENTITY. |
| C14 | Known C12 manufacturer mapping | `identity_mapping`, C12 node ID, C12, `0` | `app_identity_mappings` | `manufacturer/source_only/unknown`; evidence parent C8; exact occurrence even if string repeats. | Emit only for known branch. | Exact; T-CGROUP-MANUFACTURER, X-IDENTITY. |
| C15 | C11 series mapping | `identity_mapping`, member node ID, member, `j` | `app_identity_mappings` | `series/source_only/unknown`; evidence parent C8, source exact expression. | One per exact series member. | Exact; T-CGROUP-SERIES, X-IDENTITY. |

`conditionSubject` remains a closed object. The six atomic assertion properties
and `designationGroup` are independently optional because validator-2 does not
declare a `oneOf` between them. The database and reader therefore reproduce
every schema-valid combination instead of inventing a compatibility rule.

### 2.3 Rules, expression trees, edges, and exclusions

| ID | Canonical path / branch | Semantic node `(type, key, parent, ordinal)` | Physical owner and row identity | Required/optional columns and child/evidence/reference rule | Python materialization | DB/read/tests |
| --- | --- | --- | --- | --- | --- | --- |
| R1 | `/applicabilityRules/{i}` | `applicability_rule`, `ruleKey`, root, `i` | `app_rules`; PK node; unique `(projection,rule_key)` | Required rule key, scope-root ID, condition-presence code, nullable condition-root only when present, evaluator version `none`. Exact evidence purpose `rule_clause`. Exact exclusion set. | Emit rule first, then its two named expression contexts and exclusions. | Exact; T-RULE, X-OWNER, X-REFERENCE, X-EVIDENCE. |
| R2 | R1 `/scopeExpression` root | `expression`, full pointer, R1, `0` | `app_expressions`; PK node; unique `(R1,scope,expression_path)` | Context `scope`, path `/`; result domain `true_false_unknown`, evaluator `none`; branch columns below. Exactly one scope root. | Recursive, depth/resource bounded. | Exact; T-EXPR-ALL, X-REFERENCE, X-CARDINALITY, X-CYCLE. |
| R3 | R1 `/conditionExpression` root when property present | `expression`, full pointer, R1, `0` | same, context `condition`, path `/` | Same; exact one root iff presence is `present`, otherwise zero. | Preserve property absence. | Exact; T-RULE-OPTIONAL, X-PRESENCE. |
| R4 | expression `scope_ref` | expression node as R2/R3; parent is enclosing expression or R1; ordinal is operand index or 0 | same | `node_type=scope_ref`; exactly `scope_node_id` non-null; all other refs null. Composite FK targets exact same-projection P1. Arity 0. | Resolve key through canonical registry, never string-only storage. | T-EXPR-SCOPE, X-REFERENCE, X-ARITY. |
| R5 | expression `predicate_ref` | same | same | Exactly `condition_node_id` non-null; targets C1; arity 0. | Exact lookup. | T-EXPR-PREDICATE, X-REFERENCE, X-ARITY. |
| R6 | expression `rule_ref` | same | same | Exactly `referenced_rule_node_id` non-null; targets R1; arity 0. Rule-reference graph plus exclusions must remain acyclic. | Exact lookup and graph validation. | T-EXPR-RULE, X-REFERENCE, X-CYCLE. |
| R7 | expression `not` | same | same | All ref columns null; exactly one outgoing edge at sequence 0. | Recurse through `operand`. | T-EXPR-NOT, X-ARITY, X-ORDER. |
| R8 | expression `all|any` | same | same | All ref columns null; >=2 outgoing edges with contiguous sequence matching `operands`. | Preserve sequence; never sort operands. | T-EXPR-ALL, T-EXPR-ANY, X-ARITY, X-ORDER. |
| R9 | schema branch `requirement_state_ref` inside applicability rule | none: rejected before projection | no owner is legal in Slice 3A | Validator semantic rule forbids it because applicability rules cannot reference requirement state. DB grammar validator must also reject a directly stamped validator-2 parent containing it; no nullable catch-all column is permitted. | Raise `cross_namespace_reference`. | T-EXPR-REQ-REJECT, X-FORGED-PARENT. |
| R10 | each parent-child expression relationship | no semantic node | `app_expression_edges`; row identity `(parent_expression_id,sequence)`, also unique parent/child | Required projection/proposal/owning rule/context, parent, child, sequence. Parent/child must share owner/context/projection; child semantic parent equals parent. `not=1`, `all/any>=2`, leaf=0, contiguous, acyclic, every non-root has exactly one incoming edge. | Emit while recursing; edge sequence is canonical position. | Exact; T-EXPR-ALL, X-ORDER, X-CROSS-PROJECTION, X-CYCLE, X-ORPHAN. |
| R11 | R1 `/exclusionRuleKeys/{j}` | no semantic node | `app_rule_exclusions`; row identity `(rule_node_id,ordinal)`; unique rule/excluded pair | Exact excluded-rule composite FK in same projection; ordinal contiguous; zero rows for empty set; combined rule-ref/exclusion graph acyclic and no self-edge. | Resolve after all rule rows exist. | Exact; T-RULE-EXCLUSIONS, X-ORDER, X-REFERENCE, X-CYCLE. |

Expression `expression_path` is context-relative: `/` for a root,
`/operand` below `not`, and `/operands/{k}` recursively for sequence children.
`source_pointer` remains the complete canonical pointer. The path is a stored
regulatory identity, not computed from database edge traversal during reads.

### 2.4 Non-controlling search hints, groups, and members

| ID | Canonical path / branch | Semantic node `(type, key, parent, ordinal)` | Physical owner and row identity | Required/optional columns and child/evidence/identity rule | Python materialization | DB/read/tests |
| --- | --- | --- | --- | --- | --- | --- |
| H1 | `/applicabilitySearchHints/{i}` | `search_hint`, `hintKey`, root, `i` | `app_search_hints`; PK node; unique `(projection,hint_key)` | Required key/role/source-display assertion ID; fixed `controlling=false`, `exhaustive=false`. Exact hint evidence purpose `search_hint_clause`. Exactly one H2 and >=1 H3. No expression FK can target a hint. | Copy only; never promote to controlling applicability. | Exact; T-HINT, X-OWNER, X-EVIDENCE, X-REFERENCE. |
| H2 | H1 `/sourceDisplayText`, all VA branches | `value_assertion`, pointer, H1, `0` | `app_value_assertions` | Field `source_display_text`; exact VA union; purpose `search_hint_clause`; no identity mapping. | Emit required assertion. | Exact; T-HINT-DISPLAY, X-VALUE. |
| H3 | H1 `/manufacturerModelGroups/{j}` | `search_hint_group`, full pointer, H1, `j` | `app_search_hint_groups`; PK node; unique `(H1,group_key)` and ordinal | Required group key, association, manufacturer assertion ID and exact manufacturer union columns. `unknown` requires reason+temporal; other associations forbid them. Exact group evidence purpose `search_hint_clause`; at least one member across H6 ∪ H7, with exact total count and contiguous ordinals. | Preserve canonical pairing/unknown only; never infer manufacturer/model pairs. | Exact; T-HGROUP-ASSOCIATIONS, X-UNION, X-ORDER. |
| H4 | H3 `/manufacturer`, all VA branches | `value_assertion`, pointer, H3, `0` | `app_value_assertions` | Field `manufacturer`; exact VA union; purpose `identity_support`. Known creates H5; other branches forbid mapping. | Emit required assertion. | Exact; T-HGROUP-MANUFACTURER, X-VALUE, X-IDENTITY. |
| H5 | Known H4 manufacturer mapping | `identity_mapping`, H4 node ID, H4, `0` | `app_identity_mappings` | `manufacturer/source_only/unknown`; evidence parent H3; zero own links. | One per exact group occurrence. | Exact; X-IDENTITY. |
| H6 | H3 `/members/{k}`, `designationKind=model` | `search_hint_model`, full pointer, H3, `k` | `app_search_hint_members`; PK node; unique `(H3,member_key)` and ordinal | Exact source designation; expression/evaluation/reason null; manufacturer assertion/union required; model mapping required. Exact member evidence purpose `search_hint_clause`. | Copy one source member; never expand range-like spelling. | Exact; T-HMEMBER-MODEL, X-ORDER, X-MISCLASSIFY. |
| H7 | H3 `/members/{k}`, `designationKind=series_expression` | same semantic type/key/parent/ordinal as H6 | same | Exact expression; source designation null; physical evaluation `unevaluated`, reason `unsupported_expression`; manufacturer assertion/union and series mapping required. Exact member evidence purpose `search_hint_clause`. | Preserve expression as opaque source text. | Exact; T-HMEMBER-SERIES, X-UNION, X-MISCLASSIFY. |
| H8 | H6/H7 `/manufacturer`, all VA branches | `value_assertion`, pointer, member, `0` | `app_value_assertions` | Field `manufacturer`; exact VA union; purpose `identity_support`; known creates H9. | Emit required assertion. | Exact; T-HMEMBER-MANUFACTURER, X-VALUE. |
| H9 | Known H8 manufacturer mapping | `identity_mapping`, H8 node ID, H8, `0` | `app_identity_mappings` | `manufacturer/source_only/unknown`; evidence parent H3; exact occurrence despite repeated group spelling. | One per known member occurrence. | Exact; X-IDENTITY. |
| H10 | H6 model designation mapping | `identity_mapping`, H6 node ID, H6, `k` | `app_identity_mappings` | `model/source_only/unknown`; source exact designation; evidence parent H3. | One per model member. | Exact; T-HMEMBER-MODEL, X-IDENTITY. |
| H11 | H7 series designation mapping | `identity_mapping`, H7 node ID, H7, `k` | `app_identity_mappings` | `series/source_only/unknown`; source exact expression; evidence parent H3. | One per series member. | Exact; T-HMEMBER-SERIES, X-IDENTITY. |

The 2002 calibration hint must therefore materialize 1 hint, 1 display
assertion, 7 groups, 7 group-manufacturer assertions, 20 members, 20
member-manufacturer assertions, 19 model mappings, 1 series mapping, and the
corresponding exact manufacturer mappings. `172A through 172H` remains one
series expression and never becomes inferred model rows.

## 3. PostgreSQL commit and verified-read contract

### 3.1 Commit-time expected-graph comparison

The deferred validator must build `expected_*` relations directly from the
immutable parent proposal JSON for **every** row in section 2, then compare each
expected relation to its actual table with set equality (`FULL JOIN` or two
`EXCEPT` directions) over all meaningful columns. Counts alone are not proof.
Comparisons use `IS DISTINCT FROM` so SQL `UNKNOWN` cannot admit a bad row.

It must also:

1. validate the closed applicability JSON grammar, allowed keys, branch
   discriminators, enums, required/forbidden properties, minimum cardinality,
   references, and cycles in PostgreSQL before relying on a parent row stamped
   with validator-2 metadata;
2. recompute every semantic ID, identity hash, canonical node hash, parent,
   pointer, key, and ordinal;
3. prove every semantic node has exactly one owner from the complete owner
   union and every typed owner has exactly one matching node of the right type;
4. compare exact evidence-link and identity-mapping relations, including rows
   that must be absent;
5. compare exact expression roots/edges, group/member children, designation
   children, exclusions, all presence columns, and every same-projection ref;
6. reconstruct the full four-field JSONB subtree from typed owners in canonical
   order and require equality with both the generic datum reconstruction and
   the parent candidate subtree; and
7. verify the projection counts, restricted-JCS bytes/hash, projection hash,
   correction/dependency foundations, and materialized event envelope already
   required by the approved decision.

The validator is a deferred constraint trigger on every table capable of
changing the graph. INSERT, UPDATE, and DELETE are covered even though normal
production rows are immutable. The immutability trigger is not treated as a
substitute for equivalence validation.

### 3.2 Verified reads

Every detail/reconstruction/list audit read first derives the same complete
expected neutral graph from the verified candidate and compares exact sets for
all owner families, semantic nodes, identities, evidence, edges, exclusions,
and counts. It must reject with controlled HTTP 409 on any mismatch, including
bad ordinals; it must not index canonical arrays by an untrusted stored
ordinal. It then reconstructs from typed owners and requires exact equality
with the generic datum reconstruction, stored canonical bytes/hash, and parent
subtree. GET remains detection-only and performs no repair, flush, or commit.

## 4. Complete test oracle

Positive branch vectors are generated from a minimal valid validator-2
envelope and include:

| Test ID | Required coverage |
| --- | --- |
| T-PRODUCT / T-PRODUCT-UNION | every optional product property combination and manufacturer normalized known/unknown/not-applicable |
| T-DESIG-ALL/LISTED/SERIES/RANGES/UNKNOWN/NA | all six designation branches for model, serial, and part-number fields; listed mapping required only for model |
| T-COND-90 | Cartesian 9 condition types x 10 operators, all stored unevaluated |
| T-COND-OPTIONALS | every presence/absence combination of comparator, product role, attribute key, six assertion fields, and group |
| T-VALUE-18 | known/unknown/not-applicable for each of the six atomic condition fields |
| T-CGROUP-ASSOCIATIONS | all four associations, required/forbidden unknown metadata, model-only, series-only, mixed, one-member, and multiple-member groups |
| T-CGROUP-DISPLAY/MODEL/SERIES/MANUFACTURER | all display/manufacturer unions and both member variants |
| T-RULE / T-RULE-OPTIONAL / T-RULE-EXCLUSIONS | condition expression absent/present, empty/multiple exclusions, canonical exclusion ordering |
| T-EXPR-SCOPE/PREDICATE/RULE/NOT/ALL/ANY | every legal rule expression branch, both contexts, nested trees, repeated shapes, sequence preservation |
| T-EXPR-LONG-POINTER | a schema-valid nested expression whose pointer-derived node key exceeds 255 characters, through Python, fresh PostgreSQL commit, and verified read |
| T-EXPR-REQ-REJECT | schema-shaped requirement-state ref rejected in applicability-rule context |
| T-HINT / T-HINT-DISPLAY | empty hint top-level array plus complete hint and all display unions |
| T-HGROUP-ASSOCIATIONS/MANUFACTURER | paired/source_group/unknown, all manufacturer unions, and model-only/series-only/mixed member sets |
| T-HMEMBER-MODEL/SERIES/MANUFACTURER | both member variants, all manufacturer unions, repeated strings as distinct occurrences |
| T-CALIBRATION-5 | exact byte round trip for all five calibration packets and the approved per-packet cardinality assertions |

Every positive vector must pass four observations: neutral expected graph,
Python ORM materialization, fresh PostgreSQL commit, and verified-read
reconstruction. The four graphs/bytes must agree exactly.

For each physical table and relationship, direct-SQL tests mutate an otherwise
valid graph before deferred constraints are forced and prove commit rejection:

| Test ID | Corruption class |
| --- | --- |
| X-NODE | wrong/missing/extra node; ID, type, key, pointer, parent, ordinal, canonical hash, identity hash, projection, or proposal drift |
| X-OWNER | missing/extra/duplicate/wrong-type typed owner and owner without node |
| X-VALUE / X-UNION / X-PRESENCE | changed value; invalid required/null combination; absent-vs-present drift; unknown metadata drift |
| X-EVIDENCE | missing/extra/reordered/wrong-purpose/cross-binding link, bad link ID/hash, duplicate inherited mapping link; distinct occurrence/context sets swapped, conflated, or one side omitted |
| X-IDENTITY / X-MISCLASSIFY | missing/extra/wrong occurrence/evidence parent/kind/origin/state/value/provenance/review/hash; serial/part/ambiguous model-or-series relabeling |
| X-CARDINALITY / X-ORDER | zero where nonempty required, missing/extra child, duplicate/gap/negative/reordered ordinal |
| X-REFERENCE / X-CROSS-PROJECTION | missing, wrong-type, wrong-key, or cross-projection scope/condition/rule/root/child reference |
| X-ARITY / X-CYCLE / X-ORPHAN | bad expression arity, expression/rule cycle, multiple/no roots, multiple/no parent edge |
| X-HASH | self-consistent owner value with stale or recomputed wrong semantic/link/row/projection hashes |
| X-FORGED-PARENT | direct candidate SQL stamps validator-2 on unknown property, bad union, bad enum, illegal requirement ref, duplicate key, or cyclic refs; materialized commit must fail |

Every read-side corruption vector disables immutability only inside a rolled
back test transaction and asserts controlled 409 from detail, reconstruction,
and list as applicable. No test may accept an unhandled 500 as fail-closed.

## 5. Drift-minimizing construction

The current implementation hand-codes the same rules in `_semantic_type` /
`_flatten` / augmentation and owner builders, in the migration's PL/pgSQL
validator, and again in `_verify_source_scope_owners`. The source/product work
already demonstrates three-way drift: special designation-value identities,
manual pointer branches, duplicated evidence rules, and partial read checks.

The replacement construction is:

1. Add a versioned, immutable **data-only JSON manifest** validated against the
   closed DSL in section 5.1. It contains no Python callables, SQL snippets, or
   opaque labels. Canonical selectors, branch discriminators, semantic
   type/key/parent/ordinal expressions, typed column extractors, evidence and
   identity policy, child cardinality, ordering, and reference targets are all
   DSL values.
2. Make one pure `expected_applicability_graph(proposal, projection_id,
   proposal_id)` walker consume that specification and return frozen neutral
   records for semantic nodes, typed owners, identities, evidence links, edges,
   and exclusions. ORM insertion is a thin adapter over those records.
3. Make verified reads query each table into the same neutral record types and
   perform exact multiset/set comparison against a newly derived expected
   graph. Reconstruction consumes only the verified typed records, not generic
   datum as its primary source.
4. Freeze the canonical JSON manifest and its SHA-256 into migration 0027.
   Generator `paprnav-app-mapgen-1` produces both the Python descriptor module
   and the repetitive `expected_*` SQL fragments. Both generated files carry
   manifest version, manifest SHA, generator version, and generator source SHA
   headers. The source manifest, generated files, and a checked-in golden
   output fixture are compared byte-for-byte by `mapgen --check`; CI also
   queries the migrated database digest and compares it with Python. Historical
   migration text never imports live application modules and never changes
   when a future mapping version is introduced.
5. Generate the positive branch vector registry and expected row-count/type
   assertions from the same manifest. Direct-SQL corruption cases remain
   hand-authored adversarial tests because they test the independent database
   implementation rather than the generator.

Some rules deliberately remain independently implemented for defense in depth:

- PostgreSQL closed-shape, set-equality, FK, CHECK, deferred cardinality,
  cycle, exactly-one-owner, and reconstruction checks defend against direct SQL
  and cannot call Python.
- Validator-2 schema/semantic validation remains the ingestion boundary and
  is not replaced by materializer expectations.
- Verified-read comparison remains independent of commit triggers so disabled,
  bypassed, or historically defective constraints fail closed during audit.
- Generic datum reconstruction remains an independent byte-exact cross-check
  until the typed reconstruction has passed all final gates; it is never an
  authorization or query escape hatch.

The shared artifact is therefore declarative vocabulary and expected test data,
not one procedural validator reused everywhere. Python, PostgreSQL, and read
verification must independently agree on the frozen manifest and all branch
vectors.

### 5.1 Closed data-only mapping DSL

The manifest is a JSON object with `additionalProperties=false` at every level
and these required roots:

```text
manifestVersion, validatorVersion, canonicalizationVersion, rowDomain,
generatorVersion, resourceLimits, domains, enums, collections, occurrences,
relationships, globalInvariants, testVectors
```

Its only expression form is a recursively validated object with exactly one
operator. The closed operators are:

```text
literal(value)              field(relativeSegments)
boundIndex(name)            sourcePointer()
parentOccurrence(id)
presence(relativeSegments)  enumMap(input, closedMap)
concat(parts)               case(branches, else)
canonicalHash(input)        rowIdentity(prefix, table, fields)
reference(namespace, key)   unionState(relativeSegments)
```

`relativeSegments` is an array of literal property names and bound array-index
names, never executable JSONPath. A selector is a closed sequence of steps:

```text
rootField(name)
eachSet(bind, sortKey, minItems)
eachSequence(bind, minItems)
requiredProperty(name)
optionalProperty(name)
union(discriminatorPath, closedBranches)
recursiveUnion(discriminatorPath, closedBranches, childProperties,
               maxNodes, maxDepth)
```

Each occurrence descriptor requires:

```text
occurrenceId, selector, when, semantic {type,key,parent,pointer,ordinal,
identity}, owner {table,rowIdentity,columns,uniques}, evidence,
identityMappings, childCardinality
```

Each column descriptor requires `name`, one domain name from section 7,
`nullable`, and one derivation expression. `when` is a closed conjunction of
`present`, `absent`, `equals`, and `in` predicates. A relationship descriptor
requires source/target occurrence IDs, context-equality fields, ordering,
arity, and cycle policy. Unknown operators, fields, enum values, selector
steps, derivation omissions, or nullable columns fail manifest validation and
generation.

`recursiveUnion` is used only for expressions. Its closed branches encode the
three reference leaves, the forbidden requirement-state leaf, `not/operand`,
and `all|any/operands`. Thus recursion, leaf refs, parentage, arity, and operand
sequence are manifest-bound rather than hidden in a Python function.

`resourceLimits` freezes the validator-2 constants `maxDepth=64`,
`maxTotalNodes=75000`, `maxAstNodes=20000`, and `maxGraphEdges=40000`.
Python validation, generated expectation traversal, SQL closed-grammar checks,
and branch-vector generation use those exact values. Changing any limit
requires a new manifest digest and compatibility review.

The generator has no semantic configuration outside the manifest. It is a
pure compiler from this DSL to (a) Python frozen descriptors, (b) SQL expected
relations/check fragments, and (c) branch-vector expectations. Golden tests
feed one fixture per operator and every section-4 branch through the generated
Python walker and PostgreSQL expectations. Any deliberately hand-written
global algorithm, currently only graph-cycle traversal and final JSONB
assembly, is named in `globalInvariants`, is outside the digest's executable
claim, and must pass independent cross-layer parity vectors.

## 6. Pre-implementation decisions and family gates

Two decision amendments are required before code changes:

- `conditionSubject.modelOrSeries` has no canonical discriminator. Add
  `model_or_series` to the candidate identity-mapping kind domain for that exact
  atomic occurrence only. Mapping it to `model` or `series` is prohibited.
  Designation-group and hint members remain the only discriminated model/series
  occurrences. The independent design reviewer must accept this amendment or
  supply an equally source-faithful alternative.
- Product `manufacturer.normalizedIdentity` is a required known-string union.
  Permit `candidate_payload` mappings to preserve all three exact normalized
  states, including the canonical reason/temporal fields for unknown and
  not-applicable. Reserve `no_normalized_identity` for canonical shapes that
  truly lack a normalized-identity property. Collapsing a present unknown or
  not-applicable payload to `not_extracted` is prohibited.

Implementation proceeds only after that review, in these complete gates:

1. C1-C15 plus all `T-C*`, `T-VALUE-*`, and applicable `X-*` tests.
2. R1-R11 plus all `T-RULE*`, `T-EXPR*`, and applicable `X-*` tests.
3. H1-H11 plus all `T-H*` and applicable `X-*` tests.
4. Whole graph: every semantic node exactly one typed owner, typed-owner
   reconstruction, exact evidence/identity/reference/cardinality verification,
   `T-CALIBRATION-5`, clean host suite, and a freshly migrated disposable
   PostgreSQL suite.

No family is submitted for adversarial implementation review until all its
matrix rows and negative tests exist. IA-001 is not closed until the final
whole-graph packet passes the independent reviewer with no residual blocker.

## 7. Physical domains, columns, nullability, and uniqueness

This appendix is part of the manifest contract. `NN` means `NOT NULL`; `N`
means nullable only under the cited branch CHECK. All text originating from the
canonical `identifier` definition uses `IDENTIFIER`, so valid 512-character
values are lossless.

### 7.1 Reusable PostgreSQL domains

| Domain | SQL representation and CHECK |
| --- | --- |
| `ID` | `varchar(36)`, NN |
| `HASH` | `char(64)`, NN, lowercase hex |
| `STABLE_KEY` | `varchar(128)`, NN, length 3..128 and stable-key regex |
| `IDENTIFIER` | `text`, NN where required, character length 1..512 |
| `OPT_IDENTIFIER` | `text`, N, when present length 1..512 |
| `ORDINAL` | `integer`, NN, `>=0` |
| `PRESENCE` | `varchar(32)`, NN, `property_absent|present` |
| `STATE` | `varchar(32)`, NN, `known|unknown|not_applicable` |
| `TEMPORAL` | `varchar(64)`, enum from canonical temporal-scope kinds |
| `UNKNOWN_REASON` | `varchar(64)`, controlled canonical unknown-reason enum |
| `UNION_REASON` | `text`, N, unknown branch must be `UNKNOWN_REASON`; not-applicable branch is `IDENTIFIER` up to 512 |
| `FIELD_CODE` | `varchar(64)`, NN, `manufacturer|model_or_series|part_number|serial_number|stc_number|attribute_value|source_display_text` |
| `PRODUCT_ROLE` | `varchar(32)`, NN, exact six-role enum |
| `IDENTITY_KIND` | `varchar(32)`, NN, `manufacturer|model|series|model_or_series` |
| `BOOL` | PostgreSQL `boolean`, NN |

Every table also has a database-generated non-null timestamp. Timestamps are
operational metadata and excluded from deterministic equivalence comparisons.

### 7.2 Common graph tables

| Table | Columns beyond generated timestamp | Nullability / CHECK / identity |
| --- | --- | --- |
| `app_semantic_nodes` | `id ID`, `identity_hash HASH`, `projection_id ID`, `proposal_id ID`, `parent_node_id ID`, `node_type varchar(64)`, `node_key text`, `source_pointer text`, `canonical_node_hash HASH`, `canonical_ordinal ORDINAL` | only `parent_node_id` N for root nodes; key and pointer NN with no width narrower than validator-2; closed node-type enum; unique `(projection,node_type,node_key)`, identity hash, and `(id,projection,proposal)` |
| `app_evidence_links` | `id ID`, projection/proposal/node/binding IDs, `evidence_key STABLE_KEY`, `purpose varchar(64)`, `canonical_ordinal ORDINAL`, `link_hash HASH` | all NN; closed purpose enum; unique `(node,purpose,evidence_key)` and `(node,purpose,ordinal)` |
| `app_value_assertions` | semantic/projection/proposal/parent IDs, `field_code FIELD_CODE`, `state STATE`, `value_type varchar(16)`, `text_value OPT_IDENTIFIER`, `reason UNION_REASON`, `temporal_scope TEMPORAL` | IDs/field/state/value_type NN; reason/temporal N by union; `value_type=text`; exact §1.3 branch CHECK; unique `(parent,field_code)` |
| `app_identity_mappings` | `id ID`, semantic/projection/proposal/source-occurrence/context-owner IDs, `identity_kind IDENTITY_KIND`, `source_value IDENTIFIER`, `normalization_origin varchar(64)`, `normalized_state STATE`, `normalized_value OPT_IDENTIFIER`, `reason UNION_REASON`, `temporal_scope TEMPORAL`, `normalization_namespace varchar(64)`, `normalization_version varchar(64)`, `review_state varchar(32)`, `identity_hash HASH` | IDs/kind/source/origin/state/review/hash NN; remaining fields N exactly by §1.2 origin union; unique semantic node, identity hash, and `(projection,kind,occurrence)` |

### 7.3 Product/designation owners

| Table | Owner-specific columns | Nullability / CHECK / uniqueness |
| --- | --- | --- |
| `app_product_scopes` | `scope_key STABLE_KEY`, `product_role PRODUCT_ROLE`, manufacturer/model/serial/part presence codes, `manufacturer_source_value OPT_IDENTIFIER`, `manufacturer_identity_mapping_node_id ID` | common IDs and all presence codes NN; manufacturer value/mapping both NN iff present, otherwise both null; unique `(projection,scope_key)` |
| `app_designation_scopes` | product node ID, `field_kind varchar(32)`, `scope_kind varchar(32)`, `series_expression OPT_IDENTIFIER`, `reason UNION_REASON`, `temporal_scope TEMPORAL`, evaluation state/contract `varchar(64)` | common/product IDs, kinds, evaluation fields NN; branch nullability exactly P6-P10; unique `(product,field_kind)` |
| `app_designation_values` | designation node ID, `source_value IDENTIFIER`, `canonical_ordinal ORDINAL`, mapping node ID | common/designation/source/ordinal NN; mapping N only for serial/part and NN for model; unique `(designation,source)` and `(designation,ordinal)` |
| `app_designation_ranges` | designation node ID, lower/upper `IDENTIFIER`, inclusive `BOOL`s, `polarity varchar(16)`, `canonical_ordinal ORDINAL`, comparator `varchar(64)` | all NN; polarity exact enum; comparator fixed; unique exact five-field identity and `(designation,ordinal)` |

### 7.4 Condition/group owners

| Table | Owner-specific columns | Nullability / CHECK / uniqueness |
| --- | --- | --- |
| `app_conditions` | `condition_key STABLE_KEY`, type/operator `varchar(64)`, `temporal_basis TEMPORAL`, comparator/product-role/attribute-key/designation-group presence codes, comparator `OPT_IDENTIFIER`, product role `varchar(32)`, attribute key `varchar(128)`, designation-group node ID, evaluation state/contract `varchar(64)` | common/key/type/operator/temporal/presence/evaluation NN; each optional value/ID NN iff its presence is present; enum checks; unique `(projection,condition_key)` |
| `app_designation_groups` | condition node ID, `group_key STABLE_KEY`, `association varchar(32)`, source-display assertion ID, `reason UNKNOWN_REASON`, `temporal_scope TEMPORAL`, `canonical_ordinal ORDINAL` | common/condition/key/association/assertion/ordinal NN; reason/temporal NN iff association unknown; unique `(condition,group_key)` and `(condition,ordinal)` |
| `app_designation_group_members` | group node ID, `member_key STABLE_KEY`, designation kind `varchar(32)`, source designation/expression `OPT_IDENTIFIER`, manufacturer assertion ID/state/value/reason/temporal, evaluation state/reason `varchar(64)`, ordinal, designation mapping ID | common/group/key/kind/manufacturer assertion+state/ordinal/mapping NN; manufacturer union uses IDENTIFIER/UNION_REASON/TEMPORAL; designation and evaluation columns follow C10/C11; unique `(group,member_key)` and `(group,ordinal)` |

### 7.5 Rule/expression owners

| Table | Owner-specific columns | Nullability / CHECK / uniqueness |
| --- | --- | --- |
| `app_rules` | `rule_key STABLE_KEY`, scope-root ID, condition presence, condition-root ID, evaluator `varchar(64)` | common/key/scope/presence/evaluator NN; condition root NN iff present; unique `(projection,rule_key)` |
| `app_expressions` | owning-rule ID, context `varchar(16)`, `expression_path text`, node type `varchar(32)`, result domain/evaluator `varchar(64)`, scope/condition/referenced-rule IDs | common/owner/context/path/type/domain/evaluator NN; exactly one typed ref for matching leaf and all null for operators; unique `(rule,context,path)` |
| `app_expression_edges` | projection/proposal/owning-rule IDs, context, parent/child expression IDs, `sequence ORDINAL` | all NN; PK/unique `(parent,sequence)`, unique `(parent,child)`, unique child to enforce one incoming edge |
| `app_rule_exclusions` | projection/proposal/rule/excluded-rule IDs, `canonical_ordinal ORDINAL` | all NN; unique `(rule,excluded)` and `(rule,ordinal)` |

### 7.6 Search-hint owners

| Table | Owner-specific columns | Nullability / CHECK / uniqueness |
| --- | --- | --- |
| `app_search_hints` | `hint_key STABLE_KEY`, `product_role PRODUCT_ROLE`, source-display assertion ID, controlling/exhaustive `BOOL` | all NN; booleans both false; unique `(projection,hint_key)` |
| `app_search_hint_groups` | hint ID, `group_key STABLE_KEY`, ordinal, manufacturer assertion ID/state/value/reason/temporal, association, association reason/temporal | common/hint/key/ordinal/assertion/state/association NN; manufacturer union exact; association reason/temporal NN iff unknown; unique `(hint,group_key)` and `(hint,ordinal)` |
| `app_search_hint_members` | group ID, `member_key STABLE_KEY`, designation kind, source designation/expression, manufacturer assertion ID/state/value/reason/temporal, evaluation state/reason, ordinal, designation mapping ID | same branch nullability as condition members; all identity/parent keys NN; unique `(group,member_key)` and `(group,ordinal)` |

All owner tables' common semantic/projection/proposal IDs are NN and carry the
composite same-projection FKs stated in section 1. Values described as
`varchar(N)` must also have length CHECKs if PostgreSQL implicit width behavior
would otherwise produce a different failure contract.

Boundary vectors cover identifier lengths 1, 64, 65, 511, and 512 for known
text and not-applicable reason, and reject 0 and 513. They run through schema,
materialization, PostgreSQL commit, and verified reconstruction to prove no
valid canonical value is truncated or rejected by a narrower owner column.
`T-EXPR-LONG-POINTER` separately proves pointer-derived semantic keys above 255
characters are accepted losslessly and retain exact uniqueness, IDs, hashes,
and read reconstruction.
