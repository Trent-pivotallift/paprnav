from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

from app.core.config import get_settings
from app.services.ocr_provider import OCRPageResult, OCRProviderResult
from app.services.page_images import render_pdf_page_png, rendered_visual_metrics
from app.services.pdf_inspection import enrich_classification_from_render, inspect_pdf_bytes
from app.services.selective_ocr import process_upload_with_selective_routing


FIXTURES = Path(__file__).parent / "fixtures" / "native_text"


class ProviderSpy:
    provider_name = "aws_textract"
    provider_version = "test"
    configuration_hash = "textract-test"

    def __init__(self) -> None:
        self.calls = []

    def process_upload(self, **kwargs):
        self.calls.append(kwargs)
        return OCRProviderResult(
            provider_name=self.provider_name,
            provider_version=self.provider_version,
            configuration_hash=self.configuration_hash,
            pages=[
                OCRPageResult(
                    source_page_number=1,
                    page_label="Textract page",
                    width_px=100,
                    height_px=100,
                    rotation_degrees=0,
                    extraction_confidence=90,
                    spans=[],
                )
            ],
            billable_page_count=1,
        )


def prepared_page(pdf_bytes: bytes, page_number: int = 1):
    inspected = inspect_pdf_bytes(pdf_bytes).metadata["pages"][page_number - 1]
    rendered = render_pdf_page_png(pdf_bytes, page_number, dpi=300)
    inspected["classification"] = enrich_classification_from_render(
        inspected["classification"],
        {"visualMetrics": rendered_visual_metrics(rendered)},
        declared_rotation=inspected["declaredRotationDegrees"],
    )
    return SimpleNamespace(
        source_page_number=page_number,
        native_text_evaluation=inspected["nativeText"],
        page_classification=inspected["classification"],
    )


def test_reliably_native_page_bypasses_textract(tmp_path) -> None:
    pdf_bytes = (FIXTURES / "pure_native.pdf").read_bytes()
    storage_key = "uploads/ac/upl/pure-native.pdf"
    stored_path = tmp_path / storage_key
    stored_path.parent.mkdir(parents=True)
    stored_path.write_bytes(pdf_bytes)
    settings = replace(
        get_settings(),
        local_storage_path=str(tmp_path),
        storage_backend="local",
    )
    upload = SimpleNamespace(
        original_filename="pure-native.pdf",
        content_type="application/pdf",
        storage_backend="local",
        storage_key=storage_key,
        aircraft_id="ac",
        id="upl",
        cost_allocation_tags={},
    )
    provider = ProviderSpy()

    result = process_upload_with_selective_routing(
        settings=settings,
        upload=upload,
        pages=[prepared_page(pdf_bytes)],
        provider=provider,
    )

    assert provider.calls == []
    assert result.metadata["native_bypass_page_count"] == 1
    assert result.metadata["textract_page_count"] == 0
    assert result.billable_page_count == 0
    assert result.pages[0].source_provider_name == "pdf_native_text"


def test_mixed_page_remains_textract_routed(tmp_path) -> None:
    pdf_bytes = (FIXTURES / "mixed_native_image.pdf").read_bytes()
    storage_key = "uploads/ac/upl/mixed.pdf"
    stored_path = tmp_path / storage_key
    stored_path.parent.mkdir(parents=True)
    stored_path.write_bytes(pdf_bytes)
    settings = replace(
        get_settings(),
        local_storage_path=str(tmp_path),
        storage_backend="local",
    )
    upload = SimpleNamespace(
        original_filename="mixed.pdf",
        content_type="application/pdf",
        storage_backend="local",
        storage_key=storage_key,
        aircraft_id="ac",
        id="upl",
        cost_allocation_tags={},
    )
    provider = ProviderSpy()

    result = process_upload_with_selective_routing(
        settings=settings,
        upload=upload,
        pages=[prepared_page(pdf_bytes)],
        provider=provider,
    )

    assert len(provider.calls) == 1
    assert result.provider_name == "aws_textract"
