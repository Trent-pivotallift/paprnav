# T081-V4-SCHEMA implementation slice 1 — final closure review

Reviewer: `/root/v4_schema_adversary`  
Builder: `/root/v4_schema_builder`  
Decision: **PASS**  
Reviewed packet fingerprint: `abfcf8f02b5ee13c28502030aff0ab129d9df85cbe153479a6c10083e7a408fd`

## Outcome

**8 findings closed out of 8.** No blocker, high, or medium implementation
finding remains open for slice 1. The implementation gate passes for the
declared single-page retained-evidence and relevant-page-navigation boundary.

## Final closure evidence

- IA-001: the current packet explicitly hash-binds the decision, finding
  ledger, governing schema proposal, and implementation declaration. Packet
  freshness passed **1 out of 1** before closure-ledger mutation.
- IA-002: composite PostgreSQL keys/FKs bind directive/publication, retained
  document/hash, rendition, text version, and page. Insert triggers derive
  exact text and canonical identity. Direct-SQL wrong-chain counterexamples are
  rejected.
- IA-003: PostgreSQL enforces one admission root, same-fragment predecessor,
  predecessor sequence, canonical event hash, and unique sequence. Tests reject
  forged hashes, orphan fragments, and a cross-fragment predecessor. Two
  concurrent canonical sequence-1 successors produce exactly one commit, one
  rejection, and one stored successor.
- IA-004: downgrade holds `ACCESS EXCLUSIVE` locks before checking emptiness.
  The two-session test proves downgrade waits for an overlapping evidence
  transaction, then refuses without changing revision or deleting evidence.
- IA-005: newly stored PNG bytes are read back and checked for SHA-256, size,
  PNG structure, and dimensions before an immutable row is flushed.
- IA-006: the current focused PostgreSQL suite executes migration-0025 source
  identity, lifecycle, admission concurrency, downgrade concurrency, and
  UPDATE/DELETE rejection on all four immutable tables. The repository harness
  expects head 0025 and uses isolated databases.
- IA-007: GET is read-only and returns 404 before materialization; explicit
  idempotent POST performs the platform-admin-only mutation.
- IA-008: PostgreSQL rejects `character_end` beyond authoritative text length,
  requires parser provenance to equal the text version, and includes parser
  identity in the canonical fragment hash. Direct-SQL counterexamples execute.

## Verification accounting

- Current packet verification: **1 passed out of 1**.
- Independent reviewer focused API/evidence suite: **5 passed out of 5**.
- Coordinator independent current PostgreSQL suite on fresh
  `paprnav_t081_v4_coord_20260830b`: **2 passed out of 2 in 1.62 seconds**.
- Builder corroborating current PostgreSQL suite on fresh
  `paprnav_t081_v4_slice1_closure3`: **2 passed out of 2 in 1.71 seconds**.
- Both explicit temporary databases were dropped; the coordinator verified
  **0** databases matching `paprnav_t081_v4_%`. `paprnav_db` was untouched.

The PostgreSQL two-test suite includes multiple assertions and counterexamples;
the **2/2** count is test-case count, not assertion count. Inspection mapped
every pending finding to the exact executed assertion before closure.

## Boundary retained

This pass does not approve V4 canonical JSON, normalized applicability or
requirement persistence, decision bindings, publication/cutover, reviewer
forms, OCR, coordinates, or cross-page/table selections. Native-text-empty or
unrenderable pages still fail closed. Existing V3 release behavior remains
unchanged. A failed database transaction may leave an unreferenced
content-addressed PNG, but it cannot become admitted evidence without the
validated immutable rows and lifecycle root.
