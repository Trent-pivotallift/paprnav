from __future__ import annotations

from dataclasses import replace
from hashlib import sha256
import os
import time
from typing import Any

from app.services.ocr_provider import OCRPageResult, OCRProvider, OCRProviderResult, OCRSpanResult
from app.services.page_images import png_dimensions


class GoogleDocumentAIOCRProvider(OCRProvider):
    """Evaluation-only adapter for Google Enterprise Document OCR."""

    provider_name = "google_document_ai"
    provider_version = "enterprise-document-ocr"
    base_page_price_usd = 0.0015
    addon_page_price_usd = 0.006

    def __init__(
        self,
        *,
        project_id: str | None = None,
        location: str | None = None,
        processor_id: str | None = None,
        processor_version: str | None = None,
        client: Any | None = None,
        enable_image_quality_scores: bool = True,
        compute_style_info: bool = True,
    ) -> None:
        self.project_id = project_id or os.getenv("GOOGLE_CLOUD_PROJECT", "")
        self.location = location or os.getenv("GOOGLE_DOCUMENT_AI_LOCATION", "us")
        self.processor_id = processor_id or os.getenv("GOOGLE_DOCUMENT_AI_PROCESSOR_ID", "")
        self.processor_version = processor_version or os.getenv("GOOGLE_DOCUMENT_AI_PROCESSOR_VERSION")
        self.client = client
        self.enable_image_quality_scores = enable_image_quality_scores
        self.compute_style_info = compute_style_info
        version = self.processor_version or "default"
        self.configuration_hash = (
            f"google-document-ai:{self.location}:{self.processor_id}:{version}:"
            f"quality={int(enable_image_quality_scores)}:style={int(compute_style_info)}"
        )

    def process_upload(self, **_: Any) -> OCRProviderResult:
        raise RuntimeError(
            "Google Document AI is evaluation-only; process canonical pages "
            "with process_canonical_page()."
        )

    def process_canonical_page(
        self,
        *,
        png_bytes: bytes,
        source_page_number: int,
        labels: dict[str, str] | None = None,
    ) -> OCRProviderResult:
        if not self.project_id or not self.processor_id:
            raise ValueError(
                "GOOGLE_CLOUD_PROJECT and GOOGLE_DOCUMENT_AI_PROCESSOR_ID are required"
            )
        dimensions = png_dimensions(png_bytes)
        if dimensions is None:
            raise ValueError("Google evaluation requires a canonical PNG page")

        documentai = self._documentai()
        client = self.client or documentai.DocumentProcessorServiceClient(
            client_options={"api_endpoint": f"{self.location}-documentai.googleapis.com"}
        )
        if self.processor_version:
            name = client.processor_version_path(
                self.project_id, self.location, self.processor_id, self.processor_version
            )
        else:
            name = client.processor_path(self.project_id, self.location, self.processor_id)

        request = documentai.ProcessRequest(
            name=name,
            raw_document=documentai.RawDocument(content=png_bytes, mime_type="image/png"),
            skip_human_review=True,
            labels=labels or {},
            process_options=documentai.ProcessOptions(
                ocr_config=documentai.OcrConfig(
                    enable_image_quality_scores=self.enable_image_quality_scores,
                    compute_style_info=self.compute_style_info,
                )
            ),
        )
        started = time.monotonic()
        response = client.process_document(request=request)
        result = self.result_from_document(
            response.document,
            source_page_number=source_page_number,
            canonical_width=dimensions[0],
            canonical_height=dimensions[1],
        )
        addon_enabled = self.enable_image_quality_scores or self.compute_style_info
        rate = self.base_page_price_usd + (self.addon_page_price_usd if addon_enabled else 0.0)
        return replace(
            result,
            metadata={
                **result.metadata,
                "provider_channel": "google_cloud_api",
                "provider_mode": "evaluation_only",
                "third_party_processing": True,
                "processing_seconds": round(time.monotonic() - started, 6),
                "pricing_unit": "page",
                "pricing_rate_usd": rate,
                "estimated_unit_cost_usd_per_page": rate,
                "estimated_cost_usd": rate,
                "google_project_id": self.project_id,
                "google_location": self.location,
                "google_processor_id": self.processor_id,
                "google_processor_version": self.processor_version,
                "request_labels": labels or {},
                "canonical_sha256": sha256(png_bytes).hexdigest(),
                "image_quality_scores_enabled": self.enable_image_quality_scores,
                "style_info_enabled": self.compute_style_info,
            },
        )

    def result_from_document(
        self,
        document: Any,
        *,
        source_page_number: int,
        canonical_width: int,
        canonical_height: int,
    ) -> OCRProviderResult:
        pages = list(document.pages or [])
        if len(pages) != 1:
            raise ValueError(
                f"Expected one Google OCR page for canonical input, received {len(pages)}"
            )
        page = pages[0]
        spans: list[OCRSpanResult] = []
        reading_order = 1
        for span_type, items in (("LINE", page.lines or []), ("WORD", page.tokens or [])):
            for index, item in enumerate(items, start=1):
                layout = item.layout
                text = anchored_text(document.text or "", layout.text_anchor).strip()
                if not text:
                    continue
                bbox, polygon = layout_geometry(
                    layout.bounding_poly, width=canonical_width, height=canonical_height
                )
                spans.append(
                    OCRSpanResult(
                        provider_block_id=f"google-p{source_page_number}-{span_type.lower()}-{index}",
                        span_type=span_type,
                        text=text,
                        confidence=confidence_0_100(layout.confidence),
                        bbox_left=bbox["left"],
                        bbox_top=bbox["top"],
                        bbox_width=bbox["width"],
                        bbox_height=bbox["height"],
                        bbox_units="ratio",
                        reading_order=reading_order,
                        polygon=polygon,
                        relationships=[{
                            "provider": self.provider_name,
                            "detectedLanguages": [{
                                "languageCode": language.language_code,
                                "confidence": confidence_0_100(language.confidence),
                            } for language in (item.detected_languages or [])],
                        }],
                    )
                )
                reading_order += 1

        line_confidences = [
            span.confidence for span in spans
            if span.span_type == "LINE" and span.confidence is not None
        ]
        quality = getattr(page, "image_quality_scores", None)
        quality_metadata = None
        if quality:
            quality_metadata = {
                "qualityScore": float(quality.quality_score),
                "detectedDefects": [{
                    "type": defect.type_,
                    "confidence": float(defect.confidence),
                } for defect in (quality.detected_defects or [])],
            }
        provider_version = (
            getattr(document, "processor_version", None)
            or self.processor_version
            or self.provider_version
        )
        page_result = OCRPageResult(
            source_page_number=source_page_number,
            page_label=f"Google Document AI source page {source_page_number}",
            width_px=canonical_width,
            height_px=canonical_height,
            rotation_degrees=0,
            extraction_confidence=(
                sum(line_confidences) / len(line_confidences) if line_confidences else None
            ),
            spans=spans,
            source_provider_name=self.provider_name,
            source_provider_version=str(provider_version),
        )
        return OCRProviderResult(
            provider_name=self.provider_name,
            provider_version=str(provider_version),
            configuration_hash=self.configuration_hash,
            pages=[page_result],
            billable_page_count=1,
            metadata={
                "document_text_sha256": sha256((document.text or "").encode("utf-8")).hexdigest(),
                "document_text_character_count": len(document.text or ""),
                "image_quality": quality_metadata,
            },
        )

    @staticmethod
    def _documentai() -> Any:
        try:
            from google.cloud import documentai_v1 as documentai
        except ImportError as exc:
            raise RuntimeError(
                "Install backend/requirements-google-ocr.txt in an isolated "
                "evaluation environment"
            ) from exc
        return documentai


def anchored_text(document_text: str, text_anchor: Any) -> str:
    return "".join(
        document_text[int(segment.start_index or 0):int(segment.end_index or 0)]
        for segment in (text_anchor.text_segments or [])
    )


def confidence_0_100(value: Any) -> float | None:
    return None if value is None else round(float(value) * 100.0, 6)


def layout_geometry(
    bounding_poly: Any, *, width: int, height: int
) -> tuple[dict[str, float], list[list[float]]]:
    normalized = list(bounding_poly.normalized_vertices or [])
    if normalized:
        points = [[float(v.x or 0.0), float(v.y or 0.0)] for v in normalized]
    else:
        points = [
            [float(v.x or 0.0) / max(width, 1), float(v.y or 0.0) / max(height, 1)]
            for v in (bounding_poly.vertices or [])
        ]
    if not points:
        return {"left": 0.0, "top": 0.0, "width": 0.0, "height": 0.0}, []
    xs = [point[0] for point in points]
    ys = [point[1] for point in points]
    left, right = min(xs), max(xs)
    top, bottom = min(ys), max(ys)
    return {
        "left": left,
        "top": top,
        "width": max(right - left, 0.0),
        "height": max(bottom - top, 0.0),
    }, points
