## 1. Findings

**P1 (`claude-ad-positive-clause-closure-20260725T0610Z.md`) — Closed.**

`citation_boundary_positions()` (`backend/app/services/maintenance_extraction.py:233–246`) no longer uses `rfind` (which only ever returned the single rightmost delimiter in range). It now builds `punctuation_boundaries` via `re.finditer(r"[,;]", segment[start:end])` (`:242–245`), which returns **every** comma/semicolon occurrence in the search window. Directly confirmed:

```python
citation_boundary_positions("a, b, c", 0, 7)  # -> [1, 4]  (previously [4] only)
```

Because `positive_disposition_context()` (`:272–277`) takes `min(boundaries, default=len(text))`, it now correctly resolves to the *first* delimiter after the AD citation rather than silently falling back to a later one.

Re-executed all three exact multi-delimiter reproductions quoted in the flagged review:
- `"AD 2020-01-01 was noted, unrelated task complied with, per SB 42."` → `2020-01-01` = `mentioned` ✅ (previously `complied`)
- `"AD 2020-01-01 was noted, unrelated task complied with, per SB 42, additional note."` → `mentioned` ✅
- `"AD 2020-01-01 was noted, unrelated task complied with, per SB 42, AD 2020-02-02 was inspected."` (multi-AD variant) → `2020-01-01` = `mentioned`, `2020-02-02` = `inspected` ✅

Direct positive claims still resolve correctly (re-verified):
- `"AD 2020-01-01 complied with per SB 42."` → `complied`
- `"AD 2020-01-01 C/W per SB 42."` → `complied`
- `"AD 2020-01-01 inspected per SB 42, no discrepancies noted."` → `inspected`

`test_maintenance_extraction.py:172–213` (`test_unrelated_trailing_action_cannot_promote_ad_disposition`) now asserts the multi-AD multi-delimiter reproduction (`:198–213`) in addition to the single-delimiter cases from the prior fix, and passes.

**Minor test-coverage note (non-blocking):** the automated test suite covers the multi-AD multi-delimiter reproduction but not the single-AD two-comma variant (`"...complied with, per SB 42."`) or the three-comma variant (`"...complied with, per SB 42, additional note."`) as explicit assertions — those two were only verified manually in this review, not encoded as regression tests. Since the underlying root cause (`rfind` → single match) is fully fixed at the `citation_boundary_positions` level, this is a coverage gap rather than a functional gap, but a future regression here (e.g., someone reintroducing a `rfind`/last-match shortcut) would only be caught for the multi-AD shape, not the single-AD shape.

## 2. Open Questions
None — scope was limited to verifying this specific P1; no other edge cases investigated per review instructions.

## 3. Verification Notes
- Read `maintenance_extraction.py` and `test_maintenance_extraction.py` in full (both untracked; confirmed via `git status --short`).
- Confirmed the flagged `rfind` implementation no longer exists (`grep -n rfind` → no matches); `punctuation_boundaries` now built via `re.finditer`.
- Directly executed `citation_boundary_positions("a, b, c", 0, 7)` → `[1, 4]`, confirming both commas are now returned (previously only `[4]`).
- Re-ran all three exact adversarial reproductions from the flagged review directly against `extract_structured_maintenance_data()` — all resolve to `mentioned`/`inspected` as expected, no false `complied`.
- Re-verified direct C/W, `complied`, and `inspected` single-clause positive claims still resolve correctly.
- Ran `PYTHONPATH=. .venv/bin/pytest -q tests/test_maintenance_extraction.py` → 8 passed, including the updated `test_unrelated_trailing_action_cannot_promote_ad_disposition` with the new multi-delimiter multi-AD assertion.
- Ran full backend suite `PYTHONPATH=. .venv/bin/pytest -q` → 69 passed.

## 4. Brief Summary
The P1 is **closed**. The root cause (`citation_boundary_positions` returning only the last delimiter via `rfind` instead of all delimiters) has been fixed by switching to `re.finditer`, so `positive_disposition_context` now correctly narrows to the first delimiter after the citation regardless of how many commas/semicolons follow. All three previously-reported false-positive reproductions (single-AD two-comma, single-AD three-comma, multi-AD two-comma) now resolve correctly, and direct positive compliance/inspection claims remain unaffected. One minor, non-blocking gap: automated regression coverage exists for the multi-AD case but not for the two single-AD multi-comma reproductions from the original report.