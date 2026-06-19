# paprnav Provider References

Last updated: 2026-06-18

Use this file whenever implementation depends on an external provider, API, SDK, CLI, file format, or output shape. Check current official documentation first, then record the mapping here before coding or marking the task complete.

## Reference-First Rule

Do not design provider contracts from trained memory. For each provider-backed task:

- Check current official documentation or another primary source.
- Record the URL and date checked.
- List the fields and behaviors the implementation depends on.
- Map provider-specific output to paprnav's provider-neutral schema.
- Note confidence scales, geometry units, pagination, async behavior, IDs, raw artifacts, and replay/audit implications.

## OCR Providers

### AWS Textract

- Status: target production OCR provider
- Date checked: 2026-06-18
- References:
  - https://docs.aws.amazon.com/textract/latest/APIReference/API_Block.html
  - https://docs.aws.amazon.com/textract/latest/APIReference/API_Geometry.html

Verified fields and behaviors:

- OCR output is represented as `Block` objects.
- Relevant `BlockType` values include `PAGE`, `LINE`, and `WORD`; analysis operations may also emit key-value, table, selection, signature, query, and layout block types.
- `Text` contains recognized text for text-bearing blocks.
- `Confidence` is a float from `0` to `100`.
- `Geometry` includes `BoundingBox`, `Polygon`, and optional `RotationAngle`.
- `Page` identifies the detected page; values greater than 1 are returned for multipage PDF/TIFF documents.
- `Relationships` connect blocks, such as line-to-word child relationships.
- Provider block IDs are operation-local, not durable global IDs.

paprnav mapping notes:

- Store confidence on a `0-100` scale to avoid lossy Textract conversion.
- Store bounding boxes with explicit units; Textract boxes should map to ratio units.
- Preserve optional polygon and rotation data when present.
- Preserve provider block IDs and relationships for audit/replay, but do not use them as stable domain IDs.
- Fixture OCR output should include page, line, and word examples with mixed confidence values.

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

## GitHub Actions

- Status: CI workflow added for frontend lint/build and backend tests
- Date checked: not yet recorded for current workflow
- References: TBD if workflow syntax or permissions become nontrivial

Required before adding deployment or privileged workflow steps:

- Current GitHub Actions workflow syntax docs.
- Current permissions and OIDC-to-AWS docs if AWS deploy is added.
- Cache behavior and security guidance for pull requests.
