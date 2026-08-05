# AD Source Proof - 2026-08-04

## Outcome

The local Cessna 172G and Continental O-300-D AD source proving loop is
complete under decision D025's conservative completion rule: every retained
DRS target row is catalogued, every source difference is classified, and
unresolved publication evidence remains `needs_adjudication`. No compliance or
regulatory completeness attestation is implied.

The frozen 22-page full-ingestion partition and 11-page ingestion/AD holdout
were not opened.

## Retained controls

- DRS bulk ZIP SHA-256:
  `9ef00fba796c6073e84e03b1f0f8777a212efc94846c4c7e0c76b9caeac3fc7a`
- 172G result page SHA-256:
  `040f8cff134b6158673df194b19b052c3925f73adb36db5e6336b0adb7ab11a8`
- O-300-D result page SHA-256:
  `2aa89fa5cb7f235de6ed7125b6a9336955650790693f5a369c6667d5787eada2`

The two Excel result lists contain 10 rows each. They are page-level manual
controls, not completeness authorities. The Access database contains the full
target sets.

## DRS reconciliation

- Access table rows exported: 20,399
- Rows with normalized AD identifiers: 20,390
- Rows without usable AD identifiers: 9, all explicitly inventoried
- Cessna 172G Historical/Current target rows: 40
  - Aircraft: 30
  - Appliance: 10
- Continental O-300-D Historical/Current Engine rows: 11
- Manual-only identifiers: 0 for both controls
- Bulk-only identifiers:
  - 172G: 30, demonstrating the Excel export captured one page
  - O-300-D: 1 (`2000-11-51`), demonstrating the same pagination behavior
- Verification: **11 passed out of 11**
- Repeat manifest SHA-256:
  `12ff1e122c0644e5209f2b9ae8cc36dec357cc1275192b710d1b717101cbc366`
  on both runs

## Federal Register and GovInfo reconciliation

- Unique target directives: 51
- Exact GovInfo issue packages retained: 27
- Exact modern Federal Register API matches: 16
- Modern API exact-match gaps: 35, classified rather than discarded
- Target records without a safe publication date: 24
- Unresolved exact GovInfo packages for dated records: 0
- Undated historical records remain `needs_adjudication`; effective dates were
  not substituted for publication dates
- Provider-neutral retained JSON: 161,316 bytes
- Textract pages: 0
- Estimated external cost: $0
- Verification: **5 passed out of 5**
- Repeat manifest SHA-256:
  `cabedd2e89fe41c8eacdc4c5dd090a280c59ea78b16bea45fd28034add219cb7`
  on both runs

## Implementation changes

- The backend image now installs `mdbtools` and Poppler.
- The DRS importer maps the actual FAA Access column names.
- Multi-make/multi-model rows no longer create an invented Cartesian product.
- AD revision identity is retained while canonical matching remains stable.
- Provider-neutral source documents are content-addressed and idempotent.
- GovInfo pagination and exact date-routed package retention are implemented.
- A deterministic DRS/manual proof runner and publication reconciliation runner
  produce replayable manifests.

## Verification

- Focused AD/source tests: **13 passed out of 13**
- Publication/source tests: **9 passed out of 9**
- Backend regression in the production-equivalent image: **131 passed out of 131**
- Frozen partition invariant in repository context: **1 passed out of 1**
- Previously failing Poppler-dependent regressions: **5 passed out of 5**
- Alembic migration added: `20260804_0018`

## Remaining adjudication and next loop

The 24 undated historical rows need evidence-backed Federal Register issue
location. A later historical-publication loop may use bounded issue discovery,
retain full original issues, inspect/native-text route pages first, and use
Textract only for relevant image-only or uncertain pages. It must not infer
publication dates from effective dates. Propeller and installed-appliance
coverage remain incomplete until their identities are verified from aircraft
records.
