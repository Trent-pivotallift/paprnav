# T081-V4-SCHEMA-SLICE-3B timing/recurrence targeted closure review 2

**Verdict: PASS**

**Reviewer runtime identity:** `/root/v4_s3b_design_adversary`

**Reviewed packet SHA-256:** `bef4c52d35de0ac16ece8d363f66df34a6cbe394c1dbe5d428c89f99bfc633e3`

The packet hash matched the assignment and
`scripts/verify-review-packet.py --stage implementation` reported `review packet
is current` immediately before this report was written. The packet explicitly
binds `normative-mapping-matrix.md` at SHA-256
`1497e8b6cf1335eb430a029d7040e816a2eea602f41b70c1571a501e53c22778`.

## T-IMPL-001 — PASS

The residual equal-valued type bypass is closed. Before ordinary immutable-
family equality, `verify_timing_recurrence_family()` now gathers every numeric
field in the bounded family—semantic-node ordinals, evidence-link ordinals,
timing-group ordinals and term counts, and timing-term ordinals—and requires
`type(value) is int` plus nonnegative value
(`backend/app/services/ad_v4_obligations.py:2147-2155`). This rejects booleans,
floats, integer subclasses, and negative integers even when Python would compare
them equal to the expected integer.

The separate interval check still requires exact `Decimal` type, finite and
nonnegative value, canonical text reparsing, and exact `Decimal.as_tuple()`
agreement (`:2156-2165`). Ordinary family equality then verifies all remaining
values and ordering against the trusted-source rebuild (`:2166-2177`).

I independently verified that an untouched family with exact `int` ordinals/
counts and exact `Decimal` intervals passes, while every original substitution
now rejects:

```text
interval_numeric: Decimal("10") -> 10 / 10.0 / True
interval_numeric: Decimal("10") -> Decimal("10.0") / Decimal("1E+1")
interval_numeric: Decimal("10") -> negative / NaN / Infinity
interval_numeric: Decimal("0")  -> False / Decimal("-0")
timing-term canonical_ordinal: 0 -> 0.0 / False
timing-group canonical_ordinal: 3 -> 3.0 / True
timing-group term_count: 1 -> 1.0 / True
semantic-node canonical_ordinal: 3 -> 3.0 / True
evidence-link canonical_ordinal: 0 -> 0.0 / False
```

Canonical text/numeric disagreement and noncanonical decimal text also reject.
The durable mutation matrix covers each field class and both the Decimal and
integer type checks (`backend/tests/test_ad_v4_obligations.py:1708-1752`).

T-IMPL-001 is technically closed, subject to coordinator ledger disposition.

## Prior closure remains valid

- **T-IMPL-002:** exact 512-character not-applicable timing reason passes; 513
  rejects through the public constructor. The field-specific schema limit and
  outer source-resource limit remain distinct.
- **T-PKT-001:** the current normative matrix is an explicit packet review input
  and its byte hash is verified by packet currentness.

## Bounded rescan

- T1 and R1 remain exact fixed-slot children of Q1; R6 remains present only for
  interval/conditioned recurrence at R1 slot 1. All timing and recurrence union
  columns and required/forbidden child combinations reconstruct exactly.
- T5I/T5R order, parent references, semantic identities/hashes, evidence order/
  purpose, and conditioned EREC binding remain exact. Trusted D/Q/E dependencies
  are reverified before construction. Missing, extra, reordered, cross-parent,
  cross-projection, restamped, differently valued, and hash/evidence mutations
  fail complete-family equality.
- All three timing logics pass. All 750 metric/unit/comparator/anchor vectors
  remain covered. Exactly 2,000 terms materialize and verify; 2,001 reject via
  the generated array resource limit before term construction.
- Decimal zero, maximum 16,384-digit integer magnitude, and maximum 16,382-digit
  fractional scale remain exact. Leading zeroes, trailing fractional zeroes,
  exponent notation, signs, whitespace, empty fractions, over-limit values,
  nonfinite values, and text/numeric disagreement fail closed.
- Generated occurrence/owner contracts, physical dataclass column parity,
  reference/child policies, and evidence policies remain consistent with the
  byte-bound matrix. No blocker/high finding remains in this bounded T/R slice.

## Verification executed

```text
python3 scripts/verify-review-packet.py --task T081-V4-SCHEMA-SLICE-3B \
  --stage implementation --base 9ad410b --packet .../review-packet.md
-> review packet is current

PYTHONPATH=. .venv/bin/pytest -q tests/test_ad_v4_obligations.py \
  -k 'timing or recurrence'
-> 21 passed, 85 deselected, 1 warning

PYTHONPATH=. .venv/bin/pytest -q tests/test_ad_v4_candidates.py \
  tests/test_ad_v4_applicability.py tests/test_ad_v4_obligations.py
-> 149 passed, 1 warning
```

This PASS authorizes only the bounded pre-persistence T1/T5I/R1/R6/T5R family.
DOC-001, recurrence groups, later owner/edge families, ORM/migration/PostgreSQL,
API, authorization/audit, downgrade, calibration, and whole-Slice-3B closure
remain open and were not reviewed or relabeled complete.
