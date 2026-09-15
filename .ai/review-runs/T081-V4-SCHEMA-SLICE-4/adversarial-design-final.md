# T081 V4 Schema Slice 4 — final adversarial design review

Reviewer: `/root/v4_s4_design_adversary`

Exact packet SHA-256:
`96efc7a7c89e853ce6542c4d6a3a42b96879b3c3a23937fbdbe7ec6e85f145e0`

Outcome: **PASS.**

All design blockers and highs are closed. No new finding was identified. The
reviewer verified the packet's decision, finding-ledger, and normative-matrix
hashes against the files.

The final B-003 closure verifies that the stable input-identity hash excludes
wall-clock/request/actor/UI fields, the audit envelope separately retains
`observedAt`, clients CAS only the stable identity, rejections bind requested
and current identity/audit pairs, and tests require elapsed-time stability plus
substantive-change invalidation.

B-002 and H-005 remain closed: the complete dependency/SQL/authorship contract
and actor-then-membership `FOR UPDATE` authorization boundary are intact.
B-001, H-001 through H-004, and M-001 through M-003 remain closed: bounded
candidate-only semantics, shared locking, Slice-5 V3 freeze ownership,
supporting-document deferral, historical verification, conservative authorship,
read-only form coverage, and rollout/downgrade controls did not regress.

This attestation approves the design only. It makes no implementation or test
claim.
