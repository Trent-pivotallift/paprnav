# T081 V4 Schema Slice 4 — design closure review 1

Reviewer: `/root/v4_s4_design_adversary`

Exact packet SHA-256:
`f414c2f77d209308916eb52d50d7dc5afe9a513dee0f0f3c7096e450e3b402c3`

Outcome: **FAIL — targeted closure incomplete.**

The reviewer verified all bound input hashes and reviewed read-only against
repository HEAD `4840a0b4bc5d7334ddcf51a80e39c8fa84b7b0c2`.

Closed at design level: B-001, H-001, H-002, H-003, H-004, M-001, M-002,
and M-003.

Still open:

- **B-002:** the exact matrix omits 3A rule-exclusion dependencies; invents a
  supersession target semantic node where only an external projection exists;
  omits several manufacturer/identity-mapping consumption relations; conflicts
  on whether `actionable` means executable or merely source-representable;
  incorrectly treats independently valid timing enums as an executable
  combination; and lets SQL trust rather than reconstruct the frozen authorship
  set.
- **B-003:** S4-I04/I06 still apply acceptance-grade verified projections to
  every draft/signoff, contradicting the designed missing/stale observed-input
  remediation and graph-free rejection path.
- **H-005:** PostgreSQL `FOR KEY SHARE` does not conflict with non-key updates to
  role/status and therefore cannot protect the direct-SQL signoff boundary.

Required closure is limited to those residuals. No new finding ID was opened.
