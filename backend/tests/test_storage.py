from io import BytesIO
from urllib.parse import parse_qs

import pytest

from app.core.config import Settings
from app.services.storage import s3_upload_key, store_s3_file, store_upload_file


class FakeS3Client:
    def __init__(self) -> None:
        self.calls = []

    def upload_fileobj(self, fileobj, bucket: str, key: str, ExtraArgs: dict) -> None:
        self.calls.append(
            {
                "body": fileobj.read(),
                "bucket": bucket,
                "key": key,
                "extra_args": ExtraArgs,
            }
        )


def test_store_s3_file_uploads_with_billing_tags_and_hash() -> None:
    client = FakeS3Client()
    tags = {
        "Project": "paprnav",
        "CustomerAccount": "acct-test",
        "Aircraft": "aircraft-n123ab",
        "BillableAccount": "acct-test",
        "BillingStage": "initial-ocr",
    }

    stored_file = store_s3_file(
        BytesIO(b"logbook bytes"),
        bucket="paprnav-pilot-artifacts-527257972989",
        key="uploads/ac_1/upl_1/logbook.pdf",
        content_type="application/pdf",
        max_size_bytes=1024,
        cost_allocation_tags=tags,
        client=client,
    )

    assert stored_file.storage_backend == "s3"
    assert stored_file.storage_key == "uploads/ac_1/upl_1/logbook.pdf"
    assert stored_file.file_size_bytes == len(b"logbook bytes")
    assert stored_file.sha256 == "cb6f639de9e9001517a12f7185cf9e241d74aedfed7589bb7b7a5d164da52519"
    assert client.calls == [
        {
            "body": b"logbook bytes",
            "bucket": "paprnav-pilot-artifacts-527257972989",
            "key": "uploads/ac_1/upl_1/logbook.pdf",
            "extra_args": {
                "ContentType": "application/pdf",
                "ServerSideEncryption": "AES256",
                "Tagging": client.calls[0]["extra_args"]["Tagging"],
            },
        }
    ]
    assert parse_qs(client.calls[0]["extra_args"]["Tagging"]) == {key: [value] for key, value in tags.items()}


def test_s3_upload_key_uses_safe_filename_and_prefix() -> None:
    assert s3_upload_key("uploads", "ac_1", "upl_1", "../Log Book 1.pdf") == "uploads/ac_1/upl_1/Log_Book_1.pdf"


def test_store_upload_file_requires_bucket_for_s3_backend() -> None:
    settings = Settings(
        app_name="paprnav",
        app_version="0.1.0",
        environment="test",
        database_url="sqlite://",
        cors_origins=[],
        local_storage_path=".data",
        storage_backend="s3",
        s3_upload_bucket=None,
        s3_upload_prefix="uploads",
        max_upload_size_bytes=1024,
        ocr_max_pdf_pages=3,
        ocr_provider="deterministic",
        aws_region="us-east-1",
        textract_s3_bucket=None,
        textract_s3_prefix="textract-input",
        textract_api_mode="sync",
        textract_analysis_feature_types=["LAYOUT", "TABLES", "SIGNATURES"],
        textract_async_poll_seconds=0,
        textract_async_timeout_seconds=1,
        textract_estimated_unit_cost_usd_per_page=0,
        mistral_api_key=None,
        mistral_base_url="https://api.mistral.ai/v1",
        mistral_ocr_model="mistral-ocr-4-0",
        mistral_ocr_channel="direct_api",
        mistral_sagemaker_endpoint_name=None,
        mistral_sagemaker_region=None,
        mistral_ocr_mode="ab_test",
        mistral_ocr_timeout_seconds=120,
        mistral_ocr_max_pdf_pages=3,
        layout_first_layout_model="PaddlePaddle/PP-DocLayoutV3_safetensors",
        layout_first_layout_device="cpu",
        layout_first_layout_threshold=0.3,
        layout_first_recognition_model="glm-ocr:latest",
        layout_first_ollama_base_url="http://127.0.0.1:11434",
        layout_first_timeout_seconds=120,
        layout_first_pdf_dpi=200,
        layout_first_compute_rate_usd_per_hour=0,
        ad_extraction_provider="deterministic",
        openai_api_key=None,
        openai_base_url="https://api.openai.com/v1",
        openai_ad_extraction_model="gpt-5.5",
        ad_extraction_timeout_seconds=30,
    )

    with pytest.raises(ValueError, match="PAPRNAV_S3_UPLOAD_BUCKET"):
        store_upload_file(
            BytesIO(b"logbook bytes"),
            settings=settings,
            aircraft_id="ac_1",
            upload_id="upl_1",
            original_filename="logbook.pdf",
            content_type="application/pdf",
            max_size_bytes=1024,
            cost_allocation_tags={"Project": "paprnav"},
        )
