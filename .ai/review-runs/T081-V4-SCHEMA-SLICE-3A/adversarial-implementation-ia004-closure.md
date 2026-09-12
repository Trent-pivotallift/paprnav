# Targeted implementation closure: IA-004

Reviewer: `/root/v4_s3a_impl_adversary`  
Outcome: **PASS**

The reviewer verified that detail, reconstruction, and list GET paths perform
detection only and contain no commit, flush, event insertion, or repair call.
`projection_state()` is non-mutating. Stale repair is reachable only through
`materialize_applicability()` after application authorization and both database
write-gate checks; both normal materialization and idempotent retry invoke that
gated helper. Caller search found no alternate repair path.

The focused regression snapshots projection-event count across detail,
reconstruction, and list GET and proves it remains unchanged. The coordinator's
focused candidate/API/applicability suite passed 40 out of 40.

The reviewer noted that evidence verification can acquire a row lock, so the
detection docstring was narrowed from claiming no write locks to the exact
guarantee: no row mutation or event append. No residual IA-004 finding remains.
