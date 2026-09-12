# Decision packet: T081-V4-SCHEMA-SLICE-3A

Status: design reviewed; IA-001 holistic mapping amendment independently passed

Builder: `/root/v4_schema_builder`

Governing contract: `.ai/AD_EXTRACTION_DOMAIN_CONTRACT.md` version 1.1

Predecessor: closed `T081-V4-SCHEMA-SLICE-2` candidate-validation and
immutable-proposal boundary

## 2026-09-10 IA-001 normative mapping amendment

The complete occurrence, owner, nullability, evidence, identity, ordering,
reference, materialization, PostgreSQL, read-verification, and test contract is
`ia001-normative-mapping-matrix.md`, mapping version
`paprnav-ad-v4-applicability-mapping-1`. It governs section 2's implementation
details where it is more explicit. The independent holistic design gate passed
at packet SHA-256
`c4f91844476097f5ba733ad20c7b025ad0811c695e599c87170be3712fbd1564`;
see `adversarial-design-ia001-matrix-final.md`.

Two source-fidelity clarifications amend the earlier identity-mapping union:

- atomic `conditionSubject.modelOrSeries` uses the candidate-only mapping kind
  `model_or_series`; it must not be relabeled as model or series; and
- a present product `manufacturer.normalizedIdentity` remains origin
  `candidate_payload` for its exact known, unknown, or not-applicable branch.
  The latter two preserve their canonical reason and temporal scope rather than
  being collapsed to `no_normalized_identity/not_extracted`.

The mapping manifest also freezes validator-2 resource limits and requires
unbounded text for pointer-derived semantic keys. These amendments were made
before further schema edits.

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
  value, canonical ordinal, and a model identity-mapping node for each listed
  model occurrence. Listed serial/part-number occurrences retain exact typed
  values but have no identity mapping because the closed identity-kind domain
  contains neither serial nor part number; they must never be relabeled model
  or series;
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
