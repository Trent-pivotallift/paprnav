# Closure report: T081-V4-SCHEMA-SLICE-3B

## Outcome

Implementation is complete in the unstaged working tree. Independent design
and whole-family implementation reviews passed, all Slice-3B IA-001 owner
families and global invariants are implemented, and the selected external
critic found no blocker, High, or Medium defect. This report is prepared for
independent final closure review; it is not itself a closure attestation,
staged-state attestation, or commit authorization.

## Invariants verified

- The candidate-only obligation projection losslessly materializes all four
  canonical fields: incorporated documents, requirements, recurrence groups,
  and general AMOC authority provisions.
- Every semantic node has exactly one matching physical typed owner. Generic
  datums, typed owners, evidence links, references, child rows, ordering,
  counts, identities, canonical bytes, and hashes agree with the generated
  normative mapping and verified validator-2 candidate.
- PostgreSQL deferred validation reconstructs the graph independently and
  rejects missing, extra, reordered, cross-projection, misclassified,
  differently valued, cyclic, malformed, or self-consistently restamped direct
  SQL graphs. Verified Python reads repeat the reconstruction and fail closed.
- Document/value-assertion unions; requirement/action/branch families;
  expressions and edges; timing, recurrence, relationships, groups/members;
  authority; and Slice-3B correction bindings implement their complete closed
  unions, presence rules, cardinalities, and absence cases.
- Exact evidence owners, purposes, order, inheritance, live lifecycle state,
  application-parent identity/events, correction identities, request
  authority, and audit-event cause chains are verified at commit and read.
- Materialization is default-off, platform-admin-only, idempotent, atomic, and
  uses the same bounded lock order in Python and the direct-SQL request guard.
  Recognized integrity, deadlock, serialization, timeout, and lock failures
  map to controlled API responses; unknown database errors re-raise.
- Detail, reconstruction, and list GETs use one repeatable-read, read-only
  snapshot, never repair or write, and fail closed on evidence, parent,
  owner-graph, identity, hash, reference, ordering, or cardinality drift.
- Migration 0028 preserves Slice-3A correction identities, defaults the new
  gate off, refuses enabled or occupied downgrade, and takes bounded explicit
  projection-root-before-child locks without the reproduced deadlock cycle.
- No released V3, matching, coverage, recurrence, or aircraft due-state reader
  consumes the candidate-only projection, and all five calibration packets
  leave the 19-table released-state snapshot byte-exact.

## Findings disposition summary

The durable ledger contains 55 findings: 53 closed with evidence, two rejected
with evidence, zero open, zero pending, zero deferred, and zero accepted risk.
Independent whole-family implementation closure review 2 passed exact packet
`dab985ad87c8abbaed01cd4f2d3d31ebf16bcbeb4ab594f7ccf2bfda7638e740`
with no residual or scope omission.

Claude external critic artifact
`claude-external-critic-20260913T171021Z.md` reported one Low candidate and no
Blocker, High, or Medium candidate. `T081-V4-SCHEMA-SLICE-3B-CC-001` is
rejected as a closure finding: two single-item GETs do repeat idempotent
verification inside one snapshot, but list performs one verification per row,
no safety/correctness invariant is violated, and Claude itself marked the
optimization optional and unnecessary for closure. The earlier
`T081-V4-S3B-CAL-IMPL-002` counter-finding remains rejected because the
canonical-order fix removed its premise and the mixed correction calibration
continues to pass.

## Verification performed

- Exact current fresh PostgreSQL persistence/concurrency suite on newly
  created and migrated `t081_s3b_persist_am`: **37 passed out of 37**.
- Independent whole-family host V4 regression: **427 passed out of 427**, with
  one declared PostgreSQL-only skip.
- Independent external-critic full non-PostgreSQL backend run: **634 passed,
  101 skipped**, with two existing Starlette deprecation warnings.
- Exact committed-base `9ad410b7c4021244ac36a6fab44b1dd021f5d05c`
  reader: **1 passed out of 1** against fresh upgraded-empty 0028 and rejected
  the first Slice-3B correction binding as required.
- Five calibration packets: exact host round trip and **2 passed out of 2**
  fresh PostgreSQL gates, including byte-exact before/after snapshots of 19
  released V3/matching/coverage/recurrence/due-state tables.
- Parent candidate PostgreSQL regression: **5 passed out of 5**; Slice-3A
  applicability PostgreSQL regression: **24 passed out of 24**; generated
  serializer PostgreSQL matrix: **31 passed out of 31**.
- PostgreSQL catalog parity, direct corruption, hostile anchor re-deferral,
  seven transactional failure phases, nine forced GET/transition snapshots,
  full application/database gate and authority matrices, exact 16,384-digit
  decimal persistence, empty downgrade/re-upgrade, and observed-wait downgrade
  concurrency are included in those durable suites.
- Generated mapping `--check` passed at digest
  `e229c6008f323cb6622e96b286b6ecb93ec7f2be47a5e4dd48bec294af51465d`.
  Python compilation, ledger JSON parsing, packet verification, and
  `git diff --check` passed.

## Final scope reviewed

The reviewed scope is the entire working-tree delta from committed base
`9ad410b7c4021244ac36a6fab44b1dd021f5d05c`, including staged, unstaged, and
untracked files; migration and generated SQL; mapping contract and generator;
ORM, persistence, graph construction, candidate/applicability/evidence
compatibility; API routes, schemas, gates, and session handling; calibration,
host, PostgreSQL, rollout, migration, corruption, concurrency, and failure
tests; and all review artifacts. Independent review also inspected affected
callers, readers, administrative gate behavior, migrations, and released/V3
consumers rather than treating the manifest as a scope boundary.

## Accepted risks and deferred work

None for Slice 3B. Expression/timing evaluation, publication/approval,
released-catalog selection, aircraft matching, compliance credit, due-state
effects, maintenance-shop/UI surfaces, and real AMOC use remain explicitly
out of scope and require later reviewed slices; they are not deferred defects
in this candidate-only persistence slice. The two single-item GET routes may
be profiled later for redundant verification, but this optional internal
optimization does not weaken or defer a Slice-3B invariant.

## Not verified

- No production deployment, production data migration, or destructive
  downgrade against occupied production state was attempted.
- Claude could not independently execute PostgreSQL because its isolated
  environment lacked an unambiguously disposable configured database; its
  static review was layered on the fresh PostgreSQL execution independently
  reproduced by the Codex adversary and builder.
- No evaluation semantics, release/publication workflow, aircraft matching, or
  frontend behavior was implemented or tested because those are outside this
  slice.
- Staging and commit have not occurred. A closure PASS followed by a fresh
  staged-state fingerprint re-attestation is required before commit.
