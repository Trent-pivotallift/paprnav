# T081 adversarial implementation closure review — attempt 1

Reviewer: `/root/t081_implementation_closure`  
Builder/coordinator: `/root`  
Outcome: **FAIL**

The implementation packet was verified current against `HEAD` and the complete
staged, unstaged, and untracked working tree. Packet scope fingerprint:
`2c4c1a95e4969744d12b844e9d63c51147105ee143b40e912802498dc16c62a5`.

The current code closes the previously reproduced implementation defects. The
gate nevertheless cannot pass because two High findings still lack the
PostgreSQL closure evidence explicitly required by the accepted decision and
initial implementation review. These are proof gaps, not newly reproduced
runtime defects. Human calibration also remains deliberately deferred.

## Remaining findings

### T081-IC-1 — High — corrective migration cohort proof is incomplete

- **Invariant:** The 0024 repair deterministically covers every absent-origin
  v3 extraction/review state, preserves nonempty regulatory content, restores
  unknown rather than inventing empty meaning, records immutable pre-repair
  evidence, leaves no ambiguous approval released, and is idempotent on retry
  (T081-DA-4, T081-DC-2, and T081-IA-6 required closure).
- **Direct evidence:** `scripts/verify-t081-postgres-migrations.sh` exercises one
  v3 review with a null `decision_output` and an empty AMOC envelope. It verifies
  one repair snapshot, reopening, guarded v3 downgrades, the 0022-to-0021 index,
  the migration chain, concurrency, and correction sub-verifiers. No executable
  repository test covers an ambiguous legitimate-empty row beside a nonempty
  AMOC row, partial extraction/proposal/decision states, zero surviving
  approvals across the entire cohort, or a repair rerun/idempotency assertion.
  Repository-wide search found no second migration test containing these cases.
- **Impact:** The SQL is plausible and its principal defect has been corrected,
  but the strongest data-preservation claim remains unproved on PostgreSQL. A
  partial-state or cohort regression could silently alter signed regulatory
  meaning despite a green verifier.
- **Required closure:** Extend the isolated PostgreSQL verifier with the full
  DC-2 matrix, including empty and nonempty envelopes, partial review states,
  immutable before-images/hashes/actor metadata, zero terminal approvals after
  repair, and idempotent retry/no duplicate snapshot behavior. Alternatively,
  record an explicit High-risk acceptance with owner and rationale under the
  repository review process.

### T081-IC-2 — High — correction verifier does not prove all transactional revocations

- **Invariant:** Committed correction atomically preserves the prior decision,
  revokes applicability, requirements, AMOCs, current due states, current
  matches, and released reads, and quarantines affected coverage before
  reopening review (T081-DA-6 and T081-IA-1 required closure).
- **Direct evidence:** `backend/app/scripts/verify_ad_correction_workflow.py`
  seeds no `AircraftADDueState`, `ADMatchResult`, `ADCoverageSet`, or coverage
  subscription. Its eight assertions cover review/extraction/directive state,
  the immutable snapshot, applicability, requirements, AMOCs, and corrected
  output. It cannot assert due-state invalidation, match invalidation, coverage
  quarantine, or released-reader exclusion.
- **Impact:** Direct inspection confirms the correction implementation contains
  update paths for these objects, but the required committed PostgreSQL
  transaction proof is absent. A schema-specific failure in the unseeded half
  of the transaction would not be detected by the claimed 8/8 verifier.
- **Required closure:** Seed each affected derived object, execute the committed
  CLI, and assert all revocations plus catalog/release exclusion from a second
  session after commit.

### T081-IC-3 — Medium — complete human calibration remains deferred

The five `.ai/ad-calibration/*.requirements.json` files remain requirement-only
drafts. `.ai/ad-calibration/README.md` correctly states they cannot publish as
complete v3 packets and require human completion. This is the already-declared
T081-DA-10 / T081-IA-7 human calibration artifact, not a blocker to continuing
implementation remediation. It does block claiming end-to-end T081 calibration
complete. Closure requires five complete cited v3 packets and machine-checkable
positive, negative, and adjudication outcomes.

## Verified closure map

| Finding | Implementation closure evidence |
|---|---|
| T081-DA-1 / IA-5 applicability | Tri-state serial/model/equipment/condition evaluation fails closed; incomplete identity and mixed engine/propeller cases retain adjudication without uncertain due-state materialization. |
| T081-DA-2 | Release requires active attributed platform-admin decision, exact decided-output hash, current source-set input hash, and freshly verified source bytes/text. Catalog now enters through `released_signed_extractions`. |
| T081-DA-3 / IA-2 | Matching enumerates all applicable component/group contexts; v3 requirement lookup is exact by applicability identity; due states are linked per obligation. Mixed engine/propeller regression proves the engine evidence does not satisfy the propeller obligation. |
| T081-DA-4 | Migration 0023 no longer invents an envelope; 0024 conservatively reopens absent-origin rows, uses SHA-256 audit hashes, and blocks downgrade whenever any v3 extraction exists. Full cohort proof remains IC-1. |
| T081-DA-5 | Component recurrence no longer silently falls back to aircraft time. |
| T081-DA-6 / IA-1 | Invalid AMOC update was removed. Correction code supersedes applicability/requirements/AMOCs, clears current due states, invalidates matches, and quarantines coverage. Full transaction proof remains IC-2. |
| T081-DA-7 / IA-5 | Decision endpoint uses a database row lock and immutable winner/conflict events; the PostgreSQL two-session verifier checks 7/7 serialization and attribution outcomes. |
| T081-DA-8 | Manufacturer/model/serial/product type, equipment and requirement conditions, timing semantics, actions, and AMOC values are source-bound with negative tests. Unsupported canonical identities remain null/source-equal. |
| T081-DA-9 / IA-4 | Source download verifies and returns the same byte buffer. Release rehashes retained bytes, reparses PDF text, requires exact cached page-key/text equality, and rejects stale input document sets. |
| T081-DC-1 | Downgrade preflights precede destructive DDL; 0022-to-0021 restores the five-column identity and 0021-to-0020 restores four columns. |
| T081-DC-2 | Deterministic absent-origin cohort and immutable repair snapshot are implemented; exhaustive matrix proof remains IC-1. |
| T081-DC-3 | Applicability carries `source_extraction_id`; v3 materialization, catalog, matching, due-state exact reads, and coverage use the signed extraction chain. Catalog reconciliation repairs out-of-band derived target changes. |
| T081-IA-3 | Compose uses persistent `ad_source_data:/app/.data`; backup/import and post-rebuild hash audit are documented. |

## Latest review-list pagination / triage assessment

**No blocking finding.** `list_extraction_reviews` performs exact retained-byte
and re-derived-text verification only for the selected review page. Aggregate
counts use cached provenance and the current source-set hash without reading all
PDFs. Those counts are now explicitly labeled `source-indexed` and `approval
candidates`; frontend guidance says they are triage-only. A selected review,
approval decision, PDF download, and released read still pass through exact
verification. The availability optimization therefore does not expand the
authorization or release trust boundary.

## Verification

- Review packet currency: **PASS**, fingerprint shown above.
- Independent focused AD suite:
  `tests/test_ad_ingestion.py tests/test_ad_matching.py
  tests/test_ad_recurrence.py tests/test_ad_coverage.py` — **67 passed out of
  67**.
- Coordinator packet evidence reports product readiness **10/10**, backend
  **192/192** excluding the OCR partition, OCR **1/1**, frontend lint with zero
  errors, frontend production build PASS, and PostgreSQL aggregate **7/7** with
  concurrency **7/7** and correction **8/8**. The two findings above explain
  why the latter aggregate is not yet sufficient for formal closure.
- The reviewer could not independently rerun Docker verification in the prior
  turn because Docker socket escalation was not granted; direct code and test
  inspection was completed and the host focused suite was rerun independently.

IMPLEMENTATION OUTCOME: **FAIL**

