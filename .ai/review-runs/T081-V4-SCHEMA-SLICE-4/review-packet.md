# Review packet: T081-V4-SCHEMA-SLICE-4

Stage: closure
Generated: 2026-09-14T12:38:22+00:00
Base: `4840a0b4bc5d7334ddcf51a80e39c8fa84b7b0c2`
Head: `4840a0b4bc5d7334ddcf51a80e39c8fa84b7b0c2`
Scope fingerprint: `1085a6cdf0249c9ff8b398a100de0ad21df7d013a4b595b9514292b8910475d6`

## Reviewer instructions

Read `.ai/agents/ADVERSARIAL_REVIEWER.md`. Inspect repository files directly.
Treat the manifest as a starting point and report missing consumers or unjustified
scope exclusions as findings.

## Decision packet

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


## Current finding ledger

```json
[
  {
    "id": "T081-V4-S4-B-001",
    "stage": "design",
    "reviewer": "/root/v4_s4_design_adversary",
    "severity": "blocker",
    "status": "closed",
    "invariant": "Release eligibility is never asserted without a separately reviewed executable evaluator contract.",
    "summary": "Release-eligible acceptance and its positive fixture contradict Slice-3A's mandatory evaluator_contract='none'.",
    "evidence": ["Slice-4 decision S4-I09/I12/I24 requires actionable evaluators and a release-positive fixture.", "ORM, migration 0027, and reconstruction constrain conditions, rules, and expressions to evaluator_contract='none'.", "Slice-3A decision reserves executable semantics for separate review."],
    "impact": "Implementation would invent evaluator authority or make the advertised positive path impossible.",
    "requiredClosure": "Bound Slice 4 to candidate-only/rejection or add and separately review a complete evaluator expansion; replace the impossible positive test when bounded.",
    "closureEvidence": ["decision.md objective/S4-I02/I12/I24 and normative matrix sections 1, 3, 6, and 11 remove release acceptance, require candidate-only, and add a known-value negative release-gate proof.", "Independent design closure review 1 closed B-001 against exact packet f414c2f77d209308916eb52d50d7dc5afe9a513dee0f0f3c7096e450e3b402c3."]
  },
  {
    "id": "T081-V4-S4-B-002",
    "stage": "design",
    "reviewer": "/root/v4_s4_design_adversary",
    "severity": "blocker",
    "status": "closed",
    "invariant": "Every node gate, controlling dependency, aggregate classification, and SQL expectation has one exact normative rule.",
    "summary": "The frozen packet promises but does not contain the complete gate/dependency/SQL matrix.",
    "evidence": ["Decision section 1 defers node families, dependency rules, classifications, and reasons to a future spec.", "Existing 3A/3B graphs contain semantically different structural, expression, prerequisite, termination, recurrence, search, and correction relations."],
    "impact": "Python, SQL, reads, and tests could disagree, and caller-supplied expectations could validate themselves.",
    "requiredClosure": "Freeze every family, base gate, evidence purpose, controlling flag, edge direction, cycle rule, aggregate minimum, reason code, SQL derivation, and hand-declared oracle before migration work.",
    "closureEvidence": ["normative-gate-and-form-matrix.md sections 1-7 freeze all 3A/3B families, base gates, controlling status, evidence behavior, edge directions/ordinals, cycles, aggregate minimums, reason codes, and migration-owned SQL derivation.", "Residual revision makes representation_status orthogonal to automation gates, expects no actionable Slice-4 nodes, adds rule-exclusion and all eight identity-mapping-consumption selectors, replaces the invented supersession node edge with exact external dependency snapshots, and requires SQL to derive authorship bidirectionally.", "Independent design closure review 2 closed B-002 against exact packet f3d597efcc16c0fc8671936217760dfebc15e9ce634ccc6337d628fbd0ec2271."]
  },
  {
    "id": "T081-V4-S4-B-003",
    "stage": "design",
    "reviewer": "/root/v4_s4_design_adversary",
    "severity": "blocker",
    "status": "closed",
    "invariant": "Draft, review request, rejection, and acceptance events belong to one defined immutable aggregate with complete CAS transitions.",
    "summary": "No review-case root exists before terminal decision creation, and remediation cannot be represented consistently.",
    "evidence": ["Drafts and requests precede decision versions but no aggregate owner or root event is defined.", "The event sequence mixes state/event names and omits review_requested.", "Acceptance-grade integrity would prevent rejection of malformed inputs."],
    "impact": "Uniqueness, concurrency, re-review, and auditable remediation would be invented during implementation.",
    "requiredClosure": "Define review-case creation, event/state fold, predecessor hashes, request/draft CAS, terminal decision timing, re-review, and a weaker-integrity rejection path.",
    "closureEvidence": ["decision.md S4-I18-I20 and normative matrix section 8 define immutable review cases, exact event/state fold, case/draft/request/terminal CAS, successor cases, and a graph-free auditable rejection branch.", "Residual revision narrows S4-I04-I07 to accepting decisions/signoffs and freezes the closed verified/missing/stale/integrity_error/unsupported_version observation envelope plus two-snapshot rejection hash contract.", "Closure-3 revision separates stable paprnav-ad-v4-review-input-identity-1 bytes/hash from the timestamped audit envelope, makes clients CAS only the stable hash, and requires elapsed-time, substantive-change, and equal-identity rejection tests.", "Independent design closure review 3 closed B-003 and passed the complete design against exact packet 96efc7a7c89e853ce6542c4d6a3a42b96879b3c3a23937fbdbe7ec6e85f145e0."]
  },
  {
    "id": "T081-V4-S4-H-001",
    "stage": "design",
    "reviewer": "/root/v4_s4_design_adversary",
    "severity": "high",
    "status": "closed",
    "invariant": "All V4 writers and gate/rollback operations use one deadlock-safe lock order that protects append-only sets.",
    "summary": "Signing's membership-last order reverses existing candidate and materializer ordering.",
    "evidence": ["Slice-4 decision puts membership after proposal/projections.", "Existing candidate, 3A, 3B, and SQL request guards acquire user/membership before proposal."],
    "impact": "Forced interleavings can deadlock or accept a concurrently appended correction/authorship input.",
    "requiredClosure": "Freeze an interoperable order, advisory/predicate locks, bounded retry behavior, and forced interleaving tests.",
    "closureEvidence": ["decision.md eligibility section freezes the actor-first shared lock order, relationship/case advisory locks, gate prefix, writer exceptions, bounded DDL protocol, and forced-interleaving requirements.", "Independent design closure review 1 closed H-001 against exact packet f414c2f77d209308916eb52d50d7dc5afe9a513dee0f0f3c7096e450e3b402c3."]
  },
  {
    "id": "T081-V4-S4-H-002",
    "stage": "design",
    "reviewer": "/root/v4_s4_design_adversary",
    "severity": "high",
    "status": "closed",
    "invariant": "The parent V3 approval freeze has one explicit activation boundary and owner.",
    "summary": "Slice 4 excludes legacy changes while the parent freezes V3 approvals at V4 deployment.",
    "evidence": ["Parent design sections 8.1/11 require the platform-wide V3 freeze.", "The legacy route and UI retain immediate V3 publication and Slice 4 declares them unchanged."],
    "impact": "The coexistence interval would violate the reviewed parent contract unless explicitly dispositioned.",
    "requiredClosure": "Assign the exact activation point; add a reviewed V3-write gate here or explicitly bind the freeze to a later cutover slice.",
    "closureEvidence": ["decision.md migration section defines V4 deployment as first release/current-selection activation, assigns the V3 write freeze to Slice 5 before that capability, and documents the candidate-only coexistence interval.", "Independent design closure review 1 closed H-002 against exact packet f414c2f77d209308916eb52d50d7dc5afe9a513dee0f0f3c7096e450e3b402c3."]
  },
  {
    "id": "T081-V4-S4-H-003",
    "stage": "design",
    "reviewer": "/root/v4_s4_design_adversary",
    "severity": "high",
    "status": "closed",
    "invariant": "Supporting-document-dependent semantics never become actionable without an exact versioned immutable admission binding.",
    "summary": "Supporting-document admission is conditional and incompatible with unchanged validator-2/3B retention semantics.",
    "evidence": ["Canonical incorporated documents have no issuer/admission/scope fields and retention is forced unknown.", "Existing source delivery is not a supporting-document admission/access-policy service."],
    "impact": "A partial workflow could override canonical unknowns or allow unbound external state to change eligibility.",
    "requiredClosure": "Explicitly defer and keep nodes nonactionable, or specify the full immutable admission/access/authenticity/scope and versioned binding lifecycle.",
    "closureEvidence": ["decision.md persistence/known-uncertainty sections defer admission to named prerequisite T081-V4-SCHEMA-SLICE-4D-DOCUMENT-ADMISSION; normative matrix sections 4/6/11 force dependent nodes candidate-only and define no overlay.", "Independent design closure review 1 closed H-003 against exact packet f414c2f77d209308916eb52d50d7dc5afe9a513dee0f0f3c7096e450e3b402c3."]
  },
  {
    "id": "T081-V4-S4-H-004",
    "stage": "design",
    "reviewer": "/root/v4_s4_design_adversary",
    "severity": "high",
    "status": "closed",
    "invariant": "Each GET verifies one consistent snapshot and distinguishes frozen historical truth from current eligibility.",
    "summary": "Read verification lacks repeatable-read isolation and historical verifier-version semantics.",
    "evidence": ["Decision requires many mutable-head reads without a consistency point.", "Existing 3B reads explicitly use a separate repeatable-read read-only session."],
    "impact": "A response can mix generations or judge old history under today's rules.",
    "requiredClosure": "Require one repeatable-read snapshot, frozen historical contracts, current-head analysis, unsupported-version behavior, and concurrency tests.",
    "closureEvidence": ["decision.md read-path section and normative matrix section 9 require a separate read-only repeatable-read snapshot, frozen historical version dispatch, separate current eligibility, and fail-closed unavailable-version behavior.", "Independent design closure review 1 closed H-004 against exact packet f414c2f77d209308916eb52d50d7dc5afe9a513dee0f0f3c7096e450e3b402c3."]
  },
  {
    "id": "T081-V4-S4-H-005",
    "stage": "design",
    "reviewer": "/root/v4_s4_design_adversary",
    "severity": "high",
    "status": "closed",
    "invariant": "Signing binds a freshly read current membership state and a submit-time CAS token representable by the schema.",
    "summary": "The existing auth helper has no validity interval/version and may reuse identity-mapped ORM state.",
    "evidence": ["OrganizationMembership has role/status but no validity interval or immutable version.", "Existing locking ORM queries do not explicitly refresh cached state.", "Expected candidate/projection hashes do not detect membership changes."],
    "impact": "Expired-membership claims are unimplementable and downgrade/deactivation races may use stale authorization state.",
    "requiredClosure": "Define actual validity/CAS semantics, fresh locked scalar reads, independent SQL checks, historical snapshot rules, and interleaving tests.",
    "closureEvidence": ["decision.md authorization section and normative matrix sections 7/9 define status_only_v1, null interval fields, fresh locked scalar reads, authorization-observation CAS, SQL current checks, and historical semantics.", "Residual revision strengthens the SQL actor/membership locks to FOR UPDATE in shared order through commit and requires a direct-SQL signoff versus deactivation interleaving test.", "Independent design closure review 2 closed H-005 against exact packet f3d597efcc16c0fc8671936217760dfebc15e9ce634ccc6337d628fbd0ec2271."]
  },
  {
    "id": "T081-V4-S4-M-001",
    "stage": "design",
    "reviewer": "/root/v4_s4_design_adversary",
    "severity": "medium",
    "status": "closed",
    "invariant": "Self-review uses a frozen, provenance-grounded human authorship set.",
    "summary": "Current data has no machine-only author, and later deduplicated submissions can change a recomputed set.",
    "evidence": ["All current candidate submissions are platform-admin actions.", "Identical submissions and correction relationships can append after proposal creation."],
    "impact": "An admin submitter could be wrongly exempted or historical independence could change later.",
    "requiredClosure": "Treat current submissions as human, define creator/resubmitter/corrector semantics, freeze contributing event IDs/cutoff, and defer machine-only status.",
    "closureEvidence": ["decision.md authorship section and normative matrix sections 8/9 conservatively classify all current submissions as human and freeze contributing IDs/counts at the review-request cutoff; machine-only provenance is unavailable.", "Independent design closure review 1 closed M-001 against exact packet f414c2f77d209308916eb52d50d7dc5afe9a513dee0f0f3c7096e450e3b402c3."]
  },
  {
    "id": "T081-V4-S4-M-002",
    "stage": "design",
    "reviewer": "/root/v4_s4_design_adversary",
    "severity": "medium",
    "status": "closed",
    "invariant": "Form edits preserve every unedited validator-2 field, presence distinction, order, and reference exactly.",
    "summary": "The UI design has no complete control-to-canonical preservation/edit matrix.",
    "evidence": ["Validator-2 includes additional root families, ordered steps, typed references, and meaningful property absence.", "The packet describes broad controls but not exact coverage."],
    "impact": "A form correction can silently omit, reorder, or stale-bind valid semantics.",
    "requiredClosure": "Freeze editable/read-only mapping, exact untouched preservation, semantic diff, reference validation, and edit-specific tests.",
    "closureEvidence": ["decision.md UI section removes semantic editing; normative matrix section 10 maps every validator-2 root family to exact read-only rendering, ordering/presence preservation, semantic comparison, and fixtures.", "Independent design closure review 1 closed M-002 against exact packet f414c2f77d209308916eb52d50d7dc5afe9a513dee0f0f3c7096e450e3b402c3."]
  },
  {
    "id": "T081-V4-S4-M-003",
    "stage": "design",
    "reviewer": "/root/v4_s4_design_adversary",
    "severity": "medium",
    "status": "closed",
    "invariant": "Every rollout stage and downgrade condition is represented by enforceable capability controls.",
    "summary": "One app flag and one DB gate cannot stage reads, drafts/requests, and terminal signoff separately.",
    "evidence": ["The rollout promises three stages but specifies only two coarse controls.", "The database cannot observe application flags on every replica."],
    "impact": "Activation and downgrade behavior would be invented operationally.",
    "requiredClosure": "Define exact capabilities/defaults, DB reporting, deployment prerequisites, enforceable downgrade checks, and full occupancy.",
    "closureEvidence": ["decision.md feature-gate/rollback sections define three application capabilities, two database write gates, staged activation, operational versus DB-enforceable prerequisites, and complete occupancy refusal.", "Independent design closure review 1 closed M-003 against exact packet f414c2f77d209308916eb52d50d7dc5afe9a513dee0f0f3c7096e450e3b402c3."]
  },
  {
    "id": "T081-V4-S4-IMPL-B-001",
    "stage": "implementation",
    "reviewer": "/root/v4_s4_design_adversary",
    "severity": "blocker",
    "status": "closed",
    "invariant": "Every committed review observation satisfies the same closed branch, digest, and source contract enforced by historical reads.",
    "summary": "PostgreSQL permits fully resealed malformed nonverified observations that Python historical verification rejects.",
    "evidence": ["A fully resealed case/event with evidence state missing and headSetHash not-a-hash committed under every 0029 trigger.", "Python _verify_observation rejects malformed nested digest encoding.", "Probe case arc_9ca456bdccaf44c0a5609157b839a12b on the disposable review database."],
    "impact": "Immutable audit history can commit unreadable and cannot be remediated through normal successor workflow.",
    "requiredClosure": "Enforce the complete observation union and database-verifiable missing/source assertions independently in SQL; add resealed direct-SQL negatives and SQL/Python parity positives for every branch.",
    "closureEvidence": ["SQL now enforces exact state-dependent key unions, nested digest encodings, evidence missing/head assertions, projection row/hash/head ownership, and unconditional same-directive projection ownership independently of Python.", "Fresh 0001-to-0029 database paprnav_s4_review_final passed 70 direct-SQL observation/capacity tests as part of the 77-test Slice-4 PostgreSQL gate; tests include every positive branch and fully resealed malformed counterexamples.", "Independent implementation closure review 1 closed B-001 against exact packet 1a7385408bd7b6ae26378037d1b313c4c2735b82891eeb84492494927a4c6c37."]
  },
  {
    "id": "T081-V4-S4-IMPL-H-001",
    "stage": "implementation",
    "reviewer": "/root/v4_s4_design_adversary",
    "severity": "high",
    "status": "closed",
    "invariant": "Candidate submission and review writers follow one deadlock-safe relationship-before-evidence lock order.",
    "summary": "Candidate submission locks fragments before the relationship graph while review writers acquire the reverse order.",
    "evidence": ["_binding_snapshot takes fragment FOR UPDATE before _validate_candidate_relationship_graph obtains the relationship advisory lock.", "Review writes acquire the relationship advisory lock before fragment locks.", "A rollback-only two-administrator probe reproduced SQLSTATE 40P01."],
    "impact": "Ordinary concurrent candidate and review traffic can deadlock, and candidate-side victims can escape as server errors.",
    "requiredClosure": "Move the relationship lock before candidate fragment acquisition across dedup/resubmission paths, translate candidate transaction conflicts, and add forced interleaving tests for case/request/rejection.",
    "closureEvidence": ["Candidate writes now take content then candidate-relationship-graph advisory locks before any binding/fragment row lock; the relationship lock is also shared by review, 3A, and 3B writers.", "Candidate API translates integrity and retryable PostgreSQL SQLSTATEs to controlled 409 responses while re-raising unknown database errors.", "Six real two-administrator PostgreSQL interleavings passed for new content/reuse against case creation, request, and rejection, asserting content-before-relationship-before-bindings and both commits.", "Implementation closure review 1 kept H-001 open because final-schema inherited submission and applicability-request SQL guards still lock membership before user, reversing the review user-before-membership order; exact packet 1a7385408bd7b6ae26378037d1b313c4c2735b82891eeb84492494927a4c6c37.", "Migration 0029 now replaces both inherited guards with exact final-schema definitions that lock user before membership, drift-checks the definitions with pg_get_functiondef, and restores the exact 0028 definitions on downgrade.", "Fresh PostgreSQL tests prove exact 0028-to-0029-to-0028 function restoration and forced same-actor direct-SQL submission/review and applicability-request/review interleavings in which both transactions commit without SQLSTATE 40P01.", "The final isolated candidate, applicability, obligation, and old-reader regression suites passed 5, 24, 68, and 1 tests respectively on separate empty-to-0029 databases.", "Independent implementation closure review 2 closed H-001 against exact packet d66b273688a22b9ff05b7ab896c66b0688fd2cf30131e13576b10273b7292338 after re-running final-schema assertions and forced direct-SQL interleavings."]
  },
  {
    "id": "T081-V4-S4-IMPL-H-002",
    "stage": "implementation",
    "reviewer": "/root/v4_s4_design_adversary",
    "severity": "high",
    "status": "closed",
    "invariant": "Expected retained-source unavailability becomes a bounded nonverified observation that remains rejectable.",
    "summary": "S3 missing, access, and transport failures escape the review observation path.",
    "evidence": ["_evidence_observation invokes retained-document retrieval but does not catch provider client/transport exceptions.", "A mocked NoSuchKey ClientError escaped the observation helper."],
    "impact": "The rejection workflow can return an unhandled error precisely when inaccessible evidence requires remediation.",
    "requiredClosure": "Normalize expected storage failures without swallowing database/programming failures; test missing objects, access failures, transport failures, and subsequent rejection.",
    "closureEvidence": ["Retained-byte I/O is isolated from structural validation; only allowlisted local/provider credential, missing/access, throttling, timeout, transport, and service-unavailable failures normalize to source_identity_or_evidence_missing.", "Focused tests cover real local missing files, S3 NoSuchKey, AccessDenied, endpoint/transport families, continued request/rejection, and propagation of unexpected programmer, database, and non-allowlisted S3 errors.", "The host API/service gate passed 73 tests and the full host V4 gate passed 496 tests with one skip.", "Independent implementation closure review 1 closed H-002 against exact packet 1a7385408bd7b6ae26378037d1b313c4c2735b82891eeb84492494927a4c6c37."]
  },
  {
    "id": "T081-V4-S4-IMPL-M-001",
    "stage": "implementation",
    "reviewer": "/root/v4_s4_design_adversary",
    "severity": "medium",
    "status": "closed",
    "invariant": "Bounded review APIs also bound verification, predecessor traversal, and retained-source loading work.",
    "summary": "Pagination bounds returned arrays but full history and predecessor verification remains unbounded.",
    "evidence": ["Historical verification loads every event and draft before applying response pagination.", "Every predecessor case and repeated source record can be traversed for each queue entry.", "Draft/case accumulation has no enforceable append limit aligned to pagination reachability."],
    "impact": "Authorized immutable history growth can cause unbounded memory, database, and source-storage work.",
    "requiredClosure": "Define enforceable history/work bounds or bounded verification, batch repeated reads, and add large-history/query-budget tests.",
    "closureEvidence": ["ORM, migration checks, service appends, commit-time recounts, and historical reads enforce 100 cases per proposal, 1000 drafts per case, and 1003 events per case; reads use limit-plus-one fail-closed queries.", "Review cutoff submissions and relationships are bounded at 2000 with 2001 sentinels in Python and SQL; stored source IDs are batch-loaded, proposal observations and retained-document results are request-cached, and queue reads observe each proposal once.", "Focused tests prove exact boundaries/overflow, corrupted over-capacity history, a 10-draft/11-event detail query ceiling, one retained verification per read, and fresh PostgreSQL cutoff parity.", "Implementation closure review 1 kept M-001 open after measuring approximately 1.98 GB of legal 1000-draft blob loading before ORM/driver/parsing overhead; exact packet 1a7385408bd7b6ae26378037d1b313c4c2735b82891eeb84492494927a4c6c37.", "The initial 16 MiB aggregate cap was superseded by phase-aware 16 MiB draft, 28 MiB requested, and 40 MiB terminal caps across all 30 authoritative byte fields; service and SQL check complete pending operations before flush/parse.", "Read verification preflights a combined 64 MiB UTF-8 evidence/page/lifecycle-reason/retained-source budget plus separate 2,000 binding and lifecycle-event budgets, caches repeated proposal/source work, skips reconstruction for oversized projections, and returns controlled nonverified branches for individually oversized proposals.", "Authorship, cutoff, and frozen-source checks now use explicit scalar projections that exclude request/canonical/evidence/text payload columns; cutoff uses one ranked head per owner rather than traversing every event.", "Evidence lifecycle verification selects only its hash inputs through limit-plus-one, counts lifecycle rows and UTF-8 reason bytes in the preflight, and caches each distinct fragment chain.", "Implementation closure review 3 verified those targeted fixes but kept M-001 open because obligation reconstruction still loads every valid materialization request and its byte payloads with no count/byte preflight; exact packet 684ca24c3259a2de7df38e9e22c71cf3d01ee04e2f98876f22b2617ba97288af.", "Review observation now selects projection metadata only, then scalar-counts accumulated applicability/obligation materialization requests and projection events and sums their canonical payload bytes before loading a projection or invoking reconstruction.", "Per-projection and queue-wide reconstruction inputs are limited to 2,000 request/event rows and 64 MiB of canonical audit bytes; overflow returns stable projection_integrity for an individual proposal or review_work_limit for a cumulative page.", "Implementation closure review 4 kept M-001 open because obligation reconstruction can consume its exact applicability parent even when that parent's count or byte preflight is individually over budget and excluded from cumulative accounting; exact packet e4b4a1e0d675bfc2b57e5fc7c978442eb87a1627ebdcdcc0018d52cc7c64526a.", "Obligation observation now inherits the exact applicability parent's individual preflight failure before any obligation reconstruction; the same prepared dependency state is used by detail and queue observation paths.", "Fresh database paprnav_s4_closure7 passed populated real-projection obligation-over-count, applicability-parent-over-count, and applicability-parent-over-byte cases; all return controlled projection_integrity and assert that parent request payload columns are never selected after preflight.", "The final focused host subset passed 93 tests, the full host V4 gate passed 532 tests with one skip, and the fresh 0001-to-0029 PostgreSQL gate passed 86 tests.", "Independent implementation closure review 5 reproduced populated parent-count and parent-byte overflow for both detail and queue readers, observed matching input identities and integrity_error for both parent and child, and instrumented zero projection request/event payload-byte selections; exact packet b531efdaba8866893e8c0dcdb4d60f19922c87bfab95371892e455551ba9647a."]
  },
  {
    "id": "T081-V4-S4-IMPL-H-003",
    "stage": "implementation",
    "reviewer": "/root/v4_s4_design_adversary",
    "severity": "high",
    "status": "closed",
    "invariant": "Every legally admitted draft sequence preserves enough immutable capacity to request and reject the case, after which a successor can be created.",
    "summary": "The shared 16 MiB cap has no phase-aware terminal reserve, allowing legal drafts to permanently strand an open case.",
    "evidence": ["Independent PostgreSQL reproduction committed nine legal service drafts and reached 16,777,214 authoritative bytes with all constraints and triggers enabled.", "The same case could not request review because of review_history_limit and could not create a successor because of review_case_open.", "Immutable drafts cannot be deleted or shortened."],
    "impact": "An authorized ordinary-write sequence can permanently prevent rejection and remediation for the candidate.",
    "requiredClosure": "Enforce phase-aware byte reservations in Python and SQL for request, rejection, signoff, and companion events; prove boundary liveness and successor creation with fully sealed PostgreSQL tests.",
    "closureEvidence": ["Python and commit-time SQL now apply 16 MiB draft, 28 MiB requested, and 40 MiB terminal ceilings; the 12 MiB request-to-terminal and 22 MiB draft-to-terminal worst cases follow directly from the 1 MiB CHECK on every remaining authoritative byte column, with 2 MiB explicit cushions.", "The coarse PostgreSQL liveness test passed, but implementation closure review 3 reproduced the exact prior two-byte remainder and found request owner partial flushing is rechecked under the old stored phase before the pending phase-changing event; exact packet 684ca24c3259a2de7df38e9e22c71cf3d01ee04e2f98876f22b2617ba97288af.", "Partial-flush checks now promote the effective validation phase from pending phase-changing events before comparing already-flushed bytes, while no-pending reads still reject committed history above its stored phase ceiling.", "The PostgreSQL liveness regression writes maximal annotations, measures a final legal append without flushing, fills the draft phase to within 1 KiB, and then commits request, rejection, and successor under normal deferred validators.", "Independent implementation closure review 4 replayed the exact two-byte-remainder case: request, rejection, and successor committed, while a separate stored-phase corruption probe still failed closed; exact packet e4b4a1e0d675bfc2b57e5fc7c978442eb87a1627ebdcdcc0018d52cc7c64526a."]
  },
  {
    "id": "T081-V4-S4-IMPL-M-002",
    "stage": "implementation",
    "reviewer": "/root/v4_s4_design_adversary",
    "severity": "medium",
    "status": "closed",
    "invariant": "Migration closure evidence is automated, reproducible, and attributed to the gate that actually proves it.",
    "summary": "Exact inherited-function downgrade restoration and independent refusal by both reviewer gates are not durably tested despite the verification claim.",
    "evidence": ["The metadata test asserts final lock order but does not compare complete 0028 and downgraded function definitions.", "The rollback module verifies only the draft gate individually, not the decision gate.", "The exact restoration comparison was an ad hoc probe outside the committed test modules."],
    "impact": "The migration appears symmetric, but the closure evidence overstates reproducible regression coverage.",
    "requiredClosure": "Add isolated 0028-to-0029-to-0028 complete-definition and helper-removal tests, test both reviewer gates independently, and correct the verification document.",
    "closureEvidence": ["The isolated rollback test now captures both complete 0028 function definitions, upgrades to 0029, downgrades again, compares exact definition equality, and verifies paprnav_v4_review_case_authoritative_bytes(text) is absent after downgrade.", "The draft and decision reviewer gates are parametrized and each independently proves downgrade refusal without schema loss.", "implementation-verification.md now attributes definition restoration/helper removal only to the four-test rollback gate, which passed on fresh database paprnav_s4_rollout4.", "Independent implementation closure review 3 ran all four tests on fresh paprnav_s4_reviewer_rollout5 and closed M-002 against exact packet 684ca24c3259a2de7df38e9e22c71cf3d01ee04e2f98876f22b2617ba97288af."]
  }
]

```

## Hash-bound review inputs

### `.ai/review-runs/T081-V4-SCHEMA-SLICE-4/decision.md`

size=39002; sha256=2c5a020540be5a996f0eb52edc6ea7f5cc1d8b359897d077cc9d297813de7971

```text
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

```
### `.ai/review-runs/T081-V4-SCHEMA-SLICE-4/findings.json`

size=30763; sha256=7ac4836cd873629202bf52eddb3cef8bc2c0865db806f341aef2e1787acf77f5

```text
[
  {
    "id": "T081-V4-S4-B-001",
    "stage": "design",
    "reviewer": "/root/v4_s4_design_adversary",
    "severity": "blocker",
    "status": "closed",
    "invariant": "Release eligibility is never asserted without a separately reviewed executable evaluator contract.",
    "summary": "Release-eligible acceptance and its positive fixture contradict Slice-3A's mandatory evaluator_contract='none'.",
    "evidence": ["Slice-4 decision S4-I09/I12/I24 requires actionable evaluators and a release-positive fixture.", "ORM, migration 0027, and reconstruction constrain conditions, rules, and expressions to evaluator_contract='none'.", "Slice-3A decision reserves executable semantics for separate review."],
    "impact": "Implementation would invent evaluator authority or make the advertised positive path impossible.",
    "requiredClosure": "Bound Slice 4 to candidate-only/rejection or add and separately review a complete evaluator expansion; replace the impossible positive test when bounded.",
    "closureEvidence": ["decision.md objective/S4-I02/I12/I24 and normative matrix sections 1, 3, 6, and 11 remove release acceptance, require candidate-only, and add a known-value negative release-gate proof.", "Independent design closure review 1 closed B-001 against exact packet f414c2f77d209308916eb52d50d7dc5afe9a513dee0f0f3c7096e450e3b402c3."]
  },
  {
    "id": "T081-V4-S4-B-002",
    "stage": "design",
    "reviewer": "/root/v4_s4_design_adversary",
    "severity": "blocker",
    "status": "closed",
    "invariant": "Every node gate, controlling dependency, aggregate classification, and SQL expectation has one exact normative rule.",
    "summary": "The frozen packet promises but does not contain the complete gate/dependency/SQL matrix.",
    "evidence": ["Decision section 1 defers node families, dependency rules, classifications, and reasons to a future spec.", "Existing 3A/3B graphs contain semantically different structural, expression, prerequisite, termination, recurrence, search, and correction relations."],
    "impact": "Python, SQL, reads, and tests could disagree, and caller-supplied expectations could validate themselves.",
    "requiredClosure": "Freeze every family, base gate, evidence purpose, controlling flag, edge direction, cycle rule, aggregate minimum, reason code, SQL derivation, and hand-declared oracle before migration work.",
    "closureEvidence": ["normative-gate-and-form-matrix.md sections 1-7 freeze all 3A/3B families, base gates, controlling status, evidence behavior, edge directions/ordinals, cycles, aggregate minimums, reason codes, and migration-owned SQL derivation.", "Residual revision makes representation_status orthogonal to automation gates, expects no actionable Slice-4 nodes, adds rule-exclusion and all eight identity-mapping-consumption selectors, replaces the invented supersession node edge with exact external dependency snapshots, and requires SQL to derive authorship bidirectionally.", "Independent design closure review 2 closed B-002 against exact packet f3d597efcc16c0fc8671936217760dfebc15e9ce634ccc6337d628fbd0ec2271."]
  },
  {
    "id": "T081-V4-S4-B-003",
    "stage": "design",
    "reviewer": "/root/v4_s4_design_adversary",
    "severity": "blocker",
    "status": "closed",
    "invariant": "Draft, review request, rejection, and acceptance events belong to one defined immutable aggregate with complete CAS transitions.",
    "summary": "No review-case root exists before terminal decision creation, and remediation cannot be represented consistently.",
    "evidence": ["Drafts and requests precede decision versions but no aggregate owner or root event is defined.", "The event sequence mixes state/event names and omits review_requested.", "Acceptance-grade integrity would prevent rejection of malformed inputs."],
    "impact": "Uniqueness, concurrency, re-review, and auditable remediation would be invented during implementation.",
    "requiredClosure": "Define review-case creation, event/state fold, predecessor hashes, request/draft CAS, terminal decision timing, re-review, and a weaker-integrity rejection path.",
    "closureEvidence": ["decision.md S4-I18-I20 and normative matrix section 8 define immutable review cases, exact event/state fold, case/draft/request/terminal CAS, successor cases, and a graph-free auditable rejection branch.", "Residual revision narrows S4-I04-I07 to accepting decisions/signoffs and freezes the closed verified/missing/stale/integrity_error/unsupported_version observation envelope plus two-snapshot rejection hash contract.", "Closure-3 revision separates stable paprnav-ad-v4-review-input-identity-1 bytes/hash from the timestamped audit envelope, makes clients CAS only the stable hash, and requires elapsed-time, substantive-change, and equal-identity rejection tests.", "Independent design closure review 3 closed B-003 and passed the complete design against exact packet 96efc7a7c89e853ce6542c4d6a3a42b96879b3c3a23937fbdbe7ec6e85f145e0."]
  },
  {
    "id": "T081-V4-S4-H-001",
    "stage": "design",
    "reviewer": "/root/v4_s4_design_adversary",
    "severity": "high",
    "status": "closed",
    "invariant": "All V4 writers and gate/rollback operations use one deadlock-safe lock order that protects append-only sets.",
    "summary": "Signing's membership-last order reverses existing candidate and materializer ordering.",
    "evidence": ["Slice-4 decision puts membership after proposal/projections.", "Existing candidate, 3A, 3B, and SQL request guards acquire user/membership before proposal."],
    "impact": "Forced interleavings can deadlock or accept a concurrently appended correction/authorship input.",
    "requiredClosure": "Freeze an interoperable order, advisory/predicate locks, bounded retry behavior, and forced interleaving tests.",
    "closureEvidence": ["decision.md eligibility section freezes the actor-first shared lock order, relationship/case advisory locks, gate prefix, writer exceptions, bounded DDL protocol, and forced-interleaving requirements.", "Independent design closure review 1 closed H-001 against exact packet f414c2f77d209308916eb52d50d7dc5afe9a513dee0f0f3c7096e450e3b402c3."]
  },
  {
    "id": "T081-V4-S4-H-002",
    "stage": "design",
    "reviewer": "/root/v4_s4_design_adversary",
    "severity": "high",
    "status": "closed",
    "invariant": "The parent V3 approval freeze has one explicit activation boundary and owner.",
    "summary": "Slice 4 excludes legacy changes while the parent freezes V3 approvals at V4 deployment.",
    "evidence": ["Parent design sections 8.1/11 require the platform-wide V3 freeze.", "The legacy route and UI retain immediate V3 publication and Slice 4 declares them unchanged."],
    "impact": "The coexistence interval would violate the reviewed parent contract unless explicitly dispositioned.",
    "requiredClosure": "Assign the exact activation point; add a reviewed V3-write gate here or explicitly bind the freeze to a later cutover slice.",
    "closureEvidence": ["decision.md migration section defines V4 deployment as first release/current-selection activation, assigns the V3 write freeze to Slice 5 before that capability, and documents the candidate-only coexistence interval.", "Independent design closure review 1 closed H-002 against exact packet f414c2f77d209308916eb52d50d7dc5afe9a513dee0f0f3c7096e450e3b402c3."]
  },
  {
    "id": "T081-V4-S4-H-003",
    "stage": "design",
    "reviewer": "/root/v4_s4_design_adversary",
    "severity": "high",
    "status": "closed",
    "invariant": "Supporting-document-dependent semantics never become actionable without an exact versioned immutable admission binding.",
    "summary": "Supporting-document admission is conditional and incompatible with unchanged validator-2/3B retention semantics.",
    "evidence": ["Canonical incorporated documents have no issuer/admission/scope fields and retention is forced unknown.", "Existing source delivery is not a supporting-document admission/access-policy service."],
    "impact": "A partial workflow could override canonical unknowns or allow unbound external state to change eligibility.",
    "requiredClosure": "Explicitly defer and keep nodes nonactionable, or specify the full immutable admission/access/authenticity/scope and versioned binding lifecycle.",
    "closureEvidence": ["decision.md persistence/known-uncertainty sections defer admission to named prerequisite T081-V4-SCHEMA-SLICE-4D-DOCUMENT-ADMISSION; normative matrix sections 4/6/11 force dependent nodes candidate-only and define no overlay.", "Independent design closure review 1 closed H-003 against exact packet f414c2f77d209308916eb52d50d7dc5afe9a513dee0f0f3c7096e450e3b402c3."]
  },
  {
    "id": "T081-V4-S4-H-004",
    "stage": "design",
    "reviewer": "/root/v4_s4_design_adversary",
    "severity": "high",
    "status": "closed",
    "invariant": "Each GET verifies one consistent snapshot and distinguishes frozen historical truth from current eligibility.",
    "summary": "Read verification lacks repeatable-read isolation and historical verifier-version semantics.",
    "evidence": ["Decision requires many mutable-head reads without a consistency point.", "Existing 3B reads explicitly use a separate repeatable-read read-only session."],
    "impact": "A response can mix generations or judge old history under today's rules.",
    "requiredClosure": "Require one repeatable-read snapshot, frozen historical contracts, current-head analysis, unsupported-version behavior, and concurrency tests.",
    "closureEvidence": ["decision.md read-path section and normative matrix section 9 require a separate read-only repeatable-read snapshot, frozen historical version dispatch, separate current eligibility, and fail-closed unavailable-version behavior.", "Independent design closure review 1 closed H-004 against exact packet f414c2f77d209308916eb52d50d7dc5afe9a513dee0f0f3c7096e450e3b402c3."]
  },
  {
    "id": "T081-V4-S4-H-005",
    "stage": "design",
    "reviewer": "/root/v4_s4_design_adversary",
    "severity": "high",
    "status": "closed",
    "invariant": "Signing binds a freshly read current membership state and a submit-time CAS token representable by the schema.",
    "summary": "The existing auth helper has no validity interval/version and may reuse identity-mapped ORM state.",
    "evidence": ["OrganizationMembership has role/status but no validity interval or immutable version.", "Existing locking ORM queries do not explicitly refresh cached state.", "Expected candidate/projection hashes do not detect membership changes."],
    "impact": "Expired-membership claims are unimplementable and downgrade/deactivation races may use stale authorization state.",
    "requiredClosure": "Define actual validity/CAS semantics, fresh locked scalar reads, independent SQL checks, historical snapshot rules, and interleaving tests.",
    "closureEvidence": ["decision.md authorization section and normative matrix sections 7/9 define status_only_v1, null interval fields, fresh locked scalar reads, authorization-observation CAS, SQL current checks, and historical semantics.", "Residual revision strengthens the SQL actor/membership locks to FOR UPDATE in shared order through commit and requires a direct-SQL signoff versus deactivation interleaving test.", "Independent design closure review 2 closed H-005 against exact packet f3d597efcc16c0fc8671936217760dfebc15e9ce634ccc6337d628fbd0ec2271."]
  },
  {
    "id": "T081-V4-S4-M-001",
    "stage": "design",
    "reviewer": "/root/v4_s4_design_adversary",
    "severity": "medium",
    "status": "closed",
    "invariant": "Self-review uses a frozen, provenance-grounded human authorship set.",
    "summary": "Current data has no machine-only author, and later deduplicated submissions can change a recomputed set.",
    "evidence": ["All current candidate submissions are platform-admin actions.", "Identical submissions and correction relationships can append after proposal creation."],
    "impact": "An admin submitter could be wrongly exempted or historical independence could change later.",
    "requiredClosure": "Treat current submissions as human, define creator/resubmitter/corrector semantics, freeze contributing event IDs/cutoff, and defer machine-only status.",
    "closureEvidence": ["decision.md authorship section and normative matrix sections 8/9 conservatively classify all current submissions as human and freeze contributing IDs/counts at the review-request cutoff; machine-only provenance is unavailable.", "Independent design closure review 1 closed M-001 against exact packet f414c2f77d209308916eb52d50d7dc5afe9a513dee0f0f3c7096e450e3b402c3."]
  },
  {
    "id": "T081-V4-S4-M-002",
    "stage": "design",
    "reviewer": "/root/v4_s4_design_adversary",
    "severity": "medium",
    "status": "closed",
    "invariant": "Form edits preserve every unedited validator-2 field, presence distinction, order, and reference exactly.",
    "summary": "The UI design has no complete control-to-canonical preservation/edit matrix.",
    "evidence": ["Validator-2 includes additional root families, ordered steps, typed references, and meaningful property absence.", "The packet describes broad controls but not exact coverage."],
    "impact": "A form correction can silently omit, reorder, or stale-bind valid semantics.",
    "requiredClosure": "Freeze editable/read-only mapping, exact untouched preservation, semantic diff, reference validation, and edit-specific tests.",
    "closureEvidence": ["decision.md UI section removes semantic editing; normative matrix section 10 maps every validator-2 root family to exact read-only rendering, ordering/presence preservation, semantic comparison, and fixtures.", "Independent design closure review 1 closed M-002 against exact packet f414c2f77d209308916eb52d50d7dc5afe9a513dee0f0f3c7096e450e3b402c3."]
  },
  {
    "id": "T081-V4-S4-M-003",
    "stage": "design",
    "reviewer": "/root/v4_s4_design_adversary",
    "severity": "medium",
    "status": "closed",
    "invariant": "Every rollout stage and downgrade condition is represented by enforceable capability controls.",
    "summary": "One app flag and one DB gate cannot stage reads, drafts/requests, and terminal signoff separately.",
    "evidence": ["The rollout promises three stages but specifies only two coarse controls.", "The database cannot observe application flags on every replica."],
    "impact": "Activation and downgrade behavior would be invented operationally.",
    "requiredClosure": "Define exact capabilities/defaults, DB reporting, deployment prerequisites, enforceable downgrade checks, and full occupancy.",
    "closureEvidence": ["decision.md feature-gate/rollback sections define three application capabilities, two database write gates, staged activation, operational versus DB-enforceable prerequisites, and complete occupancy refusal.", "Independent design closure review 1 closed M-003 against exact packet f414c2f77d209308916eb52d50d7dc5afe9a513dee0f0f3c7096e450e3b402c3."]
  },
  {
    "id": "T081-V4-S4-IMPL-B-001",
    "stage": "implementation",
    "reviewer": "/root/v4_s4_design_adversary",
    "severity": "blocker",
    "status": "closed",
    "invariant": "Every committed review observation satisfies the same closed branch, digest, and source contract enforced by historical reads.",
    "summary": "PostgreSQL permits fully resealed malformed nonverified observations that Python historical verification rejects.",
    "evidence": ["A fully resealed case/event with evidence state missing and headSetHash not-a-hash committed under every 0029 trigger.", "Python _verify_observation rejects malformed nested digest encoding.", "Probe case arc_9ca456bdccaf44c0a5609157b839a12b on the disposable review database."],
    "impact": "Immutable audit history can commit unreadable and cannot be remediated through normal successor workflow.",
    "requiredClosure": "Enforce the complete observation union and database-verifiable missing/source assertions independently in SQL; add resealed direct-SQL negatives and SQL/Python parity positives for every branch.",
    "closureEvidence": ["SQL now enforces exact state-dependent key unions, nested digest encodings, evidence missing/head assertions, projection row/hash/head ownership, and unconditional same-directive projection ownership independently of Python.", "Fresh 0001-to-0029 database paprnav_s4_review_final passed 70 direct-SQL observation/capacity tests as part of the 77-test Slice-4 PostgreSQL gate; tests include every positive branch and fully resealed malformed counterexamples.", "Independent implementation closure review 1 closed B-001 against exact packet 1a7385408bd7b6ae26378037d1b313c4c2735b82891eeb84492494927a4c6c37."]
  },
  {
    "id": "T081-V4-S4-IMPL-H-001",
    "stage": "implementation",
    "reviewer": "/root/v4_s4_design_adversary",
    "severity": "high",
    "status": "closed",
    "invariant": "Candidate submission and review writers follow one deadlock-safe relationship-before-evidence lock order.",
    "summary": "Candidate submission locks fragments before the relationship graph while review writers acquire the reverse order.",
    "evidence": ["_binding_snapshot takes fragment FOR UPDATE before _validate_candidate_relationship_graph obtains the relationship advisory lock.", "Review writes acquire the relationship advisory lock before fragment locks.", "A rollback-only two-administrator probe reproduced SQLSTATE 40P01."],
    "impact": "Ordinary concurrent candidate and review traffic can deadlock, and candidate-side victims can escape as server errors.",
    "requiredClosure": "Move the relationship lock before candidate fragment acquisition across dedup/resubmission paths, translate candidate transaction conflicts, and add forced interleaving tests for case/request/rejection.",
    "closureEvidence": ["Candidate writes now take content then candidate-relationship-graph advisory locks before any binding/fragment row lock; the relationship lock is also shared by review, 3A, and 3B writers.", "Candidate API translates integrity and retryable PostgreSQL SQLSTATEs to controlled 409 responses while re-raising unknown database errors.", "Six real two-administrator PostgreSQL interleavings passed for new content/reuse against case creation, request, and rejection, asserting content-before-relationship-before-bindings and both commits.", "Implementation closure review 1 kept H-001 open because final-schema inherited submission and applicability-request SQL guards still lock membership before user, reversing the review user-before-membership order; exact packet 1a7385408bd7b6ae26378037d1b313c4c2735b82891eeb84492494927a4c6c37.", "Migration 0029 now replaces both inherited guards with exact final-schema definitions that lock user before membership, drift-checks the definitions with pg_get_functiondef, and restores the exact 0028 definitions on downgrade.", "Fresh PostgreSQL tests prove exact 0028-to-0029-to-0028 function restoration and forced same-actor direct-SQL submission/review and applicability-request/review interleavings in which both transactions commit without SQLSTATE 40P01.", "The final isolated candidate, applicability, obligation, and old-reader regression suites passed 5, 24, 68, and 1 tests respectively on separate empty-to-0029 databases.", "Independent implementation closure review 2 closed H-001 against exact packet d66b273688a22b9ff05b7ab896c66b0688fd2cf30131e13576b10273b7292338 after re-running final-schema assertions and forced direct-SQL interleavings."]
  },
  {
    "id": "T081-V4-S4-IMPL-H-002",
    "stage": "implementation",
    "reviewer": "/root/v4_s4_design_adversary",
    "severity": "high",
    "status": "closed",
    "invariant": "Expected retained-source unavailability becomes a bounded nonverified observation that remains rejectable.",
    "summary": "S3 missing, access, and transport failures escape the review observation path.",
    "evidence": ["_evidence_observation invokes retained-document retrieval but does not catch provider client/transport exceptions.", "A mocked NoSuchKey ClientError escaped the observation helper."],
    "impact": "The rejection workflow can return an unhandled error precisely when inaccessible evidence requires remediation.",
    "requiredClosure": "Normalize expected storage failures without swallowing database/programming failures; test missing objects, access failures, transport failures, and subsequent rejection.",
    "closureEvidence": ["Retained-byte I/O is isolated from structural validation; only allowlisted local/provider credential, missing/access, throttling, timeout, transport, and service-unavailable failures normalize to source_identity_or_evidence_missing.", "Focused tests cover real local missing files, S3 NoSuchKey, AccessDenied, endpoint/transport families, continued request/rejection, and propagation of unexpected programmer, database, and non-allowlisted S3 errors.", "The host API/service gate passed 73 tests and the full host V4 gate passed 496 tests with one skip.", "Independent implementation closure review 1 closed H-002 against exact packet 1a7385408bd7b6ae26378037d1b313c4c2735b82891eeb84492494927a4c6c37."]
  },
  {
    "id": "T081-V4-S4-IMPL-M-001",
    "stage": "implementation",
    "reviewer": "/root/v4_s4_design_adversary",
    "severity": "medium",
    "status": "closed",
    "invariant": "Bounded review APIs also bound verification, predecessor traversal, and retained-source loading work.",
    "summary": "Pagination bounds returned arrays but full history and predecessor verification remains unbounded.",
    "evidence": ["Historical verification loads every event and draft before applying response pagination.", "Every predecessor case and repeated source record can be traversed for each queue entry.", "Draft/case accumulation has no enforceable append limit aligned to pagination reachability."],
    "impact": "Authorized immutable history growth can cause unbounded memory, database, and source-storage work.",
    "requiredClosure": "Define enforceable history/work bounds or bounded verification, batch repeated reads, and add large-history/query-budget tests.",
    "closureEvidence": ["ORM, migration checks, service appends, commit-time recounts, and historical reads enforce 100 cases per proposal, 1000 drafts per case, and 1003 events per case; reads use limit-plus-one fail-closed queries.", "Review cutoff submissions and relationships are bounded at 2000 with 2001 sentinels in Python and SQL; stored source IDs are batch-loaded, proposal observations and retained-document results are request-cached, and queue reads observe each proposal once.", "Focused tests prove exact boundaries/overflow, corrupted over-capacity history, a 10-draft/11-event detail query ceiling, one retained verification per read, and fresh PostgreSQL cutoff parity.", "Implementation closure review 1 kept M-001 open after measuring approximately 1.98 GB of legal 1000-draft blob loading before ORM/driver/parsing overhead; exact packet 1a7385408bd7b6ae26378037d1b313c4c2735b82891eeb84492494927a4c6c37.", "The initial 16 MiB aggregate cap was superseded by phase-aware 16 MiB draft, 28 MiB requested, and 40 MiB terminal caps across all 30 authoritative byte fields; service and SQL check complete pending operations before flush/parse.", "Read verification preflights a combined 64 MiB UTF-8 evidence/page/lifecycle-reason/retained-source budget plus separate 2,000 binding and lifecycle-event budgets, caches repeated proposal/source work, skips reconstruction for oversized projections, and returns controlled nonverified branches for individually oversized proposals.", "Authorship, cutoff, and frozen-source checks now use explicit scalar projections that exclude request/canonical/evidence/text payload columns; cutoff uses one ranked head per owner rather than traversing every event.", "Evidence lifecycle verification selects only its hash inputs through limit-plus-one, counts lifecycle rows and UTF-8 reason bytes in the preflight, and caches each distinct fragment chain.", "Implementation closure review 3 verified those targeted fixes but kept M-001 open because obligation reconstruction still loads every valid materialization request and its byte payloads with no count/byte preflight; exact packet 684ca24c3259a2de7df38e9e22c71cf3d01ee04e2f98876f22b2617ba97288af.", "Review observation now selects projection metadata only, then scalar-counts accumulated applicability/obligation materialization requests and projection events and sums their canonical payload bytes before loading a projection or invoking reconstruction.", "Per-projection and queue-wide reconstruction inputs are limited to 2,000 request/event rows and 64 MiB of canonical audit bytes; overflow returns stable projection_integrity for an individual proposal or review_work_limit for a cumulative page.", "Implementation closure review 4 kept M-001 open because obligation reconstruction can consume its exact applicability parent even when that parent's count or byte preflight is individually over budget and excluded from cumulative accounting; exact packet e4b4a1e0d675bfc2b57e5fc7c978442eb87a1627ebdcdcc0018d52cc7c64526a.", "Obligation observation now inherits the exact applicability parent's individual preflight failure before any obligation reconstruction; the same prepared dependency state is used by detail and queue observation paths.", "Fresh database paprnav_s4_closure7 passed populated real-projection obligation-over-count, applicability-parent-over-count, and applicability-parent-over-byte cases; all return controlled projection_integrity and assert that parent request payload columns are never selected after preflight.", "The final focused host subset passed 93 tests, the full host V4 gate passed 532 tests with one skip, and the fresh 0001-to-0029 PostgreSQL gate passed 86 tests.", "Independent implementation closure review 5 reproduced populated parent-count and parent-byte overflow for both detail and queue readers, observed matching input identities and integrity_error for both parent and child, and instrumented zero projection request/event payload-byte selections; exact packet b531efdaba8866893e8c0dcdb4d60f19922c87bfab95371892e455551ba9647a."]
  },
  {
    "id": "T081-V4-S4-IMPL-H-003",
    "stage": "implementation",
    "reviewer": "/root/v4_s4_design_adversary",
    "severity": "high",
    "status": "closed",
    "invariant": "Every legally admitted draft sequence preserves enough immutable capacity to request and reject the case, after which a successor can be created.",
    "summary": "The shared 16 MiB cap has no phase-aware terminal reserve, allowing legal drafts to permanently strand an open case.",
    "evidence": ["Independent PostgreSQL reproduction committed nine legal service drafts and reached 16,777,214 authoritative bytes with all constraints and triggers enabled.", "The same case could not request review because of review_history_limit and could not create a successor because of review_case_open.", "Immutable drafts cannot be deleted or shortened."],
    "impact": "An authorized ordinary-write sequence can permanently prevent rejection and remediation for the candidate.",
    "requiredClosure": "Enforce phase-aware byte reservations in Python and SQL for request, rejection, signoff, and companion events; prove boundary liveness and successor creation with fully sealed PostgreSQL tests.",
    "closureEvidence": ["Python and commit-time SQL now apply 16 MiB draft, 28 MiB requested, and 40 MiB terminal ceilings; the 12 MiB request-to-terminal and 22 MiB draft-to-terminal worst cases follow directly from the 1 MiB CHECK on every remaining authoritative byte column, with 2 MiB explicit cushions.", "The coarse PostgreSQL liveness test passed, but implementation closure review 3 reproduced the exact prior two-byte remainder and found request owner partial flushing is rechecked under the old stored phase before the pending phase-changing event; exact packet 684ca24c3259a2de7df38e9e22c71cf3d01ee04e2f98876f22b2617ba97288af.", "Partial-flush checks now promote the effective validation phase from pending phase-changing events before comparing already-flushed bytes, while no-pending reads still reject committed history above its stored phase ceiling.", "The PostgreSQL liveness regression writes maximal annotations, measures a final legal append without flushing, fills the draft phase to within 1 KiB, and then commits request, rejection, and successor under normal deferred validators.", "Independent implementation closure review 4 replayed the exact two-byte-remainder case: request, rejection, and successor committed, while a separate stored-phase corruption probe still failed closed; exact packet e4b4a1e0d675bfc2b57e5fc7c978442eb87a1627ebdcdcc0018d52cc7c64526a."]
  },
  {
    "id": "T081-V4-S4-IMPL-M-002",
    "stage": "implementation",
    "reviewer": "/root/v4_s4_design_adversary",
    "severity": "medium",
    "status": "closed",
    "invariant": "Migration closure evidence is automated, reproducible, and attributed to the gate that actually proves it.",
    "summary": "Exact inherited-function downgrade restoration and independent refusal by both reviewer gates are not durably tested despite the verification claim.",
    "evidence": ["The metadata test asserts final lock order but does not compare complete 0028 and downgraded function definitions.", "The rollback module verifies only the draft gate individually, not the decision gate.", "The exact restoration comparison was an ad hoc probe outside the committed test modules."],
    "impact": "The migration appears symmetric, but the closure evidence overstates reproducible regression coverage.",
    "requiredClosure": "Add isolated 0028-to-0029-to-0028 complete-definition and helper-removal tests, test both reviewer gates independently, and correct the verification document.",
    "closureEvidence": ["The isolated rollback test now captures both complete 0028 function definitions, upgrades to 0029, downgrades again, compares exact definition equality, and verifies paprnav_v4_review_case_authoritative_bytes(text) is absent after downgrade.", "The draft and decision reviewer gates are parametrized and each independently proves downgrade refusal without schema loss.", "implementation-verification.md now attributes definition restoration/helper removal only to the four-test rollback gate, which passed on fresh database paprnav_s4_rollout4.", "Independent implementation closure review 3 ran all four tests on fresh paprnav_s4_reviewer_rollout5 and closed M-002 against exact packet 684ca24c3259a2de7df38e9e22c71cf3d01ee04e2f98876f22b2617ba97288af."]
  }
]

```
### `.ai/review-runs/T081-V4-SCHEMA-SLICE-4/closure.md`

size=8444; sha256=14b8e50fe63d9802f58eb7e164673f69f4e26b673c1829a355ebb764ade281fe

```text
# Closure report: T081-V4-SCHEMA-SLICE-4

## Outcome

**Ready for independent closure review.** The implemented Slice-4 vertical is
the frozen rejection-only workflow: immutable review cases and annotation
drafts, frozen review requests, and graph-free rejecting signoffs. The design
and implementation review stages passed with all 17 findings closed. Nothing is
staged or committed.

This outcome does not claim the complete feature set originally explored in the
decision packet. Candidate-only acceptance and every release/publication path
remain intentionally unavailable and require separately reviewed later slices.

## Model assignments

This review run began before `.ai/MODEL_ROUTING.md` was adopted. Completed
reports remain immutable; the assignments below record the metadata available
to the coordinator without retroactively inventing missing runtime fields.

| Phase and role | Runtime identity | Actual runtime metadata | Routing evidence |
| --- | --- | --- | --- |
| Slice-4 design, implementation, and first closure adversary | `/root/v4_s4_design_adversary` | model not exposed by runtime; effort not exposed | The coordinator checkpoint described an Astra assignment for schema, authorization, invariant, adversarial, and closure work, but the reviewer later confirmed that neither actual model nor effort was exposed; no exact actual-model claim is made. |
| Slice-4 builder/coordinator and remediation | `/root` | model not exposed by runtime; effort not exposed | Builder role and runtime identity are recorded throughout the run; no exact model is inferred. |
| Model-policy builder/coordinator | `/root` | model not exposed by runtime; effort not exposed | Localized policy edit; active runtime did not expose model metadata. |
| First model-policy verifier | `/root/model_routing_policy_verifier` | model not exposed by runtime; effort not exposed | Requested `gpt-5.6-terra` medium for mechanical policy verification; the reviewer closed most requirements and identified missing durable closure evidence. |
| Escalated model-policy verifier | `/root/model_routing_policy_closure` | model not exposed by runtime; effort not exposed | Requested `gpt-5.6-terra` high after the first substantive failure; it identified active-run packet integration as the remaining family. |
| Final closure re-attestation reviewer | `/root/model_policy_astra_closure` | model not exposed by runtime; effort not exposed | Requested `gpt-6-astra` xhigh after the second unsuccessful loop; the runtime accepted the assignment but did not expose actual model or effort to the reviewer. |

No fallback is claimed. Requested routing is recorded separately from actual
runtime metadata whenever the delegated runtime did not expose the latter.

## Invariants verified

- Slice-4 writes are additive V4 review history only and cannot publish, select,
  release, or mutate V1/V2/V3 authority.
- Each case, draft, request, rejection, signoff, and lifecycle event has exact
  immutable ownership, state, predecessor, request identity, authorization
  snapshot, canonical bytes, and domain-separated hashes.
- The stable input CAS excludes observation time; the timestamped observation
  envelope preserves the exact verified/missing/stale/integrity/unsupported
  branch and its closed key set.
- Requests freeze one exact immutable draft. Rejection binds the frozen and
  current observation and creates no acceptance decision-node graph.
- Server authorization is repeated under lock; active platform-admin identity,
  membership, organization, policy, action, claims, and result are retained.
- Idempotency, event order, terminal uniqueness, case succession, and lock
  ordering are enforced in both service logic and deferred PostgreSQL checks.
- Detail and queue reads use repeatable-read, reverify hashes and lifecycle
  structure, and return controlled nonverification for source or projection
  integrity failures.
- History, source verification, projection reconstruction, lifecycle, and
  returned pagination work are bounded before large payloads are loaded.
- Phase-aware 16 MiB draft, 28 MiB requested, and 40 MiB terminal limits retain
  enough capacity for request, rejection, and successor creation.
- Application and database rollout gates default off; downgrade is exact only
  while both gates are off and the six review tables are empty.

## Findings disposition summary

The ledger contains 17 findings: 4 blockers, 8 high, and 5 medium. All are
closed with evidence. There are no accepted risks, deferred findings, rejected
findings, or open/fix-pending findings.

Four design review passes and six implementation review passes were recorded.
The final implementation adversary closed M-001 against packet
`b531efdaba8866893e8c0dcdb4d60f19922c87bfab95371892e455551ba9647a`
after independently reproducing both count and byte parent-projection overflow
through case detail and queue reads.

## Verification performed

- Static: `git diff --check`, JSON validation, and Python compilation over all
  changed implementation, migration, and test modules passed.
- Host V4/API/service/reconstruction/calibration gate: **532 passed, 1 skipped**
  in 191.41 seconds.
- Focused review/service/storage gate: **93 passed** in 8.49 seconds; the
  independent reviewer repeated the same 93-test gate successfully.
- Fresh empty database `paprnav_s4_closure7` migrated through 0001-0029 and the
  migration/lock-order/review-service gate passed **86 tests** in 36.66 seconds;
  the independent reviewer repeated the same 86-test gate successfully.
- Independent populated parent-count and parent-byte probes passed for both
  detail and queue with zero projection request/event payload-byte selections.
- Dedicated rollback database `paprnav_s4_rollout4`: **4 passed**, including
  exact inherited-function restoration, helper removal, independent gate
  refusal, and occupied-history refusal.
- Isolated prior-slice PostgreSQL regressions passed: candidate 5,
  applicability 24, obligation 68, and old-reader rollout 1.

## Final scope reviewed

- Migration 0029 SQL/Alembic upgrade and downgrade, six immutable review tables,
  closed checks, deferred validators, history protection, and rollout gates.
- Review ORM models, API schemas/routes, service construction and verification,
  storage error normalization/bounds, and the bounded lock-order changes in
  candidate, applicability, and obligation services.
- Review-case migration, rollback, concurrency, service, API, bounds,
  authorization, corruption, calibration regression, and direct-SQL tests.
- The decision packet, normative matrix, rollout contract, complete working
  tree, staged/unstaged/untracked files, and relevant surrounding consumers.
- The repository-root model-routing directive and detailed persistent policy,
  added after the first closure PASS and bound into the fresh closure
  re-attestation packet before any shared commit.
- Every stable active-run review artifact is an explicit hash-bound input to
  the final re-attestation packet. Generated packet/manifest files and
  append-only final attestation bookkeeping follow the narrowly documented
  self-reference exception and repository validator path in
  `model-routing-policy-integration.md`.

## Accepted risks and deferred work

There are no accepted-risk ledger entries in this vertical.

The following work is intentionally deferred outside this rejection-only
closure and requires new decision packets and adversarial review:

- candidate-only acceptance, decision-node gates/dependencies, and actionable
  classification;
- executable evaluator and supporting-document admission contracts;
- reviewer UI and complete form/control projection;
- release/publication/current selection, V3 freeze, search, matching, coverage,
  compliance, terminating-credit, and due-state consumers.

`signature_hash` is an internal integrity digest, not PKI, a user-held-key
signature, or legal non-repudiation proof.

## Not verified

- No production rollout, gate enablement, or live-data migration was performed.
- No acceptance, publication, current-selection, or release-authority behavior
  exists in this implementation and none is approved by this closure.
- Frontend reviewer UI behavior is absent and was not tested.
- The five calibration packets were reverified through the unchanged candidate,
  Slice-3A, and Slice-3B reconstruction layers, not through deferred acceptance
  UI/signoff paths.

```
### `.ai/review-runs/T081-V4-SCHEMA-SLICE-4/normative-gate-and-form-matrix.md`

size=32650; sha256=1d38a293ab03dfc0664e1a01a43f563c10f404d18355e6c4859709dd5b23c3be

```text
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

```
### `.ai/review-runs/T081-V4-SCHEMA-SLICE-4/implementation-verification.md`

size=5601; sha256=33645eb503bef33198bfe86c1069df16bf7df8d19e36a93fdc9549d3368fce0b

```text
# T081 V4 Schema Slice 4 implementation verification

Verification date: 2026-09-13  
Builder/coordinator: `/root`  
Base commit: `4840a0b4bc5d7334ddcf51a80e39c8fa84b7b0c2`

## Static gates

- `git diff --check`: passed.
- `python3 -m py_compile` over every changed Python implementation, migration,
  and Slice-4 test module: passed.
- No files were staged or committed.

## Host API, service, reconstruction, and calibration gate

Command (from `backend`):

```text
PAPRNAV_DISABLE_DOTENV=1 PYTHONPATH=. .venv/bin/pytest -q \
  tests/test_storage.py tests/test_ad_v4_api.py tests/test_ad_v4_candidates.py \
  tests/test_ad_v4_applicability.py tests/test_ad_v4_obligations.py \
  tests/test_ad_v4_calibration.py tests/test_ad_v4_applicability_calibration.py \
  tests/test_ad_v4_obligations_calibration.py \
  tests/test_ad_v4_review_service_bounds.py tests/test_ad_v4_reviews.py
```

Result: **532 passed, 1 skipped** in 191.41 seconds. This includes the five
retained-source calibration packets through validator-2, Slice-3A, and
Slice-3B exact reconstruction. The previously reported isolated-container
page-text mismatch did not recur when the repository's exact six retained PDF
fixtures were used.

The focused review/service/storage subset also passed independently after the
final bounded-work changes: **93 passed** in 8.49 seconds.

## Fresh PostgreSQL migration and Slice-4 gate

Disposable database `paprnav_s4_closure7` was created empty and migrated
through every revision from 0001 to `20260913_0029` using the final working
tree. Migration succeeded.

Command:

```text
PAPRNAV_TEST_POSTGRES_URL=postgresql+psycopg://.../paprnav_s4_closure7 \
  PYTHONPATH=. .venv/bin/pytest -q \
  tests/test_ad_v4_review_case_migration_postgres.py \
  tests/test_ad_v4_review_lock_order_postgres.py \
  tests/test_ad_v4_review_service_postgres.py
```

Result: **86 passed** in 36.66 seconds.

This gate includes:

- every closed observation branch accepted by both SQL and Python;
- fully resealed malformed observation, digest, source-row, head, ordinal,
  cross-directive, and capacity counterexamples rejected at commit;
- cutoff source arrays accepted at 2,000 and rejected at 2,001;
- six two-administrator candidate/review interleavings covering new content and
  reuse against case creation, review request, and rejection;
- forced direct-SQL same-actor submission/review and applicability-request/review
  interleavings, proving the final inherited trigger definitions lock user
  before membership and both transactions commit without SQLSTATE `40P01`;
- phase-aware 16 MiB draft, 28 MiB requested, and 40 MiB terminal aggregate
  authoritative-byte boundaries enforced by both service preflight and
  commit-time SQL before JSON parsing;
- an exact near-ceiling PostgreSQL lifecycle that fills the draft phase to
  within 1 KiB, proves the next draft is refused, and then commits request,
  rejection, and successor creation across partial flushes;
- a combined 64 MiB evidence-text/retained-source work budget and 2,000-binding
  and lifecycle-event queue budget, including lifecycle reason bytes,
  controlled handling of individually oversized proposals, bounded local/S3
  retained-object reads, metadata-only authorship/cutoff/frozen-source queries,
  and head-only cutoff selection;
- scalar preflight of applicability/obligation projection counts, accumulated
  materialization-request/event counts, and canonical payload bytes before
  reconstruction, including populated obligation-over-count,
  applicability-parent-over-count, and applicability-parent-over-byte cases;
- exact dependency propagation from an over-budget applicability projection to
  its obligation child, which returns controlled `projection_integrity` without
  directly or indirectly selecting the parent's request payload;
- a complete service rejection lifecycle with deferred constraints forced
  immediate before commit.

## Isolated prior-slice PostgreSQL regressions

Migration tests intentionally change the schema revision, so each suite was
run against its own newly created database migrated from empty to 0029:

- candidate persistence (`paprnav_s4_final_candidate3`): **5 passed**;
- Slice-3A applicability (`paprnav_s4_final_app3`): **24 passed**;
- Slice-3B obligation persistence and serializer
  (`paprnav_s4_final_obligation3`): **68 passed**;
- Slice-3B old-reader rollout (`paprnav_s4_final_oldreader3`): **1 passed**.

Two legacy downgrade assertions were updated from old head 0028 to current
head 0029. No production behavior was weakened.

## Slice-4 downgrade/rollback gate

Disposable database `paprnav_s4_rollout4` was created empty and
migrated 0001 to 0029. The dedicated rollback module then proved:

- empty/disabled 0029 downgrades to 0028 and re-upgrades cleanly;
- each reviewer gate independently refuses downgrade without schema loss;
- immutable review occupancy refuses downgrade without row loss.

The empty-history test additionally captures both complete 0028 inherited
function definitions, upgrades, downgrades again, proves exact definition
equality, and proves the Slice-4 aggregate-byte helper is absent after each
downgrade.

Result: **4 passed** in 4.01 seconds.

## Invalid combined-run disclosure

An earlier attempt ran all PostgreSQL migration modules sequentially in one
database. Legacy tests deliberately downgraded that shared schema, cascading
into later missing-function and gate failures. That run was invalid as a test
isolation strategy. The modules were subsequently rerun on the separate fresh
databases listed above; every isolated suite passed.

```
### `.ai/review-runs/T081-V4-SCHEMA-SLICE-4/model-routing-policy-integration.md`

size=4915; sha256=e9426dc98a0902191dc0b1df202efd060c7c47d49d706b592e8c2829b70a51e6

```text
# Model-routing policy integration evidence

## Model routing

Builder/coordinator runtime: `/root`  
Actual builder model: `model not exposed by runtime`  
Actual builder effort: `effort not exposed`  
Initial requested verification route: `gpt-5.6-terra` medium  
Escalated verification route: `gpt-5.6-terra` high  
Closure re-attestation route: `gpt-6-astra` xhigh

Routing trigger: the policy edit was localized and mechanically checkable. The
first substantive verification failure increased effort. The second failure in
the same evidence/integration family escalated the complete next pass to Astra
and stopped narrow artifact-by-artifact patching.

Delegated runtime evidence:

- `/root/v4_s4_design_adversary` later reported `model not exposed by runtime`
  and `effort not exposed` for its pre-policy design, implementation, and
  closure reviews. The coordinator checkpoint's Astra description is retained
  only as requested-assignment evidence, not claimed as actual runtime metadata.
- `/root/model_routing_policy_verifier` reported `model not exposed by runtime`
  and `effort not exposed`; it found the missing authoritative model-evidence
  location.
- `/root/model_routing_policy_closure` reported `model not exposed by runtime`
  and `effort not exposed`; it found that the active run's final packet did not
  yet bind the new policy and prospective evidence.
- `/root/model_policy_astra_closure` reported `model not exposed by runtime`
  and `effort not exposed`; the coordinator requested and the runtime accepted
  the Astra xhigh assignment for the final re-attestation.

## Complete integration invariant

Every file intended to share the active Slice-4 commit must be hash-bound into
one current closure packet. Model-evidence requirements apply prospectively
from adoption: immutable reports completed before the policy was written are
not rewritten, while `closure.md`, this integration evidence, and the fresh
closure re-attestation must contain the required actual/unexposed metadata and
routing history.

The final independent reviewer must verify:

- `AGENTS.md` preserves all existing requirements and mandates the linked
  repository policy;
- `.ai/MODEL_ROUTING.md` covers tiers, escalation, separation, dynamic
  availability, notices, review evidence, closure summary, and project-subagent
  mechanics;
- the policy and all active implementation files are present in the fresh
  packet manifest with no unexplained out-of-scope dirty file;
- the prior Slice-4 implementation fingerprint and implementation content
  remain unchanged; and
- the run validates only after the fresh closure re-attestation is recorded.

## Third-loop oracle and file coverage

After the third unsuccessful evidence/integration review, implementation stayed
paused. `adversarial-closure-model-routing-fail-1.md` records the failed Astra
pass. The missing shared oracle is this exhaustive classification of the dirty
commit-intended tree:

1. **Manifest-bound source and policy files:** `AGENTS.md`,
   `.ai/MODEL_ROUTING.md`, and all 23 Slice-4 implementation, migration,
   contract, and test files. `build-review-packet.py` hashes these directly in
   `manifest.json`.
2. **Hash-bound stable review inputs:** the decision, findings ledger, closure
   report, normative matrix, implementation verification, this integration
   evidence, all eleven historical adversarial reports, the failed model-routing
   re-attestation report, and its prospective builder/reviewer metadata
   supplement. Each is passed explicitly as a review input in the final packet;
   none may change after review.
3. **Generated self-reference exceptions:** `manifest.json`,
   `review-packet.md`, and `review-packet.sha256` cannot include their own final
   hashes. The reviewer verifies the packet SHA and manifest entries directly.
4. **Append-only attestation exceptions:** `reviews.json`, `state.json`, and the
   final re-attestation artifact necessarily change or appear only after the
   reviewer returns. Their pre-attestation hashes are anchored below. The
   coordinator must use `record-review.py --reattest`, which verifies the frozen
   packet/fingerprint before appending the new artifact hash and transition,
   then run `validate-review-run.py` to verify review identity separation,
   artifact hashes, phase, and closure coverage.

Pre-attestation bookkeeping anchors:

- `reviews.json`: `9efa540f04696a060afb22cc192c5a30966820f5c613b531017eb575b945d2e2`
- `state.json`: `3907588bbb6e20c5e9164c06d2b8916ef2eb238eec2fa111f335589a9e811b2a`

Only categories 3 and 4 are exempt from direct stable-input binding. Any other
dirty commit-intended file missing from the final manifest or review-input list
is a closure blocker. Reviewer self-report is the oracle for actual model and
effort; requested assignment is recorded separately and never substituted.

No standalone commit is authorized by this evidence.

```
### `.ai/review-runs/T081-V4-SCHEMA-SLICE-4/model-routing-policy-metadata-supplement.md`

size=1118; sha256=87d3146756ae2c7db3d4e5a93780b8ae02d78afaa5504739559c4afe8cc2ce75

```text
# Model-routing metadata supplement

This supplement completes the prospective metadata contract for
`adversarial-closure-model-routing-fail-1.md` without rewriting that hash-bound
review report.

## Model routing

Builder/coordinator runtime: `/root`  
Actual builder model: `model not exposed by runtime`  
Actual builder effort: `effort not exposed`  
Reviewer runtime: `/root/model_policy_astra_closure`  
Actual reviewer model: `model not exposed by runtime`  
Actual reviewer effort: `effort not exposed`  
Requested reviewer assignment: `gpt-6-astra`, xhigh  
Trigger: closure re-attestation after recurring failures in the
model-evidence/integration family.

The failed review's own `## Model routing` section already records reviewer
identity, unexposed actual metadata, requested assignment, trigger, and packet
hash. It omitted builder metadata because the reviewer's returned report did
not contain those fields. This supplement is the authoritative prospective
builder/reviewer metadata companion for that immutable report. Requested model
selection is not represented as exposed actual runtime metadata.

```
### `.ai/review-runs/T081-V4-SCHEMA-SLICE-4/adversarial-closure-final.md`

size=3182; sha256=e575abc57f92f7f553b465f552d2f9e09338fbe1ef734e14e306cb4bfa005199

```text
# T081 V4 Schema Slice 4 closure-stage review

Outcome: **PASS**  
Reviewer runtime: `/root/v4_s4_design_adversary`  
Builder/coordinator: `/root`  
Reviewed packet SHA-256: `d721b6b6092c459fae07977a96c21c9bfc5819d685d74410fe9c4302fd29bab1`  
Base: `4840a0b4bc5d7334ddcf51a80e39c8fa84b7b0c2`

## Final-tree and record verification

The reviewer verified the exact packet, all 23 implementation-file hashes,
review-input hashes, staged/unstaged/untracked inventory, and every recorded
review-artifact hash. The reviewed closure scope fingerprint is
`ab139ebd2d1abf50a72aab1750636c39c2bdeba4328c4d8797074660c9ef8978`.
No staged changes or unexplained out-of-scope files were present;
`git diff --check` passed.

The reviewer independently reconstructed the prior M-001 ledger state by
reversing only its final closure status/evidence change. Combined with the
current implementation files and decision input, this reproduced the exact
recorded implementation-stage fingerprint:

`80d053ade74597cece7a50e70f160be350322a754ee1149c282234cafa0532e7`

This cryptographically confirms that no implementation, migration, SQL,
contract, or test content changed after the implementation PASS. The recorded
implementation closure-5 artifact accurately reflects the reviewer's returned
review, independent probes, test results, and rejection-only approval boundary.
The review records identify `/root/v4_s4_design_adversary` as reviewer and
`/root` as builder, preserving separation.

## Findings and evidence

All 17 findings—4 blockers, 8 high, and 5 medium—are closed with traceable
evidence. There is no open, fix-pending, accepted-risk, rejected, or deferred
finding, and no new finding was identified.

The closure report correctly distinguishes implemented behavior from
design-only and deferred work. It accurately attributes the independently run
93-test host gate, 86-test PostgreSQL gate, populated detail/queue overflow
probes, and prior four-test rollback gate. Broader builder regressions are
identified separately.

Rollout and downgrade documentation matches the implementation: three
application flags and two database gates default off; staged activation
requires aware binaries; occupied immutable history prohibits physical
downgrade; empty, disabled downgrade restores inherited definitions and removes
Slice-4 helpers.

## Approved boundary

This PASS approves only the rejection-only vertical: immutable cases and
annotation drafts, frozen requests, graph-free rejecting signoffs, and bounded
verified reads.

It does not approve candidate-only acceptance, node-gate classification,
reviewer UI, supporting-document admission, publication/current selection, V3
freeze, or downstream authority consumers. Those omissions are explicit,
justified, and require later reviewed work. No production rollout or gate
enablement is claimed.

Additional closure-record hashes verified by the reviewer:

- `closure.md`: `6acfa559c52f48bc8191e36124c781959a1d183d1c10fa0a6ab5af0ffe2875dc`
- `implementation-verification.md`: `33645eb503bef33198bfe86c1069df16bf7df8d19e36a93fdc9549d3368fce0b`

**Closure PASS. The reviewed working tree is ready to commit as this bounded
vertical.**

```
### `.ai/review-runs/T081-V4-SCHEMA-SLICE-4/adversarial-design-initial.md`

size=7751; sha256=15f53fdea19ca5b52c8af9b648ef29afcd65ce28df9e95230a4c1bd14dbdf096

```text
# T081 V4 Schema Slice 4 — initial adversarial design review

Reviewer: `/root/v4_s4_design_adversary`

Reviewed base: `4840a0b4bc5d7334ddcf51a80e39c8fa84b7b0c2`

Decision SHA-256: `a337ae91010ebb7c17e49ee3dffc720c3b0848a218b4bbebda920a379ce6a356`

Outcome: **FAIL. Do not advance to implementation.**

The review was read-only. Staged and unstaged changes were empty; the only
untracked scope was the Slice-4 review-run directory. No implementation or
database tests were run because this is a design gate.

## Blockers

### T081-V4-S4-B-001 — Release-eligible acceptance is impossible

S4-I09/I12/I24 require an implemented evaluator for an actionable node and all
release-required nodes to be actionable. Current Slice-3A conditions, rules,
and expressions are constrained to `evaluator_contract='none'` in the ORM,
migration 0027, and reconstruction verifier. Slice 3A expressly reserves an
evaluator for separate review. A synthetic known-value candidate therefore
cannot prove release eligibility without inventing evaluator authority.

Required closure: make Slice 4 candidate-only/rejection only until a separately
reviewed evaluator exists, or explicitly add and review the complete evaluator,
normalization, predicate/operator, version, and calibration expansion. Replace
the impossible positive release test with a negative gate proof if bounded.

### T081-V4-S4-B-002 — Exact gate and independent SQL contract are absent

The packet promises a future specification but does not freeze every node
family, base gate, controlling status, evidence requirement, dependency
direction, cycle rule, aggregate minimum, reason, or calibration oracle. The
existing graphs contain structural, expression, prerequisite, termination,
recurrence, search-hint, and correction relationships with materially different
semantics. Caller-supplied gate rows or hashes cannot be their own SQL authority.

Required closure: add the complete normative matrix before implementation.
Migration-owned SQL must independently derive the expected rows and edges from
trusted projection inputs and fixed rule data. Include exact direct-SQL
counterexamples and hand-declared fixture oracles.

### T081-V4-S4-B-003 — Lifecycle has no pre-decision aggregate

The proposed drafts and pending request exist before an immutable decision
version, but no review-case root, event owner, creation command, uniqueness/CAS
boundary, or remediation path is defined. Event and state names are mixed and
`review_requested` is omitted. Strong acceptance integrity would also prevent
recording rejection of the malformed inputs that most need remediation.

Required closure: define the immutable review-case aggregate, event/state fold,
creation timing, unique keys, predecessor hashes, draft/request concurrency,
re-review rules, and a rejection path that can record unverifiable inputs while
preserving stronger acceptance gates.

## High findings

### T081-V4-S4-H-001 — Signing lock order conflicts with current V4 writers

The packet locks membership last. Existing candidate and 3A/3B writers lock the
user/membership before proposals, creating a membership/proposal deadlock
cycle. Existing-row locks also do not prevent append-only corrections or
authorship rows.

Required closure: freeze one shared order across signing, candidates,
materialization, evidence, corrections, gate administration, and direct SQL;
name advisory/predicate locks for append-only sets and add forced interleavings.

### T081-V4-S4-H-002 — Parent-required V3 freeze has no activation disposition

The parent design freezes new V3 approvals/corrections at V4 deployment. Slice
4 explicitly leaves the live V3 publication route and buttons unchanged.

Required closure: define the exact activation point and accountable slice. If
it is Slice 4, add and review a V3-write gate. If later, explicitly amend the
coexistence interval and explain why the parent contract remains safe.

### T081-V4-S4-H-003 — Supporting-document admission is undecided

The workflow is conditional, while its proposed issuer/admission/scope binding
cannot be represented by unchanged validator-2 and 3B forces retention to
unknown. Existing source download is not a supporting-document admission or
access-policy service.

Required closure: either explicitly defer it, keep dependent nodes
nonactionable, and name the later owner, or specify the complete immutable
acquisition/access/authenticity/scope/admission lifecycle and versioned binding.

### T081-V4-S4-H-004 — Read verification has no single-snapshot/version contract

Historical and current revalidation spans mutable heads but the packet does not
require one repeatable-read snapshot or preserve the original gate/authorship/
policy verifier. Read committed can mix generations and current rules can
misclassify valid history.

Required closure: use one separate repeatable-read, read-only snapshot per
operation; distinguish frozen historical verification from current eligibility;
define unsupported old-version handling and forced concurrent-change tests.

### T081-V4-S4-H-005 — Existing auth helper cannot supply promised validity

The current helper checks role/status but membership has no validity interval or
immutable version. ORM identity-map caching is not necessarily refreshed by a
locking query, and expected input hashes do not cover membership changes.

Required closure: define validity and the submit CAS token from the actual
model; freshly fetch/refresh locked scalar state; add an independent SQL
actor/membership check; preserve historical snapshots without comparing them to
current role/status; and test downgrade/deactivation races.

## Medium findings

### T081-V4-S4-M-001 — Machine authorship and cutoff lack provenance

Existing candidate submissions are all attributable platform-admin actions;
there is no machine-only actor. Proposal content deduplicates while later
submissions/relationships may append, so recomputing authorship can rewrite the
meaning of old signoff.

Required closure: conservatively treat current submissions as human, freeze
the exact contributing event IDs/cutoff, distinguish creator/resubmitter/
corrector, and defer machine-only status absent a trusted provenance path.

### T081-V4-S4-M-002 — Form preservation/edit mapping is incomplete

The broad UI controls do not map every validator-2 root family, ordered list,
optional-property presence, and typed reference. A form correction could drop
or reorder valid semantics even though the predecessor remains immutable.

Required closure: freeze complete editable/read-only control mapping, exact
preservation rules, semantic diff, reference revalidation, and focused edits
for recurrence, ordered actions, corrections, unknowns, and search hints.

### T081-V4-S4-M-003 — Rollout stages do not match proposed gates

One app and one DB gate cannot separately stage reads, draft/request writes, and
terminal signoff. A migration cannot observe flags on all application replicas.

Required closure: define real capability controls, defaults, database reporting,
deployment procedure, enforceable downgrade checks, and complete occupancy.

## Sound boundary

The non-publication boundary is sound. Current released readers select approved
V3 extractions, and isolated V4 review/signoff tables would not by themselves
enter catalog, search, matching, coverage, compliance, or due-state readers.

## Gate result

All eleven findings remain open. No finding is accepted risk, rejected, or
closed. Required design decisions before re-review are: executable acceptance
states; the complete gate/SQL matrix; review-case lifecycle/remediation; shared
locking and read snapshots; supporting-document scope; and the V3-freeze
activation point.

```
### `.ai/review-runs/T081-V4-SCHEMA-SLICE-4/adversarial-design-closure-1.md`

size=1379; sha256=b1b3d7ed54f2bcbe208fb28a9b3832f804937600723c796238a2426c72fd886b

```text
# T081 V4 Schema Slice 4 — design closure review 1

Reviewer: `/root/v4_s4_design_adversary`

Exact packet SHA-256:
`f414c2f77d209308916eb52d50d7dc5afe9a513dee0f0f3c7096e450e3b402c3`

Outcome: **FAIL — targeted closure incomplete.**

The reviewer verified all bound input hashes and reviewed read-only against
repository HEAD `4840a0b4bc5d7334ddcf51a80e39c8fa84b7b0c2`.

Closed at design level: B-001, H-001, H-002, H-003, H-004, M-001, M-002,
and M-003.

Still open:

- **B-002:** the exact matrix omits 3A rule-exclusion dependencies; invents a
  supersession target semantic node where only an external projection exists;
  omits several manufacturer/identity-mapping consumption relations; conflicts
  on whether `actionable` means executable or merely source-representable;
  incorrectly treats independently valid timing enums as an executable
  combination; and lets SQL trust rather than reconstruct the frozen authorship
  set.
- **B-003:** S4-I04/I06 still apply acceptance-grade verified projections to
  every draft/signoff, contradicting the designed missing/stale observed-input
  remediation and graph-free rejection path.
- **H-005:** PostgreSQL `FOR KEY SHARE` does not conflict with non-key updates to
  role/status and therefore cannot protect the direct-SQL signoff boundary.

Required closure is limited to those residuals. No new finding ID was opened.

```
### `.ai/review-runs/T081-V4-SCHEMA-SLICE-4/adversarial-design-closure-2.md`

size=1022; sha256=1144533313869e4644e5aa2226f7b092d931b7c93beb7d536dc67dff1bae9125

```text
# T081 V4 Schema Slice 4 — design closure review 2

Reviewer: `/root/v4_s4_design_adversary`

Exact packet SHA-256:
`f3d597efcc16c0fc8671936217760dfebc15e9ce634ccc6337d628fbd0ec2271`

Outcome: **FAIL — one residual blocker.**

B-002 and H-005 are closed at design level. The packet now separates source
representation from automation authority, contains the missing exclusion and
identity mapping edges, binds external supersession state without invented
nodes, independently derives SQL authorship, and uses actor/membership `FOR
UPDATE` through commit.

B-003 remains open only because the observed-input hash includes `observedAt`
while also serving as the client CAS token. A fresh unchanged observation at a
later time would hash differently. Closure requires a stable input-identity
digest excluding time, separate from the timestamped audit-envelope digest,
with elapsed-time, substantive-change, and two-observation rejection tests.

All previously closed findings remain closed. No new finding ID was opened.

```
### `.ai/review-runs/T081-V4-SCHEMA-SLICE-4/adversarial-design-final.md`

size=1278; sha256=69803af2288fdc51c7936137aafb028d3a04a4665a58aeb52bb6dc7bc3b7eb53

```text
# T081 V4 Schema Slice 4 — final adversarial design review

Reviewer: `/root/v4_s4_design_adversary`

Exact packet SHA-256:
`96efc7a7c89e853ce6542c4d6a3a42b96879b3c3a23937fbdbe7ec6e85f145e0`

Outcome: **PASS.**

All design blockers and highs are closed. No new finding was identified. The
reviewer verified the packet's decision, finding-ledger, and normative-matrix
hashes against the files.

The final B-003 closure verifies that the stable input-identity hash excludes
wall-clock/request/actor/UI fields, the audit envelope separately retains
`observedAt`, clients CAS only the stable identity, rejections bind requested
and current identity/audit pairs, and tests require elapsed-time stability plus
substantive-change invalidation.

B-002 and H-005 remain closed: the complete dependency/SQL/authorship contract
and actor-then-membership `FOR UPDATE` authorization boundary are intact.
B-001, H-001 through H-004, and M-001 through M-003 remain closed: bounded
candidate-only semantics, shared locking, Slice-5 V3 freeze ownership,
supporting-document deferral, historical verification, conservative authorship,
read-only form coverage, and rollout/downgrade controls did not regress.

This attestation approves the design only. It makes no implementation or test
claim.

```
### `.ai/review-runs/T081-V4-SCHEMA-SLICE-4/adversarial-implementation-initial.md`

size=1868; sha256=864950e0ed8b64d85f17acf177147ef016ab7061b9efbb67ec59fad46139f535

```text
# T081 V4 Schema Slice 4 — implementation adversary (initial)

Outcome: **FAIL**

Reviewer runtime: `/root/v4_s4_design_adversary`

Exact packet SHA-256:
`a30f4b621611111f636caa94d7b858e3b012bbc51cf890b03af6ddb04b771994`

Base: `4840a0b4bc5d7334ddcf51a80e39c8fa84b7b0c2`

The independent reviewer inspected the staged, unstaged, and untracked tree,
the candidate/evidence/projection writers and readers, migration SQL, API and
schema contracts, storage behavior, tests, and rollout contract. It ran the
focused API/service and PostgreSQL suites and additional rollback-only probes.

The rejection-only boundary is correctly preserved: there is no acceptance,
decision-node graph, publication/current selection, V3 authority mutation, or
reviewer UI in this vertical. The implementation is not approved because one
Blocker, two Highs, and one Medium remain:

1. `T081-V4-S4-IMPL-B-001`: PostgreSQL accepted a fully resealed nonverified
   observation with a malformed nested hash that Python historical reads
   reject. SQL must enforce the complete branch/field/digest/source contract
   and gain direct-SQL parity tests.
2. `T081-V4-S4-IMPL-H-001`: candidate submission locks evidence fragments
   before the relationship graph while review writers do the reverse. A forced
   interleaving reproduced SQLSTATE `40P01`; candidate error translation is
   also incomplete.
3. `T081-V4-S4-IMPL-H-002`: expected S3 missing/access/transport errors escape
   retained-source observation rather than becoming a bounded nonverified
   remediation state.
4. `T081-V4-S4-IMPL-M-001`: response paging does not bound full history,
   predecessor, and source verification work.

The reviewer independently observed 3 API/service tests and 13 PostgreSQL
migration/service tests passing and found `git diff --check` clean. Those
passing tests do not close the four findings above.

```
### `.ai/review-runs/T081-V4-SCHEMA-SLICE-4/adversarial-implementation-closure-1.md`

size=2894; sha256=c62a02782b3c078258a71d6f9cbbc03f95c63a05e6de843bbaebd16b690e9092

```text
# T081 V4 Schema Slice 4 implementation closure review 1

Outcome: **FAIL**  
Reviewer runtime: `/root/v4_s4_design_adversary`  
Exact packet SHA-256: `1a7385408bd7b6ae26378037d1b313c4c2735b82891eeb84492494927a4c6c37`  
Base: `4840a0b4bc5d7334ddcf51a80e39c8fa84b7b0c2`

## T081-V4-S4-IMPL-B-001 — CLOSED

SQL now validates nested value types, digest encoding, required/forbidden
fields, actual evidence absence, evidence heads, selected projection identity,
and directive ownership. Fully resealed malformed-digest, nonverified-source,
and cross-directive variants are covered. Positive branch tests verify
SQL-accepted observations against Python. The independent 77-test PostgreSQL
closure run passed.

## T081-V4-S4-IMPL-H-001 — OPEN

The original fragment/relationship cycle is fixed and six real
two-administrator interleavings pass. A residual remains in inherited SQL.

Invariant: cooperating application and direct-SQL writers must use the same
authorization lock order.

Evidence:

- final-schema `paprnav_v4_validate_submission()` still locks membership before
  user, while review SQL locks user before membership;
- final-schema `paprnav_v4_validate_app_materialization_request()` similarly
  locks membership before user;
- the passing interleavings use application writers that pre-acquire user
  first, so they do not cover these direct-SQL trigger paths.

Impact: a same-actor review may hold user U while a direct-SQL writer holds
membership M, producing a U/M cycle.

Required closure: replace both inherited guards in 0029 with user-before-
membership ordering, restore prior definitions on downgrade, and force direct-
SQL-versus-review interleavings without application authorization pre-locks.

## T081-V4-S4-IMPL-H-002 — CLOSED

Expected retained-storage failures now have a dedicated allowlisted boundary
outside structural validation. Tests cover observation through rejection and
prove unexpected programming/database/provider errors propagate.

## T081-V4-S4-IMPL-M-001 — OPEN

Row caps, limit-plus-one checks, source caching, and batched lookups do not yet
bound aggregate bytes. A legal 1,000-draft allocation-light probe measured
approximately 1.98 GB before ORM/driver/parsing overhead because annotations
and request blobs are repeated in draft/event rows.

Required closure: enforce a practical aggregate per-case byte/work budget in
service admission, SQL commit validation, and read preflight before loading
blobs. Add exact-boundary, fully resealed direct-SQL overflow, and query/work
budget tests while retaining request/rejection capacity.

## Independent verification

- focused host API/service: 73 passed;
- PostgreSQL observation/migration/concurrency/lifecycle: 77 passed;
- `git diff --check`: passed;
- packet hash remained unchanged.

The reviewer remained read-only. Rejection-only scope and affirmative-authority
isolation remain intact.

```
### `.ai/review-runs/T081-V4-SCHEMA-SLICE-4/adversarial-implementation-closure-2.md`

size=3921; sha256=87bd237f19dfeeb01b7176324c81b38d13b5d6e2782707d11e6e3daeb5b06b5a

```text
# T081 V4 Schema Slice 4 implementation closure review 2

Outcome: **FAIL**  
Reviewer runtime: `/root/v4_s4_design_adversary`  
Packet SHA-256: `d66b273688a22b9ff05b7ab896c66b0688fd2cf30131e13576b10273b7292338`  
Base: `4840a0b4bc5d7334ddcf51a80e39c8fa84b7b0c2`

The packet hash remained unchanged. All 23 manifest file hashes matched the
working tree, no files were staged, and the reviewer inspected changed,
untracked, and surrounding implementation without editing repository files.

## T081-V4-S4-IMPL-H-003 — high — open

Legal drafts can consume the entire 16 MiB case budget without reserving space
for the mandatory request and rejection lifecycle. The reviewer reproduced
this on PostgreSQL with all constraints and triggers enabled: nine legal drafts
left a case at 16,777,214 authoritative bytes, `request_review` failed with
`review_history_limit`, and successor creation failed with `review_case_open`.
Because history is immutable, that candidate's workflow is permanently
stranded.

Required closure: enforce phase-aware byte reservations in Python and SQL so
admitted drafts preserve space for request, rejection, companion events, and
signoff. Add fully sealed PostgreSQL boundary tests proving request, rejection,
and successor creation remain possible after maximal admitted drafts.

## T081-V4-S4-IMPL-M-001 — medium — remains open

Case-byte accounting and retained-object bounds improved, but metadata-only
authorship, cutoff, and frozen-source verification still select complete
submission, relationship, and fragment entities, including large
`request_canonical_bytes` and `exact_text` values outside the work budget.
Cutoff head construction also traverses the complete lifecycle chain through
the unbounded evidence lifecycle verifier. Allocation-light probes confirmed a
1 MiB unused submission blob was selected and oversized evidence re-entered
full-text materialization after the observation branch declined that work.

Required closure: use explicit scalar projections for metadata-only reads,
prevent deferred blob loads, and bound or replace lifecycle traversal with a
reviewed bounded-head strategy. Apply the work policy across observation,
authorship, cutoff, and historical verification, with query-shape and overflow
tests proving prohibited payload columns are not selected.

## T081-V4-S4-IMPL-M-002 — medium — open

The verification document attributes exact downgrade restoration and helper
removal to automated gates, but current tests only assert final user-first lock
order. The exact definition comparison was an ad hoc probe, and only the draft
reviewer gate—not each gate independently—was tested for downgrade refusal.

Required closure: add an isolated `0028 -> 0029 -> 0028` regression comparing
both complete function definitions and verifying helper removal; test each
reviewer gate independently; correct the evidence document.

## Closed findings reverified

- `T081-V4-S4-IMPL-H-001`: closed. Both inherited functions now use the
  user-before-membership order, reject definition drift, and pass forced
  direct-SQL interleavings.
- `T081-V4-S4-IMPL-B-001`: remains closed. Observation-union, ownership,
  nested-digest, and SQL/Python parity tests pass.
- `T081-V4-S4-IMPL-H-002`: remains closed. Expected retained-storage failures
  and size overflow stay controlled; unexpected failures remain distinguishable.

## Independent verification

- Host review/service/storage suites: 91 passed.
- PostgreSQL migration, lock-order, and service suites: 82 passed.
- Legal lifecycle probe reproduced H-003.
- Source-query probes confirmed residual M-001 paths.
- `git diff --check`: passed.
- Manifest verification: 23 files matched with no packet drift.

Acceptance, decision graphs, publication/current selection, document
admission, the V3 freeze, and frontend UI remain outside this rejection-only
vertical. The implementation gate remains closed.

```
### `.ai/review-runs/T081-V4-SCHEMA-SLICE-4/adversarial-implementation-closure-3.md`

size=2618; sha256=9ce64726a703480bb22b7758cc7fd3d8f900d0aeb31794b855fc4f646eee7771

```text
# T081 V4 Schema Slice 4 implementation closure review 3

Outcome: **FAIL**  
Reviewer runtime: `/root/v4_s4_design_adversary`  
Packet SHA-256: `684ca24c3259a2de7df38e9e22c71cf3d01ee04e2f98876f22b2617ba97288af`  
Base: `4840a0b4bc5d7334ddcf51a80e39c8fa84b7b0c2`

The packet and all 23 manifest file hashes remained unchanged. The reviewer
inspected staged, unstaged, untracked, and surrounding scope without editing.

## H-003 — remains open

The 16/28/40 MiB reserve arithmetic is correct, but an exact two-byte-remainder
PostgreSQL probe still stranded the case. Request creation flushes the request
owner before its phase-changing event; `_finish` then checks stored bytes under
the old draft phase before considering the pending event. The request fails
with `review_integrity`, rolls back, and successor creation remains blocked by
the open case. Rejection uses the same partial-flush pattern.

Required closure: make phase accounting correct across partial flushes or flush
each transition atomically, retain rejection of genuinely corrupt committed
history, and add the exact near-ceiling request/rejection/successor regression.

## M-001 — remains open

The scalar authorship/cutoff/frozen-source queries, head-only cutoff,
lifecycle row/reason preflight, and bounded local lifecycle verifier are
verified. A surrounding projection path remains unbounded: review observation
calls obligation reconstruction, which loads every materialization request,
including its byte payload, with no count/byte preflight. A real projection
with three valid repeated requests remained verified while the observed query
had no limit and selected both canonical payload columns.

Required closure: preflight accumulating projection reconstruction inputs,
including materialization requests and projection event history, before payload
loads; use a stable nonverified branch when over budget; test the real populated
projection path with repeated valid requests.

## M-002 — closed

The rollback suite now compares both complete inherited function definitions,
verifies helper removal, and tests both reviewer gates independently. The
reviewer ran all four tests on fresh `paprnav_s4_reviewer_rollout5`; all passed.

## Verification

- Focused host review/service/storage: 93 passed.
- PostgreSQL migration/lock/service: 83 passed.
- Independent fresh rollback: 4 passed.
- Exact near-ceiling probe reproduced H-003.
- Populated projection trace confirmed residual M-001.
- Manifest and whitespace checks passed.

Earlier B-001, H-001, and H-002 remain closed. The implementation gate remains
closed on H-003 and M-001.

```
### `.ai/review-runs/T081-V4-SCHEMA-SLICE-4/adversarial-implementation-closure-4.md`

size=1737; sha256=12bcf21165e0f9179d10278041c25c0bb636138fe180b27875292ca4b598f6bd

```text
# T081 V4 Schema Slice 4 implementation closure review 4

Outcome: **FAIL**  
Reviewer runtime: `/root/v4_s4_design_adversary`  
Packet SHA-256: `e4b4a1e0d675bfc2b57e5fc7c978442eb87a1627ebdcdcc0018d52cc7c64526a`  
Base: `4840a0b4bc5d7334ddcf51a80e39c8fa84b7b0c2`

The packet and all 23 manifest hashes remained unchanged. No staged files or
reviewer edits were present.

## M-001 — remains open

Direct applicability and obligation audit preflights work, but the obligation
child does not inherit its exact applicability parent's failed preflight.
Independent PostgreSQL count and byte probes showed an over-budget parent and
within-budget child; applicability returned controlled `integrity_error`, but
obligation reconstruction still loaded the excluded parent's request payload
and returned verified. Queue accounting has the same incomplete dependency.

Required closure: bind child preflight to its exact `app_projection_id` parent,
propagate individually over-budget parent state through every consuming
reconstruction path and page accounting, and add populated count/byte tests
proving parent payloads are not selected indirectly.

## H-003 — closed

The reviewer replayed the exact prior two-byte-remainder case on
`paprnav_s4_closure6`. Request, rejection, and successor all committed; the
rejected case ended at 16,794,784 bytes. A separate probe confirmed historical
reads still use the stored phase and reject corrupt over-budget history even
when a phase-changing event is pending.

M-002, B-001, H-001, and H-002 remain closed. Focused host tests passed 93,
PostgreSQL tests passed 84, the exact lifecycle replay passed, and manifest and
whitespace checks passed. The implementation gate remains closed only on
M-001.

```
### `.ai/review-runs/T081-V4-SCHEMA-SLICE-4/adversarial-implementation-closure-5.md`

size=3746; sha256=093f85e5a5c7df8add7b194dbe5c15381f9b6cb580c7f9269f6f332461b4730e

```text
# T081 V4 Schema Slice 4 implementation closure review 5

Outcome: **PASS**  
Reviewer runtime: `/root/v4_s4_design_adversary`  
Builder/coordinator: `/root`  
Base: `4840a0b4bc5d7334ddcf51a80e39c8fa84b7b0c2`  
Reviewed packet SHA-256: `b531efdaba8866893e8c0dcdb4d60f19922c87bfab95371892e455551ba9647a`

The reviewer verified the packet hash and all 23 implementation-manifest file
hashes, inspected staged, unstaged, and untracked scope plus relevant callers,
readers, SQL, migration paths, tests, and contracts, and made no repository
edits. No staged changes were present and `git diff --check` passed.

## Finding dispositions

### T081-V4-S4-IMPL-M-001 — closed

The obligation observation inherits the applicability parent's individual
preflight failure before child reconstruction can read that parent's audit
payload. Scalar projection identity, count, and byte metadata are collected
before full projection loading. Controlled nonverification returns before
reconstruction when the budget fails. The queue uses the same prepared
metadata and observation path after cumulative-budget checks.

The reviewer checked the exact-parent assumption: the database contract
requires the obligation's same-proposal applicability parent, matching parent
hash, and supported materializer version; proposal/materializer uniqueness
prevents another valid supported parent from bypassing dependency propagation.

The populated `obligation_count`, `parent_count`, and `parent_bytes` tests
passed. The reviewer also independently exercised real detail and queue readers
against persisted projections:

- parent-count overflow used three valid parent requests and one event while
  the child remained individually within budget;
- parent-byte overflow used eight valid parent requests totaling 2,679 audit
  bytes while the child's 1,405 bytes and source evidence remained within the
  selected test budget.

For both counterexamples, detail and queue returned matching input identities,
both parent and child were `integrity_error`, and ORM selection instrumentation
observed no projection request/event payload-byte columns, directly or through
child reconstruction.

### Previously closed findings

- T081-V4-S4-IMPL-H-003 remains closed. The current PostgreSQL run passed the
  near-ceiling lifecycle test through request, rejection, and successor. The
  independently verified exact two-byte-residual and corrupt stored-phase
  probes remain applicable to unchanged implementation.
- T081-V4-S4-IMPL-M-002 remains closed. The reviewer inspected the unchanged
  lock-order transformation, exact downgrade inverse, full inherited-function
  comparison, helper removal, and independent downgrade gates. The prior
  independent four-test fresh-database rollback run remains its execution
  evidence.
- T081-V4-S4-IMPL-B-001, H-001, and H-002 remain closed. Targeted inspection
  and current suites found no regression in SQL/Python observation parity,
  lock ordering, or allowlisted storage-error handling.

No new blocker, high, or medium finding was identified.

## Independent verification

- Host service/bounds/storage suites: **93 passed**.
- PostgreSQL migration, lock-order, and service suites: **86 passed**.
- Additional populated parent-count and parent-byte probes: passed for both
  detail and queue with zero prohibited projection payload selections.

## Gate conclusion

**PASS for the frozen rejection-only implementation vertical.** M-001 is
closed and no implementation blocker remains.

This does not approve the entire Slice 4 feature set. Acceptance, actionable
classification, reviewer UI, publication/current selection, supporting-document
admission, and V3 freeze behavior remain intentionally absent and outside this
approval.

```
### `.ai/review-runs/T081-V4-SCHEMA-SLICE-4/adversarial-closure-model-routing-fail-1.md`

size=1942; sha256=09bbf97073fd78bce3d9bc86193ff288c330a9ea56f37fdfb083b95766686e11

```text
# Model-routing closure re-attestation 1

Outcome: **FAIL**  
Reviewed packet SHA-256: `925a026b46eb21ccad27165caaa1f925856a66b2fbe4ecf9f8722866a583264c`

## Model routing

Reviewer runtime: `/root/model_policy_astra_closure`  
Actual reviewer model: `model not exposed by runtime`  
Actual reviewer effort: `effort not exposed`  
Requested assignment: `gpt-6-astra`, xhigh  
Trigger: closure re-attestation after two substantive failures in the
model-evidence/integration family.

## Findings

The packet was not ready for closure re-attestation or a shared commit:

1. The active run directory was excluded by the packet builder. Stable review
   inputs—the normative matrix, implementation verification, and eleven
   historical review reports—were not hash-bound. Mutable/generated review
   bookkeeping also lacked an explicit self-reference/append-only exception.
2. The frozen packet inferred `GPT-6 Astra` as the historical reviewer's actual
   model from assignment/checkpoint evidence. The reviewer subsequently
   reported `model not exposed by runtime` and `effort not exposed`, and the
   correction was outside the reviewed fingerprint.

Both findings are one recurring evidence/integration family. The required
third-loop response is a complete dirty-file inventory, explicit hash coverage
for stable files, narrowly defined generated/append-only exceptions, and one
fresh frozen packet.

## Preserved evidence

- All seven user policy requirements were present in the policy text.
- All 23 implementation files reproduced the prior implementation fingerprint
  `80d053ade74597cece7a50e70f160be350322a754ee1149c282234cafa0532e7`.
- All eleven recorded historical report hashes and the implementation
  verification hash remained unchanged.
- The original 17 Slice-4 findings remained closed.
- There were no staged or unexplained unrelated source changes, and
  `git diff --check` passed.

The reviewer made no file edits.

```

## Changed-file manifest

```json
{
  "taskId": "T081-V4-SCHEMA-SLICE-4",
  "stage": "closure",
  "generatedAt": "2026-09-14T12:38:22+00:00",
  "baseRef": "4840a0b4bc5d7334ddcf51a80e39c8fa84b7b0c2",
  "head": "4840a0b4bc5d7334ddcf51a80e39c8fa84b7b0c2",
  "scopePaths": [],
  "scopeFingerprint": "1085a6cdf0249c9ff8b398a100de0ad21df7d013a4b595b9514292b8910475d6",
  "files": [
    {
      "path": ".ai/MODEL_ROUTING.md",
      "status": "??",
      "size": 8400,
      "sha256": "8019680d63b13cf53206a1c75569954abb3793de8051b032237933a98567bd36",
      "readStatus": "readable"
    },
    {
      "path": "AGENTS.md",
      "status": " M",
      "size": 2214,
      "sha256": "2295cae2d1394c07fe3573d4d790985eb1b85c9a6514a94d851d55337f3fc0cb",
      "readStatus": "readable"
    },
    {
      "path": "backend/app/api/routes/ads.py",
      "status": " M",
      "size": 94318,
      "sha256": "34b23d0a891d081f014e58dba7b4a35f4c2a82b9b08f83b36327f5dca2e9c5fb",
      "readStatus": "readable"
    },
    {
      "path": "backend/app/contracts/ad_v4_slice4_rollout.md",
      "status": "??",
      "size": 2003,
      "sha256": "843192a2019d51dfa56eede6201ee4654c9ada4cd283095b024ee0d2ab32d4ed",
      "readStatus": "readable"
    },
    {
      "path": "backend/app/core/config.py",
      "status": " M",
      "size": 8652,
      "sha256": "e384665dcdad19d937cb6774247ed8f398ad13c568dd47872afc3d1f68b681fb",
      "readStatus": "readable"
    },
    {
      "path": "backend/app/db/migrations/sql/20260913_0029_review_case_integrity.sql",
      "status": "??",
      "size": 44538,
      "sha256": "92cc8cb8c73356f8194fe2e995c1ca7ba9892d88d07e17f4cea67cc34d39cf7e",
      "readStatus": "readable"
    },
    {
      "path": "backend/app/db/migrations/versions/20260913_0029_add_ad_v4_review_cases.py",
      "status": "??",
      "size": 15388,
      "sha256": "325277f7ffb8c9e100028c6f32e39263b0a336591b88634f641ed24737041a8f",
      "readStatus": "readable"
    },
    {
      "path": "backend/app/models/core.py",
      "status": " M",
      "size": 226329,
      "sha256": "be50bfb1009cd24b1787cf2ceeff1377e92a82c2825aaa74023dec74852ae7ac",
      "readStatus": "readable"
    },
    {
      "path": "backend/app/schemas/ads.py",
      "status": " M",
      "size": 18647,
      "sha256": "99f65097345b362be1d73a7adc950d834ef30678c67c23378cc3ba61151f86a0",
      "readStatus": "readable"
    },
    {
      "path": "backend/app/services/ad_extraction.py",
      "status": " M",
      "size": 92258,
      "sha256": "d0d3b4a345e59fcfe4b5cfb95b47739cd48f44d2333b43d5ca5cb1c8c29ea6db",
      "readStatus": "readable"
    },
    {
      "path": "backend/app/services/ad_v4_applicability.py",
      "status": " M",
      "size": 187308,
      "sha256": "8489dd259dad93f3c4eb0981c09e449333929f5388705e550b1323a8b25686ce",
      "readStatus": "readable"
    },
    {
      "path": "backend/app/services/ad_v4_candidates.py",
      "status": " M",
      "size": 72614,
      "sha256": "1956a092ff4be35cc2941654982b8aa6067ca43e888aff09c80190171f0414d9",
      "readStatus": "readable"
    },
    {
      "path": "backend/app/services/ad_v4_obligation_persistence.py",
      "status": " M",
      "size": 49705,
      "sha256": "4106b5e430ef3a0af774e4fbddabba567454f7e1c9087b0d4f23092072736fe7",
      "readStatus": "readable"
    },
    {
      "path": "backend/app/services/ad_v4_reviews.py",
      "status": "??",
      "size": 107024,
      "sha256": "c9811b48f063f943bedd4d06c34b19e0b9fb2d37888dffdbf154705bc3188a91",
      "readStatus": "readable"
    },
    {
      "path": "backend/app/services/storage.py",
      "status": " M",
      "size": 8518,
      "sha256": "326487b15a30d75904108c3ebcc6a5c4deb3e3b9211017fd680bfae461bbc37b",
      "readStatus": "readable"
    },
    {
      "path": "backend/tests/test_ad_v4_api.py",
      "status": " M",
      "size": 16055,
      "sha256": "092ca3334be1fb614fdda9cbc686c5362e48566756a7f9161190607f2cda2494",
      "readStatus": "readable"
    },
    {
      "path": "backend/tests/test_ad_v4_obligation_persistence_postgres.py",
      "status": " M",
      "size": 78348,
      "sha256": "c2ff98cce618d24f46458f6e1a2858e6d2ce8057e26832d3db96bcfe2f445015",
      "readStatus": "readable"
    },
    {
      "path": "backend/tests/test_ad_v4_postgres.py",
      "status": " M",
      "size": 43597,
      "sha256": "797240fbfb0801c7343b14426c815f03a35a1bb95fed9318bbc0b7cbbd342bfc",
      "readStatus": "readable"
    },
    {
      "path": "backend/tests/test_ad_v4_review_case_migration_postgres.py",
      "status": "??",
      "size": 43781,
      "sha256": "3070e1862b9ea42fb0f82ddd2dea6995ed2f4a067532d63d8ce17753fe2ef7bd",
      "readStatus": "readable"
    },
    {
      "path": "backend/tests/test_ad_v4_review_lock_order_postgres.py",
      "status": "??",
      "size": 10128,
      "sha256": "cb4ffe0efbaf0c2510bbfe9018aa1f8f87698e1d1efb872a8c34cf10a3886da9",
      "readStatus": "readable"
    },
    {
      "path": "backend/tests/test_ad_v4_review_rollout_postgres.py",
      "status": "??",
      "size": 5409,
      "sha256": "7545c7dfbdb8b3203538a85a0952d371484ea608243f7ad7966c5147b11ed1ba",
      "readStatus": "readable"
    },
    {
      "path": "backend/tests/test_ad_v4_review_service_bounds.py",
      "status": "??",
      "size": 48914,
      "sha256": "24abe2c6fdfa7770af063619b021a5bbd4295113a52aef05a3b7f57cb731072c",
      "readStatus": "readable"
    },
    {
      "path": "backend/tests/test_ad_v4_review_service_postgres.py",
      "status": "??",
      "size": 17001,
      "sha256": "c750ea96ee211756e64c2f33302a67ec5f80af7e2a59833457a1fa9e44571d1a",
      "readStatus": "readable"
    },
    {
      "path": "backend/tests/test_ad_v4_reviews.py",
      "status": "??",
      "size": 9179,
      "sha256": "40869d3de9dbd0ab830f18f9d75d01e464840369206498b688e15dba1eecb67e",
      "readStatus": "readable"
    },
    {
      "path": "backend/tests/test_storage.py",
      "status": " M",
      "size": 6468,
      "sha256": "6788e6c45a5c89da5a3297092c71dab18ecd29d5f053b4ce53e8c4a2efd4e33a",
      "readStatus": "readable"
    }
  ],
  "reviewInputs": [
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4/decision.md",
      "status": "review_input",
      "size": 39002,
      "sha256": "2c5a020540be5a996f0eb52edc6ea7f5cc1d8b359897d077cc9d297813de7971",
      "readStatus": "readable"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4/findings.json",
      "status": "review_input",
      "size": 30763,
      "sha256": "7ac4836cd873629202bf52eddb3cef8bc2c0865db806f341aef2e1787acf77f5",
      "readStatus": "readable"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4/closure.md",
      "status": "review_input",
      "size": 8444,
      "sha256": "14b8e50fe63d9802f58eb7e164673f69f4e26b673c1829a355ebb764ade281fe",
      "readStatus": "readable"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4/normative-gate-and-form-matrix.md",
      "status": "review_input",
      "size": 32650,
      "sha256": "1d38a293ab03dfc0664e1a01a43f563c10f404d18355e6c4859709dd5b23c3be",
      "readStatus": "readable"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4/implementation-verification.md",
      "status": "review_input",
      "size": 5601,
      "sha256": "33645eb503bef33198bfe86c1069df16bf7df8d19e36a93fdc9549d3368fce0b",
      "readStatus": "readable"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4/model-routing-policy-integration.md",
      "status": "review_input",
      "size": 4915,
      "sha256": "e9426dc98a0902191dc0b1df202efd060c7c47d49d706b592e8c2829b70a51e6",
      "readStatus": "readable"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4/model-routing-policy-metadata-supplement.md",
      "status": "review_input",
      "size": 1118,
      "sha256": "87d3146756ae2c7db3d4e5a93780b8ae02d78afaa5504739559c4afe8cc2ce75",
      "readStatus": "readable"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4/adversarial-closure-final.md",
      "status": "review_input",
      "size": 3182,
      "sha256": "e575abc57f92f7f553b465f552d2f9e09338fbe1ef734e14e306cb4bfa005199",
      "readStatus": "readable"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4/adversarial-design-initial.md",
      "status": "review_input",
      "size": 7751,
      "sha256": "15f53fdea19ca5b52c8af9b648ef29afcd65ce28df9e95230a4c1bd14dbdf096",
      "readStatus": "readable"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4/adversarial-design-closure-1.md",
      "status": "review_input",
      "size": 1379,
      "sha256": "b1b3d7ed54f2bcbe208fb28a9b3832f804937600723c796238a2426c72fd886b",
      "readStatus": "readable"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4/adversarial-design-closure-2.md",
      "status": "review_input",
      "size": 1022,
      "sha256": "1144533313869e4644e5aa2226f7b092d931b7c93beb7d536dc67dff1bae9125",
      "readStatus": "readable"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4/adversarial-design-final.md",
      "status": "review_input",
      "size": 1278,
      "sha256": "69803af2288fdc51c7936137aafb028d3a04a4665a58aeb52bb6dc7bc3b7eb53",
      "readStatus": "readable"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4/adversarial-implementation-initial.md",
      "status": "review_input",
      "size": 1868,
      "sha256": "864950e0ed8b64d85f17acf177147ef016ab7061b9efbb67ec59fad46139f535",
      "readStatus": "readable"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4/adversarial-implementation-closure-1.md",
      "status": "review_input",
      "size": 2894,
      "sha256": "c62a02782b3c078258a71d6f9cbbc03f95c63a05e6de843bbaebd16b690e9092",
      "readStatus": "readable"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4/adversarial-implementation-closure-2.md",
      "status": "review_input",
      "size": 3921,
      "sha256": "87bd237f19dfeeb01b7176324c81b38d13b5d6e2782707d11e6e3daeb5b06b5a",
      "readStatus": "readable"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4/adversarial-implementation-closure-3.md",
      "status": "review_input",
      "size": 2618,
      "sha256": "9ce64726a703480bb22b7758cc7fd3d8f900d0aeb31794b855fc4f646eee7771",
      "readStatus": "readable"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4/adversarial-implementation-closure-4.md",
      "status": "review_input",
      "size": 1737,
      "sha256": "12bcf21165e0f9179d10278041c25c0bb636138fe180b27875292ca4b598f6bd",
      "readStatus": "readable"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4/adversarial-implementation-closure-5.md",
      "status": "review_input",
      "size": 3746,
      "sha256": "093f85e5a5c7df8add7b194dbe5c15381f9b6cb580c7f9269f6f332461b4730e",
      "readStatus": "readable"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4/adversarial-closure-model-routing-fail-1.md",
      "status": "review_input",
      "size": 1942,
      "sha256": "09bbf97073fd78bce3d9bc86193ff288c330a9ea56f37fdfb083b95766686e11",
      "readStatus": "readable"
    }
  ],
  "outOfScopeDirtyFiles": [],
  "outOfScopeReason": null
}
```

## Diff against base

```diff
diff --git a/AGENTS.md b/AGENTS.md
index 49ae914..4bf3d52 100644
--- a/AGENTS.md
+++ b/AGENTS.md
@@ -1,5 +1,14 @@
 # Paprnav agent workflow
 
+## Mandatory model routing
+
+Route every meaningful phase by risk, complexity, and review history according
+to [`.ai/MODEL_ROUTING.md`](.ai/MODEL_ROUTING.md). At phase start and whenever
+role, model, or effort changes, emit the required model-routing notice. Preserve
+builder/reviewer separation, record known assignments in review artifacts, and
+apply the documented escalation and fallback rules without silently claiming
+an unavailable model.
+
 Use the adversarial review process for changes involving regulatory or safety
 semantics, schemas or migrations, authorization, audit evidence, destructive
 data operations, provider/billing decisions, infrastructure/IAM, or public API
diff --git a/backend/app/api/routes/ads.py b/backend/app/api/routes/ads.py
index cfed88a..442e566 100644
--- a/backend/app/api/routes/ads.py
+++ b/backend/app/api/routes/ads.py
@@ -61,6 +61,13 @@ from app.schemas.ads import (
     ADV4ObligationProjectionListResponse,
     ADV4ObligationProjectionResponse,
     ADV4ObligationReconstructionResponse,
+    ADV4ReviewCaseCreateRequest,
+    ADV4ReviewCaseListResponse,
+    ADV4ReviewCaseResponse,
+    ADV4ReviewDraftCreateRequest,
+    ADV4ReviewRejectRequest,
+    ADV4ReviewRequestCreateRequest,
+    ADV4ReviewProposalObservationResponse,
     ADV4SubmissionAuditResponse,
     ADV4SubmissionRelationshipAuditResponse,
     ADProposalProvenanceResponse,
@@ -142,6 +149,15 @@ from app.services.ad_v4_obligation_persistence import (
     verified_obligation_projection,
 )
 from app.services.ad_v4_obligations import ObligationIntegrityError
+from app.services.ad_v4_reviews import (
+    create_review_case,
+    list_review_cases,
+    reject_review_case,
+    review_proposal_observation,
+    request_review,
+    save_review_draft,
+    verified_review_case,
+)
 from app.services.ad_recurrence import due_state_payload
 from app.services.installed_components import component_display_name
 from app.services.observability import record_product_event, record_workflow_status
@@ -212,6 +228,25 @@ def v4_http_error(exc: ADV4Error) -> HTTPException:
     )
 
 
+def _candidate_database_error(exc: DBAPIError) -> ADV4Error | None:
+    sqlstate = getattr(exc.orig, "sqlstate", None)
+    if sqlstate == "P0001" or (
+        isinstance(sqlstate, str) and sqlstate.startswith("23")
+    ):
+        return ADV4Error(
+            "candidate_integrity", "",
+            "PostgreSQL rejected the candidate transaction",
+            http_status=409,
+        )
+    if sqlstate in {"40P01", "40001", "57014", "55P03"}:
+        return ADV4Error(
+            "transaction_conflict", "",
+            "Candidate transaction must be retried",
+            http_status=409,
+        )
+    return None
+
+
 def _obligation_database_error(exc: DBAPIError) -> ADV4Error | None:
     sqlstate = getattr(exc.orig, "sqlstate", None)
     if sqlstate == "P0001" or (
@@ -231,6 +266,25 @@ def _obligation_database_error(exc: DBAPIError) -> ADV4Error | None:
     return None
 
 
+def _review_database_error(exc: DBAPIError) -> ADV4Error | None:
+    sqlstate = getattr(exc.orig, "sqlstate", None)
+    if sqlstate == "P0001" or (
+        isinstance(sqlstate, str) and sqlstate.startswith("23")
+    ):
+        return ADV4Error(
+            "review_integrity", "",
+            "PostgreSQL rejected the V4 review transaction",
+            http_status=409,
+        )
+    if sqlstate in {"40P01", "40001", "57014", "55P03"}:
+        return ADV4Error(
+            "transaction_conflict", "",
+            "V4 review transaction must be retried",
+            http_status=409,
+        )
+    return None
+
+
 def serialize_v4_candidate(
     proposal: ADV4CandidateProposal,
     submission: ADV4CandidateSubmission,
@@ -363,6 +417,12 @@ async def create_v4_candidate_proposal(
     except ADV4Error as exc:
         db.rollback()
         raise v4_http_error(exc) from exc
+    except DBAPIError as exc:
+        db.rollback()
+        translated = _candidate_database_error(exc)
+        if translated is None:
+            raise
+        raise v4_http_error(translated) from exc
     if stored.idempotent_retry or stored.content_reused:
         response.status_code = status.HTTP_200_OK
     return serialize_v4_candidate(
@@ -835,6 +895,310 @@ def list_v4_obligation_projections(
         raise v4_http_error(translated) from exc
 
 
+@router.get(
+    "/directives/{directive_id}/v4/candidate-proposals/{proposal_id}/review-observation",
+    response_model=ADV4ReviewProposalObservationResponse,
+    response_model_exclude_none=True,
+)
+def get_v4_review_proposal_observation(
+    directive_id: str,
+    proposal_id: str,
+    acting_membership_id: str = Header(
+        alias="Paprnav-Acting-Membership-Id", min_length=1, max_length=36,
+    ),
+    current_user: User = Depends(get_current_user),
+    db: Session = Depends(get_db),
+) -> ADV4ReviewProposalObservationResponse:
+    try:
+        with repeatable_read_only_session(db.get_bind()) as read_db:
+            result = review_proposal_observation(
+                read_db,
+                directive_id=directive_id,
+                proposal_id=proposal_id,
+                actor=current_user,
+                membership_id=acting_membership_id,
+            )
+            return ADV4ReviewProposalObservationResponse(**result)
+    except ADV4Error as exc:
+        raise v4_http_error(exc) from exc
+    except DBAPIError as exc:
+        translated = _review_database_error(exc)
+        if translated is None:
+            raise
+        raise v4_http_error(translated) from exc
+
+
+@router.post(
+    "/directives/{directive_id}/v4/candidate-proposals/{proposal_id}/review-cases",
+    response_model=ADV4ReviewCaseResponse,
+    response_model_exclude_none=True,
+    status_code=status.HTTP_201_CREATED,
+)
+def create_v4_review_case(
+    directive_id: str,
+    proposal_id: str,
+    request: ADV4ReviewCaseCreateRequest,
+    response: Response,
+    idempotency_key: str = Header(
+        alias="Idempotency-Key", min_length=1, max_length=255,
+    ),
+    acting_membership_id: str = Header(
+        alias="Paprnav-Acting-Membership-Id", min_length=1, max_length=36,
+    ),
+    current_user: User = Depends(get_current_user),
+    db: Session = Depends(get_db),
+) -> ADV4ReviewCaseResponse:
+    try:
+        result = create_review_case(
+            db,
+            directive_id=directive_id,
+            proposal_id=proposal_id,
+            actor=current_user,
+            membership_id=acting_membership_id,
+            idempotency_key=idempotency_key,
+            expected_authorization_observation_hash=(
+                request.expectedAuthorizationObservationHash
+            ),
+            expected_input_identity_hash=request.expectedInputIdentityHash,
+        )
+        db.commit()
+        if result.get("idempotentRetry"):
+            response.status_code = status.HTTP_200_OK
+        return ADV4ReviewCaseResponse(**result)
+    except ADV4Error as exc:
+        db.rollback()
+        raise v4_http_error(exc) from exc
+    except DBAPIError as exc:
+        db.rollback()
+        translated = _review_database_error(exc)
+        if translated is None:
+            raise
+        raise v4_http_error(translated) from exc
+
+
+@router.post(
+    "/v4/review-cases/{case_id}/drafts",
+    response_model=ADV4ReviewCaseResponse,
+    response_model_exclude_none=True,
+    status_code=status.HTTP_201_CREATED,
+)
+def save_v4_review_draft(
+    case_id: str,
+    request: ADV4ReviewDraftCreateRequest,
+    response: Response,
+    idempotency_key: str = Header(
+        alias="Idempotency-Key", min_length=1, max_length=255,
+    ),
+    acting_membership_id: str = Header(
+        alias="Paprnav-Acting-Membership-Id", min_length=1, max_length=36,
+    ),
+    current_user: User = Depends(get_current_user),
+    db: Session = Depends(get_db),
+) -> ADV4ReviewCaseResponse:
+    try:
+        result = save_review_draft(
+            db,
+            case_id=case_id,
+            actor=current_user,
+            membership_id=acting_membership_id,
+            idempotency_key=idempotency_key,
+            expected_authorization_observation_hash=(
+                request.expectedAuthorizationObservationHash
+            ),
+            expected_input_identity_hash=request.expectedInputIdentityHash,
+            expected_predecessor_event_hash=request.expectedPredecessorEventHash,
+            annotations=[item.model_dump() for item in request.annotations],
+            intended_action=request.intendedAction,
+        )
+        db.commit()
+        if result.get("idempotentRetry"):
+            response.status_code = status.HTTP_200_OK
+        return ADV4ReviewCaseResponse(**result)
+    except ADV4Error as exc:
+        db.rollback()
+        raise v4_http_error(exc) from exc
+    except DBAPIError as exc:
+        db.rollback()
+        translated = _review_database_error(exc)
+        if translated is None:
+            raise
+        raise v4_http_error(translated) from exc
+
+
+@router.post(
+    "/v4/review-cases/{case_id}/review-request",
+    response_model=ADV4ReviewCaseResponse,
+    response_model_exclude_none=True,
+    status_code=status.HTTP_201_CREATED,
+)
+def request_v4_review(
+    case_id: str,
+    request: ADV4ReviewRequestCreateRequest,
+    response: Response,
+    idempotency_key: str = Header(
+        alias="Idempotency-Key", min_length=1, max_length=255,
+    ),
+    acting_membership_id: str = Header(
+        alias="Paprnav-Acting-Membership-Id", min_length=1, max_length=36,
+    ),
+    current_user: User = Depends(get_current_user),
+    db: Session = Depends(get_db),
+) -> ADV4ReviewCaseResponse:
+    try:
+        result = request_review(
+            db,
+            case_id=case_id,
+            actor=current_user,
+            membership_id=acting_membership_id,
+            idempotency_key=idempotency_key,
+            expected_authorization_observation_hash=(
+                request.expectedAuthorizationObservationHash
+            ),
+            expected_input_identity_hash=request.expectedInputIdentityHash,
+            expected_predecessor_event_hash=request.expectedPredecessorEventHash,
+            draft_revision_id=request.draftRevisionId,
+        )
+        db.commit()
+        if result.get("idempotentRetry"):
+            response.status_code = status.HTTP_200_OK
+        return ADV4ReviewCaseResponse(**result)
+    except ADV4Error as exc:
+        db.rollback()
+        raise v4_http_error(exc) from exc
+    except DBAPIError as exc:
+        db.rollback()
+        translated = _review_database_error(exc)
+        if translated is None:
+            raise
+        raise v4_http_error(translated) from exc
+
+
+@router.post(
+    "/v4/review-cases/{case_id}/rejection",
+    response_model=ADV4ReviewCaseResponse,
+    response_model_exclude_none=True,
+    status_code=status.HTTP_201_CREATED,
+)
+def reject_v4_review(
+    case_id: str,
+    request: ADV4ReviewRejectRequest,
+    response: Response,
+    idempotency_key: str = Header(
+        alias="Idempotency-Key", min_length=1, max_length=255,
+    ),
+    acting_membership_id: str = Header(
+        alias="Paprnav-Acting-Membership-Id", min_length=1, max_length=36,
+    ),
+    current_user: User = Depends(get_current_user),
+    db: Session = Depends(get_db),
+) -> ADV4ReviewCaseResponse:
+    try:
+        result = reject_review_case(
+            db,
+            case_id=case_id,
+            actor=current_user,
+            membership_id=acting_membership_id,
+            idempotency_key=idempotency_key,
+            expected_authorization_observation_hash=(
+                request.expectedAuthorizationObservationHash
+            ),
+            expected_input_identity_hash=request.expectedInputIdentityHash,
+            expected_predecessor_event_hash=request.expectedPredecessorEventHash,
+            expected_request_id=request.expectedRequestId,
+            reason_codes=request.reasonCodes,
+            explanation=request.explanation,
+        )
+        db.commit()
+        if result.get("idempotentRetry"):
+            response.status_code = status.HTTP_200_OK
+        return ADV4ReviewCaseResponse(**result)
+    except ADV4Error as exc:
+        db.rollback()
+        raise v4_http_error(exc) from exc
+    except DBAPIError as exc:
+        db.rollback()
+        translated = _review_database_error(exc)
+        if translated is None:
+            raise
+        raise v4_http_error(translated) from exc
+
+
+@router.get(
+    "/v4/review-cases/{case_id}",
+    response_model=ADV4ReviewCaseResponse,
+    response_model_exclude_none=True,
+)
+def get_v4_review_case(
+    case_id: str,
+    draft_limit: int = Query(default=100, ge=1, le=100, alias="draftLimit"),
+    draft_offset: int = Query(default=0, ge=0, le=10000, alias="draftOffset"),
+    event_limit: int = Query(default=100, ge=1, le=100, alias="eventLimit"),
+    event_offset: int = Query(default=0, ge=0, le=10000, alias="eventOffset"),
+    acting_membership_id: str = Header(
+        alias="Paprnav-Acting-Membership-Id", min_length=1, max_length=36,
+    ),
+    current_user: User = Depends(get_current_user),
+    db: Session = Depends(get_db),
+) -> ADV4ReviewCaseResponse:
+    try:
+        with repeatable_read_only_session(db.get_bind()) as read_db:
+            result = verified_review_case(
+                read_db,
+                case_id=case_id,
+                actor=current_user,
+                membership_id=acting_membership_id,
+                draft_limit=draft_limit,
+                draft_offset=draft_offset,
+                event_limit=event_limit,
+                event_offset=event_offset,
+            )
+            return ADV4ReviewCaseResponse(**result)
+    except ADV4Error as exc:
+        raise v4_http_error(exc) from exc
+    except DBAPIError as exc:
+        translated = _review_database_error(exc)
+        if translated is None:
+            raise
+        raise v4_http_error(translated) from exc
+
+
+@router.get(
+    "/v4/review-cases",
+    response_model=ADV4ReviewCaseListResponse,
+    response_model_exclude_none=True,
+)
+def list_v4_review_cases(
+    directive_id: str | None = Query(default=None, alias="directiveId"),
+    proposal_id: str | None = Query(default=None, alias="proposalId"),
+    limit: int = Query(default=25, ge=1, le=100),
+    offset: int = Query(default=0, ge=0),
+    acting_membership_id: str = Header(
+        alias="Paprnav-Acting-Membership-Id", min_length=1, max_length=36,
+    ),
+    current_user: User = Depends(get_current_user),
+    db: Session = Depends(get_db),
+) -> ADV4ReviewCaseListResponse:
+    try:
+        with repeatable_read_only_session(db.get_bind()) as read_db:
+            result = list_review_cases(
+                read_db,
+                actor=current_user,
+                membership_id=acting_membership_id,
+                directive_id=directive_id,
+                proposal_id=proposal_id,
+                limit=limit,
+                offset=offset,
+            )
+            return ADV4ReviewCaseListResponse(**result)
+    except ADV4Error as exc:
+        raise v4_http_error(exc) from exc
+    except DBAPIError as exc:
+        translated = _review_database_error(exc)
+        if translated is None:
+            raise
+        raise v4_http_error(translated) from exc
+
+
 @router.get(
     "/source-documents/{source_document_id}/pages/{page_number}",
     response_model=ADSourcePageEvidenceResponse,
diff --git a/backend/app/core/config.py b/backend/app/core/config.py
index fe7eaee..256c3cd 100644
--- a/backend/app/core/config.py
+++ b/backend/app/core/config.py
@@ -85,6 +85,9 @@ class Settings:
     ad_v4_validator2_writes_enabled: bool = False
     ad_v4_slice3a_routes_enabled: bool = False
     ad_v4_slice3b_routes_enabled: bool = False
+    ad_v4_slice4_reads_enabled: bool = False
+    ad_v4_slice4_drafts_enabled: bool = False
+    ad_v4_slice4_decisions_enabled: bool = False
 
 
 def parse_bool(value: Optional[str], default: bool = False) -> bool:
@@ -188,4 +191,13 @@ def get_settings() -> Settings:
         ad_v4_slice3b_routes_enabled=parse_bool(
             os.getenv("PAPRNAV_AD_V4_SLICE3B_ROUTES_ENABLED")
         ),
+        ad_v4_slice4_reads_enabled=parse_bool(
+            os.getenv("PAPRNAV_AD_V4_SLICE4_READS_ENABLED")
+        ),
+        ad_v4_slice4_drafts_enabled=parse_bool(
+            os.getenv("PAPRNAV_AD_V4_SLICE4_DRAFTS_ENABLED")
+        ),
+        ad_v4_slice4_decisions_enabled=parse_bool(
+            os.getenv("PAPRNAV_AD_V4_SLICE4_DECISIONS_ENABLED")
+        ),
     )
diff --git a/backend/app/models/core.py b/backend/app/models/core.py
index ee05e9c..398c2dd 100644
--- a/backend/app/models/core.py
+++ b/backend/app/models/core.py
@@ -3068,3 +3068,177 @@ class WorkflowStatusEvent(Base):
     created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
 
     actor = relationship("User", foreign_keys=[actor_user_id])
+
+
+MAX_CASES_PER_PROPOSAL = 100
+MAX_DRAFT_REVISIONS_PER_CASE = 1000
+MAX_EVENTS_PER_CASE = 1003
+MAX_DRAFT_AUTHORITATIVE_BYTES_PER_CASE = 16 * 1024 * 1024
+MAX_REQUESTED_AUTHORITATIVE_BYTES_PER_CASE = 28 * 1024 * 1024
+MAX_AUTHORITATIVE_BYTES_PER_CASE = 40 * 1024 * 1024
+
+
+class _ADV4ReviewRecord:
+    """Immutable review record. Database validators own the commit boundary."""
+
+    id: Mapped[str] = mapped_column(String(36), primary_key=True)
+    proposal_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_proposals.id", ondelete="RESTRICT"), nullable=False)
+    directive_id: Mapped[str] = mapped_column(ForeignKey("airworthiness_directives.id", ondelete="RESTRICT"), nullable=False)
+    actor_user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
+    authorizing_membership_id: Mapped[str] = mapped_column(ForeignKey("organization_memberships.id", ondelete="RESTRICT"), nullable=False)
+    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False)
+    auth_snapshot_bytes: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
+    auth_snapshot_hash: Mapped[str] = mapped_column(String(64), nullable=False)
+    auth_policy_version: Mapped[str] = mapped_column(String(64), nullable=False)
+    endpoint_action: Mapped[str] = mapped_column(String(96), nullable=False)
+    idempotency_key: Mapped[str] = mapped_column(String(255), nullable=False)
+    request_canonical_bytes: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
+    request_hash: Mapped[str] = mapped_column(String(64), nullable=False)
+    contract_version: Mapped[str] = mapped_column(String(64), nullable=False)
+    canonical_bytes: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
+
+
+class _ADV4ReviewObservation:
+    input_identity_bytes: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
+    input_identity_hash: Mapped[str] = mapped_column(String(64), nullable=False)
+    observation_bytes: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
+    observation_hash: Mapped[str] = mapped_column(String(64), nullable=False)
+    observed_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)
+
+
+class ADV4ReviewCase(_ADV4ReviewRecord, _ADV4ReviewObservation, Base):
+    __tablename__ = "ad_v4_review_cases"
+    proposal_canonical_hash: Mapped[str] = mapped_column(String(64), nullable=False)
+    case_sequence: Mapped[int] = mapped_column(Integer, nullable=False)
+    predecessor_case_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
+    row_hash: Mapped[str] = mapped_column(String(64), nullable=False)
+    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)
+
+
+class ADV4ReviewDraftRevision(_ADV4ReviewRecord, _ADV4ReviewObservation, Base):
+    __tablename__ = "ad_v4_review_draft_revisions"
+    case_id: Mapped[str] = mapped_column(String(36), nullable=False)
+    revision_number: Mapped[int] = mapped_column(Integer, nullable=False)
+    predecessor_draft_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
+    expected_predecessor_event_hash: Mapped[str] = mapped_column(String(64), nullable=False)
+    annotation_bytes: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
+    annotation_hash: Mapped[str] = mapped_column(String(64), nullable=False)
+    intended_action: Mapped[str] = mapped_column(String(32), nullable=False)
+    row_hash: Mapped[str] = mapped_column(String(64), nullable=False)
+    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)
+
+
+class ADV4ReviewRequest(_ADV4ReviewRecord, _ADV4ReviewObservation, Base):
+    __tablename__ = "ad_v4_review_requests"
+    case_id: Mapped[str] = mapped_column(String(36), nullable=False)
+    draft_revision_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
+    expected_predecessor_event_hash: Mapped[str] = mapped_column(String(64), nullable=False)
+    cutoff_bytes: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
+    cutoff_hash: Mapped[str] = mapped_column(String(64), nullable=False)
+    authorship_set_bytes: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
+    authorship_set_hash: Mapped[str] = mapped_column(String(64), nullable=False)
+    authorship_source_count: Mapped[int] = mapped_column(Integer, nullable=False)
+    row_hash: Mapped[str] = mapped_column(String(64), nullable=False)
+    requested_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)
+
+
+class ADV4ReviewRejection(_ADV4ReviewRecord, Base):
+    __tablename__ = "ad_v4_review_rejections"
+    case_id: Mapped[str] = mapped_column(String(36), nullable=False)
+    request_id: Mapped[str] = mapped_column(String(36), nullable=False)
+    proposal_canonical_hash: Mapped[str] = mapped_column(String(64), nullable=False)
+    requested_input_identity_hash: Mapped[str] = mapped_column(String(64), nullable=False)
+    requested_observation_hash: Mapped[str] = mapped_column(String(64), nullable=False)
+    decision_input_identity_bytes: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
+    decision_input_identity_hash: Mapped[str] = mapped_column(String(64), nullable=False)
+    decision_observation_bytes: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
+    decision_observation_hash: Mapped[str] = mapped_column(String(64), nullable=False)
+    decision_observed_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)
+    reasons_bytes: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
+    reasons_hash: Mapped[str] = mapped_column(String(64), nullable=False)
+    expected_predecessor_event_hash: Mapped[str] = mapped_column(String(64), nullable=False)
+    row_hash: Mapped[str] = mapped_column(String(64), nullable=False)
+    rejected_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)
+
+
+class ADV4SignoffEvent(_ADV4ReviewRecord, Base):
+    __tablename__ = "ad_v4_signoff_events"
+    case_id: Mapped[str] = mapped_column(String(36), nullable=False)
+    request_id: Mapped[str] = mapped_column(String(36), nullable=False)
+    rejection_id: Mapped[str] = mapped_column(String(36), nullable=False)
+    action: Mapped[str] = mapped_column(String(32), nullable=False)
+    rejection_hash: Mapped[str] = mapped_column(String(64), nullable=False)
+    requested_input_identity_hash: Mapped[str] = mapped_column(String(64), nullable=False)
+    requested_observation_hash: Mapped[str] = mapped_column(String(64), nullable=False)
+    decision_input_identity_hash: Mapped[str] = mapped_column(String(64), nullable=False)
+    decision_observation_hash: Mapped[str] = mapped_column(String(64), nullable=False)
+    authorization_observation_hash: Mapped[str] = mapped_column(String(64), nullable=False)
+    signature_hash: Mapped[str] = mapped_column(String(64), nullable=False)
+    row_hash: Mapped[str] = mapped_column(String(64), nullable=False)
+    signed_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)
+
+
+class ADV4ReviewCaseEvent(_ADV4ReviewRecord, Base):
+    __tablename__ = "ad_v4_review_case_events"
+    case_id: Mapped[str] = mapped_column(String(36), nullable=False)
+    sequence_number: Mapped[int] = mapped_column(Integer, nullable=False)
+    predecessor_event_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
+    event_type: Mapped[str] = mapped_column(String(32), nullable=False)
+    resulting_state: Mapped[str] = mapped_column(String(32), nullable=False)
+    draft_revision_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
+    review_request_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
+    rejection_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
+    signoff_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
+    auth_policy_version: Mapped[str] = mapped_column(String(64), nullable=False)
+    endpoint_action: Mapped[str] = mapped_column(String(96), nullable=False)
+    idempotency_key: Mapped[str] = mapped_column(String(255), nullable=False)
+    request_canonical_bytes: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
+    request_hash: Mapped[str] = mapped_column(String(64), nullable=False)
+    event_hash: Mapped[str] = mapped_column(String(64), nullable=False)
+    occurred_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)
+
+
+def _install_ad_v4_review_model_constraints() -> None:
+    tables = (ADV4ReviewCase.__table__, ADV4ReviewDraftRevision.__table__, ADV4ReviewRequest.__table__, ADV4ReviewRejection.__table__, ADV4SignoffEvent.__table__, ADV4ReviewCaseEvent.__table__)
+    for ordinal, table in enumerate(tables):
+        table.append_constraint(CheckConstraint("contract_version='paprnav-ad-v4-candidate-review-1'", name=f"ck_ar4_{ordinal}_version"))
+        table.append_constraint(UniqueConstraint("id", "proposal_id", "directive_id", name=f"uq_ar4_{ordinal}_identity"))
+        if ordinal:
+            table.append_constraint(UniqueConstraint("id", "case_id", name=f"uq_ar4_{ordinal}_case_identity"))
+            table.append_constraint(ForeignKeyConstraint(["case_id", "proposal_id", "directive_id"], ["ad_v4_review_cases.id", "ad_v4_review_cases.proposal_id", "ad_v4_review_cases.directive_id"], name=f"fk_ar4_{ordinal}_case", ondelete="RESTRICT", deferrable=True, initially="DEFERRED"))
+        for column in table.c:
+            if column.name.endswith("_hash"):
+                table.append_constraint(CheckConstraint(f"length({column.name})=64", name=f"ck_ar4_{ordinal}_{column.name}"))
+            elif column.name.endswith("_bytes"):
+                table.append_constraint(CheckConstraint(f"length({column.name}) BETWEEN 2 AND 1048576", name=f"ck_ar4_{ordinal}_{column.name}"))
+    tables[0].append_constraint(UniqueConstraint("proposal_id", "case_sequence", name="uq_ar4_case_sequence"))
+    tables[0].append_constraint(CheckConstraint(f"case_sequence BETWEEN 0 AND {MAX_CASES_PER_PROPOSAL - 1}", name="ck_ar4_case_capacity"))
+    Index("ix_ar4_case_queue", tables[0].c.created_at, tables[0].c.id)
+    Index("ix_ar4_case_directive", tables[0].c.directive_id, tables[0].c.created_at, tables[0].c.id)
+    tables[0].append_constraint(CheckConstraint("(case_sequence=0 AND predecessor_case_id IS NULL) OR (case_sequence>0 AND predecessor_case_id IS NOT NULL)", name="ck_ar4_case_predecessor"))
+    tables[0].append_constraint(ForeignKeyConstraint(["predecessor_case_id", "proposal_id", "directive_id"], ["ad_v4_review_cases.id", "ad_v4_review_cases.proposal_id", "ad_v4_review_cases.directive_id"], name="fk_ar4_case_predecessor", ondelete="RESTRICT", deferrable=True, initially="DEFERRED"))
+    tables[1].append_constraint(UniqueConstraint("case_id", "revision_number", name="uq_ar4_draft_revision"))
+    tables[1].append_constraint(CheckConstraint(f"revision_number BETWEEN 0 AND {MAX_DRAFT_REVISIONS_PER_CASE - 1}", name="ck_ar4_draft_capacity"))
+    tables[1].append_constraint(CheckConstraint("(revision_number=0 AND predecessor_draft_id IS NULL) OR (revision_number>0 AND predecessor_draft_id IS NOT NULL)", name="ck_ar4_draft_predecessor"))
+    tables[1].append_constraint(CheckConstraint("intended_action IN ('undecided','reject')", name="ck_ar4_draft_intent"))
+    for ordinal in (2, 3, 4):
+        tables[ordinal].append_constraint(UniqueConstraint("case_id", name=f"uq_ar4_{ordinal}_one_per_case"))
+    tables[2].append_constraint(CheckConstraint("authorship_source_count>=0", name="ck_ar4_request_authorship_count"))
+    tables[3].append_constraint(UniqueConstraint("request_id", name="uq_ar4_rejection_request"))
+    tables[4].append_constraint(UniqueConstraint("rejection_id", name="uq_ar4_signoff_rejection"))
+    tables[4].append_constraint(CheckConstraint("action='reject'", name="ck_ar4_signoff_action"))
+    refs = ((1, "predecessor_draft_id", 1), (2, "draft_revision_id", 1), (3, "request_id", 2), (4, "request_id", 2), (4, "rejection_id", 3), (5, "draft_revision_id", 1), (5, "review_request_id", 2), (5, "rejection_id", 3), (5, "signoff_id", 4))
+    for ordinal, column, target in refs:
+        tables[ordinal].append_constraint(ForeignKeyConstraint([column, "case_id"], [f"{tables[target].name}.id", f"{tables[target].name}.case_id"], name=f"fk_ar4_{ordinal}_{column}", ondelete="RESTRICT", deferrable=True, initially="DEFERRED"))
+    events = tables[5]
+    events.append_constraint(UniqueConstraint("case_id", "sequence_number", name="uq_ar4_event_sequence"))
+    events.append_constraint(CheckConstraint(f"sequence_number BETWEEN 0 AND {MAX_EVENTS_PER_CASE - 1}", name="ck_ar4_event_capacity"))
+    events.append_constraint(UniqueConstraint("case_id", "event_hash", name="uq_ar4_event_hash"))
+    events.append_constraint(UniqueConstraint("case_id", "predecessor_event_hash", name="uq_ar4_event_predecessor"))
+    events.append_constraint(UniqueConstraint("actor_user_id", "authorizing_membership_id", "endpoint_action", "auth_policy_version", "idempotency_key", name="uq_ar4_event_idempotency"))
+    events.append_constraint(CheckConstraint("(sequence_number=0 AND predecessor_event_hash IS NULL AND event_type='case_created') OR (sequence_number>0 AND predecessor_event_hash IS NOT NULL AND event_type<>'case_created')", name="ck_ar4_event_predecessor"))
+    events.append_constraint(CheckConstraint("(event_type='case_created' AND resulting_state='draft' AND draft_revision_id IS NULL AND review_request_id IS NULL AND rejection_id IS NULL AND signoff_id IS NULL) OR (event_type='draft_saved' AND resulting_state='draft' AND draft_revision_id IS NOT NULL AND review_request_id IS NULL AND rejection_id IS NULL AND signoff_id IS NULL) OR (event_type='review_requested' AND resulting_state='pending_review' AND draft_revision_id IS NULL AND review_request_id IS NOT NULL AND rejection_id IS NULL AND signoff_id IS NULL) OR (event_type='review_rejected' AND resulting_state='rejected' AND draft_revision_id IS NULL AND review_request_id IS NOT NULL AND rejection_id IS NOT NULL AND signoff_id IS NOT NULL)", name="ck_ar4_event_union"))
+    Index("uq_ar4_terminal", events.c.case_id, unique=True, postgresql_where=text("event_type='review_rejected'"), sqlite_where=text("event_type='review_rejected'"))
+
+
+_install_ad_v4_review_model_constraints()
diff --git a/backend/app/schemas/ads.py b/backend/app/schemas/ads.py
index bb74c33..9cb7871 100644
--- a/backend/app/schemas/ads.py
+++ b/backend/app/schemas/ads.py
@@ -1,5 +1,5 @@
 from datetime import date, datetime
-from typing import Any, Optional
+from typing import Any, Literal, Optional
 
 from pydantic import BaseModel, Field
 
@@ -288,6 +288,243 @@ class ADV4ObligationReconstructionResponse(BaseModel):
     authPolicyVersion: str
 
 
+class ADV4ReviewCaseCreateRequest(BaseModel):
+    model_config = {"extra": "forbid"}
+
+    expectedAuthorizationObservationHash: str = Field(
+        min_length=64, max_length=64, pattern=r"^[0-9a-f]{64}$"
+    )
+    expectedInputIdentityHash: Optional[str] = Field(
+        default=None, min_length=64, max_length=64, pattern=r"^[0-9a-f]{64}$"
+    )
+
+
+class ADV4ReviewAnnotation(BaseModel):
+    model_config = {"extra": "forbid"}
+
+    pointer: str = Field(min_length=1, max_length=1024)
+    text: str = Field(min_length=1, max_length=4096)
+
+
+class ADV4ReviewDraftCreateRequest(BaseModel):
+    model_config = {"extra": "forbid"}
+
+    expectedAuthorizationObservationHash: str = Field(
+        min_length=64, max_length=64, pattern=r"^[0-9a-f]{64}$"
+    )
+    expectedPredecessorEventHash: str = Field(
+        min_length=64, max_length=64, pattern=r"^[0-9a-f]{64}$"
+    )
+    expectedInputIdentityHash: str = Field(
+        min_length=64, max_length=64, pattern=r"^[0-9a-f]{64}$"
+    )
+    annotations: list[ADV4ReviewAnnotation] = Field(max_length=128)
+    intendedAction: Literal["undecided", "reject"] = "undecided"
+
+
+class ADV4ReviewRequestCreateRequest(BaseModel):
+    model_config = {"extra": "forbid"}
+
+    expectedAuthorizationObservationHash: str = Field(
+        min_length=64, max_length=64, pattern=r"^[0-9a-f]{64}$"
+    )
+    expectedPredecessorEventHash: str = Field(
+        min_length=64, max_length=64, pattern=r"^[0-9a-f]{64}$"
+    )
+    expectedInputIdentityHash: str = Field(
+        min_length=64, max_length=64, pattern=r"^[0-9a-f]{64}$"
+    )
+    draftRevisionId: Optional[str] = Field(default=None, min_length=1, max_length=36)
+
+
+class ADV4ReviewRejectRequest(BaseModel):
+    model_config = {"extra": "forbid"}
+
+    expectedAuthorizationObservationHash: str = Field(
+        min_length=64, max_length=64, pattern=r"^[0-9a-f]{64}$"
+    )
+    expectedPredecessorEventHash: str = Field(
+        min_length=64, max_length=64, pattern=r"^[0-9a-f]{64}$"
+    )
+    expectedRequestId: str = Field(min_length=1, max_length=36)
+    expectedInputIdentityHash: str = Field(
+        min_length=64, max_length=64, pattern=r"^[0-9a-f]{64}$"
+    )
+    reasonCodes: list[Literal[
+        "candidate_integrity",
+        "source_identity_or_evidence_missing",
+        "evidence_not_current",
+        "projection_integrity",
+        "unsupported_version",
+        "input_changed",
+        "remediation_requested",
+    ]] = Field(min_length=1, max_length=7)
+    explanation: str = Field(min_length=1, max_length=4096)
+
+
+class ADV4ReviewEventResponse(BaseModel):
+    eventId: str
+    sequenceNumber: int
+    predecessorEventHash: Optional[str]
+    eventType: str
+    resultingState: str
+    eventHash: str
+    actorUserId: str
+    authorizingMembershipId: str
+    occurredAt: datetime
+
+
+class ADV4ReviewProposalInputResponse(BaseModel):
+    state: str
+    id: str
+    storedCanonicalHash: str
+    verifiedCanonicalHash: Optional[str] = None
+    errorCode: Optional[str] = None
+
+
+class ADV4ReviewEvidenceInputResponse(BaseModel):
+    state: str
+    storedBindingHash: str
+    verifiedBindingHash: Optional[str] = None
+    headSetHash: Optional[str] = None
+    errorCode: Optional[str] = None
+
+
+class ADV4ReviewProjectionInputResponse(BaseModel):
+    state: str
+    id: Optional[str] = None
+    storedHash: Optional[str] = None
+    eventHeadHash: Optional[str] = None
+    errorCode: Optional[str] = None
+
+
+class ADV4ReviewInputIdentityResponse(BaseModel):
+    version: str
+    directiveId: str
+    proposal: ADV4ReviewProposalInputResponse
+    evidence: ADV4ReviewEvidenceInputResponse
+    applicabilityProjection: ADV4ReviewProjectionInputResponse
+    obligationProjection: ADV4ReviewProjectionInputResponse
+
+
+class ADV4ReviewObservationResponse(BaseModel):
+    version: str
+    inputIdentityHash: str
+    observedAt: str = Field(
+        pattern=r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{6}Z$"
+    )
+
+
+class ADV4ReviewProposalObservationResponse(BaseModel):
+    proposalId: str
+    directiveId: str
+    inputIdentityHash: str
+    observationHash: str
+    inputIdentity: ADV4ReviewInputIdentityResponse
+    observation: ADV4ReviewObservationResponse
+    authorizationObservationHashes: dict[str, str]
+
+
+class ADV4ReviewDraftResponse(BaseModel):
+    draftRevisionId: str
+    revisionNumber: int
+    inputIdentityHash: str
+    observationHash: str
+    annotations: list[ADV4ReviewAnnotation]
+    intendedAction: str
+    rowHash: str
+    actorUserId: str
+    authorizingMembershipId: str
+    createdAt: datetime
+
+
+class ADV4ReviewRequestResponse(BaseModel):
+    reviewRequestId: str
+    draftRevisionId: Optional[str]
+    inputIdentityHash: str
+    observationHash: str
+    cutoffHash: str
+    authorshipSetHash: str
+    authorshipSourceCount: int
+    rowHash: str
+    actorUserId: str
+    authorizingMembershipId: str
+    requestedAt: datetime
+
+
+class ADV4ReviewRejectionResponse(BaseModel):
+    rejectionId: str
+    reviewRequestId: str
+    requestedInputIdentityHash: str
+    requestedObservationHash: str
+    decisionInputIdentityHash: str
+    decisionObservationHash: str
+    reasonCodes: list[str]
+    explanation: str
+    rowHash: str
+    actorUserId: str
+    authorizingMembershipId: str
+    rejectedAt: datetime
+
+
+class ADV4ReviewSignoffResponse(BaseModel):
+    signoffId: str
+    reviewRequestId: str
+    rejectionId: str
+    action: Literal["reject"]
+    requestedInputIdentityHash: str
+    requestedObservationHash: str
+    decisionInputIdentityHash: str
+    decisionObservationHash: str
+    authorizationObservationHash: str
+    signatureHash: str
+    rowHash: str
+    actorUserId: str
+    authorizingMembershipId: str
+    signedAt: datetime
+
+
+class ADV4ReviewCaseResponse(BaseModel):
+    caseId: str
+    proposalId: str
+    directiveId: str
+    caseSequence: int
+    state: str
+    proposalCanonicalHash: str
+    inputIdentityHash: str
+    observationHash: str
+    inputIdentity: ADV4ReviewInputIdentityResponse
+    observation: ADV4ReviewObservationResponse
+    authorizationObservationHashes: dict[str, str]
+    latestEventHash: str
+    draftRevisionId: Optional[str] = None
+    reviewRequestId: Optional[str] = None
+    rejectionId: Optional[str] = None
+    signoffId: Optional[str] = None
+    drafts: list[ADV4ReviewDraftResponse] = Field(default_factory=list)
+    reviewRequest: Optional[ADV4ReviewRequestResponse] = None
+    rejection: Optional[ADV4ReviewRejectionResponse] = None
+    signoff: Optional[ADV4ReviewSignoffResponse] = None
+    events: list[ADV4ReviewEventResponse] = Field(default_factory=list)
+    draftTotal: int
+    draftLimit: int
+    draftOffset: int
+    eventTotal: int
+    eventLimit: int
+    eventOffset: int
+    idempotentRetry: bool = False
+    createdAt: datetime
+
+
+class ADV4ReviewCaseListResponse(BaseModel):
+    cases: list[ADV4ReviewCaseResponse]
+    count: int
+    total: int
+    limit: int
+    offset: int
+    authorizationObservationHashes: dict[str, str]
+
+
 class ADProposalProvenanceResponse(BaseModel):
     stagingDecisionId: str
     actorUserId: Optional[str]
diff --git a/backend/app/services/ad_extraction.py b/backend/app/services/ad_extraction.py
index a9543fc..4b119f7 100644
--- a/backend/app/services/ad_extraction.py
+++ b/backend/app/services/ad_extraction.py
@@ -1657,13 +1657,19 @@ def extract_full_text_pages(directive: AirworthinessDirective) -> list[dict[str,
     return pages
 
 
-def verified_retained_document_bytes(document: Any, *, settings: Any | None = None) -> bytes:
+def verified_retained_document_bytes(
+    document: Any,
+    *,
+    settings: Any | None = None,
+    max_size_bytes: int | None = None,
+) -> bytes:
     """Read once and return only the exact retained bytes whose identity verifies."""
 
     payload = read_stored_file_bytes(
         settings=settings or get_settings(),
         storage_backend=document.storage_backend,
         storage_key=document.storage_key,
+        max_size_bytes=max_size_bytes,
     )
     if (
         hashlib.sha256(payload).hexdigest() != document.content_hash
diff --git a/backend/app/services/ad_v4_applicability.py b/backend/app/services/ad_v4_applicability.py
index 99302c7..891e18e 100644
--- a/backend/app/services/ad_v4_applicability.py
+++ b/backend/app/services/ad_v4_applicability.py
@@ -3018,6 +3018,7 @@ def materialize_applicability(
     membership = _authorization(db, actor, membership_id)
     scope = f"{actor.id}:{membership.id}:{ENDPOINT_ACTION}:{POLICY_VERSION}:{idempotency_key}"
     _advisory_lock(db, f"idem:{scope}")
+    _advisory_lock(db, f"candidate-relationship-graph:{directive_id}")
     candidate = db.scalar(select(ADV4CandidateProposal).where(ADV4CandidateProposal.id == proposal_id).with_for_update())
     if candidate is None or candidate.directive_id != directive_id:
         raise ADV4Error("not_found", "", "Candidate proposal not found", http_status=404)
diff --git a/backend/app/services/ad_v4_candidates.py b/backend/app/services/ad_v4_candidates.py
index 4ae7672..ca68eea 100644
--- a/backend/app/services/ad_v4_candidates.py
+++ b/backend/app/services/ad_v4_candidates.py
@@ -1008,8 +1008,6 @@ def _validate_candidate_relationship_graph(
 ) -> dict[str, ADV4CandidateProposal]:
     """Serialize and reject candidate correction/replacement graph cycles."""
 
-    if not relationships:
-        return {}
     _advisory_lock(db, f"candidate-relationship-graph:{directive_id}")
     rows = db.execute(
         select(
@@ -1108,12 +1106,17 @@ def store_v4_candidate(
         if prior.directive_id != directive_id or prior.request_hash != request_hash:
             raise ADV4Error("idempotency_conflict", "", "Idempotency key was used for different canonical content", http_status=409)
         return StoredV4Candidate(db.get(ADV4CandidateProposal, prior.proposal_id), prior, True, True)  # type: ignore[arg-type]
+    # Serialize both new content and resubmissions before locking evidence.
+    # Review and materialization writers acquire the relationship lock before
+    # proposal/binding/fragment locks; taking fragments first creates a cycle
+    # with an administrator freezing or rejecting a review of this candidate.
+    _advisory_lock(db, f"content:{directive_id}:{validator_version}:{canonicalization_version}:{proposal_hash}")
+    _advisory_lock(db, f"candidate-relationship-graph:{directive_id}")
     snapshots = _binding_snapshot(db, directive_id, proposal_value)
     binding_envelope = {"version": envelopes["binding"], "bindings": snapshots}
     if validator_version == VALIDATOR_VERSION_V2:
         binding_envelope.update({"validatorVersion": validator_version, "canonicalizationVersion": canonicalization_version})
     binding_hash = _domain_hash("bindings", binding_envelope, canonicalization_version)
-    _advisory_lock(db, f"content:{directive_id}:{validator_version}:{canonicalization_version}:{proposal_hash}")
     candidate = db.scalar(select(ADV4CandidateProposal).where(
         ADV4CandidateProposal.directive_id == directive_id,
         ADV4CandidateProposal.validator_version == validator_version,
diff --git a/backend/app/services/ad_v4_obligation_persistence.py b/backend/app/services/ad_v4_obligation_persistence.py
index f07d8ab..0143520 100644
--- a/backend/app/services/ad_v4_obligation_persistence.py
+++ b/backend/app/services/ad_v4_obligation_persistence.py
@@ -627,6 +627,7 @@ def materialize_obligations(
         f"{POLICY_VERSION}:{idempotency_key}"
     )
     _advisory_lock(db, f"idem:{scope}")
+    _advisory_lock(db, f"candidate-relationship-graph:{directive_id}")
     # Lock the immutable candidate before any database gate row. An existing
     # obligation projection is looked up only after the parent locks below.
     proposal = db.scalar(select(ADV4CandidateProposal).where(
diff --git a/backend/app/services/storage.py b/backend/app/services/storage.py
index 5958091..a6a9627 100644
--- a/backend/app/services/storage.py
+++ b/backend/app/services/storage.py
@@ -166,12 +166,34 @@ def read_stored_file_bytes(
     settings: Settings,
     storage_backend: str,
     storage_key: str,
+    max_size_bytes: int | None = None,
 ) -> bytes:
+    if max_size_bytes is not None and (
+        type(max_size_bytes) is not int or max_size_bytes < 0
+    ):
+        raise ValueError("Stored-file read byte limit must be a nonnegative integer")
     if storage_backend == "s3":
         if not settings.s3_upload_bucket:
             raise ValueError("PAPRNAV_S3_UPLOAD_BUCKET is required when PAPRNAV_STORAGE_BACKEND=s3")
         response = get_s3_client(settings.aws_region).get_object(Bucket=settings.s3_upload_bucket, Key=storage_key)
-        return response["Body"].read()
+        body = response["Body"]
+        content_length = response.get("ContentLength")
+        if (
+            max_size_bytes is not None
+            and isinstance(content_length, int)
+            and content_length > max_size_bytes
+        ):
+            close = getattr(body, "close", None)
+            if callable(close):
+                close()
+            raise ValueError("Stored file exceeds read byte limit")
+        payload = body.read() if max_size_bytes is None else body.read(max_size_bytes + 1)
+        if max_size_bytes is not None and len(payload) > max_size_bytes:
+            close = getattr(body, "close", None)
+            if callable(close):
+                close()
+            raise ValueError("Stored file exceeds read byte limit")
+        return payload
 
     if storage_backend != "local":
         raise ValueError(f"Unknown upload storage backend: {storage_backend}")
@@ -180,7 +202,15 @@ def read_stored_file_bytes(
     path = (root / storage_key).resolve()
     if root not in path.parents and path != root:
         raise ValueError("Invalid storage key")
-    return path.read_bytes()
+    if max_size_bytes is not None and path.stat().st_size > max_size_bytes:
+        raise ValueError("Stored file exceeds read byte limit")
+    if max_size_bytes is None:
+        return path.read_bytes()
+    with path.open("rb") as source:
+        payload = source.read(max_size_bytes + 1)
+    if len(payload) > max_size_bytes:
+        raise ValueError("Stored file exceeds read byte limit")
+    return payload
 
 
 def store_upload_file(
diff --git a/backend/tests/test_ad_v4_api.py b/backend/tests/test_ad_v4_api.py
index 75fc0a8..92b7523 100644
--- a/backend/tests/test_ad_v4_api.py
+++ b/backend/tests/test_ad_v4_api.py
@@ -1,9 +1,14 @@
 from __future__ import annotations
 
 import json
+from types import SimpleNamespace
 
+import pytest
 from fastapi.testclient import TestClient
+from sqlalchemy.exc import DBAPIError
 
+from app.api.routes import ads as ads_routes
+from app.api.routes.ads import _candidate_database_error
 from app.models.core import (
     ADEvidenceFragment,
     ADEvidenceFragmentLifecycleEvent,
@@ -15,6 +20,31 @@ from app.services.ad_evidence import _hash_parts
 from conftest import TEST_PASSWORD, add_membership, create_organization, create_user, login
 
 
+@pytest.mark.parametrize(
+    ("sqlstate", "code"),
+    (
+        ("P0001", "candidate_integrity"),
+        ("23514", "candidate_integrity"),
+        ("40P01", "transaction_conflict"),
+        ("40001", "transaction_conflict"),
+        ("57014", "transaction_conflict"),
+        ("55P03", "transaction_conflict"),
+    ),
+)
+def test_candidate_database_failures_have_controlled_api_mapping(
+    sqlstate: str, code: str,
+) -> None:
+    translated = _candidate_database_error(SimpleNamespace(
+        orig=SimpleNamespace(sqlstate=sqlstate),
+    ))
+    assert translated is not None
+    assert translated.code == code
+    assert translated.http_status == 409
+    assert _candidate_database_error(SimpleNamespace(
+        orig=SimpleNamespace(sqlstate="XX000"),
+    )) is None
+
+
 def _seed_candidate_source(db):
     admin = create_user(db, "v4.api.admin@paprnav.local", "V4 API Admin")
     platform = create_organization(db, "Paprnav V4", "platform")
@@ -142,6 +172,43 @@ def _headers(membership_id: str, key: str = "v4-api-key") -> dict[str, str]:
     }
 
 
+@pytest.mark.parametrize(
+    ("sqlstate", "code"),
+    (
+        ("P0001", "candidate_integrity"),
+        ("23514", "candidate_integrity"),
+        ("40P01", "transaction_conflict"),
+        ("40001", "transaction_conflict"),
+        ("57014", "transaction_conflict"),
+        ("55P03", "transaction_conflict"),
+    ),
+)
+def test_candidate_post_translates_expected_database_failures(
+    client: TestClient, db_session, monkeypatch: pytest.MonkeyPatch,
+    sqlstate: str, code: str,
+) -> None:
+    admin, membership, directive, fragment = _seed_candidate_source(db_session)
+    login(client, admin.email)
+
+    class DriverFailure(Exception):
+        pass
+
+    driver_failure = DriverFailure("injected candidate database failure")
+    driver_failure.sqlstate = sqlstate
+
+    def fail_candidate_write(*args, **kwargs):
+        raise DBAPIError("injected", {}, driver_failure)
+
+    monkeypatch.setattr(ads_routes, "store_v4_candidate", fail_candidate_write)
+    response = client.post(
+        f"/api/v1/ads/directives/{directive.id}/v4/candidate-proposals",
+        json=_envelope(directive, fragment),
+        headers=_headers(membership.id, f"candidate-db-{sqlstate}"),
+    )
+    assert response.status_code == 409
+    assert response.json()["detail"]["code"] == code
+
+
 def test_admin_raw_post_retry_list_detail_and_v3_isolation(client: TestClient, db_session) -> None:
     admin, membership, directive, fragment = _seed_candidate_source(db_session)
     login(client, admin.email)
diff --git a/backend/tests/test_ad_v4_obligation_persistence_postgres.py b/backend/tests/test_ad_v4_obligation_persistence_postgres.py
index 3022cf2..7eec195 100644
--- a/backend/tests/test_ad_v4_obligation_persistence_postgres.py
+++ b/backend/tests/test_ad_v4_obligation_persistence_postgres.py
@@ -1658,7 +1658,7 @@ def test_downgrade_root_first_lock_order_refuses_without_deadlock():
         with engine.connect() as connection:
             assert connection.scalar(text(
                 "SELECT version_num FROM alembic_version"
-            )) == "20260911_0028"
+            )) == "20260913_0029"
     finally:
         if process is not None and process.poll() is None:
             process.terminate()
diff --git a/backend/tests/test_ad_v4_postgres.py b/backend/tests/test_ad_v4_postgres.py
index 0db32f1..72675cf 100644
--- a/backend/tests/test_ad_v4_postgres.py
+++ b/backend/tests/test_ad_v4_postgres.py
@@ -817,7 +817,7 @@ def test_99_occupied_v4_downgrade_refuses_without_deleting_audit_rows():
     assert POSTGRES_URL
     engine = create_engine(POSTGRES_URL, pool_pre_ping=True)
     with engine.connect() as connection:
-        assert connection.scalar(text("SELECT version_num FROM alembic_version")) == "20260911_0028"
+        assert connection.scalar(text("SELECT version_num FROM alembic_version")) == "20260913_0029"
         assert connection.scalar(text("SELECT count(*) FROM ad_v4_candidate_proposals")) >= 2
     engine.dispose()
 
diff --git a/backend/tests/test_storage.py b/backend/tests/test_storage.py
index cd5ad7c..50e0a4f 100644
--- a/backend/tests/test_storage.py
+++ b/backend/tests/test_storage.py
@@ -1,10 +1,17 @@
 from io import BytesIO
+from types import SimpleNamespace
 from urllib.parse import parse_qs
 
 import pytest
 
 from app.core.config import Settings
-from app.services.storage import s3_upload_key, store_s3_file, store_upload_file
+from app.services import storage
+from app.services.storage import (
+    read_stored_file_bytes,
+    s3_upload_key,
+    store_s3_file,
+    store_upload_file,
+)
 
 
 class FakeS3Client:
@@ -124,3 +131,66 @@ def test_store_upload_file_requires_bucket_for_s3_backend() -> None:
             max_size_bytes=1024,
             cost_allocation_tags={"Project": "paprnav"},
         )
+
+
+def test_bounded_local_read_accepts_exact_limit_and_refuses_oversize(
+    tmp_path,
+) -> None:
+    source = tmp_path / "retained.pdf"
+    source.write_bytes(b"12345")
+    settings = SimpleNamespace(local_storage_path=str(tmp_path))
+
+    assert read_stored_file_bytes(
+        settings=settings,
+        storage_backend="local",
+        storage_key="retained.pdf",
+        max_size_bytes=5,
+    ) == b"12345"
+    with pytest.raises(ValueError, match="exceeds read byte limit"):
+        read_stored_file_bytes(
+            settings=settings,
+            storage_backend="local",
+            storage_key="retained.pdf",
+            max_size_bytes=4,
+        )
+
+
+@pytest.mark.parametrize("declared_length", [5, 1])
+def test_bounded_s3_read_checks_metadata_and_stream_sentinel(
+    monkeypatch, declared_length: int,
+) -> None:
+    class Body:
+        def __init__(self) -> None:
+            self.read_sizes: list[int] = []
+            self.closed = False
+
+        def read(self, size: int) -> bytes:
+            self.read_sizes.append(size)
+            return b"12345"[:size]
+
+        def close(self) -> None:
+            self.closed = True
+
+    body = Body()
+    client = SimpleNamespace(get_object=lambda **_: {
+        "Body": body,
+        "ContentLength": declared_length,
+    })
+    monkeypatch.setattr(storage, "get_s3_client", lambda _region: client)
+    settings = SimpleNamespace(
+        s3_upload_bucket="retained",
+        aws_region="us-east-1",
+    )
+
+    with pytest.raises(ValueError, match="exceeds read byte limit"):
+        read_stored_file_bytes(
+            settings=settings,
+            storage_backend="s3",
+            storage_key="retained.pdf",
+            max_size_bytes=4,
+        )
+    if declared_length > 4:
+        assert body.read_sizes == []
+    else:
+        assert body.read_sizes == [5]
+    assert body.closed is True

```

## Untracked text files

### `.ai/MODEL_ROUTING.md`

size=8400; sha256=8019680d63b13cf53206a1c75569954abb3793de8051b032237933a98567bd36; truncated=false

```text
# Paprnav model-routing policy

This policy is mandatory for every Codex task in this repository. Route each
meaningful phase independently; do not choose one model for an entire task when
later phases have different risk or review needs.

## Routing tiers

Choose the highest tier triggered by the work. Complexity, safety impact, and
review history override convenience or expected speed.

| Work | Preferred routing |
| --- | --- |
| Mechanical, localized, low-risk edits with an obvious oracle and limited blast radius | GPT-5.6 Luna (`gpt-5.6-luna`) or GPT-5.6 Terra (`gpt-5.6-terra`), medium |
| Coherent multi-file implementation whose design is already approved | GPT-5.6 Sol (`gpt-5.6-sol`), high |
| Schema or migration design; authorization; regulatory or safety semantics; invariant synthesis; adversarial review; closure review | GPT-6 Astra (`gpt-6-astra`), high or xhigh |

Use xhigh for interacting invariants, ambiguous trust boundaries, concurrency or
rollback reasoning, closure after substantive findings, or when high effort has
not resolved the review class. Use high for a well-framed problem with explicit
invariants and a strong test oracle.

Low-risk routing applies only when all of these are true:

- the change is localized and mechanically checkable;
- failure cannot alter authorization, regulatory meaning, safety behavior,
  persisted schema, audit evidence, billing/provider choice, or a public
  contract;
- rollback is straightforward; and
- no review-history escalation below applies.

When a phase mixes tiers, use the highest triggered tier or split it into
bounded phases with explicit handoffs. An approved design is required before
routing coherent high-risk implementation to Sol; design and invariant work
remain Astra work.

## Review-history escalation

Count substantive failures within the current finding family or review loop.
Formatting-only feedback and infrastructure/transient failures do not count.

1. After the first substantive failed review, increase reasoning effort for the
   next pass and reassess whether the issue is a local defect, a missing
   invariant, a design error, an oracle gap, or a scope omission.
2. After the second failed review, or whenever the same finding family recurs,
   route the next pass to GPT-6 Astra and stop counterexample-by-counterexample
   patching. Restate the complete invariant and close the coherent family with
   its positive and negative matrix.
3. After the third unsuccessful loop, pause implementation. Identify and record
   the missing invariant, architecture decision, or shared test oracle before
   further code changes. Resume only after that gap is resolved and, for work
   governed by the adversarial-review process, independently reviewed.

Examples:

- A first concurrency-review failure moves the next pass to higher effort and
  reclassifies the issue as lock ordering, transaction isolation, or test
  coverage before editing.
- A second malformed-row counterexample in the same schema family moves the
  work to Astra and replaces one-off trigger patches with a complete union and
  corruption matrix.
- A third reconstruction mismatch stops implementation until the canonical
  mapping invariant and shared oracle are explicit.

Escalation never authorizes broader product scope or bypasses an approval gate.

## Builder and reviewer separation

Builder/reviewer separation is mandatory regardless of model. A model upgrade
does not make self-review independent. Qualifying work must still follow
`AGENTS.md`, `.ai/REVIEW_PROCESS.md`, and the repository-local
`adversarial-review` skill.

- Assign design, implementation, and closure adversaries as separate read-only
  project subagents unless the coordinator explicitly assigns a later fix task.
- Do not let the builder attest its own review stage, even when builder and
  reviewer would use the same model family.
- Record the actual runtime reviewer identity; a model name is not an identity.

## Dynamic availability and fallbacks

Use the preferred model when it is available. Otherwise choose the closest
available capability tier that can safely perform the phase:

1. For Astra-routed work, prefer the strongest available model at high or xhigh
   and preserve the mandatory independent-review gates. If no available model
   is adequate for the risk, pause and report the limitation.
2. For Sol-routed work, fall back to Astra at high, or to the strongest
   available implementation model at high when Astra is unavailable.
3. For Luna/Terra-routed work, use the other model at medium, then the closest
   available general implementation tier at medium.

Never silently claim or imply use of an unavailable model. In the phase notice
and any review artifact, record the actual fallback model and the reason. If the
runtime does not expose its model, write exactly `model not exposed by runtime`
rather than inferring it. If effort is not exposed, say `effort not exposed`.

## Required status commentary

At the start of every meaningful phase, report the role, exact model, reasoning
effort, and routing trigger. Report again whenever the role, model, or effort
changes. A meaningful phase includes framing/design, implementation, focused
verification, adversarial review, remediation after a failed review, and final
closure. Do not repeat the notice during routine progress updates when none of
those fields changed.

Use exactly this shape:

```text
Model routing: <role> → <exact model> (<effort>). Trigger: <brief reason>.
```

For a fallback, include it in the trigger, for example:

```text
Model routing: implementation builder → gpt-5.6-terra (high). Trigger: approved multi-file implementation; gpt-5.6-sol unavailable, closest implementation fallback.
```

Identify delegated builder and reviewer models in coordinator commentary. When
a delegated runtime does not expose its model, use the required unavailable
metadata wording rather than the requested model name.

## Review artifacts and closure

When known, every adversarial-review artifact must record:

- builder runtime identity, actual model, and effort;
- reviewer runtime identity, actual model, and effort;
- the routing trigger; and
- any fallback, unavailability, or unexposed runtime metadata.

Use a `## Model routing` section in each new design, implementation, remediation,
and closure-review artifact. Use a `## Model assignments` section in
`closure.md` to summarize the full run. These sections are the authoritative,
human-readable evidence locations; do not rely on task-local commentary or
model-selection requests as proof of the runtime used.

The independent closure reviewer must verify these sections against the phase
notices, returned runtime identities, and known delegation metadata. Missing,
inconsistent, inferred, or silently substituted model/effort evidence is a
closure blocker even if `validate-review-run.py` otherwise passes. Record
`model not exposed by runtime` or `effort not exposed` when applicable; that is
valid evidence of unavailable metadata, not permission to guess.

Do not rewrite historical attestations merely because model metadata was not
previously required. New review reports and closure evidence must be accurate
about what the runtime exposed. Final closure must summarize model assignments
for design, implementation, remediation, implementation review, and closure
review, including fallbacks.

For a review run already in progress when this policy is adopted, completed
reports are historical for this purpose even if they are still uncommitted. Do
not rewrite those immutable reports. Instead, bind this policy and the current
working tree into a fresh closure packet, summarize every known, unexposed, and
requested assignment in `closure.md`, and obtain a compliant independent
closure re-attestation before the files share a commit.

## Delegation mechanics

Use project subagents for bounded model-specific work when repository policy
and the active task permit delegation. Give each subagent one coherent role,
explicit scope, requested model and effort, and required evidence. Use the
repository's subagent mechanism so work remains attached to the current task;
do not create user-visible tasks merely to switch models.

The coordinator remains responsible for integrating results, checking actual
runtime metadata, preserving the working tree, and enforcing review gates.

```
### `backend/app/contracts/ad_v4_slice4_rollout.md`

size=2003; sha256=843192a2019d51dfa56eede6201ee4654c9ada4cd283095b024ee0d2ab32d4ed; truncated=false

```text
# V4 Slice-4 rejection-only rollout boundary

Migration `20260913_0029` is expand-first. It installs the database gates
`reviewer4_draft_enabled=false` and `reviewer4_decision_enabled=false`. The
application flags `PAPRNAV_AD_V4_SLICE4_READS_ENABLED`,
`PAPRNAV_AD_V4_SLICE4_DRAFTS_ENABLED`, and
`PAPRNAV_AD_V4_SLICE4_DECISIONS_ENABLED` also default to false.

This migration supports review cases, immutable annotation drafts, frozen
review requests, and graph-free rejection signoffs only. It does not install an
acceptance branch, decision-node graph, publication, current selection, V3
freeze, search, matching, coverage, compliance, or due-state behavior.

Roll out in this order:

1. migrate every database through `0029` while both new database gates remain
   disabled;
2. deploy an `0029`-aware binary to every API replica;
3. enable read routes and verify bounded repeatable-read queue/detail checks;
4. enable the application draft flag, then `reviewer4_draft_enabled`, to admit
   cases, drafts, and review requests;
5. enable the application decision flag, then
   `reviewer4_decision_enabled`, to admit rejecting signoffs.

Disabling either application or database gate fails closed. Operational
rollback means disabling the decision flag/gate first, then the draft
flag/gate, while retaining an `0029`-aware reader so immutable history remains
verifiable. Existing V3 and V4 candidate/projection reads remain unchanged.

Physical downgrade is allowed only while both Slice-4 database gates are
disabled and all six Slice-4 review tables are empty. Once any review history
exists, physical downgrade is prohibited; preserve the schema and use the
disabled-gate operational rollback instead.

Candidate-only acceptance remains a later reviewed vertical. Release-eligible
acceptance remains blocked until a separately reviewed executable evaluator
and any required supporting-document admission work exist. Slice 5 owns the V3
freeze at the first actual release/current-selection activation.

```
### `backend/app/db/migrations/sql/20260913_0029_review_case_integrity.sql`

size=44538; sha256=92cc8cb8c73356f8194fe2e995c1ca7ba9892d88d07e17f4cea67cc34d39cf7e; truncated=false

```text
-- Frozen rejection-only review contract. No function selects or publishes authority.
CREATE OR REPLACE FUNCTION paprnav_v4_review_hash(domain text, payload bytea) RETURNS text
LANGUAGE sql IMMUTABLE STRICT AS $$
 SELECT encode(sha256(convert_to(domain,'UTF8')||decode('00','hex')||payload),'hex')
$$;

CREATE OR REPLACE FUNCTION paprnav_v4_review_authors(p_proposal text) RETURNS jsonb
LANGUAGE sql STABLE AS $$
 SELECT jsonb_build_object('version','paprnav-ad-v4-review-authorship-1','bindings',
   coalesce(jsonb_agg(jsonb_build_object('sourceTable',source_table,'sourceId',source_id,
     'userId',user_id,'authorshipRole',authorship_role,'boundHash',bound_hash)
     ORDER BY source_table,source_id,user_id,authorship_role),'[]'::jsonb))
 FROM (
   SELECT 'ad_v4_candidate_submissions' source_table,id source_id,actor_user_id user_id,
     'candidate_submitter' authorship_role,request_hash bound_hash
   FROM ad_v4_candidate_submissions WHERE proposal_id=p_proposal
   UNION
   SELECT 'ad_evidence_fragments',f.id,f.created_by_user_id,'fragment_creator',f.fragment_hash
   FROM ad_v4_candidate_evidence_bindings b JOIN ad_evidence_fragments f ON f.id=b.fragment_id
   WHERE b.proposal_id=p_proposal
   UNION
   SELECT 'ad_evidence_fragment_lifecycle_events',e.id,e.actor_user_id,'fragment_admitter',e.event_hash
   FROM ad_v4_candidate_evidence_bindings b JOIN ad_evidence_fragment_lifecycle_events e ON e.id=b.admitted_event_id
   WHERE b.proposal_id=p_proposal
 ) sources
$$;

CREATE OR REPLACE FUNCTION paprnav_v4_review_cutoff(p_proposal text) RETURNS jsonb
LANGUAGE sql STABLE AS $$
 SELECT jsonb_build_object('version','paprnav-ad-v4-review-cutoff-1','proposalId',p_proposal,
   'submissions',(SELECT coalesce(jsonb_agg(jsonb_build_object('id',id,'hash',request_hash) ORDER BY id),'[]'::jsonb) FROM (SELECT id,request_hash FROM ad_v4_candidate_submissions WHERE proposal_id=p_proposal ORDER BY id LIMIT 2001) bounded_submissions),
   'relationships',(SELECT coalesce(jsonb_agg(jsonb_build_object('id',id,'hash',relationship_hash) ORDER BY id),'[]'::jsonb) FROM (SELECT r.id,r.relationship_hash FROM ad_v4_candidate_submission_relationships r JOIN ad_v4_candidate_submissions s ON s.id=r.submission_id WHERE s.proposal_id=p_proposal OR r.predecessor_proposal_id=p_proposal ORDER BY r.id LIMIT 2001) bounded_relationships),
   'fragmentHeads',(SELECT coalesce(jsonb_agg(jsonb_build_object('fragmentId',fragment_id,'eventId',id,'eventHash',event_hash,'sequenceNumber',sequence_number) ORDER BY fragment_id),'[]'::jsonb) FROM (SELECT DISTINCT ON (e.fragment_id) e.* FROM ad_evidence_fragment_lifecycle_events e JOIN ad_v4_candidate_evidence_bindings b ON b.fragment_id=e.fragment_id WHERE b.proposal_id=p_proposal ORDER BY e.fragment_id,e.sequence_number DESC) heads),
   'applicabilityHeads',(SELECT coalesce(jsonb_agg(jsonb_build_object('projectionId',projection_id,'eventId',id,'eventHash',event_hash,'sequenceNumber',sequence_number) ORDER BY projection_id),'[]'::jsonb) FROM (SELECT DISTINCT ON (e.projection_id) e.* FROM ad_v4_candidate_app_projection_events e JOIN ad_v4_candidate_app_projections p ON p.id=e.projection_id WHERE p.proposal_id=p_proposal ORDER BY e.projection_id,e.sequence_number DESC) heads),
   'obligationHeads',(SELECT coalesce(jsonb_agg(jsonb_build_object('projectionId',projection_id,'eventId',id,'eventHash',event_hash,'sequenceNumber',sequence_number) ORDER BY projection_id),'[]'::jsonb) FROM (SELECT DISTINCT ON (e.projection_id) e.* FROM ad_v4_candidate_obligation_projection_events e JOIN ad_v4_candidate_obligation_projections p ON p.id=e.projection_id WHERE p.proposal_id=p_proposal ORDER BY e.projection_id,e.sequence_number DESC) heads))
$$;

CREATE OR REPLACE FUNCTION paprnav_v4_review_validate_auth(r jsonb) RETURNS void
LANGUAGE plpgsql AS $$
DECLARE a users%ROWTYPE; m organization_memberships%ROWTYPE; auth jsonb; stable jsonb;
BEGIN
 SELECT * INTO a FROM users WHERE id=r->>'actor_user_id' FOR UPDATE;
 SELECT * INTO m FROM organization_memberships WHERE id=r->>'authorizing_membership_id' FOR UPDATE;
 IF a.id IS NULL OR m.id IS NULL OR a.status<>'active' OR m.status<>'active'
   OR m.role<>'platform_admin' OR m.user_id<>a.id OR m.organization_id IS DISTINCT FROM r->>'organization_id'
 THEN RAISE EXCEPTION 'V4 review forbidden: active platform administrator required'; END IF;
 auth:=convert_from(decode(substr(r->>'auth_snapshot_bytes',3),'hex'),'UTF8')::jsonb;
 IF auth->>'version' IS DISTINCT FROM 'paprnav-ad-v4-review-authorization-1'
   OR auth->>'policyName' IS DISTINCT FROM 'paprnav-ad-v4-candidate-review-1'
   OR auth->>'policyVersion' IS DISTINCT FROM '1'
   OR auth->>'actorUserId' IS DISTINCT FROM a.id
   OR auth->>'authorizingMembershipId' IS DISTINCT FROM m.id
   OR auth->>'organizationId' IS DISTINCT FROM m.organization_id
   OR auth->>'userStatus' IS DISTINCT FROM 'active'
   OR auth->>'membershipStatus' IS DISTINCT FROM 'active'
   OR auth->>'role' IS DISTINCT FROM 'platform_admin'
   OR auth->>'validityRule' IS DISTINCT FROM 'status_only_v1'
   OR auth->'validFrom' IS DISTINCT FROM 'null'::jsonb
   OR auth->'validUntil' IS DISTINCT FROM 'null'::jsonb
   OR auth->'serverAuthorized' IS DISTINCT FROM 'true'::jsonb
   OR auth->>'userUpdatedAt' IS DISTINCT FROM to_char(a.updated_at AT TIME ZONE 'UTC','YYYY-MM-DD"T"HH24:MI:SS.US"Z"')
   OR auth->>'membershipUpdatedAt' IS DISTINCT FROM to_char(m.updated_at AT TIME ZONE 'UTC','YYYY-MM-DD"T"HH24:MI:SS.US"Z"')
   OR auth->>'action' NOT IN ('create_ad_v4_review_case','save_ad_v4_review_draft','request_ad_v4_review','reject_ad_v4_review')
   OR NOT auth ?& ARRAY['action','decisionTime','authorizationObservationHash','claimsHash']
   OR (SELECT count(*) FROM jsonb_object_keys(auth))<>19
 THEN RAISE EXCEPTION 'V4 review authorization snapshot differs'; END IF;
 IF auth->>'decisionTime' !~ '^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{6}Z$'
 THEN RAISE EXCEPTION 'V4 review authorization time differs'; END IF;
 stable:=auth-ARRAY['authorizationObservationHash','claimsHash','decisionTime'];
 IF auth->>'authorizationObservationHash' IS DISTINCT FROM paprnav_v4_review_hash('paprnav-ad-v4-review-auth-observation-1',convert_to(paprnav_v4_jcs(stable),'UTF8'))
   OR auth->>'claimsHash' IS DISTINCT FROM paprnav_v4_review_hash('paprnav-ad-v4-review-claims-1',convert_to(paprnav_v4_jcs(stable),'UTF8'))
 THEN RAISE EXCEPTION 'V4 review authorization observation differs'; END IF;
END $$;

CREATE OR REPLACE FUNCTION paprnav_v4_review_validate_observation(identity_bytes bytea,identity_hash text,audit_bytes bytea,audit_hash text,observed_at timestamptz,p_proposal text,p_directive text) RETURNS void
LANGUAGE plpgsql AS $$
DECLARE identity jsonb; audit jsonb; component jsonb; family text; state text;
 p ad_v4_candidate_proposals%ROWTYPE; projection record; expected_head text; heads jsonb;
 required_keys text[]; allowed_keys text[];
BEGIN
 identity:=convert_from(identity_bytes,'UTF8')::jsonb;
 audit:=convert_from(audit_bytes,'UTF8')::jsonb;
 IF identity_bytes<>convert_to(paprnav_v4_jcs(identity),'UTF8')
   OR audit_bytes<>convert_to(paprnav_v4_jcs(audit),'UTF8')
   OR identity_hash<>paprnav_v4_review_hash('paprnav-ad-v4-review-input-identity-1',identity_bytes)
   OR audit_hash<>paprnav_v4_review_hash('paprnav-ad-v4-review-observation-1',audit_bytes)
   OR identity->>'version' IS DISTINCT FROM 'paprnav-ad-v4-review-input-identity-1'
   OR identity->>'directiveId' IS DISTINCT FROM p_directive
   OR NOT identity ?& ARRAY['proposal','evidence','applicabilityProjection','obligationProjection']
   OR (SELECT count(*) FROM jsonb_object_keys(identity))<>6
   OR audit IS DISTINCT FROM jsonb_build_object('version','paprnav-ad-v4-review-observation-1','inputIdentityHash',identity_hash,'observedAt',to_char(observed_at AT TIME ZONE 'UTC','YYYY-MM-DD"T"HH24:MI:SS.US"Z"'))
 THEN RAISE EXCEPTION 'V4 review observation identity differs'; END IF;
 SELECT * INTO p FROM ad_v4_candidate_proposals WHERE id=p_proposal;
 IF p.id IS NULL OR p.directive_id<>p_directive THEN RAISE EXCEPTION 'V4 review proposal binding differs'; END IF;
 FOREACH family IN ARRAY ARRAY['proposal','evidence','applicabilityProjection','obligationProjection'] LOOP
   component:=identity->family; state:=component->>'state';
   IF jsonb_typeof(component) IS DISTINCT FROM 'object' OR state IS NULL
     OR state NOT IN ('verified','missing','stale','integrity_error','unsupported_version')
     OR EXISTS(SELECT 1 FROM jsonb_each(component) WHERE jsonb_typeof(value)<>'string')
   THEN RAISE EXCEPTION 'V4 review observation branch differs'; END IF;
   -- No branch may hide an invalid nested digest behind a valid outer digest.
   IF EXISTS(SELECT 1 FROM jsonb_each_text(component) item WHERE item.key LIKE '%Hash' AND item.value !~ '^[0-9a-f]{64}$')
     OR (component ? 'id' AND length(component->>'id') NOT BETWEEN 1 AND 36)
   THEN RAISE EXCEPTION 'V4 review observation nested identity encoding differs'; END IF;
   IF family='proposal' THEN
     required_keys:=ARRAY['state','id','storedCanonicalHash',CASE WHEN state='verified' THEN 'verifiedCanonicalHash' ELSE 'errorCode' END];
     allowed_keys:=required_keys;
   ELSIF family='evidence' THEN
     required_keys:=CASE state
       WHEN 'verified' THEN ARRAY['state','storedBindingHash','verifiedBindingHash','headSetHash']
       WHEN 'stale' THEN ARRAY['state','storedBindingHash','errorCode','headSetHash']
       ELSE ARRAY['state','storedBindingHash','errorCode'] END;
     allowed_keys:=CASE WHEN state IN ('integrity_error','unsupported_version') THEN required_keys||ARRAY['headSetHash'] ELSE required_keys END;
   ELSE
     required_keys:=CASE state
       WHEN 'missing' THEN ARRAY['state','errorCode']
       WHEN 'verified' THEN ARRAY['state','id','storedHash','eventHeadHash']
       WHEN 'stale' THEN ARRAY['state','id','storedHash','eventHeadHash','errorCode']
       ELSE ARRAY['state','id','storedHash','errorCode'] END;
     allowed_keys:=CASE WHEN state IN ('integrity_error','unsupported_version') THEN required_keys||ARRAY['eventHeadHash'] ELSE required_keys END;
   END IF;
   IF NOT component ?& required_keys OR EXISTS(SELECT 1 FROM jsonb_object_keys(component) key WHERE NOT key=ANY(allowed_keys))
   THEN RAISE EXCEPTION 'V4 review observation required or forbidden keys differ'; END IF;
   IF state='verified' THEN
     IF component ? 'errorCode' THEN RAISE EXCEPTION 'V4 verified observation has error'; END IF;
   ELSE
     IF component->>'errorCode' IS NULL OR component->>'errorCode' NOT IN ('candidate_integrity','evidence_integrity','evidence_not_current','projection_integrity','projection_missing','projection_stale','unsupported_version','unsupported_validator','missing_evidence','source_identity_or_evidence_missing')
       OR component ?| ARRAY['verifiedCanonicalHash','verifiedBindingHash']
     THEN RAISE EXCEPTION 'V4 review observation error differs'; END IF;
   END IF;
   IF family='proposal' THEN
     IF state='missing' OR component->>'id' IS DISTINCT FROM p.id OR component->>'storedCanonicalHash' IS DISTINCT FROM p.canonical_hash
       OR EXISTS(SELECT 1 FROM jsonb_object_keys(component) k WHERE k NOT IN ('state','id','storedCanonicalHash','verifiedCanonicalHash','errorCode'))
       OR (state='verified' AND component->>'verifiedCanonicalHash' IS DISTINCT FROM p.canonical_hash)
     THEN RAISE EXCEPTION 'V4 review observed proposal differs'; END IF;
     IF state='verified' AND (p.validator_version<>'paprnav-ad-v4-validator-2' OR p.canonicalization_version<>'paprnav-ad-v4-c14n-2'
       OR p.canonical_hash<>paprnav_v4_review_hash('paprnav:ad_extraction_v4:proposal:paprnav-ad-v4-c14n-2',p.canonical_bytes)
       OR convert_from(p.canonical_bytes,'UTF8')::jsonb IS DISTINCT FROM p.parsed_json::jsonb)
     THEN RAISE EXCEPTION 'V4 review falsely verified proposal'; END IF;
   ELSIF family='evidence' THEN
     IF component->>'storedBindingHash' IS DISTINCT FROM p.evidence_binding_hash
       OR EXISTS(SELECT 1 FROM jsonb_object_keys(component) k WHERE k NOT IN ('state','storedBindingHash','verifiedBindingHash','headSetHash','errorCode'))
       OR (state='verified' AND (component->>'verifiedBindingHash' IS DISTINCT FROM p.evidence_binding_hash OR NOT component ? 'headSetHash'))
     THEN RAISE EXCEPTION 'V4 review observed evidence differs'; END IF;
     IF state='missing' AND EXISTS(SELECT 1 FROM ad_v4_candidate_evidence_bindings WHERE proposal_id=p.id)
     THEN RAISE EXCEPTION 'V4 review falsely missing evidence'; END IF;
     heads:=paprnav_v4_review_cutoff(p.id)->'fragmentHeads';
     IF component ? 'headSetHash' AND (jsonb_array_length(heads)=0 OR component->>'headSetHash' IS DISTINCT FROM paprnav_v4_review_hash('paprnav-ad-v4-review-evidence-heads-1',convert_to(paprnav_v4_jcs(heads),'UTF8')))
     THEN RAISE EXCEPTION 'V4 review observed evidence head set differs'; END IF;
     IF state='verified' THEN
       IF component->>'headSetHash' IS DISTINCT FROM paprnav_v4_review_hash('paprnav-ad-v4-review-evidence-heads-1',convert_to(paprnav_v4_jcs(heads),'UTF8'))
         OR NOT EXISTS(SELECT 1 FROM ad_v4_candidate_evidence_bindings WHERE proposal_id=p.id)
         OR EXISTS(SELECT 1 FROM ad_v4_candidate_evidence_bindings b LEFT JOIN ad_evidence_fragments f ON f.id=b.fragment_id LEFT JOIN LATERAL (SELECT * FROM ad_evidence_fragment_lifecycle_events WHERE fragment_id=b.fragment_id ORDER BY sequence_number DESC LIMIT 1) e ON true WHERE b.proposal_id=p.id AND (f.id IS NULL OR f.fragment_hash IS DISTINCT FROM b.fragment_hash OR e.id IS DISTINCT FROM b.admitted_event_id OR e.event_hash IS DISTINCT FROM b.admitted_event_hash OR e.event_type IS DISTINCT FROM 'admitted'))
       THEN RAISE EXCEPTION 'V4 review falsely verified evidence'; END IF;
     END IF;
   ELSE
     IF EXISTS(SELECT 1 FROM jsonb_object_keys(component) k WHERE k NOT IN ('state','id','storedHash','eventHeadHash','errorCode'))
       OR (state='missing' AND component ?| ARRAY['id','storedHash','eventHeadHash'])
       OR (state='verified' AND NOT component ?& ARRAY['id','storedHash','eventHeadHash'])
     THEN RAISE EXCEPTION 'V4 review observed projection shape differs'; END IF;
     IF family='applicabilityProjection' THEN
       SELECT id,proposal_id,directive_id,projection_hash,materializer_version INTO projection FROM ad_v4_candidate_app_projections WHERE proposal_id=p.id ORDER BY (materializer_version='paprnav-ad-v4-app-materializer-2') DESC,id LIMIT 1;
       SELECT event_hash INTO expected_head FROM ad_v4_candidate_app_projection_events WHERE projection_id=projection.id ORDER BY sequence_number DESC LIMIT 1;
     ELSE
       SELECT id,proposal_id,directive_id,projection_hash,materializer_version INTO projection FROM ad_v4_candidate_obligation_projections WHERE proposal_id=p.id ORDER BY (materializer_version='paprnav-ad-v4-obligation-materializer-1') DESC,id LIMIT 1;
       SELECT event_hash INTO expected_head FROM ad_v4_candidate_obligation_projection_events WHERE projection_id=projection.id ORDER BY sequence_number DESC LIMIT 1;
     END IF;
     IF (state='missing' AND projection.id IS NOT NULL)
       OR (state<>'missing' AND projection.id IS NULL)
       OR (projection.id IS NOT NULL AND projection.directive_id IS DISTINCT FROM p_directive)
       OR (projection.id IS NOT NULL AND NOT component ?& ARRAY['id','storedHash'])
       OR (component ? 'id' AND component->>'id' IS DISTINCT FROM projection.id)
       OR (component ? 'storedHash' AND component->>'storedHash' IS DISTINCT FROM projection.projection_hash)
       OR (component ? 'eventHeadHash' AND component->>'eventHeadHash' IS DISTINCT FROM expected_head)
       OR (projection.id IS NOT NULL AND ((expected_head IS NOT NULL) IS DISTINCT FROM (component ? 'eventHeadHash')))
     THEN RAISE EXCEPTION 'V4 review observed projection binding differs'; END IF;
     IF state='verified' THEN
       IF projection.id IS NULL OR projection.directive_id<>p_directive THEN RAISE EXCEPTION 'V4 review verified projection missing'; END IF;
       IF family='applicabilityProjection' THEN
         IF projection.materializer_version<>'paprnav-ad-v4-app-materializer-2' THEN RAISE EXCEPTION 'V4 review falsely verified unsupported applicability'; END IF;
         PERFORM paprnav_v4_candidate_app_require_complete(projection.id);
         IF EXISTS(SELECT 1 FROM ad_v4_candidate_app_projection_events WHERE projection_id=projection.id AND event_type='stale_marked') THEN RAISE EXCEPTION 'V4 review falsely verified stale applicability'; END IF;
       ELSE
         IF projection.materializer_version<>'paprnav-ad-v4-obligation-materializer-1' THEN RAISE EXCEPTION 'V4 review falsely verified unsupported obligations'; END IF;
         PERFORM paprnav_v4_review_verify_obligation(projection.id);
         IF EXISTS(SELECT 1 FROM ad_v4_candidate_obligation_projection_events WHERE projection_id=projection.id AND event_type<>'materialized') THEN RAISE EXCEPTION 'V4 review falsely verified stale obligations'; END IF;
       END IF;
     END IF;
   END IF;
 END LOOP;
END $$;

CREATE OR REPLACE FUNCTION paprnav_v4_review_insert_guard() RETURNS trigger
LANGUAGE plpgsql AS $$
DECLARE r jsonb; auth jsonb; item record; payload bytea; parsed jsonb; expected jsonb;
 domain text; hash_column text; stamp text; required_action text; terminal boolean; gate_count integer;
BEGIN
 r:=to_jsonb(NEW);
 PERFORM paprnav_v4_review_validate_auth(r);
 auth:=convert_from(NEW.auth_snapshot_bytes,'UTF8')::jsonb;
 required_action:=CASE TG_TABLE_NAME WHEN 'ad_v4_review_cases' THEN 'create_ad_v4_review_case' WHEN 'ad_v4_review_draft_revisions' THEN 'save_ad_v4_review_draft' WHEN 'ad_v4_review_requests' THEN 'request_ad_v4_review' WHEN 'ad_v4_review_case_events' THEN r->>'endpoint_action' ELSE 'reject_ad_v4_review' END;
 IF auth->>'action' IS DISTINCT FROM required_action THEN RAISE EXCEPTION 'V4 review action differs'; END IF;
 IF NEW.auth_policy_version<>'1' OR NEW.endpoint_action IS DISTINCT FROM required_action OR length(trim(NEW.idempotency_key))=0 THEN RAISE EXCEPTION 'V4 review request scope differs'; END IF;
 PERFORM pg_advisory_xact_lock(paprnav_v4_lock_key('idem:'||NEW.actor_user_id||':'||NEW.authorizing_membership_id||':'||NEW.endpoint_action||':'||NEW.auth_policy_version||':'||NEW.idempotency_key));
 PERFORM pg_advisory_xact_lock(paprnav_v4_lock_key('candidate-relationship-graph:'||NEW.directive_id));
 PERFORM id FROM ad_v4_candidate_proposals WHERE id=NEW.proposal_id AND directive_id=NEW.directive_id FOR UPDATE;
 IF NOT FOUND THEN RAISE EXCEPTION 'V4 review proposal binding differs'; END IF;
 terminal:=required_action='reject_ad_v4_review';
 PERFORM gate_key FROM ad_v4_feature_gates WHERE gate_key IN ('validator2_write_enabled','materializer3a_enabled','materializer3b_enabled','reviewer4_draft_enabled') OR (terminal AND gate_key='reviewer4_decision_enabled') ORDER BY CASE gate_key WHEN 'validator2_write_enabled' THEN 1 WHEN 'materializer3a_enabled' THEN 2 WHEN 'materializer3b_enabled' THEN 3 WHEN 'reviewer4_draft_enabled' THEN 4 ELSE 5 END FOR SHARE;
 SELECT count(*) INTO gate_count FROM ad_v4_feature_gates WHERE enabled AND (gate_key='reviewer4_draft_enabled' OR (terminal AND gate_key='reviewer4_decision_enabled'));
 IF gate_count<>(CASE WHEN terminal THEN 2 ELSE 1 END) THEN RAISE EXCEPTION 'V4 review feature gate disabled'; END IF;
 PERFORM id FROM ad_v4_candidate_evidence_bindings WHERE proposal_id=NEW.proposal_id ORDER BY id FOR SHARE;
 PERFORM f.id FROM ad_evidence_fragments f JOIN ad_v4_candidate_evidence_bindings b ON b.fragment_id=f.id WHERE b.proposal_id=NEW.proposal_id ORDER BY f.id FOR SHARE OF f;
 PERFORM pg_advisory_xact_lock(paprnav_v4_lock_key('projection:'||NEW.proposal_id||':paprnav-ad-v4-app-materializer-2'));
 PERFORM id FROM ad_v4_candidate_app_projections WHERE proposal_id=NEW.proposal_id ORDER BY id FOR SHARE;
 PERFORM pg_advisory_xact_lock(paprnav_v4_lock_key('projection:'||NEW.proposal_id||':paprnav-ad-v4-obligation-materializer-1'));
 PERFORM id FROM ad_v4_candidate_obligation_projections WHERE proposal_id=NEW.proposal_id ORDER BY id FOR SHARE;
 PERFORM pg_advisory_xact_lock(paprnav_v4_lock_key('review-case:'||NEW.proposal_id));
 IF TG_TABLE_NAME<>'ad_v4_review_cases' THEN
   PERFORM id FROM ad_v4_review_cases WHERE id=NEW.case_id FOR UPDATE;
 END IF;

 -- Each blob is bounded, canonical, domain separated and bound by scalar hash.
 FOR item IN SELECT key,value FROM jsonb_each(r) LOOP
   IF item.key LIKE '%\_hash' ESCAPE '\' AND item.value<>'null'::jsonb AND item.value #>> '{}' !~ '^[0-9a-f]{64}$' THEN RAISE EXCEPTION 'V4 review digest encoding differs'; END IF;
   IF item.key NOT LIKE '%\_bytes' ESCAPE '\' OR item.key='canonical_bytes' THEN CONTINUE; END IF;
   payload:=decode(substr(item.value #>> '{}',3),'hex'); parsed:=convert_from(payload,'UTF8')::jsonb;
   IF payload<>convert_to(paprnav_v4_jcs(parsed),'UTF8') THEN RAISE EXCEPTION 'V4 review canonical blob differs'; END IF;
   domain:=CASE item.key WHEN 'auth_snapshot_bytes' THEN 'paprnav-ad-v4-review-authorization-1' WHEN 'input_identity_bytes' THEN 'paprnav-ad-v4-review-input-identity-1' WHEN 'decision_input_identity_bytes' THEN 'paprnav-ad-v4-review-input-identity-1' WHEN 'observation_bytes' THEN 'paprnav-ad-v4-review-observation-1' WHEN 'decision_observation_bytes' THEN 'paprnav-ad-v4-review-observation-1' WHEN 'annotation_bytes' THEN 'paprnav-ad-v4-review-annotation-1' WHEN 'cutoff_bytes' THEN 'paprnav-ad-v4-review-cutoff-1' WHEN 'authorship_set_bytes' THEN 'paprnav-ad-v4-review-authorship-1' WHEN 'reasons_bytes' THEN 'paprnav-ad-v4-review-reasons-1' WHEN 'request_canonical_bytes' THEN 'paprnav-ad-v4-review-request-1' END;
   hash_column:=CASE item.key WHEN 'request_canonical_bytes' THEN 'request_hash' ELSE replace(item.key,'_bytes','_hash') END;
   IF domain IS NULL OR r->>hash_column IS DISTINCT FROM paprnav_v4_review_hash(domain,payload) THEN RAISE EXCEPTION 'V4 review blob hash differs'; END IF;
 END LOOP;
 expected:=r-ARRAY['canonical_bytes','row_hash','event_hash','signature_hash'];
 FOR item IN SELECT key,value FROM jsonb_each(expected) LOOP
   IF item.key LIKE '%\_bytes' ESCAPE '\' THEN expected:=expected-item.key;
   ELSIF item.key IN ('created_at','observed_at','requested_at','decision_observed_at','rejected_at','signed_at','occurred_at') THEN
     expected:=jsonb_set(expected,ARRAY[item.key],to_jsonb(to_char((item.value #>> '{}')::timestamptz AT TIME ZONE 'UTC','YYYY-MM-DD"T"HH24:MI:SS.US"Z"')));
   END IF;
 END LOOP;
 expected:=jsonb_build_object('version',NEW.contract_version,'table',TG_TABLE_NAME,'record',expected);
 IF NEW.canonical_bytes<>convert_to(paprnav_v4_jcs(expected),'UTF8')
   OR coalesce(r->>'row_hash',r->>'event_hash')<>paprnav_v4_review_hash('paprnav-ad-v4-review-row-1',NEW.canonical_bytes)
 THEN RAISE EXCEPTION 'V4 review canonical record differs'; END IF;
 stamp:=CASE TG_TABLE_NAME WHEN 'ad_v4_review_cases' THEN r->>'created_at' WHEN 'ad_v4_review_draft_revisions' THEN r->>'created_at' WHEN 'ad_v4_review_requests' THEN r->>'requested_at' WHEN 'ad_v4_review_rejections' THEN r->>'rejected_at' WHEN 'ad_v4_signoff_events' THEN r->>'signed_at' ELSE r->>'occurred_at' END;
 IF auth->>'decisionTime' IS DISTINCT FROM to_char(stamp::timestamptz AT TIME ZONE 'UTC','YYYY-MM-DD"T"HH24:MI:SS.US"Z"') THEN RAISE EXCEPTION 'V4 review decision time differs'; END IF;

 IF TG_TABLE_NAME IN ('ad_v4_review_cases','ad_v4_review_draft_revisions','ad_v4_review_requests') THEN
   PERFORM paprnav_v4_review_validate_observation(NEW.input_identity_bytes,NEW.input_identity_hash,NEW.observation_bytes,NEW.observation_hash,NEW.observed_at,NEW.proposal_id,NEW.directive_id);
 END IF;
 IF TG_TABLE_NAME='ad_v4_review_cases' THEN
   IF NEW.proposal_canonical_hash IS DISTINCT FROM (SELECT canonical_hash FROM ad_v4_candidate_proposals WHERE id=NEW.proposal_id) THEN RAISE EXCEPTION 'V4 case proposal hash differs'; END IF;
 ELSIF TG_TABLE_NAME='ad_v4_review_draft_revisions' THEN
   parsed:=convert_from(NEW.annotation_bytes,'UTF8')::jsonb;
   IF parsed->>'version' IS DISTINCT FROM 'paprnav-ad-v4-review-annotation-1' OR jsonb_typeof(parsed->'annotations') IS DISTINCT FROM 'array' OR (SELECT count(*) FROM jsonb_object_keys(parsed))<>2 OR jsonb_array_length(parsed->'annotations')>128 THEN RAISE EXCEPTION 'V4 review annotation shape differs'; END IF;
   IF EXISTS(SELECT 1 FROM jsonb_array_elements(parsed->'annotations') value WHERE jsonb_typeof(value) IS DISTINCT FROM 'object' OR NOT value ?& ARRAY['pointer','text'] OR (SELECT count(*) FROM jsonb_object_keys(value))<>2 OR jsonb_typeof(value->'pointer') IS DISTINCT FROM 'string' OR jsonb_typeof(value->'text') IS DISTINCT FROM 'string' OR length(value->>'pointer') NOT BETWEEN 1 AND 1024 OR left(value->>'pointer',1)<>'/' OR value->>'pointer' ~ '~([^01]|$)' OR length(value->>'text') NOT BETWEEN 1 AND 4096 OR value->>'text' !~ '[^[:space:]]') THEN RAISE EXCEPTION 'V4 review annotation bounds differ'; END IF;
 ELSIF TG_TABLE_NAME='ad_v4_review_requests' THEN
   parsed:=convert_from(NEW.cutoff_bytes,'UTF8')::jsonb;
   expected:=paprnav_v4_review_cutoff(NEW.proposal_id);
   IF jsonb_array_length(parsed->'submissions')>2000 OR jsonb_array_length(parsed->'relationships')>2000
     OR jsonb_array_length(expected->'submissions')>2000 OR jsonb_array_length(expected->'relationships')>2000
   THEN RAISE EXCEPTION 'V4 review cutoff capacity exceeded'; END IF;
   IF parsed IS DISTINCT FROM expected
     OR convert_from(NEW.authorship_set_bytes,'UTF8')::jsonb IS DISTINCT FROM paprnav_v4_review_authors(NEW.proposal_id)
     OR NEW.authorship_source_count<>jsonb_array_length(paprnav_v4_review_authors(NEW.proposal_id)->'bindings')
   THEN RAISE EXCEPTION 'V4 review request cutoff differs'; END IF;
 ELSIF TG_TABLE_NAME='ad_v4_review_rejections' THEN
   PERFORM paprnav_v4_review_validate_observation(NEW.decision_input_identity_bytes,NEW.decision_input_identity_hash,NEW.decision_observation_bytes,NEW.decision_observation_hash,NEW.decision_observed_at,NEW.proposal_id,NEW.directive_id);
   parsed:=convert_from(NEW.reasons_bytes,'UTF8')::jsonb;
   IF parsed->>'version' IS DISTINCT FROM 'paprnav-ad-v4-review-reasons-1' OR jsonb_typeof(parsed->'codes') IS DISTINCT FROM 'array' OR jsonb_typeof(parsed->'explanation') IS DISTINCT FROM 'string' OR (SELECT count(*) FROM jsonb_object_keys(parsed))<>3 OR length(parsed->>'explanation') NOT BETWEEN 1 AND 4096 OR parsed->>'explanation' !~ '[^[:space:]]' OR jsonb_array_length(parsed->'codes') NOT BETWEEN 1 AND 7 THEN RAISE EXCEPTION 'V4 review rejection reasons differ'; END IF;
   IF EXISTS(SELECT 1 FROM jsonb_array_elements_text(parsed->'codes') code WHERE code NOT IN ('candidate_integrity','source_identity_or_evidence_missing','evidence_not_current','projection_integrity','unsupported_version','input_changed','remediation_requested')) OR parsed->'codes' IS DISTINCT FROM (SELECT jsonb_agg(code ORDER BY code) FROM (SELECT DISTINCT value code FROM jsonb_array_elements_text(parsed->'codes')) codes) THEN RAISE EXCEPTION 'V4 review rejection reason codes differ'; END IF;
 ELSIF TG_TABLE_NAME='ad_v4_signoff_events' THEN
   IF NEW.signature_hash<>paprnav_v4_review_hash('paprnav-ad-v4-review-signature-1',NEW.canonical_bytes) OR NEW.authorization_observation_hash IS DISTINCT FROM auth->>'authorizationObservationHash' THEN RAISE EXCEPTION 'V4 review signoff digest differs'; END IF;
 ELSIF TG_TABLE_NAME='ad_v4_review_case_events' THEN
   parsed:=convert_from(NEW.request_canonical_bytes,'UTF8')::jsonb;
   IF NEW.auth_policy_version<>'1' OR NEW.endpoint_action IS DISTINCT FROM (CASE NEW.event_type WHEN 'case_created' THEN 'create_ad_v4_review_case' WHEN 'draft_saved' THEN 'save_ad_v4_review_draft' WHEN 'review_requested' THEN 'request_ad_v4_review' WHEN 'review_rejected' THEN 'reject_ad_v4_review' END) OR length(trim(NEW.idempotency_key))=0
     OR parsed->>'version' IS DISTINCT FROM NEW.contract_version OR parsed->>'action' IS DISTINCT FROM NEW.endpoint_action OR parsed->>'directiveId' IS DISTINCT FROM NEW.directive_id OR parsed->>'proposalId' IS DISTINCT FROM NEW.proposal_id
     OR parsed->'caseId' IS DISTINCT FROM (CASE WHEN NEW.event_type='case_created' THEN 'null'::jsonb ELSE to_jsonb(NEW.case_id) END)
     OR jsonb_typeof(parsed->'body') IS DISTINCT FROM 'object' OR (SELECT count(*) FROM jsonb_object_keys(parsed))<>6
     OR (NEW.event_type<>'case_created' AND parsed->'body'->>'expectedPredecessorEventHash' IS DISTINCT FROM NEW.predecessor_event_hash)
   THEN RAISE EXCEPTION 'V4 review canonical request routing differs'; END IF;
 END IF;
 RETURN NEW;
END $$;

-- Aggregate retained authoritative bytes without decoding JSON or copying
-- bytea values through to_jsonb. Keep every frozen *_bytes column explicit;
-- the migration test compares this sum against metadata-driven accounting.
CREATE OR REPLACE FUNCTION paprnav_v4_review_case_authoritative_bytes(p_case text) RETURNS bigint
LANGUAGE sql STABLE AS $$
 SELECT coalesce(sum(size_bytes),0)::bigint FROM (
   SELECT coalesce(octet_length(auth_snapshot_bytes),0)::bigint + coalesce(octet_length(request_canonical_bytes),0) + coalesce(octet_length(canonical_bytes),0) + coalesce(octet_length(input_identity_bytes),0) + coalesce(octet_length(observation_bytes),0) AS size_bytes
     FROM ad_v4_review_cases WHERE id=p_case
   UNION ALL
   SELECT coalesce(octet_length(auth_snapshot_bytes),0)::bigint + coalesce(octet_length(request_canonical_bytes),0) + coalesce(octet_length(canonical_bytes),0) + coalesce(octet_length(input_identity_bytes),0) + coalesce(octet_length(observation_bytes),0) + coalesce(octet_length(annotation_bytes),0)
     FROM ad_v4_review_draft_revisions WHERE case_id=p_case
   UNION ALL
   SELECT coalesce(octet_length(auth_snapshot_bytes),0)::bigint + coalesce(octet_length(request_canonical_bytes),0) + coalesce(octet_length(canonical_bytes),0) + coalesce(octet_length(input_identity_bytes),0) + coalesce(octet_length(observation_bytes),0) + coalesce(octet_length(cutoff_bytes),0) + coalesce(octet_length(authorship_set_bytes),0)
     FROM ad_v4_review_requests WHERE case_id=p_case
   UNION ALL
   SELECT coalesce(octet_length(auth_snapshot_bytes),0)::bigint + coalesce(octet_length(request_canonical_bytes),0) + coalesce(octet_length(canonical_bytes),0) + coalesce(octet_length(decision_input_identity_bytes),0) + coalesce(octet_length(decision_observation_bytes),0) + coalesce(octet_length(reasons_bytes),0)
     FROM ad_v4_review_rejections WHERE case_id=p_case
   UNION ALL
   SELECT coalesce(octet_length(auth_snapshot_bytes),0)::bigint + coalesce(octet_length(request_canonical_bytes),0) + coalesce(octet_length(canonical_bytes),0)
     FROM ad_v4_signoff_events WHERE case_id=p_case
   UNION ALL
   SELECT coalesce(octet_length(auth_snapshot_bytes),0)::bigint + coalesce(octet_length(request_canonical_bytes),0) + coalesce(octet_length(canonical_bytes),0)
     FROM ad_v4_review_case_events WHERE case_id=p_case
 ) authoritative_rows
$$;

CREATE OR REPLACE FUNCTION paprnav_v4_review_require_complete(p_case text) RETURNS void
LANGUAGE plpgsql AS $$
DECLARE c ad_v4_review_cases%ROWTYPE; e ad_v4_review_case_events%ROWTYPE;
 previous ad_v4_review_case_events%ROWTYPE; d ad_v4_review_draft_revisions%ROWTYPE;
 q ad_v4_review_requests%ROWTYPE; rejection ad_v4_review_rejections%ROWTYPE;
 signoff ad_v4_signoff_events%ROWTYPE; latest_draft text; expected_sequence integer:=0;
 expected_revision integer:=0; authoritative_bytes bigint; object_auth text; object_bytes bytea; object_time timestamptz; object_identity text; body jsonb; body_keys text[]; expected_codes jsonb; object_record jsonb;
BEGIN
 SELECT * INTO c FROM ad_v4_review_cases WHERE id=p_case;
 IF c.id IS NULL THEN RAISE EXCEPTION 'V4 review case missing'; END IF;
 -- Closed ordinal ranges and uniqueness enforce these budgets for healthy
 -- rows. Bounded recounts also fail before traversing corrupted history.
 IF c.case_sequence NOT BETWEEN 0 AND 99
   OR (SELECT count(*) FROM (SELECT 1 FROM ad_v4_review_cases WHERE proposal_id=c.proposal_id LIMIT 101) bounded_cases)>100
   OR (SELECT count(*) FROM (SELECT 1 FROM ad_v4_review_draft_revisions WHERE case_id=c.id LIMIT 1001) bounded_drafts)>1000
   OR (SELECT count(*) FROM (SELECT 1 FROM ad_v4_review_case_events WHERE case_id=c.id LIMIT 1004) bounded_events)>1003
 THEN RAISE EXCEPTION 'V4 review history capacity exceeded'; END IF;
 -- Phase ceilings reserve the per-column worst case for every remaining
 -- immutable transition: request+event needs at most 10 MiB, while
 -- rejection+signoff+event needs at most 12 MiB. The 2 MiB cushions make the
 -- reservation explicit while every authoritative byte column is capped at
 -- 1 MiB by table CHECKs.
 authoritative_bytes:=paprnav_v4_review_case_authoritative_bytes(c.id);
 IF (NOT EXISTS(SELECT 1 FROM ad_v4_review_case_events phase_event
                  WHERE phase_event.case_id=c.id AND phase_event.event_type='review_requested')
       AND authoritative_bytes>16777216)
   OR (EXISTS(SELECT 1 FROM ad_v4_review_case_events phase_event
                  WHERE phase_event.case_id=c.id AND phase_event.event_type='review_requested')
       AND NOT EXISTS(SELECT 1 FROM ad_v4_review_case_events phase_event
                  WHERE phase_event.case_id=c.id AND phase_event.event_type='review_rejected')
       AND authoritative_bytes>29360128)
   OR (EXISTS(SELECT 1 FROM ad_v4_review_case_events phase_event
                  WHERE phase_event.case_id=c.id AND phase_event.event_type='review_rejected')
       AND authoritative_bytes>41943040)
 THEN RAISE EXCEPTION 'V4 review authoritative byte capacity exceeded'; END IF;
 IF c.case_sequence>0 AND NOT EXISTS(SELECT 1 FROM ad_v4_review_cases p WHERE p.id=c.predecessor_case_id AND p.proposal_id=c.proposal_id AND p.case_sequence=c.case_sequence-1 AND EXISTS(SELECT 1 FROM ad_v4_review_case_events prior_event WHERE prior_event.case_id=p.id AND prior_event.event_type='review_rejected')) THEN RAISE EXCEPTION 'V4 successor case predecessor differs'; END IF;
 IF (SELECT count(*) FROM ad_v4_review_cases p WHERE p.proposal_id=c.proposal_id AND NOT EXISTS(SELECT 1 FROM ad_v4_review_case_events x WHERE x.case_id=p.id AND x.event_type='review_rejected'))>1 THEN RAISE EXCEPTION 'V4 proposal has multiple open review cases'; END IF;
 FOR e IN SELECT * FROM ad_v4_review_case_events WHERE case_id=c.id ORDER BY sequence_number LOOP
   IF e.sequence_number<>expected_sequence OR e.predecessor_event_hash IS DISTINCT FROM previous.event_hash THEN RAISE EXCEPTION 'V4 review event chain differs'; END IF;
   IF expected_sequence=0 AND e.event_type<>'case_created' THEN RAISE EXCEPTION 'V4 review creation event missing'; END IF;
   IF expected_sequence>0 AND NOT ((previous.resulting_state='draft' AND e.event_type IN ('draft_saved','review_requested')) OR (previous.resulting_state='pending_review' AND e.event_type='review_rejected')) THEN RAISE EXCEPTION 'V4 review lifecycle transition differs'; END IF;
   IF e.event_type='case_created' THEN object_auth:=c.auth_snapshot_hash; object_bytes:=c.auth_snapshot_bytes; object_time:=c.created_at; object_identity:=c.input_identity_hash; object_record:=to_jsonb(c);
   ELSIF e.event_type='draft_saved' THEN
     SELECT * INTO d FROM ad_v4_review_draft_revisions WHERE id=e.draft_revision_id AND case_id=c.id;
     IF d.id IS NULL OR d.revision_number<>expected_revision OR d.predecessor_draft_id IS DISTINCT FROM latest_draft OR d.expected_predecessor_event_hash<>e.predecessor_event_hash THEN RAISE EXCEPTION 'V4 review draft binding differs'; END IF;
     latest_draft:=d.id; expected_revision:=expected_revision+1; object_auth:=d.auth_snapshot_hash; object_bytes:=d.auth_snapshot_bytes; object_time:=d.created_at; object_identity:=d.input_identity_hash; object_record:=to_jsonb(d);
   ELSIF e.event_type='review_requested' THEN
     SELECT * INTO q FROM ad_v4_review_requests WHERE id=e.review_request_id AND case_id=c.id;
     IF q.id IS NULL OR q.draft_revision_id IS DISTINCT FROM latest_draft OR q.expected_predecessor_event_hash<>e.predecessor_event_hash THEN RAISE EXCEPTION 'V4 review request binding differs'; END IF;
     object_auth:=q.auth_snapshot_hash; object_bytes:=q.auth_snapshot_bytes; object_time:=q.requested_at; object_identity:=q.input_identity_hash; object_record:=to_jsonb(q);
   ELSE
     SELECT * INTO rejection FROM ad_v4_review_rejections WHERE id=e.rejection_id AND case_id=c.id;
     SELECT * INTO signoff FROM ad_v4_signoff_events WHERE id=e.signoff_id AND case_id=c.id;
     IF q.id IS NULL OR rejection.id IS NULL OR signoff.id IS NULL OR e.review_request_id<>q.id
       OR rejection.request_id<>q.id OR signoff.request_id<>q.id OR signoff.rejection_id<>rejection.id
       OR rejection.proposal_canonical_hash<>c.proposal_canonical_hash
       OR rejection.requested_input_identity_hash<>q.input_identity_hash OR rejection.requested_observation_hash<>q.observation_hash
       OR signoff.requested_input_identity_hash<>q.input_identity_hash OR signoff.requested_observation_hash<>q.observation_hash
       OR signoff.decision_input_identity_hash<>rejection.decision_input_identity_hash OR signoff.decision_observation_hash<>rejection.decision_observation_hash
       OR signoff.rejection_hash<>rejection.row_hash OR rejection.expected_predecessor_event_hash<>e.predecessor_event_hash
       OR signoff.auth_snapshot_hash<>rejection.auth_snapshot_hash OR signoff.auth_snapshot_bytes<>rejection.auth_snapshot_bytes OR signoff.signed_at<>rejection.rejected_at
       OR signoff.auth_policy_version<>rejection.auth_policy_version OR signoff.endpoint_action<>rejection.endpoint_action OR signoff.idempotency_key<>rejection.idempotency_key OR signoff.request_hash<>rejection.request_hash OR signoff.request_canonical_bytes<>rejection.request_canonical_bytes
     THEN RAISE EXCEPTION 'V4 rejection signoff binding differs'; END IF;
     IF rejection.decision_input_identity_hash<>q.input_identity_hash AND NOT (convert_from(rejection.reasons_bytes,'UTF8')::jsonb->'codes' ? 'input_changed') THEN RAISE EXCEPTION 'V4 rejection input mismatch reason missing'; END IF;
     object_auth:=rejection.auth_snapshot_hash; object_bytes:=rejection.auth_snapshot_bytes; object_time:=rejection.rejected_at; object_identity:=rejection.decision_input_identity_hash; object_record:=to_jsonb(rejection);
   END IF;
   IF object_auth IS DISTINCT FROM e.auth_snapshot_hash OR object_bytes IS DISTINCT FROM e.auth_snapshot_bytes OR object_time IS DISTINCT FROM e.occurred_at THEN RAISE EXCEPTION 'V4 review object-event authorization differs'; END IF;
   IF object_record->>'auth_policy_version' IS DISTINCT FROM e.auth_policy_version OR object_record->>'endpoint_action' IS DISTINCT FROM e.endpoint_action OR object_record->>'idempotency_key' IS DISTINCT FROM e.idempotency_key OR object_record->>'request_hash' IS DISTINCT FROM e.request_hash OR object_record->'request_canonical_bytes' IS DISTINCT FROM to_jsonb(e)->'request_canonical_bytes' THEN RAISE EXCEPTION 'V4 review object-event idempotency differs'; END IF;
   body:=convert_from(e.request_canonical_bytes,'UTF8')::jsonb->'body';
   body_keys:=CASE e.event_type
     WHEN 'case_created' THEN ARRAY['expectedAuthorizationObservationHash','expectedInputIdentityHash']
     WHEN 'draft_saved' THEN ARRAY['expectedAuthorizationObservationHash','expectedInputIdentityHash','expectedPredecessorEventHash','annotations','intendedAction']
     WHEN 'review_requested' THEN ARRAY['expectedAuthorizationObservationHash','expectedInputIdentityHash','expectedPredecessorEventHash','draftRevisionId']
     ELSE ARRAY['expectedAuthorizationObservationHash','expectedInputIdentityHash','expectedPredecessorEventHash','expectedRequestId','reasonCodes','explanation'] END;
   IF NOT body ?& body_keys OR (SELECT count(*) FROM jsonb_object_keys(body))<>cardinality(body_keys) THEN RAISE EXCEPTION 'V4 review request body shape differs'; END IF;
   IF body->>'expectedAuthorizationObservationHash' IS DISTINCT FROM (convert_from(e.auth_snapshot_bytes,'UTF8')::jsonb->>'authorizationObservationHash')
     OR (e.event_type<>'case_created' AND body->>'expectedInputIdentityHash' IS DISTINCT FROM object_identity)
     OR (e.event_type='case_created' AND body->>'expectedInputIdentityHash' IS NOT NULL AND body->>'expectedInputIdentityHash' IS DISTINCT FROM object_identity)
     OR (e.event_type='review_rejected' AND body->>'expectedRequestId' IS DISTINCT FROM q.id)
   THEN RAISE EXCEPTION 'V4 review request compare-and-swap differs'; END IF;
   IF e.event_type='draft_saved' AND (convert_from(d.annotation_bytes,'UTF8')::jsonb IS DISTINCT FROM jsonb_build_object('version','paprnav-ad-v4-review-annotation-1','annotations',body->'annotations') OR d.intended_action IS DISTINCT FROM body->>'intendedAction') THEN RAISE EXCEPTION 'V4 review draft request content differs'; END IF;
   IF e.event_type='review_requested' AND body->'draftRevisionId' IS DISTINCT FROM coalesce(to_jsonb(q.draft_revision_id),'null'::jsonb) THEN RAISE EXCEPTION 'V4 review frozen draft request differs'; END IF;
   IF e.event_type='review_rejected' THEN
     IF jsonb_typeof(body->'reasonCodes') IS DISTINCT FROM 'array' OR jsonb_typeof(body->'explanation') IS DISTINCT FROM 'string' OR jsonb_array_length(body->'reasonCodes') NOT BETWEEN 1 AND 7 OR body->'reasonCodes' IS DISTINCT FROM (SELECT jsonb_agg(code ORDER BY code) FROM (SELECT DISTINCT value code FROM jsonb_array_elements_text(body->'reasonCodes')) codes) THEN RAISE EXCEPTION 'V4 review rejection request reasons differ'; END IF;
     SELECT jsonb_agg(code ORDER BY code) INTO expected_codes FROM (SELECT value code FROM jsonb_array_elements_text(body->'reasonCodes') UNION SELECT 'input_changed' WHERE rejection.decision_input_identity_hash<>q.input_identity_hash) codes;
     IF convert_from(rejection.reasons_bytes,'UTF8')::jsonb IS DISTINCT FROM jsonb_build_object('version','paprnav-ad-v4-review-reasons-1','codes',expected_codes,'explanation',body->'explanation') THEN RAISE EXCEPTION 'V4 review rejection request content differs'; END IF;
   END IF;
   previous:=e; expected_sequence:=expected_sequence+1;
 END LOOP;
 IF expected_sequence=0 OR expected_revision<>(SELECT count(*) FROM ad_v4_review_draft_revisions WHERE case_id=c.id)
   OR (SELECT count(*) FROM ad_v4_review_requests WHERE case_id=c.id)<>(SELECT count(*) FROM ad_v4_review_case_events WHERE case_id=c.id AND event_type='review_requested')
   OR (SELECT count(*) FROM ad_v4_review_rejections WHERE case_id=c.id)<>(SELECT count(*) FROM ad_v4_review_case_events WHERE case_id=c.id AND event_type='review_rejected')
   OR (SELECT count(*) FROM ad_v4_signoff_events WHERE case_id=c.id)<>(SELECT count(*) FROM ad_v4_review_case_events WHERE case_id=c.id AND event_type='review_rejected')
 THEN RAISE EXCEPTION 'V4 review object-event completeness differs'; END IF;
END $$;

CREATE OR REPLACE FUNCTION paprnav_v4_review_complete_trigger() RETURNS trigger
LANGUAGE plpgsql AS $$
DECLARE r jsonb; terminal boolean;
BEGIN
 -- The bounded count/byte preflight in this validator precedes even the
 -- newly inserted snapshot's JSON parsing. BEFORE INSERT already acquired
 -- actor/membership locks; the fresh authorization recheck still follows.
 IF TG_TABLE_NAME='ad_v4_review_cases' THEN
   PERFORM paprnav_v4_review_require_complete(NEW.id);
 ELSE
   PERFORM paprnav_v4_review_require_complete(NEW.case_id);
 END IF;
 -- Recheck only the newly inserted authority snapshot. Historical snapshots
 -- retain their meaning after later membership changes.
 PERFORM paprnav_v4_review_validate_auth(to_jsonb(NEW));
 r:=to_jsonb(NEW);
 terminal:=convert_from(NEW.auth_snapshot_bytes,'UTF8')::jsonb->>'action'='reject_ad_v4_review';
 IF NOT EXISTS(SELECT 1 FROM ad_v4_feature_gates WHERE gate_key='reviewer4_draft_enabled' AND enabled)
   OR (terminal AND NOT EXISTS(SELECT 1 FROM ad_v4_feature_gates WHERE gate_key='reviewer4_decision_enabled' AND enabled))
 THEN RAISE EXCEPTION 'V4 review feature gate disabled at commit'; END IF;
 IF TG_TABLE_NAME='ad_v4_review_requests' THEN
   IF jsonb_array_length(paprnav_v4_review_cutoff(NEW.proposal_id)->'submissions')>2000
     OR jsonb_array_length(paprnav_v4_review_cutoff(NEW.proposal_id)->'relationships')>2000
   THEN RAISE EXCEPTION 'V4 review cutoff capacity exceeded'; END IF;
   IF convert_from(NEW.cutoff_bytes,'UTF8')::jsonb IS DISTINCT FROM paprnav_v4_review_cutoff(NEW.proposal_id)
     OR convert_from(NEW.authorship_set_bytes,'UTF8')::jsonb IS DISTINCT FROM paprnav_v4_review_authors(NEW.proposal_id)
   THEN RAISE EXCEPTION 'V4 review request cutoff changed before commit'; END IF;
 END IF;
 RETURN NULL;
END $$;

```
### `backend/app/db/migrations/versions/20260913_0029_add_ad_v4_review_cases.py`

size=15388; sha256=325277f7ffb8c9e100028c6f32e39263b0a336591b88634f641ed24737041a8f; truncated=false

```text
"""Immutable V4 review cases through graph-free rejection.

Revision ID: 20260913_0029
Revises: 20260911_0028
"""
from pathlib import Path

from alembic import op
import sqlalchemy as sa

revision = "20260913_0029"
down_revision = "20260911_0028"
branch_labels = None
depends_on = None

TABLES = ("ad_v4_review_cases", "ad_v4_review_draft_revisions", "ad_v4_review_requests", "ad_v4_review_rejections", "ad_v4_signoff_events", "ad_v4_review_case_events")
GATES = ("validator2_write_enabled", "materializer3a_enabled", "materializer3b_enabled", "reviewer4_draft_enabled", "reviewer4_decision_enabled")
SQL_PATH = Path(__file__).resolve().parents[1] / "sql/20260913_0029_review_case_integrity.sql"
MAX_CASES_PER_PROPOSAL = 100
MAX_DRAFT_REVISIONS_PER_CASE = 1000
MAX_EVENTS_PER_CASE = 1003


def _column(name: str, kind: str = "id", nullable: bool = False) -> sa.Column:
    types = {"id": sa.String(36), "hash": sa.String(64), "bytes": sa.LargeBinary(), "time": sa.DateTime(timezone=True), "int": sa.Integer(), "str": sa.String(32), "version": sa.String(64), "action": sa.String(96), "key": sa.String(255)}
    return sa.Column(name, types[kind], nullable=nullable, primary_key=name == "id")


def _create_tables() -> None:
    specs = (
        "proposal_canonical_hash:hash case_sequence:int predecessor_case_id:id? row_hash:hash created_at:time",
        "case_id:id revision_number:int predecessor_draft_id:id? expected_predecessor_event_hash:hash annotation_bytes:bytes annotation_hash:hash intended_action:str row_hash:hash created_at:time",
        "case_id:id draft_revision_id:id? expected_predecessor_event_hash:hash cutoff_bytes:bytes cutoff_hash:hash authorship_set_bytes:bytes authorship_set_hash:hash authorship_source_count:int row_hash:hash requested_at:time",
        "case_id:id request_id:id proposal_canonical_hash:hash requested_input_identity_hash:hash requested_observation_hash:hash decision_input_identity_bytes:bytes decision_input_identity_hash:hash decision_observation_bytes:bytes decision_observation_hash:hash decision_observed_at:time reasons_bytes:bytes reasons_hash:hash expected_predecessor_event_hash:hash row_hash:hash rejected_at:time",
        "case_id:id request_id:id rejection_id:id action:str rejection_hash:hash requested_input_identity_hash:hash requested_observation_hash:hash decision_input_identity_hash:hash decision_observation_hash:hash authorization_observation_hash:hash signature_hash:hash row_hash:hash signed_at:time",
        "case_id:id sequence_number:int predecessor_event_hash:hash? event_type:str resulting_state:str draft_revision_id:id? review_request_id:id? rejection_id:id? signoff_id:id? event_hash:hash occurred_at:time",
    )
    common = "id:id proposal_id:id directive_id:id actor_user_id:id authorizing_membership_id:id organization_id:id auth_snapshot_bytes:bytes auth_snapshot_hash:hash auth_policy_version:version endpoint_action:action idempotency_key:key request_canonical_bytes:bytes request_hash:hash contract_version:version canonical_bytes:bytes"
    observation = "input_identity_bytes:bytes input_identity_hash:hash observation_bytes:bytes observation_hash:hash observed_at:time"
    for ordinal, (table, spec) in enumerate(zip(TABLES, specs)):
        fields = (common + " " + spec + (" " + observation if ordinal < 3 else "")).split()
        columns = []
        for field in fields:
            name, kind = field.split(":")
            columns.append(_column(name, kind.rstrip("?"), kind.endswith("?")))
        constraints = [sa.UniqueConstraint("id", "proposal_id", "directive_id", name=f"uq_ar4_{ordinal}_identity"), sa.CheckConstraint("contract_version='paprnav-ad-v4-candidate-review-1'", name=f"ck_ar4_{ordinal}_version")]
        for local, target in (("proposal_id", "ad_v4_candidate_proposals.id"), ("directive_id", "airworthiness_directives.id"), ("actor_user_id", "users.id"), ("authorizing_membership_id", "organization_memberships.id"), ("organization_id", "organizations.id")):
            constraints.append(sa.ForeignKeyConstraint([local], [target], ondelete="RESTRICT"))
        for column in columns:
            if column.name.endswith("_hash"):
                constraints.append(sa.CheckConstraint(f"length({column.name})=64", name=f"ck_ar4_{ordinal}_{column.name}"))
            elif column.name.endswith("_bytes"):
                constraints.append(sa.CheckConstraint(f"length({column.name}) BETWEEN 2 AND 1048576", name=f"ck_ar4_{ordinal}_{column.name}"))
        if ordinal:
            constraints.append(sa.UniqueConstraint("id", "case_id", name=f"uq_ar4_{ordinal}_case_identity"))
        op.create_table(table, *columns, *constraints)

    def check(ordinal, name, expression):
        op.create_check_constraint(name, TABLES[ordinal], expression)

    def unique(ordinal, name, fields):
        op.create_unique_constraint(name, TABLES[ordinal], fields)

    def foreign(ordinal, name, fields, target, remote):
        op.create_foreign_key(name, TABLES[ordinal], TABLES[target], fields, remote, ondelete="RESTRICT", deferrable=True, initially="DEFERRED")

    for ordinal in range(1, 6):
        foreign(ordinal, f"fk_ar4_{ordinal}_case", ["case_id", "proposal_id", "directive_id"], 0, ["id", "proposal_id", "directive_id"])
    unique(0, "uq_ar4_case_sequence", ["proposal_id", "case_sequence"])
    check(0, "ck_ar4_case_capacity", f"case_sequence BETWEEN 0 AND {MAX_CASES_PER_PROPOSAL - 1}")
    op.create_index("ix_ar4_case_queue", TABLES[0], ["created_at", "id"])
    op.create_index("ix_ar4_case_directive", TABLES[0], ["directive_id", "created_at", "id"])
    check(0, "ck_ar4_case_predecessor", "(case_sequence=0 AND predecessor_case_id IS NULL) OR (case_sequence>0 AND predecessor_case_id IS NOT NULL)")
    foreign(0, "fk_ar4_case_predecessor", ["predecessor_case_id", "proposal_id", "directive_id"], 0, ["id", "proposal_id", "directive_id"])
    unique(1, "uq_ar4_draft_revision", ["case_id", "revision_number"])
    check(1, "ck_ar4_draft_capacity", f"revision_number BETWEEN 0 AND {MAX_DRAFT_REVISIONS_PER_CASE - 1}")
    check(1, "ck_ar4_draft_predecessor", "(revision_number=0 AND predecessor_draft_id IS NULL) OR (revision_number>0 AND predecessor_draft_id IS NOT NULL)")
    check(1, "ck_ar4_draft_intent", "intended_action IN ('undecided','reject')")
    for ordinal in (2, 3, 4):
        unique(ordinal, f"uq_ar4_{ordinal}_one_per_case", ["case_id"])
    check(2, "ck_ar4_request_authorship_count", "authorship_source_count>=0")
    unique(3, "uq_ar4_rejection_request", ["request_id"])
    unique(4, "uq_ar4_signoff_rejection", ["rejection_id"])
    check(4, "ck_ar4_signoff_action", "action='reject'")
    for ordinal, column, target in ((1, "predecessor_draft_id", 1), (2, "draft_revision_id", 1), (3, "request_id", 2), (4, "request_id", 2), (4, "rejection_id", 3), (5, "draft_revision_id", 1), (5, "review_request_id", 2), (5, "rejection_id", 3), (5, "signoff_id", 4)):
        foreign(ordinal, f"fk_ar4_{ordinal}_{column}", [column, "case_id"], target, ["id", "case_id"])
    unique(5, "uq_ar4_event_sequence", ["case_id", "sequence_number"])
    check(5, "ck_ar4_event_capacity", f"sequence_number BETWEEN 0 AND {MAX_EVENTS_PER_CASE - 1}")
    unique(5, "uq_ar4_event_hash", ["case_id", "event_hash"])
    unique(5, "uq_ar4_event_predecessor", ["case_id", "predecessor_event_hash"])
    unique(5, "uq_ar4_event_idempotency", ["actor_user_id", "authorizing_membership_id", "endpoint_action", "auth_policy_version", "idempotency_key"])
    check(5, "ck_ar4_event_predecessor", "(sequence_number=0 AND predecessor_event_hash IS NULL AND event_type='case_created') OR (sequence_number>0 AND predecessor_event_hash IS NOT NULL AND event_type<>'case_created')")
    check(5, "ck_ar4_event_union", "(event_type='case_created' AND resulting_state='draft' AND draft_revision_id IS NULL AND review_request_id IS NULL AND rejection_id IS NULL AND signoff_id IS NULL) OR (event_type='draft_saved' AND resulting_state='draft' AND draft_revision_id IS NOT NULL AND review_request_id IS NULL AND rejection_id IS NULL AND signoff_id IS NULL) OR (event_type='review_requested' AND resulting_state='pending_review' AND draft_revision_id IS NULL AND review_request_id IS NOT NULL AND rejection_id IS NULL AND signoff_id IS NULL) OR (event_type='review_rejected' AND resulting_state='rejected' AND draft_revision_id IS NULL AND review_request_id IS NOT NULL AND rejection_id IS NOT NULL AND signoff_id IS NOT NULL)")
    op.create_index("uq_ar4_terminal", TABLES[5], ["case_id"], unique=True, postgresql_where=sa.text("event_type='review_rejected'"))


def _capabilities(enabled: bool) -> None:
    gates = GATES if enabled else GATES[:3]
    revision_value = revision if enabled else down_revision
    gate_sql = ",".join("'" + gate + "'" for gate in gates)
    op.drop_constraint("ck_ad_v4_feature_gate_key", "ad_v4_feature_gates", type_="check")
    op.create_check_constraint("ck_ad_v4_feature_gate_key", "ad_v4_feature_gates", f"gate_key IN ({gate_sql})")
    op.execute(f"""CREATE OR REPLACE FUNCTION paprnav_v4_capabilities() RETURNS jsonb AS $$
      SELECT jsonb_build_object('revision','{revision_value}',
        'validatorPairs',jsonb_build_array(jsonb_build_array('paprnav-ad-v4-validator-1','paprnav-ad-v4-c14n-1'),jsonb_build_array('paprnav-ad-v4-validator-2','paprnav-ad-v4-c14n-2')),
        'materializers',jsonb_build_array('paprnav-ad-v4-app-materializer-2','paprnav-ad-v4-obligation-materializer-1'))
        || (SELECT jsonb_object_agg(gate_key,enabled) FROM ad_v4_feature_gates WHERE gate_key IN ({gate_sql}));
      $$ LANGUAGE sql STABLE""")
    op.execute(f"""CREATE OR REPLACE FUNCTION paprnav_set_v4_feature_gate(p_key text,p_enabled boolean,p_actor text) RETURNS void AS $$
      BEGIN
        IF p_key IS NULL OR p_key NOT IN ({gate_sql}) OR p_enabled IS NULL OR p_actor IS NULL OR length(trim(p_actor))=0 THEN RAISE EXCEPTION 'invalid V4 feature gate change'; END IF;
        PERFORM gate_key FROM ad_v4_feature_gates WHERE gate_key IN ({gate_sql}) ORDER BY CASE gate_key WHEN 'validator2_write_enabled' THEN 1 WHEN 'materializer3a_enabled' THEN 2 WHEN 'materializer3b_enabled' THEN 3 WHEN 'reviewer4_draft_enabled' THEN 4 ELSE 5 END FOR UPDATE;
        UPDATE ad_v4_feature_gates SET enabled=p_enabled,changed_at=now(),changed_by=p_actor WHERE gate_key=p_key;
        IF NOT FOUND THEN RAISE EXCEPTION 'unknown V4 feature gate'; END IF;
      END; $$ LANGUAGE plpgsql""")


def _candidate_audit_lock_order(*, user_first: bool) -> None:
    # Preserve the frozen 0028 validator bodies exactly except for these two
    # adjacent locks. Fail migration on unexpected upstream definition drift.
    for function, mode in (("paprnav_v4_validate_submission", "UPDATE"), ("paprnav_v4_validate_app_request", "SHARE")):
        definition = op.get_bind().execute(sa.text(f"SELECT pg_get_functiondef('{function}()'::regprocedure)")).scalar_one()
        member = f"      SELECT * INTO m FROM organization_memberships WHERE id=NEW.authorizing_membership_id FOR {mode};\n"
        user = f"      SELECT * INTO u FROM users WHERE id=NEW.actor_user_id FOR {mode};\n"
        before, after = (member + user, user + member) if user_first else (user + member, member + user)
        if definition.count(before) != 1:
            raise RuntimeError(f"Revision 0029 cannot reorder {function}: frozen definition drifted")
        with op.get_bind().connection.driver_connection.cursor() as cursor:
            cursor.execute(definition.replace(before, after, 1))


def upgrade() -> None:
    _candidate_audit_lock_order(user_first=True)
    _capabilities(True)
    op.execute("INSERT INTO ad_v4_feature_gates(gate_key,enabled) VALUES ('reviewer4_draft_enabled',false),('reviewer4_decision_enabled',false)")
    _create_tables()
    # The 0028 commit validator also requires its writer gates to be enabled.
    # Review is permitted while materialization is disabled, so freeze an
    # otherwise identical verifier under a new name. Never weaken the writer.
    definition = op.get_bind().execute(sa.text("SELECT pg_get_functiondef('paprnav_v4_candidate_obligation_require_complete(text)'::regprocedure)")).scalar_one()
    gate_clause = """     OR (SELECT count(*) FROM ad_v4_feature_gates
          WHERE gate_key IN (
            'validator2_write_enabled','materializer3a_enabled','materializer3b_enabled')
            AND enabled)<>3
"""
    if definition.count(gate_clause) != 1:
        raise RuntimeError("Revision 0029 cannot freeze review verifier: 0028 definition drifted")
    definition = definition.replace("paprnav_v4_candidate_obligation_require_complete", "paprnav_v4_review_verify_obligation", 1).replace(gate_clause, "")
    with op.get_bind().connection.driver_connection.cursor() as cursor:
        cursor.execute(definition)
    with op.get_bind().connection.driver_connection.cursor() as cursor:
        cursor.execute(SQL_PATH.read_text(encoding="utf-8"))
    for ordinal, table in enumerate(TABLES):
        op.execute(f"CREATE TRIGGER trg_ar4_{ordinal}_immutable BEFORE UPDATE OR DELETE ON {table} FOR EACH ROW EXECUTE FUNCTION paprnav_v4_reject_mutation()")
        op.execute(f"CREATE TRIGGER trg_ar4_{ordinal}_guard BEFORE INSERT ON {table} FOR EACH ROW EXECUTE FUNCTION paprnav_v4_review_insert_guard()")
        op.execute(f"CREATE CONSTRAINT TRIGGER trg_ar4_{ordinal}_complete AFTER INSERT ON {table} DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION paprnav_v4_review_complete_trigger()")


def downgrade() -> None:
    op.execute("SET LOCAL lock_timeout='5s'")
    op.execute("LOCK TABLE " + ",".join((*TABLES, "ad_v4_feature_gates")) + " IN ACCESS EXCLUSIVE MODE")
    bind = op.get_bind()
    if bind.execute(sa.text("SELECT 1 FROM ad_v4_feature_gates WHERE gate_key IN ('reviewer4_draft_enabled','reviewer4_decision_enabled') AND enabled LIMIT 1")).first():
        raise RuntimeError("Revision 0029 reviewer gates are enabled")
    for table in TABLES:
        if bind.execute(sa.text(f"SELECT 1 FROM {table} LIMIT 1")).first():
            raise RuntimeError("Revision 0029 contains immutable review history")
    for ordinal, table in reversed(tuple(enumerate(TABLES))):
        for suffix in ("immutable", "guard", "complete"):
            op.execute(f"DROP TRIGGER trg_ar4_{ordinal}_{suffix} ON {table}")
    for table in TABLES:
        for constraint in sa.inspect(bind).get_foreign_keys(table):
            if constraint["referred_table"] in TABLES:
                op.drop_constraint(constraint["name"], table, type_="foreignkey")
    for function, args in (("paprnav_v4_review_complete_trigger", ""), ("paprnav_v4_review_require_complete", "text"), ("paprnav_v4_review_case_authoritative_bytes", "text"), ("paprnav_v4_review_insert_guard", ""), ("paprnav_v4_review_validate_auth", "jsonb"), ("paprnav_v4_review_validate_observation", "bytea,text,bytea,text,timestamp with time zone,text,text"), ("paprnav_v4_review_verify_obligation", "text"), ("paprnav_v4_review_authors", "text"), ("paprnav_v4_review_cutoff", "text"), ("paprnav_v4_review_hash", "text,bytea")):
        op.execute(f"DROP FUNCTION IF EXISTS {function}({args})")
    for table in reversed(TABLES):
        op.drop_table(table)
    _candidate_audit_lock_order(user_first=False)
    op.execute("DELETE FROM ad_v4_feature_gates WHERE gate_key IN ('reviewer4_draft_enabled','reviewer4_decision_enabled')")
    _capabilities(False)

```
### `backend/app/services/ad_v4_reviews.py`

size=107024; sha256=c9811b48f063f943bedd4d06c34b19e0b9fb2d37888dffdbf154705bc3188a91; truncated=false

```text
"""Append-only V4 review cases through graph-free remediation rejection.

This module owns no release, selection, materialization, or semantic mutation.
Callers commit writes and supply a repeatable-read, read-only session to GETs.
"""
from __future__ import annotations

import hashlib
import json
import re
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from botocore.exceptions import (
    ClientError, ConnectionClosedError, ConnectTimeoutError, CredentialRetrievalError,
    EndpointConnectionError, IncompleteReadError, NoCredentialsError,
    PartialCredentialsError, ReadTimeoutError, ResponseStreamingError, SSLError,
)
from sqlalchemy import LargeBinary, case as sql_case, cast, func, inspect, select
from sqlalchemy.orm import Session, load_only

from app.core.config import get_settings
from app.models.core import (
    ADEvidenceFragment, ADEvidenceFragmentLifecycleEvent, ADPublication,
    ADSourceDocument, ADSourcePageTextVersion, ADV4CandidateAppProjection,
    ADV4CandidateAppProjectionEvent, ADV4CandidateAppMaterializationRequest,
    ADV4CandidateEvidenceBinding, ADV4CandidateObligationMaterializationRequest,
    ADV4CandidateObligationProjection, ADV4CandidateObligationProjectionEvent,
    ADV4CandidateProposal, ADV4CandidateSubmission,
    ADV4CandidateSubmissionRelationship, ADV4FeatureGate, ADV4ReviewCase,
    ADV4ReviewCaseEvent, ADV4ReviewDraftRevision, ADV4ReviewRejection,
    ADV4ReviewRequest, ADV4SignoffEvent, OrganizationMembership, User,
)
from app.services.ad_evidence import ADEvidenceError, _hash_parts
from app.services.ad_extraction import verified_retained_document_bytes
from app.services.ad_v4_candidates import (
    ADV4Error, CANONICALIZATION_VERSION_V2, DOMAINS, DOMAINS_V2,
    MAX_ARRAY_ITEMS, MAX_EVIDENCE_BINDINGS, PROFILE_ENVELOPES, VALIDATOR_VERSION_V2,
    _advisory_lock, canonical_bytes, verified_candidate,
)
from app.services.ad_v4_applicability import (
    MATERIALIZER_VERSION as APP_VERSION, projection_state,
    reconstruct_applicability,
)
from app.services.ad_v4_obligation_persistence import (
    MATERIALIZER_VERSION as OBLIGATION_VERSION, reconstruct_obligation_projection,
)
from app.services.ad_v4_obligations import ObligationIntegrityError


CONTRACT_VERSION = "paprnav-ad-v4-candidate-review-1"
INPUT_VERSION = "paprnav-ad-v4-review-input-identity-1"
OBSERVATION_VERSION = "paprnav-ad-v4-review-observation-1"
ACTIONS = {
    "case_created": "create_ad_v4_review_case",
    "draft_saved": "save_ad_v4_review_draft",
    "review_requested": "request_ad_v4_review",
    "review_rejected": "reject_ad_v4_review",
}
REASON_CODES = frozenset({
    "candidate_integrity", "source_identity_or_evidence_missing",
    "evidence_not_current", "projection_integrity", "unsupported_version",
    "input_changed", "remediation_requested",
})
MAX_BYTES = 1048576
MAX_CASES_PER_PROPOSAL = 100
MAX_DRAFT_REVISIONS_PER_CASE = 1000
MAX_EVENTS_PER_CASE = 1003
MAX_DRAFT_PHASE_BYTES = 16 * 1024 * 1024
MAX_REQUESTED_PHASE_BYTES = 28 * 1024 * 1024
MAX_CASE_HISTORY_BYTES = 40 * 1024 * 1024
MAX_RETAINED_SOURCE_BYTES = 64 * 1024 * 1024
_HISTORY_MODELS = (ADV4ReviewCase, ADV4ReviewDraftRevision, ADV4ReviewRequest,
                   ADV4ReviewRejection, ADV4SignoffEvent, ADV4ReviewCaseEvent)
_HASH = re.compile(r"[0-9a-f]{64}\Z")
_STORAGE_UNAVAILABLE_CODES = frozenset({
    "NoSuchKey", "NoSuchBucket", "AccessDenied", "InvalidAccessKeyId",
    "SignatureDoesNotMatch", "ExpiredToken", "InvalidToken", "RequestExpired",
    "RequestTimeTooSkewed", "SlowDown", "Throttling", "ThrottlingException",
    "RequestTimeout", "RequestTimeoutException", "InternalError", "ServiceUnavailable",
    "403", "404", "408", "429", "500", "502", "503", "504",
})
_STORAGE_UNAVAILABLE_EXCEPTIONS = (
    OSError, ConnectionClosedError, ConnectTimeoutError, EndpointConnectionError,
    IncompleteReadError, ReadTimeoutError, ResponseStreamingError, SSLError,
    CredentialRetrievalError, NoCredentialsError, PartialCredentialsError,
)


def _error(code: str, message: str, status: int = 409) -> ADV4Error:
    return ADV4Error(code, "", message, http_status=status)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _time(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")


def review_canonical_bytes(value: Any) -> bytes:
    """Fixed-key audit JSON, distinct from the numeric/null-free AD profile."""
    try:
        payload = json.dumps(value, sort_keys=True, ensure_ascii=False,
                             allow_nan=False, separators=(",", ":")).encode("utf-8")
    except (ValueError, TypeError, UnicodeError) as exc:
        raise _error("review_payload_invalid", "Review payload is not valid JSON", 422) from exc
    if b"\\u0000" in payload or len(payload) > MAX_BYTES:
        raise _error("review_payload_invalid", "Review payload exceeds the audit contract", 422)
    return payload


def review_hash(domain: str, payload: bytes) -> str:
    return hashlib.sha256(domain.encode("utf-8") + b"\x00" + payload).hexdigest()


def _fresh(db: Session, model: Any, **where: Any) -> Any:
    query = select(model).filter_by(**where).execution_options(populate_existing=True)
    return db.scalar(query)


def _require_application_gate(*, write: bool = False, terminal: bool = False) -> None:
    settings = get_settings()
    if not settings.ad_v4_slice4_reads_enabled:
        raise _error("capability_disabled", "V4 review read capability is disabled", 404)
    if write and not settings.ad_v4_slice4_drafts_enabled:
        raise _error("review_draft_gate_disabled", "V4 review draft capability is disabled")
    if terminal and not settings.ad_v4_slice4_decisions_enabled:
        raise _error("review_decision_gate_disabled", "V4 review decision capability is disabled")


def _database_gates(db: Session, *, terminal: bool = False) -> None:
    # Lock the common prefix even where an older capability need not be enabled.
    keys = ("validator2_write_enabled", "materializer3a_enabled", "materializer3b_enabled",
            "reviewer4_draft_enabled", "reviewer4_decision_enabled")
    for key in keys[:5 if terminal else 4]:
        enabled = db.scalar(select(ADV4FeatureGate.enabled).where(
            ADV4FeatureGate.gate_key == key).with_for_update(read=True))
        if enabled is None:
            raise _error("schema_capability_mismatch", "V4 review database capability is unavailable")
        if key.startswith("reviewer4_") and not enabled:
            raise _error("review_gate_disabled", "V4 review database write gate is disabled")


def _authorize(db: Session, actor: User, membership_id: str, *, lock: bool) -> dict[str, Any]:
    # Only the immutable locator comes from the identity map. Authorization still
    # uses fresh scalar rows; expired User attributes must not trigger a full load.
    actor_identity = inspect(actor).identity
    actor_id = actor_identity[0] if actor_identity else actor.id
    actor_query = select(User.id, User.status, User.updated_at).where(User.id == actor_id)
    member_query = select(OrganizationMembership.id, OrganizationMembership.user_id,
                          OrganizationMembership.organization_id, OrganizationMembership.role,
                          OrganizationMembership.status, OrganizationMembership.updated_at).where(
                              OrganizationMembership.id == membership_id)
    if lock:
        actor_query = actor_query.with_for_update()
        member_query = member_query.with_for_update()
    user = db.execute(actor_query).mappings().one_or_none()
    member = db.execute(member_query).mappings().one_or_none()
    if (user is None or user["status"] != "active" or member is None
        or member["user_id"] != actor_id or member["status"] != "active"
        or member["role"] != "platform_admin"):
        raise _error("forbidden", "Active platform administrator membership required", 403)
    return {
        "actorUserId": user["id"], "userStatus": user["status"],
        "userUpdatedAt": _time(user["updated_at"]),
        "authorizingMembershipId": member["id"], "organizationId": member["organization_id"],
        "membershipStatus": member["status"],
        "role": member["role"], "membershipUpdatedAt": _time(member["updated_at"]),
        "validityRule": "status_only_v1", "validFrom": None, "validUntil": None,
    }


def authorize_review_audit(db: Session, actor: User, membership_id: str) -> dict[str, Any]:
    _require_application_gate()
    with db.no_autoflush:
        return _authorize(db, actor, membership_id, lock=False)


def _proposal(db: Session, proposal_id: str) -> ADV4CandidateProposal:
    row = _fresh(db, ADV4CandidateProposal, id=proposal_id)
    if row is None:
        raise _error("not_found", "V4 candidate proposal not found", 404)
    return row


def _retained_source_available(document: ADSourceDocument) -> bool:
    """Only expected storage failures become remediation observations.

    Keep this boundary outside structural row-validation exception handling:
    database failures, malformed SDK responses, and programmer errors propagate.
    """
    try:
        verified_retained_document_bytes(document, max_size_bytes=min(document.storage_bytes, MAX_RETAINED_SOURCE_BYTES))
        return True
    except _STORAGE_UNAVAILABLE_EXCEPTIONS:
        return False
    except ClientError as exc:
        code = exc.response.get("Error", {}).get("Code")
        status = exc.response.get("ResponseMetadata", {}).get("HTTPStatusCode")
        if code in _STORAGE_UNAVAILABLE_CODES or status in {403, 404, 408, 429, 500, 502, 503, 504}:
            return False
        raise
    except ValueError as exc:
        # This exact integrity exception belongs to the retained-byte verifier;
        # other ValueErrors (SDK validation/configuration/programmer errors) do not.
        if str(exc) in {"Retained AD source document hash or size mismatch", "Stored file exceeds read byte limit"}:
            return False
        raise


@dataclass(frozen=True)
class _EvidenceWork:
    binding_count: int
    text_bytes: int
    lifecycle_count: int = 0
    lifecycle_reason_bytes: int = 0
    document_keys: frozenset[tuple[str, str, int]] = frozenset()
    invalid_source_size: bool = False

    @property
    def over_budget(self) -> bool:
        return (self.invalid_source_size or self.binding_count > MAX_ARRAY_ITEMS
                or self.lifecycle_count > MAX_ARRAY_ITEMS
                or self.text_bytes + self.lifecycle_reason_bytes
                + sum(key[2] for key in self.document_keys) > MAX_RETAINED_SOURCE_BYTES)


def _evidence_work_metadata(db: Session, proposal_id: str) -> _EvidenceWork:
    # SQLite length(TEXT) counts characters; BLOB length counts UTF-8 bytes.
    # PostgreSQL octet_length(TEXT) provides the same byte measurement.
    def text_length(column: Any) -> Any:
        size = (func.length(cast(column, LargeBinary)) if db.get_bind().dialect.name == "sqlite"
                else func.octet_length(column))
        return func.coalesce(size, 0)
    binding, fragment, page, document, lifecycle = (
        ADV4CandidateEvidenceBinding, ADEvidenceFragment,
        ADSourcePageTextVersion, ADSourceDocument, ADEvidenceFragmentLifecycleEvent)
    fragment_ids = select(binding.fragment_id).where(
        binding.proposal_id == proposal_id).distinct().subquery()
    lifecycle_count = select(func.count(lifecycle.id)).select_from(lifecycle).join(
        fragment_ids, fragment_ids.c.fragment_id == lifecycle.fragment_id).scalar_subquery()
    lifecycle_reason_bytes = select(func.coalesce(func.sum(text_length(lifecycle.reason)), 0)).select_from(
        lifecycle).join(fragment_ids, fragment_ids.c.fragment_id == lifecycle.fragment_id).scalar_subquery()
    count, text_bytes, event_count, event_reason_bytes = db.execute(select(
        func.count(binding.id), func.coalesce(func.sum(
        text_length(fragment.exact_text) + text_length(page.page_text)), 0),
        lifecycle_count, lifecycle_reason_bytes).select_from(binding).outerjoin(
            fragment, fragment.id == binding.fragment_id).outerjoin(page, page.id == fragment.page_text_version_id).where(
                binding.proposal_id == proposal_id)).one()
    work = _EvidenceWork(binding_count=count, text_bytes=text_bytes,
                         lifecycle_count=event_count, lifecycle_reason_bytes=event_reason_bytes)
    if not count or work.over_budget:
        return work
    documents = db.execute(select(document.id, document.content_hash, document.storage_bytes).select_from(
        binding).join(fragment, fragment.id == binding.fragment_id).join(
            document, document.id == fragment.source_document_id).where(
                binding.proposal_id == proposal_id).distinct().limit(MAX_ARRAY_ITEMS + 1)).all()
    if any(type(row.storage_bytes) is not int or row.storage_bytes < 0 for row in documents):
        return _EvidenceWork(binding_count=count, text_bytes=text_bytes,
                             lifecycle_count=event_count, lifecycle_reason_bytes=event_reason_bytes,
                             invalid_source_size=True)
    return _EvidenceWork(binding_count=count, text_bytes=text_bytes,
                         lifecycle_count=event_count, lifecycle_reason_bytes=event_reason_bytes,
                         document_keys=frozenset(tuple(row) for row in documents))


def _verified_evidence_lifecycle_events_bounded(db: Session, fragment: ADEvidenceFragment) -> list[Any]:
    """Verify one lifecycle through a scalar, limit-plus-one projection."""
    event = ADEvidenceFragmentLifecycleEvent
    rows = db.execute(select(
        event.id, event.fragment_id, event.event_type, event.actor_user_id,
        event.reason, event.sequence_number, event.predecessor_event_hash,
        event.event_hash,
    ).where(event.fragment_id == fragment.id).order_by(event.sequence_number).limit(
        MAX_ARRAY_ITEMS + 1)).all()
    if len(rows) > MAX_ARRAY_ITEMS:
        raise ADEvidenceError("evidence_lifecycle_integrity", "Evidence lifecycle exceeds review work bound")
    if not rows or [row.sequence_number for row in rows] != list(range(len(rows))):
        raise ADEvidenceError("evidence_lifecycle_integrity", "Evidence lifecycle sequence is incomplete")
    for index, row in enumerate(rows):
        predecessor_hash = None if index == 0 else rows[index - 1].event_hash
        if (row.predecessor_event_hash != predecessor_hash
            or (index == 0 and row.event_type != "admitted")
            or (index > 0 and row.event_type not in {"superseded", "quarantined"})
            or row.event_hash != _hash_parts(
                fragment.id, fragment.fragment_hash, row.event_type,
                row.actor_user_id, row.reason, row.sequence_number,
                row.predecessor_event_hash)):
            raise ADEvidenceError("evidence_lifecycle_integrity", "Evidence lifecycle chain or hash differs")
    return rows


def _prepare_evidence_observation(db: Session, proposal: ADV4CandidateProposal, *,
                                  work: _EvidenceWork | None = None) -> tuple[
        dict[str, Any], dict[tuple[str, str, int], ADSourceDocument], bool, _EvidenceWork]:
    """Validate source metadata without loading any retained document bytes."""
    result: dict[str, Any] = {"storedBindingHash": proposal.evidence_binding_hash}
    work = work if work is not None else _evidence_work_metadata(db, proposal.id)
    if work.over_budget:
        return {**result, "state": "integrity_error", "errorCode": "source_identity_or_evidence_missing"}, {}, False, work
    bindings = _bounded_rows(db, select(ADV4CandidateEvidenceBinding).where(
        ADV4CandidateEvidenceBinding.proposal_id == proposal.id).order_by(
            ADV4CandidateEvidenceBinding.evidence_key), limit=MAX_ARRAY_ITEMS, label="review observation evidence bindings")
    if not bindings:
        return {**result, "state": "missing", "errorCode": "missing_evidence"}, {}, False, work
    try:
        if (len(bindings) != proposal.binding_count
            or set(proposal.parsed_json["evidenceBindings"]) != {b.evidence_key for b in bindings}):
            raise ValueError("binding set differs")
        snapshots, heads = [], {}
        verified_documents: set[str] = set()
        documents_to_verify: dict[tuple[str, str, int], ADSourceDocument] = {}
        stale = False
        lifecycle_cache: dict[str, list[Any]] = {}
        for binding in bindings:
            fragment = _fresh(db, ADEvidenceFragment, id=binding.fragment_id)
            if fragment is None or fragment.directive_id != proposal.directive_id:
                raise ValueError("fragment identity differs")
            events = lifecycle_cache.get(fragment.id)
            if events is None:
                events = _verified_evidence_lifecycle_events_bounded(db, fragment)
                lifecycle_cache[fragment.id] = events
            admission = events[0]
            if (binding.directive_id != proposal.directive_id
                or binding.validator_version != proposal.validator_version
                or binding.canonicalization_version != proposal.canonicalization_version
                or binding.fragment_hash != fragment.fragment_hash
                or admission.id != binding.admitted_event_id
                or admission.event_hash != binding.admitted_event_hash
                or proposal.parsed_json["evidenceBindings"][binding.evidence_key]
                != {"fragmentId": fragment.id, "fragmentHash": fragment.fragment_hash}):
                raise ValueError("binding identity differs")
            expected_fragment_hash = _hash_parts(
                fragment.directive_id, fragment.source_document_id, fragment.source_content_hash,
                fragment.rendition_id, fragment.page_text_version_id, fragment.page_start,
                fragment.page_end, fragment.character_start, fragment.character_end,
                fragment.paragraph_locator, fragment.table_locator, fragment.row_locator,
                fragment.note_locator, fragment.region_map_hash, fragment.exact_text,
                fragment.parser_name, fragment.parser_version)
            page = _fresh(db, ADSourcePageTextVersion, id=fragment.page_text_version_id)
            if (expected_fragment_hash != fragment.fragment_hash or page is None
                or page.source_document_id != fragment.source_document_id
                or page.source_content_hash != fragment.source_content_hash
                or page.rendition_id != fragment.rendition_id
                or page.page_number != fragment.page_start or fragment.page_end != fragment.page_start
                or hashlib.sha256(page.page_text.encode()).hexdigest() != page.text_hash
                or fragment.character_start < 0 or fragment.character_end > len(page.page_text)
                or fragment.character_end <= fragment.character_start
                or page.page_text[fragment.character_start:fragment.character_end] != fragment.exact_text):
                raise ValueError("fragment source differs")
            if fragment.source_document_id not in verified_documents:
                document = db.scalar(select(ADSourceDocument).options(load_only(
                    ADSourceDocument.id, ADSourceDocument.content_hash, ADSourceDocument.storage_bytes,
                    ADSourceDocument.storage_backend, ADSourceDocument.storage_key)).where(
                        ADSourceDocument.id == fragment.source_document_id).execution_options(populate_existing=True))
                publication = db.scalar(select(ADPublication.id).where(
                    ADPublication.directive_id == proposal.directive_id,
                    ADPublication.source_document_id == fragment.source_document_id))
                if (document is None or publication is None or document.content_hash != fragment.source_content_hash
                    or type(document.storage_bytes) is not int or document.storage_bytes < 0):
                    raise ValueError("retained source identity differs")
                document_key = (document.id, document.content_hash, document.storage_bytes)
                documents_to_verify[document_key] = document
                verified_documents.add(document.id)
            snapshots.append({"evidenceKey": binding.evidence_key, "fragmentId": fragment.id,
                              "fragmentHash": fragment.fragment_hash, "admittedEventId": admission.id,
                              "admittedEventHash": admission.event_hash})
            heads[fragment.id] = {"fragmentId": fragment.id, "eventId": events[-1].id,
                                  "eventHash": events[-1].event_hash, "sequenceNumber": events[-1].sequence_number}
            stale = stale or len(events) != 1
        envelope = {"version": PROFILE_ENVELOPES[proposal.validator_version]["binding"],
                    "bindings": snapshots}
        if proposal.validator_version == VALIDATOR_VERSION_V2:
            envelope.update(validatorVersion=proposal.validator_version,
                            canonicalizationVersion=proposal.canonicalization_version)
        payload = canonical_bytes(envelope, proposal.canonicalization_version)
        domain = DOMAINS_V2 if proposal.validator_version == VALIDATOR_VERSION_V2 else DOMAINS
        if (payload != proposal.evidence_binding_bytes
            or hashlib.sha256(domain["bindings"] + payload).hexdigest() != proposal.evidence_binding_hash):
            raise ValueError("binding envelope differs")
        result["headSetHash"] = review_hash("paprnav-ad-v4-review-evidence-heads-1",
            review_canonical_bytes([heads[key] for key in sorted(heads)]))
    except (ADV4Error, ADEvidenceError, ValueError, KeyError, TypeError):
        return {**result, "state": "integrity_error", "errorCode": "evidence_integrity"}, {}, False, work
    return result, documents_to_verify, stale, work


def _check_source_work_budget(document_keys: Any, *, text_bytes: int = 0,
                              binding_count: int = 0, lifecycle_count: int = 0) -> None:
    if (text_bytes + sum(key[2] for key in set(document_keys)) > MAX_RETAINED_SOURCE_BYTES
        or binding_count > MAX_ARRAY_ITEMS or lifecycle_count > MAX_ARRAY_ITEMS):
        raise _error("review_work_limit", "Evidence sources exceed the review request work budget")


def _evidence_observation(db: Session, proposal: ADV4CandidateProposal, *,
                          document_cache: dict[tuple[str, str, int], bool] | None = None,
                          prepared: Any = None,
                          ) -> dict[str, Any]:
    result, documents, stale, work = prepared if prepared is not None else _prepare_evidence_observation(db, proposal)
    if "state" in result:
        return result
    cache = document_cache if document_cache is not None else {}
    _check_source_work_budget(
        set(cache) | set(documents),
        text_bytes=work.text_bytes + work.lifecycle_reason_bytes,
        binding_count=work.binding_count, lifecycle_count=work.lifecycle_count)
    for document_key, document in documents.items():
        if document_key not in cache:
            cache[document_key] = _retained_source_available(document)
        available = cache[document_key]
        if not available:
            return {**result, "state": "integrity_error", "errorCode": "source_identity_or_evidence_missing"}
    if stale:
        return {**result, "state": "stale", "errorCode": "evidence_not_current"}
    return {**result, "state": "verified", "verifiedBindingHash": proposal.evidence_binding_hash}


@dataclass(frozen=True)
class _ProjectionAuditWork:
    projection_count: int
    request_count: int = 0
    event_count: int = 0
    payload_bytes: int = 0

    @property
    def row_count(self) -> int:
        return self.request_count + self.event_count

    @property
    def over_budget(self) -> bool:
        return (self.projection_count > MAX_ARRAY_ITEMS
                or self.row_count > MAX_ARRAY_ITEMS
                or self.payload_bytes > MAX_RETAINED_SOURCE_BYTES)


def _prepare_projection_observation(db: Session, proposal_id: str, *, obligation: bool) -> tuple[list[Any], _ProjectionAuditWork]:
    model = ADV4CandidateObligationProjection if obligation else ADV4CandidateAppProjection
    request_model = (ADV4CandidateObligationMaterializationRequest if obligation
                     else ADV4CandidateAppMaterializationRequest)
    event_model = ADV4CandidateObligationProjectionEvent if obligation else ADV4CandidateAppProjectionEvent
    columns = [model.id, model.materializer_version, model.projection_hash, model.directive_id]
    if obligation:
        columns.append(ADV4CandidateObligationProjection.app_projection_id)
    projections = list(db.execute(select(*columns).where(
        model.proposal_id == proposal_id).order_by(model.id).limit(MAX_ARRAY_ITEMS + 1)))
    if not projections:
        return [], _ProjectionAuditWork(0)
    version = OBLIGATION_VERSION if obligation else APP_VERSION
    projection = next((row for row in projections if row.materializer_version == version), projections[0])
    if len(projections) > MAX_ARRAY_ITEMS:
        return projections, _ProjectionAuditWork(len(projections))
    request_count = select(func.count(request_model.id)).where(
        request_model.projection_id == projection.id).scalar_subquery()
    request_bytes = select(func.coalesce(func.sum(func.length(
        request_model.request_canonical_bytes)), 0)).where(
            request_model.projection_id == projection.id).scalar_subquery()
    event_count = select(func.count(event_model.id)).where(
        event_model.projection_id == projection.id).scalar_subquery()
    event_bytes = select(func.coalesce(func.sum(func.length(event_model.canonical_bytes)), 0)).where(
        event_model.projection_id == projection.id).scalar_subquery()
    counts = db.execute(select(request_count, event_count, request_bytes + event_bytes)).one()
    return projections, _ProjectionAuditWork(
        projection_count=len(projections), request_count=int(counts[0] or 0),
        event_count=int(counts[1] or 0), payload_bytes=int(counts[2] or 0))


def _projection_work_exceeded(works: Any) -> bool:
    eligible = [work for work in works if not work.over_budget]
    return (sum(work.row_count for work in eligible) > MAX_ARRAY_ITEMS
            or sum(work.payload_bytes for work in eligible) > MAX_RETAINED_SOURCE_BYTES)


def _projection_observation(db: Session, proposal: ADV4CandidateProposal, *, obligation: bool,
                            source_work_exceeded: bool = False, prepared: Any = None) -> dict[str, Any]:
    model = ADV4CandidateObligationProjection if obligation else ADV4CandidateAppProjection
    event_model = ADV4CandidateObligationProjectionEvent if obligation else ADV4CandidateAppProjectionEvent
    version = OBLIGATION_VERSION if obligation else APP_VERSION
    projections, audit_work = (prepared if prepared is not None
                               else _prepare_projection_observation(db, proposal.id, obligation=obligation))
    if not projections:
        return {"state": "missing", "errorCode": "projection_missing"}
    row = next((p for p in projections if p.materializer_version == version), projections[0])
    result = {"id": row.id, "storedHash": row.projection_hash}
    head = db.execute(select(
        event_model.id, event_model.event_hash, event_model.event_type,
        event_model.sequence_number,
    ).where(event_model.projection_id == row.id).order_by(
        event_model.sequence_number.desc()).limit(1)).one_or_none()
    if head is not None:
        result["eventHeadHash"] = head.event_hash
    if row.materializer_version != version:
        return {**result, "state": "unsupported_version", "errorCode": "unsupported_version"}
    if source_work_exceeded or audit_work.over_budget:
        return {**result, "state": "integrity_error", "errorCode": "projection_integrity"}
    try:
        if row.directive_id != proposal.directive_id or head is None:
            raise ValueError("projection identity differs")
        row = _fresh(db, model, id=row.id)
        if row is None:
            raise ValueError("projection identity differs")
        if obligation:
            reconstruct_obligation_projection(db, row, require_fresh=False)
            app = _fresh(db, ADV4CandidateAppProjection, id=row.app_projection_id)
            state, _ = projection_state(db, app) if app else ("candidate_stale", [])
        else:
            reconstruct_applicability(db, row)
            state, _ = projection_state(db, row)
        if state != "candidate_verified" or (head.event_type != "materialized" if obligation else head.event_type == "stale_marked"):
            return {**result, "state": "stale", "errorCode": "projection_stale"}
        return {**result, "state": "verified"}
    except (ADV4Error, ObligationIntegrityError, ValueError, KeyError, TypeError):
        return {**result, "state": "integrity_error", "errorCode": "projection_integrity"}


def observe_review_inputs(db: Session, proposal_id: str, *, observed_at: datetime | None = None,
                           _document_cache: dict[tuple[str, str, int], bool] | None = None,
                           _prepared_evidence: Any = None,
                           _prepared_projections: Any = None) -> dict[str, Any]:
    """Describe invalid inputs honestly; observation never repairs or materializes."""
    with db.no_autoflush:
        proposal = _proposal(db, proposal_id)
        prepared = _prepared_evidence if _prepared_evidence is not None else _prepare_evidence_observation(db, proposal)
        projections = (_prepared_projections if _prepared_projections is not None else {
            obligation: _prepare_projection_observation(db, proposal.id, obligation=obligation)
            for obligation in (False, True)
        })
        projection_page_exceeded = _projection_work_exceeded(
            prepared_projection[1] for prepared_projection in projections.values())
        parent_projection_exceeded = projections[False][1].over_budget
        proposal_value = {"id": proposal.id, "storedCanonicalHash": proposal.canonical_hash}
        if (proposal.validator_version, proposal.canonicalization_version) != (VALIDATOR_VERSION_V2, CANONICALIZATION_VERSION_V2):
            proposal_value.update(state="unsupported_version", errorCode="unsupported_validator")
        else:
            try:
                verified_candidate(db, proposal.id)
                proposal_value.update(state="verified", verifiedCanonicalHash=proposal.canonical_hash)
            except (ADV4Error, ValueError, TypeError, KeyError):
                proposal_value.update(state="integrity_error", errorCode="candidate_integrity")
        identity = {"version": INPUT_VERSION, "directiveId": proposal.directive_id,
                    "proposal": proposal_value, "evidence": _evidence_observation(
                        db, proposal, document_cache=_document_cache, prepared=prepared),
                    "applicabilityProjection": _projection_observation(
                        db, proposal, obligation=False,
                        source_work_exceeded=prepared[3].over_budget or projection_page_exceeded,
                        prepared=projections[False]),
                    "obligationProjection": _projection_observation(
                        db, proposal, obligation=True,
                        source_work_exceeded=(prepared[3].over_budget or projection_page_exceeded
                                              or parent_projection_exceeded),
                        prepared=projections[True])}
        identity_bytes = review_canonical_bytes(identity)
        identity_hash = review_hash(INPUT_VERSION, identity_bytes)
        instant = observed_at or _now()
        audit = {"version": OBSERVATION_VERSION, "inputIdentityHash": identity_hash,
                 "observedAt": _time(instant)}
        audit_bytes = review_canonical_bytes(audit)
        return {"input_identity_bytes": identity_bytes, "input_identity_hash": identity_hash,
                "observation_bytes": audit_bytes, "observation_hash": review_hash(OBSERVATION_VERSION, audit_bytes),
                "observed_at": instant}


def _auth_snapshot(auth: dict[str, Any], action: str, instant: datetime) -> dict[str, Any]:
    stable = {"version": "paprnav-ad-v4-review-authorization-1", "policyName": CONTRACT_VERSION,
              "policyVersion": "1", "serverAuthorized": True, "action": action, **auth}
    payload = review_canonical_bytes(stable)
    return {**stable, "decisionTime": _time(instant),
            "authorizationObservationHash": review_hash("paprnav-ad-v4-review-auth-observation-1", payload),
            "claimsHash": review_hash("paprnav-ad-v4-review-claims-1", payload)}


def _auth_hashes(auth: dict[str, Any]) -> dict[str, str]:
    return {action: _auth_snapshot(auth, action, _now())["authorizationObservationHash"]
            for action in ACTIONS.values()}


def _blob(values: dict[str, Any], name: str, domain: str, payload: Any) -> None:
    encoded = review_canonical_bytes(payload)
    values[name + "_bytes"] = encoded
    values[name + "_hash"] = review_hash(domain, encoded)


def _common(proposal: ADV4CandidateProposal, auth: dict[str, Any], *, idempotency_key: str,
            request_bytes: bytes, request_hash: str) -> dict[str, Any]:
    values = {"id": str(uuid.uuid4()), "proposal_id": proposal.id, "directive_id": proposal.directive_id,
              "actor_user_id": auth["actorUserId"], "authorizing_membership_id": auth["authorizingMembershipId"],
              "organization_id": auth["organizationId"], "contract_version": CONTRACT_VERSION,
              "auth_policy_version": "1", "endpoint_action": auth["action"],
              "idempotency_key": idempotency_key, "request_canonical_bytes": request_bytes,
              "request_hash": request_hash}
    _blob(values, "auth_snapshot", "paprnav-ad-v4-review-authorization-1", auth)
    return values


def _record_envelope(model: Any, values: dict[str, Any]) -> dict[str, Any]:
    record = {}
    for column in model.__table__.columns:
        name = column.name
        if name.endswith("_bytes") or name in {"row_hash", "event_hash", "signature_hash"}:
            continue
        value = values.get(name)
        record[name] = _time(value) if isinstance(value, datetime) else value
    return {"version": CONTRACT_VERSION, "table": model.__tablename__, "record": record}


def _new_record(db: Session, model: Any, values: dict[str, Any]) -> Any:
    encoded = review_canonical_bytes(_record_envelope(model, values))
    values = {**values, "canonical_bytes": encoded,
              "event_hash" if model is ADV4ReviewCaseEvent else "row_hash":
                  review_hash("paprnav-ad-v4-review-row-1", encoded)}
    if model is ADV4SignoffEvent:
        values["signature_hash"] = review_hash("paprnav-ad-v4-review-signature-1", encoded)
    row = model(**values)
    db.add(row)
    return row


def _authorship(db: Session, proposal_id: str, *, submission_ids: set[str] | None = None) -> dict[str, Any]:
    sources: set[tuple[str, str, str, str, str]] = set()
    submissions = select(
        ADV4CandidateSubmission.id, ADV4CandidateSubmission.actor_user_id,
        ADV4CandidateSubmission.request_hash,
    ).where(ADV4CandidateSubmission.proposal_id == proposal_id)
    if submission_ids is not None:
        submissions = submissions.where(ADV4CandidateSubmission.id.in_(submission_ids))
    for submission in _bounded_result_rows(
            db, submissions.order_by(ADV4CandidateSubmission.id), limit=MAX_ARRAY_ITEMS,
            label="review authorship submissions", overflow_code="review_history_limit"):
        sources.add(("ad_v4_candidate_submissions", submission.id, submission.actor_user_id,
                     "candidate_submitter", submission.request_hash))
    bindings = _bounded_result_rows(db, select(
        ADV4CandidateEvidenceBinding.fragment_id,
        ADV4CandidateEvidenceBinding.admitted_event_id,
    ).where(
        ADV4CandidateEvidenceBinding.proposal_id == proposal_id).order_by(ADV4CandidateEvidenceBinding.id),
        limit=MAX_EVIDENCE_BINDINGS, label="review evidence bindings")
    fragments = {row.id: row for row in db.execute(select(
        ADEvidenceFragment.id, ADEvidenceFragment.created_by_user_id,
        ADEvidenceFragment.fragment_hash,
    ).where(ADEvidenceFragment.id.in_({binding.fragment_id for binding in bindings})))}
    admissions = {row.id: row for row in db.execute(select(
        ADEvidenceFragmentLifecycleEvent.id,
        ADEvidenceFragmentLifecycleEvent.actor_user_id,
        ADEvidenceFragmentLifecycleEvent.event_hash,
    ).where(ADEvidenceFragmentLifecycleEvent.id.in_(
        {binding.admitted_event_id for binding in bindings})))}
    for binding in bindings:
        fragment = fragments.get(binding.fragment_id)
        admission = admissions.get(binding.admitted_event_id)
        if fragment is not None:
            sources.add(("ad_evidence_fragments", fragment.id, fragment.created_by_user_id,
                         "fragment_creator", fragment.fragment_hash))
        if admission is not None:
            sources.add(("ad_evidence_fragment_lifecycle_events", admission.id, admission.actor_user_id,
                         "fragment_admitter", admission.event_hash))
    return {"version": "paprnav-ad-v4-review-authorship-1", "bindings": [
        dict(zip(("sourceTable", "sourceId", "userId", "authorshipRole", "boundHash"), source))
        for source in sorted(sources)]}


def _cutoff(db: Session, proposal_id: str) -> dict[str, Any]:
    submissions = _bounded_result_rows(db, select(
        ADV4CandidateSubmission.id, ADV4CandidateSubmission.request_hash,
    ).where(
        ADV4CandidateSubmission.proposal_id == proposal_id).order_by(ADV4CandidateSubmission.id),
        limit=MAX_ARRAY_ITEMS, label="review cutoff submissions", overflow_code="review_history_limit")
    relationships = _bounded_result_rows(db, select(
        ADV4CandidateSubmissionRelationship.id,
        ADV4CandidateSubmissionRelationship.relationship_hash,
    ).join(
        ADV4CandidateSubmission, ADV4CandidateSubmission.id == ADV4CandidateSubmissionRelationship.submission_id
    ).where((ADV4CandidateSubmission.proposal_id == proposal_id)
            | (ADV4CandidateSubmissionRelationship.predecessor_proposal_id == proposal_id)).order_by(
                ADV4CandidateSubmissionRelationship.id), limit=MAX_ARRAY_ITEMS,
        label="review cutoff relationships", overflow_code="review_history_limit")
    fragment_ids = set(db.scalars(select(ADV4CandidateEvidenceBinding.fragment_id).where(
        ADV4CandidateEvidenceBinding.proposal_id == proposal_id)))
    result = {"version": "paprnav-ad-v4-review-cutoff-1", "proposalId": proposal_id,
              "submissions": [{"id": row.id, "hash": row.request_hash} for row in submissions],
              "relationships": [{"id": row.id, "hash": row.relationship_hash} for row in relationships]}
    for key, owner_ids, event_model, owner_column, owner_name in (
        ("fragmentHeads", fragment_ids, ADEvidenceFragmentLifecycleEvent,
         ADEvidenceFragmentLifecycleEvent.fragment_id, "fragmentId"),
        ("applicabilityHeads", set(db.scalars(select(ADV4CandidateAppProjection.id).where(
            ADV4CandidateAppProjection.proposal_id == proposal_id))), ADV4CandidateAppProjectionEvent,
         ADV4CandidateAppProjectionEvent.projection_id, "projectionId"),
        ("obligationHeads", set(db.scalars(select(ADV4CandidateObligationProjection.id).where(
            ADV4CandidateObligationProjection.proposal_id == proposal_id))), ADV4CandidateObligationProjectionEvent,
         ADV4CandidateObligationProjectionEvent.projection_id, "projectionId"),
    ):
        if not owner_ids:
            result[key] = []
            continue
        ranked = select(
            owner_column.label("owner_id"), event_model.id.label("event_id"),
            event_model.event_hash.label("event_hash"),
            event_model.sequence_number.label("sequence_number"),
            func.row_number().over(partition_by=owner_column,
                                   order_by=event_model.sequence_number.desc()).label("head_rank"),
        ).where(owner_column.in_(owner_ids)).subquery()
        heads = db.execute(select(
            ranked.c.owner_id, ranked.c.event_id, ranked.c.event_hash,
            ranked.c.sequence_number,
        ).where(ranked.c.head_rank == 1).order_by(ranked.c.owner_id).limit(
            len(owner_ids) + 1)).all()
        if len(heads) > len(owner_ids):
            raise _error("review_integrity", "Review cutoff event heads exceed owner cardinality")
        result[key] = [{owner_name: row.owner_id, "eventId": row.event_id,
                        "eventHash": row.event_hash, "sequenceNumber": row.sequence_number}
                       for row in heads]
    return result


def _lock_inputs(db: Session, proposal: ADV4CandidateProposal, *, terminal: bool) -> None:
    _advisory_lock(db, f"candidate-relationship-graph:{proposal.directive_id}")
    db.execute(select(ADV4CandidateProposal.id).where(ADV4CandidateProposal.id == proposal.id).with_for_update())
    _database_gates(db, terminal=terminal)
    db.execute(select(ADV4CandidateEvidenceBinding.id).where(
        ADV4CandidateEvidenceBinding.proposal_id == proposal.id).order_by(
            ADV4CandidateEvidenceBinding.id).with_for_update(read=True)).all()
    fragment_ids = select(ADV4CandidateEvidenceBinding.fragment_id).where(
        ADV4CandidateEvidenceBinding.proposal_id == proposal.id)
    db.execute(select(ADEvidenceFragment.id).where(ADEvidenceFragment.id.in_(fragment_ids)).order_by(
        ADEvidenceFragment.id).with_for_update(read=True)).all()
    for model, version in ((ADV4CandidateAppProjection, APP_VERSION),
                           (ADV4CandidateObligationProjection, OBLIGATION_VERSION)):
        _advisory_lock(db, f"projection:{proposal.id}:{version}")
        db.execute(select(model.id).where(model.proposal_id == proposal.id).order_by(
            model.id).with_for_update(read=True)).all()
    _advisory_lock(db, f"review-case:{proposal.id}")


def _mutation_start(db: Session, *, actor: User, membership_id: str, proposal_id: str,
                    directive_id: str, case_id: str | None, event_type: str,
                    idempotency_key: str, body: dict[str, Any]) -> tuple[Any, ...]:
    terminal = event_type == "review_rejected"
    _require_application_gate(write=True, terminal=terminal)
    if not isinstance(idempotency_key, str) or not idempotency_key.strip() or len(idempotency_key) > 255:
        raise _error("invalid_idempotency_key", "A bounded idempotency key is required", 422)
    current_auth = _authorize(db, actor, membership_id, lock=True)
    action = ACTIONS[event_type]
    scope = f"{actor.id}:{membership_id}:{action}:1:{idempotency_key}"
    _advisory_lock(db, f"idem:{scope}")
    _advisory_lock(db, f"candidate-relationship-graph:{directive_id}")
    proposal = _proposal(db, proposal_id)
    if proposal.directive_id != directive_id:
        raise _error("not_found", "V4 proposal does not belong to the requested directive", 404)
    _lock_inputs(db, proposal, terminal=terminal)
    request_value = {"version": CONTRACT_VERSION, "action": action, "directiveId": directive_id,
                     "proposalId": proposal_id, "caseId": case_id, "body": body}
    request_bytes = review_canonical_bytes(request_value)
    request_hash = review_hash("paprnav-ad-v4-review-request-1", request_bytes)
    prior = db.scalar(select(ADV4ReviewCaseEvent).where(
        ADV4ReviewCaseEvent.actor_user_id == actor.id,
        ADV4ReviewCaseEvent.authorizing_membership_id == membership_id,
        ADV4ReviewCaseEvent.endpoint_action == action,
        ADV4ReviewCaseEvent.auth_policy_version == "1",
        ADV4ReviewCaseEvent.idempotency_key == idempotency_key).execution_options(populate_existing=True))
    if prior is not None:
        if prior.request_hash != request_hash or prior.request_canonical_bytes != request_bytes:
            raise _error("idempotency_conflict", "Idempotency key was used for different review content")
        return proposal, current_auth, None, prior, request_bytes, request_hash
    instant = _now()
    auth = _auth_snapshot(current_auth, action, instant)
    if body["expectedAuthorizationObservationHash"] != auth["authorizationObservationHash"]:
        raise _error("stale_authorization", "Authorization facts changed since this review page was read")
    observation = observe_review_inputs(db, proposal_id, observed_at=instant)
    expected_identity = body.get("expectedInputIdentityHash")
    if expected_identity is not None and expected_identity != observation["input_identity_hash"]:
        raise _error("stale_review_inputs", "Review input identity changed")
    return proposal, auth, observation, None, request_bytes, request_hash


def _case(db: Session, case_id: str, *, lock: bool = False) -> ADV4ReviewCase:
    _check_case_history_bytes(db, case_id)
    query = select(ADV4ReviewCase).where(ADV4ReviewCase.id == case_id).execution_options(populate_existing=True)
    row = db.scalar(query.with_for_update() if lock else query)
    if row is None:
        raise _error("not_found", "V4 review case not found", 404)
    return row


def _history_byte_columns(model: Any) -> tuple[Any, ...]:
    # canonical_bytes is included by the suffix exactly once, like every other
    # authoritative blob. Use the mapped schema so new blobs cannot be omitted.
    return tuple(column for column in model.__table__.columns if column.name.endswith("_bytes"))


def _stored_case_history_usage(db: Session, case_id: str) -> tuple[int, int]:
    """One portable scalar query; no case or child blobs cross the DB boundary."""
    totals = []
    for model in _HISTORY_MODELS:
        row_bytes = sum(func.coalesce(func.length(column), 0) for column in _history_byte_columns(model))
        identity = model.id if model is ADV4ReviewCase else model.case_id
        totals.append(select(func.coalesce(func.sum(row_bytes), 0)).where(identity == case_id).scalar_subquery())
    phase = select(func.coalesce(func.max(sql_case(
        (ADV4ReviewCaseEvent.event_type == "review_rejected", 2),
        (ADV4ReviewCaseEvent.event_type == "review_requested", 1),
        else_=0,
    )), 0)).where(ADV4ReviewCaseEvent.case_id == case_id).scalar_subquery()
    with db.no_autoflush:
        row = db.execute(select(sum(totals), phase)).one()
    return int(row[0] or 0), int(row[1] or 0)


def _stored_case_history_bytes(db: Session, case_id: str) -> int:
    return _stored_case_history_usage(db, case_id)[0]


def _pending_case_history_bytes(db: Session, case_id: str) -> int:
    return sum(len(getattr(row, column.name) or b"")
        for row in db.new if isinstance(row, _HISTORY_MODELS)
        and (row.id if isinstance(row, ADV4ReviewCase) else row.case_id) == case_id
        for column in _history_byte_columns(type(row)))


def _pending_case_history_phase(db: Session, case_id: str, stored_phase: int) -> int:
    phase = stored_phase
    for row in db.new:
        if isinstance(row, ADV4ReviewCaseEvent) and row.case_id == case_id:
            phase = max(phase, {"review_requested": 1, "review_rejected": 2}.get(row.event_type, 0))
    return phase


def _case_history_limit(phase: int) -> int:
    return min(MAX_CASE_HISTORY_BYTES, (
        MAX_DRAFT_PHASE_BYTES, MAX_REQUESTED_PHASE_BYTES, MAX_CASE_HISTORY_BYTES)[phase])


def _check_case_history_bytes(db: Session, case_id: str, *, include_pending: bool = False) -> int:
    stored, stored_phase = _stored_case_history_usage(db, case_id)
    pending_phase = _pending_case_history_phase(db, case_id, stored_phase)
    effective_phase = pending_phase if include_pending else stored_phase
    if stored > _case_history_limit(effective_phase):
        raise _error("review_integrity", "Stored review history exceeds the authoritative byte bound")
    if include_pending and stored + _pending_case_history_bytes(db, case_id) > _case_history_limit(pending_phase):
        raise _error("review_history_limit", "Review append exceeds the authoritative history byte bound")
    return stored


def _flush_review_history(db: Session, case_id: str, objects: list[Any] | None = None) -> None:
    # The whole operation (including its event/signoff) is pending before the
    # first flush. Subsequent checks count flushed rows in SQL, pending rows once.
    _check_case_history_bytes(db, case_id, include_pending=True)
    db.flush(objects)


def _bounded_rows(db: Session, query: Any, *, limit: int, label: str,
                  overflow_code: str = "review_integrity") -> list[Any]:
    rows = list(db.scalars(query.limit(limit + 1).execution_options(populate_existing=True)))
    if len(rows) > limit:
        raise _error(overflow_code, f"Stored {label} exceeds the review history bound")
    return rows


def _bounded_result_rows(db: Session, query: Any, *, limit: int, label: str,
                         overflow_code: str = "review_integrity") -> list[Any]:
    rows = list(db.execute(query.limit(limit + 1)))
    if len(rows) > limit:
        raise _error(overflow_code, f"Stored {label} exceeds the review history bound")
    return rows


def _append_event(db: Session, *, case: ADV4ReviewCase, proposal: ADV4CandidateProposal,
                  auth: dict[str, Any], event_type: str, instant: datetime,
                  predecessor: ADV4ReviewCaseEvent | None, idempotency_key: str,
                  request_bytes: bytes, request_hash: str, draft: Any = None,
                  request: Any = None, rejection: Any = None, signoff: Any = None) -> ADV4ReviewCaseEvent:
    next_sequence = predecessor.sequence_number + 1 if predecessor else 0
    if next_sequence >= MAX_EVENTS_PER_CASE:
        raise _error("review_history_limit", "Review case event capacity is exhausted")
    return _new_record(db, ADV4ReviewCaseEvent, {
        **_common(proposal, auth, idempotency_key=idempotency_key,
                  request_bytes=request_bytes, request_hash=request_hash), "case_id": case.id,
        "sequence_number": next_sequence,
        "predecessor_event_hash": predecessor.event_hash if predecessor else None,
        "event_type": event_type,
        "resulting_state": {"case_created": "draft", "draft_saved": "draft",
                            "review_requested": "pending_review", "review_rejected": "rejected"}[event_type],
        "draft_revision_id": draft.id if draft else None,
        "review_request_id": request.id if request else None,
        "rejection_id": rejection.id if rejection else None, "signoff_id": signoff.id if signoff else None,
        "auth_policy_version": "1", "endpoint_action": ACTIONS[event_type],
        "idempotency_key": idempotency_key, "request_canonical_bytes": request_bytes,
        "request_hash": request_hash, "occurred_at": instant,
    })


def _finish(db: Session, *, actor: User, membership_id: str, event: ADV4ReviewCaseEvent,
            idempotent: bool = False) -> dict[str, Any]:
    with db.no_autoflush:
        current_auth = _authorize(db, actor, membership_id, lock=True)
    _flush_review_history(db, event.case_id)
    history = _verify_case_history(db, event.case_id)
    result = _serialize_case(history, through_event_id=event.id, auth=current_auth)
    result["idempotentRetry"] = idempotent
    return result


def create_review_case(db: Session, *, actor: User, membership_id: str, directive_id: str,
                       proposal_id: str, idempotency_key: str,
                       expected_authorization_observation_hash: str,
                       expected_input_identity_hash: str | None = None) -> dict[str, Any]:
    body = {"expectedInputIdentityHash": expected_input_identity_hash,
            "expectedAuthorizationObservationHash": expected_authorization_observation_hash}
    proposal, auth, observation, prior, request_bytes, request_hash = _mutation_start(
        db, actor=actor, membership_id=membership_id, proposal_id=proposal_id,
        directive_id=directive_id, case_id=None, event_type="case_created",
        idempotency_key=idempotency_key, body=body)
    if prior is not None:
        return _finish(db, actor=actor, membership_id=membership_id, event=prior, idempotent=True)
    cases = _bounded_rows(db, select(ADV4ReviewCase).options(load_only(
        ADV4ReviewCase.id, ADV4ReviewCase.case_sequence)).where(ADV4ReviewCase.proposal_id == proposal.id).order_by(
        ADV4ReviewCase.case_sequence), limit=MAX_CASES_PER_PROPOSAL, label="proposal case history")
    if [case.case_sequence for case in cases] != list(range(len(cases))):
        raise _error("review_integrity", "Review case sequence differs")
    if len(cases) >= MAX_CASES_PER_PROPOSAL:
        raise _error("review_history_limit", "Candidate review-case capacity is exhausted")
    if cases:
        if _verify_case_history(db, cases[-1].id)["events"][-1].resulting_state != "rejected":
            raise _error("review_case_open", "This candidate already has an open review case")
    instant = observation["observed_at"]
    case = _new_record(db, ADV4ReviewCase, {
        **_common(proposal, auth, idempotency_key=idempotency_key,
                  request_bytes=request_bytes, request_hash=request_hash),
        **observation, "proposal_canonical_hash": proposal.canonical_hash,
        "case_sequence": len(cases), "predecessor_case_id": cases[-1].id if cases else None,
        "created_at": instant,
    })
    event = _append_event(db, case=case, proposal=proposal, auth=auth, event_type="case_created",
        instant=instant, predecessor=None, idempotency_key=idempotency_key,
        request_bytes=request_bytes, request_hash=request_hash)
    _flush_review_history(db, case.id, [case])
    return _finish(db, actor=actor, membership_id=membership_id, event=event)


def _existing_mutation(db: Session, *, actor: User, membership_id: str, case_id: str,
                       event_type: str, idempotency_key: str, body: dict[str, Any]) -> tuple[Any, ...]:
    # Authorization precedes aggregate lookup, including direct service callers.
    _require_application_gate(write=True, terminal=event_type == "review_rejected")
    _authorize(db, actor, membership_id, lock=True)
    case = _case(db, case_id)
    result = _mutation_start(db, actor=actor, membership_id=membership_id,
        proposal_id=case.proposal_id, directive_id=case.directive_id, case_id=case.id,
        event_type=event_type, idempotency_key=idempotency_key, body=body)
    case = _case(db, case_id, lock=True)
    if result[3] is not None:
        return case, None, *result
    history = _verify_case_history(db, case.id)
    if len(history["events"]) >= MAX_EVENTS_PER_CASE:
        raise _error("review_history_limit", "Review case event capacity is exhausted")
    head = history["events"][-1]
    if head.event_hash != body["expectedPredecessorEventHash"]:
        raise _error("stale_review_predecessor", "Review event head changed")
    expected_state = "pending_review" if event_type == "review_rejected" else "draft"
    if head.resulting_state != expected_state:
        raise _error("review_lifecycle_conflict", "Review case does not permit this transition")
    return case, history, *result


def save_review_draft(db: Session, *, actor: User, membership_id: str, case_id: str,
                      idempotency_key: str, expected_predecessor_event_hash: str,
                      expected_input_identity_hash: str, expected_authorization_observation_hash: str,
                      annotations: list[dict[str, str]], intended_action: str = "undecided") -> dict[str, Any]:
    _validate_annotations(annotations)
    if intended_action not in {"undecided", "reject"}:
        raise _error("review_payload_invalid", "Draft intent must be undecided or reject", 422)
    body = {"expectedPredecessorEventHash": expected_predecessor_event_hash,
            "expectedInputIdentityHash": expected_input_identity_hash,
            "expectedAuthorizationObservationHash": expected_authorization_observation_hash,
            "annotations": annotations, "intendedAction": intended_action}
    case, history, proposal, auth, observation, prior, request_bytes, request_hash = _existing_mutation(
        db, actor=actor, membership_id=membership_id, case_id=case_id,
        event_type="draft_saved", idempotency_key=idempotency_key, body=body)
    if prior is not None:
        return _finish(db, actor=actor, membership_id=membership_id, event=prior, idempotent=True)
    drafts = history["drafts"]
    if len(drafts) >= MAX_DRAFT_REVISIONS_PER_CASE:
        raise _error("review_history_limit", "Review case draft capacity is exhausted")
    values = {**_common(proposal, auth, idempotency_key=idempotency_key,
                       request_bytes=request_bytes, request_hash=request_hash), **observation, "case_id": case.id,
              "revision_number": len(drafts), "predecessor_draft_id": drafts[-1].id if drafts else None,
              "expected_predecessor_event_hash": expected_predecessor_event_hash,
              "intended_action": intended_action, "created_at": observation["observed_at"]}
    _blob(values, "annotation", "paprnav-ad-v4-review-annotation-1",
          {"version": "paprnav-ad-v4-review-annotation-1", "annotations": annotations})
    draft = _new_record(db, ADV4ReviewDraftRevision, values)
    event = _append_event(db, case=case, proposal=proposal, auth=auth, event_type="draft_saved",
        instant=observation["observed_at"], predecessor=history["events"][-1],
        idempotency_key=idempotency_key, request_bytes=request_bytes, request_hash=request_hash, draft=draft)
    _flush_review_history(db, case.id, [draft])
    return _finish(db, actor=actor, membership_id=membership_id, event=event)


def request_review(db: Session, *, actor: User, membership_id: str, case_id: str,
                   idempotency_key: str, expected_predecessor_event_hash: str,
                   expected_input_identity_hash: str, expected_authorization_observation_hash: str,
                   draft_revision_id: str | None = None) -> dict[str, Any]:
    body = {"expectedPredecessorEventHash": expected_predecessor_event_hash,
            "expectedInputIdentityHash": expected_input_identity_hash,
            "expectedAuthorizationObservationHash": expected_authorization_observation_hash,
            "draftRevisionId": draft_revision_id}
    case, history, proposal, auth, observation, prior, request_bytes, request_hash = _existing_mutation(
        db, actor=actor, membership_id=membership_id, case_id=case_id,
        event_type="review_requested", idempotency_key=idempotency_key, body=body)
    if prior is not None:
        return _finish(db, actor=actor, membership_id=membership_id, event=prior, idempotent=True)
    drafts = history["drafts"]
    if draft_revision_id != (drafts[-1].id if drafts else None):
        raise _error("stale_review_draft", "Review request must freeze the latest draft")
    authorship = _authorship(db, proposal.id)
    values = {**_common(proposal, auth, idempotency_key=idempotency_key,
                       request_bytes=request_bytes, request_hash=request_hash), **observation, "case_id": case.id,
              "draft_revision_id": draft_revision_id,
              "expected_predecessor_event_hash": expected_predecessor_event_hash,
              "authorship_source_count": len(authorship["bindings"]), "requested_at": observation["observed_at"]}
    _blob(values, "cutoff", "paprnav-ad-v4-review-cutoff-1", _cutoff(db, proposal.id))
    _blob(values, "authorship_set", "paprnav-ad-v4-review-authorship-1", authorship)
    request = _new_record(db, ADV4ReviewRequest, values)
    event = _append_event(db, case=case, proposal=proposal, auth=auth, event_type="review_requested",
        instant=observation["observed_at"], predecessor=history["events"][-1],
        idempotency_key=idempotency_key, request_bytes=request_bytes, request_hash=request_hash, request=request)
    _flush_review_history(db, case.id, [request])
    return _finish(db, actor=actor, membership_id=membership_id, event=event)


def reject_review_case(db: Session, *, actor: User, membership_id: str, case_id: str,
                       idempotency_key: str, expected_predecessor_event_hash: str,
                       expected_request_id: str, expected_input_identity_hash: str,
                       expected_authorization_observation_hash: str, reason_codes: list[str],
                       explanation: str) -> dict[str, Any]:
    _validate_reasons(reason_codes, explanation)
    body = {"expectedPredecessorEventHash": expected_predecessor_event_hash,
            "expectedRequestId": expected_request_id, "expectedInputIdentityHash": expected_input_identity_hash,
            "expectedAuthorizationObservationHash": expected_authorization_observation_hash,
            "reasonCodes": sorted(reason_codes), "explanation": explanation}
    case, history, proposal, auth, observation, prior, request_bytes, request_hash = _existing_mutation(
        db, actor=actor, membership_id=membership_id, case_id=case_id,
        event_type="review_rejected", idempotency_key=idempotency_key, body=body)
    if prior is not None:
        return _finish(db, actor=actor, membership_id=membership_id, event=prior, idempotent=True)
    request = history["requests"][0]
    if expected_request_id != request.id:
        raise _error("stale_review_request", "Review rejection must bind the frozen request")
    codes = set(reason_codes)
    if request.input_identity_hash != observation["input_identity_hash"]:
        codes.add("input_changed")
    instant = observation["observed_at"]
    values = {**_common(proposal, auth, idempotency_key=idempotency_key,
                       request_bytes=request_bytes, request_hash=request_hash), "case_id": case.id, "request_id": request.id,
              "proposal_canonical_hash": case.proposal_canonical_hash,
              "requested_input_identity_hash": request.input_identity_hash,
              "requested_observation_hash": request.observation_hash,
              "decision_input_identity_bytes": observation["input_identity_bytes"],
              "decision_input_identity_hash": observation["input_identity_hash"],
              "decision_observation_bytes": observation["observation_bytes"],
              "decision_observation_hash": observation["observation_hash"],
              "decision_observed_at": instant, "expected_predecessor_event_hash": expected_predecessor_event_hash,
              "rejected_at": instant}
    _blob(values, "reasons", "paprnav-ad-v4-review-reasons-1",
          {"version": "paprnav-ad-v4-review-reasons-1", "codes": sorted(codes), "explanation": explanation})
    rejection = _new_record(db, ADV4ReviewRejection, values)
    signoff = _new_record(db, ADV4SignoffEvent, {
        **_common(proposal, auth, idempotency_key=idempotency_key,
                  request_bytes=request_bytes, request_hash=request_hash), "case_id": case.id, "request_id": request.id,
        "rejection_id": rejection.id, "action": "reject", "rejection_hash": rejection.row_hash,
        "requested_input_identity_hash": request.input_identity_hash,
        "requested_observation_hash": request.observation_hash,
        "decision_input_identity_hash": rejection.decision_input_identity_hash,
        "decision_observation_hash": rejection.decision_observation_hash,
        "authorization_observation_hash": auth["authorizationObservationHash"], "signed_at": instant,
    })
    event = _append_event(db, case=case, proposal=proposal, auth=auth, event_type="review_rejected",
        instant=instant, predecessor=history["events"][-1], idempotency_key=idempotency_key,
        request_bytes=request_bytes, request_hash=request_hash, request=request, rejection=rejection, signoff=signoff)
    _flush_review_history(db, case.id, [rejection])
    _flush_review_history(db, case.id, [signoff])
    return _finish(db, actor=actor, membership_id=membership_id, event=event)


_BLOB_DOMAINS = {
    "auth_snapshot": "paprnav-ad-v4-review-authorization-1",
    "input_identity": INPUT_VERSION, "decision_input_identity": INPUT_VERSION,
    "observation": OBSERVATION_VERSION, "decision_observation": OBSERVATION_VERSION,
    "annotation": "paprnav-ad-v4-review-annotation-1",
    "cutoff": "paprnav-ad-v4-review-cutoff-1",
    "authorship_set": "paprnav-ad-v4-review-authorship-1",
    "reasons": "paprnav-ad-v4-review-reasons-1",
    "request_canonical": "paprnav-ad-v4-review-request-1",
}
_REQUEST_BODY_KEYS = {
    "case_created": {"expectedAuthorizationObservationHash", "expectedInputIdentityHash"},
    "draft_saved": {"expectedAuthorizationObservationHash", "expectedInputIdentityHash",
                    "expectedPredecessorEventHash", "annotations", "intendedAction"},
    "review_requested": {"expectedAuthorizationObservationHash", "expectedInputIdentityHash",
                         "expectedPredecessorEventHash", "draftRevisionId"},
    "review_rejected": {"expectedAuthorizationObservationHash", "expectedInputIdentityHash",
                        "expectedPredecessorEventHash", "expectedRequestId", "reasonCodes", "explanation"},
}


def _validate_annotations(annotations: Any) -> None:
    if not isinstance(annotations, list) or len(annotations) > 128:
        raise _error("review_payload_invalid", "At most 128 review annotations are allowed", 422)
    for annotation in annotations:
        if (not isinstance(annotation, dict) or set(annotation) != {"pointer", "text"}
            or not isinstance(annotation["pointer"], str) or not 1 <= len(annotation["pointer"]) <= 1024
            or not annotation["pointer"].startswith("/") or re.search(r"~(?![01])", annotation["pointer"])
            or not isinstance(annotation["text"], str) or not annotation["text"].strip()
            or len(annotation["text"]) > 4096):
            raise _error("review_payload_invalid", "Review annotations require a JSON pointer and bounded text", 422)
    review_canonical_bytes(annotations)


def _validate_reasons(codes: Any, explanation: Any) -> None:
    if (not isinstance(codes, list) or not 1 <= len(codes) <= 7
        or any(not isinstance(code, str) or code not in REASON_CODES for code in codes)
        or len(set(codes)) != len(codes) or not isinstance(explanation, str)
        or not explanation.strip() or len(explanation) > 4096):
        raise _error("review_payload_invalid", "Rejection requires distinct controlled reasons and bounded explanation", 422)
    review_canonical_bytes({"codes": codes, "explanation": explanation})


def _read_blob(encoded: bytes) -> Any:
    try:
        if not isinstance(encoded, bytes) or not 2 <= len(encoded) <= MAX_BYTES:
            raise ValueError("blob size differs")
        value = json.loads(encoded.decode("utf-8"))
        if review_canonical_bytes(value) != encoded:
            raise ValueError("blob is not canonical")
        return value
    except (ValueError, TypeError, UnicodeError) as exc:
        raise _error("review_integrity", "Review canonical blob differs") from exc


def _verify_observation(row: Any, *, decision: bool = False) -> None:
    prefix = "decision_" if decision else ""
    identity = _read_blob(getattr(row, prefix + "input_identity_bytes"))
    audit = _read_blob(getattr(row, prefix + "observation_bytes"))
    if (not isinstance(identity, dict) or set(identity) != {
        "version", "directiveId", "proposal", "evidence", "applicabilityProjection", "obligationProjection"}
        or identity["version"] != INPUT_VERSION or identity["directiveId"] != row.directive_id
        or audit != {"version": OBSERVATION_VERSION,
                     "inputIdentityHash": getattr(row, prefix + "input_identity_hash"),
                     "observedAt": _time(getattr(row, prefix + "observed_at"))}):
        raise _error("review_integrity", "Review observation envelope differs")
    for family in ("proposal", "evidence", "applicabilityProjection", "obligationProjection"):
        component = identity[family]
        if not isinstance(component, dict):
            raise _error("review_integrity", "Review observation component differs")
        state = component.get("state")
        if state not in {"verified", "missing", "stale", "integrity_error", "unsupported_version"}:
            raise _error("review_integrity", "Review observation state differs")
        if any(value is None for value in component.values()):
            raise _error("review_integrity", "Review observation must preserve field absence")
        if state == "verified":
            if "errorCode" in component:
                raise _error("review_integrity", "Verified review observation has an error")
        elif (component.get("errorCode") not in {
            "candidate_integrity", "evidence_integrity", "evidence_not_current", "projection_integrity",
            "projection_missing", "projection_stale", "unsupported_version", "unsupported_validator",
            "missing_evidence", "source_identity_or_evidence_missing"}
            or {"verifiedCanonicalHash", "verifiedBindingHash"} & set(component)):
            raise _error("review_integrity", "Nonverified review observation differs")
        if family == "proposal":
            expected = {"state", "id", "storedCanonicalHash",
                        "verifiedCanonicalHash" if state == "verified" else "errorCode"}
            if (set(component) != expected or state == "missing" or component["id"] != row.proposal_id
                or (state == "verified" and component["verifiedCanonicalHash"] != component["storedCanonicalHash"])):
                raise _error("review_integrity", "Observed proposal identity differs")
        elif family == "evidence":
            allowed = {"state", "storedBindingHash", "verifiedBindingHash", "headSetHash", "errorCode"}
            if (not set(component) <= allowed or "storedBindingHash" not in component
                or (state == "verified" and (not {"verifiedBindingHash", "headSetHash"} <= set(component)
                    or component["verifiedBindingHash"] != component["storedBindingHash"]))):
                raise _error("review_integrity", "Observed evidence identity differs")
        elif (not set(component) <= {"state", "id", "storedHash", "eventHeadHash", "errorCode"}
              or (state == "missing" and set(component) != {"state", "errorCode"})
              or (state == "verified" and set(component) != {"state", "id", "storedHash", "eventHeadHash"})):
            raise _error("review_integrity", "Observed projection identity differs")
        for key, value in component.items():
            if key.endswith("Hash") and (not isinstance(value, str) or not _HASH.fullmatch(value)):
                raise _error("review_integrity", "Observed digest encoding differs")


def _verify_observation_sources(db: Session, row: Any, *, decision: bool = False) -> None:
    prefix = "decision_" if decision else ""
    identity = _read_blob(getattr(row, prefix + "input_identity_bytes"))
    proposal = _proposal(db, row.proposal_id)
    if (identity["proposal"]["storedCanonicalHash"] != proposal.canonical_hash
        or identity["evidence"]["storedBindingHash"] != proposal.evidence_binding_hash):
        raise _error("review_integrity", "Frozen observation differs from immutable candidate identity")
    if identity["evidence"]["state"] == "verified":
        heads = {}
        for binding in db.scalars(select(ADV4CandidateEvidenceBinding).where(
            ADV4CandidateEvidenceBinding.proposal_id == proposal.id)):
            admission = _fresh(db, ADEvidenceFragmentLifecycleEvent, id=binding.admitted_event_id)
            if (admission is None or admission.fragment_id != binding.fragment_id
                or admission.event_hash != binding.admitted_event_hash):
                raise _error("review_integrity", "Frozen evidence admission differs")
            heads[binding.fragment_id] = {"fragmentId": binding.fragment_id, "eventId": admission.id,
                                          "eventHash": admission.event_hash, "sequenceNumber": admission.sequence_number}
        expected = review_hash("paprnav-ad-v4-review-evidence-heads-1",
                               review_canonical_bytes([heads[key] for key in sorted(heads)]))
        if not heads or identity["evidence"]["headSetHash"] != expected:
            raise _error("review_integrity", "Frozen evidence head identity differs")
    for name, model, event_model in (
        ("applicabilityProjection", ADV4CandidateAppProjection, ADV4CandidateAppProjectionEvent),
        ("obligationProjection", ADV4CandidateObligationProjection, ADV4CandidateObligationProjectionEvent),
    ):
        component = identity[name]
        if "id" not in component:
            continue
        projection = _fresh(db, model, id=component["id"])
        if (projection is None or projection.proposal_id != proposal.id
            or projection.directive_id != row.directive_id
            or component.get("storedHash", projection.projection_hash) != projection.projection_hash):
            raise _error("review_integrity", "Frozen projection identity differs")
        if "eventHeadHash" in component:
            event = db.scalar(select(event_model.id).where(event_model.projection_id == projection.id,
                event_model.event_hash == component["eventHeadHash"]))
            if event is None:
                raise _error("review_integrity", "Frozen projection event head differs")


def _verify_record(row: Any, *, action: str, instant: datetime, case: ADV4ReviewCase) -> dict[str, Any]:
    if row.contract_version != CONTRACT_VERSION:
        raise _error("historical_verifier_unavailable", "Historical V4 review verifier is unavailable")
    values = {column.name: getattr(row, column.name) for column in row.__table__.columns}
    if (row.proposal_id != case.proposal_id or row.directive_id != case.directive_id
        or (hasattr(row, "case_id") and row.case_id != case.id)
        or row.endpoint_action != action or row.auth_policy_version != "1"
        or not row.idempotency_key.strip() or len(row.idempotency_key) > 255
        or row.canonical_bytes != review_canonical_bytes(_record_envelope(type(row), values))):
        raise _error("review_integrity", "Review row identity or canonical envelope differs")
    digest = row.event_hash if isinstance(row, ADV4ReviewCaseEvent) else row.row_hash
    if digest != review_hash("paprnav-ad-v4-review-row-1", row.canonical_bytes):
        raise _error("review_integrity", "Review row digest differs")
    blobs = {}
    for key, value in values.items():
        if key.endswith("_hash") and value is not None and (not isinstance(value, str) or not _HASH.fullmatch(value)):
            raise _error("review_integrity", "Review digest encoding differs")
        if key.endswith("_bytes") and key != "canonical_bytes":
            name = key[:-6]
            payload = _read_blob(value)
            hash_name = "request_hash" if name == "request_canonical" else name + "_hash"
            if name not in _BLOB_DOMAINS or values[hash_name] != review_hash(_BLOB_DOMAINS[name], value):
                raise _error("review_integrity", "Review nested blob digest differs")
            blobs[name] = payload
    auth = blobs["auth_snapshot"]
    auth_keys = {"version", "policyName", "policyVersion", "actorUserId", "authorizingMembershipId",
                 "organizationId", "userStatus", "membershipStatus", "role", "validityRule",
                 "validFrom", "validUntil", "serverAuthorized", "userUpdatedAt", "membershipUpdatedAt",
                 "action", "decisionTime", "authorizationObservationHash", "claimsHash"}
    if (not isinstance(auth, dict) or set(auth) != auth_keys
        or auth["version"] != "paprnav-ad-v4-review-authorization-1"
        or auth["policyName"] != CONTRACT_VERSION or auth["policyVersion"] != "1"
        or auth["actorUserId"] != row.actor_user_id or auth["authorizingMembershipId"] != row.authorizing_membership_id
        or auth["organizationId"] != row.organization_id or auth["userStatus"] != "active"
        or auth["membershipStatus"] != "active" or auth["role"] != "platform_admin"
        or auth["validityRule"] != "status_only_v1" or auth["validFrom"] is not None
        or auth["validUntil"] is not None or auth["serverAuthorized"] is not True
        or auth["action"] != action or auth["decisionTime"] != _time(instant)):
        raise _error("review_integrity", "Historical authorization snapshot differs")
    for name in ("userUpdatedAt", "membershipUpdatedAt", "decisionTime"):
        if not isinstance(auth[name], str) or not re.fullmatch(
            r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{6}Z", auth[name]):
            raise _error("review_integrity", "Historical authorization timestamp differs")
    stable = {key: value for key, value in auth.items()
              if key not in {"authorizationObservationHash", "claimsHash", "decisionTime"}}
    if (auth["authorizationObservationHash"] != review_hash(
        "paprnav-ad-v4-review-auth-observation-1", review_canonical_bytes(stable))
        or auth["claimsHash"] != review_hash("paprnav-ad-v4-review-claims-1", review_canonical_bytes(stable))):
        raise _error("review_integrity", "Historical authorization digest differs")
    if isinstance(row, (ADV4ReviewCase, ADV4ReviewDraftRevision, ADV4ReviewRequest)):
        _verify_observation(row)
    if isinstance(row, ADV4ReviewRejection):
        _verify_observation(row, decision=True)
    if isinstance(row, ADV4SignoffEvent):
        if (row.action != "reject" or row.authorization_observation_hash != auth["authorizationObservationHash"]
            or row.signature_hash != review_hash("paprnav-ad-v4-review-signature-1", row.canonical_bytes)):
            raise _error("review_integrity", "Historical rejecting signature differs")
    return blobs


def _verify_frozen_sources(db: Session, request: ADV4ReviewRequest, blobs: dict[str, Any]) -> None:
    cutoff = blobs["cutoff"]
    if (not isinstance(cutoff, dict) or set(cutoff) != {"version", "proposalId", "submissions", "relationships",
        "fragmentHeads", "applicabilityHeads", "obligationHeads"}
        or cutoff["version"] != "paprnav-ad-v4-review-cutoff-1" or cutoff["proposalId"] != request.proposal_id):
        raise _error("review_integrity", "Frozen review cutoff differs")
    for name, model, digest_name in (("submissions", ADV4CandidateSubmission, "request_hash"),
                                     ("relationships", ADV4CandidateSubmissionRelationship, "relationship_hash")):
        items = cutoff[name]
        if not isinstance(items, list) or len(items) > MAX_ARRAY_ITEMS or items != sorted(items, key=lambda row: row["id"]):
            raise _error("review_integrity", "Frozen source order differs")
        if len({item["id"] for item in items}) != len(items):
            raise _error("review_integrity", "Frozen source identity is duplicated")
        columns = [model.id, getattr(model, digest_name)]
        if name == "submissions":
            columns.append(ADV4CandidateSubmission.proposal_id)
        else:
            columns.extend((ADV4CandidateSubmissionRelationship.submission_id,
                            ADV4CandidateSubmissionRelationship.predecessor_proposal_id))
        sources = {row.id: row for row in db.execute(select(*columns).where(
            model.id.in_({item["id"] for item in items})))}
        relationship_submissions = {}
        if name == "relationships":
            relationship_submissions = {row.id: row for row in db.execute(select(
                ADV4CandidateSubmission.id, ADV4CandidateSubmission.proposal_id,
            ).where(ADV4CandidateSubmission.id.in_(
                {row.submission_id for row in sources.values()})))}
        for item in items:
            source = sources.get(item["id"])
            if set(item) != {"id", "hash"} or source is None or getattr(source, digest_name) != item["hash"]:
                raise _error("review_integrity", "Frozen review source hash differs")
            if name == "submissions" and source.proposal_id != request.proposal_id:
                raise _error("review_integrity", "Frozen submission belongs to another proposal")
            if name == "relationships":
                submission = relationship_submissions.get(source.submission_id)
                if submission is None or (submission.proposal_id != request.proposal_id
                                          and source.predecessor_proposal_id != request.proposal_id):
                    raise _error("review_integrity", "Frozen relationship belongs to another proposal")
    for name, model, owner_column, owner_key in (
        ("fragmentHeads", ADEvidenceFragmentLifecycleEvent, "fragment_id", "fragmentId"),
        ("applicabilityHeads", ADV4CandidateAppProjectionEvent, "projection_id", "projectionId"),
        ("obligationHeads", ADV4CandidateObligationProjectionEvent, "projection_id", "projectionId"),
    ):
        items = cutoff[name]
        if not isinstance(items, list) or items != sorted(items, key=lambda item: item[owner_key]):
            raise _error("review_integrity", "Frozen event order differs")
        if len({item[owner_key] for item in items}) != len(items):
            raise _error("review_integrity", "Frozen event owner is duplicated")
        owner_attribute = getattr(model, owner_column)
        sources = {row.id: row for row in db.execute(select(
            model.id, owner_attribute, model.event_hash, model.sequence_number,
        ).where(model.id.in_({item["eventId"] for item in items})))}
        for item in items:
            source = sources.get(item["eventId"])
            if (set(item) != {owner_key, "eventId", "eventHash", "sequenceNumber"}
                or source is None or getattr(source, owner_column) != item[owner_key]
                or source.event_hash != item["eventHash"] or source.sequence_number != item["sequenceNumber"]):
                raise _error("review_integrity", "Frozen event source differs")
    authors = _authorship(db, request.proposal_id, submission_ids={item["id"] for item in cutoff["submissions"]})
    if blobs["authorship_set"] != authors or request.authorship_source_count != len(authors["bindings"]):
        raise _error("review_integrity", "Frozen authorship differs from its source set")


def _verify_case_history_unchecked(db: Session, case_id: str, *,
                                    source_cache: set[str] | None = None) -> dict[str, Any]:
    if source_cache is None:
        source_cache = set()
    case = _case(db, case_id)
    if not 0 <= case.case_sequence < MAX_CASES_PER_PROPOSAL:
        raise _error("review_integrity", "Review case sequence exceeds the proposal bound")
    history: dict[str, Any] = {"case": case}
    for name, model, order, bound in (
        ("events", ADV4ReviewCaseEvent, ADV4ReviewCaseEvent.sequence_number, MAX_EVENTS_PER_CASE),
        ("drafts", ADV4ReviewDraftRevision, ADV4ReviewDraftRevision.revision_number, MAX_DRAFT_REVISIONS_PER_CASE),
        ("requests", ADV4ReviewRequest, ADV4ReviewRequest.id, 1),
        ("rejections", ADV4ReviewRejection, ADV4ReviewRejection.id, 1),
        ("signoffs", ADV4SignoffEvent, ADV4SignoffEvent.id, 1),
    ):
        history[name] = _bounded_rows(db, select(model).where(model.case_id == case.id).order_by(
            order), limit=bound, label=name)
    events, drafts, requests, rejections, signoffs = (history[name] for name in (
        "events", "drafts", "requests", "rejections", "signoffs"))
    if (not events or [event.sequence_number for event in events] != list(range(len(events)))
        or [draft.revision_number for draft in drafts] != list(range(len(drafts)))
        or any(len(history[name]) > 1 for name in ("requests", "rejections", "signoffs"))):
        raise _error("review_integrity", "Review history cardinality differs")
    proposal = _proposal(db, case.proposal_id)
    if case.proposal_canonical_hash != proposal.canonical_hash or case.directive_id != proposal.directive_id:
        raise _error("review_integrity", "Review case proposal identity differs")
    terminated = select(ADV4ReviewCaseEvent.case_id).where(ADV4ReviewCaseEvent.event_type == "review_rejected")
    open_cases = list(db.scalars(select(ADV4ReviewCase.id).where(
        ADV4ReviewCase.proposal_id == case.proposal_id, ADV4ReviewCase.id.not_in(terminated)).limit(2)))
    if len(open_cases) > 1:
        raise _error("review_integrity", "Candidate has multiple open review cases")
    proposal_cases = _bounded_rows(db, select(ADV4ReviewCase).options(load_only(
        ADV4ReviewCase.id, ADV4ReviewCase.case_sequence)).where(
        ADV4ReviewCase.proposal_id == case.proposal_id).order_by(ADV4ReviewCase.case_sequence),
        limit=MAX_CASES_PER_PROPOSAL, label="proposal cases and predecessors")
    if [row.case_sequence for row in proposal_cases] != list(range(len(proposal_cases))):
        raise _error("review_integrity", "Proposal case sequence differs")
    predecessor_cases = [row for row in proposal_cases if row.case_sequence < case.case_sequence]
    if ([row.case_sequence for row in predecessor_cases] != list(range(case.case_sequence))
        or case.predecessor_case_id != (predecessor_cases[-1].id if predecessor_cases else None)):
        raise _error("review_integrity", "Review case predecessor sequence differs")
    if predecessor_cases:
        predecessor_ids = {row.id for row in predecessor_cases}
        terminal_ids = _bounded_rows(db, select(ADV4ReviewCaseEvent.case_id).where(
            ADV4ReviewCaseEvent.case_id.in_(predecessor_ids),
            ADV4ReviewCaseEvent.event_type == "review_rejected"),
            limit=MAX_CASES_PER_PROPOSAL, label="predecessor terminal events")
        if len(terminal_ids) != len(predecessor_ids) or set(terminal_ids) != predecessor_ids:
            raise _error("review_integrity", "Review successor follows an open case")
    draft_by_id = {row.id: row for row in drafts}
    request = requests[0] if requests else None
    rejection = rejections[0] if rejections else None
    signoff = signoffs[0] if signoffs else None
    seen_drafts: list[str] = []
    seen_request = seen_rejection = False
    previous = None
    for event in events:
        action = ACTIONS.get(event.event_type)
        if (action is None or event.predecessor_event_hash != (previous.event_hash if previous else None)
            or event.endpoint_action != action or event.auth_policy_version != "1"
            or not event.idempotency_key.strip() or len(event.idempotency_key) > 255):
            raise _error("review_integrity", "Review lifecycle identity differs")
        event_blobs = _verify_record(event, action=action, instant=event.occurred_at, case=case)
        envelope = event_blobs["request_canonical"]
        if (not isinstance(envelope, dict) or set(envelope) != {"version", "action", "directiveId", "proposalId", "caseId", "body"}
            or envelope["version"] != CONTRACT_VERSION or envelope["action"] != action
            or envelope["directiveId"] != case.directive_id or envelope["proposalId"] != case.proposal_id
            or envelope["caseId"] != (None if event.event_type == "case_created" else case.id)
            or not isinstance(envelope["body"], dict)):
            raise _error("review_integrity", "Review canonical request differs")
        body = envelope["body"]
        if set(body) != _REQUEST_BODY_KEYS[event.event_type]:
            raise _error("review_integrity", "Review request body is outside its closed branch")
        if body.get("expectedAuthorizationObservationHash") != event_blobs["auth_snapshot"]["authorizationObservationHash"]:
            raise _error("review_integrity", "Review authorization CAS differs")
        if previous is not None and body.get("expectedPredecessorEventHash") != previous.event_hash:
            raise _error("review_integrity", "Review predecessor CAS differs")
        if event.event_type == "case_created":
            if previous is not None or event.resulting_state != "draft" or any(
                (event.draft_revision_id, event.review_request_id, event.rejection_id, event.signoff_id)):
                raise _error("review_integrity", "Review creation event differs")
            owner, stamp = case, case.created_at
            if body.get("expectedInputIdentityHash") not in {None, case.input_identity_hash}:
                raise _error("review_integrity", "Review creation input CAS differs")
        elif event.event_type == "draft_saved":
            owner = draft_by_id.get(event.draft_revision_id)
            if (previous is None or previous.resulting_state != "draft" or event.resulting_state != "draft"
                or owner is None or event.review_request_id or event.rejection_id or event.signoff_id
                or owner.predecessor_draft_id != (seen_drafts[-1] if seen_drafts else None)
                or owner.revision_number != len(seen_drafts)
                or owner.expected_predecessor_event_hash != event.predecessor_event_hash):
                raise _error("review_integrity", "Review draft transition differs")
            stamp = owner.created_at
            seen_drafts.append(owner.id)
        elif event.event_type == "review_requested":
            owner = request
            if (previous is None or previous.resulting_state != "draft" or event.resulting_state != "pending_review"
                or owner is None or event.review_request_id != owner.id or seen_request
                or event.draft_revision_id or event.rejection_id or event.signoff_id
                or owner.draft_revision_id != (seen_drafts[-1] if seen_drafts else None)
                or owner.expected_predecessor_event_hash != event.predecessor_event_hash):
                raise _error("review_integrity", "Review request transition differs")
            stamp = owner.requested_at
            seen_request = True
        else:
            owner = rejection
            if (previous is None or previous.resulting_state != "pending_review" or event.resulting_state != "rejected"
                or not seen_request or seen_rejection or owner is None or signoff is None or request is None
                or event.rejection_id != owner.id or event.signoff_id != signoff.id
                or event.review_request_id != request.id or event.draft_revision_id
                or owner.request_id != request.id or signoff.request_id != request.id or signoff.rejection_id != owner.id
                or owner.expected_predecessor_event_hash != event.predecessor_event_hash
                or owner.proposal_canonical_hash != case.proposal_canonical_hash
                or owner.requested_input_identity_hash != request.input_identity_hash
                or owner.requested_observation_hash != request.observation_hash
                or signoff.requested_input_identity_hash != request.input_identity_hash
                or signoff.requested_observation_hash != request.observation_hash
                or signoff.decision_input_identity_hash != owner.decision_input_identity_hash
                or signoff.decision_observation_hash != owner.decision_observation_hash
                or signoff.rejection_hash != owner.row_hash
                or signoff.request_hash != owner.request_hash
                or signoff.request_canonical_bytes != owner.request_canonical_bytes
                or signoff.idempotency_key != owner.idempotency_key
                or signoff.auth_snapshot_bytes != owner.auth_snapshot_bytes
                or _time(signoff.signed_at) != _time(owner.rejected_at)):
                raise _error("review_integrity", "Review rejection signoff transition differs")
            _verify_record(signoff, action=action, instant=signoff.signed_at, case=case)
            stamp = owner.rejected_at
            seen_rejection = True
        owner_blobs = _verify_record(owner, action=action, instant=stamp, case=case)
        is_rejection = isinstance(owner, ADV4ReviewRejection)
        source_hash = owner.decision_input_identity_hash if is_rejection else owner.input_identity_hash
        if source_hash not in source_cache:
            _verify_observation_sources(db, owner, decision=is_rejection)
            source_cache.add(source_hash)
        if (owner.auth_snapshot_bytes != event.auth_snapshot_bytes or _time(stamp) != _time(event.occurred_at)
            or owner.idempotency_key != event.idempotency_key or owner.request_hash != event.request_hash
            or owner.request_canonical_bytes != event.request_canonical_bytes):
            raise _error("review_integrity", "Review event authorization differs from its object")
        if event.event_type != "case_created":
            actual_input = owner.decision_input_identity_hash if event.event_type == "review_rejected" else owner.input_identity_hash
            if body.get("expectedInputIdentityHash") != actual_input:
                raise _error("review_integrity", "Review input CAS differs")
        if event.event_type == "draft_saved":
            annotation = owner_blobs["annotation"]
            if annotation != {"version": "paprnav-ad-v4-review-annotation-1", "annotations": body.get("annotations")}:
                raise _error("review_integrity", "Draft annotations differ from submitted request")
            _validate_annotations(annotation["annotations"])
            if owner.intended_action != body.get("intendedAction") or owner.intended_action not in {"undecided", "reject"}:
                raise _error("review_integrity", "Draft intent differs")
        elif event.event_type == "review_requested":
            if body.get("draftRevisionId") != owner.draft_revision_id:
                raise _error("review_integrity", "Frozen draft differs from submitted request")
            _verify_frozen_sources(db, owner, owner_blobs)
        elif event.event_type == "review_rejected":
            reasons = owner_blobs["reasons"]
            _validate_reasons(body.get("reasonCodes"), body.get("explanation"))
            codes = set(body["reasonCodes"])
            if owner.decision_input_identity_hash != request.input_identity_hash:
                codes.add("input_changed")
            if (body.get("expectedRequestId") != request.id or reasons != {
                "version": "paprnav-ad-v4-review-reasons-1", "codes": sorted(codes), "explanation": body["explanation"]}):
                raise _error("review_integrity", "Rejection reasons differ from submitted request")
        previous = event
    if (len(seen_drafts) != len(drafts) or bool(requests) != seen_request
        or bool(rejections) != seen_rejection or bool(signoffs) != seen_rejection):
        raise _error("review_integrity", "Review object-event completeness differs")
    return history


def _verify_case_history(db: Session, case_id: str, *, source_cache: set[str] | None = None) -> dict[str, Any]:
    try:
        return _verify_case_history_unchecked(db, case_id, source_cache=source_cache)
    except ADV4Error as exc:
        if exc.http_status == 422:
            raise _error("review_integrity", "Stored review payload fails its historical contract") from exc
        raise
    except (KeyError, TypeError, AttributeError, ValueError, StopIteration) as exc:
        raise _error("review_integrity", "Stored review history is malformed") from exc


def _history_payload(row: Any) -> dict[str, Any]:
    common = {"rowHash": row.row_hash, "actorUserId": row.actor_user_id,
              "authorizingMembershipId": row.authorizing_membership_id}
    if isinstance(row, ADV4ReviewDraftRevision):
        return {**common, "draftRevisionId": row.id, "revisionNumber": row.revision_number,
                "inputIdentityHash": row.input_identity_hash, "observationHash": row.observation_hash,
                "annotations": _read_blob(row.annotation_bytes)["annotations"],
                "intendedAction": row.intended_action, "createdAt": row.created_at}
    if isinstance(row, ADV4ReviewRequest):
        return {**common, "reviewRequestId": row.id, "draftRevisionId": row.draft_revision_id,
                "inputIdentityHash": row.input_identity_hash, "observationHash": row.observation_hash,
                "cutoffHash": row.cutoff_hash, "authorshipSetHash": row.authorship_set_hash,
                "authorshipSourceCount": row.authorship_source_count, "requestedAt": row.requested_at}
    common.update(reviewRequestId=row.request_id,
                  requestedInputIdentityHash=row.requested_input_identity_hash,
                  requestedObservationHash=row.requested_observation_hash,
                  decisionInputIdentityHash=row.decision_input_identity_hash,
                  decisionObservationHash=row.decision_observation_hash)
    if isinstance(row, ADV4ReviewRejection):
        reasons = _read_blob(row.reasons_bytes)
        return {**common, "rejectionId": row.id, "reasonCodes": reasons["codes"],
                "explanation": reasons["explanation"], "rejectedAt": row.rejected_at}
    return {**common, "signoffId": row.id, "rejectionId": row.rejection_id, "action": row.action,
            "authorizationObservationHash": row.authorization_observation_hash,
            "signatureHash": row.signature_hash, "signedAt": row.signed_at}


def _serialize_case(history: dict[str, Any], *, through_event_id: str | None = None,
                    observation: dict[str, Any] | None = None,
                    auth: dict[str, Any] | None = None, draft_limit: int = 100,
                    draft_offset: int = 0, event_limit: int = 100,
                    event_offset: int = 0, summary_only: bool = False) -> dict[str, Any]:
    case = history["case"]
    events = history["events"]
    if through_event_id is not None:
        index = next(index for index, event in enumerate(events) if event.id == through_event_id)
        events = events[:index + 1]
    last = events[-1]
    drafts = [row for row in history["drafts"] if row.id in {event.draft_revision_id for event in events}]
    request = next((row for row in history["requests"] if row.id in {event.review_request_id for event in events}), None)
    rejection = next((row for row in history["rejections"] if row.id == last.rejection_id), None)
    signoff = next((row for row in history["signoffs"] if row.id == last.signoff_id), None)
    bound = rejection or request or (drafts[-1] if drafts else case)
    if observation is None:
        prefix = "decision_" if rejection else ""
        observation = {name: getattr(bound, prefix + name) for name in (
            "input_identity_bytes", "input_identity_hash", "observation_bytes", "observation_hash", "observed_at")}
    return {
        "caseId": case.id, "proposalId": case.proposal_id, "directiveId": case.directive_id,
        "caseSequence": case.case_sequence, "state": last.resulting_state,
        "proposalCanonicalHash": case.proposal_canonical_hash,
        "inputIdentityHash": observation["input_identity_hash"], "observationHash": observation["observation_hash"],
        "inputIdentity": _read_blob(observation["input_identity_bytes"]),
        "observation": _read_blob(observation["observation_bytes"]),
        "authorizationObservationHashes": _auth_hashes(auth) if auth is not None else {},
        "latestEventHash": last.event_hash, "draftRevisionId": drafts[-1].id if drafts else None,
        "reviewRequestId": request.id if request else None, "rejectionId": rejection.id if rejection else None,
        "signoffId": signoff.id if signoff else None,
        "drafts": [] if summary_only else [_history_payload(row) for row in drafts[draft_offset:draft_offset + draft_limit]],
        "draftTotal": len(drafts), "draftLimit": draft_limit, "draftOffset": draft_offset,
        "eventTotal": len(events), "eventLimit": event_limit, "eventOffset": event_offset,
        "reviewRequest": _history_payload(request) if request else None,
        "rejection": _history_payload(rejection) if rejection else None,
        "signoff": _history_payload(signoff) if signoff else None,
        "events": [] if summary_only else [{"eventId": event.id, "sequenceNumber": event.sequence_number,
                    "predecessorEventHash": event.predecessor_event_hash,
                    "eventType": event.event_type, "resultingState": event.resulting_state,
                    "eventHash": event.event_hash, "actorUserId": event.actor_user_id,
                    "authorizingMembershipId": event.authorizing_membership_id,
                    "occurredAt": event.occurred_at} for event in events[event_offset:event_offset + event_limit]],
        "createdAt": case.created_at,
    }


def verified_review_case(db: Session, *, case_id: str, actor: User, membership_id: str,
                         draft_limit: int = 100, draft_offset: int = 0,
                         event_limit: int = 100, event_offset: int = 0) -> dict[str, Any]:
    auth = authorize_review_audit(db, actor, membership_id)
    for limit, offset in ((draft_limit, draft_offset), (event_limit, event_offset)):
        if type(limit) is not int or not 1 <= limit <= 100 or type(offset) is not int or not 0 <= offset <= 10000:
            raise _error("review_page_invalid", "Review history pagination is outside the supported bounds", 422)
    with db.no_autoflush:
        try:
            history = _verify_case_history(db, case_id)
            observation = observe_review_inputs(db, history["case"].proposal_id)
            return _serialize_case(history, observation=observation, auth=auth,
                draft_limit=draft_limit, draft_offset=draft_offset,
                event_limit=event_limit, event_offset=event_offset)
        except ADV4Error as exc:
            if exc.http_status == 422:
                raise _error("review_integrity", "Stored review payload fails its historical contract") from exc
            raise
        except (KeyError, TypeError, AttributeError, ValueError, StopIteration) as exc:
            raise _error("review_integrity", "Stored review history is malformed") from exc


def review_proposal_observation(db: Session, *, directive_id: str, proposal_id: str,
                                actor: User, membership_id: str) -> dict[str, Any]:
    auth = authorize_review_audit(db, actor, membership_id)
    with db.no_autoflush:
        proposal = _proposal(db, proposal_id)
        if proposal.directive_id != directive_id:
            raise _error("not_found", "V4 candidate does not belong to the requested directive", 404)
        observation = observe_review_inputs(db, proposal.id)
        return {"proposalId": proposal.id, "directiveId": directive_id,
                "inputIdentityHash": observation["input_identity_hash"],
                "observationHash": observation["observation_hash"],
                "inputIdentity": _read_blob(observation["input_identity_bytes"]),
                "observation": _read_blob(observation["observation_bytes"]),
                "authorizationObservationHashes": _auth_hashes(auth)}


def list_review_cases(db: Session, *, actor: User, membership_id: str, limit: int = 25,
                      offset: int = 0, directive_id: str | None = None,
                      proposal_id: str | None = None) -> dict[str, Any]:
    auth = authorize_review_audit(db, actor, membership_id)
    if type(limit) is not int or not 1 <= limit <= 100 or type(offset) is not int or not 0 <= offset <= 10000:
        raise _error("review_page_invalid", "Review pagination is outside the supported bounds", 422)
    with db.no_autoflush:
        query = select(ADV4ReviewCase.id, ADV4ReviewCase.proposal_id)
        if directive_id is not None:
            query = query.where(ADV4ReviewCase.directive_id == directive_id)
        if proposal_id is not None:
            query = query.where(ADV4ReviewCase.proposal_id == proposal_id)
        total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
        cases = list(db.execute(query.order_by(ADV4ReviewCase.created_at.desc(), ADV4ReviewCase.id).limit(limit).offset(offset)))
        results = []
        document_cache: dict[tuple[str, str, int], bool] = {}
        source_cache: set[str] = set()
        proposal_observations: dict[str, dict[str, Any]] = {}
        proposal_ids = sorted({case.proposal_id for case in cases})
        work_metadata = {proposal_id: _evidence_work_metadata(db, proposal_id) for proposal_id in proposal_ids}
        projection_metadata = {
            proposal_id: {
                obligation: _prepare_projection_observation(db, proposal_id, obligation=obligation)
                for obligation in (False, True)
            }
            for proposal_id in proposal_ids
        }
        # Preflight the full page before its first external read. A queue-wide
        # budget failure must not turn a proposal's stable identity nonverified.
        within_budget = [work for work in work_metadata.values() if not work.over_budget]
        _check_source_work_budget((key for work in within_budget for key in work.document_keys),
            text_bytes=sum(work.text_bytes + work.lifecycle_reason_bytes for work in within_budget),
            binding_count=sum(work.binding_count for work in within_budget),
            lifecycle_count=sum(work.lifecycle_count for work in within_budget))
        if _projection_work_exceeded(
                prepared[1] for by_kind in projection_metadata.values()
                for prepared in by_kind.values()):
            raise _error("review_work_limit", "Projection histories exceed the review request work budget")
        prepared_evidence = {proposal_id: _prepare_evidence_observation(
            db, _proposal(db, proposal_id), work=work_metadata[proposal_id]) for proposal_id in proposal_ids}
        for case in cases:
            history = _verify_case_history(db, case.id, source_cache=source_cache)
            if case.proposal_id not in proposal_observations:
                proposal_observations[case.proposal_id] = observe_review_inputs(
                    db, case.proposal_id, _document_cache=document_cache,
                    _prepared_evidence=prepared_evidence[case.proposal_id],
                    _prepared_projections=projection_metadata[case.proposal_id])
            results.append(_serialize_case(history, auth=auth, summary_only=True,
                observation=proposal_observations[case.proposal_id]))
        return {"cases": results, "count": len(results), "total": total, "limit": limit, "offset": offset,
                "authorizationObservationHashes": _auth_hashes(auth)}

```
### `backend/tests/test_ad_v4_review_case_migration_postgres.py`

size=43781; sha256=3070e1862b9ea42fb0f82ddd2dea6995ed2f4a067532d63d8ce17753fe2ef7bd; truncated=false

```text
"""Independent SQL-boundary probes for the rejection-only review foundation."""
from __future__ import annotations

import hashlib
import json
import os
import uuid
import time
from concurrent.futures import ThreadPoolExecutor
from queue import Queue
from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine, inspect, select, text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session

from app.models.core import (
    ADV4CandidateProposal, ADV4CandidateAppProjection, ADV4CandidateAppProjectionEvent,
    ADV4CandidateSubmission, ADV4CandidateAppMaterializationRequest,
    ADV4CandidateObligationProjection, ADV4CandidateObligationProjectionEvent,
    ADV4ReviewCase, ADV4ReviewCaseEvent,
    ADV4ReviewDraftRevision, ADV4ReviewRequest, ADV4ReviewRejection,
    ADV4SignoffEvent, OrganizationMembership, User,
)
from app.services.ad_v4_candidates import VALIDATOR_VERSION_V2
from test_ad_v4_applicability_postgres import _enable, _store

URL = os.getenv("PAPRNAV_TEST_POSTGRES_URL")
pytestmark = pytest.mark.skipif(not URL, reason="PAPRNAV_TEST_POSTGRES_URL required")
VERSION = "paprnav-ad-v4-candidate-review-1"
MODELS = (ADV4ReviewCase, ADV4ReviewDraftRevision, ADV4ReviewRequest, ADV4ReviewRejection, ADV4SignoffEvent, ADV4ReviewCaseEvent)


def _bytes(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def _hash(domain, payload):
    return hashlib.sha256(domain.encode() + b"\0" + payload).hexdigest()


def _time(value):
    return value.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def _auth(db, user, member, action, now):
    a = db.get(User, user)
    m = db.get(OrganizationMembership, member)
    stable = dict(version="paprnav-ad-v4-review-authorization-1", policyName=VERSION,
        policyVersion="1", action=action, actorUserId=user, authorizingMembershipId=member,
        organizationId=m.organization_id, userStatus="active", membershipStatus="active",
        role="platform_admin", validityRule="status_only_v1", validFrom=None, validUntil=None,
        userUpdatedAt=_time(a.updated_at), membershipUpdatedAt=_time(m.updated_at), serverAuthorized=True)
    result = dict(stable, decisionTime=_time(now),
        authorizationObservationHash=_hash("paprnav-ad-v4-review-auth-observation-1", _bytes(stable)),
        claimsHash=_hash("paprnav-ad-v4-review-claims-1", _bytes(stable)))
    return result


def _seal(model, values):
    row = {column.name: values.get(column.name) for column in model.__table__.c}
    scalar = {key: _time(value) if isinstance(value, datetime) else value
        for key, value in row.items() if not key.endswith("_bytes")
        and key not in {"row_hash", "event_hash", "signature_hash"}}
    row["canonical_bytes"] = _bytes(dict(version=VERSION, table=model.__tablename__, record=scalar))
    row["event_hash" if model is ADV4ReviewCaseEvent else "row_hash"] = _hash("paprnav-ad-v4-review-row-1", row["canonical_bytes"])
    if model is ADV4SignoffEvent:
        row["signature_hash"] = _hash("paprnav-ad-v4-review-signature-1", row["canonical_bytes"])
    return row


def _scope(common):
    return {key: common[key] for key in ("auth_policy_version", "endpoint_action", "idempotency_key", "request_canonical_bytes", "request_hash")}


def _assert_authoritative_byte_total(db, case_id):
    # Independent metadata-driven accounting detects an omitted byte column
    # in the migration's deliberately explicit, non-JSON SQL helper.
    total = 0
    for model in MODELS:
        columns = [column for column in model.__table__.c if column.name.endswith("_bytes")]
        owner = model.id if model is ADV4ReviewCase else model.case_id
        for row in db.execute(select(*columns).where(owner == case_id)):
            total += sum(len(value) if value is not None else 0 for value in row)
    assert db.scalar(text("SELECT paprnav_v4_review_case_authoritative_bytes(:c)"), dict(c=case_id)) == total
    return total


class Records:
    def __init__(self, db, *, validator_version=VALIDATOR_VERSION_V2):
        self.db = db
        _enable(db)
        for gate in ("reviewer4_draft_enabled", "reviewer4_decision_enabled"):
            db.execute(text("SELECT paprnav_set_v4_feature_gate(:g,true,'review-test')"), dict(g=gate))
        db.commit()
        self.user, self.member, self.directive, self.proposal = _store(db,
            validator_version=validator_version, suffix=uuid.uuid4().hex)
        self.case = "arc_" + uuid.uuid4().hex
        self.head = None
        self.sequence = 0

    def common(self, action, now):
        auth = _auth(self.db, self.user, self.member, action, now)
        auth_bytes = _bytes(auth)
        return dict(id="arr_" + uuid.uuid4().hex, proposal_id=self.proposal,
            directive_id=self.directive, actor_user_id=self.user,
            authorizing_membership_id=self.member, organization_id=auth["organizationId"],
            auth_snapshot_bytes=auth_bytes, auth_snapshot_hash=_hash("paprnav-ad-v4-review-authorization-1", auth_bytes),
            contract_version=VERSION, auth_policy_version="1", endpoint_action=action, idempotency_key=uuid.uuid4().hex)

    def observation(self, now):
        p = self.db.get(ADV4CandidateProposal, self.proposal)
        heads = self.db.scalar(text("SELECT paprnav_v4_review_cutoff(:p)->'fragmentHeads'"), dict(p=self.proposal))
        identity = dict(version="paprnav-ad-v4-review-input-identity-1", directiveId=self.directive,
            proposal=dict(state="verified", id=self.proposal, storedCanonicalHash=p.canonical_hash, verifiedCanonicalHash=p.canonical_hash),
            evidence=dict(state="verified", storedBindingHash=p.evidence_binding_hash, verifiedBindingHash=p.evidence_binding_hash, headSetHash=_hash("paprnav-ad-v4-review-evidence-heads-1", _bytes(heads))),
            applicabilityProjection=dict(state="missing", errorCode="projection_missing"),
            obligationProjection=dict(state="missing", errorCode="projection_missing"))
        if getattr(self, "mutate_identity", None):
            self.mutate_identity(identity)
        identity_bytes = _bytes(identity)
        identity_hash = _hash("paprnav-ad-v4-review-input-identity-1", identity_bytes)
        observation = _bytes(dict(version="paprnav-ad-v4-review-observation-1", inputIdentityHash=identity_hash, observedAt=_time(now)))
        return dict(input_identity_bytes=identity_bytes, input_identity_hash=identity_hash,
            observation_bytes=observation, observation_hash=_hash("paprnav-ad-v4-review-observation-1", observation), observed_at=now)

    def event(self, common, kind, state, now, **objects):
        body = {} if kind == "case_created" else dict(expectedPredecessorEventHash=self.head)
        body.update(expectedAuthorizationObservationHash=json.loads(common["auth_snapshot_bytes"])["authorizationObservationHash"], expectedInputIdentityHash=self.observation(now)["input_identity_hash"])
        if kind == "review_requested":
            body["draftRevisionId"] = None
        if kind == "review_rejected":
            body["expectedRequestId"] = objects["review_request_id"]
            body["reasonCodes"] = ["projection_integrity"]
            body["explanation"] = "Both projections are missing."
        payload = _bytes(dict(version=VERSION, action=json.loads(common["auth_snapshot_bytes"])["action"], directiveId=self.directive, proposalId=self.proposal, caseId=None if kind == "case_created" else self.case, body=body))
        common.update(request_canonical_bytes=payload, request_hash=_hash("paprnav-ad-v4-review-request-1", payload))
        result = _seal(ADV4ReviewCaseEvent, dict(common, id="are_" + uuid.uuid4().hex,
            case_id=self.case, sequence_number=self.sequence, predecessor_event_hash=self.head,
            event_type=kind, resulting_state=state, auth_policy_version="1",
            endpoint_action=json.loads(common["auth_snapshot_bytes"])["action"], idempotency_key=common["idempotency_key"],
            request_canonical_bytes=payload, request_hash=_hash("paprnav-ad-v4-review-request-1", payload), occurred_at=now, **objects))
        self.head = result["event_hash"]
        self.sequence += 1
        return result

    def create(self, mutate_body=None):
        now = datetime.now(timezone.utc)
        common = self.common("create_ad_v4_review_case", now)
        event = self.event(common, "case_created", "draft", now)
        if mutate_body:
            request = json.loads(event["request_canonical_bytes"])
            mutate_body(request["body"])
            event["request_canonical_bytes"] = _bytes(request)
            event["request_hash"] = _hash("paprnav-ad-v4-review-request-1", event["request_canonical_bytes"])
            event = _seal(ADV4ReviewCaseEvent, event)
            common.update(_scope(event))
        case = _seal(ADV4ReviewCase, dict(common, **self.observation(now), id=self.case,
            proposal_canonical_hash=self.db.get(ADV4CandidateProposal, self.proposal).canonical_hash,
            case_sequence=0, predecessor_case_id=None, created_at=now))
        self.db.execute(ADV4ReviewCase.__table__.insert(), case)
        self.db.execute(ADV4ReviewCaseEvent.__table__.insert(), event)
        self.db.commit()
        return case


def test_review_migration_metadata_matches_six_table_contract():
    engine = create_engine(URL)
    with engine.connect() as connection:
        catalog = inspect(connection)
        for model in MODELS:
            actual = {column["name"] for column in catalog.get_columns(model.__tablename__)}
            assert actual == set(model.__table__.c.keys())
            assert len(catalog.get_check_constraints(model.__tablename__)) == len([c for c in model.__table__.constraints if c.__class__.__name__ == "CheckConstraint"])
        assert connection.scalar(text("SELECT count(*) FROM pg_trigger WHERE tgname LIKE 'trg_ar4_%' AND NOT tgisinternal")) == 18
        for function, mode in (("paprnav_v4_validate_submission", "UPDATE"), ("paprnav_v4_validate_app_request", "SHARE")):
            definition = connection.scalar(text(f"SELECT pg_get_functiondef('{function}()'::regprocedure)"))
            user_lock = f"SELECT * INTO u FROM users WHERE id=NEW.actor_user_id FOR {mode};"
            member_lock = f"SELECT * INTO m FROM organization_memberships WHERE id=NEW.authorizing_membership_id FOR {mode};"
            assert definition.index(user_lock) < definition.index(member_lock)
    engine.dispose()


def test_direct_review_creation_and_graph_free_rejection_commit():
    engine = create_engine(URL)
    with Session(engine) as db:
        records = Records(db)
        case = records.create()
        now = datetime.now(timezone.utc)
        common = records.common("request_ad_v4_review", now)
        cutoff = db.scalar(text("SELECT paprnav_v4_review_cutoff(:p)"), dict(p=records.proposal))
        authors = db.scalar(text("SELECT paprnav_v4_review_authors(:p)"), dict(p=records.proposal))
        request = _seal(ADV4ReviewRequest, dict(common, **records.observation(now), case_id=records.case,
            draft_revision_id=None, expected_predecessor_event_hash=records.head,
            cutoff_bytes=_bytes(cutoff), cutoff_hash=_hash("paprnav-ad-v4-review-cutoff-1", _bytes(cutoff)),
            authorship_set_bytes=_bytes(authors), authorship_set_hash=_hash("paprnav-ad-v4-review-authorship-1", _bytes(authors)),
            authorship_source_count=len(authors["bindings"]), requested_at=now))
        event = records.event(common, "review_requested", "pending_review", now, review_request_id=request["id"])
        request = _seal(ADV4ReviewRequest, dict(request, **_scope(common)))
        db.execute(ADV4ReviewRequest.__table__.insert(), request)
        db.execute(ADV4ReviewCaseEvent.__table__.insert(), event)
        db.commit()
        now = datetime.now(timezone.utc)
        common = records.common("reject_ad_v4_review", now)
        observation = records.observation(now)
        reason_bytes = _bytes(dict(version="paprnav-ad-v4-review-reasons-1", codes=["projection_integrity"], explanation="Both projections are missing."))
        rejection = _seal(ADV4ReviewRejection, dict(common, case_id=records.case, request_id=request["id"],
            proposal_canonical_hash=case["proposal_canonical_hash"], requested_input_identity_hash=request["input_identity_hash"],
            requested_observation_hash=request["observation_hash"], **{"decision_"+key:value for key,value in observation.items()},
            reasons_bytes=reason_bytes, reasons_hash=_hash("paprnav-ad-v4-review-reasons-1", reason_bytes), expected_predecessor_event_hash=records.head, rejected_at=now))
        signoff = _seal(ADV4SignoffEvent, dict(common, id="ars_"+uuid.uuid4().hex, case_id=records.case,
            request_id=request["id"], rejection_id=rejection["id"], action="reject", rejection_hash=rejection["row_hash"],
            requested_input_identity_hash=request["input_identity_hash"], requested_observation_hash=request["observation_hash"],
            decision_input_identity_hash=observation["input_identity_hash"], decision_observation_hash=observation["observation_hash"],
            authorization_observation_hash=json.loads(common["auth_snapshot_bytes"])["authorizationObservationHash"], signed_at=now))
        event = records.event(common, "review_rejected", "rejected", now, review_request_id=request["id"], rejection_id=rejection["id"], signoff_id=signoff["id"])
        rejection = _seal(ADV4ReviewRejection, dict(rejection, **_scope(common)))
        signoff = _seal(ADV4SignoffEvent, dict(signoff, **_scope(common), rejection_hash=rejection["row_hash"]))
        db.execute(ADV4ReviewRejection.__table__.insert(), rejection)
        db.execute(ADV4SignoffEvent.__table__.insert(), signoff)
        db.execute(ADV4ReviewCaseEvent.__table__.insert(), event)
        db.commit()
        assert db.scalar(select(ADV4ReviewCaseEvent.resulting_state).where(ADV4ReviewCaseEvent.id==event["id"])) == "rejected"
        assert 0 < _assert_authoritative_byte_total(db, records.case) < 16 * 1024 * 1024
        db.execute(text("UPDATE users SET status='inactive' WHERE id=:u"), dict(u=records.user))
        db.commit()
        db.execute(text("SELECT paprnav_v4_review_require_complete(:c)"), dict(c=records.case))
        db.rollback()
    engine.dispose()


def test_orphan_case_and_immutable_update_fail_closed():
    engine = create_engine(URL)
    with Session(engine) as db:
        records = Records(db)
        case = records.create()
        with pytest.raises(DBAPIError):
            db.execute(text("UPDATE ad_v4_review_cases SET case_sequence=1 WHERE id=:c"), dict(c=records.case))
        db.rollback()
        duplicate = dict(case, id="arc_"+uuid.uuid4().hex, case_sequence=1, predecessor_case_id=case["id"])
        duplicate = _seal(ADV4ReviewCase, duplicate)
        with pytest.raises(DBAPIError):
            db.execute(ADV4ReviewCase.__table__.insert(), duplicate)
            db.commit()
        db.rollback()
    engine.dispose()


@pytest.mark.parametrize("attack,expected", [
    ("auth_claim", "authorization snapshot differs"),
    ("false_proposal_hash", "observed proposal differs"),
    ("observation_time", "observation identity differs"),
    ("missing_projection_with_id", "required or forbidden keys differ"),
    ("writer_disabled", "feature gate disabled"),
])
def test_direct_sql_cannot_forge_review_observation_or_authorization(attack, expected):
    engine = create_engine(URL)
    with Session(engine) as db:
        records = Records(db)
        case = records.create()
        forged = dict(case, id="arc_"+uuid.uuid4().hex, case_sequence=1, predecessor_case_id=case["id"])
        if attack == "auth_claim":
            value = json.loads(forged["auth_snapshot_bytes"])
            value["validityRule"] = "invented_expiry_rule"
            forged["auth_snapshot_bytes"] = _bytes(value)
            forged["auth_snapshot_hash"] = _hash("paprnav-ad-v4-review-authorization-1", forged["auth_snapshot_bytes"])
        elif attack == "observation_time":
            value = json.loads(forged["observation_bytes"])
            value["observedAt"] = "2000-01-01T00:00:00.000000Z"
            forged["observation_bytes"] = _bytes(value)
            forged["observation_hash"] = _hash("paprnav-ad-v4-review-observation-1", forged["observation_bytes"])
        elif attack == "writer_disabled":
            db.execute(text("SELECT paprnav_set_v4_feature_gate('reviewer4_draft_enabled',false,'review-test')"))
            db.commit()
        else:
            value = json.loads(forged["input_identity_bytes"])
            if attack == "false_proposal_hash":
                value["proposal"]["storedCanonicalHash"] = "a"*64
            else:
                value["applicabilityProjection"]["id"] = "avp_forged"
            forged["input_identity_bytes"] = _bytes(value)
            forged["input_identity_hash"] = _hash("paprnav-ad-v4-review-input-identity-1", forged["input_identity_bytes"])
            observation = json.loads(forged["observation_bytes"])
            observation["inputIdentityHash"] = forged["input_identity_hash"]
            forged["observation_bytes"] = _bytes(observation)
            forged["observation_hash"] = _hash("paprnav-ad-v4-review-observation-1", forged["observation_bytes"])
        forged = _seal(ADV4ReviewCase, forged)
        with pytest.raises(DBAPIError, match=expected):
            db.execute(ADV4ReviewCase.__table__.insert(), forged)
            db.commit()
        db.rollback()
    engine.dispose()


@pytest.mark.parametrize("attack,expected", [
    ("missing_field", "request body shape differs"),
    ("extra_field", "request body shape differs"),
    ("input_cas", "request compare-and-swap differs"),
    ("auth_cas", "request compare-and-swap differs"),
])
def test_self_consistently_restamped_request_must_bind_exact_case(attack, expected):
    engine = create_engine(URL)
    with Session(engine) as db:
        records = Records(db)
        def mutate(body):
            if attack == "missing_field":
                body.pop("expectedInputIdentityHash")
            elif attack == "extra_field":
                body["publish"] = True
            elif attack == "input_cas":
                body["expectedInputIdentityHash"] = "a"*64
            else:
                body["expectedAuthorizationObservationHash"] = "b"*64
        with pytest.raises(DBAPIError, match=expected):
            records.create(mutate_body=mutate)
        db.rollback()
        assert db.get(ADV4ReviewCase, records.case) is None
    engine.dispose()


@pytest.mark.parametrize("family,state,changes,removed,expected", [
    ("evidence", "missing", {"headSetHash": "not-a-hash"}, ["verifiedBindingHash"], "nested identity encoding"),
    ("evidence", "integrity_error", {"headSetHash": "not-a-hash"}, ["verifiedBindingHash"], "nested identity encoding"),
    ("evidence", "integrity_error", {"headSetHash": "a"*64}, ["verifiedBindingHash"], "evidence head set differs"),
    ("evidence", "missing", {}, ["verifiedBindingHash", "headSetHash"], "falsely missing evidence"),
    ("evidence", "stale", {}, ["verifiedBindingHash", "headSetHash"], "required or forbidden keys"),
    ("evidence", "integrity_error", {"headSetHash": None}, ["verifiedBindingHash"], "observation branch differs"),
    ("proposal", "integrity_error", {}, [], "required or forbidden keys"),
    ("proposal", "stale", {"storedCanonicalHash": "bad"}, ["verifiedCanonicalHash"], "nested identity encoding"),
    ("proposal", "missing", {}, ["verifiedCanonicalHash"], "observed proposal differs"),
    ("applicabilityProjection", "integrity_error", {}, [], "required or forbidden keys"),
    ("applicabilityProjection", "integrity_error", {"id": "avp_absent", "storedHash": "a"*64}, [], "projection binding differs"),
    ("obligationProjection", "missing", {"eventHeadHash": "not-a-hash"}, [], "nested identity encoding"),
    ("obligationProjection", "unsupported_version", {"id": 12, "storedHash": "a"*64}, [], "observation branch differs"),
])
def test_fully_resealed_observation_union_negatives(family, state, changes, removed, expected):
    engine = create_engine(URL)
    with Session(engine) as db:
        records = Records(db)
        def mutate(identity):
            component = identity[family]
            component["state"] = state
            component["errorCode"] = "missing_evidence" if state == "missing" and family == "evidence" else "projection_integrity" if "Projection" in family else "candidate_integrity"
            component.update(changes)
            for key in removed:
                component.pop(key, None)
        records.mutate_identity = mutate
        with pytest.raises(DBAPIError, match=expected):
            records.create()
        db.rollback()
        assert db.get(ADV4ReviewCase, records.case) is None
    engine.dispose()


def _materialize_review_fixture(records):
    from app.core.config import get_settings
    from app.services.ad_v4_applicability import materialize_applicability
    from app.services.ad_v4_obligation_persistence import materialize_obligations
    os.environ["PAPRNAV_AD_V4_SLICE3B_ROUTES_ENABLED"] = "true"
    get_settings.cache_clear()
    db = records.db
    db.execute(text("SELECT paprnav_set_v4_feature_gate('materializer3b_enabled',true,'review-test')"))
    app = materialize_applicability(db, directive_id=records.directive, proposal_id=records.proposal,
        actor=db.get(User, records.user), membership_id=records.member, idempotency_key=uuid.uuid4().hex)
    db.commit()
    obligation = materialize_obligations(db, directive_id=records.directive, proposal_id=records.proposal,
        app_projection_id=app.projection.id, actor=db.get(User, records.user), membership_id=records.member,
        idempotency_key=uuid.uuid4().hex)
    db.commit()
    result = {}
    for name, projection, event_model in (
        ("applicabilityProjection", app.projection, ADV4CandidateAppProjectionEvent),
        ("obligationProjection", obligation.projection, ADV4CandidateObligationProjectionEvent),
    ):
        event = db.scalar(select(event_model).where(event_model.projection_id==projection.id).order_by(event_model.sequence_number.desc()))
        result[name] = dict(state="verified", id=projection.id, storedHash=projection.projection_hash, eventHeadHash=event.event_hash)
    return result


@pytest.mark.parametrize("family,state,with_head", [
    ("proposal", "verified", False), ("proposal", "integrity_error", False),
    ("proposal", "stale", False), ("proposal", "unsupported_version", False),
    ("evidence", "verified", True), ("evidence", "missing", False),
    ("evidence", "stale", True), ("evidence", "integrity_error", False),
    ("evidence", "integrity_error", True), ("evidence", "unsupported_version", False),
    ("evidence", "unsupported_version", True),
    ("applicabilityProjection", "verified", True), ("applicabilityProjection", "missing", False),
    ("applicabilityProjection", "stale", True), ("applicabilityProjection", "integrity_error", True),
    ("applicabilityProjection", "unsupported_version", True), ("applicabilityProjection", "integrity_error", False),
    ("applicabilityProjection", "unsupported_version", False),
    ("obligationProjection", "verified", True), ("obligationProjection", "missing", False),
    ("obligationProjection", "stale", True), ("obligationProjection", "integrity_error", True),
    ("obligationProjection", "unsupported_version", True), ("obligationProjection", "integrity_error", False),
    ("obligationProjection", "unsupported_version", False),
])
def test_observation_branch_shapes_commit_and_match_python(family, state, with_head):
    from app.services.ad_v4_reviews import _verify_observation, _verify_observation_sources
    engine = create_engine(URL)
    with Session(engine) as db:
        records = Records(db)
        projections = _materialize_review_fixture(records) if "Projection" in family and state != "missing" else None
        if projections and not with_head:
            event_table = "ad_v4_candidate_app_projection_events" if family == "applicabilityProjection" else "ad_v4_candidate_obligation_projection_events"
            db.execute(text(f"ALTER TABLE {event_table} DISABLE TRIGGER USER"))
            db.execute(text(f"DELETE FROM {event_table} WHERE projection_id=:p"), dict(p=projections[family]["id"]))
            db.execute(text(f"ALTER TABLE {event_table} ENABLE TRIGGER USER"))
            projections[family].pop("eventHeadHash")
            if family == "applicabilityProjection":
                projections["obligationProjection"].update(state="integrity_error", errorCode="projection_integrity")
        if family == "evidence" and state == "missing":
            # Model pre-existing source corruption. Restore guards before any
            # review insertion; the review must accurately retain absence.
            db.execute(text("ALTER TABLE ad_v4_candidate_evidence_bindings DISABLE TRIGGER USER"))
            db.execute(text("DELETE FROM ad_v4_candidate_evidence_bindings WHERE proposal_id=:p"), dict(p=records.proposal))
            db.execute(text("ALTER TABLE ad_v4_candidate_evidence_bindings ENABLE TRIGGER USER"))
        def mutate(identity):
            if projections:
                identity.update({key:dict(value) for key,value in projections.items()})
            component = identity[family]
            component["state"] = state
            if state != "verified":
                component.pop("verifiedCanonicalHash", None)
                component.pop("verifiedBindingHash", None)
                component["errorCode"] = "missing_evidence" if family == "evidence" and state == "missing" else "unsupported_version" if state == "unsupported_version" else "candidate_integrity" if family == "proposal" else "evidence_not_current" if family == "evidence" and state == "stale" else "evidence_integrity" if family == "evidence" else "projection_missing" if state == "missing" else "projection_integrity"
            if family == "evidence" and not with_head:
                component.pop("headSetHash", None)
        records.mutate_identity = mutate
        records.create()
        row = db.get(ADV4ReviewCase, records.case)
        _verify_observation(row)
        _verify_observation_sources(db, row)
        db.rollback()
    engine.dispose()


@pytest.mark.parametrize("family", ["applicabilityProjection", "obligationProjection"])
@pytest.mark.parametrize("attack", ["false_missing", "wrong_head", "omitted_head", "wrong_stored_hash"])
def test_resealed_projection_observations_bind_actual_rows_and_heads(family, attack):
    engine = create_engine(URL)
    with Session(engine) as db:
        records = Records(db)
        projections = _materialize_review_fixture(records)
        def mutate(identity):
            identity.update({key:dict(value) for key,value in projections.items()})
            component = identity[family]
            component.update(state="integrity_error", errorCode="projection_integrity")
            if attack == "false_missing":
                identity[family] = dict(state="missing", errorCode="projection_missing")
            elif attack == "wrong_head":
                component["eventHeadHash"] = "a"*64
            elif attack == "omitted_head":
                component.pop("eventHeadHash")
            else:
                component["storedHash"] = "b"*64
        records.mutate_identity = mutate
        with pytest.raises(DBAPIError, match="projection binding differs"):
            records.create()
        db.rollback()
        assert db.get(ADV4ReviewCase, records.case) is None
    engine.dispose()


@pytest.mark.parametrize("family", ["applicabilityProjection", "obligationProjection"])
def test_resealed_nonverified_projection_rejects_cross_directive_source(family):
    engine = create_engine(URL)
    with Session(engine) as db:
        records = Records(db)
        other = Records(db)
        projections = _materialize_review_fixture(records)
        table = "ad_v4_candidate_app_projections" if family == "applicabilityProjection" else "ad_v4_candidate_obligation_projections"
        db.execute(text(f"ALTER TABLE {table} DISABLE TRIGGER USER"))
        db.execute(text(f"UPDATE {table} SET directive_id=:d WHERE id=:p"), dict(d=other.directive, p=projections[family]["id"]))
        db.execute(text(f"ALTER TABLE {table} ENABLE TRIGGER USER"))
        def mutate(identity):
            identity.update({key:dict(value, state="integrity_error", errorCode="projection_integrity") for key,value in projections.items()})
        records.mutate_identity = mutate
        with pytest.raises(DBAPIError, match="projection binding differs"):
            records.create()
        db.rollback()
        assert db.get(ADV4ReviewCase, records.case) is None
    engine.dispose()


def _capacity_record(records, model, ordinal, case):
    if model is ADV4ReviewCase:
        return _seal(model, dict(case, id="arc_"+uuid.uuid4().hex,
            case_sequence=ordinal, predecessor_case_id=case["id"]))
    now = datetime.now(timezone.utc)
    action = "save_ad_v4_review_draft" if model is ADV4ReviewDraftRevision else "reject_ad_v4_review"
    common = records.common(action, now)
    observation = records.observation(now)
    body = dict(expectedAuthorizationObservationHash=json.loads(common["auth_snapshot_bytes"])["authorizationObservationHash"],
        expectedInputIdentityHash=observation["input_identity_hash"], expectedPredecessorEventHash=records.head)
    if model is ADV4ReviewDraftRevision:
        body.update(annotations=[], intendedAction="undecided")
    else:
        body.update(expectedRequestId="arq_"+"1"*32, reasonCodes=["projection_integrity"], explanation="Missing projections.")
    payload = _bytes(dict(version=VERSION, action=action, directiveId=records.directive, proposalId=records.proposal, caseId=records.case, body=body))
    common.update(request_canonical_bytes=payload, request_hash=_hash("paprnav-ad-v4-review-request-1", payload))
    if model is ADV4ReviewDraftRevision:
        annotations = _bytes(dict(version="paprnav-ad-v4-review-annotation-1", annotations=[]))
        return _seal(model, dict(common, **observation, case_id=records.case, revision_number=ordinal,
            predecessor_draft_id="ard_"+"1"*32 if ordinal else None, expected_predecessor_event_hash=records.head,
            annotation_bytes=annotations, annotation_hash=_hash("paprnav-ad-v4-review-annotation-1", annotations),
            intended_action="undecided", created_at=now))
    return _seal(model, dict(common, case_id=records.case, sequence_number=ordinal,
        predecessor_event_hash=records.head, event_type="review_rejected", resulting_state="rejected",
        draft_revision_id=None, review_request_id="arq_"+"1"*32, rejection_id="arr_"+"1"*32,
        signoff_id="ars_"+"1"*32, occurred_at=now))


@pytest.mark.parametrize("model,maximum,check", [
    (ADV4ReviewCase, 99, "ck_ar4_case_capacity"),
    (ADV4ReviewDraftRevision, 999, "ck_ar4_draft_capacity"),
    (ADV4ReviewCaseEvent, 1002, "ck_ar4_event_capacity"),
])
def test_direct_sql_capacity_ordinals_accept_boundary_reject_overflow(model, maximum, check):
    # Test the immediate ordinal boundary separately from the deferred full
    # history requirement. These deliberately incomplete probes never commit.
    engine = create_engine(URL)
    with Session(engine) as db:
        records = Records(db)
        case = records.create()
        probe = _capacity_record(records, model, maximum, case)
        nested = db.begin_nested()
        db.execute(model.__table__.insert(), probe)
        nested.rollback()
        db.rollback()
        probe = _capacity_record(records, model, maximum+1, case)
        with pytest.raises(DBAPIError, match=check):
            db.execute(model.__table__.insert(), probe)
        db.rollback()
    engine.dispose()


@pytest.mark.parametrize("model,check,extra", [
    (ADV4ReviewCase, "ck_ar4_case_capacity", 100),
    (ADV4ReviewDraftRevision, "ck_ar4_draft_capacity", 1001),
    (ADV4ReviewCaseEvent, "ck_ar4_event_capacity", 1003),
])
def test_commit_validator_bounds_corrupted_overcapacity_history(model, check, extra):
    engine = create_engine(URL)
    with Session(engine) as db:
        records = Records(db)
        case = records.create()
        probe = _capacity_record(records, model, 1 if model is ADV4ReviewCaseEvent else 0, case)
        table = model.__tablename__
        # Corruption fixture: bypass immediate defenses transactionally so the
        # independent bounded recount is exercised before any history walk.
        db.execute(text(f"ALTER TABLE {table} DISABLE TRIGGER USER"))
        db.execute(text(f"ALTER TABLE {table} DROP CONSTRAINT {check}"))
        template = {key: "\\x"+value.hex() if isinstance(value, bytes) else _time(value) if isinstance(value, datetime) else value for key,value in probe.items()}
        if model is ADV4ReviewCase:
            overrides = "jsonb_build_object('id','cap_'||lpad(g::text,32,'0'),'case_sequence',g,'predecessor_case_id',CASE WHEN g=1 THEN CAST(:case_id AS text) ELSE 'cap_'||lpad((g-1)::text,32,'0') END)"
        elif model is ADV4ReviewDraftRevision:
            overrides = "jsonb_build_object('id','cap_'||lpad(g::text,32,'0'),'revision_number',g-1,'predecessor_draft_id',CASE WHEN g=1 THEN NULL ELSE 'cap_'||lpad((g-1)::text,32,'0') END)"
        else:
            overrides = "jsonb_build_object('id','cap_'||lpad(g::text,32,'0'),'sequence_number',g,'event_type','draft_saved','resulting_state','draft','draft_revision_id','cap_'||lpad(g::text,32,'0'),'review_request_id',NULL,'rejection_id',NULL,'signoff_id',NULL,'idempotency_key','capacity-'||g,'event_hash',md5('event'||g)||md5('event2'||g),'predecessor_event_hash',md5('prior'||g)||md5('prior2'||g))"
        db.execute(text(f"INSERT INTO {table} SELECT (jsonb_populate_record(NULL::{table},CAST(:template AS jsonb)||{overrides})).* FROM generate_series(1,:extra) g"), dict(template=json.dumps(template), extra=extra, case_id=case["id"]))
        with pytest.raises(DBAPIError, match="history capacity exceeded"):
            db.execute(text("SELECT paprnav_v4_review_require_complete(:case_id)"), dict(case_id=case["id"]))
        db.rollback()  # Restores every dropped check/disabled trigger and row.
    engine.dispose()


def _seed_cutoff_sources(records, family, first, last):
    """Synthetic retained-source cardinality only; all changes are rolled back.

    Old source guards are bypassed for fixture setup, never review guards.
    This tests bounded review work, not candidate-submission validation.
    """
    db = records.db
    submission = db.scalar(text("SELECT to_jsonb(s) FROM ad_v4_candidate_submissions s WHERE proposal_id=:p LIMIT 1"), dict(p=records.proposal))
    if family == "submissions":
        table = "ad_v4_candidate_submissions"
        template = submission
        overrides = "jsonb_build_object('id','cut_'||lpad(g::text,32,'0'),'idempotency_key','cutoff-'||g)"
    else:
        table = "ad_v4_candidate_submission_relationships"
        template = dict(id="", submission_id=submission["id"], relationship_key="",
            relation_type="corrects_candidate", predecessor_proposal_id=records.proposal,
            reason="Synthetic capacity fixture", evidence_keys=[], canonical_bytes="\\x7b7d",
            relationship_hash="", validator_version=submission["validator_version"],
            canonicalization_version=submission["canonicalization_version"], created_at=submission["created_at"])
        overrides = "jsonb_build_object('id','cur_'||lpad(g::text,32,'0'),'relationship_key','cutoff-'||g,'relationship_hash',md5('cutoff'||g)||md5('cutoff2'||g))"
    db.execute(text(f"ALTER TABLE {table} DISABLE TRIGGER USER"))
    db.execute(text(f"INSERT INTO {table} SELECT (jsonb_populate_record(NULL::{table},CAST(:template AS jsonb)||{overrides})).* FROM generate_series(CAST(:first AS integer),CAST(:last AS integer)) g"), dict(template=json.dumps(template), first=first, last=last))
    db.execute(text(f"ALTER TABLE {table} ENABLE TRIGGER USER"))


def _insert_cutoff_request(records, cutoff):
    db = records.db
    now = datetime.now(timezone.utc)
    common = records.common("request_ad_v4_review", now)
    authors = db.scalar(text("SELECT paprnav_v4_review_authors(:p)"), dict(p=records.proposal))
    request = dict(common, **records.observation(now), case_id=records.case,
        draft_revision_id=None, expected_predecessor_event_hash=records.head,
        cutoff_bytes=_bytes(cutoff), cutoff_hash=_hash("paprnav-ad-v4-review-cutoff-1", _bytes(cutoff)),
        authorship_set_bytes=_bytes(authors), authorship_set_hash=_hash("paprnav-ad-v4-review-authorship-1", _bytes(authors)),
        authorship_source_count=len(authors["bindings"]), requested_at=now)
    event = records.event(common, "review_requested", "pending_review", now, review_request_id=request["id"])
    request = _seal(ADV4ReviewRequest, dict(request, **_scope(common)))
    db.execute(ADV4ReviewRequest.__table__.insert(), request)
    db.execute(ADV4ReviewCaseEvent.__table__.insert(), event)


@pytest.mark.parametrize("family", ["submissions", "relationships"])
@pytest.mark.parametrize("overflow_source", ["live", "provided"])
def test_direct_sql_cutoff_2000_boundary_and_2001_overflow(family, overflow_source):
    engine = create_engine(URL)
    with Session(engine) as db:
        records = Records(db)
        records.create()
        original_head, original_sequence = records.head, records.sequence
        _seed_cutoff_sources(records, family, 2 if family == "submissions" else 1, 2000)
        cutoff = db.scalar(text("SELECT paprnav_v4_review_cutoff(:p)"), dict(p=records.proposal))
        assert len(cutoff[family]) == 2000
        boundary = db.begin_nested()
        _insert_cutoff_request(records, cutoff)
        db.execute(text("SET CONSTRAINTS ALL IMMEDIATE"))
        boundary.rollback()  # Keep synthetic source history isolated and recover draft state.
        records.head, records.sequence = original_head, original_sequence
        if overflow_source == "live":
            _seed_cutoff_sources(records, family, 2001, 2002)
            live = db.scalar(text("SELECT paprnav_v4_review_cutoff(:p)"), dict(p=records.proposal))
            assert len(live[family]) == 2001  # limit+1 sentinel even with 2002 rows
            # Still submit the previously valid 2000-item cutoff: the live
            # bound must fail before exact-cutoff comparison or authorship walk.
        else:
            cutoff[family].append(dict(cutoff[family][-1]))
            assert len(cutoff[family]) == 2001
        with pytest.raises(DBAPIError, match="cutoff capacity exceeded"):
            _insert_cutoff_request(records, cutoff)
        db.rollback()
    engine.dispose()


@pytest.mark.parametrize("excess,validation", [(0, "read"), (1, "read"), (1, "commit")])
def test_authoritative_byte_budget_exact_boundary_and_overflow(excess, validation):
    engine = create_engine(URL)
    with Session(engine) as db:
        records = Records(db)
        case = records.create()
        baseline = _assert_authoritative_byte_total(db, records.case)
        assert baseline > 0
        target = 16 * 1024 * 1024 + excess
        byte_columns = [c.name for c in ADV4ReviewDraftRevision.__table__.c if c.name.endswith("_bytes")]
        per_column, remainder = divmod(target - baseline, 3 * len(byte_columns))
        assert 2 <= per_column < 1024 * 1024
        # Corruption fixture bypasses only the insert guard. The normal
        # deferred commit trigger stays enabled, as do every CHECK and FK.
        # Invalid padded JSON ensures the budget precedes deep verification.
        db.execute(text("ALTER TABLE ad_v4_review_draft_revisions DISABLE TRIGGER trg_ar4_1_guard"))
        previous = None
        for ordinal in range(3):
            draft = _capacity_record(records, ADV4ReviewDraftRevision, ordinal, case)
            draft["predecessor_draft_id"] = previous
            previous = draft["id"]
            for column in byte_columns:
                draft[column] = b"x" * per_column
            if ordinal == 0:
                draft[byte_columns[0]] += b"x" * remainder
            db.execute(ADV4ReviewDraftRevision.__table__.insert(), draft)
        assert _assert_authoritative_byte_total(db, records.case) == target
        expected = "authoritative byte capacity exceeded" if excess else "object-event completeness differs"
        with pytest.raises(DBAPIError, match=expected):
            if validation == "commit":
                db.commit()
            else:
                db.execute(text("SELECT paprnav_v4_review_require_complete(:c)"), dict(c=records.case))
        db.rollback()  # Restores the insert guard and removes padded records.
    engine.dispose()


@pytest.mark.parametrize("source_model", [ADV4CandidateSubmission, ADV4CandidateAppMaterializationRequest])
def test_direct_sql_candidate_audit_and_review_share_actor_membership_order(source_model):
    """Hold U in review, force old writer to wait on U, then acquire M.

    The pre-0029 writer already owns M while waiting, so the actual review
    insertion closes U→M→U. The final writer waits on U without owning M.
    No audit trigger is bypassed and both real transactions must commit.
    """
    engine = create_engine(URL, connect_args={"options": "-c statement_timeout=10000 -c lock_timeout=8000"})
    try:
        with Session(engine) as db:
            records = Records(db)
            if source_model is ADV4CandidateAppMaterializationRequest:
                projections = _materialize_review_fixture(records)
                records.mutate_identity = lambda identity: identity.update({key:dict(value) for key,value in projections.items()})
            source = dict(db.execute(select(source_model.__table__).where(source_model.proposal_id == records.proposal).limit(1)).mappings().one())
            source.update(id="con_"+uuid.uuid4().hex, idempotency_key=uuid.uuid4().hex)
            db.commit()
            review_pid = db.scalar(text("SELECT pg_backend_pid()"))
            db.execute(text("SELECT id FROM users WHERE id=:u FOR UPDATE"), dict(u=records.user))
            candidate_pid = Queue()
            def insert_candidate_audit():
                with Session(engine) as writer:
                    candidate_pid.put(writer.scalar(text("SELECT pg_backend_pid()")))
                    writer.execute(source_model.__table__.insert(), source)
                    writer.commit()
                    return source["id"]
            with ThreadPoolExecutor(max_workers=1) as pool:
                pending = pool.submit(insert_candidate_audit)
                pid = candidate_pid.get(timeout=5)
                deadline = time.monotonic()+5
                with engine.connect() as observer:
                    while time.monotonic() < deadline:
                        blocked = observer.scalar(text("SELECT :review=ANY(pg_blocking_pids(:candidate))"), dict(review=review_pid, candidate=pid))
                        if blocked:
                            break
                        time.sleep(0.01)
                    assert blocked, "Candidate audit never blocked on the review actor lock"
                records.create()  # Must acquire M and commit, not deadlock.
                assert pending.result(timeout=10) == source["id"]
            assert db.scalar(select(source_model.id).where(source_model.id == source["id"])) == source["id"]
            db.execute(text("SELECT paprnav_v4_review_require_complete(:c)"), dict(c=records.case))
            db.rollback()
    finally:
        engine.dispose()

```
### `backend/tests/test_ad_v4_review_lock_order_postgres.py`

size=10128; sha256=cb4ffe0efbaf0c2510bbfe9018aa1f8f87698e1d1efb872a8c34cf10a3886da9; truncated=false

```text
from __future__ import annotations

import json
import os
import threading
import uuid
from concurrent.futures import ThreadPoolExecutor

import pytest
from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.core import (
    ADV4CandidateProposal,
    ADV4CandidateSubmission,
    OrganizationMembership,
    User,
)
from app.services import ad_v4_candidates as candidates
from app.services import ad_v4_reviews as reviews
from test_ad_v4_applicability_postgres import _enable, _store


URL = os.getenv("PAPRNAV_TEST_POSTGRES_URL")
pytestmark = pytest.mark.skipif(not URL, reason="PAPRNAV_TEST_POSTGRES_URL required")


@pytest.mark.parametrize("transition", ["case", "request", "rejection"])
@pytest.mark.parametrize("reuse_content", [False, True], ids=["new-content", "resubmission"])
def test_candidate_submission_and_review_share_relationship_before_fragment_lock_order(
    monkeypatch: pytest.MonkeyPatch, transition: str, reuse_content: bool,
) -> None:
    """Force the previous two-admin deadlock, including content deduplication.

    The review writer owns the relationship lock before the candidate writer
    requests it. Previously the candidate already owned the fragment then,
    so allowing review to continue closed a relationship/fragment lock cycle.
    Both real transactions must now commit, with no synthetic lock bypass.
    """
    for flag in ("READS", "DRAFTS", "DECISIONS"):
        monkeypatch.setenv(f"PAPRNAV_AD_V4_SLICE4_{flag}_ENABLED", "true")
    get_settings.cache_clear()
    engine = create_engine(URL, connect_args={
        "connect_timeout": 5,
        "options": "-c statement_timeout=12000 -c lock_timeout=10000",
    })
    token = uuid.uuid4().hex
    try:
        with Session(engine) as db:
            _enable(db)
            for gate in ("materializer3b_enabled", "reviewer4_draft_enabled", "reviewer4_decision_enabled"):
                db.execute(text("SELECT paprnav_set_v4_feature_gate(:gate,true,'lock-order-test')"), {"gate": gate})
            db.commit()
            author_id, author_membership_id, directive_id, proposal_id = _store(
                db, validator_version=candidates.VALIDATOR_VERSION_V2, suffix=f"lock-order-{token}",
            )
            author_membership = db.get(OrganizationMembership, author_membership_id)
            reviewer = User(email=f"review-lock-{token}@example.test", name="Second administrator",
                            password_hash="x", status="active")
            db.add(reviewer)
            db.flush()
            membership = OrganizationMembership(
                organization_id=author_membership.organization_id, user_id=reviewer.id,
                role="platform_admin", status="active",
            )
            db.add(membership)
            db.commit()
            reviewer_id, reviewer_membership_id = reviewer.id, membership.id
            proposal = db.get(ADV4CandidateProposal, proposal_id)
            payload = json.loads(proposal.canonical_bytes)
            if not reuse_content:
                payload["decisionKey"] = f"concurrent-{token}"
            parsed = candidates.parse_v4_request_bytes(json.dumps({
                "proposal": payload, "submissionContext": {"relationships": []},
            }).encode())
            observed = reviews.review_proposal_observation(
                db, directive_id=directive_id, proposal_id=proposal_id,
                actor=reviewer, membership_id=reviewer_membership_id,
            )
            state = observed
            if transition != "case":
                state = reviews.create_review_case(
                    db, directive_id=directive_id, proposal_id=proposal_id,
                    actor=reviewer, membership_id=reviewer_membership_id,
                    idempotency_key=f"case-{token}",
                    expected_authorization_observation_hash=state["authorizationObservationHashes"]["create_ad_v4_review_case"],
                    expected_input_identity_hash=state["inputIdentityHash"],
                )
                state = reviews.save_review_draft(
                    db, case_id=state["caseId"], actor=reviewer, membership_id=reviewer_membership_id,
                    idempotency_key=f"draft-{token}",
                    expected_authorization_observation_hash=state["authorizationObservationHashes"]["save_ad_v4_review_draft"],
                    expected_input_identity_hash=state["inputIdentityHash"],
                    expected_predecessor_event_hash=state["latestEventHash"],
                    annotations=[{"pointer": "/requirements", "text": "Remediation required"}],
                    intended_action="reject",
                )
            if transition == "rejection":
                state = reviews.request_review(
                    db, case_id=state["caseId"], actor=reviewer, membership_id=reviewer_membership_id,
                    idempotency_key=f"request-{token}",
                    expected_authorization_observation_hash=state["authorizationObservationHashes"]["request_ad_v4_review"],
                    expected_input_identity_hash=state["inputIdentityHash"],
                    expected_predecessor_event_hash=state["latestEventHash"],
                    draft_revision_id=state["draftRevisionId"],
                )
            db.commit()

        review_has_relationship = threading.Event()
        candidate_requests_relationship = threading.Event()
        original_lock = candidates._advisory_lock
        original_bindings = candidates._binding_snapshot
        candidate_order: list[str] = []

        def coordinated_lock(db: Session, value: str) -> None:
            role = db.info["lock_order_test_role"]
            relationship = value == f"candidate-relationship-graph:{directive_id}"
            if role == "candidate" and relationship:
                candidate_requests_relationship.set()
            original_lock(db, value)
            if role == "candidate":
                candidate_order.append("relationship" if relationship else value.split(":", 1)[0])
            elif relationship and not review_has_relationship.is_set():
                review_has_relationship.set()
                assert candidate_requests_relationship.wait(8), "Candidate never requested relationship lock"

        def traced_bindings(db: Session, *args, **kwargs):
            candidate_order.append("bindings")
            return original_bindings(db, *args, **kwargs)

        monkeypatch.setattr(candidates, "_advisory_lock", coordinated_lock)
        monkeypatch.setattr(reviews, "_advisory_lock", coordinated_lock)
        monkeypatch.setattr(candidates, "_binding_snapshot", traced_bindings)

        def mutate_review():
            with Session(engine) as db:
                db.info["lock_order_test_role"] = "review"
                reviewer = db.get(User, reviewer_id)
                common = dict(actor=reviewer, membership_id=reviewer_membership_id,
                              idempotency_key=f"concurrent-review-{token}",
                              expected_input_identity_hash=state["inputIdentityHash"])
                if transition == "case":
                    result = reviews.create_review_case(
                        db, **common, directive_id=directive_id, proposal_id=proposal_id,
                        expected_authorization_observation_hash=state["authorizationObservationHashes"]["create_ad_v4_review_case"],
                    )
                elif transition == "request":
                    result = reviews.request_review(
                        db, **common, case_id=state["caseId"], draft_revision_id=state["draftRevisionId"],
                        expected_predecessor_event_hash=state["latestEventHash"],
                        expected_authorization_observation_hash=state["authorizationObservationHashes"]["request_ad_v4_review"],
                    )
                else:
                    result = reviews.reject_review_case(
                        db, **common, case_id=state["caseId"], expected_request_id=state["reviewRequestId"],
                        expected_predecessor_event_hash=state["latestEventHash"],
                        expected_authorization_observation_hash=state["authorizationObservationHashes"]["reject_ad_v4_review"],
                        reason_codes=["remediation_requested"], explanation="Remediation required.",
                    )
                db.commit()
                return result

        def submit_candidate():
            assert review_has_relationship.wait(8), "Review never obtained relationship lock"
            with Session(engine) as db:
                db.info["lock_order_test_role"] = "candidate"
                result = candidates.store_v4_candidate(
                    db, directive_id=directive_id, parsed=parsed, actor=db.get(User, author_id),
                    membership_id=author_membership_id, idempotency_key=f"concurrent-candidate-{token}",
                    validator_version=candidates.VALIDATOR_VERSION_V2,
                )
                db.commit()
                return result.proposal.id, result.submission.id, result.content_reused

        with ThreadPoolExecutor(max_workers=2) as pool:
            review_future = pool.submit(mutate_review)
            candidate_future = pool.submit(submit_candidate)
            review_result = review_future.result(timeout=20)
            candidate_id, submission_id, reused = candidate_future.result(timeout=20)
        assert review_result["state"] == {"case": "draft", "request": "pending_review", "rejection": "rejected"}[transition]
        assert reused is reuse_content
        assert (candidate_id == proposal_id) is reuse_content
        assert candidate_order.index("content") < candidate_order.index("relationship") < candidate_order.index("bindings")
        with Session(engine) as db:
            assert db.scalar(select(ADV4CandidateSubmission.id).where(
                ADV4CandidateSubmission.id == submission_id,
            )) == submission_id
    finally:
        engine.dispose()

```
### `backend/tests/test_ad_v4_review_rollout_postgres.py`

size=5409; sha256=7545c7dfbdb8b3203538a85a0952d371484ea608243f7ad7966c5147b11ed1ba; truncated=false

```text
"""Migration rollback gates for the immutable Slice-4 review foundation.

Run this module against its own freshly migrated disposable database.  The
tests intentionally leave immutable review history behind in the final case.
"""
from __future__ import annotations

import os
import subprocess
import sys

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from test_ad_v4_review_case_migration_postgres import Records


URL = os.getenv("PAPRNAV_TEST_POSTGRES_URL")
pytestmark = pytest.mark.skipif(not URL, reason="PAPRNAV_TEST_POSTGRES_URL required")


def _alembic(*args: str) -> subprocess.CompletedProcess[str]:
    environment = os.environ.copy()
    environment["DATABASE_URL"] = URL or ""
    return subprocess.run(
        [sys.executable, "-m", "alembic", *args],
        cwd=os.path.dirname(os.path.dirname(__file__)),
        env=environment,
        text=True,
        capture_output=True,
        timeout=30,
        check=False,
    )


def _version(engine) -> str:
    with engine.connect() as connection:
        return connection.scalar(text("SELECT version_num FROM alembic_version"))


def test_00_empty_disabled_review_schema_downgrades_and_reupgrades() -> None:
    engine = create_engine(URL, pool_pre_ping=True)
    try:
        assert _version(engine) == "20260913_0029"
        down = _alembic("downgrade", "20260911_0028")
        assert down.returncode == 0, down.stdout + down.stderr
        assert _version(engine) == "20260911_0028"
        with engine.connect() as connection:
            frozen_0028 = {
                function: connection.scalar(text(
                    f"SELECT pg_get_functiondef('{function}()'::regprocedure)"
                ))
                for function in (
                    "paprnav_v4_validate_submission",
                    "paprnav_v4_validate_app_request",
                )
            }
            assert connection.scalar(text(
                "SELECT to_regprocedure('paprnav_v4_review_case_authoritative_bytes(text)')"
            )) is None
        up = _alembic("upgrade", "head")
        assert up.returncode == 0, up.stdout + up.stderr
        assert _version(engine) == "20260913_0029"
        with engine.connect() as connection:
            gates = dict(connection.execute(text(
                "SELECT gate_key,enabled FROM ad_v4_feature_gates "
                "WHERE gate_key IN ('reviewer4_draft_enabled','reviewer4_decision_enabled')"
            )).all())
        assert gates == {
            "reviewer4_draft_enabled": False,
            "reviewer4_decision_enabled": False,
        }
        second_down = _alembic("downgrade", "20260911_0028")
        assert second_down.returncode == 0, second_down.stdout + second_down.stderr
        assert _version(engine) == "20260911_0028"
        with engine.connect() as connection:
            assert {
                function: connection.scalar(text(
                    f"SELECT pg_get_functiondef('{function}()'::regprocedure)"
                ))
                for function in frozen_0028
            } == frozen_0028
            assert connection.scalar(text(
                "SELECT to_regprocedure('paprnav_v4_review_case_authoritative_bytes(text)')"
            )) is None
        second_up = _alembic("upgrade", "head")
        assert second_up.returncode == 0, second_up.stdout + second_up.stderr
        assert _version(engine) == "20260913_0029"
    finally:
        engine.dispose()


@pytest.mark.parametrize("gate", ["reviewer4_draft_enabled", "reviewer4_decision_enabled"])
def test_01_enabled_review_gate_refuses_downgrade_without_schema_loss(gate: str) -> None:
    engine = create_engine(URL, pool_pre_ping=True)
    try:
        with engine.begin() as connection:
            connection.execute(text(
                "SELECT paprnav_set_v4_feature_gate(:gate,true,'review-rollout-test')"
            ), {"gate": gate})
        down = _alembic("downgrade", "20260911_0028")
        assert down.returncode != 0
        assert "Revision 0029 reviewer gates are enabled" in down.stdout + down.stderr
        assert _version(engine) == "20260913_0029"
        with engine.begin() as connection:
            connection.execute(text(
                "SELECT paprnav_set_v4_feature_gate(:gate,false,'review-rollout-test')"
            ), {"gate": gate})
    finally:
        engine.dispose()


def test_99_immutable_review_history_refuses_downgrade_without_row_loss() -> None:
    engine = create_engine(URL, pool_pre_ping=True)
    try:
        with Session(engine) as db:
            records = Records(db)
            records.create()
            for gate in ("reviewer4_draft_enabled", "reviewer4_decision_enabled"):
                db.execute(text(
                    "SELECT paprnav_set_v4_feature_gate(:gate,false,'review-rollout-test')"
                ), {"gate": gate})
            db.commit()
            case_id = records.case
        down = _alembic("downgrade", "20260911_0028")
        assert down.returncode != 0
        assert "Revision 0029 contains immutable review history" in down.stdout + down.stderr
        assert _version(engine) == "20260913_0029"
        with engine.connect() as connection:
            assert connection.scalar(text(
                "SELECT count(*) FROM ad_v4_review_cases WHERE id=:case_id"
            ), {"case_id": case_id}) == 1
    finally:
        engine.dispose()

```
### `backend/tests/test_ad_v4_review_service_bounds.py`

size=48914; sha256=24abe2c6fdfa7770af063619b021a5bbd4295113a52aef05a3b7f57cb731072c; truncated=false

```text
"""Storage-failure remediation and bounded review-history service regressions."""
from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest
from botocore.exceptions import (
    ClientError, ConnectionClosedError, ConnectTimeoutError, CredentialRetrievalError,
    EndpointConnectionError, IncompleteReadError, NoCredentialsError,
    PartialCredentialsError, ReadTimeoutError, ResponseStreamingError, SSLError,
)
from sqlalchemy import LargeBinary, event, func, insert, select, update
from sqlalchemy.dialects import postgresql, sqlite
from sqlalchemy.exc import OperationalError

from app.core.config import get_settings
from app.models.core import (
    ADEvidenceFragment, ADEvidenceFragmentLifecycleEvent, ADPublication,
    ADSourceDocument, ADSourcePageTextVersion, ADV4CandidateEvidenceBinding,
    ADV4CandidateProposal, ADV4CandidateSubmission, ADV4CandidateSubmissionRelationship,
    ADV4ReviewCase, ADV4ReviewCaseEvent, ADV4ReviewDraftRevision,
    ADV4ReviewRejection, ADV4ReviewRequest, ADV4SignoffEvent,
)
from app.services import ad_v4_reviews as review, storage
from app.services.ad_evidence import _hash_parts
from app.services.ad_v4_candidates import DOMAINS_V2, canonical_bytes, CANONICALIZATION_VERSION_V2
from test_ad_v4_reviews import _enable_app, _seed_review_source


def _source(db, *, backend="s3", source=None):
    actor, member, directive, proposal = source if source is not None else _seed_review_source(db)
    identifier = f"review-storage-{proposal.id}"
    document = ADSourceDocument(source_system="test", source_type="ad_rule", source_identifier=identifier,
        storage_backend=backend, storage_key="unavailable-source.pdf", content_hash=hashlib.sha256(b"source").hexdigest(),
        storage_bytes=6, captured_at=datetime.now(timezone.utc))
    db.add(document)
    db.flush()
    db.add(ADPublication(directive_id=directive.id, source_document_id=document.id,
                        source_system="test", source_type="ad_rule", source_identifier=identifier))
    page = ADSourcePageTextVersion(rendition_id=f"rendition-{document.id}"[:36], source_document_id=document.id,
        source_content_hash=document.content_hash, page_number=1, extractor_name="test", extractor_version="1",
        extractor_configuration_hash="a" * 64, page_text="source", text_hash=hashlib.sha256(b"source").hexdigest())
    db.add(page)
    db.flush()
    fragment = ADEvidenceFragment(directive_id=directive.id, source_document_id=document.id,
        source_content_hash=document.content_hash, rendition_id=page.rendition_id, page_text_version_id=page.id,
        page_start=1, page_end=1, character_start=0, character_end=6, exact_text="source",
        parser_name="test", parser_version="1", created_by_user_id=actor.id,
        fragment_hash=_hash_parts(directive.id, document.id, document.content_hash, page.rendition_id,
                                 page.id, 1, 1, 0, 6, None, None, None, None, None, "source", "test", "1"))
    db.add(fragment)
    db.flush()
    admitted = ADEvidenceFragmentLifecycleEvent(fragment_id=fragment.id, event_type="admitted",
        actor_user_id=actor.id, reason="test admission", sequence_number=0,
        event_hash=_hash_parts(fragment.id, fragment.fragment_hash, "admitted", actor.id, "test admission", 0, None))
    db.add(admitted)
    db.flush()
    binding = ADV4CandidateEvidenceBinding(proposal_id=proposal.id, directive_id=directive.id,
        evidence_key="ev-source", fragment_id=fragment.id, fragment_hash=fragment.fragment_hash,
        admitted_event_id=admitted.id, admitted_event_hash=admitted.event_hash,
        validator_version=proposal.validator_version, canonicalization_version=proposal.canonicalization_version)
    db.add(binding)
    proposal.parsed_json = {"evidenceBindings": {"ev-source": {"fragmentId": fragment.id, "fragmentHash": fragment.fragment_hash}}}
    envelope = {"version": "ad-v4-evidence-bindings-v2", "validatorVersion": proposal.validator_version,
        "canonicalizationVersion": proposal.canonicalization_version, "bindings": [{"evidenceKey": "ev-source",
        "fragmentId": fragment.id, "fragmentHash": fragment.fragment_hash, "admittedEventId": admitted.id,
        "admittedEventHash": admitted.event_hash}]}
    proposal.evidence_binding_bytes = canonical_bytes(envelope, CANONICALIZATION_VERSION_V2)
    proposal.evidence_binding_hash = hashlib.sha256(DOMAINS_V2["bindings"] + proposal.evidence_binding_bytes).hexdigest()
    proposal.binding_count = 1
    db.commit()
    return actor, member, directive, proposal


def _workflow(db, actor, member, directive, proposal, *, idempotency_key="create"):
    authority = dict(actor=actor, membership_id=member.id)
    observation = review.review_proposal_observation(db, directive_id=directive.id, proposal_id=proposal.id, **authority)
    case = review.create_review_case(db, directive_id=directive.id, proposal_id=proposal.id,
        idempotency_key=idempotency_key, expected_input_identity_hash=observation["inputIdentityHash"],
        expected_authorization_observation_hash=observation["authorizationObservationHashes"][review.ACTIONS["case_created"]],
        **authority)
    db.commit()
    return authority, case


def _args(db, authority, case, action):
    current = review.verified_review_case(db, case_id=case["caseId"], **authority)
    return dict(case_id=case["caseId"], expected_predecessor_event_hash=current["latestEventHash"],
        expected_input_identity_hash=current["inputIdentityHash"],
        expected_authorization_observation_hash=current["authorizationObservationHashes"][review.ACTIONS[action]], **authority)


@pytest.mark.parametrize("failure", ["NoSuchKey", "AccessDenied", "transport", "local_missing"])
def test_expected_storage_failure_keeps_observation_and_rejection_available(db_session, monkeypatch, tmp_path, failure):
    _enable_app(monkeypatch)
    monkeypatch.setenv("PAPRNAV_S3_UPLOAD_BUCKET", "review-test")
    monkeypatch.setenv("PAPRNAV_LOCAL_STORAGE_PATH", str(tmp_path))
    get_settings.cache_clear()
    actor, member, directive, proposal = _source(db_session, backend="local" if failure == "local_missing" else "s3")
    calls = []
    if failure != "local_missing":
        def fail(**kwargs):
            calls.append(kwargs)
            if failure == "transport":
                raise EndpointConnectionError(endpoint_url="https://storage.test")
            raise ClientError({"Error": {"Code": failure}, "ResponseMetadata": {"HTTPStatusCode": 404 if failure == "NoSuchKey" else 403}}, "GetObject")
        monkeypatch.setattr(storage, "get_s3_client", lambda region: SimpleNamespace(get_object=fail))
    observation = review.observe_review_inputs(db_session, proposal.id)
    evidence = review._read_blob(observation["input_identity_bytes"])["evidence"]
    assert evidence["state"] == "integrity_error"
    assert evidence["errorCode"] == "source_identity_or_evidence_missing"
    assert "verifiedBindingHash" not in evidence
    authority, case = _workflow(db_session, actor, member, directive, proposal)
    request = review.request_review(db_session, idempotency_key="request", **_args(db_session, authority, case, "review_requested"))
    db_session.commit()
    rejected = review.reject_review_case(db_session, idempotency_key="reject",
        expected_request_id=request["reviewRequestId"], reason_codes=["source_identity_or_evidence_missing"],
        explanation="Retained source is unavailable", **_args(db_session, authority, case, "review_rejected"))
    db_session.commit()
    assert rejected["state"] == "rejected"
    assert review.verified_review_case(db_session, case_id=case["caseId"], **authority)["signoff"]["action"] == "reject"
    if failure != "local_missing":
        assert calls


@pytest.mark.parametrize("code", sorted(review._STORAGE_UNAVAILABLE_CODES))
def test_expected_provider_error_codes_are_explicitly_classified(monkeypatch, code):
    error = ClientError({"Error": {"Code": code}}, "GetObject")
    def fail(document, **kwargs):
        raise error
    monkeypatch.setattr(review, "verified_retained_document_bytes", fail)
    assert review._retained_source_available(SimpleNamespace(storage_bytes=1)) is False


@pytest.mark.parametrize("error", [
    FileNotFoundError("missing"), PermissionError("denied"),
    EndpointConnectionError(endpoint_url="https://storage.test"),
    ConnectTimeoutError(endpoint_url="https://storage.test"),
    ReadTimeoutError(endpoint_url="https://storage.test"),
    ConnectionClosedError(endpoint_url="https://storage.test"),
    IncompleteReadError(actual_bytes=1, expected_bytes=2),
    ResponseStreamingError(error="stream unavailable"),
    SSLError(endpoint_url="https://storage.test", error="transport failed"),
    CredentialRetrievalError(provider="test", error_msg="unavailable"),
    NoCredentialsError(), PartialCredentialsError(provider="test", cred_var="secret_key"),
])
def test_expected_transport_and_unavailability_exceptions_are_classified(monkeypatch, error):
    def fail(document, **kwargs):
        raise error
    monkeypatch.setattr(review, "verified_retained_document_bytes", fail)
    assert review._retained_source_available(SimpleNamespace(storage_bytes=1)) is False


@pytest.mark.parametrize("error", [
    TypeError("programmer error"), KeyError("malformed SDK response"), RuntimeError("programmer error"),
    ValueError("SDK argument validation"), OperationalError("SELECT broken", {}, RuntimeError("database failed")),
    ClientError({"Error": {"Code": "InvalidRequest"}, "ResponseMetadata": {"HTTPStatusCode": 400}}, "GetObject"),
])
def test_unexpected_storage_or_database_exceptions_are_not_reclassified(db_session, monkeypatch, error):
    _, _, _, proposal = _source(db_session)
    def fail(document, **kwargs):
        raise error
    monkeypatch.setattr(review, "verified_retained_document_bytes", fail)
    with pytest.raises(type(error)) as captured:
        review._evidence_observation(db_session, proposal)
    assert captured.value is error


def test_history_capacity_leaves_request_and_rejection_slots(db_session, monkeypatch):
    _enable_app(monkeypatch)
    assert (review.MAX_CASES_PER_PROPOSAL, review.MAX_DRAFT_REVISIONS_PER_CASE, review.MAX_EVENTS_PER_CASE) == (100, 1000, 1003)
    monkeypatch.setattr(review, "MAX_CASES_PER_PROPOSAL", 1)
    monkeypatch.setattr(review, "MAX_DRAFT_REVISIONS_PER_CASE", 2)
    monkeypatch.setattr(review, "MAX_EVENTS_PER_CASE", 5)
    actor, member, directive, proposal = _seed_review_source(db_session)
    authority, case = _workflow(db_session, actor, member, directive, proposal)
    draft = None
    for index in range(2):
        draft = review.save_review_draft(db_session, idempotency_key=f"draft-{index}", annotations=[],
            **_args(db_session, authority, case, "draft_saved"))
        db_session.commit()
    with pytest.raises(review.ADV4Error) as exceeded:
        review.save_review_draft(db_session, idempotency_key="draft-overflow", annotations=[],
            **_args(db_session, authority, case, "draft_saved"))
    assert exceeded.value.code == "review_history_limit"
    db_session.rollback()
    request = review.request_review(db_session, idempotency_key="request", draft_revision_id=draft["draftRevisionId"],
        **_args(db_session, authority, case, "review_requested"))
    db_session.commit()
    review.reject_review_case(db_session, idempotency_key="reject", expected_request_id=request["reviewRequestId"],
        reason_codes=["remediation_requested"], explanation="Repair needed",
        **_args(db_session, authority, case, "review_rejected"))
    db_session.commit()
    current = review.verified_review_case(db_session, case_id=case["caseId"], **authority)
    assert current["eventTotal"] == 5
    with pytest.raises(review.ADV4Error) as exceeded_cases:
        review.create_review_case(db_session, directive_id=directive.id, proposal_id=proposal.id,
            idempotency_key="successor-overflow", expected_input_identity_hash=current["inputIdentityHash"],
            expected_authorization_observation_hash=current["authorizationObservationHashes"][review.ACTIONS["case_created"]], **authority)
    assert exceeded_cases.value.code == "review_history_limit"


@pytest.mark.parametrize("capacity", ["MAX_EVENTS_PER_CASE", "MAX_DRAFT_REVISIONS_PER_CASE"])
def test_history_queries_limit_plus_one_and_fail_closed_on_overflow(db_session, monkeypatch, capacity):
    _enable_app(monkeypatch)
    actor, member, directive, proposal = _seed_review_source(db_session)
    authority, case = _workflow(db_session, actor, member, directive, proposal)
    review.save_review_draft(db_session, idempotency_key="draft", annotations=[],
        **_args(db_session, authority, case, "draft_saved"))
    db_session.commit()
    monkeypatch.setattr(review, capacity, 1 if capacity == "MAX_EVENTS_PER_CASE" else 0)
    statements = []
    def capture(execute_state):
        statements.append(execute_state.statement)
    event.listen(db_session, "do_orm_execute", capture)
    try:
        with pytest.raises(review.ADV4Error) as captured:
            review.verified_review_case(db_session, case_id=case["caseId"], **authority)
        assert captured.value.code == "review_integrity"
    finally:
        event.remove(db_session, "do_orm_execute", capture)
    model = ADV4ReviewCaseEvent if capacity == "MAX_EVENTS_PER_CASE" else ADV4ReviewDraftRevision
    reads = [stmt for stmt in statements if model.__table__ in stmt.get_final_froms() and stmt._limit_clause is not None]
    assert len(reads) == 1
    assert reads[0]._limit_clause.value == getattr(review, capacity) + 1
    assert len(statements) <= 6


def test_case_overflow_query_and_predecessor_queries_are_bounded(db_session, monkeypatch):
    _enable_app(monkeypatch)
    actor, member, directive, proposal = _seed_review_source(db_session)
    authority, case = _workflow(db_session, actor, member, directive, proposal)
    statements = []
    def capture(execute_state):
        statements.append(execute_state.statement)
    event.listen(db_session, "do_orm_execute", capture)
    try:
        review.verified_review_case(db_session, case_id=case["caseId"], **authority)
    finally:
        event.remove(db_session, "do_orm_execute", capture)
    limited = [stmt._limit_clause.value for stmt in statements
               if ADV4ReviewCase.__table__ in stmt.get_final_froms() and stmt._limit_clause is not None]
    assert review.MAX_CASES_PER_PROPOSAL + 1 in limited
    assert 2 in limited
    # A bounded query detects excess rows before materializing their full graph.
    with pytest.raises(review.ADV4Error) as captured:
        review._bounded_rows(db_session, select(ADV4ReviewCase).where(ADV4ReviewCase.proposal_id == proposal.id),
                             limit=0, label="test overflow")
    assert captured.value.code == "review_integrity"


def _submission(actor, member, directive, proposal, number):
    return ADV4CandidateSubmission(proposal_id=proposal.id, directive_id=directive.id,
        actor_kind="platform_admin", actor_user_id=actor.id, authorizing_membership_id=member.id,
        organization_id=member.organization_id, actor_role="platform_admin", actor_status="active",
        auth_policy_name="test", auth_policy_version="1", auth_claims_hash="a" * 64,
        endpoint_action="test", idempotency_key=f"submission-{number}", request_hash="b" * 64,
        request_canonical_bytes=b"{}", raw_transport_hash="c" * 64,
        validator_version=proposal.validator_version, canonicalization_version=proposal.canonicalization_version)


@pytest.mark.parametrize("inventory", ["submissions", "relationships"])
def test_source_cutoff_real_2000_boundary_and_overflow(db_session, inventory):
    actor, member, directive, proposal = _seed_review_source(db_session)
    assert review.MAX_ARRAY_ITEMS == 2000
    if inventory == "submissions":
        def source(number):
            return _submission(actor, member, directive, proposal, number)
        model = ADV4CandidateSubmission
    else:
        submission = _submission(actor, member, directive, proposal, 0)
        db_session.add(submission)
        db_session.flush()
        def source(number):
            return ADV4CandidateSubmissionRelationship(submission_id=submission.id,
                relationship_key=f"relationship-{number}", relation_type="corrects_candidate",
                predecessor_proposal_id=proposal.id, reason="test bounded lookup", evidence_keys=[],
                canonical_bytes=b"{}", relationship_hash=f"{number + 1:064x}")
        model = ADV4CandidateSubmissionRelationship
    db_session.add_all([source(number) for number in range(2000)])
    db_session.flush()
    cutoff = review._cutoff(db_session, proposal.id)
    assert len(cutoff[inventory]) == 2000
    db_session.add(source(2000))
    db_session.flush()
    statements = []
    def capture(execute_state):
        statements.append(execute_state.statement)
    event.listen(db_session, "do_orm_execute", capture)
    try:
        with pytest.raises(review.ADV4Error) as captured:
            review._cutoff(db_session, proposal.id)
        assert captured.value.code == "review_history_limit"
    finally:
        event.remove(db_session, "do_orm_execute", capture)
    relevant = [stmt for stmt in statements if model.__tablename__ in str(stmt)]
    assert relevant[-1]._limit_clause.value == 2001
    assert len(statements) <= 2
    # Historical validation also refuses oversized arrays before querying IDs.
    cutoff[inventory].append(cutoff[inventory][-1])
    request = SimpleNamespace(proposal_id=proposal.id)
    with pytest.raises(review.ADV4Error) as stored:
        review._verify_frozen_sources(db_session, request, {"cutoff": cutoff})
    assert stored.value.code == "review_integrity"


def test_repeated_history_identity_uses_constant_source_verification_queries(db_session, monkeypatch):
    _enable_app(monkeypatch)
    actor, member, directive, proposal = _seed_review_source(db_session)
    authority, case = _workflow(db_session, actor, member, directive, proposal)
    for number in range(10):
        review.save_review_draft(db_session, idempotency_key=f"draft-{number}", annotations=[],
            **_args(db_session, authority, case, "draft_saved"))
        db_session.commit()
    original = review._verify_observation_sources
    calls = []
    def counted(*args, **kwargs):
        calls.append(1)
        return original(*args, **kwargs)
    monkeypatch.setattr(review, "_verify_observation_sources", counted)
    statements = []
    def capture(execute_state):
        statements.append(execute_state.statement)
    event.listen(db_session, "do_orm_execute", capture)
    try:
        result = review.verified_review_case(db_session, case_id=case["caseId"], **authority)
    finally:
        event.remove(db_session, "do_orm_execute", capture)
    assert result["draftTotal"] == 10 and result["eventTotal"] == 11
    assert len(calls) == 1
    assert len(statements) <= 20


def test_unavailable_retained_source_result_is_cached_only_within_one_read(db_session, monkeypatch):
    _, _, _, proposal = _source(db_session)
    calls = []
    def unavailable(document, **kwargs):
        calls.append(document.id)
        raise FileNotFoundError("expected missing retained source")
    monkeypatch.setattr(review, "verified_retained_document_bytes", unavailable)
    cache = {}
    for _ in range(3):
        observed = review._evidence_observation(db_session, proposal, document_cache=cache)
        assert observed["errorCode"] == "source_identity_or_evidence_missing"
    assert len(calls) == 1
    review._evidence_observation(db_session, proposal, document_cache={})
    assert len(calls) == 2


def _complete_history(db, monkeypatch):
    _enable_app(monkeypatch)
    actor, member, directive, proposal = _seed_review_source(db)
    authority, case = _workflow(db, actor, member, directive, proposal)
    draft = review.save_review_draft(db, idempotency_key="draft", annotations=[
        {"pointer": "/metadata", "text": "Keep the original extraction intact"}],
        **_args(db, authority, case, "draft_saved"))
    db.commit()
    request = review.request_review(db, idempotency_key="request", draft_revision_id=draft["draftRevisionId"],
        **_args(db, authority, case, "review_requested"))
    db.commit()
    review.reject_review_case(db, idempotency_key="reject", expected_request_id=request["reviewRequestId"],
        reason_codes=["remediation_requested"], explanation="Repair is required",
        **_args(db, authority, case, "review_rejected"))
    db.commit()
    return authority, case


def test_authoritative_byte_aggregate_is_single_portable_query_and_counts_every_blob(db_session, monkeypatch):
    _, case = _complete_history(db_session, monkeypatch)
    case_id = case["caseId"]
    models = (ADV4ReviewCase, ADV4ReviewDraftRevision, ADV4ReviewRequest,
              ADV4ReviewRejection, ADV4SignoffEvent, ADV4ReviewCaseEvent)
    expected = 0
    blobs = []
    for model in models:
        blob_columns = [column for column in model.__table__.columns if isinstance(column.type, LargeBinary)]
        assert {column.name for column in blob_columns} == {
            column.name for column in review._history_byte_columns(model)}
        identity = model.id if model is ADV4ReviewCase else model.case_id
        rows = list(db_session.scalars(select(model).where(identity == case_id)))
        assert rows
        for row in rows:
            for column in blob_columns:
                value = getattr(row, column.name)
                expected += len(value or b"")
                blobs.append((model, row.id, column.name, value))
    statements = []
    def capture(execute_state):
        statements.append(execute_state.statement)
    event.listen(db_session, "do_orm_execute", capture)
    try:
        assert review._stored_case_history_bytes(db_session, case_id) == expected
    finally:
        event.remove(db_session, "do_orm_execute", capture)
    assert len(statements) == 1
    for dialect in (postgresql.dialect(), sqlite.dialect()):
        sql = str(statements[0].compile(dialect=dialect))
        assert sql.count("length(") == sum(len(review._history_byte_columns(model)) for model in models)
        assert "coalesce(length(" in sql
    # Independently perturb every stored byte field, including each event blob:
    # no field can be skipped or counted twice by the aggregate.
    for model, row_id, field, payload in blobs:
        db_session.execute(update(model).where(model.id == row_id).values({field: payload + b" "}))
        assert review._stored_case_history_bytes(db_session, case_id) == expected + 1
        db_session.execute(update(model).where(model.id == row_id).values({field: payload}))
    assert review._stored_case_history_bytes(db_session, "absent-review-case") == 0


@pytest.mark.parametrize("delta", [-1, 0, 1])
def test_stored_and_pending_history_bytes_under_exact_and_over_boundary(db_session, monkeypatch, delta):
    assert review.MAX_DRAFT_PHASE_BYTES == 16 * 1024 * 1024
    assert review.MAX_REQUESTED_PHASE_BYTES == 28 * 1024 * 1024
    assert review.MAX_CASE_HISTORY_BYTES == 40 * 1024 * 1024
    _enable_app(monkeypatch)
    actor, member, directive, proposal = _seed_review_source(db_session)
    _, case = _workflow(db_session, actor, member, directive, proposal)
    stored = review._stored_case_history_bytes(db_session, case["caseId"])
    monkeypatch.setattr(review, "MAX_CASE_HISTORY_BYTES", stored - delta)
    if delta > 0:
        with pytest.raises(review.ADV4Error) as overflow:
            review._check_case_history_bytes(db_session, case["caseId"])
        assert overflow.value.code == "review_integrity"
    else:
        assert review._check_case_history_bytes(db_session, case["caseId"]) == stored
    # Null pending blobs count zero, with canonical_bytes counted exactly once.
    pending = ADV4ReviewDraftRevision(id="pending-byte-test", case_id=case["caseId"],
        annotation_bytes=b"abc", canonical_bytes=b"12345")
    unrelated = ADV4ReviewDraftRevision(id="other-byte-test", case_id="other-case", annotation_bytes=b"unrelated")
    db_session.add_all([pending, unrelated])
    assert review._pending_case_history_bytes(db_session, case["caseId"]) == 8
    monkeypatch.setattr(review, "MAX_CASE_HISTORY_BYTES", stored + 8 - delta)
    if delta > 0:
        with pytest.raises(review.ADV4Error) as overflow:
            review._check_case_history_bytes(db_session, case["caseId"], include_pending=True)
        assert overflow.value.code == "review_history_limit"
    else:
        assert review._check_case_history_bytes(db_session, case["caseId"], include_pending=True) == stored
    # The aggregate must never autoflush these deliberately incomplete objects.
    assert pending in db_session.new and unrelated in db_session.new
    db_session.rollback()


@pytest.mark.parametrize("action,owner_models", [
    ("case_created", {ADV4ReviewCase, ADV4ReviewCaseEvent}),
    ("draft_saved", {ADV4ReviewDraftRevision, ADV4ReviewCaseEvent}),
    ("review_requested", {ADV4ReviewRequest, ADV4ReviewCaseEvent}),
    ("review_rejected", {ADV4ReviewRejection, ADV4SignoffEvent, ADV4ReviewCaseEvent}),
])
def test_projected_operation_refused_before_any_owner_flush(db_session, monkeypatch, action, owner_models):
    _enable_app(monkeypatch)
    actor, member, directive, proposal = _seed_review_source(db_session)
    authority = dict(actor=actor, membership_id=member.id)
    if action == "case_created":
        snapshot = review.review_proposal_observation(db_session, directive_id=directive.id, proposal_id=proposal.id, **authority)
        mutate = review.create_review_case
        args = dict(directive_id=directive.id, proposal_id=proposal.id, **authority,
            expected_input_identity_hash=snapshot["inputIdentityHash"],
            expected_authorization_observation_hash=snapshot["authorizationObservationHashes"][review.ACTIONS[action]])
    else:
        authority, case = _workflow(db_session, actor, member, directive, proposal)
        if action == "review_rejected":
            request = review.request_review(db_session, idempotency_key="request", **_args(db_session, authority, case, "review_requested"))
            db_session.commit()
        args = _args(db_session, authority, case, action)
        mutate = {"draft_saved": review.save_review_draft, "review_requested": review.request_review,
                  "review_rejected": review.reject_review_case}[action]
        if action == "draft_saved":
            args["annotations"] = []
        elif action == "review_rejected":
            args.update(expected_request_id=request["reviewRequestId"], reason_codes=["remediation_requested"],
                        explanation="Needs correction")
    original_flush = review._flush_review_history
    observed = []
    flushed = []
    def before_flush(*args):
        flushed.append(True)
    def constrained_flush(db, case_id, objects=None):
        rows = [row for row in db.new if type(row) in owner_models]
        assert {type(row) for row in rows} == owner_models
        assert len(rows) == len(owner_models)
        pending = sum(len(getattr(row, column.name) or b"") for row in rows
                      for column in row.__table__.columns if isinstance(column.type, LargeBinary))
        assert review._pending_case_history_bytes(db, case_id) == pending
        stored = review._stored_case_history_bytes(db, case_id)
        observed.append((stored, pending))
        monkeypatch.setattr(review, "MAX_CASE_HISTORY_BYTES", stored + pending - 1)
        return original_flush(db, case_id, objects)
    monkeypatch.setattr(review, "_flush_review_history", constrained_flush)
    event.listen(db_session, "before_flush", before_flush)
    try:
        with pytest.raises(review.ADV4Error) as captured:
            mutate(db_session, idempotency_key="over-byte-budget", **args)
        assert captured.value.code == "review_history_limit"
    finally:
        event.remove(db_session, "before_flush", before_flush)
    assert len(observed) == 1 and not flushed
    db_session.rollback()


@pytest.mark.parametrize("reader", ["detail", "queue"])
def test_corrupted_history_byte_preflight_precedes_blob_materialization(db_session, monkeypatch, reader):
    _enable_app(monkeypatch)
    actor, member, directive, proposal = _seed_review_source(db_session)
    authority, case = _workflow(db_session, actor, member, directive, proposal)
    # The altered canonical blob is corrupt but still fits its per-column bound.
    db_session.execute(update(ADV4ReviewCase).where(ADV4ReviewCase.id == case["caseId"]).values(canonical_bytes=b"corrupt-case"))
    db_session.commit()
    stored = review._stored_case_history_bytes(db_session, case["caseId"])
    monkeypatch.setattr(review, "MAX_CASE_HISTORY_BYTES", stored - 1)
    statements, loaded = [], []
    def capture(execute_state):
        statements.append(execute_state.statement)
    def row_loaded(*args):
        loaded.append(True)
    event.listen(db_session, "do_orm_execute", capture)
    event.listen(db_session, "loaded_as_persistent", row_loaded)
    try:
        with pytest.raises(review.ADV4Error) as captured:
            if reader == "detail":
                review.verified_review_case(db_session, case_id=case["caseId"], **authority)
            else:
                review.list_review_cases(db_session, **authority)
        assert captured.value.code == "review_integrity"
    finally:
        event.remove(db_session, "do_orm_execute", capture)
        event.remove(db_session, "loaded_as_persistent", row_loaded)
    # Only scalar byte lengths, never authoritative review blobs, may be selected.
    model_tables = {model.__table__ for model in review._HISTORY_MODELS}
    for statement in statements:
        assert not any(getattr(column, "name", "").endswith("_bytes") and column.table in model_tables
                       for column in statement.selected_columns)
    if reader == "detail":
        assert not loaded
        assert len(statements) <= 3  # Fresh user/membership scalars + one byte aggregate.


def _clone_proposal(db, proposal, *, copy_bindings):
    values = {column.name: getattr(proposal, column.name) for column in proposal.__table__.columns
              if column.name not in {"id", "created_at"}}
    values["canonical_bytes"] = b'{"second":true}'
    values["canonical_hash"] = hashlib.sha256(DOMAINS_V2["proposal"] + values["canonical_bytes"]).hexdigest()
    clone = ADV4CandidateProposal(**values)
    db.add(clone)
    db.flush()
    if copy_bindings:
        for binding in db.scalars(select(ADV4CandidateEvidenceBinding).where(ADV4CandidateEvidenceBinding.proposal_id == proposal.id)):
            fields = {column.name: getattr(binding, column.name) for column in binding.__table__.columns
                      if column.name not in {"id", "created_at", "proposal_id"}}
            db.add(ADV4CandidateEvidenceBinding(proposal_id=clone.id, **fields))
    db.commit()
    return clone


@pytest.mark.parametrize("delta", [-1, 0, 1])
def test_retained_source_declared_exact_budget_and_overflow_before_io(db_session, monkeypatch, delta):
    assert review.MAX_RETAINED_SOURCE_BYTES == 64 * 1024 * 1024
    _, _, _, proposal = _source(db_session)
    document = db_session.scalar(select(ADSourceDocument))
    work = review._evidence_work_metadata(db_session, proposal.id)
    database_text_bytes = work.text_bytes + work.lifecycle_reason_bytes
    document.storage_bytes = review.MAX_RETAINED_SOURCE_BYTES - database_text_bytes + delta
    db_session.commit()
    calls = []
    def retained(document, *, max_size_bytes):
        calls.append(max_size_bytes)
        return b"stubbed-bounded-read"
    monkeypatch.setattr(review, "verified_retained_document_bytes", retained)
    observation = review._evidence_observation(db_session, proposal)
    if delta > 0:
        assert observation["state"] == "integrity_error"
        assert observation["errorCode"] == "source_identity_or_evidence_missing"
        assert not calls
    else:
        assert observation["state"] == "verified"
        assert calls == [document.storage_bytes]


def test_oversized_proposal_is_stably_nonverified_and_rejectable(db_session, monkeypatch):
    _enable_app(monkeypatch)
    actor, member, directive, proposal = _source(db_session)
    document = db_session.scalar(select(ADSourceDocument))
    document.storage_bytes = review.MAX_RETAINED_SOURCE_BYTES + 1
    db_session.commit()
    def forbidden_io(*args, **kwargs):
        pytest.fail("Over-budget proposals must never open a retained source")
    monkeypatch.setattr(review, "verified_retained_document_bytes", forbidden_io)
    authority, case = _workflow(db_session, actor, member, directive, proposal)
    request = review.request_review(db_session, idempotency_key="request", **_args(db_session, authority, case, "review_requested"))
    db_session.commit()
    rejected = review.reject_review_case(db_session, idempotency_key="reject", expected_request_id=request["reviewRequestId"],
        reason_codes=["source_identity_or_evidence_missing"], explanation="Source exceeds the review work budget",
        **_args(db_session, authority, case, "review_rejected"))
    db_session.commit()
    assert rejected["state"] == "rejected"
    queue = review.list_review_cases(db_session, **authority)
    detail = review.verified_review_case(db_session, case_id=case["caseId"], **authority)
    assert queue["cases"][0]["inputIdentityHash"] == detail["inputIdentityHash"] == case["inputIdentityHash"]


@pytest.mark.parametrize("shared_source,delta", [(False, -1), (False, 0), (False, 1), (True, 0)])
def test_queue_retained_source_budget_is_distinct_cumulative_and_preflighted(db_session, monkeypatch, shared_source, delta):
    _enable_app(monkeypatch)
    actor, member, directive, first = _source(db_session)
    second = _clone_proposal(db_session, first, copy_bindings=shared_source)
    if not shared_source:
        _source(db_session, source=(actor, member, directive, second))
    documents = list(db_session.scalars(select(ADSourceDocument).order_by(ADSourceDocument.id)))
    text_bytes = sum(
        work.text_bytes + work.lifecycle_reason_bytes
        for proposal in (first, second)
        for work in (review._evidence_work_metadata(db_session, proposal.id),)
    )
    remaining = review.MAX_RETAINED_SOURCE_BYTES - text_bytes
    per_document, remainder = divmod(remaining, len(documents))
    for index, document in enumerate(documents):
        document.storage_bytes = (remaining if shared_source else
            per_document + (remainder if index == 0 else 0) + (delta if index == len(documents) - 1 else 0))
    db_session.commit()
    calls = []
    def retained(document, *, max_size_bytes):
        calls.append((document.id, max_size_bytes))
        return b"stubbed-bounded-read"
    monkeypatch.setattr(review, "verified_retained_document_bytes", retained)
    authority, first_case = _workflow(db_session, actor, member, directive, first)
    _, second_case = _workflow(db_session, actor, member, directive, second, idempotency_key="create-second")
    calls.clear()
    if delta > 0:
        with pytest.raises(review.ADV4Error) as captured:
            review.list_review_cases(db_session, **authority)
        assert captured.value.code == "review_work_limit"
        assert not calls  # Full page union checked before even the first read.
        # Neither proposal's individual identity is weakened by queue overflow.
        for case in (first_case, second_case):
            detail = review.verified_review_case(db_session, case_id=case["caseId"], **authority)
            assert detail["inputIdentityHash"] == case["inputIdentityHash"]
            assert detail["inputIdentity"]["evidence"]["state"] == "verified"
    else:
        queue = review.list_review_cases(db_session, **authority)
        assert queue["count"] == 2
        assert len(calls) == (1 if shared_source else 2)
        assert sum(size for _, size in calls) <= review.MAX_RETAINED_SOURCE_BYTES
        assert {item["inputIdentityHash"] for item in queue["cases"]} == {
            first_case["inputIdentityHash"], second_case["inputIdentityHash"]}


def test_actual_retained_read_limit_failure_is_exactly_classified(monkeypatch):
    def too_large(document, *, max_size_bytes):
        assert max_size_bytes == 7
        raise ValueError("Stored file exceeds read byte limit")
    monkeypatch.setattr(review, "verified_retained_document_bytes", too_large)
    assert review._retained_source_available(SimpleNamespace(storage_bytes=7)) is False


def test_evidence_metadata_counts_utf8_text_repeated_per_binding_not_per_document(db_session):
    _, _, _, proposal = _source(db_session)
    binding = db_session.scalar(select(ADV4CandidateEvidenceBinding))
    fields = {column.name: getattr(binding, column.name) for column in binding.__table__.columns
              if column.name not in {"id", "created_at", "evidence_key"}}
    db_session.add(ADV4CandidateEvidenceBinding(evidence_key="second-binding", **fields))
    db_session.execute(update(ADEvidenceFragment).values(exact_text="é😀"))
    db_session.execute(update(ADSourcePageTextVersion).values(page_text="é😀"))
    db_session.commit()
    statements = []
    def capture(execute_state):
        statements.append(execute_state.statement)
    event.listen(db_session, "do_orm_execute", capture)
    proposal_id = proposal.id
    statements.clear()
    try:
        work = review._evidence_work_metadata(db_session, proposal_id)
    finally:
        event.remove(db_session, "do_orm_execute", capture)
    assert work.binding_count == 2
    assert work.text_bytes == 24  # (6 UTF-8 fragment bytes + 6 page bytes) x 2 bindings.
    assert work.lifecycle_count == 1
    assert work.lifecycle_reason_bytes == len("test admission".encode())
    assert len(work.document_keys) == 1
    assert len(statements) == 2  # One combined count/SUM plus bounded scalar document metadata.
    assert "sum(" in str(statements[0]) and "count(" in str(statements[0])


def test_authorship_cutoff_and_frozen_verification_never_select_payload_columns(db_session, monkeypatch):
    authority, case = _complete_history(db_session, monkeypatch)
    request = db_session.scalar(select(ADV4ReviewRequest).where(
        ADV4ReviewRequest.case_id == case["caseId"]))
    blobs = {
        "cutoff": review._read_blob(request.cutoff_bytes),
        "authorship_set": review._read_blob(request.authorship_set_bytes),
    }
    operations = (
        lambda: review._authorship(db_session, request.proposal_id),
        lambda: review._cutoff(db_session, request.proposal_id),
        lambda: review._verify_frozen_sources(db_session, request, blobs),
    )
    forbidden = {
        "request_canonical_bytes", "canonical_bytes", "raw_transport_bytes",
        "evidence_binding_bytes", "parsed_json", "exact_text", "page_text",
    }
    for operation in operations:
        statements = []
        def capture(execute_state):
            statements.append(execute_state.statement)
        event.listen(db_session, "do_orm_execute", capture)
        try:
            operation()
        finally:
            event.remove(db_session, "do_orm_execute", capture)
        assert statements
        selected = {getattr(column, "name", "")
                    for statement in statements for column in statement.selected_columns}
        assert not forbidden & selected
        sql = "\n".join(str(statement) for statement in statements)
        assert not any(name in sql for name in forbidden)


def test_lifecycle_count_overflow_fails_before_fragment_or_reason_materialization(db_session, monkeypatch):
    actor, _, _, proposal = _source(db_session)
    fragment = db_session.scalar(select(ADEvidenceFragment))
    admission = db_session.scalar(select(ADEvidenceFragmentLifecycleEvent).where(
        ADEvidenceFragmentLifecycleEvent.fragment_id == fragment.id))
    reason = "bounded quarantine"
    db_session.add(ADEvidenceFragmentLifecycleEvent(
        fragment_id=fragment.id, event_type="quarantined", actor_user_id=actor.id,
        reason=reason, sequence_number=1, predecessor_event_hash=admission.event_hash,
        event_hash=_hash_parts(fragment.id, fragment.fragment_hash, "quarantined",
                               actor.id, reason, 1, admission.event_hash)))
    db_session.commit()
    proposal = review._proposal(db_session, proposal.id)
    monkeypatch.setattr(review, "MAX_ARRAY_ITEMS", 1)
    statements = []
    def capture(execute_state):
        statements.append(execute_state.statement)
    event.listen(db_session, "do_orm_execute", capture)
    try:
        observed = review._evidence_observation(db_session, proposal)
    finally:
        event.remove(db_session, "do_orm_execute", capture)
    assert observed == {
        "storedBindingHash": proposal.evidence_binding_hash,
        "state": "integrity_error",
        "errorCode": "source_identity_or_evidence_missing",
    }
    assert len(statements) == 1
    assert not any(getattr(column, "name", "") in {"reason", "exact_text", "page_text"}
                   for column in statements[0].selected_columns)


@pytest.mark.parametrize("delta", [0, 1])
def test_direct_sql_text_size_is_preflighted_before_text_materialization(db_session, monkeypatch, delta):
    _, _, _, proposal = _source(db_session)
    # Generate the large page in SQLite, not as a Python/ORM text value. The
    # fixture bound is small; the same aggregate is used for the 64 MiB constant.
    monkeypatch.setattr(review, "MAX_RETAINED_SOURCE_BYTES", 1024)
    lifecycle_bytes = review._evidence_work_metadata(db_session, proposal.id).lifecycle_reason_bytes
    page_size = 1024 - 6 - 6 - lifecycle_bytes + delta  # exact text + retained file + lifecycle reason.
    db_session.execute(update(ADSourcePageTextVersion).values(
        page_text=func.substr(func.hex(func.zeroblob(page_size)), 1, page_size)))
    db_session.commit()
    proposal_id = proposal.id
    proposal = review._proposal(db_session, proposal_id)
    statements = []
    def capture(execute_state):
        statements.append(execute_state.statement)
    def forbidden_io(*args, **kwargs):
        pytest.fail("Invalid/over-budget database text must not reach external I/O")
    monkeypatch.setattr(review, "verified_retained_document_bytes", forbidden_io)
    event.listen(db_session, "do_orm_execute", capture)
    try:
        observed = review._evidence_observation(db_session, proposal)
    finally:
        event.remove(db_session, "do_orm_execute", capture)
    text_selected = any(getattr(column, "name", "") in {"exact_text", "page_text"}
                        for statement in statements for column in statement.selected_columns)
    assert observed["state"] == "integrity_error"
    if delta:
        assert observed["errorCode"] == "source_identity_or_evidence_missing"
        assert not text_selected
        assert len(statements) <= 2
    else:
        assert observed["errorCode"] == "evidence_integrity"  # Byte budget passed; altered page hash fails.
        assert text_selected


@pytest.mark.parametrize("delta", [0, 1])
def test_queue_text_and_binding_preflight_happens_before_any_preparation(db_session, monkeypatch, delta):
    _enable_app(monkeypatch)
    actor, member, directive, first = _source(db_session)
    second = _clone_proposal(db_session, first, copy_bindings=True)
    monkeypatch.setattr(review, "verified_retained_document_bytes", lambda *args, **kwargs: b"source")
    authority, _ = _workflow(db_session, actor, member, directive, first)
    _workflow(db_session, actor, member, directive, second, idempotency_key="second-create")
    # Distinct proposals each repeat the same tiny source 1,000 times. Only a
    # count budget, not a distinct retained-file byte budget, detects +1 here.
    for number, proposal in enumerate((first, second)):
        binding = db_session.scalar(select(ADV4CandidateEvidenceBinding).where(
            ADV4CandidateEvidenceBinding.proposal_id == proposal.id))
        fields = {column.name: getattr(binding, column.name) for column in binding.__table__.columns
                  if column.name not in {"id", "created_at", "evidence_key"}}
        db_session.execute(insert(ADV4CandidateEvidenceBinding), [
            {**fields, "evidence_key": f"repeat-{index}"} for index in range(999 + (delta if number else 0))])
    db_session.commit()
    prepared = []
    class PreparationReached(Exception):
        pass
    def prepare(*args, **kwargs):
        prepared.append(True)
        raise PreparationReached()
    monkeypatch.setattr(review, "_prepare_evidence_observation", prepare)
    if delta:
        with pytest.raises(review.ADV4Error) as captured:
            review.list_review_cases(db_session, **authority)
        assert captured.value.code == "review_work_limit"
        assert not prepared
    else:
        with pytest.raises(PreparationReached):
            review.list_review_cases(db_session, **authority)
        assert prepared


def test_queue_cumulative_database_text_is_preflighted_before_materialization(db_session, monkeypatch):
    _enable_app(monkeypatch)
    actor, member, directive, first = _source(db_session)
    second = _clone_proposal(db_session, first, copy_bindings=True)
    monkeypatch.setattr(review, "verified_retained_document_bytes", lambda *args, **kwargs: b"source")
    authority, _ = _workflow(db_session, actor, member, directive, first)
    _workflow(db_session, actor, member, directive, second, idempotency_key="second-create")
    # Each proposal: 6 fragment + 12 page + 6 retained = 24 bytes. The request:
    # two distinct proposal text workloads (36) + one shared retained source (6).
    db_session.execute(update(ADSourcePageTextVersion).values(page_text="longer text!"))
    db_session.commit()
    monkeypatch.setattr(review, "MAX_RETAINED_SOURCE_BYTES", 41)
    def forbidden_prepare(*args, **kwargs):
        pytest.fail("Queue byte budget must run before text preparation")
    monkeypatch.setattr(review, "_prepare_evidence_observation", forbidden_prepare)
    with pytest.raises(review.ADV4Error) as captured:
        review.list_review_cases(db_session, **authority)
    assert captured.value.code == "review_work_limit"


def test_single_proposal_binding_overflow_is_nonverified_without_binding_or_text_loads(db_session):
    _, _, _, proposal = _source(db_session)
    binding = db_session.scalar(select(ADV4CandidateEvidenceBinding))
    fields = {column.name: getattr(binding, column.name) for column in binding.__table__.columns
              if column.name not in {"id", "created_at", "evidence_key"}}
    db_session.execute(insert(ADV4CandidateEvidenceBinding), [
        {**fields, "evidence_key": f"repeat-{index}"} for index in range(review.MAX_ARRAY_ITEMS)])
    db_session.commit()
    proposal = review._proposal(db_session, proposal.id)
    statements = []
    def capture(execute_state):
        statements.append(execute_state.statement)
    event.listen(db_session, "do_orm_execute", capture)
    try:
        observed = review._evidence_observation(db_session, proposal)
    finally:
        event.remove(db_session, "do_orm_execute", capture)
    assert observed["state"] == "integrity_error"
    assert observed["errorCode"] == "source_identity_or_evidence_missing"
    assert len(statements) == 1  # Scalar count/text aggregate only, no owner rows.
    assert not any(getattr(column, "name", "") in {"exact_text", "page_text", "evidence_key"}
                   for column in statements[0].selected_columns)


@pytest.mark.parametrize("obligation", [False, True])
def test_source_work_overflow_does_not_reenter_fragment_loading_via_projection(monkeypatch, obligation):
    projection = SimpleNamespace(id="projection", projection_hash="a" * 64,
        directive_id="directive",
        materializer_version=review.OBLIGATION_VERSION if obligation else review.APP_VERSION)
    head = SimpleNamespace(event_hash="b" * 64)
    db = SimpleNamespace(execute=lambda query: SimpleNamespace(one_or_none=lambda: head))
    def forbidden(*args, **kwargs):
        pytest.fail("An over-budget source cannot enter projection reconstruction")
    monkeypatch.setattr(review, "reconstruct_applicability", forbidden)
    monkeypatch.setattr(review, "reconstruct_obligation_projection", forbidden)
    result = review._projection_observation(
        db, SimpleNamespace(id="proposal"), obligation=obligation,
        source_work_exceeded=True,
        prepared=([projection], review._ProjectionAuditWork(1)))
    assert result == {"id": "projection", "storedHash": "a" * 64, "eventHeadHash": "b" * 64,
                      "state": "integrity_error", "errorCode": "projection_integrity"}

```
### `backend/tests/test_ad_v4_review_service_postgres.py`

size=17001; sha256=c750ea96ee211756e64c2f33302a67ec5f80af7e2a59833457a1fa9e44571d1a; truncated=false

```text
from __future__ import annotations

import json
import os
import uuid

import pytest
from sqlalchemy import create_engine, event, select, text
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.core import (
    ADV4CandidateAppMaterializationRequest, ADV4CandidateAppProjection,
    ADV4CandidateObligationMaterializationRequest,
    ADV4CandidateObligationProjection, User,
)
from app.services import ad_v4_reviews as review_module
from app.services.ad_v4_candidates import ADV4Error, VALIDATOR_VERSION_V2
from app.services.ad_v4_reviews import (
    create_review_case,
    reject_review_case,
    request_review,
    review_proposal_observation,
    save_review_draft,
    verified_review_case,
)
from test_ad_v4_applicability_postgres import _enable, _store
from test_ad_v4_review_case_migration_postgres import Records, _materialize_review_fixture


URL = os.getenv("PAPRNAV_TEST_POSTGRES_URL")
pytestmark = pytest.mark.skipif(not URL, reason="PAPRNAV_TEST_POSTGRES_URL required")


def test_service_rejection_lifecycle_commits_under_deferred_sql_validation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("PAPRNAV_AD_V4_SLICE4_READS_ENABLED", "true")
    monkeypatch.setenv("PAPRNAV_AD_V4_SLICE4_DRAFTS_ENABLED", "true")
    monkeypatch.setenv("PAPRNAV_AD_V4_SLICE4_DECISIONS_ENABLED", "true")
    get_settings.cache_clear()
    engine = create_engine(URL)
    with Session(engine) as db:
        _enable(db)
        for gate in ("materializer3b_enabled", "reviewer4_draft_enabled", "reviewer4_decision_enabled"):
            db.execute(text(
                "SELECT paprnav_set_v4_feature_gate(:gate,true,'review-service-test')"
            ), {"gate": gate})
        db.commit()
        user_id, membership_id, directive_id, proposal_id = _store(
            db,
            validator_version=VALIDATOR_VERSION_V2,
            suffix=f"review-service-{uuid.uuid4().hex}",
        )
        actor = db.get(User, user_id)
        assert actor is not None

        observed = review_proposal_observation(
            db,
            directive_id=directive_id,
            proposal_id=proposal_id,
            actor=actor,
            membership_id=membership_id,
        )
        case = create_review_case(
            db,
            directive_id=directive_id,
            proposal_id=proposal_id,
            actor=actor,
            membership_id=membership_id,
            idempotency_key=f"case-{uuid.uuid4().hex}",
            expected_authorization_observation_hash=observed[
                "authorizationObservationHashes"
            ]["create_ad_v4_review_case"],
            expected_input_identity_hash=observed["inputIdentityHash"],
        )
        draft = save_review_draft(
            db,
            case_id=case["caseId"],
            actor=actor,
            membership_id=membership_id,
            idempotency_key=f"draft-{uuid.uuid4().hex}",
            expected_authorization_observation_hash=case[
                "authorizationObservationHashes"
            ]["save_ad_v4_review_draft"],
            expected_input_identity_hash=case["inputIdentityHash"],
            expected_predecessor_event_hash=case["latestEventHash"],
            annotations=[{"pointer": "/requirements", "text": "Remediate"}],
            intended_action="reject",
        )
        requested = request_review(
            db,
            case_id=case["caseId"],
            actor=actor,
            membership_id=membership_id,
            idempotency_key=f"request-{uuid.uuid4().hex}",
            expected_authorization_observation_hash=draft[
                "authorizationObservationHashes"
            ]["request_ad_v4_review"],
            expected_input_identity_hash=draft["inputIdentityHash"],
            expected_predecessor_event_hash=draft["latestEventHash"],
            draft_revision_id=draft["draftRevisionId"],
        )
        rejected = reject_review_case(
            db,
            case_id=case["caseId"],
            actor=actor,
            membership_id=membership_id,
            idempotency_key=f"reject-{uuid.uuid4().hex}",
            expected_authorization_observation_hash=requested[
                "authorizationObservationHashes"
            ]["reject_ad_v4_review"],
            expected_input_identity_hash=requested["inputIdentityHash"],
            expected_predecessor_event_hash=requested["latestEventHash"],
            expected_request_id=requested["reviewRequestId"],
            reason_codes=["remediation_requested"],
            explanation="Candidate requires remediation.",
        )
        db.execute(text("SET CONSTRAINTS ALL IMMEDIATE"))
        db.commit()

        verified = verified_review_case(
            db,
            case_id=case["caseId"],
            actor=actor,
            membership_id=membership_id,
            event_limit=2,
            event_offset=1,
        )
        assert rejected["state"] == verified["state"] == "rejected"
        assert verified["eventTotal"] == 4
        assert [event["sequenceNumber"] for event in verified["events"]] == [1, 2]
        assert verified["signoff"]["action"] == "reject"
    engine.dispose()


def test_maximal_admitted_drafts_preserve_request_rejection_and_successor_liveness(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The draft-phase ceiling must reserve every remaining immutable row."""
    monkeypatch.setenv("PAPRNAV_AD_V4_SLICE4_READS_ENABLED", "true")
    monkeypatch.setenv("PAPRNAV_AD_V4_SLICE4_DRAFTS_ENABLED", "true")
    monkeypatch.setenv("PAPRNAV_AD_V4_SLICE4_DECISIONS_ENABLED", "true")
    get_settings.cache_clear()
    engine = create_engine(URL)
    with Session(engine) as db:
        _enable(db)
        for gate in ("materializer3b_enabled", "reviewer4_draft_enabled", "reviewer4_decision_enabled"):
            db.execute(text(
                "SELECT paprnav_set_v4_feature_gate(:gate,true,'review-liveness-test')"
            ), {"gate": gate})
        db.commit()
        user_id, membership_id, directive_id, proposal_id = _store(
            db, validator_version=VALIDATOR_VERSION_V2,
            suffix=f"review-liveness-{uuid.uuid4().hex}")
        actor = db.get(User, user_id)
        observed = review_proposal_observation(
            db, directive_id=directive_id, proposal_id=proposal_id,
            actor=actor, membership_id=membership_id)
        current = create_review_case(
            db, directive_id=directive_id, proposal_id=proposal_id,
            actor=actor, membership_id=membership_id,
            idempotency_key=f"case-{uuid.uuid4().hex}",
            expected_authorization_observation_hash=observed[
                "authorizationObservationHashes"]["create_ad_v4_review_case"],
            expected_input_identity_hash=observed["inputIdentityHash"])
        db.commit()

        annotations = [
            {"pointer": f"/requirements/{index}", "text": "x" * 4096}
            for index in range(128)
        ]
        accepted = 0
        for attempt in range(30):
            try:
                current = save_review_draft(
                    db, case_id=current["caseId"], actor=actor,
                    membership_id=membership_id,
                    idempotency_key=f"draft-{attempt}-{uuid.uuid4().hex}",
                    expected_authorization_observation_hash=current[
                        "authorizationObservationHashes"]["save_ad_v4_review_draft"],
                    expected_input_identity_hash=current["inputIdentityHash"],
                    expected_predecessor_event_hash=current["latestEventHash"],
                    annotations=annotations, intended_action="reject")
                db.commit()
                accepted += 1
            except ADV4Error as exc:
                assert exc.code == "review_history_limit"
                db.rollback()
                break
        else:
            pytest.fail("Draft-phase byte ceiling was not reached")
        assert accepted > 0
        stored = db.scalar(text(
            "SELECT paprnav_v4_review_case_authoritative_bytes(:case_id)"
        ), {"case_id": current["caseId"]})

        # Fill the remaining draft phase to within one small append quantum.
        # Measuring pending rows does not flush or bypass any persisted guard;
        # the selected payload is then written through the ordinary service.
        class PendingBytes(Exception):
            def __init__(self, size: int):
                self.size = size

        def measure(text_size: int) -> int:
            annotations = [
                {"pointer": f"/requirements/{index}", "text": "y" * text_size}
                for index in range(128)
            ]
            def capture_pending(session, case_id, objects=None):
                from app.services import ad_v4_reviews as review_module
                raise PendingBytes(review_module._pending_case_history_bytes(session, case_id))
            with monkeypatch.context() as scoped:
                scoped.setattr("app.services.ad_v4_reviews._flush_review_history", capture_pending)
                with pytest.raises(PendingBytes) as captured:
                    save_review_draft(
                        db, case_id=current["caseId"], actor=actor,
                        membership_id=membership_id,
                        idempotency_key=f"measure-{text_size}-{uuid.uuid4().hex}",
                        expected_authorization_observation_hash=current[
                            "authorizationObservationHashes"]["save_ad_v4_review_draft"],
                        expected_input_identity_hash=current["inputIdentityHash"],
                        expected_predecessor_event_hash=current["latestEventHash"],
                        annotations=annotations, intended_action="reject")
            db.rollback()
            return captured.value.size

        low, high = 1, 4096
        while low < high:
            middle = (low + high + 1) // 2
            if stored + measure(middle) <= 16 * 1024 * 1024:
                low = middle
            else:
                high = middle - 1
        final_annotations = [
            {"pointer": f"/requirements/{index}", "text": "y" * low}
            for index in range(128)
        ]
        current = save_review_draft(
            db, case_id=current["caseId"], actor=actor,
            membership_id=membership_id,
            idempotency_key=f"draft-final-{uuid.uuid4().hex}",
            expected_authorization_observation_hash=current[
                "authorizationObservationHashes"]["save_ad_v4_review_draft"],
            expected_input_identity_hash=current["inputIdentityHash"],
            expected_predecessor_event_hash=current["latestEventHash"],
            annotations=final_annotations, intended_action="reject")
        db.commit()
        stored = db.scalar(text(
            "SELECT paprnav_v4_review_case_authoritative_bytes(:case_id)"
        ), {"case_id": current["caseId"]})
        assert 0 <= 16 * 1024 * 1024 - stored < 1024

        requested = request_review(
            db, case_id=current["caseId"], actor=actor,
            membership_id=membership_id,
            idempotency_key=f"request-{uuid.uuid4().hex}",
            expected_authorization_observation_hash=current[
                "authorizationObservationHashes"]["request_ad_v4_review"],
            expected_input_identity_hash=current["inputIdentityHash"],
            expected_predecessor_event_hash=current["latestEventHash"],
            draft_revision_id=current["draftRevisionId"])
        db.commit()
        rejected = reject_review_case(
            db, case_id=current["caseId"], actor=actor,
            membership_id=membership_id,
            idempotency_key=f"reject-{uuid.uuid4().hex}",
            expected_authorization_observation_hash=requested[
                "authorizationObservationHashes"]["reject_ad_v4_review"],
            expected_input_identity_hash=requested["inputIdentityHash"],
            expected_predecessor_event_hash=requested["latestEventHash"],
            expected_request_id=requested["reviewRequestId"],
            reason_codes=["remediation_requested"],
            explanation="Bounded remediation is required.")
        db.execute(text("SET CONSTRAINTS ALL IMMEDIATE"))
        db.commit()

        successor = create_review_case(
            db, directive_id=directive_id, proposal_id=proposal_id,
            actor=actor, membership_id=membership_id,
            idempotency_key=f"successor-{uuid.uuid4().hex}",
            expected_authorization_observation_hash=rejected[
                "authorizationObservationHashes"]["create_ad_v4_review_case"],
            expected_input_identity_hash=rejected["inputIdentityHash"])
        db.execute(text("SET CONSTRAINTS ALL IMMEDIATE"))
        db.commit()
        assert successor["caseId"] != current["caseId"]
        assert successor["state"] == "draft"
    engine.dispose()


@pytest.mark.parametrize("overflow", ["obligation_count", "parent_count", "parent_bytes"])
def test_repeated_projection_requests_are_preflighted_before_payload_loading(
    monkeypatch: pytest.MonkeyPatch, overflow: str,
) -> None:
    from app.services.ad_v4_applicability import materialize_applicability
    from app.services.ad_v4_obligation_persistence import materialize_obligations

    engine = create_engine(URL)
    with Session(engine) as db:
        records = Records(db)
        projections = _materialize_review_fixture(records)
        projection = db.get(
            ADV4CandidateObligationProjection,
            projections["obligationProjection"]["id"],
        )
        app_projection = db.get(ADV4CandidateAppProjection, projection.app_projection_id)
        repeats = 7 if overflow == "parent_bytes" else 2
        for _ in range(repeats):
            if overflow == "obligation_count":
                materialize_obligations(
                    db, directive_id=records.directive, proposal_id=records.proposal,
                    app_projection_id=projection.app_projection_id,
                    actor=db.get(User, records.user), membership_id=records.member,
                    idempotency_key=uuid.uuid4().hex)
            else:
                materialize_applicability(
                    db, directive_id=records.directive, proposal_id=records.proposal,
                    actor=db.get(User, records.user), membership_id=records.member,
                    idempotency_key=uuid.uuid4().hex)
            db.commit()
        request_model = (ADV4CandidateObligationMaterializationRequest
                         if overflow == "obligation_count"
                         else ADV4CandidateAppMaterializationRequest)
        request_projection_id = projection.id if overflow == "obligation_count" else app_projection.id
        assert db.scalar(select(text("count(*)")).select_from(
            request_model).where(request_model.projection_id == request_projection_id)) == repeats + 1

        statements = []
        def capture(execute_state):
            statements.append(execute_state.statement)
        if overflow.endswith("count"):
            monkeypatch.setattr(review_module, "MAX_ARRAY_ITEMS", 2)
        else:
            parent_work = review_module._prepare_projection_observation(
                db, records.proposal, obligation=False)[1]
            child_work = review_module._prepare_projection_observation(
                db, records.proposal, obligation=True)[1]
            evidence_work = review_module._evidence_work_metadata(db, records.proposal)
            evidence_bytes = (evidence_work.text_bytes + evidence_work.lifecycle_reason_bytes
                              + sum(key[2] for key in evidence_work.document_keys))
            limit = max(child_work.payload_bytes, evidence_bytes) + 1
            assert parent_work.payload_bytes > limit
            monkeypatch.setattr(review_module, "MAX_RETAINED_SOURCE_BYTES", limit)
        event.listen(db, "do_orm_execute", capture)
        try:
            observation = review_module.observe_review_inputs(db, records.proposal)
        finally:
            event.remove(db, "do_orm_execute", capture)
        identity = json.loads(observation["input_identity_bytes"])
        assert identity["obligationProjection"]["state"] == "integrity_error"
        assert identity["obligationProjection"]["errorCode"] == "projection_integrity"
        assert identity["applicabilityProjection"]["state"] == (
            "verified" if overflow == "obligation_count" else "integrity_error")
        request_statements = [statement for statement in statements
                              if request_model.__tablename__ in str(statement)]
        assert request_statements
        assert any("count(" in str(statement).lower() for statement in request_statements)
        assert not any(
            getattr(column, "name", "") == "request_canonical_bytes"
            for statement in request_statements for column in statement.selected_columns
        )
    engine.dispose()

```
### `backend/tests/test_ad_v4_reviews.py`

size=9179; sha256=40869d3de9dbd0ab830f18f9d75d01e464840369206498b688e15dba1eecb67e; truncated=false

```text
from __future__ import annotations

import hashlib

from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.models.core import (
    ADV4CandidateProposal,
    ADV4FeatureGate,
    ADV4ReviewCaseEvent,
    AirworthinessDirective,
)
from app.services.ad_v4_candidates import (
    CANONICALIZATION_VERSION_V2,
    DOMAINS_V2,
    VALIDATOR_VERSION_V2,
)
from conftest import add_membership, create_organization, create_user, login


def _seed_review_source(db):
    admin = create_user(db, "v4.review.admin@paprnav.local", "V4 Review Admin")
    platform = create_organization(db, "Paprnav V4 Review", "platform")
    membership = add_membership(db, platform, admin, "platform_admin")
    directive = AirworthinessDirective(
        ad_number="2026-09-13",
        title="V4 rejection-only review fixture",
        source_content_hash="a" * 64,
        status="candidate",
        extraction_status="not_started",
        review_status="not_started",
    )
    db.add(directive)
    db.flush()

    proposal_bytes = b"{}"
    proposal = ADV4CandidateProposal(
        directive_id=directive.id,
        schema_version="ad_extraction_v4",
        canonicalization_version=CANONICALIZATION_VERSION_V2,
        validator_version=VALIDATOR_VERSION_V2,
        canonical_bytes=proposal_bytes,
        parsed_json={"evidenceBindings": {}},
        canonical_hash=hashlib.sha256(
            DOMAINS_V2["proposal"] + proposal_bytes
        ).hexdigest(),
        evidence_binding_bytes=b"{}",
        evidence_binding_hash="b" * 64,
        binding_count=0,
        gate="candidate_only",
    )
    db.add(proposal)
    db.add_all([
        ADV4FeatureGate(gate_key=key, enabled=enabled, changed_by="review-test")
        for key, enabled in (
            ("validator2_write_enabled", False),
            ("materializer3a_enabled", False),
            ("materializer3b_enabled", False),
            ("reviewer4_draft_enabled", True),
            ("reviewer4_decision_enabled", True),
        )
    ])
    db.commit()
    return admin, membership, directive, proposal


def _enable_app(monkeypatch) -> None:
    monkeypatch.setenv("PAPRNAV_AD_V4_SLICE4_READS_ENABLED", "true")
    monkeypatch.setenv("PAPRNAV_AD_V4_SLICE4_DRAFTS_ENABLED", "true")
    monkeypatch.setenv("PAPRNAV_AD_V4_SLICE4_DECISIONS_ENABLED", "true")
    get_settings.cache_clear()


def _headers(membership_id: str, key: str | None = None) -> dict[str, str]:
    headers = {"Paprnav-Acting-Membership-Id": membership_id}
    if key is not None:
        headers["Idempotency-Key"] = key
    return headers


def test_rejection_only_review_lifecycle_is_immutable_and_idempotent(
    client: TestClient, db_session, monkeypatch,
) -> None:
    _enable_app(monkeypatch)
    admin, membership, directive, proposal = _seed_review_source(db_session)
    login(client, admin.email)

    observed = client.get(
        f"/api/v1/ads/directives/{directive.id}/v4/candidate-proposals/"
        f"{proposal.id}/review-observation",
        headers=_headers(membership.id),
    )
    assert observed.status_code == 200, observed.text
    snapshot = observed.json()
    assert snapshot["inputIdentity"]["proposal"]["state"] == "integrity_error"
    assert snapshot["inputIdentity"]["applicabilityProjection"]["state"] == "missing"
    observed_again = client.get(
        f"/api/v1/ads/directives/{directive.id}/v4/candidate-proposals/"
        f"{proposal.id}/review-observation",
        headers=_headers(membership.id),
    )
    assert observed_again.status_code == 200
    assert observed_again.json()["inputIdentityHash"] == snapshot["inputIdentityHash"]
    assert observed_again.json()["observationHash"] != snapshot["observationHash"]

    create_body = {
        "expectedAuthorizationObservationHash": snapshot[
            "authorizationObservationHashes"
        ]["create_ad_v4_review_case"],
        "expectedInputIdentityHash": snapshot["inputIdentityHash"],
    }
    created = client.post(
        f"/api/v1/ads/directives/{directive.id}/v4/candidate-proposals/"
        f"{proposal.id}/review-cases",
        json=create_body,
        headers=_headers(membership.id, "case-create"),
    )
    assert created.status_code == 201, created.text
    case = created.json()
    assert case["state"] == "draft"
    assert case["idempotentRetry"] is False

    retried = client.post(
        f"/api/v1/ads/directives/{directive.id}/v4/candidate-proposals/"
        f"{proposal.id}/review-cases",
        json=create_body,
        headers=_headers(membership.id, "case-create"),
    )
    assert retried.status_code == 200, retried.text
    assert retried.json()["caseId"] == case["caseId"]
    assert retried.json()["idempotentRetry"] is True

    draft = client.post(
        f"/api/v1/ads/v4/review-cases/{case['caseId']}/drafts",
        json={
            "expectedAuthorizationObservationHash": case[
                "authorizationObservationHashes"
            ]["save_ad_v4_review_draft"],
            "expectedPredecessorEventHash": case["latestEventHash"],
            "expectedInputIdentityHash": case["inputIdentityHash"],
            "annotations": [{"pointer": "/requirements", "text": "Needs remediation"}],
            "intendedAction": "reject",
        },
        headers=_headers(membership.id, "draft-one"),
    )
    assert draft.status_code == 201, draft.text
    case = draft.json()
    assert len(case["drafts"]) == 1

    requested = client.post(
        f"/api/v1/ads/v4/review-cases/{case['caseId']}/review-request",
        json={
            "expectedAuthorizationObservationHash": case[
                "authorizationObservationHashes"
            ]["request_ad_v4_review"],
            "expectedPredecessorEventHash": case["latestEventHash"],
            "expectedInputIdentityHash": case["inputIdentityHash"],
            "draftRevisionId": case["draftRevisionId"],
        },
        headers=_headers(membership.id, "request-one"),
    )
    assert requested.status_code == 201, requested.text
    case = requested.json()
    assert case["state"] == "pending_review"
    assert case["reviewRequest"]["authorshipSourceCount"] == 0

    rejected = client.post(
        f"/api/v1/ads/v4/review-cases/{case['caseId']}/rejection",
        json={
            "expectedAuthorizationObservationHash": case[
                "authorizationObservationHashes"
            ]["reject_ad_v4_review"],
            "expectedPredecessorEventHash": case["latestEventHash"],
            "expectedRequestId": case["reviewRequestId"],
            "expectedInputIdentityHash": case["inputIdentityHash"],
            "reasonCodes": ["remediation_requested", "candidate_integrity"],
            "explanation": "Candidate requires a schema-valid resubmission.",
        },
        headers=_headers(membership.id, "reject-one"),
    )
    assert rejected.status_code == 201, rejected.text
    final = rejected.json()
    assert final["state"] == "rejected"
    assert final["signoff"]["action"] == "reject"
    assert final["rejection"]["reasonCodes"] == [
        "candidate_integrity", "remediation_requested",
    ]
    assert [event["eventType"] for event in final["events"]] == [
        "case_created", "draft_saved", "review_requested", "review_rejected",
    ]
    assert db_session.get(AirworthinessDirective, directive.id).status == "candidate"

    detail = client.get(
        f"/api/v1/ads/v4/review-cases/{case['caseId']}",
        headers=_headers(membership.id),
    )
    assert detail.status_code == 200, detail.text
    assert detail.json()["latestEventHash"] == final["latestEventHash"]

    terminal = db_session.query(ADV4ReviewCaseEvent).filter_by(
        case_id=case["caseId"], event_type="review_rejected"
    ).one()
    terminal.event_hash = "0" * 64
    db_session.commit()
    corrupted = client.get(
        f"/api/v1/ads/v4/review-cases/{case['caseId']}",
        headers=_headers(membership.id),
    )
    assert corrupted.status_code == 409
    assert corrupted.json()["detail"]["code"] == "review_integrity"


def test_review_routes_fail_closed_when_read_capability_is_disabled(
    client: TestClient, db_session,
) -> None:
    admin, membership, directive, proposal = _seed_review_source(db_session)
    login(client, admin.email)
    response = client.get(
        f"/api/v1/ads/directives/{directive.id}/v4/candidate-proposals/"
        f"{proposal.id}/review-observation",
        headers=_headers(membership.id),
    )
    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "capability_disabled"


def test_review_authorization_uses_fresh_membership_state(
    client: TestClient, db_session, monkeypatch,
) -> None:
    _enable_app(monkeypatch)
    admin, membership, directive, proposal = _seed_review_source(db_session)
    login(client, admin.email)
    membership.status = "inactive"
    db_session.commit()

    response = client.get(
        f"/api/v1/ads/directives/{directive.id}/v4/candidate-proposals/"
        f"{proposal.id}/review-observation",
        headers=_headers(membership.id),
    )
    assert response.status_code == 403
    assert response.json()["detail"]["code"] == "forbidden"

```
