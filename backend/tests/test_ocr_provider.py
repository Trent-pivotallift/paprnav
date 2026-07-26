from pathlib import Path
from io import BytesIO

import pytest
from pypdf import PdfWriter

from app.core.config import get_settings
from app.services.ocr_provider import MistralOCRProvider, TextractOCRProvider, get_ocr_provider


class FakeTextractClient:
    def __init__(self, response: dict) -> None:
        self.response = response
        self.document = None

    def detect_document_text(self, *, Document: dict) -> dict:
        self.document = Document
        return self.response


class FakeAsyncTextractClient:
    def __init__(self, responses: list[dict]) -> None:
        self.responses = responses
        self.document_location = None
        self.requests = []

    def start_document_text_detection(self, *, DocumentLocation: dict) -> dict:
        self.document_location = DocumentLocation
        return {"JobId": "job-123"}

    def start_document_analysis(self, *, DocumentLocation: dict, FeatureTypes: list[str]) -> dict:
        self.document_location = DocumentLocation
        self.feature_types = FeatureTypes
        return {"JobId": "job-456"}

    def get_document_text_detection(self, **request: dict) -> dict:
        self.requests.append(request)
        return self.responses.pop(0)

    def get_document_analysis(self, **request: dict) -> dict:
        self.requests.append(request)
        return self.responses.pop(0)


class FakeS3Client:
    def __init__(self, body: bytes) -> None:
        self.body = body
        self.requests = []

    def get_object(self, *, Bucket: str, Key: str) -> dict:
        self.requests.append({"Bucket": Bucket, "Key": Key})
        return {"Body": BytesIO(self.body)}


class FakeHTTPResponse:
    def __init__(self, response: dict) -> None:
        self.response = response

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict:
        return self.response


class FakeHTTPClient:
    def __init__(self, response: dict) -> None:
        self.response = response
        self.requests = []

    def post(self, url: str, **kwargs) -> FakeHTTPResponse:
        self.requests.append({"url": url, **kwargs})
        return FakeHTTPResponse(self.response)


def pdf_bytes(page_count: int) -> bytes:
    writer = PdfWriter()
    for _ in range(page_count):
        writer.add_blank_page(width=72, height=72)
    output = BytesIO()
    writer.write(output)
    return output.getvalue()


def textract_response() -> dict:
    return {
        "DetectDocumentTextModelVersion": "1.0",
        "DocumentMetadata": {"Pages": 1},
        "Blocks": [
            {
                "BlockType": "LINE",
                "Id": "line-1",
                "Text": "2026-03-01 Replaced ELT battery.",
                "Confidence": 97.5,
                "Page": 1,
                "Geometry": {
                    "BoundingBox": {"Left": 0.1, "Top": 0.2, "Width": 0.7, "Height": 0.03},
                    "RotationAngle": 0,
                },
                "Relationships": [{"Type": "CHILD", "Ids": ["word-1"]}],
            },
            {
                "BlockType": "WORD",
                "Id": "word-1",
                "Text": "2026-03-01",
                "Confidence": 96.0,
                "Page": 1,
                "Geometry": {
                    "BoundingBox": {"Left": 0.1, "Top": 0.2, "Width": 0.12, "Height": 0.03},
                },
            },
        ],
    }


def textract_analysis_response() -> dict:
    return {
        "AnalyzeDocumentModelVersion": "1.0",
        "DocumentMetadata": {"Pages": 1},
        "Blocks": [
            {
                "BlockType": "LAYOUT_HEADER",
                "Id": "layout-header-1",
                "Text": "Description of Inspections, Tests, Repairs and Alterations",
                "Confidence": 98.0,
                "Page": 1,
                "Geometry": {
                    "BoundingBox": {"Left": 0.35, "Top": 0.04, "Width": 0.55, "Height": 0.04},
                    "RotationAngle": 0,
                },
            },
            {
                "BlockType": "TABLE",
                "Id": "table-1",
                "Confidence": 92.0,
                "Page": 1,
                "Geometry": {"BoundingBox": {"Left": 0.02, "Top": 0.04, "Width": 0.96, "Height": 0.88}},
                "Relationships": [{"Type": "CHILD", "Ids": ["cell-1"]}],
            },
            {
                "BlockType": "CELL",
                "Id": "cell-1",
                "Confidence": 91.0,
                "Page": 1,
                "RowIndex": 2,
                "ColumnIndex": 5,
                "RowSpan": 1,
                "ColumnSpan": 1,
                "Geometry": {"BoundingBox": {"Left": 0.30, "Top": 0.24, "Width": 0.62, "Height": 0.12}},
                "Relationships": [{"Type": "CHILD", "Ids": ["line-1"]}],
            },
            {
                "BlockType": "LINE",
                "Id": "line-1",
                "Text": "12-17-12 Tach = 1276.8 Total Time = 5405.5",
                "Confidence": 89.5,
                "Page": 1,
                "Geometry": {"BoundingBox": {"Left": 0.31, "Top": 0.25, "Width": 0.58, "Height": 0.03}},
            },
            {
                "BlockType": "SIGNATURE",
                "Id": "signature-1",
                "Confidence": 84.0,
                "Page": 1,
                "Geometry": {"BoundingBox": {"Left": 0.48, "Top": 0.66, "Width": 0.18, "Height": 0.08}},
            },
        ],
    }


def mistral_response() -> dict:
    return {
        "model": "mistral-ocr-4-0",
        "pages": [
            {
                "index": 0,
                "markdown": "12-17-12 Tach = 1276.8 Total Time = 5405.5\nELT battery replaced.",
                "dimensions": {"width": 1700, "height": 2200, "dpi": 200},
                "confidence_scores": {"average_page_confidence_score": 0.91},
                "blocks": [
                    {
                        "id": "block-1",
                        "type": "paragraph",
                        "content": "12-17-12 Tach = 1276.8 Total Time = 5405.5",
                        "top_left_x": 170,
                        "top_left_y": 220,
                        "bottom_right_x": 1530,
                        "bottom_right_y": 330,
                    }
                ],
            }
        ],
        "usage_info": {"pages_processed": 1, "doc_size_bytes": 1200},
    }


def test_textract_provider_maps_blocks_to_ocr_result(tmp_path: Path) -> None:
    storage_root = tmp_path / "storage"
    upload_path = storage_root / "uploads" / "aircraft" / "upload" / "logbook.png"
    upload_path.parent.mkdir(parents=True)
    upload_path.write_bytes(b"fake image bytes")
    client = FakeTextractClient(textract_response())

    provider = TextractOCRProvider(client=client, storage_root=str(storage_root))
    result = provider.process_upload(
        original_filename="logbook.png",
        content_type="image/png",
        storage_backend="local",
        storage_key="uploads/aircraft/upload/logbook.png",
    )

    assert client.document == {"Bytes": b"fake image bytes"}
    assert result.provider_name == "aws_textract"
    assert result.provider_version == "1.0"
    assert len(result.pages) == 1
    assert result.pages[0].extraction_confidence == 97.5
    assert [span.span_type for span in result.pages[0].spans] == ["LINE", "WORD"]
    assert result.pages[0].spans[0].bbox_units == "ratio"
    assert result.pages[0].spans[0].relationships[0] == {"Type": "CHILD", "Ids": ["word-1"]}
    assert result.pages[0].spans[0].relationships[-1]["block_metadata"]["BlockType"] == "LINE"


def test_ocr_provider_selection_uses_textract_when_enabled(monkeypatch) -> None:
    monkeypatch.setenv("PAPRNAV_OCR_PROVIDER", "textract")
    get_settings.cache_clear()

    provider = get_ocr_provider()

    assert isinstance(provider, TextractOCRProvider)
    get_settings.cache_clear()


def test_ocr_provider_selection_uses_mistral_when_enabled(monkeypatch) -> None:
    monkeypatch.setenv("PAPRNAV_OCR_PROVIDER", "mistral")
    monkeypatch.setenv("PAPRNAV_MISTRAL_API_KEY", "test-key")
    get_settings.cache_clear()

    provider = get_ocr_provider()

    assert isinstance(provider, MistralOCRProvider)
    get_settings.cache_clear()


def test_textract_provider_uses_upload_bucket_for_s3_backed_uploads(monkeypatch) -> None:
    monkeypatch.setenv("PAPRNAV_S3_UPLOAD_BUCKET", "paprnav-upload-bucket")
    monkeypatch.setenv("PAPRNAV_TEXTRACT_S3_BUCKET", "paprnav-textract-staging-bucket")
    get_settings.cache_clear()
    client = FakeTextractClient(textract_response())
    s3_client = FakeS3Client(pdf_bytes(1))
    provider = TextractOCRProvider(client=client, s3_client=s3_client)

    provider.process_upload(
        original_filename="logbook.png",
        content_type="image/png",
        storage_backend="s3",
        storage_key="uploads/ac_1/upl_1/logbook.png",
    )

    assert client.document == {
        "S3Object": {
            "Bucket": "paprnav-upload-bucket",
            "Name": "uploads/ac_1/upl_1/logbook.png",
        }
    }
    get_settings.cache_clear()


def test_textract_sync_provider_rejects_pdf(tmp_path: Path) -> None:
    storage_root = tmp_path / "storage"
    upload_path = storage_root / "uploads" / "aircraft" / "upload" / "logbook.pdf"
    upload_path.parent.mkdir(parents=True)
    upload_path.write_bytes(b"%PDF-1.4 multipage")
    provider = TextractOCRProvider(client=FakeTextractClient(textract_response()), storage_root=str(storage_root))

    with pytest.raises(ValueError, match="does not support PDF"):
        provider.process_upload(
            original_filename="logbook.pdf",
            content_type="application/pdf",
            storage_backend="local",
            storage_key="uploads/aircraft/upload/logbook.pdf",
        )


def test_textract_async_provider_processes_s3_pdf(monkeypatch) -> None:
    monkeypatch.setenv("PAPRNAV_S3_UPLOAD_BUCKET", "paprnav-upload-bucket")
    monkeypatch.setenv("PAPRNAV_TEXTRACT_API_MODE", "async")
    monkeypatch.setenv("PAPRNAV_TEXTRACT_ASYNC_POLL_SECONDS", "0")
    get_settings.cache_clear()
    client = FakeAsyncTextractClient(
        [
            {
                "JobStatus": "IN_PROGRESS",
            },
            {
                "JobStatus": "SUCCEEDED",
                "DocumentMetadata": {"Pages": 1},
                "DetectDocumentTextModelVersion": "1.0",
                "Blocks": textract_response()["Blocks"],
            },
        ]
    )
    s3_client = FakeS3Client(pdf_bytes(1))
    provider = TextractOCRProvider(client=client, s3_client=s3_client)

    result = provider.process_upload(
        original_filename="logbook.pdf",
        content_type="application/pdf",
        storage_backend="s3",
        storage_key="uploads/ac_1/upl_1/logbook.pdf",
    )

    assert client.document_location == {
        "S3Object": {
            "Bucket": "paprnav-upload-bucket",
            "Name": "uploads/ac_1/upl_1/logbook.pdf",
        }
    }
    assert client.requests == [{"JobId": "job-123"}, {"JobId": "job-123"}]
    assert s3_client.requests == [
        {
            "Bucket": "paprnav-upload-bucket",
            "Key": "uploads/ac_1/upl_1/logbook.pdf",
        }
    ]
    assert result.provider_version == "1.0"
    assert len(result.pages) == 1
    assert result.pages[0].spans[0].text == "2026-03-01 Replaced ELT battery."
    get_settings.cache_clear()


def test_textract_async_provider_rejects_pdf_over_page_guardrail(monkeypatch) -> None:
    monkeypatch.setenv("PAPRNAV_S3_UPLOAD_BUCKET", "paprnav-upload-bucket")
    monkeypatch.setenv("PAPRNAV_TEXTRACT_API_MODE", "async")
    monkeypatch.setenv("PAPRNAV_OCR_MAX_PDF_PAGES", "1")
    get_settings.cache_clear()
    provider = TextractOCRProvider(
        client=FakeAsyncTextractClient([]),
        s3_client=FakeS3Client(pdf_bytes(2)),
    )

    with pytest.raises(ValueError, match="Refusing to OCR 2 PDF pages"):
        provider.process_upload(
            original_filename="logbook.pdf",
            content_type="application/pdf",
            storage_backend="s3",
            storage_key="uploads/ac_1/upl_1/logbook.pdf",
        )
    get_settings.cache_clear()


def test_textract_async_provider_requires_s3(monkeypatch) -> None:
    monkeypatch.setenv("PAPRNAV_TEXTRACT_API_MODE", "async")
    get_settings.cache_clear()
    provider = TextractOCRProvider(client=FakeAsyncTextractClient([]))

    with pytest.raises(ValueError, match="requires an S3-backed upload"):
        provider.process_upload(
            original_filename="logbook.pdf",
            content_type="application/pdf",
            storage_backend="local",
            storage_key="uploads/ac_1/upl_1/logbook.pdf",
        )
    get_settings.cache_clear()


def test_textract_analysis_async_provider_processes_s3_pdf(monkeypatch) -> None:
    monkeypatch.setenv("PAPRNAV_S3_UPLOAD_BUCKET", "paprnav-upload-bucket")
    monkeypatch.setenv("PAPRNAV_TEXTRACT_API_MODE", "analysis_async")
    monkeypatch.setenv("PAPRNAV_TEXTRACT_ANALYSIS_FEATURE_TYPES", "LAYOUT,TABLES,SIGNATURES")
    monkeypatch.setenv("PAPRNAV_TEXTRACT_ASYNC_POLL_SECONDS", "0")
    monkeypatch.setenv(
        "PAPRNAV_TEXTRACT_ESTIMATED_UNIT_COST_USD_PER_PAGE",
        "0.015",
    )
    get_settings.cache_clear()
    client = FakeAsyncTextractClient(
        [
            {
                "JobStatus": "IN_PROGRESS",
            },
            {
                "JobStatus": "SUCCEEDED",
                **textract_analysis_response(),
            },
        ]
    )
    s3_client = FakeS3Client(pdf_bytes(1))
    provider = TextractOCRProvider(client=client, s3_client=s3_client)

    result = provider.process_upload(
        original_filename="logbook.pdf",
        content_type="application/pdf",
        storage_backend="s3",
        storage_key="uploads/ac_1/upl_1/logbook.pdf",
    )

    assert client.document_location == {
        "S3Object": {
            "Bucket": "paprnav-upload-bucket",
            "Name": "uploads/ac_1/upl_1/logbook.pdf",
        }
    }
    assert client.feature_types == ["LAYOUT", "TABLES", "SIGNATURES"]
    assert client.requests == [{"JobId": "job-456"}, {"JobId": "job-456"}]
    assert result.provider_name == "aws_textract"
    assert result.provider_version == "1.0"
    assert result.billable_page_count == 1
    assert result.metadata["provider_mode"] == "analysis_async"
    assert result.metadata["provider_channel"] == "aws"
    assert result.metadata["processing_seconds"] >= 0
    assert result.metadata["pricing_unit"] == "page"
    assert result.metadata["pricing_rate_usd"] == 0.015
    assert result.metadata["estimated_cost_usd"] == 0.015
    assert result.metadata["textract_block_counts"] == {
        "CELL": 1,
        "LAYOUT_HEADER": 1,
        "LINE": 1,
        "SIGNATURE": 1,
        "TABLE": 1,
    }
    assert [span.span_type for span in result.pages[0].spans] == [
        "LAYOUT_HEADER",
        "TABLE",
        "CELL",
        "LINE",
        "SIGNATURE",
    ]
    assert result.pages[0].spans[1].text == "[table]"
    assert result.pages[0].spans[2].text == "[cell r2 c5]"
    assert result.pages[0].spans[4].text == "[signature]"
    assert result.pages[0].spans[2].relationships[-1]["block_metadata"]["ColumnIndex"] == 5
    get_settings.cache_clear()


def test_textract_analysis_async_provider_requires_s3(monkeypatch) -> None:
    monkeypatch.setenv("PAPRNAV_TEXTRACT_API_MODE", "analysis_async")
    get_settings.cache_clear()
    provider = TextractOCRProvider(client=FakeAsyncTextractClient([]))

    with pytest.raises(ValueError, match="requires an S3-backed upload"):
        provider.process_upload(
            original_filename="logbook.pdf",
            content_type="application/pdf",
            storage_backend="local",
            storage_key="uploads/ac_1/upl_1/logbook.pdf",
        )
    get_settings.cache_clear()


def test_mistral_provider_posts_base64_pdf_with_page_guardrail(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("PAPRNAV_MISTRAL_API_KEY", "test-key")
    monkeypatch.setenv("PAPRNAV_MISTRAL_OCR_MODEL", "mistral-ocr-4-0")
    monkeypatch.setenv("PAPRNAV_MISTRAL_OCR_MAX_PDF_PAGES", "3")
    get_settings.cache_clear()
    storage_root = tmp_path / "storage"
    upload_path = storage_root / "uploads" / "aircraft" / "upload" / "logbook.pdf"
    upload_path.parent.mkdir(parents=True)
    upload_path.write_bytes(pdf_bytes(1))
    http_client = FakeHTTPClient(mistral_response())
    provider = MistralOCRProvider(http_client=http_client, storage_root=str(storage_root))

    result = provider.process_upload(
        original_filename="logbook.pdf",
        content_type="application/pdf",
        storage_backend="local",
        storage_key="uploads/aircraft/upload/logbook.pdf",
    )

    request = http_client.requests[0]
    assert request["url"] == "https://api.mistral.ai/v1/ocr"
    assert request["headers"]["Authorization"] == "Bearer test-key"
    assert request["json"]["model"] == "mistral-ocr-4-0"
    assert request["json"]["pages"] == [0]
    assert request["json"]["document"]["type"] == "document_url"
    assert request["json"]["document"]["document_url"].startswith("data:application/pdf;base64,")
    assert result.provider_name == "mistral_ocr"
    assert result.provider_version == "mistral-ocr-4-0"
    assert result.billable_page_count == 1
    assert result.metadata["third_party_processing"] is True
    assert result.metadata["processing_seconds"] >= 0
    assert result.metadata["pricing_unit"] == "page"
    assert result.metadata["pricing_rate_usd"] == 0.004
    assert result.metadata["estimated_cost_usd"] == 0.004
    assert len(result.pages) == 1
    assert result.pages[0].source_page_number == 1
    assert result.pages[0].extraction_confidence == 91.0
    assert [span.span_type for span in result.pages[0].spans] == ["PARAGRAPH", "LINE", "LINE"]
    assert result.pages[0].spans[0].bbox_left == pytest.approx(0.1)
    get_settings.cache_clear()


def test_mistral_provider_rejects_pdf_over_page_guardrail(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("PAPRNAV_MISTRAL_API_KEY", "test-key")
    monkeypatch.setenv("PAPRNAV_MISTRAL_OCR_MAX_PDF_PAGES", "1")
    get_settings.cache_clear()
    storage_root = tmp_path / "storage"
    upload_path = storage_root / "uploads" / "aircraft" / "upload" / "logbook.pdf"
    upload_path.parent.mkdir(parents=True)
    upload_path.write_bytes(pdf_bytes(2))
    provider = MistralOCRProvider(http_client=FakeHTTPClient(mistral_response()), storage_root=str(storage_root))

    with pytest.raises(ValueError, match="Refusing to OCR 2 PDF pages"):
        provider.process_upload(
            original_filename="logbook.pdf",
            content_type="application/pdf",
            storage_backend="local",
            storage_key="uploads/aircraft/upload/logbook.pdf",
        )
    get_settings.cache_clear()


def test_mistral_provider_requires_api_key(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.delenv("PAPRNAV_MISTRAL_API_KEY", raising=False)
    get_settings.cache_clear()
    storage_root = tmp_path / "storage"
    upload_path = storage_root / "uploads" / "aircraft" / "upload" / "logbook.pdf"
    upload_path.parent.mkdir(parents=True)
    upload_path.write_bytes(pdf_bytes(1))
    provider = MistralOCRProvider(http_client=FakeHTTPClient(mistral_response()), storage_root=str(storage_root))

    with pytest.raises(ValueError, match="PAPRNAV_MISTRAL_API_KEY"):
        provider.process_upload(
            original_filename="logbook.pdf",
            content_type="application/pdf",
            storage_backend="local",
            storage_key="uploads/aircraft/upload/logbook.pdf",
        )
    get_settings.cache_clear()
