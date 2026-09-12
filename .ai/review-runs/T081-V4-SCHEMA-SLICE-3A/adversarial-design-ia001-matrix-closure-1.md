# IA-001 Normative Matrix — Holistic Design Reassessment Closure 1

Outcome: **FAIL — one new blocker**  
Reviewer: `/root/v4_s3a_impl_adversary`  
Builder/coordinator: `/root`  
Packet SHA-256:
`bda863e69f285d670a7e3c4df69cda06ea6b045e84273f6980ef674775e317f9`

The reviewer independently closed MA-001 through MA-006. The exact
identity-mapping golden hash recomputed correctly; the data-only DSL,
occurrence/context evidence pair, physical domains, union cardinalities,
`model_or_series` mapping, and product normalized-identity union were accepted.

One new high-severity finding remains:

- **MA-007 — semantic node key width.** Pointer-derived node keys for recursive
  expressions can exceed 255 characters within validator-2's legal depth, but
  the physical appendix specified `varchar(255)`. A valid candidate could fail
  materialization solely because the typed representation was narrower than
  the canonical contract.

Required closure: use unbounded `text` for semantic `node_key` (or prove and
enforce one shared safe bound) and add a positive >255-character pointer vector
through Python materialization, fresh PostgreSQL commit, and verified read.
