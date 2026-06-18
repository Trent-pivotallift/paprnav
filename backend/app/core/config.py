import os
from dataclasses import dataclass
from functools import lru_cache
from typing import Optional


DEFAULT_CORS_ORIGINS = (
    "http://localhost:3000",
    "http://127.0.0.1:3000",
)


def parse_csv(value: Optional[str], default: tuple[str, ...]) -> list[str]:
    if not value:
        return list(default)

    return [item.strip() for item in value.split(",") if item.strip()]


@dataclass(frozen=True)
class Settings:
    app_name: str
    app_version: str
    environment: str
    database_url: str
    cors_origins: list[str]
    local_storage_path: str
    max_upload_size_bytes: int


@lru_cache
def get_settings() -> Settings:
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
        max_upload_size_bytes=int(os.getenv("PAPRNAV_MAX_UPLOAD_SIZE_BYTES", str(100 * 1024 * 1024))),
    )
