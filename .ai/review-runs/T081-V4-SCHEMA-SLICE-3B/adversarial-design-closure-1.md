# T081 V4 Slice 3B — Design Closure Review 1

Verdict: **FAIL**

Verified packet SHA-256:
`cd71d30c465dd0b8daef6d34470d25d9d98e51c7762790dde2d56fe6702358a6`

Runtime reviewer identity: `/root/v4_s3b_design_adversary`

## B-002 — Blocker: the exact review packet still does not bind the normative matrix

The manifest binds the decision, findings, domain contract, V4 schema, and two
Slice-3A documents, but not this run's normative mapping matrix. B-001 closure
depends on matrix sections 1.3–1.9, so those bytes must be supplied explicitly
as a review input and covered by the next packet hash.

Required closure: rebuild with
`.ai/review-runs/T081-V4-SCHEMA-SLICE-3B/normative-mapping-matrix.md` as a
review input and obtain a new exact-packet review.

## B-001 — Residual blocker: correction binding set hash undefined

The matrix now defines row identities, semantic slots, 22 immutable counts,
projection/request/auth payloads, event branches, and audit-child exclusion.
However, event payloads contain `correctionBindingSetHash` without defining its
record shape, ordering, canonical bytes, domain, or empty-set value.

Required closure: freeze the binding-set payload, sort key, empty representation,
hash domain/preimage, and positive/corruption goldens.

## H-001 — Residual high: preserved Slice-3A binding prefix is wrong

The amended design says `avc_`; committed construction uses
`_row_id("avk", "correction-binding", ...)`. `avc_` belongs to the correction
root. The contract must preserve `avk_` for both the existing 3A binding and
the new same-table 3B binding.

## M-002 — Medium: requirement sequence needs a pre-conversion rule

The canonical sequence string is schema-unbounded and raw-parser bounded at
16,384 characters. Python integer conversion and PostgreSQL integer storage
must occur only after safe textual comparison to the exact `1..N` set, where N
is capped at 2,000. Add forged-parent and normal-request boundary tests. If the
existing candidate-create path is repaired, add its service to reviewed scope.

## Prior-finding disposition

- H-002: closed by the fixed Slice-3A-compatible order, scoped 3A amendment,
  bounded DDL refusal, and forced interleaving plan.
- H-003: closed by the 16,384-character pre-cast decimal boundary, PostgreSQL
  capacity proof, stable failure, and tests.
- H-004: closed by expand-first rollout and the explicit old-binary boundary.
- M-001: closed by whole-read PostgreSQL repeatable-read snapshots and race
  tests.

No implementation is authorized until the remaining findings close against a
packet that cryptographically binds the normative matrix.
