# Review: Closure of `claude-ad-clause-final-closure-20260725T0450Z.md` Findings

## 1. Findings

Ordered by severity. Scope confirmed to `backend/app/services/maintenance_extraction.py` (untracked, new), `backend/app/services/ad_matching.py` (diff vs HEAD), their test files, and the two `.ai` docs.

### Finding #1 (prior P1, comma-interrupted negation) — **Closed**
`NEGATED_COMPLIANCE_PATTERN` / `NEGATED_INSPECTION_PATTERN` (`maintenance_extraction.py:19-35`) now use unbounded `[^\n]*` instead of `[^.;,\n]*`, and `ad_reference_context()` (`maintenance_extraction.py:182-212`) now derives clause boundaries from the nearest comma/semicolon *adjacent to the AD citations themselves* (via `rfind` between `previous_match`/`next_match` and the current match), not from a blind "stop at any comma" rule inside the negation regex. Verified directly:
- `"AD 2024-01-02 was not, in fact, complied with."` → `not_complied` ✓
- Two-AD, mixed order, comma-interrupted negation on one line (both directions) → each AD independently resolves correctly (`not_complied` / `complied`) ✓
- New tests `test_negated_ad_actions_never_become_positive_compliance` (adds the exact comma-interrupted cases from the prior review) and `test_ad_disposition_is_scoped_to_each_citation_clause` (reverse-order two-AD case) cover this and pass.

### Finding #2 (prior P2, decimal FAR/CFR truncation) — **Closed**
`.` is no longer a delimiter candidate anywhere in `ad_reference_context()` — only `,` and `;` are checked (`maintenance_extraction.py:191-193, 200-202, 207-209`). Decimal citations (`43.13`, `91.411`) therefore never truncate clause context. Verified directly and via the new `test_ad_context_preserves_regulation_decimal_and_disposition`, which passes.

### New Finding — P2 (Correctness/precision, fails-safe): period-separated AD citations on the same OCR line still bleed an earlier AD's disposition into a later AD's clause; the requested "cross-AD bleed" invariant is only closed for comma/semicolon-separated citations, not period-separated ones

`backend/app/services/maintenance_extraction.py:199-204` (the `else` branch of `ad_reference_context`, used whenever `previous_match` is not `None`): when no comma/semicolon is found between the previous AD citation and the current one, `clause_start` falls back to `previous_match.end()` — i.e., the *entire* previous AD's own sentence (including its disposition wording) is folded into the current AD's context, with no guard at all (unlike the `previous_match is None` branch, which at least checks `ad_disposition(...) == "mentioned"` before trusting/discarding a found separator).

Because sentences in real logbook entries are commonly period-terminated per AD (e.g., a mechanic writing one sentence per directive on the same physical line), this is a realistic input shape, and it reproduces the exact defect class this closure round targeted — just with `.` instead of `,` as the missed boundary:

```
"AD 2020-01-01 was not complied with. AD 2020-02-02 complied with per SB 123."
  -> AD 2020-02-02 resolves to "not_complied" (should be "complied")
     text = "was not complied with. AD 2020-02-02 complied with per SB 123."

"AD 2020-01-01 was not complied with. Unrelated squawk fixed. AD 2020-02-02 complied with per SB 123."
  -> same result; an intervening unrelated sentence does not help.
```

A related variant of the same root cause exists in the `previous_match is None` branch's guard itself: it only protects the *first* citation in a segment when the preceding text's own `ad_disposition()` evaluates to `"mentioned"`; if that preceding, unrelated text happens to itself contain a negation of "complied"/"inspected" (about a different subject, e.g. `"SB 456 was not complied with, AD 2012-01-02 complied with per note."`), the guard is bypassed (`clause_start` stays `-1`) and the full segment prefix is included, again masking the current AD's genuine positive disposition as `not_complied`.

**Impact / severity:** In both cases the result is always a false *negative* (`not_complied`/`not_inspected` instead of the true `complied`/`inspected`), never a false positive — `ad_disposition()` checks negated patterns before positive ones, so a bled-in negation about an unrelated clause can only push the result toward "not complied"/"needs_adjudication," never toward a false `candidate_satisfied` (`ad_matching.py:147-155`). This is therefore P2 (fails-safe precision loss / unnecessary adjudication of genuinely-complied ADs), not P1 — but it directly matches the review-scope's explicit request to confirm cross-AD bleed is closed, and it is not: it is closed only for comma/semicolon-delimited multi-AD lines, not for period-delimited ones, which is at least as common a shape (`.ai/AD_MATCHING_RULES.md`'s new "Punctuation remains in context so comma-set-off phrases … do not change or truncate the disposition" language does not mention this period gap, and slightly overstates the guarantee).

No test in `test_maintenance_extraction.py` or `test_ad_matching.py` exercises two AD citations on one line separated only by a period, or a first-citation-in-segment preceded by unrelated negated compliance/inspection language.

**Suggested action:** apply the same period-agnostic clause logic symmetrically — either treat `.` as a candidate delimiter too (now that decimal-digit adjacency is no longer a factor, since `.` between AD citations at sentence boundaries is always followed by whitespace+`AD`/capital, distinguishable from `NN.NN`), or extend the "trust the boundary only if the preceding clause's own disposition is neutral" check used for the first citation to the `previous_match is not None` fallback path as well.

## 2. Open Questions

- Is one OCR-merged physical line containing two AD citations separated only by a period (rather than a comma/semicolon) — as opposed to two separate `clean_lines` entries — a realistic OCR/line-segmentation outcome for this system's source documents? If OCR line-splitting reliably keeps one AD per physical line, this new finding's practical exposure is lower than the analysis above suggests (though `split_segments` operates per already-split line, so any OCR line that merges two sentences reproduces it).
- Given this is the third mechanism iteration for clause/negation boundaries (character-count → comma/semicolon+period → comma/semicolon-only), is a real clause tokenizer still planned, as raised as an open question in the prior closure review? The residual issue above is a direct consequence of continuing to use ad hoc punctuation-based boundaries rather than a real sentence/clause parse.

## 3. Verification Notes

- Read `maintenance_extraction.py` in full (untracked, new file) and the diffs of `ad_matching.py`, `test_ad_matching.py` vs `HEAD` (`git diff HEAD -- backend/app/services/ad_matching.py backend/tests/test_ad_matching.py`), plus `test_maintenance_extraction.py` in full (untracked, new).
- Ran `PYTHONPATH=. .venv/bin/pytest -q` from `backend/`: 68 passed (full suite), including the new `test_maintenance_extraction.py` (10 tests) and updated `test_ad_matching.py`.
- Directly exercised `extract_structured_maintenance_data()` with the exact adversarial inputs from the prior closure review (comma-interrupted negation, two-AD mixed-order comma-interrupted negation, decimal FAR/CFR citations co-located with an AD citation) — both prior findings confirmed fixed.
- Directly exercised additional adversarial inputs (period-separated two-AD-per-line with mixed disposition; unrelated preceding negated-compliance text before a first AD citation) to discover and confirm the new residual bleed finding above; traced the causal chain through `ad_disposition()` → `rank_candidate_entries()`/`upsert_match_result()` (`ad_matching.py:147-155`) to confirm it can only produce `needs_adjudication`, never a false `candidate_satisfied`.
- Confirmed `.ai/AD_MATCHING_RULES.md` and `.ai/DECISIONS.md` (D020) diffs describe the intended invariants accurately for the two closed findings but do not caveat the period-separated-citation gap identified above.

## 4. Brief Summary

Both findings from `claude-ad-clause-final-closure-20260725T0450Z.md` are genuinely closed: comma-interrupted negation (including the two-AD-on-one-line case, both orders) now resolves correctly, and decimal FAR/CFR references (`43.13`, `91.411`) no longer truncate the disposition clause — verified both by the new targeted tests and by direct adversarial execution. However, the mechanism chosen to close these (dropping `.` entirely as a clause boundary, and using an asymmetric guard that only protects the first citation in a segment) leaves a residual, previously-untested cross-AD bleed vector: two AD citations separated only by a period on the same physical line, or unrelated negated-compliance text preceding the first AD citation, can still cause an earlier negation to bleed into a later AD's genuinely positive disposition. This always fails safe (forces `needs_adjudication`, never a false `candidate_satisfied`), so it is P2, not P1, but it means the "cross-AD bleed" invariant the task asked me to confirm as closed is only partially closed.