# T081-V4-SCHEMA implementation slice 1 — adversarial review

Reviewer: `/root/v4_schema_adversary`  
Builder: `/root/v4_schema_builder`  
Stage: implementation  
Decision: **FAIL**  
Packet fingerprint reviewed: `23fe14c45d4f2b388147d49b0d0e031fd230fdea15a80d31f2142b2b64a99b23`

The packet freshness verifier passed before review findings were recorded. The
packet nevertheless failed completeness inspection because its manifest binds
only `decision.md` and `findings.json` as review inputs, not the slice declaration
or governing schema proposal.

## Gate result

**6 passed out of 12 implementation gates.** Four blockers, two high findings,
and one medium finding remain open. Slice 1 must not advance.

| Gate | Result | Evidence |
|---|---|---|
| Packet completeness/freshness | FAIL | T081-V4-IA-001 |
| Retained PDF byte hash/size and bounded native-text derivation | PASS | `verified_retained_document_bytes`; focused wrong-hash/tamper tests |
| Newly stored PNG read-back integrity | FAIL | T081-V4-IA-005 |
| Relational wrong-document/page/hash prevention | FAIL | T081-V4-IA-002 |
| Platform-admin authorization and response-data boundary | PASS | both evidence endpoints call `ensure_ad_extraction_reviewer`; maintenance-shop denial test |
| Single-page exact server-derived selection | PASS | `page_end = page_start`; server slices bounded page text; selector tests |
| Duplicate/concurrent admission serialization | PASS | document row lock and unique identities; PostgreSQL test design serializes two sessions |
| Append-only lifecycle/hash-chain semantics | FAIL | T081-V4-IA-003 |
| Immutable-row enforcement | PASS by implementation inspection | triggers are created on all four tables; complete PostgreSQL test evidence remains absent under T081-V4-IA-006 |
| Upgrade/downgrade/rollback safety | FAIL | T081-V4-IA-004 and T081-V4-IA-006 |
| Relevant-page UI navigation, including noncontiguous metadata | PASS | UI displays exact page list and navigates to the first relevant retained-PDF page |
| Deferred cross-page/OCR/coordinates/decision binding and mixed-V3 isolation | PASS | constraints fail closed to one page/native text; no V4 release/actionability consumer exists |

## Findings

### T081-V4-IA-001 — BLOCKER — packet omits governing implementation inputs

**Violated invariant:** the review packet must bind the slice declaration and
governing design. `manifest.json` binds only `decision.md` and `findings.json`;
`implementation-slice-1.md` and `codex-schema-proposal.md` can change without
invalidating freshness. Rebuild and rerun against explicit review inputs.

### T081-V4-IA-002 — BLOCKER — PostgreSQL permits immutable cross-source evidence

**Violated invariant:** an evidence fragment must be inseparable from its
directive/publication, retained document and content hash, rendition, text
version, and page. Migration 0025 provides only independent FKs. It does not
enforce the directive/document publication pair, document/content-hash pair, or
fragment-to-text/rendition/document/page chain. A direct SQL mismatch is valid
and then protected from correction by immutable triggers. Add composite
constraints or deferred constraint triggers and direct PostgreSQL negative
tests.

### T081-V4-IA-003 — BLOCKER — lifecycle is not a constrained hash chain

**Violated invariant:** every usable fragment has exactly one valid admission
root and cryptographically linked successor events. PostgreSQL accepts arbitrary
64-character event/predecessor hashes, cross-fragment predecessors, multiple
roots, and fragments without admission. The reuse path returns an existing
fragment without checking admission. Enforce the lifecycle graph and canonical
identity, or narrow this slice to a constrained admission record.

### T081-V4-IA-004 — BLOCKER — downgrade has a destructive insertion race

**Violated invariant:** downgrade cannot delete retained evidence. The empty
preflight performs unlocked `EXISTS` reads, then removes triggers and drops the
tables. A concurrent admission can commit after preflight and before DROP.
Acquire insertion-excluding locks before the check and retain them through DDL;
prove the race in two PostgreSQL sessions.

### T081-V4-IA-005 — HIGH — a new rendition is not read back before admission

The creation path trusts `store_bytes` metadata and persists the immutable row.
Only the reuse path reads and rehashes stored bytes. Verify a newly stored PNG
through the configured read path before database persistence and test an
acknowledged-but-corrupt write.

### T081-V4-IA-006 — HIGH — checked-in PostgreSQL verification is stale/incomplete

`verify-t081-postgres-migrations.sh` still expects migration `0024`; the focused
PostgreSQL test is skipped without an opt-in URL and checks immutable mutation
only on `ad_evidence_fragments`. Update the isolated harness to head `0025` and
exercise all four tables plus downgrade/admission concurrency.

### T081-V4-IA-007 — MEDIUM — GET creates and commits immutable artifacts

The page-evidence GET renders, stores, inserts, and commits. Browser prefetch or
retry can therefore create regulatory artifacts and cost. Use an explicit
idempotent mutation endpoint and keep reads side-effect free.

Full required closures and exact evidence are recorded in `findings.json`.

## Verification performed

- Packet freshness before ledger mutation: **1 passed out of 1**.
- Focused SQLite/API suite: **3 passed out of 3**.
- PostgreSQL-focused test invocation in this reviewer environment: **0 passed
  out of 1; 1 skipped** because `PAPRNAV_TEST_POSTGRES_URL` was not supplied.
- Direct inspection covered staged, unstaged, and untracked changes; migration,
  ORM models, evidence service, admin APIs/schemas, storage helpers, frontend
  navigation, focused tests, migration verifier, current V3 consumers, and the
  slice declaration.

The acknowledged orphaned content-addressed PNG after a failed database
transaction does not make evidence actionable and is honestly deferred. The
single-page, native-text-only, no-coordinate, no-decision-binding boundary is
also honestly enforced. Those deferrals do not waive the open integrity and
rollback blockers above.
