# T081 V4 Schema Slice 4 implementation closure review 3

Outcome: **FAIL**  
Reviewer runtime: `/root/v4_s4_design_adversary`  
Packet SHA-256: `684ca24c3259a2de7df38e9e22c71cf3d01ee04e2f98876f22b2617ba97288af`  
Base: `4840a0b4bc5d7334ddcf51a80e39c8fa84b7b0c2`

The packet and all 23 manifest file hashes remained unchanged. The reviewer
inspected staged, unstaged, untracked, and surrounding scope without editing.

## H-003 — remains open

The 16/28/40 MiB reserve arithmetic is correct, but an exact two-byte-remainder
PostgreSQL probe still stranded the case. Request creation flushes the request
owner before its phase-changing event; `_finish` then checks stored bytes under
the old draft phase before considering the pending event. The request fails
with `review_integrity`, rolls back, and successor creation remains blocked by
the open case. Rejection uses the same partial-flush pattern.

Required closure: make phase accounting correct across partial flushes or flush
each transition atomically, retain rejection of genuinely corrupt committed
history, and add the exact near-ceiling request/rejection/successor regression.

## M-001 — remains open

The scalar authorship/cutoff/frozen-source queries, head-only cutoff,
lifecycle row/reason preflight, and bounded local lifecycle verifier are
verified. A surrounding projection path remains unbounded: review observation
calls obligation reconstruction, which loads every materialization request,
including its byte payload, with no count/byte preflight. A real projection
with three valid repeated requests remained verified while the observed query
had no limit and selected both canonical payload columns.

Required closure: preflight accumulating projection reconstruction inputs,
including materialization requests and projection event history, before payload
loads; use a stable nonverified branch when over budget; test the real populated
projection path with repeated valid requests.

## M-002 — closed

The rollback suite now compares both complete inherited function definitions,
verifies helper removal, and tests both reviewer gates independently. The
reviewer ran all four tests on fresh `paprnav_s4_reviewer_rollout5`; all passed.

## Verification

- Focused host review/service/storage: 93 passed.
- PostgreSQL migration/lock/service: 83 passed.
- Independent fresh rollback: 4 passed.
- Exact near-ceiling probe reproduced H-003.
- Populated projection trace confirmed residual M-001.
- Manifest and whitespace checks passed.

Earlier B-001, H-001, and H-002 remain closed. The implementation gate remains
closed on H-003 and M-001.
