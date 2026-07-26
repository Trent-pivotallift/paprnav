from pathlib import Path

import pytest

from app.services.ocr_benchmark import (
    file_sha256,
    materialize_ocr_benchmark_selection,
    OCRBenchmarkSelection,
)


def test_materializes_only_selected_benchmark_pages(tmp_path: Path) -> None:
    from pypdf import PdfReader, PdfWriter

    source_path = tmp_path / "source.pdf"
    writer = PdfWriter()
    for width in (100, 200, 300):
        writer.add_blank_page(width=width, height=400)
    with source_path.open("wb") as output:
        writer.write(output)

    selection = OCRBenchmarkSelection(
        manifest_version="test",
        partition="ocr_refinement",
        document="aircraft",
        source_sha256=file_sha256(source_path),
        source_pages=[1, 3],
    )
    output_path = tmp_path / "selected.pdf"
    materialize_ocr_benchmark_selection(
        source_path=source_path,
        output_path=output_path,
        selection=selection,
    )

    selected = PdfReader(str(output_path))
    assert len(selected.pages) == 2
    assert [float(page.mediabox.width) for page in selected.pages] == [100, 300]


def test_rejects_out_of_range_benchmark_page(tmp_path: Path) -> None:
    from pypdf import PdfWriter

    source_path = tmp_path / "source.pdf"
    writer = PdfWriter()
    writer.add_blank_page(width=100, height=100)
    with source_path.open("wb") as output:
        writer.write(output)

    selection = OCRBenchmarkSelection(
        manifest_version="test",
        partition="ocr_refinement",
        document="aircraft",
        source_sha256=file_sha256(source_path),
        source_pages=[2],
    )
    with pytest.raises(ValueError, match="outside"):
        materialize_ocr_benchmark_selection(
            source_path=source_path,
            output_path=tmp_path / "selected.pdf",
            selection=selection,
        )
