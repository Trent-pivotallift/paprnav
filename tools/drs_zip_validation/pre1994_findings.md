# Pre-1994 DRS Historical Validation

Generated at: 2026-06-21T16:28:25.042757+00:00

## Bulk Evidence

- Source ZIP: `ADFinalRulesEmergencyADs_05312026.zip`
- Access database: `ADFinalRulesEmergencyADs_05312026.accdb`
- Normalized AD identifiers: 19731
- Pre-1994 identifiers: 6792
- Earliest pre-1994 identifier: `1941-47-01`
- Latest pre-1994 identifier: `1993-25-17`
- Sample method: decade-stratified sample from the extracted DRS bulk identifier set

## Verdict

- Confidence level: **conditional**
- Coverage claim: Pre-1994 ADs are present in the DRS bulk corpus; complete historical coverage is not proven.
- Product copy requirement: Pre-1994 ADs are included when present in the current DRS bulk data; complete historical coverage has not been proven.
- Local ZIP set cross-check available: True

## Sample Status Counts

- `historical_source_unavailable`: 4
- `matched`: 1
- `snapshot_unparseable`: 1

## Samples

### pre1994-id-1941-47-01

- AD number: `1941-47-01`
- Status: `historical_source_unavailable`
- Bulk identifier present: `True`
- Target query: `{'componentType': 'unknown', 'make': None, 'model': None}`
- DRS Web UI snapshot: `{'snapshotType': 'not_captured', 'comparison': 'identifier is present in DRS bulk extraction but no rendered DRS detail snapshot is committed'}`
- Historical sources: `[{'sourceId': 'faa-current-ad-page', 'url': 'https://www.faa.gov/regulations_policies/airworthiness_directives', 'status': 'current FAA page links AD access to DRS but does not expose a static 1940s index'}]`
- Notes: Earliest extracted pre-1994 sample; keep as presence-only until an independent historical index is captured.

### pre1994-id-1965-01-02

- AD number: `1965-01-02`
- Status: `historical_source_unavailable`
- Bulk identifier present: `True`
- Target query: `{'componentType': 'unknown', 'make': None, 'model': None}`
- DRS Web UI snapshot: `{'snapshotType': 'not_captured', 'comparison': 'identifier is present in DRS bulk extraction but no rendered DRS detail snapshot is committed'}`
- Historical sources: `[{'sourceId': 'faa-current-ad-page', 'url': 'https://www.faa.gov/regulations_policies/airworthiness_directives', 'status': 'current FAA page links AD access to DRS but does not expose a static 1965 index'}]`
- Notes: Decade-stratified sample; unresolved until historical index or rendered DRS detail is captured.

### pre1994-engine-lycoming-o320

- AD number: `1977-01-08`
- Status: `historical_source_unavailable`
- Bulk identifier present: `True`
- Target query: `{'componentType': 'engine', 'make': 'Lycoming', 'model': 'O-320'}`
- DRS Web UI snapshot: `{'snapshotType': 'not_captured', 'comparison': 'no committed DRS Web UI result snapshot for this engine sample'}`
- Historical sources: `[{'sourceId': 'faa-current-ad-page', 'url': 'https://www.faa.gov/regulations_policies/airworthiness_directives', 'status': 'does_not_provide_static_pre1994_engine_index'}]`
- Notes: High-value GA engine sample; requires a rendered DRS result-list snapshot or independent historical FAA index.

### pre1994-target-pa28-180

- AD number: `1992-26-01`
- Status: `snapshot_unparseable`
- Bulk identifier present: `True`
- Target query: `{'componentType': 'airframe', 'make': 'Piper Aircraft Inc.', 'model': 'PA-28-180'}`
- DRS Web UI snapshot: `{'snapshotType': 'drs_app_shell_html', 'capturedAt': '2026-06-21', 'sourceUrl': 'https://drs.faa.gov/browse/ADFRAWD/doctypeDetails?Status=all&Make=Piper%20Aircraft%20Inc.&Model=PA-28-180', 'comparison': 'app shell reachable, but no parseable result rows in static HTTP snapshot'}`
- Historical sources: `[{'sourceId': 'faa-current-ad-page', 'url': 'https://www.faa.gov/regulations_policies/airworthiness_directives', 'status': 'does_not_provide_static_pre1994_target_index'}]`
- Notes: High-value GA airframe target sample; DRS Web UI capture remains necessary.

### pre1994-target-c172

- AD number: `1993-01-01`
- Status: `matched`
- Bulk identifier present: `True`
- Target query: `{'componentType': 'airframe', 'make': 'Cessna', 'model': '172R'}`
- DRS Web UI snapshot: `{'snapshotType': 'normalized_manual_result_snapshot', 'capturedAt': '2026-06-21', 'resultAdNumbers': ['1993-01-01'], 'comparison': 'bulk identifier present in retained DRS target snapshot'}`
- Historical sources: `[{'sourceId': 'faa-current-ad-page', 'url': 'https://www.faa.gov/regulations_policies/airworthiness_directives', 'status': 'supports_drs_as_current_ad_access_path'}]`
- Notes: Positive control sample; proves sample presence only.

### pre1994-propeller-mccauley

- AD number: `1989-02-08`
- Status: `historical_source_unavailable`
- Bulk identifier present: `True`
- Target query: `{'componentType': 'propeller', 'make': 'McCauley', 'model': None}`
- DRS Web UI snapshot: `{'snapshotType': 'not_captured', 'comparison': 'no committed DRS Web UI result snapshot for this propeller sample'}`
- Historical sources: `[{'sourceId': 'faa-current-ad-page', 'url': 'https://www.faa.gov/regulations_policies/airworthiness_directives', 'status': 'does_not_provide_static_pre1994_propeller_index'}]`
- Notes: High-value propeller sample; unresolved until target-specific snapshot is captured.

## Required Follow-Up

- Capture rendered DRS result-list snapshots for unresolved target samples.
- Find or digitize independent historical FAA/index sources where available.
- Keep pre-1994 coverage claims conservative until ambiguous samples are resolved.
