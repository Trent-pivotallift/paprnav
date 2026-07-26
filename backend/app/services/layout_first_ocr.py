from __future__ import annotations

import base64
from dataclasses import dataclass, field
from hashlib import sha256
from html.parser import HTMLParser
from io import BytesIO
import os
from pathlib import Path
import time
from typing import Any, Optional
from urllib.parse import urlparse

from app.core.config import Settings, get_settings
from app.services.ocr_provider import (
    OCRPageResult,
    OCRProvider,
    OCRProviderResult,
    OCRSpanResult,
)


@dataclass(frozen=True)
class LayoutRegion:
    provider_region_id: str
    reading_order: int
    label: str
    task_type: str
    layout_confidence: Optional[float]
    bbox_left: float
    bbox_top: float
    bbox_width: float
    bbox_height: float
    polygon: list[list[float]] = field(default_factory=list)


@dataclass(frozen=True)
class RegionRecognition:
    text: str
    confidence: Optional[float] = None
    metadata: dict[str, Any] = field(default_factory=dict)


class PPDocLayoutRegionDetector:
    model_version = "PaddlePaddle/PP-DocLayoutV3_safetensors"

    def __init__(
        self,
        *,
        model_dir: str,
        device: str,
        threshold: float,
    ) -> None:
        self.model_version = model_dir
        self.device = device
        self.threshold = threshold
        self._detector: Any = None

    def detect(self, image: Any) -> list[LayoutRegion]:
        detector = self._get_detector()
        page_results, _ = detector.process([image], save_visualization=False)
        raw_regions = page_results[0] if page_results else []
        return [
            layout_region_from_glm(raw_region, fallback_index=index)
            for index, raw_region in enumerate(raw_regions)
        ]

    def close(self) -> None:
        if self._detector is not None:
            self._detector.stop()
            self._detector = None

    def _get_detector(self) -> Any:
        if self._detector is not None:
            return self._detector
        try:
            from glmocr.config import load_config
            from glmocr.layout.layout_detector import PPDocLayoutDetector
        except ImportError as exc:
            raise RuntimeError(
                "The layout-first OCR provider requires the optional "
                "requirements-layout-ocr.txt dependencies"
            ) from exc

        config = load_config()
        layout_config = config.pipeline.layout.model_copy(
            update={
                "model_dir": self.model_version,
                "device": self.device,
                "threshold": self.threshold,
                "batch_size": 1,
            }
        )
        self._detector = PPDocLayoutDetector(layout_config)
        self._detector.start()
        return self._detector


class OllamaGLMRegionRecognizer:
    def __init__(
        self,
        *,
        base_url: str,
        model: str,
        timeout_seconds: float,
        num_gpu: Optional[int] = None,
        num_ctx: int = 16384,
        http_client: Optional[Any] = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        validate_loopback_ollama_url(self.base_url)
        self.model_version = model
        self.timeout_seconds = timeout_seconds
        self.num_gpu = num_gpu
        self.num_ctx = num_ctx
        self.http_client = http_client

    def recognize(self, image: Any, task_type: str) -> RegionRecognition:
        import httpx

        encoded_image = encode_image_as_jpeg(image)
        payload = {
            "model": self.model_version,
            "prompt": glm_task_prompt(task_type),
            "images": [encoded_image],
            "stream": False,
            "options": {
                "temperature": 0,
                "top_p": 0.00001,
                "top_k": 1,
                "repeat_penalty": 1.1,
                "num_predict": 8192,
                "num_ctx": self.num_ctx,
            },
        }
        if self.num_gpu is not None:
            payload["options"]["num_gpu"] = self.num_gpu
        started = time.monotonic()
        client = self.http_client
        if client is not None:
            response = client.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=self.timeout_seconds,
            )
        else:
            response = httpx.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=self.timeout_seconds,
            )
        response.raise_for_status()
        body = response.json()
        if body.get("error"):
            raise RuntimeError(f"GLM-OCR recognition failed: {body['error']}")
        if body.get("response") is None:
            raise RuntimeError("GLM-OCR recognition response did not include text")

        raw_text = str(body["response"]).strip()
        text, content_format = recognized_content_to_text(raw_text)
        metadata = {
            "content_format": content_format,
            "content_sha256": sha256(raw_text.encode("utf-8")).hexdigest(),
            "raw_content_bytes": len(raw_text.encode("utf-8")),
            "raw_content_persisted": False,
            "raw_artifact_location": None,
            "latency_ms": round((time.monotonic() - started) * 1000, 3),
            "num_ctx": self.num_ctx,
            "num_gpu": self.num_gpu,
        }
        for key in ("total_duration", "load_duration", "prompt_eval_count", "eval_count"):
            if body.get(key) is not None:
                metadata[key] = body[key]
        return RegionRecognition(text=text, confidence=None, metadata=metadata)


class LayoutFirstVLMOCRProvider(OCRProvider):
    provider_name = "layout_first_vlm"

    def __init__(
        self,
        *,
        detector: Optional[Any] = None,
        recognizer: Optional[Any] = None,
        s3_client: Optional[Any] = None,
        storage_root: Optional[str] = None,
        settings: Optional[Settings] = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.storage_root = storage_root or self.settings.local_storage_path
        self.s3_client = s3_client
        self.upload_s3_bucket = self.settings.s3_upload_bucket
        self.region_name = self.settings.aws_region
        self.max_pdf_pages = self.settings.ocr_max_pdf_pages
        self.detector = detector
        self.recognizer = recognizer
        self.provider_version = self.settings.layout_first_recognition_model
        config_signature = "|".join(
            (
                self.settings.layout_first_layout_model,
                self.settings.layout_first_layout_device,
                str(self.settings.layout_first_layout_threshold),
                self.settings.layout_first_recognition_model,
                self.settings.layout_first_ollama_base_url,
                os.getenv("PAPRNAV_LAYOUT_FIRST_OLLAMA_NUM_GPU", "default"),
                os.getenv("PAPRNAV_LAYOUT_FIRST_OLLAMA_NUM_CTX", "16384"),
            )
        )
        self.configuration_hash = f"layout-first:{sha256(config_signature.encode('utf-8')).hexdigest()[:16]}"

    def process_upload(
        self,
        *,
        original_filename: str,
        content_type: str,
        storage_backend: Optional[str] = None,
        storage_key: Optional[str] = None,
    ) -> OCRProviderResult:
        if not storage_key:
            raise ValueError("Layout-first OCR requires an upload storage key")

        started = time.monotonic()
        document_bytes = self._read_upload_bytes(
            storage_backend=storage_backend,
            storage_key=storage_key,
        )
        page_images = render_upload_pages(
            document_bytes,
            original_filename=original_filename,
            content_type=content_type,
            max_pdf_pages=self.max_pdf_pages,
            dpi=self.settings.layout_first_pdf_dpi,
        )
        detector = self.detector or PPDocLayoutRegionDetector(
            model_dir=self.settings.layout_first_layout_model,
            device=self.settings.layout_first_layout_device,
            threshold=self.settings.layout_first_layout_threshold,
        )
        recognizer = self.recognizer or OllamaGLMRegionRecognizer(
            base_url=self.settings.layout_first_ollama_base_url,
            model=self.settings.layout_first_recognition_model,
            timeout_seconds=self.settings.layout_first_timeout_seconds,
            num_gpu=(
                int(os.environ["PAPRNAV_LAYOUT_FIRST_OLLAMA_NUM_GPU"])
                if os.getenv("PAPRNAV_LAYOUT_FIRST_OLLAMA_NUM_GPU") is not None
                else None
            ),
            num_ctx=int(os.getenv("PAPRNAV_LAYOUT_FIRST_OLLAMA_NUM_CTX", "16384")),
        )

        pages: list[OCRPageResult] = []
        try:
            for page_number, image in enumerate(page_images, start=1):
                pages.append(
                    self._process_page(
                        page_number=page_number,
                        image=image,
                        detector=detector,
                        recognizer=recognizer,
                    )
                )
        finally:
            if self.detector is None and hasattr(detector, "close"):
                detector.close()

        processing_seconds = time.monotonic() - started
        compute_rate = self.settings.layout_first_compute_rate_usd_per_hour
        estimated_cost = processing_seconds / 3600 * compute_rate

        return OCRProviderResult(
            provider_name=self.provider_name,
            provider_version=self.provider_version,
            configuration_hash=self.configuration_hash,
            pages=pages,
            billable_page_count=len(pages),
            metadata={
                "provider_mode": "layout_first",
                "provider_channel": "local_ollama",
                "layout_device": self.settings.layout_first_layout_device,
                "recognition_runtime": "ollama",
                "layout_model": getattr(
                    detector,
                    "model_version",
                    self.settings.layout_first_layout_model,
                ),
                "recognition_model": getattr(
                    recognizer,
                    "model_version",
                    self.settings.layout_first_recognition_model,
                ),
                "recognition_confidence_available": False,
                "third_party_processing": False,
                "processing_latency_ms": round(processing_seconds * 1000, 3),
                "processing_seconds": round(processing_seconds, 6),
                "pricing_unit": "compute_hour",
                "pricing_rate_usd": compute_rate,
                "compute_rate_usd_per_hour": compute_rate,
                "estimated_cost_usd": round(estimated_cost, 6),
            },
        )

    def _process_page(
        self,
        *,
        page_number: int,
        image: Any,
        detector: Any,
        recognizer: Any,
    ) -> OCRPageResult:
        width_px, height_px = image.size
        regions = sorted(
            detector.detect(image),
            key=lambda region: (
                region.reading_order,
                region.bbox_top,
                region.bbox_left,
                region.provider_region_id,
            ),
        )
        spans: list[OCRSpanResult] = []
        for reading_order, region in enumerate(regions, start=1):
            validate_layout_region(region)
            crop = crop_layout_region(image, region)
            recognition = recognizer.recognize(crop, region.task_type)
            spans.append(
                OCRSpanResult(
                    provider_block_id=region.provider_region_id,
                    span_type=f"REGION_{region.task_type.upper()}",
                    text=recognition.text,
                    confidence=recognition.confidence,
                    bbox_left=region.bbox_left,
                    bbox_top=region.bbox_top,
                    bbox_width=region.bbox_width,
                    bbox_height=region.bbox_height,
                    bbox_units="ratio",
                    reading_order=reading_order,
                    polygon=region.polygon,
                    relationships=[
                        {
                            "provider": self.provider_name,
                            "layout": {
                                "label": region.label,
                                "confidence": region.layout_confidence,
                                "confidence_scale": "0_100",
                            },
                            "recognition": {
                                "model": getattr(
                                    recognizer,
                                    "model_version",
                                    self.settings.layout_first_recognition_model,
                                ),
                                "confidence": recognition.confidence,
                                **recognition.metadata,
                            },
                        }
                    ],
                )
            )

        recognition_confidences = [
            span.confidence for span in spans if span.confidence is not None
        ]
        extraction_confidence = (
            sum(recognition_confidences) / len(recognition_confidences)
            if recognition_confidences
            else None
        )
        return OCRPageResult(
            source_page_number=page_number,
            page_label=f"Layout-first OCR page {page_number}",
            width_px=width_px,
            height_px=height_px,
            rotation_degrees=0,
            extraction_confidence=extraction_confidence,
            spans=spans,
        )

    def _read_upload_bytes(
        self,
        *,
        storage_backend: Optional[str],
        storage_key: str,
    ) -> bytes:
        if storage_backend == "s3":
            if not self.upload_s3_bucket:
                raise ValueError(
                    "PAPRNAV_S3_UPLOAD_BUCKET is required for S3-backed layout-first OCR"
                )
            s3_client = self.s3_client or self._create_s3_client()
            response = s3_client.get_object(
                Bucket=self.upload_s3_bucket,
                Key=storage_key,
            )
            return response["Body"].read()

        root = Path(self.storage_root).resolve()
        path = (root / storage_key).resolve()
        if root not in path.parents and path != root:
            raise ValueError("Invalid OCR storage key")
        if not path.is_file():
            raise FileNotFoundError(f"Stored upload not found: {storage_key}")
        return path.read_bytes()

    def _create_s3_client(self) -> Any:
        try:
            import boto3
        except ImportError as exc:
            raise RuntimeError(
                "boto3 is required for S3-backed layout-first OCR"
            ) from exc
        return boto3.client("s3", region_name=self.region_name)


class _PlainTextHTMLParser(HTMLParser):
    BREAK_TAGS = {
        "br",
        "div",
        "li",
        "p",
        "table",
        "tbody",
        "td",
        "th",
        "tr",
    }

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []

    def handle_starttag(
        self,
        tag: str,
        attrs: list[tuple[str, Optional[str]]],
    ) -> None:
        if tag.lower() in self.BREAK_TAGS:
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() in self.BREAK_TAGS:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        self.parts.append(data)

    def text(self) -> str:
        lines = [
            " ".join(line.split())
            for line in "".join(self.parts).splitlines()
            if line.strip()
        ]
        return "\n".join(lines)


def recognized_content_to_text(raw_text: str) -> tuple[str, str]:
    stripped = raw_text.strip()
    if "<table" not in stripped.lower():
        return stripped, "text"
    parser = _PlainTextHTMLParser()
    parser.feed(stripped)
    parser.close()
    return parser.text(), "html_table"


def glm_task_prompt(task_type: str) -> str:
    return {
        "table": "Table Recognition:",
        "formula": "Formula Recognition:",
    }.get(task_type, "Text Recognition:")


def validate_loopback_ollama_url(base_url: str) -> None:
    parsed = urlparse(base_url)
    if parsed.scheme not in {"http", "https"}:
        raise ValueError(
            "PAPRNAV_LAYOUT_FIRST_OLLAMA_BASE_URL must use http or https"
        )
    if parsed.hostname not in {"127.0.0.1", "::1", "localhost"}:
        raise ValueError(
            "The layout-first feasibility provider only permits a loopback "
            "Ollama endpoint"
        )


def encode_image_as_jpeg(image: Any) -> str:
    output = BytesIO()
    image.convert("RGB").save(output, format="JPEG", quality=95)
    return base64.b64encode(output.getvalue()).decode("ascii")


def layout_region_from_glm(
    raw_region: dict[str, Any],
    *,
    fallback_index: int,
) -> LayoutRegion:
    bbox = raw_region.get("bbox_2d")
    if not isinstance(bbox, list) or len(bbox) != 4:
        raise ValueError("Layout region is missing a four-coordinate bbox_2d")
    left, top, right, bottom = [float(value) / 1000 for value in bbox]
    raw_polygon = raw_region.get("polygon") or []
    if not isinstance(raw_polygon, list):
        raise ValueError("Layout region polygon must be a list")
    polygon = []
    for point in raw_polygon:
        if not isinstance(point, (list, tuple)) or len(point) != 2:
            raise ValueError("Layout region polygon points must contain two coordinates")
        polygon.append([float(point[0]) / 1000, float(point[1]) / 1000])
    index = int(raw_region.get("index", fallback_index))
    label = str(raw_region.get("label") or "text")
    return LayoutRegion(
        provider_region_id=f"glm-region-{index}",
        reading_order=index,
        label=label,
        task_type=str(raw_region.get("task_type") or glm_task_type(label)),
        layout_confidence=normalize_layout_confidence(raw_region.get("score")),
        bbox_left=left,
        bbox_top=top,
        bbox_width=right - left,
        bbox_height=bottom - top,
        polygon=polygon,
    )


def glm_task_type(label: str) -> str:
    if label == "table":
        return "table"
    if label in {"display_formula", "inline_formula"}:
        return "formula"
    return "text"


def normalize_layout_confidence(value: Any) -> Optional[float]:
    if value is None:
        return None
    confidence = float(value)
    if not 0 <= confidence <= 1:
        raise ValueError("PP-DocLayout confidence must use the documented 0-1 scale")
    return confidence * 100


def validate_layout_region(region: LayoutRegion) -> None:
    values = (
        region.bbox_left,
        region.bbox_top,
        region.bbox_width,
        region.bbox_height,
    )
    if not all(0 <= value <= 1 for value in values):
        raise ValueError(
            f"Layout region {region.provider_region_id} has out-of-range geometry"
        )
    if region.bbox_width <= 0 or region.bbox_height <= 0:
        raise ValueError(
            f"Layout region {region.provider_region_id} has empty geometry"
        )
    if region.bbox_left + region.bbox_width > 1.000001:
        raise ValueError(
            f"Layout region {region.provider_region_id} extends past page width"
        )
    if region.bbox_top + region.bbox_height > 1.000001:
        raise ValueError(
            f"Layout region {region.provider_region_id} extends past page height"
        )
    if region.polygon:
        if len(region.polygon) < 3:
            raise ValueError(
                f"Layout region {region.provider_region_id} polygon has fewer than three points"
            )
        for point in region.polygon:
            if len(point) != 2 or not all(0 <= coordinate <= 1 for coordinate in point):
                raise ValueError(
                    f"Layout region {region.provider_region_id} has out-of-range polygon geometry"
                )


def crop_layout_region(
    image: Any,
    region: LayoutRegion,
    *,
    padding_ratio: float = 0.01,
    max_dimension_px: int = 2048,
) -> Any:
    if not 0 <= padding_ratio <= 0.05:
        raise ValueError("Layout crop padding must be between 0 and 0.05")
    if max_dimension_px < 512:
        raise ValueError("Layout crop maximum dimension must be at least 512")
    width, height = image.size
    left = round(max(0, region.bbox_left - padding_ratio) * width)
    top = round(max(0, region.bbox_top - padding_ratio) * height)
    right = round(
        min(1, region.bbox_left + region.bbox_width + padding_ratio) * width
    )
    bottom = round(
        min(1, region.bbox_top + region.bbox_height + padding_ratio) * height
    )
    crop = image.crop((left, top, right, bottom))
    longest_edge = max(crop.size)
    if longest_edge <= max_dimension_px:
        return crop
    from PIL import Image

    scale = max_dimension_px / longest_edge
    resized = (
        max(1, round(crop.width * scale)),
        max(1, round(crop.height * scale)),
    )
    return crop.resize(resized, Image.Resampling.LANCZOS)


def render_upload_pages(
    document_bytes: bytes,
    *,
    original_filename: str,
    content_type: str,
    max_pdf_pages: Optional[int],
    dpi: int,
) -> list[Any]:
    try:
        from PIL import Image
    except ImportError as exc:
        raise RuntimeError(
            "Pillow is required when PAPRNAV_OCR_PROVIDER=layout_first_vlm"
        ) from exc

    is_pdf = content_type == "application/pdf" or original_filename.lower().endswith(
        ".pdf"
    )
    if not is_pdf:
        image = Image.open(BytesIO(document_bytes))
        image.load()
        return [image.convert("RGB")]

    try:
        import pymupdf
    except ImportError as exc:
        raise RuntimeError(
            "PyMuPDF is required for PDF layout-first OCR; install "
            "requirements-layout-ocr.txt"
        ) from exc

    document = pymupdf.open(stream=document_bytes, filetype="pdf")
    try:
        page_count = len(document)
        if max_pdf_pages is not None and page_count > max_pdf_pages:
            raise ValueError(
                f"Refusing to OCR {page_count} PDF pages; "
                f"PAPRNAV_OCR_MAX_PDF_PAGES is {max_pdf_pages}"
            )
        pages = []
        for page in document:
            pixmap = page.get_pixmap(dpi=dpi, alpha=False)
            image = Image.open(BytesIO(pixmap.tobytes("png")))
            image.load()
            pages.append(image.convert("RGB"))
        return pages
    finally:
        document.close()
