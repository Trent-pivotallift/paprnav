# Claude T081 remediation closure — 2026-08-22

Reviewer: Claude Opus, high effort, read-only CLI review

## First bounded audit

Verdict: `READINESS: FAIL`

Blocking findings:

1. `materialize_requirements_from_extraction` could approve a placeholder action when the extracted compliance action was empty.
2. Re-materializing a legacy extraction without an `amocProvisions` envelope could supersede reviewed relational AMOC rows.
3. Migration `20260822_0022` restored a five-column downgrade constraint instead of the original four-column constraint.

The audit also confirmed that trigger kinds and anchors were preserved, unresolved anchors failed closed, `whichever_first`/`whichever_later`/`alternative` semantics were distinct, group-scoped materialization was enforced, and the PostgreSQL NULL-safe expression index matched its duplicate preflight.

## Remediation

- Missing extracted actions now add `compliance_action_missing`; the placeholder is storage-only and cannot satisfy approval.
- AMOC materialization returns without supersession when the schema envelope is absent. A present empty v3 list remains an explicit statement that no provision was extracted.
- Migration `0022` now restores the original four-column constraint on downgrade.
- v3 requirement group references preflight before any requirement rows are added.
- Approval supersedes older approved extractions for the directive.
- Regression tests cover the missing-action and legacy-AMOC cases.

## Closure audit

Verdict: `READINESS: PASS`

Claude reported no new blocking finding and explicitly confirmed that all three prior blockers were fixed. It also confirmed that ambiguity paths end in `needs_adjudication` and due state `unknown`, rather than an actionable compliance state.

Two high-value, non-blocking hardening findings were applied after the PASS:

- Approved v3 extraction output is now hash-bound to the signed reviewer `decision_output`; a mismatch is recorded and reopens the review before materialization.
- Deterministic replay can widen a requirement toward adjudication but cannot silently promote a previously blocked row to approved.

Remaining non-blocking recommendations include explicit API handling for concurrent review decisions and component-time fallback semantics. They do not open an unreviewed publication or due-state path.

## Verification

- Focused recurrence/extraction verification: **40 passed out of 40**.
- Full backend verification: **176 passed out of 176**.
- Frontend lint: **0 errors**; one unrelated pre-existing image optimization warning.
- Frontend production build: passed; `/logbook/ads/reviews` is present.
- PostgreSQL migration: `20260822_0023 (head)`.
- v3 AMOC envelope backfill: extraction output **17 passed out of 17**,
  proposed-review output **17 passed out of 17**, and decided-or-pending review
  output **17 passed out of 17**.
- API health: passed.
- `http://localhost:3000/logbook/ads`: HTTP 200.
