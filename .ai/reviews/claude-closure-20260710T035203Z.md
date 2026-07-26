All four findings are addressed in the current working tree. No remaining blocking findings.

## Remaining blocking findings
None.

## Verification notes

**F1 — Textract sync PDF/large-file guard — Addressed**
- `TextractOCRProvider.process_upload` calls `_validate_sync_document` before invoking Textract (`ocr_provider.py:213`).
- PDF is rejected by both content-type and extension (`ocr_provider.py:228-229`), with a clear "use async Textract" message.
- Local files are size-checked against `sync_max_document_bytes = 10 MB` (`ocr_provider.py:185`, `231-234`).
- Tests confirm PDF rejection (`test_ocr_provider.py:85-98`, `match="does not support PDF"`).
- Minor (non-blocking) gap: the 10 MB size guard only runs for non-S3 backends (`if storage_backend != "s3"`). An S3-backed synchronous `detect_document_text` on an oversized image would still be sent to Textract and fail at the API rather than being caught locally. Acceptable for now since the multipage/large risk (PDF) is unconditionally blocked, but worth a follow-up when S3 sync OCR is exercised.

**F3 — Misleading S3 object-tag billing docs — Addressed**
- `backend/README.md:139`, `AWS_DEPLOYMENT_STATUS.md:132-135`, `PROVIDER_REFERENCES.md:31,41`, and `AWS_PILOT_TERRAFORM_PLAN.md:171-172` now consistently state S3 object tags are paprnav metadata/reconciliation only, explicitly **not** a per-customer AWS Cost Explorer dimension, and that customer OCR chargeback is derived from DB records (`OCRRun.billable_page_count`, billable account/aircraft tags), not tag-based cost attribution.

**F4 — Unconditional iam:PassRole — Addressed**
- `PassPaprnNavRuntimeRolesToExpectedServices` (`paprnav-terraform-deploy-policy.json:245-260`) now scopes `iam:PassRole` to `Resource: arn:aws:iam::527257972989:role/paprnav-*` and gates it with `iam:PassedToService` restricted to `ecs-tasks`, `ecs`, `application-autoscaling`, and `rds`. No wildcard PassRole remains.

**F5 — mdb-export table-name argument hardening — Addressed**
- `export_access_table` (`drs_bulk_import.py:256-268`) invokes `[MDB_EXPORT, str(accdb_path), "--", table_name]` — the `--` sentinel prevents a maliciously named table from being parsed as an option flag.
- Invocation uses an argv list with no `shell=True`, and `list_access_tables`/`export_access_table` both bound execution with timeouts and catch `OSError`/`CalledProcessError`/`TimeoutExpired`.
