# Decision packet: T081-V4-SCHEMA-SLICE-3B

Status: framed; independent design review required before implementation

Builder/coordinator: `/root`

Committed base: `9ad410b feat: add candidate-only V4 applicability projection`

Governing contract: `.ai/AD_EXTRACTION_DOMAIN_CONTRACT.md` version 1.1

Predecessors:

- closed `T081-V4-SCHEMA` retained-evidence slice;
- closed `T081-V4-SCHEMA-SLICE-2` immutable candidate boundary; and
- closed `T081-V4-SCHEMA-SLICE-3A` candidate applicability projection.

Normative companion: `normative-mapping-matrix.md` in this review run.

## Objective

Implement, after independent design approval, the candidate-only V4 obligation
projection. Slice 3B losslessly materializes these four canonical proposal
fields from an already verified validator-2 candidate:

```text
incorporatedDocuments
requirements
recurrenceGroups
amocAuthorityProvisions
```

The projection preserves each requirement once, its activation and branch
expressions, ordered action steps, incorporated-document references,
prerequisites, initial and recurring timing, recurrence-group membership,
terminating effects, and general AD AMOC authority. It also completes the
generation-1 semantic bindings for existing correction references owned by
`slice_3b`.

This is not an approval or release slice. It creates no signed decision,
current-selection pointer, released catalog row, aircraft match, compliance
credit, or due-state result. Expression and timing evaluation are deliberately
excluded. Every stored row remains `candidate_only` and exists only for
platform-administrator audit and later reviewed publication work.

## User-visible outcome

With default-off application and database capabilities enabled, an active
platform administrator can:

1. request idempotent Slice-3B materialization for a validator-2 proposal that
   already has a verified current Slice-3A projection;
2. list and inspect obligation-projection audit metadata; and
3. retrieve a verified reconstruction of the four Slice-3B canonical fields.

The detail, list, and reconstruction reads fail closed with HTTP 409 when any
typed owner, value, edge, evidence link, correction binding, count, byte, or
hash differs. GET performs detection only and never repairs or commits.

There is no maintenance-shop, aircraft-owner, released-catalog, or frontend
change in this slice.

## Safety and correctness invariants

These statements are falsifiable implementation gates.

1. Only a verified `paprnav-ad-v4-validator-2` / `paprnav-ad-v4-c14n-2`
   candidate can be materialized; validator-1 candidates remain readable and
   byte-identical but are ineligible for 3B.
2. Materialization requires one verified, non-stale Slice-3A projection for the
   same proposal and the fixed app materializer version
   `paprnav-ad-v4-app-materializer-2`. It never creates or repairs 3A as a side
   effect.
3. The 3B projection is immutable, proposal-scoped, `candidate_only`, and
   uniquely identified by `(proposal_id, materializer_version)`.
4. Its stored subtree has exactly the four canonical fields above. Restricted
   JCS determines object-key order, and the bytes use a domain-separated hash.
5. Generic datum rows are a complete exact JSON-pointer projection: no missing,
   extra, reordered, cross-projection, differently typed, or differently
   valued datum graph can commit.
6. Every 3B semantic node has exactly one matching physical typed owner. No
   node may have zero owners, multiple owners, an owner from another family, or
   an owner whose type/key/pointer/parent/ordinal/hash differs.
7. Incorporated-document identity remains source-faithful. `documentType`,
   `documentNumber`, `revision`, `retention`, and evidence are distinct. An
   unknown retention state cannot become retained, admitted, or actionable.
8. Known/unknown/not-applicable document and authority assertions preserve the
   exact branch, value or reason, temporal scope, evidence order, and hash.
   SQL NULL represents structural absence only, never uncertainty.
9. Every independently actionable canonical requirement produces exactly one
   requirement owner regardless of the number of product scopes or models in
   Slice 3A.
10. Requirement sequence is unique and contiguous from 1 but remains distinct
    from canonical array order, which is by `requirementKey`. Action steps
    preserve sequence; set-valued references preserve canonicalized lexical
    order. Sequence text is matched against the exact textual set `1..N`
    before any integer conversion, where the schema caps N at 2,000.
11. Each requirement has exactly one action, branch, initial-timing owner,
    recurrence owner, and terminating-effect owner, plus exactly the optional
    recurrence-group reference declared by the canonical object.
12. Action type, ordered-step presence and values, approved-data document
    references, and evidence are exact. A reference resolves to one
    same-proposal incorporated-document owner and cannot imply that its bytes
    were retained or reviewed.
13. Activation, branch-condition, and conditioned-recurrence expressions are
    lossless ordered trees. Every node has one root/parent position, correct
    arity, one owning requirement/context, exact canonical hash, and no cycle.
14. Expression leaves resolve exactly: `scope_ref`, `predicate_ref`, and
    `rule_ref` target the expected same-proposal Slice-3A semantic node;
    `requirement_state_ref` targets the expected same-proposal Slice-3B
    requirement and retains its exact required state.
15. Branch unions are exact. `required` forbids condition/alternative fields;
    `conditional|exception` require one expression root and forbid alternative
    fields; `alternative_member` requires group key and boolean exclusivity and
    forbids a condition root.
16. Prerequisite, alternative-group, requirement-state, and termination
    relationships are same-proposal and reproduce the candidate's complete
    acyclic requirement graph. Empty sets are represented by zero edge rows,
    not placeholders.
17. Timing union state is exact. Known plans require logic and at least one
    ordered term and forbid reason/temporal fields. Unknown/not-applicable
    require exact reason and temporal scope and have no terms or logic.
18. Each timing term preserves metric, canonical decimal text, queryable
    arbitrary-precision numeric value, unit, comparator, anchor, evidence,
    and ordinal. The 16,384-character bound is checked before conversion; a
    longer forged parent yields `timing_interval_resource_limit`. No binary
    float conversion or scale-changing rewrite occurs.
19. Recurrence unions are exact: `none`, `interval`, `conditioned`, and
    `unknown` have their required and forbidden children. A conditioned
    recurrence has one condition-expression root and one known timing plan.
20. Recurrence groups have at least two exact members, fixed completion policy
    `all_active_requirements`, exact initial/recurring timing owners, and
    bidirectionally identical group membership. Grouped requirements cannot
    repeat inline timing or recurrence.
21. General AMOC provisions preserve only provision key, approving-authority
    union, and AD-clause evidence. No aircraft, compliance event, approved
    method, timing override, authenticity claim, or actual AMOC-use field is
    accepted or stored.
22. Every semantic evidence link resolves to the exact same-proposal Slice-2
    binding, has the correct purpose and canonical ordinal, and recomputes its
    deterministic identity/hash. Inherited evidence is specified per owner and
    never guessed from a nearby node.
23. Every existing correction root/ref/evidence row remains byte- and
    identity-stable. For each `owner_slice='slice_3b'` ref, 3B appends exactly
    one generation-1 obligation binding to the exact same-proposal typed node.
    It cannot update or duplicate the correction foundation or its evidence.
24. The correction-binding table represents 3A and 3B ownership with mutually
    exclusive FK-backed column pairs. Existing 3A rows retain their IDs,
    hashes, app projection/node IDs, and meaning during migration.
25. Python construction, generated mapping expectations, PostgreSQL deferred
    validation, and verified reads agree for every closed union and occurrence
    shape in `normative-mapping-matrix.md`.
26. PostgreSQL commit-time validation reconstructs the 3B subtree solely from
    typed owners and requires equality with generic datum reconstruction,
    stored subtree bytes/hash, projection bytes/hash, verified proposal bytes,
    the 3A parent identity, and all stored counts.
27. Direct SQL cannot forge a validator-2 envelope and self-consistent 3B graph
    around invalid parent semantics. The deferred validator independently
    checks the closed accepted grammar and exact candidate projection rather
    than trusting stamped version strings.
28. INSERT, UPDATE, and DELETE on every 3B and amended shared-correction table
    mark affected projections for deferred validation. Immutable triggers are
    defense in depth, not the only update/delete protection.
29. Detail/list/reconstruction GETs reverify proposal bytes, live evidence,
    Slice 3A integrity, the full expected 3B graph, correction bindings, and
    typed reconstruction in one PostgreSQL repeatable-read, read-only snapshot.
    Corruption returns controlled 409, never partial data or an unhandled 500.
30. GET performs no insert, update, delete, flush, commit, stale repair, or
    audit event. Deterministic stale repair is reachable only inside an
    authorized, gate-checked materialization POST transaction.
31. Materialization authorization is the exact selected active
    `platform_admin` organization-membership row. Roles are not combined across
    memberships; actor and membership are locked/rechecked inside the write.
32. Application and database write gates are default false. After locking the
    proposal, the POST locks/rechecks `validator2_write_enabled`, then
    `materializer3a_enabled`, then `materializer3b_enabled`; only afterward does
    it lock the parent Slice-3A projection.
33. Idempotent retry returns the identical complete projection/request. Key
    reuse with different proposal or request bytes returns 409 and writes
    nothing. Concurrent identical writes converge without a 500.
34. The complete lock order is the existing Slice-3A-compatible order defined
    in section 11. Gate order is fixed, not lexical. Downgrade, gate
    administration, and concurrent 3A/3B materializers use compatible subsets
    and translate deadlock/serialization victims to controlled retry/conflict,
    never an unhandled 500.
35. No 3B table, index, service, API, or test becomes a released reader,
    aircraft-matching input, compliance fact, terminating-action credit,
    next-due input, or V3 fallback.
36. V1/V2 candidate storage, all Slice-3A bytes/hashes, 0028-aware Slice-3A
    verified reads, V3 audit rows, released catalog, matching, coverage,
    recurrence, and due-state behavior remain unchanged. The 3B gate stays off
    until all readers are 0028-aware, and rollback to `9ad410b` is prohibited
    after the first 3B binding.
37. Occupied downgrade refuses before destructive DDL while holding locks that
    prevent insertion races. Empty downgrade/re-upgrade succeeds, and failed
    downgrade leaves all data and gates usable.
38. The five calibration proposals materialize and round-trip exactly, with
    packet-specific obligation/timing/document/AMOC cardinalities and the
    source-accounted evidence oracle unchanged.

## Current behavior

Slice 2 already parses, schema-validates, semantically validates, canonicalizes,
hashes, evidence-binds, and stores the entire validator-2 proposal as immutable
candidate JSON. It validates requirement references, requirement cycles,
recurrence memberships, correction references, and evidence existence, but it
does not provide queryable obligation rows or independent relational
reconstruction.

Slice 3A materializes only `productScopes`, `conditionDefinitions`,
`applicabilityRules`, and `applicabilitySearchHints`. Its semantic expressions
are owned by applicability rules and intentionally reject
`requirement_state_ref`. It creates the shared correction foundation and the
complete changed-reference namespace, but only binds 3A-owned references.

The current `ad_v4_candidate_correction_semantic_bindings` implementation has
non-null FKs named `projection_id` and `semantic_node_id` that point only to
Slice-3A tables. That is valid for the closed 3A scope but cannot represent the
already-designed future 3B binding. Migration 0028 must make the owner pair
explicit without changing existing IDs or hashes.

Existing normalized V3 tables (`ad_compliance_requirements`, triggers, AMOC
rows, target-applicability links) are released/transitional structures with
different cardinality and audit semantics. They are not valid 3B authority and
must not be written by this slice.

## Proposed design

### 1. Version and projection boundary

The fixed versions and domains are:

```text
materializer: paprnav-ad-v4-obligation-materializer-1
mapping:      paprnav-ad-v4-obligation-mapping-1
generator:    paprnav-ad-v4-obligation-mapgen-1
subtree:      paprnav:ad_extraction_v4:obligation-subtree:paprnav-ad-v4-c14n-2\0
projection:   paprnav:ad_extraction_v4:obligation-projection:1\0
row:          paprnav:ad_extraction_v4:obligation-row:1\0
request:      paprnav:ad_extraction_v4:obligation-request:1\0
event:        paprnav:ad_extraction_v4:obligation-projection-event:1\0
binding-set:  paprnav:ad_extraction_v4:obligation-correction-binding-set:1\0
```

`ad_v4_candidate_obligation_projections` stores proposal/directive/version
identity, the exact parent 3A projection ID/hash, the four-field subtree
bytes/hash, projection-envelope bytes/hash, `candidate_only`, expected counts,
and creation time. Its identity preimage is the exact object
`{proposalId,appProjectionId,materializerVersion,subtreeHash}` defined in the
normative matrix.

The projection envelope includes all stored identity/hash values and the exact
immutable structural count inventory in the mapping matrix. It is canonicalized
with the closed internal-record c14n-2 profile and domain-hashed. Candidate
source c14n-2 remains number-free; the internal profile admits only strings,
booleans, null, and nonnegative integers through the PostgreSQL `integer`
maximum (2147483647) required by exact ordinals, counts, and sequence numbers.
It rejects U+0000 strings/keys, floats/decimals, negative or larger integers,
non-built-in JSON containers, cycles, and nesting deeper than the generated
resource limit. Validator-2 rejects U+0000 before candidate JSONB persistence.
Python and PostgreSQL must emit byte-identical numeric JSON tokens. Requests and projection events are append-only
audit children and are explicitly excluded from frozen root counts; each is
validated by its own identity and event-chain contract.

### 2. Drift-minimizing mapping contract

Add a closed data-only mapping manifest
`backend/app/contracts/ad_v4_obligation_mapping_v1.json` and schema
`backend/app/contracts/ad_v4_obligation_mapping.schema.json`. The manifest
contains only enumerated selectors, occurrence types, pointer/key/parent/
ordinal derivations, typed-owner columns, evidence policies, relationship
targets, ordering, cardinality, and resource limits. It contains no Python
callables, SQL text, JSONPath, regex supplied at runtime, or opaque prose rules.

Generator `scripts/generate_ad_v4_obligation_mapping.py` produces:

- `backend/app/services/ad_v4_obligation_mapping_v1.py`, used by the pure
  expected-graph walker and ORM adapter; and
- `backend/app/db/migrations/sql/20260911_0028_obligation_expectations.sql`,
  used by migration 0028 for expected-relation and repetitive exact-comparison
  logic.

All four files carry/freeze manifest version, manifest SHA-256, generator
version, and generator-source SHA-256. `--check` regenerates into a temporary
directory and byte-compares both outputs. PostgreSQL exposes the frozen mapping
digest; tests require source manifest, generated Python, generated SQL, and the
migrated database digest to agree.

The manifest binds structure, not the safety claim by itself. These defenses
remain independently hand-implemented and parity-tested:

- validator-2 JSON Schema and semantic validation;
- PostgreSQL CHECK/FK/unique/deferred set equality, graph cycles, exact owner
  union, typed reconstruction, and immutable-row enforcement;
- Python verified-read comparison and typed reconstruction; and
- direct-SQL corruption tests, which must not reuse the construction adapter.

Hand-written global algorithms are named in the manifest and limited to
the source and closed internal-record profiles of restricted-JCS assembly,
graph cycle traversal, decimal parsing, and final
projection/event folding. A digest cannot substitute for branch-vector parity.

### 3. Generic graph and evidence

`ad_v4_candidate_obligation_semantic_nodes` mirrors the proven 3A identity
model with obligation-specific row domains. It records proposal/projection,
parent, node type, unbounded node key and source pointer, canonical node hash,
and nonnegative ordinal.

`ad_v4_candidate_obligation_data` losslessly represents every object, array,
string, and boolean occurrence under the four-field root. Decimal intervals
remain strings in canonical JSON; numeric query values live only in typed term
owners.

`ad_v4_candidate_obligation_evidence_links` binds each evidence-bearing
semantic occurrence to the exact Slice-2 candidate binding. Purpose is closed
to:

```text
incorporated_document_clause
document_identity
document_retention
requirement_clause
action_clause
branch_clause
timing_clause
timing_term_clause
recurrence_clause
termination_clause
amoc_authority_clause
```

Evidence order is canonical order from the candidate after set
canonicalization. Container evidence is not silently inherited by a child;
the matrix states the exact evidence source for every owner.

### 4. Incorporated documents

`ad_v4_candidate_obligation_documents` owns each canonical document and stores
key, type, canonical ordinal, and FKs to exactly three value assertions.

`ad_v4_candidate_obligation_value_assertions` stores document number,
revision, retention, and AMOC approving authority. It uses a closed field-code
registry and the exact known/unknown/not-applicable state with mutually
exclusive value versus reason/temporal columns. Retention is constrained to
the canonical unknown branch in validator-2; no source-document FK or admitted
state is created in this slice.

There is no fuzzy normalization and no interpretation of a document reference
as proof that incorporated content was seen.

### 5. Requirements, actions, and branches

`ad_v4_candidate_obligation_requirements` owns one canonical requirement with
key, sequence value, canonical ordinal, requirement type, optional recurrence
group key, and FKs to its action, branch, initial timing, recurrence, and
terminating-effect nodes.

Before Python or PostgreSQL converts a sequence to integer, it checks length at
most 16,384 and membership in `{str(i): i for i in
1..requirement_count}`. A longer value fails with
`requirement_sequence_resource_limit`; any other nonmember, alternate spelling,
duplicate, or gap fails with `invalid_requirement_sequence`. Only the mapped
value, necessarily at most the schema's 2,000-requirement cap, is stored in the
integer query column. The Slice-2 semantic validator is amended to use the same
pre-conversion rule so a normal request cannot surface Python's integer-string
conversion limit.

`ad_v4_candidate_obligation_actions` owns exactly one action per requirement.
`..._action_steps` stores optional ordered step strings and exact ordinals.
`..._action_document_refs` stores the canonicalized set of same-projection
document references and exact ref hashes.

`ad_v4_candidate_obligation_branches` stores the exact branch discriminator,
optional alternative group key/exclusive flag, and optional condition-
expression root. `..._requirement_dependencies` stores prerequisite edges.
`..._terminating_effects` owns the union, and
`..._termination_edges` stores its referenced requirements.

Alternative groups remain a relationship among branch owners; no independent
canonical object is invented. Validator-2 does not require two members or
identical `exclusive` values across members, so 3B preserves every member
exactly and adds no cross-member semantic restriction. A future evaluator must
classify singleton or mixed-exclusivity groups as unresolved unless a reviewed
validator version defines stronger rules; 3B never chooses an alternative.

### 6. Requirement expressions and cross-slice references

`ad_v4_candidate_obligation_expressions` owns every expression node under one
requirement and one of three contexts:

```text
activation
branch_condition
recurrence_condition
```

It stores path within the context, node type, optional requirement-state value,
and mutually exclusive target columns. `scope_ref`, `predicate_ref`, and
`rule_ref` reference the exact same-proposal Slice-3A semantic node through
composite FKs including the fixed parent app projection. A
`requirement_state_ref` references a same-projection requirement owner. `not`,
`all`, and `any` have no leaf target.

`ad_v4_candidate_obligation_expression_edges` stores exact parent/child
ordinal. Deferred checks enforce one root, one incoming edge for every nonroot,
same owner/context, arity, reachability, and acyclicity. The candidate validator
already rejects a combined requirement graph cycle; PostgreSQL recomputes it
from expression, prerequisite, and terminating edges at commit.

No expression is evaluated in 3B. `requirementState='unknown'` is a literal
requested comparison state, not the evaluator's result.

### 7. Timing and recurrence

`ad_v4_candidate_obligation_timing_groups` owns each timing occurrence with
owner kind:

```text
requirement_initial
requirement_recurrence
recurrence_group_initial
recurrence_group_recurring
```

It stores exact union state (`known|unknown|not_applicable`), known logic or
unknown/not-applicable reason and temporal scope, canonical ordinal, and term
count. Unknown and not-applicable have zero terms.

`ad_v4_candidate_obligation_timing_terms` stores one ordered term with metric,
exact interval text, PostgreSQL arbitrary-precision numeric interval, unit,
comparator, anchor, canonical ordinal, and hash. PostgreSQL validates that the
text matches the canonical decimal grammar and casts exactly without overflow
or float conversion. Reconstruction uses the verified interval text.

The materializer freezes `MAX_TIMING_INTERVAL_CHARS = 16_384`, matching the
Slice-2 raw-parser string limit. Python and PostgreSQL check both the canonical
decimal grammar and this bound before any decimal/numeric conversion. A forged
parent containing a longer value fails with the stable integrity code
`timing_interval_resource_limit`; it is never passed to a PostgreSQL cast. At
the bound, the largest fractional scale is 16,382 digits (`0.` plus digits),
below PostgreSQL `numeric`'s 16,383 fractional-digit limit, and the largest
integer magnitude is 16,384 digits, below its 131,072 integer-digit limit.
Tests cover the exact limit, limit plus one, integer-heavy and fractional-heavy
values, and direct-SQL forged parents. Exact text remains authoritative; the
numeric column is a query projection only.

`ad_v4_candidate_obligation_recurrences` owns one exact recurrence union per
requirement. It holds optional timing and condition-expression roots according
to the discriminator.

`ad_v4_candidate_obligation_recurrence_groups` owns each group, and
`..._recurrence_group_members` stores the canonicalized requirement-key set.
Each group points to exact initial and recurring timing owners. Deferred
validation compares membership in both directions and rejects inline timing on
grouped requirements.

This slice stores timing semantics; it does not calculate deadlines or decide
whether a branch/requirement is active.

### 8. General AMOC authority

`ad_v4_candidate_obligation_amoc_provisions` owns each canonical general
provision with key, ordinal, and approving-authority assertion FK. Its schema
has no aircraft-specific fields. The API response labels it general authority
and `candidate_only`; it never uses the phrase “approved AMOC use.”

No row is written to existing aircraft compliance, AMOC-use, event, match, or
due-state tables.

### 9. Shared correction binding amendment

Migration 0028 changes no existing correction binding identity or hash. It:

1. makes existing `projection_id` and `semantic_node_id` nullable but retains
   their 3A FKs and stored values;
2. adds nullable `obligation_projection_id` and
   `obligation_semantic_node_id` with composite same-proposal 3B FKs; and
3. adds a closed CHECK:

```text
binding_slice = 'slice_3a'
  => app pair non-null and obligation pair null
binding_slice = 'slice_3b'
  => app pair null and obligation pair non-null
```

The legacy column names remain for compatibility and mean the 3A pair. Existing
rows are backfilled/validated under locks before nullability changes. The
existing unique `correction_ref_id` continues to allow exactly one semantic
binding per changed reference. Existing Slice-3A bindings retain exactly the
committed identity:

```text
row_id(
  paprnav:ad_extraction_v4:applicability-row:2\0,
  "correction-binding",
  {"refId": correction_ref_id, "semanticId": semantic_node_id}
)
```

The property names and two-property identity object above are byte-contract
data; `bindingSlice`, generation, and projection ID are not separately present
in that preimage. A new 3B binding uses the same exact two-property shape and
table label with its obligation semantic-node ID, but under
`paprnav:ad_extraction_v4:obligation-row:1\0` and the `avk_` row-ID prefix. The
semantic-node ID itself binds the target projection. The hash domain is chosen
by `binding_slice`; existing rows are never restamped. Upgrade,
materialization, failed-downgrade, and downgrade/re-upgrade tests compare the
existing 3A binding ID and full hash byte-for-byte.

The 3A commit/read validator is amended only to accept the structurally valid
new 3B alternative while continuing to require exact 3A values for 3A refs.
The 3B validator requires every 3B ref and rejects any foundation ref binding.

### 10. Completeness and read verification

Deferred procedure
`paprnav_v4_candidate_obligation_require_complete(projection_id)`:

1. acquires proposal and feature-gate locks in the global order;
2. verifies parent candidate bytes/hash/version/evidence and the exact 3A
   projection identity/hash;
3. derives the exact four-field canonical subtree;
4. compares expected versus actual generic data and semantic nodes;
5. verifies every typed owner, edge, reference, evidence link, ID, hash,
   count, nullability branch, ordinal, and exactly-one-owner union;
6. verifies complete 3B correction bindings without changing the foundation;
7. independently reconstructs the typed subtree and requires JSON equality;
8. recomputes subtree/projection bytes and hashes; and
9. validates the materialization request and root event.

Constraint triggers cover INSERT/UPDATE/DELETE for every new child/root table
and the amended shared binding table. A transaction that forces constraints
early and then appends another row is revalidated at commit through a dirty
projection set keyed by both OLD and NEW parent identities.

Python verified reads independently derive the complete expected graph from
the verified candidate, query every table, compare exact neutral records, and
reconstruct from typed owners. They never treat generic data as a query escape
hatch. Untrusted stored ordinals are range-checked and matched before use; all
loops zip against canonical expected items.

Each detail, list, and reconstruction GET performs its entire verified read in
one separate PostgreSQL `REPEATABLE READ`, read-only transaction. After the
outer route has parsed credentials and checked the application route flag, that
snapshot rechecks the exact active membership and database read gates, then reads the candidate,
evidence lifecycle, candidate relationships, Slice-3A projection/event state,
corrections, full 3B graph, and 3B event chain. The read session always rolls
back/closes and never flushes or commits. List captures and verifies its entire
result set in one snapshot. Forced-interleaving tests define the consistency
point against evidence invalidation, correction/replacement relationships, and
parent-3A stale transitions: a response is wholly before or wholly after the
concurrent commit, never a mixed observation.

### 11. Authorization, gates, idempotency, and events

Add application flag `PAPRNAV_AD_V4_SLICE3B_ROUTES_ENABLED=false` and database
gate `materializer3b_enabled=false`. Audit routes require the application flag
and an exact active platform-admin membership. Materialization additionally
requires the validator-2 application flag and all three database gates listed
in invariant 32.

`ad_v4_candidate_obligation_materialization_requests` stores actor,
membership, organization, role/status snapshots, policy/action/version,
idempotency key, proposal/app projection/materializer identity, canonical
request bytes/hash, auth claims hash, and timestamp.

`ad_v4_candidate_obligation_projection_events` is append-only. Sequence zero is
exactly one `materialized` event bound to the request and projection root.
Later stale-detection events are written only by an authorized POST retry, not
GET. Every event has one causing request. A stale event has exactly one closed
external cause: an evidence lifecycle event, parent Slice-3A projection event,
or candidate correction/replacement relationship. Cause tuples are sorted
before append, unique per projection, and form one contiguous predecessor-hash
chain. The matrix freezes the exact request and event payloads and preimages.

The HTTP body contains only proposal ID, Slice-3A projection ID, and
idempotency key. Versions and hashes are server-derived. The service performs
authorization and gate checks before expensive work, locks/rechecks all inputs,
and commits once.

The complete shared write-lock order is fixed as follows; it is intentionally
compatible with committed Slice 3A and is not lexical gate order:

1. actor user row, then exact organization-membership row;
2. the request-idempotency advisory lock;
3. candidate proposal row;
4. database gate rows in fixed order `validator2_write_enabled`,
   `materializer3a_enabled`, `materializer3b_enabled` (each writer takes the
   prefix it needs);
5. candidate evidence bindings and fragments in deterministic ID order;
6. Slice-3A supersession AD-number advisory locks when 3A is materialized;
7. Slice-3A projection advisory lock, then Slice-3A projection root;
8. correction roots and refs in deterministic ID order;
9. Slice-3B projection advisory lock, then Slice-3B projection root; and
10. projection children in deterministic table/identity order.

Gate administration acquires gate rows in the same fixed order and does not
later acquire a proposal lock. PostgreSQL necessarily obtains a DML relation
lock before a row trigger can take gate locks, so downgrade uses a distinct,
explicit DDL protocol: it acquires every affected table lock in deterministic
parent-before-child order with `NOWAIT`/a bounded lock timeout and rolls back
immediately if any is unavailable; only after the complete table set is held
does it lock gate rows in fixed order and perform occupancy checks. It never
waits on a table while holding a gate lock. Any PostgreSQL deadlock or
serialization victim at the API boundary is translated to a controlled retry
or 409; migration lock contention is a controlled no-DDL refusal. Neither is
an unhandled 500. Forced interleaving tests cover 3A versus 3B materialization,
gate disable, and downgrade.

## Alternatives considered

### Proceed directly to human approval/publication

Rejected. It would sign or select a candidate whose obligation, timing,
document, branch, and AMOC semantics lack independently reconstructed typed
storage. That would make later due-state behavior depend on unreviewed JSON
interpretation.

### Extend Slice-3A expression owners for requirements

Rejected. Slice-3A expressions are intentionally owned by applicability rules,
exclude requirement-state references, and have a closed validated owner union.
Changing them would conflate two projection lifecycles and reopen the closed
3A exactly-one-owner proof.

### Clone requirements once per applicability scope or target

Rejected. It repeats the V3 cardinality defect, loses one stable obligation
identity, and makes recurrence/termination evidence diverge among clones.

### Store requirement/timing JSONB only

Rejected. It cannot provide FK-backed graph integrity, typed numeric timing
queries, exact correction bindings, or direct-SQL protection.

### Reuse released V3 compliance and AMOC tables

Rejected. Their target-cloned cardinality, lifecycle, release meaning, and
consumer set differ. Candidate rows must not enter existing released readers.

### Put 3B correction bindings in a second table

Rejected. The canonical changed reference has exactly one semantic owner.
Keeping one binding table and one unique ref preserves that invariant while
mutually exclusive FK pairs provide physical integrity.

### Automatically ingest referenced service bulletins

Rejected. The V4 candidate contains only source-stated identity/access state.
Lawful acquisition, retention, admission, and human verification are a separate
authorized evidence workflow.

### Treat the mapping digest as proof of parity

Rejected. The manifest/generator reduces repetitive drift, but PostgreSQL,
verified reads, direct-SQL attacks, and branch vectors remain independent
defenses.

## Trust, authorization, and audit boundaries

- Slice-2 candidate bytes and evidence bindings remain the parent authority.
- Slice-3A typed applicability is a verified prerequisite, not an obligation
  writer.
- The 3B materializer may copy only exact canonical values into candidate-only
  rows; it may not normalize regulatory meaning or evaluate expressions.
- An active platform administrator can request/audit materialization but cannot
  thereby approve or publish it.
- Maintenance-shop and aircraft roles cannot access unreviewed 3B projections.
- Database direct writers remain in the threat model. Deferred validation must
  reject invalid graphs even if application code is bypassed.
- General AMOC authority is global AD source meaning. Actual AMOC use remains
  in the separate aircraft compliance-evidence domain.
- Incorporated-document identity is not retained-document authority. Unknown
  retention stays unknown.
- Correction roots/evidence are shared proposal foundations; 3B owns only its
  semantic binding edges.

## Read paths and consumers

Implementation review must inspect:

- V4 candidate create/list/detail readers and verifier;
- Slice-3A materialize/list/detail/reconstruction and correction verification;
- new Slice-3B materialize/list/detail/reconstruction routes;
- current admin extraction/review routes;
- every reader of `ad_compliance_requirements`, `ad_compliance_triggers`,
  `ad_amoc_provisions`, target applicability, compliance events, and due state;
- released AD catalog/search/detail and aircraft worklist/matching routes;
- coverage reconciliation, recurrence replay, and source-remediation scripts;
- Alembic migration/downgrade tooling and database capability administration;
- API schemas and frontend types, even though no frontend change is expected;
  and
- tests/fixtures that create validator-1/2 proposals or direct SQL projection
  rows.

No existing released reader may reference a 3B table.

## Write paths and administrative paths

Authorized writers in this slice are only:

1. the platform-admin Slice-3B materialization POST; and
2. the existing deployment-role feature-gate procedure for the new database
   gate.

The API and any future administrative wrapper must call the same materializer.
No provider, CLI, cron, background worker, startup hook, GET, V3 review path,
or direct decoded-object helper becomes an alternate writer.

Materialization order is:

1. authorize and validate request shape;
2. lock/recheck actor and exact membership;
3. lock proposal and gates;
4. verify candidate bytes/version and live evidence;
5. lock/verify Slice-3A projection and its typed reconstruction;
6. lock correction foundation/refs;
7. derive the neutral expected 3B graph;
8. insert/reuse request, root, children, correction bindings, and root event;
9. force deferred completeness; and
10. commit once.

## Migration, compatibility, correction, and rollback

Migration `20260911_0028_add_ad_v4_obligations.py` is additive except for the
backward-compatible nullable/add-column/check amendment to the correction
binding table. It depends on 0027.

Upgrade:

- takes locks on candidate, Slice-3A, and correction tables before altering the
  shared binding shape;
- proves every existing binding is a valid 3A binding;
- adds the new gate disabled;
- creates only candidate-prefixed 3B tables/functions/triggers/indexes;
- records/fixes the mapping digest; and
- performs no candidate backfill or automatic materialization.

Compatibility:

- existing 3A IDs, bytes, hashes, counts, routes, and reconstruction remain
  exact when read by the 0028-aware 3A verifier;
- validator-1 and validator-2 proposal bytes remain immutable;
- no V3 or released row changes;
- an existing validator-2 proposal remains unmaterialized until explicit POST;
  and
- materializing 3B does not change candidate or 3A creation timestamps/events.

Deployment is expand-first. Migration 0028 lands with
`materializer3b_enabled=false`, and the gate remains disabled until every API
replica uses the 0028-aware Slice-3A reader that accepts and verifies the closed
3A/3B correction-binding union. The exact `9ad410b` binary is tested only
against upgraded 0028 schema with zero 3B bindings. After the first 3B binding
is committed, binary rollback to `9ad410b` is prohibited because that reader
correctly knew only the former zero-3B-binding state. Operational application
rollback thereafter means disabling the 3B application and database gates
while remaining on an 0028-aware binary; it does not mean deploying the old
reader.

Downgrade first takes the complete deterministic table-lock set with
`NOWAIT`/bounded timeout, then the fixed-order gate locks, and refuses if any 3B
root/request/event, 3B correction binding, or enabled 3B gate exists. Lock
contention rolls back with no DDL. On an empty 3B database it drops 3B
triggers/functions/tables in reverse order, removes the added
correction-binding CHECK/columns, restores the two 3A columns to non-null after
proving every remaining row is Slice 3A, and removes the disabled gate.

Application rollback disables 3B routes/writes on an 0028-aware binary.
Candidate and 3A audit remain available. No rollback selects V3 or releases a
candidate. Physical downgrade remains available only after the stated empty-
occupancy proof.

## Test strategy

### Contract and positive matrix

Every row in `normative-mapping-matrix.md` receives a positive Python expected-
graph, ORM materialization, fresh-PostgreSQL commit, typed reconstruction, and
verified-read vector. Coverage includes:

- all document types and every document assertion branch;
- all requirement/action types and ordered-step absent/empty/multiple shapes;
- all branch, timing, recurrence, termination, and expression unions;
- every timing logic, metric, unit, comparator, and anchor value;
- empty/nonempty prerequisites and document refs;
- alternative groups, recurrence membership, and requirement graph shapes;
- empty/nonempty AMOC arrays and all authority assertion branches; and
- absent optional `recurrenceGroupKey` versus present membership.

### Direct-SQL and read corruption matrix

For each table/relationship, tests attack an otherwise valid graph with:

- missing, extra, duplicate, wrong-type, wrong-parent, wrong-pointer, wrong
  ordinal, negative/gapped/reordered ordinal, cross-proposal, and cross-
  projection rows;
- required/optional/nullability and union-presence drift;
- changed values with stale hashes and self-consistently restamped wrong
  hashes;
- evidence missing/extra/reordered/wrong-purpose/wrong-binding swaps;
- document/action/requirement/timing/expression/correction reference swaps;
- expression arity, owner-context, unreachable-node, and cycle attacks;
- requirement dependency/termination cycles and membership disagreement;
- decimal overflow, noncanonical spelling, numeric/text disagreement, and
  metric/unit/anchor drift;
- requirement-sequence maximum text, alternate spelling, overflow, duplicate,
  gap, and pre-conversion failure for normal and forged parents;
- forged validator-2 parent payloads; and
- UPDATE/DELETE with immutability disabled, including forcing constraints
  early and mutating later in the transaction.

Every equivalent read corruption asserts controlled 409 for detail,
reconstruction, and list where applicable; no 500 is accepted.

### Calibration gates

All five source-accounted packets cross real admitted Slice-1 evidence,
Slice-2 candidate storage, Slice-3A materialization, Slice-3B materialization,
PostgreSQL deferred completeness, and verified reconstruction:

- `2024-14-03`: exactly two requirements, software update plus installation
  prohibition, shared applicability, exact action/timing evidence;
- `2011-10-09`: exactly ten ordered requirements, prerequisite chain, one
  ten-member recurrence group, two-term whichever-first initial and recurring
  timing, no cloned requirement per 224 models;
- `2002-13-04`: conditional family branches plus installation prohibition and
  unresolved applicability, with no branch promotion;
- `1998-17-11`: conditional and alternative/rework requirements with retained
  approved-data reference identity but no invented aircraft compliance; and
- `2008-26-10`: four incorporated documents retained as explicit
  unknown/not-obtained, six requirements, whichever-first/later coverage,
  general AMOC authority, and exact append-only correction binding for
  `requirements/req-report`.

Each proposal must reconstruct byte-identically. Existing packet templates,
source PDFs/fragments, candidate hashes, and 3A projection hashes remain
unchanged.

### Authorization, idempotency, concurrency, migration, and isolation

- active exact platform-admin positive; inactive/wrong user/wrong membership/
  wrong role/maintenance-shop negative;
- all application/database gate combinations with zero-row failure proofs;
- same-key replay and divergent-key 409; concurrent identical convergence;
- concurrent gate disable/materialization and downgrade/materialization;
- forced 3A/3B, gate, and downgrade interleavings under the complete lock
  order, with controlled deadlock/serialization handling and no 500;
- detail/list/reconstruction snapshot races against evidence-lifecycle append,
  candidate correction/replacement, and parent-3A stale transition;
- transaction failure injection before/after root, children, correction
  binding, event, and forced constraints;
- clean 0027->0028 upgrade, empty downgrade/re-upgrade, occupied refusal, and
  unchanged 3A data/hash snapshots, including byte-exact existing correction
  binding IDs/hashes through failed downgrade and re-upgrade;
- exact-`9ad410b` reader compatibility against upgraded-empty 0028 state and
  enforcement/documentation of the no-old-binary boundary after the first 3B
  binding;
- database catalog assertions for CHECK/FK/unique/index/trigger coverage;
- mapping generator `--check` plus Python/SQL/database digest parity;
- repository scan proving zero released readers of 3B tables; and
- snapshot V3/released endpoints, matching, coverage, recurrence, and due state
  before/after all five materializations.

Required reporting names executed, skipped, and unavailable classes separately
and uses `X passed out of X`.

## Expected file scope

Framing/design stage may add only:

```text
.ai/review-runs/T081-V4-SCHEMA-SLICE-3B/**
```

Expected implementation scope after design PASS:

```text
backend/app/contracts/ad_v4_obligation_mapping.schema.json
backend/app/contracts/ad_v4_obligation_mapping_v1.json
backend/app/services/ad_v4_obligation_mapping_v1.py
backend/app/services/ad_v4_obligations.py
backend/app/services/ad_v4_applicability.py
backend/app/services/ad_v4_candidates.py
backend/app/db/migrations/sql/20260911_0028_obligation_expectations.sql
backend/app/db/migrations/versions/20260911_0028_add_ad_v4_obligations.py
scripts/generate_ad_v4_obligation_mapping.py
backend/app/models/core.py
backend/app/db/session.py
backend/app/core/config.py
backend/app/schemas/ads.py
backend/app/api/routes/ads.py
backend/tests/test_ad_v4_obligations.py
backend/tests/test_ad_v4_obligations_calibration.py
backend/tests/test_ad_v4_obligations_postgres.py
backend/tests/test_ad_v4_candidates.py
backend/tests/test_ad_v4_applicability.py
backend/tests/test_ad_v4_applicability_postgres.py
backend/tests/test_ad_v4_postgres.py
```

Implementation evidence remains inside this review run. A scope change requires
decision amendment and independent review before editing the new product area.

Explicitly forbidden in 3B:

- V4 schema or calibration proposal changes;
- retained source PDF/fragment changes;
- V3 model/service/data mutation;
- signed decision/publication/current-selection tables or events;
- released reader, frontend, aircraft configuration, matching, compliance,
  AMOC-use, or due-state changes;
- service-bulletin ingestion/admission; and
- provider, CLI, cron, worker, or GET writers.

## Known uncertainty and design-review questions

1. The shared correction binding table's current app-only FK shape is the main
   cross-slice migration risk. The reviewer must attempt partial backfills,
   invalid null combinations, cross-proposal binding, downgrade occupancy, and
   3A read regressions.
2. Slice 3B freezes the existing raw-parser limit of 16,384 characters for a
   timing interval and applies it before conversion in Python and PostgreSQL.
   A forged longer parent fails with `timing_interval_resource_limit`; exact
   text stays authoritative and silent rounding is never allowed. The reviewer
   must attempt both numeric magnitude and fractional-scale boundary attacks.
3. The current validator checks requirement sequence continuity and overall
   reference cycles but does not assign operational meaning to metric/unit/
   anchor combinations. 3B preserves validator-2 candidates exactly; it must
   not invent compatibility rules and must not advertise evaluability.
4. `orderedSteps` may be absent or present-empty. Those shapes are semantically
   distinct canonical inputs and must remain distinct in owner presence flags
   even though both have zero step rows.
5. Alternative-group exclusivity is repeated on member branches rather than a
   canonical group object. 3B intentionally preserves singleton and mixed-
   exclusivity validator-2 inputs without evaluation; the reviewer should
   confirm no generated or SQL rule accidentally narrows them.
6. The data-only mapping generator is intentionally bounded. The reviewer must
   reject any digest claim that does not mechanically cover its stated
   selectors/columns/relations and must require independent tests for every
   hand-written global algorithm.
7. The 3B projection depends on an exact 3A materializer version. A future 3A
   materializer version requires a new reviewed 3B compatibility declaration;
   3B must not silently accept it.
8. No real retained incorporated service bulletin or aircraft-specific AMOC
   use is available in the five-packet corpus. This slice proves exact
   unknown/not-obtained and general-authority behavior only and must not claim a
   positive retained-document or aircraft-use workflow.

None of these questions authorizes timing evaluation, obligation activation,
publication, source inference, retained-document invention, or V3 fallback.
