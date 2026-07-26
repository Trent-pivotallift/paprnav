# Google Document AI OCR Evaluation

Date: 2026-07-26

## Decision

Do not promote Google Document AI into active Paprnav routing.

The evaluation proved that Paprnav can send canonical page evidence to the US
Google Enterprise Document OCR processor and map the response into
provider-neutral spans. It did not demonstrate a quality advantage over
Textract on the frozen ground-truth slice.

Textract remains the scanned-page provider. Selective native-text routing is
unchanged. Google remains an evaluation-only candidate for a future,
explicitly approved unresolved-region comparison after early-adopter failures
produce a representative corpus.

## Scope

- Google project: `paprnav`
- location: `us`
- processor: `65d3fbf624c3b0ab`
- API channel: `us-documentai.googleapis.com`
- input: canonical 300-DPI RGB PNG for each physical source page
- partition: frozen `ocr_refinement`
- pages: aircraft 2-5 and engine 3-9
- full-ingestion and ingestion/AD holdout partitions: untouched
- active production routing: unchanged

Application Default Credentials authenticated the local evaluation. No API key
or service-account JSON was stored in the repository.

## Technical Gate

**11 passed out of 11**

All pages matched the frozen hashes, rendered under
`canonical-pdf-page-v1`, returned non-empty line/word output, produced valid
ratio geometry, retained source-page identity and canonical hashes, and
recorded latency, request labels, quality diagnostics, and estimated cost.

Aggregate provider time was `30.425950` seconds. Estimated cost was `$0.082500`
for 11 pages with image-quality and style add-ons enabled. This is an estimate,
not reconciled invoice cost.

That figure covers the retained final run only. The setup session also made one
mapping-failure request, one successful connectivity rerun, and an incomplete
full-run attempt that did not retain an audit summary. If that incomplete
attempt reached every page, the conservative session upper bound is 24
billable requests, or `$0.180000` at the configured rate. Reconcile the actual
charge in Google billing rather than presenting `$0.082500` as the session
total.

The first paid connectivity response exposed a schema mapping defect:
detected languages belong to Google line/token objects rather than layout
objects. The mapper was corrected, its regression gate returned 7 passed out
of 7, and the one-page connectivity rerun passed before the full partition.

## Frozen Quality Gate

**0 passed out of 3**

This uses the three pages with existing manually reviewed comparison ground
truth. It is separate from the 11-page technical gate.

| Page | Ground-truth requirement | Google result | Textract baseline |
| --- | --- | --- | --- |
| Aircraft 2 | Two entries; annual `2012-12-17`, tach `1276.8`, total `5405.5`; Jones uncertain date/times null | Merged two entries. Annual values were present, but Jones facility/credential text attached to the annual draft. | Two entries; annual fields correct; Jones uncertain fields null. |
| Aircraft 4 | Two entries; dates `2014-02-11`, `2014-12-10`; tach `1289.83`, `1293.2`; first total `5418.53` | Two entries, but the second tach was not structured. | Two entries and all expected numeric fields after parser refinement. |
| Engine 3 | Two visible handwritten regions; unsupported fields null | Ambiguous fields stayed null, but the parser produced one draft rather than two regions. | Two regions; uncertain structured fields null. |

Google also produced recognition defects on aircraft page 2, including
`determified`, `Date/215113`, and extraneous non-Latin glyphs. Confidence does
not make those values authoritative.

On pages without frozen field-level ground truth, Paprnav observed
plausible-looking candidates such as a future `2053-04-12` date and handwritten
time values. Validation and human review remain mandatory; these observations
are not scored as ground-truth failures until reviewed.

## Useful Finding

Google image-quality scoring strongly distinguished several degraded pages:
aircraft page 3 and engine pages 3, 5, 6, and 7 received scores below `0.012`.
This may help review prioritization or escalation eligibility, but it requires
calibration against reviewer outcomes before affecting routing.

## Artifacts And Boundaries

The ignored full result is:

`backend/.data/ocr-feasibility/output/google_document_ai_11_page_evaluation.json`

It contains extracted text and remains local/private. Do not register Google
in active provider selection, send untouched holdouts, replace Textract based
on the technical pass, or enable cross-cloud production processing without a
separate privacy, identity, cost-reconciliation, and promotion decision.
