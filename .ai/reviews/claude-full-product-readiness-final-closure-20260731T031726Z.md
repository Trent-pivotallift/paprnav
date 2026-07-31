I have what I need. All checks were static (no tests run — execution was denied in this sandbox); no files were modified, and neither frozen partition was opened.

---

## Remaining high-risk issue (new, same class as R1 — narrower)

**A directive approved with empty `affectedProducts` is applicable to every aircraft but fans out to nobody, so the worklist keeps reporting `matcherStatus: "current"`.**

- `backend/app/services/ad_matching.py:342-345` — `is_potentially_applicable` returns `True` when `affectedProducts` is empty, so an extraction with no parsed products is compared against *every* aircraft on the next run.
- `backend/app/services/ad_applicability.py:104-113` — `populate_applicability_from_extraction` returns `0` for empty products (records a `missing_extracted_applicability` issue instead), so no `ADTargetApplicability` row exists.
- `backend/app/api/routes/ads.py:311-337` — the new fan-out is `target_ids → ADCoverageSet → active ADCoverageSubscription`. With `target_ids == []` the fan-out collapses back to the old behavior (`ads.py:302-309`: aircraft with an existing `is_current` match row for that directive), which is empty for a brand-new directive.
- `backend/app/services/ad_extraction.py:441-443` — `validate_extraction_output` only checks `isinstance(..., list)`, so `affectedProducts: []` is an approvable payload.
- No compensating signal: `summarize_aircraft_coverage_status` (`ad_coverage.py:427-461`) reconciles only per-component subscriptions and cached coverage-set status; a directive-level unattributed-applicability issue never reaches `coverageStatus`/`coverageWarnings`.

Suggested fix: when `populate_applicability_from_extraction` returns `0` on an approve/edit, either invalidate all aircraft with any resolved coverage (or all with a prior completed run), or refuse approval of a directive with no attributable target.

Also still true (accepted, not a regression): `match_aircraft_ads` has one caller, the CLI (`app/workers/ad_matching.py:18`; `backend/README.md:318-320`), so the recompute window remains operator-bounded — but it is now honestly labeled `pending_recomputation` rather than `current`.

---

## Closures confirmed

| Item | Status | Evidence |
|---|---|---|
| **R1** subscription-based fan-out | **Closed** for directives with attributable targets | `ads.py:311-337` derives `target_ids` from `ADTargetApplicability` after `populate_applicability_from_extraction` + `db.flush()`, then unions active `ADCoverageSubscription.aircraft_id` via `ADCoverageSet.target_id.in_(target_ids)`. Imports present (`ads.py:18-19, 52-53`). |
| **R1** coverage refresh at approval | **Closed** | `ads.py:355-361` calls `resolve_aircraft_ad_coverage` per affected aircraft, which calls `refresh_coverage_set` (`ad_coverage.py:91`) — the sole writer of `status`/`directive_count` (`ad_coverage.py:168-181`), so the stale-`current`-with-stale-count case is gone. |
| **R1** invalidation after a **zero-result completed run** | **Closed** | `invalidate_aircraft_match_results` (`ad_matching.py:299-306`) now emits `ad_matching_invalidated` when `invalidated or prior_completion is not None`, and pins `event.event_time = now` (`:320`) so it sorts ahead of the earlier `ad_matching_completed` in the worklist query (`ads.py:136-144`). |
| **R1** worklist reports `pending_recomputation` | **Closed** | `ads.py:166-171` → `matching_was_invalidated or has_stale_results` yields `pending_recomputation`, `reprocessingRequired=True` (`:180`). Regression: `test_ad_ingestion.py:111-112` asserts `directives_seen == 0` for the pre-approval run, then `:161-178` asserts the subscription exists, the `ad_matching_invalidated` event exists, and the owner-visible worklist returns `pending_recomputation` / `reprocessingRequired: true`. |
| **R2** transitions *out of* verified require authority | **Closed** | `logbook_entries.py:325-330` gates on `original_review_status == "verified" and fields["reviewStatus"] != "verified"` via `ensure_maintenance_review_access`, evaluated against `original_review_status` captured at `:295` (not the already-mutated `entry.review_status`). Tested: owner demote → 403 at `test_ad_matching.py:403-408`. |
| **R2** prior attestation retained | **Closed** | The former null-out is gone; `:390-393` only *sets* `reviewed_by_user_id`/`reviewed_at` on transition **to** `verified`. Tested: `test_ad_matching.py:417` asserts `reviewedByUserId == shop_user.id` survives the demotion. |
| **R3** frontend nullable `entryDate` + "Unknown date" | **Closed** | `src/lib/api.ts:348` is `entryDate: string \| null` (consistent with `:96, 115, 128, 268`); `page.tsx:391` renders `{evidence.entryDate ?? "Unknown date"}`, matching the logbook list at `:519`. |
| **Low** dedupe tiebreaker | **Closed** | `approved_current_extractions` orders `ADExtraction.created_at.desc(), ADExtraction.id.desc()` (`ad_matching.py:170`) before `setdefault` (`:174`) — deterministic within a timestamp collision. |
| **Low** vacuous `logbook_entry_unverified` assertion | **Closed** | Grep over `app/` and `tests/` returns only stale `.pyc` hits; no source occurrence remains. |

---

## Verdict

**Ready on the reviewed scope; one follow-up recommended before calling "current means current" unconditional.**

All five requested items (R1 with its three sub-conditions, R2 with both sub-conditions, R3, and both low-risk nits) are genuinely closed in the current source, with direct regression coverage for the hardest case — approval of a new directive after a zero-result completed run now discovers aircraft via active coverage subscriptions, refreshes their coverage sets, records `ad_matching_invalidated`, and surfaces `pending_recomputation` to the owner (`test_ad_ingestion.py:111-178`).

The one residual is the empty-`affectedProducts` path, which restores the exact R1 failure mode for directives whose applicability could not be attributed to a target — reachable because `validate_extraction_output` accepts an empty list and the matcher treats "no products" as "applies to all." It is materially narrower than R1 (requires an unparsed/edited-to-empty applicability set, and the system does record a `missing_extracted_applicability` reconciliation issue), so I would not hold R1/R2/R3 closure on it, but it should be tracked as high-risk rather than closed silently. I did not run the test suite, so closure is asserted from source inspection only.
