# Review: `citation_boundary_positions`/`citation_start_boundary`/`citation_end_boundary` — closure verification for `claude-ad-boundary-closure-20260725T0530Z.md`

## 1. Findings

### Targeted P2 (abbreviation period vs. closer comma) — confirmed closed for the reported cases
`citation_boundary_positions()` (`backend/app/services/maintenance_extraction.py:233-247`) now computes sentence-terminator positions (`\.(?=\s|$)`, excluding decimals) and comma/semicolon positions together and returns the combined list, rather than short-circuiting on a sentence match. `citation_start_boundary()` (`:205-217`) takes `max(boundaries)`, correctly selecting whichever candidate — abbreviation period or comma — sits closest to (i.e., highest index before) the citation start. Re-executed all three adversarial inputs from the prior review directly:
- `"Ser. No. 12345 not complied, AD 2020-02-02 complied with per SB 123."` → `2020-02-02` = `complied` ✅ (previously `not_complied`)
- `"Ref. No. 45 not complied, AD 2020-02-02 ..."` → `complied` ✅
- `"No. 45 not complied, AD 2020-02-02 ..."` → `complied` ✅
- `"AD 2020-01-01 was not per Ref. No. 45 complied with, AD 2020-02-02 ..."` → `2020-01-01` = `not_complied` ✅ (previously degraded to `mentioned`)

`test_maintenance_extraction.py:142-150` (`abbreviation_result`) exercises exactly this case and passes. Period-separated same-line ADs (`test_maintenance_extraction.py:115-130`) and decimal FAR/CFR co-location (`test_maintenance_extraction.py:153-169`) both remain correct on re-execution. Full suite: `PYTHONPATH=. .venv/bin/pytest -q` → 68 passed.

### P1 (new, unaddressed): `citation_end_boundary` reuses `max()`, but the end direction requires the *nearest* boundary, not the farthest — reintroduces cross-delimiter bleed, this time with a confirmed false-positive path

`citation_start_boundary()` correctly wants the **rightmost** (closest-to-citation) boundary within `[search_start, citation_start)`, so `max(boundaries)` (`:216`) is correct there. `citation_end_boundary()` (`:219-230`) calls the exact same `citation_boundary_positions()` helper over `[citation_end, search_end)` and also takes `max(boundaries, default=search_end)` (`:230`) — but for the end direction, the boundary closest to the *current* citation is the **leftmost** (minimum-index) one, not the rightmost. `max()` here picks the delimiter closest to the *next* citation (or the very last delimiter in the segment when there is no next citation), so whenever **two or more** commas/semicolons/sentence-periods occur between the current citation and the next boundary, everything up to the far delimiter — including unrelated intervening text — is folded into the current citation's context.

Confirmed by direct execution (not covered by any existing test), including a reproduction of a genuine false-positive disposition flip:

```
"AD 2020-01-01 was noted, additional unrelated task complied with per SB 42, AD 2020-02-02 was not complied with."
  -> 2020-01-01 resolves to "complied" (should be "mentioned")
     text = "AD 2020-01-01 was noted, additional unrelated task complied with per SB 42"

"AD 2020-01-01 was noted, unrelated inspection complied with per SB 42, AD 2020-02-02 was inspected."
  -> 2020-01-01 resolves to "complied" (should be "mentioned")

"AD 2020-01-01 was noted, unrelated task complied with per SB 42."   (single citation, no following AD)
  -> resolves to "complied" (should be "mentioned")
```

**This is a genuine false-positive path, distinct in severity from the prior round's P2.** `ad_matching.upsert_match_result` (`backend/app/services/ad_matching.py:151-155`) only avoids appending `"explicit_compliance_claim_missing"` when `strongest_evidence.disposition_candidate ∈ {"complied", "inspected"}`, and `status` becomes `"candidate_satisfied"` (`:165`) when there are no unresolved reasons — i.e., this bug can directly produce a false `candidate_satisfied` AD compliance determination from a logbook line that never actually asserted compliance with the cited AD. This is exactly the failure mode the prior review explicitly checked for and did not find in the abbreviation-period case; it now exists via a different mechanism in the same helper this round modified.

The bug is not confined to multi-citation lines: as shown above, it also affects the *last* (or only) citation on a line whenever any trailing comma-delimited clause after it contains compliance/inspection language, since `search_end` defaults to `len(segment)` and `max()` walks all the way to the final delimiter in the remaining text.

**Suggested fix:** `citation_end_boundary` should take `min(boundaries, default=search_end)` (the boundary nearest `citation_end`), not `max(boundaries, default=search_end)`.

### Missing test coverage
No test in `test_maintenance_extraction.py` exercises a citation followed by **two or more** delimiters (comma/semicolon/sentence-period) before hitting the next citation or end-of-segment — the exact shape needed to catch this. All current end-boundary tests use exactly one delimiter between the citation and the next boundary, which is why `max()`/`min()` are indistinguishable in the existing suite.

## 2. Open Questions
- Was `citation_end_boundary`'s `max()` intentional (e.g., an assumption that only one delimiter would ever separate the citation from the next boundary), or a copy/adjust mistake when the shared `citation_boundary_positions()` helper was factored out from what was previously two separate direction-aware functions?

## 3. Verification Notes
- Read `backend/app/services/maintenance_extraction.py` (untracked, full) and `backend/tests/test_maintenance_extraction.py` (untracked, full).
- Ran `PYTHONPATH=. .venv/bin/pytest -q` from `backend/`: 68 passed.
- Re-executed the three exact adversarial inputs quoted in `claude-ad-boundary-closure-20260725T0530Z.md` (abbreviation-period cases) directly against `extract_structured_maintenance_data()` — all now resolve correctly, confirming the closure claim for those inputs.
- Re-executed period-separated two-AD and decimal FAR/CFR test inputs — both remain correct.
- Constructed and executed additional adversarial inputs with two delimiters between a citation and the next boundary (or end of segment) to discover and confirm the new P1: traced the false-positive `"complied"` output back to `citation_end_boundary`'s `max()` call (`maintenance_extraction.py:230`) via `citation_boundary_positions()` (`:233-247`), and confirmed the resulting `disposition_candidate == "complied"` would satisfy `ad_matching.upsert_match_result`'s compliance-claim check (`ad_matching.py:151-155, 165`), producing a false `candidate_satisfied` path.

## 4. Brief Summary
The specific residual P2 targeted by this closure round — a closer comma/semicolon losing to an earlier abbreviation period — is genuinely fixed for all reported cases, and period-separated ADs plus decimal FAR/CFR handling remain correct (68/68 tests pass). However, the fix's shared `citation_boundary_positions()` helper is direction-agnostic while the two callers need opposite selection rules: `citation_start_boundary`'s `max()` is correct, but `citation_end_boundary` reuses the same `max()` when it needs `min()`. This reintroduces the "unrelated text bleeds into an AD's clause" defect class through a new trigger (two-or-more delimiters between a citation and its right boundary), and — unlike the previously closed P2 — this variant produces confirmed **false-positive** `complied`/`inspected` disposition candidates that can flip `ad_matching`'s `candidate_satisfied` status on logbook text that never claimed compliance. Recommend fixing to P1 before relying on this closure.