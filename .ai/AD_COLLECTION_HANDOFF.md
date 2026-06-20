# AD Collection Handoff Findings

Last updated: 2026-06-19

This note captures the current AD ingestion/collection findings for a new chat or `/goal` run. It is intentionally focused on the unresolved collection problem, not the already-implemented local AD review and matching workflow.

## Current Implementation Baseline

- Local Federal Register AD discovery is implemented and persists discovery records, source URLs, raw API snapshots, classifications, and hashes.
- Local deterministic AD extraction, AD extraction review, first-pass AD-to-logbook matching, HITL adjudication, and compliance worklist are implemented.
- The current Federal Register discovery worker now supports a configurable search term:

```bash
cd backend
docker compose exec -T api python -m app.workers.ad_discovery \
  --term "Airworthiness Directives PA-28-180" \
  --per-page 2
```

- The checkpoint commit for parameterized discovery is `1c846f0 Add parameterized Federal Register AD discovery`.

## Evidence From PA-28-180 Check

The app produced two Federal Register AD candidates using this query:

```text
https://www.federalregister.gov/api/v1/documents.json?conditions%5Bagencies%5D%5B%5D=federal-aviation-administration&conditions%5Btype%5D%5B%5D=RULE&conditions%5Bterm%5D=Airworthiness+Directives+PA-28-180&order=newest&page=1&per_page=2
```

Worker output:

```text
ad_discovery term='Airworthiness Directives PA-28-180' seen=2 candidates=2 rejected=0
```

Persisted results observed locally:

| Federal Register document | AD number | Title | Publication date | Classification |
| --- | --- | --- | --- | --- |
| `2021-00044` | `2020-26-16` | Airworthiness Directives; Piper Aircraft, Inc. Airplanes | 2021-01-15 | `ad_candidate` |
| `2020-25690` | `2020-24-05` | Airworthiness Directives; Piper Aircraft, Inc. Airplanes | 2020-11-23 | `ad_candidate` |

This proves the current app can pull Federal Register publications that match a PA-28-180-ish search term. It does not prove the app can answer "all ADs applicable to a Piper PA-28-180."

## Important Finding

Federal Register and FAA DRS answer different questions:

- Federal Register search returns matching publications, ordered by publication metadata and text search relevance.
- FAA DRS browse/search answers applicability-style questions such as make/model/status filters.

The FAA DRS URL used for comparison was:

```text
https://drs.faa.gov/browse/ADFRAWD/doctypeDetails?Status=all&Make=Piper%20Aircraft%20Inc.&Model=PA-28-180
```

The DRS result set differed from the Federal Register query. That difference is expected because DRS has aircraft applicability indexing that Federal Register text search does not expose directly.

## Current DRS Assessment

- FAA DRS does not appear to provide a documented public API for this browse query.
- A quick page-source inspection showed a JavaScript/Angular application shell rather than direct result data in static HTML.
- Bundle inspection suggested internal API usage may exist, but no supported stable endpoint was established.
- Treat browser scraping or reverse-engineered DRS endpoints as brittle until explicitly accepted as a product/engineering tradeoff.

## Recommended Collection Architecture

Use a two-source bridge:

1. DRS is the applicability/index source.
2. Federal Register/govinfo is the publication/source-evidence source.

The MVP-safe path is:

1. Collect AD numbers from DRS for an aircraft make/model/status filter.
2. Resolve each AD number against Federal Register and/or govinfo.
3. Persist both provenance layers:
   - DRS query/filter/source context for applicability discovery.
   - Federal Register/govinfo document metadata, source URLs, PDFs, and raw snapshots for publication evidence.
4. Route unresolved or ambiguous AD numbers to human review instead of silently dropping them.

## Next Discussion Questions

- Should the first DRS bridge be human-assisted AD number entry/import, browser automation, or a brittle internal endpoint adapter?
- What is the minimum demo set for PA-28-180: latest 2 DRS ADs, all active DRS ADs, or a curated small known set?
- Should the app add a dedicated `source_system=drs` discovery/provenance table before building any scraper/import flow?
- How should DRS applicability evidence be displayed beside Federal Register/govinfo publication evidence in the AD review UI?

## Recommended Next Task

Implement a small DRS-to-Federal-Register bridge slice:

1. Add a source/provenance model or fields for DRS AD-number collection.
2. Add a worker/service that accepts AD numbers from a DRS-derived list.
3. Resolve each AD number through Federal Register search.
4. Persist links between DRS applicability context and Federal Register/govinfo publication records.
5. Add tests proving AD-number resolution and unresolved-number review behavior.

Do not treat Federal Register term search as authoritative aircraft applicability.
