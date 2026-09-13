# T081 V4 Slice 3B — Normative Mapping Matrix

Status: design proposal; independent review required

Mapping contract: `paprnav-ad-v4-obligation-mapping-1`

Canonical parent: validator-2/c14n-2 `ADV4CandidateProposal`

Projection fields, in fixed root order:

```text
incorporatedDocuments
requirements
recurrenceGroups
amocAuthorityProvisions
```

This matrix is normative for Python construction, generated structural SQL,
hand-written PostgreSQL invariants, verified reads, reconstruction, and test
coverage. `{i}`, `{j}`, and `{k}` are zero-based canonical array ordinals after
Slice-2 schema-aware canonicalization. “Own evidence” means the exact
`evidenceKeys` array on that canonical object. No unlisted evidence inheritance
is permitted.

## 1. Common identities and domains

### 1.1 Deterministic identity

All row hashes use the closed internal-record profile of restricted-JCS c14n-2
and:

```text
SHA256(ROW_DOMAIN || canonical({"table": table, "identity": identity}))
```

The row ID is the table prefix plus the first 32 lowercase hex characters.
Every table stores or can recompute the full 64-character identity hash.

Candidate source values use the validator-2 source profile, which forbids JSON
null and numbers. Closed internal identity/envelope/request/event records use a
separate profile because their normative shapes contain SQL ordinals, counts,
sequence numbers, and explicit null union arms. That profile admits only exact
built-in JSON objects, arrays, strings, booleans, null, and nonnegative base-10
integers through `2147483647`; it rejects U+0000 strings/keys, negative or
larger integers, decimals/floats, NaN, infinity, cyclic/excessively nested
containers, and every unlisted or subclassed Python type. Candidate source also
rejects U+0000 before its PostgreSQL JSONB storage boundary. Object keys
use UTF-16/JCS order and arrays retain their explicitly specified canonical
order. This distinction does not widen canonical candidate input. Python and
PostgreSQL must produce byte-identical internal records, including numeric JSON
tokens (never quoted decimal strings), before hashing.

Semantic-node identity is:

```json
{
  "projectionId": "<3B projection ID>",
  "nodeType": "<closed node type>",
  "nodeKey": "<exact key below>",
  "pointer": "<exact source pointer>"
}
```

Node `canonical_node_hash` is plain SHA-256 of the canonical value at its
pointer. Scalar synthetic nodes hash the scalar. Container-local identities
use their complete source pointer as `nodeKey`; globally stable canonical keys
use that key. Expression keys are their full source pointers and are unbounded
text so schema-valid depth cannot overflow a varchar.

### 1.2 Physical domains

| Domain | PostgreSQL/ORM representation | Rule |
| --- | --- | --- |
| IDs | varchar(36) | deterministic prefix plus 32 hex |
| stable keys | varchar(128) | exact validator-2 key |
| node key/pointer | text | no narrowing below candidate byte/depth limits |
| identifier/action step/reason | text | exact source string, up to schema/body limit |
| enum/code | varchar(64) | closed CHECK matching validator-2 |
| hashes | char/varchar(64) | lowercase hex and recomputed |
| ordinal/count | integer | 0..2147483647; exact unique order |
| boolean | boolean | never integer/text coercion |
| decimal text | text | exact canonical grammar; length 1..16,384 before conversion |
| decimal query value | unconstrained numeric | exact prechecked cast, no rounding; text remains authority |
| canonical bytes | bytea | byte-exact source or closed internal-record restricted JCS profile, as applicable |

All projection/proposal and cross-slice references use composite FKs where the
target table exposes projection/proposal identity. Nullable columns are allowed
only for explicit optional presence or mutually exclusive union branches.

### 1.3 Exact row-identity registry

Except for the compatibility-preserved correction binding below, `row_id` and
`row_hash` are computed under
`paprnav:ad_extraction_v4:obligation-row:1\0` from the exact JSON identity
object shown. Object property order is restricted-JCS order, never source or
table-column order. Every `ordinal` and `sequenceNumber` property below is a
nonnegative JSON integer in the internal-record profile and remains an integer
in PostgreSQL; it is never passed through the number-free candidate-source
canonicalizer.

| Row/table label; ID prefix | Exact identity object |
| --- | --- |
| `projection`; `aox_` | `{proposalId,appProjectionId,materializerVersion,subtreeHash}` |
| `semantic-node`; `aon_` | `{projectionId,nodeType,nodeKey,pointer}` |
| `datum`; `aod_` | `{projectionId,pointer,kind,value}` where `value` is the exact scalar or the closed container kind |
| `evidence-link`; `aoe_` | `{projectionId,semanticNodeId,purpose,evidenceKey,ordinal}` |
| `action-document-ref`; `aor_` | `{projectionId,actionNodeId,documentNodeId,ordinal}` |
| `expression-edge`; `aog_` | `{projectionId,requirementNodeId,context,parentExpressionId,childExpressionId,ordinal}` |
| `requirement-dependency`; `aop_` | `{projectionId,requirementNodeId,prerequisiteRequirementNodeId,ordinal}` |
| `termination-edge`; `aot_` | `{projectionId,effectNodeId,terminatedRequirementNodeId,ordinal}` |
| `recurrence-group-member`; `aom_` | `{projectionId,groupNodeId,requirementNodeId,ordinal}` |
| `materialization-request`; `aoq_` | `{actorUserId,authorizingMembershipId,endpointAction,authPolicyVersion,idempotencyKey}` |
| `projection-event`; `aov_` | `{projectionId,sequenceNumber,eventHash}` |

Each physical typed-owner row uses its semantic-node ID as primary key and has
no independent row-hash preimage. Its complete identity, value, parentage, and
ordinal are verified through the semantic node plus its typed columns. The
typed-owner table name is nevertheless part of the exactly-one-owner union.

The shared correction table is the only domain exception. An existing 3A row
retains prefix `avk_`, table label `correction-binding`, domain
`paprnav:ad_extraction_v4:applicability-row:2\0`, and exact identity
`{refId,semanticId}`. A new 3B row uses the same prefix, label, and exact
two-property identity object with the obligation semantic ID, but domain
`paprnav:ad_extraction_v4:obligation-row:1\0`. Domain selection follows the
stored `binding_slice`; no existing row is restamped. `bindingSlice`,
generation, and projection ID are not separately present in either preimage.

### 1.4 Semantic parent and ordinal registry

Root array occurrences D1, Q1, G1, and A1 have null semantic parent and their
canonical array ordinal. Document assertions D2/D3/D4 have parent D1 and fixed
ordinals 0/1/2. AMOC assertion A2 has parent A1 and ordinal 0. Recurrence-group
timings G3/G4 have parent G1 and fixed ordinals 0/1; their terms use their
canonical term ordinals.

Requirement child slots are fixed independently of optional presence: action
Q2 is 0, activation-expression root is 1, branch Q5 is 2, initial timing T1 is
3, recurrence R1 is 4, and terminating effect Q7 is 5. A branch-condition root
has parent Q5 and ordinal 0. A recurrence-condition root has parent R1 and
ordinal 0; recurrence timing R6 has parent R1 and ordinal 1. A nonroot
expression has its parent expression as semantic parent; `not` child ordinal
is 0 and `all|any` child ordinal is its canonical operand ordinal. Action steps
and timing terms use their canonical array ordinals under Q2 and their timing
owner respectively. There are no inferred or compacted semantic ordinals when
an optional slot is absent.

### 1.5 Semantic owner union

Every semantic node has exactly one owner among:

```text
incorporated_document
value_assertion
requirement
action
action_step
branch
expression
timing_group
timing_term
recurrence
terminating_effect
recurrence_group
amoc_provision
```

Reference/edge tables are relationships, not additional owners. A typed owner
without its matching semantic node is impossible by FK; a node with zero or
multiple matching owners fails the deferred union check and verified read.

### 1.6 Evidence and hash rules

Evidence-link identity includes projection, semantic node, purpose, evidence
key, and canonical ordinal. It references the same-proposal Slice-2 candidate
binding. Each occurrence below states its evidence source and purpose. Exact
set/order equality and deterministic link hashes are checked at commit/read.

Generic datum identity includes projection, pointer, kind, and scalar value or
container kind. Datum ownership is the nearest enclosing semantic occurrence;
the datum at a semantic occurrence belongs to that node. Each datum's pointer,
parent, property name/array ordinal, kind, scalar columns, and hash are exact.

### 1.7 Projection envelope and structural counts

The subtree is the exact four-property canonical object named at the top of
this matrix. `subtree_bytes = c14n2(subtree)` and
`subtree_hash = SHA256(SUBTREE_DOMAIN || subtree_bytes)`. The projection ID is
the `projection` row identity in section 1.3. The exact projection envelope is:

```json
{
  "proposalId": "...",
  "directiveId": "...",
  "validatorVersion": "paprnav-ad-v4-validator-2",
  "canonicalizationVersion": "paprnav-ad-v4-c14n-2",
  "proposalCanonicalHash": "...",
  "evidenceBindingHash": "...",
  "appProjectionId": "...",
  "appProjectionHash": "...",
  "appMaterializerVersion": "paprnav-ad-v4-app-materializer-2",
  "materializerVersion": "paprnav-ad-v4-obligation-materializer-1",
  "mappingVersion": "paprnav-ad-v4-obligation-mapping-1",
  "mappingDigest": "...",
  "obligationSubtreeHash": "...",
  "gate": "candidate_only",
  "counts": {
    "semanticNodeCount": 0,
    "datumCount": 0,
    "evidenceLinkCount": 0,
    "documentCount": 0,
    "valueAssertionCount": 0,
    "requirementCount": 0,
    "actionCount": 0,
    "actionStepCount": 0,
    "actionDocumentRefCount": 0,
    "branchCount": 0,
    "expressionCount": 0,
    "expressionEdgeCount": 0,
    "requirementDependencyCount": 0,
    "timingGroupCount": 0,
    "timingTermCount": 0,
    "recurrenceCount": 0,
    "terminatingEffectCount": 0,
    "terminationEdgeCount": 0,
    "recurrenceGroupCount": 0,
    "recurrenceGroupMemberCount": 0,
    "amocProvisionCount": 0,
    "correctionBindingCount": 0
  }
}
```

Every named count is an immutable root column and equals the exact structural
set at commit/read. Requests and events are append-only audit rows and are not
root counts. `projection_bytes = c14n2(envelope)` and
`projection_hash = SHA256(PROJECTION_DOMAIN || projection_bytes)`. There is no
3B projection generation: current is unique `(proposal_id,
materializer_version)`, while event freshness is the maximum contiguous event
sequence.

### 1.8 Request and authorization contract

The exact canonical request payload is:

```json
{
  "action": "materialize_ad_v4_obligations",
  "directiveId": "...",
  "proposalId": "...",
  "appProjectionId": "...",
  "validatorVersion": "paprnav-ad-v4-validator-2",
  "canonicalizationVersion": "paprnav-ad-v4-c14n-2",
  "appMaterializerVersion": "paprnav-ad-v4-app-materializer-2",
  "materializerVersion": "paprnav-ad-v4-obligation-materializer-1",
  "mappingVersion": "paprnav-ad-v4-obligation-mapping-1",
  "mappingDigest": "..."
}
```

`request_bytes = c14n2(payload)` and
`request_hash = SHA256(REQUEST_DOMAIN || request_bytes)`. The authorization
claims object is exactly
`{actorUserId,authorizingMembershipId,organizationId,role,status,endpointAction,authPolicyVersion}`;
`auth_claims_hash = SHA256(AUTH_DOMAIN || c14n2(claims))`, with
`AUTH_DOMAIN = paprnav:ad_extraction_v4:obligation-auth-claims:1\0`.
`endpointAction` is `materialize_ad_v4_obligations`, `role` is
`platform_admin`, and `status` is `active`. Stored columns, bytes, hashes, and
the section-1.3 row identity must all agree. Reusing one identity with different
request bytes or target returns 409 with no writes.

### 1.9 Event and cause contract

`correctionBindingSetHash` covers exactly the projection's 3B-owned correction
bindings, never its parent's 3A bindings. For each 3B binding the normalized
record is exactly:

```json
{
  "bindingId": "...",
  "bindingHash": "...",
  "bindingSlice": "slice_3b",
  "generation": 1,
  "correctionRefId": "...",
  "targetProjectionId": "...",
  "targetSemanticNodeId": "..."
}
```

Records are sorted by the exact tuple `(correctionRefId,bindingSlice,
targetSemanticNodeId)`. The empty set is the canonical JSON array `[]`.
`correction_binding_set_bytes = c14n2(records)` and
`correctionBindingSetHash = SHA256(CORRECTION_BINDING_SET_DOMAIN ||
correction_binding_set_bytes)`, where
`CORRECTION_BINDING_SET_DOMAIN =
paprnav:ad_extraction_v4:obligation-correction-binding-set:1\0`. Python and
PostgreSQL independently reconstruct the normalized list from the shared table;
stored list order, omitted/extra bindings, or any changed normalized property
changes the hash and fails exact set validation.

Every event has one `causingRequestId`. Event zero is `materialized`, has
`sequenceNumber=0`, null predecessor and null external `cause`, and uses this
closed payload:

```json
{
  "eventType": "materialized",
  "projectionId": "...",
  "proposalId": "...",
  "appProjectionId": "...",
  "sequenceNumber": 0,
  "predecessorEventHash": null,
  "proposalCanonicalHash": "...",
  "evidenceBindingHash": "...",
  "appProjectionHash": "...",
  "obligationSubtreeHash": "...",
  "projectionHash": "...",
  "correctionBindingSetHash": "...",
  "causingRequestId": "...",
  "cause": null
}
```

Later event types and their one required cause are closed as follows:

| Event type | Exact `cause.kind` | Exact cause target |
| --- | --- | --- |
| `evidence_invalidated` | `evidence_lifecycle_event` | lifecycle event ID and hash |
| `parent_app_stale` | `app_projection_event` | Slice-3A projection event ID and hash |
| `candidate_corrected` | `candidate_relationship` | correcting relationship ID and hash |
| `candidate_replaced` | `candidate_relationship` | replacement relationship ID and hash |

Their payload has the same exact keys as the root payload, substituting the
later `eventType`, positive contiguous `sequenceNumber`, prior event hash, and
`cause={kind,id,hash}`. `event_bytes = c14n2(payload)` and
`event_hash = SHA256(EVENT_DOMAIN || event_bytes)`; the event row identity then
uses section 1.3. External causes are sorted by `(kind,id)` before append and
unique by `(projection_id,cause_kind,cause_id)`. A stale event has exactly one
cause, never a compound or nullable union. Multiple requests/events do not
alter the immutable projection envelope or any root count.

## 2. Incorporated documents and assertions

| ID | Canonical occurrence | Semantic type/key; parent; ordinal | Typed owner and identity | Columns/presence/evidence | References/cardinality/failure tests |
| --- | --- | --- | --- | --- | --- |
| D1 | `/incorporatedDocuments/{i}` | `incorporated_document`, `documentRefKey`; root; `i` | `obligation_documents`; PK node; unique projection/key and projection/ordinal | key, type, three assertion FKs; own evidence purpose `incorporated_document_clause` | Exactly D2-D4 and their nodes; X missing/extra/reorder/type/key/hash/evidence |
| D2 | D1 `/documentNumber` | `value_assertion`, full pointer; D1; 0 | shared assertion owner; unique `(D1,document_number)` | exact known/unknown/not-applicable union; own evidence purpose `document_identity` | Known requires value only; other branches reason+temporal only; X union/null/hash/evidence |
| D3 | D1 `/revision` | same, field `revision`; D1; 1 | shared assertion owner | same as D2 | Independent occurrence even if value/evidence equal |
| D4 | D1 `/retention` | same, field `retention`; D1; 2 | shared assertion owner | exact `unknown` only; reason/temporal; own evidence purpose `document_retention` | Any known/not-applicable/retained/source-document binding fails parent validator/DB |

Document type covers all six schema values. `documentNumber` and `revision`
each cover all three union branches. D1 has no FK to retained source bytes.

## 3. Requirements, actions, steps, and document references

| ID | Canonical occurrence | Semantic type/key; parent; ordinal | Typed owner and identity | Columns/presence/evidence | References/cardinality/failure tests |
| --- | --- | --- | --- | --- | --- |
| Q1 | `/requirements/{i}` | `requirement`, `requirementKey`; root; `i` | `obligation_requirements`; PK node; unique key, sequence, ordinal | key, integer+exact string sequence, type, recurrence-group presence/key, child FKs; own evidence `requirement_clause` | canonical ordinal follows key sort; sequence text equals one member of exact `1..N` strings before conversion, N<=2,000, and the set is contiguous/unique; exactly Q2,Q5,Q7,T1,R1 plus E activation, Q10 set, and optional group ref |
| Q2 | Q1 `/action` | `action`, pointer; Q1; 0 | `obligation_actions`; one per Q1 | action type, `orderedSteps` presence flag/count, document-ref count; own evidence `action_clause` | Exactly Q3/Q4 sets; all 11 action enums; absent vs present-empty distinct |
| Q3 | Q2 `/orderedSteps/{j}` when property present | `action_step`, pointer; Q2; `j` | `obligation_action_steps`; unique action/ordinal | exact text; zero own evidence | ordered sequence exact; missing/extra/reordered/value/hash attacks |
| Q4 | Q2 `/approvedDataDocumentRefKeys/{j}` | no semantic node | `obligation_action_document_refs`; deterministic edge identity; unique action/doc and action/ordinal | exact key and ref hash | FK to exact D1 in same projection; canonical set order; cross-doc/projection fails |
| Q5 | Q1 `/branch` | `branch`, pointer; Q1; 2 | `obligation_branches`; one per Q1 | kind; alt key/exclusive presence; condition-root presence; own evidence `branch_clause` | exact union Q6; X branch field/null/root drift |
| Q6a | Q5 kind `required` | Q5 only | Q5 owner | alt/exclusive/condition root all null | Any forbidden child fails |
| Q6b | Q5 kind `conditional|exception` | Q5 plus E-context root | Q5 owner | exactly one condition-expression root; alt/exclusive null | Missing/extra/wrong-context expression fails |
| Q6c | Q5 kind `alternative_member` | Q5 only | Q5 owner | alt key and exclusive non-null; condition root null | Each member is exact; validator-2 permits singleton and mixed-exclusivity groups, so 3B adds no group-level restriction |
| Q7 | Q1 `/terminatingEffect` | `terminating_effect`, pointer; Q1; 5 | `obligation_terminating_effects`; one per Q1 | kind and edge count; own evidence `termination_clause` | exact Q8 union |
| Q8a | Q7 kind `none` | Q7 only | Q7 owner | zero edges | Any termination edge fails |
| Q8b | Q7 kind `terminates` | Q7 plus zero or more Q9 edges | Q7 owner | exact key set, including schema-valid empty | Same-projection requirement FKs; self/cycle/missing/extra fail |
| Q9 | Q7 `/requirementKeys/{j}` | no semantic node | `obligation_termination_edges`; unique source/target and source/ordinal | exact target key/ref hash | canonical set order; participates in combined requirement cycle check |
| Q10 | Q1 `/prerequisiteRequirementKeys/{j}` | no semantic node | `obligation_requirement_dependencies`; unique source/target/kind and source/ordinal | fixed kind `prerequisite`; exact target key/ref hash | canonical set order; same proposal; self/cycle/missing/extra fail |
| Q11 | Q1 optional `/recurrenceGroupKey` | no semantic node | Q1 presence/key plus group-member edge G2 | exact stable key when present | Absent is SQL NULL plus false presence; present requires exact bidirectional membership |

Every requirement type covers all nine schema enums. Equal action step strings
at different ordinals remain distinct occurrences. Requirement evidence does
not substitute for action, branch, timing, recurrence, or termination evidence.

## 4. Requirement expression trees

The same mapping applies independently to `activation`, `branch_condition`,
and `recurrence_condition`. The context root pointer is respectively:

```text
/requirements/{i}/activationExpression
/requirements/{i}/branch/conditionExpression
/requirements/{i}/recurrence/conditionExpression
```

| ID | Branch | Semantic type/key; parent/ordinal | Typed expression columns | Target/reference and cardinality | Failure tests |
| --- | --- | --- | --- | --- | --- |
| E1 | `scope_ref` | `expression`, full pointer; expression parent or context root parent; exact registry ordinal | node type/path/context/owner Q1 | exact Slice-3A `product_scope` node for `scopeKey`; no other target; 0 children | wrong type/key/app projection/proposal, child, leaf state |
| E2 | `predicate_ref` | same | same | exact Slice-3A `condition` node; 0 children | same |
| E3 | `rule_ref` | same | same | exact Slice-3A `applicability_rule` node; 0 children | same |
| E4 | `requirement_state_ref` | same | plus exact state enum | exact Q1 target in 3B; 0 children | self/cycle/state/target drift |
| E5 | `not` | same | no target/state | exactly one child at ordinal 0 | zero/two child, cycle, wrong context |
| E6 | `all` | same | no target/state | at least two ordered children | zero/one/gap/reorder/cycle |
| E7 | `any` | same | no target/state | at least two ordered children | zero/one/gap/reorder/cycle |

Each context has exactly one root at expression path `/`; every nonroot has
exactly one incoming edge; activation root is Q1/1, branch-condition root is
Q5/0, and recurrence-condition root is R1/0. All nodes are reachable. Repeated structurally equal
subtrees at different pointers remain distinct. Long pointer/key vectors beyond
255 characters must commit and reconstruct exactly. No evaluator result column
exists.

## 5. Initial timing and timing terms

| ID | Canonical occurrence | Semantic type/key; parent; ordinal | Typed owner and identity | Columns/presence/evidence | Cardinality/failure tests |
| --- | --- | --- | --- | --- | --- |
| T1 | Q1 `/initialTiming` | `timing_group`, pointer; Q1; 3 | timing owner kind `requirement_initial` | exact state/logic or reason/temporal; own evidence `timing_clause` | exactly one per Q1; union T2-T4 |
| T2 | known timing plan | T1 | timing owner | state known, logic one of 3, reason/temporal null, term count >=1 | terms T5 exact ordered set |
| T3 | unknown timing | T1 | timing owner | state unknown; controlled reason+temporal; logic null | zero terms |
| T4 | not-applicable timing | T1 | timing owner | state not_applicable; exact free-text reason+temporal; logic null | zero terms |
| T5 | T2 `/terms/{j}` | `timing_term`, pointer; T1; `j` | timing-term owner; unique T1/ordinal | metric, interval text+numeric, unit, comparator, anchor; own evidence `timing_term_clause` | exact ordered terms; decimal text/numeric equality; enum Cartesian vectors |

Known timing evidence and each term's evidence are independent exact sets.
Valid interval `0` is preserved and queryable. The projection does not infer
metric/unit/anchor compatibility beyond validator-2.

## 6. Recurrence and grouped timing

| ID | Canonical occurrence | Semantic type/key; parent; ordinal | Typed owner and identity | Columns/presence/evidence | References/cardinality/failure tests |
| --- | --- | --- | --- | --- | --- |
| R1 | Q1 `/recurrence` | `recurrence`, pointer; Q1; 4 | recurrence owner; one per Q1 | kind, timing-root presence, condition-root presence, reason/temporal; own evidence `recurrence_clause` | exact R2-R5 union |
| R2 | kind `none` | R1 | recurrence owner | no timing/expression/reason/temporal | forbidden child fails |
| R3 | kind `interval` | R1 | recurrence owner | exactly one known timing owner R6; no expression/reason/temporal | wrong timing state or extra expression fails |
| R4 | kind `conditioned` | R1 | recurrence owner | exactly one known timing R6 and one E recurrence root; no reason/temporal | missing/extra/wrong context fails |
| R5 | kind `unknown` | R1 | recurrence owner | exact controlled reason+temporal; no timing/expression | any child fails |
| R6 | R1 `/timing` | `timing_group`, pointer; R1; 1 | timing owner kind `requirement_recurrence` | known plan only; own timing evidence | exact T5 terms |
| G1 | `/recurrenceGroups/{i}` | `recurrence_group`, key; root; `i` | recurrence-group owner; unique key/ordinal | completion policy fixed; timing FKs; member count; own evidence `recurrence_clause` | >=2 members; exact G2/G3/G4 |
| G2 | G1 `/requirementKeys/{j}` | no semantic node | recurrence-group-member edge; unique group/requirement and group/ordinal | exact target key/ref hash | canonical set order; bidirectional Q11 equality |
| G3 | G1 `/initialTiming` | `timing_group`, pointer; G1; 0 | timing owner kind `recurrence_group_initial` | full T2/T3/T4 union; own evidence `timing_clause` | exact terms if known |
| G4 | G1 `/recurringTiming` | `timing_group`, pointer; G1; 1 | timing owner kind `recurrence_group_recurring` | full T2/T3/T4 union; own evidence `timing_clause` | exact terms if known |

Grouped Q1 rows must have initial timing without `logic` and recurrence kind
`none`, exactly as validator-2 defines. 3B stores but does not evaluate
`all_active_requirements`.

## 7. General AMOC authority

| ID | Canonical occurrence | Semantic type/key; parent; ordinal | Typed owner and identity | Columns/presence/evidence | Cardinality/failure tests |
| --- | --- | --- | --- | --- | --- |
| A1 | `/amocAuthorityProvisions/{i}` | `amoc_provision`, `provisionKey`; root; `i` | AMOC provision owner; unique key/ordinal | provision key, authority assertion FK; own evidence `amoc_authority_clause` | exactly A2; missing/extra/reorder/hash/evidence |
| A2 | A1 `/approvingAuthority` | `value_assertion`, pointer; A1; 0 | shared assertion owner field `approving_authority` | exact known/unknown/not-applicable union; own evidence `amoc_authority_clause` | all union branches; no aircraft/method/timing/use fields |

An empty AMOC array creates zero A1/A2 rows. The existence of A1 never creates
an aircraft-specific AMOC-use record or compliance credit.

## 8. Correction semantic bindings

For each existing correction ref where `owner_slice='slice_3b'`:

| Namespace | Exact 3B target type/key | Binding rule |
| --- | --- | --- |
| `requirements` | Q1 `requirement` / `requirementKey` | one generation-1 obligation binding |
| `recurrenceGroups` | G1 `recurrence_group` / `recurrenceGroupKey` | one generation-1 obligation binding |
| `amocAuthorityProvisions` | A1 `amoc_provision` / `provisionKey` | one generation-1 obligation binding |

The binding uses only the obligation projection/node columns; the legacy 3A
pair is null. Every 3A ref keeps exactly its existing app pair and has null 3B
columns. Foundation-owned refs have no semantic binding. Cross-namespace,
wrong-type, wrong-key, wrong proposal/projection, missing, extra, generation,
slice, and hash drift fail commit/read. A 3B binding has `binding_slice =
'slice_3b'` and `generation = 1`; its ID/hash follows the explicit 3B exception
in section 1.3. Correction root/ref/evidence counts and canonical reconstruction
do not change after adding bindings.

## 9. Projection, request, event, and global rules

| ID | Row | Required exactness |
| --- | --- | --- |
| P1 | projection root | exact section-1.7 envelope, bytes/hash, section-1.3 identity, and all 22 immutable structural counts; no request/event count |
| P2 | request | exact section-1.8 payload, auth claims, bytes/hashes, row identity, and idempotency conflict behavior |
| P3 | root event | exact section-1.9 materialized payload, sequence 0, request cause field, null predecessor/external cause, bytes/hash/row ID |
| P4 | later stale event | authorized POST only; one closed section-1.9 cause, exact prior hash, contiguous sequence, deterministic uniqueness and bytes/hash/row ID |

The deferred validator compares expected and actual sets for every table, then
performs the exactly-one-owner union and typed JSON reconstruction. All root and
child tables have immutable triggers plus INSERT/UPDATE/DELETE dirty/completeness
coverage. The unique projection has no generation; commit/read validation uses
the maximum contiguous event sequence as its latest audit state.

## 10. Complete positive and adversarial oracle

Positive vectors:

```text
D-TYPES-6
D-ASSERTION-3x3
Q-REQUIREMENT-TYPES-9
Q-SEQUENCE-PRECONVERSION-BOUNDARIES
Q-ACTION-TYPES-11
Q-STEPS-ABSENT-EMPTY-MULTIPLE
Q-DOCREF-EMPTY-MULTIPLE
Q-PREREQ-EMPTY-CHAIN-DAG
Q-BRANCH-REQUIRED-CONDITIONAL-EXCEPTION-ALTERNATIVE
E-ALL-7-BRANCHES-X-3-CONTEXTS
E-LONG-POINTER
T-STATE-KNOWN-UNKNOWN-NA
T-LOGIC-3
T-METRIC-5-UNIT-6-COMPARATOR-5-ANCHOR-5
T-DECIMAL-BOUNDARIES
R-NONE-INTERVAL-CONDITIONED-UNKNOWN
G-MEMBERSHIP-2-MULTIPLE
G-TIMING-UNIONS
A-EMPTY-ASSERTION-3
CORRECTION-3B-NAMESPACES
CALIBRATION-5
IDENTITY-GOLDENS-ALL-RELATIONSHIPS
PROJECTION-COUNTS-22-NO-AUDIT-CHILDREN
REQUEST-AUTH-PREIMAGE-GOLDENS
EVENT-ROOT-AND-ALL-4-CAUSE-UNIONS
MULTIPLE-REQUESTS-EVENTS-ROOT-STABLE
CORRECTION-3A-BYTE-COMPATIBILITY
CORRECTION-BINDING-SET-EMPTY-NONEMPTY-GOLDENS
```

Every positive vector passes expected-graph generation, ORM materialization,
fresh PostgreSQL commit, generic reconstruction, typed reconstruction, and
verified API read.

Direct-SQL/read corruption classes apply to every relevant row:

```text
X-NODE-ID-TYPE-KEY-POINTER-PARENT-ORDINAL-HASH
X-OWNER-MISSING-EXTRA-DUPLICATE-WRONG-FAMILY
X-DATUM-MISSING-EXTRA-KIND-VALUE-OWNER
X-UNION-PRESENCE-NULL-STATE-REASON-TEMPORAL
X-EVIDENCE-MISSING-EXTRA-ORDER-PURPOSE-BINDING-HASH
X-REFERENCE-MISSING-WRONG-TYPE-WRONG-KEY-CROSS-PROJECTION
X-ORDER-NEGATIVE-GAP-DUPLICATE-REORDER
X-EXPRESSION-ROOT-PARENT-ARITY-REACHABILITY-CYCLE-CONTEXT
X-REQUIREMENT-SELF-CYCLE-ALTERNATIVE-MISMATCH
X-REQUIREMENT-SEQUENCE-RESOURCE-NONMEMBER-OVERFLOW-GAP
X-TIMING-DECIMAL-CAST-ROUNDING-TERM-COUNT
X-RECURRENCE-CHILD-PRESENCE-GROUP-MEMBERSHIP
X-CORRECTION-PAIR-SLICE-GENERATION-TARGET-HASH
X-PROJECTION-COUNT-BYTES-HASH-PARENT-APP
X-REQUEST-EVENT-AUTH-IDEMPOTENCY-CHAIN
X-REQUEST-PREIMAGE-PROPERTY-TARGET-CLAIM
X-EVENT-CAUSE-NULL-MULTIPLE-TYPE-TARGET-HASH-ORDER
X-EVENT-SEQUENCE-PREDECESSOR-ID-HASH
X-CORRECTION-BINDING-SET-ORDER-FIELD-HASH
X-ROOT-COUNT-INCLUDES-REQUEST-OR-EVENT
X-FORGED-VALIDATOR2-PARENT
X-UPDATE-DELETE-AFTER-IMMUTABILITY-DISABLED
X-SET-CONSTRAINTS-IMMEDIATE-THEN-MUTATE
```

Read corruption tests derive canonical expected values by zip/enumeration and
reject stored ordinal drift before indexing. Each public audit route returns a
controlled 409 and leaves row/event counts unchanged.

## 11. Five-packet obligation expectations

| Packet | Mandatory 3B proof |
| --- | --- |
| 2024-14-03 | 2 requirements; software update and installation prohibition; no per-model clones across 182 models |
| 2011-10-09 | 10 requirements in sequence; 9 prerequisite edges; one 10-member group; two-term whichever-first initial/recurring timing |
| 2002-13-04 | family-conditional branches plus installation prohibition; uncertainty preserved and never evaluated |
| 1998-17-11 | two alternative members, conditional branch, rework action, approved-data document reference; no aircraft work-order/serial invention |
| 2008-26-10 | 4 unknown/not-obtained incorporated documents, 6 requirements, both whichever-first/later, 1 general AMOC provision, exact `req-report` correction binding |

For all five: exact source-accounted evidence links, one requirement per
canonical requirement, byte-identical four-field subtree reconstruction, and
unchanged candidate and 3A identities/hashes.
