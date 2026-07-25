# Review: Closure of `claude-ad-parser-exact-closure-20260725T0510Z.md` Residual P2

## 1. Findings

Scope confirmed to `backend/app/services/maintenance_extraction.py` (untracked, new — read in full), `backend/tests/test_maintenance_extraction.py` (untracked, new — read in full), `backend/app/services/ad_matching.py` (diff vs HEAD), and the two `.ai` docs. All prior findings from the referenced review were re-verified directly.

### Confirmed closed (as claimed)
- **Period-separated two-AD-per-line bleed** (the specific defect this round targeted): `"AD 2020-01-01 was not complied with. AD 2020-02-02 complied with per SB 123."` now resolves `2020-01-01 → not_complied`, `2020-02-02 → complied`, with correctly bounded `text` for each. Root cause fix: `sentence_boundary_positions()` (`maintenance_extraction.py:244-252`) detects `.` only when followed by whitespace/EOL (`\.(?=\s|$)`), so decimal citations (`43.13`, `91.411`) are excluded but true sentence-final periods are found and used as clause boundaries in `citation_start_boundary`/`citation_end_boundary` (`maintenance_extraction.py:205-241`). Matches `test_ad_disposition_is_scoped_to_each_citation_clause` (`test_maintenance_extraction.py:115-130`), which passes.
- **Unrelated preceding negated-compliance text before the first citation** (the second half of the prior residual finding): `"SB 456 was not complied with, AD 2012-01-02 complied with per note."` now correctly resolves to `complied`, since the comma is now used unconditionally as a fallback boundary (no more asymmetric "trust only if disposition is neutral" guard). Matches `test_maintenance_extraction.py:132-140`, passes.
- Comma-interrupted negation (`"...was not, in fact, complied with."`) and decimal FAR/CFR co-location (`43.13`, `91.411`) both remain correct, verified via existing tests and direct re-execution.
- Full suite: `PYTHONPATH=. .venv/bin/pytest -q` → 68 passed.

### New Finding — P2: abbreviation periods reintroduce the same "unrelated preceding negated text bleeds into the next AD citation" defect the closure round explicitly targeted, via a different trigger

`citation_start_boundary()` (`maintenance_extraction.py:205-221`) and `citation_end_boundary()` (`:224-241`) each check `sentence_boundary_positions()` first and **return immediately** if any match is found, without comparing that position against the closer comma/semicolon fallback in the same range. A sentence-terminator-shaped `.` produced by a common logbook abbreviation (`No.`, `Ref.`, `Approx.`, `Dr.`, `P/N.` — several of which correspond to patterns already recognized elsewhere in this file, e.g. `SERIAL_NUMBER_PATTERN`'s `Ser. No.`, `WORK_ORDER_PATTERN`'s `W.O.`) sits *before* the intended comma boundary and wins unconditionally, causing the boundary to be placed too early and pulling unrelated negated text back into the current citation's clause — exactly the bleed class this closure round was meant to eliminate, just via a new trigger mechanism.

Confirmed by direct execution (not covered by any existing test):
```
"Ser. No. 12345 not complied, AD 2020-02-02 complied with per SB 123."
  -> 2020-02-02 resolves to "not_complied" (should be "complied")
     text = "12345 not complied, AD 2020-02-02 complied with per SB 123."

"Ref. No. 45 not complied, AD 2020-02-02 complied with per SB 123."
  -> same defect

"No. 45 not complied, AD 2020-02-02 complied with per SB 123."
  -> same defect
```
A related, milder instance degrades a genuine `not_complied` to `mentioned` (rather than flipping polarity) when the abbreviation period lands inside the negation phrase itself before a second citation:
```
"AD 2020-01-01 was not per Ref. No. 45 complied with, AD 2020-02-02 complied with per SB 123."
  -> 2020-01-01 resolves to "mentioned" (should be "not_complied")
```

**Direction/severity:** I specifically tested for a false-*positive* path (bled-in text flipping a genuinely negated AD to `complied`) and could not produce one — `ad_disposition()` checks negated patterns before positive ones, and `ad_matching.py`'s `upsert_match_result`/`rank_candidate_entries` (`ad_matching.py:144-152`, `380-391`) only treat `disposition_candidate ∈ {"complied", "inspected"}` as satisfying evidence, so every case above still fails safe to `not_complied`/`mentioned` → adjudication, never to a false `candidate_satisfied`. This is P2, same class/severity as the prior round's residual finding, not P1.

**Root cause / suggested fix:** compute both candidate boundary sets (sentence-terminator positions and comma/semicolon positions) in the same search range and take whichever is closest to the citation (`max(...)` over the combined candidate list for the start boundary, `min(...)` for the end boundary), rather than letting a sentence-boundary match short-circuit the comma/semicolon check.

### Documentation note (attached to the above, not a separate finding)
`.ai/AD_MATCHING_RULES.md`'s new language ("bounded by neighboring AD citations and sentence separators... decimal regulation references... are not sentence boundaries") and the mirrored text in `.ai/DECISIONS.md` D020 describe the guarantee as fully general; neither caveats that a non-decimal, non-regulation abbreviation period (`No.`, `Ref.`, `Approx.`) can still incorrectly out-rank a closer comma boundary. Same pattern as the prior round's doc-vs-implementation gap.

### Missing test coverage
No test in `test_maintenance_extraction.py` exercises an AD-adjacent common abbreviation (`No.`, `Ref.`, `S/N`/`Ser. No.`, `W.O.`) co-occurring with unrelated negated compliance/inspection language on the same line — the exact shape needed to catch this.

## 2. Open Questions

- How likely is a single OCR-merged line to contain both an abbreviation period (`Ser. No.`, `Ref. No.`, `W.O.`) *and* unrelated negated compliance/inspection language *and* an AD citation, versus these being split across separate `clean_lines` entries in practice? This affects real-world exposure, though the mechanism itself is confirmed reachable at the unit level.
- Is a proper clause/sentence tokenizer (raised as an open question in the two prior closure rounds) still planned? This is now the third punctuation-heuristic iteration (char-count → comma/semicolon+period → comma/semicolon-only → whitespace-qualified period-or-comma) to hit an edge case of the same underlying "no true clause boundary detector" limitation.

## 3. Verification Notes

- Read `maintenance_extraction.py` in full (untracked) and `test_maintenance_extraction.py` in full (untracked); read the `ad_matching.py` diff vs `HEAD` and the `.ai/AD_MATCHING_RULES.md` / `.ai/DECISIONS.md` diffs vs `HEAD`.
- Ran `PYTHONPATH=. .venv/bin/pytest -q` from `backend/`: 68 passed.
- Re-executed the exact adversarial inputs from `claude-ad-parser-exact-closure-20260725T0510Z.md` (period-separated two-AD lines, unrelated preceding negated text, decimal FAR/CFR co-location, comma-interrupted negation) directly against `extract_structured_maintenance_data()` — all now resolve correctly, confirming the targeted closure claims.
- Constructed and executed additional adversarial inputs using common domain abbreviations (`Ser. No.`, `Ref. No.`, `No.`, `Approx.`, `Dr.`, `P/N.`) to discover and confirm the new P2 finding above, including probes specifically designed to check for a false-positive (`complied`) path, which was not found — confirming the fails-safe direction and P2 (not P1) severity.
- Traced the fails-safe property through `ad_matching.py:144-152` and `:380-391`, confirming `disposition_candidate` must be exactly `"complied"`/`"inspected"` to contribute to `candidate_satisfied`, so all reproduced bleed cases can only route to adjudication, never to a false match.

## 4. Brief Summary

Both aspects of the targeted residual P2 — period-separated same-line AD citations and unrelated preceding negated-compliance text bleeding into a later citation — are genuinely fixed for the exact shapes previously reported, verified via the new tests and direct adversarial re-execution; comma-interrupted negation and decimal FAR/CFR handling remain correct. However, the specific mechanism chosen (an unconditional "sentence boundary wins if found, else fall back to comma/semicolon" check in `citation_start_boundary`/`citation_end_boundary`) reintroduces the same bleed class through a new trigger: common logbook abbreviations that produce a whitespace-followed period (`No.`, `Ref.`, `Approx.`, `Dr.`) can incorrectly out-rank a closer, correct comma boundary, pulling unrelated negated text into an adjacent AD's clause. This always fails safe (forces `not_complied`/`mentioned`/adjudication, never a false `candidate_satisfied`), so it is P2, consistent with the severity of the finding this round intended to close — but it means the "unrelated preceding negated compliance text no longer bleeds" invariant this pass was scoped to confirm is not fully closed.