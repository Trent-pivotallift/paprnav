from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
from typing import Any


MANIFEST_PATH = Path(__file__).resolve().parents[3] / ".ai" / "OCR_BENCHMARK_PARTITIONS.json"


@dataclass(frozen=True)
class OCRBenchmarkSelection:
    manifest_version: str
    partition: str
    document: str
    source_sha256: str
    source_pages: list[int]


def load_ocr_benchmark_manifest() -> dict[str, Any]:
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def resolve_ocr_benchmark_selection(
    *,
    source_path: Path,
    document: str,
    partition: str,
) -> OCRBenchmarkSelection:
    manifest = load_ocr_benchmark_manifest()
    document_config = manifest["documents"].get(document)
    partition_config = manifest["partitions"].get(partition)
    if document_config is None:
        raise ValueError(f"Unknown benchmark document: {document}")
    if partition_config is None:
        raise ValueError(f"Unknown benchmark partition: {partition}")
    if source_path.name != document_config["filename"]:
        raise ValueError(
            f"Benchmark document {document} requires {document_config['filename']}"
        )
    source_hash = file_sha256(source_path)
    if source_hash != document_config["sha256"]:
        raise ValueError(
            f"Benchmark source hash mismatch for {document}: {source_hash}"
        )
    pages = partition_config["pages"][document]
    return OCRBenchmarkSelection(
        manifest_version=manifest["version"],
        partition=partition,
        document=document,
        source_sha256=source_hash,
        source_pages=list(pages),
    )


def materialize_ocr_benchmark_selection(
    *,
    source_path: Path,
    output_path: Path,
    selection: OCRBenchmarkSelection,
) -> None:
    from pypdf import PdfReader, PdfWriter

    reader = PdfReader(str(source_path))
    writer = PdfWriter()
    for page_number in selection.source_pages:
        if not 1 <= page_number <= len(reader.pages):
            raise ValueError(
                f"Benchmark page {page_number} is outside {source_path.name}"
            )
        writer.add_page(reader.pages[page_number - 1])
    with output_path.open("wb") as output:
        writer.write(output)


def file_sha256(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
