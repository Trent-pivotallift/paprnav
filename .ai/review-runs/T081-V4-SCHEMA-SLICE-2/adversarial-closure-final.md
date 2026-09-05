# T081 V4 Schema Slice 2 — independent closure review

## Outcome

**PASS — 19 passed out of 19 finding dispositions and 9 passed out of 9
implementation finding gates.**

Reviewer: `/root/v4_slice2_closure_reviewer`  
Builder: `/root/v4_schema_builder`  
Closure packet fingerprint:
`dd6ac0866e78ba8177c792a442657c2b9941e7b4125b67be772993f692b2c4dd`

This was a read-only review of the product implementation, tests, migration,
fixtures, decision record, finding ledger, implementation review, and closure
report. The only new artifact created by this reviewer is this immutable
closure report. No product code, test, migration, fixture, finding, decision,
or `closure.md` content was edited.

## Closure findings

No blocker, high, medium, or low closure finding remains open.

- The closure packet was reproduced against the live working tree with **0
  hash mismatches out of 49 bound files and review inputs**. Its packet SHA-256
  is `26a463ed686b33e8f62b7093a55dcbe1a470d2c4c645e908556fd236340a9e28`,
  exactly matching `review-packet.sha256`.
- The ledger has **19 closed out of 19 total findings**: ten design findings
  and nine implementation findings. There is no accepted risk, deferred
  blocker, or nonterminal disposition.
- The review history contains a current independent implementation PASS from
  `/root/v4_schema_adversary`, separate from builder
  `/root/v4_schema_builder`, against the final implementation scope.
- `git diff --check` passed, the manifest lists no out-of-scope dirty file, and
  direct repository search found no omitted V4 writer or consumer.

## Direct invariant trace

1. **Input and canonical identity.** The HTTP route receives streamed raw
   bytes under a hard cap before strict UTF-8/JSON parsing. Duplicate keys,
   numeric and null values, invalid Unicode, non-NFC strings, and versioned
   resource-limit violations fail closed. The checked-in closed schema and
   semantic graph validation precede persistence. Canonical array behavior is
   derived from schema annotations, preserves sequences, rejects duplicate set
   identities, and uses fixed domain/version bytes.
2. **Evidence.** Candidate storage locks the complete deduplicated fragment set
   in lexical fragment-ID order and requires each fragment to have exactly one
   valid admitted root. The 0026 lifecycle trigger makes competing lifecycle
   inserts lock the same parent row, preventing a stale-evidence commit.
   Official-document keys are checked against the retained source document and
   content hash. Exact source text is not copied into relational candidate
   rows.
3. **Persistence and correction.** Five additive tables separate canonical
   proposal content, evidence snapshots, submission/authorization provenance,
   candidate relationships, and the creation event. Database triggers bind
   canonical envelopes to relational parents and complete child sets, reject
   direct forgery, and forbid UPDATE or DELETE. Correction/replacement edges
   remain submission provenance and reject self-links and cycles.
4. **Authorization and audit.** Creation locks and verifies the exact active
   user and named active platform-administrator membership and snapshots the
   authorizing organization, membership, role/status, policy, hashes, and
   action. GET/list routes require an active platform administrator and expose
   bounded, stable proposal and independently paginated submission audit data
   after read-time integrity checks.
5. **Candidate-only isolation.** The database constrains every proposal to
   `candidate_only`. Direct reader/writer search found the new models only in
   the V4 candidate service and admin routes. No V3 review, publication,
   released catalog, matching, applicability, compliance, coverage, recurrence,
   or due-state reader consumes these rows.
6. **Migration and rollback.** Revision 0026 is additive and starts empty. Its
   downgrade takes exclusive locks, succeeds only for empty V4 tables, and
   refuses occupied rollback without deleting or translating audit data. The
   implementation review's fresh PostgreSQL matrix covered empty round trip,
   occupied refusal/preservation, waiting/locking, concurrency, direct SQL,
   lifecycle races, and immutability.

## Independent verification

- Current closure packet integrity: **49 passed out of 49 bound file/input
  hashes**, plus **1 passed out of 1** packet checksum.
- Current focused host suite: **45 passed out of 45**, with five expensive
  real-admission cases intentionally deselected; two deprecation warnings only.
- Independent representative retained PDF → Slice-1 admission → V4 persistence:
  **1 passed out of 1** for AD 2024-14-03.
- Previously independently reviewed calibration evidence remains current:
  **6 passed out of 6 retained PDFs**, **5 passed out of 5 AD claim packets**,
  **5 passed out of 5 real admissions/persistence cases**, **5 passed out of 5
  semantic negatives**, and **5 passed out of 5 structural negatives**, over
  67 clause-narrow fragments.
- The final isolated PostgreSQL matrix remains credited at **5 passed out of
  5**. A new read-only database-catalog query found **0 leftover databases**
  matching the Slice-2, closure, or final-proof names. The ordinary
  `paprnav_db` was not used for closure testing.
- Final implementation finding gate: **9 passed out of 9**.

## Deferred scope and regulatory claim

The stated later-slice exclusions are coherent and visible: normalized V4
semantic materialization, reviewer GUI/forms, human recurring-date review,
signoff/approval/rejection/publication/current selection, customer catalog and
aircraft matching/compliance/due-state consumers, V3 translation or fallback,
supporting-document admission, cross-page/OCR evidence, aircraft-specific AMOC
use, and provider/CLI writers.

This PASS does not approve or release any Airworthiness Directive, determine
aircraft applicability or compliance, compute a due date, or represent the V4
candidate as regulatory truth. It closes only the immutable, evidence-bound,
platform-admin-authored `candidate_only` Slice-2 foundation.
