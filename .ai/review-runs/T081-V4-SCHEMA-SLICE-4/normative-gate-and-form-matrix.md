# Slice 4 normative gate, dependency, SQL, and form matrix

This file is a normative input to `T081-V4-SCHEMA-SLICE-4`. Implementation,
PostgreSQL validation, read verification, UI rendering, and test oracles may not
invent a different rule. Version identifiers are:

- gate rules: `paprnav-ad-v4-review-gates-1`;
- dependency rules: `paprnav-ad-v4-review-dependencies-1`;
- form projection: `paprnav-ad-v4-review-form-1`;
- review lifecycle: `paprnav-ad-v4-review-lifecycle-1`; and
- authorization policy: `paprnav-ad-v4-candidate-review-1`.

## 1. Closed outcomes and ordering

Node gates use ranks:

| gate | rank | meaning |
| --- | ---: | --- |
| `candidate_only` | 0 | valid retained semantics, but no automated or affirmative conclusion |
| `human_determination_required` | 1 | a later aircraft-specific signed determination is required |
| `actionable` | 2 | source support and an independently reviewed executable evaluation contract are complete for this node |

`effective_gate(node) = min(base_gate(node), effective_gate(each propagating
dependency))`. A parent may never store a rank greater than that minimum.
Nonpropagating integrity references must resolve exactly but do not enter the
minimum. Noncontrolling nodes are recorded and verified but do not enter the
aggregate minimum.

Aggregate review classifications are closed:

| classification | commit effect |
| --- | --- |
| `remediation_only` | may be rejected; no decision-node graph or accepted decision may commit |
| `candidate_only` | may create one candidate-only decision, complete node/dependency graph, signoff, and terminal event |

There is no Slice-4 `release_eligible`, `released_actionable`, `selected`, or
`current` value. Migration checks and deferred triggers reject any such value
or event. Because every validator-2 proposal contains at least one
applicability rule and each rule has `evaluator_contract='none'`, every
otherwise acceptable proposal has aggregate gate `candidate_only`.

No Slice-4 node is `actionable`: 3A deliberately fixes its evaluator contracts
to `none`/unsupported and 3B stores source representation without an executable
applicability, timing, recurrence, termination, or compliance evaluator. The
rank remains reserved so PostgreSQL can reject fabricated actionable rows and a
future separately reviewed version can extend the contract without changing
the meaning of historical Slice-4 rows.

Exact source representation is orthogonal. Accepted node rows also store
`representation_status=exact|explicit_unknown`. Structural/known/not-applicable
source content is `exact`; a schema-valid unknown is `explicit_unknown`.
Integrity failure creates no accepted graph and is remediation-only.

## 2. Common base-gate rules

Every projected semantic node needs the exact live evidence-link set already
required by the 3A/3B projection verifier. Missing, extra, stale, cross-
directive, differently hashed, or lifecycle-noncurrent evidence makes the
entire case `remediation_only`; it is not merely a lower node gate.

Value-state branches use this exact automation mapping after evidence passes:

| state/reason | base gate | reason code |
| --- | --- | --- |
| `known` | `candidate_only` | `literal_source_no_executable_contract` |
| `not_applicable` | `candidate_only` | `literal_source_no_executable_contract` |
| `unknown` + `conflicting_evidence` | `human_determination_required` | `conflicting_evidence_requires_human` |
| `unknown` + `source_ambiguous` | `human_determination_required` | `source_ambiguous_requires_human` |
| any other schema-valid `unknown` reason | `candidate_only` | `source_value_unresolved` |

An unknown's schema-valid reason, temporal scope, and evidence are preserved in
the gate canonical bytes. No gate rewrites the canonical state.

## 3. Slice-3A applicability node matrix

`controlling` means the effective gate enters the aggregate minimum unless a
controlling ancestor already carries it.

| node type | base-gate rule | controlling | required evidence purpose | propagating dependencies | fixed reason when not common |
| --- | --- | --- | --- | --- | --- |
| `product_scope` | always `candidate_only` | yes | `scope_clause` | present manufacturer mapping; model/serial/part designation scopes | `applicability_evaluator_not_reviewed` |
| `designation_scope` | unknown: common unknown rule; every other branch: `candidate_only` | yes | `designation_scope` | listed values or range nodes | ranges: `range_evaluator_not_reviewed`; series: `unsupported_expression`; otherwise `applicability_evaluator_not_reviewed` |
| `value_assertion` | common value-state rule | inherited | `_evidence_purpose` from 3A mapping | none | common |
| `identity_mapping` | always `candidate_only` because `review_state='unreviewed_candidate'` | inherited | none; inherits through source occurrence/evidence parent | none | `identity_mapping_unreviewed` |
| `designation_value` | `candidate_only` | inherited | inherited from designation scope | identity mapping when present | `applicability_evaluator_not_reviewed` |
| `designation_range` | `candidate_only`; lexical source storage is not an executable membership comparator | inherited | inherited from designation scope | none | `range_evaluator_not_reviewed` |
| `designation_group` | `association='unknown'`: common unknown rule; otherwise `candidate_only` | inherited | `condition_clause` | display assertion and all members | `condition_evaluator_not_reviewed` |
| `designation_group_member` | always `candidate_only` | inherited | `subject_value` | manufacturer assertion and designation identity mapping | model: `identity_evaluator_not_reviewed`; series: `unsupported_expression` |
| `condition` | always `candidate_only` because `evaluation_state='unevaluated'` and `evaluator_contract='none'` | yes | `condition_clause` | subject assertions and designation groups | `condition_evaluator_not_reviewed` |
| `expression` | always `candidate_only` because `evaluator_contract='none'` | yes through owning rule | none, inherited from referenced target | structural child expressions or exactly one typed leaf target | `expression_evaluator_not_reviewed` |
| `applicability_rule` | always `candidate_only` because `evaluator_contract='none'` | yes | `rule_clause` | scope root and optional condition root expressions | `rule_evaluator_not_reviewed` |
| `search_hint` | `candidate_only` because `controlling=false` and `exhaustive=false` | no | `search_hint_clause` | display assertion and hint groups | `noncontrolling_search_hint` |
| `search_hint_group` | `candidate_only` | no | `search_hint_clause` | source manufacturer assertion and hint models/mappings | `noncontrolling_search_hint` |
| `search_hint_model` | `candidate_only` | no | `search_hint_clause` | identity mapping | `noncontrolling_search_hint` |
| `change_dependency` | always `candidate_only` | yes, aggregate root | `supersession_clause` | none; exact external projection/signal binding is outside the node graph | resolved: `supersession_evaluator_not_reviewed`; unresolved: `change_dependency_unresolved` |

An `identity_mapping` relation to its source occurrence and evidence parent is
an integrity reference, not an additional propagation edge; propagation occurs
from the semantic owner that consumes the mapping. Search hints can never raise
or lower aggregate eligibility, but corruption in any hint still makes the
case remediation-only because exact candidate reconstruction failed.

## 4. Slice-3B obligation node matrix

| node type | base-gate rule | controlling | required evidence purpose | propagating dependencies | fixed reason when not common |
| --- | --- | --- | --- | --- | --- |
| `incorporated_document` | always `candidate_only`; retention assertion is schema-required unknown and no Slice-4 admission overlay exists | only when reached by an action document reference | `incorporated_document_clause`; child purposes `document_identity`, `document_retention` | identity/revision/retention assertions | `supporting_document_not_independently_admitted` |
| `value_assertion` | common value-state rule | inherited | purpose fixed by 3B occurrence mapping | none | common |
| `requirement` | always `candidate_only` | yes | `requirement_clause` | action, activation expression when present, every branch, timing, recurrence, terminating effect, prerequisites, referenced recurrence group | `requirement_evaluator_not_reviewed` |
| `action` | always `candidate_only` | inherited | `action_clause` | ordered action steps and referenced incorporated documents | `compliance_evaluator_not_reviewed` |
| `action_step` | always `candidate_only` | inherited | exact 3B evidence-link set | none | `compliance_evaluator_not_reviewed` |
| `branch` | unknown does not exist; every branch kind is `candidate_only` | inherited | `branch_clause` | condition expression for conditional/exception | `branch_evaluator_not_reviewed` |
| `expression` | always `candidate_only`; typed target remains a dependency | inherited | exact 3B occurrence purpose | structural child expressions or exactly one typed app/requirement target | `expression_evaluator_not_reviewed` |
| `timing_group` | unknown: common rule; known/not-applicable: `candidate_only` | inherited | `timing_clause` | timing terms only for known | `timing_evaluator_not_reviewed` |
| `timing_term` | always `candidate_only`; validator-2 proves only independent enum/shape membership and exact numeric representation, not an executable combination | inherited | `timing_term_clause` | none | `timing_evaluator_not_reviewed` |
| `recurrence` | unknown: common rule; every other branch: `candidate_only` | inherited | `recurrence_clause` | timing and conditioned expression when present | `recurrence_evaluator_not_reviewed` |
| `terminating_effect` | always `candidate_only` | inherited | `termination_clause` | none; terminated target references are integrity-only | `termination_evaluator_not_reviewed` |
| `recurrence_group` | always `candidate_only` | reached from each member requirement | exact 3B group timing evidence purposes | initial and recurring timing groups | `recurrence_evaluator_not_reviewed` |
| `amoc_provision` | always `candidate_only`; source-faithful general authority is not actual use | no; never creates aircraft use or compliance | `amoc_authority_clause` | authority assertion | `general_amoc_noncontrolling` |

All 3B expression leaf targets in Slice 3A inherit that target's effective gate.
Thus an activation/branch/recurrence expression that relies on an unevaluated
condition or rule is candidate-only. A `requirement_state_ref` inherits the
target requirement gate only after the prerequisite graph is proven acyclic.

An incorporated document that is not referenced by any action is
noncontrolling. It remains exactly reconstructed and its candidate-only gate is
stored, but it does not lower a requirement or aggregate gate. A referenced
document propagates through `action -> document`.

## 5. Exact dependency-edge matrix

Stored dependency rows have `(decision_version_id, parent_slice,
parent_node_id, edge_kind, child_slice, child_node_id, canonical_ordinal,
propagates_gate)`. The unique key is all fields except `propagates_gate`; the
flag is fixed below. Ordinals come from the authoritative relation row or a
fixed named slot, never query order.

| parent | child/reference | edge kind | ordinal | propagates |
| --- | --- | --- | --- | --- |
| 3A product scope | manufacturer identity mapping | `manufacturer_mapping` | fixed 0 | yes |
| 3A product scope | model, serial, part designation scope | `designation_scope` | fixed 0,1,2 | yes |
| 3A designation scope | value or range | `designation_member` | canonical ordinal | yes |
| 3A designation value | identity mapping | `designation_mapping` | fixed 0 | yes |
| 3A condition | direct value assertion | `condition_subject` | field-code order from mapping | yes |
| 3A direct condition manufacturer/model value assertion | its identity mapping when present | `condition_subject_mapping` | fixed 0 | yes |
| 3A condition | designation group | `condition_group` | canonical ordinal | yes |
| 3A designation group | display assertion | `group_display` | fixed 0 | yes |
| 3A designation group | member | `group_member` | canonical ordinal | yes |
| 3A group member | manufacturer assertion | `member_manufacturer` | fixed 0 | yes |
| 3A group member | designation mapping | `member_mapping` | fixed 1 | yes |
| 3A group-member manufacturer assertion | its identity mapping when present | `member_manufacturer_mapping` | fixed 0 | yes |
| 3A rule | scope/condition expression root | `rule_expression_root` | scope 0, condition 1 | yes |
| 3A rule | excluded rule | `rule_exclusion` | exclusion canonical ordinal | yes |
| 3A composite expression | child expression | `expression_operand` | edge sequence | yes |
| 3A leaf expression | scope/condition/rule target | `expression_target` | fixed 0 | yes |
| 3A search hint | display assertion/group | `search_hint_child` | display 0, groups 1+ordinal | yes, within noncontrolling subtree |
| 3A search group | manufacturer assertion/model | `search_group_child` | manufacturer 0, models 1+ordinal | yes, within noncontrolling subtree |
| 3A search-group manufacturer assertion | its identity mapping when present | `search_group_manufacturer_mapping` | fixed 0 | yes, within noncontrolling subtree |
| 3A search model | manufacturer assertion | `search_model_manufacturer` | fixed 0 | yes, within noncontrolling subtree |
| 3A search model | designation identity mapping | `search_model_mapping` | fixed 1 | yes, within noncontrolling subtree |
| 3A search-model manufacturer assertion | its identity mapping when present | `search_model_manufacturer_mapping` | fixed 0 | yes, within noncontrolling subtree |
| 3B document | its value assertions | `document_assertion` | field-code mapping order | yes |
| 3B requirement | action | `requirement_action` | fixed 0 | yes |
| 3B requirement | activation expression root | `requirement_activation` | fixed 1 | yes |
| 3B requirement | branch | `requirement_branch` | canonical ordinal | yes |
| 3B requirement | timing/recurrence/effect | `requirement_semantics` | timing 0, recurrence 1, effect 2 | yes |
| 3B requirement | prerequisite requirement | `requirement_prerequisite` | relation ordinal | yes |
| 3B requirement | referenced recurrence group | `requirement_recurrence_group` | fixed 0 | yes |
| 3B action | step | `action_step` | canonical ordinal | yes |
| 3B action | referenced document | `action_document` | relation ordinal | yes |
| 3B conditional/exception branch | expression root | `branch_expression` | fixed 0 | yes |
| 3B composite expression | child expression | `expression_operand` | edge sequence | yes |
| 3B leaf expression | 3A scope/condition/rule or 3B requirement | `expression_target` | fixed 0 | yes |
| 3B timing group | timing term | `timing_term` | canonical ordinal | yes |
| 3B recurrence | timing/expression | `recurrence_semantics` | timing 0, expression 1 | yes |
| 3B terminating effect | terminated requirement | `termination_target_integrity` | relation ordinal | no |
| 3B recurrence group | member requirement | `recurrence_member_integrity` | relation ordinal | no |
| 3B recurrence group | initial/recurring timing | `recurrence_group_timing` | initial 0, recurring 1 | yes |
| 3B AMOC provision | authority assertion | `amoc_authority` | fixed 0 | yes, within noncontrolling subtree |

Structural `parent_node_id` relationships not listed above must match the
projection exactly but do not create duplicate edges. Candidate evidence links,
datum containment, correction bindings, projection events, and identity source/
evidence-parent references are validated inputs, not decision gate edges.

Every identity mapping is consumed exactly once by one of the explicit mapping
edges above. SQL derives the expected inventory from
`ad_v4_candidate_app_identity_mappings.source_occurrence_node_id` and the typed
owner columns/pointer families: product manufacturer, listed model designation,
direct condition manufacturer/model assertion, group-member designation,
group-member manufacturer assertion, search-group manufacturer assertion,
search-model designation, or search-model manufacturer assertion. A mapping
outside those eight selectors, a selector without exactly one mapping when 3A
requires it, or any duplicate/omitted consumption edge is remediation-only and
cannot commit in an accepted graph.

The propagating graph must be acyclic. Existing validator/projection contracts
already reject applicability rule-reference, expression, prerequisite, and
termination cycles. Slice 4 independently performs topological sort and makes
the case remediation-only on any cycle. To avoid inventing a recurrence cycle,
recurrence-group membership is integrity-only; the member requirement depends
on its referenced group, while the group depends only on its two timing groups.
Termination target references are also integrity-only: a target obligation's
gate neither excuses nor contaminates the terminating-effect source claim.
Rule exclusions do propagate from the excluding rule to each excluded rule;
their canonical ordinals come from
`ad_v4_candidate_app_rule_exclusions.canonical_ordinal`, and the combined
expression/exclusion graph must remain acyclic.

Change-dependency targets are not semantic-node gate edges. For every 3A
`change_dependency`, the accepted decision has exactly one external-dependency
snapshot row. The row is derived from the dependency ID/hash/kind/AD numbers,
resolution state/reason, `target_projection_id`, and `source_dependency_id`.
For a resolved branch, it also binds the external target projection's ID,
proposal ID, projection hash, and current event-head hash plus the symmetric
source dependency's ID/hash when present. For an unresolved branch, all target
fields are null and the controlled unresolved reason is present. SQL derives
this bidirectionally from current change-dependency and projection/event rows;
any later external event/head/signal change stales acceptance. External targets
never create gate rows in this decision.

## 6. Aggregate prerequisite matrix

Before candidate-only acceptance, all entries must pass in one locked snapshot:

| prerequisite | failure classification/code |
| --- | --- |
| candidate verifier and exact canonical/evidence bytes | `remediation_only/candidate_integrity` |
| directive identity and at least one verified official source/evidence binding | `remediation_only/source_identity_or_evidence_missing` |
| current fragment heads all exactly the bound admitted events | `remediation_only/evidence_not_current` |
| verified 3A and 3B projections with exact cross-binding and reconstructions | `remediation_only/projection_integrity` |
| one or more product scopes | `remediation_only/minimum_product_scope_missing` |
| one or more applicability rules | `remediation_only/minimum_rule_missing` |
| one or more requirements, each with action and applicability binding | `remediation_only/minimum_requirement_missing` |
| complete node set, edge set, gate values, counts, reasons, hashes | `remediation_only/gate_graph_incomplete` |
| acyclic propagating graph | `remediation_only/gate_dependency_cycle` |
| every unknown has schema-valid reason, temporal scope, evidence, consequence | `remediation_only/unknown_contract_incomplete` |
| frozen authorship set and independent active signer for acceptance | `remediation_only/independent_signer_required` |

After those checks, the aggregate is the minimum effective gate among all
controlling root nodes: product scopes, applicability rules, requirements, and
change dependencies. Search hints, unused incorporated documents, and general
AMOC provisions are noncontrolling. All nodes still require exact integrity.
The aggregate must be `candidate_only`; any attempted higher state is rejected
as `release_evaluator_contract_unavailable`.

## 7. Independent PostgreSQL authority

The migration owns immutable SQL constants for the five version identifiers,
gate ranks, node-family rules, reason mappings, edge-kind matrix, fixed-slot
ordinals, controlling flags, and minimum counts. The service supplies rows, but
deferred constraint functions independently derive expected sets from:

- the exact bound 3A/3B projection roots and semantic/owner/relationship rows,
  including rule exclusions, every identity-mapping consumption, and external
  change-dependency targets/heads;
- live evidence binding/fragment/event rows;
- fixed evaluator/review-state columns already constrained by 0027/0028; and
- the review case/request/authorship/signoff rows.

Commit validation uses bidirectional `EXCEPT` comparisons for expected versus
actual node-gate and dependency sets, explicit count/hash comparisons, rank
checks, and closed event/state branches. A caller-supplied expected hash, JSON
snapshot, or reason never proves itself. SQL derives the expected base gate and
edge for each trusted source row and compares the stored canonical graph.

Acceptance triggers also lock the current actor then membership rows `FOR
UPDATE` and require
`users.status='active'`, matching membership user, membership status `active`,
and role `platform_admin`. They independently reject a signer whose user ID is
in the frozen authorship binding set. At review request and again at acceptance,
SQL independently derives the complete authorship source set as every
`ad_v4_candidate_submissions` row for the proposal plus the creator and admitted
event actor for every candidate-bound fragment. Bidirectional `EXCEPT`, exact
source-ID count, and set-hash comparisons reject a missing author, extra author,
forged cutoff, or append after request; supplied bindings cannot define their
own completeness. Rejection has no graph rows but must bind
the exact pending request, stored proposal ID/hash, observed-input digest,
reason codes, auth snapshot, predecessor event, and one terminal event.

Direct-SQL negatives must individually exercise every node family and edge
kind, missing/extra/swapped endpoints, wrong ordinal/propagation flag/reason/
gate/rank/count/hash, cycle, cross-projection/candidate/directive, stale
evidence/event heads, forged current membership, self-review, duplicate terminal
event, omitted rule-exclusion edge, missing/extra identity-mapping consumption,
forged external dependency, missing/extra authorship binding, forged authorship
cutoff, graph attached to rejection, absent graph on acceptance, and every
release-like state/event spelling. A forced direct-SQL signoff versus user or
membership role/status deactivation proves the `FOR UPDATE` conflict through
commit.

## 8. Observed-input envelope and review-case lifecycle

Cases, drafts, requests, rejections, and rejecting signoffs bind two domain-
separated canonical values. `paprnav-ad-v4-review-input-identity-1` is the
stable CAS identity and contains:

```text
{
  version,
  directiveId,
  proposal: {state, id, storedCanonicalHash, [verifiedCanonicalHash], [errorCode]},
  evidence: {state, storedBindingHash, [verifiedBindingHash], [headSetHash], [errorCode]},
  applicabilityProjection: {state, [id], [storedHash], [eventHeadHash], [errorCode]},
  obligationProjection: {state, [id], [storedHash], [eventHeadHash], [errorCode]}
}
```

Its canonical bytes/hash exclude all wall-clock, request, actor, and UI fields.
The full audit value is separately domain-separated as
`paprnav-ad-v4-review-observation-1`:

```text
{version, inputIdentityHash, observedAt}
```

States are exactly `verified`, `missing`, `stale`, `integrity_error`, and
`unsupported_version`. Bracketed fields are absent, never JSON null, unless the
branch provides the underlying row. `verified` requires all applicable ID,
verified hash, and head fields and forbids `errorCode`; every other state
requires one stable controlled error code, forbids a verified hash, and retains
stored ID/hash/head fields only when the row was actually observed. Proposal is
never `missing` because case creation requires its FK row, but may have any
other state. Projection `missing` has no ID/hash/head. The server derives both
the input identity and audit envelope; clients receive/send only the stable
`inputIdentityHash` as CAS. At submit, the server freshly derives the identity
and compares that stable hash. Elapsed time alone changes the audit-envelope
hash but not the input-identity hash.

A draft/request freezes both identity and observation bytes/hashes. A rejection
stores `requested_input_identity_hash`, `requested_observation_hash`, a freshly
derived `decision_input_identity_bytes/hash`, and
`decision_observation_bytes/hash`, plus reason codes explaining mismatches. A
rejecting signoff binds both identity hashes and both audit hashes and need not have verified projections,
evidence, or candidate reconstruction. Candidate-only acceptance instead
requires every component `verified`, exact fresh hashes/heads, and a complete
decision graph; it does not use a nonverified branch as authority.

### Review-case lifecycle and CAS matrix

`ad_v4_review_cases` identity is `(proposal_id, case_sequence)`; sequence starts
at zero and is contiguous. Case creation is an explicit authorized POST under
the proposal's relationship advisory lock and a proposal-scoped review-case
advisory lock. It appends `case_created` sequence zero. It may bind stored
proposal identity even when current verification fails, so remediation remains
auditable. `predecessor_case_id` is null for sequence zero and exactly the prior
case thereafter.

| folded state | allowed next event | required bound object | next state |
| --- | --- | --- | --- |
| `draft` | `draft_saved` | immutable draft revision and previous event hash | `draft` |
| `draft` | `review_requested` | latest draft (optional only when no drafts), observed-input snapshot, authorship cutoff, auth snapshot | `pending_review` |
| `pending_review` | `review_rejected` | rejection row, signoff row, expected request/event | `rejected` |
| `pending_review` | `candidate_only_accepted` | complete decision graph/version, independent signoff, expected request/event | `candidate_only` |

No other transition exists. A terminal case is immutable. Re-review after
policy/evaluator/document changes creates a successor case; semantic correction
also requires a successor candidate/projections, then its own case. Only one
open (`draft` or `pending_review`) case may exist per proposal. Review request
freezes submission/relationship/fragment lifecycle/projection event counts and
heads. Any later append/current-head change makes acceptance stale; rejection
may still bind and describe the observed/current mismatch.

Every mutating request has a scoped idempotency key and canonical request hash.
Exact retry returns the prior row/event. Different bytes under a reused key
return conflict. Terminal event uniqueness is `(case_id,
predecessor_event_hash)` plus one terminal event per case. Forced concurrency
must prove only one terminal transaction commits.

CAS tests hold every input identity constant while advancing time and require
success with the same stable identity hash and a different audit hash. Separate
tests change each candidate/evidence/projection/event-head component and require
stale conflict. Rejection tests retain both timestamped observations even when
their stable identity hashes are equal.

## 9. Authorization snapshots and historical reads

Current membership validity is exactly `status_only_v1`: active user, active
membership, matching user ID, and `platform_admin` role. There are no membership
valid-from/until columns. Canonical auth snapshots explicitly store null
`validFrom`/`validUntil`, the user and membership `updated_at` values,
authorization-observation hash, policy/action/version, claims hash, server
result, and decision time.

The service uses fresh scalar `FOR UPDATE` queries; the deferred SQL trigger
checks the same relationship under `FOR UPDATE` in actor-then-membership order.
Historical verification compares
the frozen auth bytes/hash and referenced IDs under
`paprnav-ad-v4-candidate-review-1`; it never requires the user's present status
to equal the historical snapshot. Current eligibility separately reports later
deactivation or policy obsolescence.

All GET/list/download verification uses a separate read-only `REPEATABLE READ`
transaction. The exact historical gate/dependency/form/lifecycle/auth versions
remain dispatchable while referenced. Unknown historical versions fail closed
as `historical_verifier_unavailable`; current code is never substituted.

## 10. Form-projection matrix

Slice 4 renders semantics read-only. There is no browser form-to-canonical
serializer. Every field comes from verified canonical candidate bytes; typed
projections provide cross-checks and counts, not replacement values.

| validator-2 proposal family | UI projection | editability | preservation/check |
| --- | --- | --- | --- |
| `schemaVersion`, `decisionKey` | identity header | read-only | exact strings |
| `directiveIdentity` | typed identity fields with known/unknown/NA badges and evidence links | read-only | every property/presence in canonical order |
| `officialDocuments` | source cards, role, identifier, hash, page links | read-only | ordered exact entries and retained-source binding |
| `evidenceBindings` | evidence workspace keyed table and semantic-use reverse index | read-only | exact key set, fragment/event/hash/locator/text checks |
| `incorporatedDocuments` | document cards and retention blocker | read-only | ordered exact document/value-state fields; no admission overlay |
| `productScopes` | role/manufacturer/designation table | read-only | canonical set order, property absence, values/ranges/groups |
| `conditionDefinitions` | shared-condition library and typed subject/group members | read-only | exact keys, enums, optional presence, reuse counts |
| `applicabilityRules` | tree builder-style visualization | read-only | exact AST order, references, exclusions, evidence |
| `requirements` | requirement/action/branch/timing cards | read-only | exact sequence, ordered steps, document refs, expressions, dependencies, effects |
| `recurrenceGroups` | group/member and initial/recurring timing table | read-only | exact member order and references |
| `applicabilitySearchHints` | visibly noncontrolling hint tables | read-only | exact groups/models/order and `controlling=false`, `exhaustive=false` |
| `amocAuthorityProvisions` | general-authority warning card | read-only | exact authority assertion/evidence; never aircraft use |
| `supersessionRelations` | predecessor/successor relation table | read-only | exact order, state, unresolved reason, targets |
| `authoritativeCorrections` | correction relationship/diff metadata | read-only | exact changed refs/evidence/reason/generation bindings |

The page also renders immutable proposal submissions and relationships,
projection versions/hashes/counts, node gates/reasons, dependency explanations,
authorship conflicts, draft annotations, event history, and the release-blocker
summary. A semantic diff compares canonical JSON pointers/hashes only; it does
not generate a successor. Canonical download returns the exact stored bytes.

Five-fixture tests snapshot every section, array order, absent/present property,
reference target, and canonical download hash. Focused examples cover shared
conditions, recurrence groups, ordered action steps, corrections, all unknown
branches, noncontrolling hints, and empty optional arrays.

## 11. Hand-declared calibration oracle

All five committed validator-2 calibration packets have expected aggregate
`candidate_only` and release blocker `rule_evaluator_not_reviewed`. Exact node
and reason counts are generated once into a reviewed golden artifact from this
matrix, then treated as hand-approved fixture expectations; tests do not derive
their expected values by calling the code under test.

Additional required cases:

- known-value synthetic packet: `candidate_only`, with its controlling rule and
  expression blocked only by evaluator contract `none`;
- missing 3A or 3B projection: `remediation_only/projection_integrity`;
- current fragment quarantine: `remediation_only/evidence_not_current`;
- 2008-26-10 incorporated-document-dependent action:
  `candidate_only/supporting_document_not_independently_admitted` in addition
  to evaluator blockers;
- independent second administrator: candidate acceptance succeeds;
- proposal/fragment creator or admitter as signer:
  `remediation_only/independent_signer_required`; and
- any fabricated release state/event: commit rejection.
