# DOC-001 Astra builder preflight

- Runtime: `/root/v4_s3b_q7_edges_preflight`
- Role: builder-side preflight, not independent closure
- Packet SHA-256: `0d68e447452b6c7c1fc17088016838e43069e3b124565557dba038de54cbce6a`
- Files edited: none

The preflight independently found the U+0000 Python/PostgreSQL mismatch later
confirmed by the formal reviewer. It also found that an unbounded 4,501-digit
Python integer leaks the interpreter's integer-to-string `ValueError`, while
PostgreSQL accepts and serializes the numeric value. The internal integer domain
therefore needs an explicit storage-aligned upper bound or an intentionally
unbounded implementation.

The preflight additionally noted that generated-SQL fixture setup occurred
before the fixture cleanup guard, so an installation failure could bypass
explicit rollback, connection close, and engine disposal.

Initial localhost and Docker probes were sandbox-denied. A later authorized
localhost probe installed the exact generated SQL transactionally and rolled it
back. Valid UTF-16/prefix/escape/nested/null vectors matched. PostgreSQL numeric
normalization behaved consistently with the packet's stated JSONB-canonical
numeric rule, but those normalization cases and SQL NULL versus JSON null still
needed pinned tests.
