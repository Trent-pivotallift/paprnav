# Expression-family implementation review scope

This is a bounded pre-persistence implementation review for the EACT, EBR,
EREC, and EEDGE portion of Slice 3B. It claims only the pure construction and
verified-read oracle for expression owners, semantic nodes, and ordered edges.

## In-scope claims

- All seven closed expression branches are materialized with exact union
  columns: `scope_ref`, `predicate_ref`, `rule_ref`,
  `requirement_state_ref`, `not`, `all`, and `any`.
- Activation, branch-condition, and conditioned-recurrence contexts use their
  exact generated parent, root ordinal, full source pointer, expression path,
  and owning requirement.
- Leaf targets are type-exact. Requirement-state references resolve against a
  fully verified Q family, reject self-reference, and participate in a global
  cycle check. Applicability targets are accepted only through an exact
  proposal/projection/type/key/pointer/id/hash/canonical-bytes carrier.
- Composite-node arity and ordered EEDGE rows are exact. Edge identity uses the
  generated relationship's ordered identity properties and internal record
  canonicalization.
- Generated descriptors, owner columns, union branches, references, children,
  and relationship contracts are checked by the runtime before construction.
- Verified reads independently rebuild from trusted canonical requirements and
  dependencies, then require complete immutable-family equality. Missing,
  extra, reordered, cross-target, restamped, and differently valued graphs
  fail closed.
- Source and graph resource ceilings are applied before emitting a row beyond
  the limit. Full pointers remain lossless beyond 255 characters.

## Dependency boundary

The `ObligationApplicabilityTarget` carrier is not an alternate Slice-3A
verifier. Persistence integration must populate it only from the existing full
verified Slice-3A read path in `ad_v4_applicability.py`; the carrier then checks
that the received identity and canonical bytes are internally exact before E
construction. The final implementation review must trace and test that DB/read
integration. No claim is made here that an arbitrary caller-created carrier is
an authoritative Slice-3A projection.

## Explicitly out of scope for this bounded packet

- timing, recurrence, prerequisite/action/termination graphs, authority, and
  remaining correction bindings;
- ORM tables, migration SQL, deferred PostgreSQL invariants, API routes,
  authorization, audit envelopes, capabilities, and downgrade behavior;
- final whole-tree reconstruction, PostgreSQL cross-language canonicalization,
  disposable-database tests, closure review, staging, or commit.

These are required later Slice-3B gates and remain open. DOC-001 also remains
open until the dedicated PostgreSQL internal-record serializer and golden
cross-language tests exist.

## Builder evidence

- Expression and combined-graph focused host tests: 19 passed.
- Actual validator-2 1,100-hop envelope regression: 1 passed.
- Complete obligation-oracle host tests: 85 passed.
- Candidate + Slice-3A applicability + obligation host regression: 128 passed.
- Generated mapping digest:
  `4bad42e983c765994ab042673a3a8413aa1b4346a18f1ede9af04d024ae135fe`.
