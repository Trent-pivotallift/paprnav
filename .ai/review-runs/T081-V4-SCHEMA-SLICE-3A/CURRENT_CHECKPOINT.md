# T081 V4 Slice 3A Current Checkpoint

Date: 2026-09-10 (strategy reset during IA-001 implementation)  
Repository: `/Users/hostiletakeover/Projects/paprnav`  
Branch: `codex/ad-source-catalog-proof`  
Committed base: `28f6be0 feat: add immutable AD V4 candidate foundation`

## Current outcome

Slice 3A is fully implemented in the unstaged working tree and has passed the
holistic independent implementation review. IA-001 is closed, all 29 recorded
findings are closed, and the run is in `implementation_reviewed`. It is not yet
ready for staging or commit because the independent closure review and review-
run validation remain outstanding.

The active review run is:

```text
.ai/review-runs/T081-V4-SCHEMA-SLICE-3A
```

The review phase is `implementation_reviewed`.

## Completed review gates

- The Codex design adversary closed **10 findings out of 10**.
- Claude returned three additional findings: two medium and one low.
- All Claude findings were entered into the durable ledger and independently
  verified by the Codex adversary.
- The combined design ledger is **13 closed out of 13**.
- The authoritative design PASS is recorded in `reviews.json`; the run was
  advanced from `design_reviewed` to `implementation` before product edits.
- The final design/external-critic fingerprint before implementation was
  `838675669b7b863ed798cbbe2db29d3fd4a653ee172a0c1bd6c482550f09a5cc`.

The design PASS does not certify the current implementation. The current
external-critic packet predates the product changes and is expected to be stale.

## Approved Slice 3A boundary

Slice 3A creates candidate-only normalized applicability projections:

- validator/canonicalizer v1 and v2 dispatch without rewriting v1 candidates;
- default-off validator-v2 writer and Slice-3A materializer/read gates;
- exact active platform-admin membership authorization;
- immutable candidate-bound materialization requests and events;
- shared proposal-scoped authoritative-correction foundations;
- semantic nodes and evidence links;
- source-faithful values and explicitly unreviewed identity mappings;
- product roles/scopes, model values or unevaluated series expressions;
- serial and part-number scopes;
- conditions, three-valued expressions, applicability rules, and
  noncontrolling search hints;
- deterministic materialization and exact applicability-subtree reconstruction;
- bounded platform-admin materialize/list/detail/reconstruction endpoints; and
- inline/opportunistic deterministic stale repair within existing authorized
  service transactions.

This slice must not add human approval, publication, reviewer GUI, released
catalog reads, aircraft matching, coverage, compliance, due-state calculation,
V3 mutation, aircraft identity migration, provider writers, CLI writers, cron,
or background workers.

## Partial implementation on disk

Tracked files modified:

```text
backend/app/api/routes/ads.py
backend/app/core/config.py
backend/app/models/core.py
backend/app/schemas/ads.py
backend/app/services/ad_v4_candidates.py
```

New product/test files:

```text
backend/app/db/migrations/versions/20260907_0027_add_ad_v4_applicability.py
backend/app/services/ad_v4_applicability.py
backend/tests/test_ad_v4_applicability.py
backend/tests/test_ad_v4_applicability_calibration.py
backend/tests/test_ad_v4_applicability_postgres.py
```

The new review-run directory is also untracked. Nothing is staged and no Slice
3A commit exists.

## Verification credited at this checkpoint

On 2026-09-07, after the interruption:

- Focused Slice-3A local suite: **10 passed out of 10** in 2.02 seconds.
- Combined candidate/API/applicability host suite: **40 passed out of 40** in
  4.98 seconds.
- New Slice-3A test collection: **24 tests collected** across applicability,
  calibration, and PostgreSQL files.
- Python compilation of the new service, migration, and three new test files:
  **5 passed out of 5**.
- `git diff --check`: **1 passed out of 1**.

Two deprecation warnings were reported; neither was a test failure.

## Verification completed after resumption

- Five-packet validator-v2 calibration: **10 passed out of 10** as bounded
  per-packet schema/canonical and real-evidence materialization/round-trip runs.
- Disposable PostgreSQL Slice-3A matrix: **4 passed out of 4** after explicit
  migration to 0027 in database `t081_v4_s3a_20260907b`; cleanup dropped it and
  `paprnav_db` was never targeted.
- Candidate/API/applicability host suite: **40 passed out of 40**.
- Existing ingestion/matching/recurrence/full-readiness isolation suite:
  **81 passed out of 81**.
- Compilation: **6 passed out of 6**; `git diff --check`: **1 passed out of 1**.
- Exact evidence is in `implementation-slice-3a.md`.

## Independent implementation review

Reviewer `/root/v4_s3a_impl_adversary` returned **FAIL**. The immutable report is
`adversarial-implementation-initial.md`; the failed review is recorded in
`reviews.json`. Five findings are open in `findings.json`:

- `IA-001` blocker: still open for conditions/groups, expressions/rules, and
  search hints. Physical owners now cover value assertions, identity mappings,
  product scopes, designation scopes, designation values, and designation
  ranges with deferred direct-SQL and verified-read checks. The alternative
  generic-plus-view amendment received an independent design **FAIL** and was
  abandoned. After targeted-review fixes, this first owner sub-slice passed a
  broader relevant host **51/51** and fresh disposable PostgreSQL **17/17**
  matrix. Both review databases were dropped afterward.
- `IA-002` blocker: **closed after independent targeted re-review**. Deferred
  validation now rejects incomplete, extra, changed, reordered, or
  cross-referenced projection graphs, including listed-designation nodes.
- `IA-003` blocker: **closed after independent targeted re-review**. Exact
  successor/unique-predecessor resolution, target-local causal dependencies,
  canonical event causes, sorted application/database advisory locks, and a
  deferred global uniqueness check close sequential and concurrent direct-SQL
  write-skew. See `adversarial-implementation-ia003-closure.md`.
- `IA-004` high: **closed after independent targeted re-review**. Detail/list/
  reconstruction GETs are detection-only; repair is reachable only from the
  authorized, gated materialization POST. See
  `adversarial-implementation-ia004-closure.md`.
- `IA-005` high: **closed after independent targeted re-review**. Correction
  roots, ordered refs/evidence, document identities, 3A bindings, ordinals, and
  hashes are verified at commit and read.

The latest bounded reviewer result is the final source/product/designation
owner-family closure in
`adversarial-implementation-ia001-source-scope-final.md`: **IA-007 PASS** at
packet SHA-256
`fc8248bccc95dcee3bd5773f41fe5874c26a1127f65b352b89d574573b1528a5`.
This result closes only the read-time ordinal/corruption residual in that
family. It is not an IA-001 implementation PASS and is intentionally not
recorded as one in `reviews.json`.

The first holistic IA-001 matrix design reassessment then returned **FAIL** at
packet SHA-256
`c010cdc417c332f799b078b9e91e1000377103d8980fcbc9fa134ec95f490742`.
Its immutable result is
`adversarial-design-ia001-matrix-initial.md`; findings MA-001 through MA-005 are
recorded in the ledger and are fixed pending verification. The coordinator also
recorded MA-006 for the uncovered product normalized-identity union. No schema
or service edits were made while addressing these matrix defects. Because this
run is already in `implementation`, the review script correctly refused to
append a new design-stage attestation to `reviews.json`; the immutable artifact,
packet digest, and finding records preserve the result without falsifying the
run phase.

The final holistic matrix gate subsequently returned **PASS** at packet
SHA-256
`c4f91844476097f5ba733ad20c7b025ad0811c695e599c87170be3712fbd1564`.
The immutable result is `adversarial-design-ia001-matrix-final.md`. MA-001
through MA-007 are closed; the complete matrix is now authorized as the
pre-schema contract. IA-001 itself remains open until every family is
implemented and the whole implementation/closure review passes.

## Current IA-001 family progress

The first post-reset implementation family—conditions, value assertions, and
designation groups/members (matrix C1-C15)—is complete in the working tree and
has passed its bounded adversarial closure review. It includes exact typed
owners, union values, occurrence mappings, context evidence, commit-time SQL,
read-time verification, all 90 condition type/operator combinations, all 18
atomic known-string branches, all four group associations, both member kinds,
512-character boundary coverage, and direct-SQL corruption vectors.

The focused host/calibration evidence is **21/21** followed by **12/12** after
the read-corruption vector. The fresh PostgreSQL family evidence is **1/1**
positive plus **1/1** corruption matrix in disposable database
`t081_ia001_i`. No staging or commit occurred. Expression/rule, search-hint,
and final global families remain unimplemented, so IA-001 remains open.

The first bounded Family-1 review returned FAIL at packet `b6884407...`
with two high findings: INSERT-only deferred coverage and an underspecified
negative matrix. Both are now independently closed.
Triggers now cover INSERT/UPDATE/DELETE and both OLD/NEW projections, and the
expanded SQL/read vectors cover all named corruption classes plus later writes
after `SET CONSTRAINTS`. Post-fix host evidence is **22/22**; the full suite on
freshly migrated disposable PostgreSQL `t081_ia001_k` is **19/19**. Reviewer
`/root/v4_s3a_impl_adversary` returned PASS at packet
`a613ca3b54ad2181a47adcc896f93c86ab0c975913b55d6318927bb38c2de46f`;
see `adversarial-implementation-family1-closure.md`. IA-001 remains open while
the expression/rule, search-hint, and final global families are unfinished.

The second post-reset family—rules, recursive expressions, ordered expression
edges, and exclusions (matrix R1-R11)—is complete in the working tree and has
passed its bounded adversarial implementation review. It adds exact physical owners and
same-projection references for all six legal expression branches, explicit
condition-expression presence, context-relative paths, contiguous edges,
ordered exclusions, combined rule-reference/exclusion cycle rejection, and a
closed rejection path for requirement-state references in applicability rules.
Read verification independently reconstructs the same owner/reference graph.
The positive matrix includes both contexts, every legal branch, absent and
present condition roots, multiple exclusions, and a pointer-derived identity
longer than 255 characters. Direct-SQL tests cover changed, missing, extra,
reordered, cross-projection, cyclic, and forged-parent states. Focused host and
calibration evidence is **23/23**; the full freshly migrated PostgreSQL suite
in disposable database `t081_ia001_n` is **21/21**. No staging or commit
occurred. Reviewer `/root/v4_s3a_impl_adversary` returned PASS with no residual
finding at packet
`d287a97e1cad781ab0712a82ba5ff54e8e530faef31814ac91ed1bc44e46610a`;
see `adversarial-implementation-family2-initial.md` (artifact SHA-256
`237be72aed6d6cab8364462d05dbca0eeecc6ce0929c4b67c0b014178b7813a3`).
IA-001 remains open for the search-hint and final global families.

The third post-reset family—non-controlling search hints, manufacturer groups,
and members (matrix H1-H11)—is complete in the working tree and has passed its
bounded adversarial implementation review. It adds exact physical owners,
display/manufacturer assertions, occurrence mappings, group-context evidence,
closed association/value/member unions, canonical ordering, and independent
read verification. The positive vector covers all six product roles, all
three group associations, all assertion states, both member branches, and the
512-character boundary. The direct-SQL matrix includes a fully restamped
candidate/projection/datum/semantic graph with an extra hint property. Focused
host/calibration evidence is **24/24**; the full suite on freshly migrated
disposable PostgreSQL `t081_ia001_q` is **23/23**. No staging or commit
occurred. IA-001 remains open for the final global family and whole-tree
implementation/closure reviews.

Reviewer `/root/v4_s3a_impl_adversary` returned PASS with no blocker or
high-severity residual at packet SHA-256
`8eda25ce2c303107d6dcaba583bc5f56c2c9b8313b5748f5b43b8a63072b2072`.
The immutable result is `adversarial-implementation-family3-initial.md`
(artifact SHA-256
`9e0b4ae1c53460c7813e75ca176583a7497f071b104bdcc3a4123281313cd669`).
This result closes only H1-H11; IA-001 remains open.

The final global owner/reconstruction family is now implemented and awaiting
bounded adversarial review. It adds a complete Python and PostgreSQL typed-owner
reconstruction of the four-field applicability subtree, equality with the
generic datum graph/candidate/bytes/hashes, stored count checks on reads, a
global exactly-one-owner partition including change-dependency nodes, and the
same verified path for detail, reconstruction, and list audit responses.

Pre-review evidence is **25/25** focused host/calibration, **75/75** complete V4
host, and **24/24** on freshly migrated disposable PostgreSQL
`t081_ia001_s`, including downgrade/re-upgrade and direct-SQL duplicate-owner/
root-count attacks. Nothing is staged or committed. IA-001 remains open until
the bounded global review and whole-tree implementation/closure gates pass.

The bounded final-global review subsequently returned PASS with no blocker or
high-severity residual at packet SHA-256
`e250bc919acc55acf4578c7ee12c1e2c1c45c80e293a2fa1fa4ddbd299b467fd`.
See `adversarial-implementation-global-initial.md` (artifact SHA-256
`365742fa62948fdda0ae296f3d62d75bdabed196153af6ec6bc114db7d6e8f6d`).
All four bounded families now pass. IA-001 is deliberately still open pending
the holistic whole-tree implementation review and closure review.

The holistic whole-tree implementation review returned PASS at packet SHA-256
`d78b4a257935f45ec161bcc3af99daac8d371871e0eb72ebcb6a1a4f03384748`.
The immutable report is `adversarial-implementation-ia001-final.md` (artifact
SHA-256
`a3de4bd7b8f06e0056858c56fc72eb8885dce55a1fba8dfe9d00a58dfe51e29d`).
The reviewer explicitly authorized closing IA-001 at the implementation stage;
the ledger now contains 29 closed findings and no open finding. The recorded
implementation PASS advanced the run to `implementation_reviewed`. Closure
review, validation, staging, and commit are still pending.

## Governing strategy reset (2026-09-10)

The counterexample-by-counterexample implementation loop is stopped. Preserve
all valid fixes already in the working tree, but make no further schema or
service edits until one complete normative IA-001 mapping matrix and a
three-way-drift control design are written. Do not stage or commit.

IA-001 remains open until all owner families are implemented and reviewed
together. The remaining work is organized as complete invariant families:

1. conditions, value assertions, and designation groups/members;
2. expressions, edges, rules, and exclusions;
3. search hints, groups, and members; and
4. global exactly-one-owner, reconstruction, identity, evidence, reference,
   ordering, hash, and cardinality verification.

The normative matrix must also include the existing product/designation family
so that cross-family inconsistencies are visible before implementation. Each
family must cover every closed canonical union branch, its Python
materialization rule, PostgreSQL deferred rule, read-time verification rule,
and positive/direct-SQL corruption vectors before a new adversarial review is
requested. Review claims must never exceed the implemented checks.

## Verification not yet credited

- A passing independent implementation review: **0 passed out of 1**; the
  initial review failed with five findings.
- Closure review: not started.

## Runtime and data safety state

- The prior builder agent is interrupted and not running.
- Docker shows only the normal `backend-api-1` and healthy `backend-db-1`
  services. No one-off test container was present.
- A read-only PostgreSQL catalog query found **0 disposable databases** matching
  the Slice-3A or 0027 verification naming patterns.
- The normal `paprnav_db` was not used for the interrupted Slice-3A PostgreSQL
  verification and must not be used for future migration tests.

## Required continuation order

1. Obtain bounded adversarial review of the complete C1-C15 condition/group
   family and resolve any findings without widening the closure claim.
2. Implement and review expressions, edges, rules, and exclusions as one
   complete family.
3. Implement and review search hints, groups, and members as one complete
   family.
4. Complete global exactly-one-owner and full reconstruction/evidence checks.
5. Run the five calibration round trips, clean host suite, and a freshly
   migrated disposable PostgreSQL suite.
6. Build one honest whole-IA-001 packet and return it to the same independent
   reviewer. Obtain implementation PASS and closure PASS with no residual
   blocker.
7. Only then stage the exact reviewed tree, obtain staged-state attestation,
   and ask before committing.

## Immediate short commands

Run from the repository root unless noted:

```bash
git status --short
git diff --check

cd backend
PYTHONPATH=. .venv/bin/pytest -q tests/test_ad_v4_applicability.py
PYTHONPATH=. .venv/bin/pytest --collect-only -q \
  tests/test_ad_v4_applicability.py \
  tests/test_ad_v4_applicability_calibration.py \
  tests/test_ad_v4_applicability_postgres.py
```

Do not start the PostgreSQL matrix until its database target has been resolved
to a new explicit disposable name and checked against `paprnav_db`.

## Copy-ready prompt for a fresh Codex task

```text
Continue T081-V4-SCHEMA-SLICE-3A from
.ai/review-runs/T081-V4-SCHEMA-SLICE-3A/CURRENT_CHECKPOINT.md.

Use the adversarial-review skill and preserve builder/reviewer separation.
Do not restart the work or redo completed design review. Inspect the existing
partial implementation, then finish the bounded calibration and disposable
PostgreSQL gates, write exact implementation evidence, build the current packet,
and obtain independent implementation review. Do not use paprnav_db, do not
enable released/customer readers, and do not stage or commit without asking.
Report verification as x passed out of x.
```
