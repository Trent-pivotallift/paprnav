import hashlib
import re
from pathlib import Path
from typing import BinaryIO


FILENAME_SAFE_PATTERN = re.compile(r"[^A-Za-z0-9._-]+")


class StoredFile:
    def __init__(self, storage_key: str, file_size_bytes: int, sha256: str) -> None:
        self.storage_key = storage_key
        self.file_size_bytes = file_size_bytes
        self.sha256 = sha256


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
