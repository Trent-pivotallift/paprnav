# DOC-001 bounded implementation review

- Reviewer runtime: `/root/v4_s3b_design_adversary`
- Packet SHA-256: `0d68e447452b6c7c1fc17088016838e43069e3b124565557dba038de54cbce6a`
- Packet currentness: verified
- PostgreSQL reviewed: 16.14
- Review mode: read-only; no files edited
- Verdict: **FAIL — DOC-001 remains open**

## T081-V4-S3B-DOC-IMPL-001 — Blocker — U+0000 makes the claimed string domain impossible through JSONB

The bound profile admitted JSON strings without excluding U+0000. Python
serialized a NUL value as `b'{"value":"\\u0000"}'`, while PostgreSQL rejected
the corresponding JSONB input with SQLSTATE 22P05 before the serializer could
run. The candidate parser also admitted the value even though candidate source
is persisted as PostgreSQL JSONB.

Required closure: exclude U+0000 from the common internal-record string domain;
reject it through controlled Python and validator-2 errors; and add Python,
PostgreSQL-input, candidate-boundary, and nested key/value rejection vectors.

## T081-V4-S3B-DOC-IMPL-002 — High — Python accepts unlisted containers and leaks recursion errors

The Python serializer accepted tuples, `UserDict`, and `MappingProxyType` even
though the packet claimed a closed JSON type domain. A cyclic list leaked raw
`RecursionError`.

Required closure: accept only the exact intended built-in JSON container types,
detect cycles and excessive depth through `ObligationIntegrityError`, and add
top-level and nested tuple/mapping/mapping-subclass/cyclic-list/cyclic-dict
tests.

## Passing evidence

- Generated PostgreSQL serializer suite: 17 passed.
- Candidate plus obligation host gate: 301 passed.
- Generator reproducibility passed at mapping digest
  `3f376f46b0b3f671f52b8a50f249f17cf33d17296e3be38f7f894b1e1d44aeda`.
- Python compilation and diff hygiene passed.
- Independent additional valid UTF-16, prefix, escape, nested-container,
  integer-boundary, and all-domain hash vectors matched.
- Transactional generated-function installation rolled back cleanly.

Executable generated SQL plus PostgreSQL goldens can close DOC-001 before the
migration-installation gate, but only after the admitted Python and PostgreSQL
domains agree. This report closes no finding.
