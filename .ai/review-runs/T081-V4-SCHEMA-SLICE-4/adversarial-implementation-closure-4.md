# T081 V4 Schema Slice 4 implementation closure review 4

Outcome: **FAIL**  
Reviewer runtime: `/root/v4_s4_design_adversary`  
Packet SHA-256: `e4b4a1e0d675bfc2b57e5fc7c978442eb87a1627ebdcdcc0018d52cc7c64526a`  
Base: `4840a0b4bc5d7334ddcf51a80e39c8fa84b7b0c2`

The packet and all 23 manifest hashes remained unchanged. No staged files or
reviewer edits were present.

## M-001 — remains open

Direct applicability and obligation audit preflights work, but the obligation
child does not inherit its exact applicability parent's failed preflight.
Independent PostgreSQL count and byte probes showed an over-budget parent and
within-budget child; applicability returned controlled `integrity_error`, but
obligation reconstruction still loaded the excluded parent's request payload
and returned verified. Queue accounting has the same incomplete dependency.

Required closure: bind child preflight to its exact `app_projection_id` parent,
propagate individually over-budget parent state through every consuming
reconstruction path and page accounting, and add populated count/byte tests
proving parent payloads are not selected indirectly.

## H-003 — closed

The reviewer replayed the exact prior two-byte-remainder case on
`paprnav_s4_closure6`. Request, rejection, and successor all committed; the
rejected case ended at 16,794,784 bytes. A separate probe confirmed historical
reads still use the stored phase and reject corrupt over-budget history even
when a phase-changing event is pending.

M-002, B-001, H-001, and H-002 remain closed. Focused host tests passed 93,
PostgreSQL tests passed 84, the exact lifecycle replay passed, and manifest and
whitespace checks passed. The implementation gate remains closed only on
M-001.
