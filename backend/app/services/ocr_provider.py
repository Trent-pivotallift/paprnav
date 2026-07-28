from __future__ import annotations

import base64
from io import BytesIO
from dataclasses import dataclass, field, replace
from pathlib import Path
import time
from typing import Any, Optional

from app.core.config import get_settings


TEXTRACT_ANALYSIS_SPAN_BLOCK_TYPES = {
    "LINE",
    "WORD",
    "TABLE",
    "CELL",
    "MERGED_CELL",
    "TABLE_TITLE",
    "TABLE_FOOTER",
    "SIGNATURE",
    "LAYOUT_TEXT",
    "LAYOUT_TITLE",
    "LAYOUT_HEADER",
    "LAYOUT_FOOTER",
    "LAYOUT_SECTION_HEADER",
    "LAYOUT_PAGE_NUMBER",
    "LAYOUT_LIST",
    "LAYOUT_FIGURE",
    "LAYOUT_TABLE",
    "LAYOUT_KEY_VALUE",
}


@dataclass(frozen=True)
class OCRSpanResult:
    provider_block_id: str
    span_type: str
    text: str
    confidence: Optional[float]
    bbox_left: float
    bbox_top: float
    bbox_width: float
    bbox_height: float
    bbox_units: str
    reading_order: int
    polygon: list[list[float]] = field(default_factory=list)
    relationships: list[dict] = field(default_factory=list)


@dataclass(frozen=True)
class OCRPageResult:
    source_page_number: int
    page_label: str
    width_px: int
    height_px: int
    rotation_degrees: float
    extraction_confidence: Optional[float]
    spans: list[OCRSpanResult]
    source_provider_name: Optional[str] = None
    source_provider_version: Optional[str] = None


@dataclass(frozen=True)
class OCRProviderResult:
    provider_name: str
    provider_version: str
    configuration_hash: str
    pages: list[OCRPageResult]
    billable_page_count: Optional[int] = None
    metadata: dict[str, Any] = field(default_factory=dict)


class OCRProvider:
    provider_name: str
    provider_version: str
    configuration_hash: str

    def process_upload(
        self,
        *,
        original_filename: str,
        content_type: str,
        storage_backend: Optional[str] = None,
        storage_key: Optional[str] = None,
    ) -> OCRProviderResult:
        raise NotImplementedError


class DeterministicFixtureOCRProvider(OCRProvider):
    provider_name = "deterministic_fixture"
    provider_version = "0.1.0"
    configuration_hash = "fixture-logbook-v1"

    def process_upload(
        self,
        *,
        original_filename: str,
        content_type: str,
        storage_backend: Optional[str] = None,
        storage_key: Optional[str] = None,
    ) -> OCRProviderResult:
        page_count = 2 if content_type == "application/pdf" else 1
        pages = [self._annual_page(1)]
        if page_count > 1:
            pages.append(self._oil_change_page(2))
        return OCRProviderResult(
            provider_name=self.provider_name,
            provider_version=self.provider_version,
            configuration_hash=self.configuration_hash,
            pages=pages,
            billable_page_count=page_count,
            metadata={
                "provider_mode": "fixture",
                "provider_channel": "local_test",
                "third_party_processing": False,
                "processing_seconds": 0.0,
                "pricing_unit": "page",
                "pricing_rate_usd": 0.0,
                "estimated_cost_usd": 0.0,
            },
        )

    def _annual_page(self, page_number: int) -> OCRPageResult:
        return OCRPageResult(
            source_page_number=page_number,
            page_label="Airframe page 1",
            width_px=2550,
            height_px=3300,
            rotation_degrees=0,
            extraction_confidence=96.0,
            spans=[
                OCRSpanResult(
                    provider_block_id="fixture-p1-line-1",
                    span_type="LINE",
                    text="2026-01-15 Annual inspection completed in accordance with 14 CFR Part 43 Appendix D.",
                    confidence=94.0,
                    bbox_left=0.08,
                    bbox_top=0.12,
                    bbox_width=0.84,
                    bbox_height=0.04,
                    bbox_units="ratio",
                    reading_order=1,
                ),
                OCRSpanResult(
                    provider_block_id="fixture-p1-line-2",
                    span_type="LINE",
                    text="Performer: A. Mechanic A&P IA",
                    confidence=62.0,
                    bbox_left=0.08,
                    bbox_top=0.18,
                    bbox_width=0.48,
                    bbox_height=0.04,
                    bbox_units="ratio",
                    reading_order=2,
                ),
                OCRSpanResult(
                    provider_block_id="fixture-p1-line-3",
                    span_type="LINE",
                    text="Tach: 1022.4 Hobbs: 1188.2 Total: 3201.7",
                    confidence=88.0,
                    bbox_left=0.08,
                    bbox_top=0.24,
                    bbox_width=0.58,
                    bbox_height=0.04,
                    bbox_units="ratio",
                    reading_order=3,
                ),
            ],
        )

    def _oil_change_page(self, page_number: int) -> OCRPageResult:
        return OCRPageResult(
            source_page_number=page_number,
            page_label="Engine page 1",
            width_px=2550,
            height_px=3300,
            rotation_degrees=0,
            extraction_confidence=91.0,
            spans=[
                OCRSpanResult(
                    provider_block_id="fixture-p2-line-1",
                    span_type="LINE",
                    text="2026-02-12 Changed engine oil and filter; inspected screen with no defects noted.",
                    confidence=93.0,
                    bbox_left=0.08,
                    bbox_top=0.12,
                    bbox_width=0.82,
                    bbox_height=0.04,
                    bbox_units="ratio",
                    reading_order=1,
                ),
                OCRSpanResult(
                    provider_block_id="fixture-p2-line-2",
                    span_type="LINE",
                    text="Performer: M. Mechanic A&P",
                    confidence=82.0,
                    bbox_left=0.08,
                    bbox_top=0.18,
                    bbox_width=0.42,
                    bbox_height=0.04,
                    bbox_units="ratio",
                    reading_order=2,
                ),
                OCRSpanResult(
                    provider_block_id="fixture-p2-line-3",
                    span_type="LINE",
                    text="Tach: 1035.8",
                    confidence=58.0,
                    bbox_left=0.08,
                    bbox_top=0.24,
                    bbox_width=0.24,
                    bbox_height=0.04,
                    bbox_units="ratio",
                    reading_order=3,
                ),
            ],
        )


class TextractOCRProvider(OCRProvider):
    provider_name = "aws_textract"
    provider_version = "detect_document_text_v1"
    configuration_hash = "textract-detect-document-text-v1"
    sync_max_document_bytes = 10 * 1024 * 1024

    def __init__(
        self,
        *,
        client: Optional[Any] = None,
        s3_client: Optional[Any] = None,
        storage_root: Optional[str] = None,
        upload_s3_bucket: Optional[str] = None,
        s3_prefix: Optional[str] = None,
        region_name: Optional[str] = None,
    ) -> None:
        settings = get_settings()
        self.client = client
        self.s3_client = s3_client
        self.storage_root = storage_root or settings.local_storage_path
        self.upload_s3_bucket = upload_s3_bucket or settings.s3_upload_bucket
        self.s3_prefix = (s3_prefix if s3_prefix is not None else settings.textract_s3_prefix).strip("/")
        self.region_name = region_name or settings.aws_region
        self.api_mode = settings.textract_api_mode
        self.analysis_feature_types = settings.textract_analysis_feature_types
        self.async_poll_seconds = settings.textract_async_poll_seconds
        self.async_timeout_seconds = settings.textract_async_timeout_seconds
        self.estimated_unit_cost_usd_per_page = (
            settings.textract_estimated_unit_cost_usd_per_page
        )
        self.ocr_max_pdf_pages = settings.ocr_max_pdf_pages
        if self.api_mode == "async":
            self.provider_version = "start_document_text_detection_v1"
            self.configuration_hash = "textract-start-document-text-detection-v1"
        elif self.api_mode == "analysis_async":
            self.provider_version = "start_document_analysis_v1"
            features_hash = "-".join(sorted(self.analysis_feature_types))
            self.configuration_hash = f"textract-start-document-analysis-v1:{features_hash}"

    def process_upload(
        self,
        *,
        original_filename: str,
        content_type: str,
        storage_backend: Optional[str] = None,
        storage_key: Optional[str] = None,
    ) -> OCRProviderResult:
        if not storage_key:
            raise ValueError("Textract OCR requires an upload storage key")
        started = time.monotonic()
        if self.api_mode == "analysis_async":
            result = self._process_upload_analysis_async(
                original_filename=original_filename,
                content_type=content_type,
                storage_backend=storage_backend,
                storage_key=storage_key,
            )
        elif self.api_mode == "async":
            result = self._process_upload_async(
                original_filename=original_filename,
                content_type=content_type,
                storage_backend=storage_backend,
                storage_key=storage_key,
            )
        else:
            self._validate_sync_document(
                original_filename=original_filename,
                content_type=content_type,
                storage_backend=storage_backend,
                storage_key=storage_key,
            )

            client = self.client or self._create_client()
            document = self._document_reference(
                storage_backend=storage_backend,
                storage_key=storage_key,
            )
            response = client.detect_document_text(Document=document)
            result = self.result_from_response(response)
        return self._with_usage_metadata(
            result,
            processing_seconds=time.monotonic() - started,
        )

    def _with_usage_metadata(
        self,
        result: OCRProviderResult,
        *,
        processing_seconds: float,
    ) -> OCRProviderResult:
        page_count = (
            result.billable_page_count
            if result.billable_page_count is not None
            else len(result.pages)
        )
        estimated_cost = round(
            page_count * self.estimated_unit_cost_usd_per_page,
            6,
        )
        return replace(
            result,
            billable_page_count=page_count,
            metadata={
                **result.metadata,
                "provider_channel": "aws",
                "provider_mode": self.api_mode,
                "third_party_processing": False,
                "processing_seconds": round(processing_seconds, 6),
                "pricing_unit": "page",
                "pricing_rate_usd": self.estimated_unit_cost_usd_per_page,
                "estimated_unit_cost_usd_per_page": (
                    self.estimated_unit_cost_usd_per_page
                ),
                "estimated_cost_usd": estimated_cost,
            },
        )

    def _process_upload_async(
        self,
        *,
        original_filename: str,
        content_type: str,
        storage_backend: Optional[str],
        storage_key: str,
    ) -> OCRProviderResult:
        if storage_backend != "s3":
            raise ValueError("Async Textract OCR requires an S3-backed upload")
        if not self.upload_s3_bucket:
            raise ValueError("PAPRNAV_S3_UPLOAD_BUCKET is required for async Textract OCR")
        self._validate_async_pdf_guardrail(original_filename=original_filename, content_type=content_type, storage_key=storage_key)

        client = self.client or self._create_client()
        response = client.start_document_text_detection(
            DocumentLocation={
                "S3Object": {
                    "Bucket": self.upload_s3_bucket,
                    "Name": storage_key,
                }
            }
        )
        job_id = response["JobId"]
        return self._wait_for_async_result(client, job_id=job_id)

    def _process_upload_analysis_async(
        self,
        *,
        original_filename: str,
        content_type: str,
        storage_backend: Optional[str],
        storage_key: str,
    ) -> OCRProviderResult:
        if storage_backend != "s3":
            raise ValueError("Async Textract analysis OCR requires an S3-backed upload")
        if not self.upload_s3_bucket:
            raise ValueError("PAPRNAV_S3_UPLOAD_BUCKET is required for async Textract analysis OCR")
        if not self.analysis_feature_types:
            raise ValueError("PAPRNAV_TEXTRACT_ANALYSIS_FEATURE_TYPES must include at least one Textract feature")
        self._validate_async_pdf_guardrail(original_filename=original_filename, content_type=content_type, storage_key=storage_key)

        client = self.client or self._create_client()
        response = client.start_document_analysis(
            DocumentLocation={
                "S3Object": {
                    "Bucket": self.upload_s3_bucket,
                    "Name": storage_key,
                }
            },
            FeatureTypes=self.analysis_feature_types,
        )
        job_id = response["JobId"]
        return self._wait_for_analysis_result(client, job_id=job_id)

    def _validate_async_pdf_guardrail(self, *, original_filename: str, content_type: str, storage_key: str) -> None:
        if self.ocr_max_pdf_pages is None:
            return
        if content_type != "application/pdf" and not original_filename.lower().endswith(".pdf"):
            return
        page_count = self._s3_pdf_page_count(storage_key)
        if page_count > self.ocr_max_pdf_pages:
            raise ValueError(f"Refusing to OCR {page_count} PDF pages; PAPRNAV_OCR_MAX_PDF_PAGES is {self.ocr_max_pdf_pages}")

    def _s3_pdf_page_count(self, storage_key: str) -> int:
        try:
            from pypdf import PdfReader
        except ImportError as exc:
            raise RuntimeError("pypdf is required for PDF OCR page guardrails") from exc

        s3_client = self.s3_client or self._create_s3_client()
        response = s3_client.get_object(Bucket=self.upload_s3_bucket, Key=storage_key)
        return len(PdfReader(BytesIO(response["Body"].read())).pages)

    def _wait_for_async_result(self, client: Any, *, job_id: str) -> OCRProviderResult:
        deadline = time.monotonic() + self.async_timeout_seconds
        next_token: str | None = None
        blocks: list[dict[str, Any]] = []
        metadata: dict[str, Any] = {}
        model_version: str | None = None

        while True:
            request: dict[str, Any] = {"JobId": job_id}
            if next_token:
                request["NextToken"] = next_token
            response = client.get_document_text_detection(**request)
            status = response.get("JobStatus")
            if status == "SUCCEEDED":
                blocks.extend(response.get("Blocks", []))
                metadata = response.get("DocumentMetadata", metadata)
                model_version = response.get("DetectDocumentTextModelVersion", model_version)
                next_token = response.get("NextToken")
                if next_token:
                    continue
                return self.result_from_response(
                    {
                        "DetectDocumentTextModelVersion": model_version or self.provider_version,
                        "DocumentMetadata": metadata,
                        "Blocks": blocks,
                    }
                )
            if status in {"FAILED", "PARTIAL_SUCCESS"}:
                message = response.get("StatusMessage") or f"Textract async job {job_id} ended with status {status}"
                raise RuntimeError(message)
            if time.monotonic() >= deadline:
                raise TimeoutError(f"Timed out waiting for Textract async job {job_id}")
            time.sleep(self.async_poll_seconds)

    def _wait_for_analysis_result(self, client: Any, *, job_id: str) -> OCRProviderResult:
        deadline = time.monotonic() + self.async_timeout_seconds
        next_token: str | None = None
        blocks: list[dict[str, Any]] = []
        metadata: dict[str, Any] = {}
        model_version: str | None = None

        while True:
            request: dict[str, Any] = {"JobId": job_id}
            if next_token:
                request["NextToken"] = next_token
            response = client.get_document_analysis(**request)
            status = response.get("JobStatus")
            if status == "SUCCEEDED":
                blocks.extend(response.get("Blocks", []))
                metadata = response.get("DocumentMetadata", metadata)
                model_version = response.get("AnalyzeDocumentModelVersion", model_version)
                next_token = response.get("NextToken")
                if next_token:
                    continue
                return self.result_from_analysis_response(
                    {
                        "AnalyzeDocumentModelVersion": model_version or self.provider_version,
                        "DocumentMetadata": metadata,
                        "Blocks": blocks,
                    }
                )
            if status in {"FAILED", "PARTIAL_SUCCESS"}:
                message = response.get("StatusMessage") or f"Textract analysis job {job_id} ended with status {status}"
                raise RuntimeError(message)
            if time.monotonic() >= deadline:
                raise TimeoutError(f"Timed out waiting for Textract analysis job {job_id}")
            time.sleep(self.async_poll_seconds)

    def _validate_sync_document(
        self,
        *,
        original_filename: str,
        content_type: str,
        storage_backend: Optional[str],
        storage_key: str,
    ) -> None:
        if content_type == "application/pdf" or original_filename.lower().endswith(".pdf"):
            raise ValueError("Synchronous Textract OCR does not support PDF logbooks; use async Textract before enabling PDF OCR")

        if storage_backend != "s3":
            path = self._local_upload_path(storage_key)
            if path.stat().st_size > self.sync_max_document_bytes:
                raise ValueError("Synchronous Textract OCR input exceeds the 10 MB document limit")

    def _create_client(self) -> Any:
        try:
            import boto3
        except ImportError as exc:
            raise RuntimeError("boto3 is required when PAPRNAV_OCR_PROVIDER=textract") from exc

        return boto3.client("textract", region_name=self.region_name)

    def _create_s3_client(self) -> Any:
        try:
            import boto3
        except ImportError as exc:
            raise RuntimeError("boto3 is required for S3-backed Textract OCR") from exc

        return boto3.client("s3", region_name=self.region_name)

    def _document_reference(self, *, storage_backend: Optional[str], storage_key: str) -> dict[str, Any]:
        if storage_backend == "s3":
            if not self.upload_s3_bucket:
                raise ValueError("PAPRNAV_S3_UPLOAD_BUCKET is required for S3-backed Textract OCR")
            return {"S3Object": {"Bucket": self.upload_s3_bucket, "Name": storage_key}}

        path = self._local_upload_path(storage_key)
        return {"Bytes": path.read_bytes()}

    def _local_upload_path(self, storage_key: str) -> Path:
        root = Path(self.storage_root).resolve()
        path = (root / storage_key).resolve()
        if root not in path.parents and path != root:
            raise ValueError("Invalid OCR storage key")
        if not path.is_file():
            raise FileNotFoundError(f"Stored upload not found: {storage_key}")
        return path

    def result_from_response(self, response: dict[str, Any]) -> OCRProviderResult:
        blocks = response.get("Blocks", [])
        line_blocks = [block for block in blocks if block.get("BlockType") == "LINE"]
        word_blocks = [block for block in blocks if block.get("BlockType") == "WORD"]
        text_blocks = sorted(
            [*line_blocks, *word_blocks],
            key=lambda block: (int(block.get("Page") or 1), block_sort_top(block), block_sort_left(block)),
        )
        blocks_by_page: dict[int, list[dict[str, Any]]] = {}
        for block in text_blocks:
            page_number = int(block.get("Page") or 1)
            blocks_by_page.setdefault(page_number, []).append(block)

        page_count = int(response.get("DocumentMetadata", {}).get("Pages") or max(blocks_by_page.keys(), default=1))
        pages = [
            self._page_result(page_number, blocks_by_page.get(page_number, []))
            for page_number in range(1, page_count + 1)
        ]
        return OCRProviderResult(
            provider_name=self.provider_name,
            provider_version=response.get("DetectDocumentTextModelVersion") or self.provider_version,
            configuration_hash=self.configuration_hash,
            pages=pages,
        )

    def result_from_analysis_response(self, response: dict[str, Any]) -> OCRProviderResult:
        blocks = response.get("Blocks", [])
        supported_blocks = [
            block
            for block in blocks
            if block.get("BlockType") in TEXTRACT_ANALYSIS_SPAN_BLOCK_TYPES
        ]
        text_blocks = sorted(
            supported_blocks,
            key=lambda block: (
                int(block.get("Page") or 1),
                block_sort_top(block),
                textract_analysis_block_sort_weight(block),
                block_sort_left(block),
            ),
        )
        blocks_by_page: dict[int, list[dict[str, Any]]] = {}
        for block in text_blocks:
            page_number = int(block.get("Page") or 1)
            blocks_by_page.setdefault(page_number, []).append(block)

        page_count = int(response.get("DocumentMetadata", {}).get("Pages") or max(blocks_by_page.keys(), default=1))
        pages = [
            self._analysis_page_result(page_number, blocks_by_page.get(page_number, []))
            for page_number in range(1, page_count + 1)
        ]
        block_counts = count_blocks_by_type(blocks)
        return OCRProviderResult(
            provider_name=self.provider_name,
            provider_version=response.get("AnalyzeDocumentModelVersion") or self.provider_version,
            configuration_hash=self.configuration_hash,
            pages=pages,
            billable_page_count=page_count,
            metadata={
                "provider_mode": self.api_mode,
                "textract_feature_types": self.analysis_feature_types,
                "textract_block_counts": block_counts,
                "third_party_processing": False,
            },
        )

    def _page_result(self, page_number: int, blocks: list[dict[str, Any]]) -> OCRPageResult:
        spans = [self._span_result(block, reading_order=index + 1) for index, block in enumerate(blocks)]
        line_confidences = [span.confidence for span in spans if span.span_type == "LINE"]
        extraction_confidence = (
            sum(line_confidences) / len(line_confidences)
            if line_confidences
            else 0.0
        )
        return OCRPageResult(
            source_page_number=page_number,
            page_label=f"Textract page {page_number}",
            width_px=0,
            height_px=0,
            rotation_degrees=page_rotation(blocks),
            extraction_confidence=extraction_confidence,
            spans=spans,
        )

    def _analysis_page_result(self, page_number: int, blocks: list[dict[str, Any]]) -> OCRPageResult:
        spans = [self._span_result(block, reading_order=index + 1) for index, block in enumerate(blocks)]
        line_confidences = [span.confidence for span in spans if span.span_type == "LINE"]
        extraction_confidence = (
            sum(line_confidences) / len(line_confidences)
            if line_confidences
            else 0.0
        )
        return OCRPageResult(
            source_page_number=page_number,
            page_label=f"Textract analysis page {page_number}",
            width_px=0,
            height_px=0,
            rotation_degrees=page_rotation(blocks),
            extraction_confidence=extraction_confidence,
            spans=spans,
        )

    def _span_result(self, block: dict[str, Any], *, reading_order: int) -> OCRSpanResult:
        bbox = block.get("Geometry", {}).get("BoundingBox", {})
        return OCRSpanResult(
            provider_block_id=block.get("Id") or f"textract-{reading_order}",
            span_type=block.get("BlockType") or "UNKNOWN",
            text=textract_block_text(block),
            confidence=float(block.get("Confidence") or 0.0),
            bbox_left=float(bbox.get("Left") or 0.0),
            bbox_top=float(bbox.get("Top") or 0.0),
            bbox_width=float(bbox.get("Width") or 0.0),
            bbox_height=float(bbox.get("Height") or 0.0),
            bbox_units="ratio",
            reading_order=reading_order,
            relationships=textract_relationships(block),
        )


class MistralOCRProvider(OCRProvider):
    provider_name = "mistral_ocr"
    direct_api_page_price_usd = 0.004

    def __init__(
        self,
        *,
        http_client: Optional[Any] = None,
        s3_client: Optional[Any] = None,
        storage_root: Optional[str] = None,
    ) -> None:
        settings = get_settings()
        self.api_key = settings.mistral_api_key
        self.base_url = settings.mistral_base_url
        self.model = settings.mistral_ocr_model
        self.channel = settings.mistral_ocr_channel
        self.mode = settings.mistral_ocr_mode
        self.timeout_seconds = settings.mistral_ocr_timeout_seconds
        self.max_pdf_pages = settings.mistral_ocr_max_pdf_pages
        self.upload_s3_bucket = settings.s3_upload_bucket
        self.region_name = settings.aws_region
        self.http_client = http_client
        self.s3_client = s3_client
        self.storage_root = storage_root or settings.local_storage_path
        self.provider_version = self.model
        self.configuration_hash = f"mistral-ocr:{self.channel}:{self.model}:{self.mode}"

    def process_upload(
        self,
        *,
        original_filename: str,
        content_type: str,
        storage_backend: Optional[str] = None,
        storage_key: Optional[str] = None,
    ) -> OCRProviderResult:
        if self.channel == "sagemaker":
            raise ValueError(
                "PAPRNAV_MISTRAL_OCR_CHANNEL=sagemaker requires a configured SageMaker endpoint; "
                "direct API A/B testing uses PAPRNAV_MISTRAL_OCR_CHANNEL=direct_api"
            )
        if self.channel != "direct_api":
            raise ValueError(f"Unsupported Mistral OCR channel: {self.channel}")
        if not self.api_key:
            raise ValueError("PAPRNAV_MISTRAL_API_KEY is required when PAPRNAV_OCR_PROVIDER=mistral")
        if not storage_key:
            raise ValueError("Mistral OCR requires an upload storage key")

        started = time.monotonic()
        document_bytes = self._read_upload_bytes(storage_backend=storage_backend, storage_key=storage_key)
        pdf_pages = self._validate_pdf_guardrail(
            original_filename=original_filename,
            content_type=content_type,
            document_bytes=document_bytes,
        )
        response = self._call_direct_api(
            document_bytes=document_bytes,
            content_type=content_type,
            original_filename=original_filename,
            pdf_pages=pdf_pages,
        )
        result = self.result_from_response(response)
        return replace(
            result,
            metadata={
                **result.metadata,
                "processing_seconds": round(time.monotonic() - started, 6),
            },
        )

    def _read_upload_bytes(self, *, storage_backend: Optional[str], storage_key: str) -> bytes:
        if storage_backend == "s3":
            if not self.upload_s3_bucket:
                raise ValueError("PAPRNAV_S3_UPLOAD_BUCKET is required for S3-backed Mistral OCR")
            s3_client = self.s3_client or self._create_s3_client()
            response = s3_client.get_object(Bucket=self.upload_s3_bucket, Key=storage_key)
            return response["Body"].read()

        path = self._local_upload_path(storage_key)
        return path.read_bytes()

    def _validate_pdf_guardrail(self, *, original_filename: str, content_type: str, document_bytes: bytes) -> Optional[int]:
        if content_type != "application/pdf" and not original_filename.lower().endswith(".pdf"):
            return None
        page_count = pdf_page_count(document_bytes)
        if self.max_pdf_pages is not None and page_count > self.max_pdf_pages:
            raise ValueError(
                f"Refusing to OCR {page_count} PDF pages; PAPRNAV_MISTRAL_OCR_MAX_PDF_PAGES is {self.max_pdf_pages}"
            )
        return page_count

    def _call_direct_api(
        self,
        *,
        document_bytes: bytes,
        content_type: str,
        original_filename: str,
        pdf_pages: Optional[int],
    ) -> dict[str, Any]:
        import httpx

        media_type = content_type or content_type_from_filename(original_filename)
        document_url = f"data:{media_type};base64,{base64.b64encode(document_bytes).decode('ascii')}"
        document_type = "image_url" if media_type.startswith("image/") else "document_url"
        document_key = "image_url" if document_type == "image_url" else "document_url"
        payload: dict[str, Any] = {
            "model": self.model,
            "document": {
                "type": document_type,
                document_key: document_url,
            },
            "include_blocks": True,
            "include_image_base64": False,
            "confidence_scores_granularity": "page",
            "table_format": "markdown",
        }
        if pdf_pages is not None and self.max_pdf_pages:
            payload["pages"] = list(range(min(pdf_pages, self.max_pdf_pages)))

        client = self.http_client
        if client is not None:
            response = client.post(
                f"{self.base_url}/ocr",
                headers=self._headers(),
                json=payload,
                timeout=self.timeout_seconds,
            )
        else:
            response = httpx.post(
                f"{self.base_url}/ocr",
                headers=self._headers(),
                json=payload,
                timeout=self.timeout_seconds,
            )
        response.raise_for_status()
        return response.json()

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def _create_s3_client(self) -> Any:
        try:
            import boto3
        except ImportError as exc:
            raise RuntimeError("boto3 is required for S3-backed Mistral OCR") from exc

        return boto3.client("s3", region_name=self.region_name)

    def _local_upload_path(self, storage_key: str) -> Path:
        root = Path(self.storage_root).resolve()
        path = (root / storage_key).resolve()
        if root not in path.parents and path != root:
            raise ValueError("Invalid OCR storage key")
        if not path.is_file():
            raise FileNotFoundError(f"Stored upload not found: {storage_key}")
        return path

    def result_from_response(self, response: dict[str, Any]) -> OCRProviderResult:
        pages = [self._page_result(page, index) for index, page in enumerate(response.get("pages", []))]
        usage_info = response.get("usage_info") or {}
        pages_processed = usage_info.get("pages_processed")
        billable_page_count = int(pages_processed) if pages_processed is not None else len(pages)
        return OCRProviderResult(
            provider_name=self.provider_name,
            provider_version=response.get("model") or self.provider_version,
            configuration_hash=self.configuration_hash,
            pages=pages,
            billable_page_count=billable_page_count,
            metadata={
                "provider_channel": self.channel,
                "provider_mode": self.mode,
                "third_party_processing": True,
                "usage_info": usage_info,
                "pricing_unit": "page",
                "pricing_rate_usd": self.direct_api_page_price_usd,
                "estimated_unit_cost_usd_per_page": self.direct_api_page_price_usd,
                "estimated_cost_usd": round(billable_page_count * self.direct_api_page_price_usd, 6),
            },
        )

    def _page_result(self, page: dict[str, Any], fallback_index: int) -> OCRPageResult:
        dimensions = page.get("dimensions") or {}
        source_page_number = mistral_source_page_number(page, fallback_index)
        page_confidence = mistral_page_confidence(page)
        spans = self._block_spans(page, page_confidence)
        spans.extend(self._line_spans(page, page_confidence, starting_order=len(spans) + 1))
        return OCRPageResult(
            source_page_number=source_page_number,
            page_label=f"Mistral OCR page {source_page_number}",
            width_px=int(dimensions.get("width") or 0),
            height_px=int(dimensions.get("height") or 0),
            rotation_degrees=0,
            extraction_confidence=page_confidence,
            spans=spans,
        )

    def _block_spans(self, page: dict[str, Any], page_confidence: float) -> list[OCRSpanResult]:
        spans: list[OCRSpanResult] = []
        for index, block in enumerate(page.get("blocks") or [], start=1):
            text = str(block.get("content") or block.get("text") or "").strip()
            if not text:
                continue
            bbox = mistral_bbox(block, page.get("dimensions") or {})
            spans.append(
                OCRSpanResult(
                    provider_block_id=str(block.get("id") or f"mistral-block-{page.get('index', 0)}-{index}"),
                    span_type=str(block.get("type") or block.get("label") or "BLOCK").upper(),
                    text=text,
                    confidence=page_confidence,
                    bbox_left=bbox["left"],
                    bbox_top=bbox["top"],
                    bbox_width=bbox["width"],
                    bbox_height=bbox["height"],
                    bbox_units="ratio",
                    reading_order=index,
                    relationships=[{"provider": "mistral", "raw_block": block}],
                )
            )
        return spans

    def _line_spans(self, page: dict[str, Any], page_confidence: float, *, starting_order: int) -> list[OCRSpanResult]:
        lines = [line.strip() for line in str(page.get("markdown") or "").splitlines() if line.strip()]
        total = max(len(lines), 1)
        spans: list[OCRSpanResult] = []
        for index, line in enumerate(lines, start=1):
            spans.append(
                OCRSpanResult(
                    provider_block_id=f"mistral-line-{page.get('index', 0)}-{index}",
                    span_type="LINE",
                    text=line,
                    confidence=page_confidence,
                    bbox_left=0.0,
                    bbox_top=(index - 1) / total,
                    bbox_width=1.0,
                    bbox_height=1 / total,
                    bbox_units="ratio",
                    reading_order=starting_order + index - 1,
                    relationships=[{"provider": "mistral", "source": "markdown"}],
                )
            )
        return spans


def block_sort_top(block: dict[str, Any]) -> float:
    return float(block.get("Geometry", {}).get("BoundingBox", {}).get("Top") or 0.0)


def block_sort_left(block: dict[str, Any]) -> float:
    return float(block.get("Geometry", {}).get("BoundingBox", {}).get("Left") or 0.0)


def page_rotation(blocks: list[dict[str, Any]]) -> float:
    for block in blocks:
        rotation = block.get("Geometry", {}).get("RotationAngle")
        if rotation is not None:
            return float(rotation)
    return 0.0


def textract_analysis_block_sort_weight(block: dict[str, Any]) -> int:
    block_type = block.get("BlockType") or ""
    weights = {
        "LAYOUT_HEADER": 0,
        "LAYOUT_TITLE": 1,
        "LAYOUT_SECTION_HEADER": 2,
        "TABLE": 3,
        "LAYOUT_TABLE": 4,
        "CELL": 5,
        "MERGED_CELL": 6,
        "LINE": 7,
        "WORD": 8,
        "SIGNATURE": 9,
    }
    return weights.get(block_type, 20)


def textract_block_text(block: dict[str, Any]) -> str:
    text = block.get("Text")
    if text:
        return str(text)
    block_type = block.get("BlockType") or "UNKNOWN"
    if block_type == "SIGNATURE":
        return "[signature]"
    if block_type in {"TABLE", "LAYOUT_TABLE"}:
        return "[table]"
    if block_type in {"CELL", "MERGED_CELL"}:
        row = block.get("RowIndex")
        column = block.get("ColumnIndex")
        return f"[cell r{row or '?'} c{column or '?'}]"
    return f"[{str(block_type).lower()}]"


def textract_relationships(block: dict[str, Any]) -> list[dict[str, Any]]:
    relationships = list(block.get("Relationships") or [])
    metadata_keys = (
        "BlockType",
        "EntityTypes",
        "RowIndex",
        "ColumnIndex",
        "RowSpan",
        "ColumnSpan",
        "SelectionStatus",
    )
    metadata = {key: block[key] for key in metadata_keys if key in block}
    if metadata:
        relationships.append({"provider": "aws_textract", "block_metadata": metadata})
    return relationships


def count_blocks_by_type(blocks: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for block in blocks:
        block_type = block.get("BlockType") or "UNKNOWN"
        counts[block_type] = counts.get(block_type, 0) + 1
    return dict(sorted(counts.items()))


def content_type_from_filename(filename: str) -> str:
    lower = filename.lower()
    if lower.endswith(".png"):
        return "image/png"
    if lower.endswith(".jpg") or lower.endswith(".jpeg"):
        return "image/jpeg"
    return "application/pdf"


def pdf_page_count(document_bytes: bytes) -> int:
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise RuntimeError("pypdf is required for PDF OCR page guardrails") from exc

    return len(PdfReader(BytesIO(document_bytes)).pages)


def mistral_source_page_number(page: dict[str, Any], fallback_index: int) -> int:
    index = page.get("index")
    if isinstance(index, int):
        return index if index > 0 else index + 1
    return fallback_index + 1


def mistral_page_confidence(page: dict[str, Any]) -> float:
    scores = page.get("confidence_scores") or {}
    confidence = scores.get("average_page_confidence_score")
    if confidence is None:
        confidence = scores.get("minimum_page_confidence_score")
    if confidence is None:
        return 0.0
    confidence = float(confidence)
    return confidence * 100 if confidence <= 1 else confidence


def mistral_bbox(block: dict[str, Any], dimensions: dict[str, Any]) -> dict[str, float]:
    width = float(dimensions.get("width") or 0)
    height = float(dimensions.get("height") or 0)
    if all(key in block for key in ("top_left_x", "top_left_y", "bottom_right_x", "bottom_right_y")):
        left = float(block["top_left_x"])
        top = float(block["top_left_y"])
        right = float(block["bottom_right_x"])
        bottom = float(block["bottom_right_y"])
        return pixel_bbox_to_ratio(left, top, right, bottom, width=width, height=height)

    bbox = block.get("bbox") or block.get("bounding_box") or {}
    if isinstance(bbox, dict):
        if all(key in bbox for key in ("top_left_x", "top_left_y", "bottom_right_x", "bottom_right_y")):
            return pixel_bbox_to_ratio(
                float(bbox["top_left_x"]),
                float(bbox["top_left_y"]),
                float(bbox["bottom_right_x"]),
                float(bbox["bottom_right_y"]),
                width=width,
                height=height,
            )
        if all(key in bbox for key in ("left", "top", "width", "height")):
            return {
                "left": float(bbox["left"]),
                "top": float(bbox["top"]),
                "width": float(bbox["width"]),
                "height": float(bbox["height"]),
            }
    if isinstance(bbox, list) and len(bbox) == 4:
        return pixel_bbox_to_ratio(float(bbox[0]), float(bbox[1]), float(bbox[2]), float(bbox[3]), width=width, height=height)
    return {"left": 0.0, "top": 0.0, "width": 1.0, "height": 1.0}


def pixel_bbox_to_ratio(left: float, top: float, right: float, bottom: float, *, width: float, height: float) -> dict[str, float]:
    if width <= 0 or height <= 0:
        return {"left": 0.0, "top": 0.0, "width": 0.0, "height": 0.0}
    return {
        "left": left / width,
        "top": top / height,
        "width": max(right - left, 0.0) / width,
        "height": max(bottom - top, 0.0) / height,
    }


def get_ocr_provider() -> OCRProvider:
    settings = get_settings()
    if settings.ocr_provider == "textract":
        return TextractOCRProvider()
    if settings.ocr_provider == "mistral":
        return MistralOCRProvider()
    if settings.ocr_provider == "layout_first_vlm":
        from app.services.layout_first_ocr import LayoutFirstVLMOCRProvider

        return LayoutFirstVLMOCRProvider()
    return DeterministicFixtureOCRProvider()
