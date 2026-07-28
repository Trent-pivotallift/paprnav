# OCR Billing Summary Refinement

Date: 2026-07-27

Status: complete

## Intent

Make pilot OCR usage measurable by customer account and aircraft without
pretending that AWS resource tags provide per-customer Textract chargeback.
This loop does not change OCR routing and does not open the 22-page integration
partition or 11-page ingestion/AD holdout.

## Implemented Path

1. Ingestion persists consent-derived billing status, customer account tag,
   aircraft tag, provider metadata, page count, configured pricing rate, and
   estimated cost on each `OCRRun`.
2. A platform administrator requests `GET /api/v1/admin/ocr-billing`.
3. Optional account, aircraft, billing-status, and half-open date filters
   select runs.
4. The service groups usage by customer account and aircraft.
5. Each group exposes provider version and API/channel mode.
6. Chargeable and non-billable pages and estimated costs remain separate.
7. Runs without sufficient persisted pricing metadata are counted explicitly
   as unpriced.
8. Failed and in-flight attempts are excluded from customer-attributable usage
   and counted separately.
9. Native bypass, Textract pages, non-page-priced runs, unattributed runs, and
   nonstandard billing statuses remain explicit.

Stored run estimates are authoritative for reporting. If an older run lacks an
estimate but retains its configured pricing rate and page count, the report
calculates their product only when the persisted pricing unit is `page`. Other
missing estimates are reported as unpriced. There is no hardcoded provider
price in the billing domain service.

## Boundaries

- Access is restricted to an active `platform_admin`.
- S3 object tags remain metadata and reconciliation aids.
- AWS Budget remains the aggregate project guardrail.
- The report is operational cost attribution, not an activated customer
  invoice or cost-allocation policy.
- The frozen 22-page integration partition and 11-page final holdout remain
  untouched.

## Verification

- Focused OCR billing endpoint/service tests: **5 passed out of 5**.
- Focused billing/routing/ingestion regression: **22 passed out of 22**.
- Post-review billing/selective/provider regression: **20 passed out of 20**.
- Complete backend regression: **110 passed out of 110**.
- Frontend lint: passed with **0 errors** and one pre-existing image warning.
- Frontend production build: **1 passed out of 1**.
- Frozen 22-page integration partition: **0 pages opened**.
- Frozen 11-page ingestion/AD holdout: **0 pages opened**.
- Independent Claude billing review: completed with four blocking findings.
  All four were addressed before closure review:
  - native-only routing preserves a zero billable-page count;
  - non-page-priced runs do not enter page totals;
  - failed/in-flight attempts are excluded and counted separately; and
  - date ranges are half-open to prevent adjacent-period overlap.
- Independent targeted closure review: **0 blocking findings**. It verified all
  four corrections and reported only non-blocking pilot-scale/future hardening
  notes.
