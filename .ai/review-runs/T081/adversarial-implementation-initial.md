# T081 adversarial implementation review — initial

Reviewer: `/root/t081_implementation_adversary`

Outcome: **FAIL**

The implementation packet was verified current with
`scripts/verify-review-packet.py --task T081 --stage implementation --base HEAD`.
The review inspected staged, unstaged, and untracked scope plus the release,
catalog, coverage, matching, recurrence, correction, migration, retained-source,
API serialization, frontend, calibration, and test consumers. The following
findings remain.

## T081-IA-1 — Blocker — approved-review correction cannot execute

- **Invariant:** A correction preserves the prior signed decision, immediately
  revokes every derived row and reader, and reopens the directive atomically
  (invariant 10; T081-DA-6).
- **Evidence:**
  `backend/app/scripts/correct_approved_ad_review.py:205-212` builds
  `update(ADAMOCProvision).values(status="superseded",
  review_status="needs_adjudication")`, but `ADAMOCProvision` has no
  `review_status` column (`backend/app/models/core.py:746-765`). Compiling the
  statement with SQLAlchemy's PostgreSQL dialect produced
  `sqlalchemy.exc.CompileError: Unconsumed column names: review_status`.
- **Counterexample / impact:** Any approved directive that reaches this update
  aborts the correction transaction. Operators cannot revoke a bad signed
  extraction through the documented correction workflow, so stale regulatory
  state remains authoritative until a code change is deployed.
- **Required closure:** Remove the nonexistent assignment (or add a separately
  designed AMOC review-state column), then execute the committed correction
  path in a PostgreSQL integration test. Assert review reopening, immutable
  prior-decision retention, applicability/requirement/AMOC supersession, due
  state and match invalidation, coverage quarantine, and released-reader
  exclusion in the same transaction.

## T081-IA-2 — Blocker — matching still drops obligations across applicable component/group contexts

- **Invariant:** Every current signed v3 obligation is replayed and exposed per
  applicable obligation/component; compatibility summaries never select which
  obligations survive (invariant 6; T081-DA-3).
- **Evidence:** `select_applicable_component()` returns only one
  `(InstalledComponent, ADTargetApplicability)` tuple
  (`backend/app/services/ad_matching.py:425-448`). `match_aircraft_ads()` calls
  it once and creates one result for that tuple
  (`backend/app/services/ad_matching.py:86-121`).
  `requirements_for_applicability()` then deliberately limits replay to the
  selected applicability row (`backend/app/services/ad_recurrence.py:759-784`).
  The added multiple-obligation test covers two requirements on one selected
  applicability only (`backend/tests/test_ad_recurrence.py:186-243`); it does
  not cover two applicable groups or components.
- **Counterexample / impact:** A directive with an engine applicability group
  and a propeller applicability group, each with its own requirement, on an
  aircraft containing both components produces due state for whichever tuple
  wins the single `best` score. The other signed obligation has no match or due
  state.
- **Required closure:** Enumerate all applicable component/applicability
  contexts and persist an independently identifiable match (or an equivalent
  aggregate that retains component identity) for every requirement. Add a
  PostgreSQL/API regression with at least two applicable component groups and
  prove every requirement/due state is returned and replay-idempotent.

## T081-IA-3 — Blocker — API rebuild disconnects the retained evidence store

- **Invariant:** Retained bytes and their recorded identities remain available
  for source comparison, approval, release, correction, and audit; missing
  evidence fails closed without making the review workflow unrecoverable
  (invariants 1, 2, 9, and the retained-evidence trust boundary).
- **Evidence:** `backend/.dockerignore` excludes `.data/`.
  `backend/docker-compose.yml` sets
  `PAPRNAV_LOCAL_STORAGE_PATH=/app/.data` for `api` but mounts no volume at that
  path. The host has 176 retained AD source files (about 1.2 GB), yet a live
  `docker compose up -d --build api` resulted in the admin review API reporting
  **0 source-verified out of 50 and 50 source-quarantined**.
- **Counterexample / impact:** Rebuilding or replacing the API container leaves
  PostgreSQL source-document records pointing at bytes the API cannot read.
  Every review, PDF download, approval, and release is blocked. This is safely
  quarantined, but it makes the claimed calibration/review workflow impossible
  and loses runtime access to retained audit evidence.
- **Required closure:** Give the API an explicit persistent retained-source
  mount (for local compose, normally a validated bind mount from the existing
  host `.data`, or a named volume plus a controlled import), document backup and
  recovery, and add a rebuild/restart smoke test that verifies recorded hashes
  and review counts remain stable. Do not bake the 1.2 GB corpus into an image
  layer.

## T081-IA-4 — High — retained-content endpoint verifies a different read from the bytes it serves

- **Invariant:** The exact bytes shown or downloaded as official source must
  match the retained document's SHA-256 and size (invariants 1, 2, and 9;
  T081-DA-9).
- **Evidence:** The content endpoint first assigns `payload =
  read_stored_file_bytes(...)`, then calls `retained_document_bytes_match()`,
  which independently reads the object a second time, and finally returns the
  first `payload` (`backend/app/api/routes/ads.py:120-137` and
  `backend/app/services/ad_extraction.py:1336-1348`).
- **Counterexample / impact:** If mutable local/object storage returns tampered
  bytes on the first read and recorded bytes on the second, the endpoint returns
  the tampered first payload after the second read passes. The administrator
  can therefore review a document different from the bytes that passed the
  integrity check.
- **Required closure:** Hash and size-check the exact payload already read and
  return only that verified buffer (or use an immutable object version). Add an
  alternating-read regression proving the first payload cannot be served when
  it does not match.

## T081-IA-5 — High — mandatory applicability and concurrency proof remains absent

- **Invariant:** Supported applicability is correct at positive, negative, and
  uncertainty boundaries, and concurrent human decisions serialize to one
  immutable attributed transition (invariants 3, 4, 7, and T081-DA-1/DA-7).
- **Evidence:** The new applicability test exercises serial ranges,
  exclusions, missing serials, and an incomparable range only
  (`backend/tests/test_ad_matching.py:41-58`). Repository tests do not exercise
  `evaluate_component_applicability()` for model expressions, equipment
  predicates, or general conditions. The decision endpoint now uses
  `with_for_update()` and appends history
  (`backend/app/api/routes/ads.py:552-688`), but no test races two database
  sessions or proves that exactly one decision succeeds and both attempted
  actors remain auditable.
- **Counterexample / impact:** The implementation is plausible for these
  branches, but the explicit closure evidence required by T081-DA-1 and
  T081-DA-7 is missing. Regressions in fail-closed predicates or transaction
  serialization would be undetected.
- **Required closure:** Add negative model-expression, equipment-condition, and
  general-condition tests through the full matcher, plus a PostgreSQL
  two-session decision race asserting one terminal transition and immutable
  attribution.

## T081-IA-6 — High — migration safety claims have no executable PostgreSQL proof

- **Invariant:** Upgrade, repair rerun, and each downgrade boundary are atomic,
  schema-faithful, and never invent or erase regulatory meaning (invariant 9;
  T081-DA-4 and T081-DC-1/DC-2).
- **Evidence:** Migrations 0021-0024 contain new preflights and repair SQL, but
  no backend test executes the revision chain, verifies the exact 0022-to-0021
  five-column constraint, exercises zero-data downgrade, proves preflight
  failure occurs before DDL with v3 data, or tests 0024's ambiguous cohort,
  legitimate empty/nonempty AMOC payloads, and idempotent rerun. The current
  test references to `source_extraction_id` and `amocEnvelopeOrigin` are model
  or fixture tests, not Alembic transition tests.
- **Counterexample / impact:** A PostgreSQL-only cast, constraint, transaction,
  partial-state, or downgrade defect can ship despite the design's strongest
  data-preservation claims. These were explicit required-closure items, not
  optional coverage.
- **Required closure:** Run isolated PostgreSQL migration tests for
  0020→0024, 0024→0023 when empty, 0022→0021, and 0021→0020; assert schema
  equality at each parent, atomic guarded failure with v3/dependent rows, exact
  cohort snapshots/payloads/attribution, no surviving ambiguous approval, and
  idempotent retry behavior.

## T081-IA-7 — Medium — calibration is still requirement-only, not complete v3 proof

- **Invariant:** Calibration records exercise complete applicability,
  requirement, AMOC, correction, release, and negative/adjudication behavior
  (T081-DA-10).
- **Evidence:** All five
  `.ai/ad-calibration/*.requirements.json` files are top-level arrays. Their
  README explicitly calls them retained v2 requirement drafts that cannot
  publish by themselves and says complete `applicabilityGroups` and group keys
  still must be created in the GUI.
- **Counterexample / impact:** The calibration set cannot be validated against
  `ad_extraction_v3`, cannot prove relational materialization, and contains no
  machine-checkable expected positive/negative aircraft/component outcomes.
- **Required closure:** Replace or supplement all five drafts with complete,
  cited v3 packets and machine-checkable expected positive, negative, and
  adjudication outcomes, then run them through schema/evidence validation,
  materialization, release, matching, correction, and replay checks.

## Verification note

Direct Python compilation of the changed modules succeeded. An attempted
containerized targeted test run did not start because the existing container's
pytest import path could not resolve `app`; no passing test claim is made from
that attempt. This does not affect the direct counterexamples above. The gate
cannot pass while the three blockers remain.
