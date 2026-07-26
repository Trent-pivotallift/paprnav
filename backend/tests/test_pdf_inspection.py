from io import BytesIO

from pypdf import PdfWriter

from app.models.core import Upload
from app.services.pdf_inspection import (
    classify_page,
    enrich_classification_from_render,
    evaluate_native_text,
    inspect_pdf_bytes,
)


def blank_pdf_bytes(page_count: int = 1) -> bytes:
    output = BytesIO()
    writer = PdfWriter()
    for _ in range(page_count):
        writer.add_blank_page(width=612, height=792)
    writer.write(output)
    return output.getvalue()


def test_pdf_inspection_fingerprints_pages_and_keeps_textract_authoritative() -> None:
    document = blank_pdf_bytes(2)
    upload = Upload(
        aircraft_id="ac_pdf_inspection",
        uploaded_by_user_id="usr_pdf_inspection",
        original_filename="logbook.pdf",
        content_type="application/pdf",
        file_size_bytes=len(document),
        storage_backend="local",
        storage_key="uploads/logbook.pdf",
        sha256=__import__("hashlib").sha256(document).hexdigest(),
    )

    result = inspect_pdf_bytes(document, upload=upload)

    assert result.page_count == 2
    assert result.metadata["status"] == "complete"
    assert result.metadata["sourceHashMatchesUpload"] is True
    assert len(result.metadata["pages"][0]["sourcePageFingerprint"]) == 64
    assert result.metadata["pages"][0]["nativeText"]["mode"] == "calibration"
    assert result.metadata["pages"][0]["nativeText"]["reliableCandidate"] is False
    assert result.metadata["pages"][0]["classification"]["routingClass"] == "scanned"
    assert result.metadata["pages"][0]["extractionPlan"]["selectedProvider"] == "aws_textract"
    assert result.metadata["pages"][0]["extractionPlan"]["nativeTextMayBypassOCR"] is False


def test_page_classification_includes_document_role_and_layout_attributes() -> None:
    classification = classify_page(
        page_number=2,
        page_count=4,
        native_text={
            "textPreview": "2026 Annual inspection completed. Tach 1022.4",
            "meaningfulCharacterCount": 320,
            "reliableCandidate": True,
        },
    )

    assert classification["routingClass"] == "native_text"
    assert classification["documentRole"] == "logbook_entry"
    assert "typed" in classification["attributes"]
    assert "dense" in classification["attributes"]
    assert "continuation_sensitive" in classification["attributes"]


def test_encrypted_or_malformed_pdf_is_rejected() -> None:
    try:
        inspect_pdf_bytes(b"%PDF-1.4 malformed")
    except Exception as exc:
        assert str(exc)
    else:
        raise AssertionError("Malformed PDF should not pass inspection")


def test_render_geometry_enriches_spread_without_rotating_source_pixels() -> None:
    classification = enrich_classification_from_render(
        {"attributes": ["text_mode_uncertain", "layout_uncertain"]},
        {"visualMetrics": {"aspectRatio": 3.5, "luminanceStdDev": 42.0}},
        declared_rotation=0,
    )

    assert "side_by_side" in classification["attributes"]
    assert "landscape" in classification["attributes"]
    assert classification["visualClassification"]["orientationPolicy"] == (
        "visual_orientation_not_automatically_changed"
    )


class FakeNativePage:
    mediabox = type("MediaBox", (), {"width": 612, "height": 792})()

    def __init__(self, *, image_coverage: float = 0.0) -> None:
        self.image_coverage = image_coverage
        self.text = (
            "2024-05-10 Annual inspection completed by Example Aviation. "
            "Tach 1250.4 Total Time 5400.2 aircraft returned to service."
        )

    def extract_text(self, **kwargs):
        if kwargs.get("extraction_mode") == "layout":
            return self.text
        visitor = kwargs["visitor_text"]
        visitor(self.text, [1, 0, 0, 1, 0, 0], [1, 0, 0, 1, 72, 720], {}, 12)
        if self.image_coverage:
            operand = kwargs["visitor_operand_before"]
            operand(
                b"Do",
                [],
                [612 * self.image_coverage, 0, 0, 792, 0, 0],
                [1, 0, 0, 1, 0, 0],
            )
        return self.text


def test_native_text_reliability_requires_cross_mode_and_geometry_agreement() -> None:
    evaluation = evaluate_native_text(FakeNativePage())

    assert evaluation["profile"] == "native-text-reliability-v2"
    assert evaluation["reliableCandidate"] is True
    assert evaluation["extractorAgreement"] == 1.0
    assert evaluation["positionedSampleRatio"] == 1.0
    assert evaluation["plausibleFontRatio"] == 1.0


def test_image_dominant_page_cannot_be_reliably_native() -> None:
    evaluation = evaluate_native_text(FakeNativePage(image_coverage=1.0))

    assert evaluation["reliableCandidate"] is False
    assert "image_dominant_or_mixed_page" in evaluation["reasons"]
