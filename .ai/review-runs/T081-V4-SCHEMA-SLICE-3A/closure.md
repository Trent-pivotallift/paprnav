# Closure report: T081-V4-SCHEMA-SLICE-3A

## Outcome

Implementation is complete in the unstaged working tree. The design and
holistic implementation gates have passed, IA-001 is closed, and all 29
recorded findings are closed. This report is prepared for independent closure
review; it is not itself a closure attestation or commit authorization.

## Invariants verified

- Validator-v2 candidates remain byte-exact and candidate-only behind both
  application and database gates; validator-v1 reads remain compatible.
- Every applicability semantic node has exactly one matching physical typed
  owner, including incoming and outgoing supersession dependency nodes.
- PostgreSQL commit-time validation rejects missing, extra, reordered,
  cross-projection, misclassified, differently valued, cyclic, malformed, or
  self-consistently restamped graphs.
- Python and PostgreSQL independently reconstruct all four applicability fields
  from typed owners and require equality with the generic datum projection,
  verified parent candidate, restricted-JCS bytes, and hashes.
- Exact evidence, occurrence identity, mapping provenance, reference,
  correction, dependency, audit-event, count, order, cardinality, and
  presence/union invariants are enforced at commit and on verified reads.
- Detail, reconstruction, and list audit reads fail closed and perform no
  repair, flush, or commit; deterministic stale repair remains reachable only
  from the authorized materialization POST.
- No released-catalog or aircraft-matching reader consumes the candidate-only
  Slice-3A projection.

## Findings disposition summary

The durable ledger contains 29 findings: 29 closed, zero open, zero deferred,
zero accepted-risk, and zero rejected. The original blocker IA-001 was closed
by the holistic implementation review in
`adversarial-implementation-ia001-final.md`. IA-002 through IA-005 and all
subsequent design/family findings have their independent closure evidence in
the ledger and immutable review artifacts.

## Verification performed

- Focused applicability plus five-packet calibration host suite: **25 passed
  out of 25**.
- Complete V4 host suite (`api`, `candidates`, base calibration,
  applicability, applicability calibration): **75 passed out of 75**.
- Freshly migrated disposable PostgreSQL `t081_ia001_s`: **24 passed out of
  24**, including clean v1-only downgrade/re-upgrade, concurrency, direct-SQL
  corruption, all family matrices, and global typed reconstruction.
- Five calibration packets: **5 passed out of 5** exact typed/generic/candidate
  subtree round trips with packet-specific cardinality assertions.
- Python compilation for every changed Python product/test/migration file,
  findings/reviews JSON parsing, and `git diff --check`: passed.

## Final scope reviewed

The reviewed scope is the complete working-tree diff from committed base
`28f6be0`, including untracked migration, service, tests, both review-run
directories, routes, configuration, models, API schemas, validator-v2 candidate
logic, and PostgreSQL compatibility tests. The independent reviewer inspected
surrounding consumers rather than relying on selected diffs.

## Accepted risks and deferred work

None for Slice 3A. Published/released applicability, matching, evaluation,
approval, UI, Slice 3B requirement/recurrence/AMOC owners, and authoritative
identity bridges remain explicitly out of scope and require later reviewed
slices; they are not deferred Slice-3A defects.

## Not verified

- No production deployment, production data migration, or downgrade against
  occupied validator-v2/Slice-3A state was attempted.
- The complete repository-wide test suite was not run; the clean host gate was
  the entire V4 surface plus the fresh PostgreSQL Slice-3A suite.
- Staging and commit have not occurred. A staged-state fingerprint review is
  required after closure PASS and before commit.
