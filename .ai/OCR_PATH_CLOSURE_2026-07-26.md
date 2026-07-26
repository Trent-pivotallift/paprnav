# OCR Path Closure

Date: 2026-07-26

Status: complete for the approved OCR-refinement scope

## Production Path

Paprnav's selected path is:

1. retain the original uploaded PDF unchanged;
2. inspect and fingerprint the document and physical pages;
3. render immutable canonical 300-DPI page images;
4. classify page content, layout, and uncertainty;
5. use native PDF text only when every conservative reliability criterion
   passes;
6. route scanned, handwritten, mixed, degraded, image-dominant, spread, and
   uncertain pages to Textract;
7. normalize provider evidence into page-relative spans and logical regions;
8. validate parser candidates without inventing absent values;
9. require evidence-backed human review before verified maintenance data; and
10. retain original/canonical evidence for audit and future printing.

Stronger recognition is not part of the ordinary path. It may be reconsidered
only as an explicitly approved escalation for unresolved regions.

## Closure Evidence

- frozen PDF refinement: **11 passed out of 11**;
- controlled native routing: **3 passed out of 3**;
- combined selective-routing gate: **14 passed out of 14**;
- focused selective-routing regression: **30 passed out of 30**;
- complete backend regression after Google evaluation: **103 passed out of
  103**;
- frontend production build: **1 passed out of 1**;
- repository diff whitespace validation: passed;
- original PDFs and canonical page artifacts preserved;
- ingestion/AD holdout remained untouched.

Native bypass is active under `active_controlled_fixture_gate_v1`: two
controlled native fixtures bypass Textract and the mixed fixture remains
Textract-routed. This is engineering activation, not real-customer production
proof.

## Provider Decisions

- **Textract:** retained for scanned and uncertain pages.
- **Native PDF text:** active only behind the conservative selective gate.
- **Layout-first GLM-OCR/Ollama:** paused historical experiment; failed
  completeness, safety/quality, and latency promotion criteria.
- **Mistral:** synthetic connectivity only; no customer-document promotion.
- **Google Enterprise Document OCR:** technical mapping passed 11/11, but the
  frozen quality gate passed 0/3; evaluation-only and not active routing.

## Work That Does Not Reopen This Path

The following are post-closure product/operations work, not unfinished OCR
engine refinement:

- complete full-ingestion-path and ingestion/AD holdout phases at their
  scheduled boundaries;
- review every initially native-routed early-adopter page until the
  production-proof checkpoint is satisfied;
- collect reviewer effort, accepted-field accuracy, evidence coverage, null
  preservation, latency, failure, retry, and cost metrics;
- add durable worker leasing, retry, idempotency, and dead-letter behavior; and
- reconsider Textract Custom Queries/adapters only after an approved,
  representative corpus supports separate training and testing.

Any future provider evaluation requires a new decision, approved pages,
predeclared quality/safety thresholds, provider-neutral evidence, and regression
against the frozen corpus.

## Branch Closure Gate

The OCR branch is ready to close when:

- backend and frontend verification pass on the final working tree;
- `git diff --check` passes;
- all intended OCR files are reviewed and committed together;
- ignored private OCR artifacts and local credentials remain untracked; and
- the branch is pushed and merged through the repository's normal review
  process.
