# Internal-record serializer implementation review scope

This is a bounded PostgreSQL-foundation review for the closed internal-record
c14n-2 profile required by `T081-V4-S3B-DOC-001`. It claims byte-identical
Python/PostgreSQL serialization and domain hashing for all internal record
families. It does not claim that migration 0028, ORM tables, deferred
invariants, or APIs are implemented.

## Normative authority

This review is explicitly bound to
`.ai/review-runs/T081-V4-SCHEMA-SLICE-3B/normative-mapping-matrix.md`, the approved
Slice-3B decision, the declarative mapping manifest/schema, and generated Python
and SQL artifacts. The candidate-source `paprnav-ad-v4-c14n-2` profile remains
unchanged and number-free.

## In-scope claims

- Python `obligation_record_bytes` and generated PostgreSQL
  `paprnav_v4_obligation_record(jsonb)` emit the same UTF-8 bytes for the closed
  internal JSON domain: exact built-in objects, arrays, strings excluding
  U+0000, booleans, JSON null, and base-10 integers from 0 through 2147483647.
- Validator-2 source parsing rejects U+0000 in values and keys before the
  PostgreSQL JSONB storage boundary. PostgreSQL independently refuses an
  attempted NUL-bearing JSONB input with SQLSTATE 22P05.
- Negative or larger integers and values whose PostgreSQL JSONB canonical
  numeric text is decimal/nonintegral reject. Python rejects floats, Decimals,
  tuples, arbitrary mappings, container/scalar subclasses, non-string keys,
  cycles, excessive depth, and invalid Unicode through controlled
  `ObligationIntegrityError`.
- Object keys use exact UTF-16 code-unit order. Generated PostgreSQL computes a
  big-endian UTF-16 sort key explicitly, including surrogate-pair ordering for
  astral characters; it does not trust database collation or UTF-8/code-point
  order. Arrays preserve input order.
- String emission agrees for quotes, reverse solidus, control escapes, newline,
  U+2028, BMP non-ASCII, and astral characters.
- Fifteen fixed cross-language goldens cover:
  - ordinal-bearing row identity;
  - the exact 22-count projection envelope;
  - request and authorization payloads;
  - root event integer sequence and both explicit null arms;
  - legacy correction root, reference, and Slice-3A binding preimages;
  - new Slice-3B correction binding and normalized binding-set preimages;
  - UTF-16 and prefix ordering, empty/nested containers, arrays, every scalar
    type, all short control escapes, non-ASCII text, and the maximum integer.
- Each golden pins a literal SHA-256 result over its exact generated domain and
  serialized bytes. PostgreSQL computes the same domain hash independently with
  its native `sha256(bytea)` function.
- The generator owns the SQL functions; `--check` byte-compares the generated
  Python and SQL outputs. Current manifest digest is
  `e229c6008f323cb6622e96b286b6ecb93ec7f2be47a5e4dd48bec294af51465d`.
- PostgreSQL tests execute the exact generated SQL artifact transactionally
  against PostgreSQL 16, then roll it back. They do not substitute a test-local
  implementation.

## Builder evidence

- Python/PostgreSQL serializer matrix: 31 passed.
- Candidate + obligation host regression: 320 passed.
- Generated-artifact reproducibility passed at digest
  `e229c6008f323cb6622e96b286b6ecb93ec7f2be47a5e4dd48bec294af51465d`.
- Python compilation and `git diff --check` passed.
- The initial sandbox-local TCP attempt was denied by the execution sandbox;
  the authorized localhost rerun reached PostgreSQL 16 and passed. This was a
  harness permission issue, not a product or test skip.

## Explicitly out of scope

- Alembic migration 0028 installation/downgrade and fresh-migration testing;
- ORM models or obligation tables;
- deferred commit-time owner/reconstruction/graph/evidence invariants;
- materialization/API authorization, capabilities, request/event persistence,
  stale detection, or verified GET reconstruction;
- five calibration packets, whole-tree implementation/closure review, staging,
  or commit.

The generated SQL functions are the exact artifact intended for migration 0028;
installing them in that migration and verifying the migrated digest remain later
persistence gates. A pass here may close only `T081-V4-S3B-DOC-001`; it is not
an overall Slice-3B implementation pass.
