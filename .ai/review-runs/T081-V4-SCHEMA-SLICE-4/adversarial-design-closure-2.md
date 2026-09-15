# T081 V4 Schema Slice 4 — design closure review 2

Reviewer: `/root/v4_s4_design_adversary`

Exact packet SHA-256:
`f3d597efcc16c0fc8671936217760dfebc15e9ce634ccc6337d628fbd0ec2271`

Outcome: **FAIL — one residual blocker.**

B-002 and H-005 are closed at design level. The packet now separates source
representation from automation authority, contains the missing exclusion and
identity mapping edges, binds external supersession state without invented
nodes, independently derives SQL authorship, and uses actor/membership `FOR
UPDATE` through commit.

B-003 remains open only because the observed-input hash includes `observedAt`
while also serving as the client CAS token. A fresh unchanged observation at a
later time would hash differently. Closure requires a stable input-identity
digest excluding time, separate from the timestamped audit-envelope digest,
with elapsed-time, substantive-change, and two-observation rejection tests.

All previously closed findings remain closed. No new finding ID was opened.
