# T081-V4-SCHEMA-SLICE-3B timing/recurrence implementation review — initial

**Verdict: FAIL**

**Reviewer runtime identity:** `/root/v4_s3b_design_adversary`

**Reviewed packet SHA-256:** `4c1b741f005c48621ad5e9923c1f0093d5f1037353cd5e052a21b2f6d44e27f2`

The packet hash matched the assignment and
`scripts/verify-review-packet.py --stage implementation` reported `review packet
is current` immediately before this report was written. This verdict is bound
only to that exact packet and its unchanged implementation snapshot. DOC-001,
persistence/PostgreSQL, recurrence groups, later owner families, API, and whole-
Slice-3B closure remain open and were not relabeled complete.

## Findings

### T-IMPL-001 — High — ordinary dataclass equality accepts type-equivalent typed-owner corruption

**Violated invariant.** The in-scope verified-read oracle must fail closed on a
differently typed or differently represented timing graph. A timing term must
carry an arbitrary-precision `Decimal`, never a binary float; integer ordinals
and counts must remain integers rather than booleans or floats. Decision
invariant 18 also forbids binary-float conversion and scale-changing rewrites.

**Exact evidence.** `ObligationTimingTermOwner.interval_numeric` is annotated
`Decimal`; timing and term ordinals and `term_count` are annotated `int`
(`backend/app/services/ad_v4_obligations.py:217-243`). Construction produces
the expected values through `_timing_decimal()` and generated ordinals
(`:1991-2045`). Verification, however, performs no runtime field/type check and
accepts the supplied family whenever ordinary dataclass equality says it equals
the rebuilt family (`:2135-2157`). Python numeric equality deliberately crosses
types: `Decimal("10") == 10 == 10.0`, `Decimal("0") == False`, `0 == False`,
and `1 == True`.

I independently materialized one valid known T1/T5I family and replaced only
the indicated field. `verify_timing_recurrence_family(...)` accepted every one
of these corruptions:

```text
interval_numeric: Decimal("10") -> 10             # int accepted
interval_numeric: Decimal("10") -> 10.0           # binary float accepted
interval_numeric: Decimal("10") -> Decimal("1E+1")
interval_numeric: Decimal("0")  -> False
timing-term canonical_ordinal: 0 -> 0.0 / False
timing-group canonical_ordinal: 3 -> 3.0
timing-group term_count: 1 -> 1.0 / True
evidence-link canonical_ordinal: 0 -> 0.0
```

The existing numeric-drift test changes `Decimal("10")` to
`Decimal("11")`, so it does not exercise equal-valued cross-type or exponent/
scale corruption (`backend/tests/test_ad_v4_obligations.py:1708-1740`).

**Impact.** The claimed complete immutable-family equality is not type-exact.
It can attest a binary float, Boolean, noncanonical numeric representation, or
floating ordinal/count as the exact typed projection. This is a common-mode
hole in the pure materialization/read oracle and directly contradicts the
bounded timing numeric guarantee. It would also conceal an adapter or future
reader that returned the wrong physical type.

**Required closure.** Validate the supplied family with an exact runtime schema
before or as part of comparison. At minimum:

- require `type(interval_numeric) is Decimal`, finite and nonnegative;
- compare its exact intended representation with `_timing_decimal(interval_text)`
  (for example `as_tuple()` if scale/exponent is part of the invariant); if
  numeric scale is intentionally non-authoritative, state that explicitly while
  still rejecting every non-`Decimal` type;
- require `type(value) is int` for all ordinals/counts, thereby rejecting bools
  and floats; and
- apply the same exactness to nested semantic/evidence rows included in this
  bounded family.

Add direct negative tests for equal-valued `int`, `float`, and `bool` numeric
substitutions, float/bool ordinals and counts, zero-to-`False`, and an exponent/
scale-equivalent `Decimal`. Rebuild a fresh packet and independently rerun each
counterexample.

### T-IMPL-002 — Medium — not-applicable timing reason omits the schema's 512-character limit

**Violated invariant.** T4 must preserve the exact validator-2
not-applicable timing union. Its `reason` is `$defs.identifier`, whose length is
1 through 512 (`backend/app/schemas/ad_extraction_v4.schema.json:13-14,49-54`).
The standalone pure constructor claims exact union validation, even though its
normal service input is an already verified candidate.

**Exact evidence.** `_validate_timing_value()` requires only that a
not-applicable reason is a nonempty string (`backend/app/services/ad_v4_obligations.py:1852-1877`).
The surrounding resource walk permits strings through 16,384 characters
(`:466-500`). In direct public-family tests I observed:

```text
reason length 0      -> rejected
reason length 1      -> accepted
reason length 512    -> accepted
reason length 513    -> accepted
reason length 16,384 -> accepted
reason length 16,385 -> rejected by the generic string resource limit
```

The D-family assertion validator already applies the correct 1..512 identifier
bound (`:631-651`), showing the timing behavior is inconsistent with the shared
schema semantics.

**Impact.** Upstream verified-candidate schema validation protects the intended
service path, so this is not currently an invalid-candidate ingress. The bounded
pure constructor and its claimed exact schema oracle nevertheless accept a
schema-invalid timing value, weakening defense in depth and making a future
alternate/internal caller unsafe.

**Required closure.** Enforce `1 <= len(reason) <= 512` for T4 and add exact
512/513 boundary tests through `materialize_timing_recurrence_family()`. Keep the
larger 16,384 global source bound as the pre-allocation outer limit, not as a
replacement for the field's schema limit.

### T-PKT-001 — Medium — the exact implementation packet does not bind the amended normative matrix

**Violated invariant.** A staged implementation review must be reproducible
against the exact approved normative mapping. A missing or unverifiable review
input is a finding under the reviewer brief. This run previously closed design
finding B-002 by binding the matrix to an exact packet.

**Exact evidence.** The current packet's `reviewInputs` list includes
`decision.md`, `findings.json`, and `implementation-timing-recurrence-scope.md`,
but not `normative-mapping-matrix.md` (packet changed-file manifest around lines
2860-2920). The current matrix SHA-256 is
`1497e8b6cf1335eb430a029d7040e816a2eea602f41b70c1571a501e53c22778`,
which differs from the pre-amendment design-attested matrix hash
`7f3fb38f53cb640e53707c76c052822bfb49101e8dbc06d0f3ec0486b4a2a9b3`.
The later DOC-001 amendment review authorizes the internal-record design in
prose but does not record the amended matrix's byte hash.

**Impact.** I inspected the current matrix directly, but packet currentness
would not detect its mutation. A future closure reviewer therefore cannot prove
from this packet alone that it reviewed the same post-amendment normative bytes
used by the builder.

**Required closure.** Add the current complete normative matrix as an explicit
review input in the fresh targeted closure packet and record its digest in the
closure report.

## Other bounded results

- T1 and R1 were produced once under each Q1 at fixed slots 3 and 4. R6 appeared
  only for interval/conditioned recurrence at R1 slot 1. T5I/T5R semantic keys,
  source pointers, parents, ordinals, hashes, and owner references matched the
  generated descriptors.
- Known, unknown, and not-applicable initial timing and all four recurrence
  branches materialized with their required/forbidden children and columns.
  R6 rejected non-known timing. The conditioned recurrence root resolved to
  the already verified EREC root for the same requirement.
- All three timing logic values accepted. The existing suite exercised all 750
  metric/unit/comparator/anchor combinations and independent timing/term
  evidence. Complete-family rebuilding rejected missing, extra, reordered,
  cross-projection, cross-parent, reference, value, hash, evidence, and ordinary
  numeric-value drift in the cases inspected; T-IMPL-001 is the type-equivalence
  exception.
- Canonical decimal syntax rejected leading zeroes, trailing fractional zeroes,
  exponent notation, signs, whitespace, empty fractions, NaN, and infinity.
  `0`, a 16,384-digit integer, and a 16,382-digit fractional scale were parsed
  losslessly without binary floats. Exactly 2,000 terms materialized; 2,001 were
  rejected before term construction by the generated array resource limit.
- D, Q, and E families are reverified from trusted canonical inputs before T/R
  construction. A missing, corrupt, foreign, or restamped expression dependency
  is rejected before recurrence-root lookup. The generated manifest shape pin,
  Python selectors, SQL selector output, evidence policies, union contracts,
  references/children, and physical dataclass column inventories were inspected;
  no additional blocker/high defect was found in the bounded snapshot.

## Verification executed

```text
python3 scripts/verify-review-packet.py --task T081-V4-SCHEMA-SLICE-3B \
  --stage implementation --base 9ad410b --packet .../review-packet.md
-> review packet is current

PYTHONPATH=. .venv/bin/pytest -q tests/test_ad_v4_obligations.py \
  -k 'timing or recurrence'
-> 11 passed, 85 deselected, 1 warning

PYTHONPATH=. .venv/bin/pytest -q tests/test_ad_v4_candidates.py \
  tests/test_ad_v4_applicability.py tests/test_ad_v4_obligations.py
-> 139 passed, 1 warning
```

The green host gates do not include the equal-valued type corruption or
513-character not-applicable reason counterexamples above. No PASS is issued.
