# Review: T081-CAL-2024-14-03 (external-critic)

## 1. Scope Limitations

- **The working tree was actively being edited by another process during this review.** `backend/tests/test_ad_ingestion.py` was observed in a transiently non-parsing state (`IndentationError` at line 1138) and `backend/app/services/ad_extraction.py` / `backend/app/scripts/stage_ad_review_proposal.py` changed functional shape (e.g. `extraction_approval_blockers` was split into `extraction_approval_blocker_details` with stable `code`/`message` pairs, `validate_extraction_json_schema` became an explicit precondition of staging) between my first and later reads. I re-verified file hashes were stable for >20s before drawing conclusions, and re-ran the full backend suite to a settled result (`1 failed, 201 passed`) before finalizing. All findings below are against that final, stable snapshot; earlier transient errors I observed (schema-shape failures that later disappeared) are **not** reported as findings since they were artifacts of concurrent in-flight edits, not durable defects.
- This is a nested adversarial review: an internal `adversarial-implementation` pass (`.ai/review-runs/T081-CAL-2024-14-03/adversarial-implementation.md`, outcome FAIL) had already identified six issues (IA-001..IA-006) shortly before this review began. I independently re-verified each against the current code rather than trusting the prior report; IA-001, IA-002, IA-003, IA-004, and IA-005 now appear closed in code and covered by tests I inspected directly. IA-006 (concurrency/CLI test coverage) remains open — see CC-002.
- I did not execute the CLI end-to-end against a live PostgreSQL instance (no such instance was available in this sandbox); the audited-write/idempotency/rollback claims are verified only via the SQLite-backed unit test and direct code reading, not a live run.
- `backend/app/api/routes/ads.py`, `backend/app/schemas/ads.py`, and `backend/app/services/ad_release.py` are declared out-of-scope (prior T081 baseline) but were read to confirm the in-scope changes don't break their consumers; I did not perform a full adversarial pass on those files.

<!-- CLAUDE_FINDINGS_JSON -->
```json
[
  {
    "id": "T081-CAL-2024-14-03-CC-001",
    "severity": "medium",
    "invariant": "The full backend test suite passes for the reviewed tree; a safety-relevant recurring-AD/adjudication scenario has working, verifiable test coverage.",
    "summary": "backend/tests/test_full_product_readiness.py::test_scenario_05_recurring_ad_requires_adjudication reproducibly fails because the shared _approved_ad/create_approved_extraction fixture writes complianceIntervals as a list of raw dicts, but the v3 schema (AD_EXTRACTION_JSON_SCHEMA.complianceIntervals) requires an array of strings; this only surfaces when a non-empty intervals argument is supplied (the recurring scenario is the only caller that does so), so extraction_has_signed_release(...) returns False and the fixture's own internal assertion fails before the test's adjudication assertions run.",
    "evidence": [
      "backend/tests/test_ad_matching.py:609 sets \"complianceIntervals\": compliance_intervals (raw dicts from the caller) directly into the extraction output.",
      "backend/tests/test_full_product_readiness.py:290-320 builds output2 via `**extraction.output` spread without overriding complianceIntervals, so the dict-valued list survives into the v3 payload.",
      "backend/app/services/ad_extraction.py:214 declares \"complianceIntervals\": {\"type\": \"array\", \"items\": {\"type\": \"string\"}} in AD_EXTRACTION_JSON_SCHEMA.",
      "backend/tests/test_full_product_readiness.py:354 `assert extraction_has_signed_release(extraction) is True` fails with `False is True`.",
      "Reproduced independently via a minimal script that isolates the schema check: validate_extraction_json_schema raises 'AD extraction schema error at $.complianceIntervals[0]: must be string' for this fixture's output.",
      "`PYTHONPATH=. .venv/bin/pytest -q` on the current tree: `1 failed, 201 passed` — the only failure is this test, reproducible across repeated runs."
    ],
    "impact": "The only full-product-readiness scenario that exercises a recurring compliance interval end-to-end (matching -> due-state -> needs_adjudication) is currently red, so there is no passing regression test proving recurring-AD adjudication behavior on the current v3 schema. This is fixture drift rather than a proven production defect (a real extraction pipeline independently validates complianceIntervals before it could reach this state), but it leaves a safety-relevant path unverified and the branch's CI signal is not green.",
    "requiredClosure": "Fix the shared fixture(s) in test_ad_matching.py/test_full_product_readiness.py so complianceIntervals is a list of human-readable strings consistent with the v3 schema (e.g., derive a sourceText-style summary from `intervals`, mirroring how compliance_actions is built), and confirm `pytest` is fully green before this task is considered mergeable."
  },
  {
    "id": "T081-CAL-2024-14-03-CC-002",
    "severity": "medium",
    "invariant": "Design invariant (decision.md, 'Test strategy'): the staging CLI's same-row locking against terminal-state conflicts and its dry-run/commit split must have executable proof, not just manual verification.",
    "summary": "The new staging CLI (backend/app/scripts/stage_ad_review_proposal.py) still has no automated test for (a) a real cross-session/PostgreSQL race between staging and the HTTP approval endpoint acquiring the same `FOR UPDATE` row, or (b) the CLI's `main()` dry-run path (no `--commit`) leaving zero persisted state. This gap was already identified by the internal adversarial-implementation review as IA-006 and remains unresolved even though IA-001/002/003/004/005 from the same report have since been fixed in code.",
    "evidence": [
      "backend/app/scripts/verify_ad_review_concurrency.py:1-40 (and full file) only seeds and races two terminal `decide_extraction_review`-style decisions; it never imports or calls `stage_review_proposal`.",
      "backend/tests/test_ad_ingestion.py has exactly two staging-specific test functions (`test_visual_ocr_draft_exception_is_limited_to_an_exact_cited_model_cell`, `test_staging_complete_proposal_is_audited_idempotent_and_reversible`); none invoke `app.scripts.stage_ad_review_proposal.main()` or exercise the `--commit`-absent rollback path.",
      ".ai/review-runs/T081-CAL-2024-14-03/adversarial-implementation.md finding T081-CAL-IA-006 states the same gap and notes the only cross-path evidence is a one-off manual live-PostgreSQL check, not a reproducible test."
    ],
    "impact": "The row-locking/serialization guarantee between staging and human approval (closed design finding T081-CAL-DA-002) has plausible code but only manual, non-reproducible verification of its concurrency behavior; a future refactor of either code path could silently reintroduce a race with no CI test to catch it. Similarly, a bug in the dry-run/rollback branch of `main()` (e.g. accidentally committing) would not be caught automatically.",
    "requiredClosure": "Add an automated PostgreSQL-backed test (can reuse the pattern in verify_ad_review_concurrency.py) that starts a `stage_review_proposal` transaction, blocks on the same review row, and proves a concurrent `decide_extraction_review` sees the row already locked/updated and vice versa; add a unit test that runs `main()` (or an equivalent code path) without `--commit` and asserts the review/extraction/decision rows are unchanged afterward."
  }
]
```

## 2. Findings

### T081-CAL-2024-14-03-CC-001 — Recurring-AD readiness test is red due to a complianceIntervals schema mismatch

See machine block for full evidence. In short: `test_scenario_05_recurring_ad_requires_adjudication` fails deterministically on the current tree because its shared fixture builds `complianceIntervals` as a list of dict objects while the v3 schema this task's files help enforce (`AD_EXTRACTION_JSON_SCHEMA`) requires an array of strings. This is the only failure in an otherwise-green 202-test backend suite (`1 failed, 201 passed`), and it blocks verified proof of the recurring-AD → `needs_adjudication` path.

### T081-CAL-2024-14-03-CC-002 — Staging-vs-approval concurrency and CLI dry-run behavior remain untested

The internal adversarial-implementation pass for this exact task (`adversarial-implementation.md`, IA-006) flagged that the new `stage_ad_review_proposal.py` CLI has no automated test for a real cross-process row-lock race against the HTTP approval endpoint, nor for its `--commit`-absent dry-run leaving zero persisted state. I independently confirmed the other five findings from that same report (IA-001 schema strictness, IA-002 `normalizedDesignation` null requirement, IA-003 GUI provenance resolution, IA-004 code-based rather than string-based blocker classification, IA-005 prior/extraction-output divergence check) are now fixed in code and covered by tests (`test_visual_ocr_draft_exception_is_limited_to_an_exact_cited_model_cell`, `test_staging_complete_proposal_is_audited_idempotent_and_reversible`). IA-006 is the one item from that internal report still open as of this review.

## Positive verification (not findings, but material to the review)

- I extracted the real retained PDF (`2024-15529.pdf`) with `pypdf` independently of the app and confirmed every OCR discrepancy claimed in `.ai/ad-calibration/2024-14-03.v3.proposal.json` (`172I`→`172T`, `F172E`→`Fl 72E`, `P172D`→`Pl 72D`, `R172K`→`Rl 72K`, `210G`→`2100`, `PA‑28RT‑201T`/`PA‑32R‑301T` with an inserted space) matches the actual page-4 table text byte-for-byte.
- I ran the real `validate_requirement_evidence` / `visual_ocr_validation_shadow` pipeline against that extracted text and the proposal JSON end-to-end; it validates cleanly (`EVIDENCE OK`), and `validate_extraction_json_schema` / `validate_extraction_output` both pass on the full proposal object.
- Confirmed the persisted proposal always keeps the visually-correct `sourceDesignation` (e.g. `172I`) while citation `text` fields verbatim retain the OCR-garbled source wording — the calibration draft does not silently normalize evidence, matching the stated invariant.
- Confirmed the OCR shadow substitution is narrowly scoped: it only ever rewrites `modelApplicability.models[i].sourceDesignation` inside `applicabilityGroups`, requires the cited page to belong to that same group, requires `normalizedDesignation` to be null (raises otherwise), and is never used to satisfy manufacturer/action/timing/condition/date/AMOC checks.
- Confirmed `decide_extraction_review` (the authenticated publish path, out of scope but a consumer) still calls the un-shadowed `extraction_approval_blockers`, so the OCR exception has no effect on real approval — matches invariant 4.
- Confirmed the requirements in the proposal correctly disposition paragraph (f) ("unless already done"), Note 1 (explicit typed uncertainty pending schema support), paragraph (h), and both AMOC sub-paragraphs — closing the design-stage findings T081-CAL-DA-003 concern at the artifact level.

## 3. Open Questions

- Is `.ai/ad-calibration/2024-14-03.v3.proposal.json` actually the payload that was staged onto review `arv_94f8a23dd22a457faf007aa588601018` in a real (non-sandbox) Postgres environment, and does live serialization there show `proposalProvenance.stagingMode == "allow_incomplete"` as the code now implies? I could not verify this against a live database from this sandbox.
- Should `test_scenario_05_recurring_ad_requires_adjudication`'s failure block this specific task's merge, given the buggy fixture lives in files declared out-of-scope for T081-CAL-2024-14-03 (`test_ad_matching.py`, `test_full_product_readiness.py`)? I've treated it as a blocking regression on the current tree regardless of attribution, but the coordinating process may choose to track it separately from this task.

## 4. Verification Notes

- `PYTHONPATH=. .venv/bin/pytest -q` (backend, full suite, final stable snapshot): `1 failed, 201 passed, 1 warning in ~33s`. The single failure is CC-001.
- `PYTHONPATH=. .venv/bin/pytest tests/test_ad_ingestion.py -k "staging or visual_ocr" -q`: `2 passed`.
- `npm run lint` (frontend): `0 errors, 1 warning` (pre-existing, unrelated `<img>` usage in a different file, matches the internal implementation report's note).
- Independently reproduced the real retained-PDF text extraction and ran `validate_requirement_evidence`, `validate_extraction_json_schema`, and `visual_ocr_validation_shadow` against the actual calibration proposal outside of pytest to confirm source fidelity (see Positive verification).
- Did not run `scripts/verify-t081-postgres-migrations.sh` or any live-PostgreSQL script; no such database was available in this environment.

## 5. Brief Summary

The calibration proposal for AD 2024-14-03 is source-faithful and internally consistent — I independently re-derived the retained PDF text and confirmed every claimed OCR discrepancy and evidentiary citation. The staging CLI's design has matured significantly through an internal adversarial-implementation cycle that ran just before this review; five of its six previously-open high/medium findings (schema strictness, normalized-identity leakage, GUI provenance, code-vs-string blocker classification, prior-output divergence) are now fixed and tested. Two issues remain: the full backend test suite is not green due to a `complianceIntervals` schema mismatch in a shared recurring-AD test fixture (CC-001), and the staging CLI's concurrency-race and dry-run behavior still lack automated test coverage, matching the still-open internal finding IA-006 (CC-002). Both are medium severity; no high/critical issues were found in the current, settled state of the reviewed files.