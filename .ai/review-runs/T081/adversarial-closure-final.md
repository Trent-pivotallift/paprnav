# T081 adversarial closure review — final

Reviewer: `/root/t081_closure_final`  
Builder/coordinator: `/root`  
Outcome: **PASS FOR CONTROLLED HUMAN CALIBRATION**

No blocker or High finding remains open. This pass inspected the current
closure packet, decision, ledger, Claude critic and sidecar, prior independent
implementation reviews, closure report, working-tree code, tests, callers, and
readers. The packet verified as current against `HEAD`; the ledger has **0
non-terminal blocker/High findings**, with 14 closed findings, one accepted
Medium risk, and two deferred Medium findings that describe the same human
calibration gate.

## Claude disposition challenge

### T081-CC-001 — source-section bounding — **CLOSED**

The first remediation still admitted a non-Part-39 neighbor when the target
footer was OCR-corrupted and the neighbor supplied the first valid FR Doc
footer. I reproduced that failure independently and withheld closure. The
revised `bounded_issue_pages` now rejects any recognizable intervening docket
or document number, CFR-part header, department/agency header, or billing
marker before the candidate footer. Replaying the exact corrupted-footer plus
`NeighborCo model N-1` counterexample now returns no pages and
`source_evidence_status` reports missing evidence. The new Department of
Agriculture/non-Part-39 regression exercises this exact failure mode.

### T081-CC-002 — direct-database actor identity — **ACCEPTED RISK**

The disposition is bounded and credible. Both staging and correction CLIs now
require `--actor-user-id`, resolve an active platform-admin membership, and
persist the actor in product/workflow audit records; staging also records
`proposalStagedByUserId`. The documented model explicitly treats privileged
shell/database access as the authentication boundary and says the supplied ID
is audit attribution, not session proof. Owner, rationale, and revisit
condition are present. This acceptance is valid only while these remain local
direct-database tools; remote job-runner exposure requires signed/session-bound
operator identity.

### T081-CC-003 / T081-DA-10 — human calibration — **DEFERRED**

The five real-document packets are not complete and are not represented as
complete. Deferral does not authorize broad release: the declared outcome is
only readiness for controlled human calibration, pending/source-quarantined
records cannot enter the signed release boundary, and the ledger names a human
owner and a before-broader-release revisit condition. This remains required
work, not closure evidence for real-document calibration.

### T081-CC-004 — packet freshness — **CLOSED**

The decision and current closure packet identify migrations `0021` through
`0024`, state PostgreSQL head `0024`, and include the corrective signed-
materialization migration in reviewed scope. The regenerated closure packet
verified current. Claude's references to nonexistent `T081-DA-11` are an
immutable, non-authoritative critic prose typo; no ledger finding is missing.

## Original DA/DC closure

All original DA/DC blocker and High findings are terminal with concrete
closure evidence. Direct trace and the prior independent implementation passes
cover the exact signed-release service and its catalog/matching/coverage
consumers, tri-state applicability, all-obligation recurrence, component-bound
measurements, field-level citations, retained-byte rehashing, extraction-bound
relational identity, serialized immutable decisions, correction revocation,
and the conservative `0024` repair/downgrade contract. No alternate released
reader or administrative decision path was found that invalidates those
closures. The only original non-terminal finding is the explicitly deferred
Medium human-calibration item above.

## Verification

- Refreshed closure packet currency: **1 passed out of 1**.
- Exact non-Part-39 counterexample replay: **1 passed out of 1**.
- Current targeted issue-boundary suite: **8 passed out of 8**.
- Independent focused AD run before the final added regression: **70 passed out
  of 70**; current packet records the expanded suite at **71 passed out of 71**.
- Independent full backend run before the final added regression: **196 passed
  out of 196**; current packet records the expanded suite at **197 passed out
  of 197**.
- PostgreSQL migration/repair evidence: **11 passed out of 11**.
- PostgreSQL review concurrency evidence: **7 passed out of 7**.
- Committed PostgreSQL correction evidence: **12 passed out of 12**.
- Frontend lint: **0 errors** with one unrelated warning; production build:
  **1 passed out of 1**.
- `git diff --check`: **1 passed out of 1**.

## Not independently re-executed

The final 71-test and 197-test expanded totals were reported in the refreshed
packet after the one added boundary regression; this reviewer independently
executed that exact new regression and the complete 8-test boundary subset.
The Docker/PostgreSQL verifier was not rerun in this final pass because Docker
socket approval was interrupted; the 11/7/12 results are supported by the
existing independent Claude run, prior implementation review, executable
fixtures, and direct inspection. Human calibration, production deployment,
external identity-provider behavior, and remote object-storage durability
remain unverified as stated in `closure.md`.

CLOSURE OUTCOME: **PASS FOR CONTROLLED HUMAN CALIBRATION**
