# Q1-Q5 Pre-persistence Implementation Review

Verdict: FAIL.

- Packet SHA-256: `2d4dd1ef04a504bc1e6894c326890c055b08ec74eddc4139ffa602137258d911`
- Reviewer: Codex runtime `/root/v4_s3b_design_adversary`
- Mode: independent, read-only, bounded pre-persistence review
- Host gate: 91 passed
- Generator check: PASS

## Q-IMPL-001 — High

The Q4 document lookup checked only the supplied D-family root IDs and target
node type/proposal/projection. Swapping two document owner keys caused an
action reference for one key to target the other key's D1 node, and both
materialization and verification accepted the common-mode corruption.

## Q-IMPL-002 — Medium

Q selectors, keys, ordinals, evidence, and Q4 prefix/table label were generated
driven, but semantic parents, owner mappings/references/children,
presence/table rules, complete Q4 identity/order/cardinality, and most owner
contract semantics remained handwritten without exhaustive parity checks.

All requested enums/unions, canonical sets, ordered-step sequence and presence,
fixed Q2/Q5 slots, hashes, sequence precheck, evidence, resource checks,
deferred-child boundary, and ordinary typed corruption otherwise held.
Persistence and later families were not treated as implemented.
