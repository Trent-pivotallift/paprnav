# paprnav Provider References

Last updated: 2026-06-27

Use this file whenever implementation depends on an external provider, API, SDK, CLI, file format, or output shape. Check current official documentation first, then record the mapping here before coding or marking the task complete.

## Reference-First Rule

Do not design provider contracts from trained memory. For each provider-backed task:

- Check current official documentation or another primary source.
- Record the URL and date checked.
- List the fields and behaviors the implementation depends on.
- Map provider-specific output to paprnav's provider-neutral schema.
- Note confidence scales, geometry units, pagination, async behavior, IDs, raw artifacts, and replay/audit implications.

## AWS Cost Allocation And S3 Object Tags

- Status: pilot billing/accounting design input
- Date checked: 2026-07-08
- References:
  - https://docs.aws.amazon.com/AmazonS3/latest/userguide/object-tagging.html
  - https://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/cost-alloc-tags.html

Verified fields and behaviors:

- S3 object tags are key/value pairs used to categorize storage.
- S3 objects can have up to 10 tags, with unique tag keys.
- Tags are case-sensitive.
- S3 supports adding tags when creating objects through PUT Object or multipart upload tagging headers, or adding/replacing them later through object tagging APIs.
- AWS Billing cost allocation tags apply to taggable AWS resources after activation. S3 object tags are object metadata and should not be treated as a per-customer AWS Cost Explorer dimension.
- AWS recommends not putting sensitive information in tags.

paprnav mapping notes:

- Store non-sensitive internal tags only: customer account tag, aircraft tag, upload tag, billing stage, project, environment, and app.
- Do not put customer names, emails, N-numbers, serial numbers, or raw logbook content in AWS tags.
- Upload rows persist `cost_allocation_tags` and `initial_ocr_billable_to_tag`.
- OCR runs persist `billable_account_tag`, `billable_aircraft_tag`, `billable_page_count`, and `cost_allocation_tags`.
- When S3-backed uploads are implemented, apply the persisted upload tag set as S3 object tags for paprnav reconciliation and object-level metadata.
- Textract OCR requests are not tagged per customer. paprnav must calculate chargeable OCR by persisted OCR run page counts and billable account/aircraft tags.

## OCR Providers

### AWS Textract

- Status: target production OCR provider
- Date checked: 2026-07-07
- References:
  - https://docs.aws.amazon.com/textract/latest/APIReference/API_Block.html
  - https://docs.aws.amazon.com/textract/latest/APIReference/API_Geometry.html
  - https://docs.aws.amazon.com/textract/latest/APIReference/API_DetectDocumentText.html
  - https://docs.aws.amazon.com/textract/latest/APIReference/API_StartDocumentTextDetection.html

Verified fields and behaviors:

- OCR output is represented as `Block` objects.
- Relevant `BlockType` values include `PAGE`, `LINE`, and `WORD`; analysis operations may also emit key-value, table, selection, signature, query, and layout block types.
- `Text` contains recognized text for text-bearing blocks.
- `Confidence` is a float from `0` to `100`.
- `Geometry` includes `BoundingBox`, `Polygon`, and optional `RotationAngle`.
- `Page` identifies the detected page; values greater than 1 are returned for multipage PDF/TIFF documents.
- `Relationships` connect blocks, such as line-to-word child relationships.
- Provider block IDs are operation-local, not durable global IDs.
- `DetectDocumentText` returns detected text as `Block` objects and is synchronous.
- `DetectDocumentText` accepts document bytes or S3 object references and returns `DocumentMetadata.Pages`.
- Synchronous operations have a smaller document-size limit than asynchronous operations; current docs list 10 MB for synchronous and 500 MB for asynchronous PDF processing.
- `StartDocumentTextDetection` starts asynchronous text detection for JPEG, PNG, TIFF, and PDF documents stored in S3 and returns a `JobId`.
- `StartDocumentTextDetection` supports idempotency through `ClientRequestToken`, optional `OutputConfig`, optional KMS key, and optional SNS notification channel.

paprnav mapping notes:

- Store confidence on a `0-100` scale to avoid lossy Textract conversion.
- Store bounding boxes with explicit units; Textract boxes should map to ratio units.
- Preserve optional polygon and rotation data when present.
- Preserve provider block IDs and relationships for audit/replay, but do not use them as stable domain IDs.
- Fixture OCR output should include page, line, and word examples with mixed confidence values.
- Current implementation adds an env-gated `aws_textract` provider behind the existing OCR provider abstraction. It uses `DetectDocumentText` for first-pass synchronous OCR and maps `LINE`/`WORD` Blocks into `OCRTextSpan` rows.
- Local MVP and CI still default to deterministic OCR. `PAPRNAV_OCR_PROVIDER=textract` is required to call Textract.
- S3-backed upload storage is env-gated with `PAPRNAV_STORAGE_BACKEND=s3`; when enabled, upload objects are written with server-side encryption and the persisted upload cost tag set. Textract S3 references use `PAPRNAV_TEXTRACT_S3_BUCKET` when set, otherwise `PAPRNAV_S3_UPLOAD_BUCKET`.
- Production PDF-heavy ingestion should move to S3-backed asynchronous `StartDocumentTextDetection` before broad volunteer ingestion, because multipage PDFs and larger uploads need the async path.

### Mistral OCR

- Status: third-party A/B candidate; not the default provider
- Date checked: 2026-07-19
- Reference:
  - https://mistral.ai/fr/news/ocr-4/
  - https://docs.mistral.ai/models/model-cards/ocr-4-0
  - https://docs.mistral.ai/api/endpoint/ocr
  - https://docs.mistral.ai/studio-api/regional-inference
- Target env vars:
  - `PAPRNAV_MISTRAL_API_KEY`
  - `PAPRNAV_MISTRAL_BASE_URL`
  - `PAPRNAV_MISTRAL_OCR_MODEL`
  - `PAPRNAV_MISTRAL_OCR_CHANNEL`
  - `PAPRNAV_MISTRAL_SAGEMAKER_ENDPOINT_NAME`
  - `PAPRNAV_MISTRAL_SAGEMAKER_REGION`
  - `PAPRNAV_MISTRAL_OCR_MODE`
  - `PAPRNAV_MISTRAL_OCR_MAX_PDF_PAGES`

paprnav mapping notes:

- Pin the A/B target to `PAPRNAV_MISTRAL_OCR_MODEL=mistral-ocr-4-0`, based on Mistral's OCR 4 release page.
- Mistral must be introduced behind the existing OCR provider abstraction as `PAPRNAV_OCR_PROVIDER=mistral`.
- Direct Mistral OCR uses the OCR endpoint `POST /v1/ocr`; current docs support `pages`, `include_blocks`, `confidence_scores_granularity`, `table_format`, and `usage_info.pages_processed`.
- Use base64 `data:application/pdf;base64,...` document URLs for the internal A/B slice instead of public S3 URLs.
- Direct Mistral API and SageMaker OCR-4 access are different deployment channels. Do not treat them as interchangeable in cost, IAM, logging, data-processing, or network-risk notes.
- Current regional inference docs list the EU endpoint as available and the US endpoint as coming soon. Do not treat direct API calls as US-resident unless a US regional/private endpoint is explicitly configured and verified.
- If the SageMaker channel is selected, use `PAPRNAV_MISTRAL_OCR_CHANNEL=sagemaker` and track endpoint/model package identifiers separately from `PAPRNAV_MISTRAL_API_KEY`.
- SageMaker invocation should use AWS IAM and `sagemaker-runtime:InvokeEndpoint` permissions scoped to the OCR-4 endpoint. Endpoint hourly/runtime cost must be tracked separately from direct API per-page pricing.
- Keep default local/CI OCR deterministic and keep AWS Textract available as the AWS baseline.
- Use Mistral first only for the N3671L A/B feasibility run, not customer-default processing.
- When Mistral is used, the upload/review flow must make a conditional third-party processing note visible to the user or reviewer.
- Persist provider name, provider version/model, API mode/channel, billable page count, billable account tag, billable aircraft tag, usage info, and estimated provider unit cost for chargeback.
- Customer OCR chargeback must come from paprnav `OCRRun` records, not provider dashboard totals.
- Promote Mistral to replacement or augmentation only after comparing entry count, field extraction quality, dash/blank preservation, evidence geometry, reviewer effort, and per-page cost against Textract on the same documents.

### Tesseract

- Status: possible local OCR adapter candidate; not selected as required MVP provider
- Date checked: 2026-06-18
- Reference:
  - https://tesseract-ocr.github.io/tessdoc/Command-Line-Usage.html

Verified fields and behaviors:

- `hocr` output includes page, block/area, paragraph, line, word classes, bounding boxes, OCR system metadata, and word confidence.
- `tsv` output includes columns such as `level`, `page_num`, `block_num`, `par_num`, `line_num`, `word_num`, `left`, `top`, `width`, `height`, `conf`, and `text`.
- Tesseract bounding boxes are pixel-based in the rendered image coordinate space.
- Tesseract confidence may be `-1` for non-word/grouping rows in TSV.

paprnav mapping notes:

- Store geometry units explicitly; Tesseract boxes should map to pixel units unless normalized by an adapter.
- Treat confidence `-1` as missing/not-applicable rather than low confidence.
- Preserve page/block/paragraph/line/word ordering fields as provider metadata where useful.
- A Tesseract adapter would need a PDF-to-image/page rendering step before OCR.

## Federal Register AD Discovery

- Status: implemented local discovery provider for T046
- Date checked: 2026-06-18
- References:
  - https://www.federalregister.gov/developers/documentation/api/v1
  - https://www.federalregister.gov/api/v1/documents.json

Verified fields and behaviors:

- FederalRegister.gov exposes public API endpoints and does not require API keys.
- FederalRegister.gov is an informational XML/web rendition, not the official legal edition; results should preserve links to official govinfo PDFs when available.
- Local discovery uses `GET /api/v1/documents.json`.
- Query parameters used by the implementation:
  - `conditions[agencies][]=federal-aviation-administration`
  - `conditions[type][]=RULE`
  - `conditions[term]=Airworthiness Directives`
  - `order=newest`
  - `page`
  - `per_page`
- Response fields used by the implementation:
  - `results`
  - `count`
  - `total_pages`
  - `next_page_url`
  - per-result `document_number`, `title`, `type`, `abstract`, `publication_date`, `effective_on` or `effective_date`, `html_url`, `pdf_url`, `public_inspection_pdf_url`, `agencies`, and `excerpts`.
- A live Docker worker run on 2026-06-18 successfully discovered 20 FAA AD candidates from the Federal Register API.

paprnav mapping notes:

- Persist the raw per-document API result in `ADDiscoveryRecord.api_snapshot`.
- Compute `content_hash` from normalized raw JSON for idempotency and replay.
- Treat `document_number` as the discovery idempotency key.
- Store source URLs and publication date directly on discovery records for review and audit.
- Classify FAA rules as `ad_candidate`, `non_ad_rule`, or `rejected`; do not assume every FAA `RULE` from FAA is an AD.
- Preserve govinfo `pdf_url` for official-source verification when present.

## FAA DRS Bulk Data And Target Validation

- Status: researched for T064 and validated with one-shot bulk ZIP comparison; bulk data is the preferred ingestion source, Web UI automation is validation/diagnostic only
- Date checked: 2026-06-20
- References:
  - https://www.faa.gov/regulations_policies/airworthiness_directives
  - https://drs.faa.gov/
  - https://drs.faa.gov/browse/ADFRAWD/doctypeDetails?Status=all&Make=Piper%20Aircraft%20Inc.&Model=PA-28-180
  - https://drs.faa.gov/browse/ADFREAD/doctypeDetails
  - https://drs.faa.gov/robots.txt
  - `backend/tests/fixtures/drs/pa28_180_target_crawl.metadata.json`
  - `tools/drs_zip_validation/validate_drs_zip.py`
  - `tools/drs_zip_validation/findings.md`

Verified fields and behaviors:

- FAA's public Airworthiness Directives page describes ADs as legally enforceable regulations issued under 14 CFR part 39 to correct unsafe conditions in products, and defines product as aircraft, engine, propeller, or appliance.
- The same FAA page links AD Rules, Emergency ADs, AD NPRMs, and AD Biweekly content to `drs.faa.gov`.
- `GET https://drs.faa.gov/` returned a JavaScript application shell titled `Dynamic Regulatory System`.
- The PA-28-180 browse URL returned the same DRS application shell rather than static result rows.
- `GET https://drs.faa.gov/robots.txt` returned the DRS application shell, not a conventional robots.txt policy with explicit crawl directives.
- DRS responses observed during T064 included `Cache-Control: private, no-store`, `Set-Cookie: session=...; Max-Age=600; HttpOnly; Secure`, and an Angular-style app shell with module bundles such as `main-Y7GYRONB.js`.
- Public bundle inspection showed route/module terms such as `browse`, `search`, `document`, `drs-api`, and DRS browse/search modules, but no supported public API contract was established.
- No documented public DRS API, pagination contract, rate limit, or stable machine-readable AD result schema was found during this research pass.
- The DRS AD Final Rules/Emergency ADs page rendered a public bulk download control named `ADFinalRulesEmergencyADs_05312026.zip`.
- The downloaded ZIP contained one Access database: `ADFinalRulesEmergencyADs_05312026.accdb`.
- One-shot validation extracted 19,731 normalized AD identifiers from the Access database, spanning 1941 through 2026.
- The same validation compared the full DRS ZIP identifier set against the 2024 Federal Register AD identifier set and found 273/273 Federal Register AD identifiers present in the full DRS ZIP, for 100.00% full-source coverage.
- The AD-year surrogate comparison for 2024 was 250/273, or 91.58%, because Federal Register publications in early 2024 included late-2023 AD numbers that were present in the full DRS ZIP but outside the AD-year filter.
- The DRS bulk data includes 6,792 pre-1994 AD identifiers in the current extracted set, so pre-1994 should not be treated as unavailable by default. Completeness of the historical corpus is not proven.

paprnav mapping notes:

- Treat DRS bulk ZIP/Access database ingestion as the primary AD corpus and applicability source by product decision D017.
- Do not build the first production ingestion path around DRS Web UI scraping. Use UI automation only for validation, diagnostics, or targeted reconciliation when bulk data appears stale or incomplete.
- Do not build or depend on reverse-engineered DRS endpoints without a separate explicit decision.
- Do not run live DRS scraping or browser automation in CI.
- DRS bulk retrieval/parsing tests should use saved fixtures or small retained sample artifacts in CI.
- Live manual runs, when explicitly enabled, must use a descriptive User-Agent, slow request pacing, retries with exponential backoff, resumable crawl state, and artifact hashing.
- Default live pacing for any future manual run should be no faster than one request every 3 seconds until better FAA guidance or observed throttling behavior justifies a change.
- If `robots.txt` remains unavailable/non-informative, continue treating Web UI crawling permission as unresolved and keep that path conservative, fixture-first, and manually gated.
- Required fixture artifacts for DRS bulk ingestion:
  - Bulk ZIP filename, capture timestamp, source page URL, and artifact hash.
  - Extracted Access database filename and hash.
  - Parsed row count, table/column inventory, and parser version.
  - Normalized AD identifier set, plus sampled rows with dates, status, make, model, product type/subtype, supersession fields, and attachment references once row-level parsing is implemented.
  - Federal Register reconciliation results for a modern comparison window.
- Required fixture artifacts for any future target/Web UI validation:
  - DRS query/filter metadata.
  - DRS app-shell HTML for the target URL.
  - Rendered result-list snapshot or normalized manual row export.
  - DRS detail HTML per sampled AD when needed.
  - Linked PDF or PDF metadata per sampled AD when needed.
  - Artifact hashes and capture timestamps.
- Required normalized fixture fields:
  - `targetId`, `componentType`, `make`, `model`.
  - DRS query URL and filters.
  - `adNumber`, title/subject, DRS status when available, source URL, PDF URL or PDF metadata, and artifact hashes.
  - Federal Register document number when already matched, otherwise unresolved-match state.
- Required DRS source/import states:
  - `never_crawled`
  - `fixture_ready`
  - `in_progress`
  - `complete`
  - `partial`
  - `stale`
  - `failed`
  - `unavailable`
- `failed`, `stale`, and `unavailable` are degraded coverage states. They must create admin-visible reconciliation/workflow issues and allow the UI to warn users that historical and DRS-indexed AD coverage is unverified or may be incomplete. Do not warn that pre-1994 is unavailable by default while DRS bulk ingestion is healthy.
- The first production-oriented implementation should parse the DRS bulk ZIP/Access database from saved fixtures and must not require live DRS network access in tests.
- Pre-1994 completeness validation should be treated as a separate confidence track: compare DRS bulk against sampled DRS Web UI results and available historical FAA/index sources before claiming complete historical coverage.

### T071 Pre-1994 Historical Validation Result

- Status: completed as a conditional/low-risk-gating validation pass on 2026-06-21.
- References:
  - https://www.faa.gov/regulations_policies/airworthiness_directives
  - https://drs.faa.gov/browse/ADFRAWD/doctypeDetails?Status=all&Make=Piper%20Aircraft%20Inc.&Model=PA-28-180
  - `tools/drs_zip_validation/validate_pre1994.py`
  - `tools/drs_zip_validation/pre1994_validation_sources.json`
  - `tools/drs_zip_validation/pre1994_findings.md`
  - `tools/drs_zip_validation/pre1994_validation_report.json`
  - `backend/tests/fixtures/drs/pre1994_historical_validation.sample.json`

Result:

- The current DRS bulk extraction still supports pre-1994 presence: 6,792 normalized pre-1994 identifiers from `ADFinalRulesEmergencyADs_05312026.accdb`, with sampled identifiers spanning 1941, 1965, 1977, 1989, 1992, and 1993.
- The T071 sample set includes high-value GA targets/components: Piper PA-28-180, Cessna 172R, Lycoming O-320, and McCauley propeller.
- The local ZIP identifier cross-check passed for all sampled AD identifiers in `pre1994_validation_sources.json`.
- The current FAA Airworthiness Directives page confirms ADs are FAA regulations under 14 CFR part 39 and links AD Rules and AD Biweekly access to DRS; it does not provide a static pre-1994 historical index for the sampled targets/components.
- Static HTTP capture of the PA-28-180 DRS target URL reached the DRS app shell but did not expose parseable result rows. Rendered Web UI result-list snapshots are still required for unresolved target samples.
- Confidence level is `conditional`, not complete. The validation supports the claim that pre-1994 ADs are included when present in the current DRS bulk data; it does not support a claim of complete pre-1994 historical coverage.

Operational mapping:

- `backend/app/services/ad_historical_validation.py` records unresolved T071 samples as `ADReconciliationIssue` rows.
- Missing samples should use `pre1994_validation_missing` with high severity.
- App-shell-only or unparseable DRS target snapshots should use `pre1994_validation_snapshot_unparseable`.
- Samples lacking independent historical/index evidence should use `pre1994_validation_historical_source_unavailable`.
- User-facing copy must remain conservative: "Pre-1994 ADs are included when present in the current DRS bulk data; complete historical coverage has not been proven."

## AD Extraction Providers

- Status: implemented local deterministic extraction provider for T049; future LLM provider remains behind the same metadata/review contract
- Date checked: 2026-06-18
- References:
  - `.ai/DECISIONS.md` D015
  - `backend/app/services/ad_extraction.py`

Verified fields and behaviors:

- Current implementation is an internal deterministic provider, not an external LLM or SaaS API.
- Provider metadata persisted:
  - `provider_name=deterministic_ad_extractor`
  - `provider_version=0.1.0`
  - `schema_version=ad_extraction_v1`
  - `input_content_hash`
- Structured output validates required keys before persistence/review approval:
  - `adNumber`
  - `title`
  - `effectiveDate`
  - `publicationDate`
  - `affectedProducts`
  - `complianceActions`
  - `complianceIntervals`
  - `supersedesAdNumbers`
  - `sourceUrls`
- Confidence is a local `0.0-1.0` score.
- Low-confidence extraction routes to `ADExtractionReview`.
- Idempotency uses directive id, input content hash, provider name, provider version, and schema version.
- A live Docker worker run on 2026-06-18 processed 20 directives and queued 13 pending human reviews.

paprnav mapping notes:

- Internal deterministic extraction is intentionally conservative and review-first.
- Future provider-backed extraction must check current provider docs before implementation and map request/response shape, model/version, structured output behavior, confidence/uncertainty, citations, retries, and idempotency here.

### OpenAI Responses API Structured Outputs

- Status: optional provider-backed AD extraction path for T067, gated by configuration and retaining deterministic fallback
- Date checked: 2026-06-27
- References:
  - https://developers.openai.com/api/docs/guides/structured-outputs
  - https://developers.openai.com/api/reference/resources/responses/methods/create

Verified fields and behaviors:

- Responses API creation accepts a `text.format` object that controls model output format.
- `{"type": "json_schema"}` enables Structured Outputs and constrains the model to match the supplied JSON schema.
- JSON Schema response format includes `type=json_schema`, `name`, `schema`, optional `description`, and optional `strict`.
- `strict=true` enables exact schema adherence with the supported JSON Schema subset.
- Responses may expose model text through an `output_text` convenience field or through message `output` content items.

paprnav mapping notes:

- The OpenAI provider request uses `model`, structured system/user `input`, and `text.format` with `type=json_schema` and `strict=true`.
- Preserve response id, model, usage, provider request shape, schema version, prompt hash, and raw response metadata in `ADExtraction.raw_response` for audit/replay.
- Provider version encodes model and prompt/ruleset hash so the existing idempotency key covers input content hash, model, prompt/ruleset hash, and schema version.
- The provider returns a model-reported `confidence` on a `0.0-1.0` scale; paprnav treats this as review-routing metadata, not a calibrated probability.
- Missing applicability/compliance details, provider uncertainty, low confidence, or disagreement with deterministic safety-critical fields must route to `ADExtractionReview` instead of silently changing authoritative applicability.
- If the provider is disabled, unavailable, returns invalid structured output, or raises an error, extraction falls back to the deterministic provider.

## GitHub Actions

- Status: no workflow committed
- Date checked: 2026-06-27
- References:
  - https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax
  - https://docs.github.com/en/actions/tutorials/authenticate-with-github_token
  - https://docs.github.com/en/actions/how-tos/secure-your-work/security-harden-deployments/oidc-in-aws

Notes:

- A CI workflow draft was intentionally not retained because the available GitHub OAuth token lacked `workflow` scope to push `.github/workflows/ci.yml`.
- Reintroduce CI only after using credentials with workflow scope.
- Workflow files must be YAML files under `.github/workflows`.
- The first CI workflow should use least-privilege `permissions: contents: read`.
- GitHub recommends granting `GITHUB_TOKEN` the least required permissions.
- AWS deployment workflows, once added, should use OIDC rather than long-lived AWS keys; GitHub's AWS OIDC guidance uses `https://token.actions.githubusercontent.com` as the provider URL, `sts.amazonaws.com` as the audience for the official AWS credentials action, and a trust policy constrained by the `sub` condition.

Required before adding deployment or privileged workflow steps:

- Current AWS service docs for the selected runtime, database, storage, secrets, logging, and IaC tooling.
- Repository credential with workflow scope to create/update `.github/workflows/ci.yml`.
- Cache behavior and security guidance for pull requests.

## Terraform And AWS Pilot IAM

- Status: planning reference for controlled AWS volunteer pilot; no Terraform files committed yet
- Date checked: 2026-06-28
- References:
  - https://developer.hashicorp.com/terraform/language/backend/s3
  - https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html
  - https://docs.aws.amazon.com/AmazonECS/latest/developerguide/task_execution_IAM_role.html

Verified fields and behaviors:

- Terraform S3 backend stores state in an S3 object at the configured bucket/key.
- Terraform recommends enabling S3 bucket versioning for state recovery.
- Current Terraform S3 backend supports S3 lockfiles through `use_lockfile`; DynamoDB-based locking is documented as deprecated for future removal.
- Terraform backend credentials and sensitive data should not be hardcoded into backend configuration or plan files.
- AWS IAM best practices include human federation with temporary credentials, workload IAM roles, MFA, least privilege, Access Analyzer, regular credential cleanup, and policy conditions.
- ECS task execution role is separate from task IAM role. The execution role lets ECS/Fargate pull images, publish logs, and resolve referenced secrets; application AWS API permissions belong in task roles.

paprnav mapping notes:

- Do not use `marketer-pipeline-agent` for paprnav Terraform work.
- Use a paprnav-specific bootstrap identity only long enough to establish state storage and deploy/runtime roles.
- Use a `paprnav-terraform-deploy` role for Terraform plan and later explicitly approved apply.
- Use separate ECS runtime roles: execution, backend task, worker task, and frontend task.
- Scope pilot resources with `Project=paprnav`, `Environment=pilot`, and `us-east-1` account/region guardrails.
- Store Terraform state in an encrypted, versioned S3 bucket with S3 lockfile support.
