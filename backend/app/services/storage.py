import hashlib
import re
import tempfile
from pathlib import Path
from typing import Any, BinaryIO, Mapping, Optional
from urllib.parse import urlencode

from app.core.config import Settings


FILENAME_SAFE_PATTERN = re.compile(r"[^A-Za-z0-9._-]+")


class StoredFile:
    def __init__(self, storage_key: str, file_size_bytes: int, sha256: str, storage_backend: str = "local") -> None:
        self.storage_key = storage_key
        self.file_size_bytes = file_size_bytes
        self.sha256 = sha256
        self.storage_backend = storage_backend


def safe_filename(filename: str) -> str:
    name = Path(filename).name.strip() or "upload.bin"
    return FILENAME_SAFE_PATTERN.sub("_", name)


def store_local_file(
    source: BinaryIO,
    storage_root: str,
    aircraft_id: str,
    upload_id: str,
    original_filename: str,
    max_size_bytes: int,
) -> StoredFile:
    filename = safe_filename(original_filename)
    storage_key = f"uploads/{aircraft_id}/{upload_id}/{filename}"
    destination = Path(storage_root) / storage_key
    destination.parent.mkdir(parents=True, exist_ok=True)

    digest = hashlib.sha256()
    total_bytes = 0
    try:
        with destination.open("wb") as output:
            while True:
                chunk = source.read(1024 * 1024)
                if not chunk:
                    break
                total_bytes += len(chunk)
                if total_bytes > max_size_bytes:
                    raise ValueError("Uploaded file is too large")
                digest.update(chunk)
                output.write(chunk)
    except Exception:
        destination.unlink(missing_ok=True)
        raise

    return StoredFile(storage_key=storage_key, file_size_bytes=total_bytes, sha256=digest.hexdigest())


def get_s3_client(region_name: str) -> Any:
    try:
        import boto3
    except ImportError as exc:
        raise RuntimeError("boto3 is required when PAPRNAV_STORAGE_BACKEND=s3") from exc

    return boto3.client("s3", region_name=region_name)


def s3_upload_key(prefix: str, aircraft_id: str, upload_id: str, original_filename: str) -> str:
    filename = safe_filename(original_filename)
    cleaned_prefix = prefix.strip("/")
    path = f"{aircraft_id}/{upload_id}/{filename}"
    return f"{cleaned_prefix}/{path}" if cleaned_prefix else path


def derived_storage_key(prefix: str, aircraft_id: str, upload_id: str, filename: str) -> str:
    cleaned_prefix = prefix.strip("/")
    path = f"{aircraft_id}/{upload_id}/{safe_filename(filename)}"
    return f"{cleaned_prefix}/{path}" if cleaned_prefix else path


def store_s3_file(
    source: BinaryIO,
    *,
    bucket: str,
    key: str,
    content_type: str,
    max_size_bytes: int,
    cost_allocation_tags: Mapping[str, str],
    client: Optional[Any] = None,
    region_name: str = "us-east-1",
) -> StoredFile:
    digest = hashlib.sha256()
    total_bytes = 0

    with tempfile.SpooledTemporaryFile(max_size=min(max_size_bytes, 16 * 1024 * 1024), mode="w+b") as upload_buffer:
        while True:
            chunk = source.read(1024 * 1024)
            if not chunk:
                break
            total_bytes += len(chunk)
            if total_bytes > max_size_bytes:
                raise ValueError("Uploaded file is too large")
            digest.update(chunk)
            upload_buffer.write(chunk)

        upload_buffer.seek(0)
        s3_client = client or get_s3_client(region_name)
        s3_client.upload_fileobj(
            upload_buffer,
            bucket,
            key,
            ExtraArgs={
                "ContentType": content_type,
                "ServerSideEncryption": "AES256",
                "Tagging": urlencode(cost_allocation_tags),
            },
        )

    return StoredFile(
        storage_key=key,
        file_size_bytes=total_bytes,
        sha256=digest.hexdigest(),
        storage_backend="s3",
    )


def store_bytes(
    data: bytes,
    *,
    settings: Settings,
    storage_key: str,
    content_type: str,
    cost_allocation_tags: Mapping[str, str],
) -> StoredFile:
    digest = hashlib.sha256(data).hexdigest()
    if settings.storage_backend == "s3":
        if not settings.s3_upload_bucket:
            raise ValueError("PAPRNAV_S3_UPLOAD_BUCKET is required when PAPRNAV_STORAGE_BACKEND=s3")
        get_s3_client(settings.aws_region).put_object(
            Bucket=settings.s3_upload_bucket,
            Key=storage_key,
            Body=data,
            ContentType=content_type,
            ServerSideEncryption="AES256",
            Tagging=urlencode(cost_allocation_tags),
        )
        return StoredFile(
            storage_key=storage_key,
            file_size_bytes=len(data),
            sha256=digest,
            storage_backend="s3",
        )

    if settings.storage_backend != "local":
        raise ValueError(f"Unknown upload storage backend: {settings.storage_backend}")

    destination = Path(settings.local_storage_path) / storage_key
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(data)
    return StoredFile(storage_key=storage_key, file_size_bytes=len(data), sha256=digest)


def read_stored_file_bytes(
    *,
    settings: Settings,
    storage_backend: str,
    storage_key: str,
) -> bytes:
    if storage_backend == "s3":
        if not settings.s3_upload_bucket:
            raise ValueError("PAPRNAV_S3_UPLOAD_BUCKET is required when PAPRNAV_STORAGE_BACKEND=s3")
        response = get_s3_client(settings.aws_region).get_object(Bucket=settings.s3_upload_bucket, Key=storage_key)
        return response["Body"].read()

    if storage_backend != "local":
        raise ValueError(f"Unknown upload storage backend: {storage_backend}")

    root = Path(settings.local_storage_path).resolve()
    path = (root / storage_key).resolve()
    if root not in path.parents and path != root:
        raise ValueError("Invalid storage key")
    return path.read_bytes()


def store_upload_file(
    source: BinaryIO,
    *,
    settings: Settings,
    aircraft_id: str,
    upload_id: str,
    original_filename: str,
    content_type: str,
    max_size_bytes: int,
    cost_allocation_tags: Mapping[str, str],
) -> StoredFile:
    if settings.storage_backend == "s3":
        if not settings.s3_upload_bucket:
            raise ValueError("PAPRNAV_S3_UPLOAD_BUCKET is required when PAPRNAV_STORAGE_BACKEND=s3")
        key = s3_upload_key(settings.s3_upload_prefix, aircraft_id, upload_id, original_filename)
        return store_s3_file(
            source,
            bucket=settings.s3_upload_bucket,
            key=key,
            content_type=content_type,
            max_size_bytes=max_size_bytes,
            cost_allocation_tags=cost_allocation_tags,
            region_name=settings.aws_region,
        )

    if settings.storage_backend != "local":
        raise ValueError(f"Unknown upload storage backend: {settings.storage_backend}")

    return store_local_file(
        source=source,
        storage_root=settings.local_storage_path,
        aircraft_id=aircraft_id,
        upload_id=upload_id,
        original_filename=original_filename,
        max_size_bytes=max_size_bytes,
    )
