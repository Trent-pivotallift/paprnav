# DOC-001 Contract Amendment Review

Verdict: PASS for design authorization; DOC-001 remains implementation-open.

- Packet SHA-256: `905dedbf17a8d6b3ff14f198d5fbdd74a1db15b33c008426346b337557b2f6c1`
- Reviewer: Codex runtime `/root/v4_s3b_design_adversary`
- Mode: independent, read-only, bounded amendment review
- Base: `9ad410b`

The separate closed internal-record c14n-2 profile coherently resolves the
numeric serialization impossibility without widening candidate-source c14n-2.
It permits containers whose leaves are only null, booleans, strings, and
nonnegative integers; rejects negative integers, decimals/floats, NaN,
infinity, and unlisted types; orders object keys by UTF-16/JCS order; preserves
explicit array order; and emits integer JSON tokens without quotes.

The reviewer confirmed that this profile covers ordinal-bearing row
identities, all 22 projection counts, event sequence numbers and null arms,
and correction-binding generation. Existing Slice-3A correction binding bytes
remain unchanged because their string-only preimages use the byte-identical
common subset and their original domain remains frozen.

Implementation closure still requires a dedicated recursive PostgreSQL
serializer. `jsonb::text`, database collation, and ordinary JSONB key order are
not acceptable substitutes. Cross-language fixed byte/hash goldens must cover
ordinal identities, projection counts, root/later events, empty and nonempty
correction binding lists, escaping, UTF-16 astral/BMP ordering, and rejection
of negative/decimal/floating/unlisted values.

No design blocker remains; implementation may continue.
