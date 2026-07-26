# PDF Extraction Methodology Handoff

Date: 2026-07-25

## Purpose

This document carries the conclusions from a side conversation into the main
Paprnav implementation thread. It proposes improving clear, auditable logbook
data extraction by adopting the strongest reusable practices from the PDF
inspection workflow.

This is not a proposal to resume Layout-first GLM-OCR or Ollama work. Those
paths remain paused.

## Executive Conclusion

Paprnav should evolve from a Textract-centered OCR pipeline into a
provider-neutral document-understanding pipeline:

```text
Current:
PDF -> Textract -> deterministic parser -> human review

Proposed:
PDF validation and fingerprinting
  -> canonical page rendering
  -> page and layout classification
  -> reliable embedded text when available
  -> OCR for pages or regions that require recognition
  -> provider-neutral spans
  -> structured extraction
  -> safety and consistency validation
  -> evidence-backed human review
  -> accepted ground truth and metrics
```

Textract remains the active recognition provider initially. The architectural
improvement is to make Textract one replaceable component rather than the
definition of the extraction workflow.

## Important Terminology

The supplied PDFs are an evaluation and refinement corpus, not a model-training
corpus. Paprnav is not training Textract.

The corpus is used to refine and measure:

- document rendering;
- entry segmentation;
- deterministic field extraction;
- ambiguity rejection;
- evidence alignment;
- reviewer experience;
- retries and failure recovery;
- accepted-field accuracy, latency, and cost.

## Reusable PDF Workflow Practices

### 1. Canonical Page Rendering

Render each source page consistently before structured extraction:

- fixed DPI and color mode;
- recorded width, height, and rotation;
- stable rendered-image hash;
- unchanged original PDF retained;
- rendered image retained as review evidence.

All providers and reviewers should refer to the same canonical page rendering.

### 2. Structural and Visual Inspection

Use both:

- structural inspection with `pypdf` or `pdfplumber` for page count, metadata,
  rotation, embedded text, and malformed PDF detection;
- rendered-page inspection for scans, handwriting, stamps, tables,
  side-by-side layouts, faint content, and visual completeness.

PDF text extraction alone must not be treated as proof of layout fidelity.

### 3. Native-Text-First Detection

Before purchasing OCR for a page:

1. inspect whether the PDF contains embedded text;
2. measure whether that text is meaningful and spatially aligned;
3. use it when reliable;
4. fall back to OCR for image-only or unreliable pages.

Most scanned logbooks may still require OCR, but this avoids unnecessary work
and preserves a provider-neutral path.

### 4. Page and Layout Classification

Classify pages before recognition:

- single page versus two-page spread;
- rotation or skew;
- typed, handwritten, or mixed;
- sparse versus dense;
- table or free-form layout;
- faint, degraded, stamped, crossed-out, or otherwise difficult;
- continuation-sensitive sequence.

Classification should control rendering, segmentation, provider invocation,
validation, and review expectations.

### 5. Preserve Source Page and Logical Regions

For a two-page spread, preserve the original source page while creating
separate logical regions when appropriate. Each region must retain coordinates
relative to the source rendering.

Do not lose:

- original page identity;
- left/right or stacked reading order;
- visible evidence context;
- relationships between entries that continue across regions or pages.

### 6. Page-Level Failure Isolation

Track rendering, recognition, extraction, and validation independently for
each page. One failed page should not discard successful results from the
remainder of an upload.

Record:

- page status;
- attempt number;
- error stage and code;
- retry eligibility;
- partial-result disposition;
- human-review requirement.

### 7. Dedicated Validation Stage

Provider output is a candidate, not accepted data. Validate structured fields
separately from recognition and parsing:

- dates must be plausible and source-supported;
- tach, Hobbs, and total values must not conflict;
- blank and dash values must remain null;
- zero must be explicit;
- performer, facility, certificate, and work-order patterns must be credible;
- entry count must agree with visible regions;
- AD references must be explicit rather than inferred;
- unsupported values must never become automatically verified.

### 8. Render-and-Verify Review

The review UI should verify structured values against the canonical page:

- show the relevant source page or region;
- highlight field-level evidence;
- fall back to a candidate-level region when exact geometry is unavailable;
- distinguish accepted, corrected, unresolved, and null decisions;
- preserve elapsed review time and edit count;
- require a source-supported date before verification.

### 9. Frozen Regression Pages

Keep approved pages with:

- source and rendered hashes;
- fixed ground truth;
- explicit unresolved/null decisions;
- fixed scoring rules.

Whenever rendering, segmentation, parsing, validation, or provider
configuration changes, rerun prior frozen pages to detect regressions.

## Current Paprnav Strengths

Paprnav already implements important parts of this methodology:

- provider-neutral OCR result objects;
- upload and page-count guardrails;
- asynchronous Textract Analysis;
- page-image generation;
- OCR span geometry and evidence regions;
- deterministic structured extraction;
- null preservation;
- human correction and verification;
- field-level audit evidence;
- OCR provider, latency, page-count, and cost recording;
- timed `review_outcome` evidence.

A full rewrite is not recommended.

## Current Gaps

The main gaps are:

1. Provider selection occurs before sufficient page inspection.
2. Canonical page rendering is primarily a downstream review artifact rather
   than the common extraction reference.
3. Reliable embedded PDF text is not a first-class extraction source.
4. Page difficulty and layout do not yet drive the extraction plan.
5. Two-page spread handling is heuristic rather than an explicit
   classification and segmentation stage.
6. Validation logic is distributed across parsers instead of represented as a
   clear pipeline stage.
7. Failure and retry scope is broader than an individual page/stage.
8. Cost is recorded per OCR run but not optimized or reported per accepted
   structured field.

## Recommended Provider Strategy

### Active Path

Use Textract Analysis as the active OCR adapter while improving the surrounding
provider-neutral pipeline.

### Possible Future Escalation

A stronger approved multimodal provider may later be evaluated only for
unresolved pages or cropped regions after measured Textract failure.

Any such escalation should require:

- explicit privacy and data-processing approval;
- page or region hashing and result caching;
- bounded resolution and token/output limits;
- schema-constrained output;
- provider-neutral evidence mapping;
- deterministic validation;
- cost measured per accepted field;
- a separate decision reopening provider evaluation.

### Explicitly Paused

Do not resume:

- Layout-first GLM-OCR;
- Ollama runtime work;
- local OCR GPU or CPU tuning;
- local OCR container packaging;
- challenger ECS infrastructure;
- WebAssembly or Kubernetes investigation for the paused provider.

## Corpus Use

The currently supplied source material contains:

- one 15-page aircraft logbook;
- one 29-page engine logbook;
- one single-page PDF that duplicates aircraft page 2.

There are 44 unique source pages.

The proposed allocation is:

| Partition | Pages | Purpose |
| --- | ---: | --- |
| OCR refinement | 11 | Repeated rendering, segmentation, parser, and safety refinement |
| Full ingestion validation | 22 | Upload through review and structured persistence |
| Ingestion and AD comparison holdout | 11 | Final untouched ingestion and AD-evidence evaluation |

Recommended proportional allocation:

| Logbook | Refinement | Full ingestion | Final holdout | Total |
| --- | ---: | ---: | ---: | ---: |
| Aircraft | 4 | 7 | 4 | 15 |
| Engine | 7 | 15 | 7 | 29 |
| Total | 11 | 22 | 11 | 44 |

Before fixing page assignments:

- visually classify all pages;
- keep continuity-sensitive sequences together;
- distribute typed, handwritten, side-by-side, faint, and difficult pages;
- reserve sufficient explicit-AD pages for the final holdout;
- exclude the duplicate single-page slice from the unique-page count;
- freeze assignments and hashes before further parser tuning;
- never tune against the final 11-page holdout.

## Proposed Refinement Stages

### Stage 1: Document Inspection and Canonical Rendering

- Add structural PDF inspection.
- Define and version canonical render settings.
- Persist rendered page hashes and metadata.
- Detect reliable embedded text.
- Classify rotation, spread layout, text mode, density, and difficulty.

### Stage 2: Provider-Neutral Page Extraction Plan

- Choose native text or Textract per page.
- Preserve original page identity and logical regions.
- Isolate stage failures per page.
- Persist the extraction plan and its version.

### Stage 3: Structured Validation

- Separate candidate parsing from acceptance validation.
- Generalize date and numeric conflict detection.
- Strengthen performer, facility, certificate, and work-order validation.
- Preserve unsupported fields as null.

### Stage 4: Evidence-Backed Review Metrics

- Use canonical renderings in review.
- Capture accepted, corrected, unresolved, and null decisions.
- Report median review time, mean edits, verification rate, and accepted-field
  accuracy.

### Stage 5: Incremental Early-Adopter Refinement

- Process documents only with explicit consent.
- Add only approved and reviewed pages to the frozen benchmark.
- Tie every parser change to an observed reviewed failure.
- Rerun prior frozen pages after every extraction or validation change.

## Cost Considerations

Low-cost improvements:

- PDF validation;
- page counting and metadata inspection;
- canonical rendering;
- embedded text detection;
- page classification;
- deterministic validation;
- cached results keyed by source and configuration hashes.

Potentially expensive work:

- OCR on every page;
- repeated OCR after unchanged input;
- high-resolution multimodal processing;
- whole-page multimodal escalation when only one region is unresolved.

Control cost by:

- invoking OCR only when required;
- escalating only unresolved regions;
- caching by page/region and configuration hash;
- bounding resolution and page count;
- avoiding recognition after human verification;
- measuring cost per accepted field and reviewed page.

## Decisions Required From the Main Thread

1. Approve canonical page rendering as the authoritative review and evidence
   reference.
2. Choose initial render settings and versioning rules.
3. Define thresholds for reliable embedded PDF text.
4. Approve the page-classification schema.
5. Decide how continuity-sensitive spreads and sequences are grouped.
6. Freeze the 11/22/11 page assignments after visual inventory.
7. Scope the first implementation stage without reopening paused OCR-provider
   work.

## Suggested Main-Chat Prompt

> Review `.ai/PDF_EXTRACTION_METHODOLOGY_HANDOFF.md` and the current Paprnav
> implementation. Propose a scoped, evidence-driven refinement loop beginning
> with PDF inspection, canonical rendering, page classification, and
> provider-neutral validation. Keep Textract as the active OCR adapter, preserve
> the 11/22/11 corpus split, and do not resume Layout-first GLM-OCR or Ollama
> work.
