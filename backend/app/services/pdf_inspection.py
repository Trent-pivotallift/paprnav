from __future__ import annotations

from dataclasses import dataclass
from difflib import SequenceMatcher
from hashlib import sha256
from io import BytesIO
import re
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models.core import IngestionJob, IngestionPage, Upload
from app.services.page_images import attach_page_image
from app.services.storage import read_stored_file_bytes


INSPECTION_PROFILE = "pdf-inspection-v1"
CLASSIFICATION_PROFILE = "page-classification-v1"
NATIVE_TEXT_PROFILE = "native-text-reliability-v2"
EXTRACTION_PLAN_PROFILE = "provider-neutral-page-plan-v1"


@dataclass(frozen=True)
class PDFInspectionResult:
    document_bytes: bytes
    page_count: int
    metadata: dict[str, Any]


def inspect_and_prepare_upload(
    *,
    db: Session,
    settings: Settings,
    upload: Upload,
    job: IngestionJob,
) -> PDFInspectionResult | None:
    if upload.content_type != "application/pdf":
        job.document_inspection = {
            "profile": INSPECTION_PROFILE,
            "status": "not_applicable",
            "contentType": upload.content_type,
        }
        return None

    try:
        document_bytes = read_stored_file_bytes(
            settings=settings,
            storage_backend=upload.storage_backend,
            storage_key=upload.storage_key,
        )
        result = inspect_pdf_bytes(document_bytes, upload=upload)
    except Exception as exc:
        job.document_inspection = {
            "profile": INSPECTION_PROFILE,
            "status": "failed",
            "errorCode": "pdf_inspection_failed",
            "errorMessage": str(exc)[:1000],
        }
        return None

    job.document_inspection = result.metadata
    for page_number, inspected in enumerate(result.metadata["pages"], start=1):
        page = db.scalar(
            select(IngestionPage).where(
                IngestionPage.ingestion_job_id == job.id,
                IngestionPage.source_page_number == page_number,
            )
        )
        if page is None:
            page = IngestionPage(
                ingestion_job_id=job.id,
                upload_id=upload.id,
                source_page_number=page_number,
                current_page_order=page_number,
            )
            db.add(page)
            db.flush()
        page.rotation_degrees = inspected["declaredRotationDegrees"]
        page.inspection_status = "inspected"
        page.source_page_fingerprint = inspected["sourcePageFingerprint"]
        page.page_classification = inspected["classification"]
        page.native_text_evaluation = inspected["nativeText"]
        page.extraction_plan = inspected["extractionPlan"]
        page.stage_results = {
            "inspection": {
                "status": "complete",
                "attemptNumber": 1,
                "profile": INSPECTION_PROFILE,
            }
        }
        if page.canonical_image_sha256 is None:
            attach_page_image(settings=settings, upload=upload, page=page)
        if page.canonical_image_sha256 is None:
            page.inspection_status = "render_failed"
            page.stage_results = {
                **(page.stage_results or {}),
                "rendering": {
                    "status": "failed",
                    "attemptNumber": 1,
                    "errorCode": "canonical_render_failed",
                    "retryEligible": True,
                },
            }
        else:
            page.stage_results = {
                **(page.stage_results or {}),
                "rendering": {
                    "status": "complete",
                    "attemptNumber": 1,
                    "profile": page.render_profile,
                },
            }
            page.page_classification = enrich_classification_from_render(
                page.page_classification,
                page.render_metadata,
                declared_rotation=page.rotation_degrees,
            )
    return result


def inspect_pdf_bytes(document_bytes: bytes, *, upload: Upload | None = None) -> PDFInspectionResult:
    from pypdf import PdfReader

    reader = PdfReader(BytesIO(document_bytes), strict=False)
    if reader.is_encrypted:
        raise ValueError("Encrypted PDFs are not supported")
    if not reader.pages:
        raise ValueError("PDF contains no pages")

    pages: list[dict[str, Any]] = []
    for page_number, page in enumerate(reader.pages, start=1):
        native_text = evaluate_native_text(page)
        classification = classify_page(
            page_number=page_number,
            page_count=len(reader.pages),
            native_text=native_text,
        )
        pages.append(
            {
                "pageNumber": page_number,
                "declaredRotationDegrees": int(page.rotation or 0) % 360,
                "mediaBoxPoints": {
                    "width": float(page.mediabox.width),
                    "height": float(page.mediabox.height),
                },
                "sourcePageFingerprint": source_page_fingerprint(page),
                "classification": classification,
                "nativeText": native_text,
                "extractionPlan": {
                    "profile": EXTRACTION_PLAN_PROFILE,
                    "mode": "calibration",
                    "selectedProvider": "aws_textract",
                    "nativeTextMayBypassOCR": False,
                    "reason": "native_routing_gate_not_activated",
                },
            }
        )

    metadata = {
        "profile": INSPECTION_PROFILE,
        "status": "complete",
        "sourceSha256": sha256(document_bytes).hexdigest(),
        "sourceHashMatchesUpload": upload is None or sha256(document_bytes).hexdigest() == upload.sha256,
        "pageCount": len(reader.pages),
        "pdfHeader": document_bytes[:8].decode("latin-1", errors="replace"),
        "metadata": {str(key): str(value)[:500] for key, value in (reader.metadata or {}).items()},
        "pages": pages,
    }
    return PDFInspectionResult(document_bytes=document_bytes, page_count=len(reader.pages), metadata=metadata)


def source_page_fingerprint(page: Any) -> str:
    digest = sha256()
    digest.update(str(tuple(float(value) for value in page.mediabox)).encode())
    digest.update(str(tuple(float(value) for value in page.cropbox)).encode())
    digest.update(str(int(page.rotation or 0) % 360).encode())
    contents = page.get_contents()
    if contents is not None:
        digest.update(contents.get_data())
    return digest.hexdigest()


def evaluate_native_text(page: Any) -> dict[str, Any]:
    samples: list[tuple[str, float, float, float]] = []
    image_placements: list[float] = []
    page_area = max(float(page.mediabox.width) * float(page.mediabox.height), 1.0)

    def visitor(text: str, _cm: Any, tm: Any, _font: Any, font_size: Any) -> None:
        if text:
            samples.append((text, float(tm[4]), float(tm[5]), float(font_size or 0)))

    def operand_visitor(operator: bytes, _operands: Any, cm: Any, _tm: Any) -> None:
        if operator == b"Do" and len(cm) >= 4:
            displayed_area = abs(float(cm[0]) * float(cm[3]) - float(cm[1]) * float(cm[2]))
            image_placements.append(min(displayed_area / page_area, 1.0))

    try:
        text = page.extract_text(
            visitor_text=visitor,
            visitor_operand_before=operand_visitor,
        ) or ""
        extraction_error = None
    except Exception as exc:
        text = ""
        extraction_error = str(exc)[:500]

    meaningful = [character for character in text if not character.isspace()]
    valid = [
        character
        for character in meaningful
        if character.isprintable() and character != "\ufffd"
    ]
    valid_ratio = len(valid) / len(meaningful) if meaningful else 0.0
    width = max(float(page.mediabox.width), 1.0)
    height = max(float(page.mediabox.height), 1.0)
    positioned = [
        sample
        for sample in samples
        if 0.0 <= sample[1] <= width and 0.0 <= sample[2] <= height
    ]
    positioned_ratio = len(positioned) / len(samples) if samples else 0.0
    normalized_lines = [line.strip() for line in text.splitlines() if line.strip()]
    duplicate_ratio = (
        1.0 - (len(set(normalized_lines)) / len(normalized_lines))
        if normalized_lines
        else 0.0
    )
    plausible_font_samples = [
        sample for sample in samples if 4.0 <= sample[3] <= 72.0
    ]
    plausible_font_ratio = (
        len(plausible_font_samples) / len(samples) if samples else 0.0
    )
    word_count = len(re.findall(r"\b[\w&.-]+\b", text))
    image_coverage = min(sum(image_placements), 1.0)
    try:
        layout_text = page.extract_text(extraction_mode="layout") or ""
        extractor_agreement = SequenceMatcher(
            None,
            normalize_native_text(text),
            normalize_native_text(layout_text),
        ).ratio()
    except Exception:
        layout_text = ""
        extractor_agreement = 0.0
    has_meaningful_text = len(meaningful) >= 50 and word_count >= 8
    reliable_candidate = (
        extraction_error is None
        and has_meaningful_text
        and valid_ratio >= 0.995
        and positioned_ratio >= 0.98
        and plausible_font_ratio >= 0.98
        and duplicate_ratio <= 0.05
        and extractor_agreement >= 0.98
        and image_coverage <= 0.25
    )
    reasons: list[str] = []
    if not has_meaningful_text:
        reasons.append("insufficient_meaningful_text")
    if valid_ratio < 0.995:
        reasons.append("invalid_or_replacement_glyphs")
    if positioned_ratio < 0.98:
        reasons.append("text_positioning_unreliable")
    if plausible_font_ratio < 0.98:
        reasons.append("font_geometry_unreliable")
    if duplicate_ratio > 0.05:
        reasons.append("duplicate_text_lines")
    if extractor_agreement < 0.98:
        reasons.append("extractor_modes_disagree")
    if image_coverage > 0.25:
        reasons.append("image_dominant_or_mixed_page")
    if extraction_error:
        reasons.append("extraction_error")

    return {
        "profile": NATIVE_TEXT_PROFILE,
        "mode": "calibration",
        "characterCount": len(text),
        "meaningfulCharacterCount": len(meaningful),
        "wordCount": word_count,
        "validGlyphRatio": round(valid_ratio, 6),
        "positionedSampleCount": len(samples),
        "positionedSampleRatio": round(positioned_ratio, 6),
        "plausibleFontRatio": round(plausible_font_ratio, 6),
        "duplicateLineRatio": round(duplicate_ratio, 6),
        "extractorAgreement": round(extractor_agreement, 6),
        "imagePlacementCount": len(image_placements),
        "estimatedImageCoverage": round(image_coverage, 6),
        "reliableCandidate": reliable_candidate,
        "reasons": reasons,
        "extractionError": extraction_error,
        "textSha256": sha256(text.encode("utf-8")).hexdigest(),
        "textPreview": text[:500],
    }


def normalize_native_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def classify_page(
    *,
    page_number: int,
    page_count: int,
    native_text: dict[str, Any],
) -> dict[str, Any]:
    text = native_text["textPreview"]
    meaningful_count = native_text["meaningfulCharacterCount"]
    reliable_native = native_text["reliableCandidate"]
    if meaningful_count == 0:
        routing_class = "scanned"
    elif reliable_native:
        routing_class = "native_text"
    else:
        routing_class = "mixed"

    lower_text = text.lower()
    date_like = bool(re.search(r"\b(?:19|20)\d{2}\b|\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b", lower_text))
    maintenance_like = any(
        token in lower_text
        for token in ("inspection", "aircraft", "engine", "tach", "hobbs", "maintenance", "repaired")
    )
    if page_number == 1 and meaningful_count < 200 and not date_like:
        document_role = "cover"
    elif date_like or maintenance_like:
        document_role = "logbook_entry"
    elif page_number > 1 and meaningful_count > 0:
        document_role = "continuation"
    elif meaningful_count == 0:
        document_role = "unknown"
    else:
        document_role = "attachment"

    attributes: list[str] = []
    attributes.append("typed" if reliable_native else "text_mode_uncertain")
    attributes.append("sparse" if meaningful_count < 250 else "dense")
    attributes.append("continuation_sensitive" if page_count > 1 else "single_page")
    attributes.append("layout_uncertain")

    return {
        "profile": CLASSIFICATION_PROFILE,
        "routingClass": routing_class,
        "documentRole": document_role,
        "attributes": attributes,
        "confidence": 0.80 if reliable_native else 0.45,
        "requiresRecognitionConfirmation": True,
    }


def enrich_classification_from_render(
    classification: dict[str, Any] | None,
    render_metadata: dict[str, Any] | None,
    *,
    declared_rotation: float | None,
) -> dict[str, Any]:
    enriched = dict(classification or {})
    attributes = list(enriched.get("attributes") or [])
    metrics = (render_metadata or {}).get("visualMetrics") or {}
    reliably_native = enriched.get("routingClass") == "native_text"
    aspect_ratio = metrics.get("aspectRatio")
    contrast = metrics.get("luminanceStdDev")

    attributes = [
        attribute
        for attribute in attributes
        if attribute not in {"layout_uncertain", "sparse", "dense"}
    ]
    if isinstance(aspect_ratio, (int, float)):
        if aspect_ratio >= 2.2:
            attributes.extend(["side_by_side", "landscape"])
        elif aspect_ratio <= 0.8:
            attributes.append("portrait")
            if not reliably_native:
                attributes.append("orientation_unverified")
        elif aspect_ratio >= 1.5:
            attributes.extend(["wide_layout", "orientation_unverified"])
        else:
            attributes.append("layout_uncertain")
    else:
        attributes.append("layout_uncertain")
    if declared_rotation:
        attributes.append("rotated")
    if (
        not reliably_native
        and isinstance(contrast, (int, float))
        and contrast < 25
    ):
        attributes.append("faint")

    enriched["attributes"] = list(dict.fromkeys(attributes))
    enriched["visualClassification"] = {
        "aspectRatio": aspect_ratio,
        "luminanceStdDev": contrast,
        "orientationPolicy": (
            "declared_rotation_applied"
            if declared_rotation
            else "visual_orientation_not_automatically_changed"
        ),
    }
    return enriched
