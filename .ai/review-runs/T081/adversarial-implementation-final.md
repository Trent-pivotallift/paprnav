# T081 adversarial implementation review — final

Reviewer: `/root/t081_implementation_final`  
Builder/coordinator: `/root`  
Outcome: **PASS**

This fresh read-only pass was limited to the two High proof gaps from
`adversarial-implementation-closure-1.md` and the source-indexed review-queue
pagination boundary. The current implementation packet verified as current
against `HEAD`. No blocker or High finding remains in the assigned closure
scope.

## Finding dispositions

### T081-IC-1 — corrective migration cohort proof — **CLOSED**

The current `scripts/verify-t081-postgres-migrations.sh` now creates an isolated
PostgreSQL database at revision 0023 and seeds three distinct absent-origin v3
states before executing 0024:

1. a terminal review with a null `decision_output`;
2. a signed nonempty AMOC envelope; and
3. an empty/partial envelope whose extraction, proposal, and decision differ.

The verifier asserts the entire three-row cohort is reopened, every extraction
is marked `needs_review` with `migration_repair_pending`, empty synthetic
envelopes are removed without removing the nonempty AMOC, and all three
pre-repair decisions are retained as immutable snapshots. It separately checks
the null before-image, the nonempty AMOC before-image, the legitimate empty
before-image, repair actor metadata, and the absence of duplicate repair
snapshots on operational rerun. Direct inspection of migration 0024 confirms
the persisted origin marker excludes an already repaired extraction from a
second repair, while PostgreSQL transactional DDL supplies atomic retry after a
failed attempt. The same verifier retains the downgrade guards and exact 0021
parent-index proof.

Disposition: the missing empty/nonempty/partial cohort, before-image, terminal
reopen, and idempotency proof identified by closure attempt 1 is now present.

### T081-IC-2 — correction transaction proof — **CLOSED**

`backend/app/scripts/verify_ad_correction_workflow.py` now seeds a real approved
v3 directive and all affected derived objects: applicability, requirement,
AMOC, current due state, current match, coverage set, and active coverage
subscription. It invokes the actual correction CLI with `--commit`, then opens
a new session and checks twelve outcomes:

- review reopened and immutable prior-decision snapshot retained;
- extraction and directive revoked;
- applicability, requirements, and AMOC superseded;
- due state and match made non-current;
- coverage moved to `pending_recalculation` with correction provenance;
- `released_signed_extractions` excludes the directive after commit; and
- corrected output remains staged for a new human decision.

Direct inspection of `correct_approved_ad_review.py` confirms these writes and
the audit/workflow events share one SQLAlchemy transaction and are committed
only at the final `db.commit()`. A failure before that boundary rolls the
transaction back; the released-reader assertion occurs from the verifier's
post-commit session.

Disposition: the unseeded due-state, match, coverage, and released-reader proof
gap identified by closure attempt 1 is closed.

## Source-indexed queue pagination — **PASS**

`list_extraction_reviews` paginates the expensive exact verification to only
the selected record(s). Serialization calls `full_text_pages_for_extraction`,
which rehashes the retained PDF bytes, re-parses page text, and rejects cached
page/hash/key mismatches before displaying source or computing `canApprove`.
Aggregate queue counts use cached provenance plus the current source-set input
hash and are explicitly described in code and UI as source-indexed triage and
approval candidates. They do not make an approval or release decision. The
decision endpoint independently performs exact source verification, and the
released reader independently enforces the signed-evidence boundary. The
availability optimization therefore fails closed at every authoritative
boundary.

## Verification

- Review packet currency: **1 passed out of 1**.
- Independent focused AD suite (`test_ad_ingestion.py`, `test_ad_matching.py`,
  `test_ad_recurrence.py`, `test_ad_coverage.py`): **67 passed out of 67**.
- Current PostgreSQL verifier contract: **11 passed out of 11**, including its
  embedded decision-concurrency and committed-correction verifiers. The
  independent Docker rerun was requested but not completed because Docker
  socket approval was interrupted; closure above is based on direct inspection
  of the executable PostgreSQL fixtures/assertions and the existing successful
  run evidence, not on an invented rerun result.

The previously declared incomplete five-record human calibration set remains a
separate Medium human-review deliverable and is not represented as complete by
this implementation PASS.

IMPLEMENTATION OUTCOME: **PASS**
