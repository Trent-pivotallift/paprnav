# Decision packet: T081-V4-SCHEMA-SLICE-2

Status: design frame; independent design review required

Builder: `/root/v4_schema_builder`

Governing contract: `.ai/AD_EXTRACTION_DOMAIN_CONTRACT.md` version 1.1

Predecessor: closed `T081-V4-SCHEMA` slice 1 retained-evidence boundary

## Objective

Implement, after design approval, the second bounded V4 vertical slice:

1. a strict `ad_extraction_v4` JSON Schema validator;
2. semantic and database-backed evidence-reference validation;
3. deterministic schema-aware canonicalization and SHA-256 identity; and
4. immutable, candidate-only proposal storage with append-only submission
   provenance.

This slice turns a machine- or administrator-authored V4 document into a
durable, reproducible proposal. It does **not** turn that proposal into a
reviewed decision, released directive, applicability result, compliance fact,
or due-state input.

The following are explicitly excluded:

- normalized relational materialization of product scopes, predicates,
  expressions, requirements, timing, STCs, service bulletins, or AMOCs;
- reviewer GUI/forms, raw-JSON editing UI, signoff, approval, rejection,
  publication, selection, or catalog exposure;
- aircraft matching, coverage, compliance, terminating-action, or due-state
  calculation and any read cutover;
- V3 mutation, freeze, translation, correction, fallback, or mixed V3/V4 read;
- supporting-document upload/admission, cross-page fragments, OCR, and
  aircraft-specific AMOC evidence; and
- provider-job integration or a CLI writer.

An additive migration is required. Existing `ad_extractions.output` and
`ad_extraction_reviews.proposed_output` are V3-oriented, mutable in current
workflows, and cannot enforce immutable V4 identity or fragment bindings.

## User-visible outcome

There is no maintenance-shop or released-catalog change in this slice. A
platform administrator may submit a V4 candidate through a narrow authenticated
API and retrieve the stored candidate for audit. The response identifies:

- proposal ID, directive ID, schema/canonicalization/validator versions;
- immutable canonical hash and evidence-binding hash;
- constant gate `candidate_only`;
- submission provenance and whether an idempotent request reused content; and
- validation errors as stable codes plus JSON pointers when submission fails.

The API never calls the V3 review, publication, matching, materialization, or
due-state services. No candidate appears in customer-facing AD search.

## Safety and correctness invariants

These statements are falsifiable implementation gates.

1. Only documents with root `schemaVersion == "ad_extraction_v4"` and an exact
   closed schema are accepted. Every object rejects unknown properties.
2. JSON `null`, non-finite numbers, floating-point numbers, duplicate object
   keys, invalid Unicode, and non-NFC strings are rejected before persistence.
   Regulatory uncertainty uses an explicit known/not-applicable/unknown union.
3. Every unknown has a controlled reason, at least one evidence key, and a
   temporal scope. Every safety-relevant `not_applicable` has a nonempty reason,
   evidence, and scope; it is never inferred from omission.
4. Manufacturer, model/series, product role, serial scope, part scope, STC,
   installed-equipment condition, and source value remain distinct. Combined
   manufacturer/model authority and flattened `affectedProducts` are rejected.
5. Stable keys are unique in their namespace. Every evidence, document, scope,
   condition, rule, requirement, prerequisite, alternative, termination, AMOC,
   and supersession reference resolves exactly once inside the proposal or by
   its explicitly typed external identity.
6. Expression nodes use the closed typed three-valued AST. Arity, depth, node
   count, same-decision references, and acyclicity are enforced. Constants and
   untyped predicates are rejected.
7. Requirement dependency, alternative, termination, rule-exclusion, and
   supersession graphs satisfy their closed type and cycle rules. A requirement
   has one activation expression and source-supported action evidence.
8. Threshold values are canonical decimal strings with typed metric, unit,
   comparator, and anchor. Unsupported or missing timing components cannot be
   converted into a due value; this slice calculates no due values.
9. Derived summaries, confidence, assessment labels, calculated results,
   `complianceActions`, `complianceIntervals`, and materialized target rows are
   forbidden canonical input.
10. Every canonical evidence key resolves to exactly one slice-1 immutable
    fragment ID/hash. The fragment belongs to the proposal's directive through
    its publication/source chain and has a valid admitted lifecycle root.
11. Proposal creation rechecks, inside the write transaction, fragment hash,
    directive/publication/document/source-hash attribution, and the complete
    lifecycle chain. Slice 2 accepts only an exact singleton `admitted` root;
    any later event makes the fragment ineligible. An orphaned,
    wrong-directive, forged, quarantined, or superseded fragment fails closed.
12. A later fragment lifecycle change never rewrites or deletes a proposal.
    It makes that proposal ineligible for any future decision until a new
    proposal binds eligible evidence. Every future approval slice must repeat
    lifecycle/hash validation rather than trusting creation-time eligibility.
13. Canonicalization is deterministic and versioned. The same semantic input
    under the same schema/canonicalization version produces byte-identical
    canonical UTF-8 and the same hash across processes and retries.
14. Canonicalization does not paraphrase, case-fold, trim, normalize model
    identifiers, or rewrite source strings. Input strings must already be NFC;
    otherwise validation rejects them.
15. Arrays declared as sets are sorted by closed schema-specific keys before
    hashing; ordered regulatory arrays preserve sequence. Changing an ordered
    action, timing, branch, or expression sequence changes the hash.
16. The stored canonical byte payload, parsed JSON mirror, canonical hash,
    evidence-binding rows, and evidence-binding hash agree exactly at commit.
    Direct SQL cannot create a row whose bytes/hash or binding set disagree.
17. Every stored object is permanently `candidate_only`. No column, event, API,
    or service in this slice can represent `released_actionable`, approval, or
    current selection.
18. Proposal content, evidence snapshots, submission provenance, and
    predecessor relationships are append-only. UPDATE and DELETE are rejected
    at PostgreSQL level.
19. Retrying one idempotency key with the same directive and canonical hash
    returns the same submission/proposal. Reusing it with different content or
    directive returns 409 and creates nothing.
20. Concurrent identical submissions converge on one content proposal and one
    submission per idempotency key without 500 errors. Different submissions
    may reference the same deduplicated content without losing provenance.
21. Only an active `platform_admin` may use the HTTP writer or read unreviewed
    proposal detail/list. Maintenance shops, aircraft owners, and ordinary
    organization administrators receive 403 and cannot mutate global evidence.
22. The API calls one proposal service whose input is the opaque result of the
    reviewed raw-byte parser. No provider job, direct-table CLI, decoded-object
    alternative, or bypass writer exists in this slice.
23. V1/V2/V3 JSON, reviews, materialized rows, and read behavior remain
    byte-for-byte/behaviorally unchanged. V4 candidate creation does not update
    any V3 row.
24. An occupied schema downgrade refuses before DDL while holding locks that
    prevent insert/drop races. Empty downgrade and re-upgrade succeed.

## Current behavior

Slice 1 added immutable source page renditions, bounded text versions,
single-page evidence fragments, append-only fragment lifecycle events, and
relevant-page navigation. PostgreSQL binds each fragment transitively to the
directive, publication, source document/hash, rendition, text version, parser,
page, offsets, exact text, and canonical fragment hash. Explicit page and
fragment mutations are platform-admin-only.

Current extraction storage is not a V4 candidate boundary:

- `ad_extractions.output` stores provider JSON alongside a mutable status and
  V3 idempotency identity;
- `ad_extraction_reviews.proposed_output` and `decision_output` participate in
  V3 staging/correction and raw-JSON review;
- `structured_output_hash` uses generic sorted JSON rather than a versioned,
  schema-aware canonical contract; and
- current V3 validation derives display summaries and permits structures that
  V4 explicitly forbids.

The five source-complete calibration packets are semantic Markdown contracts,
not executable V4 JSON fixtures yet. Slice 2 will add implementation fixtures
derived from them only after this design passes; it will not edit the accepted
packet documents.

## Proposed design

### 1. Validation pipeline

The HTTP route accepts a `Request`, not a framework/Pydantic JSON-body model.
It obtains the raw body after rejecting a non-JSON content type, content
encoding, absent/invalid/oversize content length, and a streamed body over the
versioned byte limit. A shared `parse_v4_request_bytes(raw)` performs strict
UTF-8 decoding, rejects invalid scalar values (including escaped lone
surrogates), duplicate keys through an object-pairs hook, every numeric token
(including non-finite extensions), and every non-NFC key or value. It returns
an opaque `ParsedV4Request`; the proposal service accepts only that token plus
server-derived directive and authorization context. No ordinary FastAPI or
Pydantic JSON decoder runs first. It runs these phases in order and returns all
errors in
stable `(code, jsonPointer, message)` order:

1. **Parser boundary** — decode UTF-8 while rejecting duplicate object keys,
   invalid Unicode, non-finite values, and resource-limit violations.
2. **Draft 2020-12 JSON Schema** — validate a versioned checked-in schema with
   closed objects, exact discriminators, formats, enums, lengths, and bounds.
3. **Pure semantic validation** — enforce key uniqueness/reference resolution,
   used evidence keys, graph typing/arity/cycles, branch/alternative rules,
   timing types, forbidden derived input, resource limits, and minimum viable
   candidate structure.
4. **Schema-aware normalization for canonicalization** — sort only declared set
   collections; preserve declared ordered collections; perform no value
   inference or string rewriting.
5. **Canonical encoding/hash** — emit RFC 8785-compatible UTF-8 bytes using a
   pinned implementation and compute a domain-separated SHA-256.
6. **Transactional evidence validation/storage** — lock attributable fragment
   rows as needed, revalidate the slice-1 chain/lifecycle, derive binding rows,
   and insert/reuse proposal and submission records atomically.

Minimum viable candidate structure is one attributable directive identity, at
least one product scope, one applicability rule, one independently actionable
requirement, and evidence for every safety-relevant node. Explicit unknowns are
permitted and force candidate-only behavior; missing the minimum remains a
validation failure rather than a stored empty proposal.

Base JSON Schema cannot establish database identity, graph acyclicity, or
cross-array references. Those checks are normative semantic validation, not
optional warnings.

### 2. Canonical V4 surface in this slice

The root contract follows the closed V4 proposal and requires:

- `schemaVersion`, `decisionKey`, `directiveIdentity`, `officialDocuments`, and
  `evidenceBindings`;
- `incorporatedDocuments`, `productScopes`, `conditionDefinitions`,
  `applicabilityRules`, `requirements`, `amocAuthorityProvisions`, and
  `supersessionRelations`; and
- `recurrenceGroups`, `applicabilitySearchHints`, and
`authoritativeCorrections`.

`officialDocuments` is the closed namespace for retained regulatory-document
identities. Each entry is
`{officialDocumentKey,documentRole,sourceDocumentId,sourceContentHash,
publicationDocumentNumber,evidenceKeys}`. `documentRole` is exactly
`ad_rule|official_correction`; the source document must participate in an
`ad_publications` row for the proposal directive, its retained content hash
must match, and every evidence key must resolve to an admitted fragment on
that same document. Keys are unique and the set sorts by
`officialDocumentKey`. This is distinct from `incorporatedDocuments`, which
describes supporting service information and remains unknown-only in slice 2.

`recurrenceGroups` hold a stable key, two or more requirement keys, a closed
completion policy (`all_active_requirements`), shared initial/recurring timing,
and evidence. A requirement may name at most one group and then may not repeat
group timing. `applicabilitySearchHints` hold a stable key, product role,
separate manufacturer/model/identifier fields, `controlling: false`,
`exhaustive: false`, and evidence. No AST node or controlling rule may refer to
a hint. `authoritativeCorrections` hold a stable key, typed original and
correcting AD-document identities, correction type, typed changed-semantic
references, and evidence from the correcting document. Their graph is
same-directive and acyclic. `originalDocumentRefKey` and
`correctingDocumentRefKey` resolve exactly once in `officialDocuments`; the
former permits `ad_rule|official_correction`, the latter requires
`official_correction`, and both must have evidence-backed retained identities.

Minimal canonical shapes are `recurrenceGroups[{recurrenceGroupKey,
requirementKeys,completionPolicy,initialTiming,recurringTiming,evidenceKeys}]`,
`applicabilitySearchHints[{hintKey,productRole,manufacturer,models,
controlling:false,exhaustive:false,evidenceKeys}]`, and
`authoritativeCorrections[{correctionKey,correctionType:
official_correction,originalDocumentRefKey,correctingDocumentRefKey,
changedSemanticRefs:[{namespace,key}],evidenceKeys}]`. The validator rejects
missing group members, duplicate group membership, inline/group timing
conflicts, correction cycles or cross-directive documents, any hint reference
from the AST, and any controlling/exhaustive hint.

The checked-in schema fully defines the known/not-applicable/unknown union,
product and identifier scopes, typed predicates/expressions, requirements,
timing, branches, referenced-document states, general AMOC authority, and
supersession references from the predecessor proposal. It accepts no aircraft
configuration facts, aircraft maintenance evidence, aircraft-specific AMOC
use, Paprnav assessment, review decision, or release state.

Slice 2 permits incorporated-document retention only as explicit `unknown`
with reason `not_obtained|unavailable|not_yet_verified`, temporal scope, and AD
evidence for the designation. `known` retention is reserved for a later schema
version and is rejected by this schema. An AD-publication fragment cannot be
relabeled as a service bulletin; supporting-document admission remains a later
reviewed slice.

Resource limits are part of the versioned validator contract: maximum encoded
request size, object depth, string length, array size, expression depth, total
AST nodes, model count, evidence-binding count, and graph edge count. Tests use
limits above the 224-model 2011 calibration packet and reject limit+1. Exact
initial values require performance measurement during implementation and are
recorded with `validatorVersion`; changing them requires a new reviewed
validator version.

### 3. Canonicalization and hashes

Canonicalization version `paprnav-ad-v4-c14n-1` is a restricted RFC 8785
profile implemented and pinned as `paprnav-jcs-subset-v1`. Allowed canonical
values are objects, arrays, NFC strings, and booleans; numbers and JSON null are
forbidden. Object names use RFC 8785 UTF-16-code-unit ordering; strings use its
exact escaping and UTF-8 serialization. Official RFC 8785 vectors plus
surrogate, control-character, property-order, and fresh-process vectors are
normative. The profile applies these rules:

- object properties follow RFC 8785 ordering and encoding;
- every input string must already be Unicode NFC;
- JSON numbers are forbidden in canonical V4 safety values; decimal/time/cycle
  quantities are canonical strings, and ordering uses array position;
- every schema array carries `x-paprnav-array-kind: set|sequence`; a schema
  meta-test fails any unannotated array. Set collections sort by their closed
  key: official documents by `officialDocumentKey`, incorporated documents by
  `documentRefKey`,
  scopes by `scopeKey`, conditions by `conditionKey`, rules by `ruleKey`,
  requirements by `requirementKey`, recurrence groups by `recurrenceGroupKey`,
  search hints by `hintKey`, AMOC provisions by `provisionKey`, authoritative
  corrections by `correctionKey`, and supersession relations by
  `(relationType, predecessorAdNumber, successorAdNumber)`;
- `evidenceKeys`, prerequisite keys, document-reference keys, and other
  explicitly set-valued scalar arrays sort lexicographically after duplicate
  rejection;
- listed model/serial/part values sort by exact source value after duplicate
  rejection; source table order remains available through evidence, not as
  independent regulatory meaning;
- expression operands, ordered action steps, timing terms, and branch sequences
  preserve order; and
- canonicalization is idempotent: `C(C(x)) == C(x)` byte-for-byte.

The only other set arrays are evidence keys, prerequisite/alternative/
termination/document/exclusion/member references (exact string order), source
designations and identifier listed values (exact string order), and identifier
ranges ordered by `(lower, upper, lowerInclusive, upperInclusive, polarity)`.
All other arrays are sequences. Adding an array requires a new reviewed
canonicalization version. Decimal quantities match
`(?:0|[1-9][0-9]*)(?:\.[0-9]*[1-9])?`; metric thresholds additionally require
value greater than zero. Signs, exponent notation, leading zeros, `.5`, `1.0`,
and trailing fractional zeros are rejected. Dates are real Gregorian
`YYYY-MM-DD`; hashes are lowercase 64-hex; every key/identifier uses its
schema-specific anchored grammar.

Every domain separator is the displayed ASCII/UTF-8 byte string followed by
exactly one NUL byte `0x00` (never the two printable bytes `\\` and `0`). The
normative domain bytes, including the final `00`, are:

| Hash | ASCII before NUL | Complete hex bytes |
| --- | --- | --- |
| proposal | `paprnav:ad_extraction_v4:proposal:paprnav-ad-v4-c14n-1` | `706170726e61763a61645f65787472616374696f6e5f76343a70726f706f73616c3a706170726e61762d61642d76342d6331346e2d3100` |
| evidence bindings | `paprnav:ad_extraction_v4:evidence-bindings:1` | `706170726e61763a61645f65787472616374696f6e5f76343a65766964656e63652d62696e64696e67733a3100` |
| candidate event | `paprnav:ad_extraction_v4:candidate-event:1` | `706170726e61763a61645f65787472616374696f6e5f76343a63616e6469646174652d6576656e743a3100` |
| submission | `paprnav:ad_extraction_v4:submission:1` | `706170726e61763a61645f65787472616374696f6e5f76343a7375626d697373696f6e3a3100` |
| submission relationship | `paprnav:ad_extraction_v4:submission-relationship:1` | `706170726e61763a61645f65787472616374696f6e5f76343a7375626d697373696f6e2d72656c6174696f6e736869703a3100` |

For each row, `hash = lowercase_hex(SHA-256(domain_bytes ||
restricted_jcs(envelope)))`. The proposal envelope is the root object and has
fixed `schemaVersion: "ad_extraction_v4"`. The evidence envelope is exactly
`{"version":"ad-v4-evidence-bindings-v1","bindings":[...]}` with bindings
sorted by `evidenceKey`; each binding has exactly `evidenceKey`, `fragmentId`,
`fragmentHash`, `admittedEventId`, and `admittedEventHash`. The creation-event
envelope is exactly `{version:"ad-v4-candidate-created-v1",eventType:
"candidate_created",proposalId,directiveId,proposalCanonicalHash,
evidenceBindingHash,createdBySubmissionId}`. The submission envelope is exactly
`{version:"ad-v4-submission-v1",directiveId,proposalCanonicalHash,
relationships}`. Each relationship hash uses exactly
`{version:"ad-v4-submission-relationship-v1",relationshipKey,relationType,
predecessorProposalId,reason,evidenceKeys}`. No version member is caller
selectable.

Positive vectors pin all five complete hex domain prefixes, fixed version
literals, canonical envelope bytes, and expected digests. Negative vectors
replace NUL with printable `\\0`, omit/double NUL, change one version literal,
or use another artifact's domain and must produce a different digest or fail.
PostgreSQL digests the stored domain prefix plus stored canonical bytes; it
does not recanonicalize. Python/PostgreSQL parity vectors are normative.

The parsed JSON mirror is convenience data. Canonical bytes plus version and
hash are audit authority. A server round trip parses stored bytes, reruns
schema/semantic canonicalization, and requires identical bytes/hash before the
record is returned as verified.

### 4. Additive candidate storage

The implementation should add an Alembic revision after slice 1 with five
append-only structures:

`ad_v4_candidate_proposals`

- ID, directive ID, schema version, canonicalization version, validator
  version, canonical UTF-8 bytes, parsed JSONB mirror, canonical hash,
  evidence-binding hash, binding count, constant gate `candidate_only`;
- created time only; no mutable status, reviewer, decision, release, or current
  pointer;
- unique `(directive_id, canonicalization_version, canonical_hash)`; no
  predecessor or correction metadata is stored on deduplicated content.

`ad_v4_candidate_evidence_bindings`

- proposal ID, evidence key, fragment ID/hash, admitted lifecycle event ID/hash;
- unique proposal/evidence key and proposal/fragment-purpose identity;
- composite FKs bind the fragment to the same directive and bind the lifecycle
  root to that fragment/hash; no exact source text is copied.

`ad_v4_candidate_submissions`

- immutable submission ID, proposal ID, `actor_kind = platform_admin`, user ID,
  exact authorizing membership and organization IDs, snapshotted role/status,
  authorization-policy name/version/claims hash, idempotency key, canonical
  request hash, optional raw-transport hash for audit only, and created time;
- unique writer-scope/idempotency key; the same key with a different directive
  or hash is a conflict;
- multiple distinct origins may point to one deduplicated content proposal.

`ad_v4_candidate_submission_relationships`

- submission ID, stable relationship key, relation type
  `corrects_candidate|replaces_candidate`, same-directive predecessor proposal
  ID, nonempty reason, evidence keys, canonical relationship hash;
- unique submission/relationship key, no self edge, same-directive FK, and an
  acyclic relationship graph; evidence keys resolve in the new proposal; and
- relationships are part of request/submission identity, never deduplicated
  proposal-content identity.

`ad_v4_candidate_proposal_events`

- one server-created `candidate_created` root per proposal with sequence 0,
  proposal/hash/binding-hash payload, creating submission ID, null predecessor
  hash, and event hash;
- no accepted/rejected/released/selected event types in this slice.

Deferred PostgreSQL checks/triggers require at commit:

- canonical byte/hash agreement using a deterministic database-verifiable
  digest over the already canonical bytes;
- JSONB mirror equivalence to decoded canonical bytes;
- exact equality between canonical `evidenceBindings` and binding rows,
  including count and binding hash;
- one valid `candidate_created` root; and
- immutable UPDATE/DELETE rejection for all five structures.

If the database cannot safely reproduce the full schema-aware canonicalization,
it does not try. It verifies byte digest, mirror/binding agreement, relational
identity, and event root; the application proves schema-aware canonical bytes
before insertion and again on read. Direct SQL cannot forge a different hash or
binding set for stored bytes.

### 5. Append-only, idempotency, and concurrency behavior

The request envelope is exactly `{proposal, submissionContext:{relationships}}`.
The raw transport hash is audit-only; semantic retry identity uses the
canonical proposal and canonical relationships. The client must provide
`Paprnav-Acting-Membership-Id`; the server never chooses among memberships.

After raw parsing/canonicalization, the transaction uses this total lock order:

1. lock the active user row and the named active membership row; verify the
   membership belongs to the user and grants `platform_admin` under the named
   policy version, and snapshot membership, organization, role, status, and
   policy claims;
2. acquire an advisory lock on `(actor_user_id,
   authorizing_membership_id, endpoint_action, auth_policy_version,
   idempotency_key)` before looking up a submission;
3. return an existing submission only when the canonical request hash and
   directive match; otherwise return 409;
4. lock all referenced fragments in lexicographic fragment-ID order. A
   slice-2 trigger makes every lifecycle INSERT lock the same parent fragment
   row first. Under those locks, require the full lifecycle to contain exactly
   one valid sequence-0 `admitted` root with null predecessor and valid hash;
5. acquire the content advisory lock on `(directive_id,
   canonicalization_version, canonical_hash)` and then insert/reuse content;
6. insert exact binding, event, relationship, and submission rows; and
7. commit only after deferred constraints pass.

Thus any second lifecycle event of any type makes a fragment ineligible; slice
2 has no accepted-successor concept and emits no fragment lifecycle event.
Unexpected uniqueness errors roll back the whole transaction, requery under
the idempotency lock, and map to exact retry or 409, never 500.

It then:

1. inserts or reuses the content proposal by unique canonical identity;
2. inserts exact binding rows and one creation root only when content is new;
3. appends one submission plus its zero-or-more relationship rows; and
4. commits atomically.

Two concurrent identical requests with one key return one submission/proposal.
Two distinct keys for the same content append two provenance rows referencing
one proposal. Two different payloads with one key yield one success and one
409. No uniqueness race becomes 500. A failed binding/event/submission insert
rolls back every database row.

Correction never updates a proposal. Content correction submits changed
canonical content and records evidence-supported predecessor relationships on
the submission. Identical content may be submitted against different
predecessors without losing either edge. This slice creates no current pointer
and invalidates no downstream state because none consumes candidates
authoritatively yet.

### 6. Candidate-only gates

`candidate_only` is a database CHECK constant, not caller input. The API does
not accept an automation or release state. Explicit unknowns, absent/unverified
incorporated service bulletins, and unresolved source conflicts may be stored
when minimum source attribution and semantic structure are complete, but they
remain candidate-only.

In particular:

- 2002-13-04 may preserve the conflicting serial range as unknown and store a
  candidate; it cannot choose either range or become actionable;
- 2008-26-10 may preserve four bulletin identities with
  `unknown/not_obtained`; their unseen method detail cannot be asserted;
- a general AMOC provision cannot contain aircraft-specific use; and
- no customer assessment label is stored in this structured-AD candidate.

There is deliberately no transition out of candidate-only in this slice. A
later publication slice must independently revalidate schema/semantics,
canonical bytes/hash, evidence lifecycle, authorization/signoff, and release
minimums.

### 7. API and writer boundary

One HTTP writer is in scope:

`POST /api/v1/ads/directives/{directive_id}/v4/candidate-proposals`

- requires `Idempotency-Key`, `Paprnav-Acting-Membership-Id`, and the raw JSON
  request envelope;
- locks and snapshots that exact active `platform_admin` authorization inside
  the transaction;
- does not accept actor, provider, hash, gate, evidence snapshot, or lifecycle
  fields from the client; and
- returns 201 for a new content/submission, 200 for an exact retry/content
  reuse as defined by the response flags, 409 for idempotency mismatch, 422 for
  structural/semantic/evidence errors, 403 for unauthorized users.

Platform-admin-only GET detail/list endpoints may be added to retrieve verified
candidate metadata and canonical JSON for audit. They do not materialize,
approve, or release. Source text remains joined read-only from evidence APIs and
is not embedded in proposal responses as canonical input.

There is no CLI or provider writer in this slice. The database actor-kind CHECK
permits only `platform_admin`; it contains no nullable provider-origin columns.
A future provider integration requires a new reviewed migration and
authorization contract.

## Alternatives considered

### Reuse `ADExtraction.output`

Rejected. Current V3 services can update extraction/review JSON, derive display
summaries, and materialize V3. Reuse would blur schemas and make candidate-only
isolation unprovable.

### Validate with Pydantic only

Rejected. A portable, versioned JSON Schema artifact is needed for provider
contracts and fixtures, while graph/reference/evidence checks require a second
semantic layer. Pydantic may type API wrappers but is not the canonical schema.

### Hash generic `json.dumps(sort_keys=True)` output

Rejected. It does not define Unicode, number, or schema-set ordering semantics
and can produce multiple hashes for semantically identical set order.

### Store JSONB only

Rejected. JSONB does not preserve the canonical byte representation used for
signature/replay. Store canonical bytes as authority and JSONB only as a
verified query/display mirror.

### Store every submission as duplicate proposal content

Rejected. It loses idempotency and repeats large 182/224-model payloads.
Deduplicated content plus append-only origins preserves both audit and storage.

### Provide a staging CLI instead of an API

Rejected for this slice. A CLI risks becoming an authorization bypass. The
single service/API path gives direct authorization, idempotency, and concurrency
tests. Provider/operations adapters remain future work.

### Implement normalized relational rows now

Rejected as scope expansion. Binding rows are integrity snapshots, not semantic
materialization. Product, predicate, AST, requirement, timing, and document
tables remain slice 3.

## Trust, authorization, and audit boundaries

- The complete PDF and slice-1 fragments remain official evidence. Canonical
  V4 JSON is an unsigned machine/admin proposal, never source evidence.
- The schema validator proves structure; semantic validation proves internal
  consistency and resolvable evidence. Neither proves regulatory correctness.
- The server derives hashes, evidence snapshots, gate, actor, membership, and
  event data. The client cannot self-assert them.
- HTTP creation/read requires active platform-admin membership. A role change
  between page load and submit fails at the transaction boundary.
- The proposal author may later be disqualified from sole approval under the
  reviewed signoff policy, but no approval exists in this slice.
- Database accounts used by the application lack an endorsed direct-mutation
  workflow. Immutability triggers protect against accidental/direct SQL update
  and deletion; repository scripts add no bypass.
- Validation error details may expose stable keys but not private source text
  to unauthorized callers.

## Read paths and consumers

In-scope reads:

- the proposal service's post-write verification;
- platform-admin candidate detail/list API, if implemented;
- migration/test inspection of canonical bytes, binding snapshots,
  submissions, and creation roots; and
- future slices through an explicit repository/service interface only.

Out-of-scope readers must remain unchanged: V3 extraction review, released AD
catalog, aircraft AD pages, matching, coverage, compliance materialization,
recurrence/due-state, observability counts, exports, and frontend API/UI.

Repository review must confirm no existing query selects the new tables and no
existing `schema_version` branch accidentally treats V4 as V3.

## Write paths and administrative paths

The only supported write path is the transaction service called by the
platform-admin POST. It creates proposal content, evidence bindings, creation
root, and submission provenance together. GET is side-effect-free.

No seed script, calibration loader, V3 stage/correction script, direct SQL
helper, provider job, or CLI writer is added. Test factories may use the service
or direct SQL only for negative database enforcement.

## Migration, compatibility, correction, and rollback

An additive migration after `20260830_0025` is required. It adds only candidate
proposal/binding/submission/root structures and supporting constraints/indexes.
It does not add normalized semantic tables, current-decision pointers, review
or publication events, compatibility projections, or modify existing columns.

Upgrade must work with existing V1/V2/V3 and slice-1 evidence rows without
backfill. New tables begin empty. Candidate creation references existing
fragments; it never updates them.

Downgrade behavior:

1. acquire `ACCESS EXCLUSIVE` locks on all slice-2 tables before emptiness
   checks;
2. refuse if any proposal, binding, submission, or event exists;
3. on empty tables, remove slice-2 constraints/tables and return to 0025; and
4. prove an overlapping insert either commits first and makes downgrade refuse,
   or downgrade locks first and the insert cannot target dropped schema.

Application rollback disables the V4 candidate route/service but preserves all
rows. Physical removal requires an empty schema or verified backup/restore; it
never deletes candidate audit data. Because no authoritative reader consumes
the rows, rollback cannot resurrect V3 or alter released behavior.

Correction is append-only candidate creation plus immutable same-directive
submission-relationship rows. It neither changes source fragments nor claims
publication. V3 translation is absent.

## Test strategy

Verification must report `x passed out of x` per suite and list skipped or
unexecuted categories separately.

### Structural, semantic, and canonical tests

Positive:

- valid minimal candidate and each slice-2-supported closed union/predicate/
  timing variant; incorporated-document `known` is unsupported;
- all Kleene T/F/U truth-table structures are representable without evaluation;
- every reference namespace resolves and all permitted graphs pass;
- object-key permutations and declared set-array permutations canonicalize to
  identical bytes/hash;
- ordered expression/action/timing permutations produce different hashes;
- canonicalization is idempotent and stable across fresh processes;
- stored bytes parse, validate, recanonicalize, and match bytes/hash; and
- candidate with explicit supported unknown stores as candidate-only.

Negative:

- JSON null, every numeric token/non-finite extension, duplicate key before
  framework decode, invalid UTF-8, escaped lone surrogate, invalid/non-NFC
  Unicode, unknown property, wrong schema version, invalid key/hash/AD formats;
- unknown/not-applicable lacking reason/evidence/temporal scope;
- duplicate/missing/unused evidence keys and every orphan/cross-namespace ref;
- wrong AST arity/type, constant/untyped predicate, depth/node/edge limit+1,
  self/cyclic rule, requirement, termination, and supersession graphs;
- unsupported timing metric/unit/comparator/anchor/decimal and aliases `01`,
  `+1`, `-0`, `.5`, `1.0`, exponent notation, or trailing fractional zero;
- manufacturer/model concatenation and derived/display/customer fields;
- unannotated schema array, missing/cyclic recurrence/correction references,
  hint referenced by an AST, controlling/exhaustive hint, bulletin retention
  `known`, or an AD publication masquerading as a bulletin;
- missing/duplicate/cross-directive official-document key, a retained hash or
  evidence fragment inconsistent with its official document, correction refs
  aimed at `incorporatedDocuments`, or a correcting ref whose official role is
  not `official_correction`;
- wrong-directive/hash/page/document fragment, non-admitted/quarantined
  lifecycle, forged admitted event, and a lifecycle change between validation
  and insertion; and
- direct SQL canonical-byte/hash, JSON mirror, binding set/hash/count, event
  root, UPDATE, and DELETE counterexamples.

### Exact five-packet calibration matrix

Implementation must create a portable, source-accounted fixture bundle under
`backend/tests/fixtures/ad_v4_calibration/`: `sources.manifest.json` pins each
lawfully available official PDF by logical key, official attribution, SHA-256,
byte length, and page count; `fragments.manifest.json` pins each evidence key
to source key, page, character bounds, renderer/parser versions, page-text
hash, exact-text hash, and fragment-hash inputs; five proposal templates use
logical evidence keys rather than database IDs. A bootstrap test obtains bytes
only from a repository fixture or approved
`PAPRNAV_AD_CALIBRATION_SOURCE_ROOT`, verifies bytes first, invokes slice-1
retention/materialization/admission services, verifies every selection hash,
and substitutes returned fragment/event identities. A separately reviewed
manifest accounts for every logical key and expected count. No summary or
paraphrase is evidence.

If lawful bytes are unavailable, synthetic structural tests use conspicuously
synthetic identities, but the named source-complete calibration is reported as
**0 passed out of 5; 5 unexecuted**, never as pass/gold. It is a mandatory
implementation-review gate. No substitute PDF may be downloaded or invented.

| Packet | Positive candidate proof | Required negative/fail-closed proof |
| --- | --- | --- |
| 2024-14-03 | Five manufacturer scopes, exactly 182 separate models, one shared GFC 500/GSA 28/STC condition, one model/configuration rule, one software-update requirement, one independently activated installation prohibition, evidence reuse, serial criterion `not_applicable` with `ev-applicability`; stable golden hash | Reject 182 flattened labels, copied evidence text, combined manufacturer/model, invented serial unknown/range, missing GSA/STC/master-drawing predicate, or prohibition incorrectly tied only to Table 1 |
| 2011-10-09 | One Cessna scope, exactly 224 models/all serials, supersession, ten ordered requirements sharing one recurring 100-hour/12-month whichever-first timing group and source evidence; stable golden hash | Reject 172S as listed, float timing, missing/mixed anchor, missing one action in the shared recurrence completion model, or replacement falsely marked terminating |
| 2002-13-04 | Engine plus installed-magneto predicates, explicit `unknown/conflicting_evidence` serial scope bound to both fragments, two typed missing-pin branches, installation prohibition, non-exhaustive search hints isolated from applicability; stored candidate-only; stable golden hash | Reject silently selected/broadened serial endpoint, search hint referenced by controlling expression, unlisted engine family, or both engine-family branches active for one known engine |
| 98-17-11 | Engine/crankshaft scope, repairer/date/work-order evidence references, explicit unknown provenance feeding the source-mandated compliance branch, inspection/removal and replace/rework alternatives, bounded Federal Register evidence; stable golden hash | Reject blank engine serial as exclusion, unknown repairer converted to false/not-applicable, component logbook facts embedded as AD authority, or generic rework without approved-data evidence |
| 2008-26-10 + correction | Original plus correction fragments, corrected 182-model set excluding 188, historical/part predicates and exception, IFR/non-IFR alternatives, whichever-first/later timing, four bulletin identities `unknown/not_obtained`, general AMOC only; candidate-only for unseen methods; stable golden hash | Reject model 188, ignored correction/address, bulletin retention `known` without admitted bytes/fragments, unseen bulletin method asserted, general AMOC converted to aircraft use, or candidate labeled released/actionable |

Cross-packet assertions (target only; current execution is **0 passed out of
5, 5 unexecuted**):

- all five fixture keys resolve to admitted slice-1 fragments and no fragment
  text is repeated in canonical JSON: 5 expected out of 5;
- all five store with constant candidate-only gate and are absent from released
  catalog/matching/due-state queries: 5 expected out of 5;
- each fixture is invariant to object/set ordering and sensitive to ordered
  regulatory sequence: 5 expected out of 5;
- exact retries return the same proposal/submission and concurrent distinct
  origins reuse content without losing provenance: 5 expected out of 5; and
- future real retained-bulletin and aircraft-AMOC fixtures remain 0 available
  out of 2 and are not represented as passed.

### Persistence, authorization, concurrency, and rollback tests

- platform admin POST new/retry/content-reuse: expected 3 passed out of 3;
- owner, maintenance shop, inactive admin, and role-revoked-at-submit denial:
  expected 4 passed out of 4;
- same-key same-content retry, same-key different-content conflict, concurrent
  same key, concurrent different keys/same content, and transaction rollback:
  expected 5 passed out of 5;
- immutability on all five tables and direct-SQL integrity negatives;
- migration fresh upgrade, occupied downgrade refusal, overlapping
  insert/downgrade race, empty downgrade, and re-upgrade: expected 5 passed out
  of 5; and
- V3 regression proving no changed V3 extraction/review/materialization/release
  behavior.

## Expected file scope

This framing phase edits only:

- `.ai/review-runs/T081-V4-SCHEMA-SLICE-2/decision.md`.

Expected implementation scope after design PASS is additive and bounded to:

- one versioned V4 JSON Schema artifact;
- one V4 validation/canonicalization/proposal service;
- additive ORM models and one Alembic migration;
- narrow V4 candidate request/response schemas and platform-admin API route;
- focused schema/semantic/canonical/API/PostgreSQL/migration tests; and
- slice-2 implementation evidence inside this new review run.

Excluded from implementation scope are existing calibration Markdown/JSON,
closed slice-1 review artifacts, V3 services/data, normalized V4 semantic
tables, frontend/UI, publication, read cutover, matching, compliance, due state,
and provider/CLI writers.

## Known uncertainty

The following implementation details require evidence during design review or
the slice implementation but do not change the domain boundary:

1. Select and pin an RFC 8785-compatible Python dependency, or demonstrate a
   small restricted canonical encoder with complete conformance vectors. Generic
   `json.dumps` is not acceptable.
2. Set concrete resource limits above the 224-model calibration maximum from
   measured parser/validator/PostgreSQL behavior. Limits are validator-versioned
   and tested at boundary and boundary+1.
3. Confirm whether PostgreSQL `pgcrypto` is already deployable. If not, store a
   database-verifiable raw SHA-256 using a supported immutable SQL function or
   add a reviewed extension dependency; do not silently downgrade DB integrity.
4. Decide whether the optional read API is needed for this vertical slice or
   whether service-level readback plus tests is sufficient. This does not alter
   the single-writer/no-GUI boundary.
5. The accepted packets identify semantics, not executable canonical fixture
   bytes. Fixture transcription must receive independent evidence-key/count
   review; implementation may not claim gold status merely because JSON passes
   the validator.
6. Slice 1 supports single-page fragments. Calibration clauses spanning pages
   must bind multiple existing single-page fragments, not invent a cross-page
   fragment or weaken slice-1 constraints.

None of these uncertainties authorizes a release path, V3 mutation, hidden
writer, or normalized materialization in slice 2.
