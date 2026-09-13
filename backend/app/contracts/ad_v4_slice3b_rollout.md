# V4 Slice-3B rollout boundary

Migration `20260911_0028` is expand-first and installs
`materializer3b_enabled=false`.

Before enabling Slice-3B, every API replica must run an `0028`-aware binary.
The exact pre-Slice-3B binary at
`9ad410b7c4021244ac36a6fab44b1dd021f5d05c` is supported only while the
upgraded database contains zero Slice-3B correction bindings. Once the first
Slice-3B binding commits, deploying that binary is prohibited.

Operational rollback after activation means disabling the Slice-3B
application and database gates while retaining an `0028`-aware binary. It does
not mean deploying the old reader, selecting V3, or releasing candidate data.
Physical downgrade is permitted only after the migration's disabled-gate and
empty-occupancy checks succeed under its bounded parent-before-child table
locks.
