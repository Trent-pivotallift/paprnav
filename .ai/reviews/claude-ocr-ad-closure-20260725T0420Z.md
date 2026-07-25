# Findings

## Confirmed Issues (ordered by severity)

### 1. [P1 — Correctness / AD-compliance false positive] Negation guard for AD disposition is materially incomplete; modal-verb negations still resolve to a positive "complied"/"inspected" claim
`backend/app/services/maintenance_extraction.py:19-35` (`NEGATED_COMPLIANCE_PATTERN`, `NEGATED_INSPECTION_PATTERN`) and `ad_disposition()` at `maintenance_extraction.py:167-186`.

This is the fix for the prior review's blocking finding #1 ("negation is not handled in disposition classification"), and it correctly handles the literal phrasings it was tested against (`"was not complied with"`, `"did not comply"`, `"has not yet been complied with"`, `"was not inspected"`, `"inspection was not completed"` — see `test_maintenance_extraction.py:55-67` and `.ai/AD_MATCHING_RULES.md`). However, the regexes require the negation word to sit *immediately* next to "complied"/"comply"/"inspected" (`not(?:\s+yet)?\s+complied`, `did\s+not\s+comply`, etc.), so any modal-auxiliary phrasing that inserts an extra word between the negation and the verb bypasses the guard entirely and falls through to the positive match (`\bcomplied(?:\s+with)?\b` / `\binspect(?:ed|ing)?\b`). Verified directly against `ad_disposition()`:

```
'AD 2012-01-02 will not be complied with until parts arrive'      -> "complied"
'AD 2012-01-02 cannot be complied with due to parts backorder'    -> "complied"
'AD 2012-01-02 is not going to be complied with at this time'     -> "complied"
'AD 2012-01-02 will not be inspected until parts arrive'          -> "inspected"
'AD 2012-01-02 cannot be inspected at this time'                  -> "inspected"
```
(only variants containing `has/have/had ... been complied` or a bare `not complied`/`not inspected` immediately adjacent are caught — see confirmed-good cases in `test_negated_ad_actions_never_become_positive_compliance`).

Impact: this feeds directly into `rank_candidate_entries()` (`ad_matching.py:384-390`, disposition in `{"complied","inspected"}` scores `0.82`) and `upsert_match_result()` (`ad_matching.py:143-154`), where `disposition_candidate in {"complied","inspected"}` suppresses `explicit_compliance_claim_missing`. If the entry's `review_status == "verified"` and the AD number normalizes/matches, the result reaches `candidate_satisfied` with confidence `> 0.8` for a logbook line that explicitly states the AD is **not** complied with — i.e. the exact false-positive-compliance failure mode the `0.3.0` matcher rewrite (D020) was meant to close, reproduced via a very ordinary phrasing style ("will not be complied with...pending parts", "cannot be inspected until...") that's common in real logbooks. Not covered by any test.

**Action:** broaden the negation patterns to tolerate an intervening modal/auxiliary (`\bnot\b.{0,20}?\b(?:complied|comply)\b`-style with a bounded gap, or an explicit list of `be|going to|able to|elected to` insertions), and add regression tests for `"will not be complied with"`, `"cannot be complied with"`, `"is not going to be complied with"`, and the inspected equivalents.

### 2. [P2 — Product/operational gap] Filtering the match-list API by current `algorithm_version` hides stale results but has no reprocessing signal or trigger
`backend/app/api/routes/ads.py:100-105` (new `ADMatchResult.algorithm_version == ALGORITHM_VERSION` filter) and `backend/app/services/ad_matching.py:30` (`ALGORITHM_VERSION = "0.3.0"`).

This correctly closes the prior review's finding #2 in the safe direction — an aircraft's UI/API view will never again show a stale `candidate_satisfied` computed under an older, looser algorithm version (verified by the new stale-row test in `test_ad_matching.py:118-152`, which inserts an `algorithm_version="0.1.0"` row and asserts it's excluded). But there is still no automated re-matching trigger: `match_aircraft_ads` is only invoked from the manual CLI worker (`backend/app/workers/ad_matching.py`) or tests — grep confirms no call site from ingestion, extraction-approval, or a scheduled job. `ADMatchResultListResponse` (`backend/app/schemas/ads.py:152-153`) also carries no "stale/pending reprocessing" flag. Net effect: any aircraft not manually re-matched since the `0.3.0` bump now returns an **empty** match list, which is indistinguishable in the API contract from "no applicable ADs" — a different but still customer-trust-relevant correctness gap (silent absence vs. silently-wrong presence).

**Action:** either (a) auto-trigger `match_aircraft_ads` for an aircraft when its most recent result's `algorithm_version` is stale and a match-list request comes in, or (b) add a scheduled/idempotent reprocessing job plus a "results pending recomputation" indicator on the response, so an empty list is distinguishable from a genuinely-processed empty list.

## Positive/Notable Closures (confirmed correct)

- **Mistral `processing_seconds`** (prior streamed-review finding #1): `MistralOCRProvider.process_upload` now wraps its result with `replace(result, metadata={**result.metadata, "processing_seconds": ...})` (`ocr_provider.py:704-710`), and is asserted by `test_mistral_provider_posts_base64_pdf_with_page_guardrail` (`test_ocr_provider.py:477-480`). All three provider paths (fixture, Textract sync/async/analysis_async, Mistral) now populate `processing_seconds`.
- **Fixed-precision OCR cost columns** (prior streamed-review finding #2): `pricing_rate_usd`/`estimated_cost_usd` moved from `Float` to `Numeric(18,8)` via a correctly-chained follow-up migration (`20260725_0012_use_fixed_precision_ocr_costs.py`, `down_revision = "20260725_0011"`), with symmetric `upgrade`/`downgrade` using `postgresql_using` casts. Values are `round(..., 6)` in Python before assignment (`ocr_provider.py:310-313`, `layout_first_ocr.py:280`), which fits cleanly inside 8 fractional digits, so residual float-to-Decimal conversion artifacts are not a practical concern here.
- **One-pass structured entry parsing** (prior streamed-review finding #3): `match_aircraft_ads` now builds `structured_entries = {entry.id: extract_entry_structure(entry) for entry in entries}` once (`ad_matching.py:56-59`) and threads it through `upsert_match_result`/`rank_candidate_entries`, which prefer the memoized value and only fall back to re-parsing if the dict lookup misses. Verified by the new call-counting test (`test_ad_matching.py:96-121`), asserting `extraction_calls == entry_count` (i.e., parsed once per entry per run, not once per directive×entry).
- Migration `20260725_0011` additions (`processing_seconds`, `pricing_unit`, `pricing_rate_usd`, `estimated_cost_usd`) are all-nullable `add_column`s against an existing table — no backfill/data-loss risk.

# Open Questions

- For finding #1, is there a broader inventory of negation phrasings expected from real logbook text (mechanics' shorthand, abbreviations like "N/C" for "not complied") that should inform the regex redesign, or is a bounded-gap regex an acceptable interim fix pending a small labeled corpus?
- For finding #2, is manual, per-aircraft invocation of `python -m app.workers.ad_matching` the intended pilot-stage operational process (i.e., is this already documented as a runbook step elsewhere), or was continuous/automatic re-matching assumed to already exist?
- `Mistral direct_api_page_price_usd = 0.004` remains a hardcoded class constant (`ocr_provider.py:645`) rather than a configurable setting like Textract's/layout-first's rates — carried over from the prior review as an open question, unchanged by this diff; confirming this is intentional given the channel is currently policy-disabled for real customer data.

# Verification Notes

- Ran the backend suite from `backend/`: `PYTHONPATH=. PAPRNAV_DISABLE_DOTENV=1 .venv/bin/pytest -q` → **65 passed**, including all modified/new files in the focus list.
- Directly exercised `app.services.maintenance_extraction.ad_disposition()` with modal-verb negation strings; confirmed each incorrectly returns `"complied"`/`"inspected"` rather than `"not_complied"`/`"not_inspected"` (see Finding #1 for exact inputs/outputs).
- Traced `ad_disposition()` output through `rank_candidate_entries()` → `upsert_match_result()` (`ad_matching.py:143-161`) to confirm the false "complied"/"inspected" value suppresses the `explicit_compliance_claim_missing` unresolved reason and, combined with `review_status == "verified"` and an explicit normalized AD-number match, is sufficient to reach `status = "candidate_satisfied"`.
- Confirmed via `grep -rln "match_aircraft_ads" backend` that the only call sites are `ad_matching.py` itself, the manual CLI worker `app/workers/ad_matching.py`, and tests — no automatic trigger exists.
- Confirmed `git diff HEAD -- backend/app/api/routes/ads.py` shows the new `algorithm_name`/`algorithm_version` filter in `list_aircraft_matches`, and read `backend/app/schemas/ads.py` to confirm `ADMatchResultListResponse` has no staleness field.
- Read the new migration pair end-to-end; `down_revision` chain (`20260722_0010` → `20260725_0011` → `20260725_0012`) is consistent with `sqlalchemy.url` defaulting to PostgreSQL in `alembic.ini`/`config.py`, so the `postgresql_using` casts are valid for the intended deployment target.
- Confirmed `.ai/DECISIONS.md` (D020) and `.ai/AD_MATCHING_RULES.md`/`.ai/OCR_FEASIBILITY_STATUS.md` updates accurately describe the intended behavior for metering, matcher versioning, and negation handling — the documentation's stated intent ("negated statements... are never positive compliance evidence") is not fully met by the current regex implementation per Finding #1.

# Brief Summary

Three of the four previously-flagged issues (Mistral `processing_seconds`, Float→Numeric fixed-precision cost columns with a safe migration, and one-pass memoized structured-entry parsing) are correctly and verifiably closed, each with adequate new tests. The stale-matcher-version exposure issue is addressed in the safe direction (hiding old results) but trades it for a related gap: there's no automated reprocessing trigger or "stale" signal, so an unprocessed aircraft now silently looks like "no ADs apply." The most important open item is that the negated-compliance-language fix, while correct for the literal phrasings it was tested against, does not generalize to ordinary modal-verb negations ("will not be complied with," "cannot be inspected," "is not going to be complied with") — these still resolve to a positive disposition and can still produce a false `candidate_satisfied` AD-compliance result for a verified logbook entry, which is the same class of safety defect this review round was specifically meant to close.