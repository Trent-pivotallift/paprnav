# AD Pipeline Spec v2 Review

Last updated: 2026-06-20

Reviewed source: `/Users/hostiletakeover/Downloads/ad-pipeline-spec-v2.md`

## Assessment

The v2 spec is directionally strong for the next ingestion build, but it is not a drop-in replacement for the current Paprnav plan. It correctly keeps the product in a decision-support posture, preserves source citations, adds demand-driven applicability crawling, and recognizes that AD matching depends on aircraft components rather than only aircraft make/model.

The main risk is that it reopens foundational choices and scaffolding that the repo has already moved past. Paprnav already has FastAPI, SQLAlchemy, Alembic, Postgres, local file storage, Federal Register discovery, deterministic AD extraction, review, matching, and HITL adjudication. The next work should extend and refactor that implementation, not create a separate `ad_pipeline/` project from scratch.

## Recommendation

Keep PostgreSQL as the structured store for the MVP and near-term AWS target.

Reasons:

- The existing repo already uses Postgres, SQLAlchemy, and Alembic.
- The AD domain is relationship-heavy: aircraft, installed components, applicability targets, ADs, publications, extractions, supersession, match evidence, and human decisions all need joins.
- The workflow needs auditability, replay, ad-hoc review queries, and migration history more than it needs zero-idle-cost storage.
- Year-one scale of hundreds to low thousands of GA customers does not justify single-table DynamoDB complexity.
- DynamoDB remains a future option for derived read models, queue state, or high-volume event projections if a specific access pattern proves it needs it.

This confirms `.ai/DECISIONS.md` D004 and D012. Do not branch the MVP schema to DynamoDB unless the product deliberately optimizes for lowest possible idle AWS cost over implementation clarity and query flexibility.

## Conflicts For Human Debate

### 1. Federal Register-first vs DRS-first

Resolved 2026-06-20 in favor of a revised DRS-first direction: DRS bulk ZIP/Access database ingestion first, then Federal Register comparison/enrichment.

Previous Paprnav MVP planning said Federal Register was the primary AD discovery source and FAA DRS was later reconciliation/backfill. The v2 spec made DRS the primary applicability index for demand-driven target crawls, with Federal Register used for XML matching and deltas. Subsequent validation found a better default than UI crawling: the public DRS AD Final Rules/Emergency ADs bulk download currently provides a ZIP containing an Access database.

Debate:

- Federal Register-first is simpler, official, API-backed, and already partially implemented.
- DRS bulk data better supports the full AD corpus, including pre-1994 and DRS-indexed applicability behavior, without making UI scraping the primary ingestion path.
- DRS Web UI scraping has fragility, rate-limit, robots, and maintenance risks. It should be validation/diagnostic tooling, not the default ingestion mechanism.

Decision: use DRS bulk ZIP/Access database ingestion as the primary source for the revised ingestion build. Use Federal Register for comparison, publication metadata, XML/body extraction when available, correction/supersession reconciliation, and scheduled delta monitoring that marks affected targets stale or needing review.

Operational posture: if DRS bulk ingestion breaks, do not silently fall back to a Federal Register-only worklist that appears complete. Show the user a degraded-coverage warning that historical/DRS-indexed coverage is unverified or may be incomplete, and create an admin-visible repair/reconciliation issue for source retrieval or parser logic. Do not warn that pre-1994 is unavailable by default while DRS bulk ingestion is healthy; current validation found 6,792 pre-1994 AD identifiers in the bulk data, but complete historical coverage remains unproven.

### 2. Separate package vs integrated backend module

The v2 layout creates a standalone `ad_pipeline/` package with its own FastAPI app, Docker Compose, Alembic tree, and scripts. The repo already has `backend/app/...`, migrations, tests, and frontend routes.

Debate:

- Separate package improves future portability.
- Integrated backend avoids duplicated API, settings, migrations, auth, observability, and storage abstractions.

Recommendation: implement under the existing backend package, likely `backend/app/services/ad_*`, `backend/app/workers/ad_*`, and `backend/app/schemas/ads.py`, with small CLI worker entrypoints. Extract a standalone package only after the domain is stable.

### 3. Current AD schema vs target/applicability schema

Current implementation stores AD discovery records, directives, extractions, reviews, supersession, match results, evidence, and adjudication. It does not yet model `applicability_targets`, `installed_components`, `ad_publications`, or `ad_target_applicability` as first-class queryable tables.

Debate:

- Current JSON extraction is fast and flexible.
- Target/applicability tables are needed for correct component-specific matching and demand-driven crawls.

Recommendation: add relational target/applicability tables and migrate the matcher to use them, while retaining extraction JSON for audit and replay.

### 4. Aircraft facts vs installed components

Current `aircraft` rows have flat fields for engine and propeller make/model/serial. The v2 spec wants installed component rows with roles, serials, install/removal dates, and target references.

Debate:

- Flat fields are enough for the early UI.
- Installed components are necessary for twin engines, component changes, propeller swaps, appliances, rotorcraft, and serial-specific AD applicability.

Recommendation: preserve the flat fields for display/backward compatibility, but introduce `installed_components` as the matching source of truth.

### 5. Pre-1994 ADs

Current Federal Register ingestion naturally covers modern FR records. The v2 spec calls out pre-1994 ADs as important for older GA aircraft.

Debate:

- Deferring pre-1994 keeps MVP smaller.
- A GA compliance tool for Cessna/Piper fleets will look incomplete if older effective ADs are missing.

Recommendation: ingest pre-1994 ADs when present in the DRS bulk database. Do not claim complete pre-1994 historical coverage until separate validation compares DRS bulk against DRS Web UI samples and available historical FAA/index sources.

### 6. LLM extraction depth

Current deterministic extraction is intentionally shallow and routes many items to review. The v2 spec expects regex plus LLM extraction to populate structured target applicability and compliance rows.

Debate:

- Deterministic extraction is cheap and testable.
- Applicability and compliance details are too variable for regex-only quality.

Recommendation: define a provider interface and schema first, add fixture-backed tests, then add provider-backed LLM extraction behind explicit caching and review thresholds.

## Impact On Existing Tasks

Completed tasks T045-T054 are still valid as a prototype path, but they should be treated as scaffolding rather than final ingestion architecture.

- T046 remains useful for Federal Register discovery, but should be expanded to fetch full XML and support date watermarks.
- T047 needs a second schema migration adding publications, applicability targets, target applicability, installed components, and crawl state.
- T049 needs to evolve from shallow deterministic extraction into schema-validated applicability/compliance extraction with citations.
- T052 currently matches approved extraction JSON against logbook text. It should be refactored to compute applicable ADs through installed components and target applicability before searching logbook evidence.
- T053 and T054 remain important; they become the human review surface for unresolved applicability, uncertain compliance evidence, and extraction conflicts.

Earlier OCR tasks T038-T044 remain upstream dependencies. The AD comparison flow only becomes meaningful when structured logbook entries and source evidence exist.

## Revised Agentic Task Path

Use these as the next AD-ingestion completion path rather than restarting from v2 Phase 0.

1. Confirm AD architecture decisions in `.ai/DECISIONS.md`: Postgres remains the store, DRS bulk ZIP/Access ingestion becomes the primary AD corpus/applicability path, Federal Register becomes comparison/enrichment/delta reconciliation, and the code stays integrated in `backend/app`.
2. Add first-class tables and migrations for applicability targets, installed components, AD publications, AD-target applicability, and crawl/reconciliation issues.
3. Backfill installed components from existing aircraft engine/propeller fields and make new aircraft create/update paths maintain component rows.
4. Add/maintain a DRS bulk validation spike using the public bulk page, saved ZIP/Access fixtures, parser evidence, and Federal Register comparison results.
5. Implement a fixture-first DRS bulk importer that stores DRS artifacts, parses Access rows, creates directives/publications/applicability targets, and links ADs to applicability targets without hitting live DRS in CI.
6. Add AD number, amendment, docket, and FR citation normalization utilities with tests, including two-digit pre-2000 AD numbers.
7. Upgrade the Federal Register client to support comparison/enrichment: document detail, term search, XML/body retrieval, source artifact storage, and publication-date delta monitoring.
8. Implement AD-to-Federal-Register matching for AD numbers discovered from DRS bulk data and link matching publications to directives.
9. Replace shallow extraction output with schema-validated applicability and compliance extraction that can populate `ad_target_applicability` and cite source sections.
10. Add provider-backed LLM extraction only after fixtures prove the target schema and review UX are stable.
11. Refactor matching to union applicable ADs across installed components, apply serial/condition/status filters, then search structured logbook entries for compliance evidence.
12. Extend the AD worklist to show component/target applicability, source publications, crawl status, and unresolved reasons separately from compliance evidence.
13. Add reconciliation jobs for missing FR matches, stale DRS bulk data, extraction gaps, pre-1994 validation gaps, and supersession/correction conflicts.

## Agent Guardrails

- Do not build a separate `ad_pipeline/` project unless explicitly approved.
- Do not switch to DynamoDB unless the human decision changes D004/D012.
- Do not scrape live DRS in CI.
- Do not make DRS Web UI scraping the primary ingestion path unless a later human decision explicitly accepts that tradeoff.
- Do not hide DRS outage or staleness behind apparently complete Federal Register-only results.
- Do not represent a candidate match as compliance attestation.
- Keep raw/source artifacts and normalized text or hashes for replay and citations.
- Prefer fixture-backed worker tests before live network work.
