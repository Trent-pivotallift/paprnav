Now I have everything needed to write the final report.

## 1. Scope Limitations

- The review packet is ~18.9k lines; I read it in targeted sections (objective/invariants/finding ledger/manifest header) rather than linearly in full, and relied on `git`/file reads for the actual working tree rather than the embedded diff text for anything I verified in depth.
- I did not run the frontend lint/build or a fresh admin-browser walkthrough; I verified authorization purely from the backend route/service code, consistent with the packet's own disclosed limitation on this point.
- I ran the backend pytest suite and the provided PostgreSQL migration/concurrency/correction verification scripts against the live `db`/`api` containers (all passed) as primary independent evidence, rather than re-deriving every code path from first principles.
- Given the size of this slice (~4,100 changed lines across 12 backend service/route/model files plus 4 migrations), I prioritized the areas the decision packet identifies as safety-critical (release-signing boundary, applicability evaluation, recurrence/replay, migrations, correction, evidence binding) over exhaustive line-by-line coverage of every helper function.
- I did not independently re-derive OCR/PDF text-extraction correctness (e.g., pypdf behavior) beyond reading the code that consumes its output.

<!-- CLAUDE_FINDINGS_JSON -->
```json
[
  {
    "id": "T081-CC-001",
    "severity": "high",
    "invariant": "Every published applicability/requirement/AMOC field is supported by an exact citation to a retained source document and page; unrelated content must never enter the citation-eligible evidence pool.",
    "summary": "The evidence-scoping heuristic that isolates one AD's text from a combined/retained PDF fails open instead of failing closed when it cannot find the rule's closing 'FR Doc' footer, silently admitting all remaining document text (which can include a different, unrelated AD or notice) as citable evidence.",
    "evidence": [
      "backend/app/services/ad_extraction.py:1706-1711 — `footer = re.search(...); section_end = anchor_start + footer.end() if footer else len(combined)` extends the bounded section to end-of-document whenever no `[FR Doc...]`/`[PR Doc...]` footer pattern matches after the anchor.",
      "backend/app/services/ad_extraction.py:1725-1768 (`bounded_source_document_pages`) calls `bounded_issue_pages` unconditionally for every retained document (not just ones flagged `source_type == 'issue_pdf'`), so this same fail-open path is exercised on every approval/release/rehash re-scoping (`extraction_has_signed_release` -> `persisted_source_pages`; `decide_extraction_review`; `correct_approved_ad_review.py`; `stage_ad_review_proposal.py`).",
      "backend/app/services/ad_extraction.py:1808-1852 (`source_evidence_status`) only checks that the *target* AD's formal heading is present somewhere in the bounded pages; it never checks that the bounded section excludes a *different* AD's formal heading or otherwise bounds the tail, so an over-wide section still reports `verified`.",
      "backend/tests/test_ad_ingestion.py:784-829 exercises only the case where a trailing footer is present and correctly truncates; no test exercises a missing/unmatched footer, a footer using non-bracketed or non-English formatting, or an OCR-mangled footer."
    ],
    "impact": "If the footer regex fails to match for any reason (different Federal Register era formatting, OCR noise, a target rule that happens to be followed by non-rule matter without an `[FR Doc...]` marker), the reviewer's cited evidence pool silently includes unrelated regulatory text. Because `require_cited_wording`/`validate_timing_evidence`/`validate_requirement_evidence` only check that a field's claimed quote is a literal substring of the (now over-wide) citation set, a fabricated or misattributed manufacturer/model/serial/timing value that actually belongs to a neighboring rule can pass mechanical evidence validation and be approved as if it were sourced from the correct AD.",
    "requiredClosure": "When no closing footer (or equivalent authoritative section boundary, e.g. the next Part 39 heading) can be located after the anchor, fail closed: return no pages (or mark the evidence status as unverified/bounded-failure) rather than defaulting to end-of-document. Add negative tests for a missing footer, an OCR-corrupted footer, and a target rule immediately followed by a second rule with no recognizable separator."
  },
  {
    "id": "T081-CC-002",
    "severity": "medium",
    "invariant": "Each human decision (including corrections and pre-approval staging) is serialized, immutable, and fully actor-attributed; provider/staging output remains an untrusted proposal until an authenticated platform-admin decision.",
    "summary": "The two out-of-band administrative pathways that mutate an approved or in-review AD extraction outside the authenticated HTTP decision endpoint do not bind actor identity to a real session: the correction script only checks that a caller-supplied `--actor-user-id` happens to belong to an active platform_admin row (no credential/session proof), and the staging script records no actor identity at all.",
    "evidence": [
      "backend/app/scripts/correct_approved_ad_review.py:68-87 accepts `--actor-user-id` as a bare CLI argument and only verifies the referenced row is `active`/`platform_admin`; nothing proves the process invoker is that user.",
      "backend/app/scripts/stage_ad_review_proposal.py:24-105 has no `--actor-user-id` (or any identity) argument at all; `record_workflow_status(..., actor_type='system')` at line 104 records no user.",
      "Contrast with backend/app/api/routes/ads.py:598-609 (`decide_extraction_review`), which derives the actor from `Depends(get_current_user)` — an authenticated session — for the normal decision path."
    ],
    "impact": "The correction and staging workflows are exactly the pathways used to quietly rewrite a previously-approved regulatory decision (the case T081-DA-6/DC-2 were concerned with). Anyone with container/shell access to run these scripts can attribute a correction to any platform-admin user id of their choosing, or stage a v3 draft with zero recorded actor at all, weakening the non-repudiation guarantee the packet's 'Trust, authorization, and audit boundaries' section claims for reviewer/actor identity.",
    "requiredClosure": "Either restrict these scripts to a trust boundary equivalent to direct database access and document that explicitly as the accepted operational model, or require the same authenticated-session identity used by the HTTP decision endpoint (e.g., a signed operator token validated against `User`/session state) before recording actor attribution, and record an actor for every staging event."
  },
  {
    "id": "T081-CC-003",
    "severity": "medium",
    "invariant": "Calibration exercises the v3 failure modes claimed by the design, including group, serial, equipment, AMOC, and correction/release negative cases (design item 10 / ledger T081-DA-10).",
    "summary": "Independently confirmed that T081-DA-10 remains open: all five `.ai/ad-calibration/*.requirements.json` files are still v2-style requirement-only arrays (no `applicabilityGroups`, no `amocProvisions`, no negative aircraft/component adjudication cases), and the linked v3 reviews are explicitly documented as pending/incomplete.",
    "evidence": [
      ".ai/ad-calibration/README.md:1-8 states plainly: 'the linked records are new pending v3 reviews... The remaining four were never completed.'",
      "Each of .ai/ad-calibration/{1998-17-11,2002-13-04,2008-26-10,2011-10-09,2024-14-03}.requirements.json parses as a bare JSON list of requirement objects (verified by inspection), not a complete `{applicabilityGroups, requirements, amocProvisions}` v3 packet."
    ],
    "impact": "No end-to-end proof yet exists that the shipped v3 schema/evaluator correctly reproduces the five targeted compliance structures (whichever-first, conditional branches, AMOC separation, etc.) against real source text with expected positive/negative outcomes, so the calibration cannot yet be used to validate reviewer behavior or catch regressions in `ad_recurrence.py`/`ad_matching.py` logic.",
    "requiredClosure": "Complete the five v3 packets in the admin GUI (as the README already directs), including expected positive and negative aircraft/component adjudication outcomes for each, before relying on this set as calibration evidence for broader release."
  },
  {
    "id": "T081-CC-004",
    "severity": "low",
    "invariant": "The review packet's prose (objective, current behavior, expected file scope) accurately reflects the reviewed working tree so a reviewer can trust the narrative without independently re-deriving the manifest.",
    "summary": "The decision packet's prose is stale relative to the actual working tree: it states 'PostgreSQL is at `0023`' and lists 'migrations `20260822_0021`-`0023`' as the expected file scope, but the working tree contains a fourth, untracked migration `20260823_0024_bind_signed_ad_materialization.py` that is required to close T081-DA-4/DA-9(partially)/DC-2/DC-3, is the current alembic head, and is only discoverable via the JSON manifest, not the prose.",
    "evidence": [
      ".ai/review-runs/T081/review-packet.md:75 — 'PostgreSQL is at `0023`'.",
      ".ai/review-runs/T081/review-packet.md:232-236 — 'Expected file scope' lists migrations `20260822_0021`-`0023` only.",
      "backend/app/db/migrations/versions/20260823_0024_bind_signed_ad_materialization.py exists (untracked, `git status` shows `??`) and is the alembic head confirmed by `alembic current` after `run_alembic upgrade head` in scripts/verify-t081-postgres-migrations.sh."
    ],
    "impact": "A reviewer who trusts the prose summary (as the instructions otherwise encourage doing for framing) could under-scope review of the most consequential new migration in this slice, and could mistakenly believe the AMOC-envelope repair (DA-4/DC-2) is still unaddressed when it has in fact been implemented and tested in 0024.",
    "requiredClosure": "Regenerate or hand-correct the decision-packet prose to name migration `0024` and its purpose, and update 'PostgreSQL is at' to the actual current head before the packet is used for closure sign-off."
  }
]
```

## 2. Findings

### T081-CC-001 — Evidence-bounding heuristic fails open when no closing footer is found

**Invariant violated:** "Every published v3 applicability group, compliance action, threshold, recurring trigger, terminating action, and AMOC authority is supported by an exact citation to a retained source document and one-based page" (invariant 1); "Unsupported mechanical binding remains adjudication-blocked" (design item 8).

**Evidence:**
- `backend/app/services/ad_extraction.py:1706-1711` — if the `[FR Doc...]`/`[PR Doc...]` footer regex doesn't match after the AD's anchor, `section_end` defaults to `len(combined)`, i.e. "everything to the end of the retained text."
- `backend/app/services/ad_extraction.py:1725-1768` (`bounded_source_document_pages`) applies this same heuristic to *every* retained document unconditionally — this is the function used at approval time (`decide_extraction_review`), release-signing time (`ad_release.py` → `persisted_source_pages`), correction (`correct_approved_ad_review.py`), and staging (`stage_ad_review_proposal.py`).
- `source_evidence_status` (`ad_extraction.py:1808-1852`) only confirms the *target* AD's own heading is present in the bounded text; it never confirms the bounded text stops before a *different* AD's content, so an over-wide section still reports `verified`.
- `backend/tests/test_ad_ingestion.py:784-829` only tests the "footer present" case.

**Impact:** A missing/unrecognized footer (different era formatting, OCR noise, or a rule immediately followed by non-rule matter) silently widens the citation-eligible evidence pool to include unrelated text. Since field-level evidence checks (`require_cited_wording`, `validate_timing_evidence`) only verify a claimed quote is a literal substring of the (now too-wide) citation set, this can let a value sourced from an unrelated rule pass mechanical evidence validation for the AD under review — the exact "genuine but unrelated text" failure mode the design explicitly worries about (T081-DA-8).

**Required closure:** Fail closed (return no pages / report an unverified-boundary status) when no closing marker can be found, rather than defaulting to end-of-document. Add tests for missing/garbled footers and for a target rule immediately abutting a second rule.

### T081-CC-002 — Correction/staging admin scripts do not cryptographically bind actor identity

**Invariant violated:** "Corrections preserve the prior signed decision and actor attribution" (invariant 10); "Platform-admin authentication is the human decision boundary… Reviewer identity… form the audit record" (trust/authorization section).

**Evidence:**
- `backend/app/scripts/correct_approved_ad_review.py:68-87` takes `--actor-user-id` as a bare CLI argument, checking only that the referenced row is active/platform_admin — no session or credential is verified.
- `backend/app/scripts/stage_ad_review_proposal.py` has no actor argument at all; `record_workflow_status(..., actor_type="system")` (line 104) records no user identity.
- Contrast: `backend/app/api/routes/ads.py:598-609` derives the actor from an authenticated session (`Depends(get_current_user)`) for the normal decision endpoint.

**Impact:** These are precisely the two pathways used to rewrite an already-approved regulatory decision or introduce a "human-cited" v3 draft. Anyone with container/shell access can attribute a correction to an arbitrary platform-admin id, or stage a draft with zero attributed actor, undermining the non-repudiation the packet's trust section claims.

**Required closure:** Either explicitly document these scripts as operating at the same trust tier as direct database access, or require the same authenticated identity mechanism used by the HTTP endpoint, and always record an actor for staging events.

### T081-CC-003 — Calibration set (T081-DA-10) remains open and incomplete

**Invariant violated:** Design item 10 ("The five calibration records become complete v3 packets…").

**Evidence:** `.ai/ad-calibration/README.md:1-8` states the five records are "new pending v3 reviews" and "were never completed"; the five `*.requirements.json` files are bare arrays of legacy requirement objects, not complete v3 packets with applicability groups, AMOC data, or expected negative outcomes.

**Impact:** No end-to-end calibration proof yet exists for the targeted compliance patterns (whichever-first/later logic, conditional branches, AMOC separation, correction/release behavior).

**Required closure:** Complete the five packets in the admin GUI with expected positive/negative outcomes before relying on this set as calibration evidence.

### T081-CC-004 — Decision-packet prose omits migration 0024 and understates current schema head

**Invariant violated:** Review-packet completeness/accuracy for scoping (adversarial-review process guarantee, not a product invariant).

**Evidence:** `.ai/review-runs/T081/review-packet.md:75` ("PostgreSQL is at `0023`") and `:232-236` ("Expected file scope" lists only migrations `0021`-`0023`), while `backend/app/db/migrations/versions/20260823_0024_bind_signed_ad_materialization.py` is untracked, present in the working tree, and is the actual alembic head (confirmed via `alembic current` after `upgrade head`).

**Impact:** A reviewer relying on the narrative alone could under-scope the most consequential migration in this slice (the one that actually closes DA-4/DC-2/DC-3), or wrongly conclude those items are still unaddressed.

**Required closure:** Correct the packet prose to name migration `0024` and the current head before using this packet for sign-off.

## 3. Open Questions

- Is it an accepted, documented operational model that `correct_approved_ad_review.py` and `stage_ad_review_proposal.py` run only from a trust tier equivalent to direct production database access (e.g., ECS exec by an already-authenticated on-call admin), making the actor-binding gap in T081-CC-002 an accepted risk rather than a defect? The packet doesn't state this explicitly.
- Are all currently retained AD source PDFs guaranteed to end each rule with a `[FR Doc...]`/`[PR Doc...]` style footer (i.e., is T081-CC-001's fail-open path currently unreachable in practice for the corpus in scope), or could a future ingestion source (e.g., GovInfo bulk PDFs, non-US-style formatting) hit it?
- Why does the finding ledger in the packet still list all thirteen `T081-DA-*`/`T081-DC-*` items as `"status": "open"` with empty `closureEvidence` when the working tree and passing verification scripts (`scripts/verify-t081-postgres-migrations.sh`, `verify_ad_review_concurrency`, `verify_ad_correction_workflow`) demonstrate substantive closure for most of them? Is ledger reconciliation expected to happen after this external-critic pass, or was it deliberately left open pending my independent confirmation?

## 4. Verification Notes

- Ran the full backend suite: `PYTHONPATH=. .venv/bin/pytest -q` → **193 passed**.
- Ran `scripts/verify-t081-postgres-migrations.sh` end-to-end against the live `db`/`api` containers (fresh scratch database): upgrade to head, downgrade to `0023`, seeded three fixture rows (null-decision terminal review, nonempty AMOC, partial/empty AMOC), re-ran `upgrade 20260823_0024` — **11 passed out of 11**, including idempotent-rerun, guarded-irreversible-downgrade (both with live v3 data and with only origin-marked extractions), and exact `0021`-vs-`0022` parent-constraint-fidelity checks. This directly and independently confirms substantive closure of `T081-DA-4`, `T081-DC-1`, and `T081-DC-2` beyond what the (still "open") ledger records.
- The same run also executed `python -m app.scripts.verify_ad_review_concurrency` (**7 passed out of 7**, a real threaded concurrent-decision test) and `python -m app.scripts.verify_ad_correction_workflow` (**12 passed out of 12**, all boolean checks `true`: applicability/requirements/AMOC/due-state/coverage/match revocation, review reopened, decision snapshot retained, released reader excludes the correction) — independently confirming `T081-DA-6` and `T081-DA-7`.
- Traced the centralized release boundary (`backend/app/services/ad_release.py`) and confirmed catalog (`ads.py:212-232`), matching (`ad_matching.py:37,183-184`), and coverage (`ad_coverage.py:26,182`) all route through `released_signed_extractions`/`released_extraction_for_directive`, which check schema version, input-hash equality, decided-review output-hash equality, reviewer active/platform_admin status, and freshly rehashed retained bytes — this closes `T081-DA-2`/`T081-DC-3`'s core complaint.
- Traced tri-state applicability evaluation (`ad_matching.py:531-576`, `578-635`) and confirmed model/serial/equipment/expression/unknown scopes explicitly return `uncertain`/`not_applicable` rather than defaulting to applicable — closes `T081-DA-1`.
- Traced `requirements_for_applicability` (`ad_recurrence.py:776-804`) replaying all current signed requirements per applicability row rather than a single legacy interval — closes `T081-DA-3`.
- Traced `ensure_review_for_extraction` (`ad_extraction.py:630-687`) detecting output-hash mismatches between a decided review and its extraction and reopening review — closes `T081-DA-11`.
- Traced `verified_retained_document_bytes` being called on every read/validation of cached pages (including inside `persisted_source_pages`, which gates `extraction_has_signed_release`) — closes `T081-DA-9`.
- Did not run frontend lint/build; relied on backend server-side authorization gates (`ensure_ad_extraction_reviewer`, `is_platform_admin`) as the actual trust boundary for admin-only surfaces.

## 5. Brief Summary

This slice substantially and verifiably closes the prior design-adversary/design-closure blockers (DA-1–DA-9, DA-11, DC-1–DC-3) via a new centralized release-signing boundary, tri-state applicability evaluation, per-obligation recurrence replay, row-locked/immutable review decisions, and a well-tested corrective migration (`0024`) — all confirmed by passing the full backend suite plus live PostgreSQL migration, concurrency, and correction-workflow verification scripts. Independent review surfaced one high-severity residual gap (an evidence-bounding heuristic that fails open instead of closed when a source document's closing footer can't be located, potentially admitting unrelated-AD text into the citation-eligible evidence pool), one medium-severity actor-attribution gap in the correction/staging admin scripts, confirmation that the calibration set (DA-10) remains genuinely incomplete, and a low-severity staleness issue in the review packet's own prose regarding migration `0024`.