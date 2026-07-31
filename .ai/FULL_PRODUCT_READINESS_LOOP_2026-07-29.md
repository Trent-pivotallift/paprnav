# Controlled Full-Product Readiness Loop

Date: 2026-07-29

Status: completed 2026-07-30

## Intent

Prove Paprnav's integrated path from retained source PDF through human-reviewed
logbook evidence and AD/DRS comparison before opening the limited production
training partitions. This is product-path validation, not OCR-provider tuning.

The frozen 22-page full-ingestion partition and 11-page ingestion/AD holdout
must remain unopened throughout this loop.

## Controlled Evidence

- PDF: `backend/tests/fixtures/native_text/pure_native.pdf`
- AD/DRS: deterministic synthetic records derived from the existing DRS,
  applicability, matching, and coverage fixtures
- Aircraft: isolated fixture aircraft with airframe, engine, and propeller
  identities

The controlled PDF has one letter-sized page and visibly contains a dated
maintenance entry, times, performer credentials, explicit AD 2020-01-02
compliance language, and return-to-service text. It is suitable for proving
native routing, review, structured entry creation, and page evidence. It is not
used to claim general OCR quality.

## Predeclared Scenarios

| # | Scenario | Required outcome |
|---|---|---|
| 1 | Retained PDF through native ingestion and human review | Original bytes and canonical page remain available; native bypass is 1, Textract pages are 0; extracted entry starts unverified and becomes verified only through explicit review; page evidence remains attached |
| 2 | Applicable airframe AD with verified page evidence | AD 2020-01-02 is `candidate_satisfied`, selects the airframe, and links to the verified entry/page evidence |
| 3 | Applicable engine AD | Matching selects the installed engine and does not collapse applicability to the airframe |
| 4 | Applicable propeller AD | Matching selects the installed propeller and does not collapse applicability to the airframe |
| 5 | Recurring AD | Result is `needs_adjudication` with `recurring_due_status_unknown`; no automated compliance conclusion |
| 6 | Superseded AD | Result is `needs_adjudication` with `directive_superseded`; prior evidence remains visible but cannot produce a clean satisfied state |
| 7 | Applicable AD without evidence | Result is `needs_adjudication`, has no evidence links, and creates a pending review task |
| 8 | Unverified logbook claim | Unverified entry is excluded from evidence and cannot satisfy the AD |
| 9 | Degraded DRS source | Aircraft response reports degraded coverage and a user-facing warning; matcher completion cannot imply complete AD coverage |
| 10 | Second client with existing make/model/component coverage | Existing coverage is reused from the single retained source snapshot without creating another snapshot, first-trigger provenance is preserved, and shared/aircraft cost scopes remain separate and non-billable |

## Stage Gates

1. Contract: all 10 expectations are encoded before implementation.
2. Ingestion/review: scenarios 1-2 pass.
3. Applicability/adjudication: scenarios 3-8 pass.
4. Coverage reuse/cost: scenarios 9-10 pass.
5. Complete backend regression, frontend lint/build, PDF render inspection, and
   independent closure review pass.

## Stop Conditions

- Do not tune OCR gates from these scenarios.
- Do not open either frozen partition.
- Do not claim AD completeness from a degraded or missing DRS snapshot.
- Do not use unverified entries as compliance evidence.
- Do not activate customer billing or allocate shared AD/DRS cost.

## Verification

- Predeclared controlled scenarios: **10 passed out of 10**.
- Ingestion and human-review stage: **2 passed out of 2**.
- Component applicability and adjudication stage: **6 passed out of 6**.
- Degraded coverage and reuse/cost stage: **2 passed out of 2**.
- Focused cross-feature regression: **40 passed out of 40**.
- Complete backend regression: **125 passed out of 125**.
- Frontend lint: passed with **0 errors** and one pre-existing image warning.
- Frontend production build: **1 passed out of 1**.
- PDF visual inspection: **1 page out of 1**; all expected source information
  was visible and unclipped.
- Frozen 22-page integration partition: **0 pages opened**.
- Frozen 11-page ingestion/AD holdout: **0 pages opened**.

## Independent Review Corrections

The first independent review identified second-order safety gaps that the
initial clean-database scenarios did not exercise. The correction pass adds:

- assigned-maintenance authority and server-stamped reviewer attestation;
- platform-admin authority for AD extraction approval;
- immediate invalidation and historical/current separation after evidence
  changes;
- adjudication for plausibly applicable ADs with incomplete component
  identity;
- incomplete-identity and stale-snapshot coverage warnings;
- nullable historical evidence dates at the API boundary;
- an open manual-review state when extraction yields zero entries; and
- direct regression tests for authority, invalidation/recomputation, source
  date evidence, incomplete identity, and snapshot freshness.

The corrected focused safety suite passed **40 out of 40**. The complete
backend regression passed **125 out of 125**, frontend lint passed with zero
errors and one pre-existing image warning, the production build passed, and
the migration chain has one head at `20260730_0017`.

The first closure review confirmed B1, B2, B4, B5, and B6 and narrowed B3 to
new-directive fan-out. The second closure review confirmed subscription-based
fan-out, coverage refresh, zero-result invalidation, maintenance-only
verification revocation, retained attestation, nullable evidence dates, and
deterministic extraction deduplication. Its final empty-applicability edge was
closed by rejecting approval without at least one attributable product. The
edge closure review reported **0 blockers**.

The frozen 22-page integration partition and 11-page ingestion/AD holdout
remained unopened.
