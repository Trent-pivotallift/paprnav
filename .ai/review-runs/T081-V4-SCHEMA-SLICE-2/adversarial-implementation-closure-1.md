# T081 V4 Schema Slice 2 — adversarial implementation closure 1

## Outcome

**FAIL — 1 passed out of 9 finding gates.**

Reviewer: `/root/v4_schema_adversary`  
Builder: `/root/v4_schema_builder`  
Reviewed packet fingerprint: `f8f548b00a1b4062df3cd5ca72ec94f852be188293451717655fc265866849db`

The packet verified current before review. The coordinator's isolated PostgreSQL
run is credible as **3 passed out of 3 in 2.86 seconds**, with the named
temporary database removed, but the test source does not cover every required
concurrency and corruption case. Aggregate green tests therefore do not close
the implementation gate.

## Findings by severity

### Blockers

- **T081-V4-S2-IA-001 — OPEN.** Violated invariant: every accepted semantic
  graph is typed, unique, and acyclic. The new validator resolves several key
  namespaces, but `backend/app/services/ad_v4_candidates.py:577-579` rejects
  only self-supersession. An executable proposal containing
  `2001-01-01 -> 2002-01-01 -> 2001-01-01` was accepted. The validator also
  omits conditioned-recurrence expression traversal and the contract's
  inline/group timing-conflict rule. Required closure: implement and directly
  test the complete semantic graph/rule matrix, including multi-edge
  supersession cycles and recurrence expressions/conflicts.

- **T081-V4-S2-IA-002 — OPEN.** Violated invariant: schema-declared sets have
  one order-independent canonical byte representation. Two supersession
  objects with the same reviewed composite identity
  `(relationType, predecessorAdNumber, successorAdNumber)` but different
  evidence arrays were both accepted. Because `_normalize` sorts only on that
  tied composite key, reversing those two objects changed canonical bytes.
  Required closure: reject duplicate composite stable identities (not merely
  byte-identical objects), add tie/duplicate vectors for every keyed set, and
  pin bytes/digests.

- **T081-V4-S2-IA-003 — OPEN.** Violated invariant: PostgreSQL independently
  binds immutable audit bytes/hashes to the exact relational claim. Migration
  0026 now binds the major envelopes, but `paprnav_v4_validate_submission`
  does not recompute `auth_claims_hash` from the snapshotted actor/membership/
  organization/role/status/policy columns and does not constrain the policy
  name, policy version, endpoint action, or raw hash. The relationship trigger
  likewise does not require evidence keys to resolve in the new proposal and
  does not reject self/cyclic edges. The current direct-SQL negative changes
  request bytes to `{}`; it does not replay these self-consistently rehashed
  forgeries. Required closure: bind and test each immutable relational field
  and referenced row with one-field-at-a-time rehashed direct-SQL negatives.

- **T081-V4-S2-IA-004 — OPEN.** Violated invariant: all five calibration
  records prove the complete retained-byte -> Slice-1 admission -> V4 storage
  path and their negative semantics at the actual boundary. The positive real
  path is materially improved and reported **5 passed out of 5**, but
  `test_calibration_packet_rejects_required_negative` still calls only the
  fixture-local `_assert_packet_contract`; it does not submit the mutations to
  a validator/store boundary. The retained fragments also remain page-scale,
  so the test does not independently bind every normalized action/timing claim
  to its exact regulatory clause. Required closure: exercise each negative at
  the relevant boundary and make clause-level evidence assertions falsifiable.

- **T081-V4-S2-IA-005 — OPEN.** Violated invariant: the PostgreSQL matrix
  proves the complete reviewed concurrency/integrity/rollback contract. The
  executed 3-test suite covers empty/occupied downgrade, identical-key retry,
  distinct correction origins, immutability, and selected forged envelopes.
  It omits the required same-key/different-payload race, concurrent lifecycle
  transition, reversed overlapping multi-fragment lock order, relationship
  cycle, and occupied-downgrade race. An executable host counterexample also
  created candidate A, candidate B correcting A, then a new submission for A
  correcting B; the cycle was accepted. Required closure: add and run the
  omitted bounded PostgreSQL cases on a fresh isolated database.

### High

- **T081-V4-S2-IA-006 — OPEN.** The implementation now deduplicates and selects
  fragment rows with `ORDER BY id FOR UPDATE`, which is the correct structural
  remediation. The finding's required two-session reversed-order,
  multi-fragment PostgreSQL test is absent; the current PostgreSQL seed creates
  one fragment. Required closure: add that exact bounded concurrency proof.

- **T081-V4-S2-IA-007 — OPEN.** The admin API now exposes all submission and
  relationship provenance and verifies it on read. However, both proposal and
  nested submission collections are loaded without pagination; this does not
  meet the finding's explicit ordering/pagination closure and permits an
  unbounded audit response. Required closure: add stable pagination (or a
  dedicated paginated submission endpoint) and test page ordering, auth denial,
  and integrity failures across pages.

- **T081-V4-S2-IA-008 — OPEN.** Streaming and concrete post-parse limits are
  present. A 10,000-level nested JSON body under the byte cap nevertheless
  raises uncaught Python `RecursionError` from `json.loads`; the parser catches
  JSON/type/value errors only. This violates the stable fail-closed pathological
  input contract and can produce HTTP 500. Required closure: bound nesting
  before recursive decode or translate decoder recursion failure to the
  versioned 413/resource-limit error, with a hostile-depth regression.

### Closed

- **T081-V4-S2-IA-009 — CLOSED.** Relationship canonical identity now includes
  immutable `submissionId`. Host evidence preserves two sequential origins,
  and the coordinator's PostgreSQL matrix preserves concurrent distinct
  origins with separate relationship hashes and no silent collapse.

## Exact verification accounting

- Packet freshness: **1 passed out of 1**.
- Coordinator PostgreSQL execution accepted as run evidence: **3 passed out of
  3**, but incomplete against the required matrix.
- Builder-reported focused host suite: **40 passed out of 40**; not treated as
  dispositive because accepted counterexamples remain.
- Builder-reported Slice-1/V4 calibration: **5 passed out of 5** positive paths;
  negative boundary and clause-level gates remain open.
- Independent finding closure gates: **1 passed out of 9**.
- Independent contract counterexamples: **5 failed out of 5 expected
  fail-closed checks** (supersession cycle, composite-key duplicate rejection,
  tied-set order invariance, candidate correction cycle, hostile JSON depth).

No product code was edited by the reviewer.
