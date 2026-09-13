# T081-V4-SCHEMA-SLICE-3B — persistence/API implementation review scope

## Requested verdict

Review the complete Slice-3B persistence and API vertical slice against the
approved decision and normative matrix. This is the first whole-family
implementation review; prior family PASS reports were bounded and do not
authorize an overall PASS.

The reviewer is read-only. Inspect staged, unstaged, and untracked files, plus
all parent candidate/Slice-3A callers and readers, migrations, generated
contracts, administration functions, tests, and API boundaries. Treat an
omitted consumer as a finding.

## Invariants that must be reproduced

1. Every semantic node has exactly one matching typed owner and every generic
   datum, evidence link, forward/back reference, ordinal, union branch, count,
   and canonical value reconstructs the four-field source subtree exactly.
2. Direct SQL cannot commit missing, extra, reordered, cross-projection,
   misclassified, differently valued, self-consistently restamped, or
   differently wired owner graphs, including equal-payload child swaps.
3. Python materialization, PostgreSQL commit-time validation, and verified read
   reconstruction agree for every closed branch and nested expression shape.
4. Request and event identities/hashes, actor/membership snapshots, all three
   gates, dense predecessor chains, stale cause type/cardinality/binding, and
   append-once retry behavior are exact.
5. Only verified superseded/quarantined evidence, verified parent
   `stale_marked` events, or verified correction/replacement relationships can
   cause staleness. Admission/materialization roots must fail as false causes.
6. Lock acquisition and expected SQLSTATE handling do not expose supported API
   requests to unhandled integrity, deadlock, serialization, or timeout 500s.
7. The immutable Slice-3A projection accepts only exact structurally valid
   Slice-3B correction bindings and retains its existing identities/hashes.
8. The five real calibration packets pass admitted evidence, validator-2,
   Slice-3A, Slice-3B deferred validation, and exact reconstruction without
   cloning requirements across model lists or inventing aircraft compliance.
9. Generated mapping bytes/digest, migration/ORM catalog, indexes, triggers,
   helper functions, upgrade/downgrade/re-upgrade behavior, and feature-gate
   administration agree.
10. Deferred validation coalesces only initial INSERT callbacks that PostgreSQL
    transaction metadata proves precede the sequence-zero materialized-event
    anchor; the anchor validates once, and any later INSERT/UPDATE/DELETE still
    fails closed even after an immediate→deferred constraint-mode transition.

## Required adversarial emphasis

- Independently probe the Astra findings in
  `builder-preflight-persistence-api-astra.md`; do not accept builder
  dispositions without reproducing them.
- Probe c14n-2 semantic-set order versus stored JSON, mixed 3A/3B correction
  source ordinals, nested expression paths, and constraint-mode transitions
  found by the five-packet calibration gate.
- Attack the xmin/cmin anchor boundary with missing anchors, later writes,
  deletion, re-deferral, and forged/restamped event rows; do not accept the
  performance improvement without proving it cannot suppress final validation.
- Attack direct request/root/child/event insertion and forced lock
  interleavings, not only supported ORM writes.
- Compare ORM and live PostgreSQL catalog semantics rather than constraint
  names alone.
- Verify unknown database failures are re-raised and only the declared
  SQLSTATE set is translated.
- Confirm read reconstruction is non-mutating and fails closed on typed owner,
  identity, evidence, hash, reference, cardinality, and freshness drift.

## Builder gate evidence

The current exact counts and disposable database names are recorded in
`checkpoint.md`. Builder evidence is a starting point only. The reviewer must
run independent focused probes and may reuse fresh disposable databases or
create its own. No staging or commit is authorized by this review.
