# T081 V4 Slice 3B — Initial Adversarial Design Review

Verdict: **FAIL**

Reviewed packet SHA-256:
`1793c6eadd066b129c383d7a6b19fdab55542ae58b75945ce4a4dcc279afd917`

Runtime reviewer identity: `/root/v4_s3b_design_adversary`

## B-001 — Blocker: the normative mapping is not complete enough to serve as the claimed cross-language contract

Violated invariants: 3–6, 25–29, 33, plus the packet’s requirement for
deterministic identities and exact reconstruction.

Evidence:

- The common formula in `normative-mapping-matrix.md:29-36` leaves each
  relationship row’s `identity` object undefined. Q4, Q9, Q10, G2, correction
  bindings, requests, and events say only “deterministic” or “exact.”
- E1–E7 at `normative-mapping-matrix.md:157-170` do not define exact
  context-root parent ordinals. Activation, branch-condition, and recurrence-
  condition roots are described collectively as having a Q1/Q5/R1 parent and
  an “operand ordinal,” although roots are not operands and recurrence already
  gives its timing child ordinal 0.
- P1–P4 at `normative-mapping-matrix.md:233-245` do not provide closed
  canonical envelope shapes, exact hash/ID preimages, cause-column unions, or a
  count-column inventory.
- `decision.md:241-243` says immutable projection counts cover every child
  table, while `decision.md:497-501` explicitly permits later append-only stale
  events. Additional materialization requests can also accumulate against an
  existing projection. Freezing counts for these mutable audit children in
  immutable projection bytes is impossible; excluding them contradicts
  “every child table.”
- “The latest generation” in the matrix is not associated with a defined
  projection generation or selection rule.

Impact: Python, generated SQL, hand-written SQL, and read verification can each
implement different identities, ordinals, counts, and event payloads while
claiming conformance. Projection hashing is internally impossible if append-
only audit children are counted. Exact direct-SQL validation cannot be reviewed
from this packet.

Required closure:

- Define every row’s identity subobject and domain, including all edges and
  references.
- Define exact parent and ordinal rules for all three expression roots and
  descendants.
- Enumerate immutable structural count columns; explicitly exclude requests/
  events from frozen counts and validate their append-only chains separately.
- Provide closed projection, request, materialized-event, and stale-event
  payload schemas and hash/ID preimages.
- Define stale-event cause unions, cardinality, predecessor rules, and the
  meaning of “generation.”
- Update positive and corruption vectors to exercise those exact contracts.

## H-001 — High: the proposed correction-binding hash contract contradicts committed Slice 3A

Violated invariants: 23–25 and 36.

Evidence:

- `decision.md:445-450` says the frozen Slice-3A binding preimage includes
  `bindingSlice`, `generation`, projection ID, and semantic node ID.
- Committed construction at
  `backend/app/services/ad_v4_applicability.py:2973-2974` uses only
  `{"refId": ref_id, "semanticId": semantic.id}`.
- Committed PostgreSQL verification at migration 0027 lines 2759–2762 uses the
  same two-field identity under the Slice-3A applicability row domain.
- The new matrix’s global claim that “all row hashes” use the obligation row
  domain also conflicts with retaining existing Slice-3A binding hashes
  unchanged.

Impact: following the design literally either restamps immutable 3A identities/
hashes, makes existing rows fail the amended validator, or produces Python/SQL
disagreement.

Required closure: record the exact existing 3A domain and
`{refId, semanticId}` preimage as immutable. Separately define the exact 3B
binding ID/hash domain and preimage. Prove existing binding IDs/hashes are byte-
identical across upgrade, materialization, failed downgrade, and re-upgrade.

## H-002 — High: the global lock order cannot be implemented in the declared scope and is internally contradictory

Violated invariants: 31–34 and 37.

Evidence:

- `decision.md:176-178` requires feature gates in lexical order.
- Existing Slice-3A code at
  `backend/app/services/ad_v4_applicability.py:101-104` locks
  `validator2_write_enabled` before `materializer3a_enabled`, the reverse of
  lexical order.
- `ad_v4_applicability.py` is absent from the permitted implementation scope.
- Invariant 32 says all gates are rechecked while holding the Slice-3A
  projection lock, but invariant 34 and the operation list place gate locks
  before that projection lock.
- The purported global order also omits actor/membership and idempotency
  advisory locks, which current Slice 3A acquires before the proposal.

Impact: concurrent 3A and 3B materializations on different proposals can
acquire shared gate rows in opposite order, producing PostgreSQL deadlock
victims and possible 500 responses. There is no single reviewable order for
writers, gate administration, and downgrade.

Required closure: define one complete order including actor/membership,
advisory locks, proposal, every gate, parent 3A projection, evidence fragments/
bindings, corrections, and 3B projection. Either amend Slice 3A to that order
and add its service to scope, or make 3B/downgrade follow the established order.
Add forced interleaving tests for 3A/3B, gate disable, and downgrade, asserting
convergence or controlled conflict with no 500.

## H-003 — High: decimal admissibility and pre-cast failure behavior remain unresolved

Violated invariants: 18, 25–27, and 29.

Evidence:

- The checked-in timing interval schema has an unbounded digit pattern.
- Normal API creation separately applies `MAX_STRING_LENGTH = 16_384`, but
  `verified_candidate()` re-runs schema validation only; direct-SQL parent
  corruption is expressly in scope.
- PostgreSQL unconstrained `numeric` is finite.
- `decision.md` leaves the resolution as a design-review question, while the
  matrix merely requires an exact cast.
- No rule guarantees length/range checks occur before a cast in PostgreSQL or
  Python read verification.

Impact: a forged/self-consistently restamped parent can drive PostgreSQL numeric
overflow or an unhandled read/materialization exception instead of the required
controlled failure. The design does not establish which validator-2 candidates
are materializable.

Required closure: freeze an exact supported decimal bound and stable failure
code before any numeric cast. The practical option is to mirror the existing
16,384-character ingestion bound in Python and PostgreSQL, prove its integer/
fractional extremes fit deployed PostgreSQL `numeric`, and reject forged out-
of-bound parents before conversion. Otherwise remove the numeric projection or
introduce a newly reviewed validator version. Add max, max+1, integer-heavy,
fractional-heavy, and corrupted-parent tests.

## H-004 — High: mixed-version and application rollback compatibility is incorrectly claimed

Violated invariants: 23, 24, 36, and migration/rollback safety.

Evidence:

- The base Slice-3A reader at
  `backend/app/services/ad_v4_applicability.py:2671-2691` requires zero semantic
  bindings for every `owner_slice='slice_3b'` reference.
- Slice 3B necessarily appends one such binding.
- `decision.md` claims existing 3A routes/reconstruction remain compatible and
  says application rollback leaves 3A audit available.
- A binary rollback to `9ad410b` after any 3B binding exists makes that reader
  return integrity 409 for an otherwise valid 3A projection.

Impact: rolling deployment or rollback can take existing 3A audit reads out of
service even though physical downgrade correctly refuses occupied data.

Required closure: state the exact compatibility boundary. Keep
`materializer3b_enabled=false` until every replica is 0028-aware; test old
binaries against upgraded-but-empty schema; and declare rollback to `9ad410b`
prohibited after the first 3B binding. “Application rollback” must mean
disabling routes on an 0028-aware binary unless a backward-compatible legacy
reader is implemented.

## M-001 — Medium: verified GETs lack a defined consistency point

Violated invariants: 2, 29, and 30.

Evidence:

- The design requires live-evidence, parent-3A, correction, and typed-graph
  verification through many queries but specifies neither repeatable-read
  isolation nor a compatible read-lock set.
- Current live-evidence code locks evidence-binding rows but reads lifecycle
  events separately; lifecycle insertion locks the fragment row, not the
  binding row.
- The test strategy includes concurrent writes and downgrade, but not GET
  versus lifecycle invalidation, correcting/replacing submission, or incoming
  supersession.

Impact: one response may combine observations from different committed states
or complete after evidence invalidation without a defined snapshot boundary.

Required closure: define verified reads as one repeatable-read snapshot or
specify a non-mutating compatible lock protocol over every mutable cause. Add
forced interleaving tests for detail, reconstruction, and list against evidence
lifecycle, candidate relationship, and parent-3A stale transitions.

No implementation should begin until B-001 and the four high findings are
dispositioned and independently re-reviewed.
