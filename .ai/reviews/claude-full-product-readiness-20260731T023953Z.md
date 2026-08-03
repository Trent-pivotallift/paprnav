## Review: Controlled Full-Product Readiness Loop (read-only)

Scope confirmed: only the listed working-tree files plus directly imported model/route/schema code were read. Neither frozen partition was opened, and no files were modified.

---

## Blocking / high-risk findings

**B1. The human verification attestation is silently unauditable when the client omits `reviewElapsedSeconds`.**
`backend/app/api/routes/logbook_entries.py:132` returns early from `add_review_outcome_evidence` if `elapsed_seconds is None`, and `add_human_override_evidence` (`:88`) returns early when no field value changed. `LogbookEntry` has no `verified_by_user_id` / `verified_at` column (`app/models/core.py:173-188`). Therefore a `PATCH {"reviewStatus":"verified"}` with no other fields and no `reviewElapsedSeconds` flips an OCR-derived maintenance record to `verified` — making it eligible AD compliance evidence at `app/services/ad_matching.py:52-61` — while persisting **zero record of who verified it or when**. The job is then closed `complete` (`logbook_entries.py:383-387`). `reviewElapsedSeconds` is optional and client-controlled (`app/schemas/logbook_entries.py:29-30`), so the audit trail is optional in practice. Scenario 1 masks this by always sending `18.5` (`tests/test_full_product_readiness.py:118`). For an aviation maintenance-record system, the verification act must be a first-class, non-optional, server-timestamped record on the entry itself.

**B2. No authority/role gate on verification or on AD adjudication; and AD extraction approval has no authorization at all.**
`update_logbook_entry` only calls `get_visible_aircraft_or_404` (`logbook_entries.py:278`), as does `decide_match_adjudication` (`ads.py:192`). Any user with *visibility* — including a maintenance-shop member granted read access via assignment (`app/api/routes/aircraft.py:139-143`) or an owner with no mechanic credential — can mark maintenance entries verified and adjudicate an AD `satisfied`. Worse, `decide_extraction_review` (`ads.py:247-313`) performs **no aircraft, org, or role check whatsoever**: any authenticated user can approve/edit an AD extraction output, which then drives `populate_applicability_from_extraction` (`ads.py:278`) and therefore applicability for *every* customer aircraft. `list_directives`/`list_discovery_records` are likewise globally readable (`ads.py:54-75`). This is a cross-tenant integrity hole on the safety-critical side of the pipeline and is not listed in README "Missing Backend Pieces" (`backend/README.md:314-320`).

**B3. Match results are never invalidated; stale `candidate_satisfied` and stale human adjudications persist and are returned.**
`upsert_match_result` reuses a row only on an exact `input_hash` match (`ad_matching.py:199-207`), and `input_hash` includes every verified entry's id/date/text/review status (`:537-546`). Any logbook edit, un-verification, or new entry changes the hash, so a **new** row is inserted; the unique constraint permits many rows per (aircraft, directive) (`app/models/core.py:786-795`). Nothing deletes or supersedes the old rows, and `list_aircraft_matches` filters only on algorithm name/version (`ads.py:103-121`). Consequences:
- Un-verifying or correcting the entry that satisfied an AD leaves the previous `candidate_satisfied` row live in the worklist alongside the new `needs_adjudication` row — the exact failure mode Scenario 8 claims to prevent, one step later in time.
- A human `adjudicated_satisfied` row from a prior run coexists with a fresh `pending` row for the same directive; ordering by `status.desc()` (`ads.py:120`) surfaces `needs_adjudication` above `adjudicated_*`, so reviewers see duplicated, contradictory rows for one AD with no "supersedes" relationship.
There is also no automatic re-match trigger on entry change (only `app/workers/ad_matching.py`), so the displayed compliance state can be arbitrarily stale relative to the logbook.

**B4. Potentially applicable ADs are silently dropped when component identity is incomplete — no result, no adjudication task.**
`ad_matching.py:71-78`: when structured applicability exists but `select_applicable_component` returns `None`, the directive is counted in `skipped_not_applicable` and `continue`d — no `ADMatchResult`, no `ADMatchAdjudication`, nothing in the UI. `component_target_score` hard-returns `0.0` whenever the target names a make/model and the installed component's corresponding field is missing or spelled differently (`:330-337`, via `text_matches` `:341-348`). So an aircraft whose engine is recorded with make but no model, or with a variant model string, causes applicable engine ADs to vanish rather than route to human review. This contradicts `.ai/AD_MATCHING_RULES.md:105-113` ("create a pending adjudication task when … applicability … cannot be resolved from aircraft/component facts"). No test asserts anything about `skipped_not_applicable`.

**B5. `coverageStatus: "current"` can be reported while a component has no coverage at all, and while the DRS snapshot is arbitrarily stale.**
`resolve_aircraft_ad_coverage` skips any active component lacking both make and model (`ad_coverage.py:58-61`, `components_skipped`), so no coverage set or subscription is created for it. `summarize_aircraft_coverage_status` derives warnings **only from existing active subscriptions** (`ad_coverage.py:372-436`), so the unidentified component produces no warning and the aircraft reports `current`. Separately, `latest_reusable_drs_snapshot` (`:255-275`) applies no freshness bound: a months-old `complete` snapshot yields `status = "current"` with zero staleness warning. Both directly violate `.ai/DECISIONS.md:432-437` ("`current` means every active airframe/component coverage set is current … must never … imply complete historical/indexed AD coverage") and `backend/README.md:325-328`. Scenario 9 only exercises the `partial`-snapshot path.

**B6. `GET /ads/aircraft/{id}/matches` can 500 after a legal logbook edit.**
`ADMatchEvidenceResponse.entryDate: date` is required (`app/schemas/ads.py:74-83`; frontend mirrors it as non-nullable, `src/lib/api.ts:346`), but `serialize_match_evidence` reads `entry.entry_date` unconditionally (`ads.py:474-486`). `update_logbook_entry` permits `entryDate = null` for `ocr_ingestion` entries (`logbook_entries.py:293-296`) as long as the entry is not left `verified` — so a reviewer who reverts a candidate (`reviewStatus:"needs_review"`, `entryDate:null`) while a prior match still links that entry (see B3) makes the whole AD worklist response un-serializable. The AD worklist is the safety surface; it fails closed to a 500 with no partial degradation.

---

## Medium

**M1. Zero-entry extraction closes the job as `complete`.** `ingestion.py:374-376` sets `status="complete"`/`completed_at` when a verified page yields no drafts. Cluster rejection is heuristic (`cluster_has_logbook_entry_signal`, `:467-504`; cluster filter `:398-401`), so a page containing real maintenance entries that the deterministic extractor misses is closed silently — missed compliance evidence with no review task. `stage_results["validation"]` records counts (`:319-329`) but nothing gates on them.

**M2. Doc/code mismatch on the job-level gate.** `.ai/DECISIONS.md:426-430` and `backend/README.md:171-174` state entries participate in AD matching only after the job becomes complete. The matcher gates per entry (`ad_matching.py:56-58`), so in a multi-entry job an individually verified entry participates while the job is still `awaiting_entry_review`. The per-entry gate is the safer one; the docs overstate the guarantee.

**M3. Dead verified-entry guard.** `ad_matching.py:186-187` appends `logbook_entry_unverified`, which is unreachable given the query filter at `:56`. `tests/test_ad_matching.py:340` asserts its *absence*, which reads as a contract but is vacuous. Keep the query filter as the enforcement point, but the dead branch invites a future regression where the filter is relaxed and the reason silently never fires.

**M4. Bidirectional substring applicability matching.** `text_matches` accepts containment in either direction after stripping non-alphanumerics (`ad_matching.py:341-352`), so target `172R` matches component `172RG`, and `1720` matches `172`. Combined with B4's hard `0.0`, applicability is simultaneously over- and under-inclusive with no confidence penalty on fuzzy hits.

**M5. `approved_current_extractions` is not "current".** `ad_matching.py:140-155` selects *all* `approved` extractions with no dedupe per directive. A re-extracted, re-approved directive produces two rows for one directive per aircraft, inflating `directives_seen` and creating parallel match results/adjudications.

**M6. `upsert_match_result` will raise on a caller that passes `target_applicability` without `installed_component`** (`ad_matching.py:192` dereferences `installed_component.serial_number`). Safe only because the sole caller passes them as a pair (`:84-86`).

**M7. Frontend does not distinguish verified from unverified entries.** `reviewStatus` is in the type (`src/lib/api.ts:101`) but the logbook list renders only description/date/performer (`logbook/[nNumber]/page.tsx:482-508`) — an unverified OCR candidate is visually indistinguishable from a verified maintenance record. Likewise the worklist shows `unresolvedReasons` only as raw underscore-stripped tokens (`:376-381`), so `directive_superseded` is not treated any differently from `recurring_due_status_unknown`, contrary to `.ai/AD_MATCHING_RULES.md:117`.

---

## Test gaps (do the ten tests prove their declared contracts?)

Contracts genuinely proven: retained bytes + native-bypass counters + `needs_review` → explicit verify + page evidence (Scenario 1, `test_full_product_readiness.py:53-127, 219-231`); component-specific airframe/engine/propeller selection (2-4); recurring → `recurring_due_status_unknown` + pending (5); superseded → `directive_superseded` with evidence retained (6); no-evidence → pending task (7); unverified entry excluded *at first run* (8); partial-snapshot `degraded` at the API boundary (9); coverage-set reuse counts, 6 subscriptions / 3 first-triggers, ledger scope separation and `allocated_cost_usd == 0` (10).

Not proven, despite being declared or implied:
1. **`source_downloads_requested == 0` is tautological** (`:599`). `CoverageResolutionStats.source_downloads_requested` (`ad_coverage.py:37`) is never incremented anywhere; the assertion cannot fail and does not evidence "zero source downloads" (`GOAL_TASKS.md:2093`).
2. **No invalidation test.** No scenario re-runs the matcher after un-verifying or editing an entry, so B3's stale `candidate_satisfied` / duplicated adjudication behavior is entirely untested. Scenario 8 tests exclusion only in a never-previously-matched state.
3. **The `entry_has_source_supported_date` gate (`logbook_entries.py:341-349, 393-403`) is untested** in this file — no scenario attempts to verify an entry whose only `entry_date` evidence is `fallback`, so the gate's practical reachability is unproven.
4. **No authorization scenario.** Nothing asserts who may verify an entry, adjudicate a match, or approve an AD extraction (B2). Scenario 1/2/9 all log in as the owner.
5. **No `skipped_not_applicable` assertion anywhere** — B4's silent-drop path has no coverage, and Scenarios 3/4 assert only the positive selection, never the absence of a wrongly-dropped or wrongly-collapsed sibling result.
6. **Scenario 6 never checks the superseding AD** (`2026-06-02`) surfaces as outstanding, nor that the superseded row is labeled/suppressed as historical per `AD_MATCHING_RULES.md:117`.
7. **Scenario 9 does not test the missing-identity or stale-snapshot coverage paths** (B5), nor `not_resolved`, nor that a *complete* snapshot with zero applicability yields `pending_applicability`.
8. **Degraded-coverage exposure is asserted only in JSON.** No frontend test proves the banner renders (`page.tsx:284-294`); the doc claims the warning is exposed "at the worklist boundary" (`FULL_PRODUCT_READINESS_LOOP_2026-07-29.md:43`).
9. **Scenarios 3-8 assert with bare `db.scalar(select(...))`** (e.g. `:263-266, 305, 371`), which returns an arbitrary first row. These pass only because each fixture DB holds one directive; they will not detect duplicate or contradictory rows (B3).
10. **`assert ALGORITHM_VERSION == "0.4.0"`** (`:621`) is a constant tautology inside the cost/reuse scenario and evidences nothing about behavior.
11. **No serialization-robustness test** for B6, and no test that the review-outcome/reviewer-identity evidence exists when `reviewElapsedSeconds` is omitted (B1).

---

## Verdict

**Not ready to close T076 or to open the frozen partitions.** The declared 10/10 result is accurate as far as the assertions go, but the suite is composed of happy-path, single-row, single-run scenarios and contains at least two vacuous assertions (`source_downloads_requested`, `ALGORITHM_VERSION`). The conservative design choices that matter most — human-only verification, verified-only evidence, adjudication for recurring/superseded/unknown cases, non-billing attribution — are implemented correctly for a first pass and are genuinely demonstrated *in the first run of a clean database*.

What blocks readiness is the second-order behavior around those gates: the verification act is optionally unauditable and unauthorized (B1, B2), compliance conclusions are never invalidated when their evidence changes (B3), applicable ADs can disappear rather than route to review (B4), `current` coverage can be asserted over uncovered components and stale sources (B5), and the worklist can hard-fail after a permitted edit (B6). B1-B4 should be fixed and covered before this path is exercised against real early-adopter documents; B5's "current" semantics should be tightened or the status renamed, since `.ai/DECISIONS.md:432-437` currently promises more than the code delivers. Update `.ai/FULL_PRODUCT_READINESS_LOOP_2026-07-29.md:5` and `GOAL_TASKS.md:2073` to reflect review findings rather than "verification complete; independent review pending."
