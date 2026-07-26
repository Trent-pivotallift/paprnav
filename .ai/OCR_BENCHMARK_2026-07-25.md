# OCR Benchmark - 2026-07-25

## Scope

Account: `paprnav-internal-test`

Aircraft: `N3671L`

The benchmark used two derived PDFs so both providers received identical bytes:

| Slice | Original pages | SHA-256 |
| --- | --- | --- |
| Airframe | 2 and 4 | `597654a1be27063a00f00c128a1af344ee3f9d147e3c2192f9522e092020b80c` |
| Engine | 3 | `afa658ae09158d9a6dc9b92fe790efc8910c480724623e70d457156572b0cf2b` |

The source PDFs and derived artifacts remain under the ignored
`backend/.data/ocr-feasibility` directory.

## Ground Truth And Scoring

The airframe ground truth was manually transcribed from the source scan before
scoring the normalized provider output. Dates and numeric fields require an
exact normalized match. A field that is present but differs from the
transcription is incorrect, even when it remains routed to review.

| Entry | Date | Tach | Total time | Expected AD citations |
| --- | --- | ---: | ---: | --- |
| RS Aircraft Service annual | `2012-12-17` | `1276.8` | `5405.5` | `2011-10-09` |
| Jones Avionics | `2013-04-13` | null | null | none |
| RS Aircraft Service annual | `2014-02-11` | `1289.83` | `5418.53` | `2011-10-09`, `1976-07-12` |
| RS Aircraft Service seat stop | `2014-12-10` | `1293.2` | null | `2011-10-09` |

For the handwritten engine page, the two visible regions are the separation
ground truth. The scan does not support an exact date, time, performer, or
credential value confidently enough for automatic promotion. Those structured
fields must therefore remain null until a reviewer supplies a
source-supported value. In particular, `4954.0` is not an accepted total-time
value.

## Runs

| Slice | Provider | Job | Pages | Duration | Estimated provider or compute cost |
| --- | --- | --- | ---: | ---: | ---: |
| Airframe | Textract Analysis | `job_1e1c3876f59e4e158b77a1729d7d61c9` | 2 | 10.106 s | $0.0370 |
| Engine | Textract Analysis | `job_93a4f1aeea534ee7a8b4256c1c95fa66` | 1 | 5.750 s | $0.0185 |
| Airframe | Layout-first GLM-OCR | `job_d88adb2f9b7a452f80dcea8578677bd0` | 2 | 29.702 s | $0.001923 raw-duration projection |
| Engine | Layout-first GLM-OCR | `job_61cf70113656485c8c781660d0fc2d4f` | 1 | 16.352 s | $0.001059 raw-duration projection |

Textract cost used a conservative configured rate of `$0.0185/page` for
Tables plus Signatures; Layout is free when used with Tables. Total estimated
Textract cost was `$0.0555`.

The local projection used a planning rate of `$0.2330496/hour`, equivalent to
a 4-vCPU, 16-GB Linux/x86 Fargate task in `us-east-1`. Fargate has a one-minute
minimum. If the two local runs were separate tasks, the minimum compute
projection is about `$0.00777`, not the raw-duration `$0.002982`. Image pull,
startup, logs, storage, and data transfer are not included.

## Typed Airframe Results

Ground truth contains four entries across the two pages. The second entry has
no tach or total time.

| Criterion | Textract Analysis | Layout-first GLM-OCR |
| --- | --- | --- |
| Entry separation | 4 of 4 | 4 of 4 |
| Entry dates | 3 of 4; Jones date remains null | 3 of 4; Jones date was misread as `2013-12-05` |
| Recorded tach values | 3 of 3 after hyphen parser fix | 3 of 3 |
| Recorded total-time values | 2 of 2 | 2 of 2 |
| Null tach/total preservation | Correct for Jones entry | Correct for Jones entry |
| Expected AD citations | 4 of 4 after chained-revision fix | 4 of 4 after chained-revision fix |
| Performer and credential fields | 0 structured | 0 structured |
| Evidence | Granular line boxes | Coarse entry/region boxes |
| Recognition confidence | Available per Textract span | Unavailable and stored as null |

The provider-neutral parser fixes were:

- choose the earliest date in reading order instead of preferring any later
  ISO date, which had mistaken `AD 2011-10-09` for an entry date;
- accept the common `Tach - 1289.83` separator;
- recognize a chained legacy AD revision such as `and 76-07-12R1` and
  normalize it to `1976-07-12`.

## Handwritten Engine Result

Both providers separated the two side-by-side regions, but neither produced a
review-ready structured result. Dates remained null and performer credentials
were not structured. Textract kept uncertain time fields null. The local model
produced `4954.0` as a total-time candidate, which is not supported confidently
by the scan and must not be promoted automatically.

This page is the current quality gate. Coherent prose alone is not sufficient;
unsupported numeric fields are higher risk than nulls.

## Evidence And Review

The review UI now exposes date, tach, Hobbs, total, performer/facility,
certificate/work-order, and full extracted text as candidate-level edits.
Blank time values persist as database null, while zero must be entered
explicitly. `Save for Review` and `Verify Entry` are distinct actions, and a
source-supported date is required for verification.

Derived page previews now follow the source upload storage backend. The six
benchmark previews were promoted to tagged S3 objects. Browser acceptance
confirmed page 1 at `2708 x 733` and page 2 at `2700 x 770`, with evidence
selection switching the underlay and highlight context.

## Decision

Textract Analysis remains the primary OCR provider.

At this initial checkpoint, Layout-first GLM-OCR remained a challenger. It
improved coherent region recognition, but it misread the handwritten Jones date
as `2013-12-05`, had no calibrated recognition confidence, and produced an
unsafe numeric candidate on the engine page. The post-refinement decision below
supersedes this checkpoint and pauses all work on the challenger.

## Promotion Thresholds

Evaluate a challenger on at least 30 approved pages spanning typed,
handwritten, multi-entry, side-by-side, and degraded scans. Promote only when
all of these gates pass against the same source bytes and frozen ground truth:

1. Safety: zero unsupported date or numeric fields are automatically verified;
   ambiguous conflicts resolve to null.
2. Quality: entry separation recall is at least 99%, and accepted date, tach,
   Hobbs, total-time, performer/facility, and credential/work-order precision
   is at least 99%.
3. Reviewer effort: median elapsed review time and mean edited-field count are
   each at least 20% lower than Textract, with no page category regressing by
   more than 5%.
4. Evidence: every accepted structured field has drawable source evidence, or
   an explicit candidate-region fallback, and recognition confidence is never
   fabricated.
5. Operations: p95 warm processing latency is no worse than 2x Textract, the
   projected per-page cost is no higher than Textract after minimum task
   billing and startup overhead, and privacy/audit requirements remain met.

## Refinement Loop Completion

Completed in the working tree:

- added timed `review_outcome` evidence with source-provider attribution and
  accepted/corrected/null decisions for every structured field;
- added deterministic extraction for typed A&P signatures, FAA repair-station
  identifiers, and work-order references;
- added a bounded 1% region-crop context margin that cannot cross page edges;
- added a numeric ambiguity guard that rejects the observed `4454.2` versus
  `4954` one-digit conflict to null;
- defined the promotion gates above.

The existing benchmark jobs predate timed review instrumentation. Do not invent
elapsed-time results for them; reopen and save/verify their candidates through
the review UI to create the first comparable reviewer-effort observations.

## Post-Refinement Comparison

The post-refinement comparison reused the same PDFs and hashes listed in
Scope. Textract recognition was not called again because its stored spans were
unchanged; those spans were recomputed through the refined deterministic
extractor. Layout-first recognition was rerun on both PDFs with the bounded 1%
crop margin, a 2048-pixel maximum crop dimension, and an Ollama context of
16,384 tokens.

### Airframe

| Criterion | Textract Analysis | Layout-first GLM-OCR |
| --- | --- | --- |
| Entry separation | 4 of 4 | 3 of 4 |
| Entry dates | 3 of 4 | 2 of 4 |
| Recorded tach values | 3 of 3 | 2 of 3 |
| Recorded total-time values | 2 of 2 | 1 of 2 |
| Expected AD citations | 4 of 4 | 3 of 4 |
| Performer/facility | 3 of 4 | 1 of 4 |
| Credential/work order | 3 of 4 | 1 of 4 |
| Duration | 10.106 s stored run | 107.227 s rerun |

Layout-first failed to recover the first RS Aircraft Service entry on original
page 2. It no longer emitted the incorrect Jones date; that field remained
null. It did structure Jones Avionics, its FAA repair-station certificate, and
work order, but this improvement does not offset the missing entry.

### Handwritten Engine

| Criterion | Textract Analysis | Layout-first GLM-OCR |
| --- | --- | --- |
| Region separation | 2 of 2 | 2 of 2 |
| Review-ready structured entries | 0 of 2 | 0 of 2 |
| Dates promoted | 0 | 0 |
| Unsupported time values promoted | 0 | 0 |
| Duration | 5.750 s stored run | 17.612 s rerun |

The ambiguity guard detected the standalone `4454.2` versus labeled `4954`
conflict and kept total time null. This closes the specific unsafe numeric
failure from the initial run.

The two Layout-first reruns projected `$0.008081` from raw duration. With the
one-minute Fargate minimum applied separately, the projection is approximately
`$0.010825`: `$0.006941` for the 107.227-second airframe run plus `$0.003884`
for the engine run.

The first airframe attempts also exposed an Ollama/GLM-OCR runtime defect. The
default 4,096-token context crashed while shifting the vision model KV cache.
Pinning `num_ctx=16384` prevented the crash, but the airframe table recognition
used the full 8,192-token output allowance and materially increased latency.

### Post-Refinement Decision

Textract Analysis remains primary. Layout-first passes the specific engine-page
numeric safety gate but fails the airframe completeness, quality, and latency
gates. All layout-first GLM-OCR and Ollama work is paused. Keep the code only as
historical benchmark evidence; do not run, harden, package, deploy, or expand
the challenger without a new explicit decision.

Verification after the post-refinement changes:

- backend tests: 81 of 81 passed;
- frontend production builds: 1 of 1 passed;
- repository diff whitespace validation: passed.

## Active Next Steps

1. Capture real reviewer time, edits, accepted fields, and null decisions for
   the stored Textract candidates.
2. Add a reviewer-effort report over `review_outcome` evidence.
3. Improve the remaining deterministic Textract performer/facility and
   credential/work-order misses.
4. Generalize provider-neutral conflicting date/time rejection.
5. Add safe retry, leasing, and idempotent partial-write handling to the active
   OCR worker path.
6. Use the frozen 11-page OCR-refinement partition next. Keep the 22-page
   full-ingestion partition and 11-page ingestion/AD holdout untouched until
   their respective phases. Grow later benchmark versions incrementally from
   explicitly consented early-adopter aircraft and reviewed pages.
7. When early-adopter PDFs produce `pdf_native_text` routes, review every such
   page against its canonical render under
   `.ai/EARLY_ADOPTER_NATIVE_TEXT_REVIEW.md`. Keep the controlled-fixture
   activation distinct from the real-document production-proof result, and
   report `X passed out of Y`, bypass/Textract counts, information loss,
   evidence coverage, null preservation, edits, and reviewer time.

Excluded from this loop: Layout-first GLM-OCR, Ollama, local OCR containers,
ECS packaging for the challenger, GPU/CPU runtime tuning, WebAssembly, and
additional challenger benchmarks.
