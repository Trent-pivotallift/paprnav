# Native Text Selective Routing Activation

Date: 2026-07-26

## Outcome

**14 passed out of 14**

| Group | Passed | Native bypass | Textract |
| --- | ---: | ---: | ---: |
| Frozen OCR refinement | 11/11 | 0 | 11 |
| Controlled fixtures | 3/3 | 2 | 1 |
| Total | 14/14 | 2 | 12 |

Selective native-text routing is active under:

`active_controlled_fixture_gate_v1`

This is an engineering activation, not final production proof. When
early-adopter PDFs enter ingestion, Paprnav must execute the mandatory
real-document checkpoint in
`.ai/EARLY_ADOPTER_NATIVE_TEXT_REVIEW.md`. Every initially native-routed
early-adopter page is reviewed against its canonical render; any critical
information-loss failure pauses native bypass and returns uncertain pages to
Textract.

## Controlled Fixtures

- `pure_native.pdf`: native-routed; one entry and all date/time fields matched.
- `native_table.pdf`: native-routed; two entries, reading order, dates, tach,
  total-time values, and AD-reference handling matched.
- `mixed_native_image.pdf`: Textract-routed because material maintenance
  values and approval evidence exist inside a displayed image.

The fixture PDFs, exact hashes, expected text, routes, entry counts, and
structured values are frozen in
`backend/tests/fixtures/native_text/manifest.json`.

## Routing Behavior

- Reliably native pages create provider-neutral native spans and do not call
  Textract.
- Scanned, handwritten, mixed, degraded, spread, image-dominant, or uncertain
  pages continue to Textract.
- For a mixed multi-page PDF, Paprnav creates a derived PDF containing only
  Textract-routed pages and maps provider page numbers back to immutable source
  page numbers.
- Original PDFs and canonical renders remain unmodified.
- Routing decisions, source provider, bypass count, Textract count, and source
  page lists are recorded.
- Native pages have a zero billable OCR page count.

## Activation Criteria

Every native-routed page must meet all of these:

- at least 50 meaningful characters and 8 words;
- valid glyph ratio at least 0.995;
- positioned text ratio at least 0.98;
- plausible font geometry ratio at least 0.98;
- duplicate-line ratio no greater than 0.05;
- extraction-mode agreement at least 0.98;
- estimated displayed-image coverage no greater than 0.25;
- routing class exactly `native_text`;
- no handwritten, side-by-side, faint, degraded, orientation-uncertain,
  layout-uncertain, or text-mode-uncertain attribute.

Failure of any criterion routes the page to Textract.

## Regression

- Pre-activation fixtures: 3 passed out of 3; 0 native, 3 Textract.
- Post-activation fixtures: 3 passed out of 3; 2 native, 1 Textract.
- Frozen scanned pages: 11 passed out of 11; all Textract.
- Combined routing gate: 14 passed out of 14.
- Focused selective-routing regression: 30 passed out of 30.
- Complete backend regression: 100 passed out of 100.
- Fixture regeneration reproducibility: passed.
- Canonical fixture visual inspection: passed.
- Alembic head remains `20260726_0015`.

## Refinement Found During Activation

The first table-fixture run produced 2 passed out of 3 because the parser
treated the explicit `AD 2021-03-04` reference as a third entry date. The
general parser rule was corrected: an explicit AD-reference date cannot become
a maintenance-entry anchor. Both pre- and post-activation gates then passed.

## Preserved Boundaries

- The ingestion/AD holdout was not opened.
- Layout-first GLM-OCR and Ollama remain paused.
- Stronger multimodal recognition remains a future escalation for unresolved
  regions only.
- The controlled fixtures are not a substitute for reviewing native-routed
  pages from early adopters.
