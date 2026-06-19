# paprnav Data Model Plan

Last updated: 2026-06-16

This is the first-pass backend domain model plan for the paprnav MVP. It is a design note only: no database tables, migrations, or ORM models have been implemented by this task.

The model assumes FastAPI, Postgres, and a future migration stack. It should be refined before T017 creates actual tables.

## Modeling Principles

- Use stable server-generated IDs for internal references.
- Treat N-number as a central aircraft identifier, but do not use it as the only primary key.
- Preserve original uploaded files and trace structured logbook entries back to source artifacts.
- Represent human review explicitly instead of silently overwriting OCR, AD extraction, or matching output.
- Prefer review-needed states over false certainty for compliance-related conclusions.
- Store timestamps consistently: `created_at`, `updated_at`, and review/action-specific timestamps where needed.
- Include `created_by_user_id` or equivalent actor fields for auditable user actions.

## Core Entities

### User

Represents an authenticated person using paprnav.

Required fields:

- `id`
- `email`
- `name`
- `password_hash`
- `external_auth_subject` for future managed identity migration
- `status`: active, invited, disabled
- `created_at`
- `updated_at`

Relationships:

- User has many organization memberships.
- User can create aircraft, uploads, manual entries, OCR corrections, and review decisions.

Open questions:

- D010 selects FastAPI-owned session auth for the MVP.
- Keep `external_auth_subject` nullable so a future managed auth provider can be introduced without changing domain ownership.

### Organization

Represents an aircraft owner entity, maintenance shop, or future admin/reviewer organization.

Required fields:

- `id`
- `name`
- `type`: owner, maintenance_shop, admin, other
- `created_at`
- `updated_at`

Relationships:

- Organization has many memberships.
- Organization can own or manage aircraft.

Open questions:

- Whether single-owner users need a first-class organization on day one.
- Whether maintenance shops require client organizations before the first MVP workflow.

### OrganizationMembership

Connects users to organizations with a role.

Required fields:

- `id`
- `organization_id`
- `user_id`
- `role`: owner_admin, owner_member, maintenance_admin, maintenance_tech, reviewer, admin
- `status`: active, invited, removed
- `created_at`
- `updated_at`

Relationships:

- Membership belongs to one user and one organization.
- Authorization checks should use membership role and aircraft assignment records.

Open questions:

- Exact role names may change once T030 defines the role and assignment workflow.

### Aircraft

Represents an aircraft record visible to an owner or assigned maintenance shop.

Required fields:

- `id`
- `owner_organization_id`
- `n_number_raw`
- `n_number_normalized`
- `make`
- `model`
- `serial_number`
- `year`
- `status`: active, archived
- `created_by_user_id`
- `created_at`
- `updated_at`

Recommended component identity fields:

- `airframe_serial_number`
- `engine_make`
- `engine_model`
- `engine_serial_number`
- `propeller_make`
- `propeller_model`
- `propeller_serial_number`

Relationships:

- Aircraft belongs to an owner organization.
- Aircraft can have maintenance shop assignments.
- Aircraft has many logbook entries, uploads, OCR ingestion jobs, and AD matching results.

Open questions:

- Whether engines and propellers should start as separate component records or fields on aircraft.
- How to represent multiple engines, swapped engines, and historical component changes.

### AircraftAssignment

Represents maintenance-shop access to an aircraft.

Required fields:

- `id`
- `aircraft_id`
- `organization_id`
- `assigned_by_user_id`
- `role`: maintainer, viewer, reviewer
- `status`: active, revoked
- `created_at`
- `updated_at`

Relationships:

- Assignment belongs to one aircraft and one organization.
- Maintenance dashboard visibility should be based on active assignments.

Open questions:

- Whether owner users can assign individual maintenance users directly, or only organizations.

### LogbookSection

Represents a logbook category.

Required fields:

- `id`
- `key`: airframe, engine, propeller
- `name`
- `sort_order`

Relationships:

- Logbook entries reference one section.

Open questions:

- Whether avionics, appliance, or component-specific sections should be added during MVP.

### LogbookEntry

Represents a structured maintenance record.

Required fields:

- `id`
- `aircraft_id`
- `logbook_section_id`
- `entry_date`
- `description`
- `performer_name`
- `performer_credential`
- `source_type`: manual, ocr_ingestion, import
- `created_by_user_id`
- `created_at`
- `updated_at`

Recommended fields:

- `tach_time`
- `hobbs_time`
- `total_time`
- `raw_text`
- `review_status`: draft, needs_review, verified

Relationships:

- Entry belongs to an aircraft and section.
- Entry can link back to upload pages, OCR spans, and corrections through evidence link records.
- Entry can be candidate evidence for AD matching.

Open questions:

- Whether logbook entry revisions require a separate history table immediately or can be added with audit events later.

### Upload

Represents an original user-submitted file.

Required fields:

- `id`
- `aircraft_id`
- `uploaded_by_user_id`
- `original_filename`
- `content_type`
- `file_size_bytes`
- `storage_backend`: local, s3, other
- `storage_key`
- `sha256`
- `status`: received, rejected, stored
- `created_at`
- `updated_at`

Relationships:

- Upload belongs to an aircraft.
- Upload can create one or more ingestion jobs.
- Upload is the source for extracted pages and structured entries.

Open questions:

- D013 selects local filesystem storage for development and S3 or S3-compatible object storage for production behind a storage abstraction.
- Whether one upload can contain multiple logbook sections or aircraft should be constrained in MVP.

### ComplianceStatusSnapshot

Represents a summary status for fast dashboard display.

Required fields:

- `id`
- `aircraft_id`
- `status`: compliant, warning, overdue, needs_review, unknown
- `basis`: manual, computed_ad_matching
- `summary`
- `computed_at`
- `created_at`

Relationships:

- Snapshot belongs to an aircraft.
- Snapshot should be derived from AD matching and HITL adjudication once those systems exist.

Open questions:

- Whether this should be materialized in the database or computed from AD worklist records for MVP.

## Human Product Observability Entities

Human product observability means product-facing evidence that helps a human operator, founder, support person, or reviewer understand what users tried to do, where they got stuck, and what state the system believes each workflow is in. This is separate from infrastructure logs and metrics.

### ProductEvent

Represents a user or system event that is useful for product debugging, demo review, onboarding analysis, or support.

Required fields:

- `id`
- `actor_user_id`
- `organization_id`
- `aircraft_id`
- `event_type`
- `event_source`: frontend, backend, worker
- `subject_type`: aircraft, logbook_entry, upload, ingestion_job, ocr_correction, ad_review, auth, profile, other
- `subject_id`
- `event_time`
- `properties_json`
- `request_id`
- `session_id`
- `created_at`

Relationships:

- Event can reference a user, organization, aircraft, and a workflow subject.
- Event should not be required for core transactional correctness.

Privacy notes:

- Do not store raw logbook text, passwords, secrets, uploaded file contents, or full OCR output in event properties.
- Store identifiers, statuses, durations, counts, confidence bands, and high-level outcome reasons instead.

### UserFeedback

Represents explicit user feedback during demos, upload review, OCR correction, AD review, or support.

Required fields:

- `id`
- `submitted_by_user_id`
- `organization_id`
- `aircraft_id`
- `subject_type`
- `subject_id`
- `feedback_type`: confusion, bug, feature_request, data_quality, compliance_concern, demo_note, other
- `message`
- `severity`: low, medium, high
- `status`: open, triaged, closed
- `created_at`
- `updated_at`

Relationships:

- Feedback can link to a product event, upload, ingestion job, OCR correction, AD review task, or compliance worklist item.
- Feedback should be visible in a human review/admin surface before MVP release.

### WorkflowStatusEvent

Represents state transitions for long-running workflows in a human-readable way.

Required fields:

- `id`
- `workflow_type`: upload_ingestion, ocr_processing, page_verification, ocr_correction, ad_ingestion, ad_extraction, ad_matching, hitl_adjudication
- `workflow_id`
- `previous_status`
- `new_status`
- `reason`
- `actor_type`: user, system, worker, reviewer
- `actor_user_id`
- `created_at`

Relationships:

- Workflow status events supplement domain tables such as `IngestionJob` and AD extraction review tables.
- They are useful for support timelines, demo debugging, and release audit evidence.

Open questions:

- Whether `ProductEvent` and `WorkflowStatusEvent` should be one table with typed categories or two separate tables.
- Whether local MVP should expose these through a lightweight admin page or only through API/debug views first.

## AD Ingestion Entities

These entities implement the local MVP AD ingestion track from Federal Register discovery through human-reviewed structured extraction.

### ADDiscoveryRecord

Represents one Federal Register source document returned by the AD discovery worker.

Required fields:

- `id`
- `federal_register_document_number`
- `title`
- `document_type`
- `abstract`
- `publication_date`
- `effective_date`
- `html_url`
- `pdf_url`
- `public_inspection_pdf_url`
- `agency_names`
- `excerpts`
- `api_snapshot`
- `content_hash`
- `classification`: ad_candidate, non_ad_rule, rejected
- `classification_confidence`
- `classification_reason`
- `classifier_name`
- `classifier_version`
- `classified_at`

Audit notes:

- `api_snapshot` retains the raw per-document provider response.
- `content_hash` is computed from normalized provider JSON for replay/idempotency.
- FAA `RULE` documents are classified instead of assumed to be ADs.

### AirworthinessDirective

Represents an AD candidate or reviewed AD derived from a discovery record.

Required fields:

- `id`
- `discovery_record_id`
- `ad_number`
- `title`
- `status`
- `source_content_hash`
- `extraction_status`
- `review_status`
- `approved_at`

Relationships:

- Belongs to one discovery record.
- Has many extraction attempts.
- Has supersedes/superseded-by graph edges through `ADSupersession`.

### ADExtraction

Represents one structured extraction attempt for an AD.

Required fields:

- `id`
- `directive_id`
- `provider_name`
- `provider_version`
- `schema_version`
- `input_content_hash`
- `status`
- `confidence`
- `output`
- `citations`
- `raw_response`
- `extracted_at`

Audit notes:

- Idempotency is enforced by directive, input content hash, provider name, provider version, and schema version.
- Current local provider is `deterministic_ad_extractor` with schema `ad_extraction_v1`.

### ADExtractionReview

Represents human review of a low-confidence or uncertain AD extraction.

Required fields:

- `id`
- `extraction_id`
- `status`: pending, approved, edited, rejected
- `proposed_output`
- `decision_output`
- `decision`
- `reviewer_user_id`
- `notes`
- `reviewed_at`

Audit notes:

- Approved and edited decisions validate structured output before becoming available for matching.
- Rejected decisions preserve the proposed output and reviewer notes.

### ADSupersession

Represents a graph edge between two persisted AD records.

Required fields:

- `id`
- `superseding_ad_id`
- `superseded_ad_id`
- `relationship_type`
- `evidence_text`
- `confidence`

## AD Matching Entities

These entities connect approved AD extraction output to structured logbook entries.

### ADMatchResult

Represents one matcher result for an aircraft/directive pair under a specific algorithm replay input.

Required fields:

- `id`
- `aircraft_id`
- `directive_id`
- `extraction_id`
- `status`: candidate_satisfied, needs_adjudication
- `match_type`: one_time, simple_recurring
- `confidence`
- `rationale`
- `unresolved_reasons`
- `algorithm_name`
- `algorithm_version`
- `input_hash`
- `computed_at`

Audit notes:

- `input_hash` includes aircraft facts, approved AD extraction output, and logbook entry text/status.
- Status is product workflow evidence, not official compliance attestation.

### ADMatchEvidence

Represents a cited logbook entry that contributed to a match result.

Required fields:

- `id`
- `match_result_id`
- `logbook_entry_id`
- `evidence_type`
- `field_name`
- `matched_text`
- `confidence`
- `rationale`

Relationships:

- Evidence links back to structured logbook entries, which may themselves link to OCR spans and corrections.

### ADMatchAdjudication

Represents a pending or decided human review task for an unresolved AD match.

Required fields:

- `id`
- `match_result_id`
- `status`: pending, not_required, reviewed
- `decision`
- `reviewer_user_id`
- `notes`
- `reviewed_at`

## OCR Ingestion Entities

These entities extend the core model for T038. They preserve traceability from original upload through OCR, user corrections, and generated structured entries.

### IngestionJob

Represents processing state for an upload.

Required fields:

- `id`
- `upload_id`
- `aircraft_id`
- `created_by_user_id`
- `status`: queued, extracting_pages, ocr_processing, awaiting_page_review, awaiting_ocr_corrections, ready_for_entry_extraction, extracting_entries, complete, failed, canceled
- `page_extraction_status`
- `ocr_status`
- `verification_status`
- `entry_extraction_status`
- `error_code`
- `error_message`
- `created_at`
- `updated_at`
- `completed_at`

Relationships:

- Job belongs to one upload and aircraft.
- Job has many pages, OCR spans, HITL corrections, and generated entry links.

Audit notes:

- Status changes should either be reconstructable from timestamps or backed by a future job event table.

### IngestionPage

Represents one extracted page or image from an upload.

Required fields:

- `id`
- `ingestion_job_id`
- `upload_id`
- `source_page_number`
- `current_page_order`
- `page_label`
- `image_storage_backend`
- `image_storage_key`
- `width_px`
- `height_px`
- `rotation_degrees`
- `extraction_confidence`
- `created_at`
- `updated_at`

Relationships:

- Page belongs to an ingestion job.
- Page has many OCR spans.
- Page can be referenced by logbook entry evidence links.

Audit notes:

- Keep both original/source page number and current user-confirmed order.
- Do not discard page image references after structured entries are created.

### PageVerification

Represents a user's page-order and completeness decision for an ingestion job.

Required fields:

- `id`
- `ingestion_job_id`
- `verified_by_user_id`
- `is_order_confirmed`
- `is_complete`
- `missing_or_uncertain_notes`
- `verified_at`
- `created_at`

Relationships:

- Verification belongs to an ingestion job.
- Verification should record the page order that was confirmed, either as JSON or through page records updated in the same transaction.

Open questions:

- Whether repeated verification attempts should create multiple records or update a single current verification plus audit events.

### OCRRun

Represents one execution of an OCR provider against an ingestion job or page set.

Required fields:

- `id`
- `ingestion_job_id`
- `provider_name`
- `provider_version`
- `configuration_hash`
- `status`: queued, running, complete, failed
- `started_at`
- `completed_at`
- `error_message`
- `created_at`

Relationships:

- OCR run belongs to an ingestion job.
- OCR spans reference the run that produced them.

Open questions:

- D014 selects an OCR provider abstraction with a deterministic local provider first and a Textract-ready output shape.

### OCRTextSpan

Represents OCR output for a word, line, block, or region.

Required fields:

- `id`
- `ocr_run_id`
- `ingestion_page_id`
- `span_type`: word, line, block, region
- `text`
- `confidence`
- `bbox_x`
- `bbox_y`
- `bbox_width`
- `bbox_height`
- `bbox_units`: pixel, relative
- `reading_order`
- `created_at`

Relationships:

- Span belongs to an OCR run and page.
- Span can be corrected by a HITL OCR correction.
- Span can be linked to generated logbook entries as evidence.

Audit notes:

- Store low-confidence spans, not only high-confidence output.
- Preserve provider output enough to re-render highlighted snippets.

### OCRCorrection

Represents a human correction to an OCR span or region.

Required fields:

- `id`
- `ingestion_job_id`
- `ingestion_page_id`
- `ocr_text_span_id`
- `corrected_by_user_id`
- `original_text`
- `corrected_text`
- `original_confidence`
- `correction_reason`: low_confidence, illegible, wrong_text, missing_text, other
- `notes`
- `created_at`
- `updated_at`

Relationships:

- Correction belongs to an OCR span, page, job, and user.
- Corrections are source inputs for structured logbook entry extraction.

Audit notes:

- Do not overwrite OCR text with the correction. Store both.
- If corrections are edited, preserve prior values through a future audit event or correction revision table.

### LogbookEntryEvidence

Links structured logbook entries back to upload/OCR evidence.

Required fields:

- `id`
- `logbook_entry_id`
- `upload_id`
- `ingestion_job_id`
- `ingestion_page_id`
- `ocr_text_span_id`
- `ocr_correction_id`
- `evidence_type`: source_page, ocr_span, correction, extracted_field
- `field_name`: entry_date, description, performer_name, performer_credential, tach_time, other
- `confidence`
- `created_at`

Relationships:

- Evidence belongs to one logbook entry.
- Evidence can point to page, span, and correction records where available.

Audit notes:

- This is the main traceability bridge from a displayed structured entry to the original scan and human correction history.

## AD-Related Model Boundary

AD ingestion, extraction, supersession, matching, and adjudication are specified in `.ai/AD_INGESTION_MVP_SPEC.md`. They should share these modeling principles:

- Postgres stores structured AD records and review state.
- Object storage stores raw/source artifacts or snapshots.
- Matching output links AD records to aircraft, component facts, and logbook entry evidence.
- HITL adjudications are explicit records, not just status strings.

## Suggested Migration Grouping

When T017 implements the first schema, a practical migration order is:

1. Users, organizations, memberships.
2. Aircraft and aircraft assignments.
3. Logbook sections and logbook entries.
4. Upload metadata.
5. Human product observability event tables.
6. OCR ingestion jobs, pages, OCR runs, OCR spans, page verification, OCR corrections.
7. Logbook entry evidence links.
8. AD persistence and matching tables after `.ai/AD_INGESTION_MVP_SPEC.md` is accepted for implementation.

## Open Cross-Cutting Questions

- How should session records be modeled for D010: separate `Session` table, signed-cookie-only session IDs, or both?
- Should component identity be normalized into separate component records before the first AD matcher?
- Is the D013 default `100 MB` upload limit enough for the first real sample logbooks?
- How much audit history is required in the first migration versus later audit event tables?
