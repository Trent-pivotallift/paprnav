# Findings

Ordered by severity. Scope: the clause-scoped AD-citation disposition fix in `backend/app/services/maintenance_extraction.py` (new `ad_reference_context()` + unbounded, comma/semicolon/period-bounded negation regexes) and the coherence of `matcherStatus` in `backend/app/api/routes/ads.py`.

## 1. [P1 — Correctness/AD-compliance false positive, reintroduces the invariant this round was meant to close] A single comma-set-off aside between the negation word and "complied"/"inspected" defeats the negation guard entirely

`backend/app/services/maintenance_extraction.py:19-27` (`NEGATED_COMPLIANCE_PATTERN`, `NEGATED_INSPECTION_PATTERN`, both `[^.;,\n]*`), combined with the new `ad_reference_context()` (`maintenance_extraction.py:177-196`) which is now the sole basis for disposition text.

This round correctly fixed the two P2 findings from the prior closure review (cross-clause/cross-AD negation bleed, and the 48-character hard cutoff — verified via `test_ad_disposition_is_scoped_to_each_citation_clause` and the modal-negation test, both pass). However, in doing so it swapped one arbitrary boundary (character count) for another (nearest comma), and the new boundary is *easier* to trigger with ordinary phrasing than the one it replaced. Because the negation patterns stop at any comma, a logbook line that inserts a parenthetical between the negation and the verb is no longer recognized as negated and falls through to the positive match. Verified directly:

```
"AD 2020-01-01 was not, in fact, complied with."
  -> dispositionCandidate: "complied"   (should be not_complied)

"AD 2020-01-01 was not, per the mechanic, complied with; AD 2020-02-02 complied with per SB."
  -> both AD 2020-01-01 and AD 2020-02-02 resolve to "complied"
     (2020-01-01 should be not_complied)
```

Impact: `dispositionCandidate` feeds `ad_matching.py:151-155` (`strongest_evidence.disposition_candidate not in {"complied","inspected"}`), so this can produce a false `candidate_satisfied` result for a verified logbook entry — the exact "negated statements are never positive compliance evidence" invariant stated in `.ai/AD_MATCHING_RULES.md:91-95` is violated. This is a genuine regression class introduced by this specific fix: the *previous* round's residual defect required an unrealistic 85+ character negation-to-verb gap (rated P2, "residual/unlikely"); this round's defect only requires one ordinary comma-delimited interjection ("in fact," "per the mechanic," "at this time," "understandably," etc.), which is common phrasing and also a realistic OCR artifact (spurious commas from handwriting/scan noise). No test exercises this shape — `test_negated_ad_actions_never_become_positive_compliance` and `test_ad_disposition_is_scoped_to_each_citation_clause` both avoid any comma between the negation word and the verb.

**Action:** don't use a bare comma as an unconditional hard stop inside the negation lookahead; either tolerate a single bounded comma-delimited interjection, or do a real clause/dependency check anchored on the negation word and its governing verb rather than character-class punctuation exclusion. Add regression tests for comma-interrupted negation, including the two-AD/mixed-order case.

## 2. [P2 — Precision regression, fails safe] Decimal points in ordinary regulation citations (e.g. `43.13`, `91.411`, `91.413`) are treated as clause-ending periods, truncating the citation context before the disposition wording is ever seen

`backend/app/services/maintenance_extraction.py:187-192` (`clause_end_candidates` searches for a bare `.` with no digit-adjacency check).

Verified directly:

```
"AD 2020-01-01 IAW FAR 43.13 was not complied with."
  -> dispositionCandidate: "mentioned", text: "AD 2020-01-01 IAW FAR 43."

"AD 2020-01-01 per FAR 91.411 was not inspected."
  -> dispositionCandidate: "mentioned", text: "AD 2020-01-01 per FAR 91."
```

The decimal point in the CFR/FAR citation is treated as a sentence boundary, so the clause is truncated mid-citation and the actual disposition text ("was not complied with" / "was not inspected") is entirely excluded from `text`/disposition parsing. This fails safe here (result is the neutral `"mentioned"`, not a false `"complied"`), so it is not a P1 safety issue, but it is a real precision loss: this file's own inspection-type detection explicitly anticipates `91.411`/`91.413`/`43.13`-style citations as normal input (`maintenance_extraction.py:63-70`), so this is a common, not contrived, shape for these entries, and every such genuinely-complied AD citation will be under-scored (0.45 vs 0.82 in `ad_matching.py:388-397`) and pushed into unnecessary adjudication. This is newly introduced by this round's clause-scoping mechanism (the prior whole-segment `ad_disposition()` approach did not truncate context at internal periods). No test coverage exists for AD citations that share a segment with a decimal-bearing regulation reference.

**Action:** exclude decimal points between digits from clause-boundary detection (e.g. only treat `.` as a boundary when not immediately flanked by digits, or require a following space + capital letter/EOL), and add a regression test for an AD citation co-occurring with a `NN.NN`-style regulation reference.

## Verified as coherent (no new issues found)

- `list_aircraft_matches` `matcherStatus` (`backend/app/api/routes/ads.py:121-160`): traced `not_run` (no matches, no completion event, no stale rows) vs `current` (matches present, or a current-version completion event even with zero matched directives — the `directives_seen == 0` case) vs `pending_recomputation` (empty current-version matches but a stale-version row exists) and confirmed each state is reachable and mutually exclusive as implemented; both new tests (`test_match_status_distinguishes_not_run_from_current_empty`, the stale-version block in `test_ad_matching_creates_evidence_and_unresolved_review_tasks`) pass and match the code paths. `ADMatchResultListResponse`/`api.ts` fields agree exactly. This portion is unchanged from the prior closure round and not reopened here.
- `test_ad_disposition_is_scoped_to_each_citation_clause` (both forward and reverse order) genuinely passes and the underlying comma-scoping logic (`ad_reference_context`) correctly isolates each AD's own clause when the negation/positive words sit adjacent to the verb (no interposed comma) — the prior review's specific reported scenarios are fixed.
- Full backend suite passes: 67/67.

# Open Questions

- Is a single physical logbook line citing 3+ ADs with one shared trailing disposition (e.g. `"AD X, AD Y, and AD Z were all complied with per SB 456."`) a realistic shape for this system's source documents? Current behavior gives the first N-1 citations `"mentioned"` (fails safe, verified directly) rather than `"complied"`, which is consistent with the documented "each AD's disposition parsed from its own bounded clause" rule, but is a known precision limitation worth tracking rather than a regression.
- Given Finding #1 and #2 are both consequences of using bare punctuation characters as clause/negation boundaries, is a proper sentence/clause tokenizer (rather than incremental regex patching) planned before this matcher is trusted for `candidate_satisfied` at higher confidence/lower review-friction settings?

# Verification Notes

- Read `backend/app/services/maintenance_extraction.py`, `backend/app/services/ad_matching.py`, `backend/app/api/routes/ads.py`, `backend/app/schemas/ads.py`, `frontend/paprnav-frontend/src/lib/api.ts`, `backend/tests/test_maintenance_extraction.py`, the relevant diff of `backend/tests/test_ad_matching.py`, `.ai/AD_MATCHING_RULES.md`, `.ai/DECISIONS.md` (D020) in full.
- Read the four prior review checkpoints (`claude-ocr-ad-critical-*`, `claude-ocr-ad-streamed-*`, `claude-ocr-ad-closure-*`, `claude-ocr-ad-final-closure-*`) to confirm this round is the direct response to the `claude-ocr-ad-final-closure` P2 findings (cross-clause/cross-AD bleed and the 48-char cutoff), and confirmed both of those specific findings are genuinely closed.
- Ran `PYTHONPATH=. .venv/bin/pytest -q` from `backend/`: 67 passed.
- Directly exercised `extract_structured_maintenance_data()` with adversarial inputs not in the test suite (comma-interrupted negation, mixed-order two-AD lines with interrupted negation, decimal-bearing regulation citations co-located with an AD citation) to confirm Findings #1 and #2 reproduce as described.
- Traced `dispositionCandidate` → `rank_candidate_entries()` (`ad_matching.py:388-397`) → `upsert_match_result()` (`ad_matching.py:150-155`) to confirm Finding #1's false `"complied"`/`"inspected"` value would suppress `explicit_compliance_claim_missing` and, combined with a `review_status == "verified"` entry and matching normalized AD number, is sufficient to reach `status = "candidate_satisfied"` — the same causal chain confirmed in the prior review round, unchanged by this fix.
- Confirmed via direct execution that Finding #2 (decimal-point truncation) resolves to the neutral `"mentioned"` disposition rather than a false positive, so it is scored P2/fails-safe rather than P1.

# Brief Summary

The clause-scoping rework genuinely closes both P2 findings from the prior closure round: AD disposition is now correctly scoped per explicit citation (verified for both citation orders on one line, including comma-separated mixed positive/negative claims), and the negation guard no longer relies on a fixed character-count cutoff. The `matcherStatus`/`not_run`/`current`/`pending_recomputation` response states remain coherent and were not touched or reopened here. However, the mechanism used to achieve clause scoping — treating bare commas and periods as hard boundaries — introduces two new issues: (1) a P1 fails-*unsafe* regression where a single ordinary comma-delimited aside between a negation word and "complied"/"inspected" defeats the negation guard and can produce a false `candidate_satisfied` result, which is a more easily-triggered instance of the exact defect class this work was meant to eliminate; and (2) a P2 fails-safe precision regression where decimal points in routine regulation citations (`43.13`, `91.411`, `91.413`) prematurely truncate the citation clause and hide genuinely-present compliance language, degrading matcher confidence/adjudication load for common, expected input shapes. Neither is covered by the current test suite.