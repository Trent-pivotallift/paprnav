# paprnav MVP Completion Definition

Last updated: 2026-06-20

This is the working definition of "webapp complete" for the MVP. It supersedes earlier CRUD-oriented task summaries.

## MVP Product Thesis

paprnav ingests scanned aircraft logbooks, uses OCR and human review to turn them into structured maintenance records, ingests FAA Airworthiness Directives, and helps users identify likely AD compliance gaps with citations and human-in-the-loop adjudication.

The product is decision support, not an official compliance attestation.

## End-To-End MVP Workflow

1. A customer signs in and creates or selects an aircraft.
2. The customer uploads scanned logbook images or PDFs.
3. The app creates an ingestion job and stores the original upload.
4. The OCR pipeline extracts page images, text, bounding boxes, confidence scores, and page-level metadata.
5. The user verifies page order and confirms whether the upload is complete.
6. Low-confidence OCR regions are shown back to the user as highlighted snippets with focused translation/correction fields.
7. User corrections are saved as structured HITL annotations tied to the source page, bounding region, OCR output, corrected text, user, timestamp, and confidence reason.
8. The ingestion pipeline converts verified OCR plus corrections into normalized logbook entries.
9. Logbook entries persist in the database with links back to original source artifacts and OCR evidence.
10. The AD ingestion process imports the FAA DRS bulk ZIP/Access database as the primary AD corpus and applicability source, then compares/enriches those ADs with Federal Register publication records when available.
11. AD ingestion stores source metadata, source documents or source references, structured applicability, compliance requirements, supersession relationships, and extraction confidence.
12. The app matches applicable ADs against structured logbook entries.
13. Matching accounts for one-time, recurring/cyclical, conditional, component-specific, and superseded ADs.
14. If an AD is not found, cannot be confidently matched, or requires judgment, the app creates a HITL adjudication task.
15. HITL adjudications are documented for review by a software/admin user and future model/rule development.
16. The user sees an aircraft compliance worklist with candidate matches, unresolved items, cited evidence, and confidence status.

## Required MVP Capabilities

### Account And Aircraft Setup

- Users can register, sign in, sign out, and stay signed in across refreshes.
- Users can create aircraft records with at least N-number, make, model, serial number if known, engine information if known, and propeller information if known.
- Aircraft make/model/component identity can be updated as ingestion discovers better data.

### Logbook Upload And OCR

- Users can upload scanned PDFs and image files.
- Original uploads are stored and retrievable.
- Each upload creates an ingestion job with status tracking.
- The OCR process stores page order, page images or page references, extracted text, bounding regions, and confidence scores.
- The UI supports page-order verification and completeness confirmation.
- The UI presents low-confidence OCR regions as highlighted snippets with user correction fields.
- Corrections persist as auditable HITL annotations.

### Logbook Data Model

- Verified/corrected OCR is transformed into structured logbook entries.
- Each entry records date, aircraft, logbook section, source page(s), description, performer, certificate/credential when available, tach/hobbs/total time when available, and extracted raw text.
- Entries preserve source traceability back to upload, page, and OCR/HITL evidence.

### AD Ingestion

- The revised AD process uses FAA DRS bulk ZIP/Access database ingestion as the primary AD corpus and applicability path, then uses Federal Register comparison/enrichment for publication metadata, XML/body text when available, corrections, supersession, and delta monitoring.
- DRS Web UI automation is validation/diagnostic only unless a later human decision accepts it as an ingestion fallback.
- FAA `Rule` documents from Federal Register must still be filtered/classified for actual Airworthiness Directives; not every FAA rule is an AD.
- AD source metadata is persisted, including DRS source context, Federal Register document number when matched, title, publication date, HTML URL, PDF URL when present, and content hash.
- AD structured extraction captures applicability, affected aircraft/components, compliance actions, compliance intervals, effective date, supersedes/superseded-by relationships, and extraction confidence.
- If DRS bulk ingestion fails or is stale, the user sees an explicit degraded-coverage warning that the applicable AD universe may be incomplete and historical/DRS-indexed AD coverage is unverified.
- Pre-1994 ADs are supported when present in DRS bulk data, but complete historical coverage must not be claimed. The 2026-06-21 T071 validation result is conditional and requires more rendered DRS Web UI snapshots or independent historical indexes before any completeness claim.
- DRS failures create admin-visible repair/reconciliation work items instead of silently falling back to an apparently complete Federal Register-only result.
- Low-confidence AD extraction routes to a review queue instead of silently becoming authoritative.

### AD Storage Recommendation

- For MVP, keep structured AD data in the application database and keep raw/source artifacts or stable source snapshots in object storage.
- Do not discard AD data after each pull. Retention enables auditability, supersession tracking, deterministic re-matching, cache reuse, and offline/replay behavior.
- Save storage by de-duplicating raw artifacts with content hashes, storing compressed text snapshots, and using object-storage lifecycle policies for bulky PDFs/images after the active review window.
- Keep structured normalized AD records indefinitely unless a formal retention policy says otherwise.

### AD Matching And HITL Adjudication

- Matching compares AD applicability against aircraft identity and component identity.
- Matching compares AD compliance requirements against structured logbook entries.
- The matcher must handle one-time, recurring/cyclical, conditional, component-specific, and superseded ADs.
- The system should bias toward unresolved/needs-review rather than false compliance.
- HITL adjudication records include the AD, aircraft, candidate logbook entries, system rationale, user/admin decision, reviewer notes, timestamp, and follow-up tags for future rule/model improvements.

### Admin And Review

- Admin/reviewer users can see OCR correction queues, AD extraction review queues, and AD matching adjudication queues.
- Admin/reviewer users can review HITL adjustments and mark patterns for future automation.
- The app preserves audit trails for changes to OCR corrections, structured entries, AD extraction, and adjudication outcomes.

## Out Of Scope For MVP

- Official regulatory compliance attestation.
- Foreign authority AD ingestion such as EASA or TCCA.
- Fully automated no-review compliance determination.
- Real-time emergency AD notification beyond a documented future hook.
- Complete historical AD coverage claims beyond the current DRS bulk data and validation evidence.

## MVP Done Checklist

- A sample aircraft can be created.
- A scanned logbook upload can be OCR processed.
- A user can verify page order/completeness.
- A user can correct low-confidence OCR snippets.
- Corrected ingestion produces persisted structured logbook entries.
- The AD ingester can fixture-load or import FAA DRS bulk ZIP/Access data and compare/enrich discovered ADs with Federal Register records.
- Structured AD data persists and is queryable by aircraft/component applicability.
- The app can produce candidate AD-to-logbook matches.
- DRS outage/staleness produces visible coverage warnings and admin repair alerts.
- Uncertain matches create HITL adjudication tasks.
- HITL decisions are persisted and visible for admin/software review.
- Critical flows have automated tests or documented manual verification.
- The UI uses API-backed data for the above flows instead of inline mock arrays.
