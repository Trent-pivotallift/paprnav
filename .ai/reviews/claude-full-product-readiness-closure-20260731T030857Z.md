I have what I need. Here is the closure review.

---

## Closure review: six blocking findings (read-only)

Scope: `backend/app/{api/routes,services,schemas,models}`, `backend/tests`, `frontend/paprnav-frontend/src/{lib/api.ts, app/(authenticated)/logbook/[nNumber]/page.tsx}`, and the updated `.ai` readiness docs. Neither frozen partition was opened; no files were modified.

### Remaining blocking finding

**R1 (residual B3). Approving a *new or newly-applicable* AD extraction does not invalidate any aircraft, so the worklist keeps reporting `matcherStatus: "current"` and `coverageStatus: "current"` against an AD set that excludes the new directive.**

`backend/app/api/routes/ads.py:295-302` computes the invalidation fan-out as *aircraft that already have a current match row for this directive*:

```python
affected_aircraft_ids = select(ADMatchResult.aircraft_id).where(
    ADMatchResult.directive_id == review.extraction.directive_id,
    ADMatchResult.is_current.is_(True))
```

Consequences:
- A **brand-new** directive approved at `ads.py:303-310` has zero prior match rows → `invalidate_aircraft_match_results` (`ads.py:321-326`) runs for nobody. Every subscribed aircraft still satisfies `matches or completed_with_current_version` at `ads.py:166-171` and reports `matcherStatus: "current"`, `reprocessingRequired: false`.
- An **edited** extraction that newly makes a directive applicable (previously counted in `skipped_not_applicable`, `ad_matching.py:82-88`) is likewise not fanned out, because "no result" and "not applicable" are indistinguishable here.
- Coverage health does not compensate: `summarize_aircraft_coverage_status` reads the cached `ADCoverageSet.status` (`ad_coverage.py:429-432`), and `refresh_coverage_set` — the only writer of `status`/`directive_count` (`ad_coverage.py:208-226`) — is called only from `resolve_aircraft_ad_coverage` (i.e. inside a matcher run or an aircraft PATCH) or from `refresh_coverage_sets_for_snapshot`. `populate_applicability_from_extraction` (`ad_applicability.py:104-134`) changes `directive_count` inputs without touching coverage status, so the aircraft reports `current` with a stale directive count and no warning.
- There is no recompute trigger. `match_aircraft_ads` has exactly one caller, the CLI at `app/workers/ad_matching.py:18`, and `backend/README.md:318-320` confirms no production worker scheduling. So the staleness window is unbounded and operator-dependent.

This is the same class of claim B3 targeted — a "current" compliance conclusion that its own inputs have outrun — and it contradicts `.ai/DECISIONS.md:~322-326` ("Any safety-relevant edit … invalidates current AD match results until the matcher recomputes them") because directive-set changes are only partly covered. Correct fix: fan out on coverage subscriptions/applicability targets for the directive (or invalidate all aircraft subscribed to the affected targets), and either refresh coverage sets at approval or add a directive-set generation marker to the `matcherStatus` computation.

### High-risk (non-blocking) findings

**R2. Verification can be revoked without maintenance authority, clearing the attestation columns.** `logbook_entries.py:324-327` gates only the transition *to* `verified`; the edit gate at `:328-341` requires `entry.review_status == "verified"`, which is already false once `reviewStatus:"needs_review"` is applied at `:327`. Any user with visibility (e.g. the owner) can therefore demote a maintenance-verified entry, and `:387-389` nulls `reviewed_by_user_id`/`reviewed_at`. The act itself is still recoverable from `review_outcome` evidence (`:163-194`), but the entry-level attestation B1 introduced is erasable by an unauthorized actor and the entry silently stops being AD evidence (`ad_matching.py:61-70`). Suggest gating any transition *out of* `verified` on `ensure_maintenance_review_access` as well.

**R3. Frontend type still mirrors `entryDate` as non-nullable after the B6 fix.** Backend is now `Optional[date]` (`backend/app/schemas/ads.py:77`) and `serialize_match_evidence` passes it through unguarded (`ads.py:512-524`), but `frontend/paprnav-frontend/src/lib/api.ts:348` declares `entryDate: string` and `page.tsx:390` renders `{evidence.entryDate}` raw — a null historical date renders as an empty span with no "Unknown date" affordance, unlike the logbook list which handles it correctly at `page.tsx:517`. Type-level drift, not a 500.

### Low

- `approved_current_extractions` dedupe (`ad_matching.py:169-174`) keys on `created_at desc` + `setdefault` with no `id` tiebreaker; extractions approved within the same timestamp resolution pick nondeterministically.
- `tests/test_ad_matching.py:351` still asserts the absence of `logbook_entry_unverified`, a reason string no longer present anywhere in `app/` — the assertion is now permanently vacuous.

---

## Closures confirmed

| Finding | Status | Evidence |
|---|---|---|
| **B1** reviewer identity / server timestamp | **Closed** | `LogbookEntry.reviewed_by_user_id` / `reviewed_at` columns (`models/core.py`, migration `20260730_0017_...`), set server-side at `logbook_entries.py:383-389` independent of client input; `add_review_outcome_evidence` now fires on `review_status_changed` even with `elapsed_seconds is None` (`:139-143`); exposed at `:71-72`. Tested: `test_full_product_readiness.py:134-135, 243-244`. |
| **B2** authority gates | **Closed** | `ensure_maintenance_review_access` requires active maintenance-org membership **and** an active assignment on that aircraft (`aircraft.py:86-111`); applied to verification and verified-entry edits (`logbook_entries.py:326, 341`) and to adjudication (`ads.py:210`). Extraction review list and decision now require `ensure_platform_admin` (`ads.py:91, 277`). Tested: `test_full_product_readiness.py:120`, `test_ad_matching.py:207`, `test_ad_ingestion.py:102`, `test_mvp_endpoints.py:162`. |
| **B3** current/historical separation + invalidation | **Closed for logbook and aircraft-identity changes; partial for extraction changes (R1)** | `ADMatchResult.is_current` (`models/core.py:819`); run-start demotion (`ad_matching.py:51-59`); `invalidate_aircraft_match_results` (`:284-314`) called from `logbook_entries.py:401-406` and `aircraft.py:310-314`; worklist filters `is_current` (`ads.py:117`) and derives `pending_recomputation` (`:154-171`); stale adjudication rejected 409 (`ads.py:211-215`). Tested: `test_ad_matching.py:363-425, 270`. |
| **B4** incomplete/close identity → adjudication | **Closed** | `structured_applicability_is_uncertain` (`ad_matching.py:372-401`) plus `identity_is_close` (`:459-475`) route missing-make/model and near-miss identities to a result with `component_applicability_uncertain` (`:82-101`) instead of `continue`. `text_matches` is now exact-only (`:449-456`), closing the M4 bidirectional-substring issue too. Tested: `test_ad_matching.py:427-461` including `skipped_not_applicable == 0`. |
| **B5** `current` over uncovered components / stale snapshot | **Closed** | Per-component reconciliation against actual subscriptions (`ad_coverage.py:437-461`) warns on missing make/model and on unmatched identity; `snapshot_is_stale` → `stale_source` (`:218-220, 288-300`) bounded by `PAPRNAV_DRS_MAX_SNAPSHOT_AGE_DAYS` (default 7); `pending_applicability` for zero directives (`:221-223`). Tested: `test_ad_coverage.py:128-183`. |
| **B6** nullable historical evidence dates | **Closed backend-side** | `ADMatchEvidenceResponse.entryDate: Optional[date]` (`schemas/ads.py:77`); worklist no longer 500s after a legal `entryDate: null` revert. Frontend mirror still drifted — see R3. |

Also confirmed as requested:
- **Vacuous assertions removed.** `source_downloads_requested` is gone from `CoverageResolutionStats` (`ad_coverage.py:27-40`, replaced by `source_snapshots_reused`, which is actually incremented at `:92-93`), and the `assert ALGORITHM_VERSION == "0.4.0"` tautology is gone from `test_full_product_readiness.py` (grep across `app/` and `tests/` returns no source hits for either).
- **Zero-entry extraction remains open.** `ingestion.py:375-378` sets `awaiting_manual_entry_review` with `completed_at = None` when no drafts are produced, so M1's silent `complete` is fixed and the job stays in review.
- **Newer approved extraction dedupe is safe.** `approved_current_extractions` (`ad_matching.py:155-174`) keeps one extraction per `directive_id`, newest first, so `directives_seen` no longer inflates and only one current result/adjudication per directive is produced — subject to the tiebreaker nit above.

---

## Verdict

**Not ready — one residual blocking gap, materially narrower than the prior review.** Five of six findings (B1, B2, B4, B5, B6-backend) are genuinely closed with direct regression coverage, and the two vacuous assertions plus the zero-entry `complete` and dedupe issues are resolved. B3 is closed for the two changes that matter most operationally (logbook edits, aircraft identity) but not for directive-set changes: **R1** lets the worklist assert `current` matcher *and* `current` coverage while a newly approved AD has never been compared, with no scheduled recompute to bound the window. Fix R1's fan-out (subscription/target-based rather than existing-result-based) and refresh coverage status at approval; then R2 (revocation authority) and R3 (frontend nullability) can follow. `.ai/FULL_PRODUCT_READINESS_LOOP_2026-07-29.md:5` correctly still reads "closure verification pending" — that remains the accurate state.
