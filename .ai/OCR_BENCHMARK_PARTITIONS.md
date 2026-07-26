# OCR Benchmark Partitions

Date: 2026-07-25

This inventory was produced by visually rendering every page. No OCR was run
to classify or assign the reserved pages. The assignments are frozen in
`.ai/OCR_BENCHMARK_PARTITIONS.json`.

## Partition Summary

| Partition | Aircraft pages | Engine pages | Total | Permitted use |
| --- | --- | --- | ---: | --- |
| OCR refinement | 2-5 | 3-9 | 11 | Repeated OCR/parser refinement |
| Full ingestion | 6-12 | 10-24 | 22 | End-to-end upload, OCR, review, persistence, and operational validation |
| Ingestion + AD holdout | 1, 13-15 | 1-2, 25-29 | 11 | Final ingestion and AD comparison only |

The separate one-page PDF renders identically to aircraft page 2. It is a
convenience slice in the OCR-refinement partition and is not a 45th unique
page.

## Visual Classification

### Aircraft logbook

| Pages | Visual characteristics | Continuity |
| --- | --- | --- |
| 1 | Cover/identity and metadata; sparse structured fields | Standalone front matter |
| 2 | Side-by-side typed maintenance plus mixed handwritten/form content | Existing refinement benchmark |
| 3 | Rotated FAA release certificate; dense form and small print | Attachment associated with the early seat-stop work |
| 4-5 | Side-by-side typed maintenance entries, signatures, time fields, and AD text | Contiguous typed-maintenance sequence |
| 6 | Sparse left entry plus dense typed/right entry and handwriting | Start of later chronological sequence |
| 7 | Handwritten left entry and typed right entry | Same chronological sequence |
| 8-10 | Mixed sparse handwriting and typed annual/maintenance entries | Same chronological sequence |
| 11 | Dense inserted form/label plus sparse logbook entry | Attachment transition |
| 12 | Typed maintenance entry with a blank facing page | End of the integration sequence |
| 13 | Handwritten repair-station/form entry plus dense typed checklist | Start of held-out attachment sequence |
| 14-15 | Dense typed checklists and mixed typed maintenance entries | Contiguous held-out sequence with AD potential |

### Engine logbook

| Pages | Visual characteristics | Continuity |
| --- | --- | --- |
| 1-2 | Cover/identity and sparse opening entry | Front matter |
| 3 | Dense handwritten side-by-side entries | Existing refinement benchmark |
| 4 | Rotated serviceable-component tag | Attachment within historical sequence |
| 5-8 | Dense handwritten side-by-side maintenance entries, stamps, and signatures | Contiguous historical sequence |
| 9 | Heavily crossed-out/overwritten handwritten page | Same historical sequence; high difficulty |
| 10 | Dense mixed handwriting and overwritten content | Transition out of refinement sequence |
| 11 | Maintenance-release attachment with sparse handwriting | Attachment within the chronological sequence |
| 12 | Dense handwritten side-by-side maintenance entries | Entry page following the release |
| 13-14 | Handwritten entries transitioning into typed maintenance | Same chronological sequence |
| 15-17 | Mixed typed and handwritten maintenance entries | Transition sequence |
| 18-24 | Predominantly typed annual/maintenance entries with signatures, sparse fields, and blank areas | Contiguous modern-maintenance sequence |
| 25-26 | Dense typed maintenance/checklist entries with AD-comparison potential | Start of final holdout |
| 27 | Logo/identity insert with a mostly blank facing page | Held-out document-type/blank-page behavior |
| 28 | Handwritten entry plus reference/index page | Held-out mixed-layout behavior |
| 29 | Typed parts/reference list plus blank ruled page | Held-out non-entry/reference behavior |

## Selection Rationale

- The 11-page refinement set contains the existing three benchmark pages,
  typed entries, dense handwriting, side-by-side layouts, a rotated attachment,
  stamps, and overwritten content.
- The 22-page integration set preserves contiguous chronological runs and
  exercises transitions from handwriting to typed maintenance, inserted
  releases, blank areas, and ordinary modern entries.
- The 11-page holdout contains unseen cover/identity pages, dense checklists,
  AD-rich candidates, blank pages, attachments, handwriting, and reference
  lists. It must not influence parser changes before final scoring.

## Paprnav Enforcement Rules

1. Resolve a benchmark page by source PDF SHA-256 plus one-based page number.
2. Reject a run whose requested page is absent from the selected partition.
3. Never count `N3671L_page2.pdf` separately from aircraft page 2.
4. Record partition name and manifest version in OCR-run metadata.
5. OCR-refinement results may drive parser changes.
6. Full-ingestion failures may drive workflow fixes, but moving a page into the
   refinement set requires a new manifest version and a replacement page.
7. Holdout results may not drive changes until the final ingestion and AD
   comparison is recorded.
8. Keep layout-first GLM-OCR and Ollama excluded from every partition.
