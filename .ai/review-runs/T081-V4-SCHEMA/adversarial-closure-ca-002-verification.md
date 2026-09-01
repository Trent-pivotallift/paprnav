# T081-V4-SCHEMA — CA-002 independent phase-1 verification

Reviewer: `/root/v4_schema_adversary`  
Decision on CA-002: **CLOSED**  
Packet inspected before disposition:
`1f642ac865a6173e49f6045226a5cb868659d5656d7d806856e837a92f0af0d0`

## Verified behavior

`scripts/record-review.py --reattest` is limited to the closure stage and
requires:

- current state `closed`;
- an existing closure PASS;
- distinct nonempty reviewer and builder identities;
- a new repository artifact path;
- unchanged closure packet bytes;
- unchanged out-of-scope inventory; and
- a current canonical packet fingerprint.

A current PASS appends a new immutable `closure` review with `reattest: true`
and preserves `closed`. A current FAIL appends an immutable failure with
`reattest: true` and reopens the run to `implementation_reviewed`. Wrong-stage,
wrong-phase, missing-prior-PASS, stale-packet, self-review, and reused-artifact
attempts are rejected before review/state mutation. Stale and reused FAIL
attempts explicitly leave state closed.

## Verification

- closure packet freshness before ledger disposition: **1 passed out of 1**;
- narrow re-attestation/fingerprint regression suite: **10 passed out of 10**
  in 2.54 seconds;
- Python compilation: **3 passed out of 3** files;
- `git diff --check`: passed;
- product code changes: **0**.

The required closure contract is satisfied. This artifact and the CA-002
ledger disposition intentionally make the prior packet stale. No re-attestation
was invoked in phase 1; the builder must rebuild the closure packet exactly
once before the final independent re-attestation.
