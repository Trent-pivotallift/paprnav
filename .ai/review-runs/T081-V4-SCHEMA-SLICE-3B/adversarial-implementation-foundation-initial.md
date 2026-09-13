# T081 V4 Slice 3B — Foundation Implementation Review

Verdict: **FAIL**

Reviewer identity: `/root/v4_s3b_design_adversary`

Exact packet SHA-256:
`64f5de5250e75840ecf53db5680bd59a2e34e10afbd362ebb00e71716ee6a9d6`

Packet currentness passed and the reviewer independently confirmed 28/28 host
tests with one deprecation warning.

## IF-001 — Blocker: generated mapping contract is incomplete and weakly validated

The occurrence DSL omits typed-owner columns, nullability/union branches,
reference targets, and detailed cardinalities. Generated outputs expose the
manifest but do not generate expected-relation logic. The validator accepted
removing D3, changing D2's selector, replacing Q4 identity properties/table,
changing the row domain, and duplicating an algorithm. Later implementations
would therefore recreate three-way drift.

Required closure: encode every approved occurrence, owner column/presence rule,
union, identity, reference target, ordering, and cardinality; validate exact
cross-record semantics; generate executable expectations; add systematic
mutation tests.

## IF-002 — High: forged candidates can exceed 2,000 requirements

`_validated_requirement_sequences()` allocates the expected map before checking
the forged-parent count and accepts 2,001 contiguous requirements. Reject above
`MAX_ARRAY_ITEMS` before allocation with controlled integrity/resource behavior
and require the same future PostgreSQL boundary.

## IF-003 — Medium: generated Python mapping is only shallowly frozen

Nested selectors remain mutable while `MAPPING_DIGEST` stays unchanged.
Recursively freeze generated structures or expose immutable typed records and
test nested mutation failure.

Recommended closure also executes generated SQL in PostgreSQL, verifies exact
terminal-NUL domains, and tests SQL quoting/delimiter safety. No files were
edited by the reviewer.
