# Pre-Human-Calibration Audit — AD Reviewer Workflow Packet

**Scope caveat, stated first:** the diff on stdin **omits six staged files central to these questions** — `backend/app/api/routes/ads.py`, `services/ad_extraction.py`, `services/ad_applicability.py`, `services/ad_recurrence.py`, `schemas/ads.py`, and `db/migrations/versions/20260822_0021_*`. I attempted direct reads; the working tree returned inconsistent and partly corrupted content (`routes/ads.py` tail resolves to filler lines and duplicated line numbers). Findings below are anchored to the diff text, which I can cite exactly. Backend claims are cited by symbol, not line, and marked *(unverified)*.

---

## BLOCKERS

**B1 — No calibration record is publishable; all five are v2-shaped.**
Every requirement object in all five files lacks `applicabilityGroupKeys`. See `1998-17-11.requirements.json:3-4`, `2002-13-04.requirements.json:3-4`, `2008-26-10.requirements.json:3-4`, `2011-10-09.requirements.json:3-4`, `2024-14-03.requirements.json:3-4`. `API_CONTRACT.md` ("Every requirement includes `applicabilityGroupKeys`") and `test_ad_ingestion.py::test_v3_provider_schema_closes_and_requires_every_object_field` (asserts `required == properties.keys()` for every object) make these arrays hard-invalid. **The human has zero paste-ready records.**

**B2 — Zero of five records exercise the v3 applicability model this review exists to calibrate.**
No file contains `applicabilityGroups`, `serialNumberApplicability`, `equipmentConditions`, or a multi-manufacturer branch. `AD_APPLICABILITY_SCHEMA_REVIEW.md:9-15,60-66` names exactly those as the reason v2 was unsafe. 2024-14-03 (Garmin autopilot software) is the one natural equipment-condition case and models none. Diversity claim in `ad-calibration/README.md:9-11` is unsupported: 3/5 lean on `installation_prohibition`; 4/5 are single-manufacturer piston GA.

**B3 — No reproducible path to the linked v3 reviews.**
`README.md:23-29` links `reviewId=arv_...` and the header calls them "new pending v3 reviews," but the only staging script hardcodes `ADExtraction.schema_version == "ad_extraction_v2"` (`stage_ad_review_proposal.py:47`). Nothing in the packet can produce a v3 review. The five links are unverifiable and likely 404 or serve v2.

**B4 — `stage_ad_review_proposal.py` overwrites the machine proposal with agent-authored JSON.**
`stage_ad_review_proposal.py:75-80` writes `review.proposed_output`, `extraction.output`, and `extraction.confidence` from a file. Gate is only `validate_extraction_output(..., require_v2_requirements=True)` + `validate_requirement_evidence` (`:66-67`) — never `extraction_approval_blockers`, never any `applicabilityGroups` check. The only provenance marker is `raw_response.proposalStagingMode` (`:83`), invisible in the UI. The reviewer then sees this under the heading **"Proposed structured extraction"** (`reviews/page.tsx:157`). Calibrating a model against text the calibration harness wrote is invalid by construction.

**B5 — `correct_approved_ad_review.py` is an unauthenticated publish path that forges reviewer attribution.**
`:150-152` explicitly *asserts* `reviewer_identity_preserved` and `review_timestamp_preserved` — i.e., content the original approver never saw stays signed by them. `:129` destroys `proposed_output`; history retains only `priorDecisionOutput` (`:122`), not the prior proposal. With `--commit` it re-runs `populate_applicability_from_extraction` + `materialize_requirements_from_extraction` and replays coverage/matching (`:135-146`), bypassing the API's `_require_platform_admin` gate entirely. Observability records `actor_type="system"` (`:171`) — no human in the audit trail. Nothing in `DATA_MODEL.md` or `API_CONTRACT.md` documents this path.

**B6 — Source-fidelity defects that would mistrain the calibrator.**
- `2008-26-10.requirements.json:34` — `sourceText` is a **fabricated composite**: `"Inspect within the next 10 days after January 5, 2009; or install placards before further flight"`. Not verbatim. The packet's paraphrase gate (`test_requirement_evidence_rejects_paraphrased_action_text`) checks `actionText` only; threshold `sourceText` is unguarded.
- `2008-26-10.requirements.json:190-194` — the `f-obstruction-report` evidence set includes a correction excerpt ("change 1804 to 1801") that does not support the `actionText`.
- `2008-26-10.requirements.json:110` — `e-5` typed `installation_prohibition` although it is a *mandatory positive* action ("only install a P/N 2013142-18 ... inspected"). Per `API_CONTRACT.md`, that type is parked in adjudication, so a required action becomes unenforced.
- `2002-13-04.requirements.json:9-14` asserts `total_time_hours` while `:22-24` admits the flight-hours mapping is unresolved — the record contradicts itself.
- `1998-17-11.requirements.json:32` uses `terminatingAction` to encode *non-applicability*; `:58` types a mandatory failed-inspection consequence as `alternative`.
- `2011-10-09.requirements.json:5` — 90-word `actionText` ending in a colon, duplicating thresholds inline, with the (g)(1)–(g)(10) actions it introduces entirely absent.

---

## FOLLOW-UPS

**F1 — Evidence pinning is claimed but untested.** `API_CONTRACT.md` states cached pages are accepted "only while their source-document ID and content hash match." `test_deterministic_full_text_extraction_always_requires_review` proves only that caching avoids re-reads (monkeypatching `read_stored_file_bytes` to raise). **No test mutates a content hash and asserts rejection.**

**F2 — No idempotency or supersession test.** `test_v3_requirements_materialize_only_for_declared_applicability_groups` calls populate/materialize exactly once. The supersede-and-replay contract (`AD_APPLICABILITY_SCHEMA_REVIEW.md:74-80`, `DATA_MODEL.md`) is unproven. Re-approval behavior is unknown.

**F3 — Released-catalog gate is tested only against stubs.** `test_ad_ingestion.py` monkeypatches `app.api.routes.ads.full_text_pages_for_extraction` and `persisted_source_pages`; the retained PDF is `b"%PDF-1.4\nretained AD test source\n%%EOF\n"` — unparseable. The "catalog independently rechecks the gate" claim is not exercised end-to-end.

**F4 — `affectedProducts` contradiction.** `AD_APPLICABILITY_SCHEMA_REVIEW.md:22` says reviewer edits "are ignored or rejected if inconsistent"; `ad-calibration/README.md:99` instructs "Preserve the existing affected-product list." No test supplies an inconsistent value. The `API_CONTRACT.md` example response still shows authored `affectedProducts`/`complianceActions`.

**F5 — Vacuous verification checks in `ad_compliance_population.py`.** `:150-153` names `no_deterministic_full_text_approval` but implements `all(reviewId is not None)` and reports an unrelated `queued` count — the safety property is not tested. `:139-142` `all_retained_pdfs_are_routed` is tautological. `prepare_ad_compliance_reviews.py:15` hardcodes `--expected-publications 17` as an unjustified `SystemExit(1)` gate. (Rollback-by-default is correct.)

**F6 — `audit_ad_review_evidence.py:69-74` normalization is lossy.** Compares a `removeprefix("AD ")` form against `directive.ad_number`, but `official_ad_number()` maps `1995-21-15`→`95-21-15`. Pre-2000 records (incl. 1998-17-11) will misclassify. Read-only, so not a blocker.

**F7 — Counter semantics mislead.** `_review_read` sets `canApprove = not blockers and status == "pending"`, while the envelope's `approvalReadyCount` counts blockers only *(unverified)* — so the banner on `ads/page.tsx:79` and `reviews/page.tsx:73` can overstate actionable work. `quarantinedCount = total - verified` collapses `missing`/`identity_unverified`/`identity_mismatch` into one label the docs treat as distinct.

**F8 — O(N) recompute on catalog load.** `ads/page.tsx:57` calls `listAdExtractionReviews(0, 1)` purely for counts, but the list handler loops every review computing bounded pages *(unverified)*. Costly at 33 reviews, untenable at scale.

**F9 — Publish-button asymmetry.** `reviews/page.tsx:181`: Approve is gated on `!canApprove`; **Edit, validate & publish** is gated only on pending + verified + v3, so it stays enabled beneath an "approval blocked" banner and relies on a server 422. Fail-closed but confusing. Reject correctly stays enabled.

**F10 — Local-filesystem links bypass authz.** `README.md:38,45,52,59,67,74` link `backend/.data/ad-sources/...`. Dead for any human not on the authoring machine, and they route around the `_require_platform_admin`-gated `contentUrl`. The UI also truncates SHA-256 to 16 chars (`reviews/page.tsx:150`) with no verify affordance.

**F11 — `list_discovery_records` requires only `get_current_user`** *(unverified)* — any authenticated shop/owner can enumerate discovery records. Low sensitivity (public FR metadata) but outside the packet's stated admin posture and undocumented.

**F12 — Frontend `isAdmin` omits `status === "active"`** (`reviews/page.tsx:16`, `ads/page.tsx:23`) while the backend requires it. Cosmetic; server is authoritative.

**F13 — `ad_number` filter also matches title** *(unverified)*, contradicting the labeled "AD number" field (`ads/page.tsx:139`).

**F14 — `correct_approved_ad_review.py:132`** unguarded `corrected_output["confidence"]` → `KeyError` on a patch that drops the key.

---

## What is genuinely solid

Admin gating on `extraction-reviews`, the decision POST, and `source-documents/{id}/content`, with negative shop tests (`test_ad_ingestion.py` shop 403 on both). Server-side authenticated `contentUrl` rather than raw publisher URLs. Bounding tests are the strongest artifact in the packet: `test_formal_target_heading_wins_over_earlier_cross_reference`, `test_document_bounding_rejects_foreign_rule_that_only_references_target_ad`, and `test_source_evidence_requires_official_identifier_and_part_39_heading` (including the `95±21±15` OCR form) prove real identity discrimination. `test_requirement_uncertainty_blocks_approval` and the paraphrase/typography/ordered-citation trio prove `actionText` fidelity. Reject/remediation stays available for quarantined records. Both mutating scripts default to rollback.

---

## Verdict

# FAIL FOR HUMAN CALIBRATION

Not because the gate is unsafe — the approval gate is the strongest part of this packet — but because **the calibration set cannot be loaded through it (B1, B3), does not exercise the v3 model under review (B2), was authored by the same tooling it is meant to calibrate (B4), and ships two out-of-band mutation paths that can publish and misattribute approved regulatory data (B4, B5).** B6 means even a repaired paste would seed the human with wrong wording and wrong requirement types.

**Minimum to reopen:** fix B1–B6; add the hash-mismatch pinning test (F1) and a re-approval/supersession test (F2); make `stage_*` v3-only and stamp proposal provenance visibly in the GUI; require an explicit admin actor and a `re-review` status transition in `correct_approved_ad_review.py`.

## Recommended human record order (post-fix)

Ascending structural difficulty, each adding one new v3 dimension:

1. **2024-14-03** — 2 requirements, clean; validates the basic v3 envelope. Must be un-quarantined and re-staged v3 first. *Add the Garmin equipment condition this record actually needs.*
2. **2011-10-09** — recurring + whichever-first + explicitly non-terminating correction; validates trigger/terminating semantics.
3. **2002-13-04** — serial-range scope and engine-family branching; first real `serialNumberApplicability` + multi-group test.
4. **1998-17-11** — applicability-determination vs. requirement boundary, and genuine alternatives; forces the open modeling question.
5. **2008-26-10** — two-document packet, IFR/non-IFR split, whichever-first *and* whichever-later, temporary placarding, reporting. Hardest; do last, and only after `installation_prohibition` due-state policy is defined.

**Before record 1, add a sixth record with two distinct manufacturers in one AD.** Nothing in the current set can detect the exact v2 failure — sibling manufacturer/model strings — that motivated v3.
