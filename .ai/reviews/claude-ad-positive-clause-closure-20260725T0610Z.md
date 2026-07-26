## 1. Findings

### P1 (from `claude-ad-boundary-exact-final-20260725T0550Z.md`) — closed for the exact reported reproductions
`ad_disposition()` (`maintenance_extraction.py:250–270`) no longer runs the complied/inspected regexes against the raw (already end-boundary-bled) `reference_context` — it now runs them against a new `positive_disposition_context(text)` (`:273–278`), which re-derives a boundary from the first delimiter *after* the AD citation via `min(boundaries, default=len(text))`. Re-executing the exact three adversarial inputs quoted in the prior review as confirmed false positives:
- `"AD 2020-01-01 was noted, additional unrelated task complied with per SB 42, AD 2020-02-02 was not complied with."` → `2020-01-01` = `mentioned` ✅ (was `complied`)
- `"AD 2020-01-01 was noted, unrelated inspection complied with per SB 42, AD 2020-02-02 was inspected."` → `2020-01-01` = `mentioned` ✅
- `"AD 2020-01-01 was noted, unrelated task complied with per SB 42."` (single citation, no following AD) → `mentioned` ✅

These match `test_maintenance_extraction.py:172–197` (`test_unrelated_trailing_action_cannot_promote_ad_disposition`), which now exists and passes. Direct C/W, `complied`, and `inspected` claims still resolve correctly (verified: `"AD 2020-01-01 complied with per SB 42."` → `complied`; `"AD 2020-01-01 C/W per SB 42."` → `complied`; `"AD 2020-01-01 inspected per SB 42, no discrepancies noted."` → `inspected`; two-AD same-line case still resolves both correctly). Note: `citation_end_boundary` itself (`:219–230`) still uses `max(boundaries, default=search_end)` — unchanged from the prior review — so `reference_context` (the `text` field surfaced in `adReferences`) still bleeds unrelated trailing clauses; the fix works only because `positive_disposition_context` independently re-narrows before the disposition check.

### P1 regression (new, in `positive_disposition_context`): false `complied`/`inspected` still occurs when **2+ comma/semicolon delimiters** separate the citation from the next AD or end of segment
`citation_boundary_positions()` (`:233–247`) uses `segment.rfind(delimiter, start, end)` for `,`/`;`, which returns **at most one index per delimiter type** (the rightmost occurrence in range) — never all occurrences. `positive_disposition_context` calls `min(boundaries, default=len(text))` intending to find the *first* delimiter after the citation, but if the first comma isn't the last comma in range, it is never in the candidate list at all, so `min()` silently falls back to the later (or last) comma, and the unrelated intervening clause is still included in the positive-context check.

Confirmed by direct execution (not covered by any existing test):
```
"AD 2020-01-01 was noted, unrelated task complied with, per SB 42."
  -> 2020-01-01 resolves to "complied" (should be "mentioned")

"AD 2020-01-01 was noted, unrelated task complied with, per SB 42, additional note."
  -> 2020-01-01 resolves to "complied" (should be "mentioned")

"AD 2020-01-01 was noted, unrelated task complied with, per SB 42, AD 2020-02-02 was inspected."
  -> 2020-01-01 resolves to "complied" (should be "mentioned")   [multi-AD variant]
```
Root cause isolated directly: `citation_boundary_positions("a, b, c", 0, 7)` → `[4]` (only the second comma; the first comma at index 1 is never returned). This is the exact test gap the prior review flagged in its "Missing test coverage" section (citations followed by two-or-more delimiters before the next boundary) — the fix closed the specific reported single-delimiter shape but did not close the underlying multi-delimiter defect class, and it now manifests through `positive_disposition_context` instead of `citation_end_boundary`. This still produces `disposition_candidate == "complied"` and would still suppress `"explicit_compliance_claim_missing"` and flip `status` to `"candidate_satisfied"` in `ad_matching.upsert_match_result` (`ad_matching.py:151–155, 165`) on text that never claimed compliance with the cited AD.

## 2. Open Questions
- None beyond the scope requested — no P2 investigation performed.

## 3. Verification Notes
- Read `maintenance_extraction.py` and `test_maintenance_extraction.py` (both untracked, full) and `ad_matching.py` disposition-consuming logic (`:151–165`).
- Ran `PYTHONPATH=. .venv/bin/pytest -q` in `backend/`: 69 passed.
- Re-executed the three exact false-positive reproductions from `claude-ad-boundary-exact-final-20260725T0550Z.md` directly against `extract_structured_maintenance_data()` — all now correctly resolve to `mentioned`.
- Verified direct C/W, `complied`, and `inspected` positive claims, plus a two-AD same-line case, all still resolve correctly.
- Constructed and executed additional adversarial single-AD and multi-AD inputs with a second comma inserted after the unrelated "complied with" clause — both reproduce the false-positive `complied` disposition.
- Isolated the root cause directly via `citation_boundary_positions("a, b, c", 0, 7)` → `[4]`, confirming `rfind` only ever returns one occurrence per delimiter type rather than all occurrences in range.
- Traced the false `complied` output through to `ad_matching.upsert_match_result`'s compliance-claim gate (`ad_matching.py:151–155`) confirming it would still suppress `explicit_compliance_claim_missing` and yield `candidate_satisfied` (`:165`).

## 4. Brief Summary
The specific P1 false-positive reproductions cited in `claude-ad-boundary-exact-final-20260725T0550Z.md` are fixed via the new `positive_disposition_context` narrowing, and direct C/W/complied/inspected claims (single- and multi-AD) remain correct. However, the fix is incomplete: it relies on `citation_boundary_positions`, which only ever returns the single rightmost occurrence of each punctuation delimiter type rather than all occurrences, so whenever **two or more** commas/semicolons separate the citation from the next AD or end of segment, unrelated trailing "complied"/"inspected" language still bleeds into `positive_disposition_context` and produces the same class of false-positive disposition (confirmed in both single-AD and multi-AD shapes), which can still flip `ad_matching` to a false `candidate_satisfied`. This P1 is not fully closed.