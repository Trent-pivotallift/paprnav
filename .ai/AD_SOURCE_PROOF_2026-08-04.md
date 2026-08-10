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

## Operational persistence follow-up - 2026-08-06

The retained proof was materialized into the local Paprnav PostgreSQL schema
after a recoverable pre-migration backup. The database is at Alembic revision
`20260806_0019`.

The source snapshot retains the complete Access inventory of 20,390 normalized
rows and the nine separately inventoried rows without usable AD identifiers.
Operational materialization is scoped to the aircraft/component identities
requested by onboarding, rather than eagerly creating every FAA target:

- selected DRS source rows: 51;
- Cessna 172G model index: 40 (30 Aircraft and 10 Appliance);
- Continental O-300-D Engine index: 11;
- DRS publications persisted: 51;
- applicability targets persisted from the non-invented DRS axes: 4,663;
- AD-target applicability rows persisted: 8,123.

N3671L is configured locally as Cessna 172G airframe serial `17253840` with a
Continental Motors O-300-D engine serial `33608-D-5-D`. Its reusable coverage
subscriptions resolve to:

- airframe: 28 current directives and 30 retained DRS publications;
- engine: 7 current directives and 11 retained DRS publications;
- appliance: zero automatic subscriptions.

The two historical 172G airframe rows and four historical O-300-D engine rows
remain retained as history/evidence rather than being counted as current
coverage. Manufacturer-name variants in DRS are included only after a
same-product, same-model make anchor is established; this captures Cessna /
Textron and Continental legacy/successor names without collapsing Appliance
targets into the airframe.

The provider-neutral publication proof was persisted as a separate
content-hashed source snapshot:

- proof snapshot SHA-256:
  `cabedd2e89fe41c8eacdc4c5dd090a280c59ea78b16bea45fd28034add219cb7`;
- exact Federal Register links: 37 publications across 16 directives;
- GovInfo issue links: 27 publications across 27 directives;
- historical publication adjudication issues: 24;
- missing target directives: 0.

Federal Register/GovInfo rows augment the DRS-derived directive and
applicability catalog; they do not replace it. The 2026-08-09 retained-artifact
closure below supersedes the former metadata-only limitation.

An identical scoped ZIP replay and identical publication-proof replay left all
logical counts unchanged: one DRS snapshot, 51 DRS publications, 4,663
targets, 8,123 applicability rows, two coverage sets, two aircraft
subscriptions, and five non-billable cost-ledger rows. Full repository-context
backend regression: **137 passed out of 137**.

Operational persistence verification: **20 passed out of 20**. The loop found
and corrected three defects before closure: insufficient DRS subtype width,
PostgreSQL JSON `DISTINCT` usage, and manufacturer-variant coverage under-link.

## Remote artifact persistence closure - 2026-08-09

The same 51-directive Cessna 172G/O-300-D target set was reconciled again and
the remote evidence was retained before database materialization:

- 51 Federal Register search-response payloads;
- 37 exact Federal Register document payload references;
- 37 exact Federal Register document-PDF references representing 34 unique
  PDFs because three source documents were reused;
- 27 GovInfo package-summary payloads;
- 27 complete GovInfo Federal Register issue PDFs;
- 176 unique content-addressed `ad_source_documents` totaling approximately
  585 MiB in durable local storage;
- 64 `ad_publications.source_document_id` links, each pointing to the retained
  PDF used as primary publication evidence;
- 24 historical `needs_adjudication` cases preserved unchanged.

The capture manifest SHA-256 is
`8f8fb6ce17127113fcaf07b7958ed5eb280a65ea04e01a329d8a494a25b697f4`
and reports **7 passed out of 7**. All 61 unique PDFs passed Poppler structural
inspection; representative individual-rule and complete-issue pages rendered
legibly. Every persisted local object matched its declared SHA-256 and
content-addressed path. No GovInfo API-key query parameter remains in retained
provenance.

The identical database replay produced the same operation counts on both
runs: 51 records, 37 Federal Register publications, 27 GovInfo publications,
179 artifact references, 64 publication/PDF links, zero missing directives,
and 24 adjudication cases. Unique table counts remained 176 source documents,
64 linked publications, and 181 cost-ledger rows (the five earlier rows plus
one non-billable physical-storage row per unique source document).

Verification after closure:

- retained-source persistence regression: **20 passed out of 20**;
- full backend regression: **141 passed out of 141**;
- frozen logbook partitions remained unopened.

One GovInfo 502 response exposed the configured API key in transient local
command output before sanitized exception handling was added. The key was not
written into retained artifacts, but it must be rotated as a precaution before
the AWS implementation/deployment stage. Rotation was intentionally postponed
during the local proof and recurrence implementation.

## Recurrence Readiness Follow-up — 2026-08-09

The source/applicability catalog is relationally complete for the proven
N3671L scope, but catalog completeness is separate from approved compliance
meaning. The current database contains 45 current 172G/O-300-D directives; 23
have retained full-text publication evidence and 22 remain valid
historical-source adjudication cases. None of the 45 yet has an approved
compliance extraction, so the normalized recurrence tables remain empty after
migration rather than inferring intervals from DRS titles or indexes.

Alembic `20260809_0020` adds normalized requirements, triggers, verified
compliance events, time-state observations, and replayable due states. The
next local gate is evidence-backed extraction and platform review of the 23
retained publications. AWS deployment follows that gate; it does not replace
it.
