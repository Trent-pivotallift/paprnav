# Closure report: T081

## Outcome

Implementation is ready for controlled human calibration. The independent
implementation adversary passed after two PostgreSQL proof gaps were closed,
and Claude's subsequent high source-bounding finding is fixed and
regression-covered. No blocker or high finding remains open. Broader AD release
is still gated on completing the five-record human calibration set.

## Invariants verified

- Only exact, evidence-valid, human-signed v3 extractions can reach catalog,
  matching, coverage, requirement, or due-state readers.
- Applicability, requirement, recurrence, and component semantics fail to
  adjudication when a supported proof is absent or ambiguous.
- Retained source bytes, re-derived page text, document/page membership, and
  extraction input identity are reverified at approval and release.
- A missing or mismatched rule footer contributes no citation-eligible issue
  text; a later rule's footer cannot close the target section.
- Correction and migration repair preserve attribution and prior output while
  revoking every derived reader in the same PostgreSQL transaction.
- Concurrent review decisions serialize and append immutable decision history.

## Findings disposition summary

Fourteen findings are closed. T081-CC-002 is an accepted operational trust risk:
the two direct-database tools treat privileged shell/database access as their
authentication boundary, require an active platform-admin ID for attribution,
and cannot themselves prove that ID is the shell operator. T081-DA-10 and
T081-CC-003 defer the same human calibration deliverable; pending or
source-quarantined records cannot publish while it remains incomplete.

## Verification performed

- Target issue-boundary tests: **8 passed out of 8**.
- Focused AD ingestion, matching, recurrence, and coverage tests: **71 passed
  out of 71**.
- Full backend suite: **197 passed out of 197**.
- Isolated PostgreSQL migration/repair contract: **11 passed out of 11**.
- PostgreSQL review concurrency contract: **7 passed out of 7**.
- Committed PostgreSQL correction transaction contract: **12 passed out of
  12**.
- Frontend lint: **0 errors** with one unrelated image warning; the final
  production build passed.
- `bash -n scripts/claude-review.sh` and `git diff --check` passed.
- Independent implementation review: PASS; Claude external critic executed
  after that review and its structured findings are dispositioned in the
  ledger.

## Final scope reviewed

The reviewed scope includes the v3 extraction schema and evidence validators,
relational applicability/requirement/trigger/AMOC materialization, centralized
release gate, matching/coverage/recurrence readers, review and retained-source
APIs, admin AD query/review UI, direct operational scripts, migrations 0021
through 0024, Docker retained-source persistence, PostgreSQL proof scripts,
calibration documentation, and the T081 review artifacts.

## Accepted risks and deferred work

- Direct-database staging/correction tools remain appropriate only for trusted
  operators with privileged shell/database access. Before remote job-runner
  exposure, replace supplied actor attribution with signed operator/session
  identity.
- A platform administrator must complete all five calibration packets and
  expected positive/negative outcomes before broader catalog release.

## Not verified

The five real-document calibration records have not been completed or approved
by a human. Production deployment, external identity-provider behavior, and
remote object-storage durability were not exercised in this local loop.
