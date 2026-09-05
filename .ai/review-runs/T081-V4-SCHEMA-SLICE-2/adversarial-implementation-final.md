# T081 V4 Schema Slice 2 — final adversarial implementation review

## Outcome

**PASS — 9 passed out of 9 implementation finding gates.**

Reviewer: `/root/v4_schema_adversary`  
Builder: `/root/v4_schema_builder`  
Starting packet fingerprint: `b3f600c5b37b2a33da6c1fc6a8e96183aa3274f487e39348c731db8807ce6fc6`

The starting implementation packet verified current with 19 changed files and
49 explicit review inputs. This review inspected the live staged, unstaged, and
untracked implementation and direct consumers; no product code was edited by
the reviewer.

## Finding dispositions

- **T081-V4-S2-IA-001 — CLOSED.** The semantic phase now traverses activation,
  branch, and conditioned-recurrence expressions; validates typed namespaces,
  prerequisites, termination, recurrence membership, and group/inline timing;
  and rejects multi-edge rule, requirement, correction, candidate, and
  supersession cycles. The previously accepted two-edge supersession and
  candidate-correction cycles now reject with `cyclic_reference`.

- **T081-V4-S2-IA-002 — CLOSED.** Canonicalization derives set/sequence rules
  from the checked-in schema, rejects both byte-identical members and duplicate
  keyed/composite identities before sorting, and preserves declared sequences.
  The former tied supersession identity counterexample now rejects with
  `duplicate_stable_key`; model, range, and supersession reorder vectors pass.

- **T081-V4-S2-IA-003 — CLOSED.** Migration 0026 binds fixed proposal versions
  and gate, declared evidence child identity, active user and membership,
  authorization policy/action/claims hash, relationship envelope/evidence/
  parent/self/cycle constraints, event identity, and deferred complete child
  sets. The PostgreSQL matrix includes self-consistently rehashed authorization,
  direct candidate-cycle, forged envelope, and late-child counterexamples.

- **T081-V4-S2-IA-004 — CLOSED.** The calibration bundle contains 67
  clause-narrow fragments across six retained official PDFs. It verifies exact
  retained bytes/page text/offset selections and claim kinds, enters the real
  Slice-1 admission lifecycle, and persists all five candidate-only V4
  proposals. Five composed semantic negatives cross the calibration admission
  oracle, and five structural negatives cross the production schema validator.
  The deterministic rebuild reproduces the checked-in manifest identity.

- **T081-V4-S2-IA-005 — CLOSED.** The coordinator executed the final five-case
  PostgreSQL matrix on fresh database `paprnav_v4_slice2_closure3`: **5 passed
  out of 5 in 3.72 seconds**. Inspection confirms coverage of empty and occupied
  downgrade, occupied-downgrade waiting, same-key/different-payload concurrency,
  reversed overlapping two-fragment locking, distinct correction origins,
  candidate relationship cycles, direct-SQL envelope and late-child forgery,
  all-table immutability, concurrent lifecycle successors, and the exact
  candidate-binding versus lifecycle-transition race. The latter observed the
  lifecycle transaction waiting on the candidate-held row lock, allowed the
  candidate to commit, then proved later candidate use fails closed as
  `evidence_not_admitted`. The named database/container were removed and
  wildcard absence was verified.

- **T081-V4-S2-IA-006 — CLOSED.** `_binding_snapshot` deduplicates fragment IDs
  and locks the complete set in lexical ID order before lifecycle reads. The
  two-session PostgreSQL case submits overlapping fragments in opposite JSON
  order under bounded lock/statement timeouts and both complete deterministically.

- **T081-V4-S2-IA-007 — CLOSED.** Platform-admin list/detail responses expose
  the complete immutable submission authorization and relationship audit
  representation. Proposal pages and nested submission pages have independent
  bounded limit/offset controls, totals, stable created-at/ID ordering,
  authorization denial, and read-time integrity verification.

- **T081-V4-S2-IA-008 — CLOSED.** The request body is streamed under a hard byte
  cap; concrete depth/node/string/array/evidence/AST/edge limits are versioned.
  Decoder `RecursionError` is translated to stable `resource_limit` HTTP 413.
  The prior 10,000-level hostile JSON counterexample now fails closed at both
  service and API boundaries.

- **T081-V4-S2-IA-009 — CLOSED, no regression.** Relationship hash identity
  includes immutable `submissionId`; sequential and concurrent distinct origins
  persist separate provenance without collision or silent collapse.

## Exact verification accounting

- Starting packet freshness: **1 passed out of 1** at `b3f600c5...`.
- Independent focused host suite: **45 passed out of 45** in 6.42 seconds.
- Independent replay of the four closure-1 counterexamples: **4 passed out of
  4** (deep JSON, supersession cycle, duplicate composite identity, candidate
  relationship cycle).
- Independent representative real retained-PDF -> Slice-1 admission -> V4
  persistence: **1 passed out of 1** in 9.96 seconds.
- Source-accounted calibration evidence: **6/6** PDF integrity, **5/5** claim
  packets, **5/5** real admissions/persistence, **5/5** semantic negatives,
  and **5/5** structural negatives.
- Coordinator fresh PostgreSQL matrix inspected and credited: **5 passed out
  of 5** in 3.72 seconds, with cleanup verified.
- Final implementation finding gate: **9 passed out of 9**.

## Scope boundary

This PASS covers Slice 2 candidate-only canonical validation, evidence binding,
append-only persistence, admin audit APIs, and calibration. It does not approve
publication, normalized V4 semantic tables, aircraft applicability/due-state,
human signoff, customer-facing assessment, or V3 replacement; those remain
later reviewed slices.
