from types import SimpleNamespace

import pytest

from app.services.google_document_ai import (
    GoogleDocumentAIOCRProvider,
    anchored_text,
    confidence_0_100,
    layout_geometry,
)


def ns(**kwargs):
    return SimpleNamespace(**kwargs)


def test_maps_google_document_to_provider_neutral_spans() -> None:
    text = "Annual inspection\nTach 123.4"
    line = ns(detected_languages=[ns(language_code="en", confidence=0.99)], layout=ns(
        text_anchor=ns(text_segments=[ns(start_index=0, end_index=17)]),
        confidence=0.97,
        bounding_poly=ns(
            normalized_vertices=[
                ns(x=0.1, y=0.2), ns(x=0.7, y=0.2),
                ns(x=0.7, y=0.25), ns(x=0.1, y=0.25),
            ],
            vertices=[],
        ),
    ))
    token = ns(detected_languages=[], layout=ns(
        text_anchor=ns(text_segments=[ns(start_index=18, end_index=22)]),
        confidence=0.91,
        bounding_poly=ns(
            normalized_vertices=[
                ns(x=0.1, y=0.3), ns(x=0.2, y=0.3),
                ns(x=0.2, y=0.34), ns(x=0.1, y=0.34),
            ],
            vertices=[],
        ),
    ))
    document = ns(
        text=text,
        processor_version="pretrained-ocr-v2.1-2024-08-07",
        pages=[ns(
            lines=[line],
            tokens=[token],
            image_quality_scores=ns(
                quality_score=0.84,
                detected_defects=[ns(type_="quality/defect_blurry", confidence=0.2)],
            ),
        )],
    )
    provider = GoogleDocumentAIOCRProvider(
        project_id="paprnav", processor_id="processor"
    )

    result = provider.result_from_document(
        document, source_page_number=4, canonical_width=3000, canonical_height=2000
    )

    assert result.provider_name == "google_document_ai"
    assert result.billable_page_count == 1
    assert result.pages[0].source_page_number == 4
    assert [span.span_type for span in result.pages[0].spans] == ["LINE", "WORD"]
    assert result.pages[0].spans[0].text == "Annual inspection"
    assert result.pages[0].spans[0].confidence == 97.0
    assert result.pages[0].spans[0].bbox_left == pytest.approx(0.1)
    assert result.metadata["image_quality"]["qualityScore"] == pytest.approx(0.84)


def test_geometry_converts_pixel_vertices_to_ratio() -> None:
    bbox, polygon = layout_geometry(
        ns(
            normalized_vertices=[],
            vertices=[
                ns(x=100, y=200), ns(x=500, y=200),
                ns(x=500, y=300), ns(x=100, y=300),
            ],
        ),
        width=1000,
        height=1000,
    )

    assert bbox["left"] == pytest.approx(0.1)
    assert bbox["top"] == pytest.approx(0.2)
    assert bbox["width"] == pytest.approx(0.4)
    assert bbox["height"] == pytest.approx(0.1)
    assert polygon[2] == [0.5, 0.3]


def test_anchor_and_confidence_helpers() -> None:
    anchor = ns(text_segments=[ns(start_index=None, end_index=4)])
    assert anchored_text("test remainder", anchor) == "test"
    assert confidence_0_100(0.87654) == 87.654
