# Implementation evidence: T081-V4-SCHEMA-SLICE-3A

Date: 2026-09-07  
Builder: `/root` (continuing the preserved partial implementation)  
Base: `28f6be0 feat: add immutable AD V4 candidate foundation`

## Implemented scope

- Added validator-2/canonicalizer-2 dispatch while preserving validator-1
  verification and storage semantics.
- Added default-off application and database capability gates for validator-2
  writes and Slice-3A materialization/read routes.
- Added migration 0027 with validator-version propagation, additive immutable
  applicability/correction/dependency/event tables, integrity validation,
  feature-gate administration, and downgrade refusal for validator-2 or Slice-3A
  state.
- Added candidate-only applicability materialization, exact relational subtree
  reconstruction, shared correction foundations, explicit unreviewed identity
  mappings, stale-state detection, and inline authorized repair.
- Added bounded platform-admin materialize/list/detail/reconstruction API
  surfaces using the exact acting membership.
- Added unit, API, five-packet calibration, and disposable PostgreSQL coverage.

No released/customer reader, aircraft matching, compliance, due-state, V3
mutation, provider/CLI/cron/background writer, publication, or reviewer UI was
added.

## Verification performed

- Focused applicability suite after interruption: **10 passed out of 10**.
- Candidate/API/applicability suite:
  `test_ad_v4_candidates.py`, `test_ad_v4_api.py`, and
  `test_ad_v4_applicability.py`: **40 passed out of 40** in 5.05 seconds.
- Existing ingestion/matching/recurrence/full-readiness isolation suite:
  **81 passed out of 81** in 16.80 seconds.
- Validator-2 five-packet schema and canonical determinism: **5 passed out of
  5**, run as bounded one-packet invocations.
- Validator-2 five-packet real-evidence materialization and exact round trip:
  **5 passed out of 5**, run as bounded one-packet invocations.
- Disposable PostgreSQL matrix after explicit upgrade to 0027: **4 passed out
  of 4** in 3.08 seconds. It covered empty and v1-only downgrade/re-upgrade,
  v2 downgrade refusal with head preservation, projection integrity and
  immutability, occupied downgrade refusal, concurrent same-key retry, and
  gate disable. Database `t081_v4_s3a_20260907b` was dropped by the cleanup
  trap; `paprnav_db` was not targeted.
- Python compilation of both changed services, migration 0027, and the three
  new Slice-3A test files: **6 passed out of 6**.
- `git diff --check`: **1 passed out of 1**.
- Application-reader search: Slice-3A model/service references occur only in
  `app/services/ad_v4_applicability.py`, bounded admin routes in
  `app/api/routes/ads.py`, model declarations, and migration code: **1 passed
  out of 1** scope checks; no released/customer consumer was found.

Two preexisting Starlette deprecation-warning categories remain: the TestClient
httpx compatibility warning and the renamed HTTP 413 constant. Neither is a
test failure or introduced safety behavior.

## Diagnostic correction

The first disposable PostgreSQL command created a fresh blank database and ran
the matrix without first applying migrations. Test 00 correctly rejected a
downgrade from an unversioned database, and the remaining tests lacked the 0027
gate function. This was a harness precondition error, not credited as product
verification. Its cleanup trap dropped `t081_v4_s3a_20260907`. The corrected
run explicitly upgraded a separately named database to 0027 before pytest and
passed all 4 cases.

Two initial host-suite commands referenced nonexistent filenames
`test_ads_api.py`, `test_ad_v3_service.py`, and `test_ad_v3_api.py`; pytest
collected no tests. The corrected 40-test and 81-test suites above are the
credited results.

## Deviations and unverified gates

- `IA-004` was fixed after the initial FAIL: audit GET/list/reconstruction are
  now detection-only, and deterministic repair is invoked only from the
  authorized, gated materialization POST on normal and idempotent paths. The
  focused applicability suite passed **10 out of 10**, the combined focused
  suite passed **40 out of 40**, and independent reviewer
  `/root/v4_s3a_impl_adversary` returned a targeted PASS recorded in
  `adversarial-implementation-ia004-closure.md`.
- `IA-002`, `IA-003`, and `IA-005` are closed after independent targeted
  verification. Migration 0027 performs deferred exact graph, correction, and
  supersession validation; verified reads independently reconstruct correction
  and dependency facts. PostgreSQL supersession coverage includes exact,
  mismatched, ambiguous, forged-cause, application-concurrent, and raw/direct
  lock cases.
- The final clean disposable PostgreSQL matrix passed **14 out of 14**. The
  focused host suite passed **36 out of 36**, and the broader relevant
  candidate/API/applicability/calibration suite passed **50 out of 50**.
- `IA-001` remains open for conditions, expressions, rules, and search hints.
  The first physical owner sub-slice is implemented for source assertions,
  identity mappings, product scopes, designation scopes, exact listed values,
  and lexical-only ranges. Deferred validation proves exact canonical fields,
  cardinality, ownership, mapping/evidence links, and ordinals for direct SQL;
  verified reads independently compare the physical source/scope graph.
- The generic-plus-view equivalence amendment received an independent design
  **FAIL** and was abandoned in favor of the approved physical-table design.
- After the first targeted review fixes, the broader relevant host suite passed
  **51 out of 51** and a fresh disposable PostgreSQL matrix passed **17 out of
  17**. It covers the reconstruction endpoint's rejection of mapping semantic,
  occurrence, evidence-parent, kind, provenance-union, identity-hash, and link-
  hash drift, plus mapping-free listed serial/part values and a wrong-kind SQL
  negative. The earlier pre-review source/scope run passed **20 out of 20** host
  tests and **16 out of 16** PostgreSQL tests,
  including manufacturer, listed, range, series-expression, and typed-owner
  tamper coverage. Databases `t081_ia001_b` and `t081_ia001_d` were dropped;
  `paprnav_db` was not targeted.
- Current implementation has not yet passed independent Codex implementation
  review.
- Closure review and review-run validation have not yet occurred.
- The working tree is not staged and no Slice-3A commit exists.

## IA-001 complete family 1: conditions and designation groups (2026-09-10)

Implemented the complete C1-C15 matrix as one family:

- physical condition, designation-group, and designation-group-member owners;
- exact value-assertion owners for all six atomic subject fields, group display,
  and member manufacturer values across known/unknown/not-applicable branches;
- ambiguity-preserving `model_or_series` mappings plus exact model, series, and
  manufacturer occurrence mappings;
- independent occurrence/context evidence verification;
- exact Python materialization, PostgreSQL commit validation, and reconstruction
  read validation, including complete owner/mapping/node set checks; and
- a transaction-generation dirty marker so deferred validation runs once per
  complete projection state rather than once per inserted row. A later insert
  increments the generation and therefore forces revalidation even after an
  earlier `SET CONSTRAINTS` boundary.

Credited bounded verification:

- focused host applicability plus calibration suite before the final read vector:
  **21 passed out of 21**;
- reconstruction corruption and five-packet calibration: **12 passed out of
  12**;
- fresh migration from empty state in disposable PostgreSQL database
  `t081_ia001_i`: **1 passed out of 1** exhaustive positive family vector;
- direct-SQL condition/value/group/member/mapping/evidence corruption validator:
  **1 passed out of 1** with six corruption classes; and
- Python compilation of service, models, migration, and test files: passed.

The positive PostgreSQL vector contains all **90** condition type/operator
combinations, all **18** atomic field/union combinations, all **4** designation
group associations, both member designation kinds, mixed manufacturer unions,
and the **512-character** not-applicable boundary. The family is ready for a
bounded adversarial review; IA-001 as a whole remains open.

The initial bounded Family-1 review returned FAIL with two high findings. The
closure implementation expands dirty/completeness triggers to INSERT, UPDATE,
and DELETE for both OLD and NEW projections; binds mapping rows to their exact
mapping semantic-node occurrence; and adds the full missing/extra/wrong-type,
cross-projection, union/presence, evidence-pair, provenance/hash, ordering,
cardinality, and post-`SET CONSTRAINTS` generation matrix. Post-fix evidence:

- focused host applicability/calibration: **22 passed out of 22**;
- freshly migrated disposable PostgreSQL suite in `t081_ia001_k`: **19 passed
  out of 19**; and
- compilation, findings JSON validation, and `git diff --check`: passed.

Independent reviewer `/root/v4_s3a_impl_adversary` closed findings
`T081-V4-S3A-F1-IA-001` and `T081-V4-S3A-F1-IA-002` at packet
`a613ca3b54ad2181a47adcc896f93c86ab0c975913b55d6318927bb38c2de46f`.
The immutable PASS is `adversarial-implementation-family1-closure.md`.
IA-001 remains open for the expression/rule, search-hint, and final global
families.

## IA-001 complete family 2: rules and expression graphs (2026-09-10)

Implemented the complete R1-R11 matrix as one family:

- physical applicability-rule and recursive expression owners;
- typed same-projection scope, condition, and rule references;
- explicit condition-root presence and exact scope/condition root ownership;
- ordered expression edges with one parent per non-root, canonical arity, and
  context/owning-rule agreement;
- ordered rule exclusions and a combined reference/exclusion acyclicity check;
- commit-time rejection of the requirement-state-only expression branch,
  including a direct writer that restamps the candidate, projection envelope,
  datum graph, and semantic hashes; and
- independent read-time verification of nodes, owners, references, evidence,
  roots, paths, edges, exclusions, ordering, cardinality, and cycles.

Credited bounded verification:

- focused host applicability plus five-packet calibration: **23 passed out of
  23**;
- fresh migration from empty state and the complete PostgreSQL suite in
  disposable database `t081_ia001_n`: **21 passed out of 21**;
- the positive rule vector contains all six legal expression branches, both
  contexts, absent/present condition roots, multiple exclusions, nested
  sequence preservation, and a pointer/node key longer than 255 characters;
- the direct-SQL matrix covers rule presence, owner/reference/path/type drift,
  edge order and missing/extra edges, exclusion target/order/missing rows,
  evidence purpose, semantic parent/hash, missing and wrong typed owners,
  cross-projection references, self-cycle construction, and the forbidden
  requirement-state branch; and
- Python compilation and `git diff --check`: passed.

This is a bounded Family-2 implementation claim only. IA-001 remains open for
search hints and the final global exactly-one-owner/reconstruction gate.

Independent reviewer `/root/v4_s3a_impl_adversary` returned a bounded Family-2
PASS with no residual findings at review-packet SHA-256
`d287a97e1cad781ab0712a82ba5ff54e8e530faef31814ac91ed1bc44e46610a`.
The immutable result is `adversarial-implementation-family2-initial.md`
(artifact SHA-256
`237be72aed6d6cab8364462d05dbca0eeecc6ce0929c4b67c0b014178b7813a3`).
This result does not close IA-001.

## IA-001 complete family 3: non-controlling search hints (2026-09-10)

Implemented the complete H1-H11 matrix as one family:

- physical search-hint, manufacturer-group, and member owners;
- exact display, group-manufacturer, and member-manufacturer value assertions;
- exact group/manufacturer, member/model-or-series, and member/manufacturer
  occurrence mappings with the enclosing group as evidence context;
- fixed non-controlling/non-exhaustive semantics and no controlling-expression
  reference path;
- all group association and known/unknown/not-applicable manufacturer branches;
- model and opaque series-expression member branches without range expansion;
- independent PostgreSQL closed-shape, owner, union, ordering, identity,
  evidence, hash, and full-set checks; and
- independent reconstruction verification with controlled 409 failures for
  typed-owner, assertion, mapping, evidence, ordinal, hash, missing, and extra
  drift.

Credited bounded verification:

- focused host applicability plus five-packet calibration: **24 passed out of
  24**;
- fresh migration from empty state and the complete PostgreSQL suite in
  disposable database `t081_ia001_q`: **23 passed out of 23**;
- the positive search-hint vector covers all six product roles, all three group
  associations, all three assertion/manufacturer states, both member branches,
  the 512-character not-applicable boundary, 24 assertions, and 18 exact
  identity mappings;
- the PostgreSQL corruption matrix covers changed/missing/extra/reordered and
  cross-projection owners, assertion and evidence drift, mapping cross-wires,
  later writes after `SET CONSTRAINTS`, and a fully restamped candidate,
  projection, datum, and semantic graph containing a forbidden extra hint
  property; and
- Python compilation, findings JSON validation, and `git diff --check` passed.

This is a bounded Family-3 implementation claim only. IA-001 remains open for
the final global exactly-one-owner and whole-graph reconstruction gate.

Independent reviewer `/root/v4_s3a_impl_adversary` returned a bounded Family-3
PASS with no blocker or high-severity residual at review-packet SHA-256
`8eda25ce2c303107d6dcaba583bc5f56c2c9b8313b5748f5b43b8a63072b2072`.
The immutable result is `adversarial-implementation-family3-initial.md`
(artifact SHA-256
`9e0b4ae1c53460c7813e75ca176583a7497f071b104bdcc3a4123281313cd669`).
IA-001 remains open pending the final global family and whole-tree reviews.

## IA-001 final global family: owner partition and typed reconstruction (2026-09-11)

Implemented the final cross-family equivalence gate without staging or
committing:

- Python audit reads now prove stored semantic/evidence/identity counts and an
  exact one-owner partition across every semantic type, including outgoing and
  target-local incoming change-dependency nodes;
- Python independently reconstructs all four canonical applicability fields
  from physical product/designation, condition/group/member, rule/expression,
  and search-hint owners plus typed assertions, mappings, evidence links,
  references, edges, exclusions, presence discriminators, and canonical
  ordinals;
- the typed reconstruction must equal the generic datum reconstruction, the
  verified parent candidate subtree, stored restricted-JCS bytes/hash, and the
  projection envelope hash;
- PostgreSQL now exposes typed assertion, normalized-identity, designation,
  recursive-expression, condition-group, search-group, evidence, and complete
  subtree reconstruction helpers, and the deferred validator requires their
  full JSONB result to equal the candidate subtree;
- the PostgreSQL exactly-one-owner union now includes change dependencies and
  rejects duplicate owners for both outgoing and incoming semantic nodes;
- projection-root UPDATE/DELETE remains covered by the same dirty-generation
  and deferred validation mechanism as every child table; and
- detail, reconstruction, and list audit serialization all enter the complete
  verified typed-read path and remain detection-only.

Credited pre-review verification:

- focused applicability plus five-packet calibration host suite: **25 passed
  out of 25**;
- complete V4 host surface (`api`, `candidates`, base calibration,
  applicability, and applicability calibration): **75 passed out of 75**;
- fresh migration from empty state followed by the full Slice-3A PostgreSQL
  suite in disposable database `t081_ia001_s`: **24 passed out of 24**;
- the PostgreSQL suite's first test completed a clean v1-only
  downgrade/re-upgrade, proving the typed helper teardown as well as creation;
- the global positive vector combines typed designation unions, recursive
  rules, search hints, dual evidence, and a supersession dependency and proves
  exact Python and PostgreSQL typed reconstruction; and
- direct-SQL negatives prove rejection of a duplicate dependency owner and a
  root count mutation after disabling only immutability. Host audit vectors
  prove controlled 409 responses from detail, reconstruction, and list for
  stored-count drift.

Python compilation and `git diff --check` passed. This evidence makes the final
global family ready for bounded adversarial review, but IA-001 remains open
until that review and the subsequent whole-tree implementation/closure reviews
pass.

Independent reviewer `/root/v4_s3a_impl_adversary` returned a bounded final-
global PASS with no blocker or high-severity residual at packet SHA-256
`e250bc919acc55acf4578c7ee12c1e2c1c45c80e293a2fa1fa4ddbd299b467fd`.
The immutable result is `adversarial-implementation-global-initial.md`
(artifact SHA-256
`365742fa62948fdda0ae296f3d62d75bdabed196153af6ec6bc114db7d6e8f6d`).
All four bounded IA-001 families have now passed, but IA-001 remains open
pending one holistic whole-tree implementation review and closure review.

The holistic whole-tree implementation review then returned PASS at packet
SHA-256
`d78b4a257935f45ec161bcc3af99daac8d371871e0eb72ebcb6a1a4f03384748`.
The immutable report is `adversarial-implementation-ia001-final.md` (artifact
SHA-256
`a3de4bd7b8f06e0056858c56fc72eb8885dce55a1fba8dfe9d00a58dfe51e29d`).
The reviewer found no blocker or high-severity residual and authorized IA-001
closure at the implementation stage. IA-001 is now closed in the durable
ledger; all 29 findings are closed. The implementation PASS is recorded in
`reviews.json`, and the run is `implementation_reviewed`. Closure review and
review-run validation remain pending; nothing is staged or committed.
