## Review: OCR usage metering + AD matching hardening diff

### 1. [CRITICAL — AD compliance false positive] Negation is not handled in disposition classification
**`backend/app/services/maintenance_extraction.py::ad_disposition`**

```python
if re.search(r"(?:\bc\s*/\s*w\b|\bcomplied(?:\s+with)?\b)", text, re.IGNORECASE):
    return "complied"
...
if re.search(r"\b(?:inspect(?:ed|ing)?|inspection\s+completed)\b", text, re.IGNORECASE):
    return "inspected"
```
This is a plain substring/regex search with no negation awareness. A logbook line such as *"AD 2012-01-02 NOT complied with — parts on order"* or *"AD reviewed, not inspected yet"* will still match `complied`/`inspected` and return a positive disposition, because the negation check only looks for `n/a` / `not applicable`, not `not complied` / `did not` / `not yet`.

This feeds directly into `ad_matching.rank_candidate_entries` (score 0.82, "explicit AD number with disposition candidate 'complied'") and into `upsert_match_result`, where `disposition_candidate in {"complied","inspected"}` suppresses the `explicit_compliance_claim_missing` reason. If the entry's `review_status` is `"verified"`, the result can land at `candidate_satisfied` with confidence > 0.8 for an AD that the logbook entry explicitly says is **not** complied with. This is the exact false-positive-compliance failure mode this review is meant to catch, and there is no test exercising negated language (only positive-claim tests exist in `test_maintenance_extraction.py` / `test_ad_matching.py`).

**Action:** add negation guards (e.g. `not\s+(?:yet\s+)?complied`, `did\s+not`, `n\/?a`) before the positive match, default to `mentioned`/`not_applicable` on negation, and add a regression test.

### 2. [HIGH — stale/false-positive results not reprocessed] No backfill for algorithm version bump
**`backend/app/services/ad_matching.py`** — `ALGORITHM_VERSION` moved `0.1.0 → 0.2.0` with materially stricter logic (requires explicit normalized AD reference, verified review_status, non-recurring, explicit compliance claim).

Existing `ADMatchResult` rows computed under v0.1.0 (naive substring match at flat 0.7 confidence, no verified-status requirement) remain in the database with their old status/confidence until `match_aircraft_ads` happens to re-run for that aircraft (e.g., triggered by new ingestion). There's no migration data-fix, no "recompute if algorithm_version < current" trigger, and no operational note in the diff to force reprocessing. Practically, this means aircraft that were previously (and now-recognizably, incorrectly) shown as `candidate_satisfied` can continue displaying that status indefinitely for airframes with no new logbook/AD activity — a real customer-facing compliance-status correctness gap, not just a cosmetic one.

**Action:** add a migration/maintenance script (or startup check) that re-runs `match_aircraft_ads` for all aircraft with results whose `algorithm_version` predates `0.2.0`.

### 3. [HIGH — out of review scope] New OCR provider and its tests are not in this diff
`backend/app/services/ocr_provider.py::get_ocr_provider()` now routes to `layout_first_vlm` → `app.services.layout_first_ocr.LayoutFirstVLMOCRProvider`, and `config.py` adds `layout_first_compute_rate_usd_per_hour`, `layout_first_pdf_dpi`, `layout_first_timeout_seconds`, etc. — all clearly intended for per-run cost attribution. However `backend/app/services/layout_first_ocr.py`, `backend/tests/test_layout_first_ocr.py`, and `backend/requirements-layout-ocr.txt` are new/untracked files **not included in the supplied diff**. I cannot verify:
- correctness of the hourly-rate → per-run cost conversion (unit errors, e.g., seconds vs. hours),
- whether `confidence`/`extraction_confidence` are populated or left `None` for this provider (relevant to finding #5), and
- error handling if the local model/Ollama endpoint is unreachable.

This provider is already selectable via config (`PAPRNAV_OCR_PROVIDER=layout_first_vlm`), so its cost-attribution correctness is currently unverified in production-relevant code. Flag as a sign-off blocker for that specific provider path pending a follow-up review with the actual source.

### 4. [MEDIUM — missing tests for ingestion regex overhaul] Ingestion clustering/date logic changed with no dedicated unit tests
**`backend/app/services/ingestion.py`** — `entry_drafts_from_page`, `cluster_has_logbook_entry_signal`, `is_text_bearing_ocr_span`, `strip_matching_date`, `strip_date`, and the tightened `ISO_DATE_PATTERN`/`SHORT_DATE_PATTERN` are substantially rewritten, but only one end-to-end fixture (`test_mvp_endpoints.py`) exercises the pipeline, and it wasn't extended to cover the new branches. Given this pipeline produces the `raw_text`/`description` that feed AD-matching evidence (finding #1/#2), gaps here have outsized downstream risk. Specifically: `ISO_DATE_PATTERN` (`YYYY-MM-DD`) is exactly the same shape as an AD number (`2012-01-02`). If a compliance line containing "AD 2012-01-02" ends up as/near the anchor line, `parse_date` could misattribute the AD number as the entry's maintenance date. No test constructs this collision case.

### 5. [MEDIUM] Silent behavior change in `is_ignorable_logbook_line`
`lowered.startswith("see back pages")` replaces `"see back pages" in lowered`. Combined with the newly broadened `cluster_has_logbook_entry_signal` (which now fires on many more generic tokens: `n\d+`, `tach`, `p/n`, action+subject pairs, etc.), boilerplate lines like *"continued — see back pages for AD status"* are no longer filtered and could now be picked up as a maintenance-entry cluster. Not covered by any test in the diff.

### 6. [LOW — nullable confidence audit incomplete] Optional confidence propagation only partially guarded
`OCRSpanResult.confidence` and `OCRPageResult.extraction_confidence` become `Optional[float]`, and `ExtractedEntryDraft.min_confidence` follows. Only the `entries_extract_entries_from_job` verified/needs_review branch was updated with an explicit `is not None` guard. Other consumers of page/run-level confidence (serializers, dashboards, aggregate/report code) are not shown as updated in this diff — worth confirming none of them still assume a non-null float (risk of `TypeError` on comparisons/averaging, or silently defaulting to 0 and under-reporting confidence).

### 7. [LOW] Dead code
`ingestion.py::span_requires_raw_ocr_correction` is added but has no call site in this diff — either it's used elsewhere (not shown) or it's dead code that should be removed/wired up.

### 8. [LOW] `EXPLICIT_AD_PATTERN` false negatives on unspaced revision suffixes
`maintenance_extraction.py::EXPLICIT_AD_PATTERN` (`r"\bAD\s*((?:\d{4}|\d{2})-\d{2}-\d{2})\b"`) fails to match ADs with a directly-appended revision like `"AD 2013-02-03R2"` (no boundary between digit and letter), causing `explicit_ad_reference_missing`. This errs toward under-confidence (manual review) rather than a false positive, but is untested and worth a case.

### 9. [LOW] Cost-metadata test coverage gap across Textract API modes
`test_ocr_provider.py` only verifies the new `_with_usage_metadata` wrapper (`processing_seconds`, `pricing_unit`, `pricing_rate_usd`, `estimated_cost_usd`) for `analysis_async` mode. The plain `async` and synchronous `detect_document_text` code paths in `TextractOCRProvider.process_upload` route through the same wrapper but aren't asserted against in tests.

### 10. [LOW] Redundant recomputation
`ad_matching.rank_candidate_entries` re-runs `extract_structured_maintenance_data` for every `(directive, entry)` pair rather than once per entry — a performance smell for large logbooks, not a correctness bug.

---
**Bottom line:** Finding #1 (negation-blind disposition classification) is a blocking correctness/safety defect that should be fixed and tested before this ships, since it can actively mark a non-complied AD as satisfied. Finding #2 (no reprocessing of stale results after the algorithm tightening) is also blocking from a customer-trust standpoint — otherwise the safety improvement in this diff doesn't actually apply to previously-computed results. Finding #3 (missing provider source/tests) should be resolved by including the referenced files in review before merge, or by disabling the `layout_first_vlm` provider selection until reviewed.
