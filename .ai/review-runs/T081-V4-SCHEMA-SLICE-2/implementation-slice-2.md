# T081 V4 Schema Slice 2 — implementation evidence

## Outcome

**READY FOR IMPLEMENTATION RE-REVIEW — DO NOT RECORD PASS WITHOUT INDEPENDENT REVIEW.**

The implementation findings from the initial adversarial review have been
remediated in the working tree, and the coordinator's fresh isolated
PostgreSQL proof now passes. This is a builder handoff for independent
verification, not an implementation PASS.

## Implemented work in the current working tree

- Additive candidate proposal, evidence binding, submission, relationship,
  and event models were drafted in `backend/app/models/core.py`.
- A draft raw-byte parser, validator, canonicalizer, hash profile, evidence
  admission check, and candidate persistence service was added at
  `backend/app/services/ad_v4_candidates.py`.
- A draft V4 JSON Schema was added at
  `backend/app/schemas/ad_extraction_v4.schema.json`.
- The checked-in schema now closes every nested object and supplies an item
  schema plus canonical set/sequence annotation for every array. The runtime
  validates this same artifact before semantic/reference validation.
- Requirements carry a required positive canonical-decimal-string `sequence`;
  the semantic validator requires unique contiguous values from `1` so
  regulatory action order survives key-sorting of the requirement set.
- Additive migration `20260901_0026_add_ad_v4_candidates.py` was added with
  immutable candidate tables and an empty-only downgrade.
- Platform-administrator candidate POST and audit GET/list routes and response
  schemas were drafted.
- Semantic validation now closes all typed key registries and references,
  expression graphs, recurrence membership, correction/supersession edges,
  prerequisite/terminating cycles, and reviewed graph/resource limits.
- Canonical set/sequence behavior is derived from the checked-in schema rather
  than a manually maintained path list.  Requirement sequence is explicit,
  unique, and contiguous.
- Evidence fragment rows are locked in sorted fragment-id order. Candidate
  relationship identity includes the immutable submission id, so distinct
  origins retain separate immutable provenance without a global-hash
  collision.
- The HTTP writer reads the request stream incrementally and enforces raw-byte,
  depth, node, string, array, evidence, AST, and graph-edge limits before
  persistence. Audit list/detail responses verify and expose every immutable
  submission and relationship provenance record.
- Migration 0026 now validates canonical proposal, binding, submission,
  relationship, and event envelopes against relational columns; deferred
  triggers require complete proposal and submission child sets.
- All five calibration packets now retain exact official bytes, deterministically
  derive the Slice-1 bounded text identity, create real page renditions/text
  versions/admitted fragments/lifecycle roots, and persist candidate-only V4
  proposals. A transaction-local derived-text cache is bound to parser version,
  source ids/hashes/sizes, and the complete bounded-page identity; retained
  bytes are reverified on every use.

These are implementation candidates for independent inspection, not reviewed
or approved behavior.

## Exact completed verification

1. Focused schema/service, semantic-graph, canonicalization, resource-limit,
   API authorization/raw-stream/audit, V3-isolation, and source-accounted
   calibration tests: **40 passed out of 40**.
   - Fast focused subset excluding expensive real admission: **35 passed out
     of 35** in 5.86 seconds after adding the explicit PostgreSQL dependency
     flush-order regression.
   - Real Slice-1 admission plus Slice-2 persistence: **5 passed out of 5**.
     Per-packet observed results were 2024 (6.69s), 2011 (5.08s), 2002
     (11.39s), 2008 including correction evidence (10.36s), and 1998 full issue
     (26.90s under a hard 30-second alarm).
2. The explicit cache-identity assertion was rerun with 2024 and passed **1
   out of 1** in 6.45 seconds. It asserts the key carries the installed pypdf
   version and every retained source content hash, and that the cached value is
   addressed by the complete bounded-page identity hash.
3. Python compile checks for the V4 service, evidence service, calibration
   harness, PostgreSQL test, and migration: **passed**.
4. Combined Slice-1 evidence-fragment regression plus V4 candidate/API tests:
   **29 passed out of 29** in 13.10 seconds. This was rerun after adding the
   bounded-text cache and controlled error mapping for a tampered or unavailable
   retained document.
5. Coordinator fresh isolated PostgreSQL matrix: **3 passed out of 3** in 2.86
   seconds, with one deprecation warning. The run upgraded the exact disposable
   database `paprnav_v4_slice2_finalproof` from 0025 to 0026 and exercised:
   - empty downgrade/re-upgrade;
   - concurrent idempotent writes and correction-relationship origins;
   - UPDATE and DELETE immutability on all five V4 tables;
   - direct-SQL forged proposal, binding, submission, relationship, and event
     rejection; and
   - occupied downgrade refusal with immutable audit rows preserved.

## Remaining independent review gates

- The separate adversarial implementation reviewer must inspect the current
  hash-bound packet and independently disposition IA-001 through IA-009.
- No builder finding disposition is `closed`; all remain
  `fixed_pending_verification` until that review.

## Commands and observed outcomes

- `PYTHONPATH=. ... pytest -q tests/test_ad_v4_candidates.py
  tests/test_ad_v4_api.py tests/test_ad_v4_calibration.py -k 'not
  real_admitted'` — **35 passed out of 35**, 5 deselected, two deprecation
  warnings, 5.86 seconds.
- Five separately bounded invocations of
  `test_calibration_packet_uses_real_admitted_evidence_and_persists_candidate`
  — **5 passed out of 5**; exact times listed above.
- `pytest -q tests/test_ad_evidence_fragments.py
  tests/test_ad_v4_candidates.py tests/test_ad_v4_api.py` — **29 passed out of
  29**, two deprecation warnings, 13.10 seconds.
- `py_compile` of the changed service/test/migration modules — passed.
- Coordinator fresh isolated PostgreSQL matrix — **3 passed out of 3**, one
  deprecation warning, 2.86 seconds.

## Operational cleanup

Both explicitly named disposable databases `paprnav_v4_slice2_verify` and
`paprnav_v4_slice2_pgproof` were checked by exact name and dropped. The named
ephemeral test container had exited and was absent from the Compose project
listing. No production/default `paprnav_db` mutation was authorized or
intended. Earlier broad Docker invocations and failed bind-mount attempts are
not evidence.

The coordinator also removed the exact disposable database
`paprnav_v4_slice2_finalproof` and its existing-image disposable container
after the successful 3/3 run, then reverified that both were absent.

## Required next implementation steps

1. Independently inspect the five exact retained-source packets and the
   schema-derived canonicalization/semantic counterexamples.
2. Independently inspect the PostgreSQL assertions and the proposal → bindings
   → submission → relationships/event flush-order enforcement.
3. Disposition IA-001 through IA-009 from the current review packet.

## Review-state instruction

Do not record implementation PASS or move the run to
`implementation_reviewed` from this builder artifact alone. The independent
reviewer must verify the current packet. No implementation finding has been
self-closed by the builder.

## Closure-1 remediation (pending independent re-verification)

After the independent closure-1 FAIL, the builder added the following narrowly
scoped remediations without changing the candidate-only release boundary:

- complete multi-edge cycle rejection for directive supersession, official
  correction documents, and candidate correction/replacement submissions;
- reference traversal for conditioned recurrence, rejection of group/inline
  timing conflicts, and rejection of duplicate composite supersession
  identities before canonical sorting;
- stable `resource_limit` / HTTP 413 handling for a 10,000-level JSON nesting
  attack;
- bounded, stable proposal and nested submission audit pagination, including
  total/limit/offset metadata and integrity checks on every returned page;
- PostgreSQL trigger binding for fixed proposal versions/gate, declared
  evidence children, active user/membership and authorization-policy snapshot,
  relationship evidence/self/cycle rules, and deferred child-to-parent envelope
  completeness; and
- PostgreSQL counterexample source for same-key/different-payload races,
  reversed two-fragment locking, concurrent lifecycle successors, direct-SQL
  candidate cycles and self-consistent authorization forgery, late child-row
  insertion, and a downgrade wait/refusal race.

Focused host verification after those edits is **30 passed out of 30** in 3.07
seconds (candidate service plus API), with **3 passed out of 3** targeted new
graph tests in 0.40 seconds. Python compilation, test collection (**4
PostgreSQL tests collected**), and `git diff --check` passed.

The coordinator then executed the finalized four-phase PostgreSQL matrix on a
fresh database upgraded through revision 0026: **4 passed out of 4** in 4.11
seconds, with one deprecation warning. The exact disposable database was
`paprnav_v4_slice2_closure2`. Coverage included every expanded concurrency,
direct-SQL integrity, lifecycle, lock-order, relationship-cycle, and rollback
case. The database and container were removed, and read-only checks confirmed
that both `paprnav_v4_slice2_closure2` and the earlier
`paprnav_v4_slice2_finalproof` database names were absent.

The coordinator then ran the finalized five-phase matrix, including the exact
candidate-binding transaction versus lifecycle-transition race, against fresh
database `paprnav_v4_slice2_closure3`: **5 passed out of 5** in 3.72 seconds,
with one deprecation warning. The race proves that a candidate holding the
validated admitted-fragment row lock commits before a competing lifecycle
transition, after which later candidate stores fail closed because the evidence
is no longer eligible. The exact database and container were removed; a
read-only wildcard check confirmed that no closure or final-proof disposable
database remained.

The separate calibration builder completed IA-004 without production
hard-coding: **67 clause-narrow fragments**, **6 passed out of 6** retained-PDF
integrity checks, **5 passed out of 5** claim-integrity packets, **5 passed out
of 5** real evidence-admission plus candidate-persistence cases, **5 passed out
of 5** schema-valid composed negatives rejected with
`calibration_semantic_mismatch`, and **5 passed out of 5** structural validator
negatives. The deterministic rebuild reproduced the checked-in manifest hash
exactly. No fixture-local AD truth was added to the production validator or
store.
