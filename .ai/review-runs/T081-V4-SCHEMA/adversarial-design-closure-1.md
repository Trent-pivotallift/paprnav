# T081-V4-SCHEMA adversarial design closure 1

Reviewer: `/root/v4_schema_adversary`  
Builder: `/root/v4_schema_builder`  
Stage: `design`  
Outcome: **FAIL**

Packet verification:

- Packet SHA-256: `f29c641b94dcbb111c879e8a518994967d169d444f8aa410b36f004d68da73cd`
- Scope fingerprint: `aa9311d32c0303ab45adbffec4933dd24097d6a806b950dc9126b76885a1807c`
- `scripts/verify-review-packet.py`: 1 passed out of 1; packet current
- Hash-bound review inputs: 9 passed out of 9

## Open blocker

### T081-V4-DA-006 — source-complete calibration is incomplete

- **Violated invariant:** Real source-complete calibration proves every
  regulatory structure claimed by the design.
- **Exact evidence:**
  `.ai/AD_EXTRACTION_DOMAIN_CONTRACT.md:384-400` requires representative cases
  for incorporated service information and actual aircraft-specific approved
  AMOC use. `.ai/review-runs/T081-V4-SCHEMA/calibration/INDEX.md:56-61`
  explicitly states that the five packets contain neither an actual
  aircraft-specific approved AMOC use nor a retained incorporated service
  bulletin. `.ai/review-runs/T081-V4-SCHEMA/decision.md:401-404` records the
  same residual gaps and prohibits treating them as passed evidence.
- **Impact:** The design's aircraft-specific AMOC-use and incorporated-service-
  bulletin behavior is not disproved against a real, source-complete example.
  Implementing those slices would repeat the exact source/structured-data
  conflation this redesign is intended to prevent.
- **Required closure:** Add a source-complete aircraft-specific AMOC-use packet
  and a retained incorporated-service-bulletin packet, each with authoritative
  bytes, expected applicability/obligation/timing/evidence results, supported
  queries, and positive and negative cases. Alternatively, the domain owner
  may explicitly narrow the design gate and the decision packet must disable
  both uncalibrated slices; they would then require their own later design and
  calibration gates before implementation. The current full V4 objective has
  not recorded that narrower disposition, so it cannot be inferred here.

Disposition: **OPEN BLOCKER**. The full design gate fails.

## Closed findings

### T081-V4-DA-001 — immutable packet binding

- **Invariant:** The gate reviews a complete immutable packet binding every
  proposed schema artifact.
- **Exact evidence:** The final manifest binds the decision, finding ledger,
  proposal, calibration index, and five calibration packets as nine review
  inputs; the verifier accepted the final packet and fingerprint.
- **Impact removed:** A proposal or calibration change can no longer remain
  hidden behind a previously recorded current packet.
- **Required closure satisfied:** Rebuilt hash-bound packet and independent
  freshness verification.

Disposition: **CLOSED**.

### T081-V4-DA-002 — complete applicability and branch algebra

- **Invariant:** Applicability and obligation branches fail closed under true,
  false, and unknown inputs.
- **Exact evidence:**
  `.ai/review-runs/T081-V4-SCHEMA/codex-schema-proposal.md:387-399` defines the
  recursive typed expression grammar, including `ScopeRef`; the following
  truth-table and evaluator sections define Kleene T/F/U behavior, cycle and
  size limits, requirement activation, alternatives, traces, and versioning.
- **Impact removed:** Nested conditions and reusable scopes no longer require
  implicit array semantics that could broaden or narrow obligations.
- **Required closure satisfied:** Complete typed algebra, relational mapping,
  and positive/false/unknown calibration expectations.

Disposition: **CLOSED**.

### T081-V4-DA-003 — evidence-fragment integrity

- **Invariant:** Every signed source clause derives mechanically from immutable
  retained bytes, including negative assertions.
- **Exact evidence:** The proposal's evidence model binds immutable retained
  source hashes to page renditions, page-text/parser versions, coordinates or
  offsets, server-derived selections, append-only lifecycle events, and
  evidence-bearing `not_applicable` assertions.
- **Impact removed:** Supplied or stale parser text cannot masquerade as a
  source-verified fragment, and negative assertions cannot be evidence-free.
- **Required closure satisfied:** Hash-bound page/text lineage and immutable
  evidence lifecycle.

Disposition: **CLOSED**.

### T081-V4-DA-004 — canonical/PostgreSQL lossless mapping

- **Invariant:** Canonical V4 semantics and evidence round-trip losslessly
  through constrained PostgreSQL rows.
- **Exact evidence:** The proposal defines state-bearing field assertions,
  temporal/STC/series/identifier/expression tables, field-level evidence links,
  CHECK/FK/unique constraints, and canonical-to-row-to-canonical equality tests.
- **Impact removed:** SQL `NULL` cannot regain unknown semantics and critical
  match values are not relegated to opaque JSON.
- **Required closure satisfied:** Typed relational mapping, constraints,
  round-trip tests, and direct database-negative tests.

Disposition: **CLOSED**.

### T081-V4-DA-005 — reviewed unknown publication semantics

- **Invariant:** Every unknown has an explicit publication and automation
  consequence.
- **Exact evidence:**
  `.ai/AD_EXTRACTION_DOMAIN_CONTRACT.md:435-444` records the domain-owner
  `candidate_only` decision. The proposal limits that state to administrator
  and aircraft-specific discovery as **Uncertain—human determination required**
  and prohibits released-catalog, affirmative-applicability, compliance,
  termination-credit, next-due, and coverage effects.
- **Impact removed:** Reviewed uncertainty cannot be mistaken for an
  automation-safe released directive.
- **Required closure satisfied:** Domain-owner decision plus fail-closed
  eligibility and node-level automation gates.

Disposition: **CLOSED**.

### T081-V4-DA-007 — correction, supersession, and rollback lifecycle

- **Invariant:** Correction, supersession, invalidation, selection, and rollback
  are immutable auditable transitions.
- **Exact evidence:** The proposal defines append-only lifecycle, relation, and
  invalidation events; deterministic folds; compare-and-swap current selection;
  one-current-generation constraints; correction quarantine; no corrected-V4
  fallback to V3; and failure-injection tests.
- **Impact removed:** Stale or superseded decisions cannot be silently
  resurrected by rollback, retry, or concurrency.
- **Required closure satisfied:** Event semantics, transactional selection,
  rollback restrictions, and failure rehearsal.

Disposition: **CLOSED**.

### T081-V4-DA-008 — attributable authorization and signoff

- **Invariant:** Every signoff preserves the exact membership or aircraft
  assignment that authorized it.
- **Exact evidence:** The proposal binds signoffs to immutable membership and
  aircraft-assignment snapshots, governed scope and policy version, prohibits
  self-review, appends corrections, and requires server-side authorization and
  concurrency-negative tests. The decision packet records one independent
  authorized signer as the domain policy.
- **Impact removed:** A mutable role label can no longer serve as the sole audit
  evidence for a regulatory decision.
- **Required closure satisfied:** Authority snapshots, scope rules, independent
  signoff, append-only correction, and API enforcement tests.

Disposition: **CLOSED**.

## Verification totals

- Finding closures: **7 passed out of 8**.
- Retained-file existence and SHA-256: **6 passed out of 6**.
- PDF page-count and rule-identity inspection: **6 passed out of 6**.
- Gold-packet evidence-key resolution: **5 passed out of 5**.
- Required domain-pattern coverage: **17 passed out of 19**.
- Design gate: **0 passed out of 1**.

## Decision ownership

- **Domain-owner decisions, resolved:** DA-005 candidate-only exposure; DA-008
  independent-signer policy and customer-facing consequences.
- **Engineering choices, resolved subject to implementation review:** DA-001,
  DA-002, DA-003, DA-004, DA-007, and the enforcement portion of DA-008.
- **Evidence gap, unresolved:** DA-006. Adding representative evidence is an
  engineering/calibration task. Narrowing the authorized V4 objective instead
  is a domain-owner decision and must be explicit.

**DESIGN OUTCOME: FAIL — DA-006 remains an open blocker.**
