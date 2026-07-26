## Closure Review — Layout-First OCR Checkpoint

### Remaining Medium findings

**1. `app/services/ingestion.py` — the header-only-region fix is a hardcoded fragment allowlist, not a structural fix; a differently-worded boilerplate header still produces a phantom entry.**
`is_ignorable_logbook_line` correctly suppresses the exact N3671L-style header text now covered by `test_header_only_multiline_region_does_not_create_entry`. But the guard is a literal string/prefix allowlist (`"description of inspections"`, `"entries must be endorsed"`, `"total time in service"`, `"today's"`, `"year:"`, etc.), not a semantic/structural signal (e.g., "no date + no known field label + this is the only region on the page"). I reproduced the original failure mode with different but equally boilerplate header wording:

```
"AIRFRAME LOG\nDescription of Work Performed\nCertified By"
```

This still produces one draft with `entry_date=None` and `description="AIRFRAME LOG\nDescription of Work Performed\nCertified By"`. It correctly lands as `needs_review` (good — it's not silently `verified`, because `date_was_extracted` is `False`), but it still creates a real `LogbookEntry` row with a header string as its "description" and consumes a review-queue slot for something that isn't an entry at all. So this is narrowly closed for the one known fixture and remains open for any other form layout/header wording — exactly the "failure-fixture closure remains" gap the status doc itself still tracks.

**2. Raw recognizer-response persistence has no size cap, redaction, or retention policy — a data-minimization/unbounded-storage concern, though not currently network-exposed.**
`OllamaGLMRegionRecognizer.recognize` stores the full raw model output verbatim in `metadata["raw_content"]`, which flows into `OCRTextSpan.relationships` (`JSON`, not `JSONB`, no length constraint) once per detected region, in addition to the already-parsed `text` field and a `content_sha256` hash. Concretely:
- No application-level size cap on `raw_content` (bounded only by `num_predict=8192` tokens per Ollama call, which is not a hard guarantee for all recognizer configurations/models).
- No truncation, redaction, or retention/purge policy — every region's raw model dump accumulates indefinitely as ingestion volume grows, duplicating whatever PII/maintenance content is on the page (names, cert numbers, tail numbers) a second time in the same row.
- D019 asks for a "raw result artifact reference and content hash for audit/replay" — the hash is present, but the implementation embeds the full raw payload directly rather than a pointer to an object-store artifact, which is a stronger interpretation of "reference" than the decision implies.
- Mitigating factor: I confirmed `serialize_span` in `app/api/routes/ingestion.py` does **not** include `relationships` in `OCRTextSpanResponse`, so this raw content is not currently returned to any authenticated client (owner or maintenance-shop role) — the exposure surface today is limited to direct DB/backup access, not the API. This is a real but currently contained gap, not an active leak.
- This pattern (storing a full raw provider payload in `relationships`) already exists for Mistral (`"raw_block": block`) and Textract, so it's consistent with existing precedent rather than a new architectural choice unique to this diff — but layout-first is the first provider to embed the complete recognized *text content* itself (not just structural block metadata) verbatim in that column.

### Closed findings (verified)

- **Pillow mandatory dependency breaking Python 3.9/base installs — closed.** `backend/requirements.txt` has no Pillow entry (`boto3`, `pypdf` only added); `Pillow>=12.1,<13` lives solely in the new, separately-installed `requirements-layout-ocr.txt`. I created a fresh Python 3.9.6 venv and ran `pip install -r requirements.txt` — it installs cleanly. `layout_first_ocr.py` only imports Pillow/PyMuPDF/httpx/glmocr lazily inside functions, so the module itself still imports fine without those optional deps.
- **Missing layout-first cost metadata — closed.** `process_upload`'s `metadata` now includes `estimated_unit_cost_usd_per_page` and `estimated_cost_usd`, matching the Mistral provider's contract and D019. Covered by `test_layout_first_provider_preserves_regions_and_separate_confidence`.
- **Multiline header-only regions becoming entries — closed for the known fixture only.** See residual Medium finding #1 above; the specific N3671L header pattern is now correctly filtered and tested.
- **`strip_date` magic-position heuristic — closed.** The function no longer uses a raw `match.start() <= 16` cutoff; it now requires the text *before* the matched date to be empty or exactly match a `Date[:=]?` label pattern (via `re.fullmatch`), tied to the actual `parse_date` result rather than an arbitrary column offset. I verified both directions concretely: a legitimate date preceded by a long label (`"Maintenance Performed By ABC Date: 2013-05-04..."`) is correctly left in place (not stripped/duplicated), and an AD-reference occurring early in the line (`"AD 11-10-09 x 2013-05-04"`) is correctly *not* stripped, matching the existing regression test. Residual note: `is_entry_anchor_line` still uses a separate magic-number heuristic (`date_appears_near_line_start`, cutoff 16) for a different purpose — deciding which lines can *anchor* an entry cluster — which was not the specific function named in the prior finding and is narrower in blast radius (affects clustering candidacy, not text content), but it's the same category of heuristic and worth tracking if entry-splitting quality regresses on new layouts.
- **Unvalidated polygon geometry — closed.** `validate_layout_region` now rejects polygons with fewer than three points and any coordinate outside `[0, 1]`, exercised by `test_layout_first_provider_rejects_invalid_polygon`. Narrow residual: polygon points are not cross-checked for consistency with the region's own bbox (e.g., a valid-in-range polygon that doesn't actually enclose the bbox would still pass) — low impact since the frontend doesn't render polygons yet.
- **Ambiguous PP-DocLayout confidence scale — closed.** `normalize_layout_confidence` now raises `ValueError` ("must use the documented 0-1 scale") for any value outside `[0, 1]` instead of silently guessing, verified by `test_glm_layout_score_requires_documented_zero_to_one_scale`. This converts the prior silent-misinterpretation risk into a loud, testable failure.

### Verification performed

- Full backend suite: `PYTHONPATH=. .venv/bin/pytest -q` → **57 passed** (Python 3.9.6, `.venv` with Pillow 11.3.0/boto3 installed).
- Targeted: `tests/test_layout_first_ocr.py tests/test_storage.py` → **17 passed**.
- Clean-venv install check: `pip install -r requirements.txt` on bare Python 3.9.6 → succeeds.
- Manual repros for the `strip_date` heuristic and the header-allowlist fixture, both shown above.
- Confirmed `OCRTextSpanResponse`/`serialize_span` omit `relationships`, so raw recognizer output isn't currently API-exposed.

No files were modified as part of this review.
