# Decision packet: T081-V4-SCHEMA-SLICE-4

## Objective

Add the first V4 administrator review workflow and immutable human-signoff
gate on top of the candidate, applicability, obligation, and evidence records
delivered by Slices 1-3B.

This bounded slice decides whether one exact V4 candidate is rejected for
remediation or independently signed for candidate-only retention. It computes
and displays the release blockers, but release-eligible acceptance is
deliberately unavailable: Slice 3A has no reviewed executable evaluator
contract. A separately reviewed evaluator/publisher prerequisite must exist
before Slice 5 may add `released_actionable_accepted` or select a current V4
authority. This slice does not publish, replace a V3 decision, or feed search,
matching, coverage, compliance, terminating-credit, or due-state consumers.

Task base is commit `4840a0b4bc5d7334ddcf51a80e39c8fa84b7b0c2`.

## User-visible outcome

An active platform administrator can open a V4 review queue and a structured
review workspace for an exact candidate proposal. The workspace presents:

1. official source identity, immutable hashes, relevant pages, and links to
   retained source evidence;
2. evidence fragments and every semantic use of each fragment;
3. directive identity, product scopes, shared conditions, applicability rules,
   requirements, timing, documents, and general AMOC authority as typed
   controls/tables rather than an editable raw-JSON textarea;
4. all reviewed unknowns, unsupported expressions, unverified incorporated
   documents, and their computed automation consequences;
5. exact applicability and obligation projection identities, reconstruction
   status, semantic-node/cardinality counts, and a read-only canonical JSON
   download;
6. proposal/evidence authorship conflicts and the independent-review result;
7. distinct actions for saving an annotation draft, requesting review,
   rejecting for remediation, and accepting candidate-only; and
8. a disabled release gate explaining the exact evaluator, normalization, or
   supporting-document prerequisites that prevent release eligibility.

Semantic correction never mutates the reviewed candidate. Slice 4 renders every
validator-2 family in typed read-only controls and does not transform form state
back into canonical semantics. A remediation decision directs creation of a new
V4 candidate through the existing validator-2 endpoint with an explicit
correction/replacement relationship, after which new Slice-3A and Slice-3B
projections are required. Draft annotations and decision intent are append-only
review revisions; they are not canonical AD authority.

The interface may say **Accept candidate-only**, never "approve," "publish,"
"released," or "release eligible." It must explain that executable evaluation,
signed release acceptance, and catalog selection are separate later operations.

## Safety and correctness invariants

The following statements are falsifiable closure gates.

### Scope and non-publication

- **S4-I01:** No Slice-4 write creates or changes a current-decision pointer,
  released catalog row, search row, match, coverage row, compliance state,
  terminating credit, due state, V3 extraction, or V3 review.
- **S4-I02:** A candidate-only decision is never returned by an existing
  released/catalog/search endpoint merely because its signoff exists. No
  `released_actionable_accepted`, release-eligible, selected, or current V4 row
  can be inserted under the Slice-4 database contract.
- **S4-I03:** V1/V2/V3 extraction and review records remain byte-for-byte and
  state-for-state unchanged by every Slice-4 endpoint.

### Exact input binding and freshness

- **S4-I04:** Every case, draft, request, rejection, and rejecting signoff binds
  a server-derived stable input-identity bytes/hash plus a timestamped
  observed-input audit envelope/hash. Observation time is excluded from the
  stable CAS identity. The closed observation
  branches are `verified`, `missing`, `stale`, `integrity_error`, and
  `unsupported_version`, with stored IDs/hashes when present and a stable error
  code when not verified. Only an accepted decision and accepting signoff must
  bind one directive, candidate proposal ID/hash, evidence-binding hash,
  verified Slice-3A projection ID/hash, verified Slice-3B projection ID/hash,
  both materializer versions, the Slice-3B mapping version/digest, validator
  version, and canonicalization version.
- **S4-I05:** For candidate-only acceptance, the two projections must belong to the same candidate and
  directive, Slice 3B must bind that exact Slice-3A projection/hash, and both
  reconstruction verifiers must reproduce their exact canonical subtrees.
- **S4-I06:** An accepting signoff revalidates the candidate, all evidence bindings, source
  document hashes, fragment lifecycle heads, both projection event heads,
  typed-owner graphs, mapping digests, reconstructions, and counts inside the
  signing transaction. A rejecting signoff instead binds the frozen and current
  observed-input envelopes plus rejection reasons and creates no decision-node
  graph. Page-load validation is never authority for a later sign.
- **S4-I07:** Any missing, superseded, quarantined, differently hashed, stale,
  cross-candidate, cross-directive, or non-reconstructable input fails closed.
  It may be recorded in an observed-input envelope and displayed/rejected for
  remediation, but it cannot be accepted candidate-only.

### Classification and node gates

- **S4-I08:** Every Slice-3A and Slice-3B semantic node has exactly one bound
  decision-node gate row. No extra row, omitted node, duplicate node, or
  cross-projection node may commit.
- **S4-I09:** Node gate values are a closed automation set:
  `candidate_only`, `human_determination_required`, and `actionable`.
  `candidate_only` means the semantics may be retained but cannot support an
  automated or affirmative conclusion; `human_determination_required` means a
  valid later aircraft-specific determination is required; `actionable` means
  the source support and implemented evaluation contract are complete for the
  node. Exact source representation is stored separately as
  `representation_status=exact|explicit_unknown`; it never makes an
  unevaluated node actionable.
- **S4-I10:** Decision dependency edges are complete and deterministic for
  parent/child, identity-mapping consumption, rule exclusion, expression,
  requirement dependency, document, recurrence, and terminating-effect
  dependencies. External supersession/change dependencies bind exact external
  projection/signal heads in a separate non-node snapshot. A parent gate is
  never more permissive than a propagating dependency under rank
  `candidate_only < human_determination_required < actionable`.
- **S4-I11:** Gate computation is versioned and deterministic from canonical
  candidate bytes, evidence bindings, verified projection graphs, source and
  document admission state, and a declarative gate-rule specification. Python
  generation, PostgreSQL commit validation, read verification, and tests use
  the same generated expectations while retaining independent implementations
  at the trust boundaries.
- **S4-I12:** `candidate_only` is accepted only when minimum product/rule/
  independently reviewable requirement cardinalities hold, every known safety
  value has live evidence, and every explicit unknown has reason, temporal
  scope, evidence, and a recorded consequence. Missing source identity/hash,
  minimum shape, or evidence is remediation-only. All current applicability
  rules remain nonactionable because the reviewed evaluator contract is
  `none`; unreviewed identity mappings and unverified supporting documents also
  remain nonactionable. Therefore this slice always reports release blocked and
  PostgreSQL rejects every release-acceptance event/state, including direct SQL.

### Authorization, independence, and audit

- **S4-I13:** Every queue/detail/draft/request/sign/reject/correction endpoint
  performs server-side authorization. Mutating endpoints repeat authorization
  after locking and immediately before commit. UI visibility is not a control.
- **S4-I14:** Only a currently active `platform_admin` membership may sign or
  reject. The immutable signoff captures actor user, exact membership and
  organization, role/status/validity, policy/action/version, claims hash,
  server authorization result, and decision time.
- **S4-I15:** One eligible human signoff is sufficient, but any human who
  submitted or corrected the exact candidate or created/admitted any bound
  evidence fragment cannot be its sole accepting signer.
  The computed conflict set and its source event IDs are stored and hashed.
  Machine-only authorship is not self-review. Rejection and annotations do not
  create semantic authorship.
- **S4-I16:** No unsupported source-document authorship is invented. Existing
  primary-source ingestion without an attributable human admission is recorded
  as system ingestion; independently admitted supporting documents use new
  attributable immutable admission events.
- **S4-I17:** Each lifecycle event is append-only, hash chained, bound to an
  exact expected predecessor, and has one canonical event hash. The stored
  `signature_hash` is a server-generated, domain-separated integrity digest of
  the decision and authorization snapshot; the product does not represent it
  as PKI, user-held-key signature, or non-repudiation proof.

### Lifecycle, idempotency, and concurrency

- **S4-I18:** An immutable review case is the aggregate root. Its event types
  and folded states are closed and monotonic:
  `case_created/draft -> draft_saved/draft -> review_requested/pending_review
  -> review_rejected/rejected | candidate_only_accepted/candidate_only`.
  `draft_saved` may repeat only before `review_requested`. A new review of the
  same candidate creates a successor case with a higher case sequence and an
  explicit predecessor case. Release acceptance, selection, deselection,
  invalidation, and quarantine are not created by this slice.
- **S4-I19:** Save-draft appends an immutable annotation revision. Requesting
  review freezes one exact revision. Later drafts cannot change that pending or
  accepted revision.
- **S4-I20:** Exact retry of a mutating request returns the original result.
  Reuse of an idempotency key with a different canonical request conflicts.
  Concurrent terminal decisions for the same pending predecessor commit at
  most one accepted/rejected successor; no losing transaction leaves a partial
  decision, signoff, gate graph, or event.
- **S4-I21:** Accepted historical signoff rows never silently change meaning
  after actor deactivation or later input invalidation. Read-time verification
  reports the immutable historical result separately from current eligibility
  and fails the current-eligibility check closed without writing from GET.

### Read integrity and resources

- **S4-I22:** Review and decision GETs are side-effect free and reverify hashes,
  event chains, auth snapshot consistency, gate/node/edge completeness, source
  binding, projection freshness, and reconstruction. Corruption returns a
  stable conflict/integrity response rather than partially trusted content.
- **S4-I23:** All list endpoints have deterministic ordering and bounded
  pagination. Detail/canonical downloads and form submissions reuse the V4
  byte, depth, node, edge, array, and string limits; no endpoint enables
  unbounded review payloads or N+1 source-content loading.
- **S4-I24:** The five calibration packets round-trip exactly through queue,
  form projection, decision preview, gate classification, candidate-only
  signoff, and read verification. Their expected decision state is declared by
  a shared oracle, not inferred in the test. A deliberately known-value
  synthetic fixture proves that release remains blocked solely by the frozen
  `evaluator_contract='none'`; no fixture can bypass that prerequisite.

## Current behavior

The legacy `/logbook/ads/reviews` page is a V3 extraction-review workflow. It
uses a raw JSON editor and its "Approve & publish" action mutates legacy
extraction/directive state, materializes legacy applicability and requirements,
invalidates match/due data, and becomes visible to released readers. Legacy
release verification is implemented in `app.services.ad_release`, including
read-time materialization side effects. That path must not be reused for V4.

V4 currently has immutable candidate proposals and submission/audit records,
verified evidence bindings, a candidate-only Slice-3A applicability projection,
and a candidate-only Slice-3B obligation projection. Both projections have
typed graphs, immutable materialization requests, event chains, PostgreSQL
deferred validation, and fail-closed reconstruction readers. There is no V4
human review version, decision-node automation gate, signoff, or selected
released decision.

The current incorporated-document projection deliberately preserves retention
as unknown unless supported by separately retained evidence. It does not yet
represent an independently reviewed supporting-document admission. Therefore
an incorporated-document-dependent method cannot become release-eligible from
the projection alone.

## Proposed design

### 1. Declarative review/gate contract

The separately reviewed normative input
`normative-gate-and-form-matrix.md` freezes:

- semantic node family and release-required status;
- dependency extraction rules for both projection graphs;
- evidence and supporting-document requirements;
- exact conditions mapping a node to each gate rank;
- aggregate candidate-only/remediation/release-blocked classification;
- stable reason codes and user-facing descriptions; and
- lifecycle state/event transitions.

The specification produces deterministic expected node rows, dependency rows,
counts, canonical bytes, and hashes. PostgreSQL does not execute Python. A
separate deferred SQL validator enforces the generated closed-world row set,
same-projection/candidate bindings, rank monotonicity, event-state shape,
terminal uniqueness, and aggregate decision constraints. Read verification
recomputes the expectation from authoritative inputs and compares every stored
row and digest. Shared fixture-oracle snapshots exercise all three boundaries.

Rules remain independently implemented where defense in depth requires it:
current authorization and row locking in the service; FK/check/unique/deferred
constraints in PostgreSQL; and full reconstruction/hash revalidation in reads.
The Python specification is not a substitute for the database boundary, and a
stored database digest is not a substitute for source reconstruction.

### 2. Additive V4 persistence

Migration `20260913_0029` adds V4-only tables (final names may be shortened to
fit PostgreSQL identifier limits while retaining these meanings):

- `ad_v4_review_cases`: immutable aggregate roots identified by proposal and
  monotonically allocated case sequence, with optional predecessor case;
- `ad_v4_review_draft_revisions`: immutable reviewer annotations and intended
  action bound to a case, exact observed inputs (including missing/stale
  observations), prior draft, and case-event sequence;
- `ad_v4_decision_versions`: immutable aggregate snapshot with candidate,
  projection, mapping, evidence, classifier, graph, and canonical hashes. Only
  a candidate-only accepted terminal has a decision version;
- `ad_v4_decision_node_gates`: exactly one gate and reason set per Slice-3A or
  Slice-3B semantic node;
- `ad_v4_decision_gate_dependencies`: complete ordered dependency edges used
  for rank monotonicity;
- `ad_v4_decision_external_dependencies`: exact non-node supersession/change
  dependency snapshots, including target projection/hash/event head or the
  controlled unresolved branch;
- `ad_v4_decision_authorship_bindings`: proposal and fragment authors/editors
  considered by self-review policy;
- `ad_v4_review_requests`: idempotent authorization snapshot that freezes a
  draft revision and observed input set as pending review;
- `ad_v4_review_rejections`: immutable reason-coded remediation outcomes that
  bind the stored proposal identity and observed integrity failures without
  pretending that an invalid/missing projection graph was verified;
- `ad_v4_signoff_events`: immutable accepting or rejecting authorization and
  independence snapshot with decision hash and signature hash;
- `ad_v4_review_case_events`: the per-case event/state hash chain, limited to
  the events and folded states in S4-I18.

Supporting-document byte acquisition/admission is explicitly deferred to
`T081-V4-SCHEMA-SLICE-4D-DOCUMENT-ADMISSION`, which must pass its own design and
implementation review before an evaluator/release slice. Slice 4 stores no
external admission overlay, presents the canonical retention unknown exactly,
and assigns `candidate_only` to every supporting-document-dependent node.

All authoritative/event rows are insert-only through permissions and triggers.
Composite foreign keys bind same directive/proposal/projection identities.
Deferred constraint triggers validate complete graphs at commit, so insertion
order is flexible but partial/cross-boundary direct-SQL graphs cannot commit.
No Slice-4 table is a current-release pointer.

### 3. Eligibility construction

All existing and new V4 writers use the shared lock protocol below. Slice 4
adds the candidate-relationship advisory lock to the 3A/3B verification paths
so later submissions/corrections cannot enter an acceptance snapshot:

1. freshly selected actor user row, then exact membership row;
2. request-idempotency advisory lock;
3. candidate relationship-graph advisory lock for the directive;
4. candidate proposal row;
5. database gates in fixed order `validator2_write_enabled`,
   `materializer3a_enabled`, `materializer3b_enabled`,
   `reviewer4_draft_enabled`, `reviewer4_decision_enabled` (each writer takes
   the prefix it needs);
6. evidence bindings, fragments, and lifecycle heads in deterministic ID order;
7. Slice-3A supersession locks, projection advisory lock/root, correction
   roots/refs, then Slice-3B projection advisory lock/root;
8. review-case advisory lock/root, frozen request, and case-event head; and
9. projection and decision children in deterministic table/identity order.

Candidate creation follows its existing content lock before the relationship
lock because no proposal row exists yet; every operation that appends a
submission to an existing proposal takes the relationship lock before that
append. Evidence lifecycle writers take fragment locks but never later acquire
a proposal/review-case lock. Gate administration locks only the fixed gate
prefix and never later acquires proposal/case locks. Downgrade keeps the 3B
bounded table-first DDL protocol and never waits for tables while holding gates.
Deadlock/serialization victims become controlled retry/409 responses.

Within that protocol, the acceptance service:

1. calls the existing fail-closed candidate and projection verifiers;
2. reconstructs both subtrees and requires exact bytes/hashes;
3. computes every node gate and dependency edge from the versioned spec;
4. computes the aggregate state and explicit remediation/blocker reasons;
5. canonicalizes the decision snapshot, gate graph, authorship set, and input
   heads;
6. appends the decision, signoff, and terminal case-event rows in one
   transaction;
7. flushes so deferred validation failures are normalized to a stable conflict;
8. commits without touching any release consumer.

The accept endpoint exists only for candidate-only. PostgreSQL has no accepted
release branch. Administrators cannot override remediation-only to acceptance.
Rejection uses the frozen review request's observed-input digest and records
stable integrity/remediation reasons; it does not require or create a verified
decision-node graph and cannot be consumed as authority.

### 4. Authorization and self-review

Use fresh scalar `SELECT ... FOR UPDATE` queries for the actor and membership;
do not rely on previously identity-mapped ORM attributes. Under the current
schema, validity means `users.status='active'`,
`organization_memberships.status='active'`, membership user matches actor, and
role is `platform_admin`. There is no validity interval, so the snapshot records
`validityRule='status_only_v1'`, `validFrom=null`, and `validUntil=null` rather
than claiming expiry semantics. The page model exposes an authorization-
observation hash; submit supplies that stable hash as a stale-page CAS token, and the server
recomputes it from the locked rows. A deferred SQL constraint trigger locks the
same user then membership rows `FOR UPDATE` in the shared order and requires
those current values at signoff insert/commit. This conflicts with role/status
updates and is held through commit.

The authorship set is the union of:

- all current candidate submission actors, conservatively treated as human;
- `created_by_user_id` and admitted lifecycle actor for every bound evidence
  fragment; and
- no machine-only or supporting-document actor, because neither provenance
  path exists in this bounded slice.

Each binding stores the source table, event ID, user ID, authorship role, bound
hash, and a review-request cutoff set/count. The request-time SQL validator
independently reconstructs the complete set from every current proposal
submission and every bound fragment creator/admitted event, then compares both
directions with the supplied bindings and set hash. Acceptance repeats that
derivation; a missing/extra author, forged cutoff, or later submission/
relationship makes the request stale. Identical resubmissions before the cutoff
are authorship. Machine-only status is impossible and is not inferred from
payload origin. Accepting signoff requires the signer not to appear in the
independently derived frozen set.
If no independent active platform administrator exists, the object remains
pending. Rejection may be performed by an author because it cannot publish or
create affirmative authority, but the relationship is still recorded.

### 5. API contract

Add a separate V4 namespace under the existing AD router:

- `GET /ads/v4/reviews` — bounded review queue;
- `POST /ads/v4/review-cases` — explicitly create/reuse one case sequence for a
  proposal under proposal-scoped advisory lock; GET never creates it;
- `GET /ads/v4/review-cases/{case_id}` — typed form/preview model with current
  integrity, candidate-only eligibility, and release-blocker analysis;
- `POST /ads/v4/review-cases/{case_id}/drafts` — append annotation revision;
- `POST /ads/v4/review-cases/{case_id}/request-review` — freeze exact draft,
  observed input set, authorship cutoff, and predecessor event;
- `POST /ads/v4/review-cases/{case_id}/decision` — reject or accept
  candidate-only with predecessor CAS and idempotency key;
- `GET /ads/v4/decisions/{decision_version_id}` — immutable historical result
  plus separately computed current-integrity/current-eligibility status.

Pydantic request models are closed (`extra='forbid'`) and use enums/reason
codes rather than arbitrary semantic JSON. Canonical JSON download is read-only
and carries content-disposition, content type, canonical hash, and no-store
headers. Integrity failures never fall back to the V3 review serializer.

### 6. Reviewer UI

Add a V4-specific page rather than changing the behavior of the legacy V3
review page. It uses typed, read-only fields, tables, evidence selectors,
structured expression trees, and explicit unknown/blocker cards. Canonical JSON
is preview/download only. The exact control-to-canonical coverage and ordering
rules live in `normative-gate-and-form-matrix.md`. Slice 4 has no semantic edit
control and therefore no form-to-canonical transform that could drop, reorder,
or alter data. Correction is an explicit remediation outcome followed by a new
candidate submission outside this page; the page may compare predecessor and
successor candidates but cannot create or mutate either.

The UI re-fetches the detail model immediately before showing the confirmation
dialog and sends the exact expected predecessor/input hashes. The server still
rechecks all state. Stale, unauthorized, self-review, or candidate-only results
cannot be bypassed by client state or direct API calls.

### 7. Feature gates and operational boundary

Add three default-false application capabilities:
`PAPRNAV_AD_V4_SLICE4_READS_ENABLED`,
`PAPRNAV_AD_V4_SLICE4_DRAFTS_ENABLED`, and
`PAPRNAV_AD_V4_SLICE4_DECISIONS_ENABLED`. Add two default-false database write
gates: `reviewer4_draft_enabled` and `reviewer4_decision_enabled`. Reads require
the read application capability and an 0029-aware schema; draft/case/request
writes require both read+draft application capabilities and the draft database
gate; terminal writes additionally require the decision application capability
and decision database gate. The migration never enables a gate.

The rollout contract is: apply 0029, deploy 0029-aware readers everywhere,
enable reads, enable case/draft/request writes, then enable candidate-only
terminal decisions. Database capability rows are the enforceable downgrade
conditions; fleet-wide application disablement is an operational prerequisite
verified by deployment tooling, not something the migration claims to observe.
No release-acceptance/current-promotion setting exists in this slice.

## Alternatives considered

### Reuse the legacy extraction-review tables and route

Rejected. The legacy approve path has immediate V3 publication and derived-
state side effects, stores a different canonical contract, and cannot express
V4 node gates, exact 3A/3B projection binding, or V4 lifecycle hashes. Reuse
would violate S4-I01 through S4-I05.

### Add release-eligible acceptance before an evaluator exists

Rejected. Slice 3A deliberately preserves all conditions, rules, and
expressions with evaluator contract `none` and unreviewed identity mappings.
No current candidate can meet the parent release contract, even when every
source value is known. Slice 4 builds the signed candidate-only review and the
fail-closed release-blocker analysis. A separately reviewed evaluator is a
prerequisite to release acceptance; Slice 5 later adds release acceptance and a
separate CAS selection only after that prerequisite passes.

### Store only an aggregate decision gate

Rejected. It cannot prove the required complete node matrix, explain inherited
unknowns, enforce dependency monotonicity, or detect omitted/corrupted nodes.

### Store mutable review rows and a final snapshot

Rejected. Mutable drafts lose who saw and changed what and complicate stale
review/concurrency analysis. Immutable draft revisions are inexpensive and
preserve the exact pending review input.

### Let a platform administrator override the computed gate

Rejected. Human review determines whether the evidence and normalized
semantics satisfy the declared contract; it does not permit bypassing minimum
shape, evidence, reconstruction, evaluator, or document gates.

### Depend only on Python validation or only on PostgreSQL triggers

Rejected. Python-only checks are bypassable by direct SQL. SQL-only semantic
reconstruction would duplicate a large evolving validator and still not verify
retained source bytes. The proposed declarative expectation plus independent
transaction/read/database boundaries minimizes drift while preserving defense
in depth.

## Trust, authorization, and audit boundaries

- The browser is untrusted. Hidden controls, cached analysis, and form values
  never confer authority.
- The API authenticates the user and freshly evaluates a current active
  platform-admin user/membership pair under `status_only_v1`. The exact
  evaluation is frozen in the signoff snapshot.
- Existing candidate/projection tables are authoritative immutable inputs only
  after their fail-closed verifiers pass.
- Retained source bytes, page text, fragments, lifecycle heads, and exact hashes
  are evidence authority. User-supplied labels or URLs are not.
- Supporting-document bytes are authoritative only after immutable acquisition
  and independent admission events; candidate claims of retention are not.
- PostgreSQL is the final commit boundary and must reject partial, mismatched,
  unauthorized-shape, non-monotonic, or duplicate terminal graphs submitted by
  direct SQL.
- A hash proves exact binding and tamper evidence within this system, not truth,
  legal identity, or external cryptographic signature.
- The independent Codex adversary reviews design and implementation read-only.
  Claude, if used after a complete Codex packet, is untrusted review input.

## Read paths and consumers

Changed/new readers:

- V4 review queue and detail serializers;
- V4 decision historical/current-integrity serializer;
- frontend V4 review queue/detail/form components;
- canonical JSON/source/page/evidence links already used by V4 candidate and
  projection readers; and
- administrative audit display for draft, request, authorship, signoff, and
  lifecycle chains.

Explicitly unchanged consumers:

- legacy extraction review queue/decision route and UI;
- `app.services.ad_release` and all released AD catalog routes;
- AD search, match generation, coverage, compliance, terminating credit, and
  due-state readers/writers;
- current V3 directive/extraction status; and
- aircraft-specific decisions.

Repository review must still search those consumers and prove no accidental
call, relationship cascade, import side effect, or shared serializer leaks V4
accepted records.

Every queue/detail/decision/download operation runs in one separate
PostgreSQL `REPEATABLE READ`, read-only transaction, including authorization,
case/event reads, candidate submissions/relationships, fragment heads,
projections, gates, and current-integrity analysis. List ordering and its page
membership are fixed within that snapshot. Historical verification uses the
decision's frozen candidate/projection/event/authorship set and exact
gate/classifier/policy versions; current eligibility separately compares
current heads/current authorization facts. Historical verifier versions remain
available while referenced. If a version is unsupported, the API returns
`historical_verifier_unavailable` and never calls the current verifier as a
substitute. Later signer deactivation does not corrupt historical signoff.

## Write paths and administrative paths

Authorized Slice-4 writes are limited to immutable review cases, draft
revisions, review requests, candidate-only decision versions, node gates,
dependency/authorship bindings, rejections, signoffs, and case events. Slice 4
does not write supporting-document admission or semantic candidate data.

No generic CRUD, ORM cascade, seed script, fixture loader, backfill, or admin
shell helper may write accepted Slice-4 rows without satisfying the same
deferred database constraints. Tests include direct SQL because ORM/API-only
tests do not prove this boundary.

GET and list routes never flush, materialize, append invalidation, repair, or
update last-seen fields. Repair/correction is always an explicit authorized
command/event.

## Migration, compatibility, correction, and rollback

Migration 0029 is expand-only and leaves all V3 and prior V4 rows unchanged.
It creates disabled database gates and V4-only tables/functions/triggers.
Existing pre-0029 binaries remain supported only while Slice-4 gates are off
and no Slice-4 rows exist; the rollout contract requires 0029-aware readers
before writes are enabled.

Correction never updates an accepted decision. A semantic change creates a new
candidate relationship, new 3A/3B projections, new review request, new decision
version, and new signoff. Because Slice 4 does not select current authority,
there is no V4-to-V3 fallback behavior in this migration.

For parent-design sections 8.1 and 11, **V4 deployment** is the activation of
the first V4 release-acceptance/current-selection capability, not installation
or activation of candidate-only review tooling. Slice 4 neither releases nor
supersedes V3, so the existing V3 approval path remains available during this
pre-deployment coexistence interval. Slice 5 owns the platform-wide V3 write
freeze and must enable it transactionally/operationally before any V4 release
acceptance or selection capability. That later packet must re-review every V3
API, UI, provider, script, and administrative write path. No Slice-4 flag is a
V4 deployment/cutover signal.

Operational rollback disables all three application capabilities and both
database Slice-4 gates and keeps
all immutable rows readable by an 0029-aware binary. Physical downgrade takes
bounded root-before-child locks and refuses while either gate is enabled or any
Slice-4 case, draft, request, decision, node, dependency, authorship, rejection,
signoff, or event row exists.
It never deletes signed history. Restore from a verified backup is required if
physical removal is ever necessary after occupancy.

## Test strategy

### Pure specification and service tests

- table-driven gate cases for every Slice-3A and Slice-3B semantic-node family,
  each gate rank, evidence/document state, dependency inheritance, and aggregate
  decision state;
- complete graph/orphan/cycle/count/reconstruction/mapping digest checks;
- self-review sets covering proposal creator, identical resubmitter,
  corrector/replacer, fragment creator, fragment admitter, annotation author,
  independent reviewer, and post-cutoff submissions; current human submissions
  are never relabeled machine-only;
- stable canonical/hash vectors and idempotent exact replay/key-reuse conflict;
- role downgrade, user/membership deactivation, stale authorization-observation
  hash, changed event head, and cross-directive/projection counterexamples; and
- GET side-effect assertions.

### PostgreSQL migration and direct-SQL tests

- clean upgrade and fresh migrated disposable PostgreSQL suites;
- default-off gates and pre-enable route rejection;
- positive complete candidate-only and rejection transactions, plus direct-SQL
  proof that release acceptance cannot be represented;
- direct-SQL attempts with extra/missing/duplicate/cross-projection gate nodes,
  omitted/reordered/wrong dependency edges, more-permissive parents, altered
  values/hashes/counts, invalid lifecycle transition, forged auth shape,
  self-review signer, fabricated release state, and two terminal successors;
- transaction rollback/failure injection after graph insert, before event CAS,
  and after signoff insert;
- concurrent signers and idempotent retries; and
- downgrade succeeds when empty/disabled and refuses every occupied/enabled
  state without data loss.

### API and UI tests

- 401/403 for anonymous, non-admin, inactive, and downgraded users on
  every route, including direct API calls;
- queue pagination/order, form sections, source/page navigation, exact evidence
  uses, read-only JSON, blocker explanations, accessible confirmation, and
  honest non-publication copy;
- all validator-2 root families render read-only with exact order/presence and
  canonical download round-trips; no semantic edit control or transform exists;
- accept-state mismatch and stale predecessor return stable 409 responses;
- legacy V3 approve behavior remains isolated and no V4 route invokes it; and
- frontend typecheck/lint/build plus focused component/integration tests.

### Calibration and final gates

- all five canonical packets round-trip byte exactly through candidate, 3A,
  3B, review preview, node gates, signoff, and verified GET;
- the shared oracle declares each packet's expected remediation/candidate-only
  state and exact blocker/gate counts;
- 2008-26-10 remains candidate-only while incorporated bulletin contents are
  unverified and receives no affirmative method conclusion;
- a known-value synthetic packet still fails the release gate with exact
  `evaluator_contract_none` blockers, while one-bit evidence/projection/auth/
  event corruption fails closed;
- host suite and freshly migrated disposable PostgreSQL suite pass; and
- independent implementation and closure adversaries report no residual
  blocker before commit.

## Expected file scope

- `.ai/review-runs/T081-V4-SCHEMA-SLICE-4/**`
- `backend/app/db/migrations/versions/20260913_0029_*.py`
- `backend/app/models/core.py`
- `backend/app/schemas/ads.py`
- `backend/app/api/routes/ads.py`
- `backend/app/core/config.py`
- new `backend/app/services/ad_v4_review*.py` and declarative mapping/spec file
- bounded amendments to existing V4 candidate/3A/3B writers and readers needed
  to share the relationship advisory lock and repeatable-read protocol
- new Slice-4 rollout/contract documentation
- focused backend unit/API/PostgreSQL/calibration tests and shared oracle data
- frontend API types/client calls, a new V4 review route, typed components, and
  focused frontend tests
- environment/config examples only where needed to document the default-off
  application gate

Any change to legacy release/materialization code, current-selection state,
catalog/search/match/coverage/compliance/due code, or V3 review mutations is a
scope exception and must be raised as a finding before implementation.

## Known uncertainty

1. The five initial calibration packets correctly remain candidate-only because
   every current applicability evaluator contract is `none`; some also preserve
   unverified incorporated documents or unknown normalization. This is no
   longer an uncertainty or a test loophole: Slice 4 has no release-acceptance
   branch, and a known-value synthetic fixture proves the negative gate.
2. Primary AD source documents are currently ingested as system records without
   a human document-admission actor. The decision must record that fact rather
   than fabricate authorship. Incorporated supporting-document admission is
   assigned to `T081-V4-SCHEMA-SLICE-4D-DOCUMENT-ADMISSION`; dependent nodes
   remain candidate-only here and the UI exposes the blocker. No partial
   admission workflow exists in this slice.
3. The exact gate dependency graph, controlling distinctions, and form coverage
   are normative in `normative-gate-and-form-matrix.md`; implementation may not
   infer additional propagation edges or editable fields.
4. `signature_hash` is intentionally an internal integrity hash. External key
   custody, qualified electronic signatures, and legal non-repudiation are not
   claimed and are out of scope.
5. Slice 5 may not consume a Slice-4 candidate-only decision as release
   authority. It first needs separately reviewed executable evaluator and, when
   applicable, supporting-document admission contracts; then it must create a
   new released-actionable review/signoff under those frozen versions before a
   separate selection CAS/event. Slice 4 exposes no compatibility shim.
