# Closure report: T081-V4-SCHEMA

## Outcome

**READY FOR SLICE-1 CLOSURE REVIEW**

This report requests an independent closure review of implementation slice 1
only. It does not declare closure PASS, approve a later V4 slice, or declare the
T081 V4 program complete. The independent implementation reviewer recorded
PASS for the bounded slice after closing all eight implementation findings.

## Invariants verified

- Retained page renditions are immutable server-derived PNG bytes bound to the
  retained document, authoritative source hash, directive/publication identity,
  and exact page number. A newly written or reused object is read back and its
  hash, size, PNG structure, and dimensions are verified before admission.
- Bounded page-text versions are immutable and bind parser name/version, text
  hash, retained source identity, rendition, and exact page. A fragment cannot
  copy or forge different parser provenance.
- An exact clause fragment is stored once and referenced by ID/hash. Its
  canonical identity includes the authoritative selected text, offsets,
  parser provenance, and complete transitive evidence chain. PostgreSQL rejects
  reversed, empty, truncated, overlong, wrong-page, wrong-document, stale-hash,
  and cross-directive evidence.
- Slice 1 is deliberately single-page. PostgreSQL and the service require
  `page_end = page_start`; a multi-page claim cannot be represented by one text
  version.
- Fragment lifecycle is append-only and hash-bound. Each admitted fragment has
  exactly one canonical admission root; subsequent events require the same
  fragment, the exact predecessor and sequence, and a valid event hash.
  Concurrent successor attempts leave one canonical transition and no fork.
- Fragment admission is atomic with its admitted lifecycle root and serialized
  on the attributable source document. Concurrent identical admissions are
  idempotent and do not create duplicate rendition, text, fragment, or admission
  rows.
- Page materialization and fragment admission are explicit platform-admin-only
  mutations. GET is side-effect-free and returns 404 when materialization has
  not occurred. Owner and maintenance-shop identities cannot read the private
  materialization endpoint or mutate global evidence.
- Source-document metadata exposes explicit relevant page numbers separately
  from a contiguous display range, and retained-PDF navigation opens the
  verified document at a relevant page.
- Migration `20260830_0025` is additive. Its downgrade takes `ACCESS EXCLUSIVE`
  locks on all four evidence tables before checking emptiness, refuses an
  occupied downgrade, and permits empty downgrade/re-upgrade.
- Existing V3 proposal, review, publication, materialization, and released-read
  behavior remains unchanged. Slice 1 cannot make a candidate actionable or
  released.

## Findings disposition summary

- Design findings: **8 closed out of 8** (`T081-V4-DA-001` through
  `T081-V4-DA-008`) under the independent design PASS.
- Slice-1 implementation findings: **8 closed out of 8**
  (`T081-V4-IA-001` through `T081-V4-IA-008`) under the independent
  implementation closure-3 PASS.
- Closure finding `T081-V4-CA-001`: **1 closed out of 1** after independent
  verification.
- Closure finding `T081-V4-CA-002`: **1 fixed pending independent
  verification out of 1**. The builder has not closed it or recorded the
  required fresh re-attestation.
- Remaining open or unremediated blocker/high/medium findings within the
  declared slice-1 closure scope: **0**.
- Accepted-risk findings: **0**. Deferred work is listed below and is outside
  this bounded slice; it is not silently accepted as implemented behavior.

## Verification performed

The recorded verification counts are kept by suite because some focused runs
cover the same invariants and must not be added together as unique test cases.

- Backend focused regression/API suite: **58 passed out of 58**.
- Independent reviewer focused API/evidence suite: **5 passed out of 5**.
- Coordinator fresh-database PostgreSQL closure run: **2 passed out of 2** in
  1.62 seconds.
- Builder fresh-database PostgreSQL closure-3 run: **2 passed out of 2** in
  1.71 seconds.
- Frontend production build/type check: **1 passed out of 1**.
- Migration rehearsal legs: **4 passed out of 4**: fresh upgrade, occupied
  concurrent downgrade refusal, empty downgrade, and re-upgrade.
- Review-packet freshness before the implementation PASS: **1 passed out of
  1**.
- Review-infrastructure regression suite after CA-002 remediation: **10 passed
  out of 10**. In addition to the CA-001 fingerprint cases, it proves the
  supported closed-state re-attestation success path, append-only history,
  unchanged closed state, final-validator acceptance, and rejection of stale
  packets, missing prior closure PASS, non-closed phase, wrong stage,
  self-review, and reused artifacts. It also proves a current closure FAIL
  appends immutable history and reopens `implementation_reviewed` while stale
  or reused-artifact FAIL attempts leave state closed.
- Python compilation for the canonical fingerprint helper, its four consumers,
  and the regression test: **1 passed out of 1**.
- Temporary database cleanup: **0** databases matching
  `paprnav_t081_v4_%` remained after coordinator inspection; `paprnav_db` was
  not migrated or mutated.

The PostgreSQL two-test suite contains the direct-SQL negative cases and
two-session races; **2/2** is its test-case count, not its assertion count. It
specifically includes wrong/cross-fragment predecessor rejection and the
concurrent successor proof: one commit, one rejection, one stored successor,
and no valid fork.

## Final scope reviewed

The final independent implementation review covered the actual working tree
for this slice, including:

- Alembic revision `20260830_0025`, ORM models, database constraints, composite
  keys/FKs, immutable triggers, fragment/lifecycle validation, and guarded
  downgrade behavior;
- retained-source materialization and fragment-admission services;
- source-document schemas and administrator API authorization;
- current admin review-page relevant-page metadata and retained-PDF navigation;
- focused backend/API tests, direct PostgreSQL integrity/concurrency tests,
  migration harness head update, the bounded slice verifier, and frontend build;
- the decision, finding ledger, V4 schema proposal, slice-1 implementation
  evidence, and the implementation closure-3 review artifact.
- the CA-001 review-infrastructure remediation: the shared fingerprint helper,
  packet builder, packet verifier, final review-run validator, and focused
  regression test.
- the CA-002 review-infrastructure remediation: the explicit closure-only PASS
  or FAIL re-attestation contract in the review recorder and its
  positive/negative regression coverage.

This is the final reviewed scope for **slice 1**, not for the complete V4
proposal.

## Accepted risks and deferred work

No finding is disposed as accepted risk. The following work is explicitly
deferred to separately designed, implemented, and reviewed V4 slices:

- cross-page/table child selections and coordinate maps;
- reviewed OCR/rendition support for scanned or native-text-empty pages, which
  currently fail closed;
- deterministic garbage collection for an unreferenced content-addressed PNG
  left by a failed database transaction (it cannot become admitted evidence
  without the validated database chain and lifecycle root);
- V4 canonical JSON and normalized applicability, branch, requirement,
  interval, evidence-reference, STC, service-bulletin, and AMOC persistence;
- reviewer menu/forms, publication/catalog cutover, V3 migration and rollback,
  corrected-V4 fallback policy, aircraft configuration matching, compliance
  evidence, and due-state calculation;
- the authorized administrator ingestion workflow for supporting service
  bulletins, STCs, and aircraft-specific AMOC-use evidence.

## Not verified

- No later V4 slice or end-to-end V4 catalog/reviewer workflow is verified by
  this closure request.
- The broader legacy `scripts/verify-t081-postgres-migrations.sh` 14-leg wrapper
  was **not completed as one invocation** and is not used as slice-1 closure
  evidence. The interrupted run lasted approximately 545 seconds. The wrapper
  lacks an outer/per-command timeout, hides guarded-downgrade output, and calls
  legacy concurrency scripts whose non-daemon workers can remain alive after
  timed joins. The narrow missing PostgreSQL proofs were instead executed on
  fresh isolated databases and passed with the counts above.
- The full `scripts/verify-t081-v4-slice1-postgres.py` orchestration was not
  completed as one desktop invocation after the sandbox interruption. Its
  constituent current migration and PostgreSQL proofs were run directly via
  approved Docker Compose with isolated temporary databases. This report does
  not upgrade that fact into a claim about the wrapper itself.
- Closure PASS and overall review-run validation are not yet verified. They
  require a separate closure reviewer and a new immutable closure-review
  artifact.
- `T081-V4-CA-002` is fixed pending verification, not closed. The supported
  re-attestation path has not been exercised against this run by an independent
  reviewer. The builder must not create that attestation.

The state is `closed` from the prior closure PASS. Because closing CA-001
changed a hash-bound input after that PASS, the current run still needs a fresh
independent closure re-attestation. The supported `--reattest` contract appends
that new immutable closure result against a newly current packet. PASS leaves
state `closed`; FAIL reopens `implementation_reviewed`. It cannot be used for a
design review, implementation review, self-review, stale packet, or reused
artifact. The builder has not invoked it.
