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

- Status: planned provider/API for T046
- Date checked: not yet checked for implementation
- References: TBD before T046 starts

Required before implementation:

- Current Federal Register API endpoint documentation.
- Query parameters for agency, document type, publication dates, search terms, pagination, and result limits.
- Response fields for document number, title, abstract/body HTML, PDF/HTML URLs, publication date, effective date if available, CFR references, agencies, and raw citation metadata.
- Rate limit or polite polling guidance if documented.

## AD Extraction Providers

- Status: planned hybrid deterministic plus provider-backed extraction
- Date checked: not yet checked for implementation
- References: TBD before T049 starts

Required before implementation:

- Current provider API documentation for request/response shape.
- Structured output/schema validation support.
- Model/provider version metadata.
- Token/input size limits.
- Confidence or refusal/uncertainty signal behavior.
- Citation/source grounding support.
- Retry/idempotency and content-hash strategy.

## GitHub Actions

- Status: CI workflow added for frontend lint/build and backend tests
- Date checked: not yet recorded for current workflow
- References: TBD if workflow syntax or permissions become nontrivial

Required before adding deployment or privileged workflow steps:

- Current GitHub Actions workflow syntax docs.
- Current permissions and OIDC-to-AWS docs if AWS deploy is added.
- Cache behavior and security guidance for pull requests.
