# Requirement relationship implementation review scope

This is a bounded pre-persistence implementation review for Q7, Q9, and Q10.
It claims the pure construction and verified-read oracle for terminating effects,
termination edges, and prerequisite dependencies. It also includes the candidate
validator correction needed to keep the graph resource rule aligned with the
materializer.

## Normative authority

This review is explicitly bound to
`.ai/review-runs/T081-V4-SCHEMA-SLICE-3B/normative-mapping-matrix.md`, the generated
mapping manifest, and the approved Slice 3B decision. The scope document does not
replace or narrow those authorities.

## In-scope claims

- Q7 exists exactly once for every Q1 at fixed slot 5, uses the full source
  pointer as its semantic key, has the Q1 owner as parent, and owns one-or-more
  non-inherited `termination_clause` evidence links.
- Q7 preserves the exact `none` and `terminates` source unions. `none` forbids
  Q9 edges. `terminates` requires `requirementKeys` while permitting the
  schema-valid empty set. `edge_count` equals the exact canonical Q9 row count.
- Q9 and Q10 are relationship rows, not semantic-node owners. They preserve the
  exact resolved target node/key, canonical ordinal, generated identity preimage,
  ID, and hash. Q10 has fixed `dependency_kind = prerequisite`.
- Requirement-key sets are validated as closed validator-2 stable keys, reject
  duplicates and malformed collection types without leaking Python exceptions,
  and canonicalize in schema-defined set order.
- Expression-state, prerequisite, and termination references are checked as one
  requirement graph. Missing/self/cyclic/cross-family graphs fail closed.
- The candidate validator and obligation materializer both charge the graph
  limit by source occurrences. Repeated targets across relationship families
  cannot evade the 40,000-edge limit through adjacency-set deduplication.
- D, Q, and E dependencies are fully reverified from trusted canonical inputs
  before relationship construction. Verified read rebuilds the complete family
  and rejects missing, extra, duplicated, reordered, cross-target, misclassified,
  differently valued, or restamped rows.
- The generated Q7 owner contract and Q9/Q10 relationship contracts are checked
  at runtime, including exact descriptor and relationship IDs, tables, labels,
  prefixes, identity property order, evidence policy, references, children,
  ordering, and cardinality.

## Builder evidence

- Q7/Q9/Q10-focused obligation tests: 34 passed.
- Candidate graph-limit focused tests: 2 passed.
- Candidate + obligation host regression: 169 passed.
- Python compilation passed for changed candidate, obligation, and test modules.
- Positive coverage includes both Q7 unions, empty and non-empty termination
  sets, canonical set order, exact Q7 semantic identity, exact Q7 evidence-link
  identity, exact Q9/Q10 identity preimages, and independent Q1/Q7 evidence.
- Negative coverage includes malformed source objects/sets/keys, missing or
  duplicated rows, ordering drift, strict ordinal/count type drift, target
  key/node cross-wiring, kind drift, evidence-purpose drift, hash drift, and a
  fully foreign proposal/projection restamp. Malformed-type cases include
  list/dict discriminators and non-JSON `MappingProxyType`/`UserDict` objects at
  both materialization and verified-read reconstruction boundaries.

## Explicitly out of scope

- recurrence-group owners/members and their G3/G4 timing families;
- AMOC authority/value-assertion owners and correction semantic bindings;
- ORM models, migration, PostgreSQL commit-time enforcement and internal-record
  serialization, API materialization/read verification, authorization/audit,
  downgrade, calibration packets, whole-tree closure, staging, or commit.

These remain mandatory Slice 3B gates. `T081-V4-S3B-DOC-001` remains open until
the PostgreSQL canonical serializer and cross-language golden vectors are
implemented and independently reviewed. A pass here is not a final Slice 3B
implementation pass and must not be recorded as one.
