# DRS Bulk ZIP Validation Findings

Date run: 2026-06-20T20:24:40.745113+00:00
Discovered bulk ZIP URL: `playwright-download:ADFinalRulesEmergencyADs_05312026.zip`

## ZIP Contents Inventory

- Total file count: 1
- File type distribution: `{".accdb": 1}`
- Manifest/index files: none found
- First 10 filenames:
  - `ADFinalRulesEmergencyADs_05312026.accdb`
- Last 10 filenames:
  - `ADFinalRulesEmergencyADs_05312026.accdb`

## AD Extraction

- Filename/content convention used: `accdb_utf16_text`
- If method is `pdf_first_page`, filenames did not provide enough AD numbers and no parseable manifest was found.

## Comparison

- Window: 2024-01-01 to 2024-12-31
- FR set size: 273
- Full ZIP AD set size: 19731
- Full ZIP intersection size: 273
- Full ZIP source coverage: 100.00%
- ZIP set size using AD-year window surrogate: 271
- AD-year surrogate intersection size: 250
- AD-year surrogate coverage: 91.58%
- Verdict: **PASS**
- Recommended action: Proceed with bulk-ZIP-primary architecture.
- Note: The current one-shot script extracts AD identifiers from the DRS Access database but does not parse row-level publication dates; the AD-year window is a conservative surrogate, not a source-coverage failure.

## Detailed Gap Report: ADs In FR But Not Full ZIP

No FR-only gaps found.

## AD-Year Window Artifacts

These FR ADs are present in the full ZIP but fall outside the AD-year surrogate window.
- 2023-12-09: published 2024-07-18, document 2024-15827
- 2023-13-07: published 2024-04-18, document 2024-08153
- 2023-24-07: published 2024-01-02, document 2023-28799
- 2023-24-08: published 2024-01-02, document 2023-28800
- 2023-25-01: published 2024-01-02, document 2023-28801
- 2023-25-04: published 2024-01-02, document 2023-28802
- 2023-25-05: published 2024-01-03, document 2023-28851
- 2023-25-06: published 2024-01-03, document 2023-28852
- 2023-25-07: published 2024-01-26, document R2-2023-28853
- 2023-25-09: published 2024-01-03, document 2023-28854
- 2023-25-10: published 2024-01-03, document 2023-28855
- 2023-25-11: published 2024-01-03, document 2023-28846
- 2023-25-12: published 2024-01-03, document 2023-28847
- 2023-25-13: published 2024-01-18, document R1-2023-28849
- 2023-25-15: published 2024-01-03, document 2023-28848
- 2023-25-16: published 2024-01-23, document 2024-01169
- 2023-26-01: published 2024-01-03, document 2023-28850
- 2023-26-02: published 2024-01-23, document 2024-01170
- 2023-26-03: published 2024-01-03, document 2023-28877
- 2023-26-04: published 2024-01-03, document 2023-28861

## Sample ADs In ZIP But Not FR

- 2024-25-01
- 2024-25-02
- 2024-25-03
- 2024-25-04
- 2024-25-05
- 2024-25-07
- 2024-25-08
- 2024-25-09
- 2024-25-10
- 2024-25-11
- 2024-25-12
- 2024-25-51
- 2024-26-01
- 2024-26-02
- 2024-26-03
- 2024-26-04
- 2024-26-05
- 2024-26-06
- 2024-26-07
- 2024-26-08

## Recommended Next Steps

- Follow the verdict action: Proceed with bulk-ZIP-primary architecture.
- For production date-window comparisons, parse DRS Access rows instead of using AD-year filtering.
- Review `data/fr_set.json`, `data/zip_set.json`, and cached FR responses for audit.
- If gaps look like extraction errors, inspect the corresponding PDFs or FR XML before changing architecture.
- If gaps are real, update the ingestion spec before implementing production collection.
