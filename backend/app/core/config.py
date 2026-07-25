import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Optional


DEFAULT_CORS_ORIGINS = (
    "http://localhost:3000",
    "http://127.0.0.1:3000",
)


def parse_csv(value: Optional[str], default: tuple[str, ...]) -> list[str]:
    if not value:
        return list(default)

    return [item.strip() for item in value.split(",") if item.strip()]


def load_local_env_file() -> None:
    if os.getenv("PAPRNAV_DISABLE_DOTENV") == "1":
        return
    env_path = Path(__file__).resolve().parents[2] / ".env"
    if not env_path.is_file():
        return
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


@dataclass(frozen=True)
class Settings:
    app_name: str
    app_version: str
    environment: str
    database_url: str
    cors_origins: list[str]
    local_storage_path: str
    storage_backend: str
    s3_upload_bucket: Optional[str]
    s3_upload_prefix: str
    max_upload_size_bytes: int
    ocr_max_pdf_pages: Optional[int]
    ocr_provider: str
    aws_region: str
    textract_s3_bucket: Optional[str]
    textract_s3_prefix: str
    textract_api_mode: str
    textract_analysis_feature_types: list[str]
    textract_async_poll_seconds: float
    textract_async_timeout_seconds: float
    textract_estimated_unit_cost_usd_per_page: float
    mistral_api_key: Optional[str]
    mistral_base_url: str
    mistral_ocr_model: str
    mistral_ocr_channel: str
    mistral_sagemaker_endpoint_name: Optional[str]
    mistral_sagemaker_region: Optional[str]
    mistral_ocr_mode: str
    mistral_ocr_timeout_seconds: float
    mistral_ocr_max_pdf_pages: Optional[int]
    layout_first_layout_model: str
    layout_first_layout_device: str
    layout_first_layout_threshold: float
    layout_first_recognition_model: str
    layout_first_ollama_base_url: str
    layout_first_timeout_seconds: float
    layout_first_pdf_dpi: int
    layout_first_compute_rate_usd_per_hour: float
    ad_extraction_provider: str
    openai_api_key: Optional[str]
    openai_base_url: str
    openai_ad_extraction_model: str
    ad_extraction_timeout_seconds: float


@lru_cache
def get_settings() -> Settings:
    load_local_env_file()
    return Settings(
        app_name=os.getenv("PAPRNAV_APP_NAME", "paprnav"),
        app_version=os.getenv("PAPRNAV_APP_VERSION", "0.1.0"),
        environment=os.getenv("PAPRNAV_ENV", "local"),
        database_url=os.getenv(
            "DATABASE_URL",
            "postgresql+psycopg://paprnav_user:paprnav_password@localhost:5432/paprnav_db",
        ),
        cors_origins=parse_csv(os.getenv("PAPRNAV_CORS_ORIGINS"), DEFAULT_CORS_ORIGINS),
        local_storage_path=os.getenv("PAPRNAV_LOCAL_STORAGE_PATH", ".data"),
        storage_backend=os.getenv("PAPRNAV_STORAGE_BACKEND", "local").strip().lower(),
        s3_upload_bucket=os.getenv("PAPRNAV_S3_UPLOAD_BUCKET") or None,
        s3_upload_prefix=os.getenv("PAPRNAV_S3_UPLOAD_PREFIX", "uploads").strip("/"),
        max_upload_size_bytes=int(os.getenv("PAPRNAV_MAX_UPLOAD_SIZE_BYTES", str(100 * 1024 * 1024))),
        ocr_max_pdf_pages=int(os.getenv("PAPRNAV_OCR_MAX_PDF_PAGES", "3")) if os.getenv("PAPRNAV_OCR_MAX_PDF_PAGES", "3") else None,
        ocr_provider=os.getenv("PAPRNAV_OCR_PROVIDER", "deterministic").strip().lower(),
        aws_region=os.getenv("AWS_REGION", os.getenv("AWS_DEFAULT_REGION", "us-east-1")),
        textract_s3_bucket=os.getenv("PAPRNAV_TEXTRACT_S3_BUCKET") or None,
        textract_s3_prefix=os.getenv("PAPRNAV_TEXTRACT_S3_PREFIX", "textract-input").strip("/"),
        textract_api_mode=os.getenv("PAPRNAV_TEXTRACT_API_MODE", "sync").strip().lower(),
        textract_analysis_feature_types=parse_csv(
            os.getenv("PAPRNAV_TEXTRACT_ANALYSIS_FEATURE_TYPES"),
            ("LAYOUT", "TABLES", "SIGNATURES"),
        ),
        textract_async_poll_seconds=float(os.getenv("PAPRNAV_TEXTRACT_ASYNC_POLL_SECONDS", "2")),
        textract_async_timeout_seconds=float(os.getenv("PAPRNAV_TEXTRACT_ASYNC_TIMEOUT_SECONDS", "300")),
        textract_estimated_unit_cost_usd_per_page=float(
            os.getenv("PAPRNAV_TEXTRACT_ESTIMATED_UNIT_COST_USD_PER_PAGE", "0")
        ),
        mistral_api_key=os.getenv("PAPRNAV_MISTRAL_API_KEY") or None,
        mistral_base_url=os.getenv("PAPRNAV_MISTRAL_BASE_URL", "https://api.mistral.ai/v1").rstrip("/"),
        mistral_ocr_model=os.getenv("PAPRNAV_MISTRAL_OCR_MODEL", "mistral-ocr-4-0"),
        mistral_ocr_channel=os.getenv("PAPRNAV_MISTRAL_OCR_CHANNEL", "direct_api").strip().lower(),
        mistral_sagemaker_endpoint_name=os.getenv("PAPRNAV_MISTRAL_SAGEMAKER_ENDPOINT_NAME") or None,
        mistral_sagemaker_region=os.getenv("PAPRNAV_MISTRAL_SAGEMAKER_REGION") or None,
        mistral_ocr_mode=os.getenv("PAPRNAV_MISTRAL_OCR_MODE", "ab_test").strip().lower(),
        mistral_ocr_timeout_seconds=float(os.getenv("PAPRNAV_MISTRAL_OCR_TIMEOUT_SECONDS", "120")),
        mistral_ocr_max_pdf_pages=(
            int(os.getenv("PAPRNAV_MISTRAL_OCR_MAX_PDF_PAGES", "3"))
            if os.getenv("PAPRNAV_MISTRAL_OCR_MAX_PDF_PAGES", "3")
            else None
        ),
        layout_first_layout_model=os.getenv(
            "PAPRNAV_LAYOUT_FIRST_LAYOUT_MODEL",
            "PaddlePaddle/PP-DocLayoutV3_safetensors",
        ),
        layout_first_layout_device=os.getenv(
            "PAPRNAV_LAYOUT_FIRST_LAYOUT_DEVICE",
            "cpu",
        ).strip(),
        layout_first_layout_threshold=float(
            os.getenv("PAPRNAV_LAYOUT_FIRST_LAYOUT_THRESHOLD", "0.3")
        ),
        layout_first_recognition_model=os.getenv(
            "PAPRNAV_LAYOUT_FIRST_RECOGNITION_MODEL",
            "glm-ocr:latest",
        ),
        layout_first_ollama_base_url=os.getenv(
            "PAPRNAV_LAYOUT_FIRST_OLLAMA_BASE_URL",
            "http://127.0.0.1:11434",
        ).rstrip("/"),
        layout_first_timeout_seconds=float(
            os.getenv("PAPRNAV_LAYOUT_FIRST_TIMEOUT_SECONDS", "120")
        ),
        layout_first_pdf_dpi=int(
            os.getenv("PAPRNAV_LAYOUT_FIRST_PDF_DPI", "200")
        ),
        layout_first_compute_rate_usd_per_hour=float(
            os.getenv(
                "PAPRNAV_LAYOUT_FIRST_COMPUTE_RATE_USD_PER_HOUR",
                "0",
            )
        ),
        ad_extraction_provider=os.getenv("PAPRNAV_AD_EXTRACTION_PROVIDER", "deterministic").strip().lower(),
        openai_api_key=os.getenv("PAPRNAV_OPENAI_API_KEY") or None,
        openai_base_url=os.getenv("PAPRNAV_OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/"),
        openai_ad_extraction_model=os.getenv("PAPRNAV_AD_EXTRACTION_MODEL", "gpt-5.5"),
        ad_extraction_timeout_seconds=float(os.getenv("PAPRNAV_AD_EXTRACTION_TIMEOUT_SECONDS", "30")),
    )
