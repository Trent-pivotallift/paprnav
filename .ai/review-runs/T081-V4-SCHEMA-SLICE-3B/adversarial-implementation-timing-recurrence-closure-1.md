# T081-V4-SCHEMA-SLICE-3B timing/recurrence targeted closure review 1

**Verdict: FAIL**

**Reviewer runtime identity:** `/root/v4_s3b_design_adversary`

**Reviewed packet SHA-256:** `d33c2d8b1e18f6a025203b9ce1caa5002a2687e8ed299de446972a1bcc5a411e`

The packet hash matched the assignment and
`scripts/verify-review-packet.py --stage implementation` reported `review packet
is current` immediately before this report was written. The packet explicitly
binds the current `normative-mapping-matrix.md` at SHA-256
`1497e8b6cf1335eb430a029d7040e816a2eea602f41b70c1571a501e53c22778`.

## Finding disposition

### T-IMPL-001 — High — PARTIALLY FIXED; residual type-equivalent integer corruption remains

The new `verify_timing_recurrence_family()` checks every supplied timing term's
`interval_numeric` before family equality. It now requires exact `Decimal`
type, reparses `interval_text`, rejects nonfinite/negative values, and compares
`Decimal.as_tuple()` to preserve sign, exponent, and scale
(`backend/app/services/ad_v4_obligations.py:2147-2156`). I independently reran
the original interval substitutions. The verifier now rejects all of these:

```text
Decimal("10") -> 10
Decimal("10") -> 10.0
Decimal("10") -> True
Decimal("10") -> Decimal("10.0")
Decimal("10") -> Decimal("1E+1")
Decimal("10") -> Decimal("-10")
Decimal("10") -> Decimal("NaN")
Decimal("10") -> Decimal("Infinity")
Decimal("0")  -> False
Decimal("0")  -> Decimal("-0")
interval_text "10" -> "11" with numeric left at Decimal("10")
interval_text "10" -> noncanonical "10.0"
```

That closes the interval-specific part of T-IMPL-001. It does not close the
finding's originally reported and required exactness for integer ordinals and
counts in the nested timing family. The verifier still falls back to ordinary
dataclass equality for every such field (`:2157-2168`), and Python equates
integers with equal-valued floats and booleans.

I reran the original counterexamples against this fresh packet. The current
verifier **accepted** each corrupted family:

```text
timing-term canonical_ordinal: 0 -> 0.0
timing-term canonical_ordinal: 0 -> False
timing-group canonical_ordinal: 3 -> 3.0
timing-group term_count: 1 -> 1.0
timing-group term_count: 1 -> True
semantic-node canonical_ordinal: 3 -> 3.0
evidence-link canonical_ordinal: 0 -> 0.0
```

These substitutions were explicit evidence in the immutable initial report,
whose required closure said to require `type(value) is int` for all ordinals and
counts and to cover nested semantic/evidence rows. The fresh packet binds that
report at SHA-256
`78c04e240fd131bec5a24c22efe69c609ba913754fe5d908565e009d9c51730b`.
The current regression additions cover only `interval_numeric`
(`backend/tests/test_ad_v4_obligations.py:1708-1747`) and therefore do not expose
the residual bypass.

**Impact.** The bounded verified-read oracle can still attest a differently
typed physical graph containing Boolean or floating ordinals/counts as the
exact canonical family. This is the same common-mode type-equivalence failure,
not a new finding, and contradicts the claimed exact typed reconstruction.

**Required closure.** Before ordinary equality, apply a strict runtime schema or
type-aware comparison to every numeric field in the supplied bounded family.
Require `type(value) is int` (not merely `isinstance`) for at least semantic-node
ordinals, evidence-link ordinals, timing-group ordinals and term counts, and
timing-term ordinals. Add direct negative tests for the float and Boolean
substitutions above, then rebuild a fresh packet and rerun them independently.

### T-IMPL-002 — Medium — PASS

`_validate_timing_value()` now enforces the validator-2 identifier maximum for
not-applicable timing reasons (`backend/app/services/ad_v4_obligations.py:1868-1878`).
The public materialization path accepted exactly 512 characters and rejected
513 with `ObligationIntegrityError`. The durable 512/513 test is present at
`backend/tests/test_ad_v4_obligations.py:1829-1842`. The upstream source resource
limit remains an independent outer bound. This finding is technically closed,
subject to coordinator ledger disposition.

### T-PKT-001 — Medium — PASS

The changed-file manifest now lists `normative-mapping-matrix.md` as an explicit
review input with its exact current SHA-256. Packet verification included that
input and returned current. This finding is technically closed, subject to
coordinator ledger disposition.

## Other targeted results

- The original T1/T5I/R1/R6/T5R union, fixed-slot, presence/forbidden-child,
  EREC binding, evidence, identity/hash, missing/extra/reordered/cross-projection,
  and trusted D/Q/E dependency probes remained green.
- `all`, `whichever_first`, and `whichever_later` each materialized exactly.
  Exactly 2,000 timing terms materialized and 2,001 were rejected by the
  generated array resource limit before term construction.
- Canonical decimal `0`, 16,384-digit integer magnitude, and 16,382-digit
  fractional scale remain lossless. Leading zeroes, trailing fractional zeroes,
  exponent notation, signs, whitespace, empty fractions, NaN, infinity, text/
  numeric disagreement, and over-limit inputs fail closed.
- No new blocker/high finding was found in the bounded T/R scan. T-IMPL-001 is
  still open because its original closure scope was only partially implemented.

## Verification executed

```text
python3 scripts/verify-review-packet.py --task T081-V4-SCHEMA-SLICE-3B \
  --stage implementation --base 9ad410b --packet .../review-packet.md
-> review packet is current

PYTHONPATH=. .venv/bin/pytest -q tests/test_ad_v4_obligations.py \
  -k 'timing or recurrence'
-> 16 passed, 85 deselected, 1 warning

PYTHONPATH=. .venv/bin/pytest -q tests/test_ad_v4_candidates.py \
  tests/test_ad_v4_applicability.py tests/test_ad_v4_obligations.py
-> 144 passed, 1 warning
```

The green suites omit the residual ordinal/count type substitutions. No PASS is
issued. DOC-001, persistence/PostgreSQL, later families, API, and whole-Slice-3B
closure remain open and were not reviewed or relabeled complete.
