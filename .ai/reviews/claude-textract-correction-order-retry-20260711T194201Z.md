Only one construction site, and it's the one that sets `correction_order` properly. Review complete.

## Blocking findings

None. The changes are correct and safe.

## Verification notes

1. **Textract sync bucket usage — correct.** `TextractOCRProvider._document_reference` builds `S3Object` from `self.upload_s3_bucket`, which defaults from `settings.s3_upload_bucket` (`PAPRNAV_S3_UPLOAD_BUCKET`), not `settings.textract_s3_bucket`. This matches how uploads are actually stored/downloaded (`storage.py` / `uploads.py` both key off `s3_upload_bucket`), so Textract will read the same object the upload pipeline wrote. `test_textract_provider_uses_upload_bucket_for_s3_backed_uploads` explicitly asserts the upload bucket is used even when `PAPRNAV_TEXTRACT_S3_BUCKET` is also set. Note `textract_s3_bucket`/`textract_s3_prefix` settings are currently unused by the provider (dead config for now) — not a bug, just worth knowing it's reserved for a future async path.

2. **`correction_order` determinism + uniqueness — correct.** Model adds `correction_order` (default 1) plus `UniqueConstraint("ocr_text_span_id", "correction_order")`. Route logic (`create_ordered_ocr_correction`) computes `max(correction_order)+1` per span inside a `db.begin_nested()` savepoint and retries up to `MAX_CORRECTION_ORDER_ATTEMPTS` (3) on `IntegrityError`, then returns 409 if still colliding — a reasonable optimistic-concurrency pattern for races across sessions. Relationship ordering (`order_by="OCRCorrection.correction_order"`) is also updated so `span.corrections` is deterministic.

3. **Migration — safe.** Adds nullable column, backfills via `ROW_NUMBER() OVER (PARTITION BY ocr_text_span_id ORDER BY created_at, id)` (tie-break on `id` guards against equal timestamps), then sets `NOT NULL`, then adds index + unique constraint, in a sequence that won't fail on existing data since the backfill guarantees no duplicate `(span_id, order)` pairs. Downgrade cleanly reverses (constraint → index → column). Revision chain (`20260708_0008` → `20260710_0009`) is intact.

4. **Test coverage — mostly good, one gap.** `test_ocr_provider.py` covers local vs. S3 document routing, PDF rejection, provider selection, and block→span mapping. `test_mvp_endpoints.py` covers sequential corrections on the same span producing `correctionOrder` 1 then 2, and that evidence/logbook entries pick up the latest correction. However, there is no test exercising the actual `IntegrityError` retry/409 path (e.g., simulating a collision via a pre-inserted row or monkeypatched flush) — only the non-colliding sequential case is verified. This is a minor coverage gap, not a correctness issue, since the logic itself is straightforward and passes existing tests.

All targeted tests (`test_ocr_provider.py`, `test_mvp_endpoints.py`) pass locally (15/15).
