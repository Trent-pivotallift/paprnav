# T081-V4-SCHEMA slice 1 — post-PASS closure diagnostic

Reviewer: `/root/v4_schema_adversary`  
Status: **FORMAL CLOSURE INVALID — REMEDIATION REQUIRED**

## Completed evidence

- CA-001 fingerprint regression suite: **2 passed out of 2**.
- Fingerprint-tool compilation: **5 passed out of 5**.
- Refreshed packet verification before CA-001 disposition: **1 passed out of
  1**, fingerprint
  `1ee1ad81f1d593fb80419598ddf743e4401f74c77e3aafb01f8da32d0266f21e`.
- Pre-attestation validator no longer reported the CA-001 fingerprint
  contradiction.
- Closure PASS was recorded using supported tooling, transitioning state from
  `implementation_reviewed` to `closed`.

## Post-PASS failure

The required validator run immediately after the supported closure PASS did
not pass. Exact result:

`review run is not closable: - working tree changed after packet generation`

The cause is ordering, not the repaired fingerprint algorithm. CA-001 was
`fixed_pending_verification` in the reviewed packet. Independent disposition
changed hash-bound `findings.json` to `closed`, then recorded PASS against the
prior packet fingerprint. Rebuilding the packet would correctly bind that
disposition but would create a new fingerprint not covered by the recorded
closure review.

## T081-V4-CA-002

The supported tool cannot complete the required re-attestation. A closure
review is accepted only from `implementation_reviewed`; the current state is
already `closed`. Review history and state must not be manually edited or
rolled back.

Required remediation is an append-only closed-state closure re-attestation:

1. require an existing closure PASS and a current closure-stage packet;
2. require a new immutable artifact and independent reviewer identity;
3. append a new closure record against the current fingerprint;
4. retain `closed` on PASS and reopen to `implementation_reviewed` on FAIL;
5. reject wrong phase, stale packet, artifact reuse/change, and self-review;
6. prove the final validator accepts the resulting run.

No manual state or review-history mutation was performed. The recorded PASS is
retained as historical evidence, but it is not a valid final attestation for
the current working tree.
